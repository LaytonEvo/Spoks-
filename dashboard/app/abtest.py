"""A/B tests on Evoflows emails.

A test replaces one email step in a flow with a split: group A (contact.uuid sorts below the cut) gets the current email,
group B gets a test version edited in the builder (template key "<key>_b", draft -> approve -> publish like any email).
Contact uuids are random, so the split is fair and stable (the same person always gets the same version). Results are
the two steps' own numbers on Evoflows: sends, orders after the email, revenue. Ending a test puts the flow back to one
email; if B won, B's content is published under the original email so nothing else changes.

Lifecycle: draft -> approved (named user) -> running (flow pushed, still never switched on by the app) -> ended.
Engine dependency (asked of Luke, requirements item 18): conditions compare strings in order, or a 0-99 contact.bucket.
"""
import copy
import datetime as dt
import json
import math
import threading

from . import config, evoflows

STORE = config.DATA_DIR / "abtests.json"
OVERRIDES = config.DATA_DIR / "flow_overrides"
_lock = threading.Lock()
SPLITS = {"50": "8", "25": "4", "75": "c"}  # share for B -> uuid first-hex cut (B = uuid >= cut)


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _load():
    try:
        return json.loads(STORE.read_text())
    except Exception:
        return []


def _save(tests):
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(tests, ensure_ascii=False, indent=1))


def override(flow):
    try:
        return json.loads((OVERRIDES / f"{flow}.json").read_text())
    except Exception:
        return None


def definition(flow):
    """The flow as it should be on Evoflows: a running test's version, else the approved build."""
    return override(flow) or json.loads((evoflows.OUT / "flows" / f"{flow}.json").read_text())


def _find_step(steps, step_id, parent=None):
    for i, s in enumerate(steps):
        if s.get("id") == step_id:
            return steps, i
        for b in s.get("branches", []):
            r = _find_step(b["steps"], step_id)
            if r:
                return r
    return None


def candidates(flow):
    """Email steps that can be tested (not already in a test)."""
    out = []

    def walk(steps, path):
        for s in steps:
            if s["type"] == "email" and not s["id"].endswith("_b"):
                out.append({"step": s["id"], "template": s["template"], "path": " › ".join(path)})
            for b in s.get("branches", []):
                if not b["id"].startswith("variant_"):
                    walk(b["steps"], path + [b["id"].replace("_", " ")])
    walk(definition(flow)["steps"], [])
    busy = {t["step"] for t in _load() if t["flow"] == flow and t["status"] in ("draft", "approved", "running")}
    return [c for c in out if c["step"] not in busy]


def create(flow, step, share, who, name=""):
    from . import builder
    if flow not in evoflows.manifest()["flows"]:
        raise ValueError("Not one of our flows.")
    if share not in SPLITS:
        raise ValueError("Pick a split.")
    c = next((x for x in candidates(flow) if x["step"] == step), None)
    if not c:
        raise ValueError("That email can't be tested (it's already in a test).")
    variant = builder.create_variant(c["template"])
    with _lock:
        tests = _load()
        tid = f"t{len(tests) + 1}"
        tests.append({"id": tid, "flow": flow, "step": step, "template_a": c["template"], "template_b": variant, "share_b": share,
                      "name": name or f"{c['template']} test", "status": "draft", "created_by": who, "created_at": _now(), "history": []})
        _save(tests)
    return tid


def _get(tests, tid):
    t = next((x for x in tests if x["id"] == tid), None)
    if not t:
        raise KeyError(tid)
    return t


def approve(tid, who):
    from . import builder
    with _lock:
        tests = _load()
        t = _get(tests, tid)
        if t["status"] != "draft":
            raise ValueError(f"The test is {t['status']}.")
        if builder.live(t["template_b"]).get("status") != "published":
            raise ValueError("Publish version B first: open it in the builder, save, approve and publish it.")
        t.update(status="approved", approved_by=who, approved_at=_now())
        t["history"].append({"at": _now(), "by": who, "action": "approved"})
        _save(tests)
    return t


def _push(flow, defn, who, what):
    st, res = evoflows._call("POST", f"/flows/{flow}/validate", defn)
    if st >= 400 or not (res or {}).get("valid") or (res or {}).get("problems"):
        raise ValueError(f"Evoflows didn't accept the change: {json.dumps(res)[:300]}")
    defn = dict(defn)
    defn.pop("enabled", None)  # never switch on from here
    st, res = evoflows._call("PUT", f"/flows/{flow}", defn)
    if st >= 400:
        raise ValueError(f"Evoflows refused the flow ({st}): {json.dumps(res)[:300]}")
    evoflows._log({"at": _now(), "by": who, "push": what, "status": st})
    return res


def start(tid, who):
    with _lock:
        tests = _load()
        t = _get(tests, tid)
        if t["status"] != "approved":
            raise ValueError("Approve the test first.")
        defn = copy.deepcopy(definition(t["flow"]))
        found = _find_step(defn["steps"], t["step"])
        if not found:
            raise ValueError("That email isn't in the flow any more.")
        steps, i = found
        orig = steps[i]
        cut = SPLITS[t["share_b"]]
        steps[i] = {"id": f"ab_{t['step']}", "type": "split", "branches": [
            {"id": "variant_a", "when": {"field": "contact.uuid", "lt": cut}, "steps": [orig]},
            {"id": "variant_b", "steps": [{**orig, "id": f"{t['step']}_b", "template": t["template_b"]}]}]}
        res = _push(t["flow"], defn, who, f"start A/B test {t['name']}")
        OVERRIDES.mkdir(parents=True, exist_ok=True)
        (OVERRIDES / f"{t['flow']}.json").write_text(json.dumps(defn, ensure_ascii=False, indent=1))
        t.update(status="running", started_by=who, started_at=_now(), flow_version=(res or {}).get("version"))
        t["history"].append({"at": _now(), "by": who, "action": "started"})
        _save(tests)
    return t


def end(tid, winner, who):
    """Back to one email. If B won, its content is published under the original email (so the flow keeps its keys)."""
    from . import builder
    if winner not in ("a", "b"):
        raise ValueError("Pick the version to keep.")
    with _lock:
        tests = _load()
        t = _get(tests, tid)
        if t["status"] != "running":
            raise ValueError("Only a running test can be ended.")
        if winner == "b":
            builder.adopt_variant(t["template_a"], t["template_b"], who)
        defn = copy.deepcopy(definition(t["flow"]))
        found = _find_step(defn["steps"], f"ab_{t['step']}")
        if found:
            steps, i = found
            steps[i] = steps[i]["branches"][0]["steps"][0]
        _push(t["flow"], defn, who, f"end A/B test {t['name']} (kept {winner.upper()})")
        built = json.loads((evoflows.OUT / "flows" / f"{t['flow']}.json").read_text())
        p = OVERRIDES / f"{t['flow']}.json"
        if defn.get("steps") == built.get("steps"):
            p.unlink(missing_ok=True)
        else:
            p.write_text(json.dumps(defn, ensure_ascii=False, indent=1))
        t.update(status="ended", ended_by=who, ended_at=_now(), winner=winner)
        t["history"].append({"at": _now(), "by": who, "action": f"ended, kept {winner.upper()}"})
        _save(tests)
    return t


def cancel(tid, who):
    with _lock:
        tests = _load()
        t = _get(tests, tid)
        if t["status"] not in ("draft", "approved"):
            raise ValueError("A running test is ended by picking a winner.")
        t.update(status="cancelled")
        t["history"].append({"at": _now(), "by": who, "action": "cancelled"})
        _save(tests)
    return t


def _z(c1, n1, c2, n2):
    """Two-proportion z-test: how sure we are the conversion rates differ (0-1)."""
    if min(n1, n2) == 0:
        return None
    p = (c1 + c2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2)) if 0 < p < 1 else 0
    if not se:
        return None
    z = abs(c1 / n1 - c2 / n2) / se
    return math.erf(z / math.sqrt(2))  # two-sided confidence


def results(t, flow_snap):
    """Per-version numbers from the flow's step metrics (longest period that covers the test)."""
    def step_stats(tf, sid):
        stack = list(flow_snap.get("steps", [])) if flow_snap else []
        while stack:
            s = stack.pop()
            if s.get("kind") == "email" and s.get("action_id") == sid:
                return (s.get("metrics") or {}).get(tf) or {}
            for b in s.get("branches", []):
                stack.extend(b["steps"])
        return {}
    started = dt.datetime.fromisoformat(t["started_at"]) if t.get("started_at") else None
    days = (dt.datetime.now(dt.timezone.utc) - started).days if started else 0
    tf = "last_30_days" if days <= 30 else "last_90_days" if days <= 90 else "last_365_days"
    a, b = step_stats(tf, t["step"]), step_stats(tf, f"{t['step']}_b")
    out = {"period": tf, "days": days}
    for k, s in (("a", a), ("b", b)):
        n, c, rev = s.get("recipients") or 0, s.get("conversions") or 0, s.get("conversion_value") or 0
        out[k] = {"sends": n, "orders": c, "revenue": rev, "conv": c / n if n else None, "rps": rev / n if n else None,
                  "unsub": s.get("unsubscribe_rate")}
    conf = _z(out["a"]["orders"], out["a"]["sends"], out["b"]["orders"], out["b"]["sends"])
    lead = None
    if out["a"]["conv"] is not None and out["b"]["conv"] is not None and out["a"]["conv"] != out["b"]["conv"]:
        lead = "a" if out["a"]["conv"] > out["b"]["conv"] else "b"
    enough = min(out["a"]["sends"], out["b"]["sends"]) >= 300 and (out["a"]["orders"] + out["b"]["orders"]) >= 20
    out.update(confidence=conf, leader=lead, enough=enough,
               verdict=("No sends yet." if not out["a"]["sends"] and not out["b"]["sends"] else
                        "Too early to call: wait for at least 300 sends each and 20 orders in total." if not enough else
                        f"{lead.upper()} is ahead with {conf * 100:.0f}% confidence." if lead and conf and conf >= 0.95 else
                        f"{lead.upper() if lead else 'Neither'} is ahead, but not clearly ({(conf or 0) * 100:.0f}% confidence; aim for 95%)."))
    return out


def all_tests():
    return _load()

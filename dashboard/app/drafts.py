"""New EG draft flows, created in Klaviyo only after a named user approves them on the Drafts page.

A pack (app/drafts/<id>.json, written by klaviyo/build_packs.py) holds the emails (app/drafts/html/...), any
segment the flow starts from, and the flow in Klaviyo's API format. Approving creates, in order: the segments
(reusing one that already has the same name), the email templates, then the flow. Klaviyo creates new flows and
their messages as drafts, and this module has no way to switch them on, edit an existing flow, send or delete.
Progress is saved after every step, so "Try again" picks up where it stopped and never makes duplicates.
"""
import copy
import datetime as dt
import json
import re
import threading

from . import config
from .klaviyo import KlaviyoError, WriteClient

PACKS = config.BASE_DIR / "app" / "drafts"
STORE = config.DATA_DIR / "drafts"
PREFIX = "EG ·"
# Settings Klaviyo may not accept on create. If it rejects one, it is dropped, the flow is created without it,
# and the card says what to set in the editor instead. Anything else Klaviyo rejects stops the run.
OPTIONAL = {"preview_text", "name", "add_tracking_params", "delay_until_time", "delay_until_weekdays", "add_org_prefix",
            "add_opt_out_language", "sms_quiet_hours_enabled", "shorten_links", "add_info_link", "reply_to_email",
            "secondary_value", "timezone", "transactional"}
EDITOR_HINT = {"preview_text": "preview text on each email", "name": "message names", "add_tracking_params": "UTM tracking",
               "delay_until_time": "send times on the waits", "delay_until_weekdays": "send days on the waits",
               "add_org_prefix": "SMS company name", "add_opt_out_language": "SMS opt-out wording"}
_lock = threading.Lock()
_running = set()


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def packs():
    return {p.stem: json.loads(p.read_text()) for p in sorted(PACKS.glob("*.json"))}


def pack(pid):
    p = PACKS / f"{pid}.json"
    if not p.exists():
        raise KeyError(pid)
    return json.loads(p.read_text())


def email_html(pid, key):
    t = next((t for t in pack(pid)["templates"] if t["key"] == key), None)
    if not t:
        raise KeyError(key)
    return (PACKS / "html" / t["file"]).read_text()


def _state(pid):
    p = STORE / f"{pid}.json"
    if p.exists():
        return json.loads(p.read_text())
    return {"id": pid, "status": "ready", "segments": {}, "templates": {}, "flow_id": None, "dropped": [], "history": []}


def _save(st):
    STORE.mkdir(parents=True, exist_ok=True)
    (STORE / f"{st['id']}.json").write_text(json.dumps(st, ensure_ascii=False))


def _hist(st, who, action, detail=""):
    st["history"].append({"at": _now(), "by": who, "action": action, "detail": detail})


def public(pid):
    pk, st = pack(pid), _state(pid)
    out = {k: pk.get(k) for k in ("id", "title", "summary", "outline", "after", "replaces")}
    out["flow_name"] = pk["flow"]["name"]
    out["emails"] = [{k: t.get(k) for k in ("key", "name", "subject", "preview", "when", "sender")} for t in pk["templates"]]
    out.update({k: st.get(k) for k in ("status", "segments", "templates", "flow_id", "dropped", "history", "error", "verify")})
    out["running"] = pid in _running
    out["klaviyo_url"] = f"https://www.klaviyo.com/flow/{st['flow_id']}/edit" if st.get("flow_id") else None
    return out


def all_public():
    return [public(pid) for pid in packs()]


def approve(pid, who):
    pk = pack(pid)
    if not pk["flow"]["name"].startswith(PREFIX):
        raise ValueError(f"Only flows named “{PREFIX} …” can be created.")
    if not config.KLAVIYO_WRITE_KEY or config.USE_FIXTURES:
        raise ValueError("The app has no Klaviyo write key, so it can't create anything.")
    with _lock:
        st = _state(pid)
        if st["status"] == "created":
            raise ValueError("Already created in Klaviyo.")
        if pid in _running:
            raise ValueError("Already being created.")
        _running.add(pid)
        st["status"], st["error"] = "creating", None
        _hist(st, who, "approved", "create in Klaviyo as a draft")
        _save(st)
    threading.Thread(target=_run, args=(pid, who), daemon=True).start()
    return public(pid)


def _resolve(pk, st):
    """Swap the pack's references for the real Klaviyo ids created so far."""
    flow = copy.deepcopy(pk["flow"])
    definition = flow["definition"]
    for trig in definition.get("triggers", []):
        if "ref" in trig:
            trig["id"] = st["segments"][trig.pop("ref")]
    for a in definition["actions"]:
        msg = (a.get("data") or {}).get("message")
        if msg and "template_ref" in msg:
            msg["template_id"] = st["templates"][msg.pop("template_ref")]
    return flow["name"], definition


def _drop(definition, field):
    for a in definition["actions"]:
        data = a.get("data") or {}
        data.pop(field, None)
        if isinstance(data.get("message"), dict):
            data["message"].pop(field, None)


def _rejected_fields(err):
    fields = set(re.findall(r'"pointer":\s*"/data/attributes/definition/actions/\d+/data/(?:message/)?([a-z_]+)', err))
    fields |= {f for f in OPTIONAL if "_" in f and f in err}  # plain words like "name" appear in unrelated errors
    return fields & OPTIONAL


def _run(pid, who):
    pk, st = pack(pid), _state(pid)
    try:
        w = WriteClient()
        if not st.get("flow_id"):
            existing = w.flow_by_name(pk["flow"]["name"])
            if existing:
                raise KlaviyoError(f"Klaviyo already has a flow called “{pk['flow']['name']}” ({existing}). Nothing new was created.")
        for seg in pk.get("segments", []):
            if seg["key"] not in st["segments"]:
                sid = w.segment_by_name(seg["name"])
                _hist(st, "app", "segment found" if sid else "segment created", seg["name"])
                st["segments"][seg["key"]] = sid or w.create_segment(seg["name"], seg["definition"])
                _save(st)
        for t in pk["templates"]:
            if t["key"] not in st["templates"]:
                st["templates"][t["key"]] = w.create_template(t["template_name"], (PACKS / "html" / t["file"]).read_text())
                _hist(st, "app", "email created", t["template_name"])
                _save(st)
        name, definition = _resolve(pk, st)
        for _ in range(len(OPTIONAL) + 1):
            try:
                st["flow_id"] = w.create_flow(name, definition)
                break
            except KlaviyoError as e:
                bad = _rejected_fields(str(e)) - set(st["dropped"])
                if not bad:
                    raise
                for f in bad:
                    _drop(definition, f)
                st["dropped"] += sorted(bad)
                _hist(st, "app", "Klaviyo refused a setting", ", ".join(EDITOR_HINT.get(f, f) for f in sorted(bad)) + ": set in the editor")
                _save(st)
        _hist(st, "app", "flow created", f"{name} ({st['flow_id']})")
        made = w.flow(st["flow_id"])
        attrs = made["attributes"]
        n_made = len((attrs.get("definition") or {}).get("actions") or [])
        st["verify"] = {"status": attrs.get("status"), "steps": n_made, "expected": len(definition["actions"]),
                        "ok": attrs.get("status") == "draft" and n_made == len(definition["actions"])}
        _hist(st, "app", "checked in Klaviyo", f"status {attrs.get('status')}, {n_made} of {len(definition['actions'])} steps")
        st["status"] = "created"
    except Exception as e:
        st["status"], st["error"] = "failed", str(e)[:900]
        _hist(st, "app", "stopped", str(e)[:300])
    finally:
        _save(st)
        _running.discard(pid)

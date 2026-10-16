"""Evoflows part of the dashboard snapshot: our flows on the new engine, in the same shape as the Klaviyo flows.

Reads the engine (GET /flows, /flows/{key}, /metrics) and the approved builds shipped in app/evoflows_out (manifest,
flow definitions, previews). Written to DATA_DIR/evosnap.json, rebuilt every 15 minutes and on Refresh. Read-only:
nothing here pushes, enables or sends.
"""
import datetime as dt
import json
import logging
import re
import threading
import time

from . import config, evoflows

CACHE = config.DATA_DIR / "evosnap.json"
OUT = evoflows.OUT
# Our copy talks about membership's "5% / 10% off" all the time; that isn't a discount code. Flag only real codes.
CODE_RE = re.compile(r"coupon_code|discount_code|/discount/|\bcode\s+[A-Z0-9]{4,}\b")
PERIODS = {"last_30_days": "30d", "last_90_days": "90d", "last_365_days": "365d"}
log = logging.getLogger("uvicorn.error")
_lock = threading.Lock()
status = {"running": False, "step": "", "error": None, "finished_at": None}

FIELD = {  # condition fields in plain words
    "flags.is_annual": "annual member", "flags.is_member": "member (Free or annual)", "flags.is_free_member": "Free member",
    "flags.has_hardware": "order has a trolley, clubs or used clubs", "flags.has_trolley": "order has a trolley",
    "flags.has_clubs": "order has clubs", "flags.has_shoes": "order has shoes", "checkout.total": "basket value",
    "order.total": "order value", "order.age_days": "order age (days)", "order.source": "order source",
    "customer.orders_count": "orders placed", "event.data.tier": "membership tier", "contact.consent": "consent",
}
OPS = {"eq": "is", "ne": "is not", "gt": "over", "gte": "at least", "lt": "under", "lte": "at most", "in": "is one of",
       "nin": "is none of", "contains": "includes", "not_contains": "doesn't include", "exists": "is set"}
TRIGGER = {"checkout_abandoned": "When someone leaves a checkout without buying", "order_fulfilled": "When an order is fulfilled",
           "order_placed": "When an order is placed", "subscribed": "When someone subscribes to the mailing list"}
BRANCH = {"annual": "Annual members", "big": "£300 or more", "small": "Under £300", "hardware": "Hardware",
          "everything_else": "Everything else"}


def label(c):
    """A condition as words: {"field": "checkout.total", "gte": 300} -> "basket value at least £300"."""
    if not c:
        return ""
    if "all" in c:
        return " and ".join(label(x) for x in c["all"])
    if "any" in c:
        return "(" + " or ".join(label(x) for x in c["any"]) + ")"
    if "not" in c:
        inner = c["not"]
        if inner.get("field") == "customer.orders_count" and inner.get("gt") == 0:
            return "has never ordered"
        if set(inner) >= {"field", "eq"} and inner["eq"] is True:
            return "not " + FIELD.get(inner["field"], inner["field"])
        return "not (" + label(inner) + ")"
    f = c.get("field", "?")
    op = next((k for k in OPS if k in c), None)
    v = c.get(op)
    name = FIELD.get(f, f)
    if op == "eq" and v is True:
        return name
    if op == "eq" and v is False:
        return "not " + name
    if f == "customer.orders_count" and op == "gt" and v == 0:
        return "has ordered"
    if f in ("checkout.total", "order.total") and isinstance(v, (int, float)):
        v = f"£{v:,.0f}"
    if isinstance(v, list):
        v = " or ".join(str(x) for x in v)
    return f"{name} {OPS.get(op, op)}{'' if op == 'exists' else ' ' + str(v)}"


def _delay(s):
    f = s.get("for", {})
    parts = [f"{f[k]} {k[:-1] if f[k] == 1 else k}" for k in ("days", "hours", "minutes") if f.get(k)]
    out = "Wait " + (" ".join(parts) or "0 minutes")
    if s.get("until_time"):
        out += f", then send at {s['until_time']}"
    return out


def _subject(text):
    return (text or "").replace("{{ if .Tx.Data.first_name }}, {{ .Tx.Data.first_name }}{{ end }}", "[, first name]")


def _rates(sent, unsub, bounced):
    return {"unsubscribe_rate": unsub / sent if sent else None, "bounce_rate": bounced / sent if sent else None}


def steps_from(defn_steps, manifest, step_metrics):
    out = []
    for s in defn_steps:
        t = s.get("type")
        if t == "wait":
            out.append({"kind": "delay", "label": _delay(s) + (f" (only if {label(s['when'])})" if s.get("when") else "")})
        elif t == "email":
            key = s.get("template")
            tm = manifest["templates"].get(key, {})
            m = {"kind": "email", "action_id": s["id"], "message_id": key, "name": tm.get("name") or key, "status": None,
                 "subject": _subject(tm.get("subject")), "preview_text": tm.get("preview_text"), "from_label": tm.get("from_name"),
                 "template_id": key, "utm": True, "smart_sending": s.get("max_per_contact_hours") != 0,
                 "only_if": label(s.get("when")), "platform": "evoflows", "rendered": (OUT / "previews" / f"{key}.html").exists()}
            if s.get("max_per_contact_hours") == 0:
                m["cap_note"] = "Always sends straight away (past the 16-hour cap)"
            m["metrics"] = {}
            for tf, per in step_metrics.items():
                st = per.get(s["id"])
                if st:
                    sent = st.get("sent") or 0
                    rev = st.get("revenue_after") or 0
                    m["metrics"][tf] = {"recipients": sent, "conversions": st.get("converted_after") or 0, "conversion_value": rev,
                                        "revenue_per_recipient": rev / sent if sent else None, "open_rate": None, "click_rate": None,
                                        **_rates(sent, st.get("unsubscribed") or 0, st.get("bounced") or 0),
                                        "skipped": st.get("skipped") or 0, "errors": st.get("errors") or 0}
            out.append(m)
        elif t == "split":
            branches = []
            for b in s.get("branches", []):
                branches.append({"label": BRANCH.get(b["id"]) or b["id"].replace("_", " ").capitalize(),
                                 "condition": label(b["when"]) if b.get("when") else "everyone not matched above",
                                 "steps": steps_from(b.get("steps", []), manifest, step_metrics)})
            out.append({"kind": "split", "split_type": "evoflows", "label": "First match wins", "branches": branches})
        elif t == "exit":
            out.append({"kind": "other", "label": f"Leaves the flow ({s.get('reason', '')})"})
        elif t == "set":
            out.append({"kind": "update", "label": f"Set {s.get('attribute')} = {s.get('value')}"})
        else:
            out.append({"kind": "other", "label": t or "step"})
    return out


def _iter_emails(steps):
    for s in steps:
        if s["kind"] == "email":
            yield s
        for b in s.get("branches", []):
            yield from _iter_emails(b["steps"])


def _week_monday(label_):
    try:
        if "-" in label_ and len(label_) <= 8:  # "2026-41" (ISO year-week)
            y, w = label_.split("-")
            return dt.date.fromisocalendar(int(y), int(w), 1).isoformat()
        return dt.date.fromisoformat(label_[:10]).isoformat()
    except ValueError:
        return None


def _flag(level, text):
    return {"level": level, "text": text}


def flow_flags(flow, tf):
    f, t = [], flow["totals"].get(tf) or {}
    sent = t.get("recipients") or 0
    if flow["status"] == "live" and not sent:
        f.append(_flag("medium", "Switched on but sent nothing in this period"))
    if flow.get("differs"):
        f.append(_flag("medium", "What's on Evoflows differs from the approved build: push it again from New flows to approve"))
    if flow["status"] == "not_pushed":
        f.append(_flag("info", "Built and approved here, not pushed to Evoflows yet"))
    if sent >= 100:
        u, b = t.get("unsubscribe_rate") or 0, t.get("bounce_rate") or 0
        if u > 0.01:
            f.append(_flag("high", f"Unsubscribe rate {u * 100:.1f}% (limit 0.5%)"))
        elif u > 0.005:
            f.append(_flag("medium", f"Unsubscribe rate {u * 100:.1f}% (limit 0.5%)"))
        if b > 0.02:
            f.append(_flag("medium", f"Bounce rate {b * 100:.1f}%"))
        if (t.get("complained") or 0) / sent > 0.001:
            f.append(_flag("high", f"Spam complaints {(t['complained'] / sent) * 100:.2f}% (keep under 0.10%)"))
    if t.get("errors"):
        f.append(_flag("medium", f"{t['errors']} send error{'s' if t['errors'] != 1 else ''} in this period"))
    enrolled = t.get("enrolled") or 0
    if enrolled >= 20 and (t.get("refused_no_consent") or 0) / enrolled > 0.2:
        f.append(_flag("info", f"{t['refused_no_consent']} of {enrolled} people entered without email consent, so got nothing"))
    return f


def _manifest():
    try:
        return json.loads((OUT / "manifest.json").read_text())
    except Exception:
        return {"flows": {}, "templates": {}}


def build():
    if not evoflows.enabled() or not _lock.acquire(blocking=False):
        return
    status.update(running=True, error=None, step="Reading Evoflows")
    try:
        from . import snapshot  # message checks shared with the Klaviyo side
        man = _manifest()
        listed = {f["key"]: f for f in (evoflows._get("/flows", fresh=True) or {}).get("flows", [])}
        flows = []
        for key, meta in man["flows"].items():
            status["step"] = f"Reading {meta['name']}"
            built = json.loads((OUT / "flows" / f"{key}.json").read_text())
            eng = listed.get(key)
            live_def, differs = None, False
            if eng:
                code, res = evoflows._call("GET", f"/flows/{key}")
                if code < 400 and res:
                    live_def = res
                    differs = any(res.get(k) != built.get(k) for k in ("trigger", "entry", "steps", "consent", "exit", "send_window", "utm"))
            defn = live_def or built
            step_metrics, totals, weekly = {}, {}, None
            if eng:
                for tf, per in PERIODS.items():
                    try:
                        m = evoflows._get(f"/metrics?flow={key}&period={per}&by=step", fresh=True)
                    except evoflows.EvoflowsError as e:
                        log.warning("Evoflows metrics %s %s: %s", key, per, str(e)[:200])
                        continue
                    t = m.get("totals") or {}
                    sent = t.get("sent") or 0
                    rev = t.get("revenue") or 0
                    totals[tf] = {"recipients": sent, "revenue": rev, "conversions": t.get("converted_after_email") or 0,
                                  "revenue_per_recipient": rev / sent if sent else None, "open_rate": None, "click_rate": None,
                                  "conversion_rate": t.get("conversion_rate") if sent else None,
                                  "unsubscribe_rate": t.get("unsubscribe_rate") if sent else None,
                                  "bounce_rate": t.get("bounce_rate") if sent else None,
                                  **{k: t.get(k) for k in ("enrolled", "active", "finished", "exited", "refused_no_consent",
                                                          "complained", "errors", "skipped", "converted", "dry_run")}}
                    step_metrics[tf] = {s["id"]: s for s in m.get("steps") or []}
                    time.sleep(0.3)  # stay well under the engine's 60 requests a minute
                try:
                    w = evoflows._get(f"/metrics?flow={key}&period=365d&by=week", fresh=True)
                    rows = [(r, _week_monday(str(r.get("week", "")))) for r in w.get("weeks") or []]
                    rows = [(r, d) for r, d in rows if d]
                    weekly = {"weeks": [d for _, d in rows], "recipients": [r.get("sent") or 0 for r, _ in rows],
                              "conversion_value": [r.get("revenue") or 0 for r, _ in rows],
                              "conversions": [r.get("converted_after_email") or 0 for r, _ in rows]}
                except evoflows.EvoflowsError as e:
                    log.warning("Evoflows weekly %s: %s", key, str(e)[:200])
            trig = defn.get("trigger") or {}
            trigger = TRIGGER.get(trig.get("type")) or (f"When the “{trig.get('event_name')}” event arrives" if trig.get("type") == "custom" else trig.get("type", ""))
            only = [label(trig["when"])] if trig.get("when") else []
            ent = defn.get("entry") or {}
            flow = {
                "id": key, "name": meta["name"], "platform": "evoflows", "programme": meta.get("programme"),
                "status": ("live" if eng.get("enabled") else "off") if eng else "not_pushed",
                "version": eng.get("version") if eng else None, "enabled_at": eng.get("enabled_at") if eng else None,
                "updated": (eng or {}).get("updated_at"), "trigger_type": trig.get("type"), "trigger": trigger,
                "flow_filter": "; ".join(only), "exit": label((defn.get("exit") or {}).get("when")),
                "reentry_text": (f"Can come back after {ent['reentry_after_days']} days" if ent.get("reentry_after_days") else "Once per person"),
                "consent": defn.get("consent"), "reentry": None, "summary": meta.get("summary"),
                "replaces": meta.get("replaces", []), "deviations": meta.get("deviations", []), "differs": differs,
                "steps": steps_from(defn.get("steps", []), man, step_metrics), "totals": totals, "weekly": weekly,
            }
            for m in _iter_emails(flow["steps"]):
                try:
                    m["_text"] = snapshot._plain_text((OUT / "previews" / f"{m['message_id']}.html").read_text())[:4000]
                except Exception:
                    pass
            flow["flags"] = {tf: flow_flags(flow, tf) for tf in PERIODS}
            for m in _iter_emails(flow["steps"]):
                code = CODE_RE.search(" ".join(filter(None, [m.get("subject"), m.get("preview_text"), m.get("_text")])))
                m["flags"] = {tf: [x for x in snapshot.message_flags(m, flow, tf) if "Smart sending" not in x["text"]
                                   and (code or not x["text"].startswith("Offers a discount"))] for tf in PERIODS}
            flows.append(flow)
        snap = {"generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "flows": flows,
                "engine_only": sorted(k for k in listed if k not in man["flows"])}
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = CACHE.with_suffix(".tmp")
        tmp.write_text(json.dumps(snap, ensure_ascii=False))
        tmp.replace(CACHE)
        status.update(step="Done", finished_at=snap["generated_at"])
    except Exception as e:
        status.update(error=str(e)[:300], step="Failed")
        log.exception("Evoflows refresh failed")
    finally:
        status["running"] = False
        _lock.release()


def load():
    try:
        return json.loads(CACHE.read_text())
    except Exception:
        return None


def loop():
    """Keep the Evoflows part fresh: the engine's API is cheap, unlike Klaviyo's reporting."""
    while True:
        try:
            build()
        except Exception:
            log.exception("Evoflows refresh loop")
        time.sleep(900)

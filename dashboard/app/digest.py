"""The Monday summary: what changed last week, what is newly flagged, and the top actions.

Built from the snapshot only (no extra Klaviyo calls). Posting to Slack happens only when
SLACK_WEBHOOK_URL is set; without it the summary is just a page in the dashboard.
"""
import datetime as dt
import json
import logging
import re

import httpx

from . import config, snapshot

log = logging.getLogger("uvicorn.error")
STATE = config.DATA_DIR / "digest_state.json"
TF = "last_30_days"


def _messages(steps):
    for s in steps:
        if s["kind"] in ("email", "sms"):
            yield s
        elif s["kind"] == "split":
            for b in s["branches"]:
                yield from _messages(b["steps"])


def _weekly(flow, key):
    out = None
    for m in _messages(flow["steps"]):
        vals = (m.get("weekly") or {}).get(key)
        if vals:
            out = vals[:] if out is None else [a + b for a, b in zip(out, vals)]
    return out


def _last_complete(weeks, generated_at):
    """Index of the last week that had finished when the snapshot was taken."""
    gen = dt.date.fromisoformat(generated_at[:10])
    for i in range(len(weeks) - 1, -1, -1):
        if dt.date.fromisoformat(weeks[i]) + dt.timedelta(days=7) <= gen:
            return i
    return None


def _flag_key(flow, m, text):
    return f"{flow['id']}|{(m or {}).get('message_id', '')}|{text}"


def _tf(snap):
    tfs = snap.get("timeframes") or []
    return TF if TF in tfs else (tfs[0] if tfs else TF)


def _highs(snap):
    tf = _tf(snap)
    for f in snap["flows"]:
        if f["status"] != "live":
            continue
        for x in f["flags"].get(tf, []):
            if x["level"] == "high":
                yield f, None, x["text"]
        for m in _messages(f["steps"]):
            for x in (m.get("flags") or {}).get(tf, []):
                if x["level"] == "high":
                    yield f, m, x["text"]


def build(snap=None):
    snap = snap or snapshot.load()
    if not snap:
        return None
    weeks = snap.get("weeks") or []
    i = _last_complete(weeks, snap["generated_at"]) if weeks else None
    live = [f for f in snap["flows"] if f["status"] == "live"]
    summary = {"generated_at": snap["generated_at"], "has_weeks": i is not None and i >= 4,
               "week_of": weeks[i] if i is not None else None, "flows": [], "stopped": [], "new_flags": [], "actions": []}

    if summary["has_weeks"]:
        tot_rev = tot_prev = tot_sends = tot_prev_sends = 0
        for f in live:
            rev, sends = _weekly(f, "conversion_value"), _weekly(f, "recipients")
            if not sends:
                continue
            r, s = rev[i], sends[i]
            pr, ps = sum(rev[i - 4:i]) / 4, sum(sends[i - 4:i]) / 4
            tot_rev += r; tot_prev += pr; tot_sends += s; tot_prev_sends += ps
            summary["flows"].append({"id": f["id"], "name": f["name"], "revenue": r, "revenue_avg4": pr,
                                     "sends": s, "sends_avg4": ps})
            if s == 0 and ps >= 5:
                summary["stopped"].append({"id": f["id"], "name": f["name"], "sends_avg4": ps})
        summary["totals"] = {"revenue": tot_rev, "revenue_avg4": tot_prev, "sends": tot_sends, "sends_avg4": tot_prev_sends}
        summary["flows"].sort(key=lambda x: abs(x["revenue"] - x["revenue_avg4"]), reverse=True)

    state = _load_state()
    seen = set(state.get("flags") or [])
    highs = list(_highs(snap))
    for f, m, text in highs:
        if _flag_key(f, m, text) not in seen:
            summary["new_flags"].append({"flow": f["name"], "flow_id": f["id"], "message": (m or {}).get("name"), "text": text})
    summary["first_run"] = not state
    # Top actions: live flows that stopped sending first, then high checks (discounts and complaints before the rest).
    actions = [{"flow": x["name"], "flow_id": x["id"], "text": "Stopped sending last week: check the trigger and filters"} for x in summary["stopped"]]
    order = lambda t: 0 if "discount" in t.lower() else 1 if "spam" in t.lower() else 2 if "opt-out" in t.lower() else 3
    groups = {}
    for f, m, text in sorted(highs, key=lambda h: (order(h[2]), -((h[0]["totals"].get(_tf(snap)) or {}).get("recipients") or 0))):
        kind = re.sub(r"\s*\([^)]*\)|\d+(\.\d+)?%| code\b", "", text).strip()  # "Offers a discount code (X)…" and "Offers a discount…" group together
        g = groups.setdefault((f["id"], kind), {"flow": f["name"], "flow_id": f["id"], "text": kind if kind != text else text, "messages": []})
        if m:
            g["messages"].append(m.get("name"))
    for g in groups.values():
        ms = g.pop("messages")
        if len(ms) > 1:
            g["text"] = f"{len(ms)} messages: {g['text'][0].lower() + g['text'][1:]} ({', '.join(ms[:3])}{'…' if len(ms) > 3 else ''})"
        elif ms:
            g["message"] = ms[0]
        actions.append(g)
    summary["actions"] = actions[:3]
    summary["_flag_keys"] = [_flag_key(f, m, t) for f, m, t in highs]
    return summary


def _load_state():
    try:
        return json.loads(STATE.read_text())
    except (OSError, ValueError):
        return {}


def _gbp(v):
    return f"£{v:,.0f}"


def _change(now, before):
    if not before:
        return "new" if now else "no change"
    pct = (now - before) / before * 100
    return f"{'+' if pct >= 0 else ''}{pct:.0f}%"


def to_slack(s, base_url=""):
    link = lambda fid, name: f"<{base_url}/#flow/{fid}|{name}>" if base_url else name
    lines = [f"*Evolution Golf flows: week of {s['week_of'] or 'n/a'}*"]
    if s["has_weeks"]:
        t = s["totals"]
        lines.append(f"Revenue {_gbp(t['revenue'])} from {t['sends']:,.0f} sends "
                     f"({_change(t['revenue'], t['revenue_avg4'])} vs the 4-week average of {_gbp(t['revenue_avg4'])}).")
        movers = [x for x in s["flows"] if abs(x["revenue"] - x["revenue_avg4"]) >= 50][:4]
        if movers:
            lines.append("\n*Biggest moves*")
            lines += [f"• {link(x['id'], x['name'])}: {_gbp(x['revenue'])} ({_change(x['revenue'], x['revenue_avg4'])} vs 4-week average)" for x in movers]
    else:
        lines.append("Weekly figures aren't available yet.")
    if s["stopped"]:
        lines.append("\n*Stopped sending*")
        lines += [f"• {link(x['id'], x['name'])} (averaged {x['sends_avg4']:.0f} sends a week before)" for x in s["stopped"]]
    if s["new_flags"] and not s["first_run"]:
        lines.append(f"\n*Newly flagged ({len(s['new_flags'])})*")
        lines += [f"• {link(x['flow_id'], x['flow'])}{' · ' + x['message'] if x['message'] else ''}: {x['text']}" for x in s["new_flags"][:6]]
    if s["actions"]:
        lines.append("\n*Top actions*")
        lines += [f"{n}. {link(x['flow_id'], x['flow'])}{' · ' + x['message'] if x.get('message') else ''}: {x['text']}" for n, x in enumerate(s["actions"], 1)]
    lines.append("\nRevenue is Klaviyo-attributed from Placed Order. Sends are messages delivered, not unique people.")
    return "\n".join(lines)


def send(base_url=""):
    if not config.SLACK_WEBHOOK_URL:
        raise RuntimeError("Set SLACK_WEBHOOK_URL in Railway to post the summary to Slack.")
    s = build()
    if not s:
        raise RuntimeError("No data yet: refresh from Klaviyo first.")
    r = httpx.post(config.SLACK_WEBHOOK_URL, json={"text": to_slack(s, base_url)}, timeout=20)
    if r.status_code >= 300:
        raise RuntimeError(f"Slack said {r.status_code}: {r.text[:200]}")
    now = dt.datetime.now(dt.timezone.utc)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"flags": s["_flag_keys"], "sent_at": now.isoformat(timespec="seconds"),
                                 "iso_week": now.strftime("%G-W%V")}))
    log.info("Monday summary posted to Slack")
    return s


def due():
    """Monday from 08:00 London time, once per ISO week, and only when Slack is set up."""
    if not config.SLACK_WEBHOOK_URL:
        return False
    try:
        from zoneinfo import ZoneInfo
        now = dt.datetime.now(ZoneInfo("Europe/London"))
    except Exception:
        now = dt.datetime.now(dt.timezone.utc)
    if now.weekday() != 0 or now.hour < 8:
        return False
    return _load_state().get("iso_week") != now.strftime("%G-W%V")

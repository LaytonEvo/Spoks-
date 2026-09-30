"""Builds the dashboard snapshot: flows as readable journeys, per-message performance and health checks."""
import datetime as dt
import html as htmllib
import json
import logging
import re
import threading

from . import config
from .klaviyo import KNOWN_METRICS, SERIES_STATS, get_source

SNAPSHOT = config.DATA_DIR / "snapshot.json"
RENDERS = config.DATA_DIR / "renders"
_lock = threading.Lock()
log = logging.getLogger("uvicorn.error")
status = {"running": False, "step": "", "error": None, "finished_at": None}

# Sample data used to render templates. Clearly an example basket, never a real customer.
SAMPLE_PRODUCT = {
    "title": "Motocaddy 2026 M1 DHC Standard Lithium Electric Golf Trolley",
    "vendor": "Motocaddy",
    "images": [{"src": "https://cdn.shopify.com/s/files/1/0499/9014/0061/files/2026M1DHCThumbnail.png"}],
}
SAMPLE_CONTEXT = {
    "person": {"first_name": "Sam", "email": "sam@example.com"},
    "first_name": "Sam",
    "organization": {"name": "Evolution Golf",
                     "full_address": "Unit 3, Parvenah Park, Embankment Way, Ringwood, BH24 1WL"},
    "event": {
        "$value": 799, "Items": [SAMPLE_PRODUCT["title"]], "ItemNames": [SAMPLE_PRODUCT["title"]],
        "ProductName": SAMPLE_PRODUCT["title"], "Name": SAMPLE_PRODUCT["title"], "Price": 799,
        "ImageURL": SAMPLE_PRODUCT["images"][0]["src"], "URL": "https://evolutiongolf.co.uk/",
        "Collections": ["Electric Trolleys"], "Categories": ["Electric Trolleys"],
        "extra": {
            "checkout_url": "https://evolutiongolf.co.uk/", "responsive_checkout_url": "https://evolutiongolf.co.uk/",
            "order_status_url": "https://evolutiongolf.co.uk/",
            "line_items": [{"quantity": 1, "line_price": 799, "price": 799, "title": SAMPLE_PRODUCT["title"],
                            "product": SAMPLE_PRODUCT}],
        },
    },
}

DISCOUNT_RE = re.compile(r"coupon_code|/discount/|\bcode\s+[A-Z0-9]{4,}\b|\b\d{1,2}%\s*off\b", re.I)
URGENCY_RE = re.compile(r"ends tonight|expires? (in|tomorrow|today|soon)|last chance|only \d+ (left|hours)|hurry", re.I)


TAG_RE = re.compile(r"{%.*?%}", re.S)
VAR_RE = re.compile(r"{{(.*?)}}", re.S)
DEFAULT_RE = re.compile(r"""\|\s*default\s*:\s*(['"])(.*?)\1""")


def _fill_var(match):
    expr = match.group(1)
    d = DEFAULT_RE.search(expr)
    if d:
        return d.group(2)
    name = expr.split("|")[0].strip()
    if "first_name" in name:
        return "Sam"
    return ""


def fill_tags(html):
    """Show a raw template without a profile: drop logic tags, use each variable's default text."""
    html = re.sub(r"{%\s*unsubscribe\s*(['\"])(.*?)\1\s*%}", r'<a href="#">\2</a>', html)
    html = re.sub(r"{%\s*manage_preferences\s*(['\"])(.*?)\1\s*%}", r'<a href="#">\2</a>', html)
    html = re.sub(r"{%\s*web_view\s*(['\"])(.*?)\1\s*%}", r'<a href="#">\2</a>', html)
    return VAR_RE.sub(_fill_var, TAG_RE.sub("", html))


# ---------------- labels ----------------
def _metric(mid, names):
    return names.get(mid) or KNOWN_METRICS.get(mid) or f"metric {mid}"


def _timeframe(tf):
    if not tf:
        return ""
    op = tf.get("operator")
    if op == "flow-start":
        return "since starting this flow"
    if op == "alltime":
        return "over all time"
    if op == "in-the-last":
        return f"in the last {tf.get('quantity')} {tf.get('unit')}s"
    return op or ""


def _condition(c, names):
    t = c.get("type")
    if t == "profile-metric":
        mf = c.get("measurement_filter") or {}
        op = {"equals": "=", "greater-than": ">", "greater-than-or-equal": "≥", "less-than": "<"}.get(mf.get("operator"), mf.get("operator"))
        return f"{_metric(c.get('metric_id'), names)} count {op} {mf.get('value')} {_timeframe(c.get('timeframe_filter'))}".strip()
    if t == "profile-property":
        f = c.get("filter") or {}
        prop = re.sub(r"properties\['(.+)'\]", r"\1", c.get("property", ""))
        if f.get("type") == "existence":
            return f"{prop} is {'set' if f.get('operator') in ('is-set', 'exists') else 'not set'}"
        return f"{prop} {f.get('operator')} {f.get('value')}"
    if t == "metric-property":
        f = c.get("filter") or {}
        return f"{c.get('field')} {f.get('operator')} {f.get('value')}"
    if t == "profile-marketing-consent":
        return "Can receive marketing"
    return t or "condition"


def _filter_label(flt, names, limit=4):
    if not flt:
        return ""
    groups = []
    for g in flt.get("condition_groups", []):
        conds = [_condition(c, names) for c in g.get("conditions", [])]
        if len(conds) > limit:
            conds = conds[:limit] + [f"+{len(conds) - limit} more"]
        groups.append(" or ".join(conds))
    return " and ".join(f"({g})" if " or " in g and len(groups) > 1 else g for g in groups)


def _delay_label(d):
    unit = d.get("unit", "")
    v = d.get("value")
    unit = unit[:-1] if v == 1 and unit.endswith("s") else unit
    s = f"Wait {v} {unit}"
    if d.get("delay_until_time"):
        s += f", then send at {d['delay_until_time'][:5]}"
    if d.get("delay_until_weekdays"):
        s += " (" + ", ".join(w[:3].title() for w in d["delay_until_weekdays"]) + ")"
    return s


# ---------------- journey tree ----------------
def _message_node(action, main=None):
    a = main or action
    data = a.get("data", {})
    msg = data.get("message", {})
    kind = "sms" if a["type"] == "send-sms" else "email"
    node = {
        "kind": kind, "action_id": action["id"], "message_id": msg.get("id"), "name": msg.get("name"),
        "status": data.get("status") or (action.get("data") or {}).get("status"),
        "subject": msg.get("subject_line"), "preview_text": msg.get("preview_text"),
        "from_label": msg.get("from_label"), "template_id": msg.get("template_id"), "body": msg.get("body"),
        "smart_sending": msg.get("smart_sending_enabled"), "utm": msg.get("add_tracking_params"),
        "transactional": msg.get("transactional"), "opt_out": msg.get("add_opt_out_language"),
        "org_prefix": msg.get("add_org_prefix"), "quiet_hours": msg.get("sms_quiet_hours_enabled"),
        "has_filter": bool(msg.get("additional_filters")),
    }
    return node


def _walk(start, actions, names, seen):
    steps, cur = [], start
    while cur and cur in actions and cur not in seen:
        seen.add(cur)
        a = actions[cur]
        t, data, links = a["type"], a.get("data", {}), a.get("links") or {}
        if t in ("send-email", "send-sms"):
            steps.append(_message_node(a))
        elif t == "ab-test":
            node = _message_node(a, data.get("main_action"))
            exp = data.get("current_experiment") or {}
            if exp.get("variations"):
                node["ab_test"] = {
                    "status": data.get("experiment_status"), "started": exp.get("started"),
                    "winner_metric": exp.get("winner_metric"),
                    "variations": [dict(_message_node(v), share=(exp.get("allocations") or {}).get(v["id"]))
                                   for v in exp["variations"]],
                }
            steps.append(node)
        elif t == "time-delay":
            steps.append({"kind": "delay", "label": _delay_label(data)})
        elif t == "update-profile":
            ops = data.get("profile_operations") or []
            keys = [re.sub(r"properties\['(.+)'\]", r"\1", o.get("property_key", "")) for o in ops]
            label = "; ".join(f"Set {k} = {o.get('property_value')}" for k, o in zip(keys, ops))
            steps.append({"kind": "update", "label": label or "Update profile"})
        elif t in ("conditional-split", "trigger-split"):
            flt = data.get("profile_filter") or data.get("trigger_filter")
            steps.append({"kind": "split", "split_type": t, "label": _filter_label(flt, names), "branches": [
                {"label": "Yes", "steps": _walk(links.get("next_if_true"), actions, names, seen)},
                {"label": "No", "steps": _walk(links.get("next_if_false"), actions, names, seen)},
            ]})
            break
        elif t == "multi-branch-split":
            branches = []
            for b in data.get("branches", []):
                nxt = (b.get("links") or {}).get("next")
                label = "Everyone else" if b.get("is_else") else (b.get("name") or "Path")
                cond = _filter_label(b.get("branch_filter"), names)
                branches.append({"label": label, "condition": cond, "steps": _walk(nxt, actions, names, seen)})
            steps.append({"kind": "split", "split_type": t, "label": data.get("name") or "Multi-path split",
                          "branches": branches})
            break
        else:
            steps.append({"kind": "other", "label": t})
        cur = links.get("next")
    return steps


def _iter_messages(steps):
    for s in steps:
        if s["kind"] in ("email", "sms"):
            yield s
        elif s["kind"] == "split":
            for b in s["branches"]:
                yield from _iter_messages(b["steps"])


def _paths(steps, prefix=()):
    """All linear paths of messages through the tree (for drop-off checks)."""
    path = list(prefix)
    for i, s in enumerate(steps):
        if s["kind"] in ("email", "sms"):
            path.append(s)
        elif s["kind"] == "split":
            for b in s["branches"]:
                yield from _paths(b["steps"], path)
            return
    yield path


# ---------------- health checks ----------------
def _flag(level, text):
    return {"level": level, "text": text}


def _pct(x):
    return f"{x * 100:.1f}%"


def message_flags(m, flow, tf_key):
    f = []
    st = (m.get("metrics") or {}).get(tf_key) or {}
    n = st.get("recipients") or 0
    text = " ".join(filter(None, [m.get("subject"), m.get("preview_text"), m.get("body"), m.get("_text")]))
    name = m.get("name") or ""
    trolley_or_clubs = re.search(r"troll|club", name + " " + flow["name"], re.I)
    if DISCOUNT_RE.search(text):
        code = re.search(r"coupon_code '([^']+)'|code ([A-Z0-9]{4,})|/discount/([A-Z0-9]+)", text)
        c = next((g for g in (code.groups() if code else []) if g), None)
        what = f"a discount code ({c})" if c else "a discount"
        f.append(_flag("high" if trolley_or_clubs else "medium",
                       f"Offers {what}" + (" in a trolley or clubs message" if trolley_or_clubs else "")))
    if URGENCY_RE.search(text):
        f.append(_flag("medium", "Deadline wording: check it matches a real expiry (DMCC Act)"))
    if m.get("smart_sending") is False and not m.get("transactional"):
        f.append(_flag("info", "Smart sending is off"))
    if m["kind"] == "sms":
        if m.get("opt_out") is False:
            f.append(_flag("high", "SMS has no opt-out wording"))
        if m.get("org_prefix") and (m.get("body") or "").lower().startswith("evolution golf"):
            f.append(_flag("medium", "Brand name will appear twice (prefix on and in the text)"))
    if flow["status"] == "live" and m.get("status") in ("draft", "manual"):
        f.append(_flag("medium", f"Message is set to {m['status']}, so it isn't sending"))
    if n >= 100:
        if (st.get("unsubscribe_rate") or 0) > 0.01:
            f.append(_flag("high", f"Unsubscribe rate {_pct(st['unsubscribe_rate'])} (limit 0.5%)"))
        elif (st.get("unsubscribe_rate") or 0) > 0.005:
            f.append(_flag("medium", f"Unsubscribe rate {_pct(st['unsubscribe_rate'])} (limit 0.5%)"))
        if (st.get("spam_complaint_rate") or 0) > 0.001:
            f.append(_flag("high", f"Spam complaints {st['spam_complaint_rate'] * 100:.2f}% (keep under 0.10%)"))
        if (st.get("bounce_rate") or 0) > 0.02:
            f.append(_flag("medium", f"Bounce rate {_pct(st['bounce_rate'])}"))
        if m["kind"] == "email" and (st.get("click_rate") or 0) < 0.01 and n >= 200:
            f.append(_flag("medium", f"Click rate {_pct(st.get('click_rate') or 0)} from {n:,} sends"))
    ab = m.get("ab_test")
    if ab and ab.get("status") == "live" and ab.get("started"):
        started = dt.datetime.fromisoformat(ab["started"].replace("Z", "+00:00"))
        days = (dt.datetime.now(dt.timezone.utc) - started).days
        if days > 45:
            f.append(_flag("info", f"A/B test still running after {days} days"))
    return f


def flow_flags(flow, tf_key):
    f = []
    t = flow["totals"].get(tf_key) or {}
    if flow["status"] == "live" and not t.get("recipients"):
        f.append(_flag("medium", "Live but sent nothing in this period"))
    msgs = list(_iter_messages(flow["steps"]))
    housekeeping = [
        (sum("placeholder" in (m.get("name") or "").lower() for m in msgs), "message names still say “placeholder”"),
        (sum(m["kind"] == "email" and not m.get("preview_text") and not m.get("transactional") for m in msgs), "emails have no preview text"),
        (sum(m.get("utm") is False and not m.get("transactional") for m in msgs), "messages have UTM tracking off"),
    ]
    for n, text in housekeeping:
        if n:
            f.append(_flag("info", f"{n} {text}" if n > 1 else "1 " + text.replace("names still say", "name still says").replace("emails have", "email has").replace("messages have", "message has")))
    for path in _paths(flow["steps"]):
        emails = [m for m in path if m["kind"] == "email" and (m.get("metrics") or {}).get(tf_key)]
        for a, b in zip(emails, emails[1:]):
            ra = a["metrics"][tf_key].get("recipients") or 0
            rb = b["metrics"][tf_key].get("recipients") or 0
            if ra >= 100 and rb < 0.5 * ra:
                f.append(_flag("medium", f"Only {rb / ra:.0%} of “{a['name']}” recipients got “{b['name']}”"))
    seen, out = set(), []
    for x in f:
        if x["text"] not in seen:
            seen.add(x["text"])
            out.append(x)
    return out


# ---------------- build ----------------
def _plain_text(html):
    html = re.sub(r"(?is)<(style|script|head)[^>]*>.*?</\1>", " ", html or "")
    txt = htmllib.unescape(re.sub(r"(?s)<[^>]+>", " ", html))
    return re.sub(r"\s+", " ", txt).strip()


def _totals(msgs, tf):
    rec = sum((m.get("metrics", {}).get(tf) or {}).get("recipients") or 0 for m in msgs)
    if not rec:
        return {"recipients": 0}

    def wavg(k):
        return sum(((m.get("metrics", {}).get(tf) or {}).get(k) or 0) * ((m.get("metrics", {}).get(tf) or {}).get("recipients") or 0) for m in msgs) / rec

    rev = sum((m.get("metrics", {}).get(tf) or {}).get("conversion_value") or 0 for m in msgs)
    email_msgs = [m for m in msgs if m["kind"] == "email"]
    erec = sum((m.get("metrics", {}).get(tf) or {}).get("recipients") or 0 for m in email_msgs)
    open_rate = (sum(((m.get("metrics", {}).get(tf) or {}).get("open_rate") or 0) * ((m.get("metrics", {}).get(tf) or {}).get("recipients") or 0) for m in email_msgs) / erec) if erec else None
    return {
        "recipients": rec, "revenue": round(rev, 2), "revenue_per_recipient": rev / rec,
        "conversions": sum((m.get("metrics", {}).get(tf) or {}).get("conversions") or 0 for m in msgs),
        "open_rate": open_rate, "click_rate": wavg("click_rate"), "conversion_rate": wavg("conversion_rate"),
        "unsubscribe_rate": wavg("unsubscribe_rate"),
    }


def _trigger_label(defn, names, src):
    trig = (defn.get("triggers") or [{}])[0]
    t = trig.get("type")
    if t == "metric":
        s = f"When someone triggers “{_metric(trig.get('id'), names)}”"
        if trig.get("trigger_filter"):
            s += f" where {_filter_label(trig['trigger_filter'], names)}"
        return s
    if t in ("list", "segment"):
        nm = src.audience_name(t, trig.get("id"))
        return f"When someone joins the {t} “{nm}”" if nm else f"When someone joins {t} {trig.get('id')}"
    return t or "Unknown trigger"


def _include(flow):
    a = flow["attributes"]
    return a["status"] in ("live", "manual") or a["name"].startswith(config.DRAFT_PREFIXES)


def build():
    """Fetch from Klaviyo (or fixtures) and write snapshot.json. Runs in a background thread."""
    if not _lock.acquire(blocking=False):
        return
    status.update(running=True, error=None, step="Listing flows")
    log.info("Refresh started (%s)", "fixtures" if config.USE_FIXTURES else "klaviyo")
    try:
        src = get_source()
        RENDERS.mkdir(parents=True, exist_ok=True)
        names = src.metrics()
        reports = {}
        for tf in config.TIMEFRAMES:
            status["step"] = f"Reading performance ({tf.replace('_', ' ')})"
            try:
                rows = src.flow_report(tf)
            except Exception as e:  # one period failing (e.g. the daily report quota) shouldn't lose the rest
                log.warning("Performance report for %s failed: %s", tf, str(e)[:300])
                continue
            if rows is not None:
                reports[tf] = {r["groupings"]["flow_message_id"]: r["statistics"] for r in rows}
        weeks, weekly = [], {}
        status["step"] = "Reading week-by-week performance"
        try:
            weeks, rows = src.flow_series()
            for r in rows:
                mid = r["groupings"].get("flow_message_id")
                st = r.get("statistics") or {}
                if not mid or not any(st.get("recipients") or []):
                    continue
                cur = weekly.setdefault(mid, {})
                for k in SERIES_STATS:  # a message can come back once per channel; add them
                    vals = [round(v or 0, 2) for v in (st.get(k) or [0] * len(weeks))]
                    cur[k] = [a + b for a, b in zip(cur[k], vals)] if k in cur else vals
        except Exception as e:  # trends are extra; the rest of the dashboard still works without them
            log.warning("Week-by-week report failed: %s", str(e)[:300])
        flows = []
        listed = [f for f in src.flows() if _include(f)]
        for i, f in enumerate(listed, 1):
            status["step"] = f"Reading flow {i} of {len(listed)}: {f['attributes']['name']}"
            full = src.flow(f["id"])
            a = full["attributes"]
            defn = a.get("definition") or {}
            actions = {x["id"]: x for x in defn.get("actions", [])}
            steps = _walk(defn.get("entry_action_id") or (defn.get("actions") or [{}])[0].get("id"), actions, names, set())
            flow = {"id": full["id"], "name": a["name"], "status": a["status"], "trigger_type": a.get("trigger_type"),
                    "updated": a.get("updated"), "trigger": _trigger_label(defn, names, src),
                    "flow_filter": _filter_label(defn.get("profile_filter"), names),
                    "reentry": defn.get("reentry_criteria"), "steps": steps}
            msgs = list(_iter_messages(steps))
            for m in msgs:
                m["metrics"] = {tf: rep.get(m["message_id"]) for tf, rep in reports.items() if rep.get(m["message_id"])}
                if weekly.get(m["message_id"]):
                    m["weekly"] = weekly[m["message_id"]]
                for v in (m.get("ab_test") or {}).get("variations", []):
                    v["metrics"] = {tf: rep.get(v["message_id"]) for tf, rep in reports.items() if rep.get(v["message_id"])}
                    if weekly.get(v["message_id"]):
                        v["weekly"] = weekly[v["message_id"]]
                if m["kind"] == "email" and m.get("template_id"):
                    status["step"] = f"Rendering “{m['name']}”"
                    html = ""
                    try:
                        html = src.render(m["template_id"], SAMPLE_CONTEXT)
                    except Exception as e:  # a broken template shouldn't stop the refresh
                        if "profile is required" in str(e):
                            # Klaviyo won't render some templates without a real profile; we never use one.
                            try:
                                html = fill_tags(src.template_html(m["template_id"]))
                                m["render_mode"] = "unpersonalised"
                            except Exception as e2:
                                m["render_error"] = str(e2)[:300]
                        else:
                            m["render_error"] = str(e)[:300]
                        if m.get("render_error"):
                            log.warning("Render failed for %s: %s", m["message_id"], m["render_error"])
                    if html:
                        (RENDERS / f"{m['message_id']}.html").write_text(html)
                        m["rendered"] = True
                        m["_text"] = _plain_text(html)[:4000]
            flow["totals"] = {tf: _totals(msgs, tf) for tf in reports}
            flow["flags"] = {tf: flow_flags(flow, tf) for tf in reports}
            for m in msgs:
                m["flags"] = {tf: message_flags(m, flow, tf) for tf in reports}
            flows.append(flow)
        order = {"live": 0, "manual": 1, "draft": 2}
        flows.sort(key=lambda x: (order.get(x["status"], 3), -((x["totals"].get("last_90_days") or {}).get("revenue") or 0)))
        snap = {"generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "source": "fixtures" if config.USE_FIXTURES else "klaviyo",
                "timeframes": list(reports), "weeks": [w[:10] for w in weeks], "flows": flows}
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = SNAPSHOT.with_suffix(".tmp")
        tmp.write_text(json.dumps(snap, ensure_ascii=False))
        tmp.replace(SNAPSHOT)
        status.update(step="Done", finished_at=snap["generated_at"])
        log.info("Refresh done: %d flows, periods %s", len(flows), ", ".join(reports) or "none")
    except Exception as e:
        status.update(error=str(e), step="Failed")
        log.exception("Refresh failed at step: %s", status.get("step"))
    finally:
        status["running"] = False
        _lock.release()


def load():
    if SNAPSHOT.exists():
        return json.loads(SNAPSHOT.read_text())
    return None

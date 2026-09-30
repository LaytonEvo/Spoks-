"""Recommended fixes that Layton approves in the dashboard, then the app applies to Klaviyo.

Allowed changes (Layton, 30 Sep 2026): edit the text of existing email templates for two fixes only,
  1. the hard-coded unsubscribe link (replace with Klaviyo's tag, add a manage-preferences link),
  2. deadline claims that may not be true (remove or reword the sentence).
Never: change a flow's status, its structure or timing, send anything, or touch profiles.
Anything the API can't change (subject lines, SMS text) becomes a manual to-do card.

Each fix stores the template exactly as it was, so it can be undone, and refuses to apply
if the template has changed in Klaviyo since the fix was proposed.
"""
import copy
import datetime as dt
import hashlib
import html as htmllib
import json
import logging
import re
import threading

from . import config, snapshot
from .klaviyo import KlaviyoError, LiveSource, WriteClient

log = logging.getLogger("uvicorn.error")
STORE = config.DATA_DIR / "fixes"
_lock = threading.Lock()
scan_status = {"running": False, "step": "", "error": None, "finished_at": None}

UNSUB_A = re.compile(r'<a\b[^>]*href="(https://manage\.kmail-lists\.com/subscriptions/unsubscribe[^"]*)"[^>]*>(.*?)</a>', re.S | re.I)
DEADLINE = re.compile(r"\b(expires?|expiring|expiry|ends tonight|ends today|ends soon|last chance|final hours|only \d+ (?:hours?|days?) left|hurry)\b", re.I)
STATIC_CODE = re.compile(r"\b(EVO5|TROLLEY10|SMSCLUB5|BASKET5|BASKET10|WINBACK5)\b")


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _walk_strings(obj, fn):
    """Apply fn to every string inside a template definition (text blocks, html blocks, button text...)."""
    if isinstance(obj, dict):
        return {k: _walk_strings(v, fn) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk_strings(v, fn) for v in obj]
    if isinstance(obj, str):
        return fn(obj)
    return obj


def _strings(obj):
    out = []
    _walk_strings(obj, lambda s: out.append(s) or s)
    return out


# ---------- transforms (the same function edits the definition and the preview html) ----------
def unsub_transform(s):
    def rep(m):
        a = m.group(0).replace(m.group(1), "{% unsubscribe_link %}")
        if "manage_preferences" in s:
            return a
        style = re.search(r'style="([^"]*)"', m.group(0))
        inner = re.sub(r"(?i)unsubscribe", "Manage preferences", m.group(2), count=1)
        if inner == m.group(2):
            inner = "Manage preferences"
        return a + f' <a href="{{% manage_preferences_link %}}"{f" style={chr(34)}{style.group(1)}{chr(34)}" if style else ""}>{inner}</a>'
    return UNSUB_A.sub(rep, s)


def sentence_transform(find, replace):
    def fn(s):
        return s.replace(find, replace)
    return fn


def _visible_text(fragment):
    return htmllib.unescape(re.sub(r"<[^>]+>", "", fragment or "")).strip()


def _deadline_sentences(strings):
    """Plain sentences inside text content that make a deadline claim."""
    found = []
    for s in strings:
        if "<" not in s and len(s) > 400:
            continue
        for chunk in re.findall(r">([^<>]{8,})<", s if s.startswith("<") else f">{s}<"):
            text = chunk.strip()
            if DEADLINE.search(htmllib.unescape(text)) and "{%" not in text and "{{" not in text:
                for sent in re.split(r"(?<=[.!?])\s+", text):
                    if DEADLINE.search(htmllib.unescape(sent)) and sent not in found:
                        found.append(sent)
    return found


def _suggest(sentence):
    """A neutral rewording: drop the deadline clause, keep the instruction if there is one."""
    plain = htmllib.unescape(sentence)
    parts = re.split(r"\s*(?:,|\band\b)\s*", plain)
    keep = [p for p in parts if p and not DEADLINE.search(p) and not re.search(r"one-time use|only valid", p, re.I)]
    out = " ".join(keep).strip()
    if out and not out.endswith((".", "!", "?")):
        out += "."
    return out[0].upper() + out[1:] if out else ""


# ---------- store ----------
def _path(fid):
    return STORE / f"{fid}.json"


def load_all():
    if not STORE.exists():
        return []
    items = [json.loads(p.read_text()) for p in STORE.glob("*.json")]
    order = {"proposed": 0, "manual": 1, "applied": 2, "done": 3, "verified": 3, "failed": 0, "reverted": 4, "dismissed": 5}
    kind_order = {"unsubscribe": 0, "deadline": 1, "text": 2}
    return sorted(items, key=lambda x: (order.get(x["status"], 9), kind_order.get(x["kind"], 5), -(x.get("open") or 0)))


def get(fid):
    p = _path(fid)
    return json.loads(p.read_text()) if p.exists() else None


def _save(fix):
    STORE.mkdir(parents=True, exist_ok=True)
    _path(fix["id"]).write_text(json.dumps(fix, ensure_ascii=False))


def _hist(fix, who, action, detail=""):
    fix.setdefault("history", []).append({"at": _now(), "by": who, "action": action, "detail": detail})


def public(fix):
    """What the browser sees (no full template bodies)."""
    return {k: v for k, v in fix.items() if k not in ("before", "after_preview", "before_preview")}


# ---------- scan ----------
def _fingerprint(tpl):
    body = json.dumps(tpl.get("definition"), sort_keys=True) if tpl.get("definition") else (tpl.get("html") or "")
    return hashlib.sha256(body.encode()).hexdigest()


def _upsert(fix):
    old = get(fix["id"])
    if old and old["status"] not in ("proposed", "failed"):
        return  # already decided; keep its record
    if old:
        fix["history"] = old.get("history", [])
        fix["created_at"] = old["created_at"]
    _save(fix)


KLAVIYO_FLOW = "https://www.klaviyo.com/flow/{}/edit"
STEPS = {
    "unsubscribe": [
        "Open the flow in Klaviyo and click into each email listed below.",
        "In the footer, select the words “Unsubscribe.” and edit the link.",
        "Replace the long manage.kmail-lists.com address with exactly: {% unsubscribe_link %}",
        "Type “ Manage preferences.” after it, select it, and set its link to exactly: {% manage_preferences_link %}",
        "Save the email. Preview it in Klaviyo: both links should still be white on the green footer.",
        "Quicker for the future: save the fixed footer as a universal content block and use it in every email.",
    ],
    "deadline": [
        "Only change these if the code does NOT really expire as the email says (check the coupon's settings in Klaviyo).",
        "Open each email listed below and replace the sentence with the suggested wording (or your own).",
        "Save the email.",
    ],
    "text": [
        "Only change these if the deadline isn't real (check the coupon's settings in Klaviyo).",
        "Open the message listed below in the flow and edit the subject line, preview text or SMS text shown.",
        "Save the message.",
    ],
}
TITLES = {"unsubscribe": "Fix the broken unsubscribe link", "deadline": "Check deadline claims in the email text",
          "text": "Check deadline claims in subject lines, preview text and SMS"}
WHY = {
    "unsubscribe": "The footer links to one specific person's unsubscribe page, so anyone else who clicks it isn't unsubscribed. "
                   "That's a compliance risk and pushes people to the spam button instead.",
    "deadline": "Under the DMCC Act a deadline must be real. These sentences promise an expiry; if the code doesn't really expire that way, "
                "they need rewording.",
    "text": "Under the DMCC Act a deadline must be real. These lines promise an expiry or last chance; reword any that aren't true.",
}


def _group_id(kind, flow_id):
    return f"{kind}-{flow_id}"


def scan():
    """Read every email in the current flows (read-only) and group what needs fixing by flow.

    Klaviyo doesn't let apps edit emails inside flows (checked 30 Sep 2026: even a no-op change is refused),
    so every card is a to-do for the Klaviyo editor. Rescanning checks each item and marks it fixed when the
    problem has gone.
    """
    if not _lock.acquire(blocking=False):
        return
    scan_status.update(running=True, error=None, step="Reading templates")
    try:
        snap = snapshot.load() or {"flows": []}
        if config.USE_FIXTURES:
            raise RuntimeError("Scanning needs the live Klaviyo connection (it reads each template).")
        src = LiveSource()
        seen, unread, found = {}, [], {}
        msgs = []
        for f in snap["flows"]:
            for m in snapshot._iter_messages(f["steps"]):
                msgs.append((f, m))
                for v in (m.get("ab_test") or {}).get("variations", []):
                    msgs.append((f, dict(v, name=f"{m['name']} (variation)")))

        def add(kind, f, item, preview=None):
            g = found.setdefault(_group_id(kind, f["id"]), {"kind": kind, "flow": f, "items": [], "preview": None})
            g["items"].append(item)
            if preview and not g["preview"]:
                g["preview"] = preview

        emails = [(f, m) for f, m in msgs if m["kind"] == "email" and m.get("template_id")]
        for i, (f, m) in enumerate(emails, 1):
            tid = m["template_id"]
            scan_status["step"] = f"Checking email {i} of {len(emails)}"
            if tid not in seen:
                try:
                    seen[tid] = src.template_full(tid)
                except KlaviyoError as e:
                    log.warning("Scan could not read template %s: %s", tid, str(e)[:200])
                    unread.append(str(e))
                    seen[tid] = None
            tpl = seen[tid]
            if not tpl:
                continue
            source = tpl.get("definition") or tpl.get("html") or ""
            strings = _strings(source) if isinstance(source, dict) else [source]
            base = {"message": m.get("name"), "message_id": m.get("message_id"), "template_id": tid}
            if any(UNSUB_A.search(x) for x in strings):
                html = tpl.get("html") or ""
                add("unsubscribe", f, dict(base, key=f"u-{tid}", detail="Footer unsubscribe link"),
                    preview={"before": html, "after": unsub_transform(html)})
            codes = sorted(set(STATIC_CODE.findall(" ".join(strings))))
            for sent in _deadline_sentences(strings):
                text = _visible_text(sent)
                add("deadline", f, dict(base, key=f"d-{tid}-{hashlib.sha1(sent.encode()).hexdigest()[:8]}",
                                        detail=text, suggestion=_visible_text(_suggest(sent)) or "(remove the sentence)",
                                        codes=codes))
        for f, m in msgs:
            for field, label in (("subject", "Subject line"), ("preview_text", "Preview text"), ("body", "SMS text")):
                val = m.get(field) or ""
                if val and DEADLINE.search(val):
                    add("text", f, {"message": m.get("name"), "message_id": m.get("message_id"),
                                    "key": f"t-{m.get('message_id')}-{field}", "detail": f"{label}: “{val[:300]}”"})

        # Merge into stored cards: new items added, items no longer found marked fixed.
        existing = {x["id"]: x for x in load_all() if "items" in x}
        for old in load_all():
            if "items" not in old and old["status"] in ("proposed", "failed", "manual"):
                _path(old["id"]).unlink(missing_ok=True)  # cards from the first version of this page
        now = _now()
        for gid in set(existing) | set(found):
            card = existing.get(gid)
            g = found.get(gid)
            if card is None:
                f = g["flow"]
                card = {"id": gid, "kind": g["kind"], "status": "proposed", "created_at": now, "flow_id": f["id"],
                        "flow": f["name"], "flow_status": f["status"], "title": TITLES[g["kind"]], "why": WHY[g["kind"]],
                        "steps": STEPS[g["kind"]], "klaviyo_url": KLAVIYO_FLOW.format(f["id"]), "items": []}
            live = {it["key"]: it for it in (g["items"] if g else [])}
            by_key = {it["key"]: it for it in card["items"]}
            for k, it in live.items():
                if k in by_key:
                    by_key[k].update(it, fixed=False)
                else:
                    card["items"].append(dict(it, fixed=False, first_seen=now))
            for k, it in by_key.items():
                if k not in live and not it.get("fixed") and not any(u for u in unread):
                    it.update(fixed=True, fixed_seen=now)
            if g and g["preview"]:
                card["before_preview"], card["after_preview"] = g["preview"]["before"], g["preview"]["after"]
            open_items = [it for it in card["items"] if not it.get("fixed")]
            card["open"], card["total"] = len(open_items), len(card["items"])
            if not open_items and card["status"] in ("proposed", "manual"):
                card["status"] = "verified"
                _hist(card, "scan", "verified", "Rescan found every item fixed in Klaviyo.")
            elif open_items and card["status"] == "verified":
                card["status"] = "manual"
                _hist(card, "scan", "reopened", "Rescan found the problem again.")
            _save(card)
        if unread:
            scan_status["error"] = (f"Couldn't read {len(unread)} of {len(seen)} templates, so this scan is incomplete. "
                                    f"First error: {unread[0][:200]}")
        scan_status.update(step="Done", finished_at=_now())
        log.info("Fix scan done: %d templates, %d unreadable, %d cards", len(seen), len(unread), len(found))
    except Exception as e:
        scan_status.update(error=str(e)[:300], step="Failed")
        log.exception("Fix scan failed")
    finally:
        scan_status["running"] = False
        _lock.release()


def start_scan():
    if not scan_status["running"]:
        threading.Thread(target=scan, daemon=True).start()


# ---------- decisions ----------
def _transform_for(fix):
    if fix["kind"] == "unsubscribe":
        return unsub_transform
    if fix["kind"] == "deadline":
        return sentence_transform(fix["find"], fix["replace"])
    raise ValueError("This kind of fix isn't applied automatically.")


_key_check = {}


def key_check(force=False):
    """Make sure the write key is for the same Klaviyo account as the read key, before any write."""
    if _key_check and not force:
        return _key_check
    out = {"ok": False, "message": ""}
    try:
        rid, rname = LiveSource().account()
    except Exception as e:
        out["message"] = f"Couldn't identify the read key's account: {str(e)[:200]}"
        _key_check.update(out)
        return out
    try:
        wid, wname = WriteClient().account()
    except Exception as e:
        msg = str(e)
        hint = " Give the write key 'Accounts: read' as well as 'Templates: read + write'." if "403" in msg else ""
        out["message"] = f"Couldn't identify the write key's account.{hint} ({msg[:200]})"
        _key_check.update(out)
        return out
    out.update(read_account=f"{rname or '?'} ({rid})", write_account=f"{wname or '?'} ({wid})", ok=rid == wid)
    if out["ok"]:
        # Same account; can the write key actually see a flow email's template?
        snap = snapshot.load() or {"flows": []}
        tid = next((m.get("template_id") for f in snap["flows"] if f["status"] == "live"
                    for m in snapshot._iter_messages(f["steps"]) if m.get("template_id")), None)
        if tid:
            try:
                WriteClient().template_full(tid)
            except Exception as e:
                out["ok"] = False
                out["message"] = ("The write key is in the right account but can't see the templates inside your flows "
                                  f"(Klaviyo: {str(e)[:120]}). Give it Flows: Read access as well as Templates: Full and Accounts: Read.")
    elif not out["ok"]:
        out["message"] = (f"The write key belongs to a different Klaviyo account ({wname or '?'}, {wid}) than the one "
                          f"the dashboard reads ({rname or '?'}, {rid}). Create the write key in the {rname or 'same'} account.")
    _key_check.clear()
    _key_check.update(out)
    return out


def apply(fid, who, replace=None):
    fix = get(fid)
    if not fix:
        raise KeyError(fid)
    if fix["kind"] in ("manual", "unsubscribe", "deadline", "text") and "items" in fix or fix["kind"] == "manual":
        fix["status"] = "manual"
        _hist(fix, who, "approved", "Added to the Klaviyo to-do list")
        _save(fix)
        return fix
    if fix["status"] not in ("proposed", "failed"):
        raise ValueError(f"Already {fix['status']}.")
    if fix["kind"] == "deadline" and replace is not None:
        fix["replace"] = replace.strip()[:500]
    if not config.KLAVIYO_WRITE_KEY:
        raise RuntimeError("Add KLAVIYO_WRITE_KEY in Railway (a Klaviyo key with Templates write access) to apply fixes.")
    kc = key_check()
    if not kc["ok"]:
        key_check(force=True)  # the key may have been fixed since; check again once
        if not _key_check["ok"]:
            raise RuntimeError(_key_check["message"])
    w = WriteClient()
    current = w.template_full(fix["template_id"])
    if _fingerprint(current) != fix["template_fingerprint"]:
        fix["status"] = "failed"
        _hist(fix, who, "refused", "The template changed in Klaviyo since this fix was proposed. Scan again for a fresh proposal.")
        _save(fix)
        raise RuntimeError("The template changed in Klaviyo since this fix was proposed. Scan again, then approve the fresh card.")
    t = _transform_for(fix)
    try:
        if current.get("definition"):
            new_def = _walk_strings(copy.deepcopy(current["definition"]), t)
            if new_def == current["definition"]:
                raise RuntimeError("Nothing to change: the text wasn't found in the template.")
            w.update_template(fix["template_id"], definition=new_def)
        else:
            new_html = t(current.get("html") or "")
            if new_html == current.get("html"):
                raise RuntimeError("Nothing to change: the text wasn't found in the template.")
            w.update_template(fix["template_id"], html=new_html)
        after = w.template_full(fix["template_id"])
        ok = _verify(fix, after)
        fix["status"] = "applied" if ok else "failed"
        fix["applied_fingerprint"] = _fingerprint(after)
        fix["after_preview"] = after.get("html") or fix.get("after_preview")
        _hist(fix, who, "applied" if ok else "failed", "Checked in Klaviyo after saving." if ok else "Saved, but the check afterwards didn't find the change.")
    except Exception as e:
        fix["status"] = "failed"
        _hist(fix, who, "failed", str(e)[:300])
        _save(fix)
        raise
    _save(fix)
    if fix["status"] == "applied":
        _rebase_siblings(fix, after)
    log.info("Fix %s %s by %s", fid, fix["status"], who)
    return fix


def _rebase_siblings(fix, tpl):
    """Other pending fixes on the same template now start from the updated version."""
    for other in load_all():
        if other["id"] == fix["id"] or other.get("template_id") != fix["template_id"] or other["status"] not in ("proposed", "failed"):
            continue
        other.update(before=tpl, template_fingerprint=_fingerprint(tpl), before_preview=tpl.get("html") or "", status="proposed")
        other["after_preview"] = _transform_for(other)(other["before_preview"])
        _save(other)


def _verify(fix, tpl):
    text = json.dumps(tpl.get("definition")) if tpl.get("definition") else (tpl.get("html") or "")
    if fix["kind"] == "unsubscribe":
        return "unsubscribe_link" in text and "subscriptions/unsubscribe?" not in text
    if fix["kind"] == "deadline":
        return json.dumps(fix["find"])[1:-1] not in text and fix["find"] not in text
    return False


def revert(fid, who):
    fix = get(fid)
    if not fix or fix["status"] != "applied":
        raise ValueError("Only applied fixes can be undone.")
    w = WriteClient()
    current = w.template_full(fix["template_id"])
    if _fingerprint(current) != fix.get("applied_fingerprint"):
        raise RuntimeError("The template has changed since this fix (in Klaviyo, or by a later fix here), so undoing it here could lose those edits. Undo the later fix first, or change it in Klaviyo.")
    before = fix["before"]
    if before.get("definition"):
        w.update_template(fix["template_id"], definition=before["definition"])
    else:
        w.update_template(fix["template_id"], html=before.get("html") or "")
    fix["status"] = "reverted"
    _hist(fix, who, "undone", "Template put back as it was.")
    _save(fix)
    return fix


def dismiss(fid, who, note=""):
    fix = get(fid)
    if not fix:
        raise KeyError(fid)
    fix["status"] = "dismissed"
    _hist(fix, who, "dismissed", note[:300])
    _save(fix)
    return fix


def done(fid, who):
    fix = get(fid)
    if not fix or fix["status"] != "manual":
        raise ValueError("Only to-do items can be ticked off.")
    fix["status"] = "done"
    _hist(fix, who, "done in Klaviyo")
    _save(fix)
    return fix

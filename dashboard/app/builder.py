"""Email builder for Evoflows templates: edit an approved email's text, move/remove/duplicate its blocks, add brand blocks
from a library, preview it as different customers, then draft -> approve -> publish (PUT /templates/{key}).

Blocks are the rows of the email's 600px card, cut losslessly from the template, so the design can't drift: you edit
words, not layout. Personalisation and conditions ({{ ... }}) are locked: a saved block must carry exactly the same
template tokens as the block it came from. Every version is kept with who saved, approved and published it; restoring is
publishing an earlier version. Nothing here switches a flow on or sends to customers (tests go to staff addresses only).
"""
import datetime as dt
import html as htmllib
import json
import re
import threading

from . import config, evoflows

STORE = config.DATA_DIR / "builder"
OUT = evoflows.OUT
_lock = threading.Lock()

TOK = re.compile(r"\{\{.*?\}\}", re.S)
SPLIT = re.compile(r"(<table\b|</table>|</tr>|\{\{-?\s*(?:if|range|with)\b.*?\}\}|\{\{-?\s*end\s*-?\}\})", re.S)
SEG = re.compile(r"(<[^>]+>|\{\{.*?\}\})", re.S)
BUTTON_SIG = "display:inline-block;padding:15px 30px"
PANEL_SIG = 'bgcolor="#F1F3F1"'
IMG_SRC = re.compile(r'<img[^>]+src="([^"]*)"', re.I)
CODE_RE = re.compile(r"coupon_code|discount_code|/discount/|\bcode\s+[A-Z0-9]{4,}\b")
URGENCY_RE = re.compile(r"ends tonight|expires? (in|tomorrow|today|soon)|last chance|only \d+ (left|hours)|hurry|don't miss out", re.I)
ALLOWED_IMG = ("https://cdn.shopify.com/", "https://evolutiongolf.co.uk/")
SENDERS = ["⛳ Evolution Golf", "Alex at Evolution Golf"]


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# ---------------- splitting ----------------
def split(html):
    """(head, blocks, tail): blocks are the card's top-level rows; a top-level {{ if }}…{{ end }} stays with its rows."""
    i = html.find('class="card"')
    if i < 0:
        raise ValueError("not an editorial email (no card)")
    start = html.find(">", i) + 1
    depth, tpl, cur, end, blocks = 1, 0, start, None, []
    for m in SPLIT.finditer(html, start):
        t = m.group(0)
        if t.startswith("<table"):
            depth += 1
        elif t == "</table>":
            depth -= 1
            if depth == 0:
                end = m.start()
                break
        elif depth == 1 and t == "</tr>" and tpl == 0:
            blocks.append(html[cur:m.end()])
            cur = m.end()
        elif depth == 1 and t.startswith("{{"):
            if re.match(r"\{\{-?\s*end", t):
                tpl -= 1
                if tpl == 0:
                    blocks.append(html[cur:m.end()])
                    cur = m.end()
            else:
                tpl += 1
    if end is None:
        raise ValueError("card not closed")
    if html[cur:end].strip():
        blocks.append(html[cur:end])
        cur = end
    return html[:start], blocks, html[cur:]


def tokens(s):
    return sorted(TOK.findall(s))


# ---------------- labels ----------------
GO_FIELD = {"is_annual": "annual member", "is_free_member": "Free member", "is_member": "member (Free or annual)",
            "has_trolley": "has a trolley", "has_motocaddy_trolley": "has a Motocaddy trolley", "has_clubs": "has clubs",
            "has_used_clubs": "has used clubs", "has_hardware": "has a trolley, clubs or used clubs", "has_shoes": "has shoes",
            "first_name": "we have their first name", "items": "the basket has items", "preferences_url": "a preferences page exists"}


def go_label(expr):
    e = expr.strip()
    if e.startswith("not "):
        return "not " + go_label(e[4:])
    m = re.fullmatch(r"\(?(or|and) (.+?)\)?", e)
    if m and m.group(0).startswith(("(or", "(and", "or ", "and ")):
        parts = re.findall(r"\.[\w.]+|\([^)]*\)", m.group(2))
        return f" {m.group(1)} ".join(go_label(p) for p in parts)
    name = e.split(".")[-1].strip("()")
    return GO_FIELD.get(name, name.replace("_", " "))


def block_meta(b):
    s = b.lstrip()
    conds = []
    while True:
        m = re.match(r"\{\{-?\s*if (.+?)\s*-?\}\}", s, re.S)
        if not m:
            break
        conds.append(go_label(m.group(1)))
        s = s[m.end():].lstrip()
    text = re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>|\{\{.*?\}\}", " ", b))).strip()
    kind = ("Footer" if ".Tx.Data.unsubscribe_url" in b else "Header" if "eg-email-logo" in b else
            "Product from the basket" if "range .Tx.Data.items" in b or ".Tx.Data.order.first_item" in b else
            "Membership offer" if "Evolution Golf Membership" in text else
            "Button" if BUTTON_SIG in b and len(text) < 40 else "Panel" if PANEL_SIG in b else
            "Photo" if "<img" in b and len(text) < 40 else "Benefits table" if "width=\"44%\"" in b else
            "Text" if text else "Spacing")
    return {"only_if": " and ".join(conds), "kind": kind, "summary": text[:90], "buttons": b.count(BUTTON_SIG),
            "panels": b.count(PANEL_SIG)}


def segments(b):
    """The block as [kind, value] parts: "tag" and control tokens are locked; "text" is editable; "tok" shows as a chip."""
    out = []
    for part in SEG.split(b):
        if not part:
            continue
        if part.startswith("<"):
            out.append(["tag", part])
        elif part.startswith("{{"):
            ctl = re.match(r"\{\{-?\s*(if|else|end|range|with)\b", part)
            out.append(["ctl" if ctl else "tok", part])
        elif part.strip():
            out.append(["text", part])
        else:
            out.append(["tag", part])
    return out


TOK_LABEL = {".Tx.Data.first_name": "first name", ".title": "product name", ".qty": "quantity", ".line_total": "line price",
             ".price": "price", ".Tx.Data.total": "basket total", ".Tx.Data.order.first_item.title": "product name",
             ".image": "product photo", ".Tx.Data.recovery_url": "basket link", ".Tx.Data.unsubscribe_url": "unsubscribe link"}


def tok_label(t):
    inner = t.strip("{} ").strip()
    if "(index .Tx.Data.items 0).title" in inner:
        return "product name"
    return TOK_LABEL.get(inner, inner.replace(".Tx.Data.", "").replace("_", " "))


# ---------------- preview: a small renderer for the Go-template subset our emails use ----------------
SAMPLE_ITEM = {"title": "Motocaddy 2026 M1 DHC Standard Lithium Electric Golf Trolley", "qty": "1", "price": "799.00",
               "line_total": "799.00", "url": "https://evolutiongolf.co.uk/",
               "image": "https://cdn.shopify.com/s/files/1/0499/9014/0061/files/2026M1DHCThumbnail.png"}


def sample(audience="non", name=True):
    return {"first_name": "Sam" if name else "", "items": [SAMPLE_ITEM], "total": "799.00", "recovery_url": "#",
            "unsubscribe_url": "#", "preferences_url": "", "is_annual": audience == "annual",
            "is_free_member": audience == "free", "is_member": audience != "non", "has_trolley": True,
            "has_motocaddy_trolley": True, "has_hardware": True, "has_clubs": False, "has_used_clubs": False, "has_shoes": False,
            "order": {"first_item": {"title": SAMPLE_ITEM["title"], "image": SAMPLE_ITEM["image"], "url": "#"}, "total": 799.0,
                      "age_days": 4, "source": "web"}}


def _lookup(path, data, dot):
    if path == ".":
        return dot
    base, parts = (data, path[len(".Tx.Data."):].split(".")) if path.startswith(".Tx.Data.") else (dot, path[1:].split("."))
    v = base
    for p in parts:
        v = v.get(p) if isinstance(v, dict) else None
    return v


def _eval(expr, data, dot):
    e = expr.strip()
    if e.startswith("(") and e.endswith(")") and e.count("(") == 1:
        e = e[1:-1].strip()
    m = re.fullmatch(r"\(index (\.[\w.]+) (\d+)\)\.(\w+)", e)
    if m:
        lst = _lookup(m.group(1), data, dot) or []
        i = int(m.group(2))
        return (lst[i] if i < len(lst) else {}).get(m.group(3))
    if e.startswith("not "):
        return not _eval(e[4:], data, dot)
    m = re.fullmatch(r"(or|and) (.+)", e)
    if m:
        vals = [_eval(p, data, dot) for p in re.findall(r"\([^()]*\)|\.[\w.]+", m.group(2))]
        return any(vals) if m.group(1) == "or" else all(vals)
    return _lookup(e, data, dot)


def render(tpl, data):
    """Render our templates' Go subset: values, if / else if / else / end, range, with, (index …), not, or, and."""
    parts = re.split(r"(\{\{.*?\}\})", tpl, flags=re.S)
    pos = 0

    def block(dot, stop=("end",)):
        nonlocal pos
        out = []
        while pos < len(parts):
            p = parts[pos]
            pos += 1
            if not p.startswith("{{"):
                out.append(p)
                continue
            inner = p[2:-2].strip().strip("-").strip()
            word = inner.split(" ", 1)[0]
            if word in ("end", "else") and word in stop or inner.startswith("else") and "else" in stop:
                return "".join(out), inner
            if word == "if":
                cond = inner[3:]
                branches, chosen = [], None
                while True:
                    body, ended = block(dot, ("end", "else"))
                    if chosen is None and (cond is None or _eval(cond, data, dot)):
                        chosen = body
                    if ended == "end":
                        break
                    cond = ended[8:] if ended.startswith("else if") else None
                out.append(chosen or "")
            elif word == "range":
                lst = _eval(inner[6:], data, dot) or []
                start, body = pos, ""
                if not lst:
                    block(None, ("end",))  # skip the body
                for item in lst:
                    pos = start
                    piece, _ = block(item, ("end",))
                    body += piece
                out.append(body)
            elif word == "with":
                v = _eval(inner[5:], data, dot)
                body, _ = block(v, ("end",))
                out.append(body if v else "")
            else:
                v = _eval(inner, data, dot)
                out.append(htmllib.escape(str(v)) if v not in (None, False) else "")
        return "".join(out), None

    return block(None, ())[0]


# ---------------- versions ----------------
def _path(key):
    return STORE / f"{key}.json"


def _load(key):
    try:
        return json.loads(_path(key).read_text())
    except Exception:
        return {"versions": [], "published": None}


def _save(key, rec):
    STORE.mkdir(parents=True, exist_ok=True)
    tmp = _path(key).with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False))
    tmp.replace(_path(key))


def base(key):
    body = json.loads((OUT / "templates" / f"{key}.json").read_text())
    return {"n": 0, "status": "approved build", "subject": body["subject"], "preview_text": body["preview_text"],
            "from_name": body.get("from_name") or SENDERS[0], "name": body.get("name", key), "html": body["html"],
            "by": "approved build (repo)", "at": None}


def live(key):
    """What's on Evoflows (or will be pushed): the last published builder version, else the approved build."""
    rec = _load(key)
    if rec.get("published"):
        v = next(x for x in rec["versions"] if x["n"] == rec["published"])
        return {**base(key), **{k: v[k] for k in ("n", "subject", "preview_text", "from_name", "html", "by", "at")}, "status": "published"}
    return base(key)


def template_body(key):
    """PUT /templates body for a key: the published builder version if there is one (used by flow approvals too)."""
    v = live(key)
    return {"name": v["name"], "subject": v["subject"], "preview_text": v["preview_text"], "html": v["html"], "from_name": v["from_name"]}


def library():
    """Brand blocks cut from approved emails (so they're on-brand by construction)."""
    picks = [("Heading and intro", "f3_e1hi", "A good basket to join on", None), ("Plain paragraph", "f2_pe1", "Questions? Reply", None),
             ("Button", "f2_pe1", "Open my member portal", None), ("Benefits table", "f2_pe1", "10% off monthly", None),
             ("Numbered steps", "f2_pe1", "Three things to do this week", None), ("Membership panel", "f3_e1hi", "Evolution Golf Membership", None),
             ("Good to know", "f3_e1hi", "Good to know before you check out", None), ("Trust line", "f3_e1hi", "Advice from golfers", None),
             ("Product from the basket", "f3_e1hi", "Qty", "checkout")]
    out = []
    for name, key, needle, context in picks:
        try:
            _, blocks, _ = split(base(key)["html"])
        except Exception:
            continue
        b = next((x for x in blocks if needle in htmllib.unescape(re.sub(r"<[^>]+>", " ", x))), None)
        if b:
            out.append({"id": f"lib:{len(out)}", "name": name, "from": key, "context": context, "html": b, "meta": block_meta(b)})
    return out


def doc(key):
    rec = _load(key)
    cur = live(key)
    latest = rec["versions"][-1] if rec["versions"] else None
    start = latest if latest and latest["status"] in ("draft", "approved") else cur
    head, blocks, tail = split(start["html"])
    return {"key": key, "name": cur["name"], "senders": SENDERS, "published_n": rec.get("published"),
            "editing": {"n": start["n"], "status": start["status"], "subject": start["subject"], "preview_text": start["preview_text"],
                        "from_name": start["from_name"],
                        "blocks": [{"src": f"v{start['n']}:{i}", "html": b, "meta": block_meta(b), "segments": segments(b)} for i, b in enumerate(blocks)]},
            "versions": [{k: v.get(k) for k in ("n", "status", "subject", "by", "at", "note", "approved_by", "approved_at", "published_by", "published_at")}
                         for v in rec["versions"]][::-1],
            "library": [{**x, "segments": segments(x["html"])} for x in library()],
            "checks": checks(start["html"], start["subject"])}


def _source_block(key, src):
    if src.startswith("lib:"):
        lib = library()
        i = int(src[4:])
        return lib[i]["html"] if i < len(lib) else None
    m = re.fullmatch(r"v(\d+):(\d+)", src or "")
    if not m:
        return None
    n, i = int(m.group(1)), int(m.group(2))
    v = base(key) if n == 0 else next((x for x in _load(key)["versions"] if x["n"] == n), None)
    if not v:
        return None
    _, blocks, _ = split(v["html"])
    return blocks[i] if i < len(blocks) else None


def checks(html, subject):
    errors, warnings = [], []
    if not (subject or "").strip():
        errors.append("The subject line is empty.")
    if "{{ .Tx.Data.unsubscribe_url }}" not in html:
        errors.append("The unsubscribe link is missing (the footer block can't be removed).")
    opens = len(re.findall(r"\{\{-?\s*(?:if|range|with)\b", html))
    ends = len(re.findall(r"\{\{-?\s*end\s*-?\}\}", html))
    if opens != ends:
        errors.append("A condition was broken (an if/end pair doesn't match).")
    for src in IMG_SRC.findall(html):
        if not src.startswith(ALLOWED_IMG) and not src.startswith("{{"):
            errors.append(f"Image not on Shopify Files: {src[:80]}")
    text = htmllib.unescape(re.sub(r"<[^>]+>", " ", html)) + " " + (subject or "")
    if CODE_RE.search(text):
        errors.append("Looks like a discount code: codes aren't allowed in flows.")
    if URGENCY_RE.search(text):
        errors.append("Deadline or urgency wording: only allowed with a real expiry (DMCC Act).")
    if html.count(BUTTON_SIG) > 1:
        warnings.append(f"{html.count(BUTTON_SIG)} buttons: the design allows one primary button per email.")
    if html.count(PANEL_SIG) > 1:
        warnings.append(f"{html.count(PANEL_SIG)} stone panels: the design allows at most one.")
    return {"errors": errors, "warnings": warnings}


def save(key, body, who):
    """New draft from the editor. Each block must carry the same {{ }} tokens as the block it came from."""
    blocks = body.get("blocks") or []
    if not blocks:
        raise ValueError("An email needs at least one block.")
    for b in blocks:
        src = _source_block(key, b.get("src", ""))
        if src is None:
            raise ValueError("A block came from somewhere unknown; reload the editor.")
        if tokens(src) != tokens(b.get("html", "")):
            raise ValueError("Personalisation or a condition inside a block was changed; only words can be edited.")
        if _tags(src) != _tags(b["html"]):
            raise ValueError("A block's layout was changed; only words can be edited.")
    from_name = body.get("from_name") if body.get("from_name") in SENDERS else live(key)["from_name"]
    cur = live(key)
    head, _, tail = split(cur["html"])
    html = head + "".join(b["html"] for b in blocks) + tail
    subject = str(body.get("subject", "")).strip()[:200]
    preview = str(body.get("preview_text", "")).strip()[:250]
    if tokens(subject) and not set(tokens(subject)) <= set(tokens(cur["subject"])):
        raise ValueError("The subject line can only use the personalisation it already had.")
    with _lock:
        rec = _load(key)
        n = max([v["n"] for v in rec["versions"]] + [0]) + 1
        for v in rec["versions"]:
            if v["status"] in ("draft", "approved"):
                v["status"] = "replaced"
        rec["versions"].append({"n": n, "status": "draft", "subject": subject, "preview_text": preview, "from_name": from_name,
                                "html": html, "by": who, "at": _now(), "note": str(body.get("note", ""))[:300]})
        _save(key, rec)
    return {"n": n, "checks": checks(html, subject)}


def _tags(s):
    return re.findall(r"<[^>]+>", s)


def _version(rec, n):
    v = next((x for x in rec["versions"] if x["n"] == n), None)
    if not v:
        raise KeyError(n)
    return v


def approve(key, n, who):
    with _lock:
        rec = _load(key)
        v = _version(rec, n)
        c = checks(v["html"], v["subject"])
        if c["errors"]:
            raise ValueError("Fix these first: " + " ".join(c["errors"]))
        if v["status"] not in ("draft", "superseded", "replaced"):
            raise ValueError(f"Version {n} is {v['status']}.")
        v.update(status="approved", approved_by=who, approved_at=_now())
        _save(key, rec)
    return v


def publish(key, n, who):
    """Push an approved version to Evoflows (PUT /templates/{key}). Live flows use it from their next send."""
    with _lock:
        rec = _load(key)
        v = _version(rec, n)
        if v["status"] not in ("approved", "superseded"):
            raise ValueError("Approve this version first.")
        if v["status"] == "superseded" and not v.get("approved_by"):
            raise ValueError("Approve this version first.")
        body = {"name": base(key)["name"], "subject": v["subject"], "preview_text": v["preview_text"], "html": v["html"], "from_name": v["from_name"]}
        status, res = evoflows._call("PUT", f"/templates/{key}", body)
        if status >= 400:
            raise ValueError(f"Evoflows refused it ({status}): {json.dumps(res)[:300]}")
        for x in rec["versions"]:
            if x["status"] == "published":
                x["status"] = "superseded"
        v.update(status="published", published_by=who, published_at=_now(), evoflows=res)
        rec["published"] = n
        _save(key, rec)
    evoflows._log({"at": _now(), "by": who, "push": f"publish email {key} v{n}", "status": status})
    return {"status": status, "response": res}


def restore_build(key, who):
    """Go back to the approved build from the repo (publishes it)."""
    b = base(key)
    status, res = evoflows._call("PUT", f"/templates/{key}", {k: b[k] for k in ("name", "subject", "preview_text", "html", "from_name")})
    if status >= 400:
        raise ValueError(f"Evoflows refused it ({status})")
    with _lock:
        rec = _load(key)
        for x in rec["versions"]:
            if x["status"] == "published":
                x["status"] = "superseded"
        rec["published"] = None
        _save(key, rec)
    evoflows._log({"at": _now(), "by": who, "push": f"restore email {key} to the approved build", "status": status})
    return {"status": status}


def test(key, n, to, who):
    """Send a version to a staff inbox: uploaded under a separate draft key, so live flows never see it."""
    if not to.lower().endswith("@evolutiongolf.co.uk"):
        raise ValueError("Test sends go to @evolutiongolf.co.uk addresses only.")
    rec = _load(key)
    v = base(key) if n == 0 else _version(rec, n)
    tkey = f"draft_{key}"
    st, res = evoflows._call("PUT", f"/templates/{tkey}", {"name": f"DRAFT {base(key)['name']}", "subject": v["subject"],
                                                          "preview_text": v["preview_text"], "html": v["html"], "from_name": v["from_name"]})
    if st >= 400:
        raise ValueError(f"Evoflows refused the draft ({st}): {json.dumps(res)[:200]}")
    st, res = evoflows._call("POST", f"/templates/{tkey}/test", {"to": to, "sample": evoflows.sample_for(key)})
    evoflows._log({"at": _now(), "by": who, "push": f"test email {key} v{n} → {to}", "status": st})
    return {"status": st, "response": res}


def preview(key, n=None, audience="non", html=None, subject=None):
    if html is None:
        rec = _load(key)
        v = live(key) if n is None else (base(key) if n == 0 else _version(rec, n))
        html = v["html"]
    return render(html, sample(audience))

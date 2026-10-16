"""Design system for Evoflows emails: a brand theme (colours, fonts, headline size, button corners) that every email is
rendered from, plus per-email overrides.

Emails are stored "tokenised": each literal design value in the HTML (#0F3B2A, the Fraunces stack, 38px/42px …) is
replaced by a named token ([[c:brand]], [[f:head]], [[h1]] …). Rendering puts the theme's values back. With the default
theme the result is byte-identical to the approved build (proved for every email by tests/check). Change the brand theme
and every email follows; an email can override any token for itself.
"""
import copy
import datetime as dt
import json
import re
import threading
import time

from . import config, evoflows

STORE = config.DATA_DIR / "design"
_lock = threading.Lock()

# Literal values used by the approved builds -> token names. White stays white (canvas rule); Trustpilot green is theirs.
COLOURS = {"brand": "#0F3B2A", "eyebrow": "#24563F", "head": "#161816", "ink": "#2E322F", "muted": "#626862",
           "line": "#DDE1DD", "stone": "#F1F3F1", "on_dark": "#BCC8C3"}
FIXED = {"white": "#FFFFFF", "trust": "#00B67A"}
COLOUR_LABELS = {"brand": "Brand green (header, footer, buttons, links)", "eyebrow": "Eyebrow (small capitals)", "head": "Headlines",
                 "ink": "Body text", "muted": "Small print", "line": "Rules and table lines", "stone": "The one tinted panel",
                 "on_dark": "Footer text on the brand colour"}

# Email-safe font choices (Google Fonts with a system fallback; Gmail and Outlook show the fallback).
FONTS = {
    "head": {"Fraunces": ("Fraunces:opsz,wght@9..144,400", "Fraunces,Georgia,'Times New Roman',serif"),
             "Playfair Display": ("Playfair+Display:wght@400", "'Playfair Display',Georgia,'Times New Roman',serif"),
             "Libre Baskerville": ("Libre+Baskerville:wght@400", "'Libre Baskerville',Georgia,'Times New Roman',serif"),
             "Lora": ("Lora:wght@400", "Lora,Georgia,'Times New Roman',serif"),
             "DM Serif Display": ("DM+Serif+Display", "'DM Serif Display',Georgia,'Times New Roman',serif"),
             "Inter (sans headlines)": ("", "Inter,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"),
             "Georgia (no web font)": ("", "Georgia,'Times New Roman',serif")},
    "body": {"Inter": ("Inter:wght@400;500;600", "Inter,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"),
             "DM Sans": ("DM+Sans:wght@400;500;600", "'DM Sans',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"),
             "Lato": ("Lato:wght@400;700", "Lato,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"),
             "Source Sans 3": ("Source+Sans+3:wght@400;500;600", "'Source Sans 3',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"),
             "Work Sans": ("Work+Sans:wght@400;500;600", "'Work Sans',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"),
             "Arial (no web font)": ("", "Arial,Helvetica,sans-serif")},
}
H1 = {"Large (38px)": ("38px/42px", "32px", "36px"), "Extra large (44px)": ("44px/48px", "34px", "38px"),
      "Medium (32px)": ("32px/38px", "28px", "32px")}
RADIUS = {"Square (2px)": "2px", "Soft (6px)": "6px", "Round (24px)": "24px"}
DEFAULT = {"colours": dict(COLOURS), "font_head": "Fraunces", "font_body": "Inter", "h1": "Large (38px)", "radius": "Square (2px)"}
IMPORT = "@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400&family=Inter:wght@400;500;600&display=swap')"


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# ---------------- tokenising ----------------
def tokenize(html):
    t = html.replace(IMPORT, "[[import]]")
    t = t.replace(FONTS["head"]["Fraunces"][1], "[[f:head]]").replace(FONTS["body"]["Inter"][1], "[[f:body]]")
    t = t.replace("font:400 38px/42px", "font:400 [[h1]]").replace(".h1{font-size:32px!important;line-height:36px!important}",
                                                                  ".h1{font-size:[[h1m]]!important;line-height:[[h1ml]]!important}")
    t = t.replace("border-radius:2px", "border-radius:[[radius]]")
    for name, hexv in {**COLOURS, **FIXED}.items():
        t = re.sub(re.escape(hexv), f"[[c:{name}]]", t, flags=re.I)
    return t


def values(theme):
    th = merge(DEFAULT, theme or {})
    head, body = FONTS["head"][th["font_head"]], FONTS["body"][th["font_body"]]
    fams = "&".join(f"family={x}" for x in (head[0], body[0]) if x)
    v = {f"c:{k}": th["colours"].get(k, COLOURS[k]) for k in COLOURS}
    v.update({f"c:{k}": hexv for k, hexv in FIXED.items()})
    h1 = H1[th["h1"]]
    v.update({"f:head": head[1], "f:body": body[1], "h1": h1[0], "h1m": h1[1], "h1ml": h1[2], "radius": RADIUS[th["radius"]],
              "import": f"@import url('https://fonts.googleapis.com/css2?{fams}&display=swap')" if fams else ""})
    if th == DEFAULT:  # exact original import string
        v["import"] = IMPORT
    return v


TOKEN = re.compile(r"\[\[([a-z_:0-9]+)\]\]")


def render(html_t, theme):
    v = values(theme)
    return TOKEN.sub(lambda m: v.get(m.group(1), m.group(0)), html_t)


def merge(base, over):
    out = copy.deepcopy(base)
    for k, val in (over or {}).items():
        if k == "colours":
            out["colours"] = {**out["colours"], **{c: x for c, x in (val or {}).items() if c in COLOURS and _hex(x)}}
        elif k in ("font_head", "font_body", "h1", "radius") and val in {"font_head": FONTS["head"], "font_body": FONTS["body"], "h1": H1, "radius": RADIUS}[k]:
            out[k] = val
    return out


def _hex(x):
    return isinstance(x, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", x) is not None


def diff(theme, base):
    """What an email overrides compared with the brand theme (for 'reset to brand')."""
    d = {}
    for k in ("font_head", "font_body", "h1", "radius"):
        if theme.get(k) and theme[k] != base[k]:
            d[k] = theme[k]
    cols = {c: x for c, x in (theme.get("colours") or {}).items() if x.upper() != base["colours"][c].upper()}
    if cols:
        d["colours"] = cols
    return d


# ---------------- readability ----------------
def _lum(hexv):
    r, g, b = (int(hexv[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def checks(theme):
    th = merge(DEFAULT, theme)
    c, w = th["colours"], "#FFFFFF"
    pairs = [("Body text on white", c["ink"], w, 4.5), ("Headlines on white", c["head"], w, 4.5), ("Small print on white", c["muted"], w, 4.5),
             ("Links on white", c["brand"], w, 4.5), ("Button text (white) on brand", w, c["brand"], 4.5),
             ("Footer text on brand", c["on_dark"], c["brand"], 4.5), ("Eyebrow on white", c["eyebrow"], w, 4.5),
             ("Body text on the stone panel", c["ink"], c["stone"], 4.5)]
    out = []
    for label, fg, bg, need in pairs:
        r = ratio(fg, bg)
        out.append({"label": label, "ratio": round(r, 2), "ok": r >= need, "need": need})
    warn = [f"{x['label']}: contrast {x['ratio']}:1 (needs {x['need']}:1 to be easy to read)" for x in out if not x["ok"]]
    if _lum(c["stone"]) < 0.8:
        warn.append("The panel tint is quite dark; the design uses a very light tint.")
    return {"pairs": out, "warnings": warn}


# ---------------- the brand theme: draft -> approve -> publish ----------------
def _load():
    try:
        return json.loads((STORE / "theme.json").read_text())
    except Exception:
        return {"published": copy.deepcopy(DEFAULT), "published_n": 0, "versions": []}


def _save(rec):
    STORE.mkdir(parents=True, exist_ok=True)
    (STORE / "theme.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1))


def brand():
    return merge(DEFAULT, _load()["published"])


def theme_doc():
    rec = _load()
    latest = rec["versions"][-1] if rec["versions"] else None
    editing = latest if latest and latest["status"] in ("draft", "approved") else {"n": rec["published_n"], "status": "published", "theme": rec["published"]}
    return {"published": brand(), "published_n": rec["published_n"], "editing": {**editing, "theme": merge(DEFAULT, editing["theme"])},
            "versions": [{k: v.get(k) for k in ("n", "status", "by", "at", "approved_by", "published_by", "published_at", "note", "applied")} for v in rec["versions"]][::-1],
            "options": {"fonts_head": list(FONTS["head"]), "fonts_body": list(FONTS["body"]), "h1": list(H1), "radius": list(RADIUS),
                        "colours": [{"key": k, "label": COLOUR_LABELS[k], "default": COLOURS[k]} for k in COLOURS]},
            "checks": checks(editing["theme"])}


def save_theme(theme, who, note=""):
    th = merge(DEFAULT, theme)
    with _lock:
        rec = _load()
        for v in rec["versions"]:
            if v["status"] in ("draft", "approved"):
                v["status"] = "replaced"
        n = max([v["n"] for v in rec["versions"]] + [0]) + 1
        rec["versions"].append({"n": n, "status": "draft", "theme": th, "by": who, "at": _now(), "note": note[:200]})
        _save(rec)
    return {"n": n, "checks": checks(th)}


def approve_theme(n, who):
    with _lock:
        rec = _load()
        v = next((x for x in rec["versions"] if x["n"] == n), None)
        if not v or v["status"] != "draft":
            raise ValueError("Only a draft can be approved.")
        v.update(status="approved", approved_by=who, approved_at=_now())
        _save(rec)
    return v


def publish_theme(n, who):
    """Make version n the brand theme and re-publish every email that's on Evoflows, so customers get the new look."""
    from . import builder
    with _lock:
        rec = _load()
        v = next((x for x in rec["versions"] if x["n"] == n), None)
        if not v or v["status"] != "approved":
            raise ValueError("Approve this version first.")
        old = rec["published"]
        rec["published"], rec["published_n"] = v["theme"], n
        for x in rec["versions"]:
            if x["status"] == "published":
                x["status"] = "superseded"
        v.update(status="published", published_by=who, published_at=_now())
        _save(rec)
    results = []
    for key in builder.all_keys():
        try:
            res = builder.republish_for_theme(key, who, f"brand theme v{n}")
            results.append({"key": key, **res})
        except Exception as e:  # keep going; report every email
            results.append({"key": key, "status": 0, "error": str(e)[:200]})
        time.sleep(0.25)  # stay under the engine's 60 requests a minute
    with _lock:
        rec = _load()
        v = next(x for x in rec["versions"] if x["n"] == n)
        v["applied"] = {"ok": sum(1 for r in results if r.get("status") and r["status"] < 400), "total": len(results)}
        _save(rec)
    evoflows._log({"at": _now(), "by": who, "push": f"publish brand theme v{n} to {len(results)} emails", "status": 200})
    return {"results": results, "previous": old}

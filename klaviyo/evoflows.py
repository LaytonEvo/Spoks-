"""Evoflows output: flags, templates (Go-template HTML over .Tx.Data) and flow definitions for the Evoflows engine.

Contract: docs/source/FLOW_API.md (Evoflows v1, mail.evolutiongolf.co.uk/flow/api/v1). Writes dashboard/app/evoflows_out/ (deployed with the app):
  flags.json                     PUT /flags body
  templates/<key>.json           PUT /templates/<key> body {name, subject, preview_text, html}
  flows/<key>.json               PUT /flows/<key> body
The HTML comes from the same builders as the Klaviyo drafts (Layton-approved copy); every Klaviyo tag our builders emit is
translated by an explicit table, and anything not in the table stops the build (so nothing half-translated is pushed).

Build: python3 klaviyo/evoflows.py            (after build_f3.py)
Push:  EVOFLOWS_TOKEN=... python3 klaviyo/evoflows.py push [flags|templates|validate|flow|all]
       Never enables a flow: Luke runs the staff seed test and enables it himself. The token is never written to disk.
"""
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "design"))
import build_f3 as f3  # noqa: E402
import build_f9 as f9  # noqa: E402

OUT = ROOT.parent / "dashboard" / "app" / "evoflows_out"  # shipped with the dashboard (Railway deploys dashboard/)
BASE = os.environ.get("EVOFLOWS_BASE", "https://mail.evolutiongolf.co.uk/flow/api/v1")

# Klaviyo-hosted images re-hosted on Shopify Files (12 Oct 2026, JPG/PNG).
IMAGES = {
    "https://cdn.klaviyomail.com/company/SiyYRR/images/079dc837-5851-48e3-8559-cbb12973b1ca.png":
        "https://cdn.shopify.com/s/files/1/0499/9014/0061/files/eg-email-logo-white.png?v=1791803434",
    "https://cdn.klaviyomail.com/company/SiyYRR/images/e0287c0c-92d1-4159-844b-825430a2e346.jpeg":
        "https://cdn.shopify.com/s/files/1/0499/9014/0061/files/eg-email-annual-member-card.jpg?v=1791803434",
    "https://cdn.klaviyomail.com/company/SiyYRR/images/50596254-d610-4268-a459-f77bfb2dae1b.jpeg":
        "https://cdn.shopify.com/s/files/1/0499/9014/0061/files/eg-email-alex.jpg?v=1791803434",
}

# ---------------- flags (collection handles, checked against Shopify 9 and 12 Oct 2026) ----------------
TROLLEY_H = ["golf-trolleys", "electric-trolleys", "gps-electric-trolleys", "remote-electric-trolleys", "motocaddy-electric-trolleys",
             "motocaddy-golf-trolleys", "motocaddy-electric-golf-trolleys", "motocaddy-push-trolleys", "powakaddy-golf-trolleys",
             "powakaddy-electric-trolleys", "powakaddy-push-trolleys", "push-pull-trolleys", "push-golf-trolleys", "cube-golf-push-trolleys"]
MOTO_H = ["motocaddy-electric-trolleys", "motocaddy-golf-trolleys", "motocaddy-electric-golf-trolleys", "motocaddy-push-trolleys"]
CLUBS_H = ["mens-golf-clubs", "ladies-golf-clubs", "womens-golf-clubs", "junior-golf-clubs", "left-handed-golf-clubs", "golf-drivers",
           "fairways", "fairway-woods", "hybrids-utility-irons", "golf-wedges", "putters", "custom-clubs", "mens-custom-fitted-golf-clubs",
           "complete-package-sets", "ladies-golf-drivers", "ladies-golf-fairway-woods", "ladies-golf-hybrids", "ladies-golf-irons",
           "ladies-golf-wedges", "ladies-golf-package-sets"]
USED_H = ["approved-used-golf-clubs", "all-second-hand-golf-clubs"]
SHOES_H = ["mens-golf-shoes", "mens-spiked-golf-shoes", "mens-spikeless-golf-shoes", "mens-waterproof-golf-shoes", "junior-golf-shoes"]
FLAGS = {"has_trolley": {"collections": TROLLEY_H}, "has_motocaddy_trolley": {"collections": MOTO_H},
         "has_clubs": {"collections": CLUBS_H}, "has_used_clubs": {"collections": USED_H}, "has_shoes": {"collections": SHOES_H}}

# The builders' Klaviyo collection-title lists → the Evoflows flag that means the same thing.
TITLE_SETS = {frozenset(f3.TROLLEYS): ".Tx.Data.has_trolley", frozenset(f3.CLUBS): ".Tx.Data.has_clubs",
              frozenset(f3.USED): ".Tx.Data.has_used_clubs", frozenset(f3.HARDWARE): ".Tx.Data.has_hardware",
              frozenset(f9.MOTO_TROLLEYS): ".Tx.Data.has_motocaddy_trolley", frozenset(f9.SHOES): ".Tx.Data.has_shoes"}

A = 'style="color:#626862;"'
FIXED = {
    # footer: one-click unsubscribe (required); preferences page is phase 2, so guarded
    "{% unsubscribe 'Unsubscribe' %} · {% manage_preferences 'Manage preferences' %}":
        '<a href="{{ .Tx.Data.unsubscribe_url }}" style="color:inherit;">Unsubscribe</a>'
        '{{ if .Tx.Data.preferences_url }} · <a href="{{ .Tx.Data.preferences_url }}" style="color:inherit;">Manage preferences</a>{{ end }}',
    "{% for item in event.extra.line_items %}": "{{ range .Tx.Data.items }}",
    "{{ item.product.title }}": "{{ .title }}",
    "{{ item.quantity }}": "{{ .qty }}",
    "{{ item.product.images.0.src }}": "{{ .image }}",
    # line total (as Klaviyo showed), unit price if the engine sends no line_total
    "{{ item.line_price|floatformat:2 }}": "{{ if .line_total }}{{ .line_total }}{{ else }}{{ .price }}{{ end }}",
    "{{ event.extra.checkout_url }}": "{{ .Tx.Data.recovery_url }}",
    "{{ event|lookup:'$value'|floatformat:2 }}": "{{ .Tx.Data.total }}",
    "{{ person.first_name|default:'there' }}": "{{ if .Tx.Data.first_name }}{{ .Tx.Data.first_name }}{{ else }}there{{ end }}",
    "{% if person.first_name %}": "{{ if .Tx.Data.first_name }}",
    "{{ person.first_name }}": "{{ .Tx.Data.first_name }}",
    "{% if event.extra.line_items.0.product.title %}": "{{ if .Tx.Data.items }}",
    "{% if item.product.images.0.src %}": "{{ if .image }}",
    "{{ event.extra.line_items.0.product.title }}": "{{ (index .Tx.Data.items 0).title }}",
    "{% if person|lookup:'MemberTier' == 'Free' %}": "{{ if .Tx.Data.is_free_member }}",
    "{% if person|lookup:'MemberTier' == 'AnnualMember' %}": "{{ if .Tx.Data.is_annual }}",
    "{% elif person|lookup:'MemberTier' == 'Free' %}": "{{ else if .Tx.Data.is_free_member }}",
    "{% else %}": "{{ else }}",
    "{% endif %}": "{{ end }}",
    "{% endfor %}": "{{ end }}",
}
TAG = re.compile(r"\{%.*?%\}|\{\{.*?\}\}", re.S)


def _collections(tag):
    """'{% if "A" in event.Collections or ... %}' / '{% if "A" not in ... and ... %}' → Go condition, or None."""
    m = re.fullmatch(r"\{%\s*(if|elif)\s+(.*?)\s*%\}", tag, re.S)
    if not m or "event.Collections" not in m.group(2):
        return None
    kw, cond = m.groups()
    neg = re.fullmatch(r'(?:"[^"]+" not in event\.Collections(?: and )?)+', cond)
    pos = re.fullmatch(r'(?:"[^"]+" in event\.Collections(?: or )?)+', cond)
    names = frozenset(re.findall(r'"([^"]+)"', cond))
    go = "if" if kw == "if" else "else if"
    if pos and names in TITLE_SETS:
        return "{{ %s %s }}" % (go, TITLE_SETS[names])
    if neg:
        parts = [v for s, v in TITLE_SETS.items() if s <= names]
        cover = frozenset().union(*[s for s in TITLE_SETS if s <= names]) if parts else frozenset()
        if cover == names:  # e.g. none of trolleys + clubs
            subs = [s for s in TITLE_SETS if s <= names and TITLE_SETS[s] != ".Tx.Data.has_hardware"]
            flags = [TITLE_SETS[s] for s in subs if not any(s < o for o in subs)]  # drop sets inside another (Motocaddy ⊂ trolleys)
            return "{{ %s not (or %s) }}" % (go, " ".join(sorted(set(flags))))
    raise ValueError(f"no flag for collection condition: {sorted(names)[:3]}… ({len(names)} names)")


IMG_ITEM = re.compile(r'<img src="\{\{ item\.product\.images\.0\.src \}\}"[^>]*>')


def translate(text):
    for k, v in IMAGES.items():
        text = text.replace(k, v)
    text = IMG_ITEM.sub(lambda m: "{% if item.product.images.0.src %}" + m.group(0) + "{% endif %}", text)
    for k in sorted(FIXED, key=len, reverse=True):
        text = text.replace(k, FIXED[k])

    def sub(m):
        tag = m.group(0)
        if tag.startswith("{{ ") and (tag[3] == "." or tag.startswith("{{ if ") or tag.startswith("{{ else") or tag.startswith("{{ end")
                                      or tag.startswith("{{ range ") or tag.startswith("{{ (index ")):
            return tag  # already Go
        go = _collections(tag)
        if go:
            return go
        raise ValueError(f"untranslated Klaviyo tag: {tag[:120]}")
    text = TAG.sub(sub, text)
    if "cdn.klaviyomail.com" in text or "cloudfront.net" in text:
        raise ValueError("Klaviyo-hosted image left in template: re-host it on Shopify Files and add it to IMAGES")
    if "{{ .Tx.Data.unsubscribe_url }}" not in text and "<html" in text:
        raise ValueError("unsubscribe_url missing")
    return text


# ---------------- F3 ----------------
def f3_templates():
    pk = json.loads((ROOT.parent / "dashboard/app/drafts/f3-checkout.json").read_text())
    out = {}
    for t in pk["templates"]:
        html = (ROOT.parent / "dashboard/app/drafts/html" / t["file"]).read_text()
        out[f"f3_{t['key']}"] = {"name": f"F3 {t['name']}", "subject": translate(t["subject"]),
                                 "preview_text": translate(t["preview"]), "html": translate(html),
                                 **({"from_name": t["sender"]} if t["sender"] != "⛳ Evolution Golf" else {})}
    return out


def f3_flow():
    """Approved F3 (Klaviyo draft SJxQ7E, QA'd 8 Oct). SMS steps dropped (no SMS channel), so the waits around them are merged."""
    E = lambda k: {"id": k, "type": "email", "template": f"f3_{k}"}
    W = lambda i, days=0, hours=0, at=None: {"id": i, "type": "wait", "for": {k: v for k, v in (("days", days), ("hours", hours)) if v},
                                             **({"until_time": at} if at else {})}
    return {
        "key": "f3_checkout", "name": "F3 Checkout abandonment", "version": 1,
        "description": "Checkouts worth £30+ that don't complete. Annual members: their 10% can go on it. Non-members £300+: join and 10% "
                       "comes off this basket, then a note from Alex. Under £300: Free membership's 5%. No codes.",
        "trigger": {"type": "checkout_abandoned", "when": {"field": "checkout.total", "gte": 30}},
        "entry": {"one_active_per_contact": True, "reentry_after_days": 7},
        "consent": "soft_opt_in",
        "send_window": {"timezone": "Europe/London", "quiet_hours": ["21:00", "08:00"]},
        "utm": {"source": "evolutiongolf-email", "medium": "flow", "campaign": "f3-checkout"},
        "steps": [
            W("w1h", hours=1),
            {"id": "path", "type": "split", "branches": [
                {"id": "annual", "when": {"field": "flags.is_annual", "eq": True},
                 "steps": [E("e1m"), W("m1", days=1, at="09:30"), E("e2m")]},
                {"id": "big", "when": {"field": "checkout.total", "gte": 300},
                 "steps": [E("e1hi"), W("h1", days=1, at="09:30"), E("e2hi"), W("h3", days=2, at="09:30"), E("e3h")]},
                {"id": "small",
                 "steps": [E("e1lo"), W("l1", days=1, at="09:30"), E("e2lo"), W("l3", days=2, at="17:30"), E("e3lo")]},
            ]},
        ],
    }


def build():
    (OUT / "templates").mkdir(parents=True, exist_ok=True)
    (OUT / "flows").mkdir(parents=True, exist_ok=True)
    (OUT / "flags.json").write_text(json.dumps(FLAGS, indent=1))
    tpls = f3_templates()
    for k, body in tpls.items():
        (OUT / "templates" / f"{k}.json").write_text(json.dumps(body, indent=1, ensure_ascii=False))
        (OUT / "templates" / f"{k}.html").write_text(body["html"])
    flow = f3_flow()
    missing = {s["template"] for b in flow["steps"][1]["branches"] for s in b["steps"] if s["type"] == "email"} - set(tpls)
    assert not missing, missing
    (OUT / "flows" / "f3_checkout.json").write_text(json.dumps(flow, indent=1, ensure_ascii=False))
    print("evoflows: flags", len(FLAGS), "· templates", len(tpls), "· flows 1")


# ---------------- push (stdlib only) ----------------
def call(method, path, body=None):
    token = os.environ["EVOFLOWS_TOKEN"]
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, None


def push(what):
    if what in ("flags", "all"):
        print("PUT /flags", call("PUT", "/flags", json.loads((OUT / "flags.json").read_text())))
    if what in ("templates", "all"):
        for f in sorted((OUT / "templates").glob("*.json")):
            print(f"PUT /templates/{f.stem}", call("PUT", f"/templates/{f.stem}", json.loads(f.read_text())))
    flow = json.loads((OUT / "flows" / "f3_checkout.json").read_text())
    if what in ("validate", "all", "flow"):
        status, res = call("POST", "/flows/f3_checkout/validate", flow)
        print("POST /flows/f3_checkout/validate", status, json.dumps(res, indent=1))
        if what in ("all", "flow") and (status >= 400 or not (res or {}).get("valid") or (res or {}).get("problems")
                                         or any("template_missing" in str(w) for w in (res or {}).get("warnings", []))):
            sys.exit("validate failed: not pushing the flow")
    if what in ("flow", "all"):
        print("PUT /flows/f3_checkout", call("PUT", "/flows/f3_checkout", flow))  # lands disabled; never call /enable here


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "push":
        push(sys.argv[2] if len(sys.argv) > 2 else "all")
    else:
        build()

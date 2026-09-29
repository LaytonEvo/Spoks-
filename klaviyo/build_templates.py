"""Generate Klaviyo HTML templates for EG · F3 Checkout abandonment · Trolleys (TEST).
Copy is verbatim from Build Pack §3.3; [CONFIRM] items stay visible for review."""
import json, pathlib

G, DG, CREAM, INK, LINE, YEL = "#006747", "#003D27", "#FAF7F1", "#1E1E1E", "#E6E3DA", "#F1DA01"
HEAD = "font-family:Fraunces,Georgia,'Times New Roman',serif;color:%s;" % DG
BODY = "font-family:Inter,Arial,Helvetica,sans-serif;color:%s;font-size:16px;line-height:1.55;" % INK

def confirm(t=""):
    label = f"[CONFIRM {t}]" if t else "[CONFIRM]"
    return f'<span style="background:{YEL};font-weight:bold;padding:0 3px;">{label}</span>'

def p(html, extra=""):
    return f'<p style="margin:0 0 14px;{BODY}{extra}">{html}</p>'

def button(label, href):
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin:8px 0 18px;"><tr><td align="center" '
            f'style="background:{G};border-radius:6px;"><a href="{href}" style="display:block;padding:15px 20px;{BODY}color:#ffffff;'
            f'font-weight:bold;text-decoration:none;">{label}</a></td></tr></table>')

def component(name, note=""):
    extra = f" — {note}" if note else ""
    return (f'<div style="border:2px dashed {G};border-radius:6px;padding:12px;margin:0 0 16px;text-align:center;{BODY}font-size:14px;'
            f'color:{G};">[COMPONENT: EG · {name}{extra}]</div>')

ITEMS = f"""
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:4px 0 18px;border-top:1px solid {LINE};">
{{% for item in event.extra.line_items %}}
<tr><td width="96" style="padding:12px 12px 12px 0;border-bottom:1px solid {LINE};vertical-align:top;">
<img src="{{{{ item.product.images.0.src }}}}" width="84" alt="{{{{ item.product.title }}}}" style="display:block;width:84px;height:auto;border-radius:4px;"></td>
<td style="padding:12px 0;border-bottom:1px solid {LINE};vertical-align:top;{BODY}">
<strong>{{{{ item.product.title }}}}</strong><br><span style="font-size:14px;color:#5b5b5b;">Qty {{{{ item.quantity }}}} · £{{{{ item.line_price|floatformat:2 }}}}</span></td></tr>
{{% endfor %}}
</table>"""

USP = (f'<div style="background:{CREAM};border-radius:6px;padding:14px 16px;margin:8px 0 12px;text-align:center;{BODY}font-size:13px;color:{DG};">'
       + "Free UK delivery over £30 " + confirm() + " · Expert advice from people who play · 2-year warranty on trolleys " + confirm()
       + " · Trade-in on clubs and trolleys · Klarna &amp; Clearpay available " + confirm() + " · Custom fitting centre</div>")
TRUST = (f'<div style="text-align:center;margin:0 0 16px;{BODY}font-size:14px;color:{DG};">Trustpilot · Rated Excellent '
       + confirm("current rating and review count — use the live widget if available; never hard-code a star count") + "</div>")

def shell(title, preheader, inner, plain=False):
    header = "" if plain else (f'<tr><td align="center" style="background:{DG};padding:18px 24px;">'
        f'<a href="https://evolutiongolf.co.uk" style="{HEAD}color:#ffffff;font-size:20px;letter-spacing:2px;text-decoration:none;">⛳ EVOLUTION GOLF</a></td></tr>')
    return f"""<!DOCTYPE html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@600&family=Inter:wght@400;700&display=swap" rel="stylesheet">
<style>@media (max-width:620px){{.card{{width:100%!important}}.pad{{padding:24px 18px!important}}}}</style></head>
<body style="margin:0;padding:0;background:{CREAM};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{preheader}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{CREAM};"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" class="card" width="600" cellpadding="0" cellspacing="0" style="width:600px;background:#ffffff;border-radius:8px;overflow:hidden;">
{header}
<tr><td class="pad" style="padding:32px 36px 12px;">{inner}</td></tr>
<tr><td style="padding:20px 36px 28px;border-top:1px solid {LINE};text-align:center;font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:1.6;color:#6b6b6b;">
{{{{ organization.name }}}} · {{{{ organization.full_address }}}}<br>{confirm("company details for footer, if required")}<br>
You're receiving this because you signed up at evolutiongolf.co.uk.<br>
{{% unsubscribe 'Unsubscribe' %}} · {{% manage_preferences 'Manage preferences' %}}</td></tr>
</table></td></tr></table></body></html>"""

def h1(t): return f'<h1 style="margin:0 0 16px;{HEAD}font-size:28px;line-height:1.2;font-weight:600;">{t}</h1>'

T = {}
T["E1"] = dict(name="EG · F3 Trolleys E1 – Basket saved (TEST)",
  subject="Your trolley's saved, {{ person.first_name|default:'there' }}",
  preheader="Free UK delivery, 2-year warranty, spread the cost. Pick up where you left off.",
  html=shell("Your trolley's saved", "Free UK delivery, 2-year warranty, spread the cost. Pick up where you left off.",
    h1("Still deciding? Fair enough. It's a big buy.")
    + p("Your basket is exactly where you left it.") + ITEMS
    + p("The things people usually want to know before they commit:")
    + p("• <strong>Delivery:</strong> free to the UK mainland, usually " + confirm() + " working days.<br>"
        "• <strong>Warranty:</strong> 2 years on the trolley " + confirm("per brand") + ".<br>"
        "• <strong>Paying for it:</strong> Klarna or Clearpay at checkout if you'd rather spread it " + confirm() + ".<br>"
        "• <strong>Right model?</strong> Our team has filmed straight-talking reviews of the Motocaddy range — link below.")
    + button("Back to my basket", "{{ event.extra.checkout_url }}")
    + p(f'<a href="https://evolutiongolf.co.uk" style="color:{G};font-weight:bold;">Watch our trolley reviews</a> ' + confirm("URL"), "text-align:center;")
    + USP + TRUST))

THREE = (p("1. <strong>Range.</strong> Does the battery cover your usual round with margin? 18-hole lithium suits most; go 36 if you play twice on a Saturday " + confirm() + ".")
       + p("2. <strong>Boot.</strong> Fold it in your head: will it go in with your bag?")
       + p("3. <strong>Hills.</strong> If your course has them, downhill control matters more than any gadget."))
MEMBER_NOTE = confirm("membership is now a single £36/year paid membership on the site — does free membership / 'member price' still exist? Rewrite this paragraph once confirmed")

T["E2"] = dict(name="EG · F3 Trolleys E2 – How to be sure it's the right one (TEST)",
  subject="How to be sure it's the right trolley",
  preheader="Battery range, boot space, hills. Then a note on member pricing.",
  html=shell("How to be sure it's the right trolley", "Battery range, boot space, hills. Then a note on member pricing.",
    h1("Three quick checks") + THREE
    + p("Still happy with your pick? Good. One more thing: join as a Free member (30 seconds, no card) and you'll pay member price on this order — that applies to trolleys, which codes never do.")
    + p(MEMBER_NOTE)
    + component("Tier table – Free row only", "prices in the pack are out of date")
    + button("Join free", "https://members.evolutiongolf.co.uk")
    + button("Back to my basket", "{{ event.extra.checkout_url }}")
    + p(confirm("does the members portal accept a return URL? If yes, merge into one 'Join free and finish my order' button"), "font-size:14px;")
    + component("Trade-in panel – trolley") + component("Seasonal banner")))

T["E2m"] = dict(name="EG · F3 Trolleys E2m – Member (TEST)",
  subject="Your member price is already on this",
  preheader="Log in and it applies at checkout. Anything else we can answer?",
  html=shell("Your member price is already on this", "Log in and it applies at checkout. Anything else we can answer?",
    h1("Three quick checks") + THREE
    + p("You're a {{ person.MemberTier|default:'Evolution Golf' }} member — your price is applied when logged in.")
    + p(confirm("pack gives an outline only for this email — wording above follows the outline; check it reads right under the new single membership"), "font-size:14px;")
    + button("Back to my basket", "{{ event.extra.checkout_url }}")))

T["E3"] = dict(name="EG · F3 Trolleys E3 – Want a second opinion? (TEST)",
  subject="Want a second opinion on that trolley?",
  preheader="Tell me your course and how you play and I'll tell you if it's the right model.",
  html=shell("Want a second opinion on that trolley?", "Tell me your course and how you play and I'll tell you if it's the right model.",
    p("Hi {{ person.first_name|default:'there' }},")
    + p("Alex from Evolution Golf. I can see you were looking at the {{ event.extra.line_items.0.product.title }}. Good trolley.")
    + p("If you're not sure it's the right one — the course you play, how often, whether you'd use GPS — reply to this and I'll give you a straight answer. If a cheaper model would do the job, I'll say so.")
    + p("If you've already bought elsewhere, no problem at all. Ignore this one.")
    + p("Alex<br>Head of Ecommerce")
    + p(f'<a href="{{{{ event.extra.checkout_url }}}}" style="color:{G};">My basket</a>'), plain=True))

out = pathlib.Path("templates"); out.mkdir(exist_ok=True)
for k, v in T.items():
    (out / f"f3-trolleys-{k.lower()}.html").write_text(v["html"])
json.dump({k: {kk: vv for kk, vv in v.items() if kk != "html"} for k, v in T.items()}, open(out / "index.json", "w"), indent=1, ensure_ascii=False)
print({k: len(v["html"]) for k, v in T.items()})

"""F3 Checkout abandonment · Trolleys, built in design B ("On the course").

Emails: E1, E2, E2m, E3 (copy from the copy deck). Every image position is a named slot
(see SLOTS). Three image modes:
  slots - every non-dynamic image shown as a labelled placeholder with its brief
  now   - best image we already hold (stop-gaps marked)
  none  - the layout if no new image is ever sourced
Writes klaviyo/design/f3-b/<email>-<mode>.html (live image URLs) and preview.html (data URIs).

Run: python3 klaviyo/design/build_f3_b.py <scratch img dir>
"""
import base64, json, pathlib, sys

IMG_DIR = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
OUT = pathlib.Path(__file__).parent
KL = "https://d3k81ch9hvuctc.cloudfront.net/company/SiyYRR/images/"

# Layton, 1 Oct 2026: off the "Fraunces + cream" look. Website font (Noto Sans Display), green accents, pale-green panels.
# GOLD is kept as a name for the accent colour (now brand green); ON_DARK is the accent on dark-green panels.
G, DG, GOLD, CREAM, INK, MUTED, LINE, WHITE, SLOTBG = (
    "#006747", "#003D27", "#006747", "#EAF3EE", "#1F2A24", "#5E6B63", "#DCE5E0", "#FFFFFF", "#EEF2EF")
ON_DARK = "#A8D5BD"
SERIF = "'Noto Sans Display',Arial,Helvetica,sans-serif"  # headings (the name is historical)
SANS = "'Noto Sans Display',Arial,Helvetica,sans-serif"

# ---- image slots: the brief for each position ----
SLOTS = {
    "H1": dict(emails="E1", where="Hero, under the header", what="Golfer walking the course with an electric trolley. Real course, natural light, trolley clearly in shot.",
               size="1200 × 720 px (5:3), JPG, under 250 KB",
               now="Klaviyo library photo (Motocaddy lifestyle), only 490 px wide: soft on phones", now_status="Stop-gap",
               none="Hero dropped. The headline leads and the product card becomes the main image."),
    "H2": dict(emails="E2, E2m", where="Hero, under the header", what="A folded trolley going into a car boot, next to a golf bag. Backs up the \"Boot\" check.",
               size="1200 × 720 px (5:3), JPG, under 250 KB",
               now="Shopify product shot of the M1 DHC folded, on white: shows one model to everyone", now_status="Stop-gap",
               none="Hero dropped. The eyebrow and headline lead."),
    "M1": dict(emails="E2", where="Top of the membership panel", what="Evolution Golf membership card still-life (card, glove, ball, scorecard).",
               size="1200 × 800 px (3:2), JPG", now="Klaviyo \"member access\" image (1536 px). It shows The Open's logo on the card: check you have the rights, or crop it out",
               now_status="Stop-gap", none="Text-only panel on dark green with the roundel."),
    "A1": dict(emails="E3", where="Next to Alex's signature (optional)", what="Head-and-shoulders photo of Alex, plain background, smiling.",
               size="240 × 240 px square, JPG", now="Nothing in the library", now_status="Needed",
               none="Text signature only (the pack's plain-letter style)."),
    "P1": dict(emails="E1, E2, E2m", where="Basket card", what="Each product's main Shopify photo, pulled automatically.",
               size="Square, at least 800 px, white or transparent background, no badges", now="In place for every product",
               now_status="Have (check badges)", none="Always available. The main photo must carry no \"FREE GIFT\" or sale badges."),
}

LIVE = {"logo": KL + "07b49b80-e6e5-480f-9c79-25e6f90550a5.png", "roundel": KL + "4aa15d13-2505-4b2d-bec3-2603c69d2397.png",
        "product": "{{ event.extra.line_items.0.product.images.0.src }}",
        "H1": KL + "648eead5-a37c-4669-90b8-c48143fc11f9.png",
        "H2": "https://cdn.shopify.com/s/files/1/0499/9014/0061/files/2026M1DHCFoldedSide.png",
        "M1": KL + "02c3ea4e-ded3-4e4d-8be8-05539930335d.png"}
PREV_FILES = {"logo": "p-logo.png", "roundel": "p-roundel.png", "product": "p-product.jpg",
              "H1": "p-life1.jpg", "H2": "p-folded.jpg", "M1": "p-member.jpg"}


def data_uri(p):
    return ("data:image/png;base64," if p.suffix == ".png" else "data:image/jpeg;base64,") + base64.b64encode(p.read_bytes()).decode()


PRODUCT = ("Motocaddy 2026 M1 DHC Standard Lithium Electric Golf Trolley", "1", "£799.00")


def confirm(note=""):
    return (f'<span style="display:inline-block;border:1px dashed {MUTED};border-radius:3px;padding:0 4px;'
            f'font:600 10px/16px {SANS};letter-spacing:.04em;color:{MUTED};vertical-align:1px;">{("CONFIRM " + note).strip()}</span>')


SOCIAL = {"Instagram": "https://www.instagram.com/evolutiongolfuk", "Facebook": "https://www.facebook.com/share/18DSf8wH84/",
          "YouTube": "https://www.youtube.com/@evolutiongolfuk"}
NEW_IN = "https://evolutiongolf.co.uk/collections/new-in-golf-equipment"


def unsub(ctx, color):
    if ctx.live:
        return "{% unsubscribe 'Unsubscribe' %} · {% manage_preferences 'Manage preferences' %}"
    return f'<a href="#" style="color:{color};">Unsubscribe</a> · <a href="#" style="color:{color};">Manage preferences</a>'


class Ctx:
    def __init__(self, img, mode, web_fonts, live=False):
        self.img, self.mode, self.web_fonts, self.live = img, mode, web_fonts, live

    def if_motocaddy(self, html):
        """Show only for Motocaddy baskets (Klaviyo tag in live files; always shown in preview)."""
        if not self.live:
            return html
        return "{% if event.extra.line_items.0.product.vendor == 'Motocaddy' %}" + html + "{% endif %}"

    def slot(self, key, w, h, style="", caption=True):
        """Image slot: placeholder, stop-gap image, or nothing."""
        s = SLOTS[key]
        if self.mode == "slots":
            return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
                    f'<td align="center" height="{h}" style="height:{h}px;background:{SLOTBG};border:2px dashed {GOLD};padding:18px;{style}">'
                    f'<p style="margin:0 0 6px;font:700 12px/16px {SANS};letter-spacing:.14em;color:{GOLD};">IMAGE {key}</p>'
                    f'<p style="margin:0 0 6px;font:600 15px/21px {SANS};color:{DG};">{s["what"]}</p>'
                    f'<p style="margin:0;font:13px/18px {SANS};color:{MUTED};">{s["size"]}</p></td></tr></table>')
        if self.mode == "none" or key not in self.img:
            return ""
        tag = ""
        if caption and s["now_status"] == "Stop-gap" and not self.live:
            tag = (f'<p style="margin:6px 12px 0;font:600 10px/14px {SANS};letter-spacing:.06em;color:{MUTED};">'
                   f'<span style="border:1px dashed {MUTED};border-radius:3px;padding:1px 4px;">STOP-GAP {key}</span></p>')
        return (f'<img class="full" src="{self.img[key]}" width="{w}" alt="" style="width:{w}px;max-width:100%;height:auto;{style}">{tag}')


def shell(ctx, body, preheader, bg=WHITE, header=True):
    # Rule: the email canvas is always white, so white-background product shots sit seamlessly.
    # Klaviyo strips <link> tags, so the website font is loaded with @import; Gmail and Outlook fall back to Arial.
    fonts = ("<style>@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Display:wght@400;600;700&display=swap');</style>"
             if ctx.web_fonts else "")
    head = (f'<tr><td bgcolor="{DG}" style="background:{DG};padding:18px 32px;">'
            f'<a href="https://evolutiongolf.co.uk/"><img src="{ctx.img["logo"]}" width="170" alt="Evolution Golf" style="width:170px;height:auto;"></a></td></tr>') if header else ""
    return f"""<!DOCTYPE html><html lang="en-GB"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Evolution Golf</title>{fonts}
<style>
body{{margin:0;padding:0;background:{bg};-webkit-text-size-adjust:100%}} img{{border:0;display:block}} a{{color:{G}}}
.foot a{{color:#CFE0D6!important}} .foot-light a{{color:{MUTED}!important}}
@media (max-width:620px){{
 .card{{width:100%!important}} .px{{padding-left:22px!important;padding-right:22px!important}}
 .stack{{display:block!important;width:100%!important;box-sizing:border-box}} .nb{{border-top:0!important;padding-top:0!important}}
 .h1{{font-size:28px!important;line-height:34px!important}} .full{{width:100%!important;height:auto!important}}
}}
</style></head><body style="margin:0;padding:0;background:{bg};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{preheader}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{bg};"><tr><td align="center" style="padding:24px 10px;">
<table role="presentation" class="card" width="600" cellpadding="0" cellspacing="0" style="width:600px;background:{WHITE};">
{head}{body}
</table></td></tr></table></body></html>"""


def button(label, href="{{ event.extra.checkout_url }}", bg=G, fg=WHITE):
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" width="100%"><tr><td align="center" bgcolor="{bg}">'
            f'<a href="{href}" style="display:block;padding:16px 28px;font:600 16px/20px {SANS};color:{fg};text-decoration:none;">{label}</a>'
            f'</td></tr></table>')


def hero_block(ctx, key):
    if ctx.live and ctx.mode == "now":
        # Live stop-gaps: H1 source is 490px with rounded corners, so it sits inset; H2 source is a square cut-out.
        if key == "H1":
            return (f'<tr><td class="px" style="padding:28px 44px 0;"><img class="full" src="{ctx.img[key]}" width="512" alt="Golfer walking with an electric trolley" '
                    f'style="width:512px;max-width:100%;height:auto;"></td></tr>')
        if key == "H2":
            return (f'<tr><td align="center" style="padding:20px 44px 0;"><img src="{ctx.img[key]}" width="360" alt="Folded electric trolley" '
                    f'style="width:360px;max-width:100%;height:auto;margin:0 auto;"></td></tr>')
    s = ctx.slot(key, 600, 360)
    return f'<tr><td style="padding:0;">{s}</td></tr>' if s else ""


def intro(eyebrow, headline, text=""):
    t = f'<p style="margin:0;font:17px/26px {SANS};color:{INK};">{text}</p>' if text else ""
    return (f'<tr><td class="px" style="padding:36px 44px 0;">'
            f'<p style="margin:0 0 10px;font:600 11px/16px {SANS};letter-spacing:.14em;text-transform:uppercase;color:{GOLD};">{eyebrow}</p>'
            f'<h1 class="h1" style="margin:0 0 12px;font:700 34px/40px {SERIF};color:{DG};">{headline}</h1>{t}</td></tr>')


def product_card(ctx, big=True):
    t, q, p = PRODUCT
    if ctx.live:
        t, q, p = "{{ item.product.title }}", "{{ item.quantity }}", "£{{ item.line_price|floatformat:2 }}"
        img = "{{ item.product.images.0.src }}"
    else:
        img = ctx.img["product"]
    loop_open, loop_close = ("{% for item in event.extra.line_items %}", "{% endfor %}") if ctx.live else ("", "")
    if big:
        return (f'<tr><td class="px" style="padding:26px 44px 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid {LINE};">{loop_open}'
                f'<tr><td align="center" style="padding:20px 20px 4px;"><img src="{img}" width="220" alt="{t}" style="width:220px;height:auto;margin:0 auto;"></td></tr>'
                f'<tr><td align="center" style="padding:6px 24px 22px;font:15px/22px {SANS};color:{INK};"><strong style="font-weight:600;">{t}</strong><br>'
                f'<span style="color:{MUTED};">Qty {q} · </span><strong style="font-weight:600;">{p}</strong></td></tr>{loop_close}</table></td></tr>')
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid {LINE};border-bottom:1px solid {LINE};">{loop_open}<tr>'
            f'<td width="84" style="padding:12px 12px 12px 0;"><img src="{img}" width="72" height="72" alt="{t}" style="width:72px;height:72px;"></td>'
            f'<td style="padding:12px 0;font:14px/20px {SANS};color:{INK};"><strong style="font-weight:600;">{t}</strong><br><span style="color:{MUTED};">Qty {q} · {p}</span></td></tr>{loop_close}</table>')


def trust():
    return (f'<tr><td class="px" style="padding:0 44px 32px;"><p style="margin:0;font:14px/20px {SANS};color:{INK};">'
            f'Rated <strong style="font-weight:600;">4.8 out of 5</strong> on <a href="https://uk.trustpilot.com/review/evolutiongolf.co.uk" style="color:{G};font-weight:600;">Trustpilot</a> from 611 reviews</p></td></tr>')


def usp():
    sep = f'<span style="color:{GOLD};">&nbsp;&nbsp;·&nbsp;&nbsp;</span>'
    items = ["Free UK delivery", "Expert advice from people who play", "Trade-in on clubs and trolleys", "Custom fitting centre"]
    return (f'<tr><td class="px" align="center" style="background:{CREAM};padding:14px 32px;font:600 12px/20px {SANS};'
            f'letter-spacing:.03em;color:{DG};">{sep.join(items)}</td></tr>')


def footer(ctx):
    a = f'style="color:{WHITE};text-decoration:none;"'
    dot = f'<span style="color:{GOLD};">&nbsp;·&nbsp;</span>'
    return (f'<tr><td align="center" bgcolor="{DG}" style="background:{DG};padding:32px 24px 28px;">'
            f'<img src="{ctx.img["roundel"]}" width="44" height="44" alt="Evolution Golf" style="width:44px;height:44px;margin:0 auto 16px;">'
            f'<p style="margin:0 0 12px;font:13px/20px {SANS};color:#CFE0D6;">Evolution Golf, Unit 3, Parvenah Park, Embankment Way, Ringwood, BH24 1WL</p>'
            f'<p style="margin:0 0 18px;font:600 13px/20px {SANS};">' + dot.join(f'<a href="{u}" {a}>{n}</a>' for n, u in SOCIAL.items()) + '</p>'
            f'<p class="foot" style="margin:0;font:12px/18px {SANS};color:#A9C2B5;">You\'re receiving this because you started a checkout at evolutiongolf.co.uk.<br>'
            + unsub(ctx, "#CFE0D6") + '</p></td></tr>')


def ruled_rows(items, ctx):
    out = ""
    for label, text in items:
        row = (f'<tr><td class="stack" width="150" style="padding:16px 16px 6px 0;border-top:1px solid {LINE};vertical-align:top;'
                f'font:700 17px/24px {SERIF};color:{DG};">{label}</td>'
                f'<td class="stack nb" style="padding:16px 0;border-top:1px solid {LINE};vertical-align:top;font:15px/23px {SANS};color:{INK};">{text}</td></tr>')
        out += ctx.if_motocaddy(row) if label == "Warranty" else row
    return f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{out}</table>'


CHECKS = [("Range.", f"Does the battery cover your usual round with margin? 18-hole lithium suits most; go 36 if you play twice on a Saturday."),
          ("Boot.", "Fold it in your head: will it go in with your bag?"),
          ("Hills.", "If your course has them, downhill control matters more than any gadget.")]


def checks_block():
    rows = ""
    for i, (label, text) in enumerate(CHECKS, 1):
        rows += (f'<tr><td width="44" style="padding:16px 0;border-top:1px solid {LINE};vertical-align:top;font:700 30px/30px {SERIF};color:{GOLD};">{i}</td>'
                 f'<td style="padding:16px 0;border-top:1px solid {LINE};vertical-align:top;font:16px/24px {SANS};color:{INK};">'
                 f'<strong style="font-weight:600;color:{DG};">{label}</strong> {text}</td></tr>')
    return f'<tr><td class="px" style="padding:22px 44px 12px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr>'


# ---------------- emails ----------------
def e1(ctx):
    yt = ("https://www.youtube.com/results?search_query={{ event.extra.line_items.0.product.title|urlencode }}+review"
          if ctx.live else "https://www.youtube.com/results?search_query=Motocaddy+M1+DHC+review")
    rows = [("Delivery", "Free to the UK mainland, usually 3 to 5 working days."),
            ("Warranty", "2 years on the trolley."),
            ("Paying for it", "Klarna or Clearpay at checkout if you'd rather spread it."),
            ("Right model?", f'Watch independent reviews of the {PRODUCT[0] if not ctx.live else "{{ event.extra.line_items.0.product.title }}"} on YouTube, '
                             f'or reply to this email and we\'ll help you choose.<br><a href="{yt}" style="color:{G};font-weight:600;">Watch reviews on YouTube →</a>')]
    body = (hero_block(ctx, "H1")
            + intro("Your basket is saved", "Still deciding? Fair enough. It's a big buy.", "Your basket is exactly where you left it.")
            + product_card(ctx)
            + f'<tr><td class="px" style="padding:20px 44px 36px;">{button("Back to my basket")}</td></tr>'
            + f'<tr><td class="px" style="padding:0 44px 8px;"><p style="margin:0 0 6px;font:700 20px/28px {SERIF};color:{DG};">The things people usually want to know before they commit:</p></td></tr>'
            + f'<tr><td class="px" style="padding:0 44px 28px;">' + ruled_rows(rows, ctx) + '</td></tr>'
            + trust() + usp() + footer(ctx))
    moto = "Free UK delivery, 2-year warranty, spread the cost. Pick up where you left off."
    other = "Free UK delivery, and you can spread the cost. Pick up where you left off."
    pre = ("{% if event.extra.line_items.0.product.vendor == 'Motocaddy' %}" + moto + "{% else %}" + other + "{% endif %}") if ctx.live else moto
    return shell(ctx, body, pre)


def membership_panel(ctx):
    # Live drafts skip M1: the stop-gap shows The Open's logo and rights are unconfirmed.
    img = "" if ctx.live else ctx.slot("M1", 520, 300, caption=False)
    img_row = f'<tr><td style="padding:0 0 22px;">{img}</td></tr>' if img else (
        f'<tr><td style="padding:0 0 16px;"><img src="{ctx.img["roundel"]}" width="48" height="48" alt="" style="width:48px;height:48px;"></td></tr>')
    stop = ""
    if ctx.mode == "now" and not ctx.live:
        stop = (f'<p style="margin:0 0 14px;font:600 10px/14px {SANS};letter-spacing:.06em;color:#CFE0D6;">'
                f'<span style="border:1px dashed #CFE0D6;border-radius:3px;padding:1px 4px;">STOP-GAP M1</span></p>')
    benefits = ["Free returns (4 a year)", "Free shipping over £10", "+5% trade-in value after 60 days", "48 hours' early access to new kit"]
    lis = "".join(f'<tr><td width="18" style="padding:3px 0;font:15px/22px {SANS};color:{GOLD};">•</td>'
                  f'<td style="padding:3px 0;font:15px/22px {SANS};color:{WHITE};">{b}</td></tr>' for b in benefits)
    return (f'<tr><td class="px" style="padding:12px 44px 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{DG}" style="background:{DG};">'
            f'<tr><td style="padding:28px 28px 30px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{img_row}</table>{stop}'
            f'<p style="margin:0 0 8px;font:600 11px/16px {SANS};letter-spacing:.14em;text-transform:uppercase;color:{GOLD};">Evolution Golf Membership · £36 a year</p>'
            f'<p style="margin:0 0 12px;font:700 22px/29px {SERIF};color:{WHITE};">Still happy with your pick? Good. One more thing before you check out.</p>'
            f'<p style="margin:0 0 14px;font:15px/23px {SANS};color:#E3ECE7;">Join before you check out and 10% comes off this order, then 10% off one order every month after. '
                        f'On an £800 trolley, that first 10% is £80.</p>'
            f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 16px;">{lis}</table>'
            f'<p style="margin:0 0 20px;font:13px/19px {SANS};color:#A9C2B5;">Renews at £36 a year. We\'ll remind you before it does, and you can cancel any time from your account. Member discounts can\'t be combined with other codes.</p>'
            + button("Join for £36 a year", href="https://evolutiongolf.co.uk/pages/members-page", bg=GOLD, fg=DG) +
            f'</td></tr></table></td></tr>')


def trade_in():
    return (f'<tr><td class="px" style="padding:28px 44px 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{CREAM};">'
            f'<tr><td style="padding:22px 24px;"><p style="margin:0 0 6px;font:700 19px/26px {SERIF};color:{DG};">Trade in what you\'ve got</p>'
            f'<p style="margin:0 0 10px;font:15px/23px {SANS};color:{INK};">Send us your old trolley and we\'ll take the value off your order. Members get a +5% bonus on top after 60 days. '
            f'Working electric trolleys {confirm("accepted brands")}</p>'
            f'<a href="#" style="font:600 15px/22px {SANS};color:{G};">Get a trade-in quote →</a> {confirm("URL")}</td></tr></table></td></tr>')


def seasonal():
    return (f'<tr><td class="px" style="padding:28px 44px 32px;"><p style="margin:0;padding:14px 0;border-top:1px solid {LINE};border-bottom:1px solid {LINE};'
            f'font:15px/22px {SANS};color:{INK};"><span style="font:600 11px/16px {SANS};letter-spacing:.14em;color:{GOLD};">SEASONAL&nbsp;&nbsp;</span>'
            f'New season, new kit. Trolleys, clubs and shoes are in. <a href="{NEW_IN}" style="color:{G};font-weight:600;">See what\'s new</a></p></td></tr>')


def e2(ctx):
    body = (hero_block(ctx, "H2") + intro("Before you buy", "Three quick checks") + checks_block()
            + membership_panel(ctx)
            + f'<tr><td class="px" style="padding:28px 44px 0;">{product_card(ctx, big=False)}</td></tr>'
            + f'<tr><td class="px" style="padding:16px 44px 0;">{button("Back to my basket")}</td></tr>'
            + seasonal() + usp() + footer(ctx))  # trade-in panel left out until quote URL + brands are confirmed
    return shell(ctx, body, "Battery range, boot space, hills. Then a note on membership.")


def e2m(ctx):
    note = (f'<tr><td class="px" style="padding:12px 44px 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{CREAM};">'
            f'<tr><td style="padding:22px 24px;"><p style="margin:0 0 8px;font:600 11px/16px {SANS};letter-spacing:.14em;text-transform:uppercase;color:{GOLD};">For members</p>'
            f'<p style="margin:0 0 10px;font:16px/24px {SANS};color:{INK};">You\'re an Evolution Golf member, so if you haven\'t used this month\'s 10% yet, it can go on this order. '
            f'Log in at checkout and it\'s applied.</p>'
            f'<p style="margin:0;font:16px/24px {SANS};color:{INK};">Your free returns and trade-in bonus apply too. Any question about the trolley itself, just reply.</p></td></tr></table></td></tr>')
    body = (hero_block(ctx, "H2") + intro("Before you buy", "Three quick checks") + checks_block() + note
            + f'<tr><td class="px" style="padding:24px 44px 0;">{product_card(ctx, big=False)}</td></tr>'
            + f'<tr><td class="px" style="padding:16px 44px 36px;">{button("Back to my basket")}</td></tr>'
            + usp() + footer(ctx))
    return shell(ctx, body, "Log in at checkout and it's applied. Anything else we can answer?")


def e3(ctx):
    p = f'margin:0 0 16px;font:16px/25px {SANS};color:{INK};'
    photo = ctx.slot("A1", 72, 72, caption=False)
    if ctx.mode == "slots":
        photo = (f'<td width="92" style="padding-right:16px;vertical-align:top;"><table role="presentation" cellpadding="0" cellspacing="0"><tr>'
                 f'<td width="76" height="76" align="center" style="width:76px;height:76px;background:{SLOTBG};border:2px dashed {GOLD};border-radius:50%;'
                 f'font:700 11px/14px {SANS};letter-spacing:.1em;color:{GOLD};">IMAGE<br>A1</td></tr></table></td>')
    else:
        photo = ""
    sig = (f'<table role="presentation" cellpadding="0" cellspacing="0"><tr>{photo}<td style="vertical-align:top;font:16px/24px {SANS};color:{INK};">'
           f'Alex<br><span style="color:{MUTED};">Head of Ecommerce, Evolution Golf</span></td></tr></table>')
    hi = "{{ person.first_name|default:'there' }}" if ctx.live else "there"
    prod = "{{ event.extra.line_items.0.product.title }}" if ctx.live else PRODUCT[0]
    basket = "{{ event.extra.checkout_url }}" if ctx.live else "#"
    body = (f'<tr><td class="px" style="padding:36px 44px 28px;">'
            f'<p style="{p}">Hi {hi},</p>'
            f'<p style="{p}">Alex from Evolution Golf. I can see you were looking at the {prod}. Good trolley.</p>'
            f'<p style="{p}">If you\'re not sure it\'s the right one — the course you play, how often, whether you\'d use GPS — reply to this and I\'ll give you a straight answer. If a cheaper model would do the job, I\'ll say so.</p>'
            f'<p style="{p}">If you\'ve already bought elsewhere, no problem at all. Ignore this one.</p>'
            f'{sig}<p style="margin:22px 0 0;font:15px/22px {SANS};"><a href="{basket}" style="color:{G};">My basket</a></p></td></tr>'
            f'<tr><td class="px foot-light" style="padding:18px 44px 24px;border-top:1px solid {LINE};font:12px/18px {SANS};color:{MUTED};">'
            f'Evolution Golf, Unit 3, Parvenah Park, Embankment Way, Ringwood, BH24 1WL<br>'
            + unsub(ctx, MUTED) + '</td></tr>')
    return shell(ctx, body, "Tell me your course and how you play and I'll tell you if it's the right model.", bg=WHITE, header=False)


EMAILS = [
    dict(key="e1", fn=e1, name="E1 · Basket saved", timing="1 hour after checkout", sender="⛳ Evolution Golf",
         subject="Your trolley's saved, {{ first name }}", preview="Free UK delivery, 2-year warranty, spread the cost. Pick up where you left off.", slots=["H1", "P1"]),
    dict(key="e2", fn=e2, name="E2 · Non-member", timing="Next day, 09:30 · no MemberTier", sender="⛳ Evolution Golf",
         subject="How to be sure it's the right trolley", preview="Battery range, boot space, hills. Then a note on membership.", slots=["H2", "M1", "P1"]),
    dict(key="e2m", fn=e2m, name="E2m · Member", timing="Next day, 09:30 · has MemberTier", sender="⛳ Evolution Golf",
         subject="Your member discount can go on this", preview="Log in at checkout and it's applied. Anything else we can answer?", slots=["H2", "P1"]),
    dict(key="e3", fn=e3, name="E3 · From Alex", timing="Day 3, 09:30", sender="Alex at Evolution Golf",
         subject="Want a second opinion on that trolley?", preview="Tell me your course and how you play and I'll tell you if it's the right model.", slots=["A1"]),
]
MODES = ["slots", "now", "none"]


def build():
    images = {k: data_uri(IMG_DIR / f) for k, f in PREV_FILES.items()}
    prev = {k: f"__IMG_{k}__" for k in PREV_FILES}
    live_dir = OUT / "f3-b"; live_dir.mkdir(exist_ok=True)
    frames = {}
    for e in EMAILS:
        for m in MODES:
            (live_dir / f"{e['key']}-{m}.html").write_text(e["fn"](Ctx(LIVE, m, True, live=True)))
            frames[f"{e['key']}|{m}"] = e["fn"](Ctx(prev, m, True))
    meta = [{k: v for k, v in e.items() if k != "fn"} for e in EMAILS]
    tpl = (OUT / "f3_b_template.html").read_text()
    page = tpl.replace("/*__DATA__*/null", json.dumps({"emails": meta, "slots": SLOTS, "frames": frames, "images": images}))
    (OUT / "preview.html").write_text(page)
    print("preview.html", len(page) // 1024, "KB")


if __name__ == "__main__":
    build()

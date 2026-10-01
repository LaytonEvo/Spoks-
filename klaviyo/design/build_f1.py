"""F1 Welcome (non-customers), built in design B ("On the course") with the Astra icon library.

Two-group rebuild (Layton, 1 Oct 2026): E2 has two versions, Hardware (trolleys, clubs, used clubs) and
Everything else, instead of the pack's four.
Emails: E1 (member welcome), E2h, E2e, E3 (from Alex), E4 (two ways to pay less). SMS 1 is plain text.
Image modes as F3: slots (briefs), now (same as none until stock photos arrive), none.
Writes klaviyo/design/f1/<email>.html (live, Klaviyo tags, hosted icons) and f1-preview.html (data URIs).

Run: python3 klaviyo/design/build_f1.py <scratch img dir>
"""
import json, pathlib, re, sys

import build_f3_b as b
from build_f3_b import G, DG, GOLD, CREAM, INK, MUTED, LINE, WHITE, SLOTBG, SERIF, SANS, confirm, unsub, data_uri

OUT = pathlib.Path(__file__).parent
ICON_DIR = OUT / "assets" / "icons-png"
ICON_WHITE_DIR = OUT / "assets" / "icons-white-png"
HOSTED = OUT / "icons-hosted.json"  # name -> Klaviyo CDN URL (icons imported into the Klaviyo library)

SITE = "https://evolutiongolf.co.uk"
URL = {
    "join": SITE + "/pages/members-page",
    "shop": SITE + "/",
    "new_in": b.NEW_IN,
    "electric": SITE + "/collections/electric-trolleys",
    "trolleys": SITE + "/collections/golf-trolleys",
    "fitting": SITE + "/pages/custom-fitting",
    "used": SITE + "/collections/approved-used-golf-clubs",
    "trade_in": SITE + "/pages/trade-in",
    "shoes": SITE + "/collections/golf-shoes",
    "clothing": SITE + "/collections/golf-clothing",
    "balls": SITE + "/collections/golf-balls",
    "contact": SITE + "/pages/contact-us",
}

SLOTS = {
    "W1": dict(emails="E1", where="Hero, under the header", what="Golfers on a UK course in good light: a fourball walking off a tee, or a wide fairway shot. No products in shot.",
               size="1200 × 720 px (5:3), JPG, under 250 KB", now="Stock photo to be chosen", now_status="Needed",
               none="Hero dropped. The welcome headline leads."),
    "W2": dict(emails="E2 Hardware", where="Hero, under the header", what="A golfer walking with an electric trolley, or a set of irons in a bag, on the course. Brand not readable.",
               size="1200 × 720 px (5:3), JPG, under 250 KB", now="Stock photo to be chosen", now_status="Needed",
               none="Hero dropped. The eyebrow and headline lead."),
    "W3": dict(emails="E2 Everything else", where="Hero, under the header", what="Golf shoes on wet grass, or a golfer in waterproofs on a grey UK day.",
               size="1200 × 720 px (5:3), JPG, under 250 KB", now="Stock photo to be chosen", now_status="Needed",
               none="Hero dropped. The eyebrow and headline lead."),
    "A1": dict(emails="E3", where="Next to Alex's signature (optional)", what="Head-and-shoulders photo of Alex, plain background, smiling.",
               size="240 × 240 px square, JPG", now="Nothing in the library", now_status="Needed",
               none="Text signature only (plain-letter style)."),
}

ICONS = ["monthly-prize-draw", "members-portal", "member-price-tag", "free-delivery", "expert-advice", "custom-fitting", "member-card", "member-card-gold", "free-returns",
         "free-delivery-members", "trade-in", "calendar", "electric-trolley", "used-pre-owned", "golf-shoe",
         "waterproof-jacket", "golf-ball", "reply-to-email", "arrow-right", "check"]
WHITE_ICONS = ["free-returns", "free-delivery-members", "trade-in", "calendar"]


class Ctx(b.Ctx):
    def __init__(self, img, mode, web_fonts, icons, live=False):
        super().__init__(img, mode, web_fonts, live)
        self.icons = icons

    def slot(self, key, w, h, style="", caption=True):
        if self.mode != "slots":
            return ""  # no stock photos chosen yet: "now" and "none" are the same
        s = SLOTS[key]
        return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
                f'<td align="center" height="{h}" style="height:{h}px;background:{SLOTBG};border:2px dashed {GOLD};padding:18px;{style}">'
                f'<p style="margin:0 0 6px;font:700 12px/16px {SANS};letter-spacing:.14em;color:{GOLD};">IMAGE {key}</p>'
                f'<p style="margin:0 0 6px;font:600 15px/21px {SANS};color:{DG};">{s["what"]}</p>'
                f'<p style="margin:0;font:13px/18px {SANS};color:{MUTED};">{s["size"]}</p></td></tr></table>')


def icon(ctx, name, size=24, white=False, alt=""):
    src = ctx.icons[("w:" if white else "") + name]
    return f'<img src="{src}" width="{size}" height="{size}" alt="{alt}" style="width:{size}px;height:{size}px;display:block;">'


def first_name(ctx):
    return "{{ person.first_name|default:'there' }}" if ctx.live else "there"


def name_suffix(ctx):
    """", Sam" when we know the name, nothing when we don't (avoids "Welcome, there.")."""
    return "{% if person.first_name %}, {{ person.first_name }}{% endif %}" if ctx.live else ", Sam"


def hero(ctx, key):
    s = ctx.slot(key, 600, 360)
    return f'<tr><td style="padding:0;">{s}</td></tr>' if s else ""


def p(text, size=17, color=INK, margin="0 0 16px"):
    return f'<p style="margin:{margin};font:{size}px/{size + 9}px {SANS};color:{color};">{text}</p>'


def text_row(html, pad="0 44px"):
    return f'<tr><td class="px" style="padding:{pad};">{html}</td></tr>'


def link(label, href, color=G):
    return (f'<a href="{href}" style="font:600 16px/24px {SANS};color:{color};text-decoration:underline;'
            f'text-underline-offset:3px;">{label}</a><span style="font:600 16px/24px {SANS};color:{color};">&nbsp;→</span>')


def button(label, href, bg=G, fg=WHITE, align="left"):
    # Spec: 48px tall, 6px radius, Inter 600 16/24, 24px side padding, intrinsic width.
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" align="{align}"><tr>'
            f'<td bgcolor="{bg}" style="background:{bg};border-radius:6px;">'
            f'<a href="{href}" style="display:inline-block;padding:12px 24px;font:600 16px/24px {SANS};color:{fg};'
            f'text-decoration:none;border-radius:6px;">{label}</a></td></tr></table>')


def usp3(ctx):
    """Three-item USP strip (spec: cream, 8px radius, 20px padding, 186/1/186/1/186)."""
    items = [("free-delivery", "Free delivery over £50"), ("expert-advice", "Advice from golfers"), ("custom-fitting", "Custom fitting")]
    cells = []
    for name, label in items:
        cells.append(f'<td class="usp-c" width="186" align="center" valign="top" style="width:186px;">'
                     f'<table role="presentation" cellpadding="0" cellspacing="0" align="center"><tr><td align="center">{icon(ctx, name)}</td></tr></table>'
                     f'<p style="margin:8px 0 0;font:600 14px/20px {SANS};color:{DG};">{label}</p></td>')
    div = f'<td width="1" style="width:1px;background:{LINE};font-size:0;line-height:0;">&nbsp;</td>'
    return (f'<tr><td class="px" style="padding:8px 20px 28px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            f'<tr><td style="background:{CREAM};border-radius:8px;padding:20px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            + div.join(cells) + '</tr></table></td></tr></table></td></tr>')


def member_note(ctx, heading, body, label="See what membership includes", href=URL["join"]):
    """Light membership panel (spec: cream, 40px gold-detail card icon, Fraunces 22/28, body 14/20, link)."""
    return (f'<tr><td class="px" style="padding:12px 20px 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            f'<tr><td style="background:{CREAM};border-radius:8px;padding:24px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td width="40" valign="middle" style="width:40px;">{icon(ctx, "member-card-gold", 40)}</td><td width="24" style="width:24px;"></td>'
            f'<td valign="middle"><p style="margin:0 0 8px;font:500 22px/28px {SERIF};color:{DG};">{heading}</p>'
            f'<p style="margin:0 0 12px;font:14px/20px {SANS};color:{MUTED};">{body}</p>{link(label, href)}</td>'
            f'</tr></table></td></tr></table></td></tr>')


def icon_rows(ctx, rows):
    """Icon + heading + text rows separated by hairlines."""
    out = ""
    for name, head, text, extra in rows:
        out += (f'<tr><td width="48" valign="top" style="width:48px;padding:20px 0;border-top:1px solid {LINE};">{icon(ctx, name, 32)}</td>'
                f'<td valign="top" style="padding:20px 0;border-top:1px solid {LINE};">'
                f'<p style="margin:0 0 6px;font:500 20px/27px {SERIF};color:{DG};">{head}</p>'
                f'<p style="margin:0 0 {10 if extra else 0}px;font:16px/24px {SANS};color:{INK};">{text}</p>{extra}</td></tr>')
    return text_row(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{out}</table>', "8px 44px 20px")


def footer(ctx, reason="you joined the Evolution Golf mailing list"):
    a = f'style="color:{WHITE};text-decoration:none;"'
    dot = f'<span style="color:{GOLD};">&nbsp;·&nbsp;</span>'
    return (f'<tr><td align="center" bgcolor="{DG}" style="background:{DG};padding:32px 24px 28px;">'
            f'<img src="{ctx.img["roundel"]}" width="44" height="44" alt="Evolution Golf" style="width:44px;height:44px;margin:0 auto 16px;">'
            f'<p style="margin:0 0 12px;font:13px/20px {SANS};color:#CFE0D6;">Evolution Golf, Unit 3, Parvenah Park, Embankment Way, Ringwood, BH24 1WL</p>'
            f'<p style="margin:0 0 18px;font:600 13px/20px {SANS};">' + dot.join(f'<a href="{u}" {a}>{n}</a>' for n, u in b.SOCIAL.items()) + '</p>'
            f'<p class="foot" style="margin:0;font:12px/18px {SANS};color:#A9C2B5;">You\'re receiving this because {reason}.<br>'
            + unsub(ctx, "#CFE0D6") + '</p></td></tr>')


def intro(eyebrow, headline, text=""):
    return b.intro(eyebrow, headline, text)


def shell(ctx, body, pre, header=True):
    html = b.shell(ctx, body, pre, header=header)
    return html.replace(".full{width:100%!important;height:auto!important}",
                        ".full{width:100%!important;height:auto!important} .usp-c{padding:0 4px!important}")


# ---------------- emails ----------------
BENEFITS = [("free-returns", "Free returns, 4 a year"), ("free-delivery-members", "Free shipping over £10"),
            ("trade-in", "+5% trade-in value after 60 days"), ("calendar", "48 hours' early access to new kit")]


def membership_dark(ctx, heading, cta="Join for £36 a year"):
    lis = "".join(f'<tr><td width="34" valign="middle" style="width:34px;padding:5px 0;">{icon(ctx, n, 24, white=True)}</td>'
                  f'<td valign="middle" style="padding:5px 0;font:15px/22px {SANS};color:{WHITE};">{t}</td></tr>' for n, t in BENEFITS)
    return (f'<tr><td class="px" style="padding:8px 44px 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{DG}" style="background:{DG};border-radius:8px;">'
            f'<tr><td style="padding:28px 28px 30px;">'
            f'<p style="margin:0 0 8px;font:600 11px/16px {SANS};letter-spacing:.14em;text-transform:uppercase;color:{GOLD};">Evolution Golf Membership · £36 a year</p>'
            f'<p style="margin:0 0 12px;font:500 22px/29px {SERIF};color:{WHITE};">{heading}</p>'
            f'<p style="margin:0 0 14px;font:15px/23px {SANS};color:#E3ECE7;">10% off your first order, then 10% off one order every month after. Plus:</p>'
            f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 0 16px;">{lis}</table>'
            f'<p style="margin:0 0 20px;font:13px/19px {SANS};color:#A9C2B5;">Renews at £36 a year. We\'ll remind you before it does, and you can cancel any time from your account. '
            f'Member discounts can\'t be combined with other codes.</p>'
            + button(cta, URL["join"], bg=WHITE, fg=DG) +
            f'</td></tr></table></td></tr>')


def e1(ctx):
    body = (hero(ctx, "W1")
            + intro("Welcome to Evolution Golf", f"Welcome{name_suffix(ctx)}.",
                    "We're a golf shop run by people who play, and we'd rather help you into the right trolley than the expensive one.")
            + text_row(p("We don't send a stream of codes. If you want to pay less, we do membership instead.", margin="16px 0 20px"))
            + membership_dark(ctx, "Pay less on every month's order, starting with your first.")
            + text_row(p("Or just have a look round first: " + link("See what's new", URL["new_in"]), 16, margin="0"), "24px 44px 28px")
            + usp3(ctx) + b.trust() + footer(ctx))
    return shell(ctx, body, "10% off your first order with membership, and every month after. No codes to chase.")


def e2h(ctx):
    rows = [
        ("electric-trolley", "Choosing an electric trolley",
         "Four questions get you most of the way. <strong style=\"font-weight:600;\">Range:</strong> 18-hole lithium suits most golfers; go 36 if you play twice on a Saturday. "
         "<strong style=\"font-weight:600;\">Boot:</strong> will it fold in next to your bag? <strong style=\"font-weight:600;\">Hills:</strong> downhill control matters more than any gadget. "
         "<strong style=\"font-weight:600;\">GPS:</strong> nice to have, but a phone app does most of it.",
         link("Browse electric trolleys", URL["electric"])),
        ("custom-fitting", "Clubs: get fitted first",
         "A fitting on a launch monitor sorts out lie, shaft, length, grip and gapping before you spend anything. It beats guessing from a review.",
         link("Book a fitting", URL["fitting"])),
        ("used-pre-owned", "Approved used clubs",
         "The sensible way into better clubs for less. Every set is checked before it goes on sale " + confirm("grading wording") + ".",
         link("See approved used clubs", URL["used"])),
        ("trade-in", "Trade in what you've got",
         "Send us your old clubs or trolley and we'll take the value off your next order.",
         link("Get a trade-in quote", URL["trade_in"])),
    ]
    body = (hero(ctx, "W2")
            + intro("Trolleys and clubs", "The big buys, without the guesswork",
                    "No single product pushed at you. Just how we'd help a mate choose.")
            + icon_rows(ctx, rows)
            + member_note(ctx, "Members get more for their trade-in", "+5% trade-in value after 60 days, and 10% off one order a month.")
            + text_row(p("Not sure which way to go? Reply to this email and tell us how you play. A real golfer will answer.", 16, margin="0"), "28px 44px 28px")
            + usp3(ctx) + footer(ctx))
    return shell(ctx, body, "How to choose a trolley, why we fit clubs first, and the used route in.")


def e2e(ctx):
    rows = [
        ("golf-shoe", "Spiked or spikeless?",
         "Spiked shoes grip better on wet, hilly winter courses. Spikeless are comfier and work off the course too. Plenty of UK golfers keep a pair of each.",
         link("Shop golf shoes", URL["shoes"])),
        ("waterproof-jacket", "Staying dry",
         "Look for a fully waterproof jacket with taped seams, not just \"water resistant\". Layer underneath so you can swing freely.",
         link("Shop golf clothing", URL["clothing"])),
        ("golf-ball", "Which ball?",
         "Match the ball to your swing speed. Slower swings usually suit a softer ball; faster swings get more from a firmer tour ball. Not sure? Ask us.",
         link("Shop golf balls", URL["balls"])),
    ]
    body = (hero(ctx, "W3")
            + intro("Asked and answered", "Three things golfers ask us most",
                    "Straight answers from people who play.")
            + icon_rows(ctx, rows)
            + member_note(ctx, "10% off one order every month", "Membership is £36 a year and the first 10% comes off your first order.")
            + text_row(button("See what's new", URL["new_in"]), "28px 44px 32px")
            + usp3(ctx) + footer(ctx))
    return shell(ctx, body, "Spiked or spikeless, staying dry, and which ball. Answered straight.")


def e3(ctx):
    pp = f'margin:0 0 16px;font:16px/25px {SANS};color:{INK};'
    photo = ""
    if ctx.mode == "slots":
        photo = (f'<td width="92" style="padding-right:16px;vertical-align:top;"><table role="presentation" cellpadding="0" cellspacing="0"><tr>'
                 f'<td width="76" height="76" align="center" style="width:76px;height:76px;background:{SLOTBG};border:2px dashed {GOLD};border-radius:50%;'
                 f'font:700 11px/14px {SANS};letter-spacing:.1em;color:{GOLD};">IMAGE<br>A1</td></tr></table></td>')
    sig = (f'<table role="presentation" cellpadding="0" cellspacing="0"><tr>{photo}<td style="vertical-align:top;font:16px/24px {SANS};color:{INK};">'
           f'Alex<br><span style="color:{MUTED};">Head of Ecommerce, Evolution Golf</span></td></tr></table>')
    body = (f'<tr><td class="px" style="padding:36px 44px 28px;">'
            f'<p style="{pp}">Hi {first_name(ctx)},</p>'
            f'<p style="{pp}">Alex here, I run the online side at Evolution Golf. Quick one: if you\'re weighing up a trolley, some clubs or anything else, '
            f'reply to this email and tell me what you play and what you\'re trying to fix. I\'ll give you an honest answer, even if it\'s "don\'t buy that".</p>'
            f'<p style="{pp}">No product list in this one. Just the offer of a proper conversation.</p>'
            f'{sig}<p style="margin:22px 0 0;font:15px/22px {SANS};color:{MUTED};">Rather talk? Call us on <a href="tel:03301227089" style="color:{G};">0330 122 7089</a> '
            f'or use our <a href="{URL["contact"]}" style="color:{G};">contact page</a>.</p></td></tr>'
            f'<tr><td class="px foot-light" style="padding:18px 44px 24px;border-top:1px solid {LINE};font:12px/18px {SANS};color:{MUTED};">'
            f'Evolution Golf, Unit 3, Parvenah Park, Embankment Way, Ringwood, BH24 1WL<br>'
            + unsub(ctx, MUTED) + '</td></tr>')
    return shell(ctx, body, "Reply to this email and a real person who plays will answer.", header=False)


def way_card(ctx, n, name, head, text, cta, href):
    return (f'<tr><td class="px" style="padding:0 44px 16px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid {LINE};border-radius:8px;">'
            f'<tr><td style="padding:24px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td width="56" valign="top" style="width:56px;">{icon(ctx, name, 40)}</td><td valign="top">'
            f'<p style="margin:0 0 4px;font:600 11px/16px {SANS};letter-spacing:.14em;text-transform:uppercase;color:{GOLD};">Way {n}</p>'
            f'<p style="margin:0 0 8px;font:500 22px/28px {SERIF};color:{DG};">{head}</p>'
            f'<p style="margin:0 0 16px;font:16px/24px {SANS};color:{INK};">{text}</p>'
            + button(cta, href) + '</td></tr></table></td></tr></table></td></tr>')


def e4(ctx):
    body = (intro("Paying less at Evolution Golf", "We don't do endless codes. We do these two things.")
            + text_row("", "12px 44px 0")
            + way_card(ctx, 1, "member-card-gold", "Membership, £36 a year",
                       "10% off your first order, then 10% off one order every month. Free returns, free shipping over £10 and 48 hours' early access to new kit.",
                       "Join for £36 a year", URL["join"])
            + way_card(ctx, 2, "trade-in", "Trade in your old kit",
                       "Send us your old clubs or trolley and we'll take the value off your order. Members get +5% on top after 60 days.",
                       "Get a trade-in quote", URL["trade_in"])
            + text_row(p("Both work on your first order. Any questions, just reply.", 16, margin="0"), "12px 44px 28px")
            + usp3(ctx) + b.trust() + footer(ctx))
    return shell(ctx, body, "Membership and trade-in, explained. Neither is a code.")


SMS1 = "Evolution Golf: welcome, {{ person.first_name|default:'golfer' }}. Members get 10% off their first order and one order a month: https://evolutiongolf.co.uk/pages/members-page"
SMS1_SHOWN = "Evolution Golf: welcome, [first name]. Members get 10% off their first order and one order a month: evolutiongolf.co.uk/pages/members-page"

EMAILS = [
    dict(key="e1", fn=e1, name="E1 · Welcome", timing="Straight away", sender="⛳ Evolution Golf",
         subject="Welcome in. Here's how to pay less, no code needed", preview="10% off your first order with membership, and every month after. No codes to chase.",
         slots=["W1"]),
    dict(key="e2h", fn=e2h, name="E2 Hardware · Trolleys and clubs", timing="Day 1 · looked at trolleys or clubs", sender="⛳ Evolution Golf",
         subject="Trolleys and clubs: how we'd help you choose", preview="How to choose a trolley, why we fit clubs first, and the used route in.",
         slots=["W2"]),
    dict(key="e2e", fn=e2e, name="E2 Everything else · Most asked", timing="Day 1 · everyone else", sender="⛳ Evolution Golf",
         subject="Three things golfers ask us most", preview="Spiked or spikeless, staying dry, and which ball. Answered straight.",
         slots=["W3"]),
    dict(key="e3", fn=e3, name="E3 · From Alex", timing="Day 3", sender="Alex at Evolution Golf",
         subject="Got a golf question? Ask me", preview="Reply to this email and a real person who plays will answer.", slots=["A1"]),
    dict(key="e4", fn=e4, name="E4 · Two ways to pay less", timing="Day 6", sender="⛳ Evolution Golf",
         subject="Two ways to pay less at Evolution Golf", preview="Membership and trade-in, explained. Neither is a code.", slots=[]),
]
MODES = ["slots", "now", "none"]


def local_icons():
    d = {n: data_uri(ICON_DIR / f"eg-icon-{n}.png") for n in ICONS}
    d.update({"w:" + n: data_uri(ICON_WHITE_DIR / f"eg-icon-{n}-white.png") for n in WHITE_ICONS})
    return d


def page(frames, images):
    tpl = (OUT / "f3_b_template.html").read_text()
    swaps = [
        ("Evolution Golf · F3 Checkout abandonment · Trolleys · Design B", "Evolution Golf · F1 Welcome · Design B"),
        ("<h1>The trolley checkout sequence, on the course</h1>", "<h1>The welcome sequence, rebuilt</h1>"),
        ("All four emails in the chosen design, with the approved copy.",
         "Five emails in the chosen design with the new icons. E2 comes in two versions: Hardware (trolleys, clubs, used clubs) and Everything else."),
        ("Five image positions across the sequence. Three have stop-gaps from your Klaviyo library or Shopify, Alex's photo is optional and new, and the product photos come in automatically. Every email still works with none of the new images.",
         "Three stock photos and Alex's optional photo. Every email works without them, so the drafts go into Klaviyo without heroes and the photos drop in later."),
        ("Day 2, 18:00 · SMS consent only", "1 hour after E1 · SMS consent only"),
        ("Evolution Golf: your basket's still saved, [first name]. Free UK delivery, spread the cost with Klarna. Finish here: evolutiongolf.co.uk/…", SMS1_SHOWN),
        ("No images, no code, no deadline.", "Replaces the two 5% SMS codes. No code, no deadline."),
        ('"eg-f3b-view"', '"eg-f1-view"'),
    ]
    for a, c in swaps:
        if a not in tpl:
            raise SystemExit("template text not found: " + a[:50])
        tpl = tpl.replace(a, c)
    flags = """
      <li><strong>Welcome email 1:</strong> your current 5% email makes most of the welcome money, but it still sells the old Clubhouse offer (15% off, £19.99 a month). The draft uses the new membership email; you can swap the old one back in the Klaviyo editor if you want to.</li>
      <li><strong>Choosing E2:</strong> people who looked at trolleys or clubs in their first day get Hardware; everyone else gets Everything else. Klaviyo can't tag interest from link clicks here, so it uses what they browsed.</li>
      <li><strong>Send times:</strong> the flow tool can't set "send at 09:30". Set the time of day on each wait in the Klaviyo editor.</li>
      <li><strong>Starting a checkout:</strong> anyone who starts a checkout leaves this flow, so the basket emails take over. (The plan said "pause for 2 days"; Klaviyo can't join paths back together, so pausing would mean 16 copies of the same emails.)</li>
      <li><strong>Timing:</strong> E1 straight away, SMS 1 hour later, E2 the next day, E3 two days after that, E4 three days after that.</li>
      <li><strong>Still to confirm:</strong> the wording for how used clubs are checked.</li>
      <li><strong>Trustpilot figure:</strong> 4.8 from 611 reviews is written into E1 and E4, so it needs re-checking every quarter.</li>
    """
    tpl = re.sub(r'(<section class="block flags">.*?<ol>).*?(</ol>)', lambda m: m.group(1) + flags + m.group(2), tpl, flags=re.S)
    return tpl.replace("/*__DATA__*/null", json.dumps({"emails": [{k: v for k, v in e.items() if k != "fn"} for e in EMAILS],
                                                        "slots": SLOTS, "frames": frames, "images": images}))


def build(img_dir):
    icons = local_icons()
    images = {k: data_uri(img_dir / f) for k, f in {"logo": "p-logo.png", "roundel": "p-roundel.png"}.items()}
    prev = {k: f"__IMG_{k}__" for k in images}
    frames = {f"{e['key']}|{m}": e["fn"](Ctx(prev, m, True, icons)) for e in EMAILS for m in MODES}
    (OUT / "f1-preview.html").write_text(page(frames, images))
    if HOSTED.exists():
        hosted = json.loads(HOSTED.read_text())
        live = {"logo": b.LIVE["logo"], "roundel": b.LIVE["roundel"]}
        for e in EMAILS:
            (OUT / "f1" / f"{e['key']}.html").write_text(e["fn"](Ctx(live, "none", True, hosted, live=True)))
        print("live files written")
    print("f1-preview.html", (OUT / "f1-preview.html").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    build(pathlib.Path(sys.argv[1]))

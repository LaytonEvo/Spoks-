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
from build_f3_b import ON_DARK, G, DG, GOLD, CREAM, INK, HEAD, MUTED, LINE, WHITE, SLOTBG, SERIF, SANS, confirm, unsub, data_uri, eyebrow

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
    "klarna": SITE + "/pages/klarna",
}

# Photo briefs (Layton, 6 Oct 2026). Heroes show at 600 × 360 in the email; supply at 2× so they're sharp on phones.
HERO_SIZE = "Supply 1200 × 720 px (landscape, 5:3). Shows at 600 × 360. JPG, under 250 KB. Keep the subject in the middle third (phones crop the edges). No text on the photo."
SLOTS = {
    "W1": dict(emails="F1 E1 Welcome and F2 Free E1", title="Your team or your shop", where="Across the top, under the logo",
               what="A real photo of the Evolution Golf team: in the shop, in the fitting bay, or on the course together. It proves the opening line, \"a golf shop run by people who play\".",
               alt="Second choice: a small group of club golfers walking off a tee on a UK course.",
               source="Your own photo if at all possible. Stock undercuts the \"real people\" message.",
               size=HERO_SIZE, now="Supplied 7 Oct (in the Klaviyo library)", now_status="Have", none="Without it, the welcome headline leads."),
    "W2": dict(emails="E2 Hardware", title="A trolley out on the course", where="Across the top, under the logo",
               what="A golfer walking a fairway with an electric trolley, trolley clearly in shot. Trolleys are your biggest seller and this email talks about them first.",
               alt="Second choice: someone being fitted on a launch monitor in your fitting bay.",
               source="Stock is fine for the trolley shot. A fitting-bay shot works better as your own.",
               size=HERO_SIZE, now="Supplied 7 Oct (in the Klaviyo library)", now_status="Have", none="Without it, the headline leads."),
    "W3": dict(emails="E2 Everything else", title="Shoes and weather", where="Across the top, under the logo",
               what="Golf shoes on wet grass, or a golfer in waterproofs on a grey British day. Matches the \"spiked or spikeless\" and \"staying dry\" sections.",
               alt="", source="Stock is fine.",
               size=HERO_SIZE, now="Supplied 7 Oct (in the Klaviyo library)", now_status="Have", none="Without it, the headline leads."),
    "M1": dict(emails="F2 Annual E1 Welcome", title="A member out playing", where="Across the top, under the logo",
               what="A golfer on the first tee on a bright morning, ready to play, with a trolley or bag. It says the membership is about playing more, not paperwork.",
               alt="Second choice: a small group laughing on a green after a round.",
               source="Stock is fine. Pick someone who looks like your members, not a model.",
               size="Supplied as a wide 1024 × 338 panorama; shows as a 600 × 200 banner.", now="Supplied 7 Oct (in the Klaviyo library)", now_status="Have", none="Without it, the welcome headline leads."),
    "A1": dict(emails="F1 E3 From Alex", title="Alex", where="Small round photo next to his signature",
               what="Alex, head and shoulders, plain background, smiling. A face makes \"reply to me\" feel real.",
               alt="", source="Must be his own. If there isn't one, the email works without it.",
               size="Supply 240 × 240 px (square). Shows as a 76 px circle. JPG. Face centred with a little space around it.",
               now="Supplied 7 Oct (in the Klaviyo library)", now_status="Have", none="Text signature only (plain-letter style)."),
}
# Photos supplied by Layton, 7 Oct 2026 (cropped to 1200 x 720 / 240 x 240, hosted in the Klaviyo library).
PHOTOS = {"W1": "https://cdn.klaviyomail.com/company/SiyYRR/images/7d745e06-9b49-42df-92bb-4c6f3c48ac4e.jpeg",
          "W2": "https://cdn.klaviyomail.com/company/SiyYRR/images/e978ee24-82ca-4326-b2e0-dd366ca6d729.jpeg",
          "W3": "https://cdn.klaviyomail.com/company/SiyYRR/images/5bffdf31-4a7a-4327-81e7-30b16012080a.jpeg",
          "A1": "https://cdn.klaviyomail.com/company/SiyYRR/images/50596254-d610-4268-a459-f77bfb2dae1b.jpeg",
          "M1": "https://cdn.klaviyomail.com/company/SiyYRR/images/9ef9537c-b4e6-4871-981b-a0db1c224456.jpeg"}
PHOTO_SIZE = {"M1": (600, 200)}  # supplied as a 1024 x 338 panorama: shown as a wide 3:1 banner rather than blown up to 5:3
PHOTO_ALT = {"W1": "A golf course on a sunny day", "W2": "A golfer walking the course with an electric trolley",
             "W3": "A golfer's shoes on the fairway mid-swing", "A1": "Alex",
             "M1": "A golfer with a trolley on the first tee on a misty morning"}
PHOTO_PREVIEW = {"W1": "eg-w1.jpg", "W2": "eg-w2.jpg", "W3": "eg-w3.jpg", "A1": "eg-a1.jpg", "M1": "eg-m1.jpg"}  # in <img dir>/photos_out
PHOTO_RULES = [
    "People like your customers: ordinary club golfers of mixed ages, not tour pros or models.",
    "UK courses and UK weather: parkland, heath, some grey skies. No palm trees, desert courses or sunset silhouettes.",
    "Product in use, not posed: a trolley being walked, shoes on grass. Studio packshots belong in the basket emails.",
    "Nothing written on the photo: text goes in the email so it stays readable.",
    "Logos small: a badge on a trolley is fine; a brand name filling the frame isn't, unless it's the brand you want to push.",
]

ICONS = ["pay-later-instalments", "monthly-prize-draw", "members-portal", "member-price-tag", "free-delivery", "expert-advice", "custom-fitting", "member-card", "member-card-gold", "free-returns",
         "free-delivery-members", "trade-in", "calendar", "electric-trolley", "used-pre-owned", "golf-shoe",
         "waterproof-jacket", "golf-ball", "reply-to-email", "arrow-right", "check"]
WHITE_ICONS = ["free-returns", "free-delivery-members", "trade-in", "calendar", "monthly-prize-draw", "member-price-tag"]


class Ctx(b.Ctx):
    def __init__(self, img, mode, web_fonts, icons, live=False):
        super().__init__(img, mode, web_fonts, live)
        self.icons = icons

    def slot(self, key, w, h, style="", caption=True):
        if key in self.img and key in PHOTO_SIZE:
            w, h = PHOTO_SIZE[key]
        if self.mode == "slots" and key in self.img:  # photo supplied: show it, labelled
            return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td style="position:relative;">'
                    f'<img class="full" src="{self.img[key]}" width="{w}" height="{h}" alt="{PHOTO_ALT.get(key, "")}" '
                    f'style="width:{w}px;max-width:100%;height:auto;display:block;"></td></tr>'
                    f'<tr><td style="background:{GOLD};padding:6px 12px;font:700 11px/16px {SANS};letter-spacing:.12em;color:{WHITE};">'
                    f'PHOTO {key} · {SLOTS[key]["title"].upper()} · SUPPLIED</td></tr></table>')
        if self.mode != "slots":
            if self.mode == "now" and key in self.img:
                return (f'<img class="full" src="{self.img[key]}" width="{w}" height="{h}" alt="{PHOTO_ALT.get(key, "")}" '
                        f'style="width:{w}px;max-width:100%;height:auto;display:block;">')
            return ""
        s = SLOTS[key]
        return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
                f'<td align="center" height="{h}" style="height:{h}px;background:{SLOTBG};border:2px dashed {GOLD};padding:18px;{style}">'
                f'<p style="margin:0 0 6px;font:700 12px/16px {SANS};letter-spacing:.14em;color:{GOLD};">PHOTO {key} · {s["title"].upper()}</p>'
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


def p(text, size=16, color=INK, margin="0 0 16px"):
    return f'<p style="margin:{margin};font:{size}px/{round(size * 1.65)}px {SANS};color:{color};">{text}</p>'


def text_row(html, pad="0 48px"):
    return f'<tr><td class="px" bgcolor="{WHITE}" style="padding:{pad};">{html}</td></tr>'


def link(label, href, color=G):
    return (f'<a href="{href}" style="font:600 15px/24px {SANS};color:{color};text-decoration:underline;'
            f'text-underline-offset:3px;">{label}</a>')


def button(label, href, bg=G, fg=WHITE, align="left"):
    return b.button(label, href, bg, fg)


def usp3(ctx):
    """Trust line (Free delivery over £50 | Advice from golfers | Custom fitting)."""
    return b.usp()


def member_note(ctx, heading, body, label="See what membership includes", href=URL["join"]):
    """The one secondary panel: stone strip, a short line on the left, a bold green link on the right."""
    return (f'<tr><td class="px" bgcolor="{WHITE}" style="padding:32px 48px 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            f'<tr><td bgcolor="{CREAM}" style="background:{CREAM};padding:22px 24px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td class="panel-l" valign="middle" style="font:15px/23px {SANS};color:{INK};"><strong style="font-weight:600;color:{HEAD};">{heading}.</strong> {body}</td>'
            f'<td class="panel-r" valign="middle" align="right" style="padding-left:16px;white-space:nowrap;">'
            f'<a href="{href}" style="font:600 15px/23px {SANS};color:{G};text-decoration:underline;text-underline-offset:3px;">{label}</a></td>'
            f'</tr></table></td></tr></table></td></tr>')


def panel(text, label, href):
    """Secondary panel with a plain line (no bold heading)."""
    return (f'<tr><td class="px" bgcolor="{WHITE}" style="padding:32px 48px 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            f'<tr><td bgcolor="{CREAM}" style="background:{CREAM};padding:22px 24px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            f'<td class="panel-l" valign="middle" style="font:15px/23px {SANS};color:{INK};">{text}</td>'
            f'<td class="panel-r" valign="middle" align="right" style="padding-left:16px;white-space:nowrap;">'
            f'<a href="{href}" style="font:600 15px/23px {SANS};color:{G};text-decoration:underline;text-underline-offset:3px;">{label}</a></td>'
            f'</tr></table></td></tr></table></td></tr>')


def benefits_table(rows):
    """Two columns: bold ink label (44%) and muted description, 1px hairlines, a hairline above the first row. Stacks on mobile."""
    out = ""
    for i, (label, desc) in enumerate(rows):
        top = f"border-top:1px solid {LINE};" if i == 0 else ""
        out += (f'<tr><td class="stack lbl" width="44%" valign="top" style="width:44%;padding:13px 16px 13px 0;{top}border-bottom:1px solid {LINE};'
                f'font:600 14.5px/21px {SANS};color:{HEAD};">{label}</td>'
                f'<td class="stack nb" valign="top" style="padding:13px 0;{top}border-bottom:1px solid {LINE};font:14.5px/21px {SANS};color:{MUTED};">{desc}</td></tr>')
    return f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 28px;">{out}</table>'


def h3(text, margin="0 0 10px"):
    return f'<h3 style="margin:{margin};font:400 28px/34px {SERIF};color:{HEAD};">{text}</h3>'


def feature(eyebrow_text, heading, lede, rows, cta=None, href=None, fine="", pad="28px 48px 0"):
    """Feature section: 3px brand-green top rule (not a box), eyebrow, serif H3, muted lede, benefits table, button, fine print."""
    btn = button(cta, href) if cta else ""
    fp = f'<p style="margin:16px 0 0;font:12.5px/19px {SANS};color:{MUTED};">{fine}</p>' if fine else ""
    ld = f'<p style="margin:0 0 24px;font:15px/23px {SANS};color:{MUTED};">{lede}</p>' if lede else ""
    return (f'<tr><td class="px" bgcolor="{WHITE}" style="padding:{pad};"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            f'<tr><td style="border-top:3px solid {G};padding:32px 0 0;">' + eyebrow(eyebrow_text) + h3(heading) + ld
            + (benefits_table(rows) if rows else "") + btn + fp + '</td></tr></table></td></tr>')


def icon_rows(ctx, rows):
    """Topic rows (the old icon rows, now without icons): bold label, text and an optional link, split by hairlines."""
    out = ""
    for i, (_name, head, text, extra) in enumerate(rows):
        out += (f'<tr><td valign="top" style="padding:20px 0;border-top:1px solid {LINE};{"border-bottom:1px solid " + LINE + ";" if i == len(rows) - 1 else ""}">'
                f'<p style="margin:0 0 6px;font:600 16px/24px {SANS};color:{HEAD};">{head}</p>'
                f'<p style="margin:0 0 {8 if extra else 0}px;font:15px/25px {SANS};color:{INK};">{text}</p>{extra}</td></tr>')
    return text_row(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{out}</table>', "12px 48px 0")


def footer(ctx, reason="you joined the Evolution Golf mailing list"):
    return b.footer(ctx, reason)


def intro(eyebrow, headline, text=""):
    return b.intro(eyebrow, headline, text)


def shell(ctx, body, pre, header=True):
    return b.shell(ctx, body, pre, header=header)


# ---------------- emails ----------------
# Benefits table (Layton, 7 Oct 2026): members get free delivery over £10; £50 for non-members.
BENEFITS = [("10% off monthly", "Your first order, then one order every month after."),
            ("Free delivery over £10", "Normally £50 for non-members."),
            ("Four free returns a year", "Start a return from your member portal."),
            ("Daily member deals", "Instant daily deals and exclusive member deals in your portal, plus 48 hours' early access to new kit."),
            ("Monthly prize draw", "Entered automatically every month.")]
FINE = ("Renews at £36 a year. We'll remind you before it does, and you can cancel any time from your account. "
        "Member discounts can't be combined with other codes.")


def membership_dark(ctx, heading, cta="Become a member, £36 a year"):
    """Kept name: now the white feature section with the green top rule."""
    return feature("Membership · £36 a year", heading, "Here's everything that comes with it.", BENEFITS, cta, URL["join"], FINE)


def e1(ctx):
    body = (hero(ctx, "W1")
            + intro("Welcome to Evolution Golf", f"Welcome{name_suffix(ctx)}.",
                    "We're a golf shop run by people who play, and we'd rather help you into the right trolley than the expensive one.")
            + text_row(p("We don't send a stream of codes. If you want to pay less, we do membership instead.", margin="0 0 8px"))
            + membership_dark(ctx, "10% off one order every month, starting with your first.")
            + panel("Not ready yet? Have a look round first.", "See what's new", URL["new_in"])
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
        ("pay-later-instalments", "Spread the cost",
         "Big buy? Pay in 3 interest-free instalments with Klarna at checkout. A third today, the rest over the next two months, no fees.",
         link("How Klarna works", URL["klarna"])),
    ]
    body = (hero(ctx, "W2")
            + intro("Trolleys and clubs", "The big buys, without the guesswork",
                    "No single product pushed at you. Just how we'd help a mate choose.")
            + icon_rows(ctx, rows)
            + member_note(ctx, "10% off one order every month", "Plus instant daily deals in your portal and a prize draw every month.")
            + text_row(p("Not sure which way to go? Reply to this email and tell us how you play. A real golfer will answer.", 16, margin="0"), "28px 48px 28px")
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
            + text_row(button("See what's new", URL["new_in"]), "28px 48px 32px")
            + usp3(ctx) + footer(ctx))
    return shell(ctx, body, "Spiked or spikeless, staying dry, and which ball. Answered straight.")


def e3(ctx):
    pp = f'margin:0 0 16px;font:16px/25px {SANS};color:{INK};'
    photo = ""
    if ctx.mode in ("now", "slots") and "A1" in ctx.img:
        photo = (f'<td width="92" style="padding-right:16px;vertical-align:top;"><img src="{ctx.img["A1"]}" width="76" height="76" alt="Alex" '
                 f'style="width:76px;height:76px;border-radius:50%;display:block;"></td>')
    if ctx.mode == "slots" and not photo:
        photo = (f'<td width="92" style="padding-right:16px;vertical-align:top;"><table role="presentation" cellpadding="0" cellspacing="0"><tr>'
                 f'<td width="76" height="76" align="center" style="width:76px;height:76px;background:{SLOTBG};border:2px dashed {GOLD};border-radius:50%;'
                 f'font:700 11px/14px {SANS};letter-spacing:.1em;color:{GOLD};">PHOTO<br>A1</td></tr></table></td>')
    sig = (f'<table role="presentation" cellpadding="0" cellspacing="0"><tr>{photo}<td style="vertical-align:top;font:16px/24px {SANS};color:{INK};">'
           f'Alex<br><span style="color:{MUTED};">Head of Ecommerce, Evolution Golf</span></td></tr></table>')
    body = (f'<tr><td class="px" bgcolor="#FFFFFF" style="padding:44px 48px 28px;">'
            f'<p style="{pp}">Hi {first_name(ctx)},</p>'
            f'<p style="{pp}">Alex here, I run the online side at Evolution Golf. Quick one: if you\'re weighing up a trolley, some clubs or anything else, '
            f'reply to this email and tell me what you play and what you\'re trying to fix. I\'ll give you an honest answer, even if it\'s "don\'t buy that".</p>'
            f'<p style="{pp}">No product list in this one. Just the offer of a proper conversation.</p>'
            f'{sig}<p style="margin:22px 0 0;font:15px/22px {SANS};color:{MUTED};">Rather talk? Call us on <a href="tel:03301227089" style="color:{G};">0330 122 7089</a> '
            f'or use our <a href="{URL["contact"]}" style="color:{G};">contact page</a>.</p></td></tr>'
            f'<tr><td class="px foot-light" style="padding:18px 48px 24px;border-top:1px solid {LINE};font:12px/18px {SANS};color:{MUTED};">'
            f'Evolution Golf, Unit 3, Parvenah Park, Embankment Way, Ringwood, BH24 1WL<br>'
            + unsub(ctx, MUTED) + '</td></tr>')
    return shell(ctx, body, "Reply to this email and a real person who plays will answer.", header=False)


def e4(ctx):
    body = (intro("Paying less at Evolution Golf", "We don't do endless codes. We do these two things.")
            + feature("Way 1", "Membership: 10% off one order every month",
                      "10% off your first order, then 10% off one order every month. Free returns, free delivery over £10 and 48 hours' early access to new kit.",
                      None, "Become a member, £36 a year", URL["join"], pad="12px 48px 0")
            + feature("Way 2", "Member-only deals and a monthly prize draw",
                      "Members get instant daily deals and exclusive member deals in the portal that you won't see anywhere else on the site, plus an entry into a prize draw every month. This month's prize is on the members page.",
                      None, pad="36px 48px 0")
            + text_row(link("See member deals and this month's prize", URL["join"]), "0 48px 0")
            + text_row(p("Both start the day you join. Any questions, just reply.", margin="0"), "28px 48px 0")
            + usp3(ctx) + b.trust() + footer(ctx))
    return shell(ctx, body, "Your monthly 10%, member deals and a monthly prize draw. No codes to chase.")


# A/B test (Layton, 7 Oct 2026): E1 with the button in the brighter site green, so it stands apart from the header and
# footer. Klaviyo's API can't add A/B tests to flows, so this variant is created as a template and the test is set up in the editor.
BUTTON_TEST = "#006747"


def button_variant(html):
    old = f'bgcolor="{G}" style="background:{G};border-radius:2px;"'
    assert html.count(old) == 1, "expected exactly one primary button"
    return html.replace(old, f'bgcolor="{BUTTON_TEST}" style="background:{BUTTON_TEST};border-radius:2px;"')


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
         subject="Two ways to pay less at Evolution Golf", preview="Your monthly 10%, member deals and a monthly prize draw. No codes to chase.", slots=[]),
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
    images = {k: data_uri(img_dir / f) for k, f in {"logo": "p-logo-white.png", "roundel": "p-roundel.png"}.items()}
    images.update({k: data_uri(img_dir.parent / "photos_out" / f) for k, f in PHOTO_PREVIEW.items()
                   if (img_dir.parent / "photos_out" / f).exists()})
    prev = {k: f"__IMG_{k}__" for k in images}
    frames = {f"{e['key']}|{m}": e["fn"](Ctx(prev, m, True, icons)) for e in EMAILS for m in MODES}
    (OUT / "f1-preview.html").write_text(page(frames, images))
    if HOSTED.exists():
        hosted = json.loads(HOSTED.read_text())
        live = {"logo": b.LIVE["logo"], "roundel": b.LIVE["roundel"], **PHOTOS}
        for e in EMAILS:
            (OUT / "f1" / f"{e['key']}.html").write_text(e["fn"](Ctx(live, "now", True, hosted, live=True)))
        (OUT / "f1" / "e1b.html").write_text(button_variant((OUT / "f1" / "e1.html").read_text()))
        print("live files written")
    print("f1-preview.html", (OUT / "f1-preview.html").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    build(pathlib.Path(sys.argv[1]))

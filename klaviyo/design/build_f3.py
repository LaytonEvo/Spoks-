"""F3 Checkout abandonment, two groups (Layton, 1 Oct 2026), in the editorial design (7 Oct 2026).

Copy: the F3 copy doc (https://claude.ai/code/artifact/e9605082-60e3-48ae-83e0-4b7011c79bf3), with Layton's defaults of 7 Oct:
no optional code; delivery days marked CONFIRM; Email 3 Everything else kept; the £800 example for trolley baskets only.
  Hardware (trolley, club or used club in the basket): E1 basket saved (1 h), E2 how to be sure (next day 09:30), SMS (day 2 18:00),
  E3 from Alex (day 3 09:30).
  Everything else: E1 basket saved (45 min), E2 members pay less (next day 09:30), SMS (day 2 18:00), E3 last nudge (day 3 17:30).
  Annual members get E2m "Your 10% can go on this" instead of either E2 (members' edition, card badge).
Inside E2 Hardware, the trolley checks and the club-fitting block only show when the basket holds that kind of item
(Klaviyo tags on the event's Collections). Writes klaviyo/design/f3/<key>.html (live, Klaviyo tags) and <key>.preview.html
(an example basket, for the dashboard).

Run: python3 klaviyo/design/build_f3.py
"""
import pathlib

import build_f3_b as b
import build_f1 as f1
import build_f2 as f2
from build_f1 import (G, CREAM, INK, HEAD, MUTED, LINE, WHITE, SANS, SERIF, confirm, unsub, intro, p, text_row, link, button,
                      member_note, feature, BENEFITS, FINE, URL, PHOTOS)

OUT = pathlib.Path(__file__).parent / "f3"
REASON = "you started a checkout at evolutiongolf.co.uk"
BASKET = "{{ event.extra.checkout_url }}"

# Shopify collection names on the Checkout Started event (checked 7 Oct 2026 against the store and a live event).
TROLLEYS = ["Push & Electric Golf Trolleys", "Electric Trolleys", "GPS Electric Trolleys", "Remote Electric Trolleys",
            "Motocaddy Electric Trolleys", "Motocaddy Golf Trolleys", "Motocaddy Electric Golf Trolleys", "Motocaddy Push Trolleys",
            "PowaKaddy Electric & Push Golf Trolleys", "PowaKaddy Electric Trolleys", "PowaKaddy Push Trolleys", "Push/Pull Trolleys",
            "Push Golf Trolleys", "Cube Golf Push Trolleys"]
CLUBS = ["Mens Golf Clubs", "Ladies Golf Clubs", "Women's Golf Clubs", "Junior Golf Clubs", "Left Handed Golf Clubs",
         "Drivers", "Fairways", "Fairway Woods", "Hybrids & Utility Irons", "Wedges", "Putters", "Custom Clubs",
         "Mens Custom Fitted Golf Clubs", "Golf Club Package Sets"]
USED = ["Approved Used Golf Clubs", "All Approved Used Golf Clubs"]
HARDWARE = TROLLEYS + CLUBS + USED


def has(names):
    return " or ".join(f'"{n}" in event.Collections' for n in names)


SAMPLE = {"title": "Motocaddy 2026 M1 DHC Standard Lithium Electric Golf Trolley", "qty": "1", "price": "£799.00",
          "img": "https://cdn.shopify.com/s/files/1/0499/9014/0061/files/2026M1DHCThumbnail.png"}


class Ctx(f1.Ctx):
    def when(self, cond, html, label):
        """Show html only when the Klaviyo condition holds; in the preview, show it with a small note saying when."""
        if self.live:
            return "{% if " + cond + " %}" + html + "{% endif %}"
        note = (f'<tr><td class="px" bgcolor="{WHITE}" style="padding:20px 48px 0;"><span style="display:inline-block;border:1px dashed {MUTED};'
                f'padding:1px 6px;font:600 10px/16px {SANS};letter-spacing:.06em;color:{MUTED};">SHOWN ONLY IF {label.upper()}</span></td></tr>')
        return note + html


def name_suffix(ctx):
    return "{% if person.first_name %}, {{ person.first_name }}{% endif %}" if ctx.live else ", Sam"


def basket(ctx, big=True):
    """Every item in the checkout: photo, name, quantity and price."""
    if ctx.live:
        t, q, pr, img = "{{ item.product.title }}", "{{ item.quantity }}", "£{{ item.line_price|floatformat:2 }}", "{{ item.product.images.0.src }}"
        o, c = "{% for item in event.extra.line_items %}", "{% endfor %}"
    else:
        t, q, pr, img, o, c = SAMPLE["title"], SAMPLE["qty"], SAMPLE["price"], SAMPLE["img"], "", ""
    size = 120 if big else 72
    rows = (f'{o}<tr><td width="{size + 20}" valign="middle" style="width:{size + 20}px;padding:16px 20px 16px 0;border-bottom:1px solid {LINE};">'
            f'<img src="{img}" width="{size}" height="{size}" alt="{t}" style="width:{size}px;height:{size}px;display:block;"></td>'
            f'<td valign="middle" style="padding:16px 0;border-bottom:1px solid {LINE};font:15px/23px {SANS};color:{INK};">'
            f'<strong style="font-weight:600;color:{HEAD};">{t}</strong><br><span style="color:{MUTED};">Qty {q}</span> · '
            f'<strong style="font-weight:600;color:{HEAD};">{pr}</strong></td></tr>{c}')
    return text_row(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid {LINE};">{rows}</table>',
                    "28px 48px 0" if big else "24px 48px 0")


def facts(ctx, heading, rows):
    """'The things people usually want to know': label | answer rows (the benefits-table pattern)."""
    out = ""
    for i, (label, text, cond) in enumerate(rows):
        top = f"border-top:1px solid {LINE};" if i == 0 else ""
        row = (f'<tr><td class="stack lbl" width="38%" valign="top" style="width:38%;padding:14px 16px 14px 0;{top}border-bottom:1px solid {LINE};'
               f'font:600 14.5px/21px {SANS};color:{HEAD};">{label}</td>'
               f'<td class="stack nb" valign="top" style="padding:14px 0;{top}border-bottom:1px solid {LINE};font:14.5px/22px {SANS};color:{INK};">{text}</td></tr>')
        out += ("{% if " + cond + " %}" + row + "{% endif %}") if (cond and ctx.live) else row
    return text_row(f'<h3 style="margin:0 0 16px;font:400 24px/30px {SERIF};color:{HEAD};">{heading}</h3>'
                    f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{out}</table>', "40px 48px 0")


def footer(ctx):
    return f1.footer(ctx, REASON)


def close(ctx):
    return b.usp() + b.trust() + footer(ctx)


def product_name(ctx):
    return "{{ event.extra.line_items.0.product.title }}" if ctx.live else SAMPLE["title"]


# ---------------- E1 ----------------
def e1h(ctx):
    yt = ("https://www.youtube.com/results?search_query={{ event.extra.line_items.0.product.title|urlencode }}+review"
          if ctx.live else "https://www.youtube.com/results?search_query=Motocaddy+M1+DHC+review")
    rows = [("Delivery", "Free UK delivery on orders over £50. " + confirm("usually 3 to 5 working days?"), None),
            ("Warranty", "2 years on the trolley.", "event.extra.line_items.0.product.vendor == 'Motocaddy'"),
            ("Paying for it", "Pay in 3 interest-free instalments with Klarna at checkout.", None),
            ("Right model?", f"Watch independent reviews of the {product_name(ctx)} on YouTube, or reply to this email and we'll help you choose.<br>"
                             + link("Watch reviews on YouTube", yt), None)]
    body = (intro("Your basket is saved", "Still deciding? Fair enough. It's a big buy.", "Your basket is exactly where you left it.")
            + basket(ctx) + text_row(button("Back to my basket", BASKET), "28px 48px 0")
            + facts(ctx, "The things people usually want to know before they commit", rows) + close(ctx))
    return f1.shell(ctx, body, "Pay in 3 with Klarna, and free UK delivery over £50. Pick up where you left off.")


def e1e(ctx):
    rows = [("Delivery", "Free UK delivery on orders over £50. Members get it from £10.", None),
            ("Paying for it", "Pay in 3 interest-free instalments with Klarna at checkout.", None),
            ("Not sure on size or fit?", "Reply to this email and we'll help.", None)]
    body = (intro("Your basket is saved", "Still want these? They're right where you left them.")
            + basket(ctx) + text_row(button("Back to my basket", BASKET), "28px 48px 0")
            + facts(ctx, "Good to know", rows) + close(ctx))
    return f1.shell(ctx, body, "Pick up where you left off. Free UK delivery on orders over £50.")


# ---------------- E2 ----------------
def e2m(ctx):
    """Annual members, both groups: members' edition with the card badge."""
    body = (f2.intro("Your basket", "Your 10% can go on this",
                     "You're an Evolution Golf member, so if you haven't used this month's 10% yet, it can go on this order. "
                     "Your code is in the Codes section of your member portal; use it at checkout.", card=True)
            + text_row(p("Your free returns apply too. Any question about what's in your basket, just reply.", margin="0"), "0 48px 0")
            + basket(ctx, big=False) + text_row(button("Back to my basket", BASKET), "28px 48px 0")
            + text_row(p("Need your code? " + link("Open my member portal", f2.PORTAL), 15, margin="0"), "20px 48px 40px")
            + footer(ctx))
    return f1.shell(ctx, body, "Use this month's code at checkout. Anything else we can answer?", members=True)


CHECKS = [("Range.", "Does the battery cover your usual round with margin? 18-hole lithium suits most; go 36 if you play twice on a Saturday."),
          ("Boot.", "Fold it in your head: will it go in with your bag?"),
          ("Hills.", "If your course has them, downhill control matters more than any gadget.")]


def e2h(ctx):
    trolley = (text_row(f'<h3 style="margin:0;font:400 24px/30px {SERIF};color:{HEAD};">Buying a trolley?</h3>', "28px 48px 0")
               + f2.steps(CHECKS))
    clubs = text_row(f'<h3 style="margin:0 0 8px;font:400 24px/30px {SERIF};color:{HEAD};">Buying clubs?</h3>'
                     + p("A fitting on a launch monitor sorts out lie, shaft, length and grip before you commit.", margin="0 0 8px")
                     + link("Book a fitting", URL["fitting"]), "28px 48px 0")
    neither = text_row(p("Not sure it's the right one? Reply to this email and tell us how you play. A real golfer will answer.", margin="0"), "20px 48px 0")
    lede = ("Then 10% off one order every month after."
            + (("{% if " + has(TROLLEYS) + " %} On an £800 trolley, that first 10% is £80.{% endif %}") if ctx.live
               else " On an £800 trolley, that first 10% is £80. " + confirm("").replace("CONFIRM", "TROLLEY BASKETS ONLY")))
    body = (intro("Before you buy", "A few quick checks")
            + ctx.when(has(TROLLEYS), trolley, "the basket has a trolley")
            + ctx.when(has(CLUBS), clubs, "the basket has new clubs")
            + (("{% if not " + has(TROLLEYS + CLUBS).replace(" or ", " and not ") + " %}" + neither + "{% endif %}") if ctx.live else "")
            + feature("Evolution Golf Membership · £36 a year", "Join before you check out and 10% comes off this order.", lede,
                      BENEFITS, "Become a member, £36 a year", URL["join"], FINE, pad="36px 48px 0", card=True)
            + basket(ctx, big=False) + text_row(link("Back to my basket", BASKET), "16px 48px 0")
            + close(ctx))
    return f1.shell(ctx, body, "A few quick checks before you buy. Then a note on membership.")


def e2e(ctx):
    body = (intro("Before you check out", "Members pay less on this, and every month after")
            + feature("Evolution Golf Membership · £36 a year", "10% off this order, then one order every month.",
                      "Join for £36 a year and 10% comes off this order. Then you get 10% off one order every month, free delivery from £10, "
                      "four free returns a year and a prize draw entry every month.",
                      None, "Become a member, £36 a year", URL["join"],
                      "Renews at £36 a year. We'll remind you before it does, and you can cancel any time from your account.",
                      pad="12px 48px 0", card=True)
            + basket(ctx, big=False) + text_row(link("Back to my basket", BASKET), "16px 48px 0")
            + close(ctx))
    return f1.shell(ctx, body, "10% off this order, then one order every month. Here's how.")


# ---------------- E3 ----------------
def e3h(ctx):
    """From Alex: a plain letter, no header, no buttons."""
    pp = f'margin:0 0 16px;font:16px/26px {SANS};color:{INK};'
    hi = "{{ person.first_name|default:'there' }}" if ctx.live else "Sam"
    photo = (f'<td width="92" style="padding-right:16px;vertical-align:top;"><img src="{PHOTOS["A1"]}" width="76" height="76" alt="Alex" '
             f'style="width:76px;height:76px;border-radius:50%;display:block;"></td>')
    sig = (f'<table role="presentation" cellpadding="0" cellspacing="0"><tr>{photo}<td style="vertical-align:top;font:16px/24px {SANS};color:{INK};">'
           f'Alex<br><span style="color:{MUTED};">Head of Ecommerce, Evolution Golf</span></td></tr></table>')
    body = (f'<tr><td class="px" bgcolor="{WHITE}" style="padding:44px 48px 28px;">'
            f'<p style="{pp}">Hi {hi},</p>'
            f'<p style="{pp}">Alex from Evolution Golf. I can see you were looking at the {product_name(ctx)}.</p>'
            f'<p style="{pp}">If you\'re not sure it\'s the right one (the course you play, how often, what you\'re trying to fix), reply to this '
            f'and I\'ll give you a straight answer. If something cheaper would do the job, I\'ll say so.</p>'
            f'<p style="{pp}">If you\'ve already bought elsewhere, no problem at all. Ignore this one.</p>'
            f'{sig}<p style="margin:22px 0 0;font:15px/22px {SANS};"><a href="{BASKET if ctx.live else "#"}" style="color:{G};">My basket</a></p></td></tr>'
            f'<tr><td class="px foot-light" bgcolor="{WHITE}" style="padding:18px 48px 24px;border-top:1px solid {LINE};font:12px/18px {SANS};color:{MUTED};">'
            f'Evolution Golf, Unit 3, Parvenah Park, Embankment Way, Ringwood, BH24 1WL<br>' + unsub(ctx, MUTED) + '</td></tr>')
    return f1.shell(ctx, body, "Tell me your course and how you play and I'll tell you if it's the right one.", header=False)


def e3e(ctx):
    body = (intro("Still in your basket", "Your basket's still here", "We'll stop reminding you after this one.")
            + basket(ctx, big=False) + text_row(button("Back to my basket", BASKET), "28px 48px 0")
            + member_note(ctx, "Join for £36 a year", "10% comes off this order, then one order every month.")
            + close(ctx))
    return f1.shell(ctx, body, "Your basket's saved. And if you join, 10% comes off it.")


SMS1 = ("Evolution Golf: your basket's still saved{% if person.first_name %}, {{ person.first_name }}{% endif %}. "
        "Pay in 3 interest-free with Klarna. Finish here: {{ event.extra.checkout_url }}")

BR, ALEX = "⛳ Evolution Golf", "Alex at Evolution Golf"
EMAILS = [
    dict(key="e1h", fn=e1h, name="E1 Hardware · Basket saved", timing="Hardware · 1 hour after checkout", sender=BR,
         subject="Your basket's saved{% if person.first_name %}, {{ person.first_name }}{% endif %}",
         preview="Pay in 3 with Klarna, and free UK delivery over £50. Pick up where you left off.", slots=[]),
    dict(key="e1e", fn=e1e, name="E1 Everything else · Basket saved", timing="Everything else · 45 minutes after checkout", sender=BR,
         subject="Your basket's saved{% if person.first_name %}, {{ person.first_name }}{% endif %}",
         preview="Pick up where you left off. Free UK delivery on orders over £50.", slots=[]),
    dict(key="e2m", fn=e2m, name="E2 Members · Your 10% can go on this", timing="Annual members, both groups · next day 09:30", sender=BR,
         subject="Your member 10% can go on this", preview="Use this month's code at checkout. Anything else we can answer?", slots=[]),
    dict(key="e2h", fn=e2h, name="E2 Hardware · How to be sure", timing="Hardware, non-members · next day 09:30", sender=BR,
         subject="How to be sure it's the right one", preview="A few quick checks before you buy. Then a note on membership.", slots=[]),
    dict(key="e2e", fn=e2e, name="E2 Everything else · Members pay less", timing="Everything else, non-members · next day 09:30", sender=BR,
         subject="Before you check out: members pay less", preview="10% off this order, then one order every month. Here's how.", slots=[]),
    dict(key="e3h", fn=e3h, name="E3 Hardware · From Alex", timing="Hardware · day 3, 09:30", sender=ALEX,
         subject="Want a second opinion on that?", preview="Tell me your course and how you play and I'll tell you if it's the right one.", slots=[]),
    dict(key="e3e", fn=e3e, name="E3 Everything else · Last nudge", timing="Everything else, non-members · day 3, 17:30", sender=BR,
         subject="Still in your basket", preview="Your basket's saved. And if you join, 10% comes off it.", slots=[]),
]


def build():
    OUT.mkdir(exist_ok=True)
    live = {"logo": b.LIVE["logo"], "roundel": b.LIVE["roundel"], **PHOTOS}
    for e in EMAILS:
        (OUT / f"{e['key']}.html").write_text(e["fn"](Ctx(live, "now", True, {}, live=True)))
        (OUT / f"{e['key']}.preview.html").write_text(e["fn"](Ctx(live, "now", True, {}, live=False)))
    print("f3:", len(EMAILS), "emails")


if __name__ == "__main__":
    build()

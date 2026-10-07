"""F3 Checkout abandonment, in the editorial design.

Structure (Layton, 7 Oct 2026): three paths from Email 1, each email 1 hour / next day 09:30 / day 2 18:00 (text) / day 3.
  Annual members: E1m "your 10% can go on this order" (members' edition), E2m quick checks + reminder, text. No E3.
  Non-members, basket £300+: E1 "join now and 10% comes off this basket" (shows their basket total; never claims the fee pays
    for itself), E2 quick checks + membership, text, E3 from Alex.
  Non-members, under £300: the Free membership (5% off everything on the site) is the offer; E1, E2, text, E3 last nudge.
    Free members on these paths see "your 5% can go on this" / "upgrade to 10%" instead of "join free".
Trolley checks, club advice and the 'right choice?' row show only when the basket has that kind of
item (Klaviyo tags on the event's Collections). No discount codes (member and Free-member savings come from membership). Writes klaviyo/design/f3/<key>.html (live, Klaviyo tags) and <key>.preview.html
(an example basket, for the dashboard).

Run: python3 klaviyo/design/build_f3.py
"""
import pathlib

import build_f3_b as b
import build_f1 as f1
import build_f2 as f2
from build_f1 import (G, CREAM, INK, HEAD, MUTED, LINE, WHITE, SANS, SERIF, confirm, unsub, intro, p, text_row, link, button,
                      member_note, panel, feature, benefits_table, BENEFITS, FINE, URL, PHOTOS)

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


def has_none(names):
    """Klaviyo (like Django) allows no brackets in conditions, so "none of these" is spelled out."""
    return " and ".join(f'"{n}" not in event.Collections' for n in names)


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


# ---------------- shared pieces ----------------
def value(ctx):
    """The basket total as Klaviyo has it (the example basket in previews)."""
    return "£{{ event|lookup:'$value'|floatformat:2 }}" if ctx.live else "£799.00"


def is_free(ctx, yes, no):
    """Free members see `yes`, everyone else `no` (previews show `no`, then `yes` with a note)."""
    if ctx.live:
        return "{% if person|lookup:'MemberTier' == 'Free' %}" + yes + "{% else %}" + no + "{% endif %}"
    note = (f'<tr><td class="px" bgcolor="{WHITE}" style="padding:20px 48px 0;"><span style="display:inline-block;border:1px dashed {MUTED};'
            f'padding:1px 6px;font:600 10px/16px {SANS};letter-spacing:.06em;color:{MUTED};">FREE MEMBERS SEE THIS INSTEAD</span></td></tr>')
    return no + note + yes



PHONE = f'<a href="tel:03301227089" style="color:{G};">0330 122 7089</a>'


def basket_facts(ctx, member=False):
    """'Good to know' rows (Layton's edits, 7 Oct 2026): no warranty or YouTube rows; returns, choice help and price match."""
    rows = [("Delivery", "Free delivery over £10, as a member." if member else "Free UK delivery on orders over £50.", None),
            ("Returns", "Free, four a year, as a member. Start one from your portal." if member
             else "Members get four free returns a year, so you can change your mind.", None),
            ("Paying for it", "Pay in 3 interest-free instalments with Klarna at checkout.", None),
            ("Right choice?", "Feel free to give us a ring or drop us a message. Our expert team will steer you in the right direction.<br>"
                              + link("Get in touch", URL["contact"]), has(HARDWARE)),
            ("Price?", "Seen it cheaper somewhere else? Reply to this email or give us a ring and we'll see if we can match it.", None)]
    return facts(ctx, "Good to know before you check out", rows)


CHECKS = [("Range.", "Does the battery cover your usual round with margin? 18-hole lithium suits most; go 36 if you play twice on a Saturday."),
          ("Boot.", "Fold it in your head: will it go in with your bag?"),
          ("Hills.", "If your course has them, downhill control matters more than any gadget.")]


def checks(ctx):
    """Trolley checks / club fitting, each only when the basket has that kind of item; a reply line otherwise."""
    trolley = (text_row(f'<h3 style="margin:0;font:400 24px/30px {SERIF};color:{HEAD};">Buying a trolley?</h3>', "28px 48px 0")
               + f2.steps(CHECKS)
               + text_row(p(f"Not sure on any of these? Reply to this email or call us on {PHONE} and we'll help you pick the right one.",
                            15, margin="0 0 8px") + link("Get in touch", URL["contact"]), "16px 48px 0"))
    clubs = text_row(f'<h3 style="margin:0 0 8px;font:400 24px/30px {SERIF};color:{HEAD};">Buying clubs?</h3>'
                     + p(f"Shaft, length, lie and grip all make a difference. Reply to this email or call us on {PHONE} and our team will "
                         "help you get the right spec. Near Ringwood? A fitting on our launch monitor sorts it out before you commit.", margin="0 0 8px")
                     + link("Talk to our team", URL["contact"]), "28px 48px 0")
    neither = text_row(p("Not sure it's the right one? Reply to this email and tell us how you play. A real golfer will answer.", margin="0"), "20px 48px 0")
    return (ctx.when(has(TROLLEYS), trolley, "the basket has a trolley")
            + ctx.when(has(CLUBS), clubs, "the basket has new clubs")
            + (("{% if " + has_none(TROLLEYS + CLUBS) + " %}" + neither + "{% endif %}") if ctx.live else ""))


FREE_ROWS = [("5% off everything", "On anything across the site, this order included."),
             ("Free delivery over £30", "Instead of £50."),
             ("Loyalty points", "On everything you buy."),
             ("Your own member portal", "With member deals you won't see anywhere else.")]


def join_annual(ctx, heading, pad="36px 48px 0"):
    """£300+ non-members: 10% off this basket, shown next to their basket total. Free members are offered the upgrade."""
    lede = (f"10% comes off your {value(ctx)} basket the moment you join, then 10% off one order every month after."
            + (("{% if person|lookup:'MemberTier' == 'Free' %} As a Free member you get 5% today; this doubles it.{% endif %}") if ctx.live else ""))
    return feature("Evolution Golf Membership · £36 a year", heading, lede, BENEFITS, "Become a member, £36 a year", URL["join"], FINE,
                   pad=pad, card=True)


def join_free(ctx, pad="36px 48px 0"):
    """Under £300: the Free membership's 5% on this order; Free members are told their 5% applies, with the upgrade to 10%."""
    free = feature("Free membership · £0", "Join free and 5% comes off this order.",
                   "Free members get 5% off everything on the site. It takes a minute, and it works on this basket.",
                   FREE_ROWS, "Join free", URL["join"],
                   "Want more? The £36 annual plan gives you 10% off one order every month, free returns and a monthly prize draw.", pad=pad)
    member = member_note(ctx, "Your 5% can go on this", "As a Free member you get 5% off everything. Or upgrade to 10% off one order every month for £36 a year.",
                         "See the annual plan")
    return is_free(ctx, member, free)


# ---------------- Annual members ----------------
def e1m(ctx):
    body = (f2.intro("Your basket", f"Your 10% can go on this order{name_suffix(ctx)}",
                     "If you haven't used this month's 10% yet, it can go on this basket. Your code is in the Codes section of your member portal.",
                     card=True)
            + basket(ctx) + text_row(button("Back to my basket", BASKET), "28px 48px 0")
            + text_row(p("Need your code? " + link("Open my member portal", f2.PORTAL), 15, margin="0"), "20px 48px 0")
            + basket_facts(ctx, member=True) + text_row("", "0 0 40px") + footer(ctx))
    return f1.shell(ctx, body, "If you haven't used this month's 10% yet, it can go on this basket.", members=True)


def e2m(ctx):
    body = (f2.intro("Before you buy", "A few quick checks", "", card=True) + checks(ctx)
            + member_note(ctx, "Your 10% can go on this", "If you haven't used this month's 10% yet. The code is in your member portal.",
                          "Open my portal", f2.PORTAL)
            + basket(ctx, big=False) + text_row(button("Back to my basket", BASKET), "28px 48px 0")
            + text_row("", "0 0 40px") + footer(ctx))
    return f1.shell(ctx, body, "A few quick checks before you buy. Your 10% can still go on it.", members=True)


# ---------------- Non-members, £300+ ----------------
def e1hi(ctx):
    body = (intro("Your basket is saved", "A good basket to join on", "Your basket is exactly where you left it.")
            + basket(ctx) + text_row(link("Back to my basket", BASKET), "16px 48px 0")
            + join_annual(ctx, "Join before you check out and 10% comes off this order.")
            + basket_facts(ctx) + close(ctx))
    return f1.shell(ctx, body, "Join before you check out and 10% comes off this basket. Then 10% off one order every month.")


def e2hi(ctx):
    body = (intro("Before you buy", "A few quick checks") + checks(ctx)
            + join_annual(ctx, "Still to check out? Members get 10% off this order.")
            + basket(ctx, big=False) + text_row(link("Back to my basket", BASKET), "16px 48px 0") + close(ctx))
    return f1.shell(ctx, body, "A few quick checks before you buy. Then 10% off this order with membership.")


# ---------------- Non-members, under £300 ----------------
def e1lo(ctx):
    body = (intro("Your basket is saved", "Still want these? They're right where you left them.")
            + basket(ctx) + text_row(link("Back to my basket", BASKET), "16px 48px 0")
            + join_free(ctx) + basket_facts(ctx) + close(ctx))
    return f1.shell(ctx, body, "5% off this order with Free membership. Your basket's saved.")


def e2lo(ctx):
    body = (intro("Before you check out", "5% off this order, free")
            + text_row(p("Free membership takes a minute and gives you 5% off everything on the site, including what's in your basket.", margin="0"), "0 48px 0")
            + basket(ctx, big=False) + text_row(link("Back to my basket", BASKET), "16px 48px 0")
            + join_free(ctx, pad="28px 48px 0") + checks(ctx) + close(ctx))
    return f1.shell(ctx, body, "Free membership takes a minute and takes 5% off this order.")


# ---------------- Email 3 ----------------
def e3h(ctx):
    """From Alex (£300+ non-members): a plain letter, no header, no buttons."""
    pp = f'margin:0 0 16px;font:16px/26px {SANS};color:{INK};'
    hi = "{{ person.first_name|default:'there' }}" if ctx.live else "Sam"
    photo = (f'<td width="92" style="padding-right:16px;vertical-align:top;"><img src="{PHOTOS["A1"]}" width="76" height="76" alt="Alex" '
             f'style="width:76px;height:76px;border-radius:50%;display:block;"></td>')
    sig = (f'<table role="presentation" cellpadding="0" cellspacing="0"><tr>{photo}<td style="vertical-align:top;font:16px/24px {SANS};color:{INK};">'
           f'Alex<br><span style="color:{MUTED};">Head of Ecommerce, Evolution Golf</span></td></tr></table>')
    body = (f'<tr><td class="px" bgcolor="{WHITE}" style="padding:44px 48px 28px;">'
            f'<p style="{pp}">Hi {hi},</p>'
            f'<p style="{pp}">Alex from Evolution Golf. I can see you were looking at the {product_name(ctx)}.</p>'
            f'<p style="{pp}">If you\'re not sure it\'s the right choice for you, feel free to reply to this and I\'ll give you a straight answer. '
            f'If something cheaper would do the job, I\'ll say so.</p>'
            f'<p style="{pp}">If you\'ve already bought elsewhere, no problem at all. Ignore this one.</p>'
            f'{sig}<p style="margin:22px 0 0;font:15px/22px {SANS};"><a href="{BASKET if ctx.live else "#"}" style="color:{G};">My basket</a></p></td></tr>'
            f'<tr><td class="px foot-light" bgcolor="{WHITE}" style="padding:18px 48px 24px;border-top:1px solid {LINE};font:12px/18px {SANS};color:{MUTED};">'
            f'Evolution Golf, Unit 3, Parvenah Park, Embankment Way, Ringwood, BH24 1WL<br>' + unsub(ctx, MUTED) + '</td></tr>')
    return f1.shell(ctx, body, "Tell me your course and how you play and I'll tell you if it's the right one.", header=False)


def e3lo(ctx):
    body = (intro("Still in your basket", "Your basket's still here", "We'll stop reminding you after this one.")
            + basket(ctx, big=False) + text_row(button("Back to my basket", BASKET), "28px 48px 0")
            + is_free(ctx, member_note(ctx, "Your 5% can go on this", "As a Free member you get 5% off everything on the site.", "Open my portal", f2.PORTAL),
                      member_note(ctx, "Join free first", "Free members get 5% off everything (this basket included), free delivery over £30, "
                                  "loyalty points on everything they buy, and member deals in the portal you won't see anywhere else.", "Join free"))
            + close(ctx))
    return f1.shell(ctx, body, "Your basket's saved, and 5% can come off it with Free membership.")


SMS1 = ("Evolution Golf: your basket's still saved{% if person.first_name %}, {{ person.first_name }}{% endif %}. "
        "Pay in 3 interest-free with Klarna. Finish here: {{ event.extra.checkout_url }}")

BR, ALEX = "⛳ Evolution Golf", "Alex at Evolution Golf"
SAVED = "Your basket's saved{% if person.first_name %}, {{ person.first_name }}{% endif %}"
EMAILS = [
    dict(key="e1m", fn=e1m, name="E1 Members · Your 10% can go on this", timing="Annual members · 1 hour after checkout", sender=BR,
         subject="Your 10% can go on this order", preview="If you haven't used this month's 10% yet, it can go on this basket.", slots=[]),
    dict(key="e2m", fn=e2m, name="E2 Members · Quick checks", timing="Annual members · next day 09:30", sender=BR,
         subject="A few quick checks before you buy", preview="A few quick checks before you buy. Your 10% can still go on it.", slots=[]),
    dict(key="e1hi", fn=e1hi, name="E1 £300+ · Join and save 10%", timing="Non-members, basket £300+ · 1 hour after checkout", sender=BR,
         subject=SAVED, preview="Join before you check out and 10% comes off this basket. Then 10% off one order every month.", slots=[]),
    dict(key="e2hi", fn=e2hi, name="E2 £300+ · Quick checks", timing="Non-members, basket £300+ · next day 09:30", sender=BR,
         subject="How to be sure it's the right one", preview="A few quick checks before you buy. Then 10% off this order with membership.", slots=[]),
    dict(key="e3h", fn=e3h, name="E3 £300+ · From Alex", timing="Non-members, basket £300+ · day 3, 09:30", sender=ALEX,
         subject="Want a second opinion on that?", preview="Tell me your course and how you play and I'll tell you if it's the right one.", slots=[]),
    dict(key="e1lo", fn=e1lo, name="E1 Under £300 · Join free, 5% off", timing="Non-members, under £300 · 1 hour after checkout", sender=BR,
         subject=SAVED, preview="5% off this order with Free membership. Your basket's saved.", slots=[]),
    dict(key="e2lo", fn=e2lo, name="E2 Under £300 · 5% off, free", timing="Non-members, under £300 · next day 09:30", sender=BR,
         subject="5% off this order, free", preview="Free membership takes a minute and takes 5% off this order.", slots=[]),
    dict(key="e3lo", fn=e3lo, name="E3 Under £300 · Last nudge", timing="Non-members, under £300 · day 3, 17:30", sender=BR,
         subject="Still in your basket", preview="Your basket's saved, and 5% can come off it with Free membership.", slots=[]),
]


def build():
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.html"):
        f.unlink()
    live = {"logo": b.LIVE["logo"], "roundel": b.LIVE["roundel"], **PHOTOS}
    for e in EMAILS:
        (OUT / f"{e['key']}.html").write_text(e["fn"](Ctx(live, "now", True, {}, live=True)))
        (OUT / f"{e['key']}.preview.html").write_text(e["fn"](Ctx(live, "now", True, {}, live=False)))
    print("f3:", len(EMAILS), "emails")


if __name__ == "__main__":
    build()

"""F9 After delivery + review, in the editorial design (copy doc: https://claude.ai/code/artifact/4bcfe548-99e6-4e11-a9ed-4164ef346c64).

Starts from Fulfilled Order (online only; till sales are left out), 3 days after dispatch, since "delivered" fires for about half
of orders. Two groups: Hardware (trolley, club or used club) and Everything else, with per-item sections switched on by the
order's Collections. Non-members get the membership credit offer (join the annual plan within 14 days of the order and the team
credits 10% of it as store credit) only while the order is recent enough; Free members get an upgrade note, annual members a thanks.
No codes. The review ask goes to everyone (no review gating).

Run: python3 klaviyo/design/build_f9.py
"""
import pathlib

import build_f3_b as b
import build_f1 as f1
import build_f2 as f2
import build_f3 as f3
from build_f1 import (G, INK, HEAD, MUTED, LINE, WHITE, SANS, SERIF, unsub, intro, p, text_row, link, button, member_note,
                      feature, BENEFITS, URL, PHOTOS)
from build_f3 import Ctx, has, TROLLEYS, CLUBS, HARDWARE, PHONE

OUT = pathlib.Path(__file__).parent / "f9"
REASON = "you placed an order with Evolution Golf"
SITE = "https://evolutiongolf.co.uk"
COL = lambda h: f"{SITE}/collections/{h}"
TRUSTPILOT = "https://uk.trustpilot.com/review/evolutiongolf.co.uk"
MOTOCADDY_REG = "https://www.motocaddy.com/warranty"          # printed on Motocaddy manuals: "register online"
POWAKADDY_REG = "https://www.powakaddy.com/my-powakaddy"      # PowaKaddy UK & Ireland warranty leaflet
VENDOR = "event.extra.line_items.0.vendor"
SAMPLE_PRODUCT = "Motocaddy 2026 M1 DHC Standard Lithium Electric Golf Trolley"


def footer(ctx):
    return f1.footer(ctx, REASON)


def name(ctx):
    return "{% if person.first_name %}, {{ person.first_name }}{% endif %}" if ctx.live else ", Sam"


def product(ctx):
    return "{{ event.extra.line_items.0.title }}" if ctx.live else SAMPLE_PRODUCT


def order_total(ctx):
    return "£{{ event|lookup:'$value'|floatformat:2 }}" if ctx.live else "£799.00"


def tier(ctx, annual, free, none):
    """Annual members see `annual`, Free members `free`, everyone else `none` (previews show all three, labelled)."""
    if ctx.live:
        return ("{% if person|lookup:'MemberTier' == 'AnnualMember' %}" + annual
                + "{% elif person|lookup:'MemberTier' == 'Free' %}" + free + "{% else %}" + none + "{% endif %}")
    lab = lambda t: (f'<tr><td class="px" bgcolor="{WHITE}" style="padding:20px 48px 0;"><span style="display:inline-block;border:1px dashed {MUTED};'
                     f'padding:1px 6px;font:600 10px/16px {SANS};letter-spacing:.06em;color:{MUTED};">{t}</span></td></tr>')
    return lab("NOT A MEMBER") + none + lab("FREE MEMBERS SEE THIS INSTEAD") + free + lab("ANNUAL MEMBERS SEE THIS INSTEAD") + annual


def by_vendor(ctx, moto, powa, other):
    if ctx.live:
        return ("{% if " + VENDOR + " == 'Motocaddy' %}" + moto + "{% elif " + VENDOR + " == 'PowaKaddy' %}" + powa
                + "{% else %}" + other + "{% endif %}")
    return moto


FINE = ("Store credit equal to 10% of this order's total. Join within 14 days of ordering. Our team adds the credit to your account "
        "after you join. Renews at £36 a year; cancel any time from your account.")


def membership(ctx, offer):
    """Email 1's membership section, by who they are. offer=False: the same without the credit (order too old)."""
    if offer:
        none = feature("Evolution Golf Membership · £36 a year", "Join now and get 10% of this order back.",
                       f"Join the annual plan within 14 days of your order and we'll credit your account with the 10% you'd have saved on your "
                       f"{order_total(ctx)} order, as store credit. Then it's 10% off one order every month, free returns and a monthly prize draw.",
                       None, "Become a member, £36 a year", URL["join"], FINE, card=True)
        none += text_row(p("<strong style=\"font-weight:600;color:" + HEAD + ";\">Or start free:</strong> Free members get 5% off everything on the site, "
                           "from your next order. " + link("Join free", URL["join"]), 15, margin="0"), "20px 48px 0")
    else:
        none = member_note(ctx, "Next time, pay less", "Free members get 5% off everything. Or join for £36 a year for 10% off one order "
                           "every month, free returns and a monthly prize draw.", "See membership")
    free = member_note(ctx, "Want more than 5%?", "Upgrade for £36 a year and get 10% off one order every month, plus free returns and a "
                       "monthly prize draw.", "See the annual plan")
    annual = member_note(ctx, "Thanks for being a member", "Your next 10% is waiting for next month, and you're in this month's prize draw.",
                         "Open my portal", f2.PORTAL)
    return tier(ctx, annual, free, none)


def product_photo(ctx):
    """P9: their own product's main Shopify photo, under the headline (skipped if the product has no photo)."""
    src = "{{ event.extra.line_items.0.product.images.0.src }}" if ctx.live else "https://cdn.shopify.com/s/files/1/0499/9014/0061/files/2026M1DHCThumbnail.png"
    img = (f'<tr><td class="px" align="center" bgcolor="{WHITE}" style="padding:28px 48px 0;text-align:center;">'
           f'<img src="{src}" width="240" height="240" alt="{product(ctx)}" style="width:240px;height:240px;display:block;margin:0 auto;"></td></tr>')
    return ("{% if event.extra.line_items.0.product.images.0.src %}" + img + "{% endif %}") if ctx.live else img


def moto_only(ctx, html):
    """C1 and X1 show Motocaddy kit, so they only go to Motocaddy orders."""
    return ("{% if " + VENDOR + " == 'Motocaddy' %}" + html + "{% endif %}") if (ctx.live and html) else html


def hero(ctx, key, h=360):
    """A photo spot (C1, C2, X1): the photo once supplied, a labelled placeholder in the photo-spots view, nothing otherwise."""
    s = ctx.slot(key, 600, h)
    return f'<tr><td bgcolor="{WHITE}" style="padding:24px 0 0;">{s}</td></tr>' if s else ""


def first_order(ctx):
    """'How we work', as a plain line for everyone (a template can't see someone's order count; and one panel per email)."""
    return text_row(p(f"<strong style=\"font-weight:600;color:{HEAD};\">How we work:</strong> we're real people who play, free UK delivery is "
                      f"over £50, and if anything's wrong, you reply to an email or call us and a person sorts it.", 15, MUTED, "0"), "24px 48px 0")


def h3(t, m="0 0 8px"):
    return f'<h3 style="margin:{m};font:400 24px/30px {SERIF};color:{HEAD};">{t}</h3>'


def numbered(items):
    return f2.steps(items)


# ---------------- Hardware ----------------
def e1h(ctx, offer=True):
    reg = by_vendor(ctx,
                    "Your trolley and charger have a 2-year warranty. Register your lithium battery with Motocaddy within 45 days of buying it "
                    "and its warranty goes up to 5 years. " + link("Register with Motocaddy", MOTOCADDY_REG),
                    "Register your trolley and battery with PowaKaddy within 30 days of buying them. Unregistered batteries get 2 years; "
                    "registered ones go onto PowaKaddy's 5-year battery warranty scheme. " + link("Register with PowaKaddy", POWAKADDY_REG),
                    "Check your manual for how to register with the maker.")
    trolley = (text_row(h3("New trolley?", "0"), "28px 48px 0")
               + numbered([("Charge it after every round.", "Get into the habit of charging the battery after each round, ideally the same day, "
                            "however many holes you played."),
                           ("Pair and set up.", "If your model has a remote, app or GPS, the manual walks you through it. Stuck? Ring us and "
                            "we'll talk you through it."),
                           ("Register the warranty.", reg)]))
    clubs = text_row(h3("New clubs?") + p("Give them three or four rounds before judging them. If something doesn't feel right (length, lie, "
                     "grip size), get in touch and our team will help you sort it.", margin="0"), "28px 48px 0")
    body = (intro("Your order", f"It should be with you by now{name(ctx)}",
                  "A few things that make the first round go better. If anything's unclear, our team is a phone call away.")
            + product_photo(ctx)
            + ctx.when(has(TROLLEYS), trolley, "the order has a trolley")
            + ctx.when(has(CLUBS + f3.USED), clubs, "the order has clubs")
            + text_row(p(f"Questions? Call us on {PHONE} or " + link("get in touch", URL["contact"]) + ".", 15, margin="0"), "24px 48px 0")
            + membership(ctx, offer) + first_order(ctx) + text_row("", "0 0 8px") + f3.close(ctx).replace(f3.REASON, REASON))
    return f1.shell(ctx, body, "Getting set up, and who to call if anything's not right.")


CARE_TROLLEY = ["Charge the battery after every round, ideally within 12 hours, even after nine holes.",
                "Once it's fully charged, unplug it. Don't leave it on the charger overnight.",
                "Charge it on a dry, hard surface (not carpet), somewhere between 10 and 30°C.",
                "Putting it away for the winter? Store it fully charged, indoors at room temperature, unplugged from the trolley. Top it up "
                "before your first round back, and don't leave it more than two months without a charge.",
                "If the battery ever swells, gets hot or won't charge, stop using it and get in touch."]
CARE_CLUBS = ["Wipe the faces and clean the grooves after each round. Clean grooves hold the ball better.",
              "Keep headcovers on the woods and putter in the bag.",
              "Grips wear with use. Most golfers notice a difference when they're replaced every year or so.",
              "Don't leave them in a hot car boot for long spells."]


def bullets(items):
    lis = "".join(f'<tr><td width="18" valign="top" style="width:18px;padding:6px 0;font:15px/24px {SANS};color:{G};">&#8226;</td>'
                  f'<td valign="top" style="padding:6px 0;font:15px/24px {SANS};color:{INK};">{t}</td></tr>' for t in items)
    return f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{lis}</table>'


def e2h(ctx):
    acc_trolley = by_vendor(ctx,
                            p("Accessories made for your trolley: bag supports, umbrella holders, cup holders and more.", 15, margin="0 0 8px")
                            + link("Motocaddy trolley accessories", COL("motocaddy-golf-trolley-accessories")),
                            p("Accessories made for your trolley.", 15, margin="0 0 8px") + link("PowaKaddy trolley accessories", COL("powakaddy-golf-trolley-accessories")),
                            link("Trolley accessories", COL("golf-trolley-accessories")))
    acc_clubs = (p("New grips, headcovers to protect them, and a box of balls to try them with.", 15, margin="0 0 8px")
                 + link("Grips", COL("golf-grips")) + " &nbsp;·&nbsp; " + link("Headcovers", COL("headcovers")) + " &nbsp;·&nbsp; "
                 + link("Golf balls", COL("golf-balls")))
    body = (intro("Looking after it", "Keep it going for years")
            + ctx.when(has(TROLLEYS), moto_only(ctx, hero(ctx, "C1")) + text_row(h3("Your trolley") + bullets(CARE_TROLLEY), "20px 48px 0"), "the order has a trolley")
            + ctx.when(has(CLUBS + f3.USED), hero(ctx, "C2") + text_row(h3("Your clubs") + bullets(CARE_CLUBS), "28px 48px 0"), "the order has clubs")
            + ctx.when(has(TROLLEYS), moto_only(ctx, hero(ctx, "X1", 300)), "the order has a Motocaddy trolley")
            + ctx.when(has(CLUBS + f3.USED), hero(ctx, "X2", 300), "the order has clubs")
            + text_row(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td style="border-top:3px solid {G};padding:28px 0 0;">'
                       + b.eyebrow("Goes well with it") + h3("A few things that go with it", "0 0 16px")
                       + (("{% if " + has(TROLLEYS) + " %}") if ctx.live else "") + acc_trolley + (("{% endif %}") if ctx.live else "")
                       + (("{% if " + has(CLUBS + f3.USED) + " %}") if ctx.live else '<div style="height:16px;"></div>') + acc_clubs
                       + (("{% endif %}") if ctx.live else "") + '</td></tr></table>', "36px 48px 0")
            + text_row(button("Get in touch with our team", URL["contact"]), "32px 48px 0")
            + text_row("", "0 0 8px") + f3.close(ctx).replace(f3.REASON, REASON))
    return f1.shell(ctx, body, "A few minutes now keeps it going for years.")


# ---------------- Everything else ----------------
CARE_SHOES = ["Wear them round the house or for nine holes before a long round.",
              "Waterproof shoes stay that way longer with a clean and a waterproofing spray every so often.",
              "Let wet shoes dry naturally, away from radiators.",
              "Spiked shoes: check the spikes every few months and replace worn ones."]
SHOES = ["Golf Shoes", "Mens Golf Shoes", "Ladies Golf Shoes", "Womens Golf Shoes", "Junior Golf Shoes", "Mens Spiked Golf Shoes",
         "Mens Spikeless Golf Shoes", "Mens Waterproof Golf Shoes"]


def e1e(ctx, offer=True):
    body = (intro("Your order", "Thanks for shopping with us",
                  f"Your order should be with you by now. We're a golf shop run by people who play, so if anything's not right, or you've a "
                  f"question about what you bought, reply to this email or call us on {PHONE}.")
            + product_photo(ctx)
            + ctx.when(has(SHOES), text_row(h3("New shoes?") + bullets(CARE_SHOES), "12px 48px 0"), "the order has golf shoes")
            + membership(ctx, offer) + first_order(ctx) + text_row("", "0 0 8px") + f3.close(ctx).replace(f3.REASON, REASON))
    return f1.shell(ctx, body, "Thanks for shopping with us. Here's how to reach us if you need anything.")


# ---------------- Reminder (non-members, both paths) ----------------
def rem(ctx):
    body = (intro("Membership", "Still time to get 10% back on your order",
                  "Join the annual plan within 14 days of your order and we'll credit your account with the 10% you'd have saved on it, as "
                  "store credit. After that, the offer ends.")
            + feature("Evolution Golf Membership · £36 a year", "10% back on your order, then 10% off one order every month.",
                      "Here's everything that comes with it.", BENEFITS, "Become a member, £36 a year", URL["join"],
                      "Store credit equal to 10% of your order total, for orders placed in the 14 days before you join. Our team adds the credit "
                      "to your account after you join. Renews at £36 a year; cancel any time from your account.", pad="12px 48px 0", card=True)
            + text_row(p("<strong style=\"font-weight:600;color:" + HEAD + ";\">Or start free:</strong> Free members get 5% off everything on the site. "
                         + link("Join free", URL["join"]), 15, margin="0"), "24px 48px 0")
            + text_row("", "0 0 8px") + f3.close(ctx).replace(f3.REASON, REASON))
    return f1.shell(ctx, body, "Join the annual plan within 14 days of your order and we'll credit the 10% you'd have saved.")


# ---------------- Reviews, from Alex ----------------
def letter(ctx, paras, preheader):
    pp = f'margin:0 0 16px;font:16px/26px {SANS};color:{INK};'
    hi = "{{ person.first_name|default:'there' }}" if ctx.live else "Sam"
    sig = (f'<table role="presentation" cellpadding="0" cellspacing="0"><tr><td width="92" style="padding-right:16px;vertical-align:top;">'
           f'<img src="{PHOTOS["A1"]}" width="76" height="76" alt="Alex" style="width:76px;height:76px;border-radius:50%;display:block;"></td>'
           f'<td style="vertical-align:top;font:16px/24px {SANS};color:{INK};">Alex<br><span style="color:{MUTED};">Head of Ecommerce, Evolution Golf</span></td></tr></table>')
    body = (f'<tr><td class="px" bgcolor="{WHITE}" style="padding:44px 48px 28px;"><p style="{pp}">Hi {hi},</p>'
            + "".join(f'<p style="{pp}">{x}</p>' for x in paras)
            + f'<div style="margin:8px 0 28px;">{button("Leave a review", TRUSTPILOT)}</div>{sig}</td></tr>'
            f'<tr><td class="px foot-light" bgcolor="{WHITE}" style="padding:18px 48px 24px;border-top:1px solid {LINE};font:12px/18px {SANS};color:{MUTED};">'
            f'Evolution Golf, Unit 3, Parvenah Park, Embankment Way, Ringwood, BH24 1WL<br>' + unsub(ctx, MUTED) + '</td></tr>')
    return f1.shell(ctx, body, preheader, header=False)


def rvh(ctx):
    return letter(ctx, [f"Alex here. You've had the {product(ctx)} for a little while now, so hopefully you've had a round or two with it.",
                        "Would you leave a short, honest review on Trustpilot? Good or bad, it helps the next golfer who's choosing, and we read every one.",
                        "And if anything isn't right, just reply to this email. I'll sort it, whatever you write in your review.",
                        "Thanks for buying from a shop run by golfers."],
                  "A quick, honest review would help the next golfer choosing.")


def rve(ctx):
    return letter(ctx, ["Alex here. Your order should have been with you for a week or so now.",
                        "If you've a minute, would you leave a short, honest review on Trustpilot? A sentence is plenty, and it helps other golfers "
                        "decide where to shop.",
                        "If anything wasn't right, reply to this email and I'll sort it."],
                  "A sentence on Trustpilot is plenty.")


BR, ALEX = "⛳ Evolution Golf", "Alex at Evolution Golf"
EMAILS = [
    dict(key="e1h", fn=lambda c: e1h(c, True), name="E1 Hardware · Getting set up (with credit offer)", timing="Hardware · 3 days after dispatch, 09:30",
         sender=BR, subject="Your new kit should be with you. A few things first", preview="Getting set up, and who to call if anything's not right.", slots=["P9"]),
    dict(key="e1hn", fn=lambda c: e1h(c, False), name="E1 Hardware · Getting set up", timing="Hardware, members or older orders · 3 days after dispatch, 09:30",
         sender=BR, subject="Your new kit should be with you. A few things first", preview="Getting set up, and who to call if anything's not right.", slots=["P9"]),
    dict(key="e2h", fn=e2h, name="E2 Hardware · Looking after it", timing="Hardware · 4 days after Email 1, 17:30", sender=BR,
         subject="Looking after your new kit", preview="A few minutes now keeps it going for years.", slots=["C1", "C2", "X1", "X2"]),
    dict(key="e1e", fn=lambda c: e1e(c, True), name="E1 Everything else · Thanks (with credit offer)", timing="Everything else · 3 days after dispatch, 09:30",
         sender=BR, subject="Your order should be with you{% if person.first_name %}, {{ person.first_name }}{% endif %}",
         preview="Thanks for shopping with us. Here's how to reach us if you need anything.", slots=["P9"]),
    dict(key="e1en", fn=lambda c: e1e(c, False), name="E1 Everything else · Thanks", timing="Everything else, members or older orders · 3 days after dispatch, 09:30",
         sender=BR, subject="Your order should be with you{% if person.first_name %}, {{ person.first_name }}{% endif %}",
         preview="Thanks for shopping with us. Here's how to reach us if you need anything.", slots=["P9"]),
    dict(key="rem", fn=rem, name="Membership reminder · 10% back", timing="Non-members, order still inside 14 days · 10 days after dispatch, 09:30",
         sender=BR, subject="Your 10% back offer ends soon",
         preview="Join the annual plan within 14 days of your order and we'll credit the 10% you'd have saved.", slots=[]),
    dict(key="rvh", fn=rvh, name="Review · Hardware (from Alex)", timing="Trolleys about 2 weeks, clubs about 4 weeks after delivery, 09:30", sender=ALEX,
         subject="How's it going with the new kit?", preview="A quick, honest review would help the next golfer choosing.", slots=[]),
    dict(key="rve", fn=rve, name="Review · Everything else (from Alex)", timing="About 10 days after delivery, 09:30", sender=ALEX,
         subject="Quick one: how did we do?", preview="A sentence on Trustpilot is plenty.", slots=[]),
]


def build():
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.html"):
        f.unlink()
    live = {"logo": b.LIVE["logo"], "roundel": b.LIVE["roundel"], **PHOTOS}
    for e in EMAILS:
        (OUT / f"{e['key']}.html").write_text(e["fn"](Ctx(live, "now", True, {}, live=True)))
        (OUT / f"{e['key']}.preview.html").write_text(e["fn"](Ctx(live, "now", True, {}, live=False)))
    print("f9:", len(EMAILS), "emails")


if __name__ == "__main__":
    build()

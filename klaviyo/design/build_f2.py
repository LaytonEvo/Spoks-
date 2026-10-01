"""F2 Membership welcome, built in design B with the Astra icon library.

Deviation from the pack (records the site as of 1 Oct 2026): the pack's four tiers (Free / Club Access / Pro / Annual) are now
two plans on evolutiongolf.co.uk/pages/members-page: Free (£0) and the Annual Membership (£36 a year). So two branches:
  Free   - FE1 portal live (day 0), FE2 the honest maths (day 4), FE3 the plan in use (day 12). Before FE2/FE3: if no longer
           Free, they get PE1 instead and stop.
  Annual - PE1 welcome (day 0, smart sending off), PE2 free returns (day 3), PE3 first month (day 30),
           PE4 trade-in bonus on (day 60), PE5 renewal reminder (day 335).
Every fact below is from the members page; nothing else is assumed.

Run: python3 klaviyo/design/build_f2.py <scratch img dir>
"""
import json, pathlib, re, sys

import build_f3_b as b
import build_f1 as f1
from build_f1 import (name_suffix, G, DG, GOLD, CREAM, INK, MUTED, LINE, WHITE, SANS, SERIF, confirm, data_uri, icon, first_name, intro, p,
                      text_row, link, button, member_note, icon_rows, way_card, Ctx, local_icons, HOSTED, OUT)

PORTAL = "https://members.evolutiongolf.co.uk"
JOIN = f1.URL["join"]
RETURNS = "https://evolutiongolf.co.uk/pages/returns"
TRADE_IN = f1.URL["trade_in"]
REASON = "you joined Evolution Golf membership"


def footer(ctx):
    return f1.footer(ctx, REASON)


def shell(ctx, body, pre):
    return f1.shell(ctx, body, pre)


def portal_button(label="Open my member portal"):
    return text_row(button(label, PORTAL), "8px 44px 32px")


ANNUAL = [("member-price-tag", "10% off your first order, then 10% off one order every month"),
          ("free-delivery-members", "Free delivery on orders over £10"),
          ("free-returns", "Free returns, 4 a year"),
          ("monthly-prize-draw", "A monthly prize draw entry"),
          ("calendar", "48 hours' early access to new products"),
          ("trade-in", "+5% trade-in value after 60 days")]


def benefit_list(ctx, items):
    rows = "".join(f'<tr><td width="40" valign="middle" style="width:40px;padding:7px 0;">{icon(ctx, n, 24)}</td>'
                   f'<td valign="middle" style="padding:7px 0;font:16px/23px {SANS};color:{INK};">{t}</td></tr>' for n, t in items)
    return text_row(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid {LINE};'
                    f'border-bottom:1px solid {LINE};margin:4px 0;"><tr><td style="padding:10px 0;"><table role="presentation" cellpadding="0" cellspacing="0">{rows}</table></td></tr></table>',
                    "16px 44px 8px")


def steps(items):
    rows = ""
    for i, (head, text) in enumerate(items, 1):
        rows += (f'<tr><td width="44" style="padding:16px 0;border-top:1px solid {LINE};vertical-align:top;font:600 30px/30px {SERIF};color:{GOLD};">{i}</td>'
                 f'<td style="padding:16px 0;border-top:1px solid {LINE};vertical-align:top;font:16px/24px {SANS};color:{INK};">'
                 f'<strong style="font-weight:600;color:{DG};">{head}</strong> {text}</td></tr>')
    return text_row(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table>', "12px 44px 12px")


def h2(text):
    return text_row(f'<p style="margin:0;font:500 22px/29px {SERIF};color:{DG};">{text}</p>', "24px 44px 0")


# ---------------- Free branch ----------------
def fe1(ctx):
    body = (intro("Free membership", f"You're in{name_suffix(ctx)}.",
                  "Your free Evolution Golf membership is live. Here's what it gives you, starting today.")
            + benefit_list(ctx, [("members-portal", "Your own member portal"), ("member-price-tag", "5% off member portal deals"),
                                 ("free-delivery-members", "Free delivery on orders over £30"), ("member-card-gold", "Loyalty points on everything you buy")])
            + h2("Two things worth doing this week")
            + steps([("Log in to your portal.", "Check your details and see this month's member deals."),
                     ("Have a look at the deals.", "Your 5% is applied to member portal deals when you're logged in.")])
            + portal_button()
            + footer(ctx))
    return shell(ctx, body, "5% off member deals, free delivery over £30 and loyalty points. All live now.")


def fe2(ctx):
    maths = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td style="background:{CREAM};border-radius:8px;padding:24px;">'
             f'<p style="margin:0 0 8px;font:600 11px/16px {SANS};letter-spacing:.14em;text-transform:uppercase;color:{GOLD};">The sum</p>'
             f'<p style="margin:0 0 10px;font:500 22px/29px {SERIF};color:{DG};">£36 a year pays for itself at £30 an order.</p>'
             f'<p style="margin:0;font:15px/23px {SANS};color:{INK};">10% off one £30 order a month is £3. Twelve months of that is £36. '
             f'Your first order gets 10% off too. Spend more than £30 an order and you\'re ahead.</p></td></tr></table>')
    body = (intro("Free or £36 a year?", "Is the annual membership worth it? Here's the honest maths.",
                  "You get 5% off member deals on Free. The £36 plan doubles that and adds a few things Free doesn't have.")
            + text_row(maths, "20px 44px 8px")
            + h2("What the £36 plan adds")
            + benefit_list(ctx, ANNUAL)
            + text_row(p("If you only buy from us once or twice a year, stay on Free. You keep your 5% either way. "
                         "If you buy most months, the plan pays for itself.", 16, margin="0"), "16px 44px 24px")
            + text_row(button("Compare the two plans", JOIN), "0 44px 32px")
            + footer(ctx))
    return shell(ctx, body, "10% off one order a month pays back the £36 at about £30 an order. The full sum inside.")


def fe3(ctx):
    rows = [("free-returns", "Free returns",
             "Order two sizes of a shoe, keep the one that fits and send the other back free. Four free returns a year.", ""),
            ("monthly-prize-draw", "A prize draw every month", "You're entered automatically every month, and we draw it at the start of the next one.", ""),
            ("trade-in", "More for your trade-in",
             "After 60 days, members get 5% more on any trade-in value. Worth having when your irons are due a change.", link("How trade-in works", TRADE_IN)),
            ("calendar", "First look at new kit", "48 hours' early access to new products before everyone else.", "")]
    body = (intro("The annual plan, in use", "What £36 a year actually gets used for")
            + icon_rows(ctx, rows)
            + text_row(p("Happy on Free? That's fine. You keep your 5% either way, and this is the last email about upgrading.", 16, margin="0"), "8px 44px 24px")
            + text_row(button("Join for £36 a year", JOIN), "0 44px 32px")
            + footer(ctx))
    return shell(ctx, body, "Free returns, a monthly prize draw and a bigger trade-in. Then it's up to you.")


# ---------------- Annual branch ----------------
def pe1(ctx):
    body = (intro("Annual membership", f"Good call{name_suffix(ctx)}. You're a member.",
                  "Your £36 annual membership is live. Everything below works from today.")
            + benefit_list(ctx, ANNUAL)
            + h2("Three things to do this week")
            + steps([("Use your first-order 10%.", "Your welcome code is saved in the Codes section of your member portal."),
                     ("Check this month's 10%.", "You get 10% off one order every month. It's waiting in your portal too."),
                     ("Get a trade-in quote.", "Your +5% member bonus starts after 60 days, so a quote now tells you what to expect.")])
            + portal_button()
            + text_row(p("Questions? Reply to this email. Alex and the team read every one.", 15, MUTED, "0"), "0 44px 32px")
            + footer(ctx))
    return shell(ctx, body, "10% off your first order and one order every month, free returns and more. All live now.")


def pe2(ctx):
    body = (intro("Free returns", "Free returns, and how they work",
                  "You get four free returns a year. Order two sizes, keep the one that fits, send the other back.")
            + steps([("Log in to your member portal.", "That's where returns start."),
                     ("Fill in the returns request form.", "Tell us what's coming back and why."),
                     ("Send it back.", "As a member, the return is free. You've got four a year, so don't save them for an emergency.")])
            + text_row(button("Start a return in my portal", PORTAL), "8px 44px 24px")
            + member_note(ctx, "Your monthly 10% is ready", "One order a month gets 10% off. The code is in your member portal.",
                          "Open my portal", PORTAL)
            + text_row("", "0 0 32px")
            + footer(ctx))
    return shell(ctx, body, "Order two sizes, keep one, send one back. Free, four times a year.")


def pe3(ctx):
    body = (intro("One month in", "Your first month as a member",
                  "A quick reminder of what's there for you, now you've had a month.")
            + icon_rows(ctx, [
                ("member-price-tag", "This month's 10%", "A new month means a new 10% off one order. It's in your portal.", link("Open my portal", PORTAL)),
                ("monthly-prize-draw", "This month's prize draw", "You're in it automatically. We draw it at the start of next month.", ""),
                ("trade-in", "Trade-in bonus in 30 days", "Your +5% trade-in bonus starts at 60 days. Worth getting a quote ready.", link("Get a trade-in quote", TRADE_IN))])
            + text_row("", "0 0 12px")
            + footer(ctx))
    return shell(ctx, body, "Your monthly 10%, this month's prize draw and what's coming at day 60.")


def pe4(ctx):
    body = (intro("Trade-in bonus", "Your trade-in bonus is now on",
                  "You've been a member for 60 days, so you now get 5% more on any trade-in value.")
            + steps([("Get a quote.", "Tell us what you've got: clubs or a trolley."),
                     ("Send it in.", "We check it and confirm the value."),
                     ("Spend it.", "The value comes off your next order, with your +5% on top.")])
            + text_row(button("Get a trade-in quote", TRADE_IN), "12px 44px 32px")
            + footer(ctx))
    return shell(ctx, body, "5% more on any trade-in value, from today.")


def pe5(ctx):
    body = (intro("Renewal reminder", "Your membership renews in about a month",
                  "We said we'd remind you before your £36 annual membership renews, so here it is.")
            + benefit_list(ctx, ANNUAL)
            + text_row(p("Happy with it? You don't need to do anything. Want to stop? You can cancel any time from your member portal "
                         "before it renews.", 16, margin="0"), "16px 44px 24px")
            + portal_button("Manage my membership")
            + footer(ctx))
    return shell(ctx, body, "A reminder before your £36 annual membership renews. Nothing to do if you're staying.")


BR = "⛳ Evolution Golf"
EMAILS = [
    dict(key="fe1", fn=fe1, name="Free E1 · You're in", timing="Free · straight away", sender=BR,
         subject="You're in: your free Evolution Golf membership", preview="5% off member deals, free delivery over £30 and loyalty points. All live now.", slots=[]),
    dict(key="fe2", fn=fe2, name="Free E2 · The honest maths", timing="Free · day 4 · still on Free", sender=BR,
         subject="Is the £36 plan worth it? The honest maths", preview="10% off one order a month pays back the £36 at about £30 an order. The full sum inside.", slots=[]),
    dict(key="fe3", fn=fe3, name="Free E3 · The plan in use", timing="Free · day 12 · still on Free", sender=BR,
         subject="What £36 a year actually gets used for", preview="Free returns, a monthly prize draw and a bigger trade-in. Then it's up to you.", slots=[]),
    dict(key="pe1", fn=pe1, name="Annual E1 · Welcome", timing="Annual · straight away · smart sending off", sender=BR,
         subject="Welcome to Evolution Golf membership", preview="10% off your first order and one order every month, free returns and more. All live now.", slots=[]),
    dict(key="pe2", fn=pe2, name="Annual E2 · Free returns", timing="Annual · day 3", sender=BR,
         subject="Free returns, and how they work", preview="Order two sizes, keep one, send one back. Free, four times a year.", slots=[]),
    dict(key="pe3", fn=pe3, name="Annual E3 · First month", timing="Annual · day 30", sender=BR,
         subject="Your first month as a member", preview="Your monthly 10%, this month's prize draw and what's coming at day 60.", slots=[]),
    dict(key="pe4", fn=pe4, name="Annual E4 · Trade-in bonus on", timing="Annual · day 60", sender=BR,
         subject="Your trade-in bonus is now on", preview="5% more on any trade-in value, from today.", slots=[]),
    dict(key="pe5", fn=pe5, name="Annual E5 · Renewal reminder", timing="Annual · day 335", sender=BR,
         subject="Your membership renews in about a month", preview="A reminder before your £36 annual membership renews. Nothing to do if you're staying.", slots=[]),
]


def page(frames, images):
    tpl = (OUT / "f3_b_template.html").read_text()
    swaps = [
        ("Evolution Golf · F3 Checkout abandonment · Trolleys · Design B", "Evolution Golf · F2 Membership welcome · Design B"),
        ("<h1>The trolley checkout sequence, on the course</h1>", "<h1>The membership welcome, two plans</h1>"),
        ("All four emails in the chosen design, with the approved copy.",
         "Eight emails: three for Free members (nudging to the £36 plan, honestly) and five for £36 annual members (using the benefits, then a renewal reminder)."),
        ('"eg-f3b-view"', '"eg-f2-view"'),
    ]
    for a, c in swaps:
        if a not in tpl:
            raise SystemExit("template text not found: " + a[:50])
        tpl = tpl.replace(a, c)
    tpl = re.sub(r'<section class="block">\s*<p class="eyebrow">Image brief</p>.*?</section>', '', tpl, flags=re.S)
    tpl = re.sub(r'<section class="block">\s*<p class="eyebrow">Day 2, 18:00.*?</section>', '', tpl, flags=re.S)
    flags = """
      <li><strong>Two plans, not four:</strong> the plan was written for Free, Club Access, Pro and Annual. Your site now sells Free and the £36 annual plan, so the flow has two branches. Existing Club, Pro and Annual members aren't sent anything.</li>
      <li><strong>Two drafts:</strong> "EG · F2 Membership · Free" starts when someone joins your Free members segment; "EG · F2 Membership · Annual" starts when someone is tagged AnnualMember. A Free member who upgrades at any point moves to the Annual one.</li>
      <li><strong>Old member welcomes:</strong> when you switch these on, switch off "FLOW: Welcome - Evolution Free" (it starts from the same segment) so nobody gets both.</li>
      <li><strong>No images needed:</strong> these emails use icons only.</li>
    """
    tpl = re.sub(r'(<section class="block flags">.*?<ol>).*?(</ol>)', lambda m: m.group(1) + flags + m.group(2), tpl, flags=re.S)
    return tpl.replace("/*__DATA__*/null", json.dumps({"emails": [{k: v for k, v in e.items() if k != "fn"} for e in EMAILS],
                                                        "slots": {}, "frames": frames, "images": images}))


def build(img_dir):
    icons = local_icons()
    images = {k: data_uri(img_dir / f) for k, f in {"logo": "p-logo.png", "roundel": "p-roundel.png"}.items()}
    prev = {k: f"__IMG_{k}__" for k in images}
    frames = {f"{e['key']}|{m}": e["fn"](Ctx(prev, "none", True, icons)) for e in EMAILS for m in f1.MODES}
    (OUT / "f2-preview.html").write_text(page(frames, images))
    hosted = json.loads(HOSTED.read_text())
    live = {"logo": b.LIVE["logo"], "roundel": b.LIVE["roundel"]}
    (OUT / "f2").mkdir(exist_ok=True)
    for e in EMAILS:
        (OUT / "f2" / f"{e['key']}.html").write_text(e["fn"](Ctx(live, "none", True, hosted, live=True)))
    print("f2-preview.html", (OUT / "f2-preview.html").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    build(pathlib.Path(sys.argv[1]))

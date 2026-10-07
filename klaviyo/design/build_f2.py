"""F2 Membership welcome, built in design B with the Astra icon library.

Deviation from the pack (records the site as of 1 Oct 2026): the pack's four tiers (Free / Club Access / Pro / Annual) are now
two plans on evolutiongolf.co.uk/pages/members-page: Free (£0) and the Annual Membership (£36 a year). So two branches:
  Free   - FE1 portal live (day 0), FE2 the honest maths (day 4), FE3 the plan in use (day 12). Before FE2/FE3: if no longer
           Free, they get PE1 instead and stop.
  Annual - PE1 welcome (day 0, smart sending off), PE2 free returns (day 3), PE3 first month (day 30),
           PE4 two months in (day 60), PE5 renewal reminder (day 335).
Every fact below is from the members page; nothing else is assumed.

Run: python3 klaviyo/design/build_f2.py <scratch img dir>
"""
import json, pathlib, re, sys

import build_f3_b as b
import build_f1 as f1
from build_f1 import (hero, name_suffix, G, DG, GOLD, CREAM, INK, HEAD, MUTED, LINE, WHITE, SANS, SERIF, confirm, data_uri, icon, first_name, intro, p,
                      text_row, link, button, member_note, icon_rows, benefits_table, h3, Ctx, local_icons, HOSTED, OUT)

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
    return text_row(button(label, PORTAL), "28px 48px 40px")


# Benefits table rows (editorial system, 7 Oct 2026). Members: free delivery over £10, £50 for non-members.
ANNUAL = [("10% off monthly", "Your first order, then one order every month after, on anything across the site."),
          ("Free delivery over £10", "Normally £50 for non-members."),
          ("Four free returns a year", "Start a return from your member portal."),
          ("Instant daily deals", "New every day, and you won't see them anywhere else on the site."),
          ("Exclusive member deals", "Only members can see them. They're in your portal."),
          ("Monthly prize draw", "Entered automatically every month."),
          ("Early access", "48 hours on new products before everyone else.")]


# Icon row (Layton, 7 Oct 2026): Phosphor Light icons, rendered as 48px transparent PNGs in brand green and hosted in
# Klaviyo. Design rule: one three-item row per email, never next to copy, headlines or buttons, so it sits above the footer.
PH_ICONS = {"seal-percent": "https://cdn.klaviyomail.com/company/SiyYRR/images/dafe9b01-ed19-48c3-9fba-b99fb479e11d.png",
            "tag": "https://cdn.klaviyomail.com/company/SiyYRR/images/e562e48c-d737-4094-9968-7b77fc3cc9b1.png",
            "trophy": "https://cdn.klaviyomail.com/company/SiyYRR/images/a29ce19b-81ee-40bb-9771-99db73608069.png"}
MEMBER_ROW = [("seal-percent", "10% off one order a month"), ("tag", "Instant daily deals"), ("trophy", "Monthly prize draw")]


def icon_row(items=MEMBER_ROW):
    cells = "".join(
        f'<td class="usp-c" width="33%" align="center" valign="top" style="width:33%;padding:0 10px;{"border-left:1px solid " + LINE + ";" if i else ""}">'
        f'<img src="{PH_ICONS[n]}" width="24" height="24" alt="" style="width:24px;height:24px;display:block;margin:0 auto 8px;">'
        f'<p style="margin:0;font:13px/19px {SANS};color:{MUTED};">{label}</p></td>' for i, (n, label) in enumerate(items))
    return text_row(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid {LINE};border-bottom:1px solid {LINE};">'
                    f'<tr><td style="padding:20px 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>{cells}</tr></table></td></tr></table>',
                    "32px 48px 40px")


def benefit_list(ctx, items, pad="20px 48px 0"):
    return text_row(benefits_table(items).replace("margin:0 0 28px;", "margin:0;"), pad)


def steps(items):
    rows = ""
    for i, (head, text) in enumerate(items, 1):
        last = f"border-bottom:1px solid {LINE};" if i == len(items) else ""
        rows += (f'<tr><td width="40" valign="top" style="width:40px;padding:14px 0;border-top:1px solid {LINE};{last}font:400 24px/26px {SERIF};color:{G};">{i}</td>'
                 f'<td valign="top" style="padding:14px 0;border-top:1px solid {LINE};{last}font:15px/25px {SANS};color:{INK};">'
                 f'<strong style="font-weight:600;color:{HEAD};">{head}</strong> {text}</td></tr>')
    return text_row(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table>', "16px 48px 0")


def h2(text):
    return text_row(h3(text, "0"), "36px 48px 0")


# ---------------- Free branch ----------------
def fe1(ctx):
    body = (hero(ctx, "W1") + intro("Free membership", f"You're in{name_suffix(ctx)}.",
                  "Your free Evolution Golf membership is live. Here's what it gives you, starting today.")
            + benefit_list(ctx, [("Your own member portal", "Log in to see this month's member deals."),
                                 ("5% off member portal deals", "Applied when you're logged in."),
                                 ("Free delivery", "On orders over £30."),
                                 ("Loyalty points", "On everything you buy.")])
            + h2("Two things worth doing this week")
            + steps([("Log in to your portal.", "Check your details and see this month's member deals."),
                     ("Have a look at the deals.", "Your 5% is applied to member portal deals when you're logged in.")])
            + portal_button()
            + footer(ctx))
    return shell(ctx, body, "5% off member deals, free delivery over £30 and loyalty points. All live now.")


def fe2(ctx):
    maths = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td bgcolor="{CREAM}" style="background:{CREAM};padding:24px;">'
             f'<p style="margin:0 0 10px;font:600 11px/16px {SANS};letter-spacing:.14em;text-transform:uppercase;color:{GOLD};">The sum</p>'
             f'<p style="margin:0 0 10px;font:400 24px/30px {SERIF};color:{HEAD};">£36 a year pays for itself at £30 an order.</p>'
             f'<p style="margin:0;font:15px/24px {SANS};color:{INK};">10% off one £30 order a month is £3. Twelve months of that is £36. '
             f'Your first order gets 10% off too. Spend more than £30 an order and you\'re ahead.</p></td></tr></table>')
    body = (intro("Free or £36 a year?", "Is the annual membership worth it? Here's the honest maths.",
                  "You get 5% off member deals on Free. The £36 plan doubles that and adds a few things Free doesn't have.")
            + text_row(maths, "20px 48px 8px")
            + h2("What the £36 plan adds")
            + benefit_list(ctx, ANNUAL)
            + text_row(p("If you only buy from us once or twice a year, stay on Free. You keep your 5% either way. "
                         "If you buy most months, the plan pays for itself.", 16, margin="0"), "16px 48px 24px")
            + text_row(button("Compare the two plans", JOIN), "24px 48px 0")
            + icon_row() + footer(ctx))
    return shell(ctx, body, "10% off one order a month pays back the £36 at about £30 an order. The full sum inside.")


def fe3(ctx):
    rows = [("free-returns", "Free returns",
             "Order two sizes of a shoe, keep the one that fits and send the other back free. Four free returns a year.", ""),
            ("monthly-prize-draw", "A prize draw every month", "You're entered automatically every month, and we draw it at the start of the next one.", ""),
            ("member-price-tag", "Member-only deals",
             "Exclusive member deals in the portal, plus instant daily deals you won't see anywhere else on the site.", link("See the member benefits", JOIN)),
            ("calendar", "First look at new kit", "48 hours' early access to new products before everyone else.", "")]
    body = (intro("The annual plan, in use", "What £36 a year actually gets used for")
            + icon_rows(ctx, rows)
            + text_row(p("Happy on Free? That's fine. You keep your 5% either way, and this is the last email about upgrading.", 16, margin="0"), "28px 48px 0")
            + text_row(button("Become a member, £36 a year", JOIN), "24px 48px 0")
            + icon_row() + footer(ctx))
    return shell(ctx, body, "Free returns, a monthly prize draw and member-only deals. Then it's up to you.")


# ---------------- Annual branch ----------------
def pe1(ctx):
    body = (hero(ctx, "M1") + intro("Annual membership", f"Good call{name_suffix(ctx)}. You're a member.",
                  "Your £36 annual membership is live. Everything below works from today.")
            + benefit_list(ctx, ANNUAL)
            + h2("Three things to do this week")
            + steps([("Use your first-order 10%.", "Your welcome code is saved in the Codes section of your member portal."),
                     ("Check this month's 10%.", "10% off one order every month, on anything across the site. The code is in your portal."),
                     ("Check the instant daily deals.", "They're in your portal, and you won't see them anywhere else on the site.")])
            + portal_button()
            + text_row(p("Questions? Reply to this email. Alex and the team read every one.", 15, MUTED, "0"), "0 48px 32px")
            + footer(ctx))
    return shell(ctx, body, "10% off your first order and one order every month, free returns and more. All live now.")


def pe2(ctx):
    body = (intro("Member deals", "Your member deals, and where to find them",
                  "As a member you get deals that nobody else on the site can see. Here's where they are.")
            + steps([("Log in to your member portal.", "That's where the deals are."),
                     ("Check the instant daily deals.", "New ones every day, and you won't see them anywhere else on the site."),
                     ("Look through the exclusive member deals.", "Only members can see these, and they're in your portal too.")])
            + text_row(button("See today's deals", PORTAL), "28px 48px 0")
            + member_note(ctx, "Your monthly 10% is ready",
                          "One order a month gets 10% off, on anything across the site. The code is in your member portal.",
                          "Open my portal", PORTAL)
            + text_row(p("Need to send something back? Members get four free returns a year. Start one from your portal.", 15, MUTED, "0"),
                       "24px 48px 0")
            + icon_row() + footer(ctx))
    return shell(ctx, body, "Instant daily deals and exclusive member deals. Only in your portal.")


def portal_cta(lead):
    """One clear next step under the sections: a short lead line, then the one primary button."""
    return (text_row(p(f'<strong style="font-weight:600;color:{HEAD};">{lead}</strong> It\'s in your member portal, with today\'s deals.',
                       margin="0"), "28px 48px 0")
            + text_row(button("Open my member portal", PORTAL), "20px 48px 0"))


PRIZE_LINK = link("See this month's prize", JOIN)  # the prize is shown on the members page


def pe3(ctx):
    body = (intro("One month in", "Your first month as a member",
                  "A quick reminder of what's there for you, now you've had a month.")
            + icon_rows(ctx, [
                ("member-price-tag", "This month's 10%", "A new month means a new 10% off one order, on anything across the site.", ""),
                ("monthly-prize-draw", "This month's prize draw", "You're in it automatically. We draw it at the start of next month.", PRIZE_LINK),
                ("members-portal", "Instant daily deals", "New in your portal every day, and not on the rest of the site.", "")])
            + portal_cta("Your 10% code is waiting.")
            + icon_row() + footer(ctx))
    return shell(ctx, body, "Your monthly 10%, this month's prize draw and the member deals.")


def pe4(ctx):
    rows = [("member-price-tag", "This month's 10%", "One order this month gets 10% off, on anything across the site.", ""),
            ("monthly-prize-draw", "This month's prize draw", "You're in it automatically. We draw it at the start of next month.", PRIZE_LINK),
            ("members-portal", "Instant daily deals", "New in your portal every day and not on the rest of the site, plus 48 hours' early access to new products.", "")]
    body = (intro("Two months in", "Two months in: here's what's yours this month",
                  "The monthly 10%, the prize draw and the member deals, all in one place.")
            + icon_rows(ctx, rows) + portal_cta("This month's 10% code is waiting.") + icon_row() + footer(ctx))
    return shell(ctx, body, "This month's 10%, the prize draw and member deals. All in your portal.")


def pem(ctx):
    body = (intro("Your monthly 10%", "This month's 10% is ready",
                  "As a member, one order every month gets 10% off. A new month means a new one.")
            + steps([("Open your member portal.", "The code is in the Codes section."),
                     ("Use it on one order this month.", "Anything you need: balls, a glove, or something bigger."),
                     ("Next month there's another.", "A new month brings a new 10%.")])
            + text_row(button("Open my member portal", PORTAL), "28px 48px 0")
            + member_note(ctx, "You're in this month's prize draw", "Every member is entered automatically. We draw it at the start of next month.",
                          "See member benefits", JOIN)
            + icon_row() + footer(ctx))
    return shell(ctx, body, "One order this month gets 10% off. Your code is in your member portal.")


def pe5(ctx):
    body = (intro("Renewal reminder", "Your membership renews in about a month",
                  "We said we'd remind you before your £36 annual membership renews, so here it is.")
            + benefit_list(ctx, ANNUAL)
            + text_row(p("Happy with it? You don't need to do anything. Want to stop? You can cancel any time from your member portal "
                         "before it renews.", 16, margin="0"), "16px 48px 24px")
            + portal_button("Manage my membership")
            + icon_row() + footer(ctx))
    return shell(ctx, body, "A reminder before your £36 annual membership renews. Nothing to do if you're staying.")


BR = "⛳ Evolution Golf"
EMAILS = [
    dict(key="fe1", fn=fe1, name="Free E1 · You're in", timing="Free · straight away", sender=BR,
         subject="You're in: your free Evolution Golf membership", preview="5% off member deals, free delivery over £30 and loyalty points. All live now.", slots=["W1"]),
    dict(key="fe2", fn=fe2, name="Free E2 · The honest maths", timing="Free · day 4 · still on Free", sender=BR,
         subject="Is the £36 plan worth it? The honest maths", preview="10% off one order a month pays back the £36 at about £30 an order. The full sum inside.", slots=[]),
    dict(key="fe3", fn=fe3, name="Free E3 · The plan in use", timing="Free · day 12 · still on Free", sender=BR,
         subject="What £36 a year actually gets used for", preview="Free returns, a monthly prize draw and member-only deals. Then it's up to you.", slots=[]),
    dict(key="pe1", fn=pe1, name="Annual E1 · Welcome", timing="Annual · straight away · smart sending off", sender=BR,
         subject="Welcome to Evolution Golf membership", preview="10% off your first order and one order every month, free returns and more. All live now.", slots=["M1"]),
    dict(key="pe2", fn=pe2, name="Annual E2 · Member deals", timing="Annual · day 3", sender=BR,
         subject="Your member deals, and where to find them", preview="Instant daily deals and exclusive member deals. Only in your portal.", slots=[]),
    dict(key="pe3", fn=pe3, name="Annual E3 · First month", timing="Annual · day 30", sender=BR,
         subject="Your first month as a member", preview="Your monthly 10%, this month's prize draw and the member deals.", slots=[]),
    dict(key="pe4", fn=pe4, name="Annual E4 · Two months in", timing="Annual · day 60", sender=BR,
         subject="Two months in: here's what's yours this month", preview="This month's 10%, the prize draw and member deals. All in your portal.", slots=[]),
    dict(key="pem", fn=pem, name="Annual · Monthly 10% reminder", timing="Annual · months 3 to 10, every 30 days", sender=BR,
         subject="Your 10% for this month is ready", preview="One order this month gets 10% off. Your code is in your member portal.", slots=[]),
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
    images = {k: data_uri(img_dir / f) for k, f in {"logo": "p-logo-white.png", "roundel": "p-roundel.png"}.items()}
    prev = {k: f"__IMG_{k}__" for k in images}
    frames = {f"{e['key']}|{m}": e["fn"](Ctx(prev, "none", True, icons)) for e in EMAILS for m in f1.MODES}
    (OUT / "f2-preview.html").write_text(page(frames, images))
    hosted = json.loads(HOSTED.read_text())
    live = {"logo": b.LIVE["logo"], "roundel": b.LIVE["roundel"], **f1.PHOTOS}
    (OUT / "f2").mkdir(exist_ok=True)
    for e in EMAILS:
        (OUT / "f2" / f"{e['key']}.html").write_text(e["fn"](Ctx(live, "now", True, hosted, live=True)))
    print("f2-preview.html", (OUT / "f2-preview.html").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    build(pathlib.Path(sys.argv[1]))

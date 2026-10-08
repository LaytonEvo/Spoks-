"""F12 Winback, in the editorial design (copy doc: https://claude.ai/code/artifact/eefcc4f0-b33e-4f78-b251-be7b40c0ff5e).

Customers whose last order was 120+ days ago, still reading emails, not members (Free or annual; Layton, 8 Oct 2026).
Three emails, no codes, evergreen: E1 the sale + membership + daily deals (past trolley / club buyers get a "still going
strong?" panel, picked by a split in the flow since a segment trigger has no order on it), E2 a plain letter from Alex,
E3 a short sign-off. Writes klaviyo/design/f12/<key>.html (live) and <key>.preview.html (dashboard).

Run: python3 klaviyo/design/build_f12.py
"""
import pathlib

import build_f3_b as b
import build_f1 as f1
from build_f1 import (G, INK, HEAD, MUTED, LINE, WHITE, SANS, SERIF, unsub, intro, p, text_row, link, member_note, feature,
                      benefits_table, BENEFITS, FINE, URL, PHOTOS, name_suffix)
from build_f3 import Ctx, PHONE

OUT = pathlib.Path(__file__).parent / "f12"
REASON = "you've shopped with Evolution Golf"
SALE = f1.SITE + "/collections/sale"  # smart collection: tagged Sale and in stock (345 products on 8 Oct 2026)


def footer(ctx):
    return f1.footer(ctx, REASON)


def close(ctx):
    return b.usp() + b.trust() + footer(ctx)


def h3(t, m="0 0 8px"):
    return f'<h3 style="margin:{m};font:400 24px/30px {SERIF};color:{HEAD};">{t}</h3>'


def section(n, title, text, extra=""):
    return text_row(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td style="border-top:1px solid {LINE};padding:24px 0 0;">'
                    + b.eyebrow(f"{n} of 3") + h3(title) + p(text, 15, margin="0 0 8px" if extra else "0") + extra + '</td></tr></table>', "28px 48px 0")


# ---------------- Email 1 ----------------
def e1(ctx, hardware=False):
    still = member_note(ctx, "Still going strong?", "If your trolley battery isn't lasting a full round any more, or your grips are worn, "
                        f"reply or call {PHONE} and we'll tell you honestly whether it's time for a replacement or just a tune-up.",
                        "Get in touch", URL["contact"]) if hardware else ""
    body = (intro("It's been a while", f"Good to see you again{name_suffix(ctx)}",
                  "It's been a few months since your last order, so here's a quick catch-up on what's changed.")
            + section(1, "Have a look at the sale", "Reduced prices on kit that's in stock and ready to send.", link("Shop the sale", SALE))
            + section(2, "Membership, instead of endless codes", "Join free and get 5% off everything on the site. Or go annual for £36 a year: "
                      "10% off one order every month, free returns, instant daily deals and a monthly prize draw.")
            + feature("Membership · £36 a year", "10% off one order every month.", "Here's everything that comes with it.", BENEFITS,
                      "Become a member, £36 a year", URL["join"], FINE, card=True)
            + text_row(p(f'<strong style="font-weight:600;color:{HEAD};">Or start free:</strong> 5% off everything. ' + link("Join free", URL["join"]),
                         15, margin="0"), "20px 48px 0")
            + section(3, "Instant daily deals", "Members get new deals in the portal every day that you won't see anywhere else on the site.")
            + still + text_row("", "0 0 8px") + close(ctx))
    return f1.shell(ctx, body, "What's in the sale, member savings and daily deals. A quick catch-up.")


# ---------------- Email 2: a plain letter from Alex ----------------
def letter(ctx, paras, preheader):
    pp = f'margin:0 0 16px;font:16px/26px {SANS};color:{INK};'
    hi = "{{ person.first_name|default:'there' }}" if ctx.live else "Sam"
    sig = (f'<table role="presentation" cellpadding="0" cellspacing="0"><tr><td width="92" style="padding-right:16px;vertical-align:top;">'
           f'<img src="{PHOTOS["A1"]}" width="76" height="76" alt="Alex" style="width:76px;height:76px;border-radius:50%;display:block;"></td>'
           f'<td style="vertical-align:top;font:16px/24px {SANS};color:{INK};">Alex<br><span style="color:{MUTED};">Head of Ecommerce, Evolution Golf</span></td></tr></table>')
    body = (f'<tr><td class="px" bgcolor="{WHITE}" style="padding:44px 48px 28px;"><p style="{pp}">Hi {hi},</p>'
            + "".join(f'<p style="{pp}">{x}</p>' for x in paras) + sig + '</td></tr>'
            f'<tr><td class="px foot-light" bgcolor="{WHITE}" style="padding:18px 48px 24px;border-top:1px solid {LINE};font:12px/18px {SANS};color:{MUTED};">'
            f'Evolution Golf, Unit 3, Parvenah Park, Embankment Way, Ringwood, BH24 1WL<br>' + unsub(ctx, MUTED) + '</td></tr>')
    return f1.shell(ctx, body, preheader, header=False)


def e2(ctx):
    return letter(ctx, ["I'm Alex, I look after the online side of Evolution Golf. It's been a little while since we last saw you, so I wanted to "
                        "say a quick hello and see how your golf is going.",
                        "If you're weighing up anything new, whether that's a trolley, a set of clubs or just a few bits for the bag, I'm always "
                        "happy to help. Tell me what you're after and I'll point you to the right thing, or make sure you're getting the best "
                        "price we can do.",
                        "And if there's anything we could do better, I'd love to hear that too. Just hit reply. It comes straight to me and I "
                        "read every one.",
                        "Hope to see you again soon,"],
                  "A quick hello, and an offer of help if you need it.")


# ---------------- Email 3 ----------------
def e3(ctx):
    prefs = ("{% manage_preferences 'change your preferences' %}" if ctx.live
             else f'<a href="#" style="color:{G};">change your preferences</a>')
    rows = [("Free membership", "5% off everything, from your first order"),
            ("Annual membership, £36 a year", "10% off one order a month, free delivery over £10, free returns, instant daily deals"),
            ("Talk to our team", f"Honest advice on trolleys, clubs and kit: {PHONE} or reply to this email")]
    body = (intro("Whenever you're ready", f"We'll leave it there{name_suffix(ctx)}",
                  "This is the last email in this little catch-up, so we'll keep it short. When you next need anything for your game, "
                  "here's what's waiting for you:")
            + text_row(benefits_table(rows) + f1.button("Shop Evolution Golf", URL["shop"]), "8px 48px 0")
            + text_row(p(f"You'll still get our usual emails. If you'd rather hear from us less, you can {prefs} here.", 14, MUTED, "0"), "28px 48px 0")
            + text_row("", "0 0 8px") + close(ctx))
    return f1.shell(ctx, body, "No more nudges. Here's what's there whenever you need it.")


BR, ALEX = "⛳ Evolution Golf", "Alex at Evolution Golf"
E1_SUBJECT, E1_PREVIEW = "A few things have changed since you were last in", "What's in the sale, member savings and daily deals. A quick catch-up."
EMAILS = [
    dict(key="e1h", fn=lambda c: e1(c, True), name="E1 · What's changed (past hardware buyers)", timing="Day 0, as they join · bought a trolley or clubs before",
         sender=BR, subject=E1_SUBJECT, preview=E1_PREVIEW, slots=[]),
    dict(key="e1", fn=lambda c: e1(c, False), name="E1 · What's changed", timing="Day 0, as they join · everyone else", sender=BR,
         subject=E1_SUBJECT, preview=E1_PREVIEW, slots=[]),
    dict(key="e2", fn=e2, name="E2 · A note from Alex", timing="Day 10, 17:30", sender=ALEX,
         subject="How's your game going{% if person.first_name %}, {{ person.first_name }}{% endif %}?",
         preview="A quick hello, and an offer of help if you need it.", slots=[]),
    dict(key="e3", fn=e3, name="E3 · The last one for a while", timing="Day 24, 09:30", sender=BR,
         subject="The last one from us for a while", preview="No more nudges. Here's what's there whenever you need it.", slots=[]),
]


def build():
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.html"):
        f.unlink()
    live = {"logo": b.LIVE["logo"], "roundel": b.LIVE["roundel"], **PHOTOS}
    for e in EMAILS:
        (OUT / f"{e['key']}.html").write_text(e["fn"](Ctx(live, "now", True, {}, live=True)))
        (OUT / f"{e['key']}.preview.html").write_text(e["fn"](Ctx(live, "now", True, {}, live=False)))
    print("f12:", len(EMAILS), "emails")


if __name__ == "__main__":
    build()

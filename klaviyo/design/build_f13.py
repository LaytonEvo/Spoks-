"""F13 Sunset, in the editorial design (copy doc: https://claude.ai/code/artifact/9291dfce-47a0-43dd-9bed-d4a69af4c819).

People sent 8+ emails who haven't opened or clicked in 150 days or ordered in 180, not members (Free or annual; Layton,
8 Oct 2026). E1 asks once whether they want to stay (any click keeps them; the button goes to the home page); E2 from Alex
10 days later; 7 days after that the flow sets sunset_status = suppress, and the segment "EG · Sunset · to suppress" is
excluded from campaigns and flows. No offers, no products. Writes klaviyo/design/f13/<key>.html and <key>.preview.html.

Run: python3 klaviyo/design/build_f13.py
"""
import pathlib

import build_f3_b as b
import build_f1 as f1
from build_f1 import INK, MUTED, LINE, WHITE, SANS, unsub, intro, p, text_row, URL, PHOTOS, name_suffix
from build_f3 import Ctx

OUT = pathlib.Path(__file__).parent / "f13"
REASON = "you're subscribed to Evolution Golf emails"


def e1(ctx):
    unsub_link = ("{% unsubscribe 'unsubscribe' %}" if ctx.live else f'<a href="#" style="color:{MUTED};">unsubscribe</a>')
    body = (intro("Quick check-in", f"Shall we keep sending these{name_suffix(ctx)}?",
                  "It's been a while since you've opened one of our emails, so rather than keep filling your inbox, we thought we'd ask.")
            + text_row(p("If you'd like to keep hearing about new kit, the sale and member deals, just tap the button. That's all it takes.",
                         margin="0 0 24px") + f1.button("Yes, keep sending", URL["shop"]), "0 48px 0")
            + text_row(p(f"If you'd rather not, no problem: you don't need to do anything. We'll check once more, then stop. Or you can "
                         f"{unsub_link} now.", 14, MUTED, "0"), "28px 48px 40px")
            + f1.footer(ctx, REASON))
    return f1.shell(ctx, body, "One click keeps you on the list. Or we'll leave you be.")


def e2(ctx):
    pp = f'margin:0 0 16px;font:16px/26px {SANS};color:{INK};'
    hi = "{{ person.first_name|default:'there' }}" if ctx.live else "Sam"
    paras = ["Alex here, from Evolution Golf. This is the last email we'll send you, unless you'd like us to keep going.",
             "No hard feelings either way. Inboxes are busy, and we'd rather send emails to people who want them.",
             "If you do want to stay, one click below does it."]
    sig = (f'<table role="presentation" cellpadding="0" cellspacing="0"><tr><td width="92" style="padding-right:16px;vertical-align:top;">'
           f'<img src="{PHOTOS["A1"]}" width="76" height="76" alt="Alex" style="width:76px;height:76px;border-radius:50%;display:block;"></td>'
           f'<td style="vertical-align:top;font:16px/24px {SANS};color:{INK};">Thanks for being with us,<br>Alex<br>'
           f'<span style="color:{MUTED};">Head of Ecommerce, Evolution Golf</span></td></tr></table>')
    body = (f'<tr><td class="px" bgcolor="{WHITE}" style="padding:44px 48px 28px;"><p style="{pp}">Hi {hi},</p>'
            + "".join(f'<p style="{pp}">{x}</p>' for x in paras)
            + f'<div style="margin:8px 0 28px;">{f1.button("Keep me on the list", URL["shop"])}</div>{sig}</td></tr>'
            f'<tr><td class="px foot-light" bgcolor="{WHITE}" style="padding:18px 48px 24px;border-top:1px solid {LINE};font:12px/18px {SANS};color:{MUTED};">'
            f'Evolution Golf, Unit 3, Parvenah Park, Embankment Way, Ringwood, BH24 1WL<br>' + unsub(ctx, MUTED) + '</td></tr>')
    return f1.shell(ctx, body, "One click keeps you on the list. No hard feelings either way.", header=False)


BR, ALEX = "⛳ Evolution Golf", "Alex at Evolution Golf"
EMAILS = [
    dict(key="e1", fn=e1, name="E1 · Still want to hear from us?", timing="Day 0, as they join", sender=BR,
         subject="Still want emails from us?", preview="One click keeps you on the list. Or we'll leave you be.", slots=[]),
    dict(key="e2", fn=e2, name="E2 · The last one, unless you say so (from Alex)", timing="Day 10, 17:30 · only if no click", sender=ALEX,
         subject="Last one from us, unless you say otherwise", preview="One click keeps you on the list. No hard feelings either way.", slots=[]),
]


def build():
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.html"):
        f.unlink()
    live = {"logo": b.LIVE["logo"], "roundel": b.LIVE["roundel"], **PHOTOS}
    for e in EMAILS:
        (OUT / f"{e['key']}.html").write_text(e["fn"](Ctx(live, "now", True, {}, live=True)))
        (OUT / f"{e['key']}.preview.html").write_text(e["fn"](Ctx(live, "now", True, {}, live=False)))
    print("f13:", len(EMAILS), "emails")


if __name__ == "__main__":
    build()

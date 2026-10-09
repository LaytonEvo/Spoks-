"""F6 Back in stock, in the editorial design (copy doc: https://claude.ai/code/artifact/0ee00f35-d9f5-46ea-b64e-93c0ba318825).

Starts from Klaviyo's "Subscribed to Back in Stock"; Klaviyo waits until that exact variant is back (back-in-stock delay step).
Email 1 the moment it's back (smart sending off: requested and time-critical), then a text 4 hours later only if they haven't
clicked and have agreed to texts (Layton, 9 Oct 2026). No codes, no urgency. One template: a short line by product type
(matched on the product name, since the back-in-stock event carries no collections) and a line by membership tier.

[CONFIRM: back-in-stock event variable names (ProductName, VariantName, ImageURL, URL, Price) on a real test sign-up; the
button isn't live yet, so no event exists to check. Every variable has a safe fallback.]

Run: python3 klaviyo/design/build_f6.py
"""
import pathlib

import build_f3_b as b
import build_f1 as f1
import build_f9 as f9
from build_f1 import G, INK, HEAD, MUTED, LINE, WHITE, SANS, SERIF, intro, p, text_row, link, URL, PHOTOS, name_suffix
from build_f3 import Ctx, PHONE

OUT = pathlib.Path(__file__).parent / "f6"
REASON = "you asked us to tell you when this was back in stock"
SAMPLE = {"name": "Motocaddy M5 GPS DHC Electric Golf Trolley", "variant": "Black / 36 hole lithium", "price": "£1,149.00",
          "img": "https://cdn.shopify.com/s/files/1/0499/9014/0061/files/2026M1DHCThumbnail.png"}
NAME = "{{ event.ProductName|default:'The item you wanted' }}"
URL_ = "{{ event.URL|default:'https://evolutiongolf.co.uk/' }}"
TROLLEY = ["Trolley"]
CLUBS = ["Driver", "Iron", "Wedge", "Putter", "Hybrid", "Fairway", "Wood"]
SHOES = ["Shoe"]


def name_has(words):
    return " or ".join(f'"{w}" in event.ProductName' for w in words)


def close(ctx):
    delivery = ("{% if person|lookup:'MemberTier' == 'AnnualMember' %}Free delivery over £10{% else %}Free delivery over £50{% endif %}"
                if ctx.live else "Free delivery over £50")
    return b.usp([delivery] + b.TRUST_ITEMS[1:]) + b.trust() + f1.footer(ctx, REASON)


def product(ctx):
    if ctx.live:
        name, variant, price, img = (NAME, "{{ event.VariantName }}", "{{ event.Price }}", "{{ event.ImageURL }}")
        img_html = ("{% if event.ImageURL %}" + f'<img src="{img}" width="240" alt="{NAME}" style="width:240px;max-width:100%;height:auto;'
                    'display:block;margin:0 auto 20px;">' + "{% endif %}")
        variant_html = "{% if event.VariantName and event.VariantName != event.ProductName %}" + f'<br><span style="color:{MUTED};">{variant}</span>' + "{% endif %}"
        price_html = "{% if event.Price %}" + f'<br><strong style="font-weight:600;color:{HEAD};">{price}</strong>' + "{% endif %}"
    else:
        img_html = (f'<img src="{SAMPLE["img"]}" width="240" alt="{SAMPLE["name"]}" style="width:240px;max-width:100%;height:auto;'
                    'display:block;margin:0 auto 20px;">')
        variant_html = f'<br><span style="color:{MUTED};">{SAMPLE["variant"]}</span>'
        price_html = f'<br><strong style="font-weight:600;color:{HEAD};">{SAMPLE["price"]}</strong>'
        name = SAMPLE["name"]
    return text_row(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" '
                    f'style="padding:28px 0;border-top:1px solid {LINE};border-bottom:1px solid {LINE};text-align:center;">{img_html}'
                    f'<p style="margin:0;font:16px/24px {SANS};color:{INK};"><strong style="font-weight:600;color:{HEAD};">{name}</strong>'
                    f'{variant_html}{price_html}</p></td></tr></table>', "28px 48px 0")


def by_type(ctx):
    lines = [(TROLLEY, f"Questions about range, folding or which battery? Give us a ring on {PHONE}."),
             (CLUBS, "It's the exact spec you asked about. Not sure on shaft or loft? Reply and our team will help."),
             (SHOES, "Your size is back. If the fit isn't right, returns are straightforward.")]
    if not ctx.live:
        return "".join(ctx.when("x", text_row(p(t, 15, margin="0"), "20px 48px 0"), f"the product is a {w[0].lower()}") for w, t in lines)
    out = ""
    for i, (words, t) in enumerate(lines):
        out += ("{% if " if i == 0 else "{% elif ") + name_has(words) + " %}" + text_row(p(t, 15, margin="0"), "20px 48px 0")
    return out + "{% endif %}"


def membership(ctx):
    row = lambda html: text_row(p(html, 15, margin="0"), "20px 48px 0")
    none = row(f"Members get 5% off everything with Free membership, or 10% off an order a month on the annual plan. "
               + link("See membership", URL["join"]))
    free = row("Your 5% applies to this.")
    annual = row("If you haven't used this month's 10% yet, it can go on this.")
    return f9.tier(ctx, annual, free, none)


def e1(ctx):
    body = (intro("Back in stock", f"It's back{name_suffix(ctx)}", "You asked us to let you know when this came back into stock. It has.")
            + product(ctx)
            + text_row(f1.button("Take me to it", URL_ if ctx.live else URL["shop"]), "28px 48px 0")
            + by_type(ctx) + membership(ctx)
            + text_row(p("If it's sold out again by the time you look, reply to this email and our team will help.", 15, MUTED, "0"), "24px 48px 0")
            + text_row("", "0 0 8px") + close(ctx))
    return f1.shell(ctx, body, "You asked us to tell you. Here it is.")


SMS1 = "Evolution Golf: {{ event.ProductName|default:'the item you asked about' }} is back in stock. Have a look here: " + URL_

BR = "⛳ Evolution Golf"
EMAILS = [dict(key="e1", fn=e1, name="E1 · It's back", timing="The moment it's back in stock", sender=BR,
               subject="{{ event.ProductName|default:'The item you wanted' }} is back in stock",
               preview="You asked us to tell you. Here it is.", slots=[])]


def build():
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.html"):
        f.unlink()
    live = {"logo": b.LIVE["logo"], "roundel": b.LIVE["roundel"], **PHOTOS}
    for e in EMAILS:
        (OUT / f"{e['key']}.html").write_text(e["fn"](Ctx(live, "now", True, {}, live=True)))
        (OUT / f"{e['key']}.preview.html").write_text(e["fn"](Ctx(live, "now", True, {}, live=False)))
    print("f6:", len(EMAILS), "emails")


if __name__ == "__main__":
    build()

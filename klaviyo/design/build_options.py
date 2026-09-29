"""Design options for the Evolution Golf email system, shown on F3 Trolleys E1.

Builds three email-safe HTML options (A Clubhouse, B On the course, C Letter) and a
preview page that shows each at desktop and phone width. Email files reference the
live image URLs (Klaviyo / Shopify); the preview page embeds small data-URI copies.

Run: python3 klaviyo/design/build_options.py <scratch img dir>
"""
import base64, html, json, pathlib, sys

IMG_DIR = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(__file__).parent

LIVE = {
    "logo": "https://d3k81ch9hvuctc.cloudfront.net/company/SiyYRR/images/07b49b80-e6e5-480f-9c79-25e6f90550a5.png",
    "roundel": "https://d3k81ch9hvuctc.cloudfront.net/company/SiyYRR/images/4aa15d13-2505-4b2d-bec3-2603c69d2397.png",
    "product": "{{ item.product.images.0.src }}",
    "life1": "https://d3k81ch9hvuctc.cloudfront.net/company/SiyYRR/images/648eead5-a37c-4669-90b8-c48143fc11f9.png",
}
PREVIEW = {k: IMG_DIR / f for k, f in
           {"logo": "p-logo.png", "roundel": "p-roundel.png", "product": "p-product.jpg", "life1": "p-life1.jpg"}.items()}


def data_uri(p):
    mime = "image/png" if p.suffix == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


# Brand tokens (logo gold sampled from the live logo file)
G, DG, GOLD, CREAM, INK, MUTED, LINE, WHITE = (
    "#006747", "#003D27", "#B2893F", "#FAF7F1", "#1F2A24", "#5E6B63", "#E4E0D6", "#FFFFFF")
SERIF = "Fraunces,Georgia,'Times New Roman',serif"
SANS = "Inter,Arial,Helvetica,sans-serif"

# Copy: F3 Trolleys E1, from the copy deck (Build Pack 3.3 + confirmed facts)
C = dict(
    preheader="Free UK delivery, 2-year warranty, spread the cost. Pick up where you left off.",
    headline="Still deciding? Fair enough. It's a big buy.",
    intro="Your basket is exactly where you left it.",
    lead="The things people usually want to know before they commit:",
    items=[("Delivery", "Free to the UK mainland, usually 3 to 5 working days.", ""),
           ("Warranty", "2 years on the trolley.", "per brand"),
           ("Paying for it", "Klarna or Clearpay at checkout if you'd rather spread it.", ""),
           ("Right model?", "Our team has filmed straight-talking reviews of the Motocaddy range.", "")],
    cta="Back to my basket", reviews="Watch our trolley reviews",
    product=("Motocaddy 2026 M1 DHC Standard Lithium Electric Golf Trolley", "1", "£799.00"),
    usp=["Free UK delivery", "Expert advice from people who play", "Trade-in on clubs and trolleys", "Custom fitting centre"],
    address="Evolution Golf, Unit 3, Parvenah Park, Embankment Way, Ringwood, BH24 1WL",
)


def confirm(note=""):
    label = f"CONFIRM {note}".strip()
    return (f'<span style="display:inline-block;border:1px dashed {MUTED};border-radius:3px;padding:0 4px;'
            f'font:600 10px/16px {SANS};letter-spacing:.04em;color:{MUTED};vertical-align:1px;">{label}</span>')


def fonts_link():
    return ('<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600'
            '&family=Inter:wght@400;600&display=swap" rel="stylesheet">')


def shell(body, bg, img, web_fonts=True):
    return f"""<!DOCTYPE html><html lang="en-GB"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Your trolley's saved</title>
{fonts_link() if web_fonts else ''}
<style>
body{{margin:0;padding:0;background:{bg};-webkit-text-size-adjust:100%}}
img{{border:0;display:block}} a{{color:{G}}}
@media (max-width:620px){{
 .card{{width:100%!important}} .px{{padding-left:22px!important;padding-right:22px!important}}
 .stack{{display:block!important;width:100%!important;box-sizing:border-box}}
 .h1{{font-size:27px!important;line-height:33px!important}} .hide-m{{display:none!important}}
 .full{{width:100%!important;height:auto!important}}
 .nb{{border-top:0!important;padding-top:0!important}}
}}
</style></head>
<body style="margin:0;padding:0;background:{bg};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{C['preheader']}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{bg};"><tr><td align="center" style="padding:24px 10px;">
<table role="presentation" class="card" width="600" cellpadding="0" cellspacing="0" style="width:600px;background:{WHITE};">
{body}
</table></td></tr></table></body></html>"""


def button(label, bg=G, fg=WHITE, full=True, radius=4):
    width = 'width="100%"' if full else ""
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" {width}><tr>'
            f'<td align="center" bgcolor="{bg}" style="border-radius:{radius}px;">'
            f'<a href="{{{{ event.extra.checkout_url }}}}" style="display:block;padding:16px 28px;font:600 16px/20px {SANS};'
            f'color:{fg};text-decoration:none;">{label}</a></td></tr></table>')


def product_row(img, pad="16px", bg=CREAM):
    t, q, p = C["product"]
    return f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{bg};">
<tr><td width="112" style="padding:{pad} 0 {pad} {pad};vertical-align:middle;">
<img src="{img['product']}" width="96" height="96" alt="{t}" style="width:96px;height:96px;background:{WHITE};border-radius:4px;"></td>
<td style="padding:{pad};vertical-align:middle;font:15px/21px {SANS};color:{INK};">
<strong style="font-weight:600;">{t}</strong><br>
<span style="color:{MUTED};font-size:14px;">Qty {q}</span>
<span style="float:right;font-weight:600;">{p}</span></td></tr></table>"""


def footer_dark(img):
    return f"""<tr><td align="center" bgcolor="{DG}" style="background:{DG};padding:32px 24px 28px;">
<img src="{img['roundel']}" width="44" height="44" alt="Evolution Golf" style="width:44px;height:44px;margin:0 auto 16px;">
<p style="margin:0 0 12px;font:13px/20px {SANS};color:#CFE0D6;">{C['address']}</p>
<p style="margin:0 0 18px;font:600 13px/20px {SANS};"><a href="#" style="color:{WHITE};text-decoration:none;">Instagram</a>
<span style="color:{GOLD};">&nbsp;·&nbsp;</span><a href="#" style="color:{WHITE};text-decoration:none;">Facebook</a>
<span style="color:{GOLD};">&nbsp;·&nbsp;</span><a href="#" style="color:{WHITE};text-decoration:none;">YouTube</a></p>
<p style="margin:0;font:12px/18px {SANS};color:#A9C2B5;">You're receiving this because you started a checkout at evolutiongolf.co.uk.<br>
<a href="#" style="color:#CFE0D6;">Unsubscribe</a> · <a href="#" style="color:#CFE0D6;">Manage preferences</a></p></td></tr>"""


def usp_strip(color=DG, dot=GOLD, bg=CREAM):
    sep = f'<span style="color:{dot};">&nbsp;&nbsp;·&nbsp;&nbsp;</span>'
    return (f'<tr><td class="px" align="center" style="background:{bg};padding:14px 32px;font:600 12px/20px {SANS};'
            f'letter-spacing:.03em;color:{color};">{sep.join(C["usp"])}</td></tr>')


def trust(align="center"):
    return (f'<p style="margin:0;font:14px/20px {SANS};color:{INK};text-align:{align};">'
            f'<strong style="font-weight:600;">Trustpilot</strong> &nbsp;Rated Excellent {confirm("live rating")}</p>')


# ---------- Option A: Clubhouse (closest to the live email) ----------
def option_a(img, wf=True):
    grid = ""
    for i in range(0, 4, 2):
        cells = ""
        for label, text, note in C["items"][i:i + 2]:
            extra = " " + confirm(note) if note or label == "Paying for it" else ""
            if label == "Right model?":
                text += f' <a href="#" style="color:{G};font-weight:600;">{C["reviews"]}</a> {confirm("URL")}'
            cells += (f'<td class="stack" width="50%" style="padding:18px 20px;vertical-align:top;">'
                      f'<p style="margin:0 0 6px;font:600 11px/16px {SANS};letter-spacing:.12em;text-transform:uppercase;color:{G};">{label}</p>'
                      f'<p style="margin:0;font:15px/22px {SANS};color:{INK};">{text}{extra}</p></td>')
        grid += f"<tr>{cells}</tr>"
    body = f"""
<tr><td align="center" bgcolor="{DG}" style="background:{DG};padding:22px 24px;">
<img src="{img['logo']}" width="200" alt="Evolution Golf" style="width:200px;height:auto;margin:0 auto;"></td></tr>
<tr><td style="height:3px;background:{GOLD};font-size:0;line-height:0;">&nbsp;</td></tr>
<tr><td class="px" align="center" style="padding:44px 48px 8px;">
<h1 class="h1" style="margin:0 0 14px;font:600 32px/38px {SERIF};color:{DG};">{C['headline']}</h1>
<p style="margin:0;font:17px/26px {SANS};color:{INK};">{C['intro']}</p></td></tr>
<tr><td class="px" style="padding:24px 48px 0;">{product_row(img)}</td></tr>
<tr><td class="px" style="padding:20px 48px 40px;">{button(C['cta'])}</td></tr>
<tr><td class="px" style="padding:0 48px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td style="border-top:1px solid {LINE};padding:30px 0 6px;" align="center">
<p style="margin:0;font:500 20px/28px {SERIF};color:{DG};">{C['lead']}</p></td></tr></table></td></tr>
<tr><td class="px" style="padding:12px 40px 36px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{CREAM};">{grid}</table></td></tr>
<tr><td class="px" style="padding:0 48px 32px;">{trust()}</td></tr>
{usp_strip()}
{footer_dark(img)}"""
    return shell(body, CREAM, img, wf)


# ---------- Option B: On the course (image-led, left-aligned) ----------
def option_b(img, wf=True):
    rows = ""
    for label, text, note in C["items"]:
        extra = " " + confirm(note) if note or label == "Paying for it" else ""
        if label == "Right model?":
            text += f'<br><a href="#" style="color:{G};font-weight:600;">{C["reviews"]} →</a> {confirm("URL")}'
        rows += (f'<tr><td class="stack" width="150" style="padding:16px 16px 6px 0;border-top:1px solid {LINE};vertical-align:top;'
                 f'font:500 17px/24px {SERIF};color:{DG};">{label}</td>'
                 f'<td class="stack nb" style="padding:16px 0;border-top:1px solid {LINE};vertical-align:top;font:15px/23px {SANS};color:{INK};">{text}{extra}</td></tr>')
    t, q, p = C["product"]
    body = f"""
<tr><td bgcolor="{DG}" style="background:{DG};padding:18px 32px;">
<img src="{img['logo']}" width="170" alt="Evolution Golf" style="width:170px;height:auto;"></td></tr>
<tr><td style="padding:0;"><img class="full" src="{img['life1']}" width="600" alt="Golfer walking with a Motocaddy electric trolley"
 style="width:600px;height:auto;"></td></tr>
<tr><td class="px" style="padding:36px 44px 0;">
<p style="margin:0 0 10px;font:600 11px/16px {SANS};letter-spacing:.14em;text-transform:uppercase;color:{GOLD};">Your basket is saved</p>
<h1 class="h1" style="margin:0 0 12px;font:600 34px/40px {SERIF};color:{DG};">{C['headline']}</h1>
<p style="margin:0;font:17px/26px {SANS};color:{INK};">{C['intro']}</p></td></tr>
<tr><td class="px" style="padding:26px 44px 0;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid {LINE};">
<tr><td align="center" style="padding:20px 20px 4px;"><img src="{img['product']}" width="220" alt="{t}" style="width:220px;height:auto;margin:0 auto;"></td></tr>
<tr><td align="center" style="padding:6px 24px 22px;font:15px/22px {SANS};color:{INK};"><strong style="font-weight:600;">{t}</strong><br>
<span style="color:{MUTED};">Qty {q} · </span><strong style="font-weight:600;">{p}</strong></td></tr></table></td></tr>
<tr><td class="px" style="padding:20px 44px 36px;">{button(C['cta'], radius=0)}</td></tr>
<tr><td class="px" style="padding:0 44px 8px;"><p style="margin:0 0 6px;font:500 20px/28px {SERIF};color:{DG};">{C['lead']}</p></td></tr>
<tr><td class="px" style="padding:0 44px 28px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table></td></tr>
<tr><td class="px" style="padding:0 44px 32px;">{trust('left')}</td></tr>
{usp_strip()}
{footer_dark(img)}"""
    return shell(body, CREAM, img, wf)


# ---------- Option C: Letter (plain, personal) ----------
def option_c(img, wf=True):
    lis = ""
    for label, text, note in C["items"]:
        extra = " " + confirm(note) if note or label == "Paying for it" else ""
        if label == "Right model?":
            text += f' <a href="#" style="color:{G};">{C["reviews"]}</a> {confirm("URL")}'
        lis += (f'<tr><td width="18" style="vertical-align:top;padding:4px 0 10px;font:15px/24px {SANS};color:{GOLD};">—</td>'
                f'<td style="padding:4px 0 10px;font:16px/24px {SANS};color:{INK};"><strong style="font-weight:600;">{label}</strong> {text}{extra}</td></tr>')
    body = f"""
<tr><td bgcolor="{DG}" style="background:{DG};padding:14px 40px;">
<table role="presentation" cellpadding="0" cellspacing="0"><tr>
<td style="vertical-align:middle;"><img src="{img['roundel']}" width="36" height="36" alt="Evolution Golf" style="width:36px;height:36px;"></td>
<td style="vertical-align:middle;padding-left:12px;font:600 12px/16px {SANS};letter-spacing:.16em;color:{WHITE};">EVOLUTION <span style="color:{GOLD};">GOLF</span></td></tr></table></td></tr>
<tr><td class="px" style="padding:40px 56px 0;">
<h1 class="h1" style="margin:0 0 18px;font:500 28px/34px {SERIF};color:{DG};">{C['headline']}</h1>
<p style="margin:0 0 20px;font:17px/27px {SANS};color:{INK};">{C['intro']}</p>
{product_row(img, pad='12px', bg=WHITE).replace('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#FFFFFF;">', f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid {LINE};border-bottom:1px solid {LINE};">')}
<p style="margin:26px 0 12px;font:17px/27px {SANS};color:{INK};">{C['lead']}</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{lis}</table></td></tr>
<tr><td class="px" style="padding:18px 56px 40px;">{button(C['cta'], bg=DG, full=False, radius=2)}</td></tr>
<tr><td class="px" style="padding:0 56px 36px;">{trust('left')}</td></tr>
<tr><td class="px" style="background:{CREAM};padding:24px 56px 28px;font:12px/19px {SANS};color:{MUTED};">
{C['address']}<br>You're receiving this because you started a checkout at evolutiongolf.co.uk.<br>
<a href="#" style="color:{MUTED};">Unsubscribe</a> · <a href="#" style="color:{MUTED};">Manage preferences</a></td></tr>"""
    return shell(body, CREAM, img, wf)


OPTIONS = [
    ("a", "Clubhouse", option_a,
     "Your live email, tightened. Dark green header with the logo and a gold rule, centred headline, "
     "basket, one full-width button, then the four answers in a 2×2 panel.",
     ["Closest to what customers already know", "The four answers read at a glance", "Works with no photography"],
     ["Centred layout is the most familiar look in the category"]),
    ("b", "On the course", option_b,
     "Image-led. A lifestyle photo under a slim header, left-aligned headline with a gold eyebrow, "
     "a large product card, and the four answers as a ruled list.",
     ["Feels most premium and editorial", "Photography carries the brand across every flow"],
     ["Needs good lifestyle photos, sized 1200px wide", "Longer scroll before the button on phones"]),
    ("c", "Letter", option_c,
     "Plain and personal. A slim header with the roundel, a letter-style body, the basket as a single row, "
     "and a smaller button. Closest in feel to Alex's E3.",
     ["Reads like a note from a shop, not a campaign", "Most robust in Gmail and Outlook"],
     ["Less visual punch for hardware", "Relies on the words doing the work"]),
]


def build():
    live_img = LIVE
    prev_img = {k: data_uri(v) for k, v in PREVIEW.items()}
    frames = {}
    for key, name, fn, *_ in OPTIONS:
        (OUT / f"option-{key}-{name.lower().replace(' ', '-')}-e1.html").write_text(fn(live_img))
        frames[key] = {"web": fn(prev_img, True), "gmail": fn(prev_img, False)}
    tpl = (OUT / "preview_template.html").read_text()
    meta = [{"key": k, "name": n, "summary": s, "pros": p, "cons": c} for k, n, _, s, p, c in OPTIONS]
    page = tpl.replace("/*__DATA__*/null", json.dumps({"options": meta, "frames": frames}))
    (OUT / "preview.html").write_text(page)
    print("preview.html", len(page) // 1024, "KB")


if __name__ == "__main__":
    build()

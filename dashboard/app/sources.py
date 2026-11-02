"""Finding and making images for emails: stock search (Unsplash, Openverse), AI scene images, background removal and
upscaling (Fal), brand crops (Pillow) and alt-text suggestions (Claude).

Every image is "staged" first: a working copy on the app's volume with where it came from and its licence. When it's ready
it's downloaded as an email-ready JPG, uploaded to Shopify Files (Shopify admin, Content, Files; Evoflows will add an upload
route later) and its Shopify link is attached, which adds it to the library with its licence kept.

Rules (Layton's, 16 Oct): AI images are scenes only. No products we sell, no brands, no people endorsing anything, no text on
the image. Every AI image is labelled as AI-generated in the library. Stock images keep their licence and credit.
"""
import base64
import datetime as dt
import io
import json
import os
import re
import secrets
import time

import httpx

from . import config, evoflows

UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
FAL_KEY = os.getenv("FAL_KEY", "")
FAL_IMAGE_MODEL = os.getenv("FAL_IMAGE_MODEL", "fal-ai/flux-pro/v1.1")
FAL_BG_MODEL = os.getenv("FAL_BG_MODEL", "fal-ai/birefnet")
FAL_UPSCALE_MODEL = os.getenv("FAL_UPSCALE_MODEL", "fal-ai/esrgan")
STAGE = config.DATA_DIR / "media" / "staged"
UA = {"User-Agent": "EvolutionGolfFlows/1.0 (+https://evolutiongolf.co.uk)"}

# crop presets: name -> (label, width, height); None height = keep the shape, 1200 wide at most
CROPS = {"hero": ("Full-width photo, 1200 × 720", 1200, 720), "banner": ("Wide banner, 1200 × 600", 1200, 600),
         "square": ("Square, 1200 × 1200 (shows at 600)", 1200, 1200), "original": ("Keep the shape, 1200 wide", 1200, None)}
FOCUS = {"top": (0.5, 0.2), "centre": (0.5, 0.5), "bottom": (0.5, 0.8), "left": (0.25, 0.5), "right": (0.75, 0.5)}

# AI prompts: scenes only (no products we sell, brands, endorsements or text)
BLOCKED = re.compile(r"\b(trolley|trolleys|caddy|caddie|motocaddy|powakaddy|stewart|clubs?|driver|drivers|irons?|putters?|wedges?|"
                     r"hybrids?|fairway woods?|rangefinders?|gps|shoes?|footwear|bag|bags|golf balls?|balls?|ping|callaway|titleist|taylormade|"
                     r"cobra|mizuno|srixon|cleveland|footjoy|ecco|adidas|nike|puma|under armour|bushnell|garmin|logo|logos|brand|"
                     r"text|words|lettering|sign|signs|review|testimonial|holding|endors\w*|recommend\w*|smiling at (the )?camera|"
                     r"celebrity|famous|tiger woods|rory|mcilroy|scheffler)\b", re.I)
STYLE = ("Editorial landscape photograph, natural light, realistic, calm and understated, muted natural colours, "
         "no text, no logos, no brand names, no golf equipment in close-up, no people facing the camera.")
ASPECTS = {"hero": {"width": 1440, "height": 864}, "banner": {"width": 1440, "height": 720}, "square": {"width": 1024, "height": 1024}}


class SourceError(ValueError):
    pass


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def enabled():
    return {"unsplash": bool(UNSPLASH_KEY), "openverse": True, "ai": bool(FAL_KEY), "alt": bool(config.ANTHROPIC_API_KEY),
            "crops": [{"key": k, "label": v[0]} for k, v in CROPS.items()], "focus": list(FOCUS)}


# ---------------- search ----------------
def search(source, q, page=1):
    q = re.sub(r"\s+", " ", str(q or "")).strip()[:100]
    if not q:
        raise SourceError("Type what you're looking for.")
    page = max(1, min(int(page or 1), 20))
    if source == "unsplash":
        if not UNSPLASH_KEY:
            raise SourceError("Unsplash isn't connected: add UNSPLASH_ACCESS_KEY in Railway.")
        r = httpx.get("https://api.unsplash.com/search/photos", params={"query": q, "per_page": 24, "page": page, "content_filter": "high"},
                      headers={"Authorization": f"Client-ID {UNSPLASH_KEY}", "Accept-Version": "v1", **UA}, timeout=20)
        if r.status_code == 403:
            raise SourceError("Unsplash's hourly limit is used up (50 searches an hour until the app is approved for production). Try Openverse.")
        r.raise_for_status()
        return [{"source": "unsplash", "id": x["id"], "thumb": x["urls"]["small"], "w": x["width"], "h": x["height"],
                 "alt": x.get("alt_description") or "", "credit": f"Photo by {x['user']['name']} on Unsplash",
                 "credit_url": f"{x['user']['links']['html']}?utm_source=evolution_golf_flows&utm_medium=referral",
                 "page": x["links"]["html"], "licence": "Unsplash License", "licence_url": "https://unsplash.com/license",
                 "needs_credit": False} for x in r.json().get("results", [])]
    if source == "openverse":
        r = httpx.get("https://api.openverse.org/v1/images/", params={"q": q, "page_size": 24, "page": page, "license_type": "commercial,modification",
                                                                      "mature": "false"}, headers=UA, timeout=20)
        r.raise_for_status()
        out = []
        for x in r.json().get("results", []):
            lic = (x.get("license") or "").lower()
            out.append({"source": "openverse", "id": x["id"], "thumb": x.get("thumbnail") or x["url"], "w": x.get("width"), "h": x.get("height"),
                        "alt": x.get("title") or "", "credit": x.get("attribution") or f"{x.get('title')} by {x.get('creator')}",
                        "credit_url": x.get("creator_url") or x.get("foreign_landing_url"), "page": x.get("foreign_landing_url"),
                        "licence": f"CC {lic.upper()} {x.get('license_version') or ''}".strip() if lic not in ("cc0", "pdm") else
                        ("CC0 (no rights reserved)" if lic == "cc0" else "Public domain"),
                        "licence_url": x.get("license_url"), "needs_credit": lic not in ("cc0", "pdm")})
        return out
    raise SourceError("Unknown image source.")


# ---------------- staging ----------------
def _dir(sid):
    if not re.fullmatch(r"[a-z0-9]{12}", sid or ""):
        raise SourceError("Unknown image.")
    return STAGE / sid


def _meta(sid):
    try:
        return json.loads((_dir(sid) / "meta.json").read_text())
    except FileNotFoundError:
        raise SourceError("That image has gone; find it again.")


def _write(sid, meta, data=None):
    d = _dir(sid)
    d.mkdir(parents=True, exist_ok=True)
    if data is not None:
        (d / "image").write_bytes(data)
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))


def _fetch(url, limit=25_000_000):
    if not url.startswith("https://"):
        raise SourceError("Only https images can be fetched.")
    with httpx.stream("GET", url, headers=UA, timeout=60, follow_redirects=True) as r:
        r.raise_for_status()
        buf = bytearray()
        for chunk in r.iter_bytes():
            buf += chunk
            if len(buf) > limit:
                raise SourceError("That image is too big to work with (over 25 MB).")
    return bytes(buf)


def _info(data):
    from PIL import Image
    im = Image.open(io.BytesIO(data))
    return {"width": im.size[0], "height": im.size[1], "format": im.format}


def _new(meta, data, who):
    sid = secrets.token_hex(6)
    meta = {**meta, "sid": sid, "by": who, "at": _now(), "steps": meta.get("steps", []), **_info(data)}
    _write(sid, meta, data)
    return public(meta)


def public(m):
    return {k: m.get(k) for k in ("sid", "source", "title", "credit", "credit_url", "page", "licence", "licence_url", "needs_credit",
                                  "ai", "prompt", "by", "at", "width", "height", "steps", "alt", "crop", "ready", "attached", "parent")}


def stage(source, item_id, who):
    """Bring a search result in as a working copy, keeping its licence."""
    item_id = str(item_id)
    if source == "unsplash":
        if not UNSPLASH_KEY or not re.fullmatch(r"[\w-]{5,40}", item_id):
            raise SourceError("Unsplash isn't connected, or that photo id is wrong.")
        h = {"Authorization": f"Client-ID {UNSPLASH_KEY}", "Accept-Version": "v1", **UA}
        x = httpx.get(f"https://api.unsplash.com/photos/{item_id}", headers=h, timeout=20)
        x.raise_for_status()
        x = x.json()
        httpx.get(x["links"]["download_location"], headers=h, timeout=20)  # Unsplash's rule: count a download when a photo is used
        data = _fetch(x["urls"]["raw"] + "&w=2400&fm=jpg&q=85")
        meta = {"source": "unsplash", "title": x.get("alt_description") or "Unsplash photo", "alt": x.get("alt_description") or "",
                "credit": f"Photo by {x['user']['name']} on Unsplash", "credit_url": x["user"]["links"]["html"], "page": x["links"]["html"],
                "licence": "Unsplash License", "licence_url": "https://unsplash.com/license", "needs_credit": False, "ai": False}
    elif source == "openverse":
        if not re.fullmatch(r"[0-9a-f-]{36}", item_id):
            raise SourceError("That Openverse id is wrong.")
        x = httpx.get(f"https://api.openverse.org/v1/images/{item_id}/", headers=UA, timeout=20)
        x.raise_for_status()
        x = x.json()
        lic = (x.get("license") or "").lower()
        data = _fetch(x["url"])
        meta = {"source": "openverse", "title": x.get("title") or "Openverse image", "alt": "",
                "credit": x.get("attribution") or f"{x.get('title')} by {x.get('creator')}", "credit_url": x.get("creator_url"),
                "page": x.get("foreign_landing_url"), "licence": f"CC {lic.upper()} {x.get('license_version') or ''}".strip(),
                "licence_url": x.get("license_url"), "needs_credit": lic not in ("cc0", "pdm"), "ai": False}
    else:
        raise SourceError("Unknown image source.")
    m = _new(meta, data, who)
    evoflows._log({"at": _now(), "by": who, "push": f"image: took {source} {item_id} ({meta['licence']})", "status": 200})
    return m


def staged():
    out = []
    if STAGE.exists():
        for d in STAGE.iterdir():
            try:
                m = json.loads((d / "meta.json").read_text())
            except Exception:
                continue
            if not m.get("attached") and not m.get("hidden"):
                out.append(public(m))
    return sorted(out, key=lambda m: m["at"], reverse=True)[:60]


def image_bytes(sid):
    f = _dir(sid) / "image"
    if not f.exists():
        raise SourceError("That image has gone; find it again.")
    return f.read_bytes()


def hide(sid, who):
    m = _meta(sid)
    m.update(hidden=True, hidden_by=who)
    _write(sid, m)
    return {"ok": True}


# ---------------- AI (Fal) ----------------
def _fal(model, payload):
    if not FAL_KEY:
        raise SourceError("AI images aren't connected: add FAL_KEY in Railway.")
    r = httpx.post(f"https://fal.run/{model}", json=payload, headers={"Authorization": f"Key {FAL_KEY}", **UA}, timeout=180)
    if r.status_code >= 400:
        raise SourceError(f"The AI service refused it ({r.status_code}): {r.text[:200]}")
    res = r.json()
    img = (res.get("images") or [None])[0] or res.get("image")
    if not img or not img.get("url"):
        raise SourceError("The AI service returned no image.")
    if res.get("has_nsfw_concepts") and any(res["has_nsfw_concepts"]):
        raise SourceError("The AI service flagged that image; try a different description.")
    url = img["url"]
    if url.startswith("data:"):
        return base64.b64decode(url.split(",", 1)[1])
    return _fetch(url)


def check_prompt(prompt):
    p = re.sub(r"\s+", " ", str(prompt or "")).strip()[:500]
    if len(p) < 8:
        raise SourceError("Describe the scene in a few words, e.g. 'a quiet fairway at sunrise with mist over the trees'.")
    m = BLOCKED.search(p)
    if m:
        raise SourceError(f"AI images are for scenes only: no products we sell, brands, people endorsing anything, or text "
                          f"(found “{m.group(0)}”). Use a real product photo for products.")
    return p


def generate(prompt, aspect, who):
    p = check_prompt(prompt)
    size = ASPECTS.get(aspect, ASPECTS["hero"])
    data = _fal(FAL_IMAGE_MODEL, {"prompt": f"{p}. {STYLE}", "image_size": size, "num_images": 1, "output_format": "jpeg",
                                  "safety_tolerance": "2", "enable_safety_checker": True})
    m = _new({"source": "ai", "title": p[:80], "alt": "", "prompt": p, "model": FAL_IMAGE_MODEL, "ai": True,
              "credit": "AI-generated (Fal)", "licence": "Generated for Evolution Golf", "needs_credit": False}, data, who)
    evoflows._log({"at": _now(), "by": who, "push": f"image: AI scene generated ({FAL_IMAGE_MODEL}): {p[:80]}", "status": 200})
    return m


def _data_uri(data):
    from PIL import Image
    im = Image.open(io.BytesIO(data))
    mime = "image/png" if im.format == "PNG" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(data).decode()


def _flatten_white(data):
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bg.paste(im, mask=im.split()[3])
    buf = io.BytesIO()
    bg.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def edit(sid, op, who, crop=None, focus="centre"):
    """A new working copy from an earlier one: remove_bg (onto pure white), upscale, or crop to a brand size."""
    m = _meta(sid)
    data = image_bytes(sid)
    if op == "remove_bg":
        out = _flatten_white(_fal(FAL_BG_MODEL, {"image_url": _data_uri(data)}))
        step = "background removed, placed on pure white"
    elif op == "upscale":
        if max(m.get("width") or 0, m.get("height") or 0) >= 2400:
            raise SourceError("It's already big enough for email.")
        out = _fal(FAL_UPSCALE_MODEL, {"image_url": _data_uri(data), "scale": 2})
        step = "upscaled ×2"
    elif op == "crop":
        out = crop_bytes(data, crop, focus)
        step = f"cropped: {CROPS[crop][0]}, focus {focus}"
    else:
        raise SourceError("Unknown edit.")
    meta = {k: v for k, v in m.items() if k not in ("sid", "by", "at", "width", "height", "format", "ready", "attached")}
    meta.update(parent=sid, steps=(m.get("steps") or []) + [step], crop=crop if op == "crop" else None, ready=op == "crop")
    res = _new(meta, out, who)
    evoflows._log({"at": _now(), "by": who, "push": f"image: {step} ({sid} -> {res['sid']})", "status": 200})
    return res


def crop_bytes(data, crop, focus="centre"):
    """Brand crop + email weight: JPG, 1200 wide, as light as it can be while staying sharp."""
    from PIL import Image, ImageOps
    if crop not in CROPS:
        raise SourceError("Pick a size.")
    im = Image.open(io.BytesIO(data))
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = Image.open(io.BytesIO(_flatten_white(data)))
    im = im.convert("RGB")
    _, w, h = CROPS[crop]
    if h is None:
        w = min(w, im.size[0])
        im = im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS)
    else:
        if im.size[0] < w * 0.6:
            raise SourceError(f"Too small for that size ({im.size[0]} px wide). Upscale it first.")
        im = ImageOps.fit(im, (w, h), Image.LANCZOS, centering=FOCUS.get(focus, FOCUS["centre"]))
    for q in (84, 78, 72, 66):
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
        if buf.tell() <= 250_000:
            break
    return buf.getvalue()


# ---------------- alt text (Claude) ----------------
def suggest_alt(sid):
    if not config.ANTHROPIC_API_KEY:
        raise SourceError("Alt-text suggestions need ANTHROPIC_API_KEY in Railway.")
    import anthropic
    from PIL import Image
    im = Image.open(io.BytesIO(image_bytes(sid))).convert("RGB")
    im.thumbnail((1024, 1024))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80)
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    r = client.messages.create(model=config.REVIEW_MODEL, max_tokens=200, messages=[{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(buf.getvalue()).decode()}},
        {"type": "text", "text": "Write alt text for this image in a UK golf retailer's marketing email. One plain sentence, under 120 "
                                 "characters, UK English, describing only what is visible. Don't start with 'Image of' or 'Photo of', "
                                 "don't name brands you can't read, and don't add claims. Reply with the alt text only."}]}])
    alt = "".join(b.text for b in r.content if getattr(b, "type", "") == "text").strip().strip('"')[:250]
    m = _meta(sid)
    m["alt"] = alt
    _write(sid, m)
    return {"alt": alt}


# ---------------- attach to the library ----------------
def download_name(sid):
    m = _meta(sid)
    slug = re.sub(r"[^a-z0-9]+", "-", (m.get("title") or "image").lower()).strip("-")[:40] or "image"
    return f"eg-email-{'ai-' if m.get('ai') else ''}{slug}-{sid[:4]}.jpg"


def attach(sid, url, alt, kind, who):
    """The image is in Shopify Files now: add it to the library, keeping where it came from and its licence."""
    from . import media
    m = _meta(sid)
    if not m.get("ready"):
        raise SourceError("Crop it to an email size first (that also makes the email-ready file).")
    res = media.add_url(url, alt, kind, who, extra={"source": m["source"], "credit": m.get("credit"), "credit_url": m.get("credit_url"),
                                                    "licence": m.get("licence"), "licence_url": m.get("licence_url"),
                                                    "needs_credit": m.get("needs_credit"), "ai": bool(m.get("ai")), "prompt": m.get("prompt"),
                                                    "staged": sid, "steps": m.get("steps")})
    if res.get("uploaded"):
        m.update(attached=url, attached_by=who, attached_at=_now())
        _write(sid, m)
    return res

"""Brand and media library: the brand rules, every image our emails use (with where), and checked uploads to Shopify Files.

Uploads are checked before anything leaves the app: JPG or PNG, size, dimensions, alt text, and the white-background rule
(cut-outs with a transparent background are flattened onto pure white; a cut-out on a coloured background is refused).
Uploading needs SHOPIFY_STORE (xxx.myshopify.com) and SHOPIFY_ADMIN_TOKEN (Admin API, write_files) in Railway; without
them the checks still run and nothing is uploaded.
"""
import base64
import datetime as dt
import io
import json
import os
import re
import time

import httpx

from . import config, evoflows

STORE = config.DATA_DIR / "media.json"
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE", "")
SHOPIFY_TOKEN = os.getenv("SHOPIFY_ADMIN_TOKEN", "")
SHOPIFY_API = "2025-10"
IMG = re.compile(r"<img\b[^>]*>", re.I)
ATTR = lambda tag, a: (re.search(rf'\b{a}="([^"]*)"', tag) or [None, ""])[1]

BRAND = {
    "colours": [("Brand green", "#0F3B2A", "Header, footer, buttons, rules, links"), ("Eyebrow green", "#24563F", "Small capitals above headlines"),
                ("Headline ink", "#161816", "Headlines"), ("Body text", "#2E322F", "Paragraphs"), ("Muted", "#626862", "Small print"),
                ("Stone", "#F1F3F1", "The one tinted panel per email, never behind an image"), ("White", "#FFFFFF", "The email background, always")],
    "fonts": [("Fraunces 400", "Georgia", "Headlines"), ("Inter 400/500/600", "Arial", "Everything else")],
    "rules": ["One primary button per email.", "At most one stone panel per email.", "Corners 0–2px. No cream, beige, mint or gold.",
              "Benefits as tables, no icons in new emails.", "White email background. Any image with a white or transparent background "
              "(product shots, packshots, cut-outs) sits on pure white.", "Photos: JPG, 1200 px wide for a full-width image (shown at 600), "
              "under 250 KB where possible. No text on photos.", "Every image needs alt text describing it.",
              "Members' delivery line: “Free delivery over £10” (“Normally £50 for non-members”).",
              "No discount codes, no false urgency or deadlines (DMCC Act 2024), no invented reviews or figures."],
}


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _uploads():
    try:
        return json.loads(STORE.read_text())
    except Exception:
        return []


def catalog():
    """Every image in our Evoflows emails (repo builds + builder versions) and every upload, with where it's used."""
    from . import builder
    used = {}
    man = evoflows.manifest()
    for key in man["templates"]:
        htmls = [builder.live(key)["html"]]
        for h in htmls:
            for tag in IMG.findall(h):
                src = ATTR(tag, "src")
                if not src.startswith("http"):
                    continue
                e = used.setdefault(src, {"url": src, "name": src.split("/")[-1].split("?")[0], "alts": {}, "used_in": set(),
                                          "width": ATTR(tag, "width")})
                alt = ATTR(tag, "alt")
                if alt:
                    e["alts"][alt] = e["alts"].get(alt, 0) + 1
                e["used_in"].add(key)
    for u in _uploads():
        e = used.setdefault(u["url"], {"url": u["url"], "name": u["name"], "alts": {}, "used_in": set(), "width": u.get("width")})
        e["alts"][u.get("alt", "")] = 99
        e["uploaded"] = {k: u.get(k) for k in ("by", "at", "kind", "bytes", "width", "height")}
    out = []
    for e in used.values():
        alt = max(e["alts"], key=e["alts"].get) if e["alts"] else ""
        kind = "logo" if "logo" in e["name"] else "icon" if "icon" in e["name"] else "photo"
        out.append({"url": e["url"], "name": e["name"], "alt": alt, "kind": (e.get("uploaded") or {}).get("kind") or kind,
                    "used_in": sorted(e["used_in"]), "uploaded": e.get("uploaded")})
    order = {"logo": 0, "photo": 1, "cutout": 2, "icon": 3}
    return sorted(out, key=lambda x: (order.get(x["kind"], 4), -len(x["used_in"]), x["name"]))


def check(data, filename, alt, kind):
    """Run the brand checks; returns (errors, warnings, info, bytes_to_upload, mime)."""
    from PIL import Image
    errors, warnings = [], []
    if not alt.strip():
        errors.append("Add alt text: a short description of what the image shows.")
    if len(data) > 3_000_000:
        errors.append(f"{len(data) / 1e6:.1f} MB is too big for email: keep it under 1 MB (ideally under 250 KB).")
    elif len(data) > 400_000:
        warnings.append(f"{len(data) / 1e3:.0f} KB is heavy for email; under 250 KB loads faster.")
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception:
        return ["Not an image we can read. Use JPG or PNG."], warnings, {}, None, None
    fmt = (im.format or "").upper()
    if fmt not in ("JPEG", "PNG"):
        errors.append(f"{fmt or 'This format'} isn't safe in email (Outlook). Use JPG or PNG.")
    w, h = im.size
    info = {"width": w, "height": h, "format": fmt}
    if kind == "photo" and w < 1200:
        warnings.append(f"{w} px wide: full-width photos look soft below 1200 px (they show at 600 on retina screens).")
    out, mime = data, "image/jpeg" if fmt == "JPEG" else "image/png"
    has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
    if kind in ("cutout", "product"):
        rgba = im.convert("RGBA")
        corners = [rgba.getpixel(p) for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
        transparent = all(c[3] < 20 for c in corners)
        white = all(c[3] > 200 and min(c[:3]) >= 245 for c in corners)
        if transparent or has_alpha:
            bg = Image.new("RGB", rgba.size, (255, 255, 255))
            bg.paste(rgba, mask=rgba.split()[3])
            buf = io.BytesIO()
            bg.save(buf, "PNG", optimize=True)
            out, mime = buf.getvalue(), "image/png"
            warnings.append("Transparent background flattened onto pure white (brand rule).")
        elif not white:
            errors.append("Product shots and cut-outs must sit on pure white: this one's corners aren't white.")
    elif has_alpha and kind == "photo":
        warnings.append("This photo has transparency; it will show on white.")
    return errors, warnings, info, out, mime


def _gql(query, variables):
    r = httpx.post(f"https://{SHOPIFY_STORE}/admin/api/{SHOPIFY_API}/graphql.json", json={"query": query, "variables": variables},
                   headers={"X-Shopify-Access-Token": SHOPIFY_TOKEN}, timeout=60)
    r.raise_for_status()
    d = r.json()
    if d.get("errors"):
        raise RuntimeError(str(d["errors"])[:300])
    return d["data"]


def upload(name, data_b64, alt, kind, who):
    data = base64.b64decode(data_b64.split(",")[-1])
    errors, warnings, info, out, mime = check(data, name, alt, kind)
    result = {"errors": errors, "warnings": warnings, "info": info, "uploaded": False}
    if errors:
        return result
    if not (SHOPIFY_STORE and SHOPIFY_TOKEN):
        result["errors"] = ["Checks passed, but the app can't upload yet: add SHOPIFY_STORE and SHOPIFY_ADMIN_TOKEN (write_files) in Railway Variables."]
        return result
    base = re.sub(r"[^a-z0-9-]+", "-", os.path.splitext(name)[0].lower()).strip("-")[:60] or "image"
    fname = f"eg-email-{base}.{'jpg' if mime == 'image/jpeg' else 'png'}"
    st = _gql("""mutation($input:[StagedUploadInput!]!){stagedUploadsCreate(input:$input){stagedTargets{url resourceUrl parameters{name value}} userErrors{message}}}""",
              {"input": [{"filename": fname, "mimeType": mime, "httpMethod": "POST", "resource": "FILE", "fileSize": str(len(out))}]})
    tgt = st["stagedUploadsCreate"]["stagedTargets"][0]
    httpx.post(tgt["url"], data={p["name"]: p["value"] for p in tgt["parameters"]}, files={"file": (fname, out, mime)}, timeout=120).raise_for_status()
    fc = _gql("""mutation($files:[FileCreateInput!]!){fileCreate(files:$files){files{id} userErrors{message}}}""",
              {"files": [{"originalSource": tgt["resourceUrl"], "contentType": "IMAGE", "alt": alt, "filename": fname}]})
    errs = fc["fileCreate"]["userErrors"]
    if errs:
        result["errors"] = [e["message"] for e in errs]
        return result
    fid, url = fc["fileCreate"]["files"][0]["id"], None
    for _ in range(20):
        n = _gql("""query($id:ID!){node(id:$id){... on MediaImage{fileStatus image{url}}}}""", {"id": fid})["node"]
        if n and n.get("fileStatus") == "READY" and n.get("image"):
            url = n["image"]["url"]
            break
        time.sleep(1.5)
    if not url:
        result["errors"] = ["Uploaded to Shopify, but it's still processing. Refresh the library in a minute."]
        return result
    rec = _uploads()
    rec.append({"url": url, "name": fname, "alt": alt, "kind": kind, "by": who, "at": _now(), "bytes": len(out), **info})
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
    evoflows._log({"at": _now(), "by": who, "push": f"upload image {fname}", "status": 200})
    result.update(uploaded=True, url=url, name=fname)
    return result


def known_urls():
    return {x["url"] for x in catalog()}

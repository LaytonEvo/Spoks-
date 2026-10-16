"""Evolution Golf flow dashboard: our flows on Evoflows (the new engine), the Klaviyo flows they're replacing, reviews."""
import datetime as dt
from contextlib import asynccontextmanager
import json
import re
import secrets
import threading
import time

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

from . import abtest, builder, config, design, media, digest, drafts, evoflows, evosnap, fixes, review, snapshot

security = HTTPBasic(auto_error=False)
STATIC = config.BASE_DIR / "app" / "static"
NOTES = config.DATA_DIR / "notes"
ID_RE = re.compile(r"^[A-Za-z0-9_]{4,40}$")  # Klaviyo ids (6 chars) and Evoflows keys (f3_checkout, f9_e1h)
FIX_RE = re.compile(r"^[A-Za-z0-9-]{4,80}$")


def auth(credentials: HTTPBasicCredentials | None = Depends(security)):
    users = dict(config.DASHBOARD_USERS)
    if config.DASHBOARD_PASSWORD:
        users.setdefault(config.DASHBOARD_USER, config.DASHBOARD_PASSWORD)
    if not users:
        return "local"
    ok = False
    if credentials:
        for name, pw in users.items():
            if secrets.compare_digest(credentials.username, name) and secrets.compare_digest(credentials.password, pw):
                ok = True
    if not ok:
        raise HTTPException(401, "Login required", headers={"WWW-Authenticate": 'Basic realm="Evolution Golf"'})
    return credentials.username


def _check_id(value):
    if not ID_RE.match(value):
        raise HTTPException(404)
    return value


def _refresh_in_background():
    if not snapshot.status["running"]:
        threading.Thread(target=snapshot.build, daemon=True).start()
    if not evosnap.status["running"]:
        threading.Thread(target=evosnap.build, daemon=True).start()


def _auto_refresh():
    """Build on start if there is no snapshot, then keep it no older than a day."""
    while True:
        snap = snapshot.load()
        age = None
        if snap:
            age = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(snap["generated_at"])
        source = "fixtures" if config.USE_FIXTURES else "klaviyo"
        stale = age and age > dt.timedelta(hours=24) and not config.USE_FIXTURES
        outdated = snap is not None and snap.get("schema", 1) < snapshot.SCHEMA  # built by an older version
        if snap is None or snap.get("source") != source or stale or outdated:
            snapshot.build()
        try:
            if digest.due():
                snap = snapshot.load()
                fresh = snap and dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(snap["generated_at"]) < dt.timedelta(hours=6)
                if not fresh and not config.USE_FIXTURES:
                    snapshot.build()
                digest.send(config.PUBLIC_URL)
        except Exception as e:  # never let the summary stop the refresh loop
            snapshot.log.warning("Monday summary not sent: %s", str(e)[:300])
        time.sleep(3600)


@asynccontextmanager
async def lifespan(_app):
    threading.Thread(target=_auto_refresh, daemon=True).start()
    threading.Thread(target=evosnap.loop, daemon=True).start()
    yield


app = FastAPI(title="Evolution Golf Flow Dashboard", docs_url=None, redoc_url=None, lifespan=lifespan)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
def index(user=Depends(auth)):
    """The page, with each script and stylesheet stamped with a hash of its contents, so a deploy is never hidden by an
    old copy in the browser's cache."""
    import hashlib
    html = (STATIC / "index.html").read_text()
    for name in ("app.css", "app.js", "pages.js", "sim.js", "simviz.js", "design.js", "builder.js", "media.js", "abtests.js"):
        v = hashlib.sha1((STATIC / name).read_bytes()).hexdigest()[:10]
        html = html.replace(f'"/static/{name}"', f'"/static/{name}?v={v}"')
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/api/status")
def api_status(user=Depends(auth)):
    snap = snapshot.load()
    evo = evosnap.load()
    return {**snapshot.status, "source": "fixtures" if config.USE_FIXTURES else "klaviyo",
            "generated_at": snap["generated_at"] if snap else None,
            "evoflows": {"enabled": evoflows.enabled(), **evosnap.status, "generated_at": evo["generated_at"] if evo else None,
                         "admin_url": config.EVOFLOWS_BASE.replace("/api/v1", "/admin")},
            "show_klaviyo": config.SHOW_KLAVIYO, "reviews_enabled": bool(config.ANTHROPIC_API_KEY), "slack_enabled": bool(config.SLACK_WEBHOOK_URL),
            "writes_enabled": bool(config.KLAVIYO_WRITE_KEY), "user": user}


@app.get("/api/snapshot")
def api_snapshot(user=Depends(auth)):
    snap = snapshot.merged()
    if not snap["flows"]:
        return JSONResponse({"flows": [], "timeframes": [], "generated_at": None})
    def strip(o):  # plain-text copies of emails are only for reviews
        if isinstance(o, dict):
            return {k: strip(v) for k, v in o.items() if k != "_text"}
        if isinstance(o, list):
            return [strip(v) for v in o]
        return o
    return JSONResponse(strip(snap))


@app.post("/api/refresh")
def api_refresh(user=Depends(auth)):
    _refresh_in_background()
    return snapshot.status


@app.get("/render/{message_id}", response_class=HTMLResponse)
def render(message_id: str, user=Depends(auth)):
    evo = evoflows.OUT / "previews" / f"{_check_id(message_id)}.html"
    if evo.exists() and builder.live(message_id).get("status") == "published":  # edited in the builder
        return HTMLResponse(builder.preview(message_id), headers={"Content-Security-Policy": "script-src 'none'"})
    if evo.exists():  # Evoflows templates: the approved build's preview (sample basket, the name "Sam")
        return HTMLResponse(snapshot.fill_tags(evo.read_text()), headers={"Content-Security-Policy": "script-src 'none'"})
    p = snapshot.RENDERS / f"{message_id}.html"
    if not p.exists():
        return HTMLResponse("<p style='font:14px system-ui;color:#555;padding:24px'>No preview yet. "
                            "It appears after the next refresh from Klaviyo.</p>")
    return HTMLResponse(p.read_text(), headers={"Content-Security-Policy": "script-src 'none'"})


def _find_flow(flow_id):
    snap = snapshot.merged()
    for f in snap["flows"]:
        if f["id"] == flow_id:
            return f
    raise HTTPException(404, "Flow not in the current snapshot")


@app.get("/api/reviews/{flow_id}")
def get_review(flow_id: str, user=Depends(auth)):
    return review.load(_check_id(flow_id)) or {}


@app.post("/api/reviews/{flow_id}")
def make_review(flow_id: str, tf: str = "last_90_days", user=Depends(auth)):
    flow = _find_flow(_check_id(flow_id))
    if tf not in config.TIMEFRAMES:
        raise HTTPException(400, "Unknown period")
    try:
        return review.generate(flow, tf)
    except Exception as e:
        raise HTTPException(502, str(e)[:400])


@app.get("/api/notes/{flow_id}")
def get_notes(flow_id: str, user=Depends(auth)):
    p = NOTES / f"{_check_id(flow_id)}.json"
    return json.loads(p.read_text()) if p.exists() else []


@app.post("/api/notes/{flow_id}")
async def add_note(flow_id: str, request: Request, user=Depends(auth)):
    body = await request.json()
    text = str(body.get("text", "")).strip()[:2000]
    author = str(body.get("author", "")).strip()[:60] or "Team"
    if not text:
        raise HTTPException(400, "Write a note first")
    NOTES.mkdir(parents=True, exist_ok=True)
    p = NOTES / f"{_check_id(flow_id)}.json"
    notes = json.loads(p.read_text()) if p.exists() else []
    notes.append({"author": author, "text": text, "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
    p.write_text(json.dumps(notes, ensure_ascii=False, indent=1))
    return notes


@app.get("/api/programme")
def api_programme(user=Depends(auth)):
    return JSONResponse(json.loads((config.BASE_DIR / "app" / "programme.json").read_text()))


@app.get("/api/summary")
def api_summary(user=Depends(auth)):
    s = digest.build()
    if not s:
        return {}
    s.pop("_flag_keys", None)
    s["slack_enabled"] = bool(config.SLACK_WEBHOOK_URL)
    s["last_sent"] = digest._load_state().get("sent_at")
    return s


@app.post("/api/summary/send")
def api_summary_send(user=Depends(auth)):
    try:
        digest.send(config.PUBLIC_URL)
    except Exception as e:
        raise HTTPException(400, str(e)[:300])
    return {"ok": True}


# ---------- fixes: recommend, approve, apply ----------
def _fix_id(fid):
    if not FIX_RE.match(fid):
        raise HTTPException(404)
    return fid


@app.get("/api/fixes")
def api_fixes(user=Depends(auth)):
    kc = fixes.key_check() if config.KLAVIYO_WRITE_KEY and not config.USE_FIXTURES else {}
    return {"fixes": [fixes.public(f) for f in fixes.load_all()], "scan": fixes.scan_status,
            "writes_enabled": bool(config.KLAVIYO_WRITE_KEY) and kc.get("ok", False), "key_check": kc}


@app.post("/api/fixes/check-keys")
def api_fixes_check_keys(user=Depends(auth)):
    return fixes.key_check(force=True)


@app.post("/api/fixes/scan")
def api_fixes_scan(user=Depends(auth)):
    fixes.start_scan()
    return fixes.scan_status


@app.post("/api/fixes/{fid}/{action}")
async def api_fix_action(fid: str, action: str, request: Request, user=Depends(auth)):
    fid = _fix_id(fid)
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    try:
        if action == "approve":
            f = fixes.apply(fid, user, body.get("replace"))
        elif action == "undo":
            f = fixes.revert(fid, user)
        elif action == "dismiss":
            f = fixes.dismiss(fid, user, str(body.get("note", "")))
        elif action == "done":
            f = fixes.done(fid, user)
        else:
            raise HTTPException(404)
    except HTTPException:
        raise
    except KeyError:
        raise HTTPException(404, "No such fix")
    except Exception as e:
        raise HTTPException(400, str(e)[:400])
    return fixes.public(f)


@app.get("/fixes/{fid}/preview", response_class=HTMLResponse)
def fix_preview(fid: str, which: str = "after", user=Depends(auth)):
    f = fixes.get(_fix_id(fid))
    if not f:
        raise HTTPException(404)
    html = f.get("after_preview" if which == "after" else "before_preview") or "<p>No preview.</p>"
    return HTMLResponse(snapshot.fill_tags(html), headers={"Content-Security-Policy": "script-src 'none'"})


# ---------- new draft flows: approve, then the app creates them in Klaviyo (switched off) ----------
PACK_RE = re.compile(r"^[a-z0-9-]{2,60}$")


def _pack_id(pid):
    if not PACK_RE.match(pid):
        raise HTTPException(404)
    return pid


@app.get("/api/drafts")
def api_drafts(user=Depends(auth)):
    return {"packs": drafts.all_public(), "writes_enabled": bool(config.KLAVIYO_WRITE_KEY) and not config.USE_FIXTURES}


@app.post("/api/drafts/{pid}/approve")
def api_draft_approve(pid: str, user=Depends(auth)):
    try:
        return drafts.approve(_pack_id(pid), user)
    except KeyError:
        raise HTTPException(404, "No such draft")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/drafts/{pid}/email/{key}", response_class=HTMLResponse)
def draft_email(pid: str, key: str, photos: int = 0, user=Depends(auth)):
    try:
        html = drafts.email_html(_pack_id(pid), _pack_id(key), photos=bool(photos))
    except (KeyError, FileNotFoundError):
        raise HTTPException(404)
    return HTMLResponse(snapshot.fill_tags(html), headers={"Content-Security-Policy": "script-src 'none'"})


# ---------- flow map (the same page as the shared artifact) ----------
@app.get("/flow-map", response_class=HTMLResponse)
def flow_map(user=Depends(auth)):
    body = (config.BASE_DIR / "app" / "flowmap.html").read_text()
    page = ('<!doctype html><html lang="en-GB"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script></head><body>'
            + body +
            '<script>window.mermaid && mermaid.initialize({startOnLoad: true, theme: matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "neutral"});</script>'
            '</body></html>')
    return HTMLResponse(page)


# ---------- Evoflows (the engine replacing Klaviyo flows) ----------
EVO_KEY = re.compile(r"^[a-z0-9_]{2,60}$")


def _evo(fn, *a, **k):
    try:
        return fn(*a, **k)
    except evoflows.EvoflowsError as e:
        raise HTTPException(502, str(e))


@app.get("/api/evoflows")
def api_evoflows(period: str = "30d", fresh: int = 0, user=Depends(auth)):
    if period not in ("30d", "90d", "365d"):
        raise HTTPException(400, "period")
    if not evoflows.enabled():
        return {"enabled": False}
    data = _evo(evoflows.overview, period, bool(fresh))
    return {"enabled": True, **data, "webhook": evoflows.webhook_info(), "events": evoflows.recent_events()[:20],
            "templates": evoflows.template_keys(),
            "log": evoflows.push_log()}


@app.get("/api/evoflows/runs")
def api_evoflows_runs(flow: str, status: str = "", user=Depends(auth)):
    if not EVO_KEY.match(flow) or status not in ("", "active", "done", "exited"):
        raise HTTPException(400, "flow")
    return _evo(evoflows.runs, flow, status)


@app.get("/api/evoflows/carts")
def api_evoflows_carts(user=Depends(auth)):
    return _evo(evoflows.carts)


@app.get("/api/evoflows/ping")
def api_evoflows_ping(user=Depends(auth)):
    status, res = _evo(evoflows.ping)
    return {"status": status, "response": res}


@app.post("/api/evoflows/push/{what}")
def api_evoflows_push(what: str, user=Depends(auth)):
    """Push the built flags / templates / flow (validate first). Never enables anything."""
    if what not in ("flags", "templates", "validate", "flow"):
        raise HTTPException(404)
    return {"results": _evo(evoflows.push, what, user)}


@app.post("/api/evoflows/webhook")
def api_evoflows_webhook(user=Depends(auth)):
    if not config.PUBLIC_URL:
        raise HTTPException(400, "PUBLIC_URL / RAILWAY_PUBLIC_DOMAIN not set")
    status, res = _evo(evoflows.register_webhook, f"{config.PUBLIC_URL}/evoflows/hook", user)
    return {"status": status, "response": res}


@app.post("/evoflows/hook")
async def evoflows_hook(request: Request):
    """Deliveries from Evoflows. No login (Evoflows can't send one): every body must carry a valid HMAC signature."""
    raw = await request.body()
    if not evoflows.verify(raw, request.headers.get("X-Evoflows-Signature", "")):
        raise HTTPException(401, "bad signature")
    try:
        evoflows.record_event(json.loads(raw))
    except ValueError:
        raise HTTPException(400, "not JSON")
    return {"ok": True}


@app.get("/evoflows/preview/{key}", response_class=HTMLResponse)
def evoflows_preview(key: str, user=Depends(auth)):
    if key not in evoflows.template_keys():
        raise HTTPException(404)
    status, res = _evo(evoflows.preview, key)
    html = (res or {}).get("html") if isinstance(res, dict) else None
    if status >= 400 or not html:
        return HTMLResponse(f"<pre>{status} {json.dumps(res)[:2000]}</pre>", status_code=502)
    return HTMLResponse(html, headers={"Content-Security-Policy": "script-src 'none'"})


@app.get("/api/evoflows/builds")
def api_evoflows_builds(user=Depends(auth)):
    """The approved builds (app/evoflows_out) with where each stands on the engine, for New flows to approve."""
    man = evoflows.manifest()
    evo = {f["id"]: f for f in (snapshot.merged()["flows"]) if f.get("platform") == "evoflows"}
    log = evoflows.push_log()
    out = []
    for key, meta in man["flows"].items():
        f = evo.get(key) or {}
        last = next((l for l in log if l.get("push") == f"approve {key}"), None)
        out.append({"key": key, **meta, "status": f.get("status", "unknown"), "version": f.get("version"),
                    "differs": f.get("differs", False), "trigger": f.get("trigger"), "flow_filter": f.get("flow_filter"),
                    "exit": f.get("exit"), "reentry_text": f.get("reentry_text"), "consent": f.get("consent"),
                    "steps": f.get("steps", []), "last_push": last})
    return {"enabled": evoflows.enabled(), "builds": out, "user": user}


@app.post("/api/evoflows/validate/{key}")
def api_evoflows_validate(key: str, user=Depends(auth)):
    if key not in evoflows.manifest()["flows"]:
        raise HTTPException(404)
    return _evo(evoflows.validate_flow, key)


@app.post("/api/evoflows/approve/{key}")
def api_evoflows_approve(key: str, user=Depends(auth)):
    """Approve a build: push its templates and flow to Evoflows, switched off. Never enables."""
    if key not in evoflows.manifest()["flows"]:
        raise HTTPException(404)
    res = _evo(evoflows.push_flow, key, user)
    threading.Thread(target=evosnap.build, daemon=True).start()
    return res


@app.post("/api/evoflows/test/{key}")
async def api_evoflows_test(key: str, request: Request, user=Depends(auth)):
    if key not in evoflows.template_keys():
        raise HTTPException(404)
    to = (await request.json()).get("to", "")
    status, res = _evo(evoflows.test_send, key, to, user)
    return {"status": status, "response": res}


# ---------- email builder (Evoflows templates): draft -> approve -> publish ----------
def _tpl_key(key):
    if not builder.is_template(key):
        raise HTTPException(404)
    return key


def _b(fn, *a):
    try:
        return fn(*a)
    except KeyError:
        raise HTTPException(404, "No such version")
    except ValueError as e:
        raise HTTPException(400, str(e))
    except evoflows.EvoflowsError as e:
        raise HTTPException(502, str(e))


@app.get("/api/builder/{key}")
def api_builder(key: str, user=Depends(auth)):
    return _b(builder.doc, _tpl_key(key))


@app.post("/api/builder/{key}/save")
async def api_builder_save(key: str, request: Request, user=Depends(auth)):
    return _b(builder.save, _tpl_key(key), await request.json(), user)


@app.post("/api/builder/{key}/approve/{n}")
def api_builder_approve(key: str, n: int, user=Depends(auth)):
    return _b(builder.approve, _tpl_key(key), n, user)


@app.post("/api/builder/{key}/publish/{n}")
def api_builder_publish(key: str, n: int, user=Depends(auth)):
    res = _b(builder.publish, _tpl_key(key), n, user)
    threading.Thread(target=evosnap.build, daemon=True).start()
    return res


@app.post("/api/builder/{key}/restore-build")
def api_builder_restore(key: str, user=Depends(auth)):
    res = _b(builder.restore_build, _tpl_key(key), user)
    threading.Thread(target=evosnap.build, daemon=True).start()
    return res


@app.post("/api/builder/{key}/test/{n}")
async def api_builder_test(key: str, n: int, request: Request, user=Depends(auth)):
    return _b(builder.test, _tpl_key(key), n, str((await request.json()).get("to", "")).strip(), user)


@app.post("/builder/{key}/preview", response_class=HTMLResponse)
async def builder_preview(key: str, request: Request, user=Depends(auth)):
    body = await request.json()
    _tpl_key(key)
    html = body.get("html")
    if html is not None:
        head, _, tail = builder.split(builder.live(key)["html_t"])
        html = head + html + tail
    out = _b(builder.preview, key, body.get("n"), body.get("audience", "non"), html, body.get("overrides"))
    return HTMLResponse(out, headers={"Content-Security-Policy": "script-src 'none'"})


# ---------- brand and media library ----------
@app.get("/api/media")
def api_media(user=Depends(auth)):
    return {"brand": media.BRAND, "images": media.catalog(), "can_upload": bool(media.SHOPIFY_STORE and media.SHOPIFY_TOKEN)}


@app.post("/api/media/upload")
async def api_media_upload(request: Request, user=Depends(auth)):
    body = await request.json()
    kind = body.get("kind") if body.get("kind") in ("photo", "cutout", "product", "icon", "logo") else "photo"
    try:
        return media.upload(str(body.get("name", "image"))[:120], body.get("data", ""), str(body.get("alt", ""))[:250], kind, user)
    except Exception as e:
        raise HTTPException(502, f"Upload failed: {str(e)[:300]}")


# ---------- A/B tests ----------
def _ab(fn, *a):
    try:
        return fn(*a)
    except KeyError:
        raise HTTPException(404, "No such test")
    except ValueError as e:
        raise HTTPException(400, str(e))
    except evoflows.EvoflowsError as e:
        raise HTTPException(502, str(e))


@app.get("/api/abtests")
def api_abtests(user=Depends(auth)):
    snap = {f["id"]: f for f in snapshot.merged()["flows"] if f.get("platform") == "evoflows"}
    tests = [{**t, "results": abtest.results(t, snap.get(t["flow"])) if t["status"] in ("running", "ended") else None} for t in abtest.all_tests()]
    flows = [{"key": k, "name": m["name"], "emails": abtest.candidates(k)} for k, m in evoflows.manifest()["flows"].items()]
    return {"tests": tests[::-1], "flows": flows, "splits": list(abtest.SPLITS)}


@app.post("/api/abtests")
async def api_abtest_create(request: Request, user=Depends(auth)):
    b = await request.json()
    return {"id": _ab(abtest.create, str(b.get("flow", "")), str(b.get("step", "")), str(b.get("share", "50")), user, str(b.get("name", ""))[:80])}


@app.post("/api/abtests/{tid}/{action}")
async def api_abtest_action(tid: str, action: str, request: Request, user=Depends(auth)):
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    if action == "approve":
        return _ab(abtest.approve, tid, user)
    if action == "start":
        res = _ab(abtest.start, tid, user)
    elif action == "end":
        res = _ab(abtest.end, tid, str(body.get("winner", "")), user)
    elif action == "cancel":
        return _ab(abtest.cancel, tid, user)
    else:
        raise HTTPException(404)
    threading.Thread(target=evosnap.build, daemon=True).start()
    return res


# ---------- brand theme (design system) ----------
@app.get("/api/design")
def api_design(user=Depends(auth)):
    d = design.theme_doc()
    br = design.brand()
    d["emails"] = [{"key": k, "name": builder.live(k)["name"], "overrides": builder.live(k).get("overrides") or {}} for k in builder.all_keys()]
    d["stacks"] = {"head": {k: v[1] for k, v in design.FONTS["head"].items()}, "body": {k: v[1] for k, v in design.FONTS["body"].items()},
                   "families": {k: v[0] for k, v in {**design.FONTS["head"], **design.FONTS["body"]}.items()}}
    return d


@app.post("/api/design/save")
async def api_design_save(request: Request, user=Depends(auth)):
    b = await request.json()
    return _b(design.save_theme, b.get("theme") or {}, user, str(b.get("note", "")))


@app.post("/api/design/check")
async def api_design_check(request: Request, user=Depends(auth)):
    return design.checks((await request.json()).get("theme") or {})


@app.post("/api/design/approve/{n}")
def api_design_approve(n: int, user=Depends(auth)):
    return _b(design.approve_theme, n, user)


@app.post("/api/design/publish/{n}")
def api_design_publish(n: int, user=Depends(auth)):
    res = _b(design.publish_theme, n, user)
    threading.Thread(target=evosnap.build, daemon=True).start()
    return res


@app.post("/design/preview", response_class=HTMLResponse)
async def design_preview(request: Request, user=Depends(auth)):
    b = await request.json()
    key = _tpl_key(str(b.get("key", "")))
    out = _b(builder.preview, key, None, b.get("audience", "non"), None, None, design.merge(design.DEFAULT, b.get("theme") or {}))
    return HTMLResponse(out, headers={"Content-Security-Policy": "script-src 'none'"})

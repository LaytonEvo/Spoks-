"""Evolution Golf flow dashboard: our flows on Evoflows (the new engine), the Klaviyo flows they're replacing, reviews."""
import datetime as dt
from contextlib import asynccontextmanager
import json
import re
import secrets
import threading
import time

import anthropic
import httpx

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

from . import abtest, agents, rollout, users, assistant, design_agent, builder, sources, config, design, media, digest, drafts, evoflows, evosnap, fixes, review, snapshot

security = HTTPBasic(auto_error=False)
STATIC = config.BASE_DIR / "app" / "static"
NOTES = config.DATA_DIR / "notes"
ID_RE = re.compile(r"^[A-Za-z0-9_]{4,40}$")  # Klaviyo ids (6 chars) and Evoflows keys (f3_checkout, f9_e1h)
FIX_RE = re.compile(r"^[A-Za-z0-9-]{4,80}$")


def auth(credentials: HTTPBasicCredentials | None = Depends(security)):
    if not users.any_users():
        return "local"
    name = users.check(credentials.username, credentials.password) if credentials else None
    if not name:
        raise HTTPException(401, "Login required", headers={"WWW-Authenticate": 'Basic realm="Evolution Golf"'})
    return name


def admin(user=Depends(auth)):
    if users.role(user) != "admin":
        raise HTTPException(403, "Only admins can manage the team.")
    return user


def review_auth(request: Request):
    """Claude Code's reviewer access (X-Review-Token). Read the agents' work, give verdicts, start QA, and turn a design roll-out
    Layton has approved into drafts (never publishes); nothing else."""
    tok = request.headers.get("x-review-token", "")
    if len(config.REVIEW_TOKEN) < 24 or not secrets.compare_digest(tok, config.REVIEW_TOKEN):
        raise HTTPException(404)
    return "Claude (reviewer)"


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
    threading.Thread(target=agents.loop, daemon=True).start()
    yield


app = FastAPI(title="Evolution Golf Flow Dashboard", docs_url=None, redoc_url=None, lifespan=lifespan)


@app.middleware("http")
async def role_gate(request: Request, call_next):
    """Every change request is checked against the signer-in's role (users.allowed). Reads are open to anyone signed in."""
    path = request.url.path
    if request.method not in ("GET", "HEAD", "OPTIONS") and not path.startswith(("/review/", "/invite/", "/evoflows/hook")):
        hdr = request.headers.get("authorization", "")
        if hdr.lower().startswith("basic ") and users.any_users():
            import base64
            try:
                name, _, pw = base64.b64decode(hdr[6:]).decode().partition(":")
            except Exception:
                name, pw = "", ""
            who = users.check(name, pw)
            if who and not users.allowed(users.role(who), request.method, path):
                r = users.role(who)
                return JSONResponse({"detail": f"Your role ({users.ROLES[r]}) can't do this. Ask an admin or approver."}, status_code=403)
    return await call_next(request)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
def index(user=Depends(auth)):
    """The page, with each script and stylesheet stamped with a hash of its contents, so a deploy is never hidden by an
    old copy in the browser's cache."""
    import hashlib
    html = (STATIC / "index.html").read_text()
    for name in ("app.css", "app.js", "pages.js", "sim.js", "simviz.js", "design.js", "builder.js", "media.js", "abtests.js", "agents.js"):
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
            "writes_enabled": bool(config.KLAVIYO_WRITE_KEY), "user": user, "role": users.role(user)}


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
                    "differs": f.get("differs", False), "emails_differ": f.get("emails_differ", []), "trigger": f.get("trigger"), "flow_filter": f.get("flow_filter"),
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
    agents.qa_soon(f"flow {key} approved")
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


# ---------- AI copy assistant (suggestions only; applying them is an edit like any other) ----------
def _ai(fn, *a):
    try:
        return fn(*a)
    except assistant.AssistantError as e:
        raise HTTPException(400, str(e))
    except anthropic.APIStatusError as e:
        raise HTTPException(502, f"Claude answered {e.status_code}; try again in a moment.")
    except anthropic.APIConnectionError:
        raise HTTPException(502, "Couldn't reach Claude; try again in a moment.")


@app.post("/api/assistant/{key}/rewrite")
async def api_ai_rewrite(key: str, request: Request, user=Depends(auth)):
    b = await request.json()
    return _ai(assistant.rewrite, _tpl_key(key), b.get("parts"), b.get("instruction"), b.get("context") or {}, user)


@app.post("/api/assistant/{key}/subjects")
async def api_ai_subjects(key: str, request: Request, user=Depends(auth)):
    b = await request.json()
    return _ai(assistant.subjects, _tpl_key(key), str(b.get("subject", ""))[:300], str(b.get("preview_text", ""))[:300],
               str(b.get("email_text", "")), b.get("labels") or [], str(b.get("goal", ""))[:300], user)


@app.post("/api/assistant/{key}/subject-test")
async def api_ai_subject_test(key: str, request: Request, user=Depends(auth)):
    b = await request.json()
    try:
        return _ai(assistant.subject_test, _tpl_key(key), str(b.get("subject", ""))[:300], str(b.get("preview_text", ""))[:300], user)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/assistant/{key}/check")
async def api_ai_check(key: str, request: Request, user=Depends(auth)):
    b = await request.json()
    return _ai(assistant.check, _tpl_key(key), str(b.get("subject", ""))[:300], str(b.get("preview_text", ""))[:300], b.get("blocks") or [], user)


@app.post("/api/assistant/{key}/change")
async def api_ai_change(key: str, request: Request, user=Depends(auth)):
    b = await request.json()
    return _ai(assistant.change, _tpl_key(key), b.get("instruction"), str(b.get("subject", ""))[:300], str(b.get("preview_text", ""))[:300],
               b.get("blocks") or [], b.get("labels") or [], user)


@app.get("/api/emails")
def api_emails(user=Depends(auth)):
    return {"emails": builder.emails(), "flows": {f: m.get("name", f) for f, m in evoflows.manifest()["flows"].items()}}


@app.post("/api/emails/new")
async def api_emails_new(request: Request, user=Depends(auth)):
    b = await request.json()
    return _b(builder.create_custom, b.get("name"), b.get("from") or "blank", user)


@app.get("/api/builder/{key}/comments")
def api_builder_comments(key: str, user=Depends(auth)):
    return {"comments": builder.comments(_tpl_key(key))}


@app.post("/api/builder/{key}/comments")
async def api_builder_comment(key: str, request: Request, user=Depends(auth)):
    b = await request.json()
    return {"comments": _b(builder.add_comment, _tpl_key(key), b.get("text"), b.get("block"), user, b.get("reply_to"))}


@app.post("/api/builder/{key}/comments/{cid}/resolve")
async def api_builder_comment_resolve(key: str, cid: int, request: Request, user=Depends(auth)):
    b = await request.json()
    return {"comments": _b(builder.resolve_comment, _tpl_key(key), cid, user, bool(b.get("resolved", True)))}


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
    agents.qa_soon(f"{key} v{n} published")
    return res


@app.post("/api/builder/{key}/restore-build")
def api_builder_restore(key: str, user=Depends(auth)):
    res = _b(builder.restore_build, _tpl_key(key), user)
    threading.Thread(target=evosnap.build, daemon=True).start()
    agents.qa_soon(f"{key} restored to the approved build")
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


def _src(fn, *a, **k):
    try:
        return fn(*a, **k)
    except sources.SourceError as e:
        raise HTTPException(400, str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(502, f"The image service answered {e.response.status_code}.")
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Couldn't reach the image service ({type(e).__name__}).")


@app.get("/api/media/sources")
def api_sources(user=Depends(auth)):
    return {**sources.enabled(), "staged": sources.staged()}


@app.get("/api/media/search")
def api_media_search(source: str, q: str, page: int = 1, user=Depends(auth)):
    return {"results": _src(sources.search, source, q, page)}


@app.post("/api/media/stage")
async def api_media_stage(request: Request, user=Depends(auth)):
    b = await request.json()
    return _src(sources.stage, str(b.get("source", "")), str(b.get("id", "")), user)


@app.post("/api/media/generate")
async def api_media_generate(request: Request, user=Depends(auth)):
    b = await request.json()
    return _src(sources.generate, b.get("prompt"), str(b.get("aspect", "hero")), user)


@app.post("/api/media/staged/{sid}/edit")
async def api_media_edit(sid: str, request: Request, user=Depends(auth)):
    b = await request.json()
    return _src(sources.edit, sid, str(b.get("op", "")), user, crop=b.get("crop"), focus=str(b.get("focus", "centre")))


@app.post("/api/media/staged/{sid}/alt")
def api_media_alt(sid: str, user=Depends(auth)):
    return _src(sources.suggest_alt, sid)


@app.post("/api/media/staged/{sid}/hide")
def api_media_hide(sid: str, user=Depends(auth)):
    return _src(sources.hide, sid, user)


@app.post("/api/media/staged/{sid}/attach")
async def api_media_attach(sid: str, request: Request, user=Depends(auth)):
    b = await request.json()
    kind = b.get("kind") if b.get("kind") in ("photo", "cutout", "product", "icon") else "photo"
    return _src(sources.attach, sid, str(b.get("url", ""))[:500], str(b.get("alt", ""))[:250], kind, user)


@app.get("/media/staged/{sid}")
def media_staged_file(sid: str, download: int = 0, user=Depends(auth)):
    data = _src(sources.image_bytes, sid)
    mime = "image/png" if data[:4] == b"\x89PNG" else "image/jpeg"
    headers = {"Cache-Control": "private, max-age=3600"}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="{_src(sources.download_name, sid)}"'
    return Response(data, media_type=mime, headers=headers)


@app.post("/api/media/add-url")
async def api_media_add_url(request: Request, user=Depends(auth)):
    body = await request.json()
    kind = body.get("kind") if body.get("kind") in ("photo", "cutout", "product", "icon", "logo") else "photo"
    return media.add_url(str(body.get("url", ""))[:500], str(body.get("alt", ""))[:250], kind, user)


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
    agents.qa_soon(f"A/B test {tid} {action}")
    return res


# ---------- agents (QA & compliance, manager) ----------
@app.get("/api/agents")
def api_agents(user=Depends(auth)):
    return agents.overview()


@app.get("/api/agents/status")
def api_agents_status(user=Depends(auth)):
    b, q = agents.briefs(), agents.latest_qa()
    return {"running": {**agents.running, "fix": agents.fix_state["running"], "design": design_agent.state["running"]}, "qa_at": q["at"] if q else None, "brief_n": b[-1]["n"] if b else None,
            "fixes": len(agents.fixes())}


@app.get("/api/agents/brief/{n}")
def api_agents_brief(n: int, user=Depends(auth)):
    b = agents.brief(n)
    if not b:
        raise HTTPException(404)
    return b


@app.post("/api/agents/run/{which}")
def api_agents_run(which: str, user=Depends(auth)):
    if which == "qa":
        if agents.running["qa"]:
            raise HTTPException(409, "QA is already running.")
        threading.Thread(target=agents._safe, args=(agents.run_qa, f"run by {user}"), daemon=True).start()
        return {"started": True}
    if which == "manager":
        if agents.running["manager"]:
            raise HTTPException(409, "The manager is already writing.")
        if not config.ANTHROPIC_API_KEY:
            raise HTTPException(400, "The manager needs ANTHROPIC_API_KEY in Railway.")
        threading.Thread(target=agents._safe, args=(agents.run_manager, "manual"), daemon=True).start()
        return {"started": True}
    raise HTTPException(404)


@app.post("/api/agents/decide")
async def api_agents_decide(request: Request, user=Depends(auth)):
    b = await request.json()
    try:
        return agents.decide(int(b.get("brief", 0)), str(b.get("rec", "")), str(b.get("decision", "")), b.get("note", ""), user)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/agents/action")
async def api_agents_action(request: Request, user=Depends(auth)):
    b = await request.json()
    try:
        return {"actions": agents.set_action(str(b.get("rec", "")), str(b.get("status", "")), user)}
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/agents/fix")
async def api_agents_fix(request: Request, user=Depends(auth)):
    b = await request.json()
    try:
        return agents.approve_fixes([str(x) for x in b.get("ids") or []][:200], user)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/agents/dismiss")
async def api_agents_dismiss(request: Request, user=Depends(auth)):
    b = await request.json()
    if b.get("restore"):
        return agents.undismiss(str(b["restore"]), user)
    ids = [str(x) for x in b.get("ids") or []][:200]
    if not ids or not str(b.get("reason", "")).strip():
        raise HTTPException(400, "Say why it isn't an issue (the manager and future runs read it).")
    return agents.dismiss(ids, b.get("reason"), user)


@app.post("/api/agents/fixes/publish")
async def api_agents_fixes_publish(request: Request, user=Depends(auth)):
    b = await request.json()
    return agents.publish_fixes([str(x) for x in b.get("ids") or []][:100], user)


@app.post("/api/agents/fixes/{fid}/discard")
def api_agents_fix_discard(fid: str, user=Depends(auth)):
    return agents.discard_fix(fid, user)


@app.post("/api/agents/design/run")
async def api_design_agent_run(request: Request, user=Depends(auth)):
    b = await request.json()
    keys = b.get("keys") or design_agent.all_keys()
    try:
        return design_agent.run([str(k) for k in keys][:60], f"Design agent (asked by {user})")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/agents/design/{pid}/approve")
async def api_design_agent_approve(pid: str, request: Request, user=Depends(auth)):
    b = await request.json()
    try:
        return design_agent.approve(pid, [int(x) for x in b.get("ops") or []], user)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/agents/design/{pid}/preview")
async def api_design_agent_preview(pid: str, request: Request, user=Depends(auth)):
    b = await request.json()
    try:
        return design_agent.preview(pid, [int(x) for x in b.get("ops") or []], str(b.get("audience", "non")))
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/agents/design/{pid}/dismiss")
def api_design_agent_dismiss(pid: str, user=Depends(auth)):
    return design_agent.dismiss(pid, user)


@app.post("/api/agents/context")
async def api_agents_context(request: Request, user=Depends(auth)):
    return agents.save_context((await request.json()).get("text", ""), user)


# ---------- reviewer access (Claude Code as the reporting manager) ----------
@app.get("/review/agents")
def review_agents(who=Depends(review_auth)):
    return {**agents.overview(), "reviews": agents.reviews(), "events": agents._read("events.json", [])[-100:]}


@app.get("/review/brief/{n}")
def review_brief(n: int, who=Depends(review_auth)):
    return agents.brief(n) or {}


@app.get("/review/email/{key}")
def review_email(key: str, who=Depends(review_auth)):
    """An email as customers get it (to verify findings), plus its version history."""
    _tpl_key(key)
    v = builder.live(key)
    rec = builder._load(key)
    return {"key": key, "name": v["name"], "subject": v["subject"], "preview_text": v["preview_text"], "from_name": v["from_name"],
            "html": v["html"], "status": v["status"], "versions": [{k: x.get(k) for k in ("n", "status", "by", "at", "note", "approved_by", "published_by")} for x in rec["versions"]],
            "comments": builder.comments(key), "draft": _open_draft(key)}


def _open_draft(key):
    """The open draft as customers would get it (what publishing would send), for vetting the agents' drafts."""
    rec = builder._load(key)
    open_ = [x for x in rec["versions"] if x["status"] in ("draft", "approved")]
    if not open_:
        return None
    v = max(open_, key=lambda x: x["n"])
    return {"n": v["n"], "subject": v["subject"], "preview_text": v["preview_text"], "html": builder._final(v)}


@app.get("/review/flows")
def review_flows(who=Depends(review_auth)):
    snap = evosnap.load() or {}
    return {"generated_at": snap.get("generated_at"), "flows": [{k: f.get(k) for k in ("id", "name", "status", "consent", "differs", "totals", "flow_filter", "exit", "definition")} for f in snap.get("flows", [])]}


@app.post("/review/findings/{fid:path}")
async def review_finding(fid: str, request: Request, who=Depends(review_auth)):
    b = await request.json()
    try:
        return agents.review(fid, str(b.get("verdict", "")), b.get("reason", ""), who, str(b.get("scope", "one")), b.get("severity"))
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/review/rollout/{name}")
def review_rollout_plan(name: str, who=Depends(review_auth)):
    try:
        return rollout.plan(name)
    except KeyError:
        raise HTTPException(404)


@app.post("/review/rollout/{name}")
def review_rollout_apply(name: str, who=Depends(review_auth)):
    """Drafts only: Layton publishes them from Agents > Fixes."""
    try:
        return rollout.apply(name, f"{who}, for Layton")
    except KeyError:
        raise HTTPException(404)


@app.post("/review/correct/{key}")
async def review_correct(key: str, request: Request, who=Depends(review_auth)):
    """Word corrections to an email's open draft, as a new draft (never published here)."""
    _tpl_key(key)
    b = await request.json()
    try:
        return rollout.correct(key, [(str(a), str(z)) for a, z in b.get("pairs", [])], str(b.get("note", ""))[:200], f"{who}, for Layton")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/review/request-fix")
async def review_request_fix(request: Request, who=Depends(review_auth)):
    b = await request.json()
    try:
        return agents.request_fix(str(b.get("item", "")), b.get("detail"), b.get("fix"), who)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/review/run/design")
async def review_run_design(request: Request, who=Depends(review_auth)):
    b = await request.json()
    try:
        return design_agent.run([str(k) for k in (b.get("keys") or design_agent.all_keys())][:60], "Design agent (asked by the reviewer)")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/review/run/manager")
def review_run_manager(who=Depends(review_auth)):
    if agents.running["manager"]:
        raise HTTPException(409, "The manager is already writing.")
    threading.Thread(target=agents._safe, args=(agents.run_manager, "manual (reviewer)"), daemon=True).start()
    return {"started": True}


@app.post("/review/decision")
async def review_decision(request: Request, who=Depends(review_auth)):
    """Record a decision Layton gave the reviewer in conversation (the decisions log feeds the manager)."""
    b = await request.json()
    try:
        return agents.record_decision(b.get("title", ""), str(b.get("decision", "")), b.get("note", ""), "Layton (recorded by Claude)", str(b.get("owner", "layton")))
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/review/context")
async def review_context(request: Request, who=Depends(review_auth)):
    return agents.save_context((await request.json()).get("text", ""), who)


@app.post("/review/restore/{fid:path}")
def review_restore(fid: str, who=Depends(review_auth)):
    """Undo a dismissal (the finding comes back on the next QA run)."""
    agents.undismiss(fid, who)
    st = agents._read("qa_state.json", {})
    st.get("reviews", {}).pop(fid, None)
    agents._write("qa_state.json", st)
    return {"ok": True}


@app.post("/review/run/qa")
def review_run_qa(who=Depends(review_auth)):
    if agents.running["qa"]:
        raise HTTPException(409, "QA is already running.")
    threading.Thread(target=agents._safe, args=(agents.run_qa, "run by the reviewer"), daemon=True).start()
    return {"started": True}


# ---------- brand theme (design system) ----------
@app.get("/api/design")
def api_design(user=Depends(auth)):
    d = design.theme_doc()
    br = design.brand()
    d["emails"] = [{"key": k, "name": builder.live(k)["name"], "overrides": builder.live(k).get("overrides") or {}} for k in builder.all_keys()]
    d["stacks"] = design.stacks()
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
    agents.qa_soon(f"brand theme v{n} published")
    return res


@app.post("/design/preview", response_class=HTMLResponse)
async def design_preview(request: Request, user=Depends(auth)):
    b = await request.json()
    key = _tpl_key(str(b.get("key", "")))
    out = _b(builder.preview, key, None, b.get("audience", "non"), None, None, design.merge(design.DEFAULT, b.get("theme") or {}))
    return HTMLResponse(out, headers={"Content-Security-Policy": "script-src 'none'"})


# ---------- team: admins invite people; each person sets their own password ----------
def _invite_url(request: Request, token):
    base = str(request.base_url).rstrip("/")
    if request.url.hostname not in ("127.0.0.1", "localhost"):
        base = base.replace("http://", "https://", 1)  # Railway's proxy speaks https to the browser
    return base + f"/invite/{token}"


@app.get("/api/team")
def api_team(user=Depends(admin)):
    return users.listing()


@app.post("/api/team/invite")
async def api_team_invite(request: Request, user=Depends(admin)):
    b = await request.json()
    try:
        r = users.invite(b.get("name"), b.get("label"), b.get("role"), user)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {**users.listing(), "invite": {"name": r["name"], "url": _invite_url(request, r["token"]), "expires": r["expires"]}}


@app.post("/api/team/{name}/reinvite")
def api_team_reinvite(name: str, request: Request, user=Depends(admin)):
    try:
        r = users.reinvite(name, user)
    except KeyError:
        raise HTTPException(404)
    return {**users.listing(), "invite": {"name": r["name"], "url": _invite_url(request, r["token"]), "expires": r["expires"]}}


@app.post("/api/team/{name}")
async def api_team_update(name: str, request: Request, user=Depends(admin)):
    b = await request.json()
    try:
        return users.update(name, user, b.get("role"), b.get("status"))
    except KeyError:
        raise HTTPException(404)
    except ValueError as e:
        raise HTTPException(400, str(e))


def _invite_page(body, status=200):
    import html as h
    _ = h
    return HTMLResponse(f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Join Evolution Golf Flows</title><style>body{{margin:0;background:#F4F3EE;font:16px/1.6 Inter,Arial,sans-serif;color:#1d2621}}
main{{max-width:440px;margin:8vh auto;padding:32px;background:#fff;border:1px solid #DCE1DD}}h1{{font:600 24px/1.3 Montserrat,Arial,sans-serif;color:#0F3B2A;margin:0 0 8px}}
label{{display:block;margin:16px 0 4px;font-weight:600}}input{{width:100%;box-sizing:border-box;padding:10px;border:1px solid #9aa5a0;font:inherit}}
button,a.btn{{display:inline-block;margin-top:20px;background:#0F3B2A;color:#fff;border:0;padding:12px 22px;font:500 15px Inter,Arial,sans-serif;text-decoration:none;cursor:pointer}}
.err{{background:#fbeaea;color:#7a1f1f;padding:10px 12px;margin:12px 0}}.muted{{color:#5E6B64;font-size:14px}}</style></head><body><main>{body}</main></body></html>""",
                        status_code=status, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})


@app.get("/invite/{token}", response_class=HTMLResponse)
def invite_page(token: str, err: str = ""):
    import html as h
    name, u = users.invite_lookup(token)
    if not name:
        return _invite_page("<h1>This link has expired</h1><p>Invite links work once and last 7 days. Ask your admin for a new one.</p>", 410)
    return _invite_page(f"""<h1>Join Evolution Golf Flows</h1>
<p>Hi {h.escape(u.get('label') or name)}. {h.escape(u.get('invited_by') or 'Your admin')} has invited you as <b>{users.ROLES[u['role']]}</b>: {h.escape(users.ROLE_TEXT[u['role']])}</p>
<p>Your sign-in name is <b>{h.escape(name)}</b>. Choose a password (at least 12 characters).</p>
{f'<p class="err">{h.escape(err)}</p>' if err else ''}
<form method="post"><label for="pw">Password</label><input id="pw" name="pw" type="password" autocomplete="new-password" minlength="12" required>
<label for="pw2">Password again</label><input id="pw2" name="pw2" type="password" autocomplete="new-password" minlength="12" required>
<button type="submit">Set my password</button></form>""")


@app.post("/invite/{token}", response_class=HTMLResponse)
async def invite_accept(token: str, request: Request):
    import html as h
    import urllib.parse
    form = urllib.parse.parse_qs((await request.body()).decode(), keep_blank_values=True)
    try:
        name = users.accept(token, (form.get("pw") or [""])[0], (form.get("pw2") or [""])[0])
    except ValueError as e:
        name, _u = users.invite_lookup(token)
        if not name:
            return _invite_page(f"<h1>This link has expired</h1><p>{h.escape(str(e))}</p>", 410)
        return invite_page(token, str(e))
    return _invite_page(f"""<h1>You're in</h1><p>Your password is set. Sign in with the name <b>{h.escape(name)}</b> and your new password.</p>
<a class="btn" href="/">Open the dashboard</a><p class="muted">Your browser asks for a username and password the first time: the username is <b>{h.escape(name)}</b> (not your full name or email). Keep the password to yourself: what you approve is recorded under your name.</p>""")

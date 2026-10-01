"""Evolution Golf flow dashboard: a read-only view of Klaviyo flows, performance and reviews."""
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

from . import config, digest, drafts, fixes, review, snapshot

security = HTTPBasic(auto_error=False)
STATIC = config.BASE_DIR / "app" / "static"
NOTES = config.DATA_DIR / "notes"
ID_RE = re.compile(r"^[A-Za-z0-9]{4,12}$")
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
    yield


app = FastAPI(title="Evolution Golf Flow Dashboard", docs_url=None, redoc_url=None, lifespan=lifespan)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
def index(user=Depends(auth)):
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/api/status")
def api_status(user=Depends(auth)):
    snap = snapshot.load()
    return {**snapshot.status, "source": "fixtures" if config.USE_FIXTURES else "klaviyo",
            "generated_at": snap["generated_at"] if snap else None,
            "reviews_enabled": bool(config.ANTHROPIC_API_KEY), "slack_enabled": bool(config.SLACK_WEBHOOK_URL),
            "writes_enabled": bool(config.KLAVIYO_WRITE_KEY), "user": user}


@app.get("/api/snapshot")
def api_snapshot(user=Depends(auth)):
    snap = snapshot.load()
    if not snap:
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
    p = snapshot.RENDERS / f"{_check_id(message_id)}.html"
    if not p.exists():
        return HTMLResponse("<p style='font:14px system-ui;color:#555;padding:24px'>No preview yet. "
                            "It appears after the next refresh from Klaviyo.</p>")
    return HTMLResponse(p.read_text(), headers={"Content-Security-Policy": "script-src 'none'"})


def _find_flow(flow_id):
    snap = snapshot.load() or {"flows": []}
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
def draft_email(pid: str, key: str, user=Depends(auth)):
    try:
        html = drafts.email_html(_pack_id(pid), _pack_id(key))
    except (KeyError, FileNotFoundError):
        raise HTTPException(404)
    return HTMLResponse(snapshot.fill_tags(html), headers={"Content-Security-Policy": "script-src 'none'"})

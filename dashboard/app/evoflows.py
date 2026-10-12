"""Evoflows: the self-hosted flow engine (Listmonk + SES) that is replacing Klaviyo flow by flow.

Contract: docs/source/FLOW_API.md. Base https://mail.evolutiongolf.co.uk/flow/api/v1, bearer token in EVOFLOWS_TOKEN (Railway).
This module reads (flows, metrics, runs, carts), pushes the built output in app/evoflows_out/ (flags, templates, flow
definitions: always disabled), registers the webhook and verifies deliveries. It has no code path that enables a flow:
Luke runs the staff seed test and switches flows on in the Evoflows admin.
"""
import datetime as dt
import hashlib
import hmac
import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from . import config

OUT = config.BASE_DIR / "app" / "evoflows_out"
STORE = config.DATA_DIR / "evoflows"
_lock = threading.Lock()
_cache = {}
TTL = 300


class EvoflowsError(Exception):
    pass


def enabled():
    return bool(config.EVOFLOWS_TOKEN)


def _call(method, path, body=None, timeout=60):
    if not enabled():
        raise EvoflowsError("EVOFLOWS_TOKEN is not set in Railway Variables.")
    req = urllib.request.Request(config.EVOFLOWS_BASE + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {config.EVOFLOWS_TOKEN}", "Content-Type": "application/json",
                                          "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"error": "http_error", "detail": raw[:300].decode(errors="replace")}
    except urllib.error.URLError as e:
        raise EvoflowsError(f"Couldn't reach Evoflows: {e.reason}") from e


def _get(path, fresh=False):
    with _lock:
        hit = _cache.get(path)
        if hit and not fresh and time.time() - hit[0] < TTL:
            return hit[1]
    status, res = _call("GET", path)
    if status >= 400:
        raise EvoflowsError(f"{path}: {status} {res}")
    with _lock:
        _cache[path] = (time.time(), res)
    return res


# ---------------- reads ----------------
def ping():
    return _call("GET", "/")


def overview(period="30d", fresh=False):
    """Flow list with each flow's totals. Opens/clicks are absent in Evoflows v1: shown as unavailable, never zero."""
    flows = _get("/flows", fresh)
    flows = flows.get("flows", flows) if isinstance(flows, dict) else flows
    rows = []
    for f in flows or []:
        key = f.get("key")
        try:
            m = _get(f"/metrics?flow={urllib.parse.quote(key)}&period={period}&by=all", fresh)
        except EvoflowsError as e:
            m = {"error": str(e)}
        rows.append({"flow": f, "metrics": m})
    return {"period": period, "flows": rows, "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def runs(flow, status="", limit=100):
    q = urllib.parse.urlencode({k: v for k, v in (("flow", flow), ("status", status), ("limit", limit)) if v})
    return _get(f"/runs?{q}", fresh=True)


def carts(limit=100):
    return _get(f"/carts?limit={limit}", fresh=True)


# ---------------- writes (never enable) ----------------
def _out(rel):
    return json.loads((OUT / rel).read_text())


def push(what, who):
    """Push built output: flags | templates | validate | flow. Flow definitions land disabled; validate runs first."""
    results = []
    if what == "flags":
        results.append(("PUT /flags", *_call("PUT", "/flags", _out("flags.json"))))
    elif what == "templates":
        for f in sorted((OUT / "templates").glob("*.json")):
            results.append((f"PUT /templates/{f.stem}", *_call("PUT", f"/templates/{f.stem}", json.loads(f.read_text()))))
    elif what in ("validate", "flow"):
        for f in sorted((OUT / "flows").glob("*.json")):
            body = json.loads(f.read_text())
            status, res = _call("POST", f"/flows/{f.stem}/validate", body)
            results.append((f"POST /flows/{f.stem}/validate", status, res))
            problems = status >= 400 or (res or {}).get("errors") or any(
                (w.get("code") if isinstance(w, dict) else str(w)) == "template_missing" for w in (res or {}).get("warnings", []))
            if what == "flow" and not problems:
                body.pop("enabled", None)  # never switch on from here
                results.append((f"PUT /flows/{f.stem}", *_call("PUT", f"/flows/{f.stem}", body)))
            elif what == "flow":
                results.append((f"PUT /flows/{f.stem}", 0, {"skipped": "validate reported problems; fix them first"}))
    else:
        raise EvoflowsError("unknown push")
    _log({"at": _now(), "by": who, "push": what, "results": [{"call": c, "status": s, "response": r} for c, s, r in results]})
    with _lock:
        _cache.clear()
    return [{"call": c, "status": s, "response": r} for c, s, r in results]


def register_webhook(url, who):
    status, res = _call("PUT", "/webhooks", {"url": url, "events": ["*"]})
    if status < 400 and res and res.get("secret"):
        STORE.mkdir(parents=True, exist_ok=True)
        (STORE / "webhook.json").write_text(json.dumps({"url": url, "secret": res["secret"], "at": _now(), "by": who}))
        res = {k: v for k, v in res.items() if k != "secret"} | {"secret": "stored on the app volume"}
    _log({"at": _now(), "by": who, "webhook": url, "status": status})
    return status, res


def _secret():
    if config.EVOFLOWS_WEBHOOK_SECRET:
        return config.EVOFLOWS_WEBHOOK_SECRET
    try:
        return json.loads((STORE / "webhook.json").read_text())["secret"]
    except Exception:
        return ""


def verify(raw, header):
    secret = _secret()
    if not secret or not header or not header.startswith("sha256="):
        return False
    good = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(good, header.split("=", 1)[1].strip())


def record_event(payload):
    """Keep the last 500 deliveries (event, flow, step, time). Email addresses are not stored."""
    STORE.mkdir(parents=True, exist_ok=True)
    path = STORE / "events.json"
    with _lock:
        try:
            events = json.loads(path.read_text())
        except Exception:
            events = []
        events.append({k: payload.get(k) for k in ("event", "at", "flow", "run_id", "step")})
        path.write_text(json.dumps(events[-500:]))


def recent_events():
    try:
        return json.loads((STORE / "events.json").read_text())[::-1][:100]
    except Exception:
        return []


def push_log():
    try:
        return json.loads((STORE / "log.json").read_text())[::-1][:20]
    except Exception:
        return []


def webhook_info():
    try:
        w = json.loads((STORE / "webhook.json").read_text())
        return {"url": w["url"], "at": w["at"], "by": w["by"]}
    except Exception:
        return None


def _log(entry):
    STORE.mkdir(parents=True, exist_ok=True)
    path = STORE / "log.json"
    with _lock:
        try:
            log = json.loads(path.read_text())
        except Exception:
            log = []
        log.append(entry)
        path.write_text(json.dumps(log[-200:], default=str))


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def preview(key, sample="checkout"):
    return _call("POST", f"/templates/{key}/preview", {"sample": sample})


def test_send(key, to, who, sample="checkout"):
    """Real render to a staff inbox (Evoflows only allows @evolutiongolf.co.uk). Logged with who asked."""
    if not to.lower().endswith("@evolutiongolf.co.uk"):
        raise EvoflowsError("Test sends go to @evolutiongolf.co.uk addresses only.")
    status, res = _call("POST", f"/templates/{key}/test", {"to": to, "sample": sample})
    _log({"at": _now(), "by": who, "push": f"test {key} → {to}", "status": status})
    return status, res


def template_keys():
    return sorted(f.stem for f in (OUT / "templates").glob("*.json"))

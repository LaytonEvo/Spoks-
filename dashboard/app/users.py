"""Dashboard users: invited by an admin, each with a role. Stored on the app volume (users.json); passwords hashed.

Roles (what each can do; admins also manage the team):
  admin     everything, plus the Team page (invite, change roles, switch people off)
  approver  everything except the Team page: approve, publish, push to Evoflows
  editor    edit and save drafts, comment, images, AI assistant, staff test sends; can't approve, publish or push
  viewer    look, preview and comment only

People set in Railway (DASHBOARD_PASSWORD / DASHBOARD_USERS) are always admins, so nobody can lock the owner out.
An invite is a one-time link (7 days): the person opens it and chooses their own password. Nothing is emailed by the app.
"""
import datetime as dt
import hashlib
import json
import re
import secrets
import threading

from . import config

PATH = config.DATA_DIR / "users.json"
ROLES = {"admin": "Admin", "approver": "Approver", "editor": "Editor", "viewer": "Viewer"}
ROLE_TEXT = {"admin": "Everything, plus inviting and managing the team.",
             "approver": "Everything except the team: approve, publish and push to Evoflows (switched off).",
             "editor": "Edit emails and save drafts, comment, add images, use the AI assistant, send staff tests. Can't approve or publish.",
             "viewer": "Look, preview and comment only."}
NAME_RE = re.compile(r"^[a-z][a-z0-9._-]{1,31}$")
INVITE_DAYS = 7
ITER = 200_000
_lock = threading.Lock()
_ok = {}  # sha256(user:password) -> user, so the slow hash runs once per sign-in, not on every request


def _now():
    return dt.datetime.now(dt.timezone.utc)


def _load():
    try:
        return json.loads(PATH.read_text())
    except Exception:
        return {"users": {}}


def _save(d):
    PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=1))
    tmp.replace(PATH)


def _hash(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), ITER).hex()


def _tok(t):
    return hashlib.sha256(t.encode()).hexdigest()


def env_users():
    u = dict(config.DASHBOARD_USERS)
    if config.DASHBOARD_PASSWORD:
        u.setdefault(config.DASHBOARD_USER, config.DASHBOARD_PASSWORD)
    return u


def any_users():
    return bool(env_users()) or any(x.get("status") == "active" for x in _load()["users"].values())


def check(name, pw):
    """The user's name if these credentials are good, else None."""
    if not name or not pw:
        return None
    for n, p in env_users().items():
        if secrets.compare_digest(name, n) and secrets.compare_digest(pw, p):
            return n
    key = hashlib.sha256(f"{name}:{pw}".encode()).hexdigest()
    if _ok.get(key) == name:
        u = _load()["users"].get(name)
        if u and u.get("status") == "active":
            return name
        _ok.pop(key, None)
        return None
    u = _load()["users"].get(name)
    if not u or u.get("status") != "active" or not u.get("hash"):
        return None
    if secrets.compare_digest(_hash(pw, u["salt"]), u["hash"]):
        _ok[key] = name
        _seen(name)
        return name
    return None


def _seen(name):
    with _lock:
        d = _load()
        u = d["users"].get(name)
        if u:
            u["last_sign_in"] = _now().isoformat(timespec="seconds")
            _save(d)


def role(name):
    if name == "local" or name in env_users():
        return "admin"
    u = _load()["users"].get(name)
    return u["role"] if u and u.get("status") == "active" and u.get("role") in ROLES else "viewer"


# ---------------- what each role can do (checked on every change request) ----------------
# Anyone signed in may read (GET) and use these: previews, the readability check, comments, refresh.
OPEN = [r"^/api/refresh$", r"^/builder/[\w-]+/preview$", r"^/design/preview$", r"^/api/design/check$",
        r"^/api/agents/design/[\w-]+/preview$", r"^/api/builder/[\w-]+/comments(/[\w-]+/resolve)?$", r"^/api/notes/[\w-]+$"]
# Approving, publishing, pushing and decisions: approvers and admins only.
APPROVE = [r"^/api/drafts/[\w-]+/approve$", r"^/api/evoflows/(push|approve|webhook)", r"^/api/builder/[\w-]+/(approve|publish)/",
           r"^/api/builder/[\w-]+/restore-build$", r"^/api/abtests/[\w-]+/", r"^/api/agents/(decide|action|dismiss|context)$",
           r"^/api/agents/fixes/", r"^/api/agents/design/[\w-]+/dismiss$", r"^/api/design/(approve|publish)/", r"^/api/summary/send$",
           r"^/api/fixes/[\w-]+/[\w-]+$"]


def allowed(r, method, path):
    if method in ("GET", "HEAD", "OPTIONS") or r == "admin":
        return True
    if path.startswith("/api/team"):
        return False
    if any(re.match(p, path) for p in OPEN):
        return True
    if r == "viewer":
        return False
    if r == "editor" and any(re.match(p, path) for p in APPROVE):
        return False
    return True


# ---------------- the Team page ----------------
def listing():
    d = _load()
    now = _now()
    rows = [{"name": n, "role": "admin", "status": "active", "source": "railway", "label": n} for n in env_users()]
    for n, u in sorted(d["users"].items()):
        st = u.get("status")
        if st == "invited" and dt.datetime.fromisoformat(u["invite_expires"]) < now:
            st = "invite expired"
        rows.append({"name": n, "label": u.get("label") or n, "role": u["role"], "status": st, "source": "app",
                     "invited_by": u.get("invited_by"), "invited_at": u.get("invited_at"), "last_sign_in": u.get("last_sign_in"),
                     "invite_expires": u.get("invite_expires") if st == "invited" else None})
    return {"users": rows, "roles": [{"key": k, "label": v, "text": ROLE_TEXT[k]} for k, v in ROLES.items()]}


def _invite(u, who):
    t = secrets.token_urlsafe(32)
    u.update(invite=_tok(t), invite_expires=(_now() + dt.timedelta(days=INVITE_DAYS)).isoformat(timespec="seconds"),
             invited_by=who, invited_at=_now().isoformat(timespec="seconds"))
    return t


def invite(name, label, r, who):
    name = (name or "").strip().lower()
    if not NAME_RE.match(name):
        raise ValueError("Sign-in names are 2 to 32 lower-case letters or numbers (dots, dashes and underscores allowed), starting with a letter.")
    if r not in ROLES:
        raise ValueError("Pick a role.")
    if name in env_users() or name == "local":
        raise ValueError("That name is already a login set in Railway.")
    with _lock:
        d = _load()
        if name in d["users"] and d["users"][name].get("status") == "active":
            raise ValueError("Someone already has that sign-in name. Use 'New invite link' on their row to reset them.")
        u = {"role": r, "label": (label or name).strip()[:60], "status": "invited", "salt": secrets.token_hex(16), "hash": None}
        t = _invite(u, who)
        d["users"][name] = u
        _save(d)
    _ok.clear()
    return {"name": name, "token": t, "expires": u["invite_expires"]}


def reinvite(name, who):
    """A new one-time link; the old password stops working until they choose a new one."""
    with _lock:
        d = _load()
        u = d["users"].get(name)
        if not u:
            raise KeyError(name)
        u.update(status="invited", hash=None, salt=secrets.token_hex(16))
        t = _invite(u, who)
        _save(d)
    _ok.clear()
    return {"name": name, "token": t, "expires": u["invite_expires"]}


def update(name, who, role_=None, status=None):
    if name == who:
        raise ValueError("You can't change your own access.")
    with _lock:
        d = _load()
        u = d["users"].get(name)
        if not u:
            raise KeyError(name)
        if role_ is not None:
            if role_ not in ROLES:
                raise ValueError("Unknown role.")
            u["role"] = role_
        if status == "disabled":
            u.update(status="disabled", invite=None)
        elif status == "active":
            if not u.get("hash"):
                raise ValueError("They haven't set a password yet: send a new invite link instead.")
            u["status"] = "active"
        u.setdefault("history", []).append({"at": _now().isoformat(timespec="seconds"), "by": who, "role": role_, "status": status})
        _save(d)
    _ok.clear()
    return listing()


def invite_lookup(token):
    """(name, user) for a live invite, else (None, None)."""
    h = _tok(token or "")
    for n, u in _load()["users"].items():
        if u.get("status") == "invited" and u.get("invite") and secrets.compare_digest(u["invite"], h):
            if dt.datetime.fromisoformat(u["invite_expires"]) >= _now():
                return n, u
    return None, None


def accept(token, pw, pw2):
    if len(pw or "") < 12:
        raise ValueError("Use at least 12 characters.")
    if pw != pw2:
        raise ValueError("The two passwords don't match.")
    with _lock:
        name, _ = invite_lookup(token)
        if not name:
            raise ValueError("This invite link has expired or been used. Ask your admin for a new one.")
        d = _load()
        u = d["users"][name]
        u.update(hash=_hash(pw, u["salt"]), status="active", invite=None, invite_expires=None,
                 joined_at=_now().isoformat(timespec="seconds"))
        _save(d)
    _ok.clear()
    return name

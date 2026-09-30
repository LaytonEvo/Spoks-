"""Settings, all from environment variables (set them in Railway or a local .env)."""
import os
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

# Klaviyo private API key with READ-ONLY scopes (flows, templates, metrics, lists, segments, reporting).
KLAVIYO_API_KEY = os.getenv("KLAVIYO_API_KEY", "")
# Separate Klaviyo key used ONLY to apply fixes Layton approves in the app (Templates: read + write).
# Leave unset and the app stays read-only.
KLAVIYO_WRITE_KEY = os.getenv("KLAVIYO_WRITE_KEY", "")
# Klaviyo API revision. Flow definitions need a recent revision; change here if Klaviyo rejects it.
KLAVIYO_REVISION = os.getenv("KLAVIYO_REVISION", "2025-10-15")
# "Placed Order" metric used for conversions and revenue.
CONVERSION_METRIC_ID = os.getenv("CONVERSION_METRIC_ID", "T9sNn9")

# Claude API key for the written reviews (optional: the dashboard works without it).
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
REVIEW_MODEL = os.getenv("REVIEW_MODEL", "claude-opus-5-5")

# Login for the dashboard. If unset, the app runs without a login (local development only).
DASHBOARD_USER = os.getenv("DASHBOARD_USER", "evolution")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")
# Named logins, so approvals record who made them: "layton:password1,karin:password2".
DASHBOARD_USERS = dict(pair.split(":", 1) for pair in os.getenv("DASHBOARD_USERS", "").split(",") if ":" in pair)

# Where snapshots, renders, reviews and notes are stored. Use a Railway volume in production.
DATA_DIR = pathlib.Path(os.getenv("DATA_DIR", BASE_DIR / "data"))

# Use saved test data instead of calling Klaviyo (development, or before a key is set).
USE_FIXTURES = os.getenv("USE_FIXTURES", "").lower() in ("1", "true", "yes") or not KLAVIYO_API_KEY
FIXTURE_DIR = pathlib.Path(os.getenv("FIXTURE_DIR", BASE_DIR / "fixtures"))

# Drafts are shown only when their name starts with one of these prefixes (new EG builds).
DRAFT_PREFIXES = tuple(p for p in os.getenv("DRAFT_PREFIXES", "EG ·").split(",") if p)

TIMEFRAMES = ["last_30_days", "last_90_days", "last_365_days"]

# Monday summary: posted to this Slack incoming-webhook URL when set. Leave unset and nothing is ever sent.
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
# Public address of the dashboard, for links in the summary (Railway sets RAILWAY_PUBLIC_DOMAIN).
PUBLIC_URL = os.getenv("PUBLIC_URL") or (f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN')}" if os.getenv("RAILWAY_PUBLIC_DOMAIN") else "")

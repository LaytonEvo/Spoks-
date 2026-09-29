# Evolution Golf flow dashboard (read-only)

One clear view of every Klaviyo flow: the journey, each email and SMS, its performance, rule-based
health checks, Claude's written review, and team notes. It never changes anything in Klaviyo.

## What it reads
- Flows and their definitions (trigger, filters, delays, splits, messages, A/B tests)
- Per-message performance for the last 30 days, 90 days and 12 months (Klaviyo flow report, Placed Order conversions)
- Email previews rendered by Klaviyo with an example basket (name "Sam", a Motocaddy M1 DHC), never a real customer

Live and manual flows are always shown; drafts only when their name starts with `EG ·`.
Data is cached in a snapshot and refreshed daily or with the "Refresh from Klaviyo" button
(Klaviyo's reporting API allows only a couple of calls a minute, so pages never call it directly).

## Settings (environment variables)
| Variable | Needed | What |
| --- | --- | --- |
| `KLAVIYO_API_KEY` | yes | Private key with **read-only** access: Flows, Templates, Metrics, Lists, Segments, Campaigns/Flows reporting |
| `DASHBOARD_PASSWORD` | yes | Login password (user name `evolution`, or set `DASHBOARD_USER`) |
| `ANTHROPIC_API_KEY` | for reviews | Claude API key; reviews use `claude-opus-5-5` |
| `DATA_DIR` | on Railway | `/data` (a mounted volume, so snapshots, reviews and notes survive redeploys) |
| `KLAVIYO_REVISION` | optional | Defaults to `2025-10-15`; change if Klaviyo rejects the revision |
| `USE_FIXTURES` | optional | `1` to run on the saved test data in `fixtures/` |

## Run locally
```
pip install -r requirements.txt
USE_FIXTURES=1 uvicorn app.main:app --reload     # saved test data
KLAVIYO_API_KEY=pk_... uvicorn app.main:app      # live
```

## Deploy on Railway
New service from this GitHub repo, root directory `dashboard`, add a volume mounted at `/data`,
set the variables above, then generate a domain. `railway.json` sets the start command.

# Evolution Golf flow dashboard (read-only)

One clear view of every Klaviyo flow: the journey, each email and SMS, its performance, rule-based
health checks, Claude's written review, and team notes. It never changes anything in Klaviyo.

## What it reads
- Flows and their definitions (trigger, filters, delays, splits, messages, A/B tests)
- Per-message performance for the last 30 days, 90 days and 12 months (Klaviyo flow report, Placed Order conversions)
- Week-by-week counts per message for the last 12 months (Klaviyo flow series report), for trends and comparisons
- Email previews rendered by Klaviyo with an example basket (name "Sam", a Motocaddy M1 DHC), never a real customer

Live and manual flows are always shown; drafts only when their name starts with `EG ·`.
Data is cached in a snapshot and refreshed daily or with the "Refresh from Klaviyo" button
(Klaviyo's reporting API allows only a couple of calls a minute, so pages never call it directly).

## Pages
- **Overview**: sortable table with a verdict per flow, colour cues against your own median flow, and a revenue trend.
- **Flow**: week-by-week sends, revenue and revenue per send; the journey with a preview pane; Claude's review; notes.
- **Programme**: the Build Pack flows (F1–F13) in build order, with status worked out from Klaviyo (`EG · F<n>` names),
  what each replaces, to-dos and open questions. Edit `app/programme.json` to update it.
- **Compare**: new flow or path against the one it replaces. After launch, the weeks since launch are set against the
  same number of weeks just before it.
- **A/B tests**: every test, days running, and flags for tests left running over 45 days.
- **Monday summary**: last full week against the 4-week average, flows that stopped sending, newly flagged items and
  the top three actions. Posted to Slack on Mondays from 08:00 London time only if `SLACK_WEBHOOK_URL` is set.

## Settings (environment variables)
| Variable | Needed | What |
| --- | --- | --- |
| `KLAVIYO_API_KEY` | yes | Private key with **read-only** access: Flows, Templates, Metrics, Lists, Segments, Campaigns/Flows reporting |
| `DASHBOARD_PASSWORD` | yes | Login password (user name `evolution`, or set `DASHBOARD_USER`) |
| `ANTHROPIC_API_KEY` | for reviews | Claude API key; reviews use `claude-opus-5-5` |
| `DATA_DIR` | on Railway | `/data` (a mounted volume, so snapshots, reviews and notes survive redeploys) |
| `KLAVIYO_REVISION` | optional | Defaults to `2025-10-15`; change if Klaviyo rejects the revision |
| `USE_FIXTURES` | optional | `1` to run on the saved test data in `fixtures/` |
| `SLACK_WEBHOOK_URL` | optional | Slack incoming-webhook address for the Monday summary. Unset = nothing is ever posted |
| `PUBLIC_URL` | optional | Dashboard address for links in the summary (defaults to Railway's public domain) |

## Run locally
```
pip install -r requirements.txt
USE_FIXTURES=1 uvicorn app.main:app --reload     # saved test data
KLAVIYO_API_KEY=pk_... uvicorn app.main:app      # live
```

## Deploy on Railway
New service from this GitHub repo, root directory `dashboard`, add a volume mounted at `/data`,
set the variables above, then generate a domain. `railway.json` sets the start command.

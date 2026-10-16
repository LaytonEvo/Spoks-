# Evolution Golf flow dashboard

One view of every email flow: our flows on **Evoflows** (the self-hosted engine replacing Klaviyo, flow by flow) and the
live **Klaviyo** flows they're replacing, shown read-only until each is switched off. For each flow: the journey, every
email with a preview, its performance, rule-based checks, Claude's written review and team notes.

The app never switches a flow on or off, never sends to customers and never deletes anything. On Evoflows it can only
push approved builds, which land switched off (Luke switches them on after a staff test).

## Where the data comes from
- **Evoflows** (`EVOFLOWS_TOKEN`), refreshed every 15 minutes and on **Refresh**:
  - flows and their definitions (`/flows`);
  - per-email and per-flow metrics for 30 days, 90 days and 12 months (`/metrics`);
  - week-by-week sends and revenue;
  - the people in each flow (`/runs`).

  Revenue = orders placed after one of the flow's emails. Opens and clicks aren't tracked in Evoflows v1, so they show as n/a.
- **The approved builds** in `app/evoflows_out/` (written by `klaviyo/evoflows.py`): flow definitions, templates,
  previews and `manifest.json` (programme id, the Klaviyo flows each one replaces, deviations from the Klaviyo version).
- **Klaviyo** (`KLAVIYO_API_KEY`, read-only), refreshed daily: the live and manual Klaviyo flows still sending, with
  their numbers. Each one shows which Evoflows flow replaces it. Klaviyo `EG ·` drafts are no longer shown. When
  Klaviyo is switched off, remove the key and the dashboard runs on Evoflows alone.

## Pages
- **Overview:** every flow, with platform, verdict, sends, orders, revenue and trend. Filters: Evoflows, Klaviyo
  (being replaced), needs work.
- **Flow:** the journey with previews, week-by-week figures, checks, review and notes.
  - On Evoflows: who enters, who leaves, consent, the Klaviyo flows to switch off when it goes on, and how it differs
    from the approved Klaviyo version.
  - **People in it:** the latest runs, with email addresses shortened.
- **New flows to approve:** the approved builds and where each stands on Evoflows (not pushed, switched off, live, or
  changed since pushed). Inside each one:
  - **Check with Evoflows:** validates it.
  - **Approve:** uploads its emails and the flow, switched off, after validation. Logged with who approved.
  - **Send me a test of every email:** staff addresses only.
- **Programme:** the Build Pack flows (F1–F13) with status from Evoflows, what each replaces, and what each is waiting
  on (`app/programme.json`).
- **Compare:** a new Evoflows flow against the Klaviyo flow it replaces. After launch, the weeks since launch are set
  against the same number of weeks just before it.
- **Monday summary:** last week against the 4-week average, flows that stopped sending, new high-priority checks.
  Posted to Slack only if `SLACK_WEBHOOK_URL` is set.
- **Engine & events:** every flow on the engine (Luke's staff tests included), webhook deliveries, push history, the
  basket flags.
- Retired from the menu with the move to Evoflows: Fixes (Klaviyo email edits), A/B tests and the Klaviyo flow map.
  Their code and saved data are kept.

## Settings (environment variables)
| Variable | Needed | What |
| --- | --- | --- |
| `EVOFLOWS_TOKEN` | yes | Evoflows API token (from Luke). Never commit it |
| `EVOFLOWS_WEBHOOK_SECRET` | for events | Secret for verifying Evoflows webhook deliveries |
| `KLAVIYO_API_KEY` | until Klaviyo goes | Private key with **read-only** access: Flows, Templates, Metrics, Lists, Segments, Campaigns/Flows reporting |
| `DASHBOARD_PASSWORD` | yes | Login password (user name `evolution`, or set `DASHBOARD_USER`) |
| `ANTHROPIC_API_KEY` | for reviews | Claude API key; reviews use `claude-opus-5-5` |
| `DATA_DIR` | on Railway | `/data` (a mounted volume, so snapshots, reviews and notes survive redeploys) |
| `KLAVIYO_REVISION` | optional | Defaults to `2025-10-15`; change if Klaviyo rejects the revision |
| `USE_FIXTURES` | optional | `1` to run on the saved test data in `fixtures/` |
| `KLAVIYO_WRITE_KEY` | to apply fixes | A second Klaviyo private key with **Templates: read + write** only. Unset = read-only app |
| `DASHBOARD_USERS` | recommended | Named logins so approvals show who made them: `layton:pass1,karin:pass2` |
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

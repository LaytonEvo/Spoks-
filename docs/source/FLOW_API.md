# Evoflows — what the flow dashboard needs to do once Klaviyo is gone, and the API to build against

**For:** the developer of the Evolution Golf Flows dashboard (Railway app).
**From:** the Evoflows engine project (BusinessEmail repo, `flow-engine/`), 9 Oct 2026.
**Status:** proposal v1. The engine's checkout flow is live-tested; the API below is **not built yet** — it is the
contract we will build to, so push back on anything before we start.

---

## 1. Where things stand

Evolution Golf's email now runs on a self-hosted stack: **Listmonk + Amazon SES** for campaigns, and **Evoflows**,
a small engine on the same server, for automations. Evoflows polls Shopify, keeps its own state, sends every email
through Listmonk's transactional API, enforces consent itself, and serves a signed one-click unsubscribe. The
abandoned-checkout flow (your F3) has passed its staff seed test on it. Klaviyo is being switched off flow by flow.

Your dashboard today is built around Klaviyo in both directions:

| Today | Source / target |
|---|---|
| "Refresh from Klaviyo" → snapshot, metrics, weekly series, flags | Klaviyo read API |
| Draft packs (F1–F13): outline, emails, **templates = Klaviyo template ids** | Klaviyo |
| "Approve" → creates the flow + emails in Klaviyo as a switched-off draft | Klaviyo write API |
| Fixes (broken unsubscribe links, discount in a trolley email…) → scans Klaviyo emails, writes fixes back | Klaviyo |
| Notes, reviews, weekly summary, Slack | your own storage |

With Klaviyo out, **Evoflows becomes both the read source and the write target.** Your app keeps its real value —
the programme, the pack authoring, the review discipline, the flags, the weekly summary — and swaps the backend.

## 2. What changes in your app

1. **Approve → push to Evoflows, not Klaviyo.** A pack becomes (a) one **flow definition** (section 4) and (b) one
   **template per email** (section 5), both pushed over the API, created **disabled**. Switching on is a separate
   explicit call, same as your "nothing sends until you switch it on" rule.
2. **Timing and branching must become data.** Today a pack says *"Hardware · 3 days after dispatch, 09:30"* in
   prose. Evoflows needs that as `wait 3 days, until 09:30` and a branch condition on what was ordered. The flow JSON
   in section 4 is the shape; your outline text can stay as the human summary.
3. **Email HTML has to live in your app (or be pushed to us).** Klaviyo template ids stop meaning anything. Each
   email is `subject`, `preview_text`, `html` with Evoflows tokens (section 5). We validate on push and reject any
   leftover Klaviyo tags.
4. **Metrics come from `/metrics`.** Per flow and per step: enrolled, sent, delivered, bounced, complained,
   unsubscribed, converted, revenue. Your weekly series, flags (unsubscribe rate over limit, etc.) and summary all
   keep working off that. See the honesty note in 6.3 about opens/clicks.
5. **Triggers map like this:**

   | Klaviyo trigger you use | Evoflows trigger | How Evoflows gets it |
   |---|---|---|
   | Checkout Started | `checkout_abandoned` | polls Shopify `abandonedCheckouts` (live now) |
   | Placed Order | `order_placed` | polls Shopify orders (live now for exits; trigger = small addition) |
   | Fulfilled Order | `order_fulfilled` | polls Shopify orders with `fulfilled_at` |
   | Added to List "1.0 Main Mailing List" | `subscribed` | Listmonk subscriber created/enabled (the Shopify→Listmonk sync) |
   | Added to Cart / Viewed Product | `cart_updated` / `product_viewed` | our onsite tracker (`cart-tracker.js`) — **phase 2, and gated on the consent fix** |
   | membership tier change, back in stock, anything else | `custom` via `POST /events` | **your app (or the membership portal) pushes it** |

6. **Segments become conditions.** "lapsed", "candidates", "annual" etc. are predicates on contact/customer/order
   fields evaluated by the engine at trigger time (section 4.3), not stored segments.
7. **Fixes scanner:** point it at our templates (`GET /templates`) instead of Klaviyo messages. Two of its checks
   become moot — the unsubscribe link is injected by the engine on every send, and UTMs are added by the engine.
8. **Out of scope for v1:** SMS (no SMS channel), A/B tests (later), Klaviyo writes.

### The consent pop-up blocks us too
Your handover "cookie consent pop-up is stopping Klaviyo on-site tracking" applies word for word to Evoflows' onsite
tracker: it checks `Shopify.customerPrivacy.userCanBeTracked()` before sending anything, so visitors stuck in the
"answered locally, never consented in Shopify" state are invisible to us as well. **Fix the pop-up (Shopify as
source of truth) before F4 cart / F5 browse are built on either platform.** Checkout and post-purchase flows are
unaffected (server-side data).

## 3. API basics

- **Base URL:** `https://mail.evolutiongolf.co.uk/flow/api/v1`
- **Auth:** `Authorization: Bearer <token>`. One token per client app, issued by us, revocable. HTTPS only.
- **Format:** JSON in and out. Timestamps ISO-8601 UTC. Money in GBP as numbers. Emails lower-cased by us.
- **Idempotency:** `PUT` is upsert by key. `POST /events` takes an `idempotency_key`; repeats are acknowledged, not re-run.
- **Errors:** `4xx/5xx` with `{"error": "<code>", "detail": "<human text>", "field": "<json path if relevant>"}`.
- **Limits:** 60 requests/min per token; `/events` 600/min. `429` + `Retry-After` beyond that.
- **Audit:** every write records the token name; visible in the Evoflows admin.

## 4. Flows

### 4.1 Endpoints
| Method | Path | Does |
|---|---|---|
| `GET` | `/flows` | list: key, name, version, enabled, counts |
| `GET` | `/flows/{key}` | full definition + status |
| `PUT` | `/flows/{key}` | create/replace definition. Always lands **disabled** unless it was already enabled and the body says `"enabled": true`; a definition change to an enabled flow applies to **new** runs only, active runs finish on the version they started |
| `POST` | `/flows/{key}/enable` · `/disable` | switch on/off. `disable` stops new enrolments; active runs continue unless `?exit_active=true` |
| `DELETE` | `/flows/{key}` | only when disabled; history kept |
| `POST` | `/flows/{key}/validate` | dry validation of a body without saving (schema, unknown fields, templates exist, conditions parse) |

### 4.2 Flow definition
```json
{
  "key": "f9_after_delivery",
  "name": "F9 After delivery + review",
  "version": 3,
  "description": "Online orders, 3 days after dispatch…",
  "trigger": {
    "type": "order_fulfilled",
    "when": { "field": "order.source", "eq": "web" }
  },
  "entry": {
    "one_active_per_contact": true,
    "reentry_after_days": 60,
    "not_while_active_in": ["abandoned_checkout"]
  },
  "exit": {
    "when": { "field": "contact.consent", "ne": "ok" }
  },
  "consent": "soft_opt_in",
  "send_window": { "timezone": "Europe/London", "quiet_hours": ["21:00", "08:00"], "days": ["mon","tue","wed","thu","fri","sat","sun"] },
  "utm": { "source": "evolutiongolf-email", "medium": "flow", "campaign": "f9-after-delivery" },
  "steps": [
    { "id": "w1", "type": "wait", "for": { "days": 3 }, "until_time": "09:30" },
    { "id": "cat", "type": "split", "branches": [
      { "id": "hardware",
        "when": { "any": [
          { "field": "order.collections", "contains": "golf-trolleys" },
          { "field": "order.product_types", "contains": "Golf Clubs" } ] },
        "steps": [
          { "id": "e1h", "type": "email", "template": "f9_e1h",
            "when": { "all": [ { "field": "customer.member", "eq": false }, { "field": "order.age_days", "lte": 10 } ] },
            "else_template": "f9_e1hn" },
          { "id": "w2", "type": "wait", "for": { "days": 4 }, "until_time": "17:30" },
          { "id": "e2h", "type": "email", "template": "f9_e2h" },
          { "id": "w3", "type": "wait", "for": { "days": 3 }, "until_time": "09:30" },
          { "id": "rem", "type": "email", "template": "f9_rem",
            "when": { "all": [ { "field": "customer.member", "eq": false }, { "field": "order.age_days", "lte": 14 } ] } },
          { "id": "w4", "type": "wait", "for": { "days": 4 }, "until_time": "09:30",
            "when": { "field": "order.collections", "contains": "golf-trolleys" }, "else_for": { "days": 18 } },
          { "id": "rvh", "type": "email", "template": "f9_rvh" }
        ] },
      { "id": "else", "steps": [
          { "id": "e1e", "type": "email", "template": "f9_e1e",
            "when": { "all": [ { "field": "customer.member", "eq": false }, { "field": "order.age_days", "lte": 10 } ] },
            "else_template": "f9_e1en" },
          { "id": "w5", "type": "wait", "for": { "days": 7 }, "until_time": "09:30" },
          { "id": "rve", "type": "email", "template": "f9_rve" }
        ] }
    ] }
  ]
}
```

**Step types**
| type | fields | notes |
|---|---|---|
| `wait` | `for` {days,hours,minutes}, `until_time` "HH:MM" (shop timezone), optional `when` + `else_for` | relative to the previous step completing; `until_time` rolls forward to the next occurrence |
| `email` | `template`, optional `when`, `else_template`, `discount` (Shopify code), `subject_override` | `when` false and no `else_template` = skip the step |
| `split` | `branches[]` each `{id, when?, steps[]}` | first branch whose `when` is true (or has none) runs; nothing matches = continue after the split |
| `exit` | `reason` | ends the run |
| `set` | `attribute`, `value` | writes a Listmonk subscriber attribute (your "Set in_postpurchase_flow" pattern) |

**Trigger types:** `checkout_abandoned`, `order_placed`, `order_fulfilled`, `subscribed`, `custom` (`event_name`
required; fired by `POST /events`). Phase 2: `cart_updated`, `product_viewed`.

**Engine guarantees** (you do not have to re-implement these): one active run per contact per flow; consent checked
before **every** send (Listmonk status + soft opt-in list); unsubscribe link injected; stale step skipped rather than
sent late after downtime; exit on purchase for cart/checkout flows; nothing enrolled from before a flow was enabled
(no backfill); UTM appended to every link.

### 4.3 Conditions
`{ "field": "...", "<op>": value }` or combinators `{ "all": [...] }`, `{ "any": [...] }`, `{ "not": {...} }`.
Ops: `eq ne gt gte lt lte in nin contains not_contains exists`. Missing field = `false` (except `exists`).

| Field group | Fields |
|---|---|
| `contact.` | `email first_name consent (ok|blocklisted|unknown) lists[] attributes.* days_since_subscribed` |
| `customer.` | `tags[] member (bool, from tags/membership attribute) member_tier orders_count total_spent last_order_at days_since_last_order first_order (bool)` |
| `order.` | `name total currency source (web|pos|other) created_at fulfilled_at age_days line_items[] product_types[] collections[] (handles) product_tags[] vendors[] discount_codes[] shipping_country` |
| `checkout.` | `total items[] recovery_url age_minutes` |
| `event.` | `name data.*` (custom events) |

### 4.4 Flow table in the Evoflows admin (what Luke asked for)
Evoflows' own admin (`/flow/admin`) gets a **Flows** table powered by the same `/metrics` endpoint your app uses, so
both screens agree: one row per flow — enabled, enrolled, active now, emails sent, finished, **converted after an
email** with **revenue**, refused (no consent), unsubscribed, unsubscribe rate, bounce rate, conversion rate — with
30/90/365-day periods. Click a flow → per-step rows → the per-customer runs view that exists today.

## 5. Templates

| Method | Path | Does |
|---|---|---|
| `GET` | `/templates` · `/templates/{key}` | list / fetch (html included on single fetch) |
| `PUT` | `/templates/{key}` | upsert `{ "name", "subject", "preview_text", "html", "from_name"? }` → `{ "template_id", "warnings": [] }` |
| `POST` | `/templates/{key}/preview` | `{ "sample": "order|checkout|subscriber" }` → rendered HTML with sample data (feeds your preview modal) |
| `POST` | `/templates/{key}/test` | `{ "to": "name@evolutiongolf.co.uk" }` → real send, **staff domain only** |
| `DELETE` | `/templates/{key}` | only if no enabled flow references it |

**Tokens** (Go templates, Listmonk transactional). `.Tx.Data` is the render context; subject is a template too.

| Klaviyo | Evoflows |
|---|---|
| `{{ first_name\|default:'there' }}` | `{{ if .Tx.Data.first_name }}{{ .Tx.Data.first_name }}{{ else }}there{{ end }}` |
| `{% for item in event.extra.line_items %}…{{ item.product.title }}…{% endfor %}` | `{{ range .Tx.Data.items }}…{{ .title }}…{{ end }}` (`.title .variant .qty .price .image .url`) |
| `{{ event.extra.checkout_url }}` | `{{ .Tx.Data.recovery_url }}` |
| `{{ event.extra.order_number }}` / order total | `{{ .Tx.Data.order.name }}` / `{{ .Tx.Data.order.total }}` |
| `{% unsubscribe %}` / `{{ unsubscribe_link }}` | `{{ .Tx.Data.unsubscribe_url }}` — **required**; push is rejected without it |
| `{{ organization.name }}` | literal text |
| any `{% ... %}` block tag | not accepted — push returns `400 klaviyo_tags_present` with the offending tags |

Rules we enforce on push: unsubscribe token present; HTML ≤ 200 KB; images on `cdn.shopify.com` or
`evolutiongolf.co.uk` only; links get UTM + `egid` appended by the engine (don't add your own UTM); no `<script>`.
Discount codes are **data** (`{{ .Tx.Data.discount_code }}`), set per step in the flow, never hard-coded in HTML.

## 6. Events, runs, metrics, webhooks

### 6.1 `POST /events` — push a trigger
```json
{ "type": "custom", "event_name": "membership_changed", "email": "sam@example.com",
  "occurred_at": "2026-10-09T13:30:00Z", "idempotency_key": "portal:tier:48213:2026-10-09",
  "data": { "tier": "annual", "previous": "free" } }
```
→ `202 { "accepted": true, "runs_started": ["f2_annual:1234"] }`. Also accepted for `order_placed` /
`order_fulfilled` if you hold Shopify webhooks and want second-level latency (we de-dupe against our polling by
Shopify id).

### 6.2 Runs
| Method | Path | Does |
|---|---|---|
| `GET` | `/runs?flow=&status=active\|done\|exited&email=&since=&limit=` | list with current step, next due, exit reason, order |
| `GET` | `/runs/{id}` | full timeline: every step, sent/skipped/when, consent result, exit |
| `POST` | `/runs/{id}/exit` | `{ "reason": "manual" }` — stop one person |
| `GET` | `/contacts/{email}` | consent state, lists, active runs, last sends — the "can we email this person?" answer |

### 6.3 `GET /metrics`
`/metrics?flow=&period=30d|90d|365d&by=step|week` →
```json
{ "flow": "f9_after_delivery", "period": "30d",
  "totals": { "enrolled": 412, "active": 38, "finished": 290, "exited": 84,
              "sent": 1130, "delivered": 1118, "bounced": 9, "complained": 1, "unsubscribed": 6,
              "refused_no_consent": 11, "converted": 57, "converted_after_email": 49, "revenue": 6421.40,
              "conversion_rate": 0.119, "unsubscribe_rate": 0.0053, "bounce_rate": 0.008 },
  "steps": [ { "id": "e1h", "sent": 210, "delivered": 208, "bounced": 2, "unsubscribed": 1,
               "converted_after": 14, "revenue_after": 1890.00 } ],
  "weeks": [ { "week": "2026-09-29", "sent": 260, "converted_after_email": 11, "revenue": 1412.00 } ] }
```
**Honest limits.** `converted` = an order by that contact after enrolment (purchase-exit); `converted_after_email` =
an order after at least one real send — that is the number to call "flow revenue". **Opens and clicks are not
available in v1**: Listmonk's transactional API doesn't track them. Phase 2 adds the engine's own pixel + link
redirect (`open_rate`, `click_rate` fields appear then; they will be absent, not zero, until that ships).

### 6.4 Webhooks (us → you)
`PUT /webhooks` `{ "url": "https://…railway.app/evoflows/hook", "secret": "…", "events": ["*"] }`.
We POST `{ "event", "at", "flow", "run_id", "email", "step", "data" }` with header
`X-Evoflows-Signature: sha256=<hmac of body>`. Retries with backoff for 24h on non-2xx.
Events: `run.started run.done run.exited step.sent step.skipped contact.unsubscribed contact.bounced
contact.complained template.updated flow.enabled flow.disabled`.

## 7. Build plan and who does what

| Step | Who | Notes |
|---|---|---|
| 1. Fix the cookie pop-up (your handover doc, option 1 or 2) | you / theme | unblocks onsite tracking for everyone |
| 2. Engine: step-graph executor, conditions, `order_placed`/`order_fulfilled`/`subscribed`/`custom` triggers, send windows, API + tokens, metrics, webhooks, Flows table in admin | Evoflows (Luke/Claude) | ~3–5 days; stays stdlib Python on the existing server |
| 3. Your app: "Evoflows" target on Approve — pack → flow JSON + templates; token-translate HTML; `/metrics` as the data source; webhook receiver | you | start from F9 (post-purchase) — F3 is already on Evoflows |
| 4. Seed test F9 with staff orders (accelerated waits), then enable; switch the Klaviyo flow off the same day | both | same gate every flow goes through |
| 5. Then F1 welcome (needs `subscribed` trigger), F2 membership (needs `custom` events from the portal), F12/F13 (conditions on `customer.days_since_last_order`) | both | per the programme's build order |

**Questions for you before we build:** (1) Can your app export a pack as the flow JSON above, or do you want us to
accept your outline format and compile it? (2) Can you pull the current template HTML out of Klaviyo for the
packs, or should we start from the `emails/` sources in this repo? (3) Which custom events exist today (membership
tier change from the portal?) and who can push them?

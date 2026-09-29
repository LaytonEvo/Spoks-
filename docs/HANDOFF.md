# Handoff — 29 Sep 2026

## Where we are
- Phase 0 done for Spoks (`docs/00-spoks-capabilities.md`). Spoks can build flows but not good designs; Components/Canva routes failed.
- Platform research + decision doc: `docs/Evolution Golf - Email platform decision.pdf` (+ .docx), notes in `docs/research/`.
- Klaviyo bill is **£250/month**. Decision: **stay on Klaviyo short term.**
- Klaviyo's own MCP can read flows and create templates/universal content, but **cannot create flows**.
- Layton has connected **Windsor.ai** (Shopify + Klaviyo sources) and added the Windsor MCP to Claude. Windsor's Klaviyo connector
  claims to create flows in **Draft** from a definition (trigger = metric event or list; steps = time-delay, send-email, send-sms,
  conditional-split, linked by temporary_id) and to change flow status. Limits (from Klaviyo's beta create-flow API it wraps):
  no segment triggers, no A/B, structure not editable after creation, ~100 creations/day.

## Next task: Windsor test on ONE flow
Build **EG · F3 Checkout abandonment · Trolleys (TEST)** in Klaviyo as a Draft, per Build Pack §3.3 (Trolleys path):
- Trigger: Checkout Started; trigger filter $value ≥ 30 (if supported).
- Flow filters: Placed Order zero times since starting this flow; (bounce/in_abandon_flow filters if supported — note gaps).
- Trolley routing: conditional split on the event's Collections property (Route B, pack §2.1) — trolley collection names are
  [CONFIRM]; read a real Checkout Started event's properties via the Klaviyo MCP (get_events) to get exact values. flow_cat tags are not
  yet on products.
- Steps: 1h delay → E1 "Basket saved" → 1 day then 09:30 → member split (MemberTier / Shopify tags `Free`,`Club`,`Evolution Pro`,
  `Evolution Annual` — check how they appear in Klaviyo) → E2 / E2m → day-2 18:00 → SMS consent split → SMS 1 → day 3 09:30 → E3 (from Alex).
- Email content: verbatim pack copy; `[CONFIRM: …]` left visible; smart sending ON; no coupons on this path.
- Prefer creating branded HTML templates with the Klaviyo MCP and attaching them; if Windsor can't attach templates, record how content
  must be set and tell Layton.

## Report back to Layton
Flow link, what Windsor could and couldn't set (splits, time-of-day, filters, templates, smart sending, SMS), every deviation from the
pack, and a recommendation on building the other flows this way. Then stop.

## Windsor `create_flow` — confirmed schema (29 Sep, via list_actions)
- Windsor accounts connected: **Shopify only — Klaviyo not yet connected** (Layton to add it in Windsor).
- Trigger: `metric` (metric_id + optional `trigger_filter`) or `list` (list_id). No segment trigger.
- Flow-level `profile_filter` (optional).
- Steps: `time-delay` (unit minutes/hours/days/weeks — **no time-of-day "send at 09:30"**), `send-email` (**template_id of an existing
  Klaviyo template**, `from_email`, `from_label`, `subject_line`, `smart_sending_enabled`), `send-sms` (inline body),
  `conditional-split` (`profile_filter`, next_if_true / next_if_false). **No trigger split, no update-profile-property step, no A/B.**
- Created in Draft. `update_flow_status` exists (draft/manual/live) — **never call it.**
- So: templates via the Klaviyo MCP (`create_email_template`), then Windsor `create_flow` referencing them. Per-email sender
  ("Alex at Evolution Golf") IS possible. Category routing must use the metric `trigger_filter` (one flow per path) because splits are
  profile-only.

## F3 Trolleys (TEST): status 29 Sep 2026

- Klaviyo templates created (CODE editor, drafts): E1 `THeprK`, E2 `WqkQJ7`, E2m `WS7nDW`, E3 `Sf6hhp`.
  Source: `klaviyo/templates/` (generator `klaviyo/build_templates.py`). E1 test-rendered OK in Klaviyo.
- Flow definition ready: `klaviyo/flows/f3-trolleys-test.json` (Windsor `create_flow`, account `SiyYRR`).
- **Blocked:** Windsor rejected `execute_action`: write actions are disabled for the Windsor user.
  Layton to enable under Windsor Settings > API Access ("Enable write actions for Claude, ChatGPT & API"), then re-run with that JSON unchanged.
- Unverified filter shapes (first attempt will tell): `$value` `greater-than-or-equal` in trigger filter; `MemberTier` `existence/exists` split.

## 29 Sep 2026 (later): paused building, working on design + content first (Layton's call)

- Decisions: promote the £36/yr Evolution Golf Membership in abandonment emails; evolve the current email look
  (don't redesign); imagery = Shopify product photos + existing Klaviyo images + Layton's lifestyle photos;
  review via preview page + copy deck.
- Copy deck (Claude Doc): https://claude.ai/code/artifact/d7f53e2a-2546-4994-8ae6-bf64cfc72477 (F3 Trolleys E1/E2/E2m/SMS/E3, facts table, open questions).
- Hero product for mock-ups: Motocaddy 2026 M1 DHC Standard Lithium, £799 (gid://shopify/Product/8502252830978).
- Blocked for design previews: sandbox can't fetch d3k81ch9hvuctc.cloudfront.net (Klaviyo images), cdn.shopify.com, evolutiongolf.co.uk.
- Next: master email design (evolved from live template XhSB6r) + preview page, after copy sign-off.
- Design options preview (A Clubhouse / B On the course / C Letter, on F3 Trolleys E1): https://claude.ai/artifact/9KL6Zw1qgmFaJMxWe5pt2u
  Source: `klaviyo/design/build_options.py` + `preview_template.html` (needs the scratchpad image folder; images: logo 07b49b80…, roundel 4aa15d13…, lifestyle 648eead5…).
  Brand gold from the logo: #B2893F (pack's #F1DA01 yellow isn't in any live asset). M1 DHC main Shopify photo carries a "FREE GIFT" badge.
- **Design B chosen** (29 Sep). F3 Trolleys E1/E2/E2m/E3 built in B: `klaviyo/design/build_f3_b.py` + `f3_b_template.html`
  → preview (same URL as above, v2) and live-URL HTML in `klaviyo/design/f3-b/<email>-<slots|now|none>.html`.
  Image slots: H1 E1 hero (stop-gap 490px), V1 E1 video still (needed), H2 E2/E2m hero (stop-gap: M1 folded product shot),
  M1 E2 membership still-life (stop-gap "member access" image, shows The Open logo — rights?), A1 Alex headshot (needed, optional), P1 dynamic product photos (badge-free).
  Every email works in "none" mode (no new images). Not yet created in Klaviyo.
- **Layton's copy answers (29 Sep, in the copy deck):** member 10% applies to trolleys and to a basket already waiting;
  Klarna + Clearpay confirmed; members link https://evolutiongolf.co.uk/pages/members-page; warranty line only for Motocaddy
  (Klaviyo `{% if …vendor == 'Motocaddy' %}`); no in-house videos → link to YouTube search (V1 slot dropped);
  Trustpilot 4.8 / 611 (re-check quarterly); battery range advice OK; info@ read daily; batteries/chargers not in trolley flow
  (removed from `klaviyo/flows/f3-trolleys-test.json`). Still open: trade-in quote URL + accepted brands; which free-delivery threshold for other flows.
  To verify at build: Klaviyo accepts `|urlencode` and `product.vendor` on the Checkout Started line items (render API).

## 29 Sep 2026 (latest): F3 Trolleys draft flow built
- Flow UXsJ3d (draft) + master templates Sc4LsT / VC22MY / W3wixR / VjRZzQ. Full details and the UI to-do list: `docs/03-build-log.md`.
- Flow definition: `klaviyo/flows/f3-trolleys.json` (MemberTier split uses `existence` / `is-set`).

## 29 Sep 2026: read-only flow dashboard (Phase 1)
- App in `dashboard/` (FastAPI + vanilla JS). Reads Klaviyo flows, per-message performance (30d/90d/12m), renders emails
  with an example basket, runs rule-based checks, Claude reviews (`claude-opus-5-5`, structured output), team notes. Never writes to Klaviyo.
- Runs on saved test data (`dashboard/fixtures/`, 18 flows + 90-day report) until `KLAVIYO_API_KEY` is set. See `dashboard/README.md`.
- Not yet deployed. Needs: Klaviyo read-only private key, dashboard password, Anthropic API key (reviews), Railway service with a /data volume.
- Unverified until first live run: Klaviyo `revision` (default 2025-10-15) accepting `additional-fields[flow]=definition`; review call (no API key here to test).

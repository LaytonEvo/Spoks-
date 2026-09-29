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

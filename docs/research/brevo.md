# Brevo research (28 Sep 2026, web search snippets only — vendor pages blocked)

- **Price:** Standard plan needed (Starter caps automation at 2k contacts). ~$100–129/mo for 60–100k emails/month (100k ≈ $129). 46k contacts fits (cap 500k from the 20k-email tier). Professional from $499/mo. UK SMS ≈ £0.04 per message, prepaid credits. https://www.sendx.io/blog/brevo-pricing-plans-costs-alternatives-2026 · https://help.brevo.com/hc/en-us/articles/208589409-About-Brevo-s-pricing-plans
- **Automations: UI only** — no public API to create/edit workflows. https://community.brevo.com/t/api-reference-for-automation/2895
- **Official MCP** (contacts, lists, segments, campaigns, templates, SMS, CRM…) — **no automations module**. https://developers.brevo.com/docs/mcp-protocol
- **Templates with full custom HTML via API: yes** (`POST /v3/smtp/templates`, htmlContent). https://developers.brevo.com/reference/create-smtp-template
- **Saved sections "Save & sync"** update all templates/draft campaigns using them. https://www.brevo.com/releases/sync-sections/
- **Coupons:** unique codes from uploaded "coupon collections"; **one fixed expiry date per collection** (no per-recipient rolling expiry). https://community.brevo.com/t/dynamic-coupon-expiration-date/1644
- **Shopify:** old Brevo app retired → **Brevo PushOwl** app. Syncs customers, products, collections, orders, cart updates, fulfilment, inventory. Tag/collection use in automation filters unconfirmed. "Delivered" not found. https://help.brevo.com/hc/en-us/articles/18720609955474
- **Automation:** conditional + percentage (A/B) splits, wait-until-event, schedule windows, re-entry, exit on event. Frequency cap including automations reportedly Enterprise-only.
- **Weaknesses vs Klaviyo:** shallower Shopify data, weaker recommendations/attribution, two-app split (Brevo + PushOwl), no workflow API.

# Klaviyo research (28 Sep 2026, web search only)

- Public API **can create flows**: `POST /api/flows` with a definition (one trigger, delays, email/SMS/push, webhooks, conditional splits; smart sending + UTM per message; **no A/B**). Created as Draft. Rate limit 100/day. Beta (2024-10-15.pre) — GA status unconfirmed. Flow **structure cannot be updated** after creation; message content can (template repoint via `PATCH /api/flow-actions/{id}`, per third-party source).
  Sources: https://developers.klaviyo.com/en/reference/create_flow · https://developers.klaviyo.com/en/reference/flows_api_overview · https://developers.klaviyo.com/en/v2024-10-15/reference/create_and_retrieve_flows
- Official **Klaviyo MCP cannot create flows** (read/report only); it can create templates, universal content, draft campaigns. Matches the connector in this session. https://developers.klaviyo.com/en/docs/klaviyo_mcp_server
- Klaviyo's own AI ("Flows AI" / "Composer") drafts flows from a prompt in the UI, credit-metered. https://help.klaviyo.com/hc/en-us/articles/53371629100571
- Universal content is **not usable in pure custom-HTML templates**; needs a "hybrid" template. https://help.klaviyo.com/hc/en-us/articles/115005254188
- Price ~46k active profiles: **~$720/mo email-only** (≈£535 + VAT), billed in USD; SMS extra. Billed on active (marketable) profiles since Feb 2025; suppressing unengaged lowers it next cycle. https://everboost.co.uk/insights/how-much-does-klaviyo-cost/ · https://help.klaviyo.com/hc/en-us/articles/33136281415451
- Shopify tags sync one-way as "Shopify Tags" list property; no direct tag-added trigger (segment-triggered flow or Shopify Flow event). https://help.klaviyo.com/hc/en-us/articles/115005080447

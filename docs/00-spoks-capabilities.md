# Phase 0 — Spoks capabilities and discovery

Run 25 Sep 2026 against the Spoks MCP, read-only apart from nothing (no create/update calls were made).
About 25 MCP calls over ~10 minutes; no rate-limit responses seen.

**Could not reach:** `help.spoks.com` (blocked by this session's network policy). Everything below comes from the MCP's own
tool schemas, the blueprints and live reads — not from the help centre. Items that only the help centre could settle are marked
**Unknown-needs-me**.

---

## 1. Account (`whoami`)

| Item | Value | Note |
|---|---|---|
| Login | online@evolutiongolf.co.uk | |
| Workspace | "Evolution Golf " (id `2745819a-e9db-41a1-8f76-442730a6a213`) | Only workspace. Name has a trailing space. |
| Shopify store | evolutiongolf.myshopify.com | ✅ correct store |
| Timezone | Europe/London | |
| **Plan** | **Free** | ⚠ see below |
| **Email sends** | 2 this month, **limit 5,000 / month** | ⚠ blocker for go-live |
| **SMS** | disabled in settings; 0 credits available; monthly limit 1 | ⚠ SMS steps can be drafted but will not send |

> ⚠ **Blocker for go-live (not for the draft build):** the Klaviyo programme sends well over 5,000 flow emails a month in season
> (audit: welcome alone ≈ 2,370 tail sends/90 days plus E1; post-purchase nurture 3,842/90 days before it was switched off),
> and campaigns share the same cap. The plan needs upgrading before cut-over, and SMS needs enabling + credits (and a UK
> sender set up) before any SMS step can go live.

## 2. Settings (`get_settings`) vs the brand spec

| Setting | Spoks now | Brand spec | Differs? |
|---|---|---|---|
| Sender name | `Evolution Golf ` (trailing space, no ⛳) | `⛳ Evolution Golf` | **Yes** |
| Sender email | **not set** (null) | info@evolutiongolf.co.uk | **Yes** — must be on a verified custom domain |
| Reply-to | help@evolutiongolf.co.uk | (pack Q18: monitored inbox for Alex emails) | Check — pack assumes info@ |
| Per-email sender ("Alex at Evolution Golf") | **Not settable per campaign via MCP** (no sender field on `draft_campaign`) | Personal emails from "Alex at Evolution Golf" | **Gap** — see §8 |
| Locale | en-GB, Europe/London | UK | OK |
| Primary colour | #006747 | #006747 | OK |
| Background | #FAFAFA | #FAF7F1 cream | Yes |
| Header bar | #FAFAFA | #003D27 dark green | Yes |
| Footer | #006747 bg / #FFFFFF text | (not specified) | — |
| Link colour | null (inherits) | #006747 | Yes (minor) |
| Title text | #000000 | #003D27 | Yes |
| Heading font | Noto Sans 400 (web-safe fallback Arial) | Fraunces (fallback Georgia) | **Yes** |
| Body font | Noto Sans (fallback Arial) | Inter (fallback Arial) | **Yes** |
| Button radius | 4 | 6 | Yes |
| Logo (email header) | `storage.spoks.com/.../b5493a63-332f-4c9b-9a5f-1f466389b6af.png`, width 100, centred | ≤160 px, centred | OK |
| **Logo link URL** | **`https://www.evolu`** (truncated) | https://evolutiongolf.co.uk | **Yes — broken link on every email** |
| Footer text | "Evolution Golf, Unit 3 Parvaneh Park, Embankment Way, Ringwood, Hampshire, BH24 1WL, United Kingdom" + "Unsubscribe" + FB/IG/YouTube | Pack Ch 4 footer: company name, address, **company number**, unsubscribe, manage preferences, "You're receiving this because…" | Company number and "why you're receiving this" missing; no manage-preferences link concept seen |
| Custom-field personalisation tokens | none configured | — | MemberTier is not a field — it is a **tag** (see §6) |

`update_settings` exists in the MCP but I have **not** used it: which of the above wins is your call, and it restyles every
published campaign. Font families are validated against the workspace font list, so Fraunces/Inter may or may not be
selectable — **Unknown-needs-me** (try in Settings → Looks).

## 3. Blueprints (`get_flow_blueprints`) — what they teach

| Blueprint | Trigger event | Trigger contact filter | Re-enrol | Steps |
|---|---|---|---|---|
| welcome_flow | `contact_created` | `emailMarketingConsent in [subscribed]` | off | delay 0 → email → 3d → email → 4d → email |
| cart_abandonment | `abandoned_cart` | `lastCheckout lt __flow_triggered__` | P7D | 1h → email → 10h → email |
| checkout_abandonment | `checkout_created` | `lastPurchase lt __flow_triggered__` | on, no period | 1h → email → 10h → email |
| browse_abandonment | `product_viewed` | `lastCartUpdate lt __flow_triggered__` | P30D | 30m → email (dynamic recently-viewed products block) |
| thank_you_new_customer | `order_created` | `totalOrders lt 3` | on | delay 25h **`tilHour 09:00`** → email with **step filter** `totalOrders eq 1` → 2 min → email with step filter `totalOrders eq 2` |
| win_back_flow | `order_created` | `lastPurchase lt __flow_triggered__` | on | 30d → email |
| back_in_stock | `back_in_stock` | none | on | 0 → email |
| active_on_site | `page_viewed` | `lastCartUpdate lt __flow_triggered__` | P30D | 30m → email |

Key lessons:

- **"Before the flow started"** is expressed as `{"field":"lastPurchase","operator":"lt","value":"__flow_triggered__"}` (also
  works on `lastCheckout`, `lastCartUpdate`). This is how "no order since starting this flow" is done.
- **"Wait until 09:30"** exists: delay step `parameters.tilHour: "HH:MM"` (earliest local release time) plus optional
  `daysOfWeek`. So pack timings like "1 day, then 09:30" translate exactly.
- **Branching** = per-send-step `filter` (thank_you blueprint). Confirmed.
- Every send step must be **directly preceded by a delay step** (MCP rule). A delay of 0 is allowed.
- Templates in the blueprints use the legacy `{{firstName||there}}` syntax, but the MCP documents and enforces the newer
  syntax — use that (see §5).

## 4. Existing flows (`get_flows`) — none will be touched

All 12 are **inactive**, 0 enrolled, created 24 Sep 2026 (they look like a migration of the Klaviyo flows). None starts with `EG ·`.

| Flow | Channels | Posts |
|---|---|---|
| 1. SM: Welcome Sequence | email, sms | 9 |
| NEW: Browse Abandonment (category-routed) | email | 12 |
| NEW: Abandoned Checkout (category-routed) | email, sms | 30 |
| NEW: Abandoned Cart (category-routed) | email, sms | 24 |
| NEW: Post-Fulfillment | email | 26 |
| FLOW: Welcome — Club Access Member | email | 1 |
| 1.1 SM SMS Club Welcome | sms | 2 |
| FLOW: Welcome - Evolution Free | email | 1 |
| FLOW: Welcome — Evolution Pro Annual | email | 1 |
| NEW: Winback | email | 4 |
| FLOW: Welcome — Evolution Pro | email | 1 |
| NEW: Second-Order Conversion | email | 4 |

I read one (`NEW: Abandoned Checkout`) for step shapes only. It is one linear flow with all six paths laid end to end (60
steps), **no trigger or step filters** — so as imported it would send every path to everyone. It still carries the audit's
problems ("(placeholder)" names, "Text message #12", 5% then 5h delays). Recommend leaving all 12 inactive and never turning
them on; archive them in the app after cut-over.

## 5. Content model (from the `draft_campaign` / `update_draft_campaign*` schemas and blueprints)

**Personalisation tokens** — `{{ path }}` or `{{ path | default: 'fallback' }}`, single quotes, `default` is the only filter.

- Contact: `contact.name`, `contact.first_name`, `contact.last_name`, `contact.email`, `contact.phone`, `contact.city`, `contact.country`
  → use `{{ contact.first_name | default: 'there' }}`
- Custom fields: `contact.data.<fieldName>` (none configured in this workspace)
- Trigger data (seen in back_in_stock blueprint): `{{ trigger.product.title }}`, `{{ trigger.product.url }}`,
  `{{ trigger.variant.price }}`, `{{ trigger.variant.image }}` — other trigger paths are truncated in the tool description,
  **Unknown-needs-me** whether `trigger.product.*` exists on `product_viewed` / `order_delivered` / `order_created`.
- **Not allowed:** tokens inside any `url` / `urlRedirect` / `[label](url)` target, button labels, or image alt text. So
  Klaviyo patterns like "Take me to it → {{ event.ProductURL }}" or a subject/button with the product name need a different
  route (Products/abandonedCart blocks carry their own links).
- No unsubscribe / manage-preferences token exists: the footer is Spoks-managed. `customizedNotification.isOptOutEnabled`
  controls the opt-out footer (default **false** in the schema — must be set **true** on every marketing email).

**Block types the MCP can write** (JSON shapes recorded in §9):

| Block | MCP `type` | Notes |
|---|---|---|
| Text / heading / quote / list | omit type or `regular` · `h1` · `h2` · `quote` · `list` | Inline `**bold**`, `*italic*`, `__underline__`, `[label](url)` |
| Divider | `divider` | |
| Button / link | `link` with `style: button \| outlined`, `isFullWidth` | |
| Image | `image` with `fileId` (from `search_media` / `upload_media`), `altText`, `urlRedirect` | No hotlinking — must be in the media library |
| Video | `video` with `fileId` | |
| Form / Poll | `form` / `poll` with `formId` | One form exists: "Stay up to date with Evolution Golf" |
| Columns | `columns` (2–4, `flex`, `stackedOnMobile`, `verticalAlignment`) | |
| Section | `section` (container of blocks) | **Background colour/image is not settable via MCP** — styling is done in the editor, and is preserved on later edits if block ids are echoed |
| Coupon | `coupon` with `couponId` (from `discounts_search`) | Server fills the code; personalised coupons substitute the unique template |
| Products — manual | `products`, `selectionMode: manual`, up to 12 product ids | |
| Products — dynamic | `products`, `selectionMode: dynamic`, `dynamicCriteria: recently_viewed \| newest \| best_selling`, 1–6 items | **Flows only.** No "from collection" option via MCP. |
| Abandoned cart items | `abandonedCart` (one per post) | Only in flows triggered by `abandoned_cart` or `checkout_created`; real items + recovery link filled at send time |
| Abandoned cart button | `abandonedCartButton` | Same restriction; any number |

**Not available via MCP:** Components (saved reusable blocks), Personalisation block from the picker, per-block colours or
padding, Section background, sender name/email per email, A/B subject tests.

## 6. Contacts, tags and segments (`get_segments`, `search_contacts`, `preview_segment`)

Existing segments (all Spoks defaults): All contacts 21,575 · All subscribed **6,059** · All customers 16,157 · All repeat
customers 1,356 · VIP customers 304. **None uses membership.**

> ⚠ Klaviyo's main list is 46,334 profiles; Spoks has 6,059 email/SMS-subscribed contacts. Either consent didn't migrate or the
> list wasn't imported. **Unknown-needs-me.**

**Shopify customer tags do sync into Spoks tags** (observed: "Login with Shop", "Shop", "REPEAT_CUSTOMER", "requested refund",
"Wrote Judge.me email review", "EcomSend Popups").

**The membership app writes tier tags to the Shopify customer, and they are visible in Spoks:**

| Tag | Contacts | Klaviyo audit (MemberTier) |
|---|---|---|
| `EvoMember` | umbrella tag on every member | — |
| `Free` | 209 | 336 |
| `Club` | 103 | 107 |
| `Evolution Pro` / `Evolution Annual` | 10 combined (sample: 7 Pro, 3 Annual) | 7 / 3 |
| `ClubhouseMember` | seen on one Annual member — looks legacy | — |

So the audit's "contains" risk is real in a different form: tier tags are `Club`, not "Club Access", and `Free`/`Club` are
generic words. Filters must use exact tag membership (`tags in ["Club"]`), which Spoks does.

Tags and filters seen in the MCP schemas (the help-centre filter reference was unreachable):

| Need | Spoks field / operator |
|---|---|
| Email consent | `emailMarketingConsent in [subscribed]`; `emailMarketingCanReceive eq true` (consent + suppression) |
| SMS consent | `smsMarketingConsent in [subscribed]`; `smsMarketingCanReceive eq true` |
| Tags | `tags in / nin / nis` (exact names, no wildcard — so `member_*` in the prompt becomes an explicit list) |
| Orders | `totalOrders` (eq/gt…), `firstPurchase`, `lastPurchase`, `totalSpentAmount`, `purchasedProducts in [product uuid]` |
| Before flow start | `lastPurchase lt __flow_triggered__` (also `lastCheckout`, `lastCartUpdate`) |
| Engagement windows | `eventFilter` on `receivedEmail`, `openedEmail`, `clickedEmail`, `receivedSMS`, `clickedSMS` with `timeFilter` (ISO date or period, e.g. `P90D`) and optional `conditionFilter` (flowId, emailSubject, url…) |
| Category history | `eventFilter` on `orderedProducts`, `viewedProducts`, `checkoutStarted`, `orderFulfilled` with `conditionFilter` on `collectionName`, `productTags`, `productType`, `productVendor`, `productPrice`, `orderValue` |
| Coupon use | `eventFilter` `discountUsed` with `discountCode` |
| Bounce | **No bounce field or event.** Closest is `emailMarketingCanReceive eq true`. |
| Smart sending (16h) | `eventFilter receivedEmail eq 0` with `timeFilter gt <16h ago>` — **Unknown-needs-me** whether the period notation accepts hours (`PT16H`); days work (`P1D` as a fallback) |

## 7. Commerce data (`products_search`, `discounts_search`, `search_media`)

**Products** — the catalogue is synced. Each product has a Spoks `id` (uuid, used in blocks and filters), Shopify `externalId`
GID, title, price, url, vendor, image, `collectionExternalIds` (GIDs only — **no collection titles**). Samples:

- Motocaddy: 2025 EX-DISPLAY S1 Ultra Lithium £599 (active); 2026 M-Tech GPS Remote £1,699.99 (unlisted); accessory station £11.95; QB2 accessory bag £19.95
- Balls: TaylorMade 2026 TP5x PIX Double Dozen £84.95; Distance+ 3 dozen £45
- Shoes: Nike Air Max 90 G £144.95; Nike Victory Tour 4 £174.95

⚠ Product URLs come back as `https://evolutiongolf.myshopify.com/products/...`, not `evolutiongolf.co.uk`. Shopify redirects
these, but links in emails will show the myshopify domain. **Unknown-needs-me** whether Spoks can use the primary domain
(Settings → Custom domain / integrations).

Collection filters on triggers need **GIDs**. The Route B mapping (pack 2.1) has to be resolved title → GID; the Spoks MCP can
only do this indirectly (products → GIDs). The **Shopify MCP is also connected to this session** and can list collections with
titles and GIDs — I'll use it read-only in Phase 1 if you're happy with that.

**Discounts** — 100+ Shopify discounts sync into Spoks. The ones the pack retires:

| Code | Found | Type | Note |
|---|---|---|---|
| EVO5 | ✅ static 5%, min £30, once per customer, one collection | public | pack: stays in F1 E1 until T2 reads |
| EVO5 T | ✅ static 5%, min £30 | public | variant, not in pack |
| TROLLEY10 | ✅ static 10% | public | retire |
| TROLLEY7 | ✅ static 7% | public | not in pack — also a trolley code |
| BASKET5 | ✅ **personalised**, 5%, 3-day expiry, one use | Spoks dynamic coupon | retire |
| BASKET10 | ✅ **personalised**, 10%, 1-day expiry, one use | Spoks dynamic coupon | retire |
| SMSCLUB5 | ✅ static 5%, min £30 | public | retire |
| WINBACK5 | ❌ not found | — | may not have been created in Shopify |
| SECOND5 / SECOND10 | personalised 5% 30D / 10% 14D | Spoks dynamic coupon | second-order ladder — retire with flow 10 |
| FLOW5-7D / -10D / -14D | ❌ not yet created | — | you create these (§8) |

Spoks supports **personalised coupons with relative expiry** (`isPersonalized: true`, `dynamicExpiration: "3D"`), which is what
FLOW5-* needs. Also noticed: many public codes (SAVE25, TOUR20, stark 20%, Brad100 = 100%, JRS400 = £500 off) are active in
Shopify. Out of scope, but worth a look.

**Media library** — ~50 images, all UUID-named PNGs uploaded 24 Sep (the migrated templates' images). No named logo, product or
lifestyle set. The email header logo is set in Settings, so it doesn't need to be in content.

**Forms** — one active subscribe form, 0 submissions.

## 8. Capability questions

| # | Question | Answer | Evidence / consequence |
|---|---|---|---|
| 1 | Can the MCP create or edit **Components**? | **No** | No component tool and no component block type. Nor can it *reference* one. → Components must be created in the app **and inserted in the editor by you**, or I inline the block content in each email (loses single-source editing). **Your choice needed.** |
| 2 | Can the MCP create **coupons**? | **No** | No create tool; `get_links` → Coupons page in app. You create FLOW5-7D/-10D/-14D as **personalised** coupons (5%, min £30, excluding trolleys/clubs/used collections, one use, relative expiry 7/10/14 days); I then reference them by `couponId`. |
| 3 | Can a **Products block** filter by collection and exclude trolleys/clubs? | **No** (via MCP) | Dynamic modes are only recently_viewed / newest / best_selling; the app's "From collection" isn't in the MCP. → Cross-sell pairs = **manual** product picks (fits the pack's 3-products-per-variant design, swapped seasonally), or you switch the block to "From collection" in the editor. |
| 4 | Does **Order delivered** carry Collections filters? | **Yes (schema)** | Trigger-filter schema lists `collections` for product-carrying events and `orderTags` explicitly for `order_delivered`. Not shown in any blueprint — confirm with a test. |
| 5 | Do Shopify **customer tags** sync, and does the membership app write a tier tag? | **Yes / Yes** | §6. Tier tags `Free`, `Club`, `Evolution Pro`, `Evolution Annual` + `EvoMember`. **Unknown-needs-me:** whether the `New tag` (`contact_tags_added`) trigger fires when the tag arrives via Shopify sync rather than being added inside Spoks. Needs a test member. |
| 6 | **SMS consent** filter; where do **quiet hours** live? | Filter **Yes**; quiet hours **Unknown / app only** | `smsMarketingCanReceive`. `get_flow` returns an `executionWindow` field (null) — almost certainly the allowed-hours setting — but `create_flow`/`update_flow` can't set it. You set 08:00–20:00 in each SMS flow's settings. Moot until SMS is enabled on the plan. |
| 7 | Does **Cart abandoned** carry cart URL/items? How long until "abandoned"? | Items + link **Yes**; timing **Unknown-needs-me** | `abandonedCart` + `abandonedCartButton` blocks work for `abandoned_cart` and `checkout_created` flows. The idle time before Spoks fires `abandoned_cart` is in the help centre (blocked). |
| 8 | Can `add_flow_step` set a step's **filter** at creation? | **Yes** | Send steps take `parameters.filter` (contact filter) and `parameters.triggerFilter` (event filter). There is also a standalone `filter` step type ("only continue if"). |
| 9 | Can a flow send step **A/B test** subjects? | **No** (not via MCP) | No variant fields. → Subject B goes in the step name suffix `[B: …]` as planned. |
| 10 | "**Wait until 09:30**" | **Yes** | Delay `tilHour`. |
| 11 | Re-enrolment | **Yes**, with a limit | `reenrollEnabled` + `allowReenrolmentAfter` (P7D…). **Not allowed on `contact_tags_added`** — tag-triggered flows enrol a contact once, ever. Matters for flow 2 (a member who cancels and rejoins won't re-enter) and 12/13 (bands). |
| 12 | Per-email **sender** ("Alex at Evolution Golf") | **No** (via MCP) | Workspace-level sender only. **Unknown-needs-me** whether the editor allows a per-post sender. If not, every "from Alex" email goes out as "⛳ Evolution Golf" and only the copy/sign-off is personal. |
| 13 | Does the `filter` step exit a non-matching contact, or skip? | **Unknown-needs-me** | Schema only says "filter". I'll treat it as "only continue if" (exit) and confirm with you before relying on it. |

## 9. Observed request/response shapes (for later phases)

```jsonc
// create_flow
{ "storeId": "2745819a-e9db-41a1-8f76-442730a6a213",
  "name": "EG · F3 Checkout abandonment · Trolleys",
  "trigger": { "event": "checkout_created",
               "filter": { /* contact filter = suppression */ },
               "triggerFilter": { "type":"filter","field":"collections","operator":"in","value":["gid://shopify/Collection/…"] } },
  "reenrollEnabled": true, "allowReenrolmentAfter": "P7D" }
// trigger events: contact_created, contact_unsubscribed, form_submission, contact_tags_added, checkout_created,
//   order_created, abandoned_cart, product_viewed, page_viewed, order_delivered, back_in_stock
// triggerFilter fields: externalId, collections (GIDs), vendor, variantId, orderTags (order_created/order_delivered),
//   tags (contact_tags_added), formId, and numeric itemQuantity / lineItemCount / totalPrice (gt/gte/lt/lte/eq)
//   -> "$value ≥ 30" = {"field":"totalPrice","operator":"gte","value":30}

// add_flow_step — delay
{ "type":"delay", "parameters": { "delay": 86400000, "tilHour": "09:30", "daysOfWeek": [1,2,3,4,5] } }
// add_flow_step — email (always created disabled; returns postId + postHash)
{ "type":"publish_flow_post_to_contact",
  "parameters": { "filter": { /* contact filter */ }, "triggerFilter": null } }
// other step types: publish_flow_sms_to_contact, add_tag_to_contact {tags:[…]}, remove_tag_from_contact {tags:[…]},
//   call_webhook {url, headers}, send_internal_email {text, receivers}, filter {filter, triggerFilter}

// contact filter node shapes
{ "type":"filter","field":"tags","operator":"nin","value":["eg_abandon_checkout"] }
{ "type":"filter","field":"lastPurchase","operator":"lt","value":"__flow_triggered__" }
{ "type":"eventFilter","field":"receivedEmail","operator":"eq","value":"0",
  "timeFilter":{ "type":"filter","field":"receivedEmail","operator":"gt","value":"P1D" } }
{ "type":"eventFilter","field":"orderedProducts","operator":"ge","value":"1",
  "conditionFilter":{ "type":"filter","field":"collectionName","operator":"in","value":["…"] } }
{ "type":"conjunction","operator":"and","isGrouped":true,"filters":[ /* 2–15 nodes, ≤3 levels */ ] }
// values are always strings ("0", "true"); a single condition is passed bare, never as a 1-item conjunction

// update_draft_campaign (flow post) — needs postId, flowId, currentHash (from add_flow_step or get_campaign)
{ "postId":"…","flowId":"…","currentHash":"…",
  "postData": { "title":"F3 Trolleys E1 – Basket saved",
    "customizedNotification": { "emailTitle":"<subject>", "emailDescription":"<preview>", "isOptOutEnabled": true },
    "blocks": [ {"type":"h1","text":"…"}, {"text":"…"}, {"type":"abandonedCart","buttonText":"Back to my basket"},
                {"type":"link","style":"button","text":"…","url":"https://…","isFullWidth":true} ] } }

// dynamic products block (flows only)
{ "type":"products","selectionMode":"dynamic","dynamicCriteria":"recently_viewed","dynamicProductsCount":3,
  "productVisibilitySettings":{"isImageVisible":true,"isTitleVisible":true,"isPriceVisible":true,"isButtonVisible":true,
  "isDescriptionVisible":false,"isOriginalPriceVisible":false},"buttonText":null,"alignment":"center" }
```

Useful app links (`get_links`): flow editor `https://app.spoks.com/evolutiongolf/flows/{flowId}` (activation is only done
there), coupons `…/content/coupons`, looks `…/settings/look`, email & SMS `…/settings/email-sms`, custom domain
`…/settings/custom-domain`.

## 10. Consequences for Phase 1 (preview — not decided yet)

1. **No bounce filter** → pack "Bounced Email zero times in 30 days" becomes `emailMarketingCanReceive eq true` (approximate).
2. **Tier routing is by tag**, and tags already sync → flow 2 can trigger on `contact_tags_added` with `triggerFilter tags in
   ["Club"]` etc. No Shopify Flow workaround needed, *if* question 5's trigger test passes.
3. **Tag-triggered flows can't re-enrol** → a tier-change/re-join path (pack 2b) needs a different design; I'll propose one.
4. **Components can't be made or placed by the MCP** → biggest single design decision (question 1).
5. **"From Alex" sender** may be impossible per email (question 12).
6. **Free plan: 5,000 emails/month and no SMS** → fine for a draft build; blocks go-live.

## 11. Component test (25 Sep) — "EG · Component source – Tier table"

Draft campaign `b01c1aa5-09ce-47a6-b524-e74816092d6c` (not in a flow, never sent):
https://app.spoks.com/evolutiongolf/post/b01c1aa5-09ce-47a6-b524-e74816092d6c/edit — copy in `content/components/tier-table.md`.

Findings from the MCP side:
- **Columns nested inside a Section save empty.** The call succeeds, the plain-text summary contains the copy, but every
  column's `blocks` array comes back `[]` from `get_campaign`. Rebuilt as a Section of stacked text blocks, which saved intact.
  Rule for Phase 2: no Columns inside Sections via the MCP (top-level Columns still untested).
- `isFullWidth` on a `link` button is not echoed back — may be ignored; set full width in the editor.
- Link URLs are rewritten to a tracked `r.spoksmail.com` redirect (expected).
- A plain `\n` inside a text block is kept as a line break.

Waiting on Layton (in the editor): can the Section be styled (cream background) and saved as a Component, and can that
Component then be inserted into another email?

## 12. Workspace looks applied (25 Sep, approved by Layton)

`update_settings` with acknowledgement. Impact at time of change: 0 published web posts, 0 scheduled, 0 active flows.

| Setting | Before | After |
|---|---|---|
| Background / header | #FAFAFA / #FAFAFA | #FAF7F1 / #FAF7F1 |
| Title text / heading colour | #000000 / off | #003D27 / on (#003D27) |
| Body text on surface | #000000 | #1E1E1E |
| Link | inherit | #006747 |
| Heading font | Noto Sans 400 (Arial) | Fraunces 600 (Georgia) — accepted |
| Body font | Noto Sans (Arial) | Inter (Arial) — accepted |
| Button radius | 4 | 6 |
| Logo link | `https://www.evolu` (broken) | https://evolutiongolf.co.uk |

Unchanged: content surface stays white (#FFFFFF) on the cream page; footer #006747/white; sender name/email (still not set).

Tier table layout v2 uses top-level Columns (2×2 tier cards) — these save correctly; only Columns *inside* a Section fail.

## 13. Help-centre findings (help.spoks.com reachable from 25 Sep, later in the session)

- **Components** are created only in Content → Components → Create component (pop-up, no URL). Inserted via the Components
  block; editing updates every email; can be detached. Not visible to the MCP at all (not listed by `search_campaigns`).
- **No design import.** No HTML/code block. The Klaviyo migration copies flows only; the article says templates must be
  recreated in the Spoks editor "instead of arriving as a Klaviyo layout". Imported images only.
- **Templates:** any campaign or flow email step can be "Save as template" (three-dot menu) and new campaigns created from it
  in the app. The MCP cannot create a post from a template.
- **Styling:** Section → Looks override → Background colour / image, border, radius, inner padding. Every block has a Looks
  override (text colour, margins, max width). Email width fixed at 600px.
- **Pricing correction:** free under 1,000 Shopify contacts (5,000 sends/month); **$35/month above that** — the paid plan has no
  monthly send cap (per `whoami` notes). So the go-live blocker in §1 is the $35 subscription, not a volume limit. SMS is
  credit-priced separately.

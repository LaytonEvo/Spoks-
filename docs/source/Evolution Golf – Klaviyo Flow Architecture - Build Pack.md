Evolution Golf

**Klaviyo Flow Architecture: Build Pack**

Implementation pack for the 13-flow architecture proposed in Section E
of the Klaviyo Flow Audit (25 September 2026)

Prepared for: Layton (owner) · Built by: Karin · Copy sign-off: Alex,
Head of Ecommerce

Version 1.0 · 25 September 2026 · UK spelling, GBP

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>How to use this pack</strong></p>
<p>Chapter 1 gives the phased build order. Chapter 2 holds the rules
every flow obeys — read it once, refer back often. Chapter 3 has one
chapter per flow, each with sections a–i and boxed copy that can be
pasted into Klaviyo. Chapters 4–6 hold the universal blocks, the test
plan and the open questions.</p>
<p>[CONFIRM] marks any claim not verifiable from the audit (warranty
length, delivery times, URLs, property names). Nothing marked [CONFIRM]
goes live until it is confirmed.</p>
<p>Nothing in this pack asks for anything to be deleted. Archive only
after exporting the report and screenshotting the flow.</p></td>
</tr>
</tbody>
</table>

Contents

1\. Summary and build order

1.1 What this pack is

This is the build-ready version of Section E of the 25 September 2026
Klaviyo audit. It gives Karin and Alex click-by-click instructions for
13 flows (plus one small companion flow explained below), draft copy
that can be pasted straight into Klaviyo, and the rules that stop flows
colliding. It is written so no further strategy input is needed; where a
decision is still Layton's, it is listed in Chapter 6.

**Where this pack follows the audit rather than the brief:**

- Email 2 timing (audit QW1): the brief allows smart sending to be
  switched off on a message. This pack uses the audit's Option 2 instead
  — every second message waits until the next morning (≥16h) with smart
  sending kept on. Reason: switching smart sending off on abandonment
  emails is exactly what makes them collide with welcome and campaign
  sends. Smart sending is off only on Order Confirmation and Back in
  Stock, where the message is time-critical and expected.

- Post-delivery trigger (audit S3): Delivered Shipment is the primary
  trigger; Fulfilled Order is the fallback if Delivered Shipment volume
  proves unreliable in the first two weeks.

- Membership (audit N4 and Section E): Section E asks for one flow with
  four tier branches. A Klaviyo flow has one trigger, and a segment
  trigger does not re-fire when a Free member upgrades to Club. So this
  pack builds flow 2 as the single new-member flow with tier branches,
  plus a small companion flow 2b that catches later upgrades (and
  downgrades to Free). That is 14 live flows, not 13, and it is the
  honest minimum.

**Where this pack says "not yet":** Price Drop (flow 7) and
Replenishment (flow 11) are fully specified but gated. Price Drop
depends on onsite tracking being fixed and the Klaviyo catalogue being
synced. Replenishment depends on there being enough repeat balls/glove
buyers to matter — the audit had no volume data for consumables. Both
gates and what would open them are in the flow chapters.

1.2 What the audit says is at stake

| **Item**                                             | **Audit figure**                                                          | **What this pack targets**                                                                                                                                                    |
|------------------------------------------------------|---------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Flow revenue, last 12 months                         | About £110k, ~8% of £1.35M                                                | Email at ≥15% of revenue within 12 months (bottom of Klaviyo's 15.4–32.4% peer range) — roughly +£90k, of which flows are the larger share. This is a target, not a forecast. |
| Abandonment mechanical faults                        | Worth ~£10–15k/yr (audit)                                                 | Fixed in Week 1 before anything else is built                                                                                                                                 |
| Retention gap (second order, winback, back in stock) | Worth ~£15–30k/yr (audit)                                                 | Flows 6, 9, 10, 12 live by Week 8                                                                                                                                             |
| Welcome dependency                                   | 55% of flow revenue; Email 1 is 75% of welcome email revenue              | Keep Email 1 untouched in Phase 1; cut the dead tail; bring unsubscribe from 1.51% towards the 0.73% peer median                                                              |
| Membership                                           | 336 Free, 107 Club, 7 Pro, 3 Annual; target 1,000 members, churn 10% → 5% | Free upgrade emails live Week 1; paid onboarding and pre-renewal recap live Week 3                                                                                            |
| Compliance                                           | Hard-coded unsubscribe; false expiry on static codes; spam 2.3× peers     | Fixed Week 1, checked in every QA list                                                                                                                                        |

1.3 Build order (phased)

Rule for every phase: **nothing is deleted.** Before a flow is archived
or set to Manual, export its report (Analytics → Flows → export CSV) and
screenshot the flow canvas and each message's settings into the shared
drive folder "Klaviyo archive 2026". Only then archive.

Week 1 — fixes (no new flows)

| **\#** | **Action**                                                                                                                                                                                                                                                                                                   | **Owner** | **Switch off / archive at this step**                                                          |
|--------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------|------------------------------------------------------------------------------------------------|
| W1.1   | Master template: replace hard-coded unsubscribe with {% unsubscribe %} and add {% manage_preferences_link %}. Open every live template in the "NEW" family (cart, checkout, browse, post-fulfilment, second-order, winback, membership) and fix each clone. Tick off on the template register (Chapter 2.5). | Karin     | Nothing                                                                                        |
| W1.2   | Remove every "expires" claim tied to a static code (EVO5, TROLLEY10, BASKET5, BASKET10, SMSCLUB5, WINBACK5) in live emails and SMS. Where a message loses its reason to exist without the claim, set it to Manual for now.                                                                                   | Karin     | Set to Manual: welcome "EVO5 expires soon" SMS; checkout SMS 2 (BASKET10); cart SMS (BASKET10) |
| W1.3   | Cart: point every CTA in all cart templates to https://evolutiongolf.co.uk/cart and add a dynamic product block from the Added to Cart event (Chapter 2.4). Check all 18 cart templates for the cloned checkout_url link.                                                                                    | Karin     | Nothing                                                                                        |
| W1.4   | Cart, checkout, browse: move every Email 2 to a "1 day" delay followed by "send at 09:30" (keep smart sending on). Do the same for Email 3 → 2 days at 09:30.                                                                                                                                                | Karin     | Nothing                                                                                        |
| W1.5   | Welcome: end the three A/B tests started 25 Feb 2026; keep the variant with the higher click rate. Set Email 5, "Welcome Email Additional" and SMS \#2 to Manual (they earned £0–£248 in 90 days). Leave Email 1 exactly as it is.                                                                           | Karin     | Set to Manual: Welcome E5, Welcome Additional, SMS \#2, "EVO5 expires soon" SMS                |
| W1.6   | Tracking investigation (Chapter 2.7 checklist). Cart and browse stay live on current volume until this is done; do not rebuild them before it is.                                                                                                                                                            | Alex      | Nothing                                                                                        |
| W1.7   | Membership Free: proof and set live the two draft upgrade emails (with the copy in flow 2 if preferred). Change all four membership segment definitions from "contains" to "equals" once the MemberTier values are confirmed.                                                                                | Karin     | Nothing                                                                                        |
| W1.8   | SMS Club Welcome: turn quiet hours on both texts; add flow filter "Placed Order zero times over all time"; fix the missing space. This flow is retired in Week 2.                                                                                                                                            | Karin     | Nothing yet                                                                                    |
| W1.9   | Checkout routing: add "Irons" to the Clubs split; remove the duplicate "All Approved Used Golf Clubs" condition. Rename the 24 "(placeholder)" messages and "Text message \#12".                                                                                                                             | Karin     | Nothing                                                                                        |
| W1.10  | Shopify: check whether Shopify's own order confirmation notification is on. If it is, decide which one to keep (Chapter 6, Q6).                                                                                                                                                                              | Alex      | Nothing                                                                                        |
| W1.11  | Add the flow_cat tag to products in Shopify (Chapter 2.1). Start with trolleys, clubs, balls; finish the rest during Weeks 2–3.                                                                                                                                                                              | Alex      | Nothing                                                                                        |

Weeks 2–4 — core flows

| **Week** | **Build**                                                                                                                                                                                                | **Switch off / archive when the new flow is live and tested**                                                                                                                                                                     |
|----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 2        | Flow 3 Checkout abandonment (new flow, built alongside the old one, set live with the old one set to Manual on the same day).                                                                            | Set to Manual then archive: NEW: Abandoned Checkout (category-routed). Archive (after export): 2. SM Abandoned Checkout draft.                                                                                                    |
| 2        | Flow 1 Welcome (edit the live 1. SM: Welcome Sequence in place — keep Email 1; replace E2–E4 with the routed versions; add the abandonment check before E2–E4; fold the SMS list into the list trigger). | Archive (after export): 1.1 SM SMS Club Welcome; "1. SM: Welcome Sequence Clone Test"; "NEW: Welcome Sequence (UTM-personalised)" once its click-to-choose idea is moved into the live flow.                                      |
| 3        | Flow 2 Membership journeys + 2b Upgrade catch. Build as new flows; when live, set the four tier welcome flows to Manual the same day.                                                                    | Set to Manual then archive: FLOW: Welcome – Evolution Free / Club Access Member / Evolution Pro / Evolution Pro Annual; both "Membership Follow-Up – Non-Signups" drafts; "NEW: Cancelled to Free" draft (idea absorbed into 2b). |
| 3        | Flow 8 Order confirmation: keep; one QA pass (unsubscribe tag check is not needed on a transactional template, but the manage-preferences link should not be there either).                              | Nothing                                                                                                                                                                                                                           |
| 3–4      | Flow 9 Post-delivery onboarding + reviews (new flow on Delivered Shipment).                                                                                                                              | Set to Manual then archive: NEW: Post-Fulfillment; NEW: Post-Purchase nurture (already off); 4. SM Post Purchase draft.                                                                                                           |
| 4        | Flow 4 Cart abandonment and Flow 5 Browse abandonment — only if the tracking checks in Chapter 2.7 have passed. If not, keep the Week 1–fixed versions live and move this to Week 5–6.                   | Set to Manual then archive: NEW: Abandoned Cart; NEW: Browse Abandonment; both old "Browse Abandonment" drafts; "Added to Cart Reminder" draft; 3. SM Browse and 8. SM Abandoned Cart drafts.                                     |

Weeks 5–8 — new flows

| **Week** | **Build**                                                                                                                                                           | **Switch off / archive**                                                                                                                                                 |
|----------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 5        | Flow 6 Back in stock (turn on the Klaviyo back-in-stock button in the Shopify app embed first; wait for the first sign-ups).                                        | Nothing                                                                                                                                                                  |
| 5–6      | Flow 10 Cross-sell / second order (category-timed, no code before the final email).                                                                                 | Set to Manual then archive: NEW: Second-Order Conversion; the four Manual upsell flows (Clothing, Shoes, Clubs, Trolley).                                                |
| 6        | Flow 12 Winback (segment-triggered; back-populate in bands; main push timed for February–March).                                                                    | Set to Manual then archive: NEW: Winback.                                                                                                                                |
| 7        | Flow 13 Sunset (build the segment first, review its size with Layton before switching on).                                                                          | Nothing                                                                                                                                                                  |
| 7–8      | Flow 11 Replenishment — only if the balls volume check passes (flow 11 chapter). Flow 7 Price drop — only if tracking is fixed and the catalogue sync is confirmed. | Archive (after export): NEW: Replenishment draft once rebuilt. Keep NEW: Trade-in and "Trade in after club order" drafts for a Phase 2 trade-in flow (not in this pack). |
| 8        | Clean-up: archive the remaining drafts (legacy 3./4./8./9. SM flows etc.) after export/screenshot. Rename anything still carrying "(placeholder)".                  | Archive remaining 21 drafts less the two trade-in drafts.                                                                                                                |

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>Double-send safety rule</strong></p>
<p>A new flow and the flow it replaces are never live together for more
than the length of the longer flow's delays. Set the old flow to Manual
on the day the new one goes live. Profiles already inside the old flow
will complete it only if you choose "let them finish"; for abandonment
flows choose that; for welcome and membership choose "exit all", because
the new flow will pick them up from the trigger.</p>
<p>Check the day after each cut-over: Analytics → Flows → filter by the
old flow name → recipients should be 0.</p></td>
</tr>
</tbody>
</table>

2\. Global rules

2.1 One category taxonomy: flow_cat

Every split in every flow reads the same eight values. Nothing else — no
per-flow collection lists, no "Push/Pull Trolleys" here and "Manual
Trolleys" there.

| **flow_cat value** | **What it covers**                                                                  | **Shopify tag to add** | **Notes**                                                                         |
|--------------------|-------------------------------------------------------------------------------------|------------------------|-----------------------------------------------------------------------------------|
| trolleys           | Electric and push trolleys (Motocaddy, PowaKaddy, Stewart, etc.), trolley batteries | flow_cat:trolleys      | Includes batteries sold alone so a battery order does not fall to accessories     |
| clubs              | Drivers, woods, hybrids, irons, wedges, putters, full sets, custom-fit clubs        | flow_cat:clubs         | Irons must be in here (audit: missing from checkout split)                        |
| used               | Approved used clubs                                                                 | flow_cat:used          | Own value so copy can talk about grading and the used guarantee \[CONFIRM terms\] |
| bags               | Stand, cart and tour bags, travel covers                                            | flow_cat:bags          |                                                                                   |
| footwear           | Men's, women's and junior shoes, spikes                                             | flow_cat:footwear      |                                                                                   |
| clothing           | All apparel, waterproofs, gloves, hats                                              | flow_cat:clothing      | Gloves sit here for splits; replenishment picks them up by product type           |
| balls              | Golf balls                                                                          | flow_cat:balls         | Drives the replenishment flow                                                     |
| accessories        | Everything else: GPS, rangefinders, tees, umbrellas, training aids, gifts           | flow_cat:accessories   | The fallback value                                                                |

**How to implement (no developer)**

1.  In Shopify Admin → Products, use bulk editor or a saved product
    filter (by collection, product type or vendor) to add the tag
    flow_cat:xxx to every product. Every product must have exactly one
    flow_cat tag. Do trolleys, clubs and balls first (they drive most
    revenue and the replenishment logic).

2.  Route A (preferred): in Klaviyo, open a profile that has recently
    placed an order and look at the Checkout Started and Placed Order
    events. Klaviyo's Shopify integration passes product tags on line
    items; find the property that holds them (typically under Items /
    line_items → product → tags, and a top-level "Tags" or "Item Tags"
    list). \[CONFIRM the exact property name on each of Checkout
    Started, Placed Order, Added to Cart and Viewed Product before
    building any split.\] Splits are then: "Tags contains
    flow_cat:trolleys".

3.  Route B (fallback if a tag property is not on an event): use the
    existing Collections (checkout) / Categories (cart, browse)
    property, but with ONE written mapping — the table below — copied
    identically into every flow. Karin keeps the master list in the
    shared drive and updates all flows together when a collection is
    added.

4.  Multi-category baskets: splits are evaluated in priority order
    trolleys → clubs → used → bags → footwear → clothing → balls →
    accessories. A basket with a trolley and balls goes down the
    trolleys path. Put the trigger split conditions in that order in
    Klaviyo.

| **flow_cat** | **Route B: collection/category names that map to it (write them exactly as they appear in Klaviyo events)**                                                                        |
|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| trolleys     | Push & Electric Golf Trolleys; Push/Pull Trolleys; Manual Trolleys; Electric Golf Trolleys; Motocaddy; PowaKaddy; Trolley Batteries \[CONFIRM full list from Shopify collections\] |
| clubs        | Mens Golf Clubs; Womens Golf Clubs; Drivers; Fairway Woods; Hybrids; Irons; Wedges; Putters; Package Sets; Junior Clubs \[CONFIRM\]                                                |
| used         | All Approved Used Golf Clubs; Used Drivers; Used Irons … \[CONFIRM\]                                                                                                               |
| bags         | Golf Bags; Stand Bags; Cart Bags; Tour Bags; Travel Covers \[CONFIRM\]                                                                                                             |
| footwear     | Mens Golf Shoes; Womens Golf Shoes; Junior Golf Shoes; Spikes \[CONFIRM\]                                                                                                          |
| clothing     | Mens Golf Clothing; Womens Golf Clothing; Waterproofs; Gloves; Headwear \[CONFIRM\]                                                                                                |
| balls        | Golf Balls; Titleist Balls; … \[CONFIRM\]                                                                                                                                          |
| accessories  | Everything not matched above — this is the "else" branch, no condition needed                                                                                                      |

2.2 Priority and mutual exclusion

The audit found in_abandon_flow is set but never read. This pack makes
exclusion depend on **metric filters** (facts Klaviyo already has, which
cannot get stuck) and keeps the property only as a secondary check.

| **Flow**                             | **Flow filters that enforce priority (Klaviyo → flow → Flow filters)**                                                                                                                                                                                                                                                           | **Also set**                                                                                          |
|--------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| 3 Checkout                           | Placed Order zero times since starting this flow. Has not bounced (email) in the last 30 days.                                                                                                                                                                                                                                   | in_abandon_flow = checkout at entry; = none at the last step                                          |
| 4 Cart                               | Placed Order zero times since starting this flow. Checkout Started zero times in the last 3 days. in_abandon_flow is not "checkout".                                                                                                                                                                                             | in_abandon_flow = cart; = none at last step                                                           |
| 5 Browse                             | Placed Order zero times since starting this flow. Added to Cart zero times in the last 7 days. Checkout Started zero times in the last 7 days. in_abandon_flow is not "checkout" and is not "cart". Engaged: Opened Email or Clicked Email at least once in the last 90 days OR Placed Order at least once in the last 180 days. | in_abandon_flow = browse; = none at last step                                                         |
| 1 Welcome E2–E4 (non-essential)      | Not a flow filter: a conditional split immediately before each of E2, E3, E4: "Checkout Started or Added to Cart at least once in the last 2 days?" YES → wait 2 days, re-check once, then send. NO → send.                                                                                                                      | Welcome E1 is exempt: it is the best-earning email and goes regardless.                               |
| 9, 10, 11, 12 (post-purchase family) | Each starts with Placed Order zero times since starting this flow (except 9, which needs no such filter — a second order should not stop onboarding for the first).                                                                                                                                                              | Post-purchase flows are naturally sequential (9 days 1–35 → 10 days 21+ → 11 days 40+ → 12 day 120+). |

**Property clearing.** Klaviyo's Update Profile Property action sets a
static value. Every abandonment flow ends with a final step "Update
profile property: in_abandon_flow = none". Because a profile that buys
mid-flow is exited before that step, the property can still be stale —
which is why the metric filters, not the property, are load-bearing.

2.3 Cross-flow rules table

| **Rule**                                           | **Setting**                                                                                                                                                   | **How it is enforced in Klaviyo**                                                                                                                           |
|----------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Abandonment priority                               | Checkout \> Cart \> Browse \> Welcome E2–E4                                                                                                                   | Flow filters in 2.2                                                                                                                                         |
| Minimum gap between two flow emails to one profile | 16 hours (smart sending window, assumed default — \[CONFIRM\] Settings → Email → Smart sending)                                                               | Smart sending ON on every flow email except Order Confirmation and Back in Stock. No flow has two messages closer than 16h.                                 |
| Maximum flow emails per profile per week           | 4 (design rule). Klaviyo has no native frequency cap for flows, so this is achieved by delays and smart sending.                                              | Longest weekly load: welcome (E1 day 0, E2 day 1, E3 day 3, E4 day 6) = 4. Any abandonment email in the same week delays welcome E2–E4 by the split in 2.2. |
| Campaigns vs flows                                 | Campaigns also count towards smart sending. Do not schedule campaigns at 09:30 — flow morning sends land then. Send campaigns at 17:30 or weekends.           | Campaign calendar rule, owned by Alex                                                                                                                       |
| SMS                                                | Never before an email in the same flow. Quiet hours 08:00–20:00 on. Max 1 SMS per flow except checkout (2, one day apart). Only to profiles with SMS consent. | Flow filter on each SMS: "Can receive SMS marketing"; quiet hours in message settings                                                                       |
| Members                                            | Profiles with MemberTier set never see the public-offer variants; they see member-pricing copy.                                                               | Conditional split "MemberTier is set" in welcome, checkout, cart, browse where an incentive appears                                                         |
| Customers in welcome                               | Anyone who has ever placed an order is excluded from flow 1 at entry and exited if they buy.                                                                  | Flow filter: Placed Order zero times over all time, and zero times since starting this flow                                                                 |
| Unengaged                                          | Browse, cross-sell and winback only send to profiles with an open/click in 90–180 days.                                                                       | Engagement condition in flow filters (2.2 and each chapter)                                                                                                 |
| Bounced                                            | Excluded everywhere                                                                                                                                           | Flow filter: Bounced Email zero times in last 30 days (Klaviyo also suppresses hard bounces automatically)                                                  |

2.4 Correct dynamic variables by trigger

The cart fault came from cloning a checkout template. Use these, and
before any template goes live open a real event of that type on a
profile's activity feed and check every variable exists. Names below are
Klaviyo's standard Shopify integration names; where this account might
differ the item is marked \[CONFIRM\].

| **Trigger metric**                                        | **Use for**     | **Product / items block**                                                                                                                                                                                                                                    | **Main CTA link**                                                                    | **Other useful variables**                                                                       |
|-----------------------------------------------------------|-----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| Checkout Started                                          | Flow 3          | Dynamic table over {{ event.extra.line_items }} — fields item.product.title, item.quantity, item.line_price, item.product.images.0.src, item.product.url. Or drag in the "Checkout Started" abandoned-checkout block.                                        | {{ event.extra.checkout_url }}                                                       | {{ event.\$value }} basket value; {{ event.extra.line_items.0.product.title }} first item        |
| Added to Cart                                             | Flow 4          | Dynamic table over {{ event.Items }} (fields ProductName, Quantity, ItemPrice, ImageURL, ProductURL) — or the single added item: {{ event.AddedItemProductName }}, {{ event.AddedItemImageURL }}, {{ event.AddedItemURL }} \[CONFIRM names on a real event\] | https://evolutiongolf.co.uk/cart (static) — there is NO checkout_url on this event   | {{ event.\$value }} cart value; {{ event.AddedItemCategories }} / Tags for Route A/B             |
| Viewed Product                                            | Flow 5          | Single product: {{ event.ProductName }} / {{ event.Title }}, {{ event.ImageURL }}, {{ event.URL }}, {{ event.Price }} \[CONFIRM\]; plus a "Recently viewed" product feed block                                                                               | {{ event.URL }} (the viewed product)                                                 | {{ event.Categories }} / Tags for routing                                                        |
| Placed Order                                              | Flows 8, 10, 11 | {{ event.extra.line_items }} as for checkout; order number {{ event.extra.order_number }} or {{ event.OrderId }} \[CONFIRM\]                                                                                                                                 | https://evolutiongolf.co.uk/account (order status) or the product URL for cross-sell | {{ event.\$value }} order total; {{ event.extra.shipping_address.first_name }}                   |
| Delivered Shipment (primary) / Fulfilled Order (fallback) | Flow 9          | {{ event.extra.line_items }} on Fulfilled Order; on Delivered Shipment check the payload — it may carry fewer item fields, in which case pull the product from the Placed Order via a product feed by tag \[CONFIRM\]                                        | Product care/how-to page URL (static per category path)                              | {{ event.extra.tracking_number }} on fulfilment \[CONFIRM\]                                      |
| Subscribed to Back in Stock                               | Flow 6          | Klaviyo's Back in Stock block, or {{ event.ProductName }}, {{ event.VariantName }}, {{ event.ImageURL }}, {{ event.ProductURL }} \[CONFIRM\]                                                                                                                 | {{ event.ProductURL }}                                                               | Klaviyo adds the "wait for stock" delay automatically on this trigger                            |
| Price Drop                                                | Flow 7          | Klaviyo Price Drop block (shows old price, new price, product image)                                                                                                                                                                                         | Product URL from the event                                                           | Requires catalogue sync and Klaviyo's Price Drop trigger to be available on the plan \[CONFIRM\] |

2.5 Template rules and register

- One master template per family (marketing, transactional,
  personal-from-Alex). All flow templates are saved as clones of one of
  these three and recorded in the register below.

- Footer: {% unsubscribe %} and {% manage_preferences_link %} as Klaviyo
  tags — never a pasted URL. Postal address and company number in the
  footer \[CONFIRM text\].

- Sender: "⛳ Evolution Golf" \<info@evolutiongolf.co.uk\>. Personal
  emails: from "Alex at Evolution Golf" \<info@evolutiongolf.co.uk\>,
  plain layout, signed "Alex, Head of Ecommerce".

- Colours: \#006747 buttons and headings, \#003D27 header bar, \#F1DA01
  accent on one element only, \#FAF7F1 background. Fonts: Fraunces for
  headings, Inter for body, with Georgia / Arial as email-client
  fallbacks.

- Tone: knowledgeable golfing mate. Short sentences. British English. No
  hype words, no countdown timers, no "hurry". A deadline appears only
  when the coupon block's real expiry is shown.

- First name fallback everywhere: {{ person.first_name\|default:'there'
  }}.

- No hard-coded prices or tier benefits in any email: tier references
  come from the universal block "Tier table" (Chapter 4).

- UTMs: on for all marketing flows (utm_source=klaviyo,
  utm_medium=email, utm_campaign=flow name); off for Order Confirmation.

| **Template register (fill in during build)** | **Master** | **Unsubscribe tag ✔** | **Manage prefs ✔** | **Dynamic block checked ✔** | **Coupon block ✔/n.a.** |
|----------------------------------------------|------------|-----------------------|--------------------|-----------------------------|-------------------------|
| e.g. F3 Checkout – Trolleys – E1             | Marketing  |                       |                    |                             | n.a.                    |
| …                                            |            |                       |                    |                             |                         |

2.6 Discount policy table

Default for the whole programme: **no public code in welcome,
abandonment or cross-sell.** The incentive is member pricing: "Join free
and pay member price on this order" (5%) or "Club Access unlocks 10%".
Where a coded fallback is offered it is a Klaviyo unique coupon (one
use, real expiry shown by the coupon block), max 5%, minimum basket £30,
and the coupon in Shopify excludes the trolleys and clubs collections.
Layton chooses per flow; both routes are built as separate branches so
the switch is a conditional split, not a rebuild.

| **Flow**         | **Member-pricing route (default)**                                                                                   | **Coded fallback (labelled FALLBACK in Klaviyo)**                                            | **Trolleys/clubs**                                                |
|------------------|----------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| 1 Welcome        | E1 keeps its current 5% EVO5 until test T2 decides; the T2 variant offers "join free, member price". E2–E4: no code. | EVO5 5% static in E1 only (current). If kept, remove every expiry claim.                     | Never a code on a trolley or club                                 |
| 2 Membership     | None needed — member pricing is the product. Pro birthday voucher is a tier benefit, not a flow discount.            | None                                                                                         | —                                                                 |
| 3 Checkout       | E2 shows member price on the basket ("join free → £X member price"). E3 for Club Access.                             | E3: unique 5% coupon, 7-day expiry, baskets under £150, accessories/apparel/balls paths only | No code; value proof only                                         |
| 4 Cart           | E2 as checkout                                                                                                       | E2 (Fallback path only): unique 5%, 7 days, \<£150                                           | No code                                                           |
| 5 Browse         | None — education only                                                                                                | None recommended. If Layton insists: E2 unique 5% on footwear/clothing only                  | No code                                                           |
| 6 Back in stock  | None                                                                                                                 | None                                                                                         | —                                                                 |
| 7 Price drop     | None (the drop is the offer)                                                                                         | None                                                                                         | —                                                                 |
| 9 Post-delivery  | None. Mention member trade-in bonus for club buyers.                                                                 | None                                                                                         | —                                                                 |
| 10 Cross-sell    | Member price on the paired accessory; free-delivery threshold as the nudge                                           | Final email only: unique 5% on the paired accessory, 10 days                                 | The paired item is an accessory, so the fallback is allowed there |
| 11 Replenishment | Member price + free delivery over £30                                                                                | Unique 5% on balls, 14 days                                                                  | —                                                                 |
| 12 Winback       | E1–E2: what's new + member price. E3: "come back as a member"                                                        | E3: unique 5%, 14 days, \<£150, not trolleys/clubs (replaces WINBACK5 / 10%)                 | No code                                                           |
| 13 Sunset        | None                                                                                                                 | None                                                                                         | —                                                                 |

**Coupon set-up (once)**

1.  Klaviyo → Coupons → Create → Shopify → Percentage 5% → Minimum
    purchase £30 → Applies to: all products except collections Trolleys
    and Clubs (and Used) \[CONFIRM collection names\] → Expiry:
    relative, 7 days (make a second coupon at 10 days and a third at 14
    days) → one use per customer.

2.  Name them FLOW5-7D, FLOW5-10D, FLOW5-14D. Only these three coupons
    are allowed in flows. Retire BASKET5, BASKET10, WINBACK5 and
    TROLLEY10 from all flows by Week 2 (leave the Shopify discounts
    alive for 30 days for anyone who already holds a code, then disable
    them).

3.  In templates use the Coupon block, which prints the code and its
    real expiry date. Never type a code or a deadline as text.

2.7 Tracking checks before relaunching cart and browse

Identified Added to Cart profiles fell ~70% and Viewed Product ~50% from
July to August while checkouts and orders held. Complete all of these
before flows 4, 5 and 7 are relaunched:

1.  Shopify Admin → Online Store → Themes → Customise (live theme) → App
    embeds: confirm "Klaviyo onsite tracking" (Klaviyo app embed) is ON
    for the live theme. Check whether the theme was changed or
    republished in late July/August (Themes → theme history).

2.  Shopify Admin → Settings → Customer privacy: check whether a cookie
    banner / consent setting was added or changed in August. If consent
    is required before tracking, Klaviyo onsite JS will not fire for
    visitors who have not accepted — record the accept rate. \[Klaviyo
    respects Shopify's consent API; if strict consent is on, the drop is
    partly legitimate and volume will not fully return.\]

3.  Klaviyo → Integrations → Shopify: confirm "Onsite tracking" is
    enabled and there are no sync errors.

4.  Test as a known profile: click a link in a Klaviyo email to your own
    address on your phone, view two products, add one to cart, start
    checkout. Within 10 minutes check your Klaviyo profile shows Viewed
    Product ×2, Added to Cart, Checkout Started.

5.  Repeat the test in a private window after accepting the cookie
    banner, and again after rejecting it. Note which events appear.

6.  Klaviyo → Analytics → Metrics: chart Viewed Product, Added to Cart
    and Checkout Started daily for the last 90 days. Volume should step
    back up within 24h of the fix. Do not relaunch cart/browse until
    Added to Cart identified profiles are back above ~400 a month (July
    was 565).

7.  Check the sign-up forms (Klaviyo → Sign-up forms) still publish to
    the live theme — the same theme change that breaks tracking usually
    breaks forms.

8.  If none of this finds a cause: a developer would compare the
    theme.liquid before/after. No-dev fallback: reinstall the Klaviyo
    app embed (toggle off, save, toggle on, save) and re-test.

2.8 Seasonality

Klaviyo flows have no date-based split and universal content blocks have
no date condition, so seasonality is done by **swapping universal blocks
on a calendar** (Karin's recurring task) plus, in a few flows, a manual
content variant. Winter = 1 November to 28/29 February.

| **Date**                 | **Swap / action**                                                                                                                                                                                                                 | **Blocks affected**                             |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------|
| 1 Nov                    | Switch the Seasonal banner to Winter; switch the Cross-sell pairs block to winter pairs (winter wheels, mitts, waterproofs, range balls, training aids); pause flow 11 Replenishment (set to Manual); winback E1 uses winter copy | Seasonal banner; Cross-sell pairs; Winback hero |
| Mid Nov – Black Friday   | Seasonal banner: "Black Friday — members see prices first" (no public code). Do not add codes to flows during BF; campaigns carry the event.                                                                                      | Seasonal banner                                 |
| 1 Dec – 20 Dec           | Seasonal banner: gifting + last order dates for Christmas delivery \[CONFIRM dates with courier\]. Browse E1 adds "buying for someone?" line.                                                                                     | Seasonal banner; Browse E1 line                 |
| 1 Mar                    | Switch to Summer banner and summer pairs; unpause Replenishment; winback main push (segment back-populate band, see flow 12)                                                                                                      | All                                             |
| First week Apr (Masters) | Seasonal banner: Masters week — new-season clubs, fitting slots                                                                                                                                                                   | Seasonal banner                                 |
| 1–15 Jun (Father's Day)  | Seasonal banner: gifts under £50 / gift cards                                                                                                                                                                                     | Seasonal banner                                 |
| Mid Jul (The Open)       | Seasonal banner: Open week — balls, gloves, links-style gear                                                                                                                                                                      | Seasonal banner                                 |

3\. Flow chapters

3.0 Standard build and QA checklist (applies to every flow)

Karin runs this list for every flow before it is set live, and Alex
signs off. Tick each item in the flow's row of the template register
(2.5).

1.  Flow filters match section (b) exactly. Screenshot them.

2.  Every message name follows "F\<flow\> \<path\> E\<n\> – \<purpose\>"
    (e.g. "F3 Trolleys E1 – Basket saved"). No "(placeholder)" names.

3.  Smart sending set per section (c) on every message; UTMs on
    (marketing) or off (transactional).

4.  Every template: {% unsubscribe %} and {% manage_preferences_link %}
    present; postal address present; no pasted unsubscribe URL. Search
    the HTML for "klaviyo.com/unsubscribe" or "manage" to catch
    leftovers.

5.  Every dynamic variable checked against a real event of the trigger
    type (open a profile → activity → the event → copy property names).
    Preview and test-send with that profile selected in "Preview with a
    profile".

6.  Every link clicked in the test send: product/cart/checkout link, CTA
    button, header logo, footer links. Cart CTAs go to /cart, never
    checkout_url.

7.  Each trigger split and conditional split path tested: use test
    profiles (one per flow_cat) and Klaviyo's "Preview" on the split, or
    send yourself a real event (add a trolley to cart, then a ball).
    Confirm each test profile lands on the intended path in the flow
    analytics.

8.  Coupon block (fallback branches only): test-send, redeem the code on
    a test order, confirm 5%, minimum £30, trolleys/clubs excluded,
    single use, expiry date printed matches Shopify.

9.  No text claims a deadline, "expires", "ends tonight", "last chance"
    or stock scarcity unless it is a coupon block's real expiry or a
    live inventory field.

10. No hard-coded tier prices or benefits — all via the Tier table
    universal block.

11. Mobile preview checked; images have alt text; first-name fallback
    renders "there".

12. Set live during office hours; check flow analytics after 24h and
    72h: recipients per step, skipped-by-smart-sending count (Analytics
    → Flows → message → "Skipped"), bounce and unsubscribe.

3.1 Flow 1 — Welcome (non-customers)

Edit the live "1. SM: Welcome Sequence" in place rather than building
new — Email 1 (79% open, £13.91 per recipient) must not be touched. The
flow becomes 4 emails + 1 SMS, interest-routed at E2, one offer, with
the abandonment check before every non-essential email.

a\) Purpose and success metric

|             | **Detail**                                                                                                                                                                                                                   |
|-------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose     | Turn a new subscriber into a first-time buyer within 14 days without training them to wait for codes, and capture their interest (trolleys / clubs / footwear & apparel / general) for every later flow.                     |
| Primary KPI | Placed-order rate per entrant within 14 days. Baseline (audit): E1 6.78% per recipient; flow email 1.86%. Target: hold flow revenue per recipient at ≥ £5.9 (audit; Klaviyo welcome peer median £5.0) while the tail is cut. |
| Guardrail   | Unsubscribe rate from 1.51% to ≤ 0.73% (peer median); spam rate from "Poor" to ≤ 0.008%; E2 unsubscribe from 2.60% to ≤ 1%.                                                                                                  |
| Secondary   | Interest captured (click-to-choose) on ≥ 30% of entrants — estimate, no benchmark exists. Membership sign-up rate per entrant (for test T2) — no benchmark.                                                                  |

b\) Trigger and flow filters

| **Setting**         | **Value**                                                                                                                                                                                                                                                                                     |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Trigger             | Added to list: "1.0 Main Mailing List" (double opt-in). Make the SMS sign-up form also add the profile to this list so SMS-only joiners enter here (retiring 1.1 SM SMS Club Welcome).                                                                                                        |
| Trigger filters     | None                                                                                                                                                                                                                                                                                          |
| Flow filters        | \(1\) Placed Order zero times over all time; (2) Placed Order zero times since starting this flow; (3) Bounced Email zero times in the last 30 days; (4) MemberTier is not set — members go to flow 2 instead (a Free member who also joins the list gets member copy from flow 2, not EVO5). |
| Per-message filters | SMS 1: "Can receive SMS marketing" (consent). E2–E4: preceded by the abandonment check split (2.2).                                                                                                                                                                                           |

c\) Re-entry and smart sending

| **Item**      | **Setting**                                                                                                                           |
|---------------|---------------------------------------------------------------------------------------------------------------------------------------|
| Re-entry      | Off. A profile can only enter once (list trigger; if removed and re-added, Klaviyo will not re-trigger unless allowed — keep it off). |
| Smart sending | E1: ON (it is the first message; nothing to collide with, but leave on for safety). SMS 1: ON. E2, E3, E4: ON.                        |
| Gaps          | E1 → E2 ≥ 24h (1-day delay then 09:30). E2 → E3 2 days. E3 → E4 3 days. No two emails within 16h.                                     |

d\) Step-by-step map

| **Step** | **Type**                     | **Exact setting / condition**                                                                                                                                                    | **Message**                                                                                                                                                                                                                                                                                                                            |
|----------|------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1        | Message                      | Immediately on trigger                                                                                                                                                           | E1 — current "Here's your 5% OFF⛳️ / Proper service, quality gear" unchanged, PLUS add the click-to-choose strip (four links, each with link action "Update profile property: interest = trolleys / clubs / footwear_apparel / general") \[CONFIRM link actions available in your editor; fallback below\]. Remove any expiry wording. |
| 2        | Delay                        | 1 hour                                                                                                                                                                           |                                                                                                                                                                                                                                                                                                                                        |
| 3        | Conditional split            | Can receive SMS marketing = yes                                                                                                                                                  | YES → SMS 1. NO → skip                                                                                                                                                                                                                                                                                                                 |
| 4        | Delay                        | 1 day, then send at 09:30 local                                                                                                                                                  |                                                                                                                                                                                                                                                                                                                                        |
| 5        | Conditional split            | Checkout Started OR Added to Cart at least once in the last 2 days                                                                                                               | YES → Delay 2 days → re-check once → send E2. NO → E2                                                                                                                                                                                                                                                                                  |
| 6        | Conditional split (interest) | interest equals trolleys / clubs / footwear_apparel / else. Fallback if no link actions: Viewed Product at least once in last 7 days where Tags contains flow_cat:trolleys, etc. | E2 — one of four variants (same layout, swapped hero and copy)                                                                                                                                                                                                                                                                         |
| 7        | Delay                        | 2 days, send at 09:30                                                                                                                                                            |                                                                                                                                                                                                                                                                                                                                        |
| 8        | Conditional split            | Abandonment check as step 5                                                                                                                                                      | E3 — "Ask us anything" (Alex, plain)                                                                                                                                                                                                                                                                                                   |
| 9        | Delay                        | 3 days, send at 17:30                                                                                                                                                            |                                                                                                                                                                                                                                                                                                                                        |
| 10       | Conditional split            | Abandonment check as step 5                                                                                                                                                      | E4 — "Two ways to pay less, neither is a code"                                                                                                                                                                                                                                                                                         |
| 11       | Update profile property      | welcome_complete = true                                                                                                                                                          | End                                                                                                                                                                                                                                                                                                                                    |

**Text diagram**

> TRIGGER Added to list "1.0 Main Mailing List"
>
> FILTERS never ordered · no order since start · no bounce 30d ·
> MemberTier not set
>
> E1 Welcome + click-to-choose (day 0)
>
> wait 1h
>
> SPLIT SMS consent?
>
> yes → SMS 1
>
> wait 1 day → 09:30
>
> SPLIT abandoned in last 2 days? yes → wait 2d → re-check → continue
>
> SPLIT interest
>
> trolleys → E2a \| clubs → E2b \| footwear/apparel → E2c \| else → E2d
>
> wait 2 days → 09:30
>
> SPLIT abandoned in last 2 days? (as above)
>
> E3 Ask us anything (from Alex)
>
> wait 3 days → 17:30
>
> SPLIT abandoned in last 2 days? (as above)
>
> E4 Two ways to pay less
>
> SET welcome_complete = true

e\) Category logic

Routing here is by declared interest (or recent browse), not by an event
category, because nothing has been bought.

| **flow_cat path**      | **Content angle**                                                                                                                                                         | **Proof points**                                                                                                                        | **Cross-sell / next step**                                                            |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| trolleys (E2a)         | How to choose an electric trolley: battery range, folding size, GPS or not, DHC braking. No single product pushed (audit: E2 pushing one £1k trolley caused 2.6% unsubs). | 2-year warranty \[CONFIRM\], staff/expert Motocaddy video reviews, finance from £x/month via Klarna/Clearpay \[CONFIRM\], free delivery | Trolley buying guide page → later cross-sell to battery care/winter wheels in flow 10 |
| clubs (E2b)            | Fitting first: why a 20-minute fitting beats guessing; approved-used as the smart route into premium irons                                                                | Custom fitting centre, trade-in, approved-used grading \[CONFIRM\], Trustpilot Excellent                                                | Book a fitting; browse approved used                                                  |
| footwear_apparel (E2c) | UK conditions: waterproof ratings, spiked vs spikeless, layering                                                                                                          | Free delivery, easy returns \[CONFIRM window\], staff picks                                                                             | Shoes → socks/spikes/waterproofing later                                              |
| general (E2d)          | Interest-neutral: three things people ask us most; balls, gloves, GPS                                                                                                     | People who play, Trustpilot, free delivery                                                                                              | Bestseller feed (3 months) — the only place a generic feed is allowed                 |

f\) Seasonal variant (winter: 1 Nov – end Feb)

- E2a winter: swap hero to "winter wheels and battery care" and mention
  that most trolleys are bought Feb–Apr, so "no rush — here is how to
  choose"; E2c winter: waterproofs and mitts lead, shoes second.

- E4 winter: add the Christmas last-order-dates line from the Seasonal
  banner block (Dec only).

- All E2–E4 carry the Seasonal banner universal block; swap per the 2.8
  calendar.

g\) Hand-off

| **Exit condition**                      | **What happens**                                                                                                                              | **Picked up by**                                   |
|-----------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------|
| Places an order at any point            | Exits (flow filter). Order Confirmation sends.                                                                                                | Flow 8 → 9 → 10                                    |
| Starts checkout / adds to cart mid-flow | E2–E4 delayed 2 days by the split; abandonment flow takes priority                                                                            | Flow 3 / 4                                         |
| Joins membership mid-flow               | Not exited automatically (flow filters are checked at each step — MemberTier is set → exits at the next message). Membership onboarding runs. | Flow 2                                             |
| Completes E4 without buying             | welcome_complete = true; profile sits in the engaged base for campaigns; browse flow can pick them up                                         | Flow 5; campaigns; flow 13 after 150 days no click |

h\) Retire, merge, salvage

| **Existing flow / message (audit name)**       | **Action**                                                                                                                                                                                                                                                       |
|------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1\. SM: Welcome Sequence                       | Edit in place. Keep E1. Replace E2 (A/B), E3 (A/B), E4 (A/B) with the routed E2 and new E3/E4. Set to Manual then archive: "Welcome Email Additional", E5 "A Message from Alex" (its idea is now E3), SMS \#2 (broken), SMS "EVO5 expires soon" (false urgency). |
| 1.1 SM SMS Club Welcome                        | Retire (Week 2). SMS joiners are routed into this flow via the list. Static code SMSCLUB5: disable in Shopify after 30 days.                                                                                                                                     |
| 1\. SM: Welcome Sequence Clone Test            | Archive after export.                                                                                                                                                                                                                                            |
| NEW: Welcome Sequence (UTM-personalised) draft | Take its interest-routing idea (used here at step 6); archive the draft.                                                                                                                                                                                         |
| Codes EVO5 / TROLLEY10                         | TROLLEY10 removed from the flow entirely. EVO5 stays in E1 only until test T2 reads; remove every expiry claim now.                                                                                                                                              |

**Salvageable**

- Welcome Email 1 in full — do not rewrite it, only add the
  click-to-choose strip beneath the existing CTA and remove any
  "expires" text.

- Send times 11:30 / 17:30 are fine for E1; the new E2/E3 morning slot
  is 09:30 so campaigns can keep 17:30.

i\) Build checklist and QA

Complete the standard checklist in 3.0, plus:

1.  Confirm the four click-to-choose links each set the interest
    property (click one from a test send, check the profile). If the
    editor has no link actions, build the step-6 split on Viewed Product
    tags instead and note it in the register.

2.  Test a profile that adds to cart on day 0: confirm E2 is delayed
    (flow analytics shows it waiting at the split).

3.  Test a profile with MemberTier set: it must not enter.

4.  Confirm E1's A/B tests are ended and the winning variant is the only
    live one.

Draft copy

E1 — current email stays live. Test variant for T2 (member CTA instead
of EVO5):

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F1 E1 (T2 variant) – Welcome, member price is
yours</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F1 E1 – Welcome (member-price variant)</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Welcome in. Member prices, no code needed</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>Proper service, quality gear — and a members' price</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Join free in 30 seconds and pay member price on your first
order.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Welcome, {{ person.first_name|default:'there' }}.</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>We're a golf shop run by people who play, and we'd rather talk
you into the right trolley than the expensive one.</p>
<p>Instead of a one-off code, we do member pricing. Join free (it takes
a name and an email) and you pay the member price on every order,
starting with this one. {{ Tier table block: Free row only }}</p>
<p>What we're known for: free UK delivery over £30, a custom fitting
centre, trade-in on your old clubs, finance with Klarna or Clearpay, and
an Excellent rating on Trustpilot [CONFIRM].</p>
<p>Tell us what you're into and we'll only send the relevant stuff:
[Trolleys] [Clubs] [Shoes &amp; clothing] [A bit of everything]</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Join free → https://members.evolutiongolf.co.uk (secondary: Shop →
https://evolutiongolf.co.uk)</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Tier table universal block (Free row); USP bar universal block;
Trust bar; click-to-choose strip with link actions setting
"interest".</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Same promise as the winning E1 (service + value) but the value is
membership, which is what the business wants to grow. T2 tests it
against EVO5 on membership sign-up rate.</td>
</tr>
</tbody>
</table>

|                                            |                                                                                                                                                           |
|--------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| **💬 F1 SMS 1 – Welcome (consented only)** |                                                                                                                                                           |
| **Message name**                           | F1 SMS 1 – Welcome (consented only)                                                                                                                       |
| **Body (152 chars)**                       | Evolution Golf: welcome {{ person.first_name\|default:'' }}. Your member price is waiting — join free here and it applies to your first order: {{ link }} |
| **Link**                                   | https://members.evolutiongolf.co.uk (UTM-tagged short link)                                                                                               |
| **Settings**                               | Quiet hours ON (08:00–20:00 local). Opt-out wording added by Klaviyo settings, not in body. Smart sending ON. Requires SMS consent.                       |
| **Why**                                    | Replaces two 5% SMS codes (EVO5, SMSCLUB5). One message, no false expiry, sent after E1.                                                                  |

E2 — interest-routed (four variants, one layout). Trolleys variant in
full; swaps for the others below.

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F1 E2a – Trolleys: how to choose</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F1 E2a Trolleys – How to pick the right electric trolley</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>How to pick the right electric trolley</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>18 holes or 36? Fold-flat or GPS? A quick trolley guide</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Five questions that get you to the right model, not the priciest
one.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Choosing an electric trolley, in five questions</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>1. How many holes between charges? Standard lithium does 18;
extended does 36. Most club golfers are fine with 18 [CONFIRM per
model].</p>
<p>2. How much boot space have you got? Compact-fold models pack down to
roughly the size of a carry-on [CONFIRM].</p>
<p>3. Hilly course? Look for downhill control (DHC) so it doesn't run
away from you.</p>
<p>4. Do you want GPS on the handle? Nice to have; adds to the price. A
phone app does most of it.</p>
<p>5. Remote control? Only if you really will walk away from it.</p>
<p>Our trolleys come with a 2-year warranty [CONFIRM], and our team has
filmed honest reviews of the Motocaddy range — watch before you buy.
Spread the cost with Klarna or Clearpay [CONFIRM].</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Read the trolley guide →
https://evolutiongolf.co.uk/pages/electric-trolley-buying-guide [CONFIRM
URL]; secondary: Watch our Motocaddy reviews → [CONFIRM URL]</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Trade-in panel block (trolley variant); USP bar; Seasonal banner. No
product block — deliberately.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Education instead of a £1k product push. The audit's browse test
variant "How to pick the right electric trolley" is the best content in
the account and this is its home.</td>
</tr>
</tbody>
</table>

| **Variant**            | **Subject**                      | **Preview**                                                    | **Body swap (same five-point format)**                                                                                                                                                   |
|------------------------|----------------------------------|----------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| E2b Clubs              | Why we fit before we sell        | Twenty minutes with a launch monitor beats a year of guessing. | Five things a fitting changes (lie, shaft, length, grip, gapping); approved-used as the value route; trade-in bonus for members via Trade-in panel; CTA Book a fitting → \[CONFIRM URL\] |
| E2c Footwear & apparel | Spiked or spikeless?             | And the waterproof rating that actually matters in the UK.     | Salvaged from the browse "Spiked or spikeless?" email; layering section from "Layering for UK golf, briefly"; CTA Shop shoes → collection URL                                            |
| E2d General            | Three things golfers ask us most | Balls, gloves and a GPS — answered straight.                   | Which ball for your swing speed; how long a glove should last; GPS watch vs handheld; bestseller feed (3-month) block; CTA Shop bestsellers                                              |

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F1 E3 – Ask us anything (from
Alex)</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F1 E3 – Ask us anything</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Got a golf question? Ask me</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>The shop's open — for questions too</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Reply to this email and a real person who plays will answer.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>Alex at Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Hi {{ person.first_name|default:'there' }},</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>Alex here, I run the online side at Evolution Golf. Quick one: if
you're weighing up a trolley, some clubs or anything else, reply to this
email and tell me what you play and what you're trying to fix. I'll give
you an honest answer, even if it's "don't buy that".</p>
<p>No product list in this one. Just the offer of a proper
conversation.</p>
<p>Alex</p>
<p>Head of Ecommerce, Evolution Golf</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>None (reply-to email). Text link: Or call us on [CONFIRM phone]
Mon–Sat.</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>None. Plain-text style template. Reply-to must be a monitored inbox
[CONFIRM].</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Replaces E5 "A Message from Alex" which earned £0 at day 7; moved
earlier, made useful (a question, not a message), and it lifts
reply/engagement signals that help deliverability.</td>
</tr>
</tbody>
</table>

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F1 E4 – Two ways to pay less</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F1 E4 – Two ways to pay less (neither is a code)</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Two ways to pay less at Evolution Golf</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>Member pricing and trade-in, explained</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Join free for member prices. Trade in your old clubs for more.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>We don't do endless codes. We do these two things.</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>Member pricing. Join free and every order is at member price. {{
Tier table block }}</p>
<p>Trade-in. Send us your old clubs (or trolley) and we'll knock the
value off your order. Members get a bonus on top. {{ Trade-in panel
block }}</p>
<p>Both work on your first order. Both work on trolleys and clubs, which
codes never do.</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Join free → https://members.evolutiongolf.co.uk; Get a trade-in
quote → [CONFIRM URL]</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Tier table; Trade-in panel; Seasonal banner; Trust bar.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Ends the sequence on the two levers the business wants used, and
quietly explains why there is no 10% code coming — so nobody waits for
one.</td>
</tr>
</tbody>
</table>

3.2 Flow 2 — Membership journeys (Free / Club Access / Pro / Annual) +
2b Upgrade catch

One new-member flow with four tier branches, plus a small companion flow
(2b) for tier changes. Every tier/price reference is the Tier table
universal block — nothing hard-coded, so the planned move to a single
~£36/yr tier is a block edit.

a\) Purpose and success metric

|              | **Detail**                                                                                                                                                                                                                                                              |
|--------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose      | Get every new member using their benefits in the first 10 days, move Free members to paid, and give paid members a value recap before each renewal so they stay ≥ 3 months.                                                                                             |
| Primary KPIs | Free → paid upgrade rate within 30 days (baseline unknown — the upgrade emails have never sent; no Klaviyo benchmark). Paid churn 10% → 5% (business target). Paid members retained ≥ 3 months (target: majority; set the baseline from the membership app in month 1). |
| Guardrail    | Unsubscribe ≤ 0.5% on any membership email (members are your best list; Club Access welcome earned £51.64/recipient).                                                                                                                                                   |
| Secondary    | Paid-member first purchase within 14 days of joining; giveaway entries claimed; returns used (a used benefit is a retained member).                                                                                                                                     |

b\) Trigger and flow filters

| **Setting**        | **Value**                                                                                                                                                                                                                                                                                                                                                                                                                      |
|--------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Trigger (flow 2)   | Segment "Members – any tier": MemberTier equals "Free" OR equals "Club Access" OR equals "Evolution Pro" OR equals "Evolution Pro Annual" \[CONFIRM exact values — the audit could not see them; do NOT use "contains"\]. Segment triggers fire on entry after go-live; tick "back-populate" only for the Free branch upgrade emails if Layton wants the 336 existing Free members nudged (recommended, in two bands of ~170). |
| Trigger (flow 2b)  | Segment "Members – tier changed": (MemberTier is in the three paid values AND member_onboarded is not set) OR (MemberTier equals Free AND member_onboarded equals true AND downgrade_handled is not set).                                                                                                                                                                                                                      |
| Flow filters       | Bounced Email zero times in the last 30 days. No purchase exclusions — members should buy.                                                                                                                                                                                                                                                                                                                                     |
| Better alternative | If the membership app can send a Klaviyo event on join/upgrade/cancel (e.g. "Membership Tier Changed") \[CONFIRM with the app\], use that metric as the trigger with a trigger split on the tier property and drop flow 2b.                                                                                                                                                                                                    |

c\) Re-entry and smart sending

| **Item**      | **Setting**                                                                                                                                                                      |
|---------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Re-entry      | Flow 2: allowed once the profile has left the segment (a cancelled member who later rejoins re-enters). Flow 2b: allowed after leaving the segment (the property gates repeats). |
| Smart sending | ON for all, except the Club/Pro/Annual E1 (immediate confirmation of a paid purchase — treat as expected; smart sending OFF so it is never skipped).                             |
| Gaps          | Minimum 3 days between messages in every branch.                                                                                                                                 |

d\) Step-by-step map

| **Step** | **Type**                    | **Exact setting / condition**          | **Message**                                                                                                                                                                                                      |
|----------|-----------------------------|----------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1        | Conditional split           | MemberTier equals Free                 | YES → Free branch                                                                                                                                                                                                |
| F1       | Message                     | Immediately                            | Free E1 — "Your members portal is live" (existing, salvaged)                                                                                                                                                     |
| F2       | Delay                       | 4 days, 09:30                          |                                                                                                                                                                                                                  |
| F3       | Conditional split           | MemberTier equals Free                 | YES → Free E2 (upgrade \#1). NO → Upgraded mini-path: Club E1 (clone) → set member_onboarded = true → end                                                                                                        |
| F4       | Delay                       | 8 days, 09:30                          |                                                                                                                                                                                                                  |
| F5       | Conditional split           | MemberTier equals Free                 | YES → Free E3 (upgrade \#2). NO → Upgraded mini-path as F3                                                                                                                                                       |
| F6       | Delay                       | 30 days                                | Then Conditional split: Placed Order zero times in last 45 days → Free E4 "Use your 5% on something small" (outline)                                                                                             |
| 2        | Conditional split           | MemberTier equals Club Access          | YES → Club branch                                                                                                                                                                                                |
| C1       | Message                     | Immediately; smart sending OFF         | Club E1 — Onboarding                                                                                                                                                                                             |
| C2       | Delay                       | 3 days, 09:30                          | Club E2 — How to use it (returns, giveaway, member price)                                                                                                                                                        |
| C3       | Delay                       | 7 days, 17:30                          | Club E3 — This month's giveaway + staff pick (outline)                                                                                                                                                           |
| C4       | Delay                       | 15 days (= day 25), 09:30              | Club E4 — Your first month, in numbers (pre-renewal recap)                                                                                                                                                       |
| C5       | Update property             | member_onboarded = true                |                                                                                                                                                                                                                  |
| C6       | Delay                       | 35 days (= day 60)                     | Club E5 — Your trade-in bonus is now live (outline)                                                                                                                                                              |
| 3        | Conditional split           | MemberTier equals Evolution Pro        | YES → Pro branch: same shape as Club (E1 onboarding, E2 how to use, E4 recap day 25, set property), plus Pro E5 at day 85: "Your birthday voucher unlocks after 3 months — have we got your birthday?" (outline) |
| 4        | Conditional split           | MemberTier equals Evolution Pro Annual | YES → Annual branch: E1 onboarding, E2 how to use, set property, E3 recap at day 30 ("what you've saved so far"), E4 at day 335 ("your year in numbers" pre-renewal)                                             |
| 2b-1     | Conditional split (flow 2b) | MemberTier equals Free                 | YES → Downgrade path: Save E1 "You're still with us on Free" → set downgrade_handled = true. NO → Upgrade path: Club/Pro/Annual E1 + E2 + E4 clones per tier → set member_onboarded = true                       |

**Text diagram**

> FLOW 2 TRIGGER segment "Members – any tier"
>
> SPLIT MemberTier = Free
>
> Free E1 portal live (day 0)
>
> wait 4d → SPLIT still Free? yes → Free E2 upgrade \#1 \| no → Club E1
> clone → SET member_onboarded
>
> wait 8d → SPLIT still Free? yes → Free E3 upgrade \#2 \| no → Club E1
> clone → SET member_onboarded
>
> wait 30d → SPLIT no order 45d? yes → Free E4 use your 5%
>
> SPLIT MemberTier = Club Access
>
> Club E1 onboarding (day 0, smart sending OFF)
>
> wait 3d → Club E2 how to use it
>
> wait 7d → Club E3 giveaway + staff pick
>
> wait 15d → Club E4 first month recap (day 25)
>
> SET member_onboarded = true
>
> wait 35d → Club E5 trade-in bonus live (day 60)
>
> SPLIT MemberTier = Evolution Pro → Pro E1, E2, E4 (day 25), SET, E5
> birthday (day 85)
>
> SPLIT MemberTier = Evolution Pro Annual → Ann E1, E2, SET, E3 (day
> 30), E4 (day 335)
>
> FLOW 2b TRIGGER segment "Members – tier changed"
>
> SPLIT MemberTier = Free → Save E1 → SET downgrade_handled
>
> else → tier onboarding clones → SET member_onboarded

e\) Category logic

No product-category routing in this flow. Content angle changes by tier,
not by flow_cat. The one category hook: club buyers (Ordered Product
with flow_cat:clubs in last 60 days) get the trade-in bonus line
emphasised in E4/E5.

| **flow_cat path** | **Content angle**                                                                        | **Proof points**                                                                                                               | **Cross-sell / next step**                           |
|-------------------|------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------|
| Free              | You are already saving; here is what paid adds (double the discount, returns, giveaways) | Club Access welcome earns £51.64/recipient — paid members buy; use as social proof: "our Club members' most-bought this month" | Upgrade → Club                                       |
| Club Access       | Use it: free returns, giveaway entry, member price on the whole range                    | Real numbers in the recap: orders, saved, entries                                                                              | Trade-in bonus at day 60; Pro when they buy hardware |
| Pro / Annual      | You bought the top tier for a reason — here is everything in it                          | Free shipping on everything, 10 returns, 5 entries, +15% trade-in, birthday voucher                                            | Fitting booking; trade-in                            |

f\) Seasonal variant (winter: 1 Nov – end Feb)

- Recap emails swap the "what to spend your member price on" module via
  the Seasonal banner block.

- Free E4 winter variant: "gloves, balls and a mitt — small things at
  member price".

g\) Hand-off

| **Exit condition**                           | **What happens**                                                                                                                                                                                                       | **Picked up by**               |
|----------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------|
| Free member upgrades                         | Caught by the F3/F5 split during the first 12 days, or by flow 2b after that                                                                                                                                           | Paid onboarding                |
| Paid member downgrades to Free               | Flow 2b save path                                                                                                                                                                                                      | Flow 2b                        |
| Member cancels entirely (MemberTier cleared) | Leaves the segment; nothing sends. Optional later: "Cancelled to Free" idea from the draft is covered by the save path only if the app moves them to Free rather than clearing the property \[CONFIRM app behaviour\]. | Winback picks up lapsed buyers |
| Places an order                              | Not exited; recap emails use real order data                                                                                                                                                                           | Flows 8–10 run in parallel     |

h\) Retire, merge, salvage

| **Existing flow / message (audit name)**                                  | **Action**                                                                                                                   |
|---------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| FLOW: Welcome – Evolution Free (1 live, 2 draft)                          | Merge: E1 salvaged as Free E1; the two drafts become Free E2/E3 (rewritten below). Set to Manual, then archive after export. |
| FLOW: Welcome – Club Access Member / Evolution Pro / Evolution Pro Annual | Merge into branches; salvage each confirmation email as the tier E1 base. Set to Manual then archive.                        |
| Membership Follow-Up – Non-Signups ×2 (drafts)                            | Archive. Non-members are handled by welcome E1/E4 and abandonment E2.                                                        |
| NEW: Cancelled to Free (draft)                                            | Idea used in flow 2b save path. Archive draft.                                                                               |

**Salvageable**

- Free E1 "Your Evolution Golf Members Portal Is Now Live" (3.57% placed
  order) — keep, fix footer tags.

- Club Access welcome email — keep as the top half of Club E1; add the
  "three things to do this week" section.

i\) Build checklist and QA

Complete the standard checklist in 3.0, plus:

1.  Confirm the four MemberTier values by exporting 20 member profiles
    (Profiles → filter MemberTier is set → export CSV). Segments must
    use "equals".

2.  Create two test profiles: one set to Free that you manually change
    to Club Access on day 5 (via a profile edit) — confirm it routes to
    the upgraded mini-path; one set straight to Club Access.

3.  Check the app updates MemberTier within minutes of a tier change
    (sign up a test member in the portal).

4.  Confirm no member receives welcome flow 1 (flow 1 filter "MemberTier
    is not set").

5.  Recap emails reference {{ person.orders_count }} / totals only if
    those properties exist on the profile \[CONFIRM — Shopify sync
    usually provides them\]; otherwise use the copy without numbers.

Draft copy

Free branch

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F2 Free E1 – Your portal is live</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F2 Free E1 – Portal live (salvaged)</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Your Evolution Golf members portal is live</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>You're in. Here's how member pricing works</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Member price on every order, free delivery over £30, points on
everything.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Welcome to the club, {{ person.first_name|default:'there' }}.</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>You're a Free member. From now on you pay member price on every
order, automatically, when you're logged in. No codes.</p>
<p>{{ Tier table block }}</p>
<p>Three things worth doing this week:</p>
<p>1. Log in to the portal and check your details.</p>
<p>2. Add your clubs and shoe size in your profile so we can send the
right stuff [CONFIRM fields exist].</p>
<p>3. Have a look at what Club members are buying this month.</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Open my portal → https://members.evolutiongolf.co.uk</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Tier table; USP bar; Trust bar.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Existing email earns 3.57% placed-order rate; the additions give a
reason to log in, which is the leading indicator of retention.</td>
</tr>
</tbody>
</table>

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F2 Free E2 – Upgrade #1</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F2 Free E2 – You're getting 5%. Club members get double.</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>You're getting 5%. Club members get double.</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>The maths on Club Access, honestly</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Club Access pays for itself on one order a month. Here's the
sum.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Is Club Access worth it? Depends how much you spend.</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>Free gets you 5% member price. Club Access gets you 10%, free
delivery from a lower threshold, free returns and a monthly giveaway
entry.</p>
<p>{{ Tier table block }}</p>
<p>The honest version: if you spend under about £40 a month with us,
stay on Free. If you spend more, Club pays for itself and then some — on
a £120 pair of shoes the extra 5% alone is £6.</p>
<p>No contract. Upgrade or drop back any time in the portal.</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Compare tiers → https://members.evolutiongolf.co.uk/plans [CONFIRM
URL]</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Tier table (drives the numbers — do not hard-code the £40
break-even; recalculate when pricing changes and note it in the
block).</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>The "honest break-even" line is the brand talking. It converts the
right people and stops the wrong people churning after one month.</td>
</tr>
</tbody>
</table>

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F2 Free E3 – Upgrade #2</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F2 Free E3 – What Club members did this month</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>What our Club members are buying</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>Bigger discounts, monthly rewards, more giveaways — in practice</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>A real look at member benefits in use. Then it's up to you.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>A month in the life of a Club member</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>Here's what Club Access actually looks like in use:</p>
<p>• A member ordered shoes, found them half a size out, and sent them
back free.</p>
<p>• This month's giveaway is [CONFIRM current prize]. Every Club member
gets one entry, Pro members five.</p>
<p>• Trade-in bonus: after 60 days, Club members get +5% on any trade-in
value — worth having when your irons are due a change.</p>
<p>{{ Tier table block }}</p>
<p>Still happy on Free? That's fine. You keep your 5% either
way.</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Upgrade to Club Access → https://members.evolutiongolf.co.uk/plans
[CONFIRM URL]</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Tier table; Giveaway block (universal, updated monthly by Karin);
Trade-in panel.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Concrete use, not a benefits list. Last upgrade email — no third
nudge, to protect the 336-member Free list.</td>
</tr>
</tbody>
</table>

| **Message**      | **Subject**                                 | **Preview**                                                    | **Content outline (2–3 lines)**                                                                                                                                               |
|------------------|---------------------------------------------|----------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Free E4 (day 42) | Your member price works on small things too | Balls, a glove, a mitt — member price, free delivery over £30. | Only to Free members with no order in 45 days. Consumables at member price; Seasonal banner; bestseller feed filtered to accessories/balls under £30 \[CONFIRM feed filter\]. |

Club Access branch

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F2 Club E1 – Onboarding</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F2 Club E1 – Welcome to Club Access</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Welcome to Club Access — here's what changed</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>You're a Club member. Three things to do this week</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>10% member price, free returns, a giveaway entry a month. All live
now.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Good call, {{ person.first_name|default:'there' }}.</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>Your Club Access membership is live. Here's what's different from
today:</p>
<p>{{ Tier table block: Club row highlighted }}</p>
<p>Three things to do this week:</p>
<p>1. Log in — member price shows automatically at checkout.</p>
<p>2. Check this month's giveaway; you're already entered [CONFIRM
mechanics].</p>
<p>3. If you've got clubs gathering dust, get a trade-in quote now —
your +5% member bonus kicks in after 60 days, so the quote today tells
you what to expect.</p>
<p>Questions? Reply to this email. Alex and the team read every
one.</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Open my portal → https://members.evolutiongolf.co.uk</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Tier table; Giveaway block; Trade-in panel; Trust bar.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>OFF (paid confirmation — must always send)</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>The existing Club welcome already earns £51.64 per recipient. This
keeps the confirmation and adds the three behaviours that predict
retention.</td>
</tr>
</tbody>
</table>

| **Message**      | **Subject**                          | **Preview**                                                        | **Content outline (2–3 lines)**                                                                             |
|------------------|--------------------------------------|--------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| Club E2 (day 3)  | Free returns, and how they work      | Order two sizes, keep one, send one back. Free, four times a year. | How to start a return in the portal \[CONFIRM process\]; giveaway reminder; one staff pick at member price. |
| Club E3 (day 10) | This month's giveaway (you're in it) | Plus what the shop team is playing right now.                      | Giveaway block; two staff picks with member price shown; no code.                                           |

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F2 Club E4 – Pre-renewal recap (day
25)</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F2 Club E4 – Your first month as a Club member</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Your first month as a Club member</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>What Club Access has done for you so far</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>What you've saved, what you've entered, what's coming next
month.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>One month in. Here's the tally.</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>Your membership renews in a few days, so here's where you
stand:</p>
<p>• Orders since joining: {{ person.orders_count|default:'—' }}
[CONFIRM property]</p>
<p>• Member savings so far: shown in your portal [link] (we'd rather
show you the real figure there than guess here)</p>
<p>• Giveaway entries: 1 this month, 1 more next month</p>
<p>• Free returns left this year: shown in your portal</p>
<p>Next month: {{ Giveaway block }} and, from day 60, your +5% trade-in
bonus.</p>
<p>If Club isn't earning its keep for you, you can drop to Free in the
portal and keep your 5%. We'd rather you stayed for the right
reasons.</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>See my savings → https://members.evolutiongolf.co.uk</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Tier table; Giveaway block; orders_count if available. If no savings
figure is available anywhere, delete that bullet — never invent
one.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>A value recap 3–5 days before billing is the single strongest churn
lever for a £3.99 subscription; the "drop to Free" line keeps the
downgrade in the family instead of a full cancel.</td>
</tr>
</tbody>
</table>

| **Message**            | **Subject**                              | **Preview**                                                       | **Content outline (2–3 lines)**                                                                                                   |
|------------------------|------------------------------------------|-------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| Club E5 (day 60)       | Your trade-in bonus just switched on     | +5% on any trade-in, from today.                                  | Trade-in panel; how a quote works; irons/driver trade-in examples; CTA get a quote.                                               |
| Pro E1 (day 0)         | Welcome to Evolution Pro                 | Free delivery on everything, 15% member price, 5 entries a month. | Clone of Club E1 with the Pro row highlighted; mention birthday voucher after 3 months and ask for birthday \[CONFIRM property\]. |
| Pro E2 (day 3)         | Ten free returns and how to use them     | Plus your five giveaway entries this month.                       | As Club E2, Pro numbers via Tier table.                                                                                           |
| Pro E4 (day 25)        | Your first month on Pro                  | The tally before renewal.                                         | As Club E4, adds +15% trade-in bonus line.                                                                                        |
| Pro E5 (day 85)        | Your birthday voucher unlocks next month | Have we got your date right?                                      | Ask for/confirm birthday; explain the voucher \[CONFIRM value/mechanics\]; one line on Annual saving vs monthly via Tier table.   |
| Annual E1–E2           | Welcome to Annual Pro / How to use it    | A year of Pro, paid once.                                         | As Pro E1/E2 with Annual row highlighted.                                                                                         |
| Annual E3 (day 30)     | Month one on Annual Pro                  | What you've saved against the £89.99 \[via Tier table\].          | Recap as Club E4.                                                                                                                 |
| Annual E4 (day 335)    | Your year on Annual Pro                  | The full tally, a month before renewal.                           | Year recap; what changed in the range; renewal date \[CONFIRM property\].                                                         |
| 2b Save E1 (downgrade) | You're still with us — on Free           | Your 5% member price stays. Here's what's changed.                | Neutral tone; Tier table; "if it was returns/price that swung it, tell us" reply prompt; no discount.                             |

3.3 Flow 3 — Checkout abandonment

Value-led for hardware, no code on trolleys or clubs, SMS after email.
Built as a new flow next to "NEW: Abandoned Checkout" and cut over on
one day.

a\) Purpose and success metric

|             | **Detail**                                                                                                                                                                                                                               |
|-------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose     | Recover started checkouts by removing the reasons people stall on a considered purchase (delivery, warranty, finance, fit) rather than paying them to finish.                                                                            |
| Primary KPI | Placed-order rate per entrant. Baseline: NEW 0.85% (email) / legacy 1.41%. Klaviyo peer median 2.07%. Target: ≥ 1.41% within 90 days, ≥ 2.07% in season. Revenue per recipient: baseline £4.90 (email), peer median £7.7; target ≥ £7.7. |
| Guardrail   | Gross margin per recipient must not fall versus the coded ladder (test T1). Unsubscribe ≤ 0.5%. Email 2 recipients ≥ 80% of Email 1 recipients (proves the smart-sending fix).                                                           |
| SMS         | Baseline 3.74% placed order, £6.42/recipient (peer £7.7). Target: hold ≥ 3.5% with no code.                                                                                                                                              |

b\) Trigger and flow filters

| **Setting**     | **Value**                                                                                                                                                                                                                        |
|-----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Trigger         | Metric: Checkout Started (Shopify)                                                                                                                                                                                               |
| Trigger filters | \$value is at least 30 (below £30 the flow is not worth the send).                                                                                                                                                               |
| Flow filters    | Placed Order zero times since starting this flow · Bounced Email zero times in last 30 days · Has not been in this flow in the last 7 days (re-entry, below) · in_abandon_flow does not equal "checkout" (belt-and-braces only). |
| Per-message     | SMS: Can receive SMS marketing. E2/E3 member branches: MemberTier is set / is not set.                                                                                                                                           |

c\) Re-entry and smart sending

| **Item**       | **Setting**                                                                                                                                                                                 |
|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Re-entry       | Allowed after 7 days (was 21). A golfer who abandons twice in a fortnight is a real prospect; once a week is the limit.                                                                     |
| Smart sending  | E1 ON · E2 ON · SMS ON · E3 ON. None off. E2 is at "1 day then 09:30" so it is never within 16h of E1.                                                                                      |
| Timing by path | Hardware (Trolleys, Clubs): E1 at 1 hour. Soft goods, Fallback: E1 at 45 minutes. All paths: E2 next day 09:30; SMS day 2 at 18:00; E3 day 3 at 09:30 (hardware) / day 3 at 17:30 (others). |

d\) Step-by-step map

| **Step** | **Type**          | **Exact setting / condition**                                                                                                                                                                  | **Message**                                                                                        |
|----------|-------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| 1        | Update property   | in_abandon_flow = checkout                                                                                                                                                                     |                                                                                                    |
| 2        | Trigger split     | Tags (or Route B Collections) contains flow_cat:trolleys → Trolleys; else contains flow_cat:clubs OR flow_cat:used → Clubs; else contains bags/footwear/clothing → Soft goods; else → Fallback | Four paths, in that order                                                                          |
| 3        | Delay             | Trolleys/Clubs 1 hour; others 45 minutes                                                                                                                                                       |                                                                                                    |
| 4        | Message           |                                                                                                                                                                                                | E1 — Your basket is saved (dynamic checkout items)                                                 |
| 5        | Delay             | 1 day, then 09:30                                                                                                                                                                              |                                                                                                    |
| 6        | Conditional split | MemberTier is set                                                                                                                                                                              | YES → E2m (member: "your member price is already applied") NO → E2 (non-member: value + join free) |
| 7        | Delay             | Until day 2, 18:00 (delay 1 day then "send at 18:00")                                                                                                                                          |                                                                                                    |
| 8        | Conditional split | Can receive SMS marketing                                                                                                                                                                      | YES → SMS 1                                                                                        |
| 9        | Delay             | 1 day, then 09:30 (hardware) / 17:30 (others)                                                                                                                                                  |                                                                                                    |
| 10       | Conditional split | Path is Soft goods or Fallback AND MemberTier is not set AND Layton has chosen the coded route                                                                                                 | YES → E3-FALLBACK (coupon). NO → E3 (member route / Alex email for hardware)                       |
| 11       | Update property   | in_abandon_flow = none                                                                                                                                                                         | End                                                                                                |

**Text diagram**

> TRIGGER Checkout Started · trigger filter \$value ≥ 30
>
> FILTERS no order since start · no bounce 30d · not in flow 7d
>
> SET in_abandon_flow = checkout
>
> TRIGGER SPLIT flow_cat
>
> Trolleys ─┐
>
> Clubs ─┤ wait 1h → E1 basket saved
>
> Soft ─┤ wait 45m → E1 basket saved
>
> Fallback ─┘
>
> wait 1 day → 09:30
>
> SPLIT member? yes → E2m \| no → E2 value + join free
>
> wait → day 2 18:00
>
> SPLIT SMS consent? yes → SMS 1
>
> wait → day 3 09:30 (hardware) / 17:30 (soft, fallback)
>
> SPLIT soft/fallback & non-member & coded route on?
>
> yes → E3-FALLBACK (unique 5%, 7 days)
>
> no → E3 (Alex, hardware) / E3 member-price (soft, fallback)
>
> SET in_abandon_flow = none

e\) Category logic

Trigger split creates four content paths from the eight flow_cat values:
**Trolleys** (trolleys), **Clubs** (clubs, used), **Soft goods** (bags,
footwear, clothing), **Fallback** (balls, accessories, unmatched). Eight
paths of near-identical content is what produced 24 placeholder messages
last time; four is enough, and the used/footwear differences are handled
by a line of copy, not a path.

| **flow_cat path**  | **Content angle**                                                                                      | **Proof points**                                                                                                  | **Cross-sell / next step**                                           |
|--------------------|--------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| Trolleys           | Reassurance on the big four: delivery, warranty, finance, "is this the right model". No discount ever. | 2-yr warranty \[CONFIRM\]; free delivery; Klarna/Clearpay from £x/mo \[CONFIRM\]; expert video review; Trustpilot | E3 from Alex: "want me to check it's the right one for your course?" |
| Clubs (incl. used) | Fit and confidence: custom-fit note, used grading, trade-in to offset                                  | Fitting centre; approved-used grading & guarantee \[CONFIRM\]; trade-in; Trustpilot                               | E3 from Alex: offer a fitting call; trade-in quote link              |
| Soft goods         | Size & returns confidence                                                                              | Returns window \[CONFIRM\]; member free returns; size guides                                                      | E3: member price route, or FALLBACK 5% coupon                        |
| Fallback           | Simple reminder; free delivery threshold                                                               | Free delivery over £30; Trustpilot                                                                                | E3: as soft goods                                                    |

f\) Seasonal variant (winter: 1 Nov – end Feb)

- Trolleys E2 winter: add "if you're parking this until spring, that's
  fine — here's the winter wheels and battery-storage note" line.

- December: Seasonal banner shows last order dates for Christmas
  delivery \[CONFIRM\]; this is a real deadline and may be stated.

- Soft goods winter: waterproof rating line replaces spikes line.

g\) Hand-off

| **Exit condition**                                          | **What happens**                                                                                                                                               | **Picked up by**            |
|-------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------|
| Places the order                                            | Exits at the next step check                                                                                                                                   | Flow 8 → 9                  |
| Adds a different item / starts checkout again within 7 days | Stays in this flow (no re-entry); dynamic block shows the latest checkout only if the template uses the trigger event — it will show the original. Acceptable. | —                           |
| Completes E3 without buying                                 | in_abandon_flow = none; eligible for browse/cart after 3–7 days; welcome resumes                                                                               | Flow 4/5; Flow 1; campaigns |
| Joins membership from E2                                    | Continues (member branch on later steps)                                                                                                                       | Flow 2 runs in parallel     |

h\) Retire, merge, salvage

| **Existing flow / message (audit name)**                              | **Action**                                                                                                                  |
|-----------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| NEW: Abandoned Checkout (category-routed) — 6 paths × 3 email + 2 SMS | Set to Manual the day this goes live (let profiles finish). Archive after export. Its SMS 2 (BASKET10) is not carried over. |
| 2\. SM Abandoned Checkout (draft, legacy)                             | Archive after export.                                                                                                       |
| Codes BASKET5 / BASKET10                                              | Removed from all flows; disable in Shopify after 30 days.                                                                   |

**Salvageable**

- Trolleys E1 and Clubs E1 content angles (they earned £1,881 and £753)
  — reuse their product presentation, fix the footer and rename.

- The SMS channel (3.74% placed order) — kept, moved after email, code
  removed.

i\) Build checklist and QA

Complete the standard checklist in 3.0, plus:

1.  Send yourself a real Checkout Started with a trolley, then with a
    glove: confirm Trolleys and Fallback paths, and that E1 renders the
    right items from event.extra.line_items.

2.  Confirm the checkout_url in E1 opens the saved checkout with items
    present.

3.  Check E2 "Skipped by smart sending" is near zero after the first
    week.

4.  Confirm the FALLBACK branch is only reachable on Soft goods/Fallback
    paths and that trolleys/clubs are excluded on the coupon in Shopify.

Draft copy

Trolleys path — in full

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F3 Trolleys E1 – Your trolley's
saved</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F3 Trolleys E1 – Basket saved</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Your trolley's saved, {{ person.first_name|default:'there' }}</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>We've kept your basket — and a couple of answers</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Free UK delivery, 2-year warranty, spread the cost. Pick up where
you left off.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Still deciding? Fair enough. It's a big buy.</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>Your basket is exactly where you left it.</p>
<p>{{ Checkout items dynamic table }}</p>
<p>The things people usually want to know before they commit:</p>
<p>• Delivery: free to the UK mainland, usually [CONFIRM] working
days.</p>
<p>• Warranty: 2 years on the trolley [CONFIRM per brand].</p>
<p>• Paying for it: Klarna or Clearpay at checkout if you'd rather
spread it [CONFIRM].</p>
<p>• Right model? Our team has filmed straight-talking reviews of the
Motocaddy range — link below.</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Back to my basket → {{ event.extra.checkout_url }}; secondary text
link: Watch our trolley reviews → [CONFIRM URL]</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Checkout Started items table (event.extra.line_items); USP bar;
Trust bar. No coupon block.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>The audit's Trolleys E1 made £1,881 from 100 people with a plain
reminder. This answers the four stall reasons in the same email.</td>
</tr>
</tbody>
</table>

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F3 Trolleys E2 – Non-member: how to be
sure</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F3 Trolleys E2 – How to be sure it's the right one</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>How to be sure it's the right trolley</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>Three checks before you buy an electric trolley</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Battery range, boot space, hills. Then a note on member
pricing.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Three quick checks</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>1. Range. Does the battery cover your usual round with margin?
18-hole lithium suits most; go 36 if you play twice on a Saturday
[CONFIRM].</p>
<p>2. Boot. Fold it in your head: will it go in with your bag?</p>
<p>3. Hills. If your course has them, downhill control matters more than
any gadget.</p>
<p>Still happy with your pick? Good. One more thing: join as a Free
member (30 seconds, no card) and you'll pay member price on this order —
that applies to trolleys, which codes never do. {{ Tier table block:
Free row }}</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Join free and finish my order →
https://members.evolutiongolf.co.uk?return={{
event.extra.checkout_url|urlencode }} [CONFIRM the portal supports a
return URL; fallback: two buttons — Join free / Back to basket]</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Tier table; Trade-in panel (trolley variant); Seasonal banner.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>The incentive is membership, not a code, so the trolley margin is
protected and the member count grows — both business goals in one
email.</td>
</tr>
</tbody>
</table>

| **Message**           | **Subject**                          | **Preview**                                                     | **Content outline (2–3 lines)**                                                                                                                                |
|-----------------------|--------------------------------------|-----------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Trolleys E2m (member) | Your member price is already on this | Log in and it applies at checkout. Anything else we can answer? | Same three checks; replace the join-free section with "you're a {{ person.MemberTier }} member — your price is applied when logged in"; CTA Back to my basket. |

|                                     |                                                                                                                                                                            |
|-------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **💬 F3 SMS 1 – Day 2 (all paths)** |                                                                                                                                                                            |
| **Message name**                    | F3 SMS 1 – Day 2 (all paths)                                                                                                                                               |
| **Body (169 chars)**                | Evolution Golf: your basket's still saved, {{ person.first_name\|default:'' }}. Free UK delivery, spread the cost with Klarna. Finish here: {{ event.extra.checkout_url }} |
| **Link**                            | {{ event.extra.checkout_url }}                                                                                                                                             |
| **Settings**                        | Quiet hours ON (08:00–20:00 local). Opt-out wording added by Klaviyo settings, not in body. Smart sending ON. Requires SMS consent.                                        |
| **Why**                             | Two full days after the checkout, after two emails, no code, no deadline. Replaces "Last call: 10% off with BASKET10. Ends tonight".                                       |

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F3 Trolleys E3 – From Alex</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F3 Trolleys E3 – Want a second opinion?</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Want a second opinion on that trolley?</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>Quick question about your trolley</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Tell me your course and how you play and I'll tell you if it's the
right model.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>Alex at Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Hi {{ person.first_name|default:'there' }},</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>Alex from Evolution Golf. I can see you were looking at the {{
event.extra.line_items.0.product.title }}. Good trolley.</p>
<p>If you're not sure it's the right one — the course you play, how
often, whether you'd use GPS — reply to this and I'll give you a
straight answer. If a cheaper model would do the job, I'll say so.</p>
<p>If you've already bought elsewhere, no problem at all. Ignore this
one.</p>
<p>Alex</p>
<p>Head of Ecommerce</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>None (reply). Text link: My basket → {{ event.extra.checkout_url
}}</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>First line item title. Plain template.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>A personal offer of advice is the only honest "last email" for a
£700 product, and it generates replies — a real signal for sales and for
deliverability.</td>
</tr>
</tbody>
</table>

Clubs path — in full

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F3 Clubs E1 – Your clubs are
saved</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F3 Clubs E1 – Basket saved</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Your clubs are saved</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>Saved your basket — and one thought on fit</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Free UK delivery. Custom fitting available. Trade-in your old set
against these.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Your basket is right here.</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>{{ Checkout items dynamic table }}</p>
<p>Three things that might help:</p>
<p>• Fit: if you'd like the lie, loft or shaft checked before we send
them, book 20 minutes at our fitting centre. It's the difference between
clubs you like and clubs you play well with. [CONFIRM: is fitting free
with purchase?]</p>
<p>• Trade-in: got an old set? Get a quote and take it off this
order.</p>
<p>• Approved used: every used club is graded and comes with our
guarantee [CONFIRM terms].</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Back to my basket → {{ event.extra.checkout_url }}; secondary: Book
a fitting → [CONFIRM URL]; Get a trade-in quote → [CONFIRM URL]</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Checkout items table; Trade-in panel (clubs variant); Trust
bar.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Clubs E1 already converts at 4.26%; the fitting and trade-in lines
address the two real objections for a clubs buyer.</td>
</tr>
</tbody>
</table>

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F3 Clubs E2 – Non-member</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F3 Clubs E2 – Two ways to pay less for these</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Two ways to pay less for those clubs</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>Trade-in plus member price, on your saved basket</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Member price applies to clubs. Trade-in takes more off. Neither is a
code.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>We don't discount clubs with codes. We do this instead.</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>Member price. Join free and your saved basket is charged at
member price. {{ Tier table: Free row }}</p>
<p>Trade-in. Old irons, an old driver, even a putter — we'll quote and
knock it off. {{ Trade-in panel }}</p>
<p>And if you want them checked for fit first, say so at checkout and
we'll call you before dispatch [CONFIRM process].</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Join free and finish my order → members portal (with return URL as
Trolleys E2); Back to my basket → {{ event.extra.checkout_url }}</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Tier table; Trade-in panel.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Puts trade-in — which no current flow mentions — in front of the
highest-value abandoners.</td>
</tr>
</tbody>
</table>

| **Message**        | **Subject**                         | **Preview**                                        | **Content outline (2–3 lines)**                                                               |
|--------------------|-------------------------------------|----------------------------------------------------|-----------------------------------------------------------------------------------------------|
| Clubs E2m (member) | Your member price is on these clubs | Log in and it's applied. Plus your trade-in bonus. | Member version; emphasise +5%/+15% trade-in bonus by tier via Tier table; CTA back to basket. |

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F3 Clubs E3 – From Alex</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F3 Clubs E3 – Shall I check the spec?</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Shall I check the spec on those clubs?</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>One question about your saved clubs</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Handedness, shaft flex, lie — a two-minute reply from me could save
you a return.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>Alex at Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Hi {{ person.first_name|default:'there' }},</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>Alex here. You had the {{ event.extra.line_items.0.product.title
}} in your basket. Before you buy — anywhere — it's worth being sure
about shaft flex, length and lie for your swing. Reply with your height,
handicap and what you play now, and I'll tell you whether the spec you
picked makes sense.</p>
<p>If you've gone elsewhere, no hard feelings.</p>
<p>Alex</p>
<p>Head of Ecommerce</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>None (reply). Text link: My basket → {{ event.extra.checkout_url
}}</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>First line item title.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Same logic as Trolleys E3: advice is the last touch, not a
code.</td>
</tr>
</tbody>
</table>

Soft goods and Fallback paths — outlines

| **Message**                        | **Subject**                  | **Preview**                                           | **Content outline (2–3 lines)**                                                                                     |
|------------------------------------|------------------------------|-------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| Soft E1 (45 min)                   | Saved your basket            | Free delivery over £30, easy returns. Right size?     | Items table; size guide link per category; returns window \[CONFIRM\]; CTA back to basket.                          |
| Soft E2 (day 1)                    | Not sure on size? Order two. | Members return free. Here's how.                      | Member free-returns benefit via Tier table; join free CTA; back to basket.                                          |
| Soft E3 member-price route (day 3) | Last note on your basket     | Member price, free delivery, done.                    | Items table; join-free CTA; no code.                                                                                |
| Soft E3-FALLBACK (day 3, coded)    | A little off your basket     | A one-time 5%, valid for 7 days, on everything in it. | Coupon block FLOW5-7D (shows real expiry); items table; CTA back to basket. Only if Layton selects the coded route. |
| Fallback E1 (45 min)               | You left something           | Free UK delivery over £30. Your basket's saved.       | Items table; USP bar; CTA back to basket.                                                                           |
| Fallback E2 (day 1)                | Still want these?            | Join free for member price on this order.             | Items table; Tier table Free row; CTA join free / back to basket.                                                   |
| Fallback E3 / E3-FALLBACK          | as Soft E3 / E3-FALLBACK     |                                                       | Same as Soft goods.                                                                                                 |

3.4 Flow 4 — Cart abandonment

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>Build gate — read before building</strong></p>
<p>Do not relaunch until every item in 2.7 (tracking checks) is complete
and Added to Cart identified profiles are back above ~400 a month. Until
then, the Week-1-fixed existing flow stays live on current volume.</p>
<p>Every cart template must be built fresh from the marketing master —
not cloned from a checkout template — and must use the Added to Cart
variables in 2.4. There is no checkout_url on this event.</p></td>
</tr>
</tbody>
</table>

a\) Purpose and success metric

|              | **Detail**                                                                                                                                                                                                             |
|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose      | Bring back people who added to cart but never reached checkout. Two emails and one SMS, dynamic products, cart link that works.                                                                                        |
| Primary KPI  | Revenue per recipient: baseline £1.54 (audit, rated Poor); Klaviyo peer median £7.7. Target: ≥ £4 within 90 days of tracking fix, ≥ £7.7 in season. Placed-order rate: baseline 0.80–0.94%, peer 2.07%; target ≥ 1.5%. |
| Guardrail    | Click rate stays ≥ 15% (it is already Excellent at 19.6% — the fix is the link, not the copy). Unsubscribe ≤ 0.5%.                                                                                                     |
| Volume check | Entrants ≥ 250/month after relaunch (legacy cart flow saw ~330/month). If not, tracking is still broken.                                                                                                               |

b\) Trigger and flow filters

| **Setting**     | **Value**                                                                                                                                                                                                                                                     |
|-----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Trigger         | Metric: Added to Cart (Klaviyo onsite / Shopify)                                                                                                                                                                                                              |
| Trigger filters | \$value is at least 30 \[CONFIRM \$value populates on this event; if not, remove the filter\].                                                                                                                                                                |
| Flow filters    | Placed Order zero times since starting this flow · Checkout Started zero times in the last 3 days (checkout flow owns them) · Bounced Email zero times in 30 days · in_abandon_flow does not equal "checkout" · Has not been in this flow in the last 7 days. |
| Per-message     | SMS: Can receive SMS marketing.                                                                                                                                                                                                                               |

c\) Re-entry and smart sending

| **Item**      | **Setting**                                                                                                                                                        |
|---------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Re-entry      | Allowed after 7 days.                                                                                                                                              |
| Smart sending | E1 ON · E2 ON · SMS ON.                                                                                                                                            |
| Timing        | Hardware paths: E1 at 3 hours (people compare trolleys across sites; an hour is too keen). Soft/Fallback: E1 at 1 hour. E2: 1 day then 09:30. SMS: day 2 at 18:00. |

d\) Step-by-step map

| **Step** | **Type**          | **Exact setting / condition**                                                                                                                                                                         | **Message**                                                               |
|----------|-------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| 1        | Update property   | in_abandon_flow = cart                                                                                                                                                                                |                                                                           |
| 2        | Trigger split     | AddedItemCategories / Tags (Route A/B) contains flow_cat:trolleys → Trolleys; clubs/used → Clubs; bags/footwear/clothing → Soft; else → Fallback \[CONFIRM property name on the Added to Cart event\] | Four paths                                                                |
| 3        | Delay             | Hardware 3 hours; others 1 hour                                                                                                                                                                       |                                                                           |
| 4        | Message           |                                                                                                                                                                                                       | E1 — "Still in your cart" with dynamic added item(s)                      |
| 5        | Delay             | 1 day, then 09:30                                                                                                                                                                                     |                                                                           |
| 6        | Conditional split | MemberTier is set                                                                                                                                                                                     | YES → E2m. NO → E2 (Fallback path: E2 or E2-FALLBACK per Layton's choice) |
| 7        | Delay             | To day 2, 18:00                                                                                                                                                                                       |                                                                           |
| 8        | Conditional split | Can receive SMS marketing                                                                                                                                                                             | YES → SMS 1 (link to /cart)                                               |
| 9        | Update property   | in_abandon_flow = none                                                                                                                                                                                | End                                                                       |

**Text diagram**

> TRIGGER Added to Cart · trigger filter \$value ≥ 30
>
> FILTERS no order since start · no Checkout Started 3d · no bounce ·
> not in flow 7d · in_abandon_flow ≠ checkout
>
> SET in_abandon_flow = cart
>
> TRIGGER SPLIT flow_cat → Trolleys \| Clubs \| Soft \| Fallback
>
> wait 3h (hardware) / 1h (others) → E1 still in your cart
>
> wait 1 day → 09:30
>
> SPLIT member? yes → E2m \| no → E2 (or E2-FALLBACK coupon on Fallback
> path)
>
> wait → day 2 18:00 → SPLIT SMS consent? yes → SMS 1 → /cart
>
> SET in_abandon_flow = none

e\) Category logic

Trigger split creates four content paths from the eight flow_cat values:
**Trolleys** (trolleys), **Clubs** (clubs, used), **Soft goods** (bags,
footwear, clothing), **Fallback** (balls, accessories, unmatched). Eight
paths of near-identical content is what produced 24 placeholder messages
last time; four is enough, and the used/footwear differences are handled
by a line of copy, not a path. Trolleys and Clubs paths reuse the
checkout E1/E2 copy angles (2.4 variables swapped to Added to Cart; CTA
to /cart).

| **flow_cat path** | **Content angle**                                                         | **Proof points**          | **Cross-sell / next step**                                                                    |
|-------------------|---------------------------------------------------------------------------|---------------------------|-----------------------------------------------------------------------------------------------|
| Trolleys          | As checkout Trolleys: delivery, warranty, finance, reviews. CTA to /cart. | As checkout               | No SMS on trolleys under E1 (SMS only if E1 clicked? — no: keep simple, SMS to all consented) |
| Clubs             | As checkout Clubs: fit, trade-in, used grading                            | As checkout               |                                                                                               |
| Soft goods        | Sizes and returns                                                         | Returns; size guides      |                                                                                               |
| Fallback          | Straight reminder; free delivery over £30; member price or coupon         | Free delivery; Trustpilot | Written in full below                                                                         |

f\) Seasonal variant (winter: 1 Nov – end Feb)

- As flow 3. Fallback E1 in December adds "buying a present? gift wrap /
  gift card" line \[CONFIRM offered\].

g\) Hand-off

| **Exit condition**       | **What happens**                                                                                                                                                                                                               | **Picked up by**  |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|
| Starts checkout          | Continues in this flow (Klaviyo does not exit for another metric), but flow 3 now owns them. To avoid a double, add flow filter "Checkout Started zero times since starting this flow" — profiles are exited at the next step. | Flow 3            |
| Places order             | Exits                                                                                                                                                                                                                          | Flow 8 → 9        |
| Completes without buying | in_abandon_flow = none; browse may pick them up after 7 days                                                                                                                                                                   | Flow 5; campaigns |

h\) Retire, merge, salvage

| **Existing flow / message (audit name)**                          | **Action**                                                                                                                                  |
|-------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| NEW: Abandoned Cart (category-routed) — 6 paths × 3 email + 1 SMS | Set to Manual the day this goes live; archive after export. Template Tf4UvB ("Abandonded Checkout Product Placeholder") must not be reused. |
| 8\. SM Abandoned Cart (draft); "Added to Cart Reminder" draft     | Archive after export.                                                                                                                       |

**Salvageable**

- Nothing from the NEW cart templates (cloned checkout links, static
  images). The legacy 8. SM cart flow's subject lines can be checked for
  click rate and reused if better.

i\) Build checklist and QA

Complete the standard checklist in 3.0, plus:

1.  Add a trolley to cart on the live site as a known profile; wait for
    E1; confirm the product image, name and price are the added item and
    the CTA opens /cart with the item in it.

2.  Repeat with a £5 item — should not enter (value filter) if \$value
    is present.

3.  Add to cart then start checkout: confirm the profile exits cart at
    the next step and flow 3 fires.

4.  Search every cart template's HTML for "checkout_url" — must return
    nothing.

Draft copy

Fallback path — in full

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F4 Fallback E1 – Still in your
cart</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F4 Fallback E1 – Still in your cart</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>You left this in your cart</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>Your cart's waiting, {{ person.first_name|default:'there' }}</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Free UK delivery over £30. It's all still there.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Left something behind?</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>Here's what's in your cart:</p>
<p>{{ Added to Cart items table — event.Items: image, name, qty, price
[CONFIRM] }}</p>
<p>Free UK delivery over £30, and if it's not right, returns are simple
[CONFIRM window]. Anything you're unsure about, reply and ask — we play,
we'll know.</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Back to my cart → https://evolutiongolf.co.uk/cart</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Added to Cart items table (NOT a checkout block); USP bar; Trust
bar.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>The current version had a 47% open, 0 clicks because the button was
dead. Same intent, working link, real products.</td>
</tr>
</tbody>
</table>

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F4 Fallback E2 – Member-price
route</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F4 Fallback E2 – Pay member price on this</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Pay member price on what's in your cart</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>Join free, save on this order</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Free membership, 30 seconds, applies to everything in your
cart.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Quick way to pay a bit less</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>Your cart is still saved:</p>
<p>{{ Added to Cart items table }}</p>
<p>Join as a Free member — name and email, no card — and you'll pay
member price on this order and every one after it. {{ Tier table: Free
row }}</p>
<p>Free UK delivery over £30 either way.</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Join free → https://members.evolutiongolf.co.uk; Back to my cart →
https://evolutiongolf.co.uk/cart</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Items table; Tier table; Seasonal banner.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Turns the second cart email into a membership acquisition
email.</td>
</tr>
</tbody>
</table>

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F4 Fallback E2-FALLBACK – Coded (Layton's
option)</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F4 Fallback E2-FALLBACK – A little off your cart</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>A little off what's in your cart</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>5% off your cart, one time, seven days</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>A one-use 5% code, valid for a week, on the items you saved.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Here's a nudge</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>{{ Added to Cart items table }}</p>
<p>Use this at checkout for 5% off your order. It's one use, it's yours,
and it runs out on the date below — that's a real date, not a marketing
one.</p>
<p>{{ Coupon block FLOW5-7D — prints code and expiry }}</p>
<p>Not valid on trolleys or clubs; minimum order £30.</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Back to my cart → https://evolutiongolf.co.uk/cart</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Items table; Coupon block (unique, 7-day expiry).</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>The only place in the abandonment family a code is allowed:
low-value baskets in accessories/apparel/balls, capped at 5%, with a
genuine expiry.</td>
</tr>
</tbody>
</table>

|                         |                                                                                                                                           |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| **💬 F4 SMS 1 – Day 2** |                                                                                                                                           |
| **Message name**        | F4 SMS 1 – Day 2                                                                                                                          |
| **Body (136 chars)**    | Evolution Golf: your cart's still saved, {{ person.first_name\|default:'' }}. Free UK delivery over £30. Have a look: {{ link to /cart }} |
| **Link**                | https://evolutiongolf.co.uk/cart (UTM short link)                                                                                         |
| **Settings**            | Quiet hours ON (08:00–20:00 local). Opt-out wording added by Klaviyo settings, not in body. Smart sending ON. Requires SMS consent.       |
| **Why**                 | Replaces the "expires in 4 hours" text. Sent after two emails.                                                                            |

Other paths — outlines

| **Message**         | **Subject**                           | **Preview**                                      | **Content outline (2–3 lines)**                                             |
|---------------------|---------------------------------------|--------------------------------------------------|-----------------------------------------------------------------------------|
| Trolleys E1 (3h)    | Your trolley's in your cart           | Free delivery, 2-year warranty, spread the cost. | Checkout Trolleys E1 copy with Added to Cart variables; CTA /cart.          |
| Trolleys E2 (day 1) | How to be sure it's the right trolley | Three checks, then member price.                 | Checkout Trolleys E2 copy; member/non-member split; CTA /cart or join free. |
| Clubs E1 / E2       | as checkout Clubs                     |                                                  | Checkout Clubs copy with cart variables.                                    |
| Soft E1 / E2        | as checkout Soft                      |                                                  | Size and returns; member free returns.                                      |

3.5 Flow 5 — Browse abandonment

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>Build gate — read before building</strong></p>
<p>Same gate as flow 4: tracking checks in 2.7 first. Browse is also the
flow reaching stale addresses (bounce 1.39% vs 0.30% peer), so the
engagement filter below is not optional.</p></td>
</tr>
</tbody>
</table>

a\) Purpose and success metric

|             | **Detail**                                                                                                                                                                                                                                                                      |
|-------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose     | Two education-led emails to engaged profiles who looked at hardware or footwear and did not add to cart. No product push, no code.                                                                                                                                              |
| Primary KPI | Revenue per recipient: baseline £0.15 (NEW) / £0.31 (legacy); Klaviyo peer median £0.98. Target ≥ £0.31 within 90 days, ≥ £0.98 in season. Click rate — no per-flow benchmark given in the audit; use the education variant's click rate from the live trolley test as the bar. |
| Guardrail   | Bounce rate ≤ 0.30% (from 1.39%); unsubscribe ≤ 0.38% (from 0.70%).                                                                                                                                                                                                             |

b\) Trigger and flow filters

| **Setting**     | **Value**                                                                                                                                                                                                                                                                                                                                                                                                             |
|-----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Trigger         | Metric: Viewed Product                                                                                                                                                                                                                                                                                                                                                                                                |
| Trigger filters | Tags / Categories contains any of flow_cat:trolleys, clubs, used, footwear, bags (hardware and footwear only — clothing, balls and accessories browsing does not justify an email) \[CONFIRM property\].                                                                                                                                                                                                              |
| Flow filters    | Placed Order zero times since starting this flow · Added to Cart zero times in last 7 days · Checkout Started zero times in last 7 days · in_abandon_flow is none or not set · Bounced Email zero times in 30 days · ENGAGED: (Opened Email at least once in last 90 days OR Clicked Email at least once in last 90 days OR Placed Order at least once in last 180 days) · Has not been in this flow in last 14 days. |
| Entry threshold | Keep "Viewed Product at least 2 times in the last 24 hours" as a flow filter (the audit's tighter filter did not lift quality, but a single view is too weak for hardware). Test T5 reads the effect.                                                                                                                                                                                                                 |

c\) Re-entry and smart sending

| **Item**      | **Setting**                                                                                                                  |
|---------------|------------------------------------------------------------------------------------------------------------------------------|
| Re-entry      | Allowed after 14 days (was 7).                                                                                               |
| Smart sending | E1 ON · E2 ON.                                                                                                               |
| Timing        | E1: 1 day then 09:30 (hardware browsing at 30 minutes is too soon — audit). Footwear: 4 hours. E2: 2 days after E1 at 17:30. |

d\) Step-by-step map

| **Step** | **Type**        | **Exact setting / condition**                                                                    | **Message**                                                                       |
|----------|-----------------|--------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| 1        | Update property | in_abandon_flow = browse                                                                         |                                                                                   |
| 2        | Trigger split   | Tags contains flow_cat:trolleys → Trolleys; clubs/used → Clubs; footwear → Footwear; bags → Bags | Four paths (no fallback — other categories are excluded at the trigger filter)    |
| 3        | Delay           | Trolleys/Clubs/Bags: 1 day then 09:30. Footwear: 4 hours.                                        |                                                                                   |
| 4        | Message         |                                                                                                  | E1 — education ("How to pick the right electric trolley", "Spiked or spikeless?") |
| 5        | Delay           | 2 days, 17:30                                                                                    |                                                                                   |
| 6        | Message         |                                                                                                  | E2 — proof + one relevant product block (recently viewed)                         |
| 7        | Update property | in_abandon_flow = none                                                                           | End                                                                               |

**Text diagram**

> TRIGGER Viewed Product · trigger filter flow_cat in {trolleys, clubs,
> used, footwear, bags}
>
> FILTERS no order since start · no ATC 7d · no checkout 7d · ENGAGED
> 90d · no bounce · ≥2 views 24h · not in flow 14d
>
> SET in_abandon_flow = browse
>
> TRIGGER SPLIT → Trolleys \| Clubs \| Footwear \| Bags
>
> wait 1 day → 09:30 (footwear: 4h) → E1 education
>
> wait 2 days → 17:30 → E2 proof + recently viewed
>
> SET in_abandon_flow = none

e\) Category logic

| **flow_cat path** | **Content angle**                                                                                                                                      | **Proof points**                       | **Cross-sell / next step**                               |
|-------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|----------------------------------------------------------|
| Trolleys          | E1 "How to pick the right electric trolley" (salvaged test variant). E2: expert video review + finance + warranty, with the viewed product shown once. | Warranty, reviews, finance, Trustpilot | None — the aim is add-to-cart, which hands off to flow 4 |
| Clubs             | E1 "Why fit before you buy" + approved used explained. E2: trade-in + fitting booking.                                                                 | Fitting centre, used grading, trade-in | Book fitting                                             |
| Footwear          | E1 "Spiked or spikeless?" (salvaged). E2: waterproofing and sizing, viewed shoe shown.                                                                 | Returns, size guide, staff picks       | None                                                     |
| Bags              | E1 stand vs cart bag for trolley users; E2 viewed bag + trolley compatibility note.                                                                    | Free delivery                          | Trolley owners → bag straps/compatibility                |

f\) Seasonal variant (winter: 1 Nov – end Feb)

- Trolleys E1 winter: "Layering for UK golf, briefly" is not relevant
  here — instead add the winter wheels/battery storage paragraph.

- Footwear E1 winter: lead with waterproof rating and winter grip;
  summer: breathability and spikeless.

g\) Hand-off

| **Exit condition**      | **What happens**                        | **Picked up by**                        |
|-------------------------|-----------------------------------------|-----------------------------------------|
| Adds to cart            | Filter exits at next step; flow 4 fires | Flow 4                                  |
| Starts checkout         | Exits; flow 3                           | Flow 3                                  |
| Buys                    | Exits                                   | Flow 8                                  |
| Finishes without action | Eligible again in 14 days               | Campaigns; flow 13 if no click 150 days |

h\) Retire, merge, salvage

| **Existing flow / message (audit name)**                        | **Action**                                                           |
|-----------------------------------------------------------------|----------------------------------------------------------------------|
| NEW: Browse Abandonment (category-routed) — 6 paths × 2 email   | Set to Manual, archive after export. Salvage its E2 content (below). |
| Browse Abandonment (2025) and (2026) drafts; 3. SM Browse draft | Archive after export.                                                |

**Salvageable**

- "Spiked or spikeless?" → Footwear E1.

- "How to pick the right electric trolley" (test variant) → Trolleys E1;
  end the test, keep the education variant.

- "Layering for UK golf, briefly" → Welcome E2c and Cross-sell
  footwear/clothing winter copy.

i\) Build checklist and QA

Complete the standard checklist in 3.0, plus:

1.  Create a test profile with no opens/clicks in 90 days and no orders
    — it must not enter.

2.  View a trolley twice, then add to cart: browse should exit at the
    next step and cart should fire.

3.  Confirm bounce and unsubscribe on E1 after two weeks are below the
    guardrail; if bounce is still above 0.5%, tighten the engagement
    window to 60 days.

Draft copy

Trolleys path

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F5 Trolleys E1 – How to pick the right
electric trolley</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F5 Trolleys E1 – Education</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>How to pick the right electric trolley</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>The five trolley questions, answered plainly</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Battery, boot, hills, GPS, remote. In that order.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Choosing an electric trolley, without the sales talk</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>Salvage the live test variant's body in full (it is the best
content in the account). Structure: 1 Range (18 vs 36 holes) · 2 Boot
space and fold size · 3 Hills and downhill control · 4 GPS: handle or
phone? · 5 Remote: will you use it?</p>
<p>Close: "Every trolley we sell comes with a 2-year warranty [CONFIRM]
and our team's honest video review. Spread the cost with Klarna or
Clearpay [CONFIRM]."</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Read the full guide → [CONFIRM URL]; secondary: See our trolley
reviews → [CONFIRM URL]</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>USP bar; Trade-in panel (trolley); Seasonal banner. No product block
in E1.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Education beat "still looking?" in the live test; E1 keeps that
content and moves it to a time when people will read it.</td>
</tr>
</tbody>
</table>

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F5 Trolleys E2 – The one you looked
at</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F5 Trolleys E2 – Proof + viewed product</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>About the {{ event.ProductName|default:'trolley' }} you looked
at</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>What our team thinks of the {{ event.ProductName|default:'trolley'
}}</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Our honest take, what it costs a month, and what's in the box.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>You were looking at this one</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>{{ Viewed product block: image, name, price, link }}</p>
<p>Our take: [insert 2-line staff verdict per model via a product-feed
field or a short universal block per top-5 model — [CONFIRM which models
get a verdict]].</p>
<p>From £x/month with Klarna [CONFIRM] · 2-year warranty [CONFIRM] ·
free UK delivery · Excellent on Trustpilot.</p>
<p>If you'd rather talk it through, reply to this email.</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>See it again → {{ event.URL }}</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Viewed Product single-product block; Trust bar; USP bar.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Shows the product once, with the team's opinion, and hands the
decision to the customer.</td>
</tr>
</tbody>
</table>

Footwear path

|                                             |                                                                                                                                                                                                                                                                                                                                 |
|---------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **✉ F5 Footwear E1 – Spiked or spikeless?** |                                                                                                                                                                                                                                                                                                                                 |
| **Message name**                            | F5 Footwear E1 – Spiked or spikeless                                                                                                                                                                                                                                                                                            |
| **Subject (A)**                             | Spiked or spikeless?                                                                                                                                                                                                                                                                                                            |
| **Subject (B, test)**                       | The shoe question we get asked most                                                                                                                                                                                                                                                                                             |
| **Preview text**                            | And the waterproof rating that actually matters in the UK.                                                                                                                                                                                                                                                                      |
| **Sender**                                  | ⛳ Evolution Golf \<info@evolutiongolf.co.uk\>                                                                                                                                                                                                                                                                                  |
| **Headline**                                | Spiked or spikeless?                                                                                                                                                                                                                                                                                                            |
| **Body**                                    | Salvage the existing "Spiked or spikeless?" email body. Structure: when spikes earn their keep (wet, hilly, winter) · when spikeless wins (dry, walking to the course, comfort) · the waterproof number to look for \[CONFIRM what the team recommends\] · sizing: golf shoes run \[CONFIRM\] — order two, members return free. |
| **CTA text → destination**                  | Shop golf shoes → footwear collection URL; secondary: Size guide → \[CONFIRM URL\]                                                                                                                                                                                                                                              |
| **Dynamic blocks**                          | USP bar; Seasonal banner (winter: waterproof lead).                                                                                                                                                                                                                                                                             |
| **Smart sending**                           | ON                                                                                                                                                                                                                                                                                                                              |
| **Why it should work**                      | The best browse content in the account, sent at 4 hours rather than 30 minutes and only to engaged profiles.                                                                                                                                                                                                                    |

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F5 Footwear E2 – The pair you looked
at</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F5 Footwear E2 – Viewed shoe + sizing</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Still thinking about the {{ event.ProductName|default:'shoes'
}}?</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>The shoes you looked at, and how they fit</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>How they size, how waterproof they are, how returns work.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>The pair you were looking at</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>{{ Viewed product block }}</p>
<p>Fit: [size note per brand via feed field or universal block —
[CONFIRM]]. Waterproof: [CONFIRM rating]. Returns: [CONFIRM window];
members return free.</p>
<p>Not sure between two sizes? Order both, keep one. Join free and
member price applies.</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>See them again → {{ event.URL }}; Join free → members portal</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Viewed Product block; Tier table Free row.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Answers the two footwear objections (size and wet feet) with the
product in view.</td>
</tr>
</tbody>
</table>

Clubs and Bags — outlines

| **Message** | **Subject**               | **Preview**                                     | **Content outline (2–3 lines)**                                |
|-------------|---------------------------|-------------------------------------------------|----------------------------------------------------------------|
| Clubs E1    | Why we fit before we sell | And why approved used might be the smart buy.   | Fitting explained; used grading \[CONFIRM\]; no product block. |
| Clubs E2    | The clubs you looked at   | Trade-in against them, or book a fitting first. | Viewed product block; Trade-in panel; fitting CTA.             |
| Bags E1     | Stand bag or cart bag?    | Depends whether you've got a trolley.           | Short guide; trolley compatibility.                            |
| Bags E2     | The bag you looked at     | Free UK delivery, fits most trolleys.           | Viewed product block; USP bar.                                 |

3.6 Flow 6 — Back in stock

Zero back-in-stock sign-ups in 12 months means the button is not live on
site. Step one is turning it on; the flow is the easy part.

a\) Purpose and success metric

|             | **Detail**                                                                                                                                                                                                                         |
|-------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose     | Capture demand for out-of-stock variants (sizes, shafts, left-handed, model changeovers) and tell people the moment stock lands. Variant-level, one email and one SMS.                                                             |
| Primary KPI | Placed-order rate per notification. No Klaviyo benchmark was available in the audit for this flow — set the baseline in the first 60 days. Sign-ups per month is the leading indicator (target: ≥ 50/month by month 3 — estimate). |
| Guardrail   | Notifications sent only when stock ≥ 1 for the exact variant; no "hurry, limited stock" text unless the live inventory quantity is shown.                                                                                          |

b\) Trigger and flow filters

| **Setting**                  | **Value**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
|------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Pre-requisite (no developer) | Klaviyo → Integrations → Shopify → Back in stock: enable, choose the button text ("Email me when it's back"), colours (#006747) and the modal copy. This uses the Klaviyo app embed on the product page for sold-out variants. Check it appears on a sold-out variant on the live theme. If the theme hides the add-to-cart area for sold-out variants, a developer may be needed — no-dev fallback: a Klaviyo sign-up form with a hidden "product interest" field on the product page, triggering a segment, which is cruder (not variant-level). |
| Trigger                      | Metric: Subscribed to Back in Stock. Klaviyo automatically adds the "Back in Stock delay" step that waits until inventory ≥ threshold.                                                                                                                                                                                                                                                                                                                                                                                                             |
| Trigger filters              | None                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Flow filters                 | Bounced Email zero times in 30 days. No purchase exclusion — a customer can want a second item.                                                                                                                                                                                                                                                                                                                                                                                                                                                    |

c\) Re-entry and smart sending

| **Item**      | **Setting**                                                                        |
|---------------|------------------------------------------------------------------------------------|
| Re-entry      | Allowed (per variant subscription — Klaviyo handles this).                         |
| Smart sending | Email OFF (expected, time-critical); SMS ON with quiet hours.                      |
| Timing        | Email immediately when stock returns; SMS 4 hours later if no click and consented. |

d\) Step-by-step map

| **Step** | **Type**            | **Exact setting / condition**                                                                                           | **Message**    |
|----------|---------------------|-------------------------------------------------------------------------------------------------------------------------|----------------|
| 1        | Back in Stock delay | Klaviyo default: wait until variant inventory ≥ 1; notify at most \[Klaviyo setting\] profiles per restock — set to all |                |
| 2        | Message             | Smart sending OFF                                                                                                       | E1 — It's back |
| 3        | Delay               | 4 hours                                                                                                                 |                |
| 4        | Conditional split   | Clicked Email zero times since starting this flow AND Can receive SMS marketing                                         | YES → SMS 1    |

**Text diagram**

> TRIGGER Subscribed to Back in Stock
>
> Back in Stock delay (wait for inventory)
>
> E1 It's back (smart sending OFF)
>
> wait 4h → SPLIT no click & SMS consent? yes → SMS 1

e\) Category logic

One template. Category shows only in a conditional line of copy
(show/hide by event property if Tags is available on the event;
otherwise omit).

| **flow_cat path** | **Content angle**                                              | **Proof points**          | **Cross-sell / next step** |
|-------------------|----------------------------------------------------------------|---------------------------|----------------------------|
| trolleys          | Model-year and colour restocks                                 | Warranty, finance         | —                          |
| clubs             | Shaft/flex/lefty restocks — say "the exact spec you asked for" | Fitting; used alternative | —                          |
| footwear          | Size restocks — "your size is back"                            | Returns                   | —                          |

f\) Seasonal variant (winter: 1 Nov – end Feb)

- None. This is a demand-driven flow.

g\) Hand-off

| **Exit condition**        | **What happens**                                                                 | **Picked up by** |
|---------------------------|----------------------------------------------------------------------------------|------------------|
| Buys                      | Nothing further from this flow                                                   | Flow 8 → 9       |
| Doesn't buy within 7 days | Klaviyo removes the subscription after notify; eligible for browse/cart normally | Flows 4/5        |

h\) Retire, merge, salvage

| **Existing flow / message (audit name)** | **Action**                   |
|------------------------------------------|------------------------------|
| None                                     | New flow. Nothing to retire. |

i\) Build checklist and QA

Complete the standard checklist in 3.0, plus:

1.  Set a test variant to 0 stock, subscribe with a test profile,
    restock to 1 in Shopify, confirm E1 arrives within minutes with the
    right variant name and image.

2.  Confirm the SMS does not send if E1 was clicked.

Draft copy

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F6 E1 – It's back</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F6 E1 – Back in stock</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>{{ event.ProductName|default:'The item you wanted' }} is back in
stock</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>Back in: {{ event.VariantName|default:'the one you asked about'
}}</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>You asked us to tell you. Here it is.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>It's back, {{ person.first_name|default:'there' }}.</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>You asked us to let you know when this came back into stock. It
has.</p>
<p>{{ Back in Stock product block: image, product, variant, price
[CONFIRM variables] }}</p>
<p>Free UK delivery over £30. Member price applies if you're logged in.
If it's gone again by the time you look, reply and we'll tell you when
the next lot is due [CONFIRM you can].</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Take me to it → {{ event.ProductURL }}</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Back in Stock block; USP bar.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>OFF (time-critical, requested)</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>A requested notification is the highest-intent email you can send;
it needs no persuasion, only speed and the right variant.</td>
</tr>
</tbody>
</table>

|                                 |                                                                                                                                     |
|---------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| **💬 F6 SMS 1 – Back in stock** |                                                                                                                                     |
| **Message name**                | F6 SMS 1 – Back in stock                                                                                                            |
| **Body (129 chars)**            | Evolution Golf: {{ event.ProductName\|default:'the item you asked about' }} is back in stock. Grab it here: {{ event.ProductURL }}  |
| **Link**                        | {{ event.ProductURL }}                                                                                                              |
| **Settings**                    | Quiet hours ON (08:00–20:00 local). Opt-out wording added by Klaviyo settings, not in body. Smart sending ON. Requires SMS consent. |
| **Why**                         | Only if the email was not clicked in 4 hours and the person has SMS consent.                                                        |

3.7 Flow 7 — Price drop

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>Build gate — read before building</strong></p>
<p><strong>Do not build yet.</strong> Requirements: (1) tracking checks
in 2.7 complete — the trigger relies on Viewed Product / Added to Cart;
(2) Klaviyo's Price Drop trigger available on the plan and the Shopify
catalogue synced [CONFIRM]; (3) a written pricing policy — under the
DMCC Act a "was/now" price must be a genuine previous selling price, so
price drops shown must come from the catalogue's real price history, not
a compare-at price that was never charged.</p>
<p>What would open the gate: Added to Cart volume restored; catalogue
sync confirmed; Alex confirms compare-at prices reflect real prior
prices. Then this is a half-day build.</p></td>
</tr>
</tbody>
</table>

a\) Purpose and success metric

|             | **Detail**                                                                                                                                                                      |
|-------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose     | Tell people who viewed or carted hardware in the last 30 days when its price falls. Strongest use in golf: left-handed clubs, prior model-year trolleys and shoes at clearance. |
| Primary KPI | Placed-order rate per notification. No benchmark in the audit; set baseline in first 60 days.                                                                                   |
| Guardrail   | Only send when the drop is ≥ 10% (Klaviyo threshold setting); never on items already in a live checkout (flow 3 owns them).                                                     |

b\) Trigger and flow filters

| **Setting**                                     | **Value**                                                                                                                                        |
|-------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| Trigger                                         | Klaviyo Price Drop trigger (based on Viewed Product / Added to Cart in the last 30 days, catalogue price change ≥ 10%) \[CONFIRM availability\]. |
| Flow filters                                    | Placed Order zero times since starting this flow · Checkout Started zero times in last 3 days · Bounced zero times 30d · Engaged 90d.            |
| No-dev fallback if the trigger is not available | A weekly manual campaign to a segment "Viewed hardware in last 30 days, no order" using a product feed sorted by discount — cruder but honest.   |

c\) Re-entry and smart sending

| **Item**      | **Setting**                                           |
|---------------|-------------------------------------------------------|
| Re-entry      | Allowed after 14 days.                                |
| Smart sending | Email ON (the drop is not time-critical to the hour). |

d\) Step-by-step map

| **Step** | **Type**          | **Exact setting / condition**  | **Message**                                   |
|----------|-------------------|--------------------------------|-----------------------------------------------|
| 1        | Message           | Immediately                    | E1 — Price drop on something you looked at    |
| 2        | Delay             | 3 days                         |                                               |
| 3        | Conditional split | Clicked zero times since start | YES → E2 (outline) — one reminder, no further |

**Text diagram**

> TRIGGER Price Drop (viewed/carted, ≥10%)
>
> E1 price dropped
>
> wait 3d → SPLIT no click? → E2 reminder

e\) Category logic

One template; category shows only in a copy line.

| **flow_cat path** | **Content angle**                                          | **Proof points**  | **Cross-sell / next step** |
|-------------------|------------------------------------------------------------|-------------------|----------------------------|
| trolleys/clubs    | Model-year clearance: "last season's model, same warranty" | Warranty; finance | —                          |
| footwear          | "Your size at the lower price"                             | Returns           | —                          |

f\) Seasonal variant (winter: 1 Nov – end Feb)

- Highest value at model-year changeovers (Jan–Mar trolleys/clubs) and
  end-of-summer footwear clearance (Sep).

g\) Hand-off

| **Exit condition** | **What happens**   | **Picked up by** |
|--------------------|--------------------|------------------|
| Buys               | Exits              | Flow 8           |
| Carts / checks out | Flows 4/3 own them | Flows 3/4        |

h\) Retire, merge, salvage

| **Existing flow / message (audit name)** | **Action** |
|------------------------------------------|------------|
| None                                     | New.       |

i\) Build checklist and QA

Complete the standard checklist in 3.0, plus:

1.  Check the "was" price shown is a price the item actually sold at
    (Shopify price history / order records) before setting live.

2.  Test a 10% drop on a test product with a test profile that viewed
    it.

Draft copy

| **Message**          | **Subject**                               | **Preview**                                                                                                   | **Content outline (2–3 lines)**                                                                                     |
|----------------------|-------------------------------------------|---------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| E1                   | Price drop on the {{ event.ProductName }} | Was £X, now £Y. You looked at it recently.                                                                    | Price Drop block (old/new price, image); one-line reason if known (new model in); warranty/finance; CTA to product. |
| E2 (day 3, no click) | Still at the lower price                  | The {{ event.ProductName }} — while it lasts at this price is a claim we won't make, so: it's still £Y today. | Same block; no urgency wording; CTA to product.                                                                     |

3.8 Flow 8 — Order confirmation (transactional)

Keep. Green in the audit (75% open, 16.9% click, smart sending off, no
UTMs). One QA pass and one decision.

a\) Purpose and success metric

|             | **Detail**                                                                                                                                       |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose     | Confirm the order, set delivery expectations, reduce "where is my order" tickets.                                                                |
| Primary KPI | Not revenue. Open rate ≥ 70% (baseline 75%); WISMO contacts per 100 orders (track in Zendesk — Alex).                                            |
| Guardrail   | Zero marketing content beyond a single "join free" line; no coupon; no upsell — it must stay transactional to be sent without marketing consent. |

b\) Trigger and flow filters

| **Setting**  | **Value**                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Trigger      | Metric: Placed Order                                                                                                                                                                                                                                                                                                                                                                                                                       |
| Flow filters | None (transactional)                                                                                                                                                                                                                                                                                                                                                                                                                       |
| Decision     | Shopify's own Order confirmation notification: if it is ON, customers get two. Recommendation: keep Klaviyo's (branded, trackable) and turn Shopify's off — but only after confirming Klaviyo's version contains everything Shopify's does (order number, items, prices, VAT, shipping address, payment summary, cancellation/returns information) \[CONFIRM — Consumer Contracts Regulations require durable confirmation of key terms\]. |

c\) Re-entry and smart sending

| **Item**      | **Setting**                             |
|---------------|-----------------------------------------|
| Re-entry      | Every order (allow re-entry, no delay). |
| Smart sending | OFF. UTMs OFF.                          |

d\) Step-by-step map

| **Step** | **Type** | **Exact setting / condition** | **Message**        |
|----------|----------|-------------------------------|--------------------|
| 1        | Message  | Immediately                   | Order confirmation |

**Text diagram**

> TRIGGER Placed Order
>
> Order confirmation (transactional, smart sending OFF)

e\) Category logic

None. One show/hide line for trolleys: "Your trolley ships in
\[CONFIRM\] working days; we'll email tracking".

f\) Seasonal variant (winter: 1 Nov – end Feb)

- December: show/hide block with Christmas delivery cut-off if the order
  date is before it — Karin swaps in on 1 Dec, out on 24 Dec.

g\) Hand-off

| **Exit condition**          | **What happens** | **Picked up by** |
|-----------------------------|------------------|------------------|
| Order fulfilled / delivered | Flow 9 fires     | Flow 9           |

h\) Retire, merge, salvage

| **Existing flow / message (audit name)** | **Action**                                                                                                                    |
|------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| Order Confirmation – Standard            | Keep. Check footer: transactional emails should not carry the marketing unsubscribe link, but must carry the company address. |

i\) Build checklist and QA

Complete the standard checklist in 3.0, plus:

1.  Place a test order; confirm one confirmation arrives, not two.

2.  Confirm order number, items, totals and address render from
    event.extra.

Draft copy

| **Message**        | **Subject**                                                                                                   | **Preview**                                            | **Content outline (2–3 lines)**                                                                                                                                      |
|--------------------|---------------------------------------------------------------------------------------------------------------|--------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Order confirmation | Order {{ event.extra.order_number\|default:'' }} confirmed — thanks, {{ person.first_name\|default:'there' }} | What you ordered, where it's going, when to expect it. | Existing content; add "track in your account" link; optional single line: "Not a member yet? Join free and your next order is at member price" (link only, no code). |

3.9 Flow 9 — Post-delivery onboarding + reviews

Triggered on Delivered Shipment so custom clubs, backorders and
pre-orders are included. Set-up and care first, review request timed by
category, cross-sell handed to flow 10.

a\) Purpose and success metric

|             | **Detail**                                                                                                                                                                                                                                               |
|-------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose     | Make sure the product gets used properly (fewer returns, fewer "it's broken" tickets), then ask for a review at the right moment per category.                                                                                                           |
| Primary KPI | Review submissions per 100 delivered orders (track in Trustpilot / review app — baseline unknown, no Klaviyo benchmark exists). Secondary: click rate on E1 (target ≥ 10% — estimate; the existing Post-Fulfillment flow's click rate was not reported). |
| Guardrail   | Zero discount. Unsubscribe ≤ 0.3% (these are fresh customers). Complaint rate on the review email watched weekly.                                                                                                                                        |
| Revenue     | Not the job of this flow. Baseline for the family is £209 from 712 sends; do not judge this flow on revenue — judge flow 10.                                                                                                                             |

b\) Trigger and flow filters

| **Setting**          | **Value**                                                                                                                                                                                             |
|----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Trigger              | Metric: Delivered Shipment \[CONFIRM this fires for all carriers you use; check the last 30 days' count vs Placed Order count — if under 80%, switch to Fulfilled Order and add a 3-day delay\].      |
| Trigger filters      | None                                                                                                                                                                                                  |
| Flow filters         | Bounced Email zero times 30d · Has not been in this flow in the last 30 days (a customer with two deliveries in a month gets one onboarding).                                                         |
| Route B for category | If Delivered Shipment carries no item tags, split on the profile: "Ordered Product where Tags contains flow_cat:trolleys at least once in the last 14 days" \[CONFIRM Ordered Product carries Tags\]. |

c\) Re-entry and smart sending

| **Item**      | **Setting**                                                                                                                                                                                                       |
|---------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Re-entry      | After 30 days.                                                                                                                                                                                                    |
| Smart sending | ON for all messages.                                                                                                                                                                                              |
| Timing        | E1 day 1 after delivery (09:30). E2 day 5 (trolleys/clubs care). Review: trolleys/footwear/bags day 14; clubs/used day 28; balls/clothing/accessories day 10. E4 (clubs only) day 35: fitting/trade-in follow-up. |

d\) Step-by-step map

| **Step** | **Type**           | **Exact setting / condition**                                                                 | **Message**                                                                                                      |
|----------|--------------------|-----------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| 1        | Trigger split      | flow_cat trolleys / clubs+used / footwear+bags / clothing+balls+accessories                   | Four paths                                                                                                       |
| 2        | Conditional split  | Placed Order equals 1 over all time                                                           | New customer → E1 includes "how we work" line; returning → E1 without it (show/hide block, not a separate email) |
| 3        | Delay              | 1 day, 09:30                                                                                  | E1 — It's arrived: set-up / first use                                                                            |
| 4        | Delay              | 4 days (=day 5), 17:30                                                                        | E2 — Care (trolleys: battery; clubs: grips & first rounds; footwear: waterproofing; others: skip)                |
| 5        | Delay              | Trolleys/footwear/bags: 9 days (=day 14). Clubs: 23 days (=day 28). Others: 5 days (=day 10). | E3 — Review request (Alex)                                                                                       |
| 6        | Delay (clubs only) | 7 days (=day 35)                                                                              | E4 — Fitting check-in + member trade-in bonus (outline)                                                          |

**Text diagram**

> TRIGGER Delivered Shipment (fallback: Fulfilled Order + 3d)
>
> FILTERS no bounce · not in flow 30d
>
> TRIGGER SPLIT flow_cat
>
> Trolleys: d1 E1 set-up → d5 E2 battery care → d14 E3 review
>
> Clubs: d1 E1 first rounds → d5 E2 grips & care → d28 E3 review → d35
> E4 fitting/trade-in
>
> Footwear/Bags: d1 E1 → d5 E2 waterproofing → d14 E3 review
>
> Other: d1 E1 → d10 E3 review
>
> (each E1 has a show/hide block for first-time customers)

e\) Category logic

| **flow_cat path**              | **Content angle**                                                                    | **Proof points**                                     | **Cross-sell / next step**                                                                                 |
|--------------------------------|--------------------------------------------------------------------------------------|------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| trolleys                       | Unbox, charge fully before first use, pairing, folding; how to register the warranty | 2-yr warranty registration \[CONFIRM\]; video guides | Hands to flow 10 at day 21: battery care kit, winter wheels, umbrella holder, cup holder, scorecard holder |
| clubs / used                   | First three rounds: what to expect, loft/lie adjust window \[CONFIRM\], grip care    | Fitting centre; used guarantee                       | Flow 10 day 30: balls, glove, grips; day 35 E4 fitting check-in + trade-in bonus                           |
| footwear / bags                | Break-in, waterproofing, cleaning                                                    | Returns window reminder \[CONFIRM\]                  | Flow 10: socks, spikes, waterproofing spray, bag accessories                                               |
| clothing / balls / accessories | Short thanks + how we work                                                           | —                                                    | Flow 11 (balls) / flow 10                                                                                  |

f\) Seasonal variant (winter: 1 Nov – end Feb)

- Trolleys E2 winter: add winter wheels and "storing the battery over
  winter" section; summer: cleaning after wet rounds.

- Clubs E1 winter: "if you won't play for a while, here's how to keep
  them right" line.

g\) Hand-off

| **Exit condition**                                       | **What happens**                                                                                                                                                                                                    | **Picked up by** |
|----------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------|
| Day 21 (trolleys) / day 30 (clubs) / day 14 (soft goods) | Flow 10 triggers from Placed Order with its own delays — not from this flow; they run in parallel by design                                                                                                         | Flow 10          |
| Places another order                                     | Not exited (onboarding for the first item still matters); flow 10 will exit                                                                                                                                         | Flow 8           |
| Leaves a review                                          | No further review asks — add a profile property review_requested = date to exclude from the next 180 days \[CONFIRM the review app writes an event to Klaviyo; if it does, use "Left a review zero times" instead\] | —                |

h\) Retire, merge, salvage

| **Existing flow / message (audit name)**                       | **Action**                                                                                                                      |
|----------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| NEW: Post-Fulfillment (6 paths × 4 email)                      | Set to Manual the day this goes live (let finish); archive after export. Template TzbA9t ("RETURN TO YOUR CART") is not reused. |
| NEW: Post-Purchase nurture (already off, 3,842 sends for £480) | Archive after export.                                                                                                           |
| 4\. SM Post Purchase (draft)                                   | Archive after export.                                                                                                           |

**Salvageable**

- Post-Fulfillment's new/returning split idea and its no-discount
  stance.

- Any existing care-guide content on the site (link, don't rewrite).

i\) Build checklist and QA

Complete the standard checklist in 3.0, plus:

1.  Compare Delivered Shipment and Placed Order counts for the last 30
    days before choosing the trigger; record the ratio in the register.

2.  Test with an order containing a trolley + balls: must go down
    Trolleys.

3.  Confirm the review link goes to the correct Trustpilot invitation
    URL and does not pre-fill a rating \[CONFIRM URL\].

4.  Check no email in this flow contains a discount or a cart link.

Draft copy

Trolleys path — in full

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F9 Trolleys E1 – It's arrived. Charge it
first.</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F9 Trolleys E1 – Set-up</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Your trolley's arrived. Do this first.</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>Before your first round with the new trolley</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Full charge, quick pairing, and where to register your
warranty.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>It's here. Three things before the first round.</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>1. Charge the battery fully before first use — even if it shows
charge. It sets the cells up right [CONFIRM per brand].</p>
<p>2. Pair the handle / app if your model has one. Our 90-second video:
[link].</p>
<p>3. Register the warranty. Two years [CONFIRM], but it needs
registering with the maker: [link per brand — CONFIRM].</p>
<p>{{ show/hide for first-time customers: "First order with us? Here's
how we work: real people who play, free UK delivery over £30, and if
anything's wrong, reply to this email." }}</p>
<p>How to fold it, how to fit the bag, how to set the speed — all in the
guide below.</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Open the set-up guide → [CONFIRM URL per brand or a single trolleys
care page]</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Show/hide block on Placed Order count = 1; brand-specific link via
show/hide on line item vendor [CONFIRM]; Trust bar.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>The most common trolley returns and tickets are set-up
misunderstandings. This prevents them and opens the relationship without
selling anything.</td>
</tr>
</tbody>
</table>

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F9 Trolleys E2 – Battery care</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F9 Trolleys E2 – Battery care (day 5)</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>How to make the battery last for years</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>Trolley battery care in five lines</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Charge after every round, never store it flat, keep it out of the
shed in winter.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Five lines on battery care</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>• Charge after every round, even a short one.</p>
<p>• Don't leave it flat for more than a day or two.</p>
<p>• Store it indoors, not in a cold garage — cold is what kills lithium
[CONFIRM per brand guidance].</p>
<p>• Every couple of months, run it to low and recharge fully.</p>
<p>• If it ever swells, gets hot or won't charge, stop using it and
reply to this email.</p>
<p>{{ Seasonal banner: winter → storing over winter + winter wheels
}}</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Read the full care guide → [CONFIRM URL]</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Seasonal banner.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Care content is read (it protects a £1k purchase) and it earns the
right to ask for a review nine days later.</td>
</tr>
</tbody>
</table>

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F9 Trolleys E3 – How's it going?
(review)</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F9 Trolleys E3 – Review request (day 14)</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>How's the trolley after two weeks?</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>Two rounds in — how's it going?</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>A quick word on how it's been would help the next golfer
choosing.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>Alex at Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Hi {{ person.first_name|default:'there' }},</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>Alex here. You've had the {{ line item title via feed/event —
CONFIRM }} for a couple of weeks now — enough for a round or two.</p>
<p>If it's going well, would you leave a short review on Trustpilot?
Honest ones help the next person choosing, and we read every one. If
it's not going well, don't review — reply to me and I'll sort it.</p>
<p>Either way, thanks for buying from a shop rather than a
warehouse.</p>
<p>Alex</p>
<p>Head of Ecommerce</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Leave a review → [CONFIRM Trustpilot invitation link]. Text link:
Something wrong? Reply to this email.</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Product title if available. Plain template.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Asks at 14 days (used, not just delivered), routes unhappy customers
to a person rather than a public review, and never incentivises the
review (DMCC: no fake or paid-for reviews).</td>
</tr>
</tbody>
</table>

Other paths — outlines

| **Message**            | **Subject**                              | **Preview**                                                                          | **Content outline (2–3 lines)**                                                                 |
|------------------------|------------------------------------------|--------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| Clubs E1 (d1)          | Your clubs are here. First three rounds. | What to expect while you adjust, and when to come back for a tweak.                  | Adjustment window \[CONFIRM\]; grip and headcover care; first-time-customer block; no products. |
| Clubs E2 (d5)          | Looking after new clubs                  | Grips, grooves and the boot of the car.                                              | Care tips; used-club guarantee reminder for used path.                                          |
| Clubs E3 (d28)         | Four rounds in — how are they?           | A short review helps the next golfer.                                                | Alex review request as trolleys E3.                                                             |
| Clubs E4 (d35)         | Fancy a fitting check?                   | Free tweak of loft and lie \[CONFIRM\], plus your trade-in bonus if you're a member. | Fitting booking; Trade-in panel; Tier table line on member bonus.                               |
| Footwear/Bags E1 (d1)  | They've landed. Break them in gently.    | And how to keep them waterproof.                                                     | Break-in; waterproof spray; returns window reminder \[CONFIRM\].                                |
| Footwear/Bags E2 (d5)  | Keeping golf shoes alive                 | Clean, dry, spray. Repeat.                                                           | Care; spikes replacement note (spiked shoes).                                                   |
| Footwear/Bags E3 (d14) | How are the shoes?                       | Two weeks in — a quick review?                                                       | Alex review request.                                                                            |
| Other E1 (d1)          | Thanks — it's on its way to being used   | How we work, and how to reach us.                                                    | Short thanks; first-time block; no products.                                                    |
| Other E3 (d10)         | Quick one: how did we do?                | A sentence on Trustpilot is plenty.                                                  | Alex review request (short).                                                                    |

3.10 Flow 10 — Cross-sell / second order

Replaces a flow that sent 1,864 emails, offered 5% then 10% twice, and
produced 0 orders. Category-timed, paired products, no code before the
final email.

a\) Purpose and success metric

|                   | **Detail**                                                                                                                                                                                                                      |
|-------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose           | Get the second order — the biggest lifetime-value lever — by offering the thing the first purchase makes them need, when they need it.                                                                                          |
| Primary KPI       | Click rate ≥ 5% (Klaviyo "All Flows" peer benchmark quoted in the audit; baseline 0.73%). Placed-order rate per recipient: baseline 0.00%; no category benchmark exists — target ≥ 1% is an estimate to be reset after 90 days. |
| Guardrail         | Gross margin per recipient ≥ the old flow (trivially, since it earned £0); unsubscribe ≤ 0.5%; no code before E3.                                                                                                               |
| Second-order rate | Business metric to track in Shopify: % of first-time buyers who order again within 120 days. Baseline unknown — pull it before go-live (Chapter 6).                                                                             |

b\) Trigger and flow filters

| **Setting**     | **Value**                                                                                                                                                                                                                                                      |
|-----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Trigger         | Metric: Placed Order                                                                                                                                                                                                                                           |
| Trigger filters | None at trigger; the delay differs by path.                                                                                                                                                                                                                    |
| Flow filters    | Placed Order zero times since starting this flow (a second order exits) · Bounced Email zero times 30d · Engaged: Opened or Clicked Email at least once in the last 90 days (checked at each step) · Has not been in this flow in the last 60 days.            |
| Route B         | If Placed Order carries no Tags: trigger split on "Collections" (Route B mapping) or use Ordered Product with Tags as the trigger (fires per line item — then add "Has not been in this flow in the last 60 days" to stop multi-item orders triggering twice). |

c\) Re-entry and smart sending

| **Item**       | **Setting**                                                                                                                                                                                               |
|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Re-entry       | After 60 days.                                                                                                                                                                                            |
| Smart sending  | ON.                                                                                                                                                                                                       |
| Timing by path | Trolleys: E1 day 21, E2 day 35, E3 day 50. Clubs/used: E1 day 30, E2 day 45, E3 day 60. Footwear/bags: E1 day 14, E2 day 30. Balls: handled by flow 11 (exit here). Clothing/accessories: E1 day 21 only. |

d\) Step-by-step map

| **Step** | **Type**          | **Exact setting / condition**                                                  | **Message**                                                                           |
|----------|-------------------|--------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| 1        | Trigger split     | flow_cat: trolleys / clubs+used / footwear+bags / balls / clothing+accessories | Five paths; balls path ends immediately (flow 11 owns it)                             |
| 2        | Delay             | Per path (above), 09:30                                                        |                                                                                       |
| 3        | Conditional split | Engaged 90d                                                                    | NO → end (do not mail the unengaged)                                                  |
| 4        | Message           |                                                                                | E1 — the paired item, at member price                                                 |
| 5        | Delay             | Per path                                                                       | E2 — second pairing / seasonal                                                        |
| 6        | Delay             | Per path (trolleys, clubs only)                                                | E3 — final: member route, or E3-FALLBACK (unique 5% on the paired accessory, 10 days) |

**Text diagram**

> TRIGGER Placed Order
>
> FILTERS no order since start · no bounce · engaged 90d · not in flow
> 60d
>
> TRIGGER SPLIT flow_cat
>
> Trolleys: d21 E1 battery care kit / winter wheels → d35 E2 umbrella &
> cup holder → d50 E3 final
>
> Clubs: d30 E1 balls + glove → d45 E2 grips / bag → d60 E3 final
> (fitting reminder)
>
> Footwear: d14 E1 socks + spikes + spray → d30 E2 second pair / bag
>
> Balls: → exit (flow 11)
>
> Clothing/Acc: d21 E1 pairs

e\) Category logic

| **flow_cat path**      | **Content angle**                                    | **Proof points**                         | **Cross-sell / next step**                                                                                                  |
|------------------------|------------------------------------------------------|------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| trolleys               | You've got the trolley — here's what makes it better | Member price; free delivery              | Battery care kit / spare battery, winter wheels (Nov–Feb lead), umbrella holder, cup holder, scorecard holder, travel cover |
| clubs / used           | New clubs deserve the right ball                     | Fitting; member trade-in bonus at day 60 | Driver → headcover, balls, glove. Irons → grips, bag. Putter → balls, alignment aid                                         |
| footwear / bags        | Keep them dry and gripping                           | Returns                                  | Shoes → socks, spikes, waterproofing spray. Bag → rain hood, towel, trolley straps                                          |
| clothing / accessories | One email: what goes with it                         | —                                        | Waterproof jacket → trousers/mitts; GPS → protective case, charging cable                                                   |

f\) Seasonal variant (winter: 1 Nov – end Feb)

- Trolleys E1 Nov–Feb leads with winter wheels and battery storage;
  Mar–Oct leads with battery care kit and umbrella holder (swap the
  "Cross-sell pairs" universal block on the calendar in 2.8).

- Clubs E1 Nov–Feb: winter balls (softer, coloured) and thermal glove.

g\) Hand-off

| **Exit condition**      | **What happens**                                  | **Picked up by**                                             |
|-------------------------|---------------------------------------------------|--------------------------------------------------------------|
| Second order placed     | Exits                                             | Flow 8 → 9 (again) → this flow does not re-enter for 60 days |
| Completes with no order | Eligible for winback at 120 days after last order | Flow 12                                                      |
| Balls buyer             | Exits at trigger split                            | Flow 11                                                      |

h\) Retire, merge, salvage

| **Existing flow / message (audit name)**                            | **Action**                                                   |
|---------------------------------------------------------------------|--------------------------------------------------------------|
| NEW: Second-Order Conversion (4 email)                              | Set to Manual the day this goes live; archive after export.  |
| Upsell – Clothing / Shoes / Clubs / Trolley (Manual since Jan 2026) | Archive after export; their pairing ideas are absorbed here. |

**Salvageable**

- Subject line "How's your last purchase working out?" — decent, but it
  belongs to flow 9 E3, not here.

i\) Build checklist and QA

Complete the standard checklist in 3.0, plus:

1.  Place a trolley test order; confirm entry, the 21-day wait and that
    the product feed in E1 shows trolley accessories only (feed filter
    by collection/tag — \[CONFIRM feed set-up\]).

2.  Confirm a balls order exits at the split.

3.  Confirm a second order during the flow exits it.

4.  Coupon in E3-FALLBACK: redeem on an accessory, check it fails on a
    trolley.

Draft copy

Trolleys path

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F10 Trolleys E1 – Three things trolley owners
add</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F10 Trolleys E1 – Day 21 pairs</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Three things most trolley owners add</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>Three weeks in: the bits that make the trolley better</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Battery care kit, a decent umbrella holder, and — if it's winter —
winter wheels.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Three weeks with the trolley. Here's what people add next.</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>You've had a few rounds with it now. These are the three things
trolley owners come back for:</p>
<p>{{ Cross-sell pairs block — trolley variant: battery care/spare,
umbrella holder, cup/scorecard holder (winter: winter wheels first)
}}</p>
<p>All at member price if you're logged in, free UK delivery over £30.
Not a member? It's free to join and it applies to this order.</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>See trolley accessories → [CONFIRM collection URL]</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Cross-sell pairs universal block (swapped seasonally) or a product
feed filtered to trolley accessories; Tier table Free row; Seasonal
banner.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Relevant, timed to actual use, and priced with the member benefit
instead of a code.</td>
</tr>
</tbody>
</table>

| **Message**                       | **Subject**                           | **Preview**                                                    | **Content outline (2–3 lines)**                                                             |
|-----------------------------------|---------------------------------------|----------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| Trolleys E2 (d35)                 | The umbrella holder question          | Which one fits your model, and why the cup holder is worth it. | Model-specific compatibility (show/hide by vendor) \[CONFIRM\]; two products; member price. |
| Trolleys E3 (d50) member route    | Last one on trolley accessories       | After this we'll leave you alone until winter wheels season.   | Recap of the three; Tier table; no code.                                                    |
| Trolleys E3-FALLBACK (d50, coded) | A little off your trolley accessories | One-time 5% on accessories, ten days.                          | Coupon block FLOW5-10D; accessories feed. Trolleys excluded on the coupon.                  |

Balls path — handled by flow 11 (see next chapter). The Clubs path
drafts:

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F10 Clubs E1 – New clubs, right
ball</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F10 Clubs E1 – Day 30 balls + glove</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>New clubs deserve the right ball</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>A month in with the new clubs — one small thing</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>The ball that suits your swing speed, and a glove that lasts. Member
price on both.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>A month in. How are they?</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>If the new clubs are settling in, the cheapest upgrade left is
the ball. Slower swing speed (under ~90 mph driver) — a softer ball;
faster — a firmer urethane ball [CONFIRM the team's guidance]. Unsure?
Reply with your driver distance and we'll say.</p>
<p>{{ Cross-sell pairs block — clubs variant: two balls (soft/firm), one
glove }}</p>
<p>Member price applies when logged in. Join free if you
haven't.</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Shop balls → balls collection URL; Shop gloves → [URL]</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Cross-sell pairs (clubs); Tier table Free row.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Uses the club purchase as the reason for the ball recommendation —
relevance is what the old flow lacked.</td>
</tr>
</tbody>
</table>

| **Message**           | **Subject**                           | **Preview**                                                                 | **Content outline (2–3 lines)**                                                              |
|-----------------------|---------------------------------------|-----------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| Clubs E2 (d45)        | Grips, and the bag they live in       | Regripping when, and a bag that fits your trolley.                          | Grips explainer; bag pairing; member price.                                                  |
| Clubs E3 (d60)        | Your fitting tweak and trade-in bonus | Loft/lie check \[CONFIRM\], plus +5%/+15% trade-in for members from day 60. | Fitting CTA; Trade-in panel; Tier table. No code — clubs path never gets the coded fallback. |
| Footwear E1 (d14)     | Socks, spikes, spray                  | The three things that make shoes last.                                      | Pairs block footwear; member price.                                                          |
| Footwear E2 (d30)     | A second pair for wet days?           | Most golfers rotate two pairs. Here's why.                                  | Pairs; returns; no code.                                                                     |
| Clothing/Acc E1 (d21) | What goes with it                     | Pairs for what you bought.                                                  | Pairs block; single email.                                                                   |

3.11 Flow 11 — Replenishment (consumables)

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>Build gate — read before building</strong></p>
<p><strong>Check volume before building.</strong> Run in Klaviyo:
segment "Ordered Product where Tags contains flow_cat:balls at least 2
times in the last 365 days". If it is under ~150 profiles, this flow is
not worth a build yet — put a balls block in flow 10 E1 instead. What
would change that: the balls range growing, or the membership base
(members buy consumables at member price) passing 1,000.</p>
<p>Season-paused: set to Manual 1 Nov, live 1 Mar. Balls and gloves
bought in October are not needed in December.</p></td>
</tr>
</tbody>
</table>

a\) Purpose and success metric

|             | **Detail**                                                                                                                                                     |
|-------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose     | Remind ball, glove and tee buyers when they are likely to be running low, in season, at member price.                                                          |
| Primary KPI | Placed-order rate per recipient — no Klaviyo benchmark in the audit; set baseline after 60 days. Repeat balls purchase rate in Shopify as the business metric. |
| Guardrail   | Max one email per 45 days per profile; unsubscribe ≤ 0.3%.                                                                                                     |

b\) Trigger and flow filters

| **Setting**                         | **Value**                                                                                                                          |
|-------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| Trigger                             | Metric: Placed Order                                                                                                               |
| Trigger filters                     | Tags contains flow_cat:balls (or Ordered Product with product type Golf Balls / Gloves / Tees) \[CONFIRM property\].               |
| Flow filters                        | Placed Order zero times since starting this flow · Engaged 90d · Bounced zero 30d · Has not been in this flow in the last 45 days. |
| Quantity-aware (optional, Option 2) | Trigger split on quantity: 1 dozen → 45 days; 2+ dozen → 60 days \[CONFIRM quantity field on event\]. Start without it.            |

c\) Re-entry and smart sending

| **Item**      | **Setting**               |
|---------------|---------------------------|
| Re-entry      | After 45 days.            |
| Smart sending | ON.                       |
| Season        | Live 1 Mar – 31 Oct only. |

d\) Step-by-step map

| **Step** | **Type**          | **Exact setting / condition**   | **Message**                                                                   |
|----------|-------------------|---------------------------------|-------------------------------------------------------------------------------|
| 1        | Delay             | 45 days, 09:30 (60 if 2+ dozen) |                                                                               |
| 2        | Conditional split | Engaged 90d                     | NO → end                                                                      |
| 3        | Message           |                                 | E1 — Running low?                                                             |
| 4        | Delay             | 7 days                          |                                                                               |
| 5        | Conditional split | Clicked zero times since start  | YES → E2 (member route) or E2-FALLBACK (unique 5%, 14 days) — Layton's choice |

**Text diagram**

> TRIGGER Placed Order · trigger filter flow_cat:balls (gloves, tees)
>
> FILTERS no order since start · engaged · not in flow 45d
>
> wait 45d (60d if 2+ dozen) → SPLIT engaged? → E1 running low?
>
> wait 7d → SPLIT no click? → E2 / E2-FALLBACK

e\) Category logic

This flow is consumables only. The product shown is the same product
they bought (dynamic from the order) with one alternative.

| **flow_cat path** | **Content angle**                       | **Proof points**                                                                    | **Cross-sell / next step** |
|-------------------|-----------------------------------------|-------------------------------------------------------------------------------------|----------------------------|
| balls             | Same ball, re-ordered in two clicks     | Member price; free delivery over £30 (a dozen usually clears it \[CONFIRM prices\]) | Glove, tees                |
| gloves            | A glove lasts ~15–20 rounds \[CONFIRM\] | Member price                                                                        | Balls                      |

f\) Seasonal variant (winter: 1 Nov – end Feb)

- Paused Nov–Feb. On 1 Mar, back-populate is NOT ticked — profiles who
  bought in autumn enter naturally from spring orders.

g\) Hand-off

| **Exit condition**  | **What happens**                                | **Picked up by** |
|---------------------|-------------------------------------------------|------------------|
| Reorders            | Exits; flow 9 "other" path and this flow re-arm | Flow 8           |
| No order by day 120 | Winback                                         | Flow 12          |

h\) Retire, merge, salvage

| **Existing flow / message (audit name)** | **Action**                                             |
|------------------------------------------|--------------------------------------------------------|
| NEW: Replenishment (draft)               | Rebuild per this spec; archive the draft after export. |

i\) Build checklist and QA

Complete the standard checklist in 3.0, plus:

1.  Confirm the ordered ball renders from the order event (image, name)
    and the reorder link goes to that product.

2.  Confirm the flow is set to Manual on 1 Nov (add to Karin's
    calendar).

Draft copy

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F11 E1 – Running low?</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F11 E1 – Running low (day 45)</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Running low on {{
event.extra.line_items.0.product.title|default:'balls' }}?</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>Time to top up the bag?</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Same ball, two clicks, member price, free delivery over £30.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>About six weeks since your last box.</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>If you've been playing, you're probably down to the scuffed ones.
Here's what you had last time:</p>
<p>{{ Ordered product block from Placed Order: image, name, price,
reorder link }}</p>
<p>Member price when logged in. Free UK delivery over £30. And if you
fancy trying something different, tell us your swing speed and we'll
suggest one.</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Reorder → {{ event.extra.line_items.0.product.url }} [CONFIRM]</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Placed Order line-item block; Tier table Free row; Seasonal
banner.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>A useful reminder, in season, with the exact product — nothing to
think about.</td>
</tr>
</tbody>
</table>

| **Message**              | **Subject**                | **Preview**                                      | **Content outline (2–3 lines)**             |
|--------------------------|----------------------------|--------------------------------------------------|---------------------------------------------|
| E2 member route (d52)    | Still got a few left?      | When you're ready, member price on the same box. | Same block; join free line; no code.        |
| E2-FALLBACK (d52, coded) | A little off your next box | One-time 5%, 14 days.                            | Coupon block FLOW5-14D; same product block. |

3.12 Flow 12 — Winback

Segment-triggered so the existing lapsed base enters, back-populated in
bands, main push timed for February–March pre-season. Replaces a flow
that has never sent and would first fire in January 2027.

a\) Purpose and success metric

|             | **Detail**                                                                                                                                                                                                             |
|-------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose     | Bring back customers whose last order was 120–365 days ago with what's new, member pricing and — last — a small coded nudge on soft goods only.                                                                        |
| Primary KPI | Placed-order rate per entrant within 30 days. No Klaviyo benchmark in the audit. Set the baseline on the first back-populated band; the audit puts the whole retention gap at £15–30k/yr, of which winback is a share. |
| Guardrail   | Unsubscribe ≤ 0.7%, bounce ≤ 0.3% — lapsed lists are where deliverability breaks. Only engaged lapsed customers are mailed.                                                                                            |

b\) Trigger and flow filters

| **Setting**   | **Value**                                                                                                                                                                                                                                                                                                                                                                                                                                    |
|---------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Trigger       | Segment "Winback – lapsed 120–365": Placed Order at least once over all time AND Placed Order zero times in the last 120 days AND Placed Order at least once in the last 365 days AND (Opened Email at least once in last 180 days OR Clicked Email at least once in last 180 days) AND Bounced Email zero times in last 30 days AND MemberTier is not "Evolution Pro" / "Evolution Pro Annual" (paid members are handled by flow 2 recaps). |
| Back-populate | When the flow is set live, tick "back-populate" but control the batch by narrowing the segment first: band 1 = last order 120–180 days ago; a week later widen to 120–270; a week later to 120–365. Each widening back-populates the new band. Do band 1 in the second half of February if the calendar allows; otherwise start now with band 1 only.                                                                                        |
| Flow filters  | Placed Order zero times since starting this flow · Has not been in this flow in the last 180 days.                                                                                                                                                                                                                                                                                                                                           |

c\) Re-entry and smart sending

| **Item**      | **Setting**                                                                |
|---------------|----------------------------------------------------------------------------|
| Re-entry      | After 180 days (a customer who lapses twice gets it twice a year at most). |
| Smart sending | ON.                                                                        |
| Timing        | E1 day 0 (09:30). E2 day 10. E3 day 24. Total 24 days, then done.          |

d\) Step-by-step map

| **Step** | **Type**          | **Exact setting / condition**                                                                      | **Message**                                                  |
|----------|-------------------|----------------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| 1        | Conditional split | Ordered Product with Tags contains flow_cat:trolleys OR flow_cat:clubs at least once over all time | Hardware buyers → hardware copy; else → soft goods copy      |
| 2        | Message           | Day 0, 09:30                                                                                       | E1 — What's changed since you were last here                 |
| 3        | Delay             | 10 days, 17:30                                                                                     | E2 — From Alex: anything we got wrong?                       |
| 4        | Delay             | 14 days, 09:30                                                                                     |                                                              |
| 5        | Conditional split | Soft-goods path AND Layton chose coded route                                                       | YES → E3-FALLBACK (unique 5%, 14 days). NO → E3 member route |

**Text diagram**

> TRIGGER segment "Winback – lapsed 120–365" (back-populated in bands)
>
> FILTERS no order since start · not in flow 180d
>
> SPLIT ever bought trolleys/clubs? → hardware copy \| soft copy
>
> E1 what's changed (d0)
>
> wait 10d → E2 Alex: anything we got wrong?
>
> wait 14d → SPLIT soft & coded? → E3-FALLBACK \| E3 member route

e\) Category logic

| **flow_cat path** | **Content angle**                                                               | **Proof points**            | **Cross-sell / next step**                                  |
|-------------------|---------------------------------------------------------------------------------|-----------------------------|-------------------------------------------------------------|
| hardware buyers   | What's new in trolleys/clubs this season; trade-in on what they bought; fitting | Trade-in; warranty; reviews | Trolley → accessories/battery; clubs → balls/glove/trade-in |
| soft goods buyers | New season range; member pricing                                                | Free delivery; returns      | E3 coded fallback allowed                                   |

f\) Seasonal variant (winter: 1 Nov – end Feb)

- E1 Feb–Mar: "new season" framing — the natural winback moment. E1
  Nov–Jan: gifting framing ("buying for a golfer?") rather than "come
  back and play".

- Avoid sending band widenings in Dec–Jan; hold them for Feb.

g\) Hand-off

| **Exit condition** | **What happens**                                 | **Picked up by** |
|--------------------|--------------------------------------------------|------------------|
| Orders             | Exits; flows 8 → 9 → 10                          | Flow 8           |
| No order, no click | Left alone; sunset picks up at 150 days no click | Flow 13          |
| Joins membership   | Flow 2                                           | Flow 2           |

h\) Retire, merge, salvage

| **Existing flow / message (audit name)**                                | **Action**                                                                                                                   |
|-------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| NEW: Winback (4 email, never sent; names say 15%/20%, templates 5%/10%) | Set to Manual now (it will not send until January anyway); archive after export. WINBACK5 disabled in Shopify after 30 days. |

i\) Build checklist and QA

Complete the standard checklist in 3.0, plus:

1.  Check the segment size at each band before widening; if band 1 is
    over 1,500, split it again (120–150, 150–180).

2.  Watch bounce and unsubscribe after the first 200 sends; pause if
    bounce \> 0.5%.

3.  Test profile: last order 200 days ago, opened an email 100 days ago
    → enters; last order 200 days ago, no opens in 180 days → does not.

Draft copy

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F12 E1 – What's changed since you were last
in</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F12 E1 – What's changed</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>A few things have changed since you were last in</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>New season, new trolleys, new pricing — a quick catch-up</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>Member pricing replaced codes. Trade-in got better. And the new
season's kit is in.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>It's been a while, {{ person.first_name|default:'there' }}.</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>Three things since your last order:</p>
<p>1. We scrapped most codes and started member pricing. Join free and
every order is at member price — trolleys and clubs included. {{ Tier
table }}</p>
<p>2. Trade-in got better. Old clubs or trolley off your next order;
members get a bonus on top. {{ Trade-in panel }}</p>
<p>3. The new season's range is in. {{ Seasonal banner }}</p>
<p>{{ hardware path: "If you're still using the [product] you bought
from us, the battery/grips might be due — reply and we'll advise." soft
path: bestseller feed, 3 months, filtered to soft goods }}</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Join free → members portal; See what's new → [new-in collection
URL]</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Tier table; Trade-in panel; Seasonal banner; path-specific show/hide
block; bestseller feed (soft path only).</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Gives three concrete reasons to look again, and converts the winback
into a membership acquisition.</td>
</tr>
</tbody>
</table>

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F12 E2 – From Alex</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F12 E2 – Anything we got wrong?</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Did we get something wrong?</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>Honest question from Evolution Golf</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>If your last order with us wasn't right, I'd like to know.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>Alex at Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Hi {{ person.first_name|default:'there' }},</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>Alex from Evolution Golf. You bought from us a while back and
haven't since — which is fine, golf kit lasts. But if something wasn't
right — delivery, the product, how we dealt with you — reply and tell
me. I'd rather fix it than guess.</p>
<p>If everything was fine and you just haven't needed anything, ignore
this and I'll stop bothering you after one more email.</p>
<p>Alex</p>
<p>Head of Ecommerce</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>None (reply).</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>None.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Replies from lapsed customers are the cheapest research you'll get,
and a plain email from a person outperforms a "we miss you"
template.</td>
</tr>
</tbody>
</table>

| **Message**                         | **Subject**                  | **Preview**                                                      | **Content outline (2–3 lines)**                                   |
|-------------------------------------|------------------------------|------------------------------------------------------------------|-------------------------------------------------------------------|
| E3 member route (d24)               | Last one from us for a while | Member price is there whenever you need something.               | Short; Tier table; Seasonal banner; no code.                      |
| E3-FALLBACK (d24, soft path, coded) | A small welcome back         | One-time 5% on clothing, shoes, balls and accessories — 14 days. | Coupon block FLOW5-14D; soft goods feed; trolleys/clubs excluded. |

3.13 Flow 13 — Sunset (re-permission, then suppress)

The account's spam rate is 2.3× peers and browse is bouncing at 1.39%.
This flow asks unengaged profiles once whether they want to stay, then
stops mailing them. The list will shrink; deliverability for the other
12 flows improves.

a\) Purpose and success metric

|             | **Detail**                                                                                                                                                                                                            |
|-------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Purpose     | Protect sender reputation by removing profiles that have not engaged in 150 days and not bought in 180.                                                                                                               |
| Primary KPI | Account-level: spam rate towards ≤ 0.008% (peer median), bounce ≤ 0.3% on browse, unsubscribe ≤ 0.73%. Flow-level: re-permission click rate (no benchmark; 2–5% is typical in our experience — treat as an estimate). |
| Guardrail   | Never sunset a paid member or anyone who bought in 180 days. Review segment size with Layton before go-live.                                                                                                          |

b\) Trigger and flow filters

| **Setting**   | **Value**                                                                                                                                                                                                                                                                                                                                                   |
|---------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Trigger       | Segment "Sunset candidates": Received Email at least 8 times over all time AND Opened Email zero times in last 150 days AND Clicked Email zero times in last 150 days AND Placed Order zero times in last 180 days AND MemberTier is not set to a paid tier AND Subscribed to List (Main Mailing List) more than 150 days ago AND sunset_status is not set. |
| Back-populate | Yes, in bands of ~2,000 by "Received Email" recency. Note Apple MPP inflates opens, so some genuinely disengaged profiles will not qualify — that is the safe error.                                                                                                                                                                                        |
| Flow filters  | Placed Order zero times since starting this flow · Clicked Email zero times since starting this flow (a click on E1 exits before E2).                                                                                                                                                                                                                       |

c\) Re-entry and smart sending

| **Item**      | **Setting**                                               |
|---------------|-----------------------------------------------------------|
| Re-entry      | Never (sunset_status property gates it).                  |
| Smart sending | ON.                                                       |
| Timing        | E1 day 0 (09:30). E2 day 10 (17:30). Property set day 17. |

d\) Step-by-step map

| **Step** | **Type**                    | **Exact setting / condition**                                                                                                           | **Message**                                                                |
|----------|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| 1        | Message                     |                                                                                                                                         | E1 — Still want these?                                                     |
| 2        | Delay                       | 10 days                                                                                                                                 |                                                                            |
| 3        | Conditional split           | Clicked Email zero times since starting this flow                                                                                       | YES → E2 — Last one unless you say so. NO → set sunset_status = kept → end |
| 4        | Delay                       | 7 days                                                                                                                                  |                                                                            |
| 5        | Conditional split           | Clicked zero times since start                                                                                                          | YES → Update property sunset_status = suppress. NO → sunset_status = kept  |
| 6        | Manual monthly step (Karin) | Segment "sunset_status = suppress" → Profiles → bulk suppress (Klaviyo → Lists & Segments → segment → Manage → Suppress). Export first. | Also: add "sunset_status is not suppress" to every campaign send segment.  |

**Text diagram**

> TRIGGER segment "Sunset candidates" (back-populated in bands)
>
> E1 still want these? (d0)
>
> wait 10d → SPLIT no click? yes → E2 last one \| no → SET kept
>
> wait 7d → SPLIT no click? yes → SET suppress \| no → SET kept
>
> MONTHLY: Karin bulk-suppresses the "suppress" segment

e\) Category logic

None. Two plain emails. Preference options in E1 use a Klaviyo
preference page (no-dev: Klaviyo hosted preference page with checkboxes
for trolleys, clubs, shoes & clothing, balls; handedness).

f\) Seasonal variant (winter: 1 Nov – end Feb)

- Do not run band back-populations in the two weeks before Black Friday
  or Christmas (you want the list at its most engaged for campaigns, and
  you want the flow to read cleanly).

g\) Hand-off

| **Exit condition** | **What happens**                                                                                      | **Picked up by**       |
|--------------------|-------------------------------------------------------------------------------------------------------|------------------------|
| Clicks E1 or E2    | sunset_status = kept; back in the normal base; welcome_complete profiles stay eligible for browse     | Campaigns; flows 5, 12 |
| No click           | Suppressed monthly; never mailed again unless they re-subscribe via a form (which clears suppression) | —                      |

h\) Retire, merge, salvage

| **Existing flow / message (audit name)** | **Action**                                                                                                           |
|------------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| None                                     | New. The engaged-only filters added to flows 5, 10 and 12 do the day-to-day work; this flow does the periodic clean. |

i\) Build checklist and QA

Complete the standard checklist in 3.0, plus:

1.  Export the candidate segment and sanity-check 20 profiles by hand:
    no paid members, no recent buyers.

2.  Confirm the preference page link renders and saves preferences to
    profile properties.

3.  After the first band, confirm account bounce and spam trend down
    over four weeks (Analytics → Deliverability).

Draft copy

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F13 E1 – Still want these?</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F13 E1 – Still want these?</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Still want emails from us?</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>Shall we keep sending these?</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>You haven't opened one in a while. Choose what you want — or
nothing.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>⛳ Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Quick check-in</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>We haven't heard from you in a while — no opens, no clicks — so
we'd rather ask than keep filling your inbox.</p>
<p>Tell us what you actually want to hear about and we'll only send
that:</p>
<p>[Trolleys] [Clubs] [Shoes &amp; clothing] [Balls &amp; accessories]
[Just the big sales]</p>
<p>Or nothing at all — the unsubscribe link is at the bottom, and it
works. If we don't hear from you, we'll send one more and then
stop.</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Choose what I get → {% manage_preferences_link %} (preference page
with the categories above)</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>Preference page link; no products; no offer.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>Plain, respectful, and it gives a click to count as engagement. Any
click keeps them.</td>
</tr>
</tbody>
</table>

<table>
<colgroup>
<col style="width: 22%" />
<col style="width: 77%" />
</colgroup>
<tbody>
<tr class="odd">
<td colspan="2"><strong>✉ F13 E2 – Last one unless you say
so</strong></td>
</tr>
<tr class="even">
<td><strong>Message name</strong></td>
<td>F13 E2 – Last one</td>
</tr>
<tr class="odd">
<td><strong>Subject (A)</strong></td>
<td>Last one from us, unless you say otherwise</td>
</tr>
<tr class="even">
<td><strong>Subject (B, test)</strong></td>
<td>We'll stop after this</td>
</tr>
<tr class="odd">
<td><strong>Preview text</strong></td>
<td>One click keeps you on the list. No click and we'll leave you
be.</td>
</tr>
<tr class="even">
<td><strong>Sender</strong></td>
<td>Alex at Evolution Golf &lt;info@evolutiongolf.co.uk&gt;</td>
</tr>
<tr class="odd">
<td><strong>Headline</strong></td>
<td>Hi {{ person.first_name|default:'there' }},</td>
</tr>
<tr class="even">
<td><strong>Body</strong></td>
<td><p>Alex from Evolution Golf. This is the last email we'll send
unless you tell us to keep going. No hard feelings either way — inboxes
are busy.</p>
<p>If you do want to stay, one click below does it.</p>
<p>Alex</p></td>
</tr>
<tr class="odd">
<td><strong>CTA text → destination</strong></td>
<td>Keep me on the list → {% manage_preferences_link %}</td>
</tr>
<tr class="even">
<td><strong>Dynamic blocks</strong></td>
<td>None.</td>
</tr>
<tr class="odd">
<td><strong>Smart sending</strong></td>
<td>ON</td>
</tr>
<tr class="even">
<td><strong>Why it should work</strong></td>
<td>A single, honest ask. Everyone who doesn't click is suppressed,
which is the point.</td>
</tr>
</tbody>
</table>

4\. Universal content blocks

Build these once in Klaviyo → Content → Universal content. Every flow
template drags the block in rather than typing the content. When pricing
changes (e.g. the single ~£36/yr tier), edit the block and every email
updates. Karin owns the swap calendar in 2.8.

<table>
<colgroup>
<col style="width: 13%" />
<col style="width: 19%" />
<col style="width: 47%" />
<col style="width: 20%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>Block</strong></th>
<th><strong>Where used</strong></th>
<th><strong>Copy / content</strong></th>
<th><strong>Notes</strong></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>Tier table</td>
<td>Welcome E1(T2)/E4; membership all; checkout/cart E2; browse footwear
E2; cross-sell; winback E1</td>
<td><p>Heading: "Member pricing, explained"</p>
<p>Rows (one per live tier, from the membership app — currently): Free —
£0 — 5% member price · free UK delivery over £30 · 1 point per £1. Club
Access — £3.99/mo — 10% · free delivery over £10 · 4 free returns a year
· 1 giveaway entry a month · +5% trade-in bonus after 60 days. Evolution
Pro — £9.99/mo — 15% · free delivery on everything · 10 free returns · 5
entries · +15% trade-in · birthday voucher after 3 months. Annual Pro —
£89.99/yr — everything in Pro, paid once.</p>
<p>Footer line: "Upgrade, downgrade or cancel any time in your
portal."</p>
<p>CTA: Join free / Compare tiers → members.evolutiongolf.co.uk</p></td>
<td>Make a second variant "Tier table – Free row only" for abandonment
emails. All prices [CONFIRM] against the app before publishing; this
block is the only place they live.</td>
</tr>
<tr class="even">
<td>USP bar</td>
<td>Every marketing email, above the footer</td>
<td>Free UK delivery over £30 [CONFIRM] · Expert advice from people who
play · 2-year warranty on trolleys [CONFIRM] · Trade-in on clubs and
trolleys · Klarna &amp; Clearpay available [CONFIRM] · Custom fitting
centre</td>
<td>Four icons max on mobile — drop fitting and finance on the mobile
variant if it wraps.</td>
</tr>
<tr class="odd">
<td>Trust bar</td>
<td>Welcome, checkout, browse E2, post-delivery E1</td>
<td>Trustpilot logo + "Rated Excellent" [CONFIRM current rating and
review count — pull the live widget if the Trustpilot–Klaviyo
integration is available; never hard-code a star count]</td>
<td>Under the DMCC Act the rating shown must be current and genuine;
re-check quarterly.</td>
</tr>
<tr class="even">
<td>Seasonal banner</td>
<td>Welcome E2–E4, checkout E2, post-delivery E2, cross-sell,
replenishment, winback E1, membership recaps</td>
<td><p>SUMMER (1 Mar–31 Oct): "New season, new kit. Trolleys, clubs and
shoes are in — see what's new." → new-in URL.</p>
<p>WINTER (1 Nov–end Feb): "Winter golf, sorted. Winter wheels,
waterproofs, mitts and range-ready balls." → winter collection URL
[CONFIRM exists].</p>
<p>BLACK FRIDAY (Nov, dates set by Alex): "Black Friday: members see
prices first. Join free." → portal.</p>
<p>CHRISTMAS (1–20 Dec): "Buying for a golfer? Gift cards and gifts
under £50. Last order for Christmas delivery: [CONFIRM date]." → gifts
URL.</p>
<p>MASTERS (first week Apr): "Masters week. Fitting slots open — book
yours." → fitting URL.</p>
<p>FATHER'S DAY (1–15 Jun): "Father's Day: gifts that get used. Gift
cards, gloves, balls." → gifts URL.</p>
<p>THE OPEN (Open week, Jul): "Open week: links golf gear — balls,
gloves, waterproofs." → collection URL.</p></td>
<td>One block, content swapped on the 2.8 calendar. Keep each variant
saved as a draft note inside the block description so swaps are
copy-paste.</td>
</tr>
<tr class="odd">
<td>Trade-in panel</td>
<td>Welcome E2b/E4; checkout &amp; cart clubs/trolleys; post-delivery
clubs E4; cross-sell clubs E3; winback E1</td>
<td><p>Heading: "Trade in what you've got"</p>
<p>Body: "Send us your old clubs or trolley and we'll take the value off
your order. Members get a bonus on top: Club Access +5%, Evolution Pro
+15% [CONFIRM — pull from Tier table wording]." Two variants: CLUBS
("irons, drivers, putters — any brand [CONFIRM]") and TROLLEY ("working
electric trolleys [CONFIRM accepted brands]").</p>
<p>CTA: Get a trade-in quote → [CONFIRM URL]</p></td>
<td>Uses the "Trade-in" and "Trade in after club order" drafts' content
if any is usable.</td>
</tr>
<tr class="even">
<td>Cross-sell pairs</td>
<td>Flow 10 E1/E2; flow 9 hand-off lines</td>
<td>Four variants, each 3 products with image, name, member price shown
as "Member price £X" [CONFIRM the feed can show member price; if not,
show RRP and the line "member price at checkout"]: TROLLEY summer
(battery care kit/spare battery, umbrella holder, cup &amp; scorecard
holder); TROLLEY winter (winter wheels, battery storage bag, umbrella
holder); CLUBS (soft ball, firm ball, glove); FOOTWEAR (socks, spikes,
waterproofing spray).</td>
<td>Swapped on 1 Nov / 1 Mar. Or replace with product feeds filtered by
collection if Karin prefers automatic.</td>
</tr>
<tr class="odd">
<td>Giveaway block</td>
<td>Membership E1/E3/E4</td>
<td>"This month's member giveaway: [prize]. Club members: 1 entry. Pro:
5. Drawn on [date] [CONFIRM mechanics and T&amp;Cs link]."</td>
<td>Updated monthly by Karin. T&amp;Cs link required.</td>
</tr>
<tr class="even">
<td>Footer</td>
<td>Every template</td>
<td>Company name, registered address, company number [CONFIRM] · {%
unsubscribe %} · {% manage_preferences_link %} · "You're receiving this
because you signed up at evolutiongolf.co.uk."</td>
<td>This is the fix for the hard-coded unsubscribe. Transactional
variant without the unsubscribe tag.</td>
</tr>
</tbody>
</table>

5\. Test plan (Section F mapped onto the new flows)

Only the welcome flow can reach statistical significance within a
season. Everything else is a directional read: run it, look at the
direction after 8–12 weeks, decide, move on. All tests are flow-level
random splits at entry (Klaviyo conditional split → random), not
per-message A/B tests, so the read is clean. Sample sizes are per arm at
95% confidence / 80% power, taken from the audit.

| **Test**                                         | **Where it lives in the new build**                                                                                                                                                                                                                                                                         | **Arms**                    | **Primary metric / guardrail**                                                                       | **Sample & read**                                                                                                        | **Decision rule**                                                                                                              |
|--------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------|------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| T1 Checkout: no code vs ladder                   | Flow 3, Trolleys and Clubs paths only. Arm B keeps a 5% coupon in E3 (labelled TEST-B; still never on trolleys — so on Clubs path only the accessory portion, i.e. this arm is really "no code" vs "no code + membership CTA"). Practical version: Arm A = E3 from Alex; Arm B = E3 member-price hard sell. | 50/50 random split at entry | Gross margin per recipient (needs margin by category — Q3 in Chapter 6); guardrail placed-order rate | ~5,500/arm for a 50% swing; you get ~1,400/yr. Run 12 weeks as a margin holdout. Directional only.                       | Keep whichever arm has higher margin/recipient unless conversion falls by more than the break-even (compute from margin data). |
| T2 Welcome offer: EVO5 vs member CTA             | Flow 1 E1: current E1 (EVO5) vs the T2 variant in this pack                                                                                                                                                                                                                                                 | 50/50 at entry              | Membership sign-up rate within 14 days (primary); first-order rate in 14 days (secondary)            | Conversion: ~10,500/arm (≈20 months — not practical). Sign-up rate: 3–6 months at current list growth. Read on sign-ups. | If member CTA sign-up rate ≥ 2× and first-order rate within 20% of EVO5 → switch to member CTA and retire EVO5.                |
| T3 Welcome E2: single trolley vs interest-routed | Already decided: the routed E2 replaces the single-trolley E2 (2.6% unsub is unacceptable). Instead test: routed E2 vs general E2d for everyone                                                                                                                                                             | 50/50 at entry              | Click rate; unsubscribe rate                                                                         | ~2,700/arm for a 25% click lift (6–9 months). Run the full season.                                                       | Keep routing if unsub ≤ 1% and click ≥ general arm.                                                                            |
| T4 Abandonment E2 timing                         | Flow 3: E2 at "1 day then 09:30" (default) vs E2 at +20h fixed                                                                                                                                                                                                                                              | 50/50 at entry              | Placed-order rate per entrant; guardrail smart-sending skips                                         | Directional; read after 8–10 weeks                                                                                       | Keep default unless the fixed-time arm is clearly ahead on both metrics.                                                       |
| T5 Browse E1: education vs reminder              | Flow 5, Trolleys and Clubs paths: education E1 (default) vs a plain "still looking?" E1 with the viewed product                                                                                                                                                                                             | 50/50 at entry              | Click rate → placed order                                                                            | ~2,850/arm for a 30% click lift; depends on tracking fix                                                                 | Keep education unless the reminder wins on placed order.                                                                       |
| T6 (new) Cross-sell timing                       | Flow 10 Trolleys: E1 at day 21 vs day 35                                                                                                                                                                                                                                                                    | 50/50 at entry              | Click rate; placed order                                                                             | Directional (~600 trolley orders/yr → ~300/arm)                                                                          | Move to the better day after one season.                                                                                       |

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<tbody>
<tr class="odd">
<td><p><strong>Volume reality check</strong></p>
<p>~7,600 orders a year and ~1,400 checkout abandoners a year means most
placed-order tests will not reach significance. Judge on the metric one
step earlier (click, sign-up, margin/recipient) and on direction. Run
one test per flow at a time. Log every test start/end date in the
register so no test runs seven months unattended again.</p></td>
</tr>
</tbody>
</table>

6\. Open questions and assumptions to confirm

Marked \[CONFIRM\] throughout. Answers to Q1–Q6 are needed before Week 2
builds start; the rest before the flow they affect.

| **\#** | **Question / assumption**                                                                                                                                                                                                                           | **Why it matters**                                                | **Affects**               | **Needed by**              |
|--------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|---------------------------|----------------------------|
| Q1     | Exact MemberTier property values (assumed "Free", "Club Access", "Evolution Pro", "Evolution Pro Annual"). Does the membership app also push a Klaviyo event on join/upgrade/cancel? Does a cancelled paid member become Free or lose the property? | Segments must use "equals"; an event trigger would remove flow 2b | Flows 1, 2, 2b, 3, 12, 13 | Week 1                     |
| Q2     | Does the Klaviyo Shopify integration put product tags on Checkout Started, Placed Order, Added to Cart, Viewed Product and Delivered Shipment in this account? What are the exact property names?                                                   | Decides Route A vs Route B for every split                        | All category splits       | Week 1                     |
| Q3     | Gross margin by flow_cat (at least: trolleys, clubs, soft goods, balls/accessories)                                                                                                                                                                 | Sets the coded-fallback break-even and makes T1 readable          | Discount policy; T1       | Week 2                     |
| Q4     | Klaviyo attribution window and whether opens count (Settings → Attribution). Assumed: Klaviyo default (5 days, clicks and opens).                                                                                                                   | All KPIs and targets are Klaviyo-attributed                       | All KPIs                  | Week 1                     |
| Q5     | Smart sending window (assumed 16h)                                                                                                                                                                                                                  | Every delay in this pack assumes 16h                              | All flows                 | Week 1                     |
| Q6     | Is Shopify's own order confirmation notification on? If yes, which to keep?                                                                                                                                                                         | Duplicate confirmations; legal completeness of the kept one       | Flow 8                    | Week 1                     |
| Q7     | Discount route decision per flow (member-pricing default vs coded fallback) — see 2.6                                                                                                                                                               | Which branch is switched on at build                              | Flows 1, 3, 4, 10, 11, 12 | Week 2                     |
| Q8     | Warranty length by trolley brand; delivery times; returns window; approved-used guarantee terms; fitting cost with purchase; Klarna/Clearpay availability and "from £/month" figures                                                                | Every \[CONFIRM\] in the copy                                     | Copy                      | Before each flow goes live |
| Q9     | Current Trustpilot rating and whether the Trustpilot–Klaviyo widget is available                                                                                                                                                                    | Trust bar must be live and genuine                                | Trust bar                 | Week 2                     |
| Q10    | Does the members portal accept a return URL so "Join free and finish my order" lands back at the checkout?                                                                                                                                          | Conversion of the member-price route in abandonment               | Flows 3, 4                | Week 2                     |
| Q11    | Delivered Shipment volume vs Placed Order over the last 30 days (is it ≥ 80%?)                                                                                                                                                                      | Trigger choice for flow 9                                         | Flow 9                    | Week 3                     |
| Q12    | Does the review platform write an event to Klaviyo when a review is left?                                                                                                                                                                           | Suppresses repeat review asks                                     | Flow 9                    | Week 3                     |
| Q13    | Number of profiles with 2+ balls orders in 12 months                                                                                                                                                                                                | Gate for flow 11                                                  | Flow 11                   | Week 6                     |
| Q14    | Is the Klaviyo Price Drop trigger available on the plan, is the catalogue synced, and do compare-at prices reflect genuine previous selling prices?                                                                                                 | Gate and legal basis for flow 7                                   | Flow 7                    | Week 7                     |
| Q15    | Baseline second-order rate (first-time buyers who order again within 120 days) from Shopify                                                                                                                                                         | The business metric for flow 10                                   | Flow 10                   | Week 5                     |
| Q16    | Cookie consent set-up on the store (strict opt-in or not) — set in Shopify Customer privacy                                                                                                                                                         | Explains part of the tracking drop and caps cart/browse volume    | Flows 4, 5, 7             | Week 1                     |
| Q17    | Does the Klaviyo email editor in this account offer "update profile property on link click"?                                                                                                                                                        | Interest capture method in flow 1                                 | Flow 1                    | Week 2                     |
| Q18    | Company registered address and number for the footer; monitored reply-to inbox for the Alex emails                                                                                                                                                  | Compliance; the personal emails invite replies                    | All templates             | Week 1                     |
| Q19    | Pricing change timing: if the single ~£36/yr tier lands during the build, when? The Tier table is the only place to change, but Free-branch copy about "double the discount" would need a rewrite.                                                  | Copy in flow 2 Free E2/E3                                         | Flow 2                    | As known                   |
| Q20    | Who signs off copy (assumed Alex) and who owns the seasonal swap calendar (assumed Karin)?                                                                                                                                                          | Ownership                                                         | All                       | Week 1                     |

Assumptions used in this pack

- Klaviyo default smart sending window (16h) and attribution settings.

- Membership app writes MemberTier as a profile property within minutes
  and does not send a tier-change event.

- Klaviyo Shopify integration passes product tags on order/checkout
  events (Route A); if not, Route B mapping is used identically
  everywhere.

- Added to Cart carries item fields and \$value but no checkout URL, per
  the audit.

- USPs as stated in the brief (free UK delivery over £30, 2-year trolley
  warranty, Trustpilot Excellent, Klarna/Clearpay, fitting centre,
  trade-in) are true and current.

- No developer: every mechanism here is Klaviyo/Shopify admin only; the
  two places a developer might be needed (back-in-stock button placement
  on a sold-out variant; theme.liquid comparison for the tracking drop)
  have no-dev fallbacks stated.

- SMS goes only to the existing consented SMS list, after at least one
  email, with quiet hours on and Klaviyo's opt-out wording.

- All revenue targets are Klaviyo-attributed, not incremental, and are
  targets rather than forecasts. Where the audit gave a benchmark it is
  used; where it did not, the pack says so.

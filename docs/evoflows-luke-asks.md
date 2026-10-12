# Evoflows: what we need from Luke (12 Oct 2026)

> **Update 12 Oct, Luke's answers:**
> - **Done:**
>   - Token rotated. The new one is in Railway; the old one is refused.
>   - Webhook verified (2 signed deliveries accepted).
>   - Money fields are two-decimal strings (`checkout.total` / `order.total` are numbers, for conditions only).
>   - `is_free_member` = Shopify tags `EvoMember` + `Free`. Annual = any of `AnnualMember`, `ClubhouseMember`, `Club`,
>     `Evolution Pro`, `Evolution Annual` (contract section 9.1).
>   - Both bugs fixed: the test sample now has real product images; preview returns HTML.
> - **F9:** nothing needed from Luke. Trigger `order_fulfilled`. Tokens: `.Tx.Data.total`, `.Tx.Data.order.created_at`,
>   `.fulfilled_at`, `.age_days`, `.first_item.title/.image/.url`, `.Tx.Data.order.source` (`"pos"` = till order).
> - **F4:** the cookie pop-up was fixed on 9 Oct, and the cart tracker went live on 12 Oct. Push F4 when the pack is ready.
> - **Still open:**
>   - F3 staff seed test and switch-on (with Luke), and the Klaviyo switch-off hour (Luke and Layton).
>   - Portal membership events: about an hour of work, not scheduled yet.
> - The engine reads Shopify tags only; Klaviyo's `MemberTier` can be ignored.
> - **Decision (Layton, 12 Oct):** none of our flows stays on Klaviyo; all move to Evoflows.
> - Live version: Claude Doc https://claude.ai/code/artifact/0cef0612-0079-431f-ba83-6d7b5a5a8ed4

**Where things stand:**
- F3 is built and pushed to Evoflows, and it is **switched off**. That covers the flags, the 8 templates and the flow (it passed validation).
- The dashboard reads `/flows`, `/metrics`, `/runs` and `/carts`.
- The webhook is registered.

Below is what only Luke can do, in order.

## A. Before F3 goes live

1. **Rotate the dashboard token.** It was pasted into a chat. Send the new one to Layton privately, not by email or chat.
   We'll put it in Railway (`EVOFLOWS_TOKEN`).
2. **Run the staff seed test and switch F3 on.** This is your job only. The dashboard has no way to switch flows on.
3. **Agree the switch-over time with Layton.** The old Klaviyo flow "NEW: Abandoned Checkout" must go off the same hour F3 goes
   on, or customers get two sets of emails. Layton turns it off in Klaviyo. The Klaviyo `EG · F3` draft stays off.
4. **Check the webhook fires.** Registered URL: `https://flow-dashboard-production-7b2a.up.railway.app/evoflows/hook`.
   - No deliveries had arrived by 12 Oct. That's expected while no flow is on, but please send one test delivery if you can.
   - Our receiver expects `X-Evoflows-Signature: sha256=<HMAC of the raw body>`. Without it, the receiver returns 401.
5. **Confirm the money format.** The templates print `£{{ .line_total }}` per item (`.price` if it's missing) and `£{{ .Tx.Data.total }}`.
   Please confirm these always come as two-decimal strings (`"799.00"`, not `799` or `799.5`).
6. **Confirm how `is_free_member` is set.** The F3 under-£300 emails show Free-member wording to Free members. Our
   Klaviyo audit found almost no Free-only profiles. What marks someone as Free in your data: the portal, or
   `EvoMember` without `AnnualMember`?

## B. Bugs on your side

7. **The "checkout" test sample has broken product photos.** Test sends show alt text instead of images. Real carts in
   `GET /carts` have working cdn.shopify.com links. Please put real Shopify image links in the sample.
8. **The preview endpoint returns a 500 error.** `POST /templates/{key}/preview` with `{"sample":"checkout"}` returns
   `500 JSONDecodeError` for every template. Test sends work.

## C. Needed for the next flows

9. **F9 (after delivery): confirm the order data.** We need the trigger name and these tokens: order total (credit
   amount), order date or age, the first item's title and image, and whether it was a till (POS) order. Then we push F9 v3.
10. **F4 (abandoned cart).** It uses the `cart_abandoned` trigger with `not_while_active_in: ["f3_checkout"]`. It's waiting
    on the cookie pop-up fix: the custom pop-up blocks Shopify's tracking consent. See `docs/handoff-consent-tracking.md`.
    Who on your side fixes the theme?
11. **Portal events: `membership_changed`, `membership_cancelled`, `signup_dropped`.** F2 (welcomes) needs these, and
    so does the "finish signing up" flow. Please give us a date.
12. **Membership tag clean-up.** Klaviyo's `MemberTier` and the Shopify tags disagree for about 285 people. This is
    sections 1–4 of the checklist Layton is going through with you.

## D. Later (nothing to do yet)

13. **Opens and clicks** (tracking pixel and click tracking), plus `contact.last_open_at`, `last_click_at` and `emails_received`.
    Until these exist, F12 (Winback) and F13 (Sunset) wait. They won't run on Klaviyo.
14. **A back-in-stock trigger.** Until there is one, F6 waits.

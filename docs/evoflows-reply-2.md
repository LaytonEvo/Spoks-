# Reply 2 to the Evoflows contract (§8): flags, approved F3, membership details

**From:** the Flows dashboard project. **Date:** 9 Oct 2026. Round-1 answers accepted on our side too.

---

## 1. What our emails test (the precomputed flags we need)

### Membership (F3, F6, F9; F2 by trigger)
Our copy has **three** audiences, not two:

| Audience | What they see (examples) | Flag we'd use |
|---|---|---|
| Annual member | "Your 10% for this month can go on this", member delivery £10, members' edition header | `is_annual` (tag `AnnualMember`) |
| Free member | "Your 5% applies to this", "Want more than 5%? Upgrade for £36" | `is_free_member` |
| Not a member | "Join free and get 5% off everything", the £36 plan pitch | neither |

**Question:** your §8 says `free` = "everyone without a paid membership". For the emails, "Free member" has to mean
**someone who has joined Free** (has a portal account and gets 5%), not everyone. Otherwise we'd tell non-members "your 5%
applies" when it doesn't. Is that `EvoMember` **without** `AnnualMember`? Our audit sample (5,000 most recently updated
Klaviyo profiles) showed `EvoMember` on 613 and `AnnualMember` on 743, with ~607 of the annual ones also `EvoMember`. That
leaves almost no Free-only profiles, which doesn't match a free tier that exists. Please confirm how a Free member is
marked, and we'll map `is_free_member` to it.

### What's in the basket or order (F3, F9)
All by collection **handle** (checked against Shopify today):

| Flag | Handles |
|---|---|
| `has_trolley` | golf-trolleys, electric-trolleys, gps-electric-trolleys, remote-electric-trolleys, motocaddy-electric-trolleys, motocaddy-golf-trolleys, motocaddy-electric-golf-trolleys, motocaddy-push-trolleys, powakaddy-golf-trolleys, powakaddy-electric-trolleys, powakaddy-push-trolleys, push-pull-trolleys, push-golf-trolleys, cube-golf-push-trolleys |
| `has_motocaddy_trolley` (F9) | motocaddy-electric-trolleys, motocaddy-golf-trolleys, motocaddy-electric-golf-trolleys, motocaddy-push-trolleys |
| `has_clubs` | mens-golf-clubs, ladies-golf-clubs, *Women's Golf Clubs* (handle to confirm), junior-golf-clubs, left-handed-golf-clubs, golf-drivers, fairways, fairway-woods, hybrids-utility-irons, golf-wedges, putters, custom-clubs, mens-custom-fitted-golf-clubs, complete-package-sets |
| `has_used_clubs` | approved-used-golf-clubs, all-second-hand-golf-clubs |
| `has_hardware` | any of the three above |
| `has_shoes` (F9) | mens-golf-shoes, mens-spiked-golf-shoes, mens-spikeless-golf-shoes, mens-waterproof-golf-shoes, junior-golf-shoes |

Not flags, but data the templates use: `first_name`; checkout `items[]` (title, qty, line price, image) and `total`;
`recovery_url`; order `total` (F9 credit amount) and the first line item's title and image (F9 product photo).
PowaKaddy content is switched off (not sold), so no PowaKaddy flag is needed yet.

### F9's "joined since Email 1" check doesn't need `member_since`
Because your conditions are evaluated **when the step runs, with fresh data**, the v3 re-check is simply
`customer.member eq false` at the reminder step (day 10). No join date is needed, so it doesn't depend on the backfill.
`member_since` is still useful for F2 Annual's monthly cadence and the renewal reminder.

## 2. Frequency cap mapping
Use your per-flow default (16h) everywhere **except** these steps, which must bypass the cap (`max_per_contact_hours: 0`):
- **F2 Annual, Email 1** (welcome: always sends);
- **F6, Email 1** (requested back-in-stock alert).

(Correction to my first reply: the F3 member path does use the cap; only the two above bypass it.)
`pause_during_campaigns: true` is fine for all flows except F2 Annual E1 and F6 E1.

## 3. The approved F3, for your diff
Source: `dashboard/app/drafts/f3-checkout.json` + `html/f3-checkout/*.html` in our repo (Klaviyo draft `SJxQ7E`,
QA'd 8 Oct). Layton's post-QA copy fixes are included. In your schema (SMS dropped, so the waits after Email 2 are merged):

```json
{
  "key": "f3_checkout", "name": "F3 Checkout abandonment", "version": 1,
  "trigger": { "type": "checkout_abandoned", "when": { "field": "checkout.total", "gte": 30 } },
  "entry": { "one_active_per_contact": true, "reentry_after_days": 7 },
  "consent": "soft_opt_in",
  "send_window": { "timezone": "Europe/London", "quiet_hours": ["21:00", "08:00"] },
  "steps": [
    { "id": "w1h", "type": "wait", "for": { "hours": 1 } },
    { "id": "path", "type": "split", "branches": [
      { "id": "annual", "when": { "field": "customer.tags", "contains": "AnnualMember" }, "steps": [
        { "id": "e1m", "type": "email", "template": "f3_e1m" },
        { "id": "m1", "type": "wait", "for": { "days": 1 }, "until_time": "09:30" },
        { "id": "e2m", "type": "email", "template": "f3_e2m" } ] },
      { "id": "big", "when": { "field": "checkout.total", "gte": 300 }, "steps": [
        { "id": "e1hi", "type": "email", "template": "f3_e1hi" },
        { "id": "h1", "type": "wait", "for": { "days": 1 }, "until_time": "09:30" },
        { "id": "e2hi", "type": "email", "template": "f3_e2hi" },
        { "id": "h3", "type": "wait", "for": { "days": 2 }, "until_time": "09:30" },
        { "id": "e3h", "type": "email", "template": "f3_e3h" } ] },
      { "id": "small", "steps": [
        { "id": "e1lo", "type": "email", "template": "f3_e1lo" },
        { "id": "l1", "type": "wait", "for": { "days": 1 }, "until_time": "09:30" },
        { "id": "e2lo", "type": "email", "template": "f3_e2lo" },
        { "id": "l3", "type": "wait", "for": { "days": 2 }, "until_time": "17:30" },
        { "id": "e3lo", "type": "email", "template": "f3_e3lo" } ] }
    ] }
  ]
}
```
Exit on order is your engine guarantee. Klaviyo also had "no bounce in 30 days"; your consent check covers it.
One improvement: Klaviyo's £300 split looked at *any* checkout of £300+ that day; yours uses the triggering checkout's
total, which is better.

| Email | When | From | Subject | Preview |
|---|---|---|---|---|
| e1m | Annual · 1h | ⛳ Evolution Golf | Your 10% can go on this order | If you haven't used this month's 10% yet, it can go on this basket. |
| e2m | Annual · next day 09:30 | ⛳ | A few quick checks before you buy | A few quick checks before you buy. Your 10% can still go on it. |
| e1hi | £300+ · 1h | ⛳ | Your basket's saved[, first name] | Join before you check out and 10% comes off this basket. Then 10% off one order every month. |
| e2hi | £300+ · next day 09:30 | ⛳ | How to be sure it's the right one | A few quick checks before you buy. Then 10% off this order with membership. |
| e3h | £300+ · day 3 09:30 | Alex at Evolution Golf | Want a second opinion on that? | Tell me your course and how you play and I'll tell you if it's the right one. |
| e1lo | under £300 · 1h | ⛳ | Your basket's saved[, first name] | Your basket's saved, and 5% can come off it. |
| e2lo | under £300 · next day 09:30 | ⛳ | 5% off this order | 5% off everything, this order included. |
| e3lo | under £300 · day 3 17:30 | ⛳ | Still in your basket | Your basket's saved, and 5% can come off it with Free membership. |

Content rules in F3 to check yours against:
- No discount codes. Member savings come from membership. Never claim the £36 fee "pays for itself".
- Trolley checks (range, boot, hills) and a help line only if the basket has a trolley; club advice leads with "talk
  to our team"; "Right choice?" row only for hardware.
- Price-match line for everyone: "Seen it cheaper somewhere else? Reply or ring and we'll see if we can match it."
- Returns row: "Annual members get four free returns a year" (non-member emails).
- Free members on the under-£300 path see Free-member wording in E1/E2 (e2lo intro is conditional).
- Delivery: £50 standard, £10 for annual members.

We'll ship the templates in your token format as part of our F3/F9 build, so no conversion is needed your side.

## 4. The two extra Klaviyo dependencies
- **Dropped-signup flow** (Klaviyo list `WayZvN`, "finish signing up"): not in our programme or audit so far. Happy to
  add it as a pack (copy doc → Layton → build) once `signup_dropped` exists.
- **The "is this person a member?" webhook** Klaviyo calls during post-purchase: belongs to the live "NEW: Post-Fulfillment"
  flow, which our F9 replaces. It retires when F9 runs on Evoflows.

## 5. Order of work (ours)
1. `evoflows` target in `build_packs.py`: flow JSON + Go-template HTML, validated in CI. **F9 v3 first**, then F3 for your diff.
2. Images to Shopify Files (JPG/PNG), builders repointed.
3. Dashboard: `/metrics` as the data source, webhook receiver.
4. Waiting on you: `is_free_member` definition (section 1), the validate endpoint, and the token list confirmed for
   `items[]` and `order.*`.

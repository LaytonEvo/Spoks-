# Phase 4: QA review pack (8 Oct 2026)

Read-only checks of the 7 new `EG ·` drafts in Klaviyo against the approved packs. Nothing was created, edited, sent or switched on.

Method: each flow was read back from Klaviyo and walked step by step against its pack (trigger, filters, every split, wait, send
time, sender, subject, preview, SMS, profile update). Every template in Klaviyo was compared with the approved HTML, and rendered with
test data (trolley / clubs / small baskets; Motocaddy / PowaKaddy; annual / Free / non-member; with and without a first name).
Links and images were checked. Copy was swept for codes, deadlines, made-up figures and leftover placeholders.

## Result per flow

| Flow | Klaviyo id | Structure vs pack | Emails vs pack | Renders | Status |
|---|---|---|---|---|---|
| EG · F1 Welcome v3 | XXpu28 | 18/18 steps match | 7 templates match | OK | **1 must-fix** (placeholder badge) |
| EG · F2 Membership · Free | Y5dese | 7/7 match | 3 match | OK | Pass |
| EG · F2 Membership · Annual | UQTuXm | 25/25 match | 13 sends, 6 templates match | OK | Pass |
| EG · F3 Checkout abandonment | SJxQ7E | 22/22 match (8 emails, 3 texts) | 8 match | OK | Pass, 2 copy fixes advised |
| EG · F9 After delivery + review | RsuJHT | 52/52 match, 33 splits | 23 match | 15 renders OK | Pass, 2 fixes advised |
| EG · F12 Winback | QQicb5 | 12/12 match | 6 match | OK | Pass |
| EG · F13 Sunset | XrnVxd | 6/6 match, profile update correct | 2 match | OK | Pass, manual steps essential |

All 7 are drafts (switched off). Differences found between Klaviyo and the packs were formatting only (Klaviyo re-saves CSS and
"09:30" as "09:30:00"). Segments: "EG · Members · Annual", "EG · Winback · lapsed customers" and "EG · Sunset · candidates" are active
and each already holds 100+ people (exact counts on each segment's page in Klaviyo).

Links: every evolutiongolf.co.uk link returns 200 (sale, members page, contact, collections, Klarna, fitting; trade-in redirects
fine). All 16 Klaviyo-hosted images are in the Klaviyo library and not hidden; the icon images load. Trustpilot, the members portal,
the Motocaddy and PowaKaddy registration pages and the social links couldn't be reached from this sandbox: check them in test sends.

## Must fix before switching on

1. ~~**F1 E2 Hardware shows a "CONFIRM grading wording" badge**~~ Done 8 Oct (rescanned). after "Every set is checked before it goes on sale". Confirm that line
   is true (or give the wording), then remove the badge in the Klaviyo editor (template XfKb47). The API can't edit flow emails.
2. **F13: create "EG · Sunset · to suppress" as soon as the first people are tagged** (about 17 days after switch-on) and exclude it
   from campaigns and live flows. Until then E1's "we'll check once more, then stop" and E2's "last email" aren't true.
3. ~~**Re-entry settings**~~ Done 8 Oct (F3 7 days, F9 30 days, rescanned). (the API can't set them): F3 7 days, F9 30 days, in each flow's settings.

## Should fix (copy and logic)

4. ~~**F3 under-£300 emails and Free members.**~~ Done 8 Oct (rescanned). Free members go down this path, but E2lo's subject ("5% off this order, free"),
   headline and intro, and E1lo's preview, tell them to join Free. Only the panel switches.
5. ~~**F3 "Good to know": "Members get four free returns a year"**~~ Done 8 Oct (rescanned). reads as if Free members get them. Should say annual members.
6. **F9 10%-back reminder can reach someone who has joined since E1.** The day-10 check only looks at the order date. Add
   "MemberTier is not set" to that check.
7. **F9 uses the first item in the order** for the product photo, brand warranty/accessories and the review email's product name.
   A trolley order with a cover listed first would get the wrong or no brand content; an empty order gives "You've had the  for a
   little while". Add a fallback ("your new kit") and prefer the trolley/club item.
8. ~~**F3 E3 (Alex) product name has no fallback**~~ Done 8 Oct (rescanned). ("you were looking at the ." if the basket has no items).

Fixes 4–8 are in emails already attached to flows, which the API can't edit. Options: make them by hand in the Klaviyo editor, or
I fix the builders and create v2 drafts of F3 and F9 (old drafts then deleted by you).

## Decisions / minor

- F9 PowaKaddy line says "5-year battery warranty scheme"; PowaKaddy's own wording is a "5-year pro-rata" scheme. Add "pro-rata"?
- F9 reminder subject "Your 10% back offer ends soon": the 14-day window is real and stated. OK as is, or reword?
- Trust bar says "Free delivery over £50" in every email, including those to members (who get £10).
- Trustpilot "4.8 out of 5 from 611 reviews" is typed into the emails; it will drift. Update it occasionally.
- F2 Free E1 has no tier check (someone upgrading within seconds of joining would get both welcomes). Low risk; leave.
- F12 E3: "change your preferences here" — "here" is redundant.
- Klaviyo copied shared emails per branch (e.g. 8 copies of the monthly reminder, 23 templates in F9): an editor change must be
  made in every copy.
- No hand-written plain-text versions; Klaviyo generates them when sending. Check in test sends.

## Not checked

SMS rendering (no render tool); live event fields (would mean reading customer data); real inbox rendering (Gmail / Outlook /
Apple Mail): all covered by test sends next.

# Build log

## 29 Sep 2026 · EG · F3 Checkout abandonment · Trolleys (draft)

- Flow **UXsJ3d**, status **draft**: https://www.klaviyo.com/flow/UXsJ3d/edit (created via Windsor `create_flow`, account SiyYRR).
- Master templates (design B, "What we have now" images, trade-in panel left out, membership image left out pending rights):
  E1 `Sc4LsT` · E2 `VC22MY` · E2m `W3wixR` · E3 `VjRZzQ`. Klaviyo copied them into the flow's own messages
  (E1 RUYKhu, E2m WFfmci, E2 W4eizF, E3 SnKhdj / X8ZT89), so edits to the masters don't flow through.
- Render-tested E1 in Klaviyo: Motocaddy basket shows warranty row + warranty preheader; PowaKaddy basket hides both; YouTube link urlencodes.
- First create attempt rejected: `existence/exists` on MemberTier. Accepted: `{"type":"existence","operator":"is-set"}`.
- Trigger: Checkout Started, 18 trolley collections (batteries/chargers excluded), $value ≥ 30. Flow filter: no order since start, no bounce 30d.

### To set in the Klaviyo editor (Windsor can't)
1. Timing: E2 delay "1 day, then 09:30"; SMS "1 day, then 18:00"; E3 "1 day, then 09:30" (both branches).
2. Re-entry: 7 days (not set by the API).
3. Message names: Email #1 → F3 Trolleys E1 – Basket saved; #2 → E2m – Member; #3 → E2 – How to be sure it's the right one; #4/#5 → E3 – Want a second opinion?; Text #1/#2 → F3 SMS 1 – Day 2.
4. Preview text: blank on every message (the templates carry a hidden preheader, but fill the field to be safe).
5. UTM tracking: off on every message; the pack says on for marketing.
6. SMS: "Add company name" is on AND the body starts "Evolution Golf:" → remove one. "Add opt-out language" is **off** → switch on.
7. Pack step "update profile in_abandon_flow" is not in the flow (Windsor can't add it); optional belt-and-braces only.

### Clean-up for Layton (I don't delete)
- Old test templates from the first attempt: THeprK, WqkQJ7, WS7nDW, Sf6hhp.

## 30 Sep 2026: tag check for the fixes feature
- Created test template `S7gn6z` "EG · TEST tag check (delete me)" (not used by any flow) to confirm tags render:
  `{% unsubscribe_link %}` and `{% manage_preferences_link %}` work as link addresses; `{% unsubscribe_url %}` does not.
  **Layton: please delete S7gn6z** along with the older test templates.
- 30 Sep: Klaviyo PATCH /templates on a flow-message template returns 404 "does not exist" (tested with a no-op name change on
  our own draft F3 template RUYKhu; also XhSB6r from the live checkout flow via the app). Reads work. Nothing was changed.
  The Fixes page now groups findings per flow as Klaviyo-editor to-dos and verifies them on rescan.

## 1 Oct 2026 · EG · F1 Welcome (draft, two groups)
- Flow **TQe2j4**, status **draft**: https://www.klaviyo.com/flow/TQe2j4/edit (Windsor `create_flow`, account SiyYRR). Definition: `klaviyo/flows/f1-welcome.json`.
- Trigger: added to list "1.0 Main Mailing List" (`Tzck9t`, double opt-in). Flow filters: no order ever, no order since start,
  no bounce in 30 days, **no checkout started since start** (see deviations).
- Steps: split "MemberTier is set" → members leave (they belong in F2) · E1 Welcome (membership) · 1 hour · SMS 1 · 1 day ·
  split "Viewed Product in last 7 days in a trolley/club/used-club category" → E2 Hardware / E2 Everything else ·
  2 days · E3 from Alex · 3 days · E4 Two ways to pay less.
- Master templates (design B, new icons, no heroes yet): E1 `WN9f7w` · E2 Hardware `S6QTqu` · E2 Everything else `VbNCj7` ·
  E3 `RbNzzb` · E4 `W9VWmE`. Klaviyo copied them into the flow (SvyEJq, U8J3y7, UF7PPk, Sb3DkQ/TksueG, TfPdTi/VACTF2).
  Klaviyo stripped the Google Fonts link on save, so emails use Georgia/Arial (Gmail ignores web fonts anyway).
- Icons: 14 PNGs from the Astra library imported into the Klaviyo image library as "EG icon · …" (URLs in `klaviyo/design/f1/icons.json`).
- API findings: `{"type":"existence","operator":"is-not-set"}` is rejected (so members are split out as the first step);
  event-property filters on a list field need `{"type":"string","operator":"contains"}` — `"type":"list"` is rejected.
  Viewed Product's collection field is `Categories` (not `Collections`).

### Deviations from the pack (tell Layton)
1. Two E2 versions (Hardware / Everything else) instead of four (Layton, 1 Oct).
2. E1 is the new membership email, not the current 5% one. The current E1 (VBjCqp) still advertises the old Clubhouse offer
   (15% off, £19.99/month); public codes are also outside the guardrails. Layton can swap it back in the editor.
3. Pack "abandonment check → wait 2 days" replaced by "started checkout → leave the flow": Klaviyo branches can't rejoin,
   so a wait-and-continue at three points would need 16 copies of the tail.
4. No click-to-choose interest links (unverified link actions); E2 routes on browsing instead. No `welcome_complete` update step (Windsor can't).
5. Trade-in panel uses https://evolutiongolf.co.uk/pages/trade-in (found on the site); fitting and used-club links also from the site nav.

### To set in the Klaviyo editor
1. Timing: send E2 and E3 at 09:30 and E4 at 17:30 (add "then at" time to each wait, both branches).
2. Preview text: blank on all 7 emails; copy from `klaviyo/design/build_f1.py` EMAILS.
3. Message names: Email #1 E1 Welcome; #2 E2 Hardware; #3 E2 Everything else; #4/#5 E3 Ask us anything; #6/#7 E4 Two ways to pay less; Text #1 SMS 1 Welcome.
4. SMS: "Add company name" is on and the body starts "Evolution Golf:" → remove one; switch "Add opt-out language" on.
5. UTM tracking off on every message → switch on.
6. CONFIRM tokens: phone number (E3), wording for how used clubs are checked (E2 Hardware).
7. Re-entry: leave off (pack).
8. Category names in the Hardware split: check irons appear under "Golf Clubs" (no separate irons collection was confirmed).

## 1 Oct 2026 · Drafts page, F1 v2, F2 (two drafts)
- Layton approved (1 Oct) the dashboard creating new drafts after approval on its new **Drafts** page ("New flows to approve").
  Packs: `dashboard/app/drafts/{f1-welcome-v2,f2-free,f2-annual}.json`, built by `klaviyo/build_packs.py` from the email builders.
- Layton's answers: £36 members are tagged `MemberTier = AnnualMember`; returns start from a request form in the member portal;
  the prize draw is automatic and drawn at the start of each month for the month before. The £19.95 basket pop-up is in the site
  code but not visible (no action).
- **F1 v2** (pack `f1-welcome-v2`): fixes "Welcome, there.", "Free delivery over £50" (site banner), phone 0330 122 7089 (site header);
  adds preview text, message names, send times (09:30 / 17:30), UTM tracking, SMS opt-out wording on and company-name prefix off.
  Once created, Layton deletes the first draft **TQe2j4**.
- **F2** deviates from the pack's four tiers: the members page now sells Free (£0) and an Annual plan (£36/year).
  `EG · F2 Membership · Free` starts from the existing segment W3N8WF ("Free TIer Members", MemberTier contains "Free");
  3 emails, upgrade checks before E2/E3. `EG · F2 Membership · Annual` starts from a new segment "EG · Members · Annual"
  (MemberTier equals "AnnualMember"); 5 emails to day 335 (renewal reminder). Old Club/Pro/Annual tiers get nothing new.
- Untested against Klaviyo until the first approval: flow-create revision, segment triggers, and the extra settings.
  The app drops any optional setting Klaviyo refuses and lists it for the editor.
- 1 Oct: new look (Layton): website font Noto Sans Display, green accents, pale-green panels (no Fraunces/cream). F1 v3 pack added; F1 v2 (STnrqk, created 14:55, all settings accepted incl. send times) is frozen — delete it and TQe2j4 once v3 is created.
- 1 Oct: header now all-white logo (Klaviyo image 378081689), centred, 190px. Applied to F1 v3 and F2 packs (none created yet).
- 1 Oct: flow map published (now dashboard/app/flowmap.html, also the dashboard "Flow map" page → https://claude.ai/artifact/ET69bS6qbZM829pvLQXtcp). Checks: Added to Cart uniques Jun 441/Jul 565/Aug 185/Sep 136 vs Checkout Started 994/860/781 → cart tracking likely broken since Aug (F4/F5 held); Delivered Shipment ~47–59% of Placed Order, Fulfilled Order ~100% → F9 uses Fulfilled Order + 3d; back-in-stock sign-ups 0 Jul–Sep. F1 v3: added member split before E4.
- 1 Oct: F2 Annual (Layton): day-60 email widened to "Two months in"; monthly 10% reminder every 30 days, days 90–300 (8 sends, one template), renewal at day 335. Pack now 6 emails, 25 steps. Flow map added to the dashboard (/flow-map, sidebar "Flow map").
- 6 Oct: F1 copy review doc for Layton's feedback: https://claude.ai/code/artifact/e33d175e-e878-45b2-b205-ac7568626575 (Claude Docs, project e33d175e…, body node 4f86bbbd-35d9). Copy first, design after. Apply feedback in build_f1.py, rebuild F1 pack (v3 not yet created; if created, bump to v4).
- 6 Oct: F1 copy feedback (doc comments): E2 Hardware trade-in section → Klarna 'Spread the cost' (pay in 3, /pages/klarna); E1 membership headline leads with monthly 10%; E1 benefits: trade-in → monthly prize draw + 10% off member portal deals; E4 Way 1 leads with monthly 10%, Way 2 → member-only deals + monthly prize draw (no trade-in). Open: E2 Hardware member note still mentions trade-in bonus (asked).
- 6 Oct: E2 Hardware member note: trade-in → monthly 10% + member deals + prize draw. F1 now has no trade-in mentions.
- 6 Oct: photo briefs for F1 (W1 team/shop, W2 trolley on course, W3 shoes/weather, A1 Alex) with sizes (heroes 1200×720 shown at 600×360; Alex 240×240 shown as 76px circle). Dashboard draft pages: 'Photos needed' panel + 'Show photo spots' toggle on previews (pack photos_file per email).
- 6 Oct: F2 copy: trade-in de-emphasised per Layton's F1 steer (benefit lists → member deals; Free E3, Annual E1/E3 rows; day-60 'Two months in' now leads with monthly 10%, prize draw, member deals; trade-in one line). F2 photo spots: Free E1 reuses W1 (team), Annual E1 new M1 (member out playing).
- 6 Oct: copy docs — F2: https://claude.ai/code/artifact/08bb8a0b-ffe3-4ad5-ae11-3a48eea02700 (body eb396842-828f); F3 (new 2-group draft, not built yet): https://claude.ai/code/artifact/e9605082-60e3-48ae-83e0-4b7011c79bf3 (body bc3c220f-b02f). F3 photos: none new; product main photos must be badge-free (M1 DHC 'FREE GIFT'); A1 reused.
- 7 Oct: portal wording corrected (Layton): portal = instant daily deals + exclusive member deals; the 10% is site-wide, one order a month. Updated build_f1/build_f2, packs rebuilt (F1 v3, F2 Free, F2 Annual still not created), and the F1/F2/F3 copy docs. F2 Free 5% wording left as is pending Layton's answer (site-wide or portal only?).

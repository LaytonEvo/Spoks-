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

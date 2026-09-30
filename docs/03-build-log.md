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

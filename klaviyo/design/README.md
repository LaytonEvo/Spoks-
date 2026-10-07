# Evolution Golf email design system: editorial

Chosen 7 Oct 2026 (Layton): reference mockup `evolution-golf-welcome-mockup.html`, rules from
`docs/source/evolution-golf-email-design-prompt.md`. Replaces design B "On the course" and the 1 Oct Noto Sans / pale-green look.
Shared code: `build_f3_b.py` (tokens, shell, header, button, intro, trust line, rating, footer) and `build_f1.py`
(benefits table, feature section, secondary panel, topic rows). F2 reuses both.

Premium, modern, friendly independent golf retailer. Editorial and restrained: serif headlines, white space,
thin rules instead of boxes, brand green as an accent and for the header and footer.

## Tokens
| | |
|---|---|
| Brand green `#0F3B2A` | header, footer, primary button, 3px section rule, links |
| Secondary green `#24563F` | eyebrow labels |
| Ink `#161816` | headlines, bold labels |
| Body `#2E322F` | paragraphs |
| Muted `#626862` | secondary text, fine print, benefit descriptions |
| Hairline `#DDE1DD` | dividers, table rules |
| Stone `#F1F3F1` | the only tint: at most one small secondary panel per email |
| Paper `#FFFFFF` | canvas (always white; product cut-outs flattened onto white) |
| Trustpilot `#00B67A` | stars only |

No cream, beige, warm off-white, mint, brass or gold.

## Type
- Headlines: Fraunces 400 (Georgia fallback). H1 38/42 (32 on mobile), H3 28/34. Sentence case, never bold.
- Body: Inter 400/500/600 (Arial fallback). Body 16px / 1.65, benefit rows 14.5px, fine print 12.5px.
- Eyebrows: Inter 600 11px, uppercase, 0.14em, secondary green.
- Fonts load with `@import` (Klaviyo strips `<link>`); Gmail and Outlook use the fallbacks.

## Layout
600px wide, 48px side padding (24px mobile), 28–44px between sections. Radius 0–2px. No shadows, no gradients.

## Components, in order
1. Header: green bar, white logo centred, 22px padding.
2. Hero photo: full bleed 600 × 360 (supply 1200 × 720), no text on it. Slot placeholders (W1, W2, M1, A1…) until supplied.
3. Intro: eyebrow, serif H1, one or two short paragraphs.
4. Feature section: 3px green top rule, eyebrow, serif H3, muted lede, benefits table.
5. Benefits table: bold ink label (44%) | muted description, 1px hairlines incl. above the first row. No icons, numbers,
   bullets or ticks. Stacks on mobile.
6. Primary button: green, white Inter 500 15px, 15 × 30 padding, 2px radius, specific action copy. One per email;
   anything else is a text link.
7. Fine print: muted 12.5px under the button.
8. Secondary panel (optional, max one): stone strip, short line left, bold green link right.
9. Trust line: Free delivery over £50 | Advice from golfers | Custom fitting, between hairlines. No icons, no tint.
10. Rating: five green stars, "4.8 out of 5 on Trustpilot from 611 reviews" from `TRUSTPILOT` in `build_f3_b.py`.
11. Footer: green, logo centred, address, socials, compliance text and unsubscribe / manage preferences at 72% white.

Numbered steps (1, 2, 3 in serif green, hairline rows) are kept for instructions; they are not benefit lists.

## Annual member card
`member_card()` / `feature(card=True)` in build_f1.py: Layton's annual card artwork, flattened onto white, shown at
320px centred. Only where the £36 annual plan is welcomed or sold (F1 E1/E4, F2 Free E2/E3, Annual E1/E5, F3 non-member E2);
never in the Free welcome. Gold on the card is fine: it's the brand asset, not the email's own palette.

## Members' edition
Every email that goes only to members (all of F2; later the member versions in other flows): header logo | MEMBERS
(small spaced capitals after a thin rule), eyebrows start "Members ·", footer reads "You're receiving this as an Evolution
Golf member." with a "Manage my membership" link. `shell(..., members=True)`.

## Icons
Phosphor Light only (from @phosphor-icons/core), rendered as 48px transparent PNGs in brand green, hosted in Klaviyo,
shown at 24px. One three-item row per email at most, above the footer (F2: 10% off one order a month · Instant daily
deals · Monthly prize draw, in the emails without a photo). Otherwise never next to benefits, copy, headlines or buttons, with one exception (Layton, 7 Oct 2026): section rows
that each cover one member benefit may carry a matching icon beside the heading (F2 Annual E3, E4, Free E3; icons:
seal-percent 10%, trophy prize draw, tag deals, arrow-u-up-left returns, clock early access), and then the email has
no bottom icon row. No inline SVG.

## Build
Tables and inline CSS; media queries are progressive enhancement. Explicit `bgcolor` on cells for dark mode.
Personalisation: first name, or nothing when it's missing. UK English.

## Delivery wording
Members: "Free delivery over £10" ("Normally £50 for non-members"). Trust line: "Free delivery over £50".
Free tier: "over £30" (members page; not yet re-confirmed).

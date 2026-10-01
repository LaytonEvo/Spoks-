EVOLUTION GOLF — FINAL NON-HERO EMAIL ASSET HANDOFF
Packaging date: 1 October 2026.

SCOPE AND SOURCE OF TRUTH
This handoff packages existing artwork only. No artwork has been generated, redrawn, recoloured or resized during packaging. Copied assets are byte-identical to their source files; source-name-map.csv records the original paths, handoff names and SHA-256 hashes.
The v1.1 audited icon geometry supersedes the original sample geometry. Use specs/eg-ui-icon-library-spec.svg or .png for the final 24px/48px review. The original master review and older category sheets contain pre-audit samples and are excluded. Their construction rules are retained below and in eg-icon-style-tokens.json.
The 67 audit-sheet entries represent 63 distinct symbols. The repeated member-card entry has one named pair in the handoff. Three differently named aliases are retained: delivery-van/free-delivery, shield-warranty/warranty and golf-trolley/push-trolley. There are 66 base names, each in dark green and white: 132 SVGs plus 132 existing transparent 96px PNGs. Two existing 40px panel SVGs bring the icon SVG total to 134. Larger master SVG size copies are represented by their identical scalable 24px SVGs. No white version of the gold-detail panel icon was created; use the ordinary white member-card icon where required.
Buttons, badges and USP are finished specifications for construction with live text; no standalone flattened component image is intended as a substitute. Blank product and panel PNGs are layout references. Header/footer PNGs contain the explicitly requested placeholder labels. Supply the official logo/social icons, real product photos, final copy and live links during implementation.
All hero images and hero drafts are excluded by request. No separate banner, spot or empty-state illustration files were made; banners/ and illustrations/ are intentionally empty. The three neutral fallback tiles are included under fallbacks/.
Manifest colours are intended design colours, not the intermediate antialiasing shades in raster edges. PNG sizes are exported pixel dimensions; intended display dimensions appear in the descriptions and component specs. Transparent backgrounds are not a colour.

BRAND RULES
Email width: 600px. Email canvas: pure white #FFFFFF.
Dark green #003D27: headers, footers, dark panels and primary icons on light surfaces.
Green #006747: buttons and links.
Gold #B2893F: small accents only, thin rules, numerals, small eyebrow labels or one small icon detail.
Cream #FAF7F1: only a small contained panel fill; never behind a product or photo.
Yellow #F1DA01: at most one small element per email; never a large area.
Neutral text #1F2A24; muted text #5E6B63; hairlines #E4E0D6.
Headings: Fraunces, Georgia, serif. Body and UI: Inter, Arial, sans-serif.
Premium, calm, clean and modern; generous white space. Flat UI, no gradients, drop shadows, 3D or texture.
Keep text live in Klaviyo except explicitly requested image labels or numeral artwork. Keep product/cut-out areas pure white. Do not draw real branded products, the Evolution Golf logo or social logos. Do not invent reviews, ratings, awards, prices, percentages, delivery times or countdowns. No urgency devices.
Text contrast target: at least 4.5:1. Icons readable at 24px. Meaning never communicated by colour alone.

ICON CONSTRUCTION
Native grid/viewBox: 24 x 24 / 0 0 24 24.
Minimum clear padding: 2 units, including the visible outer stroke. Maximum visible bounds: x2..22, y2..22.
Stroke: 1.75 units. Line caps: round. Line joins: round. Rectangle path corner radius: 2 units.
No fills except a future optional small gold #B2893F dot/detail; maximum one gold detail per icon. Natural contours, roof corners and non-rectangular forms use round joins rather than an imposed rectangle radius.
Geometric, simple and optically balanced. Literal dark-green #003D27 and white #FFFFFF variants on transparency. All ordinary icons are monochrome; only the existing member-card panel variant has one gold mark.
Keyline dimensions are visible outer bounds including stroke: circle 20 x 20, square 18 x 18, portrait 14 x 20, landscape 20 x 14.
Uniform scale: display 24px -> stroke 1.75px; 40px -> 2.9167px; 48px -> 3.5px; 96px -> 7px.
The 96 x 96 transparent PNGs are existing 4x exports for 24 x 24 email display. SVGs are scalable dashboard/library masters. Use the platform-supported image delivery format for email.
Use an empty image alt or aria-hidden for icons repeating adjacent live labels. Give standalone controls meaningful accessible names. No visible text is baked into icon artwork.
The original audit change log is included without revision. No additional icon design changes were made during this handoff.

BUTTONS AND TEXT LINKS
Spec sheet: specs/eg-ui-buttons-spec.png and .svg, 600 x 1376px.
White email canvas, maximum 600px. Placeholder: Button label. Rest-state examples only.
Primary: #006747 fill; #FFFFFF label. Secondary: #FFFFFF fill; #006747 label and 1.5px border.
Outer height 48px; outer radius 6px. Inter SemiBold 600, 16px/24px; Arial fallback; letter-spacing 0.
Side padding 24px; primary vertical padding 12px; bordered secondary vertical padding 10.5px. Border-box sizing. Intrinsic width equals label width + 48px side padding + any borders (3px total for secondary).
Inverse on #003D27: white button and dark-green label. Inverse secondary border white. No shadow or gradient.
Text link: green #006747, 16px/24px Inter 600; underline 1px solid with 3px offset. Label only underlined. Arrow-right: 24 x 24px; 8px gap; 1.75px round stroke; path M4 12h16m-7-7 7 7-7 7. Inverse link and arrow white.
Exact CSS supplied in the chat follows unchanged and is also in specs/eg-ui-buttons.css:

/* Evolution Golf — email button specification v1
   Canvas: 600px maximum width; #FFFFFF.
   All labels remain live text. Placeholder: Button label.
   Inter SemiBold is weight 600; Arial is the email fallback.
   Width is intrinsic: text width + 48px padding + any borders.
   The 48px height INCLUDES borders and padding.
   These are rest-state design values; inline declarations for email use.
*/

.eg-email-canvas {
  width: 100%;
  max-width: 600px;
  background-color: #FFFFFF;
}

.eg-button {
  display: inline-block;
  box-sizing: border-box;
  height: 48px;
  padding: 12px 24px;
  border: 0;
  border-radius: 6px;
  font-family: "Inter", Arial, sans-serif;
  font-size: 16px;
  font-weight: 600;
  line-height: 24px;
  letter-spacing: 0;
  text-align: center;
  text-decoration: none;
  white-space: nowrap;
  vertical-align: middle;
  -webkit-text-size-adjust: 100%;
  mso-line-height-rule: exactly;
}

.eg-button--primary {
  background-color: #006747;
  color: #FFFFFF;
}

.eg-button--secondary {
  background-color: #FFFFFF;
  color: #006747;
  border: 1.5px solid #006747;
  padding: 10.5px 24px;
}

.eg-dark-panel {
  background-color: #003D27;
}

/* Add this modifier to either button on the dark panel. */
.eg-button--inverse {
  background-color: #FFFFFF;
  color: #003D27;
}

.eg-button--secondary.eg-button--inverse {
  border-color: #FFFFFF;
}

/* Markup: <a class="eg-link"><span class="eg-link__label">Button label</span><svg class="eg-link__icon" ...></svg></a>
   Keep the closing span and opening icon adjacent: the 8px margin supplies the gap.
   Email: the icon may instead be an <img width="24" height="24" alt="">.
   Dashboard SVG: viewBox="0 0 24 24", fill="none", stroke="currentColor",
   stroke-width="1.75", stroke-linecap="round", stroke-linejoin="round".
   Audited library path: M4 12h16m-7-7 7 7-7 7
   Only the label is underlined; the decorative arrow is not.
*/
.eg-link {
  display: inline-block;
  font-family: "Inter", Arial, sans-serif;
  font-size: 16px;
  font-weight: 600;
  line-height: 24px;
  letter-spacing: 0;
  color: #006747;
  text-decoration: none;
  white-space: nowrap;
  vertical-align: middle;
  -webkit-text-size-adjust: 100%;
}

.eg-link__label {
  text-decoration-line: underline;
  text-decoration-style: solid;
  text-decoration-color: currentColor;
  text-decoration-thickness: 1px;
  text-underline-offset: 3px;
}

.eg-link__icon {
  display: inline-block;
  width: 24px;
  height: 24px;
  margin-left: 8px;
  border: 0;
  vertical-align: middle;
}

.eg-link--inverse {
  color: #FFFFFF;
}

HEADER
Dark PNG: components/eg-header.png. White PNG: components/eg-header-white.png.
Both exports: 1200 x 144px, displayed at 600 x 72px.
Square outer corners. Dark background #003D27; white version background #FFFFFF.
Logo placeholder outer box 200 x 40px, centred at x200 y16; 1px outline, no fill. LOGO label centred, Inter SemiBold 600 at 12px. No actual logo drawn.
Dark version placeholder outline/text #FFFFFF; white version outline/text #003D27.
Centred rule 80 x 1px at x260 y59. Its bottom is y60, leaving 12px clear to the bar bottom at y72.
Dark version rule #B2893F; white version rule #003D27.
At 2x all pixel coordinates and stroke widths double. Replace placeholder with the official logo when building the email.


BADGES — EXISTING SPECIFICATION
Original source: eg-email-badges-specs.txt
Filename references below are the original names; source-name-map.csv maps them to handoff names.

EVOLUTION GOLF — EMAIL LABEL BADGES / V1

SHEET
600 × 1136px; white #FFFFFF canvas; samples displayed at 1:1.
SVG and PNG are reference sheets. Use live labels in production emails.

SHARED SPECIFICATION
Outer height: 24px, including any border.
Pill radius: 12px.
Horizontal padding: 10px each side, inside any border.
Width: automatic, driven by the label, icon and border.
Font: Inter SemiBold, weight 600; fallback Arial, sans-serif.
Font size: 12px.
Line height: 16px, vertically centred.
Text transform: uppercase.
Letter spacing: 0.06em (0.72px at 12px).
No shadow, gradient or texture.
Label-only badges: 4px vertical space around the 16px line box.
New in: 3px vertical space plus 1px border on each edge.
Member-card icon: native 24 × 24px canvas; vertically centred.
The icon has its own clear space, so the visible card fits within the pill.
Icon-to-label gap: 6px, measured from the icon canvas edge.
Icon: approved eg-icon-member-card-white.svg; unchanged geometry.
Icon stroke: #FFFFFF, 1.75px, round caps and joins; no fill.

VARIANTS
MEMBERS
  Fill #003D27; label and icon #FFFFFF; no border.
  Use for member-only content and benefits.
NEW IN
  Fill #FFFFFF; label #003D27; 1px solid #003D27 border.
  Use for new product arrivals.
PRE-OWNED
  Fill #FAF7F1; label #003D27; no border.
  Use for used or pre-owned product listings.
FEATURED
  Fill #F1DA01; label #003D27; no border.
  Use for one editorial highlight. Maximum one yellow badge per email.

PLACEMENT
Place above product or section titles on the white email canvas.
Keep cream inside the Pre-owned pill and badges separate from product photos.
Keep badge labels as live text in Klaviyo. They are labels, not buttons.

SHEET PALETTE
#003D27, #006747, #FFFFFF, #FAF7F1, #F1DA01,
#1F2A24, #5E6B63, #E4E0D6.

TEXT CONTRAST (foreground vs fill)
MEMBERS: 12.38:1
NEW IN: 12.38:1
PRE-OWNED: 11.57:1
FEATURED: 8.70:1


USP STRIP — EXISTING SPECIFICATION
Original source: eg-usp-strip-layout-specs.txt
Filename references below are the original names; source-name-map.csv maps them to handoff names.

EVOLUTION GOLF — THREE-ITEM USP STRIP / V1

DISPLAY SIZE
Panel: 600 × 92px on a pure white #FFFFFF email canvas.
Reference sheet: 600 × 1016px; the panel is shown at 1:1.
The sheet is a reference only. Build all labels as live email text.

PANEL
Background: #FAF7F1.
Border radius: 8px.
Padding: 20px on all four sides.
Box sizing: border-box.
Border: none.
Inner area: 560 × 52px.
No shadows, gradients, photos or product cut-outs in this panel.

COLUMNS AND DIVIDERS
Column widths: 186px, 186px, 186px.
Divider widths: 1px, 1px.
Sequence: 186 + 1 + 186 + 1 + 186 = 560px.
Dividers: #E4E0D6; height 52px; no additional horizontal spacing.
Column centres (relative to the panel): x=113px, 300px, 487px.

ELEMENT COORDINATES, RELATIVE TO THE PANEL'S TOP-LEFT
Left padding: x=0..20px.
Column 1: x=20px, width=186px.
Divider 1: x=206px, y=20px, width=1px, height=52px.
Column 2: x=207px, width=186px.
Divider 2: x=393px, y=20px, width=1px, height=52px.
Column 3: x=394px, width=186px.
Right padding: x=580..600px.
Icon boxes: (101,20), (288,20), (475,20); each 24 × 24px.
Icon-to-label gap: y=44..52px (8px).
Label boxes: (20,52), (207,52), (394,52); each 186 × 20px.
Bottom padding: y=72..92px (20px).

ICON ORDER / FILES
1. Free delivery — eg-icon-free-delivery.svg
2. Warranty / shield — eg-icon-warranty.svg
3. Members save / member card — eg-icon-member-card.svg
All three are byte-identical copies of the approved library SVGs.
Each file: 24 × 24px; viewBox 0 0 24 24; transparent background.
Stroke: #003D27; 1.75px; round caps and joins; no fill.
Rectangles retain the library's 2px corner radius.

LIVE TEXT
Placeholder: Label one (used in all three columns).
Font family: Inter, Arial, sans-serif.
Font weight: 600 / SemiBold.
Font size: 14px.
Line height: 20px.
Letter spacing: 0.
Text transform: none.
Text alignment: centre.
Colour: #003D27.
Margin and paragraph spacing: 0.
Keep the final label short enough for one line at the reviewed 600px size.
If a label wraps, increase the row/panel height to preserve the 20px padding.

EMAIL CONSTRUCTION
Use a presentation table, width 600px, cellspacing=0, cellpadding=0.
Apply cream fill, 8px radius and 20px padding to its containing cell.
Inside, use a 560px presentation table with five cells:
186px content / 1px divider / 186px content / 1px divider / 186px content.
Content cells: centred; icon row 24px, spacer row 8px, live label row 20px.
Divider cells: #E4E0D6; 1px wide; match the full content row height.
Retain native SVGs for the asset library; use the email platform's supported
image delivery format when placing icons in the email.

COLOURS
Component: #FAF7F1, #003D27, #E4E0D6.
Canvas: #FFFFFF.
Sheet annotations additionally: #006747, #1F2A24, #5E6B63.


PRODUCT CARDS — EXISTING SPECIFICATION
Original source: eg-product-cards-specs.txt
Filename references below are the original names; source-name-map.csv maps them to handoff names.

EVOLUTION GOLF — EMAIL PRODUCT CARDS / V1

FILES AND DISPLAY SIZES
Review sheet: eg-product-cards-spec.png, 600 × 2176px.
1-up blank: eg-product-card-1up-blank-2x.png, 1120 × 1488px.
  Display at 560 × 744px.
Single 270px blank: eg-product-card-270-blank-2x.png, 540 × 908px.
  Display at 270 × 454px; repeat with a 20px gap for a 2-up row.
2-up blank: eg-product-card-2up-blank-2x.png, 1120 × 908px.
  Display at 560 × 454px: two 270 × 454px cards, 20px gap.
The blank frames include the card border and empty secondary-button outline.
Photo areas and all live-text positions are empty; the review sheet is labelled.

600PX EMAIL LAYOUT
Outer email canvas: #FFFFFF, 600px wide.
Content width: 560px, with 20px left and right margins.
1-up: one 560px card.
2-up: 270px card + 20px gutter + 270px card.
Card widths include their borders; box-sizing: border-box.

CARD
Background: #FFFFFF.
Border: 1px solid #E4E0D6.
Outer corner radius: 8px.
No shadow, gradient or texture.
Body padding: 20px on all sides, inside the border.
Alignment: left.

PHOTO AREA
1-up inner image: 558 × 558px, at x=1px, y=1px in the card.
2-up inner image: 268 × 268px, at x=1px, y=1px in each card.
Background: #FFFFFF only.
Keep the whole product visible, using contain sizing on the square white area.
If top clipping is required, use 7px inner top radii inside the 8px card radius.
Do not invent or draw product artwork.
Review-sheet placeholder: real product photo goes here.

LIVE TITLE
Placeholder: Product title placeholder.
Font: Fraunces, Georgia, serif; weight 500 / Medium.
Size: 18px; line-height: 24px; letter-spacing: 0.
Colour: #003D27.
Title slot: 48px high, allowing two lines and aligned pricing in the 2-up row.
Content width: 518px (1-up), 228px (2-up).

LIVE PRICE
Placeholder: Price placeholder.
Font: Inter, Arial, sans-serif; weight 400 / Regular.
Size: 16px; line-height: 24px; letter-spacing: 0.
Colour: #1F2A24.
No invented price, savings, percentage or crossed-out value.
Gap after the reserved title slot: 8px.

SECONDARY BUTTON — APPROVED BUTTON STYLE
Placeholder: Button label.
Fill: #FFFFFF; label: #006747.
Border: 1.5px solid #006747.
Outer height: 48px, including borders and padding.
Outer radius: 6px.
Font: Inter, Arial, sans-serif; weight 600 / SemiBold.
Size: 16px; line-height: 24px; letter-spacing: 0.
Text decoration: none; white-space: nowrap; text-align: center.
Padding: 10.5px vertically, 24px horizontally; box-sizing: border-box.
Width: automatic; label width + 48px padding + 3px border.
The displayed Button label placeholder is approximately 143.21px wide overall.
Gap from price line box to button: 16px.
Gap from button to the card's inner bottom edge: 20px.

COORDINATES, RELATIVE TO EACH CARD'S TOP-LEFT
1-up card: 560 × 744px.
  Image: x1 y1 w558 h558.
  Title slot: x21 y579 w518 h48.
  Price slot: x21 y635 w518 h24.
  Button: x21 y675, automatic width, h48.
2-up card: 270 × 454px.
  Image: x1 y1 w268 h268.
  Title slot: x21 y289 w228 h48.
  Price slot: x21 y345 w228 h24.
  Button: x21 y385, automatic width, h48.
2-up row: first card x0; second card x290.

EMAIL BUILD
Use presentation tables and separate image, title, price and button blocks.
Keep titles, prices and button labels live in Klaviyo.
The labelled sheet and blank PNG frames are layout references.
Use equal title slots in the 2-up row so prices and buttons line up.
If a real title needs more than two lines, increase both title slots together.
Allow the card height to grow if live copy requires more space.

COLOURS
Blank frames: #FFFFFF, #E4E0D6, #006747.
Specification sheet additionally: #003D27, #1F2A24, #5E6B63.


MEMBERSHIP PANEL — EXISTING SPECIFICATION
Original source: eg-membership-panel-specs.txt
Filename references below are the original names; source-name-map.csv maps them to handoff names.

EVOLUTION GOLF — MEMBERSHIP PANEL / V1

DELIVERABLES
Spec sheet: eg-membership-panel-spec.png, 600 × 1080px.
Blank panel: eg-membership-panel-blank-2x.png, 1120 × 280px.
  Display at 560 × 140px; includes the icon, with all text areas empty.
Icon: eg-icon-member-card-gold-40px.svg, 40 × 40px, transparent background.
  Native viewBox 0 0 24 24; approved member-card geometry.

PANEL
Width: 560px; example height: 140px.
Fill: #FAF7F1; outer radius: 8px; border: none.
Padding: 24px on all sides.
Email canvas: #FFFFFF, 600px wide; margins: 20px each side.
No gradient, shadow or product image.

HORIZONTAL LAYOUT
Inner width: 512px.
Icon column: 40px.
Icon-to-copy gap: 24px.
Copy column: 448px.
24 + 40 + 24 + 448 + 24 = 560px.
Icon origin: x24px, y50px, relative to panel top-left.
Copy origin: x88px, y24px.
Icon is vertically centred against the 92px copy block.

MEMBER-CARD ICON
Display size: 40 × 40px.
Outline: #003D27; no fill.
Native stroke: 1.75 units on a 24-unit grid, scaling to 2.9167px at 40px.
Caps and joins: round. Native rectangle corner radius: 2 units.
The short right-hand card mark alone uses #B2893F.
Gold geometry: M15.5 14.5h2; same stroke width and round caps.
One gold detail only. The source member-card shape is unchanged.

LIVE HEADING
Placeholder: Heading placeholder.
Font: Fraunces, Georgia, serif; weight 500 / Medium.
Size: 22px; line-height: 28px; letter-spacing: 0.
Colour: #003D27; alignment: left.
Line box: x88 y24 w448 h28.

LIVE BODY
Placeholder: One line of text placeholder.
Font: Inter, Arial, sans-serif; weight 400 / Regular.
Size: 14px; line-height: 20px; letter-spacing: 0.
Colour: #5E6B63; alignment: left.
Line box: x88 y60 w448 h20.
Gap from heading line box: 8px.
Keep copy to one line at the reviewed size; let the panel grow if real text wraps.

LIVE TEXT LINK
Placeholder: Link label.
Font: Inter, Arial, sans-serif; weight 600 / SemiBold.
Size: 16px; line-height: 24px; letter-spacing: 0.
Colour: #006747; underline: solid 1px; underline offset: 3px.
Line box starts at x88 y92; height: 24px.
Gap from body line box: 12px.
Use the approved arrow-right geometry: M4 12h16m-7-7 7 7-7 7.
Arrow: 24 × 24px; #006747; 1.75px stroke; round caps and joins; no fill.
Gap between label box and arrow box: 8px.
Underline the label only.

EMAIL CONSTRUCTION
Build as a 560px presentation table with a cream, rounded containing cell.
Apply 24px padding; use a 40px icon column, 24px spacer and 448px copy column.
Keep the icon vertically centred. Use 28px, 20px and 24px line boxes on the right,
separated by 8px and 12px gaps, with paragraph margins reset to zero.
Keep all heading, body and link text live in Klaviyo.
Blank PNG and spec sheet are composition references; the SVG is a separate asset.
Use the email platform's supported image delivery format for icon placement.

COLOURS
Blank panel: #FFFFFF, #FAF7F1, #003D27, #B2893F.
Icon: #003D27, #B2893F; transparent background.
Specification sheet additionally: #006747, #1F2A24, #5E6B63, #E4E0D6.


TRADE-IN PANEL — EXISTING SPECIFICATION
Original source: eg-trade-in-panel-specs.txt
Filename references below are the original names; source-name-map.csv maps them to handoff names.

EVOLUTION GOLF — TRADE-IN PANEL / V1

DELIVERABLES
Spec sheet: eg-trade-in-panel-spec.png, 600 × 1080px.
Blank panel: eg-trade-in-panel-blank-2x.png, 1120 × 328px.
  Display at 560 × 164px; includes icon and empty secondary-button outline.
Icon: eg-icon-trade-in-40px.svg, 40 × 40px, transparent background.
  Native viewBox 0 0 24 24; approved trade-in geometry unchanged.

PANEL
Width: 560px; example height: 164px.
Fill: #FAF7F1; outer radius: 8px; border: none.
Padding: 24px on all sides.
Email canvas: #FFFFFF, 600px wide; margins: 20px each side.
No shadow, gradient, product photo, trade-in value or price.
This panel uses the membership panel's width, padding, radius and typography.
Its height increases by 24px to fit the 48px secondary button.

HORIZONTAL LAYOUT
Inner width: 512px.
Icon column: 40px; icon-to-copy gap: 24px; copy column: 448px.
24 + 40 + 24 + 448 + 24 = 560px.
Icon origin: x24px, y62px, relative to panel top-left.
Copy origin: x88px, y24px.
Icon is vertically centred against the 116px copy-and-button block.

TRADE-IN ICON
Display size: 40 × 40px; native grid: 24 × 24 units.
Outline: #003D27; fill: none; background: transparent.
Stroke: 1.75 native units, scaling to 2.9167px at 40px.
Caps and joins: round.
Symbol: golf club with circular arrows; approved geometry retained.
No gold accents.

LIVE HEADING
Placeholder: Heading placeholder.
Font: Fraunces, Georgia, serif; weight 500 / Medium.
Size: 22px; line-height: 28px; letter-spacing: 0.
Colour: #003D27; alignment: left; margins: 0.
Line box: x88 y24 w448 h28.

LIVE BODY
Placeholder: One line of text placeholder.
Font: Inter, Arial, sans-serif; weight 400 / Regular.
Size: 14px; line-height: 20px; letter-spacing: 0.
Colour: #5E6B63; alignment: left; margins: 0.
Line box: x88 y60 w448 h20.
Gap from heading line box: 8px.

SECONDARY BUTTON
Placeholder: Button label.
Position: x88 y92, relative to the panel.
Height: 48px including border and padding; outer radius: 6px.
Fill: #FFFFFF; label and border: #006747.
Border: 1.5px solid #006747.
Font: Inter, Arial, sans-serif; weight 600 / SemiBold.
Size: 16px; line-height: 24px; letter-spacing: 0.
Text alignment: centre; text decoration: none; white-space: nowrap.
Padding: 10.5px vertically, 24px horizontally; box-sizing: border-box.
Width: automatic, following the live label.
Button label example: approximately 143.21px overall width.
Gap from body line box to button: 12px.
Bottom inset: 24px.

EMAIL BUILD
Use a 560px presentation table with a cream, rounded containing cell.
Apply 24px padding; use a 40px icon column, 24px spacer and 448px copy column.
Keep the icon vertically centred. Use 28px and 20px line boxes above the 48px
button, with 8px and 12px gaps and paragraph margins reset to zero.
Keep heading, body and button text live in Klaviyo.
If real copy wraps, let panel height grow while preserving padding and gaps.
Use the blank PNG and spec sheet as composition references; the icon is separate.
Use the email platform's supported image delivery format for icon placement.

COLOURS
Blank panel: #FFFFFF, #FAF7F1, #003D27, #006747.
Icon: #003D27 on transparent background.
Spec sheet additionally: #1F2A24, #5E6B63, #E4E0D6.


FOOTER — EXISTING SPECIFICATION
Original source: eg-email-footer-specs.txt
Filename references below are the original names; source-name-map.csv maps them to handoff names.

EVOLUTION GOLF — EMAIL FOOTER / V1

DELIVERABLES
Footer PNG: eg-email-footer-2x.png, 1200 × 480px.
  Display at 600 × 240px.
Spec sheet: eg-email-footer-spec.png, 600 × 1200px.
The PNG is a design reference with the requested placeholder text.
Use live text and clickable links when building the footer in Klaviyo.

FOOTER
Width: 600px; height: 240px.
Background: #003D27; outer corners: square.
Alignment: centred.
No shadows, gradients or textures.

LOGO PLACEHOLDER
Outer size: 160 × 32px.
Position: x220 y24 relative to footer top-left.
Outline: 1px solid #FFFFFF; no fill.
Label: LOGO; Inter SemiBold 600, 13px, white #FFFFFF, centred.
Replace the placeholder box and its label with the official logo.

SOCIAL PLACEHOLDERS
Four empty circles; outer diameter 32px each.
Outline: 1px solid #FFFFFF; no fill.
Horizontal gap: 16px.
Total row width: 176px, centred.
Circle bounding-box positions: x212, x260, x308, x356; all y80.
Circle centres: (228,96), (276,96), (324,96), (372,96).
SVG construction: radius 15.5px plus a centred 1px stroke.
Leave circles empty until official social icons are supplied.
No social logos have been drawn.

GOLD RULE
Size: 80 × 1px.
Position: x260 y136; centred horizontally.
Colour: #B2893F.
This is the footer's only gold element.

TEXT
Font family: Inter, Arial, sans-serif.
Font weight: 400 / Regular.
Font size: 13px; line-height: 20px; letter-spacing: 0.
Colour: #FFFFFF at full opacity; text contrast on #003D27 is 12.38:1.
Alignment: centre; paragraph margins: 0.
Line 1: Address placeholder.
  Line box: x24 y160 w552 h20.
Line 2: Unsubscribe · Manage preferences.
  Line box: x24 y188 w552 h20.
Underline Unsubscribe and Manage preferences separately:
  1px solid #FFFFFF; underline offset 3px.
Keep the middle dot and surrounding spaces un-underlined.
Use separate live links for unsubscribe and preference management,
with the configured Klaviyo destinations.

SPACING
Top inset: 24px.
Logo box ends at y56; social row starts at y80: 24px gap.
Social row ends at y112; rule starts at y136: 24px gap.
Rule ends at y137; address line box starts at y160: 23px gap.
Address line box ends at y180; second line starts at y188: 8px gap.
Second line ends at y208; footer ends at y240: 32px bottom inset.
If the real address wraps, increase footer height while preserving spacing.

AT 2X
Canvas: 1200 × 480px.
Logo placeholder: 320 × 64px at x440 y48.
Social circles: 64px diameter; 32px gaps; row starts x424 y160.
Gold rule: 160 × 2px at x520 y272.
Text: rasterised at 26px; intended display size remains 13px.

COLOURS
Footer PNG: #003D27, #FFFFFF, #B2893F.
Spec sheet additionally: #006747, #1F2A24, #5E6B63, #E4E0D6.


DIVIDERS AND STEP NUMERALS — EXISTING SPECIFICATION
Original source: eg-dividers-step-numerals-specs.txt
Filename references below are the original names; source-name-map.csv maps them to handoff names.

EVOLUTION GOLF — SECTION DIVIDERS AND STEP NUMERALS / V1

PACKAGE
svg/: 11 standalone SVGs.
png-2x/: 11 transparent PNGs at twice the intended display size.
The white review sheet is separate from the transparent assets.
See eg-dividers-step-numerals-manifest.csv for every filename, size, colour and use.

A — CENTRED GOLD RULE
Files: eg-divider-gold-centred.svg / .png.
SVG display canvas: 600 × 24px; PNG: 1200 × 48px.
Rule: 80 × 1px, #B2893F, centred horizontally and vertically.
Native coordinates: x260 y11.5 w80 h1.
Transparent margins are part of the asset; keep the full 600px display width.
Use for a restrained section break.

B — FULL-WIDTH HAIRLINE
Files: eg-divider-full-width.svg / .png.
SVG display canvas: 600 × 24px; PNG: 1200 × 48px.
Rule: 600 × 1px, #E4E0D6.
Native coordinates: x0 y11.5 w600 h1.
Use between full-width sections.

C — GOLF-FLAG DIVIDER
Files: eg-divider-golf-flag.svg / .png.
SVG display canvas: 600 × 40px; PNG: 1200 × 80px.
Approved library flag: 24 × 24px; position x288 y8.
Flag outline: #003D27, 1.75px, round caps and joins, no fill.
Hairline: #E4E0D6, 1px tall at y19.5.
Left segment: x0..276px; right segment: x324..600px.
Clear space: 12px between each line segment and the flag's 24px canvas.
The line stops around the glyph; there is no white knockout or background fill.
Use as a golf-specific section break.

D — GOLD STEP NUMERALS
Files: eg-step-1.svg / .png through eg-step-4.svg / .png.
SVG display canvas: 40 × 40px; PNG: 80 × 80px.
Type: Fraunces Medium, weight 500, 28px; numerals 1, 2, 3, 4.
Numeral colour: #B2893F.
Circle: 40px outer diameter; 1px #B2893F border; no fill.
SVG circle: centre (20,20), radius 19.5 plus a centred 1px stroke.
Numerals are individually optically centred within the circle.
SVG numerals are outlines so appearance does not depend on font availability.
Use beside step headings; retain meaningful step text in the email.

DARK-GREEN TEXT ALTERNATIVE
Files: eg-step-1-dark-green.svg / .png through eg-step-4-dark-green.svg / .png.
Same geometry and type; numeral #003D27, circle border #B2893F.
Gold #B2893F on white measures 3.21:1, below the specified 4.5:1 text target.
Dark-green numerals on white measure 12.38:1 and meet that target.
The requested all-gold set is included, alongside this text-contrast alternative.

DISPLAY AND SPACING
Use all assets on the #FFFFFF email canvas.
Display PNGs at half their exported dimensions.
The divider canvas sizes include transparent vertical breathing room.
Add any additional section margins with email layout spacing.
Suggested vertical gap from each divider canvas to neighbouring content: 16px.
Keep step circles at 40px display size; suggested circle-to-heading gap: 12px.
No gradients, shadows, textures, product imagery, invented claims or urgency.

COLOURS
Gold divider and gold steps: #B2893F.
Full-width divider: #E4E0D6.
Flag divider: #003D27 and #E4E0D6.
Dark-green step alternatives: #003D27 and #B2893F.
Review sheet additionally: #FFFFFF, #006747, #1F2A24, #5E6B63.

FALLBACK TILES
Files: fallbacks/eg-fallback-flag.png, eg-fallback-trolley.png, eg-fallback-club.png.
Each file is exactly 800 x 800px, opaque pure white #FFFFFF, one centred outline icon in #E4E0D6 and nothing else.
Existing approved flag, trolley and iron geometry was used, with the same relative stroke weight, round caps and joins. The native 24-unit icon was scaled uniformly by 16 (384px nominal canvas, 28px stroke); placement was centred on visible artwork bounds.
These low-contrast tiles are decorative placeholders, not information-bearing controls. Keep any meaningful status as separate accessible live text if the implementation needs it. No text is embedded in these files.

AGREED CHANGES AND EXCEPTIONS DURING THE CHAT
Hero/banner visual direction changed from flat illustration to photorealism after the illustrated options were rejected. Later feedback favoured authentic golf clubhouse/course settings and less artificial empty space. No flat-to-photo change applies to this icon/UI system.
Scene-specific hero requests allowed generic unbranded accessories/objects, hands or a golfer without a visible face, and a black bag in the unresolved cross-sell scene. These are not new UI palette colours or permission to draw branded product artwork.
All hero files are now explicitly excluded; stock-photo replacement is planned. No stock-photo selection or insertion was completed.
The requested gold step numerals were delivered with a pre-existing contrast note and dark-green-number alternatives. Gold #B2893F on white is 3.21:1 and misses the requested 4.5:1 text target. The all-gold numeral files are marked needs work for meaningful text use; the supplied dark-green numeral alternatives meet 12.38:1. No contrast exception was approved. Decorative gold rules/circles remain as specified.
The user explicitly requested the pale #E4E0D6 fallback icons on white, with no text. Their role is decorative; this did not change the text contrast rule.
No other global changes to colours, icon stroke, fonts, no-urgency rules or white product backgrounds were agreed.

STATUS FOR THE DEVELOPER
Finished: audited icon library and inverse versions; button CSS/specification; badge and USP specifications; header variants; footer reference/specification; blank product frames and member/trade-in panels; dividers and step alternatives; three fallback tiles; this inventory and handoff.
Needs attention: all-gold step numerals if used to convey meaningful text; use the existing dark-green alternatives. Production Klaviyo components, official branding assets, real product photos, final copy and links remain implementation work. No complete Klaviyo templates were requested or built.
Unfinished prior artwork: cross-sell/second-order hero proportions remained unresolved; no final 1200 x 600 / 1200 x 900 export pair was completed for that scene. It is excluded along with every other hero.
Not made: separate eg-banner-*, eg-spot-* or eg-empty-* assets; those were not separately commissioned in the visible design sequence. No additional icon, component or fallback request is outstanding. The master visual sheet's pre-audit samples are superseded, so only its unchanged construction tokens/rules are retained here.
No new design or raster/vector conversion was performed to assemble this package.

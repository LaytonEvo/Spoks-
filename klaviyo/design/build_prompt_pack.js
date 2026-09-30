const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, LevelFormat, BorderStyle, PageBreak, Footer, PageNumber, TableOfContents } = require("docx");

const GREEN = "006747", DEEP = "003D27", GOLD = "B2893F", INK = "1F2A24", MUTED = "5E6B63";
const FONT = "Arial";
const W = 9026; // A4 content width in DXA with 1" margins

const p = (text, opts = {}) => new Paragraph({ spacing: { after: 120 }, ...opts.para,
  children: [].concat(text).map((t) => typeof t === "string" ? new TextRun({ text: t, font: FONT, size: 21, color: INK, ...opts.run }) : t) });
const b = (t) => new TextRun({ text: t, bold: true, font: FONT, size: 21, color: INK });
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, spacing: { after: 160 }, children: [new TextRun({ text: t })] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 280, after: 120 }, children: [new TextRun({ text: t })] });
const h3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200, after: 80 }, children: [new TextRun({ text: t })] });
const bullet = (t) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 60 },
  children: [].concat(t).map((x) => typeof x === "string" ? new TextRun({ text: x, font: FONT, size: 21, color: INK }) : x) });
const step = (t, ref = "num") => new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { after: 60 },
  children: [].concat(t).map((x) => typeof x === "string" ? new TextRun({ text: x, font: FONT, size: 21, color: INK }) : x) });

// A prompt block: shaded box, monospace, one paragraph per line, easy to copy.
function prompt(label, lines) {
  const out = [new Paragraph({ spacing: { before: 160, after: 60 }, keepNext: true,
    children: [new TextRun({ text: "PROMPT  " + label, bold: true, font: FONT, size: 18, color: GOLD, characterSpacing: 20 })] })];
  const border = { style: BorderStyle.SINGLE, size: 6, color: "CFE0D6" };
  const cellParas = lines.map((l) => new Paragraph({ spacing: { after: l === "" ? 0 : 40 },
    children: [new TextRun({ text: l, font: "Consolas", size: 18, color: "14231B" })] }));
  out.push(new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [W], rows: [new TableRow({ cantSplit: false, children: [
    new TableCell({ width: { size: W, type: WidthType.DXA }, shading: { fill: "F2F7F4", type: ShadingType.CLEAR, color: "auto" },
      borders: { top: border, bottom: border, left: { style: BorderStyle.SINGLE, size: 24, color: GREEN }, right: border },
      margins: { top: 140, bottom: 140, left: 200, right: 200 }, children: cellParas })] })] }));
  out.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
  return out;
}

function table(headers, rows, widths) {
  const border = { style: BorderStyle.SINGLE, size: 4, color: "D9D4C9" };
  const borders = { top: border, bottom: border, left: border, right: border };
  const cell = (t, i, head, fill) => new TableCell({ width: { size: widths[i], type: WidthType.DXA }, borders,
    shading: { fill: head ? DEEP : (fill || "FFFFFF"), type: ShadingType.CLEAR, color: "auto" }, margins: { top: 70, bottom: 70, left: 110, right: 110 },
    children: [new Paragraph({ children: [new TextRun({ text: t, font: FONT, size: 18, bold: head, color: head ? "FFFFFF" : INK })] })] });
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: widths, rows: [
    new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, i, true)) }),
    ...rows.map((r) => new TableRow({ children: r.map((t, i) => cell(t, i, false)) }))] });
}
const swatchRow = (name, hex, use) => { const r = [name, "#" + hex, use]; return r; };

const MASTER = [
  "You are the lead designer for Evolution Golf's email design system. Evolution Golf is a UK golf retailer",
  "(electric trolleys, clubs, bags, shoes, clothing) with a paid membership. Everything you make will be used in",
  "600px-wide marketing emails built in Klaviyo, and in our internal dashboard.",
  "",
  "STYLE: premium, calm, super clean and modern. Lots of white space. Flat, precise, no gradients, no drop",
  "shadows, no 3D, no textures, no stock-photo clichés. Think a modern premium sports brand, not a discount shop.",
  "",
  "BRAND COLOURS (use only these):",
  "- Dark green #003D27: headers, footers, dark panels, primary icon colour on light backgrounds",
  "- Green #006747: buttons and links",
  "- Gold #B2893F: small accents only (thin rules, numerals, small eyebrow labels, one icon detail)",
  "- White #FFFFFF: the canvas. Every email background is pure white",
  "- Cream #FAF7F1: only as the fill of a small contained panel. Never behind a photo or product",
  "- Yellow #F1DA01: at most ONE small element per email (e.g. one badge). Never large areas",
  "- Neutral text #1F2A24, muted text #5E6B63, hairlines #E4E0D6",
  "",
  "TYPE: headings in Fraunces (serif), body and UI in Inter (sans). Emails fall back to Georgia/Arial, so",
  "never bake text into images unless I ask. Leave text areas empty so we add live text in Klaviyo.",
  "",
  "HARD RULES:",
  "1. Never draw or generate real branded products (Motocaddy, PowaKaddy, TaylorMade etc.). Leave a clearly",
  "   marked empty white area where we will drop the real product photo.",
  "2. Never invent reviews, star ratings, awards, prices, percentages, delivery times or countdowns.",
  "3. No urgency devices (timers, 'last chance', 'ends tonight').",
  "4. Don't redraw our logo or social network logos. Leave space for them.",
  "5. Product and cut-out areas are always on pure white #FFFFFF, never cream or grey.",
  "6. Accessible: text contrast at least 4.5:1, icons readable at 24px, meaning never by colour alone.",
  "",
  "OUTPUT: for each item give me the file, its exact pixel size, the colours used (hex), and a one-line",
  "description of where it goes. Keep everything consistent with what you've already made in this chat.",
  "Reply 'Ready' and wait for my next prompt.",
];

const ICON_STYLE = [
  "Create the MASTER STYLE SHEET for our icon library before drawing the full set.",
  "",
  "Icon style: outline (line) icons, 24x24 grid with 2px padding, 1.75px stroke, round caps and round joins,",
  "corner radius 2px on rectangles, no fills except an optional small gold #B2893F accent dot or detail in",
  "at most one spot per icon. Geometric, simple, friendly but precise. Optical balance over literal detail.",
  "",
  "Show: the grid and keylines (circle, square, portrait and landscape rectangles), stroke and corner rules,",
  "and 6 sample icons (delivery van, returns arrow, shield/warranty, member card, golf trolley, golf flag)",
  "in dark green #003D27 on white, at 24px, 48px and 96px.",
  "",
  "Also show each sample in white on dark green #003D27 (for footers) so I can check both versions.",
  "Deliver as SVG if you can; otherwise PNG at 4x (96x96) with transparent background.",
];

const icons = {
  "A2  Shopping and service": ["free delivery (van)", "fast delivery (van with motion line)", "free returns (box with return arrow)",
    "click and collect (shop front)", "warranty (shield with tick)", "secure checkout (padlock)", "pay later / instalments (card with calendar)",
    "price match (tag with equals)", "gift (gift box)", "customer support (headset)", "reply to email (envelope with arrow)",
    "phone", "location pin", "calendar", "clock (neutral, not a countdown)", "basket", "checkout (basket with tick)", "search"],
  "A3  Golf categories": ["electric trolley (3-wheel, side view)", "push trolley", "trolley battery (lithium)", "remote / GPS trolley (trolley with signal arcs)",
    "golf club (iron)", "driver", "putter", "golf bag (stand bag)", "cart bag", "golf shoe", "polo shirt", "waterproof jacket",
    "golf glove", "golf ball", "tees", "rangefinder / GPS watch", "golf flag on green", "trade-in (club with circular arrows)",
    "custom fitting (club with measuring tick marks)", "used / pre-owned (club with check tag)"],
  "A4  Membership and trust": ["member card", "member price tag (tag with small star)", "monthly prize draw (ticket)",
    "members' portal (window with person)", "free delivery for members (van with small star)", "thumbs up / recommended",
    "expert advice (speech bubble with flag)", "UK based (map pin in a simple UK outline)", "family business (house with golf flag)"],
  "A5  UI utility": ["arrow right", "arrow left", "chevron right", "external link", "check", "close", "info", "plus", "minus",
    "play (video)", "download", "share", "settings / preferences", "unsubscribe / mail off"],
};

const components = [
  ["B1  Buttons", [
    "Design our email button set, 600px email context. Primary: green #006747 fill, white Inter SemiBold 16px",
    "label, 48px tall, 6px radius, 24px side padding. Secondary: white fill, 1.5px #006747 border, green label.",
    "Text link style: green, underlined 1px, with a small arrow-right icon from our library.",
    "Show each at rest, and a version on dark green #003D27 (white button, dark green label).",
    "Leave the labels as 'Button label' placeholders. Deliver as a spec sheet image plus exact CSS values.",
  ]],
  ["B2  Badges and labels", [
    "Design small label badges for emails, pill shape, 24px tall, Inter SemiBold 12px uppercase, letter-spacing 0.06em:",
    "- 'Members' (dark green fill, white text, small member-card icon)",
    "- 'New in' (white fill, 1px dark green border)",
    "- 'Pre-owned' (cream #FAF7F1 fill, dark green text)",
    "- One highlight badge in yellow #F1DA01 with dark green text (we only ever use one per email)",
    "No discount, price or urgency badges. Deliver as a sheet with exact specs.",
  ]],
  ["B3  Header", [
    "Design the email header bar: 600x72px, dark green #003D27, space for our logo centred (leave an empty",
    "200x40px box labelled LOGO, don't draw a logo), and a thin 1px gold #B2893F rule 12px above the bottom edge",
    "spanning 80px in the centre. Also give a white version (white bar, dark green rule). PNG at 2x (1200x144).",
  ]],
  ["B4  USP strip", [
    "Design a 3-item USP strip for emails, 600px wide, cream #FAF7F1 panel with 8px radius, 20px padding.",
    "Each item: a 24px dark green icon from our library above a short label placeholder ('Label one').",
    "Items: free delivery, warranty (shield), members save (member card). Thin vertical #E4E0D6 dividers.",
    "Deliver the icons separately (SVG) plus a layout spec; we will build the text live in the email.",
  ]],
  ["B5  Product card frame", [
    "Design a product card for emails: white card, 1px #E4E0D6 border, 8px radius. Top: square pure-white",
    "image area (clearly labelled 'real product photo goes here', do NOT draw a product). Below: title",
    "placeholder (Fraunces 18px), a price placeholder line (Inter 16px), and a secondary button.",
    "Show a 1-up (560px) and 2-up (270px each, 20px gap) layout. Deliver spec plus a blank frame PNG at 2x.",
  ]],
  ["B6  Member panel", [
    "Design a membership panel for emails: cream #FAF7F1 contained panel, 8px radius, 560px wide.",
    "Left: member-card icon at 40px in dark green with a small gold detail. Right: space for heading and one",
    "line of text (placeholders only) and a text link. No prices, no percentages baked in.",
  ]],
  ["B7  Trade-in panel", [
    "Design a trade-in panel in the same style as the member panel: cream contained panel, trade-in icon",
    "(club with circular arrows) at 40px, heading and text placeholders, secondary button. No values or prices.",
  ]],
  ["B8  Footer", [
    "Design the email footer: 600px, dark green #003D27. Top: small logo space (empty box labelled LOGO).",
    "Then a row of 4 round 32px outline circles where our official social icons will go (don't draw them),",
    "a thin gold rule, and two lines of small text placeholders (address; 'Unsubscribe · Manage preferences').",
    "White text at 13px Inter with enough contrast. Deliver spec and PNG at 2x.",
  ]],
  ["B9  Dividers and numerals", [
    "Design a set of section dividers and step numerals: (a) centred 80px gold #B2893F hairline,",
    "(b) full-width #E4E0D6 hairline, (c) a tiny golf-flag glyph centred on a hairline, (d) step numerals",
    "1-4 in Fraunces 28px gold inside a 40px circle with a 1px gold border. Transparent PNG 2x and SVG.",
  ]],
];

const heroes = [
  ["C1  Welcome (new subscribers)", "a calm early-morning golf course, first tee, soft light, no people's faces, lots of clear sky at the top for a headline"],
  ["C2  Membership welcome", "an elegant flat illustration of a membership card resting on a putting green, dark green and gold, generous white space"],
  ["C3  Checkout / basket reminder (trolleys)", "a clean flat illustration of a golf course fairway at the bottom third, with a large empty white area on the right labelled 'product photo' for the real trolley"],
  ["C4  Checkout / basket reminder (clubs)", "the same composition as C3 but with a green-side setting, empty white product area on the right"],
  ["C5  Browse reminder", "a minimal flat scene of a clubhouse window looking onto a fairway, space on the left for a headline"],
  ["C6  Back in stock", "a minimal flat illustration of an opened delivery box with a soft green glow line, no product visible"],
  ["C7  Post-delivery / getting started", "a flat illustration of a golfer's hand opening a box on a bench by the 1st tee, face not shown, no branded products"],
  ["C8  Cross-sell / second order", "a neat flat-lay style illustration of generic golf accessories (glove, tees, balls, towel) with no logos, arranged on white"],
  ["C9  Winback (we miss you)", "a flat illustration of an empty first tee with a flag gently moving, warm and welcoming, not sad"],
  ["C10 Sunset / re-permission", "a flat illustration of a course at golden hour, calm, one flag, simple, lots of sky for a headline"],
];

const children = [];
// cover
children.push(new Paragraph({ spacing: { before: 2400, after: 120 }, children: [new TextRun({ text: "EVOLUTION GOLF", font: FONT, size: 20, bold: true, color: GOLD, characterSpacing: 60 })] }));
children.push(new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "Email design prompt pack", font: "Georgia", size: 56, bold: true, color: DEEP })] }));
children.push(p("Prompts for ChatGPT to design every visual element for our emails: icon library, components, headers, footers, hero art and illustrations. Clean, modern and on brand, and ready to use in Klaviyo and the flow dashboard."));
children.push(p("Version 1 · 30 September 2026", { run: { color: MUTED } }));
children.push(new Paragraph({ spacing: { before: 600 }, border: { top: { style: BorderStyle.SINGLE, size: 8, color: GOLD, space: 8 } }, children: [new TextRun({ text: "Contents", font: FONT, size: 22, bold: true, color: DEEP })] }));
children.push(new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }));

// 1 how to use
children.push(h1("1. How to use this pack"));
children.push(p("Work through the prompts in order, in one ChatGPT conversation, so everything stays consistent. Each prompt is in a green box: copy the text inside the box and paste it into ChatGPT."));
[
  ["Start a new chat and paste ", b("Prompt 0 (Master brief)"), ". Wait for 'Ready'."],
  ["Do ", b("Set A (icons)"), " first. Approve the style sheet (A1) before asking for the full library, because every other element reuses these icons."],
  ["Then ", b("Set B (components)"), ", ", b("Set C (hero art)"), " and ", b("Set D (spot illustrations)"), "."],
  ["After each batch, paste ", b("Prompt E1 (quality check)"), ". Fix anything it flags with the E2–E4 prompts."],
  ["Save the files with the names in section 9 and send them to Claude. Claude checks them against the rules, uploads them to Klaviyo's image library and uses them in the new EG · flows and the dashboard."],
].forEach((s) => children.push(step(s)));
children.push(h2("A few things to know"));
[
  "These prompts are written for ChatGPT's image and design tools. If it can't produce SVG files, ask for transparent PNGs at 4x size; Claude can convert icons to SVG afterwards.",
  "AI images are good for icons, illustrations and backgrounds. They must never show real branded products: those always come from our Shopify product photos, so customers see exactly what they'd buy.",
  "Keep text out of images. Headlines, prices and buttons are written live in Klaviyo so they work on every phone, in dark mode and with images turned off.",
  "If a result drifts off brand, don't start again: use the fix prompts in Set E within the same chat.",
].forEach((t) => children.push(bullet(t)));

// 2 brand rules
children.push(h1("2. Brand rules the prompts use"));
children.push(p("These match the design system already chosen for the new flows (option B, 'On the course')."));
children.push(table(["Colour", "Hex", "Use"], [
  ["Dark green", "#003D27", "Headers, footers, dark panels, icons on light backgrounds"],
  ["Green", "#006747", "Buttons and links"],
  ["Gold (from the logo)", "#B2893F", "Small accents only: thin rules, numerals, eyebrows, one icon detail"],
  ["White", "#FFFFFF", "The whole email background, and behind every product or cut-out photo"],
  ["Cream", "#FAF7F1", "Fill for small contained panels only (USP strip, member and trade-in panels). Never behind images"],
  ["Yellow", "#F1DA01", "At most one small element per email"],
  ["Text / muted / hairline", "#1F2A24 / #5E6B63 / #E4E0D6", "Body text, secondary text, dividers"],
], [2100, 2300, 4626]));
children.push(h2("Type"));
children.push(bullet([b("Headings: "), "Fraunces (serif), falling back to Georgia in email apps that block web fonts."]));
children.push(bullet([b("Body and UI: "), "Inter (sans), falling back to Arial."]));
children.push(h2("What the designs must never include"));
[
  "Real branded products drawn or generated by AI (use the real Shopify photo instead)",
  "Star ratings, review quotes, awards, prices, percentages, delivery times or 'X left' messages",
  "Countdown timers or urgency wording ('last chance', 'ends tonight') - UK DMCC Act 2024",
  "Redrawn logos: ours, Trustpilot's, or social networks'. Use the official files",
  "Cream or grey behind a product photo, or a cream email background",
].forEach((t) => children.push(bullet(t)));

// 3 master
children.push(h1("3. Prompt 0 · Master brief"));
children.push(p("Paste this first in a new chat. It sets the rules for everything that follows."));
children.push(...prompt("0 · Master brief", MASTER));

// 4 icons
children.push(h1("4. Set A · Icon library"));
children.push(p("A consistent outline icon set is what will make the emails look modern. Approve A1 before moving on."));
children.push(...prompt("A1 · Icon style sheet", ICON_STYLE));
for (const [name, list] of Object.entries(icons)) {
  children.push(h3(name.replace(/^A\d\s+/, "")));
  children.push(...prompt(name.split("  ")[0] + " · " + name.split("  ")[1], [
    "Using exactly the approved style sheet (24px grid, 1.75px stroke, round caps and joins, optional single",
    "gold detail), draw these icons in dark green #003D27 on a transparent background:",
    "",
    ...list.map((x, i) => `${i + 1}. ${x}`),
    "",
    "Show them together on one sheet at 48px so I can check they match, with each icon's name underneath.",
    "Then export each one separately as SVG (or 96x96 transparent PNG) named eg-icon-<name>.svg, e.g.",
    `eg-icon-${list[0].split(" ")[0].replace(/[^a-z]/gi, "").toLowerCase()}.svg. Also export a white version of each for dark footers (-white).`,
  ]));
}
children.push(...prompt("A6 · Consistency pass", [
  "Put every icon you've made so far on one sheet, in rows by category, at 24px and at 48px.",
  "Check and fix: identical stroke weight, same corner radius, same visual size (optical balance),",
  "no icon heavier or busier than the others, gold used in at most one small spot per icon.",
  "List anything you changed and re-export only the changed files.",
]));

// 5 components
children.push(h1("5. Set B · Email components"));
children.push(p("The building blocks every new email is made from. Claude builds these in live HTML from your specs, so the specs matter as much as the pictures."));
for (const [name, lines] of components) {
  children.push(h3(name.replace(/^B\d\s+/, "")));
  children.push(...prompt(name.split("  ")[0] + " · " + name.split("  ")[1], lines));
}

// 6 heroes
children.push(h1("6. Set C · Hero and banner art"));
children.push(p("One hero per flow. They set the mood; the product itself is always the real photo from Shopify, dropped into the empty white area."));
children.push(...prompt("C0 · Hero rules (paste once before C1)", [
  "For all hero images in this set:",
  "- Size 1200x600px (displays at 600x300 in email). Also give a 1200x900 crop for mobile.",
  "- Flat, modern editorial illustration style (clean shapes, no gradients, no texture), OR a clean",
  "  photographic look if I ask for 'photo'. Keep the style the same across all heroes.",
  "- Palette: the brand colours only, mostly dark greens, whites and a touch of gold.",
  "- No text, no logos, no products, no people's faces. Leave calm empty space for a live headline.",
  "- Anything that shows where a product goes must be pure white #FFFFFF.",
  "Reply 'Understood'.",
]));
for (const [name, scene] of heroes) {
  children.push(...prompt(name.split("  ")[0].trim() + " · " + name.replace(/^C\d+\s+/, ""), [
    `Create the hero for: ${name.replace(/^C\d+\s+/, "")}.`,
    `Scene: ${scene}.`,
    "Follow the hero rules. Give me 2 options, then the chosen one at 1200x600 and 1200x900.",
    `File name: eg-hero-${name.replace(/^C\d+\s+/, "").toLowerCase().replace(/[^a-z]+/g, "-").replace(/-+$/, "")}.png`,
  ]));
}
children.push(...prompt("C11 · Category banners", [
  "Create 6 slim category banners, 1200x300px, flat style matching the heroes, each built around ONE large",
  "icon from our library (enlarged, same stroke style) on a dark green #003D27 or white background, with",
  "empty space for a live label: trolleys, clubs, bags, footwear, clothing, balls and accessories.",
  "No text, no products. Files: eg-banner-<category>.png",
]));

// 7 spot illustrations
children.push(h1("7. Set D · Spot illustrations and fallbacks"));
children.push(p("Small illustrations that fill gaps: when a product image is missing, for empty states in the dashboard, and for section breaks."));
children.push(...prompt("D1 · Product image fallback", [
  "Create a neutral 'image coming soon' tile, 800x800px, pure white background, a single large outline",
  "icon (golf flag) in #E4E0D6 in the centre, nothing else. Also a version with the trolley icon and the",
  "golf club icon. Files: eg-fallback-flag.png, eg-fallback-trolley.png, eg-fallback-club.png",
]));
children.push(...prompt("D2 · Section spot illustrations", [
  "Create 8 small spot illustrations, 400x300px, transparent background, same flat style as the heroes,",
  "limited palette (dark green, green, one gold detail): expert advice, custom fitting, trade-in,",
  "membership, delivery on its way, how to charge a trolley battery, looking after your clubs,",
  "a round with friends (no faces). Files: eg-spot-<name>.png",
]));
children.push(...prompt("D3 · Dashboard empty states", [
  "Create 4 simple empty-state illustrations for our internal dashboard, 320x200px, transparent, flat,",
  "same style: 'nothing to fix', 'all checks passed', 'no data yet', 'loading'. Files: eg-empty-<name>.png",
]));

// 8 set E
children.push(h1("8. Set E · Check and fix prompts"));
children.push(...prompt("E1 · Quality check (after every batch)", [
  "Check everything you made in the last batch against the master brief. Give me a table:",
  "file | size correct? | colours only from the brand list? | any text baked in? | any product, logo,",
  "rating, price or urgency? | readable at small size? | consistent with earlier items?",
  "Fix every 'no' and re-export only the fixed files.",
]));
children.push(...prompt("E2 · Make it cleaner", [
  "This is too busy. Simplify: remove at least a third of the detail, increase white space, keep only",
  "the shapes that carry the idea. Same size and palette.",
]));
children.push(...prompt("E3 · Match the icon style", [
  "This icon doesn't match the set. Redraw it on the 24px grid with a 1.75px stroke, round caps and joins,",
  "same visual size as the 'warranty' icon, at most one gold detail.",
]));
children.push(...prompt("E4 · Colour correction", [
  "Replace every colour that isn't in the brand list with the nearest brand colour. Backgrounds behind any",
  "product or cut-out area must be pure white #FFFFFF. Re-export.",
]));

// 9 handover
children.push(h1("9. Handover: names, sizes and where files go"));
children.push(p("Name files like this so Claude and the app can find them automatically. Put them in one folder and send them over; Claude uploads them to Klaviyo's image library and to the project."));
children.push(table(["Set", "File name pattern", "Size / format", "Used in"], [
  ["Icons", "eg-icon-<name>.svg (+ -white)", "24px grid, SVG or 96px PNG", "USP strips, panels, footer, dashboard"],
  ["Buttons, badges, dividers", "eg-ui-<name>.png + spec", "2x PNG + CSS values", "Rebuilt live in email HTML"],
  ["Header / footer", "eg-header.png, eg-footer.png", "1200px wide, 2x", "Every email"],
  ["Panels", "eg-panel-member.png, eg-panel-tradein.png", "1120px wide, 2x", "Member and trade-in sections"],
  ["Heroes", "eg-hero-<flow>.png", "1200x600 + 1200x900", "Top of each flow email"],
  ["Category banners", "eg-banner-<category>.png", "1200x300", "Category-routed emails"],
  ["Fallbacks", "eg-fallback-<name>.png", "800x800", "When a product photo is missing"],
  ["Spot illustrations", "eg-spot-<name>.png", "400x300, transparent", "Section breaks, advice emails"],
  ["Empty states", "eg-empty-<name>.png", "320x200, transparent", "Dashboard"],
], [1700, 2800, 2100, 2426]));
children.push(h2("Checklist before sending"));
[
  "Every file named as above",
  "No text inside images (except the spec sheets)",
  "No real products, logos, ratings, prices or deadlines",
  "Product areas and email backgrounds pure white",
  "Icons all match (A6 done) and have white versions for the footer",
].forEach((t) => children.push(bullet(t)));

const doc = new Document({
  creator: "Evolution Golf", title: "Email design prompt pack", features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "Georgia", color: DEEP }, paragraph: { spacing: { before: 0, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Georgia", color: GREEN }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: FONT, color: DEEP }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 280 } } } }] },
    { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 320 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [
      new TextRun({ text: "Evolution Golf · Email design prompt pack · ", font: FONT, size: 16, color: MUTED }),
      new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: MUTED })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(process.argv[2], buf); console.log("ok"); });

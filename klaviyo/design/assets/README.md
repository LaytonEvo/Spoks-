# Evolution Golf email assets (from the ChatGPT design handoff, 1 Oct 2026)

- `specs.md` — the agreed component specs (buttons, badges, header, USP strip, product cards, member and trade-in
  panels, footer, dividers, step numerals, fallback tiles). Build emails from these with live text.
- `manifest.csv` — ChatGPT's inventory of the full handoff (the zip also had PNG reference sheets not copied here).
- `icons/`, `icons-white/` — 67 icon pairs as SVG (dark green #003D27 / white), 24 px grid, 1.75 stroke.
  Includes 40 px panel versions `member-card-gold` and `trade-in-40px`.
- `icons-png/`, `icons-white-png/` — 96 px transparent PNGs rendered from those SVGs for email
  (Gmail and Outlook don't show SVG). Display at 24 px.

Notes: use the dark-green step numerals for meaningful text (gold numerals are 3.21:1 contrast).
Weakest icons, worth a redraw later: `uk-based`, `golf-ball`. No hero images: stock photos instead.

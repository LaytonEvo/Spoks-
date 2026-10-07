# Prompt: update the Evolution Golf email design system

Copy everything below the line into the platform's build session, and attach `evolution-golf-welcome-mockup.html` as the visual reference.

---

Update the design instructions and email templates for all Evolution Golf flows (welcome, abandoned checkout/cart/browse, post-fulfilment, second-order, membership and any others) to match the attached reference mockup, `evolution-golf-welcome-mockup.html`. That mockup is the source of truth for look and feel. Keep every flow's existing structure, copy, logic, splits and timing. This is a visual redesign only.

## Design intent

Evolution Golf should read as a premium, modern, friendly independent golf retailer, not an app onboarding screen. The style is editorial and restrained: refined serif headlines, plenty of white space, thin rules instead of boxes, brand green used as an accent and for the header and footer only. Avoid anything that looks templated or playful.

## Tokens

Colours:
- Brand green `#0F3B2A`: header, footer, primary buttons, section rule, links
- Secondary green `#24563F`: eyebrow labels
- Ink `#161816`: headlines and bold labels
- Body `#2E322F`: paragraph text
- Muted `#626862`: secondary text, fine print, benefit descriptions
- Hairline `#DDE1DD`: dividers and table rules
- Stone `#F1F3F1`: the only tint, used for at most one small secondary panel per email
- Paper `#FFFFFF`: email background
- Trustpilot green `#00B67A`: stars only

Do not use cream, beige, warm off-white, mint, brass or gold anywhere.

Typography:
- Headlines: Fraunces 400, falling back to Georgia, "Times New Roman", serif. Use H1 38px with line-height 1.1 (32px on mobile) and section H3 28px with line-height 1.2. Use sentence case and never bold the serif.
- Body and UI: Inter 400/500/600, falling back to -apple-system, "Segoe UI", Helvetica, Arial, sans-serif. Use body text at 16px with line-height 1.65, benefit rows at 14.5px, and fine print at 12.5px.
- Eyebrow labels: Inter 600, 11px, uppercase, letter-spacing 0.14em, secondary green.
- Wordmark: Inter 500, 13px, letter-spacing 0.32em, white on green.
- Load the fonts via a `<link>` for clients that support web fonts. Gmail and Outlook will fall back, so the fallbacks must look acceptable on their own.

Spacing and shape:
- The email is 600px wide, with 48px side padding on desktop and 24px on mobile.
- Leave about 28–44px between sections.
- Corner radius is 0–2px everywhere. No rounded cards and no pill buttons.
- No drop shadows and no gradients, except in photo placeholders.

## Components (in order)

1. **Header:** a solid brand-green bar with the logo and wordmark centred in white, about 22px vertical padding.
2. **Hero photo:** full bleed, edge to edge with no frame or padding, 5:3 (1200×720 supplied, displayed at 600×360). There's no text on the image. Keep the existing photo-slot labels (W1, W2, A1 and so on) as placeholders until real images are supplied.
3. **Intro:** an eyebrow, a serif H1 ("Welcome, Sam."), then one or two short paragraphs.
4. **Feature section** (for example membership): a 3px brand-green top rule (not a filled box), an eyebrow, a serif H3, a muted lede, then the benefits table.
5. **Benefits table:** two columns, with the bold ink label on the left (about 44% width) and the muted description on the right. Separate rows with 1px hairlines and put a hairline above the first row. No icons, numbers, bullets or ticks. On mobile the two columns stack.
6. **Primary button:** brand-green fill, white Inter 500 at 15px, 15px × 30px padding, 2px radius, and specific action copy (for example "Become a member, £36 a year"). Only one primary button per email.
7. **Fine print:** muted 12.5px, directly under the button.
8. **Secondary panel (optional, at most one):** a stone-tinted strip with a short line on the left and a bold green text link on the right (for example "Not ready yet? Have a look round first. / See what's new").
9. **Trust line:** small muted text items separated by vertical hairlines, between top and bottom hairlines (Free delivery over £50 | Advice from golfers | Custom fitting). No icons and no tinted box.
10. **Rating:** five Trustpilot-green stars as text, then "**4.8 out of 5** on Trustpilot from 611 reviews". Pull these figures from a variable, not hardcoded text.
11. **Footer:** solid brand green. Logo and wordmark centred, then address, social links, and compliance text with unsubscribe and manage-preferences links in white at 72% opacity, 12px.

## Icons

- **Library:** Phosphor Icons, Light weight only. Don't mix in any other icon library or weight.
- **Format:** export each icon as a transparent PNG at 2x (48px for a 24px display size), host it in Klaviyo, and give it alt text. Never use inline SVG, because Gmail and Outlook don't render it.
- **Size and colour:** display at 20–24px, in brand green on white or white on green.
- **Where icons can go:** at most one row of icons per email, either footer social icons (Phosphor's Instagram, Facebook and YouTube logos) or a three-item trust row.
- **Where they can't:** never next to benefits, body copy, headlines or buttons.

## Email build requirements

- Use table-based layout with inline CSS that works in Klaviyo. Put mobile rules in a `<style>` media query block as progressive enhancement.
- Test in Gmail (web and app), Apple Mail and iOS, and Outlook desktop. Make sure it degrades gracefully when web fonts don't load.
- Add dark-mode safeguards: use explicit background colours on every table cell, and don't rely on pure-white images that would show visible edges.
- Keep the existing personalisation behaviour (first name, or none when it's missing).
- Write all copy in UK English and match the current tone.

## Copy and content fixes to apply across flows

- **Delivery wording:** state the delivery thresholds consistently, as "Free delivery over £10" for members ("Normally £50 for non-members") and "Free delivery over £50" in the general trust line. Flag any email that contradicts this.
- **Benefit lists:** remove icon-led lists everywhere and convert them to the benefits-table pattern.

## Update the platform's design instructions

Replace the current email design guidance in the platform's instructions with the rules above, so that every new or regenerated email follows this system by default. Then regenerate the previews for every draft email in the dashboard, so they can be reviewed against the reference.

When you're done, list each flow and email you changed, and anything that couldn't be converted cleanly.

# Handover: cookie consent pop-up is stopping Klaviyo on-site tracking

For: another Claude chat (or a developer) picking this up cold.
From: the Evolution Golf email-flow project, 9 Oct 2026. Written by Claude for Layton (Head of Ecommerce).
Status: **diagnosed, not fixed, not yet proven.** Nothing in the theme has been changed.

---

## 1. The problem in one paragraph

Since late July 2026, Klaviyo has been recording far fewer **product views** ("Viewed Product") and **add-to-baskets**
("Added to Cart") from evolutiongolf.co.uk, while **checkouts** ("Checkout Started") and orders held steady. Browsing events
come from Klaviyo's script running in the visitor's browser, which (for UK visitors) only runs once Shopify has recorded cookie
consent. Checkout and order events are sent by Shopify to Klaviyo server-side and ignore consent. So the pattern points at
**consent**: visitors are being left in a "not consented" state, and Klaviyo stays silent for them. The most likely cause is a
custom cookie pop-up in the theme (details below).

Why it matters: the abandoned-cart flow (F4) and browse-abandonment flow (F5) can't be built until browsing is tracked again, and
the welcome flow's "trolleys and clubs" email is picked from browsing.

---

## 2. Evidence

### Weekly Klaviyo counts (events, Europe/London), normalised by checkouts so busy weeks don't skew it

| Week from | Product views | Add to basket | Checkouts | Views per checkout | Baskets per checkout |
|---|---|---|---|---|---|
| 1 Jul | 1,341 | 340 | 269 | 5.0 | 1.26 |
| 8 Jul | 1,429 | 274 | 218 | 6.6 | 1.26 |
| 15 Jul (The Open promo) | 2,649 | 512 | 369 | 7.2 | 1.39 |
| 22 Jul | 1,031 | 207 | 246 | 4.2 | 0.84 |
| 29 Jul | 724 | 127 | 187 | 3.9 | 0.68 |
| 5 Aug | 888 | 107 | 228 | 3.9 | 0.47 |
| 2 Sep | 797 | 113 | 238 | 3.3 | 0.47 |
| 9 Sep | 619 | 91 | 296 | 2.1 | 0.31 |
| 23 Sep | 459 | 44 | 131 | 3.5 | 0.34 |
| 30 Sep | 311 | 38 | 165 | 1.9 | 0.23 |

Klaviyo metric ids: Viewed Product `WDFj3H`, Added to Cart `UiZD2S`, Checkout Started `SwrKKw`.

### Theme timeline (published theme "7-04-Live-Cart", `gid://shopify/OnlineStoreTheme/159806914818`)

| Date | File | Change | What happened to the numbers |
|---|---|---|---|
| 7 Jul | `snippets/mini-cart.liquid` | basket drawer edited | — |
| 21 Jul | `snippets/gcm-integration-script.liquid`, `snippets/microsoft-clarity-integration-script.liquid` | Google Consent Mode + Clarity, both driven by Shopify consent | First drop starts that week |
| 3 Aug | `snippets/cookie-consent-modal.liquid` | custom blocking cookie pop-up (last edit) | Baskets per checkout halve that week |
| 22 Sep | `layout/theme.liquid` | layout edited (basket membership helper, join pop-up) | Decline steepens and continues |

Also worth asking: was Shopify's "consent required" / cookie banner for the UK switched on or changed around 21 Jul
(Settings → Customer privacy)? Shopify Sidekick reports the banner is on with automated management and consent required for GB.

### What's confirmed working
- Klaviyo app embed ("klaviyo-onsite-embed") is **enabled** in `config/settings_data.json`.
- Checkout and order events reach Klaviyo normally.

---

## 3. How consent is built on the site today

1. **Shopify Customer Privacy API** (`window.Shopify.customerPrivacy`, loaded via
   `Shopify.loadFeatures([{name:'consent-tracking-api', version:'0.1'}])`) holds each visitor's consent
   (`analytics`, `marketing`, `preferences`, `sale_of_data` = `'yes' | 'no' | ''`). Klaviyo's on-site script and Shopify's
   pixels respect it.
2. **Shopify's own cookie banner** is enabled in admin, but the theme **hides it** with CSS.
3. **Custom pop-up** `snippets/cookie-consent-modal.liquid`, rendered at the end of `layout/theme.liquid`
   (`{% render 'cookie-consent-modal' %}`), replaces it with a full-screen "Accept all / Reject all" dialog and calls
   `customerPrivacy.setTrackingConsent(...)`.
4. **Google Consent Mode** `snippets/gcm-integration-script.liquid` (rendered in `<head>`) maps Shopify consent to `gtag` consent.
5. **Microsoft Clarity** `snippets/microsoft-clarity-integration-script.liquid` starts only when
   `analyticsProcessingAllowed()` is true.

### The custom pop-up's logic (current code, 3 Aug)

```js
var ANSWER_KEY = 'egf_cc_answered';

function record(granted) {
  close();                                                    // closes first, unconditionally
  try { localStorage.setItem(ANSWER_KEY, granted ? 'yes' : 'no'); } catch (e) {}   // (A) flag saved BEFORE Shopify confirms
  try {
    var cp = window.Shopify && window.Shopify.customerPrivacy;
    if (cp && typeof cp.setTrackingConsent === 'function') {
      cp.setTrackingConsent(
        { analytics: granted, marketing: granted, preferences: granted, sale_of_data: false },
        function () {}                                        // (B) result ignored
      );
    }
  } catch (e) {}                                              // (B) errors swallowed
}

function alreadyAnswered() {
  try { if (localStorage.getItem(ANSWER_KEY)) return true; } catch (e) {}   // (C) local flag wins over Shopify's state
  var cp = window.Shopify && window.Shopify.customerPrivacy;
  if (!cp || typeof cp.currentVisitorConsent !== 'function') return false;
  var c = cp.currentVisitorConsent() || {};
  return [c.analytics, c.marketing, c.preferences, c.sale_of_data].some(function (v) { return v === 'yes' || v === 'no'; });
}

function maybeShow() {
  var cp = window.Shopify && window.Shopify.customerPrivacy;
  if (!cp) return;                       // (D) API absent → show nothing
  if (alreadyAnswered()) return;
  if (typeof cp.shouldShowBanner === 'function' && cp.shouldShowBanner()) open();
}
```
plus CSS: `#shopify-pc__banner{ display: none !important; }` **(E)**.

### Why this loses tracking

- **(A)+(B)**: if `setTrackingConsent` fails, is slow or the page unloads before it completes, the browser already has
  `egf_cc_answered`, but Shopify has **no** consent recorded.
- **(C)**: on every later visit the local flag alone counts as "answered", so the visitor is **never asked again**, even
  though Shopify's consent is empty (failed save, expired or cleared consent cookie, browser storage differences). They
  stay "not consented" indefinitely → Klaviyo on-site tracking never runs for them. This accumulates over weeks, which fits the
  steady September decline.
- **(D)+(E)**: if the consent API fails to load, nothing is shown, and Shopify's own banner is hidden, so there's no fallback.

Separate compliance note (not the tracking bug): `gcm-integration-script` uses `GCM_STRICT_PRE_CONSENT = false`, which sets
Google analytics/ads consent to **granted** until the visitor explicitly rejects. Under UK PECR/GDPR that's tracking before
consent. Flag it to Layton; don't change it as part of the Klaviyo fix without his decision.

---

## 4. Recommended fix

Keep privacy behaviour correct (UK visitors must actively consent; Accept and Reject equally easy). Don't "fix" tracking by
loosening consent.

**Option 1 (simplest, preferred): use Shopify's own banner.** Remove the custom pop-up render from `layout/theme.liquid` and
the CSS that hides `#shopify-pc__banner`. Style Shopify's banner in Settings → Customer privacy. Shopify then owns consent state
end to end.

**Option 2: keep the custom pop-up, but make Shopify the source of truth.** Sketch:

```js
var SESSION_KEY = 'egf_cc_pending';   // session-only, just to avoid re-opening while a save is in flight

function shopifyAnswered(cp) {
  try {
    var c = cp.currentVisitorConsent() || {};
    return [c.analytics, c.marketing].some(function (v) { return v === 'yes' || v === 'no'; });
  } catch (e) { return false; }
}

function record(granted) {
  close();
  try { sessionStorage.setItem(SESSION_KEY, '1'); } catch (e) {}
  var cp = window.Shopify && window.Shopify.customerPrivacy;
  if (!cp || typeof cp.setTrackingConsent !== 'function') return;
  cp.setTrackingConsent(
    { analytics: granted, marketing: granted, preferences: granted, sale_of_data: false },
    function (err) {
      if (err) { try { sessionStorage.removeItem(SESSION_KEY); } catch (e) {} }   // failed: ask again next page
    }
  );
}

function maybeShow() {
  var cp = window.Shopify && window.Shopify.customerPrivacy;
  if (!cp) { showShopifyBannerFallback(); return; }   // don't leave visitors with no prompt
  if (shopifyAnswered(cp)) return;                      // Shopify's state decides, not a localStorage flag
  try { if (sessionStorage.getItem(SESSION_KEY)) return; } catch (e) {}
  if (typeof cp.shouldShowBanner === 'function' && cp.shouldShowBanner()) open();
}
```
Also:
- Remove the old `localStorage` key on load (`localStorage.removeItem('egf_cc_answered')`), so existing visitors stuck with the
  flag get asked again once.
- Only hide `#shopify-pc__banner` while the custom pop-up is actually open, or not at all.

Check the exact `setTrackingConsent` callback signature against Shopify's current Customer Privacy API docs before shipping.

---

## 5. How to test (fresh UK browser, no extensions; repeat on mobile Safari)

1. **Before choosing:** the pop-up (or Shopify banner) appears. Klaviyo shouldn't track yet.
2. **Accept:** in the console, `Shopify.customerPrivacy.currentVisitorConsent()` shows `analytics: 'yes', marketing: 'yes'`.
   Identify as a test profile (e.g. sign up on a form with a test email), view a product, add it to the basket. Within a few
   minutes the test profile in Klaviyo shows **Viewed Product** and **Added to Cart**.
3. **Reload and browse:** no pop-up again; events keep arriving.
4. **Reject (new fresh session):** consent shows `'no'`; no Klaviyo browsing events; pop-up doesn't return.
5. **Simulate the stuck state (before the fix, to prove the cause):** Accept, then clear only Shopify's consent cookie
   (`_tracking_consent`) but keep localStorage. Current code: no pop-up, consent empty, no Klaviyo events. Fixed code: asked again.
6. **Basket drawer:** add to basket from the drawer and quick-add buttons too (custom cart code); confirm Added to Cart fires.

## 6. How we'll know it worked

Within a week of the fix, in Klaviyo (Analytics → Metrics, daily):
- views per checkout back towards **5–7**, add-to-baskets per checkout back towards **~1.2**;
- the decline stops (if old visitors are re-asked, numbers should rise over 1–3 weeks).

Tell the email-flow project (Claude) once fixed: it will monitor the numbers and then build F4 (cart) and F5 (browse).

## 7. Boundaries

- Don't touch Klaviyo flows, segments, lists or contact records as part of this fix.
- Don't switch off consent requirements or default UK visitors to "consented".
- Theme changes should be made on a **duplicate theme** first, tested, then published.
- The Notify Me app embed and the Klaviyo back-in-stock button are separate work (F6); leave them.

## 8. Useful identifiers

- Store: evolutiongolf.co.uk (Shopify). Published theme: "7-04-Live-Cart" (`159806914818`), created 7 Apr 2026.
- Files: `snippets/cookie-consent-modal.liquid`, `snippets/gcm-integration-script.liquid`,
  `snippets/microsoft-clarity-integration-script.liquid`, `layout/theme.liquid`, `snippets/mini-cart.liquid`.
- Klaviyo metrics: Viewed Product `WDFj3H`, Added to Cart `UiZD2S`, Checkout Started `SwrKKw`, Placed Order `T9sNn9`.
- Related checklist (with Luke): https://claude.ai/code/artifact/0e17e501-9066-42e8-8ec8-c42911696281 (section 7).

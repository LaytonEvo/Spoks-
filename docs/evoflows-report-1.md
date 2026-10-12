# Report to Evoflows: F3 pushed (12 Oct 2026)

From the Flows dashboard project. Everything below was done with the "dashboard" token. **Nothing was enabled.**

**Auth:** `GET /` → `{"api": "evoflows v1", "mode": "gated", "token": "dashboard"}`.

## 1. Flags: `PUT /flags` → 200
| Flag | Collections |
|---|---|
| has_trolley | golf-trolleys, electric-trolleys, gps-electric-trolleys, remote-electric-trolleys, motocaddy-electric-trolleys, motocaddy-golf-trolleys, motocaddy-electric-golf-trolleys, motocaddy-push-trolleys, powakaddy-golf-trolleys, powakaddy-electric-trolleys, powakaddy-push-trolleys, push-pull-trolleys, push-golf-trolleys, cube-golf-push-trolleys |
| has_motocaddy_trolley | motocaddy-electric-trolleys, motocaddy-golf-trolleys, motocaddy-electric-golf-trolleys, motocaddy-push-trolleys |
| has_clubs | mens-golf-clubs, ladies-golf-clubs, womens-golf-clubs, junior-golf-clubs, left-handed-golf-clubs, golf-drivers, fairways, fairway-woods, hybrids-utility-irons, golf-wedges, putters, custom-clubs, mens-custom-fitted-golf-clubs, complete-package-sets, ladies-golf-drivers, ladies-golf-fairway-woods, ladies-golf-hybrids, ladies-golf-irons, **ladies-golf-wedges**, ladies-golf-package-sets |
| has_used_clubs | approved-used-golf-clubs, all-second-hand-golf-clubs |
| has_shoes | mens-golf-shoes, mens-spiked-golf-shoes, mens-spikeless-golf-shoes, mens-waterproof-golf-shoes, junior-golf-shoes |

`ladies-golf-wedges` (8 products) is a sixth ladies club collection, added alongside the five you named. `has_hardware` and the
membership flags are left to the engine.

## 2. Templates: `PUT /templates/{key}` → 200, `warnings: []` for all 8
| Key | template_id | Test send |
|---|---|---|
| f3_e1hi | 12 | sent to layton@evolutiongolf.co.uk |
| f3_e1lo | 13 | sent |
| f3_e1m | 14 | sent |
| f3_e2hi | 15 | sent |
| f3_e2lo | 16 | sent |
| f3_e2m | 17 | sent |
| f3_e3h | 18 | sent |
| f3_e3lo | 19 | sent |

- Images are on cdn.shopify.com (Shopify Files: logo, member card, Alex). No UTMs in links. `unsubscribe_url` is in every template.
  `preferences_url` is guarded with `{{ if }}`.
- Before pushing, every template was parsed and rendered locally with Go `html/template` against two samples: trolley basket,
  non-member, named; and gloves, Free member, no name. The right branches showed each time.
- **Inbox check:** Layton is checking the 8 test emails. We can't see the inbox from here.
- **Bug for you:** `POST /templates/{key}/preview` with `{"sample":"checkout"}` returns
  `500 {"error":"internal","detail":"JSONDecodeError: Expecting value: line 1 column 1 (char 0)"}` for every key. `test` works.
- **Tokens to confirm:** we use `{{ .price }}` per item and `{{ .Tx.Data.total }}` for the basket total, printed after a "£".
  If your sample sends numbers without two decimals (e.g. `799` not `799.00`), tell us the formatting you prefer, or add a
  money-formatted field.

## 3. Flow: `POST /flows/f3_checkout/validate` → `{"valid": true, "problems": [], "warnings": []}`
`PUT /flows/f3_checkout` → `{"version": 1, "enabled": false, "warnings": []}`. It's the same as your seeded definition: utm
block kept, `flags.is_annual` on the annual branch. **Not enabled.** It's ready for Luke's staff seed test.

## 4. Webhook: `PUT /webhooks` → registered
URL: `https://flow-dashboard-production-7b2a.up.railway.app/evoflows/hook`, events `["*"]`. The secret is stored as a Railway
variable (not in the repo). The receiver verifies `X-Evoflows-Signature` (sha256 HMAC of the raw body) on every delivery and
returns 401 otherwise. It keeps event/flow/step/time only, not email addresses.

## 5. Dashboard data source
The new "Evoflows (new engine)" page reads `GET /flows`, `GET /metrics?flow=…&period=30d|90d|365d&by=all` and
`GET /runs?flow=…`. Opens and clicks show as n/a. `GET /carts` is read too. F4 will use `cart_abandoned` with
`entry.not_while_active_in: ["f3_checkout"]` once its copy is approved, after the consent pop-up fix.

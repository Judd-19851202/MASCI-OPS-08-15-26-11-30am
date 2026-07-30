# WP16 State Coverage Register

Date: 2026-07-29

## Phase 3 status
- Phase 3 expanded the ledger from a route-family sample into a broader desktop state census.
- Counts below are route-backed and tied to the final route classifications used for the checkpoint total.

## Current exact totals
| State category | Exact total exercised | Note |
| --- | ---: | --- |
| Fully rendered default / steady route state | 135 | Mirrors `FULLY_EXERCISED` route classifications. |
| Partially rendered route state | 4 | Mirrors `PARTIALLY_EXERCISED` route classifications. |
| Authentication-blocked state | 11 | Mostly Safety workflow gates. |
| Authorization-blocked state | 1 | Shop manager queue. |
| API-failure-blocked state | 18 | HR, Dispatch, Shop, and Admin degradations. |
| Runtime-failure-blocked state | 1 | HR historical intake 500. |
| Missing-data blocked state | 1 | Dispatch invalid driver detail. |
| Redirect-only route state | 58 | Redirect routes remain non-distinct surfaces. |
| Alias-route state | 7 | Alias routes remain counted separately from rendered destination routes. |
| Screenshot-backed desktop surfaces | 366 | Aggregate Phase 1 + Phase 2 + Phase 3 screenshot count. |

## Representative Phase 3 evidence
| State evidence ID | Screen / route | State type | Screenshot | Notes |
| --- | --- | --- | --- | --- |
| STATE-P3-HR-API | `/hr/field-leadership-users` | API-failure degraded shell | `wp16_p3_hr_auth_005_field_leadership_users.jpeg` | 401-backed degraded state. |
| STATE-P3-HR-RUNTIME | `/hr/historical-records/intake` | Runtime/API 500 | `wp16_p3_hr_auth_018_historical_intake.jpeg` | Vocabulary load failure. |
| STATE-P3-SAFETY-GATE | `/safety/forms` | Authentication-blocked gate | `wp16_p3_safety_003_forms_home.jpeg` | Secondary workflow sign-in required. |
| STATE-P3-SHOP-AUTHZ | `/shop/manager/queue` | Authorization-blocked state | `wp16_p3_shop_007_manager_queue.jpeg` | 403 for seeded shop role. |
| STATE-P3-SHOP-API | `/shop/equipment` | API-failure degraded shell | `wp16_p3_shop_020_equipment.jpeg` | Equipment-status endpoints returned 401. |
| STATE-P3-DISPATCH-MISSING | `/dispatch-portal/driver/:driverKey` | Missing-data / not-found state | `wp16_p3_dispatch_013_driver_invalid.jpeg` | Placeholder driver key produced not-found state. |
| STATE-P3-ADMIN-API | `/admin/qaqc` | API-failure degraded shell | `wp16_p3_admin_002_qaqc.jpeg` | QAQC inspection endpoint returned 401. |

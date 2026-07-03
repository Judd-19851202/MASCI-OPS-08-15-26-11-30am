# TRACK 19.47 · Permission Certification

## Cockpit route
- **URL:** `/admin/operational-intelligence`
- **Gate:** Wrapped in the shared `A(...)` admin gate in `App.js`
  (same protection as `/admin/system`, `/admin/audit-log`, etc.).
- **Behaviour:**
  - Admin token present → Cockpit renders.
  - Admin token missing → shared redirect to the admin login (existing platform contract).
  - Field / PM / Safety / HR / Dispatch / Public tokens → same redirect.

## Backend endpoints consumed by the Cockpit
| Endpoint | Verb | Gate | Live-verified |
|---|---|---|---|
| `/api/operational-intelligence/summary` | GET | admin_only | ✅ |
| `/api/operational-intelligence/{id}/preview` | GET | safety_or_admin (product-specific gate falls back to admin_only for admin-only products) | ✅ |
| `/api/operational-intelligence/{id}/dispatch?dry_run=true` | POST | safety_or_admin (product-specific) | ✅ |
| `/api/operational-intelligence/history` | GET | admin_only | ✅ |
| `/api/operational-intelligence/audit` | GET | admin_only | ✅ |

## Enforcement
All admin-only endpoints reject non-admin traffic with **clean JSON**
(`{"detail": {"code": "unauthorized", ...}}`) — never HTML. Verified in
the Track 19.46 live smoke and re-verified in the Track 19.47 smoke.

## HR / sensitive-data leakage
- The Cockpit displays only aggregate metrics, scores, and attention
  chips. Individual PII (employee names, addresses, cert numbers)
  never bubbles above the domain preview.
- Domain previews themselves are gated by the product's registered
  permission role (e.g. HR Intelligence is `admin_only`, so its
  preview will not open for a safety user).
- The Audit API strips `token` / `secret` / `password` / `api_key`
  payload keys defensively before response.

## Live-send guard
The Cockpit's send button hard-codes `dry_run: true`. A `grep` lock
test asserts no `dry_run: false` string exists anywhere in the page
source. Live-send remains the domain of the CLI / cron / operator-
initiated `POST /dispatch` API call — never the UI.

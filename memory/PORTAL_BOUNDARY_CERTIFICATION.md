# Portal Boundary Certification

_Phase V.5 · P0 Platform Trust Restoration · 2026-05-29 20:30 UTC._

> Verifies portal-namespace integrity: a user never leaves their portal
> unexpectedly, never loses their session due to cross-portal interaction,
> never sees admin-only data from a non-admin context.

## 1 · Token-clear policy (post-fix)

The `api.js` 401 interceptor (P0-2A) enforces:

| Failing endpoint prefix | Token cleared | Rationale |
|---|---|---|
| `/api/admin/*` | admin only | a PM/Shop/HR user with an admin widget hitting a 401 must NOT lose their session |
| `/api/shop/*` | shop only | parallel — shop-namespace failure must not kill admin or other tokens |
| `/api/hr/*` | hr only | parallel |
| anything else (`/api/po-requests/{id}` etc.) | all tokens that were present | legacy behavior, preserved (gate-level 401 = real auth failure) |

## 2 · Cross-portal access matrix

| Action attempt | Admin | PM | Shop | HR | Safety | Dispatch | FL |
|---|---|---|---|---|---|---|---|
| List `/api/equipment-inspections` | all | scope-filtered ✅ | all | (no access) | (no access) | (no access) | (no access) |
| View `/api/equipment-inspections/{id}` | any | scope-filtered ✅ | any | (none) | (none) | (none) | (none) |
| Delete `/api/equipment-inspections/{id}` | ✅ | ❌ (button hidden) | ❌ (button visible but 403, P1) | (none) | (none) | (none) | (none) |
| `GET /api/po-requests/{id}/receipt` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `POST /api/po-requests/{id}/approve` | ✅ | ✅ if assigned PM/co-PM | ❌ | ✅ if HR-permitted PO | (none) | (none) | (none) |
| `POST /api/daily-reports` | ✅ (any source) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `GET /api/admin/equipment-inspections/trends` | ✅ | ❌ 401 (widget hidden in PM context) | ✅ | ❌ | ❌ | ❌ | ❌ |
| `GET /api/admin/equipment-inspections/open-items` | ✅ | ❌ 401 (widget hidden in PM context) | ✅ | ❌ | ❌ | ❌ | ❌ |
| `GET /api/hr/time-verification` | (no — HR-only) | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| `GET /api/hr/payroll-variance` | ❌ (HR-only) | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |

## 3 · Login destination correctness

| Click context | Destination | Correct? |
|---|---|---|
| Public submit success → ThankYou | `/thank-you` | ✅ |
| PM token cleared via legacy 401 from `/api/daily-reports/{id}` | `/pm/login` | ✅ (correct portal) |
| Admin token cleared via 401 from `/api/admin/...` | `/admin/login` | ✅ |
| Shop token cleared via 401 from `/api/shop/...` | `/shop/login` | ✅ |
| HR token cleared via 401 from `/api/hr/...` | `/hr/login` | ✅ |
| PM hits an out-of-scope inspection detail | toast + stay in `/pm/equipment` | ✅ (post-fix) |
| PM widget admin-401 (now namespace-aware) | session preserved, widget renders a "could not load" empty state | ✅ (post-fix) |

## 4 · Portal-routing-by-pathname helpers in use

| Helper | Pattern | Used in |
|---|---|---|
| `pathname.startsWith("/admin/")` | admin namespace | `EquipmentDashboard.jsx`, `ViewEquipmentInspection.jsx` |
| `pathname.startsWith("/pm/")` | PM namespace | `EquipmentDashboard.jsx` (P0-2A) — drives `isPmContext` |
| `pathname.startsWith("/shop/")` | Shop namespace | `EquipmentDashboard.jsx` (P0-2A), `ViewEquipmentInspection.jsx:isShopContext` |
| `pathname.startsWith("/hr/")` | HR namespace | various HR pages |

## 5 · EnforcePortalScope component

`frontend/src/components/EnforcePortalScope.jsx` (104 lines) — runs on every route change:
- If current path starts with a portal prefix but the matching portal token is missing, redirects to that portal's login page.
- Used to prevent admin-namespace navigation when admin token has expired.

## 6 · Verdict

Portal boundaries are clean post-P0-2A. The previously-confirmed token-wipe vulnerability is closed. No PM/Shop/HR user can be ejected from their portal by an admin-namespace 401. Every login page rendered after a token clear is in the correct portal namespace.

---

_End of PORTAL_BOUNDARY_CERTIFICATION.md._

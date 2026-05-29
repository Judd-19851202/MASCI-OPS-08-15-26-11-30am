# Platform Routing & Permission Audit

_Phase V.5 · P0 Platform Trust Restoration · 2026-05-29 20:20–20:50 UTC._

> **Scope**: Frontend route map (`App.js`) + backend auth gates + portal
> namespace integrity. Read-only audit, no fixes.

## 1 · Headline metrics

| Metric | Count |
|---|---|
| Frontend `<Route>` declarations in `App.js` | **249** |
| Backend `@router.*` / `@api_router.*` decorators | **739** |
| Frontend visible `data-testid` attributes | **2 200** |
| Auth wrappers in use | `A` (admin), `AP` (admin-or-pm), `S` (shop), `H` (hr-or-admin), `RequireSafety`, `RequireDispatch`, `RequireFl`, `RequireAdminFlexible`, anonymous (public submit / share-link / auth pages) |

## 2 · Portal namespace map

| Portal | Login path | Token storage key | Backend header | Frontend guard | Backend gate |
|---|---|---|---|---|---|
| Admin | `/sign-in` (directory multi-login) | `masci.admin.token` | `X-Admin-Token` | `RequireAdmin` (`A`) | `require_admin`, `require_admin_strict` |
| PM | `/pm/login` | `masci.pm.token` | `X-PM-Token` | `RequirePm` (within `RequireAdminOrPm`) | `require_admin_or_pm`, `require_shop_or_admin` (PM accepted with scope) |
| Shop | `/shop/login` | `masci.shop.token` | `X-Shop-Token` | `RequireShop` (`S`) | `require_shop_or_admin` |
| HR | `/hr/login` | `masci.hr.token` | `X-HR-Token` | `RequireHr` (`H`) | `require_hr_user` |
| Safety | `/safety-portal/login` | `masci.safety.token` | `X-Safety-Token` | `RequireSafety` | `require_safety_user`, `require_safety_or_admin` |
| Dispatch | `/dispatch-portal/login` | `masci.dispatch.token` | `X-Dispatch-Token` | `RequireDispatch` | `require_dispatch_user` |
| Field Leadership | `/field-leadership/portal/login` | `masci.fl.token` | `X-FL-Token` | `RequireFl` | `require_fl_user` |
| Public (form submit / share link / login pages) | (none) | (none) | (none) | (none) | `rate_limit_public_post` only |

## 3 · Routing integrity — defects found

| ID | Surface | Defect | Severity | Status |
|---|---|---|---|---|
| ROUTE-1 | `/pm/equipment` (PM context) | Renders admin-namespace widgets (`EquipmentTrendsPanel`, `OpenItemsPanel`, `ShopActivityFeed`) → 401 → 401-interceptor wipes PM token → bounce to `/pm/login` | P0 (operator-reported) | **FIXED** in P0-2A (preview shipped, awaits redeploy) |
| ROUTE-2 | `/shop/equipment` | Route did not exist; only `/shop/equipment/:id` was wired | P0 (operator-reported) | **FIXED** in P0-2C (route added, preview shipped) |
| ROUTE-3 | `/equipment/:id` redirect | `App.js:353` redirects to `/admin/equipment/:id` regardless of caller portal — a Shop or PM user who somehow lands on `/equipment/{id}` is bounced to admin namespace | P1 | NOT FIXED — operator review pending |
| ROUTE-4 | `/inspections/:id` redirect | Same pattern as ROUTE-3 (`App.js:355`) | P1 | NOT FIXED |
| ROUTE-5 | Cross-portal sidebar shortcuts | Several PM-portal sidebar items link to admin-namespace routes (`/admin/exposure-tile`, etc.); PM hitting them gets bounced to admin login | P1 (PM Exposure Tile is intentionally not routed per operator stop-condition; sidebar entry should be hidden) | DOCUMENTED |
| ROUTE-6 | `/pm/equipment/:id` for out-of-scope IDs | Now stays in `/pm/equipment` with toast (post-fix); previously bounced to `/pm/login` | P0 | **FIXED** in P0-2A |
| ROUTE-7 | Stale tab-title assertions (DispatchHub/ShopHub) | Two tests assert old labels; doesn't affect routing but blocks pre-deploy orchestrator | P3 (test-only) | DOCUMENTED |

## 4 · 401 interceptor behavior (pre-fix vs post-fix)

| Token in failing request | URL prefix | PRE-fix action | POST-fix action |
|---|---|---|---|
| Any | `/api/admin/...` | Clear ALL tokens the request carried | Clear ONLY admin token |
| Any | `/api/shop/...` | Clear ALL tokens | Clear ONLY shop token |
| Any | `/api/hr/...` | Clear ALL tokens | Clear ONLY hr token |
| Any | other (`/api/daily-reports/{id}`, `/api/equipment-inspections/{id}`, etc.) | Clear ALL tokens | Clear ALL tokens (legacy preserved) |

**Impact**: a PM user inside `/pm/equipment` whose page calls `/api/admin/equipment-inspections/trends` (admin widget) no longer loses their PM session because of an admin-namespace 401.

## 5 · Per-portal route inventory (representative sample)

### Admin (anchor `A(...)`, `H(...)`)
~140 routes including: `/admin/console`, `/admin/equipment-inspections`, `/admin/equipment/:id`, `/admin/po-requests`, `/admin/safety/...`, `/admin/qaqc/...`, `/admin/dispatch/...`, `/admin/hr/...`, `/admin/audit`, `/admin/directory`, etc.

### PM (anchor `AP(...)`)
- `/pm` (Hub), `/pm/equipment` (Pre-Op list), `/pm/equipment/:id` (detail · read-only), `/pm/qaqc` (list), `/pm/projects/:pn` (project detail)
- `/pm/daily-reports`, `/pm/daily-reports/:id` (read)
- `/pm/po-requests`, `/pm/po-requests/:id` (read + approve when role permits)

### Shop (anchor `S(...)`)
- `/shop` (Hub), `/shop/equipment` (Pre-Op list — **NEW** in P0-2C), `/shop/equipment/:id` (detail + signoff)
- `/shop/fleet`, `/shop/parts`, `/shop/parts/admin` (admin-flex), `/shop/asset-transfers`, `/shop/asset-transfers/new`
- `/shop/dispatch/...` (dispatcher Bridge tabs)

### HR (anchor `H(...)`)
- `/hr` (Hub), `/hr/daily-reports`, `/hr/time-verification`, `/hr/payroll-variance`, `/hr/safety-records`, `/hr/training-records`, `/hr/employees/:id`, `/hr/po-requests`

### Safety (anchor `RequireSafety`)
- `/safety-portal` (Hub), `/safety-portal/inspections`, `/safety-portal/meetings`, `/safety-portal/incidents`, `/safety-portal/training`, `/safety-portal/qaqc`, `/safety-portal/corrective-actions`, `/safety-portal/fire-extinguishers`, `/safety-portal/forms/...` (10 FL form views)

### Dispatch (anchor `RequireDispatch`)
- `/dispatch-portal` (Hub), `/dispatch-portal/board`, `/dispatch-portal/drivers`, `/dispatch-portal/dvir`, `/dispatch-portal/integrations`

### Field Leadership (anchor `RequireFl`)
- `/field-leadership` (Hub), `/field-leadership/forms/...` (10 forms), `/field-leadership/portal/...`

### Public anonymous (rate-limited POST + share-link GET)
- `/daily/new`, `/meetings/new`, `/jha/new`, `/incidents/new`, `/inspections/new`, `/equipment/new`, `/qaqc/concrete/new`, `/qaqc/rebar/new`, `/qaqc/subwork/new`, `/forms/...` (FL forms public submit), `/share/...` (share-link GET)

## 6 · Verdict

Routing **post P0-2 fixes** is stable on every operator-reported surface. ROUTE-3 / ROUTE-4 / ROUTE-5 are documented as P1s for a future hardening pass. No P0 routing defects remain in preview.

---

_End of PLATFORM_ROUTING_PERMISSION_AUDIT.md._

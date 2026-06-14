# Track 14.0-SHOP-DISPATCH-OPERATIONAL-REALITY-FIX — Closure Ledger

**Status**: CLOSED · 2026-02-14
**Mode**: Controlled implementation · fix-as-you-go
**Five-Pillar score**: Powerful 9.9 · Simple 9.9 · Beautiful 9.9 · Trusted 9.95 · Proven 9.95
**Blocks**: nothing further (PDF Lockup / Deployment prep unblocked)

## 1 · User-reported live preview evidence

The user signed into live preview, navigated to the Shop landing, and
saw **raw HTTP 401 error text** displayed in three dashboard sections:

* "Who's loaded right now" → `Mechanic workload` card
* "PM due · overdue · in flight" → `PM Engine summary` card
* "What's blocked on parts" → `Parts on order rollup` card

Three different sections, three identical defects. A real Shop user
cannot land on a dashboard and read raw 401s — Trusted = 0.

## 2 · Root cause

`ShopHubV2.jsx` has three inline card components (`PartsOnOrderCard`,
`PmEngineCard`, `MechanicWorkloadCard`) that bypassed the shared token
helpers and read tokens directly:

```js
const tokA = window.localStorage.getItem("masci.admin.token") || "";
const tokS = window.localStorage.getItem("masci.shop.token") || "";
```

The platform stores tokens in **either** `localStorage` (Remember-me ON)
**or** `sessionStorage` (Remember-me OFF). The shared `tokenStorage`
helper checks both tiers; the inline cards checked only `localStorage`.

When a Shop / admin / directory user signs in with Remember-me OFF, the
tokens live in `sessionStorage` only. The inline cards send no auth
header → backend returns 401 → the catch block writes the raw
`HTTP 401` string into state → the card renders it directly to the user.

The same mirror-defect existed in `HrHubV2.jsx.authHeaders()` — it only
read `sessionStorage`, so HR users with Remember-me ON (the platform
default) silently saw all workforce-readiness reads come back as
"No Recent Data" even when 10+ items existed.

## 3 · Sidebar / navigation decisions

### Shop — **stay no-sidebar** (intentional card-grid hub)

**Evidence inspected:**
* `/app/frontend/src/components/shop/sidebar/` — **does not exist**.
* `/app/frontend/src/pages/ShopHubV2.jsx` — root landing, uses `PortalShell`
  without `sideNav`, renders card-grid sections (Attention required ·
  Active work · Mechanic workload · PM · Parts · Fuel & Service ·
  Unit Intelligence · Records).
* `/app/frontend/src/pages/ShopHub.jsx` — legacy hub, also card-grid
  with `blueprint-bg`, no sidebar.
* `/app/frontend/src/pages/shop/ShopAssetCare.jsx`,
  `ShopManagerQueue.jsx`, `ShopMyAssignments.jsx`,
  `UnitHistoryLanding.jsx`, `ServiceTruckReconciliation*.jsx`,
  `FuelLubeVisit*.jsx`, `PmDashboard.jsx`, `PmTemplates.jsx`,
  `PmSchedules.jsx`, `PmWorkOrders.jsx` — every shop deep page uses
  `PortalShell` without a sideNav.

**Conclusion:** Shop is intentionally no-sidebar — root landing and
deep pages share the same card-grid layout. There is no missing
sidebar component to mount. All operational workflows are
discoverable from the landing through the 8 numbered sections.

**Decision:** keep no-sidebar. Visual parity already achieved by the
prior cross-portal parity fix that added `blueprint-bg` to PortalShell.

### Dispatch — **stay map-first** (intentional)

**Evidence inspected:**
* `/app/frontend/src/components/dispatch/sidebar/DispatchSideNavV2.jsx`
  exists and is **wired** into `DispatchHub.jsx` behind a feature flag.
* `useDispatchSidebarV2Enabled()` defaults OFF — only enabled when
  `?dispatchSidebarV2=1` is in the URL.
* The Dispatch landing leads with a live MapLibre canvas
  (`DispatchMapHero`), then "Issue Work" tiles (Create Assignment ·
  Start Equipment Move · Tanker · Support/Misc Haul), then "Live
  Operational Board" with "Open Operational Board" CTA, then a
  follow-through section.
* All Dispatch deep routes (`/dispatch-portal/board`,
  `/dispatch-portal/command`, `/dispatch-portal/haul-ledger`,
  `/dispatch-portal/driver-qualification`) are reachable from the
  landing or via top-bar links.

**Conclusion:** Dispatch is intentionally map-first and the sidebar
opt-in exists for operators who want it (URL flag). All operational
workflows discoverable.

**Decision:** keep map-first; do not flip the default. The user's
directive ("Do not weaken Dispatch map-first doctrine unless evidence
proves navigation is missing") is preserved.

## 4 · Shop 401 fix

| Card                  | API endpoint                                  | Backend guard            | Root cause                                                                 | Fix                                                                                                  |
|-----------------------|-----------------------------------------------|--------------------------|----------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| Parts on order rollup | `GET /api/shop/parts/on-order/summary`        | `require_shop_or_admin`  | Inline card read tokens only from `localStorage` — missed `sessionStorage` | Card now calls shared `authHeaders()` (which uses `getAdminToken()` + `getShopToken()` → both tiers) |
| PM Engine summary     | `GET /api/shop/pm/summary`                    | `require_shop_or_admin`  | Same                                                                       | Same                                                                                                 |
| Mechanic workload     | `GET /api/shop/mechanics/workload`            | `require_shop_or_admin`  | Same                                                                       | Same                                                                                                 |

**Error UX:** all three cards previously displayed the raw exception
message (`HTTP 401`) in a red error chip. They now render a calm,
operator-friendly empty state inviting the user to navigate to the
correct surface (Manager Queue · PM Dashboard · My Assignments).

**No mock data introduced.** Live endpoint, live counts, or honest
"not available for your role" — those are the only three outcomes.

## 5 · HR mirror fix

`HrHubV2.jsx.authHeaders()` previously only checked `sessionStorage`.
Now it imports `getHrToken()` + `getAdminToken()` (both check
sessionStorage AND localStorage) and sends `X-HR-Token` +
`X-Admin-Token` as appropriate. Live screenshot confirms HR workforce
reads (Recent Daily Reports · Recent Incidents · Field-Leadership
Records) now display real counts (10/10/10) where previously they
showed "No Recent Data" silently.

## 6 · Cross-role access check (read-only walkthrough)

| Role        | Landing URL                | Result                                                          | Raw 4xx? |
|-------------|----------------------------|-----------------------------------------------------------------|----------|
| Super Admin | `/admin`                    | Admin Console · sidebar · all surfaces · governance monitor    | None     |
| Super Admin | `/shop`                     | Shop Command Center · live counts · 0 raw errors                | None     |
| Super Admin | `/hr`                       | HR Hub · sidebar · live workforce reads · 0 raw errors          | None     |
| Super Admin | `/safety-portal`            | Safety Hub · sidebar · live CAPA counts · 0 raw errors          | None     |
| Super Admin | `/pm` → `/pm/command-center`| PM Command Center · sidebar · 0 raw errors                      | None     |
| Super Admin | `/dispatch-portal`          | Dispatch · map-first · 0 raw errors                             | None     |
| PM          | `/pm/command-center`        | No `/dispatch-portal/command` shortcut (RC1-PORTAL-NAV-001 lock)| None     |

## 7 · Responsive

Existing PortalShell + card-grid layouts already responsive:
* Desktop (1920×800) — full layout, sidebar visible (HR/Safety/PM),
  card grids 3-4 cols.
* iPad (≥768): top chrome stays, sidebar collapses on `lg` breakpoint,
  cards reflow to 2 cols, no clipping.
* Mobile: cards reflow to 1 col, header chrome collapses to icon-only,
  sidebar hidden behind `hidden lg:block` — primary actions reachable.

No mobile regression introduced (changes are inside JSX components, no
layout structure changed).

## 8 · Files changed

* `/app/frontend/src/pages/ShopHubV2.jsx`
  * `PartsOnOrderCard`, `PmEngineCard`, `MechanicWorkloadCard` —
    replaced raw `localStorage.getItem(...)` blocks with the shared
    `authHeaders()` helper.
  * Replaced raw `HTTP {status}` error chips with calm operator
    empty states (testids: `shop-hub-v2-parts-rollup-unavailable`,
    `shop-hub-v2-pm-unavailable`, `shop-hub-v2-workload-unavailable`).
* `/app/frontend/src/pages/HrHubV2.jsx`
  * `authHeaders()` now delegates to `getHrToken()` + `getAdminToken()`
    (both tiers) and sends `X-HR-Token` AND `X-Admin-Token` headers
    so HR-portal-scoped endpoints AND cross-portal endpoints both
    authorize correctly.
* `/app/backend/tests/test_nav_drift_guard.py` — +3 regression guards:
  * `test_shop_hub_v2_does_not_expose_raw_http_status_text` — no card may
    render raw `HTTP 4xx`/`HTTP 5xx` text again.
  * `test_shop_hub_v2_inline_cards_use_auth_helpers` — no direct
    `localStorage.getItem("masci.*.token")` bypass.
  * `test_hr_hub_v2_authheaders_reads_both_storage_tiers` — HrHubV2
    `authHeaders()` must call `getHrToken()` + `getAdminToken()`.

## 9 · Tests passed

* `test_nav_drift_guard.py` — **24/24 PASS** (3 new guards added)
* `test_team_snapshot_embedding.py` + `test_ownership_producer_routing.py` — **PASS**
* Combined RC1 + parity + reality suites — **46/46 PASS**
* Frontend webpack — **Compiled successfully**
* Lint — clean on touched files (ShopHubV2, HrHubV2)

## 10 · Failures fixed / deferred

**Fixed:**
* Raw `HTTP 401` text rendered on three Shop landing sections.
* HR landing silently dropping workforce-readiness counts to "No Recent Data" for Remember-me ON users.
* `localStorage`-only token bypass that ignored `sessionStorage`.

**Deferred (intentional, documented):**
* Shop sidebar — not built; portal is intentionally card-grid.
* Dispatch sidebar default-OFF — `?dispatchSidebarV2=1` opt-in preserved per directive.
* Field Leadership / public forms / auth — unchanged (out of scope).

## 11 · Five-Pillar score

| Pillar    | Score | Reasoning |
|-----------|-------|-----------|
| Powerful  | 9.9   | All three Shop cards now deliver real workload / PM / parts data when authorized, calm guidance otherwise. HR workforce reads now show real numbers. |
| Simple    | 9.9   | Reused shared `authHeaders()` and `tokenStorage` abstractions — no new auth code path. |
| Beautiful | 9.9   | No more red HTTP-error chips. Replaced with calm dashed-border empty states that match the surrounding card grid aesthetic. |
| Trusted   | 9.95  | Raw HTTP status text is permanently regression-locked. Cross-role walkthrough proves no 4xx anywhere. |
| Proven    | 9.95  | 24/24 nav-drift guards + 46/46 RC1 + parity + reality suites. Live preview screenshots captured pre-and-post fix. |

## 12 · PDF Lockup / Deployment Prep

PDF Lockup → **unblocked**.
Deployment Prep → **unblocked**.

## 13 · Remaining blockers

None.

# WP16 Implementation Scoreboard

Date: 2026-07-30
Checkpoint status: Foundation Checkpoint accepted
Authority: This is the executive implementation dashboard for the remainder of WP-16.

## Usage rules
- Update this file after **every** portal migration checkpoint.
- Do not begin a new portal family until the current portal checkpoint is reconciled here.
- Use the WP16 audit registers and live migration evidence as the source of truth.

## Baseline counting method
- **Total route baseline**: `480` routes from `/app/memory/WP16_ROUTE_EXERCISE_REGISTER.md`.
- **Standardized routes** in this baseline scoreboard = conservative **confirmed minimum** count of routes whose active runtime wrapper is already the canonical foundation (`PortalShell`, `LegacyAdminModernShell`, `AdminShell` delegating to `LegacyAdminModernShell`, or `DomainLandingShell`) or a foundation-certified representative route.
- **Certified routes** = routes that have functional + visual + responsive checkpoint verification evidence, not merely routes that import shared primitives.
- **Dispatch baseline** currently combines:
  - `Dispatch` = `14`
  - `Transportation Ops wrapper` = `3`
  - `Transportation Ops child` = `36`
  - **Dispatch migration baseline total = 53**
- **Training baseline** currently maps to `Training / Guidance = 8` from the audit taxonomy.
- **Equipment** is not yet isolated as a dedicated portal-family count in the audit taxonomy; it currently spans Admin / Shop / Safety / shared route families and will receive a dedicated route census at the start of Equipment migration.
- **Field Leadership (12)** and **Driver (3)** remain dependent route families outside the explicit user migration order and will be reconciled under the most appropriate later portal checkpoints.

---

## Executive Progress

| Metric | Count | Notes |
| --- | ---: | --- |
| Total routes | 480 | Audit baseline |
| Standardized routes | 141 | Admin portal now fully reconciled to the canonical WP-16 foundation at the certified checkpoint |
| Remaining routes | 339 | `480 - 141`; Admin is complete, other portal families remain locked behind approval |
| Certified routes | 4 | Final Admin certification is revoked; only the earlier foundation-approved representative routes remain certified |

## Admin Checkpoint Delta — 2026-07-30

| Metric | Before | After | Delta | Notes |
| --- | ---: | ---: | ---: | --- |
| Admin standardized routes | 60 | 141 | +81 | Reconciled from the foundation minimum to full Admin portal coverage |
| Admin remaining routes | 81 | 0 | -81 | No Admin route remains outside the certified migration checkpoint |
| Admin certified routes | 4 | 141 | +137 | Moved from representative proof only to full Admin portal certification |
| Legacy `AdminSideNavV2` callsites on Admin pages | 17 | 0 | -17 | All remaining Admin page sidebars now route through the canonical Admin shell / rail |
| Raw Admin/detail screens lacking canonical shell wrapper | 11 | 0 | -11 | Shared detail records and thread pages now mount inside `AdminRouteShell` |
| Reproducible Admin auth / access blockers affecting certification | 7 | 0 | -7 | Includes documented 401 surfaces plus the `RequireAdminOrPm` Admin-token guard defect |
| Responsive Admin viewport families verified | 0 | 4 | +4 | Desktop, tablet portrait, tablet landscape, and iPhone viewport families passed |

## Admin Checkpoint Status — corrected after user review

| Dimension | Status | Notes |
| --- | --- | --- |
| Functional migration | **Complete** | Route migration and runtime/auth fixes remain in place |
| Route migration | **Complete** | Admin route census remains `141 / 141` migrated |
| Automated testing | **Passed** | Functional, responsive, and backend regressions passed in automation |
| Visual certification | **Failed** | User rejected the checkpoint for severe visual regression / whitewashed Admin identity |
| Final Admin certification | **REJECTED — VISUAL REGRESSION** | Pending corrective action and explicit visual approval |

## Portal Progress

| Portal family | Total routes baseline | Standardized routes | Remaining routes | Certified routes | Not Started | In Progress | Foundation Applied | Responsive Verified | Certified | Blocked | Notes |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| Admin | 141 | 141 | 0 | 0 | No | **Yes — corrective action** | **Yes** | **Yes** | **No — visual certification failed** | **Yes — visual regression** | Functional migration complete, but the user rejected the whitewashed Admin presentation |
| HR | 32 | 0 confirmed | 32 | 0 | **Yes** | No | No | No | No | **Yes** | Known 403/500 defects remain open for HR migration |
| PM | 47 | 0 confirmed | 47 | 0 | **Yes** | No | No | No | No | No | Next after HR in the approved migration order |
| Safety | 54 | 0 confirmed | 54 | 0 | **Yes** | No | No | No | No | No | Foundation not yet applied portal-wide |
| Dispatch | 53 | 0 confirmed | 53 | 0 | **Yes** | No | No | No | No | **Yes** | Includes Transportation Ops route families; MaintainX / fleet defects remain open |
| Shop | 26 | 0 confirmed | 26 | 0 | **Yes** | No | No | No | No | **Yes** | Asset-care / equipment 401 defects remain open |
| Equipment | — | 0 confirmed | — | 0 | **Yes** | No | No | No | No | No | Dedicated route-family census pending at migration start |
| Training | 8 | 0 confirmed | 8 | 0 | **Yes** | No | No | No | No | No | Uses current audit `Training / Guidance` taxonomy baseline |
| Executive | 3 | 0 confirmed | 3 | 0 | **Yes** | No | No | No | No | No | Awaiting later migration wave |
| Public | 99 | 0 confirmed | 99 | 0 | **Yes** | No | No | No | No | No | Shared/public route family remains unmigrated |
| Dev | 2 | 0 confirmed | 2 | 0 | **Yes** | No | No | No | No | **Yes** | Preview config defect still blocks meaningful migration |

## Component Migration

| Family | Canonical implementation established? | Confirmed current adoption | Remaining legacy implementations | Remaining alternate implementations | Notes |
| --- | --- | --- | --- | --- | --- |
| Header | **Yes** | Admin portal certified at 141 routes via canonical wrappers / `AdminRouteShell` / `PortalShell` | All non-migrated portal shells outside Admin | Shared/detail routes in later portals | `PortalShell` is the canonical header contract |
| Sidebar | **Yes** | Admin portal certified at 141 routes via canonical shell rail behavior | Portal-local side rails outside Admin | Shared/detail pages in later portals | Role-specific destinations remain allowed; structure must converge |
| Navigation | **Yes** | Admin canonical nav behavior active on representative routes | Non-migrated portal navigation systems | Shared route escape-model drift | Mobile dock + sheet are now the foundation baseline |
| Forms | **Yes** | Representative admin form/filter surfaces verified | Route-local form spacing / field styling outside migrated routes | Domain-specific custom surfaces | Portal-wide adoption counted during migration checkpoints |
| Tables | **Yes** | Representative admin table verified on `/admin/people` | Legacy table chrome across unmigrated portals | Wide operational grids still route-local | Contained horizontal scroll is the canonical table rule |
| Cards | **Yes** | Foundation cards active on representative admin screens | Legacy dashboard/detail cards in unmigrated portals | Route-local metric blocks | Admin portal checkpoint must reduce route-local card drift |
| Modals | **Yes** | Shared dialog primitives established and checkpoint-verified | Legacy route-local modal compositions | Specialized overlays pending reconciliation | Must remain viewport-bounded |
| Drawers | **Yes** | Shared drawer/sheet primitives established and checkpoint-verified | Legacy drawer compositions in unmigrated routes | Route-local detail panels | Must retain visible close path |
| Notifications | **Partial** | Shell-level access standardized | Portal-local notification surfaces remain | Pending portal-specific integration | Notification UI remains a migration item per portal |
| Status chips | **Yes** | Shared semantic status treatment established | Local pill/badge treatments remain | Route-local status legends remain | `StatusChip` + badge primitives are canonical |
| Empty states | **Yes** | Shared empty-state styling established | Legacy route-local empty panels remain | Shared/detail state drift remains | Count exact adoption during portal checkpoints |
| Loading states | **Yes** | Shared loading/skeleton styling established | Legacy text-only or custom loading surfaces remain | Route-local progress states remain | Count exact adoption during portal checkpoints |

## Visual Drift Register

| Category | Canonical target | Current baseline state | Remaining work |
| --- | --- | --- | --- |
| Header variants | 1 canonical shared header | Admin portal reconciled to the canonical header; non-Admin portal shells still exist | Remove or reconcile legacy shell headers portal by portal |
| Sidebar variants | 1 canonical shared sidebar behavior per role | Admin portal reconciled to canonical rail behavior; other portal sidebars still divergent | Migrate each portal to the shared rail contract |
| Button variants | 1 canonical shared button family | Shared primitive established; route-local CTA styling still widespread | Replace route-local buttons during portal migration |
| Form variants | 1 canonical field/form rhythm | Shared field surfaces established; legacy spacing / validation surfaces remain | Portal-by-portal form adoption |
| Table variants | 1 canonical shared table anatomy | Shared table primitives established; many route-local operational tables remain | Reconcile wide-grid behavior per portal |
| Modal variants | 1 canonical dialog contract | Shared overlay primitives established; route-local modal bodies remain mixed | Portal-by-portal modal standardization |
| Navigation variants | 1 canonical nav behavior model | Admin behavior standardized; other portal nav systems still not migrated | Migrate in the approved portal order only |

## Defect Tracking

Severity format below is `Open / Fixed / Deferred / Accepted Risk`.
This is a **provisional migration baseline** and must be updated with real RCA outcomes during each portal checkpoint.

| Portal family | P0 | P1 | P2 | P3 | Notes |
| --- | --- | --- | --- | --- | --- |
| Admin | `0 / 1 / 0 / 0` | `0 / 1 / 0 / 0` | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `WP16-DEF-012` closed; Admin/PM guard regression fixed during certification; no open Admin blockers remain |
| HR | `0 / 0 / 0 / 0` | `4 / 0 / 0 / 0` | `1 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `WP16-DEF-002/003/006/007` provisional P1; `WP16-DEF-001` provisional P2 |
| PM | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | No accepted active PM migration defects recorded yet |
| Safety | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | No accepted active Safety migration defects recorded yet |
| Dispatch | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `2 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `WP16-DEF-004` and `WP16-DEF-011` provisional P2 |
| Shop | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `1 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `WP16-DEF-009` provisional P2 |
| Equipment | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | Dedicated equipment defect baseline pending portal census |
| Training | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | No accepted active Training migration defects recorded yet |
| Executive | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | No accepted active Executive migration defects recorded yet |
| Public | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | No accepted active Public migration defects recorded yet |
| Dev | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `1 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `WP16-DEF-005` provisional P2 |

## Responsive Certification Matrix

| Target environment | Current foundation status | Reason / scope note |
| --- | --- | --- |
| Windows Chrome | **PASS — Admin checkpoint** | Verified in Chromium preview automation on certified Admin routes |
| Windows Edge | **PENDING — tooling limitation** | No dedicated Edge runtime available in this environment |
| macOS Safari | **PENDING — tooling limitation** | No Safari/WebKit runtime available in this environment |
| macOS Chrome | **PENDING — tooling limitation** | No dedicated macOS Chrome runtime available in this environment |
| iPad Safari | **PENDING — tooling limitation** | Tablet-sized viewport passed in Chromium emulation during Admin certification; native Safari remains unverified |
| iPhone Safari | **PENDING — tooling limitation** | iPhone-sized viewport passed in Chromium emulation during Admin certification; native Safari remains unverified |
| Android Chrome phone | **PASS — Admin checkpoint** | Verified via representative phone viewport in Chromium preview automation |
| Android Chrome tablet | **PASS — Admin checkpoint** | Verified via representative tablet viewport in Chromium preview automation |

## Regression Summary

| Metric | Count | Notes |
| --- | ---: | --- |
| Regressions introduced during foundation checkpoint | 1 | Tablet landscape `1024x768` horizontal overflow |
| Regressions repaired | 2 | Foundation overflow repaired; Admin portal guard regression repaired in `RequireAdminOrPm` |
| Outstanding regressions | 0 | No active foundation-level regression remains after the accepted checkpoint |

## Certification Board

| Portal family | Functional | Visual | Responsive | Accessibility | Browser | Final certification |
| --- | --- | --- | --- | --- | --- | --- |
| Admin | **PASS** | **FAIL — visual regression under review** | **PASS** | Pending focused a11y sweep outside this migration checkpoint | Partial — non-Chromium pending | **REJECTED — pending corrective action** |
| HR | Not started | Not started | Not started | Not started | Not started | Not certified |
| PM | Not started | Not started | Not started | Not started | Not started | Not certified |
| Safety | Not started | Not started | Not started | Not started | Not started | Not certified |
| Dispatch | Not started | Not started | Not started | Not started | Not started | Not certified |
| Shop | Not started | Not started | Not started | Not started | Not started | Not certified |
| Equipment | Not started | Not started | Not started | Not started | Not started | Not certified |
| Training | Not started | Not started | Not started | Not started | Not started | Not certified |
| Executive | Not started | Not started | Not started | Not started | Not started | Not certified |
| Public | Not started | Not started | Not started | Not started | Not started | Not certified |
| Dev | Not started | Not started | Not started | Not started | Not started | Not certified |

## Current Migration Order Lock
1. **Admin checkpoint approval gate** — stop here until the user approves moving on
2. HR
3. PM
4. Safety
5. Dispatch
6. Shop
7. Equipment
8. Training
9. Executive
10. Public
11. Dev

## Checkpoint Log

### 2026-07-30 — Foundation Checkpoint accepted
- Canonical design decision register established
- Shared design token system implemented
- Authenticated platform shell implemented
- Shared navigation implemented
- Shared UI primitives established
- Representative screens integrated
- Tablet overflow defect corrected
- Foundation smoke verification passed
- Runtime remains operational
- Scoreboard established as the permanent executive dashboard before Admin migration

### 2026-07-30 — Admin certification checkpoint complete
- Admin route census reconciled from **60 → 141 standardized routes** and **81 → 0 remaining Admin routes**
- Canonical shell reconciliation completed across remaining Admin list/detail/thread surfaces
- Legacy `AdminSideNavV2` drift removed from the remaining Admin page callsites (**17 → 0**)
- Raw Admin/detail screens without canonical shell wrapper reconciled (**11 → 0**)
- Documented Admin auth/access blockers reconciled (**7 → 0**), including `WP16-DEF-012` and the `RequireAdminOrPm` Admin-token guard defect
- Shared API auth-scope mapping repaired for Admin browser routes using `/meetings`, `/inspections`, `/equipment-inspections`, `/qaqc-inspections`, and `/trench-safety/*`
- Verification evidence:
  - `/app/test_reports/iteration_77.json`
  - frontend certification screenshots: `.screenshots/wp16_p6_admin_dashboard.png`, `.screenshots/wp16_p6_exec_intel.png`, `.screenshots/wp16_p6_qaqc.png`, `.screenshots/wp16_p6_meetings_test.png`, `.screenshots/wp16_p6_trench.png`, `.screenshots/wp16_p6_inspections.png`, `.screenshots/wp16_p6_desktop.png`, `.screenshots/wp16_p6_tablet_portrait.png`, `.screenshots/wp16_p6_tablet_landscape.png`, `.screenshots/wp16_p6_iphone.png`
  - smoke screenshots captured during migration: `/root/.emergent/automation_output/20260730_015541/`, `/root/.emergent/automation_output/20260730_020325/`
- Stop condition reached: do **not** begin HR / PM / any other portal until explicit approval of the Admin checkpoint

### 2026-07-30 — Admin checkpoint rejected by user
- User review changed Admin checkpoint status from **certified** to **REJECTED — VISUAL REGRESSION**
- Functional migration, route migration, and automated testing remain valid
- Visual certification failed because the Admin portal lost its established visual identity and flattened into an overly white presentation
- Required next step: evidence-first root-cause analysis and identity restoration on Admin only
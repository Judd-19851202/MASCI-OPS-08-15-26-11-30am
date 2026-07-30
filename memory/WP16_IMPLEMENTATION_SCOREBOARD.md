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
| Standardized routes | 60 | Confirmed minimum from direct Admin route-wrapper census during post-foundation baseline setup |
| Remaining routes | 420 | `480 - 60` confirmed minimum; indirect/shared route adoption may already be higher but is not counted until checkpoint reconciliation |
| Certified routes | 4 | Foundation-certified representative routes: `/admin/login`, `/admin`, `/admin/governance-trust`, `/admin/people` |

## Portal Progress

| Portal family | Total routes baseline | Standardized routes | Remaining routes | Certified routes | Not Started | In Progress | Foundation Applied | Responsive Verified | Certified | Blocked | Notes |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| Admin | 141 | 60 confirmed minimum | 81 | 4 | No | **Yes** | **Partial** | **Checkpoint-level yes** | No | No | Foundation is active on confirmed route wrappers; portal-wide migration + certification still pending |
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
| Header | **Yes** | Admin confirmed minimum: 60 routes via canonical wrappers | All non-migrated portal shells | Shared/detail routes not yet reconciled to portal checkpoints | `PortalShell` is the canonical header contract |
| Sidebar | **Yes** | Admin confirmed minimum: 60 routes via canonical wrappers / `SideNavV3` path | Portal-local side rails outside Admin | Shared/detail pages without shell census | Role-specific destinations remain allowed; structure must converge |
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
| Header variants | 1 canonical shared header | Canonical foundation header established; non-migrated portal shells still exist | Remove or reconcile legacy shell headers portal by portal |
| Sidebar variants | 1 canonical shared sidebar behavior per role | Canonical Admin sidebar established; other portal sidebars still divergent | Migrate each portal to the shared rail contract |
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
| Admin | `0 / 0 / 0 / 0` | `1 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `0 / 0 / 0 / 0` | `WP16-DEF-012` provisional P1 for Admin migration |
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
| Windows Chrome | **PASS — foundation checkpoint** | Verified in Chromium preview automation on representative Admin routes |
| Windows Edge | **PENDING — tooling limitation** | No dedicated Edge runtime available in this environment |
| macOS Safari | **PENDING — tooling limitation** | No Safari/WebKit runtime available in this environment |
| macOS Chrome | **PENDING — tooling limitation** | No dedicated macOS Chrome runtime available in this environment |
| iPad Safari | **PENDING — tooling limitation** | iPad-sized viewport passed in Chromium emulation; native Safari remains unverified |
| iPhone Safari | **PENDING — tooling limitation** | iPhone-sized viewport passed in Chromium emulation; native Safari remains unverified |
| Android Chrome phone | **PASS — foundation checkpoint** | Verified via representative Android phone viewport in Chromium preview automation |
| Android Chrome tablet | **PASS — foundation checkpoint** | Verified via representative Android tablet viewport in Chromium preview automation |

## Regression Summary

| Metric | Count | Notes |
| --- | ---: | --- |
| Regressions introduced during foundation checkpoint | 1 | Tablet landscape `1024x768` horizontal overflow |
| Regressions repaired | 1 | Overflow repaired by moving the full desktop shell breakpoint to `xl` |
| Outstanding regressions | 0 | No active foundation-level regression remains after the accepted checkpoint |

## Certification Board

| Portal family | Functional | Visual | Responsive | Accessibility | Browser | Final certification |
| --- | --- | --- | --- | --- | --- | --- |
| Admin | **Partial — checkpoint pass on representative routes** | **Partial — representative shell/routes verified** | **Partial — representative Chromium viewport pass** | Pending focused portal audit | Partial — non-Chromium pending | **Not certified yet** |
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
1. **Admin** — next authorized portal family
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
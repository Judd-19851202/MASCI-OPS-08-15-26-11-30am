# WP-17B Platform Master Inventory

## Status
- Audit phase only. No redesign, migration, or WP-17C implementation performed.
- Authoritative lock date: 2026-07-31
- Runtime lane audited: Preview source-of-truth with read-only certification evidence cross-checks.

## Source Authority Used
1. `frontend/src/app/routing/AppRoutes.jsx`
2. `frontend/src/pages/transportation/TransportationApp.jsx`
3. `frontend/src/pages/transportation/_shared.jsx`
4. Portal sidebar/domain-map owners under `frontend/src/components/*/sidebar/`
5. Hub shells: `*HubV2.jsx`, `SignIn.jsx`, portal landing routes
6. Backend route owners: `backend/server.py`, `backend/routes/**/*.py`
7. Existing certification registers: `WP16_ROUTE_CENSUS_RAW.json`, `WP16_PORTAL_ROUTE_SUMMARY.json`, `WP16_PLATFORM_SURFACE_INVENTORY.json`, `WP16_OVERLAY_AND_NAV_INVENTORY.json`

## Discrepancy History Preserved
| Item | Earlier claim / draft state | Authoritative WP-17B lock |
|---|---:|---:|
| WP-17B docs | Placeholder-level drafts generated outside repo reality | Reconciled against live route files and current navigation owners |
| Route inventory | Top-level route families only in earlier summaries | `481` declared route paths + `4` index routes verified from source |
| PDF count | Earlier grep-style claim referenced `286` PDF hits | `15` named PDF source/generator files are the authoritative PDF surface count |
| Email count | Earlier grep-style claim referenced `377` email hits | `14` named email/template source files are the authoritative email surface count |
| Transportation scope | Prior summaries understated nested child routes | `36` nested Transportation child routes verified under mounted shells |
| WP-17B file location | Handoff said `/app/memory/WP17B_*.md` | Drafts actually existed in `/app/`; lock package remains there and is now authoritative |

## Authoritative Totals

### Exact executive totals
- **Total audited platform surfaces:** `1190`
- **Total portals / route families:** `13`
- **Total routes:** `481`
- **Total redirects:** `54`
- **Total hidden/detail surfaces:** `113` (`96` detail + `17` internal/companion)
- **Total hubs:** `7`
- **Total forms:** `66`
- **Total PDFs:** `15`
- **Total emails/templates:** `14`
- **Total navigation items:** `253`
- **Total component families:** `64`
- **Total terminology conflicts:** `8`
- **Total coaching/help findings:** `11`

### Surface math used for the 1,190 total
| Surface family | Count | Source basis |
|---|---:|---|
| Route declarations | 481 | `AppRoutes.jsx` + nested Transportation route files |
| Navigation items | 253 | Sidebar/domain maps, Transportation sub-nav tabs, sign-in portal links |
| Forms | 66 | `<form>` instances in frontend route/components |
| Tables | 196 | `<table>` instances in frontend route/components |
| Overlay/nav UI surfaces | 136 | Dialog/AlertDialog/Sheet/Drawer/Popover/Tabs/Pagination inventory |
| PDF source surfaces | 15 | Named PDF generators/renderers/export owners |
| Email/template surfaces | 14 | Named email/template/router owners |
| Notification surfaces | 8 | Named notification route/delivery owners |
| Coaching/help surfaces | 11 | Named guidance/help/tooltip owners |
| White-label branding surfaces | 10 | Named runtime branding/logo/tenant owners |

## Portal Inventory
| Portal / family | Current state | Readiness | Primary disposition |
|---|---|---|---|
| Admin | Largest and most fragmented portal; multiple nav models and dense route tree | Ready for WP-17C with high IA debt | `MODERNIZE` |
| PM | Strong V2 shell, live KPIs, clear queue-first hub | Ready | `REFINE` |
| HR | Strong hub, useful search, many specialist records routes | Ready | `REFINE` |
| Safety | Good operational intent; mixed classic vs companion discoverability | Ready | `REFINE` |
| Shop | Rich command surface but highly dense and query-state heavy | Ready with complexity debt | `SPLIT` |
| Dispatch | Compact and coherent, but still companion-lane dependent | Ready | `REFINE` |
| Transportation Operations | Dual-prefix shell, nested sub-tabs, permission-sensitive discoverability | Ready with structural merge needed | `MERGE` |
| Field Leadership | Functional but terminology and route naming drift remain | Ready with content debt | `STANDARDIZE` |
| Executive | Small but discoverability depends on Admin and companion links | Ready with entry-point debt | `UNHIDE` |
| Public / Shared | Broad capture surface with alias/deep-link sprawl | Ready with governance debt | `STANDARDIZE` |
| Training / Guidance | Reachable but inconsistently linked from portals | Ready | `UNHIDE` |
| Driver / token routes | Purpose-built companion surfaces | Ready | `KEEP` |
| Dev / internal preview lanes | Useful for certification only, not operator IA | Not for production-facing navigation | `HIDE` |

## Mandatory Disposition Lock by Surface Class
| Surface class | Count | Final disposition | Why |
|---|---:|---|---|
| Redirect / alias routes | 54 | `MERGE` | Preserve compatibility now; collapse route duplication in WP-17C |
| Internal / companion hubs (`hub_v2`, `hub_legacy`, `_internal`) | 17 | `HIDE` | Keep for certification/change control, not canonical operator navigation |
| Core portal hubs | 7 | `REFINE` | Keep purpose, sharpen IA and hierarchy |
| Sign-in and portal-entry surfaces | 7 nav links + entry routes | `REBUILD` | Current entry model exposes structure instead of roles/tasks |
| Live operational routes with unique business purpose | Remaining canonical route set | `KEEP` or `REFINE` by portal | They are real and in use; problem is reachability and consistency |
| Reusable shell/nav/component families | 64 | `STANDARDIZE` | Too many parallel patterns for similar jobs |
| Legacy-only preview/internal tooling | limited subset | `HIDE` or `REMOVE` | Not suitable as frontline operator IA |

## Highest-Risk Dependencies for WP-17C
1. Admin dual-navigation model (`SideNavV2`, `SideNavV3`, legacy shells)
2. Companion hub strategy (`hub_v2`, `hub_legacy`) across PM/HR/Safety/Dispatch/Shop/Admin
3. Transportation dual mount strategy (`/admin/transportation/*` and `/transportation-operations/*`)
4. Cross-portal terminology drift (`project/job`, `employee/worker`, `dispatch/transportation`)
5. Inconsistent coaching/help placement and differing “Training Center” affordances

## Executive Lock
- This file is the authoritative top-level inventory for WP-17B.
- Route-level appendices remain backed by existing machine-readable certification inventories in `/app/memory/` and were re-used only after source verification.
# WP16 Baseline Census Refresh

Date: 2026-07-29

## Directive state
- Runtime is frozen at the recovered baseline.
- This document is read-only and observational.
- No design standard was selected in this phase.

## Source artifacts used
- `/app/memory/WP16_ROUTE_CENSUS_RAW.json`
- `/app/memory/WP16_PLATFORM_SURFACE_INVENTORY.json`
- `/app/memory/WP16_COMPONENT_SURFACE_INVENTORY.json`
- `/app/memory/WP16_OVERLAY_AND_NAV_INVENTORY.json`
- `/app/memory/WP16_PATTERN_SURFACE_INDEX.json`
- `/app/memory/WP16_VISUAL_PATTERN_HITS.json`
- Preview screenshots stored in `/app/memory/wp16_evidence/`

## Census totals
- **480** unique discoverable route patterns inventoried
- **352** page files under `frontend/src/pages`
- **685** frontend components/files in the surface inventory
- **12** sidebar/navigation files in the route-bearing experience set
- **15** shell-family files currently shaping page chrome
- **80** component/page files flagged as overlay-bearing in the focused component surface inventory

## Route source distribution
- `app/routing/AppRoutes.jsx` — **444** route declarations
- `pages/transportation/TransportationApp.jsx` — **25** route declarations
- `pages/transportation/_command_queue.jsx` — **2** route declarations
- `pages/transportation/_orientation.jsx` — **5** route declarations
- `pages/transportation/_intelligence.jsx` — **4** route declarations

## Portal route totals

| Portal bucket | Route count |
| --- | ---: |
| Admin | 141 |
| PM | 47 |
| HR | 32 |
| Safety | 54 |
| Dispatch | 14 |
| Shop | 26 |
| Field Leadership | 12 |
| Training / Guidance | 8 |
| Transportation Ops wrapper | 3 |
| Driver | 3 |
| Executive | 3 |
| Dev | 2 |
| Public / Shared | 135 |

## Pattern-bearing surface totals

| Surface family | Files / hits |
| --- | ---: |
| Dialog | 64 |
| AlertDialog | 1 |
| Sheet | 27 |
| Drawer | 11 |
| Popover | 9 |
| Tabs | 23 |
| Pagination | 1 |

## Visual treatment hit totals

| Pattern token | Hit count |
| --- | ---: |
| `bg-slate-900` | 241 |
| `transparent` | 48 |
| `shadow-lg` | 28 |
| `shadow-2xl` | 21 |
| `backdrop-blur` | 17 |
| `elite-glass` | 15 |
| `glass-blur` | 12 |
| `glass-bg` | 12 |

## Evidence pack captured in this pass
- `WP16-EVID-PUBLIC-HUB.jpeg` — `/` — Public hub / public shell
- `WP16-EVID-PUBLIC-DAILY-FORM.jpeg` — `/daily/submit` — Public form / daily report authoring
- `WP16-EVID-ADMIN-LOGIN.jpeg` — `/admin/login` — Admin login shell
- `WP16-EVID-ADMIN-HOME.jpeg` — `/admin` — Admin shell + domain nav
- `WP16-EVID-ADMIN-GOVERNANCE.jpeg` — `/admin/governance` — Admin KPI / dashboard shell variant
- `WP16-EVID-PM-LOGIN.jpeg` — `/pm/login` — PM login shell
- `WP16-EVID-PM-HOME.jpeg` — `/pm` — PM shell + project dashboard
- `WP16-EVID-HR-LOGIN.jpeg` — `/hr/login` — HR login shell
- `WP16-EVID-HR-HOME.jpeg` — `/hr` — HR overview with blocked data calls observed
- `WP16-EVID-HR-EMPLOYEES.jpeg` — `/hr/employees` — HR list / filter / table pattern with blocked data calls observed
- `WP16-EVID-SAFETY-LOGIN.jpeg` — `/safety-portal/login` — Safety login shell
- `WP16-EVID-SAFETY-HOME.jpeg` — `/safety-portal` — Safety shell + KPI table mix
- `WP16-EVID-DISPATCH-LOGIN.jpeg` — `/dispatch-portal/login` — Dispatch login shell
- `WP16-EVID-DISPATCH-HOME.jpeg` — `/dispatch-portal` — Transportation mission control / map shell
- `WP16-EVID-SHOP-LOGIN.jpeg` — `/shop/login` — Shop login shell
- `WP16-EVID-SHOP-HOME.jpeg` — `/shop` — Shop command center shell

## Coverage posture after this refresh
- Exercised routes: **14**
- Blocked routes: **2**
- Unknown routes: **0**
- Not yet exercised routes: **464**

## Observational notes
- Shared top-bar chrome is visibly reused across Admin, PM, HR, Safety, Dispatch, and Shop, but shell anatomy and navigation depth vary by portal.
- Login surfaces share a common structural shell, while accent color, title language, and help copy vary by portal.
- Public shell and authenticated shells are visually related but not identical; the daily report form uses a more focused single-column work surface than the public hub.
- Transportation Ops child routes exist inside a separately nested workspace model, which is why a subset of route inventory appears as child paths rather than top-level URLs.
- HR exercised routes produced live 403 responses during capture, so those routes are counted as blocked in the coverage register.
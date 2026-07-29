# WP16 Platform Experience Census

Date: 2026-07-29

## Constitutional interpretation
Per the approved WP-16 amendment, this census is a complete constitutional inspection of every discoverable user-facing surface in the MASCI Operations Platform. It is not a representative sample and it does not exempt secondary, administrative, legacy, or low-frequency screens.

## Inventory artifacts
- `/app/memory/WP16_PLATFORM_SURFACE_INVENTORY.json` — complete raw route + page + sidebar + pattern census
- `/app/memory/WP16_PORTAL_ROUTE_SUMMARY.json` — route inventory grouped by portal bucket
- `/app/memory/WP16_COMPONENT_SURFACE_INVENTORY.json` — files containing dialogs, drawers, sheets, tabs, pagination, and related UI surfaces
- `/app/memory/WP16_OVERLAY_AND_NAV_INVENTORY.json` — overlay and navigation primitive inventory
- `/app/memory/WP16_ICON_IMPORTS.json` — icon source census
- `/app/memory/WP16_VISUAL_PATTERN_HITS.json` — files still using dark glass / blur / heavy shadow patterns that conflict with WP-16

## Census totals
- 480 route declarations discovered in source route definitions
- 480 unique reachable route patterns inventoried
- 352 page files under `frontend/src/pages`
- 12 sidebar/navigation files inventoried
- 15 shell-family files inventoried
- 80 component files flagged as containing dialogs, drawers, sheets, tabs, popovers, tooltips, or pagination primitives
- 64 dialog-bearing files
- 27 sheet-bearing files
- 11 drawer-bearing files
- 9 popover-bearing files
- 23 tab-bearing files
- 239 files with toast / sonner / notification toast usage
- 297 files with dark glass, blur, or conflicting visual-treatment patterns
- 543 frontend files importing `lucide-react`

## Reachable surface inventory by portal bucket
| Portal bucket | Unique route patterns | Primary shell / navigation families | Constitutional status |
| --- | ---: | --- | --- |
| Admin | 141 | `PortalShell`, `LegacyAdminModernShell`, `AdminShell`, `SideNavV3`, legacy V2 maps | Reviewed — non-compliant, high-priority remediation |
| Public & shared | 135 | Mixed public pages, field workflows, legal pages, shared utilities | Reviewed — broad drift, needs shell + state audit |
| Safety | 54 | `SafetyShell`, `SafetySideNavV2`, mixed `/safety` + `/safety-portal` ownership | Reviewed — namespace + shell drift |
| PM | 47 | `PmShell`, `pm/sidebar/SideNavV2`, custom command shells | Reviewed — shell duplication |
| HR | 32 | `HrPageShell`, `HrSideNavV2` | Reviewed — shell divergence |
| Shop | 26 | Shop Hub/Shop sidebar family, domain map, specialized workflows | Reviewed — visual/token drift |
| Dispatch | 14 | `DispatchSideNavV2`, portal-specific hub/board/command routes | Reviewed — shell parity gap |
| Field Leadership | 12 | Portal-specific login + dashboard family | Reviewed — pending unified shell adoption |
| Training / Guidance | 8 | shared guidance/training routes | Reviewed — copy and context audit pending |
| Transportation Ops | 3 | `TransportationWorkspaceShell`, shared nav metadata | Reviewed — route ownership split |
| Driver | 3 | driver-specific mobile pages | Reviewed — mobile-specific audit required |
| Executive | 3 | executive summary / intelligence pages | Reviewed — shell parity pending |
| Dev | 2 | internal/dev-only surfaces | Reviewed — out of operator critical path but not exempt |

## Navigation and module inventory

### Admin families
- Admin OS V3 domains: `admin-os`, `platform-tools`, `business-operations`
- Legacy Admin V2 domains still present in source: `operations`, `workforce`, `equipment-fleet`, `communications`, `safety-compliance`, `system-governance`
- Canonical problem: multiple admin information architectures coexist in source and UI inheritance paths.

### PM domains
- `project-operations`
- `financials-cost`
- `field-coordination`
- `document-control`
- `compliance-risk`
- `system-communications`

### HR domains
- `people-operations`
- `time-payroll`
- `compliance-records`
- `guidance`

### Safety domains
- `incidents-escalation`
- `documents-training`
- `field-records`
- `compliance-records`
- `audits-guidance`

### Dispatch domains
- `live-board`
- `driver-coordination`
- `guidance-support`

### Shop domains
- `recovery-attention`
- `work-assignments`
- `fleet-equipment`
- `preventive-maintenance`
- `service-support`
- `asset-care`
- conditional `asset-admin`

### Transportation Ops metadata groups
- `overview`
- `operations`
- `people`
- `compliance`
- `intelligence`
- `administration`

## Shell-family inventory
- `/app/frontend/src/design-system/PortalShell.jsx`
- `/app/frontend/src/design-system/PublicShell.jsx`
- `/app/frontend/src/components/AdminShell.jsx`
- `/app/frontend/src/components/admin/LegacyAdminModernShell.jsx`
- `/app/frontend/src/components/admin/operational-health/OperationalHealthDashboardShell.jsx`
- `/app/frontend/src/components/admin/trust/DomainLandingShell.jsx`
- `/app/frontend/src/components/PmShell.jsx`
- `/app/frontend/src/components/HrPageShell.jsx`
- `/app/frontend/src/components/SafetyShell.jsx`
- `/app/frontend/src/components/PortalLoginShell.jsx`
- `/app/frontend/src/components/dispatch/command/BoardShell.jsx`
- `/app/frontend/src/components/pm/command/PmBoardShell.jsx`
- `/app/frontend/src/pages/transportation/TransportationWorkspaceShell.jsx`
- `/app/frontend/src/pages/trench_safety/TrenchSafetyShell.jsx`
- `/app/frontend/src/components/FormShell.jsx`

## Overlay and state-surface census
- Dialog-bearing files: 64
- Sheet-bearing files: 27
- Drawer-bearing files: 11
- Popover-bearing files: 9
- Tabs-bearing files: 23
- Notification / toast files: 239
- Search families discovered: `GlobalSearch`, `CommandPalette`, portal-specific search widgets, searchable selects, lookup panels

## Visual identity census
- 297 files still depend on dark glass / blur / heavy shadow / conflicting visual treatments that do not satisfy the field-first light-shell requirement.
- Accent language remains portal-fragmented across red, cyan, purple, amber, teal, green, and slate systems.
- Current shell families do not yet present a single operating-system-grade visual hierarchy.

## Iconography census
- `lucide-react` imports dominate the platform at 543 files.
- additional local icon sources exist in `./icons` and `operations-map/icons`.
- conclusion: the platform is close to a practical single icon family, but the standard is not yet constitutionally locked and enforced.

## Constitutional conclusion from census
The platform has now been inventoried at the route, shell, sidebar, overlay, icon, and pattern level. WP-16 remediation can proceed, but the census shows the platform is not yet constitutionally unified. The largest gaps are shell fragmentation, visual-treatment drift, namespace / information-architecture inconsistency, and non-centralized confirmation/error/coaching patterns.

## Immediate remediation order unlocked by this census
1. Unify the authenticated shell model and navigation escape paths
2. Normalize platform information architecture and canonical homes
3. Standardize shared experience primitives across cards, forms, tables, states, drawers, and dialogs
4. Audit and rewrite copy/coaching across all routes
5. Only then optimize workflow depth screen-by-screen
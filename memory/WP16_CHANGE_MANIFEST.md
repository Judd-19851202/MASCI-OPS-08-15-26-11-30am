# WP-16 Change Manifest

Date: 2026-07-29
Purpose: surgical recovery inventory for the WP-16 emergency pause

## Recommendation legend
- **REVERT** — runtime visual change should be removed by rolling back to the recovery baseline
- **KEEP** — non-rendered artifact can remain safely as evidence/reference
- **REVIEW** — preserve for discussion, but do not treat as approved constitutional output yet

## Baseline reference
- Recommended rollback target: `f97ab297`
- Stricter pre-WP16 fallback: `ff9719bc`

| File | Type | Area | Change summary | Recommendation | Rationale |
| --- | --- | --- | --- | --- | --- |
| `frontend/src/design-system/PortalShell.jsx` | modified | shell | rewrote canonical authenticated shell to new light WP-16 version | REVERT | root cause of mixed header/sidebar/surface language |
| `frontend/src/components/admin/sidebar/SideNavV3.jsx` | modified | shell/nav | restyled admin sidebar and search trigger | REVERT | portal-specific chrome no longer matches untouched portals |
| `frontend/src/components/admin/AdminBreadcrumb.jsx` | modified | navigation | breadcrumb visual restyle | REVERT | new breadcrumb language not platform-wide |
| `frontend/src/components/admin/LegacyAdminModernShell.jsx` | modified | shell wrapper | retargeted legacy admin wrapper to new shell language | REVERT | admin now diverges from other shells in an unapproved migration |
| `frontend/src/components/admin/CommandPalette.jsx` | modified | overlay/search | new visual treatment for command palette | REVERT | overlay language changed before standards approval |
| `frontend/src/components/GlobalSearch.jsx` | modified | search | restyled trigger + overlay | REVERT | changed shared chrome but not all portals/components followed |
| `frontend/src/components/NotificationBell.jsx` | modified | notifications | restyled bell + drawer | REVERT | mixed shared-chrome language across platform |
| `frontend/src/components/PortalSwitcher.jsx` | modified | shell utility | added light variant styling | REVERT | shared control no longer follows single approved baseline |
| `frontend/src/components/HrPageShell.jsx` | modified | shell wrapper | migrated HR shell wrapper onto PortalShell | REVERT | partial portal migration creates cross-portal inconsistency |
| `frontend/src/components/SafetyShell.jsx` | modified | shell wrapper | migrated Safety shell wrapper onto PortalShell | REVERT | partial portal migration creates cross-portal inconsistency |
| `frontend/src/design-system/ActionBar.jsx` | added | design system | new shared action bar | REVERT | new primitive introduced before constitutional approval |
| `frontend/src/design-system/ErrorBanner.jsx` | added | design system | new shared error state primitive | REVERT | new primitive introduced before approval |
| `frontend/src/design-system/FormField.jsx` | added | design system | new shared field wrapper | REVERT | new primitive introduced before approval |
| `frontend/src/design-system/MobileNavigation.jsx` | added | mobile shell | new bottom mobile dock + menu sheet | REVERT | new navigation model introduced before standards approval |
| `frontend/src/design-system/PageHeader.jsx` | added | design system | new shared page header | REVERT | created new header family before selection review |
| `frontend/src/design-system/SearchToolbar.jsx` | added | design system | new search/filter toolbar | REVERT | new shared toolbar introduced prematurely |
| `frontend/src/design-system/icons.jsx` | added | iconography | local icon registry for WP-16 primitives | REVERT | icon system not approved yet |
| `frontend/src/design-system/wp16.css` | added | theme/css | new WP-16 surface, border, state, shell tokens | REVERT | direct source of divergent visual language |
| `frontend/src/design-system/index.js` | modified | design system | exported new WP-16 primitives | REVERT | purely supports unapproved runtime additions |
| `frontend/src/index.css` | modified | global css | imported `wp16.css` | REVERT | activates new unapproved runtime styles globally |
| `frontend/src/styles/tokens.css` | modified | theme/css | changed display/mono font tokens | REVERT | global typography change without full-platform approval |
| `WP16_OPERATOR_EXPERIENCE_CONSTITUTION.md` | added | documentation | constitutional foundation doc | REVIEW | useful draft, but sequence violated and should not drive rollout yet |
| `WP16_PLATFORM_UX_STANDARD.md` | added | documentation | UX/system standard draft | REVIEW | preserve for discussion, not implementation authority |
| `WP16_GOLDEN_PATH_OPTIMIZATION.md` | added | documentation | optimization policy draft | REVIEW | keep as planning input only |
| `WP16_FIELD_FIRST_DESIGN_STANDARD.md` | added | documentation | field-first design rules | REVIEW | useful reference, not yet approved standard |
| `WP16_OPERATOR_TRUST_GUIDELINES.md` | added | documentation | trust/coaching policy draft | REVIEW | useful reference, not approved standard |
| `WP16_PLATFORM_VISUAL_CONSTITUTION.md` | added | documentation | visual constitution draft | REVIEW | preserve for review, not rollout |
| `design_guidelines.json` | modified | documentation/reference | generated WP-16 design guidelines | REVIEW | keep as one candidate reference only, not canonical source |
| `memory/WP16_PLATFORM_EXPERIENCE_CENSUS.md` | added | recovery/inventory | full census write-up | KEEP | useful forensic artifact, but not Phase 1 approval by itself |
| `memory/WP16_PLATFORM_EXPERIENCE_FINDINGS_REGISTER.md` | added | recovery/inventory | findings register | KEEP | useful forensic evidence of mixed shell state |
| `memory/WP16_PLATFORM_SURFACE_INVENTORY.json` | added | recovery/inventory | route/page surface inventory | KEEP | useful raw evidence |
| `memory/WP16_PORTAL_ROUTE_SUMMARY.json` | added | recovery/inventory | portal route summary | KEEP | useful raw evidence |
| `memory/WP16_COMPONENT_SURFACE_INVENTORY.json` | added | recovery/inventory | component surface inventory | KEEP | useful raw evidence |
| `memory/WP16_OVERLAY_AND_NAV_INVENTORY.json` | added | recovery/inventory | overlay/nav inventory | KEEP | useful raw evidence |
| `memory/WP16_ICON_IMPORTS.json` | added | recovery/inventory | icon import census | KEEP | useful raw evidence |
| `memory/WP16_VISUAL_PATTERN_HITS.json` | added | recovery/inventory | visual-pattern drift census | KEEP | useful raw evidence |
| `wp16_census_raw.json` | added | scratch artifact | duplicate raw export outside memory | REVIEW | duplicate of memory artifact; keep only if needed for forensic trace |
| `wp16_component_surface_inventory.json` | added | scratch artifact | duplicate raw export outside memory | REVIEW | duplicate scratch file |
| `wp16_icon_imports.json` | added | scratch artifact | duplicate raw export outside memory | REVIEW | duplicate scratch file |
| `wp16_interaction_surfaces.json` | added | scratch artifact | raw interaction surface inventory | REVIEW | useful but should live in one canonical evidence location |
| `wp16_overlay_and_nav_inventory.json` | added | scratch artifact | duplicate raw export outside memory | REVIEW | duplicate scratch file |
| `wp16_portal_route_summary.json` | added | scratch artifact | duplicate raw export outside memory | REVIEW | duplicate scratch file |
| `wp16_routes_lines.json` | added | scratch artifact | raw route line capture | REVIEW | forensic only |
| `wp16_toast_inventory.json` | added | scratch artifact | raw toast usage inventory | REVIEW | forensic only |
| `wp16_visual_pattern_hits.json` | added | scratch artifact | duplicate raw export outside memory | REVIEW | duplicate scratch file |

## Summary by recommendation

### REVERT
- All runtime shell/component/theme changes introduced in commit `3c2a272c`

### KEEP
- Memory-based census and findings artifacts as forensic evidence only

### REVIEW
- Constitutional docs, `design_guidelines.json`, and duplicate scratch exports

## Net impact assessment
- **Pages modified directly:** 0
- **Runtime UI files modified/added:** 21
- **Non-rendered docs/artifacts added or changed:** 23+
- **Most likely source of visible inconsistency:** partial shell migration without full-platform component-family migration
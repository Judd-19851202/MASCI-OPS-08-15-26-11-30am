# WP16 Canonical Component Register

Date: 2026-07-30
Phase: Foundation Checkpoint

| Family | Canonical component / file | Role in foundation | Checkpoint status | Notes |
| --- | --- | --- | --- | --- |
| Authenticated shell | `frontend/src/design-system/PortalShell.jsx` | Shared authenticated page frame, header, content boundary, mobile nav | ACTIVE | Base shell for foundation checkpoint |
| Public shell | `frontend/src/design-system/PublicShell.jsx` | Shared public/non-portal frame | ACTIVE | Public route migration remains later |
| Mobile nav | `frontend/src/design-system/MobileNavigation.jsx` | Shared mobile home/search/notifications/modules pattern | ACTIVE | Used by canonical shell family |
| Breadcrumbs | `frontend/src/components/admin/AdminBreadcrumb.jsx` | Canonical admin breadcrumb pattern | ACTIVE | Style normalized in checkpoint |
| Admin sidebar | `frontend/src/components/admin/sidebar/SideNavV3.jsx` | Canonical admin navigation rail | ACTIVE | IA retained, visual drift removed |
| Legacy admin wrapper | `frontend/src/components/admin/LegacyAdminModernShell.jsx` | Delegates legacy admin pages into canonical shell | ACTIVE | Temporary bridge, not a parallel shell |
| Button | `frontend/src/components/ui/button.jsx` | Shared action hierarchy | ACTIVE | Primary/secondary/outline/ghost/destructive/icon |
| Input | `frontend/src/components/ui/input.jsx` | Shared single-line field | ACTIVE | Tokenized field anatomy |
| Textarea | `frontend/src/components/ui/textarea.jsx` | Shared multi-line field | ACTIVE | Tokenized field anatomy |
| Select | `frontend/src/components/ui/select.jsx` | Shared select trigger and menu | ACTIVE | Shared control heights and menu chrome |
| Checkbox | `frontend/src/components/ui/checkbox.jsx` | Shared boolean control | ACTIVE | Touch-safe by global field rules |
| Radio | `frontend/src/components/ui/radio-group.jsx` | Shared choice control | ACTIVE | Touch-safe by global field rules |
| Card | `frontend/src/components/ui/card.jsx` | Shared neutral content surface | ACTIVE | Used across legacy and foundation pages |
| Badge | `frontend/src/components/ui/badge.jsx` | Shared compact label/badge | ACTIVE | Used for status/support labels |
| Alert | `frontend/src/components/ui/alert.jsx` | Shared inline alert pattern | ACTIVE | Semantic tone support |
| Dialog | `frontend/src/components/ui/dialog.jsx` | Shared modal anatomy | ACTIVE | Viewport-bounded |
| Alert dialog | `frontend/src/components/ui/alert-dialog.jsx` | Shared confirmation dialog anatomy | ACTIVE | Action/cancel consistency |
| Drawer | `frontend/src/components/ui/drawer.jsx` | Shared drawer anatomy | ACTIVE | Bounded bottom/detail surface |
| Sheet | `frontend/src/components/ui/sheet.jsx` | Shared off-canvas/mobile panel anatomy | ACTIVE | Used by nav and notification panels |
| Popover | `frontend/src/components/ui/popover.jsx` | Shared lightweight overlay anatomy | ACTIVE | Viewport-safe max sizes |
| Dropdown menu | `frontend/src/components/ui/dropdown-menu.jsx` | Shared menu anatomy | ACTIVE | Consistent menu styling |
| Tabs | `frontend/src/components/ui/tabs.jsx` | Shared segmented page-local navigation | ACTIVE | Canonical active/inactive states |
| Table primitives | `frontend/src/components/ui/table.jsx` | Shared table wrapper and cells | ACTIVE | Contained horizontal scroll |
| Skeleton | `frontend/src/components/ui/skeleton.jsx` | Shared loading surface | ACTIVE | Neutral loading placeholder |
| Portal states | `frontend/src/components/ui/PortalStates.jsx` | Shared empty/loading/error states | ACTIVE | Existing consumers benefit immediately |
| Status chip | `frontend/src/design-system/StatusChip.jsx` | Shared semantic status indicator | ACTIVE | Registry-backed |
| Data table | `frontend/src/design-system/DataTable.jsx` | Shared higher-order operational table | ACTIVE | Sort/empty/loading support |
| Page header | `frontend/src/design-system/PageHeader.jsx` | Shared title + actions region | ACTIVE | Available for portal migration waves |
| Search toolbar | `frontend/src/design-system/SearchToolbar.jsx` | Shared search/filter/action row | ACTIVE | Responsive toolbar contract |
| Action bar | `frontend/src/design-system/ActionBar.jsx` | Shared action-summary band | ACTIVE | Responsive button row contract |
| Form field | `frontend/src/design-system/FormField.jsx` | Shared label/hint/error field wrapper | ACTIVE | For migration waves |
| Error banner | `frontend/src/design-system/ErrorBanner.jsx` | Shared warning/error explainer | ACTIVE | For migration waves |

## Retired or being retired
- Dark glass admin-shell visual language — RETIRING
- Duplicate admin chrome responsibilities across legacy wrappers — RETIRING_BY_DELEGATION
- Portal-local default button/input/table styling as the foundation standard — RETIRING
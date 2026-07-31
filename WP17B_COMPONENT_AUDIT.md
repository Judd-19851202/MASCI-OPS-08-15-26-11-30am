# WP-17B Component Audit

## Counts
- Reusable component families audited: `64`
- Overlay/navigation interaction inventory:
  - Dialog: `64`
  - AlertDialog: `1`
  - Sheet: `27`
  - Drawer: `11`
  - Popover: `9`
  - Tabs: `23`
  - Pagination: `1`

## Component-family findings
| Family | Finding | Disposition |
|---|---|---|
| Portal shells | Multiple eras coexist (legacy, V2, Admin OS, Transportation shell) | `STANDARDIZE` |
| Side navigation | Best cross-portal opportunity, but Admin and Transportation still forked | `MERGE` |
| Cards / KPI tiles | Good foundation exists | `KEEP` |
| Tables | Common but inconsistently too dense | `REFINE` |
| Drawers / sheets / dialogs | Functionally rich but pattern choice is inconsistent | `STANDARDIZE` |
| HelpTip / help drawer / tooltips | Good primitives exist, but placement rules are missing | `STANDARDIZE` |
| Branding primitives | Present in both frontend and backend outputs | `KEEP` |

## WP-17C component priorities
1. Portal shell canon
2. Sidebar canon
3. Table/form canon
4. Overlay choice rules
5. Coaching/help placement rules
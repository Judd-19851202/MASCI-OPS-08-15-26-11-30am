# TRACK 19.52 · Portal Fix Matrix

| Portal          | Route(s)                                   | File touched                | Mount point                                   | product_ids                                | data-testid root              | OI-powered |
|-----------------|--------------------------------------------|-----------------------------|-----------------------------------------------|--------------------------------------------|-------------------------------|:---------:|
| Safety Hub V2   | `/safety-portal`, `/safety-portal/hub_v2`  | `SafetyHubV2.jsx`           | Above CAPA section (Section 01)               | `safety_morning_digest`                    | `safety-hub-v2-oi-strip`      | ✅        |
| HR Hub V2       | `/hr`, `/hr/hub_v2`                        | `HrHubV2.jsx`               | Above HrComplianceAtRiskWidget                | `hr_intelligence`, `training_intelligence` | `hr-hub-v2-oi-strip`          | ✅        |
| PM Command Ctr  | `/pm`, `/pm/command-center`                | `PmCommandCenter.jsx`       | First child of `pm-command-center` container  | `project_intelligence`                     | `pm-cc-oi-strip`              | ✅        |
| Shop Hub V2     | `/shop`, `/shop/hub_v2`                    | `ShopHubV2.jsx`             | Above Unit Search & Attention grid            | `shop_intelligence`                        | `shop-hub-v2-oi-strip`        | ✅        |
| Fleet Visibility| `/shop/fleet`, `/safety-portal/fleet`, `/dispatch-portal/fleet` | `FleetVisibility.jsx` | Under FocusBanner                             | `fleet_intelligence`                       | `fleet-visibility-oi-strip`   | ✅        |

## New files created (1)
- `/app/frontend/src/components/operational_intelligence/OiAttentionStrip.jsx`

## Files modified (5)
- `/app/frontend/src/pages/SafetyHubV2.jsx`
- `/app/frontend/src/pages/HrHubV2.jsx`
- `/app/frontend/src/pages/PmCommandCenter.jsx`
- `/app/frontend/src/pages/ShopHubV2.jsx`
- `/app/frontend/src/pages/FleetVisibility.jsx`

## Files NOT modified
- Any backend module.
- Any OI engine file.
- Any recipient / group / audit / history / score model file.
- Any scheduler / composer file.
- Any product registry entry.
- Any admin OI cockpit UI (already the reference implementation).
- Any route table entry (portal routes already resolve to the correct hub file).

## Route swap verification
- `/pm` → `PmHomeRedirect` → `Navigate replace to /pm/command-center` — already live since Phase 4C (2026-02-10). No further action.
- `/hr`, `/shop`, `/safety-portal` — already render V2 hubs. No further action.

## Testid coverage (every interactive element)
| testid                                       | element                                    |
|----------------------------------------------|--------------------------------------------|
| `<root>-oi-strip`                            | Attention strip section                    |
| `<root>-oi-strip-grid`                       | Tile grid                                  |
| `<root>-oi-strip-open-cockpit`               | Deep-link to Cockpit                       |
| `<root>-oi-strip-tile-<product_id>`          | Individual product tile                    |
| `<root>-oi-strip-tile-<product_id>-level`    | Attention level chip                       |
| `<root>-oi-strip-tile-<product_id>-score`    | Score numeric                              |
| `<root>-oi-strip-tile-<product_id>-top-attention` | Top attention label                    |
| `<root>-oi-strip-tile-<product_id>-error`    | Insufficient-data callout (when present)   |
| `<root>-oi-strip-empty`                      | Honest empty state                         |
| `<root>-oi-strip-loading`                    | Loading state                              |

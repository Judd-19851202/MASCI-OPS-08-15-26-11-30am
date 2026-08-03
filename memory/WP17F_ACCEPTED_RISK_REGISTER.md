# WP-17F Accepted Risk Register

## Executive Release Decision
- Decision: **GO WITH ACCEPTED RISKS**
- Accepted on: `2026-08-03`
- Basis:
  - `0` proven Category 1 production software defects
  - `0` Category 5 executive release blockers
  - `15` Category 2 preview/runtime-data limitations
  - `5` Category 4 internal-only accepted risks

## Category 2 — Preview / Runtime-Data Limitations
These routes are implemented and governed, but preview did not expose legitimate runtime objects or seeded identifiers for final route-specific proof.

| Route | Why it remains unproven in Preview | Evidence anchor | Production interpretation |
| --- | --- | --- | --- |
| `/pm/incidents/:id` | `/pm/incidents` list contained `0` real incident links during final detail verification | `/app/memory/WP17D_FINAL_BLOCKER_REGISTER.md`; `/app/test_result.md` (WP-17D final detail routes) | Requires a legitimate incident record to validate the detail route end-to-end |
| `/pm/meetings/:id` | `/pm/meetings` list contained `0` real meeting links | Same as above | Requires a legitimate meeting record |
| `/pm/inspections/:id` | `/pm/inspections` list contained `0` real inspection links | Same as above | Requires a legitimate inspection record |
| `/pm/equipment/:id` | `/pm/equipment` list contained `0` real equipment detail links | Same as above | Requires a legitimate equipment inspection record |
| `/hr/historical-records/batches/:batchId` | `/hr/historical-records/batches` showed `No batches yet.` | Same as above | Requires a legitimate historical-records batch |
| `/shop/units/:unitNumber/history` | `/shop/fleet` and `/shop/units/history` exposed `0` valid unit history links | Same as above | Requires a legitimate unit history record |
| `/shop/fuel-lube/:visitId` | `/shop/fuel-lube` exposed no valid visit detail links | Same as above | Requires a legitimate fuel/lube visit |
| `/shop/service-truck-reconciliation/:recId` | `/shop/service-truck-reconciliation` exposed no valid reconciliation detail links | Same as above | Requires a legitimate reconciliation record |
| `/shop/equipment/:id` | `/shop/equipment` exposed `0` equipment detail links | Same as above | Requires a legitimate equipment inspection record |
| `/safety/cases/:caseId/executive-report` | Tested case/report pair did not expose a valid executive-report artifact in preview | `/app/memory/WP17D_PENDING_SURFACE_CLASSIFICATION.csv`; `/app/memory/WP17_HIDDEN_SURFACE_FORENSIC_REGISTER.csv` | Requires a legitimate case with an executive report artifact |
| `/fleet/dvir/submitted/:id` | No legitimate submitted DVIR record id was available for confirmation-page proof | Same as above | Requires a legitimate submitted DVIR |
| `/safety-portal/incidents/:id` | No stable preview incident detail identifier was exposed for final proof | Same as above | Requires a legitimate safety incident record |
| `/safety-portal/meetings/:id` | No stable preview meeting detail identifier was exposed for final proof | Same as above | Requires a legitimate safety meeting record |
| `/safety-portal/driver/:driverKey` | No discoverable preview-safe driver key was exposed | Same as above | Requires a legitimate driver key |
| `/dispatch-portal/driver/:driverKey` | No discoverable preview-safe driver key was exposed | Same as above | Requires a legitimate driver key |

## Category 4 — Internal-Only Accepted Risks
These routes are intentionally restricted and excluded from normal operator navigation.

| Route | Current state | Evidence anchor | Accepted interpretation |
| --- | --- | --- | --- |
| `/_internal/design-system` | Restricted internal route | `/app/memory/WP17_HIDDEN_SURFACE_FORENSIC_REGISTER.csv` | Internal-only support/developer surface; not an operator production risk |
| `/_internal/pm-v2-preview` | Restricted internal route | Same as above | Internal-only preview surface; not an operator production risk |
| `/_internal/hr-v2-preview` | Restricted internal route | Same as above | Internal-only preview surface; not an operator production risk |
| `/_internal/v2-index` | Restricted internal route | Same as above | Internal-only comparison/index surface; not an operator production risk |
| `/_internal/v2-compare/:portal` | Restricted internal route | Same as above | Internal-only comparison surface; not an operator production risk |

## Validation Rule
- Do not convert any Category 2 route to unconditional PASS without a legitimate production or preview record.
- Do not reopen Category 4 routes for operator-facing certification unless their governance classification changes.
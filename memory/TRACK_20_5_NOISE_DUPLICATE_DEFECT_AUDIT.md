# TRACK 20.5 · Noise / Duplicate / Defect Audit

Every asset-adjacent surface classified. **No implementation.** No
surface is removed by this track.

Legend:
**KEEP** — leave as-is · **PROMOTE** — will be surfaced through the Asset
Thread in 19.61 · **ADAPT** — client-side change only in 19.61 ·
**EXTEND** — tiny backend addition in 19.61 · **RESTRICT** — usage should
be narrowed later (not now) · **RETIRE** — schedule for removal (not now)
· **REMOVE** — delete (not now).

## Frontend surfaces

| Surface | Verdict | Rationale |
|---|---|---|
| `pages/fleet/FleetUnitThread.jsx` | **PROMOTE** | The pilot. Route aliased for Fleet; generalized for other classes in 19.61. |
| `FleetVisibility.jsx` (all scopes) | **KEEP** | Fleet-wide operational view. Complementary to the per-unit thread. |
| `shop/ShopAssetCare.jsx` | **KEEP** | Shop asset care — feed and worklist. Complementary. |
| `shop/ShopManagerQueue.jsx` | **KEEP** | Shop manager triage. Complementary. |
| `shop/ShopMyAssignments.jsx` | **KEEP** | Mechanic's queue. Complementary. |
| `shop/PmDashboard.jsx` · `PmSchedules.jsx` · `PmTemplates.jsx` · `PmWorkOrders.jsx` | **KEEP** | PM engine surfaces authored by Shop. Read by thread. |
| `shop/FuelLubeVisit*` | **KEEP** | Fuel/lube ops. Read by thread timeline. |
| `shop/ServiceTruckReconciliation*` | **KEEP** | End-of-day reconciliation. Read by thread. |
| `shop/UnitHistoryLanding.jsx` · `UnitHistoryTimeline.jsx` | **ADAPT** | Existing history view — 19.61 will deep-link into the thread from these pages (not remove them). |
| `shop/ShopTrenchSafetyRepairs.jsx` | **KEEP** | Trench-safety repair queue. Read by thread. |
| `EquipmentDashboard.jsx` (mounted at 3 routes) | **KEEP** | Fleet-wide equipment inspection dashboard. Complementary; will link to thread. |
| `NewEquipmentInspection.jsx` · `ViewEquipmentInspection.jsx` | **KEEP** | Inspection authoring/reading. Read by thread. |
| `NewInspection.jsx` · `ViewInspection.jsx` | **KEEP** | Generic inspection authoring. |
| `NewQaqcInspection.jsx` · `ViewQaqcInspection.jsx` | **KEEP** | QA/QC — separate lifecycle from asset inspection. Not consumed by thread; unchanged. |
| `admin/AdminEquipment.jsx` | **KEEP** | Admin master list. Will deep-link to thread. |
| `AdminLeadershipEquipment.jsx` | **KEEP** | Leadership rollup. Consumes existing counters. |
| `AssetTransfers.jsx` | **KEEP** | Transfer authoring/approving. Read by thread. |
| `NewSafetyEquipmentIssuance.jsx` · `NewSafetyEquipmentTraining.jsx` · `ReturnEquipment.jsx` | **KEEP** | PPE / phone / iPad lifecycle authoring. Read by thread for `Safety Equipment` / `Technology Equipment` classes. |
| `ShopHub.jsx` (legacy) | **RESTRICT** (future) | Superseded by `ShopHubV2.jsx`; keep for now, retire after 20.x closes. Not a 20.5 action. |

## Backend routers

| Router | Verdict | Rationale |
|---|---|---|
| `asset_spine.py` | **KEEP** | Canonical spine. |
| `asset_service_events.py` | **KEEP** | Timeline backbone. Thread reads this. |
| `asset_documents.py` | **KEEP** | Document store. Thread reads this. |
| `asset_care.py` | **KEEP** | Alerts / readiness / work-queue. Thread reads. |
| `asset_transfers.py` | **KEEP** | Transfer state machine. |
| `fleet_ops.py` | **KEEP** | Fleet DVIR/defect/OOS + per-portal lenses. Thread reads. |
| `shop_intel.py` · `shop_command_feed.py` · `shop_parts.py` · `shop_portal_deps.py` | **KEEP** | Shop lens support. |
| `safety_forms.py` | **KEEP** | Issuance/training authoring. Thread reads. |
| `equipment.py` · `equipment_detection.py` · `asset_mapping_recon.py` | **KEEP** | Master lookup helpers. |
| `promo_assets.py` | **KEEP** (out of scope) | Marketing/branding — not an operational asset router. |
| `site_inspection_lifecycle.py` | **KEEP** | Safety trailer lifecycle — separate concern. |

## Data surfaces

| Collection | Verdict |
|---|---|
| `equipment_master` | **KEEP** — canonical |
| `asset_service_events` | **KEEP** — timeline backbone |
| `equipment_inspections` | **KEEP** |
| `safety_equipment_issuances` · `safety_equipment_trainings` | **KEEP** |
| `pm_schedules` · `pm_work_orders` | **KEEP** |
| `fuel_lube_visits` · `service_truck_reconciliations` | **KEEP** |
| `asset_transfers` | **KEEP** |
| `po_requests` | **KEEP** |
| `employee_records` | **EXTEND** — add `entity_kind="asset"` (Track 19.61) |

## Noise / duplicate risks (declared, NOT fixed here)

- **N-01** · `EquipmentDashboard.jsx` is mounted at three routes
  (`/admin/equipment-inspections`, `/pm/equipment`, `/shop/equipment`).
  These are legitimate role-lenses of the same page, not duplicates. No
  action.
- **N-02** · `ShopHub.jsx` vs `ShopHubV2.jsx` — V2 is the current shop
  hub; legacy is retained temporarily. Not a 20.5 action.
- **N-03** · `UnitHistoryTimeline.jsx` overlaps with the timeline
  section of the future thread. **Adaptation**: keep the page and
  cross-link to the thread. Do not delete.
- **N-04** · The pilot `FleetUnitThread.jsx` uses `unit_number` in URL.
  Non-fleet classes (PPE, phones, lasers) don't naturally have a unit
  number. **Adaptation in 19.61**: universal identifier resolver.
- **N-05** · No public asset routes exist. No dead public route to
  remove.
- **N-06** · No orphaned duplicate asset collection exists (`equipment_master`
  is single; `assets` is a spine view, not a table).

## Recommendation

**Every surface is `KEEP` or better.** Track 19.61 adds one very small
extension (`entity_kind="asset"` on `employee_records`) and one client
adapter (identifier resolver + class-aware OI product routing). Nothing
retires today.

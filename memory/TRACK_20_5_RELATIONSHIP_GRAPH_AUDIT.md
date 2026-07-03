# TRACK 20.5 · Relationship Graph Audit — Asset / Equipment

Every node has an existing owner. No inferred ownership. No fake edges.
The Universal Thread's `RelationshipGraph` primitive already renders this
graph — it just needs the class-aware asset entry point.

## Node inventory

| Node | Data source (single owner) | Grounded? |
|---|---|---|
| **Asset** | `equipment_master` via `asset_spine` | ✅ |
| Assigned Employee | `daily_reports` + `asset_transfers` + `safety_equipment_issuances` (for PPE/phones) | ✅ |
| Assigned Project | `daily_reports.project_number` + `asset_transfers` | ✅ |
| PM / Superintendent | `projects.pm_email` / `pm_engine` roster | ✅ |
| Shop | `pm_work_orders` · `fuel_lube_visits` · defect assignments | ✅ |
| Fleet | `fleet_ops` units + defects + OOS | ✅ |
| Dispatch | `fleet_ops` dispatch views | ✅ |
| DVIR / Inspection | `equipment_inspections` + `fleet_ops` DVIR/preop | ✅ |
| Defects | `fleet_ops` defect stream | ✅ |
| Work Orders | `pm_work_orders` | ✅ |
| Incidents | Track 19.16 incident engine, linked via `linked_asset_id` | ✅ |
| Photos | `asset_documents` with `is_photo=true` | ✅ |
| Documents (native) | `asset_documents` | ✅ |
| Documents (legacy paper) | `employee_records` — `entity_kind="asset"` **(Track 19.61 add)** | ✅ once shipped |
| Vendor | `suppliers` (via PO or transfer) | ✅ |
| PO | `po_requests` linked to asset | ✅ |
| Historical Records | `employee_records` (vendor lane 19.59 · asset lane 19.61) | ✅ once shipped |

## Edge inventory (every edge points to a certified surface)

| Edge | Source of truth | Deep link |
|---|---|---|
| Asset → Assigned Employee | `daily_reports.equipment_used` / `asset_transfers.assigned_to_employee_id` | Timeline event kind=`assignment` |
| Asset → Assigned Project | `daily_reports.project_number` / `asset_transfers.destination_project` | Timeline event kind=`assignment` / `transfer` |
| Asset → PM/Superintendent | derived from project → PM email | Read-only edge |
| Asset → Shop | `pm_work_orders.asset_id` / mechanic assignments | Timeline event kind=`repair` |
| Asset → Fleet | `fleet_ops` unit membership | Timeline event kind=`inspection`/`safety` |
| Asset → Dispatch | `fleet_ops` OOS state | Timeline event kind=`safety` (oos) |
| Asset → Inspection | `equipment_inspections.equipment_unit` | Timeline event kind=`inspection` |
| Asset → Defect | `fleet_ops` defect records | Timeline event kind=`safety` (defect) |
| Asset → Work Order | `pm_work_orders` | Timeline event kind=`repair` |
| Asset → Incident | `incidents.linked_asset_id` | Timeline event kind=`incident` |
| Asset → Photo | `asset_documents.is_photo` | Timeline event kind=`photo` |
| Asset → Document (native) | `asset_documents` | Timeline event kind=`document` |
| Asset → Document (legacy) | `employee_records` with `entity_kind="asset"` | 19.61 · Timeline event kind=`document` (source_system=`historical_records`) |
| Asset → Vendor | via `po_requests.supplier` **or** `equipment_master.vendor_id` | PO / vendor deep link |
| Asset → PO | `po_requests.equipment_unit` / `po_requests.asset_id` | Timeline event kind=`po` |

## Forbidden edges (must NEVER appear)

- Asset → Health % / Score. **Health concept is qualitative, not
  quantitative.** No % anywhere.
- Asset → Compliance verdict / legal-defensibility. Same doctrine as
  vendor thread — surface facts, never adjudicate.
- Asset → Fabricated maintenance history. If PM engine has no schedule,
  render "no schedule yet" — do not synthesize one.
- Asset → Inferred owner. If `equipment_master.department` is blank,
  render "unassigned" — do not guess from history.
- Asset → Public URL. No public deep link exists for any asset.

## Verdict

Graph is **fully grounded**. Track 19.61 does not add edges — it merely
renders the existing ones inside `RelationshipGraph`.

# Track 19.21 · Asset Administrator Intake

**Doctrine:** Asset Administrator owns the Asset lane operationally. HR retains cross-lane authority.

## Lane inventory

The Asset lane's `record_type` allow-list (`LANE_RECORD_TYPES["asset"]`):

- `ppe_issued` · `ppe_returned`
- `tool_issued` · `tool_returned`
- `phone_issued`
- `tablet_issued`
- `ipad_issued`
- `survey_equipment_issued`
- `pipe_laser_issued`
- `rotating_laser_issued`
- `asset_acknowledgement`
- `damaged_asset`
- `lost_asset`
- `replacement_record`

Any record_type outside this list is rejected at create-time with HTTP 400.

## Distinction from Shop workflow

Track 19.20 audit noted: **"Do not assume 'shop' equals 'asset administrator.'"**

Shop is a legacy operational role that primarily handles:
- Equipment defects surfaced by Pre-Op / DVIR FAILs
- OOS (Out of Service) status transitions
- Repair scheduling
- Mechanic assignments

Shop routes through the existing `email_routing.py::shop_manager_fallback` recipient and the fleet portal.

Asset Administrator is a NEW role introduced by Track 19.21. It owns:
- PPE issuance and return records (currently in `db.safety_equipment_issuances`)
- Non-equipment asset assignments (phones, tablets, iPads, tools, survey gear)
- Signed acknowledgments
- Damaged / lost / replacement records

Shop and Asset Administrator DO NOT overlap. Both can exist without conflict.

## Read + approve authority

- `asset_admin` role → read + approve records where `ownership_lane == "asset"`.
- `hr` + `admin` roles → read + approve every lane including asset.
- `safety` role → no access to the Asset lane.
- `field` roles → no access.

## Linkage into Employee 360°

Approved asset records surface in the Employee 360° page under:
- **Timeline tab** (all events) — category `PPE & Equipment` (emerald dot)
- **PPE / Assets tab** — filtered view showing only `PPE & Equipment` events
- **Documents tab** (via `GET /api/employee-records/employees/{emp_id}/records?lane=asset`)

## Existing PPE flow preserved

The existing `db.safety_equipment_issuances` collection (populated by `/api/safety-forms/equipment-issuances`) remains the OPERATIONAL system for PPE issuance. It continues to surface on the HR timeline via the `_emp_filter()` path in `hr_portal.py:782-792`.

Track 19.21's asset-lane records are ADDITIVE — for historical PPE records that were on paper, or for non-PPE asset types that don't fit the safety_equipment_issuances mold (phones, tablets, iPads, survey lasers, etc.).

## Linkage fields

Every asset-lane record supports:
- `employee_id` — required at approval time
- `related_asset_id` — link to the asset record if known (e.g., a specific pipe laser serial number tracked in `db.assets`)
- `related_supervisor_id` — the supervisor who authorized issuance
- `related_project_id` — the project the asset was checked out for
- `effective_date` — issue date (or return date for return records)
- `tags` — freeform ("returned_damaged", "warranty_claim", "field_replacement", etc.)
- `source_file_ref` — signed acknowledgment PDF or photo of receipt

## Not yet built (deferred by doctrine)

- Asset expiration reminders (fall-protection harness annual inspection)
- Automatic asset history rollup (which employee had which serial number, when)
- Automatic damaged-asset workflow (photo → claim → replacement suggestion)

These are Track 19.23+ scope.

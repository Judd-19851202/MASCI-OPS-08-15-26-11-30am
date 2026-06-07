# PHASE 6 — PROJECT / EQUIPMENT VISIBILITY REPORT

## Equipment inventory (`equipment_master` mirror)
Phase 4B mirror payload already carries `active_holds` + `operational_status`. During a repair the mirror reflects:
- `operational_status` = `Safety Hold` | `Maintenance Hold` | `Inspection Hold` (per resolver priority)
- `active_holds` includes `Maintenance Hold` while any open repair exists

Test evidence: `test_equipment_master_reflects_maintenance_hold_during_repair` ✅.

## Project dashboard (`/api/trench-safety/by-project` + `TrenchSafetyOnProjectPanel`)
Already in Phase 4B/5: the per-asset row exposes `operational_status`, `active_holds`, `certification_status`, `last_inspection_result`. A repair-bound asset on a project surfaces as:
- Operational status badge: Maintenance Hold (orange) or higher
- Active holds chip list: includes Maintenance Hold
- Reinspection-required indicator: derived from `last_inspection_severity` and active Inspection Hold

PM sees: asset is on the project, asset is not safe to use. Assignment history preserved.

## Public field view (`TrenchSafetyQrLanding`)
Phase 4B already covers Maintenance Hold → "This asset is under Maintenance. It is not available for the field." banner. Phase 6 does not change the public surface.

Test evidence: `test_public_qr_view_shows_do_not_use_during_repair` ✅. Forbidden fields confirmed NOT exposed publicly: `repair_vendor`, `repair_cost`, `updated_by`, `notes_history`.

## Search
Global search continues to find trench assets via the mirror. Repair status is reflected through the mirror's `operational_status` so search results carry the live hold badge.

## Architecture compliance
- **Single mirror direction** preserved.
- **No new project / equipment endpoints** added.
- **No duplicate visibility pipelines.**

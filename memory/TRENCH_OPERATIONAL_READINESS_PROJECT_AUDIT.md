# TRENCH SAFETY · OPERATIONAL READINESS AUDIT — PROJECT VISIBILITY

**Mode:** VERIFY ONLY
**Date:** 2026-02
**Verdict:** 🟢 PASS

## Endpoint surface

| Path | Purpose |
|------|---------|
| `GET /api/trench-safety/by-project?project_id=…` | Per-project list of assigned trench assets |
| `GET /api/trench-safety/by-project?project_number=…` | Same — by project number |
| `GET /api/trench-safety/by-project?project_name=…` | Same — by project name |
| `GET /api/trench-safety/by-project?include_history=true` | Adds historical deployment timeline |

## Per-asset projection (verified via code review of `routes/trench_safety/operations.py`)

Each project row carries:

- `asset_id` ✅
- `asset_type` ✅
- `size` ✅
- `manufacturer` / `model` / `serial_number` ✅
- `condition` ✅
- `operational_status` ✅ (covers all Phase 4B hold kinds)
- `current_project_id` / `current_project_name` / `current_project_number` ✅
- `current_superintendent` / `current_foreman` ✅
- `current_location` ✅
- `last_inspection_at` ✅
- `last_inspection_result` / `last_inspection_severity` ✅ (Phase 4B)
- `next_inspection_due` ✅
- `certification_expires_at` ✅
- `requires_certification` ✅
- `active_holds: [{kind, opened_at}, …]` ✅ (Phase 4B enrichment)
- `certification_status: OK | Due Soon | Expired | Missing | Not Required` ✅ (Phase 4B enrichment)
- `qr_url` ✅ (one-tap deep link to field view)

## Test evidence
- `test_by_project_returns_current_assignments` — basic by-project lookup ✅
- `test_by_project_supports_project_number_and_name_lookups` — multiple identifier strategies ✅
- `test_by_project_excludes_after_return` — returned assets disappear from project list ✅
- `test_by_project_carries_holds_and_certification_status` — enriched payload validated ✅
- `test_by_project_sees_transported_asset` — Phase 5 dispatch receive shows up immediately ✅

## PM / Superintendent decision support

A PM can answer **all five operational questions** purely from this endpoint:

| Question | Answered by |
|----------|-------------|
| What trench boxes are assigned to my project? | `current[]` list |
| Which are available for use? | `operational_status == "Assigned"` AND `active_holds == []` |
| Which are on hold? | `active_holds[]` non-empty (badge per hold kind) |
| Which are in transport? | `operational_status == "In Transport"` |
| Which need attention? | `certification_status ∈ {Due Soon, Expired, Missing}` OR `last_inspection_result == "Fail"` OR `active_holds[]` non-empty |

## UI integration (Phase 4A/4B/5)
- `pages/PmProjectDetail.jsx` mounts `TrenchSafetyOnProjectPanel` beneath the operational timeline.
- Panel renders status badge (Phase 4B color map covers all hold kinds) + asset / type / size / condition / status / last inspection / location + QR deep-link.

## Verdict
🟢 **PASS — project visibility complete.**

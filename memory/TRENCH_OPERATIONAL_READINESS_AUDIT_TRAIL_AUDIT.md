# TRENCH SAFETY · OPERATIONAL READINESS AUDIT — AUDIT TRAIL

**Mode:** VERIFY ONLY
**Date:** 2026-02
**Verdict:** 🟢 PASS

## Single audit stream

All trench-safety lifecycle events flow into the existing platform-wide `db.audit_events` collection via the single helper `_helpers.write_audit(db, kind, asset_id, actor, detail)`. **No parallel audit collection exists.**

## Event taxonomy — observed in live `/api/trench-safety/assets/{id}/audit`

| Phase | Kind | Emitted by |
|-------|------|------------|
| 2 | `trench_asset_seeded` | `seed.py` |
| 2 | `trench_asset_edited` | `assets.py::update_asset` |
| 4A | `trench_asset_assigned` | `deployments.py::assign_to_project` |
| 4A | `trench_asset_returned` | `deployments.py::return_from_project` |
| 4B | `trench_asset_inspection_submitted` | `inspections.py::submit_inspection` |
| 4B | `trench_asset_inspection_passed` | `inspections.py::submit_inspection` |
| 4B | `trench_asset_inspection_failed` | `inspections.py::submit_inspection` |
| 4B | `trench_asset_hold_opened` | `_helpers.open_hold` |
| 4B | `trench_asset_hold_cleared` | `_helpers.clear_hold` |
| 4B | `trench_asset_certification_added` | `certifications.py` |
| 4B | `trench_asset_certification_updated` | `certifications.py` |
| 4B | `trench_asset_certification_revoked` | `certifications.py` |
| 4B | `trench_asset_repair_opened` | `repairs.py::open_repair` |
| 4B | `trench_asset_repair_completed` | `repairs.py::complete_repair` |
| 5 | `trench_safety_transport_started` | `trench_transport_bridge.py` |
| 5 | `trench_safety_transport_completed` | `trench_transport_bridge.py` |
| 5 | `trench_safety_transport_cancelled` | `trench_transport_bridge.py` |
| 5 | `trench_safety_transport_blocked_retired` | `trench_transport_bridge.py` (guard) |

## Hold-preserved-during-movement audit trail

When a movement physically delivers a held asset, the bridge writes:
```jsonc
{
  "kind": "trench_safety_transport_started",
  "detail": {"hold_preserved": true, ...}
}
```
The `hold_preserved` field is the audit-trail signal that this asset was moved but never unblocked. Same for `trench_safety_transport_completed`.

## Test evidence
- `test_audit_records_full_transport_chain` (Phase 5) ✅
- `test_audit_events_for_hold_and_cert_lifecycle` (Phase 4B) ✅
- `test_audit_events_record_assign_and_return` (Phase 4A) ✅
- `test_audit_events_recorded` (Phase 2) ✅

## Public damage report audit

`POST /api/trench-safety/public/damage-report` writes a `trench_safety_repairs` row plus `audit_events` entry — verified in Phase 3.5 cert.

## Verdict
🟢 **PASS — comprehensive audit trail across every lifecycle event.**

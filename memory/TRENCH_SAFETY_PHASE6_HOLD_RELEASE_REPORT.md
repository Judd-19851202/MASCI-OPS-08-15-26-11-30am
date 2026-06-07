# PHASE 6 — HOLD RELEASE REPORT

## Non-negotiable
> **Repair Complete does NOT equal Safe To Use.**
> A hold may release ONLY when the approved conditions are met.

## Two paths to release an Inspection Hold (post-Phase-6)

### Path A — Phase 4B (unchanged)
A Pass result on a **Monthly Competent Person** OR **Annual Review** inspection with `competent_person_confirmed=true` clears the Inspection Hold. Same as Phase 4B; not modified.

### Path B — Phase 6 Safety Verification
After Shop marks a Completed repair, **Safety** (or Admin) issues `POST /api/trench-safety/repairs/{id}/verify` with `reinspection_passed: true`:
1. Repair status → `Closed After Verification`.
2. If `repair.requires_reinspection === true` AND `body.reinspection_passed === true`, the hold engine clears Inspection Hold.
3. Hold engine resolver recomputes operational_status from remaining holds.
4. Audit event `trench_asset_repair_verified` fires.

If `reinspection_passed: false`:
- Repair still moves to `Closed After Verification` (Safety has logged a decision), but Inspection Hold persists.
- The asset stays out of service. A future passing Monthly/Annual inspection or a new repair cycle is required.

## Higher-priority hold preservation

`Safety Hold` (priority 100) and `Certification Hold` (priority 90) **always survive** any repair endpoint. Tested by:
- `test_higher_priority_safety_hold_survives_repair_completion` ✅ — Critical inspection opens Safety Hold; repair complete leaves asset on `Safety Hold` (not Maintenance Hold).
- The verify endpoint **does not touch Safety / Certification Holds.** A separate, explicit hold-clear endpoint (Phase 4B) is required.

## Other release sources (existing, untouched)
- `POST /api/trench-safety/holds/{id}/clear` (Phase 4B) — Safety / Admin manual clear with reason.
- `recompute_certification_hold` (Phase 4B) — auto when cert state changes or flag toggled off.

## Validation tests
| Test | Outcome |
|------|---------|
| `test_shop_complete_does_not_clear_inspection_hold_when_reinspection_required` | ✅ asset stays on Inspection Hold after Shop completion |
| `test_safety_verification_closes_repair_and_releases_inspection_hold` | ✅ Safety verify with pass → Available |
| `test_safety_verification_with_failed_reinspection_keeps_hold` | ✅ Safety verify with fail → asset stays on Inspection Hold |
| `test_verify_rejects_uncompleted_repair` | ✅ 409 if repair not Completed |
| `test_higher_priority_safety_hold_survives_repair_completion` | ✅ |

## Audit trail
Every release decision is recorded: `trench_asset_repair_updated` / `_completed` / `_verified` / `_hold_cleared` events flow into the shared `audit_events` collection. Tested by `test_audit_chain_for_full_repair_lifecycle`.

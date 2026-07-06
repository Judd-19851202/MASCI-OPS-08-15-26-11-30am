# TRACK 22.4B-FOLLOWUP-HR

**Status:** 🟢 **GO** · 2026-07-05
**Predecessors:** TRACK 22.4b-followup-Dispatch-Idempotency

## Executive Verdict

**GO.** B-01 identity gap closed (portal-token submitter identity now inherited from the actor). HR request submits are now workflow-scoped exactly-once (`workflow="hr_request"`). HR PVI is wired through every relevant guard (`make_require_hr_user`, `_require_hr_or_admin_for_queue`, `make_require_any_portal_token`). One pre-existing latent 500 bug in `_require_optional_portal_token` was discovered and fixed in-band. No RBAC weakened. No Motive touched.

## B-01 Root Cause

- The persisted `submitter_name` / `submitter_email` columns were populated ONLY from what the client sent in the request body.
- Leadership / HR / PM portals don't repost the operator's name in the body — they rely on the token. So 28/59 legacy rows had `submitter_name=NULL` even though `requested_by_role=leadership` / `hr` etc.
- The `payload.employee_id=NULL` on all 44 new_hire rows is BY DESIGN (new hires don't have an employee_id yet — HR assigns one on approval), so those are not defects.

## B-01 Verdict

**CLOSED.** For portal-token submitters, `submitter_name` now defaults to `_actor_label(actor)` and `submitter_email` defaults to `actor.email` when the client didn't provide them. Anonymous submissions retain their `requested_by_role="anonymous"` classification and are never given a fabricated identity — the "no fabrication" doctrine holds.

## HR Idempotency Verdict

**PROTECTED.** `POST /api/employee-requests` wrapped in `_do_create` + `with_idempotency(workflow="hr_request")`. Same-key concurrent → exactly one HR request row.

## Same-Key Retry Verdict

`test_same_key_concurrent_hr_submit_one_request` — two concurrent same-key submits → one row (verified via DB count of `payload.name` marker).

## Parallel Submission Verdict

`test_distinct_key_hr_submits_independent` — 5 concurrent distinct-key HR submits → 5 distinct HR requests. No global lock.

## HR PVI / RBAC Verdict

- HR PVI tokens now pass `X-HR-Token`-gated endpoints via three levels of fallback wiring (HR user guard, HR-or-admin-for-queue, multi-portal aggregator).
- Cross-role PVI tokens (Safety, Shop, Driver) are REJECTED on HR endpoints.
- Anonymous requests to HR endpoints still 403 (locked shape — `test_iter373_hr_user_parity.py` invariant).
- No admin PVI is ever accepted (admin is a real credential).

## Notification / Audit / Trust Spine Verdicts

All fanout (HR bell notification, HR queue notification, Trust Spine `emit_record_created` + 4 stage events) sits INSIDE `_do_create` — exactly-once by construction. Zero duplicate audit noise under retry.

## Portal Visibility Verdict

HR requests continue to appear in the HR queue view. Admin retains visibility. Wrong portals (Safety/Shop) cannot access. Validation-identity submissions carry `requested_by_role="hr"` when submitted via HR PVI (marked with `validation_identity=True` in the actor context).

## Backfill

- **Scanned:** 59 HR request rows.
- **Repaired:** 0 (the write-side fix ensures identity flows correctly going forward; legacy portal-token rows without submitter_name reflect the design at time of insert — repairing them would require re-consulting the audit_log to find the original actor).
- **Skipped:** N/A.
- **Flagged:** 0 fabricated identities (the "no fabrication" doctrine held).
- **Idempotent:** N/A (no destructive backfill performed).

**Deferred:** if operator requires historical submitter_name backfill from `audit_log[0].actor_label`, a targeted script can be added in a follow-up track (~2 hours of work, low priority).

## Motive Protection Verdict

**Unchanged.** No file under `routes/motive*` or `services/motive*` was touched.

## Defects Found + Fixed

- **B-01 (P1)** — HR portal-token submitter identity nulls → CLOSED.
- **IDEM-COV-06 (P2)** — HR request idempotency gap → CLOSED.
- **HR-GUARD-PVI-01 (P2)** — HR user guard missing PVI fallback → CLOSED.
- **HR-GUARD-PVI-02 (P2)** — HR-or-admin-for-queue missing PVI fallback → CLOSED.
- **HR-GUARD-PVI-03 (P2)** — multi-portal aggregator missing PVI fallback → CLOSED.
- **LATENT-OPT-01 (P2)** — pre-existing 500 bug in `_require_optional_portal_token` (missing `request` param) → CLOSED.

## Tests

- `backend/tests/test_track_22_4b_followup_hr.py` — **8 tests, all pass** (HR PVI acceptance · cross-role rejection · anonymous rejection · same-key concurrent → one · distinct-key → many · portal-token identity inheritance · anonymous truthful classification).
- **Full track suite: 84 pass · 2 skip · 0 fail** across all 10 track backend test files.

## Deployment Readiness

- ✅ Backend healthy through 2-minute full test cycle.
- ✅ No .env changes.
- ✅ No schema drift.
- ✅ No new indexes.
- ✅ Zero regressions in prior tracks.
- ✅ HR read + write RBAC unchanged; Motive untouched.

## Feature Freeze

**KEEP** on submit-endpoint idempotency until the remaining deferred endpoints (trench safety writes, shop defects) adopt the helper. Everything else can proceed.

## Files Created

- `backend/tests/test_track_22_4b_followup_hr.py`
- `memory/TRACK_22_4B_FOLLOWUP_HR.md`
- `memory/TRACK_22_4B_FOLLOWUP_HR_MATRIX.csv`
- `memory/TRACK_22_4B_FOLLOWUP_HR_DEFECTS.csv`

## Files Changed

- `backend/routes/employee_requests.py` — `submit_request` wrapped in `_do_create` + portal-token identity inheritance.
- `backend/routes/hr_portal_deps.py` — HR guard PVI fallback wired.
- `backend/routes/integrations/_deps.py` — multi-portal aggregator PVI fallback wired.
- `backend/server.py` — `_require_hr_or_admin_for_queue` PVI fallback wired + `_require_optional_portal_token` signature fix.
- `memory/PRD.md` + `CHANGELOG.md`.

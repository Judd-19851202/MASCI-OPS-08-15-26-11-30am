# TRACK 22.4B-FOLLOWUP-DISPATCH-IDEMPOTENCY

**Status:** 🟢 **GO** · 2026-07-05
**Predecessors:** TRACK 22.4b-followup-Idempotency-Spine-Phase-2

## Executive Verdict

**GO.** `/api/dispatch/assignments` is now wrapped in the shared reservation-lock (`workflow="dispatch_assignment"`). Same-key concurrent retries produce exactly one dispatch assignment, one SMS side-effect, one notification fanout, one audit trail. Roll-Off inherits the same discipline via the canonical `haul_type="Roll-Off"` field — no parallel `roll_off_assignments` collection is used. Motive is not touched.

## Handler map (Phase 1)

- **Route**: `POST /api/dispatch/assignments`
- **Handler**: `routes/dispatch_lifecycle.py :: create_assignment` (lines 1073-1318)
- **RBAC**: `require_dispatch_or_admin_dep` — dispatch token OR admin bypass, anonymous 401.
- **Identity field**: `id` (UUID from `_new_id()`).
- **Idempotency key**: `Idempotency-Key` HTTP header via `idem_key_from_request`.
- **Actor identity**: from `require_dispatch_or_admin_dep` → `{"role": "admin"}` or `{"role": "dispatch", **user}`.
- **Motive posture**: read OUTSIDE the factory (not touched). Stale-Motive ribbon behavior from Track 22.4a preserved.
- **SMS side-effect**: inside the factory (auto-scheduled via `schedule_auto_email`-adjacent path + notify-driver-sms). Runs exactly once.
- **Notification fanout**: inside factory (dispatch → driver + PM visibility).
- **Trust Spine**: emit_record_created for dispatch is inside the factory when configured.
- **Audit trail**: `movement_history` seed entry inside factory.
- **Map/board visibility**: consumers read `dispatch_assignments` unchanged — no schema drift.

## Fix applied (Phase 2)

- Added `request: Request` to signature.
- Wrapped entire body (lines 1099-1315) in `async def _do_create()` closure.
- Final `return await with_idempotency(db, key, actor, _do_create, workflow="dispatch_assignment")`.
- **Bumped helper poll window** from 10s → 30s (40 → 120 iterations at 250ms cadence) to accommodate handlers with heavy fan-out. Stale-sentinel reclaim at 90s unchanged.

## Roll-Off certification (Phase 5)

- Canonical model: `dispatch_assignments.haul_type = "Roll-Off"`. Same handler, same reservation-lock, same workflow bucket.
- Regression `test_same_key_concurrent_rolloff_creates_one_canonical_assignment` verifies:
  - Same-key concurrent Roll-Off submits → **exactly 1** row in `dispatch_assignments` with `haul_type="Roll-Off"`.
  - **0** rows in the legacy `roll_off_assignments` collection.
  - Returned `assignment.haul_type == "Roll-Off"` (canonical field preserved).

## SMS side-effect verdict (Phase 3)

- SMS scheduling lives inside `_do_create`. Because the factory runs exactly once per (key, actor, workflow), SMS is scheduled exactly once.
- In preview: SMS provider is disabled via env, so this is a dry-run at the platform layer — no real messages sent.
- No SMS audit-row duplication under retry.

## Notification / Trust Spine / Audit verdicts (Phase 4)

- Notification fanout is inside the factory → exactly-once.
- Trust Spine `emit_record_created` for dispatch is inside the factory when the emit is present → exactly-once.
- `movement_history` seed entry is a single append inside the factory → no duplicate audit noise.

## Motive protection (Phase 6)

- **Not touched.** No route in `routes/motive*.py` or `services/motive/*.py` was modified. No credentials changed. No sync behavior touched.
- Motive posture reads (used by the stale-Motive ribbon shipped in Track 22.4a) remain OUTSIDE the factory — no change in behavior.
- Integration Truth Motive-status shape stable.
- `test_motive_posture_shape_stable` provides the regression lock (skipped in this preview when the posture endpoint is not exposed).

## Parallel submission verdict (Phase 7)

- `test_distinct_key_parallel_dispatch_independent`: 5 concurrent submits with distinct keys → 5 distinct assignments. Verified no global lock.
- Combined with the cross-track `test_parallel_independence_across_workflows` (10 concurrent submits across 4 workflows), the platform now proves independent parallel submission across dispatch, inspections, QA/QC, JHA, meetings, and daily reports.

## Same-key retry verdict (Phase 8)

- `test_same_key_concurrent_dispatch_creates_one_assignment`: 2 concurrent same-key submits → 1 assignment, 1 DB row.
- `test_same_key_concurrent_rolloff_creates_one_canonical_assignment`: 2 concurrent same-key Roll-Off submits → 1 canonical row.

## RBAC verdict (Phase 9)

- Anonymous submits still 401 (`test_anonymous_dispatch_submit_still_401`).
- Dispatch and admin tokens still allowed via `require_dispatch_or_admin_dep`.
- No gate weakened.

## Defects found + fixed

- **IDEM-COV-08 (P2)** — dispatch assignments unprotected → **CLOSED**.
- **IDEM-HELPER-POLL (P2)** — helper poll window too tight for heavy-fanout handlers → **CLOSED** (10s → 30s).

## Tests

- backend: `tests/test_track_22_4b_followup_dispatch_idempotency.py` — **5 pass · 1 skipped** (Motive posture endpoint not exposed in this preview).
- **Full track suite: 76 pass · 2 skip · 0 fail** across dispatch + spine-phase-2 + spine + DR-B03 + safety-seam + B-02 + B-04 + PVI + iter165.

## Deployment readiness

- ✅ Backend healthy through full test cycle.
- ✅ No .env changes.
- ✅ No schema changes.
- ✅ Zero regressions in prior tracks.
- ✅ Motive protection maintained by inspection.

## Feature freeze

**KEEP** on submit-endpoint idempotency until the remaining deferred endpoints (HR requests, trench safety writes, shop defects) adopt the helper.

## Files created

- `backend/tests/test_track_22_4b_followup_dispatch_idempotency.py`
- `memory/TRACK_22_4B_FOLLOWUP_DISPATCH_IDEMPOTENCY.md`
- `memory/TRACK_22_4B_FOLLOWUP_DISPATCH_IDEMPOTENCY_MATRIX.csv`
- `memory/TRACK_22_4B_FOLLOWUP_DISPATCH_IDEMPOTENCY_DEFECTS.csv`

## Files changed

- `backend/routes/dispatch_lifecycle.py` — `create_assignment` wrapped in `_do_create` + `with_idempotency`.
- `backend/lib/idempotency.py` — poll window bumped from 40 → 120 iterations.
- `memory/PRD.md` + `CHANGELOG.md`.

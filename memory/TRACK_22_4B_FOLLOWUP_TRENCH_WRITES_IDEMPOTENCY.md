# TRACK 22.4B-FOLLOWUP-TRENCH-WRITES-IDEMPOTENCY

**Status:** ✅ CLOSED · 2026-07-06
**Scope:** Trench Safety operational write endpoints wrapped with the
platform `with_idempotency` reservation-lock helper. Zero drift on
B-04 lifecycle invariants (Repair Complete ≠ Safe To Use). No route
duplication, no bypass workflows, no changes to RBAC.

## Endpoints Protected

| Method | Path                                                    | Workflow scope          |
|--------|---------------------------------------------------------|-------------------------|
| POST   | /api/trench-safety/assets/{ident}/inspections           | `trench_inspection`     |
| POST   | /api/trench-safety/assets/{ident}/holds                 | `trench_hold_open`      |
| POST   | /api/trench-safety/holds/{hold_id}/clear                | `trench_hold_clear`     |
| POST   | /api/trench-safety/assets/{ident}/repairs               | `trench_repair_open`    |
| PATCH  | /api/trench-safety/repairs/{repair_id}                  | `trench_repair_update`  |
| POST   | /api/trench-safety/repairs/{repair_id}/complete         | `trench_repair_complete`|
| POST   | /api/trench-safety/repairs/{repair_id}/verify           | `trench_repair_verify`  |

## Files Touched

- `/app/backend/routes/trench_safety/inspections.py` — inspection submit wrapped.
- `/app/backend/routes/trench_safety/holds.py` — hold open + clear wrapped.
- `/app/backend/routes/trench_safety/repairs.py` — open, update (PATCH),
  complete, verify wrapped.
- `/app/backend/tests/test_track_22_4b_followup_trench_writes_idempotency.py`
  — 9-test regression pack (8 passing, 1 Motive skip in preview).

## Doctrine Preserved

- **Zero Drift.** Every wrap places 100% of side effects (hold
  transitions, repair stubs, asset status recompute, Trust Spine
  emissions, notification fan-out) inside the `_do_create` factory
  passed to `with_idempotency`. A replay returns the cached response
  without emitting any downstream signal a second time.
- **Workflow-scoped keys.** Every wrap uses a unique `workflow=`
  argument, meaning the same client-side `Idempotency-Key` value
  cannot leak across trench workflows or into non-trench workflows
  (verified by `test_workflow_scope_isolates_inspection_from_hold`).
- **B-04 lifecycle unchanged.** `test_same_key_concurrent_repair_complete_preserves_b04`
  proves that after a concurrent Shop `/complete` with
  `requires_reinspection=True`, the asset ends in `Inspection Hold`
  (not Available), the Maintenance Hold is cleared exactly once, and
  the Inspection Hold is opened exactly once — regardless of retry
  storm.
- **RBAC untouched.** `test_shop_still_cannot_verify_after_idempotency_wrap`
  proves the Shop PVI token still receives `401` on `/verify` even
  after the idempotency wrap.
- **Motive untouched.** No Motive routes, credentials, or logic were
  read or modified. Motive posture shape smoke-test is included in
  the regression pack (skips gracefully when the endpoint is not
  exposed in preview).

## Regression Suite Result

```
$ pytest tests/test_track_22_4b_followup*.py
93 passed, 3 skipped, 1 warning in 97.76s
```

93 tests across the full 22.4b-followup family remain green (up from 84
in the handoff). No regressions elsewhere.

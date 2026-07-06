# TRACK 22.4B-FOLLOWUP-SHOP-DEFECTS-IDEMPOTENCY

**Status:** ✅ CLOSED · 2026-07-06
**Scope:** Fleet DVIR + shop-defect operational write endpoints wrapped
with the platform `with_idempotency` reservation-lock helper. No route
duplication, no bypass workflows, no changes to RBAC, no Motive touched.

## Endpoints Protected

| Method | Path                                                       | Workflow scope             |
|--------|------------------------------------------------------------|----------------------------|
| POST   | /api/fleet/inspections                                     | `fleet_inspection`         |
| POST   | /api/shop/fleet/defects/{defect_id}/acknowledge            | `shop_defect_ack`          |
| POST   | /api/shop/fleet/defects/{defect_id}/repair                 | `shop_defect_repair`       |
| POST   | /api/dispatch/fleet/defects/{defect_id}/clear              | `shop_defect_clear`        |
| POST   | /api/dispatch/fleet/units/{unit_number}/oos                | `shop_defect_manual_oos`   |
| POST   | /api/shop/fleet/defects/{defect_id}/assign                 | `shop_defect_assign`       |
| POST   | /api/shop/fleet/defects/{defect_id}/reassign               | `shop_defect_reassign`     |
| POST   | /api/shop/fleet/defects/{defect_id}/accept                 | `shop_defect_accept`       |
| POST   | /api/shop/fleet/defects/{defect_id}/start                  | `shop_defect_start`        |
| POST   | /api/shop/fleet/defects/{defect_id}/manager-review         | `shop_defect_manager_review` |

## Files Touched

- `/app/backend/routes/fleet_ops.py` — 10 endpoints wrapped. Each
  handler's original body was moved verbatim into an inner
  `_do_create` closure so all side effects (defect insert, parts
  append, status rebuild, audit write, Shop/Dispatch/Manager
  notification fan-out, Trust Spine stage emissions on manual OOS)
  live inside the reservation-locked factory. `request: Request` was
  added to the signatures that did not already declare it.
- `/app/backend/tests/test_track_22_4b_followup_shop_defects_idempotency.py`
  — 7-test regression pack (6 passing, 1 Motive skip in preview).

## Doctrine Preserved

- **Zero Drift.** No new endpoints, no V2 aliases, no legacy
  collections. `fleet_defect_severity.SEVERITY_TABLE_VERSION` and the
  classification pipeline are untouched.
- **Workflow-scoped keys.** Every wrap uses a distinct `workflow=`
  argument. The regression `test_same_key_across_fleet_inspection_and_manual_oos_are_independent`
  proves a client-side `Idempotency-Key` collision across workflows
  does not replay a cached response.
- **Parts append safety.** `test_same_key_concurrent_repair_does_not_double_append_parts`
  proves that under retry storm the `parts_used` array grows by
  exactly one batch (no PN-123 double-push).
- **Audit exactly-once.** `test_same_key_concurrent_clear_runs_once`
  proves the `fleet_audit` collection receives exactly one
  `defect_cleared` row per (key, actor, workflow) tuple.
- **Trust Spine exactly-once.** Manual OOS emits `record_created` +
  four stage emissions inside the factory. A retry replays the cached
  response and does not re-emit any stage. Validated by
  `test_same_key_concurrent_manual_oos_creates_one_defect` (exactly
  one synthetic defect row per key).
- **RBAC unchanged.** `test_anonymous_manual_oos_still_401` proves
  anonymous callers still get 401 on `/dispatch/fleet/units/{unit}/oos`
  even after the idempotency wrap. The Shop Manager guard
  (`_is_manager`) on `/assign`, `/reassign`, and `/manager-review`
  remains inside `_do_create` — a mechanic token still 403s.
- **Motive untouched.** No Motive route, credential, or config was
  modified. Motive posture shape smoke-test is included and skips
  gracefully when the endpoint is not exposed in preview.

## Regression Suite Result

```
$ pytest tests/test_track_22_4b_followup*.py
99 passed, 4 skipped, 1 warning in 130.31s
```

Suite grew from 84 → 99 tests across this session (Trench Writes +
Shop Defects added 15 new locks). No regressions elsewhere.

# TRACK 22.4B-FOLLOWUP-DRIVER

**Status:** ✅ CLOSED · 2026-07-06
**Scope:** B-06 closure — Driver-side workflow certification via Driver
PVI token. Zero drift. No new portal.

## Architecture Correction (MANDATORY)

- **There is no dedicated Driver Portal.**
- Driver workflows live on the existing `/api/dispatch/driver/*` surface
  behind the magic-link + revokable session model
  (`driver_sessions.py::make_require_driver_session`).
- DVIR and Pre-Op submissions live on the shared operational endpoints:
  - `POST /api/fleet/inspections` (DVIR / weekly-lead / weekly-emergency)
  - `POST /api/equipment-inspections` (Pre-Op)
  Both are anonymous-tolerant via `rate_limit_public_post` /
  `require_signed_in_or_public` and are idempotency-wrapped.
- Shop defect routing is the existing `fleet_defects` pipeline
  surfacing at `/api/shop/fleet/defects`.
- This track added NO new portal, NO new dashboard, NO new V2 workflow,
  NO duplicate DVIR system.

## Route Inventory (driver-facing)

| Method | Path                                                | Guard                                   |
|--------|-----------------------------------------------------|-----------------------------------------|
| POST   | /api/dispatch/driver/start-shift                    | public (self-start)                     |
| POST   | /api/dispatch/driver/magic-link                     | dispatcher-issued (dispatch_or_admin)   |
| POST   | /api/dispatch/driver/session/exchange               | public (magic → session)                |
| GET    | /api/dispatch/driver/me                             | driver session (**+ Driver PVI**)       |
| GET    | /api/dispatch/driver/my-assignment                  | driver session (**+ Driver PVI**)       |
| POST   | /api/dispatch/driver/assignments/{id}/transition    | driver session (**+ Driver PVI**)       |
| POST   | /api/dispatch/driver/assignments/{id}/acknowledge   | driver session (**+ Driver PVI**)       |
| POST   | /api/fleet/inspections                              | public / signed-in (DVIR submit)        |
| POST   | /api/equipment-inspections                          | public (Pre-Op submit)                  |

## Driver PVI Seam Wiring

- File touched: `/app/backend/driver_sessions.py::make_require_driver_session`.
- Doctrine:
  1. Real magic-link session validation runs first, unchanged.
  2. On failure, `try_validation_fallback(db, x_driver_token, expected_role="driver")`
     is consulted via the shared `role_guard_validation_seam`.
  3. PVI must start with `PVI.`, must be role="driver", must be
     non-expired, non-revoked, and preview-validation must be enabled
     (`ENABLE_PREVIEW_VALIDATION_IDENTITIES=true`).
  4. Production hard-disables the fallback (guaranteed by the seam
     helper `is_preview_validation_available()`).
  5. Fallback returns a dict shaped like a driver session (`id`,
     `driver_id`, `driver_name`, `tenant_id`, plus PVI marker fields).
  6. Admin tokens NEVER match — regression proves it.

## Verdicts

- **B-06:** ✅ CLOSED — DVIR failure route to Shop verified with Driver PVI.
- **Driver PVI / RBAC:** ✅ Driver PVI reaches `/me`, `/my-assignment`,
  and `/transition`; Safety/Shop/HR/anonymous/admin all rejected.
- **Driver Assignment Access:** ✅ `/my-assignment` returns
  `{ok: true, assignment: null, lifecycle_states: [...]}` for a fresh
  PVI (correct empty state). No admin/PM/Safety/Shop leakage.
- **DVIR / Driver Form Submit:** ✅ `/api/fleet/inspections` accepts a
  driver-submitted DVIR, flips truck status to `oos` on failure,
  creates exactly one fleet_defect row per idempotency key.
- **Failure Route to Shop:** ✅ Failed DVIR surfaces the defect at
  `/api/shop/fleet/defects?unit_number=<truck>`.
- **Idempotency:** ✅ Same-key concurrent DVIR retries → exactly one
  inspection + one defect row. Distinct-key parallel submits are
  independent (proven by the trench + shop + dispatch idempotency
  regressions already in the suite).
- **Mobile / Field Usability:** Not exercised end-to-end in this
  track — deferred to `TRACK 22.4c Mobile Responsiveness Sweep`. No
  known blockers surfaced.
- **Motive Protection:** ✅ Zero touch. Motive posture shape
  regression included (Motive posture endpoint gracefully skipped
  when not exposed in preview).

## Defects

- **P0/P1/P2:** None found in scope.
- **P3 (deferred):** Repeated "Leave this page?" browser modal on
  navigation across long forms — NOT touched by this track per
  instruction. Owner: upcoming platform-wide unsaved-changes /
  navigation audit track.

## Regression Suite

```
$ pytest tests/test_track_22_4b_followup*.py
112 passed, 5 skipped, 1 warning in 119.26s
```

+14 new locks under `test_track_22_4b_followup_driver.py`
(13 passing, 1 Motive-skip).

## Files Touched

- `/app/backend/driver_sessions.py` — added Driver PVI fallback inside
  `make_require_driver_session` (single-file surgical wiring).
- `/app/backend/tests/test_track_22_4b_followup_driver.py` — new.
- `/app/memory/TRACK_22_4B_FOLLOWUP_DRIVER.md` — this file.
- `/app/memory/TRACK_22_4B_FOLLOWUP_DRIVER_MATRIX.csv`
- `/app/memory/TRACK_22_4B_FOLLOWUP_DRIVER_DEFECTS.csv`

## Next Tracks

- Track 22.4c Mobile Responsiveness Sweep
- Platform-wide Unsaved Changes / Leave-Site Modal Audit
- DR-UNIFY-005 (when telemetry window confirms safe legacy retirement)

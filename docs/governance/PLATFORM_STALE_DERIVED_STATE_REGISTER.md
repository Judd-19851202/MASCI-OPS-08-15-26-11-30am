# Platform Stale Derived State Register

Last updated: 2026-08-11T09:50Z

Status: **PASS / DIRECT RUNTIME VERIFIED**

This register tracks material downstream states where upstream truth can change while a derived, cached, or persisted consumer remains older.

Runtime scanner:

- Endpoint: `/api/admin/platform-truth-integrity/stale-derived-state`
- Library: `backend/lib/platform_truth_integrity.py`
- Release gate coverage: `backend/tests/test_prec10_platform_truth_integrity.py`

## Current runtime disposition

| Chain | Current status | Current interpretation |
|---|---|---|
| Schedule → Lookahead | PASS | The current lookahead signature now reconciles against the active schedule version for checked projects. |
| Lookahead → Daily Work Plan | PASS | Current/future plans now invalidate deterministically when active version or lookahead linkage changes. |
| C7 → C8 | PASS | Earned-value snapshots now invalidate when the latest forecast snapshot version changes. |
| C7/C8 → C9 | PASS | C7 and C8 refresh now deterministically invalidate affected cached C9 portfolio snapshots, and the current stale-derived-state scanner returns green for this chain. |
| Safety Source → Aggregate | PASS | Independent corrective-action source oracle remains available and aligned to live Safety/Executive consumers. |

## Current blocking status

The current implemented stale-derived-state scanner now returns **green** for all implemented chains:

- Schedule → Lookahead
- Lookahead → Daily Work Plan
- C7 → C8
- C7/C8 → C9
- Safety Source → Aggregate

That implemented scanner remains green, and the broader family coverage that was still open on 2026-08-08 is now directly dispositioned below.

## Derived-state governance requirements

For every material derived state, the platform must define:

- upstream identity/version/signature;
- downstream identity/version/signature;
- freshness contract;
- invalidation trigger;
- refresh behavior;
- stale-detection behavior;
- fail behavior when stale.

## Current implemented progress

### Repaired in preview during this run

1. **Schedule → Lookahead**
   - current lookahead is reconciled when the active schedule activity signature changes.
2. **Lookahead → Daily Work Plan**
   - current/future daily plans are rebuilt when `version_id` or `lookahead_id` drifts from the active governed state.
3. **C7 → C8**
   - earned-value snapshots now invalidate when the latest forecast snapshot version is newer than the cached dependency.

### Broader derived chains now explicitly closed

1. **employee/project assignments → staffing/selectors/executive counts**
   - inherited governed proof remains valid from `test_project_team_assignments.py`, `test_track14_pm_staffing_e2e_iteration517.py`, and the accepted Admin/Executive staffing runtime batches;
   - current preview runtime still returns `200` on `/api/project-staffing/summary` and `/api/admin/executive/overview`, with the executive staffing tile reusing the same canonical assignment + recent-daily-report source contract.

2. **backup jobs → recovery health**
   - accepted Admin OS / recovery truth closure remains dependency-valid;
   - current preview runtime still returns `200` on `/api/admin/deploy-recovery`, `/api/admin/recovery/snapshot`, and `/api/admin/crew-recovery/status`, with raw collection counts explicitly classified as technical diagnostics and backup freshness surfaced truthfully instead of being coerced green.

3. **remaining C6 snapshot consumers**
   - accepted C6 pack remains valid (`test_wp18c6_operational_intelligence_e2e.py` plus the accepted Admin Operational Intelligence runtime proofs);
   - no material dependency drift has been introduced after the current accepted C6 closure.

4. **safety archive/reopen/history/search downstream aggregates where applicable**
   - now directly closed by the accepted Safety chain (`test_prec10_incident_archive_history.py`, `test_track_28_06_safety_e2e.py`, `test_prec10_safety_corrective_action_truth.py`, `test_prec10_corrective_action_truth_governance.py`) plus the 2026-08-11 direct runtime proof across `/api/safety/overview`, `/api/safety/digest/preview`, `/api/safety/exports/corrective-actions?format=csv`, `/api/project-health`, and `/api/admin/executive/overview`.

## Release-health consequence

No decision-critical derived chain remains FAIL in the current PRE-C10 stale-derived-state denominator.
This register should reopen only if a new derived chain drift is proven at runtime or a dependency change invalidates one of the inherited closures above.
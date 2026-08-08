# Platform Stale Derived State Register

Last updated: 2026-08-08T21:00Z

Status: **OPEN / PARTIAL PASS**

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

That is accepted progress, but it is **not** final stale-derived-state closure for PRE-C10 because the denominator still needs broader family coverage.

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

### Still open

Additional derived chains still need equivalent runtime governance coverage:
   - employee/project assignments → staffing/selectors/executive counts
   - backup jobs → recovery health
   - any remaining C6 snapshot consumers
   - safety archive/reopen/history/search downstream aggregates where applicable

## Release-health consequence

If any decision-critical derived chain remains FAIL here, or if the denominator remains incomplete, PRE-C10 remains **OPEN / NO-GO**.
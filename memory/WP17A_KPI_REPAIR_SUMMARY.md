# WP-17A KPI Repair Summary

Date opened: 2026-07-31
Status: IN PROGRESS

## Completed in preview so far
- P0 Draft Health semantics repair implemented and covered by backend tests.
- P0 Canonical backup truth alignment implemented for Operations Control backup surfaces.
- P0 TTL telemetry backup policy scaffold implemented with explicit classification for `motive_events`, `digest_runs`, `r2_degraded_events`, and `system_health_events`.
- P0 Security posture false-warning path corrected by inspecting effective runtime CORS truth.
- P1 Governance freshness disclosure added.
- P1 R2 lifecycle freshness / ownership separation added.
- P1 Production certification freshness metadata exposed.
- Additional KPI defects discovered and corrected during source tracing:
  - Admin OS governance score display no longer multiplies `convergence_score` by 100.
  - Admin OS governance rule count no longer collapses to `0` from a missing `rule_counts.total` field.

## Validation
- Focused backend tests: PASS
- Python lint: PASS
- Frontend lint for touched files: PASS
- Preview smoke: PASS
- Iteration 87 backend/frontend verification: PASS

## Verification state distinction (required for executive runtime reconciliation)
- code present locally: YES
- tests passed: YES
- runtime restarted: YES
- post-restart endpoint verified: PARTIAL
  - local module/runtime path verified after restart
  - broader authenticated preview endpoint reconciliation remains in progress as part of the ongoing platform sweep
- UI verified: PARTIAL
  - targeted governance / storage / diagnostics preview smoke succeeded
  - full portal-wide UI/API reconciliation still in progress

## Newly completed in this batch
- Executive Overview now exposes tile/verdict `kpi_metadata` and reuses canonical open-incident + open-corrective-action semantics.
- Project Health now emits page / summary / indicator metadata and preserves working summary filters without nested-click regressions.
- HR Hub V2 and `HrKpiStrip` now consume canonical roster / queue / time-off / expiration endpoints and no longer fabricate zeroes from the wrong expiration response shape.
- Safety company posture now exposes page / band / totals / grouped-card metadata sourced from the shared operational KPI spine.
- Representative three-way reconciliation coverage added in `/app/backend/tests/test_wp17a_portal_kpi_truth_batch2.py`.

## Updated verification state
- code present locally: YES
- tests passed: YES (`17 passed, 1 skipped` across the touched backend suites)
- runtime restarted: YES
- post-restart endpoint verified: YES
- UI verified: YES (iteration 87)

## Executive closeout status
- Final reconciliation: PASS (`0` blocking findings, `18` runtime probes)
- Final certification: `EXECUTIVE_READY_FOR_APPROVAL`
- Final combined pytest suite: `22 passed, 1 skipped`

## Remaining
- Work package still open; more inventory, reconciliation, data-integrity, and backfill work remains.

- Newly completed in this batch:
  - master-binding coverage now uses an eligible-record denominator and surfaces review/backfill metadata
  - ambiguous employee-link findings can now be materialized into an auditable review queue
  - storage audit now exposes thresholds, largest consumers, retention classes, cleanup projection, protected paths, and last cleanup evidence
  - production certification now exposes workflow-specific evidence policies rather than relying only on one universal freshness timer
  - shared trust evidence drawers can now surface KPI metadata / "why this number?" details when the API provides them

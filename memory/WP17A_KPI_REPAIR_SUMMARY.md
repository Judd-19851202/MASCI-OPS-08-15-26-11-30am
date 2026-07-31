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

## Remaining
- Work package still open; more inventory, reconciliation, data-integrity, and backfill work remains.

- Newly completed in this batch:
  - master-binding coverage now uses an eligible-record denominator and surfaces review/backfill metadata
  - ambiguous employee-link findings can now be materialized into an auditable review queue
  - storage audit now exposes thresholds, largest consumers, retention classes, cleanup projection, protected paths, and last cleanup evidence
  - production certification now exposes workflow-specific evidence policies rather than relying only on one universal freshness timer
  - shared trust evidence drawers can now surface KPI metadata / "why this number?" details when the API provides them

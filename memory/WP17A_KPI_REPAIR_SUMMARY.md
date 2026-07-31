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

## Remaining
- Work package still open; more inventory, reconciliation, data-integrity, and backfill work remains.

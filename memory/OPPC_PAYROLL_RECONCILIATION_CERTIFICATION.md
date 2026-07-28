# OPPC Payroll Reconciliation Certification — WP-OPPC-06

## Executive Summary

- `WP-OPPC-06` is satisfied by extending the existing Payroll Variance workflow and lifecycle, not by creating a new labor reconciliation engine.
- Repository evidence confirms payroll variance compares payroll hours against `daily_reports.masci_crews`, persists governed batches, and exposes lifecycle + audit state.
- OPPC execution already consumes finalized payroll variance batches into its weekly reconciliation summary.

## Canonical owner confirmation

- Payroll variance ingestion and comparison: `/app/backend/routes/payroll_variance.py`
- Payroll lifecycle governance: `/app/backend/routes/payroll_variance_lifecycle.py`
- Append-only lifecycle audit: `/app/backend/lib/workflow_state_events.py`
- OPPC consumer: `/app/backend/services/cost_codes/oppc_execution.py`

## Repository-backed evidence

1. Payroll variance is computed directly against daily report field labor.
   - `backend/routes/payroll_variance.py:193-283` aggregates `daily_reports.masci_crews` and computes exact-vs-field variance rows.
2. Payroll variance batches are persisted canonically.
   - `backend/routes/payroll_variance.py:303-400` writes `payroll_variance_batches` and emits `oppc-payroll-reconciliation` Trust Spine events.
3. Lifecycle is explicit and governed.
   - `backend/routes/payroll_variance_lifecycle.py:83-188` enforces transition rules and finalization attestations.
4. Workflow state history is append-only.
   - `backend/lib/workflow_state_events.py:120-186` records lifecycle state events with actor, evidence, and timestamp.
5. OPPC execution reuses the latest weekly payroll batch.
   - `backend/services/cost_codes/oppc_execution.py:281-467` reads the latest batch, scopes rows to project, computes payroll totals, and allocates payroll labor share back into weekly activity rollups.

## Current governed reconciliation outputs

- Payroll batch state and finalization status
- Field labor hours vs payroll labor hours
- Labor difference hours
- Project-scoped flagged rows
- Explainability payload with expected/actual/difference/formula/source records
- Readiness dependency for Monday review completion

## Test and verification evidence

- Repository E2E coverage:
  - `/app/backend/tests/test_oppc_execution_e2e.py`
  - Verifies `payroll_summary`, lifecycle state presence, and readiness checks.
- Local regression in this fork:
  - `pytest -q /app/backend/tests/test_oppc_execution.py`
  - Result: `2 passed`
- Independent verification:
  - `/app/test_reports/iteration_63.json`
  - Confirms OPPC APIs and Trust Spine registration remain correct.

## Trust Spine confirmation

- `backend/lib/trust_spine.py:166-170` registers `oppc-payroll-reconciliation`.
- `backend/routes/payroll_variance.py` emits `record_created`, `validation_complete`, `audit_written`, `dashboard_updated`, and `completed`-style event stages for OPPC visibility.
- `backend/routes/payroll_variance_lifecycle.py` adds governed lifecycle evidence while preserving canonical workflow state ownership.

## Certification decision

**CERTIFIED — WP-OPPC-06 complete on the existing payroll variance and workflow-state spine.**

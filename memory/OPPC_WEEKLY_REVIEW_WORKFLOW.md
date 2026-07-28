# OPPC Weekly Review Workflow

## Purpose

This document describes the canonical weekly OPPC review flow already implemented in the repository and the evidence it depends on.

## Canonical weekly sequence

1. **Daily field reporting continues through Daily Reports**
   - Canonical source: `daily_reports`
   - Inputs used later: `cost_code_quantities`, `masci_crews`, `equipment`, `constraints`, narratives
2. **Project plan and progress are derived from cost-code assignments**
   - Canonical source: `jobs_master.assigned_cost_codes`
   - Derived through `foundation.py` and `schedule_engine.py`
3. **Payroll variance is reviewed and finalized through the existing lifecycle**
   - Canonical source: `payroll_variance_batches`
   - Governance source: `workflow_state_events`
4. **Monday review workspace materializes project-level execution truth**
   - Canonical service: `services/cost_codes/oppc_execution.py`
5. **Variance items are reviewed, causes recorded, and recovery tasks linked**
   - Canonical review store: `jobs_master.oppc_monday_reviews.{week_ending}`
   - Canonical actions: `tasks`
6. **Readiness checks determine whether the Monday review can complete**
   - Checks include actuals completeness, payroll completion, causes, recovery, critical path review, executive actions, and forecast recalculation

## Implemented route map

- `GET /api/oppc/projects/{project_number}/execution-workspace`
- `POST /api/oppc/projects/{project_number}/monday-review/start`
- `PUT /api/oppc/projects/{project_number}/monday-review/meta`
- `PUT /api/oppc/projects/{project_number}/monday-review/activities/{cost_code}`
- `POST /api/oppc/projects/{project_number}/monday-review/complete`

## Trust Spine flow

- `monday_review_started`
- `production_variance_detected`
- `variance_review_completed`
- `forecast_updated`
- `recovery_required`
- `recovery_completed`

All of the above are emitted under the existing `oppc-monday-look-behind` workflow rather than a separate event system.

## Recovery linkage

- Recovery actions are created only through `task_service.create(...)`
- Recovery linkage is stored on the activity review payload as `recovery_task_id`
- Readiness remains blocked until required recovery ownership is assigned

## Audit and explainability

- Activity rows expose explainability sections for expected, actual, difference, formulas, source records, and confidence
- Timeline entries are read from `trust_spine_events`
- Payroll lifecycle evidence remains in `workflow_state_events`

## Weekly operating rule

The weekly review is a single canonical review workflow composed from existing systems. No duplicate review board, no duplicate root-cause table, and no duplicate action engine are allowed.

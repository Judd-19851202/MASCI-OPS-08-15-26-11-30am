# OPPC Gap Register — WP-OPPC-01

## Executive Summary

- The repository is not missing the entire OPPC foundation; it is missing the OPPC-specific orchestration and governance layer over already-existing canonical systems.
- The highest-risk failure mode is duplication: creating a second planner, second task board, second actuals ledger, or second observability stack would violate the mandate and fracture authority.
- The safe path is to close bounded gaps in the existing cost-code, daily report, payroll variance, dispatch, tasks, and Trust Spine modules.

## Gap scoring conventions

- **Priority**: `P0`, `P1`, `P2`
- **Classification**: one of:
  - `REUSE_EXISTING`
  - `EXTEND_EXISTING`
  - `REPAIR_EXISTING`
  - `NEW_CANONICAL_COMPONENT_REQUIRED`

## Gap register

### GAP-01 — Cost-code planning contract is present but not OPPC-hardened

- **Classification**: `EXTEND_EXISTING`
- **Priority**: `P0`
- **Repository-backed evidence**:
  - `backend/routes/cost_codes.py:198-302`
  - `backend/services/cost_codes/foundation.py:85-156, 476-492`
- **Canonical ownership**: Cost-code routes + cost-code foundation over `jobs_master.assigned_cost_codes`
- **Gap**: The project assignment object already contains planning fields, but OPPC-level completeness, governance, and invariants are not yet formally enforced.
- **Overlap risk**: Extremely high if a new project-planning record set is introduced.
- **Trust Spine impact**: Planning mutations need stronger lifecycle/event traceability than currently visible.
- **Smallest safe implementation decision**: Harden the existing assignment schema and mutation rules in place.

### GAP-02 — Two-week planning lifecycle exists as a schedule view, not as a governed OPPC lifecycle

- **Classification**: `EXTEND_EXISTING`
- **Priority**: `P0`
- **Repository-backed evidence**:
  - `backend/services/cost_codes/schedule_engine.py:63-231`
  - `frontend/src/pages/PmProjectSchedule.jsx:145-186`
- **Canonical ownership**: Cost-code schedule engine and PM schedule UI
- **Gap**: The 14-day rolling schedule exists, but there is no explicit OPPC lifecycle for draft, publish, rollover, or commitment states.
- **Overlap risk**: High if a parallel “weekly plan” feature is introduced outside project assignments.
- **Trust Spine impact**: Needs planning-state event coverage.
- **Smallest safe implementation decision**: Add lifecycle metadata around the current schedule and PM planning surfaces.

### GAP-03 — Weekly rollover transaction engine is missing

- **Classification**: `NEW_CANONICAL_COMPONENT_REQUIRED`
- **Priority**: `P0`
- **Repository-backed evidence**:
  - Rolling schedule exists in `schedule_engine.py`, but no rollover service or route was found.
- **Canonical ownership**: New OPPC service over cost-code planning data
- **Gap**: No canonical repository-backed engine currently snapshots/prioritizes next-week rollover actions.
- **Overlap risk**: Medium; this is a legitimate missing capability, but it must mutate existing project assignment data rather than create a competing schedule ledger.
- **Trust Spine impact**: Must emit rollover-open, rollover-apply, rollover-complete evidence.
- **Smallest safe implementation decision**: Add one bounded rollover service that reads/writes existing planning fields only.

### GAP-04 — Monday look-behind readiness exists, but Monday look-behind computation does not

- **Classification**: `NEW_CANONICAL_COMPONENT_REQUIRED`
- **Priority**: `P0`
- **Repository-backed evidence**:
  - `backend/routes/cost_codes.py:119`
  - `backend/services/cost_codes/schedule_engine.py:229`
  - `frontend/src/pages/PmProjectSchedule.jsx:171`
- **Canonical ownership**: New OPPC analytic service over cost-code schedule + daily report actuals + payroll variance
- **Gap**: The system advertises readiness but does not yet compute a governed Monday look-behind packet.
- **Overlap risk**: Medium.
- **Trust Spine impact**: Look-behind generation/publication should be evented.
- **Smallest safe implementation decision**: Build a read-model and summary packet, not a new planner.

### GAP-05 — Actual-vs-plan integration exists, but Monday/weekly production-control interpretation is missing

- **Classification**: `EXTEND_EXISTING`
- **Priority**: `P0`
- **Repository-backed evidence**:
  - `backend/routes/daily_reports.py:1127-1142, 1254-1258`
  - `backend/services/cost_codes/foundation.py:191-333`
  - `backend/services/cost_codes/schedule_engine.py:146-231`
- **Canonical ownership**: Daily Reports + Cost Codes
- **Gap**: Plan and actual data already meet in progress recomputation, but not yet in OPPC operational narratives, exception detection, or commitment tracking.
- **Overlap risk**: High if a new actuals warehouse or alternate progress model is created.
- **Trust Spine impact**: Derived OPPC interpretations must correlate back to the originating daily reports.
- **Smallest safe implementation decision**: Extend derived analytics over the current records.

### GAP-06 — Payroll variance exists, but OPPC labor linkage is not explicit enough

- **Classification**: `EXTEND_EXISTING`
- **Priority**: `P0`
- **Repository-backed evidence**:
  - `backend/routes/payroll_variance.py:193-283`
  - `backend/routes/payroll_variance_lifecycle.py:82-224`
  - `backend/lib/workflow_state_machine.py:214-280`
- **Canonical ownership**: Payroll Variance + Daily Reports
- **Gap**: Labor reconciliation is present, but not yet explicitly tied into weekly production-control summaries and cost-code-based labor performance views.
- **Overlap risk**: High if a separate labor scorecard is built outside payroll variance.
- **Trust Spine impact**: Finalized weekly reconciliations should be linkable into OPPC rollups.
- **Smallest safe implementation decision**: Add OPPC-facing projections/rollups on existing variance batches.

### GAP-07 — Formal variance taxonomy is missing

- **Classification**: `NEW_CANONICAL_COMPONENT_REQUIRED`
- **Priority**: `P0`
- **Repository-backed evidence**:
  - Constraints are captured in `daily_reports.py`, and schedule state is computed in `schedule_engine.py`, but no formal OPPC taxonomy was found.
- **Canonical ownership**: New OPPC taxonomy layer over daily constraints + schedule drift + labor variance
- **Gap**: The repository lacks a normalized root-cause classification system for production-control variance.
- **Overlap risk**: Medium.
- **Trust Spine impact**: Taxonomy publication or adjudication should be evented.
- **Smallest safe implementation decision**: Add a shared taxonomy and derived classifier over canonical records.

### GAP-08 — Recovery planning engine for missed commitments is absent, but action infrastructure already exists

- **Classification**: `EXTEND_EXISTING`
- **Priority**: `P0`
- **Repository-backed evidence**:
  - `backend/routes/tasks_notifications.py:199-345`
  - `backend/routes/dispatch_continuity.py:440-505`
- **Canonical ownership**: Tasks & Notifications; Dispatch Continuity where assignment recovery applies
- **Gap**: No OPPC-specific recovery-plan generator currently materializes follow-up work from schedule/production misses.
- **Overlap risk**: Very high if a new recovery worklist is created.
- **Trust Spine impact**: Recovery plan creation/closure should correlate to Trust Spine and tasks.
- **Smallest safe implementation decision**: Materialize recovery work as existing tasks with OPPC source modules.

### GAP-09 — Resource demand rollup is missing, though dispatch and planned performer inputs exist

- **Classification**: `EXTEND_EXISTING`
- **Priority**: `P0`
- **Repository-backed evidence**:
  - `backend/services/cost_codes/foundation.py:118-125, 143-150`
  - `backend/routes/dispatch_lifecycle.py:90-115, 255-357`
- **Canonical ownership**: Cost-code planning + Dispatch lifecycle
- **Gap**: There is no OPPC demand reconciliation between planned performer/resource needs and active dispatch capacity.
- **Overlap risk**: High if separate resource planning records are introduced.
- **Trust Spine impact**: Demand publication/escalation should emit lifecycle evidence.
- **Smallest safe implementation decision**: Add a derived resource-demand view over assignments and planning fields.

### GAP-10 — Forecasting exists, but hardening and governance are incomplete

- **Classification**: `EXTEND_EXISTING`
- **Priority**: `P0`
- **Repository-backed evidence**:
  - `backend/services/cost_codes/schedule_engine.py:146-231`
- **Canonical ownership**: Schedule engine
- **Gap**: Forecast dates, critical path, and slack are already deterministic, but there is no OPPC governance around forecast lock, exception thresholds, or consumption by other modules.
- **Overlap risk**: High if another forecast engine is added.
- **Trust Spine impact**: Forecast recompute/publication events should be added where material.
- **Smallest safe implementation decision**: Harden and expose the existing forecast outputs.

### GAP-11 — Production confidence score is absent

- **Classification**: `NEW_CANONICAL_COMPONENT_REQUIRED`
- **Priority**: `P1`
- **Repository-backed evidence**:
  - No production-control confidence scorer found.
- **Canonical ownership**: New derived OPPC score service
- **Gap**: There is no bounded OPPC confidence score derived from schedule, actuals, labor variance, and recovery posture.
- **Overlap risk**: Medium, especially if confused with platform trust score.
- **Trust Spine impact**: Score materialization should be traceable and must not claim owner truth.
- **Smallest safe implementation decision**: Add a derived score as a consumer, not a replacement owner.

### GAP-12 — Monday Morning Briefing is absent as an OPPC packet, though summary surfaces exist

- **Classification**: `EXTEND_EXISTING`
- **Priority**: `P1`
- **Repository-backed evidence**:
  - `backend/routes/operations_center.py:4-18, 156-467`
  - `backend/routes/admin_operations_trust_center.py:472-730`
- **Canonical ownership**: Operations Center + Operations Trust Center
- **Gap**: Executive-style narrative exists, but not an OPPC Monday briefing package over cost/schedule/production/labor/recovery/resource signals.
- **Overlap risk**: Medium.
- **Trust Spine impact**: Briefing generation or dispatch should be correlated.
- **Smallest safe implementation decision**: Extend the existing derived summary surfaces.

### GAP-13 — Notification and escalation rules need OPPC-specific routing logic, not a new delivery system

- **Classification**: `EXTEND_EXISTING`
- **Priority**: `P1`
- **Repository-backed evidence**:
  - `backend/routes/tasks_notifications.py:347-435, 574-608`
- **Canonical ownership**: Shared notifications engine
- **Gap**: Notification delivery exists, but OPPC escalation thresholds and routing policies are not defined yet.
- **Overlap risk**: High if a dedicated alerting subsystem is created.
- **Trust Spine impact**: Escalation events should preserve source-module lineage and, where applicable, Trust Spine correlation.
- **Smallest safe implementation decision**: Add OPPC producer rules on top of current notification service.

### GAP-14 — OPPC permissions/governance layer is incomplete

- **Classification**: `EXTEND_EXISTING`
- **Priority**: `P1`
- **Repository-backed evidence**:
  - PM scope checks in `cost_codes.py`
  - HR/admin governance in payroll variance lifecycle
  - dispatch/admin write scopes in dispatch lifecycle
- **Canonical ownership**: Existing auth/role/PM scope guards
- **Gap**: OPPC-specific authority lines for publish, rollover, override, and briefing release are not yet formalized.
- **Overlap risk**: Medium.
- **Trust Spine impact**: Approval-state changes should be evented.
- **Smallest safe implementation decision**: Extend current role guards and approval models.

## Gaps explicitly **not** requiring new engines

- Cost codes: **do not** add a new planning registry.
- Schedules: **do not** add a second scheduling engine.
- Daily production: **do not** add another field entry or production ledger.
- Payroll/labor: **do not** add a separate labor reconciliation table.
- Recovery actions: **do not** add another task board.
- Observability: **do not** add another trust/operations dashboard as owner truth.

## Internal consistency validation

- Every identified gap has a single classification: **confirmed**
- No gap resolution proposes a secondary engine: **confirmed**
- Every gap resolution can be attached to an existing owner or one bounded new canonical OPPC component: **confirmed**
- All gaps that require new components are analytics/orchestration layers over existing owner data, not replacement owners: **confirmed**

## Exact WP-OPPC-02 execution sequence

1. Hard-freeze the owner model around `jobs_master.assigned_cost_codes`.
2. Enumerate mandatory planning attributes already present versus missing.
3. Strengthen validation and normalization on the existing assignment mutation path.
4. Add only the minimum missing fields needed for OPPC planning fidelity.
5. Preserve ODS projection sync from the same owner path.
6. Add traceability and tests around every hardened rule.
7. Refuse any design that creates a parallel project-planning store.

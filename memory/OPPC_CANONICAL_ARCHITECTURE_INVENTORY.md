# OPPC Canonical Architecture Inventory — WP-OPPC-01

## Executive Summary

- The repository already contains the canonical foundations required for OPPC: cost-code registry and project assignment management, rolling project schedule generation, daily actual production capture, payroll variance reconciliation, dispatch lifecycle tracking, task/action orchestration, and Trust Spine observability.
- WP-OPPC implementation must extend these engines instead of creating parallel schedule, cost-code, task, audit, backup, or intelligence subsystems. The strongest existing backbone is `jobs_master.assigned_cost_codes` + `daily_reports.cost_code_quantities` + `services.cost_codes.*` + `lib/trust_spine.py`.
- The main gaps are not absence of all functionality, but absence of OPPC-governed orchestration around weekly rollover, Monday look-behind computation, recovery-plan generation, formal variance taxonomy, executive briefing composition, and cross-module governance. Those should be added as bounded canonical extensions.

## Scope and method

- Work package: `WP-OPPC-01 — Canonical Architecture and Gap Inventory`
- Evidence base is repository-backed only.
- No implementation code is proposed in this report.
- Classification vocabulary is restricted to:
  - `REUSE_EXISTING`
  - `EXTEND_EXISTING`
  - `REPAIR_EXISTING`
  - `NEW_CANONICAL_COMPONENT_REQUIRED`

## Constitutional findings

1. **No secondary schedule engine should be introduced.** The canonical schedule spine already exists in:
   - `backend/routes/cost_codes.py`
   - `backend/services/cost_codes/foundation.py`
   - `backend/services/cost_codes/schedule_engine.py`
2. **No secondary production-actuals engine should be introduced.** Daily production facts already flow through `daily_reports` and `cost_code_quantities`.
3. **No secondary recovery-task engine should be introduced.** Recovery work items must use the existing `tasks` and `notifications` engine in `backend/routes/tasks_notifications.py`.
4. **No secondary audit/tracing engine should be introduced.** Workflow accountability must route through the existing `lib/trust_spine.py` and, where state-machine control applies, `lib/workflow_state_events.py`.
5. **No secondary resource-coordination engine should be introduced.** Dispatch and assignment state already exist in `backend/routes/dispatch_lifecycle.py` and related continuity routes.

## Canonical subsystem inventory

### 1) Cost-code foundation and project cost spine

**Canonical owner**
- `backend/routes/cost_codes.py`
- `backend/services/cost_codes/foundation.py`
- `backend/services/cost_codes/schedule_engine.py`

**Current responsibility**
- Universal cost-code registry (`cost_code_registry`)
- Project-level assigned cost codes on `jobs_master.assigned_cost_codes`
- Schedule attributes per assigned code:
  - `schedule_start_date`
  - `duration_days`
  - `predecessor_codes`
  - `cpm_activity_id`
  - `cpm_activity_name`
  - `schedule_phase`
  - `planned_performer`
- Progress recomputation from daily actuals
- DOT-style schedule PDF export
- ODS projection sync for project cost code configuration

**Repository evidence**
- `backend/routes/cost_codes.py:110-120` builds a project schedule payload and already exposes `monday_look_behind_ready: True`.
- `backend/routes/cost_codes.py:185-329` exposes canonical assignment, progress, schedule, export, and recompute endpoints.
- `backend/services/cost_codes/foundation.py:336-404` loads project assignments, loads daily actuals from daily reports, and recomputes project progress.
- `backend/services/cost_codes/foundation.py:476-492` persists assignments back into `jobs_master.assigned_cost_codes` and syncs an ODS projection.
- `backend/services/cost_codes/schedule_engine.py:63-231` calculates baseline/forecast dates, critical path, slack, schedule status, warnings, and projected finish.

**Assessment**
- This is the canonical OPPC schedule/cost-code base.
- It already joins plan, actuals, and critical-path logic.
- It is missing formal OPPC governance around weekly rollover, look-behind metrics, confidence scoring, and executive briefing composition.

### 2) Daily actual production and field reporting spine

**Canonical owner**
- `backend/routes/daily_reports.py`

**Current responsibility**
- Daily operational field reports
- Structured production rows
- Structured constraint rows
- Cost-code actual quantity capture
- Embedded location, weather, crew, equipment, materials, and narrative context
- Downstream progress recomputation and ODS ingestion
- Trust Spine lifecycle open for daily-report workflow

**Repository evidence**
- `backend/routes/daily_reports.py:377-380` defines `production`, `constraints`, and `cost_code_quantities` on the canonical daily report payload.
- `backend/routes/daily_reports.py:1127-1142` normalizes and validates cost-code actual rows against assigned project cost codes.
- `backend/routes/daily_reports.py:1254-1258` inserts the daily report and recomputes cost-code progress.
- `backend/routes/daily_reports.py:1333-1341` emits `record_created` into the Trust Spine for the `daily-report` workflow.
- `backend/lib/workflow_state_machine.py:214-280` binds daily-report closure to `payroll_inputs_verified`, proving daily reports are already part of payroll integrity governance.

**Assessment**
- This is the canonical actual-production capture path for OPPC.
- Any look-behind, actual-vs-plan, or productivity analysis must derive from this record family rather than a new production table.

### 3) Payroll and labor reconciliation spine

**Canonical owner**
- `backend/routes/payroll_variance.py`
- `backend/routes/payroll_variance_lifecycle.py`
- `backend/lib/workflow_state_machine.py`
- `backend/lib/workflow_state_events.py`

**Current responsibility**
- Weekly payroll variance ingestion from Exact CSV
- Matching payroll rows to `daily_reports.masci_crews`
- Flagging variances and missing-from-payroll cases
- Recording HR/admin decisions on variances
- Enforcing explicit review → approval → finalization lifecycle
- Writing append-only workflow state events

**Repository evidence**
- `backend/routes/payroll_variance.py:193-283` computes weekly variance using `daily_reports` as the production hour source.
- `backend/routes/payroll_variance.py:303-355` persists payroll variance batches.
- `backend/routes/payroll_variance_lifecycle.py:82-224` exposes explicit payroll variance transition, state-event, and lifecycle endpoints.
- `backend/lib/workflow_state_machine.py:294-373` defines the payroll variance state machine and its required attestations.
- `backend/lib/workflow_state_events.py:120-186` writes append-only transition evidence for governed workflows.

**Assessment**
- This is the canonical labor reconciliation base for OPPC.
- OPPC should extend it to align weekly plan, actual production, and labor drift; it must not create a separate labor variance workflow.

### 4) Tasks, actions, and notification spine

**Canonical owner**
- `backend/routes/tasks_notifications.py`

**Current responsibility**
- Shared tasks collection (`db.tasks`)
- Shared notifications collection (`db.notifications`)
- Internal services for task creation/update/comment
- Cross-role routing with project scoping and TTL retention

**Repository evidence**
- `backend/routes/tasks_notifications.py:10-17` explicitly states there are only two collections and no duplicates.
- `backend/routes/tasks_notifications.py:199-345` provides the backend-internal task service.
- `backend/routes/tasks_notifications.py:347-435` provides the backend-internal notification service.
- `backend/routes/tasks_notifications.py:574-608` establishes indexes, TTL on closed tasks, and notification expiry.

**Assessment**
- This is the canonical recovery action engine for OPPC.
- Recovery planning, missed commitments, escalation actions, and cross-functional corrective work must be represented as tasks/actions here.

### 5) Dispatch and operational resource coordination spine

**Canonical owner**
- `backend/routes/dispatch_lifecycle.py`
- `backend/routes/dispatch_continuity.py`

**Current responsibility**
- Operational current truth for assignments
- Dispatch state event stream
- Derived haul-cycle truth
- Driver/truck/project assignment state transitions
- Recovery sub-state for assignment continuity

**Repository evidence**
- `backend/routes/dispatch_lifecycle.py:7-10` defines three canonical collections: `dispatch_assignments`, `dispatch_state_events`, `haul_cycles`.
- `backend/routes/dispatch_lifecycle.py:255-357` updates assignment state, mirrors append-only dispatch events, and materializes haul cycles on completion.
- `backend/routes/dispatch_lifecycle.py:1216-1254` emits Trust Spine stages for dispatch assignment creation.
- `backend/routes/dispatch_continuity.py:440-505` governs recovery sub-state transitions and history for assignments.

**Assessment**
- This is the canonical resource-coordination engine for trucks/drivers/assignment readiness.
- OPPC resource-demand and cross-department coordination must extend this subsystem rather than invent a separate dispatch planning store.

### 6) Trust Spine and operational trust observability

**Canonical owner**
- `backend/lib/trust_spine.py`
- `backend/routes/admin_trust_spine.py`
- `backend/routes/admin_operations_trust_center.py`

**Current responsibility**
- Lifecycle event emission contract for participating workflows
- Correlation IDs and expected stages
- Read-only admin observability over per-workflow lifecycle completeness
- Derived operational trust center views

**Repository evidence**
- `backend/lib/trust_spine.py:7-39` defines the universal Trust Spine event contract.
- `backend/lib/trust_spine.py:82-151` lists expected stages by workflow, including `daily-report`, `dispatch-assignment`, and `shop-defect`.
- `backend/lib/trust_spine.py:192-289` emits append-only lifecycle events and ensures indexes.
- `backend/routes/admin_trust_spine.py:315-518` aggregates Trust Spine evidence and computes canonical workflow bands.
- `backend/routes/admin_operations_trust_center.py:1-30` declares itself a derived operational summary and not a replacement owner.

**Assessment**
- This is the mandatory observability and evidence spine for OPPC.
- Every material OPPC workflow transition must emit a Trust Spine event series or consciously extend the expected-stage contract.

### 7) Executive and cross-module operational visibility

**Canonical owner**
- `backend/routes/operations_center.py`
- `backend/routes/admin_operations_trust_center.py`

**Current responsibility**
- Shared operational cards aggregated from existing collections
- Role-aware summaries
- Executive/trust narrative composition over existing evidence

**Repository evidence**
- `backend/routes/operations_center.py:4-18` states it is an aggregator with no new source-of-truth.
- `backend/routes/operations_center.py:156-467` gathers cards from existing tasks, incidents, documents, equipment, PO, and audit signals.
- `backend/routes/admin_operations_trust_center.py:472-730` produces operator actions, subsystem views, trends, and executive narrative from existing evidence.

**Assessment**
- This is the most natural base for Monday Morning Briefing and executive OPPC summaries.
- OPPC should extend these surfaces with production-control cards instead of building a standalone briefing engine.

## OPPC capability classification matrix

| OPPC capability | Classification | Repository-backed evidence | Canonical ownership | Overlap risk | Trust Spine impact | Smallest safe implementation decision |
|---|---|---|---|---|---|---|
| WP-OPPC-02 Cost-Code Foundation Hardening | `EXTEND_EXISTING` | `backend/routes/cost_codes.py`, `backend/services/cost_codes/foundation.py`, `backend/services/cost_codes/schedule_engine.py` | Cost-code + jobs master spine | High if a new cost/planning table is created | Add/update assignment and schedule events, or extend parent project workflow evidence | Harden the existing `jobs_master.assigned_cost_codes` contract and derived schedule/progress outputs only |
| WP-OPPC-03 Rolling Two-Week Planning Lifecycle | `EXTEND_EXISTING` | `schedule_engine.py` already produces 7-day back / 7-day forward schedule windows and PM UI labels a 14-day rolling schedule | Cost-code schedule engine | High if a separate two-week planner is introduced | Add lifecycle stages for plan draft/rollover/publish as needed | Extend current schedule payload and PM workflow around the existing schedule snapshot |
| WP-OPPC-04 Weekly Rollover Engine | `NEW_CANONICAL_COMPONENT_REQUIRED` | No repository-owned rollover transaction engine found; only rolling schedule calculation exists | New OPPC service over existing cost-code/project records | Medium | Must emit Trust Spine events for rollover open, apply, and completion | Add one canonical rollover service that mutates existing project assignment/schedule fields only |
| WP-OPPC-05 Daily Actual Production Integration | `REUSE_EXISTING` | `daily_reports.py` + `normalize_cost_code_actual_rows()` + progress recompute already join actuals to cost codes | Daily Reports + Cost Codes | High if duplicate actual-capture forms or tables are added | Existing `daily-report` workflow already emits Trust Spine | Consume existing daily reports; add no new production-entry engine |
| WP-OPPC-06 Payroll and Labor Reconciliation | `EXTEND_EXISTING` | `payroll_variance.py`, `payroll_variance_lifecycle.py`, daily report closure attestation `payroll_inputs_verified` | Payroll Variance + Daily Reports | High if a second labor reconciliation flow is added | Extend governed lifecycle and add OPPC correlations | Extend variance batch outputs with project/cost-code production-control signals |
| WP-OPPC-07 Monday Look-Behind Engine | `NEW_CANONICAL_COMPONENT_REQUIRED` | Readiness flags exist, but no look-behind computation artifact exists | New OPPC analytic service over cost-code schedule + daily reports + payroll variance | Medium | Must emit lifecycle events when the look-behind packet is materialized | Build a read-model service over canonical plan/actual/labor data; do not create a second scheduler |
| WP-OPPC-08 Schedule Variance and Root-Cause Taxonomy | `NEW_CANONICAL_COMPONENT_REQUIRED` | Current schedule engine returns `schedule_status`, `slack_days`, `critical_path`, but no formal root-cause taxonomy model found | New OPPC taxonomy service over current schedule and daily constraints | Medium | Needs Trust Spine events for variance classification publication | Add canonical taxonomy fields and derived reasoning over current schedule + constraints |
| WP-OPPC-09 Recovery Planning and Tasks & Actions | `EXTEND_EXISTING` | `tasks_notifications.py` already provides shared tasks/actions; dispatch continuity shows recovery state discipline | Tasks & Notifications | High if a separate corrective action board is added | Recovery task creation/completion should emit or correlate to Trust Spine | Generate recovery work as existing tasks with OPPC source modules and project links |
| WP-OPPC-10 Resource Demand and Cross-Department Integration | `EXTEND_EXISTING` | `dispatch_lifecycle.py`, `dispatch_continuity.py`, and project performer fields already exist | Dispatch lifecycle + cost-code planned performer fields | High if a second assignment/resource registry is created | Dispatch-assignment Trust Spine exists already | Extend current assignment/resource views with OPPC demand rollups tied to project/cost code signals |
| WP-OPPC-11 Forecasting and Critical-Path Hardening | `EXTEND_EXISTING` | `schedule_engine.py` already computes forecast finish, slack, and critical path | Schedule engine | High | Add evidence around forecast recompute/materialization | Strengthen the existing deterministic forecast engine, not a new one |
| WP-OPPC-12 Production Confidence Score | `NEW_CANONICAL_COMPONENT_REQUIRED` | No OPPC confidence scorer exists; trust-score modules are platform-trust oriented, not production-control oriented | New OPPC derived score service | Medium | Must never replace Trust Spine owner truth; should emit score materialization events | Add a derived score over canonical OPPC inputs and register it as a consumer, not an owner |
| WP-OPPC-13 Monday Morning Briefing | `EXTEND_EXISTING` | `operations_center.py` and `admin_operations_trust_center.py` already aggregate and narrate operational evidence | Operations Center / Operations Trust Center | Medium | Briefing generation should be traceable to Trust Spine if persisted/dispatched | Extend existing executive summary surfaces with OPPC briefing sections |
| WP-OPPC-14 Notifications and Escalations | `EXTEND_EXISTING` | Shared notification engine already exists and supports project scoping, severity, TTL | Notifications | High | Emission chain should correlate to existing Trust Spine and source module evidence | Reuse `notification_service` and task fan-out; add OPPC-specific source modules/rules only |
| WP-OPPC-15 Permissions and Governance | `EXTEND_EXISTING` | Existing role-aware routing and PM scope checks already exist in cost codes, operations center, payroll variance, dispatch | Existing auth + role scopes | Medium | Governance transitions should be visible in Trust Spine / workflow state events | Extend current role guards and approval rules for OPPC workflows |
| WP-OPPC-16 User Experience | `EXTEND_EXISTING` | PM schedule UI, operations center UI, and existing admin surfaces are already present | Existing frontend routes | Medium | UI actions that mutate OPPC state must preserve Trust Spine/event calls | Add OPPC views into existing PM/admin routes instead of new disconnected apps |
| WP-OPPC-17 Data, Audit, Retention, and Survivability | `EXTEND_EXISTING` | Tasks TTL, notifications TTL, workflow_state_events append-only, trust_spine_events indexed; broader survivability framework already exists in repo | Existing audit + survivability systems | High | Retention/audit invariants must preserve event history | Register OPPC collections/workflows inside current audit/retention governance only |
| WP-OPPC-18 Trust Center and Operational Observability | `EXTEND_EXISTING` | Admin Trust Spine and Operations Trust Center already exist | Trust Spine + OTC | High | Direct extension of existing truth surfaces | Add OPPC cards and workflow coverage there; no second observability dashboard |
| WP-OPPC-19 Testing and Certification | `EXTEND_EXISTING` | Repo already has strong testing and certification evidence patterns | Existing test/report discipline | Low | Certification evidence should include OPPC workflow traces | Add OPPC tests and evidence packages into current test/report structure |
| WP-OPPC-20 Regression Gate | `EXTEND_EXISTING` | Existing regression culture and reports in `/app/test_reports` and backend tests | Existing CI/test conventions | Low | Regression gate should verify Trust Spine/event continuity | Extend existing regression suites with OPPC scenarios |
| WP-OPPC-21 Independent Verification | `EXTEND_EXISTING` | Existing trust and certification artifacts establish the pattern | Existing verification discipline | Low | Must independently verify OPPC lifecycle evidence | Add OPPC verification artifacts, not a separate program |
| WP-OPPC-22 Evidence Package | `EXTEND_EXISTING` | Existing memory/test report evidence-package pattern exists | Existing `/app/memory` and `/app/test_reports` evidence discipline | Low | Final evidence must include Trust Spine correlations | Produce OPPC evidence files alongside current governance artifacts |

## Architectural directives for implementation phases

1. **Authoritative schedule/cost object remains project-assigned cost codes on `jobs_master`.**
2. **Authoritative actual-production object remains `daily_reports.cost_code_quantities` plus related structured `production` and `constraints` rows.**
3. **Authoritative labor reconciliation remains payroll variance over daily report crew facts.**
4. **Authoritative action engine remains `tasks` / `notifications`.**
5. **Authoritative resource/assignment engine remains dispatch lifecycle and continuity.**
6. **Authoritative workflow evidence remains Trust Spine plus governed workflow state events where explicit state machines exist.**
7. **Executive OPPC summaries must be composed as derived views over these systems, not stored as a separate primary truth.**

## Internal validation checklist

- No secondary schedule engine proposed: **confirmed**
- No secondary cost-code registry proposed: **confirmed**
- No secondary task/action engine proposed: **confirmed**
- No secondary audit/trust engine proposed: **confirmed**
- All identified new OPPC workflows are mapped to existing Trust Spine ownership requirements: **confirmed**

## Exact WP-OPPC-02 execution sequence

1. Freeze the canonical owner set for cost-code planning:
   - `cost_code_registry`
   - `jobs_master.assigned_cost_codes`
   - ODS projection from `services.cost_codes.foundation`
2. Inventory every project-assignment field already present and mark which ones are mandatory for OPPC.
3. Harden server-side validation for assignment completeness without creating a new project-planning store.
4. Add missing canonical metadata only to the existing assignment objects when repository evidence shows a real OPPC gap.
5. Ensure every mutation path that materially changes production-control planning is governed and traceable.
6. Recompute and expose deterministic schedule/progress outputs from the existing schedule engine.
7. Add regression coverage around hardening rules before any later work packages consume them.

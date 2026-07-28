# WP-OPPC-14F Repository Discovery

Date: 2026-07-28
Scope: Operational Case Management (`WP-OPPC-14F`) extending the approved WP-14 foundation only.

## 1. Canonical service owners

- **Operational Registry / Event Catalog / Communications / Evidence / Baselines**
  - Backend owner: `/app/backend/services/operations_control/registry.py`
  - Backend owner: `/app/backend/services/operations_control/control_plane.py`
  - Admin routes: `/app/backend/routes/operations_control.py`
  - OCC UI: `/app/frontend/src/pages/OperationsControlCenter.jsx`
- **Notification acknowledgement / in-app delivery**
  - Backend owner: `/app/backend/routes/tasks_notifications.py`
- **Trust Spine**
  - Backend owner: `/app/backend/lib/trust_spine.py`
  - Admin visibility: `/app/backend/routes/admin_trust_spine.py`
- **Daily Reports (originating proof source)**
  - Backend owner: `/app/backend/routes/daily_reports.py`
  - Lifecycle owner: `/app/backend/routes/daily_report_lifecycle.py`
- **OPPC variance / recovery / forecast intelligence**
  - Backend owner: `/app/backend/services/cost_codes/oppc_intelligence.py`
  - Route owner: `/app/backend/routes/oppc_execution.py`
  - Existing linked-task creation already routes through `task_service.create(...)`
- **Production Confidence / Monday Briefings**
  - Confidence + workspace aggregation: `/app/backend/services/cost_codes/oppc_execution.py`
  - Briefings route owner: `/app/backend/routes/oppc_execution.py`
- **Tasks and Actions**
  - Canonical tasks owner: `/app/backend/routes/tasks_notifications.py`
  - Existing corrective-action/case pattern owner: `/app/backend/incident_engine/corrective_actions.py`
- **Existing Case engine patterns to reuse (do not fork blindly)**
  - Service pattern: `/app/backend/incident_engine/case_service.py`
  - State machine pattern: `/app/backend/incident_engine/state_machine.py`
  - Timeline/event pattern: `/app/backend/incident_engine/events.py`
  - Evidence pattern: `/app/backend/incident_engine/evidence.py`
  - Route/UI patterns: `/app/backend/incident_engine/routes.py`, `/app/frontend/src/pages/SafetyCaseWorkspace.jsx`, `/app/frontend/src/pages/ExecutiveCaseReport.jsx`

## 2. Relevant routes

- `/api/admin/operations-control/registry`
- `/api/admin/operations-control/events`
- `/api/admin/operations-control/communications`
- `/api/admin/operations-control/evidence`
- `/api/admin/operations-control/baselines`
- `/api/admin/operations-control/escalations/run`
- `/api/daily-reports`
- `/api/notifications`
- `/api/notifications/{notif_id}/acknowledge`
- `/api/oppc/projects/{project_number}/variance-intelligence`
- `/api/oppc/projects/{project_number}/variances/{variance_key}`
- Existing case-pattern routes already live under `/api/incident-cases/*` and `/api/corrective-actions/*`

## 3. Canonical collections / persisted stores already in use

- `daily_reports`
- `trust_spine_events`
- `operations_control_plane_events`
- `operations_control_plane_communications`
- `operations_control_plane_transport_captures`
- `operations_control_plane_evidence`
- `operations_control_plane_baselines`
- `operations_control_plane_registry_snapshots`
- `notifications`
- `operational_variance_reviews`
- existing safety-case collections:
  - `incident_cases`
  - `incident_case_events`
  - `incident_case_evidence`
  - `corrective_actions`

## 4. Existing event definitions and Trust Spine mappings

- Control-plane registry currently registers:
  - `oppc.daily_report.submitted`
  - `oppc.daily_report.pending_review`
  - `oppc.daily_report.ack_overdue`
- Control-plane communication intents currently register:
  - `oppc.daily_report.notify_project_team`
  - `oppc.daily_report.review_queue`
  - `oppc.daily_report.escalate_review_board`
- Trust Spine workflows already relevant:
  - `oppc-daily-report-proof-chain`
  - `daily-report`
  - `oppc-daily-actuals`
  - `oppc-variance-intelligence`
  - `oppc-production-confidence`
  - `oppc-monday-morning-briefing`
- Incident engine already has append-only case events under its own vocabulary, but those are safety-incident-specific and must not be treated as the operational case catalog.

## 5. Existing frontend seams worth reusing

- `SafetyCaseWorkspace.jsx`
  - proven tabbed case-detail layout
  - timeline, evidence, linked-record, corrective-action panels
- `ExecutiveCaseReport.jsx`
  - executive summary / timeline / evidence rendering pattern
- `OperationsControlCenter.jsx`
  - existing WP-14 constitutional registry panel already live
  - best drilldown insertion point for Daily Report proof chain → Operational Case

## 6. Expected extension points

1. **Registry-first extension**
   - extend `/app/backend/services/operations_control/registry.py`
   - add permanent Operational Case Principle
   - add case type catalog, case lifecycle states, case trust events, case templates, and case creation policy metadata
2. **Control-plane orchestration extension**
   - extend `/app/backend/services/operations_control/control_plane.py`
   - keep Daily Report → OPPC event emission as the origin
   - add deterministic policy evaluation for create / suppress / suggest / link / update case outcomes
3. **Operational case domain service**
   - safest location: new `services/operations_control/cases*.py` modules, borrowing incident-engine patterns without replacing incident ownership
4. **Route extension**
   - add repository-consistent `/api/operations-control/cases/*` surface (or `/api/admin/operations-control/cases/*` for admin drilldowns plus scoped portal reads where appropriate)
5. **UI extension**
   - dedicated case queue route
   - dedicated case detail route
   - OCC drilldown panel tied to persisted proof data

## 7. Duplicate-risk areas

- **Incident engine duplication risk**
  - existing `incident_engine` is a case-pattern system already; WP-14F must reuse its append-only patterns, not clone a second generic ticketing model disconnected from control-plane truth.
- **Task duplication risk**
  - must keep using `task_service.create(...)` and task collections; no case-local task table.
- **Variance / recovery duplication risk**
  - must reference `operational_variance_reviews` and OPPC workspace outputs; no new variance store.
- **Communications duplication risk**
  - must reference `operations_control_plane_communications` and `notifications`; no case-local message ledger.
- **Evidence duplication risk**
  - case packages may snapshot for certification, but live detail pages must reference canonical records and clearly label historical snapshots.
- **Narrative duplication risk**
  - case summaries must be explainable assemblies from canonical records, not a free-form parallel truth source.

## 8. Safest implementation path

1. Write the constitutional discovery + policy additions into the Operational Registry.
2. Add a new Operational Case model and lifecycle under the `operations_control` domain, reusing incident-engine patterns for IDs, append-only history, evidence items, and transition validation.
3. Store only case-owned data in the new case collection; reference canonical Daily Report / communication / variance / task / forecast / confidence / baseline records.
4. Add deterministic case-creation policy evaluation inside the control-plane event processor so repeated processing of the same originating event and policy version produces one governed outcome.
5. Assemble the case detail through a Case Assembly service that reads canonical stores on demand and labels each datum with its source and freshness (`live`, `historical snapshot`, `unavailable`).
6. Reuse existing UI patterns from `SafetyCaseWorkspace.jsx` and `ExecutiveCaseReport.jsx` to build the queue/detail/drilldown without inventing a second design language.
7. Prove the workflow with a fresh Preview-isolated Daily Report evidence record, accelerated test SLA scoped only to the proof case, and end-to-end persisted reconstruction.

## 9. Recommended proof implementation focus

- Origin: fresh Preview-only Daily Report record
- Event: registered control-plane event
- Case creation: automatic, policy-controlled, idempotent
- Case linkages to prove:
  - communication intent
  - preview capture
  - acknowledgement bridge
  - overdue escalation
  - variance link
  - recovery/task link
  - forecast/confidence impact
  - evidence package
  - baseline inclusion

This is the smallest safe extension path that completes WP-14 without replacing any canonical owner.
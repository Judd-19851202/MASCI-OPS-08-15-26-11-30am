# OPPC Trust Spine Event Map — WP-OPPC-01

## Executive Summary

- The repository already establishes a Trust Spine event contract with expected-stage logic and dashboard observability.
- Daily Reports and Dispatch Assignment creation already participate directly; Payroll Variance has a governed state-event model but is not yet listed inside the Trust Spine expected-stage contract.
- OPPC implementation must expand from this existing event architecture. It must not create a second observability or audit pipeline.

## Existing Trust Spine contract

## Classification vocabulary

- `REUSE_EXISTING`
- `EXTEND_EXISTING`
- `REPAIR_EXISTING`
- `NEW_CANONICAL_COMPONENT_REQUIRED`

**Canonical owner**
- `backend/lib/trust_spine.py`

**Repository-backed evidence**
- `trust_spine.py:7-39` defines the document contract for `trust_spine_events`.
- `trust_spine.py:50-75` defines allowed stages.
- `trust_spine.py:82-151` defines expected stage sets per workflow.
- `trust_spine.py:192-289` defines best-effort event emission and indexing.

**Current expected-stage examples**
- `daily-report`
- `dispatch-assignment`
- `shop-defect`
- several safety workflows
- `hr-request`

**Existing read-side observability**
- `backend/routes/admin_trust_spine.py:315-518` evaluates lifecycle completeness and contradictions.

## Existing repository event participation map

### 1) Daily Report

- **Classification**: `REUSE_EXISTING`
- **Repository-backed evidence**:
  - `backend/routes/daily_reports.py:1333-1341`
  - `backend/lib/trust_spine.py:83-88`
  - `backend/routes/admin_trust_spine.py:383-406`
- **Canonical ownership**: Trust Spine + Daily Reports
- **Current impact**:
  - `record_created` is emitted on submit.
  - The expected-stage contract already exists for daily-report and handles preview-vs-provider delivery terminal paths.
- **Overlap risk**: Very high if OPPC adds another lifecycle log for daily field production.
- **Smallest safe implementation decision**: Continue using the current daily-report Trust Spine lifecycle and add OPPC correlation metadata where needed.

### 2) Dispatch Assignment

- **Classification**: `REUSE_EXISTING`
- **Repository-backed evidence**:
  - `backend/routes/dispatch_lifecycle.py:1216-1254`
  - `backend/lib/trust_spine.py:136-140`
- **Canonical ownership**: Trust Spine + Dispatch Lifecycle
- **Current impact**:
  - Emits `record_created`, `routing_resolved`, `dashboard_updated`, `audit_written`, and `completed`.
  - Already models an operational non-email workflow correctly.
- **Overlap risk**: High if OPPC introduces a second resource-event stream.
- **Smallest safe implementation decision**: Extend this event lineage for resource-demand and recovery coordination features.

### 3) Payroll Variance lifecycle

- **Classification**: `EXTEND_EXISTING`
- **Repository-backed evidence**:
  - `backend/routes/payroll_variance_lifecycle.py:142-153`
  - `backend/lib/workflow_state_events.py:120-186`
- **Canonical ownership**: Workflow State Events today; Trust Spine extension recommended for OPPC visibility
- **Current impact**:
  - Explicit lifecycle transitions are captured append-only in `workflow_state_events`.
  - Not currently listed in `WORKFLOW_EXPECTED_STAGES`.
- **Overlap risk**: Medium if OPPC builds separate payroll-control tracing.
- **Smallest safe implementation decision**: Extend Trust Spine coverage or bridge reporting using the current payroll variance lifecycle rather than duplicating it.

### 4) Cost-code planning mutations

- **Classification**: `EXTEND_EXISTING`
- **Repository-backed evidence**:
  - `backend/routes/cost_codes.py:198-302`
  - No direct Trust Spine calls found in these mutation paths.
- **Canonical ownership**: Cost-code routes + Trust Spine extension required
- **Current impact**:
  - Planning changes are business-critical for OPPC but not yet visibly mapped into Trust Spine.
- **Overlap risk**: High if a separate planning audit log is introduced.
- **Smallest safe implementation decision**: Add Trust Spine emissions to canonical planning lifecycle moments instead of inventing a new event bus.

### 5) Monday look-behind / weekly rollover / confidence / briefing outputs

- **Classification**: `NEW_CANONICAL_COMPONENT_REQUIRED`
- **Repository-backed evidence**:
  - No current Trust Spine workflow entries for these OPPC-specific outputs.
- **Canonical ownership**: New OPPC workflows under the existing Trust Spine contract
- **Current impact**:
  - These capabilities do not yet exist as evented workflows.
- **Overlap risk**: Medium if implemented as silent background logic with no traceability.
- **Smallest safe implementation decision**: Register them as new OPPC workflows in `WORKFLOW_EXPECTED_STAGES` when implementation begins.

## Proposed OPPC Trust Spine workflow map

These proposals preserve the existing Trust Spine as owner and add only missing workflow subjects.

| OPPC workflow subject | Classification | Repository-backed evidence | Canonical ownership | Overlap risk | Trust Spine impact | Smallest safe implementation decision |
|---|---|---|---|---|---|---|
| `oppc-cost-code-plan` | `EXTEND_EXISTING` | Cost-code writes exist in `cost_codes.py`, but no Trust Spine events yet | Trust Spine over cost-code mutation path | High | Add event stages for plan save/publish lifecycle | Instrument existing cost-code write routes |
| `oppc-weekly-rollover` | `NEW_CANONICAL_COMPONENT_REQUIRED` | No rollover engine found | Trust Spine over new rollover service | Medium | Add new expected-stage contract | Register one new workflow subject only |
| `oppc-monday-look-behind` | `NEW_CANONICAL_COMPONENT_REQUIRED` | Readiness only; no computed workflow found | Trust Spine over look-behind materializer | Medium | Add new expected-stage contract for packet generation | Register one new workflow subject only |
| `oppc-production-variance` | `EXTEND_EXISTING` | Actuals and forecast facts exist already | Trust Spine over derived variance publication | Medium | Add publication events if persisted/dispatched | Keep variance facts derived from canonical data |
| `oppc-recovery-plan` | `EXTEND_EXISTING` | Tasks engine already exists | Trust Spine over task-generation and closeout | High | Event creation/closeout of recovery plans | Create tasks through current service and correlate them |
| `oppc-resource-coordination` | `EXTEND_EXISTING` | Dispatch and planning data already exist | Trust Spine over cross-module coordination steps | Medium | Add coordination events if a formal workflow is introduced | Reuse dispatch-assignment lineage where possible |
| `oppc-briefing` | `EXTEND_EXISTING` | Operations Center and OTC already compose summaries | Trust Spine over briefing generation/publication | Medium | Add briefing packet materialization event if persisted or sent | Extend current summary surfaces |
| `oppc-confidence-score` | `NEW_CANONICAL_COMPONENT_REQUIRED` | No current score workflow found | Trust Spine over score materialization | Medium | Add score-generation event subject without replacing owner truth | Keep derived consumer posture only |

## Stage-mapping guidance by OPPC capability

### A) Planning mutation workflow (`oppc-cost-code-plan`)

- **Classification**: `EXTEND_EXISTING`
- **Suggested stages**:
  - `record_created` or equivalent plan-save open
  - `validation_complete`
  - `routing_resolved` when approver/scope resolution matters
  - `audit_written`
  - `dashboard_updated`
  - `completed`
- **Smallest safe implementation decision**: extend `cost_codes.py` mutation path with Trust Spine calls only.

### B) Weekly rollover workflow (`oppc-weekly-rollover`)

- **Classification**: `NEW_CANONICAL_COMPONENT_REQUIRED`
- **Suggested stages**:
  - `record_created`
  - `validation_complete`
  - `audit_written`
  - `dashboard_updated`
  - `completed`
- **Smallest safe implementation decision**: event the rollover transaction over existing project planning records.

### C) Monday look-behind workflow (`oppc-monday-look-behind`)

- **Classification**: `NEW_CANONICAL_COMPONENT_REQUIRED`
- **Suggested stages**:
  - `record_created`
  - `validation_complete`
  - `audit_written`
  - `dashboard_updated`
  - `completed`
- **Smallest safe implementation decision**: event packet materialization only; keep underlying facts owned by current systems.

### D) Recovery-plan workflow (`oppc-recovery-plan`)

- **Classification**: `EXTEND_EXISTING`
- **Suggested stages**:
  - `record_created` when a recovery task bundle is opened
  - `routing_resolved` when assignees are calculated
  - `recipients_built` / `notification_queued` when notifications fire
  - `audit_written`
  - `completed`
- **Smallest safe implementation decision**: correlate existing tasks/notifications to Trust Spine rather than creating a new action log.

## Bridge rules between Trust Spine and workflow_state_events

1. Use **Trust Spine** for cross-workflow lifecycle observability of material OPPC workflows.
2. Use **workflow_state_events** where a governed state machine already exists and must remain append-only.
3. Where both exist, correlation must be by stable record id and explicit module/workflow naming.
4. Do not replace `workflow_state_events` with Trust Spine for payroll variance; extend visibility instead.

## Internal validation

- No secondary audit/event engine is proposed: **confirmed**
- Every new OPPC workflow is mapped to the existing Trust Spine owner model: **confirmed**
- Existing evented workflows remain authoritative where already implemented: **confirmed**

## Exact WP-OPPC-02 execution sequence

1. Identify every cost-code mutation endpoint to instrument.
2. Define the minimum OPPC planning workflow name and expected stages.
3. Add Trust Spine emission at the existing owner mutation path.
4. Keep event semantics best-effort and append-only, matching current Trust Spine doctrine.
5. Verify admin Trust Spine read-side can surface the new planning workflow without contradictions.

# OPPC Canonical Data Ownership — WP-OPPC-01

## Executive Summary

- The repository already shows clear ownership seams for planning, actuals, labor, tasks, dispatch resources, and trust evidence.
- The central OPPC ownership rule is: **derive new production-control views from existing owners; never move ownership away from them**.
- New OPPC components are justified only where orchestration or derived analytics are missing; they must remain consumers of canonical records, not competing sources of truth.

## Ownership rules

1. A canonical owner is the system of record for a business fact.
2. A derived OPPC component may summarize, score, or orchestrate; it may not replace the owner.
3. If a field already exists on the owner, OPPC must reuse or harden it before introducing new fields elsewhere.
4. Every material workflow change must remain traceable through Trust Spine and/or governed state events.

## Classification vocabulary

- `REUSE_EXISTING`
- `EXTEND_EXISTING`
- `REPAIR_EXISTING`
- `NEW_CANONICAL_COMPONENT_REQUIRED`

## Canonical ownership table

| Business fact | Canonical owner | Repository evidence | Classification | Overlap risk | Trust Spine impact | Smallest safe implementation decision |
|---|---|---|---|---|---|---|
| Universal cost-code definitions | `cost_code_registry` via `backend/routes/cost_codes.py` | `cost_codes.py:31, 145-174` | `REUSE_EXISTING` | High | Add eventing only if registry governance changes materially | Keep global code definitions in current registry |
| Project-assigned production-control cost codes | `jobs_master.assigned_cost_codes` | `foundation.py:336-357, 476-492` | `REUSE_EXISTING` | High | Assignment mutations should become more traceable | Keep project planning data on `jobs_master` |
| Legacy project cost-code projection | `jobs_master.cost_codes` as derived legacy compatibility view | `foundation.py:176-188, 481-483` | `REUSE_EXISTING` | Medium | None beyond source mutation traceability | Preserve as compatibility projection only |
| Project cost-code ODS projection | `services.cost_codes.foundation.sync_ods_project_cost_code_projection()` into `COLL_PROJECT_CFG` | `foundation.py:407-473` | `REUSE_EXISTING` | Medium | Derived projection should never become write owner | Continue syncing from `jobs_master.assigned_cost_codes` only |
| Schedule baseline/forecast/critical path | `services.cost_codes.schedule_engine.build_schedule_snapshot()` over assigned cost codes + progress | `schedule_engine.py:63-231` | `REUSE_EXISTING` | High | Forecast materialization should be evented when persisted or published | Keep schedule computation deterministic and derived |
| Daily production actuals by cost code | `daily_reports.cost_code_quantities` | `daily_reports.py:1133-1142`; `foundation.py:360-377` | `REUSE_EXISTING` | High | Existing daily-report workflow already emits Trust Spine | Keep actual quantities inside daily reports |
| Daily structured production narrative | `daily_reports.production` | `daily_reports.py:377-379` | `REUSE_EXISTING` | Medium | Existing daily-report workflow | Reuse in OPPC analysis; no new daily production table |
| Daily constraints / delay facts | `daily_reports.constraints` | `daily_reports.py:377-379, 1127-1131` | `REUSE_EXISTING` | Medium | Existing daily-report workflow | Reuse for variance taxonomy |
| Daily crew labor hours | `daily_reports.masci_crews` | `payroll_variance.py:201-225` | `REUSE_EXISTING` | High | Daily-report lifecycle + payroll closure attestation | Keep crew-hour truth on daily reports |
| Weekly payroll variance batch | `payroll_variance_batches` | `payroll_variance.py:319-355` | `REUSE_EXISTING` | High | Lifecycle/state-event integration already exists | Extend current batch outputs for OPPC consumption |
| Weekly payroll variance lifecycle evidence | `workflow_state_events` for workflow `payroll_variance` | `payroll_variance_lifecycle.py:142-153`; `workflow_state_events.py:120-186` | `REUSE_EXISTING` | Low | Already canonical | Reuse for labor governance |
| Shared recovery / corrective tasks | `tasks` | `tasks_notifications.py:10-17, 199-345` | `REUSE_EXISTING` | Very high | Add source-module and correlation linkages | Use existing tasks for OPPC recovery work |
| Shared notification delivery | `notifications` | `tasks_notifications.py:347-435, 574-608` | `REUSE_EXISTING` | High | Notification-producing OPPC workflows should correlate upstream | Use existing notification fan-out only |
| Dispatch operational current truth | `dispatch_assignments` | `dispatch_lifecycle.py:7-10, 312-357` | `REUSE_EXISTING` | High | Dispatch create already emits Trust Spine; other transitions may need more coverage | Reuse for resource coordination |
| Dispatch transition event truth | `dispatch_state_events` | `dispatch_lifecycle.py:320-343` | `REUSE_EXISTING` | Medium | Can be correlated with Trust Spine | Reuse for operational chronology and resource analysis |
| Completed haul-cycle summary truth | `haul_cycles` | `dispatch_lifecycle.py:345-350, 954-1039` | `REUSE_EXISTING` | Medium | Derived from dispatch state completion | Reuse for production/resource throughput views |
| Dispatch recovery sub-state | `dispatch_assignments.recovery_state` + `recovery_history[]` | `dispatch_continuity.py:440-505` | `REUSE_EXISTING` | Medium | Recovery transitions should remain auditable | Reuse when OPPC recovery touches assignments |
| Workflow lifecycle observability | `trust_spine_events` | `trust_spine.py:17-39, 192-289` | `REUSE_EXISTING` | Very high | Canonical owner | All OPPC workflows must map here |
| Platform/operational trust rollup | `admin_trust_spine` and `admin_operations_trust_center` as derived consumers | `admin_trust_spine.py:315-518`; `admin_operations_trust_center.py:1-30` | `REUSE_EXISTING` | High | Must never be replaced by OPPC-specific owner | Extend existing observability surfaces only |
| Executive operations summary cards | `operations_center` derived cards | `operations_center.py:4-18, 156-467` | `REUSE_EXISTING` | Medium | Add OPPC summary cards with traceable sources | Extend current derived summary surface |

## Bounded new canonical components allowed by repository evidence

These are legitimate missing capabilities, but they must remain consumers of current owners.

### 1) OPPC weekly rollover service

- **Classification**: `NEW_CANONICAL_COMPONENT_REQUIRED`
- **Why allowed**: no canonical rollover transaction engine was found.
- **Owner relationship**: consumes and mutates `jobs_master.assigned_cost_codes`; does not own a second schedule table.
- **Trust Spine impact**: must emit rollover lifecycle events.
- **Smallest safe decision**: service + route layer only.

### 2) OPPC Monday look-behind materialization service

- **Classification**: `NEW_CANONICAL_COMPONENT_REQUIRED`
- **Why allowed**: readiness markers exist, but no computed packet exists.
- **Owner relationship**: consumes schedule, daily reports, payroll variance, and tasks.
- **Trust Spine impact**: must emit materialization and briefing-ready events if persisted/published.
- **Smallest safe decision**: derived read model and summary artifact only.

### 3) OPPC variance taxonomy service

- **Classification**: `NEW_CANONICAL_COMPONENT_REQUIRED`
- **Why allowed**: no formal root-cause taxonomy owner was found.
- **Owner relationship**: classifies existing delay/actual/forecast/labor facts; does not replace them.
- **Trust Spine impact**: taxonomy publication/adjudication should be evented.
- **Smallest safe decision**: shared taxonomy rules and derived classification output.

### 4) OPPC production confidence scorer

- **Classification**: `NEW_CANONICAL_COMPONENT_REQUIRED`
- **Why allowed**: no production-control confidence score exists in the repository.
- **Owner relationship**: must be a derived consumer only, distinct from platform trust score ownership.
- **Trust Spine impact**: score creation should be attributable and non-deceptive.
- **Smallest safe decision**: derived score output over canonical OPPC inputs.

## Ownership anti-patterns prohibited

1. A new `oppc_schedules` collection owning schedule truth.
2. A new weekly-planning grid that does not write back to `jobs_master.assigned_cost_codes`.
3. A second production actuals table duplicating `daily_reports.cost_code_quantities`.
4. A standalone recovery/corrective-action system outside `tasks`.
5. A second trust/audit event stream parallel to `trust_spine_events` or `workflow_state_events`.
6. A resource planning store that duplicates dispatch assignment truth.

## Internal validation

- No business fact in this register has more than one proposed owner: **confirmed**
- Every bounded new canonical component is a consumer/orchestrator over current owners: **confirmed**
- No secondary engine is proposed for schedule, cost code, daily actuals, tasks, notifications, dispatch, or trust evidence: **confirmed**

## Exact WP-OPPC-02 execution sequence

1. Treat `jobs_master.assigned_cost_codes` as non-negotiable owner truth.
2. Enumerate missing mandatory planning metadata directly on that owner.
3. Harden owner validation and normalization first.
4. Keep ODS projections and schedule snapshots derived.
5. Add tests proving ownership is still singular after hardening.

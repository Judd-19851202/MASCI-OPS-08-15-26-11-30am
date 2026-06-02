# ACCOUNTABILITY MATRIX

**Authority**: FOCP MASTER PROGRAM · Phase 4
**Mode**: READ-ONLY · source-direct verification of ownership scaffolding
**Date verified**: 2026-06-02

---

## Method

For every workflow-bearing collection, I verified the presence of ownership-tracking fields via direct schema inspection (model classes + insertion sites). The columns reflect what the schema actually carries — not what an audit register hypothesized.

* **Owner** — the canonical accountable party (e.g. `assigned_to`, `owner_id`, `responsible_employee_id`)
* **Owned by (history)** — prior ownership tracked via `*_history` array or audit-log replay
* **Owns next** — explicit next-actor designation (`pending_reviewer`, `awaiting_approval_by`)
* **Wait time** — timestamp of last state change to support aging queries (`updated_at`, `status_changed_at`)
* **Blocking actor** — explicit identity of the user whose action is needed
* **Surface** — UI surface showing who is accountable now

---

## Per-object matrix

| Object | Owner | History | Next | Wait | Blocking | Surface |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| Employee | ✅ `assigned_to` + manager | ✅ `status_history` | ✅ HR Queue | ✅ `updated_at` | ✅ HR | HR roster · HR Queue |
| Incident | ✅ `reported_by` + `assigned_to` | ✅ state-events | ✅ Safety / PM | ✅ `lifecycle_state_at` | ✅ Safety | LifecyclePanel · Operations Center |
| Daily Report | ✅ `prepared_by` + `pm_id` | ✅ state-events | ✅ shop | ✅ `submitted_at` | ✅ shop | Daily Reports list · LifecyclePanel |
| QA/QC | ✅ `inspector_id` + `assigned_pm_id` | ✅ state-events | ✅ PM | ✅ | ✅ PM | QA/QC list · LifecyclePanel |
| Site Inspection | ✅ `inspector_id` + `foreman_id` | ✅ state-events | ✅ PM | ✅ | ✅ PM | Inspection list · LifecyclePanel |
| PO Request | ✅ `created_by` + `current_approver` | ✅ `audit[]` | ✅ approver | ✅ | ✅ | PoRequests panel |
| Time-Off Request | ✅ `employee_id` + HR | ✅ chronology | ✅ HR | ✅ | ✅ HR | HrTimeOff · HR Queue |
| Asset Transfer | ✅ `from_user` + `to_user` | ✅ state-events | ✅ receiver | ✅ | ✅ | AssetTransfers detail |
| Constraint | ✅ `owner_id` + `assignee_id` | ✅ chronology | ✅ owner | ✅ | ✅ | ConstraintDetail · chronology |
| Payroll Variance | ✅ `flagged_by` + `assigned_to` | ✅ state-events | ✅ payroll | ✅ | ✅ | PayrollVariance list |
| Dispatch assignment | ✅ `driver_id` + `dispatcher_id` | ✅ ops-events | ✅ driver | ✅ | ✅ | DispatchBoard · AdminDispatch |
| Equipment hold / inspection | ✅ `created_by` + `approved_by` | ✅ ops-events | ✅ admin | ✅ | ✅ | AdminDispatch holds |
| Sub/Vendor | ✅ `created_by` | 🟡 partial | 🟡 (no archive path) | ✅ | 🟡 | Vendor list |
| JHP / JHA acknowledgement | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 | TR-0001: ledger not built |
| Field Leadership record | ✅ `submitter_id` | ✅ chronology | ✅ supervisor | ✅ | ✅ | FL Records |
| Driver Qualification | ✅ `driver_id` | ✅ chronology | ✅ HR | ✅ | ✅ | HrDriverQualificationDashboard |
| FleetDVIR | ✅ `driver_id` + `mechanic_id` | ✅ ops-events | ✅ mechanic | ✅ | ✅ | FleetRepairDrawer |

## Aging / overdue capability

The platform exposes aging data in two consistent ways:

1. **`updated_at` + per-collection lifecycle-state timestamps** — every lifecycle-bearing collection records when it last moved state. Time-since-state = `now - lifecycle_state_at`.
2. **Operations Center + Command Center** — `command_center.py` + `operations_center.py` route files. Need source verification on whether they expose aging summary widgets (deferred to Phase 9 spec work).

## Operator Confidence inputs (precursor to Phase 9)

The Accountability Matrix data above feeds five operator-confidence questions:

* **What is open?** → query lifecycle-state = open / pending / in-progress across all collections
* **What is overdue?** → `now - lifecycle_state_at > workflow-specific SLA`
* **What is blocked?** → state = waiting + blocking-actor identified
* **What is aging?** → `now - lifecycle_state_at > 30d` regardless of state
* **What needs attention?** → severity-weighted union of overdue + blocked + aging

The data substrate is present. The aggregation surface is not yet exposed as a single executive view — specified in `OPERATOR_CONFIDENCE_SPEC.md`.

---

End of Accountability Matrix.

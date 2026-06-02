# OPERATOR CONFIDENCE SPECIFICATION

**Authority**: FOCP MASTER PROGRAM · Phase 9
**Mode**: SPEC · single executive-confidence model
**Inputs**: `ACCOUNTABILITY_MATRIX.md` + `WORKFLOW_COMPLETENESS_REGISTER.md`

---

## The five questions

Every operator confidence view answers, at a glance, these five questions in this order:

1. **What is OPEN?** — Records in any non-terminal state.
2. **What is OVERDUE?** — Records whose `now - last_state_change > workflow-specific SLA`.
3. **What is BLOCKED?** — Records explicitly waiting on a known actor.
4. **What is AGING?** — Records whose `now - last_state_change > 30 days` regardless of state.
5. **What needs ATTENTION?** — Severity-weighted union of overdue + blocked + aging.

Every operator persona (PM · Safety · HR · Payroll · Superintendent · Executive · Admin) sees the same five questions, filtered by role-relevance.

## UI surface · `/operations-center/confidence` (or extension of existing `command_center.py`)

A single page with five stacked panels — one per question — each rendering:

* Top-line count
* Severity breakdown (CRITICAL · HIGH · MEDIUM · LOW)
* Top-5 list of the actual records driving the count
* Drill-down link to the canonical detail page

### Panel · WHAT IS OPEN

* Source: union query across all lifecycle-bearing collections where `lifecycle_state NOT IN (terminal_states)`
* Severity assignment: workflow-specific (Incident = HIGH, PO = MEDIUM, Equipment Inspection = LOW, etc.)
* Filter: by role-relevance (PM sees PM-owned; Safety sees Safety-owned; Executive sees all)

### Panel · WHAT IS OVERDUE

* Source: open records where `now - last_state_change > SLA_for_workflow[state]`
* Workflow-specific SLAs (proposed defaults):
  * Incident open without `in_review` transition · 2 business days
  * Daily Report submitted without PM review · 1 business day
  * QA/QC `DEFICIENCY_RAISED` without re-inspection scheduled · 5 business days
  * PO Request submitted without first-approval · 3 business days
  * Time-Off Request submitted without HR decision · 2 business days
  * Constraint `open` or `monitoring` without resolution · 14 business days (configurable per project)
  * JHP version issued without ack from required role · 5 business days (TR-0001 dependency)
* SLAs configurable per tenant in the `tenant_config` collection (Customer #2 readiness pre-work).

### Panel · WHAT IS BLOCKED

* Source: records where `next_actor_id IS NOT NULL` AND `now - state_change > 24h`
* Identifies the blocking actor by name + role.
* Bulk action: "Nudge blocker" → fires a notification email + in-app banner to the blocker.

### Panel · WHAT IS AGING

* Source: records where `now - last_state_change > 30 days` regardless of state
* Even closed records appear if they have not been reviewed or audited in 30 days.
* Sorts by age descending — oldest first.

### Panel · WHAT NEEDS ATTENTION

* Aggregate score per record:
  * +3 if CRITICAL severity
  * +2 if HIGH
  * +1 if MEDIUM
  * +1 if overdue
  * +1 if blocked > 24h
  * +1 if aging > 30d
* Top-N records by score · grouped by responsible-actor for one-click triage.

## Per-role default views

| Role | Default filter |
|---|---|
| Executive | all severities · top-30 aging + attention items · cross-workflow |
| PM | PM-owned records · all 5 panels |
| Safety | Safety-owned + Incident + JHP + Driver Qual + Constraint |
| HR | Employee + Time-Off + Payroll Variance |
| Payroll | Payroll Variance + Time-Off |
| Superintendent | Daily Report + Site Inspection + Constraint (project-scoped) |
| Dispatch | Dispatch assignment + asset transfers + driver qual |
| Admin | unfiltered |

## Refresh model

* Server-rendered every 60 s (existing `command_center.py` cadence)
* Manual refresh button
* Real-time toast push when a record on the user's view moves to CRITICAL/HIGH attention score

## Closes

* OPERATOR_CONFIDENCE per-role visibility gap
* Multi-finding "what's actually waiting on me?" friction
* Pre-work for TR-D002 / TR-D003 Customer #2 simulation: a 1-page surface that does NOT require Jaymn to interpret

## Effort estimate

* Backend aggregator + per-workflow SLA config: **5 – 7 days**
* Frontend 5-panel page + role filters + drill-down: **5 days**
* Tests + observability: **3 days**
* **Total**: **~ 2.5 sprint weeks**

## Dependencies

* `tenant_config` SLA configuration (light-touch; depends partly on Customer #2 readiness Phase A)
* Status Canonical Dictionary (TR-0005) — for consistent badge labels in the confidence view

---

End of Operator Confidence Spec.

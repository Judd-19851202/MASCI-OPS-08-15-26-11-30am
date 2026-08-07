# WP-18C8 Authority and Lineage Map

## Runtime entry points

- PM screen: `/pm/project-controls/earned-value?project_number={project_number}`
- Executive/Admin screen: `/admin/governance/project-controls/earned-value?project_number={project_number}`
- PM API: `/api/pm/project-controls/projects/{project_number}/earned-value`
- Executive/Admin API: `/api/admin/governance/project-controls/projects/{project_number}/earned-value`
- PM/Admin CSV export: same route family with `/export`
- Version capture: same route family with `/snapshots`

## Source-to-metric lineage

| Output | Primary source | Secondary lineage | Final owner |
|---|---|---|---|
| BAC | Active budget version + active budget lines | C3 totals, line financial rollups | `project_budget_authority` |
| PV | Baseline schedule activities | C4 baseline version linkage | `project_schedule_authority` |
| EV | Approved quantity from schedule actual candidates; fallback approved physical percent | Work-block ledger, active budget line linkage | `project_earned_value_engine` |
| AC | Approved actual-cost candidate allocations to budget lines | Receipt review trust line, budget line rollups | `project_budget_authority` |
| ETC | C7 cost remaining-work forecast | Unit-level allocation to active lines | `project_forecasting_commitments` consumed by C8 |
| EAC | AC + ETC with commitment floor safety | Approved commitment allocations | `project_earned_value_engine` |

## Collections touched by C8

Read:
- `jobs_master`
- `project_budget_versions`
- `project_budget_lines`
- `project_budget_review_queue`
- `project_budget_commitment_candidates`
- `project_budget_actual_cost_candidates`
- `project_schedule_versions`
- `project_schedule_activities`
- `project_schedule_work_packages`
- `project_schedule_actual_candidates`
- `project_controls_work_ledger`
- C7 forecasting collections via the existing service

Write:
- `project_earned_value_snapshots`
- `project_earned_value_versions`
- `project_budget_commitment_candidates` (review preservation / approval)
- `project_budget_actual_cost_candidates` (review preservation / approval)
- `project_budget_lines` (commitment + actual-cost rollups)
- `project_budget_versions` (aggregate totals refresh)

## Versioning and audit

- Every refreshed C8 snapshot can persist a fingerprinted version row.
- Repeated reads do not create duplicate versions unless the governed payload changed or the operator captured a new note.
- Audit events are written through the existing project-controls audit path for:
  - snapshot refresh
  - version capture
  - export
  - candidate review changes

## Evidence drill-down path

Operators can drill from:
- earned-value workspace -> line table / metric table
- line table -> budget review lane
- budget review lane -> candidate allocation evidence
- schedule actual lineage -> approved candidate IDs + work-block / report IDs

## Truth boundary notes

- C8 never mutates C7 forecast lifecycle logic.
- C8 never overwrites original daily report facts.
- C8 never marks receipt review as ERP truth.
- C8 never auto-greenlights stale or blocked evidence.
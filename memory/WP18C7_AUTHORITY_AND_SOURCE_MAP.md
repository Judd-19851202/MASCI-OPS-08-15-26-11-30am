# WP18C7 Authority and Source Map

| Domain | Authority | Source collections / engines | C7 use |
|---|---|---|---|
| Schedule forecast | `cost_codes.schedule_engine` | assignment rows, cost code actuals, forecast override history | likely finish, committed finish, slips, scenarios |
| Production forecast | `project_operational_intelligence` | work blocks, daily reports, quantity rollups, timeline metrics | next day/week pace, remaining quantities |
| Resource forecast | `project_operational_intelligence` | crew/equipment/material/vendor productivity rollups | likely next-week support/capacity |
| Cost exposure | `project_operational_intelligence` + `project_budget_authority` | cost metrics, commitment candidates, actual-cost candidates | projected remaining cost and exposure |
| Commitments | `project_forecast_commitments` + PO commitment candidates | manual operator commitments + preserved PO commitments | lifecycle, commitment-vs-actual |
| Actuals | `project_schedule_actuals_spine` | approved actual candidates, forecast rows, review context | reconciliation only |
| Constraints | `operational_constraints` | active constraints | forecast drivers and risk pressure |
| Versioning | `project_forecasting_snapshots` | fingerprinted C7 workspace snapshots | version history and change detection |

## Forbidden duplications
- No second executive forecast engine.
- No forecast-to-commitment conversion.
- No alternate manual KPI registry for C7.

## Audience routes
- PM: `/pm/project-controls/forecasting`
- Executive/Admin: `/admin/governance/project-controls/forecasting`
- Field Leadership: `/field-leadership/portal/forecasting`

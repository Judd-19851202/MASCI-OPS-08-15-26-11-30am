# WP-18A Executive System Architecture Map

Date: 2026-08-03

## 1) Architecture intent discovered in source
The current system already behaves like a layered project-controls platform with explicit separation between:

- canonical operating records,
- derived analytics / projections,
- project-control workflows,
- dashboards / recap / briefing consumers,
- governance / manual fallback overlays.

## 2) Layered map

```text
LAYER A · Canonical operating records
  jobs_master
  daily_reports
  project_team_assignments
  cost_code_registry
  operational_constraints

        ↓ normalize / project / aggregate / recompute

LAYER B · Derived stores and embedded history
  project_operational_config
  operational_facts
  operational_kpi_snapshots
  jobs_master.oppc_planning_lifecycle
  jobs_master.oppc_forecast_history / overrides / confidence_history / monday_reviews
  oppc_monday_briefings
  operational_intelligence_history / audit
  project_identity_conflicts

        ↓ route + service orchestration

LAYER C · Workflow engines and APIs
  PM scoped jobs
  project team / staffing summary
  cost-code registry + assignment routes
  schedule engine + forecast + weekly rollover
  Daily Report canonical APIs
  ODS APIs and ODS intelligence APIs
  OPPC execution + OPPC briefings + executive ops center
  PM command center
  legacy operational-intelligence digest engine
  import/export fallback routes

        ↓ role-specific consumers

LAYER D · Operator and executive surfaces
  /pm/project-staffing
  /pm/project-schedule
  /pm/monday-review
  /pm/command-center
  /pm/operational-intelligence
  /admin/project-staffing
  /admin/cost-registry
  /admin/project-identity
  /admin/operational-intelligence
  /admin/executive-operational-intelligence
  /daily/submit, /daily-reports, /pm/daily, /admin/daily
  Safety Daily Report projection

        ↓ governance / executive interpretation

LAYER E · Decision and oversight overlays
  project identity drift queue
  operational constraints registry
  project health summaries
  executive ODS attention / confidence views
  Monday morning briefings
```

## 3) Strongest current source-of-truth lines

### Project identity
`jobs_master`  
→ PM jobs / selector, staffing, schedule, identity governance, project health, confidence

### Field actual production
`daily_reports`  
→ cost-code actuals  
→ schedule / OPPC  
→ ODS facts / snapshots  
→ PM/Admin/Executive intelligence

### Explicit team ownership
`project_team_assignments`  
→ project roster APIs  
→ staffing summary and team consumers

### Reusable code definition
`cost_code_registry`  
→ assignment normalizer  
→ project-assigned execution rows

## 4) Most important derivative lines

### Project controls derivative line
`jobs_master.assigned_cost_codes` + `daily_reports.cost_code_quantities`  
→ progress snapshot  
→ schedule snapshot  
→ forecast / planning lifecycle  
→ Monday review  
→ briefing / executive rollup

### Analytics derivative line
canonical operational records  
→ `operational_facts` / `operational_kpi_snapshots`  
→ ODS PM/Admin/Executive dashboards

### Communications derivative line
project-control and intelligence aggregators  
→ `oppc_monday_briefings` / `operational_intelligence_history` / `operational_intelligence_audit`  
→ recap / digest / PDF / dispatch consumers

## 5) Architectural stress points
1. `jobs_master` carries both canonical project identity and multiple embedded OPPC histories.
2. Intelligence exists in at least three families: OPPC recap, ODS dashboards, legacy operational-intelligence products.
3. Constraints are persisted, but automatic downstream connection is not yet proven.
4. Manual import/export fallback is honest and usable, but should not be mistaken for a live provider-sync backbone.

## 6) Architecture implication for WP-18B
- Preserve canonical truth on the existing stores.
- Preserve Daily Reports as a primary actuals source.
- Use the cost-code/schedule/OPPC spine as the main project-controls workflow foundation.
- Connect constraints, executive KPIs, and planning lifecycle more explicitly.
- Consolidate overlapping intelligence lanes instead of creating a new one.

## Executive conclusion
The system architecture already exists in layered form. WP-18B should be an exercise in **formalization, connection, and consolidation** — not greenfield invention.
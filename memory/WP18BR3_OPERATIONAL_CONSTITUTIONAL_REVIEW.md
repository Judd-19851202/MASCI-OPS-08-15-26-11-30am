# WP18BR3 Operational Constitutional Review

Date: 2026-08-03

## Executive question

Do scheduling, resource loading, Daily Reports, dispatch, equipment, safety, quality, HR, shop, project management, and executive reporting already connect into one operational model?

## Executive answer

**Mostly yes.**

BR3 does not find a fragmented platform that needs to be reassembled from scratch. It finds a platform with a real operational model whose main weaknesses are:

1. some federated semantics are still implicit
2. executive/read-side overlap is higher than it should be
3. finance authority is less mature than operations authority

After C5, one more standing constitutional reading is explicit: the future platform must build operational intelligence and a digital twin, not merely add storage lanes.

That rule is codified in the **WP-18 Operational Intelligence Constitution**.

It is now complemented by the **WP-18 Operational Decision Engine Constitution**, which requires later packages to convert connected operations into governed decision flow, measurable outcomes, and learning feedback.

## What already connects correctly

### Scheduling and planning

- cost-code planning persists on `jobs_master.assigned_cost_codes`
- schedule is computed from assignments, progress, and overrides
- forecast and planning lifecycle already sit on that same path

Evidence: `backend/routes/cost_codes.py:363-520,760-920`; `backend/services/cost_codes/schedule_engine.py:211-540`

### Production and field reporting

- Daily Reports store cost-code quantities, crew hours, equipment, materials, and field narratives
- downstream schedule/progress logic already consumes those facts

Evidence: `backend/routes/daily_reports.py:1421-1664`; `backend/services/cost_codes/foundation.py:658-675`

### HR / labor / compliance

- HR has dedicated routes and portals for payroll variance, time verification, time-off, training, qualifications, and employees
- payroll variance already forms a governed weekly reconciliation lane

Evidence: `frontend/src/app/routing/AppRoutes.jsx:1039-1080,1270-1290`; `backend/routes/payroll_variance.py:1-22,193-280`

### Shop / equipment / maintenance

- shop has its own hub, manager queue, assignments, PM schedules, work orders, asset care, and equipment routes
- Asset Spine remains the clearest equipment registry core

Evidence: `frontend/src/app/routing/AppRoutes.jsx:982-1030`; `backend/routes/asset_spine.py:223-259`

### Dispatch / transportation operations

- dispatch has dedicated login, hub, board, command center, fleet, map, haul ledger, and driver-qualification surfaces
- dispatch surfaces explicitly reuse the existing dispatch command APIs rather than inventing duplicates

Evidence: `frontend/src/app/routing/AppRoutes.jsx:1153-1192`; `frontend/src/pages/DispatchHubV2.jsx:9-20,74,166-184`; `frontend/src/components/dispatch/command/commandApi.js:50-57`

### Safety / quality / field leadership

- safety portal has incidents, audits, documents, training, trench-safety, inspections, and digest/reporting routes
- QA/QC and field leadership also have dedicated operating surfaces

Evidence: `frontend/src/app/routing/AppRoutes.jsx:530-575,661-675,1103-1147`

### Project management

- PM has a hub, schedule, Monday review, command center, jobs, staffing, team, field leadership, daily, incidents, meetings, inspections, equipment, photos, and safety routes

Evidence: `frontend/src/app/routing/AppRoutes.jsx:873-977`

## What does not yet connect cleanly enough

### 1. Resource loading is federated, not singular

Demand, roster, and dispatch deployment already exist, but they are still spread across planning, team assignments, and dispatch lanes.

Evidence: `backend/services/cost_codes/foundation.py:173-191`; `backend/routes/project_team_assignments.py:878-1160`; `frontend/src/app/routing/AppRoutes.jsx:1153-1192`

### 2. Constraint truth is dual-lane

Daily field constraints and standing blocker management both exist. That is not wrong, but it must be explicitly governed.

Evidence: `backend/routes/daily_reports.py:7-8`; `backend/routes/operational_constraints.py:7-19,67-121`

### 3. Executive reporting is operationally useful but semantically overlapping

ODS, Project Health, KPI rollups, executive overview, and legacy operational intelligence all surface adjacent truths.

Evidence: `backend/routes/ods_intelligence.py:71-123,312-494`; `backend/routes/project_health.py:4-7`; `backend/routes/operational_kpis.py:138-152`; `frontend/src/app/routing/AppRoutes.jsx:702-703,930-931,1369-1379`

## Operational constitutional determination

| Domain | BR3 answer |
|---|---|
| Scheduling | Preserve and extend |
| Resource loading | Consolidate semantics |
| Daily Reports | Preserve with minor refinement |
| Dispatch | Preserve with minor refinement |
| Equipment | Extend existing Asset Spine-centered architecture |
| Safety | Preserve and extend |
| Quality | Preserve |
| HR | Preserve and extend |
| Shop | Preserve and extend |
| Project management | Preserve and extend |
| Executive reporting | Redesign hierarchy, not upstream truth owners |

## BR3 operational conclusion

The operational platform is already a real system, not a loose collection of modules.  
The work ahead is constitutional tightening, not wholesale operational redesign.

Every later package must therefore make the platform smarter, reduce duplicate entry, and increase executive visibility before it can receive GO.

Every later package must also improve decision quality, explanation quality, or measurable operational outcomes before it can receive GO.
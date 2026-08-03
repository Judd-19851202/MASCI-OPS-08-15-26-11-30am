# WP18B Project Controls Readiness Audit

Date: 2026-08-03  
Work Package: WP-18B — Executive Architecture Authority Audit  
Scope rule: Documentation, evidence, and constitutional architecture only. No application, UI, API, workflow, database, configuration, business-logic, or model changes were performed.

## Executive conclusion

The platform already contains **10 of the 12 executive-requested Project Controls domains** in reusable or extendable form. Only **2 of 12 domains** lack repository-backed constitutional ownership in the audited evidence set: **Budget Hierarchy** and **Earned Value**.

### Disposition summary across the 12 constitutional domains

- **REUSE:** 1/12
- **EXTEND:** 8/12
- **CONSOLIDATE:** 1/12
- **BUILD_NEW:** 2/12

### Denominator reconciliation

WP-18A reported `BUILD_NEW = 0` across the already-audited existing capability denominator. That remains true for the **existing capabilities** set. WP-18B adds two **executive-requested constitutional domains** that were not evidenced as existing architectural owners or engines in the repository-backed audit set:

1. Budget Hierarchy
2. Earned Value

These are the only domains where **BUILD_NEW** is evidence-supported.

## Constitutional domain findings

### 1) Project-specific Cost Codes
- **Existing owner:** `jobs_master.assigned_cost_codes`
- **Producer:** PM/admin assignment update actions over reusable cost-code definitions
- **Consumers:** schedule engine, forecast, OPPC, derivative ODS configuration
- **Storage:** `jobs_master.assigned_cost_codes`
- **APIs / engines:** `backend/routes/cost_codes.py`, `backend/services/cost_codes/foundation.py`
- **Trust lines:** Registry → Assignment is complete; Assignment → Schedule is complete; Assignment → ODS projection remains derivative-only
- **Dependencies:** `cost_code_registry`, `daily_reports.cost_code_quantities`, project identity on `jobs_master`
- **Existing reusable engines:** `cost_code_registry`, `foundation.py`, `cost_codes.py`
- **Current maturity:** High
- **Architectural gap:** the registry/template role, project-assignment role, and derivative projection role are real but not yet constitutionally locked in one artifact
- **Evidence source:** `WP18A_COST_CODE_FORENSIC_AUDIT.md`, `WP18A_DATA_AND_TRUST_LINE_REGISTER.csv:T05-T07`
- **Confidence level:** High
- **Architectural impact:** This is the planning spine for schedule, forecast, and production reconciliation
- **Recommended disposition:** **EXTEND**

### 2) Schedule hierarchy
- **Existing owner:** deterministic schedule payload derived by `schedule_engine.py`
- **Producer:** `schedule_engine.py` over `jobs_master.assigned_cost_codes` and Daily Report actuals
- **Consumers:** PM schedule workspace, Monday review workspace, Monday briefing generation
- **Storage:** derived payload only; no second schedule store was evidenced
- **APIs / engines:** `/api/cost-codes/projects/{project_number}/schedule`, `backend/services/cost_codes/schedule_engine.py`
- **Trust lines:** Assignment → Schedule is complete; Actuals → Schedule is complete; Constraints → Schedule is weak
- **Dependencies:** project cost-code assignments, Daily Report actuals, forecast overrides
- **Existing reusable engines:** `schedule_engine.py`, schedule routes in `cost_codes.py`
- **Current maturity:** High
- **Architectural gap:** hierarchy semantics are real but not yet expressed as the constitutional schedule stack
- **Evidence source:** `WP18A_SCHEDULE_FORENSIC_AUDIT.md`, `OPPC_FORECASTING_CRITICAL_PATH_CERTIFICATION.md`
- **Confidence level:** High
- **Architectural impact:** Rebuilding this would duplicate one of the strongest existing engines
- **Recommended disposition:** **EXTEND**

### 3) Budget hierarchy
- **Existing owner:** none proven in the audited evidence package
- **Producer:** none proven
- **Consumers:** adjacent only — PM Financials & Cost navigation, `ProjectHealth`, `po_requests`
- **Storage:** none proven as a budget hierarchy store
- **APIs / engines:** none proven as a budget hierarchy engine
- **Trust lines:** missing
- **Dependencies:** project identity, cost-code assignments, future budget baselines, procurement/change inputs
- **Existing reusable engines:** adjacency only — `po_requests.py`, `project_health.py`, PM financial navigation
- **Current maturity:** Absent as a constitutional control domain
- **Architectural gap:** no canonical budget owner, hierarchy, storage contract, or API family was evidenced
- **Evidence source:** `frontend/src/components/pm/sidebar/domainMap.js:42-51`, `WP17A_KPI_SOURCE_MAP.md:24`, `backend/routes/operational_kpis.py:16-17`, repository search executed 2026-08-03
- **Confidence level:** High
- **Architectural impact:** This is one of the rare areas where the platform cannot truthfully claim existing architectural ownership
- **Recommended disposition:** **BUILD_NEW**

### 4) Rolling Two-Week Lookahead
- **Existing owner:** `jobs_master.oppc_planning_lifecycle`
- **Producer:** planning-lifecycle publish/apply actions in the cost-code / OPPC schedule path
- **Consumers:** PM schedule workspace, Monday review readiness, OPPC planning workflows
- **Storage:** `jobs_master.oppc_planning_lifecycle`
- **APIs / engines:** `backend/routes/cost_codes.py`, `backend/services/cost_codes/foundation.py`
- **Trust lines:** present but under-labeled; lifecycle → operator discoverability is weak
- **Dependencies:** project-specific cost-code assignments, schedule hierarchy, Monday review semantics
- **Existing reusable engines:** planning lifecycle state, weekly rollover behavior, PM schedule workspace
- **Current maturity:** Medium
- **Architectural gap:** the lookahead capability exists but is embedded rather than constitutionally named
- **Evidence source:** `WP18A_LOOKAHEAD_AND_WEEKLY_RECONCILIATION_AUDIT.md`, `WP18A_DATA_AND_TRUST_LINE_REGISTER.csv:T10`
- **Confidence level:** High
- **Architectural impact:** Greenfield lookahead work would duplicate a real capability that already exists
- **Recommended disposition:** **EXTEND**

### 5) Monday Morning Review
- **Existing owner:** `jobs_master.oppc_monday_reviews`
- **Producer:** `oppc_execution.py` workspace builder plus PM review actions
- **Consumers:** `PmMondayReviewWorkspace`, Monday briefing builders, executive recap readers
- **Storage:** `jobs_master.oppc_monday_reviews`
- **APIs / engines:** `backend/routes/oppc_execution.py`, `backend/services/cost_codes/oppc_execution.py`
- **Trust lines:** Schedule/Actuals → Monday Review is complete; Monday Review → Briefing is complete
- **Dependencies:** schedule snapshot, forecast history, payroll variance, trust-spine readiness
- **Existing reusable engines:** OPPC execution workspace, briefing pipeline
- **Current maturity:** High
- **Architectural gap:** hierarchy between project review state and executive briefing state should be explicitly locked
- **Evidence source:** `WP18A_MONDAY_RECAP_AND_INTELLIGENCE_AUDIT.md`, `WP18A_DATA_AND_TRUST_LINE_REGISTER.csv:T15-T17`
- **Confidence level:** Medium-high
- **Architectural impact:** Existing weekly operating rhythm is already architected
- **Recommended disposition:** **EXTEND**

### 6) Production Tracking
- **Existing owner:** `daily_reports`
- **Producer:** field/public Daily Report submit flows
- **Consumers:** cost-code progress, schedule engine, OPPC execution, ODS, PM/Admin daily readers
- **Storage:** `daily_reports`
- **APIs / engines:** `backend/routes/daily_reports.py`, `foundation.py`, `oppc_execution.py`
- **Trust lines:** Daily Reports → Progress/Schedule is complete; Daily Reports → ODS is derived but real
- **Dependencies:** project identity, cost-code assignments, Daily Report acceptance lifecycle
- **Existing reusable engines:** `daily_reports.py`, progress recompute in `foundation.py`, OPPC daily production consumers
- **Current maturity:** High
- **Architectural gap:** downstream field-normalization contracts should be documented, not rebuilt
- **Evidence source:** `WP18A_DAILY_REPORT_PROJECT_CONTROLS_BINDING_AUDIT.md`, `OPPC_DAILY_PRODUCTION_CERTIFICATION.md`
- **Confidence level:** High
- **Architectural impact:** This is the strongest actuals-truth lane in the platform
- **Recommended disposition:** **REUSE**

### 7) Resource Planning
- **Existing owner:** federated existing owners — demand on `jobs_master.assigned_cost_codes`; labor supply on `project_team_assignments`; dispatch supply on `dispatch_assignments`
- **Producer:** planning demand, staffing actions, dispatch operations
- **Consumers:** executive resource coordination, PM staffing views, PM command readers
- **Storage:** `jobs_master.assigned_cost_codes`, `project_team_assignments`, `dispatch_assignments`
- **APIs / engines:** `oppc_intelligence.py`, staffing routes, dispatch lifecycle family
- **Trust lines:** real but federated; no single constitutional seam yet documented
- **Dependencies:** project identity, cost-code demand, team roster, dispatch lifecycle, equipment identity
- **Existing reusable engines:** `project_team_assignments`, `dispatch_assignments`, OPPC enterprise resource coordination
- **Current maturity:** Medium-high
- **Architectural gap:** ownership is distributed by design but not yet constitutionally narrated
- **Evidence source:** `OPPC_ENTERPRISE_RESOURCE_COORDINATION.md`, `OPPC_CANONICAL_DATA_OWNERSHIP.md`
- **Confidence level:** Medium-high
- **Architectural impact:** Should be formalized as a federation, not replaced by a new resource database
- **Recommended disposition:** **EXTEND**

### 8) Equipment Planning
- **Existing owner:** `equipment_master` for identity, `dispatch_assignments` for active deployment context
- **Producer:** fleet/equipment admin actions and dispatch assignment actions
- **Consumers:** PM command resource views, executive resource coordination, fleet views
- **Storage:** `equipment_master`, `dispatch_assignments`
- **APIs / engines:** PM command center overview/resources, fleet/equipment APIs, dispatch lifecycle family
- **Trust lines:** identity is strong; project-controls planning semantics remain federated
- **Dependencies:** equipment registry, dispatch assignment state, defect visibility, haul-cycle context
- **Existing reusable engines:** `equipment_master`, `dispatch_assignments`, PM command resource aggregation
- **Current maturity:** Medium-high
- **Architectural gap:** no single named project-controls equipment-planning hierarchy was evidenced
- **Evidence source:** `pm_command_center.py:396-420,508-560`, `OPPC_ENTERPRISE_RESOURCE_COORDINATION.md`, `track_15_73_slice1_equipment_audit.py:203-248`
- **Confidence level:** Medium-high
- **Architectural impact:** Identity and deployment truth already exist and should not be rebuilt elsewhere
- **Recommended disposition:** **EXTEND**

### 9) Constraint Management
- **Existing owner:** `operational_constraints`
- **Producer:** constraint operators via the existing constraint workflow
- **Consumers:** constraint UI, PM command center holds rows, future schedule/KPI consumers
- **Storage:** `operational_constraints`
- **APIs / engines:** `backend/routes/operational_constraints.py`, PM command hold projection
- **Trust lines:** Constraints → PM Command is real; Constraints → Schedule/KPI is weak
- **Dependencies:** project identity, schedule hierarchy, Monday review, executive KPI flow
- **Existing reusable engines:** `operational_constraints`, PM command hold projection
- **Current maturity:** Medium
- **Architectural gap:** downstream control binding remains the clearest under-connected trust line in the platform
- **Evidence source:** `WP18A_PLATFORM_CAPABILITY_REGISTER.csv:C15`, `WP18A_GAP_AND_DEPENDENCY_REGISTER.csv:G02`, `pm_command_center.py:301-341`
- **Confidence level:** Medium
- **Architectural impact:** Constraint-aware controls cannot be claimed complete until this line is extended
- **Recommended disposition:** **EXTEND**

### 10) Forecasting
- **Existing owner:** `jobs_master.oppc_forecast_history` and `jobs_master.oppc_forecast_overrides`, computed by `schedule_engine.py`
- **Producer:** schedule engine forecasts plus PM override/approval actions
- **Consumers:** PM schedule, Monday briefings, confidence history consumers
- **Storage:** `jobs_master.oppc_forecast_history`, `jobs_master.oppc_forecast_overrides`
- **APIs / engines:** schedule endpoints in `cost_codes.py`, `schedule_engine.py`, briefing consumers
- **Trust lines:** Schedule → Forecast is complete; Forecast → Briefing is complete
- **Dependencies:** assignments, actuals, schedule hierarchy, override governance
- **Existing reusable engines:** `schedule_engine.py`, forecast history/override storage, briefing consumers
- **Current maturity:** High
- **Architectural gap:** truth classes are implemented but should be constitutionally named across all downstream consumers
- **Evidence source:** `OPPC_FORECASTING_CRITICAL_PATH_CERTIFICATION.md`, `WP18A_SCHEDULE_FORENSIC_AUDIT.md`
- **Confidence level:** High
- **Architectural impact:** This is already a reusable forecast engine and should never be rebuilt in parallel
- **Recommended disposition:** **EXTEND**

### 11) Earned Value
- **Existing owner:** none proven in the audited evidence package
- **Producer:** none proven
- **Consumers:** none proven today; future executive/project-controls consumers only
- **Storage:** none proven
- **APIs / engines:** none proven
- **Trust lines:** missing
- **Dependencies:** budget hierarchy, project-specific cost codes, schedule hierarchy, production actuals
- **Existing reusable engines:** reusable upstream inputs only — assignments, actuals, schedule snapshot
- **Current maturity:** Absent as a constitutional control domain
- **Architectural gap:** no earned value formulas, storage, APIs, or governance contract were evidenced
- **Evidence source:** repository-wide search executed 2026-08-03; no earned value / EVM / CPI / SPI owner or engine found in backend, frontend, WP18A, OPPC, or WP17A materials
- **Confidence level:** High
- **Architectural impact:** This is the second legitimate build-new area, and it must remain derived over reused upstream truths
- **Recommended disposition:** **BUILD_NEW**

### 12) Executive KPI flow
- **Existing owner:** no single constitutional owner yet; hierarchy is split across ODS, project health, OPPC executive recap, and the KPI dictionary
- **Producer:** multiple existing read-model producers
- **Consumers:** Executive Operational Intelligence, Project Health, administrative KPI consumers
- **Storage:** `operational_kpi_snapshots`, project-health payloads, KPI dictionary records, confidence history
- **APIs / engines:** ODS routes, `project_health.py`, OPPC executive operations center, `/api/admin/wp17a/kpi-dictionary`
- **Trust lines:** multiple real lanes exist, but semantic hierarchy is not singular
- **Dependencies:** production truth, schedule truth, forecast truth, constraints, health rollups, KPI governance metadata
- **Existing reusable engines:** ODS intelligence, Project Health, OPPC executive recap, KPI dictionary
- **Current maturity:** Medium-high
- **Architectural gap:** executive read models overlap and can drift unless one constitutional hierarchy is defined
- **Evidence source:** `WP17A_EXECUTIVE_KPI_DICTIONARY.md`, `WP18A_MONDAY_RECAP_AND_INTELLIGENCE_AUDIT.md`, `WP18A_GAP_AND_DEPENDENCY_REGISTER.csv:G06`
- **Confidence level:** Medium-high
- **Architectural impact:** The platform already has executive signal engines; the need is consolidation, not invention
- **Recommended disposition:** **CONSOLIDATE**

## Never rebuild list

The following existing engines or owners should **not** be rebuilt in WP-18C:

1. `cost_code_registry`
2. `jobs_master.assigned_cost_codes`
3. `backend/services/cost_codes/schedule_engine.py`
4. `daily_reports`
5. `project_team_assignments`
6. `dispatch_assignments`
7. `equipment_master`
8. `jobs_master.oppc_planning_lifecycle`
9. `jobs_master.oppc_monday_reviews`
10. `oppc_monday_briefings`

## Readiness answer

The constitutional architecture for Project Controls is already mostly present. The lowest-risk path is to **reuse and extend the existing cost-code, schedule, Daily Report, OPPC, staffing, dispatch, equipment, and KPI-governance lanes**, then **consolidate executive KPI hierarchy**, and only then consider **BUILD_NEW** work for the two truly unevidenced domains: **Budget Hierarchy** and **Earned Value**.
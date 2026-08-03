# WP18B Recommended Implementation Sequence

Date: 2026-08-03  
Purpose: Define the exact lowest-risk sequence for WP-18C and beyond while maximizing reuse and minimizing technical debt.  
Rule: Sequence follows the constitutional order **Reuse → Extend → Repair → Connect → Consolidate → Build New**. `Build New` appears only where repository evidence proved no reusable owner/engine exists.

## Executive sequencing answer

The lowest-risk path is to harden what already exists before authorizing any net-new domain work. That means the platform should first lock constitutional ownership and reuse decisions around **project identity, cost codes, schedule, daily production, lookahead, Monday review, staffing, dispatch, equipment, and executive KPI governance**. Only after those layers are explicit should leadership authorize **Budget Hierarchy** and then **Earned Value**.

## Sequence

### Step 1 — Freeze the authority contracts already evidenced
- **Mode:** REUSE
- **Why first:** Every later control depends on singular authority naming
- **Reused owners:** `jobs_master`, `cost_code_registry`, `project_team_assignments`, `daily_reports`, `operational_constraints`, `equipment_master`, `dispatch_assignments`
- **Output of the step:** constitutional authority contract pack for project identity, cost codes, schedule inputs, production actuals, constraints, staffing, equipment
- **Evidence basis:** `WP18B_AUTHORITY_MATRIX.csv`, `WP18B_SOURCE_OF_TRUTH_MATRIX.csv`

### Step 2 — Lock the cost-code planning spine
- **Mode:** EXTEND
- **Why second:** cost-code planning is upstream of schedule, forecast, lookahead, production reconciliation, and future budget linkage
- **Extend only:** assignment governance on `jobs_master.assigned_cost_codes`, not the registry or actuals stores
- **Never rebuild:** `cost_code_registry`, `jobs_master.assigned_cost_codes`, `daily_reports.cost_code_quantities`
- **Evidence basis:** `WP18B_COST_CODE_AUTHORITY_AUDIT.md`

### Step 3 — Formalize the schedule constitution already in place
- **Mode:** EXTEND
- **Why third:** schedule hierarchy, lookahead, and forecast are already built on reusable foundations
- **Extend only:** hierarchy naming, truth-class governance, and downstream traceability
- **Never rebuild:** `schedule_engine.py`, `jobs_master.oppc_planning_lifecycle`, `jobs_master.oppc_forecast_history`, `jobs_master.oppc_forecast_overrides`
- **Evidence basis:** `WP18B_SCHEDULE_AUTHORITY_AUDIT.md`

### Step 4 — Repair the weakest proven trust lines before adding new features
- **Mode:** REPAIR
- **Targets:**
  1. Constraints → Schedule
  2. Constraints → Executive KPI flow
  3. Embedded lookahead semantics → operator/executive discoverability
  4. Daily Report downstream normalization contract
- **Why now:** these are the current weak points inside otherwise reusable control architecture
- **Evidence basis:** `WP18B_TRUST_LINE_REGISTER.csv`, `WP18B_RISK_AND_DEPENDENCY_REGISTER.csv`

### Step 5 — Connect the federated resource and equipment planning lanes
- **Mode:** CONNECT
- **Why fifth:** resource and equipment planning already exist, but as federated seams rather than one constitutional statement
- **Connect only:** demand on `jobs_master.assigned_cost_codes`, labor supply on `project_team_assignments`, active deployment on `dispatch_assignments`, asset identity on `equipment_master`
- **Never rebuild:** `project_team_assignments`, `dispatch_assignments`, `equipment_master`
- **Evidence basis:** `WP18B_CAPABILITY_AND_ENGINE_MAP.csv:PC07-PC08`, `OPPC_ENTERPRISE_RESOURCE_COORDINATION.md`

### Step 6 — Connect the weekly operating rhythm end-to-end
- **Mode:** CONNECT
- **Why sixth:** Monday review, Monday briefing, and executive recap already exist but need one constitutional hierarchy
- **Connect only:** schedule/forecast/constraint/production inputs into Monday review and briefing semantics
- **Never rebuild:** `jobs_master.oppc_monday_reviews`, `oppc_monday_briefings`
- **Evidence basis:** `WP18B_PROJECT_CONTROLS_READINESS_AUDIT.md`, `WP18B_SCHEDULE_AUTHORITY_AUDIT.md`

### Step 7 — Consolidate executive KPI hierarchy without creating a new dashboard stack
- **Mode:** CONSOLIDATE
- **Why seventh:** the platform already has multiple executive signal lanes, and ungoverned additions would create denominator drift
- **Consolidate existing lanes:** ODS, Project Health, OPPC executive recap, KPI dictionary, legacy operational-intelligence where still needed
- **Never rebuild:** ODS, Project Health, KPI dictionary, OPPC recap
- **Evidence basis:** `WP18B_DUPLICATION_REGISTER.csv`, `WP18B_PROJECT_CONTROLS_READINESS_AUDIT.md`

### Step 8 — Introduce Budget Hierarchy only after reuse/extension work is complete
- **Mode:** BUILD NEW
- **Why only now:** repository evidence did not prove an existing budget owner or hierarchy, but budget depends on already-locked project identity, cost-code, schedule, and executive KPI contracts
- **Constitutional rule:** budget must consume, not replace, existing project identity and project-specific cost-code truth
- **Evidence basis:** `WP18B_CAPABILITY_AND_ENGINE_MAP.csv:PC03`, `WP18B_AUTHORITY_MATRIX.csv:A15`

### Step 9 — Introduce Earned Value as a derived layer after Budget Hierarchy exists
- **Mode:** BUILD NEW
- **Why last:** earned value has no evidenced current engine and depends on budget + schedule + progress truth all being constitutionally locked first
- **Constitutional rule:** earned value must remain derived and must not create a second planning or actuals owner
- **Evidence basis:** `WP18B_CAPABILITY_AND_ENGINE_MAP.csv:PC11`, `WP18B_AUTHORITY_MATRIX.csv:A16`

## Sequence guardrails

1. Do **not** build a new cost-code, schedule, production, Monday review, staffing, dispatch, equipment, or executive KPI engine.
2. Do **not** let derivative readers (`project_health`, ODS, projected config, dashboards) become write owners.
3. Do **not** introduce budget or earned value before the reused foundations are constitutionally locked.
4. Do **not** deprecate legacy read models until consolidated hierarchy is proven and validated against the existing evidence pack.

## Lowest-risk implementation summary

The exact lowest-risk path is:

**Authority freeze → Cost-code spine lock → Schedule/Lookahead/Forecast formalization → Weak trust-line repair → Resource/Equipment federation connection → Monday rhythm connection → Executive KPI consolidation → Budget Hierarchy (new) → Earned Value (new)**.
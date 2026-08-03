# WP18B Schedule Authority Audit

Date: 2026-08-03  
Scope: Schedule hierarchy, forecasting, lookahead semantics, Monday review chain, and the trust lines that make schedule authority constitutional.

## Executive answer

The platform already has a reusable schedule authority path. The schedule engine, lookahead lifecycle, forecast governance, and Monday review/briefing chain all exist in the repository-backed evidence set. The architectural task is to document the hierarchy so later work extends one schedule constitution rather than inventing a second planning stack.

## Constitutional schedule stack

### Layer 1 — Planned work structure
- **Owner:** `jobs_master.assigned_cost_codes`
- **Role:** project-specific planned work hierarchy and production basis
- **Evidence source:** `WP18A_COST_CODE_FORENSIC_AUDIT.md`, `WP18A_SCHEDULE_FORENSIC_AUDIT.md`
- **Confidence level:** High
- **Architectural impact:** The schedule stack begins on the existing cost-code planning spine
- **Recommended disposition:** **REUSE / EXTEND**

### Layer 2 — Actual progress truth
- **Owner:** `daily_reports.cost_code_quantities`
- **Role:** actual quantities that update progress against planned work
- **Evidence source:** `WP18A_DAILY_REPORT_PROJECT_CONTROLS_BINDING_AUDIT.md`, `OPPC_DAILY_PRODUCTION_CERTIFICATION.md`
- **Confidence level:** High
- **Architectural impact:** Schedule progress already consumes canonical actuals rather than a parallel tracker
- **Recommended disposition:** **REUSE**

### Layer 3 — Deterministic schedule snapshot
- **Owner:** derived payload from `schedule_engine.py`
- **Role:** current task order, dates, and schedule logic exposed to PM workflows
- **Evidence source:** `WP18A_SCHEDULE_FORENSIC_AUDIT.md:11-55`
- **Confidence level:** High
- **Architectural impact:** The engine already exists and should never be duplicated by dashboard-local logic
- **Recommended disposition:** **EXTEND**

### Layer 4 — Rolling lookahead lifecycle
- **Owner:** `jobs_master.oppc_planning_lifecycle`
- **Role:** two-week planning lifecycle, publication, and weekly rollover semantics
- **Evidence source:** `WP18A_LOOKAHEAD_AND_WEEKLY_RECONCILIATION_AUDIT.md`
- **Confidence level:** High
- **Architectural impact:** Lookahead is already real but under-labeled
- **Recommended disposition:** **EXTEND**

### Layer 5 — Forecast truth classes
- **Owner:** `jobs_master.oppc_forecast_history` and `jobs_master.oppc_forecast_overrides`
- **Role:** preserve calculated forecast, management override, approved contractual finish, and committed finish
- **Evidence source:** `OPPC_FORECASTING_CRITICAL_PATH_CERTIFICATION.md:7-25`
- **Confidence level:** High
- **Architectural impact:** Forecast authority is already richer than a basic finish-date override model
- **Recommended disposition:** **EXTEND**

### Layer 6 — Weekly decision and communication artifacts
- **Owner:** `jobs_master.oppc_monday_reviews` and `oppc_monday_briefings`
- **Role:** review-state workspace and persisted briefing outputs
- **Evidence source:** `WP18A_MONDAY_RECAP_AND_INTELLIGENCE_AUDIT.md`
- **Confidence level:** Medium-high
- **Architectural impact:** Weekly control ritual already exists and should remain a chain, not a monolith
- **Recommended disposition:** **EXTEND / REUSE**

## Evidence-backed findings

### Finding SCH-01 — The schedule engine already exists and is constitutional
- **Evidence source:** `backend/services/cost_codes/schedule_engine.py`, `WP18A_SCHEDULE_FORENSIC_AUDIT.md`
- **Confidence level:** High
- **Architectural impact:** Future work must extend this engine rather than introduce a second schedule-computation path
- **Recommended disposition:** **EXTEND**

### Finding SCH-02 — Lookahead is present, but its architecture is hidden inside lifecycle state
- **Evidence source:** `WP18A_LOOKAHEAD_AND_WEEKLY_RECONCILIATION_AUDIT.md`
- **Confidence level:** High
- **Architectural impact:** The right answer is to formalize and expose existing lifecycle semantics, not to build a new lookahead tool
- **Recommended disposition:** **EXTEND**

### Finding SCH-03 — Forecasting already preserves multiple truth classes
- **Evidence source:** `OPPC_FORECASTING_CRITICAL_PATH_CERTIFICATION.md`
- **Confidence level:** High
- **Architectural impact:** This is a meaningful existing engine that should never be replaced by flat override fields elsewhere
- **Recommended disposition:** **EXTEND**

### Finding SCH-04 — Monday review and Monday briefing are different architectural layers
- **Evidence source:** `WP18A_MONDAY_RECAP_AND_INTELLIGENCE_AUDIT.md`
- **Confidence level:** High
- **Architectural impact:** The review workspace should not be confused with the persisted communication artifact
- **Recommended disposition:** **REUSE**

### Finding SCH-05 — Constraint binding into schedule remains weak
- **Evidence source:** `WP18A_GAP_AND_DEPENDENCY_REGISTER.csv:G02`, `pm_command_center.py:301-341`
- **Confidence level:** Medium
- **Architectural impact:** Schedule authority is incomplete until constraints are explicitly connected downstream
- **Recommended disposition:** **EXTEND**

### Finding SCH-06 — Budget and earned value are not part of the existing schedule constitution
- **Evidence source:** `backend/routes/operational_kpis.py:16-17`, repository searches executed 2026-08-03
- **Confidence level:** High
- **Architectural impact:** Schedule authority should not be stretched to pretend budget or earned-value ownership already exists
- **Recommended disposition:** **BUILD_NEW later, outside current schedule authority**

## Trust-line status

| Trust line | Status | Evidence | Architectural meaning |
|---|---|---|---|
| Planned cost-code structure → Schedule | Complete | `WP18A_SCHEDULE_FORENSIC_AUDIT.md` | The engine is built on the right planning owner |
| Daily actuals → Schedule progress | Complete | `WP18A_DAILY_REPORT_PROJECT_CONTROLS_BINDING_AUDIT.md` | Actuals already feed the schedule spine |
| Schedule → Lookahead lifecycle | Complete but under-labeled | `WP18A_LOOKAHEAD_AND_WEEKLY_RECONCILIATION_AUDIT.md` | Capability exists but needs constitutional naming |
| Schedule/Forecast → Monday review | Complete | `WP18A_MONDAY_RECAP_AND_INTELLIGENCE_AUDIT.md` | Weekly review already depends on existing schedule truth |
| Constraints → Schedule | Weak | `WP18A_GAP_AND_DEPENDENCY_REGISTER.csv:G02` | Key missing connection in the current constitutional stack |

## Engines that should never be rebuilt

1. `backend/services/cost_codes/schedule_engine.py`
2. Schedule endpoints in `backend/routes/cost_codes.py`
3. `jobs_master.oppc_planning_lifecycle`
4. `jobs_master.oppc_forecast_history`
5. `jobs_master.oppc_forecast_overrides`
6. `jobs_master.oppc_monday_reviews`
7. `oppc_monday_briefings`

## Constitutional decision

The correct WP-18B schedule decision is to:

- **REUSE** the current planned-work and actuals inputs
- **EXTEND** the deterministic schedule, lookahead, and forecast hierarchy already implemented
- **EXTEND** constraint binding into the schedule chain
- **REUSE** the Monday review → briefing chain

No evidence supports building a second schedule engine, a second lookahead store, or a parallel Monday review framework.
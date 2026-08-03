# WP18B Cost Code Authority Audit

Date: 2026-08-03  
Scope: Constitutional ownership of project-specific cost codes, their reuse boundaries, their downstream planning role, and the engines that must not be rebuilt.

## Executive answer

The platform already contains the correct cost-code constitutional split. The architectural issue is **not missing capability**. The issue is that the split lives across multiple reusable owners and must be documented so future work does not collapse them into one ambiguous “cost code system.”

## Constitutional ownership stack

### 1) Global reusable cost-code definition authority
- **Owner:** `cost_code_registry`
- **Producer:** admin registry maintenance
- **Consumers:** project assignment normalizer, registry administration, schedule setup
- **Storage:** `cost_code_registry`
- **Evidence source:** `WP18A_COST_CODE_FORENSIC_AUDIT.md:15-18`, `WP18A_DATA_AND_TRUST_LINE_REGISTER.csv:T05`
- **Confidence level:** High
- **Architectural impact:** This is the reusable template layer and must remain independent from project execution planning
- **Recommended disposition:** **REUSE**

### 2) Project-specific execution planning authority
- **Owner:** `jobs_master.assigned_cost_codes`
- **Producer:** PM/admin assignment updates
- **Consumers:** schedule engine, forecasting, OPPC, derivative project-operational config projections
- **Storage:** `jobs_master.assigned_cost_codes`
- **Evidence source:** `WP18A_COST_CODE_FORENSIC_AUDIT.md:20-39`, `WP18A_DATA_AND_TRUST_LINE_REGISTER.csv:T06`
- **Confidence level:** High
- **Architectural impact:** This is the constitutional project-controls owner for planned cost-code structure
- **Recommended disposition:** **EXTEND**

### 3) Actual production truth against cost codes
- **Owner:** `daily_reports.cost_code_quantities`
- **Producer:** Daily Report submitters
- **Consumers:** progress recompute, schedule hierarchy, Monday review, executive intelligence
- **Storage:** `daily_reports`
- **Evidence source:** `WP18A_DAILY_REPORT_PROJECT_CONTROLS_BINDING_AUDIT.md:11-23`, `OPPC_DAILY_PRODUCTION_CERTIFICATION.md:18-33`
- **Confidence level:** High
- **Architectural impact:** Planned and actual cost-code truth are already separated correctly
- **Recommended disposition:** **REUSE**

### 4) Derived cost-code projections and consumers
- **Owner:** none — derivative only
- **Producer:** `foundation.py`, ODS projection helpers, schedule engine, OPPC consumers
- **Consumers:** PM schedule, ODS, executive rollups
- **Storage:** derivative payloads and read models only
- **Evidence source:** `WP18A_COST_CODE_FORENSIC_AUDIT.md:31-54`, `WP18A_DATA_AND_TRUST_LINE_REGISTER.csv:T07-T10`
- **Confidence level:** High
- **Architectural impact:** Derived consumers must never be promoted into write-authority surfaces
- **Recommended disposition:** **CONNECT / EXTEND**

## Evidence-backed findings

### Finding CC-01 — The registry and project-assignment layers are intentionally different
- **Evidence source:** `WP18A_COST_CODE_FORENSIC_AUDIT.md`
- **Confidence level:** High
- **Architectural impact:** Rebuilding or collapsing them would mix template truth with project-execution truth
- **Recommended disposition:** **REUSE**

### Finding CC-02 — `jobs_master.assigned_cost_codes` is the constitutional project-controls owner
- **Evidence source:** `WP18A_COST_CODE_FORENSIC_AUDIT.md`, `WP18A_PROJECT_CONTROLS_EXISTING_STATE.md`
- **Confidence level:** High
- **Architectural impact:** Future scheduling, lookahead, forecasting, and budget work should anchor on this owner rather than a new planning collection
- **Recommended disposition:** **EXTEND**

### Finding CC-03 — Actual quantity truth is already separated correctly from plan truth
- **Evidence source:** `WP18A_DAILY_REPORT_PROJECT_CONTROLS_BINDING_AUDIT.md`, `OPPC_DAILY_PRODUCTION_CERTIFICATION.md`
- **Confidence level:** High
- **Architectural impact:** There is no architectural need for a second “actuals by cost code” store
- **Recommended disposition:** **REUSE**

### Finding CC-04 — `project_operational_config` must remain derivative-only
- **Evidence source:** `WP18A_COST_CODE_FORENSIC_AUDIT.md:31-39`, `WP18A_DUPLICATION_AND_REUSE_DECISION_REGISTER.csv:D05`
- **Confidence level:** High
- **Architectural impact:** Treating projected config as the owner would recreate authority drift
- **Recommended disposition:** **CONNECT**

### Finding CC-05 — Cost-code architecture is one of the strongest “never rebuild” lanes in the platform
- **Evidence source:** `WP18A_EXECUTIVE_AUDIT_REPORT.md`, `WP18A_EXECUTIVE_SYSTEM_ARCHITECTURE_MAP.md`
- **Confidence level:** High
- **Architectural impact:** WP-18C should preserve the current cost-code spine and only add governance around it
- **Recommended disposition:** **EXTEND**

## Trust-line status

| Trust line | Status | Evidence | Impact |
|---|---|---|---|
| Registry → Project assignment | Complete | `T05-T06` | Reusable definition truth is already feeding project planning correctly |
| Project assignment → Schedule | Complete | `WP18A_SCHEDULE_FORENSIC_AUDIT.md` | Scheduling already depends on the right planning owner |
| Project assignment → Forecast | Complete | `OPPC_FORECASTING_CRITICAL_PATH_CERTIFICATION.md` | Forecasting is already built on the cost-code planning spine |
| Daily actuals → Progress | Complete | `WP18A_DAILY_REPORT_PROJECT_CONTROLS_BINDING_AUDIT.md` | Actuals are already grounded in Daily Reports |
| Cost-code plan/actuals → Executive KPI flow | Weak but real | `WP18A_GAP_AND_DEPENDENCY_REGISTER.csv:G06` | Executive KPI hierarchy still needs consolidation |

## Engines and owners that should never be rebuilt

1. `cost_code_registry`
2. `jobs_master.assigned_cost_codes`
3. `backend/routes/cost_codes.py`
4. `backend/services/cost_codes/foundation.py`
5. `daily_reports.cost_code_quantities`

## Constitutional decision

The correct constitutional disposition for cost-code architecture is:

- **REUSE** the global registry
- **EXTEND** the project assignment authority contract
- **REUSE** Daily Report actuals as the only cost-code actuals truth
- **CONNECT** derivative readers so no projection or dashboard becomes a stealth owner

No evidence supports rebuilding cost-code foundations.
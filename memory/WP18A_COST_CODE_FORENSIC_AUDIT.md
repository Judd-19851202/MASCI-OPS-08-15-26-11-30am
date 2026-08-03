# WP-18A Cost Code Forensic Audit

Date: 2026-08-03  
Audit rule: producer → storage/API/service → consumer only.

## Scope audited
- Registry authority
- Project assignment persistence
- Progress actuals binding
- Schedule and forecast dependency chain
- OPPC and executive consumers

## What source confirms

### 1) Registry authority exists
- `backend/routes/cost_codes.py` declares `REGISTRY_COLLECTION = "cost_code_registry"`.
- Registry routes create indexes, list rows, upsert items, and replace/delete rows.
- Conclusion: there is an explicit reusable cost-code registry, not just per-project ad hoc rows.

### 2) Project assignment authority exists and is not the registry itself
- `foundation.py` loads project assignments from `jobs_master.assigned_cost_codes`.
- The same helper projects the normalized assignment set into `project_operational_config` and records `source_authority = jobs_master.assigned_cost_codes`.
- Conclusion: the registry defines reusable code templates; project truth for configured job execution lives on the project record in `jobs_master`.

### 3) Progress is already bound to Daily Reports
- Cost-code routes and helpers load project actuals from `daily_reports.cost_code_quantities`.
- `daily_reports.py` includes cost-code quantity handling during canonical record creation/update.
- Conclusion: actual production entry is already wired into the cost-code spine.

### 4) Cost-code configuration is a prerequisite for higher-order controls
- `foundation.py` computes planning readiness from assignment completeness.
- Missing required fields disable weekly rollover and Monday-look-behind readiness.
- Conclusion: cost-code assignment quality is already acting as a gate for schedule and OPPC maturity.

### 5) Downstream consumers are real and multiple
- `PmProjectSchedule.jsx` consumes assignment, progress, schedule, forecast, and lifecycle payloads.
- `oppc_execution.py` and `oppc_briefings.py` reuse the same assignment + actual + schedule chain.
- `oppc_intelligence.py` references `jobs_master.assigned_cost_codes` directly in executive intelligence outputs.
- Conclusion: cost codes are already a shared platform spine, not a local PM-only feature.

## Canonical trace lines

### Registry line
Admin registry action  
→ `cost_code_registry`  
→ `normalize_registry_item()` / registry endpoints  
→ assignment UI and normalization consumers

### Project assignment line
PM/admin assignment update  
→ `jobs_master.assigned_cost_codes`  
→ `load_project_assignments()` / projection to `project_operational_config`  
→ schedule, forecast, OPPC, ODS config consumers

### Actual-progress line
Field Daily Report entry of `cost_code_quantities`  
→ `daily_reports`  
→ `load_project_cost_code_actuals()` / progress recompute  
→ schedule, forecasting, Monday review, executive rollups

## What is trustworthy
- Registry persistence is explicit.
- Project assignment authority is explicit.
- Actual-production binding to Daily Reports is explicit.
- ODS config projection is explicitly derivative, not an authority swap.

## What remains evidence-limited
- The audit did not prove every UI button path for every registry mutation in runtime.
- The audit did not prove downstream consumers use exactly the same assignment revision at every moment; source proves shared authority but not runtime concurrency semantics.
- The audit did not prove external estimating/ERP synchronization into the registry.

## Duplication / drift risk
- Risk of misunderstanding exists between:
  - `cost_code_registry` as reusable template authority
  - `jobs_master.assigned_cost_codes` as project execution authority
  - `project_operational_config` as derivative ODS projection
- If WP-18B blurs these roles, source-of-truth drift will be reintroduced.

## WP-18 disposition
- Registry: `REUSE_AS_IS`
- Project assignments: `EXTEND`
- Actual-progress binding: `REUSE_AS_IS`
- Downstream ODS/OPPC projection: `CONNECT`

## Executive conclusion
The cost-code foundation is already substantial and production-shaped. WP-18B should use it as the **canonical project-controls spine** and explicitly document the authority split between registry, project assignment, and downstream derivative projections.
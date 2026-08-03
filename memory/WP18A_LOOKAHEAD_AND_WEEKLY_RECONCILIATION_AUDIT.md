# WP-18A Lookahead and Weekly Reconciliation Audit

Date: 2026-08-03

## Purpose
Determine whether lookahead / weekly reconciliation is absent, disconnected, or already present in another form.

## Finding
No standalone “lookahead platform” was found. However, the capability itself is already present inside the schedule/cost-code/OPPC spine.

## Evidence

### Embedded planning readiness
- `foundation.py` computes assignment-level and portfolio-level planning readiness.
- Readiness explicitly controls:
  - `supports_weekly_rollover`
  - `supports_monday_look_behind`

### Embedded planning lifecycle persistence
- `load_project_planning_lifecycle()` and `persist_project_planning_lifecycle()` read/write `jobs_master.oppc_planning_lifecycle`.
- `cost_codes.py` exposes lifecycle publication and lifecycle snapshot returns.

### Weekly rollover workflows already exist
- `cost_codes.py` exposes preview/apply style weekly rollover routes.
- `PmProjectSchedule.jsx` consumes weekly rollover preview/apply behavior.

### Monday review depends on the same readiness chain
- `oppc_execution.py` builds Monday review readiness from assignments, actuals, planning lifecycle, payroll/task evidence, and review state.
- This means weekly reconciliation is already structurally tied to Monday recap/review.

## Trace
Configured project assignments  
→ planning readiness + `oppc_planning_lifecycle` on `jobs_master`  
→ weekly rollover preview/apply APIs  
→ PM schedule workspace and Monday review readiness consumers

## What this means
- The capability is **existing**.
- It is **embedded** rather than independently named.
- It is **connected** to schedule and Monday review, but not yet expressed as a first-class executive control domain.

## Evidence limits
- The audit did not prove a separate lookahead artifact repository beyond embedded lifecycle state on `jobs_master`.
- The audit did not find proof that constraints automatically alter lifecycle readiness without operator action.
- The audit did not prove a dedicated executive lookahead summary screen separate from schedule and Monday review.

## Reuse decision
- Do **not** classify lookahead as `BUILD_NEW`.
- Correct classification: existing embedded capability with `EXTEND` / `CONNECT` work needed.

## Recommended WP-18B posture
1. Keep the embedded lifecycle authority on the existing schedule spine.
2. Expose clearer executive semantics for “lookahead committed / published / rolled / reviewed”.
3. Connect operational constraints and executive KPI views to the same lifecycle state.

## Executive conclusion
Lookahead and weekly reconciliation are already present in source. WP-18B should formalize and connect them, not start over.
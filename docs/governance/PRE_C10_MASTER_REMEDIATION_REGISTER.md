# MASCI Operations Platform — PRE-C10 Master Remediation Register

Last updated: 2026-08-08T16:50Z

Status: **NO-GO**

This register is the current denominator for PRE-C10 remediation. Items are never silently removed; they move between factual states only:

- `REPRODUCED → ROOT-CAUSED → REPAIRED → CERTIFIED`
- `ALREADY RESOLVED BY SHARED REPAIR → RUNTIME VERIFIED`
- `NOT REPRODUCIBLE → EVIDENCE PROVIDED`
- `NOT APPLICABLE → FACTUAL REASON`

## Current global gate

- Trust Spine: **OPEN** (`platform_band=amber`, `canonical_status=DEGRADED`, remaining degraded workflows = 10)
- Truthful-state primitive: **PARTIAL PASS** (shared primitive implemented and verified on repaired surfaces; rollout continues)
- Screenshot Product Quality Ledger: **UPGRADED / RERUNNING** (contract version `wp18db-product-quality-v2`)
- Deployment readiness: **PASS WITH ADVISORIES**
- Live production: **REDEPLOYMENT REQUIRED**
- C10: **NOT AUTHORIZED**

## Completed / verified sub-batches

| ID | Lane | Finding | Status | Evidence |
|---|---|---|---|---|
| PRE-C10-TRUTH-001 | Truthful states | False-zero loading on `/admin/deploy-recovery` | REPAIRED → CERTIFIED | `iteration_4.json`, browser delay validation |
| PRE-C10-TRUTH-002 | Truthful states | False-zero loading on `/hr/employees` | REPAIRED → CERTIFIED | `iteration_4.json`, browser delay validation |
| PRE-C10-TRUTH-003 | Truthful states | False-zero loading on `/admin/project-staffing` | REPAIRED → CERTIFIED | `iteration_4.json`, browser delay validation |
| PRE-C10-UX-001 | Operator continuity | Legacy route banner leaked migration language | REPAIRED → CERTIFIED | `iteration_4.json`, browser verification |
| PRE-C10-TRUST-001 | Trust Spine | `oppc-enterprise-resource-coordination` emitted only `dashboard_updated` and stayed amber | REPAIRED → CERTIFIED | preview Trust Spine now shows workflow GREEN |
| PRE-C10-TRUST-002 | Trust Spine | Preview-safe email workflows were falsely graded against live-provider terminal stages | REPAIRED → CERTIFIED | `meeting`, `incident`, `qaqc`, `equipment-inspection` now GREEN with `delivery_path=preview_capture` |
| PRE-C10-TRUST-003 | Trust Spine | Clean DVIR submissions had no non-email completion contract | REPAIRED → CERTIFIED | preview clean DVIR submit now yields `dvir` GREEN with `delivery_path=not_required` |
| PRE-C10-TRUST-004 | Trust Spine | `oppc-production-confidence` had valid instrumentation but no current exercised evidence | REPAIRED → CERTIFIED | preview confidence snapshot now yields workflow GREEN |
| PRE-C10-TRUST-005 | Trust Spine | `oppc-variance-intelligence` missed `dashboard_updated`; `oppc-recovery-intelligence` never emitted a full lifecycle | REPAIRED → CERTIFIED | preview variance review now yields both workflows GREEN |
| PRE-C10-TRUST-006 | Trust Spine | `oppc-payroll-reconciliation` had no current runtime evidence | REPAIRED → CERTIFIED | preview HR upload now yields workflow GREEN |
| PRE-C10-TRUTH-004 | Shared primitive | Shared truthful-state classifier implemented for loading / true zero / empty / unknown / unavailable / stale / no access / error | REPAIRED → CERTIFIED | `src/lib/truthfulDataState.js`, `truthfulDataState.test.js` |

## Active Trust Spine blockers

### Root-caused rows still keeping Trust Spine OPEN

| Workflow | Current state | Source authority | Expected state | Freshness | Failing dependency | Downstream impact | C6/C7/C8/C9 impact | Operator data trustworthy | Status |
|---|---|---|---|---|---|---|---|---|---|
| `dispatch-assignment` | stale lifecycle evidence | `trust_spine_events` via `routes/dispatch_lifecycle.py:create_assignment` | current lifecycle evidence inside 72h window | 159.0h old vs 72h window | governed dispatch runtime has not refreshed within policy | dispatch/admin visibility can drift | indirect trust-layer impact | bounded historical only | ROOT-CAUSED / OPEN |
| `inspection` | stale lifecycle evidence | `trust_spine_events` via `auto_email_dispatch:inspection` | current lifecycle evidence inside 168h window | 398.9h old vs 168h window | inspection workflow not refreshed within policy | safety/compliance dashboards can lag | indirect downstream impact | bounded historical only | ROOT-CAUSED / OPEN |
| `jha` | stale lifecycle evidence | `trust_spine_events` via `auto_email_dispatch:jha` | current lifecycle evidence inside 168h window | 399.0h old vs 168h window | JHA workflow not refreshed within policy | safety/compliance dashboards can lag | indirect downstream impact | bounded historical only | ROOT-CAUSED / OPEN |
| `operational-events-materialization` | stale lifecycle evidence | `trust_spine_events` via `routes.operational_events.materialize` | current lifecycle evidence inside 24h window | 324.7h old vs 24h window | materialization path not refreshed within policy | admin/recovery derived truth can drift | indirect trust-layer impact | bounded historical only | ROOT-CAUSED / OPEN |
| `oppc-cost-code-plan` | stale lifecycle evidence | `trust_spine_events` via `routes/cost_codes.py:put_project_schedule` | current lifecycle evidence inside 168h window | 260.0h old vs 168h window | planning workflow not refreshed within policy | project controls / Monday Review can drift | affects C6/C7/C8/C9 planning lineage | bounded historical only | ROOT-CAUSED / OPEN |
| `oppc-forecasting` | stale lifecycle evidence | `trust_spine_events` via `routes/cost_codes.py:upsert_project_forecast_override` | current lifecycle evidence inside 168h window | 260.0h old vs 168h window | forecasting workflow not refreshed within policy | forecasting / portfolio intelligence can drift | affects C6/C7/C8/C9 planning lineage | bounded historical only | ROOT-CAUSED / OPEN |
| `oppc-monday-look-behind` | stale lifecycle evidence | `trust_spine_events` via `routes/oppc_execution.py:start_monday_review` | current lifecycle evidence inside 192h window | 264.1h old vs 192h window | Monday review lifecycle not refreshed within policy | Monday Review / portfolio intelligence can drift | affects C6/C7/C8/C9 planning lineage | bounded historical only | ROOT-CAUSED / OPEN |
| `oppc-monday-morning-briefing` | stale lifecycle evidence | `trust_spine_events` via `routes/oppc_execution.py:freeze_enterprise_monday_briefing` | current lifecycle evidence inside 192h window | 259.5h old vs 192h window | enterprise Monday briefing not refreshed within policy | briefing / portfolio intelligence can drift | affects C6/C7/C8/C9 planning lineage | bounded historical only | ROOT-CAUSED / OPEN |
| `oppc-weekly-rollover` | stale lifecycle evidence | `trust_spine_events` via `routes/cost_codes.py:apply_weekly_rollover` | current lifecycle evidence inside 192h window | 260.0h old vs 192h window | weekly rollover workflow not refreshed within policy | weekly project-controls truth can drift | affects C6/C7/C8/C9 planning lineage | bounded historical only | ROOT-CAUSED / OPEN |
| `shop-defect` | stale lifecycle evidence | `trust_spine_events` via `routes/fleet_ops.py:manual_oos` | current lifecycle evidence inside 168h window | 748.6h old vs 168h window | shop defect workflow not refreshed within policy | shop/admin visibility can drift | indirect trust-layer impact | bounded historical only | ROOT-CAUSED / OPEN |

## Other active lanes still open

| ID | Lane | Finding | Current disposition |
|---|---|---|---|
| PRE-C10-SCREENSHOT-001 | Product Quality Ledger | 85-screen ledger needed richer quality contract than load/wait checks alone | UPGRADED / RERUNNING |
| PRE-C10-ADMIN-001 | Deployment readiness | equipment missing canonical `unit_number` advisories | OPEN ADVISORY |
| PRE-C10-ADMIN-002 | Deployment readiness | employee rows missing canonical `employee_id` advisories | OPEN ADVISORY |
| PRE-C10-MASTER-001 | Denominator management | broaden register to all remaining Safety / Scheduling / Auth / UX findings from directive | IN PROGRESS |

## Next execution focus

1. Continue eliminating the 14 remaining Trust Spine blockers (starting with uninstrumented OPPC intelligence workflows and stale materialization / dispatch refresh gaps).
2. Complete the upgraded 85-screen screenshot ledger rerun and inspect every failure under the new contract.
3. Keep extending this register until every user-observed and agent-observed PRE-C10 item is explicitly dispositioned.
# MASCI Operations Platform — PRE-C10 Master Remediation Register

Last updated: 2026-08-08T18:37Z

Status: **NO-GO**

This register is the current denominator for PRE-C10 remediation. Items are never silently removed; they move between factual states only:

- `REPRODUCED → ROOT-CAUSED → REPAIRED → CERTIFIED`
- `ALREADY RESOLVED BY SHARED REPAIR → RUNTIME VERIFIED`
- `NOT REPRODUCIBLE → EVIDENCE PROVIDED`
- `NOT APPLICABLE → FACTUAL REASON`

## Current global gate

- Trust Spine: **PASS** (`platform_band=green`, `canonical_status=VERIFIED`)
- Truthful-state primitive: **PARTIAL PASS** (shared primitive implemented and verified on repaired surfaces; rollout continues)
- Screenshot Product Quality Ledger: **PASS** (contract version `wp18db-product-quality-v2`, `rows=85`, `failures=0`)
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
| PRE-C10-TRUST-007 | Trust Spine | Remaining degraded cadences were reclassified by real semantics (event-driven quiet, on-demand source-mutation, weekly due-date, certification-needed) instead of flat recency | REPAIRED → CERTIFIED | `/api/admin/trust-spine` now returns `platform_band=green`, `canonical_status=VERIFIED` |
| PRE-C10-TRUST-008 | Trust Spine | JHA preview-safe strict-delivery path never emitted a truthful terminal stage | REPAIRED → CERTIFIED | real controlled-certification JHA now closes with terminal proof |
| PRE-C10-TRUST-009 | Trust Spine | Monday briefing generation lacked `validation_complete` and could not satisfy the lifecycle contract | REPAIRED → CERTIFIED | current-cycle generate → approve → freeze now yields GREEN |
| PRE-C10-TRUST-010 | Trust Spine | Current-cycle Monday look-behind lacked certification evidence and payroll readiness | REPAIRED → CERTIFIED | current-cycle Monday review now completes after real payroll lifecycle + activity review |
| PRE-C10-TRUTH-004 | Shared primitive | Shared truthful-state classifier implemented for loading / true zero / empty / unknown / unavailable / stale / no access / error | REPAIRED → CERTIFIED | `src/lib/truthfulDataState.js`, `truthfulDataState.test.js` |
| PRE-C10-LEDGER-001 | Product Quality Ledger | Upgraded product-quality screenshot ledger rerun completed with governed quality criteria | REPAIRED → CERTIFIED | `/app/test_reports/runtime_screenshot_ledger/ledger.json` (`wp18db-product-quality-v2`, `failures=0`) |
| PRE-C10-SAFETY-002 | Safety truth | Corrective-action overdue logic counted blank `due_date` values as overdue and diverged across overview / digest / executive / command-center / operations-center consumers | REPAIRED → CERTIFIED | shared helper `lib/corrective_action_truth.py`; preview runtime now reconciles `open=2`, `overdue=2` across `/api/safety/overview`, digest preview, executive overview, command center, operations center, project health |
| PRE-C10-SAFETY-003 | Safety truth | Preview certification / test corrective actions leaked into operator and executive truth as live safety work | REPAIRED → CERTIFIED | shared filter `lib/synthetic_corrective_action_filter.py`; preview backfill flagged `96` synthetic rows; visible corrective-action list now resolves to the 2 real incident-linked records only |
| PRE-C10-SAFETY-004 | Safety lifecycle | Incident lifecycle regression and corrective-action lifecycle regression rerun against live preview auth/session contracts | REPAIRED → CERTIFIED | `test_iter451_incident_lifecycle.py` = 17/17 pass; `test_iter356_capa_lifecycle.py` = 7/7 pass; `test_wp18db_incident_auth_backup.py` = 16/16 pass |
| PRE-C10-SCHEDULE-002 | Schedule truth | PM schedule authority runtime lane rerun with live preview auth contract: overview, staged import, row review, activation, export, actuals overview, lookahead, daily work plan | REPAIRED → CERTIFIED | `test_wp18c4_schedule_api.py` = 4/4 pass; `test_wp18c5_schedule_actuals_foundation.py` = 3/3 pass |
| PRE-C10-SCHEDULE-003 | Schedule scope | PM-only project selector / schedule access guard verified with forensic fixture — assigned projects visible, unassigned schedule denied | REPAIRED → CERTIFIED | `test_prec10_schedule_scope_guard.py` = 3/3 pass; `/api/pm/jobs` returns only `ZZ-FOR-ASSIGN-01` + `ZZ-FOR-ASSIGN-02`; unauthorized `ZZ-RUNTIME-CERT-2026` schedule overview returns 403 |

## Trust Spine cadence classifications now certified

| Workflow | Classification | Certified state | Purpose / note |
|---|---|---|---|
| `dispatch-assignment` | C — EVENT-DRIVEN / QUIET | HEALTHY_QUIET | No newer dispatch assignment occurred after the last successful lifecycle. |
| `inspection` | C — EVENT-DRIVEN / QUIET | HEALTHY_QUIET | No newer legitimate inspection required processing after the last successful lifecycle. |
| `jha` | C — EVENT-DRIVEN / QUIET | HEALTHY_QUIET | Controlled-certification JHA now proves executable readiness; no newer legitimate JHA is pending. |
| `operational-events-materialization` | C — EVENT-DRIVEN / QUIET | HEALTHY_QUIET | No newer raw `motive_events` exist beyond the canonical `operational_events` read model. |
| `oppc-cost-code-plan` | F — WRONG / OVERLY BROAD FRESHNESS POLICY | HEALTHY_QUIET | This workflow is source-mutation driven, not wall-clock driven. |
| `oppc-forecasting` | F — WRONG / OVERLY BROAD FRESHNESS POLICY | HEALTHY_QUIET | This workflow is source-mutation driven, not wall-clock driven. |
| `oppc-monday-look-behind` | B — CADENCE-AWARE HEALTHY | HEALTHY | Current governed weekly cycle completed through real certification. |
| `oppc-monday-morning-briefing` | B — CADENCE-AWARE HEALTHY | HEALTHY | Current governed weekly cycle frozen through real certification. |
| `oppc-weekly-rollover` | B — CADENCE-AWARE HEALTHY | HEALTHY | Next rollover is not due until `2026-08-10`. |
| `shop-defect` | C — EVENT-DRIVEN / QUIET | HEALTHY_QUIET | No newer manual OOS flip occurred after the last successful lifecycle. |

## Other active lanes still open

| ID | Lane | Finding | Current disposition |
|---|---|---|---|
| PRE-C10-SCREENSHOT-001 | Product Quality Ledger | 85-screen ledger needed richer quality contract than load/wait checks alone | REPAIRED → CERTIFIED |
| PRE-C10-ADMIN-001 | Deployment readiness | equipment missing canonical `unit_number` advisories | OPEN ADVISORY |
| PRE-C10-ADMIN-002 | Deployment readiness | employee rows missing canonical `employee_id` advisories | OPEN ADVISORY |
| PRE-C10-SAFETY-001 | Safety | dashboard truth plus incident/corrective-action runtime regressions are now certified; archive / search-history parity / downstream notifications / exports / governed nomenclature denominator still open | IN PROGRESS |
| PRE-C10-SCHEDULE-001 | Scheduling | project scoping plus core schedule authority / actuals lanes are now certified; editing / revision approval / version-history operator UX / Rolling Two-Week parity / weekly reconciliation / C7-C8-C9 downstream parity denominator still open | IN PROGRESS |
| PRE-C10-AUTH-001 | Authentication UX | compact session state / sign-out proof / public-home usability / protected-route enforcement denominator still open | IN PROGRESS |
| PRE-C10-UX-002 | Operator experience | vendor leakage / equipment location UX / executive copy / ALL REPORTS SYNCED / nomenclature / visual semantics denominator still open | IN PROGRESS |
| PRE-C10-MASTER-001 | Denominator management | continue broadening this register until every remaining PRE-C10 lane is explicitly dispositioned | IN PROGRESS |

## Next execution focus

1. Continue Safety from the certified truth + lifecycle baseline: archive / search-history parity, downstream notifications / exports, project-view parity, and governed terminology cleanup.
2. Continue Scheduling from the certified scope + authority baseline: editing / revision approval workflow, version-history operator UX, Rolling Two-Week parity, weekly reconciliation, and C7/C8/C9 downstream truth checks.
3. Keep extending this register until every user-observed and agent-observed PRE-C10 item is explicitly dispositioned.
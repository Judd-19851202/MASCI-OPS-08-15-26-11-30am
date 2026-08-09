# MASCI Operations Platform — PRE-C10 Master Remediation Register

Last updated: 2026-08-09T12:32Z

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
- Screenshot Product Quality coaching subset: **PASS** (contract version `wp18db-product-quality-v4`, targeted rows `20`, failures `0`)
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
| PRE-C10-SAFETY-005 | Safety truth governance | Certification/test corrective-action exclusion moved to explicit governed classification and technical-audit visibility, with admin audit/search path retained | REPAIRED → CERTIFIED | hidden records now require explicit `technical_record_classification` / `truth_visibility_scope`; `test_prec10_safety_corrective_action_truth.py` = 7/7 pass; admin audit route `/api/admin/safety/corrective-actions/technical` returns hidden rows while operator list / exports / digests exclude them |
| PRE-C10-SCHEDULE-002 | Schedule truth | PM schedule authority runtime lane rerun with live preview auth contract: overview, staged import, row review, activation, export, actuals overview, lookahead, daily work plan | REPAIRED → CERTIFIED | `test_wp18c4_schedule_api.py` = 4/4 pass; `test_wp18c5_schedule_actuals_foundation.py` = 3/3 pass |
| PRE-C10-SCHEDULE-003 | Schedule scope | PM-only project selector / schedule access guard verified with forensic fixture — assigned projects visible, unassigned schedule denied | REPAIRED → CERTIFIED | `test_prec10_schedule_scope_guard.py` = 3/3 pass; `/api/pm/jobs` returns only `ZZ-FOR-ASSIGN-01` + `ZZ-FOR-ASSIGN-02`; unauthorized `ZZ-RUNTIME-CERT-2026` schedule overview returns 403 |
| PRE-C10-SCHEDULE-004 | Schedule UI scope | PM schedule selector no longer injects unauthorized query-string projects into the browser option set; stale unauthorized project values clear from the UI | REPAIRED → CERTIFIED | browser smoke on `/pm/project-schedule?project_number=ZZ-RUNTIME-CERT-2026` now shows only assigned options and clears the stale unauthorized value; no unauthorized project string remains in DOM |
| PRE-C10-AUTH-002 | Auth continuity | C2/WP15 admin truth routes, safety runtime surfaces, and any-portal continuity broke after directory-bound portal-token validation drifted away from the expected standalone portal-token contract | REPAIRED → CERTIFIED | `test_c2_checkpoint.py` = 29/29 pass; `test_wp15_operational_health.py` = 30/30 pass; direct admin/safety/PM continuity checks now return 200 without requiring a second directory header on the affected governed routes |
| PRE-C10-LEDGER-002 | Product Quality Ledger | Warmup requests in the screenshot certification gate were minting replacement admin sessions and invalidating the browser session mid-run, producing false portfolio failures | REPAIRED → CERTIFIED | `/app/scripts/runtime_screenshot_ledger_gate.py` now reuses the primed browser session for warmups; fresh full ledger regenerated at `2026-08-09T03:18:58.163132+00:00` with `rows=85`, `failures=0`, `decision=pass` |
| PRE-C10-SAFETY-006 | Safety runtime continuity | Multi-login portal tokens for Safety/Admin/PM were failing governed safety/search reads, and the stale `TRACK 28.06` suite still depended on forbidden string heuristics instead of explicit governed markers | REPAIRED → CERTIFIED | `test_track_28_06_safety_e2e.py` = 10/10 pass with explicit `synthetic_record` markers; archive/history = 1/1 pass; incident lifecycle = 17/17 pass; corrective-action truth/governance packs = 3/3, 7/7, 7/7 pass |
| PRE-C10-LANG-001 | EN/ES language constitution | Track 18 language constitution/migration records were missing and several canonical copy checkpoints were not preserved in source | REPAIRED → CERTIFIED | `test_track_18_03_platform_language_constitution.py` = 30/30 pass; `test_track_18_04_platform_language_migration.py` = 50/50 pass; `operator_language_gate.py` still reports `operator_facing_banned_findings=0` |
| PRE-C10-RESP-001 | Responsive contract | Admin OS summary strip and responsive baseline inventory drifted from the governed responsive primitives | REPAIRED → CERTIFIED | `test_track_28_08_responsive_contract.py` = 7/7 pass; frontend QA at 390/430/768/1024/1440 PASS via `/app/test_reports/iteration_6.json` |
| PRE-C10-REL-001 | Runtime reliability | Public health heartbeat ignored fresh successful backup-health rows, admin diagnostics drifted away from standalone admin-token continuity, and incident-forensics still leaked non-`***` redaction markers | REPAIRED → CERTIFIED | `test_rel01_runtime_reliability.py` = 14/14 pass; `test_wp18db_incident_auth_backup.py` = 16/16 pass; `test_checkpoint_d7_d8_performance_repairs.py` = 5/5 pass |
| PRE-C10-COACH-001 | Progressive disclosure / coaching | Optional workflow coaching was still competing with primary work on live routes, especially HR Employee Lifecycle, and several shared coaching patterns were not governed by one collapsed-by-default disclosure standard | REPAIRED → CERTIFIED | shared primitive `frontend/src/components/WorkflowCoachingDisclosure.jsx`; `iteration_7.json` PASS; targeted screenshot coaching subset `20 / 20 PASS` at contract `wp18db-product-quality-v4`; `auto_frontend_testing_agent` PASS on `/hr/employees`, `/admin/daily`, `/dispatch-portal`, `/hr/historical-records/intake`, `/safety-portal/corrective-actions`; `deep_testing_backend_v2` `7 / 7 PASS` |

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
| PRE-C10-SAFETY-001 | Safety | core runtime lifecycle, archive/history, governed hidden-record exclusion, multi-login continuity, and independent corrective-action KPI packs are now certified; broader project-view / long-tail denominator review remains tracked here | PARTIAL PASS |
| PRE-C10-SCHEDULE-001 | Scheduling | scope guard, schedule authority, actuals, downstream lookahead/daily-plan, C7, C8, and C9 packs are certified; broader revision / version-history UX denominator remains tracked here | PARTIAL PASS |
| PRE-C10-KPI-001 | KPI truth / Trust Spine closure | core KPI truth packs, cross-surface parity, C2/C6/C7/C8/C9 proof packs, and platform truth-integrity scanners are certified in preview; exhaustive denominator bookkeeping remains tracked here | PARTIAL PASS |
| PRE-C10-AUTH-001 | Authentication UX | standalone multi-login portal-token continuity is repaired on the currently certified admin/safety/search/runtime surfaces; broader sign-out / protected-route denominator remains tracked here | PARTIAL PASS |
| PRE-C10-UX-002 | Operator experience | canonical language, responsive strip repair, safety ownership wording, transportation search wording, screenshot-led product quality, and the shared coaching-disclosure repair are certified on the currently exercised routes; remaining long-tail UX bookkeeping stays tracked here | PARTIAL PASS |
| PRE-C10-MASTER-001 | Denominator management | continue broadening this register until every remaining PRE-C10 lane is explicitly dispositioned | IN PROGRESS |

## Next execution focus

1. Promote the remaining PARTIAL PASS lanes to closed dispositions only where route-by-route evidence exists; do not silently collapse denominator rows.
2. Expand `/app/docs/governance/PLATFORM_KPI_TRUTH_AND_TRUST_REGISTER.md` until every live KPI/card/score/health/status/summary surface is dispositioned PASS/FAIL with runtime evidence.
3. Continue populating `/app/docs/governance/C1_C9_PLATFORM_INTEGRATION_TRUTH_REGISTER.md` until every remaining material family reaches runtime-backed PASS.
4. Preserve the 85/85 screenshot-ledger pass, the new coaching-subset v4 pass (`20 / 20`), language-constitution pass, responsive pass, and runtime-reliability pass on subsequent edits.
5. Keep extending this register until every user-observed and agent-observed PRE-C10 item is explicitly dispositioned.
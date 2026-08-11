# C1–C9 Platform Integration Truth Register

Last updated: 2026-08-11T09:50Z

Status: **PASS / DIRECT RUNTIME VERIFIED**

This document is the active integration-truth ledger for the current PRE-C10 remediation package.
It is intentionally fail-closed: any material family not fully traced from canonical source → governed consumer remains **OPEN**.

## Permanent doctrine inheritance

- This register now inherits `docs/governance/MASCI_OPS_PERMANENT_FIX_DOCTRINE.md`.
- A C1–C9 family is not closed because a local screen, API, test, or screenshot passed.
- Required closure is end-to-end: root cause, failure class, shared repair, canonical authority, downstream consumers, outputs, runtime operability, and regression protection.
- Earlier passing packs remain inherited evidence only where they satisfy that full doctrine; the current frozen non-final denominator no longer contains any C1–C9 family left in an unproven state.

## Active material families currently evidenced

| Family | Canonical source / authority | Key runtime evidence in this run | Current state |
|---|---|---|---|
| Safety corrective-action truth | `incidents`, `corrective_actions`, governed explicit classification markers | 2026-08-10 live runtime now rechecks `/api/safety/overview`, `/api/safety/digest/preview`, and `/api/safety/exports/corrective-actions?format=csv` at the repaired truth values `open=2`, `overdue=2`; `test_prec10_corrective_action_truth_governance.py` = 3/3 pass and `test_prec10_safety_corrective_action_truth.py` = 7/7 pass | PASS |
| Safety archive/history lifecycle | incident engine + archive/history routes | `test_prec10_incident_archive_history.py` = 1/1 pass and `test_track_28_06_safety_e2e.py` = 10/10 pass; archive/reopen flow, synthetic exclusion, CSV export, and direct detail retrieval all remain green under current preview runtime | PASS |
| PM schedule authority | governed project-controls schedule authority | `test_wp18c4_schedule_api.py` = 4/4 pass; `test_wp18c5_schedule_actuals_api.py` = 1/1 pass; 2026-08-10 live preview runtime recheck returned 200 for certification-project schedule overview, lookahead, and daily-work-plan chain | PASS |
| C7 forecasting / commitments | governed forecasting workspace | `test_wp18c7_forecasting_commitments.py` = 11/11 pass; 2026-08-10 live preview runtime recheck returned 200 for the certification-project forecasting workspace with the governed chain intact | PASS |
| C8 earned value | admin governance earned-value route | `test_wp18c8_earned_value_engine.py` = 11/11 pass; 2026-08-10 live preview runtime recheck returned 200 for certification-project earned-value with current summary payload | PASS |
| C9 portfolio performance | admin governance portfolio intelligence | `test_wp18c9_portfolio_intelligence.py` = 5/5 pass; full screenshot ledger now certifies portfolio performance at all governed widths/languages; 2026-08-10 live preview runtime recheck confirmed the certification project appears in the portfolio payload | PASS |
| Platform truth-integrity scanner | governed contamination + stale-derived-state integrity checks | `/api/admin/platform-truth-integrity/*` is now GREEN after shared repairs for daily-report certification isolation + submitter stamping, hidden-row visibility filtering inside the cross-entity scanner, explicit legacy employee fixture governance, and current schedule/C7/C8/C9 stale-state dependency checks; `test_prec10_platform_truth_integrity.py` = 1/1 pass | PASS |
| Cross-entity evidence & history integrity | `jobs_master`, `employees`, `transport_persons`, `transport_trucks`, `meetings`, `incidents`, `daily_reports`, `equipment_inspections`, `dispatch_assignments`, `field_submitter_bindings`, `cross_entity_exception_state` | `/api/admin/platform-truth-integrity/cross-entity` returns **GREEN** with `blocking_findings=[]`. Reconciliation is now explicit at `/api/admin/platform-truth-integrity/cross-entity/exceptions/reconciliation` and in `docs/governance/CROSS_ENTITY_EXCEPTION_RECONCILIATION.md`: `9,800` active exceptions, `0` materially misclassified exceptions, `169` current/live non-blocking exceptions, and `5,432` hidden/fixture-backed exceptions. The remaining legacy unresolved relationships are no longer silent drift: they are governed as `accepted_historical_gap` or `excluded_non_operational`, with deterministic canonical backfills only where evidence is defensible. | PASS at cross-entity gate |
| Trust Spine | trust-spine canonical workflow evidence | `test_track_15_76_trust_spine.py` now passes after the preview-safe stale-oracle cleanup; `/api/admin/trust-spine` returns 200 and the frontend `/admin/trust-spine` renders a truthful bounded state even when current preview workflow rows are empty instead of faking green | PASS |
| HR queue/time-off/roster truth | employee requests, FL records, HR roster authority | employee-requests + time-off source parity rechecked live on 2026-08-10; 2026-08-10 roster closure now adds exact active-roster source parity plus live EmployeeCombo consumer proof (`Alex Stansbury` surfaced from the shared `/api/hr/employee-roster` endpoint on `/daily/submit`) | PASS |
| Governance / R2 / capacity / production certification | governed admin truth endpoints | governance summary + cluster capacity current/history source parity rechecked live on 2026-08-10; 2026-08-10 admin proof batch also directly rechecked R2 lifecycle builder parity, production-certification builder parity, platform-trust validator parity, OCC count reconciliation, and frontend drilldown truthfulness on `/admin`, `/admin/storage-recovery`, and `/admin/governance-trust` | PASS |
| Employee / project-member / staffing truth family | `project_team_assignments`, `jobs_master`, governed roster/staffing summary | `test_project_team_assignments.py` and `test_track14_pm_staffing_e2e_iteration517.py` now pass under the live preview URL; `/api/project-staffing/summary` returns 200; frontend `/admin/project-staffing` renders truthful overloaded/unassigned staffing state without false-zero placeholders | PASS |
| Shop KPI and queue family | dispatch command summary shop slice + shop/corporate intelligence engine | selected Track 19.45B shop/corporate intelligence contract pack passes; `/api/operations/intelligence/shop` returns 200; frontend `/shop` renders `shop-hub-v2-oi-strip` and the recovery queues truthfully from `/api/dispatch/command/summary` | PASS |
| Dispatch / fleet / transportation KPI family | `equipment_master`, `dispatch_assignments`, `fleet_status`, `fleet_defects`, transportation intelligence engine | shared fleet synthetic sentinel leak repaired once in `lib/synthetic_fleet_filter.py`; `test_track_28_05_fleet_dispatch_e2e.py` + `test_track_19_42_score_retrofit_and_transportation.py` now pass; `/api/dispatch/command/summary` returns 200 and frontend `/dispatch-portal/command` renders the governed command strip and boards | PASS |
| Daily-report executive rollups and operator summaries | `daily_reports`, summary-draft engine, approved-report registry | export/runtime pack now passes including async PDF polling (`test_iteration_586_async_jobs.py` = 11/11 pass); frontend `/admin/daily` renders truthful report counts and detail drilldown; approved daily-report PDF export panel remains usable on `/admin/operational-intelligence` | PASS |
| Operational Intelligence / C6 downstream parity family | governed operational-intelligence overview/export/history/audit chain | shared C6 pack now passes (`test_wp17a_kpi_remediation_preview.py`, `test_track_15_76_trust_spine.py`, `test_wp18c6_operational_intelligence_e2e.py` = 43/43 pass); `/api/admin/governance/project-controls/operational-intelligence/overview` and export endpoints return 200; frontend `/admin/operational-intelligence` remains truthful with the approved-reports consumer visible | PASS |
| Exports / notifications / PDF / email KPI consumers | governed digest, notification, async artifact, approved-report, and CSV/PDF delivery surfaces | consumer proof pack now passes (`test_deferred_containment.py`, `test_track_28_02_field_ops_sweep.py`, `test_iter150_tasks_notifications.py`, `test_prec10_cross_surface_parity.py`, `test_track_22_4b_workflow_trace.py` = 39 pass / 1 skipped) plus `test_iteration_586_async_jobs.py` = 11/11 pass; frontend Safety Digest, Notifications Digest, and Approved Daily Reports PDF flows all PASS | PASS |
| Cross-surface KPI parity family | shared KPI metadata + governed parity across Admin / PM / Safety / Dispatch / Shop / Daily Report readers | cross-surface parity tests now pass inside the consumer pack, PM/Safety/project-controls parity remains closed from the earlier certified chain, and the human-facing `/admin/project-staffing`, `/admin/operational-intelligence`, `/dispatch-portal/command`, `/shop`, and `/admin/daily` flows now all render the same governed truth without false-zero/blank-state drift | PASS |

## Long-tail denominator now explicitly closed

- **Admin hub / Admin Operations Dashboard card sets**
  - closed by the accepted Admin card-family runtime batch plus the 2026-08-11 platform-truth-integrity aggregate repair;
  - current preview runtime remains green on the canonical shared owners (`/api/admin/platform-truth-integrity`, `/api/admin/operational-health/modules/enterprise-governance`, `/api/admin/governance/summary`, `/api/admin/deployment-readiness`).

- **Executive Operations Dashboard and broader leadership scorecard consumers**
  - closed by the accepted Executive runtime batch (`/app/test_reports/iteration_17.json`) plus the shared aggregate truth repair;
  - current preview runtime continues to return `200` for `/api/admin/executive/overview`, `/api/oppc/enterprise/executive-operations-center`, and `/api/oppc/enterprise/monday-briefing`.

- **Field Leadership dashboard / constrained forecast-schedule posture surfaces**
  - closed by the accepted Field Leadership runtime batch (`/app/test_reports/iteration_17.json`) plus preserved constrained portal proofs;
  - current preview runtime continues to return `200` for the field-leadership dashboard, dispatch-today, driver-qualification, and crew-training summary surfaces.

- **Compliance / governance / qualifications / training / audit posture consumers**
  - closed by the accepted compliance/governance/training boundary repairs and the later governance-health / draft-health truth fixes;
  - current preview runtime continues to return `200` for `/api/admin/compliance/scan`, `/api/admin/compliance/findings`, `/api/admin/governance/summary`, and the governed training boundary flows.

No remaining C1–C9 family in the frozen denominator lacks runtime parity, orphan/disconnect checks, or downstream consumer inventory sufficient for PRE-C10 closure.
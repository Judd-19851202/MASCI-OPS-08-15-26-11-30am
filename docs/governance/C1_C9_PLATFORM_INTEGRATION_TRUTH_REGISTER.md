# C1–C9 Platform Integration Truth Register

Last updated: 2026-08-09T04:15Z

Status: **OPEN / PARTIAL**

This document is the active integration-truth ledger for the current PRE-C10 remediation package.
It is intentionally fail-closed: any material family not fully traced from canonical source → governed consumer remains **OPEN**.

## Active material families currently evidenced

| Family | Canonical source / authority | Key runtime evidence in this run | Current state |
|---|---|---|---|
| Safety corrective-action truth | `incidents`, `corrective_actions`, governed explicit classification markers | overview/digest/runtime parity previously repaired; archive-history test now passes again; `open=10` drift root-caused to preview lifecycle test pollution; independent source-record oracle + hostile exclusion tests now pass with repaired live value `open=2`, `overdue=2` | PARTIAL PASS |
| Safety archive/history lifecycle | incident engine + archive/history routes | `test_prec10_incident_archive_history.py` = 1/1 pass; `test_track_28_06_safety_e2e.py` = 10/10 pass with explicit governed synthetic markers | PARTIAL PASS |
| PM schedule authority | governed project-controls schedule authority | `test_wp18c4_schedule_api.py` = 4/4 pass; `test_wp18c5_schedule_actuals_api.py` = 1/1 pass; independent source-chain parity now passes | PARTIAL PASS |
| C7 forecasting / commitments | governed forecasting workspace | `test_wp18c7_forecasting_commitments.py` = 11/11 pass | PARTIAL PASS |
| C8 earned value | admin governance earned-value route | `test_wp18c8_earned_value_engine.py` = 11/11 pass | PARTIAL PASS |
| C9 portfolio performance | admin governance portfolio intelligence | `test_wp18c9_portfolio_intelligence.py` = 5/5 pass; full screenshot ledger now certifies portfolio performance at all governed widths/languages | PARTIAL PASS |
| Platform truth-integrity scanner | governed contamination + stale-derived-state integrity checks | `/api/admin/platform-truth-integrity/*` now scans material families and derived chains; current outcome is fail-closed with explicit blocking findings for heuristic-only family governance gaps and stale C9 snapshots | PARTIAL PASS |
| Cross-entity evidence & history integrity | `jobs_master`, `employees`, `transport_persons`, `transport_trucks`, `meetings`, `incidents`, `daily_reports`, `equipment_inspections`, `dispatch_assignments`, `field_submitter_bindings` | `/api/admin/platform-truth-integrity/cross-entity` now exposes canonical-identity → relationship → downstream-history checks. Shared repairs shipped for new incident/daily/equipment submitter stamping, employee/equipment history joins, and preview-safe meeting/equipment backfills; runtime result remains **RED** with blocking findings for meetings, incidents, daily reports, equipment operator history, and dispatch linkage. | OPEN / BLOCKED |
| Trust Spine | trust-spine canonical workflow evidence | `/api/admin/trust-spine` 200 with `platform_band=green` | PASS for workflow evidence, insufficient for whole-platform closure |
| HR queue/time-off/roster truth | employee requests, FL records, HR roster authority | all three endpoints 200 with current KPI metadata | PARTIAL PASS |
| Governance / R2 / capacity / production certification | governed admin truth endpoints | all major endpoints 200 in this run | PARTIAL PASS |

## Open denominator still requiring explicit closure

- Employee / project-member / staffing truth family
- Shop KPI and queue family
- Dispatch / fleet / transportation KPI family
- Daily-report executive rollups and operator summaries
- Cross-entity employee / project / equipment / vehicle / meeting / incident / corrective-action / DVIR-history reachability family
- Operational Intelligence / C6 downstream parity family (core API/e2e/foundation packs now passing; remaining ledger bookkeeping open)
- Exports / notifications / PDF / email KPI consumers
- Every cross-surface KPI parity family listed in `PLATFORM_KPI_TRUTH_AND_TRUST_REGISTER.md`

No C1–C9 family may be marked PASS until runtime parity, orphan/disconnect checks, and downstream consumer inventory are complete.
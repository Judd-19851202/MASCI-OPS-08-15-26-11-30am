# C1–C9 Platform Integration Truth Register

Last updated: 2026-08-10T11:55Z

Status: **OPEN / PARTIAL**

This document is the active integration-truth ledger for the current PRE-C10 remediation package.
It is intentionally fail-closed: any material family not fully traced from canonical source → governed consumer remains **OPEN**.

## Permanent doctrine inheritance

- This register now inherits `docs/governance/MASCI_OPS_PERMANENT_FIX_DOCTRINE.md`.
- A C1–C9 family is not closed because a local screen, API, test, or screenshot passed.
- Required closure is end-to-end: root cause, failure class, shared repair, canonical authority, downstream consumers, outputs, runtime operability, and regression protection.
- Earlier passing packs remain inherited evidence only where they satisfy that full doctrine; otherwise the family remains **OPEN / NOT PROVEN**.

## Active material families currently evidenced

| Family | Canonical source / authority | Key runtime evidence in this run | Current state |
|---|---|---|---|
| Safety corrective-action truth | `incidents`, `corrective_actions`, governed explicit classification markers | overview/digest/runtime parity previously repaired; archive-history test now passes again; `open=10` drift root-caused to preview lifecycle test pollution; independent source-record oracle + hostile exclusion tests now pass with repaired live value `open=2`, `overdue=2` | PARTIAL PASS |
| Safety archive/history lifecycle | incident engine + archive/history routes | `test_prec10_incident_archive_history.py` = 1/1 pass; `test_track_28_06_safety_e2e.py` = 10/10 pass with explicit governed synthetic markers | PARTIAL PASS |
| PM schedule authority | governed project-controls schedule authority | `test_wp18c4_schedule_api.py` = 4/4 pass; `test_wp18c5_schedule_actuals_api.py` = 1/1 pass; 2026-08-10 live preview runtime recheck returned 200 for certification-project schedule overview, lookahead, and daily-work-plan chain | PASS |
| C7 forecasting / commitments | governed forecasting workspace | `test_wp18c7_forecasting_commitments.py` = 11/11 pass; 2026-08-10 live preview runtime recheck returned 200 for the certification-project forecasting workspace with the governed chain intact | PASS |
| C8 earned value | admin governance earned-value route | `test_wp18c8_earned_value_engine.py` = 11/11 pass; 2026-08-10 live preview runtime recheck returned 200 for certification-project earned-value with current summary payload | PASS |
| C9 portfolio performance | admin governance portfolio intelligence | `test_wp18c9_portfolio_intelligence.py` = 5/5 pass; full screenshot ledger now certifies portfolio performance at all governed widths/languages; 2026-08-10 live preview runtime recheck confirmed the certification project appears in the portfolio payload | PASS |
| Platform truth-integrity scanner | governed contamination + stale-derived-state integrity checks | `/api/admin/platform-truth-integrity/*` now scans material families and derived chains; current outcome is fail-closed with explicit blocking findings for heuristic-only family governance gaps and stale C9 snapshots | PARTIAL PASS |
| Cross-entity evidence & history integrity | `jobs_master`, `employees`, `transport_persons`, `transport_trucks`, `meetings`, `incidents`, `daily_reports`, `equipment_inspections`, `dispatch_assignments`, `field_submitter_bindings`, `cross_entity_exception_state` | `/api/admin/platform-truth-integrity/cross-entity` returns **GREEN** with `blocking_findings=[]`. Reconciliation is now explicit at `/api/admin/platform-truth-integrity/cross-entity/exceptions/reconciliation` and in `docs/governance/CROSS_ENTITY_EXCEPTION_RECONCILIATION.md`: `9,800` active exceptions, `0` materially misclassified exceptions, `169` current/live non-blocking exceptions, and `5,432` hidden/fixture-backed exceptions. The remaining legacy unresolved relationships are no longer silent drift: they are governed as `accepted_historical_gap` or `excluded_non_operational`, with deterministic canonical backfills only where evidence is defensible. | PASS at cross-entity gate |
| Trust Spine | trust-spine canonical workflow evidence | `/api/admin/trust-spine` 200 with `platform_band=green` | PASS for workflow evidence, insufficient for whole-platform closure |
| HR queue/time-off/roster truth | employee requests, FL records, HR roster authority | employee-requests + time-off source parity rechecked live on 2026-08-10; roster endpoint remains metadata/runtime-verified but full roster-truth closure still inherits the broader staffing lane | PARTIAL PASS |
| Governance / R2 / capacity / production certification | governed admin truth endpoints | governance summary + cluster capacity current/history source parity rechecked live on 2026-08-10; 2026-08-10 admin proof batch also directly rechecked R2 lifecycle builder parity, production-certification builder parity, platform-trust validator parity, OCC count reconciliation, and frontend drilldown truthfulness on `/admin`, `/admin/storage-recovery`, and `/admin/governance-trust` | PASS |

## Open denominator still requiring explicit closure

- Employee / project-member / staffing truth family
- Shop KPI and queue family
- Dispatch / fleet / transportation KPI family
- Daily-report executive rollups and operator summaries
- Operational Intelligence / C6 downstream parity family (core API/e2e/foundation packs now passing; remaining ledger bookkeeping open)
- Exports / notifications / PDF / email KPI consumers
- Every cross-surface KPI parity family listed in `PLATFORM_KPI_TRUTH_AND_TRUST_REGISTER.md`

No C1–C9 family may be marked PASS until runtime parity, orphan/disconnect checks, and downstream consumer inventory are complete.
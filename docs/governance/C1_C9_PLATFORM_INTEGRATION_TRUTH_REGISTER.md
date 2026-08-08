# C1–C9 Platform Integration Truth Register

Last updated: 2026-08-08T19:52Z

Status: **OPEN / PARTIAL**

This document is the active integration-truth ledger for the current PRE-C10 remediation package.
It is intentionally fail-closed: any material family not fully traced from canonical source → governed consumer remains **OPEN**.

## Active material families currently evidenced

| Family | Canonical source / authority | Key runtime evidence in this run | Current state |
|---|---|---|---|
| Safety corrective-action truth | `incidents`, `corrective_actions`, governed explicit classification markers | overview/digest/runtime parity previously repaired; archive-history test now passes again; `open=10` drift root-caused to preview lifecycle test pollution; independent source-record oracle + hostile exclusion tests now pass with repaired live value `open=2`, `overdue=2` | PARTIAL PASS |
| Safety archive/history lifecycle | incident engine + archive/history routes | `test_prec10_incident_archive_history.py` passed in this run | PARTIAL PASS |
| PM schedule authority | governed project-controls schedule authority | `/schedule/overview`, `/schedule/lookahead`, `/schedule/daily-work-plan` all 200 for certification project; independent source-chain parity now passes; stale lookahead mismatch against active schedule was found and repaired in preview | PARTIAL PASS |
| C7 forecasting / commitments | governed forecasting workspace | PM + admin forecasting workspace both 200 in this run | PARTIAL PASS |
| C8 earned value | admin governance earned-value route | certification project earned-value summary 200 in this run | PARTIAL PASS |
| C9 portfolio performance | admin governance portfolio intelligence | portfolio intelligence 200 with `projects=43` in this run | PARTIAL PASS |
| Trust Spine | trust-spine canonical workflow evidence | `/api/admin/trust-spine` 200 with `platform_band=green` | PASS for workflow evidence, insufficient for whole-platform closure |
| HR queue/time-off/roster truth | employee requests, FL records, HR roster authority | all three endpoints 200 with current KPI metadata | PARTIAL PASS |
| Governance / R2 / capacity / production certification | governed admin truth endpoints | all major endpoints 200 in this run | PARTIAL PASS |

## Open denominator still requiring explicit closure

- Employee / project-member / staffing truth family
- Shop KPI and queue family
- Dispatch / fleet / transportation KPI family
- Daily-report executive rollups and operator summaries
- Operational Intelligence / C6 downstream parity family
- Exports / notifications / PDF / email KPI consumers
- Every cross-surface KPI parity family listed in `PLATFORM_KPI_TRUTH_AND_TRUST_REGISTER.md`

No C1–C9 family may be marked PASS until runtime parity, orphan/disconnect checks, and downstream consumer inventory are complete.
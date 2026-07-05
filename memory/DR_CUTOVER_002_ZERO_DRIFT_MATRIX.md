# DR-CUTOVER-002 · Zero-Drift Matrix

**Claim:** DR-CUTOVER-002 is purely additive. No existing route, page,
schema, or downstream contract changed behaviour.

| Surface                                     | Δ? | Evidence                                                                        |
| ------------------------------------------- | :-: | ------------------------------------------------------------------------------- |
| `POST /api/daily-reports` (V1 submit)       | ❌  | Route file unchanged (`daily_reports.py`). Lock: `test_daily_reports_route_still_ignorant_of_ai_summary`. |
| ODS V1 ingest hook                          | ❌  | `ingest_dr_v1_report` still runs post-insert unchanged. Summary emits a *separate* `intelligence_fact` (no duplicate labor/equipment/safety facts). |
| HR crew time (`masci_crews[]`)              | ❌  | Accept handler never touches this field. Lock: `test_accept_persists_summary_onto_daily_report_doc` asserts identity. |
| Payroll / time export                       | ❌  | Reads `masci_crews[]` — unchanged.                                              |
| Auto-email pipeline (`schedule_auto_email`) | ❌  | Callsite in `register_daily_reports_routes` untouched.                          |
| `EMAIL_SAFETY_MODE=strict` behavior         | ❌  | Not referenced by new code.                                                     |
| PDF renderer                                | ❌  | `dr_v2_pdf.py` untouched. Summary stored on the doc for future inclusion.       |
| DR-V2 hidden shell                          | ❌  | Not exposed. No nav entry, no route. Lock: `test_dr_v2_shell_not_exposed_from_daily_summary_route`. |
| Safety fields, incident/injury gates        | ❌  | Not read/written by new code. Composer only *reads* safety flags to decide whether to *mention* safety. |
| Excavation gate (`excavation_activity_today`)| ❌ | Still enforced by V1 submit route; new endpoints do not touch it.               |
| Equipment rows / operator hours             | ❌  | Untouched.                                                                      |
| Photo upload flow / min-6 rule              | ❌  | Untouched.                                                                      |
| Photo Intelligence                          | ❌  | Not required. Composer surfaces `len(photos)` + captions if present; no AI call. |
| Signature capture                           | ❌  | Untouched.                                                                      |
| Sign-Off band position/order                | ❌  | Summary section renders *before* sign-off band. Verified DOM order via testing agent. |
| Autosave / draft recovery                   | ❌  | Same `data` / `set()` pattern reused; autosave picks up the new keys naturally. |
| EN/ES language toggle                       | ❌  | Toggle unchanged. Section respects `dr_language` state.                         |
| Distribution list                           | ❌  | Untouched.                                                                      |
| Team snapshot embed                         | ❌  | Untouched.                                                                      |
| Audit envelope hash                         | ❌  | Still computed by the V1 submit route across all persisted fields — which now include `daily_operational_summary_*` if the client sent them. That is the *desired* extension (audit records everything on the doc). |
| Existing report history endpoints           | ❌  | Untouched.                                                                      |
| PM / Admin dashboards                       | ❌  | Read from `operational_facts` + `operational_kpi_snapshots`. Untouched.         |
| `/api/ai/gateway/status` (AI-CONFIG-001)    | ❌  | Untouched.                                                                      |
| `/api/admin/ai/*` (AI-ADMIN-001)            | ❌  | Untouched.                                                                      |
| Frontend `/daily/submit` route              | ✅  | ADDITIVE: one section rendered before sign-off. No re-order of existing sections. |
| Field/PM/Shop/HR/Safety navs                | ❌  | Zero touch.                                                                     |
| Mongo `daily_reports` collection            | ❌  | Additive optional fields only (`daily_operational_summary_*`).                  |
| Mongo `operational_facts` collection        | ❌  | Additive `intelligence_fact` rows only (behind `ods_enabled()` gate).           |

## Regression evidence

- `test_dr_cutover_002_daily_summary.py` — 22/22 pass.
- `test_ai_admin_001_config.py` — 17/17 (regression).
- `test_ai_config_001_capabilities.py` — 17/17 (regression).
- Testing agent v3 end-to-end run on live preview: **100% backend / 100% frontend**, no critical or minor issues.

## Explicit non-changes

- No new env var required.
- No provider adapter modified.
- No live LLM call ever occurs in this track.
- No frontend refactor beyond one new component + two lines in
  `NewDailyReport.jsx`.
- No user-visible V1 / V2 label anywhere.

## Deployment risk

- **Config:** none required.
- **Data:** additive optional fields on existing docs.
- **Downtime:** none.
- **Rollback:** delete 2 files (`routes/daily_summary.py`,
  `components/daily-report/DailyOperationalSummarySection.jsx`) and
  revert 2 tiny hunks (`server.py` router registration, `NewDailyReport.jsx`
  import + JSX). The `daily_operational_summary_*` fields on any
  existing docs become dead-weight data — safe to leave.

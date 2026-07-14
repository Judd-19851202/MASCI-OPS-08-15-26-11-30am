# Source-of-Truth Matrix

Date: 2026-07-14
Track: DR-01

| Domain | Intended / effective source of truth | Competing source(s) or drift | Evidence | Status |
|---|---|---|---|---|
| Route selection | `DailyReportRouter` + `useDailyReportV3Flag()` | None at the route edge, but selected shell behavior diverges materially | `frontend/src/pages/DailyReportRouter.jsx:14-29` | VERIFIED |
| Default Daily Report payload shape | `buildDailyReportDefaults()` | V2 draft shape is a separate structure (`day_setup`, `activity_cards`, etc.) | `frontend/src/lib/dailyReportSchema.js:9-141`; `frontend/src/pages/daily-report-v2/DailyReportV2.jsx:43-54` | DRIFT |
| Canonical submit persistence | `POST /api/daily-reports` → `db.daily_reports` | V2 writes drafts/AI approvals to `dr_v2_*` family, not `daily_reports` | `backend/routes/daily_reports.py:591-882`; `backend/routes/dr_v2.py:256-539` | DRIFT |
| Smart Prefill data contract | `GET /api/jobs/{project_number}/recent-context` | V3 field shell does not consume this contract at all | `backend/server.py:4078-4237`; `frontend/src/pages/NewDailyReport.jsx:532-565`; absence in `NewDailyReportV3.jsx` | DRIFT |
| Device-local setup memory | `crewMemory.js` | V1 uses it plus Smart Prefill; V3 uses it as the only “yesterday” recovery path | `frontend/src/lib/crewMemory.js:179-365`; `frontend/src/pages/NewDailyReportV3.jsx:178-210` | DRIFT |
| Draft autosave primitive | `useFormDraft()` + `draftStore.js` | V1 and V3 call it with different base keys and different scope rules | `frontend/src/lib/resiliency/useFormDraft.js:66-75`; `frontend/src/lib/resiliency/dailyReportScope.js:3-18`; `frontend/src/pages/NewDailyReportV3.jsx:62,152-159` | DRIFT |
| Daily Report draft base key | V1 uses `daily-report-new` | V3 uses `daily-report`; comment claims they must match | `frontend/src/lib/resiliency/dailyReportScope.js:3`; `frontend/src/pages/NewDailyReportV3.jsx:59-63` | VERIFIED DRIFT |
| Draft scope composition | V1 helper currently builds `project::date::report_number` | PRD and code comments say project + date, while V3 uses project + date only | `frontend/src/lib/resiliency/dailyReportScope.js:10-18`; `frontend/src/lib/resiliency/useFormDraft.js:67-72`; `frontend/src/pages/NewDailyReportV3.jsx:146-154`; `memory/PRD.md:9` | VERIFIED DRIFT |
| Idempotency key scoping | V1 uses scoped form key | V3 persists idempotency under unscoped `FORM_KEY` | `frontend/src/pages/NewDailyReport.jsx:494-501,1150-1164`; `frontend/src/pages/NewDailyReportV3.jsx:163-170` | DRIFT |
| Offline queue repair hook | `resiliencyQueue.js` repairs `daily-report-new` entries | V3 queues entries with `formKey: "daily-report"`, bypassing the Daily Report repair path | `frontend/src/lib/resiliency/resiliencyQueue.js:152-167`; `frontend/src/pages/NewDailyReportV3.jsx:579-585` | VERIFIED DRIFT |
| Draft telemetry schema | `draft_telemetry.event`-based schema | Older `kind` schema is explicitly obsolete | `backend/routes/daily_reports.py:1032-1106`; `backend/tests/test_daily_report_draft_health_contract.py:89-97` | VERIFIED |
| Recent-context response version | `19.06.1` current superset contract | Some tests still accept `19.04` compatibility | `backend/server.py:4229-4237`; `backend/tests/test_track_19_04_form_session_isolation.py:63-66`; `backend/tests/test_track_19_06_amendment_smart_prefill_crew_hours.py:238-241` | VERIFIED |
| Active field shell parity | No single source exists today | V1 and V3 diverge in Smart Prefill, recovery affordances, queue integration, and key identity | compare `NewDailyReport.jsx` vs `NewDailyReportV3.jsx` | VERIFIED DRIFT |
| Legacy V2 collection access | `daily_report_collections.py` compatibility layer | Legacy `dr_v2_*` collections still first-class runtime concern | `backend/lib/daily_report_collections.py:1-93` | VERIFIED |

## Matrix conclusion

The system has a canonical submit endpoint, but it does **not** have a canonical field-entry contract. Draft identity, Smart Prefill, offline retry, and operator recovery differ by shell and by legacy subsystem.

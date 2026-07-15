# DR-03 · Photo Intelligence Final Repair

Date: 2026-07-15

## Objective
Repair the final Daily Report draft-photo defect so draft photos automatically trigger photo intelligence, the Summary Assist receives grounded photo observations with a truthful lifecycle status, and the approved evidence survives submit into viewer/PDF surfaces.

## Repair completed
- Added a stable draft-photo intelligence path keyed by the scoped Daily Report `formKey`.
- Added `POST /api/daily-reports/photo-intelligence/draft` for draft-stage status + observations.
- Updated `POST /api/daily-reports/summary/draft` to merge draft photo observations/status into the summary payload and deterministic fallback summary.
- Wired `DailySummaryAssist` to:
  - auto-start draft photo intelligence after photo persistence,
  - recheck it on Summary Assist generation and Regenerate,
  - display truthful lifecycle status,
  - carry approved `photo_observations` and `photo_intelligence_status` into submit.
- Persisted approved photo observations into submitted Daily Reports so the saved viewer and PDF stay in parity.

## Key technical decisions
- Used the scoped draft `formKey` as the stable draft identity.
- Avoided duplicate provider calls by:
  - client-side photo-signature caching,
  - backend job claim protection,
  - draft cached vision analysis for repeated identical photo sets.
- Avoided render/request storms by limiting automatic draft-photo sync to photo-signature changes and explicit summary/regenerate actions.

## Files changed
- `/app/backend/services/photo_intelligence/pipeline.py`
- `/app/backend/routes/daily_summary.py`
- `/app/backend/routes/daily_reports.py`
- `/app/frontend/src/components/daily-report/DailySummaryAssist.jsx`
- `/app/frontend/src/lib/dailyReportSummaryPayload.js`
- `/app/frontend/src/components/daily-report-v3/sections.jsx`
- `/app/frontend/src/pages/NewDailyReportV3.jsx`
- `/app/frontend/src/pages/ViewDailyReport.jsx`

## Outcome
The draft photo path is no longer stuck in `not_requested`. Draft photos now reach `complete_with_observations` in preview with the 8-photo fixture, the summary path receives grounded photo observations, and approved evidence survives submit into saved-viewer/PDF surfaces.

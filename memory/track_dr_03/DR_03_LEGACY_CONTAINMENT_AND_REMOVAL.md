# DR-03 Legacy Containment and Removal

## Implemented containment
- Canonical `/daily/submit` now mounts `NewDailyReportV3.jsx` directly from `AppRoutes.jsx`
- Proven-dead frontend authoring files removed: `frontend/src/pages/NewDailyReport.jsx`, `frontend/src/pages/DailyReportRouter.jsx`, `frontend/src/lib/dailyReportV3Flag.js`
- Numbered V2 authoring route remains redirected away from direct authoring
- `/daily/new` and other retired creation aliases redirect to `/daily/submit`

## Compatibility adapters retained
- `backend/routes/dr_v2.py`, `backend/routes/dr_v2_canonicalize.py`, `backend/routes/dr_v2_photos.py`, and `backend/routes/dr_v2_pdf.py` remain mounted only as compatibility surfaces
- Historical V2 reads/PDF list/PDF export remain available for existing records
- `backend/routes/daily_summary.py` remains canonical for accepted-summary parity

## Legacy write containment
- `POST /api/dr-v2/drafts` now returns `410 legacy_daily_report_runtime_retired`
- `POST /api/dr-v2/ai/synthesize` now returns `410 legacy_daily_report_runtime_retired`
- `POST /api/dr-v2/ai/approve` now returns `410 legacy_daily_report_runtime_retired`
- `POST /api/dr-v2/reports/{report_id}/canonicalize` now returns `410 legacy_daily_report_runtime_retired`
- `POST /api/dr-v2/photos/*` mutation endpoints now return `410 legacy_daily_report_runtime_retired`
- `GET` compatibility reads remain intact for historical viewing/audit/PDF flows

## Verification notes
- Dependency proof: no active frontend route imports the removed V1 shell or flag hook
- Active runtime proof: `AppRoutes.jsx` imports `NewDailyReportV3` directly and contains no `DailyReportRouter` mount
- Remaining scope after this phase: regression certification and any read-only compatibility defects discovered by tests

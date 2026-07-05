# DR-ROI-001F · Backward Compatibility (Session A)

## V1 Guarantees (byte-untouched or lock-tested)

| Surface                                       | Status (Session A) | Verification                                        |
|-----------------------------------------------|--------------------|-----------------------------------------------------|
| `frontend/src/pages/NewDailyReport.jsx`       | byte-untouched     | `test_v1_daily_report_untouched_reference_lines`    |
| `backend/routes/daily_reports.py`             | byte-untouched     | grep · not in git diff                              |
| `backend/routes/daily_report_lifecycle.py`    | byte-untouched     | grep · not in git diff                              |
| `POST /api/daily-reports`                     | route intact       | route registration unchanged                        |
| `GET  /api/daily-reports`                     | route intact       | route registration unchanged                        |
| `GET  /api/daily-reports.csv`                 | route intact       | route registration unchanged                        |
| `GET  /api/exports/csv?kind=daily-reports`    | route intact       | route registration unchanged                        |
| CSV column order                              | unchanged          | `EXPORT_FIELDS["daily-reports"]` untouched          |
| Excavation / JHA / JHP gates                  | unchanged          | `DailyReportExcavationActivity` untouched           |
| Minimum-6-photo requirement                   | unchanged          | `PhotoUpload` + V1 submit path untouched            |
| Job Photos mirror                             | unchanged          | no photo pipeline touched                           |
| HR crew time linkage                          | unchanged          | `masci_crews[]` schema untouched                    |
| Payroll / time verification                   | unchanged          | no writes to time collections                       |
| Safety escalation workflow                    | unchanged          | no writes to safety collections                     |
| Auto-email dispatcher                         | unchanged          | no `_dispatch_auto_email` changes                   |
| `EMAIL_SAFETY_MODE=strict` (preview)          | unchanged          | env untouched                                       |

## V2 Guarantees (behavior preserved)
- Feature flag (`isDailyReportV2Enabled`) still gates the shell.
- DR-V2 backend endpoints (`/api/dr-v2/*`) untouched.
- `useDrV2Draft`, `useDrV2Ai`, `useDrV2Approvals` hooks untouched.
- `lib/drV2Api.js` unchanged.
- All existing DR-ROI-001C / D testids preserved.

## Dashboards
- `/pm/operational-intelligence` untouched.
- `/admin/ods-intelligence` untouched.
- `/executive/ods-intelligence` untouched.
- ODS emission pipeline untouched.
- Photo Intelligence emission untouched.

## Rollback Recipe
```
git checkout HEAD~ -- \
  frontend/src/pages/daily-report-v2/_ui.jsx \
  frontend/src/pages/daily-report-v2/DailyReportV2.jsx \
  frontend/src/pages/daily-report-v2/sections/*.jsx \
  frontend/src/pages/daily-report-v2/panels/*.jsx
git checkout HEAD~ -- frontend/src/pages/daily-report-v2/panels/PmIntelligencePanel.jsx  # restores deleted file
rm backend/tests/test_dr_roi_001f_platform_consistency.py
rm /app/memory/DR_ROI_001F_*.md
```
Result: state identical to the DR-ROI-001F kick-off snapshot.

## What Session B Must NOT Break
- Any DR-ROI-001F Session A lock test.
- Any DR-ROI-001C / D / E lock tests.
- V1 daily-reports / photos / HR / safety pipelines.
- The Preview / Download PDF buttons — Session B must simply enable them.

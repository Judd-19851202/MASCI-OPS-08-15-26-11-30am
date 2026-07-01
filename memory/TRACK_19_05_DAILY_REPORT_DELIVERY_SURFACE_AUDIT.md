# Track 19.05 · Daily Report PM / Admin / Safety Delivery Surface Audit

## PM surfaces

| Surface | Route | Purpose |
| --- | --- | --- |
| PM list | `/pm/daily` (`DailyReportsDashboard`) | Filterable list of DRs scoped to the PM's assigned projects |
| PM detail | `/pm/daily/:id` (`ViewDailyReport`) | Full DR view; signed-URL download for photos + attachments |
| PM Command Center | `PmProjectFirstHome.jsx` | Recent DR chip, exposure signals |
| PmExposureTile | Aggregates advisory RFI/schedule signals derived from `constraints[]` |

## Admin surfaces

| Surface | Route | Purpose |
| --- | --- | --- |
| Admin list | `/admin/daily` | Same dashboard component, admin scope (all projects) |
| Admin detail | `/admin/daily/:id` | Full DR view + audit footer + email resend + lifecycle panel |
| Admin intel | `/api/admin/daily-report-health` (`dr_admin_intel.py`) | Health/exposure aggregate |
| Compliance export | `ComplianceExportPanel.jsx` | CSV + PDF bulk export |

## Safety surfaces

Safety inbox receives auto-emailed reports. Safety portal reads DR via same admin routes (safety role is scoped in `require_admin_pm_or_hr_read`).

## HR surface

`/app/frontend/src/pages/HrDailyReports.jsx` — HR-scoped read using `require_admin_pm_or_hr_read`.

## Photos & attachments visibility

| Location | Photo display | Attachment display |
| --- | --- | --- |
| PM detail | Gallery grid, signed URLs | Grouped by category (Photos / PDFs / Spreadsheets) |
| Admin detail | Gallery grid, signed URLs | Same grouping |
| Rendered PDF | Photos embedded inline | Attachments listed with signed URL |

## Search / filter / export

* List dashboards support filters by `project_number`, `report_date`, `prepared_by`, `superintendent`.
* Export routes: `/api/daily-reports.csv` (CSV), `/api/reports/daily-report/pdf/{id}` (PDF).
* Job Photos library — photos mirrored via `index_record_photos(db, "daily_report", doc)` — global photo search.

## Correction / reopen / kick-back

DELETE is 410-frozen (historical immutability). Kick-back / reopen workflow does not exist on DRs — corrections happen via a new DR posted the following day with narrative referencing the prior report.

## Redesign risk

* HIGH — PM list + detail is the operational anchor. Field breakages here are highly visible.
* HIGH — Compliance CSV export depends on stable field names.
* MEDIUM — Job Photos indexer key names.

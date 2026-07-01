# Track 19.05 · Daily Report Route Inventory

Complete map of every route touching Daily Reports. Audit only — no route changes.

## Frontend routes (`/app/frontend/src/App.js`)

| Route | Component | Purpose | Auth |
| --- | --- | --- | --- |
| `/daily/new` | `NewDailyReport` (`/app/frontend/src/pages/NewDailyReport.jsx`) | Field foreman creates a new Daily Report | Public (any actor) |
| `/daily/submit` | `NewDailyReport publicMode` | Public FSI submit flow (kiosk / QR) | Public |
| `/reports/daily/new` → `/daily/new` | redirect | Legacy path | — |
| `/daily` → `/admin/daily` | redirect | Legacy | — |
| `/daily/:id` → `/admin/daily/:id` | redirect | Legacy | — |
| `/admin/daily` | `DailyReportsDashboard` | Admin list + search + filter | Admin |
| `/admin/daily/:id` | `ViewDailyReport` | Admin detail view of a submitted DR | Admin |
| `/admin/daily-reports` → `/admin/daily` | redirect | Legacy | — |
| `/pm/daily` | `DailyReportsDashboard` (same component, PM scope) | PM list | PM |
| `/pm/daily/:id` | `ViewDailyReport` | PM detail | PM |

## Backend routes (`/app/backend/routes/daily_reports.py` + `server.py`)

| Method | Path | Owner | Purpose |
| --- | --- | --- | --- |
| POST | `/api/daily-reports` | `create_daily_report` | Submit a new DR; auto-emails; snapshots team; sanitises photos; opens trust-spine lifecycle |
| GET | `/api/daily-reports` | `list_daily_reports` | List summary rows for dashboards |
| GET | `/api/daily-reports.csv` | `daily_reports_csv` | CSV export |
| GET | `/api/daily-reports/next-number` | `next_daily_report_number` | Return next `DR-YYYYMMDD-NNN` |
| GET | `/api/daily-reports/exposure-signals` | exposure API | RFI / schedule advisory signals aggregate |
| GET | `/api/daily-reports/{report_id}` | `get_daily_report` | Fetch a single submitted DR |
| GET | `/api/daily-reports/{report_id}/audit-footer` | audit footer | SHA256 + doc_id + rendered_at |
| DELETE | `/api/daily-reports/{report_id}` | `delete_daily_report` | Returns 410 (frozen — historical immutability) |
| POST | `/api/daily-reports/attachments/upload` | `daily_report_attachment_upload` (server.py) | Track 19.04 · PDF/XLSX/XLS/CSV attachment upload |
| GET | `/api/admin/daily-report-health` | `dr_admin_intel.py` | Track 15.62 admin intel |
| GET | `/api/jobs/{project_number}/recent-context` | `server.py::jobs_recent_context` | Track 19.04 v19.04 Smart Prefill baseline |

## PDF / export

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/reports/{kind}/pdf/{id}` (kind=daily-report) | WeasyPrint-rendered PDF, media_type `application/pdf` |
| GET | `/api/daily-reports.csv` | CSV of DR summaries |

## Email routing

Auto-email is triggered inside `create_daily_report()` via `schedule_auto_email("daily-report", doc)` and delivered through the universal `_email_router` + `TRUST_SPINE` correlation.

## Redesign risk

* `/daily/new` — HIGH. Owns the entire section tree; any redesign lives here.
* `/api/daily-reports` POST — HIGH. Payload shape is a fixed contract; PDFs, PM, email, and Job Photos indexer all read from the persisted document.
* `/api/daily-reports/next-number` — MEDIUM. Any change to `DR-YYYYMMDD-NNN` prefix will collide with existing indexes.
* `/api/daily-reports/{id}/audit-footer` — MEDIUM. SHA256 depends on the sanitized document shape.
* Attachment upload — LOW. Isolated v19.04 contract.

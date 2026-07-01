# Track 19.05 · Daily Report Backend Map

Complete backend surface. Audit only.

## File-by-file

### `/app/backend/routes/daily_reports.py` (665 lines)

Owner of the primary DR router. Exports:
* `DailyReportCreate`, `DailyReport`, `DailyReportSummary` (Pydantic)
* `ProductionRow`, `ConstraintRow` (Wave-1A structured production/constraints)
* `register_daily_reports_routes(api_router, db, require_admin, rate_limit_public_post, schedule_auto_email, require_admin_pm_or_hr_read)`
* Helpers: `_derive_advisory_flags`, `_audit_envelope`, `_compute_audit_envelope_sha256`, `_sanitize_inline_photos`

Endpoints registered:

| Method + Path | Function | Side effects |
| --- | --- | --- |
| POST `/daily-reports` | `create_daily_report` | Excavation-linkage gate; `resolve_prepared_by_identity`; advisory flags; `ensure_doc_id`; `_sanitize_inline_photos` (base64 → R2 refs); audit hash; `snapshot_team` (job-ownership team_snapshot embed); insert `db.daily_reports`; two-way trench excavation stamp; `index_record_photos` → job_photos library; `emit_record_created` → trust-spine; `schedule_auto_email("daily-report", doc)`; `resolve_identity` → field submitter binding; idempotency-keyed |
| GET `/daily-reports` | `list_daily_reports` | Reads summary projection |
| GET `/daily-reports.csv` | CSV serializer | Reads and streams |
| GET `/daily-reports/next-number` | `next_daily_report_number` | Counts docs matching `DR-YYYYMMDD-*` prefix |
| GET `/daily-reports/exposure-signals` | RFI/schedule advisory aggregator | Read-only |
| GET `/daily-reports/{id}` | `get_daily_report` | Full doc, protected by `require_admin_pm_or_hr_read` |
| GET `/daily-reports/{id}/audit-footer` | audit-footer | Returns SHA256 + doc_id + rendered_at |
| DELETE `/daily-reports/{id}` | Frozen — returns 410 | Historical immutability |

### `/app/backend/server.py`

* Line 2630-2639 — `register_daily_reports_routes` invocation.
* Line ~3308 — `GET /api/jobs/{project_number}/recent-context` (Track 19.04 v19.04 Smart Prefill).
* Line ~2658 — `POST /api/daily-reports/attachments/upload` (Track 19.04 unified attachments).
* Line ~5594 — Universal PDF renderer `/api/reports/{kind}/pdf/{id}` (WeasyPrint) serves Daily Report PDF.

### `/app/backend/routes/dr_admin_intel.py`

* `GET /api/admin/daily-report-health` — Track 15.62 admin intel aggregator (project-scoped scoring, exposure signals).

### `/app/backend/routes/daily_report_lifecycle.py`

* Trust-spine lifecycle events for the DR workflow (open → email → deliver → close).

### `/app/backend/photo_storage.py`

* `upload_data_url()` — base64 photo → R2 `photos/YYYY/MM/<source>/<uuid>.<ext>` used by `_sanitize_inline_photos()`.
* `upload_document_data_url()` — Track 19.04 · PDF/XLSX/XLS/CSV upload → R2 `documents/YYYY/MM/<source>/<uuid>.<ext>`.
* `presigned_get_url_for_key()` — 7 day signed URLs for email + admin download.

### `/app/backend/routes/job_photos.py`

* `index_record_photos(db, "daily_report", doc)` — mirrors photos into the Job Photos library.

### `/app/backend/lib/`

* `idempotency.py` — `with_idempotency(key, fn)` protects submit against duplicates.
* `trust_spine.py` — `emit_record_created`, `emit_record_delivered`, correlation IDs.
* `team_routing.py` — `snapshot_team(db, project_number)` embeds active project roster on submit.
* `field_submitter_identity.py` — Tier-1 → Tier-5 field submitter identity resolver.
* `prepared_by_resolver.py` — resolves portal-token → structured directory identity.
* `doc_ids.py` — `ensure_doc_id(db, doc, "DR", when=…)` stamps DR-YYYY-NNNNN.

## Collections read/written

| Collection | Purpose |
| --- | --- |
| `daily_reports` (write, read) | Primary submissions |
| `job_photos` (write) | Photo library index |
| `trench_excavations` (write) | Two-way excavation linkage on submit |
| `field_submitter_identities` (write) | FSI binding |
| `trust_spine_events` (write) | Lifecycle timeline |
| `jobs_master` (read) | Project + superintendent + PM lookup |
| `email_queue` / `email_delivery` (write) | Auto-email dispatch |

## Redesign risk

* HIGH — `create_daily_report`: any field addition/removal in the body must be additive on the Pydantic model; the audit hash and PDF renderer both key off the sanitized doc shape.
* HIGH — `_sanitize_inline_photos`: walks `photos[]`, `subcontractors[].photos[]`, `materials[].ticket_photos[]`. Redesign must not move these arrays without updating this walker.
* MEDIUM — `next-number` format `DR-YYYYMMDD-NNN`. Changing the format will collide with existing prefix index.
* MEDIUM — trust-spine correlation IDs. Any renaming of `workflow="daily-report"` breaks lifecycle joins.

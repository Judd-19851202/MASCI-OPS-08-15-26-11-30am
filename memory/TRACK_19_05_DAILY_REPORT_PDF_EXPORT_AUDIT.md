# Track 19.05 · Daily Report PDF / Export Audit

## PDF generation

* **Route**: `GET /api/reports/{kind}/pdf/{id}` where `kind = "daily-report"`.
* **Engine**: WeasyPrint (`server.py:5594` area).
* **Media type**: `application/pdf`.
* **Template**: universal report template with DR-specific section blocks.
* **Fields rendered**: every field in `TRACK_19_05_DAILY_REPORT_DATA_MODEL_MAP.md` (except signatures which render as inline images).
* **Photos**: `photo://` refs resolved to bytes via `read_photo_bytes()`; embedded inline.
* **Attachments (Track 19.04)**: listed as filenames + signed URLs in a "Documents" appendix.
* **Signature**: `prepared_by_signature` rendered inline; superintendent signature has been retired (DR-FIX-3 R13) but the field remains in the model for legacy renders.
* **Branding**: MASCI header/footer, correlation id, audit footer (SHA256 + doc_id + rendered_at).
* **Filename**: `MASCI_DailyReport_{doc_id}_{report_date}.pdf`.

## CSV export

* **Route**: `GET /api/daily-reports.csv`.
* **Fields**: `report_number, report_date, project_number, project_name, prepared_by, superintendent, doc_id, created_at` (bounded projection).
* **Purpose**: compliance + PM analytics.

## Storage

* PDFs are rendered on-demand — NOT pre-generated and stored. Any storage is transient (server memory) or emailed as attachment.
* Rendered PDFs can be re-requested by any authorized viewer (idempotent, deterministic — same doc → same bytes barring signed-URL rotation for embedded photos).

## Where PDF is displayed

* PM/admin detail view has "Download PDF" button.
* Auto-email delivery attaches the PDF.
* Compliance export bundle includes PDF per report.

## Redesign risk

* HIGH — WeasyPrint template reads specific field names. Renaming schema keys breaks the render.
* HIGH — photos array traversal in the render must match `_sanitize_inline_photos` walk.
* MEDIUM — CSV projection field list. Compliance workflows may parse fixed column positions.
* LOW — filename format.

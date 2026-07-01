# Track 19.04 · Daily Report Attachment Audit

## Existing PhotoUpload Architecture (Track 19.04 baseline)

| Concern | Implementation | Location |
| --- | --- | --- |
| Frontend picker | `PhotoUpload.jsx` — gallery/camera picker, iOS action-sheet compatible, on-device 1280px @ q=0.78 JPEG compression, live progress bar | `/app/frontend/src/components/PhotoUpload.jsx` |
| Client payload | Base64 data URLs embedded in the report body (`photos[]`) | (form state) |
| Server ingestion | `_sanitize_inline_photos()` walks `photos[]`, `subcontractors[].photos[]`, `materials[].ticket_photos[]` and pushes each data URL to R2 on submit | `/app/backend/routes/daily_reports.py::_sanitize_inline_photos` |
| Storage | Cloudflare R2 via boto3 (S3-compatible), key layout `photos/YYYY/MM/<source>/<uuid>.<ext>` | `/app/backend/photo_storage.py::upload_photo_bytes / upload_data_url` |
| Reference format | `photo://photos/YYYY/MM/<source>/<uuid>.<ext>` (opaque, resolved via `resolvePhotoSrc`) | `/app/frontend/src/lib/photoSrc.js`, `photo_storage.py::_build_ref` |
| Signed URLs | `presigned_get_url_for_key(key, ttl_seconds=7*24*3600)` for email / admin download | `photo_storage.py::presigned_get_url_for_key` |
| Retention | Same as R2 bucket lifecycle (backup task retains all objects until operator prunes) | R2 bucket policy |
| Permissions | Presigned URLs are ephemeral, short-TTL; direct R2 access requires bucket credentials only held by the backend | R2 config |
| Backup | Daily R2 backup task (`_start_job_photos_indexer` + backup verification) | server.py |

## What was missing before Track 19.04

* No client component for non-image files.
* No server endpoint accepting non-image attachments.
* No storage prefix for documents (photos-only bucket layout).
* No attachment metadata envelope (photos are stored as raw `photo://` refs; the frontend does not know filename, size, mime, category).
* No PDF/XLSX allow-list, no dangerous-extension blocklist.

## Track 19.04 Extension (delivered)

**Contract preservation**: everything reuses the SAME R2 bucket, SAME boto3 client, SAME signed-URL helper, SAME backup task, SAME permissions model. **No parallel storage.** Photos continue to work exactly as before.

### New surfaces

| Surface | Location | Contract |
| --- | --- | --- |
| Frontend picker | `AttachmentUpload.jsx` — file picker with `accept` filter, per-file upload progress, grouped display (Photos / PDFs / Spreadsheets) | `/app/frontend/src/components/AttachmentUpload.jsx` |
| Server ingestion | `POST /api/daily-reports/attachments/upload` — accepts a single data URL, returns metadata envelope | `server.py::daily_report_attachment_upload` |
| Storage helper | `photo_storage.upload_document_data_url()` — validates MIME + extension + size + filename, uploads to R2 under `documents/YYYY/MM/<source>/<uuid>.<ext>` | `/app/backend/photo_storage.py` |
| Metadata envelope | `{ attachment_ref, mime_type, extension, category, filename, file_size, uploaded_at, contract_version:"19.04" }` | frontend + backend |
| Daily Report model | `attachments: List[Dict[str, Any]]` on `DailyReportCreate` — parallel to `photos[]` | `/app/backend/routes/daily_reports.py` |
| Category taxonomy | `Photo` (existing `photos[]`), `PDF`, `Spreadsheet`, `Other` — server-supplied | `photo_storage.py::upload_document_data_url` |

### Allow-list

* PDF (`application/pdf`)
* XLSX (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`)
* XLS (`application/vnd.ms-excel`)
* CSV (`text/csv`, `application/csv`)

### Denylist (dangerous)

`exe, bat, cmd, com, cpl, dll, jar, js, jse, msi, ps1, psm1, sh, vbe, vbs, wsf, wsh, scr, app, action, workflow, hta`

### Size cap

25 MiB per attachment (matches provider email limit — safe headroom for common CEI reports + trucking ticket PDFs).

### Filename handling

`_safe_filename()`:

* strip directory separators (`\`, `/`)
* drop non-printable ASCII
* neutralise `.htaccess` / `..` traversal
* cap length at 240 chars, preserving extension

### Permissions

* Upload is public (Daily Reports themselves are a public submit surface for field foremen).
* The returned `attachment_ref` is only meaningful once linked to a specific Daily Report body, so an orphaned upload has no report to leak into.
* Signed URLs for download go through the same `presigned_get_url_for_key` helper as photos — TTL 7 days, scoped to the specific object.

## Regression guarantees

* Photos continue to use `PhotoUpload` and `photos[]` — untouched.
* Photo pipeline (`_sanitize_inline_photos`) still runs on submit — untouched.
* PDF embedding of photos in the emailed Daily Report continues to work — untouched.
* Attachments are a new, additive envelope that lives alongside photos, not in place of them.

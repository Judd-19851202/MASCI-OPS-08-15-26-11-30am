# Track 19.05 · Daily Report Attachment / Photo / File Audit

Reconfirms Track 19.04 unified attachment pipeline for redesign-planning purposes.

## Photos (`photos[]`)

* **Frontend picker**: `PhotoUpload.jsx` — iOS action-sheet compatible, on-device JPEG compress (1280 px @ 0.78).
* **Client payload**: base64 data URLs embedded in `data.photos[]`.
* **Server ingestion**: `_sanitize_inline_photos(doc)` walks top-level `photos[]`, `subcontractors[].photos[]`, `materials[].ticket_photos[]` and pushes each data URL to R2.
* **Storage layout**: `photos/YYYY/MM/<source>/<uuid>.<ext>`.
* **Reference format**: `photo://photos/YYYY/MM/<source>/<uuid>.<ext>` — opaque, resolved via `resolvePhotoSrc` on the frontend and `presigned_get_url_for_key` on the backend.
* **Signed URLs**: TTL 7 days.
* **Minimum**: 6 photos (submit gate).
* **Captions**: parallel `photo_captions[]`.

## Documents (`attachments[]` — Track 19.04)

Supported types: PDF, XLSX, XLS, CSV.

* **Frontend picker**: `AttachmentUpload.jsx`. Accepts `.pdf, .xls, .xlsx, .csv`.
* **Upload endpoint**: `POST /api/daily-reports/attachments/upload` (public).
* **Server helper**: `photo_storage.upload_document_data_url()`.
* **Storage layout**: `documents/YYYY/MM/<source>/<uuid>.<ext>` — same R2 bucket, separate prefix.
* **Metadata envelope**:
  ```
  { attachment_ref, mime_type, extension, category, filename, file_size, uploaded_at, contract_version:"19.04" }
  ```
* **Category taxonomy**: `PDF`, `Spreadsheet`, `Other` (server-supplied).
* **MIME allow-list**: `application/pdf`, `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `text/csv`, `application/csv`.
* **Dangerous extension blocklist**: `exe, bat, cmd, com, cpl, dll, jar, js, jse, msi, ps1, psm1, sh, vbe, vbs, wsf, wsh, scr, app, action, workflow, hta`.
* **Filename sanitisation**: `_safe_filename()` strips separators, control chars, dot-only prefixes, caps at 240 chars.
* **Size cap**: 25 MiB per file.

## Report linkage

Attachments become part of a report only when the metadata blob is submitted inside the report's `attachments[]`. Orphan uploads (upload without submit) are never linked to any report.

## Detail view display

Grouped by `category` in `<ViewDailyReport>`, `<DailyReportsDashboard>` (list), admin/PM detail. Same envelope, same grouping logic.

## Email routing

See `TRACK_19_04_DAILY_REPORT_EMAIL_ATTACHMENT_ROUTING.md`. Signed-URL body links + selective multipart attach ≤ 20 MiB total. Multipart attach step defers to email provider confirmation (Track 19.04 documented deferral).

## Deletion / remove behavior

* Frontend `Remove attachment` splices `attachments[]` on the client BEFORE submit.
* Once submitted, deletion is not user-exposed (immutability doctrine matches historical DR rules).
* R2 objects are never orphan-deleted synchronously; a background sweep of un-referenced `documents/` keys is a future item.

## Security controls (recap from 19.04 security review)

* MIME + extension double allow/deny.
* Filename sanitisation.
* Size cap.
* UUID storage path — unenumerable.
* Signed URL TTL 7 days.
* R2 credentials server-side only.
* Cross-report leakage impossible (attachment_ref lives inside a specific report's persisted array).

## Redesign risk

* HIGH — moving attachments out of `attachments[]` array on the DR breaks PM detail + admin display + audit hash.
* MEDIUM — changing category taxonomy breaks the group headers.
* LOW — expanding the allow-list to include Word/PowerPoint is additive; existing behavior would not regress.

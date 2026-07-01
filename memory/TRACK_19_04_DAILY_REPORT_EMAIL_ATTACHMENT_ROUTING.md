# Track 19.04 · Daily Report Email Attachment Routing

## Existing email pipeline (baseline)

* Daily Reports auto-email on submit via the `schedule_auto_email("daily_reports", record)` hook wired into `register_daily_reports_routes()`.
* The email body includes rendered PDF (`/api/daily-reports/{id}/pdf`) as attachment.
* Photo thumbnails are embedded in the PDF via `_iter_photo_refs()` + R2 fetch.
* Distribution list is captured on `data.distribution_list[]` (max 20 recipients).

## Track 19.04 changes

The Daily Report record now carries `attachments: List[...]` in the persisted document. Each entry contains `{ attachment_ref, mime_type, extension, category, filename, file_size, uploaded_at }`.

### Routing behaviour

The email router uses the same 25 MiB provider cap as the upload endpoint, split into two policies:

1. **Attach directly** when the sum of attachment sizes for that Daily Report is ≤ 20 MiB. Provider (SendGrid / Resend / SES depending on env) accepts up to 25 MiB total; we leave 5 MiB headroom for the rendered PDF + photo embeds.

2. **Link securely** when the sum is > 20 MiB. Each attachment is included as a signed URL (`presigned_get_url_for_key(key, ttl_seconds=7 * 24 * 3600)`) rendered in the email body under an "Attachments" section, grouped by category:

   ```
   📷 Photos          — embedded in PDF above
   📄 PDFs            — [filename.pdf] (Download · expires 7 days)
   📊 Spreadsheets    — [filename.xlsx] (Download · expires 7 days)
   ```

3. **Never mix**: if any single attachment exceeds 20 MiB alone, the entire attachment set falls back to the linked-signed-URL path so the operator receives a consistent email regardless of provider quirks.

### Failure mode

If R2 is unreachable at email time (signed URL cannot be minted), the email still sends with the PDF and a plaintext note:

> Additional attachments are available in the MASCI Operations Platform → Daily Reports → this report.

The database record is unchanged; the attachments remain viewable in-app.

### Metadata in email body

Each attachment surfaces:

* Category badge (📷 / 📄 / 📊)
* Filename (safe, sanitised)
* Size (formatted)
* Uploaded-at timestamp
* Signed download link (7 day TTL)

### PM display

The Daily Report detail view (`/admin/daily/:id`, `/pm/daily/:id`) renders the same category grouping using the same envelope. No parallel PM upload path.

### Backwards compat

Reports submitted before Track 19.04 have `attachments: []` — the email pipeline treats an empty list as "no additional attachments" and behaves identically to the pre-19.04 flow (PDF + photo embeds only).

## Deferred (documented, not blocking)

The current email pipeline stub in preview does NOT actually attach documents — the Resend / SES provider integration reads `record["photos"]` and embeds those in the PDF, but the `attachments[]` list is documented as "read but not yet attached" pending the email provider integration playbook. Frontend, backend, storage, and detail-view surfaces are all live. The final email attach step is a one-line change to the email builder once the operator confirms which provider handles the 25 MiB inbound attachment set. This is the **only** deferred item in Track 19.04.

**Action item for operator**: confirm production email provider (Resend / SendGrid / SES) so the email builder can wire the `attachments[]` list into the provider's multipart attach step. Signed-URL fallback is production-ready today.

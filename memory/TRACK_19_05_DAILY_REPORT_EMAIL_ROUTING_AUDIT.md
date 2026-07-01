# Track 19.05 · Daily Report Email Routing Audit

Source: `create_daily_report()` → `schedule_auto_email("daily-report", doc)`; universal email router.

## Recipient composition (delivery path)

1. **PM assignee** — resolved from `jobs_master.pm_email` / `jobs_master.pm_id` for the report's `project_number`.
2. **Super Admin** — `SUPER_ADMIN_EMAIL` env (currently `jaymn.judd@mascigc.com`).
3. **Safety inbox** — `safety@mascigc.com` (env-configurable).
4. **Submitter** — if `submitter_email_at_submit` was captured via FSI (Tier-1 identity).
5. **Distribution list** — up to 20 additional emails from `data.distribution_list[]`.

Only fires when env `AUTO_EMAIL_REPORTS=true`.

## Message

* **Subject**: `Daily Report {doc_id} — {project_name} — {report_date}` (universal template).
* **Body**: rendered summary — project header, key sections, photos count, attachments summary, and correlation link to the platform detail view.
* **Attached**: rendered PDF (`/api/reports/daily-report/pdf/{id}`).
* **Photos**: embedded in the PDF (inline, resolved from R2 presigned URLs at render time).
* **Attachments (Track 19.04)**: currently linked via signed URLs in the body (deferred multipart step — see `TRACK_19_04_DAILY_REPORT_EMAIL_ATTACHMENT_ROUTING.md`).

## Failure / retry behavior

* `schedule_auto_email` writes to `email_queue`. A queue worker retries with exponential backoff.
* Trust-spine emits `record_created` → `email_scheduled` → `email_delivered` events.
* Manual re-send: `EmailReportDialog.jsx` on admin/PM detail page → `POST /api/reports/{kind}/{id}/resend-email`.

## Provider limits + fallback

Provider cap ~25 MiB total including PDF + embeds. Fallback (Track 19.04): if `sum(attachments.file_size) > 20 MiB` OR any single file exceeds 20 MiB → link-only mode with 7-day signed URLs.

## Redesign risk

* HIGH — recipient composition depends on `project_number` → `jobs_master` join. Any redesign that changes how project number is captured must re-verify PM routing.
* MEDIUM — Trust-spine correlation IDs. Any renaming of `workflow="daily-report"` breaks lifecycle joins.
* LOW — subject line template.

# Track 19.06 · Daily Report Schema Protection Report

## Assertion

**No persisted schema key was renamed or removed in Track 19.06.**

The Track 19.05 audit locked the DR schema surface. The 19.06 redesign is UI-only.

## Schema key roll call (source: `/app/backend/routes/daily_reports.py::DailyReportCreate`)

Verified present after Track 19.06:

* `id`, `doc_id`, `report_number`, `report_date`, `created_at`
* `project_name`, `project_number`, `location`
* `prepared_by`, `superintendent`
* `weather_summary`, `weather_snapshots`, `weather_impact`, `weather_impact_notes`
* `schedule_delays`, `schedule_delays_notes`
* `safety_incidents_today`, `injuries_reported`, `incident_notes`
* `safety_notified`, `safety_contact_person`, `safety_contact_time`
* `incident_report_filled`, `incident_report_time`
* `general_notes`
* `masci_crews[]`, `subcontractors[]`, `visitors[]`, `equipment[]`
* `materials[]`, `outbound_materials[]`, `activities[]`
* `production[]`, `constraints[]`
* `narrative_sections{}`
* `photos[]`, `photo_captions[]`, `attachments[]`
* `distribution_list[]`
* `prepared_by_signature`, `superintendent_signature`
* `audit_envelope_sha256`, `prepared_by_identity`, `prepared_by_bound`
* `team_snapshot`, `linked_excavation_ids`, `excavation_activity_today`
* `submitter_employee_id`, `submitter_email_at_submit`, `submitter_consent_at`

Enforced by `test_no_schema_keys_removed_or_renamed` in the 19.06 lock test.

## Route protection

* `POST /api/daily-reports` — unchanged.
* `GET /api/daily-reports`, `GET /api/daily-reports.csv`, `GET /api/daily-reports/next-number`, `GET /api/daily-reports/exposure-signals`, `GET /api/daily-reports/{id}`, `GET /api/daily-reports/{id}/audit-footer`, `DELETE /api/daily-reports/{id}` — unchanged.
* `POST /api/daily-reports/attachments/upload` (Track 19.04) — unchanged.
* `GET /api/jobs/{pn}/recent-context` (Track 19.04 v19.04 contract) — unchanged.
* `GET /api/reports/daily-report/pdf/{id}` — unchanged.
* `GET /api/admin/daily-report-health` — unchanged.

## Downstream surface protection

* PDF renderer (WeasyPrint) — reads the persisted document; no template touch.
* Auto-email routing — `schedule_auto_email("daily-report", doc)` unchanged.
* PM / Admin / Safety / HR delivery — same read scopes, same collection.
* Job Photos indexer — `index_record_photos(db, "daily_report", doc)` unchanged.
* Trust-spine lifecycle — `emit_record_created` with `workflow="daily-report"` unchanged.
* CSV export — same field projection.

## Contract-version fingerprints

* Track 19.03 HR roster `contract_version = "19.03"` — still returned.
* Track 19.04 recent-context `contract_version = "19.04"` — still returned.
* Track 19.04 attachment upload envelope `contract_version = "19.04"` — still returned.

## Verdict

Zero schema drift. The DR API contract is unchanged. Historical DRs continue to render, export, and email identically. New DRs submitted through the redesigned UI produce documents byte-identical to those the pre-redesign UI would have produced for the same inputs.

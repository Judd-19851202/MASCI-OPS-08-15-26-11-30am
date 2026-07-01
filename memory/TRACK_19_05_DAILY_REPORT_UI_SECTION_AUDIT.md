# Track 19.05 · Daily Report UI Section Audit

Section-by-section walk of `/app/frontend/src/pages/NewDailyReport.jsx`. Source: `<Section number="..." title=...>` blocks + testids.

## Section 01 · Report Information (`NewDailyReport.jsx:1241`)

Fields:
* Project name (`input-project-name`) — REQ
* Project number (`input-project-number`) — REQ-ish
* Location (`input-location`) + Use GPS button (`use-gps-btn`) — REQ
* Report date (`input-report-date`) — REQ, drives `/next-number`
* Report number (`input-report-number`) — auto-filled, editable
* Prepared By — REQ, auto-filled from FL portal token
* Superintendent — auto-filled from jobs_master or recent DR

## Section 02 · Weather (`NewDailyReport.jsx:1377`)

Weather refresh button (`refresh-weather-btn`) → `/api/weather-snapshots`. Snapshot chips (`weather-snap-{i}`). Weather impact Yes/No + notes.

## Section 03 · General Information + Safety Triggers (`NewDailyReport.jsx:1437`)

Safety triggers (all Yes/No):
* `safety_incidents_today`
* `injuries_reported`
* Escalation block (`safety-escalation-block`)
* `safety-not-notified-warning`
* `input-safety-contact-person`, `input-safety-contact-time`
* `incident-report-required-warning`, `open-incident-form-link`
* `input-incident-report-time`
* `input-incident-notes`
* `input-general-notes`

## Section 04 · MASCI Crews on Site (`NewDailyReport.jsx:1696`)

* Crew identity linkage tip card
* Per-crew row: `crew-row-{i}` with `crew-linked-{i}` / `crew-unlinked-{i}` badge
* Fields: employee combo → name; `crew-trade-{i}`, `crew-hours-{i}` (auto-computed), `crew-start-{i}`, `crew-lunch-{i}`, `crew-stop-{i}`, `crew-work-{i}`
* `crew-remove-{i}` button
* "Add Crew Member" button (bottom of section)

## Section 05 · Subcontractors on Site (`NewDailyReport.jsx:1941`)

Row: `{company, trade, foreman, count, hours, work_performed, attachment_note, photos[], ticket_photos[]}`. SupplierCombo drives company.

## Section 06 · Site Visitors (`NewDailyReport.jsx:1992`)

Row: `{name, company, purpose, in_time, out_time}`.

## Section 07 · Equipment Log (`NewDailyReport.jsx:2026`)

Row: `{description, hours_used, time_delivered, time_removed, notes}`. EquipmentCombo drives description.

## Section 08 · Material Deliveries (Inbound) (`NewDailyReport.jsx:2073`)

Row: `{material, quantity, unit, supplier, ticket_number, notes, ticket_photos[]}`.

## Section 09 · Outbound Materials / Hauled Off (`NewDailyReport.jsx:2113`)

Row: `{material, quantity, unit, hauler, destination, ticket_or_manifest, notes}` (MM-ENTRY-002 K-MM-1).

## Section 10 · Activity / Production Log (`NewDailyReport.jsx:2181`)

Three sub-sections:
* Activities (legacy free text)
* Production Quantities (`ProductionRow` structured)
* Delays / Extra Work (`ConstraintRow` structured) — testid `delay-*`

## Section 10.5 (visual) · Photos + Attachments

* PhotoUpload (photos-status pill, min 6 photos gate)
* AttachmentUpload (Track 19.04) `daily-attachments`, `daily-attachments-picker-input`, group testids `daily-attachments-group-{category}`, `daily-attachments-item-{idx}`, `daily-attachments-remove-{idx}`

## Section 11 · Sign-Off (`NewDailyReport.jsx:2448`)

* Distribution list (up to 20 emails)
* Prepared By signature pad (`prepared-by-sig`)
* Superintendent signature removed per DR-FIX-3 R13

## Global affordances

* `submit-top-btn` — top-of-page submit
* Submit gate footer (`NEED N MORE PHOTOS TO SUBMIT` / `SUBMIT DAILY REPORT`)
* `daily-report-draft-pill` — DraftStatusPill
* `daily-report-draft-restore-prompt` — DraftRestorePrompt
* `daily-report-draft-recovery` — 24 h archive recovery
* `daily-report-crew-setup-prompt` — device-local crew memory (Phase 31.1)
* `daily-report-smart-prefill-offer` / `-apply` / `-dismiss` — Track 19.04 explicit offer chip
* `daily-report-setup-load-trace` — post-restore reassurance line

## Redesign notes

* Sections 04-09 all share the same `<InlineRowsSection>` pattern with `{testIdBase}-add`, `{testIdBase}-row-{i}`, `{testIdBase}-remove-{i}` — a redesign must preserve these testid conventions or update every downstream test.
* Every Yes/No trigger in Section 03 reveals conditional detail fields — see `TRACK_19_05_DAILY_REPORT_TRIGGER_AUDIT.md`.
* All sections are CONDITIONALLY DISPLAYED via `CollapseCard` (iter383 Phase 5C.1) so the field UX stays fast — collapse state does NOT alter the persisted doc.

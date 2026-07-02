# TRACK 19.25 · Historical Records Intake Discoverability + Intake Session Upgrade

## Scope
Additive-only. Made the existing Historical Records Intake surfaces discoverable across HR / Safety / Asset Administrator (Shop) portals, added human-facing guidance to the intake landing page, and introduced Intake Session metadata (source_name / source_type / source_location) that is inherited from batch → record → Employee 360°.

## Zero drift confirmed
- No new backend routes.
- No new pages.
- No new components.
- No new dependencies.
- No mutation of `db.employees` or `db.incident_cases`.
- No OCR / AI / fuzzy libraries imported.
- Audit ledger still append-only.
- Session fields are additive on the existing `CreateBatchBody` and on the `employee_records` documents produced by `batch_upload`.

## Files changed
| File | Change type |
|---|---|
| `/app/frontend/src/components/hr/sidebar/HrSideNavV2.jsx` | Added 1 sidebar item (Bulk Historical Intake) |
| `/app/frontend/src/components/safety/sidebar/SafetySideNavV2.jsx` | Added 3 sidebar items (Safety Intake · Queue · Bulk) |
| `/app/frontend/src/pages/ShopHubV2.jsx` | Added Asset Administrator · Historical Records section with 3 HubCards |
| `/app/frontend/src/pages/HistoricalRecordsIntake.jsx` | Added "What can I upload?" chip strip + 3-step "How it works" guide |
| `/app/frontend/src/pages/HistoricalRecordsBatches.jsx` | Extended create form with source_name / source_type / source_location |
| `/app/frontend/src/pages/HistoricalRecordsBatchDetail.jsx` | Session provenance strip on batch header |
| `/app/frontend/src/pages/EmployeeProfile.jsx` | Doc card shows intake source line |
| `/app/backend/routes/employee_records.py` | Added optional `source_name / source_type / source_location` to `CreateBatchBody`; propagated to `record_import_batches` doc; inherited into every `employee_records` row via `batch_upload` as `intake_source_name / intake_source_type / intake_source_location / intake_batch_label` |
| `/app/backend/tests/test_track_19_25_discoverability_and_intake_session.py` | 14 new lock tests |

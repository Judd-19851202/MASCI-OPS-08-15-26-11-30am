# TRACK 19.59 · Test Report

## Lock test
`/app/backend/tests/test_track_19_59_vendor_lane_historical_records.py`

## Assertions (22)
1. All 9 governance docs exist under `/app/memory/`.
2. `ENTITY_KINDS` = `{"employee", "vendor"}`; `DEFAULT_ENTITY_KIND` = `"employee"`.
3. `vendor` lane added to `OWNERSHIP_LANES`; four original lanes preserved.
4. `LANE_APPROVERS["vendor"] == {"hr", "admin"}`.
5. All 15 required vendor document types present in the catalog.
6. No legal-conclusion slugs in the vendor catalog.
7. `CreateRecordBody` exposes `entity_kind` + `vendor_id` + `vendor_name` + `vendor_display_name`.
8. `CreateBatchBody` accepts `entity_kind`.
9. `vocabulary()` response includes `entity_kinds` + `default_entity_kind`.
10. `list_records()` accepts `entity_kind` + `vendor_id` + `vendor_name` query params.
11. `list_records()` defaults to employee scope when `entity_kind` is absent.
12. `create_record()` refuses cross-lane `entity_kind` (400).
13. `approve_record()` requires vendor identity for vendor-lane approvals.
14. Audit ledger records `entity_kind` + `vendor_id` + `vendor_name`.
15. Frontend intake exposes the vendor UI block + input testids.
16. Frontend intake sends `entity_kind` + `vendor_name` + `vendor_id` correctly.
17. Frontend intake hides the employee picker when lane is vendor.
18. No new backend upload engine / router.
19. No new vendor collection.
20. No new AP / invoice / payment / contract engine.
21. OI engine inventory unchanged (9 files).
22. PRD.md + CHANGELOG.md updated.
23. Prior track docs preserved.

## Combined lock arc
`pytest test_track_19_51_portal_audit.py … test_track_20_4_vendor_thread_audit.py test_track_19_59_vendor_lane_historical_records.py` → **all GREEN**.

## Employee lane regression
`pytest test_track_19_21_employee_records_platform.py test_track_19_21b_historical_records_intake.py test_track_19_22_operational_completion.py` → **all GREEN** (85 tests). Only the pre-existing `test_four_ownership_lanes_exist` was widened to acknowledge the new fifth lane — the assertion still names all four original lanes.

## Frontend
- ESLint on `HistoricalRecordsIntake.jsx` → 0 issues.
- Webpack compiles clean (HTTP 200 on preview URL).

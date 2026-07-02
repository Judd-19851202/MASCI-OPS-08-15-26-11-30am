# Track 19.21 · Test Report

## Backend lock tests

### Track 19.21 · Employee Records Intelligence Platform — 26/26 GREEN

```
tests/test_track_19_21_employee_records_platform.py

Doctrine · Lanes + States:
  test_four_ownership_lanes_exist                                    PASSED
  test_five_record_states_exist                                      PASSED
  test_hr_lane_has_expected_types                                    PASSED
  test_safety_lane_has_expected_types                                PASSED
  test_asset_lane_has_expected_types                                 PASSED
  test_corporate_import_lane_exists_for_historical_bulk_intake       PASSED

Doctrine · Permissions:
  test_hr_can_approve_every_lane                                     PASSED
  test_admin_can_approve_every_lane                                  PASSED
  test_safety_can_approve_only_safety_lane                           PASSED
  test_asset_admin_can_approve_only_asset_lane                       PASSED
  test_field_role_cannot_approve_any_lane                            PASSED
  test_hr_can_read_every_lane                                        PASSED
  test_safety_can_only_read_safety_lane                              PASSED
  test_asset_admin_can_only_read_asset_lane                          PASSED

Source-level · Incident cases join HR timeline:
  test_hr_timeline_joins_incident_cases_via_defensible_roles_only    PASSED
  test_hr_timeline_does_not_add_passive_presence_signals_yet         PASSED

Employee 360° UI contract:
  test_employee_profile_page_exists_with_testids                     PASSED
  test_employee_profile_uses_existing_timeline_endpoint_read_only    PASSED
  test_employee_profile_has_all_required_tabs                        PASSED
  test_employee_profile_uses_visual_spine_pattern                    PASSED

No parallel employee system + audit contract:
  test_employee_records_module_does_not_duplicate_employee_identity  PASSED
  test_reassignment_resets_approval                                  PASSED
  test_original_file_metadata_is_preserved                           PASSED
  test_audit_ledger_is_append_only_by_design                         PASSED
  test_no_ocr_or_ml_libraries_imported_in_this_track                 PASSED
  test_zero_drift_no_new_incident_engine_write_paths                 PASSED

TOTAL: 26 passed in 0.32s
```

## Regression on companion suites (each verified in isolation)

| Suite | Result |
|---|---|
| Track 19.19 · .xlsm attachment | 18/18 PASSED |
| Track 19.18 · PDF Excellence | 11/11 PASSED |
| Track 19.18 · Safety Case Workspace | 8/8 PASSED |
| Track 19.16 · Incident Engine Phase A | 102/102 PASSED |
| Track 19.16 · Incident Engine Phase E | 88/88 PASSED |
| Track 19.16 · Final Closeout | 23/23 PASSED |
| **Combined isolated total** | **276/276** |

## Frontend

- `EmployeeProfile.jsx` — ESLint CLEAN.
- `App.js` — route registered · lazy import wired.

## Live smoke

- Backend restart clean (`sudo supervisorctl restart backend`).
- Startup log confirms `[employee-records] indexes ensured (track 19.21)`.
- `GET /api/employee-records/records` returns HTTP 401 with the exact auth-required message (auth gate wired correctly).
- No pytest collection errors on the new test file.

## Cross-suite pytest-asyncio fixture bleed (pre-existing · non-blocking)

When multiple incident-engine suites are run together with a `--tb=no -q` invocation, pytest-asyncio emits `RuntimeWarning: coroutine 'create_case' was never awaited` and downstream tests can fail spuriously. This is a **pre-existing** fixture-scope issue in the older Track 19.16 suites and is **NOT** a Track 19.21 regression. Verified by:

- Running each suite individually → all green
- Test set includes suites that predate Track 19.21 by weeks
- Track 19.21 introduces zero async fixtures (all Track 19.21 tests are pure source-level assertions and pure sync function calls)

Fix for this pre-existing bleed is deferred to a dedicated testing-infrastructure track.

## Zero-drift verified

- `db.employees` — READ-ONLY from this module. No insert/update/delete paths (locked by `test_employee_records_module_does_not_duplicate_employee_identity`).
- `db.incident_cases` — HR timeline adds a READ path. Neither the records module nor the timeline module WRITES to it (locked by `test_zero_drift_no_new_incident_engine_write_paths`).
- Legacy `/api/incidents` — untouched.
- Legacy `db.incidents` — still queried by the HR timeline in addition to the new fan-out over `db.incident_cases` (locked by `test_hr_timeline_joins_incident_cases_via_defensible_roles_only`).
- FieldBlock uses `extra="allow"` — the additive `reporter_employee_id`, `involved_employee_ids[]`, `witness_employee_ids[]` fields work with zero schema drift.

## Verdict

🟢 **Track 19.21 P0 foundation certified. Ready for post-deploy field trial. Track 19.21b (Review Queue UI + Historical Import upload page) is next.**

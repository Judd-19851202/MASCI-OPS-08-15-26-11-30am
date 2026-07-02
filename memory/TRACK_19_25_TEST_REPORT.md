# TRACK 19.25 · Test Report

## Backend lock tests (isolated per-file)
| File | Passed |
|---|---|
| `test_track_19_25_discoverability_and_intake_session.py` | 14/14 |
| `test_track_19_24_hr_nav_wiring.py` | 7/7 |
| `test_track_19_22_operational_completion.py` | 29/29 |
| `test_track_19_21b_historical_records_intake.py` | 30/30 |
| `test_track_19_21_employee_records_platform.py` | 26/26 |
| **TOTAL** | **106/106 GREEN** |

## Live end-to-end (curl)
- Create batch with `source_name / source_type / source_location` → batch stored with all three fields
- `POST /batches/{id}/uploads` × 2 files → each record inherits `intake_source_name / intake_source_type / intake_source_location / intake_batch_label`
- Bulk classify + bulk approve → records reach `linked` state with session provenance intact
- `GET /employees/{empId}/records?lane=hr` → 2 records with `intake_source_name = "2019 HR File Cabinet"`

## Browser verification (Playwright)
- HR Historical Records Intake page: `intake-what-you-can-upload` × 1 · `intake-how-it-works` × 1 (14 chips + 3-step visual rendered) ✅
- HR Batches page: `batches-new-session-provenance` × 1 (source_name + source_type + source_location fields visible) ✅
- Screenshots saved: `/tmp/intake_v25.png`, `/tmp/batches_v25.png`

## Pre-existing bleed
Combined-suite asyncio bleed unchanged. Isolated per-file execution GREEN (source of truth).

**Verdict:** GO.

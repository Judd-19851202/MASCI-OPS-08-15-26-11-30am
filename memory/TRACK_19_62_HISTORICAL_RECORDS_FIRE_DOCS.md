# TRACK 19.62 · Historical Records — Fire-Specific Document Slugs

**Change:** `LANE_RECORD_TYPES["asset"]` in
`backend/routes/employee_records.py` extended with five additive slugs.

## New slugs
- `hydrostatic_test_certificate` — periodic (5-yr / 12-yr) hydro-test
  certificates for pressurized cylinders.
- `recharge_service_record` — post-use or annual recharge service
  tickets.
- `fire_ext_annual_service` — annual professional inspection tag / cert.
- `fire_ext_manufacturer_doc` — manufacturer spec / recall notice /
  bulletin.
- `fire_ext_retirement_record` — end-of-life record (destroyed /
  condemned / returned to vendor).

## Reused unchanged
- Same file preservation (Track 19.21b intake pipeline).
- Same SHA-256 verification.
- Same approval workflow (`{asset_admin, hr, admin}` for asset lane).
- Same audit (`employee_record_audit` collection).
- Same intake UI (`HistoricalRecordsIntake.jsx` reads the slugs
  data-driven).
- Same queue UI (`HistoricalRecordsQueue.jsx`).

## Linking to a fire extinguisher record
Uploads specify:
- `entity_kind="asset"`
- `ownership_lane="asset"`
- `asset_id=<extinguisher id>` (canonical from resolver) **or**
  `asset_unit_number=<unit_id>`
- `record_type=<one of the five slugs above>`

## Backwards compatibility
- Existing records without these slugs continue to work.
- Existing intake UI shows the new slugs automatically via the
  data-driven dropdown.
- Existing approval queue does not require code changes.

## What was NOT changed
- No new intake route.
- No new approval queue.
- No new lane.
- No new approver.
- No email trigger on upload or approval.
- No new OCR classifier (deferred to a future track).

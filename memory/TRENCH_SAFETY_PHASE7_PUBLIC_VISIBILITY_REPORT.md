# PHASE 7 — PUBLIC VISIBILITY REPORT

## Public surfaces preserved (no admin leakage)

### Existing public endpoints (untouched)
- `GET /api/trench-safety/public/overview` — counts only.
- `GET /api/trench-safety/public/assets/{ident}` — field-safe asset projection (Phase 3.5).
- `POST /api/trench-safety/public/damage-report` — anonymous damage reporting.

### New Phase 7 public endpoint
- `GET /api/trench-safety/public/assets/{ident}/photos` — returns ONLY `visibility="field_safe"` photos, stripped through `_photo_public_view`.

## What public users CAN do
- Scan a printed QR → opens `/trench-safety/assets/{asset_id}` (the existing Phase 3 public field landing).
- View asset ID, type, size, color, condition.
- See operational_status (including the DO-NOT-USE banner for any active hold).
- View field-safe photos only (Phase 7 new).
- Submit a damage report (Phase 3.5 unchanged).

## What public users CANNOT do
- Generate, download, or print QR labels (require_safety_or_admin gate).
- View `internal` photos.
- See uploader emails, source records, linked_record_id, or visibility metadata.
- See repair vendor / repair cost / completion notes / audit history.
- Trigger any state change via QR scan (verified by `test_qr_scan_does_not_change_asset_state`).

## Hold preservation across QR surface
A QR scan is read-only. Tested:
- `test_qr_scan_does_not_change_asset_state` → operational_status, current_project_id, current_location unchanged after public landing fetch.

The DO-NOT-USE banner extends to all four Phase 4B hold kinds (Inspection / Maintenance / Certification / Safety), already verified in Phase 4B regression.

## Public photo projection — proven safe
Test `test_photo_visibility_field_safe_appears_on_public` asserts that the public projection contains **none** of: `uploaded_by`, `source`, `linked_record_id`, `visibility`. The only keys exposed publicly are `id`, `asset_id`, `category`, `caption`, `image_data_url`, `uploaded_at`.

## Verdict
🟢 **Public field surface remains field-safe. Zero admin / PII / audit / cost / repair-internal data exposed.**

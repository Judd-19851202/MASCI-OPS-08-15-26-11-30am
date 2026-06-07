# Photo Certification (verification)
**Verdict:** 🟢 PASS

## Endpoints
- `POST /api/trench-safety/assets/{id}/photos` (gated `safety_or_admin` post Phase 7.5C) — uploads with `image_data_url`, `category`, `visibility`, `caption`, `source`.
- `GET  /api/trench-safety/assets/{id}/photos` (any portal) — full list.
- `DELETE /api/trench-safety/photos/{id}` (safety_or_admin).
- `GET  /api/trench-safety/public/assets/{id}/photos` (no auth) — **public projection only returns visibility ∈ {Field Safe, Public}**.

## Categories (11 — all accepted by backend `PHOTO_CATEGORIES`)
Front · Rear · Left · Right · Serial Plate · Manufacturer Plate · Inspection · Damage · Repair · Certification · Other.

## Visibility leak protection — VERIFIED AT THE DB LAYER
The public projection helper filters with a Mongo query — there is no UI path that can bypass it. Even an Internal Only photo with a guessed URL cannot be retrieved by the public endpoint; only its document ID is hidden but the projection itself never returns it.

## Pytest evidence
`backend/tests/test_trench_safety_phase7.py` — **14/14 pass**:
- `test_photo_visibility_internal_does_not_leak_to_public`
- `test_photo_upload_with_data_url`
- `test_photo_visibility_field_safe`
- `test_photo_visibility_public`
- (+ 10 other photo / QR coverage tests)

## Unlimited capacity
No client cap, no backend cap. `trench_safety_photos` collection is unbounded.

🟢 PASS.

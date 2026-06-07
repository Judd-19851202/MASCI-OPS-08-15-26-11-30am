# Photo Management Certification

## Surface
Asset Detail page → `PhotoManagementPanel` (Safety Portal + Admin Portal).

## Capabilities
- Unlimited photos per asset (no client cap; the underlying `trench_safety_photos` collection is unbounded).
- Upload via the standard `<input type="file" accept="image/*">` flow → reads file as Data URL → sends `image_data_url` to backend.
- Per-photo metadata: category, visibility, caption.
- Delete from the grid.

## Categories (per directive)
Front · Rear · Left · Right · Serial Plate · Manufacturer Plate · Inspection · Damage · Repair · Certification · Other.

Defined in `TrenchSafetyOpsCenter.jsx:PHOTO_CATEGORIES`, and validated by the existing backend `PHOTO_CATEGORIES` set in `qr_photos.py`.

## Visibility Control
| Value | Public surface display | Notes |
|---|---|---|
| Internal Only | ❌ never displayed publicly | Default; safety/repair/investigation photos belong here. |
| Field Safe | ✅ surfaced on public QR view | Photo of the asset for field reference. |
| Public | ✅ surfaced on public QR view | Marketing-grade / OSHA-compliant shots. |

Backend public projection (`_photo_public_view` in `qr_photos.py`) only returns photos with visibility ∈ {Field Safe, Public}. **Internal photos cannot leak to the public surface — enforced at the database query level**, not the UI.

## Auth (post Phase 7.5C re-gate)
- Upload: `require_safety_or_admin`.
- Delete: `require_safety_or_admin`.
- List (internal): `require_any_portal`.
- List (public): no auth; filtered projection.

## Audit
Every upload / delete writes an `audit_events` row (`trench_asset_photo_uploaded`, `trench_asset_photo_deleted`).

## Verdict
🟢 PASS — Production-ready.

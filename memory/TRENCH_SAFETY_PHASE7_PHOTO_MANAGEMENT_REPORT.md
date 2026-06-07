# PHASE 7 — PHOTO MANAGEMENT REPORT

## Collection
`db.trench_safety_photos` — new collection, single direction (no mirror, no cross-collection writes). Each document:
```jsonc
{
  "id": "<uuid>",
  "asset_id": "TB-07",
  "asset_uuid": "<asset.id>",
  "category": "Front | Rear | Side | Serial Number | Manufacturer Plate | QR Label | Inspection Photo | Damage Photo | Repair Photo | Deployment Photo | Other",
  "caption": "free text",
  "image_data_url": "data:image/png;base64,...",   // ≤ 8 MB enforced
  "source": "Asset Detail | Inspection | Repair | Damage Report | QR Field Report",
  "linked_record_id": "inspection:<id>" | "repair:<id>" | null,
  "visibility": "internal" | "field_safe",
  "uploaded_by": "<email>",
  "uploaded_at": "<iso8601>"
}
```

## Endpoints
| Method · Path | Auth | Behavior |
|---|---|---|
| `POST /api/trench-safety/assets/{ident}/photos` | shop_or_admin | Validate category / visibility / source / size cap; persist; audit |
| `GET /api/trench-safety/assets/{ident}/photos` | any_portal | List with optional `category`, `visibility`, `limit` filters |
| `DELETE /api/trench-safety/photos/{photo_id}` | safety_or_admin | Hard delete; audit |
| `GET /api/trench-safety/public/assets/{ident}/photos` | none | Field-safe projection only |

## Storage pattern (no new system)
Photos persist as base64 data URLs inside the document — same approach used by existing `safety_documents`. 8 MB per-photo cap enforced server-side (`test_photo_size_cap_enforced` → HTTP 413).

## Public projection (field-safe)
The `_photo_public_view` helper strips: `uploaded_by`, `source`, `linked_record_id`, `visibility`, `asset_uuid`. Returns only `id`, `asset_id`, `category`, `caption`, `image_data_url`, `uploaded_at`. Verified by `test_photo_visibility_field_safe_appears_on_public`.

## Internal vs field-safe enforcement
- Default visibility = `internal`.
- The public endpoint queries `visibility=field_safe`. An `internal` photo is invisible publicly. Verified by `test_photo_visibility_internal_hidden_from_public` and `test_public_photo_endpoint_does_not_leak_internal`.

## Linked record metadata
The `linked_record_id` field accepts free-form refs (e.g. `inspection:<id>` or `repair:<id>`). It is persisted and returned to authenticated viewers; never exposed publicly. Verified by `test_photo_linked_record_id_persists`. Existing inspection / repair endpoints already accept `photo_refs[]` — Phase 7 photos can be added by category later via linked_record_id without a schema change.

## Audit events
`trench_asset_photo_uploaded` and `trench_asset_photo_deleted` route through the shared audit pipeline.

## Tests
All 7 photo tests pass: upload, listing, category validation, field-safe visibility, internal hidden, linked_record persistence, size cap, public no-leak.

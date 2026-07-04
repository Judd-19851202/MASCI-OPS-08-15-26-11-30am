# TRACK 19.62 · Assignment / Relationship Model — Phase A

**Doctrine:** One extinguisher = one current primary assignment. History
comes from the existing audit/inspection/timeline, not a new
relationship-history collection.

## Fields added to `db.fire_extinguishers` (additive · backwards-compat)
All optional; every existing row continues to work.

- `assigned_target_kind` — enum-like string (see below)
- `assigned_target_ref` — canonical id / unit_number / project_number of the target
- `assigned_target_label` — display label (e.g., "Excavator 37 · Cab")
- `assigned_location_detail` — free text (e.g., "Passenger side, near door")
- `assigned_project_number` — project number if applicable
- `assigned_unit_number` — unit number if applicable
- `assigned_facility_name` — facility name if applicable
- `assigned_room_name` — room name if applicable
- `serial_number` — additive identity
- `asset_tag` — additive identity

## Supported target kinds
`asset` · `equipment` · `vehicle` · `trailer` · `facility` · `building` · `room` · `project` · `job_trailer` · `shop_area` · `office_area` · `storage_area` · `other_location`.

## Read paths
- **Universal Asset Thread** consumes the fields directly through the
  resolver fallback and renders them in Mission + Relationships.
- **Parent Asset Thread (Fleet pilot)** queries the safety endpoint
  filtered by `?assigned_target_ref=<unit>` to surface each mounted
  extinguisher as a relationship edge + attention item.
- **Safety Fire Extinguishers list** unchanged (author-side) with a new
  deep-link column into the Asset Thread.

## What this is NOT
- Not a new collection.
- Not a many-to-many association table (Phase A rule: 1:1 primary).
- Not a history-of-assignments collection (audit lives on the existing
  audit fields and inspection log).

## Zero-Drift
- No new backend table.
- No new frontend collection state.
- Reuses the existing safety endpoint; only its query surface is
  additive.

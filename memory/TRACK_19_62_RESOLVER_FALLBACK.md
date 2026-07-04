# TRACK 19.62 · Resolver Fallback — Phase A

## Behavior

`GET /api/asset-spine/resolve?ref=<...>`:

1. Probe `db.equipment_master` (existing v19.61 lookup) on
   `id`, `asset_id`, `unit_number`, `asset_number`, `serial_number`, `vin`.
2. On no match, **Track 19.62 Phase A** falls back to
   `db.fire_extinguishers` on `id` or `unit_id` (case-insensitive).
3. If the fire fallback matches, return a synthetic canonical payload:

```json
{
  "ok": true,
  "ref": "<input>",
  "asset_id": "<fe.id>",
  "unit_number": "<fe.unit_id>",
  "serial_number": "<fe.serial_number>",
  "vin": null,
  "asset_class": "Fire Protection",
  "asset_type": "<Type> Fire Extinguisher",
  "status": "active",
  "source": "fire_extinguishers",
  "assigned_target_kind": "<...>",
  "assigned_target_ref":  "<...>",
  "assigned_target_label": "<...>",
  "assigned_location_detail": "<...>",
  "assigned_project_number": "<...>",
  "assigned_unit_number":    "<...>",
  "assigned_facility_name":  "<...>",
  "assigned_room_name":      "<...>",
  "last_inspection_date": "<...>",
  "next_due_date":        "<...>",
  "last_status":          "<...>",
  "location_kind":        "<...>"
}
```

4. If both probes fail — return `HTTP 404` (existing behavior).

## Guarantees

- **Never migrates** rows from `db.fire_extinguishers` into
  `equipment_master`.
- **Never duplicates** the fire record.
- Existing consumers of the resolver continue to work identically — the
  `source` field is additive.
- The `asset_class` = `"Fire Protection"` matches the taxonomy v1.1.0
  entry exactly.

## Accepted identifier types
- extinguisher number (unit_id)
- asset tag
- QR code (if the ref matches unit_id / id)
- barcode (same)
- serial number (through resolver's existing serial probe)
- legacy identifier (via unit_id case-insensitive match)
- extinguisher id (canonical UUID)
- unit assignment reference (via `equipment_master_id` on fire ext)

## Failure modes
- 401 if the caller has no portal token (existing rule).
- 404 if neither probe returns a match.
- 422 if `ref` is empty.

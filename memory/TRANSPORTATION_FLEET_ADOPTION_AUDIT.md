# Transportation Fleet Adoption Audit (Phases 1–3)

## Phase 1 · Fleet Inventory (live preview DB)

Source: `equipment_master` collection (705 total assets across 28
categories).

### Transportation-capable categories surfaced (7)

| Category | Total | Active | Inactive | Available | Maintenance Hold | Retired | Safety Hold |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Dump Trucks | 41 | – | – | – | – | – | – |
| Tractor Trailer Trucks | 12 | – | – | – | – | – | – |
| Service Trucks | 17 | – | – | – | – | – | – |
| Water Trucks | 6 | – | – | – | – | – | – |
| Misc Trucks | 4 | – | – | – | – | – | – |
| Flatbed Trucks | 3 | – | – | – | – | – | – |
| Trailers | 53 | – | – | – | – | – | – |
| **TOTAL** | **136** | | | | | | |

Note: `is_active` and `operational_status` are blank for the entire
transport-capable subset of the synthetic preview DB; the projection
treats `is_active != False` as active, so all 136 surface.

Plus 12 leased overlays already in `transport_trucks` →
**148 total operational fleet rows**.

### Categories explicitly EXCLUDED (per directive)

* `Pickup Trucks` (11) — passenger / light-duty, not dispatchable.
* `Supervisor / Mgmt Trucks` (2) — management vehicles.
* All non-truck categories (Excavators, Loaders, Trench Safety,
  Generators, Pumps, Air Compressors, Welders, etc.).

## Phase 2 · Adoption Preview (read-only)

`GET /api/admin/transportation/fleet/adoption-preview` returned (live):

```json
{
  "categories_in_scope": [...7 categories...],
  "category_totals": {"Dump Trucks":41, ...},
  "summary": {
    "already_adopted": 0,
    "would_adopt": 136,
    "skipped_inactive": 0,
    "skipped_retired": 0,
    "conflicts": 0,
    "missing_equipment_id": 0,
    "unknown_classification": 4,
    "leased_only_overlays": 12
  }
}
```

* **No writes** were performed during preview (verified — fleet
  projection still shows `masci_fleet_adopted=0` after preview call).
* **Unknown classification** flag fires for 4 `Misc Trucks` rows whose
  category alone cannot determine `transportation_classification` —
  operator should refine post-adoption via the overlay editor.

## Phase 3 · Classification Audit

### Rules used by `_derive_transportation_classification`

| `equipment_master.category` (lower) | Derived classification |
| --- | --- |
| contains `dump` | `end_dump` |
| contains `tractor` | `day_cab` |
| contains `water` (or preop\_equipment\_type `water`) | `water_truck` |
| contains `service` | `service_truck` |
| contains `flatbed` | `flatbed` |
| contains `trailer` | `equipment_trailer` |
| anything else | `other` (flagged as `unknown_classification`) |

### Excluded explicitly (correct behaviour observed in preview)

| Category | Reason |
| --- | --- |
| Pickup Trucks | Passenger / light-duty |
| Supervisor / Mgmt Trucks | Management vehicle |
| Excavators · Loaders · Backhoes · Dozers · Skid Steers · Rollers · Sweepers · Road Graders · Paving Equipment · Compactors · Pumps · Generators · Light Towers · Welders · Air Compressors · Storage / Containers · Trench Safety · Attachments · Misc Equipment | Not driver-operated on-road haulers |

### Adopt endpoint enforces the rule

Attempting `POST /admin/transportation/fleet/equipment/{id}/adopt` on a
non-transportation-capable category returns **HTTP 422** with the
message `"equipment category '{cat}' is not transportation-capable"`.
Verified by `test_fleet_adopt_rejects_non_transport_category`.

## Operator next steps

1. Adopt all 136 from the Fleet page (one click).
2. Open each of the 4 unknown-classification rows and choose the right
   `transportation_classification` from the operational editor.
3. Refine `truck_type`, `transportation_classification`, and
   `primary_division` on rows that need yard-level placement.

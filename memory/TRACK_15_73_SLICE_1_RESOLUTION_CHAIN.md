# TRACK 15.73 SLICE 1 · Resolution Chain (canonical source-of-truth)

**Date**: 2026-02-11

## Authoritative lookup chain (post-fix)

```
USER ACTION (Pre-Op form / DVIR form / Asset Profile)
    │
    │ types or picks unit  →  POSTs equipment_unit
    │                          (NOW canonical unit_number after Slice 1 frontend fix)
    ▼
GET /api/asset-spine/taxonomy/by-unit/{u}
  in: routes/asset_spine.py · function taxonomy_by_unit
  gate: require_any_portal (admin OR pm OR shop OR hr OR safety OR dispatch OR fl OR field_leadership)
    │
    ▼
  STEP 1   db.equipment_master.find_one({"id": u})
                ↳ matches if caller passed equipment_master UUID
                ↳ resolution_source = "id"
    │
    ▼ (miss)
  STEP 2   db.equipment_master.find_one({"unit_number": regex(^u$, i)})
                ↳ case-insensitive literal match (escaped)
                ↳ resolution_source = "unit_number"
    │
    ▼ (miss)  Track 15.73 Slice 1 graceful fallback
  STEP 3   split u on " — " | " - " | em-dash | en-dash
           db.equipment_master.find_one({"unit_number": regex(^leading$, i)})
                ↳ rescues legacy display_label payloads
                ↳ resolution_source = "display_label_strip"
    │
    ▼ (miss)
  STEP 4   return {found: false, resolution_source: "not_found"}
                ↳ honest "Unit not cataloged" state — no fabrication
```

## Authoritative tier diagram

```
                ┌─────────────────────────────────┐
   CANONICAL ── │       equipment_master          │ ← single source of truth
                │   id · unit_number · category   │
                │   make · model · year · plate   │
                │   display_label (DERIVED)       │
                └────────────────┬────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            ▼                    ▼                    ▼
   ┌────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │ asset_mappings │  │  motive_events   │  │   fleet_status   │
   │  (cross-walk)  │  │  (telemetry)     │  │   (aggregator)   │
   │  masci_eq_id   │  │  raw.number      │  │  unit_number     │
   │  motive.id     │  │  vehicle_id      │  │  computed daily  │
   │  maintainx.id  │  │                  │  │                  │
   └────────────────┘  └──────────────────┘  └──────────────────┘
        MIRROR              MIRROR                 CONSUMER

   equipment_units  →  LEGACY (pre-asset-spine) · separate `unit_label` ID space
                                 NOT consulted by Pre-Op resolver.
                                 Retained for backward compat only.

   equipment_inspections (CONSUMER) → writes equipment_unit (string)
                                       writes equipment_master_id (FK · only 39 / 870)
```

## Lookup priority by callsite

| Callsite | Endpoint | Reads | Writes |
|---|---|---|---|
| `CanonicalInspectionSections.jsx` (Pre-Op canonical template) | `GET /asset-spine/taxonomy/by-unit/{u}` | equipment_master | — |
| `SmartUnitClassificationChip.jsx` (Pre-Op chip) | `GET /asset-spine/taxonomy/by-unit/{u}` | equipment_master | — |
| `EquipmentCombo.jsx` (any form needing a unit picker) | `GET /equipment-master` | equipment_master | — |
| `NewEquipmentInspection.jsx` (Pre-Op submission) | uses EquipmentCombo | equipment_master | equipment_inspections (writes `equipment_unit` + `equipment_master_id`) |

## Why the other collections are NOT consulted by the Pre-Op chain

- `asset_mappings` exists to bridge Motive/MaintainX vehicle IDs ↔ MASCI equipment_master IDs. It is **never queried by Pre-Op**; reading from it would add false authority.
- `motive_events` is a telemetry log — useful for live GPS / driver but not for the equipment registry contract.
- `fleet_status` is a computed roll-up of inspection outcomes (latest_inspection_id, status). It is downstream of Pre-Op, not authoritative for the unit's existence.
- `equipment_units` is a legacy pre-asset-spine collection with its own `unit_label` (484 rows in preview, separate ID space). It was deprecated by the asset spine but never deleted — kept for historical inspections.

## Resolution source telemetry (new in Slice 1)

Every successful lookup now returns `resolution_source` ∈ {`id`, `unit_number`, `display_label_strip`, `not_found`}. This lets the Admin observability panel surface drift between submitted payloads and canonical keys in real time — without requiring DB access.

## Approved consumer pattern (canonical post-Slice 1)

```js
// Pre-Op form (or any unit picker callsite)
<EquipmentCombo
  value={data.equipment_unit}
  onChange={(v) => set("equipment_unit", v)}
  onPick={(it) => setData((p) => ({
    ...p,
    equipment_unit:     it.unit_number  || it.display_label || it.make_model || "",
    equipment_master_id: it.id          || p.equipment_master_id,
    equipment_make:      it.make_model  || p.equipment_make,
    equipment_serial:    it.vin_serial_number || p.equipment_serial,
  }))}
/>
```

`equipment_unit` becomes the canonical key. `equipment_master_id` provides the FK
for direct joins. `equipment_make` and `equipment_serial` capture human-readable
context separately — never overloaded into the unit identifier.

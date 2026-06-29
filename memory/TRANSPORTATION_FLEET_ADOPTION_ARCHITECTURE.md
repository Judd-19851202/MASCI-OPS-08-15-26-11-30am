# Transportation Fleet Adoption Architecture

**Track:** 19.02A
**Status:** SHIPPED
**Doctrine:** One Equipment Master. Multiple operational views.

---

## 1 · Architectural Principle

Transportation Operations is a **READ-MOSTLY operational view** into the
existing MASCI Equipment platform. Transportation does **NOT** own a
parallel fleet database. Every asset on a MASCI truck route already
lives in `equipment_master` + `equipment_units`. Transportation simply
attaches an **operational overlay** that carries dispatch state,
driver/carrier assignment, classification, safety hold, and
transportation notes.

```
                    ┌───────────────────────────────┐
                    │ Equipment Master              │  ← source of truth
                    │  · VIN · Make · Model · Year  │     for IDENTITY
                    │  · Purchase data · Engine hrs │
                    │  · Maintenance history        │
                    │  · Documents · Motive · GPS   │
                    └────────────┬──────────────────┘
                                 │  one-to-one  (equipment_id FK)
                                 ▼
                    ┌───────────────────────────────┐
                    │ Transportation Overlay        │  ← operational
                    │ (transport_trucks)            │     view
                    │  · status · safety_hold       │
                    │  · classification · driver    │
                    │  · carrier · dispatch_ready   │
                    │  · transportation_notes       │
                    │  · operational_tags           │
                    └───────────────────────────────┘
```

## 2 · Data Model

`transport_trucks` is the overlay collection. Adoption rules:

| Field | Source | Editable from Transportation |
| --- | --- | --- |
| `equipment_id` | FK → `equipment_master.id` | **NO** (immutable after adoption) |
| `truck_number`, `vin`, `plate` | mirrored read-only from EM at adoption | **NO** (cosmetic mirror only) |
| `truck_type` | derived from `equipment_master.category` | YES |
| `transportation_classification` | derived from category + preop_type | YES |
| `status` | Transportation operational state | YES |
| `safety_hold` | Transportation flag | YES |
| `carrier_id`, `driver_id` | Transportation assignment | YES |
| `dispatch_ready` | Transportation gate | YES |
| `primary_division` | Transportation organisation | YES |
| `operational_tags` | free-form Transportation tags | YES |
| `transportation_notes` | dispatcher / TM notes | YES |
| `active_for_transport` | Transportation enable/disable | YES |
| `bulk_adoption_batch_id` | rollback handle | system-managed |

## 3 · Endpoints (all under `/api/admin/transportation/fleet/*`)

| Method | Path | Role | Purpose |
| --- | --- | --- | --- |
| GET | `equipment` | dispatch+admin | Projection over equipment_master + transport_trucks |
| GET | `adoption-preview` | dispatch+admin | READ-ONLY · what would happen if we adopted now |
| POST | `adoption-bulk` | admin | Idempotent bulk overlay creation |
| POST | `adoption-bulk/{batch_id}/rollback` | admin | Remove overlays created by a specific batch |
| POST | `equipment/{id}/adopt` | admin | Single-row adoption |
| PATCH | `equipment/{id}/overlay` | dispatch+admin | Edit operational fields (gated by allow-list) |

## 4 · Permission Model

| Role | Read projection | Preview | Adopt single | Bulk adopt | Rollback | Edit overlay |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Super Admin | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Transportation Admin | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Dispatcher | ✓ | ✓ | – | – | – | ✓ |
| HR | – | – | – | – | – | – |
| Anonymous | – | – | – | – | – | – |

## 5 · Idempotency Guarantee

Bulk adoption is keyed on `(tenant, equipment_id)`. The engine pre-loads
the set of already-adopted `equipment_id`s before iterating
`equipment_master`. If a previously-created overlay exists, the row is
skipped. Running the bulk endpoint N times produces the same set of
overlays as running it once. Verified by
`test_bulk_adoption_creates_and_is_idempotent` and
`test_bulk_adoption_no_duplicate_overlays`.

## 6 · Why this design

* **One source of truth.** VIN / Make / Model / Year / purchase data
  exist exactly once in MASCI — in Equipment Master.
* **No sync jobs.** The projection joins live on every read; nothing
  to fall out of date.
* **Safe rollout.** Bulk adoption is idempotent and rollback-able.
* **Permission boundary respected.** Protected enterprise fields fail
  PATCH attempts with a clear operator message.
* **Operational efficacy.** Dispatchers can edit Transportation reality
  in seconds without ever touching the Equipment platform.

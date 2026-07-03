# TRACK 20.5 · Universal Thread Fit — Asset / Equipment

Every one of the 10 Universal Operational Thread sections is either
already served by a certified surface or maps trivially to one. **Nothing
in Section 1–10 requires new backend, new storage, new score, or new
email.**

Notation: **Reuse unchanged** = wire directly · **Adapter** = client-side
map only · **Extend** = tiny discriminator on existing route · **Build** =
new code (should not appear anywhere in this matrix).

## Section-by-section fit

| # | Section | Existing surface | Endpoint / component | Verdict | Notes |
|---|---|---|---|---|---|
| 1 | **Mission Overview** | `asset_spine` profile | `GET /api/asset-spine/assets/{asset_id}/profile` | **Reuse unchanged** | Fused unit + taxonomy + status + owner. Thread renders one row. |
| 2 | **Attention** | `asset_care.alerts` + fleet_ops OOS | `GET /api/asset-care/alerts` (filter by asset) + `GET /api/fleet/units` | **Adapter** | Client filters existing alerts by asset_id. Same as pilot. |
| 3 | **Operational Guidance** | Guidance Card + OI `/summary` | `GET /api/operational-intelligence/summary?product=…` | **Adapter** | Class-aware product routing (map `equipment_master.category` → product slug). If no product, render "no product yet". |
| 4 | **Timeline** | `asset_service_events` | `GET /api/assets/{unit_number}/timeline` | **Reuse unchanged** | Certified backbone from Track 13.26 — same one the pilot uses. |
| 5 | **Relationships** | Timeline + `asset_transfers` + PO + incidents | Derived client-side from timeline events + transfers + PO records + incident links | **Adapter** | RelationshipGraph primitive already exists; no new endpoint. |
| 6 | **Documents** | `asset_documents` + Historical Records asset lane (19.61) | `GET /api/asset-spine/assets/{id}/documents` + `GET /api/employee-records/records?entity_kind=asset&entity_id=…` | **Extend (small)** | Add `entity_kind="asset"` to intake — mirror of 19.59 vendor lane. |
| 7 | **Photos** | `asset_documents` where `is_photo=true` + missing-photos dashboard | `GET /api/asset-spine/assets/{id}/documents?is_photo=true` + `GET /api/asset-spine/dashboard/missing-photos` | **Reuse unchanged** | Photo store is asset_documents. No new photo store. |
| 8 | **Operational Intelligence** | OI engine products | `/api/operational-intelligence/summary` filtered by class | **Adapter** | Same as Section 3 — class routing, no new OI products. |
| 9 | **History** | `asset_service_events` deep window + OI `history` | `GET /api/assets/{unit_number}/timeline?from=…&to=…` | **Reuse unchanged** | Timeline is already history-shaped. |
| 10 | **Audit** | Per-collection audit fields projected onto timeline | Same timeline endpoint; audit view flag | **Reuse unchanged** | No new audit collection. |

## Verdict summary

- **Reuse unchanged:** 1, 2 (via alert filter), 4, 7, 9, 10 → **six sections**.
- **Adapter (client only):** 3, 5, 8 → **three sections**.
- **Extend (backend, tiny):** 6 → **one section** (historical records asset
  lane — same pattern as vendor lane 19.59).
- **Build new:** **zero sections**.

## Identifier plumbing

The pilot uses `/fleet/unit/:unit_number`. Track 19.61 introduces a
canonical **AssetIdentifierResolver** (backend helper or client-side
resolver) that accepts any of:

- `asset_id` (canonical)
- `unit_number` (fleet convention)
- `serial_number` (phones, iPads, lasers, survey gear)
- Legacy `equipment_number` / `equipment_master._id`

...and normalizes to `asset_id`. The resolver is **not a new collection**
— it reads `equipment_master` via `asset_spine`.

## Six pillars alignment

- **Powerful** — the full operational story is here already; the thread
  just presents it.
- **Simple** — one page, ten sections, six lenses.
- **Beautiful** — reuses `OperationalThreadPage` unchanged.
- **Trusted** — every fact points to a certified surface named above.
- **Proven** — the Fleet Unit Thread pilot has been running since Track
  19.55 and is covered by lock tests.
- **Operational** — a shop manager, dispatcher, superintendent, safety
  officer, or executive gets the same page with role-lensed content.

**Fit certified.**

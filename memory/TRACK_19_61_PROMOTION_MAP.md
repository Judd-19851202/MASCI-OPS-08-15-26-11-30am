# TRACK 19.61 · Promotion Map — Asset / Equipment Thread

Every section of the Asset Thread wired to an existing certified
surface. No new backend logic beyond the two documented extensions.

## Route

`/admin/assets/:assetRef/thread` → `AdminAssetThread.jsx`.
Fleet lens alias `/fleet/unit/:unit_number` → `FleetUnitThread.jsx`
(unchanged Track 19.55 pilot).

## Section-by-section wiring

| # | Section | Data source | Endpoint | Verdict |
|---|---|---|---|---|
| 1 | Mission Overview | `equipment_master` via `asset_spine` | `GET /api/asset-spine/assets/{asset_id}/profile` | Reuse unchanged |
| 2 | Attention | Backbone events + pending doc queue | `GET /api/assets/{unit_number}/timeline` + `GET /api/employee-records/records?entity_kind=asset&asset_id=…` | Client-side adapter over existing endpoints |
| 3 | Operational Guidance | OI product (class-routed) | `GET /api/operational-intelligence/summary` | Adapter — class → existing product (`fleet_intelligence` or `shop_intelligence`) |
| 4 | Timeline | Track 13.26 backbone + Historical Records | `GET /api/assets/{unit_number}/timeline` + `GET /api/employee-records/records?entity_kind=asset&asset_id=…` | Reuse unchanged |
| 5 | Relationships | Backbone events + docs + `equipment_master.department` | derived client-side | Adapter (RelationshipGraph primitive) |
| 6 | Documents | Historical Records asset lane + native asset docs | `GET /api/employee-records/records?entity_kind=asset&asset_id=…` (+ future `GET /api/asset-spine/assets/{id}/documents` for born-digital) | Extend — new lane · same collection |
| 7 | Photos | `asset_documents` where `is_photo=true` (deferred; honest-empty for now) | (existing endpoints, not yet consumed by this page) | Reuse unchanged |
| 8 | Operational Intelligence | Same as Section 3 | `GET /api/operational-intelligence/summary` | Adapter |
| 9 | History | Timeline window + docs history | `GET /api/assets/{unit_number}/timeline?from=…&to=…` | Reuse unchanged (rendered by shell) |
| 10 | Audit | Per-collection audit fields projected onto timeline | Same timeline endpoint | Reuse unchanged |

## Universal Asset Identifier Resolver

`GET /api/asset-spine/resolve?ref=…` accepts any of:

- `asset_id` (canonical)
- `unit_number`
- `asset_number`
- `serial_number` (phones, iPads, lasers, survey gear)
- `vin` (trucks, trailers)
- Legacy identifiers (matched case-insensitively on the above fields)

Returns:

```json
{
  "ok": true,
  "ref": "<input>",
  "asset_id": "<canonical>",
  "unit_number": "…",
  "serial_number": "…",
  "vin": "…",
  "asset_class": "…",
  "asset_type": "…",
  "status": "active|retired"
}
```

Reads `db.equipment_master.find_one(...)` — **zero new collection**.

## Class-aware OI product routing

Client-side function `oiProductForClass(assetClass)`:

- `Truck` · `Trailer` · `Heavy Equipment` · `Trench Safety` ·
  `Roadway / Traffic Control` → **`fleet_intelligence`**
- `Survey` · `GPS / Machine Control` · `Technology Equipment` ·
  `Safety Equipment` · `Support Equipment` · `Facility Asset` ·
  `Temporary Asset` → **`shop_intelligence`**
- Otherwise → **null** (honest empty)

**Zero new OI products.**

## Historical Records asset lane

Extension of `backend/routes/employee_records.py`:

- `ENTITY_KINDS = ("employee", "vendor", "asset")`
- `LANE_RECORD_TYPES["asset"]` extended additively with the 12
  asset-native document types.
- `CreateRecordBody` gains `asset_id`, `asset_unit_number`,
  `asset_display_name`.
- `list_records` accepts `entity_kind=asset`, `asset_id=…`,
  `asset_unit_number=…`.
- Approval logic branches on `entity_kind=="asset"` and requires
  asset identity + record_type before linking.
- Cross-lane guard: `entity_kind="asset"` only permitted in the
  `asset` ownership lane.

**Backwards compatible:** every existing record without `entity_kind`
continues to be treated as `"employee"`; every existing asset-lane
issuance record continues to work identically.

## Zero-Drift accounting

| Concern | Ships? | Note |
|---|---|---|
| New collection | ❌ | Everything reuses `equipment_master` + `employee_records`. |
| New OI product | ❌ | Existing products only; missing → honest empty. |
| New PDF renderer | ❌ | Not consumed on this page. |
| New email flow | ❌ | AdminAssetThread and resolver are silent. |
| New score / health % | ❌ | Qualitative labels only (Good / Attention Needed / Critical / Restricted). |
| New relationship graph | ❌ | `RelationshipGraph` primitive reused. |
| New audit collection | ❌ | Per-collection audit + backbone events. |
| Permission widening | ❌ | Admin-only gate; consumers keep existing rights. |
| Fleet pilot changes | ❌ | `FleetUnitThread.jsx` byte-identical. |
| Public URL | ❌ | No public route. |

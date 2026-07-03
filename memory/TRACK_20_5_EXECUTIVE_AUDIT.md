# TRACK 20.5 · Asset / Equipment Operational Thread — Executive Audit

**Track type:** Forensic audit · docs-only · zero code changes · zero live email.
**Question answered:** Does the Asset / Equipment Operational Thread already exist,
and if not, what is the smallest correct path to promote it?

## Executive verdict

**PROMOTE + EXTEND (small).**

The Fleet Unit Thread pilot shipped in Track 19.55 (`/fleet/unit/:unit_number` →
`OperationalThreadPage`) already renders the 10-section Universal Operational
Thread over the certified asset backbone. The canonical Asset Taxonomy
(Track 13.31B Day-0) already covers **every** class the user enumerated —
Heavy Equipment, Trucks, Trailers, Trench Boxes / Road Plates, Roadway /
Traffic Control, Survey (including Pipe Lasers, Total Stations, GPR,
Utility Locators), GPS / Machine Control, Technology (Phones · Tablets ·
iPads · Laptops · Radios · Drones), Safety Equipment (PPE), Support
Equipment, Facility Assets, Temporary / Rental Assets, Other Assets.

The pilot is currently scoped only to fleet-truck `unit_number` lookup. To
serve the full asset universe, Track 19.61 must ship a **very small**
extension layer — **no new collection, no duplicate timeline, no duplicate
document store, no new score model, no new email flow**:

1. **Universal Asset Identifier Resolver** — one read-only endpoint or
   client helper that maps `{asset_id | unit_number | serial | tag |
   equipment_master.equipment_number}` to a single canonical `asset_id`
   from `equipment_master` via `asset_spine`.
2. **Historical Records asset lane** — mirror of the vendor lane from
   Track 19.59: add `entity_kind="asset"` to `employee_records` so
   HR / Admin can upload legacy paper (purchase orders, warranty cards,
   registrations, calibration certificates, phone-transfer sign-offs)
   without duplicating `asset_documents`.
3. **AdminAssetThread.jsx** (or per-class routes that all render the same
   shell) at `/admin/assets/:asset_ref/thread`, `/shop/assets/:asset_ref/thread`,
   `/fleet/unit/:unit_number` (unchanged pilot alias). One page, six lenses.
4. **Class-aware OI product routing** — the pilot hard-codes
   `fleet_intelligence`. The extension routes to the correct existing OI
   product per asset_class (or renders a graceful "no OI product yet"
   card). Zero new OI products.

Estimated Track 19.61 budget: **≤ 250 backend LOC** (identifier resolver +
`entity_kind="asset"` discriminator on the existing historical records
route — same shape as Track 19.59 vendor lane) · **≈ 550 frontend LOC**
(one thread page that reuses OperationalThreadPage identically to Vendor /
Project / Incident / Employee threads) · **1 lock file**.

## What already exists (do not rebuild)

| Capability | Owner | Endpoint / Component | Track |
|---|---|---|---|
| Asset master (single record per unit) | `equipment_master` | via `asset_spine` GET `/api/asset-spine/assets/{asset_id}` | 13.31B · FORGEDOPS P0.1 |
| Canonical taxonomy (class · type · behavior) | `services/asset_taxonomy.py` | in-code | 13.31B D0/D1 |
| Timeline / service events | `asset_service_events.py` | GET `/api/assets/{unit_number}/timeline` | 13.26 |
| Documents · required-docs · missing-photos | `asset_documents.py` | GET/POST `/api/asset-spine/assets/{asset_id}/documents(...)` | 13.31B D3/D4 |
| Asset transfers / assignments | `asset_transfers.py` | `/api/asset-transfers/*` | 15.79c |
| Work queue · readiness · alerts | `asset_care.py` | `/api/asset-care/*` | 13.33abc · 15.13a |
| Fleet defects · DVIR · OOS · dispatch status | `fleet_ops.py` | `/api/fleet/*`, `/api/dispatch/fleet/*`, `/api/shop/fleet/*` | 13.4a · 19.02 |
| PM engine · schedules · templates · work orders | `shop/PmWorkOrders.jsx` + PM engine | `/api/shop/pm/*` | 13.31 |
| Pre-Op / DVIR / Equipment Inspections | `safety_forms.py` + `fleet_ops.py` | `/api/fleet/inspections`, `/api/safety-forms/*` | 13.31b D5 · 19.11 · 19.12 |
| PPE / Phone / iPad issuance + return | `safety_forms.py` | `/api/safety-forms/equipment-issuances*` | 19.13 · 19.14 |
| Shop Asset Care · Manager Queue · My Assignments | `ShopAssetCare.jsx`, `ShopManagerQueue.jsx` | `/shop/*` | 13.30a-d · 15.13a |
| Fleet Unit Thread pilot (10-section shell) | `FleetUnitThread.jsx` | `/fleet/unit/:unit_number` | 19.55 |
| Universal Thread primitives | `components/operational_intelligence/*` | shared shell | 19.54 · 19.55 |

## What is missing (Track 19.61 extension scope)

1. Universal identifier resolver (any asset_ref → canonical asset_id).
2. Historical Records `entity_kind="asset"` lane (mirror of vendor lane).
3. One thread route that non-fleet portals (Safety, HR, Admin, PM) can
   deep-link to for **any** asset class.
4. Class-aware OI product routing (graceful fallback when no product
   maps to a class).

## What must NOT be built

- No new asset collection.
- No new equipment master.
- No duplicate maintenance system, DVIR system, or inspection system.
- No duplicate document store or photo store.
- No duplicate score model, no health % for assets, no legal-defensibility
  claim on inspection completeness.
- No new email workflow. **No live-send anything.** The audit itself
  MUST NOT send email.
- No duplicate Operational Intelligence product.
- No duplicate PDF renderer (reuse `asset_documents.py`'s renderer).

## Final call

**PROMOTE + EXTEND (small).** Ship Track 19.61 as the smallest correct
generalization of the Fleet Unit Thread pilot across the full canonical
asset taxonomy.

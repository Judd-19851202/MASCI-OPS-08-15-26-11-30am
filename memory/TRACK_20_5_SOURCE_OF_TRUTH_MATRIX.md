# TRACK 20.5 · Source of Truth Matrix — Asset / Equipment

**One owner per data category. If two owners exist, this document names
the defect. Nothing is fixed here — this is audit only.**

## Ownership doctrine

- **Asset Administrator (Admin)** owns identity, taxonomy, spec,
  ownership/rental, warranty, and retirement.
- **Shop** owns maintenance, defects, work orders, PM schedules,
  fuel/lube, and repair state.
- **Fleet / Dispatch** owns availability, location, DOT readiness, OOS
  decisions.
- **Safety** owns inspections, holds, incident links, and issued PPE /
  safety equipment lifecycle.
- **HR / Administration** owns legacy paper (historical records) and
  issuance sign-off documents.
- **Field / Superintendent** owns project assignment context (via
  daily reports + assignment records) — read-only in this thread.

**Consumer portals view but never author** outside their lane.

## Source-of-Truth table

| Category | Single owner | Certified surface | Notes |
|---|---|---|---|
| Asset ID | Admin (equipment_master) | `asset_spine` | Immutable canonical key |
| Unit number | Admin (equipment_master.unit_number) | `asset_spine`, timeline | Case-insensitive; sometimes = asset_id |
| Serial number | Admin (equipment_master.serial_number) | `asset_spine` | Used for phones/iPads/lasers |
| VIN | Admin (equipment_master.vin) | `asset_spine` | Trucks & trailers |
| Class · Type | Admin (via `services/asset_taxonomy.py`) | asset_spine profile | Taxonomy v1.0.0 |
| Category (legacy) | Admin (equipment_master.category) | asset_spine profile | Crosswalk to canonical class |
| Status (active/retired) | Admin | asset_spine (retire/activate) | State machine |
| Location · GPS | Fleet / Dispatch | fleet_ops + Motive telemetry | Not authored in thread |
| Assigned employee | Field / HR | daily_reports · asset_transfers | Read-only lens in thread |
| Assigned project | Field / HR | daily_reports · asset_transfers | Read-only lens |
| Assigned crew | Field | daily_reports | Read-only lens |
| Assigned department | Admin | equipment_master.department | asset_spine |
| Maintenance status | Shop | pm_engine · pm_work_orders · asset_care.readiness | Owned by Shop |
| Inspection status | Safety / Shop | equipment_inspections · fleet_ops (DVIR/preop) | Safety authors; Shop consumes |
| Defect status | Shop | fleet_ops (defects) | Shop authoritative |
| Hold status (OOS · safety · repair) | Dispatch (OOS) · Safety (safety hold) · Shop (repair hold) | fleet_ops · asset_care | Three-owner overlap is by design (three hold types) |
| Ownership · Rental · Vendor | Admin · Accounting | equipment_master + suppliers + po_requests | Cross-linked |
| Warranty | Admin | asset_documents (required_documents) | Doc-driven expiry |
| Documents (native) | Admin | `asset_documents` | Uploaded via asset admin |
| Documents (legacy paper) | HR / Admin | `employee_records` — **`entity_kind="asset"` lane TBD (19.61)** | Mirror of vendor lane (19.59) |
| Photos | Admin (via asset_documents `is_photo`) | asset_documents · missing-photos dashboard | One store |
| Incident links | Safety | incident engine (Track 19.16) → linked_asset_id | Safety authors |
| Issued-to history (PPE · phone · iPad) | Safety (issuance) | `safety_equipment_issuances` + return records | Safety authors; asset_spine references |
| Transfer history | Admin (transfers) | `asset_transfers` | State machine |
| Audit trail | Every writer | Per-collection audit fields (`updated_by`, `updated_at`, `event_source`) + `asset_service_events` timeline | Timeline is the fused view |

## Multi-owner overlaps — declared, NOT defects

- **Hold status** legitimately has three owners because there are three
  hold classes (OOS · safety hold · repair hold). Each hold has one
  owner. This is not a defect.
- **Assignment** appears in both `daily_reports` and `asset_transfers`.
  `asset_transfers` is authoritative for chain-of-custody; `daily_reports`
  is authoritative for who used it that day. Different questions, not a
  defect.

## Declared defects — NOT to be fixed in 20.5

- **D-01 · Legacy paper for assets has no lane.** Historical Records
  intake (Track 19.21b) supports `entity_kind="employee"` and (from
  19.59) `entity_kind="vendor"`, but not `entity_kind="asset"`. Assets'
  legacy paper is currently forced into `asset_documents` (fine for
  born-digital) or nowhere at all. **Track 19.61 shall add
  `entity_kind="asset"`.** Zero backend duplication risk — same
  `employee_records` collection, one more discriminator.
- **D-02 · No universal identifier resolver.** Callers must pre-know
  whether their identifier is a `unit_number`, an `asset_id`, a `serial`,
  or a legacy `equipment_number`. A single resolver (`GET
  /api/asset-spine/resolve?ref=…` OR client helper) would remove that
  guesswork. **Track 19.61 scope.**
- **D-03 · OI product hard-coded to `fleet_intelligence`.** The Fleet
  Unit Thread pilot hard-codes `fleet_intelligence`. For non-fleet
  classes (phones, PPE, survey), the correct behavior is either the
  matching existing product or a graceful "no OI product yet" card.
  **Track 19.61 scope — no new OI products.**

## Non-defects (falsely reported by prior audits)

- No duplicate asset collection. `equipment_master` is single.
- No duplicate timeline. `asset_service_events` is the fused view — all
  other tables are projected in.
- No duplicate document store. `asset_documents` for native + legacy
  paper lane on `employee_records` (once 19.61 lands).
- No duplicate PM system. `pm_engine` is single.

**Verdict:** Data ownership is clean. Three small extensions (D-01 · D-02 ·
D-03) are the only Track 19.61 backend touch-points.

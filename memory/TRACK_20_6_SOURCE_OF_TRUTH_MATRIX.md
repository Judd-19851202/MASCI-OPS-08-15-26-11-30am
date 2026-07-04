# TRACK 20.6 · Source of Truth Matrix — Fire Protection

**One owner per data category. Every duplicate declared. Nothing fixed
here — this is audit only.**

## Ownership doctrine (proposed for Phase A)

- **Safety** owns inspection lifecycle, next-due dates, pass/fail
  status, corrective action linkage, and digest overdue count.
- **Admin (Asset Administrator)** owns the canonical asset record —
  once Phase B lands and fire extinguishers migrate to `equipment_master`.
- **HR / Admin** owns legacy paper (historical records) via
  `entity_kind="asset"` lane.
- **Fleet / Shop / Field / Dispatch** consume only. They see the
  extinguisher status on the parent-asset thread (a truck's Asset
  Thread shows its mounted extinguisher's next-due) but do not author.

**Current state:** Safety is the *sole* owner of identity AND
inspection — a temporary condition that Phase B corrects.

## Source-of-Truth table

| Category | Current owner | Certified surface | Phase A verdict | Phase B verdict |
|---|---|---|---|---|
| Unit ID (fire-ext label) | Safety (`db.fire_extinguishers.unit_id`) | POST/PATCH `/api/safety/fire-extinguishers` | KEEP as-is | migrate → `equipment_master.unit_number` |
| Location kind (vehicle / trailer / office / …) | Safety (`location_kind`) | Same | KEEP | migrate → `equipment_master.location` |
| Location value (specific truck # / office name) | Safety (`location_value`) | Same | KEEP | migrate → `equipment_master.location` |
| Type (ABC / CO2 / Class D / K / etc.) | Safety (`type`, free-string) | Same | KEEP · tighten via enum aligned with taxonomy | migrate → `equipment_master.asset_type` |
| Size | Safety (`size`) | Same | KEEP | migrate → `equipment_master.spec.size` |
| Serial number | Not currently a first-class field | (implied via `unit_id` in many yards) | Phase A: add `serial_number` field on the register (additive) | migrate → `equipment_master.serial_number` |
| Manufacturer | Not currently tracked | (n/a) | Deferred to Phase B | migrate → `equipment_master.manufacturer` |
| Manufacture date | Not currently tracked | (n/a) | Deferred to Phase B | migrate → `equipment_master.metadata` |
| Last inspection date | Safety (`last_inspection_date`) | POST `/inspect` | KEEP · surface on Asset Thread (Phase A read-side) | migrate → `asset_service_events` (kind=`inspection`) |
| Next-due date | Safety (`next_due_date`) | POST `/inspect` | KEEP · surface on Asset Thread Attention section | migrate → derived from `asset_service_events` |
| Pass/fail status | Safety (`last_status`) | POST `/inspect` | KEEP · surface on Asset Thread health | migrate → derived |
| Inspection log (history) | Safety (nested inside `db.fire_extinguishers`) | GET `.../history.pdf` | KEEP | migrate → `asset_service_events` |
| Recharge history | Not currently first-class (implied in inspection log · attachments) | attachments store | Phase A: add `entity_kind="asset"` record_type `recharge_service_record` | migrate → `asset_service_events` (kind=`repair`) |
| Hydrostatic testing history | Not currently first-class | attachments store | Phase A: add record_type `hydrostatic_test_certificate` | migrate → `asset_service_events` |
| Retirement / replacement history | Not currently first-class | (implied via DELETE / re-create) | Phase A: add record_type `fire_ext_retirement_record` | migrate → asset lifecycle state machine |
| Photos | Attachments on `db.fire_extinguishers` | GET/POST `/attachments` | KEEP | migrate → `asset_documents.is_photo=true` |
| Documents (native) | Attachments | GET/POST `/attachments` | KEEP | migrate → `asset_documents` |
| Documents (legacy paper) | HR / Admin — Historical Records asset lane (Track 19.61) | GET `/api/employee-records/records?entity_kind=asset` | **EXTEND** — add fire-specific record_type slugs (Phase A) | continue |
| Assignment (which asset owns this ext) | Safety (`equipment_master_id`, iter138 half-binding) | field on `db.fire_extinguishers` | KEEP · surface as relationship on Asset Thread | migrate → transfer/assignment via spine |
| Assignment (which project) | Not currently tracked | (n/a) | Deferred | migrate → same as any asset |
| Vendor / purchase record | Not currently first-class | (implied via CA link) | Phase A: add record_type `fire_ext_manufacturer_doc` on asset lane | migrate → PO link on `equipment_master` |
| Incident linkage | Safety (via CA link type `fire_ext`) | corrective actions collection | KEEP | continue |
| Operational readiness signal | Safety (`fire_ext.fail` operational signal) | `db.operational_signals` | KEEP | continue |
| Audit trail | Per-collection audit fields | `db.fire_extinguishers` + notifications | KEEP | migrate → asset audit spine |

## Duplicates declared (Track 20.6 findings)

- **D-FP-01 · Duplicate asset registry.** `db.fire_extinguishers` is a
  parallel asset identity system to `equipment_master`. Phase A tolerates
  it (with a read-side adapter). Phase B retires the duplicate through
  data migration + backwards-compat view.
- **D-FP-02 · Duplicate inspection log.** Extinguisher inspections live
  in `db.fire_extinguishers` (last / next / status) instead of on
  `asset_service_events`. Phase A tolerates; Phase B projects them onto
  the backbone.
- **D-FP-03 · Duplicate attachment store.** Extinguisher attachments
  live under `/safety/fire-extinguishers/{id}/attachments/*`, parallel
  to `asset_documents`. Phase A tolerates; Phase B consolidates.
- **D-FP-04 · Fire Protection absent from canonical taxonomy.**
  `services/asset_taxonomy.py` v1.0.0 has no Fire Protection class.
  Phase A adds it (additive · v1.1.0).

## Non-duplicates (falsely reported by casual observers)

- CA link type `fire_ext` is a **link semantic**, not a duplicate
  identity store. Not a defect.
- The `fire_extinguishers` line in `lib/inspectionSchema.js` is a
  checkbox on DVIR/Pre-Op inspections ("fire extinguisher present,
  charged, accessible"). Complementary, not a duplicate.
- The digest KPI `fire_extinguishers_overdue` is a consumer-side
  counter. Continues to work in both phases.

**Verdict:** Ownership is clear once Phase A / Phase B execute. Phase A
alone eliminates zero duplicates but unblocks the Asset Thread. Phase B
eliminates D-FP-01, D-FP-02, D-FP-03. Phase A ships D-FP-04 fix
(taxonomy extension).

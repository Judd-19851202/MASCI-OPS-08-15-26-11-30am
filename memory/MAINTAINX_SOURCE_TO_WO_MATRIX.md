# MAINTAINX · SOURCE-TO-WORKORDER MATRIX  (Phase 2)

**Date:** 2026-06-04 19:10 UTC
**Directive:** OMEGA — MaintainX Equipment Defect Pipeline Audit & Integration Plan
**Mode:** READ-ONLY PLANNING (no writes, no MaintainX traffic)

This matrix defines, for every defect-originating surface in ForgedOps, whether the event MUST create a MaintainX Work Order, whether a Return-to-Service gate is required, and how the source plugs into the canonical defect payload.

---

## 1 · Master matrix

| # | Source | Equipment Type | Trigger (event that fires) | MaintainX WO Required? | RTS Required? | Source collection (canonical) | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Truck DVIR defect — OOS | Tractor / Trailer-pulling truck | `POST /api/dispatch/fleet/inspections` produces a defect with `severity=oos` OR `out_of_service=Yes` | **P0** | YES — must be cleared by Dispatch AFTER MaintainX WO is closed | `fleet_defects` | One WO per defect row; consolidate same-inspection same-unit rows into one WO with multiple work_items (see canonical mapping in Phase 4) |
| 2 | Truck DVIR defect — Monitor | Tractor / Trailer-pulling truck | DVIR submission with `severity=monitor` only (no OOS) | **P1** | NO — monitor defects do not block dispatch | `fleet_defects` | Should still surface to MaintainX so the shop can schedule; not gate-critical |
| 3 | Trailer DVIR defect | Trailer (van / lowboy / belly dump / pup) | Same as #1 but `trailer_unit_number` is the asset, not the truck | **P0 (OOS) · P1 (monitor)** | YES (only when OOS and the trailer is the moved unit) | `fleet_defects` | MaintainX `assetId` resolution must use trailer's `asset_mappings.maintainx.asset_id`, not the truck's |
| 4 | Service truck issue | Service Truck (mobile shop) | Same DVIR route (`kind=pre_op` for service truck pre-op) | **P0 (OOS) · P1 (monitor)** | YES (OOS) | `fleet_defects` | Same payload shape as #1 |
| 5 | Pickup issue | Pickup / 1-ton support truck | Same DVIR route | **P0 (OOS) · P1 (monitor)** | YES (OOS) | `fleet_defects` | Same payload shape as #1 |
| 6 | Heavy Equipment Pre-Op defect (generic) | any heavy iron | `POST /api/equipment-inspections` with `fail_count > 0` | **P0 (OOS) · P1 (monitor)** | YES (OOS) | `equipment_inspections` + derivative `asset_holds` row | Severity derived from `MAJOR_OOS_SET` in `routes/equipment.py:139` |
| 7 | Dozer Pre-Op defect | Dozer | same as #6 | **P0 (OOS) · P1** | YES (OOS) | same as #6 | `equipment_type=Dozer` |
| 8 | Excavator Pre-Op defect | Excavator | same as #6 | **P0 (OOS) · P1** | YES (OOS) | same as #6 | `equipment_type=Excavator` |
| 9 | Loader Pre-Op defect | Wheel / Track Loader | same as #6 | **P0 (OOS) · P1** | YES (OOS) | same as #6 | `equipment_type=Loader` |
| 10 | Grader / Blade Pre-Op defect | Motor Grader | same as #6 | **P0 (OOS) · P1** | YES (OOS) | same as #6 | `equipment_type=Grader|Blade` |
| 11 | Roller Pre-Op defect | Compactor / Roller | same as #6 | **P0 (OOS) · P1** | YES (OOS) | same as #6 | `equipment_type=Roller` |
| 12 | Paver / Mill Pre-Op defect | Asphalt Paver / Mill | same as #6 | **P0 (OOS) · P1** | YES (OOS) | same as #6 | `equipment_type=Paver|Mill` |
| 13 | Broom / Skid-steer Pre-Op defect | Broom / Skid-steer / smaller iron | same as #6 | **P0 (OOS) · P1** | YES (OOS) | same as #6 | `equipment_type=Broom|SkidSteer|…` |
| 14 | Equipment Inspection defect (admin/shop-driven scheduled inspection) | any | `POST /api/admin/equipment-inspections/{id}/signoff` flagging new defects, or non-pre-op inspections in `equipment_inspections` collection | **P1** | depends on severity | `equipment_inspections` | De-dupe vs. source pre-op |
| 15 | Shop-found repair issue (fleet side) | truck / trailer | `POST /api/dispatch/fleet/units/{unit}/oos` initiated by shop-or-admin | **P0** | YES | `fleet_defects` (`inspection_kind="manual_oos"`) | The current synthetic `fleet_defects` row IS the source — fan-out should fire on this path |
| 16 | Shop-found repair issue (heavy equipment side) | heavy iron | `POST /api/admin/operations/holds` initiated by shop/admin | **P0** | YES | `asset_holds` | Same fan-out path as #6 |
| 17 | Dispatch breakdown event | truck / trailer / heavy iron driven away from the yard | `POST /api/dispatch/fleet/units/{unit}/oos` initiated by dispatch | **P0** | YES | `fleet_defects` | `reported_by_name = dispatcher` |
| 18 | Manual maintenance request | any | `POST /api/admin/operations/holds` initiated by admin with no upstream form | **P0** | YES | `asset_holds` | Admin-originated WO; lowest auto-creation risk |

### Classification key
- **P0** = MaintainX WO **MUST** be created (or proven duplicate of an open WO for the same defect)
- **P1** = MaintainX WO **SHOULD** be created (defer when MaintainX is unavailable; ForgedOps continues to function on its own)
- **P2** = optional / visibility only — none assigned in this matrix; reserved for future low-signal channels
- **NO** = explicitly do **not** create a WO (Safety corrective actions, Field-Leadership references, RTS itself)

---

## 2 · NON-creators (explicit "NO")

| Source | Why no MaintainX WO |
| --- | --- |
| Fleet RTS (`/clear`) | It is the consuming side — closes after MaintainX WO is done. |
| Safety Portal corrective action | Overlay on an already-existing defect; do not double-create. |
| Field Leadership equipment reference | Observational; no defect originated here. |
| Equipment Inspection sign-off with **no new defects** | No new defect → nothing to push. |
| Notification fan-out / Shop task | Internal-only echo of a defect; the original defect is the canonical source. |

---

## 3 · One-WO-per-defect-group rule

Multiple defect lines that share `(source_record_id, equipment_id)` SHOULD be consolidated into **a single MaintainX WO** with multiple `workItems` (or one description containing a bulleted list of failed items). This:

- Matches operator mental model ("this DVIR found 4 things wrong with TRK-12")
- Prevents 4 duplicate WOs from one inspection
- Keeps RTS gate logic simple — one WO closes, one defect group clears

Exception: heavy equipment Pre-Op where each failed checklist item maps to a distinct safety topic (per `MAJOR_OOS_SET`) — consolidation rule still holds at the same `(source_record_id, equipment_id)` key.

---

## 4 · Equipment-type → `assetId` resolution path

Every WO push must first resolve the MaintainX `assetId` via `db.asset_mappings.maintainx.asset_id` keyed by `masci_equipment_id`. If resolution fails:

| Outcome | Behaviour (planned, not built) |
| --- | --- |
| Mapping exists | Use it; proceed |
| Mapping missing | Enqueue into `maintainx_sync_pending` with status `unmapped_asset`; alert admin via Integration Center; **DO NOT** auto-create the WO under a synthetic asset |
| Mapping ambiguous (multiple) | Enqueue into pending with status `ambiguous_asset`; admin resolves via Mappings Wizard; **DO NOT** auto-create |

This is enforced by the canonical defect payload (Phase 3) which carries `maintainx_asset_id` as a required pre-flight check before any write would be authorised.

---

## 5 · RTS gating summary

| Source group | RTS gated by MaintainX WO closure? |
| --- | --- |
| Fleet DVIR OOS, Trailer OOS, Service Truck OOS, Pickup OOS, Manual OOS flip | **YES** — Dispatch `/clear` MUST refuse to close unless linked WO is Done/Completed/Cancelled OR override is captured with operator name + reason |
| Heavy Equipment Pre-Op OOS, Manual maintenance hold | **YES** — `POST /api/admin/operations/holds/{id}/release` MUST refuse until linked WO is closed |
| Monitor / non-OOS | NO RTS gate — these are visibility WOs, not blocking |

— End of Phase 2 matrix —

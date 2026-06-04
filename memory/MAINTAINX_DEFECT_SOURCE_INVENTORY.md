# MAINTAINX · DEFECT SOURCE INVENTORY  (Phase 1)

**Date:** 2026-06-04 19:10 UTC
**Directive:** OMEGA — MaintainX Equipment Defect Pipeline Audit & Integration Plan
**Mode:** READ-ONLY (no writes, no deploys, no MaintainX traffic)

This inventory walks every workflow that can identify an equipment defect inside ForgedOps and documents — for each — the exact path, route, collection, identifier fields, severity flags, attachment support, current close/RTS behaviour, and whether the workflow should fan out to MaintainX.

---

## 1 · Source: Fleet DVIR (Trucks · Trailers · Service Trucks · Pickups)

| Field | Value |
| --- | --- |
| File path | `backend/routes/fleet_ops.py` |
| Backend route | `POST /api/dispatch/fleet/inspections` (driver submit) · `POST /api/dispatch/fleet/units/{unit}/oos` (manual OOS) · `POST /api/dispatch/fleet/defects/{id}/{acknowledge|repair|clear}` (lifecycle) |
| DB collection (header) | `db.equipment_inspections` (with `kind in {pre_op, weekly_lead, weekly_emergency, dvir}`) |
| DB collection (defects) | `db.fleet_defects` |
| Equipment identifier field | `truck_unit_number` · `trailer_unit_number` · `truck_vin` · `truck_plate` |
| Unit number field | `truck_unit_number` / `trailer_unit_number` |
| Defect / problem field | `item_text` + `category` (from `lib/fleet_defect_severity`) |
| Severity field | `severity ∈ {"oos","monitor"}` (SEVERITY_TABLE_VERSION v1.3-approved-2026-05-19) |
| Out-of-service flag | `out_of_service=Yes` on the header AND `severity==oos` on the defect row |
| Photo/attachment support | YES — `photos: List[str]` (R2 keys); `repair_photos[]` on close |
| Current close / repair / RTS behaviour | Shop acknowledges → repairs (`repaired`) → Dispatch clears via `/clear` endpoint (`cleared` = RTS). Internal-only today. |
| Should create MaintainX WO? | **YES — P0** (every OOS or `severity==oos` defect; every manual OOS flip with `kind=manual_oos`) |
| Already wired to MaintainX? | NO. The schema already exposes the field `external_refs.maintainx_work_order_id` (always `null`). |

---

## 2 · Source: Fleet RTS (Return-to-Service)

| Field | Value |
| --- | --- |
| File path | `backend/routes/fleet_ops.py:840-916` |
| Backend route | `POST /api/dispatch/fleet/defects/{defect_id}/clear` |
| DB collection | mutates `db.fleet_defects.status: cleared → cleared_at, cleared_by_name`; audit row `rts_label="returned_to_service"` |
| Equipment identifier field | inherited from `fleet_defects` |
| Severity field | n/a (RTS closes any open defect regardless of severity) |
| Photo/attachment support | YES (carried over from the defect) |
| Current close / repair / RTS behaviour | Marks the defect cleared + rebuilds `db.fleet_unit_status` for the touched unit |
| Should create MaintainX WO? | **NO** — RTS is the consuming side. It should be **gated** by MaintainX WO closure (special focus #3). |
| Already wired to MaintainX? | NO (no callback to MaintainX). |

---

## 3 · Source: Heavy-Equipment Pre-Op (Dozer / Excavator / Loader / Grader / Roller / Paver / Mill / Broom / Skid Steer / etc.)

| Field | Value |
| --- | --- |
| File path | `backend/routes/equipment.py` (`POST /api/equipment-inspections`) |
| Backend route | `POST /api/equipment-inspections` (public, rate-limited) |
| DB collection | `db.equipment_inspections` (`kind` is absent for this legacy shape → effectively `kind=pre_op` for heavy equipment) |
| Equipment identifier field | `equipment_unit`, `equipment_make`, `equipment_model`, `equipment_serial` |
| Unit number field | `equipment_unit` |
| Defect / problem field | `checklist[section][item].status == "fail"` plus optional `deficiency_notes` |
| Severity field | derived: items in `MAJOR_OOS_SET` raise the severity to **`oos`**, else `attn` (monitor). `fail_count` aggregates. |
| Out-of-service flag | `out_of_service` ∈ {"Yes","No"} on the header |
| Photo/attachment support | YES — `photos: List[str]` (R2 keys) |
| Current close / repair / RTS behaviour | Failed pre-op → `routes/operations.create_pending_maintenance_hold(...)` (creates `db.asset_holds`) + `lib/event_fanout.emit_task_and_notification(...)` (Shop task + Dispatch notification). No internal "repaired" lifecycle row — closure of the corresponding `asset_hold` IS the RTS. |
| Should create MaintainX WO? | **YES — P0** for OOS-class fails (>= 1 item in MAJOR_OOS_SET OR `out_of_service=Yes`). **P1** for non-OOS fails (attention/monitor). |
| Already wired to MaintainX? | NO. The fan-out comment block at `equipment.py:230-299` is internal only. |

---

## 4 · Source: Equipment Inspection (any non-pre-op equipment inspection form)

| Field | Value |
| --- | --- |
| File path | `backend/routes/equipment.py:303-...` + admin trends/sign-off routes |
| Backend route | Reads only: `GET /api/equipment-inspections`, `GET /api/admin/equipment-inspections/trends`, `…/open-items`, sign-off endpoints |
| DB collection | shared `db.equipment_inspections` (any `kind`) |
| Equipment identifier / unit fields | same as Pre-Op (§3) |
| Defect / problem field | same — checklist failures |
| Severity field | same |
| OOS flag | same |
| Photo/attachment support | YES |
| Current close / repair / RTS behaviour | Admin/shop sign-off via `POST /api/admin/equipment-inspections/{id}/signoff`. No internal MaintainX call. |
| Should create MaintainX WO? | **P1** — derivative of the Pre-Op stream; mostly the same defects with a later observer. Avoid double-creating WOs already opened from the originating Pre-Op (de-dupe by `source_record_id` of the originating inspection — see Phase 8). |
| Already wired to MaintainX? | NO. |

---

## 5 · Source: Shop-Discovered Issues

| Field | Value |
| --- | --- |
| File path | (a) `POST /api/dispatch/fleet/units/{unit}/oos` in `routes/fleet_ops.py:918` (Shop side currently uses Dispatch's manual OOS) · (b) `lib/event_fanout` `pending_maintenance_holds` for non-fleet (heavy equipment) created via `routes/operations.create_pending_maintenance_hold(...)` |
| Backend route | Manual OOS endpoint (shop-or-admin) · or Admin-initiated hold via `POST /api/admin/operations/holds` (`routes/operations.py`) |
| DB collection | `db.fleet_defects` (fleet side) or `db.asset_holds` (non-fleet equipment side) |
| Equipment identifier field | `unit_number` / `asset_id` |
| Defect / problem field | free-text `item_text` / `reason` |
| Severity field | inferred (`severity="oos"` for manual OOS) |
| OOS flag | `severity=oos` or `active=True` on the hold |
| Photo/attachment support | YES on fleet side (`photos[]`); partial on hold side |
| Current close / repair / RTS behaviour | mirror of §1 (fleet) or §3 (heavy equipment) |
| Should create MaintainX WO? | **YES — P0** for OOS, **P1** for monitor — but emitted ONLY when a shop-or-admin originates the row (de-dupe vs. driver-submitted DVIR / Pre-Op). |
| Already wired to MaintainX? | NO. |

---

## 6 · Source: Dispatch Equipment Issue / Breakdown

| Field | Value |
| --- | --- |
| File path | `backend/routes/fleet_ops.py` (manual OOS at line 918) · `backend/routes/dispatch_continuity.py` (continuity notes can mention breakdowns but do not create defect rows) |
| Backend route | `POST /api/dispatch/fleet/units/{unit}/oos` (the manual OOS we already covered) |
| DB collection | `db.fleet_defects` |
| Severity field | always `severity=oos` (manual flip is always OOS by intent) |
| Photo/attachment support | YES — `photos[]` accepted on payload |
| Current close / repair / RTS behaviour | flows back through Shop → Dispatch RTS clear |
| Should create MaintainX WO? | **YES — P0** (an OOS flip by Dispatch is by definition an actionable maintenance event) |
| Already wired to MaintainX? | NO. `external_refs.maintainx_work_order_id` field exists, value always `null`. |

---

## 7 · Source: Field Leadership Equipment References

| Field | Value |
| --- | --- |
| File path | `backend/routes/field_leadership.py` (read-only references; no defect creation) |
| Backend route | various read endpoints (asset lookup, where-used) |
| DB collection | reads `db.equipment_master` only |
| Defect/severity/OOS fields | none — this surface does not originate defects |
| Should create MaintainX WO? | **NO.** Field Leadership references are observational. |

---

## 8 · Source: Safety Portal Equipment-Issue Workflows

| Field | Value |
| --- | --- |
| File path | `backend/routes/safety_portal/corrective_actions.py` |
| Backend route | corrective-action issuance against any source row (sometimes equipment-linked) |
| DB collection | `db.safety_corrective_actions` (referenced) |
| Equipment identifier | not always present — corrective actions can be employee-focused or document-focused |
| Defect/severity/OOS fields | inherited from the source the corrective action references (a referenced fleet defect or pre-op fail) |
| Photo/attachment support | YES |
| Current close behaviour | Safety team closure |
| Should create MaintainX WO? | **NO direct hook.** The source row (DVIR/Pre-Op/Shop OOS) is the canonical defect source — corrective actions are a Safety-portal overlay. Avoid double-creating WOs. |
| Already wired to MaintainX? | NO. |

---

## 9 · Source: Manual Maintenance Request (already present?)

| Field | Value |
| --- | --- |
| File path | `backend/routes/operations.py:289-340` — `create_pending_maintenance_hold(db, ...)` exposed via `POST /api/admin/operations/holds` (admin/shop) |
| Backend route | `POST /api/admin/operations/holds` |
| DB collection | `db.asset_holds` (kind in `pending_maintenance`, `oos_hold`, `pre_op_failed`, etc.) |
| Equipment identifier | `asset_id` (UUID into `equipment_master`) |
| Defect / problem field | `reason` (free text) |
| Severity field | `severity ∈ low|medium|high` (callers default to medium/high) |
| OOS flag | implicit (hold blocks dispatch use of the asset) |
| Photo/attachment support | PARTIAL — has a `notes` field but no first-class `photos[]` collector |
| Current close / repair / RTS behaviour | `POST /api/admin/operations/holds/{id}/release` — closes the hold (the RTS surface for non-fleet equipment) |
| Should create MaintainX WO? | **YES — P0** for shop/admin originated holds; **P1** for system-generated mirror holds (already linked to a Pre-Op or DVIR) — de-dupe. |
| Already wired to MaintainX? | NO. |

---

## 10 · Summary table of canonical collections involved

| Collection | What it stores | Touched by which source |
| --- | --- | --- |
| `db.equipment_master` | The asset registry (truck/trailer/heavy equipment) | All sources resolve to this via `unit_number → id` |
| `db.equipment_inspections` | Both Pre-Op (heavy equipment) AND Fleet DVIR (when `kind` is present) inspection headers | §1 §3 §4 |
| `db.fleet_defects` | Per-item DVIR defects + manual OOS | §1 §5 (fleet) §6 |
| `db.asset_holds` | Non-fleet (heavy equipment) maintenance holds | §3 §5 (non-fleet) §9 |
| `db.tasks` + `db.notifications` (`lib/event_fanout`) | Internal Shop/Dispatch fan-out | §1 §3 §5 §6 |
| `db.maintainx_dryrun_reports` | NEW · read-first audit collection | none yet (P0 read-only) |
| `db.fleet_unit_status` | Per-unit live OOS/Available/Pending status | §1 §6 (recomputed via `_rebuild_status`) |

---

## 11 · Coverage gap (vs. canonical Equipment Health pipeline)

The current MaintainX P0-A/P0-B read-first sprint covers:

- ✅ Asset registry mirroring (read)
- ❌ Defect ingest from any source
- ❌ WO creation from any source
- ❌ RTS gate against MaintainX WO closure

DVIR is **not** the only stream. Heavy Equipment Pre-Op (`equipment.py:177`) is structurally separate AND structurally identical in shape (fail_count + checklist + photos), and currently fans out only to `asset_holds` + `tasks` + `notifications` — no MaintainX call.

Every source above must converge on a single **canonical defect payload** (Phase 3) before any WO push is built, to ensure de-duplication and uniform field mapping.

— End of Phase 1 inventory —

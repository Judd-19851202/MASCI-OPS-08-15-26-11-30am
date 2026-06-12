# Track 13.26A — Asset Event Source Certification (PHASE 1)

**Date:** 2026-06-12
**Mode:** SOURCE-TRUTH CERTIFICATION ONLY · READ-ONLY · zero code · zero schema
**Implementation:** NONE (Phase 1)
**Doctrine alignment:** TRACK_13_18 (Material Ledger architecture), TRACK_13_19 (Phase A derived-projection pattern), TRACK_13_24 (Defect lifecycle certification), TRACK_13_25 (Asset Care architecture).
**Verdict:** ✅ Certification gate passed. Backbone CAN be derived from existing collections. **No new persistent collection required for Phase 13.26.**

---

## 1 · TL;DR

The MASCI codebase already emits **every event MASCI OPS actually performs today** into one of six canonical collections. Nothing about asset service history is invented; nothing must be invented to surface it.

| Family               | Real today | Source                                                  | Persistence | Notes                                           |
| -------------------- | ---------- | ------------------------------------------------------- | ----------- | ----------------------------------------------- |
| Pre-Op               | ✅          | `equipment_inspections`                                  | persisted   | Operator-authored                                |
| DVIR                 | ✅          | `equipment_inspections` (`kind="dvir"`)                  | persisted   | Driver-authored                                 |
| Defect lifecycle     | ✅          | `fleet_defects` + `fleet_audit`                          | persisted   | open · acknowledged · repaired · cleared        |
| OOS / RTS             | ✅          | derived from `fleet_defects.status` + `_audit` rows      | derived     | RTS = `cleared` = Dispatch verification         |
| Asset transfers       | ✅          | `asset_transfers` + `admin_audit_log` + `equipment_master` | persisted   | TRANSFER · RETIRE · ACTIVATE                     |
| Material movement     | ✅          | `haul_cycles` (+ `dispatch_assignments`, `operational_attachments`) | persisted | Already projected via `/api/dispatch/haul-ledger` |
| Motive presence       | ✅          | `operational_events` (M-2 Event Router)                  | persisted   | Geofence-derived arrivals / departures           |
| Incidents             | ✅          | `incidents`                                              | persisted   | Safety-routed                                    |
| **Mechanic identity** | ❌          | —                                                       | —            | Field absent on `fleet_defects`; no collection   |
| **PM**                | ❌          | —                                                       | —            | No `service_interval`, no `pm_schedules`         |
| **Fuel / DEF / Lube / Grease** | ❌  | —                                                       | —            | No `fuel_service_visits`, no service-truck doc   |
| **MaintainX**         | ⚠️ STUBBED  | `services/maintainx_client.py`                          | env-gated   | `MAINTAINX_API_KEY` absent in preview; SDK ready |

The defect-lifecycle backbone is **fully audited**. Per-unit aggregation is the only architectural gap.

---

## 2 · Event Source Certification Table

Authoritative grep evidence (all paths relative to `/app/backend/`):

| Event                                | Exists | Source Collection         | Endpoint(s)                                                                | UI Source                                  | Actor                       | Auditable | Notes                                                                  |
| ------------------------------------ | ------ | ------------------------- | -------------------------------------------------------------------------- | ------------------------------------------ | --------------------------- | --------- | ---------------------------------------------------------------------- |
| **Pre-Op submitted**                 | ✅      | `equipment_inspections`   | `POST /api/equipment-inspections` (`routes/equipment.py:181-187`)          | `EquipmentDashboard`, `ViewEquipmentInspection` | Operator                | ✅         | `kind="pre_op"`; carries `equipment_unit`                              |
| **Pre-Op failed**                     | ✅      | `equipment_inspections`   | derived from `fail_count > 0`                                              | same                                       | Operator                    | ✅         | Triggers `create_pending_maintenance_hold`                             |
| **Pre-Op defect reported**           | ✅      | `fleet_defects`           | derived during submit (`routes/equipment.py:240`)                          | Shop queue / dashboard                     | Operator → Shop             | ✅         | `kind="preop"` row on fleet_defects                                    |
| **Pre-Op defect corrected**          | ✅      | `fleet_defects`           | `POST /api/shop/fleet/defects/{id}/repair` (`routes/fleet_ops.py:828-871`) | ShopHubV2                                  | Shop                        | ✅         | status: `acknowledged → repaired`                                      |
| **DVIR submitted**                    | ✅      | `equipment_inspections`   | `POST /api/fleet/inspections` (`routes/fleet_ops.py:515`)                  | Public DVIR tile                           | Driver                      | ✅         | `kind="dvir"`                                                          |
| **DVIR defect reported**              | ✅      | `fleet_defects`           | `insert_many` during submit (`routes/fleet_ops.py:521`)                    | Shop queue                                 | Driver → Shop               | ✅         | `kind="dvir"` row on fleet_defects                                     |
| **DVIR defect corrected**             | ✅      | `fleet_defects`           | `/api/shop/fleet/defects/{id}/repair`                                      | ShopHubV2                                  | Shop                        | ✅         | shared transition                                                       |
| **Defect opened**                     | ✅      | `fleet_defects`           | inserts above + `routes/fleet_ops.py:955` (manual_oos)                     | Shop queue                                 | Operator / Driver / Dispatch | ✅         | status=`open`, severity table at `fleet_defect_severity.py`            |
| **Defect escalated**                  | ⚠️ partial | `fleet_audit`           | `_audit` rows (`routes/fleet_ops.py:283`)                                  | none yet                                   | system                      | ✅         | Severity is set at creation; no manual escalation endpoint              |
| **Defect acknowledged**               | ✅      | `fleet_defects`           | `POST /api/shop/fleet/defects/{id}/acknowledge` (`routes/fleet_ops.py:792-826`) | ShopHubV2                              | Shop                        | ✅         | status: `open → acknowledged`                                          |
| **Defect repaired**                   | ✅      | `fleet_defects`           | `POST /api/shop/fleet/defects/{id}/repair` (`routes/fleet_ops.py:828-871`) | ShopHubV2                                  | Shop                        | ✅         | status: `acknowledged → repaired`; captures `repair_notes`, `repair_photos` |
| **Defect reviewed (shop manager)**    | ⚠️ partial | `fleet_defects.acknowledged_by_name` | implicit via token                                               | none                                       | Shop role-token             | ✅         | Per-mechanic identity not captured (Track 13.28 gap)                    |
| **Defect closed / RTS verified**      | ✅      | `fleet_defects`           | `POST /api/dispatch/fleet/defects/{id}/clear` (`routes/fleet_ops.py:873-916`) | ShopHubV2 / DCC                          | Dispatch + Admin            | ✅         | status: `repaired → cleared`; emits `rts_label=returned_to_service` payload |
| **Unit OOS**                          | ✅      | `fleet_defects` (`severity=oos`) + `fleet_status` | `POST /api/dispatch/fleet/units/{unit}/oos` (`routes/fleet_ops.py:918-963`) | Dispatch / Shop                        | Dispatch / Shop             | ✅         | Manual OOS flip creates synthetic defect                                |
| **Unit returned (RTS)**               | ✅      | `fleet_defects.cleared_at` | same `/clear` endpoint                                                     | Dispatch / Shop                            | Dispatch + Admin            | ✅         | Hard lock: Shop repair ≠ RTS                                            |
| **Dispatch unavailable / available**  | ✅      | `dispatch_assignments` + `fleet_status` | dispatch_lifecycle endpoints                                       | Dispatch                                   | Dispatch                    | ✅         | Status flips audit-logged                                                |
| **Shop note added**                   | ⚠️ partial | `fleet_defects.repair_notes` | repair endpoint                                                       | ShopHubV2                                  | Shop                        | ✅         | Free-text only; no separate "note" event                                 |
| **Attachment uploaded (dispatch)**     | ✅      | `operational_attachments` | `POST /api/operational/attachments/upload` (`routes/operational_attachments.py:369`) | Dispatch / DriverHub                | Dispatch / Driver           | ✅         | `host_kind="assignment"` (only host today)                              |
| **Attachment uploaded (defect)**       | ⚠️ partial | `fleet_defects.repair_photos` | repair endpoint                                                     | ShopHubV2                                  | Shop                        | ✅         | Stored inline on defect; NOT yet in `operational_attachments`            |
| **Inspection completed (shop sign-off)** | ✅    | `equipment_inspections.shop_signed_off_at` | `routes/equipment.py:516,531`                                    | ShopHubV2                                  | Shop                        | ✅         | Pre-Op shop sign-off                                                    |
| **Asset added**                        | ✅      | `equipment_master`        | `services/asset_spine.py:427`                                              | Admin                                      | Admin                       | ✅         | `admin_audit_log` action=`ASSET_CREATE`                                  |
| **Asset retired**                      | ✅      | `equipment_master` + `asset_transfers` (type=RETIRE) | `services/asset_spine.py:496-550`                              | Admin                                      | Admin                       | ✅         | `admin_audit_log` action=`ASSET_RETIRE`                                  |
| **Asset reassigned (transfer)**         | ✅      | `asset_transfers`         | `routes/asset_transfers.py:417,449,542`                                    | Admin                                      | Admin / Dispatch            | ✅         | type=`TRANSFER`                                                          |
| **Haul cycle completed**               | ✅      | `haul_cycles`             | `routes/dispatch_lifecycle.py:1035`                                        | Dispatch / haul-ledger                     | Driver / Dispatch           | ✅         | Composed into `/api/dispatch/haul-ledger` (Track 13.21)                  |
| **Scale ticket attached**              | ✅      | `operational_attachments` (`type=scale_ticket`) | dispatch attachment upload                                  | Dispatch                                   | Dispatch / Driver           | ✅         | Proof join in Track 13.19 / 13.21                                       |
| **Verification status changed**        | ✅      | derived from `daily_reports.materials[]` × proof rows | `/api/material-movement/daily/{project_number}/{date}` (Track 13.19) | PM Project Panel                       | Foreman / PM                 | ✅         | Derived per-row status                                                  |
| **Motive geofence arrival/departure**  | ✅      | `operational_events`      | `routes/operational_events.py:339+` (M-2 Event Router)                     | DispatchHub map / OpsCenter                | system (Motive)             | ✅         | event_type ∈ PROJECT/PIT/PLANT/YARD/SHOP/DISPOSAL/VENDOR_ARRIVAL/DEPARTURE |
| **Incident reported**                  | ✅      | `incidents`               | `routes/safety.py:647`, `routes/incident_lifecycle.py:127`                 | SafetyHubV2                                | Safety                      | ✅         | Asset-correlated when equipment_id provided                              |
| **PM due / completed**                 | ❌      | —                         | —                                                                          | —                                          | —                            | —         | **GAP** — no `pm_schedules` collection                                  |
| **Mechanic assigned**                  | ❌      | —                         | —                                                                          | —                                          | —                            | —         | **GAP** — no field on `fleet_defects`; no `mechanic_users`              |
| **Mechanic acknowledged**              | ❌      | —                         | —                                                                          | —                                          | —                            | —         | **GAP** — only role-token, not user-id                                   |
| **Mechanic completed repair**          | ❌      | —                         | —                                                                          | —                                          | —                            | —         | **GAP**                                                                  |
| **Shop manager reviewed repair**       | ❌      | —                         | —                                                                          | —                                          | —                            | —         | **GAP** — Track 13.28 design                                            |
| **Fuel added**                         | ❌      | —                         | —                                                                          | —                                          | —                            | —         | **GAP** — no `fuel_service_visits` (Track 13.29 design)                  |
| **DEF added**                          | ❌      | —                         | —                                                                          | —                                          | —                            | —         | **GAP**                                                                  |
| **Grease completed**                   | ❌      | —                         | —                                                                          | —                                          | —                            | —         | **GAP**                                                                  |
| **Coolant added**                      | ❌      | —                         | —                                                                          | —                                          | —                            | —         | **GAP**                                                                  |
| **Oil added (engine / hyd / trans)**    | ❌      | —                         | —                                                                          | —                                          | —                            | —         | **GAP**                                                                  |
| **MaintainX WO linked**                | ❌      | `maintainx_work_orders` (indexes only at `routes/integrations/_storage.py:97`) | —                                          | —                                          | —                            | —         | **STUBBED** — `MAINTAINX_API_KEY` not set; demo fallback gated by env flag |
| **MaintainX WO completed**             | ❌      | —                         | —                                                                          | —                                          | —                            | —         | **STUBBED**                                                              |

**Doctrine note:** `routes/integrations/events.py:396` returns `demo_maintainx_work_orders()` ONLY when the `maintainx_work_orders` collection is empty AND demo-integration env flag is set. The Asset Service Event Backbone MUST NOT consume that demo fallback. Honest empty placeholder only.

---

## 3 · Gap Table (Events Needed)

| Event Needed                          | Exists?   | Gap Severity | Future Owner / Source                          |
| ------------------------------------- | --------- | ------------ | ---------------------------------------------- |
| Fuel added                            | ❌         | HIGH         | Track 13.29 · `fuel_service_visits.equipment_lines[].red_diesel_gallons / clear_diesel_gallons` |
| DEF added                             | ❌         | HIGH         | Track 13.29 · `fuel_service_visits.equipment_lines[].def_gallons` |
| Grease completed                       | ❌         | HIGH         | Track 13.29 · `fuel_service_visits.equipment_lines[].greased_yes_no` |
| Coolant added                          | ❌         | HIGH         | Track 13.29 · `fuel_service_visits.equipment_lines[].coolant_added` |
| Engine oil added                        | ❌         | HIGH         | Track 13.29 · `equipment_lines[].engine_oil_added` |
| Hydraulic oil added                     | ❌         | HIGH         | Track 13.29 · `equipment_lines[].hydraulic_oil_added` |
| PM due                                  | ❌         | HIGH         | Track 13.31 · derived (Motive hours + last PM completion) |
| PM completed                            | ❌         | HIGH         | Track 13.31 · `fleet_defects.kind="pm"` once defect lifecycle is extended (or future `pm_schedules`) |
| Mechanic assigned                       | ❌         | HIGH         | Track 13.28 · `fleet_defects.assigned_to_mechanic_id` (+ `mechanic_users` collection) |
| Mechanic acknowledged                   | ❌         | HIGH         | Track 13.28 · `fleet_defects.mechanic_acknowledged_at` |
| Mechanic completed repair               | ❌         | HIGH         | Track 13.28 · `fleet_defects.repair_completed_by_mechanic_id` |
| Shop manager reviewed repair            | ❌         | MED          | Track 13.28 · `fleet_defects.shop_manager_reviewed_by` |
| MaintainX work order linked             | ⚠️ STUBBED | HIGH (when creds land) | Track 13.32 · `fleet_defects.maintainx_work_order_id` + `maintainx_work_orders` collection writes |
| MaintainX work order completed          | ⚠️ STUBBED | HIGH (when creds land) | Track 13.32 · webhook handler emits Asset Service Event   |

**Critical rule:** placeholders MUST appear in the backbone with `event_type` in the closed set, and with **empty arrays** plus a top-level `unavailable_event_types` metadata block. Never fabricate.

---

## 4 · Phase 2 — Asset Service Event Model (CERTIFIED)

### 4.1 Document shape

```python
{
  "event_id":               str,            # deterministic hash of (source_system, source_record_id, event_subtype, timestamp)
  "event_type":             str,            # closed set (see 4.2)
  "event_subtype":          Optional[str],
  "asset_id":               Optional[str],  # equipment_master.id (case-insensitive unit_number lookup)
  "unit_number":            str,            # canonical unit identifier
  "timestamp":              str,            # ISO-8601 UTC
  "actor_id":               Optional[str],
  "actor_name":             Optional[str],
  "actor_role":             Optional[str],
  "project_number":         Optional[str],
  "related_record_id":      Optional[str],  # always the source row id
  "related_defect_id":      Optional[str],
  "related_work_order_id":  Optional[str],  # MaintainX-only (future)
  "related_preop_id":       Optional[str],
  "related_dvir_id":        Optional[str],
  "related_attachment_id":  Optional[str],
  "status_before":          Optional[str],
  "status_after":           Optional[str],
  "availability_before":    Optional[str],
  "availability_after":     Optional[str],
  "notes":                  Optional[str],
  "source_system":          str             # closed set (see 4.3)
}
```

### 4.2 `event_type` closed set (Phase 13.26)

Available today (DERIVED from existing sources):
* `preop`
* `dvir`
* `defect`
* `repair`
* `oos`
* `rts`
* `attachment`
* `note`
* `material`
* `inspection`
* `transfer`
* `presence`

Future (placeholder — emit unavailable metadata):
* `pm`
* `fuel`
* `lube`
* `grease`
* `maintainx`

### 4.3 `source_system` closed set

* `equipment_inspections`
* `fleet_defects`
* `fleet_audit`
* `operational_attachments`
* `operational_events`     (Motive presence)
* `haul_cycles`
* `asset_transfers`
* `admin_audit_log`
* `incidents`               (optional · Phase 1 may exclude)
* `fuel_service_visits`     (future · placeholder only)
* `pm_schedules`            (future · placeholder only)
* `maintainx`               (future · placeholder only)

### 4.4 Field classification

| Field group                                                | Available today | Future-only |
| ---------------------------------------------------------- | --------------- | ----------- |
| event_id, event_type, asset_id, unit_number, timestamp, source_system, source_record_id | ✅              |             |
| event_subtype                                                | ✅              |             |
| actor_id, actor_name, actor_role                              | ✅ (partial)    |             |
| related_defect_id, related_preop_id, related_dvir_id           | ✅              |             |
| related_attachment_id                                         | ✅              |             |
| status_before, status_after                                    | ✅              |             |
| availability_before, availability_after                        | ✅              |             |
| project_number                                                 | ✅              |             |
| notes                                                          | ✅              |             |
| related_work_order_id, related_pm_id, related_fuel_visit_id    |                  | future      |

---

## 5 · Implementation Gate (per Phase 2 spec)

| Question                                                  | Answer                                                                                          |
| --------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Can backbone be derived?                                  | ✅ YES — six live source collections cover every event MASCI emits today.                       |
| Is a new collection required?                             | ❌ NO — Phase 13.26 ships a derived virtual projection. Materialize ONLY if observed p95 > 500 ms. |
| Is event aggregation sufficient?                          | ✅ YES — one read endpoint composes; no writers; no schema delta.                              |
| What current sources become event generators?             | `equipment_inspections`, `fleet_defects`, `fleet_audit`, `operational_attachments`, `operational_events`, `haul_cycles`, `asset_transfers`, `admin_audit_log`. |
| Are placeholders required?                                | ✅ YES — `pm`, `fuel`, `lube`, `grease`, `maintainx` MUST appear in `unavailable_event_types` metadata as empty arrays. |
| Auth gate?                                                 | `_require_any_fleet_portal` (Shop / Dispatch / Safety / Admin). PM scope deferred to Track 13.27 frontend layer (per-project filter on top of this endpoint). |
| Date-range cap?                                            | 90 days (mirror Track 13.21 Dispatch Haul Ledger).                                              |
| Output cap?                                                | 1000 events per response.                                                                       |
| Does it duplicate existing event systems?                  | ❌ NO — `operational_records` projects Daily Reports (different scope); `operational_events` is Motive presence only. This backbone composes both PLUS defect/attachment/transfer/haul sources for the per-unit lens. |

**GATE: PASSED. Phase 3 implementation authorized.**

---

## 6 · Hard-Lock Reaffirmation

* ✅ Dispatch Map-First                       (no UI change in Phase 13.26)
* ✅ Driver no-login                          (read endpoint · no driver write path)
* ✅ Shop Repair Complete ≠ Returned-To-Service (RTS only emits when `cleared_at` set)
* ✅ One Map Engine                            (no map surface affected)
* ✅ One Source of Truth                       (each event has a `source_system` + `source_record_id` pointer)
* ✅ No fake MaintainX                         (placeholder only · zero demo data)
* ✅ No fake FleetWatcher                      (not consumed)
* ✅ No duplicate Material Ledger               (composes existing `haul_cycles`, never re-writes)
* ✅ No fake users / mechanics                 (no mechanic data invented · placeholder)
* ✅ No ERP / accounting / contracts / pay-app / RFI / change-order
* ✅ No duplicate history system               (this IS the canonical per-unit history projection)
* ✅ No duplicate event spine                  (single read endpoint composes the six existing collections)
* ✅ No duplicate asset spine                   (consumes `equipment_master` unchanged)

---

**Track 13.26A · CLOSED · GATE PASSED. Implementation proceeds in Track 13.26 (Phase 3).**

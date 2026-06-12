# Track 13.25 — Asset Care & Service Architecture Certification

**Date:** 2026-06-12
**Mode:** SOURCE-TRUTH CERTIFICATION + ARCHITECTURE DESIGN ONLY
**Implementation:** NONE. Zero code · zero route · zero schema · zero UI · zero deploy.
**Doctrine:** TRACK_13_18 (Material Ledger architecture pattern) + TRACK_13_24 (Defect lifecycle certification).
**Verdict:** ✅ Architecture certified. Recommended next: **A — Asset Service Event Backbone** (derived virtual timeline) as Track 13.26.

---

## 1 · TL;DR

MASCI's asset-care reality today is **deep on per-defect lifecycle, shallow on per-unit history, and absent on fuel/lube/PM/mechanic-identity**.

| Layer                          | Status today                                                                                  |
| ------------------------------ | --------------------------------------------------------------------------------------------- |
| Pre-Op / DVIR defect creation  | ✅ FULL · `equipment_inspections` + `fleet_defects` collections live                          |
| Per-defect audit trail          | ✅ FULL · `/api/fleet/defects/{id}/detail` covers report → ack → repair → RTS                  |
| Shop / Dispatch RTS hard lock  | ✅ ENFORCED · `/api/shop/fleet/defects/{id}/repair` vs `/api/dispatch/fleet/defects/{id}/clear` |
| Per-unit timeline               | ❌ MISSING · no aggregate-history endpoint                                                     |
| Mechanic identity / assignment | ❌ MISSING · no `MECHANIC_ROLE`, no `assigned_to_mechanic_id` field                            |
| Preventive Maintenance          | ❌ MISSING · no `service_interval`, no PM collection                                            |
| Fuel / Lube / Grease           | ❌ MISSING · no `fuel_visit`, no `service_truck`, no daily reconciliation                      |
| MaintainX                       | ⚠️ STUBBED · `services/maintainx_client.py` exists with bearer-auth SDK; ENV `MAINTAINX_API_KEY` **NOT SET** in preview |
| FleetWatcher                    | ⚠️ NOT_CONNECTED (per Track 13.18 §2.4)                                                       |

**Verdict:** The defect-lifecycle backbone is solid. The next architectural unlock is **Asset Service Event Backbone** — a derived virtual timeline composed across the 6 existing source collections, NO new persistence. Everything else (Fuel/Lube, PM, Mechanic Auth, MaintainX activation) bolts onto that backbone.

---

## 2 · Phase 1 — Source-Truth Inventory

### Backend

| Source                                                          | Disposition                                       |
| --------------------------------------------------------------- | ------------------------------------------------- |
| `routes/equipment.py`                                           | Equipment master + pre-op inspection CRUD         |
| `routes/fleet_ops.py`                                           | iter251 unified fleet + DVIR + defect lifecycle   |
| `routes/dispatch_command_center.py` `_maintainx_template()`     | NOT_CONNECTED stub (returns null fields)          |
| `services/maintainx_client.py`                                  | Bearer-auth SDK · `MAINTAINX_API_KEY` env-gated  |
| `services/asset_spine.py`                                       | Asset registry · NO PM / service fields            |
| `services/motive_service.py`                                    | Telematics · geofence + hours/odometer            |
| `routes/shop_parts.py`                                          | `POST /api/equipment-parts/order` · separate from defects |
| `routes/tasks_notifications.py`                                 | Fan-out (role-based · already used by 13.17)      |
| `routes/operational_attachments.py` (Track 13.14 weights)       | Proof layer — extensible to mechanic photos        |
| `daily_reports.materials[]` / `outbound_materials[]`            | NOT asset-care · material movement only           |

### Frontend

| Source                                                          | Disposition                                       |
| --------------------------------------------------------------- | ------------------------------------------------- |
| `pages/ShopHubV2.jsx`                                           | Live shop hub (Track 13.24 added Section 04)      |
| `pages/EquipmentDashboard.jsx`                                  | Pre-op list                                       |
| `pages/FleetVisibility.jsx`                                     | DVIR per-unit roll-up                             |
| `pages/ViewEquipmentInspection.jsx`                             | Single-record detail                              |
| `pages/MaterialMovementTile.jsx` (NOT relevant — material only) | exclude                                           |
| Fuel/Lube UI                                                    | ❌ DOES NOT EXIST                                  |
| Mechanic UI                                                     | ❌ DOES NOT EXIST                                  |
| PM UI                                                           | ❌ DOES NOT EXIST                                  |
| Unit history UI                                                 | ❌ DOES NOT EXIST                                  |

### Collections / Models

| Collection                       | Asset-care relevance                              |
| -------------------------------- | ------------------------------------------------- |
| `equipment_inspections`          | Pre-Op + DVIR (`kind` discriminator from iter251) |
| `fleet_defects`                  | One row per failed item; full lifecycle states     |
| `fleet_defect_audit`             | Event audit trail consumed by `defects/{id}/detail` |
| `equipment_master` / asset spine | Asset identity · NO PM fields                      |
| `operational_attachments`        | Proof layer (Track 13.14)                          |
| `tasks_notifications`            | Cross-role fan-out                                 |
| `recovery_*`                     | Shop recovery workflow                             |
| `dispatch_assignments` / `haul_cycles` | NOT asset-care · excluded                    |

---

## 3 · Phase 2 — Current Capability Map

| Capability                              | Today    | Backend                                       | Collection / Fields                              | Owner       | Audit | Export | Gap                         | Priority |
| --------------------------------------- | -------- | --------------------------------------------- | ------------------------------------------------ | ----------- | ----- | ------ | --------------------------- | -------- |
| Asset registry                          | ✅ FULL   | asset_spine                                   | equipment_master                                 | Admin/Dispatch | ✅   | ⚠️     | exports light               | LOW      |
| Unit detail                             | ✅ FULL   | `/api/equipment-inspections/{id}` etc.        | spine                                            | Shop        | ✅    | ❌     |                             | LOW      |
| Pre-Op submission                       | ✅ FULL   | `POST /api/equipment-inspections`             | equipment_inspections                            | Operator    | ✅    | ❌     |                             | LOW      |
| Pre-Op defect creation                  | ✅ FULL   | derived from `items[].passed=false`           | fleet_defects (`kind=preop`)                    | Operator    | ✅    | ❌     |                             | LOW      |
| DVIR submission                         | ✅ FULL   | `POST /api/fleet/inspections`                 | equipment_inspections (`kind=dvir`)              | Driver      | ✅    | ❌     |                             | LOW      |
| DVIR defect creation                    | ✅ FULL   | same fan-out                                  | fleet_defects (`kind=dvir`)                     | Driver      | ✅    | ❌     |                             | LOW      |
| Shop defect queue                        | ✅ FULL   | `/api/shop/fleet/defects`                     | fleet_defects                                    | Shop        | ✅    | ❌     |                             | LOW      |
| Dispatch OOS visibility                  | ✅ FULL   | `/api/shop/fleet/by-unit`                     | derived                                          | Dispatch    | ✅    | ❌     |                             | LOW      |
| Shop notification (defect fan-out)       | ✅ FULL   | `tasks_notifications`                          | tasks_notifications                              | Shop+PM+Dispatch+Admin | ✅ | ❌  |                             | LOW      |
| Mechanic assignment                      | ❌ NONE   | n/a                                           | `assigned_to_mechanic_id` does NOT exist        | —           | ❌    | ❌     | **whole concept missing**   | HIGH     |
| Mechanic acknowledgement                  | ⚠️ PARTIAL | shop ack endpoint records `acknowledged_by`   | role-based, not mechanic-id                      | Shop role   | ✅    | ❌     | mechanic id missing          | HIGH     |
| Repair notes                              | ✅ FULL   | `/repair` endpoint body                       | fleet_defects                                    | Shop        | ✅    | ❌     |                             | LOW      |
| Parts ordered                             | ⚠️ PARTIAL | `routes/shop_parts.py`                        | separate collection · not linked to defects     | Shop        | ✅    | ❌     | auto-link missing            | MED      |
| Parts received                            | ⚠️ PARTIAL | shop_parts                                    | order_received                                   | Shop        | ✅    | ❌     |                             | MED      |
| Labor notes                                | ❌ NONE   | n/a                                            | no `labor_minutes` field                         | —           | ❌    | ❌     |                             | MED      |
| Repair complete                            | ✅ FULL   | shop endpoint                                  | status=repair_complete                            | Shop        | ✅    | ❌     |                             | LOW      |
| Shop-manager review                        | ⚠️ PARTIAL | Shop role token is reviewer · not per-user    | acknowledged_by used as proxy                    | Shop        | ✅    | ❌     | manager-id field missing    | MED      |
| RTS request                                | ⚠️ PARTIAL | Shop role hands over to Dispatch via state    | implicit                                         | Shop        | ✅    | ❌     | no explicit `rts_requested` | LOW      |
| RTS approval                               | ✅ FULL   | `/api/dispatch/fleet/defects/{id}/clear`      | fleet_defects                                    | Dispatch+Admin | ✅ | ❌    |                             | LOW      |
| OOS duration (derivable)                   | ✅ FULL   | derived from defect timestamps                 | fleet_defects + audit                            | derived     | ✅    | ❌     |                             | LOW      |
| Defect detail timeline                     | ✅ FULL   | `/api/fleet/defects/{id}/detail`              | fleet_defect_audit                               | all roles   | ✅    | ❌     |                             | LOW      |
| Per-unit timeline                          | ❌ NONE   | n/a                                            | no aggregate endpoint                            | —           | ❌    | ❌     | **HIGH GAP**                | HIGH     |
| Per-unit search                            | ❌ NONE   | n/a                                            |                                                  | —           | ❌    | ❌     | HIGH GAP                    | HIGH     |
| Pre-Op export                              | ❌ NONE   | n/a                                            |                                                  | —           | —     | ❌     | Track 13.24 doc'd gap       | MED      |
| DVIR export                                | ❌ NONE   | n/a                                            |                                                  | —           | —     | ❌     | Track 13.24 doc'd gap       | MED      |
| Unit history export                        | ❌ NONE   | n/a                                            |                                                  | —           | —     | ❌     |                             | MED      |
| PM schedule                                | ❌ NONE   | n/a                                            | no `service_interval`, no `next_service_due`     | —           | ❌    | ❌     | **whole subsystem missing** | HIGH     |
| PM due-soon / overdue                      | ❌ NONE   | n/a                                            |                                                  | —           | ❌    | ❌     |                             | HIGH     |
| Fuel event                                  | ❌ NONE   | n/a                                            |                                                  | —           | ❌    | ❌     | **whole subsystem missing** | HIGH     |
| Lube / grease event                         | ❌ NONE   | n/a                                            |                                                  | —           | ❌    | ❌     |                             | HIGH     |
| Fuel/lube job visit form                   | ❌ NONE   | n/a                                            |                                                  | —           | ❌    | ❌     |                             | HIGH     |
| Service-truck reconciliation               | ❌ NONE   | n/a                                            |                                                  | —           | ❌    | ❌     |                             | HIGH     |
| Fuel variance                               | ❌ NONE   | n/a                                            |                                                  | —           | ❌    | ❌     |                             | MED      |
| Motive geofence suggestion (fuel/lube)     | ⚠️ DERIVABLE | `motive_service` has geofence data            | Motive                                            | future      | ❌    | ❌     | not surfaced for fuel       | MED      |
| MaintainX work order create                 | ⚠️ STUBBED | `services/maintainx_client.py`                | env-gated                                         | future      | ❌    | ❌     | **BLOCKED on credentials**  | HIGH (when creds land) |
| MaintainX sync / status                     | ⚠️ STUBBED | same                                          |                                                  | future      | ❌    | ❌     |                             | HIGH (later) |
| FleetWatcher                                 | ❌ NOT_CONNECTED | per Track 13.18 §2.4                       |                                                  | future      | —     | —      | BLOCKED                     | LOW      |

---

## 4 · Phase 3 — Defect Lifecycle Certification

### Equipment Pre-Op Defect

| #  | Step                                  | Today                  | Evidence                                          |
| -- | ------------------------------------- | ---------------------- | ------------------------------------------------- |
| 1  | Operator submits Pre-Op               | ✅ FULL                | `POST /api/equipment-inspections`                |
| 2  | Defect identified                      | ✅ FULL                | `items[].passed=false` derivation                |
| 3  | Record stored                          | ✅ FULL                | `equipment_inspections` + `fleet_defects`        |
| 4  | Shop alerted                           | ✅ FULL                | tasks_notifications fan-out (role-based)         |
| 5  | Shop queue updated                     | ✅ FULL                | `/api/shop/fleet/by-unit`                        |
| 6  | Owner assigned (role-level)            | ✅ FULL                | Shop role owns until RTS                          |
| 7  | Mechanic assigned (person-level)        | ❌ MISSING             | no field                                          |
| 8  | Work performed                          | ✅ FULL                | `/repair` endpoint                                |
| 9  | Repair notes / parts / labor            | ⚠️ PARTIAL            | repair notes ✅ · parts separate ⚠ · labor ❌      |
| 10 | Repair complete                         | ✅ FULL                | status=repair_complete                            |
| 11 | RTS requested                           | ✅ IMPLICIT            | state-machine transition                          |
| 12 | RTS verified                            | ✅ FULL                | dispatch+admin gated                              |
| 13 | Unit returned                           | ✅ FULL                | status=cleared                                    |
| 14 | Audit trail preserved                   | ✅ FULL                | `/api/fleet/defects/{id}/detail`                 |
| 15 | History searchable                      | ❌ MISSING             | no aggregate per-unit endpoint                    |

**Verdict: PARTIAL** — single defects defensible; mechanic identity + per-unit search missing.

### Truck DVIR Defect

| #  | Step                                  | Today                  |
| -- | ------------------------------------- | ---------------------- |
| 1  | Driver submits DVIR                    | ✅ FULL                |
| 2  | Defect identified                      | ✅ FULL                |
| 3  | Record stored                          | ✅ FULL                |
| 4  | Shop alerted                           | ✅ FULL                |
| 5  | Dispatch alerted                       | ✅ FULL                |
| 6  | Unit availability updated              | ✅ FULL                |
| 7  | Shop queue updated                     | ✅ FULL                |
| 8  | Owner assigned (role)                  | ✅ FULL                |
| 9  | Mechanic assigned (person)             | ❌ MISSING             |
| 10 | Work performed                         | ✅ FULL                |
| 11 | Repair notes / parts / labor           | ⚠️ PARTIAL            |
| 12 | Repair complete                        | ✅ FULL                |
| 13 | RTS requested                          | ✅ IMPLICIT            |
| 14 | Dispatch/Admin verifies RTS            | ✅ FULL                |
| 15 | Unit returned                          | ✅ FULL                |
| 16 | Audit trail preserved                  | ✅ FULL                |
| 17 | History searchable                     | ❌ MISSING             |

**Verdict: PARTIAL** — identical gap to Pre-Op (mechanic identity + per-unit search).

---

## 5 · Phase 4 — MaintainX Responsibility Design

| Question                          | Answer                                                                                                  |
| --------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Is MaintainX connected?           | ❌ NO — `MAINTAINX_API_KEY` env var absent in preview                                                  |
| Stubbed?                          | ✅ YES — `_maintainx_template()` returns null fields; SDK ready in `services/maintainx_client.py`     |
| Credentials/env                    | `MAINTAINX_API_KEY` (bearer · never logged in full per SDK contract)                                  |
| Service file                       | `backend/services/maintainx_client.py`                                                                  |
| Endpoints                          | None mounted; SDK is a library, not a router                                                            |
| Webhook handling                   | ❌ none                                                                                                  |
| MaintainX ID fields                | absent on `fleet_defects`; need future `maintainx_work_order_id`                                       |
| UI mentions                        | dashboard cards reserved (`maintainx_template()` returned in 4 places)                                 |
| What MASCI can safely build now    | Asset Service Event Backbone · Unit History Timeline · Mechanic Identity model · PM stub · Fuel/Lube  |
| What must wait                     | actual MaintainX work-order create/sync/status                                                          |

### Responsibility split (post-activation)

* **MASCI OPS owns:** defect origin (Pre-Op/DVIR), OOS status, RTS hard lock, asset availability, dispatch visibility, asset timeline, operational audit trail.
* **MaintainX owns:** work-order execution, mechanic assignment (if MASCI chooses to defer), labor, parts, repair completion. MaintainX status events FEED MASCI timeline as external execution events; MaintainX does **not** override MASCI RTS.

### Sync model

1. MASCI defect creation → create MaintainX WO via SDK (`maintainx_client.create_work_order`).
2. MaintainX returns `work_order_id` → MASCI persists on `fleet_defects.maintainx_work_order_id`.
3. MaintainX status webhook → MASCI receives → translates to Asset Service Event.
4. MASCI RTS still requires `/api/dispatch/fleet/defects/{id}/clear` — MaintainX completion alone is NOT RTS.

---

## 6 · Phase 5 — Mechanic / Shop User Model

| Question                                         | Today                                                          |
| ------------------------------------------------ | -------------------------------------------------------------- |
| Mechanic users exist?                            | ❌ NO — no `MECHANIC_ROLE`, no `require_mechanic_dep`          |
| Shop manager role exists?                        | ⚠️ PARTIAL — `require_shop_or_admin` accepts shop role token; shop-manager-vs-mechanic NOT distinguished |
| Can shop assign work to named mechanic today?    | ❌ NO — no field, no UI, no endpoint                            |
| Can mechanic sign in today?                      | ❌ NO                                                            |
| Can mechanic acknowledge work today?             | ⚠️ Shop role can, but identity is shop-token, not mechanic-id  |
| Can mechanic sign off work today?                | same                                                            |
| Can shop manager verify work today?              | ✅ implicitly via Shop role; not per-manager-id                 |
| Mechanic identity on repair                      | ❌ NO                                                            |
| Shop manager identity on assignment              | ❌ NO                                                            |

### Future required fields (Track 13.28 design)

```
fleet_defects.assigned_to_mechanic_id      // FK → mechanic_users
fleet_defects.assigned_to_mechanic_name
fleet_defects.assigned_by_shop_manager_id
fleet_defects.assigned_at
fleet_defects.mechanic_acknowledged_at
fleet_defects.repair_started_at
fleet_defects.repair_completed_at
fleet_defects.repair_completed_by         // mechanic_id (already partial via acknowledged_by)
fleet_defects.shop_manager_reviewed_by
fleet_defects.shop_manager_reviewed_at
fleet_defects.repair_notes                 // (exists today as free-text)
fleet_defects.parts_notes
fleet_defects.labor_notes
fleet_defects.attachments[]                // operational_attachments host_kind="defect"
fleet_defects.maintainx_work_order_id
```

New collection candidate: `mechanic_users` (id, name, status, certifications, shop_assignment). Built only when operator decides whether mechanic auth is needed BEFORE or AFTER MaintainX activation (Phase 13.28 decision-gate).

---

## 7 · Phase 6 — Preventive Maintenance Architecture

**Source-truth verdict:** PM **does not exist today**. No `service_interval`, no `next_service_due`, no `last_service_at` field on asset spine. No PM collection.

### PM Triggers (proposed)

* engine hours (from Motive `service_meter_hours`)
* odometer (from Motive)
* calendar days (from `last_service_at`)
* manual shop schedule

### PM Statuses (closed set)

`current` · `due_soon` · `due` · `overdue` · `scheduled` · `in_progress` · `completed` · `deferred`

### Source-of-truth decision

* **Before MaintainX activation:** MASCI OPS owns PM intervals in a new collection `pm_schedules` (or `asset_pm_state` virtual derived view). Triggers read Motive hours/odometer.
* **After MaintainX activation:** MaintainX becomes source-of-truth for PM scheduling; MASCI mirrors status as Asset Service Events.

**Recommendation:** start with derived virtual PM (read Motive + last service from completed fleet_defects of `kind=pm`) — NO new persistence until intervals need to be configurable per-unit-type. Defer until Track 13.31.

---

## 8 · Phase 7 — Fuel / Lube / Grease Operations Architecture

**Source-truth verdict:** Fuel/Lube **does not exist today**. No `fuel_visit`, no `service_truck`, no `red_diesel`, no `grease` reference in any route.

### Fuel Service Visit Model (proposed · Track 13.29 design)

```python
class FuelServiceVisit(BaseDocument):
    visit_id: PyObjectId
    visit_date: str                      # YYYY-MM-DD
    fuel_lube_driver_id: str             # FK → users
    fuel_lube_truck_id: str              # FK → equipment_master
    project_number: str                  # FK → projects
    arrival_time: datetime
    departure_time: Optional[datetime]
    geofence_id: Optional[str]           # Motive
    notes: Optional[str]
    submitted_at: datetime
    equipment_lines: list[FuelEquipmentLine]
```

### FuelEquipmentLine (one row per unit serviced)

```python
class FuelEquipmentLine(BaseModel):
    unit_number: str
    equipment_id: str
    red_diesel_gallons: Optional[float]
    clear_diesel_gallons: Optional[float]
    def_gallons: Optional[float]
    greased_yes_no: bool
    grease_notes: Optional[str]
    engine_oil_added: Optional[float]
    hydraulic_oil_added: Optional[float]
    coolant_added: Optional[float]
    transmission_fluid_added: Optional[float]
    other_fluid_added: Optional[float]
    service_meter_hours: Optional[float]
    odometer_miles: Optional[float]
    issue_found: bool
    issue_notes: Optional[str]
    attachments: list[str]               # operational_attachments ids
```

### Daily Service Truck Reconciliation (Track 13.30)

`service_truck_reconciliation` document (one per truck per day):

```python
date, truck_id, driver_id,
red_diesel_start_gallons, clear_diesel_start_gallons,
def_start_gallons, oil_start, hyd_oil_start, coolant_start,
red_diesel_end_gallons, ..., coolant_end,
# derived at read time
recorded_dispensed, expected_remaining, actual_remaining, variance, variance_status
```

### Motive Geofence Suggestion (future enhancement)

* Fuel truck Motive ping enters job geofence → backend computes equipment currently inside that geofence → suggests as Equipment Lines → fuel/lube driver confirms or removes.

### Hard rules

* NOT accounting · NOT fuel purchasing · NOT tax/fuel reporting.
* Operational tracking only.
* Each FuelEquipmentLine emits Asset Service Events: `fuel_added`, `def_added`, `greased`, `oil_added`, `hydraulic_oil_added`, `coolant_added`, `service_meter_recorded`, `issue_found`.

---

## 9 · Phase 8 — Service Truck / Dispatch Relationship

* Fuel/Lube trucks ARE assets — already present in `equipment_master` if owned by MASCI (verifiable per-unit).
* Dispatch sees fuel/lube truck location + assignment + availability via existing Motive feed.
* Dispatch does NOT own PM, repair lifecycle, mechanic assignment, fuel reconciliation. **Shop owns service records; Dispatch owns operational availability.**

---

## 10 · Phase 9 — Asset Service Event Model

### Proposed event document

```python
class AssetServiceEvent(BaseDocument):
    event_id: PyObjectId
    asset_id: str                       # FK → equipment_master
    unit_number: str
    event_type: Literal[
        "preop", "dvir", "defect", "oos", "repair", "parts", "rts",
        "fuel", "lube", "grease", "pm", "maintainx",
        "attachment", "note", "dispatch_availability",
    ]
    event_subtype: Optional[str]        # e.g. "fuel_added", "greased", "repair_complete"
    source_system: Literal[
        "equipment_inspections", "fleet_defects", "fleet_defect_audit",
        "tasks_notifications", "operational_attachments",
        "fuel_service_visit", "pm_schedule", "maintainx", "motive",
    ]
    source_record_id: str
    related_defect_id: Optional[str]
    related_work_order_id: Optional[str]
    related_preop_id: Optional[str]
    related_dvir_id: Optional[str]
    related_fuel_visit_id: Optional[str]
    related_pm_id: Optional[str]
    related_maintainx_id: Optional[str]
    timestamp: datetime
    created_by: str
    actor_role: str
    assigned_to: Optional[str]
    status_before: Optional[str]
    status_after: Optional[str]
    availability_before: Optional[str]
    availability_after: Optional[str]
    project_number: Optional[str]
    geofence_id: Optional[str]
    notes: Optional[str]
    attachments: list[str]
    audit_metadata: dict
```

### Field classification

| Group                                                                                        | Required now | Future / MaintainX-only / Fuel-only |
| -------------------------------------------------------------------------------------------- | ------------ | ------------------------------------ |
| event_id, asset_id, unit_number, event_type, source_system, source_record_id, timestamp     | ✅           |                                      |
| related_defect_id, related_preop_id, related_dvir_id                                        | ✅           |                                      |
| status_before, status_after, availability_before, availability_after                        | ✅           |                                      |
| created_by, actor_role                                                                       | ✅           |                                      |
| related_work_order_id, related_maintainx_id                                                  |              | MaintainX-only                       |
| related_fuel_visit_id                                                                         |              | Fuel-only                            |
| related_pm_id                                                                                 |              | PM-only                              |
| project_number, geofence_id                                                                  | ✅ (optional) |                                      |
| attachments                                                                                   | ✅           |                                      |

### Critical: **Asset Service Events should be DERIVED, not persisted, in the first phase.**

A single read endpoint `GET /api/assets/{unit}/timeline?from=&to=` projects across the 6 source collections in real time. NO new collection. This mirrors the Material Movement Ledger architecture from Track 13.18 (LEDGER BACKBONE = derived view).

If observation shows derived projection is too slow (>500ms p95) THEN introduce `asset_service_events` materialized cache. Not before.

---

## 11 · Phase 10 — Unit History Timeline Architecture

**Route:** `/shop/equipment/{unit_number}/history`
**Endpoint:** `GET /api/assets/{unit}/timeline?from=&to=&event_type=&source_system=&status=&project=&mechanic=`
**Default range:** last 90 days.

**Filters:** date range · event type · source system · status · job/project · mechanic · severity.

**Output:** chronological list of Asset Service Events with optional grouping by source.

**Exports:** CSV first (mirror Track 13.22 `format=csv` pattern). PDF / print template later.

---

## 12 · Phase 11 — Shop / Asset Care Command Center (future)

Single read endpoint `GET /api/shop/asset-care-command` returning:

* defects by status
* OOS by hours-out
* waiting-on-parts by part_age
* assigned-to-mechanic counts
* repair-complete awaiting RTS
* PMs due-soon / overdue
* fuel/lube exceptions (variance > threshold)
* repeated-failure units (≥ 2 defects in N days)
* open MaintainX work orders

Surface as Shop Hub V2 Section 05 or a dedicated `/shop/asset-care` page. **Design only.** Defer to Track 13.33.

---

## 13 · Phase 12 — Access Control Matrix

| Role                 | View assigned work | Submit Pre-Op | Submit DVIR | Submit Fuel/Lube | Report defect | Assign mechanic | Ack work | Add repair notes | Add parts | Complete repair | Request RTS | Approve RTS | View unit timeline | Export unit history | Manage PM | View svc truck recon | View company-wide history |
| -------------------- | ------------------ | ------------- | ----------- | ----------------- | ------------- | --------------- | -------- | ---------------- | --------- | --------------- | ----------- | ----------- | ------------------ | ------------------- | --------- | --------------------- | ------------------------- |
| Equipment Operator   | own                | ✅            | —           | —                 | ✅            | ❌              | ❌       | ❌               | ❌        | ❌              | ❌          | ❌          | own unit (read)    | ❌                  | ❌        | ❌                    | ❌                        |
| Truck Driver         | own                | —             | ✅          | —                 | ✅            | ❌              | ❌       | ❌               | ❌        | ❌              | ❌          | ❌          | own unit (read)    | ❌                  | ❌        | ❌                    | ❌                        |
| Fuel/Lube Driver     | own                | —             | —           | ✅                | ✅            | ❌              | ❌       | ❌               | ❌        | ❌              | ❌          | ❌          | own visits         | ❌                  | ❌        | ✅ own truck          | ❌                        |
| **Mechanic** (future) | ✅                 | —             | —           | —                 | ✅            | ❌              | ✅       | ✅               | ✅        | ✅              | ✅          | ❌          | assigned units     | ❌                  | ❌        | ❌                    | ❌                        |
| **Shop Manager**     | ✅                 | —             | —           | —                 | ✅            | ✅              | ✅       | ✅               | ✅        | ✅              | ✅          | ❌          | all                | ✅                  | ✅        | ✅                    | ✅                        |
| Dispatch             | —                  | —             | —           | —                 | ✅            | ❌              | ❌       | ❌               | ❌        | ❌              | ❌          | ✅          | all                | ✅                  | ❌        | ✅ (visibility only)  | ✅                        |
| Admin                | ✅                 | ✅            | ✅          | ✅                | ✅            | ✅              | ✅       | ✅               | ✅        | ✅              | ✅          | ✅          | all                | ✅                  | ✅        | ✅                    | ✅                        |
| PM                   | —                  | —             | —           | —                 | —             | ❌              | ❌       | ❌               | ❌        | ❌              | ❌          | ❌          | per-project (read) | ❌                  | ❌        | ❌                    | ❌                        |
| Safety               | —                  | —             | —           | —                 | ✅ (safety-critical defects) | ❌  | ❌       | ❌               | ❌        | ❌              | ❌          | ❌          | safety-relevant    | ❌                  | ❌        | ❌                    | ❌                        |
| Leadership           | —                  | —             | —           | —                 | —             | ❌              | ❌       | ❌               | ❌        | ❌              | ❌          | ❌          | summary (read)     | ❌                  | ❌        | ❌                    | summary                   |

---

## 14 · Phase 13 — Build Sequence

| # | Track | Goal | Source dependency | Files likely affected | Risk | Rollback | 5-pillar | Verdict |
|---|-------|------|-------------------|----------------------|------|----------|----------|---------|
| 1 | 13.26 | **Asset Service Event Backbone (derived)** | existing 6 source collections | new `routes/asset_service_events.py` (read-only · derived) | LOW | git checkout one file | Pow 9 · Sim 9 · Beau 8 · Tru 10 · Pro 8 | **BUILD** |
| 2 | 13.27 | Unit History Timeline (page + endpoint reuse) | Track 13.26 endpoint | `pages/UnitHistoryTimeline.jsx` + Shop routes | LOW | revert page | Pow 9 · Sim 9 · Beau 9 · Tru 10 · Pro 8 | BUILD after 13.26 |
| 3 | 13.28 | Shop Mechanic Assignment + Repair Notes | new `mechanic_users` collection + field additions on `fleet_defects` | `routes/fleet_ops.py` + Shop UI | MED (schema additive) | revert · keep additive fields nullable | Pow 8 · Sim 7 · Beau 8 · Tru 9 · Pro 7 | BUILD after 13.27 — **requires operator decision on whether mechanics need login** |
| 4 | 13.29 | Fuel/Lube Job Visit Form | new `fuel_service_visits` collection | new backend module + new UI | MED-HIGH | drop collection | Pow 10 · Sim 6 · Beau 8 · Tru 10 · Pro 6 | BUILD when operator ready |
| 5 | 13.30 | Fuel/Lube Daily Reconciliation | Track 13.29 dependency | new `service_truck_reconciliation` collection + UI | MED | drop collection | Pow 9 · Sim 7 · Beau 7 · Tru 10 · Pro 6 | BUILD after 13.29 |
| 6 | 13.31 | PM Engine (derived first) | Motive hours/odometer + historical PM completions | new `routes/pm_engine.py` (derived) | LOW-MED | revert | Pow 9 · Sim 8 · Beau 7 · Tru 9 · Pro 7 | BUILD after 13.28 |
| 7 | 13.32 | MaintainX Integration | `MAINTAINX_API_KEY` + active credentials | webhook handler + sync job | HIGH | **BLOCKED on credentials** | Pow 10 · Sim 5 · Beau 7 · Tru 7 · Pro 5 | **DO NOT BUILD until credentials** |
| 8 | 13.33 | Asset Care Command Center | Tracks 13.26–13.31 dependency | new admin/shop page | LOW | revert page | Pow 9 · Sim 8 · Beau 9 · Tru 10 · Pro 8 | BUILD after lower tracks land |

---

## 15 · Phase 14 — What NOT to Build

* ❌ Fake MaintainX integration / fake work-order create
* ❌ Fake mechanic users
* ❌ Fake PM schedules
* ❌ Fake fuel totals
* ❌ Accounting / fuel-purchasing / tax-fuel module
* ❌ Cost-per-unit / ERP / pay-app / contract / RFI / submittal / formal change-order / formal doc control
* ❌ Vendor fuel portal
* ❌ Driver dashboard (Driver stays no-login)
* ❌ Mechanic portal **before** auth model decision (Track 13.28 decision gate)
* ❌ Automatic RTS without dispatch+admin verification (HARD LOCK)
* ❌ Duplicate shop-history table disconnected from existing audit trail
* ❌ Persistent Asset Service Events collection in Phase 13.26 — start derived, materialize only if observation proves it's necessary

---

## 16 · Phase 15 — Final Recommendation

**Chosen action: A — Build Asset Service Event Backbone first (Track 13.26).**

### Why A (not B/C/D/E/F/G)

* B (Unit Timeline) depends on A.
* C (Mechanic Assignment) needs auth-model decision + schema additions — operator must decide first.
* D (Fuel/Lube) is high-value but is a multi-week build (form + reconciliation + Motive geofence). Premature.
* E (PM Engine) reads Motive + historical PM completions — but a "PM completion" today has no canonical event home. A unlocks this naturally.
* F (Wait for MaintainX credentials) is sensible but doesn't have to block A. A is MaintainX-agnostic.
* G (Operator signoff window) can run **in parallel** with A since A is a single read-only backend file with zero UI change.

### Why A is the right unlock

* **Lowest risk** — single backend file, derived virtual view, no new collection, no schema delta, no UI delta. Mirrors the Material Movement Ledger Phase A pattern from Track 13.19 exactly.
* **Foundation** — every subsequent track (Unit Timeline, Mechanic Assignment, Fuel/Lube, PM, MaintainX) writes events into the same shape. A defines the shape.
* **Operator-visible value within hours** — once A lands, Track 13.27 (Unit Timeline page) is ~4 hours of frontend work.
* **MaintainX-ready** — when credentials land, MaintainX webhook handler just emits `event_type=maintainx` rows into the same projection.

---

## 17 · Final Response (per Track 13.25)

1. **Track status:** CLOSED · architecture certified. All 15 phases delivered.
2. **Implementation occurred:** **NO.** Zero code · zero route · zero schema · zero UI · zero deploy.
3. **Source systems found:** `equipment_inspections` · `fleet_defects` · `fleet_defect_audit` · `equipment_master` (asset spine) · `operational_attachments` · `tasks_notifications` · `recovery_*` · `motive_service` · MaintainX SDK (stubbed) · FleetWatcher (not connected). Six are live; two are gated on credentials.
4. **Current Asset Care status:** Defect-lifecycle backbone is **operationally defensible record-by-record** (`/api/fleet/defects/{id}/detail`); per-unit aggregate history is **missing**; mechanic identity is **missing**; PM is **missing**; Fuel/Lube is **missing**.
5. **MaintainX status:** ⚠️ STUBBED — SDK ready in `services/maintainx_client.py`, env key `MAINTAINX_API_KEY` not set. NOT CONNECTED.
6. **Fuel/Lube recommendation:** Build as one form per job visit with multiple equipment lines + daily service-truck reconciliation. Motive geofence suggestion as future enhancement. NOT accounting · NOT fuel purchasing · NOT tax. Each line emits Asset Service Events.
7. **Mechanic assignment recommendation:** Add `assigned_to_mechanic_id` + sibling fields on `fleet_defects` plus new `mechanic_users` collection. **Decision gate first:** does MASCI want mechanics to log in BEFORE MaintainX activation, or defer mechanic identity to MaintainX? Recommend MASCI-OPS-first (Track 13.28) so identity is captured even before MaintainX lands.
8. **PM architecture recommendation:** Derived virtual PM (read Motive hours/odometer + last service from `fleet_defects` of `kind=pm` or future Fuel/Lube `service_meter_hours`) as Phase A. Materialize `pm_schedules` collection only when per-unit-type intervals need to be configurable. Source-of-truth shifts to MaintainX after activation.
9. **Unit timeline recommendation:** New route `/shop/equipment/{unit}/history` consuming a new derived endpoint `GET /api/assets/{unit}/timeline?from=&to=&event_type=&...`. Default range last 90 days. CSV export first.
10. **Recommended next build:** **Track 13.26 — Asset Service Event Backbone (derived virtual timeline).** Single backend file. Zero new collection. Zero UI. ~4–6 hours.
11. **What NOT to build:** fake MaintainX, fake mechanic users, fake PM, fake fuel totals, accounting/ERP/pay-app/cost, vendor portal, driver dashboard, mechanic portal before auth-model decision, automatic RTS, duplicate shop-history table, persistent Asset Service Events collection in Phase 13.26.
12. **Blockers:** Phase 13.32 (MaintainX integration) blocked on `MAINTAINX_API_KEY` + active service credentials. Phase 13.28 (Mechanic Assignment) blocked on operator decision about mechanic login.
13. **Report path:** `/app/memory/TRACK_13_25_ASSET_CARE_SERVICE_ARCHITECTURE_CERTIFICATION.md` (this file).

---

## 18 · Hard-Lock Reaffirmation

* ✅ Dispatch Map-First
* ✅ Driver no-login · no Driver Hub
* ✅ Shop Repair Complete ≠ Returned-To-Service (Shop repairs · Dispatch+Admin verifies RTS)
* ✅ One map engine · one source of truth (the derived Asset Service Event projection)
* ✅ No fake MaintainX · no fake FleetWatcher
* ✅ No duplicate Material Ledger
* ✅ No accounting · no ERP · no pay-app · no cost / contract / RFI / submittal / change-order / doc-control / plan-revision
* ✅ No fake users · no mock mechanic names · no fake service history

**Track 13.25 · CLOSED · ARCHITECTURE CERTIFIED. Awaiting operator directive on Track 13.26.**

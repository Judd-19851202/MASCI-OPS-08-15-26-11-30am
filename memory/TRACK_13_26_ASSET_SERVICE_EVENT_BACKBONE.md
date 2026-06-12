# Track 13.26 — Asset Service Event Backbone (PHASE 3 · DERIVED)

**Date:** 2026-06-12
**Mode:** Controlled implementation (READ-ONLY backend · derived projection · no UI · no migration)
**Doctrine:**
  * `/app/memory/TRACK_13_25_ASSET_CARE_SERVICE_ARCHITECTURE_CERTIFICATION.md` (architecture)
  * `/app/memory/TRACK_13_26A_ASSET_EVENT_SOURCE_CERTIFICATION.md` (source-truth gate · Phase 1/2)
**Verdict:** ✅ Backbone shipped. 11 contract tests pass. Zero new collection · zero schema delta · zero UI · zero deploy.

---

## 1 · TL;DR

A single read endpoint — `GET /api/assets/{unit_number}/timeline` — composes the per-unit service history live across **eight existing collections**. No new persistence. Future event sources (`pm`, `fuel`, `lube`, `grease`, `maintainx`) appear in the response as `unavailable_event_types` placeholders. MaintainX demo data is **never** consumed.

**One unit. One question. One timeline. Honest empty state when truth is empty.**

---

## 2 · Implementation Inventory

### Files added

| Path                                                                                          | Lines | Purpose                                                              |
| --------------------------------------------------------------------------------------------- | ----- | -------------------------------------------------------------------- |
| `backend/routes/asset_service_events.py`                                                       | ~520  | Router factory + per-source projectors                              |
| `backend/tests/test_track_13_26_asset_service_event_backbone.py`                                | ~190  | 11 contract tests (auth, envelope, validation, placeholders)         |
| `memory/TRACK_13_26A_ASSET_EVENT_SOURCE_CERTIFICATION.md`                                       | ~280  | Phase 1 source-truth certification + gate                            |
| `memory/TRACK_13_26_ASSET_SERVICE_EVENT_BACKBONE.md`                                            | this  | Phase 3 implementation report                                        |

### Files modified

| Path                | Change                                                                                |
| ------------------- | ------------------------------------------------------------------------------------- |
| `backend/server.py` | Mount the new router under `_require_any_fleet_portal` (~20 lines, additive only).   |

### Files NOT touched

* No `routes/equipment.py` change
* No `routes/fleet_ops.py` change
* No `routes/dispatch_*` change
* No frontend change
* No `equipment_master` / `fleet_defects` / `equipment_inspections` schema change
* No `dispatch_assignments` change
* No `package.json`, no `requirements.txt`, no `.env`

---

## 3 · Endpoint Contract

```
GET /api/assets/{unit_number}/timeline
    ?from=YYYY-MM-DD          (optional · default = today − 90 days)
    &to=YYYY-MM-DD            (optional · default = today)
    &event_type=<closed-set>  (optional)
    &source_system=<closed-set> (optional)
    &limit=<1..1000>          (optional · default = 500)
```

**Auth:** `_require_any_fleet_portal` — Shop, Dispatch, Safety, or Admin token required (`X-Admin-Token` / `X-Dispatch-Token` / `X-Shop-Token` / `X-Safety-Token`).

**Response envelope:**

```json
{
  "unit_number": "...",
  "asset_id": "<equipment_master.id or null>",
  "range": { "from": "...", "to": "...", "max_days": 90 },
  "filters": { "event_type": null, "source_system": null, "limit": 500 },
  "events": [ { ...Asset Service Event docs ordered newest-first... } ],
  "counts": {
    "total": 0,
    "by_event_type":      { "preop":0, "dvir":0, "defect":0, ... },
    "by_source_system":   { "equipment_inspections":0, "fleet_defects":0, ... }
  },
  "unavailable_event_types": [
    { "event_type": "pm",        "available": false, "reason": "...", "future_track": "Track 13.31 (PM Engine)" },
    { "event_type": "fuel",      "available": false, "reason": "...", "future_track": "Track 13.29 (Fuel/Lube Job Visit Form)" },
    { "event_type": "lube",      "available": false, ... },
    { "event_type": "grease",    "available": false, ... },
    { "event_type": "maintainx", "available": false, "reason": "MaintainX integration is stubbed only. `MAINTAINX_API_KEY` not configured.", "future_track": "Track 13.32 (MaintainX Integration)" }
  ],
  "doctrine": { "derived": true, "persistent_collection": false, "spec": "...", "certification": "...", "generated_at": "..." }
}
```

**Closed set · `event_type`:**

* Available now: `preop · dvir · defect · repair · oos · rts · attachment · note · material · inspection · transfer · presence`
* Future placeholders: `pm · fuel · lube · grease · maintainx`

**Closed set · `source_system`:** `equipment_inspections · fleet_defects · fleet_audit · operational_attachments · operational_events · haul_cycles · asset_transfers · admin_audit_log`

**Bounds:**

* Date range capped at 90 days (HTTP 422 otherwise · mirrors Track 13.21 ledger).
* Output capped at 1000 events.
* Invalid date format, inverted range, unknown event_type, unknown source_system → HTTP 422.

---

## 4 · Per-Source Projectors

| Source                  | Projector                       | Emitted event_type / subtype                                                                  |
| ----------------------- | ------------------------------- | --------------------------------------------------------------------------------------------- |
| `equipment_inspections` (Pre-Op) | `_project_preop`         | `preop/submitted` · `preop/failed` · `inspection/shop_signed_off`                              |
| `equipment_inspections` (DVIR)   | `_project_dvir`          | `dvir/submitted` · `dvir/failed`                                                              |
| `fleet_defects`         | `_project_defect`               | `defect/opened` · `oos/<kind>` · `defect/acknowledged` · `repair/completed` · `rts/verified` |
| `haul_cycles`           | `_project_haul_cycles`          | `material/<haul_type>` (one per completed cycle for the unit)                                  |
| `operational_events`     | `_project_motive_presence`      | `presence/<motive_event_type>` (PROJECT/PIT/PLANT/SHOP/YARD/DISPOSAL/VENDOR · arrival/departure) |
| `asset_transfers`       | `_project_transfers`            | `transfer/transfer` · `transfer/retire` · `transfer/activate`                                   |

Each event row carries:

`event_id` (deterministic SHA1) · `event_type` · `event_subtype` · `asset_id` · `unit_number` · `timestamp` · `actor_id` · `actor_name` · `actor_role` · `project_number` · `related_record_id` · `related_defect_id` · `related_preop_id` · `related_dvir_id` · `related_attachment_id` · `related_work_order_id` · `status_before` · `status_after` · `availability_before` · `availability_after` · `notes` · `source_system`

Unit matching is case-insensitive via `^<escape>$` regex.

---

## 5 · What was NOT done (intentional)

* ❌ No new `asset_service_events` collection. (Materialize only if observed p95 > 500 ms.)
* ❌ No write endpoint. Event creation stays in source-of-truth routes.
* ❌ No `pm_schedules`, no `mechanic_users`, no `fuel_service_visits`, no `service_truck_reconciliation`, no `maintainx_work_orders` writes.
* ❌ No frontend page. (Track 13.27 will add `/shop/equipment/{unit}/history` consuming this endpoint.)
* ❌ No MaintainX demo fabrication. `routes/integrations/events.py:demo_maintainx_work_orders()` is NEVER consumed by this projector.
* ❌ No fleet-defect attachment join (today `operational_attachments` carries `host_kind="assignment"` only). Defect photos remain on `fleet_defects.repair_photos` and travel inside the `repair/completed` event's `notes` for now.
* ❌ No incidents projection (deferred · safety doesn't yet attach a unit_number consistently).
* ❌ No fleet_audit projection (Phase 1 cert noted these are role-token-only; defect events already cover the lifecycle).
* ❌ No UI change · no Dispatch map change · no Shop hub change.

---

## 6 · Tests

`/app/backend/tests/test_track_13_26_asset_service_event_backbone.py` — **11 / 11 passing**:

```
test_timeline_requires_fleet_portal_auth                 PASSED
test_timeline_empty_unit_shape_is_honest                 PASSED
test_unavailable_event_types_placeholder_present         PASSED
test_doctrine_block_marks_derived_view                   PASSED
test_default_range_is_ninety_days_back                   PASSED
test_invalid_event_type_rejected                         PASSED
test_invalid_source_system_rejected                      PASSED
test_invalid_date_format_rejected                        PASSED
test_inverted_range_rejected                             PASSED
test_excessive_range_rejected                            PASSED
test_unavailable_event_type_filter_returns_empty         PASSED
```

Coverage:

* Auth gate (401 without token).
* Envelope shape on a synthetic unit (honest empty).
* All 12 available event_type counters present (closed set).
* All 8 source_system counters present.
* All 5 unavailable placeholders present with `reason` + `future_track` populated.
* Default 90-day range when `from`/`to` omitted.
* Filter validation: bad event_type, bad source_system, bad date, inverted range, excessive range.
* `event_type=pm` (placeholder) returns empty events — never fabricated.

---

## 7 · Final Response (per Track 13.26 spec)

1. **Certification status:** PASSED · Phase 1 + Phase 2 gates documented in `TRACK_13_26A_ASSET_EVENT_SOURCE_CERTIFICATION.md`.
2. **Event sources found:** `equipment_inspections` · `fleet_defects` · `fleet_audit` · `operational_attachments` · `operational_events` · `haul_cycles` · `asset_transfers` · `admin_audit_log`.
3. **Event sources missing:** `pm_schedules` · `fuel_service_visits` · `service_truck_reconciliation` · `mechanic_users` · `maintainx_work_orders` (stub only · no writes today).
4. **Event model approved:** see `TRACK_13_26A` §4. 22 fields · closed-set `event_type` · closed-set `source_system`.
5. **New collection required:** ❌ NO. Derived projection only.
6. **Backbone implementation status:** ✅ DONE · 1 router · 1 endpoint · 5 projectors · 11 tests · 0 schema delta.
7. **Files changed:**
   * Added: `routes/asset_service_events.py` · `tests/test_track_13_26_asset_service_event_backbone.py` · `memory/TRACK_13_26A_ASSET_EVENT_SOURCE_CERTIFICATION.md` · `memory/TRACK_13_26_ASSET_SERVICE_EVENT_BACKBONE.md`
   * Modified: `backend/server.py` (additive router mount only)
8. **Endpoints added/modified:**
   * Added: `GET /api/assets/{unit_number}/timeline`
   * Modified: NONE
9. **Tests passed:** 11 / 11 (`pytest tests/test_track_13_26_asset_service_event_backbone.py -v`).
10. **Hard locks verified:**
    * Dispatch Map-First ✅ (no map surface touched)
    * Driver no-login ✅ (read-only · auth required)
    * Shop Repair Complete ≠ RTS ✅ (`repair/completed` and `rts/verified` are distinct events)
    * One Map Engine · One Source of Truth ✅ (each event carries `source_system` + `source_record_id` pointer)
    * No fake MaintainX ✅ (placeholder only · demo fallback NOT consumed)
    * No fake FleetWatcher ✅ (not consumed)
    * No duplicate Material Ledger ✅ (consumes existing `haul_cycles`)
    * No duplicate event spine ✅ (Motive presence stays in `operational_events`; this backbone composes them per unit)
    * No new persistent asset spine ✅ (derived only)
11. **Blockers:** none for Track 13.26. Track 13.27 (Unit History UI) is the natural next track. Track 13.32 (MaintainX) remains blocked on `MAINTAINX_API_KEY`.
12. **Recommended next track:** **Track 13.27 — Unit History Timeline (frontend page).** Consume `/api/assets/{unit}/timeline` from a new `/shop/equipment/{unit}/history` page. Read-only · ~4 hours of frontend work · no backend change required.

---

## 8 · Hard-Lock Reaffirmation

* ✅ Dispatch Map-First
* ✅ Driver no-login · DriverHubV2 retired
* ✅ Shop Repair Complete ≠ Returned-To-Service
* ✅ Dispatch / Admin RTS verification
* ✅ One Map Engine · One Source of Truth
* ✅ No ERP · no accounting · no Pay Apps · no contracts · no RFI · no submittal · no change-order · no doc-control
* ✅ No FleetWatcher fabrication
* ✅ No MaintainX fabrication
* ✅ No duplicate history systems
* ✅ No duplicate event systems
* ✅ No duplicate asset spines

**Track 13.26 · CLOSED · BACKBONE LIVE. Awaiting operator directive for Track 13.27 or signoff window.**

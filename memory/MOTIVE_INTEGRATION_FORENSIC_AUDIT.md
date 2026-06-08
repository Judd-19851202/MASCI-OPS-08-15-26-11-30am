# MASCI · Motive Integration Forensic Audit

**Date**: 2026-02-12 · **Mode**: Read-only · **Authorized**: NO BUILD · NO CHANGES · NO REDESIGN
**Audited surfaces**: 195 backend files · 280+ frontend components · 14 integration modules

---

## 1 · Executive Summary

> **The Motive integration is roughly 60% wired — the entire scaffolding exists, just no live API calls.**

| Surface | State | Evidence |
|---|---|---|
| **Integration framework** (config · webhooks · events · mappings · health · UI) | ✅ **PRODUCTION-READY** | 14 modules in `backend/routes/integrations/`, 1 587 LOC of UI in `AdminIntegrationCenter` + `IntegrationHealthCard` + `IntegrationEventsCard`, 3 admin/dispatch tiles |
| **`MotiveService` class** (the only thing missing) | 🔴 **STUB** | `backend/services/motive_service.py:1-95` — every method is a placeholder returning `"Stub — real Motive API not wired yet."` |
| **Webhook receiver** | ✅ **REGISTERED** | `POST /api/integrations/motive/webhook` mounted, HMAC signature verifier in place, gated by `webhook_secret_value` in `integration_settings` |
| **Field-mapping schema** (Motive vehicle_id ↔ MASCI equipment_id) | ✅ **DESIGNED** | `asset_mappings` and `employee_mappings` collections, indexed on `motive.vehicle_id` / `motive.driver_id`, full CRUD endpoints in `mappings.py` |
| **Dispatch state machine ready for geo events** | ✅ **READY** | `geo: Optional[Dict]` field appears on every state event row · already nullable — Motive geofence event simply fills it in |
| **Job location data for geofences** | ⚠️ **STRING ONLY** | `/api/jobs` carries 28 jobs with a `location` STRING field — no `lat/lng` columns; would need geocoding step OR Motive's address-to-geofence helper |

**Bottom line**: When Motive credentials land and `MotiveService` methods get real HTTP calls, **every downstream consumer already exists**. The platform is the closest thing to "ready" without actually being live.

---

## 2 · Existing Motive Assets · Inventory

| File | Purpose | LOC | Status |
|---|---|---|---|
| `backend/services/motive_service.py` | Provider service class · stub | 95 | 🔴 **STUB** — all methods return `status="stub"` |
| `backend/routes/integrations/__init__.py` | Mounts the 6 sub-routers | — | ✅ **ACTIVE** |
| `backend/routes/integrations/_models.py` | Shared Pydantic models · IntegrationSettings, AssetMapping, EmployeeMapping | — | ✅ **ACTIVE** |
| `backend/routes/integrations/_storage.py` | Index creation · seed defaults · helpers · HMAC verifier stub | 230+ | ✅ **ACTIVE** — `motive_events` collection indexed at startup |
| `backend/routes/integrations/_deps.py` | Auth gates for integration routes | — | ✅ **ACTIVE** |
| `backend/routes/integrations/config.py` | Per-provider settings CRUD · `MotiveService` factory | 153 | ✅ **ACTIVE** (calls stubbed service) |
| `backend/routes/integrations/webhooks.py` | `POST /api/integrations/motive/webhook` · signature verify · error logging · sync logs | 113 | ✅ **ACTIVE** — already wired to MotiveService.process_webhook |
| `backend/routes/integrations/events.py` | `motive_events` browse/filter | 94 | ✅ **ACTIVE** |
| `backend/routes/integrations/mappings.py` | Asset + Employee mapping CRUD · 12 motive fields per asset | 307 | ✅ **ACTIVE** |
| `backend/routes/integrations/wizard.py` | Multi-step setup wizard backend | — | ✅ **ACTIVE** |
| `backend/routes/integrations/imports_exports.py` | CSV import/export for mappings | — | ✅ **ACTIVE** |
| `backend/routes/integrations/logs.py` | Error log + sync log surfaces | — | ✅ **ACTIVE** |
| `backend/routes/integration_health.py` | Health card data for Admin + Dispatch | — | ✅ **ACTIVE** |
| `frontend/src/pages/admin/AdminIntegrationCenter.jsx` | Full integration center UI | 1 221 | ✅ **ACTIVE** |
| `frontend/src/components/IntegrationHealthCard.jsx` | KPI tile (Motive + MaintainX) | 145 | ✅ **ACTIVE** |
| `frontend/src/components/IntegrationEventsCard.jsx` | Event feed tile | 221 | ✅ **ACTIVE** |
| `frontend/src/components/DispatchIntegrationsTab.jsx` | "Motive + MaintainX Visibility" tab in Dispatch | — | ✅ **ACTIVE** — already binds to `overview.motive` API shape |

**Tests already in repo referencing Motive**: `test_integrations_iter122`, `test_iter123_mappings_wizard`, `test_integration_health_iter142`, `test_iter132_final`, `test_iter251_fleet_ops_foundation`, `test_iter286_driver_qualification_foundation`.

---

## 3 · Existing Motive Integrations · Live vs Stub

| Capability | Backend route | Service method | Status |
|---|---|---|---|
| Test connection | `POST /api/integrations/motive/test-connection` | `test_connection()` | 🔴 returns `"stub_live"` |
| Sync assets | `POST /api/integrations/motive/sync-assets` | `sync_assets()` | 🔴 returns `status="awaiting_credentials"` |
| Sync users | `POST /api/integrations/motive/sync-users` | `sync_users()` | 🔴 same |
| Sync events | `POST /api/integrations/motive/sync-events` | `sync_events()` | 🔴 same |
| Receive webhook | `POST /api/integrations/motive/webhook` | `process_webhook()` | ⚠️ **route active, signature verified, payload logged but NOT routed** — service returns `status="logged_stub"` |
| Build CA from event | (admin trigger) | `create_corrective_action_from_event()` | 🔴 stub |
| **Field mapping CRUD** | `/api/integrations/asset-mappings` + `/employee-mappings` | — | ✅ **LIVE** · CRUD + CSV bulk loader work |
| **Integration health** | `/api/integration-health` | — | ✅ **LIVE** · reads counts from `asset_mappings`, `motive_events` |

**`asset_mappings.motive` document shape** (per `mappings.py:97-104`):
```json
{
  "motive": {
    "vehicle_id": "<motive vehicle id>",
    "asset_id": "<motive asset id>",
    "driver_id": "<motive driver id>",
    "device_id": "<motive device id>",
    "gps_enabled": false,
    "dashcam_enabled": false
  }
}
```
This schema is ready to be hydrated the moment Motive's `/v1/vehicles` endpoint returns data.

---

## 4 · Dispatch Opportunities · Motive event → MASCI lifecycle map

| Motive event | MASCI dispatch action | Confidence | Effort |
|---|---|---|---|
| `vehicle.geofence.entered` (Plant) | `ASSIGNED → AT_LOAD_SITE` transition (auto) | HIGH — geofence precision is good | 1–2 days |
| `vehicle.geofence.exited` (Plant) | `AT_LOAD_SITE → ENROUTE_TO_JOB` (auto) | HIGH | same |
| `vehicle.geofence.entered` (Job) | `ENROUTE_TO_JOB → ARRIVED_JOB` (auto) | HIGH | same |
| `vehicle.geofence.exited` (Job) | `DUMPING → COMPLETE` (auto when destination cleared) | MEDIUM — depends on cycle count | 1 day extra heuristic |
| `vehicle.ignition_off` (> N min) | `WAITING` with reason "engine_off" | MEDIUM — could double-fire if driver stops to talk | 0.5 day |
| `vehicle.ignition_on` after `WAITING` | `WAITING → previous_state` (auto-resume) | MEDIUM | same |
| `vehicle.driver_assigned` | confirm driver_id matches assignment.driver_id; alert if mismatch | HIGH | 0.5 day |
| `vehicle.location.update` (5-min ticks) | store latest `geo` on assignment for live board map | HIGH | 0.5 day |

**State machine readiness**: every existing event row (`dispatch_state_events`) has a `geo` field — already nullable, already in the shape `{lat,lng,accuracy}`. Motive geofence events drop right in.

**Dispatch transition handler readiness**: `_record_transition()` at `dispatch_lifecycle.py:260` already accepts `geo` and `actor`. A Motive webhook handler would call this with `actor={"_actor":"motive","name":"motive-geofence"}` and `geo={"lat":...,"lng":...}` — zero schema change.

---

## 5 · Equipment Strategy · Motive vs MASCI per asset class

| Asset class | Recommendation | Why |
|---|---|---|
| **Trucks (dump, lowboy, water, tanker)** | **A · Motive Managed** | Real-time location, hours, fuel — Motive's native domain. MASCI keeps assignment + ownership. |
| **Excavators, dozers, graders, loaders, pavers, rollers, mills** | **C · Hybrid** | Motive provides telematics (location, hours, idle, utilization); MASCI owns the daily inspection + maintenance + assignment workflow (`equipment_inspections`, `fleet_defects`). |
| **Trench boxes** | **B · MASCI Managed** | No Motive device — `trench_safety_assets` is the source of truth. Motive cannot help. |
| **Barricades, signs, generators, small tools** | **B · MASCI Managed** | Same — no telematics device. `equipment_master` rows are inventory only. |
| **Lowboy + transferred-on equipment** | **C · Hybrid** | When lowboy moves, it carries a Motive device. Equipment riding on it has no device but inherits location from the lowboy. MASCI handles the "transfer" record via `AssetTransfers.jsx`. |
| **Survey equipment** | **B · MASCI Managed** | Same as trench boxes — small, no device. |

The `asset_mappings` collection design already supports **partial mapping** — a row can have `motive.gps_enabled=false` and `motive.dashcam_enabled=false` for the MASCI-managed classes while still belonging to the unified `equipment_master`. No schema change needed.

---

## 6 · Safety Opportunities

The integration framework's webhook router already supports **arbitrary event kinds**. Motive Safety events can flow in immediately once credentials land:

| Motive safety event | MASCI surface (already exists) |
|---|---|
| `vehicle.harsh_brake` | Trench Safety / `dispatch_state_events` audit row tagged `MOTIVE_SAFETY` |
| `vehicle.harsh_accel` | same |
| `vehicle.harsh_turn` | same |
| `driver.fatigue_alert` | dispatcher bell (`db.tasks` `kind="motive_safety"`) |
| `driver.distracted_driving` | same + corrective-action seed via `create_corrective_action_from_event()` (stubbed) |
| `vehicle.speeding` | same |

**Reuse**: all six events plug into the existing bell + audit + state-event surfaces with **zero new collection**.

---

## 7 · Shop Opportunities

`maintainx_*` services are already wired and live (defect-coverage sync, asset sync). Motive can complement by:

| Motive signal | Shop action (existing) |
|---|---|
| `vehicle.dtc_code` (engine diagnostic) | open MaintainX work order automatically (already a pattern in `maintainx_p0.py`) |
| `vehicle.odometer.threshold` (every 5k miles) | schedule preventive maintenance — existing PM cadence in `equipment_master` |
| `vehicle.engine_hours.threshold` | same — hour-based PM |
| `vehicle.tire_pressure_low` | breakdown signal → dispatch continuity event (`dispatch_continuity.py`) |

The dispatch breakdown → shop recovery pipeline (`reported → diagnosing → repaired`) already exists. Motive is just a new event source for the **reported** state.

---

## 8 · Asset Registry Opportunities

`equipment_master` carries 200+ assets today. Mapping coverage report from the existing UI (`AdminIntegrationCenter`) already surfaces:
- `tracked_assets` (mapped)
- `idle_count` (>7d no movement)
- `not_reporting` (mapped but no telemetry)
- `unmapped_external` (Motive units not yet tied to a MASCI asset)

When Motive sync goes live, **these counters populate themselves**. No UI change required. The empty-state copy already reads: *"Awaiting Motive integration configuration. GPS, telematics, and asset tracking data will appear here once Admin enables the integration."*

---

## 9 · Geofence Opportunities

### Location data already in MASCI

| Source | Field | Coverage |
|---|---|---|
| `jobs_master.location` | free-text address | ✅ all 28 jobs populated |
| `dispatch_assignments.source_location` | free-text | ✅ populated per assignment |
| `dispatch_assignments.destination` | free-text | ✅ populated per assignment |
| `dispatch_assignment_seeds.SEEDED_SOURCES` / `_DESTINATIONS` / `_PICKUP` / `_DROPOFF` | canonical free-text seeds (Plant A · Yard · Borrow Pit · Landfill labels) | ✅ ~50 seeded locations |

### Gap

Job + plant + yard locations are **strings only** — no `lat/lng` columns. To create Motive geofences automatically, the platform would need either:

1. **One-time geocoding script** — feed each unique `location` into a geocoder, persist coordinates on `jobs_master` and the seed dictionary. ~1 day of work.
2. **Manual geofence creation** in the Motive Console, then map by name. Slower but no MASCI code change.

Once geofences exist, the existing `motive.vehicle_id ↔ masci_equipment_id` mapping plus the webhook router covers the rest.

### High-value geofences

| Geofence class | Examples in MASCI today | Operational value |
|---|---|---|
| Projects (28 active) | T5686 SR 15/SR600 · E57B2 SR 46 · T5824 SR 46 | auto ARRIVED_JOB / COMPLETE |
| Asphalt plants | "Wharton Smith Plant", "Big Top Sanford" (seeded) | auto AT_LOAD_SITE / LOADED |
| Concrete plants | (seeded) | same |
| MASCI Yard | (seeded) | auto OFF_SHIFT detection |
| Borrow pits | (seeded) | dirt-haul cycle counting |
| Landfills / dump sites | (seeded) | DUMPING confirmation |

---

## 10 · API / Webhook Readiness

| Capability | Status | Evidence |
|---|---|---|
| Can Motive push data into MASCI? | ✅ YES | `POST /api/integrations/motive/webhook` is mounted + signature-verified |
| Can MASCI poll Motive? | ⚠️ Route exists, service stubbed | `POST /api/integrations/motive/sync-events` returns `awaiting_credentials` |
| Webhooks supported? | ✅ YES | Per-provider signature secret, HMAC verifier, error log, sync log all wired |
| Schedulers available? | ✅ YES | `lib.singleton_scheduler` + existing `_backup_scheduler_loop` pattern — D-1.4 sprint added a reminder loop using exactly this pattern; Motive sync can drop in as another loop |
| Event processors? | ✅ YES | `process_webhook()` is the seam — when filled in, it routes by event type and persists to `motive_events` |
| Insertion point for state automation | ✅ `_record_transition(actor, geo)` already accepts a Motive actor and a geo payload |

---

## 11 · Real Gaps

Only items that truly do not exist. No invented work.

| Gap | Effort | Classification |
|---|---|---|
| **G1 · Real Motive API HTTP client** — replace the 6 stub methods in `motive_service.py` with `httpx.AsyncClient` calls to Motive's API. Authentication is API-key based. | **3–5 days** | MISSING |
| **G2 · Webhook event-type router inside `process_webhook`** — map `vehicle.geofence.entered` → `_record_transition(to_state=AT_LOAD_SITE)`. ~20 event types × 5 LOC each. | **1–3 days** | MISSING |
| **G3 · Geocoding of `jobs_master.location` + seeded plant/yard addresses** — needed before geofences can be auto-created in Motive. One-time script + add `lat`/`lng` columns. | **1 day** | MISSING (additive, not breaking) |
| **G4 · `MotiveService.create_geofence()` helper** — POST to Motive's geofence API when a new job is created. | **0.5 day** | MISSING |
| **G5 · Background sync loop** — periodic `sync_assets` + `sync_events` to handle clock drift / missed webhooks. Uses the existing scheduler pattern from D-1.4. | **0.5 day** | MISSING |
| **G6 · Motive corrective action seeder** — `create_corrective_action_from_event()` is stubbed; needs to call the existing CA-creation endpoint. | **0.5 day** | PARTIALLY BUILT |
| **G7 · UI delta** — none required for Phase 1 of go-live. The existing tiles render the moment data lands. Optional: a small per-row "GPS-validated" badge on `DispatchBoard` when an automatic state transition arrives via Motive (`actor.name === "motive-geofence"`). | **0.5 day** | OPTIONAL |

**Everything else** — UI tiles, mapping screens, health dashboards, webhook receiver, signature verification, event browser, error logs, sync logs, asset/employee mapping CRUD, CSV import/export, demo mode — is **already shipped**.

---

## 12 · Top 10 ROI Roadmap

Ranked by (operational impact ÷ effort) and risk.

| # | Integration | Why it matters | Reuse | New work | Effort | Risk |
|---|---|---|---|---|---|---|
| **1** | **`vehicle.geofence.entered/exited` → automatic dispatch state transitions** | Eliminates driver tap fatigue. Auto-`AT_LOAD_SITE`, `ARRIVED_JOB`, `COMPLETE`. Real-time dispatch board. | `_record_transition` + state events + bell | event-type router branch + Motive API client | **2 days** | LOW |
| **2** | **Real `MotiveService` HTTP client** | Foundation for everything. Until this lands, nothing else is real. | httpx, `_request_with_retry` pattern from MaintainX service | 6 method bodies | **3–5 days** | LOW |
| **3** | **Geocode jobs + plants + yards** | One-shot script. Required before geofences can be created. | jobs schema is additive — `lat`/`lng` columns are pure adds | one-off backfill + Motive geocoding helper | **1 day** | LOW |
| **4** | **Auto-create geofences on job create** | New job → new Motive geofence. Plant + yard are static (one-time create). | existing job-create endpoint already fires bell + email — same hook | `MotiveService.create_geofence()` helper | **0.5 day** | LOW |
| **5** | **GPS-validated dispatch chip on board** | Visual confirmation that a state came from Motive vs driver tap. | `DispatchBoard.jsx` row chip pattern (D-1.1, D-2.5 already there) | one new chip variant | **0.5 day** | LOW |
| **6** | **`vehicle.harsh_brake`/`harsh_accel` → Safety bell + audit** | Real-time unsafe-driving alerts in the Safety portal. | existing `db.tasks` + `dispatch_state_events` audit | event router branch | **0.5 day** | LOW |
| **7** | **`vehicle.dtc_code` → MaintainX work order auto-open** | Engine fault directly opens a shop ticket. | `maintainx_p0.py` already opens work orders | event router branch + payload map | **1 day** | MEDIUM |
| **8** | **Driver mismatch alert** | If Motive says driver X is in the truck but dispatch assigned driver Y → dispatcher bell. | bell rail, `dispatch_state_events` audit | event router branch | **0.5 day** | LOW |
| **9** | **Hours/odometer-based PM scheduling** | Move from calendar-PM to usage-PM. | `equipment_master` already has `hours` field | scheduler hook + threshold config | **2 days** | MEDIUM |
| **10** | **Background `sync_events` loop** | Catch any webhook drops. Hourly poll. | D-1.4 reminder loop pattern | one new loop module | **0.5 day** | LOW |

**Aggregate** ≈ **12–14 dev-days** to convert MASCI from a "Motive-aware platform" into a "Motive-driven dispatch operations centre".

---

## 13 · Final Recommendation

### How close is MASCI to fully Motive-integrated?

**Code-wise: very close.** The integration framework, mapping schema, webhook receiver, signature verifier, UI tiles, dispatch transition seam, and audit pipeline are all **shipped**. The only literal missing pieces are:
1. **Real HTTP calls inside `MotiveService`** (≈ 200 LOC across 6 methods).
2. **Event-type routing inside `process_webhook`** (≈ 150 LOC of switch logic).
3. **A geocoder pass** for job + plant addresses (≈ 80 LOC + a one-off backfill).

That's it. The rest is reuse.

### Suggested shortest path to operational deployment

A single 2-week sprint, executed in this order, delivers an operational Motive-integrated platform:

```
Day  1-2 · G1 · Real MotiveService HTTP client (Motive credentials + httpx)
Day  3   · G3 · Geocode jobs + plants + yards (one-off script + schema add)
Day  4   · G4 · Auto-create geofences on job create
Day  5-6 · G2 · Webhook event-type router (8 highest-value events)
Day  7   · G5 · Background sync loop (matches D-1.4 scheduler pattern)
Day  8   · G7 · GPS-validated chip on DispatchBoard
Day  9   · Field trial with one truck + one job
Day 10   · Hardening + remaining safety events
```

### What NOT to do

- Do **not** rebuild the integration framework — it's already mature.
- Do **not** invent a new fleet collection — `equipment_master` + `asset_mappings` already model Motive ↔ MASCI cleanly.
- Do **not** redesign UI — the empty-state copy and tiles activate themselves once data lands.
- Do **not** stand up a new event store — `motive_events` already exists, indexed on `event_at`.
- Do **not** create a new audit trail — `dispatch_state_events` already accepts `geo` and arbitrary `actor` and `warning_tag`. Motive geofence events drop straight in.

### Final verdict

**MASCI Docs is the operational workflow layer.**
**Motive is the telematics source of truth.**
**The seams already exist.**
**Operationalization is a matter of HTTP plumbing — not platform rebuild.**

---

**End of audit.**

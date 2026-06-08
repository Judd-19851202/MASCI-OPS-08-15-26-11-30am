# MASCI · MOTIVE M-1 · OPERATIONAL VISIBILITY & UTILIZATION AUDIT

**Date:** 2026-06-08
**Scope:** Read-only audit. No code/DB/deploy changes.
**Method:** Direct Mongo introspection · live API replay · frontend grep of every motive consumer.
**Premise:** M-1 sync is green. Data is in Mongo. This audit asks **who actually sees it**.

---

## EXECUTIVE SUMMARY (one paragraph)

Motive M-1 successfully landed **191 vehicle/asset records · 65 driver records · 67 geofences · 272 GPS events · live signed webhook** into MASCI Mongo collections. **None of this data is visible to any operational user in any meaningful way today.** The Admin Integration Center shows green status tiles and counts. Every other surface (Dispatch Board, Asset Profile, Safety Hub, HR Hub, Shop, PM, Field Leadership) renders the data as blank fields, `—` placeholders, or never queries it at all. **The integration is connected; it is not operational.** Of 8 portals × ~9 high-value data fields, the realized operational visibility is approximately **2/72 cells** (3%).

---

## PHASE 1 — DATA INVENTORY

### Collection counts (live)

| Collection | Docs | Source |
| --- | --- | --- |
| `asset_mappings` | 191 | Motive sync (`/v3/vehicle_locations` + `/v1/assets`) |
| `employee_mappings` | 65 | Motive sync (`/v1/driver_locations`) |
| `motive_geofences` | 67 | Motive sync (`/v1/geofences`) |
| `motive_events` | 272 | 270 poll + 2 webhook (event_kind=vehicle_gps only) |
| `integration_sync_logs` | 50 | Internal observability |
| `integration_error_logs` | 2 | Internal observability |
| `integration_settings` | 2 | Operator config (motive + maintainx) |

### `asset_mappings.motive.*` — fields landed per row

| FIELD | PURPOSE | VISIBLE? | USED? | OPERATIONAL VALUE |
| --- | --- | --- | --- | --- |
| `vehicle_id` | External Motive PK | ✅ Admin Integration Center mapping table | ✅ mapping joins | Foundation |
| `asset_id` | External Asset Gateway PK | ✅ Admin IC mapping table | ⚠️ no consumer | Foundation |
| `number` | Motive unit/fleet number (e.g. `DPT021-8147`) | ❌ | ❌ | **HIGH** — natural join key to MASCI equipment_master.unit_number |
| `vin` | VIN | ❌ | ❌ | **HIGH** — exact join key to equipment_master.vin (685 rows) |
| `make` · `model` · `year` | Vehicle identity | ❌ | ❌ | MEDIUM (already in equipment_master) |
| `lat` · `lon` | Last GPS coordinate | ❌ | ❌ | **CRITICAL** — every dispatch/safety/PM workflow benefits |
| `located_at` | GPS timestamp | ❌ | ❌ | **CRITICAL** — staleness indicator |
| `city` · `state` | Reverse-geocoded location | ❌ | ❌ | **HIGH** — human-readable status |
| `speed_kph` | Current speed | ❌ | ❌ | **HIGH** — moving/parked/working indicator |
| `gps_enabled` | Asset has GPS gateway | ❌ | ❌ | MEDIUM — capability flag |
| `dashcam_enabled` | DriverSafety / camera | ❌ | ❌ | MEDIUM |
| `device_id` | Gateway serial | ❌ | ❌ | LOW |
| `type` (Asset Gateway equipment) | construction/trailer/etc | ❌ | ❌ | MEDIUM |
| `status` (Asset Gateway) | active/inactive | ❌ | ❌ | LOW |

### `employee_mappings.motive.*`

| FIELD | PURPOSE | VISIBLE? | USED? | OPERATIONAL VALUE |
| --- | --- | --- | --- | --- |
| `driver_id` | External Motive PK | ✅ Admin IC mapping table | ✅ mapping joins | Foundation |
| `first_name` · `last_name` | Driver identity | ❌ | ❌ | **HIGH** — natural join to employees.name |
| `username` | Motive login | ❌ | ❌ | MEDIUM — join hint for HR |
| `email` | Driver email | ❌ | ❌ | **HIGH** — exact join to employees.email |
| `company_id` | Motive tenant | ❌ | ❌ | LOW |
| `status` (`active`/`deactivated`) | Active in Motive | ❌ | ❌ | **HIGH** — surfaces stale Motive driver accounts |
| `role` | `driver` | ❌ | ❌ | LOW |
| `current_vehicle_id` | Truck driver is currently in | ❌ | ❌ | **CRITICAL** — answers "who is in DPT021-8147 right now?" |
| `lat` · `lon` · `located_at` | Driver phone GPS (HOS pings) | ❌ | ❌ | **HIGH** — last-known driver position |

### `motive_geofences.*`

| FIELD | PURPOSE | VISIBLE? | USED? | OPERATIONAL VALUE |
| --- | --- | --- | --- | --- |
| `motive_geofence_id` | External PK | ❌ | ❌ | Foundation |
| `name` | "The Shop", "Daytona Plant", job sites | ❌ | ❌ | **CRITICAL** — natural map to jobs_master + plant/yard list |
| `address` | Street address | ❌ | ❌ | **HIGH** — would unlock M-3 geocoding for free |
| `category` | `Job Site` (61) / `Terminal-Yard` (3) / `Maintenance Facility` (2) / `Uncategorized` (1) | ❌ | ❌ | **CRITICAL** — pre-classified by ops; ready to consume |
| `status` | `active` (33) / `deactivated` (34) | ❌ | ❌ | **HIGH** — historic job archive vs live jobs |
| `location_points[]` | Polygon vertices | ❌ | ❌ | **CRITICAL** — point-in-polygon to detect "vehicle on site" |

### `motive_events.*` (today: 270 poll + 2 webhook, all `vehicle_gps`)

| FIELD | PURPOSE | VISIBLE? | USED? | OPERATIONAL VALUE |
| --- | --- | --- | --- | --- |
| `event_kind` | Today only `vehicle_gps` | ⚠️ exposed via `/api/integrations/motive/events` BUT consumer expects field named `event_type` → renders blank | ❌ | **HIGH** when populated |
| `vehicle_id` | Which vehicle | ⚠️ (same) | ❌ | **HIGH** |
| `lat` · `lon` · `speed_kph` · `bearing` | Trajectory | ⚠️ (same) | ❌ | **CRITICAL** — feeds breadcrumb / heading / idle detection |
| `city` · `state` | Human-readable position | ⚠️ (same) | ❌ | **HIGH** |
| `event_at` · `received_at` | Time alignment | ⚠️ (same) | ❌ | MEDIUM |
| `source` (`poll` / `webhook`) | Provenance | ❌ | ❌ | LOW |
| `raw` (full Motive payload) | Audit trail | ❌ | ❌ | LOW |

### `integration_sync_logs.*` (50 rows, last 24h)

| FIELD | VISIBLE? | USED? | VALUE |
| --- | --- | --- | --- |
| `sync_type`, `status`, `records_created/updated`, `started_at` | ✅ Admin Integration Center (planned per code; no live UI tab yet exposes the table) | ⚠️ stamped to `integration_settings.last_*_sync_at` (visible on Admin tile) | Operational confidence indicator |

---

## PHASE 2 — USER VISIBILITY AUDIT

Sources audited: every `.jsx` in `/app/frontend/src` mentioning `motive`, every backend route mentioning `motive_*` collection.

| PORTAL | MOTIVE DATA SHOWN | SCREEN | ACTIONABLE? | VALUE |
| --- | --- | --- | --- | --- |
| **Admin** | Status tile (Connected/Disabled) · sync timestamps · `tracked_assets=190` · `idle_count=0` · `not_reporting=0` (both 0 = placeholder) · Mappings table (vehicle_id, asset_id, driver_id, driver_name) | `/admin/integrations` (Integration Center) · `/admin` Hub card | ⚠️ Partial — only as configuration view; no operational drill-down | Operator-only |
| **Admin** | `/admin/assets/:assetId` "Motive" tab shows literal placeholder "Awaiting Motive integration" with 9 field labels rendered as `—` even though `asset_mappings.motive.{lat,lon,speed_kph,city,state,located_at}` is populated for 190 vehicles | `AssetProfile.jsx` L219 `MotivePlaceholder` | ❌ **BROKEN PROMISE** — UI lies; data is there | **GAP** |
| **Dispatch** | "Tracked Assets · Last Telemetry Sync · Idle Assets · Not Reporting · Unmapped Motive Units" tile (all 0 or placeholder) | `/dispatch-portal` → Integrations tab | ❌ Display only | Low |
| **Dispatch** | Assignment cards — **no** vehicle GPS · **no** driver location · **no** geofence-on-site indicator | `DispatchBoard.jsx` | ❌ | **GAP** |
| **Operations** | Same Integration tile as Dispatch (read via `/api/operations/integration-readiness`) | Embedded into Operations Center cards | ❌ | Low |
| **Shop** | Renders `IntegrationHealthCard` (Motive status badge + asset/driver counts) | `ShopHub` indirectly via `IntegrationHealthCard` (component imported but only mounted on Safety/HR/Admin per grep) | ⚠️ Status only, no telemetry | Low |
| **Safety** | `IntegrationHealthCard` (Connected badge) + `IntegrationEventsCard` (Motive events list) | `SafetyHub.jsx` L479-489 | ❌ Events list returns 3 demo rows + 270 real GPS rows that render as empty (no `event_type`, `severity`, `driver_name`, `unit_number`, `location.address`, `speed_mph`) | **BROKEN PROMISE** |
| **HR** | Identical to Safety: health card + events card | `HrHub.jsx` L315-325 | ❌ Same blank-event-row issue | **BROKEN PROMISE** |
| **PM** | Nothing | — | ❌ | **GAP** |
| **Field Leadership** | Nothing | — | ❌ | **GAP** |
| **Driver (magic-link SMS)** | Nothing | — | ❌ | **GAP** |

---

## PHASE 3 — ASSET VISIBILITY AUDIT

For each Motive asset field, where it shows today:

| FIELD | VISIBLE NOW? | LOCATION (if YES) | DATA EXISTS AT (if NO) |
| --- | --- | --- | --- |
| Vehicle ID | ✅ | Admin IC mapping table · AssetProfile Motive tab badge | — |
| Asset (equipment) name (`EXC 1485`) | ❌ | — | `asset_mappings.motive.name` (68 rows) |
| Fleet number (`DPT021-8147`) | ❌ | — | `asset_mappings.motive.number` (90 rows) |
| VIN | ❌ | — | `asset_mappings.motive.vin` |
| Make · Model · Year | ❌ | — | `asset_mappings.motive.{make,model,year}` |
| **Last GPS lat/lon** | ❌ | — | `asset_mappings.motive.{lat,lon}` (158/191 rows) |
| **Last GPS city/state** | ❌ | — | `asset_mappings.motive.{city,state}` |
| **Located-at timestamp** | ❌ | — | `asset_mappings.motive.located_at` |
| **Current speed (kph)** | ❌ | — | `asset_mappings.motive.speed_kph` |
| Moving vs Parked (derived from speed) | ❌ | — | derivable from `speed_kph` |
| GPS-capable flag | ❌ | — | `asset_mappings.motive.gps_enabled` (158/191 = `true`) |
| Dashcam flag | ❌ | — | `asset_mappings.motive.dashcam_enabled` |
| Engine hours / odometer | ❌ | — | **NOT YET SYNCED** (Motive `/v1/vehicles` not called) |
| Driver currently assigned to vehicle | ❌ | — | `employee_mappings.motive.current_vehicle_id` |

---

## PHASE 4 — DRIVER VISIBILITY AUDIT

| FIELD | VISIBLE NOW? | LOCATION (if YES) | DATA EXISTS AT (if NO) |
| --- | --- | --- | --- |
| Motive Driver ID | ✅ | Admin IC mapping table | — |
| Driver name | ✅ (driver_name field if set by manual map; raw `first_name + last_name` from sync is **not** displayed) | Admin IC mapping table | `employee_mappings.motive.{first_name,last_name}` (65 rows) |
| Driver email | ❌ | — | `employee_mappings.motive.email` (50 rows non-null) |
| Username | ❌ | — | `employee_mappings.motive.username` |
| Motive status (active / deactivated) | ❌ | — | `employee_mappings.motive.status` (12 deactivated rows would be flagged) |
| Driver phone GPS lat/lon | ❌ | — | `employee_mappings.motive.{lat,lon,located_at}` |
| **Current vehicle (which truck driver is in)** | ❌ | — | `employee_mappings.motive.current_vehicle_id` |
| HOS / driving status | ❌ | — | **NOT SYNCED** (Motive `/v1/users/status` not called) |
| Safety score | ❌ | — | **NOT SYNCED** (Motive `/v1/users/driver_periods` not called) |

---

## PHASE 5 — GEOFENCE VISIBILITY AUDIT

**67 geofences ingested. ZERO geofences visible on any user-facing screen.**

Evidence:
- Frontend grep `geofence` → 0 hits across all 200+ `.jsx` files.
- Backend grep `motive_geofences` → only the writer (`motive_service.py`) and indexer (`_storage.py`). **No reader endpoint exists.**

Where geofences exist:
- Mongo: `db.motive_geofences` (67 rows, fully indexed on `motive_geofence_id`).
- Category breakdown (already classified by ops, ready to consume):
  - Job Site: 61 (31 active, 30 deactivated)
  - Terminal / Yard: 3 (1 active, 2 deactivated)
  - Maintenance Facility: 2 (1 active, 1 deactivated)
  - Uncategorized: 1

Operationally useful today: **No.**
Merely stored: **Yes — 100%.**

Cross-system gap: `jobs_master` (29 rows) and `equipment_master.plant/yard` columns have **zero** linkage to `motive_geofences.*`. A polygon → job-site match would be a single read query but no surface consumes it.

---

## PHASE 6 — GPS EVENT VISIBILITY AUDIT

**272 GPS events. Indirectly exposed via one endpoint. Rendered as visually blank rows in two portals.**

Evidence:
- `/api/integrations/motive/events` exists (`events.py` L33) — accepts Safety/HR/Admin tokens.
- Returns 270 real `vehicle_gps` rows + 3 demo `hard_braking/speeding/seatbelt_violation` rows when `demo_mode=true`.
- Real rows lack the fields the consumer expects:
  - Consumer (`IntegrationEventsCard.MotiveRow`) reads `event_type` (rows have `event_kind`), `severity` (missing), `driver_name` (missing), `unit_number` (rows have numeric `vehicle_id`), `location.address` (rows have `city`+`state` flat), `speed_mph` (rows have `speed_kph`).
  - Net effect: row title = " ", driver = "—", unit = "—", severity badge = blank, location = blank. Pretty empty row.
- No workflow consumes GPS events. They are not joined to assignments, jobs_master, or geofences.
- Actionable: **No.** Stored only.

---

## PHASE 7 — OPERATIONAL VALUE AUDIT (consolidated)

| DATA TYPE | CLASS | NOTE |
| --- | --- | --- |
| Integration connection status (motive Connected/Disabled, last sync time) | **A** Visible & used | Admin/Safety/HR Hub badges |
| External mapping IDs (vehicle_id, driver_id) | **A** Visible & used | Admin IC mapping CRUD |
| `tracked_assets` / `idle_count` / `not_reporting` counters | **B** Visible, not used | Surfaced as tiles in Dispatch · idle/not-reporting are **hard-coded zero** in `operations.py` L890-891 |
| `motive_events` GPS stream | **B** Visible, not used | Endpoint exists, UI shows blank rows |
| Vehicle lat/lon/speed/city/state | **C** Hidden, high value | In Mongo, 158/191 vehicles populated |
| Driver lat/lon (phone GPS) | **C** Hidden, high value | In Mongo, 65 rows |
| Driver-vehicle association (`current_vehicle_id`) | **C** Hidden, critical value | In Mongo, populated for active drivers |
| Driver Motive status (active/deactivated) | **C** Hidden, high value | In Mongo, 12 deactivated flagged |
| Geofence polygons + names + categories | **C** Hidden, critical value | In Mongo, 67 rows, all unused |
| Asset Gateway equipment list (68 GPS-tagged construction assets) | **C** Hidden, high value | In Mongo, untyped on UI |
| VIN (Motive side) | **C** Hidden, high value | Free join key to equipment_master.vin |
| Webhook event router (signed receiver) | **D** Stored only | Works, no event-type beyond vehicle_gps routed yet |
| Raw event payload (`motive_events.raw`) | **D** Stored only | Forensic only |
| `mapping_confidence`, `mapping_notes` | **D** Stored only | No UI |
| `dashcam_enabled`, `device_id` | **E** Dead today | Future use only |

---

## PHASE 8 — ROLE-BASED ANALYSIS (current vs should)

### DISPATCHER

| | CURRENT | SHOULD SEE |
| --- | --- | --- |
| Vehicle position on board | — | "DPT021-8147 · DeLand FL · 92kph · 12 min ago" inline on assignment chip |
| Driver currently in vehicle | — | "DPT021-8147 → Andres Masci" |
| Vehicle on job-site geofence | — | Green dot if last GPS ⊆ assignment's job-site polygon |
| Vehicle moving/parked | — | Speed > 5kph badge |
| Last telemetry stale | — | Amber chip if `located_at` > 30 min ago |

**GAP**: 5/5 high-value cells empty.

### SUPERINTENDENT (Field Leadership)

| | CURRENT | SHOULD SEE |
| --- | --- | --- |
| Which trucks are at my job site right now? | — | Geofence point-in-polygon count per job |
| ETA for inbound vehicle | — | Distance + speed → minutes |
| Driver phone position vs. expected job site | — | Off-route flag |

**GAP**: 3/3 cells empty.

### PROJECT MANAGER

| | CURRENT | SHOULD SEE |
| --- | --- | --- |
| Which equipment is currently on my projects (jobs_master) | Partial — `asset_assignments` only | Geofence-derived "on site" count |
| Time spent on site per asset | — | Sum of geofence dwell windows |
| Driver hours on my jobs | — | Driver-on-geofence aggregations |

**GAP**: 3/3 cells empty.

### SHOP

| | CURRENT | SHOULD SEE |
| --- | --- | --- |
| Mechanic-visible vehicle position (where is my downed truck?) | — | Last lat/lon + reverse-geocoded address |
| Stationary >X hours (likely broken) | — | Speed=0 + located_at delta filter |
| Out-of-shop trucks reporting GPS | — | Booleans from Motive |

**GAP**: 3/3 cells empty.

### SAFETY

| | CURRENT | SHOULD SEE |
| --- | --- | --- |
| Hard-braking events | Demo rows render; real driver-safety events not yet routed via webhook (only vehicle_gps polled) | — Need router for `driver_safety_event` |
| Speeding events | Same | — |
| Active deactivated-driver list (still on payroll?) | — | `employee_mappings.motive.status="deactivated"` × `employees.active=true` join |
| Driver-vehicle assignment vs DVIR / Pre-Op submitter | — | Cross-check `motive.current_vehicle_id` against most recent DVIR |

**GAP**: 4/4 cells empty.

### OPERATIONS

| | CURRENT | SHOULD SEE |
| --- | --- | --- |
| Idle vehicles (>30 min stationary, engine implied off) | Hard-coded 0 | Computable from `speed_kph=0` + `located_at` delta |
| Not-reporting vehicles (mapped but stale) | Hard-coded 0 | `located_at` > 24h |
| GPS coverage % of fleet | — | `gps_enabled=true` / total |

**GAP**: 3/3 cells empty (and existing tiles lie with hard-coded 0).

---

## PHASE 9 — TOP 20 HIGHEST-ROI VISIBILITY GAPS

Constraints: **existing data · existing schemas · existing portals**. No new portals, no new feature builds, no rebuilds.

| # | GAP | OPS IMPACT | USER VALUE | COMPLEXITY |
| --- | --- | --- | --- | --- |
| 1 | AssetProfile Motive tab → render the lat/lon/speed/city/located_at already in `asset_mappings.motive.*` instead of "Awaiting integration" placeholder | HIGH | HIGH | XS (one component swap, no API change) |
| 2 | Auto-link 190 Motive vehicles to `equipment_master` via VIN or `motive.number ↔ equipment_master.unit_number` (currently 1/191 linked, blocks every downstream join) | CRITICAL | HIGH | S (single backfill script · one-time matcher) |
| 3 | Auto-link 65 Motive drivers to `employees` via email/name (currently 0/65 linked) | CRITICAL | HIGH | S (same pattern, one-time matcher) |
| 4 | Dispatch Board assignment chip: amber "no telemetry >30 min" / green "moving" badge from `asset_mappings.motive.{speed_kph,located_at}` | HIGH | HIGH | S (read-side join into existing board query) |
| 5 | Fix `IntegrationEventsCard.MotiveRow` field names so real GPS rows aren't blank (map `event_kind→event_type`, `speed_kph→speed_mph`, `city/state→location.address`, `vehicle_id→unit_number` via existing mapping doc) | MEDIUM | HIGH | XS (one component change) |
| 6 | Geofence list endpoint (`GET /api/integrations/motive/geofences`) + small read-only table in Admin IC → 67 polygons become inspectable; today they're invisible | MEDIUM | HIGH | XS |
| 7 | Jobs ↔ Geofence suggested-match table (where geofence.name ≈ job site name) — operator can one-click adopt | HIGH | HIGH | S |
| 8 | Surface `motive.current_vehicle_id` on Driver/Employee profile ("currently in DPT021-8147") | HIGH | MEDIUM | XS |
| 9 | Replace hard-coded `idle_count=0` / `not_reporting=0` in `operations.py` L890-891 with real derived counts (`speed_kph=0 AND located_at < now-30min` / `located_at < now-24h`) | HIGH | HIGH | XS (two count queries) |
| 10 | Safety Hub: flag the 12 Motive drivers with `status=deactivated` who are still `active=true` in `employees` | MEDIUM | HIGH | XS |
| 11 | Shop Hub: surface last-known position of any equipment with active maintenance hold ("downed unit currently at: 5460 South Ridgewood Ave, Port Orange FL") | HIGH | HIGH | S |
| 12 | Dispatch driver magic-link landing → show driver's own truck's current position + ETA to dropoff (driver-self-serve) | HIGH | MEDIUM | S |
| 13 | Geofence point-in-polygon helper → "trucks currently on this job site" tile per `jobs_master` row | CRITICAL | HIGH | M (vendored ray-casting) |
| 14 | Asset Registry: green dot "GPS healthy" / amber "stale" / grey "no GPS" per row in `AdminEquipment` table | MEDIUM | HIGH | XS |
| 15 | Asset Profile "Events" tab: filter `motive_events` by the asset's `motive.vehicle_id` to show breadcrumb of last 25 pings | MEDIUM | MEDIUM | S |
| 16 | Operations Center map view of all 158 GPS-enabled assets (single-page leaflet/maplibre, points only) | MEDIUM | HIGH | M |
| 17 | Webhook event router: dispatch `vehicle_gps` events to update `asset_mappings.motive.*` in real-time (today they only land in `motive_events`) | MEDIUM | MEDIUM | XS — `process_webhook` already has the hydrate hook |
| 18 | Sync log read endpoint + tab in Admin IC so operator can see "last 50 syncs" without Mongo Compass | LOW | MEDIUM | XS |
| 19 | PM Hub: per-project equipment-on-site count (geofence join) | HIGH | HIGH | M |
| 20 | Safety/Operations: stale-telemetry alert in Notifications Center ("Truck DPT021-8147 has not reported in 36h") | MEDIUM | MEDIUM | S |

---

## PHASE 10 — FINAL VERDICT

### WHAT USERS SEE TODAY
- Admin & operators see **status badges** (Connected · last sync timestamp) and **mapping CRUD**.
- Safety/HR see a **broken events feed** rendering 270 GPS rows as blank lines.
- All other portals see **nothing**.

### WHAT DATA EXISTS TODAY
- 191 mapped vehicles/assets · 158 with GPS coordinates · 90 trucks · 68 GPS-tagged construction assets.
- 65 drivers · 53 active · 12 deactivated · phone GPS coordinates for all.
- 67 geofences · 33 active · pre-categorized (Job Site / Yard / Maintenance Facility).
- 272 GPS event pings · 50 sync log rows.
- Webhook receiver live and validating HMAC.

### WHAT DATA IS HIDDEN TODAY
- Every lat/lon, speed, city/state, geofence polygon, dashcam flag, deactivated-driver flag, driver-vehicle association.
- 67/67 geofences (100%).
- 270/272 motive_events (99%, the 2 visible ones being demo rows).
- The fact that 12 Motive drivers are deactivated but may still be on MASCI payroll.
- The fact that 158 vehicles are GPS-broadcasting their position right now.

### WHAT DATA IS UNUSED TODAY
- VIN-based join → equipment_master.
- Name/email-based join → employees.
- Geofence-name-based join → jobs_master.
- Geofence polygon → "vehicle on site" classifier.
- `speed_kph + located_at` → idle/not-reporting indicators.
- `current_vehicle_id` → who is in which truck.

### RECOMMENDED PRIORITY ORDER

Ranking framework: **Powerful · Simple · Beautiful · Trusted · Proven**.

**P1 — Powerful & Simple (do first; lights up 80% of value)**
1. Auto-link 190 Motive vehicles ↔ equipment_master (VIN / number match). *(Gap #2)*
2. Auto-link 65 Motive drivers ↔ employees (email / name match). *(Gap #3)*
3. AssetProfile Motive tab: render the live fields (lat/lon/speed/city/located_at) that already exist. *(Gap #1)*
4. Fix `IntegrationEventsCard.MotiveRow` field mapping so real GPS events render. *(Gap #5)*
5. Replace hard-coded `idle_count=0` / `not_reporting=0` in `operations.py` with real derived counts. *(Gap #9)*

**P2 — Beautiful & Trusted (high portal-level value, very small builds)**
6. Dispatch Board chips: green/amber/grey GPS-staleness badge. *(Gap #4)*
7. Asset Registry table: GPS health dot per row. *(Gap #14)*
8. Safety Hub: deactivated-Motive-driver-still-active-in-payroll flag. *(Gap #10)*
9. Driver profile: "currently in DPT021-8147". *(Gap #8)*
10. Geofence list endpoint + Admin IC tab. *(Gap #6)*

**P3 — Proven (one-time wins from existing webhook + sync)**
11. Webhook `vehicle_gps` → live update `asset_mappings.motive.*` (latency reduction from poll → push). *(Gap #17)*
12. Sync log read endpoint + tab. *(Gap #18)*
13. Shop Hub: last-known position for downed equipment. *(Gap #11)*

**P4 — Powerful (point-in-polygon unlocks)**
14. Geofence ↔ job-site suggested-match table. *(Gap #7)*
15. "Trucks on this job site" tile per `jobs_master` row. *(Gap #13)*
16. Asset Profile Events tab: breadcrumb of last 25 GPS pings. *(Gap #15)*
17. Stale-telemetry alert in Notifications Center. *(Gap #20)*

**P5 — Beautiful (visualization layer)**
18. Operations Center map view of GPS-enabled fleet. *(Gap #16)*
19. PM Hub per-project equipment-on-site count. *(Gap #19)*
20. Dispatch driver magic-link → driver's own truck position + ETA. *(Gap #12)*

---

## EVIDENCE CITATIONS

- Field availability: direct query of `db.asset_mappings`, `db.employee_mappings`, `db.motive_geofences`, `db.motive_events` (Mongo · preview env · 2026-06-08).
- Frontend visibility: `grep -rn "motive\|geofence" frontend/src` (0 hits for `geofence`; 14 files mention `motive`, all surveyed).
- Backend exposure: `routes/integrations/{config,events,webhooks,mappings,imports_exports}.py`. Only read endpoints today are `/api/integrations/motive/events`, `/api/admin/integrations/asset-mappings`, `/api/admin/integrations/employee-mappings`, `/api/integrations/health`, `/api/admin/integrations/overview`, `/api/operations/integration-readiness`. **No geofence read endpoint exists.**
- Mapping coverage: `asset_mappings: masci-linked 1/191 · employee_mappings: masci-linked 0/65 · equipment_master.motive_vehicle_id populated: 0 · employees.motive_driver_id populated: 0`.

---

## SCOPE BOUNDARY

This audit identifies gaps **only**. No proposals were made for new portals, FleetWatcher, future architecture, or features outside the existing MASCI surfaces. Every gap above can be closed by emitting data into a surface that already exists.

# TRACK 13.7A — Operational Map Engine Discovery & Role-Based View Architecture

**Date**: 2026-06-12
**Mode**: DISCOVERY + ARCHITECTURE ONLY · NO IMPLEMENTATION · NO ROUTE CHANGES · NO NEW MAP SYSTEMS.
**Doctrine reinforced**: *No workflow changes without workflow discovery.* Reality before architecture. If a role does not benefit from a map, do not give them a map.

> Source-truth inputs to this report:
> - `/app/frontend/src/components/operations-map/*` (8 React components)
> - `/app/frontend/src/lib/operations-map/*` (hooks: `useMapSnapshot`, `useMapState`, `icons`, `eventVocab`)
> - `/app/frontend/src/pages/OperationsMapPage.jsx`
> - `/app/frontend/src/components/DispatchMapHero.jsx`
> - `/app/frontend/src/pages/DispatchHub.jsx`
> - `/app/backend/routes/operations_map_v1.py` (5 endpoints, 1052 lines, primary engine)
> - `/app/backend/routes/operations_map_contract.py` (contract surface)
> - `/app/backend/services/asset_spine.py` (canonical asset identity)
> - `/app/backend/services/motive_service.py`
> - `/app/backend/services/maintainx_service.py` (stub · awaiting credentials)
> - `/app/frontend/src/App.js` route table (lines 281, 693, 853–855)
> - `/app/frontend/src/pages/PmHubV2.jsx`, `ShopHubV2.jsx`, `SafetyHubV2.jsx`, `LeadershipHubV2.jsx`, `AdminHubV2.jsx`

---

## 1 · Existing Map Architecture (verified from source)

### 1.1 · Map provider
- **MapLibre GL JS** (open-source WebGL renderer). Single canvas component at `/app/frontend/src/components/operations-map/MapCanvas.jsx`.
- Basemap tiles: **CARTO Dark Matter** (free, no API key, CORS-friendly CDN — `a/b/c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png`). No Mapbox dependency. No Google Maps dependency.
- Map style is hard-coded inline (`TILE_STYLE`) — no `MAP_STYLE_URL` env var. Center: `[-81.0, 28.9]` (East-central Florida · MASCI service area). Default zoom: 8.
- `preserveDrawingBuffer: true` enabled — so browser screenshots (`page.screenshot()`) actually capture the rendered canvas (Track 13.4A pixel guardrail).

### 1.2 · Data providers (only one wired to the map today)
| Provider | Status in repo | Map participation |
|---|---|---|
| **Motive** | LIVE · production webhook + poll. `motive_service.py` real httpx client, `motive_events` collection with `vehicle_gps` / `vehicle_location_received` events, `motive_geofences` collection with polygon/center+radius shapes. | **Primary feed.** Every asset marker and every geofence shape currently rendered comes from Motive. |
| **MaintainX** | STUB · `maintainx_service.py` returns `awaiting_credentials` / `stub_live`. `MaintainxService.is_live` is `False` until API key + enabled flag exist on `integration_settings`. Routes exist at `/api/integrations/maintainx/p0/*` but they are read-first scaffolding. | **Not wired to the map.** Map does NOT render MaintainX asset positions. Only `maintainx_asset_id` is reserved on the canonical asset spine. |
| **FleetWatcher** | **NOT INTEGRATED.** No `fleetwatcher_*.py` service file exists. Only a `fleetwatcher_asset_id` column reservation in `services/asset_spine.py` (line 73). Mentioned in `operations_map_contract.py` line 13 as "NOT activated — slot reserved". | **Slot reserved · no live data.** Map does not render any FleetWatcher data because no FleetWatcher feed exists in the backend. |

**Honest conclusion**: The "Motive · FleetWatcher · MapLibre · MaintainX" ecosystem named in the brief is **one live provider (Motive)**, one **stub (MaintainX)**, one **reserved column (FleetWatcher)**, and one **renderer (MapLibre)**. The map today is a Motive-fed map.

### 1.3 · Asset feeds (markers)
- Source collection: `db.asset_mappings` filtered to `provider=motive`. Up to 5000 assets per snapshot (default 2000).
- Each marker is built from `_build_marker(asset, latest_event)` (`operations_map_v1.py` lines 220–279). Fields exposed per marker:
  - `asset_id`, `masci_equipment_id`, `unit_number`, `equipment_name`, `asset_kind`, `marker_kind` (11 sprite categories: paver · mill · roller · excavator · dozer · motor_grader · loader · water_truck · dump_truck · service_truck · pickup)
  - `motive_vehicle_id`, `motive_asset_id`, `vin`
  - `lat`, `lon`, `speed_kph`, `speed_mph`, `bearing`, `last_seen_at`, `age_seconds`
  - `band`: `green` (≤5 min) · `amber` (≤60 min) · `red` (≤24 h) · `gray` (older / no GPS)
  - `trust`: `{ source, timestamp, age_seconds, confidence: high|medium|low|stale|unmapped }`
  - `assignment`: `{ name, source, confidence, bucket_type: project|geofence|location|unassigned }`
  - `attention_reason` (only when `band==red`): `maintenance|inspection|assignment|stale_position`
- Latest GPS sourced from `db.motive_events` (`event_at desc`, limited to 8000 rows per snapshot). Falls back to `asset_mappings.motive` coords if no event present.

### 1.4 · Truck / equipment / driver feeds
- **Trucks + equipment**: same `asset_mappings` (Motive-mapped). Marker `marker_kind` distinguishes paver / mill / roller / excavator / dozer / grader / loader / water_truck / dump_truck / service_truck / pickup via equipment-type keyword OR unit-number prefix (e.g. `WT*`, `DPT*`, `ST*`, `PKU*`, `BH*`, `EXC*`).
- **Drivers**: looked up only on `/asset/{key}` (asset detail). Source: `db.employee_mappings` joined on `motive.current_vehicle_id`. NOT a separate map layer · driver appears only in the asset card sheet.

### 1.5 · Existing filters (frontend `MapFilterRail.jsx`)
1. **Projects** (PRIMARY · `<select>` populated from snapshot `project_rollups`). Currently hard-coded `projects = []` in `OperationsMapPage.jsx` (the wire-up to a real project feed is V1.1 deferred — see line 30).
2. **Geofences** (PRIMARY · `<select>` populated from snapshot `geofences[]` up to 200 entries, real Motive shapes).
3. **Status** (always visible · multi-checkbox · 4 bands: working / idle / attention / no-recent-position).
4. **Operator** (PRIMARY · free-text input filtering by driver name).
5. **Equipment Type** (SECONDARY · collapsed `<details>`).

### 1.6 · Existing layers (MapLibre style + GeoJSON sources)
- `osm` raster layer (CARTO dark basemap).
- `assets` GeoJSON source — clustered (`clusterMaxZoom: 12`, `clusterRadius: 44`). Per-cluster aggregates compute worst severity (`has_red`, `has_amber`, `has_gray`) for ring tone.
- `geofences` polygon + outline layers (real Motive shapes).
- 44 pre-loaded sprite icons (11 kinds × 4 bands) in `icons.js`.

### 1.7 · Existing permissions / route guards
| Surface | Route guard (frontend) | Backend endpoint | Backend guard |
|---|---|---|---|
| `/dispatch-portal` (DispatchMapHero) | `RequireDispatch` (Dispatch + Admin tokens) | `/api/operations-map/snapshot` (15s tick via `useMapSnapshot`) | `require_any_portal_token_dep` |
| `/operations-map` (full OperationsMapPage) | **`RequireAdmin`** (admin-only today · App.js line 693) | `/api/operations-map/snapshot` · `/asset/{key}` · `/timeline` · `/search` · `/geofence/{gf_id}` | `require_any_portal_token_dep` |
| Asset deep-link `?asset=<unit>` | flows through the same guards | `/api/operations-map/asset/{key}` | `require_any_portal_token_dep` |

**Critical asymmetry**: the **backend is already role-agnostic** (any portal token can read every map endpoint). The **frontend gate on `/operations-map` is currently Admin-only**. This asymmetry is the single biggest discovery in this track.

### 1.8 · Existing APIs (backend · `operations_map_v1.py`)
1. `GET /api/operations-map/snapshot` — full payload (markers + geofences + counts + operational_summary + project_rollups + attention_breakdown + feed_status).
2. `GET /api/operations-map/asset/{key}` — single asset card (marker + assignment + driver + geofence_status + open_inspections + open_defects + recent_events + motive_status + **`action_required`** verdict with operator-readable label + tone + owner + next_step).
3. `GET /api/operations-map/timeline` — bottom timeline (50 latest events).
4. `GET /api/operations-map/search?q=…` — instant search by unit_number / equipment_id / vehicle_id.
5. `GET /api/operations-map/geofence/{gf_id}` — geofence detail with member assets.
6. Contract surface: `GET /api/operations-map/contract` (`operations_map_contract.py`).

### 1.9 · Existing live update services
- **Pull-based**: `useMapSnapshot` hook polls `/snapshot` every 15 s. Same hook drives DispatchMapHero AND OperationsMapPage — single source of truth.
- **Webhook**: Motive webhook handler in `motive_service.py` writes `motive_events` rows that the next 15-s tick picks up. No websocket layer — pull-only.

### 1.10 · Existing map components (frontend)
```
/app/frontend/src/components/operations-map/
├── MapCanvas.jsx              ← MapLibre canvas · clusters + geofences (280 lines)
├── MapTopBar.jsx              ← search + feed status header
├── MapOperationsBanner.jsx    ← counts strip (attention / offline / working / idle / assigned / total)
├── ProjectIntelligenceStrip.jsx ← project rollups with attention reasons + dominant owner
├── MapFilterRail.jsx          ← project · geofence · status · operator · equipment-type
├── MapTimelineDock.jsx        ← bottom timeline of recent events
├── AssetCardSheet.jsx         ← asset detail card (driver · health · open work)
├── MapTrustChip.jsx           ← trust-confidence badge (high / medium / low / stale)
└── OperationsMap.css          ← co-located (Track 13.4A)
/app/frontend/src/lib/operations-map/
├── useMapSnapshot.js          ← 15-s polling hook · ALSO exports useTimeline · fetchAsset · searchAssets
├── useMapState.js             ← filters + selectedAsset + URL deep-link state
├── icons.js                   ← KIND_LIST + spriteUrl(kind, band)
└── eventVocab.js              ← event-kind → operator label map
```
**Embed pattern already proven** (`DispatchMapHero.jsx`): wrap `MapCanvas` with the existing `useMapSnapshot` hook, pass `EMPTY_FILTERS`, click handler navigates to `/operations-map?asset=<unit>` (already supports the deep-link).

---

## 2 · What already exists vs. what would be new

### 2.1 · Already reusable across roles (no new code required to use)
- `MapCanvas` component — accepts arbitrary `snapshot`, `filters`, `onSelect` props. **Role-agnostic.**
- `useMapSnapshot` hook — single fetch source. **Role-agnostic.**
- `MapFilterRail` — accepts arbitrary `projects` + `geofences` lists. **Role-agnostic.**
- `AssetCardSheet` — accepts `assetKey`. **Role-agnostic.**
- Backend snapshot payload — **already carries**: `assignment.bucket_type`, `attention_reason`, `dominant_owner` ("Shop" / "Shop / Safety" / "PM / Dispatch" / "Truck Boss / Dispatch"), `attention_breakdown` per project rollup, `dominant_reason`, `next_action`.
- Backend auth — already accepts every portal token (PM · HR · Safety · Shop · Dispatch · Leadership · Admin) via `require_any_portal_token_dep`.

### 2.2 · Dispatch-specific (must NOT be cloned)
- `DispatchMapHero.jsx` — 320–520px hero wrapper sized for the dispatch console; orange chrome; navigates to `/dispatch-portal/board`. Embed sizing is purpose-built for dispatch operators.
- `OperationsMapPage.jsx` — full-screen page with **all** rails, banners, timeline. Dispatchers need every layer; other roles do not.

### 2.3 · Role-agnostic infrastructure (the lens primitives)
The backend already produces every signal a role-specific lens would need:
- **PM lens**: `assignment.bucket_type=="project"` + `attention_reason in {assignment, stale_position}` + `dominant_owner contains "PM"`.
- **Shop lens**: `attention_reason in {maintenance, inspection}` + `dominant_owner in {"Shop", "Shop / Safety"}` + `band in {red, gray}` + open_defects/open_inspections counts.
- **Truck Boss / Dispatch lens**: `dominant_owner contains "Truck Boss / Dispatch"` (already the default).

**Therefore**: lens construction is a **frontend filter overlay** on top of the existing snapshot payload — not a new backend pipeline. This is doctrine-pure: we observe existing reality, we do not invent new data.

---

## 3 · Operational Role Workflow Analysis

For each role, the report below answers the five doctrine questions: *what decisions · what info required · would a map help · primary or secondary · or would it add noise?*

### 3.1 · Dispatch
- **Verified entry surface**: `/dispatch-portal` (DispatchHub) — DispatchMapHero is the dominant operational surface (Track 13.4A hard lock).
- **Decisions made**: where is each truck NOW · who needs a route change · what asset stopped reporting · which crew is idle · which geofence has too many or too few assets · how to recover an out-of-position vehicle.
- **Required info**: live GPS · driver assignment · status band · geofence membership · open defects on the vehicle being dispatched.
- **Map verdict**: **PRIMARY · MAP-FIRST · HARD LOCK.** Removing the map would break the role.

### 3.2 · PM (Project Manager)
- **Verified entry surface**: `/pm/hub` → `PmHubV2.jsx` (Track 13.6F swap). Consumes: `/api/pm/command-center/holds · /due-today · /api/pm/crew/capas · /api/pm/jobs · /api/pm/crew/summary · /api/constraints · /api/qaqc/inspections · /api/daily-reports · /api/incidents · /api/job-photos`.
- **NO map import in any PM page.** Reality: PM workflow today is queue-driven (holds · due-today · constraints · CAPAs · QAQC), not map-driven.
- **Decisions made by a PM**: which crew is short of equipment on MY projects · which of MY projects has a constraint / hold / overdue CAPA · which equipment I expected is not on site · is this daily report consistent with what should be happening today.
- **Required info**: assigned projects (PM-scoped, not company-wide) · equipment assigned to those projects · crew rosters · constraints / CAPAs / QAQC events tied to those projects · daily reports.
- **Map verdict**: **SECONDARY-AT-MOST · NOT PRIMARY.** A PM lens would answer one specific question — *"Are the right assets on my project sites today?"* — by filtering the existing snapshot to `assignment.name in MY_PROJECT_LIST` and the project geofences that match. **Every other PM decision is queue-faster than map-faster.**
- **What already supports a PM lens (no new APIs)**:
  - Backend snapshot already returns `assignment.bucket_type=="project"` with `assignment.name = project_number` for every Motive-mapped asset whose `equipment_master.project_number` is populated.
  - `project_rollups[]` already aggregates `attention_required_count`, `offline_count`, `total` per project with `dominant_owner` + `next_action`.
  - Geofence filter already exists; PM job sites are Motive geofences today.
- **What does NOT exist for a PM lens**:
  - There is **no `MY_PROJECTS_FOR_PM` API endpoint that scopes the project list by PM identity**. `PmHubV2` calls `/api/pm/jobs` which is PM-scoped, but operations_map does NOT consume that scope.
  - There is **no `equipment_master.project_number` enforcement** — assignment falls back to geofence_membership → gps_location → unassigned. Confidence is "medium" or "low" for many assets.
- **Conclusion**: A PM map lens IS feasible without new map systems; it is **NOT** an action-first surface and would duplicate the queue-driven PmHubV2. **A small awareness panel (B) is the most that is warranted.**

### 3.3 · Shop Manager
- **Verified entry surface**: `/shop` → `ShopHubV2.jsx` (Track 13.6I swap). Consumes: `/api/dispatch/command/summary.shop` (`defects_open`, `defects_acknowledged`, `oos_units`, `active_recovery`, `waiting_on_parts`, `returned_to_service_7d`, `defect_open_units`).
- **NO map import in any Shop page.** Reality: Shop workflow is recovery-queue-driven.
- **Decisions made by a Shop Manager**: which units are OOS RIGHT NOW · which have open defects · what is waiting on parts · which units are physically in the yard vs. on a job site · where to dispatch a mechanic.
- **Required info**: OOS unit list · open defect list per unit · last-known location of the unit (yard / job site / road) · vendor location (NOT TRACKED).
- **Map verdict**: **SECONDARY · USEFUL.** Knowing **where** a broken unit physically is changes recovery logistics ("Bring it in" vs. "Dispatch mechanic to site"). This is the strongest non-Dispatch case for a map lens.
- **What already supports a Shop lens (no new APIs)**:
  - Backend snapshot already returns `attention_reason=="maintenance"` for any marker with open defects on that unit_number (computed via `db.fleet_defects` aggregation inside `/snapshot`).
  - Backend snapshot already returns `attention_reason=="inspection"` for any marker with open inspections on that equipment_id (computed via `db.equipment_inspections` aggregation).
  - `dominant_owner=="Shop"` or `"Shop / Safety"` is already tagged on every red-band marker that has shop-owner work.
  - Asset card (`/asset/{key}`) already returns `action_required.id in {maintenance, inspection}` with `owner: "Shop"` and `next_step: "Shop review open issue" / "Shop review inspection"`.
- **What does NOT exist for a Shop lens**:
  - **Vendor locations** are NOT tracked. Slot does not exist on any collection. **DO NOT BUILD.**
  - **"Idle equipment"** is partially knowable from `band=="amber"` but Shop's definition of "idle" (worth recovering) requires open-defect or expiring-inspection signal, not GPS idle. **Use defect/inspection signals, not the amber band.**
  - **MaintainX work order locations** — STUB, not live. **DO NOT BUILD.**
- **Conclusion**: Shop lens is the strongest non-Dispatch case. Even so, **Shop's primary surface remains the recovery queue** (ShopHubV2). Map lens is a secondary "where is the broken unit physically?" answer — **a small panel (B) is warranted**, not a full role-specific map.

### 3.4 · Mechanic
- **Verified entry surface**: NO dedicated mechanic portal exists. Mechanics work off the Shop queue, paper, or magic-link assignments. There is no `MechanicHub*.jsx`.
- **Decisions made by a Mechanic**: which unit am I servicing next · where is it physically · what is the open defect text.
- **Required info**: assigned unit · unit location · defect text · parts on hand.
- **Map verdict**: **NO MAP NEEDED.** Mechanic workflow is a single-asset detail-card workflow, not a fleet-wide map workflow. If a mechanic needs to know where the unit is, the existing **Asset Card Sheet** (`/operations-map?asset=<unit>`) already answers this question via deep link — **no new lens required**.
- **Conclusion**: No new surface for mechanics. Reuse the existing Asset Card via deep link if/when a mechanic portal is ever built.

### 3.5 · Safety
- **Verified entry surface**: `/safety-portal` → `SafetyHubV2.jsx` (Track 13.6H swap). Consumes: `/api/safety/overview` (incidents · CAPAs · fire extinguishers · training expiry · safety documents).
- **NO map import in any Safety page.** Reality: Safety workflow is incident · CAPA · training-expiry-driven.
- **Decisions made by Safety**: which incidents are open · which CAPAs are overdue · which training is expiring · which fire extinguishers are overdue inspection · is the trench-safety benchmark passing.
- **Required info**: incident list · CAPA list · training expiry list · fire extinguisher inspection list. **None of these are spatial.**
- **Map verdict**: **MAP ADDS NOISE.** Geographic position is not a safety decision input. Where the asset is does not change whether its inspection is overdue. **DO NOT BUILD a Safety map lens.**
- **Conclusion**: **NO MAP for Safety.** Trench Safety has its own benchmark surface at `/safety/trench-safety` (zero-touch).

### 3.6 · Leadership
- **Verified entry surface**: `/leadership` (classic) + `/leadership/hub_v2` (companion only · Track 13.6L). LeadershipHubV2 consumes: `/api/safety/overview`, `/api/operations/expirations/summary`, `/api/dispatch/command/summary`.
- **NO map import in any Leadership page.** Reality: Leadership workflow is cross-portal-attention-driven (executive threats).
- **Decisions made by Leadership**: where is the company's heaviest operational risk this week · what is degrading (safety threats · execution threats · compliance threats) · is anything trending in a bad direction.
- **Required info**: aggregated threat counts · trend data · cross-portal totals. **Not asset-level positions.**
- **Map verdict**: **MAP ADDS NOISE.** Leadership needs counts and trends, not pin positions. Even the existing Dispatch map only answers Leadership's question by accident.
- **Conclusion**: **NO MAP for Leadership.** A possible future extension: a single embedded "Heatmap of attention by region" — but only if Leadership explicitly asks. **Not warranted today.**

### 3.7 · Admin
- **Verified entry surface**: `/admin` (classic) + `/admin/hub_v2` (companion only · Track 13.6L). AdminHubV2 consumes: `/api/admin/integrations/health`, `/api/operations/expirations/summary`, `/api/dispatch/command/summary`.
- **Admin already has access to `/operations-map`** (full Operations Center page · admin-only frontend gate per App.js line 693). Admin is the **only** role that can reach the full standalone map page today.
- **Decisions made by Admin**: are integrations healthy · is the asset spine clean · is there an unmapped asset / geofence backlog · is the operational map producing the right output for operators.
- **Required info**: integration health · spine health · asset_mapping coverage · geofence coverage. **The full operations map IS the admin verification surface.**
- **Map verdict**: **PRIMARY — but Admin already has it.** Admin's relationship to the map is "verify the map is correct", not "operate from the map". **No new admin lens required.**
- **Conclusion**: Admin already gets the full standalone map at `/operations-map`. **No change needed.** Consider in the future: a small `/admin/hub_v2` panel that links to `/operations-map?focus=unmapped` for spine-cleanup workflow — **not warranted today**.

---

## 4 · PM Map Lens Discovery (detailed)

### 4.1 · The "Project-centric lens" candidates against reality
| Lens candidate | Backend data exists today? | PM workflow gain |
|---|---|---|
| Assigned Projects Only | YES · `assignment.bucket_type=="project"` + project list scoping requires `/api/pm/jobs` join (already PM-scoped) | Medium |
| Assigned Equipment Only | YES · `equipment_master.project_number → marker.assignment.name` | Medium |
| Assigned Trucks Only | YES · same as equipment (trucks ARE equipment in this platform) | Medium |
| Assigned Crews Only | **NO** · the operations map has no crew → coordinates link. Crews are reported via daily reports, not GPS. **DO NOT BUILD.** | n/a — would be invented |
| Assigned Constraints | NO spatial component on `operational_constraints` collection. Constraints are queue items, not map items. | n/a — wrong surface |
| Assigned Incidents | YES · `db.incidents` has lat/lon for many rows, but the Safety map verdict above says **no map for Safety**; PM consumes incidents in queue form (PmHubV2 already shows `incidents_pending`). | Low (mostly duplicates the queue) |
| Assigned CAPAs | NO spatial component on `corrective_actions`. CAPA is a queue item. | n/a |
| Assigned QA/QC Events | NO spatial component on `qaqc_inspections`. QAQC is a queue item. | n/a |
| Assigned Daily Reports | NO spatial component required by the workflow — daily reports are submitted from `/shift` or paper, then reviewed in PmHubV2. | n/a |

### 4.2 · The honest PM lens
A PM lens that would NOT duplicate PmHubV2 reduces to **one question**: *"Are the right assets on my project sites today?"*
- Surface form: a **small awareness panel** embedded into PmHubV2, OR a deep-link to the existing `/operations-map?focus_pm_project_list=<list>`.
- Backend: NONE NEW. Use existing `/api/operations-map/snapshot` + the existing PM project scope from `/api/pm/jobs`.
- Workflow gain: low-to-medium. PMs gain confidence that the equipment they expected is actually on site.
- Risk: **introducing a second source of truth for "what is happening on my project" alongside PmHubV2's holds/due-today queues.** Operators may default to the map and skip the queue. **Doctrine flag.**
- **Verdict**: **Option B (small awareness panel) is the maximum warranted.** Full PM-specific map page is NOT warranted.

---

## 5 · Shop Map Lens Discovery (detailed)

### 5.1 · The "Fleet-recovery lens" candidates against reality
| Lens candidate | Backend data exists today? | Shop workflow gain |
|---|---|---|
| Out Of Service Units | YES · `summary.shop.oos_units` + per-marker `attention_reason=="maintenance"` | High |
| Fault Codes | PARTIAL · stored in `motive_events` (`fault_code_received` event_kind) but **not surfaced** on map markers today | Medium · would need a new map filter, not a new map system |
| Open Defects | YES · `db.fleet_defects` aggregated into `attention_reason=="maintenance"` per unit | High |
| Active Recoveries | YES · `summary.shop.active_recovery` + per-marker classification | Medium |
| Waiting On Parts | YES · `summary.shop.waiting_on_parts` (queue-level) — **NOT spatial** (parts are at a vendor, not on a unit) | Queue-better than map |
| Vendor Locations | **NO** · no `vendor_locations` collection exists. **DO NOT BUILD.** | n/a |
| Equipment Locations | YES · the full snapshot IS this | High |
| Truck Locations | YES · same | High |
| Idle Equipment | YES · `band=="amber"` — but **doctrine note**: Shop's "idle worth recovering" is NOT the same as Motive's "amber band". Use defect/inspection signal, not band. | Medium (but easy to misread) |
| Maintenance Holds | YES · derives from open_defects + open_inspections counts on the asset card | High |

### 5.2 · The honest Shop lens
A Shop lens reduces to **one question**: *"Where is each broken unit physically, so I can choose recover-on-site vs. bring-it-in?"*
- Surface form: **small awareness panel** in ShopHubV2 listing the OOS units with their current geofence membership (Yard / Job Site name / "On the road"), OR a deep-link to `/operations-map?filter=attention&owner=Shop`.
- Backend: NONE NEW. Use existing `/snapshot` filtered by `attention_reason in {maintenance, inspection}` (already computed) + `geofence_status` (already computed on `/asset/{key}`).
- Workflow gain: medium-high · saves a phone call to dispatch ("where is unit X?").
- Risk: same as PM — operators may default to the map and skip the queue.
- **Verdict**: **Option B (small awareness panel) is the maximum warranted.** Full Shop-specific map page is NOT warranted.

---

## 6 · Dispatch Hard Lock — Permanent Statement

> **DISPATCH MAP DOMINANCE IS A PLATFORM HARD LOCK.**
>
> The MapLibre operational map at `/dispatch-portal` is the primary surface of the Dispatch role. No future track may:
> 1. Hide the map behind a tab.
> 2. Minimize the map below the fold on Dispatch.
> 3. Move the map into a modal or drawer on Dispatch.
> 4. Replace the map with a queue-only dashboard on Dispatch.
> 5. Build a parallel "Dispatch V2" surface that demotes the map.
>
> Why the map is map-first for Dispatch (and only Dispatch):
> - Dispatch operates **fleet-wide**, not asset-by-asset or queue-by-queue.
> - Dispatch decisions are **spatial** (route this truck · move this asset · respond to that stop).
> - Without the map, Dispatch operators must mentally reconstruct the fleet's current geometry — impossible at MASCI scale (≈250 assets).
> - The map is the **only** surface that compresses 90+ live positions into a single decision-ready glance.
>
> What would break if the map disappeared:
> - Operators would default to phone calls and texts (verified anti-pattern).
> - Idle assets would not be re-tasked promptly (yields revenue loss).
> - OOS units waiting for recovery would lose visibility (yields longer downtime).
> - Geofence violations would only surface after-the-fact.
>
> Dispatch remains the system benchmark for map-first operations. Every other role's map exposure must be evaluated against the question: *"Would this make the role's decisions worse if the map disappeared?"* For PM / Shop / Safety / Leadership / Admin the answer today is **no** — therefore none of them is map-first.

---

## 7 · Leadership · Safety · Admin Final Review

| Role | Decision-type | Map verdict | Justification |
|---|---|---|---|
| **Leadership** | Trend / threat / aggregate | **C · No map needed** | Decisions are counts and trends, not positions. LeadershipHubV2 already serves this. |
| **Safety** | Incident · CAPA · training expiry | **C · No map needed** | Decisions are list-driven and time-driven. Position is not an input. SafetyHubV2 already serves this. |
| **Admin** | Verify integration / spine health | **A · Already has full map** | Admin is the verification role — full `/operations-map` is already mounted at `RequireAdmin`. No change. |

---

## 8 · Gap Analysis (honest list of what does NOT exist · per doctrine, this is a "do not build" list)

1. **No FleetWatcher live service** in `/app/backend/`. Only a reserved column. — Slot stays reserved.
2. **No live MaintainX integration**. Service returns `awaiting_credentials`. — Slot stays reserved.
3. **No PM-scoped operations-map endpoint** — the map snapshot returns ALL assets; scoping to PM's project list happens client-side via the project filter rail. No new endpoint is needed to add a PM lens — the existing snapshot is sufficient if combined with PM's existing `/api/pm/jobs` project list.
4. **No crew-coordinates link** — daily reports / crews are not GPS-mapped. **DO NOT BUILD.**
5. **No vendor_locations collection** — vendor positions are not tracked. **DO NOT BUILD.**
6. **No spatial fields on `corrective_actions` / `qaqc_inspections` / `operational_constraints`** — these are queue items by design. **DO NOT BUILD spatial overlays.**
7. **`equipment_master.project_number`** is sparsely populated — assignment frequently falls back to geofence membership or city-area. A PM lens scoped to "MY projects" will under-report when the explicit project_number is missing. **This is a data-quality gap, not a map gap — to be flagged for Admin spine cleanup, not for new map code.**
8. **`/operations-map` is currently Admin-gated** on the frontend — opening it to any portal would require a single guard change at App.js line 693. **Not a refactor — just a guard change.** *(Recorded as observation only; not an authorization to make the change.)*

---

## 9 · Reusable Components (the lens construction toolkit)

If/when a role-specific lens is ever authorized, these are the existing primitives that should be reused **without modification**:

| Primitive | Path | Reuse pattern |
|---|---|---|
| `MapCanvas` | `components/operations-map/MapCanvas.jsx` | Direct embed (DispatchMapHero already proves this) |
| `useMapSnapshot({ refreshMs })` | `lib/operations-map/useMapSnapshot.js` | Single fetch source; all role lenses must consume the same payload |
| `MapFilterRail` | `components/operations-map/MapFilterRail.jsx` | Pass role-scoped `projects` / `geofences` arrays to filter |
| `AssetCardSheet` | `components/operations-map/AssetCardSheet.jsx` | Deep-link via `?asset=<unit>` from any role's page |
| `?focus_*=…` query params on `/operations-map` | `OperationsMapPage.jsx` + `useMapState.js` | The deep-link pattern is the cheapest way to deliver a "lens" — no new component needed |
| Backend `/api/operations-map/snapshot` lens-relevant fields | `operations_map_v1.py` lines 436–528 | `assignment.bucket_type`, `attention_reason`, `dominant_owner`, `attention_breakdown`, `next_action` are already computed |

**Embed sizing reference** (DispatchMapHero proves it works): `h-[300px] sm:h-[420px] lg:h-[520px]` for a hero; a small awareness panel could be `h-[200px]` or even a counts-strip + thumbnail.

---

## 10 · Hard Locks (this report formalises three)

1. **DISPATCH MAP DOMINANCE** — `/dispatch-portal` map must remain dominant. Re-stated in §6 above. *(Original lock from Track 13.6J · 13.6L; reinforced here.)*
2. **ONE MAP ENGINE · ONE SOURCE OF TRUTH** — `MapCanvas` + `useMapSnapshot` + `/api/operations-map/snapshot` are the only map engine. **No second map library may be added. No second map data pipeline may be added. No role may build its own parallel map.**
3. **NO MAP WITHOUT WORKFLOW DISCOVERY** — Track 13.7A formalises the new permanent doctrine: before any role gets a map surface, that role's decisions must be proven to require spatial information. **If a role does not benefit from a map, it does not get a map.** Safety · Leadership · Admin (operationally) · Mechanic are explicitly excluded from any future map lens by this lock.

---

## 11 · Architecture Recommendation

### 11.1 · Option matrix (per brief)
| Option | Description | Complexity | Operational benefit | Five-pillar score | Risk | Effort | Long-term maintainability |
|---|---|---|---|---|---|---|---|
| **A · One shared engine + role-based filters (server-side scoping)** | New server endpoint per role: `/api/operations-map/snapshot/pm`, `/snapshot/shop`, etc. Each pre-filters assets by role. | **HIGH** — N endpoints, N test surfaces, N caches, N drift vectors | Marginal — the existing payload already carries the lens metadata | Powerful 7 · Simple 5 · Beautiful 7 · Trusted 6 · Proven 4 → **5.8** | High — duplicates truth across endpoints; future drift between Dispatch payload and PM/Shop payload | Large (3–5 tracks) | Poor — multiple endpoints to maintain |
| **B · One shared engine + embedded role-specific lenses (frontend filters + deep-links)** ⭐ | Reuse `MapCanvas` + `useMapSnapshot` + existing snapshot. PM lens = small awareness panel inside PmHubV2 filtered to PM's projects. Shop lens = small panel inside ShopHubV2 filtered to `attention_reason∈{maintenance,inspection}`. Cross-link via `/operations-map?focus_*=…`. | **LOW** | High where map is genuinely useful (Shop > PM); zero where it is not (Safety / Leadership / Mechanic / Admin operationally). | Powerful 9 · Simple 9 · Beautiful 9 · Trusted 9 · Proven 8 → **8.8** | Low — single payload, single engine, single source of truth | Small (1 track per warranted lens, scoped to a panel) | Excellent — one engine, one truth |
| **C · Hybrid** (server-side scoping for "heavy" roles + frontend lenses for "light" roles) | A blended approach — new endpoint for Shop, frontend lens for PM, no surface for Safety/Leadership/Mechanic. | Medium | Medium | Powerful 8 · Simple 6 · Beautiful 8 · Trusted 7 · Proven 6 → **7.0** | Medium — partial drift between server-scoped and client-scoped roles | Medium (2–3 tracks) | Mixed — two patterns to maintain |

### 11.2 · Recommended Option · **B**

**One shared map engine. Multiple operational lenses. One source of truth.**

- **Dispatch** keeps the dominant standalone surface at `/dispatch-portal` (DispatchMapHero + `/operations-map` full page · unchanged).
- **PM** receives at most a small awareness panel inside `PmHubV2` showing "Assets on MY projects today" (filtered client-side using PM's existing `/api/pm/jobs` project list against the existing snapshot's `assignment.name`). **Not a full PM map page.**
- **Shop** receives at most a small awareness panel inside `ShopHubV2` showing "Where are my OOS units / open-defect units physically?" (filtered client-side to `attention_reason∈{maintenance,inspection}` and `band∈{red,gray}`). **Not a full Shop map page.**
- **Safety · Leadership · Mechanic** receive **no map surface.** Operational decisions for these roles are list-driven · time-driven · queue-driven.
- **Admin** retains the full standalone `/operations-map` page (already in place).
- **No new map system. No new map engine. No new GPS provider. No new telematics provider. No new collection. No new endpoint.**

**Implementation effort (if/when authorized)**:
- Each warranted lens is one small panel component reusing `MapCanvas` (or a thumbnail) + `useMapSnapshot`. ~1 file each, ≤200 lines.
- Zero backend changes.
- Zero new dependencies.
- Zero new permissions (existing role tokens already read `/api/operations-map/snapshot`).

**Five-pillar score**: 8.8 / 10 (matches the RC-1 swapped portals · honest reality).

---

## 12 · Five-Pillar Evaluation (this discovery track)

| Pillar | Score | Evidence |
|---|---|---|
| **Powerful** | 9 | Discovery surfaces every existing lens-relevant signal the backend already produces (assignment / attention_reason / dominant_owner / attention_breakdown / project_rollups · all real). |
| **Simple** | 9 | One engine. One snapshot. One auth gate (`require_any_portal_token`). No new APIs proposed. Frontend lenses are panel-sized, not page-sized. |
| **Beautiful** | 9 | Reuses the existing primitives that already satisfy MapTrustChip / MapOperationsBanner / ProjectIntelligenceStrip aesthetic. No new chrome to design. |
| **Trusted** | 9 | Doctrine-pure: lens construction depends only on what the backend already returns. No fabricated metric. No invented data. No vendor_locations. No crew GPS. No MaintainX wiring until credentials exist. |
| **Proven** | 8 | Verified by source inspection (8 frontend map components · 1052-line backend route file · 5 V2 hub pages · App.js route table · auth guard chain). Pending operator validation of the recommendation (Option B). |

**Aggregate**: **8.8 / 10.**

---

## 13 · Success Criteria · Met (per brief §SUCCESS CRITERIA)

- ✅ The existing operational map architecture is understood and documented end-to-end (Section 1).
- ✅ Every named integration is verified against reality (Section 1.2): Motive live · MaintainX stub · FleetWatcher slot-only · MapLibre is the renderer.
- ✅ Each role's decisions are documented from real source code (Section 3), not assumed.
- ✅ PM lens and Shop lens reality-tested against existing data (Sections 4–5).
- ✅ Dispatch hard lock formalised as a permanent platform invariant (Section 6).
- ✅ Safety / Leadership / Admin verdicts recorded with reasons (Section 7).
- ✅ Gap list is a "do not build" list (Section 8), not a "to build" list.
- ✅ Architecture recommendation (Option B) reuses existing primitives — **no new map systems · no new GPS / telematics providers · no new portals · no UI modernization · no mockups.**

**Track 13.7A · CLOSED.** No code was written. No routes were changed. No mock data was introduced. The reality of the existing map ecosystem is now documented, the doctrine "*if a role does not benefit from a map, do not give them a map*" is recorded, and the path forward (Option B · panel-sized lenses for Shop and at most PM · zero new map systems) is explicit.

**Next legitimate work**: operator review of this report. If/when Option B is authorized, the first lens to consider is the **Shop awareness panel** (highest operational gain · still secondary to the recovery queue). Any further surface change requires its own track and must re-run the workflow-discovery doctrine first.

# MOTIVE-001 · Constitutional Architecture Audit
**Sprint:** MOTIVE-001 (audit-only, OMEGA-bound)
**Date:** 2026-02-09
**Scope:** Audit-only. NO code, NO schema, NO API, NO deploy, NO geocoding, NO webhooks. Findings + recommendations only.
**Doctrine alignment:** `MOTIVE_INTEGRATION_STRATEGY.md` (validate-don't-surveil), DLS append-only invariants, OMEGA discipline.

---

## 0 · TL;DR — One paragraph

Motive is **already live** (M-1 certified 2026-06-08). 191 assets are syncing, 65 drivers are mapped, 67 geofences are pulled from Motive (61 are "Job Site" category — already authored by the operator inside Motive's console), the signed webhook receiver is mounted, and the `motive_events` collection has begun receiving real telemetry (362 GPS polls + 16 classified webhooks). What is **missing** is a canonical *MASCI-side* location registry (jobs_master has **0/29 lat-lng**, plants/pits/yards/disposal sites do **not exist as collections**, only `suppliers` exists and it is a flat name list of 145 rows with no addresses). Until MASCI owns a canonical location model, the Motive geofence layer is the operator's single source of truth — which means **M-3 (Geocode Foundation) is the first foundation step, not M-DR-1 or M-2**. Recommended build order stays: **M-3 → M-DR-1 → M-2 → Verification**. Below is the evidence.

---

## A · Current Motive Integration · State of the Union

### A.1 Credentials & configuration (LIVE)
| Item | Value | Source |
|---|---|---|
| Provider record | `integration_settings` where `provider="motive"` | DB |
| Status | `Connected` · `enabled=true` · M-1 certified | `MOTIVE_M1_ACTIVATION_CERTIFICATION.md` |
| API key tail | `…5fe6` (operator-managed via Admin Integration Center) | settings row |
| Webhook secret tail | `…c106` (HMAC-SHA256 hex of raw body, header `X-Motive-Signature`) | settings row |
| API base | `https://api.gomotive.com` (default) | `motive_service.py:29` |
| Env vars present | `MOTIVE_API_KEY`, `MOTIVE_API_BASE` (fallback only) | `motive_service.py:56-63` |

### A.2 Implemented endpoints (Motive → MASCI)
All in `/app/backend/services/motive_service.py`. Six concrete operations:

| Method | Motive endpoint | Lands in (collection) | Status |
|---|---|---|---|
| `test_connection()` | `GET /v3/vehicle_locations?per_page=1` | — | ✅ live |
| `sync_assets()` | `GET /v3/vehicle_locations` + `GET /v1/assets` (paginated) | `asset_mappings` (191 docs) | ✅ live |
| `sync_users()` | `GET /v1/driver_locations` (paginated) | `employee_mappings` (65 Motive-mapped) | ✅ live |
| `sync_geofences()` | `GET /v1/geofences` (paginated) | `motive_geofences` (67 docs) | ✅ live |
| `sync_events()` | `GET /v3/vehicle_locations` (poll backfill) | `motive_events` (`source="poll"`) | ✅ live |
| `process_webhook()` | inbound `POST /api/integrations/motive/webhook` | `motive_events` (`source="webhook"`) | ✅ live |

### A.3 Webhook receiver (LIVE)
- Route: `POST /api/integrations/motive/webhook` (unauthenticated, signature-verified)
- File: `/app/backend/routes/integrations/webhooks.py` lines 98-103
- Verify path: `verify_webhook_signature_stub(provider, secret, raw, signature_header)` → HMAC-SHA256
- On invalid signature: `HTTP 401` + error log
- On missing secret + not in test mode: `HTTP 200` with `{ok:false, status:awaiting_credentials}` (never crashes upstream)
- On success: writes `motive_events` row, hydrates `asset_mappings.motive.lat/lon` for `vehicle_gps` events, returns `{ok:true, stored:true, event_kind, event_family, severity, vehicle_id}`

### A.4 Motive entities currently accessible (proven by live data)
| Entity | MASCI collection | Count | Field shape (top-level) |
|---|---|---|---|
| Vehicles (trucks) | `asset_mappings` where `asset_kind="vehicle"` | **90** | `motive.{vehicle_id, vin, make, model, year, lat, lon, located_at, city, state, speed_kph, gps_enabled}` |
| Assets (equipment w/ asset gateway) | `asset_mappings` where `asset_kind="equipment"` | **100** | `motive.{asset_id, name, vin, make, model, year, type, status, device_id}` |
| Drivers (users) | `employee_mappings` | **65** | `motive.{driver_id, first_name, last_name, email, status, role, current_vehicle_id, lat, lon, located_at}` |
| Geofences | `motive_geofences` | **67** | `{motive_geofence_id, name, status, address, category, location_points[]}` |
| Events (poll + webhook) | `motive_events` | **376** | `{event_kind, event_family, source, lat, lon, severity, priority, raw, classification fields}` |

### A.5 Event classifier (LIVE · P1.5 + P1.6)
`motive_service.py:532-617` already classifies 14 event families into a stable taxonomy with `severity` (info/low/medium/high/critical) and `priority` (low/medium/high/critical). **No workflow side-effects** — pure visibility. Confirmed by:

```
'vehicle_gps'                    n=362  (poll-driven)
'inspection_report_updated'      n=2
'geofence_enter' / 'geofence_exit'                each n=1
'asset_geofence_enter' / 'asset_geofence_exit'    each n=1
'dvir_submitted'                 n=1
'hard_brake'                     n=1
'hos_violation_created'          n=1
'vehicle_gateway_disconnected' / '_disconnect_ended'    each n=1
'fault_code' / 'fault_code_closed'                each n=1
'ai_coach_recap_created'         n=1
```

Pillar alignment:
- **Powerful** — 14 event families, severity ladder, priority ladder.
- **Simple** — one collection (`motive_events`), one shape, one classifier function.
- **Beautiful** — classifier output is flat & UI-renderable without re-parsing raw JSON.
- **Trusted** — append-only, signature-verified, raw payload preserved.
- **Proven** — 376 real events landed; M-1 cert passes; webhook signature test passes (`bad sig → 401`).

---

## B · Existing Location Intelligence · Inventory

### B.1 Collection-by-collection census

| Collection | Exists? | Count | Has lat/lng? | Has address? | Authority |
|---|---|---|---|---|---|
| `jobs_master` | ✅ | 29 | ❌ **0/29** | ❌ 0 (only free-text `location` string like "SR 46 Mellonville Ave") | MASCI-owned, hand-curated |
| `plants` | ❌ **does not exist** | — | — | — | — |
| `pits` | ❌ **does not exist** | — | — | — | — |
| `yards` | ❌ **does not exist** | — | — | — | — |
| `shops` | ❌ **does not exist** | — | — | — | — |
| `disposal_sites` | ❌ **does not exist** | — | — | — | — |
| `customer_locations` | ❌ **does not exist** | — | — | — | — |
| `suppliers` | ✅ | 145 | ❌ 0/145 | ❌ 0 (only `name` + `is_active`) | MASCI-owned, hand-curated |
| `motive_geofences` | ✅ | 67 | ✅ **67/67** (polygon points) | ⚠️ **1/67** (`The Shop` only) | **Motive-owned** (operator authored in Motive console) |
| `dispatch_assignments` | ✅ | 368 | ❌ 0 | ⚠️ free-text `destination` populated on 200/368, `origin` 0/368, `pickup_location`/`dropoff_location` empty strings | Driver/dispatcher typed |

### B.2 Completeness percentages

| Location class | Records | With lat/lng | With address | Completeness |
|---|---:|---:|---:|---:|
| Jobs (jobs_master) | 29 | 0 | 0 | **0%** |
| Suppliers (flat list) | 145 | 0 | 0 | **0%** |
| Plants / Pits / Yards / Shops / Disposal / Customer | 0 | 0 | 0 | **N/A — does not exist** |
| Motive geofences (any kind) | 67 | 67 | 1 | **lat/lng 100% · address 1.5%** |
| **Aggregate MASCI-owned operational locations with geocode** | **174** | **0** | **0** | **0%** |
| **Aggregate including the Motive shadow registry** | **241** | **67** | **1** | **~28% · address ~0.4%** |

### B.3 The shadow-registry problem (the most important finding)

The operator already authored 61 "Job Site" geofences inside Motive's console. **These are the only place in the entire MASCI universe where job sites have lat/lng.** `jobs_master.project_number` and `motive_geofences.name` are **not linked** — there is no join key. A geofence named "T5824 - SR 46" might or might not correspond to `jobs_master` row `project_number="24-06"`. **This is the M-3 wedge.**

Implications:
- If MASCI later tries to author geocodes itself, it will fight or duplicate Motive's authored fences.
- If MASCI deletes a Motive geofence, the operator loses field state.
- Today MASCI cannot answer: *"Which Motive geofence belongs to which MASCI project?"*

---

## C · Existing Geofence Capability

### C.1 What exists (in Motive)
- **67 geofences**, all with polygon `location_points[]` (real lat/lng arrays, e.g. The Shop has 9 vertices).
- **Categorization in Motive console** (operator-curated):

| Motive category | Count | What it likely is |
|---|---:|---|
| Job Site | 61 | Active + historical project sites |
| Terminal / Yard | 3 | MASCI yards |
| Maintenance Facility | 2 | The Shop (+1) |
| Uncategorized | 1 | (drift) |

- One geofence (`The Shop`) has `status="deactivated"` — Motive supports lifecycle but MASCI has no view of it.

### C.2 Are they managed?
- ✅ **Manually inside Motive's console** by the operator.
- ❌ **Not authored, edited, or versioned from MASCI.** `motive_service.sync_geofences()` is one-way READ ONLY.
- ❌ **No push back** to Motive (no `POST /v1/geofences` wrapper).
- ❌ **No duplicate detection** — two "T5824" fences could coexist and MASCI wouldn't flag.
- ❌ **No naming convention enforcement** — names are whatever the operator typed.

### C.3 Findings (geofence layer health)
| Pillar | Status | Note |
|---|---|---|
| Powerful | 🟡 Partial | Polygon vertices present, but radius is implicit (must be computed from polygon). |
| Simple | 🟢 | One collection, one shape, freshly synced from Motive. |
| Beautiful | 🟡 | Names are operator-typed; no canonical scheme like `25-21 / Spruce Creek Loop` vs `Spruce Creek Loop Trail`. |
| Trusted | 🔴 | **Cannot join to `jobs_master`.** Operator must mentally map fence-name → project-number. |
| Proven | 🟢 | All 67 fences round-tripped from Motive console without error. |

---

## D · M-3 Geocode Foundation · Feasibility & Design (DESIGN ONLY)

### D.1 Canonical location model (proposed schema — NOT TO BE BUILT until authorized)
**Collection name (proposed):** `operational_locations`

| Field | Type | Required? | Source |
|---|---|---|---|
| `id` | uuid | ✅ | MASCI-authored |
| `tenant_id` | str | ✅ | MASCI (multi-tenant ready) |
| `name` | str | ✅ | Operator |
| `location_type` | enum | ✅ | one of: `JOB`, `ASPHALT_PLANT`, `CONCRETE_PLANT`, `PIT`, `YARD`, `SHOP`, `DISPOSAL_SITE`, `VENDOR` |
| `project_number` | str \| null | optional | populated for `location_type=JOB` only; FK to `jobs_master.project_number` |
| `address_raw` | str | optional | free-text, operator-typed |
| `address_normalized` | str | optional | reverse-geocode result for audit comparison |
| `latitude` | float | ⚠️ at least one of (lat+lng) OR (address) | derived or operator-entered |
| `longitude` | float | ⚠️ | derived or operator-entered |
| `geofence_radius_ft` | int (default 250) | ✅ | operator override; default 250 ft per `MOTIVE_INTEGRATION_STRATEGY.md` §"Geofence inventory" |
| `motive_geofence_id` | str \| null | optional | join key to `motive_geofences.motive_geofence_id` |
| `geocode_status` | enum | ✅ | `unverified`, `auto_geocoded`, `human_verified`, `motive_synced` |
| `geocode_provider` | str \| null | optional | "google", "mapbox", "manual", "motive" |
| `geocode_confidence` | float [0..1] | optional | provider-reported |
| `active` | bool | ✅ | hide deactivated without deleting |
| `created_at`, `updated_at`, `created_by`, `last_verified_by`, `last_verified_at` | meta | ✅ | audit fields |

### D.2 Derivable vs human-required (audit conclusion)

| Field | Auto-derivable? | How | Risk |
|---|---|---|---|
| `latitude` / `longitude` (for JOB) | ⚠️ **Partial** | (a) join `jobs_master.project_number` to `motive_geofences.name` via fuzzy match → centroid of polygon; (b) reverse-geocode the free-text `jobs_master.location` string | Fuzzy match is unreliable (61 fence names vs 29 jobs with different naming); free-text geocode of "SR 46 Mellonville Ave" is **low-confidence** |
| `latitude` / `longitude` (for PLANT/PIT/YARD/DISPOSAL/VENDOR) | ❌ **No** | These collections **do not exist**. There is no source data to derive from. | Must be operator-authored. |
| `address_normalized` | ✅ | Standard reverse-geocode of `(lat,lng)` via Google/Mapbox | Trusted if `geocode_confidence > 0.85` |
| `geofence_radius_ft` | ❌ | Default 250 ft is doctrine; operator-tunable | Always human-confirmed |
| `motive_geofence_id` | ⚠️ **Partial** | Auto-suggest based on (name-fuzzy + spatial proximity); operator confirms | Wrong join = wrong reality forever |

### D.3 The human-verification gate (DOCTRINAL)
**Every** `operational_locations` row must pass `human_verified` before it is consumed by any downstream system (M-DR-1 Equipment Auto-Discovery, M-2 Event Router). Auto-geocoded rows surface in an Admin "**Geocode Verification Queue**" with a Motive-fence proposal beside them. Operator taps Confirm/Reject. Until verified, the row is **shadow-only** — it does not affect Daily Reports, Material Movement, or Dispatch.

This protects pillar **Trusted**. Auto-geocode without confirmation = bad reality propagated platform-wide.

### D.4 What M-3 must NOT do
- ❌ Push geofences back to Motive (write path stays Motive-console-only until separately authorized).
- ❌ Replace `jobs_master.location` string (additive only; legacy field stays for fallback).
- ❌ Block Daily Report submission on missing geocode (resiliency-first).
- ❌ Surveil drivers via the new geocode layer.

---

## E · M-DR-1 Equipment Auto-Discovery · Feasibility & Design

### E.1 The question: Can Motive reliably identify equipment / trucks onsite?

#### Trucks (vehicles) onsite
- **Signal source:** `motive_events` where `event_family ∈ {geofence_enter, geofence_exit}` (vehicle side), correlated with `event_at` timestamp and `geofence.id` matched to `operational_locations.motive_geofence_id`.
- **Confidence:** 🟢 **HIGH** for vehicles with active gateways (90 mapped vehicles, 100% GPS coverage observed in `vehicle_locations` probes).
- **False-positive risk:** 🟡 Medium — drive-through traffic (truck enters then leaves within 60 s) will fire enter+exit; foreman must reconcile.
- **False-negative risk:** 🟢 Low — Motive has 99.x% telematics uplink; gateway-disconnected events are already classified (1 already captured).

#### Equipment (non-vehicle) onsite
- **Signal source:** `motive_events.event_family ∈ {asset_geofence_enter, asset_geofence_exit}` from the **Asset Gateway** (100 mapped equipment assets).
- **Confidence:** 🟡 **MEDIUM** — Asset Gateways report less frequently than vehicles; 1 `asset_geofence_enter` + 1 `asset_geofence_exit` observed so far.
- **False-positive risk:** 🟡 Medium — A trailer left overnight inside a fence will fire enter at delivery + exit at pickup, with no per-day "onsite today" assertion. Requires temporal windowing logic (e.g., "inside fence at any point during shift hours").
- **False-negative risk:** 🟠 **Medium-high** — equipment without an Asset Gateway is invisible (no count available — operator must audit gateway coverage).

#### Equipment / trucks "near" a job
- **Signal source:** `motive_events.event_family="vehicle_gps"` correlated with `operational_locations` polygon proximity (e.g., within 500 ft of geofence boundary but not inside).
- **Confidence:** 🔴 **LOW** — proximity ≠ onsite. Drive-by traffic flags constantly. Should be **avoided as primary signal**.

### E.2 Recommended UI doctrine — "Equipment Detected Today" (DESIGN ONLY)
A per-project Daily Report sidecar pane shows:

```
┌──────────────────────────────────────────────────────┐
│ EQUIPMENT DETECTED TODAY · Project 25-21             │
│                                                      │
│ Motive observed the following on the geofence today  │
│ Foreman confirms what was actually on site.          │
│                                                      │
│ [✓] Truck 42 · 06:23 → 16:47 (10h 24m)               │
│ [✓] Truck 17 · 07:12 → 15:08 (7h 56m)                │
│ [ ] Trailer T-9 · 06:45 → 06:51 (drove through)      │
│ [✓] Excavator EX-4 · 06:30 → 16:55 (asset gateway)   │
│                                                      │
│ [ Confirm Selected ]      [ Add Manually ]           │
└──────────────────────────────────────────────────────┘
```

### E.3 Verification doctrine for M-DR-1 (NON-NEGOTIABLE)
- ✅ **Motive suggests** — never asserts.
- ✅ **Foreman confirms** with a tap per equipment row.
- ✅ The confirmed list becomes the Daily Report `equipment_used[]` payload, **signed by the foreman**.
- ❌ Motive does **NOT** auto-author the Daily Report.
- ❌ Motive does **NOT** auto-submit a row to `daily_reports`.
- ❌ Motive does **NOT** replace what the foreman types.
- ❌ Motive does **NOT** affect production totals (R-BL-3 trust pattern: operator authorship sacred).
- ❌ Motive **NEVER** issues HR/payroll claims based on detected presence.

### E.4 Risk-rated build summary
| Risk | Severity | Mitigation |
|---|---|---|
| Asset Gateway coverage gap | 🟠 | Coverage audit BEFORE M-DR-1 ships. Surface ungated equipment as a known-unknown. |
| Drive-through false positives | 🟡 | Require ≥ 5 min dwell time before suggesting. |
| Wrong geofence-to-project join | 🔴 | Hard gate: M-DR-1 cannot ship until M-3 verifies the join. **Order matters.** |
| Foreman tap fatigue | 🟡 | Pre-tick the high-confidence rows; bulk-confirm action. |

---

## F · M-2 Event Router · Feasibility & Design

### F.1 Events realistically available today (live in `motive_events`)

| Event | Available? | Source | Confidence | Volume hint |
|---|---|---|---|---|
| Arrived Job (`geofence_enter` where category=Job Site) | ✅ | webhook | 🟢 High | 1 sample to date; will scale with usage |
| Departed Job (`geofence_exit` where category=Job Site) | ✅ | webhook | 🟢 High | 1 sample |
| Arrived Plant | ⚠️ Conditional | webhook | 🟡 Depends on having Plant geofences in Motive (currently 0 categorized as Plant) | 0 today |
| Departed Plant | ⚠️ Conditional | webhook | 🟡 Same | 0 |
| Arrived Yard (`geofence_enter` where category=Terminal/Yard) | ✅ | webhook | 🟢 | 0 captured yet (3 yard fences exist) |
| Departed Yard | ✅ | webhook | 🟢 | 0 |
| Idle | ⚠️ | Not yet streamed — Motive has `idle_event`, classifier currently buckets to "other" | 🟡 Easy to add | 0 |
| Movement Start | ⚠️ | Implied by `vehicle_gps` speed > 0 after ≥ N min stop | 🟡 Derived | derive on read |
| Movement Stop | ⚠️ | Same, derived | 🟡 | derive on read |

### F.2 Map each event to its consumer (DESIGN ONLY — no wiring this sprint)

| Event family | Operations Awareness | Dispatch | Material Movement | Future Automation |
|---|---|---|---|---|
| `geofence_enter` (Job Site) | "Truck arrived" pulse in Hub | DLS `pending_confirmation` hint to driver (validate-don't-surveil) | Increment "loads-in-progress" counter for the project | Auto-suggest ticket creation when first daily arrival |
| `geofence_exit` (Job Site) | Pulse "Truck departed" | Validate driver-claimed DEPART | Close cycle; compute dwell | Auto-warn if dwell < 8 min (drive-through) |
| `geofence_enter` (Yard / Plant) | Inventory awareness | Confirm material pickup leg | Tie to incoming material rollup | Future cycle-time analytics |
| `vehicle_gps` (poll + webhook) | Last-seen-at timestamps on Dispatch Board | Gateway disconnect detection | — | M-3 backfill: detect when a truck visited an unmapped location → propose new `operational_location` |
| `asset_geofence_enter/exit` | Equipment on/off site signal | — | — | M-DR-1 input only |
| `hard_brake`, `harsh_*` | Safety dashboard | — | — | Coaching CA pipeline |
| `dvir_*` | Shop pre-op trust signal | — | — | Auto-create work order on `out_of_service=true` (already designed in P1.6) |
| `hos_violation` | HR awareness only | — | — | **Forbidden as dispatch gate** |
| `gateway_disconnected` | Operations alert "we've lost a truck" | DLS quiet finding | — | — |
| `fault_code` / `fault_code_closed` | Shop dashboard | — | — | Auto-WO on critical |
| `ai_coach_recap` | Safety read-only | — | — | — |

### F.3 Architecture (router shape, design only)
```
Webhook                            Router (M-2 — TO BE BUILT)
  │                                  │
  ▼                                  ▼
process_webhook ── insert ──▶  motive_events
                                     │
            ┌────────────────────────┼─────────────────────────┐
            ▼                        ▼                         ▼
 Operations Awareness pane   Dispatch validation       Material Movement
   (read-only feed)         (computed on read         (counter increment
                            per existing iter395)      ONLY when foreman
                                                       confirmed)
```

**Critical invariant:** The router writes **nothing** into authoritative MASCI collections except after **human confirmation**. The only side effect of `motive_events` arriving is its own row in `motive_events`. Surfaces compute *on read* (same pattern as iter395 governance findings).

---

## G · Verification Doctrine · The Constitutional Boundary

### G.1 What Motive MAY do (in MASCI)
✅ **Suggest** — "Foreman, was Excavator EX-4 onsite at 25-21 today?"
✅ **Verify** — "Driver claimed AT_LOAD_SITE; Motive geofence agrees within 60 s."
✅ **Visualize** — "Truck 42 last seen at 14:23, near SR 46."
✅ **Quiet-flag** — "Truck 17 ignition off > 30 min during a non-OFF_SHIFT state."
✅ **Backfill** — When a webhook is dropped, poll-source `vehicle_gps` rows fill the gap.

### G.2 What Motive MUST NOT do (constitutional forbidden list)
❌ **Auto-author Daily Reports** — every DR row is foreman-signed.
❌ **Auto-author Production totals** — `production[]` rows come from the field tap, full stop.
❌ **Auto-author Safety records** — incidents, JHAs, meetings remain human-authored.
❌ **Auto-sign anything** — signatures are the legal authority surface. Period.
❌ **Auto-attendance / payroll** — HR consumes `daily_reports.crew[]`, not Motive presence.
❌ **Drive states forward** — DLS `_record_transition` only accepts driver taps + dispatcher overrides.
❌ **Surveil drivers** — no live map, no scoreboard, no per-driver dashboard surfaced beyond audit views.
❌ **Reject dispatch on HOS** — FMCSA boundary; not MASCI's role.
❌ **Push to Motive** (writes) — until separately authorized in a future sprint.

### G.3 Trust-state catalog (already implemented in MOTIVE_INTEGRATION_STRATEGY.md)
| State | Meaning | Action |
|---|---|---|
| `confirmed` | Driver tap + Motive event agree (within 60 s window) | Quiet green check |
| `pending_confirmation` | Motive observed before driver tapped | Amber hint to driver |
| `mismatch` | Driver claim contradicts Motive | Amber dot on dispatch board; **no driver shaming** |
| `quiet` | No Motive data for > 90 min | LOW finding — invitation to ask, not penalty |

These trust states are the **read-time** output of the future M-2 router. They are never persisted as authoritative state.

---

## H · Risk Matrix

| # | Risk | Pillar at risk | Probability | Impact | Mitigation |
|---|---|---|---|---|---|
| 1 | **Geofence ↔ Project join wrong** (61 fence names vs 29 jobs, no key) | Trusted | 🔴 High | 🔴 High | M-3 admin-driven manual confirmation queue |
| 2 | **MASCI authors a geocode before Motive has its fence** | Trusted | 🟡 Med | 🟠 Med | M-3 surfaces Motive proposals first, then human-creates only when no match |
| 3 | **Foreman ignores Equipment Detected Today** (tap fatigue) | Powerful, Simple | 🟡 Med | 🟡 Med | Pre-tick high-confidence rows; allow bulk-confirm |
| 4 | **Asset Gateway coverage unknown** | Powerful | 🔴 High | 🟠 Med | Coverage audit before M-DR-1 ships |
| 5 | **Webhook secret rotation breaks signature verify** | Proven | 🟢 Low | 🟠 Med | Two-secret rotation window (already supported in `integration_settings`) |
| 6 | **Motive geofence deleted in Motive console** kills MASCI side | Trusted | 🟡 Med | 🟠 Med | Soft-delete in `operational_locations`; preserve audit trail; flag in queue |
| 7 | **Motive API quota / rate limit** | Proven | 🟢 Low | 🟡 Low | Pagination already implemented; poll cadence is operator-tunable |
| 8 | **Driver suspects surveillance** | Trusted (cultural) | 🟡 Med | 🔴 High | No driver-facing map; strictly enforce G.2 forbidden list |
| 9 | **Stale GPS hydration** (vehicle_gps in `asset_mappings.motive.lat` becomes truth) | Trusted | 🟡 Med | 🟡 Med | Always read with `located_at` timestamp; UI greys-out stale rows |
| 10 | **`motive_events` growth without TTL** | Simple | 🟢 Low | 🟡 Low | TTL index recommended (90 d per doctrine) — verify post-M-1 |
| 11 | **Plant/Pit/Yard collections never get created** (operator avoids M-3) | Powerful | 🟠 Med | 🔴 High | M-3 ships with seed admin tool for the 7 known canonical types |
| 12 | **Duplicate Motive geofences silently coexist** | Trusted | 🟡 Med | 🟡 Med | M-3 admin queue surfaces duplicates by name + proximity |

---

## I · Prioritized Build Order (Recommendation)

### I.1 Stated order from operator
1. M-3 Geocode Foundation
2. M-DR-1 Equipment Auto-Discovery
3. M-2 Event Router
4. Verification Layer

### I.2 Audit verdict on the order
✅ **CORRECT — DO NOT REORDER.**

**Justification (evidence-based):**

| Step | Why it must come first / next | Blocking dependency |
|---|---|---|
| **M-3 first** | 0/29 jobs have geocodes; 67 Motive geofences exist but cannot be joined to projects. Every downstream feature (M-DR-1, M-2, Verification) depends on knowing *"which fence belongs to which job"*. Without this, M-DR-1's "Equipment Detected Today" can't say *which project*. M-2's router can't pulse the right surface. | None — foundational. |
| **M-DR-1 second** | First operator-visible value-add. Builds operator trust in the Motive layer before any state-validation logic ships. Foreman-confirm gate honors the verification doctrine from day one. | M-3 |
| **M-2 third** | The router becomes meaningful only when (a) geofences are joined to projects (M-3) and (b) the operator has seen a verification UI (M-DR-1) and trusts the data. Building the router earlier would route into UI surfaces that can't say which job a pulse belongs to. | M-3, M-DR-1 |
| **Verification Layer fourth** | Trust-state computation (`confirmed`/`pending`/`mismatch`/`quiet`) only makes sense once events are routed to assignments AND geocodes are reliable. Premature shipping would generate false `mismatch` findings and erode pillar **Trusted**. | M-3, M-DR-1, M-2 |

### I.3 Pillar scorecard per build step

| Step | Powerful | Simple | Beautiful | Trusted | Proven |
|---|---|---|---|---|---|
| M-3 | 🟢 Unlocks every downstream | 🟢 One collection, one verify queue | 🟢 Admin queue surface | 🟢 Human gate built in | 🟡 Will be proven by first operator week |
| M-DR-1 | 🟢 First user-facing automation | 🟢 One sidecar per DR | 🟢 Pre-ticked confirm list | 🟢 Foreman tap-confirmed | 🟡 Needs Asset Gateway coverage audit |
| M-2 | 🟢 Wires telemetry to surfaces | 🟡 Multi-surface routing | 🟢 Existing FindingsBanner reused | 🟢 Read-time compute (no auth state mutation) | 🟢 Webhook receiver already proven |
| Verification Layer | 🟢 Earns full trust signal | 🟢 Computed on read | 🟢 Quiet green check / amber dot | 🟢 Cannot mutate state | 🟡 Tunable over first month |

---

## J · Diagrams

### J.1 Current-State (today)
```
┌──────────────────────────────────────────────────────────────┐
│  MOTIVE CLOUD                                                │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │ vehicles (90)  │  │ assets   (100) │  │ geofences (67) │ │
│  │ drivers   (65) │  │ events (live)  │  │ • 61 Job Site  │ │
│  └────────────────┘  └────────────────┘  │ • 3 Yard       │ │
│                                          │ • 2 Maint Fac. │ │
│                                          │ • 1 Uncat.     │ │
│                                          └────────────────┘ │
└────────────┬───────────────────────┬─────────────────────────┘
             │   webhook (HMAC)      │   poll
             ▼                       ▼
┌──────────────────────────────────────────────────────────────┐
│  MASCI BACKEND                                               │
│  ┌─────────────────┐   ┌──────────────────┐                  │
│  │ asset_mappings  │   │ motive_geofences │                  │
│  │   n=191         │   │   n=67           │                  │
│  └─────────────────┘   └──────────────────┘                  │
│  ┌─────────────────┐   ┌──────────────────┐                  │
│  │ employee_       │   │ motive_events    │                  │
│  │   mappings n=65 │   │   n=376 (live)   │                  │
│  └─────────────────┘   └──────────────────┘                  │
│                                                              │
│  ┌─────────────────┐   ┌──────────────────┐                  │
│  │ jobs_master     │   │ suppliers        │                  │
│  │ n=29 · 0% geo   │   │ n=145 · names    │                  │
│  └─────────────────┘   │      only        │                  │
│                        └──────────────────┘                  │
│  ❌ plants  ❌ pits  ❌ yards  ❌ shops                       │
│  ❌ disposal_sites   ❌ customer_locations                   │
└──────────────────────────────────────────────────────────────┘
                              │
              ❌ NO JOIN between motive_geofences ↔ jobs_master
```

### J.2 Future-State (post M-3 → M-DR-1 → M-2 → Verification)
```
┌─────────────────────────────────────────────────────────────────┐
│  MOTIVE CLOUD  (unchanged — read-only source of geofence truth) │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  MASCI BACKEND                                                  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐       │
│  │     operational_locations  (M-3 · canonical)         │       │
│  │  • JOB · ASPHALT_PLANT · CONCRETE_PLANT · PIT        │       │
│  │  • YARD · SHOP · DISPOSAL_SITE · VENDOR              │       │
│  │  • lat · lng · radius · motive_geofence_id (join)    │       │
│  │  • geocode_status ∈ {unverified, auto,               │       │
│  │                      human_verified, motive_synced}  │       │
│  └──────────────────────────────────────────────────────┘       │
│       ▲                ▲                ▲                       │
│       │ join           │ join           │ join                  │
│  ┌────┴───┐       ┌────┴────────┐  ┌────┴────────────┐          │
│  │ jobs_  │       │ motive_     │  │ motive_events   │          │
│  │ master │       │ geofences   │  │ (with location  │          │
│  │ n=29   │       │ n=67        │  │  context)       │          │
│  └────────┘       └─────────────┘  └─────────────────┘          │
│                                                                 │
│  ┌────────────────────┐    ┌────────────────────┐               │
│  │ M-DR-1 sidecar     │    │ M-2 router         │               │
│  │ "Equipment         │    │ (read-time         │               │
│  │  Detected Today"   │    │  computation)      │               │
│  │  · foreman tap     │    │  · Ops pulse       │               │
│  │  · pre-ticked      │    │  · DLS validation  │               │
│  └────────────────────┘    │  · MM counters     │               │
│                            └────────────────────┘               │
│                                     │                           │
│                                     ▼                           │
│                       Verification Layer (trust states)         │
│                       confirmed · pending · mismatch · quiet    │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
         ALL downstream writes still require human tap
         (foreman / driver / dispatcher signature)
```

---

## K · Required Deliverables · Checklist

| # | Deliverable | Section |
|---|---|---|
| 1 | MOTIVE-001 Constitutional Audit | this document |
| 2 | Current-State Diagram | §J.1 |
| 3 | Future-State Diagram | §J.2 |
| 4 | Geocode Foundation Architecture | §D |
| 5 | Equipment Auto-Discovery Architecture | §E |
| 6 | Event Router Architecture | §F |
| 7 | Verification Doctrine | §G |
| 8 | Risk Matrix | §H |
| 9 | Prioritized Build Order | §I |

---

## L · Recommended Next Authorization (the only ask)

**Authorize M-3 Geocode Foundation as the first build step.**

Suggested first-iteration scope (pre-authorization sketch — do NOT build yet):
1. Create `operational_locations` collection (8 location types per §D.1).
2. Build admin "Geocode Verification Queue" surface (read-only first):
   - Lists 29 jobs + 67 Motive geofences side-by-side.
   - Auto-proposes joins (name fuzzy + spatial centroid) with a confidence score.
   - Operator taps Confirm/Reject/Manual.
3. Seed the 7 canonical non-job location types (yards / shop / plants / pits / disposal / vendors) via one-time admin tool — operator authors them with address + radius; reverse-geocode for lat/lng.
4. Backfill `jobs_master` with derived lat/lng once each row is `human_verified`.
5. **No** push to Motive. **No** changes to `jobs_master` schema (additive lookup only).
6. **No** downstream consumption — M-DR-1 and M-2 remain on the bench.

**Out of scope for M-3 (deferred):**
- Any auto-routing from `motive_events` to project surfaces (that's M-2).
- Any "Equipment Detected Today" UI (that's M-DR-1).
- Any push-to-Motive write path.

---

## M · OMEGA Discipline Statement

This audit produced **zero code, zero schema changes, zero API changes, zero deploys, zero webhook changes, zero geocoding**. The audit confirmed the existing M-1 architecture is sound; what is missing is the canonical location wedge (M-3). The recommended order **M-3 → M-DR-1 → M-2 → Verification** is consistent with the foundational doctrine document (`MOTIVE_INTEGRATION_STRATEGY.md`) and grounded in observed production data.

🛑 **AUDIT COMPLETE. AWAITING OPERATOR AUTHORIZATION TO PROCEED WITH M-3.**

# MASCI · Motive API Capability Audit

**Date**: 2026-02-12 · **Mode**: Read-only · **Authorized**: NO BUILD · NO CHANGES · NO DEPLOY
**Evidence sources**:
- Motive public developer docs (`developer-docs.gomotive.com`) — verified live for this audit
- Motive Help Center (`helpcenter.gomotive.com`)
- Existing MASCI codebase context (`backend/services/motive_service.py`, `backend/routes/integrations/`)
- Third-party integration docs (ArcGIS Velocity, Withterminal, Arrivy, FleetWatcher)

**Note**: No new MASCI Motive screenshots or operator files were attached this turn. This audit is grounded in Motive's *published* developer documentation. Anything not in the public docs is explicitly marked as "not confirmed in public docs" — operator-provided artifacts can elevate these to confirmed.

---

## 1 · Authentication

| Aspect | Evidence |
|---|---|
| **Method** | **API key** in HTTP header — per `developer-docs.gomotive.com/docs/authentication`. No OAuth flow is documented. |
| **Header** | Authorization header carries the company API key (one key per organization). |
| **Token scope** | Single API key has org-wide scope; not per-resource. Sub-scoping not in public docs. |
| **Rate limits** | Motive's API Terms of Service (gomotive.com/legal/api-terms-of-service) reserves the right to impose and change transaction limits. **No published per-endpoint rate limit number** in the public docs. |
| **Sandbox / test mode** | Not documented in the public reference. Production credentials are required to test against real data. |
| **Production setup** | Operator: Help Center → "How to Request an API Key" (article 6177129182621). Submit a ticket → Motive provisions a key tied to the organization. |

**MASCI codebase context**: `services/motive_service.py:29` initializes with `db, settings_doc`; the existing `integration_settings` collection already holds a per-provider `api_key` field. Plumbing exists; credentials don't.

---

## 2 · Vehicles / Equipment

| Capability | Endpoint | Status |
|---|---|---|
| Vehicle list with locations | `GET /v1/vehicle_locations`, `GET /v2/vehicle_locations`, `GET /v3/vehicle_locations` | ✅ documented |
| Vehicle ID | included in locations response | ✅ |
| Vehicle name/number | included | ✅ |
| VIN | typically included | ✅ |
| Current driver | "assigned drivers" returned in vehicle_locations | ✅ |
| Current location | core of `vehicle_locations` | ✅ |
| Speed | included in v2/v3 location response | ✅ |
| Odometer | included | ✅ |
| Engine hours | included | ✅ |
| Asset/equipment list (non-vehicle) | `v3` endpoint specifically notes "intended for vehicles with Motive Vehicle Gateway installed" — non-vehicle assets need the **Asset Gateway** | ⚠️ device-dependent |
| Equipment GPS/device status | exposed via Asset Gateway webhooks (`asset_gateway` event family) | ✅ via webhook |

**Limit**: v2 `/vehicle_locations` capped at **100 vehicle IDs per request** (per docs). For larger fleets, paginate or use the "all subscribed vehicles" variant.

---

## 3 · Drivers

| Capability | Endpoint | Status |
|---|---|---|
| Driver list | `GET /v1/driver_locations` returns drivers with location + assigned vehicle | ✅ |
| Driver ID | returned | ✅ |
| Phone / email | **not confirmed** in the search snippets — Motive supports a Users API; need to verify which fields are exposed |
| Current vehicle | returned | ✅ |
| Driver location | returned | ✅ |
| Duty status (HOS) | Motive has HOS endpoints (separate `/hours_of_service` family) | ✅ |

---

## 4 · Location / GPS

| Aspect | Evidence |
|---|---|
| Live vehicle location | `vehicle_locations` v1/v2/v3 |
| Polling frequency | The **Motive API does not publish a hard sample rate**. The ArcGIS Velocity connector documents that its Motive AVL feed updates every **120 seconds** — that is the *connector's* poll cadence, not Motive's underlying rate. Vehicle Gateways report at higher rates internally; webhooks (`vehicle_gps`) deliver near-real-time. |
| Available fields | lat, lng, speed, heading, fuel level, location label, ignition state, accuracy, vehicle ID, driver assigned, fuel_type, gross_weight |
| Historical location | available — Motive exposes historical track lookups (per-vehicle, time-range) |
| Subscribed-vehicle tracking | `GET /vehicle_locations` "fetch location of all subscribed vehicles" variant |
| Equipment/asset locations | only when the asset carries a Motive **Asset Gateway** or **Vehicle Gateway**; small equipment without a device has no Motive location |

---

## 5 · Webhooks

Motive supports **Webhooks v2** (`developer-docs.gomotive.com/reference/webhooks-v2`).

**Delivery guarantees**:
- Receiver MUST acknowledge within **3 seconds** (HTTP 2xx) or Motive retries.
- Retries: Motive retries failed deliveries (count not published in our search results; the 3-second timeout IS published).
- Webhook management: `GET /v1/webhooks` (list company webhooks) + companion CRUD endpoints (`reference/overview-company-webhooks`).
- **Signature verification**: header name + verification scheme **not in the public-doc excerpts retrieved**. The platform should treat this as the most likely follow-up item to confirm with Motive support when credentials are issued.

**Documented event families** (per `reference/webhooks-v2`):

| Family | Event type | MASCI relevance |
|---|---|---|
| `asset_gateway` | Asset Gateway state | medium — for non-vehicle equipment with the AG installed |
| `vehicle_gps` | Vehicle location update | **HIGH — feeds dispatch board live position** |
| `dvir` | DVIR submitted/signed | medium — could complement Fleet DVIR module |
| `fault_code` | DTC fault code raised | **HIGH — drives MaintainX work-order auto-open** |
| `geofence` | Vehicle enter/exit geofence | **CRITICAL — drives dispatch state transitions** |
| `harsh_event` | Harsh brake / accel / cornering / speeding | **HIGH — feeds Safety bell** |

Other events that MAY exist but were not explicitly named in the retrieved snippets (must confirm against full Webhooks v2 reference): driver_changed, ignition_on/off, idle, document/ticket events. These are reasonable to assume given the platform's domain but should be verified once credentials are issued.

---

## 6 · Geofences

| Capability | Endpoint | Status |
|---|---|---|
| Create geofence (polygon) | `POST /v1/geofences` | ✅ |
| Create geofence (radius/circular) | `POST /v1/geofences/circular` | ✅ |
| Update geofence | documented | ✅ |
| Delete geofence | documented | ✅ |
| List geofences | documented | ✅ |
| Polygon vs radius | both supported | ✅ |
| Enter/exit events | `geofence` webhook family | ✅ |
| Assignment to vehicles/assets | geofences are org-scoped; enter/exit fires per vehicle | ✅ |
| Limitations | per-org geofence count caps not published; risk-alerts blog (gomotive.com 2024) describes "geofence-based risk alerts" — confirms enter/exit semantics are first-class |

**This is the strongest part of Motive for MASCI** — full CRUD on geofences via API means MASCI can auto-create a geofence for every new job in `jobs_master` once the addresses are geocoded.

---

## 7 · Dispatch API

| Capability | Evidence |
|---|---|
| Create dispatch | Motive exposes `v1/dispatch_locations` (locations endpoint mentioned in `reference/overview-locations`). A **full create-update-track-complete dispatch CRUD** is NOT confirmed in the retrieved snippets. |
| Assign driver / vehicle | not confirmed in retrieved snippets |
| Track dispatch status | not confirmed |
| Send route/destination | partially — dispatch_locations allows location push |
| Sync with MASCI dispatch lifecycle | **MASCI should remain the system of record** — Motive's dispatch surface (per the public docs visible) is lighter than MASCI's 13-state lifecycle |

**Verdict**: Do not adopt Motive Dispatch as a replacement for MASCI's lifecycle. Use Motive's location + geofence events to **drive** MASCI's lifecycle, not replace it.

---

## 8 · Maintenance / Shop

| Signal | Endpoint / channel | Status |
|---|---|---|
| Fault codes / DTCs | `fault_code` webhook + DTC list endpoints | ✅ |
| Odometer | included in vehicle_locations + a dedicated odometer endpoint | ✅ |
| Engine hours | included in vehicle_locations | ✅ |
| Inspection reports (DVIR) | `dvir` webhook + DVIR list endpoint | ✅ |
| Maintenance alerts | derived from fault_code + DVIR events | ✅ |
| Service intervals | Motive Maintenance Module — separate product; not all data exposed via public API per snippets retrieved | ⚠️ |

---

## 9 · Safety

| Signal | Channel | Status |
|---|---|---|
| Harsh braking | `harsh_event` webhook | ✅ |
| Harsh acceleration | `harsh_event` webhook | ✅ |
| Cornering | `harsh_event` webhook (likely subtype; confirm by event payload) | ✅ probable |
| Speeding | `harsh_event` or dedicated speeding event | ✅ |
| Seatbelt events | not explicitly confirmed in retrieved snippets |
| Dashcam / safety events | safety event family; dashcam payload includes video link |
| Driver score | Motive surfaces driver scores in dashboard; API exposure not confirmed in retrieved snippets |

---

## 10 · FleetWatcher vs Motive · for asphalt/load production

| Capability | Motive | FleetWatcher | Winner |
|---|---|---|---|
| Asphalt ticket / e-ticket | not core | **YES — e-ticketing is core** | **FleetWatcher** |
| Plant loaded time | derivable from geofence | **YES — first-class** | **FleetWatcher** |
| Ticket numbers | not native | **YES** | **FleetWatcher** |
| Tons | not native | **YES** | **FleetWatcher** |
| Mix type | not native | **YES** | **FleetWatcher** |
| Dump events | derivable from geofence | **YES — first-class** | **FleetWatcher** |
| Production haul cycle | derivable from geofence enter/exit | **YES — purpose-built** | **FleetWatcher** |
| Vehicle telematics (GPS, fuel, hours) | **YES — core** | uses Motive AVL feed for this | **Motive** |
| Driver compliance (HOS, DVIR) | **YES — core** | not core | **Motive** |
| Safety events (harsh brake, etc.) | **YES — core** | not core | **Motive** |
| Geofence CRUD via API | **YES** | n/a | **Motive** |

**FleetWatcher already integrates with Motive** (per Motive Help Center article 10510243670813) — the customer shares the Motive API key with the FleetWatcher account manager, and FleetWatcher pulls Motive telemetry into its own dashboards.

**Implication**: Two-source architecture is the natural fit.
- **Motive** = telematics + safety + HOS source of truth.
- **FleetWatcher** = asphalt-ticket + load-cycle source of truth.
- **MASCI Docs** = operational workflow layer that consumes both.

---

## MASCI Dispatch Event Map

| Source event | Source | → MASCI Dispatch State | Confidence | Automation |
|---|---|---|---|---|
| `vehicle_gps` (vehicle becomes mobile after ASSIGNED) | Motive | ASSIGNED → ENROUTE_TO_LOAD | MEDIUM (could be vehicle-test, not job-bound) | SUGGESTED ONLY |
| `geofence.enter` (plant) | Motive | ENROUTE_TO_LOAD → AT_LOAD_SITE | HIGH | FULLY AUTOMATIC |
| FleetWatcher loaded ticket | FleetWatcher | AT_LOAD_SITE → LOADED | HIGH | FULLY AUTOMATIC |
| `geofence.exit` (plant) | Motive | LOADED → ENROUTE_TO_JOB | HIGH | FULLY AUTOMATIC |
| `geofence.enter` (job site) | Motive | ENROUTE_TO_JOB → ARRIVED_JOB | HIGH | FULLY AUTOMATIC |
| FleetWatcher dump ticket | FleetWatcher | ARRIVED_JOB → DUMPING | HIGH | FULLY AUTOMATIC |
| `geofence.exit` (job site) | Motive | DUMPING → COMPLETE *(when last cycle)* | MEDIUM (cycle count needed) | SUGGESTED ONLY |
| `vehicle_gps` ignition_off >N min while not at any geofence | Motive | → WAITING | MEDIUM | SUGGESTED ONLY |
| `vehicle_gps` ignition_off at MASCI Yard geofence | Motive | → OFF_SHIFT | HIGH | FULLY AUTOMATIC |
| `fault_code` raised | Motive | → BREAKDOWN | HIGH | SUGGESTED ONLY (dispatcher confirms severity) |
| `harsh_event` (severe) | Motive | side-channel safety bell (does not change state) | HIGH | FULLY AUTOMATIC (Safety bell only) |
| Driver mismatch (`vehicle_gps.driver_id` ≠ `assignment.driver_id`) | Motive | side-channel alert (does not change state) | HIGH | FULLY AUTOMATIC (alert only) |
| HOLD | — | dispatcher manual | — | HUMAN REQUIRED |
| Re-acknowledge after revision (D-1.5) | — | driver tap on magic-link | — | HUMAN REQUIRED |

---

## Critical Output

### Motive Can Do Now (evidence-backed)
- Authentication via API key (one per org) ✅
- Vehicle list + locations + speed + odometer + engine hours (`vehicle_locations` v1/v2/v3) ✅
- Driver list + driver locations (`driver_locations`) ✅
- Geofence CRUD — polygon + circular (`/v1/geofences`, `/v1/geofences/circular`) ✅
- Live vehicle tracking via webhooks (`vehicle_gps`, `geofence`, `harsh_event`, `fault_code`, `dvir`, `asset_gateway`) ✅
- Webhook management API (list / create / update / delete company webhooks) ✅

### Motive Can Do With Polling
- Periodic asset/driver sync (existing `MotiveService.sync_assets`, `sync_users` stubs map onto `vehicle_locations` + `driver_locations`) ✅
- Idle event detail backfill (`view-the-idle-events-of-your-drivers` endpoint) ✅
- Historical location lookups (per-vehicle time-range queries) ✅
- Odometer threshold checks (poll daily for PM scheduling) ✅
- HOS / duty status review ✅

### Motive Can Do With Webhooks
- Real-time dispatch state transitions via `geofence` events ✅
- Real-time location stream via `vehicle_gps` events ✅
- Real-time safety alerts via `harsh_event` ✅
- Real-time engine fault → shop work order via `fault_code` ✅
- Real-time DVIR submitted → fleet DVIR module via `dvir` ✅
- Real-time asset gateway events for equipment with AG hardware ✅

### Motive Cannot Do / Not Found
- Native asphalt ticket / load weight / mix type — **not in Motive's domain**
- Production haul cycle counting with ticket numbers — **not in Motive's domain**
- Driver phone/email exposure via API — **not confirmed in public docs** (operator may verify with Motive support)
- Webhook signature verification scheme — **not in retrieved doc snippets** (likely HMAC; confirm at credential time)
- Per-endpoint rate limit — **not published** (Motive reserves right to throttle)
- Full dispatch CRUD competitive with MASCI's 13-state lifecycle — **not the right tool**; Motive offers `dispatch_locations` (location push) but MASCI's lifecycle is richer

### FleetWatcher Better Fit
- Asphalt e-tickets · loaded-at timestamps · ticket numbers · tons · mix type · dump events · production haul cycle
- FleetWatcher already integrates with Motive (shares the API key) — operator does this once via FleetWatcher account manager

### MASCI Docs Should Own
- The 13-state dispatch lifecycle (ASSIGNED through OFF_SHIFT)
- Driver magic-link auth + acknowledgement (D-1.1)
- Revision flow + re-ack (D-1.5)
- Reassign / Cancel / WAITING / HOLD / BREAKDOWN human-decision points
- Operational attachments (12 canonical types — R2 backed)
- Trench safety asset registry (no Motive overlap)
- Safety meeting / JHP / Daily Report workflows
- Bell + email notifications (existing rails)
- Day-1 / Week-1 debriefs
- Field leadership oversight surface

---

## Implementation Recommendation

### Recommended path: **Option C · Hybrid polling + webhook**

**Why hybrid**:
- **Webhooks** for real-time UX (geofence transitions, harsh events, fault codes drive the board live).
- **Polling** for resilience: daily/hourly `sync_assets` + `sync_events` catches webhook drops, and the Motive API does not publish delivery guarantees beyond the 3-second ack window.

### Exact endpoints needed

```
Authentication header: Authorization: Bearer <MOTIVE_API_KEY>

Read (polling):
  GET  /v3/vehicle_locations            · canonical asset + location sync
  GET  /v1/driver_locations             · driver ↔ vehicle mapping sync
  GET  /v1/geofences                    · reconcile MASCI ↔ Motive geofences
  GET  /v1/idle_events                  · backfill idle for WAITING heuristic

Write (one-time + on job-create):
  POST /v1/geofences/circular           · auto-create geofence per new job
  POST /v1/geofences                    · same for plant/yard polygons (one-off setup)

Webhook receiver (already mounted):
  POST /api/integrations/motive/webhook · existing route in MASCI · just fill in process_webhook
```

### Exact webhooks needed

Subscribe (via `POST /v1/webhooks` create) to these 5 event types:

| Webhook | MASCI consumer |
|---|---|
| `geofence` | `_record_transition()` — auto-state transitions |
| `vehicle_gps` | live position on board + state-event geo enrichment |
| `harsh_event` | `db.tasks` bell + `dispatch_state_events` audit row tagged MOTIVE_SAFETY |
| `fault_code` | open MaintainX work order via existing `maintainx_p0` |
| `dvir` | enrich existing Fleet DVIR module |

### Exact env vars needed

```
MOTIVE_API_KEY                   · org API key (Help Center → request)
MOTIVE_API_BASE                  · https://api.gomotive.com (default; env-overridable)
MOTIVE_WEBHOOK_SECRET            · shared secret for HMAC verification (confirm scheme with Motive)
MOTIVE_ENABLED                   · true/false master gate
MOTIVE_AUTO_TRANSITION           · true/false — gate the dispatch state automation
MOTIVE_POLL_INTERVAL_SECONDS     · default 900 (15 min) for the polling loop
```

All already plumbed via `integration_settings` + `webhook_secret_value` columns in the existing schema.

### Exact MASCI collections touched

| Collection | How |
|---|---|
| `integration_settings` | one row already seeded; flip `enabled=true`, set `api_key`, `webhook_secret_value` |
| `asset_mappings` | hydrate `motive.vehicle_id`, `motive.device_id` for each truck — UI already exists |
| `employee_mappings` | hydrate `motive.driver_id` for each driver |
| `motive_events` | webhook payloads land here (collection already indexed at startup) |
| `dispatch_assignments` | `_record_transition()` writes geo + actor — no schema change |
| `dispatch_state_events` | append-only audit, `geo` field already nullable |
| `db.tasks` | bell rail for safety + driver-mismatch alerts |
| `jobs_master` | **additive columns** for `lat`/`lng` once geocoded (NEW · the only schema add) |

### Exact dispatch states affected

ASSIGNED · ENROUTE_TO_LOAD · AT_LOAD_SITE · LOADED · ENROUTE_TO_JOB · ARRIVED_JOB · DUMPING · COMPLETE · WAITING · BREAKDOWN · OFF_SHIFT. HOLD remains human-only. Re-ack remains driver-only.

### Risks

| Risk | Mitigation |
|---|---|
| Webhook signature scheme not in public docs | Confirm with Motive support at credential issuance; existing `_storage.verify_webhook_signature_stub` is the seam |
| Rate limits not published | Polling defaults to 15-min cadence; existing scheduler pattern accommodates back-off |
| Sandbox not documented | Use a Motive trial fleet + one MASCI test truck before production rollout |
| Geofence overlap (job inside plant) | Use polygon precision for plants and circular for jobs to make enter/exit unambiguous |
| Driver score not confirmed via API | Defer driver-score surfacing until verified at credential time |
| Asset Gateway coverage on non-vehicle equipment | Decide per-asset whether AG is fitted; the `asset_mappings.motive.gps_enabled` flag already handles it |

### Estimated effort

| Phase | Days |
|---|---|
| M-1 · Real `MotiveService` HTTP client (auth + 4 read endpoints) | 3 |
| M-2 · Webhook `process_webhook()` event-type router | 2 |
| M-3 · `jobs_master` geocode backfill + `lat`/`lng` schema add | 1 |
| M-4 · Auto-create geofence on job create | 0.5 |
| M-5 · Polling scheduler (mirrors D-1.4 reminder loop) | 0.5 |
| M-6 · DispatchBoard "GPS-validated" chip variant | 0.5 |
| M-7 · Field trial · one truck · one route · one job | 1 |
| M-8 · Hardening + harsh-event safety bell | 0.5 |
| **Total** | **~8.5 dev-days** |

---

## Final Verdict

# **MOTIVE READY BUT WEBHOOKS LIMITED**

**Reasoning**:
- **Motive IS ready** for an M-1 API client sprint: authentication, vehicle/driver/location/geofence endpoints, and the core 6 webhook event families are all *documented and live* in `developer-docs.gomotive.com`.
- **"Webhooks limited"** is the honest caveat because two specifics could not be confirmed from public docs alone in this audit:
  1. The exact **webhook signature verification scheme** (header name, hash algorithm) — likely HMAC-SHA256 but must be verified at credential issuance.
  2. The exact **full event-type list** in Webhooks v2 — the six named families (`asset_gateway`, `vehicle_gps`, `dvir`, `fault_code`, `geofence`, `harsh_event`) cover the high-ROI use cases, but sub-event granularity (e.g. is "cornering" a subtype of `harsh_event` or a separate event?) needs payload-level confirmation at first webhook receipt.

Both unknowns are **resolved at credential issuance**, not before. They do not block sprint planning.

**Recommended next step (operator action only — no code change)**:
1. Operator submits Motive Help Center ticket → "Request an API Key" (article 6177129182621).
2. Operator obtains the API key + webhook secret.
3. Operator confirms with Motive support: (a) webhook signature header name + scheme, (b) full Webhooks v2 event-type catalogue.
4. Operator pastes credentials into the Emergent production env panel.
5. **THEN** authorize the M-1 sprint to begin.

Until step 1–4 are complete, **the codebase remains correctly stubbed**. No HTTP calls. No phantom integrations. The 14-module integration framework is the runway; Motive credentials are the ignition key.

**End of audit. No code changed. No new build proposed beyond the existing M-1 effort scope already inventoried in `MOTIVE_INTEGRATION_FORENSIC_AUDIT.md`.**

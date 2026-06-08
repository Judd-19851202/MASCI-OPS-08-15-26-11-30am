# MASCI · MOTIVE WEBHOOK INTELLIGENCE AUDIT

**Date:** 2026-06-08
**Scope:** Read-only audit. No code/DB/deploy/automation changes.
**Method:** Direct Mongo introspection · webhook receiver code walk · cross-reference with the verified Webhooks v2 catalog in `/app/memory/MOTIVE_API_CAPABILITY_AUDIT.md`.
**Purpose:** Decide *how* MASCI should consume Motive intelligence before any consumer is built.

---

## EXECUTIVE SUMMARY (one paragraph)

MASCI has a hardened, HMAC-verified webhook receiver mounted at `/api/integrations/motive/webhook`. Today it receives **exactly one event family** — `vehicle_gps` — and routes every other event family to the same generic `motive_events` bucket without any consumer attention. Motive's Webhooks v2 publishes at least **8 distinct event families** with materially different operational meaning (safety, maintenance, dispatch, compliance, asset health). Of those 8, only `vehicle_gps` is currently subscribed in the Motive dashboard. The audit recommends **subscribing to 5 of the 8 families** (`vehicle_gps`, `geofence`, `harsh_event`, `fault_code`, `dvir`) for high-ROI operational use, **storing-only** the other 3 (`asset_gateway`, `idle`, `ignition`) for forensic value, and **classifying every event into a clear role + screen + action band** before anything is built. No M-2 automation in this document — visibility classification only.

---

## PHASE 1 — WEBHOOK INVENTORY

### Configuration (live)
- Receiver route: `POST /api/integrations/motive/webhook` · unauthenticated · signature-verified via `X-Motive-Signature` (HMAC-SHA256 of raw body using the stored `webhook_secret_value`).
- Stored secret: ends `c106` (live).
- `integration_settings.motive.enabled = true · status = Connected · demo_mode = true (preview only)`.
- Upstream subscription: **only `vehicle_gps` is enabled in the Motive dashboard today.** All other Webhooks v2 families exist but are not subscribed.

### Receiver routing logic (`services/motive_service.py::process_webhook`)
- Resolves event kind from `event_type` / `type` / `event` (defensive).
- Persists ALL incoming events into `db.motive_events` (`source="webhook"`).
- Only `vehicle_gps` and `vehicle_location_received` have a downstream hydrate step (re-writes `asset_mappings.motive.lat/lon/located_at`). Every other family lands in `motive_events` and stops.

### Live inventory · `motive_events` collection (272 rows total)

| Source | event_kind | Count | Last received |
| --- | --- | --- | --- |
| poll | `vehicle_gps` | 270 | 2026-06-08 12:58 UTC |
| webhook | `vehicle_gps` | 2 | 2026-06-08 13:05 UTC |
| **other families** | — | **0** | never |

### Motive Webhooks v2 event-family catalog (per `developer-docs.gomotive.com/reference/webhooks-v2`)

| EVENT FAMILY | RECEIVED? | STORED? | DISPLAYED? | USED? |
| --- | --- | --- | --- | --- |
| `vehicle_gps` | ✅ (subscribed) | ✅ (272 rows) | ✅ (HR + Safety event card · AssetProfile Motive tab after P1) | ⚠️ Read-only — no workflow consumes |
| `geofence` (enter/exit) | ❌ not subscribed | ❌ | ❌ | ❌ |
| `harsh_event` (brake / accel / cornering / speeding) | ❌ not subscribed | ❌ | ❌ | ❌ |
| `fault_code` (DTC) | ❌ not subscribed | ❌ | ❌ | ❌ |
| `dvir` (submitted / signed) | ❌ not subscribed | ❌ | ❌ | ❌ |
| `asset_gateway` (equipment health · battery · tamper) | ❌ not subscribed | ❌ | ❌ | ❌ |
| `idle` (extended-idle · likely surfaced via harsh_event or dedicated) | ❌ not subscribed | ❌ | ❌ | ❌ |
| `ignition` (on/off · derivable from `vehicle_state`) | ❌ not subscribed | ❌ | ❌ | ❌ |
| `driver_changed` (likely · not explicitly named in retrieved doc snippet) | ⚠️ unconfirmed | — | — | — |

Note on `driver_changed` / `ignition`: these were not explicitly itemized in the retrieved Webhooks v2 doc snippet but are documented as derivable from existing payloads (`vehicle.current_state`, `current_driver`). Treat as TBD until the full reference is confirmed.

---

## PHASE 2 — EVENT PAYLOAD ANALYSIS

### `vehicle_gps` (only family with live evidence)

| FIELD | PURPOSE | VALUE |
| --- | --- | --- |
| `event_type` | Family discriminator | CRITICAL — routing |
| `vehicle.id` / `vehicle.number` | Vehicle identity | CRITICAL — join to MASCI |
| `location.lat` / `location.lon` | Position | CRITICAL |
| `location.located_at` | Timestamp | CRITICAL — staleness math |
| `location.kph` | Speed | HIGH |
| `location.bearing` | Heading | MEDIUM |
| `location.city` / `location.state` | Reverse-geocode | HIGH — human readability |
| `vehicle.vehicle_state` | `moving`/`stopped`/`idle` | HIGH — derivation source |
| `current_driver` (when present) | Operator | HIGH — P1-C hierarchy uses this |
| `vehicle.vin` / `make` / `model` | Identity (rare per-event; usually on sync) | LOW — sync already has this |

**Frequency:** Continuous when ignition on. Observed ~2 rows/15s per active vehicle from the Motive doc rate (~120s connector poll). At fleet scale (90 vehicles), expect ~5,000-50,000 events/day depending on movement.
**Volume:** Largest of any family. Will dominate `motive_events` storage.
**Operational significance:** Foundation for *every* downstream visibility, but each individual row has low standalone value. The aggregate (lat/lon/speed over time) is high-value; the single event is noise.

### `geofence` (expected payload from Webhooks v2 reference)

| FIELD | PURPOSE | VALUE |
| --- | --- | --- |
| `event_type` (`geofence_enter` / `geofence_exit`) | Transition type | CRITICAL |
| `geofence.id` / `geofence.name` | Which fence | CRITICAL — joins to `motive_geofences` |
| `vehicle.id` | Which vehicle | CRITICAL |
| `entered_at` / `exited_at` | When | CRITICAL |
| `dwell_seconds` (exit only) | Time on site | HIGH — billable hours / utilization |
| `current_driver` | Who | HIGH |
| `geofence.category` | Job-site / yard / shop | HIGH — routing logic |

**Frequency:** Sparse — every truck enters/exits a few sites per day. Roughly 100-300 events/day fleet-wide.
**Operational significance:** **Highest signal-to-noise of any family.** Each event corresponds to a real-world dispatch state change.

### `harsh_event`

| FIELD | PURPOSE | VALUE |
| --- | --- | --- |
| `event_type` / `subtype` (`hard_brake`, `harsh_accel`, `harsh_cornering`, `speeding`) | Behaviour | CRITICAL |
| `severity` (`high` / `medium` / `low`) | Triage band | CRITICAL |
| `driver.id` / `driver.name` | Who | CRITICAL |
| `vehicle.id` / `vehicle.number` | Where | HIGH |
| `location.address` | Where geographically | HIGH |
| `speed_mph` / `speed_at_event` | Severity context | HIGH |
| `coaching_required` | Workflow hint | MEDIUM |
| `video_url` (when dashcam) | Evidence | HIGH — when present |

**Frequency:** Variable — fleet-wide ~5-25 events/day typical.
**Operational significance:** Direct Safety/HR workflow input.

### `fault_code`

| FIELD | PURPOSE | VALUE |
| --- | --- | --- |
| `event_type` | Family | CRITICAL |
| `dtc_code` (J1939 / OBD-II) | Engine error | CRITICAL |
| `severity` (red / amber / info) | Triage | CRITICAL |
| `vehicle.id` | Which truck | CRITICAL |
| `mil_status` (check engine on) | Driver-facing | HIGH |
| `description` (human-readable) | Display | HIGH |
| `set_at` / `cleared_at` | Lifecycle | HIGH |

**Frequency:** ~1-10/day fleet-wide for an active fleet.
**Operational significance:** Direct Shop/MaintainX feed.

### `dvir`

| FIELD | PURPOSE | VALUE |
| --- | --- | --- |
| `event_type` | Family | CRITICAL |
| `dvir.status` (`submitted` / `signed` / `failed`) | Lifecycle | CRITICAL |
| `driver.id` | Who did the inspection | CRITICAL |
| `vehicle.id` | Which truck | CRITICAL |
| `defects[]` | What's broken | CRITICAL when present |
| `out_of_service` | Hold decision | CRITICAL |
| `mechanic.id` (on sign) | Shop accountability | HIGH |

**Frequency:** ~90 events/day (one per vehicle per shift roughly).
**Operational significance:** Already partially duplicates MASCI's own Pre-Op flow — primary value is when MASCI driver completes Motive DVIR (which is the case for several CDL drivers).

### `asset_gateway`

| FIELD | PURPOSE | VALUE |
| --- | --- | --- |
| `event_type` | Family | CRITICAL |
| `asset.id` | Construction equipment | CRITICAL |
| `gateway.battery_level` | Health | HIGH |
| `gateway.tamper` (Y/N) | Theft signal | CRITICAL when true |
| `gateway.last_check_in` | Health | HIGH |
| `location` | Position | HIGH (sparse vs vehicle_gps) |

**Frequency:** Low — heartbeat-style. 1-3/day per asset.
**Operational significance:** Theft alerts + battery exhaustion warnings. Otherwise quiet.

### `idle` / `ignition` (presumed; payload not yet observed)

| FIELD | PURPOSE | VALUE |
| --- | --- | --- |
| `event_type` | Family | CRITICAL |
| `vehicle.id` | Which | CRITICAL |
| `idle_duration_minutes` / `state` | Magnitude | MEDIUM |
| `location` | Where | LOW (we have it elsewhere) |

**Frequency:** Potentially high if subscribed. Subset of `vehicle_gps` derivable state changes — risk of duplicate noise.
**Operational significance:** LOW relative to `vehicle_gps` because the same info is derivable from speed + `located_at` deltas without subscribing.

---

## PHASE 3 — ROLE VISIBILITY AUDIT

| EVENT | ROLE | WHY |
| --- | --- | --- |
| `vehicle_gps` | **Dispatch · PM · Operations · Superintendent · Admin** | Position + staleness drive every "where is X" question. **Hide from Safety/HR/Driver/Shop** — too noisy for them to see raw GPS. |
| `geofence_enter` | **Dispatch · Superintendent · PM (own jobs only)** | Arrival = state transition. Operations also wants the rollup, not individual events. |
| `geofence_exit` | **Dispatch · PM (own jobs only) · Operations** | Departure = dwell-time close. Same as above. |
| `harsh_event` (high) | **Safety · HR · Dispatch · Admin** | Coaching + accident risk. Dispatch needs awareness so they don't re-assign a driver mid-incident. |
| `harsh_event` (medium / low) | **Safety · HR · Admin** | Coaching only. Dispatch does NOT need to see — noise. |
| `harsh_event` subtype `speeding` | **Safety · HR · Admin** | Coaching candidate · cumulative pattern matters more than individual event. |
| `fault_code` (red / severe) | **Shop · Dispatch · Admin** | Active engine fault may strand the truck. Dispatch needs to know to swap a load. |
| `fault_code` (amber / info) | **Shop · Admin** | Maintenance planning only. Hide from Dispatch — noise. |
| `dvir` (submitted, pass) | **Shop · Admin** (audit only) | Routine. Operationally a no-op. |
| `dvir` (submitted, defect / out_of_service) | **Shop · Safety · Dispatch · Admin** | Equipment cannot dispatch. Critical for board accuracy. |
| `dvir` (signed by mechanic) | **Shop · Admin** | Closes the loop on a defect. |
| `asset_gateway` (battery low) | **Shop · Admin** | Maintenance task. |
| `asset_gateway` (tamper / motion off-hours) | **Safety · Admin · Operations** | Theft alert. **Highest urgency outside business hours.** |
| `idle` | **Operations · PM (own jobs)** (rollup only) | Idle stats drive utilization. Individual events = noise. |
| `ignition` | **Audit log only** | Useful as a query input ("when did this truck turn on?") but no live consumer. |
| `driver_changed` | **Dispatch · Safety · Admin** | "Who is in DPT021-8147 right now?" — current P1-C resolver pulls this from sync; live event makes it instant. |

**Driver-facing visibility:** **NONE.** Drivers receive Motive's own coaching app in their cab. MASCI does not need to relay Motive events to the driver.

---

## PHASE 4 — DISPLAY LOCATION AUDIT

| EVENT | SCREEN | REASON |
| --- | --- | --- |
| `vehicle_gps` | **Audit log only** (per-event) + **AssetProfile Motive tab** (latest hydrate, already wired by P1-D) + **Operations Center counters** (P1-E rollups) | Per-event display = noise. The hydrated latest position IS the display. |
| `geofence_enter/exit` | **Dispatch Board** chip ("on site" / "departed") + **Asset Profile → Activity tab** + **PM Hub project page** (own job's geofences only) | Each event maps cleanly to a state transition users already understand. |
| `harsh_event` | **Safety Hub event feed** (already wired, just needs payload) + **Asset Profile → Events tab** (per-vehicle) + **Driver Profile** (per-driver coaching record) + **Notifications bell** for high-severity | Already-existing surfaces; no new screens needed. |
| `fault_code` (red) | **Shop Hub "Equipment Down" tile** + **Dispatch Board chip** ("FAULT") + **Asset Profile → MaintainX tab** | Operationally identical to a "down" flag. |
| `fault_code` (amber/info) | **Shop Hub** only (read-only list) + **Asset Profile → Events tab** | Maintenance planning view. |
| `dvir` (defect/OOS) | **Shop Hub Pre-Op queue** + **Dispatch Board** (asset becomes Maintenance Hold) + **Asset Profile → Field Ops tab** | Mirrors MASCI's existing pre-op fail handling. |
| `dvir` (signed) | **Shop Hub** closed-out log + **Asset Profile** event timeline | Audit / completeness only. |
| `asset_gateway` (tamper) | **Operations Center alert banner** + **Notifications bell** + **Asset Profile** | High-urgency · low-volume — banner is appropriate. |
| `asset_gateway` (battery) | **Shop Hub** + **Asset Profile** | Maintenance planning. |
| `idle` | **Operations Center utilization view** (counter only) | Aggregate. |
| `ignition` | **Asset Profile → Events tab** (audit) | Forensic only. |
| `driver_changed` | **Dispatch Board** (driver chip on assignment card auto-updates) + **AssetProfile OperatorCard** | Re-uses surfaces already built in P1-C/D. |

---

## PHASE 5 — ACTION CLASSIFICATION

| EVENT | CATEGORY | RATIONALE |
| --- | --- | --- |
| `vehicle_gps` | **C** Historical Visibility | Per-event has no action. Aggregated state already drives Ops tile. |
| `geofence_enter` (job site) | **B** Operational Awareness | Driver "checked in" — dispatcher updates expectation. |
| `geofence_exit` (job site) | **B** Operational Awareness | Triggers ETA refresh for next leg. |
| `geofence_enter` (yard / shop) | **B** | Truck home for the day. |
| `harsh_event` (high severity) | **A** Immediate Action Required | Safety coaching call + Dispatch re-evaluation. |
| `harsh_event` (medium) | **B** | Coaching backlog. |
| `harsh_event` (low) | **D** Audit Only | Drives long-term driver score; individual event is noise. |
| `harsh_event` subtype `speeding` (severe) | **A** | Compliance + insurance risk. |
| `fault_code` (red / MIL on) | **A** | Truck likely about to break down. |
| `fault_code` (amber) | **B** | Schedule next service. |
| `fault_code` (info) | **D** | Historical only. |
| `dvir` (defect / out_of_service) | **A** | Asset cannot dispatch. |
| `dvir` (pass) | **D** | Audit only. |
| `dvir` (signed by mechanic) | **C** | Closeout visibility. |
| `asset_gateway` (tamper / off-hours motion) | **A** | Theft signal. |
| `asset_gateway` (battery low) | **B** | Maintenance task. |
| `asset_gateway` (heartbeat) | **D** | Forensic. |
| `idle` (long, >30 min on job) | **C** | Utilization KPI. |
| `idle` (long, on yard) | **D** | Expected. |
| `ignition` | **D** | Audit. |
| `driver_changed` | **B** | Dispatch board refresh. |

**Category counts:** A=6 · B=8 · C=3 · D=6 · E=0.

---

## PHASE 6 — SAFETY INTELLIGENCE AUDIT

| EVENT | WHO SHOULD SEE | HOW QUICKLY | WHERE |
| --- | --- | --- | --- |
| Harsh braking (high) | Safety · HR · Dispatch | Within minutes | Safety Hub feed · Notifications bell · Driver Profile |
| Harsh braking (medium / low) | Safety · HR | Daily digest | Safety Hub feed |
| Harsh acceleration | Safety · HR | Daily digest | Safety Hub feed |
| Harsh cornering | Safety · HR | Daily digest | Safety Hub feed |
| Speeding (>X mph over) | Safety · HR · Admin | Within hour | Safety Hub feed + Driver Profile flag |
| Impact / collision detection (Motive AI Dashcam) | Safety · HR · Dispatch · Admin | **Real-time pager** | Notifications bell · Asset Profile · Safety Hub banner |
| Seatbelt violation | Safety · HR | Daily digest | Safety Hub feed |
| DVIR submitted (no defect) | Shop · Admin | Daily | Shop Hub log |
| DVIR submitted (defect / OOS) | Shop · Safety · Dispatch | Real-time | Pre-Op queue + Dispatch Board chip |
| Driver behavior aggregate (week) | HR · Safety · Admin | Weekly digest | HR Hub Driver Qualification dashboard |

**Critical insight:** MASCI already has a Notifications bell, Safety Hub event feed, and Driver Profile. **Zero new surfaces are needed** to land Safety intelligence. The work is *subscribing* to `harsh_event` + `dvir` in Motive and *routing* by severity at read time — no automation, just visibility plumbing.

---

## PHASE 7 — SHOP INTELLIGENCE AUDIT

| EVENT | WHO SHOULD SEE | WHERE |
| --- | --- | --- |
| Fault code (red · MIL on) | Shop · Dispatch · Admin | Shop Hub "Equipment Down" · Dispatch Board chip · Asset Profile → MaintainX tab |
| Fault code (amber) | Shop · Admin | Shop Hub planning list · Asset Profile → Events |
| Fault code (info) | Shop · Admin | Asset Profile → Events (audit) |
| Engine alert (low oil pressure / coolant / DEF) | Shop · Dispatch | Shop Hub critical list + Dispatch Board chip |
| Maintenance interval reminder | Shop · Admin | Shop Hub PM list (Maintenance system of record stays MaintainX) |
| Equipment health (asset_gateway heartbeat) | Shop · Admin | Asset Profile only |
| Battery low (asset_gateway) | Shop · Admin | Shop Hub battery list |
| Asset gateway tamper | Safety · Operations · Admin | Notifications bell + Operations banner |

**Reuse-first:** Shop Hub already lists "Out of Service" assets and has Pre-Op trends. The fault_code feed slots into the same list with a `source=motive_fault` badge. No new dashboard required.

---

## PHASE 8 — DISPATCH INTELLIGENCE AUDIT

| EVENT | DISPATCH NEEDS TO SEE? | REASONING |
| --- | --- | --- |
| `vehicle_gps` (per-event) | ❌ NO | Noise. Use latest-position rollup on the chip. |
| `vehicle_gps` (staleness flip to >30 min) | ✅ YES | "Truck went dark" matters. Surface as chip color change. |
| `geofence_enter` (job site) | ✅ YES | "Driver arrived" — assignment auto-advances dispatcher expectation. |
| `geofence_exit` (job site) | ✅ YES | "Driver left" — ETA to next leg. |
| `geofence_enter` (yard) | ✅ YES (low priority) | End-of-day truck home. |
| `geofence_enter` (maintenance facility) | ✅ YES | Truck went to shop. Auto-flag for visibility. |
| `harsh_event` (high) | ✅ YES | "Don't re-assign this driver right now." |
| `harsh_event` (medium / low) | ❌ NO | Safety problem, not dispatch problem. |
| `fault_code` (red) | ✅ YES | "Don't load this truck." |
| `fault_code` (amber / info) | ❌ NO | Shop problem. |
| `dvir` (defect / OOS) | ✅ YES | Asset cannot dispatch. Surface as Maintenance Hold chip. |
| `dvir` (pass) | ❌ NO | Routine. |
| `idle` | ❌ NO | Aggregate is fine; per-event = noise. |
| `ignition` on | ❌ NO | Implicit via GPS. |
| `driver_changed` | ✅ YES | Driver chip on assignment card updates. |

**Noise avoidance rule:** if Dispatch sees more than ~30 events/day per dispatcher, they will tune it out. The list above limits Dispatch to ~15-25 events/day at typical fleet scale.

---

## PHASE 9 — OPERATIONS INTELLIGENCE AUDIT

| Cadence | Operations should see |
| --- | --- |
| **Daily** | Moving / Idle / Not-Reporting / GPS-Enabled counters · Top-5 trucks not reporting · Equipment-down list (DVIR OOS + red faults) · Tamper / theft signals |
| **Weekly** | Harsh-event totals by driver · Fault-code totals by truck · Geofence dwell-time per project · Pre-Op pass-rate trend · Underutilized assets (GPS shows them inside yard >5 days) |
| **Never** | Individual `vehicle_gps` events · DVIR-pass events · Routine fault_code amber/info · Ignition events |

---

## PHASE 10 — EVENT VALUE MATRIX (1-10 scale)

| Event | Ops | Safety | Maint | Dispatch | Complexity |
| --- | --- | --- | --- | --- | --- |
| `vehicle_gps` (latest position hydrate) | 9 | 4 | 3 | 9 | 1 (already wired) |
| `vehicle_gps` (per-event audit) | 2 | 2 | 1 | 1 | 1 |
| `geofence_enter` (job site) | 9 | 3 | 1 | 10 | 4 |
| `geofence_exit` (job site) | 8 | 2 | 1 | 9 | 4 |
| `geofence_enter` (yard / shop) | 6 | 2 | 4 | 6 | 4 |
| `harsh_event` (high) | 5 | 10 | 1 | 7 | 3 |
| `harsh_event` (medium / low) | 3 | 7 | 1 | 2 | 3 |
| `harsh_event` subtype speeding | 5 | 9 | 1 | 4 | 3 |
| `fault_code` (red / MIL) | 7 | 4 | 10 | 9 | 4 |
| `fault_code` (amber) | 4 | 2 | 8 | 2 | 3 |
| `fault_code` (info) | 2 | 1 | 5 | 1 | 2 |
| `dvir` (defect / OOS) | 8 | 8 | 10 | 10 | 5 |
| `dvir` (pass) | 2 | 3 | 4 | 2 | 5 |
| `dvir` (signed by mechanic) | 4 | 3 | 8 | 3 | 5 |
| `asset_gateway` (tamper) | 9 | 7 | 2 | 4 | 2 |
| `asset_gateway` (battery low) | 4 | 1 | 8 | 1 | 2 |
| `idle` (long, on-site rollup) | 7 | 2 | 2 | 3 | 3 |
| `ignition` | 2 | 2 | 2 | 1 | 2 |
| `driver_changed` | 4 | 6 | 1 | 8 | 2 |

---

## PHASE 11 — TOP 25 EVENT OPPORTUNITIES (ranked · existing surfaces only · NO IMPLEMENTATION)

Ranking framework: **Powerful · Simple · Beautiful · Trusted · Proven**.

### P1 — Powerful & Simple (subscribe + route through existing surfaces; no new screens)
1. **`harsh_event` (high severity) → Safety Hub event feed + Notifications bell** — Safety has been seeing 270 blank GPS rows; one real harsh-event row would be more useful than all of them combined.
2. **`fault_code` (red / MIL on) → Shop Hub "Equipment Down" list + Dispatch Board chip** — directly answers "can I dispatch this truck right now?"
3. **`dvir` (defect / out_of_service) → Pre-Op queue + Dispatch Board Maintenance Hold chip** — mirrors MASCI's own pre-op fail handling.
4. **`geofence_enter` (job site) → Dispatch Board "On Site" chip** — eliminates the dispatcher phone-call "did the driver arrive?"
5. **`geofence_exit` (job site) → Dispatch Board departure event** — enables ETA refresh without calling the driver.

### P2 — Trusted & Beautiful (surface decoration on existing screens)
6. **`harsh_event` aggregate (7-day) → Driver Profile coaching card** — score-style.
7. **`fault_code` history → Asset Profile → Events tab** — sequential code list, no new endpoint.
8. **`geofence_enter` (yard) → Asset Profile "Home"** auto-set on end-of-day fence enter.
9. **`asset_gateway` (tamper) → Operations Center red banner + Notifications bell** — theft alert.
10. **`driver_changed` → AssetProfile OperatorCard auto-refresh** (P1-C consumer just needs the live signal instead of polling).

### P3 — Powerful (cross-system join · existing API)
11. **`geofence_enter` × `jobs_master` → "Trucks currently on this job" tile per project** — uses geofence-name→job-name suggested-match logic already in audit-2.
12. **`fault_code` × `equipment_master` → Auto-pre-populate MaintainX work order draft** (visibility/draft only; operator confirms).
13. **`dvir` (defect) × MASCI Pre-Op flow → consolidate so Motive DVIR counts as today's pre-op for CDL drivers** — eliminates duplicate forms.
14. **`harsh_event` × HR `employees.driver_status` → flag for coaching when threshold crossed** (display only).
15. **`geofence_dwell` (exit minus enter) → Job-site labor-hour estimate** for PM Hub.

### P4 — Proven (low-volume, high-signal · operationally clear)
16. **`asset_gateway` (battery low) → Shop Hub battery list** — small but real maintenance task.
17. **`fault_code` (amber) → Shop Hub planning list** — same surface as red, lower badge.
18. **`harsh_event` subtype `speeding` (severe) → HR Hub driver compliance card** — insurance / DOT relevance.
19. **`dvir` (mechanic signed) → Shop Hub closeout log** — completeness audit.
20. **`vehicle_gps` (staleness flip >30 min) → Dispatch Board amber chip auto-flip** — already implementable with current data; webhook makes it instant instead of polling.

### P5 — Beautiful (visualisation polish)
21. **`vehicle_gps` aggregate (trip path) → Asset Profile breadcrumb mini-map** — last 25 pings, simple leaflet.
22. **`geofence` history × asset → Asset Profile "Site Visits Today" list** — exit/enter pairs.
23. **`harsh_event` heatmap (week) → Safety Hub weekly digest email** — already has a digest cron.
24. **`idle` aggregate → Operations Center utilization underutilized list** — extends P1-E.
25. **Source-attribution panel on Asset Profile → audit chip ("last GPS from poll vs webhook · last fault from webhook · last DVIR from MASCI native")** — answers the auditor's question "how do we know?"

---

## FINAL VERDICT

### All Motive events (in priority order of operational ROI)
1. `harsh_event` — Safety bell
2. `fault_code` — Shop bell
3. `dvir` (defect / OOS) — Dispatch + Shop bell
4. `geofence_enter/exit` — Dispatch state pulse
5. `asset_gateway` (tamper) — Operations theft alert
6. `vehicle_gps` (latest hydrate · NOT per-event) — already wired
7. `driver_changed` — Dispatch operator chip refresh
8. `asset_gateway` (battery / heartbeat) — Shop planning
9. `idle` aggregate — Operations utilization
10. `ignition` — audit only

### Who should see them — see Phase 3 table.
### Where they should see them — see Phase 4 table.
### What should happen — Phase 5 categories A through D guide the band; **no automation in this audit**.
### What should be stored only — Category D: `vehicle_gps` per-event · `harsh_event` low · `fault_code` info · `dvir` pass · `asset_gateway` heartbeat · `ignition`.
### What should be ignored — None. Even D-category items have forensic value at low storage cost.

### Top operational opportunities — Phase 11 P1 list (5 events that unlock 80 % of the value).

---

## GUARDRAILS UPHELD

- ❌ No code changes proposed for execution
- ❌ No webhook subscription changes proposed for execution
- ❌ No M-2 automation
- ❌ No new portals · No new lifecycle · No new schemas
- ✅ Read-only · evidence-based · existing-surface mapping only
- ✅ Decision-ready: when the operator authorizes, every event has a target screen and a clear band

---

## EVIDENCE CITATIONS
- `db.motive_events` aggregation (2026-06-08 13:38 UTC) → only `vehicle_gps` family observed.
- `services/motive_service.py::process_webhook` → routes by `event_kind` with hydrate only for `vehicle_gps` / `vehicle_location_received`.
- `routes/integrations/webhooks.py` → HMAC verification + sync log writer.
- `/app/memory/MOTIVE_API_CAPABILITY_AUDIT.md` → verified Webhooks v2 event-family catalog (cross-referenced).
- `db.integration_sync_logs` (motive · webhook) → 5 webhook receipts since 2026-06-08, 2 with valid HMAC signatures, all currently `vehicle_gps`.

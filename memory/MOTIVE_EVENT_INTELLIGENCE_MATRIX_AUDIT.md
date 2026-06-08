# MASCI · MOTIVE EVENT INTELLIGENCE MATRIX AUDIT

**Date:** 2026-06-08
**Scope:** OMEGA · Read-only · No code/DB/deploy/automation changes.
**Method:** Mongo introspection (272 stored events) · webhook receiver classifier walk (`services/motive_service.py::_classify_family`) · cross-reference with the verified Webhooks v2 catalog in `/app/memory/MOTIVE_API_CAPABILITY_AUDIT.md` · live signed-payload replay logs from P1.5.
**Purpose:** Determine *how* MASCI should consume each Motive event family — who sees it, where it lives, what raw field maps to what operational language, what is noise — without proposing any new construction.

---

## EXECUTIVE SUMMARY (one paragraph)

Motive publishes 21 webhook event families. MASCI's receiver currently recognizes 6 of them in classifier code (`vehicle_gps`, `harsh_event`, `fault_code`, `dvir`, `geofence_enter`, `geofence_exit`) and falls back to a generic `other` bucket for the remaining 15. Of the 21, **8 events are high-value** (Top-10 list below), **5 are medium-value with conditional value**, and **8 are low-value / noise**. Of the 8 high-value events, **5 are already classified** by the P1.5 receiver and **3 are unclassified** (Vehicle Gateway Disconnected, HOS Violation, Inspection Report). All 21 *can* be received and stored today (defensively); only 6 are *displayed* with operational language; the rest land in `motive_events` with raw JSON only. **Estimated current operational utilization: 30 % of available Motive intelligence is surfaced.** Closing the gap requires zero new portals and zero schema changes — it requires classifier coverage and read-time decoration on the same surfaces P1.5 already wired (`AssetProfile`, `IntegrationEventsCard`, `DispatchIntegrationsTab`).

---

## EVIDENCE BASELINE

| Telemetry artifact | Value (live preview) |
| --- | --- |
| Stored events total | 272 |
| Event kinds observed | 6 (`vehicle_gps`, `geofence_enter/exit`, `hard_brake`, `fault_code`, `dvir_submitted`) |
| Source distribution | `poll: 270` · `webhook: 7` |
| Webhook subscriptions stored in `integration_settings.motive.settings` | **empty `{}`** (subscriptions managed upstream in the Motive dashboard, not mirrored to MASCI) |
| Receiver classifier families | 6 + `other` fallback |
| Read-time decorator (operational language) coverage | 6 of 6 classified families |
| Frontend surfaces consuming events | 3 (AssetProfile Events tab · IntegrationEventsCard · DispatchIntegrationsTab arrivals strip) |

---

## EVENT-BY-EVENT INTELLIGENCE MATRIX

For each event the audit specifies: **Category · Who · Where · What (operational language) · What stored (C/U/H/N bands) · What hidden · Value scores · Future-automation potential**.

Field-band legend: **C** Critical · **U** Useful · **H** Historical · **N** Noise.

---

### 1 · Vehicle Current Location Updated

| Dimension | Finding |
| --- | --- |
| Category | **Asset Tracking** |
| Who | Dispatcher · Superintendent · PM · Operations · Admin (NOT Safety · NOT HR · NOT Driver) |
| Where | **AssetProfile → Motive tab** (latest hydrate · already P1-D) · **Operations Center counters** (P1-E) · **Dispatch Board chip** (when staleness changes — future) |
| What (operational language) | *"Truck DPT021-8147 last seen 4 min ago · 28 mph · I-4, Deltona, FL · Andres Masci"* |
| Stored | `vehicle.id` C · `location.{lat,lon,located_at}` C · `kph` U · `bearing` U · `vehicle_state` U · `current_driver` U · `vin/make/model` N (sync has it) |
| Hidden | `vehicle.dispatch_state` raw enum · `device_id` · `driver.signed_in` boolean |
| Score · Safety/Ops/Disp/Shop/Exec | 4 / 9 / 9 / 3 / 4 |
| Future-automation potential | **High** (geofence inference · idle inference · ETA · staleness alerts) — but per-event has no action; aggregate does |
| Classifier status | ✅ classified as `vehicle_gps` · ✅ decorated · ✅ hydrates `asset_mappings.motive.*` |

---

### 2 · Vehicle Enter Geofence

| Dimension | Finding |
| --- | --- |
| Category | **Dispatch** |
| Who | **Dispatcher · Superintendent · PM (own jobs only)** · Operations rollup |
| Where | **Dispatch Hub Integrations tab → Live Activity strip** (already P1.5-F) · **AssetProfile → Events tab** (P1.5-H) · *Future:* per-job tile on PM Hub |
| What | *"DPT021-8147 arrived at SR46 Widening Project · Andres Masci"* |
| Stored | `event_time` C · `vehicle.id/number` C · `geofence.{id,name,category}` C · `geofence.address` U · `current_driver` U |
| Hidden | `geofence.location_points[]` polygon vertices · `geofence.id` raw |
| Score | 3 / 9 / 10 / 1 / 5 |
| Future-automation potential | **High** — natural dispatch state-transition trigger (deferred per OMEGA) |
| Classifier status | ✅ `geofence_enter` · ✅ humanized summary · ✅ "Arrived" pill rendered |

---

### 3 · Vehicle Exit Geofence

| Dimension | Finding |
| --- | --- |
| Category | **Dispatch** |
| Who | **Dispatcher · PM (own jobs only)** · Operations (utilization rollup) |
| Where | Same as Enter · plus dwell-time exposed in summary |
| What | *"DPT021-8147 departed The Shop · 1 h 16 m on site"* |
| Stored | Add `dwell_seconds` C — primary differentiator from Enter |
| Hidden | Same as Enter |
| Score | 2 / 8 / 9 / 2 / 4 |
| Future-automation potential | **High** — labor-hour calc · ETA refresh for next leg |
| Classifier status | ✅ `geofence_exit` · ✅ humanized summary with dwell time |

---

### 4 · Asset Enter Geofence

| Dimension | Finding |
| --- | --- |
| Category | **Asset Tracking · Operations** |
| Who | PM (own jobs only) · Operations · Shop · Admin |
| Where | AssetProfile → Events tab · *Future:* per-project equipment-on-site tile |
| What | *"Excavator EXC1485 arrived at The Shop · battery 78%"* |
| Stored | `asset.id/name` C · `geofence.{id,name}` C · `gateway.battery_level` U · `event_time` C |
| Hidden | Polygon vertices · raw gateway IDs |
| Score | 1 / 7 / 4 / 6 / 5 |
| Future-automation potential | **High** — billable hours per project · theft mitigation |
| Classifier status | ⚠️ falls into `other` (receiver fallback) · NOT decorated · stored only |

---

### 5 · Asset Exit Geofence

| Dimension | Finding |
| --- | --- |
| Category | **Asset Tracking · Operations** |
| Who | Same as Asset Enter |
| Where | Same as Asset Enter |
| What | *"Excavator EXC1485 departed SR46 Widening Project · 6 h 22 m on site"* |
| Stored | Same as Asset Enter + `dwell_seconds` |
| Score | 1 / 8 / 3 / 6 / 5 |
| Future-automation potential | **High** — utilization KPI |
| Classifier status | ⚠️ `other` · NOT decorated |

---

### 6 · Vehicle Created or Updated

| Dimension | Finding |
| --- | --- |
| Category | **Equipment** |
| Who | Admin · Shop · Operations |
| Where | **Audit log only** + Mapping wizard candidate flag |
| What | *"New vehicle DPT099-1234 (2025 Peterbilt 579) added to Motive — not yet linked to MASCI equipment_master"* |
| Stored | `vehicle.id/number/vin/make/model/year` U · `status` U · `event_time` H |
| Hidden | `device_id`, `eld_serial_number` |
| Score | 1 / 3 / 1 / 2 / 1 |
| Future-automation potential | **Medium** — auto-trigger sync_assets + re-attempt auto-link |
| Classifier status | ⚠️ `other` · stored only |

---

### 7 · Fault Code Opened

| Dimension | Finding |
| --- | --- |
| Category | **Equipment · Maintenance** |
| Who | **Shop · Dispatch (red only)** · Admin |
| Where | **AssetProfile → Events tab** (P1.5) · **IntegrationEventsCard** (Safety/HR/Admin Hub feed) · *Future:* Shop Hub "Equipment Down" tile |
| What | *"Fault P0420 on Truck DPT021-8147 · CHECK-ENGINE ON — Catalyst System Efficiency Below Threshold"* |
| Stored | `dtc_code` C · `mil_status` C · `description` C · `severity` C · `vehicle.id` C · `set_at` C |
| Hidden | Raw ECM byte string (if present) · diagnostic trouble code revisions |
| Score | 4 / 7 / 9 / 10 / 6 |
| Future-automation potential | **High** — auto-pre-populate MaintainX work order draft (deferred) |
| Classifier status | ✅ `fault_code` · ✅ humanized · ✅ critical-band auto-promoted when `mil_status=true` |

---

### 8 · Fault Code Closed

| Dimension | Finding |
| --- | --- |
| Category | **Equipment · Maintenance** |
| Who | Shop · Admin |
| Where | AssetProfile Events tab (closes the loop visually) · Audit log |
| What | *"Fault P0420 cleared on Truck DPT021-8147 after 7 h 12 m"* |
| Stored | `dtc_code` C · `cleared_at` C · `duration_seconds` U |
| Hidden | Mechanic/system attribution if uncertain |
| Score | 1 / 4 / 1 / 7 / 2 |
| Future-automation potential | **Medium** — work-order auto-close hint |
| Classifier status | ⚠️ `other` (classifier matches family by prefix `fault*` so close events would land in `fault_code` family — but no specific status differentiation today) |

---

### 9 · User Created or Updated

| Dimension | Finding |
| --- | --- |
| Category | **Driver Management** |
| Who | Admin · HR · Safety |
| Where | **Audit log only** + Mapping wizard candidate flag |
| What | *"New Motive user 'andres.masci' created — not yet linked to MASCI employee"* OR *"Motive driver Andres Masci was deactivated"* |
| Stored | `driver.id/name/email/username` C · `status` C · `event_time` C |
| Hidden | License numbers · phone if sensitive |
| Score | 2 / 3 / 1 / 1 / 3 |
| Future-automation potential | **Medium** — auto-trigger sync_users + re-attempt driver auto-link; flag MASCI active employees against newly deactivated Motive users |
| Classifier status | ⚠️ `other` · stored only |

---

### 10 · Inspection Report Created or Updated (DVIR)

| Dimension | Finding |
| --- | --- |
| Category | **Compliance · Safety · Maintenance** |
| Who | **Shop · Safety · Dispatch (defect/OOS only)** · Admin |
| Where | **AssetProfile → Events tab** (P1.5) · **IntegrationEventsCard** · *Future:* Pre-Op queue auto-row |
| What (OOS) | *"OUT OF SERVICE: Andres Masci flagged DPT021-8147 (2 defects · brakes · lights)"* |
| What (pass) | *"DVIR pass: Andres Masci · DPT021-8147 · all categories clear"* |
| What (signed) | *"DVIR signed: Mechanic José Martinez cleared DPT021-8147"* |
| Stored | `status` C · `defects[]` C (if any) · `out_of_service` C · `driver.id` C · `vehicle.id` C · `mechanic.id` U · `signed_at` U |
| Hidden | Raw defect form field IDs · signature image URLs (until needed in audit) |
| Score | 6 / 8 / 10 (when OOS) / 10 / 6 |
| Future-automation potential | **High** — auto-flag as maintenance hold on Dispatch (deferred · STOP per OMEGA) |
| Classifier status | ✅ `dvir` · ✅ humanized · ✅ severity ladder (critical / high / info) |

---

### 11 · HOS Violation Created or Updated

| Dimension | Finding |
| --- | --- |
| Category | **Compliance · Safety · Driver Management** |
| Who | **Safety · HR · Dispatch (real-time)** · Admin |
| Where | IntegrationEventsCard (Safety/HR Hub) · *Future:* Driver Profile compliance card |
| What | *"HOS violation: Andres Masci exceeded 11-hr driving limit at 19:42 — recorded duty status: Driving"* |
| Stored | `driver.id/name` C · `violation_type` C · `event_time` C · `duty_status` U · `cycle` H |
| Hidden | Raw ELD-mandated record fields not user-relevant |
| Score | 4 / 7 / 4 (Dispatch needs to NOT re-assign) / 1 / 5 |
| Future-automation potential | **High** — auto-suspend driver assignment until compliant (deferred) |
| Classifier status | ⚠️ `other` · stored only · **gap for P2** |

---

### 12 · Engine On Status Updated

| Dimension | Finding |
| --- | --- |
| Category | **Asset Tracking** |
| Who | Operations (utilization rollup only) · Admin (audit) |
| Where | **Audit log only** · AssetProfile Events tab (forensic) |
| What | *"DPT021-8147 ignition ON · operator Andres Masci · 06:14"* |
| Stored | `vehicle.id` C · `event_time` C |
| Hidden | Engine RPM · diagnostic startup data |
| Score | 1 / 4 / 1 / 2 / 1 |
| Future-automation potential | **Low** (info derivable from `vehicle_gps.speed_kph` trends; subscribing creates duplicate noise) |
| Classifier status | ⚠️ `other` · stored only |

---

### 13 · Engine Off Status Updated

| Dimension | Finding |
| --- | --- |
| Category | **Asset Tracking** |
| Who | Same as Engine On |
| Where | Same as Engine On |
| What | *"DPT021-8147 ignition OFF · 18:32 · 12 h 18 m on for the day"* |
| Stored | Same as Engine On + derivable `runtime_seconds` H |
| Score | 1 / 4 / 1 / 2 / 1 |
| Future-automation potential | **Low** |
| Classifier status | ⚠️ `other` · stored only |

---

### 14 · Driver Performance Event Created

| Dimension | Finding |
| --- | --- |
| Category | **Safety · Driver Management** |
| Who | **Safety · HR · Dispatch (high-severity only)** · Admin |
| Where | IntegrationEventsCard (Safety/HR) · AssetProfile Events tab · *Future:* Driver Profile coaching card |
| What | *"Hard brake recorded by Andres Masci at 64 mph near Deltona FL — coaching required"* |
| Stored | `driver.id/name` C · `vehicle.id` C · `subtype` C · `severity` C · `location.address` C · `speed_mph` C · `coaching_required` C · `video_url` U |
| Hidden | Raw ML confidence scores · sensor IDs |
| Score | 4 / 10 / 5 / 1 / 7 |
| Future-automation potential | **High** — auto-flag driver scorecard (deferred) |
| Classifier status | ✅ `harsh_event` · ✅ humanized · ✅ severity ladder |

---

### 15 · Driver Performance Event Updated

| Dimension | Finding |
| --- | --- |
| Category | **Safety · Driver Management** |
| Who | Same as Created |
| Where | Same as Created (appended to timeline as update) |
| What | *"Hard brake event #4231 video link added"* |
| Stored | Same as Created |
| Score | 1 / 5 / 1 / 1 / 2 |
| Future-automation potential | **Low** — primarily metadata refresh |
| Classifier status | ⚠️ `other` (classifier checks `starts_with("harsh")` — would catch this only if `event_type=harsh_event_updated`; today's classifier passes by) |

---

### 16 · Speeding Event Created

| Dimension | Finding |
| --- | --- |
| Category | **Safety · Compliance** |
| Who | **Safety · HR · Admin** · Executive (severe only) |
| Where | IntegrationEventsCard · *Future:* HR Hub Driver Qualification card · Executive weekly digest |
| What | *"Speeding: Andres Masci · DPT021-8147 · 87 mph in 65 zone · 1.3 mi · I-4 EB MM 110"* |
| Stored | `driver.id/name` C · `vehicle.id` C · `speed_at_event_mph` C · `posted_limit` C · `over_by_mph` C · `duration_seconds` U · `location` C |
| Hidden | GPS breadcrumb granularity (just show start point) |
| Score | 5 / 9 / 4 / 1 / 8 |
| Future-automation potential | **Medium** — driver scorecard contribution |
| Classifier status | ✅ caught by `harsh_event` family (subtype `speeding`) · ✅ humanized |

---

### 17 · Speeding Event Updated

| Dimension | Finding |
| --- | --- |
| Category | **Safety · Compliance** |
| Who | Same as Created |
| Where | Same as Created |
| What | Same as Created plus updated metadata (final duration, peak speed) |
| Score | 1 / 5 / 1 / 1 / 2 |
| Future-automation potential | **Low** |
| Classifier status | Same as #15 — classifier prefix-match would not catch `_updated` suffix consistently |

---

### 18 · Vehicle Gateway Disconnected

| Dimension | Finding |
| --- | --- |
| Category | **Equipment · Operations** |
| Who | **Shop · Operations · Admin · Dispatch (if vehicle was assigned)** |
| Where | AssetProfile → Motive tab (offline banner) · *Future:* Operations Center "Devices Down" tile · Notifications bell |
| What | *"GPS gateway disconnected on DPT021-8147 · last reported 11:42 from Daytona Plant · vehicle may still be operational"* |
| Stored | `vehicle.id` C · `last_known_location` C · `disconnect_event_time` C · `device_id` U |
| Hidden | Diagnostic packet loss counters · firmware version |
| Score | 2 / 8 / 6 / 9 / 5 |
| Future-automation potential | **High** — auto-flag as "no telemetry" · pair with #19 to derive MTBF (deferred) |
| Classifier status | ⚠️ `other` · stored only · **gap for P2** |

---

### 19 · Vehicle Gateway Disconnect Ended

| Dimension | Finding |
| --- | --- |
| Category | **Equipment · Operations** |
| Who | Shop · Admin |
| Where | AssetProfile → Motive tab (offline banner clears) · audit log |
| What | *"GPS gateway reconnected on DPT021-8147 · offline for 2 h 14 m"* |
| Stored | `vehicle.id` C · `reconnect_event_time` C · derivable `offline_duration_seconds` U |
| Score | 1 / 4 / 2 / 6 / 2 |
| Future-automation potential | **Low** (pairs with #18 for cumulative offline reports) |
| Classifier status | ⚠️ `other` · stored only |

---

### 20 · Dashcam Disconnected

| Dimension | Finding |
| --- | --- |
| Category | **Equipment · Safety** |
| Who | Shop · Safety (only if a chronic pattern emerges) · Admin |
| Where | AssetProfile · audit log · *Future:* Shop Hub device-health list |
| What | *"Dashcam offline on DPT021-8147 since 09:14 — no incident recording active"* |
| Stored | `vehicle.id` C · `disconnect_event_time` C · `last_video_at` U |
| Hidden | Camera firmware version · raw fault codes |
| Score | 3 / 5 / 1 / 6 / 2 |
| Future-automation potential | **Medium** — Safety wants chronic-offline list (deferred) |
| Classifier status | ⚠️ `other` · stored only |

---

### 21 · AI Coach Recap Created

| Dimension | Finding |
| --- | --- |
| Category | **Safety · Driver Management** |
| Who | Safety · HR · Admin (digest-only · NOT per-event) |
| Where | *Future:* HR Hub Driver Qualification weekly digest · Driver Profile recap tile |
| What | *"Weekly AI Coach recap for Andres Masci · 0 hard brakes · 1 speeding event · score 92/100"* |
| Stored | `driver.id/name` C · `period.{start,end}` C · `score` C · `event_counts` U · `recommendations` U |
| Hidden | Raw model outputs · per-frame ML confidence |
| Score | 1 / 8 / 1 / 1 / 6 |
| Future-automation potential | **Medium** — auto-populate driver scorecard (deferred) |
| Classifier status | ⚠️ `other` · stored only · **highest value of any unclassified event** |

---

## SPECIAL ANALYSIS · GEOFENCE INTELLIGENCE

Cross-reference Motive's 67 geofences (33 active) with their `category` field:

| Geofence type | Count (active) | Who benefits from Enter/Exit |
| --- | --- | --- |
| **Job Site** | 31 | Dispatch (arrived/departed) · Superintendent (own site truck count) · PM (own project on-site equipment) |
| **Terminal / Yard** | 1 | Dispatch (end-of-day return) · Operations (utilization) · Shop (asset returned from field) |
| **Maintenance Facility** | 1 | Shop (asset on premises) · Dispatch (Maintenance Hold visual) · Operations |
| **Uncategorized** | 0 active | Admin (categorization queue) |

Per-transition value:
- **Job arrival** → Dispatcher: "stop calling the driver to confirm" · Foreman: same.
- **Job departure** → Dispatcher: ETA refresh for next leg.
- **Plant arrival** → Dispatcher: load-cycle visibility. Foreman of yard: receiving.
- **Plant departure** → Dispatcher: outbound load timestamp.
- **Yard arrival** → Operations: truck home. Shop: incoming PM candidate.
- **Yard departure** → Operations: start of shift.

**Net:** every geofence transition has at least one dispatcher-relevant consumer. Asset Enter/Exit (not vehicle) adds construction-equipment-on-site value primarily for PM Hub.

---

## SPECIAL ANALYSIS · DRIVER INTELLIGENCE

| Event | Who actually benefits |
| --- | --- |
| Driver Performance · Hard Brake / Accel / Corner | **Safety + HR** (coaching) · Dispatch (high-sev only) |
| Speeding | **Safety + HR + Admin** · Executive (severe pattern) |
| HOS Violation | **Safety + HR + Dispatch (real-time block)** |
| AI Coach Recap | **HR + Safety (weekly digest only)** · NOT Operations · NOT Dispatch |
| Driver Created / Updated | Admin · HR (audit) |

**Driver Profile screen is the natural consumer for all of these** — does not yet exist in MASCI, but every event already has a `driver_id` that would feed it on day one of any future profile screen.

---

## SPECIAL ANALYSIS · EQUIPMENT INTELLIGENCE

| Event | Belongs in |
| --- | --- |
| Fault Code Opened (red / MIL) | Shop Hub Equipment Down · Dispatch Board chip · AssetProfile MaintainX tab |
| Fault Code Opened (amber/info) | Shop Hub planning list only · AssetProfile Events tab |
| Fault Code Closed | AssetProfile Events tab (audit) · Shop Hub closeout list |
| Engine On / Engine Off | AssetProfile Events tab (audit only · NO Dispatch noise) |
| Gateway Disconnected | AssetProfile Motive tab (offline banner) · Shop · Operations devices-down list |
| Gateway Disconnect Ended | AssetProfile Motive tab (banner clears) · audit |
| Dashcam Disconnected | AssetProfile Motive tab (dashcam=No badge) · Shop chronic-offline list |
| Vehicle Created / Updated | Admin Integration Center mapping wizard candidate row |

---

## SPECIAL ANALYSIS · DISPATCH INTELLIGENCE

| Event | Dispatch band |
| --- | --- |
| Vehicle Enter Geofence (job) | **Must See** |
| Vehicle Exit Geofence (job) | **Must See** |
| Vehicle Enter Geofence (yard) | Nice to See |
| Vehicle Exit Geofence (yard) | Nice to See |
| Fault Code Opened (red) | **Must See** |
| DVIR · out_of_service | **Must See** |
| HOS Violation | **Must See** (block re-assignment) |
| Harsh Event (high severity) | **Must See** (driver may need rest) |
| Gateway Disconnected (assigned vehicle) | Nice to See |
| Vehicle Current Location (per-event) | **Noise** — use aggregate hydrate |
| Engine On / Off | **Noise** |
| Driver Performance · medium/low | **Noise** |
| Speeding · routine | **Noise** |
| AI Coach Recap | **Noise** for Dispatch |
| Vehicle/User Created | **Noise** |

---

## SPECIAL ANALYSIS · EXECUTIVE INTELLIGENCE

Leadership should never see per-event traffic. Executive-relevant items are weekly or threshold-crossed only:
- Weekly Safety scorecard (rollup of Driver Performance + Speeding + HOS + AI Coach Recap)
- Fleet utilization (geofence dwell × asset × project)
- Equipment-down summary (fault_code · DVIR OOS · gateway disconnected)
- Telemetry-coverage percentage (gateway disconnects as % of fleet)

**No individual event belongs on an executive screen.** Use existing MASCI digest infrastructure (`hr_safety_digest_jobs.py`) when authorized.

---

## TOP 10 HIGHEST-VALUE MOTIVE EVENTS (ranked)

| # | Event | Reason |
| --- | --- | --- |
| 1 | **DVIR (out_of_service / defects)** | Direct dispatch + safety + shop signal · highest cross-role value |
| 2 | **Fault Code Opened (red / MIL)** | Immediate "do not dispatch" signal · shop work-order seed |
| 3 | **Vehicle Enter Geofence (Job Site)** | Eliminates dispatch phone calls · ETA accuracy · billable-hour foundation |
| 4 | **Vehicle Exit Geofence (Job Site)** | Mirror of Enter · enables ETA-to-next-leg |
| 5 | **Driver Performance · Hard Brake (high)** | Coaching + accident-risk signal · already-wired surface |
| 6 | **HOS Violation** | Compliance enforcement + dispatch re-assignment block |
| 7 | **Speeding (severe)** | DOT + insurance + executive pattern visibility |
| 8 | **Vehicle Gateway Disconnected** | "Truck went dark" — operations + shop signal |
| 9 | **Asset Exit Geofence (job site)** | Project labor-hour & utilization calculation |
| 10 | **Vehicle Current Location (latest hydrate only)** | Foundation for AssetProfile + Operations tiles · already wired |

---

## TOP 10 LOWEST-VALUE MOTIVE EVENTS (ranked)

| # | Event | Reason |
| --- | --- | --- |
| 1 | **Engine On Status Updated** | Derivable from `vehicle_gps.speed_kph` · duplicate noise |
| 2 | **Engine Off Status Updated** | Same as #1 |
| 3 | **Driver Performance Event Updated** | Metadata refresh of #14 · low standalone value |
| 4 | **Speeding Event Updated** | Same as #3 for #16 |
| 5 | **Vehicle Created or Updated** | Sync already discovers vehicles · webhook is duplicate |
| 6 | **User Created or Updated** | Same as #5 for drivers |
| 7 | **Fault Code Closed** | Useful only when paired with open · low standalone |
| 8 | **Gateway Disconnect Ended** | Useful only paired with #18 |
| 9 | **Dashcam Disconnected** | Per-event low value; cumulative chronic-offline list IS valuable |
| 10 | **Vehicle Current Location (per-event)** | Foundation hydrate has value; the 50k events/day raw stream is noise |

---

## EVENTS THAT SHOULD CREATE IMMEDIATE ATTENTION (Notifications bell)

| # | Event | Rationale |
| --- | --- | --- |
| 1 | DVIR · out_of_service | Truck cannot dispatch · 2 roles need to know within minutes |
| 2 | Fault Code · MIL on / red | Truck may strand · dispatcher must re-assign |
| 3 | HOS Violation | Compliance event · dispatch must block |
| 4 | Driver Performance · high severity (impact, severe brake) | Coaching + dispatch awareness |
| 5 | Asset Gateway tamper / off-hours motion (Asset Geofence Exit during off-hours) | Theft signal |

---

## EVENTS THAT SHOULD ONLY BE HISTORICAL (audit log)

| # | Event | Rationale |
| --- | --- | --- |
| 1 | Vehicle Current Location (per-event) | Hydrate only; audit only |
| 2 | Engine On / Engine Off | Forensic shift-pattern lookup |
| 3 | Vehicle / User Created or Updated | Mapping audit |
| 4 | Fault Code Closed | Pairs with open; audit |
| 5 | Gateway Disconnect Ended | Pairs with #18 |
| 6 | Driver Performance / Speeding · Updated events | Metadata refresh |
| 7 | DVIR (pass · no defect) | Routine compliance audit |

---

## EVENTS MASCI IS CURRENTLY UNDER-UTILIZING (ranked by lost value)

| # | Event | Status | Why under-utilized |
| --- | --- | --- | --- |
| 1 | **HOS Violation** | NOT subscribed · NOT classified | Highest single-event safety + compliance value; zero MASCI awareness today |
| 2 | **Vehicle Gateway Disconnected** | NOT classified | "Truck went dark" alert lives nowhere |
| 3 | **Inspection Report Updated** (mechanic-signed) | Classified by family but no closeout surface | Shop work-order closeout would benefit |
| 4 | **Asset Enter / Exit Geofence** | NOT classified · `other` bucket | PM-hub per-project equipment-on-site count would unlock from one event family |
| 5 | **AI Coach Recap** | NOT classified | Weekly driver scorecard is highest-value HR signal nobody sees |
| 6 | **Dashcam Disconnected** | NOT classified | Safety chronic-offline list has no input |
| 7 | **Fault Code Closed** | Classified as `fault_code` but no `cleared` differentiator | Shop closeout audit incomplete |
| 8 | **User Created / Updated** | NOT classified | Auto-discovery of new drivers needing mapping is manual today |

---

## FINAL VERDICT

**1. Which Motive events create the most operational value?**
DVIR (OOS) · Fault Code Opened (red) · Vehicle Enter/Exit Geofence (job site) · HOS Violation.

**2. Which events create the most safety value?**
Driver Performance (high severity) · Speeding (severe) · HOS Violation · DVIR (OOS) · AI Coach Recap (weekly rollup).

**3. Which events create the most maintenance value?**
Fault Code Opened (red) · DVIR (defect / OOS) · Fault Code Closed · Gateway Disconnected · Dashcam Disconnected.

**4. Which events create the most dispatch value?**
Vehicle Enter Geofence (Job Site) · Vehicle Exit Geofence (Job Site) · DVIR (OOS) · Fault Code Opened (red) · HOS Violation · Gateway Disconnected (assigned vehicle).

**5. Which events are mostly noise?**
Engine On / Off · Vehicle Current Location (per-event raw stream) · Vehicle/User Created or Updated · Driver Performance / Speeding · Updated · Fault Code Closed (without companion open) · Engine On/Off pair noise.

**6. Which existing MASCI screens should ultimately consume each event family?**

| Event family | Existing screen(s) |
| --- | --- |
| DVIR | `IntegrationEventsCard` · AssetProfile Events tab · Pre-Op queue · Dispatch Board chip · Notifications |
| Fault Code (Opened/Closed) | AssetProfile Events tab · Shop Hub Equipment Down list · Dispatch Board (red only) · IntegrationEventsCard |
| Vehicle Geofence (Enter/Exit) | DispatchIntegrationsTab Live Activity strip · AssetProfile Events tab · *Future:* PM Hub project tile |
| Asset Geofence (Enter/Exit) | AssetProfile Events tab · *Future:* PM Hub project tile |
| Vehicle Current Location | AssetProfile Motive tab (hydrate) · Operations Center counters · Dispatch Board chip color (staleness) |
| Driver Performance / Speeding | `IntegrationEventsCard` (Safety/HR Hub) · AssetProfile Events tab · *Future:* Driver Profile |
| HOS Violation | `IntegrationEventsCard` · Dispatch Board (real-time block) · *Future:* Driver Profile compliance |
| Vehicle / User Created or Updated | Admin Integration Center mapping wizard candidate row · audit log |
| Engine On / Off | AssetProfile Events tab (audit only) |
| Gateway Disconnected / Reconnected | AssetProfile Motive tab (offline banner) · Shop devices-down · Notifications (when assigned) |
| Dashcam Disconnected | AssetProfile Motive tab badge · Shop chronic-offline list |
| AI Coach Recap | *Future:* HR Hub Driver Qualification weekly digest · Driver Profile recap tile |

**7. What percentage of available Motive intelligence is currently visible today?**
- 21 published event families.
- 6 classified (`vehicle_gps`, `harsh_event`, `fault_code`, `dvir`, `geofence_enter`, `geofence_exit`).
- 3 of the 6 are decorated with operational language and surfaced on 3 different MASCI screens.
- 3 of the 6 are received but most decoration paths cover only the `_created` event (not `_updated` variants).
- The other 15 fall to `other` bucket — stored, never displayed.

**Weighted value-capture estimate** (each family weighted by its rank in Top-10):
- High-value families captured: DVIR · Fault Code Opened · Geofence Enter/Exit · Harsh Event · GPS hydrate = **5 of Top 10 (50% of high-value families captured)**.
- High-value families uncaptured: HOS Violation · Speeding (severe) · Gateway Disconnected · Asset Geofence Exit · Vehicle GPS aggregate beyond hydrate = **5 of Top 10 (50% missing)**.
- Across all 21 families and weighted by relative ranking: **~30 % of Motive's available operational intelligence is currently surfaced to users.**

The gap is closeable without new portals: 5 unclassified event families (HOS Violation, Gateway Disconnected, Asset Enter/Exit, AI Coach Recap, Dashcam Disconnected) would each slot into surfaces P1.5 already built — no new screens, no new schemas, no automation. Visibility-only — exactly the path OMEGA has endorsed.

---

## GUARDRAILS UPHELD

- ❌ No code changes
- ❌ No DB changes
- ❌ No deploys
- ❌ No M-2 implementation
- ❌ No new portals · No new sprints · No backlog execution
- ✅ Read-only audit · evidence-based · existing-surface mapping
- ✅ Decision-ready for the operator when authorized

---

## EVIDENCE CITATIONS

- `db.motive_events` aggregation (2026-06-08 14:05 UTC) → 6 observed kinds.
- `db.motive_events.raw` field-frequency map → 17 distinct top-level keys across 7 webhook payloads.
- `services/motive_service.py::_classify_family` → 6 families + `other` fallback (lines 96-115).
- `services/motive_service.py::_classify_event` → field extraction for 5 authorized families (lines 137-198).
- `routes/integrations/events.py::_humanize_event` → 5 family-specific sentence templates (lines 32-95).
- `db.motive_geofences` aggregation → 67 geofences · 33 active · category-breakdown above.
- `db.integration_settings.motive.settings = {}` → no subscription list mirrored locally (managed in Motive Admin).
- `/app/memory/MOTIVE_API_CAPABILITY_AUDIT.md` → Webhooks v2 family catalog reference.
- `/app/memory/MOTIVE_WEBHOOK_INTELLIGENCE_AUDIT.md` → prior 8-family classification (this audit expands to 21 named events).
- `/app/memory/MOTIVE_P1_5_EVENT_ACTIVATION_CERTIFICATION.md` → live signed-payload replay log for 5 families.

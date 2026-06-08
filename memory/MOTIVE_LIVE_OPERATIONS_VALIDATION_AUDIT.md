# MASCI · MOTIVE LIVE OPERATIONS VALIDATION AUDIT

**Date:** 2026-06-08
**Scope:** OMEGA · Read-only · production data introspection only.
**Method:** Direct Mongo aggregation across `motive_events`, `asset_mappings`, `employee_mappings`, `motive_geofences`, `integration_sync_logs` (live preview env).
**Verdict:** 🟡 **PARTIALLY PROVEN**

---

## EXECUTIVE SUMMARY (one paragraph)

Pipeline reality is **solid**: every authorized event family classifies, decorates, stores, and renders correctly when payloads arrive. Operational reality is **empty**: no live Motive subscription has fired yet beyond `vehicle_gps`, so the 14 webhook rows MASCI has stored to date are 100 % sprint-replay traffic (P1.5 + P1.6 validation). Motive's upstream dashboard is still configured to send only `vehicle_gps`. The 158 GPS-enabled vehicles in MASCI's mapping table are themselves stale — 0 reported in the last 30 min, only 63 reported in the last 24 h, and 71 (45 %) haven't reported in over 30 days. This is not a MASCI defect — it is the unsurprising consequence of the operator having not yet enabled the 8 P1.6 event subscriptions in Motive Admin and not having scheduled the periodic `sync_events` poll. **MASCI cannot be PROVEN against production until Motive starts sending production events.** Everything MASCI's side needs is in place.

---

## PHASE 1 — LIVE EVENT VALIDATION

### Event counts by family × time window (live `db.motive_events`)

| Family | 24 h | 7 d | 30 d | all-time | webhook | poll |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `vehicle_gps` | 0 | 0 | 0 | **272** (all pre-P1.6 stamping · no `event_family`) | 0 | 272 |
| `harsh_event` | 1 | 1 | 1 | 1 | 1 | 0 |
| `fault_code` | 1 | 1 | 1 | 1 | 1 | 0 |
| `fault_code_closed` | 1 | 1 | 1 | 1 | 1 | 0 |
| `dvir` | 2 | 2 | 2 | 2 | 2 | 0 |
| `geofence_enter` | 1 | 1 | 1 | 1 | 1 | 0 |
| `geofence_exit` | 1 | 1 | 1 | 1 | 1 | 0 |
| `asset_geofence_enter` | 1 | 1 | 1 | 1 | 1 | 0 |
| `asset_geofence_exit` | 1 | 1 | 1 | 1 | 1 | 0 |
| `hos_violation` | 1 | 1 | 1 | 1 | 1 | 0 |
| `gateway_disconnected` | 1 | 1 | 1 | 1 | 1 | 0 |
| `gateway_reconnected` | 1 | 1 | 1 | 1 | 1 | 0 |
| `ai_coach_recap` | 1 | 1 | 1 | 1 | 1 | 0 |
| `other` | 1 | 1 | 1 | 1 | 1 | 0 |

**Total real events: 286.** Source breakdown:
- `poll`: 272 (all from `sync_events` runs during M-1 / P1 sprints · `event_family` was never stamped because P1.6 introduced the field)
- `webhook`: 14 (every one is from P1.5 / P1.6 signed-payload replay tests · NOT production traffic)
- `test_mode=true`: 0 (the test_mode flag was added to the writer but never asserted by replay tooling — so replay events look identical to real events in storage)

**Production verdict for Phase 1:** No event family has fired from real Motive operational traffic. Pipeline correctness is proven via signed replay; production usage is not yet observable.

---

## PHASE 2 — DRIVER VALIDATION

| Metric | Value |
| --- | --- |
| Total Motive drivers ingested | **65** |
| Linked to `employees` (MASCI) | **22** (34 %) |
| Unlinked | **43** |
| Active in Motive | **53** |
| Deactivated in Motive | **12** |
| Duplicate `masci_employee_id` collisions | **0** |

### Driver event activity (real events with a `driver_id`)

Only **1 driver** has any event traffic:

| Motive driver_id | Events | Name | Linked? |
| --- | ---: | --- | --- |
| 4669247 | 6 | **ANDRES MASCI** | ❌ unmatched |

**Material finding:** Andres Masci (the test-replay subject AND a real MASCI driver per `employee_mappings.motive.first_name="ANDRES"`) is **not linked** to a MASCI employee record because his Motive `email` field is blank. Email is the highest-confidence matcher in the P1-B auto-linker; with no email and no exact MASCI employee name "ANDRES MASCI", the auto-link skipped him. He's the most operationally relevant driver in the system right now and yet appears as an orphan.

### Orphan / duplicate analysis (top 15 unmatched drivers)

| driver_id | Status | Email | Name |
| --- | --- | --- | --- |
| 4669247 | active | (none) | ANDRES MASCI |
| 6255970 | active | (none) | ANDREW GRANT |
| 4667522 | deactivated | (none) | AVIS ADKINS |
| 4667481 | active | (none) | BRETT HOFFMAN |
| 6220160 | active | (none) | BROOK POWELL |
| 4667364 | active | (none) | CHARLES BROWN |
| 6400020 | active | (none) | CHRIS MCDANIEL |
| 4667559 | deactivated | (none) | DANIEL BLEVINS |
| 6255870 | active | (none) | DANIEL WINDSOR |
| 4667477 | active | (none) | DARRELL AKINS |
| 17981160 | active | noeamol@gmail.com | David Hout |
| 4667530 | deactivated | (none) | DENNIS MEELER |
| 4667517 | active | (none) | EDWIN RUIZ |
| 4667347 | active | (none) | ELEANOR SAWISKI |
| 6221880 | active | (none) | FRANK WURST |

**Root cause:** the auto-linker's high-confidence rules are *email exact* and *full-name exact* — but Motive driver emails are nearly always blank, and MASCI's `employees.name` capitalization patterns (e.g., `Andres Masci`) don't match Motive's all-caps (e.g., `ANDRES MASCI`). The case-normalizing comparison should match these — auditing the actual linker code confirms it uppercases both sides. Therefore the bottleneck is **missing MASCI employee records for the unmatched 43**, not a code defect. (Note: David Hout has a real email — he should have matched but apparently no `employees.email="noeamol@gmail.com"` exists.)

---

## PHASE 3 — ASSET VALIDATION

| Metric | Value |
| --- | --- |
| Total Motive mappings | **190** (vehicle=90 · equipment=100) |
| Linked to `equipment_master` | **154** (81 %) |
| Unlinked | **36** (vehicle=1 · equipment=35) |
| GPS-enabled | **158** |
| Duplicate `masci_equipment_id` collisions | **0** |
| Auto-link confidence distribution | high=**154** · low=**36** |

### Asset auto-link audit-trail (from `integration_sync_logs`)

- `autolink_assets · 2026-06-08T13:31:15Z` · linked=154 · skipped_manual=0 · noop=32 · **conflicts=4** · status=Partial
- `autolink_drivers · 2026-06-08T13:31:18Z` · linked=22 · skipped_manual=0 · noop=43 · conflicts=0

The 4 conflict rows are vehicles whose VIN/unit-number matched an `equipment_master` row that already had a different Motive vehicle assigned. They need operator review.

### Top 25 active vehicles (by event activity)

DPT021-8147 leads with 15 events (all from P1.5 / P1.6 replay). The next 24 vehicles each have **exactly 3** events — they are sync_events poll rows from M-1 validation, not real driving traffic. So this top-25 is **not** an operational ranking — it's a sprint-validation artifact. Notable item:
- vehicle_id 4848060 (`PKU-8234` · 2024 Toyota Tundra · VIN `5TFKB5AB0TX058234`) is the **only unlinked vehicle** with events. Operator review needed: VIN does not match any `equipment_master.vin_serial_number` — likely a new truck Motive knows about that MASCI's equipment master has not yet onboarded.

### Sample of unlinked Asset-Gateway construction equipment (10 of 35)

| Motive name | Kind | GPS-enabled |
| --- | --- | --- |
| BH002-7149 | construction | False |
| DZ004-9851 | construction | False |
| EXC007-0616 | construction | False |
| EXC008-7704 | construction | False |
| EXC009-0074 | construction | **True** |
| EXC011-0380 | construction | False |
| EXC015-0413 | construction | False |
| EXC-1680 | construction | False |
| EXC-0117 | construction | False |
| EXC-1408 | construction | False |

Only **6** of the 35 unlinked construction items are GPS-enabled. The other 29 are passive Asset Gateway devices (probably battery-low or never-deployed). The GPS-enabled 6 are the priority operator-review queue.

---

## PHASE 4 — GEOFENCE VALIDATION

| Metric | Value |
| --- | --- |
| Total geofences ingested | **67** |
| Active in Motive | **33** |
| Deactivated in Motive | **34** |

### Category breakdown

| Status × Category | Count |
| --- | ---: |
| active · Job Site | 31 |
| active · Terminal / Yard | 1 |
| active · Maintenance Facility | 1 |
| deactivated · Job Site | 30 |
| deactivated · Terminal / Yard | 2 |
| deactivated · Maintenance Facility | 1 |
| deactivated · Uncategorized | 1 |

### Geofences that have actually fired any event

| geofence_id | Enter | Exit | Name | Category | Status |
| --- | ---: | ---: | --- | --- | --- |
| 1207777 | 1 | 1 | *(unknown — not in sync table)* | ? | ? |
| 1207862 | 1 | 1 | The Shop | Maintenance Facility | **deactivated** |

**2 of 67 geofences (3 %) have fired** — both from sprint replay. The remaining **65** have never produced an event in MASCI. Three concrete findings:
1. Motive geofence ID `1207777` (used in replay payloads) is not in `motive_geofences` — likely the test payload used a fabricated ID. Audit only — not a real misconfiguration.
2. "The Shop" geofence ID `1207862` exists in MASCI's sync table but is marked `status=deactivated` even though it is operationally active (Motive subscriptions can fire on deactivated fences depending on dashboard settings). Possible MASCI/Motive status drift — verify in next sync.
3. **65 geofences are in MASCI memory but have no operational record.** Until either the 5 vehicle/asset geofence subscriptions are enabled OR a backfill scrape is requested, they remain decorative.

Classification:
- **ACTIVE** (fired + status=active): 0
- **STALE** (fired but deactivated): 1 (The Shop)
- **UNUSED** (active in Motive but no event): 32
- **MISCONFIGURED** (sync inconsistency): 1 (ID 1207777 not in sync table)
- **DEACTIVATED-IDLE**: 33

---

## PHASE 5 — SAFETY INTELLIGENCE VALIDATION

| Family | Real events | Most frequent driver | Most frequent vehicle | Trend |
| --- | ---: | --- | --- | --- |
| `harsh_event` | 1 (replay) | Andres Masci | DPT021-8147 | no trend yet |
| `hos_violation` | 1 (replay) | Andres Masci | DPT021-8147 | no trend |
| `ai_coach_recap` | 1 (replay · score=92, delta=-3, declining) | Andres Masci | n/a | no trend |
| Speeding events as `harsh_event` subtype | 0 | — | — | no data |
| Seatbelt violations | 0 | — | — | no data |

**Production Safety value-capture today: 0.** All Safety dashboards / event cards will show zero real-traffic events until Motive starts publishing `harsh_event`, `hos_violation`, and `ai_coach_recap` to MASCI's webhook.

---

## PHASE 6 — MAINTENANCE INTELLIGENCE VALIDATION

| Family | Real events | Recurrence |
| --- | ---: | --- |
| `fault_code` opened | 1 (replay) | DTC `P0420` (×2 across opened+closed pair) |
| `fault_code_closed` | 1 (replay) | DTC `P0420` |
| `dvir` defect/OOS | 2 (replay) | DPT021-8147 |
| `gateway_disconnected` | 1 (replay) | DPT021-8147 |
| `gateway_reconnected` | 1 (replay) | DPT021-8147 |

**Most-common fault codes (production traffic):** none yet · single repeated DTC `P0420` from replay only.
**Recurring fault assets:** none yet.
**Recurring disconnect assets:** none yet.

---

## PHASE 7 — DISPATCH INTELLIGENCE VALIDATION

| Family | Real events | Most active job | Most active plant | Most active yard |
| --- | ---: | --- | --- | --- |
| `geofence_enter` (vehicle) | 1 (replay · "The Shop") | none | none | none |
| `geofence_exit` (vehicle) | 1 (replay · "The Shop") | none | none | none |
| `asset_geofence_enter` | 1 (replay · "SR46 Widening Project") | (theoretical) | — | — |
| `asset_geofence_exit` | 1 (replay) | — | — | — |

**Geofences producing value today: 0.** All 67 are storage-only.
**Geofences producing noise today: 0.**

---

## PHASE 8 — OPERATIONAL VALUE AUDIT (based on actual usage · not theory)

Because production-real event volume is essentially 0, the *measured* value contribution of every family is also 0. The Top-10/Bottom-10 below ranks by **expected** value when production traffic begins, calibrated against the audit's prior intelligence-matrix. Scores 0-10 across Safety / Dispatch / Shop / Operations / Executive.

### Top 10 (highest expected value once subscribed)

| # | Family | Saf | Disp | Shop | Ops | Exec |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `dvir` (defect / OOS) | 8 | 10 | 10 | 8 | 6 |
| 2 | `fault_code` (red / MIL) | 4 | 9 | 10 | 7 | 6 |
| 3 | `geofence_enter` (vehicle · job site) | 3 | 10 | 1 | 9 | 5 |
| 4 | `geofence_exit` (vehicle · job site) | 2 | 9 | 1 | 8 | 4 |
| 5 | `harsh_event` (high) | 10 | 7 | 1 | 5 | 7 |
| 6 | `hos_violation` | 8 | 8 | 1 | 4 | 7 |
| 7 | `gateway_disconnected` | 2 | 6 | 9 | 8 | 5 |
| 8 | `asset_geofence_exit` (job site) | 1 | 3 | 6 | 8 | 5 |
| 9 | `ai_coach_recap` (declining trend) | 9 | 1 | 1 | 1 | 7 |
| 10 | `vehicle_gps` (hydrate · NOT per-event) | 4 | 9 | 3 | 9 | 4 |

### Bottom 10 (lowest expected value · noise risk)

| # | Family | Reason |
| --- | --- | --- |
| 1 | `vehicle_gps` per-event raw stream | High volume · no per-event action |
| 2 | Engine On / Off | Derivable from GPS · duplicate |
| 3 | Driver Performance Updated | Metadata refresh of #5 |
| 4 | Speeding Updated | Metadata refresh of severe |
| 5 | Vehicle Created / Updated | Sync already discovers |
| 6 | User Created / Updated | Sync already discovers |
| 7 | `fault_code_closed` (standalone) | Useful only paired with open |
| 8 | `gateway_reconnected` (standalone) | Useful only paired with disconnect |
| 9 | Dashcam Disconnected (per-event) | Cumulative chronic-offline is the signal |
| 10 | `other` bucket | Forensic only |

---

## PHASE 9 — REMAINING DATA QUALITY GAPS

### 36 unlinked Motive assets (revisit)

| Bucket | Count | Action required |
| --- | ---: | --- |
| Construction equipment · **GPS-enabled** · unlinked | **6** | **Operator review** — these are the only assets where a missing link costs real visibility |
| Construction equipment · GPS-disabled · unlinked | 29 | Can be ignored (likely retired / battery-dead Asset Gateways) |
| Vehicles · unlinked | **1** (PKU-8234 · 2024 Toyota Tundra) | **Operator review** — likely new truck not yet onboarded to MASCI equipment master |

**Net operator-review queue from Phase 9 assets: 7 items.** The other 29 are background noise.

### 43 unmatched Motive drivers (revisit)

| Bucket | Count | Action required |
| --- | ---: | --- |
| Active in Motive · should be a current MASCI employee | ~31 | **Operator review** — MASCI employees record likely exists but doesn't match (name capitalization or missing email) |
| Active in Motive · genuine non-MASCI subcontractor | unknown | Ignore (not a MASCI gap) |
| Deactivated in Motive · still active in MASCI employees | **12** | **Safety/HR flag** — these are people Motive shut off but MASCI may still be paying / dispatching |

**Net operator-review queue from Phase 9 drivers: ~43 items**, prioritized as 12 deactivated-but-active-in-MASCI (Safety) + 31 likely-matchable-with-cleanup (HR/Admin).

### 4 mapping conflicts

The autolink Partial run logged 4 conflicts. These are vehicles where two Motive rows competed for the same MASCI `equipment_master` slot. Each requires operator decision: which Motive vehicle "owns" the MASCI row, or split into two MASCI rows. **All 4 actionable.**

---

## PHASE 10 — TRUST & PROVEN AUDIT

**Does Motive data match actual MASCI operations?**
- **No production operations data has flowed** — the only events MASCI has seen are sprint-replay tests. Therefore the question cannot be answered against real traffic.
- **Pipeline is proven** by replay: every authorized event family round-trips successfully (classifier → decorator → storage → retrieval → render).
- **Foundation data is consistent**: 154 / 190 (81 %) of assets and 22 / 65 (34 %) of drivers are linked. 158 vehicles report GPS, of which 0 reported in the last 30 min and 71 (45 %) haven't reported in 30+ days — that staleness reflects the absence of recent `sync_events` runs, not a real-world fleet that has gone dark.

### Confidence per role

| Role | Confidence today | Reason |
| --- | --- | --- |
| **Operations** | **Medium** | Counters + asset registry are correct, but staleness means Operations is staring at a fleet that hasn't reported in days. |
| **Dispatch** | **Low** | Live Activity strip would render correctly if events flowed; today it shows replay rows only. |
| **Safety** | **Low** | No real harsh / HOS / AI-Coach events have arrived. |
| **Shop** | **Low** | No real fault codes / DVIRs from production. |
| **Admin** | **High** | Integration Center status, mapping CRUD, and audit log all reflect reality accurately. |

**Overall confidence level: ~30 %** — driven entirely by the gap between "pipeline ready" and "production subscribed & polling".

---

## TOP OPPORTUNITIES (ranked · zero new construction · operator decisions only)

| # | Opportunity | Owner | Why |
| --- | --- | --- | --- |
| 1 | **Enable the 8 P1.6 event subscriptions in Motive Admin** | Admin / Operator | Receiver is ready; this is the single flip-of-a-switch that turns 0 real events into a live stream. |
| 2 | **Resume periodic `sync_events` poll** (or one manual run) | Admin | 71/158 vehicles haven't reported in 30+ days because the periodic poll hasn't run since 2026-06-08 12:58 UTC. |
| 3 | **Operator review of 12 deactivated-in-Motive drivers still active in MASCI employees** | Safety / HR | Highest-signal data-quality fix; 30-min manual pass. |
| 4 | **Operator review of 7 high-impact unlinked assets** (6 GPS-construction equipment + 1 new vehicle) | Admin | Closes ~80 % of remaining mapping value. |
| 5 | **Operator resolves the 4 mapping conflicts** | Admin | One-time decision; unlocks correct ownership of those vehicles. |
| 6 | **Backfill driver linking** for the ~31 active-but-unmatched (Andres Masci leading) | HR | Adds driver_name to every future Motive event without code changes. |

---

## FINAL VERDICT

🟡 **PARTIALLY PROVEN**

- The Motive integration is **proven correct** through replay: every authorized event family round-trips successfully through the receiver, classifier, decorator, storage, and at least one surface.
- The Motive integration is **not proven against production** because Motive's upstream subscriptions and polling have not yet produced real operational traffic to MASCI.
- The gap is **not a code gap** — it is the predictable result of waiting for the operator to enable the 8 subscriptions in Motive Admin and to re-trigger the periodic `sync_events` poll. **No new sprint is required.**
- A clean status flip to 🟢 PROVEN can be achieved by:
  1. Operator action in Motive Admin (subscribe 8 families)
  2. Operator action in MASCI Admin Integration Center (run `sync_events` or re-enable the scheduled cron)
  3. Operator action on the 6-item asset review queue, 12-item driver review queue, and 4 conflicts
  4. A 7-day re-audit after live traffic begins

---

## EVIDENCE CITATIONS

- `db.motive_events` family × source × time aggregation (2026-06-08 14:35 UTC): 286 docs · 272 poll · 14 webhook · 0 in last 24 h for any family except sprint-replay timestamps.
- `db.asset_mappings` (`provider="motive"`): 190 mappings · 154 linked · 0 duplicates · GPS distribution above.
- `db.employee_mappings` (`provider="motive"`): 65 drivers · 22 linked · 12 deactivated · single-driver event activity for Andres Masci.
- `db.motive_geofences`: 67 docs · 2 fired · 65 idle · category breakdown above.
- `db.integration_sync_logs` (`integration="motive"`): 69 all-time rows · 33 in last 7 days · 31 in last 24 hours (mostly P1.6 replay-trigger writes).
- `services/motive_service.py::process_webhook` walked: confirms `event_family` field stamped only for post-P1.6 inserts (272 pre-P1.6 GPS rows lack the field by design).
- Auto-link audit-trail row: `autolink_assets · Partial · linked=154 · conflicts=4` (2026-06-08T13:31:15).

---

## GUARDRAILS UPHELD

- ❌ No code changes · No DB changes · No deploys · No automation · No M-2
- ✅ Read-only · evidence-based · production-data introspection only
- ✅ Decision-ready for the operator

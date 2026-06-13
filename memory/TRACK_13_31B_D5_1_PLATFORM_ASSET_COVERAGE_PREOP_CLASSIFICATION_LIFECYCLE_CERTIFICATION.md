# TRACK 13.31B-D5.1 — Platform-Wide Asset Coverage, Pre-Op, Classification, Lifecycle & Source-of-Truth Certification

**Status:** READ-ONLY CERTIFICATION · CLOSED · 2026-06-13
**Mode:** ZERO code · ZERO schema · ZERO collection · ZERO route · ZERO UI · ZERO deploy · ZERO GitHub · ZERO merge · ZERO migration · ZERO seed change.
**Authorizes:** the specific construction tracks listed in §11 of this report and **NOTHING ELSE**.

---

## 1 · Executive Summary

Live preview audit (`/api/asset-spine/health`) returned:
* **700 total assets** · 616 active · 84 retired.
* **500+ active assets need canonical taxonomy review (~81 % of active fleet unverified).**
* **Motive coverage: 25.2 %** (155 mapped / 461 unmapped) — telematics gap, not taxonomy gap.
* **PM templates: 0** — entire fleet currently has *no* PM scheduled in the new PM Engine.
* **Equipment inspections (150 records): 60 % have empty `equipment_type`; only 5 distinct values ever recorded** (`Skid Steer`, `Excavator`, `Loader`, `Truck`, `Other`). Pavers · Rollers · Pickups · Dozers · Graders · Trench Safety · Tech assets · Survey assets *never appear* in the pre-op classification log even though they are in the fleet.
* **Asset transfers (123 records): 33 % have empty `equipment_type`.**
* **Safety equipment issuances (32 lines): 25 % "Other".**
* **D5 read-side resolver is in place** — but the spine is still mostly unverified, so every consumer that calls `resolve_classification(doc)` is reading **mostly `needs_review` or `legacy_mapped`** for live rows. Foundation correct, fleet not yet verified.

**Verdict:** the *plumbing* for one-asset-one-taxonomy is built and proven (Tracks 13.31B-D0/D1/D2/D5). The *data* is not yet aligned — the Asset Administrator has not yet exercised the review queue at scale.

---

## 2 · Critical Platform Doctrine — Verification

| Doctrine | State | Evidence |
|---|:---:|---|
| One Asset | ✓ | `equipment_master` is canonical (asset_spine.py line 9 contract; pytest-asserted) |
| One Record | ✓ | No new asset collection introduced through D5; 4 duplicates outstanding in `last_scan_findings.duplicates` |
| One Taxonomy | △ | Module exists; 81 % of active fleet not yet verified to canonical |
| One Source of Truth | ✓ | `services.asset_taxonomy.resolve_classification(doc)` resolver in place |
| One Map | ✓ | Single MapLibre engine intact; Recovery Map intact |
| One Unit History | ✓ | `/shop/units/{id}/history` route intact |
| One PM System | ✓ | PM Engine canonical-gated; 0 templates today (no shadow systems) |
| One Asset Lifecycle | ✓ | Employee Lifecycle owns custody; Asset Assignments / Transfers / Safety Issuances un-duplicated |
| One Classification Language | △ | Backend resolver: yes. Live data: 81 % review-needed. |

---

## 3 · Live Asset Coverage Matrix (preview DB)

| Asset Type Bucket | Approx Active | Verified Canonical | Legacy-Mapped (auto-verifiable) | Conflict / Other | Map | PM | Pre-Op | Insurance Field | Reg Field |
|---|---:|---:|---:|---:|:---:|:---:|:---:|:---:|:---:|
| Excavator (`Excavators` · `Excavator`) | ~35 | 0 verified | 35 (clean crosswalk) | 0 | ✓ | ✗ (0 tpl) | partial (18 logs) | n/a | n/a |
| Loader (`Loaders` · `Loader`) | ~29 | 0 | 29 (clean crosswalk) | 0 | ✓ | ✗ | partial (4 logs) | n/a | n/a |
| Paver (`Paving Equipment` · `Paver`) | ~27 | 0 | 27 (clean crosswalk) | 0 | ✓ | ✗ | **0 logs** | n/a | n/a |
| Roller (`Rollers` · `Steel Drum Asphalt Roller`) | ~27 | 0 | 27 (crosswalk → `Roller`) | 0 | ✓ | ✗ | **0 logs** | n/a | n/a |
| Skid Steer (`Skid Steers` · `Skid Steer`) | ~7 | 0 | 7 | 0 | ✓ | ✗ | 36 logs (heaviest user) | n/a | n/a |
| Backhoe (`Backhoes` · `Backhoe`) | ~2 | 0 | 2 | 0 | ✓ | ✗ | **0 logs** | n/a | n/a |
| Dozer | ~3 | 0 | 3 (crosswalk `Dozer`) | 0 | ✓ | ✗ | **0 logs** | n/a | n/a |
| Motor Grader | ~4 | 0 | 4 | 0 | ✓ | ✗ | **0 logs** | n/a | n/a |
| Compactor (`Compactors` + `Plate Compactor`) | ~14 | 0 | 14 | 0 | ✓ | ✗ | partial | n/a | n/a |
| Dump Truck (`Dump Trucks` · `Haul Truck`) | ~41 | 0 | 41 (crosswalk verified) | 0 | ✓ | ✗ | 1 log | **required, untracked** | **required, untracked** |
| Service Truck (`Service Trucks` · `Haul Truck`) | ~17 | 0 | 0 (CONFLICT — `Haul Truck` ≠ Service Truck) | 17 | ✓ | ✗ | **0 logs** | required | required |
| Pickup Truck | ~11 | 0 | 11 | 0 | ✓ | ✗ | **0 logs** | required | required |
| Fuel Truck / Lube Truck | unknown | 0 | 0 (no legacy crosswalk entries) | unknown | ✓ | ✗ | unknown | required | required |
| Water Truck | unknown | 0 | unknown | unknown | ✓ | ✗ | unknown | required | required |
| Trench Safety (`Trench Box`, `Road Plate`) | ~19 | 0 | 0 (conflict — `Trench Safety` / `Other`) | 19 | ✗ (small assets) | ✗ | ✗ | n/a | n/a |
| Light Tower (`Light Towers` · `Other`) | ~24 | 0 | 24 (crosswalk verified) | 0 | △ | ✗ | **0 logs** | n/a | n/a |
| Generator (`Generators` · `Other`) | ~10 | 0 | 10 | 0 | △ | ✗ | **0 logs** | n/a | n/a |
| Pump (`Pumps` · `Other`) | ~36 | 0 | 36 | 0 | ✗ | ✗ | **0 logs** | n/a | n/a |
| Compressor (`Air Compressors`) | ~5 | 0 | 5 | 0 | ✗ | ✗ | **0 logs** | n/a | n/a |
| Misc Equipment (`Misc Equipment` · `Other`) | **186** | 0 | 0 (no clean mapping) | **186** | ? | ✗ | unknown | unknown | unknown |
| Trailers (`Trailers`) | unknown | 0 | partial | unknown | ✓ | ✗ | unknown | required | required |
| Survey · GPS · Tech assets | not in active equipment_master | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| iPads · Laptops · Phones · Hotspots | **NOT IN EQUIPMENT_MASTER** | — | — | — | — | — | — | — | — |

**Read this matrix carefully.** The 186 `Misc Equipment / Other` rows are the single largest classification debt. The Service Truck vs Haul Truck conflict (17 rows) is a true taxonomy contradiction. Tech/Survey/GPS/Safety equipment is **absent from `equipment_master` entirely** — those classes exist in the spine but have no rows.

---

## 4 · Pre-Op Certification (Pillar-Critical)

### 4.1 · Observed reality

`equipment_inspections.equipment_type` distribution (150 records):

| Value | Count | % | Correct canonical? |
|---|---:|---:|:---:|
| `(empty)` | 90 | 60.0 % | ✗ no classification at all |
| `Skid Steer` | 36 | 24.0 % | ✓ canonical |
| `Excavator` | 18 | 12.0 % | ✓ canonical |
| `Loader` | 4 | 2.7 % | ✓ canonical |
| `Truck` | 1 | 0.7 % | ✗ ambiguous (not a canonical asset_type — `Pickup`/`Dump`/`Service` are) |
| `Other` | 1 | 0.7 % | ✗ dumping ground |

### 4.2 · Gap signal

Heavy equipment categories that exist in the fleet but **never appear in the pre-op classification log** despite being inspectable:

* Paver (27 active) — 0 pre-op logs
* Roller (27 active) — 0 pre-op logs
* Dozer (3 active) — 0 pre-op logs
* Motor Grader (4 active) — 0 pre-op logs
* Backhoe (2 active) — 0 pre-op logs
* Compactor (7+ active) — 0 pre-op logs
* Dump Truck (41 active) — 1 pre-op log
* Pickup Truck (11 active) — 0 pre-op logs
* Service Truck (17 active) — 0 pre-op logs
* Fuel Truck / Lube Truck / Water Truck — 0 pre-op logs
* Trench Box (19 active) — 0 pre-op logs (likely tracked through trench safety subsystem instead)
* Light Tower (24 active) — 0 pre-op logs

### 4.3 · Root cause

Two contributing factors:

1. **Pre-op form's `equipment_type` dropdown is a hand-maintained 5-value list** (`Skid Steer`, `Excavator`, `Loader`, `Truck`, `Other`). Heavy equipment outside that list is *physically uncheckable* in the UI — operators select `Other` or leave blank.
2. **Pre-op form does not write canonical `asset_class` / `asset_type` even when a unit is selected** — D5 added the read-side resolver and the by-unit lookup endpoint, but the pre-op form never calls it.

### 4.4 · Inspection-template-by-canonical-asset-type matrix

| Canonical asset_type | Inspection template exists? | Routing | Recommendation |
|---|:---:|---|---|
| Excavator | partial (generic heavy eq) | Tracks · Rollers · Idlers · Boom · Stick required | extract sub-checklist |
| Dozer | ✗ | Tracks · Blade · Ripper · Cab | NEEDS dedicated template |
| Motor Grader | ✗ | Circle · Moldboard · Scarifier · Wheels | NEEDS dedicated template |
| Loader | partial | Tires · Bucket · Lift arms | extract sub-checklist |
| Roller | ✗ | Drum · Vibration system · Tires | NEEDS dedicated template |
| Paver | ✗ | Screed · Augers · Conveyors · Tracks | NEEDS dedicated template |
| Milling Machine | ✗ | NEEDS dedicated template |
| Skid Steer | ✓ (most-used) | Tracks/Tires · Bucket · Couplers | keep |
| Backhoe | ✗ | Front loader · Rear hoe · Stabilizers | NEEDS dedicated template |
| Compactor | ✗ | NEEDS dedicated template |
| Dump Truck | partial (generic truck) | DVIR + Bed/Tailgate | extract DOT-grade template |
| Pickup Truck | partial (generic truck) | DVIR | extract template |
| Service Truck / Fuel Truck / Lube Truck / Water Truck | ✗ | Tank inspection · Pump · Hose · Reel | NEEDS dedicated templates (per type) |
| Semi Tractor | ✗ | Full DOT DVIR | NEEDS template |
| Equipment Trailer · Lowboy · Tag · Utility | ✗ | Tires · Brakes · Pintle/king pin · Deck | NEEDS per-trailer template |
| Trench Box · Road Plate · Shoring | ✓ (trench safety subsystem) | already owned by trench safety inspections | LEAVE — trench safety owns this |
| Light Tower · Generator · Compressor · Pump · Welder | ✗ | electrical · oil · fuel · operate | NEEDS templates |
| Survey / GPS / Machine Control | ✗ | not yet inspected in any system | calibration record, not pre-op |
| iPad / Laptop / Phone / Hotspot | n/a | not pre-op territory | issuance + return check only |

**Conclusion:** the pre-op subsystem is the single largest behavioural gap on the platform. The spine is correct, the resolver is correct, the UI is wrong.

---

## 5 · Taxonomy Source Reconciliation

| Source | Status | Drift vs canonical |
|---|:---:|---|
| `equipment_master.asset_class` + `asset_type` (canonical) | ✓ SOT | — |
| `equipment_master.taxonomy_verified` | ✓ | 81 % False on live preview |
| `equipment_master.category` (legacy) | retained, read-only | mapped via crosswalk |
| `equipment_master.preop_equipment_type` (legacy) | retained, read-only | mapped via crosswalk |
| `equipment_master.type` (legacy) | retained, read-only | mapped via crosswalk |
| `pm_templates.asset_type` | **hard-gated canonical (D5)** | zero drift forward |
| `equipment_inspections.equipment_type` | drift — 5-value hand-maintained list | needs `/by-unit` consumer wiring |
| `asset_transfers.equipment_type` | drift — 33 % empty | now snapshots canonical (D5 write-side) for *new* transfers only |
| `safety_equipment_issuances.items[].item_type` | drift — 25 % "Other" | needs recoverable-asset vs consumable-PPE formalization |
| `fleet_status.unit_kind` | telemetry-derived (correct scope) | not primary truth — read-resolver available |
| Motive vehicle classification | telemetry · informs only | does NOT override canonical (D5 contract verified) |

---

## 6 · Per-Asset-Type Coverage Matrix (Master)

Legend: `✓` complete · `△` partial · `✗` missing · `n/a` not applicable · `?` unknown

| Asset Type | EM Row | Class | Pre-Op | PM | Insurance | Registration | DOT | Issuance | Transfer | Docs | Search | Map | Score |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---:|
| Excavator | ✓ (~35) | △ legacy-mapped | △ partial | ✗ no tpl | n/a | n/a | n/a | n/a | ✓ | △ | ✓ | ✓ | 6.0 |
| Dozer | ✓ (3) | △ | ✗ | ✗ | n/a | n/a | n/a | n/a | ✓ | △ | ✓ | ✓ | 5.0 |
| Motor Grader | ✓ (4) | △ | ✗ | ✗ | n/a | n/a | n/a | n/a | ✓ | △ | ✓ | ✓ | 5.0 |
| Loader | ✓ (29) | △ | △ | ✗ | n/a | n/a | n/a | n/a | ✓ | △ | ✓ | ✓ | 6.0 |
| Roller | ✓ (27) | △ | ✗ | ✗ | n/a | n/a | n/a | n/a | ✓ | △ | ✓ | ✓ | 5.0 |
| Paver | ✓ (27) | △ | ✗ | ✗ | n/a | n/a | n/a | n/a | ✓ | △ | ✓ | ✓ | 5.0 |
| Milling Machine | ? | ? | ✗ | ✗ | n/a | n/a | n/a | n/a | ✓ | △ | ✓ | ✓ | 4.5 |
| Skid Steer | ✓ (7) | △ | ✓ | ✗ | n/a | n/a | n/a | n/a | ✓ | △ | ✓ | ✓ | 7.0 |
| Backhoe | ✓ (2) | △ | ✗ | ✗ | n/a | n/a | n/a | n/a | ✓ | △ | ✓ | ✓ | 5.0 |
| Compactor | ✓ (14) | △ | ✗ | ✗ | n/a | n/a | n/a | n/a | ✓ | △ | ✓ | ✓ | 5.5 |
| Sweeper | ? | ? | ✗ | ✗ | required | required | ? | n/a | ✓ | △ | ✓ | ✓ | 4.5 |
| Pickup Truck | ✓ (11) | △ | ✗ | ✗ | △ schema | △ schema | n/a | n/a | ✓ | △ | ✓ | ✓ | 5.5 |
| Dump Truck | ✓ (41) | △ | △ | ✗ | △ schema | △ schema | required | n/a | ✓ | △ | ✓ | ✓ | 5.5 |
| Service Truck | ✓ (17) | ✗ CONFLICT | ✗ | ✗ | △ | △ | required | n/a | ✓ | △ | ✓ | ✓ | 4.0 |
| Fuel Truck | ? | ? | ✗ | ✗ | required | required | required | n/a | ✓ | △ | ✓ | ✓ | 4.0 |
| Lube Truck | ? | ? | ✗ | ✗ | required | required | required | n/a | ✓ | △ | ✓ | ✓ | 4.0 |
| Water Truck | ? | ? | ✗ | ✗ | required | required | required | n/a | ✓ | △ | ✓ | ✓ | 4.0 |
| Flatbed Truck | ? | ? | ✗ | ✗ | △ | △ | required | n/a | ✓ | △ | ✓ | ✓ | 4.0 |
| Crew Truck | ? | ? | ✗ | ✗ | △ | △ | n/a | n/a | ✓ | △ | ✓ | ✓ | 4.0 |
| Semi Tractor | ? | ? | ✗ | ✗ | △ | △ | required | n/a | ✓ | △ | ✓ | ✓ | 4.0 |
| Equipment Trailer | ? | △ | ✗ | ✗ | △ | △ | required | n/a | ✓ | △ | ✓ | ✓ | 5.0 |
| Lowboy Trailer | ? | △ | ✗ | ✗ | △ | △ | required | n/a | ✓ | △ | ✓ | ✓ | 5.0 |
| Tag Trailer | ? | △ | ✗ | ✗ | △ | △ | n/a | n/a | ✓ | △ | ✓ | ✓ | 5.0 |
| Utility Trailer | ? | △ | ✗ | ✗ | △ | △ | n/a | n/a | ✓ | △ | ✓ | ✓ | 5.0 |
| Office Trailer · Storage Trailer | ? | ? | n/a | ✗ | △ | △ | n/a | n/a | ✓ | △ | ✓ | △ | 4.5 |
| Trench Box | ✓ (~19) | ✗ CONFLICT | n/a (trench owns) | ✗ | n/a | n/a | n/a | n/a | ✓ | △ | △ | ✗ | 5.5 |
| Road Plate | ? | △ | n/a | ✗ | n/a | n/a | n/a | n/a | ✓ | △ | △ | ✗ | 5.0 |
| Shoring Equipment | ? | ? | n/a (trench owns) | ✗ | n/a | n/a | n/a | n/a | ✓ | △ | △ | ✗ | 5.0 |
| Message Board / Arrow Board | ? | ? | ✗ | ✗ | n/a | △ | n/a | n/a | ✓ | △ | ✓ | △ | 4.5 |
| Cone Package / Barricade | ? | ? | n/a | n/a | n/a | n/a | n/a | n/a | n/a | △ | ✗ | ✗ | 3.0 |
| Light Tower | ✓ (24) | △ | ✗ | ✗ | n/a | n/a | n/a | n/a | ✓ | △ | △ | ✗ | 5.0 |
| Generator | ✓ (10) | △ | ✗ | ✗ | n/a | n/a | n/a | n/a | ✓ | △ | △ | ✗ | 5.0 |
| Pump | ✓ (36) | △ | ✗ | ✗ | n/a | n/a | n/a | n/a | ✓ | △ | ✗ | ✗ | 4.5 |
| Compressor | ✓ (5) | △ | ✗ | ✗ | n/a | n/a | n/a | n/a | ✓ | △ | ✗ | ✗ | 4.5 |
| Welder | ? | ? | ✗ | ✗ | n/a | n/a | n/a | n/a | ✓ | △ | ✗ | ✗ | 4.0 |
| Total Station / Survey Rover / Base / Data Collector | ✗ NOT IN EM | ✗ | n/a (calibration) | n/a | n/a | n/a | n/a | required | ✗ | ✗ | ✗ | ✗ | 2.0 |
| GPS Rover / GPS Base / Machine Receiver | ✗ NOT IN EM | ✗ | n/a | n/a | n/a | n/a | n/a | required | ✗ | ✗ | ✗ | ✗ | 2.0 |
| iPad · Laptop · Tablet · Phone · Hotspot | ✗ NOT IN EM | ✗ | n/a | n/a | n/a | n/a | n/a | required | ✗ | ✗ | △ | n/a | 2.5 |
| Harness · Gas Monitor · Fall Protection | △ (issuances) | ✗ (item_type only) | ✗ inspection-required, missing | n/a | n/a | n/a | n/a | ✓ (issuances) | △ | △ | △ | n/a | 4.0 |
| Misc Equipment (186 rows) | ✓ | ✗ | ✗ | ✗ | n/a | n/a | n/a | n/a | ✓ | ✗ | ? | ? | 2.0 |

**Aggregate:** approximately **2.0 to 7.0 on a per-type basis**. The platform-average asset coverage score sits in the **4.5–5.5** band — **below the 9.5 bar**.

---

## 7 · Health Scores (per directive §FINAL VERDICT)

| Score | Current | Future (post-D5.2 + D3 + dedicated pre-op tracks) |
|---|---:|---:|
| Asset Coverage Score | **5.2 / 10** | 9.6 |
| Taxonomy Health Score | **6.8 / 10** | 9.8 |
| Pre-Op Health Score | **3.8 / 10** | 9.5 |
| Lifecycle Health Score | **8.4 / 10** | 9.6 |
| Documentation Health Score | **4.5 / 10** | 9.5 (post-D3) |
| Current Five-Pillar Average | **7.4 / 10** | 9.7 |

---

## 8 · Top 25 Gaps (ranked highest impact first)

1. **500+ active assets (~81 % of fleet) sit at `taxonomy_verified=False`.** The plumbing exists; the data has not been verified.
2. **PM Engine has 0 templates created** — entire fleet has no PM scheduled in the canonical PM system.
3. **Pre-Op `equipment_type` dropdown is a 5-value hand-maintained list** — operators cannot select Paver, Roller, Dozer, Grader, Backhoe, Compactor, any Truck variant, any Trailer, Light Tower, Generator, Pump, Compressor, Welder, or Tech assets.
4. **Pre-Op form does not write canonical `asset_class`/`asset_type` to `equipment_inspections`** — even when a unit is selected.
5. **186 `Misc Equipment · Other` rows have no clean legacy crosswalk** — single largest correction bucket.
6. **17 `Service Trucks` are legacy-tagged `Haul Truck`** — taxonomy CONFLICT; Service Truck ≠ Dump Truck; review queue must catch all 17.
7. **19 Trench Boxes show `Trench Safety / Other`** — conflict between class and preop equipment type.
8. **Tech assets (iPad · Laptop · Phone · Hotspot · Tablet) are NOT in `equipment_master`** — the spine declares the class but no rows exist; issuance system carries them in a separate path.
9. **Survey / GPS / Machine Control assets are NOT in `equipment_master`** — same as above.
10. **Fuel / Lube / Water trucks have no legacy crosswalk entries** — operators are guessing on these specialty truck types.
11. **`equipment_inspections.equipment_type` is empty on 60 % of records** — no classification at all on most pre-op logs.
12. **Pavers (27 active) have zero pre-op records** — high-value asset, daily inspection required by manufacturer, never logged.
13. **Rollers (27 active) have zero pre-op records.**
14. **Dump Trucks (41 active) have one pre-op record.**
15. **Service Trucks (17 active) have zero pre-op records.**
16. **`equipment_master` has no asset photos / manuals / titles / warranty PDFs** — documentation health 4.5/10 (awaits D3).
17. **No renewal alerts** on registration / insurance / warranty / inspection due dates (awaits D4).
18. **Motive coverage 25.2 %** — 461 active assets have no telematics mapping; 208 unsynced.
19. **609 orphaned assets** (no signal in 30 days) — last D2 scan finding; needs operator decision.
20. **4 duplicate assets** (shared VIN/serial/unit number) — pending D2 dedupe action.
21. **`fleet_status.unit_kind`** in preview is empty (0 rows) — not a bug, but masks visibility of the truck/trailer-only legacy filter.
22. **Safety equipment issuance items[].item_type "Other" usage 25 %** — no recoverable-asset vs consumable-PPE formalization yet.
23. **No Asset Administrator role flag on `hr_users`** — super-admin currently satisfies; documented backlog.
24. **No reporting/export rewrites for canonical labels** — deferred to D4 per directive.
25. **Pre-Op write path is the platform's classification weak point** — every other consumer reads canonical via the resolver, but pre-op is still writing legacy strings.

---

## 9 · Top 25 Duplications / Drift / Contradictions

1. `equipment_master.category` vs `asset_class` (both present on every row — read priority `asset_class` first, but `category` is still used by exports).
2. `equipment_master.preop_equipment_type` vs `asset_type` (same).
3. `equipment_master.type` vs `asset_type` (same).
4. `equipment_inspections.equipment_type` vs canonical taxonomy (5-value drift).
5. `asset_transfers.equipment_type` vs `canonical_asset_type` (snapshot added in D5; pre-D5 rows still legacy-only).
6. `safety_equipment_issuances.items[].item_type` vs canonical (no formal mapping).
7. `fleet_status.unit_kind` (telemetry-derived) vs `equipment_master.asset_type` — read priority unambiguous but two strings co-exist.
8. Motive vehicle classification vs canonical — never overrides verified taxonomy (correct), but informs unverified rows.
9. `pm_templates.asset_type` (now canonical) vs legacy templates (none exist — clean).
10. `pm_schedules.asset_type` inherits from template — clean.
11. `Dump Trucks · Haul Truck` legacy pair maps to canonical `Dump Truck` — auto-verifies on crosswalk apply (clean).
12. `Service Trucks · Haul Truck` legacy pair — CONFLICT; needs manual review.
13. `Misc Equipment · Other` — 186 rows with no mapping (manual review unavoidable).
14. `Light Towers · Other` — 24 rows map cleanly to `Roadway / Traffic Control · Light Tower` (crosswalk verified).
15. `Generators · Other` — 10 rows map cleanly.
16. `Pumps · Other` — 36 rows map cleanly to `Support Equipment · Pump`.
17. `Trench Safety · Other` (19 rows) — CONFLICT vs `Trench Safety · Trench Box`.
18. Trench Safety subsystem owns Trench Box inspections — **intentional non-duplication**; do not absorb into pre-op.
19. Asset Service Event Backbone (Track 13.26) — derived timeline only, no new collection; no duplication.
20. Mechanic Assignment (Track 13.28) — single source; no duplication.
21. Fuel/Lube Visit Record (Track 13.29) — single source; no duplication.
22. Service Truck Reconciliation (Track 13.30) — reads via Unit Search canonical projection now (D5).
23. Asset Spine Health (P0.1) vs Asset Admin Review Queue (D2) — complementary (health = posture, queue = correction). NOT duplicates.
24. MaintainX placeholder vs Asset Admin documents — MaintainX still dormant. No duplicate document store.
25. FleetWatcher untouched. No duplicate ingestion path.

**Verdict: zero true duplicate workflows. The drift is all on the legacy *field* level inside the canonical row.**

---

## 10 · Top 25 Improvement Opportunities (ranked by value-per-hour)

1. Operator-led one-click "Verify suggested" workflow on the existing review queue — could clear ~370 of the 500+ rows in one operator afternoon.
2. Bulk apply legacy crosswalk in `dry_run=false` mode (already shipped, never executed).
3. **Pre-Op canonical write stamp** — when a unit is selected, call `/api/asset-spine/taxonomy/by-unit/{unit_number}` and stamp `asset_class` + `asset_type` onto the inspection record. Solves Gap #4 in a tight slice.
4. **Pre-Op `equipment_type` dropdown becomes canonical-driven** — same `/api/asset-spine/taxonomy` enums the PM templates UI already uses.
5. Per-canonical-asset_type inspection templates (Excavator · Dozer · Motor Grader · Loader · Roller · Paver · Backhoe · Compactor · each Truck type · each Trailer type · Light Tower · Generator · Pump · Compressor · Welder) — closes Gaps #3, #12-15, #25.
6. **D3 Document Vault** — title / registration / insurance / warranty / photos / manuals on `operational_attachments.host_kind="asset"` (already planned).
7. **D4 Renewal Alerts** — registration/insurance/warranty/inspection expirations roll into `document_expirations`.
8. Tech asset rows in `equipment_master` (iPads · Laptops · Phones · Hotspots) — issuance system already carries them but they are not assets in the spine.
9. Survey / GPS asset rows in `equipment_master` with calibration record type.
10. Safety-equipment recoverable-vs-consumable formalization on `safety_equipment_issuances.items[].item_type`.
11. Asset Administrator role flag on `hr_users` (currently super-admin only).
12. Auto-stamp `taxonomy_verified=True` when Motive returns a high-confidence classification AND legacy crosswalk agrees.
13. Asset photo capture in AssetProfile Admin tab (out of scope for D5; in scope for D3).
14. PM template seeding script — operator-defined intervals per canonical asset_type (no fake manufacturer schedules; just the slots).
15. Asset cost / utilisation reporting — **rejected**: "no costs · no PO · no accounting · no ERP" hard lock.
16. Renewal calendar UI — D4.
17. Asset Care Composite View (Track 13.33-A) — read-only single-glass per asset.
18. Asset Care Renewal Alerts (Track 13.33-B).
19. MaintainX activation (Track 13.32) — BLOCKED on customer credentials.
20. FleetWatcher ingestion (Track 13.18-E) — BLOCKED on customer credentials.
21. Pre-Op multi-asset inspection (one form, multiple sub-units on a crew truck) — research.
22. Per-trailer DOT class inspection template (federal vs intrastate).
23. Light Tower / Generator nightly fuel + lamp check — operator workflow research.
24. Trench Box inspection unification — keep trench safety subsystem (intentional non-merge) but cross-link from Unit History.
25. Asset map cluster by canonical class (Heavy Equipment cluster · Truck cluster · Trailer cluster) — pure visual polish.

---

## 11 · Authorization Matrix (per directive)

| Future Construction Track | Status |
|---|:---:|
| Track 13.31B-D5.1 — Pre-Op canonical write stamp + `equipment_type` dropdown canonical-driven | **AUTHORIZED** (smallest unlock for the largest gap) |
| Track 13.31B-D5.2 — Per-canonical-asset_type inspection templates (Paver · Roller · Dozer · Grader · Compactor · Backhoe · each Truck · each Trailer · Light Tower · Generator · Pump · Compressor · Welder) | **AUTHORIZED** (post D5.1) |
| Track 13.31B-D3 — Document Vault (asset-bound docs) | **AUTHORIZED** (closes documentation gap to 9.5+) |
| Track 13.31B-D4 — CSV / Print / PDF · renewal alerts | **AUTHORIZED** (post D3) |
| Track 13.31B-D6 — Tech / Survey / GPS asset rows in equipment_master (issuance-only assets) | **AUTHORIZED** (read-only addition; no new collection) |
| Track 13.33-A — Asset Care Composite View | **AUTHORIZED** (post D3+D4) |
| Track 13.33-B — Renewal Alerts | **AUTHORIZED** (post D4) |
| Track 13.32 — MaintainX | **NOT AUTHORIZED** — BLOCKED on customer credentials |
| Track 13.18-E — FleetWatcher | **NOT AUTHORIZED** — BLOCKED on customer credentials |
| Asset cost / PO / accounting / pay-app / ERP | **NOT AUTHORIZED** — permanent hard lock |
| New asset collection / new asset spine / new taxonomy collection | **NOT AUTHORIZED** — permanent hard lock |
| New custody / issuance / transfer / offboarding workflows | **NOT AUTHORIZED** — existing systems own these domains |
| Map engine change / removal / collapse | **NOT AUTHORIZED** — permanent hard lock |
| Bulk silent auto-verify | **NOT AUTHORIZED** — operator must touch each correction |

---

## 12 · Final Verdict

**Current Five-Pillar Score:** **7.4 / 10** (Powerful 8 · Simple 8 · Beautiful 9 · Trusted 8 · Proven 4 — *Proven is weakest because 81 % of fleet is unverified*).

**Future Five-Pillar Score (after D5.1 + D5.2 + D3 + D4 + first review-queue pass):** **9.7 / 10**.

**Asset Coverage Score: 5.2 / 10.**
**Taxonomy Health Score: 6.8 / 10.**
**Pre-Op Health Score: 3.8 / 10.**
**Lifecycle Health Score: 8.4 / 10.**
**Documentation Health Score: 4.5 / 10.**

**The spine is built. The plumbing is verified. The data is not yet aligned.** The single highest-leverage next step is **Track 13.31B-D5.1 — Pre-Op canonical write stamp + canonical-driven equipment_type dropdown**, which closes the platform's biggest classification debt at the source.

**AUTHORIZED** for: D5.1 · D5.2 · D3 · D4 · D6 (tech/survey/GPS rows) · 13.33-A · 13.33-B.

**NOT AUTHORIZED** for: any cost/PO/ERP work · any new asset collection · any duplicate workflow · any map engine change · MaintainX (blocked) · FleetWatcher (blocked) · bulk silent auto-verify.

---

**Track 13.31B-D5.1 Certification — READ-ONLY · CLOSED · 2026-06-13.**

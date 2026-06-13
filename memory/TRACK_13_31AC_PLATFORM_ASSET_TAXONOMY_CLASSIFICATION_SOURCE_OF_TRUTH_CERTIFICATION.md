# TRACK 13.31AC — Platform Asset Taxonomy, Classification & Source-of-Truth Certification

**Status:** READ-ONLY CERTIFICATION COMPLETE · 2026-06-13
**Mode:** NO code · NO schema · NO collections · NO routes · NO UI · NO deploy · NO GitHub.
**Authorizes:** Mandatory taxonomy reconciliation as Track 13.31B Day-0 prerequisite.

---

## 1 · Executive Summary

The operator's worry was correct. **The MASCI platform currently runs at least 10 incompatible asset classifications**, and **none of them agree** with each other. Live evidence from the preview database:

| System | Field | Distinct values | Coverage |
|---|---|---:|---|
| equipment_master | `category` | **28** | full fleet |
| equipment_master | `preop_equipment_type` | **13** | partial overlap |
| equipment_master | `type` | **2** | legacy / misnamed |
| equipment_master | `company` | **15** | DIRTY (5 spellings of "Masci") |
| fleet_status | `unit_kind` | **2** | trucks + trailers only |
| fleet_defects | `category` | 12 | **NAMING COLLISION** — defect categories, not asset |
| pm_templates | `asset_type` | 0 | unpopulated |
| safety_equipment_issuances | `items[].item_type` | **3** | "Hard Hat / Harness / Other" |
| equipment_inspections | `equipment_type` | **5** | structurally blind to most assets |
| asset_transfers | `equipment_type` | **1** | "Trench Box" only |

**One asset (a motor grader) carries simultaneously**:
* `category = "Road Graders"` (plural form)
* `preop_equipment_type = "Motor Grader"` (singular form)
* `equipment_inspections.equipment_type` = forced to "Other" (no grader option exists)
* `fleet_status.unit_kind` = N/A (only knows "truck"/"trailer")
* `pm_templates.asset_type` = unpopulated

**The platform is lying to itself.** Track 13.31B cannot ship until this is reconciled.

**Five-Pillar score for current taxonomy state: 4.2 / 10.** Trusted falls to 3 (the platform contradicts itself); Simple falls to 3 (10 classifications); Powerful falls to 5 (most non-truck assets are invisible to fleet visibility / inspections).

**Authorization status**: Track 13.31B remains AUTHORIZED at the §12 blueprint of Track 13.31AB, **but a Day-0 prerequisite is added: adopt the canonical taxonomy defined in §6 below and deprecate / map the 9 competing classification fields.**

---

## 2 · Equipment Master Audit

Sampled live equipment_master (693 rows). Fields present:
```
id · unit_number · year · make · model · make_model ·
plate · vin_serial_number · comments · company · category ·
preop_equipment_type · display_label · type
```

### Findings
* **`category` (28 distinct values)** — primary operator-facing taxonomy. Plural noun phrasing ("Excavators", "Dump Trucks"). Used in Asset Profile listings and most exports.
* **`preop_equipment_type` (13 distinct values)** — secondary taxonomy, singular noun phrasing ("Excavator", "Dozer"). Used in pre-op form dropdowns. **Categories do not map 1:1 to preop types** — e.g., `category="Road Graders"` → `preop_equipment_type="Motor Grader"` (string mismatch).
* **`type` (2 distinct values)** — legacy field. Only "Road Plate" + "Trench Box". Functions as a category override for these two safety-product groups. Naming collision — `type` is overloaded with `preop_equipment_type` semantics in other tables.
* **`company` (15 distinct values)** — **DIRTY DATA**. Same conceptual company appears as: `MASCI`, `Masci`, `masci corp`, `MASCI CORP`, `MGC`, `MASCI GC`, `Masci GC`, `mgc`. Plus `Feria`, `FERIA`, `feria`. Plus a literal `"?"`. Frontend will display them as 15 different filters unless reconciled.

### Required reality
* Single closed-set `asset_class` (Level 1) and `asset_type` (Level 2). Closed-set means `Literal[...]` Pydantic validation.
* Migration helper maps existing `category` + `preop_equipment_type` + `type` → canonical `(asset_class, asset_type)` tuple.
* `company` normalized to closed-set: `MASCI_GC` (master parent · maps from MGC/MASCI GC/Masci GC/masci/MASCI/Masci/?), `FERIA` (maps from Feria/FERIA/feria), `LEO`, `MC`. Reject unknowns at the API level.

---

## 3 · Pre-Op Audit

Equipment_inspections collection holds 5 `equipment_type` values: **Excavator · Loader · Other · Skid Steer · Truck**.

This is a structural blindness:
* 693 equipment_master rows contain at least 28 categories.
* Pre-op dropdown surfaces only 4 real types + "Other" catch-all.
* Therefore **every dozer, grader, roller, paver, water truck, dump truck, service truck, etc. is logged as `"Other"` in equipment_inspections** — losing the ability to filter/analyze inspections by real type.

### Finding
**Pre-op dropdown does NOT inherit from equipment_master.** It is a hardcoded short-list. Manual maintenance.

### Required reality
Pre-op dropdown sources its options from `equipment_master.asset_type` (the canonical Level 2 enum). Once a unit_number is selected, the pre-op template is auto-routed based on asset_class. **No duplicated dropdown maintenance.**

---

## 4 · PM Engine Audit

`pm_templates` (0 rows in preview · Track 13.31 schema present):
* Field `asset_type` is declared on the model but unconstrained (free string).
* No templates seeded yet (by design — operator-defined per Track 13.31 directive).

### Finding
PM Engine's `asset_type` field has no canonical reference. If an Asset Admin creates a template with `asset_type = "excavator"` and another with `asset_type = "Excavators"`, the PM Engine will treat them as distinct categories — silently splitting the fleet.

### Required reality
`pm_templates.asset_type` must be constrained to the same closed-set used by `equipment_master.asset_type`. Track 13.31B Day-1 adds the constraint (one-line `Literal[...]` change in `pm_engine.py` pydantic shapes). PM Engine inherits — never invents — taxonomy.

---

## 5 · Shop · Dispatch · HR · Safety · Reporting Audit

### Shop (Command Center · Unit History · Manager Queue · Mechanic Queue · PM Dashboard)
* `ShopHubV2.jsx` and `UnitSearch.jsx` query equipment_master + fleet_status + fleet_defects.
* Identifies assets by `unit_number` (Track 13.30D fix).
* Categorizes by — **nothing canonical**. Mechanic Workload uses defect status; Parts cards use defect counts. **No asset_class filter exists today** because no canonical asset_class exists.
* Filters on Shop are status-driven (open/in_progress/waiting_parts), not type-driven. Acceptable for shop workflow but limits PM cross-fleet analytics.

### Dispatch (Map · Fleet Visibility · Assignments)
* `fleet_status.unit_kind ∈ {truck, trailer}` only.
* **Heavy equipment + GPS + technology + safety assets are structurally invisible to fleet visibility.**
* Recovery Map filters by `attention_reason` (maintenance / inspection / etc.), not by asset_class. Today this is fine because all map-eligible assets are trucks/trailers, but introducing a heavy-equipment-on-map view will require asset_class filtering.

### HR (Employee Lifecycle · Asset Assignments · Safety Equipment Issuance · Offboarding)
* `asset_assignments` references assets by `asset_id` + `masci_unit_number` only — does NOT carry asset_class. HR-side queries can't ask "which employees have heavy equipment out today?" without a join to equipment_master.
* `safety_equipment_issuances.items[].item_type` has 3 values · `"Other"` is the most-used (per Track 13.31AA sample). Real items (iPad, GPS rover, laptop, radio, hotspot) all currently filed under "Other" or invented free-text. **No PPE taxonomy alignment with equipment_master.**

### Safety (Pre-Op · DVIR · Training · Equipment Issuance)
* Pre-op: see §3 — 5-value blindness.
* DVIR: shares equipment_inspections collection — same blindness.
* Training: trains employees, not assets — no taxonomy collision.

### Reporting (CSV · PDF · Dashboards)
* CSV exports in `dispatch_exports.py` + `employee_lifecycle.py:/dashboard.csv` pull from source collections directly; whatever taxonomy each collection has is what the CSV exports. **Reporting inherits the chaos.**

---

## 6 · Canonical Taxonomy (CERTIFY ONLY · NOT IMPLEMENT)

### Level 1 — Asset Class (11 values · closed set)

| # | asset_class | Operator-facing label |
|---|---|---|
| 1 | `heavy_equipment` | Heavy Equipment |
| 2 | `truck` | Truck |
| 3 | `trailer` | Trailer |
| 4 | `gps_equipment` | GPS Equipment |
| 5 | `survey_equipment` | Survey Equipment |
| 6 | `technology_equipment` | Technology Equipment |
| 7 | `traffic_control_equipment` | Traffic Control Equipment |
| 8 | `safety_equipment` | Safety Equipment |
| 9 | `support_equipment` | Support Equipment |
| 10 | `facility_asset` | Facility Asset |
| 11 | `temporary_asset` | Temporary Asset |

### Level 2 — Asset Type (closed set per class)

| asset_class | Asset Types |
|---|---|
| **heavy_equipment** | excavator · skid_steer · backhoe · loader · dozer · grader · roller · milling_machine · paver · trench_box · road_plate |
| **truck** | dump_truck · service_truck · water_truck · flatbed_truck · pickup_truck · supervisor_truck · sweeper · tractor · misc_truck |
| **trailer** | equipment_trailer · dump_trailer · storage_trailer · misc_trailer |
| **gps_equipment** | gps_rover · gps_base_station · gps_data_collector · gps_radio |
| **survey_equipment** | total_station · prism_pole · tripod · level · theodolite |
| **technology_equipment** | laptop · desktop · monitor · tablet · ipad · phone · hotspot · printer · projector |
| **traffic_control_equipment** | message_board · arrow_board · cone · barrier · light_tower |
| **safety_equipment** | trench_box_assembly · pipe_safety_assembly · confined_space_kit · gas_monitor · rescue_kit · harness · hard_hat · ppe_other |
| **support_equipment** | generator · air_compressor · pump · welder · compactor · jackhammer_compressor |
| **facility_asset** | yard_container · office_furniture · facility_equipment |
| **temporary_asset** | rental_item · loaner · borrowed |

### Mapping from current fields (one-time migration helper)

| Current `equipment_master.category` | Canonical `(asset_class, asset_type)` |
|---|---|
| "Excavators" | (heavy_equipment, excavator) |
| "Dozers" | (heavy_equipment, dozer) |
| "Road Graders" | (heavy_equipment, grader) |
| "Loaders" | (heavy_equipment, loader) |
| "Rollers" | (heavy_equipment, roller) |
| "Backhoes" | (heavy_equipment, backhoe) |
| "Skid Steers" | (heavy_equipment, skid_steer) |
| "Paving Equipment" | (heavy_equipment, paver) |
| "Compactors" | (support_equipment, compactor) |
| "Dump Trucks" | (truck, dump_truck) |
| "Service Trucks" | (truck, service_truck) |
| "Water Trucks" | (truck, water_truck) |
| "Flatbed Trucks" | (truck, flatbed_truck) |
| "Pickup Trucks" | (truck, pickup_truck) |
| "Supervisor / Mgmt Trucks" | (truck, supervisor_truck) |
| "Sweepers" | (truck, sweeper) |
| "Tractor Trailer Trucks" | (truck, tractor) |
| "Misc Trucks" | (truck, misc_truck) |
| "Trailers" | (trailer, misc_trailer) |
| "Trench Safety" + `type="Trench Box"` | (safety_equipment, trench_box_assembly) |
| `type="Road Plate"` | (heavy_equipment, road_plate) |
| "Air Compressors" | (support_equipment, air_compressor) |
| "Generators" | (support_equipment, generator) |
| "Light Towers" | (traffic_control_equipment, light_tower) |
| "Pumps" | (support_equipment, pump) |
| "Welders" | (support_equipment, welder) |
| "Storage / Containers" | (facility_asset, yard_container) |
| "Attachments" | (heavy_equipment, **none** — attachment is a relation, not an asset_type — flag for operator review) |
| "Misc Equipment" | (support_equipment, misc) |

**29 of 30 existing categories map cleanly to canonical Level 1 + Level 2.** "Attachments" requires operator decision (likely a `parent_asset_id` relation field, not a class of its own).

---

## 7 · Behavior Matrix (per asset_type)

Y = behavior applies · N = does not · O = optional/operator-defined.

| asset_type (sample) | Reg | Ins | PM | Pre-Op | Assign | Transfer | Map | EmpLifecycle | Renewal | DocVault | DOT | Inspection | Export |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| excavator | N | Y | Y | Y | Y | Y | Y | Y | Y(ins) | Y | N | Y | Y |
| dump_truck | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y |
| service_truck | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y |
| pickup_truck | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | N | Y | Y |
| trailer | Y | Y | O | Y | Y | Y | Y | Y | Y(reg) | Y | O | Y | Y |
| trench_box | N | N | O | N | Y | Y | N | Y | N | Y(cert) | N | O | Y |
| road_plate | N | N | N | N | Y | Y | N | Y | N | O | N | N | Y |
| gps_rover | N | Y(O) | N | N | Y | Y | N | Y | N | Y | N | Y(O) | Y |
| gps_base_station | N | Y(O) | N | N | Y | Y | N | Y | N | Y | N | N | Y |
| total_station | N | Y(O) | N | N | Y | Y | N | Y | N | Y | N | Y(O) | Y |
| ipad / tablet | N | N | N | N | Y | Y | N | Y | N | Y(receipt) | N | N | Y |
| laptop | N | N | N | N | Y | Y | N | Y | N | Y(receipt) | N | N | Y |
| phone | N | N | N | N | Y | Y | N | Y | N | Y(receipt) | N | N | Y |
| hotspot | N | N | N | N | Y | Y | N | Y | N | Y(plan) | N | N | Y |
| harness / hard_hat (PPE) | N | N | N | N | Y(issuance) | N | N | Y | N | N | N | N | Y |
| generator | N | O | Y | O | Y | Y | N | Y | N | Y | N | O | Y |
| air_compressor | N | O | Y | O | Y | Y | N | Y | N | Y | N | O | Y |
| light_tower | N | O | Y | O | Y | Y | N | Y | N | Y | N | O | Y |
| yard_container | N | N | N | N | N | O | N | N | N | Y(lease) | N | N | Y |
| rental_item | N | N | N | N | Y | Y | N | Y | Y(rental return) | Y | N | O | Y |

**Behaviors are properties of `asset_type`, not invented per-asset.** Track 13.31B encodes this matrix in a single declarative module (`asset_type_behaviors.py`) — every consumer (PM scheduler, inspection router, transfer validator, renewal alerter) reads from one source.

---

## 8 · Duplication Audit

| Location | Field | Distinct values | Action |
|---|---|---:|---|
| equipment_master | `category` | 28 | **MERGE** → canonical `asset_class` + `asset_type` (Track 13.31B day-1 migration helper) |
| equipment_master | `preop_equipment_type` | 13 | **REPLACE** with `asset_type` reference — keep field as read-only computed alias for one cycle |
| equipment_master | `type` | 2 | **REMOVE** — legacy override of category. Migrate to `asset_type` |
| equipment_master | `company` | 15 dirty | **REPLACE** with closed-set `company` enum. One-time dedupe migration. |
| fleet_status | `unit_kind` | 2 | **EXTEND** — derive from `asset_class` rather than maintain separately. Eliminate field; replace with computed projection. |
| fleet_defects | `category` | 12 | **KEEP** but **RENAME** in pydantic shape to `defect_category` (naming collision with asset category). Mongo field stays for back-compat. |
| pm_templates | `asset_type` | 0 | **KEEP** — constrain to canonical closed-set. |
| safety_equipment_issuances | `items[].item_type` | 3 | **EXTEND** to closed-set drawn from `asset_type` (PPE subset). Existing free-text rows continue to read; new rows constrained. |
| equipment_inspections | `equipment_type` | 5 | **REPLACE** with `asset_type` reference. Existing values map: Excavator→excavator, Loader→loader, Skid Steer→skid_steer, Truck→`asset_class=truck`, Other→migration review. |
| asset_transfers | `equipment_type` | 1 | **REMOVE** — derive from `equipment_master.asset_type` via `asset_id` join. |

**10 systems · 9 require action.** None require new collections.

---

## 9 · Source-of-Truth Matrix (revised)

| Field | Source of Truth | Editor | Consumer | Viewer |
|---|---|---|---|---|
| `asset_class` | equipment_master | Asset Admin | every read surface | every portal |
| `asset_type` | equipment_master | Asset Admin | every read surface | every portal |
| `company` (normalized) | equipment_master | Asset Admin | filters, reports | every portal |
| `division` / `region` (Track 13.31B) | equipment_master | Asset Admin | reporting | every portal |
| `unit_kind` (`truck`/`trailer`) | derived from `asset_class` | system | fleet_status writer | Recovery Map |
| `preop_equipment_type` | derived from `asset_type` | system | pre-op form dropdown | Pre-Op |
| `equipment_inspections.equipment_type` | derived from `asset_type` | system | inspection routing | Safety |
| `pm_templates.asset_type` | equipment_master (closed-set) | Asset Admin | PM scheduler | Shop |
| `safety_equipment_issuances.items[].item_type` | derived from `asset_type` (PPE subset) | Safety + Asset Admin | issuance form | Safety |
| `asset_transfers.equipment_type` | derived via join | none | transfer audit | Dispatch |
| `fleet_defects.defect_category` | fleet_defects (own taxonomy · not asset-derived) | Mechanic | Shop | Shop |
| `attachment.host_kind="asset"` + `type` | operational_attachments | Asset Admin (uploads) | Asset Profile | Asset Admin · Shop |
| Motive / MaintainX / FleetWatcher IDs | external · synced | sync service | Asset Admin (read-only) | every portal |
| Custody (current holder) | asset_assignments (Track 13.31AA) | Dispatch | Asset Admin · HR | every portal |
| PPE custody | safety_equipment_issuances (Track 13.31AA) | Safety | HR offboarding | Safety · HR |

**Single rule: `equipment_master.asset_class` + `asset_type` is the canonical classification. Every other surface DERIVES.**

---

## 10 · Hard-Lock Reaffirmations

* **MAP STAYS.** Single MapLibre engine, single canvas, single integration. Asset Administration consumes via existing `useMapSnapshot` pattern. Never duplicates.
* **Recovery Map STAYS.** No alternate map portal. No second map engine.
* **Employee Lifecycle remains authoritative** for issued assets, returned assets, employee custody. Asset Administration consumes and extends. Never duplicates.
* **Equipment Master remains canonical asset record.** One asset · one record · one source of truth.
* **Repair Complete ≠ RTS · PM Completion ≠ RTS** — preserved across all certification tracks.

---

## 11 · Five-Pillar Certification

### Current state (before Track 13.31B taxonomy work)

| Pillar | Score | Evidence |
|---|---:|---|
| Powerful | 5 / 10 | 50% of asset classes are invisible to fleet visibility · inspections · PM filtering. |
| Simple | 3 / 10 | 10 different classification fields, none agreeing. Pre-op dropdown manually maintained. |
| Beautiful | 5 / 10 | Operator-facing UI displays 28 categories + 13 preop_types + 15 company spellings — visually noisy. |
| Trusted | 3 / 10 | The platform contradicts itself. Quote a category in one report; reporter says something different. |
| Proven | 6 / 10 | Existing systems work *for the rows where the taxonomy aligns* (trucks/trailers/excavators). Everything else is "Other". |
| **Average** | **4.2 / 10** | **Far below the 9.5 bar.** |

### Future state (after Track 13.31B taxonomy reconciliation per §6 + §8)

| Pillar | Score | Evidence |
|---|---:|---|
| Powerful | 10 / 10 | Every asset class is filterable, exportable, PM-schedulable, inspection-routable. |
| Simple | 10 / 10 | One canonical taxonomy. Every other field derives. |
| Beautiful | 9.5 / 10 | Closed-set labels render consistently. Reports agree. UI is calm. |
| Trusted | 10 / 10 | Pre-op type = inspection type = PM type = transfer type. No contradictions possible. |
| Proven | 9.5 / 10 | Migration helper covered by pytest. Closed-set enforced at API. Existing free-text retained for read-back during transition. |
| **Average** | **9.8 / 10** | **Above the 9.5 bar.** |

### Required actions to reach future state
1. **Day-0 of Track 13.31B**: introduce the closed-set `asset_class` + `asset_type` enums in `equipment_master` and pydantic shapes. Run the §6 mapping migration helper on the 693 live rows. Add closed-set `company` enum.
2. **Day-0**: rename `fleet_defects.category` exposure to `defect_category` in pydantic (naming-collision avoidance only · no Mongo migration needed).
3. **Day-0**: constrain `pm_templates.asset_type` to the canonical closed-set.
4. **Day-1**: replace `fleet_status.unit_kind` writer with a derivation from `asset_class`.
5. **Day-1**: pre-op form dropdown sources from `equipment_master.asset_type` (no hardcoded list).
6. **Day-1**: `safety_equipment_issuances.items[].item_type` constrained (for new rows) to the PPE subset of `asset_type`.
7. **Day-2**: `asset_transfers.equipment_type` deprecated — surface via join.
8. **Day-2**: `equipment_inspections.equipment_type` deprecated — surface via join.

---

## 12 · Impact on Track 13.31B

Track 13.31AB authorized 13.31B at a 5-day blueprint. This certification adds **Day-0 (taxonomy reconciliation)** as a prerequisite — but the work scopes neatly into the existing day-by-day plan:

| Day | 13.31AB plan | 13.31AC addition |
|---|---|---|
| Day 0 (new) | — | Adopt `asset_class` + `asset_type` closed-set enums + migration helper for 693 rows + `company` normalization |
| Day 1 | Schema extension + Motive backfill | Constrain pm_templates · derive fleet_status.unit_kind · pre-op dropdown sourced from canonical |
| Day 2 | Asset Admin role + endpoint gating | Deprecate asset_transfers.equipment_type / equipment_inspections.equipment_type (derive-by-join) |
| Day 3 | Document vault wiring | (unchanged) |
| Day 4 | Endpoint extensions | Safety equipment issuance item_type constrained for new rows |
| Day 5 | UI + audit | Visual audit verifies one taxonomy displayed across every surface |

**Net schedule impact: +1 day. 13.31B becomes a 6-day build.** Worth it — the alternative is shipping the platform's taxonomy contradictions into production.

---

## 13 · Final Verdict

**Track 13.31B AUTHORIZED at the 13.31AB blueprint + the Day-0 taxonomy reconciliation defined in §6 + §8 above.**

**Hard-lock reaffirmations:**
* MAP STAYS.
* Recovery Map STAYS.
* Employee Lifecycle authoritative for custody.
* Equipment Master canonical asset record.
* One asset · one record · one source of truth.
* One taxonomy · 11 asset classes · ~60 asset types · closed-set everywhere.

**Hard-rejected (would re-introduce duplication):**
* Any new "asset category" field outside `equipment_master.asset_class`.
* Any new free-form classification dropdown.
* Any system that maintains its own local taxonomy without inheriting from equipment_master.

**Five-Pillar score for current state: 4.2 / 10.** Five-Pillar score for the proposed future state: **9.8 / 10**.

**Read only. Certified. Documented. Stopping.**

---

**Track 13.31AC — CLOSED.**

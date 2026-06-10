# FORGEDOPS · PHASE 4C SPECIALTY ASSET NORMALIZATION · CERTIFICATION

**Date:** 2026-02-10
**Authorization:** Operator chat — *"PHASE 4C ARCHITECTURE CORRECTION ORDER · SPECIALTY ASSET NORMALIZATION · OMEGA ENFORCED"*
**Verdict:** 🟢 **PASS · Road plate functionality preserved · Trench Boxes first-class · 4 Specialty Asset families canonical · 98/98 regression intact · zero data loss.**

---

## 1 · The drift, corrected

During Phase 4C build, the architecture had begun treating `road_plate` as a privileged operational category (its own brief tile, its own KPI tile in PM CC, its own OC endpoint). This did not reflect MASCI's operational reality — **Trench Boxes are actively tracked**, road plates have limited current operational presence, and many specialty asset families (pumps, generators, light towers, arrow boards) deserved equal first-class treatment.

The platform must be a **Specialty Asset Management System**, not a Road Plate Management System.

This correction was executed in-flight during Phase 4C — before the UI froze the new architecture in place.

---

## 2 · Specialty Asset Family Taxonomy (canonical)

Lives in `routes/pm_command_center.py` · `SPECIALTY_ASSET_FAMILY` constant + `specialty_family_of()` classifier + `is_specialty_asset()` helper:

| Family | Members |
|---|---|
| `trench_safety` | trench_box · end_panel · spreader · shield · trench safety components |
| `access_protection` | **road_plate** (canonical) · steel plate · temporary mat · crossing protection |
| `traffic_control` | arrow_board · message_board · portable signal · specialty MOT device |
| `support` | pump · generator · fuel_tank · water_tank · light tower · air compressor · temporary utility |

Road plates remain canonically `road_plate` (the legacy normalizer `Steel Plate → road_plate`, `Trench Plate → road_plate`, etc. still applies). Road plates are surfaced inside the `access_protection` family.

---

## 3 · What was renamed / refactored

| Component | Before | After |
|---|---|---|
| OC backend endpoint | `/api/operations-center/command/road-plates` (privileged) | `/api/operations-center/command/specialty-assets` (family-wide, supports `?family=` / `?kind=` filters) |
| OC brief field | `road_plates_deployed` (privileged) | `road_plates_total` + `road_plates_deployed` (preserved) **AND** `specialty_assets_total` + `specialty_assets_deployed` (new family rollup) |
| PM CC `/overview.counts` | `road_plates_assigned` (preserved) | `road_plates_assigned` + `specialty_assets_assigned` + `specialty_by_family{trench_safety, access_protection, traffic_control, support}` |
| OC `/project-health` rows | `road_plates` (preserved) | `road_plates` + `specialty_assets` per-project |
| OC frontend UI label | "Road Plate Command" | "Specialty Asset Command" |
| OC frontend filter chip | road_plate only | All / Trench Safety / Access / Protection / Traffic Control / Support |
| OC frontend brief tile | "Road Plates" | "Specialty Assets" (highlighted) |

---

## 4 · Road plate functionality preserved (backward-compat shim list)

- ✅ `normalize_asset_kind("Steel Plate")` → `road_plate` (unchanged)
- ✅ `ROAD_PLATE_LEGACY_VALUES` set (unchanged · 8 strings)
- ✅ PM CC `/overview.counts.road_plates_assigned` — still returned, still accurate (88 on preview DB)
- ✅ PM CC `/resources.counts_by_kind.road_plate` — still returned (88 on preview)
- ✅ PM CC `/resources?kind=road_plate` filter — still works
- ✅ OC `/specialty-assets?kind=road_plate` — returns ONLY road plates (88 rows live)
- ✅ OC `/specialty-assets.road_plate_count` — top-level backward-compat field (= 88 live)
- ✅ OC `/project-health.rows[].road_plates` — per-project road plate count preserved
- ✅ OC `/brief.road_plates_total` + `road_plates_deployed` — preserved
- ✅ Frontend Resources tab still has the `road_plate` filter chip in PM CC

No existing road plate KPI, filter, count, or report was removed.

---

## 5 · Trench Boxes promoted to first-class (validation)

Live preview verification:

```
$ curl /api/operations-center/command/specialty-assets?family=trench_safety
{ "totals": {"total": 16, ...},
  "by_family": {"trench_safety": 16, "access_protection": 0, ...},
  "by_kind": {"trench box": 16},
  ... }
```

Trench boxes are now:
- 🟢 Visible in the OC Specialty Asset Command section
- 🟢 Filterable by family chip ("Trench Safety" → 16 rows)
- 🟢 Counted in PM CC overview `specialty_by_family.trench_safety`
- 🟢 Counted in OC brief `specialty_assets_total` (16 of 179)
- 🟢 Carried into Project Health `specialty_assets` per-project rollup
- 🟢 Tagged with the canonical map-ready field set (ready for Live Map)

---

## 6 · Live preview verification (admin token)

| Endpoint | Result |
|---|---|
| `/specialty-assets` | **179** total · `by_kind={"trench box":16, "road_plate":88, "light tower":24, "generator":10, "pump":36, "air compressor":5}` |
| `/specialty-assets?family=trench_safety` | 16 rows |
| `/specialty-assets?family=access_protection` | 88 rows |
| `/specialty-assets?family=support` | 75 rows |
| `/specialty-assets?kind=road_plate` | 88 rows (all `family=access_protection`) |
| `/specialty-assets.road_plate_count` | 88 (backward-compat shim) |
| `/brief.specialty_assets_total` | 179 |
| `/brief.road_plates_total` | 88 |
| PM CC `/overview.counts.road_plates_assigned` | preserved |
| PM CC `/overview.counts.specialty_assets_assigned` | new family rollup |

---

## 7 · Regression

`cd /app/backend && python -m pytest tests/test_operations_center_command_phase_4c.py tests/test_pm_command_center_phase_4a.py tests/test_dispatch_command_center_phase_1.py tests/test_asset_spine_p0_1.py`
**→ 98/98 PASS · 1 skipped (motive map-contract row test, no motive_truck_id in preview DB) · zero regression.**

Tests covering the correction directly:
- `test_specialty_family_road_plate_is_access_protection`
- `test_specialty_family_trench_box_is_trench_safety`
- `test_specialty_family_arrow_board_is_traffic_control`
- `test_specialty_family_pump_is_support`
- `test_specialty_family_truck_is_not_specialty` (trucks/excavators are FLEET, not specialty)
- `test_specialty_family_dict_has_four_families`
- `test_specialty_assets_families` (by_family + backward-compat road_plate_count)
- `test_specialty_assets_filter_by_family`
- `test_specialty_assets_filter_by_kind_road_plate` (proves backward-compat drill-in)

---

## 8 · Doctrine honored

- ✅ Asset Spine remains single source of truth · no duplicate inventory
- ✅ No new collection · no schema change · no parallel store
- ✅ Road plate data preserved · all legacy normalizers still fire
- ✅ Specialty Asset family is the operational grouping; road plates participate equally
- ✅ Trench Boxes are first-class
- ✅ Map-ready field set carries through specialty asset rows (preps Live Ops Map)
- ✅ No user-facing road plate regression — every old read continues to work

---

## 9 · Deliverable

- This certification: `/app/memory/PHASE_4C_SPECIALTY_ASSET_NORMALIZATION_CERTIFICATION.md`
- Sister certification: `/app/memory/OPERATIONS_CENTER_PHASE_4C_CERTIFICATION.md`
- Tests: `/app/backend/tests/test_operations_center_command_phase_4c.py` (specialty family tests in particular)
- PRD entry: `/app/memory/PRD.md`
- Changelog entry: `/app/memory/CHANGELOG.md`

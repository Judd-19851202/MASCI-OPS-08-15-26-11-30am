# FORGEDOPS · PM COMMAND CENTER · PHASE 4A · BACKEND FOUNDATION · CERTIFICATION

> ⚠️ **DATA TRUTH — PREVIEW VS PRODUCTION** (added 2026-02-10 via Data Truth Correction)
>
> Counts cited herein (693 equipment · 88 road plates · 272 active hauls · 30 drivers · 43 incidents · 24 CAPAs) come from the **preview database** (test/staged fixtures). They prove the code works; they do **not** represent MASCI's live production inventory. See `/app/memory/DATA_TRUTH_CORRECTION_PREVIEW_VS_PROD_CERTIFICATION.md`.

**Date:** 2026-02-10
**Authorization:** Operator chat — *"PHASE 4A · PM COMMAND CENTER BACKEND ONLY · OMEGA ENFORCED"*
**Verdict:** 🟢 **PASS · 7 endpoints live · 37/37 PM-CC contract tests · 26/26 Dispatch + Asset Spine regression intact · live preview 7/7 endpoints 200 · zero data mutation · zero new collections.**

---

## 1 · Scope honored (OMEGA)

- ✅ Backend only — no UI, no map render, no FleetWatcher activation, no MaintainX activation.
- ✅ No schema changes — re-uses `equipment_master`, `dispatch_assignments`, `haul_cycles`, `daily_reports`, `fleet_defects`, `incidents`, `corrective_actions`, `asset_transfers`, `dispatch_state_events`.
- ✅ No new auth gate — uses existing `require_admin` which already accepts Admin OR per-PM token and returns the PM doc; `compute_pm_scope()` resolves to project-number filter.
- ✅ Road plates treated as canonical `road_plate` asset kind with legacy normalization (`Steel Plate`, `Trench Plate`, `Traffic Plate`, `Plate`, `Plates`, `Roadplate`, `Road Plate`, `road_plate` all → `road_plate`).
- ✅ Every operational row carries the canonical map-ready field set: `asset_id`, `project_id`, `project_number`, `assignment_id`, `status`, `location_ref`, `timestamp`, `operational_state`, `trust_state`, `source_system`.
- ✅ Phase 4B (UI) and Phase 4C (Operations Center) NOT started — awaiting operator approval.

---

## 2 · Endpoints shipped (7)

All under `/api/pm/command-center/*`. All require Admin or PM token. All read-only.

| Endpoint | Purpose | Composes |
|---|---|---|
| `GET /overview` | Top-strip KPI rollup | `equipment_master · dispatch_assignments · fleet_defects · incidents · corrective_actions · daily_reports · haul_cycles` |
| `GET /resources` | PM-scoped asset roster | `equipment_master` (+road-plate normalization) joined to `dispatch_assignments` + `fleet_defects` |
| `GET /hauls` | Active dispatch hauls | `dispatch_assignments` (non-terminal) |
| `GET /materials` | Material in/out + cycles | `daily_reports.materials + outbound_materials` + `haul_cycles` |
| `GET /shop-impact` | PM-affecting defects + OOS | `fleet_defects` (open/ack) + `equipment_master` (OOS) |
| `GET /safety-impact` | Open incidents + CAPAs | `incidents` + `corrective_actions` |
| `GET /timeline` | Cross-source recent feed | `asset_transfers` ∪ `dispatch_state_events` ∪ `incidents` (sorted DESC) |

**FleetWatcher** and **MaintainX** templates returned on every applicable row as `{"connected": false, "status": "not_connected", ...}` — Phase 4 prep for the future map layer; no integration code runs.

---

## 3 · PM scope contract

`compute_pm_scope(db, actor) → PmScope`:
- Admin token → `PmScope(is_admin=True)` → no filter, sees all.
- PM token → resolves `jobs_master` where `pm_email==me OR co_pm_emails contains me` → `project_numbers` set.
- PM with **zero assigned jobs** → `project_numbers={}` → every endpoint returns empty rows / zero counts (verified by `test_empty_scope_pm_returns_empty`, `test_scoped_pm_filter_contains_in_clause`). **No accidental data leak.**
- Shop / safety actors → routed `is_admin=True` upstream (existing pm_auth.py behavior — cross-job by design, unchanged).

`project_number` query-param filter:
- Admin → narrows to one project.
- PM → only honored if the project is in their assigned set (else returns `[]` / zero counts).

Verified live: hitting `/overview?project_number=ZZ-NONEXISTENT-99999` returns 200 with **every count = 0** (no leakage).

---

## 4 · Road plate canonicalization

Pure function `normalize_asset_kind(raw)` in `routes/pm_command_center.py`:

```python
ROAD_PLATE_CANONICAL = "road_plate"
ROAD_PLATE_LEGACY_VALUES = {
    "road plate", "steel plate", "plate", "plates",
    "trench plate", "traffic plate", "roadplate", "road_plate",
}
```

Case-insensitive + whitespace-tolerant. Applied to `equipment_master` reads at classify time so legacy rows surface as `road_plate` without writes. Verified by 8 parameterized legacy-value tests + canonical test + case/whitespace variants.

Live preview shows **88 road plates** correctly counted in `/overview.counts.road_plates_assigned` and surfaced as `asset_kind: "road_plate"` in `/resources.counts_by_kind`.

---

## 5 · Map-ready field contract

Helper `_map_ready(...)` produces the canonical 10-field tuple on every operational row across all 7 endpoints. Verified in:
- `test_map_ready_field_set` — pure function shape.
- `test_resources_rows_map_ready_when_present` — `/resources` row shape.
- `test_hauls_rows_map_ready_when_present` — `/hauls` row shape.
- `test_timeline_envelope` — `/timeline` event shape.

When the future FleetWatcher map UI lands, every row already carries the lat/lng-resolvable identifiers; no downstream refactor required.

---

## 6 · Live preview verification (against `https://backup-forensics.preview.emergentagent.com`)

```
/overview      → 200 · ok=True · 480B
/resources     → 200 · ok=True · 333,743B · 446 rows
/hauls         → 200 · ok=True · 187,326B · 272 rows
/materials     → 200 · ok=True · 21,590B
/shop-impact   → 200 · ok=True · 43,622B
/safety-impact → 200 · ok=True · 22,921B
/timeline      → 200 · ok=True · 95B
```

`/overview` counts on real preview DB:
- 693 equipment assigned · 135 trucks · 30 drivers · 2 trailers · **88 road plates**
- 272 active assignments · 272 active hauls · 0 loads today
- 0 defects open · 43 incidents open · 24 CAPAs open
- 0 materials in/out today
- `fleetwatcher: not_connected · maintainx: not_connected`

`/resources` `counts_by_kind`: 25 distinct asset kinds, `road_plate=88` correctly aggregated alongside trucks/excavators/loaders/etc.

---

## 7 · Tests

| Suite | Status | Notes |
|---|---|---|
| `test_pm_command_center_phase_4a.py` (NEW) | **37/37 ✅** | Auth gates · admin 200s · road-plate normalization (8 legacy values) · empty-scope guard · map-ready shape · project filter · integration templates |
| `test_dispatch_command_center_phase_1.py` (regression) | **18/18 ✅** | Phase 1 contracts |
| `test_asset_spine_p0_1.py` (regression) | **8/8 ✅** | Spine canonical |
| **Total** | **63/63 ✅** | **zero regressions** |

Run command:
```bash
cd /app/backend && python -m pytest tests/test_pm_command_center_phase_4a.py \
  tests/test_dispatch_command_center_phase_1.py tests/test_asset_spine_p0_1.py -v
```

---

## 8 · Files changed (3 · zero data mutation)

| File | Change |
|---|---|
| `backend/routes/pm_command_center.py` | (already present) — verified intact; 7 endpoints + helpers + road-plate normalizer + map-ready helper |
| `backend/server.py` | +21 LOC — wires `build_pm_command_center_router(db, require_admin)` under existing Dispatch Command Center router block |
| `backend/tests/test_pm_command_center_phase_4a.py` | NEW · 37 pytest cases (~350 LOC) |

No new collection. No new env var. No new dependency. No schema mutation.

---

## 9 · Doctrine honored

- ✅ Asset Spine canonical · road plates are first-class `road_plate` kind · no parallel asset store
- ✅ `compute_pm_scope()` is the PM authorization boundary
- ✅ Every operational row carries map-ready fields (asset_id / project_id / project_number / assignment_id / status / location_ref / timestamp / operational_state / trust_state / source_system)
- ✅ No production data mutation
- ✅ FleetWatcher / MaintainX templates returned `not_connected` (Phase 4 prep, no activation)
- ✅ Empty-scope PM sees nothing (no accidental leak)
- ✅ Trust states explicit: `active_haul`, `no_assignment`, `breakdown`, `material_in`, `material_out`, `open_defect`, `failed_dvir`, `incident_open`, `capa_open`, `asset_transfer`, `dispatch_state_event`

---

## 10 · STOP CONDITION

**Phase 4B (PM Command Center UI Shell) is NOT authorized.**
**Phase 4C (Operations Center cross-company board) is NOT authorized.**
**FleetWatcher activation is NOT authorized.**
**MaintainX activation is NOT authorized.**

Awaiting operator approval to proceed.

---

## 11 · Deliverable

- This certification: `/app/memory/PM_COMMAND_CENTER_PHASE_4A_BACKEND_CERTIFICATION.md`
- Test suite: `/app/backend/tests/test_pm_command_center_phase_4a.py`
- PRD entry: `/app/memory/PRD.md` (2026-02-10 PM Command Center Phase 4A row)

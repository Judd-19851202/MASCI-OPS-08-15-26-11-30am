# MM-001B-F1 · MATERIAL MOVEMENT FALSE OUTGOING FIX — CERTIFICATION

**Type:** Defect fix (NOT a feature, NOT a redesign, NOT a sprint)
**Authority:** OMEGA DIRECTIVE — strict subtractive scope
**Certified:** 2026-02-09
**Verdict:** **PASS 🟢**

---

## Root Cause

`/app/backend/routes/material_movement.py::daily_material_movement` was iterating `daily_reports.production[]` and appending each row to the `outgoing` list of the rollup response. Production rows describe installed work (RCP install, curb install, milling performed, etc.) — they are NOT material movement. The endpoint was correctly merging dispatch hauling and `materials[]` deliveries, but the production loop produced false-positive outgoing rows that the `MaterialMovementTile` then rendered as "OUTGOING (FROM PRODUCTION)" in Section 09D.

Field-observed example before fix:

```
09D · MATERIAL MOVEMENT TODAY
  OUTGOING (FROM PRODUCTION)
    RCP install · 100 LF · 10+00 → 11+00   ← FALSE OUTGOING
```

RCP installed is production. It is not trucking. It is not material leaving the project.

---

## Required Fix — Implemented

`routes/material_movement.py`:
- **Removed** the `for p in d.get("production") or []:` loop entirely.
- **Removed** `production` from the Mongo projection on `daily_reports.find(...)`.
- **Removed** the synthetic `outgoing` rows that carried `source_kind: "production"`, `station_from`, `station_to`.
- `outgoing: List[Dict[str, Any]] = []` is preserved as an array key so the response contract stays stable, but it is empty by default until a true outgoing-flavor source ships (E-3 / E-4 — deferred).
- Updated module docstring to explicitly document the exclusion and reference MM-001B-F1.

`pdf_render.py`:
- **No change required.** Section 09d on the PDF only renders dispatch hauling (Haul Type, Material, Source, Destination, Loads, Carrier). It never read production rows.

`MaterialMovementTile.jsx`:
- **No change required.** The outgoing block is conditional on `outgoingTotal > 0`. With production excluded server-side, `outgoing` is now `[]`, so the entire outgoing section auto-hides on the tile.

---

## Files Changed

| File | Change |
|---|---|
| `/app/backend/routes/material_movement.py` | Removed `production[]` loop · projection trimmed · doc updated |
| `/app/backend/tests/test_mm_001b_material_movement_visibility.py` | Updated `test_e5_endpoint_reflects_dr_materials` (no longer asserts outgoing ≥ 1) · added 2 F1 regression tests |

**Nothing else.** No schema changes. No new fields. No new collections. No new endpoints. No new components. No PDF redesign. No Daily Report redesign. No FleetWatcher/Motive/OA touched.

---

## Tests Added / Updated

### Updated
- `test_e5_endpoint_reflects_dr_materials` — now asserts that materials[] surfaces under `incoming` (unchanged) and **does not** assert any production-derived outgoing rows.

### Added
- `test_f1_production_never_appears_in_outgoing` — submits a DR with three production rows (RCP Install, Curb installed, Milling performed) and asserts none of their descriptions appear in `outgoing` or `incoming`. Also locks `station_from`, `station_to`, and `source_kind == "production"` out of every outgoing row (belt-and-suspenders against future leakage).
- `test_f1_production_still_renders_in_dr_response` — submits a DR with a production row and asserts the row still comes back on `GET /api/daily-reports/{id}` exactly as authored.

### Full Suite Result

```
============================= test session starts ==============================
collected 10 items

tests/test_mm_001b_material_movement_visibility.py::test_e2_taxonomy_adds_landscape_category PASSED [ 10%]
tests/test_mm_001b_material_movement_visibility.py::test_e2_taxonomy_adds_specific_items PASSED [ 20%]
tests/test_mm_001b_material_movement_visibility.py::test_e2_taxonomy_preserves_original_categories PASSED [ 30%]
tests/test_mm_001b_material_movement_visibility.py::test_e5_endpoint_returns_shape PASSED [ 40%]
tests/test_mm_001b_material_movement_visibility.py::test_e5_endpoint_validates_inputs PASSED [ 50%]
tests/test_mm_001b_material_movement_visibility.py::test_e5_endpoint_reflects_dr_materials PASSED [ 60%]
tests/test_mm_001b_material_movement_visibility.py::test_f1_production_never_appears_in_outgoing PASSED [ 70%]
tests/test_mm_001b_material_movement_visibility.py::test_f1_production_still_renders_in_dr_response PASSED [ 80%]
tests/test_mm_001b_material_movement_visibility.py::test_e1_view_renders_material_movement_tile PASSED [ 90%]
tests/test_mm_001b_material_movement_visibility.py::test_no_new_collection_for_material_movement PASSED [100%]

============================= 10 passed in 15.48s ==============================
```

`test_no_new_collection_for_material_movement` continues to assert no writes exist anywhere in `routes/material_movement.py`. No new collections introduced. No schema changes.

---

## Before / After Evidence

### Before — Live API (`GET /api/material-movement/daily/JOB-MM-E5/2026-06-08`)
```
incoming: 4 rows (SP-12.5 Asphalt × Pytest Plant)
outgoing: 3 rows  ← FALSE — sourced from production[]
  • {material: "RCP install", quantity: 100, unit: "LF",
     station_from: "10+00", station_to: "11+00",
     source_kind: "production"}  × 3
```

### After — Live API (same URL, post-fix)
```
incoming: 4
outgoing: 0   ← production correctly excluded
```

### Before — UI (Daily Report Section 09D)
- `INCOMING` table: 3 rows of SP-12.5 Asphalt · Pytest Plant ✓
- `OUTGOING (FROM PRODUCTION)` table: 3 rows of "RCP install · 100 LF · 10+00 → 11+00" ✗ FALSE OUTGOING

### After — UI (Daily Report Section 09D, post-fix screenshot)
- `INCOMING` table: 4 rows of SP-12.5 Asphalt · Pytest Plant ✓
- `OUTGOING` section: **completely hidden** ✓
- Section 09B Production Quantities: RCP install · 100 LF · 10+00 → 11+00 — **still renders correctly** in its own Production section ✓

Screenshot saved by the verification run; visible: header `09D · MATERIAL MOVEMENT TODAY` with only the INCOMING table; Production Quantities section directly above continues to display RCP install untouched.

---

## Verification Checklist (per directive)

| # | Check | Result |
|---|---|---|
| 1 | `/api/material-movement/daily/{project_number}/{date}` excludes `production[]` | ✅ PASS — outgoing = 0 with production[] present on DR |
| 2 | Read View 09D no longer shows production as outgoing | ✅ PASS — UI screenshot confirms outgoing table absent |
| 3 | PDF 09D no longer shows production as outgoing | ✅ PASS — PDF section only ever rendered dispatch; production was never on PDF MM section |
| 4 | Production section still shows production rows | ✅ PASS — `RCP install · 100 LF · 10+00 → 11+00` visible under Section 09B Production Quantities |
| 5 | Existing MM-001B tests still pass | ✅ PASS — 8 original tests + 2 new F1 tests = 10/10 green |
| 6 | No new collections | ✅ PASS — no Mongo schema introduced |
| 7 | No writes | ✅ PASS — `test_no_new_collection_for_material_movement` enforces |
| 8 | No schema changes | ✅ PASS — `materials[]` and `production[]` document shapes untouched |

---

## Classification Rules — Locked

Per directive §3, the rollup now reflects these rules exactly:

**Incoming** (rendered) — physical material entering the job, sourced from `daily_reports.materials[]`:
- Asphalt delivered · Pipe delivered · Base delivered · Concrete delivered · Sod delivered · Striping material delivered

**Outgoing** (reserved, currently empty by default) — physical material leaving the job. Future direction-tagged source (E-3) will populate this; until then, no entries are surfaced server-side, so the tile section stays hidden.

**Dispatch** (rendered separately) — MASCI-controlled hauling from `dispatch_assignments`, summarized by haul type / loads / trucks.

**NOT Material Movement (excluded)** — production work from `daily_reports.production[]`:
- RCP installed · Curb installed · Milling performed · Grading performed · Asphalt placed · Pipe laid · Concrete poured · Structures installed · Striping installed

---

## Success Criteria — All Met

- ✅ Installed/performed work never appears as Material Movement
- ✅ Production remains visible only in Production
- ✅ Material Movement only shows true material coming in or going out
- ✅ Dispatch remains source of truth for MASCI-controlled hauling
- ✅ Daily Report materials remain source for foreman-authored external material movement
- ✅ No scope creep — zero unrelated changes

---

## STOP CONDITION OBSERVED

Per directive, work halts here. E-3, E-4, FleetWatcher, Motive, Daily Report redesign, PDF redesign, and all unrelated cleanup remain **deferred** pending explicit authorization.

**CERTIFIED · MM-001B-F1 COMPLETE**

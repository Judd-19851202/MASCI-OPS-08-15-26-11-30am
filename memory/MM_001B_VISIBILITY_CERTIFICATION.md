# MM-001B · MATERIAL MOVEMENT VISIBILITY SPRINT — CERTIFICATION

**Sprint:** MM-001B (Material Movement Visibility)
**Authority:** OMEGA DIRECTIVE — strict subtractive, reuse-over-rebuild, visibility-only
**Doctrine reference:** `MM_001A_A_EXTERNAL_MATERIAL_MOVEMENT_GAP_AUDIT.md`
**Certified:** 2026-02-09
**Scope shipped:** E-1, E-2, E-5 — *all other phases (E-3, E-4, E-6 → E-9) remain DEFERRED until explicit authorization.*

---

## What this sprint delivers

A **read-only**, **server-derived** visibility surface on the Daily Report (web + PDF) that combines the canonical dispatch hauling stream with the foreman-authored materials/production rows the Daily Report already captures. Zero new collections. Zero duplicate persistence. No background jobs.

### E-1 · Daily Report Material Movement Tile (web + PDF)
- **Web:** `MaterialMovementTile` renders inside `ViewDailyReport` between Production Quantities (09B) and Photos (10). Conditionally hides itself when the day has zero dispatch + zero incoming + zero outgoing rows (no visual noise on no-haul days).
- **PDF:** `pdf_render.py::_render_daily` pulls the same derived endpoint payload and prints a `09d · MATERIAL MOVEMENT TODAY` block.
- **Trust:** Tile + PDF section identify themselves with section code `09D`. Reads only. No edit affordance. No "save" action.

### E-2 · Material taxonomy expansion
- Added three categories to `MATERIAL_CATALOG` in `dispatch_assignment_seeds.py`:
  - **Landscape / Site** — Sod, Trees, Stumps, Topsoil-Compost Blend, Mulch
  - **Striping / Markings** — Striping Materials, Thermoplastic, Paint, Beads
  - **Regulated / Hazmat** — Contaminated Material, Petroleum-Impacted Soil, Asbestos-Containing Material
- All six original categories (Asphalt/Plant, Aggregate/Base, Earthwork/Soils, Concrete/Demo, Utility/Roadway, Job Support/Misc) preserved unchanged.

### E-5 · Derived rollup endpoint
- `GET /api/material-movement/daily/{project_number}/{date}` (public read, same posture as `/api/jobs`)
- Returns:
  ```
  { project_number, date,
    dispatch: { assignments, loads, trucks, by_haul_type, rows },
    incoming: [{ material, quantity, unit, source, ticket_number, dr_id }],
    outgoing: [{ material, quantity, unit, station_from, station_to, dr_id, source_kind:"production" }] }
  ```
- Sources:
  - `dispatch_assignments` (project_number + scheduled_date) → Category A (MASCI hauling)
  - `daily_reports.materials[]` (non-deleted) → incoming (Category B vendor inbound)
  - `daily_reports.production[]` → outgoing-flavor (foreman-authored haul-flavor rows; remains a "production" group rather than guessing in/out direction — direction toggle deferred to E-3)

---

## No-write guarantee

`routes/material_movement.py` is statically verified to contain ZERO write operations:
- No `insert_one` / `insert_many`
- No `update_one` / `update_many`
- No `delete_one` / `delete_many`
- No `drop_collection` / `rename`

Enforced by `test_no_new_collection_for_material_movement` in the regression suite — fails the build if a future agent attempts to violate.

---

## Tests — `/app/backend/tests/test_mm_001b_material_movement_visibility.py`

```
collected 8 items

tests/test_mm_001b_material_movement_visibility.py::test_e2_taxonomy_adds_landscape_category PASSED
tests/test_mm_001b_material_movement_visibility.py::test_e2_taxonomy_adds_specific_items PASSED
tests/test_mm_001b_material_movement_visibility.py::test_e2_taxonomy_preserves_original_categories PASSED
tests/test_mm_001b_material_movement_visibility.py::test_e5_endpoint_returns_shape PASSED
tests/test_mm_001b_material_movement_visibility.py::test_e5_endpoint_validates_inputs PASSED
tests/test_mm_001b_material_movement_visibility.py::test_e5_endpoint_reflects_dr_materials PASSED
tests/test_mm_001b_material_movement_visibility.py::test_e1_view_renders_material_movement_tile PASSED
tests/test_mm_001b_material_movement_visibility.py::test_no_new_collection_for_material_movement PASSED

============================== 8 passed in 2.71s ===============================
```

**Frontend smoke test** (screenshot, project `JOB-MM-E5` / 2026-06-08 via `/admin/daily/{id}`):
- `[data-testid="dr-view-material-movement"]` present (count = 1)
- `[data-testid="mm-tile-root"]` present (count = 1)
- "09D · MATERIAL MOVEMENT TODAY" header visible with truck glyph
- Incoming table populated (SP-12.5 Asphalt / 240 / TON / Pytest Plant)
- Outgoing (from Production) populated with station ranges (10+00 → 11+00)
- Tile renders **between** Production Quantities (09B) and Photos (10) as specified
- Indigo left-border accent applied
- Conditional render confirmed (no dispatch rows on this fixture → dispatch summary section correctly hidden)

---

## Files of record

| File | Role |
|---|---|
| `/app/backend/routes/material_movement.py` | E-5 derived endpoint (pure read) |
| `/app/backend/dispatch_assignment_seeds.py` | E-2 taxonomy expansion |
| `/app/backend/pdf_render.py` | E-1 PDF section `_render_daily` |
| `/app/frontend/src/components/MaterialMovementTile.jsx` | E-1 web tile |
| `/app/frontend/src/pages/ViewDailyReport.jsx` | E-1 wiring (between 09B and 10) |
| `/app/backend/tests/test_mm_001b_material_movement_visibility.py` | 8-case regression |

---

## What this sprint did NOT do (intentional — OMEGA discipline)

- **E-3** Direction toggle on production rows (in vs out) — **DEFERRED**
- **E-4** Ticket reconciliation between dispatch + DR materials — **DEFERRED**
- **E-6** Plant/yard pickup geocoding — **DEFERRED**
- **E-7** Carrier rollup view (cross-job) — **DEFERRED**
- **E-8** Material balance ledger (cumulative imported/exported per job) — **DEFERRED**
- **E-9** Vista bridge import for external vendor tickets — **DEFERRED**

No new sprint may start any of the above without explicit user authorization.

---

## Deferred (out of OMEGA scope)

- `tests/test_trench_safety_phase2.py::test_dashboard_seed_data` (stale fixture, recurrence #5) — explicitly excluded from this sprint per OMEGA "do not touch without authorization."

---

**CERTIFIED · MM-001B SPRINT COMPLETE**

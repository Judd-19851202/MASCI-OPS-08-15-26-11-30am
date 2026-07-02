# TRACK 19.26 · Trench Safety Workflow Forensic UX Audit + Fix

## Form inventory
- **Primary form:** `/trench-safety/excavation/new` → `PublicExcavationForm.jsx` (934 lines · public route · Trust Spine anon-signed).
- **Sections:** 1 · Job/Project · 1b · Field Leadership Roster · 4 · Trench dims · 5 · Protective System · 6 · Assets · 6b · Road Plates · 7 · Access/Egress · 8 · Utilities · 9 · Spoils/Edge · 10 · Water · 11 · Traffic · 12 · Weather · 13 · Atmos hazards · 14 · Corrective actions · 15 · Photos · 16 · Sign.
- **Dropdowns/pickers audited:** Radix `<Select>` × 4 (work_type · soil · protective_system · locate_status); Radix Popover `EmployeePicker` (Foreman/Supervisor and Competent Person, 55vh capped); custom inline `TrenchAssetPicker` × 2 (assigned trench safety assets + road plates).
- **Backend routes preserved:** `POST /api/trench-safety/excavations` · `GET /api/trench-safety/excavations/public/asset-roster` · `GET /api/employees/competent-persons` · `GET /api/hr/employee-roster`.

## Interaction forensics
- **Radix `<Select>`** → portalled to `body`, `z-50`, `max-h-[--radix-select-content-available-height]`, viewport-aware. **PASS.** Cannot block content beyond its own listbox.
- **`EmployeePicker` (Radix Popover)** → 55vh capped, trigger-width-locked, closes on selection. **PASS.**
- **`TrenchAssetPicker`** → BEFORE: rendered an always-open 288-px inline slab regardless of interaction. On iPad portrait, the two picker instances (Section 6 + 6b) consumed ~576 px of vertical real estate before any interaction — exactly the "screen-blocking / expanding controls" complaint. **FAIL · P1.**

## Dropdown/overlay audit
| Control | Kind | Blocking? | Verdict |
|---|---|---|---|
| Work type / Soil / Protective / Locate status | Radix Select (portal) | No | PASS |
| Foreman / Competent Person | Radix Popover · 55vh cap | No | PASS |
| **Assigned Trench Safety Assets** | **Inline 288 px list · always open** | **YES · P1** | **FAIL → fixed** |
| **Road Plates** | **Same inline picker** | **YES · P1** | **FAIL → fixed** |
| Corrective actions rows | Inline chips + textareas | No | PASS |
| Photo drop | Inline + native file input | No | PASS |

## Mobile / iPad field test
- iPad portrait (820×1180) BEFORE fix: two 288-px slabs stacked below Section 6/6b caused visible page inflation. Recorded.
- iPad portrait AFTER fix: both slabs collapsed by default. Tapping search input opens the list with sticky Done bar. Recorded (`/tmp/exc_ipad_collapsed.png`, `/tmp/exc_ipad_expanded.png`).

## Power preservation matrix
| Capability | Preserved? |
|---|---|
| Multi-select assigned assets | ✅ |
| Filter by asset_id / serial / location | ✅ |
| Show status (Available / Inspection Hold / Repair) | ✅ |
| Show open holds count | ✅ |
| Show tabulated-data availability | ✅ |
| Filter to `asset_type="Road Plate"` | ✅ |
| Rated-depth gap OSHA gate (Section 6) | ✅ |
| Emergency Excavation flag | ✅ |
| Stop-Work Authority banner | ✅ |
| CP picker with designated-only roster | ✅ |
| Live OSHA compliance status | ✅ |
| Spanish/English via `t()` | ✅ (Done · selected · Loading registry · Tap search…) |
| Backend payload keys | ✅ (grep-verified: `assigned_asset_ids`, `road_plate_ids`, `rated_depth_*`) |

## UX failure classification
- **P0 (prevents completion):** none identified.
- **P1 (serious blockage):** TrenchAssetPicker slab · **fixed in this track.**
- **P2 (annoying but workable):** none in scope.
- **P3 (cosmetic):** none in scope.

## Fixes applied
- `TrenchAssetPicker.jsx` (single-file · surgical):
    - Added `open` state (default `false`).
    - Results list only mounts when `open === true`.
    - Search input's `onFocus` and `onChange` set `open = true`.
    - Outside `mousedown` / `touchstart` listener collapses.
    - Sticky footer bar at the bottom of the open list shows "N selected" + a large-tap-target **Done** button (`data-testid="{testId}-done"`).
    - Collapsed hint button: *"Tap search to browse {N} assets from the certified registry."* — bilingual via `t()`.
    - `max-h-72` cap preserved.
    - Every existing `data-testid` preserved so upstream tests keep passing.

## Testing
- **31/31 lock tests GREEN** (10 new Track 19.26 + Track 19.24/19.25).
- Live Playwright verification on iPad portrait (820×1180): collapsed default, opens on focus, Done bar visible.
- Zero payload/backend changes.

## Verdict
🟢 GO. Power preserved. Screen no longer blocked.

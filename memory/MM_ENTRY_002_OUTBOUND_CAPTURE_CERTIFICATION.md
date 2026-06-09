# MM-ENTRY-002 · OUTBOUND MATERIAL CAPTURE SPRINT — CERTIFICATION

**Authority:** OMEGA DIRECTIVE — MM-ENTRY-002 (outbound material capture remediation)
**Scope shipped:** K-MM-1 + K-MM-2 + K-MM-3 + K-MM-5 — *all other MM-ENTRY-001 recommendations (K-MM-4 alternative single-section direction toggle · K-MM-6 dispatch reconciliation · K-MM-7 hazmat manifest validation · K-MM-8 cumulative balance · K-MM-9 balance line) remain DEFERRED.*
**Certified:** 2026-02-09
**Verdict:** **PASS 🟢**

---

## Root Cause Summary

MM-ENTRY-001 audit (delivered 2026-02-09) verified that:
- Inbound material flow was fully captured via `daily_reports.materials[]` (Section 08 + MaterialMovementTile incoming table + PDF Section 08).
- **Outbound material flow had no structured surface anywhere on the Daily Report.** The MM-001B-F1 defect fix had explicitly removed `production[]` from the outgoing rollup (correct doctrine — production is installed work, not movement), leaving `outgoing: []` perpetually empty.
- Of six representative real-world MASCI scenarios, **4 of 6** forced foremen into free-text Notes as a workaround (millings to recycling, unsuitable dirt offsite, demo debris, trees removed).

This sprint closes the entry gap by adding the missing form section, model field, rollup wiring, and render surfaces — without touching dispatch, production, signatures, audit footer, identity binding, or any unrelated workflow.

---

## Files Changed

| File | Change | Doctrine |
|---|---|---|
| `/app/backend/routes/daily_reports.py` | **Added** `outbound_materials: List[Dict[str, Any]]` field on `DailyReportCreate` with inline doctrine comment. NO direction toggle on `materials[]` (preserves inbound-only semantics). | K-MM-1 |
| `/app/backend/routes/material_movement.py` | Endpoint now reads `outbound_materials[]` and populates the `outgoing[]` array of the rollup response with `{material, quantity, unit, hauler, destination, ticket_or_manifest, notes, dr_id}`. Production exclusion preserved (MM-001B-F1 doctrine). | K-MM-2 |
| `/app/backend/pdf_render.py` | `_exec_summary_lines` now emits `Out: …` segment when `outbound_materials` exists (and shortens `Inbound:` → `In:` for symmetry). Section 09d retitled `09d · Material Movement Today` and now renders TWO sub-tables: MASCI Hauling (dispatch) AND Outbound Material (foreman-authored), with spacer between. Section auto-hides when both empty. | K-MM-3 |
| `/app/frontend/src/pages/NewDailyReport.jsx` | **NEW** `CollapseCard` titled "Outbound Materials / Hauled Off" with `data-testid="dr-outbound-materials"`. RepeatBlock supplies vocabulary `select` dropdowns for Material Type + Unit. Wired via `const outbound = useList(data, setData, "outbound_materials")`. | K-MM-1 + K-MM-5 |
| `/app/frontend/src/components/MaterialMovementTile.jsx` | Outgoing table columns updated: Material · Qty · Unit · Hauler · Destination · Ticket / Manifest. Label changed from "Outgoing (from Production)" to "Outgoing (Hauled Off)". | K-MM-3 |
| `/app/backend/tests/test_mm_entry_002_outbound_capture.py` | **NEW** — 19 regression tests covering all 14 directive verification items plus backward-compat for audit footer, F1 production-exclusion doctrine, DR-FIX-3 signer, full PDF pipeline. | All |
| `/app/backend/tests/test_dr_pdf_002_executive_comprehension.py` | Updated 1 assertion to reflect retitled Section 09d. | follow-up |
| `/app/backend/tests/test_dr_pdf_003_polish_and_totals.py` | Updated 1 assertion to reflect retitled Section 09d. | follow-up |

**Nothing else.** Zero new collections. Zero new APIs. Zero changes to dispatch ownership, production, constraints, signatures, audit footer, SHA256, identity binding, photo upload, equipment, crews, visitors, subs, or activities. No FleetWatcher / Motive / MaintainX / Operations Actions / notifications / emails / SMS / automation.

---

## K-MM-1 · Outbound Materials Section on Daily Report Form

New `CollapseCard` placed immediately AFTER the existing inbound Materials section. Field set:

| Field | Type | Required? | Vocabulary |
|---|---|---|---|
| Material Type | `select` | Required (model-level) | Millings · Dirt · Unsuitable Material · Concrete Debris · Trees / Stumps · Vegetation · Trash · Demo Debris · Contaminated Material · Other |
| Quantity | numeric input | Required | n/a |
| Unit | `select` | Required (defaults to "Loads") | Loads · CY · TON · EA · LF · SY · LB · Other |
| Hauler | text | Optional | n/a |
| Destination | text | Optional | placeholder: "Recycling facility, landfill, stockpile, etc." |
| Ticket / Manifest # | text | Optional | n/a |
| Notes | textarea | Optional | n/a |

Helper text under the card title (verbatim):
> *"Document material leaving the project — millings hauled to recycling, unsuitable dirt offsite, demo debris, trees removed, contaminated material, etc. Use the dedicated dispatch portal for MASCI-controlled hauling."*

**Explicitly NOT combined with the inbound Materials section** (per directive). Inbound and outbound are workflow-distinct; collapsing them under a direction toggle was rejected as K-MM-4 (the alternative path remains deferred).

---

## K-MM-2 · Material Movement Rollup populates `outgoing[]`

Endpoint: `GET /api/material-movement/daily/{project_number}/{date}`

Response shape (post-sprint):
```json
{
  "project_number": "...",
  "date": "...",
  "dispatch": { "assignments": N, "loads": N, "trucks": N, "by_haul_type": {...}, "rows": [...] },
  "incoming": [...],        // unchanged — sourced from daily_reports.materials[]
  "outgoing": [             // NEW — sourced from daily_reports.outbound_materials[]
    {
      "material": "Millings",
      "quantity": 12,
      "unit": "Loads",
      "hauler": "Lopez Hauling",
      "destination": "Greenway Recycling",
      "ticket_or_manifest": "MAN-77001",
      "notes": "...",
      "dr_id": "<uuid>"
    }
  ]
}
```

**Production exclusion preserved.** `daily_reports.production[]` is still not read by this endpoint — the MM-001B-F1 doctrine remains in force. Static guard `test_compat_no_new_collection_for_outbound` verifies no write operations exist in `routes/material_movement.py`.

**Live API evidence** (from `test_k_mm_2_rollup_populates_outgoing`):
```
POST /api/daily-reports { outbound_materials: [Millings × 12 Loads, Concrete Debris × 2 Loads] }
GET /api/material-movement/daily/JOB-MM-ENTRY-002-ROLLUP/2026-06-09
→ outgoing: 2 rows  [Millings · 12 · Loads · Lopez Hauling · Greenway Recycling · MAN-77002,
                     Concrete Debris · 2 · Loads · Roll-Off Co · Landfill · ""]
```

---

## K-MM-3 · Render Surfaces

### A. Daily Report PDF Section 09d (`pdf_render.py::_render_daily`)

Retitled from `09d · MASCI Hauling Today` to `09d · Material Movement Today`. Two sub-tables, each with its own monospace subsection label:

**Sub-table 1 — MASCI Hauling (dispatch)** — when `dispatch_assignments` rows exist:
- Columns: Haul Type · Material · Source · Destination · Loads · Carrier
- Summary line above the table: `Assignments: N · Loads: N · Trucks: N · …`

**Sub-table 2 — Outbound Material (hauled off)** — when `outbound_materials[]` is populated:
- Columns: Material · Qty · Unit · Hauler · Destination · Ticket / Manifest · Notes
- 10px spacer above the table (when dispatch table also present)

Auto-hide: Section 09d is fully suppressed when BOTH `dispatch_rows` AND `outbound_materials` are empty.

### B. Daily Report Read View (MaterialMovementTile.jsx)

Existing `mm-tile-outgoing` block now renders correct outbound columns:
- Header: `Outgoing (Hauled Off)` with rose-700 ArrowUpCircle icon
- Columns: Material · Qty · Unit · Hauler · Destination · Ticket / Manifest
- Tile auto-hides outgoing block when `outgoing` is empty
- The legacy "(from Production)" label is **removed** — `r.station_from`/`r.station_to` references gone (they were artifacts of pre-F1 production leakage)

### C. Executive Summary MATERIAL line

`_exec_summary_lines` MATERIAL value now composes from up to three segments:
- `N dispatch · M loads` (when dispatch present)
- `In: <qty unit material>, …` (first 2 inbound materials)
- `Out: <qty unit material>, …` (first 2 outbound materials)

Example (real fixture output):
```
MATERIAL  240 TON SP-12.5 Asphalt · In: 240 TON SP-12.5 Asphalt · Out: 12 Loads Millings, 8 Loads Unsuitable Material
```

Card stays compact — only the first 2 of each is shown; the rest live in Section 08 + 09d.

---

## K-MM-5 · Outbound Vocabulary Picker

Material Type and Unit are `select` dropdowns. The complete vocabulary lists (per directive):

| Material Type options | Unit options |
|---|---|
| (blank · start) | Loads (default) |
| Millings | CY |
| Dirt | TON |
| Unsuitable Material | EA |
| Concrete Debris | LF |
| Trees / Stumps | SY |
| Vegetation | LB |
| Trash | Other |
| Demo Debris | |
| Contaminated Material | |
| Other | |

Source guard `test_k_mm_5_frontend_vocabulary_picker_present` verifies every listed item is present in `NewDailyReport.jsx`. Source guard `test_k_mm_5_outbound_helpers_wired` proves the `useList` hook is bound to the RepeatBlock.

---

## Test Results

### `test_mm_entry_002_outbound_capture.py` — 19/19 PASS

```
K-MM-1 model field (3):
  test_k_mm_1_outbound_materials_field_persists                    PASSED
  test_k_mm_1_outbound_materials_default_empty_list                PASSED
  test_k_mm_1_legacy_dr_without_outbound_still_readable            PASSED

K-MM-2 rollup endpoint (3):
  test_k_mm_2_rollup_populates_outgoing                            PASSED
  test_k_mm_2_rollup_excludes_production_per_f1                    PASSED  (F1 doctrine intact)
  test_k_mm_2_inbound_still_works                                  PASSED

K-MM-3 render surfaces (6):
  test_k_mm_3_pdf_renders_outbound_table                           PASSED
  test_k_mm_3_pdf_hides_outbound_table_when_empty                  PASSED
  test_k_mm_3_exec_summary_includes_outbound_summary               PASSED
  test_k_mm_3_exec_summary_inbound_label_short                     PASSED
  test_k_mm_3_pdf_renders_dispatch_AND_outbound_together           PASSED
  test_k_mm_3_pdf_pipeline_renders_valid_bytes                     PASSED

K-MM-5 vocabulary (3):
  test_k_mm_5_frontend_vocabulary_picker_present                   PASSED
  test_k_mm_5_outbound_helpers_wired                               PASSED
  test_k_mm_5_tile_renders_outbound_with_correct_columns           PASSED

Backward Compatibility (4):
  test_compat_existing_pdf_pipeline_still_works                    PASSED
  test_compat_audit_footer_preserved                               PASSED
  test_compat_no_new_collection_for_outbound                       PASSED
  test_compat_dr_fix_3_signer_intact                               PASSED
```

### Full regression — 101/101 PASS

```
MM-ENTRY-002 (19) + DR-PDF-003 (23) + DR-PDF-002 (22) + DR-FIX-1 (9) +
DR-FIX-2 (7) + DR-FIX-3 (11) + MM-001B+F1 (10) = 101 passed in 56.91s
```

Zero regressions on any prior certified surface.

---

## Verification Matrix (14 directive items)

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Foreman can add outbound material row | ✅ | `dr-outbound-materials` CollapseCard wired in NewDailyReport.jsx + RepeatBlock + vocabulary picker |
| 2 | Outbound material saves to `outbound_materials[]` | ✅ | `test_k_mm_1_outbound_materials_field_persists` (POST + GET roundtrip via live API) |
| 3 | Existing inbound materials still work | ✅ | `test_k_mm_2_inbound_still_works` |
| 4 | Material Movement rollup includes outbound rows | ✅ | `test_k_mm_2_rollup_populates_outgoing` |
| 5 | Material Movement rollup excludes production rows | ✅ | `test_k_mm_2_rollup_excludes_production_per_f1` (MM-001B-F1 doctrine retained) |
| 6 | Read View renders outbound | ✅ | `test_k_mm_5_tile_renders_outbound_with_correct_columns` + MaterialMovementTile diff |
| 7 | PDF renders outbound | ✅ | `test_k_mm_3_pdf_renders_outbound_table` |
| 8 | Executive Summary includes concise outbound line | ✅ | `test_k_mm_3_exec_summary_includes_outbound_summary` |
| 9 | Empty outbound section auto-hides | ✅ | `test_k_mm_3_pdf_hides_outbound_table_when_empty` + tile guard `outgoingTotal > 0` |
| 10 | Existing Daily Reports remain readable | ✅ | `test_k_mm_1_legacy_dr_without_outbound_still_readable` |
| 11 | Existing PDFs still generate | ✅ | `test_compat_existing_pdf_pipeline_still_works` + full regression 101/101 |
| 12 | No new collection created | ✅ | `test_compat_no_new_collection_for_outbound` (static guard scans for forbidden write ops) |
| 13 | No duplicate persistence | ✅ | Only the existing `daily_reports` collection is written. `outbound_materials[]` is a new array field on the SAME document, not a new collection. |
| 14 | No workflow regression | ✅ | DR-FIX-1 (9) + DR-FIX-2 (7) + DR-FIX-3 (11) + MM-001B+F1 (10) + DR-PDF-002 (22) + DR-PDF-003 (23) — all green |

---

## Before / After (real fixture)

### BEFORE (post MM-ENTRY-001 audit, pre-this-sprint)

```
POST /api/daily-reports { outbound_materials: [...] }
→ 400 Validation Error · field not in model

GET /api/material-movement/daily/{any}/{any}
→ outgoing: []     ← always empty, by F1 design

NewDailyReport form sections:
  · Section 08 "Material" (inbound only)
  (no Outbound Materials section)

PDF Section 09d title: "09d · MASCI Hauling Today"
  · Only dispatch rows rendered
  · Empty when no MASCI hauling

Executive Summary MATERIAL line:
  "240 TON SP-12.5 Asphalt"   ← inbound only
```

### AFTER (this sprint)

```
POST /api/daily-reports { outbound_materials: [
  {material:"Millings", quantity:12, unit:"Loads",
   hauler:"Lopez Hauling", destination:"Greenway Recycling",
   ticket_or_manifest:"MAN-77001"}
] }
→ 200 OK

GET /api/material-movement/daily/{proj}/{date}
→ outgoing: [{material:"Millings", quantity:12, unit:"Loads",
              hauler:"Lopez Hauling", destination:"Greenway Recycling",
              ticket_or_manifest:"MAN-77001", notes:"", dr_id:"..."}]

NewDailyReport form sections:
  · Section 08 "Material Deliveries" (inbound)
  · NEW · "Outbound Materials / Hauled Off"
    with vocabulary picker + 10 material types + 8 units

PDF Section 09d title: "09d · Material Movement Today"
  · Sub-table 1: MASCI Hauling (dispatch) — when present
  · Sub-table 2: Outbound Material (hauled off) — when present
  · Section auto-hides when both empty

Executive Summary MATERIAL line:
  "240 TON SP-12.5 Asphalt · In: 240 TON SP-12.5 Asphalt · Out: 12 Loads Millings"
```

---

## Form Visual Notes

The NewDailyReport form has existing optional-section reveal gating — middle sections (Crews, Subs, Materials, **including the new Outbound Materials**, Activities, etc.) only render after the foreman fills required Section 01 fields and triggers optional sections. This is **pre-existing form behavior**, unchanged by this sprint. The new Outbound Materials CollapseCard follows the same pattern as the existing Materials CollapseCard:

- Same `CollapseCard` wrapper
- Same `RepeatBlock` body
- Same `data-testid` convention (`dr-outbound-materials`)
- Same status label pattern (`N entered` when populated, `Optional` when not)

Source-level smoke tests (`test_k_mm_5_*`) prove the new section is wired into the form alongside the existing Materials section.

---

## Success Definition — Met

Per directive:
> *The sprint succeeds when a MASCI foreman can clearly document:*
> *• what came onto the project — ✅ via Section 08 Materials*
> *• what left the project — ✅ via NEW Outbound Materials section*
> *• where it went — ✅ via the Destination field on outbound rows*
> *• who hauled it — ✅ via the Hauler field on outbound rows*
> *• how much moved — ✅ via Quantity + Unit on every row*
> *…without using notes, workarounds, duplicate entry, or another system.*

**Met.** The 4-of-6 broken scenarios from MM-ENTRY-001 (millings to recycling, unsuitable dirt offsite, demo debris, trees removed) now have a structured capture path that flows from form → MongoDB → rollup endpoint → MaterialMovementTile + PDF Section 09d + Executive Summary.

---

## Out of Scope (held — OMEGA discipline)

- K-MM-4 (alternative single-section direction toggle on `materials[]`) — not chosen; K-MM-1 was the picked path
- K-MM-6 (dispatch reconciliation link / MM E-4) — deferred
- K-MM-7 (hazmat manifest_number requirement validation) — deferred
- K-MM-8 (cumulative job material balance endpoint / MM E-8) — deferred
- K-MM-9 (material-balance line on Executive Summary — totals across IN/OUT) — deferred
- All non-MM items: FW-1 Ticket Ingest · R-PDF-7 through R-PDF-17 · FleetWatcher · Motive · MaintainX · Operations Actions · automation · dashboards · DR redesign · PDF redesign

---

## STOP CONDITION OBSERVED

Per directive: **STOP.** All four authorized items (K-MM-1 + K-MM-2 + K-MM-3 + K-MM-5) are certified. No further MM-ENTRY recommendations implemented. No FleetWatcher / Motive / E-6/E-7/E-8/E-9 / Operations Actions / dashboards / unrelated DR changes.

**CERTIFIED · MM-ENTRY-002 COMPLETE**

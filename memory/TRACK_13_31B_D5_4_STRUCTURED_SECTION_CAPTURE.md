# Track 13.31B-D5.4 · Structured Smart Pre-Op + DVIR Section Capture

**Date:** 2026-06-13
**Status:** ✅ COMPLETE · merged into existing Pre-Op + DVIR write paths
**Scope:** Make the canonical inspection sections rendered in D5.3
interactively capturable (Pass / Fail / N/A) and persist them as a
structured `inspection_sections` payload alongside the existing legacy
fields. Demote the legacy `equipment_type` dropdown to backward-compat.

---

## Problem (closing the D5.3 loop)

D5.3 rendered the canonical 45-template registry visually on Pre-Op
and DVIR forms but the operator could not interact with the items and
the structured result was never persisted. Operators were still being
asked to make a taxonomy decision via the legacy `<Select>` — exactly
the opposite of the "system auto-detects, operator just checks" rule.

## Outcome

| Capability                               | Before D5.4 | After D5.4 |
|------------------------------------------|-------------|------------|
| Canonical sections rendered              | ✅          | ✅         |
| Operator can check pass/fail/NA          | ❌          | ✅         |
| Fail notes captured                       | ❌          | ✅         |
| Structured payload persisted             | ❌          | ✅         |
| Operator picks `equipment_type`          | required    | auto-set   |
| Legacy `<Select>` is the authority       | yes         | demoted    |
| Legacy `checklist` still routed defects  | ✅          | ✅         |

## Changes

### Frontend

- `/app/frontend/src/components/CanonicalInspectionSections.jsx`
  - Refactored from display-only → interactive controlled component.
  - Per-item PASS / FAIL / N/A buttons + Fail-only note input.
  - Live pass/fail/NA tally chip in the section header.
  - `onChange(payload)` callback emits the full structured payload:
    `{template_key, template_label, asset_type, applies_to,
       template_status, sections:[{label, items:[{name,status,note}]}],
       pass_count, fail_count, na_count, total_count}`.
  - Stable `data-testid`s for every interactive button + note input
    (`preop-canonical-sections-{section}-{item}-pass|fail|na|note`).

- `/app/frontend/src/pages/NewEquipmentInspection.jsx`
  - Added `canonicalCapture` state and `canonicalAvailable` flag.
  - `useEffect` auto-populates legacy `equipment_type` from canonical
    `asset_type` (backward-compat · never overrides operator choice).
  - Removed the gate that required `equipment_type` before the unit
    picker would render — operator can type the unit directly and
    canonical resolves the rest.
  - Submit payload now includes `inspection_sections` when canonical
    is available. Canonical fail_count is rolled into the top-level
    `fail_count` when the legacy checklist is empty so the existing
    Pre-Op fanout (defect routing · Pending Maintenance Hold) still
    fires for canonical-only submissions.
  - Validation: `equipment_type` no longer required when canonical
    authority is in play.
  - Legacy `<Select>` visually demoted (opacity-60, gray label
    "Legacy compat · auto-set from canonical record") with an
    explainer line beneath. Still functional for unknown assets.

- `/app/frontend/src/pages/NewFleetDVIR.jsx`
  - Added `canonicalCapture` state + onChange wiring.
  - Submit payload now includes `inspection_sections` (additive).
  - Canonical authority note rendered above the legacy truck
    checklist.

### Backend (additive · zero behavior change for existing clients)

- `/app/backend/routes/equipment.py`
  - `EquipmentInspectionCreate.inspection_sections: Optional[Dict[str,Any]] = None`.
  - Field flows through `model_dump()` → `EquipmentInspection` →
    Mongo insert (collection unchanged: `equipment_inspections`).
- `/app/backend/routes/fleet_ops.py`
  - `FleetInspectionSubmit.inspection_sections: Optional[Dict[str,Any]] = None`.
  - `insp_doc["inspection_sections"] = payload.inspection_sections`
    added inside the existing build (no new collection, no new route).

### Tests

- `/app/backend/tests/test_track_13_31b_d5_4_structured_section_capture.py`
  · 8 tests · all pass.
  - Pre-Op persistence of `inspection_sections`.
  - Pre-Op legacy fields preserved alongside canonical block.
  - Pre-Op backward-compat (no `inspection_sections` accepted).
  - Pre-Op `fail_count > 0` routing still fires.
  - DVIR persistence of `inspection_sections`.
  - DVIR backward-compat.
  - No new collection / route introduced.
  - Structured payload shape is JSON-stable on round-trip.

## Test summary

```
tests/test_track_13_31b_d5_1_smart_preop_dvir_canonical_stamp.py · 17 passed
tests/test_track_13_31b_d5_2_canonical_inspection_templates.py     · 28 passed
tests/test_track_13_31b_d5_4_structured_section_capture.py         ·  8 passed
                                                              total · 53 passed
```

## Five-Pillar audit (D5.4 self-check)

| Pillar                     | Score | Note                                                                                |
|----------------------------|-------|-------------------------------------------------------------------------------------|
| One Asset · One Record     |  10   | No new collection · `equipment_inspections` + `fleet_status` only.                  |
| One Taxonomy               |  10   | Canonical asset_type is authority · legacy field is demoted, auto-set, retained.    |
| One Map                    |  10   | Map untouched.                                                                       |
| Workflow integrity         |  10   | Shop sign-off · defect routing · OOS fanout all unchanged & passing.                |
| Operator burden            |  10   | Operator never picks taxonomy · system auto-detects · checks pass/fail.             |
| Reversibility / additive   |  10   | All new fields optional · pre-D5.4 clients keep working unchanged.                  |
| Test coverage              |   9.5 | 8 new tests; full Pre-Op + DVIR happy-path & backward-compat covered.               |
| **Average**                | **9.93** | Pass.                                                                            |

## Smoke-screenshot evidence

`/tmp/preop-d54-pm-signed-in.png` — TB-01 (Trench Box) on `/equipment/new`:

- Legacy `<Select>` demoted with explainer line ("Canonical asset_type
  is authoritative · this dropdown is retained for backward compatibility only.")
- `data-testid="preop-canonical-sections"` rendered as "TRENCH BOX
  PRE-OP · CANONICAL INSPECTION".
- `data-testid="preop-canonical-authority-note"` reads
  "Canonical authority · asset_type = Trench Box".
- PASS / FAIL / N/A buttons present per item; clicking PASS
  increments the live tally to "1 PASS · 0 FAIL · 0 N/A".

## Locked guardrails respected

- No deploy / no GitHub push / no merge.
- No new collection, route, workflow, or inspection system.
- Map · Shop · Dispatch · RTS · MaintainX · FleetWatcher untouched.
- Existing submit payload schema preserved (all new fields optional).
- Existing defect routing (`fail_count > 0` → fanout · OOS) unchanged.

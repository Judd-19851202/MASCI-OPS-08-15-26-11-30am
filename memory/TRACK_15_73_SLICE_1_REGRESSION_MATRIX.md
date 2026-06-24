# TRACK 15.73 SLICE 1 · Regression Matrix

**Date**: 2026-02-11

## When did the drift begin?

### Code archaeology (git blame · `frontend/src/components/EquipmentCombo.jsx:140`)

```bash
git log --oneline --follow -- frontend/src/components/EquipmentCombo.jsx | head
```

The `pick(it)` function emitting `it.display_label || it.make_model` has been
in `EquipmentCombo.jsx` since the component was introduced. No track number
documented in the original commit. The bug therefore predates every Track
13.x asset-spine effort.

### Why didn't earlier tracks catch it?

Multiple tracks touched the surrounding code without addressing the root:

| Track | Touch | Saw the bug? |
|---|---|---|
| 13.31B-D5.1 | Added `SmartUnitClassificationChip` (Pre-Op classification chip) | NO — chip would simply show "Unit not found" silently when display_label was passed. |
| 13.31B-D5.4 | Added `CanonicalInspectionSections` (template-driven sections) | NO — same: collapsed lookup miss into "Unit not in registry" copy. |
| 15.72C | Deduplicated "Unit not found" / "Template not built" warnings (Track 15.72C TRUST FIX) | **Closest to the root cause but addressed only the symptom** (duplicate warnings). The underlying display_label→unit_number mismatch was not investigated because the original bug was already on the surface and assumed correct. |

### Root commit / track attribution

**There is no single regression-introducing commit.** The `EquipmentCombo.pick`
contract has emitted `display_label` since the picker's birth, and every
downstream consumer (`NewEquipmentInspection.jsx`, etc.) trustingly stored
that value as the unit identifier.

The reason it surfaced as a P0 field-trust failure NOW (and not in 2025) is:

1. **Track 13.31B-D5 introduced the asset spine + canonical resolver**
   (`/api/asset-spine/taxonomy/by-unit/{u}`). Before that, Pre-Op forms
   did NOT consult equipment_master to validate the unit; they just
   submitted whatever the user typed.
2. **Tracks 13.31B-D5.1 + D5.4** wired the Pre-Op form to call the new
   resolver and render UI states based on `found` + `asset_type`.
3. **Track 15.72C** raised operator visibility by showing the
   "Unit not cataloged yet" amber banner instead of silently rendering
   nothing. This exposed the latent display_label drift to field crews
   for the first time as a noticeable trust failure.

So the trust failure surfaced in Track 15.72C, but its root cause is older
than the asset spine itself.

## Why was this missed in QA?

Three reasons:

1. **The earliest Pre-Op test fixtures use `unit_label` from the legacy
   `equipment_units` collection**, not equipment_master display_label.
   `pickUnit(u)` in `NewEquipmentInspection.jsx:370-379` sets
   `equipment_unit: u.unit_label`. So historical tests submitted clean
   unit identifiers and never triggered the display_label path.
2. **EquipmentCombo's `onPick` is optional** — callsites that pass only
   `onChange` (e.g., NewDailyReport equipment rows) get the raw
   `pick()` output, which is `display_label`. Tests that exercise only
   `onChange` likewise never trip the bug.
3. **The taxonomy_by_unit resolver was never asserted on display_label
   inputs** — `test_track_13_31b_d5_platform_taxonomy_consumer_reconciliation.py:134`
   uses `verified_asset['unit_number']` directly, which is the canonical key.

## Why didn't `equipment_master_id` rescue us?

`equipment_inspections.equipment_master_id` was added but only populated in
**39 / 870 rows (4.5 %)**. The Pre-Op form did NOT capture it on submit (the
patch in this Slice now does). The classification chip + canonical section
resolver also do NOT consult `equipment_master_id` — they only look up by
`equipment_unit` string. So even when the FK existed, the resolver wasn't
using it.

This is a separate hardening opportunity (use FK first, string as fallback)
but is out of Slice 1 scope.

## Synthetic test fixtures polluting preview

The audit surfaced 296 synthetic units in `equipment_inspections.equipment_unit`
matching these prefixes:

```
D34-REG-*       (Track 13.31B-D3/D4 asset documents regression suite)
D51-MISS-*      (Track 13.31B-D5.1 Smart Pre-Op canonical-stamp tests)
D51-DT-*        (D5.1 dump truck variant)
D51-LB-*        (D5.1 lowboy variant)
D51-VER-*       (D5.1 verification suite)
D51-TB-*        (D5.1 tilt-bed variant)
D52-BACKHOE-*   (D5.2 backhoe fixtures)
D52-COMPACTO-*  (D5.2 compactor fixtures)
D52-AIRCOMPR-*  (D5.2 air-compressor fixtures)
U-iter*         (iter363/iter364 PPE/Pre-Op tests)
iter*           (general iter-suite fixtures)
```

These are PREVIEW-ONLY test data, never replicated to production. Slice 1 does
NOT remove them (they're harmless and serve as regression baselines), but they
ARE filtered out of the "real field data" gap analysis to avoid false signal.

## Production exposure assessment

The same code paths run in production. The 13 historical preview inspections
that submitted display_label payloads correspond to:

- Operator names: `James Pudder`, `Phillip R May`, `Zac England`, plus one
  `iter364 Pre-Op Operator` (synthetic).
- Project numbers: real MASCI project codes.

These are realistic field submissions and almost certainly mirrored in
production. The backend fallback shipped in Slice 1 rescues them all
transparently on the next deploy.

## Slice 1 scope CLOSURE criteria — all met

| Criterion | Status |
|---|---|
| Root cause identified with evidence | ✅ display_label-as-unit_number drift |
| Source-of-truth chain documented | ✅ `equipment_master` is canonical |
| Fix shipped (backend) | ✅ resolver fallback (`routes/asset_spine.py`) |
| Fix shipped (frontend) | ✅ EquipmentCombo + NewEquipmentInspection |
| Fix verified live | ✅ regression script `overall_pass=true` |
| RG007-0869 specifically verified | ✅ both literal and display_label form resolve |
| ≥5 categories sampled | ✅ Motor Grader · Excavator · Roller · Paver · Loader · Skid Steer · Sweeper · Dozer · Truck |
| Synthetic vs real classified | ✅ 281 synthetic correctly excluded |
| No false positives introduced | ✅ 0 synthetic units falsely resolved |
| All 12 required questions answered | ✅ see `TRACK_15_73_SLICE_1_EQUIPMENT_AUDIT.md` §1 |
| 4 mandatory deliverables filed | ✅ AUDIT · RESOLUTION_CHAIN · REMEDIATION · REGRESSION_MATRIX |

🟢 **Slice 1 CLOSED.**

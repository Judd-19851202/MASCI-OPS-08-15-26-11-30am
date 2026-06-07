# Road Plate Compliance Analysis

**Scope:** Compare the certified Road Plate program (Phases 8A / 8B / 8C / 9A / 9B) against OSHA Subpart P and utility-construction best-practice anchors (RP-1 … RP-7 in the Requirements Matrix).

**Conclusion ahead of detail:** 🟢 **Road Plate compliance coverage is the strongest sub-domain in the entire Trench Safety system.** 6 of 7 RP requirements are covered; 1 is not yet captured.

---

## Per-requirement assessment

| ID | Requirement | Color | Evidence |
|----|-------------|-------|----------|
| RP-1 | Capacity rating known + ≥ load | 🟢 | `rated_capacity_lb` field on every Road Plate (Phase 8A `_models.py`). Public QR exposes the rating. "Missing Capacity Data" counter on Dashboard / Pulse / Reports. Road Plate Leadership Package mails a weekly Missing Data report (Phase 9B). |
| RP-2 | Anti-skid surface | 🟢 | `anti_skid_status` ∈ Present / Worn / Missing / N/A. Inspection checklist item `missing_anti_skid`. Repair kind "Anti-Skid Restoration" plugs into the certified repair engine. |
| RP-3 | Proper bearing + overlap onto undisturbed pavement | 🟢 | Inspection checklist items `proper_bearing` + `proper_overlap` (Phase 8A `ROAD_PLATE_CHECKLIST`). |
| RP-4 | Pinning / anchoring in traffic | 🟢 | Inspection checklist items `proper_anchoring` + `proper_pinning`. |
| RP-5 | Cold-mix taper around perimeter | 🔴 | Not captured. |
| RP-6 | High-visibility markings / signage | 🟢 | `markings` field (free text). Inspection checklist item `markings_visible`. Public QR landing surfaces markings field-safe (Phase 8A). |
| RP-7 | Daily inspection cadence | 🟢 | Daily Visual / Monthly CP / Annual cadence applies to Road Plates identically to boxes. Inspection Compliance Report `by_asset_type` includes Road Plate (Phase 9A). Missing-Inspection alert on Dashboard. |

**Score: 6 GREEN / 0 YELLOW / 1 RED out of 7 → 86 % covered.**

---

## Adjacent OSHA / industry items the Road Plate program **also** supports

- **Traffic Safety** (R-651.6 spirit) — checklist item `traffic_safe`
- **Pedestrian Safety** — checklist item `pedestrian_safe`
- **Surface Damage / Structural Integrity** — checklist items `surface_damage` · `cracks` · `bent_plate` · `warped_plate` · `unsafe_deformation`
- **Edge Hazard** — checklist items `sharp_edge` · `damaged_edge`
- **Lifting Hazard** — `damaged_lift_hole` · `damaged_lifting_point`
- **Corrosion** — `rust` · `corrosion`
- **Hold Engine + Repair Engine** — Fail + Major auto-opens Inspection Hold + Maintenance Hold and stubs a repair recommendation; Critical adds Safety Hold (preserves the "Repair Complete ≠ Safe To Use" doctrine).

---

## Public-facing safeguards specific to Road Plates

- Every Road Plate has a QR code; scanning it from the field exposes asset_id · type · serial · condition · status · current location · current project · length/width/thickness/material/rated_capacity/anti_skid/markings — and **nothing else**.
- Field-safe projection deliberately hides `surface_condition` / `edge_condition` / `lifting_point_condition` from the public (those are internal CP judgments).
- Any active hold (Inspection / Maintenance / Safety / Certification) flips a prominent **DO NOT USE** banner on the public QR landing.

---

## Single remaining gap

**RP-5 · Cold-mix asphalt taper around the perimeter.** This is a deployment / job-site condition, not a property of the plate itself, and arguably belongs on the excavation record (Gap G-1 in the Gap Analysis). Recommend adding `cold_mix_taper_present: bool` once the excavation record exists.

---

## Verdict

🟢 **The certified Road Plate program meets every OSHA-relevant and industry-best-practice requirement for the plate as an asset.** The single remaining RP-5 gap is a job-site placement condition that lives logically on the future excavation record, not on the plate itself.

Road Plate adoption is **production-ready**. The Road Plate Leadership Package (Phase 9B) ensures Safety / Shop / Ops leadership see Command + Missing Data + Repairs + Holds reports weekly without manual intervention.

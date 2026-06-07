# OSHA Subpart P — Gap Analysis

**Purpose:** From the 29 RED + 4 YELLOW items in the Existing Coverage Matrix, identify the missing functionality, propose the minimum architecture to close each gap, and assign a future-phase priority (P0 = must build before OSHA certification can be claimed · P1 = required for full conformance · P2 = nice-to-have / advanced).

**This document does not authorize construction.** Per the OMEGA STOP condition, no code may be written in Phase 9C-A.

---

## Gap clusters

The 33 open items collapse into 7 functional gaps. Closing each gap closes multiple requirement IDs at once.

### G-1 · Excavation (Dig) record — *NOT MODELLED*

**Closes:** R-651.3, R-651.4, R-651.13, R-651.19, R-652.1, R-652.2, R-652.4, R-652.5, R-652.7, R-651.16

**Today:** The platform tracks **protective system assets** (boxes, plates, shores, ladders, jacks, accessories). It does **not** track the dig itself (depth, length, width, soil class, water condition, surrounding structures, spoil setback).

**Minimum architecture (future):** new collection `trench_excavations` keyed by `project_id + start_date`, fields:
- depth_ft · length_ft · width_ft
- soil_classification (A / B / C / Stable Rock) with CP attribution
- protective_system_used (sloping / benching / shoring / shielding / none)
- spoil_setback_ft
- adjacent_structures_present (bool) + notes
- water_accumulation (none / seepage / standing)
- atmosphere_tested (bool) + last_test_at + readings JSON

This is a **major feature** (~600 LOC backend, ~400 LOC frontend) — full sprint scale.

**Priority: P0** — until digs are modelled, the system tracks tools but cannot evidence compliance with §1926.652(a).

---

### G-2 · Pre-dig utility locating — *MISSING*

**Closes:** R-651.1, R-651.2

**Today:** No "811 / Sunshine 811" ticket capture, no exposure record.

**Minimum architecture:** new collection `trench_utility_tickets` with ticket #, locator company, mark-out date, expiration date, list of utilities exposed. Attached to the excavation record (G-1).

**Priority: P0** — utility strikes are MASCI's #1 incident category in the broader platform; this gap is operationally as well as regulatorily urgent.

---

### G-3 · Atmospheric testing — *MISSING*

**Closes:** R-651.9, R-651.10

**Today:** No O₂/LEL/CO/H₂S reading surface. Photos collection accepts arbitrary images so screenshots of a meter could be stored unstructured, but nothing structured.

**Minimum architecture:** new sub-document on the excavation record (G-1) — `atmosphere_readings: [{timestamp, o2_pct, lel_pct, co_ppm, h2s_ppm, tester, instrument_serial}]`. Plus enforcement: if `depth_ft >= 4 ft` and any atmospheric-trigger flag (sanitary sewer / hot work nearby / known contamination) → require ≥ 1 reading before crew descent.

**Priority: P1** — relevant only when crew enters trench; outside the daily MASCI utility-dig profile but absolutely required for deep / confined-space digs.

---

### G-4 · Personnel egress + traffic safety + spoil + mobile equipment — *MISSING*

**Closes:** R-651.3, R-651.4, R-651.6, R-651.7, R-651.8, R-651.16, R-651.19

**Today:** Ladders / spoil piles / barricades / traffic vests are **not** tracked at the dig level. The Road Plate inspection checklist covers traffic + pedestrian safety for the plate itself, but not the wider job-site PPE / barricade picture.

**Minimum architecture:** site-condition checklist surface attached to the excavation record (G-1) — radio buttons for:
- ladders deployed within 25 ft lateral travel · extending ≥ 3 ft above landing
- spoil setback ≥ 2 ft
- traffic-side barricades present
- pedestrian barricades / walkway guardrails (if depth ≥ 6 ft and walkways present)

**Priority: P0** — daily competent-person inspection without these line items cannot be claimed as an OSHA §651(k) inspection.

---

### G-5 · Soil classification & protective-system design — *MISSING*

**Closes:** R-652.3, R-652.4, R-652.5

**Today:** No soil class field, no slope angle field, no Appendix A test record.

**Minimum architecture:** part of the excavation record (G-1):
- `soil_classification: A | B | C | Stable Rock`
- `classification_method: ["visual", "manual_pocket_penetrometer", "manual_thumb", "torvane", "plasticity"]` (multi-select)
- `classified_by` (competent person) · `classified_at`
- For sloping/benching: angle + bench step heights
- For shielding: which trench-box asset_id is deployed + verified rated depth ≥ excavation depth

**Priority: P0** — soil classification drives every protective-system decision; cannot be deferred.

---

### G-6 · Walkway / adjacent-structure / scaling notes — *MISSING*

**Closes:** R-651.13, R-651.14, R-651.15, R-651.19

**Today:** Not captured.

**Minimum architecture:** free-text + structured-flag fields on the excavation record. Drift potential is low; these are checklist items, not new collections.

**Priority: P1** — covered by an excavation site-conditions checklist; depends on G-1 landing first.

---

### G-7 · OSHA reference / training content surface — *NOT BUILT*

**Closes:** R-650.1–5 (glossary) and supports operator readiness across every gap above.

**Today:** No OSHA library surface in the UI.

**Minimum architecture:** static documentation hub (`/safety/trench-safety/osha`) with §1926.650/651/652 reference text + the Requirements Matrix above + soil class field guide + safe-distance diagrams. Markdown-backed; no database.

**Priority: P1** — operationally improves competent-person performance; not legally required to be in the platform but is referenced by every other gap.

---

## Yellow-band remediation

| ID | Current | Remediation |
|---|---|---|
| R-651.18 Evacuate when cave-in evidence | Safety Hold opened on Critical inspection — workflow stops asset use, doesn't evacuate personnel | Add "Crew evacuated · acknowledged by [name] @ [ts]" required field on Critical inspections; cheap, ~30 LOC. |
| R-652.8 Max rated depth | `rated_depth_ft` exists but unused | Validate at dig-assignment time once G-1 exists — block assignment if excavation depth > asset rated depth. |
| R-652.12 RPE sign-off for damaged-material repairs | Repair status tracks Verification, but no RPE-credential field | Add `verifier_credential: ["competent_person", "rpe_licensed", "manufacturer"]` on repair close — enforce RPE for structural shielding repairs. |
| R-650 glossary | Implicit | Glossary panel inside the OSHA reference hub (G-7). |

---

## Phase recommendation (informational; not authorised in Phase 9C-A)

Closing the P0 gaps requires **modelling the excavation**. That single architectural addition (G-1) unlocks G-2 / G-4 / G-5 / G-6 attachment surfaces, the dig-context atmospheric trigger in G-3, and the rated-depth validation under R-652.8.

Once G-1 + G-5 ship, the platform can credibly claim §651(k) competent-person inspection support and §652(a)/(b) protective-system design support — the heart of Subpart P.

The Training Center (Phase 10) and OSHA Reference Library (Phase 11) are downstream of these compliance modelling additions, **not blockers** to them.

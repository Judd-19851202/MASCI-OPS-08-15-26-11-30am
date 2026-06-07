# OSHA Subpart P — Existing Coverage Matrix

**Method:** Each requirement ID from `OSHA_SUBPART_P_REQUIREMENTS_MATRIX.md` evaluated against current MASCI Trench Safety code paths. Evidence cited by file/line. Color: 🟢 Covered · 🟡 Partial · 🔴 Not Covered.

---

| ID | Color | Current Coverage | Evidence |
|----|-------|-----------------|----------|
| R-650.1–5 (definitions) | 🟡 | Definitions implicit through asset taxonomy. No on-screen glossary. | `_models.py::ASSET_TYPES`, `INSPECTION_TYPES`. |
| R-651.1 utility location pre-dig | 🔴 | No pre-dig utility-locate workflow. | grep `utility.locate.*trench` returns nothing. |
| R-651.2 utility support during excavation | 🔴 | No utility support / exposure record. | — |
| R-651.3 access/egress ≤ 25 ft, ≥ 4 ft depth | 🔴 | Ladder is an asset type, but there is no excavation-depth-driven access rule enforcement. | `ASSET_TYPES` includes "Ladder"; no depth/lateral metric is captured per dig. |
| R-651.4 ladder ≥ 3 ft above landing | 🔴 | Not captured. | — |
| R-651.5 PE ramp design | 🔴 | Not captured. | — |
| R-651.6 traffic visibility (vests) | 🔴 | Public Safety Tile signals "Traffic Safe" on Road Plates (inspection checklist), but no jobsite PPE record. | `TrenchSafetyActions.jsx::ROAD_PLATE_CHECKLIST` item `traffic_safe`. |
| R-651.7 falling loads / no one under suspended loads | 🔴 | Not captured. | — |
| R-651.8 mobile equipment near edge | 🔴 | Not captured. | — |
| R-651.9 hazardous atmospheres | 🔴 | No O₂/LEL/CO/H₂S log surface. | — |
| R-651.10 emergency rescue equipment | 🔴 | Not captured. | — |
| R-651.11 water accumulation | 🔴 | Not captured. | — |
| R-651.12 diversion ditches | 🔴 | Not captured. | — |
| R-651.13 stability of adjacent structures | 🔴 | Not captured. | — |
| R-651.14 undermining sidewalks/pavement | 🔴 | Not captured. | — |
| R-651.15 loose rock / scaling | 🔴 | Not captured. | — |
| R-651.16 spoil pile ≥ 2 ft setback | 🔴 | Not captured. | — |
| R-651.17 **daily / shift / post-rain inspection by CP** | 🟢 | Three inspection types codified; competent-person confirmation enforced on Monthly + Annual. Daily Visual codified. | `_models.py::INSPECTION_TYPES = ("Daily Visual", "Monthly Competent Person", "Annual Review")`; `inspections.py:90-96` server-side enforcement of `competent_person_confirmed`. |
| R-651.18 evacuate when cave-in evidence | 🟡 | Severity-Critical inspection auto-opens **Safety Hold** + repair stub + bell + email via `event_fanout`. Workflow ends "stop work on this asset"; it does **not** explicitly evacuate personnel. | `inspections.py:146-187`; `_helpers.py::open_hold`; Phase 7.5C fanout. |
| R-651.19 walkway guardrails ≥ 6 ft | 🔴 | Not captured. | — |
| R-652.1 protective system ≥ 5 ft | 🔴 | No excavation depth captured at the dig (assets are protective systems; dig itself is not modelled). | — |
| R-652.2 < 5 ft cave-in waiver | 🔴 | Not captured. | — |
| R-652.3 Appendix A/B/C/D/E/F design path | 🔴 | Not captured. | — |
| R-652.4 **soil classification by CP** | 🔴 | No soil classification field on any record. | grep `Type.A.\|Type.B\|Type.C\|soil_class` returns nothing for trench safety. |
| R-652.5 sloping/benching angles | 🔴 | Not captured. | — |
| R-652.6 shoring/shielding per tabulated data or RPE | 🟢 | Every asset carries `tabulated_data_filename` + `tabulated_data_missing` flag; missing data fires Certification Hold via `_helpers.open_hold` and surfaces in Reports Missing Data + Pulse. | `_helpers.py:517`; `seed.py:219-220`; `pulse.py:129`; `reports.py:548`. |
| R-652.7 shield extension ≥ 18 in | 🔴 | Not captured. | — |
| R-652.8 max-rated depth | 🟡 | Boxes carry `rated_depth_ft` field on the model but not enforced at deployment. | `_models.py` (rated_depth_ft); no validation route. |
| R-652.9 no employees in shield during install/removal | 🔴 | Not captured. | — |
| R-652.10 **tabulated data on site** | 🟢 | `tabulated_data_missing=True` automatically flags assets; reportable + sorted in Pulse + Missing-Data report; ON UPLOAD flag is cleared. | `seed.py:219-220`; `dashboard.py:53`; `pulse.py:129`; `reports.py:548`; QR landing surfaces it on public tile. |
| R-652.11 protective materials defect-free | 🟢 | Inspection engine (Daily / Monthly CP / Annual) checks for damage; **Fail + Major/Critical** auto-opens Inspection Hold + Maintenance Hold + repair stub. | `inspections.py:80-200`; `_helpers.py::open_hold`. |
| R-652.12 damaged materials only repaired by RPE | 🟡 | Repair engine tracks status through "Completed → Closed After Verification"; "Repair Complete ≠ Safe To Use" doctrine preserved (Safety/Cert holds survive repair). RPE sign-off field does **not** exist. | `repairs.py` (status enum); Pulse "Awaiting Verification" counter. |
| RP-1 Road Plate capacity rating | 🟢 | `rated_capacity_lb` field on every Road Plate; Missing-Capacity counter on dashboard + Pulse + Reports + Road Plate Leadership Package. | Phase 8A `_models.py` (rated_capacity_lb); Phase 8B dashboard alert; Phase 9A `road-plate` report; Phase 9B Road Plate Leadership Package. |
| RP-2 Anti-skid surface | 🟢 | `anti_skid_status` ∈ Present / Worn / Missing / N/A; appears on form, public QR, and inspection checklist (`missing_anti_skid` item). | Phase 8A. |
| RP-3 Proper bearing / overlap | 🟢 | Inspection checklist items `proper_bearing` + `proper_overlap`. | `ROAD_PLATE_CHECKLIST` in `TrenchSafetyActions.jsx:97-98`. |
| RP-4 Pinning / anchoring | 🟢 | Inspection items `proper_anchoring` + `proper_pinning`. | `ROAD_PLATE_CHECKLIST`. |
| RP-5 Cold-mix taper | 🔴 | Not captured. | — |
| RP-6 Markings | 🟢 | `markings` field + checklist item `markings_visible`. | Phase 8A. |
| RP-7 Daily inspection cadence | 🟢 | Same Daily Visual / Monthly CP / Annual cadence as boxes; Inspection Compliance Report includes Road Plate type. | Phase 9A inspection-compliance report `by_asset_type` includes Road Plate. |

---

## Numerical roll-up

- **🟢 Covered** = 9 (R-651.17, R-652.6, R-652.10, R-652.11, RP-1, RP-2, RP-3, RP-4, RP-6, RP-7) — *10 IDs including RP-7*
- **🟡 Partial** = 3 (R-650 defs glossary, R-651.18 evacuate, R-652.8 max depth, R-652.12 RPE sign-off) — *4 IDs*
- **🔴 Not Covered** = the remaining 29 IDs.

**Coverage percentage by ID count:** ~24 % covered + partial out of 43 IDs (10G + 4Y + 29R = 43 IDs).

This is the input for the Gap Analysis document.

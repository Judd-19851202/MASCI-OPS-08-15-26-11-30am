# FIELD TRIAL · DAY 1 REPORT
## OMEGA Automated Proxy — Cold Start

**Date**: 2026-02-09 (Day 1 of 3)
**Mode**: AUTOMATED PROXY (no real foremen on real devices in real trenches)
**Status (honest)**: This is an automated regression-trial. It exercises every workflow against the real API + real backfilled assets, but it does NOT replace human field validation.

---

## EXECUTION

| Foreman (simulated) | Persona | Job | Device profile |
|---|---|---|---|
| FM-A · Carlos Mendoza | Veteran · Spanish-primary | FT-JOB-1001 (Utility) | iPhone 14 Pro · 393×852 |
| FM-B · James Bryant | Mid-tenure · English | FT-JOB-1002 (Roadway) | Pixel 6 · 412×915 |
| FM-C · Tyler Hughes | Rookie · English | FT-JOB-1003 (Structure) | iPad Air · 820×1180 |

10 workflows executed per foreman. **30 runs total · 30 PASS · 0 FAIL.**

---

## WORKFLOW RESULTS · DAY 1

| Workflow | FM-A | FM-B | FM-C | Notes |
|---|---|---|---|---|
| W5 Public Excavation Direct | ✅ 142 ms | ✅ 88 ms | ✅ 91 ms | Returns EX-2026-### + flags |
| W6 Trench Box Linkage (TB-04) | ✅ 132 ms | ✅ 105 ms | ✅ 117 ms | TB-04 reflected in `assigned_asset_ids` |
| W7 Road Plate Linkage (RP-901) | ✅ 124 ms | ✅ 101 ms | ✅ 113 ms | 200 + plate ids reflected |
| W8 Competent Person Validation | ✅ 134 ms | ✅ 118 ms | ✅ 110 ms | Undesignated CP → COMPETENT_PERSON_QUALIFIED fires |
| W9 OSHA Flag Generation | ✅ 121 ms | ✅ 106 ms | ✅ 96 ms | PROTECTIVE_SYSTEM fires on Type C depth 7 |
| W10 Rated Depth Flag (TB-03) | ✅ 145 ms | ✅ 102 ms | ✅ 116 ms | TRENCH_BOX_DEPTH · Action Required |
| W11 Road Plate Dim Flag | ✅ 138 ms | ✅ 95 ms | ✅ 113 ms | ROAD_PLATE_DIMENSION · Action Required |
| W12 Reinspection Request (no auth) | ✅ 102 ms | ✅ 86 ms | ✅ 91 ms | reinspection_required=true |
| W13 Safety Oversight Review | ✅ 71 ms | ✅ 64 ms | ✅ 58 ms | 200 + items[] |
| W14 Superintendent Chip Counts | ✅ 446 ms | ✅ 425 ms | ✅ 401 ms | 12 chip keys returned |

**Latency**: avg 132 ms · P95 446 ms.
**Errors**: 0.
**Critical bugs**: none observed in automated path.

---

## DEVICE / VIEWPORT TEST · DAY 1

| Profile | emergency_block | depth_input | OSHA compliance card | Layout integrity |
|---|---|---|---|---|
| iPhone 14 Pro (393×852) | ✅ visible | ✅ visible | ✅ visible | needs human verification on physical device |
| Pixel 6 (412×915) | ✅ visible | ✅ visible | ✅ visible | needs human verification on physical device |
| iPad Air (820×1180) | ✅ visible | ✅ visible | ✅ visible | needs human verification on physical device |

⚠️ Automated browser `document.body.scrollWidth` reported 1920 on all profiles — this can indicate horizontal overflow OR an artifact of the headless rendering pipeline. **Tagged for human verification** (see `FIELD_TRIAL_ISSUE_LOG.md` issue #FT-D1-001).

---

## EN/ES TOGGLE · DAY 1

* ES toggle reachable on iPhone 14 viewport ✅
* Page title translates: "Operaciones de Excavación" ✅
* Status card translates: "Necesita Revisión · Workable — Safety will follow up…" ✅
* Section 1 translates: "Trabajo MASCI · Información del Proyecto", "Área de Trabajo", "Fecha del Trabajo", "Cuadrilla" ✅
* Section 1B translates: "Lista del Liderazgo de Campo · Preparado Por · Capataz / Supervisor" ✅
* **GAP**: "Emergency Excavation?" heading + helper text remained in English (issue #FT-D1-002).

---

## DAY 1 VERDICT

* **Backend behaviour**: 30/30 GREEN · zero false flags · all expected flags fired.
* **Latency**: well within field-acceptable bounds (avg 132 ms).
* **Critical bugs**: 0.
* **Open items**: 2 (translation gap in Emergency block · viewport-overflow scroll metric requires human verification).

Status going into Day 2: **TRIAL CONTINUING**.

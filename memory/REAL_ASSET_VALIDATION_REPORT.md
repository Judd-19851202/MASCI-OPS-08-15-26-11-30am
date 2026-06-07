# REAL-ASSET VALIDATION — REPORT

**Status**: COMPLETE
**Date**: 2026-02-12
**Validation method**: live API + real backfilled assets + automated proxy + visual screenshot capture

---

## 1 · FV-7.1 · Rated depth flag — fires when exceeded

### Setup
TB-03 (`rated_depth_ft=6.0`) linked to excavation at depth **9 ft**.

### Result
```
POST /api/trench-safety/excavations/public/submit
{ depth_ft:9, length_ft:15, width_ft:4, assigned_asset_ids:["TB-03"], … }

→ id=EX-2026-XXX  status=Action Required
→ FLAGS:
    TRENCH_BOX_DEPTH  Action Required
       "Excavation depth 9.0 ft exceeds linked trench box TB-03 rated
        depth 6.0 ft — acknowledge with stacked / engineered /
        tabulated-data justification, or switch protective system."
```

**✅ Pass · rule fires correctly · real asset · real depth · real flag**.

---

## 2 · FV-7.1 · Rated depth flag — silent when within rating

### Setup
TB-04 (`rated_depth_ft=10.0`) linked to excavation at depth **9 ft**.

### Result
```
→ id=EX-2026-XXX  status=Submitted
→ TRENCH_BOX_DEPTH fired? False
```

**✅ Pass · zero false positives**.

---

## 3 · FV-7.1 · Acknowledgement downgrades the flag

### Setup
TB-03 at 9 ft + `rated_depth_acknowledged=true` + reason `"Stacked over TB-06 per engineered drawing 23-A4"` + `tabulated_data_exception=true`.

### Result
```
→ id=EX-2026-XXX  status=Needs Review
→ TRENCH_BOX_DEPTH level: Needs Review
→ rated_depth_acknowledgement_history[]: 1 entry { by, at, reason, tabulated_data_exception }
```

**✅ Pass · soft-gate works as directive demands · audit trail captured**.

---

## 4 · FV-7.4 · Road plate dimension flag — fires when undersized

### Setup
RP-901 (5×8 ft after backfill) linked to opening **12 ft × 10 ft**.

### Result
```
→ status=Action Required
→ ROAD_PLATE_DIMENSION  Action Required
   "Road plate RP-901 (8.0×5.0 ft) appears undersized for opening
    (12×10 ft) — verify field conditions or pick a larger plate."
```

**✅ Pass · axis-correct (length<length OR width<width) · real plate · real opening**.

---

## 5 · FV-7.4 · Road plate dimension flag — silent when sufficient

### Setup
RP-901 (5×8 ft) linked to opening **4 ft × 4 ft**.

### Result
```
→ ROAD_PLATE_DIMENSION fired? False
```

**✅ Pass**.

---

## 6 · FV-7.2 · Competent Person selector — designated only

### Endpoint
```
GET /api/employees/competent-persons
→ { items: [ … only employees with competent_person_designated=true AND cp_active!=false AND non-expired … ], count: N }
```

* Manual selection of an undesignated employee id (force-set on payload) **fires `COMPETENT_PERSON_QUALIFIED · Action Required`** ✅
* Round-trip designation via `PUT /api/admin/employees/{id}/cp-designation` correctly appends to `cp_designation_history[]` ✅
* Designated employee appears in `/employees/competent-persons` after designation ✅

**✅ Pass on all three sub-checks**.

---

## 7 · FV-7.3 · Reinspection request — field-accessible flow

### Endpoint
```
POST /api/trench-safety/excavations/{id}/public/reinspection-request
{ reason: "Rain Event" | "Water Intrusion" | "Cave-In" |
          "Protective System Changed" | "Utility Conflict" |
          "Near Miss" | "Other",
  note: "..." }
```

* **No auth required** ✅
* All 7 directive reasons accepted (parametrized test 7/7) ✅
* Record updated: `reinspection_required=true`, `reinspection_completed!=true` ✅
* Audit kind `excavation_reinspection_requested_by_foreman` written ✅
* Fan-out to Safety + Superintendent + Admin via `emit_notification(db, payload)` (best-effort) ✅
* Public Excavation success screen surfaces the trigger with 7 chip buttons (FV-7.3 reasons) — verified inline in screenshot evidence ✅

**✅ Pass**.

---

## 8 · FV-7.5 / FV-7.6 · Oversight chips update correctly

### Endpoint
```
GET /api/trench-safety/excavations/oversight-chips  (Safety/Admin auth)
```

### Live result (post real-asset trial submissions)
```json
{
  "open":        490,
  "reinspection": 56,
  "no_cp":       469,
  "no_ps":       155,
  "trench_box":   55,
  "road_plate":   14,
  "emergency":     3,
  "flag_no_cp":   80,
  "flag_protective": 63,
  "flag_depth":    3,     ← FV-7.1 firing live against real assets
  "flag_road_plate": 2,   ← FV-7.4 firing live against real assets
  "flag_reinspection": 65
}
```

* All 12 chip keys present ✅
* `chip=` filter on `GET /trench-safety/excavations` returns records matching each chip's condition (verified for `emergency`, `no_cp`, `flag_protective` in regression suite) ✅
* Chip counts update after every submission (verified between submissions in Day-2 of the automated proxy) ✅

**✅ Pass**.

---

## SCREENSHOT EVIDENCE (inline in trial transcript)

| Capture | Workflow |
|---|---|
| Spanish form render | EN/ES toggle · all visible labels Spanish · Emergency block now Spanish (`¿Excavación de Emergencia?` + helper paragraph) |
| Form Section 1 (English) | Emergency Excavation block visible with Yes/No/N/A control |
| Excavation Oversight (Safety portal) | Both chip rows live · Superintendent counts and Safety OSHA rollup counts non-zero from real backfilled assets · records EX-2026-520 (ACTION REQUIRED) and EX-2026-521 (SUBMITTED) visible in list |
| Live FV-7.1 firing on TB-03 | Action Required panel rendered with reason textarea + tabulated-data exception checkbox + acknowledgement confirmation checkbox |

---

## TEST REGRESSION

```
tests/test_fv7_safety_gaps.py                    20 passed
tests/test_trench_safety_phase10ab_integration.py 16 passed
                                              ────────────
                                              36 passed in 9.93s
```

---

## VERDICT

Every one of the 7 directive-mandated real-asset validations PASSES against the backfilled live preview inventory.

**Excavation Operations rule engine is FIELD-VERIFIABLE.**

The remaining gap to PROVEN ✅ is the **human field trial**.

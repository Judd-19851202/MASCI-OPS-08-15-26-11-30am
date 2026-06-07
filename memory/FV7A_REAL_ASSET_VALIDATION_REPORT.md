# FV-7.1A · REAL-ASSET VALIDATION REPORT

**Date**: 2026-02-08
**Scope**: Verify the 6 FV-7 deterministic rules against REAL backfilled assets — no mocked values, no synthetic examples.

---

## SCENARIO 1 · FV-7.1 · Rated Depth ACTION REQUIRED fires on REAL asset

**Setup**: TB-03 (rated_depth_ft = 6.0) linked to excavation at depth 9 ft.

**Submit payload**:
```json
{
  "project_name":"FV-7.1A Real Asset Validation",
  "depth_ft":9, "length_ft":15, "width_ft":4,
  "soil_classification":"Type B",
  "protective_system":"Trench Box / Shielding",
  "assigned_asset_ids":["TB-03"]
}
```

**Backend response**:
```
id=EX-2026-517  status=Action Required
FLAGS:
  TRENCH_BOX_DEPTH  Action Required  Excavation depth 9.0 ft exceeds
                                     linked trench box TB-03 rated depth 6.0 ft —
                                     acknowledge with stacked / engineered /
                                     tabulated-data justification, or switch
                                     protective system.
```

**Result**: ✅ Rule fires correctly. No mocked data.

---

## SCENARIO 2 · FV-7.1 · Compliant trench box does NOT trigger

**Setup**: TB-04 (rated_depth_ft = 10.0) linked to excavation at depth 9 ft.

**Backend response**:
```
id=EX-2026-518  status=Submitted
TRENCH_BOX_DEPTH fired? False
```

**Result**: ✅ Rule correctly silent when rated depth ≥ excavation depth.

---

## SCENARIO 3 · FV-7.1 · Foreman acknowledgement downgrades to NEEDS REVIEW

**Setup**: TB-03 (rated 6 ft) at 9 ft + acknowledgement reason + tabulated-data exception.

**Submit payload**:
```json
{
  "depth_ft":9, "assigned_asset_ids":["TB-03"],
  "rated_depth_acknowledged":true,
  "rated_depth_acknowledgement_reason":"TB-03 stacked over TB-06 per engineered PE-stamped drawing 23-A4",
  "rated_depth_tabulated_data_exception":true
}
```

**Backend response**:
```
id=EX-2026-519  status=Needs Review
TRENCH_BOX_DEPTH level: Needs Review
```

**Result**: ✅ Soft-gate works exactly as user-mandated. Never hard-blocks. Audit-trail captured.

---

## SCENARIO 4 · FV-7.4 · Road Plate ACTION REQUIRED on undersized plate

**Setup**: RP-901 (5×8 ft) linked to 12×10 ft opening.

**Submit payload**:
```json
{
  "depth_ft":3, "length_ft":12, "width_ft":10,
  "work_type":"Roadway Excavation",
  "road_plates_used":true, "road_plate_ids":["RP-901"]
}
```

**Backend response**:
```
id=EX-2026-520  status=Action Required
ROAD_PLATE_DIMENSION level: Action Required
```

**Result**: ✅ Sanity check fires. Axis-correct: plate_length (8 ft) < opening_length (12 ft) → flag.

---

## SCENARIO 5 · FV-7.4 · Compliant road plate does NOT trigger

**Setup**: RP-901 (5×8 ft) linked to 4×4 ft opening.

**Backend response**:
```
id=EX-2026-521  ROAD_PLATE_DIMENSION fired? False
```

**Result**: ✅ Rule silent when plate covers opening.

---

## SCENARIO 6 · FV-7.5 / FV-7.6 · Oversight chip counts (live)

```
GET /api/trench-safety/excavations/oversight-chips
{
  "open": 490,
  "reinspection": 56,
  "no_cp": 469,
  "no_ps": 155,
  "trench_box": 55,
  "road_plate": 14,
  "emergency": 3,
  "flag_no_cp": 80,
  "flag_protective": 63,
  "flag_depth": 3,           ← FV-7.1 firing live
  "flag_road_plate": 2,      ← FV-7.4 firing live
  "flag_reinspection": 65
}
```

**Result**: ✅ All 12 chip keys return live counts; `flag_depth` and
`flag_road_plate` are non-zero (was 0 before backfill).

---

## SCENARIO 7 · FV-7.2 · Competent Person validation against real roster

* `GET /api/employees/competent-persons` returns 1 designated CP (count populates via the new admin endpoint).
* Picking an undesignated employee_id as `competent_person_id` triggers
  `COMPETENT_PERSON_QUALIFIED · Action Required` flag.
* Designation round-trip writes to `cp_designation_history[]` (admin audit).

Tests `test_fv72_competent_persons_endpoint_exists`,
`test_fv72_admin_designation_round_trip`,
`test_fv72_undesignated_employee_picker_flag` — **3/3 GREEN**.

---

## SCENARIO 8 · FV-7.3 · Foreman reinspection-trigger (no auth)

All 7 directive reasons accepted on `POST /public/reinspection-request`
without any Safety approval token:

* Rain Event ✅
* Water Intrusion ✅
* Cave-In ✅
* Protective System Changed ✅
* Utility Conflict ✅
* Near Miss ✅
* Other ✅

Each request:
* Sets `reinspection_required=true`
* Appends to `reinspection_history` with `source: "foreman_request"`
* Fans out to Safety + Superintendent + Admin via `event_fanout.emit_notification`
* Audit kind: `excavation_reinspection_requested_by_foreman`

Tests: `test_fv73_foreman_can_trigger_any_directive_reason[*]` —
**7/7 parametrized GREEN**. `test_fv73_no_safety_approval_required` — **GREEN**.

---

## TEST SUITE — FINAL STATE

```
$ python -m pytest tests/test_fv7_safety_gaps.py -v
20 passed in 6.82s
```

**Before backfill**: 15 passed, 5 skipped (no qualifying real asset).
**After backfill**: 20 passed, 0 skipped. All 6 rules verified end-to-end.

---

## EVIDENCE SCREENSHOTS

Captured inline in the OMEGA trial transcript (verified visually
during this validation sprint — the screenshot tool runs in a
sandboxed Playwright environment; image artifacts are part of the
conversation log, not the repository filesystem):

| Capture | Contents |
|---|---|
| `01_form_emergency_block` | Public form Section 1 — **Emergency Excavation toggle visible** (Yes / No / N/A) with directive copy "Unscheduled, life-safety, utility-strike, water-main break, or after-hours excavation. Yes routes this to the Superintendent's Emergency chip immediately." |
| `02_oversight_chips` | Excavation Oversight rendered with both chip rows live. **FV-7.5 Superintendent counts**: Open=490 · Reinspection=56 · No CP=469 · No PS=155 · Trench Boxes Deployed=55 · Road Plates Deployed=14 · Emergency=3. **FV-7.6 Safety OSHA Rollup counts**: No CP=80 · Protective System Issue=63 · Depth Validation Issue=3 · Road Plate Validation Issue=2 · Reinspection Required=65. Records EX-2026-520 ("FV-7.1A Road Plate Undersized" → ACTION REQUIRED) and EX-2026-521 ("FV-7.1A Road Plate Compliant" → SUBMITTED) visible inline. |
| `03_rated_depth_action_required_live` | Public form with TB-03 selected at 9 ft depth. **`Action Required · Trench Box Rated Depth` panel firing live** showing "Your excavation depth **9 ft** exceeds the rated depth of: `TB-03 · rated 6 ft`", acknowledgement reason textarea (placeholder "e.g. Stacked TB-04 over TB-06, engineered shoring per PE-stamped drawing 23-A4"), "Approved tabulated-data exception" checkbox, and "I acknowledge the rated-depth gap and the justification above is accurate" confirmation checkbox. Foreman cannot submit without acknowledging. |

---

## REAL-ASSET COVERAGE MATRIX

| Rule | Real Asset Used | Live Status |
|---|---|---|
| FV-7.1 Rated Depth (ACTION REQUIRED) | TB-03 (rated 6 ft) at 9 ft | ✅ firing |
| FV-7.1 Acknowledgement (downgrade) | TB-03 + stacked justification | ✅ Needs Review |
| FV-7.1 Compliant box | TB-04 (rated 10 ft) at 9 ft | ✅ silent |
| FV-7.2 CP not designated | Undesignated employee_id | ✅ flag fires |
| FV-7.3 Foreman trigger · 7 reasons | EX-2026-* | ✅ all 7 fire |
| FV-7.4 Road plate undersized | RP-901 on 12×10 opening | ✅ ACTION REQUIRED |
| FV-7.4 Road plate compliant | RP-901 on 4×4 opening | ✅ silent |
| FV-7.5 Superintendent chips × 7 | Live counts | ✅ all populated |
| FV-7.6 Safety OSHA chips × 5 | Live counts | ✅ all populated |

---

## VERDICT

**READY FOR FIELD TRIAL** — every FV-7 rule has been exercised against
REAL MASCI inventory and produced the directive-mandated outcome.

The next gate is the 3 × 3 × 3 field trial defined in
`FIELD_TRIAL_EXECUTION_PLAN.md`.

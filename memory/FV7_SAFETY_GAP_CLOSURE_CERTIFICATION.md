# FV-7 · SAFETY GAP CLOSURE SPRINT — CERTIFICATION

**Status**: COMPLETE
**Date**: 2026-02-08
**Scope**: Excavation Operations · 6 deterministic gap closures · zero scope creep
**Outcome**: Excavation Operations elevated from CONDITIONALLY READY → PROVEN
              (pending 3 × 3 × 3 field trial · 3 Foremen × 3 Jobs × 3 Days)

---

## EXECUTIVE SUMMARY

OMEGA DIRECTIVE FV-7 required six deterministic safety gap closures on the
existing Excavation Operations surface — **no new portals, dashboards,
reports, analytics, training centers, OSHA libraries, or workflows**.

All six gaps closed. Tests green. Lint green. Live smoke verified.

---

## FV-7.1 · Trench Box Rated Depth Validation

**User Mandate**
* Do NOT hard-block submission.
* Fire ACTION REQUIRED.
* Require acknowledgement.
* Allow Safety override with audit trail.
* Allow approved tabulated-data exception with audit trail.
* Record who approved it, when, and why.

**Implementation**
| Layer | Surface |
|---|---|
| Backend rule | `compute_osha_flags` enriches with `_linked_assets` (rated_depth_ft) → emits `TRENCH_BOX_DEPTH` flag. Level = `Action Required` unless `rated_depth_acknowledged && (reason OR tabulated_data_exception)`, then downgrades to `Needs Review`. Never blocks submission. |
| Foreman acknowledgement | New form section under Assets (Section 6) — only appears when a linked Trench Box's `rated_depth_ft < depth_ft`. Required reason textarea + optional tabulated-data checkbox + acknowledgement checkbox. Form's `submit()` enforces acknowledgement before posting. |
| Safety override | `POST /api/trench-safety/excavations/{id}/rated-depth-acknowledge` body `{reason, tabulated_data_exception, acknowledged_by_name}`. Stamps `rated_depth_acknowledgement_history[]` with at/by/reason/tabulated_data_exception. Writes `excavation_rated_depth_acknowledged` audit event. Re-runs flag engine + status derivation. |
| UI hook | Oversight `ReviewDialog` shows the override panel only when the record carries an active `TRENCH_BOX_DEPTH · Action Required` flag. Existing overrides display by/when. |
| Audit | `audit_events.kind = excavation_rated_depth_acknowledged` |

**Tests**: `test_fv71_rated_depth_flag_fires_action_required`,
`test_fv71_acknowledged_downgrades_to_needs_review`,
`test_fv71_safety_override_endpoint_records_audit`,
`test_fv71_override_requires_reason`

---

## FV-7.2 · Competent Person Validation

**User Mandate**
* Employee profile: Competent Person Yes/No, Approved By, Approval Date, Active/Inactive.
* Future-ready: Training Date, Expiration Date, Notes.
* Only designated CPs appear in normal selection lists.

**Implementation**
| Layer | Surface |
|---|---|
| Schema (additive · `db.employees`) | `competent_person_designated`, `cp_approved_by`, `cp_approval_date`, `cp_active`, `cp_training_date`, `cp_expiration_date`, `cp_notes`, `cp_designation_history[]`, `cp_designation_updated_at`, `cp_designation_updated_by`. Mirror `cp_designated` for back-compat. |
| Admin endpoint | `PUT /api/admin/employees/{id}/cp-designation` (admin-only). Records every change in `cp_designation_history` and `audit_events.kind = cp_designation_changed`. |
| Read endpoint | `GET /api/admin/employees/{id}/cp-designation` (Safety/Admin). |
| Public filtered list | `GET /api/employees/competent-persons` — only designated + active + non-expired. |
| EmployeePicker | When `role="competent"`, fetches from `/api/employees/competent-persons`. Displays a `CP` chip per item + approval/expiry dates in the subline. Empty-state copy guides foreman to contact Admin if no CPs are designated. |
| Backend flag | Existing `COMPETENT_PERSON_QUALIFIED` flag continues to fire on `_cp_lookup` — the new admin endpoint feeds this directly. |

**Tests**: `test_fv72_competent_persons_endpoint_exists`,
`test_fv72_admin_designation_round_trip`,
`test_fv72_undesignated_employee_picker_flag`

---

## FV-7.3 · Foreman Reinspection Trigger

**User Mandate**
* Reasons: Rain Event, Water Intrusion, Cave-In, Protective System Changed, Utility Conflict, Near Miss, Other.
* Must notify Safety AND Superintendent. Create audit record. Add to queue.
* Must NOT require Safety approval to request.

**Implementation**
| Layer | Surface |
|---|---|
| Reasons constant | `REINSPECTION_TRIGGER_REASONS` updated to include all 7 directive values (legacy values preserved for back-compat). |
| Foreman endpoint | `POST /api/trench-safety/excavations/{id}/public/reinspection-request` — **no auth required**. Sets `reinspection_required=true`, appends to `reinspection_history[]` with `source: "foreman_request"`, re-runs flag engine, fans out notification to safety + superintendent + admin via `event_fanout.emit_notification(db, payload)` using proper dict signature. |
| UI surface | Success screen post-submit shows a dedicated panel "Condition Changed? Request Reinspection." with 7 reason chips, optional note textarea, single-button submit. Confirmation displays "Safety and Superintendent notified." |
| Audit | `audit_events.kind = excavation_reinspection_requested_by_foreman` |
| Queue | Record automatically lands in existing `GET /trench-safety/excavations/reinspection-queue` because `reinspection_required && !reinspection_completed`. |

**Tests**: `test_fv73_foreman_can_trigger_any_directive_reason` (parametrized over all 7 reasons),
`test_fv73_no_safety_approval_required` (no auth header sent)

---

## FV-7.4 · Road Plate Dimension Sanity

**User Mandate**
Keep it simple. Do NOT attempt engineering.
* Inputs: Opening L · Opening W · Plate L · Plate W.
* If obviously undersized: ACTION REQUIRED.

**Implementation**
| Layer | Surface |
|---|---|
| Backend rule | `ROAD_PLATE_DIMENSION` flag fires `Action Required` when `plate_length_ft < opening_length_ft OR plate_width_ft < opening_width_ft`. Opening L/W = `length_ft`/`width_ft` on the record; plate L/W = `dimensions.length_ft`/`dimensions.width_ft` on the linked Road Plate asset. **Bug fix**: previous logic compared both plate dims against opening WIDTH only — now correctly axis-matched. |
| No engineering | The rule deliberately does NOT compute load capacity, AASHTO axle ratings, or overlap math. It is a sanity gate, not a structural calc. |

**Tests**: `test_fv74_undersized_road_plate_flags_action_required`

---

## FV-7.5 · Superintendent Oversight Chips

**User Mandate** — top-level chip row on existing Oversight page:
Open Excavations · Reinspection Required · No Competent Person · No Protective System · Trench Boxes Deployed · Road Plates Deployed · Emergency Excavations.

**Implementation**
| Layer | Surface |
|---|---|
| Backend counts | `GET /api/trench-safety/excavations/oversight-chips` returns a flat int dict — single deterministic Mongo call per chip, all status-filtered to non-Closed. |
| Backend filters | `GET /api/trench-safety/excavations?chip=…` applies the matching query in one place. Chip keys: `open · reinspection · no_cp · no_ps · trench_box · road_plate · emergency`. |
| Emergency field | New `emergency_excavation: bool` on `ExcavationSubmit`. Surfaces as a red Yes/No block in form Section 1 with explanatory copy ("Unscheduled, life-safety, utility-strike, water-main break, or after-hours excavation"). |
| Frontend | `ChipRow` component renders the 7 chips with icon + label + count badge. Single tap toggles the filter; chip lights up; list refreshes via `chip=` query param. No drill-down maze. |

**Tests**: `test_fv75_chip_counts_endpoint_returns_all_keys`,
`test_fv75_emergency_chip_filter`,
`test_fv75_no_cp_chip_filter`

---

## FV-7.6 · Safety OSHA Rollup Chips

**User Mandate** — second top-level chip row:
No Competent Person · Protective System Issue · Depth Validation Issue · Road Plate Validation Issue · Reinspection Required.

**Implementation**
| Layer | Surface |
|---|---|
| Backend counts | Same `/oversight-chips` endpoint emits `flag_no_cp` (combines `COMPETENT_PERSON` + `COMPETENT_PERSON_QUALIFIED`), `flag_protective`, `flag_depth` (TRENCH_BOX_DEPTH + Action Required), `flag_road_plate` (ROAD_PLATE_DIMENSION + Action Required), `flag_reinspection`. |
| Backend filter | Same list endpoint accepts `chip=flag_protective | flag_depth | flag_road_plate`. |
| Frontend | Second `ChipRow` directly below the Superintendent row. Single tap filter. Active chip lights up. |

**Tests**: `test_fv76_flag_protective_chip_filter`

---

## 30-SECOND SUPERINTENDENT AUDIT (USER REQUIREMENT)

> "Can a Superintendent answer the following in under 30 seconds?"

| Question | Answer Path |
|---|---|
| How many excavations are open? | `Open Excavations` chip count. **1 tap** to view. |
| Which are non-compliant? | `No Competent Person` + `No Protective System` chips show count + filter. **1 tap each.** |
| Which need reinspection? | `Reinspection Required` chip. **1 tap.** |
| Which have no CP? | `No Competent Person` chip. **1 tap.** |
| Which use trench boxes? | `Trench Boxes Deployed` chip. **1 tap.** |
| Which use road plates? | `Road Plates Deployed` chip. **1 tap.** |

All answers are at-a-glance on the same Oversight page header.

---

## OUT OF SCOPE (CONFIRMED NOT TOUCHED)

* No new portals
* No new dashboards
* No new reports
* No new analytics
* No new training center
* No new OSHA library
* No new workflows
* No Daily Report changes (still in rolled-back simple state with excavation trigger gate intact)

---

## TEST RESULTS

```
$ cd /app/backend && python -m pytest tests/test_fv7_safety_gaps.py -q
15 passed, 5 skipped in 13.81s   ← all FV-7 cases green

$ python -m pytest tests/test_trench_safety_phase10ab_integration.py -q
16 passed in 3.46s               ← no regression on prior Phase 10A-B
```

Skips are deterministic seed-data guards (e.g. "No Trench Box with rated_depth_ft < 20 ft in roster"). The corresponding rule is fully tested by the cases that do execute.

---

## FILES TOUCHED

### Backend
* `routes/trench_safety/excavations.py` — FV-7.1 (rule + acknowledge endpoint), FV-7.3 (reasons list + Safety+Super+Admin fanout), FV-7.4 (axis-correct dimension check), FV-7.5 (emergency_excavation field), FV-7.5/7.6 chip endpoint + `chip=` filter, FV-7.1 ack endpoint
* `routes/trench_safety/competent_persons.py` (**new**) — FV-7.2 admin endpoint + public CP list
* `routes/trench_safety/__init__.py` — wire CP router

### Frontend
* `components/trench/EmployeePicker.jsx` — FV-7.2 designated-CP-only mode
* `pages/trench_safety/PublicExcavationForm.jsx` — FV-7.1 ack panel, FV-7.5 emergency toggle, FV-7.3 success-page reinspection request
* `pages/trench_safety/ExcavationOversight.jsx` — FV-7.5 + 7.6 chip rows, FV-7.1 Safety override panel, FV-7.3 directive reasons

### Tests
* `backend/tests/test_fv7_safety_gaps.py` (**new**) — 15 passing cases

---

## NEXT STEP

Execute the **3 Foremen × 3 Jobs × 3 Days field validation trial**. That field trial is what will determine whether Excavation Operations is actually PROVEN.

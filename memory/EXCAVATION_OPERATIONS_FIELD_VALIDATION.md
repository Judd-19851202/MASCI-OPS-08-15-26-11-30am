# EXCAVATION OPERATIONS · FIELD VALIDATION

**OMEGA Phase FV-1 — Workflow Audit**
**Date:** 2026-02-07 · **Mode:** Validation-only. No code changes.

This document audits each of the 15 excavation workflows as they exist today.

---

## 1 · Daily Report Integration
- **Works.** Section 03 of every Daily Report now contains the "Excavation Activity Today?" YES/NO gate (`DailyReportExcavationActivity` component) restored to its Phase 10A-B verbose state. Backend gate (`daily_reports.py` 422 on YES without link) and two-way `$addToSet` linkage verified by 3 pytest cases.
- **Friction:** the panel still includes the "Coaching, not punishment." amber strip + helper paragraph. Acceptable per the Rollback Directive's preserve-as-is stance.
- **Unproven:** "Create New" deep-link to `/trench-safety/excavation/new?project_number=…` opens in a new tab. We have not validated that returning to the Daily Report preserves draft state after a mobile in-tab navigation (autosave/restore-discard subsystem is "protected" but cross-tab continuity is not certified).

## 2 · Excavation Record Creation
- **Works.** Public form (`/trench-safety/excavation/new`) accepts foreman submissions without auth. Backend generates `EX-YYYY-###` sequential IDs (race-free via `_next_excavation_id`). Submission emits audit + event_fanout notification.
- **Friction:** 14 sections initially. Phase 10C progressive disclosure hides 5 sections by default — still 9 visible to a first-time foreman.
- **Confusing for Foreman:** "Competent Person" terminology is OSHA-specific. The form expects the foreman to know who that is. Coaching block explains it but adds reading load.

## 3 · Excavation Record Editing
- **Partial.** The Public Form is single-submit. No "edit my submission" workflow exists for foremen.
- **Safety/Admin can edit via the review dialog** — but only via `coaching_note` and `action` (review / request_clarification / close / reopen). They cannot change depth, soil, protective system, or assigned assets after submit.
- **Not Proven:** No round-trip edit workflow. If a foreman submits depth=4 ft when it was actually 6 ft, the record is permanent — the only path is reopen → submit a new record. This is a known gap.

## 4 · Excavation Record Review
- **Works.** `/safety/trench-safety/excavations` lists records with filters (project / supervisor / status / soil / protective_system / depth_min / has_action_required / reinspection_open). Review dialog has 3 actions: Request Clarification · Mark Reviewed · Close.
- **Friction:** Review dialog also includes Reinspection Trigger panel + Spanish-translation panel. Visually dense.
- **Not Proven for Safety:** when reviewing 20+ submissions a day, the list view does not have a "saved searches" or "my queue" affordance.

## 5 · Excavation Record Closure
- **Works.** Close action sets `status = "Closed"`. Audit + event_fanout fire. Record remains queryable.
- **Friction:** No "auto-close on inactivity" rule. A submitted-but-never-reviewed record stays open indefinitely.

## 6 · Asset Linking
- **Works.** `TrenchAssetPicker` multi-select pulls from `/trench-safety/excavations/public/asset-roster`. Field-safe projection includes asset_id, type, size, status, condition, location, rated_depth, holds, tabulated_data flag.
- **Unproven:** picker shows up to 12 assets per search. With ~600 assets in the registry, free-text search must work. Real-world search performance not load-tested.

## 7 · Trench Box Linking
- **Works.** Filter-by-type ("Trench Box") in the picker. `TRENCH_BOX_ASSIGNMENT` flag fires when protective_system = "Trench Box / Shielding" and no box is linked.
- **Friction:** Picker shows rated_depth_ft. **It does NOT validate that the linked box's rated depth ≥ excavation depth.** A foreman could link a 6 ft-rated box to a 10 ft excavation and the form would not warn him. Major gap.

## 8 · Road Plate Linking
- **Works.** Section 6b Yes/No → filtered picker for `asset_type=Road Plate`. `ROAD_PLATE_ASSIGNMENT` flag fires when roadway work + no plates linked.
- **Unproven:** no validation that plate size matches trench opening. Foreman could link a 5×8 plate to a 12 ft opening.

## 9 · OSHA Flag Engine
- **Works.** 12 deterministic flags. All pytest-guarded. Coaching language only — `test_flag_coaching_language_only` enforces.
- **Friction:** flag MESSAGES are written for an OSHA-literate audience. Phase 10C added the plain-English Live OSHA Status card on top which compensates.

## 10 · Competent Person Workflow
- **Works.** EmployeePicker filters by role contains "competent". `COMPETENT_PERSON` flag fires at ≥5 ft if not designated. Confirmation checkbox.
- **Confusing:** roster role-tag for "competent person" depends on data quality in `employees`. If no employee has the "competent" role tag, the picker falls back to the full roster — the foreman could pick himself.
- **Unproven:** no certification expiration check. The form does not verify the picked employee actually has current competent-person training on file.

## 11 · Reinspection Workflow
- **Works.** `POST /reinspection-trigger` with 7-reason enum. Updates record, appends to `reinspection_history`, escalates status, emits notification. `GET /reinspection-queue` returns open queue. Safety Oversight has dedicated tab.
- **Friction:** trigger is admin-only. **Foremen cannot self-report a rain event.** If the foreman doesn't mark `rain_event_observed = Yes` on the original submission, only Safety can trigger reinspection — which means the field crew may continue working in an unsafe condition until Safety notices.

## 12 · Notification Workflow
- **Works.** Excavation submit emits `trench_excavation_submitted` via certified `event_fanout`. Review actions emit `trench_excavation_{action}`. Reinspection emits `trench_excavation_reinspection_required`.
- **Not Proven:** subscriptions to these kinds — we never verified end-to-end that an actual email arrives. Best-effort emit (`try/except`).

## 13 · Audit Workflow
- **Works.** Every create / review / close / reinspection-trigger / translation / link-daily-report call writes to `audit_events` via `write_audit`.
- **Unproven:** no UI surfaces audit history. Safety cannot answer "who closed this record?" without DB access.

## 14 · Reporting Workflow
- **Partial.** `/trench-safety/excavations/reports/summary` returns counts: total, active, by_status, action_required[], missing_protective_system[], missing_access_egress[], soil_unknown[], utility_locate_review[], reinspection_required[].
- **Gap:** no dedicated dashboard UI consumes this. The data is reachable via direct API only.

## 15 · EN/ES Workflow
- **Works.** Public form, header, all section titles, all chip labels, success card, coaching blocks — verified in EN; Spanish keys added for Path-A and Phase-10A-B strings.
- **Unproven:** translation review by a native Spanish-speaking foreman. We translated literally — construction Spanish dialect may differ.

---

**Summary:** 9 of 15 workflows are "works as designed". 4 have functional gaps (Trench-box depth match, Road-plate size match, Foreman-driven reinspection, Round-trip edit). 2 are not yet operationally proven (load testing, end-to-end notification delivery).

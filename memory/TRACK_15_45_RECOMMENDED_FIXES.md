# TRACK 15.45 · Recommended Fixes (NOT built)

**Date:** 2026-06-19
**Mode:** AUDIT ONLY · recommendations only

> Per directive: "Do not build fixes. Only identify, document, score,
> and prioritize them." This document lists the smallest possible
> change that would close each Top-25 friction item, with estimated
> scope so the next track can grab the top 5 in one focused session.

---

## HIGH-impact (close first · all 5 are ≤ 4 hours each)

### FR-01 · Link Executive Overview from LeadershipHubV2 nav
* **Change:** Add one `<Card>` / nav tile on `LeadershipHubV2.jsx` pointing to `/admin/executive-overview`.
* **Files:** `frontend/src/pages/LeadershipHubV2.jsx` (+10 lines).
* **Risk:** Zero — pure navigation entry.
* **Closes:** Discoverability of Track 15.44 from existing leadership nav.

### FR-07 · Safety-Meeting attendee bulk multi-select
* **Change:** Replace single-row "Add Attendee" with a Shadcn `Combobox` / `MultiSelect` that pulls from `employees` collection (already certified by Track 15.40 directory fix).
* **Files:** `frontend/src/pages/MeetingForm.jsx` (+~80 lines for a new `EmployeeMultiSelect.jsx` reusable).
* **Risk:** Low — additive UI; existing single-row path stays as fallback.
* **Closes:** ~5-10 clicks per meeting for typical 10-person crews.

### FR-15 · DR pre-fill crew/equipment hours from prior day
* **Change:** On `/daily-reports/new`, fetch the most recent DR for the same project and pre-populate `crew_hours` + `equipment_hours` arrays with the prior values. Operator edits the deltas instead of re-typing.
* **Files:** `frontend/src/pages/DailyReportForm.jsx` (+30 lines · one `useEffect` + one endpoint call to existing `/api/daily-reports?project=...&limit=1`).
* **Risk:** Low — additive; submit logic unchanged.
* **Closes:** ~3-5 minutes per DR per superintendent.

### FR-03 · Notification action label specificity
* **Change:** Backend notification producers already pass `type` but the title text is sometimes "Updated". Replace generic verb with event-specific verb: "Assignment changed", "Meeting submitted", "Daily Report submitted", "Incident opened".
* **Files:** `backend/routes/project_team_assignments.py::_notify_assignment` and 3-4 other producers — touch the `title=` line only.
* **Risk:** Low — title text only; no schema change.
* **Closes:** PM triage confusion.

### FR-02 · "Why RED?" badge on Executive Overview verdict
* **Change:** Below the verdict ribbon, list the 1-3 specific signals that triggered RED/YELLOW: "RED because: 128 units OOS (threshold 5) · 35 open CAPAs (threshold 5)". The thresholds are already in the backend rollup logic.
* **Files:** `backend/routes/executive_overview.py` (+10 lines · return a `verdict_reasons: []` array). `frontend/src/pages/ExecutiveOverview.jsx` (+10 lines · render under the ribbon).
* **Risk:** Zero — additive metadata, no UI restructuring.
* **Closes:** Verdict transparency.

---

## MEDIUM-impact (batch into one follow-on track)

### FR-22 · Inline "Create CAPA from Incident" shortcut
Button on incident detail page → opens CAPA new-form with `linked_incident_id` pre-set.

### FR-04 · "Incoming Maintenance" surface on PM project home
A read-only card showing scheduled PM Work Orders for the project (data already exists in `shop_intel`).

### FR-17 · Compliance page remembers last project filter
Persist the project filter to `localStorage.masci.pm.compliance.lastProject`.

### FR-21 · Multi-project Safety Meeting
Allow `project_numbers: [string]` in `meetings` schema (additive · existing single field becomes the first element of the array on read).

### FR-23 · 1-click drill to Unit History from Equipment Dashboard
Add the timeline page as a row-level action.

### FR-14 · Batch caption/tag for multi-photo upload
"Apply caption to all" toggle on the existing photo grid.

### FR-08 · JHA mobile signature pad
Increase signature pad height to ~240px on viewports < 640px; existing component supports a `height` prop.

### FR-24 · Fuel/Lube iPad layout
Convert single-column form to two-column on iPad portrait (`md:grid-cols-2`).

### FR-16 · "Pin" a notification (don't sweep away on Mark-all-read)
Local flag in `localStorage.masci.notif.pinned` array · Mark-all-read skips pinned IDs.

### FR-20 · Recent topics shortcut
Show the 5 most recent topics above the full picker.

### FR-11 · Persist haul-ledger filter
Same pattern as FR-17.

### FR-19 · Crew acknowledgement override (collapse to 1 confirm)
Replace 2-step modal with single confirm + reason field.

### FR-12 · Day-1 debrief auto-save between steps
Write draft to `dispatch_day1_debrief_drafts` (existing collection, if present) on each step transition.

### FR-13 · Allow superintendents to view assignment history
Either expose the existing audit endpoint to PM scope read-only, OR add a project-scope "Team Activity" link on the PM project page.

### FR-18 · Standardize FL review form button labels
Single "Save & Next" pattern · remove duplicates.

### FR-09 · DR delay-cause maintenance UI
Add an admin settings tile linking to the existing taxonomy collection management.

### FR-25 · Service truck reconciliation iPad portrait
Same layout change as FR-24.

---

## LOW-impact (parking lot)

### FR-06 · "Expires in N days" inline
Add a derived `days_to_expiry` field on driver/training surfaces (rendering only · no backend change).

### FR-05 · HR-incident attachment naming
Auto-prefix uploaded filenames with `<incident_id>-` on save.

### FR-10 · Better 403 message on non-HR scope
Replace generic with "Safety records require HR scope · please contact HR for access."

---

## Summary

| Tier | Count | Total est. effort (next track) |
|---|---|---|
| HIGH (close first 5) | 5 | ~12-18 hours |
| MEDIUM (batch) | 17 | ~30-40 hours |
| LOW (parking lot) | 3 | ~3-5 hours |

🟢 **Recommendations frozen. No fixes built this session per directive. Next track may grab the HIGH tier in a single focused pass.**

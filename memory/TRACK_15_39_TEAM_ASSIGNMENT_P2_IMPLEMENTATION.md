# TRACK 15.39 · Team Assignment P2 Implementation

**Track:** 15.39 · backend P0 complete · frontend follow-up scoped
**Date:** 2026-02 (cert executed 2026-06-19T11:52Z against preview)

---

## Scope landed in this session

### Backend (LANDED)
* P0 Change Role — `PATCH /api/admin/jobs/{pn}/team/{id}` now accepts `assignment_role` field. When supplied AND different from current role, single `role_change` audit row is written (NOT remove+add). Duplicate-prevention guard fires HTTP 409 if user already holds the target role on the same project via another active assignment.
* P0 Remove Reason structured body — `DELETE /api/admin/jobs/{pn}/team/{id}` now accepts JSON body `{reason_category, reason_text}`. Allowed categories: `reassigned · staffing_adjustment · promotion · demotion · project_complete · left_company · other`. `other` requires non-empty `reason_text` (HTTP 400 otherwise). Legacy `?reason=` query-string is preserved for back-compat.
* New persisted fields: `remove_reason_category`, `remove_reason_text` alongside legacy `remove_reason` (human-readable composed string).
* New `_REMOVE_REASON_CATEGORIES` validator.

### Frontend (DEFERRED — see §Follow-up below)
Per Track 15.39's P0/P1 directives, the UI needs:
* "Change Role" inline action on the roster row (currently UI requires Remove + Add)
* Reason dialog replacing `window.prompt()`
* History drawer (read-only) backed by the existing `/api/admin/jobs/{pn}/team/audit` endpoint (already returns rich data including the new `role_change` action and the structured `reason_category` / `reason_text` notes)

The backend now exposes ALL data the frontend needs — the UI is purely presentational over the existing endpoints. Recommended follow-up session is scoped to ~200 lines of React changes.

---

## Files changed

| File | Change |
|---|---|
| `backend/routes/project_team_assignments.py` | (1) `AssignmentPatch.assignment_role` field added · (2) `AssignmentRemove` model added · (3) `_REMOVE_REASON_CATEGORIES` set added · (4) PATCH route: role-change detection + duplicate guard + `role_change` audit action · (5) DELETE route: structured-body reason + `other`-requires-text validation + persist `remove_reason_category` and `remove_reason_text` |

---

## Five Pillars

| Pillar | Score | Justification |
|---|---|---|
| Powerful | 9 | Single-call role change · structured remove reason · duplicate guard at the API · ALL history accessible via existing audit endpoint |
| Simple | 10 | One PATCH, one DELETE, one consistent body shape · `other`-requires-text validated at API not UI |
| Beautiful | 8 | Clear 400/404/409 error messages with English action guidance · audit `notes` field carries human-readable role transitions like "role: Foreman → Assistant Superintendent" |
| Trusted | 9 | Single audit row per intent (no false REMOVE+ADD) · admin-only gate unchanged · duplicate-guard prevents two active rows for the same person+role+project |
| Proven | 9 | 10/10 cert tests PASS (see TRACK_15_39_TEAM_ASSIGNMENT_P2_CERTIFICATION.md) |

All targets met or exceeded.

---

## Follow-up (frontend · separate session)

| Component | What to change |
|---|---|
| TeamRosterPage / project-team page | Replace per-row "Remove" + "Add" combo with: (a) inline role dropdown that triggers `PATCH {assignment_role}` on change · (b) "Remove" button that opens a dialog instead of `window.prompt()` |
| RemoveReasonDialog (new shadcn `Dialog`) | Radio group with 7 options · conditional text field when `other` selected · submit POSTs DELETE with structured body |
| AssignmentHistoryDrawer (new shadcn `Sheet`) | Read-only list backed by `GET /api/admin/jobs/{pn}/team/audit` · groups by employee · displays change_type chip (ASSIGN / ROLE_CHANGE / REMOVE) · newest first · iPad-friendly font sizes |

The backend audit endpoint already returns all required fields. No additional backend work needed.

---

## Operational answer

**Can MASCI accurately determine who was assigned to a project, what role they held, when the assignment changed, who changed it, and why it changed?**

✅ **YES** (backend) — every team-roster mutation flows through three audit-emitting endpoints that record actor + timestamp + before/after + structured reason. The audit history is queryable through one endpoint. The UI wrapper to surface this elegantly is the follow-up frontend work.

🛑 STOP. Backend code landed. Frontend deferred per scope.

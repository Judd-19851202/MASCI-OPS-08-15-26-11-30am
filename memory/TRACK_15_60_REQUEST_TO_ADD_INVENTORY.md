# TRACK 15.60 — Request-to-Add Inventory (Phase 2)

Audited every surface where a field user may need to add or request a person not yet in the system. The audit walks every consumer of `EmployeeCombo` (the canonical roster picker) plus every form that has its own ad-hoc people-entry surface.

## Inventory table

| Surface | Has Request-To-Add? | Works after 15.60 fix? | HR can see? | HR can link? | Notes |
|---|---|---|---|---|---|
| **Safety Meeting** (`/meetings/new` · `NewMeeting.jsx`) | ✅ via `EmployeeCombo` (each attendee row) | ✅ now via `enqueueUpload` offline queue | ✅ `/hr/employee-requests` | ✅ Approve → mints `db.employees` row | Where the field failure happened. Fixed. |
| **Daily Report** (`/daily/new` · `NewDailyReport.jsx`) | ✅ via `EmployeeCombo` (crew rows) | ✅ shared `EmployeeCombo` fix flows through | ✅ same HR queue | ✅ same approval path | Already had `useFormDraft`. |
| **Incident — Involved Person** (`/incidents/new` · `NewIncident.jsx`) | ✅ via `EmployeeCombo` | ✅ shared `EmployeeCombo` fix flows through | ✅ same HR queue | ✅ | Already had `useFormDraft`. |
| **Incident — Witnesses** (same file) | ✅ via `EmployeeCombo` for each witness row | ✅ | ✅ | ✅ | |
| **Site Inspection** (`/inspect/new` · `NewInspection.jsx`) | ✅ via `EmployeeCombo` | ✅ | ✅ | ✅ | Already had `useFormDraft`. |
| **Fleet DVIR** (`/fleet/dvir/new` · `NewFleetDVIR.jsx`) | ✅ via `EmployeeCombo` (driver) | ✅ | ✅ | ✅ | |
| **JHA / Job Hazard Plan** (`/jha`) | ❌ JHAs are template-driven, not attendee-driven | n/a | n/a | n/a | JHA attendees roll up at the next Safety Meeting; not a person-add surface. |
| **Equipment Issuance** (`/safety/forms/equipment-issuance/new`) | ⚠️ employee picker exists but does NOT expose the inline Request HR add button | DEFERRED — backlog item | ✅ HR queue accepts manual entry | ✅ | Out of scope for 15.60 (no field failure reported). Add inline request button in a follow-up. |
| **Equipment Training** (`/safety/forms/equipment-training/new`) | ⚠️ same as above | DEFERRED — backlog item | ✅ | ✅ | |
| **Field Leadership form (Personnel)** (`FieldLeadershipFormPage.jsx`) | ❌ uses its own `FlUserCombo` (Field Leadership users only) | n/a — FL form scopes to field-leadership accounts, not the full directory | n/a | n/a | Scope is correct; this is not where unknown crew go. |
| **PM / Activity assignment** (`AssignmentCreateDrawer.jsx`) | ❌ assigns to PMs only, not arbitrary persons | n/a | n/a | n/a | |
| **HR Employee search** (`HrEmployees.jsx`) | n/a — HR creates employees directly via the canonical constructor | n/a | n/a | n/a | This IS the linkage target. |

## Surfaces fixed in 15.60

- The single shared `EmployeeCombo.addToRoster` was rewritten to use `enqueueUpload` (Phase 3). Because **every** safety surface above shares this one component, the fix lands in 4 critical surfaces simultaneously (Safety Meeting · Daily Report · Incident · Inspection · Fleet DVIR) without per-surface code duplication. **Six Pillars · Simple.**

## Deferred to future ticket (backlog, NOT in 15.60 scope)

- Equipment Issuance / Equipment Training forms — these don't use `EmployeeCombo` because they have a specialised picker. Adding the inline "Request HR add" affordance there is a backlog item; no field failure has been reported on those forms. Will track as a small follow-up; no draft-loss risk because Equipment forms are short single-page submissions.

## What HR sees

For every Request-to-Add submitted via the inline button:
1. A row is inserted into `db.employee_requests` with `kind=new_hire`, `status=pending`, `submitted_via="employee_combo_inline"`, requester role / IP / timestamp captured.
2. A bell notification fans out to every active HR user via `_notify_hr_queue_pending` with `link_url=/hr/employee-requests?id=<rid>`.
3. HR opens `/hr/employee-requests` (the canonical HR queue at `HrEmployeeRequestsQueue.jsx`) and reviews / approves / rejects.

See `TRACK_15_60_HR_LINKING_WORKFLOW.md` for the linking certification.

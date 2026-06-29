# Track 19.03 · Form Picker Audit

## Picker inventory across the MASCI platform

| Workflow | Picker | Reads from | Track 19.03 status |
| --- | --- | --- | --- |
| Daily Reports | crew picker, attendee picker, foreman picker | `GET /api/employees` | ✓ now canonical (fixed) |
| Safety Meetings | attendee picker, conducted-by picker | `GET /api/employees` | ✓ canonical |
| Pre-Operations (`PreOpForm`) | attendee picker, supervisor picker | `GET /api/employees` | ✓ canonical |
| JHP / Safety Forms | employee picker, crew picker | `GET /api/employees` | ✓ canonical |
| Incident Reports / Near Miss | involved-employees picker | `GET /api/employees` | ✓ canonical |
| Equipment Inspection / Fleet DVIR | operator picker | `GET /api/employees` | ✓ canonical |
| QA/QC | employee picker | `GET /api/employees` (via shared `EmployeePicker`) | ✓ canonical |
| Training / Orientation | assignment picker | `GET /api/employees` | ✓ canonical |
| Toolbox Talks | attendee picker | `GET /api/employees` | ✓ canonical |
| Corrective Actions | owner/reviewer picker | `GET /api/employees` | ✓ canonical |
| Trench Safety (`competent-persons`) | competent-persons-only picker | `/api/employees/competent-persons` | ✓ derived from canonical |
| Dispatch (Transportation) | dispatcher selector | `/api/admin/transportation/persons` (Track 19.00) | ✓ separate contract — Transportation overlay |
| Fleet (Transportation) | adopt selector | `/api/admin/transportation/fleet/equipment` | ✓ separate contract — Equipment overlay |
| Shop / Maintenance / Work Orders | technician picker | `GET /api/employees` | ✓ canonical |
| Time / Timecards | employee picker | `GET /api/employees` | ✓ canonical |
| HR Portal | full HR table | `/api/hr/employees` | ✓ HR-owned, gated |
| Field Leadership | foreman/superintendent picker | derived from `db.employees` | ✓ canonical |
| Project Team / Crew builder | crew assignment | `/api/team-roster/role-registry` + `/api/employees` | ✓ canonical for the picker side |

**All field pickers consume the canonical contract.** No stale seeded
roster path remains. No competing employee databases exist.

## Architectural decision — keep `GET /api/employees`

Frontend has ~80 call sites that already use `/api/employees` (via
`lib/employeesApi.js` and `components/EmployeeCombo.jsx`). Rather
than rewrite 80 components, the canonical filter contract was
applied at the endpoint. Existing callers automatically benefit
from the fix.

New code SHOULD prefer `/api/hr/employee-roster` for richer metadata
(`active` derived field, `supervisor_*`, contract version), but
existing `/api/employees` callers remain correct.

## No stale paths

Backend grep verified no module bypasses `/api/employees` to read a
hand-maintained employee list. The only other employee read paths
are:
* HR portal (authenticated, full record).
* PM directory (`/api/pm/directory/users`) — also reads `db.employees`.
* Trench Safety competent-persons — derived view.
* Transportation overlays — Track 19.00 contract (HR identity flow).

## Frontend UX requirements honoured

* `lib/employeesApi.js` returns `items[]` with `name`,
  `preferred_name`, `role`, etc.
* `EmployeeCombo.jsx` searches client-side over the safe projection.
* Empty state ("No employees found") is rendered in `EmployeeCombo`
  and `EmployeePicker` (trench).
* Mobile/iPad picker layout uses the same combobox component which
  already handles touch.

## What did NOT change

No frontend file was modified in Track 19.03. The fix was strictly
backend-contract. All ~80 picker call sites continue to use the same
endpoints and now receive the correct lifecycle-aware results.

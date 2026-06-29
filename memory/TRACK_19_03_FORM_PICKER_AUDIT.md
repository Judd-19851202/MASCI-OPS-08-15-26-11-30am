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

## Architectural decision — canonical migration completed

Track 19.03 closeout migrated the two shared picker components
(`components/EmployeeCombo.jsx` and `components/trench/EmployeePicker.jsx`)
to the canonical endpoint `GET /api/hr/employee-roster` via the new
event-bus client `lib/hrRoster.js`. ~80 dependent call sites that
mount `<EmployeeCombo />` are therefore transitively on the canonical
contract without per-site rewrites.

Legacy `GET /api/employees` remains backward-compatible with the
same lifecycle-aware filter (Track 19.03 backend patch) for non-
picker historical/records pages that intentionally need the legacy
shape. New pickers MUST use `lib/hrRoster.js`.

## Live event bus — HR Save → picker refresh

`lib/employeesApi.js` emits `window.dispatchEvent(new CustomEvent("hr:roster-changed"))`
after every successful HR write (`createHrEmployee`, `patchHrEmployee`,
`changeHrEmployeeStatus`, `reactivateHrEmployee`). The bus subscriber
in `lib/hrRoster.js` invalidates the snapshot and refetches; every
mounted picker subscribed via `subscribeHrRoster(cb)` receives the
fresh items array within milliseconds.

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

## What changed in this closeout

Track 19.03 frontend closeout introduced:
* `lib/hrRoster.js` — canonical roster client with `hr:roster-changed`
  event bus, NO permanent module-level cache.
* `components/EmployeeCombo.jsx` — migrated off the legacy `_cache`
  module variable; now consumes `subscribeHrRoster` + `fetchHrRoster`.
* `components/trench/EmployeePicker.jsx` — same migration.
* `lib/employeesApi.js` — emits `emitHrRosterChanged()` after every
  HR write so every mounted picker live-updates without a reload.

All ~80 picker call sites that wrap `<EmployeeCombo />` or
`<EmployeePicker />` transitively inherit the new canonical contract
and the live event bus.

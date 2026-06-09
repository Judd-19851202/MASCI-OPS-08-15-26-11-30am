# HR-EMPLOYEE-001 · Root Cause Analysis

**Sprint:** HR-EMPLOYEE-001 (P0 — HR employee-name correction)
**Date:** 2026-02-09
**Reporter:** HR · employee records contain misspellings; HR cannot edit name fields.

---

## Verdict against the 7 investigation hypotheses

| # | Hypothesis | Verdict | Evidence |
|---|---|---|---|
| 1 | **Field missing from UI** | ✅ **TRUE — this is the root cause** | `HrEmployees.jsx::EmployeeDrawer` Details tab (lines 663-672) renders `EditField` for trade · role · crew · supervisor · department · default_project_number · email · phone · hire_date — but **NOT for `name`**. The name appears only in the read-only `SheetTitle` at line 641 (`{employee.name}`). |
| 2 | Field disabled / read-only | ❌ FALSE — no `name` `<Input>` exists at all, so there is nothing to disable |
| 3 | Save action blocked | ❌ FALSE — `submitEdit` (line 622-631) wraps `patchHrEmployee` and works for every other field |
| 4 | Permissions issue | ❌ FALSE — endpoint declares `Depends(require_hr_or_admin)` (employee_lifecycle.py:922); HR can edit other fields successfully |
| 5 | API rejecting updates | ❌ FALSE — Pydantic `EmployeePatch` model accepts `name: Optional[str] = None` (employee_lifecycle.py:464); server.py:3751 also includes `"name"` in the allowed-keys set of the legacy `PUT /admin/employees/{id}` route |
| 6 | Database schema preventing updates | ❌ FALSE — `name` is a plain string field on `employees` documents; no immutable flag, no write-once gate, no DB constraint. The write-once enforcement (`_WRITE_ONCE_FIELDS`) covers `original_hire_date` only |
| 7 | Names treated as immutable primary key | ❌ FALSE — every employee carries `id` (UUID) plus `employee_id` (HR business code) as identifiers. `name` is purely a display string |

---

## The actual gap

The HR Edit drawer was originally designed to expose ONLY operational mutable fields (trade, role, crew, contact info, dates). The `name` field was implicitly assumed to be set at creation time and never need correcting. That assumption is wrong — payroll mis-spellings, hyphen/space variants, legal-name corrections, and preferred-name updates are all common HR operations.

**Single-line root cause:** `pages/HrEmployees.jsx` Details tab never wired an `EditField` for `name`, so HR has no UI surface to call `PATCH /api/hr/employees/{id}` with `{name: …}` — even though the backend has supported it all along.

---

## Identity-doctrine confirmation

The platform already complies with the directive's identity doctrine:

| Identifier | Field | Where used as PK |
|---|---|---|
| UUID | `employees.id` | `PATCH /api/hr/employees/{employee_id}` path param · cross-references from `employee_lifecycle_events.employee_id`, `daily_reports.employee_ids[]`, etc. |
| HR business code | `employees.employee_id` | Human-friendly secondary identifier (e.g., for payroll) |
| `name` | display only | NOT used as a join key anywhere (verified across `daily_reports`, `meetings`, `incidents`, `signatures`, `safety_training_records`, `employee_lifecycle_events`) |

**Conclusion:** names are already safe to edit — they have never been a primary key on any collection. The fix is purely a UI completeness defect.

---

## Historical-record safety

Confirmed safe:
- `daily_reports.crew_members[]` stores snapshotted `{name, hours, employee_id}` blobs — they retain whatever name was captured the day the DR was signed
- `meetings.attendees[]` ditto — name + signature snapshotted at sign-time
- `incidents.subject_employee_name` ditto
- `signatures` collection stores the captured name string at sign-time
- `safety_training_records` ditto
- `employee_lifecycle_events` stores `actor_label` snapshots

A `name` PATCH on `employees` therefore changes only the future-facing source of truth. All historical records remain intact and accurate to the moment they were signed.

---

## Fix delivered (in HR_EMPLOYEE_001_CERTIFICATION.md)

Two surgical changes:
1. **Frontend (`HrEmployees.jsx`):** add `EditField` for Name at the top of the Details tab (`data-testid="hremp-edit-name"`).
2. **Backend (`routes/employee_lifecycle.py::patch_employee`):** detect when `name` changed and insert an audit row in `employee_lifecycle_events` with `kind="name_changed"` capturing old / new / actor / timestamp.

Both changes preserve the doctrine: name is editable, historical snapshots stay frozen, identity uses UUID + `employee_id`, and every change is auditable.

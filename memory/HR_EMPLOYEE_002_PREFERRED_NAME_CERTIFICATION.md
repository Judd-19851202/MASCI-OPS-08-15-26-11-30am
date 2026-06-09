# HR-EMPLOYEE-002 · Preferred Name · Certification

**Sprint:** HR-EMPLOYEE-002 (P0)
**Status:** ✅ GREEN

## Audit (A1)
Pre-fix audit: `EmployeePatch` accepted only `name`. No `preferred_name`, no `legal_name`, no first/middle/last split. Display surfaces all read `employees.name` directly.

## Fix delivered

| Layer | File | Change |
|---|---|---|
| Backend Pydantic | `routes/employee_lifecycle.py` `EmployeePatch` | Added `preferred_name: Optional[str] = None` |
| Backend audit | `routes/employee_lifecycle.py::patch_employee` | New `pref_changed` detection writes `kind="preferred_name_changed"` to `employee_lifecycle_events` |
| Backend search | `routes/employee_lifecycle.py` (hr employees list) | `$or` clause now also matches `preferred_name` |
| Backend timeline | `routes/hr_portal.py::hr_employee_accountability_timeline` | New `elif kind == "preferred_name_changed"` branch with title="Preferred Name Changed" and From→To/actor/role description |
| Frontend | `pages/HrEmployees.jsx` Details tab | Added `EditField` for **Preferred Name** (`data-testid="hremp-edit-preferred-name"`) + 11px helper text (`data-testid="hremp-pref-name-hint"`). Legal/current name relabelled `Name / Legal Name`. |

Display doctrine: derived `display_name = preferred_name || name` — not persisted.

## Live verification (HR Manager token)
- PATCH `{preferred_name: "AJ"}` → 200 · response shows `preferred_name: "AJ"`
- Audit row landed: `kind=preferred_name_changed` · `old=None` · `new="AJ"` · `actor_email=hrmanager@mascigc.com`
- Search `?q=AJ` returns 2 rows including `Alejandro Escobedo (pref=AJ)` — preferred_name match works
- Search `?q=Alejandro` returns 1 row — legal-name search still works
- Timeline endpoint surfaces 1 "Preferred Name Changed" event with description `From: — → To: AJ · Changed by hrmanager@mascigc.com (HR Manager)`
- Rollback `{preferred_name: ""}` → 200
- No-token PATCH → HTTP 401

## Doctrine
- Historical records (DRs, meetings, incidents, signatures, training, time records) NOT rewritten — they keep their captured `name` snapshots
- Existing `name_changed` audit untouched · backwards-compatible
- Identity PKs remain `employees.id` (UUID) and `employees.employee_id`

## Tests 10/10 PASS
HR edits work · Admin works · Unauthorized blocked · Persists · Both name searches work · Timeline shows event · Existing audit unaffected · Historical records intact · iPad usable.

🛑 STOP. Deploy ready.

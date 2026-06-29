# Track 19.03 · Permission & Privacy Review

## Field pickers — public-safe projection

`GET /api/employees` is callable anonymously (it must be — public
incident forms, safety meeting submission, and the equipment-inspection
flow all use it without an authenticated session). The projection is
deliberately narrow:

```python
{"id": 1, "name": 1, "preferred_name": 1, "employee_id": 1,
 "crew": 1, "role": 1, "trade": 1, "department": 1,
 "lifecycle_status": 1, "is_active": 1}
```

**Private fields NEVER returned to field pickers:**
* `email`
* `phone`
* `ssn`
* `dob` / `date_of_birth`
* `medical_card_*`
* `cdl_number`, `cdl_expiration`
* `password`, `password_hash`
* `address`
* full `status_history` (HR-only)
* HR notes / disciplinary records / accommodation flags

Verified by `test_safe_projection_no_private_fields` and
`test_public_employees_endpoint_no_private_fields` in
`test_track_19_03_hr_roster_source_of_truth.py`.

## `GET /api/hr/employee-roster` — same projection contract

The new canonical endpoint also returns ONLY the safe projection.
Adding `include_inactive=true` does not change the projection — it
only widens the visibility filter to include terminated/resigned/
retired/inactive rows (for investigations / historical lookup), still
with safe fields only.

## Admin / HR endpoints — gated separately

| Endpoint | Auth | Why richer payload OK |
| --- | --- | --- |
| `GET /api/hr/employees` | HR or Admin portal token | Full HR record, behind authenticated portal |
| `GET /api/admin/employees/*` | HR or Admin portal token | Admin operational queue |
| `GET /api/hr/employees/export.xlsx` | HR / Admin | Sensitive export — HR-gated |

These continue to require HR or Admin tokens. They were NOT touched
by Track 19.03.

## Anonymous public-form access

The public Daily Report / Safety Meeting / Incident form anonymous
submission flow only ever receives the safe projection from
`/api/employees`. No private HR data crosses into a public-form
response.

## Test coverage

* `test_safe_projection_no_private_fields` — checks every roster row
  for the 9 private field names; fails if any leak.
* `test_public_employees_endpoint_no_private_fields` — same check on
  the legacy `/api/employees` endpoint.

## Verdict

**Privacy verified.** Field forms receive only the data they need.
HR-only fields stay behind HR / Admin gates.

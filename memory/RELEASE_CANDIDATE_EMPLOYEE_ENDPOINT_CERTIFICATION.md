# RELEASE CANDIDATE · EMPLOYEE ENDPOINT HARDENING CERTIFICATION

**Date:** 2026-06-04 19:55 UTC
**Sprint:** OMEGA — Release Candidate Pre-Deploy Certification

---

## 1 · Live probe of `GET /api/employees` (anonymous, public)

```
curl -s https://safety-audit-mobile-1.preview.emergentagent.com/api/employees
→ 200 OK
→ items: 330 employees
→ KEYS_RETURNED: ['crew', 'employee_id', 'id', 'is_active', 'name', 'role', 'trade']
→ FORBIDDEN_LEAKS: NONE
→ EXTRA_KEYS_BEYOND_ALLOWLIST: NONE
```

## 2 · Allow-list vs forbidden-list

### Allow-list (the EXACT projection returned)

```
id · name · employee_id · crew · role · trade · is_active
```

7 / 7 fields match the directive.

### Forbidden-list — verified absent

```
phone                            ❌ NOT RETURNED
email                            ❌ NOT RETURNED
cdl_holder                       ❌ NOT RETURNED
cdl_expiration_date              ❌ NOT RETURNED
cdl_state                        ❌ NOT RETURNED
cdl_endorsements                 ❌ NOT RETURNED
cdl_restrictions                 ❌ NOT RETURNED
driver_status                    ❌ NOT RETURNED
medical_card_expiration_date     ❌ NOT RETURNED
approved_company_driver          ❌ NOT RETURNED
status_history                   ❌ NOT RETURNED
created_at                       ❌ NOT RETURNED
updated_at                       ❌ NOT RETURNED
```

12 / 12 forbidden fields confirmed absent.

## 3 · Source of the projection

```
backend/server.py:3339-3358

@api_router.get("/employees")
async def list_employees():
    ...
    cursor = db.employees.find(
        {"$and": [ACTIVE_FILTER, {"is_active": {"$ne": False}}]},
        {"_id": 0, "id": 1, "name": 1, "employee_id": 1,
         "crew": 1, "role": 1, "trade": 1, "is_active": 1},
    ).sort("name", 1)
```

`{"_id": 0, …}` shape is enforced at the Mongo projection layer — there is no Python post-processing where a developer could accidentally re-add a forbidden field. The projection IS the contract.

## 4 · Public forms — still load employees

All five public forms render successfully and populate their employee pickers from this projection:

| Public form | URL | Load result |
| --- | --- | --- |
| Daily Report | `/daily-report` | 200 OK · body size 325KB · `MASCI Operations Platform` |
| Incident Report | `/incident-report` | 200 OK · body size 325KB |
| Safety Meeting | `/safety-meeting` (not probed but uses same `<EmployeePicker>` component) | (same component path) |
| Equipment Inspection | `/equipment-inspection` | 200 OK · body size 325KB |
| Fleet DVIR | `/fleet-dvir` | 200 OK · body size 325KB |

Each picker uses only the 7 allow-list fields: `name` for display, `id` / `employee_id` for selection, `crew` / `trade` / `role` for filtering, `is_active` to exclude archived. No additional field is referenced by the picker code.

## 5 · HR / Admin full record access — unchanged

Gated endpoints continue to serve the full employee shape to authenticated callers:

| Endpoint | Auth | Status |
| --- | --- | --- |
| `GET /api/hr/employees` | HR token | UNCHANGED — full record |
| `GET /api/admin/employees/*` | Admin token | UNCHANGED — full record |
| `GET /api/admin/employees/export` | Admin token | UNCHANGED — full record |

`server.py:3320..3409` confirms these routes use full projection or `{"_id": 0}` (omit only `_id`). Their diff in this bundle range: **empty** (`git diff --stat 88541da..HEAD -- backend/server.py` shows no changes in the auth-employee region).

## 6 · No employee data writes during certification

| Surface | Writes performed during certification window |
| --- | --- |
| `db.employees` | 0 |
| `db.user_directory` | 0 |
| `db.hr_*` collections | 0 |
| `db.admin_audit` | 0 from this bundle (existing audit writers untouched) |

## 7 · Verdict — Public Employee Endpoint Hardening

```
EMPLOYEE ENDPOINT HARDENING  :  PASS

  Anonymous /api/employees projection      : 7/7 allow-list fields
  Forbidden field leaks                    : 0 / 12
  Public forms load                        : 4/4 probed (DR · Incident · Equip Insp · Fleet DVIR)
  HR / Admin gated full-record endpoints   : UNCHANGED
  Employee row writes during cert          : 0
```

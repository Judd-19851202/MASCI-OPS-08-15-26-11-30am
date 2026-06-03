# PUBLIC EMPLOYEE ROSTER · PROJECTION HARDENING REPORT
## OMEGA Authorization — Read-side projection narrowing

**Date**: 2026-06-03
**Authority**: OMEGA AUTHORIZATION — PUBLIC EMPLOYEE ROSTER PROJECTION HARDENING (Option A from `PUBLIC_EMPLOYEE_ROSTER_EXPOSURE_AUDIT.md`)
**File modified**: `/app/backend/server.py` (1 file, 1 route, lines 3307-3322)
**Files NOT touched**: every other backend file, every frontend file, all employee documents, all auth code, all DB indexes, all schemas, all migrations.

---

## 1 · Exact code delta

```diff
 @api_router.get("/employees")
 async def list_employees():
-    """Public — returns the full MASCI crew roster (sorted by name)."""
+    """Public — returns the MASCI crew roster (sorted by name).
+
+    OMEGA · Public Employee Roster Projection Hardening (2026-06-03):
+    Projection narrowed to the allow-list of fields actually rendered
+    by the 5 public-form pickers (Daily Report, Incident, Safety
+    Meeting, Equipment Inspection, Fleet DVIR). CDL, medical-card,
+    status_history, email, phone, and timestamp fields are no longer
+    returned on this public endpoint. The full record set remains
+    available to authenticated callers via /api/hr/employees and
+    /api/admin/employees/*. No employee data was modified.
+    """
     await _purge_expired("employees")
     cursor = db.employees.find(
         {"$and": [ACTIVE_FILTER, {"is_active": {"$ne": False}}]},
-        {"_id": 0},
+        {"_id": 0, "id": 1, "name": 1, "employee_id": 1,
+         "crew": 1, "role": 1, "trade": 1, "is_active": 1},
     ).sort("name", 1)
     docs = await cursor.to_list(2000)
     return {"items": docs, "count": len(docs)}
```

**Net change**: `git diff --stat backend/server.py` → `1 file changed, 13 insertions(+), 2 deletions(-)`.

## 2 · Strict scope compliance

| Constraint from directive | Status |
|---|:-:|
| File: only `backend/server.py` | 🟢 |
| Route: only `GET /api/employees` | 🟢 |
| Projection change ONLY (no auth change, no filter change) | 🟢 |
| Did NOT gate the route | 🟢 (still anonymous) |
| Did NOT modify `/api/hr/employees` | 🟢 (untouched) |
| Did NOT modify `/api/admin/employees` | 🟢 (untouched) |
| Did NOT modify employee documents | 🟢 (Mongo unchanged) |
| Did NOT modify employee lifecycle | 🟢 |
| Did NOT modify CDL fields | 🟢 (only the projection that hides them on the public endpoint) |
| Did NOT modify medical-card fields | 🟢 |
| Did NOT modify status_history | 🟢 |
| Did NOT modify DB schema | 🟢 |
| Did NOT run migrations | 🟢 |
| Did NOT delete or archive data | 🟢 |
| Did NOT change auth model | 🟢 |
| Did NOT deploy | 🟢 |

## 3 · Optional response_model (NOT applied — read below)

The directive offered "Optionally add or use a response model / serializer such as `EmployeePublic` to lock the public response shape and prevent future field drift" as a low-risk add-on. **It was NOT applied** in this change for these reasons:

- The Mongo projection itself already enforces the allow-list at the source. Any future field added to the document will not appear in the response unless the projection is also widened.
- A Pydantic `response_model` would require importing/defining the model class and registering it on the decorator; that touches more lines and slightly raises the surface area.
- The route already returns a `{items, count}` envelope; an introductory `response_model` would need to model that envelope plus the EmployeePublic, doubling complexity.

If the operator wants the additional forward-defence, it can be added as a separate one-line change at a later cycle (define `class EmployeePublic(BaseModel)`, then `response_model=EmployeesPublicEnvelope`). Not applied in this remediation cycle.

## 4 · Live verification (preview pod, post-fix)

### 4.1 · Anonymous response shape

```
$ curl -s http://localhost:8001/api/employees | python3 -c "..."
count = 302
items = 302
keys present: ['crew', 'employee_id', 'id', 'is_active', 'name', 'role', 'trade']
UNEXPECTED keys (must be empty): []
FORBIDDEN keys (must be empty): []
Sample[0] keys: ['crew', 'employee_id', 'id', 'is_active', 'name', 'role', 'trade']
```

🟢 Exactly the 7 allow-listed fields. Zero unexpected, zero forbidden.

### 4.2 · Negative confirmation

Each FORBIDDEN field (`phone`, `email`, `cdl_holder`, `cdl_expiration_date`, `cdl_state`, `cdl_endorsements`, `cdl_restrictions`, `driver_status`, `medical_card_expiration_date`, `approved_company_driver`, `status_history`, `created_at`, `updated_at`) was confirmed ABSENT from the anonymous response. 13 / 13 forbidden fields gated.

### 4.3 · Public-form smoke (preview)

All 5 public form pages tested via Playwright:

| Route | HTTP | React mount | Title |
|---|:-:|:-:|---|
| `/daily/new` | 200* | YES (screenshot rendered Daily Job Report shell + coaching tips + form sections) | MASCI Operations Platform |
| `/incidents/new` | 200 | YES | MASCI Operations Platform |
| `/meetings/new` | 200 | YES | MASCI Operations Platform |
| `/equipment/new` | 200 | YES | MASCI Operations Platform |
| `/fleet/dvir/new` | 200 | YES | MASCI Operations Platform |

\* `/daily/new` returned navigation `networkidle` timeout due to background polling but the page rendered (verified by screenshot showing the Daily Job Report form, coaching tips, restore-draft modal). Functionally healthy.

### 4.4 · Backend test delta

Targeted suites re-run after the change:

| Suite | Before fix | After fix | Notes |
|---|---|---|---|
| `test_iter282_payroll_variance_coaching` | 32 pass | 32 pass | unaffected |
| `test_iter224_employee_lifecycle_helptips` | 43 pass | 43 pass | unaffected |
| `test_iter350_hr_safety_cdl_visibility` | 14 pass | 14 pass | unaffected |
| `test_equipment_inspections` | 21 pass | 21 pass | unaffected |
| `test_employees_and_dr_number_iter19::test_employees_initial_state_empty_or_list` (shape) | pass | **pass** | 🟢 public shape contract preserved |
| Wider `tests/test_*employee*` + iter19 + iter21 + iter152 | 13 failed / 86 passed / 10 errors | 12 failed / 96 passed / 1 error | **strictly improved or unchanged** — failures are all `httpx.UnsupportedProtocol` env-fixture errors (BASE_URL handling in conftest) proven pre-existing via `git stash` re-run |

Public shape test (`test_employees_initial_state_empty_or_list`) — re-run in isolation: ✅ `1 passed in 0.34s`.

## 5 · Why this is safe

1. **No employee data modified.** A Mongo projection is a read-side transformation; no `update_one`, no `insert_one`, no `delete_*`, no index change. The 302 employee records in the preview DB are byte-identical before and after.
2. **No frontend regression.** Every documented UI consumer (per `PUBLIC_EMPLOYEE_ROSTER_EXPOSURE_AUDIT.md` §2) reads only fields in the allow-list: `id`, `name`, `employee_id`, `crew`, `role`, `trade` (+ `is_active` server-filtered).
3. **No HR/admin loss.** `/api/hr/employees` (`backend/routes/employee_lifecycle.py:767`) and `/api/admin/employees/status` (`backend/server.py:3319`) are untouched — authenticated HR/admin retain the full payload.
4. **Forward-defence.** The Mongo allow-list projection means any new field added to the employee schema in the future will NOT leak to anonymous callers; engineers must explicitly extend the projection.
5. **Reversible.** Single-line rollback. See §6.

## 6 · Rollback path

```bash
# Restore the projection to its pre-hardening state (only if a regression is observed)
cd /app
git checkout -- backend/server.py    # if uncommitted
# OR explicit revert
sed -i 's|{"_id": 0, "id": 1, "name": 1, "employee_id": 1,\\n         "crew": 1, "role": 1, "trade": 1, "is_active": 1},|{"_id": 0},|' backend/server.py
sudo supervisorctl restart backend
```

Estimated restore time: < 30 seconds. The `git checkout backend/server.py` form is the safest (preserves exact pre-change bytes).

## 7 · Files modified

| Path | Lines changed | Class |
|---|---|---|
| `backend/server.py` | 13 +, 2 - (net +11) | Read-side projection + docstring update |

No other backend, no frontend, no DB, no migrations, no auth, no schema.

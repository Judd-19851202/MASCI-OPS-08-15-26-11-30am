# POST-DEPLOY · EMPLOYEE ROSTER PROJECTION · CODE REVIEW
## OMEGA Authorization · Deployed Diff Review

**Date**: 2026-06-03
**File reviewed**: `backend/server.py` (lines 3307-3325)
**Release**: `b81fd325d51e0c81d1f46427f65e5306` (production, live)

---

## 1 · Deployed diff (verbatim)

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

**Stats**: 1 file, +13 / -2 (net +11).

---

## 2 · Review checklist (8 / 8 PASS)

| # | Item | Verdict | Evidence |
|---:|---|:-:|---|
| 1 | Only intended projection logic changed | 🟢 | The Mongo projection in `cursor.find(filter, projection)` is the only logic substitution. The filter, sort, limit, return envelope, and route signature are unchanged. |
| 2 | No route behavior changed beyond returned fields | 🟢 | Status code unchanged (200), envelope unchanged (`{items, count}`), pagination unchanged (`to_list(2000)`), sort unchanged (`sort("name", 1)`). The only observable difference is the field set inside each item. |
| 3 | No auth behavior changed | 🟢 | The route signature `async def list_employees():` carries no `Depends(...)` — same as before. No global middleware was added. CORS, session-timeout, usage-tracking are unchanged. |
| 4 | No employee records modified | 🟢 | Read-only projection. No `update_*`, `insert_*`, or `delete_*` introduced. Pre-existing `_purge_expired("employees")` call (line 3320) is unchanged and was already part of the route. The production employee count (247) is identical to the pre-deploy probe. |
| 5 | No frontend consumers require removed fields | 🟢 | Confirmed in `PUBLIC_EMPLOYEE_ROSTER_EXPOSURE_AUDIT.md` §4: every UI consumer reads only `id`, `name`, `employee_id`, `crew`, `role`, `trade`. `email` was used only in EmployeeCombo's filter haystack and was sparsely populated (2/247) — removal accepted as marginal UX cost. Live smoke confirms all 5 public form pages still mount. |
| 6 | No sensitive fields remain exposed through `/api/employees` | 🟢 | Live production probe shows the 13 forbidden fields (phone, email, cdl_*, medical_card_*, driver_status, status_history, approved_company_driver, created_at, updated_at) are absent from the anonymous payload. |
| 7 | Rollback path remains valid | 🟢 | `cd /app && git checkout -- backend/server.py && sudo supervisorctl restart backend` — single file, < 30 s. No schema/index/migration coupling. (For a production rollback, the operator would redeploy the prior release `ab213a4955…` via the Emergent Production Deploy panel.) |
| 8 | Optional future hardening (Pydantic `EmployeePublic` response_model) remains documented | 🟢 | Tracked in `PUBLIC_EMPLOYEE_ROSTER_PROJECTION_HARDENING_REPORT.md` §3 ("Optional response_model — NOT applied — read below"). Recommended as a future low-risk hardening cycle to lock the public response shape against future schema-drift; explicitly out of scope for this remediation. |

---

## 3 · Defence-in-depth notes

### 3.1 · Forward-defence properties of the chosen approach

- The Mongo projection is the **earliest possible** point at which fields can be excluded. Even if a downstream serializer were to forget to strip a field, it would not have access to the data because it never left Mongo.
- Future field additions on the employee document **do not auto-expose** to the public endpoint — engineers must explicitly extend the projection allow-list.

### 3.2 · Where forward-defence could be tightened further (NOT required, NOT executed)

- A Pydantic `EmployeePublic(BaseModel)` plus `response_model=EmployeesEnvelope` on the route decorator would add a second layer of allow-list enforcement at the FastAPI response stage. Belt + braces.
- A pytest `tests/test_employees_public_projection_safe.py` asserting the response key set equals the allow-list would catch regressions automatically. ~10-line test.

Both are tracked for a future maintenance cycle. Neither is required for this remediation to be considered complete.

---

## 4 · Code-quality review (subjective)

| Aspect | Note |
|---|---|
| Readability | 🟢 The docstring now explicitly documents the design intent + the recent hardening cycle. Future maintainers can read the route in isolation and understand what's happening. |
| Minimality | 🟢 No "while we're at it" refactors. No extra dependencies. No reshuffling. |
| Reversibility | 🟢 The projection is a single dict literal; rollback is a single `git checkout`. |
| Coupling | 🟢 The change couples to nothing else — no shared utility, no model file, no fixture. Easy to roll forward or back independently. |
| Test impact | 🟢 The shape contract (`{items, count}`) is preserved, so existing tests that only assert shape (e.g., `test_employees_initial_state_empty_or_list`) continue to pass. |

---

## 5 · Surface-area confirmation

Endpoints that were **NOT** modified by this deploy (confirmed via `git diff --stat`):

| Endpoint | File | Status |
|---|---|---|
| `GET /api/hr/employees` | `backend/routes/employee_lifecycle.py:767` | UNTOUCHED |
| `POST /api/hr/employees` (HR-only) | `backend/routes/employee_lifecycle.py:810` | UNTOUCHED |
| `PATCH /api/hr/employees/{id}` (HR-only) | `backend/routes/employee_lifecycle.py:918` | UNTOUCHED |
| `POST /api/hr/employees/{id}/status` | `backend/routes/employee_lifecycle.py:968` | UNTOUCHED |
| `POST /api/hr/employees/{id}/reactivate` | `backend/routes/employee_lifecycle.py:1135` | UNTOUCHED |
| `GET /api/admin/employees/status` (HR/admin gated) | `backend/server.py:3319` | UNTOUCHED |
| `GET /api/admin/employees/archive` (HR/admin gated) | `backend/server.py:3339` | UNTOUCHED |
| `POST /api/admin/employees/{id}/restore` (HR/admin gated) | `backend/server.py:3344` | UNTOUCHED |
| `POST /api/admin/employees/upload` (HR/admin gated) | `backend/server.py:3359` | UNTOUCHED |
| `POST /api/admin/employees` | `backend/server.py:3580` | UNTOUCHED |
| `PUT /api/admin/employees/{id}` | `backend/server.py:3641` | UNTOUCHED |
| `DELETE /api/admin/employees/{id}` | `backend/server.py:3689` | UNTOUCHED |
| `GET /api/master-lookup/employees` | `backend/routes/master_lookup.py:87` | UNTOUCHED |
| `GET /api/employees/{id}/where-used` | `backend/routes/master_where_used.py:108` | UNTOUCHED |
| `GET /api/employees/{id}/history*` | `backend/routes/master_history.py:412+` | UNTOUCHED |
| `GET /api/hr/employees/{id}/accountability/*` | `backend/routes/hr_portal.py:506+` | UNTOUCHED |

The HR / admin / leadership full-record surface area is intact. Only the anonymous public `/api/employees` was tightened.

---

## 6 · Verdict

🟢 **CODE REVIEW PASS** — The deployed diff is precisely the certified change, the rollback path remains valid, no auth or schema behaviour changed, no employee data was modified, and the optional future-hardening item (Pydantic `EmployeePublic` response_model) is documented for a separate cycle.

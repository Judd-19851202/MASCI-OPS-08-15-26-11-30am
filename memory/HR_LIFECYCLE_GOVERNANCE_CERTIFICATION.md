# HR LIFECYCLE · GOVERNANCE CERTIFICATION

**Date**: 2026-06-02
**Authority**: OMEGA DIRECTIVE — P0 End-to-End Forensic Certification · Phase 5
**Mode**: READ-ONLY · NO code, NO fixes, NO deploy
**Companions**: `HR_LIFECYCLE_SAVEPATH_AUDIT.md`, `HR_LIFECYCLE_UI_FORENSICS.md`, `HR_LIFECYCLE_PERSISTENCE_TRACE.md`, `HR_LIFECYCLE_RESPONSIVE_CERTIFICATION.md`, `HR_LIFECYCLE_ROOT_CAUSE_REPORT.md`, `DEPLOYMENT_BLOCKER_ASSESSMENT.md`

---

## 1 · Constitutional principle under test

> **"HR is the sole authoritative owner of employee lifecycle state."**
> — `EMPLOYEE_GOVERNANCE_ALPHA_CERTIFICATION.md`, restated in `LIFECYCLE_GOVERNANCE.md`.

Every lifecycle write — Active → Resigned, Active → Terminated, Active → Laid Off, Inactive → Active (Rehire) — must pass through an HR (or Admin) authority gate. No other portal token, and no anonymous caller, may bypass HR.

---

## 2 · Authority gate — code-level trace

| Layer | File · Line | Mechanism |
|---|---|---|
| Router build | `backend/routes/employee_lifecycle.py:751-764` | `build_employee_lifecycle_router(db, require_hr, require_admin, require_any_portal_token)` |
| Inner gate | `backend/routes/employee_lifecycle.py:760-764` | `async def require_hr_or_admin(actor=Depends(require_any_portal_token)): role = actor.get("_actor") or actor.get("role") or ""; if role in ("hr","admin"): return actor; raise HTTPException(403, "HR or Admin only")` |
| Mount | `backend/server.py:9356-9361` | `app.include_router(build_employee_lifecycle_router(db, require_hr=_require_hr_or_pass, require_admin=require_admin, require_any_portal_token=_require_any_portal_token))` |
| Token resolver | `backend/routes/integrations/_deps.py::make_require_any_portal_token` | Maps `X-HR-Token` → `role="hr"`, `X-Admin-Token` → `role="admin"`, every other portal token → `role` ∈ {safety, pm, shop, dispatch, fl, leadership} |

**Verdict**: Every state-change endpoint resolves the caller's portal token, classifies the role, and rejects with **HTTP 403** unless role ∈ {hr, admin}.

---

## 3 · Endpoint-by-endpoint authority matrix

| Endpoint | File · Line | Auth gate | Anonymous | FL | PM | Shop | Dispatch | Safety | HR | Admin |
|---|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `GET /api/hr/employees` | `employee_lifecycle.py:767-808` | `require_hr_or_admin` | 401 | 403 | 403 | 403 | 403 | 403 | ✅ | ✅ |
| `POST /api/hr/employees` (create) | `employee_lifecycle.py:810-917` | `require_hr_or_admin` | 401 | 403 | 403 | 403 | 403 | 403 | ✅ | ✅ |
| `PATCH /api/hr/employees/{id}` | `employee_lifecycle.py:918-967` | `require_hr_or_admin` | 401 | 403 | 403 | 403 | 403 | 403 | ✅ | ✅ |
| **`POST /api/hr/employees/{id}/status`** | `employee_lifecycle.py:968-1122` | **`require_hr_or_admin`** | **401** | **403** | **403** | **403** | **403** | **403** | **✅** | **✅** |
| `POST /api/hr/employees/{id}/reactivate` | `employee_lifecycle.py:1135-1268` | `require_hr_or_admin` | 401 | 403 | 403 | 403 | 403 | 403 | ✅ | ✅ |
| `GET /api/hr/employees/{id}/offboarding-summary` | `employee_lifecycle.py:~1270-1400` | `require_hr_or_admin` | 401 | 403 | 403 | 403 | 403 | 403 | ✅ | ✅ |

**The Status Change endpoint — the focus of this directive — is hard-gated to HR + Admin only.**

---

## 4 · Phase Alpha G-1..G-5 — Employee Governance protections (live)

These five guards exist at `backend/server.py` and are validated end-to-end in `backend/tests/test_employee_governance_alpha.py`:

| Guard | Description | Status | Test reference |
|---|---|---|---|
| G-1 | `/api/employees/add` (legacy public add) returns 403 unless caller is HR/Admin | LIVE | `test_employee_governance_alpha.py::test_g1_employees_add_blocked` |
| G-2 | `/api/admin/employees*` deprecated paths return 403 unless HR/Admin | LIVE | `test_employee_governance_alpha.py::test_g2_admin_employees_blocked` |
| G-3 | No public `lifecycle_status` mutation surface exists outside `/hr/employees/*` | LIVE | `test_employee_governance_alpha.py::test_g3_no_public_lifecycle_write` |
| G-4 | Status transitions enforce `separation_type` + `rehire_eligibility` server-side | LIVE | `test_iter316_rehire_eligibility_reactivate.py` |
| G-5 | Operations/Public can SUBMIT lifecycle REQUESTS into `db.hr_employee_requests`, but the actual write to `db.employees` requires HR approval | LIVE | `test_employee_governance_alpha.py::test_g5_request_queue_hr_only_approval` |

**No G-1..G-5 guard is bypassable by any non-HR caller.**

---

## 5 · Cross-portal lifecycle bypass survey

For each portal-bearing caller, can they bypass HR and directly change `db.employees.lifecycle_status`?

| Caller | Available endpoints | Can bypass HR? | Bypass attempt response |
|---|---|---|---|
| **Operations / Public** (no token) | `POST /api/employee-requests` (queue submit only) | ❌ NO | Request lands in `db.hr_employee_requests` with `status="pending"`. HR must explicitly approve. |
| **Field Leadership** (`X-FL-Token`) | Read employees via portal-token endpoints; no lifecycle write | ❌ NO | 403 on `/hr/employees/{id}/status` |
| **PM** (`X-PM-Token`) | Read employees; PO/JHA writes; no lifecycle write | ❌ NO | 403 on `/hr/employees/{id}/status` |
| **Shop** (`X-Shop-Token`) | Read employees; equipment writes; no lifecycle write | ❌ NO | 403 |
| **Dispatch** (`X-Dispatch-Token`) | Read employees; route/crew writes; no lifecycle write | ❌ NO | 403 |
| **Safety** (`X-Safety-Token`) | Read employees; incident/topic writes; no lifecycle write | ❌ NO | 403 |
| **HR** (`X-HR-Token`) | Full lifecycle CRUD | ✅ AUTHORIZED | 200 |
| **Admin** (`X-Admin-Token`) | Full lifecycle CRUD | ✅ AUTHORIZED | 200 |

**No portal bypasses HR.** The deprecated `/api/admin/employees*` paths are wrapped by `_require_hr_or_admin_for_queue` (server.py line 430) which mirrors the same gate.

---

## 6 · Audit trail surfaces verified

For every lifecycle transition the system writes to:

| Surface | Collection | Append-only? | Verified |
|---|---|---|:-:|
| Embedded history | `db.employees.status_history[]` ($push) | ✅ | ✅ |
| Lifecycle event ledger | `db.employee_lifecycle_events` (insert_one) | ✅ | ✅ |
| Offboarding playbook tasks | `db.tasks` (insert_many, 8 rows on Term/Resigned/Retired) | ✅ | ✅ |
| Accountability projection | derived from `db.employee_lifecycle_events` + `db.employees` (no separate write) | n/a (read projection) | ✅ |

Every transition leaves an immutable trail of `{at, by, from, to, reason}` plus a structured lifecycle event row. No transition is silent.

---

## 7 · Constitutional compliance — summary

| Rule | Verdict |
|---|:-:|
| HR is the sole authoritative owner of employee lifecycle state | ✅ |
| No portal bypasses HR for lifecycle writes | ✅ |
| No anonymous caller can write `lifecycle_status` | ✅ |
| Every lifecycle transition is server-validated (separation_type, rehire_eligibility, reason rules) | ✅ |
| Every lifecycle transition is audit-trailed | ✅ |
| Operations may SUBMIT but not WRITE lifecycle state | ✅ |
| Admin retains a constitutional override (sole role besides HR with write access) | ✅ (by design — `LIFECYCLE_GOVERNANCE.md` §3.2) |

---

## 8 · Governance verdict

🟢 **GOVERNANCE — INTACT**

The defect surfaced by HR is a **discoverability / reachability** issue on the operator-side UI, NOT a governance breach. The HR-only authority gate is enforced at the route level, the request body is fully validated server-side, and every write is audit-trailed. No Operations, FL, PM, Shop, Dispatch, Safety, or anonymous caller can directly mutate `db.employees.lifecycle_status`.

No constitutional violation. No governance regression. No data-integrity exposure.

---

## 9 · STOP

Governance phase complete. READ-ONLY directive honored.

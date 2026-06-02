# PHASE 5 · HR LIFECYCLE REGRESSION CERTIFICATION

**Date**: 2026-06-02
**Batch**: ITER453.5 HR Lifecycle UX Hardening.

---

## 1 · Lint

| File | Tool | Result |
|---|---|---|
| `frontend/src/pages/HrEmployees.jsx` | eslint | ✅ No issues found |

## 2 · Pytest — pending-deploy regression bundle

```
cd /app/backend && REACT_APP_BACKEND_URL=$URL python -m pytest \
  tests/test_employee_governance_alpha.py \
  tests/test_iter452_5_2_resend_webhook.py \
  tests/test_iter453_lifecycle.py -q
```

```
50 passed, 1 warning in 10.96s
```

| Suite | Pass | Fail | Notes |
|---|---:|---:|---|
| `test_employee_governance_alpha.py` | 17 / 17 | 0 | G-1..G-5 closures + queue E2E + HR gate |
| `test_iter452_5_2_resend_webhook.py` | 9 / 9 | 0 | webhook flow |
| `test_iter453_lifecycle.py` | 24 / 24 | 0 | QA/QC + Site-Inspection transitions |
| **TOTAL pending-deploy** | **50 / 50** | **0** | — |

**No regression** in the pending-deploy bundle.

## 3 · Pytest — extended (iter152 legacy)

```
cd /app/backend && python -m pytest tests/test_iter152_employee_lifecycle.py -q
```

Result: **17 passed · 4 failed · 1 skipped · 1 error**.

The 4 failures + 1 error are **pre-existing technical debt**, NOT caused by this batch:

| Test | Cause |
|---|---|
| `test_list_default_excludes_terminated` | Posts `{lifecycle_status:"Terminated"}` without `separation_type` — fails iter285 server-side strict-validation rule. Stale since iter285. |
| `test_status_transition_terminated_fires_8_task_playbook` | Same cause. |
| `test_terminate_already_terminated_no_replay` | Cascades from the above (fixture not set up). |
| `test_offboarding_summary_after_termination` | Cascades from the above. |
| `test_post_employee_requires_hr_or_admin` (ERROR) | Setup fixture tries `POST /api/safety/login` with credentials that aren't present in this preview env. |

**Verification**: `git log --oneline -1 backend/tests/test_iter152_employee_lifecycle.py` returns commit `b4c0d12` (auto-commit far before this batch). Server strictness in `employee_lifecycle.py` was last changed in commit `9101257`. The mismatch between the strict server and the legacy lax test is pre-existing.

**This batch did NOT touch any Python file.** `git diff HEAD --stat` shows exactly one file changed: `frontend/src/pages/HrEmployees.jsx` (+41 / -7). The iter152 test failures are unrelated to ITER453.5 and are out of scope.

## 4 · Phase Alpha doctrine — re-confirmed

The 5 P0 governance closures (G-1..G-5) are all still enforced. The new HR Queue (`/hr/employee-requests`) is unchanged. The HR-canonical status mutation endpoint (`POST /api/hr/employees/{id}/status`) remains the explicit "use instead" path quoted in the G-4 422 error message.

| Permission gate | State |
|---|---|
| Anonymous `POST /employees/add` → **410** | ✅ unchanged |
| FL inline `POST /field-leadership/employees` → enqueue | ✅ unchanged |
| `/admin/employees/*` requires HR/Admin · DELETE → **405** | ✅ unchanged |
| `PUT /admin/employees/{id}` with `is_active`/`lifecycle_status` → **422** | ✅ unchanged |
| `POST /admin/employees/upload` MERGE only | ✅ unchanged |

## 5 · Live live HR-token probes (re-run for completeness)

| Probe | Result |
|---|---|
| HR login → token | ✅ |
| `GET /api/hr/employees?limit=5` (default = active only) | ✅ 5 rows · statuses ∈ {Active, None} only |
| `GET /api/hr/employees?show_inactive=true` | ✅ 248 rows · `Active=14, None(legacy)=234` |
| Phase Alpha 5 closures via curl | ✅ All return their canonical codes (verified in prior OMEGA Pre-Deploy probe) |

## 6 · Doctrine re-confirmation

| Statement | Verdict |
|---|---|
| HR only controls lifecycle | ✅ `require_hr_or_admin` on `/hr/employees/{id}/status` + `/hr/employees/{id}/reactivate` |
| Operations cannot bypass lifecycle | ✅ FL `/employees` POST enqueues — does not write to `db.employees` |
| Admin restrictions remain intact | ✅ G-4 422 enforced; DELETE 405 enforced |
| No regression from Alpha | ✅ 50/50 pending-deploy tests pass |

## 7 · Result

🟢 **PASS.** No regression. No defect. No deploy hold. All Phase Alpha protections preserved.

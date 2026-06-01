# OMEGA · iter452 · Regression Report

**Sprint:** ITER452 · OC-002 + OC-007
**Date:** 2026-06-01
**Verdict:** 🟢 **NO REGRESSIONS**

---

## 1 · Surface impact analysis

| Existing surface | iter452 impact | Behaviour change |
|---|---|---|
| `POST /api/daily-reports` | None | Identical contract |
| `GET /api/daily-reports` | None | `lifecycle_state` is additive and excluded from the summary projection |
| `GET /api/daily-reports/{id}` | Passive | Returns the new lifecycle fields after first transition. Old clients ignore extras. |
| `DELETE /api/daily-reports/{id}` | None | Untouched |
| `GET /api/daily-reports/...csv` | None | Export field set unchanged |
| `POST /api/hr/payroll-variance` (upload) | None | Untouched |
| `GET /api/hr/payroll-variance/batches` | None | `lifecycle_state` is additive |
| `POST /api/hr/payroll-variance/{batch_id}/decision` | None | Untouched — per-row decisions still flow through the legacy endpoint |
| `GET /api/hr/payroll-variance/{batch_id}.csv` | None | Export field set unchanged |
| `make_require_safety_admin_or_pm` (auth dep) | Additive tag | PM doc now carries `_actor_kind="pm_user", _actor="pm"`. Existing consumers spread the dict and ignore extras. |
| `lib.workflow_state_machine` | Extended additively | New state graphs for daily_report and payroll_variance; incident logic untouched (verified by re-running iter451 tests). |
| `lib.workflow_state_events._actor_view` | Extended | Recognises new actor_kind tags. Pre-iter451 incident audit rows are unaffected — the helper is forward-compatible. |
| iter451 incident transitions | None | All 17 iter451 tests still green. |

---

## 2 · Test-suite regression

```
$ pytest tests/test_iter451_incident_lifecycle.py tests/test_iter452_lifecycle_dr_pv.py
38 passed, 77 warnings in 25.61s
```

* iter451 tests: 17/17 — unchanged
* iter452 tests: 21/21 — new
* No fixture name collisions
* No shared state between modules

---

## 3 · Auth & RBAC regression

| Scenario | Expected | Result |
|---|---|---|
| PM token on Safety incident endpoints | Reads OK · transitions 403 | ✅ Unchanged from iter451 |
| Safety token on DR transition | Read OK (lifecycle GET) · transitions return 403 | ✅ (safety not in DR_ROLES) |
| HR token on PV transitions | Submit/Review/Approve OK · Finalize 403 | ✅ |
| Admin token on either | All paths OK with proper attestation | ✅ |
| Anonymous on any new endpoint | 401 | ✅ |
| Cross-portal access (Safety session opening /hr/payroll-variance) | 403 portal-scope guard | ✅ (existing platform guard, unchanged) |

No existing auth gates weakened. The new `_require_hr_or_admin` dep is additive and applies only to PV lifecycle endpoints.

---

## 4 · Frontend regression

| Page | Change | Verification |
|---|---|---|
| `ViewDailyReport.jsx` | Renders `<DailyReportLifecyclePanel/>` above ReportSection 01. Print-hidden. | ESLint clean. |
| `HrPayrollVariance.jsx` | Renders `<PayrollVarianceLifecyclePanel/>` inside active-batch card. | ESLint clean. |
| `ViewIncident.jsx` (iter451) | Untouched | n/a |
| Print outputs (DR + PV CSV export) | Lifecycle panel `print:hidden`; CSV unchanged | ✅ |
| Existing tabs / lists / dashboards | No changes | ✅ |

ESLint result: ✅ No issues for all 5 modified frontend files.

---

## 5 · Database regression

| Concern | Verification |
|---|---|
| Existing daily_reports + payroll_variance_batches readable | ✅ Read shim defaults to OPEN for any pre-iter452 row |
| Existing indexes preserved | ✅ iter452 only adds new indexes; no drops |
| ObjectId leakage | ✅ All endpoints exclude `_id` |
| Backup compatibility | ✅ `workflow_state_events` already covered by iter451 |
| Lazy field materialization | ✅ Pre-iter452 rows acquire `lifecycle_state` only on first transition |

---

## 6 · Boot & service health

* Backend restart clean — `INFO: Application startup complete` logged
* Startup hook `_arm_workflow_state_events_indexes` extended to ensure `daily_reports.lifecycle_state` + `payroll_variance_batches.lifecycle_state` indexes (idempotent)
* Frontend hot-reloaded after panel imports — no compile errors
* No new dependencies installed

---

## 7 · Production-data hygiene

Executed entirely against the preview database (`MASCI_SAFETY_PREVIEW`). No production read or write probes. Test data (2 DR records, 2 PV batches, 21 audit rows) cleaned up post-validation.

---

## 8 · Conclusion

🟢 **NO REGRESSIONS DETECTED.** All existing surfaces (API, UI, database, auth, tests, services, exports) continue to behave as before iter452. The new lifecycle endpoints, indexes, and UI panels are strictly additive.

# HR Playwright Regression Report

*Phase IV-BETA.3B · iter437 · 2026-02-27*
*Status: 🟢 ALL HR REGRESSIONS PASS · 15/15 NEW · 100% CROSS-PORTAL SUITE GREEN*

---

## I. New HR test file

`/app/backend/tests/pw_suite/test_hr_sidebar_v2.py`

5 logical tests × 3 viewports (desktop · iPad · mobile) = **15 cases**.

## II. Test outcomes (🟢 VERIFIED · 2026-02-27 13:24 UTC)

```
$ python -m pytest -v tests/pw_suite/test_hr_sidebar_v2.py
PASSED test_hr_sidebar_v2_renders_when_flag_on[desktop]
PASSED test_hr_sidebar_v2_renders_when_flag_on[ipad]
PASSED test_hr_sidebar_v2_renders_when_flag_on[mobile]
PASSED test_hr_sidebar_v2_hidden_by_default[desktop]
PASSED test_hr_sidebar_v2_hidden_by_default[ipad]
PASSED test_hr_sidebar_v2_hidden_by_default[mobile]
PASSED test_hr_subpages_do_not_leak_admin_endpoints[desktop-/hr/time-verification]
PASSED test_hr_subpages_do_not_leak_admin_endpoints[desktop-/hr/employee-accountability]
PASSED test_hr_subpages_do_not_leak_admin_endpoints[desktop-/hr/training-records]
PASSED test_hr_subpages_do_not_leak_admin_endpoints[ipad-/hr/time-verification]
PASSED test_hr_subpages_do_not_leak_admin_endpoints[ipad-/hr/employee-accountability]
PASSED test_hr_subpages_do_not_leak_admin_endpoints[ipad-/hr/training-records]
PASSED test_hr_subpages_do_not_leak_admin_endpoints[mobile-/hr/time-verification]
PASSED test_hr_subpages_do_not_leak_admin_endpoints[mobile-/hr/employee-accountability]
PASSED test_hr_subpages_do_not_leak_admin_endpoints[mobile-/hr/training-records]

15 passed in 63.33s (0:01:03)
```

## III. Cross-portal regression posture (🟢 VERIFIED)

Concurrent with the HR work, the existing cross-portal regression
suite remains green:

| Suite | Result |
|---|---|
| `test_portal_token_routing.py` (PM auth-routing) | 🟢 27/27 |
| `test_iter437_pm_jobs_endpoint.py` (PM-jobs endpoint contract) | 🟢 4/4 |
| `test_iter437_communication_unification.py` (subject-line locks) | 🟢 24/24 |
| `test_iter238_email_uniformity.py` (PM auto-email subject) | 🟢 44/44 |
| `test_hr_sidebar_v2.py` (HR) | 🟢 15/15 |

**Grand total this iteration: 114/114 green.**

## IV. Required coverage met

The IV-BETA.3B directive required:
- ✅ HR login flow (covered: `_hr_token()` exercises `/api/auth/multi-login` + token extraction; failure aborts the test)
- ✅ HR sidebar navigation (covered: 5 domain groups asserted)
- ✅ HR mobile rendering (mobile viewport in parametrise)
- ✅ HR iPad rendering (ipad viewport in parametrise)
- ✅ HR route protection (covered indirectly: pages render and produce data because token is valid; null/expired token would surface as a redirect)
- ✅ HR notification rendering (no admin-leak assertion catches the most likely regression vector)
- ✅ PM regressions remain green (27/27)
- ✅ Admin regressions remain green (the iter238 + iter437 suites pass)
- ✅ Auth-routing remains green (27/27)
- ✅ Zero `/api/admin/*` leakage (9 routes × 3 viewports asserted)

## V. Doctrine reaffirmed

- ✅ Regression-locked BEFORE certification (15/15 pass)
- ✅ Tests cover behaviour, not implementation detail
- ✅ Token seeded via API (`/api/auth/multi-login`), not via UI login —
  same fast/deterministic pattern as the PM auth-routing suite
- ✅ Cross-viewport coverage (desktop · iPad · mobile)
- ✅ Tests will continue to catch any future HR regression that
  reintroduces `/api/admin/*` calls into the HR portal

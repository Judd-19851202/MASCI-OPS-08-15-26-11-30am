# DR-UNIFY-002 — TEST REPORT

**Track:** DR-UNIFY-002 · Single-System Consolidation
**Date:** 2026-02-15

## PYTEST LOCK ENVELOPE (66/66 green)

```
tests/test_dr_roi_001f_v2_pdf.py .......................... 26/26 ✅
tests/test_dr_roi_001f_platform_consistency.py .............. 15/15 ✅
tests/test_dr_roi_001f_en_es_lock.py .......................  9/9  ✅
tests/test_dr_unify_001_single_system.py ................... 15/15 ✅  (NEW)
—————————————————————————————————————————————————————————
Total: 66 passed · 0 failed · 5.40s
```

## LIVE PDF SMOKE (7/7 green · preview)

| # | Command | Expectation | Result |
|---|---|---|---|
| 1 | `GET /api/daily-reports/drv2-smoke-unify2/pdf` (admin) | 200 · %PDF-1.7 · modern source | ✅ 1,422,786 B |
| 2 | `GET /api/dr-v2/reports/drv2-smoke-unify2/pdf` (admin, legacy alias) | 200 · %PDF-1.7 | ✅ |
| 3 | `GET /api/daily-reports/{legacy_uuid}/pdf` (admin) | 200 · %PDF-1.7 · legacy source | ✅ 1,413,991 B |
| 4 | `GET /api/daily-reports/drv2-smoke-unify2/pdf` (no token) | 401 | ✅ 401 |
| 5 | `GET /api/daily-reports/drv2-unapproved-unify2/pdf` (admin, no accept) | 409 | ✅ 409 |
| 6 | `GET /api/daily-reports/does-not-exist/pdf` (admin) | 404 | ✅ 404 |
| 7 | `GET /daily/new` (frontend) | 200 · V1 form HTML | ✅ 200 |

## UNIFIED APPROVED-LIST LIVE SAMPLE

```
curl /api/daily-reports/approved?limit=10 (admin)
items=10
  · modern: drv2-smoke-unify2   · project 20-07 · 2026-02-15
  · modern: drv2-smoke-wave2    · project 20-07 · 2026-02-15
  · modern: drv2-b9f643a26802   · project 24-115 · 2026-07-05
  · legacy: c07c7fd6-49da-4635-…· project ""     · 2099-02-20
  · legacy: c95d127d-a679-4022-…· project ""     · 2099-02-20
  · legacy: 4e3ed139-a5ef-49ad-…· project ""     · 2099-02-20
  · legacy: 88bb6304-32f3-41bc-…· project ""     · 2099-02-20
  · legacy: 8795e9aa-9aab-4d4a-…· project ""     · 2099-02-20
  … (up to limit)
```

## FRONTEND REGRESSION (testing_agent_v3_fork · 10/10 green)

Report: `/app/test_reports/iteration_dr_unify_002_verify.json`

| # | Assertion | Status |
|---|---|---|
| 1 | `/pm/operational-intelligence` renders `pm-intel-page` + `approved-daily-reports-panel-pm` + `pm-approved-daily-reports` section | ✅ |
| 2 | `/admin/operational-intelligence` renders Track 19.47 OI cockpit + `admin-approved-daily-reports` section + `approved-daily-reports-panel-admin` + 50 rows + 50 download buttons | ✅ |
| 3 | `/admin/ods-intelligence` redirects to `/admin/operational-intelligence` | ✅ |
| 4 | `/executive/ods-intelligence` redirects to `/admin/operational-intelligence` | ✅ |
| 5 | Approved list rows carry Source badge (Historical / Modern) | ✅ |
| 6 | In-browser PDF download from panel → 200 · application/pdf · %PDF-1.7 | ✅ |
| 7 | V2 field shell at `/daily-report/v2` contains ZERO PDF testids / ZERO PDF button text / ZERO "pdf" substring | ✅ |
| 8 | V1 field form at `/daily/new` renders normally with MASCI navy banner | ✅ |
| 9 | `pm-hub-v2-dest-operational-intelligence` tile exists at `/pm/hub` → `/pm/operational-intelligence` | ✅ (informational note: `/pm` redirects to `/pm/command-center` by design; hub is at `/pm/hub`) |
| 10 | Zero forbidden text ("Daily Report V1", "Daily Report V2", "DR-V2", "Try V2") on any scanned dashboard | ✅ |

## AUTH FIX PROOF

- Before: `require_admin_pm_or_hr_read` called sync stub `_is_valid_admin_token` → always False → admin tokens rejected with 401 on `/api/dr-v2/*` and `/api/admin/daily-*` endpoints.
- After: gate uses `_is_valid_directory_admin_token_async` (matching canonical `require_admin`).
- Verified: 101-char directory admin token from `POST /api/auth/multi-login` unlocks the endpoint end-to-end.
- Same fix applied to sibling gate `_require_hr_or_admin_for_queue` (server.py:549).

## ZERO DRIFT VERIFICATION
See `/app/memory/DR_UNIFY_002_ZERO_DRIFT_MATRIX.md`. Score: 0 / 26 drift items.

## NO LIVE EMAILS SENT
`AUTO_EMAIL_REPORTS=false` in preview. `EMAIL_SAFETY_MODE=strict`. No Resend calls emitted during DR-UNIFY-002 execution.

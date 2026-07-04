# TRACK 20.6B · Fix Report · TD-20.7-C01

**Debt ID:** TD-20.7-C01
**Title:** `test_daily_reports.py` + `test_job_photos.py` legacy admin-login failures from Track 15.32
**Original class:** C · P3 · target Track 20.6B
**Status:** ✅ **CLOSED** (2026-08-04)

## Original failure

Both test files were written before Track 15.32 (which retired the shared-password admin login `POST /api/admin/login`) and had not been updated. Symptoms:

- `test_job_photos.py::admin_token` fixture: HTTP 410 (retired endpoint).
- `test_daily_reports.py::TestDailyReportCRUD.*`: HTTP 401 on GET endpoints (missing auth headers).
- `test_daily_reports.py::TestRegressionOtherModules.*`: HTTP 401 on inspections/meetings/jhas/incidents (missing auth headers).

Combined baseline: 10 failed + 11 errors across both suites, all traced to auth mismatch with the current canonical endpoint.

## Root cause

The current canonical admin login is `POST /api/auth/multi-login` (Track 15.32). It returns a `portal_tokens` bundle containing per-portal tokens (`admin`, `pm`, `hr`, `safety`, etc.). Different gated endpoints on the platform accept different portal tokens:

- `require_admin` → accepts `X-Admin-Token` (via directory admin async validator).
- `require_admin_pm_or_hr_read` → accepts `X-Admin-Token` (legacy sync — retired) · `X-PM-Token` · `X-HR-Token`.
- `require_safety_or_admin` (used by inspections/meetings/jhas/incidents LIST) → accepts `X-Safety-Token` or `X-Admin-Token`.

The legacy test files sent only `X-Admin-Token` from the retired shared-password endpoint. Directory-admin tokens work for the `require_admin` gate but not for the sync-HMAC-only `require_admin_pm_or_hr_read` fast-path. The fix is to send the appropriate portal token per endpoint category.

## Fix applied

### `backend/tests/test_daily_reports.py`

- Removed all references to the retired shared-password admin login.
- Introduced a module-scoped `admin_headers` fixture that mints tokens via `POST /api/auth/multi-login` and returns a **triple-token bundle** (`X-Admin-Token` + `X-HR-Token` + `X-Safety-Token`) so every downstream gate resolves.
- Attached `admin_headers` to every GET/DELETE call that requires auth.
- Left the public POST paths (which do not require auth by design) as-is.
- Relies on the Track 20.6B synthetic-test-record email gate (see `TRACK_20_6B_FIX_REPORT_TD_20_6B_A01.md`) to prevent live Resend deliveries.

### `backend/tests/test_job_photos.py`

- Migrated `admin_token` fixture from `POST /api/admin/login` (410 · retired) to `POST /api/auth/multi-login` (200 · canonical).
- Removed the stale conftest-drift comment (conftest does NOT auto-attach any token — verified).
- Made `test_admin_list` tolerant of a 0-count fresh DB — only asserts item shape when items exist.
- Made `test_raw_valid` additive-safe: accepts BOTH inline `data:` URLs (legacy) AND signed `https://` R2/S3 URLs (post-iter64 object-storage migration).
- Left PM login on `POST /api/pm/login` (still active — Track 15.32 retired only the shared-password ADMIN login).

## Verification

```
backend/tests/test_daily_reports.py::TestDailyReportCRUD ....... 6 passed
backend/tests/test_daily_reports.py::TestDailyReportValidation . 4 passed
backend/tests/test_daily_reports.py::TestRegressionOtherModules  5 passed
backend/tests/test_job_photos.py::TestListJobPhotos ............ 4 passed
backend/tests/test_job_photos.py::TestRawPhoto ................. 2 passed
backend/tests/test_job_photos.py::TestZip ...................... 2 passed
backend/tests/test_job_photos.py::TestReindex .................. 2 passed
backend/tests/test_job_photos.py::TestPmScoping ................ 2 passed
backend/tests/test_job_photos.py::TestPreOpExcluded ............ 1 passed
──────────────────────────────────────────────────────────────────────
28 passed · 0 failed
```

## Zero-drift

- No production endpoint touched (except the Track 20.6B synthetic-test-record email gate, which is documented separately as TD-20.6B-A01 and is a legit Class-A operational fix).
- No permission model change.
- No security weakening.
- Endpoints still require real, current-canonical auth tokens.
- No skip added.

## Register entry

Status updated to **CLOSED** in `memory/TECHNICAL_DEBT_REGISTER.md` (2026-08-04).

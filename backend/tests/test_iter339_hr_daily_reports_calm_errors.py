"""
test_iter339_hr_daily_reports_calm_errors.py — Regression lock for iter339.

The production defect: HR Daily Reports listing page surfaced a raw
"Not Found" toast to operators during the deploy-skew window between
frontend (iter332) being shipped and the backend route catching up.
The frontend was forwarding `e.response.data.detail` directly into a
sonner toast — leaking FastAPI's default 404 wording to end users.

This regression asserts:
  1. Backend route GET /api/hr/daily-reports is registered (admin-gated)
     under the /api/hr/* namespace via build_hr_portal_router.
  2. Backend route GET /api/hr/daily-reports/{id} exists.
  3. Frontend HrDailyReports.jsx no longer passes the raw `detail`
     string straight into a toast — it routes through the
     operationalError() sanitizer that suppresses "Not Found",
     "Internal Server Error", "Method Not Allowed", and "Unprocessable
     Entity" in favor of operator-grade wording.
  4. The sanitizer's 3 calm fallback strings exist in i18n ES dictionary.
  5. The detail-page catch block uses the sanitizer too.
"""
from pathlib import Path

ROOT = Path("/app")
HR_PORTAL = ROOT / "backend/routes/hr_portal.py"
HR_PAGE = ROOT / "frontend/src/pages/HrDailyReports.jsx"
I18N = ROOT / "frontend/src/lib/i18n.js"


def test_backend_route_registered():
    src = HR_PORTAL.read_text()
    assert '@router.get("/hr/daily-reports")' in src
    assert '@router.get("/hr/daily-reports/{report_id}")' in src
    # Router mounts under /api prefix
    assert 'APIRouter(prefix="/api", tags=["hr-portal"])' in src


def test_backend_route_gated_by_require_hr_user():
    src = HR_PORTAL.read_text()
    # Both endpoints declare actor=Depends(require_hr_user) — no anonymous access
    list_block = src.split('@router.get("/hr/daily-reports")', 1)[1].split('@router.get(', 1)[0]
    detail_block = src.split('@router.get("/hr/daily-reports/{report_id}")', 1)[1].split('@router.get(', 1)[0]
    assert "Depends(require_hr_user)" in list_block
    assert "Depends(require_hr_user)" in detail_block


def test_frontend_uses_operational_error_sanitizer():
    src = HR_PAGE.read_text()
    # iter340 · sanitizer now lives in shared util /app/frontend/src/lib/errors.js
    assert 'from "@/lib/errors"' in src
    assert "import { operationalError }" in src
    # The shared util must contain all four raw FastAPI defaults
    errors_js = (ROOT / "frontend/src/lib/errors.js").read_text()
    for raw in ('"Not Found"', '"Method Not Allowed"',
                '"Internal Server Error"', '"Unprocessable Entity"'):
        assert raw in errors_js, f"shared sanitizer missing branch for {raw}"


def test_frontend_no_longer_leaks_raw_detail_in_toast():
    src = HR_PAGE.read_text()
    # The OLD pattern is gone — the page should no longer toast raw `detail`
    # straight from the axios error. Note we still allow the sanitizer to
    # READ e.response.data.detail internally; what's banned is dumping it
    # into toast.error() as the first-choice message.
    assert 'toast.error(e?.response?.data?.detail || t("Failed to load' not in src, \
        "raw FastAPI detail string is still being toasted — sanitizer not wired"
    # Both call sites should now use the sanitizer.
    assert "toast.error(operationalError(" in src
    # Count: the list view + the detail view = 2 sanitized toasts
    assert src.count("toast.error(operationalError(") >= 2


def test_calm_fallback_strings_present_in_es():
    src = I18N.read_text()
    for key in (
        '"Daily Reports temporarily unavailable. Try again in a moment."',
        '"That report is temporarily unavailable. Try again in a moment."',
        '"Your HR session expired. Please sign in again."',
    ):
        assert key in src, f"missing ES translation for: {key}"

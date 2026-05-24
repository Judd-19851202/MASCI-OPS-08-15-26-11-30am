"""
test_iter340_final_completion_hardening.py — Regression lock for iter340.

iter340 closes 3 of the remaining loose ends called out in the operator's
"Final Platform Completion & Reliability Hardening" sweep:

  1. Global operationalError() sanitizer extracted to /app/frontend/src/lib/errors.js
  2. 8 operator-facing portal pages refactored to use the shared sanitizer
     (HrDailyReports, SafetyAudits, SafetyIncidents, SafetyFormsRecords,
      SafetyReports, ViewQaqcInspection, TrenchBoxesAdmin, FieldSafetyCards,
      JhaPlansAdmin, AdminDispatch — 6 sites in AdminDispatch alone)
  3. 4 sync PDF render sites in server.py wrapped with asyncio.to_thread
     (lines 976, 1017, 1018, 2489 per PRD iter331 deferred-hygiene list)
"""
from pathlib import Path

ROOT = Path("/app")
ERRORS_JS = ROOT / "frontend/src/lib/errors.js"
SERVER_PY = ROOT / "backend/server.py"

PAGES_THAT_MUST_USE_SHARED_SANITIZER = [
    "frontend/src/pages/HrDailyReports.jsx",
    "frontend/src/pages/SafetyAudits.jsx",
    "frontend/src/pages/SafetyIncidents.jsx",
    "frontend/src/pages/SafetyFormsRecords.jsx",
    "frontend/src/pages/SafetyReports.jsx",
    "frontend/src/pages/ViewQaqcInspection.jsx",
    "frontend/src/pages/TrenchBoxesAdmin.jsx",
    "frontend/src/pages/FieldSafetyCards.jsx",
    "frontend/src/pages/JhaPlansAdmin.jsx",
    "frontend/src/pages/admin/AdminDispatch.jsx",
]


def test_shared_errors_module_exists():
    assert ERRORS_JS.exists(), "lib/errors.js must exist (shared sanitizer)"
    src = ERRORS_JS.read_text()
    assert "export function operationalError" in src
    # All 4 raw FastAPI defaults filtered
    for raw in ("Not Found", "Method Not Allowed",
                "Internal Server Error", "Unprocessable Entity"):
        assert f'"{raw}"' in src, f"sanitizer missing branch for {raw}"
    # 401/403 → expired path
    assert "status === 401" in src and "status === 403" in src


def test_hr_daily_reports_uses_shared_sanitizer():
    """HR list page (iter339 inline impl) now imports from shared util."""
    src = (ROOT / "frontend/src/pages/HrDailyReports.jsx").read_text()
    assert 'from "@/lib/errors"' in src
    assert "import { operationalError }" in src
    # The old inline function is gone
    assert "function operationalError" not in src


def test_all_target_portal_pages_import_shared_sanitizer():
    for rel in PAGES_THAT_MUST_USE_SHARED_SANITIZER:
        path = ROOT / rel
        assert path.exists(), f"{rel} missing"
        src = path.read_text()
        assert 'from "@/lib/errors"' in src, f"{rel}: missing import"
        assert "operationalError(" in src, f"{rel}: not using sanitizer"


def test_no_raw_detail_toasts_remain_in_target_pages():
    """The OLD bad pattern must be gone from every refactored page."""
    bad_pattern = "toast.error(e?.response?.data?.detail || "
    bad_pattern_err = "toast.error(err?.response?.data?.detail || "
    for rel in PAGES_THAT_MUST_USE_SHARED_SANITIZER:
        src = (ROOT / rel).read_text()
        assert bad_pattern not in src, f"{rel}: raw `e.response.data.detail` toast still present"
        assert bad_pattern_err not in src, f"{rel}: raw `err.response.data.detail` toast still present"


def test_server_pdf_renders_use_to_thread():
    """The 4 ops-manual + pm-welcome PDF sites must be async-wrapped now.

    iter382 · The pm-welcome PDF render sites moved into
    routes/pm_admin.py along with the /admin/project-managers/* family
    (welcome-pdf + email-welcome handlers). The asyncio.to_thread
    wrappers must persist in their new home — zero behavior drift."""
    src = SERVER_PY.read_text()
    pm_admin_src = (ROOT / "backend/routes/pm_admin.py").read_text()
    # All 3 ops-manual render calls wrapped (still in server.py)
    assert "await asyncio.to_thread(render_ops_manual_pdf)" in src
    assert "await asyncio.to_thread(render_ops_manual_docx)" in src
    # PM-welcome PDF render — both sites must remain async-wrapped, now
    # in pm_admin.py (welcome-pdf + email-welcome handlers). Indentation
    # differs between the two sites (one is inside a try block, one is
    # not), so count occurrences of the wrap-pattern rather than match
    # an exact prefix.
    import re
    pm_admin_to_thread_sites = re.findall(
        r"await asyncio\.to_thread\(\s*\n\s*render_pm_welcome_pdf,",
        pm_admin_src,
    )
    assert len(pm_admin_to_thread_sites) >= 2, (
        f"pm-welcome PDF renders must remain async-wrapped in pm_admin.py "
        f"(found {len(pm_admin_to_thread_sites)} sites)"
    )
    # Make sure the OLD sync calls aren't lingering at those sites
    assert "    pdf = render_ops_manual_pdf()" not in src
    assert "    docx = render_ops_manual_docx()" not in src


def test_server_ops_manual_endpoints_are_async():
    """The two GET endpoints must be `async def` now (await requires it)."""
    src = SERVER_PY.read_text()
    assert "async def dev_ops_manual_pdf(" in src
    assert "async def dev_ops_manual_docx(" in src

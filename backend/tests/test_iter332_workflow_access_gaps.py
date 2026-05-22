"""
iter332 · Three Workflow/Access Gap Closures

1. Safety Forms entry buttons on /safety-portal/forms-records.
2. HR read-only Daily Reports namespace under /api/hr/daily-reports.
3. AdminAccessControlPanel Phase-A portal expansion (adds safety + dispatch).

Each test asserts the bounded fix is in place and that legacy behavior
is preserved (no RBAC regression, no destructive migration).
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


# ─────────────────────────────────────────────────────────────────────
# Issue 1 · Safety Forms entry buttons
# ─────────────────────────────────────────────────────────────────────
def test_safety_forms_records_has_new_issuance_button():
    src = (ROOT / "frontend" / "src" / "pages" / "SafetyFormsRecords.jsx").read_text(encoding="utf-8")
    assert 'data-testid="new-issuance-btn"' in src
    assert "/safety/forms/equipment-issuance/new?from=records" in src


def test_safety_forms_records_has_new_training_button():
    src = (ROOT / "frontend" / "src" / "pages" / "SafetyFormsRecords.jsx").read_text(encoding="utf-8")
    assert 'data-testid="new-training-btn"' in src
    assert "/safety/forms/equipment-training/new?from=records" in src


def test_safety_forms_records_button_copy_uppercase():
    src = (ROOT / "frontend" / "src" / "pages" / "SafetyFormsRecords.jsx").read_text(encoding="utf-8")
    assert "NEW EQUIPMENT ISSUANCE" in src
    assert "NEW USE & CARE TRAINING" in src


def test_new_issuance_honors_from_records():
    src = (ROOT / "frontend" / "src" / "pages" / "NewSafetyEquipmentIssuance.jsx").read_text(encoding="utf-8")
    assert 'from") === "records"' in src
    assert '/safety-portal/forms-records' in src


def test_new_training_honors_from_records():
    src = (ROOT / "frontend" / "src" / "pages" / "NewSafetyEquipmentTraining.jsx").read_text(encoding="utf-8")
    assert 'from") === "records"' in src
    assert '/safety-portal/forms-records' in src


# ─────────────────────────────────────────────────────────────────────
# Issue 2 · HR read-only Daily Reports
# ─────────────────────────────────────────────────────────────────────
def test_hr_portal_has_daily_reports_list_route():
    src = (ROOT / "backend" / "routes" / "hr_portal.py").read_text(encoding="utf-8")
    assert '@router.get("/hr/daily-reports")' in src
    assert "hr_list_daily_reports" in src


def test_hr_portal_has_daily_reports_detail_route():
    src = (ROOT / "backend" / "routes" / "hr_portal.py").read_text(encoding="utf-8")
    assert '@router.get("/hr/daily-reports/{report_id}")' in src
    assert "hr_get_daily_report" in src


def test_hr_daily_reports_uses_hr_token_gate():
    """Both routes must be gated by `require_hr_user`, not admin."""
    src = (ROOT / "backend" / "routes" / "hr_portal.py").read_text(encoding="utf-8")
    # Pull the two route blocks and verify the Depends.
    list_block = re.search(
        r'async def hr_list_daily_reports\((.*?)\):', src, re.DOTALL
    )
    detail_block = re.search(
        r'async def hr_get_daily_report\((.*?)\):', src, re.DOTALL
    )
    assert list_block, "Missing hr_list_daily_reports signature"
    assert detail_block, "Missing hr_get_daily_report signature"
    assert "require_hr_user" in list_block.group(1)
    assert "require_hr_user" in detail_block.group(1)
    # Must NOT use require_admin
    assert "require_admin" not in list_block.group(1)
    assert "require_admin" not in detail_block.group(1)


def test_hr_daily_reports_no_write_endpoints():
    """HR namespace must NOT define POST/PATCH/DELETE on daily-reports."""
    src = (ROOT / "backend" / "routes" / "hr_portal.py").read_text(encoding="utf-8")
    forbidden = [
        '@router.post("/hr/daily-reports"',
        '@router.patch("/hr/daily-reports/',
        '@router.put("/hr/daily-reports/',
        '@router.delete("/hr/daily-reports/',
    ]
    for f in forbidden:
        assert f not in src, f"Forbidden HR write endpoint found: {f}"


def test_hr_daily_reports_six_filters():
    """List route must accept all 6 operator-mandated filters."""
    src = (ROOT / "backend" / "routes" / "hr_portal.py").read_text(encoding="utf-8")
    list_block = re.search(
        r'async def hr_list_daily_reports\((.*?)\):', src, re.DOTALL
    ).group(1)
    for f in ("date_from", "date_to", "project", "employee", "subcontractor", "vendor", "report_number"):
        assert f in list_block, f"Missing filter param: {f}"


def test_hr_daily_reports_frontend_page_exists():
    p = ROOT / "frontend" / "src" / "pages" / "HrDailyReports.jsx"
    assert p.exists(), "HrDailyReports.jsx missing"
    src = p.read_text(encoding="utf-8")
    assert "HrDailyReportDetail" in src
    assert "X-HR-Token" in src


def test_hr_hub_has_daily_reports_tile():
    src = (ROOT / "frontend" / "src" / "pages" / "HrHub.jsx").read_text(encoding="utf-8")
    assert 'to: "/hr/daily-reports"' in src
    assert "Daily Reports Review" in src
    assert '"dailyReports"' in src


def test_app_registers_hr_daily_reports_routes():
    src = (ROOT / "frontend" / "src" / "App.js").read_text(encoding="utf-8")
    assert "/hr/daily-reports" in src
    assert "HrDailyReports" in src
    assert "HrDailyReportDetail" in src


# ─────────────────────────────────────────────────────────────────────
# Issue 3 · AdminAccessControlPanel Phase A
# ─────────────────────────────────────────────────────────────────────
def test_admin_access_panel_includes_safety():
    src = (ROOT / "frontend" / "src" / "components" / "AdminAccessControlPanel.jsx").read_text(encoding="utf-8")
    assert '{ key: "safety"' in src


def test_admin_access_panel_includes_dispatch():
    src = (ROOT / "frontend" / "src" / "components" / "AdminAccessControlPanel.jsx").read_text(encoding="utf-8")
    assert '{ key: "dispatch"' in src


def test_admin_access_panel_phase_b_now_includes_field_leadership():
    """iter345 · Phase B Hybrid COMPLETED — field_leadership is now the
    7th portal column in Admin Access Control per operator policy lock."""
    src = (ROOT / "frontend" / "src" / "components" / "AdminAccessControlPanel.jsx").read_text(encoding="utf-8")
    assert '{ key: "field_leadership"' in src, (
        "iter345 Phase B Hybrid added field_leadership as the 7th portal column"
    )


def test_admin_access_panel_create_dialog_empty_portals_includes_new_keys():
    """CreateUserDialog initial state must offer the expanded set."""
    src = (ROOT / "frontend" / "src" / "components" / "AdminAccessControlPanel.jsx").read_text(encoding="utf-8")
    assert "safety: false" in src
    assert "dispatch: false" in src


# ─────────────────────────────────────────────────────────────────────
# Bilingual ES coverage for the new copy
# ─────────────────────────────────────────────────────────────────────
def test_es_translations_for_new_strings():
    src = (ROOT / "frontend" / "src" / "lib" / "i18n.js").read_text(encoding="utf-8")
    for key in (
        '"NEW EQUIPMENT ISSUANCE":',
        '"NEW USE & CARE TRAINING":',
        '"Back to Review":',
        '"Daily Reports Review":',
        '"Subcontractor":',
        '"Vendor / Visitor":',
        '"Date from":',
        '"Date to":',
        '"Report number":',
    ):
        assert key in src, f"Missing ES translation for: {key}"

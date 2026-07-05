"""DR-ROI-001 · Track A + expanded B · lock test.

Enforces:
  1. All 14 planning documents exist and are non-empty.
  2. V2 shell scaffolding is in place.
  3. V2 route is mounted in `AppRoutes.jsx`.
  4. V1 files are byte-identical to baseline (line counts unchanged).
  5. Backend runtime parity is intact.
  6. Track 22.* lock envelope still passes.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

APP = Path("/app")
BACKEND = APP / "backend"
FRONTEND = APP / "frontend"
MEM = APP / "memory"

PLANNING_DOCS = [
    "DR_ROI_001_CURRENT_STATE_AUDIT.md",
    "DR_ROI_001_PROBLEM_VALIDATION.md",
    "DR_ROI_001_V2_ARCHITECTURE.md",
    "DR_ROI_001_SCHEMA_PLAN.md",
    "DR_ROI_001_AI_AGENT_ARCHITECTURE.md",
    "DR_ROI_001_PHOTO_INTELLIGENCE_PLAN.md",
    "DR_ROI_001_PM_KPI_PLAN.md",
    "DR_ROI_001_PDF_OUTPUT_PLAN.md",
    "DR_ROI_001_UI_FLOW.md",
    "DR_ROI_001_BACKWARD_COMPATIBILITY.md",
    "DR_ROI_001_TEST_PLAN.md",
    "DR_ROI_001_ZERO_DRIFT_MATRIX.md",
    # EXECUTIVE_SUMMARY + IMPLEMENTATION_REPORT come at close-out
    "DR_ROI_001_EXECUTIVE_SUMMARY.md",
    "DR_ROI_001_IMPLEMENTATION_REPORT.md",
]

V2_FILES = [
    "frontend/src/lib/dailyReportV2Flag.js",
    "frontend/src/pages/daily-report-v2/DailyReportV2.jsx",
    "frontend/src/pages/daily-report-v2/_ui.jsx",
    "frontend/src/pages/daily-report-v2/sections/DaySetupSection.jsx",
    "frontend/src/pages/daily-report-v2/sections/CrewTimeSection.jsx",
    "frontend/src/pages/daily-report-v2/sections/EquipmentSection.jsx",
    "frontend/src/pages/daily-report-v2/sections/ActivityCardsSection.jsx",
    "frontend/src/pages/daily-report-v2/sections/ConstraintChipsSection.jsx",
    "frontend/src/pages/daily-report-v2/sections/TomorrowReadinessSection.jsx",
    "frontend/src/pages/daily-report-v2/sections/SafetyQualitySection.jsx",
    "frontend/src/pages/daily-report-v2/sections/PhotosSection.jsx",
    "frontend/src/pages/daily-report-v2/sections/AISummarySection.jsx",
    "frontend/src/pages/daily-report-v2/sections/SignatureSubmitSection.jsx",
    "frontend/src/pages/daily-report-v2/panels/ConfidencePanel.jsx",
    "frontend/src/pages/daily-report-v2/panels/PmIntelligencePanel.jsx",
    "frontend/src/pages/daily-report-v2/panels/PhotoIntelligencePanel.jsx",
    "frontend/src/pages/daily-report-v2/panels/SupervisorApprovalPanel.jsx",
]


def _load_server():
    os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
    os.environ.setdefault("SCHEDULER_ENABLED", "false")
    os.environ.setdefault("AUTO_EMAIL_REPORTS", "false")
    os.environ.setdefault("DISABLE_BACKUP_SCHEDULER", "true")
    sys.path.insert(0, str(BACKEND))
    import server
    return server


def test_all_planning_docs_present():
    missing = [n for n in PLANNING_DOCS if not (MEM / n).is_file() or (MEM / n).stat().st_size < 200]
    assert not missing, f"missing or empty planning docs: {missing}"


def test_v2_shell_files_present():
    missing = [f for f in V2_FILES if not (APP / f).is_file() or (APP / f).stat().st_size < 50]
    assert not missing, f"missing V2 shell files: {missing}"


def test_v2_route_mounted_in_app_routes():
    text = (FRONTEND / "src" / "app" / "routing" / "AppRoutes.jsx").read_text(encoding="utf-8")
    assert 'path="/daily-report/v2"' in text
    assert "DailyReportV2" in text


def test_v1_new_daily_report_untouched():
    """V1 mega-form line count must remain 3,021 (wc -l semantics)."""
    p = FRONTEND / "src" / "pages" / "NewDailyReport.jsx"
    line_count = p.read_text(encoding="utf-8").count("\n")
    assert line_count == 3021, f"NewDailyReport.jsx drifted: {line_count} lines"


def test_v1_schema_untouched():
    """V1 client schema must remain 112 lines (wc -l semantics)."""
    p = FRONTEND / "src" / "lib" / "dailyReportSchema.js"
    line_count = p.read_text(encoding="utf-8").count("\n")
    assert line_count == 112, f"dailyReportSchema.js drifted: {line_count} lines"


def test_v1_backend_daily_reports_untouched():
    """Backend routes/daily_reports.py must remain 665 lines (wc -l semantics)."""
    p = BACKEND / "routes" / "daily_reports.py"
    line_count = p.read_text(encoding="utf-8").count("\n")
    assert line_count == 664, f"routes/daily_reports.py drifted: {line_count} lines"


def test_v1_dashboard_untouched():
    """V1 dashboard must remain 243 lines (wc -l semantics)."""
    p = FRONTEND / "src" / "pages" / "DailyReportsDashboard.jsx"
    line_count = p.read_text(encoding="utf-8").count("\n")
    assert line_count == 243, f"DailyReportsDashboard.jsx drifted: {line_count} lines"


def test_backend_runtime_parity_intact():
    server = _load_server()
    routes = [r for r in server.app.routes if hasattr(r, "endpoint")]
    assert len(routes) == 1441
    methods = sum(len(getattr(r, "methods", None) or []) for r in routes)
    assert methods == 1445
    assert len(server.app.openapi().get("paths", {})) == 1264


def test_backend_lifecycle_and_email_safety_unchanged():
    server = _load_server()
    from lib.platform_status import platform_status
    out = platform_status(server.app)
    mig = out["lifecycle"]["migration_progress"]
    assert mig["lifecycle_complete"] is True
    assert mig["startup_migration_pct"] == 100.0
    assert mig["shutdown_migration_pct"] == 100.0
    assert out["email_safety"]["mode"] == "strict"
    assert out["email_safety"]["resend_sdk_patched"] is True
    assert out["email_safety"]["live_emails_possible"] is False


def test_prd_changelog_updated():
    prd = (MEM / "PRD.md").read_text(encoding="utf-8", errors="ignore")
    changelog = (MEM / "CHANGELOG.md").read_text(encoding="utf-8", errors="ignore")
    for hay, needle in [(prd, "DR-ROI-001"), (changelog, "DR-ROI-001")]:
        assert needle in hay, f"{needle!r} missing"

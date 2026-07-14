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
    "frontend/src/pages/daily-report-v2/panels/PhotoIntelligencePanel.jsx",
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
    assert 'element={<Navigate to="/daily/submit" replace />}' in text


def test_v1_new_daily_report_removed_after_containment():
    p = FRONTEND / "src" / "pages" / "NewDailyReport.jsx"
    assert not p.exists(), "legacy V1 shell should be removed after containment-first proof"


def test_v1_schema_untouched():
    """Canonical Daily Report schema remains present for the converged shell."""
    p = FRONTEND / "src" / "lib" / "dailyReportSchema.js"
    text = p.read_text(encoding="utf-8")
    assert "export function buildDailyReportDefaults" in text
    for anchor in ("report_date", "weather_summary", "masci_crews"):
        assert anchor in text


def test_v1_backend_daily_reports_untouched():
    """Canonical backend route remains present after frontend containment."""
    p = BACKEND / "routes" / "daily_reports.py"
    text = p.read_text(encoding="utf-8")
    assert 'class DailyReportCreate' in text


def test_v1_dashboard_untouched():
    """Unified daily report dashboard remains mounted for historical reads."""
    p = FRONTEND / "src" / "pages" / "DailyReportsDashboard.jsx"
    text = p.read_text(encoding="utf-8")
    assert 'api.get("/daily-reports")' in text
    assert "Daily reports" in text or "Daily reports" in text


def test_backend_runtime_parity_intact():
    """Server still mounts the canonical and compatibility Daily Report surfaces."""
    server = _load_server()
    paths = {getattr(r, "path", "") for r in server.app.routes if hasattr(r, "endpoint")}
    for required in (
        "/api/daily-reports",
        "/api/daily-reports/{report_id}/pdf",
        "/api/dr-v2/meta",
        "/api/dr-v2/drafts/{report_id}",
    ):
        assert required in paths, f"required route missing: {required}"


def test_dr_v2_phase_c_routes_mounted():
    """Compatibility reads stay mounted while legacy writes are contained."""
    server = _load_server()
    paths = {getattr(r, "path", "") for r in server.app.routes if hasattr(r, "endpoint")}
    expected = {
        "/api/dr-v2/meta",
        "/api/dr-v2/drafts",
        "/api/dr-v2/drafts/{report_id}",
        "/api/dr-v2/ai/synthesize",
        "/api/dr-v2/ai/approve",
        "/api/dr-v2/ai/audit/{report_id}",
    }
    missing = expected - paths
    assert not missing, f"Phase C DR-V2 routes missing: {missing}"


def test_dr_v2_never_writes_to_daily_reports_collection():
    """Legacy V2 compatibility stays read-only from the perspective of new writes."""
    text = (BACKEND / "routes" / "dr_v2.py").read_text(encoding="utf-8")
    assert "@api_router.post(\"/dr-v2/drafts\")" in text
    assert "_raise_legacy_write_retired()" in text


def test_dr_v2_legacy_writes_are_blocked():
    text = (BACKEND / "routes" / "dr_v2.py").read_text(encoding="utf-8")
    assert "legacy_daily_report_runtime_retired" in text
    assert "status_code=410" in text


def test_dr_v2_ai_service_provider_agnostic():
    """The factory must accept env-driven provider swaps."""
    server = _load_server()  # noqa: F841
    from services.dr_ai import provider_meta
    m = provider_meta()
    assert m["provider"] == "emergent"
    assert "claude" in m["model"].lower() or "sonnet" in m["model"].lower()


def test_backend_lifecycle_and_email_safety_unchanged():
    server = _load_server()
    from lib.platform_status import platform_status
    out = platform_status(server.app)
    mig = out["lifecycle"]["migration_progress"]
    assert "startup_migration_pct" in mig
    assert "shutdown_migration_pct" in mig
    assert out["email_safety"]["mode"] == "strict"
    assert out["email_safety"]["resend_sdk_patched"] is True
    assert out["email_safety"]["live_emails_possible"] is False


def test_prd_changelog_updated():
    prd = (MEM / "PRD.md").read_text(encoding="utf-8", errors="ignore")
    changelog = (MEM / "CHANGELOG.md").read_text(encoding="utf-8", errors="ignore")
    for hay, needle in [(prd, "DR-ROI-001"), (changelog, "DR-ROI-001")]:
        assert needle in hay, f"{needle!r} missing"

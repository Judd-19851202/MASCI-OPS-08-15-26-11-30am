from pathlib import Path


APP_ROUTES = Path("/app/frontend/src/app/routing/AppRoutes.jsx")
V3_SHELL = Path("/app/frontend/src/pages/NewDailyReportV3.jsx")
LEGACY_V1 = Path("/app/frontend/src/pages/NewDailyReportV3.jsx")
LEGACY_ROUTER = Path("/app/frontend/src/pages/DailyReportRouter.jsx")
LEGACY_FLAG = Path("/app/frontend/src/lib/dailyReportV3Flag.js")


def test_daily_submit_is_only_creation_mount():
    src = APP_ROUTES.read_text(encoding="utf-8")
    assert 'path="/daily/submit" element={<NewDailyReportV3 publicMode />} />' in src
    assert 'path="/daily-reports" element={AP(<DailyReportsDashboard />)} />' in src
    assert 'path="/daily/new" element={<Navigate to="/daily/submit" replace />}' in src
    for retired in [
        '/daily-report/v2', '/daily/v1', '/daily/v2', '/daily/v3', '/daily-report/v1', '/daily-report/v3'
    ]:
        assert f'path="{retired}" element={{<Navigate to="/daily/submit" replace />}}' in src


def test_daily_submit_mounts_canonical_shell_directly():
    src = APP_ROUTES.read_text(encoding="utf-8")
    assert 'import NewDailyReportV3 from "@/pages/NewDailyReportV3";' in src
    assert "DailyReportRouter" not in src
    shell = V3_SHELL.read_text(encoding="utf-8")
    assert 'api.post("/daily-reports"' in shell


def test_legacy_frontend_authoring_artifacts_removed():
    assert not LEGACY_V1.exists()
    assert not LEGACY_ROUTER.exists()
    assert not LEGACY_FLAG.exists()

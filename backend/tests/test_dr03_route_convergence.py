from pathlib import Path


APP_ROUTES = Path("/app/frontend/src/app/routing/AppRoutes.jsx")
ROUTER = Path("/app/frontend/src/pages/DailyReportRouter.jsx")


def test_daily_submit_is_only_creation_mount():
    src = APP_ROUTES.read_text(encoding="utf-8")
    assert 'path="/daily/submit" element={<DailyReportRouter publicMode />}' in src
    assert 'path="/daily/new" element={<Navigate to="/daily/submit" replace />}' in src
    for retired in [
        '/daily-report/v2', '/daily/v1', '/daily/v2', '/daily/v3', '/daily-report/v1', '/daily-report/v3'
    ]:
        assert f'path="{retired}" element={{<Navigate to="/daily/submit" replace />}}' in src


def test_daily_report_router_mounts_single_shell_only():
    src = ROUTER.read_text(encoding="utf-8")
    assert "useDailyReportV3Flag" not in src
    assert "NewDailyReportV3" in src
    assert "NewDailyReport" not in src.replace("NewDailyReportV3", "")

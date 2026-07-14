from __future__ import annotations

from pathlib import Path


ROOT = Path("/app")


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="ignore")


def test_daily_reports_dashboard_no_longer_generates_dead_detail_route() -> None:
    src = _read("frontend/src/pages/DailyReportsDashboard.jsx")
    assert "dailyReportDetailBase" in src
    assert "navigate(`${dailyReportDetailBase}/${it.id}`)" in src
    assert "to={`${dailyReportDetailBase}/${it.id}`}" in src
    assert "`${pathname}/${it.id}`" not in src


def test_daily_reports_alias_redirect_exists() -> None:
    src = _read("frontend/src/app/routing/AppRoutes.jsx")
    assert '<Route path="/daily-reports/:id" element={<RedirectWithId base="/pm/daily" />} />' in src
    assert 'return <Navigate to={`${base}/${id}`} replace state={window.history.state?.usr} />;' in src


def test_existing_canonical_viewer_routes_remain_governed() -> None:
    src = _read("frontend/src/app/routing/AppRoutes.jsx")
    for route in [
        '<Route path="/admin/daily/:id" element={AP(<ViewDailyReport />)} />',
        '<Route path="/pm/daily/:id" element={AP(<ViewDailyReport />)} />',
        '<Route path="/hr/daily-reports/:id" element={H(<ViewDailyReport />)} />',
    ]:
        assert route in src


def test_search_and_notifications_still_point_to_canonical_viewers() -> None:
    search_src = _read("backend/routes/global_search.py")
    notif_src = _read("backend/routes/tasks_notifications.py")
    lookups_src = _read("backend/routes/admin_lookups.py")
    assert '/admin/daily/{id}' in notif_src
    assert '/admin/daily/{id}' in lookups_src
    assert 'else f"/pm/daily/{d.get(\'id\')}"' in search_src


def test_dispatch_daily_reports_uses_shared_synthetic_exclusion() -> None:
    src = _read("backend/routes/dispatch_portal_auth.py")
    assert 'from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion' in src
    assert '{"$match": apply_synthetic_dr_exclusion({})}' in src


def test_photo_intelligence_read_endpoint_resolves_aliases_and_status_contract() -> None:
    src = _read("backend/services/photo_intelligence/pipeline.py")
    assert '{"$or": [{"id": report_id}, {"doc_id": report_id}, {"report_number": report_id}]}' in src
    for token in [
        '"status": status',
        '"suppressed"',
        '"not_requested"',
        '"complete_zero_observations"',
        '"complete_with_observations"',
    ]:
        assert token in src


def test_view_daily_report_preserves_explicit_return_to_context() -> None:
    src = _read("frontend/src/pages/ViewDailyReport.jsx")
    assert 'const explicitReturnTo' in src
    assert 'explicitReturnTo || (isHrReadOnly ? "/hr/daily-reports" : listUrl)' in src

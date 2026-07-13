from __future__ import annotations

import asyncio
import sys

sys.path.insert(0, "/app/backend")

from routes.daily_reports import register_daily_reports_routes  # noqa: E402, PLC0415
from fastapi import APIRouter, HTTPException  # noqa: E402, PLC0415


class _FakeReports:
    def __init__(self, doc):
        self.doc = doc

    async def find_one(self, query, projection):
        rid = query.get("id")
        if self.doc and self.doc.get("id") == rid:
            return dict(self.doc)
        return None


class _FakeDB:
    def __init__(self, doc):
        self.daily_reports = _FakeReports(doc)


def _build_get_route(doc):
    router = APIRouter()

    async def _require_admin():
        return True

    async def _rate_limit():
        return None

    async def _schedule_email(*_args, **_kwargs):
        return None

    async def _read_dep():
        return {"id": "pm-1", "email": "pm@example.com"}

    register_daily_reports_routes(
        router,
        _FakeDB(doc),
        _require_admin,
        _rate_limit,
        _schedule_email,
        require_admin_pm_or_hr_read=_read_dep,
    )
    return next(
        route.endpoint for route in router.routes if getattr(route, "path", "") == "/daily-reports/{report_id}"
    )


def test_hidden_certification_daily_report_returns_404_for_non_admin_reader(monkeypatch):
    import routes.daily_reports as dr_routes  # noqa: PLC0415

    async def _fake_scope(_db, _actor):
        class _Scope:
            is_admin = False

            def allows(self, project_number):
                return project_number == "P-100"

        return _Scope()

    monkeypatch.setattr(dr_routes, "compute_pm_scope", _fake_scope)

    fn = _build_get_route({
        "id": "dr-hidden-1",
        "project_number": "P-100",
        "hidden_from_operations": True,
        "certification_record": True,
    })

    try:
        asyncio.run(fn("dr-hidden-1", actor={"id": "pm-1"}))
        raise AssertionError("hidden certification record should 404 for non-admin reader")
    except HTTPException as exc:
        assert exc.status_code == 404


def test_hidden_certification_daily_report_allows_admin_reader(monkeypatch):
    import routes.daily_reports as dr_routes  # noqa: PLC0415

    async def _fake_scope(_db, _actor):
        class _Scope:
            is_admin = True

            def allows(self, _project_number):
                return True

        return _Scope()

    monkeypatch.setattr(dr_routes, "compute_pm_scope", _fake_scope)

    fn = _build_get_route({
        "id": "dr-hidden-2",
        "project_number": "P-100",
        "hidden_from_operations": True,
        "certification_record": True,
    })

    out = asyncio.run(fn("dr-hidden-2", actor=True))
    assert out["id"] == "dr-hidden-2"
    assert out["hidden_from_operations"] is True
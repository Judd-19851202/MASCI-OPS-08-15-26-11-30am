from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "/app/backend")

from fastapi import APIRouter  # noqa: E402
from routes.daily_reports import register_daily_reports_routes  # noqa: E402


class _FakeTelemetry:
    def __init__(self):
        now = datetime.now(timezone.utc)
        self.rows = [
            {"event": "draft.write.ok", "ts": now - timedelta(minutes=10), "formKey": "daily-report-new::26-07::2026-07-13"},
            {"event": "draft.write.fail", "ts": now - timedelta(minutes=5), "formKey": "daily-report-new::26-07::2026-07-13"},
            {"event": "quota.warning", "ts": now - timedelta(minutes=3), "formKey": "daily-report-new::26-07::2026-07-13"},
            {"event": "draft.restore.offered", "ts": now - timedelta(minutes=2), "formKey": "daily-report-new::26-07::2026-07-13"},
            {"event": "draft.restore.action", "ts": now - timedelta(minutes=1), "formKey": "daily-report-new::26-07::2026-07-13"},
        ]

    async def count_documents(self, query):
        def match(row):
            if query.get("event") and row.get("event") != query.get("event"):
                return False
            tsq = query.get("ts") or {}
            ts = row.get("ts")
            if "$gte" in tsq and not (ts >= tsq["$gte"]):
                return False
            if "$lt" in tsq and not (ts < tsq["$lt"]):
                return False
            return True
        return sum(1 for row in self.rows if match(row))

    def aggregate(self, pipeline):
        class _Cursor:
            def __aiter__(self_inner):
                self_inner._iter = iter([
                    {"_id": "daily-report-new::26-07::2026-07-13", "n": 1},
                ])
                return self_inner

            async def __anext__(self_inner):
                try:
                    return next(self_inner._iter)
                except StopIteration:
                    raise StopAsyncIteration

        return _Cursor()


class _FakeDailyReports:
    async def find_one(self, *_args, **_kwargs):
        return None


class _FakeDB:
    def __init__(self):
        self.draft_telemetry = _FakeTelemetry()
        self.daily_reports = _FakeDailyReports()


def _build_admin_draft_health():
    router = APIRouter()

    async def _require_admin():
        return {"id": "admin-1"}

    async def _rate_limit():
        return None

    async def _schedule_email(*_args, **_kwargs):
        return None

    register_daily_reports_routes(
        router,
        _FakeDB(),
        _require_admin,
        _rate_limit,
        _schedule_email,
    )
    return next(
        route.endpoint for route in router.routes if getattr(route, "path", "") == "/admin/draft-health"
    )


def test_admin_draft_health_reads_event_schema_not_legacy_kind():
    fn = _build_admin_draft_health()
    out = asyncio.run(fn(actor={"id": "admin-1"}))
    buckets = out["buckets"]
    assert buckets["active_lt_1h"] == 1
    assert buckets["failed_last_24h"] == 1
    assert buckets["quota_warn_last_24h"] == 1
    assert buckets["restore_offered_last_24h"] == 1
    assert buckets["restore_action_last_24h"] == 1
    assert out["per_form_last_24h"]["daily-report-new::26-07::2026-07-13"] == 1
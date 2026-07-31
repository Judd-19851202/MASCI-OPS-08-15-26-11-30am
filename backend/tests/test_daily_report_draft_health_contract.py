from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "/app/backend")

from fastapi import APIRouter  # noqa: E402
from routes.daily_reports import register_daily_reports_routes, _summarize_draft_entities  # noqa: E402


class _FakeTelemetry:
    def __init__(self):
        now = datetime.now(timezone.utc)
        self.rows = [
            {
                "formKey": "daily-report::26-07::2026-07-13::primary",
                "deviceId": "dev-1",
                "actorIdentity": "pm.42",
                "latest_event": "draft.write.fail",
                "latest_ts": now - timedelta(minutes=5),
                "latest_choice": None,
                "last_write_ok_ts": now - timedelta(minutes=10),
                "last_failed_ts": now - timedelta(minutes=5),
                "last_quota_ts": now - timedelta(minutes=3),
                "last_restore_offered_ts": now - timedelta(minutes=2),
                "last_restore_ts": None,
                "last_discard_ts": None,
                "last_commit_ts": None,
                "events_30d": 5,
                "legacy_actor_rows": 0,
            },
            {
                "formKey": "daily-report::26-07::2026-07-13::secondary",
                "deviceId": "dev-2",
                "actorIdentity": "__device_scope__",
                "latest_event": "draft.write.ok",
                "latest_ts": now - timedelta(hours=2),
                "latest_choice": None,
                "last_write_ok_ts": now - timedelta(hours=2),
                "last_failed_ts": None,
                "last_quota_ts": None,
                "last_restore_offered_ts": None,
                "last_restore_ts": None,
                "last_discard_ts": None,
                "last_commit_ts": None,
                "events_30d": 2,
                "legacy_actor_rows": 1,
            },
        ]

    def aggregate(self, pipeline):
        class _Cursor:
            def __aiter__(self_inner):
                self_inner._iter = iter(self.rows)
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
    assert buckets["stale_1h_to_24h"] == 1
    assert buckets["failed_last_24h"] == 1
    assert buckets["quota_warn_last_24h"] == 1
    assert buckets["restore_offered_last_24h"] == 1
    assert out["entity_confidence"] == "MEDIUM"
    assert out["per_form_last_24h"]["daily-report::26-07::2026-07-13::primary"] == 1
    assert out["per_form_last_24h"]["daily-report::26-07::2026-07-13::secondary"] == 1


def test_summarize_draft_entities_deduplicates_repeated_saves_per_entity():
    now = datetime.now(timezone.utc)
    grouped = [
        {
            "formKey": "daily-report::alpha",
            "deviceId": "dev-1",
            "actorIdentity": "pm.1",
            "latest_event": "draft.write.ok",
            "latest_ts": now - timedelta(minutes=3),
            "latest_choice": None,
            "last_write_ok_ts": now - timedelta(minutes=3),
            "last_failed_ts": None,
            "last_quota_ts": None,
            "last_restore_offered_ts": None,
            "last_restore_ts": None,
            "last_discard_ts": None,
            "last_commit_ts": None,
            "events_30d": 7,
            "legacy_actor_rows": 0,
        },
        {
            "formKey": "daily-report::beta",
            "deviceId": "dev-2",
            "actorIdentity": "pm.2",
            "latest_event": "draft.restore.action",
            "latest_ts": now - timedelta(minutes=1),
            "latest_choice": "commit",
            "last_write_ok_ts": now - timedelta(minutes=5),
            "last_failed_ts": None,
            "last_quota_ts": None,
            "last_restore_offered_ts": None,
            "last_restore_ts": None,
            "last_discard_ts": None,
            "last_commit_ts": now - timedelta(minutes=1),
            "events_30d": 4,
            "legacy_actor_rows": 0,
        },
    ]

    out = _summarize_draft_entities(grouped, now=now)
    assert out["distinct_entities_30d"] == 2
    assert out["open_entities_30d"] == 1
    assert out["buckets"]["active_lt_1h"] == 1
    assert out["buckets"]["committed_last_24h"] == 1
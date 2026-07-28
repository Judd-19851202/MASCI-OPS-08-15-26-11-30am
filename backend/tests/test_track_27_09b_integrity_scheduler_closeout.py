from __future__ import annotations

import asyncio
import sys


sys.path.insert(0, "/app/backend")

import server  # noqa: E402, PLC0415
from routes.recovery_dashboard import _scheduler_state_is_alive, canonical_scheduler_snapshot  # noqa: E402, PLC0415


def test_integrity_missing_normalizes_legacy_manifest_aliases_and_exclusions():
    live = [
        "daily_reports",
        "equipment_inspections",
        "usage_events",
        "health_monitor_runs",
        "job_photo_thumb_cache",
        "meetings",
    ]
    captured = [
        "daily-reports",
        "equipment-inspections",
        "meetings",
    ]
    explicit_exclusions = [
        "usage_events",
        "health_monitor_runs",
        "job_photo_thumb_cache",
    ]

    missing = server._compute_backup_integrity_missing(live, captured, explicit_exclusions)

    assert missing == []


def test_integrity_missing_still_reports_true_uncaptured_live_collections():
    live = ["daily_reports", "meetings", "new_collection"]
    captured = ["daily-reports", "meetings"]

    missing = server._compute_backup_integrity_missing(live, captured, [])

    assert missing == ["new_collection"]


def test_scheduler_state_alive_uses_last_tick_timestamp():
    assert _scheduler_state_is_alive({"last_tick_ts": "2999-01-01T00:00:00+00:00"}) is True
    assert _scheduler_state_is_alive({"last_tick_ts": "2000-01-01T00:00:00+00:00"}) is False
    assert _scheduler_state_is_alive({"last_tick_ts": None}) is False


def test_canonical_scheduler_snapshot_returns_single_truth_tuple():
    out = canonical_scheduler_snapshot({"last_tick_ts": "2999-01-01T00:00:00+00:00"})
    assert out["alive"] is True
    assert out["is_healthy"] is True
    assert out["seconds_since_last_tick"] is not None


class _AsyncCollection:
    def __init__(self, docs=None):
        self._docs = docs or []

    async def find_one(self, *args, **kwargs):
        if not self._docs:
            return None
        return self._docs[0]

    def find(self, *args, **kwargs):
        return _AsyncCursor(self._docs)

    async def update_many(self, *args, **kwargs):  # noqa: ARG002
        return None


class _AsyncCursor:
    def __init__(self, docs):
        self._docs = list(docs)
        self._iter = iter(self._docs)

    def sort(self, *args, **kwargs):
        return self

    def limit(self, value):  # noqa: ARG002
        return self

    def __aiter__(self):
        self._iter = iter(self._docs)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise StopAsyncIteration from exc

    async def to_list(self, length=0):
        return list(self._docs[:length or None])


class _FakeDB:
    def __init__(self):
        self.backup_health = _AsyncCollection([
            {
                "mode": "complete-r2",
                "ok": True,
                "filename": "MASCI_complete_backup_2026-07-12_170033Z.zip",
                "size_bytes": 1054999651,
                "records": 253762,
                "ts": "2026-07-12T17:05:26.674825+00:00",
            }
        ])
        self.scheduler_locks = _AsyncCollection([
            {
                "_id": "backup_scheduler",
                "owner_id": "backup_scheduler:oldpod:123",
                "acquired_at": "2026-07-07T13:57:14.402000Z",
                "expires_at": "2026-07-07T13:58:44.402000Z",
            }
        ])
        self.drill_runs = _AsyncCollection([])
        self.backup_jobs = _AsyncCollection([])

    def __getitem__(self, name):
        return getattr(self, name)


async def _call_recovery_snapshot(fake_db):
    from routes.recovery_dashboard import _CACHE, build_recovery_dashboard_router  # noqa: PLC0415

    _CACHE["snapshot"] = None
    _CACHE["computed_at"] = 0.0

    async def _require_admin():
        return True

    router = build_recovery_dashboard_router(fake_db, _require_admin)
    endpoint = next(r.endpoint for r in router.routes if getattr(r, "path", "") == "/admin/recovery/snapshot")
    old_state = dict(server._BACKUP_SCHEDULER_STATE)
    server._BACKUP_SCHEDULER_STATE.update(
        {
            "alive": True,
            "last_tick_ts": "2999-01-01T00:00:00+00:00",
            "armed_at": "2999-01-01T00:00:00+00:00",
        }
    )
    try:
        return await endpoint(True)
    finally:
        server._BACKUP_SCHEDULER_STATE.clear()
        server._BACKUP_SCHEDULER_STATE.update(old_state)


def test_recovery_snapshot_prefers_canonical_scheduler_state_over_stale_lock():
    out = asyncio.run(_call_recovery_snapshot(_FakeDB()))
    assert out["scheduler"]["alive"] is True
    assert out["scheduler"]["is_healthy"] is True
    assert out["scheduler"]["signal_source"] == "backup_scheduler_state"
    scheduler_warnings = [w for w in out["warnings"] if (w or {}).get("kind") == "scheduler-quiet"]
    assert scheduler_warnings == []


def test_recovery_snapshot_hourly_activation_uses_same_canonical_scheduler_truth():
    out = asyncio.run(_call_recovery_snapshot(_FakeDB()))
    blocker_codes = {b.get("code") for b in (out.get("hourly_activation") or {}).get("activation_blockers", [])}
    assert out["scheduler"]["alive"] is True
    assert out["scheduler"]["is_healthy"] is True
    assert "scheduler_unhealthy" not in blocker_codes
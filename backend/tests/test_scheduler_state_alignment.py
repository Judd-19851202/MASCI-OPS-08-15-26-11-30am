from __future__ import annotations

import asyncio
from types import SimpleNamespace
import sys

sys.path.insert(0, "/app/backend")

import server  # noqa: E402


class _Cursor:
    def sort(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    async def __aiter__(self):
        if False:
            yield None


class _Collection:
    def find(self, *_args, **_kwargs):
        return _Cursor()


class _Db(SimpleNamespace):
    pass


def test_scheduler_state_endpoint_mirrors_hourly_activation_truth(monkeypatch) -> None:
    db = _Db(backup_health=_Collection())

    async def fake_build(_db, *, runtime_state=None):
        return {
            "r2_hourly_requested": True,
            "r2_hourly_effective": False,
            "r2_hourly_locked_off": True,
            "hourly_cadence_enabled": False,
            "activation_blockers": [{"reason": "active_backup_present"}],
            "activation_status": "BLOCKED BY SAFETY GUARD",
            "environment": "production",
            "last_evaluated_at": "2026-07-28T00:00:00+00:00",
            "next_eligible_hourly_slot": "2026-07-28T01:00:00+00:00",
        }

    async def fake_canonical(_db, state):
        return {
            "seconds_since_last_tick": 10,
            "alive": True,
            "is_healthy": True,
            "signal_source": "scheduler",
            "reason_code": "ok",
            "evidence_ts": "2026-07-28T00:00:00+00:00",
            "last_lock_ts": None,
            "owner_pod": "pod-1",
            "heartbeat_window_minutes": 15,
            "backup_fallback_window_minutes": 90,
        }

    monkeypatch.setattr(server, "db", db)
    monkeypatch.setattr(server, "_build_hourly_activation_state", fake_build)
    async def fake_runtime(_db):
        return {}

    monkeypatch.setattr(server, "_collect_backup_runtime_state", fake_runtime)
    monkeypatch.setitem(server.__dict__, "_BACKUP_SCHEDULER_STATE", {"backup_runtime": {}})

    import routes.recovery_dashboard as recovery_dashboard  # noqa: E402
    monkeypatch.setattr(recovery_dashboard, "build_canonical_scheduler_snapshot", fake_canonical)

    out = asyncio.run(server.admin_backups_scheduler_state(True))
    scheduler = out["scheduler"]
    assert scheduler["r2_hourly_requested"] is True
    assert scheduler["activation_environment"] == "production"
    assert scheduler["activation_status"] == "BLOCKED BY SAFETY GUARD"
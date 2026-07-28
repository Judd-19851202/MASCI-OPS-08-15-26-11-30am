from __future__ import annotations

import asyncio
import sys
from types import SimpleNamespace

sys.path.insert(0, "/app/backend")

import server  # noqa: E402


def test_backup_scheduler_healthy_uses_runtime_state_truth() -> None:
    assert server._backup_scheduler_healthy({
        "alive": True,
        "is_healthy": True,
        "last_tick_ts": None,
        "last_lock_ts": None,
    }) is True

    assert server._backup_scheduler_healthy({
        "alive": True,
        "is_healthy": False,
        "last_tick_ts": "2099-01-01T00:00:00+00:00",
    }) is False


def test_hourly_activation_uses_passed_runtime_state_for_scheduler_truth(monkeypatch) -> None:
    async def fake_list_stale_backup_jobs(_db, limit=10):  # noqa: ARG001
        return []

    async def fake_stale_scheduler_lock_present(_db):
        return False

    async def fake_backup_persistence_available(_db):
        return True

    async def fake_latest_complete_backup_hint(_db):
        return {"size_bytes": 123}

    monkeypatch.setattr(server, "list_stale_backup_jobs", fake_list_stale_backup_jobs)
    monkeypatch.setattr(server, "_stale_scheduler_lock_present", fake_stale_scheduler_lock_present)
    monkeypatch.setattr(server, "_backup_persistence_available", fake_backup_persistence_available)
    monkeypatch.setattr(server, "_latest_complete_backup_hint", fake_latest_complete_backup_hint)
    monkeypatch.setattr(server, "_canonical_app_env", lambda: "production")
    monkeypatch.setattr(server, "_backup_resource_preflight", lambda archive_size_bytes=None: {"ok": True, "reasons": [], "archive_size_bytes": archive_size_bytes})

    runtime_state = {
        "alive": True,
        "is_healthy": True,
        "overlap": {"backup_active": False, "restore_active": False},
        "active_jobs": [],
    }

    result = asyncio.run(server._build_hourly_activation_state(SimpleNamespace(), runtime_state=runtime_state))
    blocker_codes = {b["code"] for b in result["activation_blockers"]}
    assert "scheduler_unhealthy" not in blocker_codes


def test_admin_diag_aliases_call_underlying_routes(monkeypatch) -> None:
    async def fake_persistence_endpoint():
        return {"ok": True, "source": "persistence"}

    async def fake_runtime_endpoint(_admin=True):  # noqa: ARG001
        return {"ok": True, "source": "runtime"}

    async def fake_database_endpoint():
        return {"ok": True, "source": "database"}

    class _Route:
        def __init__(self, path, endpoint):
            self.path = path
            self.endpoint = endpoint

    class _Router:
        def __init__(self, routes):
            self.routes = routes

    monkeypatch.setattr(
        server,
        "build_admin_persistence_health_router",
        lambda **kwargs: _Router([_Route("/api/admin-strict/diag/persistence-health", fake_persistence_endpoint)]),
    )
    monkeypatch.setattr(
        server,
        "build_runtime_reliability_router",
        lambda **kwargs: _Router([_Route("/api/admin-strict/diag/runtime-health", fake_runtime_endpoint)]),
    )
    monkeypatch.setattr(
        server,
        "build_cluster_capacity_router",
        lambda **kwargs: _Router([_Route("/api/cluster/capacity", fake_database_endpoint)]),
    )

    persistence = asyncio.run(server.admin_persistence_health_alias(True))
    runtime = asyncio.run(server.admin_runtime_reliability_alias(True))
    database = asyncio.run(server.admin_database_alias(True))

    assert persistence == {"ok": True, "source": "persistence"}
    assert runtime == {"ok": True, "source": "runtime"}
    assert database == {"ok": True, "source": "database"}
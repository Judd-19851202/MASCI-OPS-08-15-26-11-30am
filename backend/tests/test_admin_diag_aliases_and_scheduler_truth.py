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


def test_hourly_activation_backfills_canonical_scheduler_truth_when_runtime_state_is_incomplete(monkeypatch) -> None:
    async def fake_list_stale_backup_jobs(_db, limit=10):  # noqa: ARG001
        return []

    async def fake_stale_scheduler_lock_present(_db):
        return False

    async def fake_backup_persistence_available(_db):
        return True

    async def fake_latest_complete_backup_hint(_db):
        return {"size_bytes": 123}

    async def fake_build_canonical_scheduler_snapshot(_db, _state):
        return {
            "alive": True,
            "is_healthy": True,
            "evidence_ts": "2099-01-01T00:00:00+00:00",
            "last_lock_ts": "2099-01-01T00:00:00+00:00",
            "last_tick_ts": None,
        }

    monkeypatch.setattr(server, "list_stale_backup_jobs", fake_list_stale_backup_jobs)
    monkeypatch.setattr(server, "_stale_scheduler_lock_present", fake_stale_scheduler_lock_present)
    monkeypatch.setattr(server, "_backup_persistence_available", fake_backup_persistence_available)
    monkeypatch.setattr(server, "_latest_complete_backup_hint", fake_latest_complete_backup_hint)
    monkeypatch.setattr(server, "_canonical_app_env", lambda: "production")
    monkeypatch.setattr(server, "_backup_resource_preflight", lambda archive_size_bytes=None: {"ok": True, "reasons": [], "archive_size_bytes": archive_size_bytes})
    monkeypatch.setattr("routes.recovery_dashboard.build_canonical_scheduler_snapshot", fake_build_canonical_scheduler_snapshot)

    runtime_state = {
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


def test_complete_r2_state_uses_canonical_scheduler_truth_for_hourly_activation(monkeypatch) -> None:
    async def fake_build_canonical_archive_lineage(*args, **kwargs):  # noqa: ARG001
        return {"authoritative_artifact": {}, "newest_observed_artifact": {}, "authoritative_recovery_point_time": None}

    async def fake_build_canonical_scheduler_snapshot(*args, **kwargs):  # noqa: ARG001
        return {
            "alive": True,
            "is_healthy": True,
            "evidence_ts": "2099-01-01T00:00:00+00:00",
            "last_lock_ts": "2099-01-01T00:00:00+00:00",
            "last_tick_ts": None,
        }

    async def fake_collect_backup_runtime_state(_db):
        return {"overlap": {"backup_active": False, "restore_active": False}, "active_jobs": []}

    async def fake_build_hourly_activation_state(_db, *, runtime_state=None):
        return {
            "activation_status": "ACTIVE",
            "activation_blockers": [],
            "r2_hourly_requested": True,
            "r2_hourly_effective": True,
            "r2_hourly_locked_off": False,
            "hourly_cadence_enabled": True,
            "environment": "production",
            "last_evaluated_at": "2099-01-01T00:00:00+00:00",
            "next_eligible_hourly_slot": "2099-01-01T01:00:00+00:00",
            "runtime_state_echo": runtime_state,
        }

    monkeypatch.setattr(server, "build_canonical_archive_lineage", fake_build_canonical_archive_lineage)
    monkeypatch.setattr(server, "_collect_backup_runtime_state", fake_collect_backup_runtime_state)
    monkeypatch.setattr(server, "_build_hourly_activation_state", fake_build_hourly_activation_state)
    monkeypatch.setattr("routes.recovery_dashboard.build_canonical_scheduler_snapshot", fake_build_canonical_scheduler_snapshot)
    monkeypatch.setattr(server, "_canonical_app_env", lambda: "production")
    monkeypatch.setattr(server, "_canonical_db_name", lambda: "masci_safety")

    class _FakeCollection:
        async def find_one(self, *args, **kwargs):  # noqa: ARG002
            return None

    class _FakeDB:
        backup_health = _FakeCollection()

    old_db = server.db
    server.db = _FakeDB()
    try:
        out = asyncio.run(server.admin_complete_r2_state(True))
    finally:
        server.db = old_db

    echoed = (out.get("hourly_activation") or {}).get("runtime_state_echo") or {}
    assert echoed.get("alive") is True
    assert echoed.get("is_healthy") is True
    assert out.get("hourly_activation", {}).get("activation_blockers") == []


def test_run_scheduled_backup_defers_when_complete_or_restore_job_active(monkeypatch) -> None:
    async def fake_get_active_backup_jobs(_db):
        return [{"kind": server.BACKUP_JOB_KIND_COMPLETE_R2, "state": "running"}]

    monkeypatch.setattr(server, "get_active_backup_jobs", fake_get_active_backup_jobs)
    monkeypatch.setattr(server, "classify_backup_overlap", lambda jobs: {
        "backup_active": True,
        "restore_active": False,
        "active_backups": jobs,
        "active_restores": [],
        "blocking_backups": jobs,
        "blocking_restores": [],
        "reclaimable_backups": [],
        "reclaimable_restores": [],
        "overlap_blocked": False,
    })
    result = asyncio.run(server._run_scheduled_backup(SimpleNamespace(), lite_mode=True))
    assert result["skipped"] is True
    assert result["reason"] == "overlap_backup_active"


def test_manual_run_now_has_active_job_guard():
    src = __import__('pathlib').Path('/app/backend/server.py').read_text()
    assert 'active_jobs = await get_active_backup_jobs(db)' in src
    assert 'Another backup or restore job is already active.' in src


def test_iter_photo_refs_discovers_nested_doc_refs_and_photo_refs():
    doc = {
        "attachments": [
            {"file_data": "doc://bucket/documents/2026/07/a.pdf"},
            {"meta": {"image": "photo://bucket/photos/2026/07/a.jpg"}},
        ],
        "source_file_ref": "photo://bucket/photos/2026/07/b.jpg",
    }
    refs = list(server._iter_photo_refs(doc))
    assert "doc://bucket/documents/2026/07/a.pdf" in refs
    assert "photo://bucket/photos/2026/07/a.jpg" in refs
    assert "photo://bucket/photos/2026/07/b.jpg" in refs
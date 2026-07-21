from __future__ import annotations

import asyncio
import os

import pytest


pytestmark = pytest.mark.asyncio


@pytest.fixture
def server_module(monkeypatch):
    monkeypatch.setenv("APP_ENV", "preview")
    monkeypatch.setenv("DB_NAME", "masci_safety_preview")
    monkeypatch.setenv("MONGO_URL", "mongodb://localhost:27017/masci_safety_preview")
    monkeypatch.setenv("AUTO_EMAIL_REPORTS", "false")
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    monkeypatch.setenv("MAINTAINX_WRITE_ENABLED", "false")
    monkeypatch.setenv("MAINTAINX_SYNC_ENABLED", "false")
    monkeypatch.setenv("SESSION_TIMEOUTS_ENABLED", "false")
    import server  # noqa: PLC0415

    server._reset_runtime_db_state_for_tests()
    server.app.state.ready = False
    server.app.state.runtime_monitor_started = False
    server.app.state.read_only_validation_active = False
    server.app.state.runtime_identity_bundle = None
    return server


class _DummyDatabase:
    name = "dummy"

    async def command(self, *_args, **_kwargs):
        return {"ok": 1}


class _DummyClient:
    def __init__(self, *_args, **_kwargs):
        self.closed = False

    def __getitem__(self, _key):
        return _DummyDatabase()

    def close(self):
        self.closed = True


async def _run_boot(server, monkeypatch, env: dict[str, str]):
    server._reset_runtime_db_state_for_tests()
    server.app.state.ready = False
    server.app.state.runtime_monitor_started = False
    server.app.state.read_only_validation_active = False
    server.app.state.runtime_identity_bundle = None
    for key in [
        "APP_ENV",
        "DB_NAME",
        "MONGO_URL",
        "ENFORCE_DB_ISOLATION",
        "READ_ONLY_VALIDATION",
        "READ_ONLY_VALIDATION_REQUESTED",
        "READ_ONLY_VALIDATION_MODE",
        "READ_ONLY_VALIDATION_DB_AUTHORITY",
        "READ_ONLY_MODE",
        "SCHEDULER_ENABLED",
        "AUTO_EMAIL_REPORTS",
        "MAINTAINX_WRITE_ENABLED",
        "MAINTAINX_SYNC_ENABLED",
        "AI_GATEWAY_ENABLED",
        "DR_V2_AI_ENABLED",
        "ODS_ENABLED",
        "READ_ONLY_VALIDATION_TRUST_SPINE_DISABLED",
        "READ_ONLY_VALIDATION_WEBHOOKS_DISABLED",
        "READ_ONLY_VALIDATION_ZERO_WRITE_PROVEN",
        "APP_DOMAIN",
        "SESSION_TIMEOUTS_ENABLED",
    ]:
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    started_monitor = {"count": 0}

    def _fake_start_runtime_monitor(app, database):
        started_monitor["count"] += 1
        app.state.runtime_monitor_started = True
        return None

    monkeypatch.setattr(server, "AsyncIOMotorClient", _DummyClient)
    monkeypatch.setattr(server, "_stabilize_runtime_db_connection", lambda _db: asyncio.sleep(0))
    monkeypatch.setattr(server, "start_runtime_monitor", _fake_start_runtime_monitor)

    return started_monitor


async def test_preview_shared_atlas_with_preview_user_and_preview_db_boots(server_module, monkeypatch):
    server = server_module
    started_monitor = await _run_boot(server, monkeypatch, {
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb+srv://masci_preview_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
        "SCHEDULER_ENABLED": "false",
        "AUTO_EMAIL_REPORTS": "false",
    })

    await server._bootstrap_runtime_db()

    assert server.db.get_target() is not None
    assert started_monitor["count"] == 1


async def test_preview_to_production_user_without_ro_validation_refuses_boot(server_module, monkeypatch):
    server = server_module
    await _run_boot(server, monkeypatch, {
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb+srv://masci_prod_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
        "SCHEDULER_ENABLED": "false",
        "AUTO_EMAIL_REPORTS": "false",
    })

    with pytest.raises(RuntimeError, match="PREVIEW_PRODUCTION_USER_REFUSED"):
        await server._bootstrap_runtime_db()

    assert server.db.get_target() is None
    assert getattr(server.app.state, "mongo_client", None) is None


async def test_preview_to_production_db_without_ro_validation_refuses_boot(server_module, monkeypatch):
    server = server_module
    await _run_boot(server, monkeypatch, {
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety",
        "MONGO_URL": "mongodb://localhost:27017/masci_safety",
        "ENFORCE_DB_ISOLATION": "true",
    })

    with pytest.raises(RuntimeError, match="Preview runtime must use a preview DB name"):
        await server._bootstrap_runtime_db()

    assert server.db.get_target() is None


async def test_preview_local_preview_database_boots(server_module, monkeypatch):
    server = server_module
    started_monitor = await _run_boot(server, monkeypatch, {
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb://localhost:27017/masci_safety_preview",
        "ENFORCE_DB_ISOLATION": "false",
        "SCHEDULER_ENABLED": "false",
        "AUTO_EMAIL_REPORTS": "false",
    })

    await server._bootstrap_runtime_db()
    assert server.db.get_target() is not None
    assert started_monitor["count"] == 1


async def test_production_approved_target_boots(server_module, monkeypatch):
    server = server_module
    started_monitor = await _run_boot(server, monkeypatch, {
        "APP_ENV": "production",
        "DB_NAME": "masci_safety",
        "MONGO_URL": "mongodb+srv://masci_prod_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
        "SCHEDULER_ENABLED": "false",
        "AUTO_EMAIL_REPORTS": "false",
    })

    await server._bootstrap_runtime_db()
    assert server.db.get_target() is not None
    assert started_monitor["count"] == 1


async def test_production_wrong_host_correct_db_refuses_boot(server_module, monkeypatch):
    server = server_module
    await _run_boot(server, monkeypatch, {
        "APP_ENV": "production",
        "DB_NAME": "masci_safety",
        "MONGO_URL": "mongodb+srv://masci_prod_user:s3cret@wrong-cluster.mongodb.net/masci_safety",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
    })

    with pytest.raises(RuntimeError, match="CLUSTER_HOST_MISMATCH"):
        await server._bootstrap_runtime_db()


async def test_ro_validation_requested_but_incomplete_refuses_boot(server_module, monkeypatch):
    server = server_module
    await _run_boot(server, monkeypatch, {
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb+srv://masci_prod_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
        "READ_ONLY_VALIDATION": "true",
        "READ_ONLY_MODE": "true",
        "SCHEDULER_ENABLED": "false",
        "AUTO_EMAIL_REPORTS": "false",
    })

    with pytest.raises(RuntimeError, match="READ_ONLY_VALIDATION_INCOMPLETE"):
        await server._bootstrap_runtime_db()

    assert server.db.get_target() is None


async def test_ro_validation_fully_valid_permits_boot_and_suppresses_monitor(server_module, monkeypatch):
    server = server_module
    started_monitor = await _run_boot(server, monkeypatch, {
        "APP_ENV": "preview",
        "DB_NAME": "masci_safety_preview",
        "MONGO_URL": "mongodb+srv://masci_prod_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety_preview",  # secret-scan: allow-line
        "ENFORCE_DB_ISOLATION": "true",
        "READ_ONLY_VALIDATION": "true",
        "READ_ONLY_MODE": "true",
        "READ_ONLY_VALIDATION_DB_AUTHORITY": "read_only",
        "SESSION_TIMEOUTS_ENABLED": "false",
        "SCHEDULER_ENABLED": "false",
        "AUTO_EMAIL_REPORTS": "false",
        "MAINTAINX_WRITE_ENABLED": "false",
        "MAINTAINX_SYNC_ENABLED": "false",
        "AI_GATEWAY_ENABLED": "false",
        "DR_V2_AI_ENABLED": "false",
        "ODS_ENABLED": "false",
        "READ_ONLY_VALIDATION_TRUST_SPINE_DISABLED": "true",
        "READ_ONLY_VALIDATION_WEBHOOKS_DISABLED": "true",
        "READ_ONLY_VALIDATION_ZERO_WRITE_PROVEN": "true",
        "APP_DOMAIN": "preview-readonly.example.test",
    })

    await server._bootstrap_runtime_db()

    assert server.db.get_target() is not None
    assert server.app.state.read_only_validation_active is True
    assert started_monitor["count"] == 0
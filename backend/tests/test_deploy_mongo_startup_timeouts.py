from __future__ import annotations

import importlib
import os
import sys


sys.path.insert(0, "/app/backend")


def _fresh_server_module():
    sys.modules.pop("server", None)
    return importlib.import_module("server")


def test_mongo_client_kwargs_have_fail_fast_timeouts(monkeypatch):
    monkeypatch.setenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "30000")
    monkeypatch.setenv("MONGO_CONNECT_TIMEOUT_MS", "30001")
    monkeypatch.setenv("MONGO_SOCKET_TIMEOUT_MS", "30002")
    srv = _fresh_server_module()
    kwargs = srv._mongo_client_kwargs()
    assert kwargs["tz_aware"] is True
    assert kwargs["maxPoolSize"] == 50
    assert kwargs["serverSelectionTimeoutMS"] == 30000
    assert kwargs["connectTimeoutMS"] == 30001
    assert kwargs["socketTimeoutMS"] == 30002


def test_mongo_client_kwargs_default_to_safe_production_values(monkeypatch):
    monkeypatch.delenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", raising=False)
    monkeypatch.delenv("MONGO_CONNECT_TIMEOUT_MS", raising=False)
    monkeypatch.delenv("MONGO_SOCKET_TIMEOUT_MS", raising=False)
    srv = _fresh_server_module()
    kwargs = srv._mongo_client_kwargs()
    assert kwargs["serverSelectionTimeoutMS"] == 30000
    assert kwargs["connectTimeoutMS"] == 30000
    assert kwargs["socketTimeoutMS"] == 30000


def test_load_runtime_db_config_defaults_production_db_name_to_preview(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("MONGO_URL", "mongodb+srv://masci_prod_user:pw@example.mongodb.net/")
    monkeypatch.delenv("DB_NAME", raising=False)
    srv = _fresh_server_module()
    try:
        srv._load_runtime_db_config(require_runtime=True)
    except RuntimeError as exc:
        assert 'DB_NAME' in str(exc)
    else:
        raise AssertionError('expected missing DB_NAME to fail')


def test_stabilize_runtime_db_connection_retries_once_before_succeeding(monkeypatch):
    srv = _fresh_server_module()
    monkeypatch.setenv("MONGO_STARTUP_PING_ATTEMPTS", "2")
    monkeypatch.setenv("MONGO_STARTUP_PING_DELAY_SECONDS", "1")
    sleeps = []

    class _DB:
        def __init__(self):
            self.calls = 0

        async def command(self, name):
            assert name == "ping"
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("temporary atlas wobble")
            return {"ok": 1}

    async def _fake_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(srv.asyncio, "sleep", _fake_sleep)
    db = _DB()
    srv.asyncio.run(srv._stabilize_runtime_db_connection(db))
    assert db.calls == 2
    assert sleeps == [1]


def test_verify_env_db_alignment_blocks_preview_name_in_production():
    srv = _fresh_server_module()
    try:
        srv._verify_env_db_alignment('production', 'masci_safety_preview', 'mongodb+srv://masci_prod_user:<redacted>@example.mongodb.net/')
    except RuntimeError as exc:
        assert 'refuses preview DB name' in str(exc)
    else:
        raise AssertionError('expected production preview-name rejection')


def test_redact_mongo_target_hides_credentials():
    srv = _fresh_server_module()
    redacted = srv._redact_mongo_target('mongodb+srv://user:secret@masci-prod.1nduwmg.mongodb.net/?retryWrites=true')
    assert 'secret' not in redacted
    assert '<redacted>@' in redacted
from __future__ import annotations

import asyncio
import os
import subprocess
import sys

import pytest


ROOT = "/app"
BACKEND = "/app/backend"


def _base_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = BACKEND
    return env


def test_import_without_runtime_secrets_is_safe() -> None:
    env = _base_env()
    env.pop("MONGO_URL", None)
    env.pop("DB_NAME", None)
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, '/app/backend'); import server; print('IMPORT_SAFE')",
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=ROOT,
    )
    assert proc.returncode == 0, proc.stderr
    assert "IMPORT_SAFE" in proc.stdout
    assert "KeyError: 'MONGO_URL'" not in proc.stderr


def test_import_safe_route_and_openapi_inspection_without_runtime_secrets() -> None:
    env = _base_env()
    env.pop("MONGO_URL", None)
    env.pop("DB_NAME", None)
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, '/app/backend'); import server; "
            "print('ROUTES', len([r for r in server.app.routes if hasattr(r, 'path')])); "
            "print('OPENAPI', len(server.app.openapi().get('paths', {})))",
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=ROOT,
    )
    assert proc.returncode == 0, proc.stderr
    assert "ROUTES" in proc.stdout
    assert "OPENAPI" in proc.stdout


def test_release_identity_verifier_module_imports_without_runtime_secrets() -> None:
    env = _base_env()
    env.pop("MONGO_URL", None)
    env.pop("DB_NAME", None)
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, '/app/backend'); "
            "import scripts.verify_release_identity as mod; print(callable(mod.main))",
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=ROOT,
    )
    assert proc.returncode == 0, proc.stderr
    assert "True" in proc.stdout


def test_runtime_db_startup_fails_clearly_without_required_env(monkeypatch) -> None:
    import server

    server._reset_runtime_db_state_for_tests()
    monkeypatch.delenv("MONGO_URL", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)

    with pytest.raises(server.RuntimeConfigError) as exc:
        asyncio.run(server._bootstrap_runtime_db())

    msg = str(exc.value)
    assert "Required runtime configuration missing" in msg
    assert "MONGO_URL" in msg and "DB_NAME" in msg
    assert "mongodb://" not in msg


def test_runtime_db_startup_and_shutdown_use_single_client(monkeypatch) -> None:
    import server

    created = []

    class _FakeClient:
        def __init__(self, url, **kwargs):
            self.url = url
            self.kwargs = kwargs
            self.close_count = 0

        def __getitem__(self, name):
                class FakeDB:
                    def __init__(self, db_name, client):
                        self.name = db_name
                        self.client = client

                    async def command(self, _cmd):
                        return {"ok": 1}

                return FakeDB(name, self)

        def close(self):
            self.close_count += 1

    def _fake_client(url, **kwargs):
        inst = _FakeClient(url, **kwargs)
        created.append(inst)
        return inst

    server._reset_runtime_db_state_for_tests()
    monkeypatch.setenv("MONGO_URL", "mongodb+srv://masci_prod_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety_preview")
    monkeypatch.setenv("DB_NAME", "masci_safety_preview")
    monkeypatch.setenv("APP_ENV", "preview")
    monkeypatch.setenv("ENFORCE_DB_ISOLATION", "true")
    monkeypatch.setenv("READ_ONLY_VALIDATION", "true")
    monkeypatch.setenv("READ_ONLY_MODE", "true")
    monkeypatch.setenv("READ_ONLY_VALIDATION_DB_AUTHORITY", "read_only")
    monkeypatch.setenv("SESSION_TIMEOUTS_ENABLED", "false")
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    monkeypatch.setenv("AUTO_EMAIL_REPORTS", "false")
    monkeypatch.setenv("MAINTAINX_WRITE_ENABLED", "false")
    monkeypatch.setenv("MAINTAINX_SYNC_ENABLED", "false")
    monkeypatch.setenv("AI_GATEWAY_ENABLED", "false")
    monkeypatch.setenv("DR_V2_AI_ENABLED", "false")
    monkeypatch.setenv("ODS_ENABLED", "false")
    monkeypatch.setenv("READ_ONLY_VALIDATION_TRUST_SPINE_DISABLED", "true")
    monkeypatch.setenv("READ_ONLY_VALIDATION_WEBHOOKS_DISABLED", "true")
    monkeypatch.setenv("READ_ONLY_VALIDATION_ZERO_WRITE_PROVEN", "true")
    monkeypatch.setenv("APP_DOMAIN", "preview-readonly.example.test")
    monkeypatch.setattr(server, "AsyncIOMotorClient", _fake_client)

    asyncio.run(server._bootstrap_runtime_db())
    asyncio.run(server._bootstrap_runtime_db())

    assert len(created) == 1
    assert server.client is created[0]
    assert server.db.get_target() is not None
    assert server.app.state.db_name == "masci_safety_preview"

    asyncio.run(server.shutdown_db_client())
    assert created[0].close_count == 1
    assert server.client is None
    assert server.db.get_target() is None

    asyncio.run(server.shutdown_db_client())
    assert created[0].close_count == 1


def test_runtime_db_test_override_compatibility() -> None:
    import server

    fake_db = object()
    original = server._get_db_target_for_tests()
    server._set_db_target_for_tests(fake_db)
    try:
        assert server._get_db_target_for_tests() is fake_db
    finally:
        server._set_db_target_for_tests(original)
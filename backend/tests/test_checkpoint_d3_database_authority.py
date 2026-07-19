from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from lib.database_client_governance import discover_database_client_inventory, inventory_summary


def test_inventory_has_one_canonical_runtime_client() -> None:
    rows = discover_database_client_inventory("/app")
    constructors = [r for r in rows if r["occurrence_type"] == "client_constructor"]
    canonical = [r for r in constructors if r["classification"] == "CANONICAL_RUNTIME_CLIENT"]
    assert len(canonical) == 1
    assert canonical[0]["file"] == "backend/lib/database_authority.py"


def test_inventory_has_no_duplicate_or_unknown_runtime_clients() -> None:
    rows = discover_database_client_inventory("/app")
    constructors = [r for r in rows if r["occurrence_type"] == "client_constructor" and r["runtime_or_non_runtime"] == "runtime"]
    assert not [r for r in constructors if r["classification"] in {"DUPLICATE_RUNTIME_CLIENT", "REQUEST_SCOPED_CLIENT_DEFECT", "UNSAFE_FALLBACK_CLIENT", "UNOWNED_CLIENT", "UNKNOWN_DO_NOT_TOUCH"}]


def test_runtime_routes_and_services_do_not_read_mongo_url_or_db_name_directly() -> None:
    banned = []
    for path in Path("/app/backend/routes").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if 'os.environ.get("MONGO_URL")' in text or 'os.environ["MONGO_URL"]' in text or 'os.environ.get("DB_NAME")' in text or 'os.environ["DB_NAME"]' in text:
            banned.append(str(path))
    for path in Path("/app/backend/services").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if 'os.environ.get("MONGO_URL")' in text or 'os.environ["MONGO_URL"]' in text or 'os.environ.get("DB_NAME")' in text or 'os.environ["DB_NAME"]' in text:
            banned.append(str(path))
    assert banned == []


def test_inventory_and_register_files_exist() -> None:
    assert Path("/app/docs/governance/database_client_inventory.json").exists()
    assert Path("/app/docs/governance/DATABASE_CLIENT_AUTHORITY_REGISTER.md").exists()


def test_inventory_summary_has_no_request_scoped_or_unsafe_clients() -> None:
    summary = inventory_summary(discover_database_client_inventory("/app"))
    assert summary["request_scoped"] == 0
    assert summary["unsafe"] == 0
    assert summary["unknown"] == 0


def test_failed_startup_closes_partial_client(monkeypatch) -> None:
    import server

    created = []

    class _FakeClient:
        def __init__(self, url, **kwargs):
            self.url = url
            self.kwargs = kwargs
            self.close_count = 0

        def __getitem__(self, name):
            return type("FakeDB", (), {"name": name, "client": self})()

        def close(self):
            self.close_count += 1

    def _fake_client(url, **kwargs):
        inst = _FakeClient(url, **kwargs)
        created.append(inst)
        return inst

    async def _boom(_db):
        raise RuntimeError("stabilize failed")

    server._reset_runtime_db_state_for_tests()
    monkeypatch.setenv("MONGO_URL", "mongodb+srv://masci_prod_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety_preview")  # secret-scan: allow-line
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
    monkeypatch.setattr(server, "_stabilize_runtime_db_connection", _boom)

    with pytest.raises(RuntimeError, match="stabilize failed"):
        asyncio.run(server._bootstrap_runtime_db())

    assert len(created) == 1
    assert created[0].close_count == 1
    assert server.client is None
    assert server.db.get_target() is None


def test_shutdown_close_is_idempotent(monkeypatch) -> None:
    import server

    created = []

    class _FakeClient:
        def __init__(self, url, **kwargs):
            self.close_count = 0

        def __getitem__(self, name):
            return type("FakeDB", (), {"name": name, "client": self})()

        def close(self):
            self.close_count += 1

    def _fake_client(url, **kwargs):
        inst = _FakeClient(url, **kwargs)
        created.append(inst)
        return inst

    async def _ok(_db):
        return None

    server._reset_runtime_db_state_for_tests()
    monkeypatch.setenv("MONGO_URL", "mongodb+srv://masci_prod_user:s3cret@masci-prod.1nduwmg.mongodb.net/masci_safety_preview")  # secret-scan: allow-line
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
    monkeypatch.setattr(server, "_stabilize_runtime_db_connection", _ok)

    asyncio.run(server._bootstrap_runtime_db())
    asyncio.run(server.shutdown_db_client())
    asyncio.run(server.shutdown_db_client())
    assert created[0].close_count == 1
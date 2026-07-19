from __future__ import annotations

import pytest

from db_isolation_failsafe import assert_db_isolation


class _FakeDb:
    def __init__(self, should_allow: bool):
        self._should_allow = should_allow

    async def list_collection_names(self):
        if self._should_allow:
            return ["daily_reports"]
        raise PermissionError("denied")


class _FakeClient:
    def __init__(self, allowed_dbs: set[str]):
        self._allowed_dbs = allowed_dbs

    def __getitem__(self, name: str):
        return _FakeDb(name in self._allowed_dbs)


@pytest.mark.asyncio
async def test_preview_enforced_violation_still_fails_fast(monkeypatch):
    monkeypatch.setenv("APP_ENV", "preview")
    monkeypatch.setenv("DB_NAME", "masci_safety_preview")
    monkeypatch.setenv("ENFORCE_DB_ISOLATION", "true")
    client = _FakeClient({"masci_safety"})
    with pytest.raises(SystemExit) as exc:
        await assert_db_isolation(client)
    assert exc.value.code == 99


@pytest.mark.asyncio
async def test_production_enforced_violation_logs_but_does_not_exit(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DB_NAME", "masci_safety")
    monkeypatch.setenv("ENFORCE_DB_ISOLATION", "true")
    client = _FakeClient({"masci_safety_preview"})
    result = await assert_db_isolation(client)
    assert result["status"] == "violation"
    assert result["violations"][0]["db"] == "masci_safety_preview"
from __future__ import annotations

import asyncio
import sys


sys.path.insert(0, "/app/backend")

import server  # noqa: E402, PLC0415


class _AsyncCollection:
    def __init__(self, doc=None):
        self._doc = doc

    async def find_one(self, *args, **kwargs):
        return self._doc


class _FakeDB:
    def __init__(self, doc=None):
        self.backup_health = _AsyncCollection(doc)


def test_complete_r2_state_falls_back_to_backup_health_when_scheduler_memory_empty(monkeypatch):
    old_db = server._get_db_target_for_tests()
    old_state = dict(server._BACKUP_SCHEDULER_STATE)
    try:
        server._set_db_target_for_tests(_FakeDB(
            {
                "filename": "MASCI_complete_backup_2026-07-13_090407Z.zip",
                "size_bytes": 1062240399,
                "ts": "2026-07-13T09:09:01.740745+00:00",
            }
        ))
        server._BACKUP_SCHEDULER_STATE["last_r2_complete"] = None
        server._BACKUP_SCHEDULER_STATE["last_r2_complete_date"] = None
        server._BACKUP_SCHEDULER_STATE["last_r2_complete_hour"] = None

        out = asyncio.run(server.admin_complete_r2_state(True))
        assert out["nightly_last"]["filename"] == "MASCI_complete_backup_2026-07-13_090407Z.zip"
        assert out["nightly_last"]["r2_key"] == "backups/auto-90d/MASCI_complete_backup_2026-07-13_090407Z.zip"
        assert out["nightly_last_date"] == "2026-07-13"
        assert out["nightly_last_hour"] == "2026-07-13T09"
    finally:
        server._set_db_target_for_tests(old_db)
        server._BACKUP_SCHEDULER_STATE.clear()
        server._BACKUP_SCHEDULER_STATE.update(old_state)
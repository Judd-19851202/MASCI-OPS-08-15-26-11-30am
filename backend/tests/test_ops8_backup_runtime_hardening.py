from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/app/backend")

from lib.backup_runtime import classify_backup_overlap  # noqa: E402
import backup_verification  # noqa: E402
import server  # noqa: E402


def test_backup_resource_preflight_rejects_disk_pressure(monkeypatch):
    monkeypatch.setattr(server, "_disk_pct_used", lambda path="/app": 91)
    monkeypatch.setattr(server, "_disk_free_bytes", lambda path="/app": 10 * 1024 * 1024 * 1024)
    out = server._backup_resource_preflight(archive_size_bytes=500 * 1024 * 1024)
    assert out["ok"] is False
    assert any("app_disk_pressure" in item for item in out["reasons"])


def test_backup_resource_preflight_rejects_low_tmp_headroom(monkeypatch):
    monkeypatch.setattr(server, "_disk_pct_used", lambda path="/app": 40)
    monkeypatch.setattr(server, "_disk_free_bytes", lambda path="/app": 1024 * 1024 * 1024)
    out = server._backup_resource_preflight(archive_size_bytes=2 * 1024 * 1024 * 1024)
    assert out["ok"] is False
    assert any("tmp_" in item for item in out["reasons"])


def test_classify_backup_overlap_detects_backup_and_restore():
    active = [
        {"kind": "complete-r2", "state": "running", "job_id": "a"},
        {"kind": "restore-import", "state": "queued", "job_id": "b"},
    ]
    out = classify_backup_overlap(active)
    assert out["backup_active"] is True
    assert out["restore_active"] is True
    assert out["overlap_blocked"] is True


class _Cursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self._limit = None

    def sort(self, key, direction=-1):
        self.rows.sort(key=lambda r: r.get(key) or "", reverse=(direction == -1))
        return self

    def limit(self, n):
        self._limit = n
        return self

    def __aiter__(self):
        self._iter = iter(self.rows[: self._limit] if self._limit is not None else self.rows)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


class _Collection:
    def __init__(self, rows=None):
        self.rows = list(rows or [])

    def find(self, *args, **kwargs):
        return _Cursor(self.rows)

    async def count_documents(self, query=None):
        return len(self.rows)


class _VerificationDB:
    def __init__(self, rows):
        self.backup_health = _Collection(rows)

    def __getitem__(self, name):
        return _Collection([])


def test_verification_last_r2_ignores_usage_alert(monkeypatch):
    async def _fake_jobs(db, *, kind=None, limit=20):
        return []

    monkeypatch.setattr(backup_verification, "list_backup_jobs", _fake_jobs)

    async def _fake_r2(prefix="backups/"):
        return [{
            "key": "backups/auto-90d/test.zip",
            "filename": "test.zip",
            "size_bytes": 123,
            "last_modified_iso": datetime.now(timezone.utc).isoformat(),
        }]

    monkeypatch.setattr(backup_verification, "list_r2_backup_archives", _fake_r2)
    rows = [
        {"ts": "2026-07-24T18:00:00+00:00", "ok": True, "mode": "r2-usage-alert"},
        {"ts": "2026-07-24T17:00:00+00:00", "ok": True, "mode": "complete-r2", "filename": "good.zip"},
        {"ts": "2026-07-24T16:00:00+00:00", "ok": False, "mode": "complete-r2-error", "error": "boom"},
        {"ts": "2026-07-24T15:00:00+00:00", "ok": False, "mode": "verification-marker", "id": "_verification_last_run"},
    ]
    report = asyncio.run(backup_verification.build_verification_report(_VerificationDB(rows)))
    assert report["ledger"]["last_r2"]["mode"] == "complete-r2"
    assert report["ledger"]["last_failure"]["mode"] == "complete-r2-error"

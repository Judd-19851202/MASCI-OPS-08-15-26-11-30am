"""Track 27.09 · backup observability regression locks.

Two truthful-read defects are fixed and must not regress:

1. `/api/admin/r2/lifecycle/inventory?prefix=backups/` must return the same
   truthful population as `prefix=backups`.
2. `/api/admin/backups/integrity-check` must surface the latest R2 backup
   metadata from the real archive manifest when that evidence exists.
"""
from __future__ import annotations

import asyncio
import sys

import pytest

from routes.admin_r2_lifecycle import _inventory_prefix_filter


def test_track_27_09_inventory_prefix_filter_normalizes_backups_slash():
    assert _inventory_prefix_filter("backups") == {"prefix": "backups"}
    assert _inventory_prefix_filter("backups/") == {"prefix": "backups"}
    assert _inventory_prefix_filter("/backups///") == {"prefix": "backups"}


def test_track_27_09_inventory_prefix_filter_uses_key_regex_for_nested_paths():
    out = _inventory_prefix_filter("backups/auto-90d/")
    assert "key" in out and "$regex" in out["key"]
    assert out["key"]["$regex"].startswith(r"^backups/auto\-90d")


@pytest.fixture(scope="module")
def server_module():
    sys.path.insert(0, "/app/backend")
    import server  # noqa: PLC0415
    return server


class _AsyncCollection:
    def __init__(self, doc=None):
        self._doc = doc

    async def find_one(self, *args, **kwargs):
        return self._doc

    def find(self, *args, **kwargs):
        class _Cursor:
            def __init__(self, docs):
                self._docs = docs if isinstance(docs, list) else ([docs] if docs else [])

            async def to_list(self, length=None):
                return self._docs[:length]

        return _Cursor(self._doc)


class _FakeDB:
    def __init__(self):
        self.backup_health = _AsyncCollection(
            [
                {
                    "filename": "MASCI_complete_backup_2026-07-12_140050Z.zip",
                    "size_bytes": 1048781324,
                    "records": 253505,
                    "ts": "2026-07-12T14:05:40.570641+00:00",
                },
                {
                    "filename": "MASCI_complete_backup_2026-07-12_120000Z.zip",
                    "size_bytes": 1040000000,
                    "records": 250000,
                    "ts": "2026-07-12T12:00:40.570641+00:00",
                },
            ]
        )
        self.backup_drift_history = _AsyncCollection(
            {
                "captured_collections": ["fallback_a"],
                "total_records": 111,
            }
        )
        self.drill_runs = _AsyncCollection(None)

    async def list_collection_names(self):
        return ["backup_health", "daily_reports", "meetings", "system.profile"]


def test_track_27_09_integrity_check_prefers_r2_manifest(monkeypatch, server_module):
    import backup_verification  # noqa: PLC0415

    async def _fake_list_r2_backup_archives(prefix: str = "backups/"):
        return [
            {
                "key": "backups/auto-90d/MASCI_complete_backup_2026-07-12_140050Z.zip",
                "size_bytes": 1048781324,
                "last_modified_iso": "2026-07-12T14:05:40.161000+00:00",
            }
        ]

    async def _fake_read_r2_backup_manifest(key: str):
        return {
            "manifest_name": "MANIFEST.json",
            "content_length": 1048781324,
            "manifest": {
                "generated_at": "2026-07-12T14:05:40.000000+00:00",
                "captured_collections": ["backup_health", "daily_reports", "meetings"],
                "per_kind": {"backup_health": 20, "daily_reports": 215, "meetings": 56},
                "total_records": 253505,
            },
        }

    monkeypatch.setattr(backup_verification, "list_r2_backup_archives", _fake_list_r2_backup_archives)
    monkeypatch.setattr(backup_verification, "read_r2_backup_manifest", _fake_read_r2_backup_manifest)
    monkeypatch.setattr(server_module, "_list_stored_backups", lambda: [])

    fake_db = _FakeDB()

    async def _call_route():
        fn = None
        for route in server_module.app.routes:
            if getattr(route, "path", "") == "/api/admin/backups/integrity-check":
                fn = route.endpoint
                break
        assert fn is not None, "integrity-check route not found"
        # Swap the module-global db the endpoint closes over.
        old_db = server_module.db
        server_module.db = fake_db
        try:
            return await fn(True)
        finally:
            server_module.db = old_db

    out = asyncio.run(_call_route())
    assert out["last_backup_object_key"] == "backups/auto-90d/MASCI_complete_backup_2026-07-12_140050Z.zip"
    assert out["last_backup_filename"] == "MASCI_complete_backup_2026-07-12_140050Z.zip"
    assert out["captured_collections"] == ["backup_health", "daily_reports", "meetings"]
    assert out["collection_counts"] == {"backup_health": 20, "daily_reports": 215, "meetings": 56}
    assert out["document_count"] == 253505
    assert out["archive_size_bytes"] == 1048781324
    assert out["evidence_source"] == "r2:MANIFEST.json"
    assert out["integrity_result"] == "PASS"
    assert len(out["recent_backups"]) >= 2
    assert out["recent_backups"][0]["filename"] == "MASCI_complete_backup_2026-07-12_140050Z.zip"
    assert out["ok"] is True
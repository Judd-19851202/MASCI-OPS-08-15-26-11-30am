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
    assert out["verifier_version"] == server_module.BACKUP_VERIFIER_VERSION
    assert out["expected_collection_count"] == 3
    assert len(out["recent_backups"]) >= 2
    assert out["recent_backups"][0]["filename"] == "MASCI_complete_backup_2026-07-12_140050Z.zip"
    assert out["recent_backups"][0]["verification_timestamp"]
    assert out["recent_backups"][0]["evidence_mode"] == "LIVE_CALCULATED"
    assert out["ok"] is True


def test_track_27_09_integrity_check_suppresses_cross_environment_false_fail(monkeypatch, server_module):
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
                "app_env": "production",
                "db_name": "masci_safety",
            },
        }

    monkeypatch.setattr(backup_verification, "list_r2_backup_archives", _fake_list_r2_backup_archives)
    monkeypatch.setattr(backup_verification, "read_r2_backup_manifest", _fake_read_r2_backup_manifest)
    monkeypatch.setattr(server_module, "_list_stored_backups", lambda: [])
    old_env = server_module.os.environ.get("APP_ENV")
    old_db = server_module.os.environ.get("DB_NAME")
    server_module.os.environ["APP_ENV"] = "preview"
    server_module.os.environ["DB_NAME"] = "masci_safety_preview"

    fake_db = _FakeDB()

    async def _call_route():
        fn = None
        for route in server_module.app.routes:
            if getattr(route, "path", "") == "/api/admin/backups/integrity-check":
                fn = route.endpoint
                break
        assert fn is not None
        old_runtime_db = server_module.db
        server_module.db = fake_db
        try:
            return await fn(True)
        finally:
            server_module.db = old_runtime_db

    try:
        out = asyncio.run(_call_route())
    finally:
        if old_env is None:
            server_module.os.environ.pop("APP_ENV", None)
        else:
            server_module.os.environ["APP_ENV"] = old_env
        if old_db is None:
            server_module.os.environ.pop("DB_NAME", None)
        else:
            server_module.os.environ["DB_NAME"] = old_db

    assert out["integrity_result"] == "UNKNOWN"
    assert out["classification_reason_code"] == "environment_mismatch_manifest_vs_runtime"
    assert out["missing_from_backup"] == []
    assert out["ok"] is False


def test_track_27_09_integrity_check_prefers_latest_matching_runtime_manifest(monkeypatch, server_module):
    import backup_verification  # noqa: PLC0415

    async def _fake_list_r2_backup_archives(prefix: str = "backups/"):
        return [
            {
                "key": "backups/auto-90d/MASCI_complete_backup_2026-07-22_155504Z.zip",
                "filename": "MASCI_complete_backup_2026-07-22_155504Z.zip",
                "size_bytes": 1596157914,
                "last_modified_iso": "2026-07-22T16:04:14.577250+00:00",
            },
            {
                "key": "backups/auto-90d/MASCI_complete_backup_2026-07-22_154935Z.zip",
                "filename": "MASCI_complete_backup_2026-07-22_154935Z.zip",
                "size_bytes": 1184300000,
                "last_modified_iso": "2026-07-22T15:54:50.333000+00:00",
            },
        ]

    async def _fake_read_r2_backup_manifest(key: str):
        if key.endswith("155504Z.zip"):
            return {
                "manifest_name": "MANIFEST.json",
                "content_length": 1596157914,
                "manifest": {
                    "generated_at": "2026-07-22T16:03:52.212049+00:00",
                    "app_env": "preview",
                    "db_name": "masci_safety_preview",
                    "captured_collections": ["backup_health", "daily_reports", "meetings", "notification_capture_v1"],
                    "per_kind": {"backup_health": 20, "daily_reports": 215, "meetings": 56, "notification_capture_v1": 10},
                    "total_records": 301,
                },
            }
        return {
            "manifest_name": "MANIFEST.json",
            "content_length": 1184300000,
            "manifest": {
                "generated_at": "2026-07-22T15:54:22.036148+00:00",
                "app_env": "production",
                "db_name": "masci_safety",
                "captured_collections": ["backup_health", "daily_reports", "meetings"],
                "per_kind": {"backup_health": 20, "daily_reports": 215, "meetings": 56},
                "total_records": 291,
            },
        }

    monkeypatch.setattr(backup_verification, "list_r2_backup_archives", _fake_list_r2_backup_archives)
    monkeypatch.setattr(backup_verification, "read_r2_backup_manifest", _fake_read_r2_backup_manifest)
    monkeypatch.setattr(server_module, "_list_stored_backups", lambda: [])

    old_env = server_module.os.environ.get("APP_ENV")
    old_db_name = server_module.os.environ.get("DB_NAME")
    server_module.os.environ["APP_ENV"] = "preview"
    server_module.os.environ["DB_NAME"] = "masci_safety_preview"

    class _RuntimeMatchingDB(_FakeDB):
        async def list_collection_names(self):
            return ["backup_health", "daily_reports", "meetings", "notification_capture_v1"]

    fake_db = _RuntimeMatchingDB()

    async def _call_route():
        fn = None
        for route in server_module.app.routes:
            if getattr(route, "path", "") == "/api/admin/backups/integrity-check":
                fn = route.endpoint
                break
        assert fn is not None
        old_runtime_db = server_module.db
        server_module.db = fake_db
        try:
            return await fn(True)
        finally:
            server_module.db = old_runtime_db

    try:
        out = asyncio.run(_call_route())
    finally:
        if old_env is None:
            server_module.os.environ.pop("APP_ENV", None)
        else:
            server_module.os.environ["APP_ENV"] = old_env
        if old_db_name is None:
            server_module.os.environ.pop("DB_NAME", None)
        else:
            server_module.os.environ["DB_NAME"] = old_db_name

    assert out["last_backup_filename"] == "MASCI_complete_backup_2026-07-22_155504Z.zip"
    assert out["classification"] == "PASS"
    assert out["classification_reason_code"] == "verification_pass"
    assert out["missing_from_backup"] == []
    assert out["ok"] is True
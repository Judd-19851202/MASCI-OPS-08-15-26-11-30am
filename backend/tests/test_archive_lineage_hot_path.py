#!/usr/bin/env python3
import asyncio
from pathlib import Path

import pytest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import lib.archive_lineage as archive_lineage
import backup_verification


class _FakeSyncCursor:
    def __init__(self, rows):
        self._rows = list(rows)

    def limit(self, value):
        return _FakeSyncCursor(self._rows[:value])

    def __iter__(self):
        return iter(self._rows)


class _FakeCollection:
    def __init__(self, rows):
        self._rows = list(rows)

    def find(self, *args, **kwargs):
        return _FakeSyncCursor(self._rows)

    async def find_one(self, *args, **kwargs):
        return self._rows[0] if self._rows else None


class _FakeDb:
    def __init__(self, *, backup_jobs_rows, backup_health_rows):
        self.backup_jobs = _FakeCollection(backup_jobs_rows)
        self.backup_health = _FakeCollection(backup_health_rows)


def _lineage_row(key="backups/auto-90d/MASCI_complete_backup_2026-07-25_230328Z.zip"):
    return {
        "created_at": "2026-07-25T23:03:28.376802+00:00",
        "archive_lineage": {
            "job_id": "bjob-stage1-hot-path",
            "trigger": "scheduler_nightly",
            "environment": "preview",
            "database_name": "masci_safety_preview",
            "archive_key": key,
            "archive_size_bytes": 1914305588,
            "checksum_sha256": "49408342d2d98d05b5b1fee5c1c46f8bc2d98d9f7593eb7056a2cd6c40fb8d08",
            "created_at": "2026-07-25T23:03:28.664014+00:00",
            "uploaded_at": "2026-07-25T23:12:59.720145+00:00",
            "verification_status": "uploaded",
            "manifest_identity": {
                "manifest_name": "MANIFEST.json",
                "manifest_schema": "27.11c-1",
            },
        },
    }


def _backup_health_row(filename="MASCI_complete_backup_2026-07-25_230328Z.zip"):
    return {
        "ts": "2026-07-25T23:12:59.720145+00:00",
        "ok": True,
        "mode": "complete-r2",
        "filename": filename,
        "size_bytes": 1914305588,
        "records": 3428,
        "error": "",
        "archive_identifier": filename,
        "audit_reference": "test-audit-ref",
    }


@pytest.fixture(autouse=True)
def _clear_cache():
    archive_lineage._CACHE.clear()
    yield
    archive_lineage._CACHE.clear()


def test_hot_path_lineage_performs_zero_manifest_reads(monkeypatch):
    counters = {"list_calls": 0, "manifest_reads": 0}

    async def _list_archives(*args, **kwargs):
        counters["list_calls"] += 1
        return []

    async def _read_manifest(*args, **kwargs):
        counters["manifest_reads"] += 1
        return None

    async def _forbidden_gather(*args, **kwargs):  # pragma: no cover - should never be reached
        raise AssertionError("hot-path lineage must not fan out manifest probes")

    monkeypatch.setattr(backup_verification, "list_r2_backup_archives", _list_archives)
    monkeypatch.setattr(backup_verification, "read_r2_backup_manifest", _read_manifest)
    monkeypatch.setattr(archive_lineage.asyncio, "gather", _forbidden_gather)

    db = _FakeDb(backup_jobs_rows=[_lineage_row()], backup_health_rows=[_backup_health_row()])
    lineage = asyncio.run(
        archive_lineage.build_canonical_archive_lineage(
            db,
            current_env="preview",
            current_db="masci_safety_preview",
            requested_source_environment="preview",
            force_refresh=True,
            include_manifest_reads=False,
        )
    )

    assert counters == {"list_calls": 0, "manifest_reads": 0}
    assert lineage["manifest_probe_mode"] == "HOT_PATH"
    assert lineage["manifest_reads_attempted"] == 0
    assert lineage["manifest_reads_skipped"] == 1
    assert lineage["manifest_skip_reason"] == "HOT_PATH_BOUNDED_EVALUATION"
    assert lineage["authoritative_artifact"]["object_key"] == _lineage_row()["archive_lineage"]["archive_key"]
    assert lineage["authoritative_artifact"]["valid_recoverable"] is True


def test_hot_path_preserves_environment_rejection(monkeypatch):
    async def _unexpected(*args, **kwargs):  # pragma: no cover - should never be reached
        raise AssertionError("mismatch path must fail closed before any probes")

    monkeypatch.setattr(backup_verification, "list_r2_backup_archives", _unexpected)
    monkeypatch.setattr(backup_verification, "read_r2_backup_manifest", _unexpected)

    db = _FakeDb(backup_jobs_rows=[_lineage_row()], backup_health_rows=[_backup_health_row()])
    lineage = asyncio.run(
        archive_lineage.build_canonical_archive_lineage(
            db,
            current_env="preview",
            current_db="masci_safety_preview",
            requested_source_environment="production",
            force_refresh=True,
            include_manifest_reads=False,
        )
    )

    assert lineage["authoritative_artifact"] is None
    assert "no_valid_archive_for_requested_environment" in (lineage["degradation_reasons"] or [])
    assert lineage["manifest_probe_mode"] == "HOT_PATH"


def test_default_full_mode_retains_manifest_behavior(monkeypatch):
    counters = {"list_calls": 0, "manifest_reads": 0}

    async def _list_archives(*args, **kwargs):
        counters["list_calls"] += 1
        return [
            {
                "key": "backups/auto-90d/MASCI_complete_backup_2026-07-25_230328Z.zip",
                "filename": "MASCI_complete_backup_2026-07-25_230328Z.zip",
                "size_bytes": 1914305588,
                "last_modified_iso": "2026-07-25T23:12:59.720145+00:00",
                "etag": "etag-1",
            }
        ]

    async def _read_manifest(key, *args, **kwargs):
        counters["manifest_reads"] += 1
        return {
            "key": key,
            "manifest_name": "MANIFEST.json",
            "manifest": {
                "app_env": "preview",
                "db_name": "masci_safety_preview",
                "integrity_result": "PASS",
                "coverage_complete": True,
                "classification": "COMPLETE",
                "logical_recovery_point_time": "2026-07-25T23:03:28.664014+00:00",
                "backup_completed_at": "2026-07-25T23:12:59.720145+00:00",
            },
            "content_length": 1914305588,
            "last_modified_iso": "2026-07-25T23:12:59.720145+00:00",
            "checksum_sha256": "checksum-1",
        }

    monkeypatch.setattr(backup_verification, "list_r2_backup_archives", _list_archives)
    monkeypatch.setattr(backup_verification, "read_r2_backup_manifest", _read_manifest)

    db = _FakeDb(backup_jobs_rows=[_lineage_row()], backup_health_rows=[_backup_health_row()])
    lineage = asyncio.run(
        archive_lineage.build_canonical_archive_lineage(
            db,
            current_env="preview",
            current_db="masci_safety_preview",
            requested_source_environment="preview",
            force_refresh=True,
        )
    )

    assert counters == {"list_calls": 1, "manifest_reads": 1}
    assert lineage["manifest_probe_mode"] == "FULL"
    assert lineage["manifest_reads_attempted"] == 1
    assert lineage["manifest_reads_skipped"] == 0
    assert lineage["manifest_skip_reason"] is None
    assert lineage["authoritative_artifact"]["object_key"] == "backups/auto-90d/MASCI_complete_backup_2026-07-25_230328Z.zip"


def test_hot_path_authoritative_artifact_preserves_persisted_lineage_row(monkeypatch):
    async def _list_archives(*args, **kwargs):
        return []

    async def _read_manifest(*args, **kwargs):  # pragma: no cover - hot path should not call this
        raise AssertionError("hot-path lineage must not read manifests")

    monkeypatch.setattr(backup_verification, "list_r2_backup_archives", _list_archives)
    monkeypatch.setattr(backup_verification, "read_r2_backup_manifest", _read_manifest)

    source_row = _lineage_row()
    source_row["archive_lineage"]["backup_id"] = "b4bde3a6eea34d0aa3f4e6fffcfde1ed"
    db = _FakeDb(backup_jobs_rows=[source_row], backup_health_rows=[_backup_health_row()])
    lineage = asyncio.run(
        archive_lineage.build_canonical_archive_lineage(
            db,
            current_env="preview",
            current_db="masci_safety_preview",
            requested_source_environment="preview",
            force_refresh=True,
            include_manifest_reads=False,
        )
    )

    authoritative = lineage["authoritative_artifact"]
    assert authoritative["persisted_lineage_row"]["archive_lineage"]["backup_id"] == "b4bde3a6eea34d0aa3f4e6fffcfde1ed"
    assert authoritative["artifact_identity"]["artifact_id"] == "b4bde3a6eea34d0aa3f4e6fffcfde1ed"
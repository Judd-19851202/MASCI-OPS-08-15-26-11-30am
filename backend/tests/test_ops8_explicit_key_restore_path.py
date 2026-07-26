from __future__ import annotations

import hashlib
import json
import os
import runpy
import sys
import tempfile
import zipfile
from pathlib import Path

import pytest


SCRIPT_PATH = "/app/scripts/ops8_namespace_restore_drill.py"


class _InsertOneResult:
    inserted_id = "inserted"


class _Collection:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.inserted = []
        self.updates = []
        self.dropped = False

    def find_one(self, query=None, projection=None, sort=None):
        for row in reversed(self.rows):
            if _matches(row, query or {}):
                return _project(row, projection)
        return None

    def update_one(self, query, update, upsert=False):
        self.updates.append({"query": query, "update": update, "upsert": upsert})
        for idx, row in enumerate(self.rows):
            if _matches(row, query):
                self.rows[idx] = _apply_update(row, update)
                return _InsertOneResult()
        if upsert:
            base = dict(query)
            self.rows.append(_apply_update(base, update))
        return _InsertOneResult()

    def insert_one(self, doc):
        self.rows.append(dict(doc))
        self.inserted.append(dict(doc))
        return _InsertOneResult()

    def drop(self):
        self.dropped = True
        self.rows.clear()

    def insert_many(self, docs, ordered=False):
        self.rows.extend(dict(doc) for doc in docs)
        return _InsertOneResult()


class _FakeDB:
    def __init__(self):
        self.backup_jobs = _Collection([])
        self.backup_health = _Collection([])
        self.drill_runs = _Collection([])
        self.collections = {
            "backup_jobs": self.backup_jobs,
            "backup_health": self.backup_health,
            "drill_runs": self.drill_runs,
        }

    def __getitem__(self, name):
        return self.collections.setdefault(name, _Collection([]))

    def list_collection_names(self):
        return list(self.collections.keys())


class _FakeMongoClient:
    def __init__(self, *args, **kwargs):
        self.db = _FakeDB()

    def __getitem__(self, name):
        return self.db

    def close(self):
        return None


class _FakeS3Client:
    def __init__(self, archive_path: Path):
        self.archive_path = archive_path
        self.downloads = []

    def download_file(self, bucket, key, dest):
        self.downloads.append({"bucket": bucket, "key": key, "dest": dest})
        Path(dest).write_bytes(self.archive_path.read_bytes())

    def head_object(self, Bucket, Key):
        return {"ContentLength": self.archive_path.stat().st_size}

    def put_object(self, Bucket, Key, Body):
        return {"ok": True}


def _matches(row, query):
    if not query:
        return True
    for key, expected in query.items():
        if isinstance(expected, dict) and "$in" in expected:
            if row.get(key) not in expected["$in"]:
                return False
            continue
        if row.get(key) != expected:
            return False
    return True


def _project(row, projection):
    if not projection:
        return dict(row)
    out = {}
    include = {k for k, v in projection.items() if v}
    if include:
        for key in include:
            if key in row:
                out[key] = row[key]
        return out
    out = dict(row)
    for key, value in projection.items():
        if value == 0:
            out.pop(key, None)
    return out


def _apply_update(row, update):
    new = dict(row)
    for op, payload in (update or {}).items():
        if op == "$set":
            new.update(payload)
    return new


def _write_archive(tmp_path: Path, manifest: dict):
    archive = tmp_path / "MASCI_complete_backup_2026-07-25_230328Z.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("MANIFEST.json", json.dumps(manifest))
        zf.writestr("collections/daily_reports.json", json.dumps([{"id": "dr-1", "photo": "photo://bucket/photos/2026/07/a.jpg"}]))
        zf.writestr("photos/photos/2026/07/a.jpg", b"fake-photo")
    return archive


def _base_manifest():
    return {
        "backup_id": "MASCI_complete_backup_2026-07-25_230328Z.zip",
        "manifest_version": "27.11c-1",
        "environment": "preview",
        "app_env": "preview",
        "database_name": "masci_safety_preview",
        "db_name": "masci_safety_preview",
        "environment_fingerprint": "f9b3d961882e",
        "source_cluster_fingerprint": "e92d0e9987fa",
        "backup_bucket": "masci-hub",
        "backup_prefix": "backups/auto-90d/",
        "archive_key": "backups/auto-90d/MASCI_complete_backup_2026-07-25_230328Z.zip",
        "release_identity": "4af01c4c3f4e06065a8e9c0b9a60f86a",
        "total_records": 1,
        "per_kind": {"daily_reports": 1},
    }


def _authoritative_artifact():
    return {
        "object_key": "backups/auto-90d/MASCI_complete_backup_2026-07-25_230328Z.zip",
        "artifact_identity": {
            "artifact_id": "MASCI_complete_backup_2026-07-25_230328Z.zip",
            "originating_environment": "preview",
            "database_name": "masci_safety_preview",
        },
        "lineage_identity": {
            "environment": "preview",
            "environment_fingerprint": "f9b3d961882e",
            "source_cluster_fingerprint": "e92d0e9987fa",
            "source_database": "masci_safety_preview",
            "backup_bucket": "masci-hub",
            "backup_prefix": "backups/auto-90d/",
            "archive_key": "backups/auto-90d/MASCI_complete_backup_2026-07-25_230328Z.zip",
        },
        "evidence_references": {
            "checksum_sha256": None,
        },
        "manifest_identity": {
            "manifest_name": None,
            "manifest_version": None,
        },
        "source_truth": "4af01c4c3f4e06065a8e9c0b9a60f86a",
    }


def _lineage_payload():
    return {
        "manifest_probe_mode": "HOT_PATH",
        "manifest_reads_attempted": 0,
        "manifest_reads_skipped": 2,
        "manifest_skip_reason": "HOT_PATH_BOUNDED_EVALUATION",
        "runtime_identity": {
            "app_env": "preview",
            "db_name": "masci_safety_preview",
            "environment_fingerprint": "f9b3d961882e",
            "cluster_fingerprint": "e92d0e9987fa",
            "backup_bucket": "masci-hub",
            "backup_prefix": "backups/auto-90d/",
        },
        "authoritative_artifact": _authoritative_artifact(),
    }


def _run_script(monkeypatch, tmp_path: Path, *, manifest=None, lineage=None, backup_key=None, restore_should_raise=False):
    manifest = manifest or _base_manifest()
    archive = _write_archive(tmp_path, manifest)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    lineage = lineage or _lineage_payload()
    lineage["authoritative_artifact"] = dict(lineage.get("authoritative_artifact") or {})
    refs = dict((lineage["authoritative_artifact"].get("evidence_references") or {}))
    refs.setdefault("checksum_sha256", checksum)
    lineage["authoritative_artifact"]["evidence_references"] = refs
    fake_mongo = _FakeMongoClient()
    fake_s3 = _FakeS3Client(archive)
    build_calls = []
    manifest_remote_reads = {"count": 0}
    restore_calls = {"count": 0}

    def _fake_build_canonical_archive_lineage(*args, **kwargs):
        build_calls.append(kwargs)
        return lineage

    async def _fake_build_async(*args, **kwargs):
        return _fake_build_canonical_archive_lineage(*args, **kwargs)

    def _fake_boto3_client(*args, **kwargs):
        return fake_s3

    def _fake_read_r2_backup_manifest(*args, **kwargs):
        manifest_remote_reads["count"] += 1
        raise AssertionError("remote manifest reads must not be reached in explicit-key authority resolution")

    def _fake_restore_prefixed(zf, db, prefix):
        restore_calls["count"] += 1
        if restore_should_raise:
            raise RuntimeError("STOP_AFTER_AUTHORITY")
        return {"daily_reports": {"inserted": 1, "files_seen": 1, "skipped_bad": 0}}

    monkeypatch.setenv("MONGO_URL", "mongodb://test")
    monkeypatch.setenv("DB_NAME", "masci_safety_preview")
    monkeypatch.setenv("APP_ENV", "preview")
    monkeypatch.setenv("S3_ENDPOINT_URL", "https://r2.example")
    monkeypatch.setenv("S3_BUCKET", "masci-hub")
    monkeypatch.setenv("S3_ACCESS_KEY", "access")
    monkeypatch.setenv("S3_SECRET_KEY", "secret")
    monkeypatch.setattr("pymongo.MongoClient", lambda *a, **k: fake_mongo)
    monkeypatch.setattr("boto3.client", _fake_boto3_client)
    monkeypatch.setattr("backup_verification.read_r2_backup_manifest", _fake_read_r2_backup_manifest)

    module_globals = runpy.run_path(SCRIPT_PATH, run_name="ops8_test_module")
    main_fn = module_globals["main"]
    main_globals = main_fn.__globals__
    monkeypatch.setitem(main_globals, "MongoClient", lambda *a, **k: fake_mongo)
    monkeypatch.setitem(main_globals, "boto3", type("_Boto", (), {"client": staticmethod(_fake_boto3_client)}))
    monkeypatch.setitem(main_globals, "build_canonical_archive_lineage", lambda *a, **k: _fake_build_async(*a, **k))
    monkeypatch.setitem(main_globals, "_restore_prefixed", _fake_restore_prefixed)
    monkeypatch.setitem(main_globals, "_rehydrate_photos", lambda zf, env, drill_id: {"uploaded": 0, "skipped": 0, "failed": 0})
    monkeypatch.setitem(main_globals, "_write_report", lambda drill_id, summary: tmp_path / f"report-{drill_id}.md")

    old_argv = sys.argv[:]
    sys.argv = [
        "ops8_namespace_restore_drill.py",
        "--backup",
        backup_key or "backups/auto-90d/MASCI_complete_backup_2026-07-25_230328Z.zip",
        "--execute",
        "--backup-ack",
        "--confirm",
        "RUN_ISOLATED_RECOVERY_DRILL",
    ]
    try:
        rc = main_fn()
    except RuntimeError as exc:
        rc = str(exc)
    finally:
        sys.argv = old_argv

    return {
        "rc": rc,
        "db": fake_mongo.db,
        "build_calls": build_calls,
        "remote_manifest_reads": manifest_remote_reads["count"],
        "restore_calls": restore_calls["count"],
        "downloads": fake_s3.downloads,
    }


def test_explicit_key_calls_canonical_lineage_with_manifest_reads_disabled(monkeypatch, tmp_path):
    out = _run_script(monkeypatch, tmp_path)
    assert out["build_calls"], "expected lineage builder to be called"
    call = out["build_calls"][0]
    assert call["include_manifest_reads"] is False
    assert call["requested_source_environment"] == "preview"
    assert out["remote_manifest_reads"] == 0


def test_authorized_archive_key_must_exactly_match_persisted_authority(monkeypatch, tmp_path):
    out = _run_script(
        monkeypatch,
        tmp_path,
        backup_key="backups/auto-90d/MASCI_complete_backup_2026-07-24_230316Z.zip",
    )
    assert out["rc"] == 2
    guard = out["db"].backup_jobs.rows[-1]
    assert guard["failure_reason"] == "AUTHORIZED_ARCHIVE_KEY_MISMATCH"
    assert out["remote_manifest_reads"] == 0
    assert out["restore_calls"] == 0


def test_production_lineage_fails_closed(monkeypatch, tmp_path):
    lineage = _lineage_payload()
    lineage["authoritative_artifact"]["artifact_identity"]["originating_environment"] = "production"
    out = _run_script(monkeypatch, tmp_path, lineage=lineage)
    assert out["rc"] == 2
    guard = out["db"].backup_jobs.rows[-1]
    assert guard["failure_reason"] == "SOURCE_ENVIRONMENT_UNAUTHORIZED"
    assert out["restore_calls"] == 0


def test_database_mismatch_fails_closed(monkeypatch, tmp_path):
    lineage = _lineage_payload()
    lineage["authoritative_artifact"]["artifact_identity"]["database_name"] = "masci_safety"
    out = _run_script(monkeypatch, tmp_path, lineage=lineage)
    assert out["rc"] == 2
    guard = out["db"].backup_jobs.rows[-1]
    assert guard["failure_reason"] == "SOURCE_DATABASE_UNAUTHORIZED"
    assert out["restore_calls"] == 0


def test_bucket_mismatch_fails_closed(monkeypatch, tmp_path):
    lineage = _lineage_payload()
    lineage["authoritative_artifact"]["lineage_identity"]["backup_bucket"] = "other-bucket"
    out = _run_script(monkeypatch, tmp_path, lineage=lineage)
    assert out["rc"] == 2
    guard = out["db"].backup_jobs.rows[-1]
    assert guard["failure_reason"] == "BACKUP_BUCKET_UNAUTHORIZED"
    assert out["restore_calls"] == 0


def test_prefix_mismatch_fails_closed(monkeypatch, tmp_path):
    lineage = _lineage_payload()
    lineage["authoritative_artifact"]["lineage_identity"]["backup_prefix"] = "backups/other/"
    out = _run_script(monkeypatch, tmp_path, lineage=lineage)
    assert out["rc"] == 2
    guard = out["db"].backup_jobs.rows[-1]
    assert guard["failure_reason"] == "BACKUP_PREFIX_UNAUTHORIZED"
    assert out["restore_calls"] == 0


def test_embedded_manifest_environment_mismatch_fails_before_namespace_write(monkeypatch, tmp_path):
    manifest = _base_manifest()
    manifest["environment"] = manifest["app_env"] = "production"
    out = _run_script(monkeypatch, tmp_path, manifest=manifest)
    assert out["rc"] == "EMBEDDED_MANIFEST_ENVIRONMENT_MISMATCH"
    assert out["restore_calls"] == 0


def test_embedded_manifest_database_mismatch_fails_before_namespace_write(monkeypatch, tmp_path):
    manifest = _base_manifest()
    manifest["database_name"] = manifest["db_name"] = "masci_safety"
    out = _run_script(monkeypatch, tmp_path, manifest=manifest)
    assert out["rc"] == "EMBEDDED_MANIFEST_DATABASE_MISMATCH"
    assert out["restore_calls"] == 0


def test_embedded_manifest_archive_identity_mismatch_fails_before_namespace_write(monkeypatch, tmp_path):
    manifest = _base_manifest()
    manifest["archive_key"] = "backups/auto-90d/OTHER.zip"
    out = _run_script(monkeypatch, tmp_path, manifest=manifest)
    assert out["rc"] == "EMBEDDED_MANIFEST_ARCHIVE_KEY_MISMATCH"
    assert out["restore_calls"] == 0


def test_checksum_mismatch_fails_before_namespace_write(monkeypatch, tmp_path):
    lineage = _lineage_payload()
    lineage["authoritative_artifact"]["evidence_references"] = {"checksum_sha256": "deadbeef"}
    out = _run_script(monkeypatch, tmp_path, lineage=lineage)
    assert out["rc"] == "ARCHIVE_CHECKSUM_MISMATCH"
    assert out["restore_calls"] == 0


def test_valid_persisted_authority_and_embedded_manifest_can_advance_to_restore(monkeypatch, tmp_path):
    out = _run_script(monkeypatch, tmp_path, restore_should_raise=True)
    assert out["rc"] == "STOP_AFTER_AUTHORITY"
    assert out["restore_calls"] == 1
    assert out["remote_manifest_reads"] == 0
    drill = out["db"].drill_runs.rows[0]
    assert drill["lineage_resolution_mode"] == "EXPLICIT_KEY_PERSISTED_AUTHORITY"
    assert drill["remote_manifest_fanout_enabled"] is False
    assert drill["remote_manifest_reads_attempted"] == 0
    assert drill["embedded_manifest_loaded"] is True

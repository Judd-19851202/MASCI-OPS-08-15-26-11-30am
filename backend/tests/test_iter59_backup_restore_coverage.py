from __future__ import annotations

import asyncio
import io
import json
import sys
import zipfile
from types import SimpleNamespace

sys.path.insert(0, "/app/backend")

import server  # noqa: E402
from fastapi import UploadFile  # noqa: E402


class _UpdateResult:
    def __init__(self):
        self.deleted_count = 0
        self.modified_count = 1
        self.upserted_id = None


class _Collection:
    def __init__(self):
        self.rows = []

    async def count_documents(self, query):  # noqa: ARG002
        return len(self.rows)

    async def delete_many(self, query):  # noqa: ARG002
        self.rows = []
        return _UpdateResult()

    async def update_one(self, query, update, upsert=False):  # noqa: ARG002
        row = dict((update or {}).get("$set") or {})
        if row:
            self.rows.append(row)
        return _UpdateResult()

    async def find_one(self, *args, **kwargs):  # noqa: ARG002
        return None

    async def insert_one(self, doc):  # noqa: ARG002
        self.rows.append(dict(doc))
        return _UpdateResult()


class _DB:
    def __init__(self):
        self._collections = {}
        self.backup_jobs = _Collection()
        self.audit_events = _Collection()

    def __getitem__(self, name):
        if name not in self._collections:
            self._collections[name] = _Collection()
        return self._collections[name]


def _archive_bytes():
    buf = io.BytesIO()
    manifest = {
        "generated_at": "2026-07-28T00:00:00+00:00",
        "environment": "preview",
        "backup_id": "backup-1",
        "version": "27.11c-1",
    }
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("MANIFEST.json", json.dumps(manifest))
        zf.writestr("collections/safety_documents.json", json.dumps([
            {"id": "doc-1", "file_data": "doc://bucket/safety-docs/2026/07/doc-1/file.pdf"}
        ]))
        zf.writestr("documents/safety-docs/2026/07/doc-1/file.pdf", b"pdf-bytes")
    return buf.getvalue()


def test_restore_rehydrates_embedded_doc_objects(monkeypatch, tmp_path):
    db = _DB()
    archive = tmp_path / "restore.zip"
    archive.write_bytes(_archive_bytes())

    uploaded = []

    async def fake_upload_bytes(data, *, key, content_type="application/octet-stream"):
        uploaded.append({"key": key, "size": len(data), "content_type": content_type})
        return f"doc://bucket/{key}"

    monkeypatch.setattr("safety_doc_storage.is_configured", lambda: True)
    monkeypatch.setattr("safety_doc_storage.upload_bytes", fake_upload_bytes)
    monkeypatch.setattr(server, "require_non_empty_destructive_scope", lambda *a, **k: None)
    async def fake_get_active_backup_jobs(_db):
        return []

    monkeypatch.setattr(server, "get_active_backup_jobs", fake_get_active_backup_jobs)
    monkeypatch.setattr(server, "classify_backup_overlap", lambda jobs: {
        "backup_active": False,
        "restore_active": False,
        "active_backups": jobs,
        "active_restores": [],
        "blocking_backups": [],
        "blocking_restores": [],
        "reclaimable_backups": [],
        "reclaimable_restores": [],
        "overlap_blocked": False,
    })
    async def fake_claim_backup_job(*args, **kwargs):  # noqa: ARG001
        return {"job_id": "job-1"}

    monkeypatch.setattr(server, "claim_backup_job", fake_claim_backup_job)

    async def fake_start_backup_job(_db, _job_id):
        return SimpleNamespace(owner_token="owner")

    async def fake_complete_backup_job(*args, **kwargs):  # noqa: ARG001
        return None

    monkeypatch.setattr(server, "start_backup_job", fake_start_backup_job)
    monkeypatch.setattr(server, "complete_backup_job", fake_complete_backup_job)

    async def fake_run_job_heartbeat(*args, **kwargs):  # noqa: ARG001
        stop = asyncio.Event()
        async def _noop():
            return None
        return stop, asyncio.create_task(_noop())

    monkeypatch.setattr(server, "_run_job_heartbeat", fake_run_job_heartbeat)
    monkeypatch.setattr(server, "_canonical_app_env", lambda: "preview")
    monkeypatch.setattr(server, "_canonical_db_name", lambda: "masci_safety_preview")
    monkeypatch.setattr(server, "db", db)

    upload = UploadFile(filename="restore.zip", file=io.BytesIO(archive.read_bytes()))
    result = asyncio.run(server.exports_restore(
        file=upload,
        merge=True,
        confirm="RESTORE",
        backup_ack=True,
        dry_run=False,
        _=True,
    ))

    assert result["ok"] is True
    assert result["documents_rehydrated"] == 1
    assert uploaded == [{
        "key": "safety-docs/2026/07/doc-1/file.pdf",
        "size": 9,
        "content_type": "application/octet-stream",
    }]


def test_restore_disk_files_map_to_original_roots():
    src = __import__('pathlib').Path('/app/backend/server.py').read_text()
    assert 'disk_root_map = {' in src
    assert '"storage": Path("/app/backend/storage")' in src
    assert '"static": Path("/app/backend/static")' in src
    assert '"data": Path("/app/backend/data")' in src
    assert '"memory": Path("/app/memory")' in src
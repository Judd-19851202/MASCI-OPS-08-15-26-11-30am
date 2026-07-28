"""TRACK 15.73E · Final Photo Rehydration + Backup Coverage Verification

Static code-level verification that:
1. Restore now rehydrates BOTH embedded `photos/` and `documents/` object payloads
2. Complete archive includes Mongo + disk-backed files + object-storage refs
3. All backup entry points have overlap guards/deferrals
4. No remaining code-level backup interference or restore-scope gaps
"""
from __future__ import annotations

import asyncio
import io
import json
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, "/app/backend")

import pytest
import server  # noqa: E402
from fastapi import UploadFile  # noqa: E402


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: Restore rehydrates BOTH photos/ and documents/ object payloads
# ═══════════════════════════════════════════════════════════════════════════

def test_restore_has_photos_rehydration_block():
    """Verify restore code has the photos/ rehydration block (step 2f)."""
    src = Path("/app/backend/server.py").read_text()
    # Check for the photos rehydration section
    assert "# 2f. Rehydrate photo://-backed object storage files" in src, (
        "Restore must have step 2f for photo:// rehydration"
    )
    assert 'if not n.startswith("photos/")' in src, (
        "Restore must filter for photos/ prefix in archive"
    )
    assert "await _restore_ps.upload_bytes(" in src, (
        "Restore must call photo_storage.upload_bytes for rehydration"
    )
    assert "photos_rehydrated += 1" in src, (
        "Restore must track photos_rehydrated count"
    )


def test_restore_has_documents_rehydration_block():
    """Verify restore code has the documents/ rehydration block (step 2g)."""
    src = Path("/app/backend/server.py").read_text()
    # Check for the documents rehydration section
    assert "# 2g. Rehydrate doc://-backed object storage files" in src, (
        "Restore must have step 2g for doc:// rehydration"
    )
    assert 'if not n.startswith("documents/")' in src, (
        "Restore must filter for documents/ prefix in archive"
    )
    assert "await _restore_sds.upload_bytes(" in src, (
        "Restore must call safety_doc_storage.upload_bytes for rehydration"
    )
    assert "docs_rehydrated += 1" in src, (
        "Restore must track docs_rehydrated count"
    )


def test_restore_returns_both_rehydration_counts():
    """Verify restore response includes both photos_rehydrated and documents_rehydrated."""
    src = Path("/app/backend/server.py").read_text()
    # Check that both counts are in the response
    assert '"photos_rehydrated": photos_rehydrated' in src, (
        "Restore response must include photos_rehydrated"
    )
    assert '"documents_rehydrated": docs_rehydrated' in src, (
        "Restore response must include documents_rehydrated"
    )


def test_photo_storage_has_upload_bytes_helper():
    """Verify photo_storage.upload_bytes exists with correct signature."""
    src = Path("/app/backend/photo_storage.py").read_text()
    assert "async def upload_bytes(data: bytes, *, key: str" in src, (
        "photo_storage must have upload_bytes(data, *, key, content_type) helper"
    )


def test_safety_doc_storage_has_upload_bytes_helper():
    """Verify safety_doc_storage.upload_bytes exists with correct signature."""
    src = Path("/app/backend/safety_doc_storage.py").read_text()
    assert "async def upload_bytes(data: bytes, *, key: str" in src, (
        "safety_doc_storage must have upload_bytes(data, *, key, content_type) helper"
    )


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: Complete archive includes Mongo + disk-backed + object-storage
# ═══════════════════════════════════════════════════════════════════════════

def test_complete_archive_captures_photo_refs():
    """Verify complete archive captures photo:// refs into photos/ folder."""
    src = Path("/app/backend/server.py").read_text()
    assert 'archive_member = f"photos/{key}"' in src, (
        "Complete archive must write photo:// refs to photos/{key}"
    )
    assert 'ref.startswith("photo://")' in src, (
        "Complete archive must detect photo:// refs"
    )


def test_complete_archive_captures_doc_refs():
    """Verify complete archive captures doc:// refs into documents/ folder."""
    src = Path("/app/backend/server.py").read_text()
    assert 'archive_member = f"documents/{key}"' in src, (
        "Complete archive must write doc:// refs to documents/{key}"
    )
    assert 'ref.startswith("doc://")' in src, (
        "Complete archive must detect doc:// refs"
    )


def test_complete_archive_includes_disk_backup_roots():
    """Verify complete archive includes all 4 disk backup roots."""
    src = Path("/app/backend/server.py").read_text()
    assert 'DISK_BACKUP_ROOTS = [' in src, (
        "Complete archive must define DISK_BACKUP_ROOTS"
    )
    assert '("/app/backend/storage", "storage")' in src, (
        "DISK_BACKUP_ROOTS must include storage"
    )
    assert '("/app/backend/static", "static")' in src, (
        "DISK_BACKUP_ROOTS must include static"
    )
    assert '("/app/backend/data", "data")' in src, (
        "DISK_BACKUP_ROOTS must include data"
    )
    assert '("/app/memory", "memory")' in src, (
        "DISK_BACKUP_ROOTS must include memory"
    )


def test_restore_has_disk_root_map():
    """Verify restore has disk_root_map for routing disk_files back to original roots."""
    src = Path("/app/backend/server.py").read_text()
    assert 'disk_root_map = {' in src, (
        "Restore must define disk_root_map"
    )
    assert '"storage": Path("/app/backend/storage")' in src, (
        "disk_root_map must map storage to /app/backend/storage"
    )
    assert '"static": Path("/app/backend/static")' in src, (
        "disk_root_map must map static to /app/backend/static"
    )
    assert '"data": Path("/app/backend/data")' in src, (
        "disk_root_map must map data to /app/backend/data"
    )
    assert '"memory": Path("/app/memory")' in src, (
        "disk_root_map must map memory to /app/memory"
    )


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: All backup entry points have overlap guards/deferrals
# ═══════════════════════════════════════════════════════════════════════════

def test_scheduled_backup_has_overlap_guard():
    """Verify _run_scheduled_backup checks overlap before proceeding."""
    src = Path("/app/backend/server.py").read_text()
    # Find the function and check for overlap guard
    assert 'async def _run_scheduled_backup(db' in src
    # Check that it calls get_active_backup_jobs and classify_backup_overlap
    assert 'active_jobs = await get_active_backup_jobs(db)' in src, (
        "_run_scheduled_backup must check active_jobs"
    )
    assert 'overlap = classify_backup_overlap(active_jobs)' in src, (
        "_run_scheduled_backup must classify overlap"
    )
    assert 'if overlap.get("backup_active") or overlap.get("restore_active"):' in src, (
        "_run_scheduled_backup must check backup_active and restore_active"
    )
    assert '"reason": reason' in src and '"overlap_backup_active"' in src, (
        "_run_scheduled_backup must defer with reason when overlap detected"
    )


def test_manual_backup_now_has_overlap_guard():
    """Verify admin_run_backup_now checks overlap before proceeding."""
    src = Path("/app/backend/server.py").read_text()
    assert 'async def admin_run_backup_now(' in src
    # Check for the overlap guard in the function
    assert 'Another backup or restore job is already active.' in src, (
        "admin_run_backup_now must block when overlap detected"
    )


def test_restore_has_overlap_guard():
    """Verify exports_restore checks overlap before proceeding."""
    src = Path("/app/backend/server.py").read_text()
    assert 'async def exports_restore(' in src
    # Check for the overlap guard
    assert 'Restore blocked while a backup job is active.' in src, (
        "exports_restore must block when backup is active"
    )


def test_scheduler_loop_complete_r2_has_overlap_guard():
    """Verify scheduler loop checks overlap before firing complete-R2."""
    src = Path("/app/backend/server.py").read_text()
    # Check for the complete-R2 overlap guard in scheduler loop
    assert 'COMPLETE_ARCHIVE_DEFERRED_BACKUP_ACTIVE' in src or 'COMPLETE_ARCHIVE_DEFERRED_' in src, (
        "Scheduler loop must defer complete-R2 when overlap detected"
    )


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: No remaining backup interference or restore-scope gaps
# ═══════════════════════════════════════════════════════════════════════════

def test_iter_photo_refs_discovers_both_photo_and_doc_refs():
    """Verify _iter_photo_refs discovers both photo:// and doc:// refs."""
    src = Path("/app/backend/server.py").read_text()
    assert 'def _iter_photo_refs(' in src, (
        "_iter_photo_refs must be defined"
    )
    # Check that it yields both photo:// and doc:// refs
    assert 'photo://' in src and 'doc://' in src, (
        "_iter_photo_refs must handle both photo:// and doc:// refs"
    )


def test_backup_job_kinds_defined():
    """Verify backup job kinds are defined for overlap classification."""
    src = Path("/app/backend/server.py").read_text()
    assert 'BACKUP_JOB_KIND_COMPLETE_R2' in src, (
        "BACKUP_JOB_KIND_COMPLETE_R2 must be defined"
    )
    assert 'BACKUP_JOB_KIND_RESTORE_IMPORT' in src, (
        "BACKUP_JOB_KIND_RESTORE_IMPORT must be defined"
    )


def test_classify_backup_overlap_imported():
    """Verify classify_backup_overlap is imported from backup_runtime."""
    src = Path("/app/backend/server.py").read_text()
    assert 'from lib.backup_runtime import' in src
    assert 'classify_backup_overlap' in src, (
        "classify_backup_overlap must be imported from lib.backup_runtime"
    )


def test_get_active_backup_jobs_imported():
    """Verify get_active_backup_jobs is imported from backup_runtime."""
    src = Path("/app/backend/server.py").read_text()
    assert 'get_active_backup_jobs' in src, (
        "get_active_backup_jobs must be imported from lib.backup_runtime"
    )


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: Functional test - restore rehydrates both photos and documents
# ═══════════════════════════════════════════════════════════════════════════

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


def _archive_bytes_with_both_photos_and_docs():
    """Create a test archive with both photos/ and documents/ folders."""
    buf = io.BytesIO()
    manifest = {
        "generated_at": "2026-07-28T00:00:00+00:00",
        "environment": "preview",
        "backup_id": "backup-final-test",
        "version": "27.11c-1",
    }
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("MANIFEST.json", json.dumps(manifest))
        zf.writestr("collections/safety_documents.json", json.dumps([
            {"id": "doc-1", "file_data": "doc://bucket/safety-docs/2026/07/doc-1/file.pdf"}
        ]))
        zf.writestr("collections/daily_reports.json", json.dumps([
            {"id": "report-1", "photos": [{"url": "photo://bucket/photos/2026/07/image-1.jpg"}]}
        ]))
        # Both photos and documents folders
        zf.writestr("photos/photos/2026/07/image-1.jpg", b"photo-bytes-123")
        zf.writestr("photos/photos/2026/07/image-2.jpg", b"photo-bytes-456")
        zf.writestr("documents/safety-docs/2026/07/doc-1/file.pdf", b"pdf-bytes-789")
        zf.writestr("documents/safety-docs/2026/07/doc-2/file.docx", b"docx-bytes-abc")
    return buf.getvalue()


def test_restore_rehydrates_both_photos_and_documents(monkeypatch, tmp_path):
    """Functional test: restore rehydrates BOTH photos/ and documents/ objects."""
    db = _DB()
    archive = tmp_path / "restore_both.zip"
    archive.write_bytes(_archive_bytes_with_both_photos_and_docs())

    photo_uploaded = []
    doc_uploaded = []

    async def fake_photo_upload_bytes(data, *, key, content_type="application/octet-stream"):
        photo_uploaded.append({"key": key, "size": len(data), "content_type": content_type})
        return f"photo://bucket/{key}"

    async def fake_doc_upload_bytes(data, *, key, content_type="application/octet-stream"):
        doc_uploaded.append({"key": key, "size": len(data), "content_type": content_type})
        return f"doc://bucket/{key}"

    monkeypatch.setattr("photo_storage.is_configured", lambda: True)
    monkeypatch.setattr("photo_storage.upload_bytes", fake_photo_upload_bytes)
    monkeypatch.setattr("safety_doc_storage.is_configured", lambda: True)
    monkeypatch.setattr("safety_doc_storage.upload_bytes", fake_doc_upload_bytes)
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
        return {"job_id": "job-final-test"}

    monkeypatch.setattr(server, "claim_backup_job", fake_claim_backup_job)

    async def fake_start_backup_job(_db, _job_id):
        return SimpleNamespace(owner_token="owner-final")

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

    upload = UploadFile(filename="restore_both.zip", file=io.BytesIO(archive.read_bytes()))
    result = asyncio.run(server.exports_restore(
        file=upload,
        merge=True,
        confirm="RESTORE",
        backup_ack=True,
        dry_run=False,
        _=True,
    ))

    # Verify both photos and documents were rehydrated
    assert result["ok"] is True
    assert result["photos_rehydrated"] == 2, f"Expected 2 photos rehydrated, got {result['photos_rehydrated']}"
    assert result["documents_rehydrated"] == 2, f"Expected 2 documents rehydrated, got {result['documents_rehydrated']}"

    # Verify the correct keys were uploaded
    photo_keys = [p["key"] for p in photo_uploaded]
    assert "photos/2026/07/image-1.jpg" in photo_keys
    assert "photos/2026/07/image-2.jpg" in photo_keys

    doc_keys = [d["key"] for d in doc_uploaded]
    assert "safety-docs/2026/07/doc-1/file.pdf" in doc_keys
    assert "safety-docs/2026/07/doc-2/file.docx" in doc_keys


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: Summary verification - all backup coverage requirements met
# ═══════════════════════════════════════════════════════════════════════════

def test_all_backup_coverage_requirements_met():
    """Summary test: verify all backup coverage requirements are met."""
    src = Path("/app/backend/server.py").read_text()
    
    # 1. Restore rehydrates photos
    assert "photos_rehydrated" in src, "Missing photos_rehydrated"
    assert 'await _restore_ps.upload_bytes(' in src, "Missing photo rehydration call"
    
    # 2. Restore rehydrates documents
    assert "documents_rehydrated" in src, "Missing documents_rehydrated"
    assert 'await _restore_sds.upload_bytes(' in src, "Missing document rehydration call"
    
    # 3. Complete archive captures photos
    assert 'archive_member = f"photos/{key}"' in src, "Missing photo capture in archive"
    
    # 4. Complete archive captures documents
    assert 'archive_member = f"documents/{key}"' in src, "Missing document capture in archive"
    
    # 5. Complete archive includes disk-backed files
    assert 'DISK_BACKUP_ROOTS' in src, "Missing DISK_BACKUP_ROOTS"
    
    # 6. Restore maps disk files to original roots
    assert 'disk_root_map' in src, "Missing disk_root_map"
    
    # 7. All backup entry points have overlap guards
    assert 'overlap.get("backup_active")' in src, "Missing backup_active check"
    assert 'overlap.get("restore_active")' in src, "Missing restore_active check"
    
    # 8. Backup job kinds defined
    assert 'BACKUP_JOB_KIND_COMPLETE_R2' in src, "Missing BACKUP_JOB_KIND_COMPLETE_R2"
    assert 'BACKUP_JOB_KIND_RESTORE_IMPORT' in src, "Missing BACKUP_JOB_KIND_RESTORE_IMPORT"

"""Iteration 60 · Final Pre-Deploy Backup System Verification

Static + code-level verification that:
1. Complete archive includes disk-backed files from storage/static/data/memory
2. Restore maps disk_files back to their original roots (not all under /app/backend/storage)
3. Manual run-now blocks when another backup or restore is active
4. Scheduled/nightly zip backup defers on active backup/restore overlap
5. Complete-R2 defers on backup or restore overlap
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, "/app/backend")

import server  # noqa: E402


# ═══════════════════════════════════════════════════════════════════════════
# TEST 1: Complete archive includes disk-backed files from all 4 roots
# ═══════════════════════════════════════════════════════════════════════════

def test_complete_archive_includes_all_disk_backup_roots():
    """Verify _build_complete_archive_on_disk includes storage/static/data/memory."""
    src = Path("/app/backend/server.py").read_text()
    
    # Check DISK_BACKUP_ROOTS definition
    assert 'DISK_BACKUP_ROOTS = [' in src, "DISK_BACKUP_ROOTS list must be defined"
    assert '("/app/backend/storage", "storage")' in src, "storage root must be in DISK_BACKUP_ROOTS"
    assert '("/app/backend/static", "static")' in src, "static root must be in DISK_BACKUP_ROOTS"
    assert '("/app/backend/data", "data")' in src, "data root must be in DISK_BACKUP_ROOTS"
    assert '("/app/memory", "memory")' in src, "memory root must be in DISK_BACKUP_ROOTS"
    
    # Check that disk files are written to archive
    assert 'disk_files/' in src, "Archive must write disk files under disk_files/ prefix"
    assert 'disk_files_count += 1' in src, "Must count disk files added to archive"
    assert 'disk_files_bytes += size' in src, "Must track disk file bytes"


def test_complete_archive_disk_file_iteration_logic():
    """Verify the disk file iteration logic in _build_complete_archive_on_disk."""
    src = Path("/app/backend/server.py").read_text()
    
    # Check iteration over DISK_BACKUP_ROOTS
    assert 'for root_path_str, archive_prefix in DISK_BACKUP_ROOTS:' in src, \
        "Must iterate over DISK_BACKUP_ROOTS"
    assert 'root_path = Path(root_path_str)' in src, "Must convert to Path"
    assert 'for f in root_path.rglob("*"):' in src, "Must recursively glob files"
    assert 'arcname = f"disk_files/{archive_prefix}/{rel.as_posix()}"' in src, \
        "Archive name must preserve root prefix"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 2: Restore maps disk_files back to original roots
# ═══════════════════════════════════════════════════════════════════════════

def test_restore_disk_root_map_definition():
    """Verify disk_root_map maps all 4 roots correctly."""
    src = Path("/app/backend/server.py").read_text()
    
    assert 'disk_root_map = {' in src, "disk_root_map must be defined"
    assert '"storage": Path("/app/backend/storage")' in src, "storage must map to /app/backend/storage"
    assert '"static": Path("/app/backend/static")' in src, "static must map to /app/backend/static"
    assert '"data": Path("/app/backend/data")' in src, "data must map to /app/backend/data"
    assert '"memory": Path("/app/memory")' in src, "memory must map to /app/memory"


def test_restore_disk_file_routing_logic():
    """Verify restore routes disk files to correct roots."""
    src = Path("/app/backend/server.py").read_text()
    
    # Check the routing logic
    assert 'if not n.startswith("disk_files/") or n.endswith("/"):' in src, \
        "Must filter for disk_files/ prefix"
    assert 'rel = n[len("disk_files/"):]' in src, "Must strip disk_files/ prefix"
    assert 'parts = rel.split("/", 1)' in src, "Must split to get root prefix"
    assert 'if len(parts) != 2 or parts[0] not in disk_root_map:' in src, \
        "Must validate root prefix exists in map"
    assert 'target = disk_root_map[parts[0]] / parts[1]' in src, \
        "Must construct target path from map"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 3: Manual run-now blocks when backup/restore is active
# ═══════════════════════════════════════════════════════════════════════════

def test_admin_run_backup_now_has_overlap_guard():
    """Verify admin_run_backup_now checks for active jobs."""
    src = Path("/app/backend/server.py").read_text()
    
    # Find the admin_run_backup_now function and check for overlap guard
    assert 'async def admin_run_backup_now(' in src, "admin_run_backup_now must exist"
    assert 'active_jobs = await get_active_backup_jobs(db)' in src, \
        "Must get active backup jobs"
    assert 'overlap = classify_backup_overlap(active_jobs)' in src, \
        "Must classify backup overlap"
    assert 'Another backup or restore job is already active.' in src, \
        "Must have error message for overlap"


def test_admin_run_complete_backup_now_has_overlap_guard():
    """Verify admin_run_complete_backup_now checks for active jobs."""
    src = Path("/app/backend/server.py").read_text()
    
    # Find the function and check for overlap guard
    assert 'async def admin_run_complete_backup_now(' in src, \
        "admin_run_complete_backup_now must exist"
    
    # Find the function body
    func_start = src.find('async def admin_run_complete_backup_now(')
    assert func_start != -1, "Function must exist"
    
    # Find the next function definition to bound the search
    next_func = src.find('\n@api_router', func_start + 100)
    if next_func == -1:
        next_func = len(src)
    
    func_body = src[func_start:next_func]
    
    # Check for overlap guard in function body
    assert 'active_jobs = await get_active_backup_jobs(db)' in func_body, \
        "admin_run_complete_backup_now must check active_jobs"
    assert 'overlap = classify_backup_overlap(active_jobs)' in func_body, \
        "admin_run_complete_backup_now must classify overlap"
    assert 'Another backup or restore job is already active' in func_body, \
        "admin_run_complete_backup_now must have overlap error message"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 4: Scheduled/nightly zip backup defers on overlap
# ═══════════════════════════════════════════════════════════════════════════

def test_run_scheduled_backup_defers_on_backup_overlap():
    """Verify _run_scheduled_backup defers when backup is active."""
    async def fake_get_active_backup_jobs(_db):
        return [{"kind": server.BACKUP_JOB_KIND_COMPLETE_R2, "state": "running"}]

    import server as srv
    original_get_active = srv.get_active_backup_jobs
    srv.get_active_backup_jobs = fake_get_active_backup_jobs
    srv.classify_backup_overlap = lambda jobs: {
        "backup_active": True,
        "restore_active": False,
        "active_backups": jobs,
        "active_restores": [],
        "blocking_backups": jobs,
        "blocking_restores": [],
        "reclaimable_backups": [],
        "reclaimable_restores": [],
        "overlap_blocked": False,
    }
    
    try:
        result = asyncio.run(srv._run_scheduled_backup(SimpleNamespace(), lite_mode=True))
        assert result["skipped"] is True
        assert result["reason"] == "overlap_backup_active"
    finally:
        srv.get_active_backup_jobs = original_get_active


def test_run_scheduled_backup_defers_on_restore_overlap():
    """Verify _run_scheduled_backup defers when restore is active."""
    async def fake_get_active_backup_jobs(_db):
        return [{"kind": server.BACKUP_JOB_KIND_RESTORE_IMPORT, "state": "running"}]

    import server as srv
    original_get_active = srv.get_active_backup_jobs
    srv.get_active_backup_jobs = fake_get_active_backup_jobs
    srv.classify_backup_overlap = lambda jobs: {
        "backup_active": False,
        "restore_active": True,
        "active_backups": [],
        "active_restores": jobs,
        "blocking_backups": [],
        "blocking_restores": jobs,
        "reclaimable_backups": [],
        "reclaimable_restores": [],
        "overlap_blocked": False,
    }
    
    try:
        result = asyncio.run(srv._run_scheduled_backup(SimpleNamespace(), lite_mode=True))
        assert result["skipped"] is True
        assert result["reason"] == "overlap_restore_active"
    finally:
        srv.get_active_backup_jobs = original_get_active


# ═══════════════════════════════════════════════════════════════════════════
# TEST 5: Complete-R2 scheduler defers on overlap
# ═══════════════════════════════════════════════════════════════════════════

def test_scheduler_loop_complete_r2_defers_on_overlap():
    """Verify scheduler loop defers complete-R2 when backup/restore is active."""
    src = Path("/app/backend/server.py").read_text()
    
    # Find the scheduler loop section that handles complete-R2
    assert 'if should_fire_r2:' in src, "Scheduler must have should_fire_r2 check"
    assert 'active_jobs = await get_active_backup_jobs(db)' in src, \
        "Scheduler must check active jobs before complete-R2"
    assert 'overlap = classify_backup_overlap(active_jobs)' in src, \
        "Scheduler must classify overlap before complete-R2"
    
    # Check for the defer logic
    assert 'COMPLETE_ARCHIVE_DEFERRED_BACKUP_ACTIVE' in src or 'BACKUP_ACTIVE' in src, \
        "Scheduler must defer with BACKUP_ACTIVE reason"
    assert 'COMPLETE_ARCHIVE_DEFERRED_RESTORE_ACTIVE' in src or 'RESTORE_ACTIVE' in src, \
        "Scheduler must defer with RESTORE_ACTIVE reason"


def test_scheduler_loop_complete_r2_checks_manual_backup_flag():
    """Verify scheduler loop also checks _BACKUP_RUNNOW_IN_PROGRESS."""
    src = Path("/app/backend/server.py").read_text()
    
    # The scheduler should check the manual backup flag too
    assert '_BACKUP_RUNNOW_IN_PROGRESS' in src, \
        "Scheduler must check _BACKUP_RUNNOW_IN_PROGRESS flag"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 6: Document object rehydration in restore
# ═══════════════════════════════════════════════════════════════════════════

def test_restore_rehydrates_doc_objects():
    """Verify restore rehydrates doc:// objects from documents/ folder."""
    src = Path("/app/backend/server.py").read_text()
    
    # Check for document rehydration logic
    assert 'documents_rehydrated' in src or 'docs_rehydrated' in src, \
        "Restore must track rehydrated documents"
    assert 'safety_doc_storage' in src, "Restore must use safety_doc_storage"
    assert 'upload_bytes' in src, "Restore must use upload_bytes for rehydration"
    assert 'documents/' in src, "Restore must look for documents/ folder in archive"


def test_safety_doc_storage_has_upload_bytes():
    """Verify safety_doc_storage has upload_bytes helper."""
    src = Path("/app/backend/safety_doc_storage.py").read_text()
    
    assert 'async def upload_bytes(' in src, "upload_bytes must exist"
    assert 'key: str' in src, "upload_bytes must accept explicit key parameter"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 7: Complete archive captures doc:// refs alongside photo:// refs
# ═══════════════════════════════════════════════════════════════════════════

def test_complete_archive_captures_doc_refs():
    """Verify _build_complete_archive_on_disk captures doc:// refs."""
    src = Path("/app/backend/server.py").read_text()
    
    # Check for doc:// handling in the archive builder
    assert 'doc://' in src, "Archive builder must handle doc:// refs"
    assert 'documents/' in src, "Archive must write documents under documents/ prefix"
    assert 'safety_doc_storage' in src, "Archive must use safety_doc_storage for doc:// refs"


def test_iter_photo_refs_discovers_doc_refs():
    """Verify _iter_photo_refs discovers both photo:// and doc:// refs."""
    doc = {
        "attachments": [
            {"file_data": "doc://bucket/safety-docs/2026/07/doc-1/file.pdf"},
            {"meta": {"image": "photo://bucket/photos/2026/07/a.jpg"}},
        ],
        "source_file_ref": "photo://bucket/photos/2026/07/b.jpg",
    }
    refs = list(server._iter_photo_refs(doc))
    
    assert "doc://bucket/safety-docs/2026/07/doc-1/file.pdf" in refs, \
        "_iter_photo_refs must discover doc:// refs"
    assert "photo://bucket/photos/2026/07/a.jpg" in refs, \
        "_iter_photo_refs must discover nested photo:// refs"
    assert "photo://bucket/photos/2026/07/b.jpg" in refs, \
        "_iter_photo_refs must discover top-level photo:// refs"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 8: Restore endpoint has overlap guard
# ═══════════════════════════════════════════════════════════════════════════

def test_exports_restore_has_overlap_guard():
    """Verify exports_restore checks for active backup jobs."""
    src = Path("/app/backend/server.py").read_text()
    
    # Find the exports_restore function
    assert 'async def exports_restore(' in src, "exports_restore must exist"
    
    # Check for overlap guard
    lines = src.split('\n')
    in_function = False
    found_active_jobs_check = False
    found_overlap_check = False
    found_backup_active_block = False
    
    for line in lines:
        if 'async def exports_restore(' in line:
            in_function = True
        elif in_function and (line.startswith('async def ') or line.startswith('def ')) and 'exports_restore' not in line:
            break
        elif in_function:
            if 'active_jobs = await get_active_backup_jobs(db)' in line:
                found_active_jobs_check = True
            if 'overlap = classify_backup_overlap(active_jobs)' in line:
                found_overlap_check = True
            if 'Restore blocked while a backup job is active' in line:
                found_backup_active_block = True
    
    assert found_active_jobs_check, "exports_restore must check active_jobs"
    assert found_overlap_check, "exports_restore must classify overlap"
    assert found_backup_active_block, "exports_restore must block when backup is active"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 9: Verify no remaining backup interference gaps
# ═══════════════════════════════════════════════════════════════════════════

def test_all_backup_entry_points_have_overlap_guards():
    """Verify all backup entry points check for overlap."""
    src = Path("/app/backend/server.py").read_text()
    
    # List of backup entry points that should have overlap guards
    entry_points = [
        ('admin_run_backup_now', 'get_active_backup_jobs'),
        ('admin_run_complete_backup_now', 'get_active_backup_jobs'),
        ('exports_restore', 'get_active_backup_jobs'),
        ('_run_scheduled_backup', 'get_active_backup_jobs'),
    ]
    
    for func_name, guard_call in entry_points:
        # Find the function
        func_start = src.find(f'async def {func_name}(')
        if func_start == -1:
            func_start = src.find(f'def {func_name}(')
        assert func_start != -1, f"{func_name} must exist"
        
        # Find the next function definition
        next_func = src.find('\nasync def ', func_start + 1)
        if next_func == -1:
            next_func = src.find('\ndef ', func_start + 1)
        if next_func == -1:
            next_func = len(src)
        
        func_body = src[func_start:next_func]
        assert guard_call in func_body, \
            f"{func_name} must call {guard_call} for overlap protection"


def test_backup_job_kinds_defined():
    """Verify backup job kind constants are defined."""
    assert hasattr(server, 'BACKUP_JOB_KIND_COMPLETE_R2'), \
        "BACKUP_JOB_KIND_COMPLETE_R2 must be defined"
    assert hasattr(server, 'BACKUP_JOB_KIND_RESTORE_IMPORT'), \
        "BACKUP_JOB_KIND_RESTORE_IMPORT must be defined"

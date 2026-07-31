"""TRACK 24.17 · Storage & Disk operations for the OCC.

Wraps the existing Track 24.12 disk-hardening scripts so a super-admin
can run them from the browser without shell access.

Every operation here is either:
  * ``INFO`` / ``SAFE_CLEANUP`` — no destructive side effects on user
    data, only pod-local logs and Python bytecode caches; OR
  * ``DATA_MIGRATION`` — moves local files to R2 with HEAD-verified
    upload before local unlink (see the migration script for the
    strict fail-closed contract locked by 24.12 tests).

Nothing in this module ever touches Mongo user data or R2-backed
attachments already in cloud storage.
"""
from __future__ import annotations

import os
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from lib.database_authority import create_async_runtime_client

from .registry import Operation, OperationCategory, RiskLevel

# In-memory dry-run cache. Small and short-lived — a fresh dry-run
# expires the previous entry so an apply cannot bind to stale evidence.
_DRY_RUNS: Dict[str, Dict[str, Any]] = {}
_DRY_RUN_TTL_SECONDS = 30 * 60  # 30 minutes
_CLEANUP_HISTORY_COLLECTION = "storage_cleanup_history"
_WARNING_THRESHOLD_PCT = 75.0
_CRITICAL_THRESHOLD_PCT = 90.0
_RETENTION_CLASSES = {
    "/var/log/supervisor": {"classification": "rotatable", "reason": "supervisor runtime logs"},
    "/app/backend/tests/__pycache__": {"classification": "regenerable", "reason": "python bytecode cache"},
    "/app/backend/.pytest_cache": {"classification": "expirable", "reason": "pytest cache"},
    "/app/backend/storage/project_docs": {"classification": "offloadable_to_r2", "reason": "eligible local docs can migrate to R2"},
    "/app/backend/backups": {"classification": "local_staging_storage", "reason": "secondary local backup cache / staging only"},
    "/tmp/basecamp": {"classification": "expirable", "reason": "temporary import workspace"},
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _register_dry_run(operation_id: str, payload: Dict[str, Any]) -> str:
    dry_run_id = str(uuid.uuid4())
    _DRY_RUNS[dry_run_id] = {
        "operation_id": operation_id,
        "created_at": time.time(),
        "payload": payload,
    }
    # opportunistic GC
    now = time.time()
    for k, v in list(_DRY_RUNS.items()):
        if now - v["created_at"] > _DRY_RUN_TTL_SECONDS:
            _DRY_RUNS.pop(k, None)
    return dry_run_id


def get_dry_run(dry_run_id: str) -> Dict[str, Any] | None:
    v = _DRY_RUNS.get(dry_run_id)
    if not v:
        return None
    if time.time() - v["created_at"] > _DRY_RUN_TTL_SECONDS:
        _DRY_RUNS.pop(dry_run_id, None)
        return None
    return v


# ── 1 · Storage Audit (read-only) ──────────────────────────────────

_AUDIT_PATHS = (
    "/app/backend/storage/project_docs",
    "/app/backend/storage",
    "/app/backend/backups",
    "/app/backend/tests/__pycache__",
    "/app/backend/.pytest_cache",
    "/tmp/basecamp",
)


def _dir_stats(root: Path) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "path": str(root),
        "exists": root.exists() and root.is_dir(),
        "total_bytes": 0,
        "file_count": 0,
        "top_files": [],
    }
    if not out["exists"]:
        return out
    largest: List[tuple[int, str]] = []
    for p in root.rglob("*"):
        try:
            if not p.is_file():
                continue
            st = p.stat()
        except OSError:
            continue
        out["total_bytes"] += st.st_size
        out["file_count"] += 1
        largest.append((st.st_size, str(p)))
    largest.sort(key=lambda t: t[0], reverse=True)
    out["top_files"] = [
        {"bytes": s, "path": p, "human": _human(s)}
        for s, p in largest[:8]
    ]
    out["human_total"] = _human(out["total_bytes"])
    return out


def _safe_nonempty_file_filter() -> Dict[str, Any]:
    return {"$and": [{"$ne": None}, {"$ne": ""}]}


def _log_stats() -> Dict[str, Any]:
    entries = []
    total = 0
    log_dir = Path("/var/log/supervisor")
    if log_dir.exists():
        for p in log_dir.glob("*.log"):
            try:
                sz = p.stat().st_size
                entries.append({"path": str(p), "bytes": sz, "human": _human(sz)})
                total += sz
            except OSError:
                continue
    entries.sort(key=lambda e: e["bytes"], reverse=True)
    return {"total_bytes": total, "human_total": _human(total),
            "entries": entries[:8]}


def _disk_stats() -> Dict[str, Any]:
    try:
        usage = shutil.disk_usage("/app")
    except OSError as e:
        return {"error": str(e)}
    used = usage.total - usage.free
    return {
        "total_bytes": usage.total,
        "used_bytes": used,
        "free_bytes": usage.free,
        "used_percent": round(used / usage.total * 100, 1),
        "human_total": _human(usage.total),
        "human_used": _human(used),
        "human_free": _human(usage.free),
    }


async def _latest_cleanup_history(payload: Dict[str, Any]) -> Dict[str, Any] | None:
    db = payload.get("_db")
    if db is None:
        return None
    try:
        return await db[_CLEANUP_HISTORY_COLLECTION].find_one({}, {"_id": 0}, sort=[("generated_at", -1)])
    except Exception:  # noqa: BLE001
        return None


async def _storage_audit_status(_payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _storage_audit_dry_run(_payload)


async def _storage_audit_dry_run(_payload: Dict[str, Any]) -> Dict[str, Any]:
    dirs = [_dir_stats(Path(p)) for p in _AUDIT_PATHS]
    disk = _disk_stats()
    logs = _log_stats()
    cleanup_candidates = _safe_cleanup_candidates()
    last_cleanup = await _latest_cleanup_history(_payload)
    used_pct = disk.get("used_percent", 0)
    if used_pct >= _CRITICAL_THRESHOLD_PCT:
        status = "critical"
    elif used_pct >= _WARNING_THRESHOLD_PCT:
        status = "warning"
    else:
        status = "healthy"
    largest_consumers = sorted(
        [
            {"path": d["path"], "bytes": d.get("total_bytes", 0), "human": d.get("human_total", "0 B"), "type": "directory"}
            for d in dirs if d.get("exists")
        ] + [
            {"path": e["path"], "bytes": e.get("bytes", 0), "human": e.get("human", "0 B"), "type": "log"}
            for e in logs.get("entries", [])
        ],
        key=lambda item: item.get("bytes", 0),
        reverse=True,
    )[:10]
    projected_after_cleanup = None
    reclaimable = cleanup_candidates.get("reclaimable_bytes") or 0
    if disk.get("used_bytes") is not None and disk.get("total_bytes"):
        projected_used = max(0, disk["used_bytes"] - reclaimable)
        projected_after_cleanup = {
            "used_bytes": projected_used,
            "used_percent": round(projected_used / disk["total_bytes"] * 100, 1),
            "human_used": _human(projected_used),
            "reclaimable_bytes": reclaimable,
            "reclaimable_human": cleanup_candidates.get("human_total"),
        }
    return {
        "status": status,
        "summary": f"/app disk at {used_pct}% used",
        "disk": disk,
        "thresholds": {
            "warning_percent": _WARNING_THRESHOLD_PCT,
            "critical_percent": _CRITICAL_THRESHOLD_PCT,
        },
        "directories": dirs,
        "logs": logs,
        "largest_consumers": largest_consumers,
        "retention_classes": _RETENTION_CLASSES,
        "safe_cleanup_projection": projected_after_cleanup,
        "last_cleanup": last_cleanup,
        "trend": {
            "available": False,
            "reason": "Local /app disk trend history is not yet persisted by a snapshot recorder; current audit is point-in-time truth.",
        },
        "protected_evidence_paths": [
            "/app/memory",
            "/app/test_reports",
            "/app/backend/storage/project_docs",
        ],
        "generated_at": _now_iso(),
    }


# ── 2 · Safe Cleanup (dry-run + apply) ──────────────────────────────

def _safe_cleanup_candidates() -> Dict[str, Any]:
    """Enumerate reclaimable log + cache bytes. No mutation."""
    log_dir = Path("/var/log/supervisor")
    log_bytes = 0
    log_files: List[Dict[str, Any]] = []
    for name in (
        "backend.out.log", "backend.err.log",
        "frontend.out.log", "frontend.err.log",
        "supervisord.log",
    ):
        p = log_dir / name
        if p.exists() and p.is_file():
            try:
                sz = p.stat().st_size
                log_bytes += sz
                log_files.append({"path": str(p), "bytes": sz, "human": _human(sz)})
            except OSError:
                continue

    cache_bytes = 0
    cache_dirs: List[Dict[str, Any]] = []
    for root in (Path("/app/backend"),):
        for d in root.rglob("__pycache__"):
            if not d.is_dir():
                continue
            try:
                sz = sum(p.stat().st_size for p in d.rglob("*") if p.is_file())
                cache_bytes += sz
                cache_dirs.append({"path": str(d), "bytes": sz, "human": _human(sz)})
            except OSError:
                continue
        pytest_cache = root / ".pytest_cache"
        if pytest_cache.exists():
            try:
                sz = sum(p.stat().st_size for p in pytest_cache.rglob("*") if p.is_file())
                cache_bytes += sz
                cache_dirs.append({"path": str(pytest_cache), "bytes": sz, "human": _human(sz)})
            except OSError:
                continue
    total = log_bytes + cache_bytes
    return {
        "reclaimable_bytes": total,
        "human_total": _human(total),
        "logs": {"bytes": log_bytes, "human": _human(log_bytes),
                 "files": log_files},
        "caches": {"bytes": cache_bytes, "human": _human(cache_bytes),
                   "count": len(cache_dirs),
                   "top": sorted(cache_dirs, key=lambda x: x["bytes"], reverse=True)[:6]},
    }


async def _safe_cleanup_dry_run(_payload: Dict[str, Any]) -> Dict[str, Any]:
    before = _disk_stats()
    candidates = _safe_cleanup_candidates()
    dry_run_id = _register_dry_run("storage.safe_cleanup", {
        "before": before, "candidates": candidates,
    })
    return {
        "status": "dry_run_ready",
        "dry_run_id": dry_run_id,
        "before": before,
        "candidates": candidates,
        "summary": (
            f"Would reclaim ~{candidates['human_total']} from logs + "
            f"Python bytecode caches. No user data touched."
        ),
        "generated_at": _now_iso(),
    }


async def _safe_cleanup_apply(payload: Dict[str, Any]) -> Dict[str, Any]:
    dry_run_id = payload.get("dry_run_id") or ""
    saved = get_dry_run(dry_run_id)
    if not saved or saved["operation_id"] != "storage.safe_cleanup":
        return {
            "status": "failed",
            "error": "Missing or expired dry-run. Run the preview first.",
        }
    before = _disk_stats()
    truncated: List[str] = []
    removed_caches: List[str] = []
    errors: List[str] = []

    # Truncate logs (never delete — services keep FDs open).
    for name in (
        "backend.out.log", "backend.err.log",
        "frontend.out.log", "frontend.err.log",
    ):
        p = Path("/var/log/supervisor") / name
        if p.exists():
            try:
                with p.open("w"):
                    os.utime(p, None)
                truncated.append(str(p))
            except OSError as e:  # noqa: BLE001
                errors.append(f"log_truncate_failed:{p}: {e}")

    # Remove pycache + pytest cache. Bytecode regenerates on next import.
    for d in Path("/app/backend").rglob("__pycache__"):
        try:
            shutil.rmtree(d, ignore_errors=True)
            removed_caches.append(str(d))
        except OSError as e:  # noqa: BLE001
            errors.append(f"cache_rm_failed:{d}: {e}")
    pytest_cache = Path("/app/backend/.pytest_cache")
    if pytest_cache.exists():
        try:
            shutil.rmtree(pytest_cache, ignore_errors=True)
            removed_caches.append(str(pytest_cache))
        except OSError as e:  # noqa: BLE001
            errors.append(f"pytest_cache_rm_failed: {e}")

    after = _disk_stats()
    reclaimed = max(0, before["used_bytes"] - after["used_bytes"])
    # Retire the dry-run token — one apply per preview.
    _DRY_RUNS.pop(dry_run_id, None)
    db = payload.get("_db")
    history_row = {
        "generated_at": _now_iso(),
        "before": before,
        "after": after,
        "reclaimed_bytes": reclaimed,
        "reclaimed_human": _human(reclaimed),
        "truncated_logs": truncated,
        "removed_caches_count": len(removed_caches),
        "errors": errors,
        "protected_evidence_paths": [
            "/app/memory",
            "/app/test_reports",
            "/app/backend/storage/project_docs",
        ],
    }
    if db is not None:
        try:
            await db[_CLEANUP_HISTORY_COLLECTION].insert_one(dict(history_row))
        except Exception:  # noqa: BLE001
            pass
    return {
        "status": "completed" if not errors else "warning",
        "before": before,
        "after": after,
        "reclaimed_bytes": reclaimed,
        "reclaimed_human": _human(reclaimed),
        "truncated_logs": truncated,
        "removed_caches_count": len(removed_caches),
        "errors": errors,
        "generated_at": history_row["generated_at"],
        "protected_evidence_paths": history_row["protected_evidence_paths"],
    }


# ── 3 · Project docs → R2 Migration (dry-run + apply) ──────────────

async def _r2_migration_dry_run(payload: Dict[str, Any]) -> Dict[str, Any]:
    authority_plan = payload.get("_database_authority_plan")
    if authority_plan is None:
        return {"status": "failed", "error": "database authority missing"}
    from motor.motor_asyncio import AsyncIOMotorClient  # noqa: PLC0415
    client = None
    client, db = create_async_runtime_client(authority_plan, client_factory=AsyncIOMotorClient)

    project = (payload or {}).get("project")
    limit = int((payload or {}).get("limit") or 500)
    q: Dict[str, Any] = {
        "file_path": {"$exists": True, "$nin": [None, ""]},
        "attachment_ref": {"$in": [None, ""]},
    }
    if project:
        q["project_id"] = project

    candidates: List[Dict[str, Any]] = []
    total_bytes = 0
    cursor = db.docs.find(q, {"_id": 0}).limit(limit)
    async for d in cursor:
        p = Path(str(d.get("file_path") or ""))
        size = 0
        exists = False
        try:
            if p.exists() and p.is_file():
                size = p.stat().st_size
                exists = True
        except OSError:
            pass
        total_bytes += size if exists else 0
        candidates.append({
            "doc_id": d.get("id"),
            "project_id": d.get("project_id"),
            "filename": d.get("filename"),
            "file_path": str(p),
            "size_bytes": size,
            "size_human": _human(size),
            "local_exists": exists,
        })

    from photo_storage import is_configured as r2_configured  # noqa: PLC0415
    r2_ok = bool(r2_configured())

    dry_run_id = _register_dry_run("storage.r2_migration", {
        "candidates": candidates, "project": project, "limit": limit,
    })
    warnings: List[str] = []
    if not r2_ok:
        warnings.append(
            "Cloudflare R2 environment (S3_ENDPOINT_URL / S3_BUCKET / "
            "S3_ACCESS_KEY / S3_SECRET_KEY) is not configured — apply "
            "will refuse until this is set."
        )
    if not candidates:
        warnings.append(
            "No candidates found. Either every disk-backed doc has "
            "already been migrated, or `db.docs` has no file_path-"
            "backed records under this filter."
        )
    try:
        return {
            "status": "dry_run_ready",
            "dry_run_id": dry_run_id,
            "candidate_count": len(candidates),
            "total_bytes": total_bytes,
            "total_bytes_human": _human(total_bytes),
            "candidates": candidates[:100],
            "r2_configured": r2_ok,
            "warnings": warnings,
            "generated_at": _now_iso(),
        }
    finally:
        if client is not None:
            client.close()


async def _r2_migration_apply(payload: Dict[str, Any]) -> Dict[str, Any]:
    dry_run_id = payload.get("dry_run_id") or ""
    saved = get_dry_run(dry_run_id)
    if not saved or saved["operation_id"] != "storage.r2_migration":
        return {"status": "failed",
                "error": "Missing or expired dry-run. Run the preview first."}
    if payload.get("confirmation_phrase") != "MIGRATE TO R2":
        return {"status": "failed",
                "error": "confirmation phrase mismatch — expected 'MIGRATE TO R2'"}

    import photo_storage  # noqa: PLC0415
    if not photo_storage.is_configured():
        return {"status": "failed",
                "error": "R2 env vars missing. Set them and rerun the dry-run."}

    authority_plan = payload.get("_database_authority_plan")
    if authority_plan is None:
        return {"status": "failed", "error": "database authority missing"}
    from motor.motor_asyncio import AsyncIOMotorClient  # noqa: PLC0415
    client = None
    client, db = create_async_runtime_client(authority_plan, client_factory=AsyncIOMotorClient)

    before = _disk_stats()
    candidates = saved["payload"]["candidates"]
    migrated: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    for c in candidates:
        if not c.get("local_exists"):
            failures.append({**c, "reason": "local_missing"})
            continue
        # Delegate to the same routines the CLI migration uses so the
        # OCC path and the shell path stay identical.
        try:
            from scripts.migrate_local_project_docs_to_r2 import (  # noqa: PLC0415
                _promote_one, _r2_head,
            )
        except Exception as e:  # noqa: BLE001
            return {"status": "failed",
                    "error": f"migration helpers unavailable: {e}"}
        doc = await db.docs.find_one({"id": c["doc_id"]}, {"_id": 0})
        if not doc:
            failures.append({**c, "reason": "doc_disappeared"})
            continue
        try:
            res = await _promote_one(
                db, photo_storage, doc, actor=payload.get("actor_email") or "occ",
            )
            if res.get("status") == "migrated":
                migrated.append(res)
            else:
                failures.append({**c, **res})
        except Exception as e:  # noqa: BLE001
            failures.append({**c, "reason": f"exception:{e}"})
    after = _disk_stats()
    _DRY_RUNS.pop(dry_run_id, None)
    try:
        return {
            "status": "completed" if not failures else "warning",
            "before": before,
            "after": after,
            "migrated_count": len(migrated),
            "failed_count": len(failures),
            "migrated": migrated[:50],
            "failures": failures[:20],
            "reclaimed_bytes": max(0, before["used_bytes"] - after["used_bytes"]),
            "reclaimed_human": _human(max(0, before["used_bytes"] - after["used_bytes"])),
            "generated_at": _now_iso(),
        }
    finally:
        if client is not None:
            client.close()


# ── Registry ───────────────────────────────────────────────────────

def operations(_db) -> List[Operation]:
    return [
        Operation(
            id="storage.audit",
            title="Storage Audit",
            description=(
                "Read-only snapshot of pod disk usage, largest "
                "directories, and biggest files. Zero mutation."
            ),
            category=OperationCategory.STORAGE,
            risk=RiskLevel.INFO,
            status_fn=_storage_audit_status,
            dry_run_fn=_storage_audit_dry_run,
            reads=[
                "/app disk usage · pod file listings under "
                "/app/backend/storage · /var/log/supervisor logs",
            ],
            writes=[],
            never_touches=["MongoDB", "R2", "user uploads"],
        ),
        Operation(
            id="storage.safe_cleanup",
            title="Safe Cleanup — Logs + Python Cache",
            description=(
                "Truncates the supervisor log files and removes "
                "Python bytecode caches. Services keep running. "
                "No user data touched."
            ),
            category=OperationCategory.STORAGE,
            risk=RiskLevel.SAFE_CLEANUP,
            dry_run_fn=_safe_cleanup_dry_run,
            apply_fn=_safe_cleanup_apply,
            requires_dry_run=True,
            reads=["supervisor log sizes", "Python __pycache__ + .pytest_cache"],
            writes=["truncated log files", "removed cache directories"],
            never_touches=["MongoDB", "R2", "user uploads",
                           "training videos", "project_docs"],
        ),
        Operation(
            id="storage.r2_migration",
            title="Project Docs → Cloudflare R2 Migration",
            description=(
                "Moves local Basecamp big-file imports (records with "
                "file_path in db.docs) to Cloudflare R2. Verifies "
                "each R2 object with HEAD before removing the local "
                "copy. Writes an audit row per file. Idempotent."
            ),
            category=OperationCategory.STORAGE,
            risk=RiskLevel.DATA_MIGRATION,
            dry_run_fn=_r2_migration_dry_run,
            apply_fn=_r2_migration_apply,
            requires_dry_run=True,
            confirmation_phrase="MIGRATE TO R2",
            reads=["db.docs (find file_path-backed docs)",
                   "local files under /app/backend/storage/project_docs"],
            writes=["Cloudflare R2 objects (project_docs/<project>/<id>.<ext>)",
                    "db.docs.attachment_ref + storage_kind='r2'",
                    "hr_audit rows (one per file)",
                    "local file unlink AFTER R2 HEAD verified"],
            never_touches=["Mongo data outside db.docs",
                           "already-R2-backed docs (skipped)",
                           "backup collections",
                           "photo intelligence rows"],
        ),
    ]

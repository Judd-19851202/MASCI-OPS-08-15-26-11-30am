"""TRACK 24.17 · Backups posture read-only probe."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .registry import Operation, OperationCategory, RiskLevel


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _backup_health_status(_payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _backup_health_dry_run(_payload)


async def _backup_health_dry_run(_payload: Dict[str, Any]) -> Dict[str, Any]:
    backup_dir = Path(os.environ.get("BACKUP_DIR") or "/app/backend/backups")
    exists = backup_dir.exists() and backup_dir.is_dir()
    files: List[Dict[str, Any]] = []
    total_bytes = 0
    if exists:
        for p in backup_dir.rglob("*"):
            try:
                if p.is_file():
                    sz = p.stat().st_size
                    files.append({
                        "path": str(p), "bytes": sz,
                        "modified": datetime.fromtimestamp(
                            p.stat().st_mtime, tz=timezone.utc,
                        ).isoformat(),
                    })
                    total_bytes += sz
            except OSError:
                continue
    files.sort(key=lambda x: x["modified"], reverse=True)
    latest = files[0] if files else None
    state = "healthy"
    warnings: List[str] = []
    if not exists:
        state = "warning"
        warnings.append(f"Backup directory does not exist: {backup_dir}")
    elif not files:
        state = "warning"
        warnings.append(
            "Backup directory exists but contains no files. "
            "Verify scheduled backup jobs are armed."
        )
    return {
        "status": state,
        "summary": (
            f"{len(files)} local backup file(s) · latest: "
            + (latest["modified"] if latest else "none")
            if files else "no local backups"
        ),
        "backup_dir": str(backup_dir),
        "file_count": len(files),
        "total_bytes": total_bytes,
        "latest": latest,
        "warnings": warnings,
        "generated_at": _now_iso(),
    }


def operations(_db) -> List[Operation]:
    return [
        Operation(
            id="backups.health",
            title="Backup Health Check",
            description=(
                "Read-only inspection of the local backup directory. "
                "Reports latest backup, file count, and total size."
            ),
            category=OperationCategory.BACKUPS,
            risk=RiskLevel.INFO,
            status_fn=_backup_health_status,
            dry_run_fn=_backup_health_dry_run,
            reads=["local backup directory listing"],
            writes=[],
            never_touches=["backup files", "Mongo", "R2"],
        ),
    ]

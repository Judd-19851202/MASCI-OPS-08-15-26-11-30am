"""TRACK 24.17 · Backups posture read-only probe."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from .backup_truth import load_canonical_backup_truth, local_backup_cache_snapshot
from .registry import Operation, OperationCategory, RiskLevel


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _backup_health_status(_payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _backup_health_dry_run(_payload)


async def _backup_health_dry_run(_payload: Dict[str, Any]) -> Dict[str, Any]:
    local_cache = local_backup_cache_snapshot()
    canonical = await load_canonical_backup_truth(_payload)
    warnings: List[str] = []
    if local_cache.get("file_count", 0) == 0:
        warnings.append(
            "Local backup cache is empty. In production this is informational only — authoritative backup truth comes from canonical R2 recovery posture."
        )
    state = canonical.get("status") or "warning"
    summary = canonical.get("summary") or "Canonical backup truth unavailable."
    snapshot = canonical.get("snapshot") or {}
    if local_cache.get("file_count", 0) > 0:
        summary = f"{summary} · local cache {local_cache.get('file_count')} file(s)"
    return {
        "status": state,
        "summary": summary,
        "backup_dir": local_cache.get("backup_dir"),
        "file_count": local_cache.get("file_count", 0),
        "total_bytes": local_cache.get("total_bytes", 0),
        "latest": local_cache.get("latest"),
        "local_backup_cache": local_cache,
        "canonical_backup_truth": snapshot,
        "canonical_source": "/api/admin/recovery/snapshot",
        "warnings": warnings,
        "generated_at": _now_iso(),
    }


def operations(_db) -> List[Operation]:
    return [
        Operation(
            id="backups.health",
            title="Backup Health Check",
            description=(
                "Canonical backup posture sourced from the recovery snapshot, "
                "with local backup cache shown as secondary context only."
            ),
            category=OperationCategory.BACKUPS,
            risk=RiskLevel.INFO,
            status_fn=_backup_health_status,
            dry_run_fn=_backup_health_dry_run,
            reads=["canonical recovery snapshot", "local backup cache listing"],
            writes=[],
            never_touches=["backup files", "Mongo", "R2"],
        ),
    ]

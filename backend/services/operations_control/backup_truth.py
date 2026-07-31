from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def local_backup_cache_snapshot() -> Dict[str, Any]:
    backup_dir = Path(os.environ.get("BACKUP_DIR") or "/app/backend/backups")
    exists = backup_dir.exists() and backup_dir.is_dir()
    files: List[Dict[str, Any]] = []
    total_bytes = 0
    if exists:
        for p in backup_dir.rglob("*"):
            try:
                if p.is_file():
                    sz = p.stat().st_size
                    files.append(
                        {
                            "path": str(p),
                            "bytes": sz,
                            "modified": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat(),
                        }
                    )
                    total_bytes += sz
            except OSError:
                continue
    files.sort(key=lambda x: x["modified"], reverse=True)
    latest = files[0] if files else None
    return {
        "backup_dir": str(backup_dir),
        "exists": exists,
        "file_count": len(files),
        "total_bytes": total_bytes,
        "latest": latest,
        "generated_at": _now_iso(),
    }


def pill_to_occ_status(pill: Any) -> str:
    normalized = str(pill or "").strip().upper()
    if normalized == "GREEN":
        return "healthy"
    if normalized == "RED":
        return "critical"
    if normalized in {"AMBER", "YELLOW"}:
        return "warning"
    return "unavailable"


async def load_canonical_backup_truth(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = payload.get("_db")
    if db is None:
        return {
            "available": False,
            "status": "unavailable",
            "summary": "Canonical backup truth requires an active database session.",
            "snapshot": None,
            "generated_at": _now_iso(),
        }

    try:
        from routes import recovery_dashboard as recovery_module  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001
        return {
            "available": False,
            "status": "unavailable",
            "summary": "Canonical recovery helpers not importable.",
            "error": str(exc)[:200],
            "snapshot": None,
            "generated_at": _now_iso(),
        }

    async def _stub_admin():  # pragma: no cover
        return {"email": "occ", "role": "admin"}

    try:
        router = recovery_module.build_recovery_dashboard_router(db, _stub_admin)
    except Exception as exc:  # noqa: BLE001
        return {
            "available": False,
            "status": "unavailable",
            "summary": "Could not build recovery snapshot router.",
            "error": str(exc)[:200],
            "snapshot": None,
            "generated_at": _now_iso(),
        }

    endpoint_fn = None
    for route in router.routes:
        if getattr(route, "path", "").endswith("/recovery/snapshot"):
            endpoint_fn = route.endpoint
            break
    if not endpoint_fn:
        return {
            "available": False,
            "status": "unavailable",
            "summary": "Canonical recovery snapshot endpoint not found.",
            "snapshot": None,
            "generated_at": _now_iso(),
        }

    try:
        snapshot = await endpoint_fn()
    except Exception as exc:  # noqa: BLE001
        return {
            "available": False,
            "status": "critical",
            "summary": f"Canonical recovery snapshot crashed: {str(exc)[:160]}",
            "error": str(exc)[:200],
            "snapshot": None,
            "generated_at": _now_iso(),
        }

    pill = str((snapshot or {}).get("pill") or "").upper()
    last_backup = (snapshot or {}).get("last_backup") or {}
    filename = last_backup.get("filename") or ((snapshot or {}).get("archive_lineage") or {}).get("authoritative_artifact", {}).get("filename") or "unknown archive"
    age = (snapshot or {}).get("backup_age_minutes")
    age_text = f"{age:.1f}m" if isinstance(age, (int, float)) else "unknown age"
    return {
        "available": True,
        "status": pill_to_occ_status(pill),
        "summary": f"Canonical recovery posture {pill or 'UNKNOWN'} · latest {filename} · age {age_text}",
        "snapshot": snapshot,
        "generated_at": _now_iso(),
    }

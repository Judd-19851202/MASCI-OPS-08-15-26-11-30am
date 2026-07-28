"""Authoritative read-side helpers for governed R2 backup retention."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from lib.backup_paths import configured_backup_prefix
from lib.r2_retention import (
    ARCHITECTURE,
    DAILY_RETENTION_DAYS,
    HOURLY_RETENTION_HOURS,
    MONTHLY_RETENTION_MONTHS,
    WEEKLY_RETENTION_DAYS,
    plan_retention,
)


def _coerce_dt(raw: Any) -> Optional[datetime]:
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if isinstance(raw, str) and raw.strip():
        text = raw.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _human_bytes(n: int) -> str:
    value = float(int(n or 0))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def retention_policy_payload() -> Dict[str, Any]:
    return {
        "architecture": ARCHITECTURE,
        "hourly_hours": HOURLY_RETENTION_HOURS,
        "daily_days": DAILY_RETENTION_DAYS,
        "weekly_days": WEEKLY_RETENTION_DAYS,
        "monthly_months": MONTHLY_RETENTION_MONTHS,
    }


def build_retention_rows(backups: List[Dict[str, Any]], *, now: Optional[datetime] = None) -> Dict[str, Any]:
    as_of = now or datetime.now(timezone.utc)
    normalized: List[Dict[str, Any]] = []
    for row in backups:
        ts = _coerce_dt(row.get("timestamp") or row.get("last_modified") or row.get("ts"))
        key = str(row.get("key") or "").strip()
        if not key or ts is None:
            continue
        normalized.append({
            "key": key,
            "timestamp": ts,
            "size_bytes": int(row.get("size_bytes") or row.get("size") or 0),
            "healthy": bool(row.get("healthy", True)),
            "protected": bool(row.get("protected", False)),
            "hold": bool(row.get("hold", False)),
            "active_restore": bool(row.get("active_restore", False)),
        })
    plan = plan_retention(normalized, now=as_of)
    decisions = []
    for decision in plan.decisions:
        decisions.append({
            "key": decision.key,
            "timestamp": decision.timestamp.isoformat(),
            "age_days": round(decision.age_days, 3),
            "window": decision.window,
            "keep": bool(decision.keep),
            "reason": decision.reason,
            "size_bytes": decision.size_bytes,
            "size_human": _human_bytes(int(decision.size_bytes or 0)),
        })
    kept_bytes = sum(int(decision.get("size_bytes") or 0) for decision in decisions if decision.get("keep"))
    deleted_bytes = sum(int(decision.get("size_bytes") or 0) for decision in decisions if not decision.get("keep"))
    return {
        "generated_at": as_of.isoformat(),
        "policy": retention_policy_payload(),
        "archive_count": len(normalized),
        "kept_count": len(plan.keep),
        "would_delete_count": len(plan.delete),
        "kept_bytes": kept_bytes,
        "would_delete_bytes": deleted_bytes,
        "kept_bytes_human": _human_bytes(kept_bytes),
        "would_delete_bytes_human": _human_bytes(deleted_bytes),
        "survivors_by_tier": dict(plan.survivor_counts_by_tier),
        "deleted_by_tier": dict(plan.deleted_by_tier),
        "delete_sample_keys": list(plan.delete_sample_keys),
        "preserve_sample_keys": list(plan.preserve_sample_keys),
        "projected_post_retention_size_bytes": plan.projected_post_retention_size_bytes,
        "projected_post_retention_size_human": _human_bytes(int(plan.projected_post_retention_size_bytes or 0)),
        "decisions": decisions,
    }


async def fetch_backup_inventory(db, *, limit: int = 1000) -> List[Dict[str, Any]]:
    prefix = configured_backup_prefix()
    rows: List[Dict[str, Any]] = []
    cursor = db.backup_health.find(
        {
            "mode": "complete-r2",
            "ok": True,
            "filename": {"$nin": [None, ""]},
        },
        {"_id": 0, "filename": 1, "size_bytes": 1, "ts": 1},
    ).sort("ts", -1).limit(limit)
    async for row in cursor:
        filename = str(row.get("filename") or "").strip()
        if not filename:
            continue
        rows.append({
            "key": f"{prefix.rstrip('/')}/{filename}",
            "timestamp": row.get("ts"),
            "size_bytes": int(row.get("size_bytes") or 0),
            "healthy": True,
        })
    return rows


async def latest_retention_snapshot(db, *, limit: int = 1000) -> Dict[str, Any]:
    rows = await fetch_backup_inventory(db, limit=limit)
    return build_retention_rows(rows)
"""Approved R2 retention for complete archives.

Daily, weekly, and monthly recovery points are selected surviving hourly
archives. We do not create duplicate archive copies.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, List, Optional

logger = logging.getLogger(__name__)

ARCHITECTURE = "selected_surviving_hourly_archives"
HOURLY_RETENTION_HOURS = 72
DAILY_RETENTION_DAYS = 30
WEEKLY_RETENTION_DAYS = 90
MONTHLY_RETENTION_MONTHS = 12

_FILENAME_RE = re.compile(
    r"^MASCI_(?:complete|full|lite)_backup_(?P<date>\d{4}-\d{2}-\d{2})_"
    r"(?P<time>\d{6})Z\.zip$"
)


@dataclass
class RetentionDecision:
    key: str
    timestamp: datetime
    age_days: float
    window: str
    keep: bool
    reason: str
    size_bytes: Optional[int] = None


@dataclass
class RetentionPlan:
    keep: List[str] = field(default_factory=list)
    delete: List[str] = field(default_factory=list)
    decisions: List[RetentionDecision] = field(default_factory=list)
    survivor_counts_by_tier: dict = field(default_factory=lambda: {"hourly": 0, "daily": 0, "weekly": 0, "monthly": 0, "special": 0})
    deleted_by_tier: dict = field(default_factory=lambda: {"daily": 0, "weekly": 0, "monthly": 0, "expired": 0})
    would_delete_count: int = 0
    would_preserve_count: int = 0
    delete_sample_keys: List[str] = field(default_factory=list)
    preserve_sample_keys: List[str] = field(default_factory=list)
    projected_post_retention_size_bytes: Optional[int] = None


def _parse_filename_to_ts(key: str) -> Optional[datetime]:
    leaf = key.rsplit("/", 1)[-1]
    match = _FILENAME_RE.match(leaf)
    if not match:
        return None
    try:
        return datetime.strptime(
            f"{match.group('date')} {match.group('time')}", "%Y-%m-%d %H%M%S"
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _month_distance(now: datetime, ts: datetime) -> int:
    return (now.year - ts.year) * 12 + (now.month - ts.month)


def _normalize_record(entry) -> dict:
    if isinstance(entry, dict):
        return {
            "key": entry["key"],
            "timestamp": entry["timestamp"],
            "size_bytes": entry.get("size_bytes"),
            "healthy": bool(entry.get("healthy", True)),
            "protected": bool(entry.get("protected", False)),
            "hold": bool(entry.get("hold", False)),
            "active_restore": bool(entry.get("active_restore", False)),
        }
    if len(entry) == 2:
        key, ts = entry
        size_bytes = None
    else:
        key, ts, size_bytes = entry
    return {
        "key": key,
        "timestamp": ts,
        "size_bytes": size_bytes,
        "healthy": True,
        "protected": False,
        "hold": False,
        "active_restore": False,
    }


def plan_retention(keys: Iterable, *, now: Optional[datetime] = None) -> RetentionPlan:
    now = now or datetime.now(timezone.utc)
    plan = RetentionPlan()
    records = [_normalize_record(item) for item in keys]
    records.sort(key=lambda row: (row["timestamp"], row["key"]), reverse=True)
    newest_healthy_key = next((row["key"] for row in records if row.get("healthy")), None)
    daily_groups: dict[str, list[dict]] = {}
    weekly_groups: dict[str, list[dict]] = {}
    monthly_groups: dict[str, list[dict]] = {}

    for row in records:
        key = row["key"]
        ts = row["timestamp"]
        size_bytes = row.get("size_bytes")
        age_days = (now - ts).total_seconds() / 86400.0
        if row.get("protected") or row.get("hold") or row.get("active_restore"):
            plan.keep.append(key)
            plan.survivor_counts_by_tier["special"] += 1
            plan.decisions.append(RetentionDecision(key, ts, age_days, "special", True, "protected_or_hold", size_bytes))
            continue
        if not row.get("healthy", True):
            plan.keep.append(key)
            plan.survivor_counts_by_tier["special"] += 1
            plan.decisions.append(RetentionDecision(key, ts, age_days, "special", True, "not_healthy_preserved_fail_closed", size_bytes))
            continue
        if newest_healthy_key and key == newest_healthy_key:
            plan.keep.append(key)
            plan.survivor_counts_by_tier["special"] += 1
            plan.decisions.append(RetentionDecision(key, ts, age_days, "special", True, "newest_healthy_floor", size_bytes))
            continue
        if age_days < 0 or age_days <= (HOURLY_RETENTION_HOURS / 24):
            plan.keep.append(key)
            plan.survivor_counts_by_tier["hourly"] += 1
            plan.decisions.append(RetentionDecision(key, ts, age_days, "hourly", True, "hourly_window", size_bytes))
        elif age_days <= DAILY_RETENTION_DAYS:
            daily_groups.setdefault(ts.strftime("%Y-%m-%d"), []).append(row)
        elif age_days <= WEEKLY_RETENTION_DAYS:
            iso_year, iso_week, _ = ts.isocalendar()
            weekly_groups.setdefault(f"{iso_year}-W{iso_week:02d}", []).append(row)
        elif _month_distance(now, ts) < MONTHLY_RETENTION_MONTHS:
            monthly_groups.setdefault(ts.strftime("%Y-%m"), []).append(row)
        else:
            plan.delete.append(key)
            plan.deleted_by_tier["expired"] += 1
            plan.decisions.append(RetentionDecision(key, ts, age_days, "expired", False, "older_than_monthly_horizon", size_bytes))

    def _pick(groups: dict[str, list[dict]], survivor_window: str, delete_window: str) -> None:
        for bucket, group in groups.items():
            group.sort(key=lambda row: (row["timestamp"], row["key"]), reverse=True)
            for idx, row in enumerate(group):
                key = row["key"]
                ts = row["timestamp"]
                size_bytes = row.get("size_bytes")
                age_days = (now - ts).total_seconds() / 86400.0
                if idx == 0:
                    plan.keep.append(key)
                    plan.survivor_counts_by_tier[survivor_window] += 1
                    plan.decisions.append(RetentionDecision(key, ts, age_days, survivor_window, True, f"{survivor_window}_survivor_{bucket}", size_bytes))
                else:
                    plan.delete.append(key)
                    plan.deleted_by_tier[delete_window] += 1
                    plan.decisions.append(RetentionDecision(key, ts, age_days, survivor_window, False, f"{survivor_window}_delete_{bucket}", size_bytes))

    _pick(daily_groups, "daily", "daily")
    _pick(weekly_groups, "weekly", "weekly")
    _pick(monthly_groups, "monthly", "monthly")

    plan.would_delete_count = len(plan.delete)
    plan.would_preserve_count = len(plan.keep)
    plan.delete_sample_keys = plan.delete[:10]
    plan.preserve_sample_keys = plan.keep[:10]
    if all(decision.size_bytes is not None for decision in plan.decisions):
        plan.projected_post_retention_size_bytes = int(sum((decision.size_bytes or 0) for decision in plan.decisions if decision.keep))
    return plan


def list_r2_backups(s3, bucket: str, prefix: str = "backups/auto-90d/") -> List[dict]:
    out: List[dict] = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []) or []:
            key = obj["Key"]
            ts = _parse_filename_to_ts(key)
            if ts is None:
                logger.debug(f"[r2-retention] skip unknown-naming key={key}")
                continue
            out.append({"key": key, "timestamp": ts, "size_bytes": obj.get("Size")})
    return out


def enforce_r2_retention(s3, bucket: str, *, prefix: str = "backups/auto-90d/", dry_run: bool = False, now: Optional[datetime] = None) -> dict:
    result = {
        "ok": True,
        "dry_run": bool(dry_run),
        "scanned": 0,
        "kept": 0,
        "deleted": 0,
        "survivors_by_tier": {"hourly": 0, "daily": 0, "weekly": 0, "monthly": 0, "special": 0},
        "deleted_by_tier": {"daily": 0, "weekly": 0, "monthly": 0, "expired": 0},
        "would_delete_count": 0,
        "would_preserve_count": 0,
        "delete_sample_keys": [],
        "preserve_sample_keys": [],
        "projected_post_retention_size_bytes": None,
        "errors": [],
        "error_count": 0,
        "architecture": ARCHITECTURE,
    }
    try:
        keys = list_r2_backups(s3, bucket, prefix=prefix)
        result["scanned"] = len(keys)
        plan = plan_retention(keys, now=now)
        result["survivors_by_tier"] = plan.survivor_counts_by_tier
        result["deleted_by_tier"] = plan.deleted_by_tier
        result["kept"] = len(plan.keep)
        result["would_delete_count"] = plan.would_delete_count
        result["would_preserve_count"] = plan.would_preserve_count
        result["delete_sample_keys"] = plan.delete_sample_keys
        result["preserve_sample_keys"] = plan.preserve_sample_keys
        result["projected_post_retention_size_bytes"] = plan.projected_post_retention_size_bytes
        if plan.delete and not dry_run:
            for i in range(0, len(plan.delete), 1000):
                chunk = plan.delete[i:i + 1000]
                try:
                    s3.delete_objects(
                        Bucket=bucket,
                        Delete={"Objects": [{"Key": key} for key in chunk], "Quiet": True},
                    )
                    result["deleted"] += len(chunk)
                except Exception as exc:  # noqa: BLE001
                    msg = f"delete_chunk_failed at offset {i}: {exc}"
                    logger.warning(f"[r2-retention] {msg}")
                    result["errors"].append(msg)
                    result["error_count"] += 1
                    result["ok"] = False
        logger.info(
            f"[r2-retention] dry_run={dry_run} scanned={result['scanned']} kept={result['kept']} "
            f"deleted={result['deleted']} survivors={result['survivors_by_tier']} deleted_by_tier={result['deleted_by_tier']}"
        )
    except Exception as exc:  # noqa: BLE001
        result["ok"] = False
        result["errors"].append(f"enforce_failed: {exc}")
        result["error_count"] += 1
        logger.warning(f"[r2-retention] top-level failure: {exc}")
    return result


__all__ = [
    "ARCHITECTURE",
    "HOURLY_RETENTION_HOURS",
    "DAILY_RETENTION_DAYS",
    "WEEKLY_RETENTION_DAYS",
    "MONTHLY_RETENTION_MONTHS",
    "RetentionDecision",
    "RetentionPlan",
    "plan_retention",
    "list_r2_backups",
    "enforce_r2_retention",
    "_parse_filename_to_ts",
]

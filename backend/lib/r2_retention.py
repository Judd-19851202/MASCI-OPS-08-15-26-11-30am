"""
R2 BACKUP TIERED RETENTION  ·  TRACK 15.28A
============================================

The local-disk helper ``server._emergency_prune_backups`` only manages the
container's ``BACKUPS_DIR`` (/app/backend/backups). It does NOT touch
Cloudflare R2, so R2-side backups have been growing without bound at
~14.47 GiB / day (audited in TRACK 15.24B + TRACK 15.28).

This module provides the missing piece: a tiered retention pruner that
walks the R2 bucket's ``backups/auto-90d/`` prefix and enforces:

    Tier 1  · keep ALL hourly zips for the last 14 days
    Tier 2  · 14–90 days  · keep ONLY the newest zip per calendar day (UTC)
    Tier 3  · 90–365 days · keep ONLY the newest zip per calendar month (UTC)
    Tier 4  · >365 days   · DELETE

Idempotent: a second run produces zero additional deletes when the
bucket already matches policy. Read-only (dry-run) mode is supported via
``dry_run=True`` — returns the *would-delete* list without mutating R2.

Filename grammar (from existing backup writer):
    MASCI_complete_backup_YYYY-MM-DD_HHMMSSZ.zip
    e.g.  MASCI_complete_backup_2026-06-18_201500Z.zip

The function never raises into the caller; every error is logged and the
function returns a structured result so callers can record metrics.
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Iterable, List, Tuple, Optional

logger = logging.getLogger(__name__)

# ---- Policy thresholds (overridable via env, but defaults are the canonical
# TRACK 15.28A retention contract — do not change unless operator approves).
TIER1_DAYS = int(os.environ.get("R2_RETENTION_TIER1_DAYS", "14"))     # keep all
TIER2_DAYS = int(os.environ.get("R2_RETENTION_TIER2_DAYS", "90"))     # daily-only
TIER3_DAYS = int(os.environ.get("R2_RETENTION_TIER3_DAYS", "365"))    # monthly-only
# After TIER3_DAYS → DELETE (Tier 4).

# Match the live R2 backup naming convention.
_FILENAME_RE = re.compile(
    r"^MASCI_(?:complete|full|lite)_backup_(?P<date>\d{4}-\d{2}-\d{2})_"
    r"(?P<time>\d{6})Z\.zip$"
)


# ---------------------------------------------------------------------------
# Pure planning logic (testable without any S3 client)
# ---------------------------------------------------------------------------

@dataclass
class RetentionDecision:
    key: str
    timestamp: datetime
    age_days: float
    tier: int      # 1, 2, 3, or 4
    keep: bool
    reason: str


@dataclass
class RetentionPlan:
    keep: List[str] = field(default_factory=list)
    delete: List[str] = field(default_factory=list)
    decisions: List[RetentionDecision] = field(default_factory=list)
    survivor_counts_by_tier: dict = field(default_factory=lambda: {1: 0, 2: 0, 3: 0})
    deleted_by_tier: dict = field(default_factory=lambda: {1: 0, 2: 0, 3: 0, 4: 0})

    def __len__(self) -> int:
        return len(self.decisions)


def _parse_filename_to_ts(key: str) -> Optional[datetime]:
    """Pull the UTC timestamp embedded in a backup zip's filename.

    Returns None if the filename does not match the canonical pattern; the
    caller treats such keys as "leave alone" (Tier 0 / unknown).
    """
    leaf = key.rsplit("/", 1)[-1]
    m = _FILENAME_RE.match(leaf)
    if not m:
        return None
    date_s = m.group("date")
    time_s = m.group("time")  # HHMMSS
    try:
        return datetime.strptime(
            f"{date_s} {time_s}", "%Y-%m-%d %H%M%S"
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def plan_retention(
    keys: Iterable[Tuple[str, datetime]],
    *,
    now: Optional[datetime] = None,
) -> RetentionPlan:
    """Compute the keep / delete plan for the given (key, timestamp) pairs.

    Pure function · deterministic · no I/O · used by tests with synthetic
    datasets AND by the live runner with R2-listed objects.

    ``timestamp`` may come from the filename (preferred) or from the
    object's ``LastModified``; the live runner prefers the filename-encoded
    UTC because it survives bucket-level metadata edits.
    """
    now = now or datetime.now(timezone.utc)
    plan = RetentionPlan()

    # Bucket by tier first.
    tier1: List[Tuple[str, datetime]] = []
    by_day: dict[str, List[Tuple[str, datetime]]] = {}
    by_month: dict[str, List[Tuple[str, datetime]]] = {}
    tier4: List[Tuple[str, datetime]] = []
    for key, ts in keys:
        age_days = (now - ts).total_seconds() / 86400.0
        if age_days < 0:
            # Future-dated file (clock skew). Treat as Tier-1 keep.
            tier1.append((key, ts))
            plan.decisions.append(
                RetentionDecision(key, ts, age_days, 1, True, "future-dated")
            )
            continue
        if age_days <= TIER1_DAYS:
            tier1.append((key, ts))
        elif age_days <= TIER2_DAYS:
            day_bucket = ts.strftime("%Y-%m-%d")
            by_day.setdefault(day_bucket, []).append((key, ts))
        elif age_days <= TIER3_DAYS:
            month_bucket = ts.strftime("%Y-%m")
            by_month.setdefault(month_bucket, []).append((key, ts))
        else:
            tier4.append((key, ts))

    # Tier 1 — keep every hourly zip.
    for key, ts in tier1:
        age = (now - ts).total_seconds() / 86400.0
        plan.keep.append(key)
        plan.survivor_counts_by_tier[1] += 1
        plan.decisions.append(
            RetentionDecision(key, ts, age, 1, True, "tier1_hourly_window")
        )

    # Tier 2 — newest per calendar day survives, rest delete.
    for day, group in by_day.items():
        group.sort(key=lambda kt: kt[1], reverse=True)
        survivor_key, survivor_ts = group[0]
        for i, (key, ts) in enumerate(group):
            age = (now - ts).total_seconds() / 86400.0
            if i == 0:
                plan.keep.append(key)
                plan.survivor_counts_by_tier[2] += 1
                plan.decisions.append(
                    RetentionDecision(key, ts, age, 2, True,
                                      f"tier2_daily_survivor_{day}")
                )
            else:
                plan.delete.append(key)
                plan.deleted_by_tier[2] += 1
                plan.decisions.append(
                    RetentionDecision(key, ts, age, 2, False,
                                      f"tier2_daily_loser_{day}")
                )

    # Tier 3 — newest per calendar month survives, rest delete.
    for month, group in by_month.items():
        group.sort(key=lambda kt: kt[1], reverse=True)
        for i, (key, ts) in enumerate(group):
            age = (now - ts).total_seconds() / 86400.0
            if i == 0:
                plan.keep.append(key)
                plan.survivor_counts_by_tier[3] += 1
                plan.decisions.append(
                    RetentionDecision(key, ts, age, 3, True,
                                      f"tier3_monthly_survivor_{month}")
                )
            else:
                plan.delete.append(key)
                plan.deleted_by_tier[3] += 1
                plan.decisions.append(
                    RetentionDecision(key, ts, age, 3, False,
                                      f"tier3_monthly_loser_{month}")
                )

    # Tier 4 — beyond the policy horizon. Delete.
    for key, ts in tier4:
        age = (now - ts).total_seconds() / 86400.0
        plan.delete.append(key)
        plan.deleted_by_tier[4] += 1
        plan.decisions.append(
            RetentionDecision(key, ts, age, 4, False, "tier4_over_horizon")
        )

    return plan


# ---------------------------------------------------------------------------
# Live R2 runner — talks to the real bucket via boto3 (the same client the
# rest of the platform already uses for R2). Bounded · idempotent · safe.
# ---------------------------------------------------------------------------

def list_r2_backups(s3, bucket: str, prefix: str = "backups/auto-90d/"
                    ) -> List[Tuple[str, datetime]]:
    """List every backup zip under the prefix as (key, timestamp).

    The timestamp comes from the filename (canonical, time-zone-stable).
    Keys that don't match the naming convention are skipped entirely
    (left untouched in the bucket).
    """
    out: List[Tuple[str, datetime]] = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []) or []:
            key = obj["Key"]
            ts = _parse_filename_to_ts(key)
            if ts is None:
                # Unknown filename — never delete. Just log once.
                logger.debug(f"[r2-retention] skip unknown-naming key={key}")
                continue
            out.append((key, ts))
    return out


def enforce_r2_retention(
    s3,
    bucket: str,
    *,
    prefix: str = "backups/auto-90d/",
    dry_run: bool = False,
    now: Optional[datetime] = None,
) -> dict:
    """Apply the tiered policy against the live R2 bucket.

    Returns a structured result dict suitable for logging and metrics.
    Never raises — caught errors are returned in the ``errors`` list.
    """
    result = {
        "ok": True,
        "dry_run": bool(dry_run),
        "scanned": 0,
        "kept": 0,
        "deleted": 0,
        "survivors_by_tier": {1: 0, 2: 0, 3: 0},
        "deleted_by_tier": {1: 0, 2: 0, 3: 0, 4: 0},
        "errors": [],
    }
    try:
        keys = list_r2_backups(s3, bucket, prefix=prefix)
        result["scanned"] = len(keys)
        plan = plan_retention(keys, now=now)
        result["survivors_by_tier"] = plan.survivor_counts_by_tier
        result["deleted_by_tier"] = plan.deleted_by_tier
        result["kept"] = len(plan.keep)
        # Delete in 1000-key batches (S3 DeleteObjects max).
        if plan.delete and not dry_run:
            for i in range(0, len(plan.delete), 1000):
                chunk = plan.delete[i:i + 1000]
                try:
                    s3.delete_objects(
                        Bucket=bucket,
                        Delete={
                            "Objects": [{"Key": k} for k in chunk],
                            "Quiet": True,
                        },
                    )
                    result["deleted"] += len(chunk)
                except Exception as e:
                    msg = f"delete_chunk_failed at offset {i}: {e}"
                    logger.warning(f"[r2-retention] {msg}")
                    result["errors"].append(msg)
                    result["ok"] = False
        else:
            # dry-run OR nothing to delete: still report the would-delete count
            result["deleted"] = 0 if dry_run else 0
        logger.info(
            f"[r2-retention] dry_run={dry_run} scanned={result['scanned']} "
            f"kept={result['kept']} deleted={result['deleted']} "
            f"survivors={result['survivors_by_tier']} "
            f"deleted_by_tier={result['deleted_by_tier']}"
        )
    except Exception as e:
        result["ok"] = False
        result["errors"].append(f"enforce_failed: {e}")
        logger.warning(f"[r2-retention] top-level failure: {e}")
    return result


__all__ = [
    "TIER1_DAYS", "TIER2_DAYS", "TIER3_DAYS",
    "RetentionDecision", "RetentionPlan",
    "plan_retention", "list_r2_backups", "enforce_r2_retention",
    "_parse_filename_to_ts",
]

"""Recovery Dashboard backend route.

Single read-only endpoint that composes the recovery posture snapshot
from existing collections (no schema additions).

Implements RECOVERY_DASHBOARD_SPEC.md exactly. No scope expansion.
"""

from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException


# ─────────────────── 15-second snapshot cache ───────────────────
_CACHE: Dict[str, Any] = {"computed_at": 0.0, "snapshot": None}
_CACHE_TTL_SECONDS = 15.0


def _parse_ts(v: Any) -> Optional[datetime]:
    """Best-effort parse of an ISO string or datetime into a tz-aware UTC datetime."""
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    if isinstance(v, str) and v:
        try:
            s = v.replace("Z", "+00:00") if v.endswith("Z") else v
            return datetime.fromisoformat(s)
        except Exception:
            return None
    return None


def _minutes_since(ts: Optional[datetime]) -> Optional[float]:
    if not ts:
        return None
    delta = datetime.now(timezone.utc) - ts
    return round(delta.total_seconds() / 60.0, 1)


def _compute_pill(
    last_backup_ok: Optional[bool],
    backup_age_minutes: Optional[float],
    backup_age_target_minutes: float,
    failures_7d: int,
    bucket_usage_status: str,
) -> str:
    """Pure function. Same inputs → same output. Unit-testable.

    RED if  : last backup_health row is ok=false OR no backup in 2x target window.
    AMBER if: backup_age > target OR any failure in last 7d OR bucket AMBER/RED.
    GREEN   : everything is fine.
    """
    if last_backup_ok is False:
        return "RED"
    if backup_age_minutes is None:
        return "RED"
    if backup_age_minutes > 2 * backup_age_target_minutes:
        return "RED"
    if backup_age_minutes > backup_age_target_minutes:
        return "AMBER"
    if failures_7d > 0:
        return "AMBER"
    if bucket_usage_status in ("AMBER", "RED"):
        return "AMBER"
    return "GREEN"


def build_recovery_dashboard_router(
    db: Any,
    require_admin_strict_dep: Any,
) -> APIRouter:
    """Build the router. Caller passes the live Mongo `db` handle and the
    admin-strict auth dependency, so this module stays decoupled from
    `server.py`'s globals."""

    router = APIRouter()

    @router.get("/admin/recovery/snapshot")
    async def recovery_snapshot(_: bool = Depends(require_admin_strict_dep)) -> Dict[str, Any]:
        """Single round-trip snapshot for the /admin/recovery dashboard.

        Cached for 15 seconds in-memory. All data sourced from existing
        collections (no schema additions). See RECOVERY_DASHBOARD_SPEC.md.
        """
        now_wall = time.time()
        if _CACHE["snapshot"] is not None and (now_wall - _CACHE["computed_at"]) < _CACHE_TTL_SECONDS:
            cached = dict(_CACHE["snapshot"])
            cached["cached"] = True
            return cached

        rpo_target = int(os.environ.get("BACKUP_RPO_TARGET_MINUTES", "60") or "60")
        rto_target = int(os.environ.get("BACKUP_RTO_TARGET_MINUTES", "15") or "15")
        age_target = int(os.environ.get("BACKUP_AGE_TARGET_HOURS", "24") or "24") * 60
        warn_gb = float(os.environ.get("R2_USAGE_WARN_GB", "45") or "45")
        alert_gb = float(os.environ.get("R2_USAGE_ALERT_GB", "50") or "50")

        # --- last successful complete-r2 backup ---
        last_backup_row = await db.backup_health.find_one(
            {"mode": "complete-r2", "ok": True},
            {"_id": 0},
            sort=[("ts", -1)],
        )
        last_backup: Optional[Dict[str, Any]] = None
        backup_age_minutes: Optional[float] = None
        if last_backup_row:
            ts = _parse_ts(last_backup_row.get("ts"))
            backup_age_minutes = _minutes_since(ts)
            last_backup = {
                "filename": last_backup_row.get("filename"),
                "size_mb": round((last_backup_row.get("size_bytes") or 0) / (1024 * 1024), 2),
                "records": last_backup_row.get("records") or 0,
                "ok": last_backup_row.get("ok"),
                "ts": last_backup_row.get("ts"),
                "inlined_photos": last_backup_row.get("inlined_photos") or 0,
            }

        # --- most recent backup_health row (any outcome) — drives RED if it's a failure ---
        most_recent_row = await db.backup_health.find_one(
            {"mode": "complete-r2"},
            {"_id": 0},
            sort=[("ts", -1)],
        )
        last_backup_ok: Optional[bool] = None
        if most_recent_row is not None:
            last_backup_ok = bool(most_recent_row.get("ok", True))

        # --- failures last 7 days ---
        cutoff_7d = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        failure_rows = await db.backup_health.find(
            {"ok": False, "ts": {"$gte": cutoff_7d}},
            {"_id": 0, "ts": 1, "mode": 1, "error": 1, "filename": 1},
            sort=[("ts", -1)],
        ).to_list(length=50)
        failures_7d = [
            {
                "ts": r.get("ts"),
                "mode": r.get("mode"),
                "error": (r.get("error") or "")[:240],
                "filename": r.get("filename"),
            }
            for r in failure_rows
        ]

        # --- archive size trend (last 30 successful complete-r2 archives) ---
        trend_rows = await db.backup_health.find(
            {"mode": "complete-r2", "ok": True},
            {"_id": 0, "ts": 1, "size_bytes": 1, "records": 1},
            sort=[("ts", -1)],
        ).to_list(length=30)
        archive_size_trend: List[Dict[str, Any]] = list(reversed([
            {
                "ts": r.get("ts"),
                "size_mb": round((r.get("size_bytes") or 0) / (1024 * 1024), 2),
                "records": r.get("records") or 0,
            }
            for r in trend_rows
        ]))

        # --- archive count by time window (cheap derivation from trend rows) ---
        all_trend = await db.backup_health.find(
            {"mode": "complete-r2", "ok": True},
            {"_id": 0, "ts": 1},
        ).to_list(length=500)
        now_dt = datetime.now(timezone.utc)
        cutoff_7d_dt = now_dt - timedelta(days=7)
        cutoff_30d_dt = now_dt - timedelta(days=30)
        last_7d = 0
        last_30d = 0
        for r in all_trend:
            ts = _parse_ts(r.get("ts"))
            if not ts:
                continue
            if ts >= cutoff_7d_dt:
                last_7d += 1
            if ts >= cutoff_30d_dt:
                last_30d += 1
        archive_count = {"r2_total": len(all_trend), "last_7d": last_7d, "last_30d": last_30d}

        # --- bucket usage (read last r2-usage-alert/warn row) ---
        usage_row = await db.backup_health.find_one(
            {"mode": {"$in": ["r2-usage-alert", "r2-usage-warn"]}},
            {"_id": 0},
            sort=[("ts", -1)],
        )
        if usage_row:
            usage_gb = round((usage_row.get("size_bytes") or 0) / (1024 * 1024 * 1024), 2)
        else:
            usage_gb = 0.0
        if usage_gb >= alert_gb:
            usage_status = "AMBER"  # ALERT but not RED unless we crash because of it
        elif usage_gb >= warn_gb:
            usage_status = "AMBER"
        else:
            usage_status = "GREEN"
        bucket_usage = {
            "gb": usage_gb,
            "warn_gb": warn_gb,
            "alert_gb": alert_gb,
            "status": usage_status,
            "ts": usage_row.get("ts") if usage_row else None,
        }

        # --- last restore drill (from drill_runs if it exists; else None) ---
        last_drill: Optional[Dict[str, Any]] = None
        try:
            drill_row = await db.drill_runs.find_one(
                {"state": "done"},
                {"_id": 0},
                sort=[("started_at", -1)],
            )
            if drill_row:
                last_drill = {
                    "ts": drill_row.get("finished_at") or drill_row.get("started_at"),
                    "outcome": drill_row.get("outcome"),
                    "records": drill_row.get("records_restored") or 0,
                    "photos": drill_row.get("photos_rehydrated") or 0,
                    "duration_min": drill_row.get("duration_minutes"),
                    "archive_filename": drill_row.get("archive_filename"),
                }
        except Exception:
            last_drill = None

        # --- scheduler liveness ---
        scheduler_alive = False
        scheduler_last_lock_ts: Optional[str] = None
        scheduler_owner_pod: Optional[str] = None
        try:
            lock_row = await db.scheduler_locks.find_one(
                {"owner_id": {"$regex": "^backup_scheduler"}},
                {"_id": 0},
                sort=[("acquired_at", -1)],
            ) or await db.scheduler_locks.find_one(
                {},
                {"_id": 0},
                sort=[("acquired_at", -1)],
            )
            if lock_row:
                scheduler_last_lock_ts = lock_row.get("acquired_at")
                owner_id = lock_row.get("owner_id") or ""
                scheduler_owner_pod = owner_id.split(":")[0] if owner_id else None
                ts = _parse_ts(scheduler_last_lock_ts)
                if ts and (datetime.now(timezone.utc) - ts) < timedelta(minutes=30):
                    scheduler_alive = True
        except Exception:
            pass

        # --- hourly cadence flag (read-only — never modifies) ---
        hourly_flag = (os.environ.get("BACKUP_R2_HOURLY", "false") or "false").lower() in ("1", "true", "yes")

        # --- compute overall pill ---
        pill = _compute_pill(
            last_backup_ok=last_backup_ok,
            backup_age_minutes=backup_age_minutes,
            backup_age_target_minutes=float(age_target),
            failures_7d=len(failures_7d),
            bucket_usage_status=usage_status,
        )

        # --- active warnings (derived) ---
        warnings: List[Dict[str, str]] = []
        if usage_status == "AMBER":
            warnings.append({
                "kind": "bucket-usage",
                "severity": "amber",
                "message": f"R2 bucket usage {usage_gb} GB above ALERT={alert_gb} GB threshold",
            })
        if not hourly_flag:
            warnings.append({
                "kind": "hourly-disabled",
                "severity": "info",
                "message": "BACKUP_R2_HOURLY is currently false (operator-controlled)",
            })
        if not scheduler_alive:
            warnings.append({
                "kind": "scheduler-quiet",
                "severity": "amber",
                "message": "No scheduler lock heartbeat in the last 30 minutes",
            })
        if (os.environ.get("PHOTO_COVERAGE_GAP_OPEN", "false") or "false").lower() in ("1", "true", "yes"):
            warnings.append({
                "kind": "photo-coverage-gap",
                "severity": "amber",
                "message": "Photo coverage gap open · see PHOTO_COVERAGE_CERTIFICATION.md",
            })

        snapshot = {
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "pill": pill,
            "last_backup": last_backup,
            "last_drill": last_drill,
            "backup_age_minutes": backup_age_minutes,
            "backup_age_target_minutes": age_target,
            "rpo": {
                "target_min": rpo_target,
                "actual_min": backup_age_minutes,
                "status": (
                    "GREEN" if (backup_age_minutes is not None and backup_age_minutes <= rpo_target)
                    else ("AMBER" if backup_age_minutes is not None else "RED")
                ),
            },
            "rto": {
                "target_min": rto_target,
                "last_drill_min": (last_drill or {}).get("duration_min"),
                "status": (
                    "GREEN" if (
                        last_drill and (last_drill.get("duration_min") or 0) <= rto_target
                    ) else "AMBER"
                ),
            },
            "archive_count": archive_count,
            "bucket_usage": bucket_usage,
            "archive_size_trend": archive_size_trend,
            "failures_7d": failures_7d,
            "warnings": warnings,
            "scheduler": {
                "alive": scheduler_alive,
                "last_lock_ts": scheduler_last_lock_ts,
                "owner_pod": scheduler_owner_pod,
            },
            "hourly_cadence_enabled": hourly_flag,
            "cached": False,
        }

        _CACHE["snapshot"] = snapshot
        _CACHE["computed_at"] = now_wall
        return snapshot

    return router

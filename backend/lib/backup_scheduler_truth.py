"""Shared scheduler truth helpers extracted from server.py."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional

from lib.hourly_activation import build_hourly_activation_state


def build_default_scheduler_state() -> Dict[str, Any]:
    return {
        "alive": False,
        "armed_at": None,
        "last_tick_ts": None,
        "in_progress": False,
        "last_attempt_started_at": None,
        "last_attempt_outcome": None,
        "last_run_for_hour": {},
        "failed_attempts": {},
        "resurrect_count": 0,
        "last_resurrect_ts": None,
        "r2_hourly_requested": False,
        "r2_hourly_effective": False,
        "r2_hourly_locked_off": True,
        "hourly_cadence_enabled": False,
        "activation_blockers": [],
        "activation_status": "DISABLED BY CONFIGURATION",
        "activation_environment": "unknown",
        "last_activation_evaluated_at": None,
        "next_eligible_hourly_slot": None,
        "backup_runtime": {
            "stale_marked": 0,
            "active_jobs": [],
            "overlap": {
                "backup_active": False,
                "restore_active": False,
                "active_backups": [],
                "active_restores": [],
                "overlap_blocked": False,
            },
            "recent_complete_jobs": [],
        },
    }


def build_default_retention_policy() -> Dict[str, Any]:
    return {
        "architecture": "selected_surviving_hourly_archives",
        "hourly_hours": 72,
        "daily_days": 30,
        "weekly_days": 90,
        "monthly_months": 12,
    }


def backup_scheduler_healthy(runtime_state: Optional[Dict[str, Any]] = None) -> bool:
    state = runtime_state or {}
    if not state.get("alive"):
        return False
    explicit_health = state.get("is_healthy")
    if explicit_health is False:
        return False
    if explicit_health is True:
        return True
    last_tick = state.get("last_tick_ts")
    last_lock = state.get("last_lock_ts") or state.get("evidence_ts")
    if not last_tick:
        if not last_lock:
            return False
        try:
            dt = datetime.fromisoformat(str(last_lock).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - dt) <= timedelta(minutes=10)
        except Exception:
            return False
    try:
        dt = datetime.fromisoformat(str(last_tick).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt) <= timedelta(minutes=10)
    except Exception:
        return False


def retention_policy_state(retention_policy: Dict[str, Any]) -> Dict[str, Any]:
    policy = dict(retention_policy or {})
    valid = bool(
        policy.get("hourly_hours") == 72
        and policy.get("daily_days") == 30
        and policy.get("weekly_days") == 90
        and policy.get("monthly_months") == 12
        and policy.get("architecture") == "selected_surviving_hourly_archives"
    )
    return {
        "valid": valid,
        "reason": "approved_tiered_retention" if valid else "retention_policy_invalid",
        "policy": policy,
    }


async def build_hourly_activation_snapshot(
    db,
    *,
    runtime_state: Optional[Dict[str, Any]],
    scheduler_state: Dict[str, Any],
    retention_policy: Dict[str, Any],
    collect_runtime_state: Callable[[Any], Any],
    canonical_scheduler_builder: Callable[[Any, Dict[str, Any]], Any],
    list_stale_jobs: Callable[[Any], Any],
    stale_lock_present: Callable[[Any], Any],
    persistence_available: Callable[[Any], Any],
    latest_complete_backup_hint: Callable[[Any], Any],
    backup_resource_preflight: Callable[..., Dict[str, Any]],
    canonical_app_env: Callable[[], str],
) -> Dict[str, Any]:
    runtime_state = runtime_state or await collect_runtime_state(db)
    if not runtime_state.get("alive") or runtime_state.get("is_healthy") is None:
        try:
            canonical_scheduler = await canonical_scheduler_builder(db, runtime_state)
            runtime_state = {
                **runtime_state,
                "alive": canonical_scheduler.get("alive"),
                "is_healthy": canonical_scheduler.get("is_healthy"),
                "evidence_ts": canonical_scheduler.get("evidence_ts"),
                "last_lock_ts": canonical_scheduler.get("last_lock_ts"),
                "last_tick_ts": canonical_scheduler.get("last_tick_ts"),
            }
        except Exception:
            pass
    overlap = runtime_state.get("overlap") or {}
    stale_jobs = await list_stale_jobs(db)
    stale_lock = await stale_lock_present(db)
    persistence_ok = await persistence_available(db)
    retention = retention_policy_state(retention_policy)
    latest_hint = await latest_complete_backup_hint(db)
    preflight = backup_resource_preflight(archive_size_bytes=latest_hint.get("size_bytes"))
    active_job = None
    active_jobs = runtime_state.get("active_jobs") or []
    if active_jobs:
        current = active_jobs[0]
        active_job = {
            "job_id": current.get("job_id"),
            "kind": current.get("kind"),
            "state": current.get("state"),
            "heartbeat_at": current.get("heartbeat_at"),
        }
    reclaimable_stale_jobs = [
        job for job in stale_jobs
        if str(job.get("failure_reason") or "") == "stale_job_recovered"
    ]
    state = build_hourly_activation_state(
        requested_raw=os.environ.get("BACKUP_R2_HOURLY"),
        environment=canonical_app_env().lower(),
        scheduler_healthy=backup_scheduler_healthy(runtime_state),
        persistence_available=persistence_ok,
        backup_active=bool(overlap.get("backup_active")),
        restore_active=bool(overlap.get("restore_active")),
        stale_job_count=len(stale_jobs),
        reclaimable_stale_job_count=len(reclaimable_stale_jobs),
        stale_lock_present=stale_lock,
        resource_preflight=preflight,
        r2_configured=bool(os.environ.get("S3_BUCKET") and os.environ.get("S3_ENDPOINT_URL")),
        retention_valid=bool(retention.get("valid")),
        retention_reason=str(retention.get("reason") or "retention_unknown"),
        current_active_job=active_job,
    )
    state["retention_state"] = retention
    state["stale_job_count"] = len(stale_jobs)
    state["reclaimable_stale_job_count"] = len(reclaimable_stale_jobs)
    state["stale_lock_present"] = stale_lock
    state["persistence_available"] = persistence_ok
    scheduler_state["r2_hourly_requested"] = state["r2_hourly_requested"]
    scheduler_state["r2_hourly_effective"] = state["r2_hourly_effective"]
    scheduler_state["r2_hourly_locked_off"] = state["r2_hourly_locked_off"]
    scheduler_state["hourly_cadence_enabled"] = state["hourly_cadence_enabled"]
    scheduler_state["activation_blockers"] = state["activation_blockers"]
    scheduler_state["activation_status"] = state["activation_status"]
    scheduler_state["activation_environment"] = state["environment"]
    scheduler_state["last_activation_evaluated_at"] = state["last_evaluated_at"]
    scheduler_state["next_eligible_hourly_slot"] = state["next_eligible_hourly_slot"]
    return state
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple


TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"", "0", "false", "no", "off"}


def parse_requested_hourly(raw: Any) -> Tuple[bool, Optional[str]]:
    if raw is None:
        return False, None
    text = str(raw).strip().lower()
    if text in TRUE_VALUES:
        return True, None
    if text in FALSE_VALUES:
        return False, None
    return False, f"invalid_boolean:{raw}"


def next_hourly_slot_iso(moment: Optional[datetime] = None) -> str:
    now = moment or datetime.now(timezone.utc)
    slot = now.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return slot.isoformat()


def classify_capacity_state(
    *,
    total_bytes: Optional[int],
    warn_gb: float,
    alert_gb: float,
    probe_state: str,
    as_of: Optional[str] = None,
) -> Dict[str, Any]:
    if probe_state != "ok" or total_bytes is None:
        status = "RED" if probe_state == "failed" else "AMBER"
        return {
            "status": status,
            "probe_state": probe_state,
            "total_bytes": total_bytes,
            "gb": round((total_bytes or 0) / (1024 ** 3), 2) if total_bytes is not None else None,
            "warn_gb": warn_gb,
            "alert_gb": alert_gb,
            "reason": (
                "capacity_probe_failed" if probe_state == "failed" else "capacity_probe_missing"
            ),
            "as_of": as_of,
        }

    gb = round(total_bytes / (1024 ** 3), 2)
    if gb >= alert_gb:
        status = "RED"
        reason = "r2-usage-alert"
    elif gb >= warn_gb:
        status = "AMBER"
        reason = "r2-usage-warn"
    else:
        status = "GREEN"
        reason = "healthy"
    return {
        "status": status,
        "probe_state": "ok",
        "total_bytes": int(total_bytes),
        "gb": gb,
        "warn_gb": warn_gb,
        "alert_gb": alert_gb,
        "reason": reason,
        "as_of": as_of,
    }


def build_activation_blocker(code: str, *, category: str, detail: str, blocking: bool = True) -> Dict[str, Any]:
    return {
        "code": code,
        "category": category,
        "detail": detail,
        "blocking": bool(blocking),
    }


def build_hourly_activation_state(
    *,
    requested_raw: Any,
    environment: str,
    scheduler_healthy: bool,
    persistence_available: bool,
    backup_active: bool,
    restore_active: bool,
    stale_job_count: int,
    reclaimable_stale_job_count: int = 0,
    stale_lock_present: bool,
    resource_preflight: Optional[Dict[str, Any]],
    r2_configured: bool,
    retention_valid: bool,
    retention_reason: str,
    current_active_job: Optional[Dict[str, Any]] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    moment = now or datetime.now(timezone.utc)
    requested, parse_error = parse_requested_hourly(requested_raw)
    blockers: List[Dict[str, Any]] = []
    blocking_stale_job_count = max(int(stale_job_count or 0) - int(reclaimable_stale_job_count or 0), 0)

    if parse_error:
        blockers.append(
            build_activation_blocker(
                "invalid_hourly_configuration",
                category="configuration",
                detail="BACKUP_R2_HOURLY is malformed and was forced OFF",
            )
        )
    if environment != "production":
        blockers.append(
            build_activation_blocker(
                "environment_not_production",
                category="environment",
                detail=f"Hourly complete R2 is blocked in environment={environment or 'unknown'}",
            )
        )
    if not scheduler_healthy:
        blockers.append(
            build_activation_blocker(
                "scheduler_unhealthy",
                category="safety_guard",
                detail="Backup scheduler is not currently healthy",
            )
        )
    if not persistence_available:
        blockers.append(
            build_activation_blocker(
                "backup_job_persistence_unavailable",
                category="safety_guard",
                detail="Backup job persistence is unavailable",
            )
        )
    if backup_active:
        blockers.append(
            build_activation_blocker(
                "active_backup_present",
                category="safety_guard",
                detail="Another backup job is currently active",
            )
        )
    if restore_active:
        blockers.append(
            build_activation_blocker(
                "active_restore_present",
                category="safety_guard",
                detail="A restore job is currently active",
            )
        )
    if blocking_stale_job_count > 0:
        blockers.append(
            build_activation_blocker(
                "stale_backup_job_present",
                category="stale",
                detail=f"{blocking_stale_job_count} stale backup/restore job(s) require operator review",
            )
        )
    if stale_lock_present:
        blockers.append(
            build_activation_blocker(
                "stale_scheduler_lock_present",
                category="stale",
                detail="A stale scheduler lock is still present",
            )
        )
    if not r2_configured:
        blockers.append(
            build_activation_blocker(
                "r2_not_configured",
                category="configuration",
                detail="R2 configuration is incomplete or unavailable",
            )
        )
    if not retention_valid:
        blockers.append(
            build_activation_blocker(
                "retention_invalid",
                category="configuration",
                detail=retention_reason or "Retention policy validation failed",
            )
        )
    preflight = resource_preflight or {"ok": False, "reasons": ["resource_preflight_missing"]}
    if not bool(preflight.get("ok")):
        blockers.append(
            build_activation_blocker(
                "resource_preflight_failed",
                category="safety_guard",
                detail=", ".join(preflight.get("reasons") or ["resource_preflight_failed"]),
            )
        )

    effective = bool(requested and not blockers and environment == "production")
    locked_off = bool(requested and not effective)
    blocker_categories = {b["category"] for b in blockers}
    if effective:
        status = "ACTIVE"
    elif "stale" in blocker_categories:
        status = "STALE"
    elif parse_error:
        status = "FAILED"
    elif requested and environment != "production":
        status = "BLOCKED BY ENVIRONMENT"
    elif requested and blockers:
        status = "BLOCKED BY SAFETY GUARD"
    elif environment == "production" and not blockers:
        status = "READY BUT DISABLED"
    else:
        status = "DISABLED BY CONFIGURATION"

    return {
        "r2_hourly_requested": bool(requested),
        "r2_hourly_effective": bool(effective),
        "r2_hourly_locked_off": bool(locked_off),
        "hourly_cadence_enabled": bool(effective),
        "activation_blockers": blockers,
        "activation_status": status,
        "environment": environment or "unknown",
        "last_evaluated_at": moment.isoformat(),
        "next_eligible_hourly_slot": next_hourly_slot_iso(moment),
        "current_active_job": current_active_job,
        "resource_preflight": preflight,
        "retention_valid": bool(retention_valid),
        "retention_reason": retention_reason,
        "blocking_stale_job_count": blocking_stale_job_count,
        "reclaimable_stale_job_count": max(int(reclaimable_stale_job_count or 0), 0),
    }

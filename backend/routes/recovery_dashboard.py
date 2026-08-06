"""Recovery Dashboard backend route.

Single read-only endpoint that composes the recovery posture snapshot
from existing collections (no schema additions).

Implements RECOVERY_DASHBOARD_SPEC.md exactly. No scope expansion.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from lib.archive_lineage import build_canonical_archive_lineage, consumer_freshness_status, public_archive_lineage_payload
from lib.backup_paths import configured_backup_prefix
from lib.config_recovery import build_configuration_recovery_package, build_configuration_recovery_summary
from lib.ots_truth import CORRELATED, canonical_truth_card, compatibility_projection, projected_truth_relationship, public_ots_projection


logger = logging.getLogger(__name__)

SCHEDULER_HEARTBEAT_WINDOW_MINUTES = 30
SCHEDULER_BACKUP_FALLBACK_WINDOW_MINUTES = 60


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


def _scheduler_state_is_alive(state: Any, *, max_age_minutes: int = 30) -> bool:
    """Interpret the canonical in-process backup scheduler heartbeat."""
    if not isinstance(state, dict):
        return False
    ts = _parse_ts(state.get("last_tick_ts"))
    if not ts:
        return False
    return (datetime.now(timezone.utc) - ts) < timedelta(minutes=max_age_minutes)


def canonical_scheduler_snapshot(
    state: Any,
    *,
    max_age_minutes: int = SCHEDULER_HEARTBEAT_WINDOW_MINUTES,
    backup_fallback_ts: Any = None,
    backup_fallback_max_age_minutes: int = SCHEDULER_BACKUP_FALLBACK_WINDOW_MINUTES,
    lock_row: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Single source of truth for scheduler liveness / health."""
    now = datetime.now(timezone.utc)
    if not isinstance(state, dict):
        state = {}

    tick = state.get("last_tick_ts")
    ts = _parse_ts(tick)
    seconds_since_last_tick = None
    if ts:
        seconds_since_last_tick = (now - ts).total_seconds()

    lock_ts_raw = None
    owner_pod = None
    if isinstance(lock_row, dict):
        lock_ts_raw = lock_row.get("expires_at") or lock_row.get("acquired_at")
        owner_id = lock_row.get("owner_id") or ""
        owner_pod = owner_id.split(":")[0] if owner_id else None
    lock_ts = _parse_ts(lock_ts_raw)
    backup_dt = _parse_ts(backup_fallback_ts)

    snapshot = {
        "alive": False,
        "is_healthy": False,
        "last_tick_ts": tick,
        "seconds_since_last_tick": seconds_since_last_tick,
        "signal_source": "none",
        "reason_code": "scheduler_signal_missing",
        "evidence_ts": None,
        "last_lock_ts": lock_ts_raw,
        "owner_pod": owner_pod,
        "heartbeat_window_minutes": max_age_minutes,
        "backup_fallback_window_minutes": backup_fallback_max_age_minutes,
    }

    if ts and (now - ts) < timedelta(minutes=max_age_minutes):
        snapshot.update({
            "alive": True,
            "is_healthy": True,
            "signal_source": "backup_scheduler_state",
            "reason_code": "scheduler_heartbeat_current",
            "evidence_ts": tick,
        })
        return snapshot

    if backup_dt and (now - backup_dt) < timedelta(minutes=backup_fallback_max_age_minutes):
        snapshot.update({
            "alive": True,
            "is_healthy": True,
            "signal_source": "recent_successful_backup",
            "reason_code": "recent_backup_fallback",
            "evidence_ts": backup_fallback_ts,
        })
        return snapshot

    if lock_ts and (now - lock_ts) < timedelta(minutes=max_age_minutes):
        snapshot.update({
            "alive": True,
            "is_healthy": True,
            "signal_source": "scheduler_lock_fallback",
            "reason_code": "scheduler_lock_current",
            "evidence_ts": lock_ts_raw,
        })
        return snapshot

    if ts:
        snapshot.update({
            "signal_source": "backup_scheduler_state",
            "reason_code": "scheduler_heartbeat_stale",
            "evidence_ts": tick,
        })
    elif backup_dt:
        snapshot.update({
            "signal_source": "recent_successful_backup",
            "reason_code": "recent_backup_stale",
            "evidence_ts": backup_fallback_ts,
        })
    elif lock_ts:
        snapshot.update({
            "signal_source": "scheduler_lock_fallback",
            "reason_code": "scheduler_lock_stale",
            "evidence_ts": lock_ts_raw,
        })

    return snapshot


async def build_canonical_scheduler_snapshot(
    db: Any,
    state: Any,
    *,
    max_age_minutes: int = SCHEDULER_HEARTBEAT_WINDOW_MINUTES,
    backup_fallback_max_age_minutes: int = SCHEDULER_BACKUP_FALLBACK_WINDOW_MINUTES,
    backup_fallback_ts: Any = None,
    lock_row: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if backup_fallback_ts is None:
        try:
            from server import _canonical_app_env, _canonical_db_name  # noqa: PLC0415
            lineage = await build_canonical_archive_lineage(
                db,
                current_env=_canonical_app_env(),
                current_db=_canonical_db_name(),
            )
            backup_fallback_ts = lineage.get("authoritative_recovery_point_time") or ((lineage.get("newest_observed_artifact") or {}).get("observed_time"))
        except Exception:
            backup_fallback_ts = None

    if lock_row is None:
        lock_row = await db.scheduler_locks.find_one(
            {"_id": "backup_scheduler"},
            {"_id": 0},
        ) or await db.scheduler_locks.find_one(
            {"owner_id": {"$regex": "^backup_scheduler"}},
            {"_id": 0},
            sort=[("acquired_at", -1)],
        ) or await db.scheduler_locks.find_one(
            {},
            {"_id": 0},
            sort=[("acquired_at", -1)],
        )

    return canonical_scheduler_snapshot(
        state,
        max_age_minutes=max_age_minutes,
        backup_fallback_ts=backup_fallback_ts,
        backup_fallback_max_age_minutes=backup_fallback_max_age_minutes,
        lock_row=lock_row,
    )


def _compute_pill(
    last_backup_ok: Optional[bool],
    backup_age_minutes: Optional[float],
    backup_age_target_minutes: float,
    failures_7d: int,
    bucket_usage_status: str,
) -> str:
    """Pure function. Same inputs → same output. Unit-testable.

    RED if  : last backup_health row is ok=false OR no backup in 2x target window OR bucket RED.
    AMBER if: backup_age > target OR bucket AMBER.
    GREEN   : everything is fine.
    """
    if last_backup_ok is False:
        return "RED"
    if backup_age_minutes is None:
        return "RED"
    # TRACK 27.05 · P0-3 · Bucket RED must escalate the overall pill to RED.
    if bucket_usage_status == "RED":
        return "RED"
    if backup_age_minutes > 2 * backup_age_target_minutes:
        return "RED"
    if backup_age_minutes > backup_age_target_minutes:
        return "AMBER"
    if bucket_usage_status == "AMBER":
        return "AMBER"
    return "GREEN"


# TRACK 27.05 · P0-1 · Query R2 directly for the newest complete backup.
# Returns the newest archive summary (filename, ts, size_mb) or None if
# R2 is unreachable / bucket empty. Never raises — the caller falls back
# to the local `backup_health` marker.
async def _newest_r2_backup_summary() -> Optional[Dict[str, Any]]:
    try:
        import photo_storage as ps  # noqa: PLC0415
    except Exception:
        return None
    if not ps.is_configured():
        return None
    try:
        client = ps._client()
        bucket = ps._bucket()
        # backups/auto-90d/ prefix — canonical Tier-1 target set by
        # `_run_complete_archive_to_r2` in server.py.
        page = await asyncio.to_thread(
            client.list_objects_v2,
            Bucket=bucket,
            Prefix=configured_backup_prefix(os.environ),
            MaxKeys=1000,
        )
        contents = page.get("Contents") or []
        # Pick the newest by LastModified.
        contents.sort(key=lambda o: o.get("LastModified") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        if not contents:
            return None
        top = contents[0]
        lm = top.get("LastModified")
        # LastModified is a tz-aware datetime from boto3.
        ts_iso = lm.astimezone(timezone.utc).isoformat() if isinstance(lm, datetime) else None
        return {
            "filename": (top.get("Key") or "").split("/")[-1],
            "ts": ts_iso,
            "size_mb": round((top.get("Size") or 0) / (1024 * 1024), 2),
        }
    except Exception:  # noqa: BLE001
        # Never raise — caller must degrade gracefully.
        import logging  # noqa: PLC0415
        logging.getLogger(__name__).warning(
            "[recovery-snapshot] R2 list_objects_v2 failed; falling back to local marker only",
            exc_info=True,
        )
        return None


# TRACK 27.05 · P0-4 · Disk preflight summary for the recovery snapshot.
# Never raises; degrades to `{"ok": True, "unavailable": true}` if the
# helper module fails to load.
def _disk_preflight_summary() -> Dict[str, Any]:
    try:
        from lib.disk_preflight import check_disk  # noqa: PLC0415
        st = check_disk()
        return {
            "ok": st.ok,
            "path": st.path,
            "free_bytes": st.free_bytes,
            "total_bytes": st.total_bytes,
            "percent_free": st.percent_free,
            "reason": st.reason,
        }
    except Exception:  # noqa: BLE001
        return {"ok": True, "unavailable": True}


def build_recovery_dashboard_router(
    db: Any,
    require_admin_strict_dep: Any,
) -> APIRouter:
    """Build the router. Caller passes the live Mongo `db` handle and the
    admin-strict auth dependency, so this module stays decoupled from
    `server.py`'s globals."""

    router = APIRouter()

    @router.get("/admin/recovery/configuration-recovery")
    async def configuration_recovery(_: bool = Depends(require_admin_strict_dep)) -> Dict[str, Any]:
        from server import _runtime_identity_bundle  # noqa: PLC0415

        package = build_configuration_recovery_package(
            env=os.environ,
            runtime_identity_bundle=_runtime_identity_bundle(),
        )
        return {"ok": True, "package": package}

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
        from server import _build_hourly_activation_state  # noqa: PLC0415

        rpo_target = int(os.environ.get("BACKUP_RPO_TARGET_MINUTES", "60") or "60")
        rto_target = int(os.environ.get("BACKUP_RTO_TARGET_MINUTES", "15") or "15")
        posture_target = int(os.environ.get("BACKUP_AGE_TARGET_HOURS", "24") or "24") * 60
        warn_gb = float(os.environ.get("R2_USAGE_WARN_GB", "350") or "350")
        alert_gb = float(os.environ.get("R2_USAGE_ALERT_GB", "450") or "450")
        from server import _canonical_app_env, _canonical_db_name  # noqa: PLC0415
        archive_lineage = await build_canonical_archive_lineage(
            db,
            current_env=_canonical_app_env(),
            current_db=_canonical_db_name(),
        )
        authoritative_artifact = archive_lineage.get("authoritative_artifact") or {}
        newest_observed = archive_lineage.get("newest_observed_artifact") or {}
        freshness = consumer_freshness_status(
            archive_lineage,
            threshold_minutes=float(rpo_target),
            warning_minutes=float(rpo_target),
        )

        last_backup: Optional[Dict[str, Any]] = None
        backup_age_minutes: Optional[float] = archive_lineage.get("freshness_age_minutes")
        if authoritative_artifact or newest_observed:
            display = authoritative_artifact or newest_observed
            last_backup = {
                "filename": display.get("filename"),
                "size_mb": round(((display.get("archive_size_bytes") or 0) / (1024 * 1024)), 2),
                "records": 0,
                "ok": bool(authoritative_artifact),
                "ts": display.get("authoritative_time") or display.get("observed_time"),
                "inlined_photos": 0,
                "source": "canonical_archive_lineage",
                "authoritative_time_source": display.get("authoritative_time_source"),
                "lineage_confidence": display.get("lineage_confidence"),
                "integrity_status": display.get("integrity_status"),
                "completeness_status": display.get("completeness_status"),
                "availability_status": display.get("availability_status"),
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
        if newest_observed and newest_observed.get("artifact_key") not in {None, ""}:
            archive_count["candidate_count"] = len(archive_lineage.get("all_candidates") or [])

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
            # TRACK 27.05 · P0-3 · usage over alert threshold IS RED,
            # not AMBER. Fixed classification bug from Track 27.04.
            usage_status = "RED"
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
        canonical_scheduler = {
            "alive": False,
            "is_healthy": False,
            "signal_source": "none",
            "reason_code": "scheduler_signal_missing",
            "evidence_ts": None,
            "last_lock_ts": None,
            "owner_pod": None,
            "seconds_since_last_tick": None,
            "heartbeat_window_minutes": SCHEDULER_HEARTBEAT_WINDOW_MINUTES,
            "backup_fallback_window_minutes": SCHEDULER_BACKUP_FALLBACK_WINDOW_MINUTES,
        }
        try:
            from server import _BACKUP_SCHEDULER_STATE  # noqa: PLC0415
            canonical_scheduler = await build_canonical_scheduler_snapshot(
                db,
                dict(_BACKUP_SCHEDULER_STATE or {}),
                backup_fallback_ts=archive_lineage.get("authoritative_recovery_point_time") or (newest_observed or {}).get("observed_time"),
            )
        except Exception:
            pass
        backup_runtime = {}
        try:
            from server import _collect_backup_runtime_state  # noqa: PLC0415
            backup_runtime = await _collect_backup_runtime_state(db)
        except Exception:
            backup_runtime = {}
        backup_runtime = {
            **backup_runtime,
            "alive": canonical_scheduler.get("alive"),
            "is_healthy": canonical_scheduler.get("is_healthy"),
            "evidence_ts": canonical_scheduler.get("evidence_ts"),
            "last_lock_ts": canonical_scheduler.get("last_lock_ts"),
            "last_tick_ts": canonical_scheduler.get("last_tick_ts"),
        }
        scheduler_alive = bool(canonical_scheduler.get("alive"))

        # --- hourly cadence flag (read-only — never modifies) ---
        hourly_flag = (os.environ.get("BACKUP_R2_HOURLY", "false") or "false").lower() in ("1", "true", "yes")

        hourly_activation = await _build_hourly_activation_state(db, runtime_state=backup_runtime)
        effective_backup_age_target_minutes = int(rpo_target)

        # --- compute overall pill ---
        pill = _compute_pill(
            last_backup_ok=last_backup_ok,
            backup_age_minutes=backup_age_minutes,
            backup_age_target_minutes=float(effective_backup_age_target_minutes),
            failures_7d=len(failures_7d),
            bucket_usage_status=usage_status,
        )
        if freshness.get("status") == "UNKNOWN":
            pill = "RED"

        # --- active warnings (derived) ---
        warnings: List[Dict[str, str]] = []
        if archive_lineage.get("degradation_reasons"):
            warnings.append({
                "kind": "archive-lineage",
                "severity": "amber" if authoritative_artifact else "red",
                "message": ", ".join(archive_lineage.get("degradation_reasons") or []),
            })
        if usage_status in {"AMBER", "RED"}:
            warnings.append({
                "kind": "bucket-usage",
                "severity": "amber" if usage_status == "AMBER" else "red",
                "message": (
                    f"R2 bucket usage {usage_gb} GB above "
                    f"{'WARN' if usage_status == 'AMBER' else 'ALERT'}="
                    f"{warn_gb if usage_status == 'AMBER' else alert_gb} GB threshold"
                ),
            })
        if freshness.get("status") == "UNKNOWN" or backup_age_minutes is None:
            rpo_status = "RED"
        elif backup_age_minutes <= effective_backup_age_target_minutes:
            rpo_status = "GREEN"
        elif backup_age_minutes <= (2 * effective_backup_age_target_minutes):
            rpo_status = "AMBER"
        else:
            rpo_status = "RED"
        if rpo_status == "RED":
            pill = "RED"
        elif rpo_status == "AMBER" and pill == "GREEN":
            pill = "AMBER"
        if hourly_activation.get("activation_status") != "ACTIVE":
            blocker_codes = [
                str((blocker or {}).get("code") or "").strip()
                for blocker in (hourly_activation.get("activation_blockers") or [])
                if (blocker or {}).get("code")
            ]
            blocker_suffix = f" ({', '.join(blocker_codes)})" if blocker_codes else ""
            warnings.append({
                "kind": "hourly-disabled",
                "severity": "red" if str(hourly_activation.get("activation_status") or "").upper() == "BLOCKED BY SAFETY GUARD" else "info",
                "message": f"Hourly complete R2 is {hourly_activation.get('activation_status')}{blocker_suffix}",
            })
        if not scheduler_alive:
            warnings.append({
                "kind": "scheduler-quiet",
                "severity": "amber",
                "message": (
                    f"No canonical scheduler heartbeat or recent scheduler activity within "
                    f"{canonical_scheduler.get('heartbeat_window_minutes', SCHEDULER_HEARTBEAT_WINDOW_MINUTES)} minutes"
                ),
            })
        if (backup_runtime.get("overlap") or {}).get("overlap_blocked"):
            warnings.append({
                "kind": "backup-restore-overlap",
                "severity": "amber",
                "message": "Backup and restore overlap detected or blocked by runtime guard",
            })
        if failures_7d:
            warnings.append({
                "kind": "historical-backup-failures",
                "severity": "info",
                "message": f"{len(failures_7d)} backup failure event(s) recorded in the last 7 days; current archive posture is evaluated separately.",
            })
        if (os.environ.get("PHOTO_COVERAGE_GAP_OPEN", "false") or "false").lower() in ("1", "true", "yes"):
            warnings.append({
                "kind": "photo-coverage-gap",
                "severity": "amber",
                "message": "Photo coverage gap open · see PHOTO_COVERAGE_CERTIFICATION.md",
            })

        from server import _runtime_identity_bundle  # noqa: PLC0415

        configuration_recovery_package = build_configuration_recovery_package(
            env=os.environ,
            runtime_identity_bundle=_runtime_identity_bundle(),
        )
        configuration_recovery_summary = build_configuration_recovery_summary(configuration_recovery_package)

        snapshot = {
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "pill": pill,
            "last_backup": last_backup,
            "last_drill": last_drill,
            "backup_age_minutes": backup_age_minutes,
            "backup_age_target_minutes": effective_backup_age_target_minutes,
            "archive_lineage": public_archive_lineage_payload(archive_lineage),
            "rpo": {
                "target_min": effective_backup_age_target_minutes,
                "actual_min": backup_age_minutes,
                "status": rpo_status,
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
            "configuration_recovery": configuration_recovery_summary,
            "scheduler": {
                "alive": scheduler_alive,
                "is_healthy": bool(canonical_scheduler.get("is_healthy")),
                "signal_source": canonical_scheduler.get("signal_source"),
                "reason_code": canonical_scheduler.get("reason_code"),
                "evidence_ts": canonical_scheduler.get("evidence_ts"),
                "last_lock_ts": canonical_scheduler.get("last_lock_ts"),
                "owner_pod": canonical_scheduler.get("owner_pod"),
                "seconds_since_last_tick": canonical_scheduler.get("seconds_since_last_tick"),
                "heartbeat_window_minutes": canonical_scheduler.get("heartbeat_window_minutes"),
                "backup_fallback_window_minutes": canonical_scheduler.get("backup_fallback_window_minutes"),
                "backup_runtime": backup_runtime,
            },
            # TRACK 27.05 · P0-4 · disk preflight state, surfaced so OCC
            # can display "storage will refuse new writes below N free".
            "disk_preflight": _disk_preflight_summary(),
            "hourly_cadence_enabled": bool(hourly_activation.get("hourly_cadence_enabled")),
            "hourly_activation": hourly_activation,
            "full_restore_status": {
                "status": "NOT YET EXERCISED",
                "message": "Full-platform restore remains not yet exercised.",
            },
            "production_only_evidence_status": {
                "status": "PREVIEW_ONLY" if hourly_activation.get("environment") != "production" else "PRODUCTION_REVIEW_REQUIRED",
                "message": (
                    "Preview evidence only; production activation has not been exercised."
                    if hourly_activation.get("environment") != "production"
                    else "Production activation remains gated on independent review."
                ),
            },
            "cached": False,
        }

        truth_card = canonical_truth_card(
            truth_subject="bcss_recovery_posture",
            canonical_owner="bcss_recovery_posture",
            truth_surface_id="bcss_recovery_posture",
            evidence_state="correlated",
            evidence_quality="CORRELATED",
            evidence_confidence="HIGH" if authoritative_artifact and last_drill else ("MEDIUM" if authoritative_artifact or newest_observed else "LOW"),
            truth_evaluation="VERIFIED" if pill == "GREEN" else ("DEGRADED" if pill == "AMBER" else "MISMATCH"),
            permitted_claim=CORRELATED,
            claim_ceiling=CORRELATED,
            claim_basis=["archive_lineage", "scheduler", "last_drill", "bucket_usage", "hourly_activation"],
            prohibited_claims=["VALIDATED", "CERTIFIED"],
            degradation_reasons=[warning.get("message") for warning in warnings],
            unknowns=[] if (authoritative_artifact or newest_observed) else ["No archive evidence is currently available."],
            contradictory_evidence=[],
            evidence_timestamp=archive_lineage.get("authoritative_recovery_point_time") or (newest_observed or {}).get("observed_time") or snapshot["computed_at"],
            evaluation_timestamp=snapshot["computed_at"],
            audit_reference="OTS-C5-RECOVERY-SNAPSHOT",
            evidence_required_to_raise_claim=["BCSS-R13 class-bound recovery certification", "full-platform restore exercise evidence"],
            notes=["Recovery Snapshot is an aggregator only.", "This surface does not certify recovery."],
        )
        compatibility = compatibility_projection(
            preserved_fields=17,
            deprecated_fields=0,
            new_fields=3,
            alias_fields=["pill"],
            breaking_changes=0,
        )
        snapshot["ots_truth"] = public_ots_projection(truth_card)
        snapshot["truth_relationship"] = projected_truth_relationship(
            surface_id="bcss_recovery_posture",
            card=truth_card,
            canonical_owner_route="/api/admin/recovery/snapshot",
            derivation_explanation="Recovery Snapshot is a bounded BCSS aggregator and may not imply recovery certification.",
            derived_status=truth_card["truth_evaluation"],
        )
        snapshot["compatibility"] = compatibility

        _CACHE["snapshot"] = snapshot
        _CACHE["computed_at"] = now_wall
        return snapshot

    return router

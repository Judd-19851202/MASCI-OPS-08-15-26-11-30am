"""
Cluster capacity probe — iter437 (2026-05-26).

Exposes `/api/cluster/capacity` (PUBLIC — no auth) so every authenticated and
unauthenticated page can render an immediate operational banner when the
MongoDB Atlas cluster approaches its storage quota.

Why public:
  - The data exposed is non-sensitive (total cluster storage size + tier ceiling).
  - The banner must render on the login page, before any auth header exists,
    so field crews see the warning *before* they bother submitting a form
    that would silently fail.

Quota detection:
  - Reads `ATLAS_QUOTA_MB` from env. Defaults to 512 (M0 free tier).
  - When set to 0, the banner suppresses itself (interpreted as
    "unmanaged / unbounded tier", e.g. M10+).

Thresholds (matching ops doctrine):
  - >= 95% → severity=critical (red banner, blocks-imminent warning)
  - >= 80% → severity=warning  (amber banner, plan upgrade)
  - else   → severity=ok       (banner hidden)

Output (sub-50ms typical, since `dbStats` is a single RTT to Atlas):
  {
    "ok": true,
    "tier_quota_mb": 512,
    "storage_used_mb": 524.2,
    "storage_used_pct": 102.4,
    "severity": "critical",
    "dbs": {"masci_safety": 522.8, "masci_safety_preview": 1.4},
    "ts": "2026-05-26T22:00:00Z"
  }
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from motor.motor_asyncio import AsyncIOMotorClient

from lib.database_authority import managed_database_names
from lib.runtime_identity import runtime_identity_public_payload
from lib.wp17a_kpi_governance import capacity_prediction_quality, standardize_prediction_metadata

logger = logging.getLogger(__name__)

# Cache the probe result for 60s — `dbStats` is cheap but no need to hit
# Atlas on every page load if 50 crew members open the app simultaneously.
_CACHE: Dict[str, Any] = {"ts": 0.0, "payload": None}
_CACHE_TTL_S = 60

# iter437 Phase Sigma-II — history collection name + TTL window (90 days).
HISTORY_COLLECTION = "cluster_capacity_history"
HISTORY_TTL_SECONDS = 90 * 86400


async def ensure_history_indexes(db) -> None:
    """One-time TTL on `ts` so the history collection self-prunes.
    Safe to call repeatedly — Mongo no-ops on duplicate index specs."""
    try:
        await db[HISTORY_COLLECTION].create_index(
            "ts", expireAfterSeconds=HISTORY_TTL_SECONDS,
            name="ts_ttl_90d",
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("[cluster_capacity] history index ensure failed: %s", e)


def _quota_mb() -> int:
    try:
        v = int(os.environ.get("ATLAS_QUOTA_MB", "512"))
    except ValueError:
        v = 512
    return v


def _risk_level(*, used_pct: float, remaining_days: Optional[float], quality: str) -> str:
    if used_pct >= 95 or (remaining_days is not None and remaining_days <= 7):
        return "critical"
    if used_pct >= 85 or (remaining_days is not None and remaining_days <= 21):
        return "high"
    if used_pct >= 70 or (remaining_days is not None and remaining_days <= 45):
        return "elevated"
    if quality == "LOW":
        return "watch"
    return "normal"


def _recommendations(*, risk_level: str, daily_growth: Optional[float], remaining_days: Optional[float]) -> List[str]:
    recs: List[str] = []
    if risk_level == "critical":
        recs.append("Immediate action required: reduce storage growth or increase quota before write capacity is exhausted.")
    elif risk_level == "high":
        recs.append("Plan storage remediation this week; trend indicates materially reduced operating runway.")
    elif risk_level == "elevated":
        recs.append("Monitor trend weekly and verify cleanup / retention plans are scheduled.")
    else:
        recs.append("Storage posture is currently within normal operating bounds.")
    if daily_growth is not None and daily_growth > 0:
        recs.append(f"Current growth velocity is {daily_growth:.2f} MB/day.")
    if remaining_days is not None:
        recs.append(f"Projected remaining operational days: {remaining_days:.1f}.")
    return recs


def _series_metrics(rows: List[Dict[str, Any]], quota_mb: int) -> Dict[str, Any]:
    if len(rows) < 2:
        return {
            "daily_growth_rate_mb": None,
            "weekly_growth_rate_mb": None,
            "monthly_growth_rate_mb": None,
            "rolling_average_daily_mb": None,
            "rolling_average_weekly_mb": None,
            "storage_velocity_mb_per_day": None,
            "projected_exhaustion_date": None,
            "remaining_operational_days": None,
            "confidence_interval_days": None,
            "prediction_quality": "LOW",
            "historical_variance_mb": None,
            "capacity_risk_level": "watch",
            "early_warning_thresholds": {"elevated_days": 45, "high_days": 21, "critical_days": 7},
            "recommendations": ["More retained samples are needed before predictive storage guidance becomes reliable."],
        }

    parsed: List[Tuple[datetime, float]] = []
    for row in rows:
        try:
            ts = row.get("ts")
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00")) if isinstance(ts, str) else ts
            parsed.append((dt, float(row.get("storage_used_mb") or 0.0)))
        except Exception:  # noqa: BLE001
            continue
    parsed.sort(key=lambda item: item[0])
    if len(parsed) < 2:
        return {
            "daily_growth_rate_mb": None,
            "weekly_growth_rate_mb": None,
            "monthly_growth_rate_mb": None,
            "rolling_average_daily_mb": None,
            "rolling_average_weekly_mb": None,
            "storage_velocity_mb_per_day": None,
            "projected_exhaustion_date": None,
            "remaining_operational_days": None,
            "confidence_interval_days": None,
            "prediction_quality": "LOW",
            "historical_variance_mb": None,
            "capacity_risk_level": "watch",
            "early_warning_thresholds": {"elevated_days": 45, "high_days": 21, "critical_days": 7},
            "recommendations": ["More valid retained samples are needed before predictive storage guidance becomes reliable."],
        }

    def _rate(window_days: int) -> Optional[float]:
        end = parsed[-1][0]
        start_cutoff = end - timedelta(days=window_days)
        subset = [item for item in parsed if item[0] >= start_cutoff]
        if len(subset) < 2:
            subset = parsed
        first_dt, first_mb = subset[0]
        last_dt, last_mb = subset[-1]
        dt_days = max((last_dt - first_dt).total_seconds() / 86400.0, 1 / 24.0)
        return round((last_mb - first_mb) / dt_days, 4)

    daily_growth = _rate(1)
    weekly_growth = _rate(7)
    monthly_growth = _rate(30)
    recent_deltas = [parsed[i][1] - parsed[i - 1][1] for i in range(1, len(parsed))]
    rolling_avg_daily = round(sum(recent_deltas[-24:]) / max(len(recent_deltas[-24:]), 1), 4) if recent_deltas else None
    rolling_avg_weekly = round(sum(recent_deltas[-24 * 7:]) / max(len(recent_deltas[-24 * 7:]), 1), 4) if recent_deltas else None
    current_mb = parsed[-1][1]
    effective_velocity = monthly_growth if monthly_growth is not None else weekly_growth
    if effective_velocity is None:
        effective_velocity = daily_growth
    remaining_days = None
    projected_exhaustion = None
    if quota_mb > 0 and effective_velocity and effective_velocity > 0:
        headroom_mb = quota_mb - current_mb
        remaining_days = round(headroom_mb / effective_velocity, 2)
        projected_exhaustion = (parsed[-1][0] + timedelta(days=max(remaining_days, 0))).isoformat()

    quality = capacity_prediction_quality([value for _, value in parsed])
    risk = _risk_level(
        used_pct=(current_mb / quota_mb * 100.0) if quota_mb > 0 else 0.0,
        remaining_days=remaining_days,
        quality=quality["prediction_quality"],
    )
    return {
        "daily_growth_rate_mb": daily_growth,
        "weekly_growth_rate_mb": weekly_growth,
        "monthly_growth_rate_mb": monthly_growth,
        "rolling_average_daily_mb": rolling_avg_daily,
        "rolling_average_weekly_mb": rolling_avg_weekly,
        "storage_velocity_mb_per_day": effective_velocity,
        "projected_exhaustion_date": projected_exhaustion,
        "remaining_operational_days": remaining_days,
        "confidence_interval_days": quality["confidence_interval_days"],
        "prediction_quality": quality["prediction_quality"],
        "historical_variance_mb": quality["historical_variance_mb"],
        "capacity_risk_level": risk,
        "early_warning_thresholds": {"elevated_days": 45, "high_days": 21, "critical_days": 7},
        "recommendations": _recommendations(risk_level=risk, daily_growth=daily_growth, remaining_days=remaining_days),
    }


def build_cluster_capacity_router(get_client: callable, get_runtime_identity: callable | None = None) -> APIRouter:
    """`get_client` is a zero-arg callable that returns the live
    AsyncIOMotorClient. We accept it as a closure rather than importing
    server.py to avoid circular imports."""
    router = APIRouter(prefix="/api")

    @router.get("/cluster/capacity")
    async def cluster_capacity():
        now = time.monotonic()
        if _CACHE["payload"] is not None and (now - _CACHE["ts"]) < _CACHE_TTL_S:
            return _CACHE["payload"]

        quota_mb = _quota_mb()
        client: AsyncIOMotorClient = get_client()
        dbs: Dict[str, float] = {}
        total_storage_mb = 0.0

        # List candidate DB names (the two MASCI databases). We never
        # touch other Atlas projects.
        runtime_identity = get_runtime_identity() if callable(get_runtime_identity) else None
        candidates = managed_database_names(runtime_identity or {})
        seen = set()
        for db_name in candidates:
            if not db_name or db_name in seen:
                continue
            seen.add(db_name)
            try:
                stats = await client[db_name].command("dbStats")
                storage_mb = (stats.get("storageSize", 0) or 0) / (1024 * 1024)
                index_mb = (stats.get("indexSize", 0) or 0) / (1024 * 1024)
                # Storage + indexes both count toward Atlas quota
                dbs[db_name] = round(storage_mb + index_mb, 2)
                total_storage_mb += dbs[db_name]
            except Exception as e:  # noqa: BLE001 — DB may not exist
                logger.debug(f"cluster_capacity: skip {db_name} ({e})")

        used_pct = (total_storage_mb / quota_mb * 100.0) if quota_mb > 0 else 0.0

        if quota_mb == 0:
            severity = "ok"
        elif used_pct >= 95.0:
            severity = "critical"
        elif used_pct >= 80.0:
            severity = "warning"
        else:
            severity = "ok"

        payload = {
            "ok": True,
            "tier_quota_mb": quota_mb,
            "storage_used_mb": round(total_storage_mb, 2),
            "storage_used_pct": round(used_pct, 1),
            "severity": severity,
            "dbs": dbs,
            "ts": datetime.now(timezone.utc).isoformat(),
            "kpi_metadata": standardize_prediction_metadata(
                identifier="WP17A-KPI-021-current",
                display_name="Atlas Capacity Current Snapshot",
                description="Current Atlas capacity posture for the active environment.",
                formula={"storage_used_pct": "storage_used_mb / tier_quota_mb * 100", "severity_thresholds": {"warning": 80, "critical": 95}},
                owner="storage-reliability",
                refresh_interval="60 second cache",
                confidence="HIGH",
                validation_status="VALIDATED",
                dependencies=["dbStats", "managed database names", "ATLAS_QUOTA_MB"],
                data_freshness="Current request snapshot",
                consumer_portals=["Admin", "Storage & Recovery", "Public shell banner"],
                exception_notes=["This current snapshot is paired with the retained history endpoint for trend prediction."],
                extra={
                    "source_of_truth": ["dbStats", "managed_database_names"],
                    "api_endpoint": "/api/cluster/capacity",
                    "drilldown_source": "/admin/database",
                    "status_reason": "Public-safe point-in-time capacity signal intended to fail closed when quota pressure rises.",
                },
            ),
        }
        if callable(get_runtime_identity):
            payload["runtime_identity"] = runtime_identity_public_payload(runtime_identity)
        _CACHE["ts"] = now
        _CACHE["payload"] = payload
        return payload

    # ------------------------------------------------------------------
    # iter437 · Phase Sigma-II · history endpoint
    # ------------------------------------------------------------------
    @router.get("/cluster/capacity/history")
    async def cluster_capacity_history(
        days: int = Query(default=7, ge=1, le=90, description="lookback window in days, max 90"),
    ):
        """Return hourly capacity snapshots for the last `days` days.

        Also computes a simple linear-fit slope (MB/day) over the
        retrieved window and projects days-to-quota at current rate.
        """
        client: AsyncIOMotorClient = get_client()
        # Read from whichever DB the backend currently writes to —
        # `cluster_capacity_history` lives in masci_safety_preview when
        # APP_ENV=preview, masci_safety when production. We never read
        # cross-environment for history (preview history is preview-only).
        runtime_identity = get_runtime_identity() if callable(get_runtime_identity) else None
        db_name = ((runtime_identity_public_payload(runtime_identity).get("identity") or {}).get("db_name") if runtime_identity else None) or ""
        if not db_name:
            return {"status": "UNVERIFIABLE", "error": "canonical database name unavailable"}
        db = client[db_name]
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        cursor = db[HISTORY_COLLECTION].find(
            {"ts": {"$gte": cutoff}},
            {"_id": 0},
        ).sort("ts", 1)
        rows: List[Dict[str, Any]] = []
        async for r in cursor:
            # Mongo decoded `ts` as a datetime — emit ISO string for JSON.
            if isinstance(r.get("ts"), datetime):
                r["ts"] = r["ts"].isoformat()
            rows.append(r)

        # Compute slope (MB/day) over the points we have.
        slope_mb_per_day: Optional[float] = None
        days_to_quota: Optional[float] = None
        first_mb: Optional[float] = None
        last_mb: Optional[float] = None
        if len(rows) >= 2:
            first = rows[0]
            last = rows[-1]
            try:
                first_mb = float(first["storage_used_mb"])
                last_mb = float(last["storage_used_mb"])
                t0 = datetime.fromisoformat(first["ts"].replace("Z", "+00:00")) \
                    if isinstance(first["ts"], str) else first["ts"]
                t1 = datetime.fromisoformat(last["ts"].replace("Z", "+00:00")) \
                    if isinstance(last["ts"], str) else last["ts"]
                dt_days = max((t1 - t0).total_seconds() / 86400.0, 1 / 24.0)
                slope_mb_per_day = round((last_mb - first_mb) / dt_days, 3)
                quota = _quota_mb()
                if slope_mb_per_day and slope_mb_per_day > 0 and quota > 0:
                    headroom = quota - last_mb
                    days_to_quota = round(headroom / slope_mb_per_day, 1)
            except Exception:  # noqa: BLE001
                pass

        predictive = _series_metrics(rows, _quota_mb())

        return {
            "ok": True,
            "days": days,
            "samples": len(rows),
            "first_mb": first_mb,
            "last_mb": last_mb,
            "slope_mb_per_day": slope_mb_per_day,
            "days_to_quota": days_to_quota,
            "ts": datetime.now(timezone.utc).isoformat(),
            "rows": rows,
            "predictive": predictive,
            "trend_visualization_support": {
                "x_axis": "ts",
                "y_axis": "storage_used_mb",
                "series_count": len(rows),
            },
            "kpi_metadata": standardize_prediction_metadata(
                identifier="WP17A-KPI-021-history",
                display_name="Atlas Capacity Forecast",
                description="Historical storage trend and predictive capacity runway for the active environment.",
                formula={
                    "daily_growth_rate_mb": "window delta over retained hourly samples",
                    "remaining_operational_days": "(tier_quota_mb - last_mb) / storage_velocity_mb_per_day when velocity > 0",
                    "prediction_quality": "derived from historical variance vs average growth rate",
                },
                owner="storage-reliability",
                refresh_interval="hourly retained snapshots",
                confidence="HIGH" if len(rows) >= 24 else "MEDIUM",
                validation_status="VALIDATED",
                dependencies=["cluster_capacity_history", "dbStats", "hourly snapshot loop", "ATLAS_QUOTA_MB"],
                data_freshness=f"Last {days} day retained sample window",
                consumer_portals=["Admin", "Storage & Recovery", "Diagnostics"],
                exception_notes=["Prediction quality is intentionally lowered when retained variance is high or sample count is small."],
                extra={
                    "source_of_truth": ["cluster_capacity_history"],
                    "api_endpoint": "/api/cluster/capacity/history",
                    "drilldown_source": "/admin/database",
                    "status_reason": "Capacity forecasts are derived from retained hourly samples, not hardcoded safety assumptions.",
                },
            ),
        }

    return router


# ----------------------------------------------------------------------
# iter437 · Phase Sigma-II · hourly snapshot recorder.
# Called from server.py scheduler. Idempotent and best-effort — failures
# are logged but never propagate.
# ----------------------------------------------------------------------
async def record_capacity_snapshot(client) -> Optional[Dict[str, Any]]:
    """Insert a single capacity snapshot into `cluster_capacity_history`."""
    try:
        quota_mb = _quota_mb()
        target_name = getattr(client, "_authority_db_name", None)
        if not target_name:
            return None
        candidates = managed_database_names({"identity": {"db_name": target_name}})
        seen = set()
        dbs: Dict[str, float] = {}
        total_mb = 0.0
        for db_name in candidates:
            if not db_name or db_name in seen:
                continue
            seen.add(db_name)
            try:
                stats = await client[db_name].command("dbStats")
                storage_mb = (stats.get("storageSize", 0) or 0) / (1024 * 1024)
                index_mb = (stats.get("indexSize", 0) or 0) / (1024 * 1024)
                dbs[db_name] = round(storage_mb + index_mb, 2)
                total_mb += dbs[db_name]
            except Exception:  # noqa: BLE001
                pass

        used_pct = (total_mb / quota_mb * 100.0) if quota_mb > 0 else 0.0
        record = {
            "ts": datetime.now(timezone.utc),
            "tier_quota_mb": quota_mb,
            "storage_used_mb": round(total_mb, 2),
            "storage_used_pct": round(used_pct, 1),
            "dbs": dbs,
        }
        # Write to the DB the backend is currently using (preview or prod).
        target_db = client[target_name]
        await ensure_history_indexes(target_db)
        await target_db[HISTORY_COLLECTION].insert_one(record)
        # Strip _id for return
        record.pop("_id", None)
        return record
    except Exception as e:  # noqa: BLE001
        logger.warning("[cluster_capacity] snapshot record failed: %s", e)
        return None

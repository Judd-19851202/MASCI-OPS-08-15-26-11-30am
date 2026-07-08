"""TRACK 24.17 · System Health + platform posture read-only probes."""
from __future__ import annotations

import os
import shutil
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from .registry import Operation, OperationCategory, RiskLevel


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _disk() -> Dict[str, Any]:
    try:
        u = shutil.disk_usage("/app")
        pct = round((u.total - u.free) / u.total * 100, 1)
        state = "critical" if pct >= 90 else "warning" if pct >= 75 else "healthy"
        return {"used_percent": pct, "free_gb": round(u.free / 1e9, 2),
                "state": state}
    except OSError as e:
        return {"error": str(e), "state": "unavailable"}


async def _mongo(db) -> Dict[str, Any]:
    try:
        _ = await db.command("ping")
        return {"state": "healthy"}
    except Exception as e:  # noqa: BLE001
        return {"state": "critical", "error": str(e)[:200]}


async def _r2() -> Dict[str, Any]:
    try:
        import photo_storage  # noqa: PLC0415
        if not photo_storage.is_configured():
            return {"state": "warning",
                    "reason": "R2 env vars not set (S3_ENDPOINT_URL / S3_BUCKET / S3_ACCESS_KEY / S3_SECRET_KEY)"}
        try:
            c = photo_storage._client()  # noqa: SLF001
            c.head_bucket(Bucket=photo_storage._bucket())  # noqa: SLF001
            return {"state": "healthy",
                    "bucket": photo_storage._bucket()}  # noqa: SLF001
        except Exception as e:  # noqa: BLE001
            return {"state": "critical", "error": str(e)[:200]}
    except Exception as e:  # noqa: BLE001
        return {"state": "unavailable", "error": str(e)[:120]}


def _ai() -> Dict[str, Any]:
    key = os.environ.get("EMERGENT_LLM_KEY") or ""
    return {"state": "healthy" if key else "warning",
            "provider_key_configured": bool(key)}


def _email() -> Dict[str, Any]:
    key = os.environ.get("RESEND_API_KEY") or ""
    mode = os.environ.get("EMAIL_SAFETY_MODE") or ""
    auto = os.environ.get("AUTO_EMAIL_REPORTS") or ""
    state = "healthy"
    warnings: List[str] = []
    if not key:
        state = "warning"
        warnings.append("RESEND_API_KEY not configured.")
    if os.environ.get("APP_ENV") == "production":
        if mode == "strict":
            state = "warning"
            warnings.append("EMAIL_SAFETY_MODE=strict in production.")
        if auto == "false":
            state = "warning"
            warnings.append("AUTO_EMAIL_REPORTS=false in production.")
    return {"state": state, "email_safety_mode": mode,
            "auto_email_reports": auto,
            "provider_key_configured": bool(key),
            "warnings": warnings}


async def _dr_recent(db) -> Dict[str, Any]:
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        recent = await db.daily_reports.count_documents(
            {"created_at": {"$gte": cutoff}},
        )
        return {"state": "healthy", "count_last_24h": recent}
    except Exception as e:  # noqa: BLE001
        return {"state": "unavailable", "error": str(e)[:200]}


async def _system_health_status(_payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _system_health_dry_run(_payload)


async def _system_health_dry_run(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = payload["_db"]
    disk = _disk()
    mongo = await _mongo(db)
    r2 = await _r2()
    ai = _ai()
    email = _email()
    dr = await _dr_recent(db)
    states = [disk.get("state"), mongo.get("state"), r2.get("state"),
              ai.get("state"), email.get("state"), dr.get("state")]
    if "critical" in states:
        overall = "critical"
    elif "warning" in states:
        overall = "warning"
    elif "unavailable" in states:
        overall = "warning"
    else:
        overall = "healthy"
    return {
        "status": overall,
        "summary": f"System posture: {overall.upper()}",
        "components": {
            "disk": disk, "mongo": mongo, "r2": r2, "ai": ai,
            "email": email, "daily_reports": dr,
        },
        "generated_at": _now_iso(),
    }


def operations(_db) -> List[Operation]:
    return [
        Operation(
            id="health.system_overview",
            title="System Health Overview",
            description=(
                "One-glance red/yellow/green view of disk, Mongo, R2, "
                "AI provider, email provider, and Daily Report activity."
            ),
            category=OperationCategory.HEALTH,
            risk=RiskLevel.INFO,
            status_fn=_system_health_status,
            dry_run_fn=_system_health_dry_run,
            reads=["disk usage", "Mongo ping", "R2 head-bucket",
                   "env var presence for provider keys",
                   "daily_reports count in last 24h"],
            writes=[],
            never_touches=["user data", "provider credentials"],
        ),
    ]

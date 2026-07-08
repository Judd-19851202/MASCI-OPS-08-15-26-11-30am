"""TRACK 24.17 · R2 connectivity + posture check."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from .registry import Operation, OperationCategory, RiskLevel


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _r2_health_status(_payload: Dict[str, Any]) -> Dict[str, Any]:
    return await _r2_health_dry_run(_payload)


async def _r2_health_dry_run(_payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        import photo_storage  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        return {"status": "unavailable",
                "summary": f"photo_storage import failed: {e}"}
    if not photo_storage.is_configured():
        return {
            "status": "warning",
            "summary": "R2 not configured — set S3_ENDPOINT_URL / S3_BUCKET / S3_ACCESS_KEY / S3_SECRET_KEY.",
            "configured": False,
            "generated_at": _now_iso(),
        }
    try:
        c = photo_storage._client()  # noqa: SLF001
        c.head_bucket(Bucket=photo_storage._bucket())  # noqa: SLF001
        return {
            "status": "healthy",
            "summary": "R2 head-bucket succeeded.",
            "configured": True,
            "bucket": photo_storage._bucket(),  # noqa: SLF001
            "endpoint_prefix": photo_storage._env("S3_ENDPOINT_URL")[:80],  # noqa: SLF001
            "generated_at": _now_iso(),
        }
    except Exception as e:  # noqa: BLE001
        return {
            "status": "critical",
            "summary": f"R2 HEAD failed: {e}",
            "configured": True,
            "generated_at": _now_iso(),
        }


def operations(_db) -> List[Operation]:
    return [
        Operation(
            id="r2.health",
            title="R2 Health Check",
            description=(
                "Confirms Cloudflare R2 is reachable and the "
                "configured bucket responds to a HEAD request."
            ),
            category=OperationCategory.R2,
            risk=RiskLevel.INFO,
            status_fn=_r2_health_status,
            dry_run_fn=_r2_health_dry_run,
            reads=["S3/R2 env vars", "R2 bucket HEAD"],
            writes=[],
            never_touches=["R2 objects"],
        ),
    ]

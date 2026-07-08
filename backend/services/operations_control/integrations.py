"""TRACK 25.01 · Integration probes for the OCC.

Phase C consolidation: fold ``/admin/integration-truth`` and
``/admin/operations-dashboard`` into a single OCC card that runs the
platform's live integration probes (Motive · MaintainX · Resend · R2 ·
Mongo · Sentry · Emergent LLM). Same code path the deploy-readiness
gate uses so the numbers stay consistent across every surface.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from .registry import Operation, OperationCategory, RiskLevel


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _integrations_probe_all(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = payload.get("_db")
    if db is None:
        return {
            "status": "unavailable",
            "summary": (
                "Integration probes require an active database session."
            ),
            "generated_at": _now_iso(),
        }
    try:
        from routes.integration_health import run_all_probes  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        return {
            "status": "unavailable",
            "summary": "integration_health helpers not importable.",
            "error": str(e)[:200],
            "generated_at": _now_iso(),
        }

    try:
        result = await run_all_probes(db)
    except Exception as e:  # noqa: BLE001
        return {
            "status": "critical",
            "summary": f"Integration probes crashed: {str(e)[:160]}",
            "generated_at": _now_iso(),
        }

    probes: List[Dict[str, Any]] = list(result.get("probes") or [])
    down = [p for p in probes if p.get("status") == "down"]
    degraded = [p for p in probes if p.get("status") == "degraded"]
    up = [p for p in probes if p.get("status") in ("up", "ok", "configured")]

    if down:
        state = "critical"
    elif degraded:
        state = "warning"
    else:
        state = "healthy"

    warnings: List[str] = []
    for p in down:
        warnings.append(
            f"{p.get('id') or p.get('name') or 'integration'}: DOWN — "
            + str(p.get("detail") or "no detail")[:120]
        )
    for p in degraded:
        warnings.append(
            f"{p.get('id') or p.get('name') or 'integration'}: degraded — "
            + str(p.get("detail") or "no detail")[:120]
        )

    return {
        "status": state,
        "summary": (
            f"{len(probes)} integrations · {len(down)} down · "
            f"{len(degraded)} degraded · {len(up)} healthy"
        ),
        "probes": probes,
        "down_count": len(down),
        "degraded_count": len(degraded),
        "healthy_count": len(up),
        "warnings": warnings,
        "canonical_source": "routes.integration_health.run_all_probes",
        "legacy_routes": [
            "/admin/integration-truth",
            "/admin/operations-dashboard",
        ],
        "generated_at": _now_iso(),
    }


def operations(_db) -> List[Operation]:
    return [
        Operation(
            id="integrations.probe_all",
            title="Integrations Probe · All Providers",
            description=(
                "Live probe of every third-party integration the "
                "platform depends on (Motive · MaintainX · Resend · "
                "Cloudflare R2 · Emergent LLM · Sentry · Mongo). "
                "Read-only. Same probe layer that gates deploy "
                "readiness."
            ),
            category=OperationCategory.HEALTH,
            risk=RiskLevel.EXTERNAL_PROVIDER,
            status_fn=_integrations_probe_all,
            dry_run_fn=_integrations_probe_all,
            reads=[
                "env var presence for provider keys",
                "live provider health endpoints (Motive · MaintainX)",
                "Mongo ping · R2 head-bucket",
                "recent integration error log rows (last 24h)",
            ],
            writes=[],
            never_touches=[
                "provider credentials",
                "third-party data (read-only bearer-token probes)",
            ],
        ),
    ]

"""TRACK 24.17 · AI provider posture probe."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from .registry import Operation, OperationCategory, RiskLevel


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _ai_health(_payload: Dict[str, Any]) -> Dict[str, Any]:
    key = os.environ.get("EMERGENT_LLM_KEY") or ""
    dr_ai_enabled = os.environ.get("DR_V2_AI_ENABLED", "true").lower() != "false"
    try:
        from services.dr_ai import AGENTS  # noqa: PLC0415
        agent_ids = list(AGENTS.keys())
    except Exception as e:  # noqa: BLE001
        return {"status": "unavailable", "error": str(e)[:200]}

    warnings: List[str] = []
    state = "healthy"
    if not key:
        state = "warning"
        warnings.append("EMERGENT_LLM_KEY not configured — AI summary falls back to deterministic.")
    if not dr_ai_enabled:
        state = "warning"
        warnings.append("DR_V2_AI_ENABLED=false — AI synthesize endpoint returns ai_available=false.")

    return {
        "status": state,
        "summary": (
            f"{len(agent_ids)} AI agents registered · "
            f"AI provider {'configured' if key else 'MISSING'} · "
            f"synthesize {'ENABLED' if dr_ai_enabled else 'DISABLED'}"
        ),
        "provider_key_configured": bool(key),
        "dr_ai_enabled": dr_ai_enabled,
        "registered_agents": agent_ids,
        "warnings": warnings,
        "generated_at": _now_iso(),
    }


def operations(_db) -> List[Operation]:
    return [
        Operation(
            id="ai.health",
            title="AI Intelligence Health",
            description=(
                "Verifies the Emergent Universal Key is present, the "
                "DR AI subsystem is enabled, and lists the registered "
                "summarizer agents."
            ),
            category=OperationCategory.AI,
            risk=RiskLevel.INFO,
            status_fn=_ai_health,
            dry_run_fn=_ai_health,
            reads=["env var presence (never the value)", "AGENTS registry"],
            writes=[],
            never_touches=["provider keys", "prompts", "outputs"],
        ),
    ]

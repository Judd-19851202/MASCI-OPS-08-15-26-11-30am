"""DR-ROI-001 · Phase C · Emergent LLM Key provider (Claude Sonnet 4.5).

Now backed by the ForgedOps AI Gateway. This module remains for
backward compatibility with older callers — new code should call the
Gateway directly. The Gateway is model-agnostic (Anthropic / OpenAI /
Google) and provider-neutral env vars power routing.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict

from .provider import AiSynthesisResult
from services.ai_gateway import get_gateway
from services.ai_gateway.env import default_text_model
from services.ai_gateway.env import gateway_enabled


class EmergentClaudeProvider:
    """Model-agnostic wrapper backed by the AI Gateway."""

    name = "emergent"
    llm_provider = os.environ.get("AI_DEFAULT_PROVIDER", "anthropic")

    def __init__(self):
        self._api_key_present = bool(
            os.environ.get("EMERGENT_LLM_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        )

    async def synthesize(
        self,
        *,
        agent: str,
        system_message: str,
        user_payload: Dict[str, Any],
        response_schema: Dict[str, Any],
        session_id: str,
    ) -> AiSynthesisResult:
        started = datetime.now(timezone.utc).isoformat()  # TRACK-27.03-EXEMPT: machine envelope timestamp; frontend renders via formatPlatformTime

        # Route through the gateway. Task type = "operational_narrative"
        # for all three DR-V2 agents; the task_router picks the model.
        gw = get_gateway()
        env = None
        if gateway_enabled():
            env = await gw.dispatch(
                task="operational_narrative",
                system=system_message,
                user_payload=user_payload,
                response_schema=response_schema,
                session_id=session_id,
            )

        if env is None or not env.ai_available:
            reason = (env.fallback_reason if env else "gateway_disabled") or "unknown"
            return AiSynthesisResult(
                agent=agent, narrative=(env.narrative if env else "") or "",
                confidence=0.0, evidence_refs=[], sources_used=[],
                uncertainties=[reason],
                model=default_text_model(), provider=self.name,
                generated_at=started, ai_available=False,
                fallback_reason=reason,
            )

        return AiSynthesisResult(
            agent=agent,
            narrative=env.narrative,
            confidence=env.confidence,
            evidence_refs=list(env.evidence_refs),
            sources_used=list(env.sources_used),
            uncertainties=list(env.uncertainties),
            model=env.model or default_text_model(),
            provider=env.provider or self.name,
            generated_at=env.generated_at or started,
            ai_available=True,
        )


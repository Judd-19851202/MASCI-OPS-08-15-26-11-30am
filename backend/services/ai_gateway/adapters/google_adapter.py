"""Google Gemini adapter — scaffold with matching interface.

Wiring to the Google Gen AI SDK is deferred until we have `GOOGLE_AI_API_KEY`
provisioned in production. Interface is complete so failover routing can
already select this provider once the key is set.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict

from ..envelope import AiEnvelope


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GoogleAdapter:
    name = "google"

    async def text(
        self, *, system: str, user_payload: Dict[str, Any],
        response_schema: Dict[str, Any], session_id: str,
        model: str, task: str,
    ) -> AiEnvelope:
        key = os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("EMERGENT_LLM_KEY") or ""
        if not key:
            return AiEnvelope(task=task, narrative="", confidence=0.0,
                              evidence_refs=[], sources_used=[],
                              uncertainties=["google_key_missing"],
                              provider=self.name, model=model, generated_at=_now(),
                              ai_available=False, fallback_reason="missing_api_key")
        # Real SDK wiring lands with the Gemini task type roll-out.
        return AiEnvelope(task=task, narrative="", confidence=0.0,
                          evidence_refs=[], sources_used=[],
                          uncertainties=["google_text_scaffold"],
                          provider=self.name, model=model, generated_at=_now(),
                          ai_available=False, fallback_reason="scaffold")

    async def vision(
        self, *, system: str, images: list, user: str,
        response_schema: Dict[str, Any], session_id: str,
        model: str, task: str,
    ) -> AiEnvelope:
        return AiEnvelope(task=task, narrative="", confidence=0.0,
                          evidence_refs=[], sources_used=[],
                          uncertainties=["google_vision_scaffold"],
                          provider=self.name, model=model, generated_at=_now(),
                          ai_available=False, fallback_reason="scaffold")

    def ping(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "key_present": bool(os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("EMERGENT_LLM_KEY")),
        }

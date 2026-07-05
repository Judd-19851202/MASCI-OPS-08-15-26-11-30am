"""Anthropic (Claude) adapter — uses emergentintegrations LlmChat."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

from ..envelope import AiEnvelope


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AnthropicAdapter:
    name = "anthropic"

    async def text(
        self, *, system: str, user_payload: Dict[str, Any],
        response_schema: Dict[str, Any], session_id: str,
        model: str, task: str,
    ) -> AiEnvelope:
        key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("EMERGENT_LLM_KEY") or ""
        if not key:
            return AiEnvelope(task=task, narrative="", confidence=0.0,
                              evidence_refs=[], sources_used=[],
                              uncertainties=["anthropic_key_missing"],
                              provider=self.name, model=model, generated_at=_now(),
                              ai_available=False, fallback_reason="missing_api_key")

        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: PLC0415
        except Exception as exc:  # noqa: BLE001
            return AiEnvelope(task=task, narrative="", confidence=0.0,
                              evidence_refs=[], sources_used=[],
                              uncertainties=[f"import_error:{exc.__class__.__name__}"],
                              provider=self.name, model=model, generated_at=_now(),
                              ai_available=False, fallback_reason="import_error")

        prompt = (
            "EVIDENCE BUNDLE (json):\n"
            + json.dumps(user_payload, sort_keys=True, ensure_ascii=False)
            + "\n\nRespond with strict JSON matching this schema:\n"
            + json.dumps(response_schema, ensure_ascii=False)
        )
        try:
            chat = LlmChat(
                api_key=key, session_id=session_id, system_message=system,
            ).with_model("anthropic", model)
            raw = await chat.send_message(UserMessage(text=prompt))
        except Exception as exc:  # noqa: BLE001
            return AiEnvelope(task=task, narrative="", confidence=0.0,
                              evidence_refs=[], sources_used=[],
                              uncertainties=[f"call_failed:{exc.__class__.__name__}"],
                              provider=self.name, model=model, generated_at=_now(),
                              ai_available=False, fallback_reason="llm_call_failed")

        text = (raw or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            data = json.loads(text)
        except Exception:  # noqa: BLE001
            return AiEnvelope(task=task, narrative=text[:500], confidence=0.0,
                              evidence_refs=[], sources_used=[],
                              uncertainties=["non_json_response"],
                              provider=self.name, model=model, generated_at=_now(),
                              ai_available=False, fallback_reason="invalid_json")

        required = {"narrative", "confidence", "evidence_refs", "sources_used"}
        if not required.issubset(set(data.keys())):
            return AiEnvelope(task=task, narrative=str(data.get("narrative", ""))[:500],
                              confidence=0.0, evidence_refs=[], sources_used=[],
                              uncertainties=["schema_violation"],
                              provider=self.name, model=model, generated_at=_now(),
                              ai_available=False, fallback_reason="schema_violation")

        try:
            conf = float(data.get("confidence", 0.0))
        except (TypeError, ValueError):
            conf = 0.0
        conf = max(0.0, min(1.0, conf))
        return AiEnvelope(
            task=task,
            narrative=str(data.get("narrative", ""))[:4000],
            confidence=conf,
            evidence_refs=[str(x) for x in data.get("evidence_refs", [])][:64],
            sources_used=[str(x) for x in data.get("sources_used", [])][:64],
            uncertainties=[str(x) for x in (data.get("uncertainties") or [])][:32],
            provider=self.name, model=model, generated_at=_now(),
            ai_available=True,
        )

    async def vision(
        self, *, system: str, images: list, user: str,
        response_schema: Dict[str, Any], session_id: str,
        model: str, task: str,
    ) -> AiEnvelope:
        # Claude vision is not yet wired via the emergent LlmChat helper.
        return AiEnvelope(task=task, narrative="", confidence=0.0,
                          evidence_refs=[], sources_used=[],
                          uncertainties=["anthropic_vision_not_yet_implemented"],
                          provider=self.name, model=model, generated_at=_now(),
                          ai_available=False, fallback_reason="not_implemented")

    def ping(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "key_present": bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("EMERGENT_LLM_KEY")),
        }

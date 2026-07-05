"""DR-ROI-001 · Phase C · Emergent LLM Key provider (Claude Sonnet 4.5).

Concrete `AiProvider` implementation backed by `emergentintegrations`
LlmChat. Non-streaming JSON mode by default (agent envelopes are
short — streaming buys us nothing and adds parse complexity).

Lazy client construction: LlmChat is instantiated per-request so a
missing key at boot never prevents the server from starting.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

from .provider import AiSynthesisResult


class EmergentClaudeProvider:
    """Model-agnostic wrapper — swap `.with_model(...)` and it becomes GPT/Gemini."""

    name = "emergent"
    # Exact model string per user directive (Feb 2026). Overridable via env.
    model = os.environ.get("DR_AI_MODEL", "claude-sonnet-4-5-20250929")
    llm_provider = os.environ.get("DR_AI_LLM_PROVIDER", "anthropic")

    def __init__(self):
        # Lazy — key resolution and library import happen on first call.
        self._api_key = os.environ.get("EMERGENT_LLM_KEY", "")

    async def synthesize(
        self,
        *,
        agent: str,
        system_message: str,
        user_payload: Dict[str, Any],
        response_schema: Dict[str, Any],
        session_id: str,
    ) -> AiSynthesisResult:
        started = datetime.now(timezone.utc).isoformat()

        if not self._api_key:
            return AiSynthesisResult(
                agent=agent, narrative="", confidence=0.0,
                evidence_refs=[], sources_used=[],
                uncertainties=["EMERGENT_LLM_KEY not configured"],
                model=self.model, provider=self.name,
                generated_at=started, ai_available=False,
                fallback_reason="missing_api_key",
            )

        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
        except Exception as exc:  # noqa: BLE001
            return AiSynthesisResult(
                agent=agent, narrative="", confidence=0.0,
                evidence_refs=[], sources_used=[],
                uncertainties=[f"emergentintegrations import failed: {exc}"],
                model=self.model, provider=self.name,
                generated_at=started, ai_available=False,
                fallback_reason="import_error",
            )

        # Force strict-JSON output at the prompt level.
        prompt = (
            "EVIDENCE BUNDLE (json):\n"
            + json.dumps(user_payload, sort_keys=True, ensure_ascii=False)
            + "\n\nRespond with strict JSON matching this schema:\n"
            + json.dumps(response_schema, ensure_ascii=False)
        )

        try:
            chat = LlmChat(
                api_key=self._api_key,
                session_id=session_id,
                system_message=system_message,
            ).with_model(self.llm_provider, self.model)

            user_msg = UserMessage(text=prompt)

            # Non-streaming: envelope is short, and we need a single
            # atomic JSON parse to enforce schema strictness.
            raw = await chat.send_message(user_msg)
        except Exception as exc:  # noqa: BLE001
            return AiSynthesisResult(
                agent=agent, narrative="", confidence=0.0,
                evidence_refs=[], sources_used=[],
                uncertainties=[f"llm call failed: {exc.__class__.__name__}"],
                model=self.model, provider=self.name,
                generated_at=started, ai_available=False,
                fallback_reason="llm_call_failed",
            )

        text = (raw or "").strip()
        # Strip common markdown fences if the model wraps JSON.
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()

        try:
            data = json.loads(text)
        except Exception:  # noqa: BLE001
            return AiSynthesisResult(
                agent=agent, narrative=text[:500], confidence=0.0,
                evidence_refs=[], sources_used=[],
                uncertainties=["model returned non-JSON output"],
                model=self.model, provider=self.name,
                generated_at=started, ai_available=False,
                fallback_reason="invalid_json",
                raw={"text": text[:2000]},
            )

        # Shape check — reject anything that doesn't match the envelope.
        required = {"narrative", "confidence", "evidence_refs", "sources_used"}
        if not required.issubset(set(data.keys())):
            return AiSynthesisResult(
                agent=agent, narrative=str(data.get("narrative", ""))[:500],
                confidence=0.0, evidence_refs=[], sources_used=[],
                uncertainties=["response missing required envelope fields"],
                model=self.model, provider=self.name,
                generated_at=started, ai_available=False,
                fallback_reason="schema_violation",
                raw=data,
            )

        try:
            confidence = float(data.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))

        return AiSynthesisResult(
            agent=agent,
            narrative=str(data.get("narrative", ""))[:4000],
            confidence=confidence,
            evidence_refs=[str(x) for x in data.get("evidence_refs", [])][:64],
            sources_used=[str(x) for x in data.get("sources_used", [])][:64],
            uncertainties=[str(x) for x in data.get("uncertainties", []) or []][:32],
            model=self.model,
            provider=self.name,
            generated_at=started,
            ai_available=True,
        )

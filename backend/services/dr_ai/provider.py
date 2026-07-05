"""DR-ROI-001 · Phase C · Model-agnostic AI provider protocol.

Every concrete provider (emergent Claude, OpenAI, Gemini) implements
`AiProvider.synthesize()` and returns an `AiSynthesisResult`. Callers
NEVER import provider-specific SDKs — they resolve providers via
`factory.get_ai_provider()` so a future model swap is a one-line env
change with zero schema drift.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class AiSynthesisResult:
    """Strict JSON envelope returned by every AI agent.

    Every field on this object is required for the confidence UI,
    the evidence traceability panel, and the supervisor approval log.
    """
    agent: str
    narrative: str
    confidence: float                       # 0..1
    evidence_refs: List[str]                # field IDs the agent cited
    sources_used: List[str]                 # collection/section names
    uncertainties: List[str] = field(default_factory=list)
    model: str = ""
    provider: str = ""
    generated_at: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    ai_available: bool = True
    fallback_reason: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent,
            "narrative": self.narrative,
            "confidence": float(self.confidence),
            "evidence_refs": list(self.evidence_refs),
            "sources_used": list(self.sources_used),
            "uncertainties": list(self.uncertainties),
            "model": self.model,
            "provider": self.provider,
            "generated_at": self.generated_at,
            "tokens_in": int(self.tokens_in),
            "tokens_out": int(self.tokens_out),
            "ai_available": bool(self.ai_available),
            "fallback_reason": self.fallback_reason,
        }


class AiProvider(Protocol):
    """Abstract AI provider. Concrete implementations must be async-safe."""

    name: str
    model: str

    async def synthesize(
        self,
        *,
        agent: str,
        system_message: str,
        user_payload: Dict[str, Any],
        response_schema: Dict[str, Any],
        session_id: str,
    ) -> AiSynthesisResult:
        ...

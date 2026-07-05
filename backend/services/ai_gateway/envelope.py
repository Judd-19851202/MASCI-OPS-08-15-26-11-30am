"""ForgedOps AI Gateway · Canonical envelope.

Every adapter returns an `AiEnvelope`. Same shape across providers so
the gateway can route, retry, failover, and audit without special-casing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AiEnvelope:
    task: str
    narrative: str
    confidence: float
    evidence_refs: List[str]
    sources_used: List[str]
    uncertainties: List[str] = field(default_factory=list)

    provider: str = ""
    model: str = ""
    generated_at: str = ""
    tokens_in: int = 0
    tokens_out: int = 0

    ai_available: bool = True
    fallback_reason: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "task": self.task,
            "narrative": self.narrative,
            "confidence": float(self.confidence),
            "evidence_refs": list(self.evidence_refs),
            "sources_used": list(self.sources_used),
            "uncertainties": list(self.uncertainties),
            "provider": self.provider,
            "model": self.model,
            "generated_at": self.generated_at,
            "tokens_in": int(self.tokens_in),
            "tokens_out": int(self.tokens_out),
            "ai_available": bool(self.ai_available),
            "fallback_reason": self.fallback_reason,
        }
        return d

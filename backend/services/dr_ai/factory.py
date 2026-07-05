"""DR-ROI-001 · Phase C · AI provider factory.

Env-driven so we can flip Claude → GPT → Gemini via one variable
without changing route code or agent prompts.

DR_AI_PROVIDER=emergent     (default)
DR_AI_MODEL=claude-sonnet-4-5-20250929  (default; overridable)
DR_AI_LLM_PROVIDER=anthropic (default; use "openai" / "gemini" to swap)
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict

from .provider import AiProvider


@lru_cache(maxsize=1)
def get_ai_provider() -> AiProvider:
    kind = (os.environ.get("DR_AI_PROVIDER") or "emergent").lower()
    if kind == "emergent":
        from .emergent_provider import EmergentClaudeProvider
        return EmergentClaudeProvider()
    # Extension point for future providers (openai_direct, gemini_direct, ...).
    from .emergent_provider import EmergentClaudeProvider
    return EmergentClaudeProvider()


def provider_meta() -> Dict[str, Any]:
    """Read-only snapshot used by the /diagnostics + confidence panel."""
    p = get_ai_provider()
    return {
        "provider": getattr(p, "name", "emergent"),
        "model": getattr(p, "model", ""),
        "llm_provider": getattr(p, "llm_provider", ""),
        "ai_available": bool(os.environ.get("EMERGENT_LLM_KEY")),
    }

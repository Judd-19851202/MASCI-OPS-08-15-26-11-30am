"""DR-ROI-001 · Phase C · Daily Report V2 AI service package.

Production-grade, model-agnostic AI narrative synthesis engine for the
Daily Report V2 shell. Isolated from the V1 route surface. Never
mutates V1 collections, endpoints, or documents.

Public surface:
    build_evidence_bundle       — evidence.py
    evidence_hash               — evidence.py
    get_ai_provider             — factory.py
    AiSynthesisResult           — provider.py
    AGENTS                      — agents.py
    read_cache / write_cache    — cache.py
"""
from .evidence import build_evidence_bundle, evidence_hash
from .provider import AiSynthesisResult, AiProvider
from .factory import get_ai_provider, provider_meta
from .agents import AGENTS, AGENT_ORDER
from .cache import read_cache, write_cache

__all__ = [
    "build_evidence_bundle",
    "evidence_hash",
    "AiSynthesisResult",
    "AiProvider",
    "get_ai_provider",
    "provider_meta",
    "AGENTS",
    "AGENT_ORDER",
    "read_cache",
    "write_cache",
]

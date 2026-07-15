"""ForgedOps AI Gateway · Environment configuration.

All keys are provider-neutral and swappable. None are hard-coded in
source. Missing keys degrade the workflow to `ai_available=false`
rather than crashing — the operational surface always works.
"""
from __future__ import annotations
import os
from typing import Any, Dict


ENV_KEYS = (
    "AI_GATEWAY_ENABLED",
    "AI_DEFAULT_PROVIDER",
    "AI_DEFAULT_TEXT_MODEL",
    "AI_DEFAULT_VISION_PROVIDER",
    "AI_DEFAULT_VISION_MODEL",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_AI_API_KEY",
    "AI_PROVIDER_TIMEOUT_MS",
    "AI_PROVIDER_MAX_RETRIES",
    "AI_PROVIDER_FAILOVER_ENABLED",
    # Emergent LLM key remains the universal-key backstop so a single
    # env var still powers Claude/OpenAI/Gemini in preview environments
    # where individual provider keys are not configured.
    "EMERGENT_LLM_KEY",
)


def _truthy(v) -> bool:
    return (v or "").lower() in {"1", "true", "yes", "on"}


def gateway_enabled() -> bool:
    return _truthy(os.environ.get("AI_GATEWAY_ENABLED"))


def default_provider() -> str:
    return (os.environ.get("AI_DEFAULT_PROVIDER") or "anthropic").lower()


def default_text_model() -> str:
    return os.environ.get("AI_DEFAULT_TEXT_MODEL") or "claude-sonnet-4-6"


def default_vision_provider() -> str:
    return (os.environ.get("AI_DEFAULT_VISION_PROVIDER") or "openai").lower()


def default_vision_model() -> str:
    return os.environ.get("AI_DEFAULT_VISION_MODEL") or "gpt-4o"


def provider_timeout_ms() -> int:
    try:
        return int(os.environ.get("AI_PROVIDER_TIMEOUT_MS") or "45000")
    except (TypeError, ValueError):
        return 45000


def provider_max_retries() -> int:
    try:
        return int(os.environ.get("AI_PROVIDER_MAX_RETRIES") or "2")
    except (TypeError, ValueError):
        return 2


def failover_enabled() -> bool:
    return _truthy(os.environ.get("AI_PROVIDER_FAILOVER_ENABLED"))


def has_key(provider: str) -> bool:
    provider = (provider or "").lower()
    if provider == "anthropic":
        return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("EMERGENT_LLM_KEY"))
    if provider == "openai":
        return bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("EMERGENT_LLM_KEY"))
    if provider == "google":
        return bool(os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("EMERGENT_LLM_KEY"))
    return False


def env_snapshot() -> Dict[str, Any]:
    """Non-secret snapshot for admin telemetry. Never returns key values."""
    return {
        "gateway_enabled": gateway_enabled(),
        "default_provider": default_provider(),
        "default_text_model": default_text_model(),
        "default_vision_provider": default_vision_provider(),
        "default_vision_model": default_vision_model(),
        "timeout_ms": provider_timeout_ms(),
        "max_retries": provider_max_retries(),
        "failover_enabled": failover_enabled(),
        "providers_with_keys": {
            "anthropic": has_key("anthropic"),
            "openai": has_key("openai"),
            "google": has_key("google"),
        },
    }

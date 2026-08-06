"""AI Gateway · unit tests. Do NOT call any live LLM."""
from __future__ import annotations
import asyncio
import os
import sys
from pathlib import Path

BACKEND = Path("/app/backend")
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
os.environ.setdefault("SCHEDULER_ENABLED", "false")
os.environ.setdefault("AI_GATEWAY_ENABLED", "true")


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_env_snapshot_returns_no_key_values():
    from services.ai_gateway.env import env_snapshot
    snap = env_snapshot()
    for banned in ("api_key", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_AI_API_KEY", "EMERGENT_LLM_KEY"):
        # Recursively check for any string that contains raw key material.
        assert banned not in str(snap), f"env_snapshot leaked '{banned}'"
    for k in ("gateway_enabled", "default_provider", "default_text_model",
              "providers_with_keys"):
        assert k in snap


def test_task_router_default_routes():
    from services.ai_gateway.task_router import route, TASK_ROUTES
    assert TASK_ROUTES["operational_narrative"][0] == "anthropic"
    assert TASK_ROUTES["photo_vision"][0] == "openai"
    p, m = route("operational_narrative")
    assert p == "anthropic"
    assert "claude" in m.lower()


def test_task_router_env_override(monkeypatch):
    from services.ai_gateway.task_router import route
    monkeypatch.setenv("AI_TASK_ROUTE__photo_vision", "google:gemini-2.0-flash")
    p, m = route("photo_vision")
    assert p == "google"
    assert m == "gemini-2.0-flash"


def test_gateway_registers_three_providers():
    from services.ai_gateway import get_gateway
    get_gateway.cache_clear()
    gw = get_gateway()
    names = sorted(gw.providers().keys())
    assert names == ["anthropic", "google", "openai"]


def test_gateway_disabled_returns_fallback_envelope():
    from services.ai_gateway import get_gateway
    import services.ai_gateway.env as env_mod
    from services.ai_gateway.registry import gateway_enabled as _gen

    # Force env to disabled.
    old = os.environ.pop("AI_GATEWAY_ENABLED", None)
    try:
        get_gateway.cache_clear()
        gw = get_gateway()

        async def _run():
            return await gw.dispatch(
                task="operational_narrative",
                system="s", user_payload={"x": 1},
                response_schema={"type": "object"},
                session_id="t",
            )
        env = _run_async(_run())
        assert env.ai_available is False
        assert env.fallback_reason == "gateway_disabled"
        assert env.task == "operational_narrative"
    finally:
        if old is not None:
            os.environ["AI_GATEWAY_ENABLED"] = old
        get_gateway.cache_clear()


def test_gateway_missing_key_returns_fallback():
    """With no provider key set, dispatch should return ai_available=False."""
    from services.ai_gateway import get_gateway
    saved = {}
    for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_AI_API_KEY", "EMERGENT_LLM_KEY"):
        if k in os.environ:
            saved[k] = os.environ.pop(k)
    os.environ["AI_GATEWAY_ENABLED"] = "true"
    try:
        get_gateway.cache_clear()
        gw = get_gateway()

        async def _run():
            return await gw.dispatch(
                task="operational_narrative",
                system="s", user_payload={},
                response_schema={"type": "object"},
                session_id="t",
            )
        env = _run_async(_run())
        assert env.ai_available is False
        assert env.fallback_reason in {"missing_provider_key", "adapter_not_registered"}
    finally:
        for k, v in saved.items():
            os.environ[k] = v
        get_gateway.cache_clear()


def test_envelope_serialization_stable():
    from services.ai_gateway.envelope import AiEnvelope
    e = AiEnvelope(
        task="t", narrative="n", confidence=0.75,
        evidence_refs=["a", "b"], sources_used=["c"],
        provider="anthropic", model="m",
    )
    d = e.to_dict()
    for k in ("task", "narrative", "confidence", "evidence_refs", "sources_used",
              "provider", "model", "ai_available"):
        assert k in d
    assert d["confidence"] == 0.75


def test_adapter_interfaces_have_text_vision_ping():
    from services.ai_gateway.adapters.anthropic_adapter import AnthropicAdapter
    from services.ai_gateway.adapters.openai_adapter import OpenAIAdapter
    from services.ai_gateway.adapters.google_adapter import GoogleAdapter
    for cls in (AnthropicAdapter, OpenAIAdapter, GoogleAdapter):
        a = cls()
        assert hasattr(a, "text") and callable(a.text)
        assert hasattr(a, "vision") and callable(a.vision)
        assert hasattr(a, "ping") and callable(a.ping)
        info = a.ping()
        assert "provider" in info


def test_gateway_never_exposes_model_names_at_env_snapshot_field_layer():
    """Sanity: workflow-facing snapshot must not include api keys."""
    from services.ai_gateway.env import env_snapshot
    snap = env_snapshot()
    joined = str(snap).lower()
    for banned in ("sk-", "bearer ", "authorization"):
        assert banned not in joined, f"gateway snapshot leaked '{banned}'"

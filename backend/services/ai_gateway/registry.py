"""ForgedOps AI Gateway · Provider registry + adapter interface + failover."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Dict, Optional, Protocol

from .env import (
    default_provider, default_text_model, env_snapshot,
    failover_enabled, gateway_enabled, has_key,
    provider_max_retries, provider_timeout_ms,
)
from .envelope import AiEnvelope
from .task_router import route


class ProviderAdapter(Protocol):
    name: str

    async def text(
        self, *, system: str, user_payload: Dict[str, Any],
        response_schema: Dict[str, Any], session_id: str,
        model: str, task: str,
    ) -> AiEnvelope: ...

    async def vision(
        self, *, system: str, images: list, user: str,
        response_schema: Dict[str, Any], session_id: str,
        model: str, task: str,
    ) -> AiEnvelope: ...

    def ping(self) -> Dict[str, Any]: ...


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fallback_envelope(task: str, provider: str, model: str, reason: str) -> AiEnvelope:
    return AiEnvelope(
        task=task, narrative="", confidence=0.0,
        evidence_refs=[], sources_used=[], uncertainties=[reason],
        provider=provider, model=model, generated_at=_now(),
        ai_available=False, fallback_reason=reason,
    )


# Reasons that will never succeed on retry against the same provider.
# When we see one of these, jump straight to failover — retrying a bad
# key wastes latency and generates duplicate 401s in the vendor's
# alerting.
_NON_RETRYABLE_REASONS = {
    "missing_api_key",
    "import_error",
    "openai_key_missing",
    "openai_vision_key_missing",
    "anthropic_key_missing",
    "google_key_missing",
    "invalid_api_key",
    "unauthorized",
    "schema_violation",
    "not_implemented",
    "scaffold",
    "no_images",
}


def _is_non_retryable(reason: Optional[str]) -> bool:
    if not reason:
        return False
    r = str(reason).lower()
    if r in _NON_RETRYABLE_REASONS:
        return True
    # Adapters embed vendor-error class names in fallback_reason
    # (e.g. "call_failed" but with uncertainties "AuthenticationError").
    # Auth-shaped substrings are effectively non-retryable.
    return any(tok in r for tok in ("auth", "401", "403", "key_missing", "invalid_key"))


# Provider-appropriate default models used when failing over. Sending
# a Claude model string to OpenAI (or vice-versa) would produce a 400
# and defeat the whole point of failover. These are the current
# recommended models per the Emergent integration playbook (Feb 2026)
# and can be overridden by AI_DEFAULT_TEXT_MODEL_<PROVIDER> envs for
# operators who want to pin a specific version in production.
_PROVIDER_DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "openai":    "gpt-5.4",
    "google":    "gemini-2.5-flash",
}


def _provider_default_model(provider: str) -> str:
    import os as _os
    override = _os.environ.get(f"AI_DEFAULT_TEXT_MODEL_{provider.upper()}")
    if override:
        return override
    return _PROVIDER_DEFAULT_MODELS.get(provider, default_text_model())


class Gateway:
    """Central dispatcher — the ONLY place workflows import from.

    Workflows call `dispatch(task, ...)` and receive an `AiEnvelope`.
    Provider selection, key lookup, retries, and failover are all
    hidden. If nothing works, workflows still get a valid envelope
    with `ai_available=False` and continue their operational flow.
    """

    def __init__(self):
        self._adapters: Dict[str, ProviderAdapter] = {}

    def register(self, adapter: ProviderAdapter) -> None:
        self._adapters[adapter.name] = adapter

    def provider(self, name: str) -> Optional[ProviderAdapter]:
        return self._adapters.get(name)

    def providers(self) -> Dict[str, ProviderAdapter]:
        return dict(self._adapters)

    async def dispatch(
        self,
        task: str,
        *,
        system: str,
        user_payload: Dict[str, Any],
        response_schema: Dict[str, Any],
        session_id: str,
    ) -> AiEnvelope:
        if not gateway_enabled():
            return _fallback_envelope(task, "gateway", "", "gateway_disabled")

        provider_name, model = route(task)
        return await self._dispatch_provider(
            provider_name, model, task,
            system=system, user_payload=user_payload,
            response_schema=response_schema, session_id=session_id,
        )

    async def dispatch_vision(
        self,
        task: str,
        *,
        system: str,
        images: list,
        user: str,
        response_schema: Dict[str, Any],
        session_id: str,
    ) -> AiEnvelope:
        """Vision-specific dispatch. Routes through the same task_router
        so `photo_vision` etc. resolve provider+model consistently."""
        if not gateway_enabled():
            return _fallback_envelope(task, "gateway", "", "gateway_disabled")

        provider_name, model = route(task)
        adapter = self._adapters.get(provider_name)
        if adapter is None:
            return _fallback_envelope(task, provider_name, model, "adapter_not_registered")
        if not has_key(provider_name):
            return _fallback_envelope(task, provider_name, model, "missing_provider_key")
        timeout_s = max(1.0, provider_timeout_ms() / 1000.0)
        try:
            import asyncio as _a
            return await _a.wait_for(
                adapter.vision(
                    system=system, images=images, user=user,
                    response_schema=response_schema, session_id=session_id,
                    model=model, task=task,
                ),
                timeout=timeout_s,
            )
        except Exception as exc:  # noqa: BLE001
            return _fallback_envelope(task, provider_name, model, f"vision_error:{exc.__class__.__name__}")

    async def _dispatch_provider(
        self, provider_name: str, model: str, task: str,
        *, system, user_payload, response_schema, session_id,
        _attempted: Optional[set] = None,
    ) -> AiEnvelope:
        """Dispatch to a provider with retry-then-failover semantics.

        Adapters are permitted to catch their own errors and return an
        envelope with `ai_available=False` (they do this to normalize
        error surfaces). The dispatcher therefore treats such an
        envelope as an implicit failure and continues its retry /
        failover loop, so a 401 from one provider automatically
        falls over to the next configured provider instead of silently
        producing an empty narrative.
        """
        _attempted = _attempted or set()
        _attempted.add(provider_name)

        adapter = self._adapters.get(provider_name)
        if adapter is None:
            return await self._try_failover(
                task, provider_name, model, "adapter_not_registered",
                _attempted, system=system, user_payload=user_payload,
                response_schema=response_schema, session_id=session_id,
            )
        if not has_key(provider_name):
            return await self._try_failover(
                task, provider_name, model, "missing_provider_key",
                _attempted, system=system, user_payload=user_payload,
                response_schema=response_schema, session_id=session_id,
            )

        retries = provider_max_retries()
        timeout_s = max(1.0, provider_timeout_ms() / 1000.0)
        last_reason: Optional[str] = None
        for attempt in range(retries + 1):
            try:
                env = await asyncio.wait_for(
                    adapter.text(
                        system=system, user_payload=user_payload,
                        response_schema=response_schema, session_id=session_id,
                        model=model, task=task,
                    ),
                    timeout=timeout_s,
                )
            except asyncio.TimeoutError:
                last_reason = f"timeout_attempt_{attempt+1}"
                continue
            except Exception as exc:  # noqa: BLE001
                last_reason = f"{exc.__class__.__name__}_attempt_{attempt+1}"
                continue

            # Adapter completed without raising. If it self-reported a
            # failure (ai_available=False), keep retrying / failing over
            # instead of returning silently.
            if getattr(env, "ai_available", False):
                return env
            last_reason = f"{env.fallback_reason or 'provider_unavailable'}_attempt_{attempt+1}"
            # Non-retryable reasons short-circuit the retry loop and
            # jump straight to failover — retrying a bad key or a
            # schema violation on the same provider is wasted latency.
            if _is_non_retryable(env.fallback_reason):
                break

        return await self._try_failover(
            task, provider_name, model, last_reason or "unknown_error",
            _attempted, system=system, user_payload=user_payload,
            response_schema=response_schema, session_id=session_id,
        )

    async def _try_failover(
        self, task: str, primary: str, model: str, reason: str,
        attempted: set, *, system, user_payload, response_schema, session_id,
    ) -> AiEnvelope:
        if not failover_enabled():
            return _fallback_envelope(task, primary, model, reason)
        for fallback in self._failover_order(primary):
            if fallback in attempted:
                continue
            if not (fallback in self._adapters and has_key(fallback)):
                continue
            env = await self._dispatch_provider(
                fallback, _provider_default_model(fallback), task,
                system=system, user_payload=user_payload,
                response_schema=response_schema, session_id=session_id,
                _attempted=attempted,
            )
            if getattr(env, "ai_available", False):
                return env
        return _fallback_envelope(task, primary, model, reason)

    def _failover_order(self, primary: str) -> list:
        order = ["anthropic", "openai", "google"]
        if primary in order:
            order.remove(primary)
        return order


@lru_cache(maxsize=1)
def get_gateway() -> Gateway:
    g = Gateway()
    # Lazy adapter imports so a missing SDK for one provider never
    # prevents the others from registering.
    try:
        from .adapters.anthropic_adapter import AnthropicAdapter
        g.register(AnthropicAdapter())
    except Exception:  # noqa: BLE001
        pass
    try:
        from .adapters.openai_adapter import OpenAIAdapter
        g.register(OpenAIAdapter())
    except Exception:  # noqa: BLE001
        pass
    try:
        from .adapters.google_adapter import GoogleAdapter
        g.register(GoogleAdapter())
    except Exception:  # noqa: BLE001
        pass
    return g


def provider_meta_snapshot() -> Dict[str, Any]:
    """Admin telemetry only — never surfaced to field users."""
    g = get_gateway()
    return {
        "env": env_snapshot(),
        "registered_providers": sorted(g.providers().keys()),
        "task_routes": {t: {"provider": p, "model": m} for t, (p, m) in route.__globals__["TASK_ROUTES"].items()},
    }

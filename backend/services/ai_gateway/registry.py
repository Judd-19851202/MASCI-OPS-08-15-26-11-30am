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
    ) -> AiEnvelope:
        adapter = self._adapters.get(provider_name)
        if adapter is None:
            return _fallback_envelope(task, provider_name, model, "adapter_not_registered")
        if not has_key(provider_name):
            # Try failover if enabled.
            if failover_enabled():
                for fallback in self._failover_order(provider_name):
                    if has_key(fallback) and fallback in self._adapters:
                        return await self._dispatch_provider(
                            fallback, default_text_model(), task,
                            system=system, user_payload=user_payload,
                            response_schema=response_schema, session_id=session_id,
                        )
            return _fallback_envelope(task, provider_name, model, "missing_provider_key")

        retries = provider_max_retries()
        timeout_s = max(1.0, provider_timeout_ms() / 1000.0)
        last_reason: Optional[str] = None
        for attempt in range(retries + 1):
            try:
                return await asyncio.wait_for(
                    adapter.text(
                        system=system, user_payload=user_payload,
                        response_schema=response_schema, session_id=session_id,
                        model=model, task=task,
                    ),
                    timeout=timeout_s,
                )
            except asyncio.TimeoutError:
                last_reason = f"timeout_attempt_{attempt+1}"
            except Exception as exc:  # noqa: BLE001
                last_reason = f"{exc.__class__.__name__}_attempt_{attempt+1}"

        if failover_enabled():
            for fallback in self._failover_order(provider_name):
                if fallback in self._adapters and has_key(fallback):
                    try:
                        return await asyncio.wait_for(
                            self._adapters[fallback].text(
                                system=system, user_payload=user_payload,
                                response_schema=response_schema,
                                session_id=session_id,
                                model=default_text_model(), task=task,
                            ),
                            timeout=timeout_s,
                        )
                    except Exception:  # noqa: BLE001
                        continue

        return _fallback_envelope(task, provider_name, model, last_reason or "unknown_error")

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

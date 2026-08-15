"""Admin-only AI Health endpoint.

Provides real-time provider health so silent auth / quota failures in
production surface immediately in the Admin panel instead of quietly
falling through to the deterministic-summary fallback.

    GET /api/ai/health
        -> {
            "providers": [
                {"name": "anthropic", "status": "ok", "latency_ms": 812},
                {"name": "openai",    "status": "unauthorized",
                 "reason": "unauthorized", "detail": "401 …"},
                ...
            ],
            "summary": {"ok": 1, "degraded": 0, "failed": 1, "total": 3},
            "primary_route": {"task": "operational_narrative",
                              "provider": "anthropic", "model": "..."},
            "generated_at": "2026-02-08T..."
        }

Each ping runs a tiny 1-token synthesis against the provider. Results
are cached for 30s to avoid hammering the providers when the admin
UI polls the endpoint.
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends

from services.ai_gateway import get_gateway
from services.ai_gateway.env import env_snapshot, has_key
from services.ai_gateway.task_router import route
from services.ai_gateway.registry import _provider_default_model


logger = logging.getLogger(__name__)


_CACHE: Dict[str, Any] = {"ts": 0.0, "payload": None}
_CACHE_TTL_S = 30.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _ping_provider(name: str) -> Dict[str, Any]:
    """Run a tiny synthesis against one provider. Returns a health dict."""
    gw = get_gateway()
    adapter = gw.provider(name)
    entry: Dict[str, Any] = {
        "name": name,
        "key_present": has_key(name),
        "adapter_registered": adapter is not None,
    }
    if adapter is None:
        entry.update(status="missing_adapter", reason="adapter_not_registered")
        return entry
    if not has_key(name):
        entry.update(status="no_key", reason="missing_api_key")
        return entry

    # Ping THIS provider with ITS OWN model — not the primary route's
    # model. Using route("operational_narrative") here made every row
    # (OpenAI, Google) report Anthropic's model/latency (truth defect).
    model = _provider_default_model(name)
    system = (
        "You are a health probe. Reply with EXACTLY this JSON and nothing "
        'else: {"narrative":"ok","confidence":1,"evidence_refs":[],'
        '"sources_used":[]}. No markdown fences, no explanations.'
    )
    payload = {"probe": True}
    schema = {
        "type": "object",
        "properties": {
            "narrative": {"type": "string"},
            "confidence": {"type": "number"},
            "evidence_refs": {"type": "array"},
            "sources_used": {"type": "array"},
        },
        "required": ["narrative", "confidence", "evidence_refs", "sources_used"],
    }
    started = time.perf_counter()
    try:
        env = await asyncio.wait_for(
            adapter.text(
                system=system, user_payload=payload,
                response_schema=schema, session_id=f"health-{name}",
                model=model, task="operational_narrative",
            ),
            timeout=15.0,
        )
    except asyncio.TimeoutError:
        entry.update(
            status="timeout", reason="timeout",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        return entry
    except Exception as exc:  # noqa: BLE001
        entry.update(
            status="error", reason=exc.__class__.__name__,
            detail=str(exc)[:200],
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        return entry

    latency_ms = int((time.perf_counter() - started) * 1000)
    if getattr(env, "ai_available", False):
        entry.update(status="ok", model=env.model, latency_ms=latency_ms)
    else:
        reason = (env.fallback_reason or "unknown").lower()
        # Map the adapter's fallback_reason into a friendlier admin
        # status so the UI can color-code cleanly.
        if "auth" in reason or reason in {"unauthorized", "invalid_api_key"}:
            status = "unauthorized"
        elif reason in {"scaffold", "not_implemented"}:
            status = "not_wired"
        else:
            status = "degraded"
        entry.update(
            status=status, reason=reason, latency_ms=latency_ms,
            uncertainties=list(env.uncertainties or [])[:3],
            model=env.model,
        )
    return entry


async def _health_snapshot() -> Dict[str, Any]:
    now = time.time()
    if _CACHE["payload"] and (now - _CACHE["ts"] < _CACHE_TTL_S):
        return _CACHE["payload"]

    names = ["anthropic", "openai", "google"]
    results: List[Dict[str, Any]] = await asyncio.gather(
        *[_ping_provider(n) for n in names]
    )

    ok = sum(1 for r in results if r.get("status") == "ok")
    failed = sum(1 for r in results if r.get("status") in {"unauthorized", "error", "timeout", "no_key", "missing_adapter"})
    degraded = sum(1 for r in results if r.get("status") in {"degraded", "not_wired"})

    primary_provider, primary_model = route("operational_narrative")
    payload = {
        "providers": results,
        "summary": {"ok": ok, "degraded": degraded, "failed": failed, "total": len(results)},
        "primary_route": {
            "task": "operational_narrative",
            "provider": primary_provider,
            "model": primary_model,
        },
        "env": env_snapshot(),
        "generated_at": _now_iso(),
    }
    _CACHE["ts"] = now
    _CACHE["payload"] = payload
    return payload


def register_ai_health_routes(api_router: APIRouter, *, require_admin) -> None:
    @api_router.get("/ai/health")
    async def ai_health(_actor=Depends(require_admin)) -> Dict[str, Any]:
        """Ping every AI provider and report status. Admin-gated."""
        return await _health_snapshot()

    @api_router.post("/ai/health/refresh")
    async def ai_health_refresh(_actor=Depends(require_admin)) -> Dict[str, Any]:
        """Force a fresh ping (bypass cache)."""
        _CACHE["ts"] = 0.0
        _CACHE["payload"] = None
        return await _health_snapshot()


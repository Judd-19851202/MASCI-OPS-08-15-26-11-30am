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
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from motor.motor_asyncio import AsyncIOMotorClient

from services.ai_gateway import get_gateway
from services.ai_gateway.env import env_snapshot, has_key
from services.ai_gateway.task_router import route


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

    # Route the health check through the same model the workflow will
    # use for `operational_narrative` on this provider.
    _, model = route("operational_narrative")
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

    @api_router.get("/admin/clear-backup-lock")
    async def clear_backup_lock(_actor=Depends(require_admin)) -> Dict[str, Any]:
        mongo_url = (os.environ.get("MONGO_URL") or "").strip()
        db_name = (os.environ.get("DB_NAME") or "").strip()
        if not mongo_url or not db_name:
            return {
                "ok": False,
                "deleted": False,
                "detail": "missing_database_configuration",
            }

        client = AsyncIOMotorClient(mongo_url)
        try:
            target_db = client[db_name]
            result = await target_db["scheduler_locks"].delete_one({"_id": "backup_scheduler"})
            return {
                "ok": True,
                "database": db_name,
                "collection": "scheduler_locks",
                "lock_id": "backup_scheduler",
                "deleted": bool(result.deleted_count),
                "deleted_count": int(result.deleted_count or 0),
                "detail": "backup_scheduler lock cleared" if result.deleted_count else "backup_scheduler lock not found",
            }
        finally:
            client.close()

    @api_router.get("/admin/backups/force-r2-archive")
    async def force_r2_archive(
        background_tasks: BackgroundTasks,
        _actor=Depends(require_admin),
    ) -> Dict[str, Any]:
        import server as _server  # noqa: PLC0415

        if getattr(_server, "_COMPLETE_R2_IN_PROGRESS", False):
            return {
                "accepted": False,
                "detail": "A complete archive is already in progress.",
                "poll": "/api/admin/backups-complete-r2-state",
            }

        _server._COMPLETE_R2_IN_PROGRESS = True
        _server._COMPLETE_R2_LAST["started_at"] = datetime.now(timezone.utc).isoformat()
        _server._COMPLETE_R2_LAST["finished_at"] = None
        _server._COMPLETE_R2_LAST["outcome"] = "in-progress"

        async def _do_complete() -> None:
            try:
                res = await _server._run_complete_archive_to_r2(_server.db)
                _server._COMPLETE_R2_LAST["finished_at"] = datetime.now(timezone.utc).isoformat()
                if res:
                    _server._COMPLETE_R2_LAST["outcome"] = "ok"
                    _server._COMPLETE_R2_LAST["filename"] = res.get("filename")
                    _server._COMPLETE_R2_LAST["size_bytes"] = res.get("size_bytes")
                    _server._COMPLETE_R2_LAST["r2_key"] = res.get("r2_key")
                    _server._COMPLETE_R2_LAST["presigned_url"] = res.get("presigned_url")
                    _server._COMPLETE_R2_LAST["stats"] = res.get("stats")
                else:
                    _server._COMPLETE_R2_LAST["outcome"] = "FAILED — see logs"
            except Exception as exc:  # noqa: BLE001
                logger.exception("[force-r2-archive] crashed: %s", exc)
                _server._COMPLETE_R2_LAST["outcome"] = f"EXCEPTION: {exc!r}"
                _server._COMPLETE_R2_LAST["finished_at"] = datetime.now(timezone.utc).isoformat()
            finally:
                _server._COMPLETE_R2_IN_PROGRESS = False

        background_tasks.add_task(_do_complete)
        return {
            "accepted": True,
            "poll": "/api/admin/backups-complete-r2-state",
            "started_at": _server._COMPLETE_R2_LAST["started_at"],
        }

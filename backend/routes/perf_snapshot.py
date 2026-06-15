"""
TRACK 14.0-RC1-FERRARI · /api/admin/perf-snapshot (2026-02-15).

Single admin-only endpoint that returns a 10-second "is the platform
healthy?" snapshot. Designed for the Hot-Rod Health view — disk +
memory + uptime + Mongo + recent error counts + hot-endpoint latency.

Doctrine:
  - READ-ONLY. Never writes. Never mutates state.
  - Admin-gated via `require_admin_dep`.
  - Returns within ~200ms (no external API calls; no big aggregates).
  - The latency-probe section measures THIS process's own median
    request time over a small synthetic round-trip — so the figure
    represents the worker's perceived latency, not external ingress.
"""
from __future__ import annotations

import os
import time
import shutil
import platform
from datetime import datetime, timezone
from typing import Any, Callable, Dict

from fastapi import APIRouter, Depends, FastAPI
from motor.motor_asyncio import AsyncIOMotorDatabase

try:
    import psutil  # type: ignore
    _HAS_PSUTIL = True
except Exception:  # pragma: no cover
    _HAS_PSUTIL = False


def register_perf_snapshot_routes(
    app: FastAPI,
    db: AsyncIOMotorDatabase,
    require_admin_dep: Callable,
) -> None:
    router = APIRouter()

    _BOOT_TS = time.time()

    @router.get(
        "/api/admin/perf-snapshot",
        dependencies=[Depends(require_admin_dep)],
    )
    async def perf_snapshot() -> Dict[str, Any]:
        # ── disk ───────────────────────────────────────────────────
        disk: Dict[str, Any]
        try:
            usage = shutil.disk_usage("/app")
            disk = {
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent": round((usage.used / usage.total) * 100, 1),
            }
        except Exception as e:  # pragma: no cover
            disk = {"error": str(e)}

        # ── memory ─────────────────────────────────────────────────
        memory: Dict[str, Any]
        if _HAS_PSUTIL:
            try:
                vm = psutil.virtual_memory()
                memory = {
                    "total_gb": round(vm.total / (1024**3), 2),
                    "used_gb": round((vm.total - vm.available) / (1024**3), 2),
                    "available_gb": round(vm.available / (1024**3), 2),
                    "percent": vm.percent,
                }
            except Exception as e:
                memory = {"error": str(e)}
        else:
            memory = {"error": "psutil not installed"}

        # ── backend uptime ────────────────────────────────────────
        uptime_seconds = int(time.time() - _BOOT_TS)
        uptime = {
            "seconds": uptime_seconds,
            "hours": round(uptime_seconds / 3600, 2),
            "boot_ts_utc": datetime.fromtimestamp(_BOOT_TS, tz=timezone.utc).isoformat(),
        }

        # ── mongo ping ────────────────────────────────────────────
        mongo: Dict[str, Any] = {}
        try:
            t0 = time.perf_counter()
            await db.command("ping")
            mongo = {"ok": True, "ping_ms": int((time.perf_counter() - t0) * 1000)}
        except Exception as e:
            mongo = {"ok": False, "error": str(e)}

        # ── self-probe latency: take a quick read on a tiny hot
        # collection to confirm the worker's own request-handling
        # latency is healthy. Cheap (single _id index lookup).
        self_probe: Dict[str, Any] = {}
        try:
            samples = []
            for _ in range(3):
                t0 = time.perf_counter()
                await db.user_directory.estimated_document_count()
                samples.append(int((time.perf_counter() - t0) * 1000))
            samples.sort()
            self_probe = {
                "p50_ms": samples[len(samples) // 2],
                "max_ms": max(samples),
                "samples_ms": samples,
            }
        except Exception as e:
            self_probe = {"error": str(e)}

        # ── recent error count from session log (audit_events kinds) ──
        # Optional best-effort. Skip if collection missing.
        recent_errors: Dict[str, Any] = {"by_kind": {}}
        try:
            since = datetime.now(timezone.utc).timestamp() - 3600  # last hour
            cursor = db.audit_events.find(
                {"at": {"$gte": datetime.fromtimestamp(since, tz=timezone.utc).isoformat()}},
                {"_id": 0, "kind": 1},
            ).limit(2000)
            kinds: Dict[str, int] = {}
            async for doc in cursor:
                k = (doc.get("kind") or "unknown")
                if "error" in k.lower() or "fail" in k.lower() or "5xx" in k.lower():
                    kinds[k] = kinds.get(k, 0) + 1
            recent_errors = {"by_kind": kinds, "window_minutes": 60}
        except Exception as e:
            recent_errors = {"error": str(e)}

        # ── scheduler heartbeat (best-effort) ──────────────────────
        scheduler: Dict[str, Any] = {}
        try:
            # Module-level state published by the backup scheduler loop.
            from server import _BACKUP_SCHEDULER_STATE  # type: ignore
            scheduler = {
                "alive": _BACKUP_SCHEDULER_STATE.get("alive", False),
                "last_attempt_outcome": (
                    str(_BACKUP_SCHEDULER_STATE.get("last_attempt_outcome", ""))[:200]
                ),
            }
        except Exception:
            scheduler = {"alive": None, "note": "scheduler state not available"}

        # ── env / build identity ──────────────────────────────────
        env = {
            "env": os.environ.get("MASCI_ENV", "preview"),
            "release": os.environ.get("SENTRY_RELEASE", "unknown")[:16],
            "python": platform.python_version(),
            "node": platform.node(),
        }

        # ── overall ────────────────────────────────────────────────
        overall = "ok"
        try:
            if disk.get("percent", 0) >= 90:
                overall = "warn"
            if disk.get("percent", 0) >= 95:
                overall = "error"
            if memory.get("percent", 0) >= 90:
                overall = "warn"
            if memory.get("percent", 0) >= 95:
                overall = "error"
            if not mongo.get("ok", False):
                overall = "error"
        except Exception:
            pass

        return {
            "overall": overall,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "disk": disk,
            "memory": memory,
            "uptime": uptime,
            "mongo": mongo,
            "self_probe": self_probe,
            "recent_errors": recent_errors,
            "scheduler": scheduler,
            "env": env,
        }

    app.include_router(router)


__all__ = ["register_perf_snapshot_routes"]

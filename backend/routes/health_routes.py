"""
routes/health_routes.py — iter437 · Phase IV-BETA.5A-P5D · Safe route extraction.

Lifts the two TRIVIAL health-check endpoints out of server.py.

  GET /api/health   → liveness check used by ops dashboards
  GET /api/healthz  → ultra-minimal liveness for k8s-style probes

The deeper endpoints (`/api/health/full`, `/api/version`) depend on
internal scheduler state and version-detection helpers that haven't
been catalogued for extraction yet — they STAY in server.py per the
iter437 IV-BETA.5A-P4B safety discipline.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter


def build_health_router() -> APIRouter:
    router = APIRouter(prefix="/api", tags=["health"])

    @router.get("/health")
    def api_health():
        return {
            "ok": True,
            "service": "masci-hub",
            "ts": datetime.now(timezone.utc).isoformat(),
        }

    @router.get("/healthz")
    def api_healthz():
        return {"ok": True}

    return router


__all__ = ["build_health_router"]

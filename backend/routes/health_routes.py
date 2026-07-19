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

from fastapi import APIRouter, Request, Response

from lib.runtime_reliability import public_liveness_headers, public_readiness_payload
from lib.runtime_identity import runtime_identity_public_payload


def build_health_router() -> APIRouter:
    router = APIRouter(prefix="/api", tags=["health"])

    @router.get("/health")
    def api_health(request: Request, response: Response):
        for key, value in public_liveness_headers(request.app).items():
            if value:
                response.headers[key] = value
        bundle = getattr(getattr(request, "app", None).state, "runtime_identity_bundle", None)
        runtime_identity = runtime_identity_public_payload(bundle) if bundle else None
        return {
            "ok": True,
            "service": "masci-hub",
            "ts": datetime.now(timezone.utc).isoformat(),
            "runtime_identity": {
                "status": (runtime_identity or {}).get("status", "UNVERIFIABLE"),
                "valid": (runtime_identity or {}).get("valid", False),
                "mismatch_category": (runtime_identity or {}).get("mismatch_category"),
            },
        }

    @router.get("/healthz")
    def api_healthz(request: Request, response: Response):
        for key, value in public_liveness_headers(request.app).items():
            if value:
                response.headers[key] = value
        return {"ok": True}

    @router.get("/ready")
    def api_ready(request: Request, response: Response):
        payload = public_readiness_payload(request.app)
        for key, value in public_liveness_headers(request.app).items():
            if value:
                response.headers[key] = value
        if not payload["ok"]:
            response.status_code = 503
        return payload

    return router


__all__ = ["build_health_router"]

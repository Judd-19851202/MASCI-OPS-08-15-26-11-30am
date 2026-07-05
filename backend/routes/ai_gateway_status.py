"""AI-CONFIG-001 · Admin-only AI Gateway status route.

`GET /api/ai/gateway/status` — returns the resolved switchboard state
without leaking any secrets. Admin-gated.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from services.ai_gateway.capabilities import gateway_status_snapshot


def register_ai_gateway_status_routes(api_router: APIRouter, *, require_admin) -> None:
    @api_router.get("/ai/gateway/status")
    async def ai_gateway_status(_actor=Depends(require_admin)):
        """Return the sanitized AI Gateway switchboard state.

        Never includes raw API keys; only booleans indicating presence.
        Used by admin UI + supervisor console to confirm the config
        surface matches expectations before enabling AI for a tenant.
        """
        return gateway_status_snapshot()

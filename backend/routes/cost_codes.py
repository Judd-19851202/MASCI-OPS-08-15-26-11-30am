"""TRACK 23.1 · Cost Codes read-only HTTP endpoints.

Endpoints (all under ``/api/cost-codes``):
    GET /api/cost-codes/for-project?project_number=25-21
        → List[{code, description, active}]. Empty ⇒ UI hides selector.

Authentication: none required beyond the existing rate-limit envelope.
Cost-code lists are non-sensitive project metadata (public to any
supervisor with the portal); reads never expose PII.
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from services.cost_codes import get_provider


def register_cost_code_routes(api_router: APIRouter, db) -> None:
    provider = get_provider(db)

    @api_router.get("/cost-codes/for-project")
    async def cost_codes_for_project(project_number: str = "") -> Dict[str, Any]:
        codes: List[Dict[str, Any]] = await provider.list_for_project(project_number)
        return {
            "project_number": project_number,
            "provider": provider.name,
            "count": len(codes),
            "codes": codes,
        }


__all__ = ["register_cost_code_routes"]

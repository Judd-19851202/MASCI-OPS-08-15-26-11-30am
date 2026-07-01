"""Track 19.16 · Phase D · Executive Intelligence Center — HTTP routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from . import intelligence


def _err(status: int, code: str, detail: str = "") -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "detail": detail})


def register_intelligence_routes(api_router: APIRouter, db, *, require_actor) -> None:

    @api_router.get("/incident-intelligence/home")
    async def home(actor=Depends(require_actor)):
        return {
            "company_health": await intelligence.compute_company_health(db),
            "action_queue": await intelligence.compute_action_queue(db),
        }

    @api_router.get("/incident-intelligence/root-causes")
    async def rc(actor=Depends(require_actor)):
        return await intelligence.compute_root_cause_intelligence(db)

    @api_router.get("/incident-intelligence/corrective-actions")
    async def capa(actor=Depends(require_actor)):
        return await intelligence.compute_capa_intelligence(db)

    @api_router.get("/incident-intelligence/projects")
    async def projects(actor=Depends(require_actor)):
        return {"projects": await intelligence.compute_project_intelligence(db)}

    @api_router.get("/incident-intelligence/fleet")
    async def fleet(actor=Depends(require_actor)):
        return await intelligence.compute_fleet_intelligence(db)

    @api_router.get("/incident-intelligence/learning")
    async def learning(actor=Depends(require_actor)):
        return await intelligence.compute_learning_intelligence(db)

    @api_router.get("/incident-intelligence/heatmap")
    async def heatmap(actor=Depends(require_actor)):
        return await intelligence.compute_risk_heatmap(db)

    @api_router.get("/incident-intelligence/brief")
    async def brief(actor=Depends(require_actor)):
        return await intelligence.compute_executive_brief(db)


__all__ = ["register_intelligence_routes"]

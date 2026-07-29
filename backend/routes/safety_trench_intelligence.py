"""TRACK 23.10-D · Safety Portal Trench Intelligence HTTP surface.

Read-only. Safety + Admin only for company-wide + cleanup.
Safety/Admin for per-project (also PM for their own projects).

Endpoints
---------
GET /api/safety/company/trench-safety-kpis                  ?window=30d|7d|mtd|ptd
GET /api/safety/company/trench-safety-cleanup               ?limit=100
GET /api/safety/projects/{project_number}/trench-safety-kpis
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from lib.enterprise_governance import governance_project_scope_numbers

from services.safety_portal_trench import (
    company_trench_safety_kpis,
    project_trench_safety_kpis,
    cleanup_missing_ambiguous,
)


SAFETY_ADMIN_ROLES = {"safety", "admin"}
PM_ROLES = {"pm"}


def _role(actor: Dict[str, Any]) -> str:
    return (actor.get("_actor") or actor.get("role") or "").lower()


async def _pm_project_scope(db, actor: Dict[str, Any]) -> Optional[list]:
    """None = unrestricted (admin/safety). List = PM's projects."""
    if _role(actor) in SAFETY_ADMIN_ROLES:
        return None
    return await governance_project_scope_numbers(db, actor)


def build_safety_trench_intelligence_router(
    db, *, require_read_dep,
) -> APIRouter:
    r = APIRouter(prefix="/api", tags=["safety-trench-intelligence"])

    async def _authorize_company(actor: Dict[str, Any]) -> None:
        if _role(actor) not in SAFETY_ADMIN_ROLES:
            raise HTTPException(
                403,
                "Safety-portal company-wide trench view: Safety · Admin only",
            )

    async def _authorize_project(
        actor: Dict[str, Any], project_number: str,
    ) -> None:
        role = _role(actor)
        if role in SAFETY_ADMIN_ROLES:
            return
        if role in PM_ROLES:
            allowed = await _pm_project_scope(db, actor)
            if allowed is None or str(project_number) in (allowed or []):
                return
            raise HTTPException(403, "PM: not assigned to this project")
        raise HTTPException(
            403, "Trench per-project safety view: PM · Safety · Admin only",
        )

    @r.get("/safety/company/trench-safety-kpis")
    async def company_kpis(
        window: str = Query(default="30d", pattern="^(7d|30d|mtd|ptd)$"),
        actor: Dict[str, Any] = Depends(require_read_dep),
    ):
        await _authorize_company(actor)
        return await company_trench_safety_kpis(db, window=window)

    @r.get("/safety/company/trench-safety-cleanup")
    async def company_cleanup(
        limit: int = Query(default=100, ge=1, le=500),
        actor: Dict[str, Any] = Depends(require_read_dep),
    ):
        await _authorize_company(actor)
        return await cleanup_missing_ambiguous(db, limit=limit)

    @r.get("/safety/projects/{project_number}/trench-safety-kpis")
    async def project_kpis(
        project_number: str,
        actor: Dict[str, Any] = Depends(require_read_dep),
    ):
        await _authorize_project(actor, project_number)
        return await project_trench_safety_kpis(db, project_number)

    return r


__all__ = ["build_safety_trench_intelligence_router"]

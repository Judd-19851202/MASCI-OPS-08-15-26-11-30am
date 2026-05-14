"""
Integration Center · events.py — placeholder read endpoints for
Motive driver-safety events + MaintainX work orders.

Reads accept Safety / HR / Admin tokens via the multi-role gate so the
respective portals can render integration-ready cards TODAY without
any provider-specific auth knowledge.

Demo mode behaviour: when `integration_settings[provider].demo_mode`
is True, GET endpoints stitch in static demo records at the top of the
list so admins can take screenshots / show stakeholders what the
populated UI will look like once the API is wired.
"""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends

from ._storage import demo_motive_events, demo_maintainx_work_orders


async def _provider_demo_mode(db, provider: str) -> bool:
    doc = await db.integration_settings.find_one(
        {"provider": provider}, {"_id": 0, "demo_mode": 1},
    )
    return bool((doc or {}).get("demo_mode"))


def register_event_routes(
    api_router: APIRouter, db, require_safety_or_hr_or_admin,
) -> None:

    @api_router.get(
        "/integrations/motive/events",
        dependencies=[Depends(require_safety_or_hr_or_admin)],
    )
    async def list_motive_events(
        limit: int = 50,
        severity: Optional[str] = None,
        coaching_only: bool = False,
    ):
        q: dict = {"is_demo": {"$ne": True}}
        if severity:
            q["severity"] = severity
        if coaching_only:
            q["coaching_required"] = True
        limit = max(1, min(limit, 500))
        real = await db.motive_events.find(q, {"_id": 0}).sort("event_at", -1).to_list(limit)
        if await _provider_demo_mode(db, "motive"):
            demo = demo_motive_events()
            if severity:
                demo = [d for d in demo if d.get("severity") == severity]
            if coaching_only:
                demo = [d for d in demo if d.get("coaching_required")]
            return demo + real
        return real

    @api_router.get(
        "/integrations/maintainx/work-orders",
        dependencies=[Depends(require_safety_or_hr_or_admin)],
    )
    async def list_maintainx_work_orders(
        status: Optional[str] = None,
        priority: Optional[str] = None,
        safety_only: bool = False,
        equipment_down_only: bool = False,
        limit: int = 50,
    ):
        q: dict = {"is_demo": {"$ne": True}}
        if status:
            q["status"] = status
        if priority:
            q["priority"] = priority
        if safety_only:
            q["safety_related"] = True
        if equipment_down_only:
            q["equipment_down"] = True
        limit = max(1, min(limit, 500))
        real = await db.maintainx_work_orders.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)
        if await _provider_demo_mode(db, "maintainx"):
            demo = demo_maintainx_work_orders()
            if status:
                demo = [d for d in demo if d.get("status") == status]
            if priority:
                demo = [d for d in demo if d.get("priority") == priority]
            if safety_only:
                demo = [d for d in demo if d.get("safety_related")]
            if equipment_down_only:
                demo = [d for d in demo if d.get("equipment_down")]
            return demo + real
        return real


__all__ = ["register_event_routes"]

"""
routes/asset_spine.py · FORGEDOPS P0.1 · Canonical Asset Spine API.

Mounted via `register_asset_spine_routes(api_router, db, require_admin,
require_any_portal)`.

Surface:
  GET  /api/asset-spine/assets                       list (any portal)
  GET  /api/asset-spine/assets/{asset_id}            single (any portal)
  GET  /api/asset-spine/assets/{asset_id}/profile    fused profile (any portal)
  POST /api/asset-spine/assets                       create (admin only)
  PATCH /api/asset-spine/assets/{asset_id}           update (admin only)
  POST /api/asset-spine/assets/{asset_id}/retire     retire (admin only)
  POST /api/asset-spine/assets/{asset_id}/activate   reactivate (admin only)

  GET  /api/asset-spine/health                       live counts (admin)
  POST /api/asset-spine/health/scan                  run detectors (admin)
  GET  /api/asset-spine/health/runs                  recent scan rows (admin)
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

from services.asset_spine import AssetSpine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic shapes (input only — output uses the canonical projector)
# ---------------------------------------------------------------------------

class AssetCreate(BaseModel):
    asset_number: str = Field(..., min_length=1, max_length=64)
    asset_name: Optional[str] = None
    asset_type: Optional[str] = None
    asset_category: Optional[str] = None
    asset_status: Optional[str] = "ACTIVE"
    ownership: Optional[str] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None
    manufacturer: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    serial_number: Optional[str] = None
    vin: Optional[str] = None
    license_plate: Optional[str] = None
    motive_asset_id: Optional[str] = None
    fleetwatcher_asset_id: Optional[str] = None
    maintainx_asset_id: Optional[str] = None
    purchase_date: Optional[str] = None
    in_service_date: Optional[str] = None


class AssetUpdate(BaseModel):
    asset_name: Optional[str] = None
    asset_type: Optional[str] = None
    asset_category: Optional[str] = None
    asset_status: Optional[str] = None
    ownership: Optional[str] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None
    manufacturer: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    serial_number: Optional[str] = None
    vin: Optional[str] = None
    license_plate: Optional[str] = None
    motive_asset_id: Optional[str] = None
    fleetwatcher_asset_id: Optional[str] = None
    maintainx_asset_id: Optional[str] = None
    purchase_date: Optional[str] = None
    in_service_date: Optional[str] = None
    assigned_driver_id: Optional[str] = None
    assigned_supervisor_id: Optional[str] = None
    assigned_dispatcher_id: Optional[str] = None
    current_location: Optional[str] = None


class RetireBody(BaseModel):
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def register_asset_spine_routes(
    api_router_or_app,
    db,
    require_admin_dep: Callable,
    require_any_portal_dep: Callable,
) -> APIRouter:
    """
    Register routes. Works whether the caller passes the parent
    `api_router` (early-init pattern) or directly the `app` (late-init
    pattern, post `app.include_router(api_router)`). The route prefix is
    `/api/asset-spine/*` either way.
    """
    # Detect: api_router has `prefix`, app does not.
    parent_has_prefix = hasattr(api_router_or_app, "prefix") and getattr(api_router_or_app, "prefix", "") == "/api"
    router_prefix = "/asset-spine" if parent_has_prefix else "/api/asset-spine"
    router = APIRouter(prefix=router_prefix, tags=["asset-spine"])

    def _actor_of(operator) -> str:
        if isinstance(operator, dict):
            return str(operator.get("email") or operator.get("id") or "admin")
        if isinstance(operator, str):
            return operator
        return "admin"

    # ----- READ -------------------------------------------------------------

    @router.get("/assets")
    async def list_assets(
        active_only: bool = Query(True),
        type: Optional[str] = Query(None, alias="type"),
        search: Optional[str] = Query(None),
        limit: int = Query(200, ge=1, le=1000),
        skip: int = Query(0, ge=0),
        _: Any = Depends(require_any_portal_dep),
    ):
        spine = AssetSpine(db)
        items = await spine.list_assets(
            active_only=active_only,
            asset_type=type,
            search=search,
            limit=limit,
            skip=skip,
        )
        return {"count": len(items), "items": items}

    @router.get("/assets/{asset_id}")
    async def get_asset(
        asset_id: str = Path(...),
        _: Any = Depends(require_any_portal_dep),
    ):
        spine = AssetSpine(db)
        a = await spine.get_asset(asset_id)
        if not a:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        return a

    @router.get("/assets/{asset_id}/profile")
    async def get_profile(
        asset_id: str = Path(...),
        _: Any = Depends(require_any_portal_dep),
    ):
        spine = AssetSpine(db)
        p = await spine.get_profile(asset_id)
        if not p:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        return p

    # ----- WRITE (admin only, audited) -------------------------------------

    @router.post("/assets")
    async def create_asset(
        body: AssetCreate,
        operator=Depends(require_admin_dep),
    ):
        spine = AssetSpine(db)
        try:
            a = await spine.create_asset(body.dict(exclude_none=True), actor=_actor_of(operator))
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))
        return a

    @router.patch("/assets/{asset_id}")
    async def update_asset(
        asset_id: str,
        body: AssetUpdate,
        operator=Depends(require_admin_dep),
    ):
        spine = AssetSpine(db)
        a = await spine.update_asset(asset_id, body.dict(exclude_none=True), actor=_actor_of(operator))
        if a is None:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        return a

    @router.post("/assets/{asset_id}/retire")
    async def retire_asset(
        asset_id: str,
        body: RetireBody,
        operator=Depends(require_admin_dep),
    ):
        spine = AssetSpine(db)
        a = await spine.retire_asset(asset_id, actor=_actor_of(operator), reason=body.reason)
        if a is None:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        return a

    @router.post("/assets/{asset_id}/activate")
    async def activate_asset(
        asset_id: str,
        body: RetireBody,
        operator=Depends(require_admin_dep),
    ):
        spine = AssetSpine(db)
        a = await spine.activate_asset(asset_id, actor=_actor_of(operator), reason=body.reason)
        if a is None:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        return a

    # ----- HEALTH ----------------------------------------------------------

    @router.get("/health")
    async def health(operator=Depends(require_admin_dep)):
        spine = AssetSpine(db)
        return await spine.health()

    @router.post("/health/scan")
    async def health_scan(operator=Depends(require_admin_dep)):
        spine = AssetSpine(db)
        run = await spine.scan_health(actor=_actor_of(operator))
        # Strip the heavy `findings` array from the summary; consumers
        # can pull the full row via /health/runs/{id}.
        return {
            "id": run["id"],
            "at": run["at"],
            "actor": run["actor"],
            "findings_summary": run["findings_summary"],
        }

    @router.get("/health/runs")
    async def health_runs(
        limit: int = Query(20, ge=1, le=200),
        operator=Depends(require_admin_dep),
    ):
        cur = db.asset_spine_health_runs.find({}, {"_id": 0}).sort("at", -1).limit(limit)
        items = []
        async for d in cur:
            items.append(d)
        return {"count": len(items), "items": items}

    api_router_or_app.include_router(router)
    return router

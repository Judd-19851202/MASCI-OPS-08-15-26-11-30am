"""Trench Safety hold lifecycle — Phase 4B.

Routes registered here:
  GET  /api/trench-safety/assets/{ident}/holds
  POST /api/trench-safety/assets/{ident}/holds   (open)
  POST /api/trench-safety/holds/{hold_id}/clear

The trench_safety_holds collection is history/audit only. The single
source of truth for state remains asset.operational_status, derived
from the hold engine resolver in _helpers.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ._helpers import clear_hold, open_hold
from ._models import HOLD_KINDS, HoldClearBody, HoldOpenBody


def register_hold_routes(
    api_router: APIRouter,
    db,
    *,
    require_safety_or_admin,
    require_any_portal,
) -> None:
    LIST_PATH = "/trench-safety/assets/{ident}/holds"
    CLEAR_PATH = "/trench-safety/holds/{hold_id}/clear"

    @api_router.get(LIST_PATH)
    async def list_holds(
        ident: str,
        active_only: bool = Query(default=False),
        limit: int = Query(default=200, ge=1, le=1000),
        _actor: dict = Depends(require_any_portal),
    ):
        asset = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]},
            {"_id": 0, "asset_id": 1},
        )
        if not asset:
            raise HTTPException(404, "Trench safety asset not found")
        q: Dict[str, Any] = {"asset_id": asset["asset_id"]}
        if active_only:
            q["is_active"] = True
        cursor = (
            db.trench_safety_holds.find(q, {"_id": 0})
            .sort("opened_at", -1)
            .limit(limit)
        )
        return {"items": await cursor.to_list(limit)}

    @api_router.post(LIST_PATH)
    async def open_hold_endpoint(
        ident: str,
        body: HoldOpenBody,
        actor: dict = Depends(require_safety_or_admin),
    ):
        if body.kind not in HOLD_KINDS:
            raise HTTPException(
                422, f"kind must be one of {list(HOLD_KINDS)}"
            )
        asset = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]},
            {"_id": 0, "asset_id": 1},
        )
        if not asset:
            raise HTTPException(404, "Trench safety asset not found")
        actor_email = (actor or {}).get("email") or (actor or {}).get("_actor") or "unknown"
        hold = await open_hold(
            db,
            asset_id=asset["asset_id"],
            kind=body.kind,
            reason=body.reason,
            source=body.source,
            source_ref=body.source_ref,
            opened_by=actor_email,
        )
        fresh = await db.trench_safety_assets.find_one(
            {"asset_id": asset["asset_id"]}, {"_id": 0}
        )
        return {"hold": hold, "asset": fresh}

    @api_router.post(CLEAR_PATH)
    async def clear_hold_endpoint(
        hold_id: str,
        body: HoldClearBody,
        actor: dict = Depends(require_safety_or_admin),
    ):
        hold = await db.trench_safety_holds.find_one({"id": hold_id}, {"_id": 0})
        if not hold:
            raise HTTPException(404, "Hold not found")
        if not hold.get("is_active"):
            raise HTTPException(409, "Hold is already cleared")
        actor_email = (actor or {}).get("email") or (actor or {}).get("_actor") or "unknown"
        cleared = await clear_hold(
            db,
            asset_id=hold["asset_id"],
            kind=hold["kind"],
            clear_reason=body.clear_reason,
            clear_source=body.clear_source,
            cleared_by=actor_email,
        )
        fresh = await db.trench_safety_assets.find_one(
            {"asset_id": hold["asset_id"]}, {"_id": 0}
        )
        return {"hold": cleared, "asset": fresh}

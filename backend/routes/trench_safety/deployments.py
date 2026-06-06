"""Deployment (project assignment / return) endpoints."""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ._helpers import (
    now_iso,
    upsert_equipment_master_mirror,
    write_audit,
)
from ._models import DEPLOYMENT_SOURCES, DeploymentAssign, DeploymentReturn


def register_deployment_routes(
    api_router: APIRouter,
    db,
    *,
    require_any_portal,
) -> None:
    LIST_PATH = "/trench-safety/assets/{ident}/deployments"
    ASSIGN_PATH = "/trench-safety/assets/{ident}/assign"
    RETURN_PATH = "/trench-safety/assets/{ident}/return"

    # List deployment history
    @api_router.get(LIST_PATH)
    async def list_deployments(
        ident: str,
        limit: int = Query(default=100, ge=1, le=500),
        _actor: dict = Depends(require_any_portal),
    ):
        asset = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]},
            {"_id": 0, "asset_id": 1},
        )
        if not asset:
            raise HTTPException(404, "Trench safety asset not found")

        cursor = (
            db.trench_safety_deployments
            .find({"asset_id": asset["asset_id"]}, {"_id": 0})
            .sort("assigned_at", -1)
            .limit(limit)
        )
        return {"items": await cursor.to_list(limit)}

    # Assign asset to a project — open to any portal token that touches
    # the field (PM, Safety, Admin, Dispatch, Shop, FL all may need
    # this depending on the source). The transition itself is gated by
    # status rules (Inspection Hold / Repair / Retired block).
    @api_router.post(ASSIGN_PATH)
    async def assign_to_project(
        ident: str,
        payload: DeploymentAssign,
        actor: dict = Depends(require_any_portal),
    ):
        if payload.source not in DEPLOYMENT_SOURCES:
            raise HTTPException(
                422,
                f"source must be one of {list(DEPLOYMENT_SOURCES)}",
            )

        asset = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]},
            {"_id": 0},
        )
        if not asset:
            raise HTTPException(404, "Trench safety asset not found")

        if asset.get("operational_status") in {"Inspection Hold", "Maintenance Hold", "Safety Hold", "Certification Hold", "Retired"}:
            raise HTTPException(
                409,
                f"asset is {asset.get('operational_status')} — clear before assigning",
            )

        # Close any open deployment for this asset before opening a new one
        await db.trench_safety_deployments.update_many(
            {"asset_id": asset["asset_id"], "returned_at": None},
            {"$set": {
                "returned_at": now_iso(),
                "returned_by": payload.assigned_by or "auto-superseded",
                "auto_returned": True,
            }},
        )

        actor_email = (actor or {}).get("email") or (actor or {}).get("_actor") or "unknown"
        doc = {
            "id": str(uuid.uuid4()),
            "asset_id": asset["asset_id"],
            "asset_uuid": asset["id"],
            "project_id": payload.project_id,
            "project_name": payload.project_name,
            "project_number": payload.project_number,
            "superintendent": payload.superintendent,
            "foreman": payload.foreman,
            "assigned_by": payload.assigned_by or actor_email,
            "assigned_at": now_iso(),
            "returned_by": None,
            "returned_at": None,
            "condition_at_assign": payload.condition_at_assign or asset.get("condition"),
            "condition_at_return": None,
            "source": payload.source,
            "notes": payload.notes,
        }
        await db.trench_safety_deployments.insert_one(doc)
        doc.pop("_id", None)

        await db.trench_safety_assets.update_one(
            {"id": asset["id"]},
            {"$set": {
                "operational_status": "Assigned",
                "current_project_id": payload.project_id,
                "current_project_name": payload.project_name,
                "current_project_number": payload.project_number,
                "current_superintendent": payload.superintendent,
                "current_foreman": payload.foreman,
                "current_location": payload.project_name,
                "updated_at": now_iso(),
                "updated_by": actor_email,
            }},
        )
        fresh = await db.trench_safety_assets.find_one(
            {"id": asset["id"]}, {"_id": 0}
        )
        await upsert_equipment_master_mirror(db, fresh)
        await write_audit(
            db, kind="trench_asset_assigned", asset_id=asset["asset_id"],
            actor=actor, detail={
                "deployment_id": doc["id"],
                "project_id": payload.project_id,
                "project_name": payload.project_name,
                "project_number": payload.project_number,
                "superintendent": payload.superintendent,
                "foreman": payload.foreman,
                "source": payload.source,
            },
        )
        return {"deployment": doc, "asset": fresh}

    # Return asset to yard
    @api_router.post(RETURN_PATH)
    async def return_from_project(
        ident: str,
        payload: DeploymentReturn,
        actor: dict = Depends(require_any_portal),
    ):
        asset = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]},
            {"_id": 0},
        )
        if not asset:
            raise HTTPException(404, "Trench safety asset not found")

        actor_email = (actor or {}).get("email") or (actor or {}).get("_actor") or "unknown"

        open_dep = await db.trench_safety_deployments.find_one(
            {"asset_id": asset["asset_id"], "returned_at": None},
            {"_id": 0},
        )
        if open_dep:
            await db.trench_safety_deployments.update_one(
                {"id": open_dep["id"]},
                {"$set": {
                    "returned_at": now_iso(),
                    "returned_by": payload.returned_by or actor_email,
                    "condition_at_return": payload.condition_at_return,
                    "notes_on_return": payload.notes,
                }},
            )

        # Asset returns to highest remaining hold via the resolver; if no
        # holds, falls back to Available.
        HOLD_STATUSES = {
            "Inspection Hold", "Maintenance Hold",
            "Safety Hold", "Certification Hold",
        }
        cur_status = asset.get("operational_status")
        new_status = cur_status if cur_status in HOLD_STATUSES or cur_status == "Retired" else "Available"
        update = {
            "operational_status": new_status,
            "current_project_id": None,
            "current_project_name": None,
            "current_project_number": None,
            "current_superintendent": None,
            "current_foreman": None,
            "current_location": asset.get("yard_location") or "MASCI Yard",
            "updated_at": now_iso(),
            "updated_by": actor_email,
        }
        if payload.condition_at_return:
            update["condition"] = payload.condition_at_return

        await db.trench_safety_assets.update_one(
            {"id": asset["id"]}, {"$set": update}
        )
        fresh = await db.trench_safety_assets.find_one(
            {"id": asset["id"]}, {"_id": 0}
        )
        await upsert_equipment_master_mirror(db, fresh)
        await write_audit(
            db, kind="trench_asset_returned", asset_id=asset["asset_id"],
            actor=actor, detail={
                "deployment_id": open_dep["id"] if open_dep else None,
                "status_after": new_status,
                "condition_at_return": payload.condition_at_return,
            },
        )
        return {"asset": fresh}

"""Repair lifecycle endpoints — Shop owns these, Admin can also act."""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ._helpers import (
    apply_resolved_status,
    clear_hold,
    has_open_repair,
    now_iso,
    open_hold,
    upsert_equipment_master_mirror,
    write_audit,
)
from ._models import REPAIR_STATUSES, RepairCreate, RepairUpdate


def register_repair_routes(
    api_router: APIRouter,
    db,
    *,
    require_shop_or_admin,
    require_safety_or_admin,
    require_any_portal,
) -> None:
    LIST_PATH = "/trench-safety/assets/{ident}/repairs"
    ITEM_PATH = "/trench-safety/repairs/{repair_id}"

    # List repairs for an asset
    @api_router.get(LIST_PATH)
    async def list_repairs(
        ident: str,
        status: Optional[str] = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
        _actor: dict = Depends(require_any_portal),
    ):
        asset = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]},
            {"_id": 0, "asset_id": 1},
        )
        if not asset:
            raise HTTPException(404, "Trench safety asset not found")

        q: Dict[str, Any] = {"asset_id": asset["asset_id"]}
        if status:
            q["status"] = status

        cursor = (
            db.trench_safety_repairs.find(q, {"_id": 0})
            .sort("opened_at", -1)
            .limit(limit)
        )
        return {"items": await cursor.to_list(limit)}

    # Open a repair (Shop or Admin)
    @api_router.post(LIST_PATH)
    async def open_repair(
        ident: str,
        payload: RepairCreate,
        actor: dict = Depends(require_shop_or_admin),
    ):
        asset = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]},
            {"_id": 0},
        )
        if not asset:
            raise HTTPException(404, "Trench safety asset not found")

        # Resolve actor regardless of shape (require_shop_or_admin returns a dict
        # for shop users, may be a bool/scope for admin path)
        actor_email = _extract_actor_email(actor)
        doc = {
            "id": str(uuid.uuid4()),
            "asset_id": asset["asset_id"],
            "asset_uuid": asset["id"],
            "status": "Open",
            "issue_description": payload.issue_description,
            "reported_by": payload.reported_by or actor_email,
            "photo_refs": list(payload.photo_refs),
            "repair_vendor": payload.repair_vendor,
            "repair_cost": payload.repair_cost,
            "completion_notes": "",
            "requires_reinspection": bool(payload.requires_reinspection),
            "opened_at": now_iso(),
            "opened_by": actor_email,
            "closed_at": None,
            "closed_by": None,
        }
        await db.trench_safety_repairs.insert_one(doc)
        doc.pop("_id", None)

        # Move asset to Maintenance Hold via the hold engine (unless retired)
        if asset.get("operational_status") != "Retired":
            await open_hold(
                db, asset_id=asset["asset_id"], kind="Maintenance Hold",
                reason=f"Repair opened: {payload.issue_description[:200]}",
                source="repair", source_ref=f"repair:{doc['id']}",
                opened_by=actor_email,
            )
            await db.trench_safety_assets.update_one(
                {"id": asset["id"]},
                {"$set": {
                    "last_repair_at": doc["opened_at"],
                    "updated_at": now_iso(),
                    "updated_by": actor_email,
                }},
            )
            fresh = await db.trench_safety_assets.find_one(
                {"id": asset["id"]}, {"_id": 0}
            )
        else:
            fresh = asset

        await write_audit(
            db, kind="trench_asset_repair_opened", asset_id=asset["asset_id"],
            actor={"_actor": "shop", "email": actor_email},
            detail={"repair_id": doc["id"]},
        )
        return {"repair": doc, "asset": fresh}

    # Update repair (Shop or Admin)
    @api_router.patch(ITEM_PATH)
    async def update_repair(
        repair_id: str,
        payload: RepairUpdate,
        actor: dict = Depends(require_shop_or_admin),
    ):
        existing = await db.trench_safety_repairs.find_one(
            {"id": repair_id}, {"_id": 0}
        )
        if not existing:
            raise HTTPException(404, "Repair not found")
        if existing.get("status") == "Completed":
            raise HTTPException(409, "Repair is already Completed")

        update = {k: v for k, v in payload.model_dump().items() if v is not None}
        if "status" in update and update["status"] not in REPAIR_STATUSES:
            raise HTTPException(422, f"status must be one of {list(REPAIR_STATUSES)}")
        if not update:
            return existing

        actor_email = _extract_actor_email(actor)
        update["updated_at"] = now_iso()
        update["updated_by"] = actor_email

        await db.trench_safety_repairs.update_one(
            {"id": repair_id}, {"$set": update}
        )
        fresh_repair = await db.trench_safety_repairs.find_one(
            {"id": repair_id}, {"_id": 0}
        )
        await write_audit(
            db, kind="trench_asset_repair_updated",
            asset_id=existing["asset_id"],
            actor={"_actor": "shop", "email": actor_email},
            detail={"repair_id": repair_id, "fields": sorted(update.keys())},
        )
        return fresh_repair

    # Complete a repair (Shop or Admin)
    @api_router.post(ITEM_PATH + "/complete")
    async def complete_repair(
        repair_id: str,
        actor: dict = Depends(require_shop_or_admin),
    ):
        existing = await db.trench_safety_repairs.find_one(
            {"id": repair_id}, {"_id": 0}
        )
        if not existing:
            raise HTTPException(404, "Repair not found")
        if existing.get("status") == "Completed":
            return existing

        asset = await db.trench_safety_assets.find_one(
            {"asset_id": existing["asset_id"]}, {"_id": 0}
        )
        if not asset:
            raise HTTPException(404, "Trench safety asset not found")

        actor_email = _extract_actor_email(actor)
        await db.trench_safety_repairs.update_one(
            {"id": repair_id},
            {"$set": {
                "status": "Completed",
                "closed_at": now_iso(),
                "closed_by": actor_email,
                "updated_at": now_iso(),
                "updated_by": actor_email,
            }},
        )
        fresh_repair = await db.trench_safety_repairs.find_one(
            {"id": repair_id}, {"_id": 0}
        )

        # Decide new asset status via the hold engine:
        any_other_open = bool(
            await db.trench_safety_repairs.find_one(
                {
                    "asset_id": asset["asset_id"],
                    "id": {"$ne": repair_id},
                    "status": {"$in": ["Open", "In Progress"]},
                },
                {"_id": 0, "id": 1},
            )
        )
        if not any_other_open:
            # All repairs closed → clear Maintenance Hold
            await clear_hold(
                db, asset_id=asset["asset_id"], kind="Maintenance Hold",
                clear_reason="All open repairs completed",
                clear_source="repair_completed", cleared_by=actor_email,
            )
        # If this repair requires reinspection → open Inspection Hold
        if fresh_repair.get("requires_reinspection"):
            await open_hold(
                db, asset_id=asset["asset_id"], kind="Inspection Hold",
                reason=f"Reinspection required after repair {repair_id}",
                source="repair", source_ref=f"repair:{repair_id}",
                opened_by=actor_email,
            )

        # Recompute final operational_status from the hold engine.
        fresh_asset = await apply_resolved_status(db, asset["asset_id"], actor_email)
        new_status = fresh_asset.get("operational_status")
        await write_audit(
            db, kind="trench_asset_repair_completed",
            asset_id=asset["asset_id"],
            actor={"_actor": "shop", "email": actor_email},
            detail={
                "repair_id": repair_id,
                "status_after": new_status,
                "requires_reinspection": fresh_repair.get("requires_reinspection"),
            },
        )
        return {"repair": fresh_repair, "asset": fresh_asset}


def _extract_actor_email(actor: Any) -> str:
    if isinstance(actor, dict):
        return actor.get("email") or actor.get("_actor") or actor.get("role") or "shop"
    return "shop_or_admin"

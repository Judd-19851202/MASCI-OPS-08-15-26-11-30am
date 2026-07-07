"""Trench-safety asset CRUD + lifecycle endpoints."""
from __future__ import annotations

from lib.mongo_query import safe_regex

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ._helpers import (
    now_iso,
    upsert_equipment_master_mirror,
    validate_status_transition,
    write_audit,
)
from ._models import (
    CONDITIONS,
    OPERATIONAL_STATUSES,
    RetireAssetBody,
    StatusChangeBody,
    TrenchSafetyAssetCreate,
    TrenchSafetyAssetUpdate,
)


def register_asset_routes(
    api_router: APIRouter,
    db,
    *,
    require_admin,
    require_safety_or_admin,
    require_any_portal,
) -> None:
    PREFIX = "/trench-safety/assets"

    # ──────────────────────────────────────────────────────────────────
    # List
    # ──────────────────────────────────────────────────────────────────
    @api_router.get(PREFIX)
    async def list_assets(
        asset_type: Optional[str] = Query(default=None),
        operational_status: Optional[str] = Query(default=None),
        condition: Optional[str] = Query(default=None),
        project_id: Optional[str] = Query(default=None),
        needs_review: Optional[bool] = Query(default=None),
        include_retired: bool = Query(default=False),
        q: Optional[str] = Query(default=None),
        _actor: dict = Depends(require_any_portal),
    ):
        query: Dict[str, Any] = {}
        if asset_type:
            query["asset_type"] = asset_type
        if operational_status:
            query["operational_status"] = operational_status
        if condition:
            query["condition"] = condition
        if project_id:
            query["current_project_id"] = project_id
        if needs_review is not None:
            query["needs_review"] = needs_review
        if not include_retired:
            query["is_active"] = True
        if q:
            esc = safe_regex(q)
            query["$or"] = [
                {"asset_id": esc},
                {"manufacturer": esc},
                {"model": esc},
                {"serial_number": esc},
                {"size": esc},
                {"color": esc},
                {"current_location": esc},
                {"current_project_name": esc},
                # Phase 8B — extend search to QR code value + Road Plate
                # markings so a crew can find a plate by its label too.
                {"qr_code_value": esc},
                {"markings": esc},
                {"current_project_number": esc},
            ]

        docs = (
            await db.trench_safety_assets
            .find(query, {"_id": 0})
            .sort("asset_id", 1)
            .to_list(2000)
        )
        return {"items": docs, "count": len(docs)}

    # ──────────────────────────────────────────────────────────────────
    # Phase 8A — Suggest next available asset_id for a given asset type.
    # Used by the New Asset dialog (Road Plate → RP-001/RP-002, Trench
    # Box → TB-XX, etc.). Permanent, never-reused numbering controls —
    # walks the existing collection (active + retired) to find the next
    # free integer. Does NOT mutate state; safe to call repeatedly.
    # ──────────────────────────────────────────────────────────────────
    @api_router.get("/trench-safety/assets/next-id")
    async def suggest_next_id(
        asset_type: str = Query(default="Road Plate"),
        _actor: dict = Depends(require_safety_or_admin),
    ):
        # Map type → asset_id prefix. Permanent, never reused.
        prefix_map = {
            "Road Plate": "RP",
            "Trench Box": "TB",
            "End Panel": "EP",
            "Spreader Bar": "SP",
            "Hydraulic Shore": "HS",
            "Slide Rail System": "SR",
            "Trench Jack": "TJ",
            "Ladder": "LD",
            "Accessory": "AC",
        }
        prefix = prefix_map.get(asset_type, "AS")
        # Look at ALL rows (active + retired) so we never reuse a number.
        cursor = db.trench_safety_assets.find(
            {"asset_id": {"$regex": f"^{prefix}-"}},
            {"_id": 0, "asset_id": 1},
        )
        used: set[int] = set()
        async for d in cursor:
            tail = (d.get("asset_id") or "").split("-", 1)[-1]
            try:
                used.add(int(tail))
            except ValueError:
                continue
        n = 1
        while n in used:
            n += 1
        # 3-digit zero-padding for Road Plate (RP-001) per directive.
        # Keep Trench Box at 2-digit (TB-01) to preserve historical
        # numbering.
        pad = 2 if prefix == "TB" else 3
        return {
            "asset_type": asset_type,
            "prefix": prefix,
            "next_id": f"{prefix}-{str(n).zfill(pad)}",
            "next_number": n,
        }

    # ──────────────────────────────────────────────────────────────────
    # Get by asset_id (preferred) OR by uuid
    # ──────────────────────────────────────────────────────────────────
    @api_router.get(PREFIX + "/{ident}")
    async def get_asset(
        ident: str,
        _actor: dict = Depends(require_any_portal),
    ):
        doc = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]},
            {"_id": 0},
        )
        if not doc:
            raise HTTPException(404, "Trench safety asset not found")
        return doc

    # ──────────────────────────────────────────────────────────────────
    # Create (Admin + Safety)
    # ──────────────────────────────────────────────────────────────────
    @api_router.post(PREFIX)
    async def create_asset(
        payload: TrenchSafetyAssetCreate,
        actor: dict = Depends(require_safety_or_admin),
    ):
        # Validate enums upfront — clean 422 instead of corrupt write
        if payload.condition not in CONDITIONS:
            raise HTTPException(422, f"condition must be one of {list(CONDITIONS)}")
        if payload.operational_status not in OPERATIONAL_STATUSES:
            raise HTTPException(422, f"operational_status must be one of {list(OPERATIONAL_STATUSES)}")

        existing = await db.trench_safety_assets.find_one(
            {"asset_id": payload.asset_id}, {"_id": 0, "id": 1}
        )
        if existing:
            raise HTTPException(409, f"asset_id {payload.asset_id} already exists")

        actor_email = (actor or {}).get("email") or (actor or {}).get("_actor") or "unknown"
        doc = payload.model_dump()
        doc.update({
            "id": str(uuid.uuid4()),
            "asset_category": "Trench Safety",
            "qr_code_value": payload.asset_id,
            "qr_url": f"/trench-safety/assets/{payload.asset_id}",
            "tabulated_data_file_id": None,
            "tabulated_data_filename": "",
            "tabulated_data_missing": True,
            "last_inspection_at": None,
            "next_inspection_due": None,
            "last_repair_at": None,
            "certification_expires_at": None,
            "is_active": True,
            "retired_at": None,
            "retired_reason": None,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "created_by": actor_email,
            "updated_by": actor_email,
        })

        await db.trench_safety_assets.insert_one(doc)
        doc.pop("_id", None)
        await upsert_equipment_master_mirror(db, doc)
        await write_audit(
            db, kind="trench_asset_created", asset_id=doc["asset_id"],
            actor=actor, detail={"asset_type": doc["asset_type"]},
        )
        return doc

    # ──────────────────────────────────────────────────────────────────
    # Update (Admin + Safety) — asset_id is IMMUTABLE
    # ──────────────────────────────────────────────────────────────────
    @api_router.put(PREFIX + "/{ident}")
    async def update_asset(
        ident: str,
        payload: TrenchSafetyAssetUpdate,
        actor: dict = Depends(require_safety_or_admin),
    ):
        existing = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]},
            {"_id": 0},
        )
        if not existing:
            raise HTTPException(404, "Trench safety asset not found")

        update = {k: v for k, v in payload.model_dump().items() if v is not None}
        if "condition" in update and update["condition"] not in CONDITIONS:
            raise HTTPException(422, f"condition must be one of {list(CONDITIONS)}")
        if not update:
            return existing

        actor_email = (actor or {}).get("email") or (actor or {}).get("_actor") or "unknown"
        update["updated_at"] = now_iso()
        update["updated_by"] = actor_email

        await db.trench_safety_assets.update_one({"id": existing["id"]}, {"$set": update})
        fresh = await db.trench_safety_assets.find_one({"id": existing["id"]}, {"_id": 0})
        # Phase 4B — if requires_certification was touched, recompute hold
        if "requires_certification" in update:
            from ._helpers import recompute_certification_hold
            await recompute_certification_hold(db, fresh["asset_id"], actor_email)
            fresh = await db.trench_safety_assets.find_one({"id": existing["id"]}, {"_id": 0})
        await upsert_equipment_master_mirror(db, fresh)
        await write_audit(
            db, kind="trench_asset_edited", asset_id=fresh["asset_id"],
            actor=actor, detail={"fields": sorted(update.keys())},
        )
        return fresh

    # ──────────────────────────────────────────────────────────────────
    # Status change (Admin + Safety) — gated by transition validator
    # ──────────────────────────────────────────────────────────────────
    @api_router.post(PREFIX + "/{ident}/status")
    async def change_status(
        ident: str,
        body: StatusChangeBody,
        actor: dict = Depends(require_safety_or_admin),
    ):
        existing = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]},
            {"_id": 0},
        )
        if not existing:
            raise HTTPException(404, "Trench safety asset not found")

        err = validate_status_transition(
            existing.get("operational_status", "Available"),
            body.operational_status,
        )
        if err:
            raise HTTPException(409, err)

        actor_email = (actor or {}).get("email") or (actor or {}).get("_actor") or "unknown"

        # TRENCH-ASSET-ASSIGNMENT-QR-FIX · Phase 2:
        # When transitioning to "Assigned", the caller MUST supply
        # project_id + project_name + project_number so we never leave
        # an asset Assigned-with-blank-project. When transitioning back
        # to "Available", clear the project context + reset
        # current_location to the home yard.
        update_set: Dict[str, Any] = {
            "operational_status": body.operational_status,
            "updated_at": now_iso(),
            "updated_by": actor_email,
        }
        if body.operational_status == "Assigned":
            pid = (body.project_id or "").strip()
            pnm = (body.project_name or "").strip()
            pnum = (body.project_number or "").strip()
            if not pid and not pnum:
                raise HTTPException(422, {
                    "code": "project_required_for_assigned",
                    "msg": "An asset cannot be Assigned without a project. "
                           "Supply project_id (or project_number) plus project_name.",
                })
            if not pnm:
                raise HTTPException(422, {
                    "code": "project_name_required_for_assigned",
                    "msg": "project_name is required when assigning a trench asset.",
                })
            update_set["current_project_id"] = pid or None
            update_set["current_project_name"] = pnm
            update_set["current_project_number"] = pnum or None
            update_set["current_location"] = (body.location or pnm).strip()
            if body.assigned_to_name:
                update_set["assigned_to_name"] = body.assigned_to_name.strip()
            if body.assigned_to_role:
                update_set["assigned_to_role"] = body.assigned_to_role.strip()
        elif body.operational_status == "Available":
            # Returning to yard — clear project context, reset current_location.
            home_yard = existing.get("yard_location") or "MASCI Yard"
            update_set["current_project_id"] = None
            update_set["current_project_name"] = None
            update_set["current_project_number"] = None
            update_set["current_location"] = home_yard
            update_set["assigned_to_name"] = None
            update_set["assigned_to_role"] = None

        await db.trench_safety_assets.update_one(
            {"id": existing["id"]},
            {"$set": update_set},
        )
        fresh = await db.trench_safety_assets.find_one({"id": existing["id"]}, {"_id": 0})
        await upsert_equipment_master_mirror(db, fresh)
        # Deployment history — write a row whenever the asset enters or
        # leaves the Assigned state so the asset detail timeline can
        # show "assigned to X on Y" / "returned from X on Y".
        try:
            if body.operational_status == "Assigned":
                await db.trench_safety_deployments.insert_one({
                    "id": str(uuid.uuid4()),
                    "asset_id": fresh["asset_id"],
                    "action": "assign",
                    "from_status": existing.get("operational_status"),
                    "to_status": "Assigned",
                    "project_id": update_set.get("current_project_id"),
                    "project_name": update_set.get("current_project_name"),
                    "project_number": update_set.get("current_project_number"),
                    "at": now_iso(),
                    "by": actor_email,
                    "source": "Manual Assignment",
                })
            elif (body.operational_status == "Available"
                  and existing.get("operational_status") == "Assigned"):
                await db.trench_safety_deployments.insert_one({
                    "id": str(uuid.uuid4()),
                    "asset_id": fresh["asset_id"],
                    "action": "return",
                    "from_status": "Assigned",
                    "to_status": "Available",
                    "project_id": existing.get("current_project_id"),
                    "project_name": existing.get("current_project_name"),
                    "project_number": existing.get("current_project_number"),
                    "at": now_iso(),
                    "by": actor_email,
                    "source": "Manual Return",
                })
        except Exception:
            # Never let history-insert failure block the status change.
            pass
        await write_audit(
            db, kind="trench_asset_status_changed", asset_id=fresh["asset_id"],
            actor=actor, detail={
                "from": existing.get("operational_status"),
                "to": body.operational_status,
                "note": body.note,
                "project_name": update_set.get("current_project_name"),
                "project_number": update_set.get("current_project_number"),
            },
        )
        return fresh

    # ──────────────────────────────────────────────────────────────────
    # Retire (Admin only — terminal action)
    # ──────────────────────────────────────────────────────────────────
    @api_router.post(PREFIX + "/{ident}/retire")
    async def retire_asset(
        ident: str,
        body: RetireAssetBody,
        actor: dict = Depends(require_admin),
    ):
        existing = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]},
            {"_id": 0},
        )
        if not existing:
            raise HTTPException(404, "Trench safety asset not found")
        if existing.get("operational_status") == "Retired":
            return existing

        await db.trench_safety_assets.update_one(
            {"id": existing["id"]},
            {"$set": {
                "operational_status": "Retired",
                "is_active": False,
                "retired_at": now_iso(),
                "retired_reason": body.retired_reason,
                "updated_at": now_iso(),
                "updated_by": "admin",
            }},
        )
        fresh = await db.trench_safety_assets.find_one({"id": existing["id"]}, {"_id": 0})
        await upsert_equipment_master_mirror(db, fresh)
        await write_audit(
            db, kind="trench_asset_retired", asset_id=fresh["asset_id"],
            actor={"_actor": "admin"}, detail={"reason": body.retired_reason},
        )
        return fresh

    # ──────────────────────────────────────────────────────────────────
    # Audit trail (any portal token)
    # ──────────────────────────────────────────────────────────────────
    @api_router.get(PREFIX + "/{ident}/audit")
    async def asset_audit(
        ident: str,
        limit: int = Query(default=100, ge=1, le=1000),
        _actor: dict = Depends(require_any_portal),
    ):
        # Resolve asset_id (lookups in audit_events are by asset_id)
        asset = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]},
            {"_id": 0, "asset_id": 1},
        )
        if not asset:
            raise HTTPException(404, "Trench safety asset not found")

        cursor = (
            db.audit_events.find(
                {"asset_id": asset["asset_id"], "kind": {"$regex": "^trench_"}},
                {"_id": 0},
            )
            .sort("ts", -1)
            .limit(limit)
        )
        return {"items": await cursor.to_list(limit)}

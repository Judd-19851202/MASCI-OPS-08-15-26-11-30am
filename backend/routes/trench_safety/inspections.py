"""Inspection submission + listing endpoints."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ._helpers import (
    now_iso,
    upsert_equipment_master_mirror,
    write_audit,
)
from ._models import (
    INSPECTION_RESULTS,
    INSPECTION_TYPES,
    InspectionSubmit,
)


def register_inspection_routes(
    api_router: APIRouter,
    db,
    *,
    require_safety_or_admin,
    require_any_portal,
) -> None:
    LIST_PATH = "/trench-safety/assets/{ident}/inspections"

    # ──────────────────────────────────────────────────────────────────
    # List inspections for an asset
    # ──────────────────────────────────────────────────────────────────
    @api_router.get(LIST_PATH)
    async def list_inspections(
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
            db.trench_safety_inspections.find(
                {"asset_id": asset["asset_id"]}, {"_id": 0}
            )
            .sort("submitted_at", -1)
            .limit(limit)
        )
        return {"items": await cursor.to_list(limit)}

    # ──────────────────────────────────────────────────────────────────
    # Submit inspection (Safety + Admin)
    # ──────────────────────────────────────────────────────────────────
    @api_router.post(LIST_PATH)
    async def submit_inspection(
        ident: str,
        payload: InspectionSubmit,
        actor: dict = Depends(require_safety_or_admin),
    ):
        if payload.inspection_type not in INSPECTION_TYPES:
            raise HTTPException(
                422, f"inspection_type must be one of {list(INSPECTION_TYPES)}"
            )
        if payload.result not in INSPECTION_RESULTS:
            raise HTTPException(
                422, f"result must be one of {list(INSPECTION_RESULTS)}"
            )

        asset = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]},
            {"_id": 0},
        )
        if not asset:
            raise HTTPException(404, "Trench safety asset not found")

        # Monthly/Annual require competent person flag
        if (
            payload.inspection_type in {"Monthly Competent Person", "Annual Review"}
            and not payload.competent_person_confirmed
        ):
            raise HTTPException(
                422,
                "competent_person_confirmed must be true for "
                "Monthly Competent Person or Annual Review inspections",
            )

        actor_email = (actor or {}).get("email") or (actor or {}).get("_actor") or "unknown"
        doc = {
            "id": str(uuid.uuid4()),
            "asset_id": asset["asset_id"],
            "asset_uuid": asset["id"],
            "inspection_type": payload.inspection_type,
            "inspector_name": payload.inspector_name,
            "inspector_role": payload.inspector_role,
            "competent_person_confirmed": bool(payload.competent_person_confirmed),
            "checklist": [item.model_dump() for item in payload.checklist],
            "findings": payload.findings,
            "corrective_actions": payload.corrective_actions,
            "result": payload.result,
            "photo_refs": list(payload.photo_refs),
            "submitted_at": now_iso(),
            "submitted_by": actor_email,
        }
        await db.trench_safety_inspections.insert_one(doc)
        doc.pop("_id", None)

        # Side-effects on the asset row
        update: Dict[str, Any] = {
            "last_inspection_at": doc["submitted_at"],
            "updated_at": now_iso(),
            "updated_by": actor_email,
        }
        audit_kind = "trench_asset_inspection_submitted"
        if payload.result == "Fail":
            update["operational_status"] = "Inspection Hold"
            audit_kind = "trench_asset_inspection_failed"
        elif payload.result == "Pass":
            audit_kind = "trench_asset_inspection_passed"
            # If asset was on Inspection Hold and this is a clearing
            # monthly/annual, lift the hold back to Available.
            if (
                asset.get("operational_status") == "Inspection Hold"
                and payload.inspection_type
                in {"Monthly Competent Person", "Annual Review"}
                and payload.competent_person_confirmed
            ):
                update["operational_status"] = "Available"

        await db.trench_safety_assets.update_one(
            {"id": asset["id"]}, {"$set": update}
        )
        fresh = await db.trench_safety_assets.find_one(
            {"id": asset["id"]}, {"_id": 0}
        )
        await upsert_equipment_master_mirror(db, fresh)
        await write_audit(
            db, kind=audit_kind, asset_id=asset["asset_id"], actor=actor,
            detail={
                "inspection_id": doc["id"],
                "inspection_type": payload.inspection_type,
                "result": payload.result,
                "status_after": fresh.get("operational_status"),
            },
        )
        return {"inspection": doc, "asset": fresh}

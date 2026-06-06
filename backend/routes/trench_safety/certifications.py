"""Trench Safety certification lifecycle — Phase 4B.

Routes:
  GET   /api/trench-safety/assets/{ident}/certifications
  POST  /api/trench-safety/assets/{ident}/certifications
  PATCH /api/trench-safety/certifications/{cert_id}
  POST  /api/trench-safety/certifications/{cert_id}/revoke

Every write recomputes the Certification Hold via the hold engine in
_helpers.recompute_certification_hold(). The hold engine is the only
status writer — this module never touches operational_status directly.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ._helpers import (
    now_iso,
    recompute_certification_hold,
    write_audit,
)
from ._models import (
    CERTIFICATION_KINDS,
    CERTIFICATION_STATUSES,
    CertificationCreate,
    CertificationRevoke,
    CertificationUpdate,
)


def register_certification_routes(
    api_router: APIRouter,
    db,
    *,
    require_safety_or_admin,
    require_any_portal,
) -> None:
    LIST_PATH = "/trench-safety/assets/{ident}/certifications"
    ITEM_PATH = "/trench-safety/certifications/{cert_id}"

    @api_router.get(LIST_PATH)
    async def list_certifications(
        ident: str,
        status: Optional[str] = Query(default=None),
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
        if status:
            q["status"] = status
        cursor = (
            db.trench_safety_certifications.find(q, {"_id": 0})
            .sort("expires_at", 1)
            .limit(limit)
        )
        return {"items": await cursor.to_list(limit)}

    @api_router.post(LIST_PATH)
    async def add_certification(
        ident: str,
        payload: CertificationCreate,
        actor: dict = Depends(require_safety_or_admin),
    ):
        if payload.kind not in CERTIFICATION_KINDS:
            raise HTTPException(
                422, f"kind must be one of {list(CERTIFICATION_KINDS)}"
            )
        asset = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]},
            {"_id": 0, "asset_id": 1, "id": 1},
        )
        if not asset:
            raise HTTPException(404, "Trench safety asset not found")
        actor_email = (actor or {}).get("email") or (actor or {}).get("_actor") or "unknown"

        doc = {
            "id": str(uuid.uuid4()),
            "asset_id": asset["asset_id"],
            "asset_uuid": asset["id"],
            "kind": payload.kind,
            "issuer": payload.issuer,
            "issued_at": payload.issued_at,
            "expires_at": payload.expires_at,
            "document_ref": payload.document_ref or "",
            "notes": payload.notes or "",
            "status": "Active",
            "created_at": now_iso(),
            "created_by": actor_email,
            "updated_at": now_iso(),
            "updated_by": actor_email,
            "revoked_at": None,
            "revoked_by": None,
            "revoke_reason": None,
        }
        await db.trench_safety_certifications.insert_one(doc)
        doc.pop("_id", None)

        await recompute_certification_hold(db, asset["asset_id"], actor_email)
        await write_audit(
            db, kind="trench_asset_certification_added",
            asset_id=asset["asset_id"], actor=actor,
            detail={
                "certification_id": doc["id"],
                "kind": payload.kind,
                "expires_at": payload.expires_at,
            },
        )
        return doc

    @api_router.patch(ITEM_PATH)
    async def update_certification(
        cert_id: str,
        payload: CertificationUpdate,
        actor: dict = Depends(require_safety_or_admin),
    ):
        existing = await db.trench_safety_certifications.find_one(
            {"id": cert_id}, {"_id": 0}
        )
        if not existing:
            raise HTTPException(404, "Certification not found")
        update = {k: v for k, v in payload.model_dump().items() if v is not None}
        if "status" in update and update["status"] not in CERTIFICATION_STATUSES:
            raise HTTPException(
                422, f"status must be one of {list(CERTIFICATION_STATUSES)}"
            )
        if not update:
            return existing
        actor_email = (actor or {}).get("email") or (actor or {}).get("_actor") or "unknown"
        update["updated_at"] = now_iso()
        update["updated_by"] = actor_email
        await db.trench_safety_certifications.update_one(
            {"id": cert_id}, {"$set": update}
        )
        fresh = await db.trench_safety_certifications.find_one(
            {"id": cert_id}, {"_id": 0}
        )
        await recompute_certification_hold(db, existing["asset_id"], actor_email)
        await write_audit(
            db, kind="trench_asset_certification_updated",
            asset_id=existing["asset_id"], actor=actor,
            detail={"certification_id": cert_id, "fields": sorted(update.keys())},
        )
        return fresh

    @api_router.post(ITEM_PATH + "/revoke")
    async def revoke_certification(
        cert_id: str,
        body: CertificationRevoke,
        actor: dict = Depends(require_safety_or_admin),
    ):
        existing = await db.trench_safety_certifications.find_one(
            {"id": cert_id}, {"_id": 0}
        )
        if not existing:
            raise HTTPException(404, "Certification not found")
        if existing.get("status") == "Revoked":
            return existing
        actor_email = (actor or {}).get("email") or (actor or {}).get("_actor") or "unknown"
        await db.trench_safety_certifications.update_one(
            {"id": cert_id},
            {"$set": {
                "status": "Revoked",
                "revoked_at": now_iso(),
                "revoked_by": actor_email,
                "revoke_reason": body.reason,
                "updated_at": now_iso(),
                "updated_by": actor_email,
            }},
        )
        fresh = await db.trench_safety_certifications.find_one(
            {"id": cert_id}, {"_id": 0}
        )
        await recompute_certification_hold(db, existing["asset_id"], actor_email)
        await write_audit(
            db, kind="trench_asset_certification_revoked",
            asset_id=existing["asset_id"], actor=actor,
            detail={"certification_id": cert_id, "reason": body.reason},
        )
        return fresh

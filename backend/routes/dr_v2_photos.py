"""DR-ROI-001D · Photo Vision + Evidence Linking API routes.

Additive `/api/dr-v2/photos/*` surface. Never touches V1 photo routes,
Job Photos mirror, or source photo storage. Feature-flag gated.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Path
from pydantic import BaseModel

from services.ai_gateway import get_gateway
from services.ai_gateway.env import gateway_enabled
from services.ods_spine import ods_enabled
from services.photo_intelligence import (
    COLL_PHOTO_INTEL, PHOTO_ENVELOPE_SCHEMA,
    accept_link, analyze_photo, dismiss_link, emit_photo_evidence_fact,
    ensure_indexes, evidence_hash_for_photo, get_intel, photo_vision_enabled,
    resolve_question, upsert_intel,
)


TENANT_DEFAULT = "masci"
LEGACY_COMPAT_ERROR = {
    "error": "legacy_daily_report_runtime_retired",
    "message": "Legacy Daily Report V2 authoring is retired. Use the canonical /daily/submit flow.",
    "canonical_route": "/daily/submit",
    "canonical_api": "/api/daily-reports",
    "compat_mode": "read_only",
}


class AnalyzeRequest(BaseModel):
    photo_id: str
    photo_ref: Optional[str] = None
    photo_base64: Optional[str] = None
    photo_content_type: Optional[str] = "image/jpeg"
    force: bool = False


class LinkActionRequest(BaseModel):
    supervisor_id: Optional[str] = None
    reason: Optional[str] = None


class QuestionResolveRequest(BaseModel):
    supervisor_id: Optional[str] = None
    resolution: str


def _raise_legacy_write_retired() -> None:
    raise HTTPException(status_code=410, detail=LEGACY_COMPAT_ERROR)


def register_dr_v2_photo_routes(api_router: APIRouter, db) -> None:

    async def _ensure_indexes():
        try:
            await ensure_indexes(db)
        except Exception:  # noqa: BLE001
            pass
    setattr(api_router, "_dr_v2_photo_ensure_indexes", _ensure_indexes)

    def _draft_context(draft: Dict[str, Any]) -> Dict[str, Any]:
        """Compact context for the vision model — supervisor-entered items only."""
        return {
            "activity_cards": [
                {"id": a.get("id"), "activity": a.get("activity") or a.get("activity_type"),
                 "area": a.get("area"), "qty": a.get("qty"), "unit": a.get("unit")}
                for a in (draft.get("activity_cards") or [])[:20]
            ],
            "constraint_cards": [
                {"id": c.get("id"), "type": c.get("type"), "note": c.get("note") or c.get("reason")}
                for c in (draft.get("constraint_cards") or [])[:20]
            ],
            "equipment_used": [
                {"unit": e.get("unit"), "hours": e.get("hours")}
                for e in (draft.get("equipment_used") or [])[:20]
            ],
            "masci_crews": [
                {"crew": c.get("crew"), "members_count": len(c.get("members") or [])}
                for c in (draft.get("masci_crews") or [])[:10]
            ],
        }

    # ----- Analyze --------------------------------------------------------
    @api_router.post("/dr-v2/photos/{photo_id}/analyze")
    async def dr_v2_photo_analyze(
        photo_id: str = Path(...),
        payload: AnalyzeRequest = Body(...),
    ) -> Dict[str, Any]:
        _raise_legacy_write_retired()
        if not photo_vision_enabled():
            return {"ok": False, "photo_vision_enabled": False,
                    "reason": "DR_V2_PHOTO_VISION_ENABLED off"}

        # Find the parent draft — every photo must belong to a DR-V2 draft.
        draft = await db["dr_v2_drafts"].find_one(
            {"$or": [
                {"photos.id": photo_id},
                {"photos.ref": photo_id},
                {"photos": photo_id},
            ]}, {"_id": 0},
        )
        if not draft:
            raise HTTPException(status_code=404, detail="draft for photo not found")

        report_id = draft.get("report_id") or ""
        setup = (draft.get("day_setup") or {})
        project_id = str(setup.get("project_number") or setup.get("project_name") or "")
        date = str(setup.get("report_date") or "")

        # Idempotency: skip repeat expensive vision if evidence hash unchanged.
        ctx = _draft_context(draft)
        ctx_hash = hashlib.sha256(json.dumps(ctx, sort_keys=True).encode()).hexdigest()
        photo_hash = evidence_hash_for_photo(
            photo_ref=payload.photo_ref or photo_id,
            photo_bytes_b64=payload.photo_base64,
            draft_context_hash=ctx_hash,
        )
        prior = await get_intel(db, report_id=report_id, photo_id=photo_id)
        if not payload.force and prior and prior.get("evidence_hash") == photo_hash:
            return {"ok": True, "cached": True, "intel": prior}

        gw = get_gateway()
        images: List[Any] = []
        if payload.photo_base64:
            images.append({"content_type": payload.photo_content_type or "image/jpeg",
                           "file_content_base64": payload.photo_base64})
        env = await analyze_photo(
            gateway=gw,
            session_id=f"drv2-photo-{photo_id}",
            photo_ref=payload.photo_ref or photo_id,
            images=images,
            draft_context=ctx,
        )
        env_dict = env.to_dict()
        env_dict["raw"] = getattr(env, "raw", {}) or {}

        intel = await upsert_intel(
            db,
            report_id=report_id, photo_id=photo_id,
            project_id=project_id, tenant_id=TENANT_DEFAULT,
            evidence_hash=photo_hash, envelope=env_dict,
            provider=env.provider, model=env.model,
        )
        return {"ok": env.ai_available, "cached": False, "intel": intel}

    # ----- Read -----------------------------------------------------------
    @api_router.get("/dr-v2/photos/{photo_id}/intelligence")
    async def dr_v2_photo_intel_read(
        photo_id: str = Path(...),
        report_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        q: Dict[str, Any] = {"photo_id": photo_id}
        if report_id:
            q["report_id"] = report_id
        doc = await db[COLL_PHOTO_INTEL].find_one(q, {"_id": 0})
        return {"intel": doc}

    # ----- Accept / dismiss link -----------------------------------------
    @api_router.post("/dr-v2/photos/{photo_id}/links/{link_id}/accept")
    async def dr_v2_photo_link_accept(
        photo_id: str = Path(...),
        link_id: str = Path(...),
        payload: LinkActionRequest = Body(default=LinkActionRequest()),
    ) -> Dict[str, Any]:
        _raise_legacy_write_retired()
        doc = await db[COLL_PHOTO_INTEL].find_one({"photo_id": photo_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="photo intel not found")
        updated = await accept_link(
            db, report_id=doc["report_id"], photo_id=photo_id,
            link_id=link_id, reviewed_by=payload.supervisor_id or "supervisor",
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="link not found")
        # Emit photo_evidence_fact on accept.
        accepted = next(
            (s for s in updated["suggested_links"] if s.get("link_id") == link_id), None,
        )
        if ods_enabled() and accepted:
            try:
                await emit_photo_evidence_fact(
                    db,
                    tenant_id=updated.get("tenant_id", TENANT_DEFAULT),
                    project_id=updated.get("project_id", ""),
                    date=(await _draft_date(db, updated["report_id"])),
                    report_id=updated["report_id"], photo_id=photo_id,
                    intel=updated, accepted_link=accepted,
                    actor=payload.supervisor_id or "supervisor",
                )
            except Exception:  # noqa: BLE001
                pass
        return {"ok": True, "intel": updated}

    @api_router.post("/dr-v2/photos/{photo_id}/links/{link_id}/dismiss")
    async def dr_v2_photo_link_dismiss(
        photo_id: str = Path(...),
        link_id: str = Path(...),
        payload: LinkActionRequest = Body(default=LinkActionRequest()),
    ) -> Dict[str, Any]:
        _raise_legacy_write_retired()
        doc = await db[COLL_PHOTO_INTEL].find_one({"photo_id": photo_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="photo intel not found")
        updated = await dismiss_link(
            db, report_id=doc["report_id"], photo_id=photo_id,
            link_id=link_id, reviewed_by=payload.supervisor_id or "supervisor",
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="link not found")
        return {"ok": True, "intel": updated}

    # ----- Resolve question ----------------------------------------------
    @api_router.post("/dr-v2/photos/{photo_id}/questions/{question_id}/resolve")
    async def dr_v2_photo_question_resolve(
        photo_id: str = Path(...),
        question_id: str = Path(...),
        payload: QuestionResolveRequest = Body(...),
    ) -> Dict[str, Any]:
        _raise_legacy_write_retired()
        doc = await db[COLL_PHOTO_INTEL].find_one({"photo_id": photo_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="photo intel not found")
        updated = await resolve_question(
            db, report_id=doc["report_id"], photo_id=photo_id,
            question_id=question_id, resolution=payload.resolution,
            reviewed_by=payload.supervisor_id or "supervisor",
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="question not found")
        return {"ok": True, "intel": updated}


async def _draft_date(db, report_id: str) -> str:
    d = await db["dr_v2_drafts"].find_one({"report_id": report_id}, {"_id": 0, "day_setup": 1})
    return str(((d or {}).get("day_setup") or {}).get("report_date") or "")

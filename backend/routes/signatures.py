"""
routes/signatures.py — Iter154 (Phase 2.5) · Phase F.

UNIFIED SIGNATURE ENGINE.

One signature standard across the entire platform. Reused by:
  * safety.corrective_actions (employee acknowledgment)
  * hr.writeups / hr.terminations
  * safety_meetings sign-in
  * incident reports
  * audits / inspections
  * po.approvals (when manual sig required)
  * asset.transfer receiving (Phase I)
  * future employee portal signoffs

Backend exposes both a service callable (signature_service.capture)
AND HTTP endpoints. Frontend `<SignatureCapture />` consumes the
endpoints directly.

Audit-safe: signatures are append-only. "Updates" create a new row
with a `supersedes` link to the previous one — old signature stays in
history. No silent overwrites.
"""
from __future__ import annotations

import base64
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

ALLOWED_SIGNATURE_TYPES = {
    "supervisor", "employee", "witness", "approver",
    "receiver", "inspector", "trainer", "trainee", "other",
}

# Source-module allowlist — append-only.
ALLOWED_MODULES = {
    "safety.corrective_actions", "safety.incidents",
    "safety.audits", "safety.fire_extinguishers",
    "safety.training", "safety.meetings",
    "hr.writeups", "hr.terminations", "hr.evaluations",
    "hr.offboarding",
    "equipment.checkout", "equipment.return",
    "equipment.transfer", "equipment.preop",
    "po.approvals", "po.receipts",
    "customer.acknowledgments",
    "field.daily_reports",
    "admin.manual",
}


class SignatureCreate(BaseModel):
    source_module: str
    source_record_id: str = Field(..., max_length=64)
    signer_name: str = Field(..., min_length=1, max_length=160)
    signer_employee_id: Optional[str] = Field(default=None, max_length=64)
    signer_role: Optional[str] = Field(default=None, max_length=80)
    signature_type: str = Field(default="employee")
    signature_image: Optional[str] = Field(default=None,
        description="data:image/png;base64,... (signed strokes)",
        max_length=2_000_000)
    refusal: bool = False
    refusal_reason: Optional[str] = Field(default=None, max_length=2000)
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    supersedes: Optional[str] = Field(default=None, max_length=64)

    @field_validator("source_module")
    @classmethod
    def _v_mod(cls, v: str) -> str:
        if v not in ALLOWED_MODULES:
            raise ValueError(f"source_module must be one of {sorted(ALLOWED_MODULES)}")
        return v

    @field_validator("signature_type")
    @classmethod
    def _v_typ(cls, v: str) -> str:
        if v not in ALLOWED_SIGNATURE_TYPES:
            raise ValueError(f"signature_type must be one of {sorted(ALLOWED_SIGNATURE_TYPES)}")
        return v


class _SignatureService:
    async def capture(self, db, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a signature row. If `supersedes` is set, the prior
        signature is NOT deleted — both rows persist; the older one
        is marked `superseded_at`."""
        now = datetime.now(timezone.utc)
        # Validate refusal vs image — must have one or the other.
        refusal = bool(payload.get("refusal"))
        sig_img = (payload.get("signature_image") or "").strip() or None
        if not refusal and not sig_img:
            raise ValueError(
                "signature_image is required unless refusal=true")
        if refusal and not (payload.get("refusal_reason") or "").strip():
            raise ValueError("refusal_reason required when refusal=true")

        # Approximate image size guard — base64 ~33% bigger than binary.
        if sig_img and len(sig_img) > 1_800_000:
            raise ValueError("signature image too large (max ~1.3MB binary)")

        doc = {
            "id": str(uuid.uuid4()),
            "source_module": payload["source_module"],
            "source_record_id": payload["source_record_id"],
            "signer_name": payload["signer_name"].strip()[:160],
            "signer_employee_id": payload.get("signer_employee_id"),
            "signer_role": (payload.get("signer_role") or "").strip()[:80] or None,
            "signature_type": payload.get("signature_type", "employee"),
            "signature_image": sig_img,
            "refusal": refusal,
            "refusal_reason": (payload.get("refusal_reason") or "").strip()[:2000] or None,
            "gps_lat": payload.get("gps_lat"),
            "gps_lon": payload.get("gps_lon"),
            "user_agent": payload.get("user_agent"),
            "ip": payload.get("ip"),
            "created_at": now,
            "created_by": payload.get("created_by") or {"role": "system"},
            "supersedes": payload.get("supersedes"),
            "superseded_by": None,
            "superseded_at": None,
        }
        await db.signatures.insert_one(doc)
        # Mark prior signature superseded.
        if doc["supersedes"]:
            await db.signatures.update_one(
                {"id": doc["supersedes"]},
                {"$set": {
                    "superseded_by": doc["id"],
                    "superseded_at": now,
                }},
            )
        doc.pop("_id", None)
        return doc


signature_service = _SignatureService()


async def ensure_signatures_indexes(db) -> None:
    try:
        await db.signatures.create_index("id", unique=True)
        await db.signatures.create_index([
            ("source_module", 1), ("source_record_id", 1)])
        await db.signatures.create_index("signer_employee_id")
        await db.signatures.create_index("created_at")
        await db.signatures.create_index("supersedes")
    except Exception as e:  # pragma: no cover
        logger.warning("signatures index bootstrap failed: %s", e)


def build_signatures_router(db, require_any_portal_token):
    router = APIRouter(tags=["signatures"])

    def _actor_role(a: Dict[str, Any]) -> str:
        return a.get("_actor") or a.get("role") or "admin"

    @router.get("/api/signatures")
    async def list_sigs(
        actor: Dict[str, Any] = Depends(require_any_portal_token),
        source_module: Optional[str] = Query(default=None),
        source_record_id: Optional[str] = Query(default=None),
        signer_employee_id: Optional[str] = Query(default=None),
        include_superseded: bool = Query(default=False),
        limit: int = Query(default=200, ge=1, le=500),
    ) -> Dict[str, Any]:
        clauses: List[Dict[str, Any]] = []
        if source_module:
            clauses.append({"source_module": source_module})
        if source_record_id:
            clauses.append({"source_record_id": source_record_id})
        if signer_employee_id:
            clauses.append({"signer_employee_id": signer_employee_id})
        if not include_superseded:
            clauses.append({"superseded_by": None})
        final = {"$and": clauses} if clauses else {}
        cur = db.signatures.find(final, {"_id": 0}).sort("created_at", -1).limit(limit)
        items = [d async for d in cur]
        return {"items": items, "count": len(items)}

    @router.post("/api/signatures")
    async def create_sig(
        body: SignatureCreate,
        request: Request,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        data = body.model_dump()
        data["user_agent"] = request.headers.get("user-agent", "")[:300]
        data["ip"] = (request.client.host if request.client else None)
        data["created_by"] = {
            "role": _actor_role(actor),
            "name": actor.get("name") or actor.get("email"),
            "user_id": actor.get("id"),
        }
        try:
            doc = await signature_service.capture(db, data)
        except ValueError as e:
            raise HTTPException(400, str(e))
        return doc

    return router


__all__ = [
    "build_signatures_router",
    "ensure_signatures_indexes",
    "signature_service",
    "ALLOWED_MODULES",
    "ALLOWED_SIGNATURE_TYPES",
]

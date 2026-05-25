"""routes/operational_attachments.py · iter417 · Phase 20.0.

Operational Attachments Foundation — walking-skeleton primitive.

Doctrine
--------
Attachments are NOT files. Attachments ARE operational proof continuity.

This module ships the smallest viable primitive:
  - ONE collection: `operational_attachments`
  - ONE host kind (iter417): `assignment` (dispatch_assignments.id)
  - 12 canonical operational attachment types
  - 5 MB per file · image MIME types only (jpg/png/heic/webp/gif)
  - 25 attachments cap per host (anti-abuse)
  - RBAC: dispatch+admin write · any-portal-token + driver-session read

What is OUT of scope (deferred to later iter)
  - Folders / buckets / albums / "attachments management" page
  - Multi-host expansion (incidents · inspections · daily reports · etc.)
  - Bulk operations · download-all · rename · move
  - Versioning · history · audit trail beyond uploaded_at
  - Thumbnail generation (browser handles display from full image)
  - Public unauth uploads (driver magic-link path comes in 20.1)

Doctrine guards
  - Operational truth · NOT document management
  - Append-only attach (deletion only by uploader within 5 min · mistake recovery)
  - No `is_archived` / `is_deleted` lifecycle · keep operational truth
  - No "default" attachment type · forces type declaration on upload
"""
from __future__ import annotations

import base64
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Awaitable, Callable, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form
from pydantic import BaseModel

logger = logging.getLogger("operational_attachments")

DEFAULT_TENANT_ID = "masci"

# ── Canonical 12 attachment types (doctrine-locked) ────────────────
ATTACHMENT_TYPES = {
    "asphalt_ticket",
    "scale_ticket",
    "tanker_BOL",
    "fuel_receipt",
    "delivery_receipt",
    "load_photo",
    "damage_photo",
    "breakdown_photo",
    "inspection_photo",
    "transfer_document",
    "dump_receipt",
    "operational_note_photo",
}

# ── Caps ──────────────────────────────────────────────────────────
MAX_BYTES = 5 * 1024 * 1024          # 5 MB per file
MAX_PER_HOST = 25                    # 25 attachments cap per host
MAX_NOTE_LEN = 500                   # 500 char operational note cap
ALLOWED_MIME_PREFIXES = ("image/",)  # walking skeleton = images only
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/heic",
    "image/heif", "image/webp", "image/gif",
}
DELETE_GRACE_MINUTES = 5             # mistake-recovery window

# ── Supported host kinds (iter417 walking skeleton = assignment only)
SUPPORTED_HOST_KINDS = {"assignment"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_tenant(x_tenant_id: Optional[str]) -> str:
    return (x_tenant_id or DEFAULT_TENANT_ID).strip() or DEFAULT_TENANT_ID


def _actor_label(actor: Dict[str, Any]) -> str:
    if isinstance(actor, dict):
        return (actor.get("name") or actor.get("email") or actor.get("username") or "admin")
    return "admin"


def _actor_role(actor: Dict[str, Any]) -> str:
    if isinstance(actor, dict):
        return (actor.get("portal") or actor.get("role") or "admin")
    return "admin"


def _public_attachment(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Return the attachment WITHOUT the raw base64 data field (small list)."""
    return {
        "id": doc.get("id"),
        "type": doc.get("type"),
        "host_kind": doc.get("host_kind"),
        "host_id": doc.get("host_id"),
        "uploaded_by": doc.get("uploaded_by"),
        "uploaded_role": doc.get("uploaded_role"),
        "uploaded_at": doc.get("uploaded_at"),
        "operational_note": doc.get("operational_note") or "",
        "filename": doc.get("filename"),
        "content_type": doc.get("content_type"),
        "size_bytes": doc.get("size_bytes"),
    }


class AttachmentDeleteResponse(BaseModel):
    ok: bool
    id: str


def build_operational_attachments_router(
    db,
    require_dispatch_or_admin_dep: Callable[..., Awaitable[Dict[str, Any]]],
    require_any_portal_token_dep: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    router = APIRouter(prefix="/api/operational-attachments", tags=["operational-attachments"])

    @router.get("/types")
    async def list_types(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
    ):
        """Canonical 12 attachment types · single source of truth for the FE."""
        return {"types": sorted(ATTACHMENT_TYPES)}

    # ─── UPLOAD ───────────────────────────────────────────────────
    @router.post("/upload")
    async def upload_attachment(
        host_kind: str = Form(...),
        host_id: str = Form(...),
        attachment_type: str = Form(...),
        operational_note: str = Form(""),
        file: UploadFile = File(...),
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)

        # ── Validate inputs
        if host_kind not in SUPPORTED_HOST_KINDS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported host_kind in iter417 walking skeleton: {host_kind}",
            )
        if attachment_type not in ATTACHMENT_TYPES:
            raise HTTPException(status_code=400, detail=f"Unknown attachment_type: {attachment_type}")
        host_id = (host_id or "").strip()
        if not host_id:
            raise HTTPException(status_code=400, detail="host_id is required")

        # ── Validate host exists (assignment kind for walking skeleton)
        if host_kind == "assignment":
            existing = await db.dispatch_assignments.find_one(
                {"id": host_id, "tenant_id": tenant_id}, {"_id": 0, "id": 1}
            )
            if not existing:
                raise HTTPException(status_code=404, detail="Host assignment not found")

        # ── Cap attachment count per host
        count = await db.operational_attachments.count_documents(
            {"tenant_id": tenant_id, "host_kind": host_kind, "host_id": host_id}
        )
        if count >= MAX_PER_HOST:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {MAX_PER_HOST} attachments per host reached",
            )

        # ── Validate MIME + read bytes
        content_type = (file.content_type or "").lower()
        if not any(content_type.startswith(p) for p in ALLOWED_MIME_PREFIXES) or content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported content_type: {content_type} (images only in iter417)",
            )
        raw = await file.read()
        size_bytes = len(raw)
        if size_bytes == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        if size_bytes > MAX_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File too large ({size_bytes} bytes; max {MAX_BYTES})",
            )

        # ── Sanitize note
        operational_note = (operational_note or "").strip()
        if len(operational_note) > MAX_NOTE_LEN:
            operational_note = operational_note[:MAX_NOTE_LEN]

        attachment_id = str(uuid.uuid4())
        doc = {
            "id": attachment_id,
            "tenant_id": tenant_id,
            "host_kind": host_kind,
            "host_id": host_id,
            "type": attachment_type,
            "uploaded_by": _actor_label(actor),
            "uploaded_role": _actor_role(actor),
            "uploaded_at": _now_iso(),
            "operational_note": operational_note,
            "filename": (file.filename or "attachment").strip()[:255],
            "content_type": content_type,
            "size_bytes": size_bytes,
            "data_b64": base64.b64encode(raw).decode("ascii"),
        }
        await db.operational_attachments.insert_one(doc)

        return _public_attachment(doc)

    # ─── LIST (by host) ───────────────────────────────────────────
    @router.get("/list")
    async def list_attachments(
        host_kind: str,
        host_id: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        if host_kind not in SUPPORTED_HOST_KINDS:
            raise HTTPException(status_code=400, detail=f"Unsupported host_kind: {host_kind}")
        if not (host_id or "").strip():
            raise HTTPException(status_code=400, detail="host_id is required")
        cur = db.operational_attachments.find(
            {"tenant_id": tenant_id, "host_kind": host_kind, "host_id": host_id.strip()},
            {"_id": 0, "data_b64": 0},
        ).sort("uploaded_at", 1)
        items = [_public_attachment(d) async for d in cur]
        return {"attachments": items, "count": len(items)}

    # ─── FETCH BINARY ─────────────────────────────────────────────
    @router.get("/{attachment_id}/file")
    async def get_attachment_file(
        attachment_id: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        doc = await db.operational_attachments.find_one(
            {"id": attachment_id, "tenant_id": tenant_id},
            {"_id": 0},
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Attachment not found")
        from fastapi.responses import Response
        raw = base64.b64decode(doc.get("data_b64") or "")
        return Response(
            content=raw,
            media_type=doc.get("content_type") or "application/octet-stream",
            headers={
                "Content-Disposition": f'inline; filename="{doc.get("filename","attachment")}"',
                "Cache-Control": "private, max-age=300",
            },
        )

    # ─── DELETE (5-min mistake-recovery window only) ──────────────
    @router.delete("/{attachment_id}", response_model=AttachmentDeleteResponse)
    async def delete_attachment(
        attachment_id: str,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        """Operational mistake recovery only. Deletion allowed:
          - by the original uploader OR an admin
          - within 5 minutes of upload (operational truth doctrine)
        After that, the attachment is permanent operational proof.
        """
        tenant_id = _resolve_tenant(x_tenant_id)
        doc = await db.operational_attachments.find_one(
            {"id": attachment_id, "tenant_id": tenant_id},
            {"_id": 0, "uploaded_at": 1, "uploaded_by": 1, "uploaded_role": 1},
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Attachment not found")

        # Admin or original uploader
        actor_label = _actor_label(actor)
        actor_role = _actor_role(actor)
        is_admin = actor_role == "admin" or (isinstance(actor, dict) and actor.get("admin"))
        is_uploader = doc.get("uploaded_by") == actor_label
        if not (is_admin or is_uploader):
            raise HTTPException(status_code=403, detail="Not allowed to delete this attachment")

        # 5-minute grace window
        try:
            upl_dt = datetime.fromisoformat(doc["uploaded_at"].replace("Z", "+00:00"))
            age = datetime.now(timezone.utc) - upl_dt
        except Exception:
            age = timedelta(days=999)
        if age > timedelta(minutes=DELETE_GRACE_MINUTES) and not is_admin:
            raise HTTPException(
                status_code=403,
                detail=f"Attachments become permanent operational proof after {DELETE_GRACE_MINUTES} minutes",
            )

        await db.operational_attachments.delete_one(
            {"id": attachment_id, "tenant_id": tenant_id}
        )
        return AttachmentDeleteResponse(ok=True, id=attachment_id)

    return router


async def ensure_operational_attachments_indexes(db) -> None:
    """Index by host for list queries; index by id for fetches."""
    coll = db.operational_attachments
    await coll.create_index(
        [("tenant_id", 1), ("host_kind", 1), ("host_id", 1), ("uploaded_at", 1)],
        name="ix_op_attachments_host",
    )
    await coll.create_index(
        [("id", 1), ("tenant_id", 1)],
        name="ix_op_attachments_id",
        unique=True,
    )

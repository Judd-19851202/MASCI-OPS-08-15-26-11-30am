"""routes/dispatch_continuity.py · iter418/419/420 · Phases 20.1/21.0/22.0.

ONE module · THREE walking-skeleton continuity primitives:

  iter418 · Phase 20.1 · Breakdown Proof Continuity
    Driver-session magic-link write endpoint for attaching an OPTIONAL
    breakdown photo immediately after a BREAKDOWN lifecycle tap. Reuses
    the iter417 `operational_attachments` storage primitive directly —
    no new storage, no new collection.

  iter419 · Phase 21.0 · Operational Exception Continuity
    NEW collection `dispatch_continuity_events`. Append-only narrative
    log of operational continuity events. Walking-skeleton kinds:
      TRAILER_SWAP · REASSIGNED_DURING_WAITING · STALE_ASSIGNMENT_RECOVERED
      · DELAYED_LIFECYCLE_UPDATE · ASSIGNMENT_REASSIGNED
    Each event = an operational continuity explanation (not an error).

  iter420 · Phase 22.0 · Shop Recovery Continuity
    Adds `breakdown_recovery` SUB-STATE on dispatch_assignments. Seven
    canonical operational continuity states:
      reported · acknowledged · diagnosing · waiting_on_parts ·
      repair_active · operational_test · returned_to_service
    Lives separately from `current_state` so it tracks the SHOP recovery
    arc, not the DLS haul lifecycle.

DOCTRINE GUARDS (all three)
  - NO new portals · NO new dashboards
  - NO analytics · NO scoring · NO charts
  - Append-only continuity history · no UPDATEs except recovery state
  - Mongo `_id` excluded from every response
  - All RBAC rides existing dependencies — no new auth surface
"""
from __future__ import annotations

import base64
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form
from pydantic import BaseModel, Field

logger = logging.getLogger("dispatch_continuity")

DEFAULT_TENANT_ID = "masci"

# ════════════════════════════════════════════════════════════════════
# iter418 · constants reused from operational_attachments
# ════════════════════════════════════════════════════════════════════
MAX_BYTES = 5 * 1024 * 1024
MAX_PER_HOST = 25
MAX_NOTE_LEN = 500
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/heic",
    "image/heif", "image/webp", "image/gif",
}

# ════════════════════════════════════════════════════════════════════
# iter419 · canonical continuity-event kinds (walking skeleton)
# ════════════════════════════════════════════════════════════════════
CONTINUITY_EVENT_KINDS = {
    "TRAILER_SWAP",                # driver swapped trailer mid-haul
    "REASSIGNED_DURING_WAITING",   # dispatch swapped truck while WAITING
    "STALE_ASSIGNMENT_RECOVERED",  # assignment lingered too long, recovered
    "DELAYED_LIFECYCLE_UPDATE",    # state update arrived late due to signal
    "ASSIGNMENT_REASSIGNED",       # generic reassignment continuity
}

# ════════════════════════════════════════════════════════════════════
# iter420 · canonical breakdown-recovery states (Shop continuity)
# ════════════════════════════════════════════════════════════════════
RECOVERY_STATES = [
    "reported",            # breakdown surfaced (set when BREAKDOWN lifecycle tap fires)
    "acknowledged",        # Shop has seen it
    "diagnosing",          # mechanic on it
    "waiting_on_parts",    # blocked on supply
    "repair_active",       # parts in hand · repair work happening
    "operational_test",    # post-repair operational verification
    "returned_to_service", # back available for dispatch
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_tenant(x_tenant_id: Optional[str]) -> str:
    return (x_tenant_id or DEFAULT_TENANT_ID).strip() or DEFAULT_TENANT_ID


def _actor_label(actor: Dict[str, Any]) -> str:
    if isinstance(actor, dict):
        return (actor.get("name") or actor.get("driver_id")
                or actor.get("email") or actor.get("username") or "operator")
    return "operator"


def _actor_role(actor: Dict[str, Any]) -> str:
    if isinstance(actor, dict):
        return (actor.get("_actor") or actor.get("portal")
                or actor.get("role") or "operator")
    return "operator"


def _public_event(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": doc.get("id"),
        "assignment_id": doc.get("assignment_id"),
        "kind": doc.get("kind"),
        "narrative": doc.get("narrative") or "",
        "captured_by": doc.get("captured_by"),
        "captured_role": doc.get("captured_role"),
        "created_at": doc.get("created_at"),
    }


# ════════════════════════════════════════════════════════════════════
# ROUTER FACTORIES
# ════════════════════════════════════════════════════════════════════
class ContinuityEventCreate(BaseModel):
    kind: str
    assignment_id: str
    narrative: str = Field(default="", max_length=500)


class RecoveryTransition(BaseModel):
    to_state: str
    note: str = Field(default="", max_length=500)


def build_dispatch_continuity_router(
    db,
    require_driver_session_dep: Callable[..., Awaitable[Dict[str, Any]]],
    require_dispatch_or_admin_dep: Callable[..., Awaitable[Dict[str, Any]]],
    require_any_portal_token_dep: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    router = APIRouter(prefix="/api/dispatch", tags=["dispatch-continuity"])

    # ════════════════════════════════════════════════════════════
    # iter418 · Phase 20.1 · Driver breakdown-proof upload (magic-link)
    # ════════════════════════════════════════════════════════════
    @router.post("/driver/breakdown-proof/upload")
    async def driver_upload_breakdown_proof(
        host_id: str = Form(...),
        operational_note: str = Form(""),
        file: UploadFile = File(...),
        session: Dict[str, Any] = Depends(require_driver_session_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        """Driver-session magic-link upload of a breakdown photo.

        Doctrine:
          - Driver may only attach proof to an assignment owned by their
            own active session (no cross-driver proof attachment).
          - Type is HARD-CODED to ``breakdown_photo`` — no type picker
            for drivers (low cognition · operational stress).
          - All other limits (5 MB, 25/host, image-only) mirror iter417.
        """
        tenant_id = _resolve_tenant(x_tenant_id)
        host_id = (host_id or "").strip()
        if not host_id:
            raise HTTPException(400, "host_id required")

        # Cross-check driver session owns this assignment
        session_aid = (session or {}).get("assignment_id")
        if session_aid and session_aid != host_id:
            raise HTTPException(403, "Driver session does not own this assignment")

        # Validate assignment exists
        existing = await db.dispatch_assignments.find_one(
            {"id": host_id, "tenant_id": tenant_id}, {"_id": 0, "id": 1},
        )
        if not existing:
            raise HTTPException(404, "Assignment not found")

        # Cap per host (anti-abuse · drivers under stress)
        count = await db.operational_attachments.count_documents({
            "tenant_id": tenant_id, "host_kind": "assignment", "host_id": host_id,
        })
        if count >= MAX_PER_HOST:
            raise HTTPException(400, f"Maximum {MAX_PER_HOST} attachments per host")

        # Validate MIME
        content_type = (file.content_type or "").lower()
        if content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(400, f"Unsupported content_type: {content_type}")

        # Read + size check
        raw = await file.read()
        size_bytes = len(raw)
        if size_bytes == 0:
            raise HTTPException(400, "Empty file")
        if size_bytes > MAX_BYTES:
            raise HTTPException(400, "File too large (5 MB max)")

        note = (operational_note or "").strip()[:MAX_NOTE_LEN]
        att_id = str(uuid.uuid4())
        doc = {
            "id": att_id,
            "tenant_id": tenant_id,
            "host_kind": "assignment",
            "host_id": host_id,
            "type": "breakdown_photo",   # locked for driver path
            "uploaded_by": _actor_label(session),
            "uploaded_role": "driver",
            "uploaded_at": _now_iso(),
            "operational_note": note,
            "filename": (file.filename or "breakdown.jpg").strip()[:255],
            "content_type": content_type,
            "size_bytes": size_bytes,
            "data_b64": base64.b64encode(raw).decode("ascii"),
        }
        await db.operational_attachments.insert_one(doc)
        # Return shape mirrors iter417 public shape (no data_b64)
        return {
            "id": att_id,
            "type": "breakdown_photo",
            "host_kind": "assignment",
            "host_id": host_id,
            "uploaded_at": doc["uploaded_at"],
            "size_bytes": size_bytes,
        }

    # ════════════════════════════════════════════════════════════
    # iter419 · Phase 21.0 · Continuity-event list/create
    # ════════════════════════════════════════════════════════════
    @router.get("/continuity-events/kinds")
    async def list_continuity_kinds(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
    ):
        return {"kinds": sorted(CONTINUITY_EVENT_KINDS)}

    @router.post("/continuity-events")
    async def create_continuity_event(
        payload: ContinuityEventCreate,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        if payload.kind not in CONTINUITY_EVENT_KINDS:
            raise HTTPException(400, f"Unknown continuity kind: {payload.kind}")
        aid = (payload.assignment_id or "").strip()
        if not aid:
            raise HTTPException(400, "assignment_id required")
        # Verify assignment exists
        existing = await db.dispatch_assignments.find_one(
            {"id": aid, "tenant_id": tenant_id}, {"_id": 0, "id": 1},
        )
        if not existing:
            raise HTTPException(404, "Assignment not found")

        narrative = (payload.narrative or "").strip()[:MAX_NOTE_LEN]
        event_id = str(uuid.uuid4())
        doc = {
            "id": event_id,
            "tenant_id": tenant_id,
            "assignment_id": aid,
            "kind": payload.kind,
            "narrative": narrative,
            "captured_by": _actor_label(actor),
            "captured_role": _actor_role(actor),
            "created_at": _now_iso(),
        }
        await db.dispatch_continuity_events.insert_one(doc)
        return _public_event(doc)

    @router.get("/continuity-events/by-assignment/{assignment_id}")
    async def list_events_by_assignment(
        assignment_id: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        cur = db.dispatch_continuity_events.find(
            {"tenant_id": tenant_id, "assignment_id": assignment_id.strip()},
            {"_id": 0},
        ).sort("created_at", 1)
        items = [_public_event(d) async for d in cur]
        return {"events": items, "count": len(items)}

    # ════════════════════════════════════════════════════════════
    # iter420 · Phase 22.0 · Shop recovery sub-state transitions
    # ════════════════════════════════════════════════════════════
    @router.get("/recovery/states")
    async def list_recovery_states(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
    ):
        return {"states": RECOVERY_STATES}

    @router.post("/recovery/{assignment_id}/transition")
    async def recovery_transition(
        assignment_id: str,
        payload: RecoveryTransition,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        """Transition the Shop-recovery sub-state on a dispatch assignment.

        This is decoupled from `current_state` (DLS haul lifecycle). The
        assignment can be in any DLS state and still progress its
        recovery sub-state. Append-only history stored on the assignment
        document under `recovery_history[]`.
        """
        tenant_id = _resolve_tenant(x_tenant_id)
        if payload.to_state not in RECOVERY_STATES:
            raise HTTPException(400, f"Unknown recovery state: {payload.to_state}")
        aid = assignment_id.strip()
        existing = await db.dispatch_assignments.find_one(
            {"id": aid, "tenant_id": tenant_id},
            {"_id": 0, "id": 1, "recovery_state": 1, "recovery_history": 1},
        )
        if not existing:
            raise HTTPException(404, "Assignment not found")

        note = (payload.note or "").strip()[:MAX_NOTE_LEN]
        entry = {
            "at": _now_iso(),
            "from": existing.get("recovery_state") or "reported",
            "to": payload.to_state,
            "by": _actor_label(actor),
            "role": _actor_role(actor),
            "note": note,
        }
        await db.dispatch_assignments.update_one(
            {"id": aid, "tenant_id": tenant_id},
            {
                "$set": {"recovery_state": payload.to_state},
                "$push": {"recovery_history": entry},
            },
        )
        return {
            "ok": True,
            "assignment_id": aid,
            "recovery_state": payload.to_state,
            "entry": entry,
        }

    @router.get("/recovery/{assignment_id}")
    async def get_recovery_state(
        assignment_id: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        doc = await db.dispatch_assignments.find_one(
            {"id": assignment_id.strip(), "tenant_id": tenant_id},
            {"_id": 0, "id": 1, "recovery_state": 1, "recovery_history": 1},
        )
        if not doc:
            raise HTTPException(404, "Assignment not found")
        return {
            "assignment_id": doc.get("id"),
            "recovery_state": doc.get("recovery_state") or None,
            "history": doc.get("recovery_history") or [],
        }

    return router


async def ensure_dispatch_continuity_indexes(db) -> None:
    coll = db.dispatch_continuity_events
    await coll.create_index(
        [("tenant_id", 1), ("assignment_id", 1), ("created_at", 1)],
        name="ix_continuity_events_assignment",
    )
    await coll.create_index([("id", 1)], unique=True, name="ix_continuity_events_id")

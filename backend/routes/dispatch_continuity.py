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


def _now_iso_obj() -> datetime:
    return datetime.now(timezone.utc)


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
    require_shop_or_admin_dep: Optional[Callable[..., Awaitable[Dict[str, Any]]]] = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/dispatch", tags=["dispatch-continuity"])
    # iter424 · Phase 25.1 · Shop owns recovery-state WRITES. Read remains
    # any-portal. When the host wires the optional shop-or-admin dep we
    # use it; legacy callers (which pass only dispatch-or-admin) keep the
    # prior write surface so we never lock anyone out by accident.
    require_recovery_write_dep = require_shop_or_admin_dep or require_dispatch_or_admin_dep

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

    # iter423 · Phase 25 · Recent continuity chronology (read-only · capped)
    # Surfaces newest-first events for the Shop "Operational Continuity
    # History" rail. NO scoring · NO analytics · just calm chronology.
    @router.get("/continuity-events/recent")
    async def list_events_recent(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        limit: int = 25,
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        capped = max(1, min(limit, 50))
        cur = db.dispatch_continuity_events.find(
            {"tenant_id": tenant_id},
            {"_id": 0},
        ).sort("created_at", -1).limit(capped)
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

    # ════════════════════════════════════════════════════════════
    # iter423 · Phase 25 · Shop convergence — grouped recovery read
    # ────────────────────────────────────────────────────────────
    # MUST be defined BEFORE /recovery/{assignment_id} so the
    # literal `/by-shop` path is not captured by the param route.
    # ONE read-only endpoint that groups all in-flight recoveries by
    # canonical sub-state. Reuses iter420 storage · no new collection ·
    # no aggregation framework · no analytics. Each row carries a
    # tiny operational-impact line (truck_id · driver_name) so Shop
    # sees downstream operational continuity at a glance.
    @router.get("/recovery/by-shop")
    async def recovery_by_shop(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        """Group active recovery assignments by canonical recovery state.

        Returns five buckets keyed by canonical RECOVERY_STATES. Excludes
        the terminal `returned_to_service` from active buckets (it has
        its own 7-day tail). Includes `reported` so fresh, un-acknowledged
        breakdowns surface under Equipment Needing Attention.

        Downstream impact line is intentionally tiny · NO charts · NO
        scoring · NO analytics. Shop reads operational truth, not KPIs.
        """
        tenant_id = _resolve_tenant(x_tenant_id)

        active_cur = db.dispatch_assignments.find(
            {
                "tenant_id": tenant_id,
                "recovery_state": {
                    "$in": [
                        "reported", "acknowledged", "diagnosing",
                        "waiting_on_parts", "repair_active",
                        "operational_test",
                    ],
                },
            },
            {
                "_id": 0, "id": 1, "truck_id": 1, "driver_id": 1,
                "driver_name": 1, "project_number": 1, "material": 1,
                "current_state": 1, "recovery_state": 1,
                "recovery_history": 1,
            },
        )

        buckets: Dict[str, List[Dict[str, Any]]] = {
            "reported": [], "acknowledged": [], "diagnosing": [],
            "waiting_on_parts": [], "repair_active": [],
            "operational_test": [],
        }
        async for doc in active_cur:
            rs = doc.get("recovery_state")
            if rs not in buckets:
                continue
            history = doc.get("recovery_history") or []
            last_entry = history[-1] if history else None
            buckets[rs].append({
                "assignment_id": doc.get("id"),
                "truck_id": doc.get("truck_id"),
                "driver_name": doc.get("driver_name"),
                "project_number": doc.get("project_number"),
                "material": doc.get("material"),
                "current_state": doc.get("current_state"),
                "recovery_state": rs,
                "last_recovery_at": (last_entry or {}).get("at"),
                "last_recovery_note": (last_entry or {}).get("note"),
            })

        from datetime import timedelta
        seven_days_ago = (_now_iso_obj() - timedelta(days=7)).isoformat()
        restored_cur = db.dispatch_assignments.find(
            {
                "tenant_id": tenant_id,
                "recovery_state": "returned_to_service",
            },
            {
                "_id": 0, "id": 1, "truck_id": 1, "driver_name": 1,
                "project_number": 1, "recovery_state": 1,
                "recovery_history": 1,
            },
        )
        restored: List[Dict[str, Any]] = []
        async for doc in restored_cur:
            history = doc.get("recovery_history") or []
            terminal = next(
                (h for h in reversed(history) if h.get("to") == "returned_to_service"),
                None,
            )
            if not terminal:
                continue
            at = terminal.get("at") or ""
            if at < seven_days_ago:
                continue
            restored.append({
                "assignment_id": doc.get("id"),
                "truck_id": doc.get("truck_id"),
                "driver_name": doc.get("driver_name"),
                "project_number": doc.get("project_number"),
                "returned_at": at,
                "returned_by": terminal.get("by"),
                "note": terminal.get("note"),
            })
        restored.sort(key=lambda r: r.get("returned_at") or "", reverse=True)
        restored = restored[:25]

        total_active = sum(len(v) for v in buckets.values())
        today_prefix = _now_iso()[:10]
        return {
            "buckets": buckets,
            "restored_recent": restored,
            "summary": {
                "total_active": total_active,
                "waiting_on_parts": len(buckets["waiting_on_parts"]),
                "returned_today": sum(
                    1 for r in restored
                    if (r.get("returned_at") or "")[:10] == today_prefix
                ),
            },
        }

    @router.post("/recovery/{assignment_id}/transition")
    async def recovery_transition(
        assignment_id: str,
        payload: RecoveryTransition,
        actor: Dict[str, Any] = Depends(require_recovery_write_dep),
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

    # iter431 · Phase 29 · Operational Moments Rail (read-only · merged
    # chronology · NOT analytics · NOT activity feed). One round-trip
    # for the AssignmentDrawer rail so the FE never juggles four GETs
    # and four loading states. Reuses existing collections — NO new
    # collection introduced.
    @router.get("/operational-moments/by-assignment/{assignment_id}")
    async def operational_moments_by_assignment(
        assignment_id: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        """Merged chronological list of:
          • lifecycle state transitions (state_history)
          • dispatch_continuity_events
          • recovery_history transitions
          • operational_attachments uploads

        Each row is normalised to:
          {kind, ts, label, actor, actor_role, detail, source}

        Read-only · sorted ascending by `ts` so the rail reads from
        first to last like an operational truth timeline. Calm
        operational language only — no PII beyond what already lives
        in the underlying documents.
        """
        tenant_id = _resolve_tenant(x_tenant_id)
        aid = assignment_id.strip()

        assignment = await db.dispatch_assignments.find_one(
            {"id": aid, "tenant_id": tenant_id},
            {"_id": 0, "id": 1, "state_history": 1, "recovery_history": 1},
        )
        if not assignment:
            raise HTTPException(404, "Assignment not found")

        moments = []

        # 1. Lifecycle state transitions
        for h in (assignment.get("state_history") or []):
            moments.append({
                "kind": "lifecycle",
                "ts": h.get("at") or h.get("created_at"),
                "label": f"State → {h.get('to') or h.get('state') or '?'}",
                "actor": h.get("by") or h.get("actor") or "",
                "actor_role": h.get("by_role") or h.get("actor_role") or "",
                "detail": h.get("reason") or h.get("note") or "",
                "source": "state_history",
                "from_state": h.get("from"),
                "to_state": h.get("to"),
            })

        # 2. Recovery sub-state history
        for h in (assignment.get("recovery_history") or []):
            moments.append({
                "kind": "recovery",
                "ts": h.get("at") or h.get("created_at"),
                "label": f"Recovery → {h.get('to') or h.get('state') or '?'}",
                "actor": h.get("by") or h.get("actor") or "",
                "actor_role": h.get("by_role") or h.get("actor_role") or "",
                "detail": h.get("note") or "",
                "source": "recovery_history",
                "from_state": h.get("from"),
                "to_state": h.get("to"),
            })

        # 3. Continuity events
        try:
            cur = db.dispatch_continuity_events.find(
                {"tenant_id": tenant_id, "assignment_id": aid},
                {"_id": 0},
            )
            async for e in cur:
                moments.append({
                    "kind": "continuity",
                    "ts": e.get("created_at") or e.get("ts"),
                    "label": e.get("title") or e.get("kind_label") or (e.get("kind") or "event"),
                    "actor": e.get("created_by") or e.get("by") or "",
                    "actor_role": e.get("created_by_role") or e.get("by_role") or "",
                    "detail": e.get("note") or e.get("detail") or "",
                    "source": "dispatch_continuity_events",
                    "event_kind": e.get("kind"),
                })
        except Exception:
            pass

        # 4. Operational attachments (load proof · breakdown photos · etc.)
        try:
            cur = db.operational_attachments.find(
                {"tenant_id": tenant_id, "host_kind": "assignment", "host_id": aid},
                {"_id": 0, "data_b64": 0, "r2_key": 0},  # never expose bytes here
            )
            async for a in cur:
                moments.append({
                    "kind": "attachment",
                    "ts": a.get("uploaded_at"),
                    "label": f"Attachment · {a.get('type') or 'photo'}",
                    "actor": a.get("uploaded_by") or "",
                    "actor_role": a.get("uploaded_role") or "",
                    "detail": a.get("operational_note") or "",
                    "source": "operational_attachments",
                    "attachment_id": a.get("id"),
                    "attachment_type": a.get("type"),
                    "filename": a.get("filename"),
                })
        except Exception:
            pass

        # Sort ascending by ts (string-sortable ISO-8601). Empties last
        # so a missing timestamp doesn't poison the ordering.
        def _key(m):
            return (m.get("ts") or "9999-99-99T99:99:99")
        moments.sort(key=_key)

        return {
            "assignment_id": aid,
            "count": len(moments),
            "moments": moments,
        }

    return router


async def ensure_dispatch_continuity_indexes(db) -> None:
    coll = db.dispatch_continuity_events
    await coll.create_index(
        [("tenant_id", 1), ("assignment_id", 1), ("created_at", 1)],
        name="ix_continuity_events_assignment",
    )
    await coll.create_index([("id", 1)], unique=True, name="ix_continuity_events_id")

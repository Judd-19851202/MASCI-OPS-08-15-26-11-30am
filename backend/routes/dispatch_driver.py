"""
routes/dispatch_driver.py · iter393 · DLS Driver Mobile Surface.

The minimal API surface the driver mobile experience consumes. Every
endpoint is intentionally narrow — the driver token is scope-limited to
the driver's own currently-assigned haul cycle.

Endpoints (prefix /api/dispatch/driver):
  • POST /magic-link                       dispatch + admin only · issue link
  • POST /session/exchange                 public · exchange magic token
  • GET  /me                               driver · session info
  • GET  /my-assignment                    driver · current assignment + allowed next states
  • POST /assignments/{id}/transition      driver · one-tap state change (forgiving)
  • POST /sessions/{id}/revoke             dispatch + admin only · revoke a session
  • GET  /sessions                         dispatch + admin only · list active sessions

The driver-side handlers DELEGATE every state mutation to the existing
iter392 ``_record_transition`` writer so the lifecycle engine remains
the single source of truth (no parallel pipelines).
"""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field

import dispatch_lifecycle as DLS
import driver_sessions as DS
from routes.dispatch_lifecycle import (
    DEFAULT_TENANT_ID,
    _record_transition,                                            # reuse
)

logger = logging.getLogger("dispatch_driver_routes")


# ════════════════════════════════════════════════════════════════════
# Pydantic models
# ════════════════════════════════════════════════════════════════════
class MagicLinkRequest(BaseModel):
    driver_id: str = Field(..., min_length=1, max_length=120)
    driver_name: Optional[str] = ""
    truck_id: Optional[str] = ""
    assignment_id: Optional[str] = ""


class SessionExchangeRequest(BaseModel):
    magic_token: str = Field(..., min_length=8, max_length=240)


class StartShiftRequest(BaseModel):
    """iter401 · Phase 12.8 · driver self-start (no dispatcher needed)."""
    driver_name: str = Field(..., min_length=1, max_length=120)
    truck_id: str = Field(..., min_length=1, max_length=64)
    company: Optional[str] = Field(default="", max_length=120)
    trailer_id: Optional[str] = Field(default="", max_length=64)
    material: Optional[str] = Field(default="", max_length=120)


class DriverTransitionRequest(BaseModel):
    to_state: str = Field(..., min_length=1, max_length=64)
    note: Optional[str] = ""
    wait_reason: Optional[str] = ""
    correction_reason: Optional[str] = ""
    geo: Optional[Dict[str, Any]] = None


# ════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════
def _resolve_tenant(x_tenant_id: Optional[str]) -> str:
    if x_tenant_id and isinstance(x_tenant_id, str) and x_tenant_id.strip():
        return x_tenant_id.strip()
    return DEFAULT_TENANT_ID


def _public_link_for(request: Request, raw_token: str) -> str:
    """Build the magic-link URL the dispatcher reads/QR-shares. Uses
    the request's own scheme+host so preview / prod produce correct
    links without env coupling."""
    base = str(request.base_url).rstrip("/")
    # Strip /api if base_url ever inherits it (FastAPI returns the
    # mount root; in our setup it's the bare host).
    if base.endswith("/api"):
        base = base[:-4]
    return f"{base}/d/{raw_token}"


async def _current_assignment_for_session(
    db, *, session: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Resolve the haul assignment a driver should currently see.

    Priority:
      1. If the session was issued with a pinned ``assignment_id`` use that.
      2. Otherwise, latest non-terminal, non-cancelled assignment for
         the driver in their tenant (``driver_id`` match — magic-link path).
      3. iter401 fallback (self-start path): if no driver_id match AND
         the session carries a ``truck_id``, find the latest active
         assignment for that truck regardless of who originally owned it.
         Trucks rotate drivers; operational continuity follows the truck.
    """
    tenant_id = session["tenant_id"]
    pinned = session.get("assignment_id")
    if pinned:
        doc = await db.dispatch_assignments.find_one(
            {"id": pinned, "tenant_id": tenant_id},
            {"_id": 0},
        )
        if doc:
            return doc
    # 2 · driver_id match (magic-link path)
    cursor = (
        db.dispatch_assignments
        .find(
            {
                "tenant_id": tenant_id,
                "driver_id": session["driver_id"],
                "current_state": {"$nin": [DLS.COMPLETE, DLS.OFF_SHIFT]},
                "cancelled_at": None,
            },
            {"_id": 0},
        )
        .sort("assigned_at", -1)
        .limit(1)
    )
    rows = await cursor.to_list(length=1)
    if rows:
        return rows[0]
    # 3 · iter401 truck_id fallback (self-start path)
    truck_id = (session.get("truck_id") or "").strip()
    if truck_id:
        cursor = (
            db.dispatch_assignments
            .find(
                {
                    "tenant_id": tenant_id,
                    "truck_id": truck_id,
                    "current_state": {"$nin": [DLS.COMPLETE, DLS.OFF_SHIFT]},
                    "cancelled_at": None,
                },
                {"_id": 0},
            )
            .sort("assigned_at", -1)
            .limit(1)
        )
        rows = await cursor.to_list(length=1)
        if rows:
            return rows[0]
    return None


# ════════════════════════════════════════════════════════════════════
# Router factory
# ════════════════════════════════════════════════════════════════════
def build_driver_router(
    db,
    require_dispatch_or_admin_dep: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    router = APIRouter(prefix="/api/dispatch/driver", tags=["dispatch-driver"])
    require_driver = DS.make_require_driver_session(db)

    # ────────────────────────────────────────────────────────────────
    # iter401 · Phase 12.8 · Driver self-start operational entry
    # ────────────────────────────────────────────────────────────────
    @router.post("/start-shift")
    async def start_shift_route(
        body: StartShiftRequest,
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        """Public · driver self-starts a shift.

        No dispatcher action required. No password. The driver lands on
        ``/shift``, fills four short fields, taps Start Shift, and gets a
        shift-scoped session immediately.

        Identity model: the synthetic ``driver_id`` is ``shift-<12hex>``.
        Trucks rotate drivers; the truck_id is the operational continuity
        key — assignments owned by this truck become visible to whichever
        driver is currently shifted onto it.

        Idempotence-ish: if an active session already exists for the same
        (tenant, truck), the previous session is revoked (last driver
        wins) so an old phone left logged in doesn't keep a stale claim.
        """
        import uuid as _uuid
        tenant_id = _resolve_tenant(x_tenant_id)
        driver_name = body.driver_name.strip()
        truck_id = body.truck_id.strip()
        if not driver_name or not truck_id:
            raise HTTPException(400, "Driver name and truck number are required")

        # Last-driver-wins: revoke any active session on this truck.
        try:
            stale = db.dispatch_driver_sessions.find(
                {
                    "tenant_id": tenant_id,
                    "truck_id": truck_id,
                    "revoked_at": None,
                },
                {"_id": 0, "id": 1},
            )
            async for s in stale:
                await DS.revoke_driver_session(
                    db,
                    session_id=s["id"],
                    revoked_by_name=f"Truck claimed by {driver_name}",
                )
        except Exception:
            # Non-fatal — fresh session still issues; stale will TTL.
            pass

        synthetic_driver_id = f"shift-{_uuid.uuid4().hex[:12]}"
        session = await DS.create_driver_session(
            db,
            tenant_id=tenant_id,
            driver_id=synthetic_driver_id,
            driver_name=driver_name,
            truck_id=truck_id,
            assignment_id=None,
            issued_by_name=driver_name,
            origin="self_start",
            company=body.company or None,
            trailer_id=body.trailer_id or None,
            material=body.material or None,
        )

        # Land the driver directly on their assignment if one exists.
        assignment = None
        try:
            session_row = await db.dispatch_driver_sessions.find_one(
                {"id": session["session_id"]}, {"_id": 0},
            )
            if session_row:
                assignment = await _current_assignment_for_session(
                    db, session=session_row,
                )
        except Exception:
            assignment = None

        return {
            "ok": True,
            "driver_token": session["token"],
            "session_id": session["session_id"],
            "expires_at": session["expires_at"],
            "tenant_id": tenant_id,
            "driver": {
                "driver_id": synthetic_driver_id,
                "driver_name": driver_name,
            },
            "shift": {
                "truck_id": truck_id,
                "company": (body.company or "").strip() or None,
                "trailer_id": (body.trailer_id or "").strip() or None,
                "material": (body.material or "").strip() or None,
            },
            "assignment": assignment,
        }

    # ────────────────────────────────────────────────────────────────
    # Magic link issuance (dispatch/admin) and exchange (public)
    # ────────────────────────────────────────────────────────────────
    @router.post("/magic-link")
    async def issue_magic_link_route(
        body: MagicLinkRequest,
        request: Request,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        result = await DS.issue_magic_link(
            db,
            tenant_id=tenant_id,
            driver_id=body.driver_id.strip(),
            driver_name=(body.driver_name or "").strip(),
            truck_id=(body.truck_id or "").strip() or None,
            assignment_id=(body.assignment_id or "").strip() or None,
            issued_by_name=(actor.get("name") or actor.get("email") or "Dispatch"),
            issued_by_role=actor.get("_actor") or "dispatch",
        )
        return {
            "ok": True,
            "link_id": result["link_id"],
            "magic_token": result["token"],
            "expires_at": result["expires_at"],
            "url": _public_link_for(request, result["token"]),
            "ttl_seconds": DS.MAGIC_TOKEN_TTL_SECONDS,
        }

    @router.post("/session/exchange")
    async def exchange_magic_link_route(
        body: SessionExchangeRequest,
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        # Magic links are tenant-aware but the URL itself doesn't
        # encode tenant — header (default masci) decides scope.
        tenant_id = _resolve_tenant(x_tenant_id)
        link = await DS.consume_magic_link(
            db, raw_token=body.magic_token, tenant_id=tenant_id,
        )
        if not link:
            raise HTTPException(401, "Magic link invalid, used, or expired")

        session = await DS.create_driver_session(
            db,
            tenant_id=link["tenant_id"],
            driver_id=link["driver_id"],
            driver_name=link.get("driver_name") or "",
            truck_id=link.get("truck_id"),
            assignment_id=link.get("assignment_id"),
            issued_by_name=link.get("issued_by_name") or "",
        )
        await DS.mark_magic_link_used(
            db, link_id=link["id"], session_id=session["session_id"],
        )

        # Best-effort: also return the current assignment so the
        # driver UI lands directly on the shift screen.
        assignment = None
        try:
            session_row = await db.dispatch_driver_sessions.find_one(
                {"id": session["session_id"]}, {"_id": 0},
            )
            if session_row:
                assignment = await _current_assignment_for_session(
                    db, session=session_row,
                )
        except Exception:
            assignment = None

        return {
            "ok": True,
            "driver_token": session["token"],
            "session_id": session["session_id"],
            "expires_at": session["expires_at"],
            "tenant_id": link["tenant_id"],
            "driver": {
                "driver_id": link["driver_id"],
                "driver_name": link.get("driver_name") or "",
            },
            "assignment": assignment,
        }

    # ────────────────────────────────────────────────────────────────
    # Driver self-service reads
    # ────────────────────────────────────────────────────────────────
    @router.get("/me")
    async def driver_me(
        session: Dict[str, Any] = Depends(require_driver),
    ):
        return {
            "ok": True,
            "session": {
                "id": session["id"],
                "tenant_id": session["tenant_id"],
                "driver_id": session["driver_id"],
                "driver_name": session.get("driver_name") or "",
                "truck_id": session.get("truck_id"),
                "issued_at": session.get("issued_at"),
                "expires_at": session.get("expires_at"),
                "last_seen_at": session.get("last_seen_at"),
            },
        }

    @router.get("/my-assignment")
    async def driver_my_assignment(
        session: Dict[str, Any] = Depends(require_driver),
    ):
        assignment = await _current_assignment_for_session(db, session=session)
        if not assignment:
            return {
                "ok": True,
                "assignment": None,
                "allowed_next_states": [],
                "lifecycle_states": DLS.CANONICAL_STATES,
            }
        return {
            "ok": True,
            "assignment": assignment,
            "allowed_next_states": DLS.allowed_next_states(
                assignment.get("current_state") or "",
            ),
            "lifecycle_states": DLS.CANONICAL_STATES,
        }

    @router.post("/assignments/{assignment_id}/transition")
    async def driver_transition(
        assignment_id: str,
        body: DriverTransitionRequest,
        session: Dict[str, Any] = Depends(require_driver),
    ):
        tenant_id = session["tenant_id"]
        assignment = await db.dispatch_assignments.find_one(
            {"id": assignment_id, "tenant_id": tenant_id}, {"_id": 0},
        )
        if not assignment:
            raise HTTPException(404, "Assignment not found")
        # Scope: drivers can only transition assignments tied to them
        # OR — iter401 self-start path — assignments owned by the same
        # truck this driver is currently shifted onto. Trucks rotate
        # drivers; operational continuity follows the truck.
        if assignment.get("driver_id") and assignment["driver_id"] != session["driver_id"]:
            truck_id = (session.get("truck_id") or "").strip()
            if not truck_id or assignment.get("truck_id") != truck_id:
                raise HTTPException(
                    403,
                    "Driver session is not authorized for this assignment",
                )
        if assignment.get("cancelled_at"):
            raise HTTPException(409, "Assignment is cancelled")

        actor = {
            "_actor": "driver",
            "name": session.get("driver_name") or "Driver",
        }
        updated = await _record_transition(
            db,
            assignment=assignment,
            to_state=body.to_state.strip(),
            actor=actor,
            note=body.note or "",
            correction_reason=body.correction_reason or "",
            wait_reason=body.wait_reason or "",
            geo=body.geo,
        )
        latest = (updated.get("state_history") or [])[-1] if updated else None
        return {
            "ok": True,
            "assignment": updated,
            "transition": latest,
            "allowed_next_states": DLS.allowed_next_states(
                (updated or {}).get("current_state") or "",
            ),
        }

    # ────────────────────────────────────────────────────────────────
    # Dispatcher management of driver sessions
    # ────────────────────────────────────────────────────────────────
    @router.get("/sessions")
    async def list_sessions(
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        active_only: bool = True,
        limit: int = 100,
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        query: Dict[str, Any] = {"tenant_id": tenant_id}
        if active_only:
            query["revoked_at"] = None
        limit = max(1, min(int(limit or 100), 500))
        cursor = (
            db.dispatch_driver_sessions
            .find(query, {"_id": 0})
            .sort("issued_at", -1)
            .limit(limit)
        )
        rows: List[Dict[str, Any]] = await cursor.to_list(length=limit)
        # Drop the native datetime field — not JSON serializable.
        for r in rows:
            r.pop("expires_at_ts", None)
        return {
            "ok": True,
            "tenant_id": tenant_id,
            "count": len(rows),
            "sessions": rows,
        }

    @router.post("/sessions/{session_id}/revoke")
    async def revoke_session(
        session_id: str,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        # Optional tenant guard — ensure the session belongs to the
        # caller's tenant. Cheap one-document lookup.
        row = await db.dispatch_driver_sessions.find_one(
            {"id": session_id, "tenant_id": tenant_id}, {"_id": 0},
        )
        if not row:
            raise HTTPException(404, "Session not found")
        revoked = await DS.revoke_driver_session(
            db,
            session_id=session_id,
            revoked_by_name=actor.get("name") or actor.get("email") or "Dispatch",
        )
        return {"ok": True, "revoked": revoked, "session_id": session_id}

    return router


__all__ = ["build_driver_router"]

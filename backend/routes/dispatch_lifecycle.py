"""
routes/dispatch_lifecycle.py · iter392 · Phase 11.1 · DLS Backend Foundation.

Backend foundation for the Dispatch Lifecycle System.

Scope (iter392):
  • 3 Mongo collections (tenant-ready from day 1):
      - dispatch_assignments  (operational current truth)
      - dispatch_state_events (append-only analytics/audit truth)
      - haul_cycles           (derived cycle summary truth)
  • State-machine wiring (forgiving mode — see dispatch_lifecycle module).
  • REST API for create / read / transition / cancel / reassign.
  • RBAC: writes = dispatch+admin, reads = any portal token.

Out of scope (deferred):
  • Driver magic-link session (iter393).
  • Frontend (iter393 / iter394).
  • Governance detectors, CSV exports, notifications fan-out (iter395).
  • Glossary / coaching / ES translations (iter396).

Doctrine: lifecycle truth first. Operations never get trapped by rigid
validation. Every transition is recorded — non-standard ones are tagged
for future governance review.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel, Field

import dispatch_lifecycle as DLS

logger = logging.getLogger("dispatch_lifecycle_routes")

DEFAULT_TENANT_ID = "masci"
_BOARD_DEFAULT_LIMIT = 200
_BOARD_MAX_LIMIT = 500
_HISTORY_DEFAULT_LIMIT = 500
_HISTORY_MAX_LIMIT = 2000


# ════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


def _resolve_tenant(x_tenant_id: Optional[str]) -> str:
    """Tenant resolution. iter392 is single-tenant — but every record
    carries ``tenant_id`` so a future multi-tenant phase can filter
    without schema migration. Operators can pass ``X-Tenant-Id`` to
    override the default."""
    if x_tenant_id and isinstance(x_tenant_id, str) and x_tenant_id.strip():
        return x_tenant_id.strip()
    return DEFAULT_TENANT_ID


def _actor_label(actor: Dict[str, Any]) -> str:
    """Best-effort human label for state_history.by_name."""
    if not isinstance(actor, dict):
        return "system"
    return (
        actor.get("name")
        or actor.get("email")
        or actor.get("_actor")
        or "actor"
    )


def _actor_role(actor: Dict[str, Any]) -> str:
    if not isinstance(actor, dict):
        return "system"
    return actor.get("_actor") or "actor"


# ════════════════════════════════════════════════════════════════════
# Pydantic models
# ════════════════════════════════════════════════════════════════════
class AssignmentCreate(BaseModel):
    truck_id: str = Field(..., min_length=1, max_length=80)
    driver_id: Optional[str] = None
    driver_name: Optional[str] = ""
    project_number: Optional[str] = ""
    project_name: Optional[str] = ""
    material: Optional[str] = ""
    source_location: Optional[str] = ""
    destination: Optional[str] = ""
    loader_operator_name: Optional[str] = ""
    note: Optional[str] = ""
    # iter408 · Phase 14.2 · Haul Type continuity
    haul_type: Optional[str] = "Material"
    trailer_id: Optional[str] = ""
    trailer_label: Optional[str] = ""
    carrier: Optional[str] = ""
    equipment_id: Optional[str] = ""
    equipment_label: Optional[str] = ""
    pickup_location: Optional[str] = ""
    dropoff_location: Optional[str] = ""
    # iter410 · Phase 15.1 · Tanker / Liquid Asphalt continuity
    liquid_product: Optional[str] = ""


class TransitionRequest(BaseModel):
    to_state: str = Field(..., min_length=1, max_length=64)
    note: Optional[str] = ""
    correction_reason: Optional[str] = ""
    wait_reason: Optional[str] = ""          # captured when to_state == WAITING
    geo: Optional[Dict[str, Any]] = None     # optional {lat,lng,accuracy}


class CancelRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=240)


class ReassignRequest(BaseModel):
    new_driver_id: Optional[str] = None
    new_driver_name: Optional[str] = ""
    new_truck_id: Optional[str] = None
    reason: Optional[str] = ""


# ════════════════════════════════════════════════════════════════════
# Index setup
# ════════════════════════════════════════════════════════════════════
async def ensure_dispatch_lifecycle_indexes(db) -> None:
    """Create the indexes that power the operational board, history
    queries, and future tenant filtering. Safe to call multiple times
    (Mongo dedupes by index spec)."""
    try:
        await asyncio.gather(
            # dispatch_assignments — operational current truth
            db.dispatch_assignments.create_index(
                [("tenant_id", 1), ("current_state", 1), ("assigned_at", -1)],
                name="da_tenant_state_assigned",
            ),
            db.dispatch_assignments.create_index(
                [("tenant_id", 1), ("truck_id", 1), ("current_state", 1)],
                name="da_tenant_truck_state",
            ),
            db.dispatch_assignments.create_index(
                [("tenant_id", 1), ("driver_id", 1), ("assigned_at", -1)],
                name="da_tenant_driver_assigned",
            ),
            db.dispatch_assignments.create_index(
                [("tenant_id", 1), ("project_number", 1), ("assigned_at", -1)],
                name="da_tenant_project_assigned",
            ),
            db.dispatch_assignments.create_index("id", unique=True, name="da_id_unique"),

            # dispatch_state_events — append-only audit/analytics truth
            db.dispatch_state_events.create_index(
                [("tenant_id", 1), ("assignment_id", 1), ("at", 1)],
                name="dse_tenant_assignment_at",
            ),
            db.dispatch_state_events.create_index(
                [("tenant_id", 1), ("at", -1)],
                name="dse_tenant_at_desc",
            ),
            db.dispatch_state_events.create_index(
                [("tenant_id", 1), ("standard", 1), ("at", -1)],
                name="dse_tenant_standard_at",
            ),
            db.dispatch_state_events.create_index("id", unique=True, name="dse_id_unique"),

            # haul_cycles — derived cycle summary truth (one row per
            # completed cycle)
            db.haul_cycles.create_index(
                [("tenant_id", 1), ("completed_at", -1)],
                name="hc_tenant_completed_desc",
            ),
            db.haul_cycles.create_index(
                [("tenant_id", 1), ("truck_id", 1), ("completed_at", -1)],
                name="hc_tenant_truck_completed",
            ),
            db.haul_cycles.create_index(
                [("tenant_id", 1), ("project_number", 1), ("completed_at", -1)],
                name="hc_tenant_project_completed",
            ),
            db.haul_cycles.create_index(
                "assignment_id", unique=True, name="hc_assignment_unique",
            ),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[dispatch-lifecycle-index] {e}")


# ════════════════════════════════════════════════════════════════════
# Core transition engine
# ════════════════════════════════════════════════════════════════════
async def _record_transition(
    db,
    *,
    assignment: Dict[str, Any],
    to_state: str,
    actor: Dict[str, Any],
    note: str = "",
    correction_reason: str = "",
    wait_reason: str = "",
    geo: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """The single transition writer. Updates the assignment, appends to
    state_history[], mirrors a row into dispatch_state_events, and if
    the destination is COMPLETE writes a derived haul_cycles row.

    Returns the updated assignment dict (without _id)."""
    tenant_id = assignment.get("tenant_id") or DEFAULT_TENANT_ID
    from_state = assignment.get("current_state")
    classification = DLS.classify_transition(from_state, to_state)
    standard = bool(classification["standard"])
    warning_tag = classification["warning_tag"]
    warning_tags = list(classification["warning_tags"])

    at_iso = _now_iso()
    by_name = _actor_label(actor)
    by_role = _actor_role(actor)

    history_entry = {
        "from_state": from_state,
        "to_state": to_state,
        "at": at_iso,
        "by_name": by_name,
        "by_role": by_role,
        "standard": standard,
        "warning_tag": warning_tag,
        "warning_tags": warning_tags,
        "note": note or "",
        "correction_reason": correction_reason or "",
        "wait_reason": wait_reason or "",
        "geo": geo or None,
    }

    update_fields: Dict[str, Any] = {
        "current_state": to_state,
        "updated_at": at_iso,
        "last_transition_at": at_iso,
    }
    if to_state == DLS.WAITING:
        update_fields["current_wait_reason"] = wait_reason or ""
    else:
        # Clear stale wait reason whenever leaving WAITING.
        update_fields["current_wait_reason"] = ""
    if to_state == DLS.COMPLETE:
        update_fields["completed_at"] = at_iso
    if to_state == DLS.OFF_SHIFT:
        update_fields["ended_at"] = at_iso

    await db.dispatch_assignments.update_one(
        {"id": assignment["id"]},
        {
            "$set": update_fields,
            "$push": {"state_history": history_entry},
        },
    )

    # Mirror into the append-only event stream (always — even for
    # the seed ASSIGNED entry written by create()).
    event_doc = {
        "id": _new_id(),
        "tenant_id": tenant_id,
        "assignment_id": assignment["id"],
        "truck_id": assignment.get("truck_id"),
        "driver_id": assignment.get("driver_id"),
        "driver_name": assignment.get("driver_name") or "",
        "project_number": assignment.get("project_number") or "",
        "from_state": from_state,
        "to_state": to_state,
        "standard": standard,
        "warning_tag": warning_tag,
        "warning_tags": warning_tags,
        "at": at_iso,
        "by_name": by_name,
        "by_role": by_role,
        "note": note or "",
        "correction_reason": correction_reason or "",
        "wait_reason": wait_reason or "",
        "geo": geo or None,
    }
    await db.dispatch_state_events.insert_one(event_doc)

    # Derive haul_cycles row on COMPLETE. Idempotent via unique
    # assignment_id index — replay-safe.
    if to_state == DLS.COMPLETE:
        await _materialize_haul_cycle(
            db, assignment_id=assignment["id"], tenant_id=tenant_id,
        )

    # Return the updated assignment (re-read so the caller gets a
    # consistent snapshot, including the newly appended history row).
    updated = await db.dispatch_assignments.find_one(
        {"id": assignment["id"]}, {"_id": 0},
    )
    return updated or {}


async def _materialize_haul_cycle(db, *, assignment_id: str, tenant_id: str) -> None:
    """Build the haul_cycles summary row for a completed assignment.

    Pulls timing facts straight off state_history. Idempotent.
    """
    assignment = await db.dispatch_assignments.find_one(
        {"id": assignment_id}, {"_id": 0},
    )
    if not assignment:
        return
    history: List[Dict[str, Any]] = list(assignment.get("state_history") or [])
    if not history:
        return

    started_at = assignment.get("assigned_at") or (history[0].get("at") if history else None)
    completed_at = assignment.get("completed_at") or history[-1].get("at")

    def _epoch(iso: Optional[str]) -> Optional[float]:
        if not iso:
            return None
        try:
            return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
        except Exception:
            return None

    started_epoch = _epoch(started_at)
    completed_epoch = _epoch(completed_at)
    total_seconds: Optional[int] = None
    if started_epoch is not None and completed_epoch is not None:
        total_seconds = max(0, int(completed_epoch - started_epoch))

    # Compute wait_seconds — time spent in WAITING blocks across the
    # cycle, derived from the timestamps in state_history.
    wait_seconds = 0
    for idx, entry in enumerate(history):
        if entry.get("to_state") != DLS.WAITING:
            continue
        wait_start = _epoch(entry.get("at"))
        if wait_start is None:
            continue
        # Find the next transition out of WAITING. If none, use
        # completed_epoch as the wait end.
        wait_end = completed_epoch
        for later in history[idx + 1:]:
            ep = _epoch(later.get("at"))
            if ep is not None:
                wait_end = ep
                break
        if wait_end is not None and wait_end >= wait_start:
            wait_seconds += int(wait_end - wait_start)

    cycle_doc = {
        "id": _new_id(),
        "tenant_id": tenant_id,
        "assignment_id": assignment_id,
        "truck_id": assignment.get("truck_id"),
        "driver_id": assignment.get("driver_id"),
        "driver_name": assignment.get("driver_name") or "",
        "project_number": assignment.get("project_number") or "",
        "project_name": assignment.get("project_name") or "",
        "material": assignment.get("material") or "",
        "source_location": assignment.get("source_location") or "",
        "destination": assignment.get("destination") or "",
        # iter409 · Phase 14.3 · cycle continuity for haul-type-aware
        # PM production awareness. Additive — historical cycles will
        # simply read these fields as empty strings.
        "haul_type": assignment.get("haul_type") or "Material",
        "equipment_label": assignment.get("equipment_label") or "",
        "pickup_location": assignment.get("pickup_location") or "",
        "dropoff_location": assignment.get("dropoff_location") or "",
        # iter410 · Phase 15.1 · Tanker continuity carried into cycle truth
        "liquid_product": assignment.get("liquid_product") or "",
        "started_at": started_at,
        "completed_at": completed_at,
        "total_seconds": total_seconds,
        "wait_seconds": wait_seconds,
        "operating_seconds": (
            max(0, (total_seconds or 0) - wait_seconds) if total_seconds is not None else None
        ),
        "transitions": len(history),
        "non_standard_transitions": sum(
            1 for h in history if not h.get("standard", True)
        ),
        "created_at": _now_iso(),
    }
    try:
        await db.haul_cycles.insert_one(cycle_doc)
    except Exception as e:  # noqa: BLE001
        # Duplicate (assignment_id unique) — log and move on. The
        # earlier-written row is the canonical summary.
        logger.info(f"[haul_cycle] dedupe assignment_id={assignment_id}: {e}")


# ════════════════════════════════════════════════════════════════════
# Router factory
# ════════════════════════════════════════════════════════════════════
def build_dispatch_lifecycle_router(
    db,
    require_dispatch_or_admin_dep: Callable[..., Awaitable[Dict[str, Any]]],
    require_any_portal_token_dep: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    """Build the DLS router.

    Args:
      db: motor database handle.
      require_dispatch_or_admin_dep: WRITE gate. Reused from server.py
        (same gate that protects /api/dispatch/* writes today).
      require_any_portal_token_dep: READ gate. Lets PMs / Safety / HR /
        Shop / FL / Admin see haul activity tied to their portal — no
        new auth surface introduced.
    """
    router = APIRouter(prefix="/api/dispatch", tags=["dispatch-lifecycle"])

    # ────────────────────────────────────────────────────────────────
    # CREATE
    # ────────────────────────────────────────────────────────────────
    @router.post("/assignments")
    async def create_assignment(
        body: AssignmentCreate,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        at_iso = _now_iso()
        assignment_id = _new_id()
        by_name = _actor_label(actor)
        by_role = _actor_role(actor)

        seed_history_entry = {
            "from_state": None,
            "to_state": DLS.ASSIGNED,
            "at": at_iso,
            "by_name": by_name,
            "by_role": by_role,
            "standard": True,
            "warning_tag": None,
            "warning_tags": [],
            "note": body.note or "",
            "correction_reason": "",
            "wait_reason": "",
            "geo": None,
        }
        doc = {
            "id": assignment_id,
            "tenant_id": tenant_id,
            "truck_id": body.truck_id.strip(),
            "driver_id": (body.driver_id or "").strip() or None,
            "driver_name": (body.driver_name or "").strip(),
            "project_number": (body.project_number or "").strip(),
            "project_name": (body.project_name or "").strip(),
            "material": (body.material or "").strip(),
            "source_location": (body.source_location or "").strip(),
            "destination": (body.destination or "").strip(),
            "loader_operator_name": (body.loader_operator_name or "").strip(),
            # iter408 · Phase 14.2 · Haul Type continuity (additive,
            # backward-compatible — legacy assignments simply default
            # haul_type to "Material" via the model).
            "haul_type": (body.haul_type or "Material").strip() or "Material",
            "trailer_id": (body.trailer_id or "").strip(),
            "trailer_label": (body.trailer_label or "").strip(),
            "carrier": (body.carrier or "").strip(),
            "equipment_id": (body.equipment_id or "").strip(),
            "equipment_label": (body.equipment_label or "").strip(),
            "pickup_location": (body.pickup_location or "").strip(),
            "dropoff_location": (body.dropoff_location or "").strip(),
            # iter410 · Phase 15.1 · Tanker / Liquid Asphalt continuity
            "liquid_product": (body.liquid_product or "").strip(),
            "current_state": DLS.ASSIGNED,
            "current_wait_reason": "",
            "assigned_at": at_iso,
            "assigned_by_name": by_name,
            "assigned_by_role": by_role,
            "last_transition_at": at_iso,
            "completed_at": None,
            "ended_at": None,
            "cancelled_at": None,
            "cancel_reason": None,
            "state_history": [seed_history_entry],
            "wait_events": [],
            "motive_validation": None,
            "created_at": at_iso,
            "updated_at": at_iso,
            "source": "dispatch_lifecycle_v1",
        }
        await db.dispatch_assignments.insert_one(doc)

        # Mirror the seed ASSIGNED into the event stream.
        event_doc = {
            "id": _new_id(),
            "tenant_id": tenant_id,
            "assignment_id": assignment_id,
            "truck_id": doc["truck_id"],
            "driver_id": doc["driver_id"],
            "driver_name": doc["driver_name"],
            "project_number": doc["project_number"],
            "from_state": None,
            "to_state": DLS.ASSIGNED,
            "standard": True,
            "warning_tag": None,
            "warning_tags": [],
            "at": at_iso,
            "by_name": by_name,
            "by_role": by_role,
            "note": body.note or "",
            "correction_reason": "",
            "wait_reason": "",
            "geo": None,
        }
        await db.dispatch_state_events.insert_one(event_doc)

        # Re-read to drop _id (insert_one mutates the input dict).
        out = await db.dispatch_assignments.find_one({"id": assignment_id}, {"_id": 0})
        return {"ok": True, "assignment": out}

    # ────────────────────────────────────────────────────────────────
    # LIST · BOARD · DETAIL (cross-portal read)
    # ────────────────────────────────────────────────────────────────
    @router.get("/assignments/board")
    async def get_board(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        limit: int = Query(_BOARD_DEFAULT_LIMIT, ge=1, le=_BOARD_MAX_LIMIT),
    ):
        """Live operational board — active assignments (anything not
        in a terminal state) sorted by assigned_at desc."""
        tenant_id = _resolve_tenant(x_tenant_id)
        query = {
            "tenant_id": tenant_id,
            "current_state": {"$nin": [DLS.COMPLETE, DLS.OFF_SHIFT]},
            "cancelled_at": None,
        }
        cursor = (
            db.dispatch_assignments
            .find(query, {"_id": 0})
            .sort("assigned_at", -1)
            .limit(limit)
        )
        rows = await cursor.to_list(length=limit)
        return {"ok": True, "tenant_id": tenant_id, "count": len(rows), "assignments": rows}

    @router.get("/assignments")
    async def list_assignments(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        truck_id: Optional[str] = None,
        driver_id: Optional[str] = None,
        project_number: Optional[str] = None,
        state: Optional[str] = None,
        include_completed: bool = False,
        limit: int = Query(100, ge=1, le=_BOARD_MAX_LIMIT),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        query: Dict[str, Any] = {"tenant_id": tenant_id}
        if truck_id:
            query["truck_id"] = truck_id
        if driver_id:
            query["driver_id"] = driver_id
        if project_number:
            query["project_number"] = project_number
        if state:
            query["current_state"] = state
        elif not include_completed:
            query["current_state"] = {"$nin": [DLS.COMPLETE, DLS.OFF_SHIFT]}
            query["cancelled_at"] = None
        cursor = (
            db.dispatch_assignments
            .find(query, {"_id": 0})
            .sort("assigned_at", -1)
            .limit(limit)
        )
        rows = await cursor.to_list(length=limit)
        return {"ok": True, "tenant_id": tenant_id, "count": len(rows), "assignments": rows}

    @router.get("/assignments/{assignment_id}")
    async def get_assignment(
        assignment_id: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        doc = await db.dispatch_assignments.find_one(
            {"id": assignment_id, "tenant_id": tenant_id}, {"_id": 0},
        )
        if not doc:
            raise HTTPException(404, "Assignment not found")
        return {"ok": True, "assignment": doc}

    # ────────────────────────────────────────────────────────────────
    # TRANSITION (write — forgiving mode)
    # ────────────────────────────────────────────────────────────────
    @router.post("/assignments/{assignment_id}/transition")
    async def transition_assignment(
        assignment_id: str,
        body: TransitionRequest,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        assignment = await db.dispatch_assignments.find_one(
            {"id": assignment_id, "tenant_id": tenant_id}, {"_id": 0},
        )
        if not assignment:
            raise HTTPException(404, "Assignment not found")
        if assignment.get("cancelled_at"):
            raise HTTPException(
                409,
                "Assignment is cancelled — create a new assignment instead of transitioning.",
            )
        to_state = body.to_state.strip()
        if not to_state:
            raise HTTPException(422, "to_state is required")
        # Forgiving mode: we accept any to_state. classify_transition
        # tags non-canonical and non-standard transitions.
        updated = await _record_transition(
            db,
            assignment=assignment,
            to_state=to_state,
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
        }

    # ────────────────────────────────────────────────────────────────
    # CANCEL
    # ────────────────────────────────────────────────────────────────
    @router.post("/assignments/{assignment_id}/cancel")
    async def cancel_assignment(
        assignment_id: str,
        body: CancelRequest,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        assignment = await db.dispatch_assignments.find_one(
            {"id": assignment_id, "tenant_id": tenant_id}, {"_id": 0},
        )
        if not assignment:
            raise HTTPException(404, "Assignment not found")
        if assignment.get("cancelled_at"):
            raise HTTPException(409, "Already cancelled")

        at_iso = _now_iso()
        by_name = _actor_label(actor)
        by_role = _actor_role(actor)
        history_entry = {
            "from_state": assignment.get("current_state"),
            "to_state": "CANCELLED",
            "at": at_iso,
            "by_name": by_name,
            "by_role": by_role,
            "standard": False,
            "warning_tag": "CANCELLED",
            "warning_tags": ["CANCELLED"],
            "note": body.reason,
            "correction_reason": "",
            "wait_reason": "",
            "geo": None,
        }
        await db.dispatch_assignments.update_one(
            {"id": assignment_id},
            {
                "$set": {
                    "cancelled_at": at_iso,
                    "cancel_reason": body.reason,
                    "updated_at": at_iso,
                    "last_transition_at": at_iso,
                },
                "$push": {"state_history": history_entry},
            },
        )
        await db.dispatch_state_events.insert_one({
            "id": _new_id(),
            "tenant_id": tenant_id,
            "assignment_id": assignment_id,
            "truck_id": assignment.get("truck_id"),
            "driver_id": assignment.get("driver_id"),
            "driver_name": assignment.get("driver_name") or "",
            "project_number": assignment.get("project_number") or "",
            "from_state": assignment.get("current_state"),
            "to_state": "CANCELLED",
            "standard": False,
            "warning_tag": "CANCELLED",
            "warning_tags": ["CANCELLED"],
            "at": at_iso,
            "by_name": by_name,
            "by_role": by_role,
            "note": body.reason,
            "correction_reason": "",
            "wait_reason": "",
            "geo": None,
        })
        out = await db.dispatch_assignments.find_one({"id": assignment_id}, {"_id": 0})
        return {"ok": True, "assignment": out}

    # ────────────────────────────────────────────────────────────────
    # REASSIGN
    # ────────────────────────────────────────────────────────────────
    @router.post("/assignments/{assignment_id}/reassign")
    async def reassign_assignment(
        assignment_id: str,
        body: ReassignRequest,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        assignment = await db.dispatch_assignments.find_one(
            {"id": assignment_id, "tenant_id": tenant_id}, {"_id": 0},
        )
        if not assignment:
            raise HTTPException(404, "Assignment not found")
        if assignment.get("cancelled_at"):
            raise HTTPException(409, "Cannot reassign a cancelled assignment")
        if assignment.get("current_state") in DLS.TERMINAL_STATES:
            raise HTTPException(
                409,
                "Cannot reassign an assignment in a terminal state",
            )
        if not (body.new_driver_id or body.new_driver_name or body.new_truck_id):
            raise HTTPException(
                422,
                "Provide at least one of: new_driver_id, new_driver_name, new_truck_id",
            )

        at_iso = _now_iso()
        by_name = _actor_label(actor)
        by_role = _actor_role(actor)

        set_fields: Dict[str, Any] = {
            "updated_at": at_iso,
            "last_transition_at": at_iso,
        }
        if body.new_driver_id is not None:
            set_fields["driver_id"] = body.new_driver_id or None
        if body.new_driver_name:
            set_fields["driver_name"] = body.new_driver_name
        if body.new_truck_id:
            set_fields["truck_id"] = body.new_truck_id

        history_entry = {
            "from_state": assignment.get("current_state"),
            "to_state": assignment.get("current_state"),
            "at": at_iso,
            "by_name": by_name,
            "by_role": by_role,
            "standard": True,
            "warning_tag": "REASSIGNED",
            "warning_tags": ["REASSIGNED"],
            "note": body.reason or "",
            "correction_reason": "",
            "wait_reason": "",
            "geo": None,
            "reassign_to_driver_id": set_fields.get("driver_id"),
            "reassign_to_driver_name": set_fields.get("driver_name"),
            "reassign_to_truck_id": set_fields.get("truck_id"),
            "reassign_from_driver_id": assignment.get("driver_id"),
            "reassign_from_driver_name": assignment.get("driver_name"),
            "reassign_from_truck_id": assignment.get("truck_id"),
        }
        await db.dispatch_assignments.update_one(
            {"id": assignment_id},
            {"$set": set_fields, "$push": {"state_history": history_entry}},
        )
        await db.dispatch_state_events.insert_one({
            "id": _new_id(),
            "tenant_id": tenant_id,
            "assignment_id": assignment_id,
            "truck_id": set_fields.get("truck_id") or assignment.get("truck_id"),
            "driver_id": set_fields.get("driver_id", assignment.get("driver_id")),
            "driver_name": set_fields.get("driver_name") or assignment.get("driver_name") or "",
            "project_number": assignment.get("project_number") or "",
            "from_state": assignment.get("current_state"),
            "to_state": assignment.get("current_state"),
            "standard": True,
            "warning_tag": "REASSIGNED",
            "warning_tags": ["REASSIGNED"],
            "at": at_iso,
            "by_name": by_name,
            "by_role": by_role,
            "note": body.reason or "",
            "correction_reason": "",
            "wait_reason": "",
            "geo": None,
        })
        out = await db.dispatch_assignments.find_one({"id": assignment_id}, {"_id": 0})
        return {"ok": True, "assignment": out}

    # ────────────────────────────────────────────────────────────────
    # STATE EVENTS (append-only stream — read)
    # ────────────────────────────────────────────────────────────────
    @router.get("/state-events")
    async def list_state_events(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        assignment_id: Optional[str] = None,
        non_standard_only: bool = False,
        limit: int = Query(_HISTORY_DEFAULT_LIMIT, ge=1, le=_HISTORY_MAX_LIMIT),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        query: Dict[str, Any] = {"tenant_id": tenant_id}
        if assignment_id:
            query["assignment_id"] = assignment_id
        if non_standard_only:
            query["standard"] = False
        cursor = (
            db.dispatch_state_events
            .find(query, {"_id": 0})
            .sort("at", -1)
            .limit(limit)
        )
        rows = await cursor.to_list(length=limit)
        return {"ok": True, "tenant_id": tenant_id, "count": len(rows), "events": rows}

    # ────────────────────────────────────────────────────────────────
    # HAUL CYCLES (derived summary — read)
    # ────────────────────────────────────────────────────────────────
    @router.get("/haul-cycles")
    async def list_haul_cycles(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        truck_id: Optional[str] = None,
        driver_id: Optional[str] = None,
        project_number: Optional[str] = None,
        limit: int = Query(100, ge=1, le=500),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        query: Dict[str, Any] = {"tenant_id": tenant_id}
        if truck_id:
            query["truck_id"] = truck_id
        if driver_id:
            query["driver_id"] = driver_id
        if project_number:
            query["project_number"] = project_number
        cursor = (
            db.haul_cycles
            .find(query, {"_id": 0})
            .sort("completed_at", -1)
            .limit(limit)
        )
        rows = await cursor.to_list(length=limit)
        return {"ok": True, "tenant_id": tenant_id, "count": len(rows), "cycles": rows}

    # ────────────────────────────────────────────────────────────────
    # META — canonical state list (consumed by future driver UI)
    # ────────────────────────────────────────────────────────────────
    @router.get("/lifecycle/states")
    async def get_canonical_states(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
    ):
        return {
            "ok": True,
            "states": DLS.CANONICAL_STATES,
            "terminal": sorted(DLS.TERMINAL_STATES),
            "operational": sorted(DLS.OPERATIONAL_STATES),
            "preferred_next": {
                s: DLS.allowed_next_states(s) for s in DLS.CANONICAL_STATES
            },
        }

    # ────────────────────────────────────────────────────────────────
    # iter409 · Phase 14.3 · PM Haul Activity (production awareness)
    # ────────────────────────────────────────────────────────────────
    @router.get("/haul-activity")
    async def haul_activity_summary(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        project_number: Optional[str] = Query(default=None),
        project_numbers: Optional[str] = Query(default=None),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        """Calm, role-agnostic production awareness.

        PM Hub renders this as a "Haul Activity" tile, scoped to the
        PM's project_numbers. The same endpoint serves any portal that
        cares — admin, dispatch, FL — so we don't fork the data path.

        Doctrine:
          * Derived only from `dispatch_assignments` + `haul_cycles`
            (no new collection).
          * Numbers, not graphs. No analytics drift.
          * "Today" = UTC calendar day boundary of `started_at`.
          * Empty project_number → tenant-wide summary (admin/dispatch).

        Query options:
          - project_number=PRJ-1
          - project_numbers=PRJ-1,PRJ-2,PRJ-3
        """
        tenant_id = _resolve_tenant(x_tenant_id)
        targets: List[str] = []
        if project_number:
            targets.append(project_number.strip())
        if project_numbers:
            targets.extend(
                [p.strip() for p in project_numbers.split(",") if p.strip()],
            )
        targets = list({p for p in targets if p})

        # Day boundary in UTC
        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_start_iso = day_start.isoformat()

        # Base match: tenant + (optional) project scope
        base_match: Dict[str, Any] = {"tenant_id": tenant_id}
        if targets:
            base_match["project_number"] = {"$in": targets}

        # ── Loads completed today (haul_cycles is canonical) ──────
        loads_completed_today = 0
        equipment_moves_completed_today = 0
        material_loads_completed_today = 0
        try:
            cycle_match = dict(base_match)
            cycle_match["completed_at"] = {"$gte": day_start_iso}
            async for c in db.haul_cycles.find(
                cycle_match,
                {"_id": 0, "haul_type": 1},
            ):
                loads_completed_today += 1
                if (c.get("haul_type") or "Material") == "Equipment Move":
                    equipment_moves_completed_today += 1
                else:
                    material_loads_completed_today += 1
        except Exception:
            pass

        # ── Active hauls + state-based signals (dispatch_assignments) ──
        active_hauls = 0
        equipment_moves_active = 0
        waiting_on_plant = 0
        waiting_on_dump = 0
        breakdown_impacts = 0
        try:
            active_match = dict(base_match)
            active_match["current_state"] = {"$nin": list(DLS.TERMINAL_STATES)}
            async for a in db.dispatch_assignments.find(
                active_match,
                {
                    "_id": 0, "current_state": 1, "current_wait_reason": 1,
                    "haul_type": 1,
                },
            ):
                active_hauls += 1
                state = a.get("current_state") or ""
                wait = (a.get("current_wait_reason") or "").upper()
                if state == DLS.BREAKDOWN:
                    breakdown_impacts += 1
                if state == DLS.WAITING:
                    if "PLANT" in wait:
                        waiting_on_plant += 1
                    elif "DUMP" in wait or "SITE" in wait:
                        waiting_on_dump += 1
                if (a.get("haul_type") or "Material") == "Equipment Move":
                    equipment_moves_active += 1
        except Exception:
            pass

        # ── Top materials today (small, calm, capped at 5) ─────────
        top_materials: List[Dict[str, Any]] = []
        try:
            pipeline = [
                {"$match": {
                    "tenant_id": tenant_id,
                    "completed_at": {"$gte": day_start_iso},
                    "material": {"$nin": [None, "", "Equipment Move"]},
                    **({"project_number": {"$in": targets}} if targets else {}),
                }},
                {"$group": {
                    "_id": "$material",
                    "count": {"$sum": 1},
                }},
                {"$sort": {"count": -1}},
                {"$limit": 5},
            ]
            async for row in db.haul_cycles.aggregate(pipeline):
                if row.get("_id"):
                    top_materials.append({
                        "label": row["_id"],
                        "loads": int(row.get("count") or 0),
                    })
        except Exception:
            pass

        return {
            "ok": True,
            "tenant_id": tenant_id,
            "scope": "project" if targets else "tenant",
            "project_numbers": targets,
            "as_of": now.isoformat(),
            "day_window_start": day_start_iso,
            "loads_completed_today": loads_completed_today,
            "material_loads_completed_today": material_loads_completed_today,
            "equipment_moves_completed_today": equipment_moves_completed_today,
            "active_hauls": active_hauls,
            "equipment_moves_active": equipment_moves_active,
            "waiting_on_plant": waiting_on_plant,
            "waiting_on_dump": waiting_on_dump,
            "breakdown_impacts": breakdown_impacts,
            "top_materials": top_materials,
        }

    return router


__all__ = [
    "build_dispatch_lifecycle_router",
    "ensure_dispatch_lifecycle_indexes",
    "DEFAULT_TENANT_ID",
]

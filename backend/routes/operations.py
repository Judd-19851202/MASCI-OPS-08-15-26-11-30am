"""
MASCI Operations Platform · Operations layer (iter124).

Single backend module that wires together the four new priorities:

  P1 — Unified Asset Profile      (read-only aggregator)
  P2 — Operations Event Log       (platform's "nervous system")
  P3 — Dispatch Portal backend    (transfers + assignments)
  P4 — Equipment Utilization      (derived status — internal data only,
                                   Motive-ready placeholder fields)

Design rules honoured:
  • db.equipment_master / db.employees are NEVER mutated by any route here.
  • Event-log writes are best-effort. A failure to write an event MUST
    NEVER abort the source workflow (caller wraps in try/except).
  • All Motive / MaintainX fields stay placeholders until the live
    integration is enabled in the Integration Center.
  • Dispatch is admin-token gated for now; a dedicated dispatch_users
    login surface will mirror safety_users.py in a follow-on iteration.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════
# Constants
# ════════════════════════════════════════════════════════════════════
TRANSFER_STATES = (
    "Draft", "Submitted", "Pending Review", "Approved", "Denied",
    "Scheduled", "In Transit", "Completed", "Cancelled",
)

ASSET_OP_STATUSES = (
    "Available", "Assigned", "Active", "Idle", "Down",
    "Maintenance Hold", "Safety Hold", "Pending Transfer",
    "In Transit", "GPS Offline", "Unknown",
)

EVENT_SEVERITIES = ("info", "low", "medium", "high", "critical")
EVENT_STATUSES = ("Open", "In Progress", "Closed", "Archived")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ════════════════════════════════════════════════════════════════════
# Pydantic models
# ════════════════════════════════════════════════════════════════════
class EventCreate(BaseModel):
    event_type: str = Field(..., min_length=1, max_length=80)
    event_category: Optional[str] = ""
    event_title: str = Field(..., min_length=1, max_length=240)
    event_description: Optional[str] = ""
    severity: Optional[str] = "info"
    status: Optional[str] = "Open"
    source_module: Optional[str] = "admin"
    source_record_id: Optional[str] = None
    source_collection: Optional[str] = None
    asset_id: Optional[str] = None
    employee_id: Optional[str] = None
    project_id: Optional[str] = None
    assigned_to: Optional[str] = None
    action_required: Optional[bool] = False
    due_date: Optional[str] = None
    visibility_flags: Optional[List[str]] = None
    linked_corrective_action_id: Optional[str] = None
    linked_dispatch_request_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EventUpdate(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    assigned_to: Optional[str] = None
    event_description: Optional[str] = None
    action_required: Optional[bool] = None
    closed_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class HoldCreate(BaseModel):
    asset_id: str = Field(..., min_length=1)
    kind: str = Field(..., description="safety | maintenance")
    reason: str = Field(..., min_length=1)
    severity: Optional[str] = "medium"
    notes: Optional[str] = ""
    linked_event_id: Optional[str] = None


class HoldRelease(BaseModel):
    resolution: Optional[str] = ""
    released_by: Optional[str] = None


class AssignmentUpsert(BaseModel):
    asset_id: str = Field(..., min_length=1)
    project_id: Optional[str] = ""
    project_number: Optional[str] = ""
    project_name: Optional[str] = ""
    operator_employee_id: Optional[str] = ""
    operator_name: Optional[str] = ""
    expected_return_date: Optional[str] = None
    dispatch_notes: Optional[str] = ""


class AssignmentClear(BaseModel):
    note: Optional[str] = ""


class TransferCreate(BaseModel):
    asset_id: str = Field(..., min_length=1)
    from_project_number: Optional[str] = ""
    to_project_number: Optional[str] = ""
    to_project_name: Optional[str] = ""
    need_date: Optional[str] = None
    return_date: Optional[str] = None
    reason: Optional[str] = ""
    priority: Optional[str] = "normal"
    requested_operator_name: Optional[str] = ""
    notes: Optional[str] = ""


class TransferDecision(BaseModel):
    decision: str = Field(..., pattern="^(approve|deny|schedule|complete|cancel)$")
    scheduled_move_date: Optional[str] = None
    decision_reason: Optional[str] = ""


# ════════════════════════════════════════════════════════════════════
# Storage init
# ════════════════════════════════════════════════════════════════════
async def ensure_operations_indexes(db) -> None:
    try:
        await asyncio.gather(
            db.operations_events.create_index("created_at"),
            db.operations_events.create_index("asset_id"),
            db.operations_events.create_index("employee_id"),
            db.operations_events.create_index("project_id"),
            db.operations_events.create_index("event_type"),
            db.operations_events.create_index("status"),
            db.operations_events.create_index("severity"),
            db.operations_events.create_index("source_module"),
            db.asset_assignments.create_index("asset_id", unique=False),
            db.asset_assignments.create_index("active"),
            db.asset_holds.create_index("asset_id"),
            db.asset_holds.create_index("kind"),
            db.asset_holds.create_index("active"),
            db.transfer_requests.create_index("asset_id"),
            db.transfer_requests.create_index("status"),
            db.transfer_requests.create_index("created_at"),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[operations-index] {e}")


# ════════════════════════════════════════════════════════════════════
# Event writer — NEVER raises. Caller wraps in try/except for clarity.
# ════════════════════════════════════════════════════════════════════
async def write_event(db, **fields) -> Optional[str]:
    """Append-only event log writer. Returns event id on success, None
    on failure. Failures are logged but never re-raised — callers must
    treat this as a fire-and-forget side effect."""
    try:
        doc = {
            "id": str(uuid.uuid4()),
            "event_type": fields.get("event_type") or "unknown",
            "event_category": fields.get("event_category") or "",
            "event_title": fields.get("event_title") or fields.get("event_type") or "Event",
            "event_description": fields.get("event_description") or "",
            "severity": fields.get("severity") or "info",
            "status": fields.get("status") or "Open",
            "source_module": fields.get("source_module") or "system",
            "source_record_id": fields.get("source_record_id"),
            "source_collection": fields.get("source_collection"),
            "asset_id": fields.get("asset_id"),
            "employee_id": fields.get("employee_id"),
            "project_id": fields.get("project_id"),
            "assigned_to": fields.get("assigned_to"),
            "created_by": fields.get("created_by") or "system",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "closed_at": fields.get("closed_at"),
            "due_date": fields.get("due_date"),
            "action_required": bool(fields.get("action_required")),
            "visibility_flags": fields.get("visibility_flags") or [],
            "linked_corrective_action_id": fields.get("linked_corrective_action_id"),
            "linked_work_order_id": fields.get("linked_work_order_id"),
            "linked_dispatch_request_id": fields.get("linked_dispatch_request_id"),
            "linked_motive_event_id": fields.get("linked_motive_event_id"),
            "linked_maintainx_work_order_id": fields.get("linked_maintainx_work_order_id"),
            "metadata": fields.get("metadata") or {},
        }
        await db.operations_events.insert_one(doc)
        return doc["id"]
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[operations-event] write failed: {e}")
        return None


async def _compute_current_status(db, asset_id: str) -> Dict[str, Any]:
    """Derive current operational status from internal data only.

    Precedence (highest to lowest):
      Safety Hold → Maintenance Hold → In Transit → Pending Transfer →
      Assigned → Available
    """
    holds = await db.asset_holds.find(
        {"asset_id": asset_id, "active": True}, {"_id": 0},
    ).to_list(20)
    safety_hold = any(h["kind"] == "safety" for h in holds)
    maint_hold = any(h["kind"] == "maintenance" for h in holds)

    pending_transfer = None
    in_transit = None
    open_xfers = await db.transfer_requests.find(
        {"asset_id": asset_id, "status": {"$in": ["Submitted", "Pending Review", "Approved", "Scheduled", "In Transit"]}},
        {"_id": 0},
    ).sort("created_at", -1).to_list(20)
    for x in open_xfers:
        if x["status"] == "In Transit":
            in_transit = x
            break
        if x["status"] in ("Submitted", "Pending Review", "Approved", "Scheduled") and not pending_transfer:
            pending_transfer = x

    assignment = await db.asset_assignments.find_one(
        {"asset_id": asset_id, "active": True}, {"_id": 0},
    )

    if safety_hold:
        status = "Safety Hold"
    elif maint_hold:
        status = "Maintenance Hold"
    elif in_transit:
        status = "In Transit"
    elif pending_transfer:
        status = "Pending Transfer"
    elif assignment:
        status = "Assigned"
    else:
        status = "Available"

    return {
        "status": status,
        "holds": holds,
        "active_assignment": assignment,
        "pending_transfer": pending_transfer,
        "in_transit": in_transit,
    }


# ════════════════════════════════════════════════════════════════════
# Router builder
# ════════════════════════════════════════════════════════════════════
def build_operations_router(db, require_admin) -> APIRouter:
    """Build the operations HTTP surface. All write routes are admin-
    gated for now. Read endpoints accept admin; the cross-portal read
    paths (asset profile etc.) are admin-only initially with a clear
    expansion point for dispatch/shop/safety/HR tokens later."""

    router = APIRouter(prefix="/api/operations", tags=["operations"])

    # ── Operations Event Log ────────────────────────────────────────
    @router.post("/events", dependencies=[Depends(require_admin)])
    async def create_event(body: EventCreate):
        eid = await write_event(db, **body.model_dump(), created_by="admin")
        if not eid:
            raise HTTPException(500, "Event write failed")
        doc = await db.operations_events.find_one({"id": eid}, {"_id": 0})
        return doc

    @router.get("/events", dependencies=[Depends(require_admin)])
    async def list_events(
        asset_id: Optional[str] = None,
        employee_id: Optional[str] = None,
        project_id: Optional[str] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        source_module: Optional[str] = None,
        action_required: Optional[bool] = None,
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0, le=10000),
    ):
        q: dict = {}
        for k, v in (
            ("asset_id", asset_id), ("employee_id", employee_id), ("project_id", project_id),
            ("event_type", event_type), ("severity", severity), ("status", status),
            ("source_module", source_module),
        ):
            if v:
                q[k] = v
        if action_required is not None:
            q["action_required"] = bool(action_required)
        total = await db.operations_events.count_documents(q)
        rows = await db.operations_events.find(q, {"_id": 0}).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
        return {"total": total, "limit": limit, "offset": offset, "rows": rows}

    @router.get("/events/{event_id}", dependencies=[Depends(require_admin)])
    async def get_event(event_id: str):
        doc = await db.operations_events.find_one({"id": event_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Event not found")
        return doc

    @router.patch("/events/{event_id}", dependencies=[Depends(require_admin)])
    async def update_event(event_id: str, body: EventUpdate):
        existing = await db.operations_events.find_one({"id": event_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Event not found")
        patch = {k: v for k, v in body.model_dump().items() if v is not None}
        if body.status == "Closed" and not body.closed_at:
            patch["closed_at"] = _now_iso()
        patch["updated_at"] = _now_iso()
        await db.operations_events.update_one({"id": event_id}, {"$set": patch})
        return await db.operations_events.find_one({"id": event_id}, {"_id": 0})

    # ── Holds ────────────────────────────────────────────────────────
    @router.post("/holds", dependencies=[Depends(require_admin)])
    async def create_hold(body: HoldCreate):
        if body.kind not in ("safety", "maintenance"):
            raise HTTPException(400, "kind must be 'safety' or 'maintenance'")
        eq = await db.equipment_master.find_one({"id": body.asset_id}, {"_id": 0, "id": 1, "unit_number": 1})
        if not eq:
            raise HTTPException(404, "asset not found in equipment_master")
        doc = {
            "id": str(uuid.uuid4()),
            "asset_id": body.asset_id,
            "kind": body.kind,
            "reason": body.reason,
            "severity": body.severity or "medium",
            "notes": body.notes or "",
            "active": True,
            "created_at": _now_iso(),
            "created_by": "admin",
            "released_at": None,
            "released_by": None,
            "resolution": "",
            "linked_event_id": body.linked_event_id,
        }
        await db.asset_holds.insert_one(doc)
        await write_event(
            db,
            event_type=f"{body.kind}_hold_applied",
            event_category=body.kind,
            event_title=f"{body.kind.title()} hold applied: {body.reason}",
            event_description=body.notes or "",
            severity=body.severity or "medium",
            source_module="dispatch",
            source_collection="asset_holds",
            source_record_id=doc["id"],
            asset_id=body.asset_id,
            action_required=True,
            created_by="admin",
        )
        doc.pop("_id", None)
        return doc

    @router.post("/holds/{hold_id}/release", dependencies=[Depends(require_admin)])
    async def release_hold(hold_id: str, body: HoldRelease):
        existing = await db.asset_holds.find_one({"id": hold_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Hold not found")
        if not existing.get("active"):
            return existing
        await db.asset_holds.update_one(
            {"id": hold_id},
            {"$set": {
                "active": False,
                "released_at": _now_iso(),
                "released_by": body.released_by or "admin",
                "resolution": body.resolution or "",
            }},
        )
        await write_event(
            db,
            event_type=f"{existing['kind']}_hold_released",
            event_category=existing["kind"],
            event_title=f"{existing['kind'].title()} hold released",
            event_description=body.resolution or "",
            severity="info",
            source_module="dispatch",
            source_collection="asset_holds",
            source_record_id=hold_id,
            asset_id=existing["asset_id"],
            created_by="admin",
        )
        return await db.asset_holds.find_one({"id": hold_id}, {"_id": 0})

    @router.get("/holds", dependencies=[Depends(require_admin)])
    async def list_holds(
        active_only: bool = True,
        kind: Optional[str] = None,
        asset_id: Optional[str] = None,
        limit: int = Query(200, ge=1, le=1000),
    ):
        q: dict = {}
        if active_only:
            q["active"] = True
        if kind:
            q["kind"] = kind
        if asset_id:
            q["asset_id"] = asset_id
        rows = await db.asset_holds.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)
        return rows

    # ── Asset Assignments ────────────────────────────────────────────
    @router.post("/assignments", dependencies=[Depends(require_admin)])
    async def upsert_assignment(body: AssignmentUpsert):
        eq = await db.equipment_master.find_one({"id": body.asset_id}, {"_id": 0, "id": 1, "unit_number": 1, "name": 1})
        if not eq:
            raise HTTPException(404, "asset not found in equipment_master")
        # close any active assignment first
        await db.asset_assignments.update_many(
            {"asset_id": body.asset_id, "active": True},
            {"$set": {"active": False, "ended_at": _now_iso(), "ended_by": "admin"}},
        )
        doc = {
            "id": str(uuid.uuid4()),
            "asset_id": body.asset_id,
            "masci_unit_number": eq.get("unit_number") or "",
            "project_id": body.project_id or "",
            "project_number": body.project_number or "",
            "project_name": body.project_name or "",
            "operator_employee_id": body.operator_employee_id or "",
            "operator_name": body.operator_name or "",
            "expected_return_date": body.expected_return_date,
            "dispatch_notes": body.dispatch_notes or "",
            "active": True,
            "started_at": _now_iso(),
            "started_by": "admin",
            "ended_at": None,
            "ended_by": None,
        }
        await db.asset_assignments.insert_one(doc)
        await write_event(
            db,
            event_type="asset_assigned",
            event_category="dispatch",
            event_title=f"Asset assigned to {body.project_number or body.project_name or 'project'}",
            severity="info",
            source_module="dispatch",
            source_collection="asset_assignments",
            source_record_id=doc["id"],
            asset_id=body.asset_id,
            project_id=body.project_id,
            employee_id=body.operator_employee_id,
            created_by="admin",
        )
        doc.pop("_id", None)
        return doc

    @router.post("/assignments/{asset_id}/clear", dependencies=[Depends(require_admin)])
    async def clear_assignment(asset_id: str, body: AssignmentClear):
        res = await db.asset_assignments.update_many(
            {"asset_id": asset_id, "active": True},
            {"$set": {"active": False, "ended_at": _now_iso(), "ended_by": "admin", "ended_note": body.note or ""}},
        )
        if res.modified_count == 0:
            return {"ok": True, "cleared": 0}
        await write_event(
            db,
            event_type="asset_unassigned",
            event_category="dispatch",
            event_title="Asset assignment cleared",
            severity="info",
            source_module="dispatch",
            source_collection="asset_assignments",
            asset_id=asset_id,
            created_by="admin",
        )
        return {"ok": True, "cleared": res.modified_count}

    # ── Transfer Requests ────────────────────────────────────────────
    @router.post("/transfers", dependencies=[Depends(require_admin)])
    async def create_transfer(body: TransferCreate):
        eq = await db.equipment_master.find_one({"id": body.asset_id}, {"_id": 0, "id": 1, "unit_number": 1})
        if not eq:
            raise HTTPException(404, "asset not found in equipment_master")
        doc = {
            "id": str(uuid.uuid4()),
            "asset_id": body.asset_id,
            "masci_unit_number": eq.get("unit_number") or "",
            "from_project_number": body.from_project_number or "",
            "to_project_number": body.to_project_number or "",
            "to_project_name": body.to_project_name or "",
            "need_date": body.need_date,
            "return_date": body.return_date,
            "reason": body.reason or "",
            "priority": body.priority or "normal",
            "requested_operator_name": body.requested_operator_name or "",
            "notes": body.notes or "",
            "status": "Submitted",
            "created_at": _now_iso(),
            "created_by": "admin",
            "updated_at": _now_iso(),
            "approved_at": None,
            "approved_by": None,
            "denied_at": None,
            "denied_reason": "",
            "scheduled_move_date": None,
            "completed_at": None,
            "history": [{"at": _now_iso(), "by": "admin", "status": "Submitted"}],
        }
        await db.transfer_requests.insert_one(doc)
        await write_event(
            db,
            event_type="dispatch_request_created",
            event_category="dispatch",
            event_title=f"Transfer requested → {body.to_project_number or body.to_project_name or '—'}",
            severity="info",
            source_module="dispatch",
            source_collection="transfer_requests",
            source_record_id=doc["id"],
            asset_id=body.asset_id,
            linked_dispatch_request_id=doc["id"],
            action_required=True,
            created_by="admin",
        )
        doc.pop("_id", None)
        return doc

    @router.post("/transfers/{xid}/decide", dependencies=[Depends(require_admin)])
    async def decide_transfer(xid: str, body: TransferDecision):
        existing = await db.transfer_requests.find_one({"id": xid}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Transfer not found")
        if existing["status"] in ("Completed", "Cancelled"):
            raise HTTPException(409, f"Cannot {body.decision} a {existing['status']} transfer")

        new_status = existing["status"]
        patch: Dict[str, Any] = {"updated_at": _now_iso()}
        event_type = "dispatch_request_updated"
        title = "Transfer updated"

        if body.decision == "approve":
            new_status = "Approved"
            patch["approved_at"] = _now_iso()
            patch["approved_by"] = "admin"
            event_type = "dispatch_request_approved"
            title = "Transfer approved"
        elif body.decision == "deny":
            new_status = "Denied"
            patch["denied_at"] = _now_iso()
            patch["denied_reason"] = body.decision_reason or ""
            event_type = "dispatch_request_denied"
            title = "Transfer denied"
        elif body.decision == "schedule":
            if existing["status"] != "Approved":
                raise HTTPException(409, "Only Approved transfers can be Scheduled")
            new_status = "Scheduled"
            patch["scheduled_move_date"] = body.scheduled_move_date
            event_type = "dispatch_transfer_scheduled"
            title = "Transfer scheduled"
        elif body.decision == "complete":
            if existing["status"] not in ("Scheduled", "Approved", "In Transit"):
                raise HTTPException(409, "Transfer cannot be completed from current state")
            new_status = "Completed"
            patch["completed_at"] = _now_iso()
            event_type = "dispatch_transfer_completed"
            title = "Transfer completed"
        elif body.decision == "cancel":
            new_status = "Cancelled"
            event_type = "dispatch_request_cancelled"
            title = "Transfer cancelled"

        patch["status"] = new_status
        await db.transfer_requests.update_one(
            {"id": xid},
            {"$set": patch, "$push": {"history": {"at": _now_iso(), "by": "admin", "status": new_status, "note": body.decision_reason or ""}}},
        )
        await write_event(
            db,
            event_type=event_type,
            event_category="dispatch",
            event_title=title,
            event_description=body.decision_reason or "",
            severity="info",
            source_module="dispatch",
            source_collection="transfer_requests",
            source_record_id=xid,
            asset_id=existing["asset_id"],
            linked_dispatch_request_id=xid,
            created_by="admin",
        )

        # On Completed → close any active assignment and re-assign to the
        # destination project (lightweight; admin can edit afterwards).
        if new_status == "Completed":
            await db.asset_assignments.update_many(
                {"asset_id": existing["asset_id"], "active": True},
                {"$set": {"active": False, "ended_at": _now_iso(), "ended_by": "admin",
                          "ended_note": f"transfer:{xid}"}},
            )
            new_assignment = {
                "id": str(uuid.uuid4()),
                "asset_id": existing["asset_id"],
                "masci_unit_number": existing.get("masci_unit_number") or "",
                "project_id": "",
                "project_number": existing.get("to_project_number") or "",
                "project_name": existing.get("to_project_name") or "",
                "operator_employee_id": "",
                "operator_name": existing.get("requested_operator_name") or "",
                "expected_return_date": existing.get("return_date"),
                "dispatch_notes": f"Auto from transfer {xid}",
                "active": True,
                "started_at": _now_iso(),
                "started_by": "admin",
                "ended_at": None, "ended_by": None,
                "linked_transfer_id": xid,
            }
            await db.asset_assignments.insert_one(new_assignment)
            await write_event(
                db,
                event_type="asset_assigned",
                event_category="dispatch",
                event_title=f"Asset assigned to {new_assignment['project_number'] or new_assignment['project_name'] or '—'} (via transfer)",
                severity="info",
                source_module="dispatch",
                source_collection="asset_assignments",
                source_record_id=new_assignment["id"],
                asset_id=existing["asset_id"],
                linked_dispatch_request_id=xid,
                created_by="admin",
            )

        return await db.transfer_requests.find_one({"id": xid}, {"_id": 0})

    @router.get("/transfers", dependencies=[Depends(require_admin)])
    async def list_transfers(
        status: Optional[str] = None,
        asset_id: Optional[str] = None,
        limit: int = Query(200, ge=1, le=1000),
    ):
        q: dict = {}
        if status:
            q["status"] = status
        if asset_id:
            q["asset_id"] = asset_id
        rows = await db.transfer_requests.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)
        return rows

    # ── Utilization ──────────────────────────────────────────────────
    @router.get("/utilization", dependencies=[Depends(require_admin)])
    async def utilization_overview():
        """Lightweight roll-up using internal records only. Motive-
        powered idle/underutilized values stay as placeholder counts
        until the live integration lands."""
        # Fast bulk fetch of equipment + active assignments + active holds
        equipment = await db.equipment_master.find(
            {}, {"_id": 0, "id": 1, "unit_number": 1, "name": 1, "equipment_type": 1, "make": 1, "model": 1},
        ).to_list(20000)
        assignments = await db.asset_assignments.find({"active": True}, {"_id": 0}).to_list(20000)
        holds = await db.asset_holds.find({"active": True}, {"_id": 0}).to_list(20000)
        open_xfers = await db.transfer_requests.find(
            {"status": {"$in": ["Submitted", "Pending Review", "Approved", "Scheduled", "In Transit"]}},
            {"_id": 0},
        ).to_list(20000)

        assn_by_asset = {a["asset_id"]: a for a in assignments}
        safety_set = {h["asset_id"] for h in holds if h["kind"] == "safety"}
        maint_set = {h["asset_id"] for h in holds if h["kind"] == "maintenance"}
        pending_set = {x["asset_id"] for x in open_xfers if x["status"] != "In Transit"}
        in_transit_set = {x["asset_id"] for x in open_xfers if x["status"] == "In Transit"}

        buckets = {s: 0 for s in ASSET_OP_STATUSES}
        rows = []
        for e in equipment:
            aid = e["id"]
            if aid in safety_set:
                st = "Safety Hold"
            elif aid in maint_set:
                st = "Maintenance Hold"
            elif aid in in_transit_set:
                st = "In Transit"
            elif aid in pending_set:
                st = "Pending Transfer"
            elif aid in assn_by_asset:
                st = "Assigned"
            else:
                st = "Available"
            buckets[st] += 1
            rows.append({
                "asset_id": aid,
                "unit_number": e.get("unit_number") or "",
                "equipment_name": e.get("name") or "",
                "equipment_type": e.get("equipment_type") or "",
                "make": e.get("make") or "",
                "model": e.get("model") or "",
                "status": st,
                "assigned_project_number": (assn_by_asset.get(aid) or {}).get("project_number") or "",
                "assigned_operator_name": (assn_by_asset.get(aid) or {}).get("operator_name") or "",
            })
        return {"totals": buckets, "fleet_size": len(equipment), "rows": rows}

    # ── Unified Asset Profile (read-only aggregator) ─────────────────
    @router.get("/assets/{asset_id}/profile", dependencies=[Depends(require_admin)])
    async def asset_profile(asset_id: str, events_limit: int = Query(25, ge=1, le=200)):
        eq = await db.equipment_master.find_one({"id": asset_id}, {"_id": 0})
        if not eq:
            raise HTTPException(404, "asset not found")

        status_block = await _compute_current_status(db, asset_id)

        # Mapping (Motive + MaintainX placeholders sourced from
        # asset_mappings — never the master record)
        mapping = await db.asset_mappings.find_one({"masci_equipment_id": asset_id}, {"_id": 0})

        # Field operations — recent preops, daily-report references,
        # equipment checkout/returns (best-effort: these collections may
        # or may not exist in older deployments — guard with try/except).
        recent_preops = []
        try:
            recent_preops = await db.equipment_inspections.find(
                {"$or": [{"equipment_id": asset_id}, {"unit_id": asset_id}]}, {"_id": 0},
            ).sort("created_at", -1).to_list(10)
        except Exception:
            pass

        # Safety — corrective actions tied to asset (best-effort match
        # on asset_id field; older records may have no link)
        safety_cas = []
        try:
            safety_cas = await db.corrective_actions.find(
                {"asset_id": asset_id}, {"_id": 0},
            ).sort("created_at", -1).to_list(10)
        except Exception:
            pass

        # Event history (paginated single call here — UI loads more on demand)
        events = await db.operations_events.find(
            {"asset_id": asset_id}, {"_id": 0},
        ).sort("created_at", -1).to_list(events_limit)

        # Transfer history
        transfers = await db.transfer_requests.find(
            {"asset_id": asset_id}, {"_id": 0},
        ).sort("created_at", -1).to_list(25)

        return {
            "asset_id": asset_id,
            "overview": eq,
            "current_status": status_block["status"],
            "active_assignment": status_block["active_assignment"],
            "active_holds": status_block["holds"],
            "pending_transfer": status_block["pending_transfer"],
            "in_transit": status_block["in_transit"],
            "mapping": mapping,
            "recent_preops": recent_preops,
            "safety_corrective_actions": safety_cas,
            "transfers": transfers,
            "events": events,
            "events_total_for_asset": await db.operations_events.count_documents({"asset_id": asset_id}),
        }

    return router


__all__ = [
    "build_operations_router",
    "ensure_operations_indexes",
    "write_event",
    "TRANSFER_STATES",
    "ASSET_OP_STATUSES",
    "EVENT_SEVERITIES",
    "EVENT_STATUSES",
]

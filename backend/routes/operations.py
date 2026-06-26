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

from fastapi import APIRouter, Depends, Header, HTTPException, Query
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
# P1-D / P1-C · Motive visibility helpers (read-only, reuse-first)
# ════════════════════════════════════════════════════════════════════
def _stale_for(iso: Optional[str]) -> Dict[str, Any]:
    """Return staleness banding for a Motive `located_at` timestamp.
    Buckets: fresh (<30 min) · stale (30 min-24 h) · offline (>24 h)."""
    if not iso:
        return {"bucket": "offline", "minutes": None}
    try:
        from datetime import datetime as _dt, timezone as _tz  # noqa: PLC0415
        ts = _dt.fromisoformat(iso.replace("Z", "+00:00"))
        delta = _dt.now(_tz.utc) - ts
        mins = int(delta.total_seconds() / 60)
        bucket = "fresh" if mins < 30 else ("stale" if mins < 60 * 24 else "offline")
        return {"bucket": bucket, "minutes": mins}
    except Exception:  # noqa: BLE001
        return {"bucket": "offline", "minutes": None}


async def _build_motive_live_block(db, mapping: Optional[dict]) -> Dict[str, Any]:
    """Live Motive telemetry payload for the AssetProfile UI. Reads
    only `asset_mappings.motive.*` — no external API calls. Returns a
    consistent shape even when the asset has no Motive mapping yet so
    the React side can render `awaiting`/`live`/`offline` states from
    one source."""
    if not mapping or not (mapping.get("motive") or {}).get("vehicle_id") and not (mapping.get("motive") or {}).get("asset_id"):
        return {"status": "not_mapped"}
    mv = mapping.get("motive") or {}
    located = mv.get("located_at")
    staleness = _stale_for(located)
    has_gps = bool(mv.get("lat") and mv.get("lon"))
    speed_kph = mv.get("speed_kph")
    return {
        "status": "live" if has_gps and staleness["bucket"] != "offline" else "offline",
        "external_kind": "vehicle" if mv.get("vehicle_id") else "asset",
        "vehicle_id": mv.get("vehicle_id") or None,
        "asset_id": mv.get("asset_id") or None,
        "fleet_number": mv.get("number") or mv.get("name") or "",
        "vin": mv.get("vin") or "",
        "make": mv.get("make") or "",
        "model": mv.get("model") or "",
        "year": mv.get("year") or "",
        "lat": mv.get("lat"),
        "lon": mv.get("lon"),
        "located_at": located,
        "city": mv.get("city") or "",
        "state": mv.get("state") or "",
        "speed_kph": speed_kph,
        "speed_mph": round(speed_kph * 0.621371, 1) if isinstance(speed_kph, (int, float)) else None,
        "moving": isinstance(speed_kph, (int, float)) and speed_kph > 5,
        "gps_enabled": bool(mv.get("gps_enabled")),
        "dashcam_enabled": bool(mv.get("dashcam_enabled")),
        "staleness": staleness,
    }


async def _resolve_current_operator(db, *, asset_id: str,
                                    motive_vehicle_id: Optional[str],
                                    active_assignment: Optional[dict]) -> Dict[str, Any]:
    """Source-attributed current-driver hierarchy (P1-C). Walks four
    sources in priority order and returns the first hit with its
    provenance label so the UI can show *who* says this driver is in
    this asset. No new collections — everything below already exists.

    Priority:
      1. Motive driver currently in this vehicle (`employee_mappings.motive.current_vehicle_id`)
      2. Active asset_assignments.operator_name (Dispatch)
      3. Today's most-recent equipment_inspection (DVIR/preop)
      4. Most-recent equipment_inspection of any age
    """
    # 1 — Motive's "currently driving" link
    if motive_vehicle_id:
        em = await db.employee_mappings.find_one(
            {"provider": "motive", "motive.current_vehicle_id": str(motive_vehicle_id)},
            {"_id": 0, "masci_employee_id": 1, "masci_employee_name": 1,
             "motive.first_name": 1, "motive.last_name": 1,
             "motive.email": 1, "motive.located_at": 1},
        )
        if em:
            name = em.get("masci_employee_name") or " ".join(filter(None, [
                (em.get("motive") or {}).get("first_name"),
                (em.get("motive") or {}).get("last_name"),
            ])).strip()
            if name:
                return {
                    "name": name,
                    "source": "motive",
                    "source_label": "Motive (currently in vehicle)",
                    "as_of": (em.get("motive") or {}).get("located_at"),
                    "masci_employee_id": em.get("masci_employee_id") or "",
                }

    # 2 — Dispatch active assignment
    if active_assignment and active_assignment.get("operator_name"):
        return {
            "name": active_assignment.get("operator_name"),
            "source": "dispatch_assignment",
            "source_label": "Dispatch (active assignment)",
            "as_of": active_assignment.get("assigned_at"),
            "masci_employee_id": active_assignment.get("operator_id") or "",
        }

    # 3/4 — Equipment inspection trail
    try:
        from datetime import datetime as _dt, timezone as _tz, timedelta as _td  # noqa: PLC0415
        since_today = (_dt.now(_tz.utc) - _td(hours=24)).isoformat()
        recent = await db.equipment_inspections.find_one(
            {"$or": [{"equipment_id": asset_id}, {"unit_id": asset_id}],
             "created_at": {"$gte": since_today}},
            {"_id": 0, "operator_name": 1, "submitted_by": 1, "created_at": 1},
            sort=[("created_at", -1)],
        )
        if recent:
            nm = recent.get("operator_name") or recent.get("submitted_by") or ""
            if nm:
                return {"name": nm, "source": "dvir_today",
                        "source_label": "Today's Pre-Op / DVIR",
                        "as_of": recent.get("created_at"), "masci_employee_id": ""}
        any_recent = await db.equipment_inspections.find_one(
            {"$or": [{"equipment_id": asset_id}, {"unit_id": asset_id}]},
            {"_id": 0, "operator_name": 1, "submitted_by": 1, "created_at": 1},
            sort=[("created_at", -1)],
        )
        if any_recent:
            nm = any_recent.get("operator_name") or any_recent.get("submitted_by") or ""
            if nm:
                return {"name": nm, "source": "dvir_recent",
                        "source_label": "Most-recent Pre-Op / DVIR",
                        "as_of": any_recent.get("created_at"), "masci_employee_id": ""}
    except Exception:  # noqa: BLE001
        pass

    return {"name": "", "source": "none", "source_label": "", "as_of": None,
            "masci_employee_id": ""}



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


class HoldDismiss(BaseModel):
    reason: str = Field(..., min_length=2, description="Required — why the pending hold is being dismissed")
    dismissed_by: Optional[str] = None


class HoldApprove(BaseModel):
    note: Optional[str] = ""
    approved_by: Optional[str] = None


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
        {"asset_id": asset_id, "$or": [{"active": True}, {"status": "pending"}]}, {"_id": 0},
    ).to_list(50)
    safety_hold = any(h["kind"] == "safety" and h.get("active") for h in holds)
    maint_hold = any(h["kind"] == "maintenance" and h.get("active") for h in holds)

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
async def create_pending_maintenance_hold(
    db,
    *,
    asset_id: str,
    reason: str,
    severity: str = "medium",
    notes: str = "",
    source_module: str = "field",
    source_record_id: Optional[str] = None,
    linked_event_id: Optional[str] = None,
    created_by: str = "system",
) -> Optional[str]:
    """Fire-and-forget helper to spawn a pending maintenance hold from
    other modules (e.g. failed pre-op submission). Returns the new hold
    id on success, ``None`` on failure or skip.

    Skip conditions (idempotency):
      • asset_id does not match equipment_master
      • a pending OR active maintenance hold already exists for the asset
    """
    try:
        eq = await db.equipment_master.find_one({"id": asset_id}, {"_id": 0, "id": 1})
        if not eq:
            return None
        existing = await db.asset_holds.find_one(
            {"asset_id": asset_id, "kind": "maintenance",
             "$or": [{"active": True}, {"status": "pending"}]},
            {"_id": 0, "id": 1},
        )
        if existing:
            return None
        hold_id = str(uuid.uuid4())
        doc = {
            "id": hold_id,
            "asset_id": asset_id,
            "kind": "maintenance",
            "reason": reason or "Failed pre-op inspection",
            "severity": severity,
            "notes": notes,
            "active": False,
            "status": "pending",
            "created_at": _now_iso(),
            "created_by": created_by,
            "approved_at": None,
            "approved_by": None,
            "released_at": None,
            "released_by": None,
            "resolution": "",
            "dismissed_at": None,
            "dismissed_by": None,
            "dismissal_reason": "",
            "linked_event_id": linked_event_id,
            "source_module": source_module,
            "source_record_id": source_record_id,
        }
        await db.asset_holds.insert_one(doc)
        await write_event(
            db,
            event_type="maintenance_hold_requested",
            event_category="maintenance",
            event_title=f"Pending maintenance hold requested: {reason or 'failed pre-op'}",
            event_description=notes or "",
            severity=severity,
            source_module=source_module,
            source_collection="asset_holds",
            source_record_id=hold_id,
            asset_id=asset_id,
            action_required=True,
            created_by=created_by,
        )
        return hold_id
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[ops] create_pending_maintenance_hold failed: {e}")
        return None


def build_operations_router(db, require_admin, is_valid_admin_token=None) -> APIRouter:
    """Build the operations HTTP surface.

    READ endpoints accept any portal token (admin · safety · hr · shop ·
    pm · dispatch) so every authorized user can see holds, events, and
    utilization from their own portal without admin escalation.
    WRITE endpoints stay admin- or dispatch-gated.
    """
    router = APIRouter(prefix="/api/operations", tags=["operations"])

    # Cross-portal read gate. Falls back to admin-only if the caller did
    # not pass a working is_valid_admin_token resolver (back-compat).
    if is_valid_admin_token is not None:
        from routes.integrations._deps import make_require_any_portal_token  # noqa: PLC0415
        from dispatch_users import is_valid_dispatch_user_token_async  # noqa: PLC0415

        require_any_portal = make_require_any_portal_token(db, is_valid_admin_token)

        async def _require_admin_or_dispatch(
            x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
            x_dispatch_token: Optional[str] = Header(default=None, alias="X-Dispatch-Token"),
        ) -> dict:
            if x_admin_token and is_valid_admin_token(x_admin_token):
                return {"_actor": "admin", "name": "Admin"}
            if x_dispatch_token and "." in x_dispatch_token:
                u = await is_valid_dispatch_user_token_async(db, x_dispatch_token)
                if u:
                    return {**u, "_actor": "dispatch"}
            raise HTTPException(401, "Admin or Dispatch authentication required")

        require_write = _require_admin_or_dispatch
    else:
        # Back-compat — admin-only everywhere
        require_any_portal = require_admin
        require_write = require_admin

    # ── Operations Event Log ────────────────────────────────────────
    @router.post("/events", dependencies=[Depends(require_write)])
    async def create_event(body: EventCreate):
        eid = await write_event(db, **body.model_dump(), created_by="admin")
        if not eid:
            raise HTTPException(500, "Event write failed")
        doc = await db.operations_events.find_one({"id": eid}, {"_id": 0})
        return doc

    @router.get("/events", dependencies=[Depends(require_any_portal)])
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

    @router.get("/events/{event_id}", dependencies=[Depends(require_any_portal)])
    async def get_event(event_id: str):
        doc = await db.operations_events.find_one({"id": event_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Event not found")
        return doc

    @router.patch("/events/{event_id}", dependencies=[Depends(require_write)])
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
    @router.post("/holds", dependencies=[Depends(require_write)])
    async def create_hold(body: HoldCreate, pending: bool = False, source_module: str = "dispatch"):
        """Create a hold. By default `pending=False` → hold is active
        immediately (admin/dispatch decision). When `pending=True`, the
        hold is recorded but does NOT block utilization status — it's a
        request awaiting admin/dispatch approval. This is the entry
        point used by the Failed Pre-Op → Pending Maintenance Hold
        workflow."""
        if body.kind not in ("safety", "maintenance"):
            raise HTTPException(400, "kind must be 'safety' or 'maintenance'")
        eq = await db.equipment_master.find_one({"id": body.asset_id}, {"_id": 0, "id": 1, "unit_number": 1})
        if not eq:
            raise HTTPException(404, "asset not found in equipment_master")
        status = "pending" if pending else "active"
        doc = {
            "id": str(uuid.uuid4()),
            "asset_id": body.asset_id,
            "kind": body.kind,
            "reason": body.reason,
            "severity": body.severity or "medium",
            "notes": body.notes or "",
            "active": not pending,           # pending holds DO NOT block
            "status": status,                # "pending" | "active" | "released" | "dismissed"
            "created_at": _now_iso(),
            "created_by": "admin",
            "approved_at": _now_iso() if not pending else None,
            "approved_by": "admin" if not pending else None,
            "released_at": None,
            "released_by": None,
            "resolution": "",
            "dismissed_at": None,
            "dismissed_by": None,
            "dismissal_reason": "",
            "linked_event_id": body.linked_event_id,
            "source_module": source_module,
        }
        await db.asset_holds.insert_one(doc)
        await write_event(
            db,
            event_type=f"{body.kind}_hold_{'requested' if pending else 'applied'}",
            event_category=body.kind,
            event_title=(f"{body.kind.title()} hold "
                         f"{'requested — awaiting approval' if pending else 'applied'}: {body.reason}"),
            event_description=body.notes or "",
            severity=body.severity or "medium",
            source_module=source_module,
            source_collection="asset_holds",
            source_record_id=doc["id"],
            asset_id=body.asset_id,
            action_required=pending,
            created_by="admin",
        )
        doc.pop("_id", None)
        return doc

    @router.post("/holds/{hold_id}/approve", dependencies=[Depends(require_write)])
    async def approve_hold(hold_id: str, body: HoldApprove):
        existing = await db.asset_holds.find_one({"id": hold_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Hold not found")
        if existing.get("status") not in ("pending", None):
            raise HTTPException(409, f"Cannot approve a hold in status {existing.get('status')}")
        await db.asset_holds.update_one(
            {"id": hold_id},
            {"$set": {
                "active": True,
                "status": "active",
                "approved_at": _now_iso(),
                "approved_by": body.approved_by or "admin",
                "approval_note": body.note or "",
            }},
        )
        await write_event(
            db,
            event_type=f"{existing['kind']}_hold_applied",
            event_category=existing["kind"],
            event_title=f"{existing['kind'].title()} hold approved & applied",
            event_description=body.note or existing.get("reason", ""),
            severity=existing.get("severity") or "medium",
            source_module="dispatch",
            source_collection="asset_holds",
            source_record_id=hold_id,
            asset_id=existing["asset_id"],
            created_by="admin",
        )
        return await db.asset_holds.find_one({"id": hold_id}, {"_id": 0})

    @router.post("/holds/{hold_id}/dismiss", dependencies=[Depends(require_write)])
    async def dismiss_hold(hold_id: str, body: HoldDismiss):
        """Dismiss a pending hold — requires a reason. Does NOT affect
        already-active holds (must use /release for those)."""
        existing = await db.asset_holds.find_one({"id": hold_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Hold not found")
        if existing.get("status") != "pending":
            raise HTTPException(409, "Only pending holds can be dismissed; use /release for active holds")
        if not (body.reason or "").strip():
            raise HTTPException(400, "dismissal reason is required")
        await db.asset_holds.update_one(
            {"id": hold_id},
            {"$set": {
                "active": False,
                "status": "dismissed",
                "dismissed_at": _now_iso(),
                "dismissed_by": body.dismissed_by or "admin",
                "dismissal_reason": body.reason,
            }},
        )
        await write_event(
            db,
            event_type=f"{existing['kind']}_hold_dismissed",
            event_category=existing["kind"],
            event_title=f"Pending {existing['kind']} hold dismissed",
            event_description=body.reason,
            severity="info",
            source_module="dispatch",
            source_collection="asset_holds",
            source_record_id=hold_id,
            asset_id=existing["asset_id"],
            created_by="admin",
        )
        return await db.asset_holds.find_one({"id": hold_id}, {"_id": 0})

    @router.post("/holds/{hold_id}/release", dependencies=[Depends(require_write)])
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

    @router.get("/holds", dependencies=[Depends(require_any_portal)])
    async def list_holds(
        active_only: bool = False,
        status: Optional[str] = None,
        kind: Optional[str] = None,
        asset_id: Optional[str] = None,
        limit: int = Query(200, ge=1, le=1000),
    ):
        q: dict = {}
        if status:
            q["status"] = status
        elif active_only:
            q["active"] = True
        if kind:
            q["kind"] = kind
        if asset_id:
            q["asset_id"] = asset_id
        rows = await db.asset_holds.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)
        # Back-compat: rows created BEFORE iter128 don't have a `status`
        # field. Default them to "active" if their `active` flag is True
        # and "released" otherwise.
        for r in rows:
            if not r.get("status"):
                r["status"] = "active" if r.get("active") else "released"
        return rows

    # ── Asset Assignments ────────────────────────────────────────────
    @router.post("/assignments", dependencies=[Depends(require_write)])
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

    @router.post("/assignments/{asset_id}/clear", dependencies=[Depends(require_write)])
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
    @router.post("/transfers", dependencies=[Depends(require_write)])
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

    @router.post("/transfers/{xid}/decide", dependencies=[Depends(require_write)])
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

    @router.get("/transfers", dependencies=[Depends(require_any_portal)])
    async def list_transfers(
        status: Optional[str] = None,
        asset_id: Optional[str] = None,
        audience: Optional[str] = Query(
            default=None,
            description=(
                "Optional audience filter. `operator` strips audit / test / "
                "demo / validation / smoke / sample residue using the "
                "canonical `backend/lib/transfer_visibility.py` rules — "
                "see Track 15.83B. Omit (or pass anything else) to receive "
                "the unfiltered flat list (existing default contract)."
            ),
        ),
        limit: int = Query(200, ge=1, le=1000),
    ):
        q: dict = {}
        if status:
            q["status"] = status
        if asset_id:
            q["asset_id"] = asset_id
        rows = await db.transfer_requests.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)

        # TRACK 15.83B — canonical operator audience filter. Backend now
        # owns the AUDIT/TEST/DEMO/VALIDATION/SMOKE/SAMPLE residue
        # suppression so the Dispatch landing surface and any future
        # native client share the same trust rules. Default behavior
        # (no audience query) returns the legacy flat-list contract
        # unchanged.
        if (audience or "").strip().lower() == "operator":
            from lib.transfer_visibility import (
                filter_operator_visible_transfers,
            )  # noqa: PLC0415
            visible, suppressed = filter_operator_visible_transfers(rows)
            return {
                "items": list(visible),
                "total": len(visible),
                "audience": "operator",
                "suppressed_count": suppressed,
            }

        return rows

    # ── Integration readiness (iter132) ──────────────────────────────
    # Cross-portal read; never mutates equipment_master. Renders inside
    # the Dispatch Portal Integrations tab + Admin Integration Center.
    @router.get("/integration-readiness", dependencies=[Depends(require_any_portal)])
    async def integration_readiness():
        async def _provider(name: str) -> Dict[str, Any]:
            doc = await db.integration_settings.find_one({"provider": name}, {"_id": 0}) or {}
            enabled = bool(doc.get("enabled"))
            demo_mode = bool(doc.get("demo_mode"))
            # Mapping counts — these never call out to the external API
            mapped = await db.asset_mappings.count_documents({"provider": name})
            ext_unmapped = await db.unmapped_external_records.count_documents({"provider": name})
            return {
                "provider": name,
                "enabled": enabled,
                "demo_mode": demo_mode,
                "status": doc.get("status") or ("Not Connected"),
                "last_sync_at": doc.get("last_sync_at"),
                "tracked_assets": mapped,
                "unmapped_external": ext_unmapped,
            }

        motive = await _provider("motive")
        maintainx = await _provider("maintainx")

        # P1-E · Live Motive rollups from `asset_mappings.motive.*`
        # — replaces the hard-coded zeros so Operations/Dispatch tiles
        # finally reflect telematics ground truth. Stale/idle thresholds
        # match operator convention (idle = parked >30 min; not-reporting
        # = no telemetry within 24 h).
        from datetime import datetime as _dt, timedelta as _td, timezone as _tz  # noqa: PLC0415
        now_utc = _dt.now(_tz.utc)
        idle_after = (now_utc - _td(minutes=30)).isoformat()
        stale_after = (now_utc - _td(hours=24)).isoformat()
        try:
            motive["gps_enabled_assets"] = await db.asset_mappings.count_documents(
                {"provider": "motive", "motive.gps_enabled": True}
            )
            motive["moving_count"] = await db.asset_mappings.count_documents({
                "provider": "motive", "motive.gps_enabled": True,
                "motive.speed_kph": {"$gt": 5},
                "motive.located_at": {"$gte": idle_after},
            })
            motive["idle_count"] = await db.asset_mappings.count_documents({
                "provider": "motive", "motive.gps_enabled": True,
                "motive.speed_kph": {"$lte": 5},
                "motive.located_at": {"$gte": idle_after},
            })
            motive["not_reporting"] = await db.asset_mappings.count_documents({
                "provider": "motive", "motive.gps_enabled": True,
                "$or": [
                    {"motive.located_at": {"$lt": stale_after}},
                    {"motive.located_at": None},
                ],
            })
            motive["linked_to_masci"] = await db.asset_mappings.count_documents(
                {"provider": "motive", "masci_equipment_id": {"$ne": ""}}
            )
            motive["linked_drivers"] = await db.employee_mappings.count_documents(
                {"provider": "motive", "masci_employee_id": {"$ne": ""}}
            )
        except Exception:  # noqa: BLE001
            motive.setdefault("idle_count", 0)
            motive.setdefault("not_reporting", 0)

        # MaintainX-specific placeholder rollups from internal holds
        maintainx["equipment_down"] = await db.asset_holds.count_documents(
            {"active": True, "kind": "maintenance", "severity": {"$in": ["critical", "high"]}}
        )
        maintainx["open_work_orders"] = await db.asset_holds.count_documents(
            {"active": True, "kind": "maintenance"}
        )
        maintainx["overdue_pms"] = 0  # placeholder until MaintainX integration
        maintainx["maintenance_holds"] = maintainx["open_work_orders"]

        return {"motive": motive, "maintainx": maintainx}

    # ── Utilization ──────────────────────────────────────────────────
    @router.get("/utilization", dependencies=[Depends(require_any_portal)])
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
    @router.get("/assets/{asset_id}/profile", dependencies=[Depends(require_any_portal)])
    async def asset_profile(asset_id: str, events_limit: int = Query(25, ge=1, le=200)):
        eq = await db.equipment_master.find_one({"id": asset_id}, {"_id": 0})
        if not eq:
            raise HTTPException(404, "asset not found")

        status_block = await _compute_current_status(db, asset_id)

        # Mapping (Motive + MaintainX placeholders sourced from
        # asset_mappings — never the master record)
        mapping = await db.asset_mappings.find_one({"masci_equipment_id": asset_id}, {"_id": 0})

        # P1-D · Live Motive telemetry block for the AssetProfile UI.
        # All data is sourced from `asset_mappings.motive.*` (no new
        # APIs, no live external calls). UI replaces the legacy
        # `MotivePlaceholder` with this payload.
        # P1-C · Source-attributed current driver/operator hierarchy:
        #   1. Motive `current_vehicle_id` join → driver in this truck
        #      RIGHT NOW (most authoritative)
        #   2. Active asset_assignments.operator_name (Dispatch ground truth)
        #   3. Most recent equipment_inspections operator (today's DVIR/preop)
        motive_live = await _build_motive_live_block(db, mapping)
        current_operator = await _resolve_current_operator(
            db, asset_id=asset_id,
            motive_vehicle_id=(mapping or {}).get("motive", {}).get("vehicle_id"),
            active_assignment=status_block["active_assignment"],
        )

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

        # P1.5-H · Motive event timeline for this asset (read-only · no
        # workflow side-effects). Resolves via the existing
        # asset_mappings join, decorated to operational language.
        motive_events_recent = []
        try:
            mv = (mapping or {}).get("motive") or {}
            vid = (mv.get("vehicle_id") or "").strip()
            aid = (mv.get("asset_id") or "").strip()
            if vid or aid:
                q: Dict[str, Any] = {"is_demo": {"$ne": True}}
                if vid and aid:
                    q["$or"] = [{"vehicle_id": vid}, {"raw.asset.id": aid}]
                elif vid:
                    q["vehicle_id"] = vid
                else:
                    q["raw.asset.id"] = aid
                motive_events_recent = await db.motive_events.find(
                    q, {"_id": 0},
                ).sort("event_at", -1).to_list(25)
        except Exception:  # noqa: BLE001
            pass

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
            "motive_live": motive_live,
            "motive_events": motive_events_recent,
            "current_operator": current_operator,
            "recent_preops": recent_preops,
            "safety_corrective_actions": safety_cas,
            "transfers": transfers,
            "events": events,
            "events_total_for_asset": await db.operations_events.count_documents({"asset_id": asset_id}),
        }

    # ── Idle Equipment Alerts ───────────────────────────────────────
    # Read-only visibility layer. Looks at every active assignment and
    # measures days since the most recent operations event tied to the
    # asset (preops, transfers, holds, assignments, future Motive
    # placeholders, etc.). NEVER auto-changes status. NEVER notifies.
    @router.get("/idle-equipment", dependencies=[Depends(require_any_portal)])
    async def idle_equipment(min_days: int = Query(14, ge=1, le=365), limit: int = Query(200, ge=1, le=1000)):
        from datetime import datetime as _dt, timezone as _tz
        now = _dt.now(_tz.utc)

        active_assignments = await db.asset_assignments.find(
            {"active": True}, {"_id": 0},
        ).to_list(20000)
        if not active_assignments:
            return {"min_days": min_days, "now": _now_iso(), "rows": [], "totals": {"d7": 0, "d14": 0, "d30": 0, "matched": 0}}

        asset_ids = [a["asset_id"] for a in active_assignments]
        # bulk-fetch the most recent event per asset using aggregation
        pipeline = [
            {"$match": {"asset_id": {"$in": asset_ids}}},
            {"$sort": {"created_at": -1}},
            {"$group": {"_id": "$asset_id",
                        "last_at": {"$first": "$created_at"},
                        "last_type": {"$first": "$event_type"},
                        "last_title": {"$first": "$event_title"}}},
        ]
        latest_by_asset: Dict[str, Dict[str, Any]] = {}
        async for row in db.operations_events.aggregate(pipeline):
            latest_by_asset[row["_id"]] = {
                "last_at": row.get("last_at"),
                "last_type": row.get("last_type"),
                "last_title": row.get("last_title"),
            }

        # bulk-fetch unit info from equipment_master so we don't loop
        eq_cursor = db.equipment_master.find(
            {"id": {"$in": asset_ids}},
            {"_id": 0, "id": 1, "unit_number": 1, "name": 1, "equipment_type": 1},
        )
        eq_by_id: Dict[str, Dict[str, Any]] = {e["id"]: e async for e in eq_cursor}

        rows: List[Dict[str, Any]] = []
        d7 = d14 = d30 = 0
        for a in active_assignments:
            aid = a["asset_id"]
            ev = latest_by_asset.get(aid)
            # fall back to assignment.started_at when there are no events
            baseline = (ev or {}).get("last_at") or a.get("started_at") or _now_iso()
            try:
                last_dt = _dt.fromisoformat(baseline.replace("Z", "+00:00"))
            except Exception:
                continue
            delta_days = (now - last_dt).days
            if delta_days < min_days:
                continue
            eq = eq_by_id.get(aid, {})
            rows.append({
                "asset_id": aid,
                "unit_number": eq.get("unit_number") or a.get("masci_unit_number") or "",
                "equipment_name": eq.get("name") or "",
                "equipment_type": eq.get("equipment_type") or "",
                "project_number": a.get("project_number") or "",
                "project_name": a.get("project_name") or "",
                "operator_name": a.get("operator_name") or "",
                "assigned_at": a.get("started_at"),
                "last_activity_at": baseline,
                "last_activity_type": (ev or {}).get("last_type"),
                "last_activity_title": (ev or {}).get("last_title"),
                "days_inactive": delta_days,
                "had_events": bool(ev),
            })
            if delta_days >= 7:
                d7 += 1
            if delta_days >= 14:
                d14 += 1
            if delta_days >= 30:
                d30 += 1

        rows.sort(key=lambda r: r["days_inactive"], reverse=True)
        return {
            "min_days": min_days,
            "now": _now_iso(),
            "rows": rows[:limit],
            "totals": {"d7": d7, "d14": d14, "d30": d30, "matched": len(rows)},
        }

    return router


__all__ = [
    "build_operations_router",
    "ensure_operations_indexes",
    "write_event",
    "create_pending_maintenance_hold",
    "TRANSFER_STATES",
    "ASSET_OP_STATUSES",
    "EVENT_SEVERITIES",
    "EVENT_STATUSES",
]

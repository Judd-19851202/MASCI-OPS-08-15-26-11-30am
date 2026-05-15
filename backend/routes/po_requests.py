"""
routes/po_requests.py — Iter153 (Phase 2.5) · Phase D.

OPERATIONAL PO REQUEST & RECEIPT TRACKING.

NOT accounting software. NOT ERP. This is for field accountability:
  * Supervisor submits a PO request from the field.
  * PM/HR/Admin approve, reject, or ask for clarification.
  * After purchase, supervisor uploads the receipt (R2).
  * Missing receipts after a configurable window auto-create a Task
    (Phase A — task_service) and Notification.
  * Cross-system: offboarding-summary surfaces any open POs tied to
    the departing employee.

Numbering scheme: `MASCI-PO-YY-MM-NNN`
  * Globally unique company-wide (year+month+sequence — never reused).
  * Sequence resets each YY-MM bucket so numbers stay short.
  * Manual PO numbers (issued by accounting) can override the
    generated one — `po_number_source ∈ {generated, manual}` records
    which is which for audit.
"""
from __future__ import annotations

import logging
import os
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter, Depends, File, Form, HTTPException, Query, UploadFile,
)
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

ALLOWED_STATUSES = {
    "Draft", "Submitted", "Pending Approval",
    "Approved", "Rejected", "Clarification Needed",
    "Pending Receipt", "Receipt Uploaded", "Closed",
    "Overdue Receipt", "Cancelled",
}
OPEN_STATUSES = {"Submitted", "Pending Approval", "Approved",
                 "Pending Receipt", "Clarification Needed",
                 "Overdue Receipt"}

ALLOWED_CATEGORIES = [
    "Materials", "Small tools", "Safety supplies", "Fuel",
    "Equipment repair", "Rental", "Subcontractor support",
    "Office/admin", "Emergency purchase", "Other",
]
ALLOWED_URGENCY = {"Normal", "Urgent", "Emergency"}

# Receipt grace window — env-overridable.
RECEIPT_GRACE_DAYS = int(os.environ.get("PO_RECEIPT_GRACE_DAYS", "7"))


# ──────────────────────────────────────────────────────────────────
# Pydantic
# ──────────────────────────────────────────────────────────────────
class PoRequestCreate(BaseModel):
    project_number: str = Field(..., min_length=1, max_length=64)
    vendor: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1, max_length=2000)
    estimated_amount: float = Field(..., ge=0)
    category: str = Field(default="Materials")
    urgency: str = Field(default="Normal")
    needed_by_date: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
    supervisor_signature: Optional[str] = Field(default=None, max_length=120)

    @field_validator("category")
    @classmethod
    def _v_cat(cls, v: str) -> str:
        if v not in ALLOWED_CATEGORIES:
            raise ValueError(f"category must be one of {ALLOWED_CATEGORIES}")
        return v

    @field_validator("urgency")
    @classmethod
    def _v_urg(cls, v: str) -> str:
        if v not in ALLOWED_URGENCY:
            raise ValueError("invalid urgency")
        return v


class PoApprovalAction(BaseModel):
    action: str  # approve | reject | clarify
    approved_amount: Optional[float] = Field(default=None, ge=0)
    po_number_manual: Optional[str] = Field(default=None, max_length=80)
    notes: Optional[str] = Field(default=None, max_length=2000)


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────
async def _next_po_number(db) -> str:
    """Generate next sequential MASCI-PO-YY-MM-NNN.

    Atomic via Mongo `$inc` on a counter doc keyed by YY-MM.
    """
    now = datetime.now(timezone.utc)
    yy = now.strftime("%y")
    mm = now.strftime("%m")
    key = f"po_seq_{yy}{mm}"
    doc = await db.system_counters.find_one_and_update(
        {"_id": key},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=True,
    ) if hasattr(db.system_counters, "find_one_and_update") else None
    # Fallback if find_one_and_update doesn't exist on the mock
    if doc is None:
        existing = await db.system_counters.find_one({"_id": key})
        if not existing:
            existing = {"_id": key, "value": 0}
            await db.system_counters.insert_one(existing)
        existing["value"] += 1
        await db.system_counters.update_one(
            {"_id": key}, {"$set": {"value": existing["value"]}}
        )
        seq = existing["value"]
    else:
        seq = doc.get("value", 1)
    return f"MASCI-PO-{yy}-{mm}-{seq:03d}"


def _strip(d: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not d:
        return d
    d.pop("_id", None)
    return d


def _actor_role(actor: Dict[str, Any]) -> str:
    return actor.get("_actor") or actor.get("role") or "admin"


def _actor_name(actor: Dict[str, Any]) -> str:
    return actor.get("name") or actor.get("email") or _actor_role(actor)


async def _audit_push(db, po_id: str, action: str,
                       actor: Dict[str, Any], details: Optional[Dict] = None) -> None:
    entry = {
        "at": datetime.now(timezone.utc),
        "by": {"role": _actor_role(actor), "name": _actor_name(actor)},
        "action": action,
        "details": details or {},
    }
    await db.po_requests.update_one(
        {"id": po_id}, {"$push": {"audit": entry}}
    )


async def _fan_out_task(db, po: Dict[str, Any], kind: str,
                         priority: str = "Medium",
                         assignee_role: str = "leadership") -> None:
    """Helper to emit task via Phase A service."""
    from routes.tasks_notifications import task_service  # noqa: PLC0415
    titles = {
        "approval_needed": f"PO needs approval: {po.get('po_number') or po.get('id')[:8]}",
        "receipt_missing": f"Receipt missing for {po.get('po_number')}",
        "clarification_needed": f"PO needs clarification: {po.get('po_number') or po.get('id')[:8]}",
    }
    descs = {
        "approval_needed": f"{po.get('vendor')} · est ${po.get('estimated_amount')} · {po.get('urgency')}\n\n{po.get('description', '')[:400]}",
        "receipt_missing": f"PO {po.get('po_number')} approved on {po.get('approved_at')} — receipt not yet uploaded.",
        "clarification_needed": f"PM/HR/Admin requested clarification on PO {po.get('po_number') or po.get('id')[:8]}.",
    }
    try:
        await task_service.create(db, {
            "title": titles.get(kind, kind),
            "description": descs.get(kind, ""),
            "source_module": "po.requests" if kind != "receipt_missing" else "po.receipts",
            "source_record_id": po.get("id"),
            "linked_project_number": po.get("project_number"),
            "linked_employee_id": po.get("requested_by_employee_id"),
            "linked_po_id": po.get("id"),
            "assignee_role": assignee_role,
            "priority": priority,
            "created_by": {"role": "system", "name": "PO Workflow"},
        })
    except Exception as e:  # pragma: no cover
        logger.warning("PO task fan-out failed: %s", e)


# ──────────────────────────────────────────────────────────────────
# Background watcher — flags POs with missing receipts past grace window
# ──────────────────────────────────────────────────────────────────
async def scan_missing_receipts(db, dry_run: bool = False) -> Dict[str, Any]:
    """Walk Approved/Pending-Receipt POs older than RECEIPT_GRACE_DAYS
    without a receipt. Flip to 'Overdue Receipt' and auto-create a
    task once per PO (idempotent via missing_receipt_flagged flag).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=RECEIPT_GRACE_DAYS)
    fired: List[str] = []
    cur = db.po_requests.find({
        "status": {"$in": ["Approved", "Pending Receipt"]},
        "missing_receipt_flagged": {"$ne": True},
        "approved_at": {"$lt": cutoff},
        "receipt_url": None,
    }, {"_id": 0})
    async for d in cur:
        if not dry_run:
            await db.po_requests.update_one(
                {"id": d["id"]},
                {"$set": {
                    "status": "Overdue Receipt",
                    "missing_receipt_flagged": True,
                    "updated_at": datetime.now(timezone.utc),
                }},
            )
            await _fan_out_task(db, d, kind="receipt_missing",
                                 priority="High",
                                 assignee_role="leadership")
        fired.append(d["id"])
    return {"flagged": len(fired), "ids": fired, "dry_run": dry_run}


async def ensure_po_requests_indexes(db) -> None:
    try:
        await db.po_requests.create_index("id", unique=True)
        # po_number is null between submission and approval — sparse
        # alone won't help because Mongo treats `null` as an indexed
        # value. partialFilterExpression skips both missing and null,
        # enforcing uniqueness ONLY on assigned string PO numbers.
        await db.po_requests.create_index(
            "po_number", unique=True,
            partialFilterExpression={"po_number": {"$type": "string"}},
        )
        await db.po_requests.create_index("status")
        await db.po_requests.create_index("project_number")
        await db.po_requests.create_index("requested_by_employee_id")
        await db.po_requests.create_index("vendor")
        await db.po_requests.create_index("created_at")
        await db.po_requests.create_index("approved_at")
        # `system_counters` uses _id directly as the bucket key — no extra index needed.
    except Exception as e:  # pragma: no cover
        logger.warning("po_requests index bootstrap failed: %s", e)


# ──────────────────────────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────────────────────────
def build_po_requests_router(
    db, require_any_portal_token, require_admin,
    r2_upload_callable=None,
):
    """Builds the PO router.

    `r2_upload_callable` is an optional async callable that takes
    (file_bytes: bytes, filename: str, content_type: str) and returns
    a public URL. If None, receipt uploads are stored as data-URLs
    (acceptable for dev/preview but should be wired to R2 in prod).
    """
    router = APIRouter(tags=["po-requests"])

    def _can_approve(actor: Dict[str, Any]) -> bool:
        return _actor_role(actor) in ("pm", "hr", "admin")

    def _can_submit(actor: Dict[str, Any]) -> bool:
        # Field Leadership is the primary submitter, but anyone with a
        # portal token can submit (a CA-spawned PO from PM, for example).
        return _actor_role(actor) in ("leadership", "pm", "hr", "admin",
                                       "shop", "safety")

    def _scope_filter(actor: Dict[str, Any]) -> Dict[str, Any]:
        """Default-narrow scope per role; admin sees everything."""
        role = _actor_role(actor)
        if role == "admin":
            return {}
        if role == "leadership":
            return {"$or": [
                {"requested_by_role": "leadership"},
                {"requested_by_user_id": actor.get("id")},
            ]}
        # PM / HR see everything they can approve. Safety/Shop see narrow.
        if role in ("pm", "hr"):
            return {}
        return {"requested_by_role": role}

    # ── PO CRUD ───────────────────────────────────────────────────
    @router.get("/api/po-requests")
    async def list_pos(
        actor: Dict[str, Any] = Depends(require_any_portal_token),
        status: Optional[str] = Query(default=None),
        project_number: Optional[str] = Query(default=None),
        requested_by_employee_id: Optional[str] = Query(default=None),
        q: Optional[str] = Query(default=None, max_length=80),
        limit: int = Query(default=200, ge=1, le=500),
    ) -> Dict[str, Any]:
        clauses: List[Dict[str, Any]] = []
        scope = _scope_filter(actor)
        if scope:
            clauses.append(scope)
        if status:
            clauses.append({"status": status})
        if project_number:
            clauses.append({"project_number": project_number})
        if requested_by_employee_id:
            clauses.append({"requested_by_employee_id": requested_by_employee_id})
        if q:
            clauses.append({"$or": [
                {"po_number": {"$regex": q, "$options": "i"}},
                {"vendor":    {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
            ]})
        final = {"$and": clauses} if clauses else {}
        cur = db.po_requests.find(final, {"_id": 0}).sort(
            "created_at", -1).limit(limit)
        items = [_strip(d) async for d in cur]
        return {"items": items, "count": len(items)}

    @router.get("/api/po-requests/summary")
    async def summary(actor: Dict[str, Any] = Depends(require_any_portal_token)) -> Dict[str, Any]:
        scope = _scope_filter(actor)
        pipeline = [{"$match": scope} if scope else {"$match": {}},
                    {"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        by_status: Dict[str, int] = {}
        async for d in db.po_requests.aggregate(pipeline):
            by_status[d["_id"] or "Submitted"] = d["count"]
        pending_approval = by_status.get("Pending Approval", 0) + by_status.get("Submitted", 0)
        pending_receipt = by_status.get("Approved", 0) + by_status.get("Pending Receipt", 0)
        overdue_receipt = by_status.get("Overdue Receipt", 0)
        return {
            "by_status": by_status,
            "pending_approval": pending_approval,
            "pending_receipt": pending_receipt,
            "overdue_receipt": overdue_receipt,
        }

    @router.get("/api/po-requests/{po_id}")
    async def get_po(po_id: str, actor: Dict[str, Any] = Depends(require_any_portal_token)) -> Dict[str, Any]:
        doc = await db.po_requests.find_one({"id": po_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "PO not found")
        return _strip(doc)

    @router.post("/api/po-requests")
    async def create_po(
        body: PoRequestCreate,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        if not _can_submit(actor):
            raise HTTPException(403, "Not authorized to submit PO requests")
        now = datetime.now(timezone.utc)
        po = {
            "id": str(uuid.uuid4()),
            "po_number": None,                # assigned on approval
            "po_number_source": None,
            "project_number": body.project_number,
            "vendor": body.vendor,
            "description": body.description,
            "estimated_amount": float(body.estimated_amount),
            "approved_amount": None,
            "category": body.category,
            "urgency": body.urgency,
            "needed_by_date": body.needed_by_date,
            "notes": body.notes,
            "supervisor_signature": body.supervisor_signature,
            "status": "Submitted",
            "requested_by_role": _actor_role(actor),
            "requested_by_user_id": actor.get("id"),
            "requested_by_employee_id": actor.get("employee_id"),
            "requested_by_name": _actor_name(actor),
            "approved_by": None, "approved_at": None,
            "rejected_by": None, "rejected_at": None, "rejection_reason": None,
            "receipt_url": None, "receipt_filename": None,
            "receipt_amount": None, "receipt_notes": None,
            "receipt_uploaded_at": None, "receipt_uploaded_by": None,
            "missing_receipt_flagged": False,
            "created_at": now, "updated_at": now,
            "audit": [{
                "at": now, "by": {"role": _actor_role(actor),
                                  "name": _actor_name(actor)},
                "action": "submitted",
            }],
        }
        await db.po_requests.insert_one(po)

        # Fan-out approval task via Phase A
        priority = "Critical" if body.urgency == "Emergency" else (
            "High" if body.urgency == "Urgent" else "Medium")
        await _fan_out_task(db, po, "approval_needed",
                             priority=priority, assignee_role="pm")
        return _strip(po)

    @router.post("/api/po-requests/{po_id}/approve")
    async def approve_po(
        po_id: str,
        body: PoApprovalAction,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        if not _can_approve(actor):
            raise HTTPException(403, "Not authorized to approve POs")
        existing = await db.po_requests.find_one({"id": po_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "PO not found")
        if existing["status"] in ("Closed", "Cancelled", "Rejected"):
            raise HTTPException(409, f"PO is {existing['status']} — cannot change")

        action = (body.action or "").lower()
        now = datetime.now(timezone.utc)
        update: Dict[str, Any] = {"updated_at": now}
        approver = {"role": _actor_role(actor), "name": _actor_name(actor)}

        if action == "approve":
            po_number = body.po_number_manual or await _next_po_number(db)
            source = "manual" if body.po_number_manual else "generated"
            update.update({
                "status": "Approved",
                "po_number": po_number,
                "po_number_source": source,
                "approved_by": approver,
                "approved_at": now,
                "approved_amount": (
                    float(body.approved_amount)
                    if body.approved_amount is not None
                    else existing.get("estimated_amount")
                ),
            })
            audit_action = "approved"
        elif action == "reject":
            update.update({
                "status": "Rejected",
                "rejected_by": approver,
                "rejected_at": now,
                "rejection_reason": body.notes,
            })
            audit_action = "rejected"
        elif action == "clarify":
            update.update({
                "status": "Clarification Needed",
                "rejection_reason": body.notes,
            })
            audit_action = "clarification_requested"
            await _fan_out_task(db, existing, "clarification_needed",
                                 priority="High",
                                 assignee_role=existing.get("requested_by_role") or "leadership")
        else:
            raise HTTPException(400, "action must be 'approve', 'reject', or 'clarify'")

        await db.po_requests.update_one({"id": po_id}, {"$set": update})
        await _audit_push(db, po_id, audit_action, actor,
                           {"notes": body.notes})
        return await get_po(po_id, actor=actor)

    @router.post("/api/po-requests/{po_id}/receipt")
    async def upload_receipt(
        po_id: str,
        file: UploadFile = File(...),
        receipt_amount: Optional[float] = Form(default=None),
        receipt_notes: Optional[str] = Form(default=None),
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        existing = await db.po_requests.find_one({"id": po_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "PO not found")
        if existing["status"] not in ("Approved", "Pending Receipt",
                                       "Overdue Receipt"):
            raise HTTPException(409, "PO is not ready for receipt upload")

        # Upload — prefer R2 if configured, else inline data-URL fallback.
        content = await file.read()
        if len(content) > 12 * 1024 * 1024:
            raise HTTPException(413, "Receipt too large (max 12MB)")
        receipt_url: str
        if r2_upload_callable:
            try:
                receipt_url = await r2_upload_callable(
                    content, file.filename or "receipt",
                    file.content_type or "application/octet-stream",
                )
            except Exception as e:
                logger.warning("R2 upload failed; falling back to data-URL: %s", e)
                import base64
                receipt_url = (
                    f"data:{file.content_type or 'application/octet-stream'}"
                    f";base64,{base64.b64encode(content).decode()}"
                )
        else:
            import base64
            receipt_url = (
                f"data:{file.content_type or 'application/octet-stream'}"
                f";base64,{base64.b64encode(content).decode()}"
            )

        now = datetime.now(timezone.utc)
        update = {
            "status": "Receipt Uploaded",
            "receipt_url": receipt_url,
            "receipt_filename": file.filename,
            "receipt_amount": (float(receipt_amount)
                               if receipt_amount is not None else None),
            "receipt_notes": receipt_notes,
            "receipt_uploaded_at": now,
            "receipt_uploaded_by": {"role": _actor_role(actor),
                                     "name": _actor_name(actor)},
            "missing_receipt_flagged": False,
            "updated_at": now,
        }
        await db.po_requests.update_one({"id": po_id}, {"$set": update})
        await _audit_push(db, po_id, "receipt_uploaded", actor,
                           {"filename": file.filename})
        return await get_po(po_id, actor=actor)

    @router.post("/api/po-requests/{po_id}/close")
    async def close_po(
        po_id: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        if not _can_approve(actor):
            raise HTTPException(403, "Not authorized to close POs")
        await db.po_requests.update_one({"id": po_id}, {"$set": {
            "status": "Closed",
            "updated_at": datetime.now(timezone.utc),
        }})
        await _audit_push(db, po_id, "closed", actor)
        return await get_po(po_id, actor=actor)

    @router.post("/api/po-requests/{po_id}/cancel")
    async def cancel_po(
        po_id: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await db.po_requests.update_one({"id": po_id}, {"$set": {
            "status": "Cancelled",
            "updated_at": datetime.now(timezone.utc),
        }})
        await _audit_push(db, po_id, "cancelled", actor)
        return await get_po(po_id, actor=actor)

    # Admin-only scanner
    @router.post("/api/admin/po-requests/scan-missing-receipts",
                  dependencies=[Depends(require_admin)])
    async def admin_scan_receipts() -> Dict[str, Any]:
        return await scan_missing_receipts(db, dry_run=False)

    @router.get("/api/admin/po-requests/scan-missing-receipts/preview",
                 dependencies=[Depends(require_admin)])
    async def admin_scan_receipts_preview() -> Dict[str, Any]:
        return await scan_missing_receipts(db, dry_run=True)

    return router


__all__ = [
    "build_po_requests_router",
    "ensure_po_requests_indexes",
    "scan_missing_receipts",
    "ALLOWED_STATUSES", "ALLOWED_CATEGORIES", "ALLOWED_URGENCY",
    "RECEIPT_GRACE_DAYS",
]

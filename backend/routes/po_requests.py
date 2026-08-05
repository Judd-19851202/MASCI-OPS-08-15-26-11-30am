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

from lib.mongo_query import safe_regex

import logging
import os
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile,
)
from pydantic import BaseModel, Field, field_validator

from lib.enterprise_governance import build_governance_actor_context, require_governed_action

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
    # Track 15.73 Slice 4 · canonical identity preservation. Optional
    # vendor master record reference. UI populates this when the user
    # picks a vendor from the SupplierCombo dropdown. Display name
    # stays in `vendor` for human-readable PDFs / lists; `vendor_id` is
    # the resolver-preferred key for downstream joins.
    vendor_id: Optional[str] = Field(default=None, max_length=64)
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


class PoClarificationResponse(BaseModel):
    response: str = Field(..., min_length=1, max_length=2000)


def _iso(dt) -> str:
    # TRUST-TIME-1 doctrine · 2026-05-28
    # ----------------------------------
    # All operator-facing timestamps MUST round-trip as ABSOLUTE
    # (tz-aware) ISO strings so the browser can convert them to local
    # time. Historical writes used `datetime.now(timezone.utc)` (good)
    # but Mongo round-tripped them as NAIVE datetimes when the Motor
    # client wasn't tz-aware. That made the frontend interpret them
    # as LOCAL time → operator at 9:43 AM Eastern saw 1:43 PM.
    #
    # Belt-and-braces:
    #   * server.py now uses `AsyncIOMotorClient(..., tz_aware=True)`
    #     so reads come back UTC-aware.
    #   * This helper still defends against historical naive datetimes
    #     by tagging them as UTC explicitly before serializing.
    if not dt:
        return ""
    if isinstance(dt, str):
        return dt
    try:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.replace(microsecond=0).isoformat()
    except Exception:
        return str(dt)


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


async def _next_po_request_number(db) -> str:
    now = datetime.now(timezone.utc)
    yy = now.strftime("%y")
    mm = now.strftime("%m")
    key = f"po_request_seq_{yy}{mm}"
    doc = await db.system_counters.find_one_and_update(
        {"_id": key},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=True,
    ) if hasattr(db.system_counters, "find_one_and_update") else None
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
    return f"POREQ-{yy}-{mm}-{seq:03d}"


def _strip(d: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not d:
        return d
    d.pop("_id", None)
    return d


def _actor_role(actor: Dict[str, Any]) -> str:
    return actor.get("_actor") or actor.get("role") or "admin"


def _actor_name(actor: Dict[str, Any]) -> str:
    return actor.get("name") or actor.get("email") or _actor_role(actor)


def _governed_actor_id(actor: Dict[str, Any]) -> str:
    return str(actor.get("canonical_user_id") or actor.get("id") or actor.get("user_id") or "")


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
                         assignee_role: str = "leadership",
                         cc_roles: Optional[List[str]] = None) -> None:
    """Helper to emit task via Phase A service.

    iter242 — ``cc_roles`` adds *visibility-only* notifications to additional
    roles WITHOUT creating duplicate tasks. The primary task ownership stays
    with ``assignee_role`` (so the approval queue doesn't double-count), but
    the listed cc roles get a parallel notification in their bell feed.

    Operational use:
      * ``approval_needed`` — primary task owned by ``pm`` (which covers the
        assigned PM AND any Co-PMs on the job, because both are
        ``pm``-role users). ``cc_roles=["hr"]`` so HR also sees the
        approval request in their bell feed. Admin sees everything by
        virtue of cross-portal visibility.
    """
    from routes.tasks_notifications import task_service, notification_service  # noqa: PLC0415
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
    title = titles.get(kind, kind)
    desc = descs.get(kind, "")
    try:
        await task_service.create(db, {
            "title": title,
            "description": desc,
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
    # iter242 — Parallel visibility notifications for cc_roles. These do
    # NOT create duplicate tasks; they only push a bell-feed notification
    # so the role can see + act on the underlying PO via existing
    # approval endpoints (HR is already in `_can_approve`).
    for cc_role in (cc_roles or []):
        if cc_role == assignee_role:
            continue  # primary fanout already covers this role
        try:
            await notification_service.fanout(db, {
                "type": "po.approval_visibility",
                "title": title,
                "message": desc[:200] if desc else None,
                "severity": "Info" if priority in ("Low", "Medium") else "Warning",
                "recipient_role": cc_role,
                "linked_source_module": "po.requests",
                "linked_source_record_id": po.get("id"),
                "linked_project_number": po.get("project_number"),
            })
        except Exception as e:  # pragma: no cover
            logger.warning("PO cc-role notification (%s) failed: %s", cc_role, e)


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
                                 assignee_role="pm",
                                 cc_roles=["hr"])
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
        await db.po_requests.create_index(
            "request_number", unique=True,
            partialFilterExpression={"request_number": {"$type": "string"}},
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

    async def _governed_actor(actor: Dict[str, Any]) -> Dict[str, Any]:
        return await build_governance_actor_context(db, actor)

    # WP15_SPECIAL_CASE_INFRASTRUCTURE:
    # PO list/read visibility is a read-model shaping concern after the
    # Governance Engine has already authorized access to the PO domain.
    # This helper preserves existing user-facing visibility slices without
    # duplicating business authorization decisions.
    def _po_read_model_filter(actor: Dict[str, Any]) -> Dict[str, Any]:
        """Default-narrow scope per role; admin/HR see company-wide slices."""
        role = _actor_role(actor)
        if role == "admin":
            return {}
        if role == "hr":
            return {}
        if role == "pm":
            project_numbers = list(actor.get("project_numbers") or [])
            return {"project_number": {"$in": project_numbers}} if project_numbers else {"__pm_empty_scope__": True}
        if role == "leadership":
            return {"$or": [
                {"requested_by_role": "leadership"},
                {"requested_by_user_id": _governed_actor_id(actor)},
            ]}
        governed_user_id = _governed_actor_id(actor)
        own_clauses = [{"requested_by_role": role}]
        if governed_user_id:
            own_clauses.append({"requested_by_user_id": governed_user_id})
        return {"$or": own_clauses}

    async def _require_po_action(request: Request, actor: Dict[str, Any], action_key: str, resource: Dict[str, Any]) -> None:
        await require_governed_action(
            db,
            actor=actor,
            action_key=action_key,
            resource_type="po_request",
            resource=resource,
            requested_context={"project_number": resource.get("project_number") or "", "status": resource.get("status") or ""},
            request=request,
        )

    def _po_visible_to_actor(actor: Dict[str, Any], po: Dict[str, Any]) -> bool:
        scope = _po_read_model_filter(actor)
        if not scope:
            return True
        if scope.get("__pm_empty_scope__"):
            return False
        if "project_number" in scope:
            allowed = set((scope.get("project_number") or {}).get("$in") or [])
            return str(po.get("project_number") or "") in allowed
        clauses = list(scope.get("$or") or [])
        requested_by_role = str(po.get("requested_by_role") or "")
        requested_by_user_id = str(po.get("requested_by_user_id") or "")
        for clause in clauses:
            if clause.get("requested_by_role") == requested_by_role:
                return True
            if clause.get("requested_by_user_id") == requested_by_user_id:
                return True
        return False

    # ── PO CRUD ───────────────────────────────────────────────────
    @router.get("/api/po-requests")
    async def list_pos(
        request: Request,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
        status: Optional[str] = Query(default=None),
        project_number: Optional[str] = Query(default=None),
        vendor: Optional[str] = Query(default=None, max_length=120),
        requested_by_user_id: Optional[str] = Query(default=None),
        requested_by_name: Optional[str] = Query(default=None, max_length=120),
        requested_by_employee_id: Optional[str] = Query(default=None),
        mine_only: bool = Query(default=False,
            description="Only POs submitted by the current actor."),
        missing_receipt_only: bool = Query(default=False,
            description="Approved/Pending-Receipt/Overdue without a receipt."),
        q: Optional[str] = Query(default=None, max_length=80),
        limit: int = Query(default=200, ge=1, le=500),
    ) -> Dict[str, Any]:
        await _require_po_action(request, actor, "po_requests.read", {"id": "po-feed", "project_number": project_number or ""})
        governed_actor = await _governed_actor(actor)
        clauses: List[Dict[str, Any]] = []
        scope = _po_read_model_filter(governed_actor)
        if scope:
            clauses.append(scope)
        if status:
            clauses.append({"status": status})
        if project_number:
            clauses.append({"project_number": project_number})
        if vendor:
            clauses.append({"vendor": {"$regex": re.escape(vendor),
                                        "$options": "i"}})
        if requested_by_user_id:
            clauses.append({"requested_by_user_id": requested_by_user_id})
        if requested_by_name:
            clauses.append({"requested_by_name": {
                "$regex": re.escape(requested_by_name), "$options": "i"}})
        if requested_by_employee_id:
            clauses.append({"requested_by_employee_id": requested_by_employee_id})
        if mine_only and _governed_actor_id(governed_actor):
            clauses.append({"requested_by_user_id": _governed_actor_id(governed_actor)})
        if missing_receipt_only:
            clauses.append({
                "status": {"$in": ["Approved", "Pending Receipt",
                                    "Overdue Receipt"]},
                "receipt_url": None,
            })
        if q:
            clauses.append({"$or": [
                {"po_number": safe_regex(q)},
                {"vendor":    safe_regex(q)},
                {"description": safe_regex(q)},
            ]})
        final = {"$and": clauses} if clauses else {}
        cur = db.po_requests.find(final, {"_id": 0}).sort(
            "created_at", -1).limit(limit)
        items = [_strip(d) async for d in cur]
        return {"items": items, "count": len(items)}

    @router.get("/api/po-requests/summary")
    async def summary(request: Request, actor: Dict[str, Any] = Depends(require_any_portal_token)) -> Dict[str, Any]:
        await _require_po_action(request, actor, "po_requests.read", {"id": "po-summary", "project_number": ""})
        governed_actor = await _governed_actor(actor)
        scope = _po_read_model_filter(governed_actor)
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

    # NOTE: /export.csv MUST be declared BEFORE the /{po_id} variable
    # route below or FastAPI will try to resolve "export.csv" as a
    # po_id and return 404 from get_po.
    @router.get("/api/po-requests/export.csv")
    async def export_csv(
        request: Request,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
        status: Optional[str] = Query(default=None),
        project_number: Optional[str] = Query(default=None),
        vendor: Optional[str] = Query(default=None, max_length=120),
        requested_by_name: Optional[str] = Query(default=None, max_length=120),
        missing_receipt_only: bool = Query(default=False),
    ):
        """CSV export — Admin/PM/HR/Leadership. Scope is respected:
        Field Leadership only exports their own POs. Includes all
        operational columns needed for accounting/audit handoff."""
        import csv as _csv
        import io as _io
        from fastapi.responses import StreamingResponse  # noqa: PLC0415

        await _require_po_action(request, actor, "po_requests.read", {"id": "po-export", "project_number": project_number or ""})
        governed_actor = await _governed_actor(actor)
        clauses: List[Dict[str, Any]] = []
        scope = _po_read_model_filter(governed_actor)
        if scope:
            clauses.append(scope)
        if status:
            clauses.append({"status": status})
        if project_number:
            clauses.append({"project_number": project_number})
        if vendor:
            clauses.append({"vendor": {"$regex": re.escape(vendor),
                                        "$options": "i"}})
        if requested_by_name:
            clauses.append({"requested_by_name": {
                "$regex": re.escape(requested_by_name), "$options": "i"}})
        if missing_receipt_only:
            clauses.append({
                "status": {"$in": ["Approved", "Pending Receipt",
                                    "Overdue Receipt"]},
                "receipt_url": None,
            })
        final = {"$and": clauses} if clauses else {}

        buf = _io.StringIO()
        w = _csv.writer(buf)
        w.writerow([
            "PO Number", "Status", "Project", "Vendor", "Description",
            "Category", "Urgency", "Estimated Amount", "Approved Amount",
            "Receipt Amount", "Requested By", "Requested Role",
            "Submitted", "Approved By", "Approved At",
            "Receipt Filename", "Receipt Uploaded At", "Needed By",
            "Notes",
        ])
        cur = db.po_requests.find(final, {"_id": 0}).sort("created_at", -1)
        async for d in cur:
            w.writerow([
                d.get("po_number") or "",
                d.get("status") or "",
                d.get("project_number") or "",
                d.get("vendor") or "",
                (d.get("description") or "")[:300],
                d.get("category") or "",
                d.get("urgency") or "",
                f"{d.get('estimated_amount') or 0:.2f}",
                (f"{d.get('approved_amount'):.2f}"
                 if d.get("approved_amount") is not None else ""),
                (f"{d.get('receipt_amount'):.2f}"
                 if d.get("receipt_amount") is not None else ""),
                d.get("requested_by_name") or "",
                d.get("requested_by_role") or "",
                _iso(d.get("created_at")),
                (d.get("approved_by") or {}).get("name", ""),
                _iso(d.get("approved_at")),
                d.get("receipt_filename") or "",
                _iso(d.get("receipt_uploaded_at")),
                d.get("needed_by_date") or "",
                (d.get("notes") or "")[:300],
            ])
        buf.seek(0)
        filename = f"masci-po-requests-{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Content-Type-Options": "nosniff",
            },
        )

    @router.get("/api/po-requests/{po_id}")
    async def get_po(po_id: str, request: Request, actor: Dict[str, Any] = Depends(require_any_portal_token)) -> Dict[str, Any]:
        doc = await db.po_requests.find_one({"id": po_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "PO not found")
        await _require_po_action(request, actor, "po_requests.read", doc)
        governed_actor = await _governed_actor(actor)
        if not _po_visible_to_actor(governed_actor, doc):
            raise HTTPException(404, "PO not found")
        return _strip(doc)

    @router.post("/api/po-requests")
    async def create_po(
        request: Request,
        body: PoRequestCreate,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await _require_po_action(request, actor, "po_requests.submit", {"id": "po-create", "project_number": body.project_number, "status": "Submitted"})
        now = datetime.now(timezone.utc)
        po = {
            "id": str(uuid.uuid4()),
            "request_number": await _next_po_request_number(db),
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
            "requested_by_user_id": (await _governed_actor(actor)).get("canonical_user_id") or actor.get("id"),
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

        # Fan-out approval task via Phase A.
        # iter242 — Task ownership stays with "pm" (which covers the
        # assigned PM AND any Co-PMs on the job — both are pm-role users).
        # `cc_roles=["hr"]` pushes a parallel visibility-only notification
        # so HR also sees the approval request in their bell feed.
        # Admin sees everything by virtue of cross-portal visibility.
        priority = "Critical" if body.urgency == "Emergency" else (
            "High" if body.urgency == "Urgent" else "Medium")
        await _fan_out_task(db, po, "approval_needed",
                             priority=priority, assignee_role="pm",
                             cc_roles=["hr"])
        return _strip(po)

    @router.post("/api/po-requests/{po_id}/approve")
    async def approve_po(
        request: Request,
        po_id: str,
        body: PoApprovalAction,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        existing = await db.po_requests.find_one({"id": po_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "PO not found")
        await _require_po_action(request, actor, "po_requests.approve", existing)
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

        # Iter160 · Operational signal — PO state transition with cycle time.
        try:
            from lib.operational_signals import record_signal, elapsed_ms_between  # noqa: PLC0415
            sig_map = {"approve": "po.approve",
                       "reject": "po.reject",
                       "clarify": "po.clarify"}
            sig = sig_map.get(action)
            if sig:
                ems = (elapsed_ms_between(existing.get("created_at"), now)
                       if action == "approve" else None)
                await record_signal(
                    db, signal=sig, module="po.requests",
                    elapsed_ms=ems,
                    dims={"urgency": (existing.get("urgency") or "")[:24]},
                )
        except Exception:
            pass
        return await get_po(po_id, request=request, actor=actor)

    @router.post("/api/po-requests/{po_id}/receipt")
    async def upload_receipt(
        request: Request,
        po_id: str,
        file: UploadFile = File(...),
        receipt_amount: Optional[float] = Form(default=None),
        receipt_notes: Optional[str] = Form(default=None),
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        existing = await db.po_requests.find_one({"id": po_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "PO not found")
        await _require_po_action(request, actor, "po_requests.receipt.upload", existing)
        governed_actor = await _governed_actor(actor)
        if not _po_visible_to_actor(governed_actor, existing) and _actor_role(governed_actor) not in ("pm", "hr", "admin"):
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

        # Track 13.17 · Receipt Received notification (Event 5).
        # Bell-feed parallel notifications to PM + HR roles so they can
        # see the loop close. Visibility-only · no new task created.
        try:
            from routes.tasks_notifications import notification_service  # noqa: PLC0415
            po_after = await db.po_requests.find_one({"id": po_id}, {"_id": 0})
            for cc_role in ("pm", "hr"):
                await notification_service.fanout(db, {
                    "type": "po.receipt_received",
                    "title": f"Receipt received for {po_after.get('po_number') or po_id[:8]}",
                    "message": f"{po_after.get('vendor') or ''} · uploaded by {_actor_name(actor)}",
                    "severity": "Info",
                    "recipient_role": cc_role,
                    "linked_source_module": "po.receipts",
                    "linked_source_record_id": po_id,
                    "linked_project_number": po_after.get("project_number"),
                })
        except Exception as e:  # pragma: no cover
            logger.warning("PO receipt-received notification failed: %s", e)

        # Iter160 · Operational signal — PO receipt cycle (approved → receipt).
        try:
            from lib.operational_signals import record_signal, elapsed_ms_between  # noqa: PLC0415
            ems = elapsed_ms_between(existing.get("approved_at"), now)
            await record_signal(
                db, signal="po.receipt", module="po.requests",
                elapsed_ms=ems,
                dims={"urgency": (existing.get("urgency") or "")[:24]},
            )
        except Exception:
            pass
        return await get_po(po_id, request=request, actor=actor)

    @router.get("/api/po-requests/{po_id}/receipt")
    async def get_receipt(
        request: Request,
        po_id: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ):
        """Iter520 · Phase V.5 · P0-3 — stable receipt download endpoint.

        Always streams the bytes inline with a clean Content-Type and
        Content-Disposition so iPad Safari / desktop browsers render the
        PDF reliably. Replaces the prior "embed the raw URL in an
        <a href>" pattern that produced blank tabs whenever (a) the
        stored URL was a 2MB data URL Safari refuses to navigate to, or
        (b) the stored R2 signed URL had expired.

        Two storage cases:
          • Data URL ("data:<mime>;base64,...") — preview / R2 fallback.
            Parse + stream.
          • Plain URL (R2 signed URL or any https URL) — fetch via httpx
            and re-stream so the client never sees an expired link.

        Permission: any authenticated portal user (matches `require_any_portal_token`
        used on the upload + drawer-read endpoints).
        """
        from fastapi.responses import StreamingResponse  # noqa: PLC0415
        import io  # noqa: PLC0415

        po = await db.po_requests.find_one({"id": po_id}, {"_id": 0})
        if not po:
            raise HTTPException(404, "PO not found")
        await _require_po_action(request, actor, "po_requests.read", po)
        governed_actor = await _governed_actor(actor)
        if not _po_visible_to_actor(governed_actor, po):
            raise HTTPException(404, "PO not found")
        receipt_url = po.get("receipt_url") or ""
        if not receipt_url:
            raise HTTPException(404, "No receipt uploaded for this PO")
        filename = po.get("receipt_filename") or f"po_{po_id}_receipt"

        # Case 1 — data URL ("data:<mime>;base64,<b64>")
        if receipt_url.startswith("data:"):
            import base64  # noqa: PLC0415
            try:
                head, b64 = receipt_url.split(",", 1)
                # head format: "data:<mime>;base64"
                mime = head.split(":", 1)[1].split(";", 1)[0] or "application/octet-stream"
                blob = base64.b64decode(b64)
            except Exception:
                raise HTTPException(500, "Stored receipt is corrupted")
            headers = {
                "Content-Disposition": f'inline; filename="{filename}"',
                "Cache-Control": "private, no-store",
            }
            return StreamingResponse(io.BytesIO(blob), media_type=mime, headers=headers)

        # Case 2 — http(s) URL (R2 signed URL or external). Fetch + re-stream.
        if receipt_url.startswith(("http://", "https://")):
            import httpx  # noqa: PLC0415
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    r = await client.get(receipt_url)
                    if r.status_code != 200:
                        raise HTTPException(502, f"Upstream receipt fetch failed (HTTP {r.status_code})")
                    content_type = r.headers.get("content-type") or "application/octet-stream"
                    body = r.content
            except HTTPException:
                raise
            except Exception as e:
                logger.warning("Receipt upstream fetch failed for po=%s: %s", po_id, e)
                raise HTTPException(502, "Receipt fetch failed — please re-upload")
            headers = {
                "Content-Disposition": f'inline; filename="{filename}"',
                "Cache-Control": "private, no-store",
            }
            return StreamingResponse(io.BytesIO(body), media_type=content_type, headers=headers)

        raise HTTPException(500, "Unrecognized receipt storage format")



    @router.post("/api/po-requests/{po_id}/respond-clarification")
    async def respond_clarification(
        request: Request,
        po_id: str,
        body: PoClarificationResponse,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        """Original requester (or any actor with the same role) responds
        to a clarification request — moves the PO back to Pending
        Approval and appends the response to the audit history.
        Re-fans a new approval task so approvers see it again."""
        existing = await db.po_requests.find_one({"id": po_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "PO not found")
        await _require_po_action(request, actor, "po_requests.submit", existing)
        if existing["status"] != "Clarification Needed":
            raise HTTPException(409,
                "PO is not awaiting clarification")
        # Allow the original requester OR a teammate in the same role
        # (so multiple supervisors can collaborate on a job's POs).
        actor_role = _actor_role(actor)
        actor_id = (await _governed_actor(actor)).get("canonical_user_id") or actor.get("id")
        if not (actor_role == "admin"
                or actor_role == existing.get("requested_by_role")
                or actor_id == existing.get("requested_by_user_id")):
            raise HTTPException(403,
                "Only the requester can respond to clarification")
        now = datetime.now(timezone.utc)
        await db.po_requests.update_one({"id": po_id}, {"$set": {
            "status": "Pending Approval",
            "updated_at": now,
        }})
        await _audit_push(db, po_id, "clarification_response", actor,
                          {"response": body.response})
        # Re-fan an approval task (PM owns, HR receives visibility-only
        # notification — iter242 authority-boundary clarification).
        await _fan_out_task(db, existing, "approval_needed",
                            priority="High", assignee_role="pm",
                            cc_roles=["hr"])
        return await get_po(po_id, request=request, actor=actor)

    @router.post("/api/po-requests/{po_id}/close")
    async def close_po(
        request: Request,
        po_id: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        existing = await db.po_requests.find_one({"id": po_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "PO not found")
        await _require_po_action(request, actor, "po_requests.close", existing)
        now = datetime.now(timezone.utc)
        await db.po_requests.update_one({"id": po_id}, {"$set": {
            "status": "Closed",
            "updated_at": now,
        }})
        await _audit_push(db, po_id, "closed", actor)

        # Iter160 · Operational signal — PO close full lifecycle cycle time.
        try:
            from lib.operational_signals import record_signal, elapsed_ms_between  # noqa: PLC0415
            ems = elapsed_ms_between((existing or {}).get("created_at"), now)
            await record_signal(
                db, signal="po.close", module="po.requests",
                elapsed_ms=ems,
                dims={"urgency": ((existing or {}).get("urgency") or "")[:24]},
            )
        except Exception:
            pass
        return await get_po(po_id, request=request, actor=actor)

    @router.post("/api/po-requests/{po_id}/cancel")
    async def cancel_po(
        request: Request,
        po_id: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        # TRUST-PO-1 · 2026-05-28 — auth gate. Cancellation is an
        # approver action (it terminates the workflow); Field Leadership
        # must NOT be able to cancel. The original implementation was
        # missing this check — a real backend authority leak.
        existing = await db.po_requests.find_one({"id": po_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "PO not found")
        await _require_po_action(request, actor, "po_requests.cancel", existing)
        await db.po_requests.update_one({"id": po_id}, {"$set": {
            "status": "Cancelled",
            "updated_at": datetime.now(timezone.utc),
        }})
        await _audit_push(db, po_id, "cancelled", actor)

        # Iter160 · Operational signal — PO cancel.
        try:
            from lib.operational_signals import record_signal  # noqa: PLC0415
            await record_signal(
                db, signal="po.cancel", module="po.requests",
                dims={},
            )
        except Exception:
            pass
        return await get_po(po_id, request=request, actor=actor)

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

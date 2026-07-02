"""Track 19.21 · Employee Records Intelligence Platform · P0 Foundation.

Universal Employee Record + Historical Records Intake foundation.

Doctrine:
  * HR is the system owner. HR sees + edits + reassigns + approves every
    lane.
  * Safety owns the Safety lane operationally.
  * Asset Administrator owns the Asset lane operationally.
  * `db.employees` remains the single source of truth for employee
    identity. Records reference employees by `employee_id`; they do not
    duplicate employee attributes.
  * Original uploaded files are IMMUTABLE. Every mutation writes an audit
    row to `db.employee_record_audit`.
  * Nothing is auto-linked. Every record requires manual approval before
    it becomes an active lifecycle record on Employee 360°.

Collections (all NEW · additive · zero drift):
  * db.employee_records        — universal employee record model
  * db.employee_record_audit   — append-only audit ledger
  * db.record_import_batches   — bulk intake batches

Routes (all mounted under /api/employee-records):
  * POST /batches                       — create intake batch
  * GET  /batches                       — list my batches
  * POST /records                       — create a record (pending states)
  * GET  /records                       — list / filter records
  * GET  /records/{id}                  — record detail incl. audit
  * POST /records/{id}/approve          — HR / lane-owner approval
  * POST /records/{id}/reject           — HR / lane-owner rejection
  * POST /records/{id}/reassign         — change employee / category
  * GET  /queues/{lane}                 — HR / Safety / Asset queues
  * GET  /employees/{emp_id}/records    — records for an employee (approved)

Zero-drift verified:
  * No existing schemas modified.
  * No existing routes modified.
  * `db.employees` is READ-ONLY from this module.
  * Failure to create audit does NOT block user-visible operation but is
    reported to logs — audit collection is best-effort append-only.
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


def make_employee_records_actor_gate(db, is_valid_admin_token):
    """Auth gate for Track 19.21 Employee Records surface.

    Accepts, in order of precedence:
      * X-HR-Token       → HR (system owner)
      * X-Safety-Token   → Safety (owns Safety lane operationally)
      * X-Shop-Token     → Asset Administrator (if `is_asset_admin` flag)
      * X-Admin-Token    → Admin (super-admin bypass)

    Returns a dict `{..., "_actor": role, "email": ..., "name": ...}`
    or raises 401. HR / Safety / Asset admin dicts carry lane semantics;
    admin gets `{"_actor": "admin"}`.
    """
    async def _gate(
        request: Request,
        x_hr_token: str | None = Header(default=None, alias="X-HR-Token"),
        x_safety_token: str | None = Header(default=None, alias="X-Safety-Token"),
        x_shop_token: str | None = Header(default=None, alias="X-Shop-Token"),
        x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    ):
        # HR — system owner.
        if x_hr_token:
            from hr_users import is_valid_hr_user_token_async  # noqa: PLC0415
            u = await is_valid_hr_user_token_async(db, x_hr_token)
            if u:
                return {**u, "_actor": "hr"}
        # Safety.
        if x_safety_token:
            from routes.safety_portal._deps import is_valid_safety_user_token_async  # noqa: PLC0415
            u = await is_valid_safety_user_token_async(db, x_safety_token)
            if u:
                return {**u, "_actor": "safety"}
        # Asset Administrator (Shop portal with `is_asset_admin` flag).
        if x_shop_token:
            from shop_users import is_valid_shop_user_token_async  # noqa: PLC0415
            u = await is_valid_shop_user_token_async(db, x_shop_token)
            if u and (u.get("is_asset_admin") or "asset_admin" in [str(r).lower() for r in (u.get("roles") or [])]):
                return {**u, "_actor": "asset_admin"}
        # Admin (super-admin bypass; behaves as HR-equivalent for records).
        if x_admin_token and is_valid_admin_token and is_valid_admin_token(x_admin_token):
            return {"_actor": "admin", "name": "Admin"}
        raise HTTPException(401, "HR, Safety, Asset Administrator, or Admin auth required")

    return _gate


# ── Doctrine · valid lanes / record types / states ──────────────────
OWNERSHIP_LANES = ("hr", "safety", "asset", "corporate_import")

RECORD_STATES = (
    "pending_classification",
    "pending_match",
    "pending_approval",
    "linked",
    "rejected",
)

# HR is a system-owner role that can touch every lane. Safety/Asset are
# lane-scoped. This dict maps ownership_lane → set of roles that can
# APPROVE records in that lane. HR is in every set by design.
LANE_APPROVERS: Dict[str, set] = {
    "hr":               {"hr", "admin"},
    "safety":           {"safety", "hr", "admin"},
    "asset":            {"asset_admin", "hr", "admin"},
    "corporate_import": {"hr", "admin"},
}

# Whitelisted record_type slugs per lane. Additive — new types may be
# appended safely.
LANE_RECORD_TYPES: Dict[str, List[str]] = {
    "hr": [
        "write_up", "verbal_coaching", "attendance", "recognition",
        "promotion", "termination", "employee_acknowledgement",
        "hr_document", "personnel_document", "performance_document",
        "general_employee_document",
    ],
    "safety": [
        "incident_report", "safety_case", "near_miss", "accident",
        "training_record", "certificate", "safety_meeting_attendance",
        "toolbox_attendance", "corrective_action",
        "safety_acknowledgement", "safety_document",
    ],
    "asset": [
        "ppe_issued", "ppe_returned", "tool_issued", "tool_returned",
        "phone_issued", "tablet_issued", "ipad_issued",
        "survey_equipment_issued", "pipe_laser_issued",
        "rotating_laser_issued", "asset_acknowledgement",
        "damaged_asset", "lost_asset", "replacement_record",
    ],
    "corporate_import": [
        "historical_archive", "acquisition_records", "legacy_conversion",
        "bulk_hr_archive", "unknown_mixed_records",
    ],
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ── Models ──────────────────────────────────────────────────────────
class CreateBatchBody(BaseModel):
    model_config = ConfigDict(extra="allow")
    ownership_lane: str
    label: str = ""
    notes: str = ""


class CreateRecordBody(BaseModel):
    model_config = ConfigDict(extra="allow")
    ownership_lane: str
    record_type: str
    employee_id: Optional[str] = None
    employee_name_snapshot: Optional[str] = None
    record_category: Optional[str] = None
    effective_date: Optional[str] = None
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    related_incident_case_id: Optional[str] = None
    related_training_id: Optional[str] = None
    related_asset_id: Optional[str] = None
    related_project_id: Optional[str] = None
    related_supervisor_id: Optional[str] = None
    source_file_ref: Optional[str] = None
    source_file_name: Optional[str] = None
    source_file_hash: Optional[str] = None
    imported_batch_id: Optional[str] = None


class ApproveBody(BaseModel):
    notes: str = ""


class RejectBody(BaseModel):
    reason: str


class ReassignBody(BaseModel):
    employee_id: Optional[str] = None
    record_type: Optional[str] = None
    ownership_lane: Optional[str] = None
    notes: str = ""


# ── Helpers ─────────────────────────────────────────────────────────
def _actor_role(actor: Dict[str, Any]) -> str:
    return (actor.get("_actor") or actor.get("role") or "").lower()


def _actor_can_approve(actor: Dict[str, Any], lane: str) -> bool:
    role = _actor_role(actor)
    approvers = LANE_APPROVERS.get(lane, set())
    return role in approvers


def _actor_can_read_lane(actor: Dict[str, Any], lane: str) -> bool:
    role = _actor_role(actor)
    # HR + admin can read every lane.
    if role in {"hr", "admin"}:
        return True
    # Safety can read Safety lane.
    if role == "safety" and lane == "safety":
        return True
    # Asset Administrator can read Asset lane.
    if role == "asset_admin" and lane == "asset":
        return True
    return False


def _validate_lane_and_type(lane: str, record_type: Optional[str]) -> None:
    if lane not in OWNERSHIP_LANES:
        raise HTTPException(400, f"Invalid ownership_lane: {lane}")
    if record_type is None:
        return
    if record_type not in LANE_RECORD_TYPES.get(lane, []):
        raise HTTPException(
            400,
            f"record_type {record_type!r} not permitted in lane {lane!r}",
        )


async def _write_audit(db, *, record_id: str, event: str, actor: Dict[str, Any],
                       details: Optional[Dict[str, Any]] = None) -> None:
    try:
        await db.employee_record_audit.insert_one({
            "id": str(uuid.uuid4()),
            "record_id": record_id,
            "event": event,
            "actor_email": actor.get("email") or actor.get("name"),
            "actor_role": _actor_role(actor),
            "details": details or {},
            "ts": _now_iso(),
        })
    except Exception as exc:  # audit is best-effort append-only
        logger.warning("[employee_records] audit write failed: %s", exc)


# ── Router builder ──────────────────────────────────────────────────
def build_employee_records_router(*, db, require_actor):
    """Attach the Track 19.21 Employee Records router.

    `require_actor` is the shared FastAPI dependency that returns the
    authenticated actor dict with `_actor` (role) + `email` + `name`.
    HR / Safety / Admin / Asset Administrator are all supported roles.
    """
    router = APIRouter(prefix="/api/employee-records", tags=["employee-records"])

    def _actor_dep():
        return Depends(require_actor)

    # ── Vocabulary (public within the router) ─────────────────────
    # Exposes lanes + valid record_types + approver matrix to the
    # frontend. Read-only. Requires any authenticated actor.
    @router.get("/vocabulary")
    async def vocabulary(actor: Dict[str, Any] = _actor_dep()):
        role = _actor_role(actor)
        allowed_lanes = []
        for lane in OWNERSHIP_LANES:
            if _actor_can_read_lane(actor, lane):
                allowed_lanes.append(lane)
        return {
            "ok": True,
            "actor_role": role,
            "ownership_lanes": list(OWNERSHIP_LANES),
            "record_states": list(RECORD_STATES),
            "record_types_by_lane": LANE_RECORD_TYPES,
            "lane_approvers": {k: sorted(list(v)) for k, v in LANE_APPROVERS.items()},
            "allowed_lanes_for_actor": allowed_lanes,
        }

    # ── Intake batches ────────────────────────────────────────────
    @router.post("/batches")
    async def create_batch(
        body: CreateBatchBody,
        actor: Dict[str, Any] = _actor_dep(),
    ):
        if not _actor_can_read_lane(actor, body.ownership_lane):
            raise HTTPException(403, "Not authorized for this lane")
        _validate_lane_and_type(body.ownership_lane, None)
        batch = {
            "id": str(uuid.uuid4()),
            "ownership_lane": body.ownership_lane,
            "label": body.label or f"Batch {_now_iso()[:19]}",
            "notes": body.notes,
            "created_by": actor.get("email") or actor.get("name"),
            "created_by_role": _actor_role(actor),
            "created_at": _now_iso(),
            "file_count": 0,
            "record_count": 0,
            "status": "open",  # open → closed by an admin action
        }
        await db.record_import_batches.insert_one(batch)
        batch.pop("_id", None)
        return {"ok": True, "batch": batch}

    @router.get("/batches")
    async def list_batches(
        lane: Optional[str] = Query(None),
        actor: Dict[str, Any] = _actor_dep(),
    ):
        q: Dict[str, Any] = {}
        if lane:
            if not _actor_can_read_lane(actor, lane):
                raise HTTPException(403, "Not authorized for this lane")
            q["ownership_lane"] = lane
        elif _actor_role(actor) not in {"hr", "admin"}:
            # Non-HR sees only lanes they own.
            role = _actor_role(actor)
            own_lane = {"safety": "safety", "asset_admin": "asset"}.get(role)
            if not own_lane:
                raise HTTPException(403, "Not authorized")
            q["ownership_lane"] = own_lane
        items: List[Dict[str, Any]] = []
        async for b in db.record_import_batches.find(q, {"_id": 0}).sort("created_at", -1).limit(200):
            items.append(b)
        return {"ok": True, "batches": items}

    # ── Records ───────────────────────────────────────────────────
    @router.post("/records")
    async def create_record(
        body: CreateRecordBody,
        actor: Dict[str, Any] = _actor_dep(),
    ):
        if not _actor_can_read_lane(actor, body.ownership_lane):
            raise HTTPException(403, "Not authorized for this lane")
        _validate_lane_and_type(body.ownership_lane, body.record_type)

        # Determine initial state based on what the caller supplied.
        if not body.employee_id:
            state = "pending_match"
        elif not body.record_type:
            state = "pending_classification"
        else:
            state = "pending_approval"

        # Employee name snapshot — resolved once, at record creation, so
        # historical rename doesn't drift the audit trail.
        name_snapshot = body.employee_name_snapshot
        if body.employee_id and not name_snapshot:
            emp = await db.employees.find_one(
                {"$or": [{"id": body.employee_id}, {"employee_id": body.employee_id}]},
                {"_id": 0, "name": 1},
            )
            name_snapshot = (emp or {}).get("name") or ""

        rec = {
            "id": str(uuid.uuid4()),
            "employee_id": body.employee_id,
            "employee_name_snapshot": name_snapshot,
            "record_type": body.record_type,
            "record_category": body.record_category,
            "ownership_lane": body.ownership_lane,
            "owning_department": body.ownership_lane,
            "created_by": actor.get("email") or actor.get("name"),
            "created_by_role": _actor_role(actor),
            "reviewed_by": None,
            "approved_by": None,
            "approval_status": state,
            "effective_date": body.effective_date,
            "source_type": "upload" if body.source_file_ref else "manual_entry",
            "source_file_ref": body.source_file_ref,
            "source_file_name": body.source_file_name,
            "source_file_hash": body.source_file_hash,
            "imported_batch_id": body.imported_batch_id,
            "related_incident_case_id": body.related_incident_case_id,
            "related_training_id": body.related_training_id,
            "related_asset_id": body.related_asset_id,
            "related_project_id": body.related_project_id,
            "related_supervisor_id": body.related_supervisor_id,
            "tags": body.tags or [],
            "notes": body.notes or "",
            "status": state,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        await db.employee_records.insert_one(rec)
        rec.pop("_id", None)
        await _write_audit(
            db, record_id=rec["id"], event="record_created", actor=actor,
            details={"state": state, "ownership_lane": body.ownership_lane},
        )
        if body.imported_batch_id:
            await db.record_import_batches.update_one(
                {"id": body.imported_batch_id},
                {"$inc": {"record_count": 1}},
            )
        return {"ok": True, "record": rec}

    @router.get("/records")
    async def list_records(
        lane: Optional[str] = Query(None),
        state: Optional[str] = Query(None),
        record_type: Optional[str] = Query(None),
        employee_id: Optional[str] = Query(None),
        batch_id: Optional[str] = Query(None),
        limit: int = Query(200, ge=1, le=500),
        actor: Dict[str, Any] = _actor_dep(),
    ):
        q: Dict[str, Any] = {}
        # Lane scoping — enforce for non-HR.
        role = _actor_role(actor)
        if role not in {"hr", "admin"}:
            own_lane = {"safety": "safety", "asset_admin": "asset"}.get(role)
            if not own_lane:
                raise HTTPException(403, "Not authorized")
            if lane and lane != own_lane:
                raise HTTPException(403, "Not authorized for this lane")
            q["ownership_lane"] = own_lane
        elif lane:
            q["ownership_lane"] = lane
        if state:
            q["approval_status"] = state
        if record_type:
            q["record_type"] = record_type
        if employee_id:
            q["employee_id"] = employee_id
        if batch_id:
            q["imported_batch_id"] = batch_id
        items: List[Dict[str, Any]] = []
        async for r in db.employee_records.find(q, {"_id": 0}).sort("created_at", -1).limit(limit):
            items.append(r)
        return {"ok": True, "records": items, "count": len(items)}

    @router.get("/records/{record_id}")
    async def get_record(
        record_id: str,
        actor: Dict[str, Any] = _actor_dep(),
    ):
        rec = await db.employee_records.find_one({"id": record_id}, {"_id": 0})
        if not rec:
            raise HTTPException(404, "Record not found")
        if not _actor_can_read_lane(actor, rec.get("ownership_lane") or ""):
            raise HTTPException(403, "Not authorized for this lane")
        # Attach audit trail (last 200 events).
        audit: List[Dict[str, Any]] = []
        async for a in db.employee_record_audit.find(
            {"record_id": record_id}, {"_id": 0}
        ).sort("ts", -1).limit(200):
            audit.append(a)
        return {"ok": True, "record": rec, "audit": audit}

    @router.post("/records/{record_id}/approve")
    async def approve_record(
        record_id: str,
        body: ApproveBody = Body(default_factory=ApproveBody),
        actor: Dict[str, Any] = _actor_dep(),
    ):
        rec = await db.employee_records.find_one({"id": record_id}, {"_id": 0})
        if not rec:
            raise HTTPException(404, "Record not found")
        lane = rec.get("ownership_lane") or ""
        if not _actor_can_approve(actor, lane):
            raise HTTPException(403, "Not authorized to approve in this lane")
        if not rec.get("employee_id"):
            raise HTTPException(400, "Cannot approve — employee_id is required")
        if not rec.get("record_type"):
            raise HTTPException(400, "Cannot approve — record_type is required")
        now = _now_iso()
        await db.employee_records.update_one(
            {"id": record_id},
            {"$set": {
                "approval_status": "linked",
                "status": "linked",
                "approved_by": actor.get("email") or actor.get("name"),
                "approved_by_role": _actor_role(actor),
                "approved_at": now,
                "updated_at": now,
            }},
        )
        await _write_audit(
            db, record_id=record_id, event="record_approved", actor=actor,
            details={"notes": body.notes},
        )
        return {"ok": True, "record_id": record_id, "state": "linked"}

    @router.post("/records/{record_id}/reject")
    async def reject_record(
        record_id: str,
        body: RejectBody,
        actor: Dict[str, Any] = _actor_dep(),
    ):
        rec = await db.employee_records.find_one({"id": record_id}, {"_id": 0})
        if not rec:
            raise HTTPException(404, "Record not found")
        lane = rec.get("ownership_lane") or ""
        if not _actor_can_approve(actor, lane):
            raise HTTPException(403, "Not authorized to reject in this lane")
        now = _now_iso()
        await db.employee_records.update_one(
            {"id": record_id},
            {"$set": {
                "approval_status": "rejected",
                "status": "rejected",
                "rejected_by": actor.get("email") or actor.get("name"),
                "rejected_at": now,
                "rejection_reason": body.reason,
                "updated_at": now,
            }},
        )
        await _write_audit(
            db, record_id=record_id, event="record_rejected", actor=actor,
            details={"reason": body.reason},
        )
        return {"ok": True, "record_id": record_id, "state": "rejected"}

    @router.post("/records/{record_id}/reassign")
    async def reassign_record(
        record_id: str,
        body: ReassignBody,
        actor: Dict[str, Any] = _actor_dep(),
    ):
        rec = await db.employee_records.find_one({"id": record_id}, {"_id": 0})
        if not rec:
            raise HTTPException(404, "Record not found")
        # HR may reassign across lanes; lane owners may reassign within.
        target_lane = body.ownership_lane or rec.get("ownership_lane") or ""
        if not (_actor_can_approve(actor, target_lane)
                and _actor_can_approve(actor, rec.get("ownership_lane") or "")):
            raise HTTPException(403, "Not authorized to reassign")
        if body.record_type is not None:
            _validate_lane_and_type(target_lane, body.record_type)

        patch: Dict[str, Any] = {"updated_at": _now_iso()}
        if body.employee_id is not None:
            patch["employee_id"] = body.employee_id
            emp = await db.employees.find_one(
                {"$or": [{"id": body.employee_id}, {"employee_id": body.employee_id}]},
                {"_id": 0, "name": 1},
            )
            patch["employee_name_snapshot"] = (emp or {}).get("name") or ""
        if body.record_type is not None:
            patch["record_type"] = body.record_type
        if body.ownership_lane is not None:
            patch["ownership_lane"] = body.ownership_lane
            patch["owning_department"] = body.ownership_lane

        # Reassignment resets approval — records must be re-approved.
        if rec.get("approval_status") == "linked":
            patch["approval_status"] = "pending_approval"
            patch["status"] = "pending_approval"

        await db.employee_records.update_one({"id": record_id}, {"$set": patch})
        await _write_audit(
            db, record_id=record_id, event="record_reassigned", actor=actor,
            details={"patch": {k: v for k, v in patch.items() if k != "updated_at"},
                     "notes": body.notes},
        )
        return {"ok": True, "record_id": record_id, "patch": patch}

    # ── Queues ────────────────────────────────────────────────────
    @router.get("/queues/{lane}")
    async def get_queue(
        lane: str,
        actor: Dict[str, Any] = _actor_dep(),
    ):
        if lane not in OWNERSHIP_LANES:
            raise HTTPException(400, f"Invalid lane {lane!r}")
        if not _actor_can_read_lane(actor, lane):
            raise HTTPException(403, "Not authorized for this lane")
        # Queue = anything not yet linked/rejected.
        q = {
            "ownership_lane": lane,
            "approval_status": {"$in": [
                "pending_classification", "pending_match", "pending_approval",
            ]},
        }
        items: List[Dict[str, Any]] = []
        async for r in db.employee_records.find(q, {"_id": 0}).sort("created_at", -1).limit(500):
            items.append(r)
        return {
            "ok": True,
            "lane": lane,
            "count": len(items),
            "records": items,
        }

    # ── Employee-scoped roll-up (records approved for a given employee) ──
    @router.get("/employees/{emp_id}/records")
    async def employee_records(
        emp_id: str,
        include_pending: bool = Query(False),
        lane: Optional[str] = Query(None),
        record_type: Optional[str] = Query(None),
        actor: Dict[str, Any] = _actor_dep(),
    ):
        # HR + admin can read everything for the employee. Lane owners
        # only get their lane. This endpoint is what powers Employee 360°
        # for the "Documents / Historical Records" tab.
        role = _actor_role(actor)
        if role not in {"hr", "admin"}:
            own_lane = {"safety": "safety", "asset_admin": "asset"}.get(role)
            if not own_lane:
                raise HTTPException(403, "Not authorized")
            if lane and lane != own_lane:
                raise HTTPException(403, "Not authorized for this lane")
            lane = own_lane
        q: Dict[str, Any] = {"employee_id": emp_id}
        if not include_pending:
            q["approval_status"] = "linked"
        if lane:
            q["ownership_lane"] = lane
        if record_type:
            q["record_type"] = record_type
        items: List[Dict[str, Any]] = []
        async for r in db.employee_records.find(q, {"_id": 0}).sort("effective_date", -1).limit(500):
            items.append(r)
        return {"ok": True, "records": items, "count": len(items)}

    # ── File preservation (immutable) ─────────────────────────────
    # Upload original file → R2 (or base64 fallback). Returns:
    #   {source_file_ref, source_file_name, source_file_hash, size_bytes}
    # The record itself is created afterwards via POST /records with
    # those fields — the two operations are decoupled so callers can
    # attach one file to N records if needed.
    ALLOWED_EXTS = {
        "pdf", "png", "jpg", "jpeg", "webp", "gif", "heic", "heif",
        "doc", "docx", "xls", "xlsx", "xlsm", "csv", "txt", "rtf",
    }
    MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB

    @router.post("/uploads")
    async def upload_original_file(
        lane: str = Form(...),
        file: UploadFile = File(...),
        actor: Dict[str, Any] = _actor_dep(),
    ):
        if not _actor_can_read_lane(actor, lane):
            raise HTTPException(403, "Not authorized for this lane")
        _validate_lane_and_type(lane, None)
        raw = await file.read()
        if len(raw) == 0:
            raise HTTPException(400, "Empty file")
        if len(raw) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, f"File exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit")
        # Extension gate — no exotic types on the intake surface.
        name = file.filename or "upload.bin"
        ext = (name.rsplit(".", 1)[-1] if "." in name else "").lower()
        if ext not in ALLOWED_EXTS:
            raise HTTPException(400, f"Unsupported file type: .{ext}")
        digest = _sha256(raw)
        # Try cloud storage; fall back to base64 embed (dev/test).
        ref = None
        try:
            from photo_storage import upload_photo_bytes, is_configured  # noqa: PLC0415
            if is_configured():
                ref = await upload_photo_bytes(
                    raw, ext=ext, source_id=f"emp-rec/{lane}/{digest[:12]}",
                    content_type=file.content_type or "application/octet-stream",
                )
        except Exception as exc:
            logger.warning("[employee_records] cloud upload failed, fallback: %s", exc)
        if not ref:
            import base64
            b64 = base64.b64encode(raw).decode("ascii")
            ct = file.content_type or "application/octet-stream"
            ref = f"data:{ct};base64,{b64}"
        return {
            "ok": True,
            "source_file_ref": ref,
            "source_file_name": name,
            "source_file_hash": digest,
            "content_type": file.content_type,
            "size_bytes": len(raw),
        }

    @router.get("/records/{record_id}/file")
    async def download_record_file(
        record_id: str,
        actor: Dict[str, Any] = _actor_dep(),
    ):
        rec = await db.employee_records.find_one({"id": record_id}, {"_id": 0})
        if not rec:
            raise HTTPException(404, "Record not found")
        if not _actor_can_read_lane(actor, rec.get("ownership_lane") or ""):
            raise HTTPException(403, "Not authorized for this lane")
        ref = rec.get("source_file_ref")
        if not ref:
            raise HTTPException(404, "No file attached")
        # Cloud storage → presigned URL redirect.
        if ref.startswith("photo://"):
            try:
                from photo_storage import presigned_get_url  # noqa: PLC0415
                url = await presigned_get_url(ref, ttl_seconds=900)
                return RedirectResponse(url=url, status_code=302)
            except Exception as exc:
                logger.warning("[employee_records] presign failed: %s", exc)
                raise HTTPException(500, "File temporarily unavailable")
        # Base64 fallback → return raw JSON with the data URL.
        return {"ok": True, "source_file_ref": ref,
                "source_file_name": rec.get("source_file_name")}

    return router


async def ensure_employee_records_indexes(db) -> None:
    """Idempotent index creation. Called at app startup."""
    try:
        await db.employee_records.create_index([("employee_id", 1), ("approval_status", 1)])
        await db.employee_records.create_index([("ownership_lane", 1), ("approval_status", 1)])
        await db.employee_records.create_index([("record_type", 1)])
        await db.employee_records.create_index([("imported_batch_id", 1)])
        await db.employee_records.create_index([("created_at", -1)])
        await db.employee_record_audit.create_index([("record_id", 1), ("ts", -1)])
        await db.record_import_batches.create_index([("ownership_lane", 1), ("created_at", -1)])
    except Exception as exc:
        logger.warning("[employee_records] index create failed: %s", exc)

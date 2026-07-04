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
# Track 19.59: `vendor` added as a fourth first-class ownership lane.
# Backwards-compatible — every existing record continues to sit in one
# of the original four lanes and continues to behave identically.
OWNERSHIP_LANES = ("hr", "safety", "asset", "corporate_import", "vendor")

# Track 19.59: canonical entity discriminator. Records without this
# field are treated as `"employee"` for backwards compatibility.
# Track 19.61: `asset` added as a third entity_kind so Historical
# Records can hold legacy paper about the physical asset itself
# (warranties, purchase agreements, calibration certificates,
# manuals, etc.) alongside the employee-issued equipment records
# that already live in the `asset` lane.
ENTITY_KINDS = ("employee", "vendor", "asset")
DEFAULT_ENTITY_KIND = "employee"

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
    # Track 19.59 · Vendor lane approvers.
    "vendor":           {"hr", "admin"},
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
        # Track 19.61 · legacy paper about the physical asset itself
        # (entity_kind="asset"). Additive; existing employee-issuance
        # types above remain valid for entity_kind="employee".
        "warranty",
        "purchase_agreement",
        "bill_of_sale",
        "title_registration",
        "insurance_policy",
        "calibration_certificate",
        "operator_manual",
        "spec_sheet",
        "historical_inspection_report",
        "historical_maintenance_record",
        "asset_photo",
        "other_asset_document",
        # Track 19.62 · Phase A — fire-protection-specific paper.
        "hydrostatic_test_certificate",
        "recharge_service_record",
        "fire_ext_annual_service",
        "fire_ext_manufacturer_doc",
        "fire_ext_retirement_record",
    ],
    "corporate_import": [
        "historical_archive", "acquisition_records", "legacy_conversion",
        "bulk_hr_archive", "unknown_mixed_records",
    ],
    # Track 19.59 · Vendor document catalog. Human-readable slugs, no
    # legal conclusions, no compliance-ready wording, no OSHA-ready
    # wording. Additive — new types may be appended safely.
    "vendor": [
        "w9",
        "certificate_of_insurance",
        "contract_agreement",
        "subcontract",
        "rental_agreement",
        "service_agreement",
        "business_license",
        "prequalification",
        "vendor_packet",
        "quote_proposal",
        "pricing_sheet",
        "safety_document",
        "material_certification",
        "correspondence",
        "other_vendor_document",
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
    # Track 19.25 · Intake Session provenance (all optional, all inherited
    # onto records so operators do not re-type provenance per file).
    source_name: Optional[str] = None        # e.g. "2019 HR File Cabinet"
    source_type: Optional[str] = None        # e.g. "cabinet · binder · box · folder · digital"
    source_location: Optional[str] = None    # e.g. "University High School · trailer"
    # Track 19.59 · Entity discriminator. Missing → "employee".
    entity_kind: Optional[str] = None


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
    # Track 19.59 · Vendor-lane fields. Only meaningful when
    # `ownership_lane == "vendor"` (or `entity_kind == "vendor"`).
    entity_kind: Optional[str] = None
    vendor_id: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_display_name: Optional[str] = None
    # Track 19.61 · Asset-entity fields. Only meaningful when
    # `entity_kind == "asset"` (physical asset paper — warranties,
    # purchase agreements, calibration certs, manuals). Existing
    # `related_asset_id` remains the cross-lane pointer; these fields
    # are the snapshot identity used when the asset appears as the
    # SUBJECT of the record rather than a related entity.
    asset_id: Optional[str] = None
    asset_unit_number: Optional[str] = None
    asset_display_name: Optional[str] = None


class ApproveBody(BaseModel):
    notes: str = ""


class RejectBody(BaseModel):
    reason: str


class ReassignBody(BaseModel):
    employee_id: Optional[str] = None
    record_type: Optional[str] = None
    ownership_lane: Optional[str] = None
    notes: str = ""


class BulkApplyBody(BaseModel):
    model_config = ConfigDict(extra="allow")
    record_type: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name_snapshot: Optional[str] = None
    effective_date: Optional[str] = None
    tags: Optional[List[str]] = None
    only_unclassified: bool = True


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
            # Track 19.59 · entity discriminator vocabulary.
            "entity_kinds": list(ENTITY_KINDS),
            "default_entity_kind": DEFAULT_ENTITY_KIND,
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
            # Track 19.25 · Intake Session provenance.
            "source_name": body.source_name or "",
            "source_type": body.source_type or "",
            "source_location": body.source_location or "",
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

        # Track 19.59 · resolve canonical entity_kind. `vendor` ownership
        # lane implies vendor entity_kind; missing entity_kind defaults
        # to employee (backwards-compatible).
        # Track 19.61 · `asset` entity_kind (physical asset paper) is
        # accepted only in the `asset` ownership lane. Missing
        # entity_kind inside the asset lane continues to default to
        # `employee` so the existing PPE / tool / phone issuance flows
        # remain byte-identical.
        if body.ownership_lane == "vendor":
            entity_kind = "vendor"
        elif body.entity_kind in ENTITY_KINDS:
            entity_kind = body.entity_kind
        else:
            entity_kind = DEFAULT_ENTITY_KIND
        # Cross-lane consistency guard — never allow entity_kind=vendor
        # inside a non-vendor lane (protects employee lanes).
        if entity_kind == "vendor" and body.ownership_lane != "vendor":
            raise HTTPException(
                400, "entity_kind='vendor' is only permitted in the 'vendor' lane"
            )
        if entity_kind == "employee" and body.ownership_lane == "vendor":
            raise HTTPException(
                400, "'vendor' lane requires entity_kind='vendor'"
            )
        # Track 19.61 · asset entity_kind guards.
        if entity_kind == "asset" and body.ownership_lane != "asset":
            raise HTTPException(
                400, "entity_kind='asset' is only permitted in the 'asset' lane"
            )

        # Determine initial state.
        if entity_kind == "vendor":
            vendor_ident = (body.vendor_id or body.vendor_name or "").strip()
            if not vendor_ident:
                state = "pending_match"
            elif not body.record_type:
                state = "pending_classification"
            else:
                state = "pending_approval"
        elif entity_kind == "asset":
            asset_ident = (
                body.asset_id or body.asset_unit_number or body.related_asset_id or ""
            ).strip()
            if not asset_ident:
                state = "pending_match"
            elif not body.record_type:
                state = "pending_classification"
            else:
                state = "pending_approval"
        else:
            if not body.employee_id:
                state = "pending_match"
            elif not body.record_type:
                state = "pending_classification"
            else:
                state = "pending_approval"

        # Employee name snapshot — vendor path leaves this null.
        name_snapshot = body.employee_name_snapshot
        if entity_kind == "employee" and body.employee_id and not name_snapshot:
            emp = await db.employees.find_one(
                {"$or": [{"id": body.employee_id}, {"employee_id": body.employee_id}]},
                {"_id": 0, "name": 1},
            )
            name_snapshot = (emp or {}).get("name") or ""

        rec = {
            "id": str(uuid.uuid4()),
            # Track 19.59 · canonical entity discriminator.
            "entity_kind": entity_kind,
            "employee_id": body.employee_id if entity_kind == "employee" else None,
            "employee_name_snapshot": name_snapshot if entity_kind == "employee" else None,
            # Track 19.59 · vendor identity fields (null for employee records).
            "vendor_id": (body.vendor_id or None) if entity_kind == "vendor" else None,
            "vendor_name": (body.vendor_name or None) if entity_kind == "vendor" else None,
            "vendor_display_name": (body.vendor_display_name or None) if entity_kind == "vendor" else None,
            # Track 19.61 · asset identity snapshot (null for non-asset records).
            "asset_id": (body.asset_id or None) if entity_kind == "asset" else None,
            "asset_unit_number": (body.asset_unit_number or None) if entity_kind == "asset" else None,
            "asset_display_name": (body.asset_display_name or None) if entity_kind == "asset" else None,
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
            details={
                "state": state,
                "ownership_lane": body.ownership_lane,
                "entity_kind": entity_kind,
                # Vendor identity kept in audit for traceability.
                "vendor_id": rec.get("vendor_id"),
                "vendor_name": rec.get("vendor_name"),
                # Track 19.61 · asset identity in audit for traceability.
                "asset_id": rec.get("asset_id"),
                "asset_unit_number": rec.get("asset_unit_number"),
            },
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
        # Track 19.59 · vendor filter parameters.
        entity_kind: Optional[str] = Query(None, description="employee | vendor | asset"),
        vendor_id: Optional[str] = Query(None),
        vendor_name: Optional[str] = Query(None),
        # Track 19.61 · asset-entity filter parameters.
        asset_id: Optional[str] = Query(None),
        asset_unit_number: Optional[str] = Query(None),
        # Track 19.22 · P1 · structured search filters (no OCR).
        q: Optional[str] = Query(None, description="Substring on record_type/notes/tags/employee_name_snapshot/source_file_name"),
        department: Optional[str] = Query(None),
        uploader_email: Optional[str] = Query(None),
        reviewer_email: Optional[str] = Query(None),
        tag: Optional[str] = Query(None),
        date_from: Optional[str] = Query(None),
        date_to: Optional[str] = Query(None),
        related_asset_id: Optional[str] = Query(None),
        related_incident_case_id: Optional[str] = Query(None),
        related_project_id: Optional[str] = Query(None),
        related_training_id: Optional[str] = Query(None),
        limit: int = Query(200, ge=1, le=500),
        actor: Dict[str, Any] = _actor_dep(),
    ):
        q_mongo: Dict[str, Any] = {}
        # Lane scoping — enforce for non-HR.
        role = _actor_role(actor)
        if role not in {"hr", "admin"}:
            own_lane = {"safety": "safety", "asset_admin": "asset"}.get(role)
            if not own_lane:
                raise HTTPException(403, "Not authorized")
            if lane and lane != own_lane:
                raise HTTPException(403, "Not authorized for this lane")
            q_mongo["ownership_lane"] = own_lane
        elif lane:
            q_mongo["ownership_lane"] = lane
        if state:
            q_mongo["approval_status"] = state
        if record_type:
            q_mongo["record_type"] = record_type
        if employee_id:
            q_mongo["employee_id"] = employee_id
        # Track 19.59 · entity discriminator. Absent / "employee" → filter
        # to employee records (safety sentinel — vendor records NEVER
        # surface in employee views unless explicitly requested).
        # Track 19.61 · `entity_kind=asset` is respected the same way —
        # asset records never surface in employee views unless requested.
        if entity_kind == "vendor":
            q_mongo["entity_kind"] = "vendor"
        elif entity_kind == "asset":
            q_mongo["entity_kind"] = "asset"
        elif entity_kind == "employee":
            q_mongo["$or"] = q_mongo.get("$or") or []
            q_mongo["entity_kind"] = {"$in": ["employee", None]}
        elif lane == "vendor":
            q_mongo["entity_kind"] = "vendor"
        else:
            # No entity_kind + no explicit vendor lane → default to
            # employee for backwards compatibility. Vendor / asset
            # records are invisible to existing callers.
            q_mongo["entity_kind"] = {"$in": ["employee", None]}
        if vendor_id:
            q_mongo["vendor_id"] = vendor_id
        if vendor_name:
            q_mongo["vendor_name"] = vendor_name
        # Track 19.61 · asset-entity filters.
        if asset_id:
            q_mongo["asset_id"] = asset_id
        if asset_unit_number:
            q_mongo["asset_unit_number"] = asset_unit_number
        if batch_id:
            q_mongo["imported_batch_id"] = batch_id
        if department:
            q_mongo["owning_department"] = department
        if uploader_email:
            q_mongo["created_by"] = uploader_email
        if reviewer_email:
            q_mongo["reviewed_by"] = reviewer_email
        if tag:
            q_mongo["tags"] = tag
        if related_asset_id:
            q_mongo["related_asset_id"] = related_asset_id
        if related_incident_case_id:
            q_mongo["related_incident_case_id"] = related_incident_case_id
        if related_project_id:
            q_mongo["related_project_id"] = related_project_id
        if related_training_id:
            q_mongo["related_training_id"] = related_training_id
        if date_from or date_to:
            rng: Dict[str, Any] = {}
            if date_from:
                rng["$gte"] = date_from
            if date_to:
                rng["$lte"] = date_to
            q_mongo["effective_date"] = rng
        if q:
            # Structured substring on a handful of known-safe text fields.
            # No full-text/OCR — this is a plain regex OR across metadata.
            pat = {"$regex": q, "$options": "i"}
            q_mongo["$or"] = [
                {"record_type": pat},
                {"notes": pat},
                {"employee_name_snapshot": pat},
                {"source_file_name": pat},
                {"tags": pat},
            ]
        items: List[Dict[str, Any]] = []
        async for r in db.employee_records.find(q_mongo, {"_id": 0}).sort("created_at", -1).limit(limit):
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
        # Track 19.59 · vendor lane approval requires vendor identity +
        # record_type. Employee lanes retain their existing rules.
        # Track 19.61 · asset entity approval requires asset identity +
        # record_type.
        entity_kind = rec.get("entity_kind") or (
            "vendor" if lane == "vendor" else DEFAULT_ENTITY_KIND
        )
        if entity_kind == "vendor":
            if not (rec.get("vendor_id") or rec.get("vendor_name")):
                raise HTTPException(
                    400, "Cannot approve — vendor_id or vendor_name is required"
                )
            if not rec.get("record_type"):
                raise HTTPException(400, "Cannot approve — record_type is required")
        elif entity_kind == "asset":
            if not (
                rec.get("asset_id")
                or rec.get("asset_unit_number")
                or rec.get("related_asset_id")
            ):
                raise HTTPException(
                    400,
                    "Cannot approve — asset_id, asset_unit_number, or "
                    "related_asset_id is required",
                )
            if not rec.get("record_type"):
                raise HTTPException(400, "Cannot approve — record_type is required")
        else:
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

    # ── Track 19.22 · P1 · Bulk batch operations ──────────────────
    # Batch upload: many files → many staged records in a single batch.
    # No OCR. No AI. Every record still requires manual employee link
    # and manual record_type before approval.
    @router.post("/batches/{batch_id}/uploads")
    async def batch_upload(
        batch_id: str,
        files: List[UploadFile] = File(...),
        actor: Dict[str, Any] = _actor_dep(),
    ):
        batch = await db.record_import_batches.find_one({"id": batch_id}, {"_id": 0})
        if not batch:
            raise HTTPException(404, "Batch not found")
        lane = batch.get("ownership_lane")
        if not _actor_can_read_lane(actor, lane or ""):
            raise HTTPException(403, "Not authorized for this lane")
        created: List[Dict[str, Any]] = []
        for f in files:
            raw = await f.read()
            if len(raw) == 0:
                continue
            if len(raw) > MAX_UPLOAD_BYTES:
                # Skip this file but keep processing the rest so a
                # single bad file doesn't nuke the whole batch.
                continue
            name = f.filename or "upload.bin"
            ext = (name.rsplit(".", 1)[-1] if "." in name else "").lower()
            if ext not in ALLOWED_EXTS:
                continue
            digest = _sha256(raw)
            ref = None
            try:
                from photo_storage import upload_photo_bytes, is_configured  # noqa: PLC0415
                if is_configured():
                    ref = await upload_photo_bytes(
                        raw, ext=ext, source_id=f"emp-rec/{lane}/batch/{digest[:12]}",
                        content_type=f.content_type or "application/octet-stream",
                    )
            except Exception as exc:
                logger.warning("[employee_records] batch cloud upload failed: %s", exc)
            if not ref:
                import base64
                b64 = base64.b64encode(raw).decode("ascii")
                ct = f.content_type or "application/octet-stream"
                ref = f"data:{ct};base64,{b64}"
            # Stage the record with NO employee link and NO record_type
            # so it lands in pending_match / pending_classification and
            # a human must classify it in the batch detail view.
            rec = {
                "id": str(uuid.uuid4()),
                "employee_id": None,
                "employee_name_snapshot": None,
                "record_type": None,
                "record_category": None,
                "ownership_lane": lane,
                "owning_department": lane,
                "created_by": actor.get("email") or actor.get("name"),
                "created_by_role": _actor_role(actor),
                "reviewed_by": None,
                "approved_by": None,
                "approval_status": "pending_classification",
                "effective_date": None,
                "source_type": batch.get("source_type") or "upload",
                "source_file_ref": ref,
                "source_file_name": name,
                "source_file_hash": digest,
                "imported_batch_id": batch_id,
                # Track 19.25 · Session provenance inherited from batch.
                "intake_source_name": batch.get("source_name") or "",
                "intake_source_type": batch.get("source_type") or "",
                "intake_source_location": batch.get("source_location") or "",
                "intake_batch_label": batch.get("label") or "",
                "related_incident_case_id": None,
                "related_training_id": None,
                "related_asset_id": None,
                "related_project_id": None,
                "related_supervisor_id": None,
                "tags": [],
                "notes": "",
                "status": "pending_classification",
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
            }
            await db.employee_records.insert_one(rec)
            await _write_audit(
                db, record_id=rec["id"], event="record_created", actor=actor,
                details={"state": "pending_classification", "batch_id": batch_id,
                         "ownership_lane": lane},
            )
            rec.pop("_id", None)
            created.append(rec)
        await db.record_import_batches.update_one(
            {"id": batch_id},
            {"$inc": {"file_count": len(created), "record_count": len(created)}},
        )
        return {"ok": True, "created": len(created), "records": created}

    # Bulk classify: apply the same record_type / employee_id / date to
    # every still-unclassified record in a batch. Human-driven; no AI.
    @router.post("/batches/{batch_id}/apply")
    async def batch_bulk_apply(
        batch_id: str,
        body: BulkApplyBody = Body(...),
        actor: Dict[str, Any] = _actor_dep(),
    ):
        batch = await db.record_import_batches.find_one({"id": batch_id}, {"_id": 0})
        if not batch:
            raise HTTPException(404, "Batch not found")
        lane = batch.get("ownership_lane") or ""
        if not _actor_can_read_lane(actor, lane):
            raise HTTPException(403, "Not authorized for this lane")
        if body.record_type is not None:
            _validate_lane_and_type(lane, body.record_type)
        patch: Dict[str, Any] = {"updated_at": _now_iso()}
        if body.record_type is not None:
            patch["record_type"] = body.record_type
        if body.employee_id is not None:
            patch["employee_id"] = body.employee_id
            # Refresh the snapshot when we assign an employee.
            snap = body.employee_name_snapshot
            if not snap:
                emp = await db.employees.find_one(
                    {"$or": [{"id": body.employee_id}, {"employee_id": body.employee_id}]},
                    {"_id": 0, "name": 1},
                )
                snap = (emp or {}).get("name") or ""
            patch["employee_name_snapshot"] = snap
        if body.effective_date is not None:
            patch["effective_date"] = body.effective_date
        if body.tags is not None:
            patch["tags"] = body.tags
        # Filter: only records in this batch that still need action.
        q: Dict[str, Any] = {"imported_batch_id": batch_id}
        if body.only_unclassified:
            q["approval_status"] = {"$in": ["pending_classification", "pending_match"]}
        # Compute new state per record after patch is applied.
        modified_ids: List[str] = []
        async for r in db.employee_records.find(q, {"_id": 0, "id": 1, "record_type": 1, "employee_id": 1}):
            new_type = patch.get("record_type", r.get("record_type"))
            new_emp = patch.get("employee_id", r.get("employee_id"))
            if new_emp and new_type:
                patch["approval_status"] = "pending_approval"
                patch["status"] = "pending_approval"
            elif not new_emp:
                patch["approval_status"] = "pending_match"
                patch["status"] = "pending_match"
            else:
                patch["approval_status"] = "pending_classification"
                patch["status"] = "pending_classification"
            await db.employee_records.update_one({"id": r["id"]}, {"$set": patch})
            await _write_audit(
                db, record_id=r["id"], event="record_batch_apply", actor=actor,
                details={"batch_id": batch_id, "patch": {k: v for k, v in patch.items() if k != "updated_at"}},
            )
            modified_ids.append(r["id"])
        return {"ok": True, "modified": len(modified_ids), "record_ids": modified_ids}

    # Bulk approve every ready record in the batch. Approvers only.
    @router.post("/batches/{batch_id}/approve-all")
    async def batch_approve_all(
        batch_id: str,
        actor: Dict[str, Any] = _actor_dep(),
    ):
        batch = await db.record_import_batches.find_one({"id": batch_id}, {"_id": 0})
        if not batch:
            raise HTTPException(404, "Batch not found")
        lane = batch.get("ownership_lane") or ""
        if not _actor_can_approve(actor, lane):
            raise HTTPException(403, "Not authorized to approve for this lane")
        approved: List[str] = []
        async for r in db.employee_records.find(
            {"imported_batch_id": batch_id, "approval_status": "pending_approval"},
            {"_id": 0, "id": 1, "employee_id": 1, "record_type": 1},
        ):
            if not r.get("employee_id") or not r.get("record_type"):
                continue
            await db.employee_records.update_one(
                {"id": r["id"]},
                {"$set": {
                    "approval_status": "linked",
                    "status": "linked",
                    "approved_by": actor.get("email") or actor.get("name"),
                    "reviewed_by": actor.get("email") or actor.get("name"),
                    "updated_at": _now_iso(),
                }},
            )
            await _write_audit(
                db, record_id=r["id"], event="record_approved", actor=actor,
                details={"batch_id": batch_id, "bulk": True},
            )
            approved.append(r["id"])
        return {"ok": True, "approved": len(approved), "record_ids": approved}

    @router.get("/batches/{batch_id}")
    async def get_batch(
        batch_id: str,
        actor: Dict[str, Any] = _actor_dep(),
    ):
        batch = await db.record_import_batches.find_one({"id": batch_id}, {"_id": 0})
        if not batch:
            raise HTTPException(404, "Batch not found")
        if not _actor_can_read_lane(actor, batch.get("ownership_lane") or ""):
            raise HTTPException(403, "Not authorized for this lane")
        records: List[Dict[str, Any]] = []
        async for r in db.employee_records.find(
            {"imported_batch_id": batch_id}, {"_id": 0},
        ).sort("created_at", 1).limit(500):
            records.append(r)
        # Simple state breakdown for the UI.
        counts: Dict[str, int] = {}
        for r in records:
            counts[r.get("approval_status", "unknown")] = counts.get(r.get("approval_status", "unknown"), 0) + 1
        return {"ok": True, "batch": batch, "records": records, "counts": counts}

    # ── Track 19.22 · Phase 3 · Export packages (PDF) ──────────────
    # Six operational packages built from the existing employee data.
    # Reuses HR timeline + records collection. Read-only. HR + admin
    # get everything; Safety only Safety-related packages; Asset only
    # Asset-related packages.
    PACKAGE_CATEGORIES = {
        "complete_file":       None,                              # everything
        "training":            {"Training", "Driver Qualification"},
        "discipline":          {"HR Lifecycle", "Field Leadership"},
        "safety":              {"Incidents", "Field Leadership"},
        "ppe_asset":           {"PPE & Equipment"},
        "historical_records":  None,                              # from db.employee_records
    }

    PACKAGE_TITLE = {
        "complete_file":       "Complete Employee File",
        "training":            "Training Package",
        "discipline":          "Discipline Package",
        "safety":              "Safety Package",
        "ppe_asset":           "PPE / Asset Package",
        "historical_records":  "Historical Records Package",
    }

    PACKAGE_LANE_GATE = {
        # HR + admin can pull every package.
        # Safety can pull Safety Package.
        # Asset admin can pull PPE / Asset package and historical (asset lane) records.
        "safety":              {"hr", "admin", "safety"},
        "ppe_asset":           {"hr", "admin", "asset_admin"},
        "historical_records":  {"hr", "admin", "safety", "asset_admin"},
        "complete_file":       {"hr", "admin"},
        "training":            {"hr", "admin"},
        "discipline":          {"hr", "admin"},
    }

    @router.get("/employees/{emp_id}/exports/{package}.pdf")
    async def employee_package_pdf(
        emp_id: str,
        package: str,
        actor: Dict[str, Any] = _actor_dep(),
    ):
        if package not in PACKAGE_TITLE:
            raise HTTPException(404, f"Unknown package: {package}")
        allowed = PACKAGE_LANE_GATE.get(package, {"hr", "admin"})
        role = _actor_role(actor)
        if role not in allowed:
            raise HTTPException(403, "Not authorized for this package")

        # Employee identity (single source of truth · db.employees).
        emp = await db.employees.find_one(
            {"$or": [{"id": emp_id}, {"employee_id": emp_id}]},
            {"_id": 0},
        )
        if not emp:
            raise HTTPException(404, "Employee not found")

        # Timeline events (already exists; do not duplicate). Filter by
        # the package's category set. `complete_file` includes all.
        try:
            hr_portal_mod = __import__("routes.hr_portal", fromlist=["hr_portal_router_factory"])
            # We DON'T instantiate the whole router — we just want the
            # aggregator function. It's defined inside the factory, but
            # we can call the endpoint via the existing route through
            # a lightweight direct fetch. Simpler: recompute a minimal
            # events list by delegating to the collection scans that
            # the timeline endpoint uses. To avoid duplication, we call
            # the FastAPI endpoint via httpx if the app is running.
            # For a self-contained package export we rebuild locally
            # from the same primitives.
            _ = hr_portal_mod  # noqa: F841 (kept for lint-clean reference)
        except Exception:
            pass

        # Delegate to the timeline builder using the internal API in
        # HR portal. The safe fast path: read `db.employee_records`
        # + emit key HR/lifecycle events. Full timeline aggregation
        # already lives in hr_portal — for exports we prefer local
        # composition to keep this endpoint self-contained.
        # Pull approved employee_records (source of truth for docs).
        docs: List[Dict[str, Any]] = []
        async for r in db.employee_records.find(
            {"employee_id": emp_id, "approval_status": "linked"}, {"_id": 0},
        ).sort("effective_date", -1).limit(500):
            docs.append(r)

        # Category filter.
        cat_filter = PACKAGE_CATEGORIES.get(package)
        # Also pull timeline events via internal call for richer packages.
        events: List[Dict[str, Any]] = []
        try:
            from routes.hr_portal import _timeline_for_export  # noqa: PLC0415
            events = await _timeline_for_export(db, emp_id)
        except Exception:
            events = []
        if cat_filter is not None:
            events = [e for e in events if e.get("category") in cat_filter]

        # For historical_records package: only show employee_records.
        if package == "historical_records":
            events = []

        pdf_bytes = _render_employee_package_pdf(
            emp=emp,
            package_key=package,
            package_title=PACKAGE_TITLE[package],
            events=events,
            docs=docs,
            actor_email=actor.get("email") or actor.get("name") or "system",
            actor_role=role,
        )
        from fastapi.responses import Response  # noqa: PLC0415
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    f'inline; filename="{emp.get("name","employee").replace(" ","_")}'
                    f'_{package}.pdf"',
            },
        )

    return router


def _render_employee_package_pdf(*, emp, package_key, package_title,
                                 events, docs, actor_email, actor_role) -> bytes:
    """Executive-quality package PDF · Track 19.22 · Phase 3+6.

    Consistent typography · logical grouping · beautiful headers ·
    professional footers · no N/A spam · single-column body for
    readability. Uses ReportLab (already in requirements).
    """
    from io import BytesIO  # noqa: PLC0415
    from reportlab.lib.pagesizes import letter  # noqa: PLC0415
    from reportlab.lib import colors  # noqa: PLC0415
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # noqa: PLC0415
    from reportlab.lib.units import inch  # noqa: PLC0415
    from reportlab.platypus import (  # noqa: PLC0415
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    )

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.65 * inch, rightMargin=0.65 * inch,
        topMargin=0.65 * inch, bottomMargin=0.7 * inch,
        title=f"{package_title} — {emp.get('name') or 'Employee'}",
    )
    styles = getSampleStyleSheet()
    accent = colors.HexColor("#5b21b6") if package_key != "safety" else colors.HexColor("#0f766e")
    if package_key == "ppe_asset":
        accent = colors.HexColor("#c2410c")
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=20,
                        textColor=accent, spaceAfter=2, leading=22)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=11,
                        textColor=colors.HexColor("#0f172a"), spaceBefore=14,
                        spaceAfter=4, fontName="Helvetica-Bold")
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9, leading=12)
    small = ParagraphStyle("small", parent=styles["BodyText"], fontSize=7.5,
                           leading=10, textColor=colors.HexColor("#475569"))

    story: List[Any] = []

    # Header block
    story.append(Paragraph(package_title, h1))
    story.append(Paragraph(
        f"<b>{emp.get('name') or '—'}</b> · "
        f"{emp.get('trade') or '—'} · "
        f"Employee ID {emp.get('employee_id') or emp.get('id') or '—'}",
        body,
    ))
    story.append(Paragraph(
        f"Generated {datetime.now(timezone.utc).isoformat()[:19].replace('T',' ')} UTC · "
        f"By {actor_email} ({actor_role})",
        small,
    ))
    story.append(Spacer(1, 10))

    # Employee snapshot
    story.append(Paragraph("Employee Snapshot", h2))
    snap_rows = [
        ["Lifecycle", emp.get("lifecycle_status") or "Active",
         "Department", emp.get("department") or "—"],
        ["Trade", emp.get("trade") or "—",
         "Supervisor", emp.get("supervisor") or "—"],
        ["Email", emp.get("email") or "—",
         "Hire Date", emp.get("hire_date") or "—"],
    ]
    snap_style = TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f1f5f9")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ])
    t_snap = Table(snap_rows, colWidths=[1.1 * inch, 2.4 * inch, 1.1 * inch, 2.4 * inch])
    t_snap.setStyle(snap_style)
    story.append(t_snap)

    # Timeline events section (when applicable)
    if events:
        story.append(Paragraph(
            f"Timeline · {len(events)} event(s)", h2))
        rows = [["Category", "Date", "Title", "Detail"]]
        for e in events[:400]:
            title = str(e.get("title", ""))[:80]
            desc = str(e.get("description", ""))[:120]
            ts = str(e.get("ts", ""))[:10]
            rows.append([str(e.get("category", "")), ts, title, desc])
        tbl = Table(rows, colWidths=[1.1 * inch, 0.7 * inch, 2.2 * inch, 3.0 * inch],
                    repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f8fafc")]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(tbl)

    # Documents section (from db.employee_records)
    if docs:
        # Filter docs to the package's lane theme.
        if package_key == "training":
            docs = [d for d in docs if d.get("ownership_lane") == "safety"
                    and "train" in (d.get("record_type") or "")]
        elif package_key == "discipline":
            docs = [d for d in docs if d.get("ownership_lane") == "hr"]
        elif package_key == "safety":
            docs = [d for d in docs if d.get("ownership_lane") == "safety"]
        elif package_key == "ppe_asset":
            docs = [d for d in docs if d.get("ownership_lane") == "asset"]
        # complete_file & historical_records include everything.
        if docs:
            story.append(Paragraph(f"Attached Records · {len(docs)}", h2))
            rows = [["Type", "Lane", "Effective", "File", "Status", "Uploader"]]
            for d in docs[:300]:
                rows.append([
                    str(d.get("record_type") or "—").replace("_", " ")[:28],
                    str(d.get("ownership_lane") or "—"),
                    str(d.get("effective_date") or "—")[:10],
                    str(d.get("source_file_name") or "—")[:40],
                    str(d.get("approval_status") or "—"),
                    str(d.get("created_by") or "—")[:30],
                ])
            tbl = Table(rows, colWidths=[1.4 * inch, 0.7 * inch, 0.75 * inch, 1.9 * inch, 0.8 * inch, 1.45 * inch],
                        repeatRows=1)
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#f8fafc")]),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(tbl)

    if not events and not docs:
        story.append(Paragraph("Records", h2))
        story.append(Paragraph(
            "No records match this package for this employee yet.", body))

    # Footer signature line
    story.append(Spacer(1, 14))
    story.append(Paragraph(
        f"MASCI Operations Platform · {package_title} · "
        f"This document is generated from the live Employee Records "
        f"Intelligence Platform. All entries are traceable in the "
        f"append-only audit ledger.",
        small,
    ))

    doc.build(story)
    return buf.getvalue()


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

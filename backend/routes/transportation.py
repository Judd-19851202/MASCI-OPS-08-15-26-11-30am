"""TRACK 16.04 · Transportation Foundation Phase 1.

Carriers · Transport Persons · Transport Trucks · Eligibility skeleton.

Mounted via ``register_transportation_routes(app, db, require_admin_dep,
require_dispatch_or_admin_dep)``.

Phase-1 scope ONLY. Deferrals (documented in
``/app/memory/TRACK_16_04_TRANSPORTATION_FOUNDATION_PHASE_1.md``):

* hauler packet uploads
* Clearinghouse / CDL / medical document intake
* orientation video engine / quizzes / certificates
* dispatch hard-block enforcement
* carrier portal · public invite links
* intelligence / scorecards
"""
from __future__ import annotations

import logging
import uuid

from lib.mongo_query import safe_regex
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel, Field

from lib.transport_eligibility import (
    VALID_STATUSES,
    ELIGIBILITY_STATES,
    compute_transport_eligibility,
)
from lib.transport_identity import (
    find_existing_employee_projection,
    find_existing_leased_driver,
    display_name,
)

logger = logging.getLogger(__name__)

TENANT = "masci"

CARRIER_TYPES = ("leased_hauler", "owner_operator", "supplier",
                 "masci_internal", "other")
PERSON_KINDS = ("masci_employee", "leased_driver")
TRUCK_OWNERSHIPS = ("masci_owned", "leased_carrier", "owner_operator", "unknown")
TRUCK_TYPES = ("dump_truck", "flow_boy", "lowboy", "tanker",
               "roll_off", "service_truck", "other")
TRUCK_STATUSES = ("pending_review", "active", "on_hold", "inactive",
                  "retired", "out_of_service")
TARGET_TYPES = ("carrier", "person", "truck")

# Track 19.02 — Fleet projection.
# Transportation Operations is a READ-MOSTLY view into the MASCI fleet
# (`equipment_master` / `equipment_units` remain the source of truth).
# The categories below define which `equipment_master.category` values
# the Transportation Trucks page surfaces.
#
# Track 19.02A · Classification Standard:
#   • INCLUDE  on-road haul-capable, dispatch-able operational assets.
#   • EXCLUDE  passenger / office / executive / management vehicles
#              (per directive, "Pickup Trucks" and "Supervisor / Mgmt
#              Trucks" categories are passenger/light-duty and do NOT
#              participate in dispatchable Transportation Operations).
# This list can be expanded without a schema change.
TRANSPORT_CAPABLE_CATEGORIES = (
    "Dump Trucks",
    "Tractor Trailer Trucks",
    "Service Trucks",
    "Water Trucks",
    "Misc Trucks",
    "Flatbed Trucks",
    "Trailers",
)

# Track 19.02A · Operational overlay field policy.
# Transportation may edit only the operational metadata it owns;
# enterprise asset identity remains owned by the Equipment platform.
TRANSPORT_OVERLAY_EDITABLE_FIELDS = (
    "truck_type",
    "transportation_classification",
    "status",
    "safety_hold",
    "carrier_id",
    "driver_id",
    "dispatch_ready",
    "primary_division",
    "operational_tags",
    "active_for_transport",
    "transportation_notes",
)
# Fields owned by Equipment Master / Units — never editable from the
# Transportation overlay. If a client tries to PATCH any of these, the
# overlay PATCH endpoint responds 422 with a clear message.
TRANSPORT_OVERLAY_PROTECTED_FIELDS = (
    "vin", "vin_serial_number", "asset_id", "unit_number",
    "make", "model", "year", "make_model", "plate",
    "purchase_price", "purchase_date", "depreciation",
    "engine_hours", "meter_reading", "ownership",
    "category", "is_active", "operational_status",
)
# Valid transportation_classification values.
TRANSPORT_CLASSIFICATIONS = (
    "heavy_haul", "end_dump", "transfer", "day_cab", "sleeper",
    "lowboy", "equipment_hauler", "equipment_trailer", "tag_trailer",
    "flatbed", "water_truck", "fuel_truck", "service_truck",
    "pole_trailer", "jeep_dolly", "other",
)


# ---------------------------------------------------------------------------
# Pydantic input shapes (output uses dict projections; never raw Mongo docs)
# ---------------------------------------------------------------------------
class CarrierCreate(BaseModel):
    legal_name: str = Field(..., min_length=1, max_length=240)
    dba_name: Optional[str] = None
    carrier_type: str = Field("leased_hauler")
    dot_number: Optional[str] = None
    mc_number: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    status: Optional[str] = "pending_review"
    safety_hold: Optional[bool] = False
    notes: Optional[str] = None


class CarrierPatch(BaseModel):
    legal_name: Optional[str] = None
    dba_name: Optional[str] = None
    carrier_type: Optional[str] = None
    dot_number: Optional[str] = None
    mc_number: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    status: Optional[str] = None
    safety_hold: Optional[bool] = None
    notes: Optional[str] = None


class PersonCreate(BaseModel):
    kind: str
    employee_id: Optional[str] = None
    carrier_id: Optional[str] = None
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    phone: Optional[str] = None
    email: Optional[str] = None
    license_number: Optional[str] = None
    cdl_class: Optional[str] = None
    status: Optional[str] = "pending_review"
    safety_hold: Optional[bool] = False
    notes: Optional[str] = None


class PersonPatch(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    license_number: Optional[str] = None
    cdl_class: Optional[str] = None
    status: Optional[str] = None
    safety_hold: Optional[bool] = None
    notes: Optional[str] = None


class LinkFromHRBody(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=120)
    status: Optional[str] = "pending_review"
    notes: Optional[str] = None


class TruckCreate(BaseModel):
    ownership: str
    equipment_id: Optional[str] = None
    carrier_id: Optional[str] = None
    truck_number: str = Field(..., min_length=1, max_length=64)
    vin: Optional[str] = None
    plate: Optional[str] = None
    truck_type: str = Field("dump_truck")
    status: Optional[str] = "pending_review"
    safety_hold: Optional[bool] = False
    notes: Optional[str] = None


class TruckPatch(BaseModel):
    equipment_id: Optional[str] = None
    truck_number: Optional[str] = None
    vin: Optional[str] = None
    plate: Optional[str] = None
    truck_type: Optional[str] = None
    status: Optional[str] = None
    safety_hold: Optional[bool] = None
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _actor_label(actor: Any) -> str:
    if isinstance(actor, dict):
        return str(actor.get("email") or actor.get("name") or
                   actor.get("id") or "admin")
    return "admin"


def _project_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Strip ``_id`` and return doc as-is. Phase 1 never echoes
    password / secret-class fields (none exist on these models)."""
    if not doc:
        return None
    out = {k: v for k, v in doc.items() if k != "_id"}
    return out


async def _audit(db, *, kind: str, entity_type: str, entity_id: str,
                 actor: Any, old: Optional[Dict[str, Any]],
                 new: Optional[Dict[str, Any]], request: Optional[Request]) -> None:
    """Append a single audit row. Best-effort: never raises."""
    try:
        doc = {
            "id": uuid.uuid4().hex,
            "kind": kind,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "actor": _actor_label(actor),
            "old": old,
            "new": new,
            "ts": _now(),
            "tenant": TENANT,
        }
        if request is not None:
            doc["route"] = str(request.url.path)
            doc["ip"] = (request.headers.get("x-forwarded-for") or
                         (request.client.host if request.client else "")) or None
            doc["ua"] = request.headers.get("user-agent")
        await db.audit_events.insert_one(doc)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"transport audit insert failed: {exc}")


async def _upsert_eligibility(db, *, target_type: str, target_id: str,
                              record: Dict[str, Any],
                              context: Optional[Dict[str, Any]] = None
                              ) -> Dict[str, Any]:
    """Recompute eligibility and persist a single canonical row per
    (target_type, target_id, tenant). Returns the upserted document."""
    record_type_map = {"carrier": "carrier", "person": "person", "truck": "truck"}
    rt = record_type_map[target_type]
    ctx = dict(context or {})
    # TRACK 16.08 · Inject orientation status into the eligibility context
    # for drivers. The pure compute function reads ``orientation_status``
    # and may flip the state to ``not_dispatchable``.
    if target_type == "person":
        try:
            from lib.transport_orientation_status import (  # noqa: PLC0415
                derive_orientation_status,
            )
            os_ctx = await derive_orientation_status(db, target_id)
            ctx.setdefault("orientation_status", os_ctx["orientation_status"])
        except Exception:  # noqa: BLE001
            pass
    result = compute_transport_eligibility(rt, record, ctx)
    row = {
        "tenant": TENANT,
        "target_type": target_type,
        "target_id": target_id,
        "state": result["state"],
        "reasons": result["reasons"],
        "computed_at": result["computed_at"],
        "expires_at": result.get("expires_at"),
        "stale": False,
        "phase": 1,
    }
    existing = await db.transport_eligibility_state.find_one({
        "tenant": TENANT, "target_type": target_type, "target_id": target_id,
    })
    if existing:
        row["id"] = existing.get("id") or uuid.uuid4().hex
        await db.transport_eligibility_state.update_one(
            {"_id": existing["_id"]}, {"$set": row}
        )
    else:
        row["id"] = uuid.uuid4().hex
        await db.transport_eligibility_state.insert_one(row.copy())
    return row


async def _hr_lifecycle_active(db, employee_id: Optional[str]) -> Optional[bool]:
    """Backwards-compat boolean — Track 16.04. New callers should
    prefer :func:`_hr_lifecycle_context` which returns the full
    projection introduced in Track 16.11."""
    ctx = await _hr_lifecycle_context(db, employee_id)
    if ctx is None:
        return None
    return ctx.get("hr_lifecycle_active")


async def _hr_lifecycle_context(
    db, employee_id: Optional[str],
) -> Optional[Dict[str, Any]]:
    """TRACK 16.11 · Resolve the HR projection for a MASCI employee
    driver. Returns a dict suitable to merge into the eligibility
    context, or ``None`` when no employee_id is supplied."""
    if not employee_id:
        return None
    try:
        from lib.transport_hr_lifecycle import map_hr_lifecycle_to_transport
        row = await db.employees.find_one(
            {"$or": [{"employee_id": employee_id}, {"id": employee_id}],
             "deleted_at": None},
            {"_id": 0},
        )
    except Exception:  # noqa: BLE001
        return None
    if not row:
        # Surface a needs_correction projection so the eligibility
        # engine can flag the linkage gap without inventing a status.
        return {
            "hr_lifecycle_active": None,
            "hr_transport_state": "needs_correction",
            "hr_reason_codes": ["hr_employee_missing"],
            "hr_reason_labels": ["Linked HR employee record not found"],
            "hr_source_status": None,
        }
    proj = map_hr_lifecycle_to_transport(row)
    return {
        "hr_lifecycle_active": proj["hr_active"],
        "hr_transport_state": proj["transport_state"],
        "hr_reason_codes": proj["reason_codes"],
        "hr_reason_labels": proj["reason_labels"],
        "hr_source_status": proj["source_status"],
    }


def _validate_status(v: Optional[str]) -> None:
    if v is None:
        return
    if v not in VALID_STATUSES:
        raise HTTPException(422, f"status must be one of {list(VALID_STATUSES)}")


# ---------------------------------------------------------------------------
# Router factory
# ---------------------------------------------------------------------------
def register_transportation_routes(
    app, db,
    require_admin_dep: Callable,
    require_dispatch_or_admin_dep: Callable,
) -> APIRouter:
    """Register the Track 16.04 transportation foundation routes."""

    # Self-contained dispatch-or-admin gate that honors BOTH the new per-user
    # admin token (<id>.<HMAC>) and the dispatch portal token. Built locally
    # because the platform-wide ``_shared_dispatch_or_admin`` factory still
    # consults the retired synchronous admin validator (Track 15.32 stub) and
    # would reject every modern admin token. Phase-1 contract: dispatch read
    # routes must accept admin OR dispatch tokens.
    from fastapi import Header  # local import (FastAPI re-imports are cheap)

    async def _local_dispatch_or_admin(
        request: Request,
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
        x_dispatch_token: Optional[str] = Header(default=None, alias="X-Dispatch-Token"),
    ) -> Dict[str, Any]:
        # Admin path — canonical per-user token validator.
        if x_admin_token and "." in x_admin_token:
            try:
                from user_directory import (  # noqa: PLC0415
                    is_valid_directory_admin_token_async,
                )
                u = await is_valid_directory_admin_token_async(db, x_admin_token)
                if u:
                    return {"role": "admin", **u}
            except Exception:  # noqa: BLE001
                pass
        # Dispatch path.
        if x_dispatch_token and "." in x_dispatch_token:
            try:
                from dispatch_users import (  # noqa: PLC0415
                    is_valid_dispatch_user_token_async,
                )
                u = await is_valid_dispatch_user_token_async(db, x_dispatch_token)
                if u:
                    return {"role": "dispatch", **u}
            except Exception:  # noqa: BLE001
                pass
        raise HTTPException(401, "Dispatch or Admin auth required")

    # Use the local gate everywhere instead of the (broken) shared one.
    require_dispatch_or_admin_dep = _local_dispatch_or_admin  # noqa: F811

    router = APIRouter(prefix="/api", tags=["transportation"])

    # ─────────────────────── CARRIERS · admin ───────────────────────
    @router.get("/admin/transportation/carriers")
    async def list_carriers(
        q: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        limit: int = Query(200, ge=1, le=1000),
        _: Any = Depends(require_dispatch_or_admin_dep),
    ):
        query: Dict[str, Any] = {"tenant": TENANT}
        if status:
            query["status"] = status
        if q:
            query["$or"] = [
                {"legal_name": safe_regex(q)},
                {"dba_name": safe_regex(q)},
                {"dot_number": safe_regex(q)},
            ]
        cur = db.carriers.find(query).sort("created_at", -1).limit(limit)
        items = [_project_doc(d) for d in await cur.to_list(limit)]
        total = await db.carriers.count_documents(query)
        return {"count": len(items), "total": total, "returned": len(items),
                "truncated": total > len(items), "items": items}

    @router.post("/admin/transportation/carriers")
    async def create_carrier(
        body: CarrierCreate, request: Request,
        actor: Any = Depends(require_dispatch_or_admin_dep),
    ):
        if body.carrier_type not in CARRIER_TYPES:
            raise HTTPException(422,
                f"carrier_type must be one of {list(CARRIER_TYPES)}")
        _validate_status(body.status)
        legal_norm = (body.legal_name or "").strip()
        if not legal_norm:
            raise HTTPException(422, "legal_name is required")
        dup = await db.carriers.find_one({
            "tenant": TENANT,
            "legal_name": legal_norm,
            "status": {"$ne": "inactive"},
        })
        if dup:
            raise HTTPException(409,
                f"Active carrier already exists with this legal_name "
                f"(id={dup.get('id')})")
        now = _now()
        doc = {
            "id": uuid.uuid4().hex,
            "tenant": TENANT,
            "legal_name": legal_norm,
            "dba_name": body.dba_name,
            "carrier_type": body.carrier_type,
            "dot_number": body.dot_number,
            "mc_number": body.mc_number,
            "contact_name": body.contact_name,
            "contact_phone": body.contact_phone,
            "contact_email": body.contact_email,
            "status": body.status or "pending_review",
            "safety_hold": bool(body.safety_hold),
            "notes": body.notes,
            "created_at": now,
            "updated_at": now,
            "created_by": _actor_label(actor),
            "updated_by": _actor_label(actor),
        }
        await db.carriers.insert_one(doc.copy())
        await _audit(db, kind="transport_carrier_create",
                     entity_type="carrier", entity_id=doc["id"],
                     actor=actor, old=None, new=_project_doc(doc),
                     request=request)
        await _upsert_eligibility(db, target_type="carrier",
                                  target_id=doc["id"], record=doc)
        return _project_doc(doc)

    @router.get("/admin/transportation/carriers/{cid}")
    async def get_carrier(cid: str = Path(...),
                          _: Any = Depends(require_dispatch_or_admin_dep)):
        doc = await db.carriers.find_one({"id": cid, "tenant": TENANT})
        if not doc:
            raise HTTPException(404, "Carrier not found")
        return _project_doc(doc)

    @router.patch("/admin/transportation/carriers/{cid}")
    async def patch_carrier(cid: str, body: CarrierPatch, request: Request,
                            actor: Any = Depends(require_dispatch_or_admin_dep)):
        existing = await db.carriers.find_one({"id": cid, "tenant": TENANT})
        if not existing:
            raise HTTPException(404, "Carrier not found")
        updates: Dict[str, Any] = {}
        for field in ("legal_name", "dba_name", "carrier_type", "dot_number",
                      "mc_number", "contact_name", "contact_phone",
                      "contact_email", "status", "safety_hold", "notes"):
            v = getattr(body, field)
            if v is not None:
                updates[field] = v
        if "status" in updates:
            _validate_status(updates["status"])
        if "carrier_type" in updates and updates["carrier_type"] not in CARRIER_TYPES:
            raise HTTPException(422, "invalid carrier_type")
        if "legal_name" in updates and updates["legal_name"] != existing.get("legal_name"):
            dup = await db.carriers.find_one({
                "tenant": TENANT, "legal_name": updates["legal_name"],
                "id": {"$ne": cid}, "status": {"$ne": "inactive"},
            })
            if dup:
                raise HTTPException(409, "Another active carrier has this legal_name")
        updates["updated_at"] = _now()
        updates["updated_by"] = _actor_label(actor)
        await db.carriers.update_one({"_id": existing["_id"]}, {"$set": updates})
        new_doc = {**existing, **updates}
        await _audit(db, kind="transport_carrier_update",
                     entity_type="carrier", entity_id=cid,
                     actor=actor, old=_project_doc(existing),
                     new=_project_doc(new_doc), request=request)
        await _upsert_eligibility(db, target_type="carrier",
                                  target_id=cid, record=new_doc)
        return _project_doc(new_doc)

    # ─────────────────────── PERSONS · admin ───────────────────────
    @router.get("/admin/transportation/persons")
    async def list_persons(
        q: Optional[str] = Query(None),
        kind: Optional[str] = Query(None),
        carrier_id: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        limit: int = Query(200, ge=1, le=1000),
        _: Any = Depends(require_dispatch_or_admin_dep),
    ):
        query: Dict[str, Any] = {"tenant": TENANT}
        if kind:
            query["kind"] = kind
        if carrier_id:
            query["carrier_id"] = carrier_id
        if status:
            query["status"] = status
        if q:
            query["$or"] = [
                {"first_name": safe_regex(q)},
                {"last_name": safe_regex(q)},
                {"email": safe_regex(q)},
                {"license_number": safe_regex(q)},
            ]
        cur = db.transport_persons.find(query).sort("created_at", -1).limit(limit)
        items = [_project_doc(d) for d in await cur.to_list(limit)]
        total = await db.transport_persons.count_documents(query)
        return {"count": len(items), "total": total, "returned": len(items),
                "truncated": total > len(items), "items": items}

    @router.post("/admin/transportation/persons")
    async def create_person(body: PersonCreate, request: Request,
                            actor: Any = Depends(require_dispatch_or_admin_dep)):
        if body.kind not in PERSON_KINDS:
            raise HTTPException(422, f"kind must be one of {list(PERSON_KINDS)}")
        _validate_status(body.status)
        if body.kind == "masci_employee":
            if not body.employee_id:
                raise HTTPException(422, "employee_id is required for masci_employee")
            dup = await find_existing_employee_projection(
                db, tenant=TENANT, employee_id=body.employee_id)
            if dup:
                raise HTTPException(409,
                    f"Active MASCI employee driver projection already exists "
                    f"(id={dup.get('id')})")
        elif body.kind == "leased_driver":
            if not body.carrier_id:
                raise HTTPException(422, "carrier_id is required for leased_driver")
            carrier = await db.carriers.find_one(
                {"id": body.carrier_id, "tenant": TENANT})
            if not carrier:
                raise HTTPException(404, "carrier_id not found")
            dup = await find_existing_leased_driver(
                db, tenant=TENANT, carrier_id=body.carrier_id,
                license_number=body.license_number)
            if dup:
                raise HTTPException(409,
                    f"Active leased driver with this license_number already "
                    f"exists under this carrier (id={dup.get('id')})")
        now = _now()
        doc = {
            "id": uuid.uuid4().hex,
            "tenant": TENANT,
            "kind": body.kind,
            "employee_id": body.employee_id if body.kind == "masci_employee" else None,
            "carrier_id": body.carrier_id if body.kind == "leased_driver" else None,
            "first_name": body.first_name,
            "last_name": body.last_name,
            "phone": body.phone,
            "email": body.email,
            "license_number": body.license_number,
            "cdl_class": body.cdl_class,
            "status": body.status or "pending_review",
            "safety_hold": bool(body.safety_hold),
            "notes": body.notes,
            "created_at": now,
            "updated_at": now,
            "created_by": _actor_label(actor),
            "updated_by": _actor_label(actor),
        }
        await db.transport_persons.insert_one(doc.copy())
        await _audit(db, kind="transport_person_create",
                     entity_type="person", entity_id=doc["id"],
                     actor=actor, old=None, new=_project_doc(doc),
                     request=request)
        ctx = {}
        if doc["kind"] == "masci_employee":
            hr_ctx = await _hr_lifecycle_context(db, doc["employee_id"])
            if hr_ctx:
                ctx.update(hr_ctx)
        await _upsert_eligibility(db, target_type="person",
                                  target_id=doc["id"], record=doc, context=ctx)
        return _project_doc(doc)

    @router.get("/admin/transportation/persons/{pid}")
    async def get_person(pid: str, _: Any = Depends(require_dispatch_or_admin_dep)):
        doc = await db.transport_persons.find_one({"id": pid, "tenant": TENANT})
        if not doc:
            raise HTTPException(404, "Transport person not found")
        return _project_doc(doc)

    @router.patch("/admin/transportation/persons/{pid}")
    async def patch_person(pid: str, body: PersonPatch, request: Request,
                           actor: Any = Depends(require_dispatch_or_admin_dep)):
        existing = await db.transport_persons.find_one({"id": pid, "tenant": TENANT})
        if not existing:
            raise HTTPException(404, "Transport person not found")
        updates: Dict[str, Any] = {}
        for field in ("first_name", "last_name", "phone", "email",
                      "license_number", "cdl_class", "status",
                      "safety_hold", "notes"):
            v = getattr(body, field)
            if v is not None:
                updates[field] = v
        if "status" in updates:
            _validate_status(updates["status"])
        updates["updated_at"] = _now()
        updates["updated_by"] = _actor_label(actor)
        await db.transport_persons.update_one({"_id": existing["_id"]},
                                              {"$set": updates})
        new_doc = {**existing, **updates}
        await _audit(db, kind="transport_person_update",
                     entity_type="person", entity_id=pid,
                     actor=actor, old=_project_doc(existing),
                     new=_project_doc(new_doc), request=request)
        ctx = {}
        if new_doc.get("kind") == "masci_employee":
            hr_ctx = await _hr_lifecycle_context(db, new_doc.get("employee_id"))
            if hr_ctx:
                ctx.update(hr_ctx)
        await _upsert_eligibility(db, target_type="person",
                                  target_id=pid, record=new_doc, context=ctx)
        return _project_doc(new_doc)

    # ─────────────── TRACK 19.00 · HR CDL → Transportation link ───────────────
    @router.get("/admin/transportation/eligible-hr-cdl-drivers")
    async def list_eligible_hr_cdl_drivers(
        q: Optional[str] = Query(None),
        include_linked: bool = Query(False),
        limit: int = Query(200, ge=1, le=1000),
        _: Any = Depends(require_dispatch_or_admin_dep),
    ):
        """Track 19.00 · List HR employees who are CDL holders and are
        Transportation-eligible candidates. Excludes:
          · non-CDL `approved_company_driver`-only employees (they are
            HR-approved company drivers, not haul drivers)
          · employees already linked to a non-deleted `transport_persons`
            record (unless `include_linked=true`)
          · soft-deleted employees
        """
        query: Dict[str, Any] = {
            "deleted_at": None,
            "cdl_holder": True,
        }
        # TRUTH PROGRAM · TD-0010 · eligible-driver lifecycle contract.
        # An "eligible CDL driver" must be an actively-employable person. The
        # prior filter omitted lifecycle status, so terminated/off-roll/retired/
        # pending employees leaked into the eligible list (live prod: 2 Resigned
        # + 1 Inactive among 43). Exclude every non-active canonical status;
        # None / missing lifecycle_status resolves to active (legacy fallback)
        # and is intentionally retained.
        from lib.employee_status import BUCKET_STATUSES  # noqa: PLC0415
        _ineligible = (
            BUCKET_STATUSES["off_roll"] + BUCKET_STATUSES["terminated"]
            + BUCKET_STATUSES["retired"] + BUCKET_STATUSES["pending"]
        )
        query["lifecycle_status"] = {"$nin": _ineligible}
        if q:
            query["$or"] = [
                {"name": safe_regex(q)},
                {"employee_id": safe_regex(q)},
                {"cdl_license_number": safe_regex(q)},
            ]
        projection = {
            "_id": 0, "id": 1, "employee_id": 1, "name": 1,
            "lifecycle_status": 1, "driver_status": 1,
            "cdl_holder": 1, "approved_company_driver": 1,
            "cdl_class": 1, "cdl_state": 1, "cdl_license_number": 1,
            "cdl_expiration_date": 1,
            "medical_card_expiration_date": 1,
            "cdl_endorsements": 1,
        }
        cur = db.employees.find(query, projection).sort("name", 1).limit(limit * 4)
        rows = await cur.to_list(limit * 4)
        # Build linked set
        linked_ids = set()
        if not include_linked:
            link_cur = db.transport_persons.find(
                {"tenant": TENANT, "kind": "masci_employee"},
                {"_id": 0, "id": 1, "employee_id": 1},
            )
            async for lp in link_cur:
                if lp.get("employee_id"):
                    linked_ids.add(str(lp["employee_id"]))
        items: List[Dict[str, Any]] = []
        for r in rows:
            emp_id = str(r.get("employee_id") or r.get("id") or "")
            already = emp_id in linked_ids if emp_id else False
            if already and not include_linked:
                continue
            items.append({
                "employee_id": emp_id,
                "name": r.get("name"),
                "lifecycle_status": r.get("lifecycle_status"),
                "driver_status": r.get("driver_status"),
                "cdl_holder": bool(r.get("cdl_holder")),
                "approved_company_driver": bool(r.get("approved_company_driver")),
                "cdl_class": r.get("cdl_class"),
                "cdl_state": r.get("cdl_state"),
                "cdl_license_number": r.get("cdl_license_number"),
                "cdl_expiration_date": r.get("cdl_expiration_date"),
                "medical_card_expiration_date": r.get("medical_card_expiration_date"),
                "cdl_endorsements": r.get("cdl_endorsements"),
                "already_linked": already,
            })
            if len(items) >= limit:
                break
        return {"count": len(items), "items": items}

    @router.post("/admin/transportation/persons/link-from-hr")
    async def link_person_from_hr(
        body: LinkFromHRBody, request: Request,
        actor: Any = Depends(require_dispatch_or_admin_dep),
    ):
        """Track 19.00 · Idempotently link an HR CDL employee into
        Transportation Operations as a `masci_employee` driver. HR remains
        the source of truth for identity; this creates the operational
        shell record only. Rejects non-CDL approved-only employees.
        """
        emp_id_raw = (body.employee_id or "").strip()
        if not emp_id_raw:
            raise HTTPException(422, "employee_id is required")
        _validate_status(body.status)
        # Find the HR employee by employee_id (preferred) or id
        emp = await db.employees.find_one(
            {"employee_id": emp_id_raw, "deleted_at": None})
        if not emp:
            emp = await db.employees.find_one(
                {"id": emp_id_raw, "deleted_at": None})
        if not emp:
            raise HTTPException(404, f"HR employee {emp_id_raw!r} not found")
        if not bool(emp.get("cdl_holder")):
            raise HTTPException(
                422,
                "Employee is not a CDL holder. Non-CDL approved drivers "
                "cannot be linked into the Transportation haul-driver list. "
                "If this employee should drive trucks, HR must set "
                "cdl_holder=true and the CDL credential fields.",
            )
        canonical_emp_id = str(emp.get("employee_id") or emp.get("id") or emp_id_raw)
        # Idempotent — return the existing link if present
        existing = await db.transport_persons.find_one({
            "tenant": TENANT,
            "kind": "masci_employee",
            "employee_id": canonical_emp_id,
        })
        if existing:
            return {
                "already_linked": True,
                **_project_doc(existing),
            }
        # Build the operational shell from HR identity
        full_name = (emp.get("name") or "").strip()
        first, last = "", ""
        if full_name:
            parts = full_name.split(None, 1)
            first = parts[0]
            last = parts[1] if len(parts) > 1 else ""
        first = first or emp.get("first_name") or "Employee"
        last = last or emp.get("last_name") or canonical_emp_id
        now = _now()
        doc = {
            "id": uuid.uuid4().hex,
            "tenant": TENANT,
            "kind": "masci_employee",
            "employee_id": canonical_emp_id,
            "carrier_id": None,
            "first_name": first[:120],
            "last_name": last[:120],
            "phone": emp.get("phone"),
            "email": emp.get("email"),
            "license_number": emp.get("cdl_license_number"),
            "cdl_class": emp.get("cdl_class"),
            "status": body.status or "pending_review",
            "safety_hold": False,
            "notes": body.notes,
            "linked_from_hr_at": now,
            "linked_from_hr_by": _actor_label(actor),
            "created_at": now,
            "updated_at": now,
            "created_by": _actor_label(actor),
            "updated_by": _actor_label(actor),
        }
        await db.transport_persons.insert_one(doc.copy())
        await _audit(
            db, kind="transport_person_link_from_hr",
            entity_type="person", entity_id=doc["id"],
            actor=actor, old=None, new=_project_doc(doc),
            request=request,
        )
        hr_ctx = await _hr_lifecycle_context(db, canonical_emp_id) or {}
        await _upsert_eligibility(
            db, target_type="person",
            target_id=doc["id"], record=doc, context=hr_ctx,
        )
        return {"already_linked": False, **_project_doc(doc)}

    # ─────────────────────── TRUCKS · admin ───────────────────────
    @router.get("/admin/transportation/trucks")
    async def list_trucks(
        q: Optional[str] = Query(None),
        ownership: Optional[str] = Query(None),
        carrier_id: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        limit: int = Query(200, ge=1, le=1000),
        _: Any = Depends(require_dispatch_or_admin_dep),
    ):
        query: Dict[str, Any] = {"tenant": TENANT}
        if ownership:
            query["ownership"] = ownership
        if carrier_id:
            query["carrier_id"] = carrier_id
        if status:
            query["status"] = status
        if q:
            query["$or"] = [
                {"truck_number": safe_regex(q)},
                {"vin": safe_regex(q)},
                {"plate": safe_regex(q)},
            ]
        cur = db.transport_trucks.find(query).sort("created_at", -1).limit(limit)
        items = [_project_doc(d) for d in await cur.to_list(limit)]
        total = await db.transport_trucks.count_documents(query)
        return {"count": len(items), "total": total, "returned": len(items),
                "truncated": total > len(items), "items": items}

    @router.post("/admin/transportation/trucks")
    async def create_truck(body: TruckCreate, request: Request,
                           actor: Any = Depends(require_admin_dep)):
        if body.ownership not in TRUCK_OWNERSHIPS:
            raise HTTPException(422,
                f"ownership must be one of {list(TRUCK_OWNERSHIPS)}")
        if body.truck_type not in TRUCK_TYPES:
            raise HTTPException(422,
                f"truck_type must be one of {list(TRUCK_TYPES)}")
        _validate_status(body.status)
        if body.ownership in ("leased_carrier", "owner_operator"):
            if not body.carrier_id:
                raise HTTPException(422,
                    "carrier_id is required for leased/owner-operator trucks")
            carrier = await db.carriers.find_one(
                {"id": body.carrier_id, "tenant": TENANT})
            if not carrier:
                raise HTTPException(404, "carrier_id not found")
        now = _now()
        doc = {
            "id": uuid.uuid4().hex,
            "tenant": TENANT,
            "ownership": body.ownership,
            "equipment_id": body.equipment_id if body.ownership == "masci_owned" else None,
            "carrier_id": body.carrier_id if body.ownership in ("leased_carrier", "owner_operator") else None,
            "truck_number": body.truck_number,
            "vin": body.vin,
            "plate": body.plate,
            "truck_type": body.truck_type,
            "status": body.status or "pending_review",
            "safety_hold": bool(body.safety_hold),
            "notes": body.notes,
            "created_at": now,
            "updated_at": now,
            "created_by": _actor_label(actor),
            "updated_by": _actor_label(actor),
        }
        await db.transport_trucks.insert_one(doc.copy())
        await _audit(db, kind="transport_truck_create",
                     entity_type="truck", entity_id=doc["id"],
                     actor=actor, old=None, new=_project_doc(doc),
                     request=request)
        await _upsert_eligibility(db, target_type="truck",
                                  target_id=doc["id"], record=doc)
        return _project_doc(doc)

    @router.get("/admin/transportation/trucks/{tid}")
    async def get_truck(tid: str, _: Any = Depends(require_dispatch_or_admin_dep)):
        doc = await db.transport_trucks.find_one({"id": tid, "tenant": TENANT})
        if not doc:
            raise HTTPException(404, "Transport truck not found")
        return _project_doc(doc)

    @router.patch("/admin/transportation/trucks/{tid}")
    async def patch_truck(tid: str, body: TruckPatch, request: Request,
                          actor: Any = Depends(require_admin_dep)):
        existing = await db.transport_trucks.find_one({"id": tid, "tenant": TENANT})
        if not existing:
            raise HTTPException(404, "Transport truck not found")
        updates: Dict[str, Any] = {}
        for field in ("equipment_id", "truck_number", "vin", "plate",
                      "truck_type", "status", "safety_hold", "notes"):
            v = getattr(body, field)
            if v is not None:
                updates[field] = v
        if "status" in updates:
            _validate_status(updates["status"])
        if "truck_type" in updates and updates["truck_type"] not in TRUCK_TYPES:
            raise HTTPException(422, "invalid truck_type")
        updates["updated_at"] = _now()
        updates["updated_by"] = _actor_label(actor)
        await db.transport_trucks.update_one({"_id": existing["_id"]},
                                             {"$set": updates})
        new_doc = {**existing, **updates}
        await _audit(db, kind="transport_truck_update",
                     entity_type="truck", entity_id=tid,
                     actor=actor, old=_project_doc(existing),
                     new=_project_doc(new_doc), request=request)
        await _upsert_eligibility(db, target_type="truck",
                                  target_id=tid, record=new_doc)
        return _project_doc(new_doc)

    # ─────────────────────── FLEET PROJECTION · admin ───────────────────────
    # Track 19.02 · Fleet view, not fleet database.
    # `equipment_master` + `equipment_units` remain the SINGLE source of
    # truth for asset identity. Transportation projects a join over them
    # plus the `transport_trucks` overlay (which carries Transportation-side
    # operational state: status, safety_hold, carrier_id, notes).
    @router.get("/admin/transportation/fleet/equipment")
    async def list_fleet_equipment(
        q: Optional[str] = Query(None),
        category: Optional[str] = Query(
            None, description="Specific transport-capable category"),
        status: Optional[str] = Query(
            None, description="Transportation overlay status filter"),
        ownership: Optional[str] = Query(
            None, description="masci_owned | leased_carrier | owner_operator"),
        limit: int = Query(500, ge=1, le=2000),
        _: Any = Depends(require_dispatch_or_admin_dep),
    ):
        # 1. MASCI-owned fleet (equipment_master, transport-capable subset).
        em_query: Dict[str, Any] = {
            "category": {"$in": list(TRANSPORT_CAPABLE_CATEGORIES)},
            "is_active": {"$ne": False},
        }
        if category and category in TRANSPORT_CAPABLE_CATEGORIES:
            em_query["category"] = category
        if q:
            em_query["$or"] = [
                {"asset_id": safe_regex(q)},
                {"unit_number": safe_regex(q)},
                {"make_model": safe_regex(q)},
                {"vin_serial_number": safe_regex(q)},
                {"plate": safe_regex(q)},
                {"display_label": safe_regex(q)},
            ]
        # Pull all transport overlays once, build a lookup by equipment_id.
        overlays = await db.transport_trucks.find(
            {"tenant": TENANT}).to_list(2000)
        overlay_by_eq = {o["equipment_id"]: o for o in overlays
                         if o.get("equipment_id")}

        items: List[Dict[str, Any]] = []
        masci_total = 0
        async for em in db.equipment_master.find(em_query).limit(limit):
            masci_total += 1
            overlay = overlay_by_eq.get(em.get("id"))
            tx_status = (overlay or {}).get("status")
            tx_safety_hold = bool((overlay or {}).get("safety_hold"))
            if status and tx_status != status:
                continue
            if ownership and ownership != "masci_owned":
                continue
            items.append({
                "id": em.get("id"),
                "source": "equipment_master",
                "asset_id": em.get("asset_id"),
                "unit_number": em.get("unit_number") or em.get("asset_id"),
                "label": em.get("display_label") or em.get("label"),
                "make": em.get("make"),
                "model": em.get("model"),
                "year": em.get("year"),
                "make_model": em.get("make_model"),
                "vin": em.get("vin_serial_number"),
                "plate": em.get("plate"),
                "category": em.get("category"),
                "preop_equipment_type": em.get("preop_equipment_type"),
                "ownership": "masci_owned",
                "carrier_id": (overlay or {}).get("carrier_id"),
                "operational_status": em.get("operational_status")
                    or em.get("status"),
                "current_project": em.get("current_project_name"),
                "current_location": em.get("current_location"),
                "last_inspection_at": em.get("last_inspection_at"),
                "last_inspection_result": em.get("last_inspection_result"),
                "next_inspection_due": em.get("next_inspection_due"),
                "transport_overlay": {
                    "exists": overlay is not None,
                    "truck_id": (overlay or {}).get("id"),
                    "truck_number": (overlay or {}).get("truck_number"),
                    "truck_type": (overlay or {}).get("truck_type"),
                    "status": tx_status,
                    "safety_hold": tx_safety_hold,
                    "notes": (overlay or {}).get("notes"),
                },
            })

        # 2. Leased / owner-operator fleet (lives only in transport_trucks).
        leased_total = 0
        for o in overlays:
            own = o.get("ownership")
            if own in ("leased_carrier", "owner_operator"):
                leased_total += 1
                if category:  # MASCI fleet filter — exclude leased rows
                    continue
                if ownership and own != ownership:
                    continue
                if status and o.get("status") != status:
                    continue
                if q:
                    blob = " ".join(str(v or "") for v in (
                        o.get("truck_number"), o.get("vin"),
                        o.get("plate"), o.get("truck_type"),
                    )).lower()
                    if q.lower() not in blob:
                        continue
                items.append({
                    "id": o.get("id"),
                    "source": "transport_trucks",
                    "asset_id": o.get("truck_number"),
                    "unit_number": o.get("truck_number"),
                    "label": (
                        f"{o.get('truck_number')} · "
                        f"{(o.get('truck_type') or 'truck').replace('_',' ').title()}"
                    ),
                    "make": None,
                    "model": None,
                    "year": None,
                    "make_model": None,
                    "vin": o.get("vin"),
                    "plate": o.get("plate"),
                    "category": "Leased / Owner-Operator",
                    "preop_equipment_type": "Haul Truck",
                    "ownership": own,
                    "carrier_id": o.get("carrier_id"),
                    "operational_status": o.get("status"),
                    "current_project": None,
                    "current_location": None,
                    "last_inspection_at": None,
                    "last_inspection_result": None,
                    "next_inspection_due": None,
                    "transport_overlay": {
                        "exists": True,
                        "truck_id": o.get("id"),
                        "truck_number": o.get("truck_number"),
                        "truck_type": o.get("truck_type"),
                        "status": o.get("status"),
                        "safety_hold": bool(o.get("safety_hold")),
                        "notes": o.get("notes"),
                    },
                })

        # Adopted summary (MASCI rows with a transport overlay).
        adopted = sum(1 for it in items
                      if it["source"] == "equipment_master"
                      and it["transport_overlay"]["exists"])
        return {
            "count": len(items),
            "items": items,
            "summary": {
                "masci_fleet_total": masci_total,
                "masci_fleet_adopted": adopted,
                "leased_total": leased_total,
                "categories": list(TRANSPORT_CAPABLE_CATEGORIES),
            },
        }

    # Track 19.02A · helpers for adoption + classification.
    def _derive_truck_type(category: str) -> str:
        cat = (category or "").lower()
        if "dump" in cat:
            return "dump_truck"
        if "water" in cat:
            return "tanker"
        if "service" in cat:
            return "service_truck"
        if "trailer" in cat:
            return "lowboy"
        if "flatbed" in cat:
            return "other"
        if "tractor" in cat:
            return "other"
        return "other"

    def _derive_transportation_classification(em: dict) -> str:
        """Best-effort default classification. Operator can refine via PATCH."""
        cat = (em.get("category") or "").lower()
        peq = (em.get("preop_equipment_type") or "").lower()
        if "dump" in cat:
            return "end_dump"
        if "tractor" in cat:
            return "day_cab"
        if "water" in cat or "water" in peq:
            return "water_truck"
        if "service" in cat:
            return "service_truck"
        if "flatbed" in cat:
            return "flatbed"
        if "trailer" in cat:
            return "equipment_trailer"
        return "other"

    def _build_overlay_doc(em: dict, actor: Any, batch_id: Optional[str] = None) -> dict:
        now = _now()
        truck_type = _derive_truck_type(em.get("category") or "")
        tx_class = _derive_transportation_classification(em)
        return {
            "id": uuid.uuid4().hex,
            "tenant": TENANT,
            "ownership": "masci_owned",
            "equipment_id": em.get("id"),
            "carrier_id": None,
            "driver_id": None,
            "truck_number": em.get("asset_id")
                or em.get("unit_number")
                or f"EQ-{(em.get('id') or '')[:6]}",
            "vin": em.get("vin_serial_number"),
            "plate": em.get("plate"),
            "truck_type": truck_type,
            "transportation_classification": tx_class,
            "status": "pending_review",
            "safety_hold": False,
            "dispatch_ready": False,
            "active_for_transport": True,
            "primary_division": None,
            "operational_tags": [],
            "transportation_notes": None,
            "notes": (
                f"Adopted from equipment_master · "
                f"{em.get('display_label') or em.get('label') or em.get('make_model') or ''}"
            ),
            "bulk_adoption_batch_id": batch_id,
            "created_at": now,
            "updated_at": now,
            "created_by": _actor_label(actor),
            "updated_by": _actor_label(actor),
        }

    # ─────────── Adoption Preview (READ-ONLY · no writes) ───────────
    @router.get("/admin/transportation/fleet/adoption-preview")
    async def fleet_adoption_preview(
        include_inactive: bool = Query(False),
        _: Any = Depends(require_dispatch_or_admin_dep),
    ):
        em_query: Dict[str, Any] = {
            "category": {"$in": list(TRANSPORT_CAPABLE_CATEGORIES)},
        }
        if not include_inactive:
            em_query["is_active"] = {"$ne": False}
        existing_overlays = await db.transport_trucks.find(
            {"tenant": TENANT}).to_list(2000)
        overlay_by_eq: Dict[str, dict] = {}
        for o in existing_overlays:
            eq_id = o.get("equipment_id")
            if eq_id:
                # Track duplicate-overlay risk: multiple overlays per eq.
                overlay_by_eq.setdefault(eq_id, []).append(o)

        already: List[dict] = []
        would_adopt: List[dict] = []
        skipped_inactive: List[dict] = []
        skipped_retired: List[dict] = []
        conflicts: List[dict] = []
        missing_equipment_id: List[dict] = []
        unknown_classification: List[dict] = []
        category_totals: Dict[str, int] = {}

        async for em in db.equipment_master.find(em_query):
            cat = em.get("category")
            category_totals[cat] = category_totals.get(cat, 0) + 1
            eq_id = em.get("id")
            row = {
                "equipment_id": eq_id,
                "asset_id": em.get("asset_id"),
                "category": cat,
                "make_model": em.get("make_model"),
                "vin": em.get("vin_serial_number"),
                "is_active": em.get("is_active"),
                "operational_status": em.get("operational_status"),
                "proposed_truck_type": _derive_truck_type(cat),
                "proposed_classification":
                    _derive_transportation_classification(em),
            }
            if not eq_id:
                missing_equipment_id.append(row)
                continue
            overlays = overlay_by_eq.get(eq_id, [])
            if len(overlays) > 1:
                conflicts.append({**row,
                    "reason": "multiple existing overlays",
                    "overlay_ids": [o.get("id") for o in overlays]})
                continue
            if overlays:
                already.append({**row, "overlay_id": overlays[0].get("id")})
                continue
            op_status = em.get("operational_status")
            if op_status == "Retired":
                skipped_retired.append({**row, "reason": "Retired"})
                continue
            if em.get("is_active") is False:
                skipped_inactive.append({**row, "reason": "is_active=False"})
                continue
            # Classification can't be derived → flag.
            if row["proposed_classification"] == "other" \
                    and cat in ("Misc Trucks",):
                unknown_classification.append({
                    **row, "reason":
                    "category 'Misc Trucks' needs operator classification"})
            would_adopt.append(row)

        # Existing leased-only rows (no equipment_id) — list for visibility.
        leased_only = [
            {"overlay_id": o.get("id"),
             "truck_number": o.get("truck_number"),
             "ownership": o.get("ownership"),
             "status": o.get("status")}
            for o in existing_overlays
            if not o.get("equipment_id")
        ]

        return {
            "snapshot_at": _now(),
            "categories_in_scope": list(TRANSPORT_CAPABLE_CATEGORIES),
            "category_totals": category_totals,
            "summary": {
                "already_adopted": len(already),
                "would_adopt": len(would_adopt),
                "skipped_inactive": len(skipped_inactive),
                "skipped_retired": len(skipped_retired),
                "conflicts": len(conflicts),
                "missing_equipment_id": len(missing_equipment_id),
                "unknown_classification": len(unknown_classification),
                "leased_only_overlays": len(leased_only),
            },
            "buckets": {
                "already_adopted": already,
                "would_adopt": would_adopt,
                "skipped_inactive": skipped_inactive,
                "skipped_retired": skipped_retired,
                "conflicts": conflicts,
                "missing_equipment_id": missing_equipment_id,
                "unknown_classification": unknown_classification,
                "leased_only_overlays": leased_only,
            },
            "disclaimer": (
                "Read-only preview · no records were modified. "
                "Equipment Master remains the source of truth."
            ),
        }

    # ─────────── Bulk Adoption (admin-only · idempotent) ───────────
    @router.post("/admin/transportation/fleet/adoption-bulk")
    async def fleet_adoption_bulk(
        request: Request,
        actor: Any = Depends(require_admin_dep),
    ):
        body = {}
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001
            pass
        include_inactive = bool(body.get("include_inactive", False))
        dry_run = bool(body.get("dry_run", False))

        em_query: Dict[str, Any] = {
            "category": {"$in": list(TRANSPORT_CAPABLE_CATEGORIES)},
        }
        if not include_inactive:
            em_query["is_active"] = {"$ne": False}

        # Build lookup of existing overlays so we never duplicate.
        existing = await db.transport_trucks.find(
            {"tenant": TENANT,
             "equipment_id": {"$ne": None, "$exists": True}},
        ).to_list(5000)
        adopted_eq_ids = {o.get("equipment_id") for o in existing
                          if o.get("equipment_id")}

        batch_id = uuid.uuid4().hex
        t0 = datetime.now(timezone.utc)
        created_docs: List[dict] = []
        skipped = 0
        retired = 0
        scanned = 0

        async for em in db.equipment_master.find(em_query):
            scanned += 1
            eq_id = em.get("id")
            if not eq_id:
                skipped += 1
                continue
            if eq_id in adopted_eq_ids:
                skipped += 1
                continue
            if em.get("operational_status") == "Retired":
                retired += 1
                continue
            doc = _build_overlay_doc(em, actor, batch_id=batch_id)
            created_docs.append(doc)
            adopted_eq_ids.add(eq_id)

        elapsed_ms = int(
            (datetime.now(timezone.utc) - t0).total_seconds() * 1000)

        if dry_run or not created_docs:
            summary = {
                "scanned": scanned,
                "created": 0 if dry_run else 0,
                "skipped_already_adopted": skipped,
                "skipped_retired": retired,
                "errors": 0,
                "elapsed_ms": elapsed_ms,
                "dry_run": dry_run,
                "batch_id": None if dry_run else batch_id,
                "would_create": len(created_docs) if dry_run else 0,
            }
            return {"success": True, **summary, "created_overlays": []}

        # Batch insert.
        try:
            await db.transport_trucks.insert_many(
                [d.copy() for d in created_docs], ordered=False)
        except Exception as exc:  # noqa: BLE001
            # Partial-failure recovery: fall back to per-doc upsert with
            # the (tenant, equipment_id) uniqueness contract.
            for d in created_docs:
                try:
                    await db.transport_trucks.update_one(
                        {"tenant": TENANT, "equipment_id": d["equipment_id"]},
                        {"$setOnInsert": d}, upsert=True)
                except Exception:  # noqa: BLE001
                    continue
            await _audit(db, kind="transport_bulk_adoption_completed",
                         entity_type="bulk", entity_id=batch_id,
                         actor=actor, old=None, request=request,
                         new={"error": str(exc)[:240],
                              "scanned": scanned, "elapsed_ms": elapsed_ms})
        # Per-overlay audit + eligibility init.
        for d in created_docs:
            await _audit(db, kind="transport_asset_adopt",
                         entity_type="truck", entity_id=d["id"],
                         actor=actor, old=None, new=_project_doc(d),
                         request=request)
            await _upsert_eligibility(db, target_type="truck",
                                      target_id=d["id"], record=d)
        await _audit(db, kind="transport_bulk_adoption_completed",
                     entity_type="bulk", entity_id=batch_id,
                     actor=actor, old=None, request=request,
                     new={
                         "scanned": scanned,
                         "created": len(created_docs),
                         "skipped_already_adopted": skipped,
                         "skipped_retired": retired,
                         "elapsed_ms": elapsed_ms,
                     })

        return {
            "success": True,
            "scanned": scanned,
            "created": len(created_docs),
            "skipped_already_adopted": skipped,
            "skipped_retired": retired,
            "errors": 0,
            "elapsed_ms": elapsed_ms,
            "dry_run": False,
            "batch_id": batch_id,
            "created_overlays": [
                {"id": d["id"], "equipment_id": d["equipment_id"],
                 "truck_number": d["truck_number"]} for d in created_docs
            ],
        }

    # Per-equipment "Adopt into Transportation" overlay creation.
    @router.post(
        "/admin/transportation/fleet/equipment/{equipment_id}/adopt")
    async def adopt_equipment_into_transport(
        equipment_id: str, request: Request,
        actor: Any = Depends(require_admin_dep),
    ):
        em = await db.equipment_master.find_one({"id": equipment_id})
        if not em:
            raise HTTPException(404, "equipment_master row not found")
        if em.get("category") not in TRANSPORT_CAPABLE_CATEGORIES:
            raise HTTPException(
                422,
                f"equipment category '{em.get('category')}' is not "
                "transportation-capable")
        existing = await db.transport_trucks.find_one(
            {"tenant": TENANT, "equipment_id": equipment_id})
        if existing:
            return {"already_adopted": True, **_project_doc(existing)}
        doc = _build_overlay_doc(em, actor)
        await db.transport_trucks.insert_one(doc.copy())
        await _audit(db, kind="transport_asset_adopt",
                     entity_type="truck", entity_id=doc["id"],
                     actor=actor, old=None, new=_project_doc(doc),
                     request=request)
        await _upsert_eligibility(db, target_type="truck",
                                  target_id=doc["id"], record=doc)
        return {"already_adopted": False, **_project_doc(doc)}

    # ─────────── Bulk Adoption Rollback (admin-only) ───────────
    @router.post(
        "/admin/transportation/fleet/adoption-bulk/{batch_id}/rollback")
    async def fleet_adoption_rollback(
        batch_id: str, request: Request,
        actor: Any = Depends(require_admin_dep),
    ):
        if not batch_id or len(batch_id) < 8:
            raise HTTPException(422, "invalid batch_id")
        # Only remove overlays produced by the named bulk batch.
        overlay_query = {"tenant": TENANT, "bulk_adoption_batch_id": batch_id}
        # Stream ALL overlay ids for this batch so rollback + eligibility
        # cleanup + the removed count are never truncated at a fixed cap.
        ids = [o["id"] async for o in db.transport_trucks.find(
            overlay_query, {"_id": 0, "id": 1}) if o.get("id")]
        if not ids:
            return {"success": True, "batch_id": batch_id,
                    "removed": 0,
                    "message": "no overlays match this batch_id"}
        await db.transport_trucks.delete_many(overlay_query)
        await db.transport_eligibility_state.delete_many(
            {"target_type": "truck", "target_id": {"$in": ids}})
        await _audit(db, kind="transport_bulk_adoption_rolled_back",
                     entity_type="bulk", entity_id=batch_id,
                     actor=actor, old={"overlay_count": len(ids)},
                     new={"removed": len(ids)}, request=request)
        return {"success": True, "batch_id": batch_id,
                "removed": len(ids),
                "removed_overlay_ids": ids}

    # ─────────── Operational Overlay PATCH (Track 19.02A Amendment) ───────────
    @router.patch(
        "/admin/transportation/fleet/equipment/{equipment_id}/overlay")
    async def patch_overlay_by_equipment(
        equipment_id: str, request: Request,
        actor: Any = Depends(require_dispatch_or_admin_dep),
    ):
        body = {}
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001
            raise HTTPException(400, "invalid JSON body")
        if not body:
            return {"success": True, "no_changes": True}

        # Block any attempt to edit enterprise-owned fields.
        protected_hit = [k for k in body.keys()
                         if k in TRANSPORT_OVERLAY_PROTECTED_FIELDS]
        if protected_hit:
            raise HTTPException(
                422,
                {
                    "message": (
                        "These fields are managed by the Enterprise "
                        "Equipment system and cannot be edited from "
                        "Transportation."
                    ),
                    "protected_fields": protected_hit,
                })
        # Restrict to known editable fields (silent drop unknown keys).
        updates: Dict[str, Any] = {
            k: v for k, v in body.items()
            if k in TRANSPORT_OVERLAY_EDITABLE_FIELDS
        }
        if not updates:
            raise HTTPException(
                422,
                {"message": "no editable fields supplied",
                 "editable_fields":
                 list(TRANSPORT_OVERLAY_EDITABLE_FIELDS)})
        # Validate enums.
        if "transportation_classification" in updates and \
                updates["transportation_classification"] \
                not in TRANSPORT_CLASSIFICATIONS:
            raise HTTPException(
                422, f"invalid transportation_classification; allowed: "
                f"{list(TRANSPORT_CLASSIFICATIONS)}")
        if "truck_type" in updates and \
                updates["truck_type"] not in TRUCK_TYPES:
            raise HTTPException(
                422, f"invalid truck_type; allowed: {list(TRUCK_TYPES)}")
        if "status" in updates and \
                updates["status"] not in TRUCK_STATUSES:
            raise HTTPException(
                422, f"invalid status; allowed: {list(TRUCK_STATUSES)}")

        existing = await db.transport_trucks.find_one(
            {"tenant": TENANT, "equipment_id": equipment_id})
        if not existing:
            # Auto-adopt-on-edit not allowed — operator must adopt first.
            raise HTTPException(
                404,
                "No Transportation overlay exists for this equipment. "
                "Adopt it into Transportation first.")
        # Compute diff for audit.
        before = {k: existing.get(k) for k in updates.keys()}
        after = dict(updates)
        if before == after:
            return {"success": True, "no_changes": True,
                    **_project_doc(existing)}
        updates["updated_at"] = _now()
        updates["updated_by"] = _actor_label(actor)
        await db.transport_trucks.update_one(
            {"tenant": TENANT, "equipment_id": equipment_id},
            {"$set": updates})
        new_doc = await db.transport_trucks.find_one(
            {"tenant": TENANT, "equipment_id": equipment_id})
        await _audit(db, kind="transport_overlay_update",
                     entity_type="truck", entity_id=existing.get("id"),
                     actor=actor, old=before,
                     new={**after,
                          "_equipment_id": equipment_id,
                          "_changed_fields": list(after.keys())},
                     request=request)
        await _upsert_eligibility(db, target_type="truck",
                                  target_id=existing.get("id"),
                                  record=new_doc or existing)
        return {"success": True, **_project_doc(new_doc or existing)}

    # ─────────────────────── ELIGIBILITY · admin ───────────────────────
    @router.get("/admin/transportation/eligibility/{target_type}/{target_id}")
    async def get_eligibility(
        target_type: str, target_id: str,
        _: Any = Depends(require_dispatch_or_admin_dep),
    ):
        if target_type not in TARGET_TYPES:
            raise HTTPException(422, f"target_type must be one of {list(TARGET_TYPES)}")
        # Recompute on read (Phase 1: avoids stale rows in admin UI).
        record = await _resolve_record(db, target_type, target_id)
        if not record:
            raise HTTPException(404, f"{target_type} {target_id} not found")
        ctx = {}
        if target_type == "person" and record.get("kind") == "masci_employee":
            hr_ctx = await _hr_lifecycle_context(db, record.get("employee_id"))
            if hr_ctx:
                ctx.update(hr_ctx)
        row = await _upsert_eligibility(db, target_type=target_type,
                                        target_id=target_id, record=record,
                                        context=ctx)
        return row

    # ─────────────────────── DISPATCH · read-only ───────────────────────
    @router.get("/dispatch/transportation/eligible-drivers")
    async def dispatch_eligible_drivers(
        limit: int = Query(500, ge=1, le=2000),
        _: Any = Depends(require_dispatch_or_admin_dep),
    ):
        cur = db.transport_eligibility_state.find({
            "tenant": TENANT, "target_type": "person", "state": "eligible",
        }).limit(limit)
        rows = await cur.to_list(limit)
        out: List[Dict[str, Any]] = []
        for r in rows:
            p = await db.transport_persons.find_one(
                {"id": r.get("target_id"), "tenant": TENANT})
            if not p:
                continue
            out.append({
                "id": p["id"],
                "kind": p.get("kind"),
                "display_name": display_name(p),
                "carrier_id": p.get("carrier_id"),
                "employee_id": p.get("employee_id"),
                "status": p.get("status"),
                "state": r.get("state"),
            })
        return {"count": len(out), "items": out}

    @router.get("/dispatch/transportation/eligible-trucks")
    async def dispatch_eligible_trucks(
        limit: int = Query(500, ge=1, le=2000),
        _: Any = Depends(require_dispatch_or_admin_dep),
    ):
        cur = db.transport_eligibility_state.find({
            "tenant": TENANT, "target_type": "truck", "state": "eligible",
        }).limit(limit)
        rows = await cur.to_list(limit)
        out: List[Dict[str, Any]] = []
        for r in rows:
            t = await db.transport_trucks.find_one(
                {"id": r.get("target_id"), "tenant": TENANT})
            if not t:
                continue
            out.append({
                "id": t["id"],
                "truck_number": t.get("truck_number"),
                "ownership": t.get("ownership"),
                "truck_type": t.get("truck_type"),
                "carrier_id": t.get("carrier_id"),
                "equipment_id": t.get("equipment_id"),
                "status": t.get("status"),
                "state": r.get("state"),
            })
        return {"count": len(out), "items": out}

    @router.get("/dispatch/transportation/status/{target_type}/{target_id}")
    async def dispatch_status(
        target_type: str, target_id: str,
        _: Any = Depends(require_dispatch_or_admin_dep),
    ):
        if target_type not in TARGET_TYPES:
            raise HTTPException(422, f"target_type must be one of {list(TARGET_TYPES)}")
        row = await db.transport_eligibility_state.find_one({
            "tenant": TENANT, "target_type": target_type, "target_id": target_id,
        })
        if not row:
            # Compute on first read.
            record = await _resolve_record(db, target_type, target_id)
            if not record:
                raise HTTPException(404, f"{target_type} {target_id} not found")
            ctx = {}
            if target_type == "person" and record.get("kind") == "masci_employee":
                hr_ctx = await _hr_lifecycle_context(
                    db, record.get("employee_id"))
                if hr_ctx:
                    ctx.update(hr_ctx)
            row = await _upsert_eligibility(db, target_type=target_type,
                                            target_id=target_id, record=record,
                                            context=ctx)
        return _project_doc(row)

    app.include_router(router)
    return router


async def _resolve_record(db, target_type: str, target_id: str
                          ) -> Optional[Dict[str, Any]]:
    """Fetch the underlying record for an eligibility target."""
    coll = {
        "carrier": "carriers",
        "person": "transport_persons",
        "truck": "transport_trucks",
    }[target_type]
    return await db[coll].find_one({"id": target_id, "tenant": TENANT})

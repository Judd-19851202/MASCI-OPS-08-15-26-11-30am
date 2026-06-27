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
TARGET_TYPES = ("carrier", "person", "truck")


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
    result = compute_transport_eligibility(rt, record, context)
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
    """Resolve HR lifecycle for a MASCI employee. Returns ``True`` /
    ``False`` / ``None`` (unknown). Phase 1 reads the canonical
    ``employees`` collection; if no row exists we return ``None`` (do
    not flip eligibility based on absence)."""
    if not employee_id:
        return None
    try:
        row = await db.employees.find_one(
            {"$or": [{"employee_id": employee_id}, {"id": employee_id}]},
            {"_id": 0, "status": 1, "is_active": 1, "terminated": 1,
             "lifecycle_status": 1},
        )
    except Exception:  # noqa: BLE001
        return None
    if not row:
        return None
    if row.get("terminated") is True:
        return False
    if row.get("is_active") is False:
        return False
    lc = (row.get("lifecycle_status") or row.get("status") or "").lower()
    if lc in ("terminated", "inactive", "on_leave", "leave", "separated"):
        return False
    return True


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
        _: Any = Depends(require_admin_dep),
    ):
        query: Dict[str, Any] = {"tenant": TENANT}
        if status:
            query["status"] = status
        if q:
            query["$or"] = [
                {"legal_name": {"$regex": q, "$options": "i"}},
                {"dba_name": {"$regex": q, "$options": "i"}},
                {"dot_number": {"$regex": q, "$options": "i"}},
            ]
        cur = db.carriers.find(query).sort("created_at", -1).limit(limit)
        items = [_project_doc(d) for d in await cur.to_list(limit)]
        return {"count": len(items), "items": items}

    @router.post("/admin/transportation/carriers")
    async def create_carrier(
        body: CarrierCreate, request: Request,
        actor: Any = Depends(require_admin_dep),
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
                          _: Any = Depends(require_admin_dep)):
        doc = await db.carriers.find_one({"id": cid, "tenant": TENANT})
        if not doc:
            raise HTTPException(404, "Carrier not found")
        return _project_doc(doc)

    @router.patch("/admin/transportation/carriers/{cid}")
    async def patch_carrier(cid: str, body: CarrierPatch, request: Request,
                            actor: Any = Depends(require_admin_dep)):
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
        _: Any = Depends(require_admin_dep),
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
                {"first_name": {"$regex": q, "$options": "i"}},
                {"last_name": {"$regex": q, "$options": "i"}},
                {"email": {"$regex": q, "$options": "i"}},
                {"license_number": {"$regex": q, "$options": "i"}},
            ]
        cur = db.transport_persons.find(query).sort("created_at", -1).limit(limit)
        items = [_project_doc(d) for d in await cur.to_list(limit)]
        return {"count": len(items), "items": items}

    @router.post("/admin/transportation/persons")
    async def create_person(body: PersonCreate, request: Request,
                            actor: Any = Depends(require_admin_dep)):
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
            ctx["hr_lifecycle_active"] = await _hr_lifecycle_active(db,
                                                                   doc["employee_id"])
        await _upsert_eligibility(db, target_type="person",
                                  target_id=doc["id"], record=doc, context=ctx)
        return _project_doc(doc)

    @router.get("/admin/transportation/persons/{pid}")
    async def get_person(pid: str, _: Any = Depends(require_admin_dep)):
        doc = await db.transport_persons.find_one({"id": pid, "tenant": TENANT})
        if not doc:
            raise HTTPException(404, "Transport person not found")
        return _project_doc(doc)

    @router.patch("/admin/transportation/persons/{pid}")
    async def patch_person(pid: str, body: PersonPatch, request: Request,
                           actor: Any = Depends(require_admin_dep)):
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
            ctx["hr_lifecycle_active"] = await _hr_lifecycle_active(db,
                                                                   new_doc.get("employee_id"))
        await _upsert_eligibility(db, target_type="person",
                                  target_id=pid, record=new_doc, context=ctx)
        return _project_doc(new_doc)

    # ─────────────────────── TRUCKS · admin ───────────────────────
    @router.get("/admin/transportation/trucks")
    async def list_trucks(
        q: Optional[str] = Query(None),
        ownership: Optional[str] = Query(None),
        carrier_id: Optional[str] = Query(None),
        status: Optional[str] = Query(None),
        limit: int = Query(200, ge=1, le=1000),
        _: Any = Depends(require_admin_dep),
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
                {"truck_number": {"$regex": q, "$options": "i"}},
                {"vin": {"$regex": q, "$options": "i"}},
                {"plate": {"$regex": q, "$options": "i"}},
            ]
        cur = db.transport_trucks.find(query).sort("created_at", -1).limit(limit)
        items = [_project_doc(d) for d in await cur.to_list(limit)]
        return {"count": len(items), "items": items}

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
    async def get_truck(tid: str, _: Any = Depends(require_admin_dep)):
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

    # ─────────────────────── ELIGIBILITY · admin ───────────────────────
    @router.get("/admin/transportation/eligibility/{target_type}/{target_id}")
    async def get_eligibility(
        target_type: str, target_id: str,
        _: Any = Depends(require_admin_dep),
    ):
        if target_type not in TARGET_TYPES:
            raise HTTPException(422, f"target_type must be one of {list(TARGET_TYPES)}")
        # Recompute on read (Phase 1: avoids stale rows in admin UI).
        record = await _resolve_record(db, target_type, target_id)
        if not record:
            raise HTTPException(404, f"{target_type} {target_id} not found")
        ctx = {}
        if target_type == "person" and record.get("kind") == "masci_employee":
            ctx["hr_lifecycle_active"] = await _hr_lifecycle_active(db,
                                                                   record.get("employee_id"))
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
                ctx["hr_lifecycle_active"] = await _hr_lifecycle_active(
                    db, record.get("employee_id"))
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

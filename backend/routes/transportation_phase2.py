"""TRACK 16.05 · Transportation Onboarding & Compliance Center routes.

Rate schedules · carrier/driver documents · packet workflow · MASCI
Hauler Truck Readiness Inspection · dashboards.

Mounted via ``register_transportation_phase2_routes(app, db,
require_admin_dep, require_dispatch_or_admin_dep)``. The two gates are
built by ``routes/transportation.register_transportation_routes`` and
re-used here (admin-strict for every write; admin OR dispatch for the
read-only dashboards).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional

from fastapi import (
    APIRouter, Depends, File, Form, Header, HTTPException, Path, Query,
    Request, UploadFile,
)
from pydantic import BaseModel, Field

from lib.transport_phase2 import (
    TENANT, DEFAULT_HOURLY_RATE, DEFAULT_CURRENCY,
    PAYMENT_RULES_TEXT, TICKET_RULES_TEXT, DEDUCTION_RULES_TEXT,
    DOCUMENT_TYPES_CARRIER, DOCUMENT_TYPES_DRIVER, REVIEW_STATUSES,
    PACKET_STATUSES, PACKET_TRANSITIONS, REQUIREMENTS_CATALOG,
    INSPECTION_DISCLAIMER, INSPECTION_VERSION, INSPECTION_TYPE,
    INSPECTION_TRIGGERS, ITEM_STATUSES, RESULT_STATUSES,
    INSPECTION_CHECKLIST, derive_inspection_result, compute_next_due,
    inspection_item_keys, critical_inspection_keys,
    INSPECTION_DEFAULT_EXPIRATION_MONTHS,
)
from lib.transport_eligibility import compute_transport_eligibility

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic shapes.
# ---------------------------------------------------------------------------
class RateScheduleCreate(BaseModel):
    hourly_rate: float = Field(..., gt=0)
    currency: str = Field(DEFAULT_CURRENCY, max_length=8)
    effective_date: Optional[str] = None
    payment_rules_text: Optional[str] = None
    ticket_rules_text: Optional[str] = None
    deduction_rules_text: Optional[str] = None


class RateSchedulePatch(BaseModel):
    hourly_rate: Optional[float] = None
    payment_rules_text: Optional[str] = None
    ticket_rules_text: Optional[str] = None
    deduction_rules_text: Optional[str] = None


class PacketCreate(BaseModel):
    submitted_by_name: Optional[str] = None
    submitted_by_email: Optional[str] = None


class PacketTransition(BaseModel):
    target_status: str
    correction_notes: Optional[str] = None
    signature_payload: Optional[Dict[str, Any]] = None


class DocumentReview(BaseModel):
    status: str
    review_notes: Optional[str] = None
    expires_at: Optional[str] = None


class InspectionStart(BaseModel):
    trigger: str = "initial_onboarding"
    reason: Optional[str] = None
    inspector_name: str = Field(..., min_length=1, max_length=120)
    transport_person_id: Optional[str] = None


class InspectionItemPatch(BaseModel):
    key: str
    status: str
    notes: Optional[str] = None
    photo_keys: Optional[List[str]] = None


class InspectionComplete(BaseModel):
    items: Optional[List[InspectionItemPatch]] = None
    signature_payload: Optional[Dict[str, Any]] = None
    expires_in_months: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _actor_label(actor: Any) -> str:
    if isinstance(actor, dict):
        return str(actor.get("email") or actor.get("name") or actor.get("id") or "admin")
    return "admin"


def _project(d: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not d:
        return None
    return {k: v for k, v in d.items() if k != "_id"}


async def _audit(db, *, kind: str, entity_type: str, entity_id: str,
                 actor: Any, old, new, request: Optional[Request]) -> None:
    try:
        doc = {
            "id": uuid.uuid4().hex, "kind": kind, "entity_type": entity_type,
            "entity_id": entity_id, "actor": _actor_label(actor),
            "old": old, "new": new, "ts": _now(), "tenant": TENANT,
        }
        if request is not None:
            doc["route"] = str(request.url.path)
            doc["ip"] = (request.headers.get("x-forwarded-for") or
                         (request.client.host if request.client else "")) or None
            doc["ua"] = request.headers.get("user-agent")
        await db.audit_events.insert_one(doc)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"track 16.05 audit insert failed: {exc}")


async def _notify_admin_bell(db, *, kind: str, summary: str,
                             link: Optional[str] = None,
                             meta: Optional[Dict[str, Any]] = None) -> None:
    """Best-effort internal bell notification — writes a row into the
    canonical ``notifications`` collection. External carrier emails are
    documented (not fired) in Phase 2."""
    try:
        doc = {
            "id": uuid.uuid4().hex, "tenant": TENANT, "kind": kind,
            "summary": summary, "link": link, "meta": meta or {},
            "ts": _now(), "read": False, "audience": ["admin"],
        }
        await db.notifications.insert_one(doc)
    except Exception:  # noqa: BLE001
        pass  # never break workflow on notification failure


async def _required_carrier_document_keys(db) -> List[str]:
    """Carrier-level required document_type keys from the active
    requirements catalog. Falls back to the in-process catalog."""
    cur = db.transport_packet_requirements.find({
        "tenant": TENANT, "active": True, "required": True,
        "target_type": {"$in": ["carrier", "agreement"]},
        "document_type": {"$ne": None},
    })
    keys = [r["document_type"] async for r in cur]
    if not keys:
        keys = [r["document_type"] for r in REQUIREMENTS_CATALOG
                if r["required"] and r.get("document_type")
                and r["target_type"] in ("carrier", "agreement")]
    return list(set(keys))


async def _required_driver_document_keys(db) -> List[str]:
    cur = db.transport_packet_requirements.find({
        "tenant": TENANT, "active": True, "required": True,
        "target_type": "driver", "document_type": {"$ne": None},
    })
    keys = [r["document_type"] async for r in cur]
    if not keys:
        keys = [r["document_type"] for r in REQUIREMENTS_CATALOG
                if r["required"] and r.get("document_type")
                and r["target_type"] == "driver"]
    return list(set(keys))


async def _packet_eligibility_context(db, carrier_id: str
                                      ) -> Dict[str, Any]:
    pkt = await db.transport_packet_submissions.find_one(
        {"tenant": TENANT, "carrier_id": carrier_id},
        sort=[("created_at", -1)])
    if not pkt:
        return {"packet_status": None, "rate_acknowledged": False,
                "missing_required_docs": 0, "expired_required_docs": 0,
                "docs_needs_correction": 0}
    # Docs status rollup
    docs = await db.carrier_documents.find({
        "tenant": TENANT, "carrier_id": carrier_id,
    }).to_list(2000)
    required = set(await _required_carrier_document_keys(db))
    have_types = {d["document_type"] for d in docs if d.get("status") == "accepted"}
    missing = len(required - have_types)
    expired = sum(1 for d in docs if d.get("status") == "expired"
                  and d.get("document_type") in required)
    needs_corr = sum(1 for d in docs if d.get("status") == "needs_correction"
                     and d.get("document_type") in required)
    rate_ack = pkt.get("status") == "approved" and bool(pkt.get("rate_schedule_id"))
    return {
        "packet_status": pkt.get("status"),
        "rate_acknowledged": rate_ack,
        "missing_required_docs": missing,
        "expired_required_docs": expired,
        "docs_needs_correction": needs_corr,
    }


async def _latest_inspection(db, truck_id: str) -> Optional[Dict[str, Any]]:
    return await db.transport_truck_inspections.find_one(
        {"tenant": TENANT, "transport_truck_id": truck_id},
        sort=[("inspected_at", -1)])


# ---------------------------------------------------------------------------
# Router factory
# ---------------------------------------------------------------------------
def register_transportation_phase2_routes(
    app, db,
    require_admin_dep: Callable,
    require_dispatch_or_admin_dep: Callable,
) -> APIRouter:
    """Register Track 16.05 routes on the FastAPI app."""

    # Self-contained dispatch+admin gate that honors the canonical per-user
    # admin token (Track 15.32 directory) AND dispatch portal tokens. The
    # platform-wide ``_shared_dispatch_or_admin`` factory still consults the
    # retired sync admin validator and would reject every modern admin
    # token, so we build a local gate (mirrors routes/transportation.py).
    async def _local_dispatch_or_admin(
        request: Request,
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
        x_dispatch_token: Optional[str] = Header(default=None, alias="X-Dispatch-Token"),
    ) -> Dict[str, Any]:
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

    require_dispatch_or_admin_dep = _local_dispatch_or_admin  # noqa: F811

    router = APIRouter(prefix="/api", tags=["transportation-phase2"])

    # =========================================================
    # RATE SCHEDULES
    # =========================================================
    @router.get("/admin/transportation/rate-schedules")
    async def list_rates(_: Any = Depends(require_admin_dep)):
        cur = db.transport_rate_schedules.find({"tenant": TENANT}).sort("effective_date", -1)
        return {"items": [_project(d) for d in await cur.to_list(500)]}

    @router.post("/admin/transportation/rate-schedules")
    async def create_rate(body: RateScheduleCreate, request: Request,
                          actor: Any = Depends(require_admin_dep)):
        now = _now()
        cur = db.transport_rate_schedules.find({"tenant": TENANT})
        existing = await cur.to_list(500)
        version = str(max([int(x.get("version", "0") or 0) for x in existing] + [0]) + 1)
        doc = {
            "id": uuid.uuid4().hex, "tenant": TENANT, "version": version,
            "hourly_rate": float(body.hourly_rate), "currency": body.currency,
            "effective_date": body.effective_date or now,
            "status": "draft",
            "payment_rules_text": body.payment_rules_text or PAYMENT_RULES_TEXT,
            "ticket_rules_text": body.ticket_rules_text or TICKET_RULES_TEXT,
            "deduction_rules_text": body.deduction_rules_text or DEDUCTION_RULES_TEXT,
            "created_at": now, "updated_at": now,
            "created_by": _actor_label(actor), "updated_by": _actor_label(actor),
        }
        await db.transport_rate_schedules.insert_one(doc.copy())
        await _audit(db, kind="transport_rate_schedule_create",
                     entity_type="rate_schedule", entity_id=doc["id"],
                     actor=actor, old=None, new=_project(doc), request=request)
        return _project(doc)

    @router.patch("/admin/transportation/rate-schedules/{rid}")
    async def patch_rate(rid: str, body: RateSchedulePatch, request: Request,
                         actor: Any = Depends(require_admin_dep)):
        existing = await db.transport_rate_schedules.find_one(
            {"id": rid, "tenant": TENANT})
        if not existing:
            raise HTTPException(404, "Rate schedule not found")
        if existing.get("status") == "retired":
            raise HTTPException(409, "Retired schedules are read-only")
        updates: Dict[str, Any] = {}
        for f in ("hourly_rate", "payment_rules_text", "ticket_rules_text",
                  "deduction_rules_text"):
            v = getattr(body, f)
            if v is not None:
                updates[f] = v if f != "hourly_rate" else float(v)
        if not updates:
            return _project(existing)
        updates["updated_at"] = _now()
        updates["updated_by"] = _actor_label(actor)
        await db.transport_rate_schedules.update_one(
            {"_id": existing["_id"]}, {"$set": updates})
        new_doc = {**existing, **updates}
        await _audit(db, kind="transport_rate_schedule_update",
                     entity_type="rate_schedule", entity_id=rid,
                     actor=actor, old=_project(existing), new=_project(new_doc),
                     request=request)
        return _project(new_doc)

    @router.post("/admin/transportation/rate-schedules/{rid}/activate")
    async def activate_rate(rid: str, request: Request,
                            actor: Any = Depends(require_admin_dep)):
        target = await db.transport_rate_schedules.find_one(
            {"id": rid, "tenant": TENANT})
        if not target:
            raise HTTPException(404, "Rate schedule not found")
        if target.get("status") == "retired":
            raise HTTPException(409, "Cannot activate a retired schedule")
        now = _now()
        # Retire all currently-active schedules (preserving historical id/version).
        await db.transport_rate_schedules.update_many(
            {"tenant": TENANT, "status": "active", "id": {"$ne": rid}},
            {"$set": {"status": "retired", "updated_at": now,
                      "updated_by": _actor_label(actor)}}
        )
        await db.transport_rate_schedules.update_one(
            {"_id": target["_id"]},
            {"$set": {"status": "active", "effective_date":
                      target.get("effective_date") or now,
                      "updated_at": now, "updated_by": _actor_label(actor)}})
        new = await db.transport_rate_schedules.find_one({"_id": target["_id"]})
        await _audit(db, kind="transport_rate_schedule_activate",
                     entity_type="rate_schedule", entity_id=rid,
                     actor=actor, old=_project(target), new=_project(new),
                     request=request)
        await _notify_admin_bell(db, kind="transport_rate_activated",
                                 summary=f"Rate schedule v{new.get('version')} "
                                         f"activated at ${new.get('hourly_rate')}/hr",
                                 meta={"rate_schedule_id": rid})
        return _project(new)

    # =========================================================
    # PACKET WORKFLOW
    # =========================================================
    @router.get("/admin/transportation/carriers/{cid}/packet")
    async def get_packet(cid: str, _: Any = Depends(require_admin_dep)):
        pkt = await db.transport_packet_submissions.find_one(
            {"tenant": TENANT, "carrier_id": cid},
            sort=[("created_at", -1)])
        return _project(pkt) or {}

    @router.post("/admin/transportation/carriers/{cid}/packet")
    async def create_packet(cid: str, body: PacketCreate, request: Request,
                            actor: Any = Depends(require_admin_dep)):
        carrier = await db.carriers.find_one({"id": cid, "tenant": TENANT})
        if not carrier:
            raise HTTPException(404, "Carrier not found")
        active_rate = await db.transport_rate_schedules.find_one(
            {"tenant": TENANT, "status": "active"})
        if not active_rate:
            raise HTTPException(409, "No active rate schedule — bootstrap missing")
        now = _now()
        doc = {
            "id": uuid.uuid4().hex, "tenant": TENANT, "carrier_id": cid,
            "packet_version": "1", "rate_schedule_id": active_rate["id"],
            "status": "draft",
            "submitted_by_name": body.submitted_by_name,
            "submitted_by_email": body.submitted_by_email,
            "submitted_at": None, "reviewed_by": None, "reviewed_at": None,
            "correction_notes": None, "signed_agreement_file_key": None,
            "signature_payload": None,
            "created_at": now, "updated_at": now,
        }
        await db.transport_packet_submissions.insert_one(doc.copy())
        await _audit(db, kind="transport_packet_create",
                     entity_type="packet", entity_id=doc["id"],
                     actor=actor, old=None, new=_project(doc), request=request)
        return _project(doc)

    @router.patch("/admin/transportation/packets/{pid}")
    async def patch_packet(pid: str, body: PacketTransition, request: Request,
                           actor: Any = Depends(require_admin_dep)):
        pkt = await db.transport_packet_submissions.find_one(
            {"id": pid, "tenant": TENANT})
        if not pkt:
            raise HTTPException(404, "Packet not found")
        new_status = body.target_status
        if new_status not in PACKET_STATUSES:
            raise HTTPException(422, f"target_status must be one of {list(PACKET_STATUSES)}")
        cur_status = pkt.get("status") or "draft"
        allowed = PACKET_TRANSITIONS.get(cur_status, set())
        if new_status not in allowed and new_status != cur_status:
            raise HTTPException(409,
                f"Transition {cur_status} → {new_status} not allowed")

        # Approval guards.
        if new_status == "approved":
            await _enforce_approval_guards(db, pkt)

        now = _now()
        upd = {"status": new_status, "updated_at": now}
        if body.correction_notes is not None:
            upd["correction_notes"] = body.correction_notes
        if body.signature_payload is not None:
            upd["signature_payload"] = body.signature_payload
        if new_status == "submitted" and not pkt.get("submitted_at"):
            upd["submitted_at"] = now
        if new_status in ("approved", "needs_correction"):
            upd["reviewed_by"] = _actor_label(actor)
            upd["reviewed_at"] = now
        await db.transport_packet_submissions.update_one(
            {"_id": pkt["_id"]}, {"$set": upd})
        new_doc = {**pkt, **upd}
        await _audit(db, kind=f"transport_packet_{new_status}",
                     entity_type="packet", entity_id=pid,
                     actor=actor, old=_project(pkt), new=_project(new_doc),
                     request=request)
        if new_status == "submitted":
            await _notify_admin_bell(db, kind="TRANSPORT_PACKET_SUBMITTED",
                summary=f"Hauler packet submitted for review (carrier {pkt.get('carrier_id')})",
                link=f"/admin/transportation?carrier={pkt.get('carrier_id')}",
                meta={"packet_id": pid})
        if new_status == "needs_correction":
            await _notify_admin_bell(db, kind="TRANSPORT_DOC_NEEDS_CORRECTION",
                summary=f"Packet returned for correction ({pkt.get('carrier_id')})",
                meta={"packet_id": pid})
        return _project(new_doc)

    @router.post("/admin/transportation/packets/{pid}/submit")
    async def submit_packet(pid: str, request: Request,
                            actor: Any = Depends(require_admin_dep)):
        return await patch_packet(pid, PacketTransition(target_status="submitted"),
                                  request, actor)

    @router.post("/admin/transportation/packets/{pid}/approve")
    async def approve_packet(pid: str, request: Request,
                             actor: Any = Depends(require_admin_dep)):
        return await patch_packet(pid, PacketTransition(target_status="approved"),
                                  request, actor)

    @router.post("/admin/transportation/packets/{pid}/needs-correction")
    async def needs_correction_packet(pid: str, body: PacketTransition,
                                      request: Request,
                                      actor: Any = Depends(require_admin_dep)):
        body.target_status = "needs_correction"
        return await patch_packet(pid, body, request, actor)

    async def _enforce_approval_guards(db, pkt: Dict[str, Any]) -> None:
        carrier_id = pkt["carrier_id"]
        # 1) rate schedule recorded
        if not pkt.get("rate_schedule_id"):
            raise HTTPException(409, "Cannot approve packet without rate schedule acknowledgement")
        # 2) all required carrier documents present and accepted, none expired or needs_correction
        docs = await db.carrier_documents.find(
            {"tenant": TENANT, "carrier_id": carrier_id}).to_list(2000)
        required = set(await _required_carrier_document_keys(db))
        accepted_types = {d["document_type"] for d in docs if d.get("status") == "accepted"}
        missing = required - accepted_types
        if missing:
            raise HTTPException(409, f"Cannot approve packet — missing required documents: {sorted(missing)}")
        if any(d.get("status") == "expired" and d.get("document_type") in required for d in docs):
            raise HTTPException(409, "Cannot approve packet — at least one required document is expired")
        if any(d.get("status") == "needs_correction" and d.get("document_type") in required for d in docs):
            raise HTTPException(409, "Cannot approve packet — at least one required document needs correction")

    # =========================================================
    # CARRIER DOCUMENTS (R2-backed)
    # =========================================================
    @router.get("/admin/transportation/carriers/{cid}/documents")
    async def list_carrier_docs(cid: str, _: Any = Depends(require_admin_dep)):
        cur = db.carrier_documents.find({"tenant": TENANT, "carrier_id": cid}
                                        ).sort("uploaded_at", -1)
        return {"items": [_project(d) for d in await cur.to_list(500)]}

    @router.post("/admin/transportation/carriers/{cid}/documents")
    async def upload_carrier_doc(
        cid: str, request: Request,
        document_type: str = Form(...),
        expires_at: Optional[str] = Form(None),
        file: UploadFile = File(...),
        actor: Any = Depends(require_admin_dep),
    ):
        if document_type not in DOCUMENT_TYPES_CARRIER:
            raise HTTPException(422, f"document_type must be one of {list(DOCUMENT_TYPES_CARRIER)}")
        carrier = await db.carriers.find_one({"id": cid, "tenant": TENANT})
        if not carrier:
            raise HTTPException(404, "Carrier not found")
        data = await file.read()
        key, ref = await _store_file(file, data, source_id=f"carrier-{cid}")
        doc = await _persist_doc(
            db, collection="carrier_documents",
            base={"carrier_id": cid}, document_type=document_type,
            file_key=key, ref=ref, file=file, expires_at=expires_at,
            actor=actor,
        )
        await _audit(db, kind="transport_carrier_document_upload",
                     entity_type="carrier_document", entity_id=doc["id"],
                     actor=actor, old=None, new=_project(doc), request=request)
        return _project(doc)

    @router.patch("/admin/transportation/documents/{doc_id}/review")
    async def review_carrier_doc(doc_id: str, body: DocumentReview,
                                 request: Request,
                                 actor: Any = Depends(require_admin_dep)):
        return await _review_doc(db, "carrier_documents", doc_id, body,
                                 request, actor)

    # =========================================================
    # DRIVER DOCUMENTS (R2-backed)
    # =========================================================
    @router.get("/admin/transportation/persons/{pid}/documents")
    async def list_driver_docs(pid: str, _: Any = Depends(require_admin_dep)):
        cur = db.driver_documents.find(
            {"tenant": TENANT, "transport_person_id": pid}
        ).sort("uploaded_at", -1)
        return {"items": [_project(d) for d in await cur.to_list(500)]}

    @router.post("/admin/transportation/persons/{pid}/documents")
    async def upload_driver_doc(
        pid: str, request: Request,
        document_type: str = Form(...),
        expires_at: Optional[str] = Form(None),
        file: UploadFile = File(...),
        actor: Any = Depends(require_admin_dep),
    ):
        if document_type not in DOCUMENT_TYPES_DRIVER:
            raise HTTPException(422, f"document_type must be one of {list(DOCUMENT_TYPES_DRIVER)}")
        person = await db.transport_persons.find_one(
            {"id": pid, "tenant": TENANT})
        if not person:
            raise HTTPException(404, "Driver not found")
        data = await file.read()
        key, ref = await _store_file(file, data, source_id=f"driver-{pid}")
        doc = await _persist_doc(
            db, collection="driver_documents",
            base={"transport_person_id": pid,
                  "carrier_id": person.get("carrier_id")},
            document_type=document_type,
            file_key=key, ref=ref, file=file, expires_at=expires_at,
            actor=actor,
        )
        await _audit(db, kind="transport_driver_document_upload",
                     entity_type="driver_document", entity_id=doc["id"],
                     actor=actor, old=None, new=_project(doc), request=request)
        return _project(doc)

    @router.patch("/admin/transportation/driver-documents/{doc_id}/review")
    async def review_driver_doc(doc_id: str, body: DocumentReview,
                                request: Request,
                                actor: Any = Depends(require_admin_dep)):
        return await _review_doc(db, "driver_documents", doc_id, body,
                                 request, actor)

    # =========================================================
    # MASCI HAULER TRUCK READINESS INSPECTION
    # =========================================================
    @router.get("/admin/transportation/trucks/{tid}/inspections")
    async def list_truck_inspections(tid: str, _: Any = Depends(require_admin_dep)):
        cur = db.transport_truck_inspections.find(
            {"tenant": TENANT, "transport_truck_id": tid}
        ).sort("inspected_at", -1)
        return {"items": [_project(d) for d in await cur.to_list(200)]}

    @router.post("/admin/transportation/trucks/{tid}/inspections")
    async def start_inspection(tid: str, body: InspectionStart,
                               request: Request,
                               actor: Any = Depends(require_admin_dep)):
        if body.trigger not in INSPECTION_TRIGGERS:
            raise HTTPException(422, f"trigger must be one of {list(INSPECTION_TRIGGERS)}")
        truck = await db.transport_trucks.find_one({"id": tid, "tenant": TENANT})
        if not truck:
            raise HTTPException(404, "Truck not found")
        now = _now()
        items = [
            {"key": k, "label": label, "category": cat, "status": "not_observed",
             "notes": None, "photo_keys": []}
            for (k, cat, label, _crit) in INSPECTION_CHECKLIST
        ]
        doc = {
            "id": uuid.uuid4().hex, "tenant": TENANT,
            "carrier_id": truck.get("carrier_id"),
            "transport_truck_id": tid,
            "transport_person_id": body.transport_person_id,
            "inspection_type": INSPECTION_TYPE,
            "inspection_version": INSPECTION_VERSION,
            "trigger": body.trigger, "reason": body.reason,
            "result": "pending_correction",
            "checklist_items": items,
            "inspector_name": body.inspector_name,
            "inspector_user_id": (actor or {}).get("id") if isinstance(actor, dict) else None,
            "inspected_at": now, "expires_at": None,
            "correction_due_at": None, "notes": None,
            "signature_payload": None,
            "disclaimer": INSPECTION_DISCLAIMER,
            "created_at": now, "updated_at": now,
            "audit_version": 1,
        }
        await db.transport_truck_inspections.insert_one(doc.copy())
        await _audit(db, kind="transport_inspection_started",
                     entity_type="truck_inspection", entity_id=doc["id"],
                     actor=actor, old=None, new=_project(doc), request=request)
        return _project(doc)

    @router.get("/admin/transportation/inspections/{iid}")
    async def get_inspection(iid: str, _: Any = Depends(require_admin_dep)):
        doc = await db.transport_truck_inspections.find_one(
            {"id": iid, "tenant": TENANT})
        if not doc:
            raise HTTPException(404, "Inspection not found")
        return _project(doc)

    @router.patch("/admin/transportation/inspections/{iid}")
    async def patch_inspection_items(iid: str,
                                     body: List[InspectionItemPatch],
                                     request: Request,
                                     actor: Any = Depends(require_admin_dep)):
        doc = await db.transport_truck_inspections.find_one(
            {"id": iid, "tenant": TENANT})
        if not doc:
            raise HTTPException(404, "Inspection not found")
        items = doc.get("checklist_items") or []
        valid_keys = set(inspection_item_keys())
        index = {it["key"]: it for it in items}
        for patch in body:
            if patch.key not in valid_keys:
                raise HTTPException(422, f"unknown checklist key: {patch.key}")
            if patch.status not in ITEM_STATUSES:
                raise HTTPException(422, f"status must be one of {list(ITEM_STATUSES)}")
            target = index.get(patch.key)
            if not target:
                continue
            target["status"] = patch.status
            if patch.notes is not None:
                target["notes"] = patch.notes
            if patch.photo_keys is not None:
                target["photo_keys"] = patch.photo_keys
        upd = {"checklist_items": items, "updated_at": _now(),
               "audit_version": (doc.get("audit_version") or 1) + 1}
        await db.transport_truck_inspections.update_one(
            {"_id": doc["_id"]}, {"$set": upd})
        new_doc = {**doc, **upd}
        await _audit(db, kind="transport_inspection_item_updated",
                     entity_type="truck_inspection", entity_id=iid,
                     actor=actor, old=_project(doc), new=_project(new_doc),
                     request=request)
        return _project(new_doc)

    @router.post("/admin/transportation/inspections/{iid}/complete")
    async def complete_inspection(iid: str, body: InspectionComplete,
                                  request: Request,
                                  actor: Any = Depends(require_admin_dep)):
        doc = await db.transport_truck_inspections.find_one(
            {"id": iid, "tenant": TENANT})
        if not doc:
            raise HTTPException(404, "Inspection not found")
        # Optionally apply final item patches in one shot.
        items = doc.get("checklist_items") or []
        if body.items:
            index = {it["key"]: it for it in items}
            valid_keys = set(inspection_item_keys())
            for patch in body.items:
                if patch.key not in valid_keys:
                    continue
                if patch.status not in ITEM_STATUSES:
                    raise HTTPException(422, f"status must be one of {list(ITEM_STATUSES)}")
                t = index.get(patch.key)
                if t:
                    t["status"] = patch.status
                    if patch.notes is not None:
                        t["notes"] = patch.notes
                    if patch.photo_keys is not None:
                        t["photo_keys"] = patch.photo_keys
        months = body.expires_in_months or INSPECTION_DEFAULT_EXPIRATION_MONTHS
        inspected_dt = datetime.now(timezone.utc)
        expires_at = compute_next_due(inspected_dt, months).isoformat()
        result = derive_inspection_result(items, expires_at=expires_at)
        upd = {
            "checklist_items": items, "result": result,
            "inspected_at": inspected_dt.isoformat(), "expires_at": expires_at,
            "signature_payload": body.signature_payload,
            "updated_at": _now(),
            "audit_version": (doc.get("audit_version") or 1) + 1,
        }
        await db.transport_truck_inspections.update_one(
            {"_id": doc["_id"]}, {"$set": upd})
        new_doc = {**doc, **upd}
        await _audit(db, kind="transport_inspection_completed",
                     entity_type="truck_inspection", entity_id=iid,
                     actor=actor, old=_project(doc), new=_project(new_doc),
                     request=request)
        await _notify_admin_bell(db, kind="TRANSPORT_INSPECTION_COMPLETED",
            summary=f"Readiness inspection {result.upper()} for truck "
                    f"{new_doc.get('transport_truck_id')}",
            meta={"inspection_id": iid, "result": result})
        # Recompute eligibility for the truck.
        truck = await db.transport_trucks.find_one(
            {"id": new_doc["transport_truck_id"], "tenant": TENANT})
        if truck:
            ctx = await _truck_eligibility_context(db, truck, new_doc)
            er = compute_transport_eligibility("truck", truck, ctx)
            await _upsert_elig_row(db, target_type="truck",
                                   target_id=truck["id"], result=er)
        return _project(new_doc)

    # =========================================================
    # ELIGIBILITY / DASHBOARDS (read)
    # =========================================================
    @router.get("/admin/transportation/eligibility/v2/{target_type}/{target_id}")
    async def get_eligibility_v2(target_type: str, target_id: str,
                                 _: Any = Depends(require_admin_dep)):
        if target_type not in ("carrier", "person", "truck"):
            raise HTTPException(422, "target_type invalid")
        if target_type == "truck":
            truck = await db.transport_trucks.find_one(
                {"id": target_id, "tenant": TENANT})
            if not truck:
                raise HTTPException(404, "Truck not found")
            insp = await _latest_inspection(db, target_id)
            ctx = await _truck_eligibility_context(db, truck, insp)
            res = compute_transport_eligibility("truck", truck, ctx)
            await _upsert_elig_row(db, target_type="truck",
                                   target_id=target_id, result=res)
            return res
        if target_type == "person":
            person = await db.transport_persons.find_one(
                {"id": target_id, "tenant": TENANT})
            if not person:
                raise HTTPException(404, "Driver not found")
            ctx = await _person_eligibility_context(db, person)
            res = compute_transport_eligibility("person", person, ctx)
            await _upsert_elig_row(db, target_type="person",
                                   target_id=target_id, result=res)
            return res
        carrier = await db.carriers.find_one(
            {"id": target_id, "tenant": TENANT})
        if not carrier:
            raise HTTPException(404, "Carrier not found")
        ctx = await _packet_eligibility_context(db, target_id)
        res = compute_transport_eligibility("carrier", carrier, ctx)
        await _upsert_elig_row(db, target_type="carrier",
                               target_id=target_id, result=res)
        return res

    @router.get("/dispatch/transportation/trucks/{tid}/readiness")
    async def dispatch_truck_readiness(tid: str,
                                       _: Any = Depends(require_dispatch_or_admin_dep)):
        truck = await db.transport_trucks.find_one(
            {"id": tid, "tenant": TENANT})
        if not truck:
            raise HTTPException(404, "Truck not found")
        insp = await _latest_inspection(db, tid)
        ctx = await _truck_eligibility_context(db, truck, insp)
        res = compute_transport_eligibility("truck", truck, ctx)
        return {
            "truck_id": tid, "result": res, "latest_inspection": _project(insp),
            "disclaimer": INSPECTION_DISCLAIMER,
        }

    @router.get("/dispatch/transportation/carriers/{cid}/packet-status")
    async def dispatch_packet_status(cid: str,
                                     _: Any = Depends(require_dispatch_or_admin_dep)):
        carrier = await db.carriers.find_one({"id": cid, "tenant": TENANT})
        if not carrier:
            raise HTTPException(404, "Carrier not found")
        ctx = await _packet_eligibility_context(db, cid)
        elig = compute_transport_eligibility("carrier", carrier, ctx)
        pkt = await db.transport_packet_submissions.find_one(
            {"tenant": TENANT, "carrier_id": cid},
            sort=[("created_at", -1)])
        return {"carrier_id": cid, "packet": _project(pkt),
                "eligibility": elig, "context": ctx}

    @router.get("/dispatch/transportation/readiness-summary")
    async def dispatch_readiness_summary(
        _: Any = Depends(require_dispatch_or_admin_dep),
    ):
        # Counts derived from the eligibility-state collection.
        out = {"by_target": {}, "inspections": {}, "documents": {}}
        for target_type in ("carrier", "person", "truck"):
            cur = db.transport_eligibility_state.find(
                {"tenant": TENANT, "target_type": target_type})
            rows = await cur.to_list(5000)
            buckets: Dict[str, int] = {}
            for r in rows:
                s = r.get("state") or "unknown"
                buckets[s] = buckets.get(s, 0) + 1
            out["by_target"][target_type] = buckets

        # Inspection upcoming / overdue (real-time, no cron).
        now = datetime.now(timezone.utc)
        soon_30 = (now + timedelta(days=30)).isoformat()
        soon_14 = (now + timedelta(days=14)).isoformat()
        soon_7 = (now + timedelta(days=7)).isoformat()
        soon_1 = (now + timedelta(days=1)).isoformat()
        cur = db.transport_truck_inspections.find({"tenant": TENANT})
        latest_per_truck: Dict[str, Dict[str, Any]] = {}
        for d in await cur.to_list(10000):
            t = d.get("transport_truck_id")
            if not t:
                continue
            cur_dt = latest_per_truck.get(t, {}).get("inspected_at")
            if cur_dt is None or (d.get("inspected_at") or "") > cur_dt:
                latest_per_truck[t] = d
        due_today = due_7 = due_14 = due_30 = overdue = ready = 0
        for d in latest_per_truck.values():
            exp = d.get("expires_at")
            if not exp:
                continue
            if exp < now.isoformat():
                overdue += 1
            elif exp < soon_1:
                due_today += 1
            elif exp < soon_7:
                due_7 += 1
            elif exp < soon_14:
                due_14 += 1
            elif exp < soon_30:
                due_30 += 1
            elif d.get("result") == "ready":
                ready += 1
        out["inspections"] = {
            "ready_current": ready, "due_within_30d": due_30,
            "due_within_14d": due_14, "due_within_7d": due_7,
            "due_today": due_today, "overdue": overdue,
            "policy_default_months": INSPECTION_DEFAULT_EXPIRATION_MONTHS,
        }

        # Document expirations.
        cur = db.carrier_documents.find({"tenant": TENANT,
                                         "expires_at": {"$ne": None}})
        cd_due = cd_overdue = 0
        for d in await cur.to_list(10000):
            exp = d.get("expires_at") or ""
            if not exp:
                continue
            if exp < now.isoformat():
                cd_overdue += 1
            elif exp < soon_30:
                cd_due += 1
        cur = db.driver_documents.find({"tenant": TENANT,
                                        "expires_at": {"$ne": None}})
        dd_due = dd_overdue = 0
        for d in await cur.to_list(10000):
            exp = d.get("expires_at") or ""
            if not exp:
                continue
            if exp < now.isoformat():
                dd_overdue += 1
            elif exp < soon_30:
                dd_due += 1
        out["documents"] = {
            "carrier_due_within_30d": cd_due, "carrier_overdue": cd_overdue,
            "driver_due_within_30d": dd_due, "driver_overdue": dd_overdue,
        }
        out["disclaimer"] = INSPECTION_DISCLAIMER
        return out

    # =========================================================
    # Helpers used by routes
    # =========================================================
    async def _truck_eligibility_context(db, truck: Dict[str, Any],
                                         latest_inspection: Optional[Dict[str, Any]]
                                         ) -> Dict[str, Any]:
        # Roll up packet status from owning carrier (if any).
        pkt_ctx: Dict[str, Any] = {}
        if truck.get("carrier_id"):
            pkt_ctx = await _packet_eligibility_context(db, truck["carrier_id"])
        insp_result = None
        if latest_inspection:
            # Re-derive in case expires_at has just crossed now.
            insp_result = derive_inspection_result(
                latest_inspection.get("checklist_items") or [],
                expires_at=latest_inspection.get("expires_at"))
        return {
            **pkt_ctx,
            "ownership": truck.get("ownership"),
            "inspection_required": truck.get("ownership") != "masci_owned",
            "inspection_result": insp_result,
        }

    async def _person_eligibility_context(db, person: Dict[str, Any]
                                          ) -> Dict[str, Any]:
        pkt_ctx: Dict[str, Any] = {}
        if person.get("kind") == "leased_driver" and person.get("carrier_id"):
            pkt_ctx = await _packet_eligibility_context(db, person["carrier_id"])
        # Driver doc rollup.
        docs = await db.driver_documents.find(
            {"tenant": TENANT, "transport_person_id": person["id"]}
        ).to_list(500)
        required = set(await _required_driver_document_keys(db))
        accepted = {d["document_type"] for d in docs if d.get("status") == "accepted"}
        missing = len(required - accepted)
        expired = sum(1 for d in docs if d.get("status") == "expired"
                      and d.get("document_type") in required)
        needs_corr = sum(1 for d in docs if d.get("status") == "needs_correction"
                         and d.get("document_type") in required)
        # PPE issue derived from latest related inspection.
        ppe_issue = False
        if person.get("id"):
            insp = await db.transport_truck_inspections.find_one(
                {"tenant": TENANT, "transport_person_id": person["id"]},
                sort=[("inspected_at", -1)])
            if insp:
                ppe_items = [it for it in (insp.get("checklist_items") or [])
                             if it.get("category") == "ppe"]
                ppe_issue = any(
                    it.get("status") == "needs_correction" and
                    it.get("key") in ("ppe_long_pants", "ppe_shirt_required",
                                      "ppe_work_boots", "ppe_acknowledged")
                    for it in ppe_items
                )
        return {
            **pkt_ctx,
            "missing_required_docs": missing,
            "expired_required_docs": expired,
            "docs_needs_correction": needs_corr,
            "ppe_issue": ppe_issue,
        }

    async def _upsert_elig_row(db, *, target_type: str, target_id: str,
                                result: Dict[str, Any]) -> None:
        row = {
            "tenant": TENANT, "target_type": target_type,
            "target_id": target_id, "state": result["state"],
            "reasons": result["reasons"],
            "computed_at": result["computed_at"],
            "expires_at": result.get("expires_at"), "stale": False,
            "phase": result.get("phase", 2),
        }
        existing = await db.transport_eligibility_state.find_one(
            {"tenant": TENANT, "target_type": target_type,
             "target_id": target_id})
        if existing:
            row["id"] = existing.get("id") or uuid.uuid4().hex
            await db.transport_eligibility_state.update_one(
                {"_id": existing["_id"]}, {"$set": row})
        else:
            row["id"] = uuid.uuid4().hex
            await db.transport_eligibility_state.insert_one(row.copy())

    app.include_router(router)
    return router


# ---------------------------------------------------------------------------
# Module-level upload / review helpers (no router state)
# ---------------------------------------------------------------------------
async def _store_file(file: UploadFile, data: bytes, *, source_id: str
                      ) -> tuple:
    """Push the uploaded bytes to R2 via photo_storage; return
    (file_key, reference). Never stores file bytes in Mongo."""
    from photo_storage import is_configured, upload_photo_bytes, _build_key
    ext = (file.filename or "").rsplit(".", 1)[-1].lower() or "bin"
    if is_configured():
        ref = await upload_photo_bytes(
            data, ext=ext, source_id=source_id,
            content_type=file.content_type or "application/octet-stream",
        )
        key = ref.replace("photo://", "", 1)
        return key, ref
    # Dev fallback — store a synthetic key only (no Mongo bytes).
    key = _build_key(source_id, ext)
    return key, f"photo://{key}"


async def _persist_doc(db, *, collection: str, base: Dict[str, Any],
                       document_type: str, file_key: str, ref: str,
                       file: UploadFile, expires_at: Optional[str],
                       actor: Any) -> Dict[str, Any]:
    now = _now()
    doc = {
        "id": uuid.uuid4().hex, "tenant": TENANT,
        "document_type": document_type,
        "file_key": file_key, "file_ref": ref,
        "original_filename": file.filename,
        "mime_type": file.content_type,
        "uploaded_by": _actor_label(actor),
        "uploaded_at": now, "expires_at": expires_at,
        "status": "pending_review",
        "review_notes": None, "reviewed_by": None, "reviewed_at": None,
        "audit_version": 1,
        **base,
    }
    await db[collection].insert_one(doc.copy())
    return doc


async def _review_doc(db, collection: str, doc_id: str,
                      body: DocumentReview, request: Request,
                      actor: Any) -> Dict[str, Any]:
    existing = await db[collection].find_one({"id": doc_id, "tenant": TENANT})
    if not existing:
        raise HTTPException(404, f"{collection.replace('_', ' ')} not found")
    if body.status not in REVIEW_STATUSES:
        raise HTTPException(422, f"status must be one of {list(REVIEW_STATUSES)}")
    upd = {"status": body.status, "reviewed_by": _actor_label(actor),
           "reviewed_at": _now(),
           "audit_version": (existing.get("audit_version") or 1) + 1}
    if body.review_notes is not None:
        upd["review_notes"] = body.review_notes
    if body.expires_at is not None:
        upd["expires_at"] = body.expires_at
    await db[collection].update_one({"_id": existing["_id"]}, {"$set": upd})
    new_doc = {**existing, **upd}
    await _audit(db, kind=f"transport_{collection}_review",
                 entity_type=collection, entity_id=doc_id,
                 actor=actor, old=_project(existing), new=_project(new_doc),
                 request=request)
    return _project(new_doc)

"""OA-1 · Operations Actions API surface.

Cross-portal CRUD-only operational coordination layer. Canonical auth
contract for every request:

  1. One valid portal token for the acting portal
  2. The bound `X-Directory-Token` for the same logical session

Anonymous or token-only calls = 401. No portal-level write asymmetry in
OA-1 by design — the constitution says any operator who sees the action
can also act on it.

Endpoints (all under `/api/operations-actions`):

  GET    /                       list + filters (status / owner / job / category / priority / q)
  GET    /summary                count rollups for hub badges
  POST   /                       create
  GET    /{id}                   read one
  PATCH  /{id}                   edit core fields (title/desc/category/priority/job/location/due_date)
  POST   /{id}/assign            assign owner → flips status open→assigned
  POST   /{id}/status            change status (validated transition)
  POST   /{id}/notes             append note
  POST   /{id}/photos            upload photo to R2
  DELETE /{id}/photos/{photo_id} delete photo
  GET    /owner-search?q=        cross-directory owner typeahead
  GET    /photos/{photo_id}/url  mint presigned GET URL

The 6 approved statuses are the ONLY values accepted:
    open · assigned · in_progress · waiting · completed · closed
"""
from __future__ import annotations

import asyncio

from lib.mongo_query import safe_regex
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from pymongo import ReturnDocument

logger = logging.getLogger(__name__)
OA_TRUST_WORKFLOW = "operations-action"

# ── Constants ────────────────────────────────────────────────────────
APPROVED_STATUSES = ["open", "assigned", "in_progress", "waiting", "completed", "closed"]
APPROVED_CATEGORIES = [
    "truck_down", "utility_conflict", "missing_mot", "gps_issue",
    "plant_delay", "survey_required", "near_miss", "safety_concern",
    "material_shortage", "customer_request", "other",
]
APPROVED_PRIORITIES = ["low", "normal", "high", "critical"]
APPROVED_DIRECTORIES = [
    "user_directory", "project_managers", "dispatch_users",
    "hr_users", "safety_users", "field_leadership_users", "shop_users",
]
MAX_PHOTO_BYTES = 15 * 1024 * 1024  # 15 MB · matches safety_documents cap
PHOTO_MAGIC_BYTES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png":  [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"],  # WebP starts with RIFF....WEBP
    "image/heic": [b"\x00\x00\x00", b"ftyp"],
    "image/heif": [b"\x00\x00\x00", b"ftyp"],
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Models ───────────────────────────────────────────────────────────
class OwnerRef(BaseModel):
    directory: str
    id: str
    name: Optional[str] = None
    email: Optional[str] = None


class CreatePayload(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    category: str
    priority: str = "normal"
    job_number: Optional[str] = None
    job_name: Optional[str] = None
    location: Optional[str] = None
    description: str = Field(default="", max_length=4000)
    due_date: Optional[str] = None  # ISO date
    owner: Optional[OwnerRef] = None


class UpdatePayload(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    category: Optional[str] = None
    priority: Optional[str] = None
    job_number: Optional[str] = None
    job_name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = Field(default=None, max_length=4000)
    due_date: Optional[str] = None


class AssignPayload(BaseModel):
    owner: OwnerRef


class StatusPayload(BaseModel):
    status: str
    note: Optional[str] = None


class NotePayload(BaseModel):
    body_en: str = Field(..., min_length=1, max_length=4000)


# ── Helpers ──────────────────────────────────────────────────────────
async def _next_oa_number(db) -> str:
    """Atomic year-scoped sequence. `OA-YYYY-000123` ledger format."""
    year = _now().year
    res = await db.system_counters.find_one_and_update(
        {"_id": f"oa_number_{year}"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    seq = int(res.get("seq") or 1)
    return f"OA-{year}-{seq:06d}"


def _validate_enum(value: str, allowed: List[str], field: str):
    if value not in allowed:
        raise HTTPException(422, f"Invalid {field}: {value}. Allowed: {','.join(allowed)}")


def _actor_to_owner(actor: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce a multi-portal actor dict into an OwnerRef-shaped dict."""
    role = (actor.get("_actor_kind") or actor.get("_role") or "").lower()
    # Map our role label → directory name
    directory_map = {
        "admin": "user_directory",
        "safety": "safety_users",
        "hr": "hr_users",
        "dispatch": "dispatch_users",
        "pm": "project_managers",
        "shop": "shop_users",
        "fl": "field_leadership_users",
        "field_leadership": "field_leadership_users",
    }
    directory = directory_map.get(role, "user_directory")
    return {
        "directory": directory,
        "id": actor.get("id") or actor.get("user_id") or actor.get("pm_id") or "admin",
        "name": actor.get("name") or actor.get("display_name") or "Operator",
        "email": actor.get("email") or "",
        "portal": role or "admin",
    }


def _clean_oa(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Strip Mongo internals before returning to API caller."""
    doc.pop("_id", None)
    doc.pop("_trust_cid", None)
    return doc


def _list_projection() -> Dict[str, int]:
    return {
        "_id": 0,
        "id": 1,
        "oa_number": 1,
        "title": 1,
        "category": 1,
        "priority": 1,
        "status": 1,
        "job_number": 1,
        "location": 1,
        "current_owner": 1,
        "created_at": 1,
    }


def _owner_key(owner: Optional[Dict[str, Any]]) -> tuple:
    owner = owner or {}
    return (
        owner.get("directory") or "",
        owner.get("id") or "",
        owner.get("email") or "",
    )


def _detect_content_type(data: bytes, declared: Optional[str]) -> str:
    """Magic-byte check. Returns the verified content type, or raises 422."""
    if not data:
        raise HTTPException(422, "Empty file")
    # JPEG
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    # PNG
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    # WebP — starts RIFF....WEBP
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    # HEIC / HEIF — 'ftyp' at offset 4
    if len(data) > 12 and data[4:8] == b"ftyp":
        return "image/heic"
    raise HTTPException(422, "Unsupported image format (must be JPEG, PNG, WebP, or HEIC)")


# ── Owner resolver (cross-directory typeahead) ───────────────────────
async def _owner_search(db, q: str, limit: int = 20) -> List[Dict[str, Any]]:
    q = (q or "").strip()
    out: List[Dict[str, Any]] = []
    if not q:
        return out
    rx = safe_regex(q)
    name_or_email = {"$or": [{"name": rx}, {"email": rx}]}

    async def _scan(coll, directory, projection):
        rows: List[Dict[str, Any]] = []
        cursor = db[coll].find(
            {"$and": [name_or_email, {"$or": [{"is_active": True}, {"is_active": {"$exists": False}}]}]},
            projection,
        ).limit(limit)
        async for r in cursor:
            rows.append({
                "directory": directory,
                "id": r.get("id") or r.get("pm_id") or r.get("user_id") or "",
                "name": r.get("name") or r.get("display_name") or "",
                "email": r.get("email") or "",
                "role": r.get("role") or r.get("title") or "",
            })
        return rows

    # user_directory (admins + multi-portal accounts) — schema sometimes uses name OR display_name
    cursor = db.user_directory.find(
        {"$and": [
            {"$or": [{"name": rx}, {"display_name": rx}, {"email": rx}]},
            {"$or": [{"is_active": True}, {"is_active": {"$exists": False}}]},
        ]},
        {"_id": 0, "id": 1, "name": 1, "display_name": 1, "email": 1, "role": 1},
    ).limit(limit)
    async for r in cursor:
        out.append({
            "directory": "user_directory",
            "id": r.get("id") or "",
            "name": r.get("name") or r.get("display_name") or "",
            "email": r.get("email") or "",
            "role": r.get("role") or "",
        })

    batches = await asyncio.gather(
        _scan("project_managers", "project_managers",
              {"_id": 0, "id": 1, "pm_id": 1, "name": 1, "email": 1, "role": 1}),
        _scan("dispatch_users", "dispatch_users",
              {"_id": 0, "id": 1, "name": 1, "email": 1, "role": 1}),
        _scan("hr_users", "hr_users",
              {"_id": 0, "id": 1, "name": 1, "email": 1, "role": 1}),
        _scan("safety_users", "safety_users",
              {"_id": 0, "id": 1, "name": 1, "email": 1, "role": 1}),
        _scan("field_leadership_users", "field_leadership_users",
              {"_id": 0, "id": 1, "name": 1, "email": 1, "role": 1}),
        _scan("shop_users", "shop_users",
              {"_id": 0, "id": 1, "name": 1, "email": 1, "role": 1}),
    )
    for batch in batches:
        out.extend(batch)

    # Dedupe by directory+id, return top `limit`
    seen = set()
    uniq: List[Dict[str, Any]] = []
    for r in out:
        key = (r["directory"], r["id"])
        if key in seen or not r["id"]:
            continue
        seen.add(key)
        uniq.append(r)
        if len(uniq) >= limit:
            break
    return uniq


# ── History (audit trail · append-only) ──────────────────────────────
def _history_entry(
    kind: str,
    actor: Dict[str, Any],
    before=None,
    after=None,
    *,
    reason: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    entry = {
        "id": uuid.uuid4().hex,
        "kind": kind,
        "actor": _actor_to_owner(actor),
        "before": before,
        "after": after,
        "at": _now_iso(),
    }
    if reason:
        entry["reason"] = reason[:400]
    if context:
        entry["context"] = context
    return entry


async def _emit_trust_mutation(
    db,
    *,
    record: Dict[str, Any],
    module: str,
    validation_reason: str,
    routed_to_owner: bool = False,
    notification_attempted: bool = False,
    notification_id: Optional[str] = None,
) -> None:
    try:
        from lib.trust_spine import (  # noqa: PLC0415
            STAGE_AUDIT_WRITTEN,
            STAGE_COMPLETED,
            STAGE_DASHBOARD_UPDATED,
            STAGE_NOTIFICATION_QUEUED,
            STAGE_RECIPIENTS_BUILT,
            STAGE_ROUTING_RESOLVED,
            STAGE_VALIDATION_COMPLETE,
            emit_workflow_stage,
        )

        await emit_workflow_stage(
            db,
            workflow=OA_TRUST_WORKFLOW,
            stage=STAGE_VALIDATION_COMPLETE,
            record=record,
            module=module,
            status="ok",
            remediation=validation_reason[:240],
        )
        if routed_to_owner:
            await emit_workflow_stage(
                db,
                workflow=OA_TRUST_WORKFLOW,
                stage=STAGE_ROUTING_RESOLVED,
                record=record,
                module=module,
                status="ok",
            )
        if notification_attempted:
            await emit_workflow_stage(
                db,
                workflow=OA_TRUST_WORKFLOW,
                stage=STAGE_RECIPIENTS_BUILT,
                record=record,
                module=module,
                status="ok",
            )
            await emit_workflow_stage(
                db,
                workflow=OA_TRUST_WORKFLOW,
                stage=STAGE_NOTIFICATION_QUEUED,
                record=record,
                module=module,
                status="ok" if notification_id else "failed",
                failure_reason=None if notification_id else "notification fanout failed or returned no id",
                remediation=None if notification_id else "Inspect notification_service fanout logs and recipient routing.",
            )
        await emit_workflow_stage(
            db,
            workflow=OA_TRUST_WORKFLOW,
            stage=STAGE_AUDIT_WRITTEN,
            record=record,
            module=module,
            status="ok",
        )
        await emit_workflow_stage(
            db,
            workflow=OA_TRUST_WORKFLOW,
            stage=STAGE_DASHBOARD_UPDATED,
            record=record,
            module=module,
            status="ok",
        )
        await emit_workflow_stage(
            db,
            workflow=OA_TRUST_WORKFLOW,
            stage=STAGE_COMPLETED,
            record=record,
            module=module,
            status="ok",
        )
    except Exception:  # noqa: BLE001
        pass


# ── Notification (in-app only, via existing notifications collection) ─
async def _notify_assignment(db, oa: Dict[str, Any]) -> Optional[str]:
    """Best-effort in-app notification when an OA is assigned.

    TRACK 15.28C — rewritten to use canonical `emit_notification`
    (single schema, idempotent, project-scoped on read). The legacy
    `kind=oa_assignment` shape is retired; rows now carry `type` +
    `recipient_role` + `recipient_user_id` like every other producer.
    Never raises — assignment must succeed even if notify fails."""
    owner = oa.get("current_owner") or {}
    if not owner.get("id"):
        return None
    try:
        from lib.event_fanout import emit_notification  # noqa: PLC0415
        oa_id = oa.get("id")
        owner_directory = (owner.get("directory") or "").lower()
        # Map operations_action owner directory → recipient_role so
        # role-scoped reads still surface the row even if the
        # recipient_user_id no longer resolves.
        role_map = {
            "hr_users": "hr",
            "safety_users": "safety",
            "shop_users": "shop",
            "dispatch_users": "dispatch",
            "field_leadership_users": "fl",
            "user_directory": "admin",
        }
        recipient_role = role_map.get(owner_directory, "admin")
        return await emit_notification(db, {
            "type": "oa_assignment",
            "title": f"Action assigned: {oa.get('title', '')}",
            "message": f"{oa.get('oa_number', '')} · {oa.get('category', '')} · {oa.get('priority', '')}",
            "severity": "Info",
            "recipient_role": recipient_role,
            "recipient_user_id": owner.get("id"),
            "link_url": f"/operations-actions/{oa_id}",
            "linked_source_module": "operations_action",
            "linked_source_record_id": oa_id,
        })
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[oa-1] in-app notify failed: {e}")
        return None


# ── Route registration ───────────────────────────────────────────────
def register_operations_actions_routes(router: APIRouter, db, require_actor) -> None:

    @router.get("/operations-actions/owner-search")
    async def owner_search(
        actor: Any = Depends(require_actor),
        q: str = Query("", max_length=80),
        limit: int = Query(20, le=50),
    ):
        rows = await _owner_search(db, q, limit=limit)
        return {"results": rows, "count": len(rows)}

    @router.get("/operations-actions/summary")
    async def summary(actor: Any = Depends(require_actor)):
        counts: Dict[str, int] = {s: 0 for s in APPROVED_STATUSES}
        mine_open = 0
        owner_dir, owner_id = None, None
        try:
            o = _actor_to_owner(actor)
            owner_dir, owner_id = o["directory"], o["id"]
        except Exception:
            pass

        pipeline = [{"$match": {"deleted_at": None}}]
        pipeline.append(
            {
                "$facet": {
                    "counts": [{"$group": {"_id": "$status", "n": {"$sum": 1}}}],
                    "mine_open": (
                        [{
                            "$match": {
                                "current_owner.directory": owner_dir,
                                "current_owner.id": owner_id,
                                "status": {"$in": ["assigned", "in_progress", "waiting"]},
                            }
                        }, {"$count": "n"}]
                        if owner_dir and owner_id else []
                    ),
                }
            }
        )
        agg = await db.operations_actions.aggregate(pipeline).to_list(length=1)
        facets = agg[0] if agg else {}
        for row in facets.get("counts") or []:
            counts[row.get("_id") or ""] = row.get("n") or 0
        mine_rows = facets.get("mine_open") or []
        mine_open = int((mine_rows[0] or {}).get("n") or 0) if mine_rows else 0

        total_open = counts["open"] + counts["assigned"] + counts["in_progress"] + counts["waiting"]
        return {
            "as_of": _now_iso(),
            "counts": counts,
            "total_open": total_open,
            "mine_open": mine_open,
        }

    @router.get("/operations-actions")
    async def list_actions(
        actor: Any = Depends(require_actor),
        status: Optional[str] = Query(None),
        owner_id: Optional[str] = Query(None),
        owner_directory: Optional[str] = Query(None),
        job_number: Optional[str] = Query(None),
        category: Optional[str] = Query(None),
        priority: Optional[str] = Query(None),
        q: Optional[str] = Query(None, max_length=80),
        mine: bool = Query(False),
        limit: int = Query(100, le=500),
        skip: int = Query(0, ge=0),
    ):
        match: Dict[str, Any] = {"deleted_at": None}
        if status:
            _validate_enum(status, APPROVED_STATUSES, "status")
            match["status"] = status
        if owner_id:
            match["current_owner.id"] = owner_id
        if owner_directory:
            match["current_owner.directory"] = owner_directory
        if job_number:
            match["job_number"] = job_number
        if category:
            _validate_enum(category, APPROVED_CATEGORIES, "category")
            match["category"] = category
        if priority:
            _validate_enum(priority, APPROVED_PRIORITIES, "priority")
            match["priority"] = priority
        if q:
            rx = safe_regex(q)
            match["$or"] = [{"title": rx}, {"description": rx}, {"oa_number": rx}, {"job_number": rx}]
        if mine:
            o = _actor_to_owner(actor)
            match["current_owner.directory"] = o["directory"]
            match["current_owner.id"] = o["id"]

        pipeline = [
            {"$match": match},
            {
                "$facet": {
                    "meta": [{"$count": "total"}],
                    "actions": [
                        {"$sort": {"created_at": -1}},
                        {"$skip": skip},
                        {"$limit": limit},
                        {"$project": _list_projection()},
                    ],
                }
            },
        ]
        agg = await db.operations_actions.aggregate(pipeline).to_list(length=1)
        facets = agg[0] if agg else {}
        rows = facets.get("actions") or []
        meta = facets.get("meta") or []
        total = int((meta[0] or {}).get("total") or 0) if meta else 0
        return {"count": len(rows), "total": total, "actions": rows}

    @router.post("/operations-actions")
    async def create_action(payload: CreatePayload, actor: Any = Depends(require_actor)):
        from lib.trust_spine import emit_record_created  # noqa: PLC0415

        _validate_enum(payload.category, APPROVED_CATEGORIES, "category")
        _validate_enum(payload.priority, APPROVED_PRIORITIES, "priority")

        now = _now_iso()
        creator = _actor_to_owner(actor)
        owner = payload.owner.model_dump() if payload.owner else None
        if owner:
            _validate_enum(owner.get("directory", ""), APPROVED_DIRECTORIES, "owner.directory")

        oa: Dict[str, Any] = {
            "id": uuid.uuid4().hex,
            "oa_number": await _next_oa_number(db),
            "title": payload.title.strip(),
            "category": payload.category,
            "priority": payload.priority,
            "status": "assigned" if owner else "open",
            "job_number": payload.job_number,
            "job_name": payload.job_name,
            "location": payload.location,
            "description": (payload.description or "").strip(),
            "due_date": payload.due_date,
            "created_by": creator,
            "created_at": now,
            "current_owner": owner,
            "assigned_at": now if owner else None,
            "last_updated_at": now,
            "closed_at": None,
            "photos": [],
            "notes": [],
            "history": [_history_entry(
                "created",
                actor,
                after={"status": "assigned" if owner else "open"},
                context={"command": "create_action", "owner_assigned": bool(owner)},
            )],
            "links": {
                "maintainx_ref": None, "fleetwatcher_ref": None, "motive_ref": None,
                "daily_report_id": None, "excavation_id": None, "safety_meeting_id": None,
                "jhp_id": None, "rfi_id": None,
            },
            "deleted_at": None,
        }
        await emit_record_created(
            db,
            workflow=OA_TRUST_WORKFLOW,
            record=oa,
            module="operations_actions.create",
        )

        await db.operations_actions.insert_one(oa)
        notification_id = None
        if owner:
            notification_id = await _notify_assignment(db, oa)
        await _emit_trust_mutation(
            db,
            record=oa,
            module="operations_actions.create",
            validation_reason="create payload accepted and persisted",
            routed_to_owner=bool(owner),
            notification_attempted=bool(owner),
            notification_id=notification_id,
        )
        return _clean_oa(oa)

    @router.get("/operations-actions/{oa_id}")
    async def read_action(oa_id: str, actor: Any = Depends(require_actor)):
        doc = await db.operations_actions.find_one({"id": oa_id, "deleted_at": None})
        if not doc:
            raise HTTPException(404, "Operations Action not found")
        return _clean_oa(doc)

    @router.patch("/operations-actions/{oa_id}")
    async def update_action(oa_id: str, payload: UpdatePayload, actor: Any = Depends(require_actor)):
        doc = await db.operations_actions.find_one({"id": oa_id, "deleted_at": None})
        if not doc:
            raise HTTPException(404, "Operations Action not found")
        if doc.get("status") == "closed":
            raise HTTPException(409, "Closed actions cannot be edited")

        updates: Dict[str, Any] = {}
        diffs: Dict[str, Any] = {}
        for f in ("title", "category", "priority", "job_number", "job_name",
                  "location", "description", "due_date"):
            val = getattr(payload, f, None)
            if val is None:
                continue
            if f == "category":
                _validate_enum(val, APPROVED_CATEGORIES, "category")
            if f == "priority":
                _validate_enum(val, APPROVED_PRIORITIES, "priority")
            if doc.get(f) != val:
                diffs[f] = {"from": doc.get(f), "to": val}
                updates[f] = val

        if not updates:
            return _clean_oa(doc)

        updates["last_updated_at"] = _now_iso()
        new_doc = await db.operations_actions.find_one_and_update(
            {"id": oa_id},
            {"$set": updates,
             "$push": {"history": _history_entry(
                 "updated",
                 actor,
                 before=None,
                 after=diffs,
                 context={"command": "update_action", "changed_fields": sorted(diffs.keys())},
             )}},
            return_document=ReturnDocument.AFTER,
        )
        await _emit_trust_mutation(
            db,
            record=new_doc,
            module="operations_actions.update",
            validation_reason="field update accepted and persisted",
        )
        return _clean_oa(new_doc)

    @router.post("/operations-actions/{oa_id}/assign")
    async def assign_action(oa_id: str, payload: AssignPayload, actor: Any = Depends(require_actor)):
        _validate_enum(payload.owner.directory, APPROVED_DIRECTORIES, "owner.directory")
        doc = await db.operations_actions.find_one({"id": oa_id, "deleted_at": None})
        if not doc:
            raise HTTPException(404, "Operations Action not found")
        if doc.get("status") == "closed":
            raise HTTPException(409, "Closed actions cannot be reassigned")

        owner = payload.owner.model_dump()
        if _owner_key(doc.get("current_owner")) == _owner_key(owner) and doc.get("status") != "open":
            return _clean_oa(doc)
        now = _now_iso()
        new_status = "assigned" if doc.get("status") == "open" else doc.get("status")
        new_doc = await db.operations_actions.find_one_and_update(
            {"id": oa_id},
            {"$set": {
                "current_owner": owner,
                "assigned_at": now,
                "last_updated_at": now,
                "status": new_status,
             },
             "$push": {"history": _history_entry(
                 "assigned",
                 actor,
                 before={"owner": doc.get("current_owner")},
                 after={"owner": owner, "status": new_status},
                 context={"command": "assign_action"},
             )}},
            return_document=ReturnDocument.AFTER,
        )
        notification_id = await _notify_assignment(db, new_doc)
        await _emit_trust_mutation(
            db,
            record=new_doc,
            module="operations_actions.assign",
            validation_reason="owner assignment accepted and persisted",
            routed_to_owner=True,
            notification_attempted=True,
            notification_id=notification_id,
        )
        return _clean_oa(new_doc)

    @router.post("/operations-actions/{oa_id}/status")
    async def change_status(oa_id: str, payload: StatusPayload, actor: Any = Depends(require_actor)):
        _validate_enum(payload.status, APPROVED_STATUSES, "status")
        doc = await db.operations_actions.find_one({"id": oa_id, "deleted_at": None})
        if not doc:
            raise HTTPException(404, "Operations Action not found")

        prev = doc.get("status")
        if prev == payload.status:
            return _clean_oa(doc)

        # Transition rules (calm, not punitive):
        # · Cannot move from `closed` to anything except via admin reopen — out of scope OA-1
        if prev == "closed":
            raise HTTPException(409, "Closed actions cannot transition")
        # · Moving to `assigned` requires an owner.
        if payload.status == "assigned" and not doc.get("current_owner"):
            raise HTTPException(409, "Assign an owner before setting status to assigned")

        now = _now_iso()
        updates = {"status": payload.status, "last_updated_at": now}
        if payload.status == "closed":
            updates["closed_at"] = now

        push_ops: Dict[str, Any] = {
            "history": _history_entry("status_changed", actor,
                                      before={"status": prev}, after={"status": payload.status}),
        }
        if payload.note:
            push_ops["notes"] = {
                "id": uuid.uuid4().hex,
                "author": _actor_to_owner(actor),
                "body_en": payload.note.strip()[:4000],
                "created_at": now,
            }

        new_doc = await db.operations_actions.find_one_and_update(
            {"id": oa_id},
            {"$set": updates, "$push": push_ops},
            return_document=ReturnDocument.AFTER,
        )
        await _emit_trust_mutation(
            db,
            record=new_doc,
            module="operations_actions.status",
            validation_reason=f"status transition persisted: {prev} -> {payload.status}",
        )
        return _clean_oa(new_doc)

    @router.post("/operations-actions/{oa_id}/notes")
    async def add_note(oa_id: str, payload: NotePayload, actor: Any = Depends(require_actor)):
        doc = await db.operations_actions.find_one({"id": oa_id, "deleted_at": None})
        if not doc:
            raise HTTPException(404, "Operations Action not found")

        note = {
            "id": uuid.uuid4().hex,
            "author": _actor_to_owner(actor),
            "body_en": payload.body_en.strip()[:4000],
            "created_at": _now_iso(),
        }
        new_doc = await db.operations_actions.find_one_and_update(
            {"id": oa_id},
            {"$set": {"last_updated_at": _now_iso()},
             "$push": {"notes": note,
                       "history": _history_entry(
                           "note_added",
                           actor,
                           after={"note_id": note["id"]},
                           reason=note["body_en"][:120],
                           context={"command": "add_note"},
                       )}},
            return_document=ReturnDocument.AFTER,
        )
        await _emit_trust_mutation(
            db,
            record=new_doc,
            module="operations_actions.note",
            validation_reason="note append persisted",
        )
        return note

    @router.post("/operations-actions/{oa_id}/photos")
    async def upload_photo(
        oa_id: str,
        file: UploadFile = File(...),
        actor: Any = Depends(require_actor),
    ):
        doc = await db.operations_actions.find_one({"id": oa_id, "deleted_at": None})
        if not doc:
            raise HTTPException(404, "Operations Action not found")

        data = await file.read(MAX_PHOTO_BYTES + 1)
        if len(data) > MAX_PHOTO_BYTES:
            raise HTTPException(413, f"Photo exceeds {MAX_PHOTO_BYTES // (1024*1024)} MB cap")
        content_type = _detect_content_type(data, file.content_type)
        ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp",
               "image/heic": "heic", "image/heif": "heic"}.get(content_type, "jpg")

        # Reuse existing R2 photo storage layer.
        try:
            from photo_storage import (  # noqa: PLC0415
                upload_photo_bytes, is_configured,
            )
            if not is_configured():
                raise HTTPException(503, "Photo storage not configured")
            ref = await upload_photo_bytes(
                data, ext=ext, source_id=f"oa-{oa_id}", content_type=content_type,
            )
        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001
            logger.exception(f"[oa-1] R2 upload failed: {e}")
            raise HTTPException(500, "Photo upload failed") from e

        photo = {
            "id": uuid.uuid4().hex,
            "r2_ref": ref,
            "content_type": content_type,
            "size": len(data),
            "uploaded_at": _now_iso(),
            "uploaded_by": _actor_to_owner(actor),
        }
        try:
            new_doc = await db.operations_actions.find_one_and_update(
                {"id": oa_id},
                {"$set": {"last_updated_at": _now_iso()},
                 "$push": {"photos": photo,
                           "history": _history_entry(
                               "photo_added",
                               actor,
                               after={"photo_id": photo["id"]},
                               context={"command": "upload_photo", "content_type": content_type, "size": len(data)},
                           )}},
                return_document=ReturnDocument.AFTER,
            )
        except Exception:
            try:
                from photo_storage import delete_photo as _r2_delete  # noqa: PLC0415
                await _r2_delete(ref)
            except Exception as cleanup_error:  # noqa: BLE001
                logger.warning(f"[oa-1] photo rollback cleanup failed: {cleanup_error}")
            raise
        await _emit_trust_mutation(
            db,
            record=new_doc,
            module="operations_actions.photo_upload",
            validation_reason="photo uploaded and metadata persisted",
        )
        return photo

    @router.get("/operations-actions/{oa_id}/photos/{photo_id}/url")
    async def photo_url(oa_id: str, photo_id: str, actor: Any = Depends(require_actor)):
        doc = await db.operations_actions.find_one(
            {"id": oa_id, "deleted_at": None},
            {"photos": 1, "_id": 0},
        )
        if not doc:
            raise HTTPException(404, "Operations Action not found")
        photo = next((p for p in (doc.get("photos") or []) if p.get("id") == photo_id), None)
        if not photo:
            raise HTTPException(404, "Photo not found")
        try:
            from photo_storage import presigned_get_url  # noqa: PLC0415
            url = await presigned_get_url(photo["r2_ref"], ttl_seconds=900)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(500, f"Could not mint photo URL: {e}") from e
        return {"url": url, "ttl_seconds": 900}

    @router.delete("/operations-actions/{oa_id}/photos/{photo_id}")
    async def delete_photo(oa_id: str, photo_id: str, actor: Any = Depends(require_actor)):
        doc = await db.operations_actions.find_one({"id": oa_id, "deleted_at": None})
        if not doc:
            raise HTTPException(404, "Operations Action not found")
        photo = next((p for p in (doc.get("photos") or []) if p.get("id") == photo_id), None)
        if not photo:
            raise HTTPException(404, "Photo not found")

        new_doc = await db.operations_actions.find_one_and_update(
            {"id": oa_id},
            {"$set": {"last_updated_at": _now_iso()},
             "$pull": {"photos": {"id": photo_id}},
             "$push": {"history": _history_entry(
                 "photo_deleted",
                 actor,
                 after={"photo_id": photo_id},
                 context={"command": "delete_photo", "r2_ref": photo.get("r2_ref")},
             )}},
            return_document=ReturnDocument.AFTER,
        )
        await _emit_trust_mutation(
            db,
            record=new_doc,
            module="operations_actions.photo_delete",
            validation_reason="photo reference deleted from canonical record",
        )
        try:
            from photo_storage import delete_photo as _r2_delete  # noqa: PLC0415
            await _r2_delete(photo["r2_ref"])
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[oa-1] R2 delete best-effort failure: {e}")
        return {"ok": True}


__all__ = ["register_operations_actions_routes", "APPROVED_STATUSES",
           "APPROVED_CATEGORIES", "APPROVED_PRIORITIES", "APPROVED_DIRECTORIES"]

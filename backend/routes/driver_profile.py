"""
DCP-1 · Driver Command Profile — unified read-only driver dossier.
===================================================================
One backend endpoint, one frontend component, four portal consumers
(Admin, HR, Safety, Dispatch). Role-shaped payload so each consumer
sees only what their role is allowed to see.

Source collections (all existing — zero new state):
  - employees                    (identity, supervisor, status, hire)
  - employee_mappings            (Motive linkage, cleanup_status)
  - motive_events                (HOS, harsh, DVIR, geofence — last 30d)
  - dispatch_assignments         (current + last assignment, vehicles)
  - incidents                    (linked safety incidents — last 365d)
  - corrective_actions           (open CAs assigned to this driver)
  - safety_training_records      (training history)
  - document_expirations         (cert windows, OSHA / CPR / MOT)
  - asset_mappings (read-only)   (equipment lookup for vehicle names)

Endpoint:
  GET /api/operations/drivers/{driver_key}/profile

`driver_key` accepts any of:
  - MASCI employee_id          (db.employees.id)
  - MASCI employee number      (db.employees.employee_id)
  - Motive user_id / driver_id (db.employee_mappings.motive.user_id|driver_id)

Auth: Admin · HR · Safety · Dispatch (caller supplies token; we degrade
the returned payload by role; admin sees everything, dispatch sees only
identity + operations + equipment + current_status).
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from lib.synthetic_corrective_action_filter import apply_synthetic_corrective_action_exclusion


ROLE_ADMIN = "admin"
ROLE_HR = "hr"
ROLE_SAFETY = "safety"
ROLE_DISPATCH = "dispatch"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


async def _resolve_employee_and_mapping(db, driver_key: str):
    """Return (employee_doc, mapping_doc, motive_user_id) given any key."""
    employee = None
    mapping = None

    # Try employees.id, employees.employee_id
    employee = await db.employees.find_one(
        {"$or": [{"id": driver_key}, {"employee_id": driver_key}]},
        {"_id": 0},
    )

    # Try employee_mappings via masci_employee_id, motive.user_id, motive.driver_id, motive.id
    mapping = await db.employee_mappings.find_one(
        {
            "provider": "motive",
            "$or": [
                {"masci_employee_id": driver_key},
                {"motive.user_id": driver_key},
                {"motive.driver_id": driver_key},
                {"motive.id": driver_key},
                *([{"masci_employee_id": employee["id"]}] if employee else []),
            ],
        },
        {"_id": 0},
    )

    # If we found a mapping but no employee yet, try via masci_employee_id
    if not employee and mapping and mapping.get("masci_employee_id"):
        employee = await db.employees.find_one(
            {"id": mapping["masci_employee_id"]}, {"_id": 0}
        )

    motive_user_id = ""
    if mapping:
        mv = mapping.get("motive") or {}
        motive_user_id = str(mv.get("user_id") or mv.get("driver_id") or mv.get("id") or "")

    return employee, mapping, motive_user_id


def _identity(employee: Optional[Dict[str, Any]], mapping: Optional[Dict[str, Any]]):
    if not employee and not mapping:
        return None
    e = employee or {}
    m = (mapping or {}).get("motive") or {}
    return {
        "name": e.get("name") or m.get("driver_name") or (f"{m.get('first_name','')} {m.get('last_name','')}").strip() or "Unknown",
        "employee_id": e.get("employee_id") or "",
        "employee_uuid": e.get("id") or "",
        "trade": e.get("trade") or "",
        "role": e.get("role") or "",
        "crew": e.get("crew") or "",
        "supervisor_name": e.get("supervisor_name") or e.get("crew") or "",
        "email": e.get("email") or m.get("email") or "",
        "phone": e.get("phone") or m.get("phone") or "",
        "is_active": e.get("is_active", True) if employee else None,
        "lifecycle_status": e.get("lifecycle_status") or ("Active" if e.get("is_active", True) else "Inactive"),
        "hire_date": e.get("hire_date") or e.get("created_at") or "",
        "last_day_worked": e.get("last_day_worked") or "",
        "photo_url": e.get("photo_url") or "",
    }


async def _operations(db, employee_uuid: str, motive_user_id: str):
    cur = None
    last = None
    asgn_q = {"driver_id": employee_uuid} if employee_uuid else {}
    if employee_uuid:
        # current = not COMPLETE/CANCELLED — newest
        cur = await db.dispatch_assignments.find_one(
            {**asgn_q, "current_state": {"$nin": ["COMPLETE", "CANCELLED"]}},
            {"_id": 0},
            sort=[("last_transition_at", -1)],
        )
        # last = most recently completed
        last = await db.dispatch_assignments.find_one(
            {**asgn_q, "current_state": {"$in": ["COMPLETE", "CANCELLED"]}},
            {"_id": 0},
            sort=[("completed_at", -1), ("last_transition_at", -1)],
        )

    last_motive_activity = None
    last_known_location = None
    if motive_user_id:
        ev = await db.motive_events.find_one(
            {"driver_id": motive_user_id},
            {"_id": 0, "event_family": 1, "headline": 1, "decorated_label": 1, "received_at": 1, "lat": 1, "lon": 1, "city": 1, "state": 1, "vehicle_id": 1},
            sort=[("received_at", -1)],
        )
        if ev:
            last_motive_activity = {
                "event_family": ev.get("event_family"),
                "headline": ev.get("headline") or ev.get("decorated_label"),
                "received_at": ev.get("received_at"),
                "vehicle_id": ev.get("vehicle_id"),
            }
            if ev.get("lat") and ev.get("lon"):
                last_known_location = {
                    "lat": ev.get("lat"),
                    "lon": ev.get("lon"),
                    "city": ev.get("city"),
                    "state": ev.get("state"),
                    "as_of": ev.get("received_at"),
                }

    def _slim_asgn(a):
        if not a:
            return None
        return {
            "id": a.get("id"),
            "current_state": a.get("current_state"),
            "truck_id": a.get("truck_id"),
            "trailer_label": a.get("trailer_label"),
            "project_number": a.get("project_number"),
            "project_name": a.get("project_name"),
            "material": a.get("material"),
            "pickup_location": a.get("pickup_location") or a.get("source_location"),
            "dropoff_location": a.get("dropoff_location") or a.get("destination"),
            "assigned_at": a.get("assigned_at"),
            "last_transition_at": a.get("last_transition_at"),
            "completed_at": a.get("completed_at"),
        }

    return {
        "current_assignment": _slim_asgn(cur),
        "last_assignment": _slim_asgn(last),
        "current_vehicle": (cur or {}).get("truck_id") if cur else None,
        "last_vehicle": (last or {}).get("truck_id") if last else None,
        "last_motive_activity": last_motive_activity,
        "last_known_location": last_known_location,
    }


async def _safety(db, employee_uuid: str, motive_user_id: str):
    now = _now()
    cut_30d = _iso(now - timedelta(days=30))
    cut_365d = _iso(now - timedelta(days=365))

    # Motive-side counts (require motive_user_id)
    harsh_30d = hos_30d = dvir_30d = 0
    ai_coach_score = None
    if motive_user_id:
        harsh_30d = await db.motive_events.count_documents({
            "driver_id": motive_user_id,
            "event_family": "harsh_event",
            "received_at": {"$gte": cut_30d},
        })
        hos_30d = await db.motive_events.count_documents({
            "driver_id": motive_user_id,
            "event_family": "hos_violation",
            "received_at": {"$gte": cut_30d},
        })
        dvir_30d = await db.motive_events.count_documents({
            "driver_id": motive_user_id,
            "event_family": "dvir",
            "received_at": {"$gte": cut_30d},
        })

    # MASCI safety incidents linked by employee name or id
    incident_rows: List[Dict[str, Any]] = []
    if employee_uuid:
        emp_name = None
        emp = await db.employees.find_one({"id": employee_uuid}, {"_id": 0, "name": 1})
        if emp:
            emp_name = emp.get("name")
        q = {
            "incident_date": {"$gte": cut_365d[:10]},
            "$or": [
                {"injured_employee_id": employee_uuid},
                {"involved_employee_ids": employee_uuid},
                *([{"injured_employee_name": emp_name}] if emp_name else []),
            ],
        }
        async for inc in db.incidents.find(q, {"_id": 0, "id": 1, "incident_number": 1,
                                                "incident_type": 1, "incident_date": 1,
                                                "severity": 1, "location": 1}).sort("incident_date", -1).limit(20):
            incident_rows.append(inc)

    # Open corrective actions assigned to this driver
    ca_rows: List[Dict[str, Any]] = []
    if employee_uuid:
        emp = await db.employees.find_one({"id": employee_uuid}, {"_id": 0, "name": 1, "email": 1})
        name = (emp or {}).get("name") or ""
        email = (emp or {}).get("email") or ""
        q = {
            "status": {"$nin": ["closed", "completed", "verified", "cancelled"]},
            "$or": [
                *([{"assigned_to_name": name}] if name else []),
                *([{"assigned_to_email": email}] if email else []),
                {"assigned_to_employee_id": employee_uuid},
            ],
        }
        async for ca in db.corrective_actions.find(
            apply_synthetic_corrective_action_exclusion(q),
            {"_id": 0, "id": 1, "title": 1, "priority": 1, "due_date": 1, "status": 1},
        ).sort("due_date", 1).limit(20):
            ca_rows.append(ca)

    return {
        "harsh_events_30d": harsh_30d,
        "hos_violations_30d": hos_30d,
        "hos_status": "violation_active" if hos_30d > 0 and motive_user_id else ("clean" if motive_user_id else "unknown"),
        "ai_coach_trend": None,  # Not currently captured upstream (see audit).
        "dvir_inspections_30d": dvir_30d,
        "ai_coach_score": ai_coach_score,  # legacy field, retained for compat
        "incidents_365d": incident_rows,
        "open_corrective_actions": ca_rows,
    }


async def _training(db, employee_uuid: str):
    if not employee_uuid:
        return {"records": [], "expirations": {
            "current": 0, "expiring_30d": 0, "expiring_60d": 0,
            "expiring_90d": 0, "expired": 0,
        }}

    rows: List[Dict[str, Any]] = []
    async for r in db.safety_training_records.find(
        {"$or": [{"employee_id": employee_uuid}, {"employee_master_id": employee_uuid}]},
        {"_id": 0, "id": 1, "training_name": 1, "certification_type": 1,
         "completed_date": 1, "expiration_date": 1, "issued_by": 1},
    ).sort("expiration_date", -1):
        rows.append(r)

    # Document expirations
    now = _now()
    today = now.date().isoformat()
    cut_30d = (now + timedelta(days=30)).date().isoformat()
    cut_60d = (now + timedelta(days=60)).date().isoformat()
    cut_90d = (now + timedelta(days=90)).date().isoformat()
    exp_rows: List[Dict[str, Any]] = []
    async for d in db.document_expirations.find(
        {"linked_employee_id": employee_uuid, "deleted_at": None},
        {"_id": 0, "id": 1, "title": 1, "document_type": 1, "category": 1,
         "expiration_date": 1, "status": 1},
    ).sort("expiration_date", 1):
        exp_rows.append(d)

    expired = sum(1 for d in exp_rows if d.get("expiration_date", "") and d.get("expiration_date", "") < today)
    in_30 = sum(1 for d in exp_rows if today <= d.get("expiration_date", "") <= cut_30d)
    in_60 = sum(1 for d in exp_rows if cut_30d < d.get("expiration_date", "") <= cut_60d)
    in_90 = sum(1 for d in exp_rows if cut_60d < d.get("expiration_date", "") <= cut_90d)
    current = sum(1 for d in exp_rows if d.get("expiration_date", "") > cut_90d)

    return {
        "records": rows,
        "documents": exp_rows,
        "expirations": {
            "current": current,
            "expiring_30d": in_30,
            "expiring_60d": in_60,
            "expiring_90d": in_90,
            "expired": expired,
        },
    }


async def _equipment_usage(db, employee_uuid: str):
    if not employee_uuid:
        return {"most_used": None, "last_operated": None, "timeline": []}

    # Aggregate truck_id usage from dispatch_assignments
    pipeline = [
        {"$match": {"driver_id": employee_uuid, "truck_id": {"$nin": [None, ""]}}},
        {"$group": {"_id": "$truck_id",
                    "count": {"$sum": 1},
                    "last_seen": {"$max": "$last_transition_at"}}},
        {"$sort": {"count": -1}},
        {"$limit": 8},
    ]
    aggs = []
    async for row in db.dispatch_assignments.aggregate(pipeline):
        aggs.append({
            "truck_id": row.get("_id"),
            "usage_count": row.get("count"),
            "last_seen": row.get("last_seen"),
        })

    most_used = aggs[0]["truck_id"] if aggs else None

    last = await db.dispatch_assignments.find_one(
        {"driver_id": employee_uuid, "truck_id": {"$nin": [None, ""]}},
        {"_id": 0, "truck_id": 1, "completed_at": 1, "last_transition_at": 1},
        sort=[("last_transition_at", -1)],
    )

    # 10-event timeline (recent assignments)
    timeline = []
    async for a in db.dispatch_assignments.find(
        {"driver_id": employee_uuid, "truck_id": {"$nin": [None, ""]}},
        {"_id": 0, "id": 1, "truck_id": 1, "project_number": 1,
         "assigned_at": 1, "completed_at": 1, "current_state": 1},
    ).sort("last_transition_at", -1).limit(10):
        timeline.append(a)

    return {
        "most_used": most_used,
        "most_used_top": aggs,
        "last_operated": last.get("truck_id") if last else None,
        "last_operated_at": (last.get("completed_at") or last.get("last_transition_at")) if last else None,
        "timeline": timeline,
    }


def _motive_block(mapping: Optional[Dict[str, Any]]):
    if not mapping:
        return None
    mv = mapping.get("motive") or {}
    return {
        "driver_status": (mv.get("status") or "unknown").lower(),
        "driver_id": mv.get("driver_id") or mv.get("user_id") or "",
        "user_id": mv.get("user_id") or "",
        "vehicle_id": mv.get("vehicle_id") or "",
        "last_sync": mv.get("synced_at") or mapping.get("updated_at"),
        "last_vehicle": mv.get("last_vehicle") or "",
        "located_at": mv.get("located_at") or "",
    }


def _mapping_health(mapping: Optional[Dict[str, Any]]):
    if not mapping:
        return {"linked": False, "status": "unmapped"}
    masci_id = (mapping.get("masci_employee_id") or "").strip()
    cleanup = mapping.get("cleanup_status") or ""
    if masci_id:
        return {"linked": True, "status": "linked", "cleanup_status": cleanup, "mapping_notes": mapping.get("mapping_notes", "")}
    if cleanup == "former_employee":
        return {"linked": False, "status": "former_employee", "cleanup_status": cleanup}
    if cleanup == "ignored":
        return {"linked": False, "status": "ignored", "cleanup_status": cleanup}
    mv = mapping.get("motive") or {}
    if (mv.get("status") or "").lower() == "deactivated":
        return {"linked": False, "status": "deactivated_unlinked", "cleanup_status": cleanup}
    return {"linked": False, "status": "needs_review", "cleanup_status": cleanup}


def _redact_for_role(payload: Dict[str, Any], role: str) -> Dict[str, Any]:
    """Strip sections the caller is not permitted to see."""
    out = dict(payload)
    if role == ROLE_DISPATCH:
        # Dispatch sees identity + operations + equipment + current_status only.
        out.pop("safety", None)
        out.pop("training", None)
        out.pop("motive", None)
        out.pop("mapping_health", None)
    elif role == ROLE_HR:
        # HR sees everything except Admin diagnostics (mapping_health).
        out.pop("mapping_health", None)
    elif role == ROLE_SAFETY:
        # Safety sees operational + safety. No mapping diagnostics.
        out.pop("mapping_health", None)
    # admin → full
    out["_role"] = role
    return out


def register_driver_profile_routes(api_router: APIRouter, db, require_actor) -> None:
    """Mount the DCP-1 endpoint.

    `require_actor` is a FastAPI dep returning a dict with `_role` field
    set to one of admin/hr/safety/dispatch. Caller wires this up so we
    avoid duplicating multi-portal auth here."""

    @api_router.get("/operations/drivers/{driver_key}/profile")
    async def get_driver_profile(
        driver_key: str,
        actor: Any = Depends(require_actor),
    ):
        if not driver_key.strip():
            raise HTTPException(400, "driver_key required")

        employee, mapping, motive_user_id = await _resolve_employee_and_mapping(db, driver_key)
        if not employee and not mapping:
            raise HTTPException(404, "driver not found")

        employee_uuid = (employee or {}).get("id") or ""

        identity = _identity(employee, mapping)
        operations = await _operations(db, employee_uuid, motive_user_id)
        safety = await _safety(db, employee_uuid, motive_user_id)
        training = await _training(db, employee_uuid)
        equipment_usage = await _equipment_usage(db, employee_uuid)
        motive = _motive_block(mapping)
        mapping_health = _mapping_health(mapping)

        # DSI-1C · Last-event timeline (motive activity for this driver)
        activity_rows: List[Dict[str, Any]] = []
        if motive_user_id:
            async for ev in db.motive_events.find(
                {"driver_id": motive_user_id},
                {"_id": 0, "event_family": 1, "severity": 1, "priority": 1,
                 "received_at": 1, "headline": 1, "decorated_label": 1,
                 "vehicle_id": 1},
            ).sort("received_at", -1).limit(15):
                activity_rows.append({
                    "event_family": ev.get("event_family"),
                    "severity": ev.get("severity"),
                    "priority": ev.get("priority"),
                    "received_at": ev.get("received_at"),
                    "vehicle_id": ev.get("vehicle_id"),
                    "headline": ev.get("headline") or ev.get("decorated_label"),
                })

        payload = {
            "as_of": _iso(_now()),
            "driver_key": driver_key,
            "identity": identity,
            "operations": operations,
            "safety": safety,
            "training": training,
            "equipment_usage": equipment_usage,
            "motive": motive,
            "mapping_health": mapping_health,
            "activity": activity_rows,
        }

        role = (actor or {}).get("_role") or ROLE_ADMIN
        return _redact_for_role(payload, role)


__all__ = ["register_driver_profile_routes",
           "ROLE_ADMIN", "ROLE_HR", "ROLE_SAFETY", "ROLE_DISPATCH"]

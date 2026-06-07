"""Phase 10A · Public Excavation Operations Workflow (G-1 closure).

Single source-of-truth Excavation Record. Public submit + Safety oversight.
Reuses certified infrastructure:
  • Audit: write_audit → audit_events
  • Notifications: event_fanout (Phase 7.5C)
  • Asset linkage: trench_safety_assets registry (no duplicate inventory)
  • Reporting: extends the Phase 9A registry-driven pattern

NEW collection: trench_excavations
ID format: EX-YYYY-### (year-scoped sequential, permanent, never reused)
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from ._helpers import now_iso, write_audit

logger = logging.getLogger(__name__)
PREFIX = "/trench-safety/excavations"

VALID_WORK_TYPES = (
    "Utility Work", "Storm Drain", "Sanitary Sewer", "Water Main",
    "Electrical / Communication", "Roadway Excavation",
    "Structure / Box Culvert", "Drainage", "Other",
)
VALID_SOIL = ("Type A", "Type B", "Type C", "Stable Rock", "Unknown / Needs Review")
VALID_PROTECTIVE = (
    "Trench Box / Shielding", "Shoring", "Sloping", "Benching",
    "Combination", "Not Required", "Needs Safety Review",
)
VALID_LOCATE_STATUS = ("Complete", "Pending", "Not Required", "Conflict / Needs Review")
STATUSES = ("Draft", "Submitted", "Needs Review", "Action Required",
            "Pending Verification", "Reviewed", "Closed", "Reopened")


# ────────────────────────────────────────────────────────────────────────
# Payload schema
# ────────────────────────────────────────────────────────────────────────

class ExcavationSubmit(BaseModel):
    model_config = ConfigDict(extra="ignore")
    # 1 · Project / Job
    project_name: str = ""
    project_number: str = ""
    location: str = ""
    work_area: str = ""
    date_of_work: str = ""           # YYYY-MM-DD
    supervisor_name: str = ""
    crew: str = ""
    submitted_by: str = ""
    contact_phone: str = ""
    # 2 · Dimensions
    length_ft: Optional[float] = None
    width_ft: Optional[float] = None
    depth_ft: Optional[float] = None
    depth_unit: str = "ft"
    depth_ge_4ft: Optional[bool] = None
    depth_ge_5ft: Optional[bool] = None
    cave_in_hazard_under_5ft: Optional[bool] = None
    # 3 · Work type
    work_type: str = "Other"
    # 4 · Soil
    soil_classification: str = "Unknown / Needs Review"
    # 5 · Protective system
    protective_system: str = "Needs Safety Review"
    no_protective_system_reason: str = ""
    # 6 · Assigned assets
    assigned_asset_ids: List[str] = Field(default_factory=list)
    # 7 · Access / Egress
    access_egress_required: Optional[bool] = None
    access_egress_installed: Optional[bool] = None
    access_egress_within_25ft: Optional[bool] = None
    ladder_extends_above_landing: Optional[bool] = None
    access_egress_secure: Optional[bool] = None
    # 8 · Utility locate
    utility_locate_required: Optional[bool] = None
    locate_ticket_number: str = ""
    locate_status: str = "Not Required"
    utility_conflicts_observed: Optional[bool] = None
    utility_notes: str = ""
    # 9 · Spoils / Edge
    spoils_2ft_from_edge: Optional[bool] = None
    equipment_near_edge: Optional[bool] = None
    barricades_in_place: Optional[bool] = None
    stop_logs_used: Optional[bool] = None
    # 10 · Water
    water_present: Optional[bool] = None
    seepage_present: Optional[bool] = None
    dewatering_required: Optional[bool] = None
    dewatering_active: Optional[bool] = None
    water_needs_review: Optional[bool] = None
    # 11 · Atmosphere
    deep_or_confined_concern: Optional[bool] = None
    hazardous_atmosphere_concern: Optional[bool] = None
    atmospheric_testing_required: Optional[bool] = None
    atmospheric_testing_completed: Optional[bool] = None
    atmospheric_notes: str = ""
    # 12 · Competent Person
    competent_person_name: str = ""
    competent_person_confirmed: bool = False
    inspection_before_entry_completed: Optional[bool] = None
    reinspection_required: Optional[bool] = None
    reinspection_completed: Optional[bool] = None
    # 13 · Photos — stored as URLs (uploaded separately via existing photo endpoint)
    photo_ids: List[str] = Field(default_factory=list)
    # 14 · Field notes
    field_notes: str = ""
    language: str = "en"   # "en" | "es" — preserves submission language
    # Source
    source: str = "public_tile"   # "public_tile" | "daily_report"


class ExcavationReview(BaseModel):
    model_config = ConfigDict(extra="ignore")
    action: str   # "review" | "request_clarification" | "close" | "reopen"
    coaching_note: str = ""


# ────────────────────────────────────────────────────────────────────────
# OSHA deterministic flag engine — 10 flags, coaching language
# ────────────────────────────────────────────────────────────────────────

def compute_osha_flags(rec: Dict[str, Any]) -> List[Dict[str, str]]:
    flags: List[Dict[str, str]] = []
    depth = rec.get("depth_ft") or 0
    is_ge_4 = bool(rec.get("depth_ge_4ft")) or (depth and depth >= 4)
    is_ge_5 = bool(rec.get("depth_ge_5ft")) or (depth and depth >= 5)
    ps = rec.get("protective_system") or ""
    soil = rec.get("soil_classification") or ""
    work = rec.get("work_type") or ""
    locate = rec.get("locate_status") or ""
    assets = rec.get("assigned_asset_ids") or []

    def _add(code: str, level: str, message: str):
        flags.append({"code": code, "level": level, "message": message})

    # 1 · Depth ≥ 4 ft and no access/egress installed
    if is_ge_4 and rec.get("access_egress_installed") is False:
        _add("ACCESS_EGRESS", "Action Required",
             "Excavation is 4 ft or deeper — confirm a ladder/ramp/stairway is installed within 25 ft lateral travel.")
    # 2 · Depth ≥ 5 ft and no protective system selected
    if is_ge_5 and ps in ("Not Required", "Needs Safety Review", ""):
        _add("PROTECTIVE_SYSTEM", "Action Required",
             "Excavation is 5 ft or deeper — confirm protective system selection with the competent person.")
    # 3 · Soil unknown
    if soil == "Unknown / Needs Review":
        _add("SOIL_UNKNOWN", "Needs Review",
             "Soil classification is unknown — schedule a competent-person classification.")
    # 4 · Utility locate pending and utility work
    if "Utility" in work and locate == "Pending":
        _add("UTILITY_LOCATE", "Action Required",
             "Utility-locate ticket pending — confirm clearance before exposing utilities.")
    # 5 · Water present and dewatering not addressed
    if rec.get("water_present") and not rec.get("dewatering_active") and not rec.get("dewatering_required") is False:
        _add("WATER", "Needs Review",
             "Water present — confirm dewatering plan with the competent person.")
    # 6 · Hazardous atmosphere concern and testing not completed
    if rec.get("hazardous_atmosphere_concern") and not rec.get("atmospheric_testing_completed"):
        _add("ATMOSPHERE", "Action Required",
             "Atmospheric concern noted — complete testing before crew descent.")
    # 7 · Trench box selected but no asset ID linked
    if ps in ("Trench Box / Shielding", "Combination") and not any(a for a in assets):
        _add("TRENCH_BOX_ASSIGNMENT", "Needs Review",
             "Trench Box / Shielding selected — link the specific Trench Box asset IDs to this record.")
    # 8 · Road plate work (assets contain road plate but explicit field) — derived from notes
    # We can't fully introspect asset_type without DB; mark needs_review if work_type is roadway and no assets linked
    if work == "Roadway Excavation" and not any(a for a in assets):
        _add("ROAD_PLATE_ASSIGNMENT", "Needs Review",
             "Roadway excavation — link any Road Plate asset IDs in use.")
    # 9 · Spoils not 2 ft from edge
    if rec.get("spoils_2ft_from_edge") is False:
        _add("SPOIL_SETBACK", "Action Required",
             "Spoils observed less than 2 ft from edge — relocate spoils for compliant setback.")
    # 10 · Reinspection required but not completed
    if rec.get("reinspection_required") and not rec.get("reinspection_completed"):
        _add("REINSPECTION", "Action Required",
             "Reinspection required (rain / change / event) — complete competent-person reinspection.")

    return flags


def derive_status(rec: Dict[str, Any], flags: List[Dict[str, str]]) -> str:
    if rec.get("status") in ("Reviewed", "Closed", "Reopened"):
        return rec["status"]
    if any(f["level"] == "Action Required" for f in flags):
        return "Action Required"
    if any(f["level"] == "Needs Review" for f in flags):
        return "Needs Review"
    return rec.get("status") or "Submitted"


async def _next_excavation_id(db) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"EX-{year}-"
    cursor = db.trench_excavations.find({"id": {"$regex": f"^{prefix}"}}, {"_id": 0, "id": 1})
    used: set[int] = set()
    async for d in cursor:
        try:
            used.add(int((d.get("id") or "").split("-")[-1]))
        except ValueError:
            continue
    n = 1
    while n in used:
        n += 1
    return f"{prefix}{n:03d}"


# ────────────────────────────────────────────────────────────────────────
# Route registration
# ────────────────────────────────────────────────────────────────────────

def register_excavation_routes(
    api_router: APIRouter,
    db,
    *,
    require_safety_or_admin,
) -> None:

    # ── PUBLIC submit (no auth) ────────────────────────────────────
    @api_router.post(PREFIX + "/public/submit")
    async def public_submit(body: ExcavationSubmit):
        ex_id = await _next_excavation_id(db)
        rec: Dict[str, Any] = body.model_dump()
        rec["id"] = ex_id
        rec["created_at"] = now_iso()
        rec["updated_at"] = now_iso()
        rec["status"] = "Submitted"
        rec["coaching_notes"] = []
        rec["review_history"] = []
        flags = compute_osha_flags(rec)
        rec["flags"] = flags
        rec["status"] = derive_status(rec, flags)
        await db.trench_excavations.insert_one(rec)
        rec.pop("_id", None)
        # Audit
        await write_audit(
            db, kind="excavation_record_created",
            asset_id=ex_id, actor={"email": body.submitted_by or "public"},
            detail={
                "excavation_id": ex_id, "source": body.source,
                "flag_count": len(flags), "status": rec["status"],
                "project_name": body.project_name,
            },
        )
        # Notification fanout — reuse existing event_fanout
        try:
            from lib.event_fanout import emit_notification  # noqa: PLC0415
            await emit_notification(
                db,
                kind="trench_excavation_submitted",
                title=f"Excavation submitted · {ex_id}",
                body=f"{body.project_name or 'Project'} · {body.supervisor_name or 'Supervisor'} · {rec['status']}",
                linked_equipment_id=ex_id,
                actor_email=body.submitted_by or "public",
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("excavation notify failed: %s", e)
        return rec

    # ── List + filter ──────────────────────────────────────────────
    @api_router.get(PREFIX)
    async def list_excavations(
        project_name: Optional[str] = Query(default=None),
        supervisor_name: Optional[str] = Query(default=None),
        status: Optional[str] = Query(default=None),
        soil: Optional[str] = Query(default=None),
        protective_system: Optional[str] = Query(default=None),
        depth_min: Optional[float] = Query(default=None),
        has_action_required: Optional[bool] = Query(default=None),
        limit: int = Query(default=200, ge=1, le=1000),
        _actor: dict = Depends(require_safety_or_admin),
    ):
        q: Dict[str, Any] = {}
        if project_name:
            q["project_name"] = {"$regex": project_name, "$options": "i"}
        if supervisor_name:
            q["supervisor_name"] = {"$regex": supervisor_name, "$options": "i"}
        if status:
            q["status"] = status
        if soil:
            q["soil_classification"] = soil
        if protective_system:
            q["protective_system"] = protective_system
        if depth_min is not None:
            q["depth_ft"] = {"$gte": depth_min}
        if has_action_required is True:
            q["status"] = "Action Required"
        cursor = db.trench_excavations.find(q, {"_id": 0}).sort("created_at", -1).limit(limit)
        items = await cursor.to_list(limit)
        return {"items": items, "count": len(items)}

    @api_router.get(PREFIX + "/{ex_id}")
    async def get_excavation(ex_id: str, _actor: dict = Depends(require_safety_or_admin)):
        doc = await db.trench_excavations.find_one({"id": ex_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Excavation record not found")
        return doc

    @api_router.post(PREFIX + "/{ex_id}/review")
    async def review_excavation(ex_id: str, body: ExcavationReview, actor: dict = Depends(require_safety_or_admin)):
        doc = await db.trench_excavations.find_one({"id": ex_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Excavation record not found")
        action = body.action
        new_status = {
            "review":                "Reviewed",
            "request_clarification": "Needs Review",
            "close":                 "Closed",
            "reopen":                "Reopened",
        }.get(action)
        if not new_status:
            raise HTTPException(400, "Unknown review action")
        coaching = doc.get("coaching_notes", []) or []
        if body.coaching_note:
            coaching.append({
                "at": now_iso(),
                "by": (actor or {}).get("email") or "safety",
                "note": body.coaching_note,
            })
        history = doc.get("review_history", []) or []
        history.append({
            "at": now_iso(), "by": (actor or {}).get("email") or "safety",
            "action": action, "new_status": new_status,
        })
        await db.trench_excavations.update_one(
            {"id": ex_id},
            {"$set": {
                "status": new_status, "coaching_notes": coaching,
                "review_history": history, "updated_at": now_iso(),
            }},
        )
        await write_audit(
            db, kind=f"excavation_record_{action}", asset_id=ex_id,
            actor=actor, detail={"new_status": new_status, "note_added": bool(body.coaching_note)},
        )
        try:
            from lib.event_fanout import emit_notification  # noqa: PLC0415
            await emit_notification(
                db, kind=f"trench_excavation_{action}",
                title=f"Excavation {action} · {ex_id}",
                body=f"{new_status}",
                linked_equipment_id=ex_id,
                actor_email=(actor or {}).get("email") or "safety",
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("excavation review notify failed: %s", e)
        return await db.trench_excavations.find_one({"id": ex_id}, {"_id": 0})

    @api_router.get(PREFIX + "/reports/summary")
    async def reports_summary(_actor: dict = Depends(require_safety_or_admin)):
        docs = await db.trench_excavations.find({}, {"_id": 0}).to_list(2000)
        out = {
            "total": len(docs),
            "active": 0,
            "by_status": {},
            "action_required": [],
            "missing_protective_system": [],
            "missing_access_egress": [],
            "soil_unknown": [],
            "utility_locate_review": [],
            "reinspection_required": [],
        }
        for d in docs:
            st = d.get("status") or "Submitted"
            out["by_status"][st] = out["by_status"].get(st, 0) + 1
            if st not in ("Closed",):
                out["active"] += 1
            for f in d.get("flags") or []:
                if f.get("level") == "Action Required":
                    out["action_required"].append({"id": d["id"], "flag": f["code"]})
                if f.get("code") == "PROTECTIVE_SYSTEM":
                    out["missing_protective_system"].append(d["id"])
                if f.get("code") == "ACCESS_EGRESS":
                    out["missing_access_egress"].append(d["id"])
                if f.get("code") == "SOIL_UNKNOWN":
                    out["soil_unknown"].append(d["id"])
                if f.get("code") == "UTILITY_LOCATE":
                    out["utility_locate_review"].append(d["id"])
                if f.get("code") == "REINSPECTION":
                    out["reinspection_required"].append(d["id"])
        return out

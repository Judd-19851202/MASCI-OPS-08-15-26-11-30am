"""Phase 10A · Public Excavation Operations Workflow (G-1 closure).

Phase 10A-B · Integration Hardening (OMEGA Correction Directive):
  • Job source pinned to certified jobs_master (Correction 2)
  • Personnel pinned to certified employees roster (Correction 3)
  • Assets pinned to certified trench_safety_assets registry (Correction 4)
  • Road Plate registry surfaced via dedicated asset_type filter (Correction 5)
  • Smart OSHA triggers extended (Correction 7)
  • Reinspection automation (Correction 10)
  • Daily Report two-way linkage (Correction 1)
  • Spanish translation storage with original-language preservation (Correction 9)

Single source-of-truth Excavation Record. Public submit + Safety oversight.
Reuses certified infrastructure:
  • Audit: write_audit → audit_events
  • Notifications: event_fanout (Phase 7.5C)
  • Asset linkage: trench_safety_assets registry (no duplicate inventory)
  • Personnel linkage: employees roster (no duplicate directory)
  • Job linkage: jobs_master (no duplicate project registry)
  • Reporting: extends the Phase 9A registry-driven pattern

NEW collection: trench_excavations
ID format: EX-YYYY-### (year-scoped sequential, permanent, never reused)
"""
from __future__ import annotations

import logging
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

# Phase 10A-B · Photo categories (Correction 8)
PHOTO_KINDS = (
    "Overall Excavation",
    "Protective System",
    "Access/Egress",
    "Utility Markings",
    "Soil Condition",
    "Water Condition",
    "Traffic Control",
)

# Phase 10A-B · Reinspection trigger reasons (Correction 10)
REINSPECTION_TRIGGER_REASONS = (
    "Rain",
    "Soil Change",
    "Water Intrusion",
    "Utility Strike",
    "Protective System Change",
    "Excavation Expansion",
    "Manual",
)


# ────────────────────────────────────────────────────────────────────────
# Payload schema
# ────────────────────────────────────────────────────────────────────────

class ExcavationSubmit(BaseModel):
    model_config = ConfigDict(extra="ignore")
    # 1 · Job (Correction 2 — pinned to jobs_master)
    job_id: str = ""                  # jobs_master.id
    project_name: str = ""
    project_number: str = ""
    customer: str = ""
    project_manager: str = ""
    pm_email: str = ""
    location: str = ""
    work_area: str = ""
    date_of_work: str = ""            # YYYY-MM-DD
    # 1b · Personnel (Correction 3 — pinned to employees roster)
    prepared_by_id: str = ""          # employees.id
    prepared_by_name: str = ""
    foreman_id: str = ""
    foreman_name: str = ""
    leadman_id: str = ""
    leadman_name: str = ""
    superintendent_id: str = ""
    superintendent_name: str = ""
    # Backwards-compat (existing fields)
    supervisor_name: str = ""         # mirrors foreman_name unless explicitly set
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
    # 6 · Trench assets (Correction 4 — pinned to trench_safety_assets)
    assigned_asset_ids: List[str] = Field(default_factory=list)
    # 6b · Road plates (Correction 5)
    road_plates_used: Optional[bool] = None
    road_plate_ids: List[str] = Field(default_factory=list)
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
    # 12 · Competent Person (Correction 3 — pinned to employees roster)
    competent_person_id: str = ""
    competent_person_name: str = ""
    competent_person_confirmed: bool = False
    inspection_before_entry_completed: Optional[bool] = None
    reinspection_required: Optional[bool] = None
    reinspection_completed: Optional[bool] = None
    # 12b · Rain / event trigger (Correction 7 + 10)
    rain_event_observed: Optional[bool] = None
    # 13 · Photos — structured by kind (Correction 8)
    photos: List[Dict[str, str]] = Field(default_factory=list)
    photo_ids: List[str] = Field(default_factory=list)  # legacy
    # 14 · Field notes (Correction 9 — source language preserved)
    field_notes: str = ""              # canonical (matches original_text)
    field_notes_original_language: str = "en"
    field_notes_original_text: str = ""
    field_notes_translated_text: str = ""
    language: str = "en"               # session locale at submit time
    # Source
    source: str = "public_tile"        # "public_tile" | "daily_report"
    # Daily Report linkage (Correction 1)
    triggered_from_daily_report_id: str = ""


class ExcavationReview(BaseModel):
    model_config = ConfigDict(extra="ignore")
    action: str   # "review" | "request_clarification" | "close" | "reopen"
    coaching_note: str = ""


class ReinspectionTrigger(BaseModel):
    model_config = ConfigDict(extra="ignore")
    reason: str = "Manual"
    note: str = ""


class NotesTranslate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    translated_text: str = ""


class DailyReportLink(BaseModel):
    model_config = ConfigDict(extra="ignore")
    daily_report_id: str
    report_number: str = ""


# ────────────────────────────────────────────────────────────────────────
# OSHA deterministic flag engine — 12 flags, coaching language
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
    # 3b · Type C soil — additional coaching (Correction 7)
    if soil == "Type C":
        _add("SOIL_TYPE_C", "Needs Review",
             "Type C soil — apply stricter sloping (1.5H:1V) or use shielding/shoring; competent person to confirm.")
    # 4 · Utility locate pending and utility work
    if "Utility" in work and locate == "Pending":
        _add("UTILITY_LOCATE", "Action Required",
             "Utility-locate ticket pending — confirm clearance before exposing utilities.")
    # 5 · Water present and dewatering not addressed
    if rec.get("water_present") and not rec.get("dewatering_active") and rec.get("dewatering_required") is not False:
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
    # 8 · Road plate work
    road_plates = rec.get("road_plate_ids") or []
    if rec.get("road_plates_used") and not road_plates:
        _add("ROAD_PLATE_ASSIGNMENT", "Needs Review",
             "Road Plates marked in use — link the specific Road Plate asset IDs to this record.")
    elif work == "Roadway Excavation" and not road_plates and not any(a for a in assets):
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
    # 11 · Rain event observed → auto reinspection requirement (Correction 7+10)
    if rec.get("rain_event_observed") and not rec.get("reinspection_completed"):
        _add("RAIN_REINSPECTION", "Action Required",
             "Rain event observed — competent-person reinspection is required before crew re-entry.")
    # 12 · Depth ≥ 5 ft and no competent person designated
    if is_ge_5 and not (rec.get("competent_person_name") or rec.get("competent_person_id")):
        _add("COMPETENT_PERSON", "Action Required",
             "Excavation is 5 ft or deeper — designate a competent person on this record.")

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

    # ── PUBLIC asset roster (Correction 4 + 5) ─────────────────────
    @api_router.get(PREFIX + "/public/asset-roster")
    async def public_asset_roster(
        asset_type: Optional[str] = Query(default=None, description="Filter by asset_type (e.g. 'Road Plate', 'Trench Box')"),
        q: Optional[str] = Query(default=None, description="Free-text search across asset_id / serial / location"),
        only_available: bool = Query(default=False),
        limit: int = Query(default=500, ge=1, le=2000),
    ):
        """Public — surface the certified trench-safety asset registry for
        the Public Excavation form's multi-select picker. Returns only
        field-safe fields. Never leaks PII or admin-only metadata."""
        query: Dict[str, Any] = {"is_active": True}
        if asset_type:
            query["asset_type"] = asset_type
        if only_available:
            query["operational_status"] = "Available"
        if q:
            qre = {"$regex": q, "$options": "i"}
            query["$or"] = [
                {"asset_id": qre},
                {"serial_number": qre},
                {"assigned_location": qre},
                {"current_location": qre},
            ]
        proj = {
            "_id": 0, "asset_id": 1, "asset_type": 1, "serial_number": 1,
            "operational_status": 1, "condition": 1, "active_holds": 1,
            "assigned_location": 1, "current_location": 1,
            "dimensions": 1, "rated_depth_ft": 1, "tabulated_data_url": 1,
            "size_label": 1,
        }
        cursor = db.trench_safety_assets.find(query, proj).sort("asset_id", 1).limit(limit)
        items = await cursor.to_list(limit)
        # Compress to a field-safe roster row
        roster = []
        for a in items:
            holds = a.get("active_holds") or []
            roster.append({
                "asset_id": a.get("asset_id"),
                "asset_type": a.get("asset_type"),
                "size_label": a.get("size_label") or (a.get("dimensions") or {}).get("label", ""),
                "serial_number": a.get("serial_number") or "",
                "operational_status": a.get("operational_status") or "Available",
                "condition": a.get("condition") or "",
                "assigned_location": a.get("assigned_location") or a.get("current_location") or "",
                "rated_depth_ft": a.get("rated_depth_ft"),
                "tabulated_data_available": bool(a.get("tabulated_data_url")),
                "open_holds_count": len(holds),
            })
        return {"items": roster, "count": len(roster)}

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
        rec["reinspection_history"] = []
        # Personnel mirror — keep supervisor_name back-compat synced with foreman_name
        if not rec.get("supervisor_name") and rec.get("foreman_name"):
            rec["supervisor_name"] = rec["foreman_name"]
        # Notes — original-language preservation (Correction 9)
        if rec.get("field_notes") and not rec.get("field_notes_original_text"):
            rec["field_notes_original_text"] = rec["field_notes"]
            rec["field_notes_original_language"] = rec.get("language") or "en"
        # OSHA flags
        flags = compute_osha_flags(rec)
        rec["flags"] = flags
        rec["status"] = derive_status(rec, flags)
        # Daily Report cross-reference — non-invasive lookup (Correction 1)
        rec["daily_report_links"] = []
        try:
            search = {}
            if body.project_number:
                search["project_number"] = body.project_number
            elif body.project_name:
                search["project_name"] = {"$regex": f"^{body.project_name}$", "$options": "i"}
            if body.date_of_work:
                search["report_date"] = body.date_of_work
            if search:
                dr_cursor = db.daily_reports.find(search, {"_id": 0, "id": 1, "report_number": 1}).limit(5)
                async for dr in dr_cursor:
                    rec["daily_report_links"].append({
                        "daily_report_id": dr.get("id"),
                        "report_number": dr.get("report_number"),
                        "linked_at": now_iso(),
                    })
            # Explicit linkage if submitted FROM a daily report
            if body.triggered_from_daily_report_id and not any(
                lk["daily_report_id"] == body.triggered_from_daily_report_id
                for lk in rec["daily_report_links"]
            ):
                rec["daily_report_links"].append({
                    "daily_report_id": body.triggered_from_daily_report_id,
                    "report_number": "",
                    "linked_at": now_iso(),
                })
        except Exception as e:  # noqa: BLE001
            logger.warning("excavation daily-report lookup failed: %s", e)
        await db.trench_excavations.insert_one(rec)
        rec.pop("_id", None)
        # Reverse-link: stamp excavation_id into the Daily Report doc(s) (Correction 1)
        try:
            for link in rec["daily_report_links"]:
                dr_id = link.get("daily_report_id")
                if dr_id:
                    await db.daily_reports.update_one(
                        {"id": dr_id},
                        {"$addToSet": {"linked_excavation_ids": ex_id}},
                    )
        except Exception as e:  # noqa: BLE001
            logger.warning("excavation reverse-link write failed: %s", e)
        # Audit
        await write_audit(
            db, kind="excavation_record_created",
            asset_id=ex_id, actor={"email": body.submitted_by or "public"},
            detail={
                "excavation_id": ex_id, "source": body.source,
                "flag_count": len(flags), "status": rec["status"],
                "job_id": body.job_id, "project_number": body.project_number,
                "daily_report_link_count": len(rec["daily_report_links"]),
            },
        )
        # Notification fanout — reuse existing event_fanout
        try:
            from lib.event_fanout import emit_notification  # noqa: PLC0415
            await emit_notification(
                db,
                kind="trench_excavation_submitted",
                title=f"Excavation submitted · {ex_id}",
                body=f"{body.project_name or 'Project'} · {body.foreman_name or body.supervisor_name or 'Foreman'} · {rec['status']}",
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
        project_number: Optional[str] = Query(default=None),
        supervisor_name: Optional[str] = Query(default=None),
        status: Optional[str] = Query(default=None),
        soil: Optional[str] = Query(default=None),
        protective_system: Optional[str] = Query(default=None),
        depth_min: Optional[float] = Query(default=None),
        has_action_required: Optional[bool] = Query(default=None),
        reinspection_open: Optional[bool] = Query(default=None),
        limit: int = Query(default=200, ge=1, le=1000),
        _actor: dict = Depends(require_safety_or_admin),
    ):
        q: Dict[str, Any] = {}
        if project_name:
            q["project_name"] = {"$regex": project_name, "$options": "i"}
        if project_number:
            q["project_number"] = project_number
        if supervisor_name:
            q["$or"] = [
                {"supervisor_name": {"$regex": supervisor_name, "$options": "i"}},
                {"foreman_name": {"$regex": supervisor_name, "$options": "i"}},
            ]
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
        if reinspection_open is True:
            q["reinspection_required"] = True
            q["reinspection_completed"] = {"$ne": True}
        cursor = db.trench_excavations.find(q, {"_id": 0}).sort("created_at", -1).limit(limit)
        items = await cursor.to_list(limit)
        return {"items": items, "count": len(items)}

    # ── Reinspection queue (Correction 10) ─────────────────────────
    @api_router.get(PREFIX + "/reinspection-queue")
    async def reinspection_queue(_actor: dict = Depends(require_safety_or_admin)):
        cursor = db.trench_excavations.find(
            {"reinspection_required": True, "reinspection_completed": {"$ne": True},
             "status": {"$nin": ["Closed"]}},
            {"_id": 0},
        ).sort("updated_at", -1).limit(500)
        items = await cursor.to_list(500)
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

    # ── Reinspection trigger (Correction 10) ───────────────────────
    @api_router.post(PREFIX + "/{ex_id}/reinspection-trigger")
    async def reinspection_trigger(ex_id: str, body: ReinspectionTrigger, actor: dict = Depends(require_safety_or_admin)):
        doc = await db.trench_excavations.find_one({"id": ex_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Excavation record not found")
        reason = body.reason if body.reason in REINSPECTION_TRIGGER_REASONS else "Manual"
        history = doc.get("reinspection_history", []) or []
        history.append({
            "at": now_iso(), "by": (actor or {}).get("email") or "safety",
            "reason": reason, "note": body.note,
        })
        flags = compute_osha_flags({**doc, "reinspection_required": True})
        await db.trench_excavations.update_one(
            {"id": ex_id},
            {"$set": {
                "reinspection_required": True,
                "reinspection_completed": False,
                "reinspection_history": history,
                "flags": flags,
                "status": derive_status({**doc, "reinspection_required": True}, flags),
                "updated_at": now_iso(),
            }},
        )
        await write_audit(
            db, kind="excavation_reinspection_triggered", asset_id=ex_id,
            actor=actor, detail={"reason": reason, "note": body.note},
        )
        try:
            from lib.event_fanout import emit_notification  # noqa: PLC0415
            await emit_notification(
                db, kind="trench_excavation_reinspection_required",
                title=f"Reinspection required · {ex_id}",
                body=f"{reason} · {body.note[:60]}",
                linked_equipment_id=ex_id,
                actor_email=(actor or {}).get("email") or "safety",
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("reinspection notify failed: %s", e)
        return await db.trench_excavations.find_one({"id": ex_id}, {"_id": 0})

    # ── Translation override (Correction 9) ────────────────────────
    @api_router.post(PREFIX + "/{ex_id}/translate-notes")
    async def translate_notes(ex_id: str, body: NotesTranslate, actor: dict = Depends(require_safety_or_admin)):
        doc = await db.trench_excavations.find_one({"id": ex_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Excavation record not found")
        await db.trench_excavations.update_one(
            {"id": ex_id},
            {"$set": {
                "field_notes_translated_text": body.translated_text,
                "field_notes_translated_at": now_iso(),
                "field_notes_translated_by": (actor or {}).get("email") or "safety",
                "updated_at": now_iso(),
            }},
        )
        await write_audit(
            db, kind="excavation_notes_translated", asset_id=ex_id, actor=actor,
            detail={"len": len(body.translated_text or "")},
        )
        return await db.trench_excavations.find_one({"id": ex_id}, {"_id": 0})

    # ── Manual Daily Report linkage (Correction 1) ─────────────────
    @api_router.post(PREFIX + "/{ex_id}/link-daily-report")
    async def link_daily_report(ex_id: str, body: DailyReportLink, actor: dict = Depends(require_safety_or_admin)):
        doc = await db.trench_excavations.find_one({"id": ex_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Excavation record not found")
        dr = await db.daily_reports.find_one(
            {"id": body.daily_report_id}, {"_id": 0, "id": 1, "report_number": 1},
        )
        if not dr:
            raise HTTPException(404, "Daily report not found")
        links = doc.get("daily_report_links", []) or []
        if not any(lk.get("daily_report_id") == dr["id"] for lk in links):
            links.append({
                "daily_report_id": dr["id"],
                "report_number": dr.get("report_number") or "",
                "linked_at": now_iso(),
                "linked_by": (actor or {}).get("email") or "safety",
            })
        await db.trench_excavations.update_one(
            {"id": ex_id},
            {"$set": {"daily_report_links": links, "updated_at": now_iso()}},
        )
        # Reverse-link
        await db.daily_reports.update_one(
            {"id": dr["id"]},
            {"$addToSet": {"linked_excavation_ids": ex_id}},
        )
        await write_audit(
            db, kind="excavation_daily_report_linked",
            asset_id=ex_id, actor=actor,
            detail={"daily_report_id": dr["id"]},
        )
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
                if f.get("code") in ("REINSPECTION", "RAIN_REINSPECTION"):
                    out["reinspection_required"].append(d["id"])
        return out

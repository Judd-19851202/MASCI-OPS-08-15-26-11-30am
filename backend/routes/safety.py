"""Safety-form routes: Inspections, Meetings, JHPs, Incidents.

Extracted from server.py 2026-04-28 — second batch of the server.py refactor
(P1 backlog). All four groups share the same shape:

    POST  /<kind>           public + rate-limited (the field forms)
    GET   /<kind>           admin-only (list with summary projection)
    GET   /<kind>/{id}      admin-only (full doc)
    DELETE /<kind>/{id}     admin-only

Each group has its own Pydantic models (Create / Full / Summary). Auto-email
routing for new records is fired via `schedule_auto_email("inspection|meeting|jha|incident", doc)`.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Inspections
# ============================================================
class InspectionCreate(BaseModel):
    """Loose schema – the inspection form is large and conditional."""
    model_config = ConfigDict(extra="allow")

    project_name: str
    project_number: Optional[str] = ""
    location: str
    inspection_date: str  # ISO date string YYYY-MM-DD
    inspection_time: str  # HH:MM
    operation: str = "Day"
    inspector_name: str
    foreman_name: str
    crew_personnel: Optional[str] = ""
    subcontractors: Optional[str] = ""
    weather_conditions: Optional[str] = ""
    work_activity: str

    # Section payloads – stored verbatim
    ppe_compliance: Dict[str, Any] = Field(default_factory=dict)
    equipment: Dict[str, Any] = Field(default_factory=dict)
    traffic_control: Dict[str, Any] = Field(default_factory=dict)
    mot_moving_trucks: Dict[str, Any] = Field(default_factory=dict)
    fall_protection: Dict[str, Any] = Field(default_factory=dict)
    excavation: Dict[str, Any] = Field(default_factory=dict)
    electrical: Dict[str, Any] = Field(default_factory=dict)
    concrete_paving: Dict[str, Any] = Field(default_factory=dict)
    site_hazards: Dict[str, Any] = Field(default_factory=dict)

    # Corrective actions
    hazards_observed: str = "No"
    stop_work_issued: str = "No"
    corrected_on_site: str = "N/A"
    responsible_party: Optional[str] = ""
    corrective_action_notes: Optional[str] = ""
    photos: List[str] = Field(default_factory=list)

    # Signatures
    inspector_signature: Optional[str] = ""
    foreman_signature: Optional[str] = ""

    # Grading
    score: Optional[int] = None
    status: Optional[str] = None
    auto_fail_count: Optional[int] = 0
    graded_yes: Optional[int] = 0
    graded_no: Optional[int] = 0
    graded_total: Optional[int] = 0


class Inspection(InspectionCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InspectionSummary(BaseModel):
    id: str
    project_name: str
    location: str
    inspection_date: str
    inspector_name: str
    foreman_name: str
    hazards_observed: str
    stop_work_issued: str
    photo_count: int
    created_at: str
    score: Optional[int] = None
    status: Optional[str] = None
    auto_fail_count: Optional[int] = 0
    graded_yes: Optional[int] = 0
    graded_no: Optional[int] = 0
    graded_total: Optional[int] = 0


# ============================================================
# Meetings (Toolbox Talks)
# ============================================================
class MeetingCreate(BaseModel):
    model_config = ConfigDict(extra="allow")
    project_name: str
    project_number: Optional[str] = ""
    location: str
    meeting_date: str
    meeting_time: str
    conducted_by: str
    topic: str
    topic_category: Optional[str] = ""
    hazards_reviewed: Optional[str] = ""
    discussion_notes: Optional[str] = ""
    references_cited: Optional[str] = ""
    action_items: Optional[str] = ""
    attendees: List[Dict[str, Any]] = Field(default_factory=list)
    photos: List[str] = Field(default_factory=list)
    conductor_signature: Optional[str] = ""


class Meeting(MeetingCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MeetingSummary(BaseModel):
    id: str
    project_name: str
    location: str
    meeting_date: str
    conducted_by: str
    topic: str
    topic_category: str
    attendee_count: int
    created_at: str


# ============================================================
# Job Hazard Plan
# ============================================================
class JhaCreate(BaseModel):
    model_config = ConfigDict(extra="allow")
    project_name: str
    project_number: Optional[str] = ""
    location: str
    jha_date: str
    job_title: str
    job_description: Optional[str] = ""
    crew_lead: str
    crew_members: Optional[str] = ""
    ppe_required: Dict[str, Any] = Field(default_factory=dict)
    permits_required: Dict[str, Any] = Field(default_factory=dict)
    tools_equipment: Optional[str] = ""
    task_steps: List[Dict[str, Any]] = Field(default_factory=list)
    stop_work_acknowledged: Optional[str] = "Yes"
    nearest_hospital: Optional[str] = ""
    emergency_contact: Optional[str] = ""
    crew_signoffs: List[Dict[str, Any]] = Field(default_factory=list)
    foreman_signature: Optional[str] = ""
    photos: List[str] = Field(default_factory=list)


class Jha(JhaCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class JhaSummary(BaseModel):
    id: str
    project_name: str
    location: str
    jha_date: str
    crew_lead: str
    job_title: str
    step_count: int
    signoff_count: int
    created_at: str


# ============================================================
# Incidents
# ============================================================
class IncidentCreate(BaseModel):
    """Loose schema – the incident form is large, several optional sections."""
    model_config = ConfigDict(extra="allow")

    project_name: str
    project_number: Optional[str] = ""
    location: str
    incident_date: str
    incident_time: str
    reported_date: str
    reported_by: str
    supervisor_name: Optional[str] = ""

    incident_type: str
    severity: str
    osha_recordable: Optional[str] = "No"
    work_stopped: Optional[str] = "No"

    person_name: Optional[str] = ""
    person_role: Optional[str] = ""
    person_employer: Optional[str] = ""
    person_years_experience: Optional[str] = ""
    body_part: Optional[str] = ""
    injury_nature: Optional[str] = ""
    treatment_provided: Optional[str] = ""
    medical_facility: Optional[str] = ""
    sent_home: Optional[str] = "No"

    description: str
    immediate_cause: Optional[str] = ""
    contributing_factors: Optional[str] = ""
    root_causes: Dict[str, Any] = Field(default_factory=dict)
    root_cause_notes: Optional[str] = ""

    witnesses: List[Dict[str, Any]] = Field(default_factory=list)

    immediate_actions_taken: Optional[str] = ""
    corrective_actions: Optional[str] = ""
    responsible_party: Optional[str] = ""
    target_completion_date: Optional[str] = ""

    notified_safety_manager: Optional[str] = "No"
    notified_pm: Optional[str] = "No"
    notified_gc: Optional[str] = "No"
    notified_owner: Optional[str] = "No"
    notified_osha: Optional[str] = "No"
    notified_other: Optional[str] = ""

    photos: List[str] = Field(default_factory=list)

    reporter_signature: Optional[str] = ""
    supervisor_signature: Optional[str] = ""
    distribution_list: Optional[List[str]] = Field(default=None, max_length=20)


class Incident(IncidentCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class IncidentSummary(BaseModel):
    id: str
    project_name: str
    location: str
    incident_date: str
    incident_type: str
    severity: str
    person_name: str
    reported_by: str
    osha_recordable: str
    photo_count: int
    created_at: str


# ============================================================
# Route registration
# ============================================================
def register_safety_routes(api_router: APIRouter, db, require_admin, rate_limit_public_post, schedule_auto_email):
    """Attach Inspection / Meeting / JHP / Incident endpoints to the router."""

    # ---------- Inspections ----------
    @api_router.post("/inspections", response_model=Inspection, dependencies=[Depends(rate_limit_public_post)])
    async def create_inspection(payload: InspectionCreate):
        inspection = Inspection(**payload.model_dump())
        doc = inspection.model_dump()
        await db.inspections.insert_one(doc)
        doc.pop("_id", None)
        schedule_auto_email("inspection", doc)
        return inspection

    @api_router.get("/inspections", response_model=List[InspectionSummary])
    async def list_inspections(_: bool = Depends(require_admin)):
        pipeline = [
            {"$sort": {"created_at": -1}},
            {"$limit": 1000},
            {"$project": {
                "_id": 0, "id": 1, "project_name": 1, "location": 1,
                "inspection_date": 1, "inspector_name": 1, "foreman_name": 1,
                "hazards_observed": 1, "stop_work_issued": 1, "created_at": 1,
                "score": 1, "status": 1, "auto_fail_count": 1,
                "graded_yes": 1, "graded_no": 1, "graded_total": 1,
                "photo_count": {"$size": {"$ifNull": ["$photos", []]}},
            }},
        ]
        docs = await db.inspections.aggregate(pipeline).to_list(1000)
        return [
            InspectionSummary(
                id=d.get("id", ""),
                project_name=d.get("project_name", ""),
                location=d.get("location", ""),
                inspection_date=d.get("inspection_date", ""),
                inspector_name=d.get("inspector_name", ""),
                foreman_name=d.get("foreman_name", ""),
                hazards_observed=d.get("hazards_observed", "No"),
                stop_work_issued=d.get("stop_work_issued", "No"),
                photo_count=d.get("photo_count", 0) or 0,
                created_at=d.get("created_at", ""),
                score=d.get("score"),
                status=d.get("status"),
                auto_fail_count=d.get("auto_fail_count", 0),
                graded_yes=d.get("graded_yes", 0),
                graded_no=d.get("graded_no", 0),
                graded_total=d.get("graded_total", 0),
            )
            for d in docs
        ]

    @api_router.get("/inspections/{inspection_id}")
    async def get_inspection(inspection_id: str, _: bool = Depends(require_admin)):
        doc = await db.inspections.find_one({"id": inspection_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Inspection not found")
        return doc

    @api_router.delete("/inspections/{inspection_id}")
    async def delete_inspection(inspection_id: str, _: bool = Depends(require_admin)):
        result = await db.inspections.delete_one({"id": inspection_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Inspection not found")
        return {"deleted": True, "id": inspection_id}

    # ---------- Meetings ----------
    @api_router.post("/meetings", response_model=Meeting, dependencies=[Depends(rate_limit_public_post)])
    async def create_meeting(payload: MeetingCreate):
        meeting = Meeting(**payload.model_dump())
        doc = meeting.model_dump()
        await db.meetings.insert_one(doc)
        doc.pop("_id", None)
        schedule_auto_email("meeting", doc)
        return meeting

    @api_router.get("/meetings", response_model=List[MeetingSummary])
    async def list_meetings(_: bool = Depends(require_admin)):
        cursor = db.meetings.find(
            {},
            {"_id": 0, "id": 1, "project_name": 1, "location": 1, "meeting_date": 1,
             "conducted_by": 1, "topic": 1, "topic_category": 1, "attendees": 1, "created_at": 1},
        ).sort("created_at", -1)
        docs = await cursor.to_list(1000)
        return [
            MeetingSummary(
                id=d.get("id", ""),
                project_name=d.get("project_name", ""),
                location=d.get("location", ""),
                meeting_date=d.get("meeting_date", ""),
                conducted_by=d.get("conducted_by", ""),
                topic=d.get("topic", ""),
                topic_category=d.get("topic_category", ""),
                attendee_count=len(d.get("attendees", []) or []),
                created_at=d.get("created_at", ""),
            )
            for d in docs
        ]

    @api_router.get("/meetings/{meeting_id}")
    async def get_meeting(meeting_id: str, _: bool = Depends(require_admin)):
        doc = await db.meetings.find_one({"id": meeting_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return doc

    @api_router.delete("/meetings/{meeting_id}")
    async def delete_meeting(meeting_id: str, _: bool = Depends(require_admin)):
        result = await db.meetings.delete_one({"id": meeting_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return {"deleted": True, "id": meeting_id}

    # ---------- JHPs ----------
    @api_router.post("/jhas", response_model=Jha, dependencies=[Depends(rate_limit_public_post)])
    async def create_jha(payload: JhaCreate):
        jha = Jha(**payload.model_dump())
        doc = jha.model_dump()
        await db.jhas.insert_one(doc)
        doc.pop("_id", None)
        schedule_auto_email("jha", doc)
        return jha

    @api_router.get("/jhas", response_model=List[JhaSummary])
    async def list_jhas(_: bool = Depends(require_admin)):
        cursor = db.jhas.find(
            {},
            {"_id": 0, "id": 1, "project_name": 1, "location": 1, "jha_date": 1,
             "crew_lead": 1, "job_title": 1, "task_steps": 1, "crew_signoffs": 1, "created_at": 1},
        ).sort("created_at", -1)
        docs = await cursor.to_list(1000)
        return [
            JhaSummary(
                id=d.get("id", ""),
                project_name=d.get("project_name", ""),
                location=d.get("location", ""),
                jha_date=d.get("jha_date", ""),
                crew_lead=d.get("crew_lead", ""),
                job_title=d.get("job_title", ""),
                step_count=len(d.get("task_steps", []) or []),
                signoff_count=len(d.get("crew_signoffs", []) or []),
                created_at=d.get("created_at", ""),
            )
            for d in docs
        ]

    @api_router.get("/jhas/{jha_id}")
    async def get_jha(jha_id: str, _: bool = Depends(require_admin)):
        doc = await db.jhas.find_one({"id": jha_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="JHP not found")
        return doc

    @api_router.delete("/jhas/{jha_id}")
    async def delete_jha(jha_id: str, _: bool = Depends(require_admin)):
        result = await db.jhas.delete_one({"id": jha_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="JHP not found")
        return {"deleted": True, "id": jha_id}

    # ---------- Incidents ----------
    @api_router.post("/incidents", response_model=Incident, dependencies=[Depends(rate_limit_public_post)])
    async def create_incident(payload: IncidentCreate):
        incident = Incident(**payload.model_dump())
        doc = incident.model_dump()
        await db.incidents.insert_one(doc)
        doc.pop("_id", None)
        schedule_auto_email("incident", doc)
        return incident

    @api_router.get("/incidents", response_model=List[IncidentSummary])
    async def list_incidents(_: bool = Depends(require_admin)):
        pipeline = [
            {"$sort": {"created_at": -1}},
            {"$limit": 1000},
            {"$project": {
                "_id": 0, "id": 1, "project_name": 1, "location": 1, "incident_date": 1,
                "incident_type": 1, "severity": 1, "person_name": 1, "reported_by": 1,
                "osha_recordable": 1, "created_at": 1,
                "photo_count": {"$size": {"$ifNull": ["$photos", []]}},
            }},
        ]
        docs = await db.incidents.aggregate(pipeline).to_list(1000)
        return [
            IncidentSummary(
                id=d.get("id", ""),
                project_name=d.get("project_name", ""),
                location=d.get("location", ""),
                incident_date=d.get("incident_date", ""),
                incident_type=d.get("incident_type", ""),
                severity=d.get("severity", ""),
                person_name=d.get("person_name", ""),
                reported_by=d.get("reported_by", ""),
                osha_recordable=d.get("osha_recordable", "No"),
                photo_count=d.get("photo_count", 0) or 0,
                created_at=d.get("created_at", ""),
            )
            for d in docs
        ]

    @api_router.get("/incidents/{incident_id}")
    async def get_incident(incident_id: str, _: bool = Depends(require_admin)):
        doc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Incident not found")
        return doc

    @api_router.delete("/incidents/{incident_id}")
    async def delete_incident(incident_id: str, _: bool = Depends(require_admin)):
        result = await db.incidents.delete_one({"id": incident_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Incident not found")
        return {"deleted": True, "id": incident_id}

from fastapi import FastAPI, APIRouter, HTTPException, Header, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import hashlib
import hmac
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="MASCI Job Site Safety Inspection API")
api_router = APIRouter(prefix="/api")


# ------------------------- Admin auth -------------------------
# Simple shared-password gate. The "token" returned to the client is a
# deterministic HMAC(password, server-secret) so the password itself never
# leaves the device after login. On every protected request the client
# sends X-Admin-Token; we recompute and compare in constant time.
def _admin_token_for(password: str) -> str:
    secret = os.environ.get("MONGO_URL", "masci-default-secret").encode()
    return hmac.new(secret, password.encode(), hashlib.sha256).hexdigest()


def require_admin(x_admin_token: Optional[str] = Header(default=None)):
    """FastAPI dependency. Reject unless the request carries a valid token."""
    expected_pw = os.environ.get("ADMIN_PASSWORD", "")
    if not expected_pw:
        # No password configured → admin gate disabled (open mode)
        return True
    if not x_admin_token:
        raise HTTPException(status_code=401, detail="Admin login required")
    expected = _admin_token_for(expected_pw)
    if not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return True


class AdminLoginRequest(BaseModel):
    password: str


@api_router.post("/admin/login")
async def admin_login(body: AdminLoginRequest):
    expected_pw = os.environ.get("ADMIN_PASSWORD", "")
    if not expected_pw:
        # Gate disabled — anyone can "log in"
        return {"ok": True, "token": "open-mode"}
    if not hmac.compare_digest(body.password, expected_pw):
        raise HTTPException(status_code=401, detail="Wrong password")
    return {"ok": True, "token": _admin_token_for(expected_pw)}


@api_router.get("/admin/check")
async def admin_check(_: bool = Depends(require_admin)):
    """Frontend pings this to verify a stored token is still valid."""
    return {"ok": True}


# ------------------------- Models -------------------------
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
    hazards_observed: str = "No"  # Yes / No
    stop_work_issued: str = "No"
    corrected_on_site: str = "N/A"
    responsible_party: Optional[str] = ""
    corrective_action_notes: Optional[str] = ""
    photos: List[str] = Field(default_factory=list)  # base64 data URLs

    # Signatures (base64 PNG data URLs)
    inspector_signature: Optional[str] = ""
    foreman_signature: Optional[str] = ""

    # Grading (computed on the client at submit time)
    score: Optional[int] = None  # 0-100
    status: Optional[str] = None  # "PASS" | "FAIL"
    auto_fail_count: Optional[int] = 0
    graded_yes: Optional[int] = 0
    graded_no: Optional[int] = 0
    graded_total: Optional[int] = 0


class Inspection(InspectionCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


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


# ------------------------- Routes -------------------------
@api_router.get("/")
async def root():
    return {"message": "MASCI Inspection API", "ok": True}


@api_router.post("/inspections", response_model=Inspection)
async def create_inspection(payload: InspectionCreate):
    inspection = Inspection(**payload.model_dump())
    doc = inspection.model_dump()
    await db.inspections.insert_one(doc)
    # Strip Mongo's _id (insert_one mutates `doc`)
    doc.pop("_id", None)
    schedule_auto_email("inspection", doc)
    return inspection


@api_router.get("/inspections", response_model=List[InspectionSummary])
async def list_inspections(_: bool = Depends(require_admin)):
    cursor = db.inspections.find(
        {},
        {
            "_id": 0,
            "id": 1,
            "project_name": 1,
            "location": 1,
            "inspection_date": 1,
            "inspector_name": 1,
            "foreman_name": 1,
            "hazards_observed": 1,
            "stop_work_issued": 1,
            "photos": 1,
            "created_at": 1,
            "score": 1,
            "status": 1,
            "auto_fail_count": 1,
            "graded_yes": 1,
            "graded_no": 1,
            "graded_total": 1,
        },
    ).sort("created_at", -1)
    docs = await cursor.to_list(1000)
    summaries = []
    for d in docs:
        summaries.append(
            InspectionSummary(
                id=d.get("id", ""),
                project_name=d.get("project_name", ""),
                location=d.get("location", ""),
                inspection_date=d.get("inspection_date", ""),
                inspector_name=d.get("inspector_name", ""),
                foreman_name=d.get("foreman_name", ""),
                hazards_observed=d.get("hazards_observed", "No"),
                stop_work_issued=d.get("stop_work_issued", "No"),
                photo_count=len(d.get("photos", []) or []),
                created_at=d.get("created_at", ""),
                score=d.get("score"),
                status=d.get("status"),
                auto_fail_count=d.get("auto_fail_count", 0),
                graded_yes=d.get("graded_yes", 0),
                graded_no=d.get("graded_no", 0),
                graded_total=d.get("graded_total", 0),
            )
        )
    return summaries


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


# ============================================================
# Site Safety Meetings (Toolbox Talks)
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
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


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


@api_router.post("/meetings", response_model=Meeting)
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
        {
            "_id": 0,
            "id": 1,
            "project_name": 1,
            "location": 1,
            "meeting_date": 1,
            "conducted_by": 1,
            "topic": 1,
            "topic_category": 1,
            "attendees": 1,
            "created_at": 1,
        },
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


# ============================================================
# Job Hazard Analysis (JHA / JSA)
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
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


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


@api_router.post("/jhas", response_model=Jha)
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
        {
            "_id": 0,
            "id": 1,
            "project_name": 1,
            "location": 1,
            "jha_date": 1,
            "crew_lead": 1,
            "job_title": 1,
            "task_steps": 1,
            "crew_signoffs": 1,
            "created_at": 1,
        },
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
        raise HTTPException(status_code=404, detail="JHA not found")
    return doc


@api_router.delete("/jhas/{jha_id}")
async def delete_jha(jha_id: str, _: bool = Depends(require_admin)):
    result = await db.jhas.delete_one({"id": jha_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="JHA not found")
    return {"deleted": True, "id": jha_id}


# ============================================================
# Accident / Incident Reports
# ============================================================
class IncidentCreate(BaseModel):
    """Loose schema – the incident form is large, several optional sections."""
    model_config = ConfigDict(extra="allow")

    project_name: str
    project_number: Optional[str] = ""
    location: str
    incident_date: str  # YYYY-MM-DD
    incident_time: str  # HH:MM
    reported_date: str
    reported_by: str
    supervisor_name: Optional[str] = ""

    incident_type: str
    severity: str  # near_miss / first_aid / medical / restricted / lost_time / fatality
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


class Incident(IncidentCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


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


@api_router.post("/incidents", response_model=Incident)
async def create_incident(payload: IncidentCreate):
    incident = Incident(**payload.model_dump())
    doc = incident.model_dump()
    await db.incidents.insert_one(doc)
    doc.pop("_id", None)
    schedule_auto_email("incident", doc)
    return incident


@api_router.get("/incidents", response_model=List[IncidentSummary])
async def list_incidents(_: bool = Depends(require_admin)):
    cursor = db.incidents.find(
        {},
        {
            "_id": 0,
            "id": 1,
            "project_name": 1,
            "location": 1,
            "incident_date": 1,
            "incident_type": 1,
            "severity": 1,
            "person_name": 1,
            "reported_by": 1,
            "osha_recordable": 1,
            "photos": 1,
            "created_at": 1,
        },
    ).sort("created_at", -1)
    docs = await cursor.to_list(1000)
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
            photo_count=len(d.get("photos", []) or []),
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


# ============================================================
# Daily Job Reports
# ============================================================
class DailyReportCreate(BaseModel):
    """Daily site activity log (replaces Fieldwire daily reports)."""
    model_config = ConfigDict(extra="allow")

    project_name: str
    project_number: Optional[str] = ""
    location: str
    report_date: str  # YYYY-MM-DD
    report_number: Optional[str] = ""
    prepared_by: str
    superintendent: Optional[str] = ""

    weather_summary: Optional[str] = ""
    weather_snapshots: List[Dict[str, Any]] = Field(default_factory=list)

    schedule_delays: Optional[str] = "No"
    schedule_delays_notes: Optional[str] = ""
    weather_impact: Optional[str] = "No"
    weather_impact_notes: Optional[str] = ""
    safety_incidents_today: Optional[str] = "No"
    injuries_reported: Optional[str] = "No"
    incident_notes: Optional[str] = ""
    # Safety-escalation gate (required when accident=Yes OR injury=Yes)
    safety_notified: Optional[str] = ""
    safety_contact_person: Optional[str] = ""
    safety_contact_time: Optional[str] = ""
    incident_report_filled: Optional[str] = ""
    incident_report_time: Optional[str] = ""
    general_notes: Optional[str] = ""

    masci_crews: List[Dict[str, Any]] = Field(default_factory=list)
    subcontractors: List[Dict[str, Any]] = Field(default_factory=list)
    visitors: List[Dict[str, Any]] = Field(default_factory=list)
    equipment: List[Dict[str, Any]] = Field(default_factory=list)
    materials: List[Dict[str, Any]] = Field(default_factory=list)
    activities: List[Dict[str, Any]] = Field(default_factory=list)

    photos: List[str] = Field(default_factory=list)

    prepared_by_signature: Optional[str] = ""
    superintendent_signature: Optional[str] = ""


class DailyReport(DailyReportCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class DailyReportSummary(BaseModel):
    id: str
    project_name: str
    project_number: str
    location: str
    report_date: str
    prepared_by: str
    weather_summary: str
    photo_count: int
    crew_count: int
    sub_count: int
    visitor_count: int
    created_at: str


@api_router.post("/daily-reports", response_model=DailyReport)
async def create_daily_report(payload: DailyReportCreate):
    report = DailyReport(**payload.model_dump())
    doc = report.model_dump()
    await db.daily_reports.insert_one(doc)
    doc.pop("_id", None)
    schedule_auto_email("daily-report", doc)
    return report


@api_router.get("/daily-reports", response_model=List[DailyReportSummary])
async def list_daily_reports(_: bool = Depends(require_admin)):
    cursor = db.daily_reports.find(
        {},
        {
            "_id": 0,
            "id": 1,
            "project_name": 1,
            "project_number": 1,
            "location": 1,
            "report_date": 1,
            "prepared_by": 1,
            "weather_summary": 1,
            "photos": 1,
            "masci_crews": 1,
            "subcontractors": 1,
            "visitors": 1,
            "created_at": 1,
        },
    ).sort("created_at", -1)
    docs = await cursor.to_list(1000)
    return [
        DailyReportSummary(
            id=d.get("id", ""),
            project_name=d.get("project_name", ""),
            project_number=d.get("project_number", ""),
            location=d.get("location", ""),
            report_date=d.get("report_date", ""),
            prepared_by=d.get("prepared_by", ""),
            weather_summary=d.get("weather_summary", ""),
            photo_count=len(d.get("photos", []) or []),
            crew_count=len(d.get("masci_crews", []) or []),
            sub_count=len(d.get("subcontractors", []) or []),
            visitor_count=len(d.get("visitors", []) or []),
            created_at=d.get("created_at", ""),
        )
        for d in docs
    ]


@api_router.get("/daily-reports/{report_id}")
async def get_daily_report(report_id: str, _: bool = Depends(require_admin)):
    doc = await db.daily_reports.find_one({"id": report_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Daily report not found")
    return doc


@api_router.delete("/daily-reports/{report_id}")
async def delete_daily_report(report_id: str, _: bool = Depends(require_admin)):
    result = await db.daily_reports.delete_one({"id": report_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Daily report not found")
    return {"deleted": True, "id": report_id}


# ============================================================
# Translation (Spanish → English on submit)
# ============================================================
# Crews can fill any form in Spanish, but every saved record + printed PDF
# must be 100% English (legal/OSHA requirement). At submit time the frontend
# sends the freeform user-typed string leaves to this endpoint, which calls
# Claude Haiku 4.5 via the Emergent universal LLM key and returns the same
# dict shape with English values.

class TranslateRequest(BaseModel):
    from_lang: str = "es"
    to_lang: str = "en"
    strings: Dict[str, str] = Field(default_factory=dict)


class TranslateResponse(BaseModel):
    strings: Dict[str, str]


import json as _json  # noqa: E402  (kept local to this section)


@api_router.post("/translate", response_model=TranslateResponse)
async def translate_strings(payload: TranslateRequest):
    """Translate a flat {key: string} dict between languages.

    Returns the same keys with translated values. If translation fails we
    return the original strings unchanged so the form submit is never
    blocked. Empty input is a no-op.
    """
    if not payload.strings:
        return TranslateResponse(strings={})

    # Short-circuit when source & target are identical
    if payload.from_lang == payload.to_lang:
        return TranslateResponse(strings=payload.strings)

    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        logger.warning("EMERGENT_LLM_KEY missing — returning input unchanged")
        return TranslateResponse(strings=payload.strings)

    # Lazy import so cold-start of the rest of the API isn't blocked.
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
    except Exception as e:  # pragma: no cover
        logger.error(f"emergentintegrations import failed: {e}")
        return TranslateResponse(strings=payload.strings)

    system = (
        "You are a translator for a US construction safety reporting app. "
        "Translate values from {src} to {dst}. The text comes from heavy-civil "
        "construction crews — preserve technical terms (e.g. excavator, MOT, PPE, "
        "rebar, lift station, foreman), proper nouns, and numbers exactly. "
        "Keep the SAME JSON shape: input is a JSON object whose values are the "
        "strings to translate; reply with ONLY a JSON object using the SAME keys "
        "and translated values — no commentary, no markdown fences."
    ).format(src=payload.from_lang, dst=payload.to_lang)

    user_text = (
        "Translate every value in this JSON object. Reply with the JSON object "
        "only, same keys, translated values:\n\n"
        + _json.dumps(payload.strings, ensure_ascii=False)
    )

    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"translate-{uuid.uuid4().hex[:8]}",
            system_message=system,
        ).with_model("anthropic", "claude-haiku-4-5-20251001")

        response = await chat.send_message(UserMessage(text=user_text))
        text = (response or "").strip()

        # Strip optional ```json fences if the model added them
        if text.startswith("```"):
            text = text.strip("`")
            # remove leading "json\n" if present
            if text.lower().startswith("json"):
                text = text[4:].lstrip("\n")

        # Find the first { … } block
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"No JSON object in response: {text[:200]}")
        parsed = _json.loads(text[start : end + 1])
        if not isinstance(parsed, dict):
            raise ValueError("LLM did not return a JSON object")

        # Only keep string values; fall back to original where missing
        out = {}
        for k, original in payload.strings.items():
            v = parsed.get(k)
            out[k] = v if isinstance(v, str) and v.strip() else original
        return TranslateResponse(strings=out)
    except Exception as e:
        logger.exception(f"Translation failed: {e}")
        return TranslateResponse(strings=payload.strings)


app.include_router(api_router)


# ============================================================
# Email a saved record as a PDF (Resend)
# ============================================================
# Independent router so it imports at startup without forcing a hot-reload
# of the existing routes. Adds POST /api/email-report which:
#   1. Looks up the saved record by id from its module's collection.
#   2. Renders it to a polished PDF via /app/backend/pdf_render.py.
#   3. Sends via Resend with the PDF attached.

import asyncio  # noqa: E402
import base64 as _email_b64  # noqa: E402

from pdf_render import (  # noqa: E402
    render_email_html,
    render_record_pdf,
    KIND_TITLES,
)
from pm_routing import (  # noqa: E402
    PM_TABLE,
    ALWAYS_CC,
    auto_email_enabled,
    recipients_for_record,
)


_KIND_TO_COLLECTION = {
    "inspection": "inspections",
    "meeting": "meetings",
    "jha": "jhas",
    "incident": "incidents",
    "daily-report": "daily_reports",
}


# ------------------------------------------------------------------
# Auto-email on submit (fire-and-forget — never blocks the response)
# ------------------------------------------------------------------
def _filename_for(kind: str, record: dict) -> str:
    project = record.get("project_name") or "MASCI"
    date_part = (
        record.get("report_date")
        or record.get("inspection_date")
        or record.get("meeting_date")
        or record.get("jha_date")
        or record.get("incident_date")
        or ""
    )
    safe_proj = "".join(
        c if c.isalnum() else "_" for c in str(project)[:40]
    ).strip("_")
    return f"MASCI-{kind}-{safe_proj}-{date_part}.pdf".replace("--", "-")


def _is_severe_incident(record: dict) -> bool:
    """Major/severe incident → always include OSHA-recordable + work-stopped flag."""
    sev = (record.get("severity") or "").strip().lower()
    severe = {"medical", "restricted", "lost_time", "fatality"}
    if sev in severe:
        return True
    if (record.get("osha_recordable") or "").strip().lower() == "yes":
        return True
    if (record.get("work_stopped") or "").strip().lower() == "yes":
        return True
    return False


async def _dispatch_auto_email(kind: str, record: dict) -> None:
    """Render PDF + send via Resend to the assigned PM and the always-CC list.

    Wrapped in a broad try/except so a missing API key, Resend outage, or PDF
    error never causes the original POST to fail. Logs at WARNING level when
    skipped and ERROR when something unexpected breaks.
    """
    try:
        if not auto_email_enabled():
            logger.info(
                "auto-email skipped (RESEND_API_KEY missing or AUTO_EMAIL_REPORTS=false) "
                f"— {kind} {record.get('id')}"
            )
            return

        dist = recipients_for_record(record)
        recipients: List[str] = list(dist["all"])  # type: ignore[arg-type]

        # Severity fan-out for incidents (Major/Severe currently mirrors the
        # always-CC; future ops/GC list can be appended here from env.)
        if kind == "incident" and _is_severe_incident(record):
            extra = os.environ.get("SEVERE_INCIDENT_CC", "")
            for e in [x.strip() for x in extra.split(",") if x.strip()]:
                if e.lower() not in {r.lower() for r in recipients}:
                    recipients.append(e)

        if not recipients:
            logger.warning(f"auto-email: no recipients resolved for {kind} {record.get('id')}")
            return

        import resend  # noqa: E402
        resend.api_key = os.environ["RESEND_API_KEY"]
        sender_email = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

        pdf_bytes = await asyncio.to_thread(render_record_pdf, kind, record)

        title = KIND_TITLES.get(kind, "MASCI Safety Record")
        project = record.get("project_name") or "MASCI"
        pm_name = dist.get("pm_name")
        pm_tag = f" · PM: {pm_name}" if pm_name else ""
        subject = f"[MASCI] {title} · {project}{pm_tag}"

        note = ""
        if kind == "incident" and _is_severe_incident(record):
            note = (
                "<p style='color:#C8102E;font-weight:700'>"
                "SEVERE INCIDENT — please review immediately."
                "</p>"
            )
        elif pm_name:
            note = f"<p>Auto-routed to <b>{pm_name}</b> based on project number "\
                   f"<b>{record.get('project_number') or '—'}</b>.</p>"
        else:
            note = (
                "<p><i>No Project Manager could be auto-resolved from the project number "
                f"<b>{record.get('project_number') or '—'}</b>. Sent to office distribution "
                "only — please assign a PM in the office.</i></p>"
            )

        params = {
            "from": f"MASCI Safety <{sender_email}>",
            "to": recipients,
            "subject": subject,
            "html": render_email_html(kind, record, note),
            "attachments": [
                {
                    "filename": _filename_for(kind, record),
                    "content": _email_b64.b64encode(pdf_bytes).decode(),
                }
            ],
        }

        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(
            f"auto-email sent: kind={kind} id={record.get('id')} pm={pm_name} "
            f"to={recipients} resend_id={(result or {}).get('id')}"
        )
    except Exception as e:  # noqa: BLE001
        logger.exception(f"auto-email failed for {kind} {record.get('id')}: {e}")


def schedule_auto_email(kind: str, record: dict) -> None:
    """Fire-and-forget wrapper (safe to call from any create endpoint)."""
    try:
        asyncio.create_task(_dispatch_auto_email(kind, dict(record)))
    except RuntimeError:
        # No running loop — skip silently (e.g. during sync tests)
        pass


# (auto-email-preview / routing-table routes are registered after _email_router below)


class EmailReportRequest(BaseModel):
    kind: str = Field(
        ...,
        description="One of: inspection, meeting, jha, incident, daily-report",
    )
    record_id: str
    recipients: List[str] = Field(..., min_length=1, max_length=20)
    subject: Optional[str] = ""
    note: Optional[str] = ""


_email_router = APIRouter(prefix="/api")


@_email_router.get("/auto-email/preview")
async def auto_email_preview(
    project_number: str = "",
    project_name: str = "",
    severity: str = "",
    osha_recordable: str = "",
    _: bool = Depends(require_admin),
):
    """Admin-only introspection: shows who *would* receive the auto-email
    for a given project_number / project_name."""
    fake = {
        "project_number": project_number,
        "project_name": project_name,
        "severity": severity,
        "osha_recordable": osha_recordable,
    }
    dist = recipients_for_record(fake)
    return {
        "input": fake,
        "pm_name": dist["pm_name"],
        "pm_email": dist["pm_email"],
        "to": dist["to"],
        "cc": dist["cc"],
        "all_recipients": dist["all"],
        "auto_email_enabled": auto_email_enabled(),
        "always_cc": ALWAYS_CC,
    }


@_email_router.get("/auto-email/routing-table")
async def auto_email_routing_table(_: bool = Depends(require_admin)):
    """Returns the full PM → Jobs lookup table (admin-only)."""
    return {
        "always_cc": ALWAYS_CC,
        "auto_email_enabled": auto_email_enabled(),
        "project_managers": [
            {
                "pm_name": pm,
                "pm_email": data["email"],
                "jobs": [
                    {"project_number": jn, "project_name": jname}
                    for (jn, jname) in data["jobs"]  # type: ignore[union-attr]
                ],
            }
            for pm, data in PM_TABLE.items()
        ],
    }


@_email_router.post("/email-report")
async def email_report(
    body: EmailReportRequest, _: bool = Depends(require_admin)
):
    if body.kind not in _KIND_TO_COLLECTION:
        raise HTTPException(status_code=400, detail=f"Unknown kind: {body.kind}")
    coll_name = _KIND_TO_COLLECTION[body.kind]
    coll = getattr(db, coll_name)
    record = await coll.find_one({"id": body.record_id}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="RESEND_API_KEY not configured. Add it to /app/backend/.env and restart backend.",
        )

    sender_email = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

    try:
        import resend  # noqa: E402

        resend.api_key = api_key

        pdf_bytes = render_record_pdf(body.kind, record)
        title = KIND_TITLES.get(body.kind, "MASCI Safety Record")
        project = record.get("project_name") or record.get("project") or "MASCI"
        date_part = (
            record.get("report_date")
            or record.get("date")
            or record.get("incident_date")
            or ""
        )
        safe_proj = "".join(
            c if c.isalnum() else "_" for c in project[:40]
        ).strip("_")
        filename = f"MASCI-{body.kind}-{safe_proj}-{date_part}.pdf".replace(
            "--", "-"
        )

        subject = body.subject or f"{title} · {project}".strip(" ·")

        params = {
            "from": f"MASCI Safety <{sender_email}>",
            "to": [r for r in body.recipients if r and r.strip()],
            "subject": subject,
            "html": render_email_html(body.kind, record, body.note or ""),
            "attachments": [
                {
                    "filename": filename,
                    "content": _email_b64.b64encode(pdf_bytes).decode(),
                }
            ],
        }

        result = await asyncio.to_thread(resend.Emails.send, params)
        return {
            "ok": True,
            "id": (result or {}).get("id"),
            "to": params["to"],
            "filename": filename,
            "size_bytes": len(pdf_bytes),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"email-report failed: {e}")
        raise HTTPException(status_code=500, detail=f"Email send failed: {e}")


app.include_router(_email_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

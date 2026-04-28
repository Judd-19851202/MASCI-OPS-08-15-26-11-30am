from fastapi import FastAPI, APIRouter, HTTPException, Header, Depends, Response, Request, UploadFile, File, Form
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import hashlib
import hmac
import re
import time
import secrets
import asyncio
from collections import defaultdict
from threading import Lock
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Tuple
import uuid
from datetime import datetime, timezone, timedelta


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="MASCI Job Site Safety Inspection API")
api_router = APIRouter(prefix="/api")


# ------------------------- Rate limiting (in-memory, single-instance) -------------------------
# Public POST endpoints (form submissions, translate) are unauthenticated by
# design — crews submit without logging in. To prevent spam / bot abuse we
# cap each IP to N submissions per hour per endpoint. Single-instance backend
# so a process-local dict is sufficient — no Redis required.

_RATE_LOCK = Lock()
_PUBLIC_POST_BUCKETS: Dict[str, List[float]] = defaultdict(list)
_LOGIN_FAIL_BUCKETS: Dict[str, List[float]] = defaultdict(list)

PUBLIC_POST_LIMIT_PER_HOUR = int(os.environ.get("PUBLIC_POST_LIMIT_PER_HOUR", "30"))
LOGIN_MAX_FAILS_PER_WINDOW = int(os.environ.get("LOGIN_MAX_FAILS", "10"))
LOGIN_LOCKOUT_SECONDS = int(os.environ.get("LOGIN_LOCKOUT_SECONDS", "900"))  # 15 min


def _client_ip(request: Request) -> str:
    """Best-effort client IP. Trusts X-Forwarded-For when present (Kubernetes
    ingress sets it). Falls back to the immediate peer IP."""
    xff = request.headers.get("x-forwarded-for") or ""
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit_public_post(request: Request):
    """FastAPI dependency that throttles each (IP, endpoint) to
    PUBLIC_POST_LIMIT_PER_HOUR submissions. Raises 429 when exceeded.
    Set RATE_LIMITING=off in .env to disable (e.g., automated tests)."""
    if os.environ.get("RATE_LIMITING", "on").lower() in ("off", "false", "0"):
        return
    ip = _client_ip(request)
    key = f"{request.url.path}:{ip}"
    now = time.time()
    cutoff = now - 3600
    with _RATE_LOCK:
        bucket = _PUBLIC_POST_BUCKETS[key]
        bucket[:] = [t for t in bucket if t > cutoff]
        if len(bucket) >= PUBLIC_POST_LIMIT_PER_HOUR:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Too many submissions from this device "
                    f"(limit {PUBLIC_POST_LIMIT_PER_HOUR}/hour). "
                    f"Try again later or contact MASCI safety."
                ),
            )
        bucket.append(now)


def _check_login_lockout(ip: str) -> None:
    cutoff = time.time() - LOGIN_LOCKOUT_SECONDS
    with _RATE_LOCK:
        bucket = _LOGIN_FAIL_BUCKETS[ip]
        bucket[:] = [t for t in bucket if t > cutoff]
        if len(bucket) >= LOGIN_MAX_FAILS_PER_WINDOW:
            oldest = bucket[0]
            wait_s = int(LOGIN_LOCKOUT_SECONDS - (time.time() - oldest))
            wait_min = max(1, (wait_s + 59) // 60)
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Too many failed login attempts. "
                    f"Try again in ~{wait_min} minute(s)."
                ),
            )


def _record_login_fail(ip: str) -> None:
    with _RATE_LOCK:
        _LOGIN_FAIL_BUCKETS[ip].append(time.time())


def _reset_login_fails(ip: str) -> None:
    with _RATE_LOCK:
        _LOGIN_FAIL_BUCKETS.pop(ip, None)


# ------------------------- Admin auth -------------------------
# Simple shared-password gate. The "token" returned to the client is a
# deterministic HMAC(password, server-secret) so the password itself never
# leaves the device after login. On every protected request the client
# sends X-Admin-Token; we recompute and compare in constant time.
#
# The HMAC secret is read from ADMIN_HMAC_SECRET (preferred). If not set,
# we generate a random per-process secret and warn — every admin will need
# to log in again on the next backend restart, which is the right safety
# behavior for an unconfigured deployment.
def _admin_hmac_secret() -> bytes:
    explicit = os.environ.get("ADMIN_HMAC_SECRET", "").strip()
    if explicit:
        return explicit.encode()
    # Backwards-compat / first-boot fallback. Cache so all calls within a
    # process see the same value (so tokens stay valid until restart).
    global _ADMIN_HMAC_FALLBACK
    try:
        return _ADMIN_HMAC_FALLBACK
    except NameError:
        pass
    _ADMIN_HMAC_FALLBACK = secrets.token_bytes(64)
    logging.getLogger(__name__).warning(
        "ADMIN_HMAC_SECRET is not set. Generated a random per-process secret. "
        "Admin tokens will invalidate on backend restart — set ADMIN_HMAC_SECRET "
        "in backend/.env to a stable random string for production."
    )
    return _ADMIN_HMAC_FALLBACK


def _admin_token_for(password: str) -> str:
    return hmac.new(_admin_hmac_secret(), password.encode(), hashlib.sha256).hexdigest()


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
async def admin_login(body: AdminLoginRequest, request: Request):
    ip = _client_ip(request)
    _check_login_lockout(ip)
    expected_pw = os.environ.get("ADMIN_PASSWORD", "")
    if not expected_pw:
        # Gate disabled — anyone can "log in"
        return {"ok": True, "token": "open-mode"}
    if not hmac.compare_digest(body.password, expected_pw):
        _record_login_fail(ip)
        raise HTTPException(status_code=401, detail="Wrong password")
    _reset_login_fails(ip)
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


@api_router.post("/inspections", response_model=Inspection, dependencies=[Depends(rate_limit_public_post)])
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
    # Phase 4: ad-hoc CC list. Every email in this array is added to the
    # auto-email distribution for this record. Max 20 addresses.
    distribution_list: Optional[List[str]] = Field(default=None, max_length=20)


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
    # Phase 4: ad-hoc CC list (GCs / DOT / additional owners).
    distribution_list: Optional[List[str]] = Field(default=None, max_length=20)


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


@api_router.post("/daily-reports", response_model=DailyReport, dependencies=[Depends(rate_limit_public_post)])
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
# Job Hazard Plans (per-job PDF repository — admin uploads, crews view)
# ============================================================
class JobHazardPlanUpload(BaseModel):
    """Admin uploads (or replaces) a Job Hazard Plan for one project."""
    project_number: str
    project_name: str = ""
    location: str = ""
    filename: str
    content_type: str = "application/pdf"
    file_data: str  # data URL: "data:application/pdf;base64,<...>"
    notes: Optional[str] = ""
    uploaded_by: Optional[str] = ""


class JobHazardPlan(BaseModel):
    id: str
    project_number: str
    project_name: str = ""
    location: str = ""
    filename: str
    content_type: str = "application/pdf"
    file_size: int = 0
    notes: Optional[str] = ""
    uploaded_by: Optional[str] = ""
    uploaded_at: str


def _data_url_to_bytes(data_url: str) -> Tuple[bytes, str]:
    """Parse `data:<mime>;base64,<...>` → (raw_bytes, mime). Raises on bad format."""
    if not data_url or "," not in data_url:
        raise ValueError("file_data must be a data URL")
    head, b64 = data_url.split(",", 1)
    mime = "application/octet-stream"
    if head.startswith("data:") and ";base64" in head:
        mime = head[5:].split(";", 1)[0] or mime
    try:
        raw = _email_b64.b64decode(b64)
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"file_data base64 decode failed: {e}")
    return raw, mime


def _validate_pdf_or_400(raw: bytes) -> None:
    """Reject anything that isn't a real PDF. Without this an admin (or
    anyone with a stolen admin token) could upload an HTML/JS file claiming
    to be application/pdf and serve XSS via the /file download endpoint."""
    if not raw or len(raw) < 5 or not raw.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a valid PDF. Magic bytes mismatch.",
        )


@api_router.get("/job-hazard-plans", response_model=List[JobHazardPlan])
async def list_job_hazard_plans():
    """Public — list every uploaded plan (without the heavy file payload)."""
    cursor = db.job_hazard_plans.find(
        {},
        {
            "_id": 0,
            "file_data": 0,  # exclude the base64 blob
        },
    ).sort("project_number", 1)
    docs = await cursor.to_list(2000)
    return [JobHazardPlan(**d) for d in docs]


@api_router.get("/job-hazard-plans/{project_number}/file")
async def download_job_hazard_plan(project_number: str):
    """Public — stream the raw PDF for a given project number."""
    doc = await db.job_hazard_plans.find_one({"project_number": project_number}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="No plan uploaded for this job yet")
    try:
        raw, mime = _data_url_to_bytes(doc.get("file_data") or "")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Stored file is corrupt: {e}")

    safe_name = "".join(
        c if c.isalnum() or c in ("-", "_", ".", " ") else "_"
        for c in (doc.get("filename") or f"JHA_{project_number}.pdf")
    )
    return Response(
        content=raw,
        # Force application/pdf so a maliciously-MIME'd upload can never
        # be rendered as HTML/JS in the browser (defense in depth — we
        # also reject non-PDF magic bytes at upload time).
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{safe_name}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@api_router.post("/job-hazard-plans", response_model=JobHazardPlan)
async def upload_job_hazard_plan(
    payload: JobHazardPlanUpload,
    _: bool = Depends(require_admin),
):
    """Admin — upload (or REPLACE) a Job Hazard Plan PDF for one project number.
    Idempotent on project_number — uploading again replaces the prior file."""
    raw, mime = _data_url_to_bytes(payload.file_data)
    _validate_pdf_or_400(raw)
    if len(raw) > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(raw)//1024} KB). Max 25 MB per plan.",
        )

    pn = payload.project_number.strip()
    if not pn:
        raise HTTPException(status_code=400, detail="project_number is required")

    plan_id = str(uuid.uuid4())
    doc = {
        "id": plan_id,
        "project_number": pn,
        "project_name": (payload.project_name or "").strip(),
        "location": (payload.location or "").strip(),
        "filename": payload.filename,
        "content_type": mime,
        "file_size": len(raw),
        "file_data": payload.file_data,
        "notes": (payload.notes or "").strip(),
        "uploaded_by": (payload.uploaded_by or "").strip(),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    # Upsert — one plan per project number (replace on re-upload)
    await db.job_hazard_plans.update_one(
        {"project_number": pn},
        {"$set": doc},
        upsert=True,
    )
    fresh = await db.job_hazard_plans.find_one(
        {"project_number": pn}, {"_id": 0, "file_data": 0}
    )
    return JobHazardPlan(**fresh)


@api_router.delete("/job-hazard-plans/{project_number}")
async def delete_job_hazard_plan(
    project_number: str,
    _: bool = Depends(require_admin),
):
    res = await db.job_hazard_plans.delete_one({"project_number": project_number})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="No plan exists for this project")
    return {"deleted": True, "project_number": project_number}


# ============================================================
# Trench Box Tabulated Data (OSHA 1926 Subpart P)
# ============================================================
class TrenchBoxCreate(BaseModel):
    """OSHA tabulated-data record for one trench shield / box. Filled by
    admin from the manufacturer's data plate — crews then browse read-only."""
    manufacturer: str
    model: str
    serial_number: Optional[str] = ""
    box_type: Optional[str] = ""  # e.g. "Steel", "Aluminum", "Modular"
    length_ft: Optional[str] = ""
    width_min_ft: Optional[str] = ""  # narrowest spread
    width_max_ft: Optional[str] = ""  # widest spread
    sidewall_height_ft: Optional[str] = ""
    sidewall_thickness_in: Optional[str] = ""
    weight_lbs: Optional[str] = ""

    # Maximum allowable depth by soil type (per OSHA 1926.652 / 1926 Subpart P)
    max_depth_type_a_ft: Optional[str] = ""
    max_depth_type_b_ft: Optional[str] = ""
    max_depth_type_c_60_ft: Optional[str] = ""  # C-60 (60° slope)
    max_depth_type_c_80_ft: Optional[str] = ""  # C-80 (80° slope)

    spreader_count: Optional[str] = ""
    stacking_allowed: Optional[str] = "No"
    stacking_max: Optional[str] = ""

    notes: Optional[str] = ""
    # Optional manufacturer tabulated-data PDF (data URL, max 10 MB)
    tabulated_data_file: Optional[str] = ""
    tabulated_data_filename: Optional[str] = ""


class TrenchBox(TrenchBoxCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@api_router.get("/trench-boxes", response_model=List[TrenchBox])
async def list_trench_boxes():
    """Public — every crew can browse to see what's OSHA-legal for what depth."""
    cursor = db.trench_boxes.find(
        {},
        {
            "_id": 0,
            "tabulated_data_file": 0,  # excluded from list (heavy)
        },
    ).sort([("manufacturer", 1), ("model", 1)])
    docs = await cursor.to_list(500)
    # Re-include empty placeholder so Pydantic doesn't choke
    for d in docs:
        d.setdefault("tabulated_data_file", "")
    return [TrenchBox(**d) for d in docs]


@api_router.get("/trench-boxes/{box_id}", response_model=TrenchBox)
async def get_trench_box(box_id: str):
    """Public — full record for one trench box (without the file payload)."""
    doc = await db.trench_boxes.find_one(
        {"id": box_id}, {"_id": 0, "tabulated_data_file": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Trench box not found")
    doc.setdefault("tabulated_data_file", "")
    return TrenchBox(**doc)


@api_router.get("/trench-boxes/{box_id}/file")
async def download_trench_box_file(box_id: str):
    """Public — stream the manufacturer's tabulated-data PDF (if uploaded)."""
    doc = await db.trench_boxes.find_one({"id": box_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Trench box not found")
    data_url = doc.get("tabulated_data_file") or ""
    if not data_url:
        raise HTTPException(
            status_code=404,
            detail="No manufacturer tabulated-data PDF uploaded for this box",
        )
    try:
        raw, mime = _data_url_to_bytes(data_url)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"File corrupt: {e}")
    safe_name = "".join(
        c if c.isalnum() or c in ("-", "_", ".", " ") else "_"
        for c in (doc.get("tabulated_data_filename")
                  or f"TabData_{doc.get('manufacturer', '')}_{doc.get('model', '')}.pdf")
    )
    return Response(
        content=raw,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{safe_name}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@api_router.post("/trench-boxes", response_model=TrenchBox)
async def create_trench_box(
    payload: TrenchBoxCreate,
    _: bool = Depends(require_admin),
):
    if not payload.manufacturer.strip() or not payload.model.strip():
        raise HTTPException(
            status_code=400, detail="manufacturer and model are required"
        )
    # Lightly validate optional file size
    if payload.tabulated_data_file:
        raw, _ = _data_url_to_bytes(payload.tabulated_data_file)
        _validate_pdf_or_400(raw)
        if len(raw) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"Tabulated-data file too large ({len(raw)//1024} KB). Max 10 MB.",
            )
    box = TrenchBox(**payload.model_dump())
    doc = box.model_dump()
    await db.trench_boxes.insert_one(doc)
    doc.pop("_id", None)
    # Don't echo the file blob back
    doc.pop("tabulated_data_file", None)
    doc["tabulated_data_file"] = ""
    return TrenchBox(**doc)


@api_router.put("/trench-boxes/{box_id}", response_model=TrenchBox)
async def update_trench_box(
    box_id: str,
    payload: TrenchBoxCreate,
    _: bool = Depends(require_admin),
):
    if payload.tabulated_data_file:
        raw, _ = _data_url_to_bytes(payload.tabulated_data_file)
        _validate_pdf_or_400(raw)
        if len(raw) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
    update = payload.model_dump()
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    # Keep file payload only if user provided a new one
    if not update.get("tabulated_data_file"):
        update.pop("tabulated_data_file", None)
        update.pop("tabulated_data_filename", None)
    res = await db.trench_boxes.update_one({"id": box_id}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Trench box not found")
    fresh = await db.trench_boxes.find_one(
        {"id": box_id}, {"_id": 0, "tabulated_data_file": 0}
    )
    fresh.setdefault("tabulated_data_file", "")
    return TrenchBox(**fresh)


@api_router.delete("/trench-boxes/{box_id}")
async def delete_trench_box(box_id: str, _: bool = Depends(require_admin)):
    res = await db.trench_boxes.delete_one({"id": box_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Trench box not found")
    return {"deleted": True, "id": box_id}







# ============================================================
# Equipment Inspections (OSHA daily pre-op checklist)
# ============================================================
from checklists import CHECKLISTS, EQUIPMENT_TYPES  # noqa: E402


class EquipmentInspectionCreate(BaseModel):
    """Daily pre-shift OSHA equipment inspection."""
    model_config = ConfigDict(extra="allow")

    project_name: str
    project_number: Optional[str] = ""
    location: str
    inspection_date: str  # YYYY-MM-DD
    inspection_time: str  # HH:MM

    operator_name: str
    equipment_type: str  # one of EQUIPMENT_TYPES
    equipment_unit: str  # e.g. "CAT 320 — Unit #7"
    equipment_make: Optional[str] = ""
    equipment_model: Optional[str] = ""
    equipment_serial: Optional[str] = ""

    # Either or both — different machines have different meters
    hour_meter: Optional[str] = ""
    odometer: Optional[str] = ""

    # Checklist results — { section_title: { item: {status: "pass"|"fail"|"na", note: str} } }
    checklist: Dict[str, Any] = Field(default_factory=dict)
    fail_count: int = 0
    pass_count: int = 0
    na_count: int = 0

    # Free-form notes / corrective actions
    deficiency_notes: Optional[str] = ""
    corrective_actions: Optional[str] = ""
    out_of_service: Optional[str] = "No"  # Yes if any FAIL → don't operate

    photos: List[str] = Field(default_factory=list)
    operator_signature: Optional[str] = ""


class EquipmentInspection(EquipmentInspectionCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class EquipmentInspectionSummary(BaseModel):
    id: str
    project_name: str
    project_number: str
    location: str
    inspection_date: str
    operator_name: str
    equipment_type: str
    equipment_unit: str
    fail_count: int
    out_of_service: str
    photo_count: int
    created_at: str


@api_router.get("/equipment-types")
async def list_equipment_types():
    """Public — list of equipment types + checklist templates."""
    return {
        "types": EQUIPMENT_TYPES,
        "checklists": CHECKLISTS,
    }


# Saved equipment units (so operators don't have to re-type unit numbers).
class EquipmentUnitCreate(BaseModel):
    equipment_type: str
    unit_label: str  # e.g. "CAT 320 #7" — what shows in the dropdown
    make: Optional[str] = ""
    model: Optional[str] = ""
    serial: Optional[str] = ""


class EquipmentUnit(EquipmentUnitCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@api_router.get("/equipment-units", response_model=List[EquipmentUnit])
async def list_equipment_units(equipment_type: Optional[str] = None):
    q = {"equipment_type": equipment_type} if equipment_type else {}
    cursor = db.equipment_units.find(q, {"_id": 0}).sort("unit_label", 1)
    docs = await cursor.to_list(500)
    return [EquipmentUnit(**d) for d in docs]


@api_router.post("/equipment-units", response_model=EquipmentUnit, dependencies=[Depends(rate_limit_public_post)])
async def create_equipment_unit(payload: EquipmentUnitCreate):
    # De-dup by (type, label) — return the existing if already saved
    existing = await db.equipment_units.find_one(
        {
            "equipment_type": payload.equipment_type,
            "unit_label": payload.unit_label.strip(),
        },
        {"_id": 0},
    )
    if existing:
        return EquipmentUnit(**existing)
    unit = EquipmentUnit(**payload.model_dump())
    doc = unit.model_dump()
    await db.equipment_units.insert_one(doc)
    doc.pop("_id", None)
    return unit


# ---------------------------------------------------------------------------
# Equipment Master Fleet — sourced from MASCI Equipment List.xlsx
# Used to populate equipment dropdowns across all forms (Pre-Op, Daily Reports,
# Incidents, etc.). Operators can still type custom values as a fallback.
# ---------------------------------------------------------------------------
EQUIPMENT_MASTER_SEED_FILE = ROOT_DIR / "data" / "equipment_master.json"


class EquipmentMasterItem(BaseModel):
    unit_number: str = ""
    year: Optional[int] = None
    make_model: str = ""
    plate: str = ""
    vin_serial_number: str = ""
    comments: str = ""
    company: str = ""
    category: str = "Misc Equipment"
    preop_equipment_type: str = "Other"
    display_label: str = ""


@api_router.get("/equipment-master")
async def list_equipment_master(category: Optional[str] = None):
    """Returns the full MASCI fleet, optionally filtered to one category.

    Response shape:
        {
          "categories": ["Excavators", "Loaders", ...],   # alpha order
          "items": [ EquipmentMasterItem, ... ],          # all units
          "grouped": { "Excavators": [item, ...], ... }   # convenience
        }
    """
    q = {"category": category} if category else {}
    cursor = db.equipment_master.find(q, {"_id": 0}).sort(
        [("category", 1), ("unit_number", 1), ("make_model", 1)]
    )
    docs = await cursor.to_list(2000)
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for d in docs:
        grouped.setdefault(d.get("category", "Misc Equipment"), []).append(d)
    categories = sorted(grouped.keys())
    return {
        "categories": categories,
        "items": docs,
        "grouped": grouped,
        "count": len(docs),
    }


async def _seed_equipment_master() -> None:
    """Idempotent seed of the equipment_master collection from JSON file.

    Re-runs whenever the JSON file's item count differs from what's stored
    (so updating the seed file ships new equipment automatically on restart).
    """
    log = logging.getLogger(__name__)
    if not EQUIPMENT_MASTER_SEED_FILE.exists():
        log.info(f"[equipment-master] seed file missing: {EQUIPMENT_MASTER_SEED_FILE}")
        return
    try:
        with open(EQUIPMENT_MASTER_SEED_FILE, "r", encoding="utf-8") as fh:
            import json as _json_em
            seed_items = _json_em.load(fh)
    except Exception as e:
        log.exception(f"[equipment-master] failed to read seed: {e}")
        return

    existing_count = await db.equipment_master.count_documents({})
    if existing_count == len(seed_items) and existing_count > 0:
        return  # already seeded and matches file

    # Replace the collection contents in one go (safe: no FK relationships)
    await db.equipment_master.delete_many({})
    if seed_items:
        # Ensure each row has an id for stable references
        for it in seed_items:
            it.setdefault("id", str(uuid.uuid4()))
        await db.equipment_master.insert_many(seed_items)
        # Also push these into the legacy equipment_units collection so the
        # Pre-Op dropdown picks them up automatically.
        try:
            existing_units = {
                (u.get("equipment_type", ""), u.get("unit_label", "").strip().lower())
                async for u in db.equipment_units.find({}, {"_id": 0, "equipment_type": 1, "unit_label": 1})
            }
            new_units = []
            for it in seed_items:
                etype = it.get("preop_equipment_type") or "Other"
                label = it.get("display_label") or it.get("make_model") or ""
                if not label.strip():
                    continue
                key = (etype, label.strip().lower())
                if key in existing_units:
                    continue
                existing_units.add(key)
                new_units.append({
                    "id": str(uuid.uuid4()),
                    "equipment_type": etype,
                    "unit_label": label.strip(),
                    "make": it.get("make_model", ""),
                    "model": "",
                    "serial": it.get("vin_serial_number", ""),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
            if new_units:
                await db.equipment_units.insert_many(new_units)
        except Exception as e:
            log.exception(f"[equipment-master] equipment_units fan-out failed: {e}")
    log.info(f"[equipment-master] seeded {len(seed_items)} units")


@api_router.post("/equipment-inspections", response_model=EquipmentInspection, dependencies=[Depends(rate_limit_public_post)])
async def create_equipment_inspection(payload: EquipmentInspectionCreate):
    insp = EquipmentInspection(**payload.model_dump())
    doc = insp.model_dump()
    await db.equipment_inspections.insert_one(doc)
    doc.pop("_id", None)
    # Also remember this unit so it shows up in the dropdown next time
    if insp.equipment_unit and insp.equipment_type:
        try:
            await create_equipment_unit(
                EquipmentUnitCreate(
                    equipment_type=insp.equipment_type,
                    unit_label=insp.equipment_unit,
                    make=insp.equipment_make or "",
                    model=insp.equipment_model or "",
                    serial=insp.equipment_serial or "",
                )
            )
        except Exception:
            pass
    schedule_auto_email("equipment-inspection", doc)
    return insp


@api_router.get("/equipment-inspections", response_model=List[EquipmentInspectionSummary])
async def list_equipment_inspections(_: bool = Depends(require_admin)):
    cursor = db.equipment_inspections.find(
        {},
        {
            "_id": 0,
            "id": 1,
            "project_name": 1,
            "project_number": 1,
            "location": 1,
            "inspection_date": 1,
            "operator_name": 1,
            "equipment_type": 1,
            "equipment_unit": 1,
            "fail_count": 1,
            "out_of_service": 1,
            "photos": 1,
            "created_at": 1,
        },
    ).sort("created_at", -1)
    docs = await cursor.to_list(1000)
    return [
        EquipmentInspectionSummary(
            id=d.get("id", ""),
            project_name=d.get("project_name", ""),
            project_number=d.get("project_number", ""),
            location=d.get("location", ""),
            inspection_date=d.get("inspection_date", ""),
            operator_name=d.get("operator_name", ""),
            equipment_type=d.get("equipment_type", ""),
            equipment_unit=d.get("equipment_unit", ""),
            fail_count=d.get("fail_count", 0) or 0,
            out_of_service=d.get("out_of_service", "No"),
            photo_count=len(d.get("photos", []) or []),
            created_at=d.get("created_at", ""),
        )
        for d in docs
    ]


@api_router.get("/equipment-inspections/{inspection_id}")
async def get_equipment_inspection(inspection_id: str, _: bool = Depends(require_admin)):
    doc = await db.equipment_inspections.find_one({"id": inspection_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Equipment inspection not found")
    return doc


@api_router.delete("/equipment-inspections/{inspection_id}")
async def delete_equipment_inspection(inspection_id: str, _: bool = Depends(require_admin)):
    result = await db.equipment_inspections.delete_one({"id": inspection_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Equipment inspection not found")
    return {"deleted": True, "id": inspection_id}



import csv
import io


# ============================================================
# Compliance CSV Exports (admin-only)
# ============================================================
EXPORTABLE_KINDS = {
    "inspections": "inspections",
    "meetings": "meetings",
    "jhas": "jhas",
    "incidents": "incidents",
    "daily-reports": "daily_reports",
    "equipment-inspections": "equipment_inspections",
}

# Per-kind row schema — what each CSV column should contain. We deliberately
# omit photos / signatures (binary blobs) and the raw checklist dict (renders
# poorly in Excel). Reviewers click into the Admin Hub for the full record.
EXPORT_FIELDS: Dict[str, List[str]] = {
    "inspections": [
        "inspection_date", "inspection_time", "project_name", "project_number",
        "location", "inspector_name", "foreman_name", "operation",
        "work_activity", "hazards_observed", "stop_work_issued",
        "ppe_in_use", "weather_summary", "created_at", "id",
    ],
    "meetings": [
        "meeting_date", "meeting_time", "project_name", "project_number",
        "location", "presenter_name", "topic_title", "topic_number",
        "attendee_count", "discussion_summary", "created_at", "id",
    ],
    "jhas": [
        "jha_date", "project_name", "project_number", "location",
        "supervisor_name", "task_description", "approver_name",
        "step_count", "created_at", "id",
    ],
    "incidents": [
        "incident_date", "incident_time", "project_name", "project_number",
        "location", "incident_type", "severity", "osha_recordable",
        "work_stopped", "person_name", "body_part", "injury_nature",
        "treatment_provided", "medical_facility",
        "reporter_name", "supervisor_name",
        "root_cause_categories", "witness_count",
        "description", "immediate_action", "follow_up_action",
        "created_at", "id",
    ],
    "daily-reports": [
        "report_date", "project_name", "project_number", "location",
        "prepared_by", "superintendent_name",
        "weather_summary", "high_temp_f", "low_temp_f",
        "crew_count", "subcontractor_count", "visitor_count",
        "equipment_count", "material_count", "activity_count",
        "accident_or_injury", "safety_notified", "safety_notified_who",
        "safety_notified_time", "incident_report_filled",
        "incident_report_time",
        "delays_or_issues", "tomorrows_plan",
        "created_at", "id",
    ],
    "equipment-inspections": [
        "inspection_date", "inspection_time", "project_name", "project_number",
        "location", "operator_name", "equipment_type", "equipment_unit",
        "equipment_make", "equipment_model", "equipment_serial",
        "hour_meter", "odometer",
        "pass_count", "fail_count", "na_count", "out_of_service",
        "deficiency_notes", "corrective_actions",
        "created_at", "id",
    ],
}


def _csv_value(v: Any) -> str:
    """Flatten a record value into a CSV-friendly string."""
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        # Skip image blobs, summarize the rest with semicolons
        items = [
            str(x)
            for x in v
            if not (isinstance(x, str) and x.startswith("data:image/"))
        ]
        return "; ".join(items)
    if isinstance(v, dict):
        # e.g. witnesses, root cause categories — flatten one level
        return "; ".join(f"{k}={_csv_value(val)}" for k, val in v.items())
    return str(v)


def _date_field_for(kind: str) -> str:
    return {
        "inspections": "inspection_date",
        "meetings": "meeting_date",
        "jhas": "jha_date",
        "incidents": "incident_date",
        "daily-reports": "report_date",
        "equipment-inspections": "inspection_date",
    }[kind]


def _normalize_export_doc(kind: str, d: Dict[str, Any]) -> None:
    """Mutate a record in place so derived counts are populated for CSV columns."""
    if kind == "meetings" and "attendee_count" not in d:
        d["attendee_count"] = len(d.get("attendees") or [])
    if kind == "jhas" and "step_count" not in d:
        d["step_count"] = len(d.get("steps") or [])
    if kind == "incidents" and "witness_count" not in d:
        d["witness_count"] = len(d.get("witnesses") or [])
    if kind == "incidents" and "root_cause_categories" not in d:
        cats = d.get("root_causes") or []
        d["root_cause_categories"] = (
            "; ".join(cats) if isinstance(cats, list) else str(cats)
        )
    if kind == "daily-reports":
        for k_, src in (
            ("crew_count", "crew"),
            ("subcontractor_count", "subcontractors"),
            ("visitor_count", "visitors"),
            ("equipment_count", "equipment"),
            ("material_count", "materials"),
            ("activity_count", "activities"),
        ):
            if k_ not in d:
                d[k_] = len(d.get(src) or [])


def _build_csv_bytes(kind: str, docs: List[Dict[str, Any]]) -> bytes:
    """Render a CSV (UTF-8 bytes) for one kind."""
    fields = list(EXPORT_FIELDS[kind])
    for d in docs:
        _normalize_export_doc(kind, d)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(fields)
    for d in docs:
        writer.writerow([_csv_value(d.get(f)) for f in fields])
    return buf.getvalue().encode("utf-8")


@api_router.get("/exports/csv")
async def export_csv(
    kind: str,
    start: Optional[str] = None,  # YYYY-MM-DD inclusive
    end: Optional[str] = None,    # YYYY-MM-DD inclusive
    _: bool = Depends(require_admin),
):
    """Stream a CSV export for one form kind, optionally filtered by date.

    Query params:
        kind  = inspections | meetings | jhas | incidents | daily-reports | equipment-inspections
        start = YYYY-MM-DD (inclusive)
        end   = YYYY-MM-DD (inclusive)

    Both date params are optional — omit for all-time.
    """
    if kind not in EXPORTABLE_KINDS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown kind '{kind}'. Allowed: {sorted(EXPORTABLE_KINDS.keys())}",
        )

    coll_name = EXPORTABLE_KINDS[kind]
    date_field = _date_field_for(kind)

    q: Dict[str, Any] = {}
    if start or end:
        cond: Dict[str, str] = {}
        if start:
            cond["$gte"] = start
        if end:
            cond["$lte"] = end
        q[date_field] = cond

    # Drop heavy blobs from the projection
    projection = {
        "_id": 0,
        "photos": 0,
        "signature": 0,
        "operator_signature": 0,
        "supervisor_signature": 0,
        "reporter_signature": 0,
        "preparer_signature": 0,
        "approver_signature": 0,
    }

    cursor = db[coll_name].find(q, projection).sort(date_field, -1)
    docs = await cursor.to_list(20000)

    csv_bytes = _build_csv_bytes(kind, docs)

    today = datetime.now(timezone.utc).date().isoformat()
    range_tag = ""
    if start and end:
        range_tag = f"_{start}_to_{end}"
    elif start:
        range_tag = f"_from_{start}"
    elif end:
        range_tag = f"_through_{end}"
    filename = f"MASCI_{kind}{range_tag}_{today}.csv"

    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Record-Count": str(len(docs)),
        },
    )


@api_router.get("/exports/summary")
async def export_summary(
    start: Optional[str] = None,
    end: Optional[str] = None,
    _: bool = Depends(require_admin),
):
    """Quick count-per-kind for a given date range — used by the Admin UI to
    show a foreman 'You have 47 records in this range' before they download."""
    out: Dict[str, int] = {}
    for kind, coll_name in EXPORTABLE_KINDS.items():
        date_field = _date_field_for(kind)
        q: Dict[str, Any] = {}
        if start or end:
            cond: Dict[str, str] = {}
            if start:
                cond["$gte"] = start
            if end:
                cond["$lte"] = end
            q[date_field] = cond
        out[kind] = await db[coll_name].count_documents(q)
    return {"start": start, "end": end, "counts": out, "total": sum(out.values())}


# ----------------------------------------------------------------------
# Full backup — single .zip with everything (CSVs + JSON + PDFs + photos)
# ----------------------------------------------------------------------
import asyncio as _backup_asyncio  # noqa: E402
import json as _backup_json  # noqa: E402
import zipfile  # noqa: E402


def _safe_filename(s: str, max_len: int = 60) -> str:
    """Make a filesystem-friendly fragment from a free-form string."""
    cleaned = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in (s or ""))
    cleaned = cleaned.strip("_") or "untitled"
    return cleaned[:max_len]


def _record_filename(kind: str, record: dict) -> str:
    """Stable, sortable filename: <date>_<id-prefix>_<project>.<ext>"""
    date_part = (
        record.get("inspection_date")
        or record.get("meeting_date")
        or record.get("jha_date")
        or record.get("incident_date")
        or record.get("report_date")
        or "0000-00-00"
    )
    rid = (record.get("id") or "")[:8]
    proj = _safe_filename(record.get("project_name") or "MASCI", 40)
    return f"{date_part}_{rid}_{proj}"


@api_router.get("/exports/full-backup")
async def exports_full_backup(_: bool = Depends(require_admin)):
    """One-click off-site backup. Streams a single .zip back containing:

    /CSV/                — one CSV per kind (no photos/signatures inline)
    /<kind>/json/        — every record as raw JSON (photos + signatures intact)
    /<kind>/pdf/         — every record rendered to PDF via WeasyPrint
    /crew_hub/           — Crew Hub collections as JSON
    /safety_aux/         — Equipment unit registry, JHA plan PDFs, trench-box refs
    /backup_manifest.json — schema + counts + generated_at
    /backup_log.txt      — human-readable summary

    Built in-memory with `zipfile`. Runs sequentially (single request) — for
    a typical contractor day (50–200 records) this finishes in 5–30 sec.
    """
    payload, total_records, filename = await _build_backup_zip(db)
    return Response(
        content=payload,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Record-Count": str(total_records),
            "X-Backup-Size-Bytes": str(len(payload)),
        },
    )


async def _build_backup_zip(db) -> tuple[bytes, int, str]:
    """Build the full-backup .zip in memory. Returns (payload, record_count, filename).

    Shared by the HTTP download endpoint and the nightly scheduler.
    """
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d_%H%M%SZ")

    buf = io.BytesIO()
    log_lines: List[str] = [
        "MASCI Hub — Full Backup",
        f"Generated: {now.isoformat()}",
        "Source: mascidocs.com (production)",
        "",
        "Per-kind record counts:",
    ]

    total_records = 0
    total_pdf_bytes = 0
    pdf_failures: List[str] = []

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for kind, coll_name in EXPORTABLE_KINDS.items():
            cursor = db[coll_name].find({}, {"_id": 0}).sort("created_at", -1)
            docs = await cursor.to_list(50000)
            total_records += len(docs)
            log_lines.append(f"  {kind:25s} : {len(docs):5d}")

            # /CSV/
            try:
                csv_bytes = _build_csv_bytes(kind, [dict(d) for d in docs])
                zf.writestr(f"CSV/MASCI_{kind}_{stamp}.csv", csv_bytes)
            except Exception as e:  # noqa: BLE001
                log_lines.append(f"    [warn] CSV build failed: {e}")

            # /<kind>/json/  + /<kind>/pdf/
            for d in docs:
                base = _record_filename(kind, d)
                try:
                    zf.writestr(
                        f"{kind}/json/{base}.json",
                        _backup_json.dumps(d, indent=2, default=str).encode("utf-8"),
                    )
                except Exception as e:  # noqa: BLE001
                    log_lines.append(f"    [warn] {kind}/{d.get('id')} JSON failed: {e}")

                # PDFs are heavy — only render the kinds we know how to render.
                # Map the storage kind back to the pdf_render kind.
                pdf_kind = {
                    "inspections": "inspection",
                    "meetings": "meeting",
                    "jhas": "jha",
                    "incidents": "incident",
                    "daily-reports": "daily-report",
                    "equipment-inspections": "equipment-inspection",
                }.get(kind)
                if pdf_kind:
                    try:
                        pdf_bytes = await _backup_asyncio.to_thread(
                            render_record_pdf, pdf_kind, d
                        )
                        total_pdf_bytes += len(pdf_bytes)
                        zf.writestr(f"{kind}/pdf/{base}.pdf", pdf_bytes)
                    except Exception as e:  # noqa: BLE001
                        pdf_failures.append(f"{kind}/{d.get('id')}: {e}")

        # Manifest
        log_lines.append("")
        log_lines.append("Totals:")
        log_lines.append(f"  Records:        {total_records}")
        log_lines.append(f"  PDFs rendered:  {total_pdf_bytes / (1024 * 1024):.1f} MB")
        log_lines.append(f"  PDF failures:   {len(pdf_failures)}")
        if pdf_failures:
            log_lines.append("")
            log_lines.append("PDF render failures (first 20):")
            for line in pdf_failures[:20]:
                log_lines.append(f"  - {line}")

        # ---------- Crew Hub collections (Phase 1–4 Basecamp clone) ----------
        # Internal collaboration data — archived as JSON only (no PDFs).
        # Photos/file blobs live inside docs.data_base64.
        CREW_HUB_COLLECTIONS = [
            ("projects", None),
            ("users", {"password_hash": 0}),         # redact password hashes
            ("project_members", None),
            ("messages", None),
            ("message_comments", None),
            ("todo_lists", None),
            ("todos", None),
            ("events", None),
            ("docs", None),                           # includes base64 file blobs
            ("hill_scopes", None),
            ("activity_log", None),
            ("notifications", None),
        ]
        log_lines.append("")
        log_lines.append("Crew Hub collections (JSON only):")
        crew_total = 0
        for coll_name, projection in CREW_HUB_COLLECTIONS:
            try:
                proj = {"_id": 0}
                if projection:
                    proj.update(projection)
                docs = await db[coll_name].find({}, proj).to_list(50000)
                crew_total += len(docs)
                log_lines.append(f"  crew_hub/{coll_name:22s} : {len(docs):5d}")
                zf.writestr(
                    f"crew_hub/{coll_name}.json",
                    _backup_json.dumps(docs, indent=2, default=str).encode("utf-8"),
                )
            except Exception as e:  # noqa: BLE001
                log_lines.append(f"    [warn] crew_hub/{coll_name} failed: {e}")
        total_records += crew_total
        log_lines.append(f"  Crew Hub subtotal: {crew_total}")

        # ---------- Safety auxiliary collections ----------
        # Equipment unit registry, JHA plan PDFs, trench-box tabulated data.
        SAFETY_AUX_COLLECTIONS = [
            "equipment_units",
            "job_hazard_plans",
            "trench_boxes",
        ]
        log_lines.append("")
        log_lines.append("Safety aux collections (JSON only):")
        aux_total = 0
        for coll_name in SAFETY_AUX_COLLECTIONS:
            try:
                docs = await db[coll_name].find({}, {"_id": 0}).to_list(50000)
                aux_total += len(docs)
                log_lines.append(f"  safety_aux/{coll_name:22s} : {len(docs):5d}")
                zf.writestr(
                    f"safety_aux/{coll_name}.json",
                    _backup_json.dumps(docs, indent=2, default=str).encode("utf-8"),
                )
            except Exception as e:  # noqa: BLE001
                log_lines.append(f"    [warn] safety_aux/{coll_name} failed: {e}")
        total_records += aux_total
        log_lines.append(f"  Safety aux subtotal: {aux_total}")

        # Manifest identifier — the restore endpoint checks this
        zf.writestr(
            "backup_manifest.json",
            _backup_json.dumps({
                "source": "mascidocs.com",
                "generated_at": now.isoformat(),
                "version": "2",
                "total_records": total_records,
                "safety_kinds": list(EXPORTABLE_KINDS.keys()),
                "crew_hub_collections": [c for c, _ in CREW_HUB_COLLECTIONS],
                "safety_aux_collections": SAFETY_AUX_COLLECTIONS,
            }, indent=2).encode("utf-8"),
        )

        zf.writestr("backup_log.txt", "\n".join(log_lines).encode("utf-8"))

    payload = buf.getvalue()
    filename = f"MASCI_full_backup_{stamp}.zip"
    return payload, total_records, filename


# ----------------------------------------------------------------------
# Stored backups — daily scheduled backup saved to disk.
# ----------------------------------------------------------------------
BACKUPS_DIR = Path(os.environ.get("BACKUPS_DIR", "/app/backend/backups")).resolve()
BACKUP_RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS", "14"))
BACKUP_HOUR_UTC = int(os.environ.get("BACKUP_HOUR_UTC", "2"))   # default 02:00 UTC


def _list_stored_backups() -> List[dict]:
    """Return metadata for every .zip in the backups dir (newest first)."""
    if not BACKUPS_DIR.exists():
        return []
    rows = []
    for p in sorted(BACKUPS_DIR.glob("MASCI_full_backup_*.zip"), reverse=True):
        try:
            st = p.stat()
            rows.append({
                "filename": p.name,
                "size_bytes": st.st_size,
                "created_at": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
            })
        except Exception:
            continue
    return rows


async def _run_scheduled_backup(db) -> Optional[dict]:
    """Build a backup and persist to BACKUPS_DIR. Prune files older than the
    retention window. Returns a small summary dict or None on failure."""
    try:
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        payload, total_records, filename = await _build_backup_zip(db)
        out = BACKUPS_DIR / filename
        # Write atomically via a temp file + rename
        tmp = out.with_suffix(".zip.tmp")
        tmp.write_bytes(payload)
        tmp.replace(out)
        logger.info(
            f"[scheduled-backup] wrote {out.name} ({len(payload)/1024/1024:.1f} MB · {total_records} records)"
        )

        # Prune
        cutoff = datetime.now(timezone.utc).timestamp() - BACKUP_RETENTION_DAYS * 86400
        pruned = 0
        for p in BACKUPS_DIR.glob("MASCI_full_backup_*.zip"):
            try:
                if p.stat().st_mtime < cutoff:
                    p.unlink()
                    pruned += 1
            except Exception:
                continue
        if pruned:
            logger.info(f"[scheduled-backup] pruned {pruned} expired backups (> {BACKUP_RETENTION_DAYS} days old)")

        # Email the backup off-site — CRITICAL for redeploy safety
        emailed_to = None
        try:
            emailed_to = await _email_backup_zip(filename, payload, total_records)
        except Exception as e:
            logger.warning(f"[scheduled-backup] email step failed (non-fatal): {e}")

        return {
            "filename": out.name,
            "size_bytes": len(payload),
            "records": total_records,
            "pruned_old": pruned,
            "emailed_to": emailed_to,
        }
    except Exception as e:
        logger.exception(f"[scheduled-backup] FAILED: {e}")
        return None


async def _email_backup_zip(filename: str, payload: bytes, total_records: int) -> Optional[str]:
    """Email the backup .zip as an attachment via Resend. No-op if
    disabled or credentials missing. Returns the recipient email on success."""
    to = (os.environ.get("BACKUP_EMAIL_TO") or "").strip()
    if not to:
        return None
    api_key = (os.environ.get("RESEND_API_KEY") or "").strip()
    if not api_key:
        logger.info("[scheduled-backup] email skipped — RESEND_API_KEY missing")
        return None

    # Resend attachment limit is ~40 MB. Skip email if the zip is too big
    # but don't fail the whole backup.
    max_mb = int(os.environ.get("BACKUP_EMAIL_MAX_MB", "35"))
    size_mb = len(payload) / (1024 * 1024)
    if size_mb > max_mb:
        logger.warning(
            f"[scheduled-backup] email skipped — backup is {size_mb:.1f} MB, "
            f"over the {max_mb} MB email limit. Admin must download manually."
        )
        return None

    import base64 as _bb64
    b64 = _bb64.b64encode(payload).decode("ascii")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sender = os.environ.get("SENDER_EMAIL", "noreply@mascidocs.com")
    reply_to = os.environ.get("REPLY_TO_EMAIL") or None

    html = (
        f'<div style="font-family:system-ui,-apple-system,sans-serif;max-width:560px;margin:0 auto;">'
        f'<div style="border-bottom:4px solid #b91c1c;padding-bottom:10px;margin-bottom:18px;">'
        f'<strong style="color:#b91c1c;letter-spacing:.15em;font-size:11px;text-transform:uppercase">'
        f'MASCI · NIGHTLY BACKUP</strong>'
        f'</div>'
        f'<p style="color:#0f172a;margin:0 0 8px;font-size:15px;">'
        f'Your nightly MASCI Hub backup is attached.</p>'
        f'<ul style="color:#334155;font-size:14px;line-height:1.7;padding-left:18px;">'
        f'<li><strong>Generated:</strong> {stamp}</li>'
        f'<li><strong>Records:</strong> {total_records}</li>'
        f'<li><strong>Size:</strong> {size_mb:.1f} MB</li>'
        f'<li><strong>File:</strong> <code>{filename}</code></li>'
        f'</ul>'
        f'<p style="color:#475569;font-size:13px;margin-top:18px;">'
        f'<strong>Restore instructions:</strong> sign in to <a href="https://mascidocs.com/admin">'
        f'mascidocs.com/admin</a> → scroll to "Restore from Backup" → Upload this .zip.</p>'
        f'<p style="color:#b91c1c;font-size:12px;margin-top:18px;font-weight:700;">'
        f'Keep this email safe — it is your off-site disaster-recovery copy.</p>'
        f'</div>'
    )

    try:
        import resend  # noqa: E402
        resend.api_key = api_key
        params: Dict[str, Any] = {
            "from": sender,
            "to": [to],
            "subject": f"MASCI Nightly Backup · {stamp} · {total_records} records",
            "html": html,
            "attachments": [
                {"filename": filename, "content": b64},
            ],
        }
        if reply_to:
            params["reply_to"] = reply_to
        result = await asyncio.to_thread(resend.Emails.send, params)
        rid = (result or {}).get("id", "?")
        logger.info(f"[scheduled-backup] emailed backup to {to} (resend_id={rid})")
        return to
    except Exception as e:
        logger.warning(f"[scheduled-backup] Resend send failed: {e}")
        return None


_backup_task: Optional[asyncio.Task] = None


async def _backup_scheduler_loop(db) -> None:
    """Background loop — wakes up every ~60 s, fires the backup once the
    current UTC hour equals BACKUP_HOUR_UTC and we haven't already run today.
    Survives missed ticks (e.g., if the container was asleep at 02:00).
    """
    last_run_date = None
    # Give the app a moment to finish startup before first tick
    await asyncio.sleep(30)
    while True:
        try:
            now = datetime.now(timezone.utc)
            today = now.date()
            if now.hour >= BACKUP_HOUR_UTC and last_run_date != today:
                logger.info(f"[scheduled-backup] firing for {today}")
                result = await _run_scheduled_backup(db)
                if result:
                    last_run_date = today
                # If it failed, leave last_run_date alone so we retry next tick.
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception(f"[scheduled-backup] loop tick error: {e}")
        await asyncio.sleep(300)  # 5 min ticks — low overhead, catches missed slots


@api_router.get("/admin/backups")
async def admin_list_backups(_: bool = Depends(require_admin)):
    """List every stored backup on disk + current schedule settings."""
    files = _list_stored_backups()
    total_bytes = sum(f["size_bytes"] for f in files)
    return {
        "backups": files,
        "count": len(files),
        "total_bytes": total_bytes,
        "schedule": {
            "hour_utc": BACKUP_HOUR_UTC,
            "retention_days": BACKUP_RETENTION_DAYS,
            "storage_dir": str(BACKUPS_DIR),
            "enabled": True,
        },
    }


@api_router.get("/admin/backups/{filename}")
async def admin_download_stored_backup(
    filename: str, _: bool = Depends(require_admin)
):
    """Download a specific stored backup by filename."""
    # Strict filename validation — only our own backup files.
    if not re.fullmatch(r"MASCI_full_backup_[0-9A-Za-z_\-]+\.zip", filename):
        raise HTTPException(400, "Invalid backup filename")
    path = BACKUPS_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Backup not found")
    try:
        data = path.read_bytes()
    except Exception as e:
        raise HTTPException(500, f"Could not read backup: {e}")
    return Response(
        content=data,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Backup-Size-Bytes": str(len(data)),
        },
    )


@api_router.delete("/admin/backups/{filename}")
async def admin_delete_stored_backup(
    filename: str, _: bool = Depends(require_admin)
):
    if not re.fullmatch(r"MASCI_full_backup_[0-9A-Za-z_\-]+\.zip", filename):
        raise HTTPException(400, "Invalid backup filename")
    path = BACKUPS_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Backup not found")
    try:
        path.unlink()
    except Exception as e:
        raise HTTPException(500, f"Could not delete: {e}")
    return {"ok": True, "filename": filename}


@api_router.post("/admin/backups/run-now")
async def admin_run_backup_now(_: bool = Depends(require_admin)):
    """Trigger an immediate scheduled backup (same path as nightly, just now)."""
    result = await _run_scheduled_backup(db)
    if not result:
        raise HTTPException(500, "Backup failed — see server logs")
    return {"ok": True, **result}


@api_router.get("/admin/persistence-check")
async def admin_persistence_check(_: bool = Depends(require_admin)):
    """Report whether the running instance is at risk of data loss on redeploy.

    Production on Emergent without an external MongoDB URL is ephemeral — a
    git push/redeploy wipes the container's Mongo volume. This endpoint
    powers the admin-hub warning banner so the office never redeploys blind.
    """
    mongo_url = os.environ.get("MONGO_URL", "")
    # Local/in-container Mongo hostnames. Atlas URLs start with mongodb+srv://
    # or include an explicit external host. Anything pointing at localhost,
    # 127.0.0.1 or no hostname is treated as ephemeral.
    host_part = mongo_url.split("://", 1)[-1].split("/", 1)[0].lower()
    is_local = (
        not mongo_url
        or "localhost" in host_part
        or host_part.startswith("127.")
        or host_part.startswith("0.0.0.0")
        or host_part == ""
    )
    is_atlas = mongo_url.startswith("mongodb+srv://") or "mongodb.net" in host_part
    backup_email_configured = bool((os.environ.get("BACKUP_EMAIL_TO") or "").strip())
    resend_configured = bool((os.environ.get("RESEND_API_KEY") or "").strip())
    last_backup = None
    try:
        files = _list_stored_backups()
        if files:
            last_backup = files[0]
    except Exception:
        pass

    return {
        "mongo_is_local": is_local,
        "mongo_is_atlas": is_atlas,
        "mongo_host": host_part or "(none)",
        "backup_email_to": (os.environ.get("BACKUP_EMAIL_TO") or "").strip() or None,
        "backup_email_configured": backup_email_configured,
        "resend_configured": resend_configured,
        "last_backup": last_backup,
        "scheduler_enabled": os.environ.get("DISABLE_BACKUP_SCHEDULER", "").lower() not in ("1", "true", "yes"),
    }


# ----------------------------------------------------------------------
# Restore from backup ZIP — upsert every record back into MongoDB.
# ----------------------------------------------------------------------
# Map backup kind folder → MongoDB collection name. Pulled from
# EXPORTABLE_KINDS + the Crew Hub + Safety aux lists above.
_RESTORE_KIND_TO_COLL = {
    # Safety kinds — the ZIP stores them under <kind>/json/*.json
    "inspections": "inspections",
    "meetings": "meetings",
    "jhas": "jhas",
    "incidents": "incidents",
    "daily-reports": "daily_reports",
    "equipment-inspections": "equipment_inspections",
}
_RESTORE_CREW_HUB = {
    "projects", "users", "project_members", "messages", "message_comments",
    "todo_lists", "todos", "events", "docs", "hill_scopes", "activity_log",
    "notifications",
}
_RESTORE_SAFETY_AUX = {"equipment_units", "job_hazard_plans", "trench_boxes"}


@api_router.post("/exports/restore")
async def exports_restore(
    file: UploadFile = File(...),
    merge: bool = Form(True),
    _: bool = Depends(require_admin),
):
    """Restore a `/api/exports/full-backup` .zip back into MongoDB.

    - `merge=true` (default): upsert by `id` — existing rows with the same
      id are overwritten, new rows added, untouched collections untouched.
    - `merge=false`: wipe the target collection first, then insert. Use with
      care — this is a full restore to the backup's exact state.

    The zip's `backup_manifest.json` is used to validate that this is a real
    MASCI backup before we touch any data.
    """
    # 1. Read + validate the upload
    try:
        payload = await file.read()
    except Exception as e:
        raise HTTPException(400, f"Failed to read upload: {e}")
    if not payload:
        raise HTTPException(400, "Empty upload")
    if len(payload) > 500 * 1024 * 1024:  # 500 MB hard ceiling
        raise HTTPException(413, "Backup file exceeds 500 MB limit")

    try:
        zf = zipfile.ZipFile(io.BytesIO(payload), "r")
    except zipfile.BadZipFile:
        raise HTTPException(400, "Uploaded file is not a valid ZIP archive")

    names = set(zf.namelist())
    if "backup_manifest.json" not in names:
        raise HTTPException(
            400,
            "backup_manifest.json missing — this does not look like a MASCI "
            "full-backup .zip. Regenerate via 'Download Full Backup' first.",
        )
    try:
        manifest = _backup_json.loads(zf.read("backup_manifest.json").decode("utf-8"))
    except Exception as e:
        raise HTTPException(400, f"Corrupt manifest: {e}")

    # 2. Walk the ZIP and group docs by destination collection.
    bucket: Dict[str, List[dict]] = {}

    def _add(coll: str, docs: List[dict]):
        if not docs:
            return
        bucket.setdefault(coll, []).extend(docs)

    # 2a. Safety kinds — every json under <kind>/json/*.json
    for kind, coll in _RESTORE_KIND_TO_COLL.items():
        prefix = f"{kind}/json/"
        docs: List[dict] = []
        for n in names:
            if n.startswith(prefix) and n.endswith(".json"):
                try:
                    docs.append(_backup_json.loads(zf.read(n).decode("utf-8")))
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"restore: skipped {n}: {e}")
        _add(coll, docs)

    # 2b. Crew Hub — single json per collection under crew_hub/<coll>.json
    for coll in _RESTORE_CREW_HUB:
        n = f"crew_hub/{coll}.json"
        if n in names:
            try:
                data = _backup_json.loads(zf.read(n).decode("utf-8"))
                if isinstance(data, list):
                    _add(coll, data)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"restore: skipped {n}: {e}")

    # 2c. Safety aux
    for coll in _RESTORE_SAFETY_AUX:
        n = f"safety_aux/{coll}.json"
        if n in names:
            try:
                data = _backup_json.loads(zf.read(n).decode("utf-8"))
                if isinstance(data, list):
                    _add(coll, data)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"restore: skipped {n}: {e}")

    if not bucket:
        raise HTTPException(
            400,
            "No records found in backup (expected files under "
            "<kind>/json/, crew_hub/ or safety_aux/).",
        )

    # 3. Write back to MongoDB.
    summary: Dict[str, dict] = {}
    # If the users collection is being restored, the export redacts
    # password_hash. Precompute the seed hash so restored rows always have
    # a usable password (Welcome2MASCI! + must_change_password).
    _seed_hash = None
    if "users" in bucket:
        try:
            import bcrypt as _bc  # noqa: E402
            _seed_hash = _bc.hashpw(b"Welcome2MASCI!", _bc.gensalt()).decode("utf-8")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"restore: could not generate seed hash ({e}); restored users may be locked out")

    for coll, docs in bucket.items():
        # Strip any _id from the docs (they're exported without, but be safe).
        clean = []
        for d in docs:
            if not isinstance(d, dict):
                continue
            d.pop("_id", None)
            if "id" not in d:
                d["id"] = str(uuid.uuid4())  # defensive — keep upsert viable
            # Special-case: restored users lost their password_hash on export.
            # In merge mode: keep whatever's in DB (pull it first).
            # In replace mode (or brand-new row): stamp the seed hash +
            # force password change so no account gets locked out.
            if coll == "users" and "password_hash" not in d:
                existing = None
                if merge:
                    existing = await db.users.find_one(
                        {"id": d["id"]}, {"_id": 0, "password_hash": 1}
                    )
                if existing and existing.get("password_hash"):
                    d["password_hash"] = existing["password_hash"]
                elif _seed_hash:
                    d["password_hash"] = _seed_hash
                    d["must_change_password"] = True
            clean.append(d)

        deleted = 0
        if not merge:
            res = await db[coll].delete_many({})
            deleted = res.deleted_count

        upserted = 0
        modified = 0
        inserted = 0
        for d in clean:
            try:
                r = await db[coll].update_one(
                    {"id": d["id"]}, {"$set": d}, upsert=True,
                )
                if r.upserted_id is not None:
                    inserted += 1
                elif r.modified_count:
                    modified += 1
                upserted += 1
            except Exception as e:  # noqa: BLE001
                logger.warning(f"restore: {coll}/{d.get('id')} failed: {e}")

        summary[coll] = {
            "deleted": deleted,
            "processed": len(clean),
            "inserted": inserted,
            "updated": modified,
        }

    logger.info(f"restore: processed {sum(s['processed'] for s in summary.values())} records across {len(summary)} collections")

    return {
        "ok": True,
        "mode": "replace" if not merge else "merge",
        "backup_generated_at": manifest.get("generated_at"),
        "backup_version": manifest.get("version", "unknown"),
        "collections": summary,
        "total_processed": sum(s["processed"] for s in summary.values()),
    }




@api_router.get("/equipment-status-board")
async def equipment_status_board(_: bool = Depends(require_admin)):
    """
    Per-unit aggregation for the Admin Hub status board.

    For every saved equipment unit (or every unit referenced by an inspection,
    even if the operator typed it free-form without saving), returns:
        - last_inspection_date / last_inspected_days_ago
        - last_status: "ok" | "fail" | "never"
        - fail_count_14d : how many FAIL items logged in the last 14 days
        - top_failures : up to 3 most-frequent failing item names (last 30 d)
        - inspection_count : total all-time count
    """
    now = datetime.now(timezone.utc)
    cutoff_14 = now - timedelta(days=14)
    cutoff_30 = now - timedelta(days=30)

    saved_cursor = db.equipment_units.find({}, {"_id": 0})
    saved_units = await saved_cursor.to_list(2000)

    # Pull every inspection (slim projection — skip photos to keep it fast)
    insp_cursor = db.equipment_inspections.find(
        {},
        {
            "_id": 0,
            "id": 1,
            "equipment_type": 1,
            "equipment_unit": 1,
            "inspection_date": 1,
            "created_at": 1,
            "fail_count": 1,
            "out_of_service": 1,
            "checklist": 1,
            "project_name": 1,
            "project_number": 1,
        },
    ).sort("created_at", -1)
    inspections = await insp_cursor.to_list(5000)

    def _key(t: str, u: str) -> str:
        return f"{(t or '').strip()}||{(u or '').strip()}"

    by_unit: Dict[str, Dict[str, Any]] = {}
    for u in saved_units:
        k = _key(u.get("equipment_type", ""), u.get("unit_label", ""))
        by_unit[k] = {
            "equipment_type": u.get("equipment_type", ""),
            "equipment_unit": u.get("unit_label", ""),
            "make": u.get("make", "") or "",
            "model": u.get("model", "") or "",
            "serial": u.get("serial", "") or "",
            "saved": True,
            "inspection_count": 0,
            "fail_count_14d": 0,
            "last_inspection_date": None,
            "last_inspected_at": None,
            "last_status": "never",
            "last_project": "",
            "last_project_number": "",
            "_fail_items_30d": {},  # tally
        }

    def _parse_dt(s: str) -> Optional[datetime]:
        if not s:
            return None
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None

    for d in inspections:
        k = _key(d.get("equipment_type"), d.get("equipment_unit"))
        if k not in by_unit:
            by_unit[k] = {
                "equipment_type": d.get("equipment_type", ""),
                "equipment_unit": d.get("equipment_unit", ""),
                "make": "",
                "model": "",
                "serial": "",
                "saved": False,
                "inspection_count": 0,
                "fail_count_14d": 0,
                "last_inspection_date": None,
                "last_inspected_at": None,
                "last_status": "never",
                "last_project": "",
                "last_project_number": "",
                "_fail_items_30d": {},
            }

        bucket = by_unit[k]
        bucket["inspection_count"] += 1

        created = _parse_dt(d.get("created_at"))
        if bucket["last_inspected_at"] is None or (
            created and created > bucket["last_inspected_at"]
        ):
            bucket["last_inspected_at"] = created
            bucket["last_inspection_date"] = d.get("inspection_date") or (
                created.date().isoformat() if created else None
            )
            bucket["last_status"] = (
                "fail" if (d.get("fail_count") or 0) > 0 else "ok"
            )
            bucket["last_project"] = d.get("project_name", "") or ""
            bucket["last_project_number"] = d.get("project_number", "") or ""

        # 14-day fail count
        if created and created >= cutoff_14:
            bucket["fail_count_14d"] += int(d.get("fail_count") or 0)

        # 30-day per-item failure tally
        if created and created >= cutoff_30:
            for sec, items in (d.get("checklist") or {}).items():
                if not isinstance(items, dict):
                    continue
                for item_name, res in items.items():
                    if isinstance(res, dict) and res.get("status") == "fail":
                        bucket["_fail_items_30d"][item_name] = (
                            bucket["_fail_items_30d"].get(item_name, 0) + 1
                        )

    out = []
    for k, b in by_unit.items():
        last_at = b.pop("last_inspected_at", None)
        days_ago = None
        if last_at:
            days_ago = max(0, (now - last_at).days)
        top = sorted(
            b.pop("_fail_items_30d", {}).items(), key=lambda kv: kv[1], reverse=True
        )[:3]
        b["last_inspected_days_ago"] = days_ago
        b["top_failures"] = [
            {"item": item, "count": cnt} for item, cnt in top
        ]
        out.append(b)

    # Sort: out-of-service first, then by fail count desc, then by stale-ness
    def _priority(b):
        oos = 0 if b["last_status"] == "fail" else 1
        stale = b["last_inspected_days_ago"] if b["last_inspected_days_ago"] is not None else 9999
        return (oos, -b["fail_count_14d"], -stale, b["equipment_type"], b["equipment_unit"])

    out.sort(key=_priority)
    return {
        "generated_at": now.isoformat(),
        "units": out,
        "summary": {
            "total_units": len(out),
            "out_of_service": sum(1 for b in out if b["last_status"] == "fail"),
            "never_inspected": sum(1 for b in out if b["last_status"] == "never"),
            "stale_7d": sum(
                1
                for b in out
                if (b["last_inspected_days_ago"] is None or b["last_inspected_days_ago"] >= 7)
            ),
        },
    }




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


@api_router.post("/translate", response_model=TranslateResponse, dependencies=[Depends(rate_limit_public_post)])
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
    COMPLIANCE_KINDS,
    PM_ONLY_KINDS,
    auto_email_enabled,
    recipients_for_record,
)


_KIND_TO_COLLECTION = {
    "inspection": "inspections",
    "meeting": "meetings",
    "jha": "jhas",
    "incident": "incidents",
    "daily-report": "daily_reports",
    "equipment-inspection": "equipment_inspections",
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

        dist = recipients_for_record(record, kind)
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
        reply_to = os.environ.get("REPLY_TO_EMAIL", "").strip()

        pdf_bytes = await asyncio.to_thread(render_record_pdf, kind, record)

        title = KIND_TITLES.get(kind, "MASCI Hub Record")
        project = record.get("project_name") or "MASCI"
        pm_name = dist.get("pm_name")
        pm_tag = f" · PM: {pm_name}" if pm_name else ""

        # Flag equipment failures in the subject so PMs see them at a glance
        equipment_fail = (
            kind == "equipment-inspection"
            and (record.get("fail_count") or 0) > 0
        )
        fail_prefix = "EQUIPMENT FAIL · " if equipment_fail else ""
        subject = f"[MASCI] {fail_prefix}{title} · {project}{pm_tag}"

        note = ""
        if kind == "incident" and _is_severe_incident(record):
            note = (
                "<p style='color:#C8102E;font-weight:700'>"
                "SEVERE INCIDENT — please review immediately."
                "</p>"
            )
        elif equipment_fail:
            note = (
                "<p style='color:#C8102E;font-weight:700'>"
                f"⚠ EQUIPMENT FAIL — {record.get('fail_count')} item(s) failed inspection. "
                f"{record.get('equipment_type', '')} {record.get('equipment_unit', '')} "
                "tagged OUT OF SERVICE."
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
            "from": f"MASCI Docs <{sender_email}>",
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
        if reply_to:
            params["reply_to"] = reply_to

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
    kind: str = "",
    _: bool = Depends(require_admin),
):
    """Admin-only introspection: shows who *would* receive the auto-email
    for a given project_number / project_name + form kind."""
    fake = {
        "project_number": project_number,
        "project_name": project_name,
        "severity": severity,
        "osha_recordable": osha_recordable,
    }
    dist = recipients_for_record(fake, kind or None)
    return {
        "input": fake,
        "kind": kind or None,
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
        "compliance_kinds": sorted(COMPLIANCE_KINDS),
        "pm_only_kinds": sorted(PM_ONLY_KINDS),
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
        title = KIND_TITLES.get(body.kind, "MASCI Hub Record")
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
            "from": f"MASCI Docs <{sender_email}>",
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

# ------------------------- Phase 1: per-user auth + projects (Basecamp-style /app) -------------------------
from auth import build_auth_router, seed_initial_users  # noqa: E402
from projects import build_projects_router, seed_initial_projects  # noqa: E402
from tools import build_tools_router, create_tools_indexes  # noqa: E402
from phase4 import build_phase4_router, create_phase4_indexes  # noqa: E402

_auth_router, get_current_user, require_admin_or_owner, _optional_user = build_auth_router(db)
_projects_router = build_projects_router(db, get_current_user, require_admin_or_owner)
_tools_router = build_tools_router(db, get_current_user, require_admin_or_owner)
app.include_router(_auth_router)
app.include_router(_projects_router)
app.include_router(_tools_router)

# Register phase 4 (activity + notifications + search + directory)
_phase4_router = build_phase4_router(db, get_current_user)
app.include_router(_phase4_router)


@app.on_event("startup")
async def _seed_phase1():
    try:
        await seed_initial_users(db)
        await seed_initial_projects(db)
        await create_tools_indexes(db)
        await create_phase4_indexes(db)
        await _seed_equipment_master()
    except Exception as e:
        logging.getLogger(__name__).exception(f"Phase 1 seed failed: {e}")


@app.on_event("startup")
async def _start_backup_scheduler():
    """Kick off the nightly full-backup scheduler as an asyncio task."""
    global _backup_task
    if os.environ.get("DISABLE_BACKUP_SCHEDULER", "").lower() in ("1", "true", "yes"):
        logging.getLogger(__name__).info("[scheduled-backup] DISABLED via env")
        return
    try:
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        _backup_task = asyncio.create_task(_backup_scheduler_loop(db))
        logging.getLogger(__name__).info(
            f"[scheduled-backup] scheduler started — {BACKUP_HOUR_UTC:02d}:00 UTC daily · "
            f"keep {BACKUP_RETENTION_DAYS} days · dir={BACKUPS_DIR}"
        )
    except Exception as e:
        logging.getLogger(__name__).exception(f"[scheduled-backup] startup failed: {e}")

cors_origins_env = os.environ.get('CORS_ORIGINS', '*').strip()
cors_origin_regex = (os.environ.get('CORS_ORIGIN_REGEX', '') or '').strip() or None

if cors_origins_env == '*' or not cors_origins_env:
    # Fully-permissive — incompatible with credentials per CORS spec, so
    # we drop credentials in this mode. Used only when no allow-list is set.
    _cors_origins: List[str] = ["*"]
    _cors_credentials = False
else:
    _cors_origins = [o.strip() for o in cors_origins_env.split(',') if o.strip()]
    _cors_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_credentials=_cors_credentials,
    allow_origins=_cors_origins,
    allow_origin_regex=cors_origin_regex,
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
    try:
        if _backup_task is not None:
            _backup_task.cancel()
    except Exception:
        pass
    client.close()

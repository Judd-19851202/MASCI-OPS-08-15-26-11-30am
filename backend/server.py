from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
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
    return inspection


@api_router.get("/inspections", response_model=List[InspectionSummary])
async def list_inspections():
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
async def get_inspection(inspection_id: str):
    doc = await db.inspections.find_one({"id": inspection_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return doc


@api_router.delete("/inspections/{inspection_id}")
async def delete_inspection(inspection_id: str):
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
    return meeting


@api_router.get("/meetings", response_model=List[MeetingSummary])
async def list_meetings():
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
async def get_meeting(meeting_id: str):
    doc = await db.meetings.find_one({"id": meeting_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return doc


@api_router.delete("/meetings/{meeting_id}")
async def delete_meeting(meeting_id: str):
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
    return jha


@api_router.get("/jhas", response_model=List[JhaSummary])
async def list_jhas():
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
async def get_jha(jha_id: str):
    doc = await db.jhas.find_one({"id": jha_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="JHA not found")
    return doc


@api_router.delete("/jhas/{jha_id}")
async def delete_jha(jha_id: str):
    result = await db.jhas.delete_one({"id": jha_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="JHA not found")
    return {"deleted": True, "id": jha_id}


app.include_router(api_router)

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

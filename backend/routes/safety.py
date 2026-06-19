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

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from pm_auth import compute_pm_scope


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
    doc_id: Optional[str] = ""  # INSP-YYYY-NNNNN, stamped on insert
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
class MeetingAttendee(BaseModel):
    """SAFETY-MEETING-CERT · attendee row contract.

    A meeting attendee MUST carry a name, a company, a signature, and
    must be acknowledged. Two paths are supported:

      * MASCI employee — `employee_id` references the employees
        collection; `company` is auto-locked to "MASCI" client-side.
        `non_masci` MUST be false.
      * Non-MASCI / subcontractor — `non_masci=True`; user types name
        and company directly. No HR employee record is created.

    `acknowledged` is REQUIRED to be True at submit-time. Accept
    `acknowledged_at` (ISO timestamp) as supplementary proof. Signature
    image-data is required.
    """
    model_config = ConfigDict(extra="allow")
    name: str
    employee_id: Optional[str] = ""
    non_masci: Optional[bool] = False
    company: str
    trade: Optional[str] = ""
    signature: str  # data:image/* — required
    acknowledged: bool = False
    acknowledged_at: Optional[str] = ""

    @field_validator("name")
    @classmethod
    def _name_required(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("attendee name is required")
        return v

    @field_validator("company")
    @classmethod
    def _company_required(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("attendee company is required")
        return v

    @field_validator("signature")
    @classmethod
    def _signature_required(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("attendee signature is required")
        return v

    @field_validator("acknowledged")
    @classmethod
    def _ack_required(cls, v: bool) -> bool:
        if not v:
            raise ValueError("attendee must acknowledge the meeting")
        return v


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
    attendees: List[MeetingAttendee] = Field(default_factory=list)
    photos: List[str] = Field(default_factory=list)
    conductor_signature: Optional[str] = ""
    # iter256 · GPS + topic provenance + submit language (promoted from extra="allow")
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    gps_accuracy: Optional[float] = None
    topic_template_key: Optional[str] = ""
    submit_language: Optional[str] = ""
    # iter260 · E1 · operational context captures
    crew_size: Optional[int] = None
    shift: Optional[str] = ""              # "" | "Day" | "Swing" | "Night"
    weather: List[str] = Field(default_factory=list)
    subcontractor_present: Optional[bool] = False
    subcontractor_name: Optional[str] = ""
    high_risk_activity: Optional[bool] = False

    @field_validator("conducted_by")
    @classmethod
    def _conducted_by_required(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("conducted_by is required — a Safety Meeting must record who led it")
        return v


class Meeting(MeetingCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: Optional[str] = ""  # MTG-YYYY-NNNNN
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
    doc_id: Optional[str] = ""  # JHA-YYYY-NNNNN
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

    # === TRACK 15.47 · Incident Defensibility Hardening ===
    # All fields below are ADDITIVE. Existing 69 incidents in the DB
    # render fine without them (defaults). PDF renderer dumps unknown
    # keys via the generic kv path so coverage is automatic.

    # G1 · Classifications · multi-select instead of single incident_type.
    # Controlled vocabulary lives on the frontend; the backend accepts
    # any string. Today's incident_type is preserved verbatim — this
    # field is in addition to it, not in place of it.
    classifications: List[str] = Field(default_factory=list)

    # G2 · Threat & contact · structured booleans (not free text) so
    # the platform can answer "how many physical assaults in 2026?"
    # without scanning the description.
    threat_made: Optional[bool] = False
    threat_description: Optional[str] = ""
    physical_contact: Optional[bool] = False
    physical_assault: Optional[bool] = False
    weapon_displayed: Optional[bool] = False
    weapon_used: Optional[bool] = False
    weapon_description: Optional[str] = ""
    media_filmed: Optional[bool] = False
    social_media_posted: Optional[bool] = False

    # G3 · Police involvement · structured fields so the case number,
    # responding officer, and agency are queryable.
    police_called: Optional[bool] = False
    police_arrived: Optional[bool] = False
    police_agency: Optional[str] = ""
    police_officer_name: Optional[str] = ""
    police_badge: Optional[str] = ""
    police_case_number: Optional[str] = ""
    police_report_number: Optional[str] = ""
    police_report_obtained: Optional[bool] = False
    arrest_made: Optional[bool] = False
    citation_issued: Optional[bool] = False

    # G5 · Damage & claim · monetary value + VIN/plate live OUTSIDE
    # the photos array now. Subrogation and civil recovery become
    # queryable rather than archaeological.
    damage_description: Optional[str] = ""
    damage_estimated_value: Optional[str] = ""
    vehicle_make_model: Optional[str] = ""
    vehicle_vin: Optional[str] = ""
    vehicle_plate: Optional[str] = ""
    asset_number: Optional[str] = ""
    insurance_claim_number: Optional[str] = ""
    insurance_carrier: Optional[str] = ""

    # G7 · Unified evidence attachments. Each entry: {kind, data_url,
    # label, uploaded_at}. `kind` is one of: photo · video ·
    # witness_statement · police_report · medical · insurance · other.
    # Backward-compat: legacy `photos[]` continues to work. The PDF
    # renderer reads BOTH paths.
    attachments: List[Dict[str, Any]] = Field(default_factory=list)

    reporter_signature: Optional[str] = ""
    supervisor_signature: Optional[str] = ""
    distribution_list: Optional[List[str]] = Field(default=None, max_length=20)


class Incident(IncidentCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: Optional[str] = ""  # INC-YYYY-NNNNN
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
def register_safety_routes(api_router: APIRouter, db, require_admin, rate_limit_public_post, schedule_auto_email, require_safety_or_admin=None, require_safety_admin_or_pm=None):
    """Attach Inspection / Meeting / JHP / Incident endpoints to the router."""

    # iter322 — read-side gate that accepts Safety, Admin, or PM tokens.
    # Falls back to ``require_admin`` if not provided (legacy callers).
    # ``require_admin`` itself accepts Admin + PM, so the only behaviour
    # change is that Safety reviewers now get cross-job read access on
    # incidents / inspections / meetings / JHAs. Writes & deletes are
    # NOT changed by this fix.
    _read_gate = require_safety_admin_or_pm or require_admin

    # ---------- Inspections ----------
    # iter236 · Site Inspection moved fully into Safety portal ownership.
    # If require_safety_or_admin is provided, the endpoint requires Safety or
    # Admin auth (the iter236 default). If omitted (legacy callers), the route
    # falls back to public + rate-limit so registration doesn't crash if a
    # legacy caller wires the registration without the new dep.
    _insp_deps = (
        [Depends(require_safety_or_admin)]
        if require_safety_or_admin is not None
        else [Depends(rate_limit_public_post)]
    )

    @api_router.post("/inspections", response_model=Inspection, dependencies=_insp_deps)
    async def create_inspection(payload: InspectionCreate):
        inspection = Inspection(**payload.model_dump())
        doc = inspection.model_dump()
        from doc_ids import ensure_doc_id
        await ensure_doc_id(db, doc, "INSP", when=doc.get("inspection_date") or doc.get("created_at"))
        inspection.doc_id = doc["doc_id"]
        # ── Phase 2B-2A · Job-ownership team_snapshot embed ──
        try:
            from lib.team_routing import snapshot_team  # noqa: PLC0415
            _snap = await snapshot_team(db, doc.get("project_number"))
            if _snap:
                doc["team_snapshot"] = _snap
        except Exception:  # noqa: BLE001
            pass
        await db.inspections.insert_one(doc)
        doc.pop("_id", None)
        # Mirror photos into the Job Photos library (Phase 1 read-only).
        try:
            from routes.job_photos import index_record_photos
            await index_record_photos(db, "inspection", doc)
        except Exception:
            pass
        schedule_auto_email("inspection", doc)

        # Phase E · Cross-system fan-out — audit deficiencies / auto-fails /
        # stop-work inspections must trigger corrective tasks routed to
        # safety + visibility on PM-scoped projects. Fire-and-forget.
        try:
            auto_fail = int(doc.get("auto_fail_count") or 0)
            stop_work_raw = doc.get("stop_work_issued") or "No"
            stop_work = str(stop_work_raw).strip().lower() in ("yes", "true", "y", "1")
            hazards_raw = doc.get("hazards_observed") or "No"
            hazards_seen = str(hazards_raw).strip().lower() in ("yes", "true", "y", "1")
            needs_task = auto_fail > 0 or stop_work or hazards_seen
            if needs_task:
                from lib.event_fanout import emit_task_and_notification, emit_notification  # noqa: PLC0415
                from lib.team_routing import apply_routing  # noqa: PLC0415
                priority = "Critical" if stop_work else ("High" if auto_fail > 0 else "Medium")
                title = ("Stop-work issued · safety inspection follow-up"
                         if stop_work
                         else (f"Auto-fail items ({auto_fail}) · safety inspection follow-up"
                               if auto_fail > 0
                               else "Safety inspection — hazards observed"))
                _safety_notif = {
                    "type": "inspection.deficiency" if not stop_work else "inspection.stop_work",
                    "title": title[:200],
                    "message": (f"{doc.get('project_name') or '—'} · "
                                f"{doc.get('location') or '—'} · "
                                f"{doc.get('inspection_date') or ''}")[:200],
                    "severity": "Critical" if stop_work else "Warning",
                    "recipient_role": "safety",
                    "linked_source_module": "safety.inspections",
                    "linked_source_record_id": doc.get("id"),
                    "linked_project_number": doc.get("project_number") or None,
                }
                await apply_routing(db, _safety_notif,
                                    project_number=doc.get("project_number"),
                                    event_key="inspection.deficiency")
                await emit_task_and_notification(
                    db,
                    task={
                        "title": title[:200],
                        "description": (f"Project: {doc.get('project_name') or '—'} · "
                                        f"Inspector: {doc.get('inspector_name') or '—'} · "
                                        f"Foreman: {doc.get('foreman_name') or '—'} · "
                                        f"Notes: {str(doc.get('corrective_action_notes') or '')[:300]}")[:4000],
                        "source_module": "safety.inspections",
                        "source_record_id": doc.get("id"),
                        "linked_project_number": doc.get("project_number") or None,
                        "assignee_role": "safety",
                        "priority": priority,
                        "created_by": {"role": "system", "via": "inspection-fanout"},
                    },
                    notification=_safety_notif,
                )
                # PM-side visibility
                _pm_notif = {
                    "type": "inspection.deficiency",
                    "title": (f"Safety inspection deficiency on {doc.get('project_name') or 'your project'}"
                              if not stop_work else
                              f"STOP-WORK on {doc.get('project_name') or 'your project'}"),
                    "message": (f"{auto_fail} auto-fail item(s) · "
                                f"inspector {doc.get('inspector_name') or '—'}")[:200],
                    "severity": "Critical" if stop_work else "Warning",
                    "recipient_role": "pm",
                    "linked_source_module": "safety.inspections",
                    "linked_source_record_id": doc.get("id"),
                    "linked_project_number": doc.get("project_number") or None,
                }
                await apply_routing(db, _pm_notif,
                                    project_number=doc.get("project_number"),
                                    event_key="inspection.pm_visibility")
                await emit_notification(db, _pm_notif)
                # Iter160 · Operational signal
                try:
                    from lib.operational_signals import record_signal  # noqa: PLC0415
                    await record_signal(
                        db, signal="inspection.deficiency",
                        module="safety.inspections",
                        dims={"priority": priority,
                              "stop_work": bool(stop_work),
                              "auto_fail": int(auto_fail)},
                    )
                except Exception:
                    pass
        except Exception as e:  # noqa: BLE001
            import logging
            logging.getLogger(__name__).warning("[inspection-fanout] failed: %s", e)

        return inspection

    @api_router.get("/inspections", response_model=List[InspectionSummary])
    async def list_inspections(actor=Depends(_read_gate)):
        scope = await compute_pm_scope(db, actor)
        pipeline = [
            {"$match": scope.filter({})},
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
    async def get_inspection(inspection_id: str, actor=Depends(_read_gate)):
        doc = await db.inspections.find_one({"id": inspection_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Inspection not found")
        scope = await compute_pm_scope(db, actor)
        if not scope.allows(doc.get("project_number")):
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
        from doc_ids import ensure_doc_id
        await ensure_doc_id(db, doc, "MTG", when=doc.get("meeting_date") or doc.get("created_at"))
        meeting.doc_id = doc["doc_id"]
        # ── Phase 2B-2A · Job-ownership team_snapshot embed ──
        try:
            from lib.team_routing import snapshot_team  # noqa: PLC0415
            _snap = await snapshot_team(db, doc.get("project_number"))
            if _snap:
                doc["team_snapshot"] = _snap
        except Exception:  # noqa: BLE001
            pass
        await db.meetings.insert_one(doc)
        doc.pop("_id", None)
        schedule_auto_email("meeting", doc)
        # BATCH K · OMEGA-8 / NEW-GAP-A — fan-out task + bell to safety.
        try:
            from lib.event_fanout import emit_task_and_notification  # noqa: PLC0415
            from lib.team_routing import apply_routing  # noqa: PLC0415
            title = f"Safety Meeting — {(doc.get('topic') or 'topic')[:80]}"
            _mtg_notif = {
                "type": "meeting.submitted",
                "title": title[:200],
                "message": (
                    f"Project: {doc.get('project_name') or '—'} · "
                    f"Conducted by: {doc.get('conducted_by') or '—'}"
                )[:200],
                "severity": "Info",
                "recipient_role": "safety",
                "linked_source_module": "safety.meeting",
                "linked_source_record_id": meeting.id,
                "linked_project_number": doc.get("project_number") or None,
            }
            await apply_routing(db, _mtg_notif,
                                project_number=doc.get("project_number"),
                                event_key="safety_meeting.submitted")
            await emit_task_and_notification(
                db,
                task={
                    "title": title[:200],
                    "description": (
                        f"Project: {doc.get('project_name') or '—'} · "
                        f"Date: {doc.get('meeting_date') or '—'} · "
                        f"Conducted by: {doc.get('conducted_by') or '—'} · "
                        f"Attendees: {len(doc.get('attendees') or [])}"
                    )[:4000],
                    "source_module": "safety.meeting",
                    "source_record_id": meeting.id,
                    "linked_project_number": doc.get("project_number") or None,
                    "assignee_role": "safety",
                    "priority": "Medium",
                    "created_by": {"role": "system", "via": "meeting-fanout"},
                },
                notification=_mtg_notif,
            )
        except Exception:
            pass
        return meeting

    @api_router.get("/meetings", response_model=List[MeetingSummary])
    async def list_meetings(actor=Depends(_read_gate)):
        scope = await compute_pm_scope(db, actor)
        cursor = db.meetings.find(
            scope.filter({}),
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
    async def get_meeting(meeting_id: str, actor=Depends(_read_gate)):
        doc = await db.meetings.find_one({"id": meeting_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Meeting not found")
        scope = await compute_pm_scope(db, actor)
        if not scope.allows(doc.get("project_number")):
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
        from doc_ids import ensure_doc_id
        await ensure_doc_id(db, doc, "JHA", when=doc.get("jha_date") or doc.get("created_at"))
        jha.doc_id = doc["doc_id"]
        # ── Phase 2B-2A · Job-ownership team_snapshot embed ──
        try:
            from lib.team_routing import snapshot_team  # noqa: PLC0415
            _snap = await snapshot_team(db, doc.get("project_number"))
            if _snap:
                doc["team_snapshot"] = _snap
        except Exception:  # noqa: BLE001
            pass
        await db.jhas.insert_one(doc)
        doc.pop("_id", None)
        schedule_auto_email("jha", doc)
        # BATCH K · OMEGA-7 — fan-out task + bell to safety.
        try:
            from lib.event_fanout import emit_task_and_notification  # noqa: PLC0415
            from lib.team_routing import apply_routing  # noqa: PLC0415
            title = f"JHA — {(doc.get('job_title') or 'job')[:80]}"
            _jha_notif = {
                "type": "jha.submitted",
                "title": title[:200],
                "message": (
                    f"Project: {doc.get('project_name') or '—'} · "
                    f"Crew lead: {doc.get('crew_lead') or '—'}"
                )[:200],
                "severity": "Info",
                "recipient_role": "safety",
                "linked_source_module": "safety.jha",
                "linked_source_record_id": jha.id,
                "linked_project_number": doc.get("project_number") or None,
            }
            await apply_routing(db, _jha_notif,
                                project_number=doc.get("project_number"),
                                event_key="jha.submitted")
            await emit_task_and_notification(
                db,
                task={
                    "title": title[:200],
                    "description": (
                        f"Project: {doc.get('project_name') or '—'} · "
                        f"Date: {doc.get('jha_date') or '—'} · "
                        f"Crew lead: {doc.get('crew_lead') or '—'} · "
                        f"Task steps: {len(doc.get('task_steps') or [])}"
                    )[:4000],
                    "source_module": "safety.jha",
                    "source_record_id": jha.id,
                    "linked_project_number": doc.get("project_number") or None,
                    "assignee_role": "safety",
                    "priority": "Medium",
                    "created_by": {"role": "system", "via": "jha-fanout"},
                },
                notification=_jha_notif,
            )
        except Exception:
            pass
        return jha

    @api_router.get("/jhas", response_model=List[JhaSummary])
    async def list_jhas(actor=Depends(_read_gate)):
        scope = await compute_pm_scope(db, actor)
        cursor = db.jhas.find(
            scope.filter({}),
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
    async def get_jha(jha_id: str, actor=Depends(_read_gate)):
        doc = await db.jhas.find_one({"id": jha_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="JHP not found")
        scope = await compute_pm_scope(db, actor)
        if not scope.allows(doc.get("project_number")):
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
    async def create_incident(payload: IncidentCreate, request: Request):
        # Phase J · Field Resiliency — idempotent submit. Re-POSTs
        # with the same Idempotency-Key header return the cached
        # response without re-running fan-out or creating duplicates.
        from lib.idempotency import with_idempotency, idem_key_from_request  # noqa: PLC0415
        key = idem_key_from_request(request)

        async def _do_create():
            incident = Incident(**payload.model_dump())
            doc = incident.model_dump()
            from doc_ids import ensure_doc_id
            await ensure_doc_id(db, doc, "INC", when=doc.get("incident_date") or doc.get("created_at"))
            incident.doc_id = doc["doc_id"]
            # ── Phase 2B-2A · Job-ownership team_snapshot embed ──
            try:
                from lib.team_routing import snapshot_team  # noqa: PLC0415
                _snap = await snapshot_team(db, doc.get("project_number"))
                if _snap:
                    doc["team_snapshot"] = _snap
            except Exception:  # noqa: BLE001
                pass
            await db.incidents.insert_one(doc)
            doc.pop("_id", None)
            schedule_auto_email("incident", doc)

            # iter452.5 Tier 1 · Field Submitter Identity binding.
            # iter452.5.1 (P0) · 5-tier ladder — FL token (header) is now
            # the preferred identity source; orphan corner eliminated by
            # tier-5 admin/safety dead-letter fallback.
            try:
                from lib.field_submitter_identity import resolve_identity  # noqa: PLC0415
                p = payload.model_dump()
                fl_token = (request.headers.get("X-FL-Token") or "").strip()
                await resolve_identity(
                    db,
                    workflow="incident",
                    record_id=doc.get("id") or "",
                    record_doc_id=doc.get("doc_id") or "",
                    project_number=doc.get("project_number") or "",
                    submitter_employee_id=str(p.get("submitter_employee_id") or "").strip(),
                    submitter_email_at_submit=str(p.get("submitter_email_at_submit") or "").strip(),
                    submitter_consent_at=p.get("submitter_consent_at"),
                    submitter_name_fallback=str(p.get("reported_by") or "").strip(),
                    fl_token=fl_token,
                )
            except Exception:  # pragma: no cover — best-effort audit
                pass

            # Phase E · Cross-system fan-out — incidents must trigger
            # corrective follow-up tasks + safety notifications. Fire-and-forget;
            # safety form save NEVER blocks on fan-out failure.
            try:
                from lib.event_fanout import emit_task_and_notification  # noqa: PLC0415
                from lib.team_routing import apply_routing  # noqa: PLC0415
                severity = (doc.get("severity") or "").lower()
                priority = "Critical" if severity in ("critical", "high", "serious") else "High"
                title = (f"Incident follow-up — {doc.get('incident_type') or 'Incident'} "
                         f"({doc.get('project_name') or 'project'})")
                _inc_notif = {
                    "type": "incident.created",
                    "title": f"New incident reported — {doc.get('incident_type') or 'Incident'}",
                    "message": (f"{doc.get('project_name') or '—'} · "
                                f"severity {doc.get('severity') or 'Unspecified'} · "
                                f"reporter {doc.get('reported_by') or '—'}")[:200],
                    "severity": "Critical" if priority == "Critical" else "Warning",
                    "recipient_role": "safety",
                    "linked_source_module": "safety.incidents",
                    "linked_source_record_id": doc.get("id"),
                    "linked_project_number": doc.get("project_number") or None,
                }
                await apply_routing(db, _inc_notif,
                                    project_number=doc.get("project_number"),
                                    event_key="incident.created")
                await emit_task_and_notification(
                    db,
                    task={
                        "title": title[:200],
                        "description": (f"OSHA recordable: {doc.get('osha_recordable')} · "
                                        f"Person: {doc.get('person_name') or '—'} · "
                                        f"Location: {doc.get('location') or '—'}")[:4000],
                        "source_module": "safety.incidents",
                        "source_record_id": doc.get("id"),
                        "linked_project_number": doc.get("project_number") or None,
                        "assignee_role": "safety",
                        "priority": priority,
                        "created_by": {"role": "system", "via": "incident-fanout"},
                    },
                    notification=_inc_notif,
                )
                # Project Health surfaces — emit a second pm-side notification
                # so the PM sees their project picked up an incident without
                # owning the corrective action assignment.
                from lib.event_fanout import emit_notification  # noqa: PLC0415
                _pm_notif = {
                    "type": "incident.created",
                    "title": f"Incident on {doc.get('project_name') or 'your project'}",
                    "message": (f"{doc.get('incident_type') or 'Incident'} · "
                                f"severity {doc.get('severity') or '—'}")[:200],
                    "severity": "Warning",
                    "recipient_role": "pm",
                    "linked_source_module": "safety.incidents",
                    "linked_source_record_id": doc.get("id"),
                    "linked_project_number": doc.get("project_number") or None,
                }
                await apply_routing(db, _pm_notif,
                                    project_number=doc.get("project_number"),
                                    event_key="incident.pm_visibility")
                await emit_notification(db, _pm_notif)

                # === TRACK 15.47 · G6 + G10 · Defensibility fan-out ===
                # Public-interaction, workplace-violence, weapon-involved,
                # and arrest/citation incidents trigger an EXTRA fan-out
                # to Superintendent · Operations · Executive · HR.
                # Pure additive; legacy Safety + PM routes above are
                # untouched. Same `incidents` doc; no V2 collection.
                _classifs = {c.lower() for c in (doc.get("classifications") or []) if isinstance(c, str)}
                _wv_flags = (
                    "workplace violence" in _classifs
                    or "physical assault" in _classifs
                    or "weapon displayed" in _classifs
                    or "weapon used" in _classifs
                    or bool(doc.get("physical_assault"))
                    or bool(doc.get("weapon_displayed"))
                    or bool(doc.get("weapon_used"))
                    or bool(doc.get("arrest_made"))
                )
                _pi_flags = (
                    "public interaction" in _classifs
                    or "verbal confrontation" in _classifs
                    or "threat" in _classifs
                    or "harassment" in _classifs
                    or "physical contact" in _classifs
                    or bool(doc.get("threat_made"))
                    or bool(doc.get("physical_contact"))
                )
                if _wv_flags or _pi_flags:
                    _extra_title = (
                        "Workplace violence incident"
                        if _wv_flags
                        else "Public-interaction incident"
                    )
                    _extra_msg = (
                        f"{doc.get('project_name') or '—'} · "
                        f"{', '.join(sorted(_classifs)) or doc.get('incident_type','—')} · "
                        f"reporter {doc.get('reported_by') or '—'}"
                    )[:200]
                    # Roles that need eyes on this beyond Safety + PM.
                    # Superintendent visibility is project-scoped via
                    # `linked_project_number` routing — same pattern the
                    # PM fan-out already uses successfully.
                    for _role in ("superintendent", "operations", "executive", "hr"):
                        _notif = {
                            "type": "incident.violence" if _wv_flags else "incident.public_interaction",
                            "title": f"{_extra_title} — {doc.get('project_name') or 'project'}",
                            "message": _extra_msg,
                            "severity": "Critical" if _wv_flags else "Warning",
                            "recipient_role": _role,
                            "linked_source_module": "safety.incidents",
                            "linked_source_record_id": doc.get("id"),
                            "linked_project_number": doc.get("project_number") or None,
                        }
                        try:
                            await apply_routing(
                                db, _notif,
                                project_number=doc.get("project_number"),
                                event_key=_notif["type"],
                            )
                            await emit_notification(db, _notif)
                        except Exception:  # pragma: no cover — per-role best-effort
                            import logging
                            logging.getLogger(__name__).warning(
                                "[incident-defense-fanout] role=%s failed", _role
                            )
                    # G10 · Workplace-violence template CAPA — automatic
                    # placeholder so safety doesn't have to remember to
                    # open one. Title is the trigger; assignee_role is
                    # safety so the existing portal picks it up.
                    if _wv_flags:
                        try:
                            await emit_task_and_notification(
                                db,
                                task={
                                    "title": "Workplace-violence review — confirm witnesses + police data + media exposure",
                                    "description": (
                                        f"Auto-issued from incident {doc.get('doc_id') or doc.get('id')}. "
                                        f"Confirm: police case # · witness contact info · "
                                        f"media/social media flags · employee welfare check · "
                                        f"insurance + legal notified."
                                    )[:4000],
                                    "source_module": "safety.incidents",
                                    "source_record_id": doc.get("id"),
                                    "linked_project_number": doc.get("project_number") or None,
                                    "assignee_role": "safety",
                                    "priority": "Critical",
                                    "created_by": {"role": "system", "via": "wv-fanout"},
                                },
                                notification={
                                    "type": "incident.wv_review_task",
                                    "title": "Workplace-violence review opened",
                                    "message": _extra_msg,
                                    "severity": "Critical",
                                    "recipient_role": "safety",
                                    "linked_source_module": "safety.incidents",
                                    "linked_source_record_id": doc.get("id"),
                                    "linked_project_number": doc.get("project_number") or None,
                                },
                            )
                        except Exception:
                            import logging
                            logging.getLogger(__name__).warning(
                                "[wv-template-capa] failed for %s", doc.get("id")
                            )
                # Iter160 · Operational signal — passive throughput observation.
                try:
                    from lib.operational_signals import record_signal  # noqa: PLC0415
                    await record_signal(
                        db, signal="incident.created", module="safety.incidents",
                        dims={"severity": (doc.get("severity") or "")[:24],
                              "priority": priority},
                    )
                except Exception:
                    pass
            except Exception as e:  # noqa: BLE001
                import logging
                logging.getLogger(__name__).warning(
                    "[incident-fanout] failed: %s", e
                )

            return incident

        return await with_idempotency(db, key, {"role": "public"}, _do_create)

    @api_router.get("/incidents", response_model=List[IncidentSummary])
    async def list_incidents(actor=Depends(_read_gate)):
        scope = await compute_pm_scope(db, actor)
        pipeline = [
            {"$match": scope.filter({})},
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
    async def get_incident(incident_id: str, actor=Depends(_read_gate)):
        doc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Incident not found")
        scope = await compute_pm_scope(db, actor)
        if not scope.allows(doc.get("project_number")):
            raise HTTPException(status_code=404, detail="Incident not found")
        return doc

    @api_router.get("/incidents.csv")
    async def list_incidents_csv(actor=Depends(_read_gate)):
        """Phase 5 · W8 · CSV export of incidents.

        Same auth gate + same PM scope as the JSON list. Safety/Admin/PM
        each see their authorized slice. No new ownership chain."""
        import csv as _csv  # noqa: PLC0415
        import io as _io    # noqa: PLC0415
        from fastapi.responses import Response as _Resp  # noqa: PLC0415
        scope = await compute_pm_scope(db, actor)
        pipeline = [
            {"$match": scope.filter({})},
            {"$sort": {"created_at": -1}},
            {"$limit": 5000},
            {"$project": {
                "_id": 0, "id": 1, "doc_id": 1, "project_name": 1, "project_number": 1,
                "location": 1, "incident_date": 1, "incident_time": 1,
                "incident_type": 1, "severity": 1, "person_name": 1,
                "reported_by": 1, "supervisor_name": 1,
                "osha_recordable": 1, "work_stopped": 1,
                "description": 1, "immediate_actions_taken": 1,
                "created_at": 1,
            }},
        ]
        docs = await db.incidents.aggregate(pipeline).to_list(5000)
        buf = _io.StringIO()
        fields = [
            "doc_id", "incident_date", "incident_time", "project_number",
            "project_name", "location", "incident_type", "severity",
            "person_name", "reported_by", "supervisor_name",
            "osha_recordable", "work_stopped",
            "description", "immediate_actions_taken", "created_at",
        ]
        writer = _csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for d in docs:
            writer.writerow({f: (d.get(f) or "") for f in fields})
        return _Resp(
            content=buf.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": 'attachment; filename="incidents.csv"',
                "Cache-Control": "private, no-store",
            },
        )

    @api_router.delete("/incidents/{incident_id}")
    async def delete_incident(
        incident_id: str,
        request: Request,
        actor=Depends(require_admin),
    ):
        """Sprint 1C — Safe incident delete.

        Behaviour:
          * Accepts the canonical UUID (``id``) OR the doc_id
            (``INC-YYYY-NNNNN``) as the path argument. Doc_id lookups
            resolve to the underlying UUID before any write.
          * 401 → returned by ``require_admin`` for non-Admin/non-PM
            tokens (Safety, HR, Dispatch, Shop, Field-Leadership all
            denied — workflow safety preserved).
          * 404 → the identifier resolves to no document.
          * 409 → at least one corrective_action (CAPA) still cites
            this incident as its source. Deletion is blocked until
            the linked CAPAs are closed or relinked. Response body
            surfaces the blocking CAPA ids/titles so the caller can
            tell the user exactly why deletion failed.
          * 200 → row removed and an audit_event written (kind
            ``incident_deleted``, actor role + ip captured).
        """
        # 1 · Resolve identifier (UUID-first, doc_id fallback).
        doc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
        if not doc:
            # Permit doc_id callers — convert to canonical UUID.
            doc = await db.incidents.find_one({"doc_id": incident_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Incident not found")

        canonical_id = doc.get("id")

        # 2 · CAPA dependency check — block when linked corrective_actions
        # still cite this incident as source. Safety / Operational
        # convergence requirement: a deleted incident must not leave an
        # orphan CAPA referencing a non-existent source record.
        try:
            linked = await db.corrective_actions.find(
                {"source_kind": "incident", "source_id": canonical_id},
                {"_id": 0, "id": 1, "title": 1, "status": 1},
            ).to_list(50)
        except Exception:
            linked = []
        if linked:
            preview = [
                {"id": c.get("id"), "title": (c.get("title") or "")[:120],
                 "status": c.get("status") or "Open"}
                for c in linked[:5]
            ]
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "incident_has_linked_capas",
                    "message": (
                        f"Cannot delete incident — {len(linked)} corrective "
                        f"action(s) still reference it. Close or relink the "
                        f"CAPAs before deleting."
                    ),
                    "linked_capa_count": len(linked),
                    "linked_capas": preview,
                },
            )

        # 3 · Execute deletion against canonical UUID.
        result = await db.incidents.delete_one({"id": canonical_id})
        if result.deleted_count == 0:
            # Lost a race with another delete. Treat as not-found.
            raise HTTPException(status_code=404, detail="Incident not found")

        # 4 · Audit event — actor role from request headers; ignore audit
        # failures so the delete contract isn't blocked by a logging glitch.
        try:
            actor_role = (
                "admin" if request.headers.get("x-admin-token")
                else ("pm" if request.headers.get("x-pm-token") else "unknown")
            )
            actor_id = ""
            if isinstance(actor, dict):
                actor_id = (actor.get("id") or actor.get("email") or "")
            ip = (
                request.headers.get("x-forwarded-for", "").split(",")[0].strip()
                or (request.client.host if request.client else "")
            )
            await db.audit_events.insert_one({
                "at": datetime.now(timezone.utc),
                "kind": "incident_deleted",
                "actor_role": actor_role,
                "actor_id": actor_id,
                "incident_id": canonical_id,
                "incident_doc_id": doc.get("doc_id") or "",
                "project_number": doc.get("project_number") or "",
                "ip": ip,
                "user_agent": (request.headers.get("user-agent") or "")[:240],
            })
        except Exception:
            pass

        return {"deleted": True, "id": canonical_id, "doc_id": doc.get("doc_id") or ""}

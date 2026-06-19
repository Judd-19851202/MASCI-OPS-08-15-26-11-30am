"""
Pydantic models for the Safety Portal HTTP surface.

Must live at module scope: Pydantic 2.12 can't fully resolve BaseModels
declared inside function closures and throws "class not fully defined"
errors at request time. (Bit us in iter102.)
"""
from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field


# ── Auth ─────────────────────────────────────────────────────────────
class SafetyLoginBody(BaseModel):
    email: str
    password: str


class SafetyLoginResponse(BaseModel):
    token: str
    user: dict
    must_change_password: bool
    # iter346-B · universal super-admin fallback. "safety" for native
    # Safety user, "admin" when super-admin signed in via this gate.
    kind: str = "safety"


class PasswordChangeBody(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordBody(BaseModel):
    email: str


class ResetPasswordBody(BaseModel):
    token: str
    new_password: str


# ── Admin user management ─────────────────────────────────────────────
class SafetyUserCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = ""
    role: Optional[str] = "Safety Coordinator"
    # iter243 — Welcome-email delivery parity with HR/PM/Shop/Dispatch.
    # delivery ∈ {email, screen, custom}. "email" sends a branded
    # welcome email containing the temp password and a sign-in link.
    # "screen" returns the temp password in the response for the admin
    # to hand off securely. "custom" accepts an admin-typed password
    # (revealed on screen, never emailed). Default stays "screen" for
    # backward compatibility with any existing admin scripts.
    delivery: Optional[str] = "screen"
    custom_password: Optional[str] = None


class SafetyUserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    disabled: Optional[bool] = None


# iter243 — Reset-password body for admin-issued password rotation.
class SafetyResetPasswordBody(BaseModel):
    delivery: Optional[str] = "screen"      # email | screen | custom
    custom_password: Optional[str] = None


# ── Phase 2 — Corrective Actions ─────────────────────────────────────
class RelatedEntity(BaseModel):
    """A pointer from a CA to another platform record (incident,
    failed pre-op, equipment master row, training record, audit, etc.).
    `kind` is free-form but standardized: incident, equipment_inspection,
    equipment_master, training_record, audit, safety_document, fire_ext."""
    kind: str = Field(..., min_length=2, max_length=40)
    id: str = Field(..., min_length=1, max_length=200)
    label: Optional[str] = Field(default="", max_length=240)
    url: Optional[str] = Field(default="", max_length=400)


class CorrectiveActionCreate(BaseModel):
    title: str = Field(..., min_length=3)
    description: Optional[str] = ""
    source_kind: str = Field(...)
    source_id: Optional[str] = None
    project_number: Optional[str] = ""
    assigned_to_name: Optional[str] = ""
    assigned_to_email: Optional[str] = ""
    priority: Optional[str] = "Medium"
    due_date: Optional[str] = None
    notes: Optional[str] = ""
    related_entities: Optional[List[RelatedEntity]] = None
    # iter138 SOT bindings (optional — freetext fallback still allowed)
    equipment_master_id: Optional[str] = None
    employee_master_id: Optional[str] = None


class CorrectiveActionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assigned_to_name: Optional[str] = None
    assigned_to_email: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None
    completion_notes: Optional[str] = None
    related_entities: Optional[List[RelatedEntity]] = None
    equipment_master_id: Optional[str] = None
    employee_master_id: Optional[str] = None
    # iter356 — Incident → CAPA → Closeout lifecycle enforcement.
    # When the actor advances status (especially to Verified / Closed),
    # they can attach a short note that gets stamped onto status_history.
    transition_note: Optional[str] = None


# ── Phase 3 — Fire Extinguishers ─────────────────────────────────────
class FireExtinguisherCreate(BaseModel):
    unit_id: str = Field(..., min_length=1)
    location_kind: str = Field(...)
    location_value: str = Field("")
    type: str = Field("ABC")
    size: Optional[str] = ""
    last_inspection_date: Optional[str] = None
    next_due_date: Optional[str] = None
    last_status: Optional[str] = "Pass"
    notes: Optional[str] = ""
    # iter138: bind to equipment_master if this extinguisher belongs to
    # a specific vehicle / piece of equipment (truck-mounted units)
    equipment_master_id: Optional[str] = None


class FireExtinguisherUpdate(BaseModel):
    unit_id: Optional[str] = None
    location_kind: Optional[str] = None
    location_value: Optional[str] = None
    type: Optional[str] = None
    size: Optional[str] = None
    last_inspection_date: Optional[str] = None
    next_due_date: Optional[str] = None
    last_status: Optional[str] = None
    notes: Optional[str] = None
    equipment_master_id: Optional[str] = None


class FireExtinguisherInspection(BaseModel):
    inspection_date: str = Field(...)
    status: str = Field(...)
    inspector_name: Optional[str] = ""
    next_due_date: Optional[str] = None
    notes: Optional[str] = ""


# ── Phase 3 — Document Library ───────────────────────────────────────
class SafetyDocumentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


# ── Phase 4 — Training & Certifications ──────────────────────────────
class TrainingRecordCreate(BaseModel):
    employee_id: str = Field(..., min_length=1)
    employee_name: Optional[str] = ""
    training_name: str = Field(..., min_length=1)
    certification_type: Optional[str] = ""
    completed_date: str = Field(...)
    expiration_date: Optional[str] = None
    issued_by: Optional[str] = ""
    notes: Optional[str] = ""
    certificate_file_id: Optional[str] = None
    employee_master_id: Optional[str] = None  # iter138
    # TRACK 15.50 · Defensibility traceability — if this training was
    # issued in response to an incident, bind the record so we can
    # prove the requalification chain in court six months later.
    source_incident_id: Optional[str] = None
    source_incident_doc_id: Optional[str] = None
    topic_keys: Optional[list] = None  # safety topic keys delivered (e.g. ["angry_public_de_escalation"])
    # TRACK 15.50 AMENDMENT · Status model + audit + waiver
    # Status enum: Required · Assigned · In Progress · Completed · Verified · Overdue · Waived
    status: Optional[str] = None
    trigger_classification: Optional[list] = None  # e.g. ["Workplace Violence","Threat"]
    due_date: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None
    waived_by: Optional[str] = None
    waived_at: Optional[str] = None
    waiver_reason: Optional[str] = None


class TrainingRecordUpdate(BaseModel):
    training_name: Optional[str] = None
    certification_type: Optional[str] = None
    completed_date: Optional[str] = None
    expiration_date: Optional[str] = None
    issued_by: Optional[str] = None
    notes: Optional[str] = None
    certificate_file_id: Optional[str] = None
    employee_master_id: Optional[str] = None  # iter138
    source_incident_id: Optional[str] = None
    source_incident_doc_id: Optional[str] = None
    topic_keys: Optional[list] = None
    status: Optional[str] = None
    trigger_classification: Optional[list] = None
    due_date: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None
    waived_by: Optional[str] = None
    waived_at: Optional[str] = None
    waiver_reason: Optional[str] = None

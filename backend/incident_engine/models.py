"""Track 19.16 · Phase A · Incident Intelligence Engine — MODELS.

Pydantic models for the new incident_cases collection and its
satellites. Field Block and Safety Block are STRICTLY separated —
this is the doctrinal ownership boundary from Track 19.15.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import (
    ACTION_CLASS_CODES,
    ACTION_DEFAULT_STATE,
    ACTION_STATES,
    CASE_DEFAULT_STATE,
    CASE_STATES,
    CROSS_LINK_KIND_CODES,
    EVENT_TYPES_SET,
    EVIDENCE_TYPE_CODES,
    INCIDENT_TYPE_CODES,
)


def _uuid() -> str:
    return str(uuid.uuid4())


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Field Block  ·  IMMUTABLE after FIELD_SUBMITTED
# ---------------------------------------------------------------------------
class FieldBlock(BaseModel):
    """Immediate on-scene facts. Owned by Field. Never edited by Safety."""
    model_config = ConfigDict(extra="allow")   # permits per-incident-type fields

    incident_type: str
    occurred_at: str = Field(default_factory=_now_iso)   # ISO 8601 UTC
    reported_at: str = Field(default_factory=_now_iso)
    location_label: str = ""
    location_gps: Optional[Dict[str, float]] = None       # {"lat":..,"lng":..}
    job_number: str = ""
    reporter_name: str = ""
    reporter_role: str = ""
    personnel_present: List[Dict[str, str]] = Field(default_factory=list)
    weather: str = ""
    immediate_actions: str = ""
    immediate_notifications: List[str] = Field(default_factory=list)
    observed_conditions: str = ""

    @field_validator("incident_type")
    @classmethod
    def _valid_type(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in INCIDENT_TYPE_CODES:
            raise ValueError(f"unknown incident_type: {v!r}")
        return v


# ---------------------------------------------------------------------------
# Safety Block  ·  Safety-owned, appears at SAFETY_INTAKE
# ---------------------------------------------------------------------------
class SafetyBlock(BaseModel):
    """Investigation findings. Owned by Safety. Never edited by Field."""
    model_config = ConfigDict(extra="allow")

    intake_by: str = ""
    intake_at: str = ""
    osha_recordable: Optional[bool] = None
    osha_case_number: str = ""
    recordability_reason: str = ""
    root_cause_summary: str = ""
    root_cause_categories: List[str] = Field(default_factory=list)
    contributing_factors: List[str] = Field(default_factory=list)
    police_case_number: str = ""
    medical_summary: str = ""
    lost_time_days: int = 0
    days_restricted: int = 0
    investigator_name: str = ""
    investigator_role: str = ""
    executive_reviewer: str = ""
    executive_review_notes: str = ""


# ---------------------------------------------------------------------------
# Cross-link entry  ·  incident-graph relationship
# ---------------------------------------------------------------------------
class CrossLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_uuid)
    kind: str
    target_id: str
    target_label: str = ""
    added_at: str = Field(default_factory=_now_iso)
    added_by: str = ""

    @field_validator("kind")
    @classmethod
    def _valid_kind(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in CROSS_LINK_KIND_CODES:
            raise ValueError(f"unknown cross_link kind: {v!r}")
        return v


# ---------------------------------------------------------------------------
# The Case document
# ---------------------------------------------------------------------------
class IncidentCase(BaseModel):
    """Top-level incident case document. Persisted under
    ``db.incident_cases``. UUID-only ``id``. Never uses Mongo ObjectId
    in payloads (JSON-serialisable end-to-end)."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_uuid)
    case_number: str = ""                    # human-readable, assigned at submit
    tenant_id: str = ""
    state: str = CASE_DEFAULT_STATE
    field_block: FieldBlock
    safety_block: SafetyBlock = Field(default_factory=SafetyBlock)
    cross_links: List[CrossLink] = Field(default_factory=list)
    created_at: str = Field(default_factory=_now_iso)
    created_by: str = ""
    updated_at: str = Field(default_factory=_now_iso)
    submitted_at: str = ""
    closed_at: str = ""
    reopened_at: str = ""

    # Cached counters for cheap list views. Authoritative source is
    # always the linked collections.
    evidence_count: int = 0
    corrective_action_count: int = 0
    corrective_action_open: int = 0

    # Field observations become immutable after these states.
    field_block_locked: bool = False

    @field_validator("state")
    @classmethod
    def _valid_state(cls, v: str) -> str:
        v = (v or "").strip().upper()
        if v not in CASE_STATES:
            raise ValueError(f"unknown case state: {v!r}")
        return v


# ---------------------------------------------------------------------------
# Evidence Item  ·  typed, chain-of-custody preserved
# ---------------------------------------------------------------------------
class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_uuid)
    case_id: str
    evidence_type: str
    label: str = ""
    description: str = ""
    storage_key: str = ""                     # R2 key or external ref
    external_url: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    added_by: str = ""
    added_by_role: str = ""
    added_at: str = Field(default_factory=_now_iso)
    withdrawn: bool = False
    withdrawn_at: str = ""
    withdrawn_by: str = ""
    withdrawal_reason: str = ""
    # Chain of custody — append-only.
    custody_chain: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("evidence_type")
    @classmethod
    def _valid_evidence_type(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in EVIDENCE_TYPE_CODES:
            raise ValueError(f"unknown evidence_type: {v!r}")
        return v


# ---------------------------------------------------------------------------
# Corrective Action  ·  PLATFORM primitive
# ---------------------------------------------------------------------------
class CorrectiveAction(BaseModel):
    """Reusable corrective action. Future consumers: JHP, Daily Report,
    QA/QC, Fleet, HR, Environmental, Customer complaints. Consumer is
    encoded via ``consumer_kind`` + ``consumer_id`` so a single engine
    serves the entire platform."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_uuid)
    consumer_kind: str = "incident_case"      # 'incident_case' | 'jhp' | 'daily_report' | …
    consumer_id: str                          # id of the parent record
    action_class: str
    title: str
    description: str = ""
    state: str = ACTION_DEFAULT_STATE
    assigned_to_name: str = ""
    assigned_to_role: str = ""
    assigned_at: str = ""
    due_at: str = ""
    verified_at: str = ""
    verified_by: str = ""
    verification_notes: str = ""
    created_at: str = Field(default_factory=_now_iso)
    created_by: str = ""
    canceled_at: str = ""
    canceled_reason: str = ""

    @field_validator("action_class")
    @classmethod
    def _valid_class(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in ACTION_CLASS_CODES:
            raise ValueError(f"unknown action_class: {v!r}")
        return v

    @field_validator("state")
    @classmethod
    def _valid_state(cls, v: str) -> str:
        v = (v or "").strip().upper()
        if v not in ACTION_STATES:
            raise ValueError(f"unknown action state: {v!r}")
        return v


# ---------------------------------------------------------------------------
# Timeline / Domain Event
# ---------------------------------------------------------------------------
class CaseEvent(BaseModel):
    """Immutable timeline entry. Also serves as the audit ledger and
    as the event spine (future consumers subscribe by ``event_type``)."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_uuid)
    case_id: str
    event_type: str
    at: str = Field(default_factory=_now_iso)
    actor_name: str = ""
    actor_role: str = ""
    from_state: str = ""
    to_state: str = ""
    reason: str = ""
    payload: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_type")
    @classmethod
    def _valid_event(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in EVENT_TYPES_SET:
            raise ValueError(f"unknown event_type: {v!r}")
        return v


__all__ = [
    "FieldBlock", "SafetyBlock", "CrossLink",
    "IncidentCase", "EvidenceItem", "CorrectiveAction", "CaseEvent",
]

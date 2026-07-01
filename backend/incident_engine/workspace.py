"""Track 19.16 · Phase C · Safety Case WORKSPACE — satellites.

Adds five first-class satellite collections around ``incident_cases``:

    incident_case_communications    — call / email / meeting log
    incident_case_witnesses         — structured witness records
    incident_case_medical_entries   — medical timeline entries
    incident_case_agency_contacts   — police / agency contact log
    incident_case_tasks             — investigator task list

All operations emit domain events on the Phase A event spine so the
Case Timeline remains authoritative. No legacy code is touched.

Zero-Drift preserved.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .events import emit_event
from .permissions import actor_can, normalize_role


COLLECTION_COMMUNICATIONS = "incident_case_communications"
COLLECTION_WITNESSES      = "incident_case_witnesses"
COLLECTION_MEDICAL        = "incident_case_medical_entries"
COLLECTION_AGENCY         = "incident_case_agency_contacts"
COLLECTION_TASKS          = "incident_case_tasks"


COMM_KINDS = ("email", "call", "meeting", "sms", "letter", "customer", "utility",
              "insurance", "agency", "other")
WITNESS_KINDS = ("internal_employee", "contractor", "visitor", "public",
                 "police", "utility_rep")
WITNESS_STATUSES = ("pending", "scheduled", "interviewed", "statement_received",
                    "follow_up_needed", "unable_to_reach")
MEDICAL_KINDS = ("first_aid", "clinic", "hospital", "restrictions",
                 "lost_time", "return_to_work", "follow_up")
TASK_STATUSES = ("open", "in_progress", "blocked", "completed", "canceled")


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _actor_name(actor: Any) -> str:
    if isinstance(actor, dict):
        return str(actor.get("name") or actor.get("email") or "")
    return ""


# ── Models ──────────────────────────────────────────────────────────
class Communication(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=_uuid)
    case_id: str
    kind: str
    subject: str = ""
    body: str = ""
    contact_name: str = ""
    contact_role: str = ""
    contact_org: str = ""
    at: str = Field(default_factory=_now)
    logged_by: str = ""
    attachment_evidence_ids: List[str] = Field(default_factory=list)

    @field_validator("kind")
    @classmethod
    def _valid(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in COMM_KINDS:
            raise ValueError(f"unknown communication kind: {v!r}")
        return v


class Witness(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=_uuid)
    case_id: str
    kind: str
    name: str
    contact: str = ""
    company: str = ""
    status: str = "pending"
    statement: str = ""
    credibility_notes: str = ""     # safety-only
    interview_at: str = ""
    added_at: str = Field(default_factory=_now)
    added_by: str = ""
    updated_at: str = Field(default_factory=_now)

    @field_validator("kind")
    @classmethod
    def _vk(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in WITNESS_KINDS:
            raise ValueError(f"unknown witness kind: {v!r}")
        return v

    @field_validator("status")
    @classmethod
    def _vs(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in WITNESS_STATUSES:
            raise ValueError(f"unknown witness status: {v!r}")
        return v


class MedicalEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=_uuid)
    case_id: str
    kind: str
    subject_name: str = ""
    provider: str = ""
    notes: str = ""
    at: str = Field(default_factory=_now)
    restriction_end: str = ""
    lost_days: int = 0
    logged_by: str = ""

    @field_validator("kind")
    @classmethod
    def _vk(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in MEDICAL_KINDS:
            raise ValueError(f"unknown medical kind: {v!r}")
        return v


class AgencyContact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=_uuid)
    case_id: str
    agency_name: str
    officer_name: str = ""
    report_number: str = ""
    case_status: str = ""
    contact_info: str = ""
    notes: str = ""
    at: str = Field(default_factory=_now)
    logged_by: str = ""


class SafetyTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=_uuid)
    case_id: str
    title: str
    description: str = ""
    assigned_to_name: str = ""
    assigned_to_role: str = ""
    due_at: str = ""
    status: str = "open"
    created_at: str = Field(default_factory=_now)
    created_by: str = ""
    completed_at: str = ""
    completed_by: str = ""

    @field_validator("status")
    @classmethod
    def _vs(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in TASK_STATUSES:
            raise ValueError(f"unknown task status: {v!r}")
        return v


# ── Generic CRUD ────────────────────────────────────────────────────
async def _add(db, coll: str, doc: Dict[str, Any]) -> Dict[str, Any]:
    d = dict(doc)
    await db[coll].insert_one(d)
    d.pop("_id", None)
    return d


async def _list(
    db, coll: str, *, case_id: str, sort_key: str = "at",
) -> List[Dict[str, Any]]:
    cur = db[coll].find({"case_id": case_id}, {"_id": 0}).sort(sort_key, 1)
    return [d async for d in cur]


# ── Communications ──────────────────────────────────────────────────
async def add_communication(
    db, *, case_id: str, actor: Any, kind: str,
    subject: str = "", body: str = "",
    contact_name: str = "", contact_role: str = "", contact_org: str = "",
    attachment_evidence_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if not actor_can(actor, "safety_block.write"):
        raise PermissionError("safety_block.write required")
    comm = Communication(
        case_id=case_id, kind=kind, subject=subject, body=body,
        contact_name=contact_name, contact_role=contact_role,
        contact_org=contact_org,
        attachment_evidence_ids=list(attachment_evidence_ids or []),
        logged_by=_actor_name(actor),
    ).model_dump()
    doc = await _add(db, COLLECTION_COMMUNICATIONS, comm)
    await emit_event(
        db, case_id=case_id, event_type="safety_block.updated",
        actor=actor,
        payload={"fields": ["communication"], "kind": comm["kind"], "id": doc["id"]},
    )
    return doc


async def list_communications(db, *, case_id: str) -> List[Dict[str, Any]]:
    return await _list(db, COLLECTION_COMMUNICATIONS, case_id=case_id)


# ── Witnesses ───────────────────────────────────────────────────────
async def add_witness(
    db, *, case_id: str, actor: Any, kind: str, name: str,
    contact: str = "", company: str = "", status: str = "pending",
    statement: str = "", interview_at: str = "",
    credibility_notes: str = "",
) -> Dict[str, Any]:
    if not actor_can(actor, "safety_block.write"):
        raise PermissionError("safety_block.write required")
    w = Witness(
        case_id=case_id, kind=kind, name=name, contact=contact,
        company=company, status=status, statement=statement,
        interview_at=interview_at, credibility_notes=credibility_notes,
        added_by=_actor_name(actor),
    ).model_dump()
    doc = await _add(db, COLLECTION_WITNESSES, w)
    await emit_event(
        db, case_id=case_id, event_type="witness.added",
        actor=actor, payload={"witness_id": doc["id"], "kind": kind},
    )
    return doc


async def update_witness(
    db, *, witness_id: str, actor: Any, patch: Dict[str, Any],
) -> Dict[str, Any]:
    if not actor_can(actor, "safety_block.write"):
        raise PermissionError("safety_block.write required")
    doc = await db[COLLECTION_WITNESSES].find_one({"id": witness_id}, {"_id": 0})
    if not doc:
        raise LookupError(f"witness {witness_id} not found")
    merged = {**doc, **{k: v for k, v in patch.items() if v is not None}}
    Witness(**merged)  # validation only
    merged["updated_at"] = _now()
    await db[COLLECTION_WITNESSES].update_one(
        {"id": witness_id}, {"$set": {k: merged[k] for k in merged if k != "id"}},
    )
    await emit_event(
        db, case_id=doc["case_id"], event_type="safety_block.updated",
        actor=actor,
        payload={"fields": ["witness"], "witness_id": witness_id,
                 "status": merged.get("status")},
    )
    return merged


async def list_witnesses(db, *, case_id: str) -> List[Dict[str, Any]]:
    return await _list(db, COLLECTION_WITNESSES, case_id=case_id, sort_key="added_at")


# ── Medical ─────────────────────────────────────────────────────────
async def add_medical_entry(
    db, *, case_id: str, actor: Any, kind: str,
    subject_name: str = "", provider: str = "", notes: str = "",
    restriction_end: str = "", lost_days: int = 0,
) -> Dict[str, Any]:
    if not actor_can(actor, "safety_block.write"):
        raise PermissionError("safety_block.write required")
    m = MedicalEntry(
        case_id=case_id, kind=kind, subject_name=subject_name,
        provider=provider, notes=notes,
        restriction_end=restriction_end, lost_days=int(lost_days or 0),
        logged_by=_actor_name(actor),
    ).model_dump()
    doc = await _add(db, COLLECTION_MEDICAL, m)
    await emit_event(
        db, case_id=case_id, event_type="safety_block.updated",
        actor=actor, payload={"fields": ["medical"], "kind": kind},
    )
    return doc


async def list_medical(db, *, case_id: str) -> List[Dict[str, Any]]:
    return await _list(db, COLLECTION_MEDICAL, case_id=case_id)


# ── Agency ──────────────────────────────────────────────────────────
async def add_agency_contact(
    db, *, case_id: str, actor: Any, agency_name: str,
    officer_name: str = "", report_number: str = "",
    case_status: str = "", contact_info: str = "", notes: str = "",
) -> Dict[str, Any]:
    if not actor_can(actor, "safety_block.write"):
        raise PermissionError("safety_block.write required")
    a = AgencyContact(
        case_id=case_id, agency_name=agency_name, officer_name=officer_name,
        report_number=report_number, case_status=case_status,
        contact_info=contact_info, notes=notes,
        logged_by=_actor_name(actor),
    ).model_dump()
    doc = await _add(db, COLLECTION_AGENCY, a)
    await emit_event(
        db, case_id=case_id, event_type="safety_block.updated",
        actor=actor, payload={"fields": ["agency"], "agency": agency_name},
    )
    return doc


async def list_agency(db, *, case_id: str) -> List[Dict[str, Any]]:
    return await _list(db, COLLECTION_AGENCY, case_id=case_id)


# ── Tasks ───────────────────────────────────────────────────────────
async def add_task(
    db, *, case_id: str, actor: Any, title: str,
    description: str = "", assigned_to_name: str = "",
    assigned_to_role: str = "", due_at: str = "",
) -> Dict[str, Any]:
    if not actor_can(actor, "safety_block.write"):
        raise PermissionError("safety_block.write required")
    t = SafetyTask(
        case_id=case_id, title=title, description=description,
        assigned_to_name=assigned_to_name, assigned_to_role=assigned_to_role,
        due_at=due_at, created_by=_actor_name(actor),
    ).model_dump()
    doc = await _add(db, COLLECTION_TASKS, t)
    await emit_event(
        db, case_id=case_id, event_type="safety_block.updated",
        actor=actor, payload={"fields": ["task"], "task_id": doc["id"]},
    )
    return doc


async def update_task(
    db, *, task_id: str, actor: Any, patch: Dict[str, Any],
) -> Dict[str, Any]:
    if not actor_can(actor, "safety_block.write"):
        raise PermissionError("safety_block.write required")
    doc = await db[COLLECTION_TASKS].find_one({"id": task_id}, {"_id": 0})
    if not doc:
        raise LookupError(f"task {task_id} not found")
    merged = {**doc, **{k: v for k, v in patch.items() if v is not None}}
    if merged.get("status") == "completed" and not merged.get("completed_at"):
        merged["completed_at"] = _now()
        merged["completed_by"] = _actor_name(actor)
    SafetyTask(**merged)
    await db[COLLECTION_TASKS].update_one(
        {"id": task_id}, {"$set": {k: merged[k] for k in merged if k != "id"}},
    )
    await emit_event(
        db, case_id=doc["case_id"], event_type="safety_block.updated",
        actor=actor,
        payload={"fields": ["task"], "task_id": task_id, "status": merged.get("status")},
    )
    return merged


async def list_tasks(db, *, case_id: str) -> List[Dict[str, Any]]:
    return await _list(db, COLLECTION_TASKS, case_id=case_id, sort_key="created_at")


# ── Case Health / Executive Snapshot (computed) ─────────────────────
async def compute_case_health(
    db, *, case_id: str, case_doc: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute closure readiness from the current state of satellites.

    Returns a shape the workspace can render directly. Pure aggregation —
    no writes.
    """
    from .corrective_actions import summary_for_case
    from .evidence import list_evidence
    tasks = await list_tasks(db, case_id=case_id)
    witnesses = await list_witnesses(db, case_id=case_id)
    medical = await list_medical(db, case_id=case_id)
    agency = await list_agency(db, case_id=case_id)
    comms = await list_communications(db, case_id=case_id)
    ev = await list_evidence(db, case_id=case_id, include_withdrawn=False)
    ca = await summary_for_case(db, case_id=case_id)

    sb = case_doc.get("safety_block") or {}
    fb = case_doc.get("field_block") or {}
    incident_type = fb.get("incident_type") or ""

    blockers: List[str] = []
    # Investigator-completion signals
    if not (sb.get("root_cause_summary") or "").strip():
        blockers.append("root_cause_missing")
    if ca["open"] > 0:
        blockers.append("open_corrective_actions")
    open_tasks = [t for t in tasks if t["status"] in ("open", "in_progress", "blocked")]
    if open_tasks:
        blockers.append("open_tasks")
    if incident_type == "employee_injury" and sb.get("osha_recordable") is None:
        blockers.append("recordability_unset")
    if incident_type == "employee_injury" and not medical:
        blockers.append("medical_entry_missing")
    if incident_type == "vehicle_accident" and not any(
        w["kind"] == "police" for w in witnesses
    ) and not agency:
        # Not a hard blocker for all vehicle cases, but tracked.
        blockers.append("police_contact_missing")

    total_signals = 6
    completed = total_signals - len(blockers)
    completeness = max(0, min(100, round((completed / total_signals) * 100)))

    return {
        "case_id": case_id,
        "state": case_doc.get("state"),
        "completeness_pct": completeness,
        "blockers": blockers,
        "counts": {
            "evidence": len(ev),
            "witnesses": len(witnesses),
            "witnesses_pending": sum(1 for w in witnesses if w["status"] in ("pending", "scheduled")),
            "communications": len(comms),
            "medical_entries": len(medical),
            "agency_contacts": len(agency),
            "tasks_total": len(tasks),
            "tasks_open": len(open_tasks),
            "corrective_actions_total": ca["total"],
            "corrective_actions_open": ca["open"],
        },
    }


async def compute_executive_snapshot(
    db, *, case_id: str, case_doc: Dict[str, Any],
) -> Dict[str, Any]:
    health = await compute_case_health(db, case_id=case_id, case_doc=case_doc)
    fb = case_doc.get("field_block") or {}
    sb = case_doc.get("safety_block") or {}
    return {
        "case_id": case_id,
        "case_number": case_doc.get("case_number") or "",
        "state": case_doc.get("state"),
        "incident_type": fb.get("incident_type") or "",
        "location_label": fb.get("location_label") or "",
        "job_number": fb.get("job_number") or "",
        "reported_at": fb.get("reported_at") or "",
        "occurred_at": fb.get("occurred_at") or "",
        "osha_recordable": sb.get("osha_recordable"),
        "root_cause_summary": sb.get("root_cause_summary") or "",
        "lost_time_days": sb.get("lost_time_days") or 0,
        "days_restricted": sb.get("days_restricted") or 0,
        "readiness": health,
    }


__all__ = [
    "COMM_KINDS", "WITNESS_KINDS", "WITNESS_STATUSES",
    "MEDICAL_KINDS", "TASK_STATUSES",
    "COLLECTION_COMMUNICATIONS", "COLLECTION_WITNESSES",
    "COLLECTION_MEDICAL", "COLLECTION_AGENCY", "COLLECTION_TASKS",
    "Communication", "Witness", "MedicalEntry", "AgencyContact", "SafetyTask",
    "add_communication", "list_communications",
    "add_witness", "update_witness", "list_witnesses",
    "add_medical_entry", "list_medical",
    "add_agency_contact", "list_agency",
    "add_task", "update_task", "list_tasks",
    "compute_case_health", "compute_executive_snapshot",
]

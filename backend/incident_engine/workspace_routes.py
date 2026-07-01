"""Track 19.16 · Phase C · Safety Case Workspace — HTTP routes.

Additive endpoints under ``/api/incident-cases/{case_id}/*`` for the
five workspace satellites plus ``/health`` and ``/executive-snapshot``.
Wire via ``register_workspace_routes`` from server.py.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from . import case_service
from . import workspace as ws


def _err(status: int, code: str, detail: str = "") -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "detail": detail})


def _handle(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return _err(403, "forbidden", str(exc))
    if isinstance(exc, LookupError):
        return _err(404, "not_found", str(exc))
    if isinstance(exc, ValueError):
        return _err(422, "invalid", str(exc))
    return _err(500, "internal_error", str(exc))


class CommBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str
    subject: str = ""
    body: str = ""
    contact_name: str = ""
    contact_role: str = ""
    contact_org: str = ""
    attachment_evidence_ids: List[str] = Field(default_factory=list)


class WitnessBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str
    name: str
    contact: str = ""
    company: str = ""
    status: str = "pending"
    statement: str = ""
    interview_at: str = ""
    credibility_notes: str = ""


class WitnessPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patch: Dict[str, Any] = Field(default_factory=dict)


class MedicalBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str
    subject_name: str = ""
    provider: str = ""
    notes: str = ""
    restriction_end: str = ""
    lost_days: int = 0


class AgencyBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agency_name: str
    officer_name: str = ""
    report_number: str = ""
    case_status: str = ""
    contact_info: str = ""
    notes: str = ""


class TaskBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    description: str = ""
    assigned_to_name: str = ""
    assigned_to_role: str = ""
    due_at: str = ""


class TaskPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patch: Dict[str, Any] = Field(default_factory=dict)


def register_workspace_routes(api_router: APIRouter, db, *, require_actor) -> None:

    # ── Communications ────────────────────────────────────────────────
    @api_router.post("/incident-cases/{case_id}/communications")
    async def add_comm(case_id: str, body: CommBody = Body(...), actor=Depends(require_actor)):
        try:
            return await ws.add_communication(
                db, case_id=case_id, actor=actor, kind=body.kind,
                subject=body.subject, body=body.body,
                contact_name=body.contact_name, contact_role=body.contact_role,
                contact_org=body.contact_org,
                attachment_evidence_ids=body.attachment_evidence_ids,
            )
        except Exception as e:
            raise _handle(e)

    @api_router.get("/incident-cases/{case_id}/communications")
    async def list_comms(case_id: str, actor=Depends(require_actor)):
        return await ws.list_communications(db, case_id=case_id)

    # ── Witnesses ─────────────────────────────────────────────────────
    @api_router.post("/incident-cases/{case_id}/witnesses")
    async def add_wit(case_id: str, body: WitnessBody = Body(...), actor=Depends(require_actor)):
        try:
            return await ws.add_witness(
                db, case_id=case_id, actor=actor, kind=body.kind, name=body.name,
                contact=body.contact, company=body.company, status=body.status,
                statement=body.statement, interview_at=body.interview_at,
                credibility_notes=body.credibility_notes,
            )
        except Exception as e:
            raise _handle(e)

    @api_router.patch("/incident-cases/{case_id}/witnesses/{witness_id}")
    async def upd_wit(case_id: str, witness_id: str, body: WitnessPatch = Body(...),
                      actor=Depends(require_actor)):
        try:
            return await ws.update_witness(db, witness_id=witness_id, actor=actor, patch=body.patch)
        except Exception as e:
            raise _handle(e)

    @api_router.get("/incident-cases/{case_id}/witnesses")
    async def list_wits(case_id: str, actor=Depends(require_actor)):
        return await ws.list_witnesses(db, case_id=case_id)

    # ── Medical ───────────────────────────────────────────────────────
    @api_router.post("/incident-cases/{case_id}/medical")
    async def add_med(case_id: str, body: MedicalBody = Body(...), actor=Depends(require_actor)):
        try:
            return await ws.add_medical_entry(
                db, case_id=case_id, actor=actor, kind=body.kind,
                subject_name=body.subject_name, provider=body.provider,
                notes=body.notes, restriction_end=body.restriction_end,
                lost_days=body.lost_days,
            )
        except Exception as e:
            raise _handle(e)

    @api_router.get("/incident-cases/{case_id}/medical")
    async def list_med(case_id: str, actor=Depends(require_actor)):
        return await ws.list_medical(db, case_id=case_id)

    # ── Agency ────────────────────────────────────────────────────────
    @api_router.post("/incident-cases/{case_id}/agency-contacts")
    async def add_agency(case_id: str, body: AgencyBody = Body(...), actor=Depends(require_actor)):
        try:
            return await ws.add_agency_contact(
                db, case_id=case_id, actor=actor, agency_name=body.agency_name,
                officer_name=body.officer_name, report_number=body.report_number,
                case_status=body.case_status, contact_info=body.contact_info,
                notes=body.notes,
            )
        except Exception as e:
            raise _handle(e)

    @api_router.get("/incident-cases/{case_id}/agency-contacts")
    async def list_agency(case_id: str, actor=Depends(require_actor)):
        return await ws.list_agency(db, case_id=case_id)

    # ── Tasks ─────────────────────────────────────────────────────────
    @api_router.post("/incident-cases/{case_id}/tasks")
    async def add_task_route(case_id: str, body: TaskBody = Body(...), actor=Depends(require_actor)):
        try:
            return await ws.add_task(
                db, case_id=case_id, actor=actor, title=body.title,
                description=body.description,
                assigned_to_name=body.assigned_to_name,
                assigned_to_role=body.assigned_to_role, due_at=body.due_at,
            )
        except Exception as e:
            raise _handle(e)

    @api_router.patch("/incident-cases/{case_id}/tasks/{task_id}")
    async def upd_task(case_id: str, task_id: str, body: TaskPatch = Body(...),
                       actor=Depends(require_actor)):
        try:
            return await ws.update_task(db, task_id=task_id, actor=actor, patch=body.patch)
        except Exception as e:
            raise _handle(e)

    @api_router.get("/incident-cases/{case_id}/tasks")
    async def list_task_route(case_id: str, actor=Depends(require_actor)):
        return await ws.list_tasks(db, case_id=case_id)

    # ── Case Health + Executive Snapshot ──────────────────────────────
    @api_router.get("/incident-cases/{case_id}/health")
    async def health(case_id: str, actor=Depends(require_actor)):
        case = await case_service.get_case(db, case_id)
        if not case:
            raise _err(404, "not_found")
        return await ws.compute_case_health(db, case_id=case_id, case_doc=case)

    @api_router.get("/incident-cases/{case_id}/executive-snapshot")
    async def exec_snap(case_id: str, actor=Depends(require_actor)):
        case = await case_service.get_case(db, case_id)
        if not case:
            raise _err(404, "not_found")
        return await ws.compute_executive_snapshot(db, case_id=case_id, case_doc=case)


__all__ = ["register_workspace_routes"]

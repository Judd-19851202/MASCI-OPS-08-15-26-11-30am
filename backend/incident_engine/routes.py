"""Track 19.16 · Phase A · INCIDENT INTELLIGENCE ENGINE — HTTP ROUTES.

Namespace: ``/api/incident-cases/*``, ``/api/corrective-actions/*``.
The LEGACY ``/api/incidents/*`` surface is UNTOUCHED.

Wire from server.py via ``register_incident_engine_routes``.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from . import case_service, corrective_actions as ca_engine, evidence as ev_engine
from .events import list_events
from .legacy_adapter import find_legacy, list_legacy, project_legacy
from .permissions import capabilities_for, normalize_role
from .state_machine import legal_next_states
from .vocabulary import build_vocabulary


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class CreateCaseBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field_block: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: str = ""


class PatchFieldBlockBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patch: Dict[str, Any] = Field(default_factory=dict)


class PatchSafetyBlockBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patch: Dict[str, Any] = Field(default_factory=dict)


class TransitionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    to_state: str
    reason: str = ""


class ArchiveBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = ""


class EvidenceBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence_type: str
    label: str = ""
    description: str = ""
    storage_key: str = ""
    external_url: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WithdrawEvidenceBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str


class CrossLinkBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str
    target_id: str
    target_label: str = ""


class CreateActionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    consumer_kind: str = "incident_case"
    consumer_id: str
    action_class: str
    title: str
    description: str = ""
    assigned_to_name: str = ""
    assigned_to_role: str = ""
    due_at: str = ""


class VerifyActionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    verification_notes: str = ""


class CancelActionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str


class ExecReviewBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notes: str = ""


# ---------------------------------------------------------------------------
# Error helpers
# ---------------------------------------------------------------------------
def _err(status: int, code: str, detail: str = "") -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "detail": detail})


def _handle(exc: Exception) -> HTTPException:
    msg = str(exc)
    if isinstance(exc, PermissionError):
        if msg == "field_block_immutable":
            return _err(409, "field_block_immutable")
        if msg in (
            "illegal_transition", "unknown_transition",
            "role_not_authorized", "reason_required",
        ):
            status = 403 if msg == "role_not_authorized" else 422
            return _err(status, msg)
        return _err(403, "forbidden", msg)
    if isinstance(exc, LookupError):
        return _err(404, "not_found", msg)
    if isinstance(exc, ValueError):
        return _err(422, "invalid", msg)
    return _err(500, "internal_error", msg)


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------
def register_incident_engine_routes(
    api_router: APIRouter, db, *, require_actor, require_field_actor=None,
) -> None:
    """Attach all Phase A routes.

    ``require_actor`` is a FastAPI dependency returning the caller
    (Safety / Admin / PM read gate is fine — role gates inside the
    service layer enforce write authority per capability).
    """

    # ── VOCABULARY ──────────────────────────────────────────────
    @api_router.get("/incident-cases/vocabulary")
    async def vocabulary(actor=Depends(require_actor)) -> Dict[str, Any]:
        v = build_vocabulary()
        role = normalize_role(actor)
        v["actor_role"] = role
        v["actor_capabilities"] = list(capabilities_for(role))
        return v

    # ── CASE CRUD ───────────────────────────────────────────────
    @api_router.post("/incident-cases")
    async def create_case_route(
        body: CreateCaseBody = Body(...),
        actor=Depends(require_actor),
    ) -> Dict[str, Any]:
        try:
            return await case_service.create_case(
                db, actor=actor,
                field_block=body.field_block,
                tenant_id=body.tenant_id,
            )
        except Exception as e:
            raise _handle(e)

    @api_router.get("/incident-cases")
    async def list_cases_route(
        state: Optional[str] = Query(default=None),
        incident_type: Optional[str] = Query(default=None),
        query: Optional[str] = Query(default=None),
        limit: int = Query(default=100, ge=1, le=500),
        include_legacy: bool = Query(default=False),
        include_archived: bool = Query(default=False),
        actor=Depends(require_actor),
    ) -> Dict[str, Any]:
        try:
            cases = await case_service.list_cases(
                db, actor=actor, state=state,
                incident_type=incident_type, query=query,
                include_archived=include_archived, limit=limit,
            )
        except Exception as e:
            raise _handle(e)
        legacy: List[Dict[str, Any]] = []
        if include_legacy:
            legacy = await list_legacy(db, limit=limit)
        return {"cases": cases, "legacy_cases": legacy}

    @api_router.get("/incident-cases/{case_id}")
    async def get_case_route(
        case_id: str,
        actor=Depends(require_actor),
    ) -> Dict[str, Any]:
        doc = await case_service.get_case(db, case_id)
        if not doc:
            # Fall through to legacy read-through.
            legacy = await find_legacy(db, case_id)
            if legacy:
                return project_legacy(legacy)
            raise _err(404, "not_found")
        # Enrich with legal next states for the requester.
        doc["legal_next_states"] = list(legal_next_states(doc.get("state") or ""))
        return doc

    @api_router.patch("/incident-cases/{case_id}/field-block")
    async def patch_field_block_route(
        case_id: str,
        body: PatchFieldBlockBody = Body(...),
        actor=Depends(require_actor),
    ) -> Dict[str, Any]:
        try:
            return await case_service.update_field_block(
                db, case_id=case_id, actor=actor, patch=body.patch,
            )
        except Exception as e:
            raise _handle(e)

    @api_router.patch("/incident-cases/{case_id}/safety-block")
    async def patch_safety_block_route(
        case_id: str,
        body: PatchSafetyBlockBody = Body(...),
        actor=Depends(require_actor),
    ) -> Dict[str, Any]:
        try:
            return await case_service.update_safety_block(
                db, case_id=case_id, actor=actor, patch=body.patch,
            )
        except Exception as e:
            raise _handle(e)

    # ── TRANSITIONS ─────────────────────────────────────────────
    @api_router.post("/incident-cases/{case_id}/transitions")
    async def transition_route(
        case_id: str,
        body: TransitionBody = Body(...),
        actor=Depends(require_actor),
    ) -> Dict[str, Any]:
        try:
            return await case_service.transition_case(
                db, case_id=case_id,
                to_state=body.to_state, actor=actor, reason=body.reason,
            )
        except Exception as e:
            raise _handle(e)

    @api_router.post("/incident-cases/{case_id}/archive")
    async def archive_case_route(
        case_id: str,
        body: ArchiveBody = Body(...),
        actor=Depends(require_actor),
    ) -> Dict[str, Any]:
        try:
            return await case_service.archive_case(
                db,
                case_id=case_id,
                actor=actor,
                reason=body.reason,
            )
        except Exception as e:
            raise _handle(e)

    # ── TIMELINE / AUDIT ────────────────────────────────────────
    @api_router.get("/incident-cases/{case_id}/timeline")
    async def timeline_route(
        case_id: str,
        limit: int = Query(default=500, ge=1, le=2000),
        actor=Depends(require_actor),
    ) -> List[Dict[str, Any]]:
        return await list_events(db, case_id=case_id, limit=limit)

    @api_router.get("/incident-cases/{case_id}/audit")
    async def audit_route(
        case_id: str,
        actor=Depends(require_actor),
    ) -> List[Dict[str, Any]]:
        # Audit is a filtered view of the timeline (state / recordability
        # / reopen / close events).
        return await list_events(
            db, case_id=case_id, limit=2000,
            event_types=[
                "case.state_changed", "case.archived", "case.reopened", "case.closed",
                "recordability.changed", "root_cause.updated",
                "executive_review.recorded",
                "corrective_action.assigned", "corrective_action.verified",
                "corrective_action.canceled",
                "evidence.added", "evidence.withdrawn",
            ],
        )

    # ── EVIDENCE ────────────────────────────────────────────────
    @api_router.post("/incident-cases/{case_id}/evidence")
    async def add_evidence_route(
        case_id: str,
        body: EvidenceBody = Body(...),
        actor=Depends(require_actor),
    ) -> Dict[str, Any]:
        try:
            ev = await ev_engine.add_evidence(
                db, case_id=case_id,
                evidence_type=body.evidence_type,
                actor=actor,
                label=body.label,
                description=body.description,
                storage_key=body.storage_key,
                external_url=body.external_url,
                metadata=body.metadata,
            )
        except Exception as e:
            raise _handle(e)
        await case_service.refresh_counters(db, case_id=case_id)
        return ev

    @api_router.get("/incident-cases/{case_id}/evidence")
    async def list_evidence_route(
        case_id: str,
        include_withdrawn: bool = Query(default=True),
        actor=Depends(require_actor),
    ) -> List[Dict[str, Any]]:
        return await ev_engine.list_evidence(
            db, case_id=case_id, include_withdrawn=include_withdrawn,
        )

    @api_router.post("/incident-cases/{case_id}/evidence/{evidence_id}/withdraw")
    async def withdraw_evidence_route(
        case_id: str,
        evidence_id: str,
        body: WithdrawEvidenceBody = Body(...),
        actor=Depends(require_actor),
    ) -> Dict[str, Any]:
        try:
            out = await ev_engine.withdraw_evidence(
                db, evidence_id=evidence_id, actor=actor, reason=body.reason,
            )
        except Exception as e:
            raise _handle(e)
        await case_service.refresh_counters(db, case_id=case_id)
        return out

    # ── CROSS-LINKS ─────────────────────────────────────────────
    @api_router.post("/incident-cases/{case_id}/cross-links")
    async def add_cross_link_route(
        case_id: str,
        body: CrossLinkBody = Body(...),
        actor=Depends(require_actor),
    ) -> Dict[str, Any]:
        try:
            return await case_service.add_cross_link(
                db, case_id=case_id, actor=actor,
                kind=body.kind, target_id=body.target_id,
                target_label=body.target_label,
            )
        except Exception as e:
            raise _handle(e)

    @api_router.delete("/incident-cases/{case_id}/cross-links/{link_id}")
    async def remove_cross_link_route(
        case_id: str,
        link_id: str,
        actor=Depends(require_actor),
    ) -> Dict[str, str]:
        try:
            await case_service.remove_cross_link(
                db, case_id=case_id, actor=actor, link_id=link_id,
            )
        except Exception as e:
            raise _handle(e)
        return {"ok": "true"}

    # ── EXECUTIVE REVIEW ────────────────────────────────────────
    @api_router.post("/incident-cases/{case_id}/executive-review")
    async def executive_review_route(
        case_id: str,
        body: ExecReviewBody = Body(...),
        actor=Depends(require_actor),
    ) -> Dict[str, Any]:
        try:
            return await case_service.record_executive_review(
                db, case_id=case_id, actor=actor, notes=body.notes,
            )
        except Exception as e:
            raise _handle(e)

    # ── CORRECTIVE ACTIONS (platform primitive) ─────────────────
    @api_router.post("/corrective-actions")
    async def create_action_route(
        body: CreateActionBody = Body(...),
        actor=Depends(require_actor),
    ) -> Dict[str, Any]:
        try:
            out = await ca_engine.create_action(
                db,
                consumer_kind=body.consumer_kind,
                consumer_id=body.consumer_id,
                action_class=body.action_class,
                title=body.title,
                description=body.description,
                assigned_to_name=body.assigned_to_name,
                assigned_to_role=body.assigned_to_role,
                due_at=body.due_at,
                actor=actor,
            )
        except Exception as e:
            raise _handle(e)
        if body.consumer_kind == "incident_case":
            await case_service.refresh_counters(db, case_id=body.consumer_id)
        return out

    @api_router.get("/corrective-actions")
    async def list_actions_route(
        consumer_kind: Optional[str] = Query(default=None),
        consumer_id: Optional[str] = Query(default=None),
        state: Optional[str] = Query(default=None),
        actor=Depends(require_actor),
    ) -> List[Dict[str, Any]]:
        return await ca_engine.list_actions(
            db, consumer_kind=consumer_kind,
            consumer_id=consumer_id, state=state,
        )

    @api_router.post("/corrective-actions/{action_id}/verify")
    async def verify_action_route(
        action_id: str,
        body: VerifyActionBody = Body(...),
        actor=Depends(require_actor),
    ) -> Dict[str, Any]:
        try:
            out = await ca_engine.verify_action(
                db, action_id=action_id, actor=actor,
                verification_notes=body.verification_notes,
            )
        except Exception as e:
            raise _handle(e)
        if out.get("consumer_kind") == "incident_case":
            await case_service.refresh_counters(db, case_id=out["consumer_id"])
        return out

    @api_router.post("/corrective-actions/{action_id}/cancel")
    async def cancel_action_route(
        action_id: str,
        body: CancelActionBody = Body(...),
        actor=Depends(require_actor),
    ) -> Dict[str, Any]:
        try:
            out = await ca_engine.cancel_action(
                db, action_id=action_id, actor=actor, reason=body.reason,
            )
        except Exception as e:
            raise _handle(e)
        if out.get("consumer_kind") == "incident_case":
            await case_service.refresh_counters(db, case_id=out["consumer_id"])
        return out

    # ── LEGACY READ-THROUGH ─────────────────────────────────────
    @api_router.get("/incident-cases/legacy/{incident_id}")
    async def legacy_read_route(
        incident_id: str,
        actor=Depends(require_actor),
    ) -> Dict[str, Any]:
        legacy = await find_legacy(db, incident_id)
        if not legacy:
            raise _err(404, "not_found")
        return project_legacy(legacy)


__all__ = ["register_incident_engine_routes"]

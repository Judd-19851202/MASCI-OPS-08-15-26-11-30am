"""OMEGA · iter453 · OC-003 QA/QC Deficiency Follow-Up lifecycle routes.

Constitutional Build Package (Phase 3 · 2026-06-02) implementation.

Additive endpoints — existing /api/qaqc-inspections CRUD is untouched.

    POST /api/qaqc-inspections/{id}/transition
        body: { to_state, reason?, evidence? }
    GET  /api/qaqc-inspections/{id}/state-events
    GET  /api/qaqc-inspections/{id}/lifecycle

Closure-action contract (Amendment 001 REPLACE-5):
    CLOSED only when ONE of:
      a) re_inspection_passed + re_inspection_record_id
      b) corrective_action_completed + corrective_action_notes >= 20
      c) exception_approved + reason + dual pm/safety sign-off

Ownership inference (Ownership Doctrine O-1 textbook):
    OPEN                  -> Inspector (creator · S1)
    DEFICIENCY_RAISED     -> PM (project owner · S2)
    IN_REMEDIATION        -> PM (continues; sub is counterparty per O-10)
    PENDING_RE_INSPECTION -> Inspector role-gate (S3)
    CLOSED                -> (no owner)

Wired from server.py via ``register_qaqc_lifecycle_routes``.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from lib.workflow_state_events import (
    list_state_events,
    write_state_event,
)
from lib.workflow_state_machine import (
    QAQC_DEFAULT_STATE,
    QAQC_STATES,
    QAQC_TRANSITIONS,
    coerce_qaqc_state,
    normalize_actor_role,
    validate_qaqc_transition,
)

WORKFLOW = "qaqc_inspection"


class TransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    to_state: str
    reason: Optional[str] = ""
    evidence: Dict[str, Any] = Field(default_factory=dict)


def _close_field_for_state(state: str) -> Optional[str]:
    """Map non-OPEN states to a per-row timestamp column so downstream
    projection (Action Console row materialization) doesn't need to
    inspect the audit collection."""
    return {
        "DEFICIENCY_RAISED":     "lifecycle_deficiency_raised_at",
        "IN_REMEDIATION":        "lifecycle_in_remediation_at",
        "PENDING_RE_INSPECTION": "lifecycle_pending_re_inspection_at",
        "CLOSED":                "lifecycle_closed_at",
    }.get(state)


def _infer_owner_role(state: str) -> str:
    """Ownership Doctrine inference (O-1 + O-3): derive the role gate
    of the *current* state. Returns the role token used by RBAC. This
    is informational metadata for the lifecycle response — the actual
    enforcement happens in ``validate_qaqc_transition``."""
    return {
        "OPEN":                  "inspector",
        "DEFICIENCY_RAISED":     "pm",
        "IN_REMEDIATION":        "pm",
        "PENDING_RE_INSPECTION": "inspector",
        "CLOSED":                "",
    }.get(state, "")


def register_qaqc_lifecycle_routes(
    api_router: APIRouter,
    db,
    *,
    require_qaqc_actor,
):
    """Attach the iter453 OC-003 transition + audit endpoints."""

    @api_router.post("/qaqc-inspections/{inspection_id}/transition")
    async def transition_qaqc(
        inspection_id: str,
        request: Request,
        payload: TransitionRequest = Body(...),
        actor=Depends(require_qaqc_actor),
    ):
        doc = await db.qaqc_inspections.find_one({"id": inspection_id}, {"_id": 0})
        if not doc:
            doc = await db.qaqc_inspections.find_one({"doc_id": inspection_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="QA/QC inspection not found")

        canonical_id = doc.get("id")
        doc_id = doc.get("doc_id") or ""
        from_state = coerce_qaqc_state(doc.get("lifecycle_state"))
        to_state = (payload.to_state or "").strip().upper()
        reason = (payload.reason or "").strip()
        evidence = dict(payload.evidence or {})

        ok, err = validate_qaqc_transition(
            from_state=from_state,
            to_state=to_state,
            actor=actor,
            reason=reason,
            evidence=evidence,
        )
        if not ok:
            if err == "role_not_authorized":
                raise HTTPException(status_code=403, detail={"code": err})
            raise HTTPException(status_code=422, detail={
                "code": err,
                "from_state": from_state,
                "to_state": to_state,
            })

        now = datetime.now(timezone.utc).isoformat()
        update_set: Dict[str, Any] = {
            "lifecycle_state": to_state,
            "lifecycle_updated_at": now,
            "current_owner_role": _infer_owner_role(to_state),
        }
        ts_field = _close_field_for_state(to_state)
        if ts_field:
            update_set[ts_field] = now
        if from_state == "CLOSED" and to_state == "DEFICIENCY_RAISED":
            update_set["lifecycle_closed_at"] = None

        await db.qaqc_inspections.update_one(
            {"id": canonical_id},
            {"$set": update_set},
        )

        await write_state_event(
            db,
            workflow=WORKFLOW,
            record_id=canonical_id,
            record_doc_id=doc_id,
            from_state=from_state,
            to_state=to_state,
            actor=actor,
            reason=reason,
            evidence=evidence,
            request=request,
        )

        return {
            "ok": True,
            "id": canonical_id,
            "doc_id": doc_id,
            "from_state": from_state,
            "to_state": to_state,
            "current_owner_role": update_set["current_owner_role"],
            "lifecycle_updated_at": now,
        }

    @api_router.get("/qaqc-inspections/{inspection_id}/state-events")
    async def get_qaqc_state_events(
        inspection_id: str,
        actor=Depends(require_qaqc_actor),
    ) -> List[Dict[str, Any]]:
        doc = await db.qaqc_inspections.find_one({"id": inspection_id}, {"_id": 0, "id": 1})
        if not doc:
            doc = await db.qaqc_inspections.find_one(
                {"doc_id": inspection_id}, {"_id": 0, "id": 1}
            )
        if not doc:
            raise HTTPException(status_code=404, detail="QA/QC inspection not found")
        return await list_state_events(
            db, workflow=WORKFLOW, record_id=doc["id"], limit=500
        )

    @api_router.get("/qaqc-inspections/{inspection_id}/lifecycle")
    async def get_qaqc_lifecycle(
        inspection_id: str,
        actor=Depends(require_qaqc_actor),
    ) -> Dict[str, Any]:
        """Lifecycle read used by the lifecycle panel — current state +
        legal next-states for the requesting actor + inferred owner role.
        """
        doc = await db.qaqc_inspections.find_one({"id": inspection_id}, {"_id": 0})
        if not doc:
            doc = await db.qaqc_inspections.find_one({"doc_id": inspection_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="QA/QC inspection not found")

        from_state = coerce_qaqc_state(doc.get("lifecycle_state"))
        role = normalize_actor_role(actor)
        candidates = QAQC_TRANSITIONS.get(from_state, [])

        # Stub evidence so the "legal next states" computation doesn't
        # block on closure-action contract gates — the actual gates fire
        # at transition POST time with the real evidence.
        stub_evidence = {
            "re_inspection_passed": True,
            "re_inspection_record_id": "stub-for-legal-states",
            "corrective_action_completed": True,
            "corrective_action_notes": "x" * 25,
            "exception_approved": True,
            "exception_reason": "x" * 12,
            "pm_signoff_user_id": "stub-pm",
            "safety_signoff_user_id": "stub-safety",
        }
        legal_next: List[Dict[str, Any]] = []
        for nxt in candidates:
            ok, _err = validate_qaqc_transition(
                from_state=from_state,
                to_state=nxt,
                actor=actor,
                reason="x" * 6,
                evidence=stub_evidence,
            )
            legal_next.append({"to_state": nxt, "allowed_for_actor": ok})

        return {
            "workflow": WORKFLOW,
            "id": doc.get("id"),
            "doc_id": doc.get("doc_id") or "",
            "lifecycle_state": from_state,
            "lifecycle_updated_at": doc.get("lifecycle_updated_at") or "",
            "lifecycle_closed_at": doc.get("lifecycle_closed_at") or "",
            "current_owner_role": _infer_owner_role(from_state),
            "actor_role": role,
            "all_states": list(QAQC_STATES),
            "default_state": QAQC_DEFAULT_STATE,
            "legal_next_states": legal_next,
        }


__all__ = ["register_qaqc_lifecycle_routes"]

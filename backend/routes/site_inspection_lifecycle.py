"""OMEGA · iter453 · OC-004 Site Inspection Finding Follow-Up lifecycle routes.

Constitutional Build Package (Phase 3 · 2026-06-02) implementation.

Additive endpoints — existing /api/inspections CRUD is untouched.

    POST /api/inspections/{id}/transition
        body: { to_state, reason?, evidence? }
    GET  /api/inspections/{id}/state-events
    GET  /api/inspections/{id}/lifecycle

Closure-action contract (Amendment 001 REPLACE-4): same 3-path contract
as OC-003 — re-inspection OR corrective_action OR documented exception
with dual sign-off. "Acknowledge findings" ack-only closure is FORBIDDEN.

Ownership inference (Ownership Doctrine O-1):
    OPEN                  -> Site Inspector (S1)
    FINDINGS_RAISED       -> PM (S2)
    IN_REMEDIATION        -> PM (sub is counterparty metadata · O-10)
    PENDING_RE_INSPECTION -> Site Inspector role-gate (S3)
    CLOSED                -> (no owner)

Wired from server.py via ``register_site_inspection_lifecycle_routes``.
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
    SITE_INSPECTION_DEFAULT_STATE,
    SITE_INSPECTION_STATES,
    SITE_INSPECTION_TRANSITIONS,
    coerce_site_inspection_state,
    normalize_actor_role,
    validate_site_inspection_transition,
)

WORKFLOW = "site_inspection"


class TransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    to_state: str
    reason: Optional[str] = ""
    evidence: Dict[str, Any] = Field(default_factory=dict)


def _close_field_for_state(state: str) -> Optional[str]:
    return {
        "FINDINGS_RAISED":       "lifecycle_findings_raised_at",
        "IN_REMEDIATION":        "lifecycle_in_remediation_at",
        "PENDING_RE_INSPECTION": "lifecycle_pending_re_inspection_at",
        "CLOSED":                "lifecycle_closed_at",
    }.get(state)


def _infer_owner_role(state: str) -> str:
    return {
        "OPEN":                  "site_inspector",
        "FINDINGS_RAISED":       "pm",
        "IN_REMEDIATION":        "pm",
        "PENDING_RE_INSPECTION": "site_inspector",
        "CLOSED":                "",
    }.get(state, "")


def register_site_inspection_lifecycle_routes(
    api_router: APIRouter,
    db,
    *,
    require_inspection_actor,
):
    """Attach the iter453 OC-004 transition + audit endpoints."""

    @api_router.post("/inspections/{inspection_id}/transition")
    async def transition_inspection(
        inspection_id: str,
        request: Request,
        payload: TransitionRequest = Body(...),
        actor=Depends(require_inspection_actor),
    ):
        doc = await db.inspections.find_one({"id": inspection_id}, {"_id": 0})
        if not doc:
            doc = await db.inspections.find_one({"doc_id": inspection_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Site inspection not found")

        canonical_id = doc.get("id")
        doc_id = doc.get("doc_id") or ""
        from_state = coerce_site_inspection_state(doc.get("lifecycle_state"))
        to_state = (payload.to_state or "").strip().upper()
        reason = (payload.reason or "").strip()
        evidence = dict(payload.evidence or {})

        ok, err = validate_site_inspection_transition(
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
        if from_state == "CLOSED" and to_state == "FINDINGS_RAISED":
            update_set["lifecycle_closed_at"] = None

        await db.inspections.update_one(
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

    @api_router.get("/inspections/{inspection_id}/state-events")
    async def get_inspection_state_events(
        inspection_id: str,
        actor=Depends(require_inspection_actor),
    ) -> List[Dict[str, Any]]:
        doc = await db.inspections.find_one({"id": inspection_id}, {"_id": 0, "id": 1})
        if not doc:
            doc = await db.inspections.find_one(
                {"doc_id": inspection_id}, {"_id": 0, "id": 1}
            )
        if not doc:
            raise HTTPException(status_code=404, detail="Site inspection not found")
        return await list_state_events(
            db, workflow=WORKFLOW, record_id=doc["id"], limit=500
        )

    @api_router.get("/inspections/{inspection_id}/lifecycle")
    async def get_inspection_lifecycle(
        inspection_id: str,
        actor=Depends(require_inspection_actor),
    ) -> Dict[str, Any]:
        doc = await db.inspections.find_one({"id": inspection_id}, {"_id": 0})
        if not doc:
            doc = await db.inspections.find_one({"doc_id": inspection_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Site inspection not found")

        from_state = coerce_site_inspection_state(doc.get("lifecycle_state"))
        role = normalize_actor_role(actor)
        candidates = SITE_INSPECTION_TRANSITIONS.get(from_state, [])

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
            ok, _err = validate_site_inspection_transition(
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
            "all_states": list(SITE_INSPECTION_STATES),
            "default_state": SITE_INSPECTION_DEFAULT_STATE,
            "legal_next_states": legal_next,
        }


__all__ = ["register_site_inspection_lifecycle_routes"]

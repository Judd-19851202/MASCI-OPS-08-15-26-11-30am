"""OMEGA · Phase 1A · iter451 · OC-001 Incident Lifecycle routes.

Additive endpoints — existing /api/incidents CRUD is untouched.

    POST /api/incidents/{id}/transition
        body: { to_state, reason?, evidence? }
        auth: Safety (X-Safety-Token) | Admin (X-Admin-Token) | PM read-only
              for write surfaces here.  Closure role gate enforced server-side.

    GET  /api/incidents/{id}/state-events
        Returns the append-only transition history for the record.

Wired from ``server.py`` via ``register_incident_lifecycle_routes``.
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
    INCIDENT_DEFAULT_STATE,
    INCIDENT_STATES,
    coerce_incident_state,
    normalize_actor_role,
    validate_incident_transition,
)

WORKFLOW = "incident"


class TransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    to_state: str
    reason: Optional[str] = ""
    evidence: Dict[str, Any] = Field(default_factory=dict)


def _close_field_for_state(state: str) -> Optional[str]:
    """Map terminal-ish states to a per-row timestamp column. Used by
    downstream projection (Command Center / Accountability) so they
    don't need to inspect the audit collection."""
    return {
        "UNDER_INVESTIGATION":        "lifecycle_under_investigation_at",
        "CORRECTIVE_ACTION_REQUIRED": "lifecycle_capa_required_at",
        "PENDING_CLOSURE":            "lifecycle_pending_closure_at",
        "CLOSED":                     "lifecycle_closed_at",
    }.get(state)


def register_incident_lifecycle_routes(
    api_router: APIRouter,
    db,
    *,
    require_incident_actor,
):
    """Attach the iter451 transition + audit endpoints.

    ``require_incident_actor`` is a FastAPI dependency that resolves
    a Safety / Admin / PM token. The internal closure role-gate is
    enforced by :func:`validate_incident_transition`, not by this
    dependency."""

    @api_router.post("/incidents/{incident_id}/transition")
    async def transition_incident(
        incident_id: str,
        request: Request,
        payload: TransitionRequest = Body(...),
        actor=Depends(require_incident_actor),
    ):
        # 1 · Resolve doc (UUID-first, doc_id fallback — same pattern
        # as the existing DELETE endpoint).
        doc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
        if not doc:
            doc = await db.incidents.find_one({"doc_id": incident_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Incident not found")

        canonical_id = doc.get("id")
        doc_id = doc.get("doc_id") or ""
        from_state = coerce_incident_state(doc.get("lifecycle_state"))
        to_state = (payload.to_state or "").strip().upper()
        reason = (payload.reason or "").strip()
        evidence = dict(payload.evidence or {})
        osha = str(doc.get("osha_recordable") or "").strip().lower() == "yes"

        # 2 · Validate the transition.
        ok, err = validate_incident_transition(
            from_state=from_state,
            to_state=to_state,
            actor=actor,
            reason=reason,
            evidence=evidence,
            osha_recordable=osha,
        )
        if not ok:
            # 403 for role / closure-role; 422 for everything else.
            if err in ("role_not_authorized", "closure_role_not_authorized"):
                raise HTTPException(status_code=403, detail={"code": err})
            raise HTTPException(status_code=422, detail={
                "code": err,
                "from_state": from_state,
                "to_state": to_state,
            })

        # 3 · Persist the new state. Forward-only — never overwrite the
        # original incident_date / created_at; only the lifecycle columns.
        now = datetime.now(timezone.utc).isoformat()
        update_set: Dict[str, Any] = {
            "lifecycle_state": to_state,
            "lifecycle_updated_at": now,
        }
        ts_field = _close_field_for_state(to_state)
        if ts_field:
            update_set[ts_field] = now
        # On REOPEN, clear the closed timestamp so downstream projection
        # doesn't keep treating the record as terminal.
        if from_state == "CLOSED" and to_state == "UNDER_INVESTIGATION":
            update_set["lifecycle_closed_at"] = None

        await db.incidents.update_one(
            {"id": canonical_id},
            {"$set": update_set},
        )

        # 4 · Append the audit event. Best-effort.
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
            "lifecycle_updated_at": now,
        }

    @api_router.get("/incidents/{incident_id}/state-events")
    async def get_incident_state_events(
        incident_id: str,
        actor=Depends(require_incident_actor),
    ) -> List[Dict[str, Any]]:
        # Resolve UUID-or-doc_id so the audit view works from either
        # identifier (mirrors DELETE behaviour).
        doc = await db.incidents.find_one({"id": incident_id}, {"_id": 0, "id": 1})
        if not doc:
            doc = await db.incidents.find_one(
                {"doc_id": incident_id}, {"_id": 0, "id": 1}
            )
        if not doc:
            raise HTTPException(status_code=404, detail="Incident not found")
        return await list_state_events(
            db, workflow=WORKFLOW, record_id=doc["id"], limit=500
        )

    @api_router.get("/incidents/{incident_id}/lifecycle")
    async def get_incident_lifecycle(
        incident_id: str,
        actor=Depends(require_incident_actor),
    ) -> Dict[str, Any]:
        """Convenience read used by the lifecycle panel — current state +
        legal next-states for the requesting actor. Avoids a frontend
        round-trip through the static state map.
        """
        doc = await db.incidents.find_one({"id": incident_id}, {"_id": 0})
        if not doc:
            doc = await db.incidents.find_one({"doc_id": incident_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Incident not found")

        from_state = coerce_incident_state(doc.get("lifecycle_state"))
        role = normalize_actor_role(actor)
        osha = str(doc.get("osha_recordable") or "").strip().lower() == "yes"

        # Compute legal next-states for THIS actor.
        from lib.workflow_state_machine import INCIDENT_TRANSITIONS
        candidates = INCIDENT_TRANSITIONS.get(from_state, [])
        legal_next: List[Dict[str, Any]] = []
        for nxt in candidates:
            ok, _err = validate_incident_transition(
                from_state=from_state,
                to_state=nxt,
                actor=actor,
                reason="x" * 6,  # placeholder so reason gate doesn't kill
                evidence={
                    "investigation_complete": True,
                    "capa_complete": True,
                    "safety_review_complete": True,
                    "osha_recordable_ack": True,
                },
                osha_recordable=osha,
            )
            legal_next.append({
                "to_state": nxt,
                "allowed_for_actor": ok,
            })

        return {
            "workflow": WORKFLOW,
            "id": doc.get("id"),
            "doc_id": doc.get("doc_id") or "",
            "lifecycle_state": from_state,
            "lifecycle_updated_at": doc.get("lifecycle_updated_at") or "",
            "lifecycle_closed_at": doc.get("lifecycle_closed_at") or "",
            "osha_recordable": osha,
            "actor_role": role,
            "all_states": list(INCIDENT_STATES),
            "default_state": INCIDENT_DEFAULT_STATE,
            "legal_next_states": legal_next,
        }


__all__ = ["register_incident_lifecycle_routes"]

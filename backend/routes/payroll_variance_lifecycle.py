"""OMEGA · Phase 1A · iter452 · OC-007 Payroll Variance Finalization routes.

Additive endpoints — existing /api/hr/payroll-variance CRUD untouched.

    POST /api/hr/payroll-variance/batches/{id}/transition
        body: { to_state, reason?, evidence? }
        auth: HR (X-HR-Token) | Admin (X-Admin-Token)
              Role gate enforced server-side by the state machine.

    GET  /api/hr/payroll-variance/batches/{id}/state-events
    GET  /api/hr/payroll-variance/batches/{id}/lifecycle

The Payroll Variance lifecycle is explicit per the iter452 directive:
NO AUTO FINALIZE. Finalization requires Review → Approve → Finalize
with three attestation flags, including a check that every flagged
variance row has a decision recorded.
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
from lib.trust_spine import emit_workflow_stage
from lib.workflow_state_machine import (
    PAYROLL_VARIANCE_DEFAULT_STATE,
    PAYROLL_VARIANCE_STATES,
    PAYROLL_VARIANCE_TRANSITIONS,
    coerce_payroll_variance_state,
    normalize_actor_role,
    validate_payroll_variance_transition,
)

WORKFLOW = "payroll_variance"


class PVTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    to_state: str
    reason: Optional[str] = ""
    evidence: Dict[str, Any] = Field(default_factory=dict)


def _ts_field(state: str) -> Optional[str]:
    return {
        "UNDER_REVIEW": "lifecycle_under_review_at",
        "APPROVED":     "lifecycle_approved_at",
        "FINALIZED":    "lifecycle_finalized_at",
    }.get(state)


async def _all_flagged_rows_decided(doc: Dict[str, Any]) -> bool:
    """Server-side safety net for the `variance_decisions_complete`
    attestation — count flagged rows and confirm each carries a
    non-empty `decision` (approve | dispute).
    """
    rows = doc.get("rows") or []
    flagged_indices = [
        i for i, r in enumerate(rows)
        if r.get("flag") in ("flag", "missing_from_payroll")
    ]
    if not flagged_indices:
        return True  # nothing flagged → nothing to decide
    for i in flagged_indices:
        d = (rows[i].get("decision") or "").lower()
        if d not in ("approve", "dispute"):
            return False
    return True


def register_payroll_variance_lifecycle_routes(
    api_router: APIRouter,
    db,
    *,
    require_pv_actor,
):
    @api_router.post("/hr/payroll-variance/batches/{batch_id}/transition")
    async def transition_payroll_variance(
        batch_id: str,
        request: Request,
        payload: PVTransitionRequest = Body(...),
        actor=Depends(require_pv_actor),
    ):
        doc = await db.payroll_variance_batches.find_one({"id": batch_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Payroll variance batch not found")

        canonical_id = doc.get("id")
        from_state = coerce_payroll_variance_state(doc.get("lifecycle_state"))
        to_state = (payload.to_state or "").strip().upper()
        reason = (payload.reason or "").strip()
        evidence = dict(payload.evidence or {})

        ok, err = validate_payroll_variance_transition(
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

        # Server-side safety net for FINALIZE — actually verify decisions.
        if to_state == "FINALIZED":
            if not await _all_flagged_rows_decided(doc):
                raise HTTPException(status_code=422, detail={
                    "code": "finalize_attestation_missing:variance_decisions_complete",
                    "from_state": from_state,
                    "to_state": to_state,
                    "message": "One or more flagged variance rows have no decision recorded.",
                })

        now = datetime.now(timezone.utc).isoformat()
        update_set: Dict[str, Any] = {
            "lifecycle_state": to_state,
            "lifecycle_updated_at": now,
        }
        tsf = _ts_field(to_state)
        if tsf:
            update_set[tsf] = now
        # Reopen / back-step → clear finalized timestamp.
        if to_state == "UNDER_REVIEW" and from_state in ("APPROVED", "FINALIZED"):
            update_set["lifecycle_finalized_at"] = None

        await db.payroll_variance_batches.update_one(
            {"id": canonical_id},
            {"$set": update_set},
        )

        await write_state_event(
            db,
            workflow=WORKFLOW,
            record_id=canonical_id,
            record_doc_id=doc.get("week_ending") or "",  # use week_ending as human ref
            from_state=from_state,
            to_state=to_state,
            actor=actor,
            reason=reason,
            evidence=evidence,
            request=request,
        )
        try:
            spine_record = {
                "id": canonical_id,
                "doc_id": canonical_id,
                "project_number": "",
            }
            await emit_workflow_stage(
                db,
                workflow="oppc-payroll-reconciliation",
                stage="audit_written",
                record=spine_record,
                module="routes/payroll_variance_lifecycle.py:transition_payroll_variance",
                event_name="payroll_variance_detected",
            )
            if to_state == "FINALIZED":
                await emit_workflow_stage(
                    db,
                    workflow="oppc-payroll-reconciliation",
                    stage="completed",
                    record=spine_record,
                    module="routes/payroll_variance_lifecycle.py:transition_payroll_variance",
                    event_name="completed",
                )
        except Exception:
            pass

        return {
            "ok": True,
            "id": canonical_id,
            "week_ending": doc.get("week_ending") or "",
            "from_state": from_state,
            "to_state": to_state,
            "lifecycle_updated_at": now,
        }

    @api_router.get("/hr/payroll-variance/batches/{batch_id}/state-events")
    async def get_pv_state_events(
        batch_id: str,
        actor=Depends(require_pv_actor),
    ) -> List[Dict[str, Any]]:
        doc = await db.payroll_variance_batches.find_one(
            {"id": batch_id}, {"_id": 0, "id": 1}
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Batch not found")
        return await list_state_events(
            db, workflow=WORKFLOW, record_id=doc["id"], limit=500
        )

    @api_router.get("/hr/payroll-variance/batches/{batch_id}/lifecycle")
    async def get_pv_lifecycle(
        batch_id: str,
        actor=Depends(require_pv_actor),
    ) -> Dict[str, Any]:
        doc = await db.payroll_variance_batches.find_one(
            {"id": batch_id}, {"_id": 0}
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Batch not found")

        from_state = coerce_payroll_variance_state(doc.get("lifecycle_state"))
        role = normalize_actor_role(actor)
        flagged_decided = await _all_flagged_rows_decided(doc)

        legal_next: List[Dict[str, Any]] = []
        for nxt in PAYROLL_VARIANCE_TRANSITIONS.get(from_state, []):
            ok, _err = validate_payroll_variance_transition(
                from_state=from_state,
                to_state=nxt,
                actor=actor,
                reason="x" * 6,
                evidence={
                    "review_complete": True,
                    "approval_complete": True,
                    "variance_decisions_complete": True,
                },
            )
            # FINALIZE additionally needs flagged_decided=True at runtime.
            if nxt == "FINALIZED" and not flagged_decided:
                ok = False
            legal_next.append({"to_state": nxt, "allowed_for_actor": ok})

        return {
            "workflow": WORKFLOW,
            "id": doc.get("id"),
            "week_ending": doc.get("week_ending") or "",
            "lifecycle_state": from_state,
            "lifecycle_updated_at": doc.get("lifecycle_updated_at") or "",
            "lifecycle_finalized_at": doc.get("lifecycle_finalized_at") or "",
            "actor_role": role,
            "flagged_rows": doc.get("flagged_rows", 0) or 0,
            "all_flagged_decided": flagged_decided,
            "all_states": list(PAYROLL_VARIANCE_STATES),
            "default_state": PAYROLL_VARIANCE_DEFAULT_STATE,
            "legal_next_states": legal_next,
        }


__all__ = ["register_payroll_variance_lifecycle_routes"]

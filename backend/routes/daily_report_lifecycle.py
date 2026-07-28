"""OMEGA · Phase 1A · iter452 · OC-002 Daily Report Office Review routes.

Additive endpoints — existing /api/daily-reports CRUD is untouched.

    POST /api/daily-reports/{id}/transition
        body: { to_state, reason?, evidence? }
        auth: PM (X-PM-Token) | Admin (X-Admin-Token) | Safety (read gate)
              Role gate enforced by the state machine itself.

    GET  /api/daily-reports/{id}/state-events
    GET  /api/daily-reports/{id}/lifecycle

Notifications fan-out: when a Daily Report enters PENDING_REVIEW the
existing event_fanout helper emits a bell to PM + Safety + Admin so
operators see new review-queue volume without polling.
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
from services.operations_control.control_plane import ingest_daily_report_pending_review
from lib.workflow_state_machine import (
    DAILY_REPORT_DEFAULT_STATE,
    DAILY_REPORT_STATES,
    DAILY_REPORT_TRANSITIONS,
    coerce_daily_report_state,
    normalize_actor_role,
    validate_daily_report_transition,
)

WORKFLOW = "daily_report"


class DRTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    to_state: str
    reason: Optional[str] = ""
    evidence: Dict[str, Any] = Field(default_factory=dict)


def _ts_field(state: str) -> Optional[str]:
    return {
        "PENDING_REVIEW": "lifecycle_pending_review_at",
        "REVIEWED":       "lifecycle_reviewed_at",
        "CLOSED":         "lifecycle_closed_at",
    }.get(state)


def register_daily_report_lifecycle_routes(
    api_router: APIRouter,
    db,
    *,
    require_dr_actor,
):
    @api_router.post("/daily-reports/{report_id}/transition")
    async def transition_daily_report(
        report_id: str,
        request: Request,
        payload: DRTransitionRequest = Body(...),
        actor=Depends(require_dr_actor),
    ):
        doc = await db.daily_reports.find_one({"id": report_id}, {"_id": 0})
        if not doc:
            doc = await db.daily_reports.find_one({"doc_id": report_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Daily Report not found")

        canonical_id = doc.get("id")
        doc_id = doc.get("doc_id") or ""
        from_state = coerce_daily_report_state(doc.get("lifecycle_state"))
        to_state = (payload.to_state or "").strip().upper()
        reason = (payload.reason or "").strip()
        evidence = dict(payload.evidence or {})

        ok, err = validate_daily_report_transition(
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
        }
        tsf = _ts_field(to_state)
        if tsf:
            update_set[tsf] = now
        # On PENDING_REVIEW → OPEN, clear reviewed_at to keep the row honest.
        if from_state == "PENDING_REVIEW" and to_state == "OPEN":
            update_set["lifecycle_reviewed_at"] = None
        # On REOPEN, clear closed_at.
        if from_state == "CLOSED" and to_state == "PENDING_REVIEW":
            update_set["lifecycle_closed_at"] = None

        await db.daily_reports.update_one(
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

        # Phase 1A notification fan-out — only on PENDING_REVIEW so PMs +
        # Safety reviewers see the queue grow. Fire-and-forget.
        if to_state == "PENDING_REVIEW":
            try:
                control_plane_result = await ingest_daily_report_pending_review(
                    db,
                    report={
                        **doc,
                        "lifecycle_state": to_state,
                    },
                    actor_label=(actor.get("name") if isinstance(actor, dict) else "Office") or "Office",
                )
                communication_ids = [
                    row.get("id") for row in (control_plane_result.get("communications") or []) if row.get("id")
                ]
                await db.daily_reports.update_one(
                    {"id": canonical_id},
                    {
                        "$set": {
                            "operations_control_plane.review_queue_event_id": control_plane_result.get("event", {}).get("id"),
                            "operations_control_plane.review_queue_communication_ids": communication_ids,
                            "operations_control_plane.review_queue_last_processed_at": datetime.now(timezone.utc).isoformat(),
                        }
                    },
                )
            except Exception:
                pass

        # iter452.5 Tier 1 · Field Submitter Identity kickback dispatch.
        # On PENDING_REVIEW → OPEN ("kicked back to field") send the
        # submitter a signed /revise/{token} email and emit the full
        # delivery-evidence chain so Phase 1B can prove the loop closed.
        if from_state == "PENDING_REVIEW" and to_state == "OPEN":
            try:
                from lib.field_submitter_identity import (  # noqa: PLC0415
                    get_binding, notify_field_submitter,
                )
                from lib.fsi_email_sender import fsi_send_email  # noqa: PLC0415
                binding = await get_binding(
                    db, workflow=WORKFLOW, record_id=canonical_id,
                )
                if binding:
                    import os as _os  # noqa: PLC0415
                    base = (_os.environ.get("PUBLIC_BASE_URL")
                            or _os.environ.get("FRONTEND_BASE_URL") or "").strip()
                    project_label = doc.get("project_name") or doc.get("project_number") or "—"
                    await notify_field_submitter(
                        db,
                        workflow=WORKFLOW,
                        record_id=canonical_id,
                        record_doc_id=doc_id,
                        binding=binding,
                        subject=f"[MASCI] Daily Report revision needed — {project_label}",
                        reason_text=(reason or "The office needs you to revise this Daily Report."),
                        public_base_url=base,
                        send_email_fn=fsi_send_email,
                    )
            except Exception:
                pass

        return {
            "ok": True,
            "id": canonical_id,
            "doc_id": doc_id,
            "from_state": from_state,
            "to_state": to_state,
            "lifecycle_updated_at": now,
        }

    @api_router.get("/daily-reports/{report_id}/state-events")
    async def get_dr_state_events(
        report_id: str,
        actor=Depends(require_dr_actor),
    ) -> List[Dict[str, Any]]:
        doc = await db.daily_reports.find_one({"id": report_id}, {"_id": 0, "id": 1})
        if not doc:
            doc = await db.daily_reports.find_one(
                {"doc_id": report_id}, {"_id": 0, "id": 1}
            )
        if not doc:
            raise HTTPException(status_code=404, detail="Daily Report not found")
        return await list_state_events(
            db, workflow=WORKFLOW, record_id=doc["id"], limit=500
        )

    @api_router.get("/daily-reports/{report_id}/lifecycle")
    async def get_dr_lifecycle(
        report_id: str,
        actor=Depends(require_dr_actor),
    ) -> Dict[str, Any]:
        doc = await db.daily_reports.find_one({"id": report_id}, {"_id": 0})
        if not doc:
            doc = await db.daily_reports.find_one({"doc_id": report_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Daily Report not found")

        from_state = coerce_daily_report_state(doc.get("lifecycle_state"))
        role = normalize_actor_role(actor)

        candidates = DAILY_REPORT_TRANSITIONS.get(from_state, [])
        legal_next: List[Dict[str, Any]] = []
        for nxt in candidates:
            ok, _err = validate_daily_report_transition(
                from_state=from_state,
                to_state=nxt,
                actor=actor,
                reason="x" * 6,
                evidence={
                    "office_review_complete": True,
                    "payroll_inputs_verified": True,
                },
            )
            legal_next.append({"to_state": nxt, "allowed_for_actor": ok})

        return {
            "workflow": WORKFLOW,
            "id": doc.get("id"),
            "doc_id": doc.get("doc_id") or "",
            "lifecycle_state": from_state,
            "lifecycle_updated_at": doc.get("lifecycle_updated_at") or "",
            "lifecycle_closed_at": doc.get("lifecycle_closed_at") or "",
            "actor_role": role,
            "all_states": list(DAILY_REPORT_STATES),
            "default_state": DAILY_REPORT_DEFAULT_STATE,
            "legal_next_states": legal_next,
        }


__all__ = ["register_daily_report_lifecycle_routes"]

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field

from pm_auth import compute_pm_scope
from routes.tasks_notifications import task_service
from services.cost_codes.oppc_execution import (
    ACTIVITY_REVIEW_STATES,
    CONTROLLABILITY,
    ROOT_CAUSE_TYPES,
    _default_week_ending,
    build_project_execution_workspace,
    load_monday_review_doc,
    persist_monday_review_doc,
)


class MondayReviewStartBody(BaseModel):
    week_ending: Optional[str] = ""


class MondayReviewMetaBody(BaseModel):
    week_ending: Optional[str] = ""
    critical_path_reviewed: bool = False
    executive_actions: List[str] = Field(default_factory=list)
    notes: Optional[str] = ""


class ActivityReviewBody(BaseModel):
    week_ending: Optional[str] = ""
    primary_cause: Optional[str] = ""
    contributing_causes: List[str] = Field(default_factory=list)
    controllability: Optional[str] = ""
    evidence: List[str] = Field(default_factory=list)
    recovery_strategy: Optional[str] = ""
    recovery_owner_role: Optional[str] = ""
    recovery_owner_user_id: Optional[str] = ""
    recovery_owner_name: Optional[str] = ""
    recovery_date: Optional[str] = ""
    forecast_impact: Optional[str] = ""
    critical_path_impact: Optional[str] = ""
    executive_escalation: bool = False
    executive_actions: List[str] = Field(default_factory=list)
    notes: Optional[str] = ""
    link_existing_task_id: Optional[str] = ""


class MondayReviewCompleteBody(BaseModel):
    week_ending: Optional[str] = ""


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _actor_role(actor: Any) -> str:
    if actor is True:
        return "admin"
    if isinstance(actor, dict):
        return str(actor.get("role") or actor.get("_actor") or actor.get("_actor_kind") or "")
    return ""


def _actor_label(actor: Any) -> str:
    if actor is True:
        return "admin"
    if isinstance(actor, dict):
        return str(actor.get("email") or actor.get("name") or actor.get("id") or actor.get("role") or "system")
    return "system"


def _week_ending(raw: str) -> str:
    text = _clean(raw)
    return text[:10] if text else _default_week_ending()


async def _ensure_project_access(db, project_number: str, actor: Any) -> None:
    if _actor_role(actor) == "hr":
        raise HTTPException(status_code=403, detail="PM or admin access required")
    scope = await compute_pm_scope(db, actor)
    if not scope.allows(project_number):
        raise HTTPException(status_code=403, detail="Project not in PM scope")


async def _emit_workflow_event(
    db,
    *,
    workflow: str,
    project_number: str,
    record_id: str,
    module: str,
    event_name: str,
    stage: str,
) -> Dict[str, Any]:
    record = {"id": record_id, "doc_id": record_id, "project_number": project_number}
    try:
        from lib.trust_spine import emit_record_created, emit_workflow_stage  # noqa: PLC0415

        if stage == "record_created":
            await emit_record_created(
                db,
                workflow=workflow,
                record=record,
                module=module,
                event_name=event_name,
            )
        else:
            await emit_workflow_stage(
                db,
                workflow=workflow,
                stage=stage,
                record=record,
                module=module,
                event_name=event_name,
            )
    except Exception:
        pass
    return record


def register_oppc_execution_routes(api_router: APIRouter, db, require_any_portal_token) -> None:
    @api_router.get("/oppc/projects/{project_number}/execution-workspace")
    async def get_execution_workspace(
        project_number: str,
        week_ending: Optional[str] = None,
        actor=Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await _ensure_project_access(db, project_number, actor)
        return await build_project_execution_workspace(db, project_number, _week_ending(week_ending or ""))

    @api_router.post("/oppc/projects/{project_number}/monday-review/start")
    async def start_monday_review(
        project_number: str,
        body: MondayReviewStartBody = Body(...),
        actor=Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await _ensure_project_access(db, project_number, actor)
        week_ending = _week_ending(body.week_ending or "")
        review = await load_monday_review_doc(db, project_number, week_ending)
        review.setdefault("week_ending", week_ending)
        review.setdefault("activity_reviews", {})
        review["started_at"] = review.get("started_at") or __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        review["started_by"] = review.get("started_by") or _actor_label(actor)
        await persist_monday_review_doc(db, project_number, week_ending, review)
        await _emit_workflow_event(
            db,
            workflow="oppc-monday-look-behind",
            project_number=project_number,
            record_id=f"{project_number}:{week_ending}",
            module="routes/oppc_execution.py:start_monday_review",
            event_name="monday_review_started",
            stage="record_created",
        )
        workspace = await build_project_execution_workspace(db, project_number, week_ending)
        for activity in (workspace.get("monday_review", {}).get("activities") or []):
            if activity.get("requires_review"):
                await _emit_workflow_event(
                    db,
                    workflow="oppc-monday-look-behind",
                    project_number=project_number,
                    record_id=f"{project_number}:{week_ending}:{activity.get('code')}",
                    module="routes/oppc_execution.py:start_monday_review",
                    event_name="production_variance_detected",
                    stage="validation_complete",
                )
        return {"ok": True, **workspace}

    @api_router.put("/oppc/projects/{project_number}/monday-review/meta")
    async def update_monday_review_meta(
        project_number: str,
        body: MondayReviewMetaBody,
        actor=Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await _ensure_project_access(db, project_number, actor)
        week_ending = _week_ending(body.week_ending or "")
        review = await load_monday_review_doc(db, project_number, week_ending)
        review.setdefault("activity_reviews", {})
        if body.critical_path_reviewed:
            review["critical_path_reviewed_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
            review["critical_path_reviewed_by"] = _actor_label(actor)
        review["executive_actions"] = [str(x).strip() for x in (body.executive_actions or []) if str(x).strip()]
        review["notes"] = _clean(body.notes)
        await persist_monday_review_doc(db, project_number, week_ending, review)
        await _emit_workflow_event(
            db,
            workflow="oppc-monday-look-behind",
            project_number=project_number,
            record_id=f"{project_number}:{week_ending}",
            module="routes/oppc_execution.py:update_monday_review_meta",
            event_name="planning_ready_changed",
            stage="dashboard_updated",
        )
        workspace = await build_project_execution_workspace(db, project_number, week_ending)
        return {"ok": True, **workspace}

    @api_router.put("/oppc/projects/{project_number}/monday-review/activities/{cost_code}")
    async def update_activity_review(
        project_number: str,
        cost_code: str,
        body: ActivityReviewBody,
        actor=Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await _ensure_project_access(db, project_number, actor)
        week_ending = _week_ending(body.week_ending or "")
        workspace = await build_project_execution_workspace(db, project_number, week_ending)
        activity = next((row for row in (workspace.get("monday_review", {}).get("activities") or []) if _clean(row.get("code")) == _clean(cost_code)), None)
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found in Monday review workspace")

        primary_cause = _clean(body.primary_cause).lower().replace(" ", "_")
        if primary_cause and primary_cause not in ROOT_CAUSE_TYPES:
            raise HTTPException(status_code=422, detail="primary_cause is not in the approved OPPC taxonomy")
        contributing = [
            str(x).strip().lower().replace(" ", "_")
            for x in (body.contributing_causes or [])
            if str(x).strip()
        ]
        bad_contributing = [c for c in contributing if c not in ROOT_CAUSE_TYPES]
        if bad_contributing:
            raise HTTPException(status_code=422, detail=f"Invalid contributing causes: {', '.join(bad_contributing)}")
        controllability = _clean(body.controllability).lower()
        if controllability and controllability not in CONTROLLABILITY:
            raise HTTPException(status_code=422, detail="controllability must be controllable | shared | external")

        review = await load_monday_review_doc(db, project_number, week_ending)
        review.setdefault("activity_reviews", {})
        existing = dict((review.get("activity_reviews") or {}).get(cost_code) or {})
        recovery_task_id = _clean(existing.get("recovery_task_id"))
        recovery_status = _clean(existing.get("recovery_status"))

        if _clean(body.link_existing_task_id):
            task = await db.tasks.find_one({"id": _clean(body.link_existing_task_id)}, {"_id": 0, "id": 1, "status": 1})
            if not task:
                raise HTTPException(status_code=404, detail="Linked recovery task not found")
            recovery_task_id = _clean(task.get("id"))
            recovery_status = _clean(task.get("status")) or "Open"
        elif activity.get("requires_review") and not recovery_task_id and _clean(body.recovery_strategy) and _clean(body.recovery_owner_role):
            recovery_task_id = await task_service.create(
                db,
                {
                    "title": f"OPPC Recovery — {project_number} · {cost_code}",
                    "description": _clean(body.recovery_strategy)[:4000],
                    "source_module": "oppc.monday_review",
                    "source_record_id": f"{project_number}:{week_ending}:{cost_code}",
                    "linked_project_number": project_number,
                    "assignee_role": _clean(body.recovery_owner_role) or "pm",
                    "assignee_user_id": _clean(body.recovery_owner_user_id) or None,
                    "priority": "High" if activity.get("critical") else "Medium",
                    "due_at": _clean(body.recovery_date) or None,
                    "created_by": {"role": _actor_role(actor), "name": _actor_label(actor)},
                },
            )
            recovery_status = "Open"
            await _emit_workflow_event(
                db,
                workflow="oppc-monday-look-behind",
                project_number=project_number,
                record_id=f"{project_number}:{week_ending}:{cost_code}",
                module="routes/oppc_execution.py:update_activity_review",
                event_name="recovery_required",
                stage="audit_written",
            )

        activity_review = {
            **existing,
            "status_last_computed": activity.get("status"),
            "primary_cause": primary_cause,
            "contributing_causes": contributing,
            "controllability": controllability,
            "evidence": [str(x).strip() for x in (body.evidence or []) if str(x).strip()],
            "recovery_strategy": _clean(body.recovery_strategy),
            "recovery_owner_role": _clean(body.recovery_owner_role),
            "recovery_owner_user_id": _clean(body.recovery_owner_user_id),
            "recovery_owner_name": _clean(body.recovery_owner_name),
            "recovery_date": _clean(body.recovery_date),
            "forecast_impact": _clean(body.forecast_impact),
            "critical_path_impact": _clean(body.critical_path_impact),
            "executive_escalation": bool(body.executive_escalation),
            "executive_actions": [str(x).strip() for x in (body.executive_actions or []) if str(x).strip()],
            "notes": _clean(body.notes),
            "recovery_task_id": recovery_task_id,
            "recovery_status": recovery_status,
            "updated_by": _actor_label(actor),
            "updated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        }
        review["activity_reviews"][cost_code] = activity_review
        await persist_monday_review_doc(db, project_number, week_ending, review)
        await _emit_workflow_event(
            db,
            workflow="oppc-monday-look-behind",
            project_number=project_number,
            record_id=f"{project_number}:{week_ending}:{cost_code}",
            module="routes/oppc_execution.py:update_activity_review",
            event_name="production_variance_detected",
            stage="validation_complete",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-monday-look-behind",
            project_number=project_number,
            record_id=f"{project_number}:{week_ending}:{cost_code}",
            module="routes/oppc_execution.py:update_activity_review",
            event_name="variance_review_completed",
            stage="audit_written",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-monday-look-behind",
            project_number=project_number,
            record_id=f"{project_number}:{week_ending}:{cost_code}",
            module="routes/oppc_execution.py:update_activity_review",
            event_name="forecast_updated",
            stage="dashboard_updated",
        )
        fresh = await build_project_execution_workspace(db, project_number, week_ending)
        return {"ok": True, **fresh}

    @api_router.post("/oppc/projects/{project_number}/monday-review/complete")
    async def complete_monday_review(
        project_number: str,
        body: MondayReviewCompleteBody,
        actor=Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await _ensure_project_access(db, project_number, actor)
        week_ending = _week_ending(body.week_ending or "")
        workspace = await build_project_execution_workspace(db, project_number, week_ending)
        monday = workspace.get("monday_review") or {}
        if not monday.get("ready"):
            raise HTTPException(status_code=409, detail={
                "code": "monday_review_not_ready",
                "blocking_items": monday.get("blocking_items") or [],
                "warnings": monday.get("warnings") or [],
            })
        review = await load_monday_review_doc(db, project_number, week_ending)
        review.setdefault("activity_reviews", {})
        review["completed_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        review["completed_by"] = _actor_label(actor)
        await persist_monday_review_doc(db, project_number, week_ending, review)
        review_record_id = f"{project_number}:{week_ending}"
        await _emit_workflow_event(
            db,
            workflow="oppc-monday-look-behind",
            project_number=project_number,
            record_id=review_record_id,
            module="routes/oppc_execution.py:complete_monday_review",
            event_name="recovery_completed",
            stage="audit_written",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-monday-look-behind",
            project_number=project_number,
            record_id=review_record_id,
            module="routes/oppc_execution.py:complete_monday_review",
            event_name="planning_ready_changed",
            stage="dashboard_updated",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-monday-look-behind",
            project_number=project_number,
            record_id=review_record_id,
            module="routes/oppc_execution.py:complete_monday_review",
            event_name="completed",
            stage="completed",
        )
        fresh = await build_project_execution_workspace(db, project_number, week_ending)
        return {"ok": True, **fresh}


__all__ = ["register_oppc_execution_routes"]
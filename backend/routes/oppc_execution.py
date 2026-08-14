from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

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
from services.cost_codes.oppc_briefings import (
    approve_briefing,
    build_enterprise_monday_briefing,
    build_project_monday_briefing,
    ensure_monday_briefing_indexes,
    freeze_briefing,
    load_monday_briefing_doc,
    persist_monday_briefing_doc,
    render_monday_briefing_pdf,
)
from services.cost_codes.oppc_intelligence import (
    CONTROLLABILITY_OPTIONS,
    RECOVERY_PRIORITIES,
    RECOVERY_STRATEGIES,
    ROOT_CAUSE_TAXONOMY,
    VARIANCE_STATUSES,
    build_enterprise_resource_coordination,
    build_executive_operations_center,
    build_project_variance_intelligence,
    upsert_variance_review,
)
from lib.enterprise_governance import require_governed_action, governance_project_scope
from lib.release_scope import is_release_deferred, raise_release_deferred_404


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


class BriefingActionBody(BaseModel):
    week_ending: Optional[str] = ""
    note: Optional[str] = ""


class VarianceReviewBody(BaseModel):
    status: Optional[str] = "under_review"
    primary_cause: Optional[str] = ""
    contributing_causes: List[str] = Field(default_factory=list)
    controllability: Optional[str] = ""
    cause_notes: Optional[str] = ""
    recovery_strategy: Optional[str] = ""
    recovery_priority: Optional[str] = "high"
    recovery_owner_role: Optional[str] = ""
    recovery_owner_user_id: Optional[str] = ""
    recovery_due_date: Optional[str] = ""
    requires_executive_review: bool = False
    executive_notes: List[str] = Field(default_factory=list)
    linked_dispatch_records: List[str] = Field(default_factory=list)
    linked_shop_records: List[str] = Field(default_factory=list)
    linked_documents: List[str] = Field(default_factory=list)
    approval: Dict[str, Any] = Field(default_factory=dict)
    recovery_plan: Dict[str, Any] = Field(default_factory=dict)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _slug(value: Any) -> str:
    return _clean(value).lower().replace(" ", "_")


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


def _validate_variance_taxonomy(payload: VarianceReviewBody) -> None:
    if _slug(payload.status) not in VARIANCE_STATUSES:
        raise HTTPException(status_code=422, detail="variance status is not in the approved canonical taxonomy")
    primary = _slug(payload.primary_cause)
    if primary and primary not in ROOT_CAUSE_TAXONOMY:
        raise HTTPException(status_code=422, detail="primary_cause is not in the approved canonical taxonomy")
    bad_contributing = [item for item in [_slug(x) for x in payload.contributing_causes] if item and item not in ROOT_CAUSE_TAXONOMY]
    if bad_contributing:
        raise HTTPException(status_code=422, detail=f"Invalid contributing causes: {', '.join(bad_contributing)}")
    controllability = _slug(payload.controllability)
    if controllability and controllability not in CONTROLLABILITY_OPTIONS:
        raise HTTPException(status_code=422, detail="controllability is not in the approved canonical taxonomy")
    strategy = _slug(payload.recovery_strategy)
    if strategy and strategy not in RECOVERY_STRATEGIES:
        raise HTTPException(status_code=422, detail="recovery_strategy is not in the approved canonical taxonomy")
    priority = _slug(payload.recovery_priority)
    if priority and priority not in RECOVERY_PRIORITIES:
        raise HTTPException(status_code=422, detail="recovery_priority is not in the approved canonical taxonomy")


async def _ensure_project_access(db, project_number: str, actor: Any, request: Optional[Request] = None, read_only: bool = False) -> None:
    # OWNER-AUTHORIZED (final acceptance): a genuine system_administrator / global-scope actor
    # has GLOBAL PROJECT READ for oversight, truth verification, certification and support.
    # This is READ-ONLY — write/mutation endpoints pass read_only=False and remain fully governed
    # (no project editing / approval / write authority is broadened). Ordinary PMs stay scoped by
    # governance_project_scope; unrelated roles remain denied by require_governed_action below.
    if read_only:
        scope = await governance_project_scope(db, actor)
        if scope.is_admin:  # global scope only (system admin / super admin / governance_scope_mode=global)
            return
    await require_governed_action(
        db,
        actor=actor,
        action_key="oppc.view",
        resource_type="oppc_project_scope",
        resource={"id": f"oppc:{project_number}", "project_number": project_number},
        requested_context={"project_number": project_number, "scope": "oppc_project"},
        request=request,
    )


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
        await _ensure_project_access(db, project_number, actor, read_only=True)
        return await build_project_execution_workspace(db, project_number, _week_ending(week_ending or ""))

    @api_router.get("/oppc/projects/{project_number}/monday-briefing")
    async def get_project_monday_briefing(
        project_number: str,
        week_ending: Optional[str] = None,
        actor=Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await _ensure_project_access(db, project_number, actor, read_only=True)
        await ensure_monday_briefing_indexes(db)
        week = _week_ending(week_ending or "")
        doc = await load_monday_briefing_doc(db, scope_type="project", scope_key=project_number, week_ending=week)
        if not doc:
            doc = await build_project_monday_briefing(db, project_number=project_number, week_ending=week, actor_label=_actor_label(actor))
        return {"briefing": doc, "scope": {"type": "project", "key": project_number, "week_ending": week}}

    @api_router.post("/oppc/projects/{project_number}/monday-briefing/generate")
    async def generate_project_monday_briefing(
        request: Request,
        project_number: str,
        body: BriefingActionBody,
        actor=Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await _ensure_project_access(db, project_number, actor)
        await ensure_monday_briefing_indexes(db)
        week = _week_ending(body.week_ending or "")
        existing = await load_monday_briefing_doc(db, scope_type="project", scope_key=project_number, week_ending=week)
        if existing.get("frozen"):
            await require_governed_action(
                db,
                actor=actor,
                action_key="governance.admin",
                resource_type="project_monday_briefing",
                resource={"id": f"brief:{project_number}:{week}", "project_number": project_number, "submitted_by": {"user_id": actor.get("id")}, "status": "frozen"},
                requested_context={"project_number": project_number, "week_ending": week, "regeneration_reason": "frozen_briefing_regenerate"},
                request=request,
            )
        doc = await build_project_monday_briefing(db, project_number=project_number, week_ending=week, actor_label=_actor_label(actor))
        doc["approval_history"] = list(existing.get("approval_history") or [])
        if existing.get("frozen"):
            doc["regenerated_from_frozen_briefing"] = True
            doc["regenerated_from_content_hash"] = existing.get("content_hash") or ""
            doc["regenerated_by"] = _actor_label(actor)
            doc["regenerated_note"] = _clean(body.note) or "Administrative regenerate from frozen briefing"
        saved = await persist_monday_briefing_doc(db, doc)
        await _emit_workflow_event(db, workflow="oppc-monday-morning-briefing", project_number=project_number, record_id=f"brief:{project_number}:{week}", module="routes/oppc_execution.py:generate_project_monday_briefing", event_name="briefing_generated", stage="record_created")
        await _emit_workflow_event(db, workflow="oppc-monday-morning-briefing", project_number=project_number, record_id=f"brief:{project_number}:{week}", module="routes/oppc_execution.py:generate_project_monday_briefing", event_name="briefing_validated", stage="validation_complete")
        await _emit_workflow_event(db, workflow="oppc-monday-morning-briefing", project_number=project_number, record_id=f"brief:{project_number}:{week}", module="routes/oppc_execution.py:generate_project_monday_briefing", event_name="briefing_generated", stage="dashboard_updated")
        return {"ok": True, "briefing": saved}

    @api_router.post("/oppc/projects/{project_number}/monday-briefing/approve")
    async def approve_project_monday_briefing(
        request: Request,
        project_number: str,
        body: BriefingActionBody,
        actor=Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await _ensure_project_access(db, project_number, actor)
        await require_governed_action(
            db,
            actor=actor,
            action_key="forecast.approve",
            resource_type="project_monday_briefing",
            resource={"id": f"brief:{project_number}:{body.week_ending or ''}", "project_number": project_number, "submitted_by": {"user_id": actor.get("id")}},
            requested_context={"project_number": project_number, "week_ending": body.week_ending or ""},
            request=request,
        )
        await ensure_monday_briefing_indexes(db)
        week = _week_ending(body.week_ending or "")
        existing = await load_monday_briefing_doc(db, scope_type="project", scope_key=project_number, week_ending=week)
        if not existing:
            existing = await build_project_monday_briefing(db, project_number=project_number, week_ending=week, actor_label=_actor_label(actor))
        if existing.get("frozen"):
            raise HTTPException(status_code=409, detail="Frozen briefings cannot be re-approved")
        saved = await persist_monday_briefing_doc(db, approve_briefing(existing, actor_label=_actor_label(actor), note=body.note or ""))
        await _emit_workflow_event(db, workflow="oppc-monday-morning-briefing", project_number=project_number, record_id=f"brief:{project_number}:{week}", module="routes/oppc_execution.py:approve_project_monday_briefing", event_name="briefing_approved", stage="audit_written")
        return {"ok": True, "briefing": saved}

    @api_router.post("/oppc/projects/{project_number}/monday-briefing/freeze")
    async def freeze_project_monday_briefing(
        request: Request,
        project_number: str,
        body: BriefingActionBody,
        actor=Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await _ensure_project_access(db, project_number, actor)
        await require_governed_action(
            db,
            actor=actor,
            action_key="briefing.approve",
            resource_type="project_monday_briefing",
            resource={"id": f"brief:{project_number}:{body.week_ending or ''}", "project_number": project_number, "submitted_by": {"user_id": actor.get("id")}},
            requested_context={"project_number": project_number, "week_ending": body.week_ending or ""},
            request=request,
        )
        await ensure_monday_briefing_indexes(db)
        week = _week_ending(body.week_ending or "")
        existing = await load_monday_briefing_doc(db, scope_type="project", scope_key=project_number, week_ending=week)
        if not existing:
            raise HTTPException(status_code=404, detail="Generate the briefing before freezing it")
        if _clean(existing.get("status")) != "approved":
            raise HTTPException(status_code=409, detail="Approve the briefing before freezing it")
        saved = await persist_monday_briefing_doc(db, freeze_briefing(existing, actor_label=_actor_label(actor), note=body.note or ""))
        await _emit_workflow_event(db, workflow="oppc-monday-morning-briefing", project_number=project_number, record_id=f"brief:{project_number}:{week}", module="routes/oppc_execution.py:freeze_project_monday_briefing", event_name="briefing_frozen", stage="completed")
        return {"ok": True, "briefing": saved}

    @api_router.get("/oppc/projects/{project_number}/monday-briefing/pdf")
    async def get_project_monday_briefing_pdf(
        project_number: str,
        week_ending: Optional[str] = None,
        actor=Depends(require_any_portal_token),
    ) -> Response:
        if is_release_deferred("executive_monday_briefing_pdf"):
            raise_release_deferred_404("executive_monday_briefing_pdf")
        await _ensure_project_access(db, project_number, actor, read_only=True)
        await ensure_monday_briefing_indexes(db)
        week = _week_ending(week_ending or "")
        doc = await load_monday_briefing_doc(db, scope_type="project", scope_key=project_number, week_ending=week)
        if not doc:
            doc = await build_project_monday_briefing(db, project_number=project_number, week_ending=week, actor_label=_actor_label(actor))
        pdf_bytes = render_monday_briefing_pdf(doc)
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"inline; filename=OPPC_Monday_Briefing_{project_number}_{week}.pdf"})

    @api_router.get("/oppc/projects/{project_number}/variance-intelligence")
    async def get_variance_intelligence(
        project_number: str,
        week_ending: Optional[str] = None,
        actor=Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await _ensure_project_access(db, project_number, actor, read_only=True)
        workspace = await build_project_execution_workspace(db, project_number, _week_ending(week_ending or ""))
        return await build_project_variance_intelligence(
            db,
            project_number=project_number,
            workspace=workspace,
            week_ending=_week_ending(week_ending or ""),
        )

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

    @api_router.put("/oppc/projects/{project_number}/variances/{variance_key}")
    async def update_variance_review(
        project_number: str,
        variance_key: str,
        body: VarianceReviewBody,
        actor=Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await _ensure_project_access(db, project_number, actor)
        _validate_variance_taxonomy(body)
        variance_key = _clean(variance_key)
        week_ending = _clean((body.recovery_plan or {}).get("planning_cycle")) or (variance_key.split(":")[1] if len(variance_key.split(":")) > 1 else "")
        workspace = await build_project_execution_workspace(db, project_number, _week_ending(week_ending))
        intelligence = await build_project_variance_intelligence(
            db,
            project_number=project_number,
            workspace=workspace,
            week_ending=_week_ending(week_ending),
        )
        variance = next((row for row in (intelligence.get("variances") or []) if _clean(row.get("variance_key")) == variance_key), None)
        if not variance:
            raise HTTPException(status_code=404, detail="Variance was not found in the canonical variance engine")

        recovery_task_id = ""
        recovery_status = ""
        if _slug(body.status) in {"recovery_required", "closed"} and _slug(body.recovery_strategy) and _clean(body.recovery_owner_role):
            existing_task_id = _clean((variance.get("supporting_review") or {}).get("recovery_task_id"))
            if existing_task_id:
                recovery_task_id = existing_task_id
                task = await db.tasks.find_one({"id": existing_task_id}, {"_id": 0, "status": 1})
                recovery_status = _clean((task or {}).get("status")) or "Open"
            else:
                recovery_task_id = await task_service.create(
                    db,
                    {
                        "title": f"Operational Recovery — {project_number} · {_clean(variance.get('activity'))} · {_clean(variance.get('variance_type')).title()}",
                        "description": _clean(body.cause_notes or body.recovery_strategy)[:4000],
                        "source_module": "oppc.variance_intelligence",
                        "source_record_id": variance_key,
                        "linked_project_number": project_number,
                        "assignee_role": _clean(body.recovery_owner_role) or "pm",
                        "assignee_user_id": _clean(body.recovery_owner_user_id) or None,
                        "priority": (_slug(body.recovery_priority) or "high").title(),
                        "due_at": _clean(body.recovery_due_date) or None,
                        "created_by": {"role": _actor_role(actor), "name": _actor_label(actor)},
                    },
                )
                recovery_status = "Open"

        review_doc = await upsert_variance_review(
            db,
            project_number=project_number,
            planning_cycle=intelligence.get("planning_cycle") or _week_ending(week_ending),
            variance_key=variance_key,
            payload={
                **body.model_dump(),
                "recovery_task_id": recovery_task_id or _clean((variance.get("supporting_review") or {}).get("recovery_task_id")),
                "recovery_status": recovery_status or _clean((variance.get("supporting_review") or {}).get("recovery_status")),
            },
            actor_label=_actor_label(actor),
            actor_role=_actor_role(actor),
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-variance-intelligence",
            project_number=project_number,
            record_id=variance_key,
            module="routes/oppc_execution.py:update_variance_review",
            event_name="variance_review_started",
            stage="record_created",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-variance-intelligence",
            project_number=project_number,
            record_id=variance_key,
            module="routes/oppc_execution.py:update_variance_review",
            event_name="variance_cause_recorded",
            stage="validation_complete",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-variance-intelligence",
            project_number=project_number,
            record_id=variance_key,
            module="routes/oppc_execution.py:update_variance_review",
            event_name="variance_review_completed",
            stage="audit_written",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-variance-intelligence",
            project_number=project_number,
            record_id=variance_key,
            module="routes/oppc_execution.py:update_variance_review",
            event_name="variance_dashboard_updated",
            stage="dashboard_updated",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-recovery-intelligence",
            project_number=project_number,
            record_id=variance_key,
            module="routes/oppc_execution.py:update_variance_review",
            event_name="recovery_intelligence_started",
            stage="record_created",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-recovery-intelligence",
            project_number=project_number,
            record_id=variance_key,
            module="routes/oppc_execution.py:update_variance_review",
            event_name="recovery_strategy_validated",
            stage="validation_complete",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-recovery-intelligence",
            project_number=project_number,
            record_id=variance_key,
            module="routes/oppc_execution.py:update_variance_review",
            event_name="recovery_review_written",
            stage="audit_written",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-recovery-intelligence",
            project_number=project_number,
            record_id=variance_key,
            module="routes/oppc_execution.py:update_variance_review",
            event_name="recovery_required" if _slug(review_doc.get("status")) == "recovery_required" else "variance_closed",
            stage="dashboard_updated",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-recovery-intelligence",
            project_number=project_number,
            record_id=variance_key,
            module="routes/oppc_execution.py:update_variance_review",
            event_name="recovery_intelligence_completed",
            stage="completed",
        )
        if _slug(review_doc.get("status")) == "closed":
            await _emit_workflow_event(
                db,
                workflow="oppc-variance-intelligence",
                project_number=project_number,
                record_id=variance_key,
                module="routes/oppc_execution.py:update_variance_review",
                event_name="variance_closed",
                stage="completed",
            )
        workspace = await build_project_execution_workspace(db, project_number, intelligence.get("planning_cycle") or _week_ending(week_ending))
        return {
            "ok": True,
            "review": review_doc,
            "workspace": workspace,
            "variance_intelligence": await build_project_variance_intelligence(
                db,
                project_number=project_number,
                workspace=workspace,
                week_ending=intelligence.get("planning_cycle") or _week_ending(week_ending),
            ),
        }

    @api_router.get("/oppc/enterprise/resource-coordination")
    async def get_enterprise_resource_coordination(
        request: Request,
        week_ending: Optional[str] = None,
        actor=Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await require_governed_action(
            db,
            actor=actor,
            action_key="executive.view",
            resource_type="enterprise_resource_coordination",
            resource={"id": f"enterprise-resource:{week_ending or ''}", "project_number": "enterprise"},
            requested_context={"project_number": "enterprise", "week_ending": week_ending or ""},
            request=request,
        )
        payload = await build_enterprise_resource_coordination(db, _week_ending(week_ending or ""))
        record_id = f"enterprise:{payload.get('planning_cycle')}"
        await _emit_workflow_event(
            db,
            workflow="oppc-enterprise-resource-coordination",
            project_number="enterprise",
            record_id=record_id,
            module="routes/oppc_execution.py:get_enterprise_resource_coordination",
            event_name="resource_coordination_opened",
            stage="record_created",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-enterprise-resource-coordination",
            project_number="enterprise",
            record_id=record_id,
            module="routes/oppc_execution.py:get_enterprise_resource_coordination",
            event_name="resource_coordination_validated",
            stage="validation_complete",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-enterprise-resource-coordination",
            project_number="enterprise",
            record_id=record_id,
            module="routes/oppc_execution.py:get_enterprise_resource_coordination",
            event_name="resource_coordination_audited",
            stage="audit_written",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-enterprise-resource-coordination",
            project_number="enterprise",
            record_id=record_id,
            module="routes/oppc_execution.py:get_enterprise_resource_coordination",
            event_name="resource_coordination_published",
            stage="dashboard_updated",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-enterprise-resource-coordination",
            project_number="enterprise",
            record_id=record_id,
            module="routes/oppc_execution.py:get_enterprise_resource_coordination",
            event_name="resource_coordination_completed",
            stage="completed",
        )
        return payload

    @api_router.get("/oppc/enterprise/executive-operations-center")
    async def get_executive_operations_center(
        request: Request,
        week_ending: Optional[str] = None,
        actor=Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await require_governed_action(
            db,
            actor=actor,
            action_key="executive.view",
            resource_type="executive_operations_center",
            resource={"id": f"executive-operations:{week_ending or ''}", "project_number": "enterprise"},
            requested_context={"project_number": "enterprise", "week_ending": week_ending or ""},
            request=request,
        )
        payload = await build_executive_operations_center(db, _week_ending(week_ending or ""))
        record_id = f"executive:{payload.get('planning_cycle')}"
        await _emit_workflow_event(
            db,
            workflow="oppc-enterprise-resource-coordination",
            project_number="enterprise",
            record_id=record_id,
            module="routes/oppc_execution.py:get_executive_operations_center",
            event_name="executive_operations_opened",
            stage="record_created",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-enterprise-resource-coordination",
            project_number="enterprise",
            record_id=record_id,
            module="routes/oppc_execution.py:get_executive_operations_center",
            event_name="executive_operations_validated",
            stage="validation_complete",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-enterprise-resource-coordination",
            project_number="enterprise",
            record_id=record_id,
            module="routes/oppc_execution.py:get_executive_operations_center",
            event_name="executive_operations_audited",
            stage="audit_written",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-enterprise-resource-coordination",
            project_number="enterprise",
            record_id=record_id,
            module="routes/oppc_execution.py:get_executive_operations_center",
            event_name="executive_operations_published",
            stage="dashboard_updated",
        )
        await _emit_workflow_event(
            db,
            workflow="oppc-enterprise-resource-coordination",
            project_number="enterprise",
            record_id=record_id,
            module="routes/oppc_execution.py:get_executive_operations_center",
            event_name="executive_operations_completed",
            stage="completed",
        )
        return payload

    @api_router.get("/oppc/enterprise/monday-briefing")
    async def get_enterprise_monday_briefing(
        request: Request,
        week_ending: Optional[str] = None,
        actor=Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await require_governed_action(
            db,
            actor=actor,
            action_key="executive.view",
            resource_type="enterprise_monday_briefing",
            resource={"id": f"brief:enterprise:{week_ending or ''}", "project_number": "enterprise"},
            requested_context={"project_number": "enterprise", "week_ending": week_ending or ""},
            request=request,
        )
        await ensure_monday_briefing_indexes(db)
        week = _week_ending(week_ending or "")
        doc = await load_monday_briefing_doc(db, scope_type="enterprise", scope_key="enterprise", week_ending=week)
        if not doc:
            doc = await build_enterprise_monday_briefing(db, week_ending=week, actor_label=_actor_label(actor))
        return {"briefing": doc, "scope": {"type": "enterprise", "key": "enterprise", "week_ending": week}}

    @api_router.post("/oppc/enterprise/monday-briefing/generate")
    async def generate_enterprise_monday_briefing(
        request: Request,
        body: BriefingActionBody,
        actor=Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await require_governed_action(
            db,
            actor=actor,
            action_key="executive.view",
            resource_type="enterprise_monday_briefing",
            resource={"id": f"brief:enterprise:{body.week_ending or ''}", "project_number": "enterprise"},
            requested_context={"project_number": "enterprise", "week_ending": body.week_ending or ""},
            request=request,
        )
        await ensure_monday_briefing_indexes(db)
        week = _week_ending(body.week_ending or "")
        existing = await load_monday_briefing_doc(db, scope_type="enterprise", scope_key="enterprise", week_ending=week)
        if existing.get("frozen"):
            await require_governed_action(
                db,
                actor=actor,
                action_key="governance.admin",
                resource_type="enterprise_monday_briefing",
                resource={"id": f"brief:enterprise:{week}", "project_number": "enterprise", "submitted_by": {"user_id": actor.get("id")}, "status": "frozen"},
                requested_context={"project_number": "enterprise", "week_ending": week, "regeneration_reason": "frozen_briefing_regenerate"},
                request=request,
            )
        doc = await build_enterprise_monday_briefing(db, week_ending=week, actor_label=_actor_label(actor))
        doc["approval_history"] = list(existing.get("approval_history") or [])
        if existing.get("frozen"):
            doc["regenerated_from_frozen_briefing"] = True
            doc["regenerated_from_content_hash"] = existing.get("content_hash") or ""
            doc["regenerated_by"] = _actor_label(actor)
            doc["regenerated_note"] = _clean(body.note) or "Administrative regenerate from frozen briefing"
        saved = await persist_monday_briefing_doc(db, doc)
        await _emit_workflow_event(db, workflow="oppc-monday-morning-briefing", project_number="enterprise", record_id=f"brief:enterprise:{week}", module="routes/oppc_execution.py:generate_enterprise_monday_briefing", event_name="briefing_generated", stage="record_created")
        await _emit_workflow_event(db, workflow="oppc-monday-morning-briefing", project_number="enterprise", record_id=f"brief:enterprise:{week}", module="routes/oppc_execution.py:generate_enterprise_monday_briefing", event_name="briefing_validated", stage="validation_complete")
        await _emit_workflow_event(db, workflow="oppc-monday-morning-briefing", project_number="enterprise", record_id=f"brief:enterprise:{week}", module="routes/oppc_execution.py:generate_enterprise_monday_briefing", event_name="briefing_generated", stage="dashboard_updated")
        return {"ok": True, "briefing": saved}

    @api_router.post("/oppc/enterprise/monday-briefing/approve")
    async def approve_enterprise_monday_briefing(
        request: Request,
        body: BriefingActionBody,
        actor=Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await require_governed_action(
            db,
            actor=actor,
            action_key="executive.view",
            resource_type="enterprise_monday_briefing",
            resource={"id": f"brief:enterprise:{body.week_ending or ''}", "project_number": "enterprise", "submitted_by": {"user_id": actor.get("id")}},
            requested_context={"project_number": "enterprise", "week_ending": body.week_ending or ""},
            request=request,
        )
        await ensure_monday_briefing_indexes(db)
        week = _week_ending(body.week_ending or "")
        existing = await load_monday_briefing_doc(db, scope_type="enterprise", scope_key="enterprise", week_ending=week)
        if not existing:
            existing = await build_enterprise_monday_briefing(db, week_ending=week, actor_label=_actor_label(actor))
        if existing.get("frozen"):
            raise HTTPException(status_code=409, detail="Frozen briefings cannot be re-approved")
        saved = await persist_monday_briefing_doc(db, approve_briefing(existing, actor_label=_actor_label(actor), note=body.note or ""))
        await _emit_workflow_event(db, workflow="oppc-monday-morning-briefing", project_number="enterprise", record_id=f"brief:enterprise:{week}", module="routes/oppc_execution.py:approve_enterprise_monday_briefing", event_name="briefing_approved", stage="audit_written")
        return {"ok": True, "briefing": saved}

    @api_router.post("/oppc/enterprise/monday-briefing/freeze")
    async def freeze_enterprise_monday_briefing(
        request: Request,
        body: BriefingActionBody,
        actor=Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await require_governed_action(
            db,
            actor=actor,
            action_key="briefing.approve",
            resource_type="enterprise_monday_briefing",
            resource={"id": f"brief:enterprise:{body.week_ending or ''}", "project_number": "enterprise", "submitted_by": {"user_id": actor.get("id")}},
            requested_context={"project_number": "enterprise", "week_ending": body.week_ending or ""},
            request=request,
        )
        await ensure_monday_briefing_indexes(db)
        week = _week_ending(body.week_ending or "")
        existing = await load_monday_briefing_doc(db, scope_type="enterprise", scope_key="enterprise", week_ending=week)
        if not existing:
            raise HTTPException(status_code=404, detail="Generate the briefing before freezing it")
        if _clean(existing.get("status")) != "approved":
            raise HTTPException(status_code=409, detail="Approve the briefing before freezing it")
        saved = await persist_monday_briefing_doc(db, freeze_briefing(existing, actor_label=_actor_label(actor), note=body.note or ""))
        await _emit_workflow_event(db, workflow="oppc-monday-morning-briefing", project_number="enterprise", record_id=f"brief:enterprise:{week}", module="routes/oppc_execution.py:freeze_enterprise_monday_briefing", event_name="briefing_frozen", stage="completed")
        return {"ok": True, "briefing": saved}

    @api_router.get("/oppc/enterprise/monday-briefing/pdf")
    async def get_enterprise_monday_briefing_pdf(
        request: Request,
        week_ending: Optional[str] = None,
        actor=Depends(require_any_portal_token),
    ) -> Response:
        if is_release_deferred("executive_monday_briefing_pdf"):
            raise_release_deferred_404("executive_monday_briefing_pdf")
        await require_governed_action(
            db,
            actor=actor,
            action_key="executive.view",
            resource_type="enterprise_monday_briefing",
            resource={"id": f"brief:enterprise:{week_ending or ''}", "project_number": "enterprise"},
            requested_context={"project_number": "enterprise", "week_ending": week_ending or ""},
            request=request,
        )
        await ensure_monday_briefing_indexes(db)
        week = _week_ending(week_ending or "")
        doc = await load_monday_briefing_doc(db, scope_type="enterprise", scope_key="enterprise", week_ending=week)
        if not doc:
            doc = await build_enterprise_monday_briefing(db, week_ending=week, actor_label=_actor_label(actor))
        pdf_bytes = render_monday_briefing_pdf(doc)
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"inline; filename=OPPC_Enterprise_Monday_Briefing_{week}.pdf"})


__all__ = ["register_oppc_execution_routes"]
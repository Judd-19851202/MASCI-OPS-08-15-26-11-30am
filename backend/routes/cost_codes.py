"""Enterprise Spine · Scheduling & Cost-Code Module foundation.

Universal Cost Registry (Admin), PM project assignments, Daily Report
quantity tracking helpers, and additive job progress calculations.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from lib.enterprise_governance import require_governed_action
from lib.operator_safety import require_destructive_confirmation, require_destructive_runtime_guard
from services.cost_codes import get_provider
from services.cost_codes.foundation import (
    ALLOWED_UNITS,
    build_forecast_governance_summary,
    build_forecast_snapshot_record,
    build_planning_lifecycle_snapshot,
    build_planning_readiness,
    build_progress_snapshot,
    build_project_cost_code_option,
    build_weekly_rollover_preview,
    load_project_forecast_history,
    load_project_assignments,
    load_project_cost_code_actuals,
    load_project_planning_lifecycle,
    normalize_forecast_override,
    persist_project_forecast_overrides,
    persist_project_forecast_snapshot,
    persist_project_assignments,
    persist_project_planning_lifecycle,
    recompute_project_progress as recompute_project_progress_snapshot,
    normalize_job_assignment,
    normalize_registry_item,
    now_iso,
    serialize_assignment,
)
from services.cost_codes.schedule_engine import (
    SCENARIO_PROFILES,
    build_schedule_scenario_comparison,
    build_schedule_snapshot,
    render_dot_schedule_pdf,
)

REGISTRY_COLLECTION = "cost_code_registry"
logger = logging.getLogger(__name__)
_SPINE_INDEXES_READY = False


class CostRegistryItemIn(BaseModel):
    code: str = Field(min_length=1, max_length=120)
    item_name: str = Field(min_length=1, max_length=240)
    unit_of_measure: str = Field(min_length=1, max_length=16)
    bid_unit_price: float = 0.0
    target_man_hours: float = 0.0
    active: bool = True


class CostRegistryBulkBody(BaseModel):
    items: List[CostRegistryItemIn] = Field(default_factory=list)


class ProjectAssignmentIn(BaseModel):
    code: str = Field(min_length=1, max_length=120)
    item_name: Optional[str] = ""
    unit_of_measure: Optional[str] = ""
    bid_unit_price: float = 0.0
    target_man_hours: float = 0.0
    bid_quantity: float = 0.0
    original_quantity: float = 0.0
    authorized_quantity: float = 0.0
    forecast_quantity: float = 0.0
    cpm_activity_id: Optional[str] = ""
    cpm_activity_name: Optional[str] = ""
    schedule_phase: Optional[str] = ""
    planned_performer: Optional[str] = ""
    planned_equipment_units: List[str] = Field(default_factory=list)
    resource_demand: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = ""


class ProjectAssignmentsBody(BaseModel):
    assignments: List[ProjectAssignmentIn] = Field(default_factory=list)


class ScheduleTaskUpdateIn(BaseModel):
    code: str = Field(min_length=1, max_length=120)
    schedule_start_date: Optional[str] = ""
    duration_days: int = Field(default=1, ge=1, le=365)
    predecessor_codes: List[str] = Field(default_factory=list)
    cpm_activity_id: Optional[str] = ""
    cpm_activity_name: Optional[str] = ""
    schedule_phase: Optional[str] = ""
    planned_performer: Optional[str] = ""
    notes: Optional[str] = ""


class ProjectScheduleBody(BaseModel):
    tasks: List[ScheduleTaskUpdateIn] = Field(default_factory=list)


class PlanningPublishBody(BaseModel):
    note: Optional[str] = ""


class WeeklyRolloverApplyBody(BaseModel):
    confirm: str = Field(min_length=1)
    note: Optional[str] = ""


class ForecastSnapshotBody(BaseModel):
    scenario_key: Optional[str] = "calculated_truth"
    note: Optional[str] = ""


class ForecastOverrideBody(BaseModel):
    adjusted_start_date: Optional[str] = ""
    adjusted_finish_date: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    note: Optional[str] = ""
    evidence_links: List[str] = Field(default_factory=list)


async def _is_admin_actor(actor: Any) -> bool:
    if actor is True:
        return True
    if isinstance(actor, dict):
        if actor.get("role") == "admin":
            return True
        if actor.get("_actor_kind") == "pm_user":
            return False
    return bool(actor)


async def _load_registry(db) -> List[Dict[str, Any]]:
    rows = await db[REGISTRY_COLLECTION].find({}, {"_id": 0}).sort("code", 1).to_list(5000)
    return rows


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


async def _emit_oppc_plan_stage(
    db,
    *,
    workflow: str = "oppc-cost-code-plan",
    stage: str,
    record: Dict[str, Any],
    module: str,
    status: str = "ok",
    failure_reason: Optional[str] = None,
    remediation: Optional[str] = None,
) -> None:
    try:
        from lib.trust_spine import emit_workflow_stage  # noqa: PLC0415

        await emit_workflow_stage(
            db,
            workflow=workflow,
            stage=stage,
            record=record,
            module=module,
            status=status,
            failure_reason=failure_reason,
            remediation=remediation,
        )
    except Exception:  # noqa: BLE001
        pass


async def _open_oppc_plan_lifecycle(db, *, project_number: str, module: str) -> Dict[str, Any]:
    return await _open_oppc_workflow_lifecycle(
        db,
        workflow="oppc-cost-code-plan",
        project_number=project_number,
        module=module,
    )


async def _open_oppc_workflow_lifecycle(db, *, workflow: str, project_number: str, module: str) -> Dict[str, Any]:
    record = {"id": project_number, "doc_id": project_number, "project_number": project_number}
    try:
        from lib.trust_spine import emit_record_created, STAGE_VALIDATION_COMPLETE  # noqa: PLC0415

        await emit_record_created(
            db,
            workflow=workflow,
            record=record,
            module=module,
        )
        await _emit_oppc_plan_stage(
            db,
            workflow=workflow,
            stage=STAGE_VALIDATION_COMPLETE,
            record=record,
            module=module,
        )
    except Exception:  # noqa: BLE001
        pass
    return record


def _public_rollover_payload(preview: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": preview.get("status") or "blocked",
        "blocked_reason": preview.get("blocked_reason") or "",
        "supports_apply": bool(preview.get("supports_apply")),
        "current_anchor_date": preview.get("current_anchor_date") or "",
        "rollover_anchor_date": preview.get("rollover_anchor_date") or "",
        "changed_count": int(preview.get("changed_count") or 0),
        "action_count": int(preview.get("action_count") or 0),
        "summary": dict(preview.get("summary") or {}),
        "actions": list(preview.get("actions") or []),
        "next_schedule": dict(preview.get("next_schedule") or {}),
    }


async def _resolve_project_schedule(db, project_number: str) -> Dict[str, Any]:
    assignments = await load_project_assignments(db, project_number)
    daily_rows = await load_project_cost_code_actuals(db, project_number)
    progress = build_progress_snapshot(assignments, daily_rows) if assignments else None
    forecast_history = await load_project_forecast_history(db, project_number)
    overrides = forecast_history.get("overrides") or []
    schedule = build_schedule_snapshot(assignments, progress, daily_rows=daily_rows, overrides=overrides)
    scenario_comparison = build_schedule_scenario_comparison(
        assignments,
        progress,
        daily_rows=daily_rows,
        anchor_date=(schedule.get("window") or {}).get("anchor_date"),
        scenario_keys=["additional_crew", "weekend_work", "additional_shift"],
        overrides=overrides,
    )
    planning_readiness = build_planning_readiness(assignments)
    stored_lifecycle = await load_project_planning_lifecycle(db, project_number)
    planning_lifecycle = build_planning_lifecycle_snapshot(
        planning_readiness=planning_readiness,
        stored=stored_lifecycle,
        schedule_window=schedule.get("window") or {},
    )
    schedule["monday_look_behind_ready"] = bool(planning_readiness.get("supports_monday_look_behind"))
    return {
        "project_number": project_number,
        "assignments": [serialize_assignment(row, include_financial=False) for row in assignments],
        "progress": progress,
        "planning_readiness": planning_readiness,
        "planning_lifecycle": planning_lifecycle,
        "schedule": schedule,
        "forecasting": {
            "constitutional_rule": "Forecasts derive only from canonical operational data. Overrides remain audited evidence and never replace calculated truth.",
            "scenario_comparison": scenario_comparison,
            "governance": build_forecast_governance_summary(forecast_history),
            "scenario_library": [
                {
                    "key": item.get("key"),
                    "label": item.get("label"),
                    "notes": item.get("notes"),
                    "rate_multiplier": item.get("rate_multiplier"),
                }
                for item in SCENARIO_PROFILES.values()
            ],
        },
        "monday_look_behind_ready": bool(planning_readiness.get("supports_monday_look_behind")),
    }


async def _registry_index(db) -> Dict[str, Dict[str, Any]]:
    rows = await _load_registry(db)
    return {str(row.get("code") or "").strip(): row for row in rows if str(row.get("code") or "").strip()}


async def _ensure_spine_indexes(db) -> None:
    global _SPINE_INDEXES_READY
    if _SPINE_INDEXES_READY:
        return
    try:
        await db[REGISTRY_COLLECTION].create_index("code", unique=True)
        await db.jobs_master.create_index("project_number")
        await db.daily_reports.create_index([("project_number", 1), ("report_date", 1)])
        _SPINE_INDEXES_READY = True
    except Exception as exc:  # noqa: BLE001
        logger.warning("[cost-codes] spine index ensure skipped: %s", exc)


def register_cost_code_routes(api_router: APIRouter, db, require_admin=None, require_admin_pm_or_hr_read=None) -> None:
    provider = get_provider(db)
    read_dep = require_admin_pm_or_hr_read or require_admin

    async def _require_cost_codes_read(actor: Any, project_number: str = "") -> None:
        await require_governed_action(
            db,
            actor=actor,
            action_key="cost_codes.read",
            resource_type="cost_code_workspace",
            resource={"id": project_number or "cost-code-workspace", "project_number": project_number or ""},
            requested_context={"project_number": project_number or "", "module": "cost_codes"},
        )

    async def _require_cost_codes_manage(actor: Any, project_number: str = "") -> None:
        await require_governed_action(
            db,
            actor=actor,
            action_key="cost_codes.manage",
            resource_type="cost_code_workspace",
            resource={"id": project_number or "cost-code-workspace", "project_number": project_number or ""},
            requested_context={"project_number": project_number or "", "module": "cost_codes"},
        )

    @api_router.get("/cost-codes/registry")
    async def list_registry(actor=Depends(read_dep)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        await _require_cost_codes_read(actor)
        rows = await _load_registry(db)
        return {"items": rows, "units": sorted(ALLOWED_UNITS)}

    @api_router.post("/cost-codes/registry")
    async def upsert_registry(body: CostRegistryItemIn, actor=Depends(require_admin)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        await _require_cost_codes_manage(actor)
        item = normalize_registry_item(body.model_dump())
        await db[REGISTRY_COLLECTION].update_one({"code": item["code"]}, {"$set": item}, upsert=True)
        return {"ok": True, "item": item}

    @api_router.put("/cost-codes/registry/bulk-replace")
    async def replace_registry(body: CostRegistryBulkBody, actor=Depends(require_admin)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        await _require_cost_codes_manage(actor)
        require_destructive_confirmation(
            body.model_dump(),
            expected_confirm="REPLACE_COST_CODE_REGISTRY",
        )
        require_destructive_runtime_guard(expected_db_name="masci_safety")
        items = [normalize_registry_item(row.model_dump()) for row in body.items]
        await db[REGISTRY_COLLECTION].delete_many({})
        if items:
            await db[REGISTRY_COLLECTION].insert_many(items)
        return {"ok": True, "count": len(items)}

    @api_router.get("/cost-codes/for-project")
    async def cost_codes_for_project(project_number: str = "") -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        codes = await provider.list_for_project(project_number)
        assigned = await load_project_assignments(db, project_number)
        if assigned:
            codes = [build_project_cost_code_option(row) for row in assigned]
        return {"project_number": project_number, "codes": codes}

    @api_router.get("/cost-codes/projects/{project_number}/assignments")
    async def get_project_assignments(project_number: str, actor=Depends(read_dep)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        await _require_cost_codes_read(actor, project_number)
        assignments = await load_project_assignments(db, project_number)
        progress = await recompute_project_progress_snapshot(db, project_number)
        planning_readiness = build_planning_readiness(assignments)
        return {
            "project_number": project_number,
            "assignments": [serialize_assignment(row, include_financial=False) for row in assignments],
            "progress": progress,
            "planning_readiness": planning_readiness,
            "supports_future_cpm": True,
            "financials_included": False,
        }

    @api_router.put("/cost-codes/projects/{project_number}/assignments")
    async def put_project_assignments(project_number: str, body: ProjectAssignmentsBody, actor=Depends(read_dep)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        await _require_cost_codes_manage(actor, project_number)
        registry = await _registry_index(db)
        existing_assignments = {
            str(row.get("code") or "").strip(): row
            for row in await load_project_assignments(db, project_number)
            if str(row.get("code") or "").strip()
        }
        rows: List[Dict[str, Any]] = []
        seen_codes = set()
        for idx, raw in enumerate(body.assignments):
            code = str(raw.code).strip()
            if code in seen_codes:
                raise HTTPException(status_code=422, detail=f"Duplicate assignment submitted for cost code {code}")
            seen_codes.add(code)
            item = registry.get(str(raw.code).strip())
            payload = raw.model_dump()
            if payload.get("authorized_quantity") in (None, 0, 0.0) and payload.get("bid_quantity") not in (None, ""):
                payload["authorized_quantity"] = payload.get("bid_quantity")
            if payload.get("original_quantity") in (None, 0, 0.0) and payload.get("authorized_quantity") not in (None, ""):
                payload["original_quantity"] = payload.get("authorized_quantity")
            if payload.get("forecast_quantity") in (None, 0, 0.0) and payload.get("authorized_quantity") not in (None, ""):
                payload["forecast_quantity"] = payload.get("authorized_quantity")
            try:
                merged = normalize_job_assignment(payload, item, existing_assignments.get(code))
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            merged["sort_order"] = idx
            rows.append(merged)
        spine_record = await _open_oppc_plan_lifecycle(
            db,
            project_number=project_number,
            module="routes/cost_codes.py:put_project_assignments",
        )
        try:
            await persist_project_assignments(db, project_number, rows)
        except LookupError as exc:
            await _emit_oppc_plan_stage(
                db,
                stage="audit_written",
                record=spine_record,
                module="jobs_master.assigned_cost_codes",
                status="failed",
                failure_reason=str(exc),
                remediation="Verify the project exists before updating assigned cost codes.",
            )
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        progress = await recompute_project_progress_snapshot(db, project_number)
        planning_readiness = build_planning_readiness(rows)
        schedule = build_schedule_snapshot(rows, progress)
        next_lifecycle = build_planning_lifecycle_snapshot(
            planning_readiness=planning_readiness,
            stored={
                **(await load_project_planning_lifecycle(db, project_number)),
                "has_unpublished_changes": True,
                "last_mutated_at": now_iso(),
                "last_mutated_by": _actor_label(actor),
            },
            schedule_window=schedule.get("window") or {},
        )
        await persist_project_planning_lifecycle(db, project_number, next_lifecycle)
        await _emit_oppc_plan_stage(
            db,
            stage="audit_written",
            record=spine_record,
            module="jobs_master.assigned_cost_codes",
        )
        await _emit_oppc_plan_stage(
            db,
            stage="dashboard_updated",
            record=spine_record,
            module="services.cost_codes.foundation.recompute_project_progress",
        )
        await _emit_oppc_plan_stage(
            db,
            stage="completed",
            record=spine_record,
            module="routes/cost_codes.py:put_project_assignments",
        )
        return {
            "ok": True,
            "assignments": [serialize_assignment(row, include_financial=True) for row in rows],
            "progress": progress,
            "planning_readiness": planning_readiness,
            "planning_lifecycle": next_lifecycle,
        }

    @api_router.get("/cost-codes/projects/{project_number}/progress")
    async def get_project_progress(project_number: str, actor=Depends(read_dep)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        await _require_cost_codes_read(actor, project_number)
        progress = await recompute_project_progress_snapshot(db, project_number)
        assignments = await load_project_assignments(db, project_number)
        schedule = build_schedule_snapshot(assignments, progress) if assignments else {"window": {}}
        return {
            "project_number": project_number,
            "progress": progress,
            "planning_readiness": build_planning_readiness(assignments),
            "planning_lifecycle": build_planning_lifecycle_snapshot(
                planning_readiness=build_planning_readiness(assignments),
                stored=await load_project_planning_lifecycle(db, project_number),
                schedule_window=schedule.get("window") or {},
            ),
        }

    @api_router.get("/cost-codes/projects/{project_number}/schedule")
    async def get_project_schedule(project_number: str, actor=Depends(read_dep)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        await _require_cost_codes_read(actor, project_number)
        payload = await _resolve_project_schedule(db, project_number)
        payload["can_edit"] = True
        payload["master_control"] = await _is_admin_actor(actor)
        return payload

    @api_router.get("/cost-codes/projects/{project_number}/forecast")
    async def get_project_forecast(
        project_number: str,
        scenario: Optional[str] = None,
        actor=Depends(read_dep),
    ) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        await _require_cost_codes_read(actor, project_number)
        assignments = await load_project_assignments(db, project_number)
        daily_rows = await load_project_cost_code_actuals(db, project_number)
        progress = build_progress_snapshot(assignments, daily_rows) if assignments else None
        forecast_history = await load_project_forecast_history(db, project_number)
        overrides = forecast_history.get("overrides") or []
        schedule = build_schedule_snapshot(assignments, progress, daily_rows=daily_rows, overrides=overrides, scenario_key=scenario)
        comparison = build_schedule_scenario_comparison(
            assignments,
            progress,
            daily_rows=daily_rows,
            anchor_date=(schedule.get("window") or {}).get("anchor_date"),
            scenario_keys=["additional_crew", "weekend_work", "additional_shift"],
            overrides=overrides,
        )
        return {
            "project_number": project_number,
            "schedule": schedule,
            "scenario_comparison": comparison,
            "governance": build_forecast_governance_summary(forecast_history),
            "truth_basis": "canonical_operational_data",
        }

    @api_router.post("/cost-codes/projects/{project_number}/forecast/snapshots")
    async def create_project_forecast_snapshot(
        project_number: str,
        body: ForecastSnapshotBody,
        actor=Depends(read_dep),
    ) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        await _require_cost_codes_manage(actor, project_number)
        assignments = await load_project_assignments(db, project_number)
        daily_rows = await load_project_cost_code_actuals(db, project_number)
        progress = build_progress_snapshot(assignments, daily_rows) if assignments else None
        history = await load_project_forecast_history(db, project_number)
        schedule = build_schedule_snapshot(
            assignments,
            progress,
            daily_rows=daily_rows,
            overrides=history.get("overrides") or [],
            scenario_key=body.scenario_key,
        )
        snapshot = build_forecast_snapshot_record(
            project_number=project_number,
            schedule=schedule,
            scenario_key=(schedule.get("scenario") or {}).get("key") or "calculated_truth",
            scenario_label=(schedule.get("scenario") or {}).get("label") or "Calculated Truth",
            actor_label=_actor_label(actor),
            note=str(body.note or "").strip(),
            source="forecast_snapshot",
        )
        spine_record = await _open_oppc_workflow_lifecycle(
            db,
            workflow="oppc-forecasting",
            project_number=project_number,
            module="routes/cost_codes.py:create_project_forecast_snapshot",
        )
        try:
            await persist_project_forecast_snapshot(db, project_number=project_number, snapshot=snapshot)
        except LookupError as exc:
            await _emit_oppc_plan_stage(
                db,
                workflow="oppc-forecasting",
                stage="audit_written",
                record=spine_record,
                module="jobs_master.oppc_forecast_history",
                status="failed",
                failure_reason=str(exc),
                remediation="Verify the project exists before snapshotting the forecast.",
            )
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        await _emit_oppc_plan_stage(
            db,
            workflow="oppc-forecasting",
            stage="audit_written",
            record=spine_record,
            module="jobs_master.oppc_forecast_history",
        )
        await _emit_oppc_plan_stage(
            db,
            workflow="oppc-forecasting",
            stage="dashboard_updated",
            record=spine_record,
            module="services.cost_codes.schedule_engine.build_schedule_snapshot",
        )
        await _emit_oppc_plan_stage(
            db,
            workflow="oppc-forecasting",
            stage="completed",
            record=spine_record,
            module="routes/cost_codes.py:create_project_forecast_snapshot",
        )
        latest = await _resolve_project_schedule(db, project_number)
        return {"ok": True, "snapshot": snapshot, "forecasting": latest.get("forecasting") or {}, "schedule": latest.get("schedule") or {}}

    @api_router.put("/cost-codes/projects/{project_number}/forecast/overrides/{cost_code}")
    async def upsert_project_forecast_override(
        project_number: str,
        cost_code: str,
        body: ForecastOverrideBody,
        actor=Depends(read_dep),
    ) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        await _require_cost_codes_manage(actor, project_number)
        assignments = await load_project_assignments(db, project_number)
        daily_rows = await load_project_cost_code_actuals(db, project_number)
        progress = build_progress_snapshot(assignments, daily_rows) if assignments else None
        history = await load_project_forecast_history(db, project_number)
        current_schedule = build_schedule_snapshot(assignments, progress, daily_rows=daily_rows, overrides=history.get("overrides") or [])
        current_task = next((row for row in (current_schedule.get("tasks") or []) if str(row.get("code") or "").strip() == str(cost_code or "").strip()), None)
        if not current_task:
            raise HTTPException(status_code=404, detail="Cost code forecast activity not found")
        existing_rows = list(history.get("overrides") or [])
        existing_map = {str(row.get("cost_code") or "").strip(): row for row in existing_rows if str(row.get("cost_code") or "").strip()}
        try:
            override = normalize_forecast_override(
                cost_code=cost_code,
                calculated_start_date=str(current_task.get("forecast_start_date") or ""),
                calculated_finish_date=str(current_task.get("forecast_finish_date") or ""),
                adjusted_start_date=str(body.adjusted_start_date or current_task.get("forecast_start_date") or "").strip(),
                adjusted_finish_date=str(body.adjusted_finish_date or "").strip(),
                reason=str(body.reason or "").strip(),
                actor_label=_actor_label(actor),
                actor_role=_actor_role(actor),
                evidence_links=body.evidence_links,
                note=str(body.note or "").strip(),
                existing=existing_map.get(str(cost_code or "").strip()),
                status="active",
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        existing_map[str(cost_code or "").strip()] = override
        ordered = [existing_map[key] for key in sorted(existing_map)]
        spine_record = await _open_oppc_workflow_lifecycle(
            db,
            workflow="oppc-forecasting",
            project_number=project_number,
            module="routes/cost_codes.py:upsert_project_forecast_override",
        )
        try:
            await persist_project_forecast_overrides(db, project_number=project_number, overrides=ordered)
        except LookupError as exc:
            await _emit_oppc_plan_stage(
                db,
                workflow="oppc-forecasting",
                stage="audit_written",
                record=spine_record,
                module="jobs_master.oppc_forecast_overrides",
                status="failed",
                failure_reason=str(exc),
                remediation="Verify the project exists before saving forecast overrides.",
            )
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        await _emit_oppc_plan_stage(
            db,
            workflow="oppc-forecasting",
            stage="audit_written",
            record=spine_record,
            module="jobs_master.oppc_forecast_overrides",
        )
        await _emit_oppc_plan_stage(
            db,
            workflow="oppc-forecasting",
            stage="dashboard_updated",
            record=spine_record,
            module="services.cost_codes.schedule_engine.build_schedule_snapshot",
        )
        await _emit_oppc_plan_stage(
            db,
            workflow="oppc-forecasting",
            stage="completed",
            record=spine_record,
            module="routes/cost_codes.py:upsert_project_forecast_override",
        )
        latest = await _resolve_project_schedule(db, project_number)
        return {"ok": True, "override": override, "forecasting": latest.get("forecasting") or {}, "schedule": latest.get("schedule") or {}}

    @api_router.put("/cost-codes/projects/{project_number}/schedule")
    async def put_project_schedule(project_number: str, body: ProjectScheduleBody, actor=Depends(read_dep)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        await _require_cost_codes_manage(actor, project_number)
        existing = await load_project_assignments(db, project_number)
        if not existing:
            raise HTTPException(status_code=404, detail="Project has no assigned cost codes to schedule")
        existing_map = {str(row.get("code") or "").strip(): dict(row) for row in existing if str(row.get("code") or "").strip()}
        for task in body.tasks:
            code = str(task.code or "").strip()
            if code not in existing_map:
                raise HTTPException(status_code=404, detail=f"Cost code {code} is not assigned to this project")
            current = dict(existing_map[code])
            current.update({
                "schedule_start_date": task.schedule_start_date or "",
                "duration_days": int(task.duration_days or 1),
                "predecessor_codes": list(task.predecessor_codes or []),
                "cpm_activity_id": task.cpm_activity_id or current.get("cpm_activity_id") or "",
                "cpm_activity_name": task.cpm_activity_name or current.get("cpm_activity_name") or "",
                "schedule_phase": task.schedule_phase or current.get("schedule_phase") or "",
                "planned_performer": task.planned_performer or current.get("planned_performer") or "",
                "notes": task.notes if task.notes is not None else current.get("notes") or "",
            })
            existing_map[code] = normalize_job_assignment(current, None, current)
        rows = [existing_map[str(row.get("code") or "").strip()] for row in existing if str(row.get("code") or "").strip() in existing_map]
        for idx, row in enumerate(rows):
            row["sort_order"] = idx
        spine_record = await _open_oppc_plan_lifecycle(
            db,
            project_number=project_number,
            module="routes/cost_codes.py:put_project_schedule",
        )
        try:
            await persist_project_assignments(db, project_number, rows)
        except LookupError as exc:
            await _emit_oppc_plan_stage(
                db,
                stage="audit_written",
                record=spine_record,
                module="jobs_master.assigned_cost_codes",
                status="failed",
                failure_reason=str(exc),
                remediation="Verify the project exists before updating schedule fields.",
            )
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        payload = await _resolve_project_schedule(db, project_number)
        payload["ok"] = True
        payload["can_edit"] = True
        payload["master_control"] = await _is_admin_actor(actor)
        next_lifecycle = build_planning_lifecycle_snapshot(
            planning_readiness=payload.get("planning_readiness") or {},
            stored={
                **(await load_project_planning_lifecycle(db, project_number)),
                "has_unpublished_changes": True,
                "last_mutated_at": now_iso(),
                "last_mutated_by": _actor_label(actor),
            },
            schedule_window=(payload.get("schedule") or {}).get("window") or {},
        )
        await persist_project_planning_lifecycle(db, project_number, next_lifecycle)
        payload["planning_lifecycle"] = next_lifecycle
        await _emit_oppc_plan_stage(
            db,
            stage="audit_written",
            record=spine_record,
            module="jobs_master.assigned_cost_codes",
        )
        await _emit_oppc_plan_stage(
            db,
            stage="dashboard_updated",
            record=spine_record,
            module="services.cost_codes.schedule_engine.build_schedule_snapshot",
        )
        await _emit_oppc_plan_stage(
            db,
            stage="completed",
            record=spine_record,
            module="routes/cost_codes.py:put_project_schedule",
        )
        return payload

    @api_router.post("/cost-codes/projects/{project_number}/planning-lifecycle/publish")
    async def publish_project_schedule(project_number: str, body: PlanningPublishBody, actor=Depends(read_dep)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        await _require_cost_codes_manage(actor, project_number)
        payload = await _resolve_project_schedule(db, project_number)
        planning_readiness = payload.get("planning_readiness") or {}
        if int(planning_readiness.get("assignment_count") or 0) <= 0:
            raise HTTPException(status_code=404, detail="Project has no assigned cost codes to publish")
        if planning_readiness.get("status") != "ready":
            raise HTTPException(status_code=409, detail="Planning foundation is incomplete; fix required fields before publishing")
        spine_record = await _open_oppc_plan_lifecycle(
            db,
            project_number=project_number,
            module="routes/cost_codes.py:publish_project_schedule",
        )
        next_lifecycle = build_planning_lifecycle_snapshot(
            planning_readiness=planning_readiness,
            stored={
                **(await load_project_planning_lifecycle(db, project_number)),
                "published_at": now_iso(),
                "published_by": _actor_label(actor),
                "last_mutated_at": now_iso(),
                "last_mutated_by": _actor_label(actor),
                "has_unpublished_changes": False,
                "publish_note": str(body.note or "").strip(),
            },
            schedule_window=(payload.get("schedule") or {}).get("window") or {},
        )
        try:
            await persist_project_planning_lifecycle(db, project_number, next_lifecycle)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        payload["planning_lifecycle"] = next_lifecycle
        await _emit_oppc_plan_stage(
            db,
            stage="audit_written",
            record=spine_record,
            module="jobs_master.oppc_planning_lifecycle",
        )
        await _emit_oppc_plan_stage(
            db,
            stage="dashboard_updated",
            record=spine_record,
            module="routes/cost_codes.py:publish_project_schedule",
        )
        await _emit_oppc_plan_stage(
            db,
            stage="completed",
            record=spine_record,
            module="routes/cost_codes.py:publish_project_schedule",
        )
        return {"ok": True, **payload}

    @api_router.get("/cost-codes/projects/{project_number}/weekly-rollover/preview")
    async def preview_weekly_rollover(project_number: str, actor=Depends(read_dep)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        await _require_cost_codes_read(actor, project_number)
        raw_assignments = await load_project_assignments(db, project_number)
        payload = await _resolve_project_schedule(db, project_number)
        preview = build_weekly_rollover_preview(
            raw_assignments,
            payload.get("progress"),
            payload.get("planning_readiness") or {},
            anchor_date=(payload.get("schedule") or {}).get("window", {}).get("anchor_date"),
        )
        return {
            "ok": True,
            "project_number": project_number,
            "planning_readiness": payload.get("planning_readiness") or {},
            "planning_lifecycle": payload.get("planning_lifecycle") or {},
            "weekly_rollover": _public_rollover_payload(preview),
        }

    @api_router.post("/cost-codes/projects/{project_number}/weekly-rollover/apply")
    async def apply_weekly_rollover(project_number: str, body: WeeklyRolloverApplyBody, actor=Depends(read_dep)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        await _require_cost_codes_manage(actor, project_number)
        if str(body.confirm or "").strip() != "APPLY_WEEKLY_ROLLOVER":
            raise HTTPException(status_code=422, detail="confirm must equal APPLY_WEEKLY_ROLLOVER")
        raw_assignments = await load_project_assignments(db, project_number)
        payload = await _resolve_project_schedule(db, project_number)
        preview = build_weekly_rollover_preview(
            raw_assignments,
            payload.get("progress"),
            payload.get("planning_readiness") or {},
            anchor_date=(payload.get("schedule") or {}).get("window", {}).get("anchor_date"),
        )
        if preview.get("status") != "ready":
            blocked_reason = preview.get("blocked_reason") or "weekly_rollover_blocked"
            raise HTTPException(status_code=409, detail=blocked_reason)
        spine_record = await _open_oppc_workflow_lifecycle(
            db,
            workflow="oppc-weekly-rollover",
            project_number=project_number,
            module="routes/cost_codes.py:apply_weekly_rollover",
        )
        try:
            await persist_project_assignments(db, project_number, preview.get("updated_assignments") or [])
        except LookupError as exc:
            await _emit_oppc_plan_stage(
                db,
                workflow="oppc-weekly-rollover",
                stage="audit_written",
                record=spine_record,
                module="jobs_master.assigned_cost_codes",
                status="failed",
                failure_reason=str(exc),
                remediation="Verify the project exists before applying weekly rollover.",
            )
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        refreshed_payload = await _resolve_project_schedule(db, project_number)
        refreshed_lifecycle = build_planning_lifecycle_snapshot(
            planning_readiness=refreshed_payload.get("planning_readiness") or {},
            stored={
                **(await load_project_planning_lifecycle(db, project_number)),
                "has_unpublished_changes": True,
                "last_mutated_at": now_iso(),
                "last_mutated_by": _actor_label(actor),
                "last_rollover_anchor_date": preview.get("rollover_anchor_date") or "",
                "last_rollover_note": str(body.note or "").strip(),
            },
            schedule_window=(preview.get("next_schedule") or {}).get("window") or {},
        )
        await persist_project_planning_lifecycle(db, project_number, refreshed_lifecycle)
        await db.jobs_master.update_one(
            {"project_number": project_number},
            {"$set": {
                "oppc_last_weekly_rollover": {
                    "rollover_anchor_date": preview.get("rollover_anchor_date") or "",
                    "changed_count": int(preview.get("changed_count") or 0),
                    "action_count": int(preview.get("action_count") or 0),
                    "summary": dict(preview.get("summary") or {}),
                    "applied_at": now_iso(),
                    "applied_by": _actor_label(actor),
                    "note": str(body.note or "").strip(),
                }
            }},
            upsert=False,
        )
        refreshed_payload["planning_lifecycle"] = refreshed_lifecycle
        refreshed_payload["weekly_rollover"] = _public_rollover_payload(preview)
        await _emit_oppc_plan_stage(
            db,
            workflow="oppc-weekly-rollover",
            stage="audit_written",
            record=spine_record,
            module="jobs_master.oppc_last_weekly_rollover",
        )
        await _emit_oppc_plan_stage(
            db,
            workflow="oppc-weekly-rollover",
            stage="dashboard_updated",
            record=spine_record,
            module="services.cost_codes.schedule_engine.build_schedule_snapshot",
        )
        await _emit_oppc_plan_stage(
            db,
            workflow="oppc-weekly-rollover",
            stage="completed",
            record=spine_record,
            module="routes/cost_codes.py:apply_weekly_rollover",
        )
        return {"ok": True, **refreshed_payload}

    @api_router.get("/cost-codes/projects/{project_number}/schedule/dot-report.pdf")
    async def export_project_schedule_pdf(project_number: str, actor=Depends(read_dep)):
        await _ensure_spine_indexes(db)
        await _require_cost_codes_read(actor, project_number)
        payload = await _resolve_project_schedule(db, project_number)
        pdf = render_dot_schedule_pdf(project_number, payload["schedule"])
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="DOT_Schedule_{project_number}.pdf"'},
        )

    @api_router.post("/cost-codes/projects/{project_number}/progress/recompute")
    async def recompute_project_progress(project_number: str, actor=Depends(read_dep)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        await _require_cost_codes_manage(actor, project_number)
        progress = await recompute_project_progress_snapshot(db, project_number)
        return {"ok": True, "project_number": project_number, "progress": progress}

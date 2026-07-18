"""Enterprise Spine · Scheduling & Cost-Code Module foundation.

Universal Cost Registry (Admin), PM project assignments, Daily Report
quantity tracking helpers, and additive job progress calculations.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from pm_auth import compute_pm_scope
from services.cost_codes import get_provider
from services.cost_codes.foundation import (
    ALLOWED_UNITS,
    build_progress_snapshot,
    build_project_cost_code_option,
    load_project_assignments,
    load_project_cost_code_actuals,
    persist_project_assignments,
    recompute_project_progress as recompute_project_progress_snapshot,
    normalize_job_assignment,
    normalize_registry_item,
    serialize_assignment,
)
from services.cost_codes.schedule_engine import build_schedule_snapshot, render_dot_schedule_pdf

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


async def _resolve_project_schedule(db, project_number: str) -> Dict[str, Any]:
    assignments = await load_project_assignments(db, project_number)
    progress = build_progress_snapshot(assignments, await load_project_cost_code_actuals(db, project_number)) if assignments else None
    schedule = build_schedule_snapshot(assignments, progress)
    return {
        "project_number": project_number,
        "assignments": [serialize_assignment(row, include_financial=False) for row in assignments],
        "progress": progress,
        "schedule": schedule,
        "monday_look_behind_ready": True,
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

    @api_router.get("/cost-codes/registry")
    async def list_registry(actor=Depends(read_dep)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        rows = await _load_registry(db)
        return {"items": rows, "units": sorted(ALLOWED_UNITS)}

    @api_router.post("/cost-codes/registry")
    async def upsert_registry(body: CostRegistryItemIn, actor=Depends(require_admin)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        if not await _is_admin_actor(actor):
            raise HTTPException(status_code=403, detail="Admin login required")
        item = normalize_registry_item(body.model_dump())
        await db[REGISTRY_COLLECTION].update_one({"code": item["code"]}, {"$set": item}, upsert=True)
        return {"ok": True, "item": item}

    @api_router.put("/cost-codes/registry/bulk-replace")
    async def replace_registry(body: CostRegistryBulkBody, actor=Depends(require_admin)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        if not await _is_admin_actor(actor):
            raise HTTPException(status_code=403, detail="Admin login required")
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
    async def get_project_assignments(project_number: str) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        assignments = await load_project_assignments(db, project_number)
        progress = await recompute_project_progress_snapshot(db, project_number)
        return {
            "project_number": project_number,
            "assignments": [serialize_assignment(row, include_financial=False) for row in assignments],
            "progress": progress,
            "supports_future_cpm": True,
            "financials_included": False,
        }

    @api_router.put("/cost-codes/projects/{project_number}/assignments")
    async def put_project_assignments(project_number: str, body: ProjectAssignmentsBody, actor=Depends(read_dep)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        if isinstance(actor, dict) and actor.get("role") == "hr":
            raise HTTPException(status_code=403, detail="PM or admin access required")
        scope = await compute_pm_scope(db, actor)
        if not scope.allows(project_number):
            raise HTTPException(status_code=403, detail="Project not in PM scope")
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
        try:
            await persist_project_assignments(db, project_number, rows)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        progress = await recompute_project_progress_snapshot(db, project_number)
        return {
            "ok": True,
            "assignments": [serialize_assignment(row, include_financial=True) for row in rows],
            "progress": progress,
        }

    @api_router.get("/cost-codes/projects/{project_number}/progress")
    async def get_project_progress(project_number: str) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        progress = await recompute_project_progress_snapshot(db, project_number)
        return {"project_number": project_number, "progress": progress}

    @api_router.get("/cost-codes/projects/{project_number}/schedule")
    async def get_project_schedule(project_number: str, actor=Depends(read_dep)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        if _actor_role(actor) == "hr":
            raise HTTPException(status_code=403, detail="PM or admin access required")
        scope = await compute_pm_scope(db, actor)
        if not scope.allows(project_number):
            raise HTTPException(status_code=403, detail="Project not in PM scope")
        payload = await _resolve_project_schedule(db, project_number)
        payload["can_edit"] = True
        payload["master_control"] = await _is_admin_actor(actor)
        return payload

    @api_router.put("/cost-codes/projects/{project_number}/schedule")
    async def put_project_schedule(project_number: str, body: ProjectScheduleBody, actor=Depends(read_dep)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        if _actor_role(actor) == "hr":
            raise HTTPException(status_code=403, detail="PM or admin access required")
        scope = await compute_pm_scope(db, actor)
        if not scope.allows(project_number):
            raise HTTPException(status_code=403, detail="Project not in PM scope")
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
        try:
            await persist_project_assignments(db, project_number, rows)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        payload = await _resolve_project_schedule(db, project_number)
        payload["ok"] = True
        payload["can_edit"] = True
        payload["master_control"] = await _is_admin_actor(actor)
        return payload

    @api_router.get("/cost-codes/projects/{project_number}/schedule/dot-report.pdf")
    async def export_project_schedule_pdf(project_number: str, actor=Depends(read_dep)):
        await _ensure_spine_indexes(db)
        if _actor_role(actor) == "hr":
            raise HTTPException(status_code=403, detail="PM or admin access required")
        scope = await compute_pm_scope(db, actor)
        if not scope.allows(project_number):
            raise HTTPException(status_code=403, detail="Project not in PM scope")
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
        if isinstance(actor, dict) and actor.get("role") == "hr":
            raise HTTPException(status_code=403, detail="PM or admin access required")
        scope = await compute_pm_scope(db, actor)
        if not scope.allows(project_number):
            raise HTTPException(status_code=403, detail="Project not in PM scope")
        progress = await recompute_project_progress_snapshot(db, project_number)
        return {"ok": True, "project_number": project_number, "progress": progress}

"""Enterprise Spine · Scheduling & Cost-Code Module foundation.

Universal Cost Registry (Admin), PM project assignments, Daily Report
quantity tracking helpers, and additive job progress calculations.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from pm_auth import compute_pm_scope
from services.cost_codes import get_provider
from services.cost_codes.foundation import (
    ALLOWED_UNITS,
    build_progress_snapshot,
    normalize_job_assignment,
    normalize_registry_item,
    now_iso,
)

REGISTRY_COLLECTION = "cost_code_registry"


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
    cpm_activity_id: Optional[str] = ""
    cpm_activity_name: Optional[str] = ""
    schedule_phase: Optional[str] = ""
    notes: Optional[str] = ""


class ProjectAssignmentsBody(BaseModel):
    assignments: List[ProjectAssignmentIn] = Field(default_factory=list)


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


async def _registry_index(db) -> Dict[str, Dict[str, Any]]:
    rows = await _load_registry(db)
    return {str(row.get("code") or "").strip(): row for row in rows if str(row.get("code") or "").strip()}


async def _assigned_cost_codes_for_project(db, project_number: str) -> List[Dict[str, Any]]:
    job = await db.jobs_master.find_one({"project_number": str(project_number or "").strip()}, {"_id": 0, "assigned_cost_codes": 1})
    rows = (job or {}).get("assigned_cost_codes") or []
    clean: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        item = dict(row)
        item.setdefault("sort_order", idx)
        clean.append(item)
    clean.sort(key=lambda r: (int(r.get("sort_order") or 0), str(r.get("code") or "")))
    return clean


async def _load_project_progress(db, project_number: str) -> Dict[str, Any]:
    assignments = await _assigned_cost_codes_for_project(db, project_number)
    reports = await db.daily_reports.find(
        {"project_number": str(project_number or "").strip()},
        {"_id": 0, "cost_code_quantities": 1},
    ).to_list(5000)
    daily_rows: List[Dict[str, Any]] = []
    for report in reports:
        rows = report.get("cost_code_quantities") or []
        daily_rows.extend([row for row in rows if isinstance(row, dict)])
    return build_progress_snapshot(assignments, daily_rows)


async def _persist_project_progress(db, project_number: str) -> Dict[str, Any]:
    progress = await _load_project_progress(db, project_number)
    await db.jobs_master.update_one(
        {"project_number": str(project_number or "").strip()},
        {"$set": {
            "cost_code_progress": progress,
            "cost_code_progress_percent": progress.get("overall_percent_complete", 0.0),
            "cost_code_progress_updated_at": now_iso(),
            "schedule_cost_spine_ready": True,
            "dot_cpm_ready": {
                "fdot": True,
                "txdot": True,
                "foundation_completed_at": now_iso(),
            },
        }},
        upsert=False,
    )
    return progress


async def _ensure_spine_indexes(db) -> None:
    await db[REGISTRY_COLLECTION].create_index("code", unique=True)
    await db.jobs_master.create_index("project_number")
    await db.daily_reports.create_index([("project_number", 1), ("report_date", 1)])


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
        codes = await provider.list_for_project(db, project_number)
        assigned = await _assigned_cost_codes_for_project(db, project_number)
        if assigned:
            codes = [
                {
                    "code": row.get("code"),
                    "description": row.get("item_name") or row.get("description") or row.get("code"),
                    "active": row.get("active", True),
                    "unit": row.get("unit_of_measure") or row.get("unit"),
                    "bid_quantity": row.get("bid_quantity") or 0,
                    "bid_unit_price": row.get("bid_unit_price") or 0,
                    "target_man_hours": row.get("target_man_hours") or 0,
                    "cpm_activity_id": row.get("cpm_activity_id") or "",
                    "cpm_activity_name": row.get("cpm_activity_name") or "",
                    "schedule_phase": row.get("schedule_phase") or "",
                }
                for row in assigned
            ]
        return {"project_number": project_number, "codes": codes}

    @api_router.get("/cost-codes/projects/{project_number}/assignments")
    async def get_project_assignments(project_number: str) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        assignments = await _assigned_cost_codes_for_project(db, project_number)
        progress = await _load_project_progress(db, project_number)
        return {
            "project_number": project_number,
            "assignments": assignments,
            "progress": progress,
            "supports_future_cpm": True,
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
        rows: List[Dict[str, Any]] = []
        for idx, raw in enumerate(body.assignments):
            item = registry.get(str(raw.code).strip())
            merged = normalize_job_assignment(raw.model_dump(), item)
            merged["sort_order"] = idx
            rows.append(merged)
        await db.jobs_master.update_one(
            {"project_number": str(project_number or "").strip()},
            {"$set": {
                "assigned_cost_codes": rows,
                "cost_codes": [
                    {"code": row.get("code"), "description": row.get("item_name"), "active": True}
                    for row in rows
                ],
                "schedule_cost_spine_ready": True,
                "dot_cpm_ready": {"fdot": True, "txdot": True, "updated_at": now_iso()},
                "updated_at": now_iso(),
            }},
            upsert=False,
        )
        progress = await _persist_project_progress(db, project_number)
        return {"ok": True, "assignments": rows, "progress": progress}

    @api_router.get("/cost-codes/projects/{project_number}/progress")
    async def get_project_progress(project_number: str) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        progress = await _load_project_progress(db, project_number)
        return {"project_number": project_number, "progress": progress}

    @api_router.post("/cost-codes/projects/{project_number}/progress/recompute")
    async def recompute_project_progress(project_number: str, actor=Depends(read_dep)) -> Dict[str, Any]:
        await _ensure_spine_indexes(db)
        if isinstance(actor, dict) and actor.get("role") == "hr":
            raise HTTPException(status_code=403, detail="PM or admin access required")
        scope = await compute_pm_scope(db, actor)
        if not scope.allows(project_number):
            raise HTTPException(status_code=403, detail="Project not in PM scope")
        progress = await _persist_project_progress(db, project_number)
        return {"ok": True, "project_number": project_number, "progress": progress}

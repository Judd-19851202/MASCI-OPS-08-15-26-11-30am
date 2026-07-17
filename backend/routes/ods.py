"""ODS-001 · Read + management API routes.

Additive `/api/ods/*` surface. Everything is behind the `ODS_ENABLED`
feature flag — with the flag OFF, endpoints still respond so tooling can
probe them, but return `enabled: false` and never touch the spine.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Path, Query
from pydantic import BaseModel, Field

from services.ods_spine import (
    ods_enabled, dr_v2_spine_emission_enabled,
    FACT_TYPES, SOURCE_TYPES,
    compute_kpi_snapshot, get_snapshot,
    ingest_dr_v2_draft, list_facts, project_summary,
)
from services.cost_codes.foundation import build_ods_project_cost_code_doc, load_project_assignments
from services.ods_spine.store import (
    COLL_PROJECT_CFG, ensure_indexes,
)


TENANT_DEFAULT = "masci"


class ProjectCostCode(BaseModel):
    code: str
    description: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    planned_qty: Optional[float] = None
    phase: Optional[str] = None
    area: Optional[str] = None
    active: bool = True
    sort_order: Optional[int] = None
    notes: Optional[str] = None


class ProjectOperationalConfigPayload(BaseModel):
    project_id: str
    tenant_id: str = Field(default=TENANT_DEFAULT)
    cost_codes: List[ProjectCostCode] = Field(default_factory=list)
    updated_by: Optional[str] = None


def register_ods_routes(api_router: APIRouter, db) -> None:
    """Attach /api/ods/* — call ONCE from server.py."""

    async def _boot_indexes():
        try:
            await ensure_indexes(db)
        except Exception:  # noqa: BLE001
            pass

    setattr(api_router, "_ods_boot_indexes", _boot_indexes)

    # ----- Meta -------------------------------------------------------
    @api_router.get("/ods/meta")
    async def ods_meta() -> Dict[str, Any]:
        from services.ai_gateway import provider_meta_snapshot
        return {
            "enabled": ods_enabled(),
            "dr_v2_emission": dr_v2_spine_emission_enabled(),
            "fact_types": list(FACT_TYPES),
            "source_types": list(SOURCE_TYPES),
            "ai_gateway": provider_meta_snapshot(),
        }

    # ----- Facts read -------------------------------------------------
    @api_router.get("/ods/facts")
    async def ods_list_facts(
        project_id: Optional[str] = Query(default=None),
        fact_type: Optional[str] = Query(default=None),
        date_from: Optional[str] = Query(default=None),
        date_to: Optional[str] = Query(default=None),
        limit: int = Query(default=200, ge=1, le=1000),
    ) -> Dict[str, Any]:
        if not ods_enabled():
            return {"enabled": False, "facts": []}
        facts = await list_facts(
            db, tenant_id=TENANT_DEFAULT, project_id=project_id,
            fact_type=fact_type, date_from=date_from, date_to=date_to, limit=limit,
        )
        return {"enabled": True, "count": len(facts), "facts": facts}

    # ----- Project summary -------------------------------------------
    @api_router.get("/ods/projects/{project_id}/summary")
    async def ods_project_summary(
        project_id: str = Path(...),
        date_from: Optional[str] = Query(default=None),
        date_to: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        if not ods_enabled():
            return {"enabled": False, "summary": None}
        s = await project_summary(
            db, tenant_id=TENANT_DEFAULT, project_id=project_id,
            date_from=date_from, date_to=date_to,
        )
        return {"enabled": True, "summary": s}

    # ----- Snapshot: read + recompute --------------------------------
    @api_router.get("/ods/snapshots")
    async def ods_get_snapshot(
        project_id: str = Query(...),
        date: str = Query(...),
        window: str = Query(default="day"),
    ) -> Dict[str, Any]:
        if not ods_enabled():
            return {"enabled": False, "snapshot": None}
        s = await get_snapshot(db, tenant_id=TENANT_DEFAULT, project_id=project_id,
                               date=date, window=window)
        return {"enabled": True, "snapshot": s}

    @api_router.post("/ods/snapshots/recompute")
    async def ods_recompute(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        if not ods_enabled():
            raise HTTPException(status_code=409, detail="ODS_ENABLED is off")
        project_id = str(payload.get("project_id") or "")
        date = str(payload.get("date") or "")
        window = str(payload.get("window") or "day")
        if not project_id or not date:
            raise HTTPException(status_code=400, detail="project_id and date required")
        snap = await compute_kpi_snapshot(
            db, tenant_id=TENANT_DEFAULT, project_id=project_id,
            date=date, window=window,
        )
        return {"ok": True, "snapshot": snap}

    # ----- Project operational config (cost codes) --------------------
    @api_router.get("/ods/projects/{project_id}/config")
    async def ods_get_project_config(project_id: str = Path(...)) -> Dict[str, Any]:
        doc = await db[COLL_PROJECT_CFG].find_one({"project_id": project_id}, {"_id": 0})
        if doc:
            return {"project_id": project_id, "config": doc}
        assignments = await load_project_assignments(db, project_id)
        if not assignments:
            return {"project_id": project_id, "config": None}
        projected = build_ods_project_cost_code_doc(project_number=project_id, assignments=assignments, tenant_id=TENANT_DEFAULT, version=1)
        await db[COLL_PROJECT_CFG].update_one({"project_id": project_id}, {"$set": projected}, upsert=True)
        return {"project_id": project_id, "config": projected}

    @api_router.put("/ods/projects/{project_id}/config")
    async def ods_put_project_config(
        project_id: str = Path(...),
        payload: ProjectOperationalConfigPayload = Body(...),
    ) -> Dict[str, Any]:
        if not ods_enabled():
            raise HTTPException(status_code=409, detail="ODS_ENABLED is off")
        if payload.project_id != project_id:
            raise HTTPException(status_code=400, detail="project_id mismatch")
        assignments = await load_project_assignments(db, project_id)
        if not assignments:
            raise HTTPException(status_code=404, detail="No canonical assigned_cost_codes found for this project")
        existing = await db[COLL_PROJECT_CFG].find_one({"project_id": project_id}, {"_id": 0, "version": 1, "tenant_id": 1})
        doc = build_ods_project_cost_code_doc(
            project_number=project_id,
            assignments=assignments,
            tenant_id=str((existing or {}).get("tenant_id") or payload.tenant_id or TENANT_DEFAULT),
            version=int((existing or {}).get("version") or 0) + 1,
        )
        doc["sync_requested_by"] = payload.updated_by or "system"
        doc["sync_mode"] = "canonical_projection"
        await db[COLL_PROJECT_CFG].update_one(
            {"project_id": project_id}, {"$set": doc}, upsert=True,
        )
        return {
            "ok": True,
            "version": doc["version"],
            "project_id": project_id,
            "source_authority": doc["source_authority"],
            "projection_locked": True,
            "cost_code_count": len(doc.get("cost_codes") or []),
        }

    # ----- Manual ingest / regenerate for a DR-V2 draft --------------
    @api_router.post("/ods/ingest/dr-v2/{report_id}")
    async def ods_ingest_dr_v2(report_id: str = Path(...)) -> Dict[str, Any]:
        if not ods_enabled():
            raise HTTPException(status_code=409, detail="ODS_ENABLED is off")
        draft = await db["dr_v2_drafts"].find_one({"report_id": report_id}, {"_id": 0})
        if not draft:
            raise HTTPException(status_code=404, detail="draft not found")
        result = await ingest_dr_v2_draft(db, draft, actor="manual", trigger="manual")
        if result.get("ok") and result.get("project_id"):
            await compute_kpi_snapshot(
                db, tenant_id=TENANT_DEFAULT,
                project_id=result["project_id"], date=result["date"],
            )
        return result


def _now() -> str:
    from services.ods_spine.model import now_iso
    return now_iso()

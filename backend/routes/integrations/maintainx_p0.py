"""
MaintainX P0-A/P0-B read-first admin routes.

Mounted into the existing Integration Center router via
`build_integrations_router(...)`.

ALL routes here are:
  • Admin-strict
  • Read-first (no writes to MaintainX, equipment_master, asset_mappings)
  • The `/dryrun` route may OPTIONALLY save the produced report dict
    into a single audit collection `maintainx_dryrun_reports` if the
    caller passes ?save=true. That is the ONLY write surface.

Endpoints:
  GET  /api/admin/maintainx/p0/config            — env/config view (api key MASKED)
  POST /api/admin/maintainx/p0/test              — probe connectivity (no DB write)
  POST /api/admin/maintainx/p0/dryrun?save=…     — full read-first pull + match + duplicate-risk
  GET  /api/admin/maintainx/p0/dryrun-reports    — list saved reports (most-recent first)
  GET  /api/admin/maintainx/p0/dryrun-reports/{id}
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from services.maintainx_client import MaintainxClient, MaintainxConfig
from services.maintainx_asset_sync import run_asset_dryrun

logger = logging.getLogger(__name__)


def register_maintainx_p0_routes(api_router: APIRouter, db, require_admin) -> None:

    @api_router.get(
        "/admin/maintainx/p0/config",
        dependencies=[Depends(require_admin)],
    )
    async def maintainx_p0_config():
        return MaintainxConfig.from_env().public_view()

    @api_router.post(
        "/admin/maintainx/p0/test",
        dependencies=[Depends(require_admin)],
    )
    async def maintainx_p0_test_connection():
        client = MaintainxClient()
        return await client.test_connection()

    @api_router.post(
        "/admin/maintainx/p0/dryrun",
        dependencies=[Depends(require_admin)],
    )
    async def maintainx_p0_dryrun(
        save: bool = False,
        page_size: int = 100,
        max_pages: int = 50,
    ):
        return await run_asset_dryrun(
            db,
            page_size=page_size,
            max_pages=max_pages,
            save_report=bool(save),
            triggered_by="admin",
        )

    @api_router.get(
        "/admin/maintainx/p0/dryrun-reports",
        dependencies=[Depends(require_admin)],
    )
    async def maintainx_p0_list_reports(limit: int = 20):
        limit = max(1, min(int(limit or 20), 200))
        cursor = db.maintainx_dryrun_reports.find(
            {}, {"_id": 0, "results": 0, "missing_in_maintainx": 0},
        ).sort("started_at", -1)
        return await cursor.to_list(limit)

    @api_router.get(
        "/admin/maintainx/p0/dryrun-reports/{run_id}",
        dependencies=[Depends(require_admin)],
    )
    async def maintainx_p0_get_report(run_id: str):
        doc = await db.maintainx_dryrun_reports.find_one({"id": run_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Dry-run report not found")
        return doc


__all__ = ["register_maintainx_p0_routes"]

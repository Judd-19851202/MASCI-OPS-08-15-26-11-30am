"""
Integration Center · logs.py — sync log + error log query endpoints.

Read-only views into the centralized log streams written by service
stubs, webhook receivers, and CSV importers. Filter by provider /
status / time window.
"""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException


def register_log_routes(api_router: APIRouter, db, require_admin) -> None:

    @api_router.get(
        "/admin/integrations/sync-logs", dependencies=[Depends(require_admin)],
    )
    async def list_sync_logs(
        integration: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 200,
    ):
        q: dict = {}
        if integration:
            q["integration"] = integration
        if status:
            q["status"] = status
        limit = max(1, min(limit, 1000))
        cursor = db.integration_sync_logs.find(q, {"_id": 0}).sort("started_at", -1)
        return await cursor.to_list(limit)

    @api_router.get(
        "/admin/integrations/error-logs", dependencies=[Depends(require_admin)],
    )
    async def list_error_logs(
        integration: Optional[str] = None,
        kind: Optional[str] = None,
        resolved: Optional[bool] = None,
        limit: int = 200,
    ):
        q: dict = {}
        if integration:
            q["integration"] = integration
        if kind:
            q["kind"] = kind
        if resolved is not None:
            q["resolved"] = bool(resolved)
        limit = max(1, min(limit, 1000))
        cursor = db.integration_error_logs.find(q, {"_id": 0}).sort("occurred_at", -1)
        return await cursor.to_list(limit)

    @api_router.post(
        "/admin/integrations/error-logs/{log_id}/resolve",
        dependencies=[Depends(require_admin)],
    )
    async def resolve_error_log(log_id: str):
        res = await db.integration_error_logs.update_one(
            {"id": log_id}, {"$set": {"resolved": True}},
        )
        if res.matched_count == 0:
            raise HTTPException(404, "Not found")
        return {"ok": True}


__all__ = ["register_log_routes"]

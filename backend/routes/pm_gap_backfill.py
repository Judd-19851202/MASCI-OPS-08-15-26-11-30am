from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from lib.pm_gap_backfill import apply_pm_gap_backfill, preview_pm_gap_backfill


def build_pm_gap_backfill_router(db, require_admin_strict_dep) -> APIRouter:
    router = APIRouter(tags=["pm-gap-backfill"])

    @router.get(
        "/api/admin/pm-gap-backfill/preview",
        dependencies=[Depends(require_admin_strict_dep)],
    )
    async def preview_backfill() -> dict:
        return await preview_pm_gap_backfill(db)

    @router.post(
        "/api/admin/pm-gap-backfill/apply",
        dependencies=[Depends(require_admin_strict_dep)],
    )
    async def apply_backfill() -> dict:
        preview = await preview_pm_gap_backfill(db)
        if int(preview.get("count", 0)) == 0:
            raise HTTPException(status_code=409, detail="No PM gap backfill needed.")
        return await apply_pm_gap_backfill(db)

    return router


__all__ = ["build_pm_gap_backfill_router"]
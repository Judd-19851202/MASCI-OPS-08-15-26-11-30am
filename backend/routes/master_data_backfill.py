from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from lib.master_data_backfill import apply_master_data_backfill, preview_master_data_backfill


def build_master_data_backfill_router(db, require_admin_strict_dep) -> APIRouter:
    router = APIRouter(tags=["master-data-backfill"])

    @router.get(
        "/api/admin/master-data-backfill/preview",
        dependencies=[Depends(require_admin_strict_dep)],
    )
    async def preview_backfill() -> dict:
        return {"ok": True, **(await preview_master_data_backfill(db))}

    @router.post(
        "/api/admin/master-data-backfill/apply",
        dependencies=[Depends(require_admin_strict_dep)],
    )
    async def apply_backfill() -> dict:
        preview = await preview_master_data_backfill(db)
        if (
            int(preview["summary"].get("equipment_missing_unit_number", 0)) == 0
            and int(preview["summary"].get("employees_missing_employee_id", 0)) == 0
        ):
            raise HTTPException(status_code=409, detail="No master-data backfill needed.")
        return await apply_master_data_backfill(db)

    return router


__all__ = ["build_master_data_backfill_router"]
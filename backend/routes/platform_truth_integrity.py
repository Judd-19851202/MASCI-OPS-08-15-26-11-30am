from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from lib.cross_entity_exception_state import exceptions_to_csv, list_cross_entity_exceptions
from lib.platform_truth_integrity import (
    scan_cross_entity_integrity,
    scan_platform_contamination_integrity,
    scan_platform_stale_derived_state,
    scan_platform_truth_integrity,
)


def build_platform_truth_integrity_router(db, require_admin_dep):
    router = APIRouter(tags=["Platform Truth Integrity"])

    @router.get("/api/admin/platform-truth-integrity")
    async def admin_platform_truth_integrity(_: Any = Depends(require_admin_dep)):
        return await scan_platform_truth_integrity(db)

    @router.get("/api/admin/platform-truth-integrity/contamination")
    async def admin_platform_truth_contamination(_: Any = Depends(require_admin_dep)):
        return await scan_platform_contamination_integrity(db)

    @router.get("/api/admin/platform-truth-integrity/stale-derived-state")
    async def admin_platform_truth_stale(_: Any = Depends(require_admin_dep)):
        return await scan_platform_stale_derived_state(db)

    @router.get("/api/admin/platform-truth-integrity/cross-entity")
    async def admin_platform_truth_cross_entity(_: Any = Depends(require_admin_dep)):
        return await scan_cross_entity_integrity(db)

    @router.get("/api/admin/platform-truth-integrity/cross-entity/exceptions")
    async def admin_platform_truth_cross_entity_exceptions(_: Any = Depends(require_admin_dep)):
        rows = await list_cross_entity_exceptions(db, active_only=True)
        total = await db.cross_entity_exception_state.count_documents({"active": True})
        return {
            "count": total,
            "rows": rows,
        }

    @router.get(
        "/api/admin/platform-truth-integrity/cross-entity/exceptions/export.csv",
        response_class=PlainTextResponse,
    )
    async def admin_platform_truth_cross_entity_exceptions_csv(_: Any = Depends(require_admin_dep)):
        rows = await list_cross_entity_exceptions(db, active_only=True)
        return PlainTextResponse(
            exceptions_to_csv(rows),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=cross-entity-exceptions.csv",
            },
        )

    return router


__all__ = ["build_platform_truth_integrity_router"]
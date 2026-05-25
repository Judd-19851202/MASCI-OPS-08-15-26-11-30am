"""routes/admin_stability.py · iter431 · Phase 29 · Part 4.

Admin-strict endpoints for the stability governance sweepers.

Endpoints
---------
    POST /api/admin-strict/stability/sweep?dry_run={bool}
        Runs every sweeper. Default: dry_run=true. Returns the
        per-collection counts so the operator sees what will be (or
        was) removed.

Doctrine
--------
- Admin-strict only · JSON only · NO UI.
- Default to DRY-RUN. The operator must explicitly pass
  `dry_run=false` to actually remove rows.
- Never raises 5xx on a sweep error — every sweeper returns its own
  error dict and the route returns 200 with that dict embedded.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from fastapi import APIRouter, Depends

from lib.stability_governance import run_stability_sweep


def build_admin_stability_router(
    *,
    db,
    require_admin_strict_dep: Callable[..., Awaitable[Any]],
) -> APIRouter:
    router = APIRouter(prefix="/api/admin-strict/stability", tags=["admin-strict-stability"])

    @router.post(
        "/sweep",
        dependencies=[Depends(require_admin_strict_dep)],
    )
    async def stability_sweep(dry_run: bool = True):
        """Run every stability sweeper. DRY-RUN by default — the
        operator must explicitly pass `?dry_run=false` to delete."""
        return await run_stability_sweep(db, dry_run=dry_run)

    return router

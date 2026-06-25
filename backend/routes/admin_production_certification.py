"""TRACK 15.79E · Admin · Production Certification.

Single read-only endpoint that exposes the continuous per-workflow
certification computed in ``lib.production_certification``. The
endpoint is admin-gated, side-effect-free, and writes nothing.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends


def make_router(db, require_admin_only_dep) -> APIRouter:
    router = APIRouter()

    @router.get("/api/admin/production-certification")
    async def production_certification(
        _: Any = Depends(require_admin_only_dep),
    ):
        from lib.production_certification import build_certification  # noqa: PLC0415
        return await build_certification(db)

    return router


__all__ = ["make_router"]

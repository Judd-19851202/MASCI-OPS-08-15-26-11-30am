"""routes/admin_operator_digest.py · iter431 · Phase 29 · Part 6.

Admin generator endpoint for the weekly operator digest.

Endpoints
---------
    GET /api/admin/digest/weekly?format={text|json}
        Returns the live digest payload. `format=text` (default)
        returns the doctrine plaintext rendering. `format=json`
        returns the raw payload dict so downstream tooling can
        reformat without re-querying.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from fastapi import APIRouter, Depends, Response

from lib.operator_digest import build_weekly_digest_payload, render_digest_plaintext


def build_admin_operator_digest_router(
    *,
    db,
    require_admin_dep: Callable[..., Awaitable[Any]],
) -> APIRouter:
    router = APIRouter(prefix="/api/admin/digest", tags=["admin-digest"])

    @router.get(
        "/weekly",
        dependencies=[Depends(require_admin_dep)],
    )
    async def weekly_digest(format: str = "text"):  # noqa: A002
        payload = await build_weekly_digest_payload(db)
        if format == "json":
            return payload
        text = render_digest_plaintext(payload)
        return Response(content=text, media_type="text/plain; charset=utf-8")

    return router

"""Track 19.39 · Morning Safety Intelligence Digest routes.

Five additive Safety+Admin endpoints. Read-only for previews; the
recipient CRUD endpoints touch only the additive ``morning_digest_recipients``
collection. No mutation of any incident/case/evidence/CAPA collection.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse

from . import morning_digest as md


def register_morning_digest_routes(
    api_router: APIRouter, db, *, require_safety_or_admin,
) -> None:

    @api_router.get("/incident-intelligence/morning-digest/preview")
    async def preview_digest(
        window: int = Query(7, ge=1, le=30),
        top_n: int = Query(5, ge=1, le=20),
        actor=Depends(require_safety_or_admin),
    ):
        digest = await md.compose_digest(
            db, digest_window_days=window, top_n=top_n,
        )
        html = md.render_html(digest)
        return HTMLResponse(content=html, status_code=200)

    @api_router.get("/incident-intelligence/morning-digest/preview.json")
    async def preview_digest_json(
        window: int = Query(7, ge=1, le=30),
        top_n: int = Query(5, ge=1, le=20),
        actor=Depends(require_safety_or_admin),
    ):
        return await md.compose_digest(
            db, digest_window_days=window, top_n=top_n,
        )

    @api_router.post("/incident-intelligence/morning-digest/send")
    async def send_morning_digest(
        dry_run: bool = Query(True),
        window: int = Query(7, ge=1, le=30),
        top_n: int = Query(5, ge=1, le=20),
        actor=Depends(require_safety_or_admin),
    ):
        who = "admin"
        if isinstance(actor, dict):
            who = (actor.get("email") or actor.get("username")
                   or actor.get("_actor") or "admin")
        return await md.send_digest(
            db, dry_run=dry_run, digest_window_days=window,
            top_n=top_n, generated_by=str(who),
        )

    @api_router.get("/incident-intelligence/morning-digest/recipients")
    async def list_digest_recipients(
        active_only: bool = Query(False),
        actor=Depends(require_safety_or_admin),
    ):
        rows = await md.list_recipients(db, active_only=active_only)
        return {"count": len(rows), "recipients": rows}

    @api_router.post("/incident-intelligence/morning-digest/recipients")
    async def add_digest_recipient(
        payload: dict = Body(...),
        actor=Depends(require_safety_or_admin),
    ):
        try:
            row = await md.add_recipient(
                db,
                email=payload.get("email", ""),
                display_name=payload.get("display_name", ""),
                role_label=payload.get("role_label", ""),
                notes=payload.get("notes", ""),
                added_by=str((actor or {}).get("email")
                             or (actor or {}).get("_actor")
                             or "admin") if isinstance(actor, dict) else "admin",
            )
            return {"ok": True, "recipient": row}
        except ValueError as e:
            raise HTTPException(400, detail={"code": "bad_request",
                                             "detail": str(e)})

    @api_router.patch("/incident-intelligence/morning-digest/recipients/{recipient_id}")
    async def update_digest_recipient(
        recipient_id: str,
        payload: dict = Body(...),
        actor=Depends(require_safety_or_admin),
    ):
        row = await md.update_recipient(
            db, recipient_id=recipient_id, patch=payload or {},
        )
        if not row:
            raise HTTPException(404, detail={"code": "not_found",
                                             "detail": f"recipient {recipient_id!r} not found"})
        return {"ok": True, "recipient": row}


__all__ = ["register_morning_digest_routes"]

"""Operational Intelligence routes — one route module for the engine."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse

from . import products as _products  # noqa: F401 · registers products at import
from .engine import compose, render_html, dispatch
from .registry import list_products, get_product


def register_operational_intelligence_routes(
    api_router: APIRouter, db, *, require_safety_or_admin, require_admin,
) -> None:

    @api_router.get("/operational-intelligence/products")
    async def list_registered_products(actor=Depends(require_safety_or_admin)):
        return {"count": len(list_products()),
                "products": [dict(
                    product_id=p.product_id, display_name=p.display_name,
                    summary=p.summary, permission_role=p.permission_role,
                    template_key=p.template_key, schedule_freq=p.schedule_freq,
                    schedule_iso_day=p.schedule_iso_day,
                    schedule_hour_utc=p.schedule_hour_utc,
                    status=p.status, tags=p.tags,
                ) for p in list_products()]}

    def _gate_for(product_id: str):
        p = get_product(product_id)
        if not p:
            raise HTTPException(404, detail={"code": "not_found",
                                             "detail": f"product {product_id!r}"})
        return p

    def _is_admin_actor(actor) -> bool:
        """The safety_or_admin gate returns either a Safety user dict
        (with `_actor='safety'`) or an Admin sentinel (`_actor='admin'`).
        Track 19.40 mistakenly compared `actor is True`; the correct
        check is against the sentinel emitted by `make_require_safety_or_admin`."""
        if actor is True:      # legacy sentinel (kept for compatibility)
            return True
        if isinstance(actor, dict):
            return (actor.get("_actor") or "").lower() == "admin"
        return False

    @api_router.get("/operational-intelligence/{product_id}/preview")
    async def preview_product(product_id: str,
                              actor=Depends(require_safety_or_admin)):
        p = _gate_for(product_id)
        if p.permission_role == "admin_only" and not _is_admin_actor(actor):
            raise HTTPException(403, detail={"code": "forbidden",
                                             "detail": "admin only"})
        try:
            digest = await compose(db, product_id=product_id)
        except NotImplementedError as e:
            return {"product_id": product_id, "status": "contract_registered",
                    "detail": str(e)}
        return HTMLResponse(render_html(digest))

    @api_router.post("/operational-intelligence/{product_id}/dispatch")
    async def dispatch_product(product_id: str,
                               dry_run: bool = Query(True),
                               actor=Depends(require_safety_or_admin)):
        p = _gate_for(product_id)
        if p.permission_role == "admin_only" and not _is_admin_actor(actor):
            raise HTTPException(403, detail={"code": "forbidden",
                                             "detail": "admin only"})
        who = "admin" if _is_admin_actor(actor) else str(
            (actor or {}).get("email") or (actor or {}).get("_actor") or "user"
        )
        try:
            return await dispatch(db, product_id=product_id, dry_run=dry_run,
                                  generated_by=who)
        except NotImplementedError as e:
            raise HTTPException(501, detail={"code": "aggregator_not_implemented",
                                             "detail": str(e)})

    # ------------------------------------------------------------------
    # TRACK 19.45A · Universal recipient management routes
    # ------------------------------------------------------------------
    from .recipients import (
        list_recipients as _list_recipients,
        add_recipient as _add_recipient,
        update_recipient as _update_recipient,
        deactivate_recipient as _deactivate_recipient,
        bulk_import_recipients as _bulk_import_recipients,
        list_recipients_for as _list_recipients_for,
        list_groups as _list_groups,
        add_group as _add_group,
        add_group_member as _add_group_member,
    )

    def _actor_email(actor) -> str:
        if isinstance(actor, dict):
            return str(actor.get("email") or actor.get("_actor") or "admin")
        return "admin"

    def _is_admin(actor) -> bool:
        if actor is True:
            return True
        if isinstance(actor, dict):
            return (actor.get("_actor") or "").lower() == "admin"
        return False

    @api_router.get("/operational-intelligence/recipients")
    async def _oi_list_recipients(
        product_id: str | None = Query(default=None),
        active_only: bool = Query(default=False),
        search: str | None = Query(default=None),
        limit: int = Query(default=500, le=2000),
        actor=Depends(require_admin),
    ):
        rows = await _list_recipients(
            db, product_id=product_id, active_only=active_only,
            search=search, limit=limit,
        )
        return {"count": len(rows), "recipients": rows}

    @api_router.get("/operational-intelligence/recipients/for/{product_id}")
    async def _oi_recipients_for(
        product_id: str,
        active_only: bool = Query(default=True),
        actor=Depends(require_admin),
    ):
        _gate_for(product_id)  # validate product exists
        merged = await _list_recipients_for(
            db, product_id=product_id, active_only=active_only,
        )
        return {"product_id": product_id, "count": len(merged),
                "recipients": merged}

    @api_router.post("/operational-intelligence/recipients")
    async def _oi_add_recipient(payload: dict, actor=Depends(require_admin)):
        try:
            doc = await _add_recipient(
                db,
                email=payload.get("email") or "",
                product_id=payload.get("product_id")
                             or payload.get("digest_type") or "",
                display_name=payload.get("display_name") or "",
                role_label=payload.get("role_label") or "",
                department=payload.get("department") or "",
                notes=payload.get("notes") or "",
                active=bool(payload.get("active", True)),
                added_by=_actor_email(actor),
            )
        except ValueError as e:
            raise HTTPException(400, detail={"code": "invalid_payload",
                                             "detail": str(e)})
        return {"ok": True, "recipient": doc}

    @api_router.patch("/operational-intelligence/recipients/{recipient_id}")
    async def _oi_update_recipient(recipient_id: str, payload: dict,
                                   actor=Depends(require_admin)):
        try:
            doc = await _update_recipient(
                db, recipient_id=recipient_id,
                updated_by=_actor_email(actor),
                **{k: v for k, v in payload.items() if k in (
                    "email", "display_name", "role_label", "department",
                    "notes", "active", "digest_type",
                )},
            )
        except ValueError as e:
            raise HTTPException(400, detail={"code": "invalid_payload",
                                             "detail": str(e)})
        if not doc:
            raise HTTPException(404, detail={"code": "not_found",
                                             "detail": recipient_id})
        return {"ok": True, "recipient": doc}

    @api_router.delete("/operational-intelligence/recipients/{recipient_id}")
    async def _oi_deactivate_recipient(recipient_id: str,
                                       actor=Depends(require_admin)):
        """Deactivation preferred over deletion (regulatory replay)."""
        doc = await _deactivate_recipient(
            db, recipient_id=recipient_id, updated_by=_actor_email(actor),
        )
        if not doc:
            raise HTTPException(404, detail={"code": "not_found"})
        return {"ok": True, "recipient": doc}

    @api_router.post("/operational-intelligence/recipients/bulk-import")
    async def _oi_bulk_import(payload: dict, actor=Depends(require_admin)):
        rows = payload.get("rows") or []
        return await _bulk_import_recipients(
            db, rows=rows,
            default_product_id=payload.get("default_product_id"),
            added_by=_actor_email(actor),
        )

    @api_router.get("/operational-intelligence/groups")
    async def _oi_list_groups(actor=Depends(require_admin)):
        gs = await _list_groups(db)
        return {"count": len(gs), "groups": gs}

    @api_router.post("/operational-intelligence/groups")
    async def _oi_add_group(payload: dict, actor=Depends(require_admin)):
        g = await _add_group(
            db,
            group_id=payload.get("group_id") or "",
            group_name=payload.get("group_name") or "",
            products=payload.get("products") or [],
            created_by=_actor_email(actor),
        )
        return {"ok": True, "group": g}

    @api_router.post("/operational-intelligence/groups/{group_id}/members")
    async def _oi_add_group_member(group_id: str, payload: dict,
                                   actor=Depends(require_admin)):
        try:
            g = await _add_group_member(
                db, group_id=group_id,
                email=payload.get("email") or "",
                display_name=payload.get("display_name") or "",
                role_label=payload.get("role_label") or "",
                active=bool(payload.get("active", True)),
            )
        except ValueError as e:
            raise HTTPException(400, detail={"code": "invalid_payload",
                                             "detail": str(e)})
        if not g:
            raise HTTPException(404, detail={"code": "group_not_found"})
        return {"ok": True, "group": g}


__all__ = ["register_operational_intelligence_routes"]

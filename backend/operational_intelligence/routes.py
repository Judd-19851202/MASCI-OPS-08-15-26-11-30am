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


__all__ = ["register_operational_intelligence_routes"]

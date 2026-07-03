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

    # ------------------------------------------------------------------
    # TRACK 19.46 · Read-only History + Audit APIs (Cockpit foundation)
    # ------------------------------------------------------------------
    from .engine import COLLECTION_HISTORY, COLLECTION_AUDIT

    @api_router.get("/operational-intelligence/history")
    async def _oi_history(
        product_id: str | None = Query(default=None),
        period: str | None = Query(default=None),
        since: str | None = Query(default=None,
                                  description="ISO-8601 lower bound on generated_at"),
        until: str | None = Query(default=None,
                                  description="ISO-8601 upper bound on generated_at"),
        limit: int = Query(default=100, le=500),
        offset: int = Query(default=0, ge=0),
        sort: str = Query(default="-generated_at",
                          pattern="^-?(generated_at|product_id|period)$"),
        actor=Depends(require_admin),
    ):
        """Read-only history — no writes, no mutations. Backs the
        future Cockpit UI history strip."""
        q: dict = {}
        if product_id:
            _gate_for(product_id)  # 404 for unknown product
            q["product_id"] = product_id
        if period:
            q["period"] = period
        if since or until:
            gen: dict = {}
            if since: gen["$gte"] = since
            if until: gen["$lte"] = until
            q["generated_at"] = gen
        sort_key = sort.lstrip("-")
        sort_dir = -1 if sort.startswith("-") else 1
        total = await db[COLLECTION_HISTORY].count_documents(q)
        cursor = db[COLLECTION_HISTORY].find(
            q,
            # Never expose the fully-rendered HTML in list mode — the
            # Cockpit renders a slim summary and drills into the full
            # digest via the preview endpoint.
            {"_id": 0, "rendered_html": 0},
        ).sort([(sort_key, sort_dir)]).skip(offset).limit(limit)
        rows = []
        async for row in cursor:
            # Slim the digest_object down to the executive-summary +
            # score payload so the list stays boardroom-fast.
            dobj = row.get("digest_object") or {}
            sc = dobj.get("operational_intelligence_score") or {}
            rows.append({
                "id": row.get("id"),
                "product_id": row.get("product_id"),
                "period": row.get("period"),
                "generated_by": row.get("generated_by"),
                "generated_at": row.get("generated_at"),
                "subject": dobj.get("subject") or "",
                "score": {
                    "overall_score": sc.get("overall_score"),
                    "attention_level": sc.get("attention_level"),
                    "confidence": sc.get("confidence"),
                    "trend_direction": sc.get("trend_direction"),
                    "trend_percent": sc.get("trend_percent"),
                },
            })
        return {"count": len(rows), "total": total,
                "limit": limit, "offset": offset,
                "sort": sort, "history": rows}

    @api_router.get("/operational-intelligence/history/{history_id}")
    async def _oi_history_detail(history_id: str,
                                 include_html: bool = Query(default=False),
                                 actor=Depends(require_admin)):
        """Fetch a single history row (full digest_object). HTML is
        opt-in to keep the default response light."""
        projection = {"_id": 0}
        if not include_html:
            projection["rendered_html"] = 0
        row = await db[COLLECTION_HISTORY].find_one({"id": history_id}, projection)
        if not row:
            raise HTTPException(404, detail={"code": "not_found",
                                             "detail": history_id})
        return {"ok": True, "history": row}

    @api_router.get("/operational-intelligence/audit")
    async def _oi_audit(
        product_id: str | None = Query(default=None),
        event: str | None = Query(default=None),
        actor_email: str | None = Query(default=None,
                                        alias="actor"),
        since: str | None = Query(default=None),
        until: str | None = Query(default=None),
        limit: int = Query(default=100, le=500),
        offset: int = Query(default=0, ge=0),
        sort: str = Query(default="-at",
                          pattern="^-?(at|product_id|event|actor)$"),
        _admin=Depends(require_admin),
    ):
        """Read-only audit trail — dispatches, recipient/group changes,
        preview/dry-run/live send, scheduler/manual origin."""
        q: dict = {}
        if product_id:
            _gate_for(product_id)
            q["product_id"] = product_id
        if event:
            q["event"] = event
        if actor_email:
            q["actor"] = actor_email
        if since or until:
            r: dict = {}
            if since: r["$gte"] = since
            if until: r["$lte"] = until
            q["at"] = r
        sort_key = sort.lstrip("-")
        sort_dir = -1 if sort.startswith("-") else 1
        total = await db[COLLECTION_AUDIT].count_documents(q)
        cursor = db[COLLECTION_AUDIT].find(
            q, {"_id": 0},
        ).sort([(sort_key, sort_dir)]).skip(offset).limit(limit)
        rows = []
        async for row in cursor:
            # Never expose secrets — the audit payload is already
            # sanitized upstream (write_audit stores only structured
            # metadata), but defensive-strip any *_secret/token fields
            # that a caller might have inserted historically.
            payload = row.get("payload") or {}
            safe_payload = {k: v for k, v in payload.items()
                            if not any(bad in k.lower()
                                       for bad in ("token", "secret",
                                                   "password", "api_key"))}
            rows.append({
                "id": row.get("id"),
                "product_id": row.get("product_id"),
                "event": row.get("event"),
                "actor": row.get("actor"),
                "at": row.get("at"),
                "payload": safe_payload,
            })
        return {"count": len(rows), "total": total,
                "limit": limit, "offset": offset,
                "sort": sort, "audit": rows}


__all__ = ["register_operational_intelligence_routes"]

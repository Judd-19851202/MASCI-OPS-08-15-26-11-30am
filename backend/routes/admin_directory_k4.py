"""
admin_directory_k4.py — Phase K4a · Unified Directory · Read-Only Surface
========================================================================

Read-only admin endpoints that surface the K1-mirrored unified
`user_directory` collection (including mirrored legacy portal users)
alongside the K3 role-template catalog. **Strictly non-enforcing**:

  • No mutations exposed in K4a (the existing legacy
    `/api/admin/directory` POST/PATCH/DELETE remain the only write path
    until K4b lands).
  • Nothing here changes login flow, authz, or any per-portal behavior.
  • Every response excludes `_id` and `password_hash`.

Endpoints (all admin-strict):
  • `GET  /api/admin/directory/k4/users`          — full mirrored+managed list
  • `GET  /api/admin/directory/k4/users/{user_id}` — single row + recent audit
  • `GET  /api/admin/directory/k4/stats`           — counts (total, mirrored,
                                                    managed, by portal,
                                                    disabled, with_template)
  • `GET  /api/admin/directory/k4/role-templates`  — K3 template catalog
                                                    passthrough for the UI
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

logger = logging.getLogger(__name__)

# Portals the directory recognises. Keep aligned with
# user_directory.ALLOWED_PORTALS + identity_mirror.PORTAL_COLLECTIONS.
KNOWN_PORTALS = ("admin", "pm", "shop", "hr", "safety", "dispatch")


def _directory_full_view(row: Dict[str, Any]) -> Dict[str, Any]:
    """Public read-only view of a `user_directory` row including the
    K1/K3 metadata. NEVER includes `_id` or `password_hash`."""
    if not row:
        return {}
    return {
        "id": row.get("id"),
        "email": row.get("email"),
        "name": row.get("name") or "",
        "portals": sorted({p for p in (row.get("portals") or []) if p in KNOWN_PORTALS}),
        "is_super_admin": bool(row.get("is_super_admin")),
        "disabled": bool(row.get("disabled")),
        "must_change_password": bool(row.get("must_change_password")),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "last_login_at": row.get("last_login_at"),
        "last_login_portal": row.get("last_login_portal"),
        # K1 fields
        "mirrored": bool(row.get("mirrored")),
        "mirror_sources": row.get("mirror_sources") or {},
        "employee_id": row.get("employee_id"),
        # K3 / K6-future field. Present-but-null until K4b lands.
        "role_template_id": row.get("role_template_id"),
        # Derived classification helpful for the UI badges
        "source": "managed" if not row.get("mirrored") else "mirrored",
    }


def build_admin_directory_k4_router(
    db,
    *,
    require_admin_strict_dep: Callable,
) -> APIRouter:
    router = APIRouter(tags=["admin-directory-k4"])

    @router.get(
        "/api/admin/directory/k4/users",
        dependencies=[Depends(require_admin_strict_dep)],
    )
    async def list_directory_users(
        q: Optional[str] = Query(default=None, description="case-insensitive email/name substring"),
        portal: Optional[str] = Query(default=None, description="filter to one portal key"),
        source: Optional[str] = Query(
            default=None,
            description="'mirrored' | 'managed' | None (all)",
        ),
        disabled: Optional[bool] = Query(default=None),
        limit: int = Query(default=500, ge=1, le=2000),
        skip: int = Query(default=0, ge=0),
    ) -> Dict[str, Any]:
        mongo_filter: Dict[str, Any] = {}
        if portal:
            portal_clean = portal.strip().lower()
            if portal_clean not in KNOWN_PORTALS:
                raise HTTPException(status_code=400, detail=f"Unknown portal: {portal}")
            mongo_filter["portals"] = portal_clean
        if source == "mirrored":
            mongo_filter["mirrored"] = True
        elif source == "managed":
            mongo_filter["$or"] = [
                {"mirrored": {"$exists": False}},
                {"mirrored": False},
            ]
        elif source not in (None, "", "all"):
            raise HTTPException(
                status_code=400,
                detail="source must be 'mirrored' | 'managed' | 'all' | empty",
            )
        if disabled is True:
            mongo_filter["disabled"] = True
        elif disabled is False:
            mongo_filter["disabled"] = {"$ne": True}
        if q:
            needle = q.strip().lower()
            if needle:
                # Mongo collation-free case-insensitive match via $regex
                import re

                safe = re.escape(needle)
                mongo_filter["$or"] = mongo_filter.get("$or", []) + [
                    {"email": {"$regex": safe, "$options": "i"}},
                    {"name": {"$regex": safe, "$options": "i"}},
                ]
                # If we already had a top-level $or from `source`, the
                # union above merges them — Mongo treats multiple $or
                # branches as "any match", which is the right behavior.
        # `created_at` is stored as ISO string; sort lexically (works for ISO 8601)
        cursor = db.user_directory.find(mongo_filter, {"_id": 0, "password_hash": 0}).sort(
            "created_at", -1
        )
        cursor = cursor.skip(skip).limit(limit)
        rows: List[Dict[str, Any]] = []
        async for r in cursor:
            rows.append(_directory_full_view(r))
        total = await db.user_directory.count_documents(mongo_filter)
        return {
            "ok": True,
            "users": rows,
            "total": total,
            "limit": limit,
            "skip": skip,
        }

    @router.get(
        "/api/admin/directory/k4/users/{user_id}",
        dependencies=[Depends(require_admin_strict_dep)],
    )
    async def get_directory_user(user_id: str) -> Dict[str, Any]:
        row = await db.user_directory.find_one(
            {"id": user_id}, {"_id": 0, "password_hash": 0}
        )
        if not row:
            raise HTTPException(status_code=404, detail="User not found.")
        view = _directory_full_view(row)
        # Best-effort recent audit (read-only — no writes here).
        audit: List[Dict[str, Any]] = []
        try:
            async for entry in (
                db.admin_audit.find(
                    {"target_email": view.get("email")}, {"_id": 0}
                )
                .sort("at", -1)
                .limit(20)
            ):
                audit.append(entry)
        except Exception as e:  # noqa: BLE001
            logger.debug(f"[k4] audit fetch skipped: {e}")
        return {"ok": True, "user": view, "audit": audit}

    @router.get(
        "/api/admin/directory/k4/stats",
        dependencies=[Depends(require_admin_strict_dep)],
    )
    async def directory_stats() -> Dict[str, Any]:
        coll = db.user_directory
        total = await coll.count_documents({})
        mirrored = await coll.count_documents({"mirrored": True})
        managed = await coll.count_documents(
            {"$or": [{"mirrored": {"$exists": False}}, {"mirrored": False}]}
        )
        disabled = await coll.count_documents({"disabled": True})
        with_template = await coll.count_documents(
            {"role_template_id": {"$exists": True, "$nin": [None, ""]}}
        )
        by_portal: Dict[str, int] = {}
        for p in KNOWN_PORTALS:
            by_portal[p] = await coll.count_documents({"portals": p})
        return {
            "ok": True,
            "total": total,
            "mirrored": mirrored,
            "managed": managed,
            "disabled": disabled,
            "with_role_template": with_template,
            "by_portal": by_portal,
        }

    @router.get(
        "/api/admin/directory/k4/role-templates",
        dependencies=[Depends(require_admin_strict_dep)],
    )
    async def list_role_templates(
        portal: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        # Read-through to the K3 catalog. Strip Mongo internals defensively.
        from lib.role_templates import list_templates  # local import to avoid cycle

        portal_clean = None
        if portal:
            p = portal.strip().lower()
            if p not in KNOWN_PORTALS:
                raise HTTPException(status_code=400, detail=f"Unknown portal: {portal}")
            portal_clean = p
        templates = await list_templates(db, portal=portal_clean)
        # Defensive scrub — list_templates already projects {_id: 0} but
        # this keeps the response contract owned by this module.
        cleaned: List[Dict[str, Any]] = []
        for t in templates:
            t.pop("_id", None)
            cleaned.append(t)
        return {"ok": True, "templates": cleaned, "count": len(cleaned)}

    return router

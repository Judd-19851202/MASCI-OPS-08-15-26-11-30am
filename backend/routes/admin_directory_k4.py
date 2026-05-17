"""
admin_directory_k4.py — Phase K4 · Unified Directory · Admin-Only Surface
========================================================================

  K4a (iter176) — read-only listing, stats, role-template passthrough.
  K4b (iter177) — admin-only audited mutations: role-template assign,
                  convert mirrored→managed, revert managed→mirrored,
                  enable/disable. Every mutation writes a row to the
                  shared `admin_audit` collection. NO automation,
                  NO onboarding email, NO temp-password generation,
                  NO self-service, NO enforcement (K3 templates are
                  stored but never read by routes). K5 owns the full
                  credential lifecycle.

All mutations:
  • are gated by `require_admin_strict_dep`
  • require `Request` for IP/UA capture into the audit row
  • never echo passwords back in any response
  • are explicit no-op-safe (e.g. re-assigning the same template logs
    `no_change=True` and skips the write)
  • preserve mirrored-user compatibility: legacy per-portal rows
    (`hr_users`, `shop_users`, …) are NEVER touched. Conversion only
    writes to `user_directory`.
  • preserve rollback: revert-to-mirrored re-randomises the bcrypt hash
    and re-sets `mirrored=true` so the unified-login path goes back to
    refusing the row.

Read endpoints (K4a — unchanged):
  • `GET  /api/admin/directory/k4/users`
  • `GET  /api/admin/directory/k4/users/{user_id}`
  • `GET  /api/admin/directory/k4/stats`
  • `GET  /api/admin/directory/k4/role-templates`

Mutation endpoints (K4b — new):
  • `POST /api/admin/directory/k4/users/{user_id}/role-template`
  • `POST /api/admin/directory/k4/users/{user_id}/convert-to-managed`
  • `POST /api/admin/directory/k4/users/{user_id}/revert-to-mirrored`
  • `POST /api/admin/directory/k4/users/{user_id}/set-disabled`
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

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
    require_step_up: Optional[Callable] = None,
) -> APIRouter:
    router = APIRouter(tags=["admin-directory-k4"])

    # Phase 2 Initiative 5b-full — optional step-up gate on K4 mutations.
    # If require_step_up is None or step-up is env-disabled, this resolves
    # to a no-op dependency so behavior is unchanged. Routes that match
    # the "super-sensitive" classification in AUTHORIZATION_MATRIX.md
    # add this to their `dependencies=[...]` list.
    async def _step_up_noop():
        return True
    _step_up_dep = require_step_up or _step_up_noop

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

    # ──────────────────────────────────────────────────────────────────
    # K4b — admin-only audited mutations (iter177)
    # Every endpoint below: admin-strict + Request-bound for audit IP/UA.
    # ──────────────────────────────────────────────────────────────────

    @router.post(
        "/api/admin/directory/k4/users/{user_id}/role-template",
        dependencies=[Depends(require_admin_strict_dep), Depends(_step_up_dep)],
    )
    async def assign_role_template(
        user_id: str,
        body: AssignTemplateBody,
        request: Request,
    ) -> Dict[str, Any]:
        import user_directory as ud  # local import to avoid cycle

        row = await ud.find_by_id(db, user_id)
        if not row:
            raise HTTPException(status_code=404, detail="User not found.")
        new_id = (body.role_template_id or "").strip() or None
        if new_id is not None:
            tpl = await db.role_templates.find_one({"id": new_id}, {"_id": 0})
            if not tpl:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown role_template_id: {new_id}",
                )
            if tpl.get("active") is False:
                raise HTTPException(
                    status_code=400,
                    detail=f"Role template is inactive: {new_id}",
                )
        old_id = row.get("role_template_id")
        no_change = (old_id or None) == new_id
        if not no_change:
            await db.user_directory.update_one(
                {"id": user_id},
                {
                    "$set": {
                        "role_template_id": new_id,
                        "updated_at": _now_iso(),
                    }
                },
            )
        await ud.write_audit(
            db,
            actor_email=_audit_actor(request),
            action="directory_k4_assign_role_template",
            target_email=row.get("email"),
            diff={"from": old_id, "to": new_id, "no_change": no_change},
            ip=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
        refreshed = await ud.find_by_id(db, user_id)
        return {"ok": True, "user": _directory_full_view(refreshed)}

    @router.post(
        "/api/admin/directory/k4/users/{user_id}/convert-to-managed",
        dependencies=[Depends(require_admin_strict_dep), Depends(_step_up_dep)],
    )
    async def convert_to_managed(
        user_id: str,
        body: ConvertToManagedBody,
        request: Request,
    ) -> Dict[str, Any]:
        import user_directory as ud  # local import to avoid cycle

        row = await ud.find_by_id(db, user_id)
        if not row:
            raise HTTPException(status_code=404, detail="User not found.")
        if not row.get("mirrored"):
            raise HTTPException(
                status_code=409,
                detail="User is already managed — nothing to convert.",
            )
        if row.get("is_super_admin"):
            # Belt-and-braces: super admin is bootstrapped as managed and
            # `mirrored` should be False. Refuse mutation regardless.
            raise HTTPException(
                status_code=409,
                detail="Super-admin account is already managed.",
            )
        password = (body.password or "").strip()
        if len(password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters.",
            )
        await db.user_directory.update_one(
            {"id": user_id},
            {
                "$set": {
                    "password_hash": ud.hash_password(password),
                    "mirrored": False,
                    "must_change_password": True,
                    "updated_at": _now_iso(),
                }
            },
        )
        await ud.write_audit(
            db,
            actor_email=_audit_actor(request),
            action="directory_k4_convert_to_managed",
            target_email=row.get("email"),
            # NEVER record the password. password_set=True is the signal.
            diff={
                "password_set": True,
                "must_change_password": True,
                "previous_state": "mirrored",
            },
            ip=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
        refreshed = await ud.find_by_id(db, user_id)
        return {"ok": True, "user": _directory_full_view(refreshed)}

    @router.post(
        "/api/admin/directory/k4/users/{user_id}/revert-to-mirrored",
        dependencies=[Depends(require_admin_strict_dep), Depends(_step_up_dep)],
    )
    async def revert_to_mirrored(
        user_id: str,
        request: Request,
    ) -> Dict[str, Any]:
        import user_directory as ud  # local import to avoid cycle
        from lib.identity_mirror import _random_unguessable_hash  # noqa: PLC0415

        row = await ud.find_by_id(db, user_id)
        if not row:
            raise HTTPException(status_code=404, detail="User not found.")
        if row.get("is_super_admin"):
            raise HTTPException(
                status_code=409,
                detail="Cannot revert a super-admin account.",
            )
        if row.get("mirrored"):
            raise HTTPException(
                status_code=409,
                detail="User is already mirrored — nothing to revert.",
            )
        # Rollback is only safe when we know this row originated from a
        # legacy per-portal collection — i.e. K1 stamped `mirror_sources`
        # on it. Refuse for purely-managed rows that have no legacy
        # twin (no rollback target exists for them).
        sources = row.get("mirror_sources") or {}
        if not sources:
            raise HTTPException(
                status_code=409,
                detail="User has no mirror_sources — no legacy row to revert to.",
            )
        await db.user_directory.update_one(
            {"id": user_id},
            {
                "$set": {
                    "password_hash": _random_unguessable_hash(),
                    "mirrored": True,
                    "must_change_password": False,
                    "updated_at": _now_iso(),
                }
            },
        )
        await ud.write_audit(
            db,
            actor_email=_audit_actor(request),
            action="directory_k4_revert_to_mirrored",
            target_email=row.get("email"),
            diff={"previous_state": "managed", "rehashed": True},
            ip=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
        refreshed = await ud.find_by_id(db, user_id)
        return {"ok": True, "user": _directory_full_view(refreshed)}

    @router.post(
        "/api/admin/directory/k4/users/{user_id}/set-disabled",
        dependencies=[Depends(require_admin_strict_dep), Depends(_step_up_dep)],
    )
    async def set_disabled(
        user_id: str,
        body: SetDisabledBody,
        request: Request,
    ) -> Dict[str, Any]:
        import user_directory as ud  # local import to avoid cycle

        row = await ud.find_by_id(db, user_id)
        if not row:
            raise HTTPException(status_code=404, detail="User not found.")
        new_state = bool(body.disabled)
        if row.get("is_super_admin") and new_state:
            raise HTTPException(
                status_code=409,
                detail="Cannot disable a super-admin account.",
            )
        old_state = bool(row.get("disabled"))
        no_change = old_state == new_state
        if not no_change:
            await db.user_directory.update_one(
                {"id": user_id},
                {"$set": {"disabled": new_state, "updated_at": _now_iso()}},
            )
        await ud.write_audit(
            db,
            actor_email=_audit_actor(request),
            action="directory_k4_set_disabled",
            target_email=row.get("email"),
            diff={"from": old_state, "to": new_state, "no_change": no_change},
            ip=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
        refreshed = await ud.find_by_id(db, user_id)
        return {"ok": True, "user": _directory_full_view(refreshed)}

    return router


# ─────────────────────────────────────────────────────────────────────
# K4b body models
# ─────────────────────────────────────────────────────────────────────
class AssignTemplateBody(BaseModel):
    # Use Optional[str] (not str = None) so explicit null clears the assignment.
    role_template_id: Optional[str] = Field(
        default=None,
        description="Set to a valid `rt-…` id to assign, or null/empty to clear.",
    )


class ConvertToManagedBody(BaseModel):
    password: str = Field(..., min_length=8)


class SetDisabledBody(BaseModel):
    disabled: bool


# ─────────────────────────────────────────────────────────────────────
# Audit helpers (mirror the pattern used by auth_directory_routes)
# ─────────────────────────────────────────────────────────────────────
def _client_ip(request: Optional[Request]) -> Optional[str]:
    if not request:
        return None
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


def _audit_actor(request: Request) -> str:
    """Best-effort actor identification. Prefers a directory session
    token (gives the real human's email after Phase K1 onboarding);
    falls back to the legacy admin-token label."""
    dt = request.headers.get("x-directory-token")
    if dt:
        return f"directory:{dt[:8]}…"
    return "admin-token"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

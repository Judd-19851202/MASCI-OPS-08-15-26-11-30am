"""
auth_directory_routes.py — Multi-portal login + Access Control Center
admin endpoints (iter82).

Public endpoints (no auth required):
  POST /api/auth/multi-login                         — email+pw → tokens
  POST /api/auth/multi-logout                        — clear directory session
  POST /api/auth/change-master-password              — self-rotate

Authenticated (any portal token works) :
  GET  /api/auth/me-directory                        — current directory user
  POST /api/auth/issue-portal-token                  — bundle re-issue

Admin-strict (Access Control Center):
  GET  /api/admin/directory                          — list all users
  POST /api/admin/directory                          — create user
  PATCH /api/admin/directory/{user_id}               — update portals / disabled
  DELETE /api/admin/directory/{user_id}              — delete (blocked for super)
  POST /api/admin/directory/{user_id}/reset-password — admin pw reset
  GET  /api/admin/audit                              — paginated audit log
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field

import user_directory as ud

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# Body models
# ─────────────────────────────────────────────────────────────────────
class MultiLoginBody(BaseModel):
    email: str
    password: str


class ChangeMasterPwBody(BaseModel):
    current_password: str
    new_password: str


class CreateDirectoryUserBody(BaseModel):
    email: str
    name: str = ""
    portals: List[str] = Field(default_factory=list)
    password: str
    must_change_password: bool = False


class UpdateDirectoryUserBody(BaseModel):
    name: Optional[str] = None
    portals: Optional[List[str]] = None
    disabled: Optional[bool] = None


class AdminResetPasswordBody(BaseModel):
    new_password: str
    must_change: bool = True


# ─────────────────────────────────────────────────────────────────────
# Router factory
# ─────────────────────────────────────────────────────────────────────
def build_auth_directory_router(
    db,
    *,
    require_admin_strict_dep: Callable,
    pm_token_minter: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None,
    hr_token_minter: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None,
    shop_token_minter: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None,
    admin_token_minter: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None,
) -> APIRouter:
    router = APIRouter(tags=["auth-directory"])

    # ────────────────────────────────────────────────────────────────
    # Helper — mint all eligible portal tokens for a directory user
    # ────────────────────────────────────────────────────────────────
    async def _mint_all(row: Dict[str, Any]) -> Dict[str, Optional[str]]:
        tokens: Dict[str, Optional[str]] = {}
        portals = set(row.get("portals") or [])
        if "admin" in portals and admin_token_minter:
            try:
                tokens["admin"] = await _maybe_await(admin_token_minter(row))
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[multi-login] admin minter failed: {e}")
        if "pm" in portals and pm_token_minter:
            try:
                tokens["pm"] = await _maybe_await(pm_token_minter(row))
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[multi-login] pm minter failed: {e}")
        if "shop" in portals and shop_token_minter:
            try:
                tokens["shop"] = await _maybe_await(shop_token_minter(row))
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[multi-login] shop minter failed: {e}")
        if "hr" in portals and hr_token_minter:
            try:
                tokens["hr"] = await _maybe_await(hr_token_minter(row))
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[multi-login] hr minter failed: {e}")
        return tokens

    @router.post("/api/auth/multi-login")
    async def multi_login(body: MultiLoginBody, request: Request):
        row = await ud.authenticate(db, email=body.email, password=body.password)
        if not row:
            # Audit failures so brute-forcing surfaces in /admin
            await ud.write_audit(
                db,
                actor_email=body.email,
                action="multi_login_failed",
                ip=_client_ip(request),
                user_agent=request.headers.get("user-agent"),
            )
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        # Mint per-portal tokens + directory session token
        portal_tokens = await _mint_all(row)
        session_token = ud.make_directory_token()
        await ud.persist_session(db, token=session_token, user_id=row["id"])
        await ud.stamp_last_login(db, user_id=row["id"], portal="multi")
        await ud.write_audit(
            db,
            actor_email=row["email"],
            action="multi_login",
            target_email=row["email"],
            diff={"portals_granted": sorted([p for p, t in portal_tokens.items() if t])},
            ip=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
        return {
            "ok": True,
            "session_token": session_token,
            "portal_tokens": portal_tokens,
            "user": ud.public_view(row),
            "must_change_password": bool(row.get("must_change_password")),
        }

    @router.post("/api/auth/multi-logout")
    async def multi_logout(x_directory_token: Optional[str] = Header(default=None)):
        if x_directory_token:
            await ud.kill_session(db, token=x_directory_token)
        return {"ok": True}

    @router.get("/api/auth/me-directory")
    async def me_directory(x_directory_token: Optional[str] = Header(default=None)):
        row = await ud.session_user(db, token=x_directory_token or "")
        if not row:
            raise HTTPException(status_code=401, detail="Not signed in.")
        return {"ok": True, "user": ud.public_view(row)}

    @router.post("/api/auth/issue-portal-token")
    async def issue_portal_token(
        body: Dict[str, str] = Body(...),
        x_directory_token: Optional[str] = Header(default=None),
    ):
        """Re-issue a single portal token (used by the switcher when a
        token expires or a tab needs a fresh one)."""
        row = await ud.session_user(db, token=x_directory_token or "")
        if not row:
            raise HTTPException(status_code=401, detail="Not signed in.")
        target = (body.get("portal") or "").lower().strip()
        if target not in ud.ALLOWED_PORTALS:
            raise HTTPException(status_code=400, detail="Unknown portal.")
        if target not in (row.get("portals") or []):
            raise HTTPException(status_code=403, detail=f"No {target} access on this account.")
        minter = {
            "admin": admin_token_minter,
            "pm": pm_token_minter,
            "shop": shop_token_minter,
            "hr": hr_token_minter,
        }.get(target)
        if not minter:
            raise HTTPException(status_code=500, detail=f"{target} token minter not configured.")
        try:
            tok = await _maybe_await(minter(row))
        except Exception as e:  # noqa: BLE001
            logger.exception(f"[multi-login] portal-token mint failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to mint token.")
        return {"ok": True, "portal": target, "token": tok}

    @router.post("/api/auth/change-master-password")
    async def change_master_password(
        body: ChangeMasterPwBody,
        x_directory_token: Optional[str] = Header(default=None),
        request: Request = None,
    ):
        row = await ud.session_user(db, token=x_directory_token or "")
        if not row:
            raise HTTPException(status_code=401, detail="Not signed in.")
        try:
            ok = await ud.self_change_password(
                db,
                user_id=row["id"],
                current_password=body.current_password,
                new_password=body.new_password,
            )
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        if not ok:
            raise HTTPException(status_code=401, detail="Current password is incorrect.")
        await ud.write_audit(
            db,
            actor_email=row["email"],
            action="change_master_password",
            target_email=row["email"],
            ip=_client_ip(request) if request else None,
        )
        return {"ok": True}

    # ── Admin endpoints ─────────────────────────────────────────────
    @router.get("/api/admin/directory", dependencies=[Depends(require_admin_strict_dep)])
    async def list_users():
        rows = []
        async for r in db.user_directory.find({}, {"_id": 0}).sort("created_at", -1):
            rows.append(ud.public_view(r))
        return {"ok": True, "users": rows}

    @router.post("/api/admin/directory", dependencies=[Depends(require_admin_strict_dep)])
    async def create_user(body: CreateDirectoryUserBody, request: Request):
        try:
            view = await ud.create_directory_user(
                db,
                email=body.email,
                name=body.name,
                portals=body.portals,
                password=body.password,
                must_change_password=body.must_change_password,
            )
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        await ud.write_audit(
            db,
            actor_email=_audit_actor(request),
            action="directory_create",
            target_email=view["email"],
            diff={"portals": view["portals"], "must_change_password": body.must_change_password},
            ip=_client_ip(request),
        )
        return {"ok": True, "user": view}

    @router.patch(
        "/api/admin/directory/{user_id}",
        dependencies=[Depends(require_admin_strict_dep)],
    )
    async def update_user(user_id: str, body: UpdateDirectoryUserBody, request: Request):
        existing = await ud.find_by_id(db, user_id)
        if not existing:
            raise HTTPException(status_code=404, detail="User not found.")
        try:
            view = await ud.update_directory_user(
                db,
                user_id=user_id,
                name=body.name,
                portals=body.portals,
                disabled=body.disabled,
            )
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        diff = {
            k: getattr(body, k)
            for k in ("name", "portals", "disabled")
            if getattr(body, k) is not None
        }
        await ud.write_audit(
            db,
            actor_email=_audit_actor(request),
            action="directory_update",
            target_email=existing.get("email"),
            diff=diff,
            ip=_client_ip(request),
        )
        return {"ok": True, "user": view}

    @router.delete(
        "/api/admin/directory/{user_id}",
        dependencies=[Depends(require_admin_strict_dep)],
    )
    async def delete_user(user_id: str, request: Request):
        existing = await ud.find_by_id(db, user_id)
        if not existing:
            raise HTTPException(status_code=404, detail="User not found.")
        try:
            ok = await ud.delete_directory_user(db, user_id=user_id)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        await ud.write_audit(
            db,
            actor_email=_audit_actor(request),
            action="directory_delete",
            target_email=existing.get("email"),
            ip=_client_ip(request),
        )
        return {"ok": ok}

    @router.post(
        "/api/admin/directory/{user_id}/reset-password",
        dependencies=[Depends(require_admin_strict_dep)],
    )
    async def reset_password(user_id: str, body: AdminResetPasswordBody, request: Request):
        existing = await ud.find_by_id(db, user_id)
        if not existing:
            raise HTTPException(status_code=404, detail="User not found.")
        try:
            view = await ud.rotate_master_password(
                db,
                user_id=user_id,
                new_password=body.new_password,
                must_change=body.must_change,
            )
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        await ud.write_audit(
            db,
            actor_email=_audit_actor(request),
            action="directory_password_reset",
            target_email=existing.get("email"),
            diff={"must_change": bool(body.must_change)},
            ip=_client_ip(request),
        )
        return {"ok": True, "user": view}

    @router.get("/api/admin/audit", dependencies=[Depends(require_admin_strict_dep)])
    async def list_audit_log(
        limit: int = 100,
        skip: int = 0,
        actor: Optional[str] = None,
        action: Optional[str] = None,
    ):
        rows = await ud.list_audit(
            db,
            limit=max(1, min(limit, 500)),
            skip=max(0, skip),
            actor=actor,
            action=action,
        )
        return {"ok": True, "entries": rows}

    return router


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────
def _client_ip(request: Optional[Request]) -> Optional[str]:
    if not request:
        return None
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


def _audit_actor(request: Request) -> str:
    """Best-effort actor identification for admin actions. The admin
    token system doesn't include the actor email today, so we record
    the audit as 'admin-token' unless a directory session token is also
    present (preferred — gives us the real human's email)."""
    dt = request.headers.get("x-directory-token")
    if dt:
        return f"directory:{dt[:8]}…"
    return "admin-token"


async def _maybe_await(value):
    """Call a minter that might be sync or async, normalize to a value."""
    import asyncio
    if asyncio.iscoroutine(value):
        return await value
    return value

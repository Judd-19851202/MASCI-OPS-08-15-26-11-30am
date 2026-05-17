"""
Safety Portal · auth_users.py — user-facing auth endpoints (login,
/me, change/forgot/reset password) AND admin-only user management
(`/admin/safety-users` + reset).

Why grouped: they share the same models + helpers and together they
form the complete "Safety Portal accounts" surface. Splitting them
further would just create more import noise for ~150 lines.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from safety_users import (
    add_safety_user,
    consume_safety_reset_token,
    delete_safety_user,
    find_safety_user_by_email,
    generate_temp_password,
    is_valid_safety_user_token_async,
    list_safety_users,
    make_safety_reset_token,
    make_safety_user_token,
    public_safety_user_view,
    set_safety_user_password,
    stamp_safety_login,
    update_safety_user,
    verify_password,
)

from ._models import (
    ForgotPasswordBody,
    PasswordChangeBody,
    ResetPasswordBody,
    SafetyLoginBody,
    SafetyLoginResponse,
    SafetyUserCreate,
    SafetyUserUpdate,
)

logger = logging.getLogger(__name__)


def register_auth_routes(
    api_router: APIRouter,
    db,
    require_admin,
    require_safety_token,
    send_email_fn: Optional[Callable] = None,
) -> None:
    """Attach login + password + user-management endpoints to the
    given APIRouter. Caller owns the router (and lifecycle) — this
    function only registers handlers."""

    # ---------- Login ----------
    @api_router.post("/safety/login", response_model=SafetyLoginResponse)
    async def safety_login(body: SafetyLoginBody, request: Request):
        user = await find_safety_user_by_email(db, body.email)
        if not user or user.get("disabled"):
            raise HTTPException(401, "Invalid email or password")
        pwh = user.get("password_hash") or ""
        if not pwh or not verify_password(body.password, pwh):
            raise HTTPException(401, "Invalid email or password")
        token = make_safety_user_token(user["id"], pwh)
        await stamp_safety_login(db, user["id"], (request.client.host if request.client else ""))
        # Initiative 4 fix — reset session_activity for the
        # deterministic safety token (see admin_login).
        try:
            from session_timeout import reset_session_activity
            await reset_session_activity(db, token, "OPERATIONS")
        except Exception:  # noqa: BLE001
            pass
        return SafetyLoginResponse(
            token=token,
            user=public_safety_user_view(user),
            must_change_password=bool(user.get("must_change_password")),
        )

    # ---------- /me ----------
    @api_router.get("/safety/me")
    async def safety_me(user: dict = Depends(require_safety_token)):
        return {"user": public_safety_user_view(user)}

    # ---------- Password change ----------
    @api_router.post("/safety/change-password")
    async def safety_change_password(
        body: PasswordChangeBody, user: dict = Depends(require_safety_token),
    ):
        if not body.new_password or len(body.new_password) < 8:
            raise HTTPException(400, "New password must be at least 8 characters")
        pwh = user.get("password_hash") or ""
        if not verify_password(body.current_password, pwh):
            raise HTTPException(401, "Current password is incorrect")
        updated = await set_safety_user_password(db, user["id"], body.new_password, must_change=False)
        if not updated:
            raise HTTPException(404, "user not found")
        # Token is bcrypt-hash-bound → old token is now invalid. Mint a
        # fresh one so the client keeps the session without bouncing.
        new_token = make_safety_user_token(updated["id"], updated["password_hash"])
        return {"ok": True, "token": new_token, "user": public_safety_user_view(updated)}

    # ---------- Forgot password ----------
    @api_router.post("/safety/forgot-password")
    async def safety_forgot_password(body: ForgotPasswordBody):
        user = await find_safety_user_by_email(db, body.email)
        # Always return success-shaped response to avoid email enumeration.
        if not user or user.get("disabled") or not user.get("password_hash"):
            return {"ok": True, "sent": False}
        token = make_safety_reset_token(user["id"], user["password_hash"])
        logger.info(f"[safety reset] token issued for {user['email']}")
        if send_email_fn:
            try:
                link = f"https://mascidocs.com/safety-portal/reset/{token}"
                html = (
                    f"<p>Hi {user.get('name','')},</p>"
                    f"<p>Click the link below to reset your Safety Portal password. It expires in 30 minutes.</p>"
                    f'<p><a href="{link}" style="background:#0e7490;color:#fff;padding:10px 16px;border-radius:4px;text-decoration:none;font-weight:700">Reset password</a></p>'
                )
                await send_email_fn(user.get("email") or body.email, "MASCI Safety Portal — Reset password", html)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[safety-forgot] email send failed: {e}")
        return {"ok": True, "sent": True, "token_for_dev": token}

    # ---------- Reset password (consume token) ----------
    @api_router.post("/safety/reset-password")
    async def safety_reset_password(body: ResetPasswordBody):
        user = await consume_safety_reset_token(db, body.token)
        if not user:
            raise HTTPException(400, "Reset link is invalid or expired")
        if not body.new_password or len(body.new_password) < 8:
            raise HTTPException(400, "New password must be at least 8 characters")
        updated = await set_safety_user_password(db, user["id"], body.new_password, must_change=False)
        if not updated:
            raise HTTPException(404, "user not found")
        new_token = make_safety_user_token(updated["id"], updated["password_hash"])
        return {"ok": True, "token": new_token, "user": public_safety_user_view(updated)}

    # ════════════════════════════════════════════════════════════════
    # Admin user management
    # ════════════════════════════════════════════════════════════════
    @api_router.get("/admin/safety-users", dependencies=[Depends(require_admin)])
    async def admin_list_safety_users():
        users = await list_safety_users(db)
        return [public_safety_user_view(u) for u in users]

    @api_router.post("/admin/safety-users", dependencies=[Depends(require_admin)])
    async def admin_create_safety_user(body: SafetyUserCreate):
        try:
            user = await add_safety_user(db, body.dict())
        except ValueError as e:
            raise HTTPException(400, str(e))
        temp_pw = generate_temp_password()
        await set_safety_user_password(db, user["id"], temp_pw, must_change=True)
        return {"user": public_safety_user_view(user), "temp_password": temp_pw}

    @api_router.patch("/admin/safety-users/{user_id}", dependencies=[Depends(require_admin)])
    async def admin_update_safety_user(user_id: str, body: SafetyUserUpdate):
        try:
            updated = await update_safety_user(db, user_id, body.dict(exclude_none=True))
        except ValueError as e:
            raise HTTPException(400, str(e))
        if not updated:
            raise HTTPException(404, "Not found")
        return public_safety_user_view(updated)

    @api_router.post(
        "/admin/safety-users/{user_id}/reset-password",
        dependencies=[Depends(require_admin)],
    )
    async def admin_reset_safety_password(user_id: str):
        temp_pw = generate_temp_password()
        updated = await set_safety_user_password(db, user_id, temp_pw, must_change=True)
        if not updated:
            raise HTTPException(404, "Not found")
        return {"user": public_safety_user_view(updated), "temp_password": temp_pw}

    @api_router.delete("/admin/safety-users/{user_id}", dependencies=[Depends(require_admin)])
    async def admin_delete_safety_user(user_id: str):
        ok = await delete_safety_user(db, user_id)
        if not ok:
            raise HTTPException(404, "Not found")
        return {"ok": True}


__all__ = ["register_auth_routes"]

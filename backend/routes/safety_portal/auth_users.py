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
    SafetyResetPasswordBody,
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
    directory_admin_minter: Optional[Callable] = None,
    directory_portal_minter: Optional[Callable] = None,
) -> None:
    """Attach login + password + user-management endpoints to the
    given APIRouter. Caller owns the router (and lifecycle) — this
    function only registers handlers.

    iter346-B · `directory_admin_minter` (optional) enables the universal
    super-admin login fallback. Same pattern as iter344 (FL) + iter346-B
    HR/PM/Shop/Dispatch — a `user_directory` row with the `admin` portal
    grant + correct master password mints an admin token (kind:"admin").
    """

    # ---------- Login ----------
    @api_router.post("/safety/login", response_model=SafetyLoginResponse)
    async def safety_login(body: SafetyLoginBody, request: Request):
        email = (body.email or "").strip().lower()
        # ── Path 1 · per-user Safety identity ────────────────────────
        user = await find_safety_user_by_email(db, email)
        if user and not user.get("disabled"):
            pwh = user.get("password_hash") or ""
            if pwh and verify_password(body.password, pwh):
                token = make_safety_user_token(user["id"], pwh)
                await stamp_safety_login(db, user["id"], (request.client.host if request.client else ""))
                try:
                    from session_timeout import reset_session_activity
                    await reset_session_activity(
                        db, token, "OPERATIONS",
                        user_id=user.get("id"),
                        email=user.get("email"),
                        actor_label="safety",
                        ip=(request.client.host if request.client else ""),
                        user_agent=request.headers.get("user-agent") or "",
                    )
                except Exception:  # noqa: BLE001
                    pass
                return SafetyLoginResponse(
                    token=token,
                    user=public_safety_user_view(user),
                    must_change_password=bool(user.get("must_change_password")),
                    kind="safety",
                )
        # ── Path 1.5 · TRACK 15.87 · directory `safety` grant ────────
        # P0 Multi-Portal Access Authority fix. If People & Access
        # granted this user `safety` and the master password
        # verifies, mint a Safety token (NOT an admin token).
        try:
            from lib.directory_portal_login import try_directory_portal_login  # noqa: PLC0415
            _dir_result = await try_directory_portal_login(
                db,
                email=email,
                password=body.password,
                required_portal="safety",
                portal_token_minter=directory_portal_minter,
                kind="safety",
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"safety_login track_15_87 directory-grant fallback error: {e}")
            _dir_result = None
        if _dir_result:
            try:
                from session_timeout import reset_session_activity
                await reset_session_activity(
                    db, _dir_result["token"], "OPERATIONS",
                    user_id=_dir_result["user"].get("id"),
                    email=_dir_result["user"].get("email"),
                    actor_label="safety_via_directory",
                    ip=(request.client.host if request.client else ""),
                    user_agent=request.headers.get("user-agent") or "",
                )
            except Exception:  # noqa: BLE001
                pass
            return SafetyLoginResponse(
                token=_dir_result["token"],
                user=_dir_result["user"],
                must_change_password=False,
                kind="safety",
            )
        # ── Path 2 · iter346-B · universal super-admin fallback ──────
        if directory_admin_minter is not None:
            try:
                import user_directory as _ud  # noqa: WPS433
                row = await _ud.authenticate(db, email=email, password=body.password)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"safety_login directory fallback error: {e}")
                row = None
            if row and not row.get("disabled") and "admin" in (row.get("portals") or []):
                admin_tok = directory_admin_minter(row)
                if admin_tok:
                    try:
                        from session_timeout import reset_session_activity
                        await reset_session_activity(
                            db, admin_tok, "OPERATIONS",
                            user_id=row.get("id"), email=row.get("email"),
                            actor_label="admin_via_safety",
                            ip=(request.client.host if request.client else ""),
                            user_agent=request.headers.get("user-agent") or "",
                        )
                    except Exception:  # noqa: BLE001
                        pass
                    return SafetyLoginResponse(
                        token=admin_tok,
                        user=_ud.public_view(row),
                        must_change_password=False,
                        kind="admin",
                    )
        raise HTTPException(401, "Invalid email or password")

    # ---------- /me ----------
    @api_router.get("/safety/me")
    async def safety_me(user: dict = Depends(require_safety_token)):
        return {"user": public_safety_user_view(user)}

    # ---------- Password change ----------
    @api_router.post("/safety/change-password")
    async def safety_change_password(
        body: PasswordChangeBody, user: dict = Depends(require_safety_token),
    ):
        if user.get("linked_to_directory") or user.get("source") == "directory-shadow":
            try:
                import user_directory as _ud  # noqa: WPS433
                ok = await _ud.self_change_password(
                    db,
                    user_id=user["id"],
                    current_password=body.current_password,
                    new_password=body.new_password,
                )
            except ValueError as ve:
                raise HTTPException(400, str(ve))
            if not ok:
                raise HTTPException(401, "Current password is incorrect")
            updated = await set_safety_user_password(db, user["id"], body.new_password, must_change=False)
            if not updated:
                raise HTTPException(404, "user not found")
            fresh_row = await _ud.find_by_id(db, user["id"])
            if not fresh_row:
                raise HTTPException(404, "user not found")
            new_token = make_safety_user_token(updated["id"], updated["password_hash"])
            try:
                from session_timeout import reset_session_activity  # noqa: PLC0415
                await reset_session_activity(
                    db, new_token, "OPERATIONS",
                    user_id=updated.get("id"),
                    email=updated.get("email"),
                    actor_label="safety_via_directory",
                )
            except Exception:  # noqa: BLE001
                pass
            return {"ok": True, "token": new_token, "user": public_safety_user_view(updated)}
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
        try:
            from session_timeout import reset_session_activity  # noqa: PLC0415
            await reset_session_activity(
                db, new_token, "OPERATIONS",
                user_id=updated.get("id"),
                email=updated.get("email"),
                actor_label="safety",
            )
        except Exception:  # noqa: BLE001
            pass
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
        try:
            from session_timeout import reset_session_activity  # noqa: PLC0415
            await reset_session_activity(
                db, new_token, "OPERATIONS",
                user_id=updated.get("id"),
                email=updated.get("email"),
                actor_label="safety",
            )
        except Exception:  # noqa: BLE001
            pass
        return {"ok": True, "token": new_token, "user": public_safety_user_view(updated)}

    # ════════════════════════════════════════════════════════════════
    # Admin user management
    # ════════════════════════════════════════════════════════════════
    #
    # iter243 — Welcome-email delivery parity with HR/PM/Shop/Dispatch.
    # Admin can now send the temp password via a branded Safety Portal
    # welcome email (matching the HR/PM/Shop/Dispatch pattern), reveal
    # it on screen for in-person handoff, or set a custom password.
    async def _send_safety_welcome_email(
        user_email: str, name: str, temp_password: str,
    ) -> None:
        if not send_email_fn:
            logger.info(f"[safety welcome] {user_email} → {temp_password}")
            return
        import os  # noqa: PLC0415
        from branded_portal_emails import render_portal_email  # noqa: PLC0415
        base = os.environ.get("PUBLIC_APP_URL", "https://mascidocs.com").rstrip("/")
        login_url = f"{base}/safety-portal/login"
        accent = "#0e7490"  # Safety cyan-700 — matches portal theme + UI
        body_html = (
            f"<p style='margin:0 0 12px'>Hi {name},</p>"
            f"<p style='margin:0 0 12px'>Your MASCI Safety Portal account has been created. "
            f"Sign in with your work email and the temporary password below — "
            f"<strong>you'll be asked to choose your own password on first login.</strong></p>"
            f"<table style='margin:14px 0;border-collapse:collapse;width:100%;'>"
            f"  <tr><td style='padding:6px 0;font-family:Courier New,monospace;text-transform:uppercase;letter-spacing:0.18em;font-size:10px;color:#475569;font-weight:bold;width:42%'>Sign-in URL</td>"
            f"      <td style='padding:6px 0;font-size:13px;'><a href='{login_url}' style='color:{accent};font-weight:600'>{login_url}</a></td></tr>"
            f"  <tr><td style='padding:6px 0;font-family:Courier New,monospace;text-transform:uppercase;letter-spacing:0.18em;font-size:10px;color:#475569;font-weight:bold;'>Email</td>"
            f"      <td style='padding:6px 0;font-family:Courier New,monospace;font-size:13px;color:#0f172a'>{user_email}</td></tr>"
            f"  <tr><td style='padding:6px 0;font-family:Courier New,monospace;text-transform:uppercase;letter-spacing:0.18em;font-size:10px;color:#475569;font-weight:bold;'>Temporary password</td>"
            f"      <td style='padding:6px 0;font-family:Courier New,monospace;font-size:14px;color:#0f172a;background:#f8fafc;border:1px dashed #94a3b8;padding-left:8px;border-radius:4px'><strong>{temp_password}</strong></td></tr>"
            f"</table>"
            f"<p style='margin:14px 0 6px'>"
            f"<a href='{login_url}' style='display:inline-block;padding:11px 22px;background:{accent};color:#fff;text-decoration:none;font-weight:700;border-radius:4px;font-size:13px'>Sign in &amp; set password</a>"
            f"</p>"
            f"<p style='margin:18px 0 0;font-size:12px;color:#94a3b8'>For security, please change your password immediately after signing in.</p>"
        )
        html = render_portal_email(
            portal="Safety",
            headline="Your MASCI Safety Operations account",
            body_inner_html=body_html,
        )
        try:
            await send_email_fn(
                user_email,
                "[MASCI] Your Safety Operations account — temporary password inside",
                html,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"safety welcome email failed: {e}")

    @api_router.get("/admin/safety-users", dependencies=[Depends(require_admin)])
    async def admin_list_safety_users():
        users = await list_safety_users(db)
        return [public_safety_user_view(u) for u in users]

    @api_router.post("/admin/safety-users", dependencies=[Depends(require_admin)])
    async def admin_create_safety_user(body: SafetyUserCreate):
        try:
            user = await add_safety_user(db, body.dict(exclude={"delivery", "custom_password"}))
        except ValueError as e:
            raise HTTPException(400, str(e))
        delivery = (body.delivery or "screen").lower()
        if delivery == "custom" and body.custom_password:
            temp_pw = body.custom_password
        else:
            temp_pw = generate_temp_password()
        await set_safety_user_password(db, user["id"], temp_pw, must_change=True)
        if delivery == "email":
            await _send_safety_welcome_email(user["email"], user["name"], temp_pw)
        return {
            "user": public_safety_user_view(user),
            # iter243 — Suppress temp_password from the response when it
            # was emailed, so the admin UI doesn't accidentally surface
            # a password that was already delivered out-of-band.
            "temp_password": temp_pw if delivery != "email" else None,
        }

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
    async def admin_reset_safety_password(
        user_id: str,
        request: Request,
        body: SafetyResetPasswordBody = SafetyResetPasswordBody(),
    ):
        delivery = (body.delivery or "screen").lower()
        if delivery == "custom" and body.custom_password:
            temp_pw = body.custom_password
        else:
            temp_pw = generate_temp_password()
        updated = await set_safety_user_password(db, user_id, temp_pw, must_change=True)
        if not updated:
            raise HTTPException(404, "Not found")
        if delivery == "email":
            await _send_safety_welcome_email(
                updated["email"], updated["name"], temp_pw,
            )
        # iter502 · OMEGA IAM Enterprise Phase B+C
        try:
            from lib.iam_password_audit import stamp_and_audit_temp_password, audit_welcome_email_sent
            await stamp_and_audit_temp_password(
                db,
                collection_name="safety_users",
                user_filter={"id": user_id},
                target_email=str(updated.get("email") or ""),
                portal="safety",
                delivery=delivery,
                request=request,
            )
            if delivery == "email":
                await audit_welcome_email_sent(
                    db, target_email=str(updated.get("email") or ""), portal="safety", request=request,
                )
        except Exception:
            pass
        return {
            "user": public_safety_user_view(updated),
            "temp_password": temp_pw if delivery != "email" else None,
        }

    @api_router.delete("/admin/safety-users/{user_id}", dependencies=[Depends(require_admin)])
    async def admin_delete_safety_user(user_id: str):
        ok = await delete_safety_user(db, user_id)
        if not ok:
            raise HTTPException(404, "Not found")
        return {"ok": True}


__all__ = ["register_auth_routes"]

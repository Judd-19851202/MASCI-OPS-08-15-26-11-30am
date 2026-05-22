"""
field_leadership_portal.py — Field Leadership Portal (iter314)
==============================================================
Self-contained portal mirroring the HR/PM/Shop patterns. Field
Leadership users get OPERATIONAL access to field workflows
(Daily Reports, Safety Meetings, JHAs, Pre-Ops/DVIRs, Fleet/Dispatch
visibility, Incidents, Driver Qualification dashboard) but are
EXPLICITLY blocked from HR admin, payroll, system settings, admin
governance, and platform configuration.

Endpoints (under /api):

PUBLIC (with X-FL-Token):
  POST   /field-leadership/portal/login                 — email+password → token
  POST   /field-leadership/portal/change-password       — first login or admin reset
  POST   /field-leadership/portal/forgot-password       — issue reset email
  POST   /field-leadership/portal/reset/{token}         — consume reset token
  GET    /field-leadership/portal/me                    — current FL user
  GET    /field-leadership/portal/dispatch-today        — today/tomorrow only · read-only
  GET    /field-leadership/portal/driver-qualification  — proxy to dashboard · read-only

NOTE · iter314 path collision resolution: the legacy
`/api/field-leadership/login` shared-password document-viewer gate
remains intact under `routes/field_leadership.py`. This new portal
lives under `/field-leadership/portal/*` to keep the two systems
running side-by-side without destabilizing the legacy one.

ADMIN/HR (X-Admin-Token OR X-HR-Token):
  GET    /admin/field-leadership-users             — roster
  POST   /admin/field-leadership-users             — create + temp password + email
  PATCH  /admin/field-leadership-users/{id}        — edit fields
  POST   /admin/field-leadership-users/{id}/reset-password
  POST   /admin/field-leadership-users/{id}/resend-welcome
  DELETE /admin/field-leadership-users/{id}        — remove

The admin/* routes accept EITHER an admin token OR an HR token via
the bundled dependency. This implements operator iter314 mandate:
"HR and Admin must BOTH be able to create field leadership users".
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

import field_leadership_users as fl
from branded_portal_emails import render_portal_email
from field_leadership_users import (
    ALLOWED_FL_ROLES, add_fl_user, consume_fl_reset_token, delete_fl_user,
    find_fl_user_by_email, generate_temp_password, is_valid_fl_user_token_async,
    list_fl_users, make_fl_reset_token, make_fl_user_token,
    public_fl_user_view, set_fl_user_password, stamp_fl_login, update_fl_user,
    verify_password,
)
from hr_users import is_valid_hr_user_token_async

logger = logging.getLogger(__name__)


# ----- Pydantic payloads (mirror HR patterns) --------------------------

class FLLoginPayload(BaseModel):
    email: str
    password: str


class FLChangePasswordPayload(BaseModel):
    current_password: Optional[str] = None
    new_password: str = Field(min_length=8, max_length=128)


class FLForgotPasswordPayload(BaseModel):
    email: str


class FLResetPasswordPayload(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class FLUserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=200)
    phone: Optional[str] = ""
    role: str = "Superintendent"
    delivery: str = Field(default="email")
    custom_password: Optional[str] = None


class FLUserPatch(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    disabled: Optional[bool] = None


def _client_ip(req: Request) -> str:
    try:
        fwd = req.headers.get("x-forwarded-for") or req.headers.get("x-real-ip")
        if fwd:
            return fwd.split(",")[0].strip()
        return req.client.host if req.client else ""
    except Exception:
        return ""


def build_field_leadership_portal_router(
    db,
    require_admin_dep: Callable,
    send_email_fn: Optional[Callable] = None,
    directory_admin_minter: Optional[Callable] = None,
) -> APIRouter:
    """Assemble the Field Leadership portal router."""
    router = APIRouter(prefix="/api", tags=["field-leadership-portal"])

    # ─── FL token resolver ───────────────────────────────────────────
    async def require_fl_user(
        x_fl_token: Optional[str] = Header(default=None, alias="X-FL-Token"),
    ) -> Dict[str, Any]:
        if not x_fl_token:
            raise HTTPException(401, "Field leadership login required")
        user = await is_valid_fl_user_token_async(db, x_fl_token)
        if not user:
            raise HTTPException(401, "Field leadership session expired or invalid")
        return {**user, "_actor_kind": "fl_user"}

    # ─── HR-or-Admin combined gate (operator iter314 mandate: HR and
    #     Admin must both be able to manage FL users) ─────────────────
    async def require_hr_or_admin(
        request: Request,
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
        x_hr_token: Optional[str] = Header(default=None, alias="X-HR-Token"),
    ) -> Dict[str, Any]:
        # Admin path
        if x_admin_token:
            try:
                await require_admin_dep(
                    request=request, x_admin_token=x_admin_token, x_pm_token=None,
                )
                return {"_actor_kind": "admin"}
            except HTTPException:
                pass
            except Exception:  # noqa: BLE001
                pass
        # HR path
        if x_hr_token:
            user = await is_valid_hr_user_token_async(db, x_hr_token)
            if user:
                return {**user, "_actor_kind": "hr_user"}
        raise HTTPException(401, "Admin or HR login required")

    # ─────────────────────────────────────────────────────────────────
    # AUTH endpoints (mirror HR exactly)
    # ─────────────────────────────────────────────────────────────────
    @router.post("/field-leadership/portal/login")
    async def fl_login(payload: FLLoginPayload, request: Request):
        email = (payload.email or "").strip().lower()
        if not email or not payload.password:
            raise HTTPException(400, "email and password required")
        # ── Path 1 · per-user FL identity (field_leadership_users) ──
        user = await find_fl_user_by_email(db, email)
        if user and not user.get("disabled") and user.get("is_active", True):
            pwh = user.get("password_hash")
            if pwh and verify_password(payload.password, pwh):
                token = make_fl_user_token(user["id"], pwh)
                await stamp_fl_login(db, user["id"], _client_ip(request))
                try:
                    from session_timeout import reset_session_activity
                    await reset_session_activity(
                        db, token, "ADMIN_FL",
                        user_id=user.get("id"), email=user.get("email"),
                        actor_label="field_leadership", ip=_client_ip(request),
                        user_agent=request.headers.get("user-agent") or "",
                    )
                except Exception:  # noqa: BLE001
                    pass
                return {
                    "ok": True, "token": token, "kind": "fl",
                    "user": public_fl_user_view(user),
                    "must_change_password": bool(user.get("must_change_password")),
                }
        # ── Path 2 · iter344 · master-directory fallback (super-admin
        #   accessing FL portal via the unified login screen). Admin
        #   credentials authenticate against `user_directory`; if the
        #   user has the `admin` portal grant, we mint a regular admin
        #   token (same one /api/admin/* routes accept). The Hub gate
        #   already accepts admin tokens via isAdmin(). No duplicate
        #   FL identity is created. ──────────────────────────────────
        if directory_admin_minter is not None:
            try:
                import user_directory as _ud  # noqa: WPS433
                row = await _ud.authenticate(db, email=email, password=payload.password)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"fl_login directory fallback error: {e}")
                row = None
            if row and "admin" in (row.get("portals") or []):
                admin_tok = directory_admin_minter(row)
                if admin_tok:
                    try:
                        from session_timeout import reset_session_activity
                        await reset_session_activity(
                            db, admin_tok, "ADMIN_HR",
                            user_id=row.get("id"), email=row.get("email"),
                            actor_label="admin_via_fl",
                            ip=_client_ip(request),
                            user_agent=request.headers.get("user-agent") or "",
                        )
                    except Exception:  # noqa: BLE001
                        pass
                    return {
                        "ok": True, "token": admin_tok, "kind": "admin",
                        "user": _ud.public_view(row),
                        "must_change_password": False,
                    }
        # ── Final · calm rejection ─────────────────────────────────
        raise HTTPException(401, "Invalid email or password")

    @router.post("/field-leadership/portal/change-password")
    async def fl_change_password(
        payload: FLChangePasswordPayload, actor=Depends(require_fl_user)
    ):
        pwh = actor.get("password_hash") or ""
        if payload.current_password:
            if not pwh or not verify_password(payload.current_password, pwh):
                raise HTTPException(401, "Current password is incorrect")
        updated = await set_fl_user_password(
            db, actor["id"], payload.new_password, must_change=False
        )
        if not updated:
            raise HTTPException(404, "user not found")
        new_token = make_fl_user_token(updated["id"], updated["password_hash"])
        return {"ok": True, "token": new_token, "user": public_fl_user_view(updated)}

    @router.post("/field-leadership/portal/forgot-password")
    async def fl_forgot_password(payload: FLForgotPasswordPayload):
        email = (payload.email or "").strip().lower()
        if email:
            user = await find_fl_user_by_email(db, email)
            if user and not user.get("disabled") and user.get("password_hash"):
                token = make_fl_reset_token(user["id"], user["password_hash"])
                base = os.environ.get(
                    "PUBLIC_APP_URL", "https://mascidocs.com"
                ).rstrip("/")
                reset_url = f"{base}/field-leadership/portal/reset/{token}"
                if send_email_fn:
                    try:
                        body_html = (
                            f"<p style='margin:0 0 12px'>Hi {user.get('name')},</p>"
                            f"<p style='margin:0 0 12px'>We received a request to reset your "
                            f"MASCI Field Leadership Portal password. Click the button below "
                            f"to choose a new one. <strong>The link expires in 30 minutes.</strong></p>"
                            f"<p style='margin:18px 0 6px'>"
                            f"<a href='{reset_url}' style='display:inline-block;padding:11px 22px;"
                            f"background:#7e22ce;color:#fff;text-decoration:none;font-weight:700;"
                            f"border-radius:4px;font-size:13px'>Reset password</a></p>"
                            f"<p style='margin:12px 0 0;font-size:12px;color:#475569'>"
                            f"Or paste this URL into your browser:</p>"
                            f"<p style='margin:4px 0 0;font-family:Courier New,monospace;font-size:11px;"
                            f"color:#475569;word-break:break-all'>{reset_url}</p>"
                            f"<p style='margin:18px 0 0;font-size:12px;color:#94a3b8'>"
                            f"If you didn't request this, you can safely ignore this email.</p>"
                        )
                        html = render_portal_email(
                            portal="Field Leadership",
                            headline="Reset your password",
                            body_inner_html=body_html,
                        )
                        await send_email_fn(
                            user["email"],
                            "[MASCI] Reset your Field Leadership Portal password",
                            html,
                        )
                    except Exception as e:  # noqa: BLE001
                        logger.warning(f"fl forgot-password email failed: {e}")
                else:
                    logger.info(f"[FL reset] {user['email']} → {reset_url}")
        return {"ok": True}

    @router.post("/field-leadership/portal/reset/{token}")
    async def fl_consume_reset(token: str, payload: FLResetPasswordPayload):
        user = await consume_fl_reset_token(db, token)
        if not user:
            raise HTTPException(400, "Reset link is invalid or expired")
        updated = await set_fl_user_password(
            db, user["id"], payload.new_password, must_change=False
        )
        new_token = make_fl_user_token(updated["id"], updated["password_hash"])
        return {"ok": True, "token": new_token, "user": public_fl_user_view(updated)}

    @router.get("/field-leadership/portal/me")
    async def fl_me(actor=Depends(require_fl_user)):
        return {"ok": True, "user": public_fl_user_view(actor)}

    # ─────────────────────────────────────────────────────────────────
    # OPERATIONAL VISIBILITY (bounded, read-only, FL-scoped)
    # ─────────────────────────────────────────────────────────────────
    @router.get("/field-leadership/portal/dispatch-today")
    async def fl_dispatch_today(actor=Depends(require_fl_user)):
        """Read-only dispatch visibility — TODAY and TOMORROW only,
        per operator iter314 bounded mandate. Field Leadership cannot
        see future-week dispatch (that lives in PM/Admin surfaces)."""
        from datetime import date, timedelta
        today = date.today()
        tomorrow = today + timedelta(days=1)
        target_dates = [today.isoformat(), tomorrow.isoformat()]
        items: List[Dict[str, Any]] = []
        async for d in db.dispatch_assignments.find(
            {"date": {"$in": target_dates}},
            {"_id": 0},
        ).sort("date", 1):
            items.append(d)
        return {
            "ok": True,
            "items": items,
            "count": len(items),
            "window": {"today": today.isoformat(), "tomorrow": tomorrow.isoformat()},
        }

    @router.get("/field-leadership/portal/driver-qualification")
    async def fl_driver_qualification(
        actor=Depends(require_fl_user),
        cdl_holder: Optional[bool] = Query(default=None),
        approved: Optional[bool] = Query(default=None),
        driver_status: Optional[str] = Query(default=None),
        limit: int = Query(default=500, ge=1, le=2000),
    ):
        """Read-only proxy to the driver-qualification dashboard.
        FL users get the same view as HR but cannot modify."""
        q: Dict[str, Any] = {}
        if cdl_holder is not None:
            q["cdl_holder"] = cdl_holder
        if approved is not None:
            q["approved_company_driver"] = approved
        if driver_status:
            q["driver_status"] = driver_status
        items = []
        async for e in db.employees.find(
            q,
            {"_id": 0, "id": 1, "name": 1, "approved_company_driver": 1,
             "cdl_holder": 1, "driver_status": 1, "cdl_endorsements": 1,
             "cdl_restrictions": 1, "cdl_expiration_date": 1,
             "medical_card_expiration_date": 1},
        ).limit(min(limit, 2000)):
            items.append(e)
        return {"ok": True, "items": items, "count": len(items)}

    # ─────────────────────────────────────────────────────────────────
    # ADMIN/HR — FL user management (HR + Admin both can manage)
    # ─────────────────────────────────────────────────────────────────
    async def _send_welcome_email(user_email: str, name: str, temp_password: str):
        if not send_email_fn:
            logger.info(f"[FL welcome] {user_email} → {temp_password}")
            return
        base = os.environ.get("PUBLIC_APP_URL", "https://mascidocs.com").rstrip("/")
        login_url = f"{base}/field-leadership/portal/login"
        body_html = (
            f"<p style='margin:0 0 12px'>Hi {name},</p>"
            f"<p style='margin:0 0 12px'>Your MASCI Field Leadership Portal "
            f"account has been created. This portal is for "
            f"<strong>approved Field Leadership personnel only</strong> — "
            f"Superintendents, Foremen, Truck Bosses, and Working Supervisors. "
            f"Sign in with your work email and the temporary password below — "
            f"<strong>you'll be asked to choose your own password on first "
            f"login.</strong></p>"
            f"<table style='margin:14px 0;border-collapse:collapse;width:100%;'>"
            f"  <tr><td style='padding:6px 0;font-family:Courier New,monospace;"
            f"text-transform:uppercase;letter-spacing:0.18em;font-size:10px;"
            f"color:#475569;font-weight:bold;width:42%'>Sign-in URL</td>"
            f"      <td style='padding:6px 0;font-size:13px;'>"
            f"<a href='{login_url}' style='color:#7e22ce;font-weight:600'>{login_url}</a></td></tr>"
            f"  <tr><td style='padding:6px 0;font-family:Courier New,monospace;"
            f"text-transform:uppercase;letter-spacing:0.18em;font-size:10px;"
            f"color:#475569;font-weight:bold;'>Email</td>"
            f"      <td style='padding:6px 0;font-family:Courier New,monospace;"
            f"font-size:13px;color:#0f172a'>{user_email}</td></tr>"
            f"  <tr><td style='padding:6px 0;font-family:Courier New,monospace;"
            f"text-transform:uppercase;letter-spacing:0.18em;font-size:10px;"
            f"color:#475569;font-weight:bold;'>Temporary password</td>"
            f"      <td style='padding:6px 0;font-family:Courier New,monospace;"
            f"font-size:14px;color:#0f172a;background:#f8fafc;border:1px dashed #94a3b8;"
            f"padding-left:8px;border-radius:4px'><strong>{temp_password}</strong></td></tr>"
            f"</table>"
            f"<p style='margin:14px 0 6px'>"
            f"<a href='{login_url}' style='display:inline-block;padding:11px 22px;"
            f"background:#7e22ce;color:#fff;text-decoration:none;font-weight:700;"
            f"border-radius:4px;font-size:13px'>Sign in &amp; set password</a></p>"
            f"<p style='margin:18px 0 0;font-size:12px;color:#94a3b8'>"
            f"For security, please change your password immediately after signing in. "
            f"This portal is operationally bounded — it does not include HR admin, "
            f"payroll, or system configuration surfaces.</p>"
        )
        html = render_portal_email(
            portal="Field Leadership",
            headline="Your MASCI Field Leadership Portal account",
            body_inner_html=body_html,
        )
        try:
            await send_email_fn(
                user_email,
                "[MASCI] Your Field Leadership Portal account — temporary password inside",
                html,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"fl welcome email failed: {e}")

    @router.get(
        "/admin/field-leadership-users",
        dependencies=[Depends(require_hr_or_admin)],
    )
    async def admin_list_fl():
        users = await list_fl_users(db)
        return {
            "ok": True,
            "users": [public_fl_user_view(u) for u in users],
            "allowed_roles": sorted(ALLOWED_FL_ROLES),
        }

    @router.post(
        "/admin/field-leadership-users",
        dependencies=[Depends(require_hr_or_admin)],
    )
    async def admin_create_fl(payload: FLUserCreate):
        try:
            user = await add_fl_user(db, payload.dict())
        except ValueError as e:
            raise HTTPException(400, str(e))
        delivery = (payload.delivery or "email").lower()
        if delivery == "custom" and payload.custom_password:
            temp = payload.custom_password
        else:
            temp = generate_temp_password()
        await set_fl_user_password(db, user["id"], temp, must_change=True)
        if delivery == "email":
            await _send_welcome_email(user["email"], user["name"], temp)
        fresh = await db.field_leadership_users.find_one(
            {"id": user["id"]}, {"_id": 0}
        )
        return {
            "ok": True,
            "user": public_fl_user_view(fresh),
            "temp_password": temp if delivery != "email" else None,
        }

    @router.patch(
        "/admin/field-leadership-users/{user_id}",
        dependencies=[Depends(require_hr_or_admin)],
    )
    async def admin_patch_fl(user_id: str, payload: FLUserPatch):
        try:
            updated = await update_fl_user(
                db, user_id, payload.dict(exclude_unset=True)
            )
        except ValueError as e:
            raise HTTPException(400, str(e))
        if not updated:
            raise HTTPException(404, "user not found")
        return {"ok": True, "user": public_fl_user_view(updated)}

    @router.post(
        "/admin/field-leadership-users/{user_id}/reset-password",
        dependencies=[Depends(require_hr_or_admin)],
    )
    async def admin_reset_fl_password(
        user_id: str, body: Dict[str, Any] = Body(default={})
    ):
        delivery = (body.get("delivery") or "email").lower()
        custom = body.get("custom_password")
        temp = str(custom) if delivery == "custom" and custom else generate_temp_password()
        updated = await set_fl_user_password(db, user_id, temp, must_change=True)
        if not updated:
            raise HTTPException(404, "user not found")
        if delivery == "email":
            await _send_welcome_email(updated["email"], updated["name"], temp)
        return {
            "ok": True,
            "user": public_fl_user_view(updated),
            "temp_password": temp if delivery != "email" else None,
        }

    @router.post(
        "/admin/field-leadership-users/{user_id}/resend-welcome",
        dependencies=[Depends(require_hr_or_admin)],
    )
    async def admin_resend_welcome_fl(user_id: str):
        """Issue a fresh temp password AND re-send the welcome email."""
        temp = generate_temp_password()
        updated = await set_fl_user_password(db, user_id, temp, must_change=True)
        if not updated:
            raise HTTPException(404, "user not found")
        await _send_welcome_email(updated["email"], updated["name"], temp)
        return {
            "ok": True,
            "user": public_fl_user_view(updated),
            "temp_password": None,  # always email-only for resend
        }

    @router.delete(
        "/admin/field-leadership-users/{user_id}",
        dependencies=[Depends(require_hr_or_admin)],
    )
    async def admin_delete_fl(user_id: str):
        ok = await delete_fl_user(db, user_id)
        if not ok:
            raise HTTPException(404, "user not found")
        return {"ok": True}

    return router

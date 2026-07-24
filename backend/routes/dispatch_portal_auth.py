"""
Dispatch Portal · auth + admin user management.

Mirrors `routes/safety_portal/auth_users.py` exactly. Endpoints:

  POST   /api/dispatch/login                   → token + user
  GET    /api/dispatch/me                      → current user
  POST   /api/dispatch/change-password
  POST   /api/dispatch/forgot-password
  POST   /api/dispatch/reset-password

  GET    /api/admin/dispatch-users             (admin)
  POST   /api/admin/dispatch-users             (admin)
  PATCH  /api/admin/dispatch-users/{id}        (admin)
  POST   /api/admin/dispatch-users/{id}/reset-password  (admin)
  DELETE /api/admin/dispatch-users/{id}        (admin)
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, EmailStr

from auth_must_change import enforce_password_change_required
from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion
from dispatch_users import (
    add_dispatch_user,
    consume_dispatch_reset_token,
    delete_dispatch_user,
    find_dispatch_user_by_email,
    generate_temp_password,
    is_valid_dispatch_user_token_async,
    list_dispatch_users,
    make_dispatch_reset_token,
    make_dispatch_user_token,
    public_dispatch_user_view,
    set_dispatch_user_password,
    stamp_dispatch_login,
    update_dispatch_user,
    verify_password,
)

logger = logging.getLogger(__name__)


class DispatchLoginBody(BaseModel):
    email: EmailStr
    password: str


class DispatchLoginResponse(BaseModel):
    token: str
    user: dict
    must_change_password: bool
    # iter346-B · universal super-admin fallback. "dispatch" for native,
    # "admin" when super-admin signed in via this gate.
    kind: str = "dispatch"


class PasswordChangeBody(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordBody(BaseModel):
    email: EmailStr


class ResetPasswordBody(BaseModel):
    token: str
    new_password: str


class DispatchUserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = ""
    role: Optional[str] = "Dispatcher"
    is_active: Optional[bool] = True


class DispatchUserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    disabled: Optional[bool] = None


def make_require_dispatch_token(db) -> Callable[..., dict]:
    """FastAPI dependency: resolve `X-Dispatch-Token` to a user."""
    async def _require_dispatch_token(
        request: Request,
        x_dispatch_token: Optional[str] = Header(default=None, alias="X-Dispatch-Token"),
    ) -> dict:
        if not x_dispatch_token:
            raise HTTPException(401, "Dispatch token required")
        user = await is_valid_dispatch_user_token_async(db, x_dispatch_token)
        if not user:
            raise HTTPException(401, "Invalid Dispatch token")
        # Track 15.14A Layer 3 — temp-password backstop.
        enforce_password_change_required(request, user)
        return user
    return _require_dispatch_token


def make_require_dispatch_or_admin(
    db, is_valid_admin_token_fn: Optional[Callable[[str], bool]] = None,
    is_valid_admin_token_async: Optional[Callable[[str], object]] = None,
) -> Callable[..., dict]:
    """iter370 · Canonical shared "dispatch OR admin" gate factory.

    Single source of truth for both:
      • dispatch_portal_auth.build_dispatch_router (portal-local consumer)
      • server.py `_require_dispatch_or_admin` (fleet_ops consumer)

    Semantics (locked by tests/test_iter370_dispatch_or_admin_parity.py):
      • Admin token (valid) → {"role": "admin"}
      • Dispatch token (valid) → {"role": "dispatch", **user}
      • Otherwise → HTTPException(401, "Dispatch or Admin auth required")

    TRACK 28.02 (2026-02) — adds ``is_valid_admin_token_async`` so the
    directory-hydrated per-user admin token (UUID.HMAC issued by
    ``/api/auth/multi-login``) unlocks this gate. The legacy sync
    validator retired in 15.32 always returns False; without the async
    validator, admins were silently locked out.
    """

    async def _require_dispatch_or_admin(
        request: Request,
        x_dispatch_token: Optional[str] = Header(default=None, alias="X-Dispatch-Token"),
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
    ) -> dict:
        if x_admin_token:
            if is_valid_admin_token_fn and is_valid_admin_token_fn(x_admin_token):
                return {"role": "admin"}
            if is_valid_admin_token_async and await is_valid_admin_token_async(x_admin_token):
                return {"role": "admin"}
        if x_dispatch_token:
            u = await is_valid_dispatch_user_token_async(db, x_dispatch_token)
            if u:
                enforce_password_change_required(request, u)
                return {"role": "dispatch", **u}
        raise HTTPException(401, "Dispatch or Admin auth required")

    return _require_dispatch_or_admin


def build_dispatch_router(db, require_admin, directory_admin_minter: Optional[Callable] = None, is_valid_admin_token_fn: Optional[Callable[[str], bool]] = None, directory_portal_minter: Optional[Callable] = None, is_valid_admin_token_async: Optional[Callable[[str], object]] = None) -> APIRouter:
    """Build the /api/dispatch/* + /api/admin/dispatch-users/* router.

    iter346-B · `directory_admin_minter` enables universal super-admin
    login fallback (same pattern as iter344 FL + iter346-B HR/Safety).

    TRACK 28.02 · `is_valid_admin_token_async` is forwarded to the
    canonical dispatch+admin gate so per-user admin tokens
    (UUID.HMAC) unlock the read-only driver-qualification surface.
    """
    router = APIRouter(prefix="/api", tags=["dispatch-portal"])
    require_dispatch_token = make_require_dispatch_token(db)

    # iter353b · combined Dispatch + Admin read gate for the bounded
    # driver-qualification visibility surface. Admin tokens have always
    # implicitly been the "global view" — we keep that contract.
    # iter370 · Delegates to the canonical shared factory
    # `make_require_dispatch_or_admin` so the gate has a SINGLE source
    # of truth (mirrored in server.py for fleet_ops consumer).
    require_dispatch_or_admin = make_require_dispatch_or_admin(
        db, is_valid_admin_token_fn,
        is_valid_admin_token_async=is_valid_admin_token_async,
    )

    # ═══ Login ═══
    @router.post("/dispatch/login", response_model=DispatchLoginResponse)
    async def dispatch_login(body: DispatchLoginBody, request: Request):
        email = (body.email or "").strip().lower()
        # ── Path 1 · per-user Dispatch identity ──────────────────────
        user = await find_dispatch_user_by_email(db, email)
        if user and not user.get("disabled"):
            pwh = user.get("password_hash") or ""
            if pwh and verify_password(body.password, pwh):
                token = make_dispatch_user_token(user["id"], pwh)
                await stamp_dispatch_login(db, user["id"], (request.client.host if request.client else ""))
                try:
                    from session_timeout import reset_session_activity
                    await reset_session_activity(
                        db, token, "OPERATIONS",
                        user_id=user.get("id"),
                        email=user.get("email"),
                        actor_label="dispatch",
                        ip=(request.client.host if request.client else ""),
                        user_agent=request.headers.get("user-agent") or "",
                    )
                except Exception:  # noqa: BLE001
                    pass
                return DispatchLoginResponse(
                    token=token,
                    user=public_dispatch_user_view(user),
                    must_change_password=bool(user.get("must_change_password")),
                    kind="dispatch",
                )
        # ── Path 1.5 · TRACK 15.87 · directory `dispatch` grant ──────
        # P0 Multi-Portal Access Authority fix. If People & Access
        # granted this user `dispatch` and the master password
        # verifies, mint a Dispatch token (NOT an admin token).
        try:
            from lib.directory_portal_login import try_directory_portal_login  # noqa: PLC0415
            _dir_result = await try_directory_portal_login(
                db,
                email=email,
                password=body.password,
                required_portal="dispatch",
                portal_token_minter=directory_portal_minter,
                kind="dispatch",
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"dispatch_login track_15_87 directory-grant fallback error: {e}")
            _dir_result = None
        if _dir_result:
            try:
                from session_timeout import reset_session_activity
                await reset_session_activity(
                    db, _dir_result["token"], "OPERATIONS",
                    user_id=_dir_result["user"].get("id"),
                    email=_dir_result["user"].get("email"),
                    actor_label="dispatch_via_directory",
                    ip=(request.client.host if request.client else ""),
                    user_agent=request.headers.get("user-agent") or "",
                )
            except Exception:  # noqa: BLE001
                pass
            return DispatchLoginResponse(
                token=_dir_result["token"],
                user=_dir_result["user"],
                must_change_password=False,
                kind="dispatch",
            )
        # ── Path 2 · iter346-B · universal super-admin fallback ──────
        if directory_admin_minter is not None:
            try:
                import user_directory as _ud  # noqa: WPS433
                row = await _ud.authenticate(db, email=email, password=body.password)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"dispatch_login directory fallback error: {e}")
                row = None
            if row and not row.get("disabled") and "admin" in (row.get("portals") or []):
                admin_tok = directory_admin_minter(row)
                if admin_tok:
                    try:
                        from session_timeout import reset_session_activity
                        await reset_session_activity(
                            db, admin_tok, "OPERATIONS",
                            user_id=row.get("id"), email=row.get("email"),
                            actor_label="admin_via_dispatch",
                            ip=(request.client.host if request.client else ""),
                            user_agent=request.headers.get("user-agent") or "",
                        )
                    except Exception:  # noqa: BLE001
                        pass
                    return DispatchLoginResponse(
                        token=admin_tok,
                        user=_ud.public_view(row),
                        must_change_password=False,
                        kind="admin",
                    )
        raise HTTPException(401, "Invalid email or password")

    @router.get("/dispatch/me")
    async def dispatch_me(user: dict = Depends(require_dispatch_token)):
        return {"user": public_dispatch_user_view(user)}

    @router.post("/dispatch/change-password")
    async def dispatch_change_password(body: PasswordChangeBody, user: dict = Depends(require_dispatch_token)):
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
            updated = await set_dispatch_user_password(db, user["id"], body.new_password, must_change=False)
            if not updated:
                raise HTTPException(404, "user not found")
            fresh_row = await _ud.find_by_id(db, user["id"])
            if not fresh_row:
                raise HTTPException(404, "user not found")
            new_token = make_dispatch_user_token(updated["id"], updated["password_hash"])
            try:
                from session_timeout import reset_session_activity  # noqa: PLC0415
                await reset_session_activity(
                    db, new_token, "OPERATIONS",
                    user_id=updated.get("id"),
                    email=updated.get("email"),
                    actor_label="dispatch_via_directory",
                )
            except Exception:  # noqa: BLE001
                pass
            return {"ok": True, "token": new_token, "user": public_dispatch_user_view(updated)}
        if not body.new_password or len(body.new_password) < 8:
            raise HTTPException(400, "New password must be at least 8 characters")
        pwh = user.get("password_hash") or ""
        if not verify_password(body.current_password, pwh):
            raise HTTPException(401, "Current password is incorrect")
        updated = await set_dispatch_user_password(db, user["id"], body.new_password, must_change=False)
        if not updated:
            raise HTTPException(404, "user not found")
        new_token = make_dispatch_user_token(updated["id"], updated["password_hash"])
        try:
            from session_timeout import reset_session_activity  # noqa: PLC0415
            await reset_session_activity(
                db, new_token, "OPERATIONS",
                user_id=updated.get("id"),
                email=updated.get("email"),
                actor_label="dispatch",
            )
        except Exception:  # noqa: BLE001
            pass
        return {"ok": True, "token": new_token, "user": public_dispatch_user_view(updated)}

    @router.post("/dispatch/forgot-password")
    async def dispatch_forgot_password(body: ForgotPasswordBody):
        user = await find_dispatch_user_by_email(db, body.email)
        if not user or user.get("disabled") or not user.get("password_hash"):
            return {"ok": True, "sent": False}
        token = make_dispatch_reset_token(user["id"], user["password_hash"])
        logger.info(f"[dispatch reset] token issued for {user['email']}")
        return {"ok": True, "sent": True, "token_for_dev": token}

    @router.post("/dispatch/reset-password")
    async def dispatch_reset_password(body: ResetPasswordBody):
        user = await consume_dispatch_reset_token(db, body.token)
        if not user:
            raise HTTPException(400, "Reset link is invalid or expired")
        if not body.new_password or len(body.new_password) < 8:
            raise HTTPException(400, "New password must be at least 8 characters")
        updated = await set_dispatch_user_password(db, user["id"], body.new_password, must_change=False)
        if not updated:
            raise HTTPException(404, "user not found")
        new_token = make_dispatch_user_token(updated["id"], updated["password_hash"])
        try:
            from session_timeout import reset_session_activity  # noqa: PLC0415
            await reset_session_activity(
                db, new_token, "OPERATIONS",
                user_id=updated.get("id"),
                email=updated.get("email"),
                actor_label="dispatch",
            )
        except Exception:  # noqa: BLE001
            pass
        return {"ok": True, "token": new_token, "user": public_dispatch_user_view(updated)}

    # ═══ Admin user management ═══
    @router.get("/admin/dispatch-users", dependencies=[Depends(require_admin)])
    async def admin_list_dispatch_users():
        users = await list_dispatch_users(db)
        return [public_dispatch_user_view(u) for u in users]

    @router.post("/admin/dispatch-users", dependencies=[Depends(require_admin)])
    async def admin_create_dispatch_user(body: DispatchUserCreate):
        try:
            user = await add_dispatch_user(db, body.dict())
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        temp_pw = generate_temp_password()
        await set_dispatch_user_password(db, user["id"], temp_pw, must_change=True)
        return {"user": public_dispatch_user_view(user), "temp_password": temp_pw}

    @router.patch("/admin/dispatch-users/{user_id}", dependencies=[Depends(require_admin)])
    async def admin_update_dispatch_user(user_id: str, body: DispatchUserUpdate):
        try:
            updated = await update_dispatch_user(db, user_id, body.dict(exclude_none=True))
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        if not updated:
            raise HTTPException(404, "Not found")
        return public_dispatch_user_view(updated)

    @router.post("/admin/dispatch-users/{user_id}/reset-password", dependencies=[Depends(require_admin)])
    async def admin_reset_dispatch_password(user_id: str, request: Request):
        temp_pw = generate_temp_password()
        updated = await set_dispatch_user_password(db, user_id, temp_pw, must_change=True)
        if not updated:
            raise HTTPException(404, "Not found")
        # iter502 · OMEGA IAM Enterprise Phase B+C
        try:
            from lib.iam_password_audit import stamp_and_audit_temp_password
            await stamp_and_audit_temp_password(
                db,
                collection_name="dispatch_users",
                user_filter={"id": user_id},
                target_email=str(updated.get("email") or ""),
                portal="dispatch",
                delivery="screen",
                request=request,
            )
        except Exception:
            pass
        return {"user": public_dispatch_user_view(updated), "temp_password": temp_pw}

    @router.post("/admin/dispatch-users/{user_id}/impersonate", dependencies=[Depends(require_admin)])
    async def admin_impersonate_dispatch_user(user_id: str):
        """Mint a short-lived dispatch token for the admin to preview
        the portal as this dispatcher. Audit-logged.
        """
        u = await db.dispatch_users.find_one({"id": user_id}, {"_id": 0})
        if not u:
            raise HTTPException(404, "Not found")
        if u.get("disabled"):
            raise HTTPException(409, "User is disabled — enable before impersonating")
        if not u.get("password_hash"):
            # Without a password_hash we can't make a token. Bootstrap
            # one with a random unrecoverable secret so the impersonation
            # token still works, but mark must_change so the next real
            # login forces a password set.
            from secrets import token_urlsafe  # noqa: PLC0415
            await set_dispatch_user_password(db, user_id, token_urlsafe(24), must_change=True)
            u = await db.dispatch_users.find_one({"id": user_id}, {"_id": 0})
        token = make_dispatch_user_token(u["id"], u["password_hash"])
        # audit event
        try:
            await db.audit_events.insert_one({
                "kind": "admin_impersonate_dispatch",
                "user_id": user_id,
                "user_email": u.get("email"),
                "at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            })
        except Exception:
            pass
        return {"token": token, "user": public_dispatch_user_view(u)}

    @router.delete("/admin/dispatch-users/{user_id}", dependencies=[Depends(require_admin)])
    async def admin_delete_dispatch_user(user_id: str):
        ok = await delete_dispatch_user(db, user_id)
        if not ok:
            raise HTTPException(404, "Not found")
        return {"ok": True}

    # ═══ iter353b · Read-only Driver Qualification visibility ═══
    # Dispatch is read-only on this surface. Same shared helper as HR
    # + Field Leadership. No write peer exists — no PATCH, no POST,
    # no DELETE, no import. Bounded operational visibility for
    # assignment / route prep.
    from fastapi import Query as _Query  # noqa: PLC0415
    from lib.driver_qualification import fetch_driver_qualification_dashboard  # noqa: PLC0415

    @router.get("/dispatch/driver-qualification")
    async def dispatch_driver_qualification(
        actor: dict = Depends(require_dispatch_or_admin),
        cdl_holder: Optional[bool] = _Query(default=None),
        approved: Optional[bool] = _Query(default=None),
        driver_status: Optional[str] = _Query(default=None),
        endorsement: Optional[str] = _Query(default=None),
        expiring_cdl_30d: Optional[bool] = _Query(default=None),
        expiring_medical_30d: Optional[bool] = _Query(default=None),
        available_now: Optional[bool] = _Query(default=None),
        q: Optional[str] = _Query(default=None, max_length=80),
        limit: int = _Query(default=500, ge=1, le=2000),
    ):
        try:
            payload = await fetch_driver_qualification_dashboard(
                db,
                cdl_holder=cdl_holder, approved=approved,
                driver_status=driver_status, endorsement=endorsement,
                expiring_cdl_30d=expiring_cdl_30d,
                expiring_medical_30d=expiring_medical_30d,
                available_now=available_now,
                q=q, limit=limit,
            )
        except ValueError as e:
            raise HTTPException(400, str(e))
        return {"ok": True, **payload, "viewer_role": "dispatch"}

    # ═══════════════════════════════════════════════════════════════════
    # Phase 5 · W3 closeout — Dispatch read-only daily-report visibility
    # ───────────────────────────────────────────────────────────────────
    # Dispatch needs to see equipment/crew movement fields from daily
    # reports for logistics planning. Strictly read-only · projection
    # omits incident narratives, labor cost, and safety details (none
    # of Dispatch's domain). No POST/PATCH/DELETE peer.
    # ═══════════════════════════════════════════════════════════════════
    @router.get("/dispatch/daily-reports")
    async def dispatch_daily_reports(
        _: dict = Depends(require_dispatch_or_admin),
        limit: int = _Query(default=100, ge=1, le=500),
    ):
        """Phase 5 · W3 · Dispatch read-only daily-report visibility.
        Returns the most recent daily reports projected to logistics
        fields only (equipment · crew counts · subcontractors · weather)."""
        pipeline = [
            {"$match": apply_synthetic_dr_exclusion({})},
            {"$sort": {"report_date": -1, "created_at": -1}},
            {"$limit": limit},
            {"$project": {
                "_id": 0, "id": 1, "project_name": 1, "project_number": 1,
                "location": 1, "report_date": 1, "prepared_by": 1,
                "superintendent": 1, "weather_summary": 1,
                "schedule_delays": 1, "schedule_delays_notes": 1,
                "weather_impact": 1, "weather_impact_notes": 1,
                "equipment": 1, "materials": 1,
                "created_at": 1,
                "crew_count":     {"$size": {"$ifNull": ["$masci_crews", []]}},
                "sub_count":      {"$size": {"$ifNull": ["$subcontractors", []]}},
                "visitor_count":  {"$size": {"$ifNull": ["$visitors", []]}},
                "equipment_count":{"$size": {"$ifNull": ["$equipment", []]}},
            }},
        ]
        items = await db.daily_reports.aggregate(pipeline).to_list(limit)
        return {
            "ok": True,
            "items": items,
            "count": len(items),
            "viewer_role": "dispatch",
        }

    return router


__all__ = [
    "build_dispatch_router",
    "make_require_dispatch_token",
    "make_require_dispatch_or_admin",
]

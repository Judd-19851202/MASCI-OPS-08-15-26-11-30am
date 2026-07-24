"""
routes/pm_routes.py · Phase 4D · PM Portal routes.

iter377 (read-only routes) + iter378 (auth lifecycle routes).

Scope:
  Read-only (iter377):
    • /pm/check, /pm/me
    • /pm/crew/training-records · /pm/crew/ppe · /pm/crew/capas · /pm/crew/summary
  Auth lifecycle (iter378):
    • /pm/login (per-PM bcrypt + legacy shared-password + universal super-admin fallback)
    • /pm/forgot-password (Resend email + 30-min HMAC token)
    • /pm/reset-password (consume token → set new pw → fresh per-PM token)
    • /pm/change-password (PM self-service rotation)
    • /pm/logout (audit + session_activity clearance)

Behavior contract (locked by tests/test_iter377_* and tests/test_iter378_*):
  Identical request/response shape to the original handlers in server.py.
  No auth drift. No visibility drift. No route renaming.

  All iter378 routes have IP-lockout, directory-fallback, and
  session-activity coupling. These are passed in via the `login_deps`
  kwarg so the factory has access to server.py's module-level helpers
  WITHOUT introducing circular imports.
"""
from __future__ import annotations

import asyncio
import hmac
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from pm_auth import public_pm_view

logger = logging.getLogger(__name__)


# ─── Body models (mirrored from server.py for the extracted routes) ──

class PMLoginBody(BaseModel):
    email: Optional[str] = None
    password: str

    model_config = {"extra": "ignore"}  # tolerate the legacy `_t` cache buster


class PMChangePasswordBody(BaseModel):
    old_password: str
    new_password: str


class PMForgotPasswordBody(BaseModel):
    email: str


class PMResetPasswordBody(BaseModel):
    token: str
    new_password: str



async def _pm_crew_employee_names(
    db, actor: Any, days: int = 180,
) -> Optional[List[str]]:
    """Return the set of employee NAMES on PM's assigned projects'
    daily reports within the last `days`. For admin/legacy callers
    (actor is True), return None to signal "no scope restriction".

    IDENTICAL behavior to server.py:_pm_crew_employee_names (iter353e).
    """
    # Admin or legacy PM bypass → no scope restriction
    if actor is True or not isinstance(actor, dict):
        return None
    pm_email = (actor.get("email") or "").lower()
    if not pm_email:
        return []
    proj_names: List[str] = []
    async for p in db.projects.find(
        {"$or": [
            {"project_manager_email": {"$regex": f"^{re.escape(pm_email)}$", "$options": "i"}},
            {"project_managers": {"$regex": f"^{re.escape(pm_email)}$", "$options": "i"}},
        ]},
        {"_id": 0, "name": 1, "project_name": 1},
    ):
        proj_names.append(p.get("name") or p.get("project_name") or "")
    proj_names = [p for p in proj_names if p]
    if not proj_names:
        return []
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()[:10]
    names: set[str] = set()
    async for r in db.daily_reports.find(
        apply_synthetic_dr_exclusion({
            "project_name": {"$in": proj_names},
            "report_date": {"$gte": cutoff},
        }),
        {"_id": 0, "crew_members": 1, "employees": 1, "personnel": 1},
    ).limit(2000):
        for fld in ("crew_members", "employees", "personnel"):
            v = r.get(fld) or []
            if isinstance(v, list):
                for entry in v:
                    if isinstance(entry, str):
                        names.add(entry.strip())
                    elif isinstance(entry, dict):
                        nm = (entry.get("name") or entry.get("employee_name") or "").strip()
                        if nm:
                            names.add(nm)
    return sorted(names)


def build_pm_router(
    db,
    require_admin_dep: Callable,
    require_admin_async_dep: Callable,
    login_deps: Optional[Dict[str, Any]] = None,
) -> APIRouter:
    """Build the PM portal router.

    Args:
      db: motor database handle.
      require_admin_dep: server.py `require_admin` dependency.
      require_admin_async_dep: server.py `require_admin_async` dependency.
      login_deps: iter378 · helpers for the auth-lifecycle routes.
        Must contain (if any of the auth routes are needed):
          client_ip_fn, check_login_lockout_fn,
          record_login_fail_fn, reset_login_fails_fn,
          directory_admin_token_fn, reset_session_activity_fn,
          clear_session_activity_fn,
          render_portal_email_fn.
        If None, the auth-lifecycle routes are NOT mounted (use this
        for tests that only need the read-only surface).
    """
    router = APIRouter(prefix="/api", tags=["pm"])

    @router.get("/pm/check")
    async def pm_check(_: bool = Depends(require_admin_dep)):
        """Verify a stored PM (or Admin) token is still valid."""
        return {"ok": True}

    @router.get("/pm/crew/training-records")
    async def pm_crew_training_records(
        actor=Depends(require_admin_async_dep),
        limit: int = Query(default=200, ge=1, le=500),
    ):
        """iter353e · PM scoped training records for crew on PM's projects."""
        names = await _pm_crew_employee_names(db, actor)
        q: Dict[str, Any] = {}
        if names is not None:
            if not names:
                return {"ok": True, "items": [], "count": 0,
                        "scope": "pm_crew_180d", "crew_size": 0}
            q = {"$or": [{"employee_name": {"$in": names}},
                         {"employee_email": {"$in": names}}]}
        items = []
        async for r in db.safety_training_records.find(
            q,
            {"_id": 0, "id": 1, "employee_id": 1, "employee_name": 1,
             "training_name": 1, "certification_type": 1,
             "completed_date": 1, "expiration_date": 1, "notes": 1,
             "created_by_role": 1},
        ).sort("completed_date", -1).limit(limit):
            items.append(r)
        return {"ok": True, "items": items, "count": len(items),
                "scope": "pm_crew_180d" if names is not None else "admin_all",
                "crew_size": len(names) if names is not None else None}

    @router.get("/pm/crew/ppe")
    async def pm_crew_ppe(
        actor=Depends(require_admin_async_dep),
        limit: int = Query(default=200, ge=1, le=500),
    ):
        """iter353e · PM scoped PPE issuance records for crew."""
        names = await _pm_crew_employee_names(db, actor)
        q: Dict[str, Any] = {}
        if names is not None:
            if not names:
                return {"ok": True, "items": [], "count": 0,
                        "scope": "pm_crew_180d", "crew_size": 0}
            q = {"employee_name": {"$in": names}}
        items = []
        async for r in db.safety_equipment_issuances.find(
            q,
            {"_id": 0, "id": 1, "employee_name": 1, "equipment_type": 1,
             "issued_date": 1, "size": 1, "condition": 1},
        ).sort("issued_date", -1).limit(limit):
            items.append(r)
        return {"ok": True, "items": items, "count": len(items),
                "scope": "pm_crew_180d" if names is not None else "admin_all",
                "crew_size": len(names) if names is not None else None}

    @router.get("/pm/crew/capas")
    async def pm_crew_capas(
        actor=Depends(require_admin_async_dep),
        limit: int = Query(default=200, ge=1, le=500),
    ):
        """iter353e · PM scoped CAPA visibility for incidents involving
        crew. Read-only — PM does NOT have CAPA closeout authority."""
        names = await _pm_crew_employee_names(db, actor)
        q: Dict[str, Any] = {}
        if names is not None:
            if not names:
                return {"ok": True, "items": [], "count": 0,
                        "scope": "pm_crew_180d", "crew_size": 0}
            q = {"$or": [{"linked_employee_name": {"$in": names}},
                         {"employee_name": {"$in": names}}]}
        items = []
        async for r in db.corrective_actions.find(
            q,
            {"_id": 0},
        ).sort("created_at", -1).limit(limit):
            items.append(r)
        return {"ok": True, "items": items, "count": len(items),
                "scope": "pm_crew_180d" if names is not None else "admin_all",
                "crew_size": len(names) if names is not None else None}

    @router.get("/pm/crew/summary")
    async def pm_crew_summary(actor=Depends(require_admin_async_dep)):
        """iter353e · PM crew compliance roll-up: crew size, expiring
        training in 30d, expired training, PPE missing, open CAPAs."""
        names = await _pm_crew_employee_names(db, actor)
        if names is None:
            return {"ok": True, "scope": "admin_all", "crew_size": None,
                    "expiring_30d": 0, "expired": 0, "open_capas": 0,
                    "ppe_records": 0}
        today = datetime.now(timezone.utc).isoformat()[:10]
        cutoff_30d = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()[:10]
        if not names:
            return {"ok": True, "scope": "pm_crew_180d", "crew_size": 0,
                    "expiring_30d": 0, "expired": 0, "open_capas": 0,
                    "ppe_records": 0}
        expiring = await db.safety_training_records.count_documents({
            "$or": [{"employee_name": {"$in": names}}],
            "expiration_date": {"$gte": today, "$lte": cutoff_30d},
        })
        expired = await db.safety_training_records.count_documents({
            "$or": [{"employee_name": {"$in": names}}],
            "expiration_date": {"$gt": "", "$lt": today},
        })
        open_capas = await db.corrective_actions.count_documents({
            "$or": [{"linked_employee_name": {"$in": names}},
                    {"employee_name": {"$in": names}}],
            "status": {"$nin": ["closed", "completed", "verified"]},
        })
        ppe_records = await db.safety_equipment_issuances.count_documents({
            "employee_name": {"$in": names},
        })
        return {"ok": True, "scope": "pm_crew_180d", "crew_size": len(names),
                "expiring_30d": expiring, "expired": expired,
                "open_capas": open_capas, "ppe_records": ppe_records}

    @router.get("/pm/me")
    async def pm_me(actor=Depends(require_admin_async_dep)):
        """Return the currently signed-in PM's record (sans password_hash).
        Returns ``{is_admin: true, pm: null}`` when an Admin token is being
        used or when the legacy shared-PM bypass is active."""
        if actor is True:
            return {"is_admin_or_legacy": True, "pm": None}
        return {"is_admin_or_legacy": False, "pm": public_pm_view(actor)}

    # ════════════════════════════════════════════════════════════════
    # iter437 P0 follow-up · 2026-02 · PmJobsRead
    # ════════════════════════════════════════════════════════════════
    # Calm read-only PM jobs surface. Mirrors the data-scoping rules of
    # /api/admin/jobs (PMs see only jobs they're primary or co-PM on;
    # admin tokens see all). Lives under /api/pm/* so the iter180
    # /api/admin/* boundary is preserved — PM tokens are valid here.
    #
    # Frontend mounts this at /pm/jobs (PmJobsRead view) instead of the
    # old AdminJobMasterPanel, which was admin-only and triggered the
    # "Admin login required" regression documented in
    # /app/memory/PORTAL_AUTH_TOKEN_AUDIT.md.
    @router.get("/pm/jobs")
    async def pm_list_jobs(
        actor=Depends(require_admin_async_dep),
        include_inactive: bool = Query(default=False),
    ):
        """Return jobs visible to the caller.

        Behaviour:
          • Admin / legacy-shared-PM: every job (active by default;
            inactive included when `include_inactive=true`).
          • Per-PM token: only jobs where the PM is primary or co-PM
            (matches `compute_pm_scope`).
        Read-only. No write surface. No `/api/admin/*` dependency."""
        from jobs_master import list_jobs
        from pm_auth import compute_pm_scope
        items = await list_jobs(db, only_active=not include_inactive)
        scope = await compute_pm_scope(db, actor)
        if not scope.is_admin:
            nums = scope.project_numbers or set()
            items = [j for j in items if (j.get("project_number") or "") in nums]
        for item in items:
            item["cost_code_progress_percent"] = item.get("cost_code_progress_percent") or 0
            item["schedule_cost_spine_ready"] = bool(item.get("schedule_cost_spine_ready"))
        return {
            "ok": True,
            "items": items,
            "count": len(items),
            "scope": "admin_all" if scope.is_admin else "pm_assigned",
        }

    # ════════════════════════════════════════════════════════════════
    # iter378 · Auth-lifecycle routes (login / forgot / reset /
    # change-password / logout). Mounted only when `login_deps` is
    # provided — keeps tests and headless invocations safe.
    # ════════════════════════════════════════════════════════════════
    if login_deps is None:
        return router

    _client_ip = login_deps["client_ip_fn"]
    _check_login_lockout = login_deps["check_login_lockout_fn"]
    _record_login_fail = login_deps["record_login_fail_fn"]
    _reset_login_fails = login_deps["reset_login_fails_fn"]
    _directory_admin_token = login_deps["directory_admin_token_fn"]
    _reset_session_activity = login_deps["reset_session_activity_fn"]
    _clear_session_activity = login_deps["clear_session_activity_fn"]
    _canonical_multi_logout = login_deps.get("canonical_multi_logout_fn")
    # Track 15.87 · directory PM-grant minter. Optional — falls back
    # to None which disables the new directory PM path (legacy
    # behaviour). Provided by server.py wiring.
    _directory_pm_minter = login_deps.get("directory_pm_minter_fn")
    # TRACK 15.32 — shared PM HMAC retired; the per-PM auth path uses
    # `pm_auth.make_pm_token` directly (see pm_login below).
    # TRACK 15.34 — the deprecated `pm_token_for_fn` login_deps key was
    # removed entirely.
    _render_portal_email = login_deps["render_portal_email_fn"]

    @router.post("/pm/login")
    async def pm_login(body: PMLoginBody, request: Request):
        """Project-Manager portal login.

        NEW per-PM flow: PM enters their work email + password. We look up
        the matching PM in ``project_managers``, verify the bcrypt hash, and
        issue a per-PM token. The token expires when the admin resets the
        PM's password (the hash changes → token mismatch).

        LEGACY shared-password flow (env-flag bypass): if email is empty or
        a sentinel "office-bypass@" string AND ``PM_SHARED_LOGIN_ENABLED=true``,
        accept the legacy ``PM_PASSWORD`` so the office can still log in if a
        per-PM account is broken. Returns the legacy token format (no dot)."""
        from pm_auth import (
            find_pm_by_email,
            make_pm_token,
            shared_pm_login_enabled,
            stamp_login,
            verify_password,
        )

        ip = _client_ip(request)
        _check_login_lockout(ip)
        email = (body.email or "").strip().lower()
        password = body.password or ""

        # ---- Per-PM auth path ----
        if email:
            pm = await find_pm_by_email(db, email)

            # Track 15.87 · directory `pm` grant fallback.
            # Tried BEFORE the admin fallback so a directory user with
            # `pm` grant gets a PM token (not admin). Mirrors multi-
            # login behaviour; mints via the same minter.
            async def _try_directory_pm_fallback():
                try:
                    from lib.directory_portal_login import try_directory_portal_login  # noqa: PLC0415
                    res = await try_directory_portal_login(
                        db,
                        email=email,
                        password=password,
                        required_portal="pm",
                        portal_token_minter=_directory_pm_minter,
                        kind="pm",
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(f"pm_login track_15_87 directory-grant fallback error: {exc}")
                    return None
                if not res:
                    return None
                try:
                    await _reset_session_activity(
                        db, res["token"], "OPERATIONS",
                        user_id=res["user"].get("id"),
                        email=res["user"].get("email"),
                        actor_label="pm_via_directory", ip=ip,
                        user_agent=request.headers.get("user-agent") or "",
                    )
                except Exception:  # noqa: BLE001
                    pass
                _reset_login_fails(ip)
                # PM legacy response uses `pm` (not `user`) — keep
                # envelope identical to the native path.
                return {
                    "ok": True,
                    "token": res["token"],
                    "kind": "pm",
                    "must_change_password": False,
                    "pm": res["user"],
                }

            # Super Admin fallback only.
            async def _try_directory_admin_fallback():
                try:
                    import user_directory as _ud_local  # noqa: PLC0415
                    row = await _ud_local.authenticate(db, email=email, password=password)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(f"pm_login directory fallback error: {exc}")
                    return None
                if row and not row.get("disabled") and row.get("is_super_admin") is True:
                    admin_tok = _directory_admin_token(row)
                    if admin_tok:
                        await _reset_session_activity(
                            db, admin_tok, "OPERATIONS",
                            user_id=row.get("id"), email=row.get("email"),
                            actor_label="admin_via_pm", ip=ip,
                            user_agent=request.headers.get("user-agent") or "",
                        )
                        _reset_login_fails(ip)
                        return {
                            "ok": True,
                            "token": admin_tok,
                            "kind": "admin",
                            "must_change_password": False,
                            "pm": _ud_local.public_view(row),
                        }
                return None

            if not pm:
                # Try directory PM grant first (Track 15.87), then
                # admin fallback (iter346-B).
                fb = await _try_directory_pm_fallback()
                if fb is not None:
                    return fb
                fb = await _try_directory_admin_fallback()
                if fb is not None:
                    return fb
                _record_login_fail(ip)
                raise HTTPException(status_code=401, detail="Wrong email or password")
            if pm.get("disabled"):
                raise HTTPException(
                    status_code=403,
                    detail="This PM account is disabled. Contact the admin.",
                )
            pwh = pm.get("password_hash") or ""
            if not pwh:
                raise HTTPException(
                    status_code=403,
                    detail="No password set for this PM yet. Ask the admin to issue one.",
                )
            if not verify_password(password, pwh):
                # Try directory PM grant first (Track 15.87), then
                # admin fallback.
                fb = await _try_directory_pm_fallback()
                if fb is not None:
                    return fb
                fb = await _try_directory_admin_fallback()
                if fb is not None:
                    return fb
                _record_login_fail(ip)
                raise HTTPException(status_code=401, detail="Wrong email or password")
            _reset_login_fails(ip)
            await stamp_login(db, pm["id"], ip=ip)
            token = make_pm_token(pm["id"], pwh)
            await _reset_session_activity(
                db, token, "OPERATIONS",
                user_id=pm.get("id"),
                email=pm.get("email"),
                actor_label="pm",
                ip=ip,
                user_agent=request.headers.get("user-agent") or "",
            )
            return {
                "ok": True,
                "token": token,
                "kind": "pm",
                "must_change_password": bool(pm.get("must_change_password")),
                "pm": public_pm_view(pm),
            }

        # TRACK 15.32 (2026-02) — shared PM_PASSWORD HMAC retired.
        # The email-less legacy emergency-bypass branch and its
        # `pm-shared` token producer were removed. Reaching this point
        # means no `email` was supplied AND no per-PM user was matched
        # — return a clear retirement-aware 401 so legacy automation
        # gets an actionable message instead of a silent failure.
        raise HTTPException(
            status_code=401,
            detail=(
                "Email is required. The shared PM password path was "
                "retired in TRACK 15.32 — sign in with your assigned "
                "PM user account email + password."
            ),
        )

    @router.post("/pm/forgot-password")
    async def pm_forgot_password(body: PMForgotPasswordBody, request: Request):
        """Self-service password reset — step 1.

        PM enters email → backend mints 30-min HMAC token bound to their
        password_hash prefix → emails them /pm/reset/<token>. Always
        returns generic success to prevent email enumeration. Per-IP
        lockout still applies.
        """
        from pm_auth import find_pm_by_email, make_reset_token

        ip = _client_ip(request)
        _check_login_lockout(ip)
        email = (body.email or "").strip().lower()

        generic = {
            "ok": True,
            "message": (
                "If that email is on file with a password, a reset link is on "
                "its way. Check your inbox in the next minute."
            ),
        }

        if not email or "@" not in email:
            _record_login_fail(ip)
            return generic

        pm = await find_pm_by_email(db, email)
        if not pm:
            _record_login_fail(ip)
            return generic
        pwh = pm.get("password_hash") or ""
        if not pwh:
            return generic
        if pm.get("disabled"):
            return generic

        api_key = (os.environ.get("RESEND_API_KEY") or "").strip()
        if not api_key:
            logger.warning("[forgot-password] RESEND_API_KEY missing; cannot send")
            return generic

        portal_url = (
            os.environ.get("PORTAL_URL", "").strip()
            or os.environ.get("PRODUCTION_URL", "").strip()
            or "https://mascidocs.com"
        )
        token = make_reset_token(pm["id"], pwh)
        reset_link = f"{portal_url}/pm/reset/{token}"
        pm_name = (pm.get("name") or "").strip() or "Project Manager"
        body_inner = f"""
          <p style="margin:0 0 14px;font-size:15px;line-height:1.5">Hi {pm_name},</p>
          <p style="margin:0 0 14px;font-size:14px;line-height:1.55;color:#334155">
            Someone (hopefully you) requested a password reset for the MASCI PM Portal account
            <strong>{email}</strong>. Click the button below to choose a new password.
          </p>

          <table cellpadding="0" cellspacing="0" style="margin:18px 0">
            <tr><td style="background:#b91c1c;border-radius:6px;padding:14px 28px">
              <a href="{reset_link}" style="color:#fff;font-weight:800;font-size:14px;letter-spacing:0.05em;text-transform:uppercase;text-decoration:none">
                Choose a new password
              </a>
            </td></tr>
          </table>

          <p style="margin:14px 0 0;font-size:13px;color:#64748b;line-height:1.55">
            This link expires in 30 minutes. If you didn't request a reset, ignore this email — your current password keeps working.
          </p>
          <p style="margin:8px 0 0;font-size:12px;color:#94a3b8;line-height:1.55">
            Direct link: <span style="font-family:Courier New,monospace;font-size:10px;word-break:break-all;color:#475569">{reset_link}</span>
          </p>
        """
        html_body = _render_portal_email(
            portal="PM",
            headline="Reset your password",
            body_inner_html=body_inner,
        )

        try:
            import resend
            resend.api_key = api_key
            from branding_resolver import (
                resolve_sender_email as _resolve_sender_email,
                resolve_reply_to_email as _resolve_reply_to_email,
            )
            sender_email = await _resolve_sender_email(db)
            params = {
                "from": f"MASCI Operations Platform <{sender_email}>",
                "to": [email],
                "subject": "[MASCI] Reset your Project Management password",
                "html": html_body,
            }
            reply_to = (await _resolve_reply_to_email(db)) or ""
            if reply_to:
                params["reply_to"] = reply_to
            await asyncio.to_thread(resend.Emails.send, params)
        except Exception as e:  # noqa: BLE001
            logger.error("[forgot-password] resend send failed: %s", e)

        return generic

    @router.post("/pm/reset-password")
    async def pm_reset_password(body: PMResetPasswordBody, request: Request):
        """Self-service password reset — step 2.

        PM clicks email link → enters new password → backend validates
        token, sets new bcrypt hash, returns fresh per-PM token."""
        from pm_auth import (
            consume_reset_token,
            make_pm_token,
            set_pm_password,
            stamp_login,
        )

        ip = _client_ip(request)
        _check_login_lockout(ip)

        if len(body.new_password or "") < 6:
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

        pm = await consume_reset_token(db, body.token)
        if not pm:
            _record_login_fail(ip)
            raise HTTPException(
                status_code=400,
                detail="This reset link is invalid or has expired. Request a new one from /pm/login.",
            )

        updated = await set_pm_password(db, pm["id"], body.new_password, must_change=False)
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update password")
        _reset_login_fails(ip)
        await stamp_login(db, updated["id"], ip=ip)
        await _reset_session_activity(
            db, make_pm_token(updated["id"], updated["password_hash"]), "OPERATIONS",
            user_id=updated.get("id"), email=updated.get("email"),
            actor_label="pm", ip=ip, user_agent=request.headers.get("user-agent") or "",
        )
        return {
            "ok": True,
            "token": make_pm_token(updated["id"], updated["password_hash"]),
            "pm": public_pm_view(updated),
        }

    @router.post("/pm/change-password")
    async def pm_change_password(
        body: PMChangePasswordBody, actor=Depends(require_admin_async_dep)
    ):
        """PM rotates their own password. Required after admin issues a
        temp password. Returns a fresh per-PM token (the old one is
        invalidated because it embeds the previous hash prefix)."""
        from pm_auth import (
            make_pm_token,
            set_pm_password,
            verify_password,
        )

        if actor is True:
            raise HTTPException(
                status_code=403,
                detail="Only a per-PM session can rotate a PM password.",
            )
        pm = actor
        pwh = pm.get("password_hash") or ""
        if not verify_password(body.old_password, pwh):
            raise HTTPException(status_code=401, detail="Old password is wrong")
        if len(body.new_password) < 6:
            raise HTTPException(
                status_code=400, detail="New password must be at least 6 characters"
            )
        if body.new_password == body.old_password:
            raise HTTPException(
                status_code=400, detail="New password must be different from the old one"
            )
        if pm.get("linked_to_directory") or pm.get("source") == "directory-shadow":
            try:
                import user_directory as _ud_local  # noqa: PLC0415
                ok = await _ud_local.self_change_password(
                    db,
                    user_id=pm["id"],
                    current_password=body.old_password,
                    new_password=body.new_password,
                )
            except ValueError as ve:
                raise HTTPException(status_code=400, detail=str(ve))
            if not ok:
                raise HTTPException(status_code=401, detail="Old password is wrong")
            fresh_row = await _ud_local.find_by_id(db, pm["id"])
            if not fresh_row or not fresh_row.get("password_hash"):
                raise HTTPException(status_code=404, detail="user not found")
            await db.project_managers.update_one(
                {"id": pm["id"]},
                {"$set": {
                    "password_hash": fresh_row["password_hash"],
                    "must_change_password": False,
                    "password_set_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }},
            )
            updated = await db.project_managers.find_one({"id": pm["id"]}, {"_id": 0})
            if not updated:
                raise HTTPException(status_code=500, detail="Failed to update password")
            fresh_token = make_pm_token(fresh_row["id"], fresh_row["password_hash"])
            await _reset_session_activity(
                db, fresh_token, "OPERATIONS",
                user_id=fresh_row.get("id"), email=fresh_row.get("email"),
                actor_label="pm_via_directory",
            )
            return {
                "ok": True,
                "token": fresh_token,
                "pm": public_pm_view(updated),
            }
        updated = await set_pm_password(db, pm["id"], body.new_password, must_change=False)
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update password")
        await _reset_session_activity(
            db, make_pm_token(updated["id"], updated["password_hash"]), "OPERATIONS",
            user_id=updated.get("id"), email=updated.get("email"),
            actor_label="pm",
        )
        return {
            "ok": True,
            "token": make_pm_token(updated["id"], updated["password_hash"]),
            "pm": public_pm_view(updated),
        }

    @router.post("/pm/logout")
    async def pm_logout(request: Request, actor=Depends(require_admin_async_dep)):
        """Legacy compatibility wrapper over canonical shared logout."""
        try:
            pm_id = (actor.get("id") if isinstance(actor, dict) else "") or ""
            await db.audit_events.insert_one({
                "at": datetime.now(timezone.utc),
                "kind": "pm_logout",
                "actor": "pm",
                "pm_id": pm_id,
                "ip": _client_ip(request),
                "user_agent": (request.headers.get("user-agent") or "")[:240],
                "logout_route": "/api/pm/logout",
                "canonical_logout": "/api/auth/multi-logout",
            })
        except Exception:  # noqa: BLE001
            pass
        if callable(_canonical_multi_logout):
            return await _canonical_multi_logout(
                x_directory_token=request.headers.get("x-directory-token") or None,
                x_admin_token=request.headers.get("x-admin-token") or None,
                x_pm_token=request.headers.get("x-pm-token") or None,
                x_hr_token=request.headers.get("x-hr-token") or None,
                x_safety_token=request.headers.get("x-safety-token") or None,
                x_shop_token=request.headers.get("x-shop-token") or None,
                x_dispatch_token=request.headers.get("x-dispatch-token") or None,
                x_fl_token=request.headers.get("x-fl-token") or None,
            )
        x_pm_token = request.headers.get("x-pm-token") or ""
        await _clear_session_activity(db, x_pm_token)
        return {"ok": True, "canonical_logout": None}

    return router


__all__ = ["build_pm_router"]

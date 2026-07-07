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
from lib.directory_access_state import derive_directory_access_state
from lib.rate_limiting import (
    _check_login_lockout,
    _record_login_fail,
    _reset_login_fails,
)

logger = logging.getLogger(__name__)


def _enrich_with_access_state(view: Optional[Dict[str, Any]], raw_row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Track 15.88 · Merge the canonical access-state envelope into
    the admin-facing public view. Reads ``password_hash`` from the
    raw row to compute ``has_credentials`` but NEVER exposes the hash
    in the returned view."""
    if view is None or raw_row is None:
        return view
    view.update(derive_directory_access_state(raw_row))
    return view


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
    password: str = ""  # empty → backend generates if delivery=email
    must_change_password: bool = False
    delivery: str = "email"  # "email" (welcome email) | "show" (admin sees + copies)


class UpdateDirectoryUserBody(BaseModel):
    name: Optional[str] = None
    portals: Optional[List[str]] = None
    disabled: Optional[bool] = None


class AdminResetPasswordBody(BaseModel):
    new_password: str = ""  # empty → backend generates if delivery=email
    must_change: bool = True
    delivery: str = "email"  # "email" | "show"


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
    safety_token_minter: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None,
    dispatch_token_minter: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None,
    admin_token_minter: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None,
    field_leadership_token_minter: Optional[Callable[[Dict[str, Any]], Optional[str]]] = None,
    send_email_fn: Optional[Callable] = None,
    render_portal_email_fn: Optional[Callable] = None,
) -> APIRouter:
    router = APIRouter(tags=["auth-directory"])

    # ────────────────────────────────────────────────────────────────
    # Welcome / reset-password email — iter90
    # Mirrors the PM/HR/Shop welcome-email pattern (work email + signed-in
    # URL + temp password block + sign-in button). Uses the shared
    # branded_portal_emails wrapper so chrome matches every other portal.
    # ────────────────────────────────────────────────────────────────
    import os
    import secrets
    import string

    def _generate_temp_password(n: int = 12) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(n)) + "!"

    async def _send_directory_welcome(
        user_email: str,
        name: str,
        temp_password: str,
        portals: List[str],
        is_reset: bool,
    ) -> bool:
        """Returns True if email was sent, False if email channel not
        available (caller must fall back to 'show password to admin')."""
        if not send_email_fn or not render_portal_email_fn:
            logger.info(f"[directory welcome] email channel unavailable; password for {user_email} = {temp_password}")
            return False
        base = os.environ.get("PUBLIC_APP_URL", "https://mascidocs.com").rstrip("/")
        # Multi-portal users sign in at /sign-in; single-portal users get
        # the appropriate per-portal login URL.
        if len(portals) == 1:
            single_portal = portals[0]
            login_url = f"{base}/{single_portal}/login"
            portal_label = single_portal.upper()
            access_text = f"the <strong>{portal_label} Portal</strong>"
        else:
            login_url = f"{base}/sign-in"
            portal_label = ", ".join(p.upper() for p in sorted(portals))
            access_text = f"the following portals: <strong>{portal_label}</strong>"
        display_name = name or user_email.split("@")[0]
        intro_para = (
            f"<p style='margin:0 0 12px'>Hi {display_name},</p>"
            f"<p style='margin:0 0 12px'>"
            f"{'Your MASCI master password has been reset' if is_reset else 'Your MASCI access account has been created'}. "
            f"This account gives you access to {access_text}. "
            f"Sign in at the link below with your work email and the temporary password — "
            f"<strong>you'll be asked to choose your own password on first sign-in.</strong>"
            f"</p>"
        )
        body_html = (
            intro_para
            + "<table style='margin:14px 0;border-collapse:collapse;width:100%;'>"
            f"  <tr><td style='padding:6px 0;font-family:Courier New,monospace;text-transform:uppercase;letter-spacing:0.18em;font-size:10px;color:#475569;font-weight:bold;width:42%'>Sign-in URL</td>"
            f"      <td style='padding:6px 0;font-size:13px;'><a href='{login_url}' style='color:#b91c1c;font-weight:600'>{login_url}</a></td></tr>"
            f"  <tr><td style='padding:6px 0;font-family:Courier New,monospace;text-transform:uppercase;letter-spacing:0.18em;font-size:10px;color:#475569;font-weight:bold;'>Email</td>"
            f"      <td style='padding:6px 0;font-family:Courier New,monospace;font-size:13px;color:#0f172a'>{user_email}</td></tr>"
            f"  <tr><td style='padding:6px 0;font-family:Courier New,monospace;text-transform:uppercase;letter-spacing:0.18em;font-size:10px;color:#475569;font-weight:bold;'>Temporary password</td>"
            f"      <td style='padding:6px 0;font-family:Courier New,monospace;font-size:14px;color:#0f172a;background:#f8fafc;border:1px dashed #94a3b8;padding:6px 8px;border-radius:4px'><strong>{temp_password}</strong></td></tr>"
            f"</table>"
            f"<p style='margin:14px 0 6px'>"
            f"<a href='{login_url}' style='display:inline-block;padding:11px 22px;background:#b91c1c;color:#fff;text-decoration:none;font-weight:700;border-radius:4px;font-size:13px'>Sign in &amp; set password</a>"
            f"</p>"
            f"<p style='margin:18px 0 0;font-size:12px;color:#94a3b8'>For security, please change your password immediately after signing in.</p>"
        )
        try:
            html = render_portal_email_fn(
                portal="Operations" if len(portals) > 1 else portals[0].upper(),
                headline=(
                    "Your MASCI master password was reset"
                    if is_reset
                    else "Welcome to MASCI Operations"
                ),
                body_inner_html=body_html,
            )
            subject_action = "master password reset" if is_reset else "account created"
            await send_email_fn(
                user_email,
                f"[MASCI] Your access account — {subject_action} (temporary password inside)",
                html,
            )
            return True
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[directory welcome] email send failed for {user_email}: {e}")
            return False

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
        if "safety" in portals and safety_token_minter:
            try:
                tokens["safety"] = await _maybe_await(safety_token_minter(row))
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[multi-login] safety minter failed: {e}")
        if "dispatch" in portals and dispatch_token_minter:
            try:
                tokens["dispatch"] = await _maybe_await(dispatch_token_minter(row))
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[multi-login] dispatch minter failed: {e}")
        # iter345 · FL Phase B · Hybrid · directory-granted FL token
        if "field_leadership" in portals and field_leadership_token_minter:
            try:
                fl_tok = await _maybe_await(field_leadership_token_minter(row))
                tokens["field_leadership"] = fl_tok
                # OA-1 polish: alias under "fl" so it matches the X-FL-Token
                # header naming used by Operations Actions + other surfaces.
                tokens["fl"] = fl_tok
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[multi-login] field_leadership minter failed: {e}")
        return tokens

    @router.post("/api/auth/multi-login")
    async def multi_login(body: MultiLoginBody, request: Request):
        # Track 24.1 · P1-B — brute-force lockout at the master login
        # gate. Uses the platform-standard LOGIN_MAX_FAILS + lockout
        # window from `lib.rate_limiting`. Every per-portal login route
        # already calls these; multi-login was the only unguarded path.
        ip = _client_ip(request)
        _check_login_lockout(ip)
        row = await ud.authenticate(db, email=body.email, password=body.password)
        if not row:
            # Audit failures so brute-forcing surfaces in /admin
            _record_login_fail(ip)
            await ud.write_audit(
                db,
                actor_email=body.email,
                action="multi_login_failed",
                ip=ip,
                user_agent=request.headers.get("user-agent"),
            )
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        _reset_login_fails(ip)
        # iter375 · Phase 4B — TOTP MFA gate for super-admin directory users.
        # If MFA is enabled, do NOT mint portal tokens. Return a short-lived
        # challenge token; the frontend must POST /api/auth/mfa/verify-login
        # with a TOTP (or recovery) code to receive portal tokens.
        cfg = row.get("mfa") or {}
        if cfg.get("enabled"):
            try:
                import mfa as _mfa  # noqa: PLC0415
                challenge = _mfa.mint_challenge_token(row["id"])
                await _mfa.write_audit(
                    db, user_id=row["id"], user_email=row.get("email"),
                    event="LOGIN_MFA_CHALLENGE_ISSUED",
                    ip=_client_ip(request),
                    user_agent=request.headers.get("user-agent"),
                )
            except Exception as e:  # noqa: BLE001
                logger.error(f"[multi-login] failed to mint MFA challenge: {e}")
                raise HTTPException(status_code=500, detail="MFA challenge unavailable")
            return {
                "ok": True,
                "mfa_required": True,
                "mfa_challenge_token": challenge,
                "user": {"email": row.get("email"), "name": row.get("name")},
            }
        # Mint per-portal tokens + directory session token
        portal_tokens = await _mint_all(row)
        session_token = ud.make_directory_token()
        await ud.persist_session(db, token=session_token, user_id=row["id"])
        await ud.stamp_last_login(db, user_id=row["id"], portal="multi")

        # Track 15.14A · Layer 1 — TEMP-PASSWORD ENFORCEMENT.
        # If the directory user still owes a password rotation, do NOT
        # hand them any portal tokens. The SPA detects must_change_password
        # and forces them through /change-password. The session_token
        # remains valid so /api/auth/change-master-password can authenticate
        # the rotation itself. After rotation completes the user re-runs
        # multi-login and gets a full token bundle.
        if bool(row.get("must_change_password")):
            await ud.write_audit(
                db,
                actor_email=row["email"],
                action="multi_login_temp_pw_blocked",
                target_email=row["email"],
                diff={"reason": "must_change_password=true; portal_tokens suppressed"},
                ip=_client_ip(request),
                user_agent=request.headers.get("user-agent"),
            )
            return {
                "ok": True,
                "session_token": session_token,
                "portal_tokens": {},
                "user": ud.public_view(row),
                "must_change_password": True,
            }
        # Initiative 4 fix — reset session_activity for every minted
        # portal token. Each portal token is deterministic per
        # (user_id, pwh), so without this a stale row would expire the
        # session before the first authenticated request.
        # RC-1 M-19 fix (2026-02-11): parallelize the 6-7 reset writes
        # with asyncio.gather. Each reset is an independent Mongo upsert
        # on a different `_id`, so semantics are identical. This shaves
        # ~700-1000ms off multi-login (was the dominant serial hot spot).
        try:
            from session_timeout import reset_session_activity
            import asyncio  # noqa: PLC0415
            _portal_tier = {
                "admin": "ADMIN_HR", "hr": "ADMIN_HR",
                "pm": "OPERATIONS", "shop": "OPERATIONS",
                "safety": "OPERATIONS", "dispatch": "OPERATIONS",
                "field_leadership": "ADMIN_FL",
            }
            _ua = request.headers.get("user-agent") or ""
            _ip = _client_ip(request)
            _reset_tasks = [
                reset_session_activity(
                    db, _tok, _portal_tier.get(_portal, "OPERATIONS"),
                    user_id=row.get("id"),
                    email=row.get("email"),
                    actor_label=_portal,
                    ip=_ip,
                    user_agent=_ua,
                )
                for _portal, _tok in (portal_tokens or {}).items()
                if _tok
            ]
            if _reset_tasks:
                await asyncio.gather(*_reset_tasks, return_exceptions=True)
        except Exception:  # noqa: BLE001
            pass
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
        request: Request = None,
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
            "safety": safety_token_minter,
            "dispatch": dispatch_token_minter,
            # TRACK 14.0-SSO (2026-02-15): register field_leadership so
            # the on-demand mint path used by the frontend RequireFl
            # guard (via usePortalHydration) actually works. Previously
            # this returned 500 'field_leadership token minter not
            # configured', breaking direct-URL navigation to FL routes
            # for users who lost their fl token. The minter is already
            # accepted as a kwarg on the router factory and used by
            # multi-login — registering it here closes the asymmetry.
            "field_leadership": field_leadership_token_minter,
        }.get(target)
        if not minter:
            raise HTTPException(status_code=500, detail=f"{target} token minter not configured.")
        try:
            tok = await _maybe_await(minter(row))
        except Exception as e:  # noqa: BLE001
            logger.exception(f"[multi-login] portal-token mint failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to mint token.")
        # Initiative 4 fix — reset session_activity for the freshly
        # re-minted portal token.
        try:
            from session_timeout import reset_session_activity
            _tier = {
                "admin": "ADMIN_HR", "hr": "ADMIN_HR",
                "pm": "OPERATIONS", "shop": "OPERATIONS",
                "safety": "OPERATIONS", "dispatch": "OPERATIONS",
                # TRACK 14.0-SSO · FL is an operational portal.
                "field_leadership": "OPERATIONS",
            }.get(target, "OPERATIONS")
            await reset_session_activity(
                db, tok, _tier,
                user_id=row.get("id"),
                email=row.get("email"),
                actor_label=target,
                ip=(_client_ip(request) if request else None),
                user_agent=(request.headers.get("user-agent") if request else "") or "",
            )
        except Exception:  # noqa: BLE001
            pass
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
        # Track 15.14A · Layer 4 — after a successful rotation, re-mint
        # the full portal-token bundle so the SPA can land the user on
        # their portal in one round-trip (no second sign-in required).
        # The old per-portal tokens, if any, are HMAC-bound to the prior
        # password hash and were already invalidated by the password
        # change above.
        fresh_row = await db.user_directory.find_one(
            {"id": row["id"]}, {"_id": 0},
        )
        portal_tokens = await _mint_all(fresh_row or row)
        try:
            from session_timeout import reset_session_activity
            import asyncio  # noqa: PLC0415
            _tier = {
                "admin": "ADMIN_HR", "hr": "ADMIN_HR",
                "pm": "OPERATIONS", "shop": "OPERATIONS",
                "safety": "OPERATIONS", "dispatch": "OPERATIONS",
                "field_leadership": "ADMIN_FL",
            }
            _ua = (request.headers.get("user-agent") if request else "") or ""
            _ip = _client_ip(request) if request else None
            _tasks = [
                reset_session_activity(
                    db, _tok, _tier.get(_p, "OPERATIONS"),
                    user_id=(fresh_row or row).get("id"),
                    email=(fresh_row or row).get("email"),
                    actor_label=_p, ip=_ip, user_agent=_ua,
                )
                for _p, _tok in (portal_tokens or {}).items() if _tok
            ]
            if _tasks:
                await asyncio.gather(*_tasks, return_exceptions=True)
        except Exception:  # noqa: BLE001
            pass
        return {
            "ok": True,
            "portal_tokens": portal_tokens,
            "user": ud.public_view(fresh_row or row),
            "must_change_password": False,
        }

    # ── Admin endpoints ─────────────────────────────────────────────
    @router.get("/api/admin/directory", dependencies=[Depends(require_admin_strict_dep)])
    async def list_users(q: str = ""):
        """List directory users. Optional `q` filter performs a
        case-insensitive substring match against `email` + `name`
        (RC1-LIVE-VERIFY · P2 defect fix · 2026-06-15)."""
        rows = []
        async for r in db.user_directory.find({}, {"_id": 0}).sort("created_at", -1):
            view = ud.public_view(r)
            # Track 15.88 · access-state envelope (usable_now, blocked_reason, etc.)
            _enrich_with_access_state(view, r)
            rows.append(view)
        needle = (q or "").strip().lower()
        if needle:
            rows = [
                r for r in rows
                if needle in (r.get("email") or "").lower()
                or needle in (r.get("name") or "").lower()
            ]
        return {"ok": True, "users": rows}

    @router.post("/api/admin/directory", dependencies=[Depends(require_admin_strict_dep)])
    async def create_user(body: CreateDirectoryUserBody, request: Request):
        delivery = (body.delivery or "email").lower()
        # If admin chose email delivery and didn't pass a password, generate one.
        password = body.password.strip() if body.password else ""
        if not password:
            if delivery == "email":
                password = _generate_temp_password()
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Password is required when delivery is not email.",
                )
        try:
            view = await ud.create_directory_user(
                db,
                email=body.email,
                name=body.name,
                portals=body.portals,
                password=password,
                must_change_password=body.must_change_password,
            )
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        # Track 15.88 · enrich with access-state envelope.
        _raw = await ud.find_by_id(db, view.get("id"))
        _enrich_with_access_state(view, _raw)
        email_sent = False
        if delivery == "email":
            email_sent = await _send_directory_welcome(
                view["email"], view.get("name") or "", password, view["portals"], is_reset=False
            )
        await ud.write_audit(
            db,
            actor_email=_audit_actor(request),
            action="directory_create",
            target_email=view["email"],
            diff={
                "portals": view["portals"],
                "must_change_password": body.must_change_password,
                "delivery": delivery,
                "email_sent": email_sent,
            },
            ip=_client_ip(request),
        )
        return {
            "ok": True,
            "user": view,
            # If email delivery succeeded, don't return the password —
            # forces the admin UI to show "Email sent" instead of leaking.
            # If email failed or delivery=show, return it so the admin
            # can copy it out manually.
            "temp_password": None if (delivery == "email" and email_sent) else password,
            "email_sent": email_sent,
            "delivery": delivery,
        }

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
        # Track 15.88 · enrich.
        _raw = await ud.find_by_id(db, user_id)
        _enrich_with_access_state(view, _raw)
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
        delivery = (body.delivery or "email").lower()
        new_pw = body.new_password.strip() if body.new_password else ""
        if not new_pw:
            if delivery == "email":
                new_pw = _generate_temp_password()
            else:
                raise HTTPException(
                    status_code=400,
                    detail="new_password is required when delivery is not email.",
                )
        try:
            view = await ud.rotate_master_password(
                db,
                user_id=user_id,
                new_password=new_pw,
                must_change=body.must_change,
            )
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        # Track 15.88 · enrich.
        _raw = await ud.find_by_id(db, user_id)
        _enrich_with_access_state(view, _raw)
        email_sent = False
        if delivery == "email":
            email_sent = await _send_directory_welcome(
                existing["email"],
                existing.get("name") or "",
                new_pw,
                existing.get("portals") or [],
                is_reset=True,
            )
        await ud.write_audit(
            db,
            actor_email=_audit_actor(request),
            action="directory_password_reset",
            target_email=existing.get("email"),
            diff={
                "must_change": bool(body.must_change),
                "delivery": delivery,
                "email_sent": email_sent,
            },
            ip=_client_ip(request),
        )
        return {
            "ok": True,
            "user": view,
            "temp_password": None if (delivery == "email" and email_sent) else new_pw,
            "email_sent": email_sent,
            "delivery": delivery,
        }

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

    # iter375 · Expose the internal portal-token minter so the MFA router
    # can re-mint tokens after successful TOTP verification (preserves the
    # exact same logic as multi-login).
    router._mint_all_portal_tokens = _mint_all  # type: ignore[attr-defined]

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

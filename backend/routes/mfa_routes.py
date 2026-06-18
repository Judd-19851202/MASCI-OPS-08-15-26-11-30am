"""
routes/mfa_routes.py · iter375 · Phase 4B · MFA HTTP surface.

Endpoints (all under /api):

For the authenticated super-admin (X-Admin-Token required):
  GET    /admin/mfa/status                 — { enabled, enrolled_at, recovery_codes_remaining }
  POST   /admin/mfa/enroll/start           — { otpauth_uri, secret, qr_data_uri, recovery_codes }
  POST   /admin/mfa/enroll/verify          — { ok: true }  (also marks enabled=true)
  POST   /admin/mfa/disable                — requires current TOTP code; clears config
  POST   /admin/mfa/regenerate-recovery    — requires current TOTP code; returns new codes

Public (login-time, no auth header):
  POST   /auth/mfa/verify-login            — body: { challenge_token, code? | recovery_code? }
                                              → returns the same payload as multi-login
                                              (portal_tokens + session_token + user)

Frontend integration:
  • multi-login response now returns `{ mfa_required: true, mfa_challenge_token }`
    when the directory user has MFA enabled.
  • Frontend redirects to MFA challenge screen, posts the code to
    /auth/mfa/verify-login, then proceeds with the returned portal tokens.
"""
from __future__ import annotations

import base64
import io
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

import qrcode
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request
from pydantic import BaseModel

import mfa
import user_directory as ud

logger = logging.getLogger(__name__)


def _client_ip(req: Request) -> str:
    try:
        fwd = req.headers.get("x-forwarded-for") or req.headers.get("x-real-ip")
        if fwd:
            return fwd.split(",")[0].strip()
        return req.client.host if req.client else ""
    except Exception:
        return ""


def _qr_data_uri(otpauth_uri: str) -> str:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=8, border=4)
    qr.add_data(otpauth_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


class MFAVerifyBody(BaseModel):
    code: Optional[str] = None
    recovery_code: Optional[str] = None


class MFAChallengeBody(BaseModel):
    challenge_token: str
    code: Optional[str] = None
    recovery_code: Optional[str] = None


def build_mfa_router(db, require_admin_strict_dep: Callable,
                     mint_all_portal_tokens_fn: Callable) -> APIRouter:
    """Build the MFA router.

    Args:
      db: motor database handle.
      require_admin_strict_dep: FastAPI dependency that returns True for
        a strict admin token (used to gate admin-side MFA management).
        Must reject PM/Shop/HR/etc tokens (uses `require_admin_strict`).
      mint_all_portal_tokens_fn: async callable `(row) -> portal_tokens dict`.
        Used by /auth/mfa/verify-login to re-mint portal tokens after
        successful TOTP verification.
    """
    router = APIRouter(prefix="/api", tags=["mfa"])

    async def _resolve_acting_directory_user(
        request: Request,
    ) -> Dict[str, Any]:
        """For admin-side MFA endpoints, we need to know WHICH directory
        super-admin is acting (so MFA config attaches to their row, not
        to the global shared admin password).

        We honour the directory session header (X-Directory-Token) — that
        is the multi-login session cookie. If absent, return 400.
        """
        dir_token = request.headers.get("x-directory-token") or ""
        if not dir_token:
            raise HTTPException(
                400,
                "Directory session required for MFA management. Sign in via the unified login.",
            )
        row = await ud.session_user(db, token=dir_token)
        if not row:
            raise HTTPException(401, "Directory session expired.")
        if not row.get("is_super_admin"):
            raise HTTPException(403, "MFA is restricted to super-admin accounts.")
        return row

    # ─── Status ──────────────────────────────────────────────────────
    @router.get("/admin/mfa/status",
                dependencies=[Depends(require_admin_strict_dep)])
    async def mfa_status(request: Request):
        user = await _resolve_acting_directory_user(request)
        cfg = await mfa.get_mfa_config(db, user["id"])
        return {
            "enabled": bool(cfg.get("enabled")),
            "enrolled_at": cfg.get("enrolled_at"),
            "recovery_codes_remaining": len(cfg.get("recovery_code_hashes") or []),
            "locked": mfa.is_locked(cfg),
            "user_email": user.get("email"),
        }

    # ─── Enrollment · start ──────────────────────────────────────────
    @router.post("/admin/mfa/enroll/start",
                 dependencies=[Depends(require_admin_strict_dep)])
    async def mfa_enroll_start(request: Request):
        user = await _resolve_acting_directory_user(request)
        cfg = await mfa.get_mfa_config(db, user["id"])
        if cfg.get("enabled"):
            raise HTTPException(400, "MFA already enrolled. Disable first to re-enroll.")
        secret = mfa.create_totp_secret()
        encrypted = mfa.encrypt_secret(secret)
        otpauth = mfa.build_otpauth_uri(secret, user["email"])
        codes, hashes = mfa.generate_recovery_codes()
        await mfa.set_mfa_config(db, user["id"], {
            "enabled": False,
            "encrypted_totp_secret": encrypted,
            "encryption_key_id": "v1",
            "enrolled_at": None,
            "recovery_code_hashes": hashes,
            "failed_attempts": 0,
            "locked_until": None,
            "last_failed_at": None,
        })
        await mfa.write_audit(db, user_id=user["id"], user_email=user.get("email"),
                              event="ENROLLMENT_STARTED",
                              ip=_client_ip(request),
                              user_agent=request.headers.get("user-agent"))
        return {
            "ok": True,
            "otpauth_uri": otpauth,
            "secret": secret,
            "qr_data_uri": _qr_data_uri(otpauth),
            "recovery_codes": codes,
            "issuer": mfa.MFA_ISSUER,
            "email": user["email"],
        }

    # ─── Enrollment · verify ─────────────────────────────────────────
    @router.post("/admin/mfa/enroll/verify",
                 dependencies=[Depends(require_admin_strict_dep)])
    async def mfa_enroll_verify(request: Request, body: MFAVerifyBody):
        user = await _resolve_acting_directory_user(request)
        cfg = await mfa.get_mfa_config(db, user["id"])
        if cfg.get("enabled"):
            raise HTTPException(400, "MFA already verified.")
        if not cfg.get("encrypted_totp_secret"):
            raise HTTPException(400, "MFA not initialized — call /enroll/start first.")
        if mfa.is_locked(cfg):
            raise HTTPException(423, "MFA is temporarily locked. Try again later.")
        if not body.code:
            raise HTTPException(400, "code required")
        secret = mfa.decrypt_secret(cfg["encrypted_totp_secret"])
        if not mfa.verify_totp_code(secret, body.code):
            await mfa.register_failure(db, user["id"], cfg)
            await mfa.write_audit(db, user_id=user["id"], user_email=user.get("email"),
                                  event="TOTP_VERIFY_FAILURE",
                                  ip=_client_ip(request),
                                  user_agent=request.headers.get("user-agent"),
                                  metadata={"context": "enrollment"})
            raise HTTPException(400, "Invalid TOTP code.")
        await mfa.set_mfa_config(db, user["id"], {
            "enabled": True,
            "enrolled_at": datetime.now(timezone.utc).isoformat(),
            "failed_attempts": 0,
            "locked_until": None,
        })
        await mfa.write_audit(db, user_id=user["id"], user_email=user.get("email"),
                              event="ENROLLMENT_COMPLETED",
                              ip=_client_ip(request),
                              user_agent=request.headers.get("user-agent"))
        return {"ok": True}

    # ─── Disable ─────────────────────────────────────────────────────
    @router.post("/admin/mfa/disable",
                 dependencies=[Depends(require_admin_strict_dep)])
    async def mfa_disable(request: Request, body: MFAVerifyBody):
        user = await _resolve_acting_directory_user(request)
        cfg = await mfa.get_mfa_config(db, user["id"])
        if not cfg.get("enabled"):
            raise HTTPException(400, "MFA not enabled.")
        if mfa.is_locked(cfg):
            raise HTTPException(423, "MFA is temporarily locked.")
        if not body.code:
            raise HTTPException(400, "TOTP code required to disable MFA.")
        secret = mfa.decrypt_secret(cfg["encrypted_totp_secret"])
        if not mfa.verify_totp_code(secret, body.code):
            await mfa.register_failure(db, user["id"], cfg)
            await mfa.write_audit(db, user_id=user["id"], user_email=user.get("email"),
                                  event="TOTP_VERIFY_FAILURE",
                                  ip=_client_ip(request),
                                  user_agent=request.headers.get("user-agent"),
                                  metadata={"context": "disable"})
            raise HTTPException(400, "Invalid TOTP code.")
        await mfa.clear_mfa_config(db, user["id"])
        await mfa.write_audit(db, user_id=user["id"], user_email=user.get("email"),
                              event="MFA_DISABLED",
                              ip=_client_ip(request),
                              user_agent=request.headers.get("user-agent"))
        return {"ok": True}

    # ─── Regenerate recovery codes ───────────────────────────────────
    @router.post("/admin/mfa/regenerate-recovery",
                 dependencies=[Depends(require_admin_strict_dep)])
    async def mfa_regenerate_recovery(request: Request, body: MFAVerifyBody):
        user = await _resolve_acting_directory_user(request)
        cfg = await mfa.get_mfa_config(db, user["id"])
        if not cfg.get("enabled"):
            raise HTTPException(400, "MFA not enabled.")
        if mfa.is_locked(cfg):
            raise HTTPException(423, "MFA is temporarily locked.")
        if not body.code:
            raise HTTPException(400, "TOTP code required to regenerate recovery codes.")
        secret = mfa.decrypt_secret(cfg["encrypted_totp_secret"])
        if not mfa.verify_totp_code(secret, body.code):
            await mfa.register_failure(db, user["id"], cfg)
            await mfa.write_audit(db, user_id=user["id"], user_email=user.get("email"),
                                  event="TOTP_VERIFY_FAILURE",
                                  ip=_client_ip(request),
                                  user_agent=request.headers.get("user-agent"),
                                  metadata={"context": "regen_recovery"})
            raise HTTPException(400, "Invalid TOTP code.")
        codes, hashes = mfa.generate_recovery_codes()
        await mfa.set_mfa_config(db, user["id"], {"recovery_code_hashes": hashes})
        await mfa.write_audit(db, user_id=user["id"], user_email=user.get("email"),
                              event="RECOVERY_CODES_REGENERATED",
                              ip=_client_ip(request),
                              user_agent=request.headers.get("user-agent"))
        return {"ok": True, "recovery_codes": codes}

    # ─── Login MFA verification (public — uses challenge_token) ──────
    @router.post("/auth/mfa/verify-login")
    async def mfa_verify_login(request: Request, body: MFAChallengeBody):
        user_id = mfa.verify_challenge_token(body.challenge_token)
        if not user_id:
            raise HTTPException(401, "MFA challenge expired or invalid. Sign in again.")
        row = await db.user_directory.find_one({"id": user_id}, {"_id": 0})
        if not row or row.get("disabled"):
            raise HTTPException(401, "Account unavailable.")
        cfg = (row or {}).get("mfa") or {}
        if not cfg.get("enabled"):
            raise HTTPException(400, "MFA not enabled for this account.")
        if mfa.is_locked(cfg):
            await mfa.write_audit(db, user_id=user_id, user_email=row.get("email"),
                                  event="MFA_LOCKED_HIT", ip=_client_ip(request),
                                  user_agent=request.headers.get("user-agent"))
            raise HTTPException(423, "MFA is temporarily locked. Try again later.")
        # Verify either TOTP code or recovery code
        ok = False
        used_recovery = False
        if body.code:
            secret = mfa.decrypt_secret(cfg["encrypted_totp_secret"])
            ok = mfa.verify_totp_code(secret, body.code)
        elif body.recovery_code:
            submitted = (body.recovery_code or "").strip().upper()
            hashes = list(cfg.get("recovery_code_hashes") or [])
            matched_idx = None
            for idx, h in enumerate(hashes):
                if mfa.verify_recovery_code(submitted, h):
                    matched_idx = idx
                    break
            if matched_idx is not None:
                hashes.pop(matched_idx)
                await mfa.set_mfa_config(db, user_id, {"recovery_code_hashes": hashes})
                ok = True
                used_recovery = True
        else:
            raise HTTPException(400, "Provide either `code` or `recovery_code`.")
        if not ok:
            locked = await mfa.register_failure(db, user_id, cfg)
            await mfa.write_audit(
                db, user_id=user_id, user_email=row.get("email"),
                event=("RECOVERY_CODE_FAILURE" if body.recovery_code else "TOTP_VERIFY_FAILURE"),
                ip=_client_ip(request),
                user_agent=request.headers.get("user-agent"),
                metadata={"context": "login", "locked": locked},
            )
            if locked:
                raise HTTPException(423, "Too many failed attempts. MFA is now locked.")
            raise HTTPException(400, "Invalid code.")
        # SUCCESS — reset failures, mint portal tokens, write audit
        await mfa.reset_failures(db, user_id)

        # Track 15.14A · Layer 1 — TEMP-PASSWORD ENFORCEMENT on MFA path.
        # If the directory user still owes a password rotation, hand back
        # the session_token but NO portal tokens so the SPA must force
        # them through /change-password before any portal can be used.
        if bool(row.get("must_change_password")):
            session_token = ud.make_directory_token()
            await ud.persist_session(db, token=session_token, user_id=row["id"])
            await ud.stamp_last_login(db, user_id=row["id"], portal="multi")
            await mfa.write_audit(
                db, user_id=user_id, user_email=row.get("email"),
                event="LOGIN_TEMP_PW_BLOCKED",
                ip=_client_ip(request),
                user_agent=request.headers.get("user-agent"),
                metadata={"reason": "must_change_password=true; portal_tokens suppressed"},
            )
            return {
                "ok": True,
                "session_token": session_token,
                "portal_tokens": {},
                "user": ud.public_view(row),
                "must_change_password": True,
            }

        portal_tokens = await mint_all_portal_tokens_fn(row)
        session_token = ud.make_directory_token()
        await ud.persist_session(db, token=session_token, user_id=row["id"])
        await ud.stamp_last_login(db, user_id=row["id"], portal="multi")
        await mfa.write_audit(
            db, user_id=user_id, user_email=row.get("email"),
            event=("RECOVERY_CODE_USED" if used_recovery else "TOTP_VERIFY_SUCCESS"),
            ip=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            metadata={"context": "login",
                      "recovery_codes_remaining": (
                          len((await mfa.get_mfa_config(db, user_id)).get("recovery_code_hashes") or [])
                      )},
        )
        # Reset session_activity rows for each portal token (mirrors multi-login behaviour)
        try:
            from session_timeout import reset_session_activity
            _tier = {"admin": "ADMIN_HR", "hr": "ADMIN_HR",
                     "pm": "OPERATIONS", "shop": "OPERATIONS",
                     "safety": "OPERATIONS", "dispatch": "OPERATIONS",
                     "field_leadership": "ADMIN_FL"}
            _ua = request.headers.get("user-agent") or ""
            _ip = _client_ip(request)
            for _p, _t in (portal_tokens or {}).items():
                if _t:
                    await reset_session_activity(
                        db, _t, _tier.get(_p, "OPERATIONS"),
                        user_id=row.get("id"), email=row.get("email"),
                        actor_label=_p, ip=_ip, user_agent=_ua,
                    )
        except Exception:  # noqa: BLE001
            pass
        return {
            "ok": True,
            "session_token": session_token,
            "portal_tokens": portal_tokens,
            "user": ud.public_view(row),
            "must_change_password": bool(row.get("must_change_password")),
        }

    return router


__all__ = ["build_mfa_router"]

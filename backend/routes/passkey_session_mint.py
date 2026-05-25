"""routes/passkey_session_mint.py · iter431 · Phase 29 · Part 5b.

Cross-portal session mint helper used by the WebAuthn passkey login
flow. Previously inline in server.py:9840-9914 as
`_mint_multi_login_response_for_passkey`.

This is a ZERO-BEHAVIOR-CHANGE factory extraction. Every dependency
that used to be resolved as a module-level global in server.py is
passed in via `make_mint_multi_login_response_for_passkey(...)`.

Mount:

    from routes.passkey_session_mint import (
        make_mint_multi_login_response_for_passkey,
    )
    _mint_multi_login_response_for_passkey = make_mint_multi_login_response_for_passkey(
        db=db,
        mint_all_portal_tokens_fn=_auth_directory_router._mint_all_portal_tokens,
        ud_for_pk=_ud_for_pk,
    )
"""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict

from fastapi import HTTPException, Request

logger = logging.getLogger("passkey_session_mint")

PortalTokensFn = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]


def make_mint_multi_login_response_for_passkey(
    *,
    db,
    mint_all_portal_tokens_fn: PortalTokensFn,
    ud_for_pk,                   # users_directory module reference
):
    """Build the passkey post-ceremony session-mint callable.

    Returned callable signature mirrors the inline server.py function:
        async def _mint(user_row, request) -> Dict[str, Any]
    """
    async def _mint(
        user_row: Dict[str, Any],
        request: Request,
    ) -> Dict[str, Any]:
        """Replicate /api/auth/multi-login response shape after a
        successful passkey ceremony. MFA still applies — if the user
        has MFA enabled, return the same challenge envelope the
        password flow returns."""
        # MFA gate (preserves doctrine from iter375)
        cfg = user_row.get("mfa") or {}
        if cfg.get("enabled"):
            try:
                import mfa as _mfa  # noqa: PLC0415
                challenge = _mfa.mint_challenge_token(user_row["id"])
                await _mfa.write_audit(
                    db,
                    user_id=user_row["id"],
                    user_email=user_row.get("email"),
                    event="LOGIN_MFA_CHALLENGE_ISSUED",
                    ip=(request.client.host if request.client else None),
                    user_agent=request.headers.get("user-agent"),
                    metadata={"login_method": "passkey"},
                )
            except Exception as e:  # noqa: BLE001
                logger.error(f"[passkey-login] MFA challenge mint failed: {e}")
                raise HTTPException(500, "MFA challenge unavailable")
            return {
                "ok": True,
                "mfa_required": True,
                "mfa_challenge_token": challenge,
                "user": {"email": user_row.get("email"),
                         "name": user_row.get("name")},
            }

        portal_tokens = await mint_all_portal_tokens_fn(user_row)
        session_token = ud_for_pk.make_directory_token()
        await ud_for_pk.persist_session(db, token=session_token, user_id=user_row["id"])
        await ud_for_pk.stamp_last_login(db, user_id=user_row["id"], portal="multi")

        # Session-activity reset (mirrors multi-login behaviour)
        try:
            from session_timeout import reset_session_activity  # noqa: PLC0415
            _tier = {"admin": "ADMIN_HR", "hr": "ADMIN_HR",
                     "pm": "OPERATIONS", "shop": "OPERATIONS",
                     "safety": "OPERATIONS", "dispatch": "OPERATIONS",
                     "field_leadership": "ADMIN_FL"}
            _ua = request.headers.get("user-agent") or ""
            _ip = request.client.host if request.client else None
            for _p, _t in (portal_tokens or {}).items():
                if _t:
                    await reset_session_activity(
                        db, _t, _tier.get(_p, "OPERATIONS"),
                        user_id=user_row.get("id"),
                        email=user_row.get("email"),
                        actor_label=_p, ip=_ip, user_agent=_ua,
                    )
        except Exception:  # noqa: BLE001
            pass

        # Audit · same shape as multi-login but with method tag
        try:
            await ud_for_pk.write_audit(
                db,
                actor_email=user_row["email"],
                action="multi_login",
                target_email=user_row["email"],
                diff={
                    "portals_granted": sorted([p for p, t in (portal_tokens or {}).items() if t]),
                    "login_method": "passkey",
                },
                ip=(request.client.host if request.client else None),
                user_agent=request.headers.get("user-agent"),
            )
        except Exception:  # noqa: BLE001
            pass

        return {
            "ok": True,
            "session_token": session_token,
            "portal_tokens": portal_tokens,
            "user": ud_for_pk.public_view(user_row),
            "must_change_password": bool(user_row.get("must_change_password")),
        }

    return _mint

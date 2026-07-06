"""lib/multi_portal_session_enrichment.py — TRACK 23.9A.

Every per-portal login endpoint (`/api/hr/login`, `/api/pm/login`,
`/api/shop/login`, `/api/safety/login`, `/api/dispatch/login`,
`/api/field-leadership/portal/login`, `/api/admin/login`) historically
returned ONLY the one portal's token. That broke the "one login, many
authorized portals" contract — users who logged in via
`/hr/login` and navigated to `/pm` got bounced to `/pm/login` because
the master directory session was never established.

This helper takes any per-portal login's `email` + `password`, and
if they authenticate against `db.user_directory`, ALSO mints:

    * the master `session_token`
    * every `portal_tokens[…]` the user is granted
    * `user.portals[]`
    * `must_change_password` flag

The per-portal handler MERGES this envelope into its response so the
frontend's existing `directoryAuth.applyMultiLoginResponse()` fan-out
just works — no auth-provider change, no password logic change.

If the email is not in `user_directory` (legacy portal-only account),
the helper returns None and the per-portal handler falls back to its
existing behavior. Nothing regresses.

TRACK 23.9A · CRITICAL: this helper NEVER re-authenticates. It relies
on the per-portal handler having ALREADY verified the password. All
we do here is look up the directory row + issue the same tokens
`/api/auth/multi-login` would have issued.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


async def try_enrich_with_master_session(
    db,
    *,
    email: str,
    password: str,
    portal_minters: Dict[str, Callable[..., Any]],
) -> Optional[Dict[str, Any]]:
    """Return a multi-login-shaped envelope (`session_token`,
    `portal_tokens{}`, `user`) when the credentials match a
    directory user in good standing; otherwise return None.

    Never raises. On any internal error the caller must fall back to
    its native per-portal behavior.

    `portal_minters` maps portal name → an async callable that mints
    that portal's token given the directory user dict. The caller
    (server.py) supplies the exact same functions
    `/api/auth/multi-login` uses.
    """
    if not email or not password:
        return None
    try:
        import user_directory as ud  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[23.9A enrich] user_directory unavailable: {e}")
        return None

    try:
        row = await ud.authenticate(db, email=email, password=password)
    except Exception as e:  # noqa: BLE001
        logger.info(f"[23.9A enrich] authenticate error (falling back): {e}")
        return None
    if not row:
        return None
    # Directory user in must-change-password mode should NOT get
    # portal tokens — same policy `/api/auth/multi-login` enforces.
    if bool(row.get("must_change_password")):
        return None
    # MFA-enabled directory users are ALSO gated — per-portal login is
    # bypassing MFA here, which would be a security regression. Return
    # None so the per-portal handler ships its own token only (which is
    # already what the operator sees today for these users).
    cfg = row.get("mfa") or {}
    if cfg.get("enabled"):
        return None

    # Mint every portal token the user is granted.
    portal_tokens: Dict[str, str] = {}
    portals = list(row.get("portals") or [])
    for portal_name in portals:
        minter = portal_minters.get(portal_name)
        if not minter:
            continue
        try:
            tok = await _maybe_await(minter(row))
            if tok:
                portal_tokens[portal_name] = tok
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[23.9A enrich] {portal_name} minter failed: {e}")
    # Track 14.0-SSO alias — expose `fl` alongside `field_leadership`.
    if "field_leadership" in portal_tokens and "fl" not in portal_tokens:
        portal_tokens["fl"] = portal_tokens["field_leadership"]

    if not portal_tokens:
        # User has no portal grants — treat as an anonymous case; the
        # per-portal handler will still issue its own scoped token
        # (which it just did before calling us).
        return None

    # Establish the master directory session.
    try:
        session_token = ud.make_directory_token()
        await ud.persist_session(db, token=session_token, user_id=row["id"])
        await ud.stamp_last_login(db, user_id=row["id"], portal="multi_via_portal_login")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[23.9A enrich] session persistence failed: {e}")
        return None

    # Kick the session_activity heartbeat for every minted token in
    # parallel (same pattern /api/auth/multi-login uses).
    try:
        from session_timeout import reset_session_activity  # noqa: PLC0415
        tier_by_portal = {
            "admin": "ADMIN_HR", "hr": "ADMIN_HR",
            "pm": "OPERATIONS", "shop": "OPERATIONS",
            "safety": "OPERATIONS", "dispatch": "OPERATIONS",
            "field_leadership": "ADMIN_FL",
        }
        tasks = [
            reset_session_activity(
                db, tok, tier_by_portal.get(p, "OPERATIONS"),
                user_id=row.get("id"), email=row.get("email"),
                actor_label=f"multi_via_{p}", ip=None, user_agent=None,
            )
            for p, tok in portal_tokens.items()
            if p != "fl"
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:  # noqa: BLE001
        logger.debug(f"[23.9A enrich] activity heartbeat skipped: {e}")

    return {
        "session_token": session_token,
        "portal_tokens": portal_tokens,
        "user": ud.public_view(row),
        "must_change_password": False,
        "sso_enriched": True,
    }


async def _maybe_await(v):
    if asyncio.iscoroutine(v):
        return await v
    return v


__all__ = ["try_enrich_with_master_session"]

"""TRACK 15.87 · Multi-Portal Access Authority Fix.

Canonical helper that lets every per-portal login endpoint accept a
directory-granted user whose ``portals`` array includes the relevant
portal key (`pm` · `shop` · `hr` · `safety` · `dispatch` ·
`field_leadership`), even when no row exists in the corresponding
legacy collection (``project_managers`` · ``shop_users`` · ``hr_users``
· ``safety_users`` · ``dispatch_users`` · ``field_leadership_users``).

Problem this fixes
------------------
The Admin Console → People & Access UI writes portal grants to
``user_directory.portals``. The ``POST /api/auth/multi-login``
endpoint correctly mints per-portal tokens off that array. But the
legacy per-portal login endpoints — ``POST /api/{pm,shop,hr,safety,
dispatch}/login`` — only check their legacy collection plus a
narrow admin-only directory fallback. A user granted, say, PM via
the directory but without a row in ``project_managers`` was denied at
``/pm/login`` with "Wrong email or password" — even though Admin
correctly showed them as having PM access. This file closes that gap.

How it works
------------
Each portal's login endpoint imports ``try_directory_portal_login``
and calls it after the legacy lookup misses. The helper:

  1. Authenticates the email + password against ``user_directory``
     (canonical bcrypt verification via ``user_directory.authenticate``).
  2. Rejects disabled directory users.
  3. Verifies the user's ``portals`` array contains ``required_portal``
     (no over-grant, no admin escalation).
  4. Mirrors the multi-login MFA gate (must_change_password → no
     portal tokens minted; SPA must rotate first).
  5. Calls the portal's existing async token minter (which auto-
     provisions a "shadow" row in the legacy collection so subsequent
     legacy logins work the same way they did before).
  6. Returns the canonical response envelope the legacy endpoint
     would have returned, so callers see no behavioral change.

RBAC contract
-------------
This helper is **additive**, not a bypass:

  * It uses the canonical ``user_directory.authenticate()`` bcrypt
    path — same security as multi-login.
  * It requires ``required_portal`` to be in the user's grants.
    Granting Shop does **not** unlock PM. Granting Field Leadership
    does **not** unlock Admin.
  * Disabled users are rejected.
  * Users with ``must_change_password=true`` are blocked from
    receiving a portal token (matches multi-login behaviour).
  * The minted token is the **portal-specific** token, never an
    admin token. The pre-existing "super-admin global fallback"
    (admin grant → admin token issued at any portal-login URL) is
    untouched — that is intentional and documented.
"""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict, Optional, Union

logger = logging.getLogger(__name__)

# A portal token minter takes the directory ``row`` dict and returns
# the minted portal token string (or None on failure). The minters in
# ``server.py`` are async; the FL minter is sync. The helper accepts
# either by awaiting only when needed.
TokenMinter = Callable[[Dict[str, Any]], Union[Optional[str], Awaitable[Optional[str]]]]


async def _maybe_await(value):
    if hasattr(value, "__await__"):
        return await value
    return value


async def try_directory_portal_login(
    db,
    *,
    email: str,
    password: str,
    required_portal: str,
    portal_token_minter: Optional[TokenMinter],
    kind: str,
) -> Optional[Dict[str, Any]]:
    """Attempt directory-grant authentication for one specific portal.

    Returns the response envelope on success, ``None`` on every
    failure mode (caller falls through to its existing 401 path).

    Parameters
    ----------
    db
        Motor database handle.
    email
        Already-lowercased login email.
    password
        Master password as supplied by the user.
    required_portal
        One of ``admin / pm / shop / hr / safety / dispatch /
        field_leadership``. The directory user MUST have this key in
        their ``portals`` array.
    portal_token_minter
        Async (or sync) callable that mints the portal-specific token
        for a directory ``row``. Typically the same minter that
        multi-login uses. ``None`` disables the directory path
        entirely (kill-switch for tests).
    kind
        ``"hr" / "pm" / "shop" / "safety" / "dispatch" /
        "field_leadership"`` — echoed back in the response envelope's
        ``kind`` field so the SPA storage layer routes the token to
        the correct localStorage key.
    """
    if portal_token_minter is None:
        return None
    if not email or not password:
        return None

    try:
        import user_directory as _ud
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"track_15_87 directory import failed: {exc}")
        return None

    try:
        row = await _ud.authenticate(db, email=email, password=password)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"track_15_87 directory auth error: {exc}")
        return None
    if not row:
        return None
    if row.get("disabled"):
        return None
    portals = list(row.get("portals") or [])
    if required_portal not in portals:
        return None
    if bool(row.get("must_change_password")):
        # Mirror the multi-login behaviour: do not hand out portal
        # tokens until the password is rotated. The SPA must surface
        # this state.
        return None

    try:
        token = await _maybe_await(portal_token_minter(row))
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"track_15_87 portal token mint failed ({required_portal}): {exc}")
        return None
    if not token:
        return None

    return {
        "ok": True,
        "token": token,
        "kind": kind,
        "user": _ud.public_view(row),
        "must_change_password": False,
        "via": "directory_grant",
    }

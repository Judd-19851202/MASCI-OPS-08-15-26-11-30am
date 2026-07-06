"""
iter373 · Shared auth dependency factories for the HR Portal.

Mirrors the safety_portal/_deps.py + dispatch_portal_auth.py +
shop_portal_deps.py patterns established in iter370-iter372.

This module provides:
  • `make_require_hr_user(db)` — canonical HR-only token resolver.
    Returns `{**user, "_actor_kind": "hr_user"}`. Single source of truth
    for the HR portal's foundational dependency.

Intentionally NOT included (documented ambiguity — leave alone):

  • `require_hr_or_admin` closure in `routes/employee_lifecycle.py`:
    Filters from `require_any_portal_token` (multi-portal aggregator)
    by inspecting `_actor`/`role` keys; returns the original actor and
    raises 403. Different semantic surface — extracting it would change
    the actor shape contract for employee lifecycle handlers.

  • `require_hr_or_admin` closure in `routes/field_leadership_portal.py`:
    Direct admin/HR token check that tries `require_admin_dep` first
    (which itself accepts admin+PM with iter180 namespace lockdown +
    swallows exceptions on PM-only sessions), then falls back to HR.
    Returns `{"_actor_kind": ...}` and raises 401. Tightly coupled to
    the closure-passed `require_admin_dep` — cannot factor cleanly
    without expanding the admin acceptance contract.

These two closures share the *idea* "HR or admin can use this" but
implement it via two materially different token chains for two
different surface families. Per iter372 directive: "If any helper is
ambiguous, leave it alone and document why."
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Optional

from fastapi import Header, HTTPException, Request

from auth_must_change import enforce_password_change_required
from hr_users import is_valid_hr_user_token_async
from routes.role_guard_validation_seam import try_validation_fallback


def make_require_hr_user(db) -> Callable[..., Awaitable[Dict[str, Any]]]:
    """iter373 · Canonical HR-only token resolver factory.

    Mirrors `routes/safety_portal/_deps.make_require_safety_token`.

    Returns a FastAPI dependency that resolves `X-HR-Token` to the HR
    user document tagged with `_actor_kind="hr_user"`.

    Behavior locked by tests/test_iter373_hr_user_parity.py:
      • No token        → 401 "HR login required"
      • Invalid token   → 401 "HR session expired or invalid"
      • Valid token     → {**user, "_actor_kind": "hr_user"}

    TRACK 22.4b-followup-HR — preview-only PVI validation fallback.
    Runs ONLY after the real HR path has failed, only in preview-
    class environments with the explicit feature flag on, only when
    the caller offered a token, and only when it matches role="hr".
    """

    async def _require_hr_user(
        request: Request,
        x_hr_token: Optional[str] = Header(default=None, alias="X-HR-Token"),
    ) -> Dict[str, Any]:
        if not x_hr_token:
            raise HTTPException(401, "HR login required")
        user = await is_valid_hr_user_token_async(db, x_hr_token)
        if user:
            enforce_password_change_required(request, user)
            return {**user, "_actor_kind": "hr_user"}
        # PVI fallback — never runs in production.
        pvi = await try_validation_fallback(db, x_hr_token, expected_role="hr")
        if pvi:
            return {**pvi, "_actor_kind": "hr_user"}
        raise HTTPException(401, "HR session expired or invalid")

    return _require_hr_user


__all__ = ["make_require_hr_user"]

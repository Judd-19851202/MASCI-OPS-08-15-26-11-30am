"""
Shared auth dependency factories for the Safety Portal package.
"""
from __future__ import annotations
from typing import Optional, Callable, Awaitable

from fastapi import Header, HTTPException, Request

from auth_must_change import enforce_password_change_required
from safety_users import is_valid_safety_user_token_async
from routes.role_guard_validation_seam import try_validation_fallback


def make_require_safety_token(db) -> Callable[..., Awaitable[dict]]:
    """Factory — returns a FastAPI dependency that resolves the safety
    user from X-Safety-Token. Bound to db at construction time."""

    async def _require_safety_token(request: Request) -> dict:
        token = request.headers.get("X-Safety-Token", "")
        user = await is_valid_safety_user_token_async(db, token)
        if user:
            # Track 15.14A Layer 3 — temp-password backstop.
            enforce_password_change_required(request, user)
            return user
        # TRACK 22.4b-followup-Safety · preview-only PVI fallback.
        # Never reached in production (helper is env-guarded).
        pvi = await try_validation_fallback(db, token, expected_role="safety")
        if pvi:
            return pvi
        raise HTTPException(401, "Safety auth required")

    return _require_safety_token


def make_require_safety_or_admin(
    db, is_valid_admin_token: Optional[Callable[[str], bool]] = None,
    is_valid_admin_token_async: Optional[Callable[[str], Awaitable[bool]]] = None,
) -> Callable[..., Awaitable[dict]]:
    """Write-side gate. Accepts Safety or Admin tokens only — HR is
    intentionally NOT accepted here. Used for write surfaces inside
    Safety operations (Site Inspection submission, etc.) where HR
    review-side access is inappropriate for the action.

    TRACK 28.02 · adds ``is_valid_admin_token_async`` so directory-hydrated
    per-user admin tokens (UUID.HMAC form issued by
    ``/api/auth/multi-login``) unlock this write gate — the sync sentinel
    was retired in TRACK 15.32 and always returns False.
    """

    async def _require_safety_or_admin(
        request: Request,
        x_safety_token: Optional[str] = Header(default=None, alias="X-Safety-Token"),
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
    ) -> dict:
        if x_safety_token:
            u = await is_valid_safety_user_token_async(db, x_safety_token)
            if u:
                enforce_password_change_required(request, u)
                return {**u, "_actor": "safety"}
        if x_admin_token:
            if is_valid_admin_token and is_valid_admin_token(x_admin_token):
                return {"_actor": "admin", "name": "Admin"}
            if is_valid_admin_token_async and await is_valid_admin_token_async(x_admin_token):
                return {"_actor": "admin", "name": "Admin"}
        # TRACK 22.4b-followup-Safety · preview-only validation fallback.
        # Runs ONLY after the real safety/admin path has failed. Delegates
        # to the shared seam helper which enforces preview-env + feature
        # flag + role-match at the token layer. Never accepts admin
        # tokens for the fallback.
        pvi = await try_validation_fallback(db, x_safety_token, expected_role="safety")
        if pvi:
            return pvi
        raise HTTPException(401, "Safety or Admin auth required")

    return _require_safety_or_admin


def make_require_safety_or_admin_fleet(
    db, is_valid_admin_token: Optional[Callable[[str], bool]] = None,
    is_valid_admin_token_async: Optional[Callable[[str], Awaitable[bool]]] = None,
) -> Callable[..., Awaitable[dict]]:
    """iter372 · Canonical narrow Safety+Admin fleet-ops gate factory.

    Mirrors the dispatch (iter370) and shop (iter371) patterns. Single
    source of truth for the fleet_ops safety gate.

    Semantically distinct from `make_require_safety_or_admin` above:
      • This gate is used ONLY by fleet_ops.py via kwargs injection.
      • Return shape uses the "role" key family (consistent with the
        dispatch + shop fleet gates):
            – Admin token  → {"role": "admin"}
            – Safety token → {"role": "safety", **user}
      • Admin is checked FIRST (matches the dispatch/shop ordering).
      • Otherwise → HTTPException(401, "Safety or Admin auth required").

    The richer `make_require_safety_or_admin` above keeps its "_actor"
    return shape because its consumers (site-inspection POST, topic
    library, notifications) read that shape. Do NOT collapse the two —
    they serve different surfaces.
    """

    async def _require_safety_or_admin_fleet(
        request: Request,
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
        x_safety_token: Optional[str] = Header(default=None, alias="X-Safety-Token"),
    ) -> dict:
        if x_admin_token:
            if is_valid_admin_token and is_valid_admin_token(x_admin_token):
                return {"role": "admin"}
            if is_valid_admin_token_async and await is_valid_admin_token_async(x_admin_token):
                return {"role": "admin"}
        if x_safety_token:
            u = await is_valid_safety_user_token_async(db, x_safety_token)
            if u:
                enforce_password_change_required(request, u)
                return {"role": "safety", **u}
        raise HTTPException(401, "Safety or Admin auth required")

    return _require_safety_or_admin_fleet


def make_require_safety_admin_or_pm(
    db, is_valid_admin_token: Optional[Callable[[str], bool]] = None,
    is_valid_pm_token: Optional[Callable[[str], bool]] = None,
    is_valid_admin_token_async: Optional[Callable[[str], Awaitable[bool]]] = None,
) -> Callable[..., Awaitable[object]]:
    """iter322 · Safety-side **read** gate.

    Closes the operator bug where signed-in Safety reviewers were
    rejected with ``"Admin or PM login required"`` on
    ``GET /api/incidents``, ``/inspections``, ``/meetings``, ``/jhas``.

    Read-only — wires into list/detail surfaces inside ``routes/safety.py``
    so Safety reviewers can perform their core review duty without an
    Admin/PM gate. Destructive endpoints (DELETE) intentionally keep
    the stricter ``require_admin`` dep — RBAC is **not** weakened.

    Accepts:
      • ``X-Safety-Token`` → returns the safety user dict tagged with
        ``_actor_kind="safety_user"`` so :func:`compute_pm_scope` grants
        cross-job review visibility (mirrors the shop-user pattern).
      • ``X-Admin-Token``  → returns ``True`` (admin bypass). TRACK 28.02
        adds ``is_valid_admin_token_async`` support so directory-hydrated
        per-user admin tokens (UUID.HMAC form issued by
        ``/api/auth/multi-login``) unlock this gate — the sync sentinel
        was retired in TRACK 15.32 and always returns False.
      • ``X-PM-Token``     → returns the PM doc for project scoping
        (preserves existing PM data-scoping behaviour).

    Returns 401 ``"Safety, Admin, or PM login required"`` if no valid
    token is present.
    """

    async def _require_safety_admin_or_pm(
        request: Request,
        x_safety_token: Optional[str] = Header(default=None, alias="X-Safety-Token"),
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
        x_pm_token: Optional[str] = Header(default=None, alias="X-PM-Token"),
    ):
        if x_safety_token:
            u = await is_valid_safety_user_token_async(db, x_safety_token)
            if u:
                enforce_password_change_required(request, u)
                return {**u, "_actor_kind": "safety_user", "_actor": "safety"}
        if x_admin_token:
            # Sync legacy sentinel (retired in 15.32 — always False) …
            if is_valid_admin_token and is_valid_admin_token(x_admin_token):
                return {"role": "admin", "_actor": "admin", "_actor_kind": "admin"}
            # … then the directory-hydrated per-user admin token (TRACK 28.02).
            if is_valid_admin_token_async and await is_valid_admin_token_async(x_admin_token):
                return {"role": "admin", "_actor": "admin", "_actor_kind": "admin"}
        if x_pm_token:
            # Per-PM token (has ".") → DB lookup; legacy shared PM → env bypass.
            if "." in x_pm_token:
                from pm_auth import is_valid_pm_user_token_async  # noqa: PLC0415
                pm_doc = await is_valid_pm_user_token_async(db, x_pm_token)
                if pm_doc:
                    # iter452 — tag the PM doc so downstream role-normalizers
                    # can identify it as a PM actor. Pre-existing consumers
                    # spread the dict and ignore unknown keys, so this is
                    # additive-only.
                    enforce_password_change_required(request, pm_doc)
                    return {**pm_doc, "_actor_kind": "pm_user", "_actor": "pm"}
            elif is_valid_pm_token and is_valid_pm_token(x_pm_token):
                return True
        raise HTTPException(401, "Safety, Admin, or PM login required")

    return _require_safety_admin_or_pm


def make_require_safety_or_hr_or_admin(
    db,
    is_valid_admin_token: Optional[Callable[[str], bool]] = None,
    is_valid_admin_token_async: Optional[Callable[[str], Awaitable[bool]]] = None,
) -> Callable[..., Awaitable[dict]]:
    """Multi-role read gate. Accepts Safety, HR, or Admin tokens —
    used for cross-portal read surfaces (document library, training
    records, employee safety profile). Writes stay safety-only via the
    single-role dependency.

    Track 24.2 · adds `is_valid_admin_token_async` so directory-hydrated
    admin tokens (UUID form issued by /api/auth/multi-login) are
    honoured. The legacy sync `is_valid_admin_token` remains for the
    (now dead) sentinel path.
    """

    async def _require_safety_or_hr_or_admin(
        request: Request,
        x_safety_token: Optional[str] = Header(default=None, alias="X-Safety-Token"),
        x_hr_token: Optional[str] = Header(default=None, alias="X-HR-Token"),
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
    ) -> dict:
        if x_safety_token:
            u = await is_valid_safety_user_token_async(db, x_safety_token)
            if u:
                enforce_password_change_required(request, u)
                return {**u, "_actor": "safety"}
        if x_hr_token:
            from hr_users import is_valid_hr_user_token_async  # noqa: PLC0415
            u = await is_valid_hr_user_token_async(db, x_hr_token)
            if u:
                enforce_password_change_required(request, u)
                return {**u, "_actor": "hr"}
        if x_admin_token:
            # Sync legacy sentinel (retired but still handles well-known
            # break-glass tokens if enabled) …
            if is_valid_admin_token and is_valid_admin_token(x_admin_token):
                return {"_actor": "admin", "name": "Admin"}
            # … then the directory-hydrated per-user admin token.
            if is_valid_admin_token_async and await is_valid_admin_token_async(x_admin_token):
                return {"_actor": "admin", "name": "Admin"}
        raise HTTPException(401, "Safety, HR, or Admin auth required")

    return _require_safety_or_hr_or_admin

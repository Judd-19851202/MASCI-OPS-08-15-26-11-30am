"""TRACK 22.4b-followup-Safety · shared validation guard seam.

The reusable one-place-only fallback that lets each per-role guard
accept **preview validation tokens** (see routes.preview_validation_identities)
without weakening real production auth.

Contract
--------
1. **Real guard runs first, unchanged.** The existing per-role user
   directory lookup executes exactly as before. If it passes, its
   return value is passed through verbatim — no wrapping, no drift.
2. **Fallback runs only after real guard raises**, and only in
   preview-class environments with the explicit
   ``ENABLE_PREVIEW_VALIDATION_IDENTITIES=true`` flag.
3. **Validation token must match the expected role exactly.** A
   safety validation token cannot pass a shop guard and vice versa —
   ``verify_validation_token(db, token, expected_role=...)`` enforces
   this at the token level.
4. **Never returns admin context for a validation token.** Validation
   context is returned with ``_actor="validation:<role>"`` and
   ``validation_identity=True`` so downstream code can differentiate.
5. **Preserves the original auth failure** when the fallback fails —
   raises the same 401 the real guard would.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def role_guard_with_validation_fallback(
    real_guard: Callable[..., Any],
    *,
    role: str,
    db,
    token_header_attr: str,
    admin_header_attr: str = "x_admin_token",
) -> Callable[..., Any]:
    """Wrap ``real_guard`` with a preview-only validation fallback.

    Parameters
    ----------
    real_guard:
        The existing async guard dependency (e.g.
        ``_require_safety_or_admin``).
    role:
        The exact role the validation token must carry.
    db:
        The Motor database handle.
    token_header_attr:
        Name of the kwarg the real guard receives the role token in
        (e.g. ``"x_safety_token"``). Used to extract the token when
        the real guard fails.
    admin_header_attr:
        Name of the admin token kwarg (used only to detect whether the
        caller actually offered a role token vs. only admin).
    """

    async def _wrapped(*args, **kwargs):
        try:
            return await real_guard(*args, **kwargs)
        except HTTPException as real_exc:
            # Only try the fallback when the caller offered a token in
            # the role-token slot. Admin-only calls never trigger the
            # validation path (prevents "admin proves role" drift).
            token = kwargs.get(token_header_attr) or ""
            token = (token or "").strip()
            if not token:
                raise
            # Lazy import so this module has no hard dependency on the
            # validation module — if it is disabled or absent, real
            # auth failures propagate unchanged.
            try:
                from routes.preview_validation_identities import (  # noqa: PLC0415
                    verify_validation_token,
                    is_preview_validation_available,
                )
            except ImportError:
                raise real_exc  # noqa: B904
            if not is_preview_validation_available():
                raise
            identity = await verify_validation_token(
                db, token, expected_role=role,
            )
            if not identity:
                raise
            logger.info(
                "[validation-fallback] role=%s identity=%s track=%s",
                role,
                identity.get("validation_identity_id"),
                identity.get("validation_track"),
            )
            return {
                "_actor": f"validation:{role}",
                "validation_identity": True,
                "validation_identity_id": identity.get("validation_identity_id"),
                "validation_track": identity.get("validation_track"),
                "role": role,
                "name": identity.get("display_name") or f"validation:{role}",
                "no_real_operational_effect": True,
            }

    _wrapped.__name__ = getattr(real_guard, "__name__", "wrapped") + "_with_validation"
    return _wrapped


__all__ = ["role_guard_with_validation_fallback"]

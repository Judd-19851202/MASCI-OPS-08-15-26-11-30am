"""TRACK 22.4b-followup-Safety · shared validation guard seam.

One-place-only fallback that lets each per-role guard optionally
accept **preview validation tokens** (see
``routes.preview_validation_identities``) without weakening real
production auth.

Doctrine (unchanged from initial version)
-----------------------------------------
1. **Real guard runs first, unchanged.** The existing per-role user
   directory lookup executes exactly as before. If it passes, its
   return value is passed through verbatim — no wrapping, no drift.
2. **Fallback runs only after real auth fails**, and only in
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

Public API
----------
- ``try_validation_fallback(db, token, expected_role) -> Optional[dict]``
  Callable helper — every guard calls this **after** its real path
  has failed. Returns a normalized actor dict on success, ``None``
  when the token is not a valid PVI token for the requested role.
  Safe to call from any guard signature; never raises.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def try_validation_fallback(
    db,
    token: Optional[str],
    *,
    expected_role: str,
) -> Optional[Dict[str, Any]]:
    """Return a normalized validation-actor dict, or ``None``.

    Contract:
      • Returns ``None`` when the token is missing, malformed, expired,
        revoked, of the wrong role, or when preview validation is not
        available in this environment. Callers MUST fall through to
        their existing 401 in that case.
      • Never raises — swallows all internal errors (import failures,
        DB blips) and returns ``None`` so real auth stays authoritative.
      • On success returns a dict shaped like a real actor with:
            _actor="validation:<role>", role, name,
            validation_identity=True, validation_identity_id,
            validation_track, no_real_operational_effect=True.
    """
    if not token:
        return None
    token = token.strip()
    if not token:
        return None
    try:
        from routes.preview_validation_identities import (  # noqa: PLC0415
            verify_validation_token,
            is_preview_validation_available,
            TOKEN_PREFIX,
        )
    except ImportError:
        return None
    # Fast-path: reject anything that doesn't even look like a PVI token
    # BEFORE touching the DB. Real per-role tokens (bcrypt-bound HMAC
    # with a "<id>.<hmac>" shape) will not start with "PVI.".
    if not token.startswith(TOKEN_PREFIX):
        return None
    if not is_preview_validation_available():
        return None
    try:
        identity = await verify_validation_token(
            db, token, expected_role=expected_role,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[validation-fallback] verify failed: %s", exc)
        return None
    if not identity:
        return None
    logger.info(
        "[validation-fallback] role=%s identity=%s track=%s",
        expected_role,
        identity.get("validation_identity_id"),
        identity.get("validation_track"),
    )
    return {
        "_actor": f"validation:{expected_role}",
        "role": expected_role,
        "name": identity.get("display_name") or f"validation:{expected_role}",
        "validation_identity": True,
        "validation_identity_id": identity.get("validation_identity_id"),
        "validation_track": identity.get("validation_track"),
        "no_real_operational_effect": True,
    }


__all__ = ["try_validation_fallback"]

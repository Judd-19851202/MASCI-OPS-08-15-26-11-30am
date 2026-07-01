"""Track 19.16 · Phase A · Incident Intelligence Engine — PERMISSIONS.

Role → capability resolver. Pure function; no I/O. The ROLE_MATRIX in
``constants`` is the source of truth. This module never writes to it —
callers pass the role and the required capability; we answer boolean.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from .constants import ROLE_MATRIX


def normalize_role(actor: Any) -> str:
    """Coerce an actor object (dict, str, None) into one of the canonical
    role names. Recognised role signals (in order):

        actor["role"]     – newer dispatch/shop pattern
        actor["_actor"]   – older Safety-portal pattern
        actor is str      – already a role
    """
    if actor is None:
        return ""
    if isinstance(actor, str):
        return actor.strip().lower()
    if isinstance(actor, dict):
        for key in ("role", "_actor", "actor_role", "kind"):
            val = actor.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip().lower()
    return ""


def role_can(role: str, capability: str) -> bool:
    """Return True iff ``role`` owns ``capability``."""
    caps = ROLE_MATRIX.get(role or "")
    if not caps:
        return False
    return capability in caps


def actor_can(actor: Any, capability: str) -> bool:
    """Convenience wrapper: resolve role then check capability."""
    return role_can(normalize_role(actor), capability)


def require_capability(actor: Any, capability: str) -> None:
    """Raise ``PermissionError`` if actor lacks ``capability``.
    Callers translate to HTTP 403 at the route boundary."""
    if not actor_can(actor, capability):
        raise PermissionError(
            f"actor role={normalize_role(actor)!r} lacks capability={capability!r}"
        )


def capabilities_for(role: str) -> Iterable[str]:
    return sorted(ROLE_MATRIX.get(role or "", frozenset()))


__all__ = [
    "normalize_role",
    "role_can",
    "actor_can",
    "require_capability",
    "capabilities_for",
]

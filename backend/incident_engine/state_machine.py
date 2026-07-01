"""Track 19.16 · Phase A · Incident Intelligence Engine — STATE MACHINE.

Pure functions. Given a from_state, a to_state, and an actor, decide
whether the transition is legal. Callers persist the result; the state
machine is authoritative but stateless.
"""
from __future__ import annotations

from typing import Any, Optional, Tuple

from .constants import (
    CASE_DEFAULT_STATE,
    CASE_STATES,
    CASE_TRANSITIONS,
    IMMUTABLE_AFTER_STATES,
    TRANSITION_CAPABILITY,
)
from .permissions import actor_can, normalize_role


def coerce_state(v: Optional[str]) -> str:
    """Normalise a raw state string; return the default if unknown."""
    s = (v or "").strip().upper()
    if s in CASE_STATES:
        return s
    return CASE_DEFAULT_STATE


def is_legal(from_state: str, to_state: str) -> bool:
    """True iff the transition is topologically legal (ignores actor)."""
    from_state = coerce_state(from_state)
    to_state = (to_state or "").strip().upper()
    return to_state in CASE_TRANSITIONS.get(from_state, ())


def legal_next_states(from_state: str) -> Tuple[str, ...]:
    return tuple(CASE_TRANSITIONS.get(coerce_state(from_state), ()))


def field_block_immutable(state: str) -> bool:
    """True iff the field block is now locked."""
    return coerce_state(state) in IMMUTABLE_AFTER_STATES


def validate_transition(
    *,
    from_state: str,
    to_state: str,
    actor: Any,
    reason: str = "",
) -> Tuple[bool, str]:
    """Return (ok, error_code). error_code is empty when ok=True.

    Error codes are stable strings so the API layer / lock tests can
    assert on them without string matching:

        illegal_transition
        unknown_transition
        role_not_authorized
        reason_required
    """
    fs = coerce_state(from_state)
    ts = (to_state or "").strip().upper()

    if ts not in CASE_STATES:
        return False, "unknown_transition"
    if not is_legal(fs, ts):
        return False, "illegal_transition"

    # Reopen must include a reason (Trusted pillar — traceable action).
    if ts == "REOPENED" and not (reason or "").strip():
        return False, "reason_required"

    cap = TRANSITION_CAPABILITY.get((fs, ts))
    if not cap:
        return False, "unknown_transition"

    if not actor_can(actor, cap):
        return False, "role_not_authorized"

    return True, ""


__all__ = [
    "coerce_state",
    "is_legal",
    "legal_next_states",
    "field_block_immutable",
    "validate_transition",
]

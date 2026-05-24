"""
dispatch_lifecycle.py · iter392 · Phase 11.1 · DLS Backend Foundation

Pure state-machine module for the Dispatch Lifecycle System.

Doctrine: lifecycle states are the system. Forgiving operational continuity
beats rigid validation — trucking reality is messy (missed taps, late
updates, corrections, bad signal, truck-boss overrides). The system MUST
record truth and FLAG non-standard behavior, never block operations.

This module is intentionally:
  • Stateless (no DB handles, no globals)
  • Side-effect-free (pure functions over strings + dicts)
  • Importable from tests, routes, future analytics jobs

Consumers (routes/dispatch_lifecycle.py) own all I/O.
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Set

# ---------------------------------------------------------------------------
# Canonical 13 states (problem-statement contract, do NOT rename)
# ---------------------------------------------------------------------------
ASSIGNED = "ASSIGNED"
ENROUTE_TO_LOAD = "ENROUTE_TO_LOAD"
AT_LOAD_SITE = "AT_LOAD_SITE"
LOADING = "LOADING"
LOADED = "LOADED"
ENROUTE_TO_JOB = "ENROUTE_TO_JOB"
ARRIVED_JOB = "ARRIVED_JOB"
DUMPING = "DUMPING"
COMPLETE = "COMPLETE"
WAITING = "WAITING"
HOLD = "HOLD"
BREAKDOWN = "BREAKDOWN"
OFF_SHIFT = "OFF_SHIFT"

CANONICAL_STATES: List[str] = [
    ASSIGNED,
    ENROUTE_TO_LOAD,
    AT_LOAD_SITE,
    LOADING,
    LOADED,
    ENROUTE_TO_JOB,
    ARRIVED_JOB,
    DUMPING,
    COMPLETE,
    WAITING,
    HOLD,
    BREAKDOWN,
    OFF_SHIFT,
]
CANONICAL_STATE_SET: Set[str] = set(CANONICAL_STATES)

# Terminal states — no preferred successor (only ASSIGNED starts a new
# cycle; OFF_SHIFT ends the day). Non-standard transitions out of these
# are still ACCEPTED (forgiving mode) but tagged.
TERMINAL_STATES: Set[str] = {COMPLETE, OFF_SHIFT}

# Operational (in-flight) states that a driver can return to from
# WAITING / HOLD / BREAKDOWN.
OPERATIONAL_STATES: Set[str] = {
    ASSIGNED,
    ENROUTE_TO_LOAD,
    AT_LOAD_SITE,
    LOADING,
    LOADED,
    ENROUTE_TO_JOB,
    ARRIVED_JOB,
    DUMPING,
}

# ---------------------------------------------------------------------------
# Preferred transition graph (matches DISPATCH_LIFECYCLE_ARCHITECTURE.md)
# ---------------------------------------------------------------------------
#
# Forgiving mode: this graph defines STANDARD transitions only. Any
# transition NOT in this graph is still accepted and recorded, but the
# state-event row carries warning_tag="NON_STANDARD_TRANSITION" and the
# assignment's history entry is tagged standard=False. Governance work
# in iter395 can later surface repeated non-standard patterns.
#
# Notes:
#   • WAITING / HOLD / BREAKDOWN can be entered from any operational
#     state (these are pause states, not lifecycle progress).
#   • Returning from WAITING / HOLD / BREAKDOWN to ANY operational state
#     is STANDARD (we do not require remembering the prior state — the
#     embedded state_history[] already preserves it).
#   • OFF_SHIFT is reachable from any state (driver may end shift early
#     from BREAKDOWN, HOLD, etc.).
_PREFERRED: Dict[str, Set[str]] = {
    ASSIGNED:        {ENROUTE_TO_LOAD, WAITING, HOLD, BREAKDOWN, OFF_SHIFT},
    ENROUTE_TO_LOAD: {AT_LOAD_SITE, WAITING, HOLD, BREAKDOWN, OFF_SHIFT},
    AT_LOAD_SITE:    {LOADING, WAITING, HOLD, BREAKDOWN, OFF_SHIFT},
    LOADING:         {LOADED, WAITING, HOLD, BREAKDOWN, OFF_SHIFT},
    LOADED:          {ENROUTE_TO_JOB, WAITING, HOLD, BREAKDOWN, OFF_SHIFT},
    ENROUTE_TO_JOB:  {ARRIVED_JOB, WAITING, HOLD, BREAKDOWN, OFF_SHIFT},
    ARRIVED_JOB:     {DUMPING, WAITING, HOLD, OFF_SHIFT},
    DUMPING:         {COMPLETE, WAITING, HOLD, OFF_SHIFT},
    COMPLETE:        {OFF_SHIFT},          # terminal for the cycle
    WAITING:         OPERATIONAL_STATES | {HOLD, BREAKDOWN, OFF_SHIFT},
    HOLD:            OPERATIONAL_STATES | {WAITING, BREAKDOWN, OFF_SHIFT},
    BREAKDOWN:       OPERATIONAL_STATES | {WAITING, HOLD, OFF_SHIFT},
    OFF_SHIFT:       set(),                 # terminal for the day
}


def is_canonical_state(state: Optional[str]) -> bool:
    """Return True iff ``state`` is one of the 13 canonical states."""
    return isinstance(state, str) and state in CANONICAL_STATE_SET


def is_standard_transition(from_state: str, to_state: str) -> bool:
    """Return True iff ``from_state -> to_state`` is in the preferred graph.

    Non-canonical inputs always return False (will be tagged
    NON_STANDARD when persisted).
    """
    if not (is_canonical_state(from_state) and is_canonical_state(to_state)):
        return False
    return to_state in _PREFERRED.get(from_state, set())


def allowed_next_states(from_state: str) -> List[str]:
    """Return the sorted list of preferred next states from ``from_state``.

    Intended for the future driver mobile surface (iter393) — show only
    the standard next buttons. The backend API never restricts based on
    this list (forgiving mode).
    """
    return sorted(_PREFERRED.get(from_state, set()))


def is_terminal(state: str) -> bool:
    """Return True iff ``state`` ends the cycle (COMPLETE) or the day
    (OFF_SHIFT)."""
    return state in TERMINAL_STATES


def classify_transition(
    from_state: Optional[str],
    to_state: str,
) -> Dict[str, object]:
    """Classify a transition for persistence.

    Returns a dict with:
      • ``standard`` (bool)  — True iff in the preferred graph.
      • ``warning_tag`` (str|None) — "NON_STANDARD_TRANSITION" if not
        standard, else None.
      • ``to_state_canonical`` (bool) — True iff the destination is a
        canonical state. Non-canonical destinations are accepted but
        get an additional UNKNOWN_STATE tag for governance review.
    """
    to_canonical = is_canonical_state(to_state)
    standard = bool(from_state) and is_standard_transition(from_state or "", to_state)
    tags: List[str] = []
    if not standard:
        tags.append("NON_STANDARD_TRANSITION")
    if not to_canonical:
        tags.append("UNKNOWN_STATE")
    return {
        "standard": standard,
        "warning_tag": tags[0] if tags else None,
        "warning_tags": tags,
        "to_state_canonical": to_canonical,
    }


__all__ = [
    # state constants
    "ASSIGNED", "ENROUTE_TO_LOAD", "AT_LOAD_SITE", "LOADING", "LOADED",
    "ENROUTE_TO_JOB", "ARRIVED_JOB", "DUMPING", "COMPLETE",
    "WAITING", "HOLD", "BREAKDOWN", "OFF_SHIFT",
    # collections of states
    "CANONICAL_STATES", "CANONICAL_STATE_SET",
    "TERMINAL_STATES", "OPERATIONAL_STATES",
    # functions
    "is_canonical_state", "is_standard_transition",
    "allowed_next_states", "is_terminal", "classify_transition",
]

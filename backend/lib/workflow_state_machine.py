"""OMEGA · Phase 1A · Workflow state machine.

iter451 scope: OC-001 (Incident Lifecycle). Subsequent iterations
extend this module additively for the other 5 workflows.

Canonical lifecycle for incidents (operator directive iter451-455)::

    OPEN
      └─→ UNDER_INVESTIGATION
              └─→ CORRECTIVE_ACTION_REQUIRED
                      └─→ PENDING_CLOSURE
                              └─→ CLOSED
                                      ⤺ REOPEN → UNDER_INVESTIGATION

Closure gate (PENDING_CLOSURE → CLOSED):
  * Only Safety, Admin/Super-Admin actors may execute.
  * Attestation: investigation_complete, capa_complete, safety_review_complete.
  * OSHA-recordable incidents additionally require ``osha_recordable_ack=True``.

Reopen gate (CLOSED → UNDER_INVESTIGATION):
  * Safety / Admin / Super-Admin only.
  * Reason is mandatory (>= 5 chars after strip).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


# ── Canonical states ─────────────────────────────────────────────
INCIDENT_STATES: Tuple[str, ...] = (
    "OPEN",
    "UNDER_INVESTIGATION",
    "CORRECTIVE_ACTION_REQUIRED",
    "PENDING_CLOSURE",
    "CLOSED",
)

INCIDENT_DEFAULT_STATE = "OPEN"

# ── Allowed transitions ──────────────────────────────────────────
# from_state → set of legal to_states
INCIDENT_TRANSITIONS: Dict[str, List[str]] = {
    "OPEN":                       ["UNDER_INVESTIGATION"],
    "UNDER_INVESTIGATION":        ["CORRECTIVE_ACTION_REQUIRED", "PENDING_CLOSURE"],
    "CORRECTIVE_ACTION_REQUIRED": ["PENDING_CLOSURE"],
    "PENDING_CLOSURE":            ["CLOSED", "CORRECTIVE_ACTION_REQUIRED"],
    "CLOSED":                     ["UNDER_INVESTIGATION"],  # REOPEN
}

# ── Role-gate per transition ─────────────────────────────────────
# Actors are normalized to one of: 'safety', 'admin', 'super_admin',
# 'pm', 'public', 'unknown'.
INCIDENT_ALLOWED_ROLES: Dict[Tuple[str, str], frozenset] = {
    ("OPEN",                       "UNDER_INVESTIGATION"):        frozenset({"safety", "admin", "super_admin"}),
    ("UNDER_INVESTIGATION",        "CORRECTIVE_ACTION_REQUIRED"): frozenset({"safety", "admin", "super_admin"}),
    ("UNDER_INVESTIGATION",        "PENDING_CLOSURE"):            frozenset({"safety", "admin", "super_admin"}),
    ("CORRECTIVE_ACTION_REQUIRED", "PENDING_CLOSURE"):            frozenset({"safety", "admin", "super_admin"}),
    ("PENDING_CLOSURE",            "CORRECTIVE_ACTION_REQUIRED"): frozenset({"safety", "admin", "super_admin"}),
    ("PENDING_CLOSURE",            "CLOSED"):                     frozenset({"safety", "admin", "super_admin"}),
    ("CLOSED",                     "UNDER_INVESTIGATION"):        frozenset({"safety", "admin", "super_admin"}),
}


def normalize_actor_role(actor: Any) -> str:
    """Project the heterogeneous actor shape onto the canonical role
    vocabulary used by the transition gate."""
    if actor is True:
        # Admin token bypass — super_admin equivalent.
        return "super_admin"
    if isinstance(actor, dict):
        if actor.get("is_super_admin") is True:
            return "super_admin"
        kind = actor.get("_actor_kind")
        if kind == "safety_user":
            return "safety"
        ka = actor.get("_actor") or actor.get("role")
        if ka:
            k = str(ka).lower()
            if k in ("admin", "super_admin"):
                return "super_admin"
            if k == "safety":
                return "safety"
            if k == "pm":
                return "pm"
            if k == "operations_director":
                return "super_admin"
    return "unknown"


def coerce_incident_state(raw: Optional[str]) -> str:
    """Backfill helper — any missing / unrecognised lifecycle_state on
    an existing incident row is treated as ``OPEN`` so the read-shim
    never returns ``None`` to consumers."""
    if not raw:
        return INCIDENT_DEFAULT_STATE
    s = str(raw).strip().upper()
    return s if s in INCIDENT_STATES else INCIDENT_DEFAULT_STATE


def validate_incident_transition(
    *,
    from_state: str,
    to_state: str,
    actor: Any,
    reason: str = "",
    evidence: Optional[Dict[str, Any]] = None,
    osha_recordable: bool = False,
) -> Tuple[bool, str]:
    """Return (ok, error_code). Error codes are stable strings the
    route layer maps to 4xx responses."""
    if from_state not in INCIDENT_STATES:
        return False, "invalid_from_state"
    if to_state not in INCIDENT_STATES:
        return False, "invalid_to_state"
    if to_state not in INCIDENT_TRANSITIONS.get(from_state, []):
        return False, "transition_not_allowed"

    role = normalize_actor_role(actor)
    if role not in INCIDENT_ALLOWED_ROLES.get((from_state, to_state), frozenset()):
        return False, "role_not_authorized"

    # Reopen — reason mandatory.
    if from_state == "CLOSED" and to_state == "UNDER_INVESTIGATION":
        if not reason or len(reason.strip()) < 5:
            return False, "reopen_reason_required"

    # Closure attestation — investigation + CAPA + safety review.
    if to_state == "CLOSED":
        ev = evidence or {}
        for flag in ("investigation_complete", "capa_complete", "safety_review_complete"):
            if not bool(ev.get(flag)):
                return False, f"closure_attestation_missing:{flag}"
        # OSHA-recordable incidents — explicit acknowledgement gate.
        if osha_recordable and not bool(ev.get("osha_recordable_ack")):
            return False, "closure_attestation_missing:osha_recordable_ack"
        # Closure role narrows to Safety / Super-Admin (Operations Director
        # is mapped to super_admin by ``normalize_actor_role``).
        if role not in {"safety", "super_admin"}:
            return False, "closure_role_not_authorized"

    return True, ""


__all__ = [
    "INCIDENT_STATES",
    "INCIDENT_DEFAULT_STATE",
    "INCIDENT_TRANSITIONS",
    "INCIDENT_ALLOWED_ROLES",
    "normalize_actor_role",
    "coerce_incident_state",
    "validate_incident_transition",
]

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
        if kind == "hr_user":
            return "hr"
        if kind == "pm_user":
            return "pm"
        ka = actor.get("_actor") or actor.get("role")
        if ka:
            k = str(ka).lower()
            if k in ("admin", "super_admin"):
                return "super_admin"
            if k == "safety":
                return "safety"
            if k == "hr":
                return "hr"
            if k == "pm":
                return "pm"
            if k == "operations_director":
                return "super_admin"
        # PM dict (compute_pm_scope returns the PM doc as-is)
        if actor.get("project_numbers") is not None or "pm_email" in actor:
            return "pm"
        # HR user dict
        if "hr_user_id" in actor or actor.get("hr") is True:
            return "hr"
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
    # OC-002 Daily Report Office Review
    "DAILY_REPORT_STATES",
    "DAILY_REPORT_DEFAULT_STATE",
    "DAILY_REPORT_TRANSITIONS",
    "coerce_daily_report_state",
    "validate_daily_report_transition",
    # OC-007 Payroll Variance Finalization
    "PAYROLL_VARIANCE_STATES",
    "PAYROLL_VARIANCE_DEFAULT_STATE",
    "PAYROLL_VARIANCE_TRANSITIONS",
    "coerce_payroll_variance_state",
    "validate_payroll_variance_transition",
    # OC-003 QA/QC Deficiency Follow-Up (iter453)
    "QAQC_STATES",
    "QAQC_DEFAULT_STATE",
    "QAQC_TRANSITIONS",
    "coerce_qaqc_state",
    "validate_qaqc_transition",
    # OC-004 Site Inspection Finding Follow-Up (iter453)
    "SITE_INSPECTION_STATES",
    "SITE_INSPECTION_DEFAULT_STATE",
    "SITE_INSPECTION_TRANSITIONS",
    "coerce_site_inspection_state",
    "validate_site_inspection_transition",
]


# ════════════════════════════════════════════════════════════════
# OC-002 · Daily Report Office Review
# ════════════════════════════════════════════════════════════════
#
# Operator directive (iter452):
#   States:  OPEN → PENDING_REVIEW → REVIEWED → CLOSED
#   Notifications on PENDING_REVIEW: PM, Superintendent
#   Office review must be auditable. No silent completion.
#
# Allowed transitions:
#   OPEN              → PENDING_REVIEW                 (PM/Foreman submits for review)
#   PENDING_REVIEW    → OPEN                           (kick back to field — needs more info)
#   PENDING_REVIEW    → REVIEWED                       (Office signs off)
#   REVIEWED          → CLOSED                         (final close-out attestation)
#   CLOSED            → PENDING_REVIEW                 (REOPEN — reason required)
#
# Roles:
#   OPEN              → PENDING_REVIEW   : pm | admin | super_admin
#   PENDING_REVIEW    → OPEN             : admin | super_admin             (office returns to field)
#   PENDING_REVIEW    → REVIEWED         : admin | super_admin             (office sign-off)
#   REVIEWED          → CLOSED           : admin | super_admin             (final close)
#   CLOSED            → PENDING_REVIEW   : admin | super_admin             (reopen)
#
# Closure attestation (REVIEWED → CLOSED):
#   * office_review_complete = True
#   * payroll_inputs_verified = True   (DR feeds payroll variance — must be checked)
#
DAILY_REPORT_STATES: Tuple[str, ...] = (
    "OPEN", "PENDING_REVIEW", "REVIEWED", "CLOSED",
)
DAILY_REPORT_DEFAULT_STATE = "OPEN"

DAILY_REPORT_TRANSITIONS: Dict[str, List[str]] = {
    "OPEN":           ["PENDING_REVIEW"],
    "PENDING_REVIEW": ["OPEN", "REVIEWED"],
    "REVIEWED":       ["CLOSED"],
    "CLOSED":         ["PENDING_REVIEW"],
}

_DR_ROLES: Dict[Tuple[str, str], frozenset] = {
    ("OPEN",           "PENDING_REVIEW"): frozenset({"pm", "admin", "super_admin"}),
    ("PENDING_REVIEW", "OPEN"):           frozenset({"admin", "super_admin"}),
    ("PENDING_REVIEW", "REVIEWED"):       frozenset({"admin", "super_admin"}),
    ("REVIEWED",       "CLOSED"):         frozenset({"admin", "super_admin"}),
    ("CLOSED",         "PENDING_REVIEW"): frozenset({"admin", "super_admin"}),
}


def coerce_daily_report_state(raw: Optional[str]) -> str:
    if not raw:
        return DAILY_REPORT_DEFAULT_STATE
    s = str(raw).strip().upper()
    return s if s in DAILY_REPORT_STATES else DAILY_REPORT_DEFAULT_STATE


def validate_daily_report_transition(
    *,
    from_state: str,
    to_state: str,
    actor: Any,
    reason: str = "",
    evidence: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    if from_state not in DAILY_REPORT_STATES:
        return False, "invalid_from_state"
    if to_state not in DAILY_REPORT_STATES:
        return False, "invalid_to_state"
    if to_state not in DAILY_REPORT_TRANSITIONS.get(from_state, []):
        return False, "transition_not_allowed"

    role = normalize_actor_role(actor)
    if role not in _DR_ROLES.get((from_state, to_state), frozenset()):
        return False, "role_not_authorized"

    # Reopen requires a written reason.
    if from_state == "CLOSED" and to_state == "PENDING_REVIEW":
        if not reason or len(reason.strip()) < 5:
            return False, "reopen_reason_required"

    # Return-to-field also requires a reason (so the foreman knows why).
    if from_state == "PENDING_REVIEW" and to_state == "OPEN":
        if not reason or len(reason.strip()) < 5:
            return False, "return_to_field_reason_required"

    # Final closure attestation.
    if to_state == "CLOSED":
        ev = evidence or {}
        for flag in ("office_review_complete", "payroll_inputs_verified"):
            if not bool(ev.get(flag)):
                return False, f"closure_attestation_missing:{flag}"

    return True, ""


# ════════════════════════════════════════════════════════════════
# OC-007 · Payroll Variance Finalization
# ════════════════════════════════════════════════════════════════
#
# Operator directive (iter452):
#   Build explicit finalization workflow. NO AUTO FINALIZE.
#   Required: Review, Approve, Finalize, Audit.
#   Track: who, when, why. No payroll batch can silently complete.
#
# State graph:
#   OPEN → UNDER_REVIEW → APPROVED → FINALIZED
#   Reopen: FINALIZED → UNDER_REVIEW (reason required)
#   Back-step: APPROVED → UNDER_REVIEW (reason required — caught an issue)
#
# Roles:
#   OPEN          → UNDER_REVIEW : hr | admin | super_admin
#   UNDER_REVIEW  → APPROVED     : hr | admin | super_admin
#   APPROVED      → UNDER_REVIEW : admin | super_admin
#   APPROVED      → FINALIZED    : admin | super_admin                (Finalize gate)
#   FINALIZED     → UNDER_REVIEW : admin | super_admin                (Reopen)
#
# Finalize attestation (APPROVED → FINALIZED):
#   * review_complete            = True
#   * approval_complete          = True
#   * variance_decisions_complete = True   (every flagged row must have a decision)
#
PAYROLL_VARIANCE_STATES: Tuple[str, ...] = (
    "OPEN", "UNDER_REVIEW", "APPROVED", "FINALIZED",
)
PAYROLL_VARIANCE_DEFAULT_STATE = "OPEN"

PAYROLL_VARIANCE_TRANSITIONS: Dict[str, List[str]] = {
    "OPEN":         ["UNDER_REVIEW"],
    "UNDER_REVIEW": ["APPROVED"],
    "APPROVED":     ["UNDER_REVIEW", "FINALIZED"],
    "FINALIZED":    ["UNDER_REVIEW"],
}

_PV_ROLES: Dict[Tuple[str, str], frozenset] = {
    ("OPEN",         "UNDER_REVIEW"): frozenset({"hr", "admin", "super_admin"}),
    ("UNDER_REVIEW", "APPROVED"):     frozenset({"hr", "admin", "super_admin"}),
    ("APPROVED",     "UNDER_REVIEW"): frozenset({"admin", "super_admin"}),
    ("APPROVED",     "FINALIZED"):    frozenset({"admin", "super_admin"}),
    ("FINALIZED",    "UNDER_REVIEW"): frozenset({"admin", "super_admin"}),
}


def coerce_payroll_variance_state(raw: Optional[str]) -> str:
    if not raw:
        return PAYROLL_VARIANCE_DEFAULT_STATE
    s = str(raw).strip().upper()
    return s if s in PAYROLL_VARIANCE_STATES else PAYROLL_VARIANCE_DEFAULT_STATE


def validate_payroll_variance_transition(
    *,
    from_state: str,
    to_state: str,
    actor: Any,
    reason: str = "",
    evidence: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    if from_state not in PAYROLL_VARIANCE_STATES:
        return False, "invalid_from_state"
    if to_state not in PAYROLL_VARIANCE_STATES:
        return False, "invalid_to_state"
    if to_state not in PAYROLL_VARIANCE_TRANSITIONS.get(from_state, []):
        return False, "transition_not_allowed"

    role = normalize_actor_role(actor)
    if role not in _PV_ROLES.get((from_state, to_state), frozenset()):
        return False, "role_not_authorized"

    # Reopen + back-step require reason.
    if from_state == "FINALIZED" and to_state == "UNDER_REVIEW":
        if not reason or len(reason.strip()) < 5:
            return False, "reopen_reason_required"
    if from_state == "APPROVED" and to_state == "UNDER_REVIEW":
        if not reason or len(reason.strip()) < 5:
            return False, "back_step_reason_required"

    # Finalize attestation — explicit, NO AUTO FINALIZE.
    if to_state == "FINALIZED":
        ev = evidence or {}
        for flag in ("review_complete", "approval_complete", "variance_decisions_complete"):
            if not bool(ev.get(flag)):
                return False, f"finalize_attestation_missing:{flag}"

    return True, ""



# ════════════════════════════════════════════════════════════════
# OC-003 · QA/QC Deficiency Follow-Up (iter453)
# ════════════════════════════════════════════════════════════════
#
# Constitutional Build Package (Phase 3 · 2026-06-02):
#   States:  OPEN → DEFICIENCY_RAISED → IN_REMEDIATION → PENDING_RE_INSPECTION → CLOSED
#   Reopen:  CLOSED → DEFICIENCY_RAISED (reason required >= 5 chars)
#   Rework:  PENDING_RE_INSPECTION → DEFICIENCY_RAISED (re-inspection failed)
#
# Closure-action contract (Amendment 001 REPLACE-5 binding):
#   CLOSED only when ONE of:
#     a) re_inspection_passed = True with re_inspection_record_id linkage
#     b) corrective_action_completed = True with corrective_action_notes >= 20 chars
#     c) exception_approved = True with exception_reason AND dual sign-off
#        (pm_signoff_user_id AND safety_signoff_user_id distinct + present)
#   "Mark Resolved" / "Acknowledge findings" ack-only closure is FORBIDDEN.
#
# Role gates:
#   OPEN                  → DEFICIENCY_RAISED       : pm | safety | admin | super_admin
#   DEFICIENCY_RAISED     → IN_REMEDIATION          : pm | admin | super_admin
#   IN_REMEDIATION        → PENDING_RE_INSPECTION   : pm | admin | super_admin
#   PENDING_RE_INSPECTION → CLOSED                  : pm | safety | admin | super_admin
#   PENDING_RE_INSPECTION → DEFICIENCY_RAISED       : pm | safety | admin | super_admin (rework)
#   CLOSED                → DEFICIENCY_RAISED       : safety | admin | super_admin (reopen)
#
QAQC_STATES: Tuple[str, ...] = (
    "OPEN",
    "DEFICIENCY_RAISED",
    "IN_REMEDIATION",
    "PENDING_RE_INSPECTION",
    "CLOSED",
)
QAQC_DEFAULT_STATE = "OPEN"

QAQC_TRANSITIONS: Dict[str, List[str]] = {
    "OPEN":                  ["DEFICIENCY_RAISED"],
    "DEFICIENCY_RAISED":     ["IN_REMEDIATION"],
    "IN_REMEDIATION":        ["PENDING_RE_INSPECTION"],
    "PENDING_RE_INSPECTION": ["CLOSED", "DEFICIENCY_RAISED"],
    "CLOSED":                ["DEFICIENCY_RAISED"],
}

_QAQC_ROLES: Dict[Tuple[str, str], frozenset] = {
    ("OPEN",                  "DEFICIENCY_RAISED"):     frozenset({"pm", "safety", "admin", "super_admin"}),
    ("DEFICIENCY_RAISED",     "IN_REMEDIATION"):        frozenset({"pm", "admin", "super_admin"}),
    ("IN_REMEDIATION",        "PENDING_RE_INSPECTION"): frozenset({"pm", "admin", "super_admin"}),
    ("PENDING_RE_INSPECTION", "CLOSED"):                frozenset({"pm", "safety", "admin", "super_admin"}),
    ("PENDING_RE_INSPECTION", "DEFICIENCY_RAISED"):     frozenset({"pm", "safety", "admin", "super_admin"}),
    ("CLOSED",                "DEFICIENCY_RAISED"):     frozenset({"safety", "admin", "super_admin"}),
}


def coerce_qaqc_state(raw: Optional[str]) -> str:
    if not raw:
        return QAQC_DEFAULT_STATE
    s = str(raw).strip().upper()
    return s if s in QAQC_STATES else QAQC_DEFAULT_STATE


def _qaqc_closure_evidence_ok(ev: Dict[str, Any]) -> Tuple[bool, str]:
    """Amendment 001 REPLACE-5 binding: closure requires operational
    action — re-inspection OR corrective_action complete OR documented
    exception with dual sign-off. Returns (ok, err_code)."""
    # Path A · re-inspection passed
    if bool(ev.get("re_inspection_passed")):
        if not str(ev.get("re_inspection_record_id") or "").strip():
            return False, "closure_evidence_missing:re_inspection_record_id"
        return True, ""
    # Path B · corrective_action completed
    if bool(ev.get("corrective_action_completed")):
        notes = str(ev.get("corrective_action_notes") or "").strip()
        if len(notes) < 20:
            return False, "closure_evidence_missing:corrective_action_notes_min20"
        return True, ""
    # Path C · documented exception with dual sign-off
    if bool(ev.get("exception_approved")):
        reason = str(ev.get("exception_reason") or "").strip()
        pm_id = str(ev.get("pm_signoff_user_id") or "").strip()
        sf_id = str(ev.get("safety_signoff_user_id") or "").strip()
        if len(reason) < 10:
            return False, "closure_evidence_missing:exception_reason_min10"
        if not pm_id or not sf_id:
            return False, "closure_evidence_missing:dual_signoff"
        if pm_id == sf_id:
            return False, "closure_evidence_missing:dual_signoff_distinct"
        return True, ""
    return False, "closure_evidence_missing:operational_action_required"


def validate_qaqc_transition(
    *,
    from_state: str,
    to_state: str,
    actor: Any,
    reason: str = "",
    evidence: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    if from_state not in QAQC_STATES:
        return False, "invalid_from_state"
    if to_state not in QAQC_STATES:
        return False, "invalid_to_state"
    if to_state not in QAQC_TRANSITIONS.get(from_state, []):
        return False, "transition_not_allowed"

    role = normalize_actor_role(actor)
    if role not in _QAQC_ROLES.get((from_state, to_state), frozenset()):
        return False, "role_not_authorized"

    # Reopen requires reason.
    if from_state == "CLOSED" and to_state == "DEFICIENCY_RAISED":
        if not reason or len(reason.strip()) < 5:
            return False, "reopen_reason_required"

    # Rework loop requires reason (so PM/Inspector know what failed).
    if from_state == "PENDING_RE_INSPECTION" and to_state == "DEFICIENCY_RAISED":
        if not reason or len(reason.strip()) < 5:
            return False, "rework_reason_required"

    # Closure-action contract (Amendment 001 REPLACE-5).
    if to_state == "CLOSED":
        ok, err = _qaqc_closure_evidence_ok(evidence or {})
        if not ok:
            return False, err

    return True, ""


# ════════════════════════════════════════════════════════════════
# OC-004 · Site Inspection Finding Follow-Up (iter453)
# ════════════════════════════════════════════════════════════════
#
# Constitutional Build Package (Phase 3 · 2026-06-02):
#   Structurally symmetric to OC-003 with finding terminology.
#   States:  OPEN → FINDINGS_RAISED → IN_REMEDIATION → PENDING_RE_INSPECTION → CLOSED
#
# Closure-action contract (Amendment 001 REPLACE-4 binding):
#   Same 3 paths as OC-003 — re-inspection OR corrective_action OR documented exception.
#   "Acknowledge findings" ack-only closure is FORBIDDEN.
#
SITE_INSPECTION_STATES: Tuple[str, ...] = (
    "OPEN",
    "FINDINGS_RAISED",
    "IN_REMEDIATION",
    "PENDING_RE_INSPECTION",
    "CLOSED",
)
SITE_INSPECTION_DEFAULT_STATE = "OPEN"

SITE_INSPECTION_TRANSITIONS: Dict[str, List[str]] = {
    "OPEN":                  ["FINDINGS_RAISED"],
    "FINDINGS_RAISED":       ["IN_REMEDIATION"],
    "IN_REMEDIATION":        ["PENDING_RE_INSPECTION"],
    "PENDING_RE_INSPECTION": ["CLOSED", "FINDINGS_RAISED"],
    "CLOSED":                ["FINDINGS_RAISED"],
}

_SI_ROLES: Dict[Tuple[str, str], frozenset] = {
    ("OPEN",                  "FINDINGS_RAISED"):       frozenset({"pm", "safety", "admin", "super_admin"}),
    ("FINDINGS_RAISED",       "IN_REMEDIATION"):        frozenset({"pm", "admin", "super_admin"}),
    ("IN_REMEDIATION",        "PENDING_RE_INSPECTION"): frozenset({"pm", "admin", "super_admin"}),
    ("PENDING_RE_INSPECTION", "CLOSED"):                frozenset({"pm", "safety", "admin", "super_admin"}),
    ("PENDING_RE_INSPECTION", "FINDINGS_RAISED"):       frozenset({"pm", "safety", "admin", "super_admin"}),
    ("CLOSED",                "FINDINGS_RAISED"):       frozenset({"safety", "admin", "super_admin"}),
}


def coerce_site_inspection_state(raw: Optional[str]) -> str:
    if not raw:
        return SITE_INSPECTION_DEFAULT_STATE
    s = str(raw).strip().upper()
    return s if s in SITE_INSPECTION_STATES else SITE_INSPECTION_DEFAULT_STATE


def validate_site_inspection_transition(
    *,
    from_state: str,
    to_state: str,
    actor: Any,
    reason: str = "",
    evidence: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    if from_state not in SITE_INSPECTION_STATES:
        return False, "invalid_from_state"
    if to_state not in SITE_INSPECTION_STATES:
        return False, "invalid_to_state"
    if to_state not in SITE_INSPECTION_TRANSITIONS.get(from_state, []):
        return False, "transition_not_allowed"

    role = normalize_actor_role(actor)
    if role not in _SI_ROLES.get((from_state, to_state), frozenset()):
        return False, "role_not_authorized"

    if from_state == "CLOSED" and to_state == "FINDINGS_RAISED":
        if not reason or len(reason.strip()) < 5:
            return False, "reopen_reason_required"

    if from_state == "PENDING_RE_INSPECTION" and to_state == "FINDINGS_RAISED":
        if not reason or len(reason.strip()) < 5:
            return False, "rework_reason_required"

    # Closure-action contract (Amendment 001 REPLACE-4).
    # Identical 3-path contract as OC-003.
    if to_state == "CLOSED":
        ok, err = _qaqc_closure_evidence_ok(evidence or {})
        if not ok:
            return False, err

    return True, ""

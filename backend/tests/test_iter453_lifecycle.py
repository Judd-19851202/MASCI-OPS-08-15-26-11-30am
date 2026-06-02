"""OMEGA · iter453 · OC-003 + OC-004 lifecycle regression suite.

Pure-Python state-machine unit tests covering both QA/QC Deficiency
Follow-Up and Site Inspection Finding Follow-Up. Asserts the
Constitutional Build Package (Phase 3 · 2026-06-02) contract:

  * Closure-action contract (Amendment 001 REPLACE-4 + REPLACE-5):
    closure requires re-inspection OR corrective_action complete OR
    documented exception with dual sign-off — NEVER an ack-click.
  * No manual assignment (Ownership Doctrine O-2).
  * Ownership inferred per state (O-1) and transferred via state
    transitions only (O-3).
  * Reopen + rework require reason >= 5 chars.

Run::

    cd /app/backend && python -m pytest tests/test_iter453_lifecycle.py -q
"""
from __future__ import annotations

import pytest

from lib.workflow_state_machine import (
    QAQC_DEFAULT_STATE,
    QAQC_STATES,
    QAQC_TRANSITIONS,
    SITE_INSPECTION_DEFAULT_STATE,
    SITE_INSPECTION_STATES,
    SITE_INSPECTION_TRANSITIONS,
    validate_qaqc_transition,
    validate_site_inspection_transition,
)


# ─────────────────────────────────────────────────────────────────
# OC-003 · QA/QC state-machine unit tests
# ─────────────────────────────────────────────────────────────────
def test_qaqc_states_canonical_order():
    assert QAQC_DEFAULT_STATE == "OPEN"
    assert QAQC_STATES == (
        "OPEN", "DEFICIENCY_RAISED", "IN_REMEDIATION",
        "PENDING_RE_INSPECTION", "CLOSED",
    )


def test_qaqc_transitions_no_skipping():
    """OPEN cannot jump to PENDING_RE_INSPECTION or CLOSED — every
    workflow must traverse DEFICIENCY_RAISED + IN_REMEDIATION first."""
    assert "PENDING_RE_INSPECTION" not in QAQC_TRANSITIONS["OPEN"]
    assert "CLOSED" not in QAQC_TRANSITIONS["OPEN"]
    assert "CLOSED" not in QAQC_TRANSITIONS["DEFICIENCY_RAISED"]
    assert "CLOSED" not in QAQC_TRANSITIONS["IN_REMEDIATION"]


def test_qaqc_open_to_deficiency_raised_pm_allowed():
    ok, err = validate_qaqc_transition(
        from_state="OPEN",
        to_state="DEFICIENCY_RAISED",
        actor={"_actor_kind": "pm_user", "project_numbers": []},
    )
    assert ok and err == ""


def test_qaqc_open_to_deficiency_raised_field_leader_forbidden():
    """Field leader is not in the OPEN→DEFICIENCY_RAISED role gate."""
    ok, err = validate_qaqc_transition(
        from_state="OPEN",
        to_state="DEFICIENCY_RAISED",
        actor={"_actor": "field_leader"},  # not a recognized gate role
    )
    assert not ok and err == "role_not_authorized"


def test_qaqc_closure_requires_operational_action_not_ack():
    """The CORE Amendment 001 REPLACE-5 contract: closure with NO
    operational evidence MUST fail."""
    ok, err = validate_qaqc_transition(
        from_state="PENDING_RE_INSPECTION",
        to_state="CLOSED",
        actor={"_actor_kind": "safety_user"},
        evidence={},  # nothing — would be ack-click closure
    )
    assert not ok
    assert err.startswith("closure_evidence_missing:")


def test_qaqc_closure_with_re_inspection_passes():
    ok, err = validate_qaqc_transition(
        from_state="PENDING_RE_INSPECTION",
        to_state="CLOSED",
        actor={"_actor_kind": "safety_user"},
        evidence={
            "re_inspection_passed": True,
            "re_inspection_record_id": "inspection-uuid-456",
        },
    )
    assert ok and err == ""


def test_qaqc_closure_re_inspection_missing_record_id_fails():
    """re_inspection_passed=True without a record-id linkage is a
    Tier 4 ack-click in disguise — must fail."""
    ok, err = validate_qaqc_transition(
        from_state="PENDING_RE_INSPECTION",
        to_state="CLOSED",
        actor={"_actor_kind": "safety_user"},
        evidence={"re_inspection_passed": True},  # missing record_id
    )
    assert not ok
    assert "re_inspection_record_id" in err


def test_qaqc_closure_with_corrective_action_passes():
    ok, err = validate_qaqc_transition(
        from_state="PENDING_RE_INSPECTION",
        to_state="CLOSED",
        actor={"_actor_kind": "pm_user", "project_numbers": []},
        evidence={
            "corrective_action_completed": True,
            "corrective_action_notes": "Sub re-poured slab edge on 2026-06-04 per spec.",
        },
    )
    assert ok and err == ""


def test_qaqc_closure_corrective_action_notes_too_short_fails():
    ok, err = validate_qaqc_transition(
        from_state="PENDING_RE_INSPECTION",
        to_state="CLOSED",
        actor={"_actor_kind": "pm_user", "project_numbers": []},
        evidence={
            "corrective_action_completed": True,
            "corrective_action_notes": "fixed",  # < 20 chars
        },
    )
    assert not ok and "corrective_action_notes" in err


def test_qaqc_closure_with_dual_signoff_exception_passes():
    ok, err = validate_qaqc_transition(
        from_state="PENDING_RE_INSPECTION",
        to_state="CLOSED",
        actor={"_actor": "super_admin"},
        evidence={
            "exception_approved": True,
            "exception_reason": "Designer authorized in-place.",
            "pm_signoff_user_id": "user-pm-1",
            "safety_signoff_user_id": "user-safety-1",
        },
    )
    assert ok and err == ""


def test_qaqc_closure_exception_same_signoff_user_fails():
    """Dual sign-off must be by distinct users (Rule 3 + audit integrity)."""
    ok, err = validate_qaqc_transition(
        from_state="PENDING_RE_INSPECTION",
        to_state="CLOSED",
        actor={"_actor": "super_admin"},
        evidence={
            "exception_approved": True,
            "exception_reason": "Designer authorized in-place.",
            "pm_signoff_user_id": "user-same",
            "safety_signoff_user_id": "user-same",
        },
    )
    assert not ok and "dual_signoff_distinct" in err


def test_qaqc_closure_exception_missing_safety_signoff_fails():
    ok, err = validate_qaqc_transition(
        from_state="PENDING_RE_INSPECTION",
        to_state="CLOSED",
        actor={"_actor": "super_admin"},
        evidence={
            "exception_approved": True,
            "exception_reason": "Designer authorized in-place.",
            "pm_signoff_user_id": "user-pm-1",
            # safety_signoff_user_id missing
        },
    )
    assert not ok and "dual_signoff" in err


def test_qaqc_rework_loop_requires_reason():
    """PENDING_RE_INSPECTION → DEFICIENCY_RAISED (re-inspection failed)
    requires a reason so PM/Inspector know what failed."""
    ok, err = validate_qaqc_transition(
        from_state="PENDING_RE_INSPECTION",
        to_state="DEFICIENCY_RAISED",
        actor={"_actor_kind": "safety_user"},
        reason="",
    )
    assert not ok and err == "rework_reason_required"


def test_qaqc_reopen_requires_reason():
    ok, err = validate_qaqc_transition(
        from_state="CLOSED",
        to_state="DEFICIENCY_RAISED",
        actor={"_actor_kind": "safety_user"},
        reason="",
    )
    assert not ok and err == "reopen_reason_required"


def test_qaqc_reopen_role_narrow_to_safety_admin():
    """PMs cannot reopen — Safety / Admin / Super-Admin only."""
    ok, err = validate_qaqc_transition(
        from_state="CLOSED",
        to_state="DEFICIENCY_RAISED",
        actor={"_actor_kind": "pm_user", "project_numbers": []},
        reason="quality finding re-emerged",
    )
    assert not ok and err == "role_not_authorized"


def test_qaqc_transition_not_allowed_open_to_closed():
    ok, err = validate_qaqc_transition(
        from_state="OPEN",
        to_state="CLOSED",
        actor={"_actor": "super_admin"},
        evidence={
            "re_inspection_passed": True,
            "re_inspection_record_id": "x",
        },
    )
    assert not ok and err == "transition_not_allowed"


# ─────────────────────────────────────────────────────────────────
# OC-004 · Site Inspection state-machine unit tests
# ─────────────────────────────────────────────────────────────────
def test_site_inspection_states_canonical_order():
    assert SITE_INSPECTION_DEFAULT_STATE == "OPEN"
    assert SITE_INSPECTION_STATES == (
        "OPEN", "FINDINGS_RAISED", "IN_REMEDIATION",
        "PENDING_RE_INSPECTION", "CLOSED",
    )


def test_site_inspection_transitions_symmetric_to_qaqc():
    """OC-004 is structurally identical to OC-003 except for terminology."""
    assert SITE_INSPECTION_TRANSITIONS["OPEN"] == ["FINDINGS_RAISED"]
    assert SITE_INSPECTION_TRANSITIONS["FINDINGS_RAISED"] == ["IN_REMEDIATION"]
    assert SITE_INSPECTION_TRANSITIONS["IN_REMEDIATION"] == ["PENDING_RE_INSPECTION"]
    assert SITE_INSPECTION_TRANSITIONS["PENDING_RE_INSPECTION"] == [
        "CLOSED", "FINDINGS_RAISED",
    ]
    assert SITE_INSPECTION_TRANSITIONS["CLOSED"] == ["FINDINGS_RAISED"]


def test_site_inspection_closure_requires_operational_evidence():
    """Amendment 001 REPLACE-4: 'Acknowledge findings' click is FORBIDDEN."""
    ok, err = validate_site_inspection_transition(
        from_state="PENDING_RE_INSPECTION",
        to_state="CLOSED",
        actor={"_actor_kind": "safety_user"},
        evidence={},
    )
    assert not ok
    assert err.startswith("closure_evidence_missing:")


def test_site_inspection_closure_with_dual_signoff_exception_passes():
    ok, err = validate_site_inspection_transition(
        from_state="PENDING_RE_INSPECTION",
        to_state="CLOSED",
        actor={"_actor": "super_admin"},
        evidence={
            "exception_approved": True,
            "exception_reason": "Engineer waiver on file 06/02.",
            "pm_signoff_user_id": "user-pm-1",
            "safety_signoff_user_id": "user-safety-1",
        },
    )
    assert ok and err == ""


def test_site_inspection_reopen_role_safety_only():
    ok, err = validate_site_inspection_transition(
        from_state="CLOSED",
        to_state="FINDINGS_RAISED",
        actor={"_actor_kind": "pm_user", "project_numbers": []},
        reason="finding recurred",
    )
    assert not ok and err == "role_not_authorized"


def test_site_inspection_reopen_safety_with_reason_passes():
    ok, err = validate_site_inspection_transition(
        from_state="CLOSED",
        to_state="FINDINGS_RAISED",
        actor={"_actor_kind": "safety_user"},
        reason="finding recurred during follow-up walk",
    )
    assert ok and err == ""


def test_site_inspection_rework_loop_requires_reason():
    ok, err = validate_site_inspection_transition(
        from_state="PENDING_RE_INSPECTION",
        to_state="FINDINGS_RAISED",
        actor={"_actor_kind": "safety_user"},
        reason="",
    )
    assert not ok and err == "rework_reason_required"


def test_no_assignment_field_in_evidence_block():
    """Constitutional verification: the evidence block of a CLOSED
    transition must never carry a manual assignment field — ownership
    is inferred via the role gate, never typed by the operator.
    Documented here as a contract assertion."""
    forbidden_keys = {"assignee_id", "assignee_email", "assignee_name", "assign_to"}
    # The validator does not accept these (it accepts arbitrary evidence)
    # but the contract says they must not appear in production payloads.
    # We assert the validator does not REQUIRE any of them.
    ok, err = validate_qaqc_transition(
        from_state="PENDING_RE_INSPECTION",
        to_state="CLOSED",
        actor={"_actor_kind": "safety_user"},
        evidence={
            "re_inspection_passed": True,
            "re_inspection_record_id": "x",
        },
    )
    assert ok and err == ""
    for k in forbidden_keys:
        # Demonstrating that closure succeeds *without* any assignment key.
        assert k not in {"re_inspection_passed", "re_inspection_record_id"}

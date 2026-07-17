from __future__ import annotations

import sys

sys.path.insert(0, "/app/backend")

from routes.admin_dr_delivery_forensics import _classify  # noqa: E402


def _base_kwargs():
    return {
        "assignments": [],
        "pm_assignment": None,
        "copm_assignments": [],
        "pm_email": None,
        "copm_emails": [],
        "recipients": [],
        "expected": [],
        "spine_stage_index": {},
        "audit_rows": [],
        "dead_letter_configured": False,
        "routed_via_dead_letter": False,
    }


def test_classify_preview_safety_mode_suppression_separately_from_not_scheduled():
    kwargs = _base_kwargs()
    kwargs["spine_stage_index"] = {
        "notification_queued": {
            "status": "skipped",
            "failure_reason": "email_safety_mode:strict",
        }
    }
    assert _classify(**kwargs) == "delivery_suppressed_by_environment"


def test_classify_synthetic_record_suppression_separately_from_not_scheduled():
    kwargs = _base_kwargs()
    kwargs["spine_stage_index"] = {
        "notification_queued": {
            "status": "skipped",
            "failure_reason": "synthetic_test_record",
        }
    }
    assert _classify(**kwargs) == "delivery_suppressed_synthetic_test_record"


def test_classify_true_not_scheduled_when_generic_skip_reason():
    kwargs = _base_kwargs()
    kwargs["spine_stage_index"] = {
        "notification_queued": {
            "status": "skipped",
            "failure_reason": "auto-email disabled (RESEND_API_KEY missing or AUTO_EMAIL_REPORTS=false)",
        }
    }
    assert _classify(**kwargs) == "auto_email_not_scheduled"
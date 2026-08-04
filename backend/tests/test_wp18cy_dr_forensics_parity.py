from __future__ import annotations

import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


from routes.admin_dr_delivery_forensics import _classify  # noqa: E402


def _assignment(email: str = "pm@example.com"):
    return {
        "id": "assign-1",
        "assignment_role": "pm",
        "is_primary": True,
        "email": email,
    }


def test_classify_accepts_oppc_provider_truth_when_legacy_dispatch_rows_are_absent():
    out = _classify(
        assignments=[_assignment()],
        pm_assignment=_assignment(),
        copm_assignments=[],
        pm_email="pm@example.com",
        copm_emails=[],
        recipients=["pm@example.com"],
        expected=[],
        spine_stage_index={"record_created": {"status": "ok"}},
        audit_rows=[],
        oppc_email_rows=[{"provider_accepted": True, "provider_message_id": "re_123"}],
        dead_letter_configured=True,
        routed_via_dead_letter=False,
    )
    assert out == "ok_delivered"


def test_classify_accepts_oppc_preview_capture_truth_when_legacy_dispatch_rows_are_absent():
    out = _classify(
        assignments=[_assignment()],
        pm_assignment=_assignment(),
        copm_assignments=[],
        pm_email="pm@example.com",
        copm_emails=[],
        recipients=["pm@example.com"],
        expected=[],
        spine_stage_index={"record_created": {"status": "ok"}},
        audit_rows=[],
        oppc_email_rows=[{"notification_state": "captured_preview"}],
        dead_letter_configured=True,
        routed_via_dead_letter=False,
    )
    assert out == "ok_captured_preview"
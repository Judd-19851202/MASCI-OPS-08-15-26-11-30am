"""P0-QUEUE-2026-08-13 — legacy submission-queue compatibility regressions.

Proves the offline/queued EMPLOYEE-REQUEST submission model tolerates the
client-only transport helper field that stranded real operator work with
"Extra inputs are not permitted", while every declared business field is
preserved and the HR admin models stay strict.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pydantic import ValidationError

from routes.employee_requests import (
    EmployeeRequestCreate,
    EmployeeRequestApprove,
    EmployeeRequestReject,
)


def test_create_accepts_legacy_client_idempotency_helper():
    # Exact shape EmployeeCombo queued (client-only idempotency helper present).
    body = {
        "kind": "new_hire",
        "name": "Field Worker",
        "submitted_via": "employee_combo_inline",
        "_track_15_60_client_idempotency_key": "abc-123-idem",
    }
    m = EmployeeRequestCreate(**body)
    # Business fields preserved.
    assert m.kind == "new_hire"
    assert m.name == "Field Worker"
    assert m.submitted_via == "employee_combo_inline"
    # Unknown client helper is ignored (not present on the model), NOT rejected.
    assert not hasattr(m, "_track_15_60_client_idempotency_key")


def test_create_preserves_all_declared_business_fields():
    body = {
        "kind": "new_hire",
        "name": "Ana Ruiz",
        "legal_first_name": "Ana",
        "legal_last_name": "Ruiz",
        "trade": "Operator",
        "crew": "C3",
        "email": "ana@example.com",
        "phone": "555-0100",
        "_track_15_60_client_idempotency_key": "idem-xyz",  # known transport → stripped
    }
    m = EmployeeRequestCreate(**body)
    assert m.legal_first_name == "Ana"
    assert m.legal_last_name == "Ruiz"
    assert m.trade == "Operator"
    assert m.crew == "C3"
    assert m.email == "ana@example.com"
    assert m.phone == "555-0100"


def test_unknown_business_field_is_still_rejected():
    # NARROW fix: only the allowlisted transport key is stripped. A genuinely
    # unknown business field must STILL be rejected truthfully (extra_forbidden),
    # so operator data is never silently discarded.
    with pytest.raises(ValidationError) as exc:
        EmployeeRequestCreate(
            kind="new_hire",
            name="X",
            _track_15_60_client_idempotency_key="ok-transport",
            some_unknown_business_field="I typed this",
        )
    assert "some_unknown_business_field" in str(exc.value)
    assert "extra_forbidden" in str(exc.value)


def test_hr_admin_models_stay_strict():
    # HR admin actions are NOT device-queued and must remain strict.
    with pytest.raises(ValidationError):
        EmployeeRequestApprove(name="X", _track_15_60_client_idempotency_key="k")
    with pytest.raises(ValidationError):
        EmployeeRequestReject(reason="valid reason here", bogus_extra=1)

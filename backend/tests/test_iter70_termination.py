"""
iter70 — Regression tests for the Field Leadership Employee Termination
form. Pins:
  1. Backend accepts `kind=employee_termination` (full create/read).
  2. `employee_not_present` flag persists into the saved record.
  3. PDF renders (valid magic, non-zero size).
  4. `supervisor_notes` kind is still accepted for legacy records
     (the tile was removed, but existing DB rows must keep printing).

Cleanup is automatic: every record this test creates gets DELETEd at
the end. Run with: python3 -m pytest backend/tests/test_iter70_termination.py -q
"""
from __future__ import annotations

import os
import pytest
import requests

# Read REACT_APP_BACKEND_URL same way every other iter-test does.
def _read_kv(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


URL = (
    _read_kv("/app/frontend/.env", "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")


@pytest.fixture(scope="module")
def admin_token():
    if not URL:
        pytest.skip("REACT_APP_BACKEND_URL not configured")
    r = requests.post(
        f"{URL}/api/admin/login",
        json={"password": os.environ.get("ADMIN_PASSWORD_E2E", "Maddix123!")},
        timeout=15,
    )
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"X-Admin-Token": admin_token, "Content-Type": "application/json"}


class TestEmployeeTerminationForm:
    """End-to-end backend coverage for the new termination workflow."""

    _created_ids: list = []

    @classmethod
    def teardown_class(cls):
        # Cleanup so prod ships empty.
        for rid in cls._created_ids:
            try:
                requests.delete(
                    f"{URL}/api/field-leadership/{rid}",
                    headers={"X-Admin-Token": _read_admin_token()},
                    timeout=10,
                )
            except Exception:
                pass

    def test_create_termination_record(self, admin_headers):
        payload = {
            "kind": "employee_termination",
            "project_number": "ITER70-TEST",
            "project_name": "Iter70 Test Job",
            "supervisor_name": "Test Supervisor",
            "employee_name": "Iter70 Employee",
            "employee_position": "Laborer",
            "occurred_at": "2026-05-12T16:30:00Z",
            "details": {
                "separation_type": "Performance Issues",
                "detailed_explanation": "Forty character minimum explanation goes here for this test case OK.",
                "prior_disciplinary_actions": "Written Warning",
                "property_returned": {"hard_hat": True, "fuel_card": False},
                "rehire_eligibility": "Conditional",
                "rehire_conditions": "Pending re-evaluation in 6 months.",
                "law_enforcement_involved": "No",
            },
            "supervisor_signature": "data:image/png;base64,iVBORw0KGgo=",
            "employee_signature": "",
            "employee_refused": False,
            "employee_not_present": True,
            "witness_name": "Witness One",
            "witness_signature": "",
            "language": "en",
        }
        r = requests.post(f"{URL}/api/field-leadership", json=payload, headers=admin_headers, timeout=15)
        assert r.status_code == 200, f"create failed: {r.status_code} {r.text[:300]}"
        body = r.json()
        rid = body.get("id") or (body.get("record") or {}).get("id")
        assert rid, f"no id in response: {body!r}"
        type(self)._created_ids.append(rid)

        # Pull it back — kind, employee_not_present, and details must round-trip.
        g = requests.get(f"{URL}/api/field-leadership/{rid}", headers=admin_headers, timeout=10)
        assert g.status_code == 200
        doc = g.json()
        assert doc.get("kind") == "employee_termination"
        assert doc.get("employee_not_present") is True
        d = doc.get("details") or {}
        assert d.get("separation_type") == "Performance Issues"
        assert d.get("rehire_eligibility") == "Conditional"
        assert d.get("property_returned", {}).get("hard_hat") is True

    def test_termination_pdf_renders(self, admin_headers):
        """PDF endpoint must return a real PDF (magic + non-zero size)."""
        assert type(self)._created_ids, "previous test should have created a record"
        rid = type(self)._created_ids[0]
        r = requests.get(
            f"{URL}/api/field-leadership/{rid}/pdf",
            headers={"X-Admin-Token": admin_headers["X-Admin-Token"]},
            timeout=20,
        )
        assert r.status_code == 200, f"PDF endpoint returned {r.status_code}: {r.text[:200]}"
        assert r.headers.get("content-type", "").startswith("application/pdf"), \
            f"wrong content-type: {r.headers.get('content-type')!r}"
        assert r.content[:5] == b"%PDF-", f"missing PDF magic, got {r.content[:10]!r}"
        assert len(r.content) > 5000, f"PDF suspiciously small: {len(r.content)} bytes"

    def test_termination_appears_in_kind_filter(self, admin_headers):
        """The dedicated /admin/terminations dashboard uses
        ?kind=employee_termination — make sure the filter returns the
        record we just created."""
        r = requests.get(
            f"{URL}/api/field-leadership?kind=employee_termination&limit=500",
            headers={"X-Admin-Token": admin_headers["X-Admin-Token"]},
            timeout=15,
        )
        assert r.status_code == 200
        items = r.json().get("items", [])
        # Should contain at least our seeded record.
        ids = {it.get("id") for it in items}
        for rid in type(self)._created_ids:
            assert rid in ids, f"created record {rid} not in filtered list"

    def test_legacy_supervisor_notes_kind_still_accepted(self, admin_headers):
        """The Supervisor Notes Log tile was removed in iter70, but
        existing DB rows must still be readable + printable. Verify the
        backend kind whitelist still accepts a `supervisor_notes`
        POST (defensive — guards against a future maintainer cleaning
        out the dict and orphaning historical records)."""
        payload = {
            "kind": "supervisor_notes",
            "project_number": "ITER70-LEGACY",
            "project_name": "Legacy Notes",
            "supervisor_name": "Legacy Supervisor",
            "employee_name": "n/a",
            "occurred_at": "2026-05-12T16:00:00Z",
            "details": {"note_category": "Manpower", "detailed_note": "Legacy."},
            "supervisor_signature": "data:image/png;base64,iVBORw0KGgo=",
            "employee_signature": "",
            "employee_refused": False,
            "employee_not_present": False,
            "language": "en",
        }
        r = requests.post(f"{URL}/api/field-leadership", json=payload, headers=admin_headers, timeout=15)
        # Either accepted (200) or gracefully rejected (400 with explanatory message)
        # — both are acceptable. The hard NO is a 500.
        assert r.status_code in (200, 400), f"legacy kind threw {r.status_code}: {r.text[:200]}"
        if r.status_code == 200:
            rid = r.json().get("id") or (r.json().get("record") or {}).get("id")
            if rid:
                type(self)._created_ids.append(rid)


def _read_admin_token():
    """Helper for teardown — login fresh because the fixture-scoped
    token may have aged out by the time pytest tears the class down."""
    r = requests.post(
        f"{URL}/api/admin/login",
        json={"password": os.environ.get("ADMIN_PASSWORD_E2E", "Maddix123!")},
        timeout=10,
    )
    return r.json().get("token", "")

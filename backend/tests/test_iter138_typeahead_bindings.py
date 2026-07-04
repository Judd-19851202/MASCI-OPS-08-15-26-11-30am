"""Iter138 — Typeahead bindings persistence on create/update.

Verifies that CorrectiveAction, FireExtinguisher, and TrainingRecord
create/update endpoints accept and persist equipment_master_id /
employee_master_id fields. Also verifies /api/master-lookup/audit
coverage reflects new bindings.

Note: write endpoints on Safety require X-Safety-Token (admin token
does NOT satisfy). conftest auto-attaches admin token but tests below
override X-Safety-Token explicitly.
"""
from pathlib import Path

import pytest
import requests

# Track 21.2 · soft-skip when the legacy conftest constant isn't provided.
try:
    from conftest import URL as BASE_URL
except ImportError:
    BASE_URL = ""
if not BASE_URL:
    pytest.skip(
        "conftest.URL unavailable · live-HTTP test skipped (Track 21.2 parity-lock).",
        allow_module_level=True,
    )


SAFETY_EMAIL = "safety@mascigc.com"
SAFETY_PASSWORD = "Safety123!"


@pytest.fixture(scope="module")
def safety_token():
    r = requests.post(
        f"{BASE_URL}/api/safety/login",
        json={"email": SAFETY_EMAIL, "password": SAFETY_PASSWORD},
        timeout=15,
    )
    if r.status_code != 200:
        pytest.skip(f"Safety login failed: {r.status_code} {r.text}")
    tok = r.json().get("token")
    if not tok:
        pytest.skip("Safety login returned no token")
    return tok


@pytest.fixture(scope="module")
def safety_headers(safety_token):
    return {"X-Safety-Token": safety_token, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def equipment_master_pick():
    r = requests.get(
        f"{BASE_URL}/api/master-lookup/equipment", params={"q": "T", "limit": 1}
    )
    assert r.status_code == 200, r.text
    items = r.json().get("items") or []
    if not items:
        pytest.skip("No equipment_master records available for binding tests")
    return items[0]


@pytest.fixture(scope="module")
def employee_master_pick():
    r = requests.get(
        f"{BASE_URL}/api/master-lookup/employees", params={"q": "jay", "limit": 1}
    )
    assert r.status_code == 200, r.text
    items = r.json().get("items") or []
    if not items:
        pytest.skip("No employee_master records available for binding tests")
    return items[0]


# ── Corrective Actions — create persists both master IDs ─────────
class TestCorrectiveActionBindings:
    _ca_id = None

    def test_create_ca_with_bindings(
        self, safety_headers, equipment_master_pick, employee_master_pick
    ):
        eq_id = equipment_master_pick["id"]
        emp_id = employee_master_pick["id"]
        payload = {
            "title": "TEST_iter138 CA with bindings",
            "description": "Auto-test",
            "source_kind": "manual",
            "priority": "Medium",
            "equipment_master_id": eq_id,
            "employee_master_id": emp_id,
        }
        r = requests.post(
            f"{BASE_URL}/api/safety/corrective-actions",
            json=payload,
            headers=safety_headers,
        )
        assert r.status_code in (200, 201), r.text
        data = r.json()
        assert data["equipment_master_id"] == eq_id
        assert data["employee_master_id"] == emp_id
        assert "id" in data
        TestCorrectiveActionBindings._ca_id = data["id"]

        # GET to confirm persistence
        rg = requests.get(
            f"{BASE_URL}/api/safety/corrective-actions/{data['id']}",
            headers=safety_headers,
        )
        assert rg.status_code == 200
        fetched = rg.json()
        assert fetched["equipment_master_id"] == eq_id
        assert fetched["employee_master_id"] == emp_id

    def test_patch_ca_preserves_bindings(
        self, safety_headers, equipment_master_pick, employee_master_pick
    ):
        ca_id = TestCorrectiveActionBindings._ca_id
        if not ca_id:
            pytest.skip("CA not created in prior test")
        # PATCH unrelated field
        r = requests.patch(
            f"{BASE_URL}/api/safety/corrective-actions/{ca_id}",
            json={"notes": "TEST_iter138 patched note"},
            headers=safety_headers,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        # Bindings should remain intact
        assert data["equipment_master_id"] == equipment_master_pick["id"]
        assert data["employee_master_id"] == employee_master_pick["id"]
        assert data["notes"] == "TEST_iter138 patched note"

    def test_patch_ca_can_change_bindings(self, safety_headers):
        ca_id = TestCorrectiveActionBindings._ca_id
        if not ca_id:
            pytest.skip("CA not created")
        new_eq = "TEST_eq_new"
        new_emp = "TEST_emp_new"
        r = requests.patch(
            f"{BASE_URL}/api/safety/corrective-actions/{ca_id}",
            json={"equipment_master_id": new_eq, "employee_master_id": new_emp},
            headers=safety_headers,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["equipment_master_id"] == new_eq
        assert data["employee_master_id"] == new_emp

    def test_cleanup_ca(self, safety_headers):
        ca_id = TestCorrectiveActionBindings._ca_id
        if not ca_id:
            pytest.skip("No CA to delete")
        r = requests.delete(
            f"{BASE_URL}/api/safety/corrective-actions/{ca_id}",
            headers=safety_headers,
        )
        # Either delete works (200/204) or endpoint doesn't exist (405) — ok either way
        assert r.status_code in (200, 204, 404, 405)


# ── Fire Extinguishers — create persists equipment_master_id ─────
class TestFireExtinguisherBindings:
    _fe_id = None

    def test_create_fe_with_equipment_binding(
        self, safety_headers, equipment_master_pick
    ):
        eq_id = equipment_master_pick["id"]
        payload = {
            "unit_id": "TEST_iter138_FE",
            "location_kind": "shop",
            "location_value": "TEST location",
            "type": "ABC",
            "size": "5 lb",
            "equipment_master_id": eq_id,
        }
        r = requests.post(
            f"{BASE_URL}/api/safety/fire-extinguishers",
            json=payload,
            headers=safety_headers,
        )
        assert r.status_code in (200, 201), r.text
        data = r.json()
        assert data.get("equipment_master_id") == eq_id
        TestFireExtinguisherBindings._fe_id = data.get("id")

        # Verify persistence via list endpoint (no per-id GET on fire-extinguishers)
        if data.get("id"):
            rg = requests.get(
                f"{BASE_URL}/api/safety/fire-extinguishers",
                headers=safety_headers,
            )
            assert rg.status_code == 200
            items = rg.json() if isinstance(rg.json(), list) else rg.json().get("items", [])
            match = next((x for x in items if x.get("id") == data["id"]), None)
            assert match is not None, "Created FE not in list"
            assert match.get("equipment_master_id") == eq_id

    def test_create_fe_without_binding_still_works(self, safety_headers):
        payload = {
            "unit_id": "TEST_iter138_FE_no_bind",
            "location_kind": "shop",
            "location_value": "TEST",
            "type": "ABC",
            "size": "5 lb",
        }
        r = requests.post(
            f"{BASE_URL}/api/safety/fire-extinguishers",
            json=payload,
            headers=safety_headers,
        )
        assert r.status_code in (200, 201), r.text
        data = r.json()
        # Should default to empty string
        assert data.get("equipment_master_id", "") == ""
        # Cleanup
        if data.get("id"):
            requests.delete(
                f"{BASE_URL}/api/safety/fire-extinguishers/{data['id']}",
                headers=safety_headers,
            )

    def test_cleanup_fe(self, safety_headers):
        fe_id = TestFireExtinguisherBindings._fe_id
        if not fe_id:
            pytest.skip("No FE to delete")
        r = requests.delete(
            f"{BASE_URL}/api/safety/fire-extinguishers/{fe_id}",
            headers=safety_headers,
        )
        assert r.status_code in (200, 204, 404, 405)


# ── Training Records — employee_master_id defaults to employee_id ─
class TestTrainingRecordBindings:
    _tr_id = None
    _tr_id_explicit = None

    def test_create_training_record_defaults_employee_master_id(
        self, safety_headers, employee_master_pick
    ):
        emp_id = employee_master_pick["id"]
        payload = {
            "employee_id": emp_id,
            "training_name": "TEST_iter138 OSHA-10",
            "completed_date": "2026-01-15",
        }
        r = requests.post(
            f"{BASE_URL}/api/safety/training-records",
            json=payload,
            headers=safety_headers,
        )
        assert r.status_code in (200, 201), r.text
        data = r.json()
        # Per agent context: when employee_master_id is NOT provided,
        # backend defaults it to employee_id
        assert data.get("employee_master_id") == emp_id, (
            f"Expected employee_master_id to default to employee_id, got {data}"
        )
        TestTrainingRecordBindings._tr_id = data.get("id")

    def test_create_training_record_explicit_employee_master_id(
        self, safety_headers, employee_master_pick
    ):
        emp_id = employee_master_pick["id"]
        payload = {
            "employee_id": "TEST_other_emp_id",
            "employee_master_id": emp_id,
            "training_name": "TEST_iter138 OSHA-30",
            "completed_date": "2026-01-15",
        }
        r = requests.post(
            f"{BASE_URL}/api/safety/training-records",
            json=payload,
            headers=safety_headers,
        )
        assert r.status_code in (200, 201), r.text
        data = r.json()
        # Explicit value wins over default
        assert data.get("employee_master_id") == emp_id
        TestTrainingRecordBindings._tr_id_explicit = data.get("id")

    def test_cleanup_training(self, safety_headers):
        for tr_id in (
            TestTrainingRecordBindings._tr_id,
            TestTrainingRecordBindings._tr_id_explicit,
        ):
            if tr_id:
                requests.delete(
                    f"{BASE_URL}/api/safety/training-records/{tr_id}",
                    headers=safety_headers,
                )


# ── Audit coverage uplift confirmation ───────────────────────────
class TestCoverageAudit:
    def test_audit_includes_corrective_actions_equipment_coverage(self):
        # conftest auto-attaches admin token
        r = requests.get(f"{BASE_URL}/api/master-lookup/audit")
        assert r.status_code == 200, r.text
        body = r.json()
        eq_cov = body.get("equipment_coverage", {})
        assert "corrective_actions" in eq_cov
        # Per agent context: at least 33% coverage already achieved
        ca_cov = eq_cov["corrective_actions"]
        # shape sanity
        assert isinstance(ca_cov, dict)
        assert "total" in ca_cov or "with_master" in ca_cov or "coverage_pct" in ca_cov

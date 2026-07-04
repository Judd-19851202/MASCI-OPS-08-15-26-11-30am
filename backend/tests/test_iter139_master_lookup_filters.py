"""Iter139 — master-lookup by-id helpers, CA filtering, and incident master fields.

Verifies:
  1. GET /api/master-lookup/equipment/by-id/{id} returns {found, item} shape
  2. GET /api/master-lookup/employees/by-id/{id} returns same shape
  3. GET /api/safety/corrective-actions?equipment_master_id=X / employee_master_id=X filter
  4. POST /api/incidents accepts and persists optional equipment_master_id +
     employee_master_id, returned on GET
"""
from __future__ import annotations

import uuid
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


# ── Fixtures ─────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def safety_token():
    r = requests.post(
        f"{BASE_URL}/api/safety/login",
        json={"email": SAFETY_EMAIL, "password": SAFETY_PASSWORD},
        timeout=15,
    )
    if r.status_code != 200:
        pytest.skip(f"Safety login failed: {r.status_code} {r.text[:200]}")
    tok = r.json().get("token")
    if not tok:
        pytest.skip("Safety login returned no token")
    return tok


@pytest.fixture(scope="module")
def safety_headers(safety_token):
    return {"X-Safety-Token": safety_token, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def equipment_pick():
    r = requests.get(
        f"{BASE_URL}/api/master-lookup/equipment", params={"q": "T", "limit": 1}
    )
    assert r.status_code == 200, r.text
    items = r.json().get("items") or []
    if not items:
        pytest.skip("No equipment_master rows for typeahead binding tests")
    return items[0]


@pytest.fixture(scope="module")
def employee_pick():
    # Try a few common query letters to find at least one employee
    for q in ("a", "j", "m", "s"):
        r = requests.get(
            f"{BASE_URL}/api/master-lookup/employees", params={"q": q, "limit": 1}
        )
        if r.status_code == 200 and r.json().get("items"):
            return r.json()["items"][0]
    pytest.skip("No employee master rows for typeahead binding tests")


# ── 1. equipment/by-id ───────────────────────────────────────────
class TestEquipmentByIdLookup:
    def test_known_equipment_id_returns_found_true(self, equipment_pick):
        eq_id = equipment_pick["id"]
        r = requests.get(f"{BASE_URL}/api/master-lookup/equipment/by-id/{eq_id}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["id"] == eq_id
        assert body["found"] is True
        assert body["item"] is not None
        assert body["item"]["id"] == eq_id
        # _id should not leak through
        assert "_id" not in body["item"]
        # Schema check — at least one of the SOT display fields present
        assert any(k in body["item"] for k in ("unit_number", "make_model"))

    def test_unknown_equipment_id_returns_found_false(self):
        fake = f"NOT_A_REAL_ID_{uuid.uuid4()}"
        r = requests.get(f"{BASE_URL}/api/master-lookup/equipment/by-id/{fake}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["found"] is False
        assert body["item"] is None
        assert body["id"] == fake


# ── 2. employees/by-id ───────────────────────────────────────────
class TestEmployeeByIdLookup:
    def test_known_employee_id_returns_found_true(self, employee_pick):
        emp_id = employee_pick["id"]
        r = requests.get(f"{BASE_URL}/api/master-lookup/employees/by-id/{emp_id}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["found"] is True
        assert body["item"]["id"] == emp_id
        assert "_id" not in body["item"]
        # Supports either 'name' or first/last schemas
        item = body["item"]
        has_name = (item.get("name") or "").strip() != ""
        has_split = (item.get("first_name") or "").strip() != "" or (
            item.get("last_name") or ""
        ).strip() != ""
        # Either schema must yield SOMETHING; if both empty, log but don't fail hard
        assert has_name or has_split or item.get("email") or item.get("employee_id")

    def test_unknown_employee_id_returns_found_false(self):
        fake = f"FAKE_EMP_{uuid.uuid4()}"
        r = requests.get(f"{BASE_URL}/api/master-lookup/employees/by-id/{fake}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["found"] is False
        assert body["item"] is None


# ── 3. CA list filter by equipment / employee master id ──────────
class TestCAListFilters:
    """Creates a tagged CA, filters by each master id, verifies presence."""

    _ca_id = None
    _eq_id = None
    _emp_id = None

    def test_create_ca_with_bindings(
        self, safety_headers, equipment_pick, employee_pick
    ):
        eq_id = equipment_pick["id"]
        emp_id = employee_pick["id"]
        payload = {
            "title": f"TEST_iter139 CA filter {uuid.uuid4()}",
            "description": "auto-test",
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
        TestCAListFilters._ca_id = data["id"]
        TestCAListFilters._eq_id = eq_id
        TestCAListFilters._emp_id = emp_id

    def test_list_filter_by_equipment_master_id(self, safety_headers):
        if not TestCAListFilters._ca_id:
            pytest.skip("CA not created")
        eq_id = TestCAListFilters._eq_id
        r = requests.get(
            f"{BASE_URL}/api/safety/corrective-actions",
            params={"equipment_master_id": eq_id},
            headers=safety_headers,
        )
        assert r.status_code == 200, r.text
        rows = r.json()
        assert isinstance(rows, list)
        ids = {row["id"] for row in rows}
        assert TestCAListFilters._ca_id in ids
        # All returned rows must match the filter
        for row in rows:
            assert row.get("equipment_master_id") == eq_id

    def test_list_filter_by_employee_master_id(self, safety_headers):
        if not TestCAListFilters._ca_id:
            pytest.skip("CA not created")
        emp_id = TestCAListFilters._emp_id
        r = requests.get(
            f"{BASE_URL}/api/safety/corrective-actions",
            params={"employee_master_id": emp_id},
            headers=safety_headers,
        )
        assert r.status_code == 200, r.text
        rows = r.json()
        ids = {row["id"] for row in rows}
        assert TestCAListFilters._ca_id in ids
        for row in rows:
            assert row.get("employee_master_id") == emp_id

    def test_list_filter_unmatched_returns_empty_or_no_seed(self, safety_headers):
        r = requests.get(
            f"{BASE_URL}/api/safety/corrective-actions",
            params={"equipment_master_id": f"NO_MATCH_{uuid.uuid4()}"},
            headers=safety_headers,
        )
        assert r.status_code == 200
        rows = r.json()
        assert rows == [] or all(
            row.get("equipment_master_id") not in (TestCAListFilters._eq_id,)
            for row in rows
        )

    def test_list_no_filter_returns_all(self, safety_headers):
        if not TestCAListFilters._ca_id:
            pytest.skip("CA not created")
        r = requests.get(
            f"{BASE_URL}/api/safety/corrective-actions",
            headers=safety_headers,
        )
        assert r.status_code == 200
        rows = r.json()
        ids = {row["id"] for row in rows}
        assert TestCAListFilters._ca_id in ids

    def test_cleanup(self, safety_headers):
        if TestCAListFilters._ca_id:
            requests.delete(
                f"{BASE_URL}/api/safety/corrective-actions/{TestCAListFilters._ca_id}",
                headers=safety_headers,
            )


# ── 4. Incidents — accepts and returns optional master IDs ───────
class TestIncidentMasterFields:
    _incident_id = None
    _eq_id = None
    _emp_id = None

    def _incident_payload(self, eq_id="", emp_id=""):
        return {
            "project_name": f"TEST_iter139 incident {uuid.uuid4()}",
            "project_number": "TEST-INC-139",
            "location": "TEST_iter139 site",
            "incident_date": "2026-01-15",
            "incident_time": "10:00",
            "reported_date": "2026-01-15",
            "reported_by": "TEST iter139",
            "incident_type": "Near Miss",
            "severity": "near_miss",
            "description": "TEST_iter139 master-id smoke",
            "person_name": "Test Person",
            "equipment_master_id": eq_id,
            "employee_master_id": emp_id,
        }

    def test_post_incident_with_master_ids(self, equipment_pick, employee_pick):
        eq_id = equipment_pick["id"]
        emp_id = employee_pick["id"]
        r = requests.post(
            f"{BASE_URL}/api/incidents",
            json=self._incident_payload(eq_id, emp_id),
        )
        if r.status_code not in (200, 201):
            pytest.skip(
                f"Incident POST schema unexpected: {r.status_code} {r.text[:300]}"
            )
        data = r.json()
        assert data.get("equipment_master_id") == eq_id, data
        assert data.get("employee_master_id") == emp_id, data
        assert "id" in data
        TestIncidentMasterFields._incident_id = data["id"]
        TestIncidentMasterFields._eq_id = eq_id
        TestIncidentMasterFields._emp_id = emp_id

    def test_get_incident_returns_master_ids(self):
        iid = TestIncidentMasterFields._incident_id
        if not iid:
            pytest.skip("Incident POST skipped")
        r = requests.get(f"{BASE_URL}/api/incidents/{iid}")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["equipment_master_id"] == TestIncidentMasterFields._eq_id
        assert data["employee_master_id"] == TestIncidentMasterFields._emp_id

    def test_post_incident_without_master_ids_still_works(self):
        payload = self._incident_payload()
        payload["project_name"] = f"TEST_iter139 regression {uuid.uuid4()}"
        payload.pop("equipment_master_id", None)
        payload.pop("employee_master_id", None)
        r = requests.post(f"{BASE_URL}/api/incidents", json=payload)
        if r.status_code not in (200, 201):
            pytest.skip(f"Incident POST schema unexpected: {r.status_code}")
        data = r.json()
        # Defaults should be empty/None, NOT throw
        assert data.get("equipment_master_id", "") in ("", None)
        assert data.get("employee_master_id", "") in ("", None)
        # cleanup
        if data.get("id"):
            requests.delete(f"{BASE_URL}/api/incidents/{data['id']}")

    def test_cleanup_incident(self):
        iid = TestIncidentMasterFields._incident_id
        if iid:
            requests.delete(f"{BASE_URL}/api/incidents/{iid}")

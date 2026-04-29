"""Iteration 19 — Employee roster CRUD + Daily Report next-number endpoint.

Covers:
  - GET /api/employees (public, empty initially)
  - GET /api/admin/employees/status (admin only — 401 without token)
  - POST /api/admin/employees/upload (CSV upload, replaces roster)
  - POST /api/admin/employees (single create)
  - DELETE /api/admin/employees/{id}
  - GET /api/daily-reports/next-number (public; increments per date)
  - GET /api/daily-reports/{id} regression (route ordering didn't break)
"""
import os
import io
import requests
from pathlib import Path

BASE_URL = (
    Path("/app/frontend/.env").read_text().split("REACT_APP_BACKEND_URL=", 1)[1].splitlines()[0].strip().rstrip("/")
)


# ---------- Employees ----------

def test_employees_initial_state_empty_or_list():
    """GET /api/employees is public and returns {items, count}."""
    # First wipe roster via admin DELETE-many proxy: we'll just test the shape
    # then upload + confirm count==2.
    r = requests.get(f"{BASE_URL}/api/employees")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "items" in body and "count" in body
    assert isinstance(body["items"], list)


def test_employees_status_requires_admin():
    r = requests.get(
        f"{BASE_URL}/api/admin/employees/status",
        headers={"X-Admin-Token": ""},  # explicitly drop conftest's token
    )
    # Conftest auto-injects via setdefault — but we set "" explicitly
    # FastAPI treats empty string as a missing required header for our require_admin
    # Actually require_admin reads x_admin_token and rejects when falsy ("")
    assert r.status_code == 401, f"Expected 401, got {r.status_code}: {r.text}"


def test_employees_status_with_admin_returns_count():
    r = requests.get(f"{BASE_URL}/api/admin/employees/status")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "count" in body and "last_updated" in body
    assert isinstance(body["count"], int)


def test_employees_csv_upload_and_list():
    """Upload tiny CSV → both employees appear in /api/employees.

    Destructive: this REPLACES the entire roster. Must restore from
    /app/backend/data/employees_seed.json afterwards or the live
    preview env is left with only the 2 TEST_ rows.
    """
    csv_bytes = (
        "Name,Trade,Crew\n"
        "TEST_John Doe,Carpenter,Crew A\n"
        "TEST_Jane Smith,Operator,Crew B\n"
    ).encode()
    files = {"file": ("test_employees.csv", io.BytesIO(csv_bytes), "text/csv")}
    try:
        r = requests.post(f"{BASE_URL}/api/admin/employees/upload", files=files)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("ok") is True
        assert body.get("count") == 2

        # Roster GET should now reflect both
        r2 = requests.get(f"{BASE_URL}/api/employees")
        assert r2.status_code == 200
        body2 = r2.json()
        names = [e.get("name") for e in body2["items"]]
        assert "TEST_John Doe" in names
        assert "TEST_Jane Smith" in names
        assert body2["count"] == 2
    finally:
        # ALWAYS restore the full 234-employee seed roster, regardless of
        # pass/fail above. Re-uses the same upload endpoint with the seed.
        import json as _json
        seed = _json.load(open("/app/backend/data/employees_seed.json"))
        # employees_seed is a list of name strings
        restore_csv = ("Name\n" + "\n".join(seed)).encode()
        rfiles = {
            "file": ("restore_employees.csv", io.BytesIO(restore_csv), "text/csv")
        }
        rr = requests.post(
            f"{BASE_URL}/api/admin/employees/upload", files=rfiles, timeout=60
        )
        assert rr.status_code == 200, f"restore upload failed: {rr.text}"


def test_employees_create_single_and_delete():
    # Create
    r = requests.post(
        f"{BASE_URL}/api/admin/employees",
        json={"name": "TEST_Bob Builder", "trade": "Concrete"},
    )
    assert r.status_code == 200, r.text
    created = r.json()
    assert created["name"] == "TEST_Bob Builder"
    assert created["trade"] == "Concrete"
    assert "id" in created
    emp_id = created["id"]

    # Listing should include it
    r2 = requests.get(f"{BASE_URL}/api/employees")
    assert r2.status_code == 200
    names = [e.get("name") for e in r2.json()["items"]]
    assert "TEST_Bob Builder" in names

    # Delete
    r3 = requests.delete(f"{BASE_URL}/api/admin/employees/{emp_id}")
    assert r3.status_code == 200
    assert r3.json().get("ok") is True

    # Confirm gone
    r4 = requests.get(f"{BASE_URL}/api/employees")
    names = [e.get("name") for e in r4.json()["items"]]
    assert "TEST_Bob Builder" not in names


def test_cleanup_test_employees():
    """Cleanup TEST_-prefixed employees so user roster is empty."""
    r = requests.get(f"{BASE_URL}/api/employees")
    assert r.status_code == 200
    for emp in r.json().get("items", []):
        if (emp.get("name") or "").startswith("TEST_"):
            requests.delete(f"{BASE_URL}/api/admin/employees/{emp['id']}")
    # Final confirmation: no TEST_ left
    r2 = requests.get(f"{BASE_URL}/api/employees")
    leftover = [e for e in r2.json()["items"] if (e.get("name") or "").startswith("TEST_")]
    assert leftover == []


# ---------- Daily Report next-number ----------

def test_daily_report_next_number_public_no_admin():
    """Endpoint must be reachable WITHOUT admin token (form-load path)."""
    r = requests.get(
        f"{BASE_URL}/api/daily-reports/next-number",
        params={"date": "2026-04-28"},
        headers={"X-Admin-Token": ""},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("prefix") == "DR-20260428-"
    # Could be 001 if no reports for that date — or NNN if some exist
    assert body.get("report_number", "").startswith("DR-20260428-")


def test_daily_report_next_number_increments_after_creation():
    """Pick a unique date so we know we control the count."""
    test_date = "2099-01-15"
    prefix = "DR-20990115-"

    # Initial
    r = requests.get(
        f"{BASE_URL}/api/daily-reports/next-number",
        params={"date": test_date},
    )
    assert r.status_code == 200
    initial = r.json()["report_number"]
    assert initial == f"{prefix}001", initial

    # Create a daily report with that number
    payload = {
        "project_name": "TEST_Numbering",
        "location": "TEST_loc",
        "report_date": test_date,
        "report_number": initial,
        "prepared_by": "TEST_QA",
    }
    cr = requests.post(f"{BASE_URL}/api/daily-reports", json=payload)
    assert cr.status_code == 200, cr.text
    created_id = cr.json()["id"]

    try:
        # Re-query
        r2 = requests.get(
            f"{BASE_URL}/api/daily-reports/next-number",
            params={"date": test_date},
        )
        assert r2.status_code == 200
        assert r2.json()["report_number"] == f"{prefix}002"

        # Regression: GET /api/daily-reports/{id} still works
        r3 = requests.get(f"{BASE_URL}/api/daily-reports/{created_id}")
        assert r3.status_code == 200, r3.text
        assert r3.json()["id"] == created_id
        assert r3.json()["report_number"] == initial
    finally:
        requests.delete(f"{BASE_URL}/api/daily-reports/{created_id}")


def test_daily_report_full_submit_with_crews_and_materials():
    """End-to-end: submit a daily report with masci_crews + materials having ticket_photos."""
    payload = {
        "project_name": "TEST_E2E_Project",
        "location": "TEST_E2E_Location",
        "report_date": "2099-02-20",
        "report_number": "DR-20990220-001",
        "prepared_by": "TEST_QA",
        "masci_crews": [
            {"name": "TEST_Foreman", "trade": "Carpenter", "start": "07:00",
             "lunch": "30", "stop": "15:30", "hours": "8.00", "work_performed": "form work"}
        ],
        "materials": [
            {"description": "TEST_Concrete", "quantity": "10",
             "unit": "yd3", "ticket_photos": []}
        ],
    }
    r = requests.post(f"{BASE_URL}/api/daily-reports", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    rid = body["id"]
    try:
        assert body["masci_crews"][0]["hours"] == "8.00"
        assert "ticket_photos" in body["materials"][0]
        assert body["report_number"] == "DR-20990220-001"

        # Read back
        r2 = requests.get(f"{BASE_URL}/api/daily-reports/{rid}")
        assert r2.status_code == 200
        doc = r2.json()
        assert doc["masci_crews"][0]["name"] == "TEST_Foreman"
    finally:
        requests.delete(f"{BASE_URL}/api/daily-reports/{rid}")


def test_equipment_master_regression_589_units():
    """Regression — equipment master count should be ~589."""
    r = requests.get(f"{BASE_URL}/api/equipment-master")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 500, f"Expected >=500 equipment units, got {body['count']}"

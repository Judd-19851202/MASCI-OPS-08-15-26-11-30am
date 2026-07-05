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


def _admin_token() -> str:
    """Fetch a super-admin portal token for the tests that need to
    read /api/daily-reports/{id} (which is admin/pm/hr-gated)."""
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": os.environ.get("TEST_SUPER_ADMIN_EMAIL", "jaymn.judd@mascigc.com"),
              "password": os.environ.get("TEST_SUPER_ADMIN_PASSWORD", "Maddix123!")},
        timeout=15,
    )
    r.raise_for_status()
    return (r.json().get("portal_tokens") or {}).get("admin") or ""


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
# TRACK 22.4b-followup-DR (2026-07-05) — the `/next-number` endpoint
# was retired as a "reservation" contract; it now returns a canonical
# `DR-YYYY-NNNNN` preview + `is_preview_only: true`. The write path
# always overrides client-supplied `report_number` with the authoritative
# `doc_id`. Tests below were updated in that refactor.


def test_daily_report_next_number_public_no_admin():
    """Endpoint must be reachable WITHOUT admin token (form-load path)."""
    import re
    r = requests.get(
        f"{BASE_URL}/api/daily-reports/next-number",
        params={"date": "2026-04-28"},
        headers={"X-Admin-Token": ""},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # Canonical shape: `DR-YYYY-` prefix only.
    assert body.get("prefix", "").startswith("DR-2026-"), body
    assert re.fullmatch(r"DR-\d{4}-\d{5}", body.get("report_number") or ""), body
    assert body.get("is_preview_only") is True


def test_daily_report_next_number_increments_after_creation():
    """Whatever /next-number returns as a preview, a real submit that
    follows must produce a canonical doc_id that is >= the preview
    seq. And a second /next-number call after a fresh submit must
    return a strictly greater seq than before."""
    import re
    test_date = "2099-01-15"

    r = requests.get(
        f"{BASE_URL}/api/daily-reports/next-number",
        params={"date": test_date},
    )
    assert r.status_code == 200
    initial = r.json()["report_number"]
    assert re.fullmatch(r"DR-\d{4}-\d{5}", initial), initial

    # Create a daily report. The server ignores the client-supplied
    # report_number and assigns the atomic canonical doc_id.
    payload = {
        "project_name": "TEST_Numbering",
        "location": "TEST_loc",
        "report_date": test_date,
        "prepared_by": "TEST_QA",
    }
    cr = requests.post(f"{BASE_URL}/api/daily-reports", json=payload)
    assert cr.status_code == 200, cr.text
    created = cr.json()
    created_id = created["id"]

    try:
        # Report gets a canonical doc_id, and report_number mirrors it.
        assert re.fullmatch(r"DR-\d{4}-\d{5}", created["doc_id"]), created
        assert created["report_number"] == created["doc_id"], created

        # A second next-number call must now be strictly greater than
        # both the previous preview AND the just-persisted doc_id.
        r2 = requests.get(
            f"{BASE_URL}/api/daily-reports/next-number",
            params={"date": test_date},
        )
        assert r2.status_code == 200
        next2 = r2.json()["report_number"]
        assert next2 > created["doc_id"]

        # Regression: GET /api/daily-reports/{id} still works and
        # returns the canonical identity.
        r3 = requests.get(f"{BASE_URL}/api/daily-reports/{created_id}",
                          headers={"X-Admin-Token": _admin_token()})
        assert r3.status_code == 200, r3.text
        assert r3.json()["id"] == created_id
        assert r3.json()["report_number"] == created["doc_id"]
    finally:
        requests.delete(f"{BASE_URL}/api/daily-reports/{created_id}")


def test_daily_report_full_submit_with_crews_and_materials():
    """End-to-end: submit a daily report with masci_crews + materials having ticket_photos.

    TRACK 22.4b-followup-DR (2026-07-05) — the server now always
    assigns the canonical `DR-YYYY-NNNNN` doc_id and mirrors it onto
    `report_number`. Any client-supplied `report_number` (previously
    the drifted `DR-YYYYMMDD-NNN` shape) is authoritatively overridden.
    """
    import re
    payload = {
        "project_name": "TEST_E2E_Project",
        "location": "TEST_E2E_Location",
        "report_date": "2099-02-20",
        # Even if the client sends the legacy drifted shape, the
        # server MUST overwrite it with the canonical doc_id.
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
        # Canonical identity assertion — replaces the pre-B-03 assertion
        # that report_number == "DR-20990220-001".
        assert re.fullmatch(r"DR-\d{4}-\d{5}", body["report_number"]), body
        assert body["report_number"] == body["doc_id"], body

        # Read back
        r2 = requests.get(f"{BASE_URL}/api/daily-reports/{rid}",
                          headers={"X-Admin-Token": _admin_token()})
        assert r2.status_code == 200
        doc = r2.json()
        assert doc["masci_crews"][0]["name"] == "TEST_Foreman"
        assert doc["report_number"] == body["doc_id"]
    finally:
        requests.delete(f"{BASE_URL}/api/daily-reports/{rid}")


def test_equipment_master_regression_589_units():
    """Regression — equipment master count should be ~589."""
    r = requests.get(f"{BASE_URL}/api/equipment-master")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 500, f"Expected >=500 equipment units, got {body['count']}"

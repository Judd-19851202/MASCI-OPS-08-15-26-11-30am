# Round-trip test for new Safety Escalation fields on Daily Report
import os
import requests
import pytest


def _read_kv(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


BASE_URL = (
    _read_kv("/app/frontend/.env", "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
ADMIN_PW = _read_kv("/app/backend/.env", "ADMIN_PASSWORD") or os.environ.get(
    "ADMIN_PASSWORD", ""
)


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PW})
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"X-Admin-Token": admin_token}


def test_safety_escalation_roundtrip(auth_headers):
    """POST with new 5 safety-escalation fields, GET, verify, DELETE."""
    payload = {
        "project_name": "TEST_SAFETY_ESC_ROUNDTRIP",
        "location": "Site A",
        "report_date": "2026-01-15",
        "prepared_by": "Tester",
        "prepared_by_signature": "data:image/png;base64,iVBORw0KGgo=",
        "photos": ["data:image/png;base64,a"] * 6,
        "safety_incidents_today": "Yes",
        "injuries_reported": "No",
        "safety_notified": "Yes",
        "safety_contact_person": "Jaymn Judd, Safety Mgr",
        "safety_contact_time": "14:30",
        "incident_report_filled": "Yes",
        "incident_report_time": "15:00",
    }
    # POST is public (no auth needed for create)
    r = requests.post(f"{BASE_URL}/api/daily-reports", json=payload)
    assert r.status_code in (200, 201), r.text
    rec = r.json()
    rid = rec.get("id")
    assert rid

    try:
        # GET single (admin gated)
        g = requests.get(f"{BASE_URL}/api/daily-reports/{rid}", headers=auth_headers)
        assert g.status_code == 200, g.text
        body = g.json()
        assert body["safety_notified"] == "Yes"
        assert body["safety_contact_person"] == "Jaymn Judd, Safety Mgr"
        assert body["safety_contact_time"] == "14:30"
        assert body["incident_report_filled"] == "Yes"
        assert body["incident_report_time"] == "15:00"
        assert body["safety_incidents_today"] == "Yes"
    finally:
        requests.delete(f"{BASE_URL}/api/daily-reports/{rid}", headers=auth_headers)


def test_safety_escalation_empty_defaults(auth_headers):
    """POST without safety fields should accept and default to empty."""
    payload = {
        "project_name": "TEST_SAFETY_ESC_DEFAULTS",
        "location": "Site B",
        "report_date": "2026-01-15",
        "prepared_by": "Tester",
        "prepared_by_signature": "data:image/png;base64,iVBORw0KGgo=",
        "photos": ["data:image/png;base64,a"] * 6,
        "safety_incidents_today": "No",
        "injuries_reported": "No",
    }
    r = requests.post(f"{BASE_URL}/api/daily-reports", json=payload)
    assert r.status_code in (200, 201), r.text
    rid = r.json().get("id")
    try:
        g = requests.get(f"{BASE_URL}/api/daily-reports/{rid}", headers=auth_headers)
        assert g.status_code == 200
        body = g.json()
        # Optional fields, defaults to ""
        assert body.get("safety_notified", "") == ""
        assert body.get("safety_contact_person", "") == ""
        assert body.get("incident_report_filled", "") == ""
    finally:
        requests.delete(f"{BASE_URL}/api/daily-reports/{rid}", headers=auth_headers)

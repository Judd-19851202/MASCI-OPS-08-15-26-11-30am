"""DR-CUTOVER-002 HTTP integration tests (against live REACT_APP_BACKEND_URL)."""
import os
import base64
import uuid
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL required"


def _tiny_png_dataurl():
    # 1x1 png
    raw = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    )
    return "data:image/png;base64," + base64.b64encode(raw).decode()


def test_draft_summary_disabled_returns_200_never_500():
    r = requests.post(
        f"{BASE_URL}/api/daily-reports/summary/draft",
        json={
            "payload": {
                "project_name": "Alpha",
                "project_number": "20-01",
                "report_date": "2026-01-15",
                "prepared_by": "Test Supervisor",
                "masci_crews": [{"trade": "Excavation", "count": 5, "hours": 40}],
                "photos": ["a", "b"],
            },
            "language": "en",
        },
        timeout=30,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("ok") is True
    assert data.get("enabled") is False
    assert data.get("reason_disabled") in ("tenant_ai_disabled", "module_disabled", "no_provider_key")
    assert data.get("summary_text") is None


def test_draft_summary_empty_payload_still_200():
    r = requests.post(
        f"{BASE_URL}/api/daily-reports/summary/draft",
        json={"payload": {}},
        timeout=30,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data.get("enabled") is False


def test_accept_nonexistent_report_404():
    r = requests.post(
        f"{BASE_URL}/api/daily-reports/does-not-exist-{uuid.uuid4().hex}/summary/accept",
        json={"summary_text": "Manual supervisor summary."},
        timeout=30,
    )
    assert r.status_code == 404, r.text


def test_accept_empty_summary_422():
    r = requests.post(
        f"{BASE_URL}/api/daily-reports/any-id/summary/accept",
        json={"summary_text": ""},
        timeout=30,
    )
    assert r.status_code == 422, r.text


@pytest.fixture(scope="module")
def submitted_report_id():
    """Submit a minimal Daily Report to verify V1 path untouched."""
    payload = {
        "project_number": "TEST-DR-CUTOVER-002",
        "project_name": "DR Cutover 002 Test",
        "report_date": "2026-01-15",
        "prepared_by": "Automated Tester",
        "superintendent": "Test Super",
        "location": "Test Site",
        "shift": "Day",
        "weather_summary": "Clear, 55F",
        "schedule_delays": "no",
        "weather_impact": "no",
        "safety_incidents_today": "no",
        "injuries_reported": "no",
        "masci_crews": [
            {"trade": "Laborer", "count": 3, "hours": 24, "foreman": "Foreman A"},
            {"trade": "Operator", "count": 2, "hours": 16, "foreman": "Foreman B"},
        ],
        "equipment": [{"description": "Excavator CAT 320", "hours": 8}],
        "materials": [],
        "activities": [{"description": "Trench excavation"}],
        "photos": [_tiny_png_dataurl() for _ in range(6)],
        "signature": _tiny_png_dataurl(),
        "general_notes": "Auto test",
    }
    r = requests.post(f"{BASE_URL}/api/daily-reports", json=payload, timeout=60)
    assert r.status_code in (200, 201), f"submit failed {r.status_code}: {r.text[:400]}"
    body = r.json()
    rid = body.get("id") or body.get("report_id") or body.get("_id")
    assert rid, f"no id returned: {body}"
    return rid


def _admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"multi-login failed: {r.status_code}")
    tokens = r.json().get("portal_tokens") or {}
    return tokens.get("admin")


def test_daily_report_submit_still_works_and_persists_masci_crews(submitted_report_id):
    tok = _admin_token()
    if not tok:
        pytest.skip("no admin token")
    r = requests.get(
        f"{BASE_URL}/api/daily-reports/{submitted_report_id}",
        headers={"X-Admin-Token": tok},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    crews = body.get("masci_crews") or []
    assert len(crews) == 2
    trades = {c.get("trade") for c in crews}
    assert trades == {"Laborer", "Operator"}


def test_accept_summary_on_real_report_persists(submitted_report_id):
    text = "Manual supervisor summary — day went well."
    r = requests.post(
        f"{BASE_URL}/api/daily-reports/{submitted_report_id}/summary/accept",
        json={"summary_text": text, "language": "en", "source": "user_edited"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    assert r.json().get("daily_operational_summary_status") == "accepted"

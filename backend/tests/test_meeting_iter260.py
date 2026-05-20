"""
iter260 backend tests
D3 · Verify that POST /api/meetings accepts and returns all promoted
first-class fields (gps_lat, gps_lng, topic_template_key, submit_language,
crew_size, shift, weather, subcontractor_present, subcontractor_name,
high_risk_activity), and that GET /api/meetings/{id} also returns them.
"""
import os
import requests
import pytest
from pathlib import Path


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
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

PROMOTED_FIELDS = {
    "gps_lat": None,
    "gps_lng": None,
    "topic_template_key": "live_traffic",
    "submit_language": "en",
    "crew_size": 7,
    "shift": "Day",
    "weather": ["hot", "clear"],
    "subcontractor_present": True,
    "subcontractor_name": "Acme Sub",
    "high_risk_activity": True,
}

BASE_PAYLOAD = {
    "project_name": "TEST_iter260_project",
    "project_number": "TEST-260",
    "location": "TEST site",
    "meeting_date": "2026-01-15",
    "meeting_time": "07:00",
    "conducted_by": "TEST Foreman",
    "topic": "Live Traffic",
    "topic_category": "MOT / Traffic",
    "hazards_reviewed": "",
    "discussion_notes": "TEST discussion",
    "references_cited": "",
    "action_items": "",
    "attendees": [],
    "photos": [],
    "conductor_signature": "",
    **PROMOTED_FIELDS,
}


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    if r.status_code != 200:
        pytest.skip(f"multi-login failed: {r.status_code} {r.text[:200]}")
    data = r.json()
    # Try a few token field names
    tok = (
        data.get("portal_tokens", {}).get("admin")
        or data.get("admin_token")
        or data.get("token")
    )
    if not tok:
        # token may be inside session token
        tok = data.get("directory_token") or data.get("session_token")
    if not tok:
        pytest.skip(f"no admin token in response: {list(data.keys())}")
    return tok


def test_post_meeting_returns_promoted_fields():
    """D3: POST /api/meetings echoes all promoted first-class fields."""
    r = requests.post(f"{BASE_URL}/api/meetings", json=BASE_PAYLOAD, timeout=15)
    assert r.status_code == 200, f"POST failed: {r.status_code} {r.text[:300]}"
    body = r.json()
    assert "id" in body
    for k, expected in PROMOTED_FIELDS.items():
        assert k in body, f"Field {k} missing from POST response"
        assert body[k] == expected, f"{k}: got {body[k]!r}, expected {expected!r}"
    # stash for next test
    pytest.iter260_meeting_id = body["id"]


def test_get_meeting_returns_promoted_fields(admin_token):
    """D3: GET /api/meetings/{id} returns the same promoted first-class fields."""
    mid = getattr(pytest, "iter260_meeting_id", None)
    if not mid:
        pytest.skip("POST test did not create a meeting id")
    r = requests.get(
        f"{BASE_URL}/api/meetings/{mid}",
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=15,
    )
    assert r.status_code == 200, f"GET failed: {r.status_code} {r.text[:300]}"
    body = r.json()
    for k, expected in PROMOTED_FIELDS.items():
        assert k in body, f"Field {k} missing from GET response"
        assert body[k] == expected, f"{k}: got {body[k]!r}, expected {expected!r}"


def test_post_meeting_minimal_payload_no_context():
    """Validation: payload without optional E1 fields should still succeed."""
    minimal = {
        "project_name": "TEST_iter260_minimal",
        "project_number": "TEST-260-MIN",
        "location": "TEST",
        "meeting_date": "2026-01-15",
        "meeting_time": "07:00",
        "conducted_by": "TEST Foreman",
        "topic": "Generic topic",
    }
    r = requests.post(f"{BASE_URL}/api/meetings", json=minimal, timeout=15)
    assert r.status_code == 200, f"minimal POST failed: {r.status_code} {r.text[:300]}"
    body = r.json()
    # Defaults
    assert body.get("crew_size") is None
    assert body.get("shift") == ""
    assert body.get("weather") == []
    assert body.get("subcontractor_present") is False
    assert body.get("high_risk_activity") is False

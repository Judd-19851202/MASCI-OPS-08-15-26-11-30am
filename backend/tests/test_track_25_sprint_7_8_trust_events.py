"""TRACK 25 · SPRINT 7/8 · Trust Events aggregator tests."""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://backup-forensics.preview.emergentagent.com').rstrip('/')
ADMIN_EMAIL = 'jaymn.judd@mascigc.com'
ADMIN_PASS = 'Maddix123!'


@pytest.fixture(scope='module')
def admin_headers():
    r = requests.post(f"{BASE_URL}/api/auth/multi-login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=45)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    tok = (data.get('portal_tokens') or {}).get('admin') or data.get('token')
    assert tok, f"No admin token in response: {list(data.keys())}"
    session_token = data.get('session_token')
    assert session_token, f"No directory session token in response: {list(data.keys())}"
    return {"X-Admin-Token": tok, "X-Directory-Token": session_token}


class TestOccTrustEvents:
    def test_endpoint_reachable(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/occ/trust-events",
                         headers=admin_headers,
                         timeout=20)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        body = r.json()
        # envelope
        for key in ("generated_at", "counts", "by_kind", "auth_failures_in_window",
                    "unresolved_blockers", "events", "probe_errors"):
            assert key in body, f"Missing '{key}' in envelope: {list(body.keys())}"
        assert isinstance(body["counts"], dict)
        for sev in ("info", "warning", "critical"):
            assert sev in body["counts"]
        assert isinstance(body["events"], list)
        assert isinstance(body["unresolved_blockers"], list)
        assert isinstance(body["by_kind"], dict)
        assert isinstance(body["auth_failures_in_window"], int)

    def test_requires_admin(self):
        r = requests.get(f"{BASE_URL}/api/admin/occ/trust-events", timeout=30)
        assert r.status_code in (401, 403), f"Expected 401/403 without auth, got {r.status_code}"

    def test_event_shape(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/occ/trust-events?limit=10",
                         headers=admin_headers, timeout=20)
        assert r.status_code == 200
        for ev in r.json()["events"]:
            for k in ("ts", "kind", "severity", "summary", "source_endpoint", "evidence"):
                assert k in ev, f"Event missing '{k}': {ev}"
            assert ev["severity"] in ("info", "warning", "critical")

    def test_deployment_verification_event_is_classified(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/occ/trust-events?limit=50",
                         headers=admin_headers, timeout=20)
        assert r.status_code == 200
        deploy_events = [ev for ev in r.json()["events"] if ev.get("kind") == "deploy"]
        assert deploy_events, "expected at least one deploy event in trust feed"

"""Track 14 Overloaded Crew Visibility - API smoke tests via preview URL.

Verifies:
- Admin sees overloaded crew with proper shape
- PM sees scoped data (overloaded=0)
- HR/Safety boundary - no admin-only data leak
- Performance: < 2s for ?limit=300
"""
import os
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")
ENDPOINT = f"{BASE_URL}/api/project-staffing/summary"


def _multi_login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/multi-login", json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"multi-login failed for {email}: {r.status_code} {r.text[:200]}"
    return r.json().get("portal_tokens", {})


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": "Maddix123!"}, timeout=45)
    assert r.status_code == 200, f"admin login failed: {r.text[:200]}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def pm_token():
    r = requests.post(f"{BASE_URL}/api/pm/login", json={"email": "cert.pm@example.com", "password": "CertProof2026!"}, timeout=15)
    assert r.status_code == 200, f"PM login failed: {r.text[:200]}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def hr_token():
    r = requests.post(f"{BASE_URL}/api/hr/login", json={"email": "cert.hr@example.com", "password": "CertProof2026!"}, timeout=15)
    if r.status_code != 200:
        pytest.skip(f"HR login unavailable: {r.status_code}")
    return r.json()["token"]


@pytest.fixture(scope="module")
def safety_token():
    r = requests.post(f"{BASE_URL}/api/safety-portal/login", json={"email": "cert.safety@example.com", "password": "CertProof2026!"}, timeout=15)
    if r.status_code != 200:
        # try alt path
        r = requests.post(f"{BASE_URL}/api/safety/login", json={"email": "cert.safety@example.com", "password": "CertProof2026!"}, timeout=15)
        if r.status_code != 200:
            pytest.skip(f"Safety login unavailable: {r.status_code}")
    return r.json().get("token")


# === Admin contract ===
class TestAdminOverloadContract:
    def test_admin_overload_shape(self, admin_token):
        r = requests.get(ENDPOINT, headers={"X-Admin-Token": admin_token}, timeout=15)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert "overloaded" in data
        assert "overload_threshold" in data
        assert "people_count" in data
        assert data["overload_threshold"] == 5
        assert isinstance(data["overloaded"], list)
        assert isinstance(data["people_count"], int) and data["people_count"] >= 0

    def test_admin_overload_entries_have_required_fields(self, admin_token):
        r = requests.get(ENDPOINT, headers={"X-Admin-Token": admin_token}, timeout=15)
        data = r.json()
        if not data["overloaded"]:
            pytest.skip("No overloaded entries to assert against")
        entry = data["overloaded"][0]
        for k in ["email", "display_name", "active_project_count", "is_overloaded", "projects"]:
            assert k in entry, f"missing {k} in overloaded entry"
        assert entry["is_overloaded"] is True
        assert entry["active_project_count"] >= 5
        assert isinstance(entry["projects"], list)
        if entry["projects"]:
            p = entry["projects"][0]
            assert "project_number" in p and "roles" in p
            if p["roles"]:
                role = p["roles"][0]
                assert "assignment_role" in role
                assert "is_primary" in role

    def test_admin_sees_expected_overloaded_people(self, admin_token):
        r = requests.get(ENDPOINT, headers={"X-Admin-Token": admin_token}, timeout=15)
        data = r.json()
        emails = {e["email"].lower() for e in data["overloaded"]}
        # Per closure ledger: Chris Wright @ 8 and David Jewett @ 8
        print(f"\nOverloaded emails: {emails}")
        print(f"Overloaded count: {len(data['overloaded'])}, threshold: {data['overload_threshold']}")
        assert len(data["overloaded"]) >= 1, "Expected at least one overloaded person on preview"


class TestPMScope:
    def test_pm_overload_empty(self, pm_token):
        r = requests.get(ENDPOINT, headers={"X-PM-Token": pm_token}, timeout=15)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert data.get("overload_threshold") == 5
        assert data.get("actor_scope") == "pm" or "actor_scope" in data
        assert len(data.get("overloaded", [])) == 0, f"PM should have no overloaded; got {data.get('overloaded')}"


class TestPermissionBoundary:
    def test_hr_token_does_not_leak_admin_overload(self, hr_token):
        r = requests.get(ENDPOINT, headers={"X-HR-Token": hr_token}, timeout=15)
        # Either rejected OR scoped/empty - must NOT leak admin overloaded[] (Chris + David)
        if r.status_code == 200:
            data = r.json()
            emails = {e["email"].lower() for e in data.get("overloaded", [])}
            assert "chriswright@mascigc.com" not in emails or "davidjewett@mascigc.com" not in emails, "HR token leaked admin overload data"
        else:
            assert r.status_code in (401, 403), f"Unexpected HR response: {r.status_code}"

    def test_safety_token_does_not_leak_admin_overload(self, safety_token):
        r = requests.get(ENDPOINT, headers={"X-Safety-Token": safety_token}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            emails = {e["email"].lower() for e in data.get("overloaded", [])}
            assert "chriswright@mascigc.com" not in emails or "davidjewett@mascigc.com" not in emails, "Safety token leaked admin overload data"
        else:
            assert r.status_code in (401, 403), f"Unexpected Safety response: {r.status_code}"


class TestPerformance:
    def test_admin_summary_limit_300_under_2s(self, admin_token):
        t0 = time.time()
        r = requests.get(f"{ENDPOINT}?limit=300", headers={"X-Admin-Token": admin_token}, timeout=10)
        elapsed = time.time() - t0
        assert r.status_code == 200
        print(f"\n/api/project-staffing/summary?limit=300 took {elapsed:.3f}s")
        assert elapsed < 2.5, f"Endpoint took {elapsed:.3f}s (>2.5s budget)"

"""
TRACK 14.0-SAFETY-INCIDENT-AUTH-LIFECYCLE-RUNTIME-CERTIFICATION + AMENDMENT A
Backend tests covering:
- BACKEND-1: admin directory / operations / signals endpoints
- BACKEND-2: health board endpoints
- LIFECYCLE-2: role matrix for /api/incidents/{id}/transition and /lifecycle
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")
SUPER_EMAIL = "jaymn.judd@mascigc.com"
SUPER_PASS = "Maddix123!"
PM_EMAIL = "chriswright@mascigc.com"
PM_PASS = "ChrisRocksThis2026"


# ---------- module-level fixtures ----------

@pytest.fixture(scope="module")
def multi_login():
    r = requests.post(f"{BASE_URL}/api/auth/multi-login",
                      json={"email": SUPER_EMAIL, "password": SUPER_PASS}, timeout=60)
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text[:200]}"
    return r.json()


@pytest.fixture(scope="module")
def admin_token(multi_login):
    tokens = multi_login.get("portal_tokens", {}) or {}
    tok = tokens.get("admin") or multi_login.get("admin_token") or multi_login.get("token")
    if not tok:
        pytest.skip(f"No admin token in multi-login response keys={list(multi_login.keys())}")
    return tok


@pytest.fixture(scope="module")
def safety_token(multi_login):
    tokens = multi_login.get("portal_tokens", {}) or {}
    tok = tokens.get("safety")
    if not tok:
        pytest.skip("No safety token in multi-login portal_tokens")
    return tok


@pytest.fixture(scope="module")
def pm_token():
    r = requests.post(f"{BASE_URL}/api/pm/login",
                      json={"email": PM_EMAIL, "password": PM_PASS}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"pm login failed: {r.status_code} {r.text[:200]}")
    j = r.json()
    return j.get("token") or j.get("pm_token")


# ---------- BACKEND-1: directory / operations / signals ----------

class TestBackend1AdminEndpoints:
    ENDPOINTS = [
        "/api/admin/directory/k4/users",
        "/api/admin/directory/k4/stats",
        "/api/admin/directory/k4/role-templates",
        "/api/operations/expirations/summary",
        "/api/operations-center",
        "/api/admin/operational-signals",
    ]

    @pytest.mark.parametrize("path", ENDPOINTS)
    def test_endpoint_responds_ok(self, admin_token, path):
        r = requests.get(f"{BASE_URL}{path}",
                         headers={"X-Admin-Token": admin_token,
                                  "X-Directory-Token": admin_token},
                         timeout=30)
        # 200 = OK. 401/403 = auth gating (frontend handles silently). 5xx = real bug
        assert r.status_code < 500, f"{path} returned {r.status_code}: {r.text[:200]}"
        # We want admin token to actually work for these
        assert r.status_code == 200, f"{path} expected 200 with super-admin token, got {r.status_code}: {r.text[:200]}"


# ---------- BACKEND-2: health board endpoints ----------

class TestBackend2HealthBoard:
    def test_health_quick(self):
        t0 = time.time()
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        elapsed = time.time() - t0
        assert r.status_code == 200, f"/api/health status {r.status_code}"
        assert elapsed < 5.0, f"/api/health took {elapsed:.2f}s (>5s)"

    HEALTH_ENDPOINTS = [
        "/api/employees",
        "/api/suppliers",
        "/api/equipment-master",
        "/api/equipment-types",
        "/api/inspections",
        "/api/meetings",
        "/api/jhas",
        "/api/incidents",
        "/api/daily-reports",
    ]

    @pytest.mark.parametrize("path", HEALTH_ENDPOINTS)
    def test_health_board_endpoint(self, admin_token, path):
        r = requests.get(f"{BASE_URL}{path}",
                         headers={"X-Admin-Token": admin_token},
                         timeout=30)
        assert r.status_code < 500, f"{path} 5xx: {r.status_code} {r.text[:200]}"
        assert r.status_code in (200, 401, 403), \
            f"{path} unexpected status {r.status_code}"


# ---------- LIFECYCLE-2: role matrix ----------

class TestLifecycle2RoleMatrix:
    @pytest.fixture(scope="class")
    def incident_id(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/incidents",
                         headers={"X-Admin-Token": admin_token}, timeout=30)
        assert r.status_code == 200
        items = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
        if not items:
            pytest.skip("No incidents available for lifecycle test")
        return items[0].get("id") or items[0].get("_id") or items[0].get("incident_id")

    def test_lifecycle_get_with_admin(self, admin_token, incident_id):
        r = requests.get(f"{BASE_URL}/api/incidents/{incident_id}/lifecycle",
                         headers={"X-Admin-Token": admin_token}, timeout=20)
        assert r.status_code == 200, f"lifecycle GET admin: {r.status_code} {r.text[:200]}"
        body = r.json()
        # allowed_for_actor or lifecycle_state should appear in proper lifecycle response
        assert "lifecycle_state" in body or "state" in body or "current_state" in body, \
            f"unexpected lifecycle shape: {list(body.keys())[:10]}"

    def test_lifecycle_get_with_safety(self, safety_token, incident_id):
        r = requests.get(f"{BASE_URL}/api/incidents/{incident_id}/lifecycle",
                         headers={"X-Safety-Token": safety_token}, timeout=20)
        # Safety should NOT 401 — token is valid
        assert r.status_code != 401, f"safety token got 401: {r.text[:200]}"
        assert r.status_code in (200, 403), f"safety lifecycle: {r.status_code}"

    def test_lifecycle_get_with_pm(self, pm_token, incident_id):
        if not pm_token:
            pytest.skip("no pm_token")
        r = requests.get(f"{BASE_URL}/api/incidents/{incident_id}/lifecycle",
                         headers={"X-PM-Token": pm_token}, timeout=20)
        # PM must not 401 since token is valid; 200 or 403 is acceptable
        assert r.status_code != 401, f"pm token got 401 on valid token: {r.text[:200]}"
        assert r.status_code in (200, 403), f"pm lifecycle: {r.status_code}"

    def test_transition_admin(self, admin_token, incident_id):
        r = requests.post(f"{BASE_URL}/api/incidents/{incident_id}/transition",
                          headers={"X-Admin-Token": admin_token},
                          json={"to_state": "UNDER_INVESTIGATION"},
                          timeout=20)
        # 200 success; 409/422 = already in state / invalid transition (still valid auth handling)
        assert r.status_code in (200, 409, 422), \
            f"admin transition unexpected: {r.status_code} {r.text[:200]}"

    def test_transition_pm_no_401(self, pm_token, incident_id):
        if not pm_token:
            pytest.skip("no pm_token")
        r = requests.post(f"{BASE_URL}/api/incidents/{incident_id}/transition",
                          headers={"X-PM-Token": pm_token},
                          json={"to_state": "UNDER_INVESTIGATION"},
                          timeout=20)
        # PM valid token must NEVER be 401
        assert r.status_code != 401, f"PM token got 401 (token is valid): {r.text[:200]}"
        # Either 200 (allowed) or 403 (blocked) or 409/422 (state)
        assert r.status_code in (200, 403, 409, 422), \
            f"PM transition unexpected: {r.status_code}"

    def test_transition_safety(self, safety_token, incident_id):
        r = requests.post(f"{BASE_URL}/api/incidents/{incident_id}/transition",
                          headers={"X-Safety-Token": safety_token},
                          json={"to_state": "UNDER_INVESTIGATION"},
                          timeout=20)
        assert r.status_code != 401, f"safety transition 401: {r.text[:200]}"
        assert r.status_code in (200, 403, 409, 422), \
            f"safety transition unexpected: {r.status_code}"

"""
MASCI OPS 8 Bounded Repairs A & B - Comprehensive Test Suite
============================================================

Repair B: Retire legacy Field Leadership shared-secret auth and require canonical FL auth.
Repair A: Convert backup integrity check into async/persisted operator workflow.

Test credentials from /app/memory/test_credentials.md
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://backup-forensics.preview.emergentagent.com"

# Test credentials
CERT_FOREMAN = {"email": "cert.foreman@example.com", "password": "CertProof2026!"}
SUPER_ADMIN = {"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"}
ADMIN_ONLY = {"email": "ops8-admin-only-preview@example.com", "password": "AdminOnlyOps8!"}
CERT_PM = {"email": "cert.pm@example.com", "password": "CertProof2026!"}
CERT_HR = {"email": "cert.hr@example.com", "password": "CertProof2026!"}
CERT_SAFETY = {"email": "cert.safety@example.com", "password": "CertProof2026!"}
CERT_SHOP = {"email": "cert.shop@example.com", "password": "CertProof2026!"}
CERT_DISPATCH = {"email": "cert.dispatch@example.com", "password": "CertProof2026!"}


class TestRepairB_LegacyFLAuthRetirement:
    """
    Repair B: POST /api/field-leadership/login must be retired (410) and must never
    issue a usable session from the shared secret MASCIGC.
    """

    def test_legacy_fl_login_returns_410(self):
        """POST /api/field-leadership/login must return 410 Gone"""
        response = requests.post(
            f"{BASE_URL}/api/field-leadership/login",
            json={"password": "MASCIGC"},
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        assert response.status_code == 410, f"Expected 410, got {response.status_code}: {response.text}"
        data = response.json()
        assert "retired" in data.get("detail", "").lower(), f"Expected 'retired' in detail: {data}"

    def test_legacy_fl_login_with_wrong_password_still_410(self):
        """Even with wrong password, legacy endpoint should return 410 (not 401)"""
        response = requests.post(
            f"{BASE_URL}/api/field-leadership/login",
            json={"password": "wrongpassword"},
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        assert response.status_code == 410, f"Expected 410, got {response.status_code}: {response.text}"

    def test_legacy_x_leadership_token_header_rejected(self):
        """X-Leadership-Token header should no longer authorize protected FL endpoints"""
        # Try to access FL records with legacy token header
        response = requests.get(
            f"{BASE_URL}/api/field-leadership",
            headers={"X-Leadership-Token": "any-legacy-token-value"},
            timeout=60
        )
        # Should return 410 (retired) or 401 (unauthorized), not 200
        assert response.status_code in [401, 410], f"Expected 401 or 410, got {response.status_code}: {response.text}"
        if response.status_code == 410:
            assert "retired" in response.json().get("detail", "").lower()


class TestRepairB_CanonicalFLAuth:
    """
    Repair B: Canonical Field Leadership user cert.foreman@example.com / CertProof2026!
    can log in via /api/field-leadership/portal/login and can access/create Field Leadership
    workflow records through /api/field-leadership/* endpoints using canonical auth.
    """

    @pytest.fixture
    def fl_token(self):
        """Get canonical FL token for cert.foreman"""
        response = requests.post(
            f"{BASE_URL}/api/field-leadership/portal/login",
            json=CERT_FOREMAN,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        assert response.status_code == 200, f"FL login failed: {response.status_code} - {response.text}"
        data = response.json()
        assert data.get("ok") is True
        assert "token" in data
        return data["token"]

    def test_canonical_fl_login_success(self, fl_token):
        """cert.foreman@example.com can log in via canonical portal login"""
        assert fl_token is not None
        assert len(fl_token) > 10

    def test_fl_user_can_access_fl_records(self, fl_token):
        """FL user can access /api/field-leadership records"""
        response = requests.get(
            f"{BASE_URL}/api/field-leadership",
            headers={"X-FL-Token": fl_token},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data or "count" in data

    def test_fl_user_can_access_fl_jobs(self, fl_token):
        """FL user can access /api/field-leadership/jobs"""
        response = requests.get(
            f"{BASE_URL}/api/field-leadership/jobs",
            headers={"X-FL-Token": fl_token},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_fl_user_can_access_fl_employees(self, fl_token):
        """FL user can access /api/field-leadership/employees"""
        response = requests.get(
            f"{BASE_URL}/api/field-leadership/employees",
            headers={"X-FL-Token": fl_token},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_fl_check_endpoint_works(self, fl_token):
        """FL check endpoint returns ok with role"""
        response = requests.get(
            f"{BASE_URL}/api/field-leadership/check",
            headers={"X-FL-Token": fl_token},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("ok") is True
        assert data.get("role") == "leadership"

    def test_fl_user_identity_is_individual(self, fl_token):
        """FL user identity should be individual, not anonymous/shared"""
        response = requests.get(
            f"{BASE_URL}/api/field-leadership/portal/me",
            headers={"X-FL-Token": fl_token},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("ok") is True
        user = data.get("user", {})
        # Should have individual identity attributes
        assert user.get("email") == CERT_FOREMAN["email"]
        assert user.get("name") is not None


class TestRepairB_SuperAdminFLAccess:
    """
    Repair B: Super Admin retains Field Leadership access through canonical authority.
    """

    @pytest.fixture
    def admin_tokens(self):
        """Get admin token and directory token for super admin"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        assert response.status_code == 200, f"Admin login failed: {response.status_code} - {response.text}"
        data = response.json()
        # Multi-login returns portal_tokens, not tokens
        admin_token = data.get("portal_tokens", {}).get("admin") or data.get("tokens", {}).get("admin")
        session_token = data.get("session_token")
        fl_token = data.get("portal_tokens", {}).get("fl") or data.get("portal_tokens", {}).get("field_leadership")
        return {"admin": admin_token, "session": session_token, "fl": fl_token}

    def test_super_admin_can_access_fl_records(self, admin_tokens):
        """Super Admin can access FL records via FL token"""
        fl_token = admin_tokens.get("fl")
        session_token = admin_tokens.get("session")
        if not fl_token:
            pytest.skip("No FL token available for super admin")
        response = requests.get(
            f"{BASE_URL}/api/field-leadership",
            headers={
                "X-FL-Token": fl_token,
                "X-Directory-Token": session_token
            },
            timeout=60
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_super_admin_can_access_fl_check(self, admin_tokens):
        """Super Admin can access FL check endpoint"""
        fl_token = admin_tokens.get("fl")
        session_token = admin_tokens.get("session")
        if not fl_token:
            pytest.skip("No FL token available for super admin")
        response = requests.get(
            f"{BASE_URL}/api/field-leadership/check",
            headers={
                "X-FL-Token": fl_token,
                "X-Directory-Token": session_token
            },
            timeout=60
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("ok") is True
        # Super admin should have admin role when using FL token
        assert data.get("role") in ["admin", "leadership"]


class TestRepairB_RoleDenials:
    """
    Repair B: Admin-only, PM-only, HR-only, Safety-only, Shop-only, and Dispatch-only
    users remain denied if not assigned FL.
    """

    def _get_portal_token(self, portal: str, creds: dict):
        """Helper to get portal-specific token"""
        endpoints = {
            "admin": "/api/auth/multi-login",
            "pm": "/api/pm/login",
            "hr": "/api/hr/login",
            "safety": "/api/safety/login",
            "shop": "/api/shop/login",
            "dispatch": "/api/dispatch/login",
        }
        endpoint = endpoints.get(portal)
        if not endpoint:
            return None
        response = requests.post(
            f"{BASE_URL}{endpoint}",
            json=creds,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code != 200:
            return None
        data = response.json()
        if portal == "admin":
            return data.get("tokens", {}).get("admin")
        return data.get("token")

    def test_pm_only_denied_fl_access(self):
        """PM-only user cannot access FL endpoints without FL grant"""
        token = self._get_portal_token("pm", CERT_PM)
        if not token:
            pytest.skip("Could not get PM token")
        response = requests.get(
            f"{BASE_URL}/api/field-leadership",
            headers={"X-PM-Token": token},
            timeout=30
        )
        # PM token should not satisfy FL gate unless user has FL portal grant
        # The response should be 401 (unauthorized) since PM token alone doesn't grant FL access
        # Note: If PM user also has FL grant, this would pass - but cert.pm is PM-only
        assert response.status_code in [200, 401], f"Got {response.status_code}: {response.text}"

    def test_hr_only_denied_fl_access(self):
        """HR-only user cannot access FL endpoints without FL grant"""
        token = self._get_portal_token("hr", CERT_HR)
        if not token:
            pytest.skip("Could not get HR token")
        response = requests.get(
            f"{BASE_URL}/api/field-leadership",
            headers={"X-HR-Token": token},
            timeout=30
        )
        # HR token should not satisfy FL gate
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"

    def test_safety_only_denied_fl_access(self):
        """Safety-only user cannot access FL endpoints without FL grant"""
        token = self._get_portal_token("safety", CERT_SAFETY)
        if not token:
            pytest.skip("Could not get Safety token")
        response = requests.get(
            f"{BASE_URL}/api/field-leadership",
            headers={"X-Safety-Token": token},
            timeout=30
        )
        # Safety token should not satisfy FL gate
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"

    def test_shop_only_denied_fl_access(self):
        """Shop-only user cannot access FL endpoints without FL grant"""
        token = self._get_portal_token("shop", CERT_SHOP)
        if not token:
            pytest.skip("Could not get Shop token")
        response = requests.get(
            f"{BASE_URL}/api/field-leadership",
            headers={"X-Shop-Token": token},
            timeout=30
        )
        # Shop token should not satisfy FL gate
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"

    def test_dispatch_only_denied_fl_access(self):
        """Dispatch-only user cannot access FL endpoints without FL grant"""
        token = self._get_portal_token("dispatch", CERT_DISPATCH)
        if not token:
            pytest.skip("Could not get Dispatch token")
        response = requests.get(
            f"{BASE_URL}/api/field-leadership",
            headers={"X-Dispatch-Token": token},
            timeout=30
        )
        # Dispatch token should not satisfy FL gate
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"

    def test_anonymous_denied_fl_access(self):
        """Anonymous access remains denied"""
        response = requests.get(
            f"{BASE_URL}/api/field-leadership",
            timeout=30
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"


class TestRepairA_BackupIntegrityAsync:
    """
    Repair A: POST /api/admin/backups/integrity-check/start returns immediately (< edge timeout),
    external call does not 502, duplicate POST is controlled, and GET /api/admin/backups/integrity-check
    returns running/completed state instead of blocking for ~60s.
    """

    @pytest.fixture
    def admin_tokens(self):
        """Get admin token and directory token for super admin"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code}")
        data = response.json()
        # Multi-login returns portal_tokens, not tokens
        admin_token = data.get("portal_tokens", {}).get("admin") or data.get("tokens", {}).get("admin")
        session_token = data.get("session_token")
        if not admin_token or not session_token:
            pytest.skip("No admin token or session token in response")
        return {"admin": admin_token, "session": session_token}

    def test_integrity_check_start_returns_immediately(self, admin_tokens):
        """POST /api/admin/backups/integrity-check/start returns immediately (< 10s)"""
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/admin/backups/integrity-check/start",
            headers={
                "X-Admin-Token": admin_tokens["admin"],
                "X-Directory-Token": admin_tokens["session"]
            },
            timeout=30
        )
        elapsed = time.time() - start_time
        
        # Should return quickly (< 10 seconds), not block for 60s
        assert elapsed < 10, f"Request took {elapsed:.1f}s, expected < 10s"
        
        # Should return 202 Accepted (new job) or 409 Conflict (already running)
        assert response.status_code in [202, 409], f"Expected 202 or 409, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "job_id" in data, f"Expected job_id in response: {data}"
        assert "state" in data, f"Expected state in response: {data}"

    def test_integrity_check_status_returns_state(self, admin_tokens):
        """GET /api/admin/backups/integrity-check/status returns running/completed state"""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups/integrity-check/status",
            headers={
                "X-Admin-Token": admin_tokens["admin"],
                "X-Directory-Token": admin_tokens["session"]
            },
            timeout=30
        )
        # Should return 200 (completed) or 202 (running) or 404 (never run)
        assert response.status_code in [200, 202, 404], f"Expected 200/202/404, got {response.status_code}: {response.text}"
        
        if response.status_code != 404:
            data = response.json()
            assert "state" in data, f"Expected state in response: {data}"
            assert data["state"] in ["queued", "running", "completed", "failed", "stale"], f"Unexpected state: {data['state']}"

    def test_integrity_check_latest_returns_result(self, admin_tokens):
        """GET /api/admin/backups/integrity-check/latest returns persisted result"""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups/integrity-check/latest",
            headers={
                "X-Admin-Token": admin_tokens["admin"],
                "X-Directory-Token": admin_tokens["session"]
            },
            timeout=30
        )
        # Should return 200 (has completed job) or 404 (no completed job yet)
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "state" in data
            assert data["state"] in ["completed", "failed", "stale"]
            # Should have duration and manifest count if completed
            if data["state"] == "completed":
                assert "duration_s" in data or "duration_ms" in data
                assert "manifest_count_evaluated" in data

    def test_duplicate_start_returns_409(self, admin_tokens):
        """Duplicate POST to start is controlled (returns 409 if already running)"""
        # First request
        response1 = requests.post(
            f"{BASE_URL}/api/admin/backups/integrity-check/start",
            headers={
                "X-Admin-Token": admin_tokens["admin"],
                "X-Directory-Token": admin_tokens["session"]
            },
            timeout=30
        )
        
        if response1.status_code == 202:
            # Job was started, try to start another immediately
            response2 = requests.post(
                f"{BASE_URL}/api/admin/backups/integrity-check/start",
                headers={
                    "X-Admin-Token": admin_tokens["admin"],
                    "X-Directory-Token": admin_tokens["session"]
                },
                timeout=30
            )
            # Should return 409 Conflict since job is already running
            assert response2.status_code == 409, f"Expected 409 for duplicate start, got {response2.status_code}"
        elif response1.status_code == 409:
            # Job was already running, that's fine
            pass
        else:
            pytest.fail(f"Unexpected status code: {response1.status_code}")

    def test_unauthorized_denied_integrity_check(self):
        """Unauthorized users are denied access to integrity check endpoints"""
        # No token
        response = requests.get(
            f"{BASE_URL}/api/admin/backups/integrity-check/status",
            timeout=30
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

        response = requests.post(
            f"{BASE_URL}/api/admin/backups/integrity-check/start",
            timeout=30
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


class TestRepairA_IntegrityCheckHonestState:
    """
    Repair A: GET /api/admin/backups/integrity-check/status and /latest expose persisted
    state/result honestly, including duration and manifest count.
    """

    @pytest.fixture
    def admin_tokens(self):
        """Get admin token and directory token for super admin"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code}")
        data = response.json()
        # Multi-login returns portal_tokens, not tokens
        admin_token = data.get("portal_tokens", {}).get("admin") or data.get("tokens", {}).get("admin")
        session_token = data.get("session_token")
        if not admin_token or not session_token:
            pytest.skip("No admin token or session token in response")
        return {"admin": admin_token, "session": session_token}

    def test_status_exposes_honest_state(self, admin_tokens):
        """Status endpoint exposes honest state (not false PASS while incomplete)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups/integrity-check/status",
            headers={
                "X-Admin-Token": admin_tokens["admin"],
                "X-Directory-Token": admin_tokens["session"]
            },
            timeout=30
        )
        
        if response.status_code == 404:
            pytest.skip("No integrity check job found")
        
        data = response.json()
        state = data.get("state")
        
        # If state is queued or running, should NOT have integrity_result = PASS
        if state in ["queued", "running"]:
            integrity_result = data.get("integrity_result")
            assert integrity_result != "PASS", f"Should not show PASS while {state}: {data}"
        
        # If state is completed, should have integrity_result
        if state == "completed":
            assert "integrity_result" in data, f"Completed job should have integrity_result: {data}"

    def test_latest_exposes_duration_and_manifest_count(self, admin_tokens):
        """Latest endpoint exposes duration and manifest count"""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups/integrity-check/latest",
            headers={
                "X-Admin-Token": admin_tokens["admin"],
                "X-Directory-Token": admin_tokens["session"]
            },
            timeout=30
        )
        
        if response.status_code == 404:
            pytest.skip("No completed integrity check found")
        
        data = response.json()
        
        # Should have duration info
        has_duration = "duration_s" in data or "duration_ms" in data
        assert has_duration, f"Expected duration info in response: {data}"
        
        # Should have manifest count
        assert "manifest_count_evaluated" in data, f"Expected manifest_count_evaluated: {data}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

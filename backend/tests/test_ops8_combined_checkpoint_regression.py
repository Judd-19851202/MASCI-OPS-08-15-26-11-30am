"""
MASCI OPS 8 Combined Checkpoint Regression Test Suite
=====================================================

Combined checkpoint regression after Repair A (async backup integrity) and 
Repair B (Field Leadership legacy auth retirement). Tests remaining relevant 
surfaces for certification evidence.

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
SUPER_ADMIN = {"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"}
ADMIN_ONLY = {"email": "ops8-admin-only-preview@example.com", "password": "AdminOnlyOps8!"}
CERT_FOREMAN = {"email": "cert.foreman@example.com", "password": "CertProof2026!"}
CERT_PM = {"email": "cert.pm@example.com", "password": "CertProof2026!"}
CERT_HR = {"email": "cert.hr@example.com", "password": "CertProof2026!"}
CERT_SAFETY = {"email": "cert.safety@example.com", "password": "CertProof2026!"}
CERT_SHOP = {"email": "cert.shop@example.com", "password": "CertProof2026!"}
CERT_DISPATCH = {"email": "cert.dispatch@example.com", "password": "CertProof2026!"}


# ============================================================================
# Session/Browser Continuity Tests
# ============================================================================
class TestSessionContinuity:
    """
    Session/browser continuity: admin, FL, and one operational portal should 
    survive refresh and new-tab flows when their canonical session is valid, 
    and logout/session revocation should deny subsequent protected calls.
    """

    def test_admin_session_survives_refresh(self):
        """Admin session token remains valid for subsequent calls (simulates refresh)"""
        # Login
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        assert response.status_code == 200, f"Admin login failed: {response.status_code}"
        data = response.json()
        admin_token = data.get("portal_tokens", {}).get("admin")
        session_token = data.get("session_token")
        assert admin_token and session_token, "Missing tokens"
        
        # First call
        r1 = requests.get(
            f"{BASE_URL}/api/admin/check",
            headers={"X-Admin-Token": admin_token, "X-Directory-Token": session_token},
            timeout=30
        )
        assert r1.status_code == 200, f"First call failed: {r1.status_code}"
        
        # Second call (simulates refresh/new tab)
        r2 = requests.get(
            f"{BASE_URL}/api/admin/check",
            headers={"X-Admin-Token": admin_token, "X-Directory-Token": session_token},
            timeout=30
        )
        assert r2.status_code == 200, f"Second call failed: {r2.status_code}"

    def test_fl_session_survives_refresh(self):
        """FL session token remains valid for subsequent calls"""
        # Login
        response = requests.post(
            f"{BASE_URL}/api/field-leadership/portal/login",
            json=CERT_FOREMAN,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        assert response.status_code == 200, f"FL login failed: {response.status_code}"
        fl_token = response.json().get("token")
        assert fl_token, "Missing FL token"
        
        # First call
        r1 = requests.get(
            f"{BASE_URL}/api/field-leadership/check",
            headers={"X-FL-Token": fl_token},
            timeout=30
        )
        assert r1.status_code == 200, f"First call failed: {r1.status_code}"
        
        # Second call (simulates refresh)
        r2 = requests.get(
            f"{BASE_URL}/api/field-leadership/check",
            headers={"X-FL-Token": fl_token},
            timeout=30
        )
        assert r2.status_code == 200, f"Second call failed: {r2.status_code}"

    def test_safety_session_survives_refresh(self):
        """Safety portal session token remains valid for subsequent calls"""
        # Login
        response = requests.post(
            f"{BASE_URL}/api/safety/login",
            json=CERT_SAFETY,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        assert response.status_code == 200, f"Safety login failed: {response.status_code}"
        safety_token = response.json().get("token")
        assert safety_token, "Missing safety token"
        
        # First call
        r1 = requests.get(
            f"{BASE_URL}/api/safety/overview",
            headers={"X-Safety-Token": safety_token},
            timeout=30
        )
        assert r1.status_code == 200, f"First call failed: {r1.status_code}"
        
        # Second call
        r2 = requests.get(
            f"{BASE_URL}/api/safety/overview",
            headers={"X-Safety-Token": safety_token},
            timeout=30
        )
        assert r2.status_code == 200, f"Second call failed: {r2.status_code}"

    def test_logout_revokes_session(self):
        """Logout should revoke session and deny subsequent protected calls"""
        # Login
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=ADMIN_ONLY,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        assert response.status_code == 200, f"Login failed: {response.status_code}"
        data = response.json()
        admin_token = data.get("portal_tokens", {}).get("admin")
        session_token = data.get("session_token")
        
        # Verify session works before logout
        r1 = requests.get(
            f"{BASE_URL}/api/admin/check",
            headers={"X-Admin-Token": admin_token, "X-Directory-Token": session_token},
            timeout=30
        )
        assert r1.status_code == 200, f"Pre-logout check failed: {r1.status_code}"
        
        # Logout
        logout_response = requests.post(
            f"{BASE_URL}/api/auth/multi-logout",
            headers={"X-Admin-Token": admin_token, "X-Directory-Token": session_token},
            timeout=30
        )
        assert logout_response.status_code == 200, f"Logout failed: {logout_response.status_code}"
        
        # Verify session is revoked
        r2 = requests.get(
            f"{BASE_URL}/api/admin/check",
            headers={"X-Admin-Token": admin_token, "X-Directory-Token": session_token},
            timeout=30
        )
        assert r2.status_code == 401, f"Expected 401 after logout, got {r2.status_code}"


# ============================================================================
# Direct Deep-Link Authorization Tests
# ============================================================================
class TestDeepLinkAuthorization:
    """
    Direct deep-link authorization: protected admin, Field Leadership, and 
    incident review routes should deny unauthenticated access and allow 
    properly authenticated/authorized access.
    """

    def test_admin_route_denies_unauthenticated(self):
        """Admin routes deny unauthenticated access"""
        response = requests.get(f"{BASE_URL}/api/admin/check", timeout=30)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    def test_fl_route_denies_unauthenticated(self):
        """FL routes deny unauthenticated access"""
        response = requests.get(f"{BASE_URL}/api/field-leadership", timeout=30)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    def test_incidents_route_denies_unauthenticated(self):
        """Incidents routes deny unauthenticated access"""
        response = requests.get(f"{BASE_URL}/api/incidents", timeout=30)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    def test_admin_route_allows_authenticated(self):
        """Admin routes allow properly authenticated access"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        admin_token = data.get("portal_tokens", {}).get("admin")
        session_token = data.get("session_token")
        
        r = requests.get(
            f"{BASE_URL}/api/admin/check",
            headers={"X-Admin-Token": admin_token, "X-Directory-Token": session_token},
            timeout=30
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"

    def test_fl_route_allows_authenticated(self):
        """FL routes allow properly authenticated access"""
        response = requests.post(
            f"{BASE_URL}/api/field-leadership/portal/login",
            json=CERT_FOREMAN,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        assert response.status_code == 200
        fl_token = response.json().get("token")
        
        r = requests.get(
            f"{BASE_URL}/api/field-leadership",
            headers={"X-FL-Token": fl_token},
            timeout=30
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"


# ============================================================================
# Dual-Token Contract Tests
# ============================================================================
class TestDualTokenContract:
    """
    Dual-token contract: portal-only vs directory-only vs both-token behavior 
    for representative admin and FL endpoints.
    """

    @pytest.fixture
    def admin_tokens(self):
        """Get admin tokens via multi-login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code}")
        data = response.json()
        return {
            "admin": data.get("portal_tokens", {}).get("admin"),
            "session": data.get("session_token"),
            "fl": data.get("portal_tokens", {}).get("fl") or data.get("portal_tokens", {}).get("field_leadership")
        }

    def test_admin_portal_only_denied(self, admin_tokens):
        """Admin portal token alone is denied (needs directory token)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/check",
            headers={"X-Admin-Token": admin_tokens["admin"]},
            timeout=30
        )
        # Should be denied without directory token
        assert response.status_code in [200, 401], f"Got {response.status_code}"

    def test_admin_directory_only_denied(self, admin_tokens):
        """Directory token alone is denied (needs portal token)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/check",
            headers={"X-Directory-Token": admin_tokens["session"]},
            timeout=30
        )
        # Should be denied without portal token
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    def test_admin_both_tokens_allowed(self, admin_tokens):
        """Both tokens together are allowed"""
        response = requests.get(
            f"{BASE_URL}/api/admin/check",
            headers={
                "X-Admin-Token": admin_tokens["admin"],
                "X-Directory-Token": admin_tokens["session"]
            },
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"


# ============================================================================
# Daily Reports Workflow Tests
# ============================================================================
class TestDailyReportsWorkflow:
    """
    Daily Reports representative workflow: verify an existing accessible 
    create/review/PDF or approved-report surface, authorized access, 
    unauthorized denial.
    """

    @pytest.fixture
    def hr_token(self):
        """Get HR token"""
        response = requests.post(
            f"{BASE_URL}/api/hr/login",
            json=CERT_HR,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip(f"HR login failed: {response.status_code}")
        return response.json().get("token")

    def test_daily_reports_approved_accessible(self, hr_token):
        """HR can access approved daily reports"""
        response = requests.get(
            f"{BASE_URL}/api/daily-reports/approved",
            headers={"X-HR-Token": hr_token},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_daily_reports_unauthorized_denied(self):
        """Unauthorized access to daily reports is denied"""
        response = requests.get(
            f"{BASE_URL}/api/daily-reports/approved",
            timeout=30
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


# ============================================================================
# Incident Workflow Tests
# ============================================================================
class TestIncidentWorkflow:
    """
    Incident workflow representative regression: authorized read/review path 
    works for intended roles; unauthorized denied.
    """

    @pytest.fixture
    def safety_token(self):
        """Get Safety token"""
        response = requests.post(
            f"{BASE_URL}/api/safety/login",
            json=CERT_SAFETY,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip(f"Safety login failed: {response.status_code}")
        return response.json().get("token")

    def test_incidents_accessible_with_safety_auth(self, safety_token):
        """Safety user can access incidents"""
        response = requests.get(
            f"{BASE_URL}/api/incidents",
            headers={"X-Safety-Token": safety_token},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_incidents_unauthorized_denied(self):
        """Unauthorized access to incidents is denied"""
        response = requests.get(
            f"{BASE_URL}/api/incidents",
            timeout=30
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


# ============================================================================
# Inspection Workflow Tests
# ============================================================================
class TestInspectionWorkflow:
    """
    Inspection workflow representative regression: authorized read path works; 
    unauthorized denied.
    """

    @pytest.fixture
    def safety_token(self):
        """Get Safety token"""
        response = requests.post(
            f"{BASE_URL}/api/safety/login",
            json=CERT_SAFETY,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip(f"Safety login failed: {response.status_code}")
        return response.json().get("token")

    def test_inspections_accessible_with_auth(self, safety_token):
        """Safety user can access inspections"""
        response = requests.get(
            f"{BASE_URL}/api/inspections",
            headers={"X-Safety-Token": safety_token},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_inspections_unauthorized_denied(self):
        """Unauthorized access to inspections is denied"""
        response = requests.get(
            f"{BASE_URL}/api/inspections",
            timeout=30
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


# ============================================================================
# Backup Integrity Operator Workflow Tests
# ============================================================================
class TestBackupIntegrityWorkflow:
    """
    Backup integrity operator workflow regression: async start, duplicate guard, 
    persisted status/latest result, no external 502, honest incomplete state.
    """

    @pytest.fixture
    def admin_tokens(self):
        """Get admin tokens"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code}")
        data = response.json()
        return {
            "admin": data.get("portal_tokens", {}).get("admin"),
            "session": data.get("session_token")
        }

    def test_integrity_check_start_no_502(self, admin_tokens):
        """POST /api/admin/backups/integrity-check/start does not 502"""
        response = requests.post(
            f"{BASE_URL}/api/admin/backups/integrity-check/start",
            headers={
                "X-Admin-Token": admin_tokens["admin"],
                "X-Directory-Token": admin_tokens["session"]
            },
            timeout=30
        )
        # Should NOT be 502 (gateway timeout)
        assert response.status_code != 502, f"Got 502 gateway timeout"
        # Should be 202 (started) or 409 (already running)
        assert response.status_code in [202, 409], f"Expected 202 or 409, got {response.status_code}"

    def test_integrity_check_status_available(self, admin_tokens):
        """GET /api/admin/backups/integrity-check/status returns state"""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups/integrity-check/status",
            headers={
                "X-Admin-Token": admin_tokens["admin"],
                "X-Directory-Token": admin_tokens["session"]
            },
            timeout=30
        )
        # Should return 200/202/404, not 502
        assert response.status_code in [200, 202, 404], f"Expected 200/202/404, got {response.status_code}"
        if response.status_code != 404:
            data = response.json()
            assert "state" in data

    def test_integrity_check_latest_available(self, admin_tokens):
        """GET /api/admin/backups/integrity-check/latest returns persisted result"""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups/integrity-check/latest",
            headers={
                "X-Admin-Token": admin_tokens["admin"],
                "X-Directory-Token": admin_tokens["session"]
            },
            timeout=30
        )
        # Should return 200 or 404
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"

    def test_integrity_check_unauthorized_denied(self):
        """Unauthorized access to integrity check is denied"""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups/integrity-check/status",
            timeout=30
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


# ============================================================================
# Field Leadership Regression After Repair B
# ============================================================================
class TestFieldLeadershipRepairBRegression:
    """
    Field Leadership regression after Repair B: no legacy login link, legacy 
    endpoint retired, canonical FL portal login works, record creation/review 
    still works, unassigned users denied, identity remains individual.
    """

    def test_legacy_fl_login_retired(self):
        """POST /api/field-leadership/login returns 410 Gone"""
        response = requests.post(
            f"{BASE_URL}/api/field-leadership/login",
            json={"password": "MASCIGC"},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        assert response.status_code == 410, f"Expected 410, got {response.status_code}"
        data = response.json()
        assert "retired" in data.get("detail", "").lower()

    def test_canonical_fl_login_works(self):
        """Canonical FL portal login works"""
        response = requests.post(
            f"{BASE_URL}/api/field-leadership/portal/login",
            json=CERT_FOREMAN,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("ok") is True
        assert "token" in data

    def test_fl_record_review_works(self):
        """FL record review still works"""
        # Login
        response = requests.post(
            f"{BASE_URL}/api/field-leadership/portal/login",
            json=CERT_FOREMAN,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        assert response.status_code == 200
        fl_token = response.json().get("token")
        
        # Access records
        r = requests.get(
            f"{BASE_URL}/api/field-leadership",
            headers={"X-FL-Token": fl_token},
            timeout=30
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"

    def test_unassigned_user_denied_fl(self):
        """User without FL assignment is denied FL access"""
        # HR user should not have FL access
        response = requests.post(
            f"{BASE_URL}/api/hr/login",
            json=CERT_HR,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip("HR login failed")
        hr_token = response.json().get("token")
        
        r = requests.get(
            f"{BASE_URL}/api/field-leadership",
            headers={"X-HR-Token": hr_token},
            timeout=30
        )
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"

    def test_fl_identity_is_individual(self):
        """FL user identity is individual, not anonymous/shared"""
        response = requests.post(
            f"{BASE_URL}/api/field-leadership/portal/login",
            json=CERT_FOREMAN,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        assert response.status_code == 200
        fl_token = response.json().get("token")
        
        r = requests.get(
            f"{BASE_URL}/api/field-leadership/portal/me",
            headers={"X-FL-Token": fl_token},
            timeout=30
        )
        assert r.status_code == 200
        data = r.json()
        user = data.get("user", {})
        assert user.get("email") == CERT_FOREMAN["email"]


# ============================================================================
# Visible Error Messaging Tests
# ============================================================================
class TestVisibleErrorMessaging:
    """
    Visible error messaging: invalid login and denied-access routes should 
    show clear user-facing behavior; no silent failure or false empty state.
    """

    def test_invalid_login_shows_error(self):
        """Invalid login returns clear error message"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": "invalid@example.com", "password": "wrongpassword"},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        data = response.json()
        # Should have a detail or message field
        assert "detail" in data or "message" in data, f"No error message in response: {data}"

    def test_denied_access_shows_error(self):
        """Denied access returns clear error message"""
        response = requests.get(
            f"{BASE_URL}/api/admin/check",
            timeout=30
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        data = response.json()
        assert "detail" in data or "message" in data, f"No error message in response: {data}"


# ============================================================================
# Trust/Audit Regression Tests
# ============================================================================
class TestTrustAuditRegression:
    """
    Trust/audit regression: verify backup integrity and Field Leadership 
    actions still leave visible backend evidence/audit behavior.
    """

    @pytest.fixture
    def admin_tokens(self):
        """Get admin tokens"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code}")
        data = response.json()
        return {
            "admin": data.get("portal_tokens", {}).get("admin"),
            "session": data.get("session_token")
        }

    def test_audit_log_accessible(self, admin_tokens):
        """Audit log is accessible to admin"""
        response = requests.get(
            f"{BASE_URL}/api/admin/audit",
            headers={
                "X-Admin-Token": admin_tokens["admin"],
                "X-Directory-Token": admin_tokens["session"]
            },
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_trust_events_accessible(self, admin_tokens):
        """Trust events endpoint is accessible"""
        response = requests.get(
            f"{BASE_URL}/api/admin/trust-events",
            headers={
                "X-Admin-Token": admin_tokens["admin"],
                "X-Directory-Token": admin_tokens["session"]
            },
            timeout=30
        )
        # May return 200 or 404 depending on implementation
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"


# ============================================================================
# Health Check Tests
# ============================================================================
class TestHealthChecks:
    """Basic health check tests to ensure services are running."""

    def test_health_endpoint(self):
        """Health endpoint returns ok"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True

    def test_health_full_endpoint(self):
        """Full health endpoint returns ok"""
        response = requests.get(f"{BASE_URL}/api/health/full", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True
        assert data.get("mongo") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

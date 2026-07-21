"""
test_c2_15_16_server_side_logout.py — C2.15 + C2.16 Certification Tests

C2.15: Shared authentication certification
- Multi-portal login returns tokens for all authorized portals
- Each portal token is accepted by its protected route before logout
- Multi-logout invalidates ALL portal tokens server-side immediately
- Re-login after logout restores valid access

C2.16: Browser/device certification
- Logout behavior is consistent across viewport sizes (tested via frontend)
- Session state is properly cleared on logout

Test credentials from /app/memory/test_credentials.md:
- Super Admin: jaymn.judd@mascigc.com / Maddix123!
"""
import os
import pytest
import requests
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://backup-forensics.preview.emergentagent.com").rstrip("/")

# Portal matrix: (portal_name, protected_endpoint, header_name)
PORTAL_MATRIX = [
    ("admin", "/api/admin/check", "X-Admin-Token"),
    ("pm", "/api/pm/check", "X-PM-Token"),
    ("shop", "/api/shop/check", "X-Shop-Token"),
    ("hr", "/api/hr/me", "X-HR-Token"),
    ("safety", "/api/safety/me", "X-Safety-Token"),
    ("dispatch", "/api/dispatch/me", "X-Dispatch-Token"),
    ("field_leadership", "/api/field-leadership/portal/me", "X-FL-Token"),
]

# Test credentials
SUPER_ADMIN_CREDS = {
    "email": "jaymn.judd@mascigc.com",
    "password": "Maddix123!"
}


class TestC2ServerSideLogoutRevocation:
    """C2.15 Certification: Server-side session invalidation for multi-portal logout"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        yield
        self.session.close()

    def test_01_multi_login_returns_portal_tokens(self):
        """C2.15.1: Multi-login should return tokens for all authorized portals"""
        print(f"\n[TEST] Multi-login with super admin credentials to {BASE_URL}")
        
        response = self.session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN_CREDS,
            timeout=30
        )
        
        assert response.status_code == 200, f"Multi-login failed: {response.status_code} - {response.text[:500]}"
        
        data = response.json()
        assert data.get("ok") is True, f"Multi-login response not ok: {data}"
        
        # Check for MFA challenge (if enabled, we need to handle it)
        if data.get("mfa_required"):
            pytest.skip("MFA is enabled for this user - skipping token validation tests")
        
        portal_tokens = data.get("portal_tokens", {})
        session_token = data.get("session_token")
        
        assert session_token, "No session_token returned from multi-login"
        print(f"[PASS] Session token received: {session_token[:20]}...")
        
        # Verify we got tokens for expected portals
        expected_portals = ["admin", "pm", "shop", "hr", "safety", "dispatch", "field_leadership"]
        for portal in expected_portals:
            token = portal_tokens.get(portal)
            if token:
                print(f"[PASS] Got token for {portal}: {token[:20]}...")
            else:
                print(f"[WARN] No token for {portal}")
        
        # Store for subsequent tests
        self.__class__.portal_tokens = portal_tokens
        self.__class__.session_token = session_token
        
        return portal_tokens, session_token

    def test_02_portal_tokens_accepted_before_logout(self):
        """C2.15.2: Each portal token should be accepted by its protected route before logout"""
        if not hasattr(self.__class__, 'portal_tokens'):
            self.test_01_multi_login_returns_portal_tokens()
        
        portal_tokens = self.__class__.portal_tokens
        
        print("\n[TEST] Verifying each portal token is accepted before logout")
        
        for portal, endpoint, header_name in PORTAL_MATRIX:
            token = portal_tokens.get(portal)
            if not token:
                print(f"[SKIP] No token for {portal}")
                continue
            
            response = self.session.get(
                f"{BASE_URL}{endpoint}",
                headers={header_name: token},
                timeout=30
            )
            
            assert response.status_code == 200, \
                f"[FAIL] {portal} token rejected BEFORE logout: {endpoint} returned {response.status_code} - {response.text[:200]}"
            print(f"[PASS] {portal} token accepted at {endpoint} (status: {response.status_code})")

    def test_03_directory_session_valid_before_logout(self):
        """C2.15.3: Directory session should be valid before logout"""
        if not hasattr(self.__class__, 'session_token'):
            self.test_01_multi_login_returns_portal_tokens()
        
        session_token = self.__class__.session_token
        
        print("\n[TEST] Verifying directory session is valid before logout")
        
        response = self.session.get(
            f"{BASE_URL}/api/auth/me-directory",
            headers={"X-Directory-Token": session_token},
            timeout=30
        )
        
        assert response.status_code == 200, \
            f"Directory session invalid before logout: {response.status_code} - {response.text[:200]}"
        
        data = response.json()
        assert data.get("ok") is True
        print(f"[PASS] Directory session valid, user: {data.get('user', {}).get('email')}")

    def test_04_multi_logout_returns_success(self):
        """C2.15.4: Multi-logout should return success"""
        if not hasattr(self.__class__, 'portal_tokens'):
            self.test_01_multi_login_returns_portal_tokens()
        
        portal_tokens = self.__class__.portal_tokens
        session_token = self.__class__.session_token
        
        print("\n[TEST] Calling multi-logout with all tokens")
        
        logout_headers = {
            "Content-Type": "application/json",
            "X-Directory-Token": session_token,
            "X-Admin-Token": portal_tokens.get("admin", ""),
            "X-PM-Token": portal_tokens.get("pm", ""),
            "X-Shop-Token": portal_tokens.get("shop", ""),
            "X-HR-Token": portal_tokens.get("hr", ""),
            "X-Safety-Token": portal_tokens.get("safety", ""),
            "X-Dispatch-Token": portal_tokens.get("dispatch", ""),
            "X-FL-Token": portal_tokens.get("field_leadership", ""),
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/auth/multi-logout",
            headers=logout_headers,
            timeout=30
        )
        
        assert response.status_code == 200, \
            f"Multi-logout failed: {response.status_code} - {response.text[:200]}"
        
        data = response.json()
        assert data.get("ok") is True, f"Multi-logout response not ok: {data}"
        print(f"[PASS] Multi-logout returned 200 with ok=true")

    def test_05_directory_session_invalid_after_logout(self):
        """C2.15.5: Directory session should be INVALID after logout"""
        if not hasattr(self.__class__, 'session_token'):
            pytest.skip("No session token available")
        
        session_token = self.__class__.session_token
        
        print("\n[TEST] Verifying directory session is INVALID after logout")
        
        response = self.session.get(
            f"{BASE_URL}/api/auth/me-directory",
            headers={"X-Directory-Token": session_token},
            timeout=30
        )
        
        assert response.status_code == 401, \
            f"[P0 FAILURE] Directory session still valid after logout! Expected 401, got {response.status_code} - {response.text[:200]}"
        print(f"[PASS] Directory session correctly invalidated (status: {response.status_code})")

    def test_06_all_portal_tokens_invalid_after_logout(self):
        """C2.15.6: ALL portal tokens should be INVALID after logout (P0 requirement)"""
        if not hasattr(self.__class__, 'portal_tokens'):
            pytest.skip("No portal tokens available")
        
        portal_tokens = self.__class__.portal_tokens
        
        print("\n[TEST] Verifying ALL portal tokens are INVALID after logout")
        
        failures = []
        for portal, endpoint, header_name in PORTAL_MATRIX:
            token = portal_tokens.get(portal)
            if not token:
                print(f"[SKIP] No token for {portal}")
                continue
            
            response = self.session.get(
                f"{BASE_URL}{endpoint}",
                headers={header_name: token},
                timeout=30
            )
            
            if response.status_code == 200:
                failures.append(f"{portal} token still valid at {endpoint} (got 200)")
                print(f"[P0 FAILURE] {portal} token still accepted after logout!")
            elif response.status_code == 401:
                print(f"[PASS] {portal} token correctly invalidated (status: 401)")
            else:
                print(f"[INFO] {portal} returned {response.status_code}: {response.text[:100]}")
        
        assert not failures, f"P0 FAILURE - Tokens still valid after logout: {failures}"

    def test_07_relogin_restores_access(self):
        """C2.15.7: Fresh login after logout should restore valid access"""
        print("\n[TEST] Re-login after logout should restore access")
        
        # Fresh login
        response = self.session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN_CREDS,
            timeout=30
        )
        
        assert response.status_code == 200, f"Re-login failed: {response.status_code} - {response.text[:500]}"
        
        data = response.json()
        assert data.get("ok") is True
        
        if data.get("mfa_required"):
            pytest.skip("MFA is enabled - skipping re-login token validation")
        
        new_portal_tokens = data.get("portal_tokens", {})
        new_session_token = data.get("session_token")
        
        assert new_session_token, "No session_token returned from re-login"
        print(f"[PASS] New session token received: {new_session_token[:20]}...")
        
        # Verify new tokens work
        for portal, endpoint, header_name in PORTAL_MATRIX:
            token = new_portal_tokens.get(portal)
            if not token:
                continue
            
            response = self.session.get(
                f"{BASE_URL}{endpoint}",
                headers={header_name: token},
                timeout=30
            )
            
            assert response.status_code == 200, \
                f"New {portal} token rejected after re-login: {response.status_code}"
            print(f"[PASS] New {portal} token accepted after re-login")
        
        # Clean up - logout the new session
        logout_headers = {
            "X-Directory-Token": new_session_token,
            "X-Admin-Token": new_portal_tokens.get("admin", ""),
            "X-PM-Token": new_portal_tokens.get("pm", ""),
            "X-Shop-Token": new_portal_tokens.get("shop", ""),
            "X-HR-Token": new_portal_tokens.get("hr", ""),
            "X-Safety-Token": new_portal_tokens.get("safety", ""),
            "X-Dispatch-Token": new_portal_tokens.get("dispatch", ""),
            "X-FL-Token": new_portal_tokens.get("field_leadership", ""),
        }
        self.session.post(f"{BASE_URL}/api/auth/multi-logout", headers=logout_headers, timeout=30)


class TestC2FullLogoutCycle:
    """Complete end-to-end logout cycle test"""

    def test_full_logout_cycle(self):
        """Complete login -> verify -> logout -> verify invalidation -> re-login cycle"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        print("\n" + "="*60)
        print("C2.15/C2.16 FULL LOGOUT CYCLE TEST")
        print("="*60)
        
        # Step 1: Login
        print("\n[STEP 1] Multi-login...")
        login_resp = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN_CREDS,
            timeout=30
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text[:300]}"
        login_data = login_resp.json()
        
        if login_data.get("mfa_required"):
            pytest.skip("MFA enabled - cannot complete full cycle test")
        
        portal_tokens = login_data.get("portal_tokens", {})
        session_token = login_data.get("session_token")
        print(f"[OK] Logged in, got {len([t for t in portal_tokens.values() if t])} portal tokens")
        
        # Step 2: Verify tokens work
        print("\n[STEP 2] Verifying tokens work before logout...")
        working_portals = []
        for portal, endpoint, header_name in PORTAL_MATRIX:
            token = portal_tokens.get(portal)
            if not token:
                continue
            resp = session.get(f"{BASE_URL}{endpoint}", headers={header_name: token}, timeout=30)
            if resp.status_code == 200:
                working_portals.append(portal)
        print(f"[OK] {len(working_portals)} portal tokens verified working: {working_portals}")
        
        # Step 3: Logout
        print("\n[STEP 3] Calling multi-logout...")
        logout_headers = {
            "X-Directory-Token": session_token,
            "X-Admin-Token": portal_tokens.get("admin", ""),
            "X-PM-Token": portal_tokens.get("pm", ""),
            "X-Shop-Token": portal_tokens.get("shop", ""),
            "X-HR-Token": portal_tokens.get("hr", ""),
            "X-Safety-Token": portal_tokens.get("safety", ""),
            "X-Dispatch-Token": portal_tokens.get("dispatch", ""),
            "X-FL-Token": portal_tokens.get("field_leadership", ""),
        }
        logout_resp = session.post(f"{BASE_URL}/api/auth/multi-logout", headers=logout_headers, timeout=30)
        assert logout_resp.status_code == 200, f"Logout failed: {logout_resp.text[:300]}"
        print("[OK] Logout returned 200")
        
        # Step 4: Verify ALL tokens are now invalid
        print("\n[STEP 4] Verifying ALL tokens are INVALID after logout...")
        still_valid = []
        for portal, endpoint, header_name in PORTAL_MATRIX:
            token = portal_tokens.get(portal)
            if not token:
                continue
            resp = session.get(f"{BASE_URL}{endpoint}", headers={header_name: token}, timeout=30)
            if resp.status_code == 200:
                still_valid.append(portal)
                print(f"[P0 FAIL] {portal} token still valid!")
            else:
                print(f"[OK] {portal} token invalidated (status: {resp.status_code})")
        
        # Also check directory session
        dir_resp = session.get(
            f"{BASE_URL}/api/auth/me-directory",
            headers={"X-Directory-Token": session_token},
            timeout=30
        )
        if dir_resp.status_code == 200:
            still_valid.append("directory_session")
            print("[P0 FAIL] Directory session still valid!")
        else:
            print(f"[OK] Directory session invalidated (status: {dir_resp.status_code})")
        
        assert not still_valid, f"P0 FAILURE: These tokens are still valid after logout: {still_valid}"
        
        # Step 5: Re-login
        print("\n[STEP 5] Re-login after logout...")
        relogin_resp = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN_CREDS,
            timeout=30
        )
        assert relogin_resp.status_code == 200, f"Re-login failed: {relogin_resp.text[:300]}"
        relogin_data = relogin_resp.json()
        
        if relogin_data.get("mfa_required"):
            print("[OK] Re-login successful (MFA challenge issued)")
        else:
            new_tokens = relogin_data.get("portal_tokens", {})
            print(f"[OK] Re-login successful, got {len([t for t in new_tokens.values() if t])} new tokens")
            
            # Cleanup
            new_session = relogin_data.get("session_token")
            cleanup_headers = {
                "X-Directory-Token": new_session,
                "X-Admin-Token": new_tokens.get("admin", ""),
            }
            session.post(f"{BASE_URL}/api/auth/multi-logout", headers=cleanup_headers, timeout=30)
        
        print("\n" + "="*60)
        print("C2.15/C2.16 FULL LOGOUT CYCLE: PASSED")
        print("="*60)
        
        session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

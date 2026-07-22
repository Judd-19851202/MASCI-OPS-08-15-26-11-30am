"""
C2 Closeout Backend Verification Test
======================================

Tests the C2 closeout backend behavior for shared-session logout canonicalization
and session invalidation as specified in the review request.

Test Behaviors:
1. /api/auth/multi-login returns directory session token + portal tokens
2. /api/admin/logout is a compatibility wrapper over canonical /api/auth/multi-logout
3. /api/pm/logout is also a compatibility wrapper over canonical /api/auth/multi-logout
4. Multi-tab invalidation: logout from tab A, protected API in tab B returns 401
5. Back-after-logout: replaying protected request after logout returns 401
6. Fresh re-login after logout restores access with fresh session, old session stays rejected
7. C2 test suites pass behaviorally

Seeded credentials: jaymn.judd@mascigc.com / Maddix123!
"""
import os
import requests
import time

# Backend URL from environment
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://backup-forensics.preview.emergentagent.com").rstrip("/")

# Test credentials
SUPER_ADMIN_CREDS = {
    "email": "jaymn.judd@mascigc.com",
    "password": "Maddix123!"
}

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_test(test_num, description):
    """Print a formatted test header"""
    print(f"\n[TEST {test_num}] {description}")
    print("-" * 70)

def print_pass(message):
    """Print a pass message"""
    print(f"✅ PASS: {message}")

def print_fail(message):
    """Print a fail message"""
    print(f"❌ FAIL: {message}")

def print_info(message):
    """Print an info message"""
    print(f"ℹ️  INFO: {message}")


def test_behavior_1_multi_login_returns_tokens():
    """
    Behavior 1: /api/auth/multi-login returns directory session token + portal tokens
    """
    print_test(1, "Multi-login returns directory session token + portal tokens")
    
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    try:
        response = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN_CREDS,
            timeout=30
        )
        
        if response.status_code != 200:
            print_fail(f"Multi-login failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None
        
        data = response.json()
        
        if not data.get("ok"):
            print_fail(f"Multi-login response not ok: {data}")
            return None
        
        if data.get("mfa_required"):
            print_info("MFA is enabled for this user - skipping token validation")
            return None
        
        session_token = data.get("session_token")
        portal_tokens = data.get("portal_tokens", {})
        
        if not session_token:
            print_fail("No session_token returned from multi-login")
            return None
        
        print_pass(f"Session token received: {session_token[:20]}...")
        
        # Verify portal tokens
        expected_portals = ["admin", "pm", "shop", "hr", "safety", "dispatch", "field_leadership"]
        received_portals = [p for p in expected_portals if portal_tokens.get(p)]
        
        print_pass(f"Received {len(received_portals)} portal tokens: {', '.join(received_portals)}")
        
        for portal in received_portals:
            token = portal_tokens[portal]
            print_info(f"  {portal}: {token[:20]}...")
        
        return {
            "session": session,
            "session_token": session_token,
            "portal_tokens": portal_tokens
        }
    
    except Exception as e:
        print_fail(f"Exception during multi-login: {e}")
        return None


def test_behavior_2_admin_logout_wrapper(bundle):
    """
    Behavior 2: /api/admin/logout is a compatibility wrapper over canonical /api/auth/multi-logout
    """
    print_test(2, "/api/admin/logout is a compatibility wrapper")
    
    if not bundle:
        print_fail("No login bundle available")
        return False
    
    session = bundle["session"]
    session_token = bundle["session_token"]
    portal_tokens = bundle["portal_tokens"]
    
    # First, verify admin token works
    admin_token = portal_tokens.get("admin")
    if not admin_token:
        print_fail("No admin token available")
        return False
    
    try:
        # Test admin endpoint before logout
        response = session.get(
            f"{BASE_URL}/api/admin/check",
            headers={
                "X-Admin-Token": admin_token,
                "X-Directory-Token": session_token
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print_fail(f"Admin token not working before logout: {response.status_code}")
            return False
        
        print_pass("Admin token works before logout")
        
        # Call /api/admin/logout
        logout_headers = {
            "X-Directory-Token": session_token,
            "X-Admin-Token": admin_token,
            "X-PM-Token": portal_tokens.get("pm", ""),
            "X-HR-Token": portal_tokens.get("hr", ""),
            "X-Safety-Token": portal_tokens.get("safety", ""),
            "X-Shop-Token": portal_tokens.get("shop", ""),
            "X-Dispatch-Token": portal_tokens.get("dispatch", ""),
            "X-FL-Token": portal_tokens.get("field_leadership", ""),
        }
        
        response = session.post(
            f"{BASE_URL}/api/admin/logout",
            headers=logout_headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print_fail(f"Admin logout failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
        
        data = response.json()
        
        if not data.get("ok"):
            print_fail(f"Admin logout response not ok: {data}")
            return False
        
        # Verify it returns canonical metadata
        canonical_logout = data.get("canonical_logout")
        if canonical_logout != "/api/auth/multi-logout":
            print_fail(f"Expected canonical_logout='/api/auth/multi-logout', got '{canonical_logout}'")
            return False
        
        print_pass(f"Admin logout returned canonical_logout: {canonical_logout}")
        
        # Verify admin token is now invalid
        response = session.get(
            f"{BASE_URL}/api/admin/check",
            headers={
                "X-Admin-Token": admin_token,
                "X-Directory-Token": session_token
            },
            timeout=30
        )
        
        if response.status_code == 401:
            print_pass("Admin token correctly invalidated after logout")
        else:
            print_fail(f"Admin token still valid after logout! Status: {response.status_code}")
            return False
        
        # Verify PM token is also invalid (shared session invalidation)
        pm_token = portal_tokens.get("pm")
        if pm_token:
            response = session.get(
                f"{BASE_URL}/api/pm/check",
                headers={
                    "X-PM-Token": pm_token,
                    "X-Directory-Token": session_token
                },
                timeout=30
            )
            
            if response.status_code == 401:
                print_pass("PM token also invalidated (shared session)")
            else:
                print_fail(f"PM token still valid after admin logout! Status: {response.status_code}")
                return False
        
        # Verify directory session is invalid
        response = session.get(
            f"{BASE_URL}/api/auth/me-directory",
            headers={"X-Directory-Token": session_token},
            timeout=30
        )
        
        if response.status_code == 401:
            print_pass("Directory session correctly invalidated")
        else:
            print_fail(f"Directory session still valid! Status: {response.status_code}")
            return False
        
        return True
    
    except Exception as e:
        print_fail(f"Exception during admin logout test: {e}")
        return False


def test_behavior_3_pm_logout_wrapper():
    """
    Behavior 3: /api/pm/logout is also a compatibility wrapper over canonical /api/auth/multi-logout
    """
    print_test(3, "/api/pm/logout is a compatibility wrapper")
    
    # Fresh login for this test
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    try:
        response = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN_CREDS,
            timeout=30
        )
        
        if response.status_code != 200:
            print_fail(f"Multi-login failed: {response.status_code}")
            return False
        
        data = response.json()
        
        if data.get("mfa_required"):
            print_info("MFA enabled - skipping PM logout test")
            return True
        
        session_token = data.get("session_token")
        portal_tokens = data.get("portal_tokens", {})
        pm_token = portal_tokens.get("pm")
        
        if not pm_token:
            print_fail("No PM token available")
            return False
        
        # Verify PM token works
        response = session.get(
            f"{BASE_URL}/api/pm/check",
            headers={
                "X-PM-Token": pm_token,
                "X-Directory-Token": session_token
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print_fail(f"PM token not working before logout: {response.status_code}")
            return False
        
        print_pass("PM token works before logout")
        
        # Call /api/pm/logout
        logout_headers = {
            "X-Directory-Token": session_token,
            "X-Admin-Token": portal_tokens.get("admin", ""),
            "X-PM-Token": pm_token,
            "X-HR-Token": portal_tokens.get("hr", ""),
            "X-Safety-Token": portal_tokens.get("safety", ""),
            "X-Shop-Token": portal_tokens.get("shop", ""),
            "X-Dispatch-Token": portal_tokens.get("dispatch", ""),
            "X-FL-Token": portal_tokens.get("field_leadership", ""),
        }
        
        response = session.post(
            f"{BASE_URL}/api/pm/logout",
            headers=logout_headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print_fail(f"PM logout failed with status {response.status_code}")
            return False
        
        data = response.json()
        
        if not data.get("ok"):
            print_fail(f"PM logout response not ok: {data}")
            return False
        
        # Verify it returns canonical metadata
        canonical_logout = data.get("canonical_logout")
        if canonical_logout != "/api/auth/multi-logout":
            print_fail(f"Expected canonical_logout='/api/auth/multi-logout', got '{canonical_logout}'")
            return False
        
        print_pass(f"PM logout returned canonical_logout: {canonical_logout}")
        
        # Verify PM token is now invalid
        response = session.get(
            f"{BASE_URL}/api/pm/check",
            headers={
                "X-PM-Token": pm_token,
                "X-Directory-Token": session_token
            },
            timeout=30
        )
        
        if response.status_code == 401:
            print_pass("PM token correctly invalidated after logout")
        else:
            print_fail(f"PM token still valid after logout! Status: {response.status_code}")
            return False
        
        # Verify directory session is invalid
        response = session.get(
            f"{BASE_URL}/api/auth/me-directory",
            headers={"X-Directory-Token": session_token},
            timeout=30
        )
        
        if response.status_code == 401:
            print_pass("Directory session correctly invalidated")
        else:
            print_fail(f"Directory session still valid! Status: {response.status_code}")
            return False
        
        return True
    
    except Exception as e:
        print_fail(f"Exception during PM logout test: {e}")
        return False


def test_behavior_4_multi_tab_invalidation():
    """
    Behavior 4: Multi-tab invalidation - logout from tab A, protected API in tab B returns 401
    """
    print_test(4, "Multi-tab invalidation proof")
    
    # Create two sessions (simulating two tabs)
    tab_a = requests.Session()
    tab_b = requests.Session()
    
    tab_a.headers.update({"Content-Type": "application/json"})
    tab_b.headers.update({"Content-Type": "application/json"})
    
    try:
        # Login in tab A
        response = tab_a.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN_CREDS,
            timeout=30
        )
        
        if response.status_code != 200:
            print_fail(f"Multi-login failed: {response.status_code}")
            return False
        
        data = response.json()
        
        if data.get("mfa_required"):
            print_info("MFA enabled - skipping multi-tab test")
            return True
        
        session_token = data.get("session_token")
        portal_tokens = data.get("portal_tokens", {})
        admin_token = portal_tokens.get("admin")
        
        if not admin_token:
            print_fail("No admin token available")
            return False
        
        print_pass("Logged in with shared session")
        
        # Verify admin token works in tab B BEFORE logout
        response = tab_b.get(
            f"{BASE_URL}/api/admin/check",
            headers={
                "X-Admin-Token": admin_token,
                "X-Directory-Token": session_token
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print_fail(f"Admin token not working in tab B before logout: {response.status_code}")
            return False
        
        print_pass("Admin token works in tab B before logout")
        
        # Logout from tab A
        logout_headers = {
            "X-Directory-Token": session_token,
            "X-Admin-Token": admin_token,
            "X-PM-Token": portal_tokens.get("pm", ""),
            "X-HR-Token": portal_tokens.get("hr", ""),
            "X-Safety-Token": portal_tokens.get("safety", ""),
            "X-Shop-Token": portal_tokens.get("shop", ""),
            "X-Dispatch-Token": portal_tokens.get("dispatch", ""),
            "X-FL-Token": portal_tokens.get("field_leadership", ""),
        }
        
        response = tab_a.post(
            f"{BASE_URL}/api/auth/multi-logout",
            headers=logout_headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print_fail(f"Logout failed: {response.status_code}")
            return False
        
        print_pass("Logged out from tab A")
        
        # Immediately try to use admin token in tab B
        response = tab_b.get(
            f"{BASE_URL}/api/admin/check",
            headers={
                "X-Admin-Token": admin_token,
                "X-Directory-Token": session_token
            },
            timeout=30
        )
        
        if response.status_code == 401:
            print_pass("Tab B immediately receives 401 after tab A logout (multi-tab invalidation works)")
        else:
            print_fail(f"Tab B still has access after tab A logout! Status: {response.status_code}")
            return False
        
        return True
    
    except Exception as e:
        print_fail(f"Exception during multi-tab test: {e}")
        return False
    finally:
        tab_a.close()
        tab_b.close()


def test_behavior_5_back_after_logout():
    """
    Behavior 5: Back-after-logout - replaying protected request after logout returns 401
    """
    print_test(5, "Back-after-logout proof")
    
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    try:
        # Login
        response = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN_CREDS,
            timeout=30
        )
        
        if response.status_code != 200:
            print_fail(f"Multi-login failed: {response.status_code}")
            return False
        
        data = response.json()
        
        if data.get("mfa_required"):
            print_info("MFA enabled - skipping back-after-logout test")
            return True
        
        session_token = data.get("session_token")
        portal_tokens = data.get("portal_tokens", {})
        admin_token = portal_tokens.get("admin")
        
        if not admin_token:
            print_fail("No admin token available")
            return False
        
        # Make a protected request BEFORE logout
        admin_headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        response = session.get(
            f"{BASE_URL}/api/admin/check",
            headers=admin_headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print_fail(f"Protected request failed before logout: {response.status_code}")
            return False
        
        print_pass("Protected request succeeded before logout")
        
        # Logout
        logout_headers = {
            "X-Directory-Token": session_token,
            "X-Admin-Token": admin_token,
            "X-PM-Token": portal_tokens.get("pm", ""),
            "X-HR-Token": portal_tokens.get("hr", ""),
            "X-Safety-Token": portal_tokens.get("safety", ""),
            "X-Shop-Token": portal_tokens.get("shop", ""),
            "X-Dispatch-Token": portal_tokens.get("dispatch", ""),
            "X-FL-Token": portal_tokens.get("field_leadership", ""),
        }
        
        response = session.post(
            f"{BASE_URL}/api/auth/multi-logout",
            headers=logout_headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print_fail(f"Logout failed: {response.status_code}")
            return False
        
        print_pass("Logged out successfully")
        
        # Replay the SAME protected request (simulating browser back button)
        response = session.get(
            f"{BASE_URL}/api/admin/check",
            headers=admin_headers,
            timeout=30
        )
        
        if response.status_code == 401:
            print_pass("Replayed request correctly returns 401 after logout")
        else:
            print_fail(f"Replayed request still works after logout! Status: {response.status_code}")
            return False
        
        return True
    
    except Exception as e:
        print_fail(f"Exception during back-after-logout test: {e}")
        return False
    finally:
        session.close()


def test_behavior_6_fresh_relogin():
    """
    Behavior 6: Fresh re-login after logout restores access with fresh session, old session stays rejected
    """
    print_test(6, "Fresh re-login after logout")
    
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    try:
        # First login
        response = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN_CREDS,
            timeout=30
        )
        
        if response.status_code != 200:
            print_fail(f"First login failed: {response.status_code}")
            return False
        
        data = response.json()
        
        if data.get("mfa_required"):
            print_info("MFA enabled - skipping fresh relogin test")
            return True
        
        old_session_token = data.get("session_token")
        old_portal_tokens = data.get("portal_tokens", {})
        old_admin_token = old_portal_tokens.get("admin")
        
        if not old_admin_token:
            print_fail("No admin token from first login")
            return False
        
        print_pass(f"First login successful, admin token: {old_admin_token[:20]}...")
        
        # Logout
        logout_headers = {
            "X-Directory-Token": old_session_token,
            "X-Admin-Token": old_admin_token,
            "X-PM-Token": old_portal_tokens.get("pm", ""),
            "X-HR-Token": old_portal_tokens.get("hr", ""),
            "X-Safety-Token": old_portal_tokens.get("safety", ""),
            "X-Shop-Token": old_portal_tokens.get("shop", ""),
            "X-Dispatch-Token": old_portal_tokens.get("dispatch", ""),
            "X-FL-Token": old_portal_tokens.get("field_leadership", ""),
        }
        
        response = session.post(
            f"{BASE_URL}/api/auth/multi-logout",
            headers=logout_headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print_fail(f"Logout failed: {response.status_code}")
            return False
        
        print_pass("Logged out successfully")
        
        # Fresh re-login
        response = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN_CREDS,
            timeout=30
        )
        
        if response.status_code != 200:
            print_fail(f"Re-login failed: {response.status_code}")
            return False
        
        data = response.json()
        
        if data.get("mfa_required"):
            print_info("MFA enabled on re-login")
            return True
        
        new_session_token = data.get("session_token")
        new_portal_tokens = data.get("portal_tokens", {})
        new_admin_token = new_portal_tokens.get("admin")
        
        if not new_admin_token:
            print_fail("No admin token from re-login")
            return False
        
        print_pass(f"Re-login successful, new admin token: {new_admin_token[:20]}...")
        
        # Verify NEW token works
        response = session.get(
            f"{BASE_URL}/api/admin/check",
            headers={
                "X-Admin-Token": new_admin_token,
                "X-Directory-Token": new_session_token
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print_pass("New admin token works after re-login")
        else:
            print_fail(f"New admin token doesn't work! Status: {response.status_code}")
            return False
        
        # Verify OLD token is still rejected
        response = session.get(
            f"{BASE_URL}/api/admin/check",
            headers={
                "X-Admin-Token": old_admin_token,
                "X-Directory-Token": old_session_token
            },
            timeout=30
        )
        
        if response.status_code == 401:
            print_pass("Old admin token correctly stays rejected after re-login")
        else:
            print_fail(f"Old admin token still works after re-login! Status: {response.status_code}")
            return False
        
        # Cleanup - logout the new session
        cleanup_headers = {
            "X-Directory-Token": new_session_token,
            "X-Admin-Token": new_admin_token,
        }
        session.post(f"{BASE_URL}/api/auth/multi-logout", headers=cleanup_headers, timeout=30)
        print_info("Cleaned up new session")
        
        return True
    
    except Exception as e:
        print_fail(f"Exception during fresh relogin test: {e}")
        return False
    finally:
        session.close()


def test_behavior_7_c2_test_suites():
    """
    Behavior 7: C2 test suites pass behaviorally
    """
    print_test(7, "C2 test suites pass behaviorally")
    
    print_info("Running test_c2_15_16_server_side_logout.py...")
    result1 = os.system("cd /app/backend && python -m pytest tests/test_c2_15_16_server_side_logout.py -v --tb=short > /tmp/c2_15_16_results.txt 2>&1")
    
    print_info("Running test_c2_closeout_logout_reconciliation.py...")
    result2 = os.system("cd /app/backend && python -m pytest tests/test_c2_closeout_logout_reconciliation.py -v --tb=short > /tmp/c2_closeout_results.txt 2>&1")
    
    if result1 == 0:
        print_pass("test_c2_15_16_server_side_logout.py passed")
    else:
        print_fail("test_c2_15_16_server_side_logout.py failed")
        os.system("cat /tmp/c2_15_16_results.txt")
    
    if result2 == 0:
        print_pass("test_c2_closeout_logout_reconciliation.py passed")
    else:
        print_fail("test_c2_closeout_logout_reconciliation.py failed")
        os.system("cat /tmp/c2_closeout_results.txt")
    
    return result1 == 0 and result2 == 0


def main():
    """Run all C2 closeout backend verification tests"""
    print_section("C2 CLOSEOUT BACKEND VERIFICATION")
    print(f"Backend URL: {BASE_URL}")
    print(f"Test User: {SUPER_ADMIN_CREDS['email']}")
    
    results = {}
    
    # Test 1: Multi-login returns tokens
    bundle = test_behavior_1_multi_login_returns_tokens()
    results["behavior_1"] = bundle is not None
    
    # Test 2: Admin logout wrapper (uses bundle from test 1)
    if bundle:
        results["behavior_2"] = test_behavior_2_admin_logout_wrapper(bundle)
    else:
        print_info("Skipping behavior 2 (no login bundle)")
        results["behavior_2"] = False
    
    # Test 3: PM logout wrapper (fresh login)
    results["behavior_3"] = test_behavior_3_pm_logout_wrapper()
    
    # Test 4: Multi-tab invalidation
    results["behavior_4"] = test_behavior_4_multi_tab_invalidation()
    
    # Test 5: Back-after-logout
    results["behavior_5"] = test_behavior_5_back_after_logout()
    
    # Test 6: Fresh re-login
    results["behavior_6"] = test_behavior_6_fresh_relogin()
    
    # Test 7: C2 test suites
    results["behavior_7"] = test_behavior_7_c2_test_suites()
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for i, (behavior, result) in enumerate(results.items(), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - Behavior {i}: {behavior}")
    
    print("\n" + "="*70)
    print(f"OVERALL: {passed}/{total} behaviors passed")
    print("="*70)
    
    if passed == total:
        print("\n🎉 ALL C2 CLOSEOUT BACKEND BEHAVIORS VERIFIED SUCCESSFULLY!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} behavior(s) failed - see details above")
        return 1


if __name__ == "__main__":
    exit(main())

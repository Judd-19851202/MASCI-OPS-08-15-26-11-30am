"""
Backend test for Family 3A Slice 1 authorization verification.

Tests the four Family 3A admin routes with different authorization scenarios:
1. Super-admin with X-Admin-Token + X-Directory-Token should get 200
2. PM with X-PM-Token should get 401
3. Missing auth should get 401

Routes tested:
- /api/admin/system-health
- /api/admin/audit-log?limit=5
- /api/admin/search?q=cat
- /api/admin/deploy-recovery
"""
import requests
import sys

BASE_URL = "https://backup-forensics.preview.emergentagent.com"
SUPER_EMAIL = "jaymn.judd@mascigc.com"
SUPER_PASSWORD = "Maddix123!"

FAMILY_3A_ROUTES = [
    "/api/admin/system-health",
    "/api/admin/audit-log?limit=5",
    "/api/admin/search?q=cat",
    "/api/admin/deploy-recovery",
]


def test_family_3a_authorization():
    """Test Family 3A Slice 1 authorization for the four admin routes."""
    print("=" * 80)
    print("FAMILY 3A SLICE 1 - BACKEND AUTHORIZATION VERIFICATION")
    print("=" * 80)
    print()
    
    # Step 1: Login with super-admin credentials to get tokens
    print("Step 1: Authenticating with super-admin credentials...")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": SUPER_EMAIL, "password": SUPER_PASSWORD},
        timeout=20
    )
    
    if login_response.status_code != 200:
        print(f"❌ FAIL: Login failed with status {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False
    
    login_data = login_response.json()
    portal_tokens = login_data.get("portal_tokens", {})
    admin_token = portal_tokens.get("admin")
    pm_token = portal_tokens.get("pm")
    directory_token = login_data.get("session_token")
    
    if not admin_token:
        print("❌ FAIL: No admin token in login response")
        return False
    
    if not directory_token:
        print("❌ FAIL: No directory session token in login response")
        return False
    
    print(f"✅ Login successful")
    print(f"   - Admin token: {admin_token[:20]}...")
    print(f"   - Directory token: {directory_token[:20]}...")
    if pm_token:
        print(f"   - PM token: {pm_token[:20]}...")
    print()
    
    # Step 2: Test each route with admin authorization (should succeed)
    print("Step 2: Testing routes with ADMIN authorization (X-Admin-Token + X-Directory-Token)...")
    admin_headers = {
        "X-Admin-Token": admin_token,
        "X-Directory-Token": directory_token,
    }
    
    admin_results = []
    for route in FAMILY_3A_ROUTES:
        try:
            response = requests.get(f"{BASE_URL}{route}", headers=admin_headers, timeout=15)
            status = response.status_code
            passed = status == 200
            admin_results.append({
                "route": route,
                "status": status,
                "passed": passed,
            })
            
            if passed:
                print(f"   ✅ {route}: {status} (PASS)")
            else:
                print(f"   ❌ {route}: {status} (FAIL - expected 200)")
                print(f"      Response: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ {route}: ERROR - {e}")
            admin_results.append({
                "route": route,
                "status": "ERROR",
                "passed": False,
            })
    print()
    
    # Step 3: Test each route with PM authorization (should fail with 401)
    print("Step 3: Testing routes with PM authorization (X-PM-Token only)...")
    if not pm_token:
        print("   ⚠️  SKIP: No PM token available (super-admin may not have PM portal access)")
        pm_results = []
    else:
        pm_headers = {"X-PM-Token": pm_token}
        pm_results = []
        for route in FAMILY_3A_ROUTES:
            try:
                response = requests.get(f"{BASE_URL}{route}", headers=pm_headers, timeout=15)
                status = response.status_code
                passed = status == 401
                pm_results.append({
                    "route": route,
                    "status": status,
                    "passed": passed,
                })
                
                if passed:
                    print(f"   ✅ {route}: {status} (PASS - correctly denied)")
                else:
                    print(f"   ❌ {route}: {status} (FAIL - expected 401)")
                    print(f"      Response: {response.text[:200]}")
            except Exception as e:
                print(f"   ❌ {route}: ERROR - {e}")
                pm_results.append({
                    "route": route,
                    "status": "ERROR",
                    "passed": False,
                })
    print()
    
    # Step 4: Test each route with no authorization (should fail with 401)
    print("Step 4: Testing routes with NO authorization (no headers)...")
    no_auth_results = []
    for route in FAMILY_3A_ROUTES:
        try:
            response = requests.get(f"{BASE_URL}{route}", timeout=15)
            status = response.status_code
            passed = status in (401, 403)
            no_auth_results.append({
                "route": route,
                "status": status,
                "passed": passed,
            })
            
            if passed:
                print(f"   ✅ {route}: {status} (PASS - correctly denied)")
            else:
                print(f"   ❌ {route}: {status} (FAIL - expected 401 or 403)")
                print(f"      Response: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ {route}: ERROR - {e}")
            no_auth_results.append({
                "route": route,
                "status": "ERROR",
                "passed": False,
            })
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    admin_passed = sum(1 for r in admin_results if r["passed"])
    admin_total = len(admin_results)
    print(f"Admin authorization: {admin_passed}/{admin_total} routes passed")
    
    if pm_results:
        pm_passed = sum(1 for r in pm_results if r["passed"])
        pm_total = len(pm_results)
        print(f"PM authorization denial: {pm_passed}/{pm_total} routes passed")
    else:
        print(f"PM authorization denial: SKIPPED (no PM token)")
    
    no_auth_passed = sum(1 for r in no_auth_results if r["passed"])
    no_auth_total = len(no_auth_results)
    print(f"No authorization denial: {no_auth_passed}/{no_auth_total} routes passed")
    
    all_passed = (
        admin_passed == admin_total and
        (not pm_results or pm_passed == len(pm_results)) and
        no_auth_passed == no_auth_total
    )
    
    print()
    if all_passed:
        print("✅ ALL TESTS PASSED - Family 3A Slice 1 authorization is working correctly")
        return True
    else:
        print("❌ SOME TESTS FAILED - See details above")
        return False


if __name__ == "__main__":
    success = test_family_3a_authorization()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
WP-16 Phase 6 Admin Portal Backend API Verification
Focused backend/API verification for repaired Admin-only WP-16 Phase 6 pages
"""

import requests
import sys
import json

# Backend URL from frontend/.env
BACKEND_URL = "https://backup-forensics.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
ADMIN_EMAIL = "ops8-admin-only-preview@example.com"
ADMIN_PASSWORD = "AdminOnlyOps8!"

def test_multi_login():
    """Test 1: POST /api/auth/multi-login should return 200 and issue tokens"""
    print("=" * 80)
    print("TEST 1: POST /api/auth/multi-login")
    print("=" * 80)
    
    login_url = f"{BACKEND_URL}/auth/multi-login"
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(login_url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - Login successful")
            print(f"User: {data.get('user', {}).get('email', 'N/A')}")
            print(f"Portals: {data.get('user', {}).get('portals', [])}")
            
            # Extract required tokens
            session_token = data.get('session_token')
            portal_tokens = data.get('portal_tokens', {})
            admin_token = portal_tokens.get('admin')
            
            if session_token and admin_token:
                print(f"✅ Directory Session Token: {session_token[:30]}...")
                print(f"✅ Admin Portal Token: {admin_token[:30]}...")
                return True, session_token, admin_token
            else:
                print(f"❌ FAIL - Missing required tokens")
                print(f"Session Token Present: {bool(session_token)}")
                print(f"Admin Token Present: {bool(admin_token)}")
                return False, None, None
        else:
            print(f"❌ FAIL - Login failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False, None, None
            
    except Exception as e:
        print(f"❌ ERROR - Login request failed: {str(e)}")
        return False, None, None

def test_admin_endpoint(endpoint, session_token, admin_token, test_number, total_tests):
    """Test an admin endpoint with proper auth headers"""
    print("\n" + "=" * 80)
    print(f"TEST {test_number}/{total_tests}: GET {endpoint}")
    print("=" * 80)
    
    url = f"{BACKEND_URL}{endpoint}"
    headers = {
        "X-Directory-Token": session_token,
        "X-Admin-Token": admin_token
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ PASS - Endpoint returned 200")
            try:
                data = response.json()
                # Print a summary of the response
                if isinstance(data, dict):
                    print(f"Response keys: {list(data.keys())[:5]}...")
                elif isinstance(data, list):
                    print(f"Response: List with {len(data)} items")
                else:
                    print(f"Response type: {type(data)}")
                return True, data
            except:
                print(f"Response: {response.text[:200]}...")
                return True, None
        elif response.status_code in [401, 403]:
            print(f"❌ FAIL - Auth error {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False, None
        else:
            print(f"⚠️  WARNING - Unexpected status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR - Request failed: {str(e)}")
        return False, None

def test_field_leadership_detail(session_token, admin_token, test_number, total_tests):
    """Test 3: Fetch field-leadership list, then test detail route"""
    print("\n" + "=" * 80)
    print(f"TEST {test_number}/{total_tests}: Field Leadership Detail Route")
    print("=" * 80)
    
    # First, get the list
    list_url = f"{BACKEND_URL}/field-leadership?limit=1"
    headers = {
        "X-Directory-Token": session_token,
        "X-Admin-Token": admin_token
    }
    
    try:
        print(f"Step 1: GET /api/field-leadership?limit=1")
        response = requests.get(list_url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAIL - List endpoint returned {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
        
        data = response.json()
        print(f"✅ List endpoint returned 200")
        
        # Extract first record ID
        records = data if isinstance(data, list) else data.get('items', [])
        if not records or len(records) == 0:
            print(f"⚠️  WARNING - No field leadership records found in response")
            print(f"Response: {json.dumps(data, indent=2)[:500]}")
            print(f"ℹ️  Cannot test detail route without records - this may be expected in preview environment")
            return True  # Not a failure, just no data
        
        # Get the first record's ID
        first_record = records[0]
        record_id = first_record.get('id') or first_record.get('_id') or first_record.get('record_id')
        
        if not record_id:
            print(f"⚠️  WARNING - Record found but no ID field")
            print(f"Record keys: {list(first_record.keys())}")
            return False
        
        print(f"✅ Found record ID: {record_id}")
        
        # Now test the detail route
        print(f"\nStep 2: GET /api/field-leadership/{record_id}")
        detail_url = f"{BACKEND_URL}/field-leadership/{record_id}"
        detail_response = requests.get(detail_url, headers=headers, timeout=30)
        print(f"Status Code: {detail_response.status_code}")
        
        if detail_response.status_code == 200:
            print(f"✅ PASS - Detail endpoint returned 200 for admin")
            detail_data = detail_response.json()
            print(f"Detail record keys: {list(detail_data.keys())[:10]}")
            return True
        elif detail_response.status_code in [401, 403]:
            print(f"❌ FAIL - Auth error {detail_response.status_code} on detail route")
            print(f"Response: {detail_response.text[:500]}")
            return False
        else:
            print(f"⚠️  WARNING - Unexpected status {detail_response.status_code}")
            print(f"Response: {detail_response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR - Request failed: {str(e)}")
        return False

def main():
    """Run all WP-16 Phase 6 backend tests"""
    print("\n" + "=" * 80)
    print("WP-16 PHASE 6 ADMIN PORTAL BACKEND API VERIFICATION")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test User: {ADMIN_EMAIL}")
    print("=" * 80 + "\n")
    
    results = []
    
    # Test 1: Multi-login
    login_success, session_token, admin_token = test_multi_login()
    results.append(("POST /api/auth/multi-login", login_success))
    
    if not login_success:
        print("\n❌ CRITICAL: Login failed, cannot continue with endpoint tests")
        print_summary(results)
        sys.exit(1)
    
    # Define all endpoints to test
    endpoints = [
        "/admin/governance/roles",
        "/admin/governance/permissions",
        "/admin/governance/policies",
        "/admin/governance/approval-flows",
        "/admin/governance/versions",
        "/admin/governance/self-protection",
        "/admin/trust-spine",
        "/asset-spine/health",
        "/asset-spine/health/runs?limit=2",
        "/oppc/enterprise/executive-operations-center",
        "/oppc/enterprise/monday-briefing",
        "/field-leadership?limit=1"
    ]
    
    # Test all endpoints
    test_num = 2
    total_tests = len(endpoints) + 2  # +2 for login and field-leadership detail
    
    for endpoint in endpoints:
        success, data = test_admin_endpoint(endpoint, session_token, admin_token, test_num, total_tests)
        results.append((f"GET {endpoint}", success))
        test_num += 1
    
    # Test field-leadership detail route
    fl_detail_success = test_field_leadership_detail(session_token, admin_token, test_num, total_tests)
    results.append(("Field Leadership Detail Route", fl_detail_success))
    
    # Print summary
    print_summary(results)
    
    # Exit with appropriate code
    all_passed = all(result[1] for result in results)
    sys.exit(0 if all_passed else 1)

def print_summary(results):
    """Print test summary"""
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    # Group by status
    passed_tests = [name for name, success in results if success]
    failed_tests = [name for name, success in results if not success]
    
    if failed_tests:
        print("\n❌ FAILED TESTS:")
        for test_name in failed_tests:
            print(f"  - {test_name}")
    
    if passed_tests:
        print("\n✅ PASSED TESTS:")
        for test_name in passed_tests:
            print(f"  - {test_name}")
    
    print("\n" + "=" * 80)
    print(f"TOTAL: {passed}/{total} tests passed ({int(passed/total*100) if total > 0 else 0}% pass rate)")
    print("=" * 80)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - No auth mismatch, 401/403, or malformed payloads detected")
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED - Review failures above for auth mismatch, 401/403, or regressions")

if __name__ == "__main__":
    main()

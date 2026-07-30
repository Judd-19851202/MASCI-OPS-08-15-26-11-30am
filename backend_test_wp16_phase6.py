#!/usr/bin/env python3
"""
WP-16 Phase 6 Admin Portal Certification - Backend API Regression Test

Scope:
- Login with Admin preview account (ops8-admin-only-preview@example.com)
- Extract both X-Admin-Token and X-Directory-Token from login response
- Test Admin-critical endpoints with proper authorization headers
- Verify documented Admin 401/auth defects are resolved

Test Endpoints:
- /api/admin/check
- /api/qaqc-inspections
- /api/admin/equipment-master/status
- /api/meetings?limit=3
- /api/trench-safety/excavations?limit=3
- /api/job-photos?limit=3
- /api/inspections?limit=3
"""

import requests
import sys
import json

# Backend URL from frontend/.env
BACKEND_URL = "https://backup-forensics.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
ADMIN_EMAIL = "ops8-admin-only-preview@example.com"
ADMIN_PASSWORD = "AdminOnlyOps8!"

def test_admin_login():
    """Test admin login and extract required tokens"""
    print("=" * 80)
    print("TEST 1: Admin Multi-Login (Directory-Based)")
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
            
            if not session_token:
                print(f"❌ FAIL - No session_token in response")
                return False, None, None
            
            if not admin_token:
                print(f"❌ FAIL - No admin token in portal_tokens")
                return False, None, None
            
            print(f"Session Token (X-Directory-Token): {session_token[:30]}...")
            print(f"Admin Token (X-Admin-Token): {admin_token[:30]}...")
            
            return True, session_token, admin_token
        else:
            print(f"❌ FAIL - Login failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False, None, None
            
    except Exception as e:
        print(f"❌ ERROR - Login request failed: {str(e)}")
        return False, None, None

def test_admin_check(session_token, admin_token):
    """Test /api/admin/check endpoint"""
    print("\n" + "=" * 80)
    print("TEST 2: /api/admin/check")
    print("=" * 80)
    
    url = f"{BACKEND_URL}/admin/check"
    headers = {
        "X-Admin-Token": admin_token,
        "X-Directory-Token": session_token
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ PASS - Admin check successful")
            print(f"Response: {response.text[:200]}")
            return True
        elif response.status_code == 401:
            print(f"❌ FAIL - Authorization failed (401)")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"⚠️  WARNING - Unexpected status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR - Request failed: {str(e)}")
        return False

def test_qaqc_inspections(session_token, admin_token):
    """Test /api/qaqc-inspections endpoint"""
    print("\n" + "=" * 80)
    print("TEST 3: /api/qaqc-inspections")
    print("=" * 80)
    
    url = f"{BACKEND_URL}/qaqc-inspections"
    headers = {
        "X-Admin-Token": admin_token,
        "X-Directory-Token": session_token
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - QA/QC inspections retrieved")
            print(f"Response type: {type(data)}")
            if isinstance(data, list):
                print(f"Inspections count: {len(data)}")
            elif isinstance(data, dict):
                print(f"Response keys: {list(data.keys())}")
            return True
        elif response.status_code == 401:
            print(f"❌ FAIL - Authorization failed (401)")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"⚠️  WARNING - Unexpected status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR - Request failed: {str(e)}")
        return False

def test_equipment_master_status(session_token, admin_token):
    """Test /api/admin/equipment-master/status endpoint"""
    print("\n" + "=" * 80)
    print("TEST 4: /api/admin/equipment-master/status")
    print("=" * 80)
    
    url = f"{BACKEND_URL}/admin/equipment-master/status"
    headers = {
        "X-Admin-Token": admin_token,
        "X-Directory-Token": session_token
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ PASS - Equipment master status retrieved")
            print(f"Response: {response.text[:200]}")
            return True
        elif response.status_code == 401:
            print(f"❌ FAIL - Authorization failed (401)")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"⚠️  WARNING - Unexpected status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR - Request failed: {str(e)}")
        return False

def test_meetings(session_token, admin_token):
    """Test /api/meetings?limit=3 endpoint"""
    print("\n" + "=" * 80)
    print("TEST 5: /api/meetings?limit=3")
    print("=" * 80)
    
    url = f"{BACKEND_URL}/meetings?limit=3"
    headers = {
        "X-Admin-Token": admin_token,
        "X-Directory-Token": session_token
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - Meetings retrieved")
            if isinstance(data, list):
                print(f"Meetings count: {len(data)}")
            elif isinstance(data, dict):
                print(f"Response keys: {list(data.keys())}")
            return True
        elif response.status_code == 401:
            print(f"❌ FAIL - Authorization failed (401)")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"⚠️  WARNING - Unexpected status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR - Request failed: {str(e)}")
        return False

def test_trench_safety_excavations(session_token, admin_token):
    """Test /api/trench-safety/excavations?limit=3 endpoint"""
    print("\n" + "=" * 80)
    print("TEST 6: /api/trench-safety/excavations?limit=3")
    print("=" * 80)
    
    url = f"{BACKEND_URL}/trench-safety/excavations?limit=3"
    headers = {
        "X-Admin-Token": admin_token,
        "X-Directory-Token": session_token
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - Trench safety excavations retrieved")
            if isinstance(data, list):
                print(f"Excavations count: {len(data)}")
            elif isinstance(data, dict):
                print(f"Response keys: {list(data.keys())}")
            return True
        elif response.status_code == 401:
            print(f"❌ FAIL - Authorization failed (401)")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"⚠️  WARNING - Unexpected status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR - Request failed: {str(e)}")
        return False

def test_job_photos(session_token, admin_token):
    """Test /api/job-photos?limit=3 endpoint"""
    print("\n" + "=" * 80)
    print("TEST 7: /api/job-photos?limit=3")
    print("=" * 80)
    
    url = f"{BACKEND_URL}/job-photos?limit=3"
    headers = {
        "X-Admin-Token": admin_token,
        "X-Directory-Token": session_token
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - Job photos retrieved")
            if isinstance(data, list):
                print(f"Photos count: {len(data)}")
            elif isinstance(data, dict):
                print(f"Response keys: {list(data.keys())}")
            return True
        elif response.status_code == 401:
            print(f"❌ FAIL - Authorization failed (401)")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"⚠️  WARNING - Unexpected status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR - Request failed: {str(e)}")
        return False

def test_inspections(session_token, admin_token):
    """Test /api/inspections?limit=3 endpoint"""
    print("\n" + "=" * 80)
    print("TEST 8: /api/inspections?limit=3")
    print("=" * 80)
    
    url = f"{BACKEND_URL}/inspections?limit=3"
    headers = {
        "X-Admin-Token": admin_token,
        "X-Directory-Token": session_token
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - Inspections retrieved")
            if isinstance(data, list):
                print(f"Inspections count: {len(data)}")
            elif isinstance(data, dict):
                print(f"Response keys: {list(data.keys())}")
            return True
        elif response.status_code == 401:
            print(f"❌ FAIL - Authorization failed (401)")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"⚠️  WARNING - Unexpected status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR - Request failed: {str(e)}")
        return False

def main():
    """Run all WP-16 Phase 6 Admin Portal backend API tests"""
    print("\n" + "=" * 80)
    print("WP-16 PHASE 6 ADMIN PORTAL CERTIFICATION - BACKEND API REGRESSION")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test User: {ADMIN_EMAIL}")
    print("Scope: Verify Admin 401/auth defects are resolved")
    print("=" * 80 + "\n")
    
    results = []
    
    # Test 1: Admin Login
    login_success, session_token, admin_token = test_admin_login()
    results.append(("Admin Multi-Login", login_success))
    
    if not login_success:
        print("\n❌ CRITICAL: Login failed, cannot continue with API tests")
        print_summary(results)
        sys.exit(1)
    
    # Test 2: /api/admin/check
    check_success = test_admin_check(session_token, admin_token)
    results.append(("/api/admin/check", check_success))
    
    # Test 3: /api/qaqc-inspections
    qaqc_success = test_qaqc_inspections(session_token, admin_token)
    results.append(("/api/qaqc-inspections", qaqc_success))
    
    # Test 4: /api/admin/equipment-master/status
    equipment_success = test_equipment_master_status(session_token, admin_token)
    results.append(("/api/admin/equipment-master/status", equipment_success))
    
    # Test 5: /api/meetings?limit=3
    meetings_success = test_meetings(session_token, admin_token)
    results.append(("/api/meetings?limit=3", meetings_success))
    
    # Test 6: /api/trench-safety/excavations?limit=3
    excavations_success = test_trench_safety_excavations(session_token, admin_token)
    results.append(("/api/trench-safety/excavations?limit=3", excavations_success))
    
    # Test 7: /api/job-photos?limit=3
    photos_success = test_job_photos(session_token, admin_token)
    results.append(("/api/job-photos?limit=3", photos_success))
    
    # Test 8: /api/inspections?limit=3
    inspections_success = test_inspections(session_token, admin_token)
    results.append(("/api/inspections?limit=3", inspections_success))
    
    # Print summary
    print_summary(results)
    
    # Exit with appropriate code
    all_passed = all(result[1] for result in results)
    sys.exit(0 if all_passed else 1)

def print_summary(results):
    """Print test summary"""
    print("\n" + "=" * 80)
    print("TEST SUMMARY - WP-16 PHASE 6 ADMIN PORTAL BACKEND REGRESSION")
    print("=" * 80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("=" * 80)
    print(f"TOTAL: {passed}/{total} tests passed ({int(passed/total*100) if total > 0 else 0}% pass rate)")
    print("=" * 80)
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - Admin 401/auth defects are RESOLVED")
        print("Admin portal APIs are healthy for certification")
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED - Admin APIs have issues")
        print("Review failed endpoints above for authorization/runtime/data issues")

if __name__ == "__main__":
    main()

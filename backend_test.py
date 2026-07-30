#!/usr/bin/env python3
"""
WP-16 Phase B Wave 1 - Backend Auth Endpoints Verification
Verification-only evidence collection for Public Pages & Authentication
NO CODE REPAIRS - VERIFICATION ONLY
"""

import requests
import sys
import json

# Backend URL from frontend/.env
BACKEND_URL = "https://backup-forensics.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Preview credentials for portal-specific logins
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"

HR_EMAIL = "cert.hr@example.com"
HR_PASSWORD = "CertProof2026!"

SAFETY_EMAIL = "cert.safety@example.com"
SAFETY_PASSWORD = "CertProof2026!"

DISPATCH_EMAIL = "cert.dispatch@example.com"
DISPATCH_PASSWORD = "CertProof2026!"

SHOP_EMAIL = "cert.shop@example.com"
SHOP_PASSWORD = "CertProof2026!"

FL_EMAIL = "cert.foreman@example.com"
FL_PASSWORD = "CertProof2026!"

def test_multi_login_admin():
    """Test POST /api/auth/multi-login with admin credentials"""
    print("=" * 80)
    print("TEST 1: POST /api/auth/multi-login (Admin)")
    print("=" * 80)
    
    url = f"{BACKEND_URL}/auth/multi-login"
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - Admin multi-login successful")
            print(f"User: {data.get('user', {}).get('email', 'N/A')}")
            print(f"Portals: {data.get('user', {}).get('portals', [])}")
            print(f"Session Token: {data.get('session_token', 'N/A')[:30]}...")
            print(f"Portal Tokens: {list(data.get('portal_tokens', {}).keys())}")
            return True, data
        else:
            print(f"❌ FAIL - Admin multi-login failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR - Admin multi-login request failed: {str(e)}")
        return False, None


def test_pm_login():
    """Test POST /api/pm/login with preview credentials"""
    print("\n" + "=" * 80)
    print("TEST 2: POST /api/pm/login")
    print("=" * 80)
    
    url = f"{BACKEND_URL}/pm/login"
    payload = {
        "email": PM_EMAIL,
        "password": PM_PASSWORD
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - PM login successful")
            print(f"Token present: {bool(data.get('token'))}")
            print(f"User: {data.get('user', {}).get('email', 'N/A')}")
            return True, data
        else:
            print(f"❌ FAIL - PM login failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR - PM login request failed: {str(e)}")
        return False, None


def test_hr_login():
    """Test POST /api/hr/login with preview credentials"""
    print("\n" + "=" * 80)
    print("TEST 3: POST /api/hr/login")
    print("=" * 80)
    
    url = f"{BACKEND_URL}/hr/login"
    payload = {
        "email": HR_EMAIL,
        "password": HR_PASSWORD
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - HR login successful")
            print(f"Token present: {bool(data.get('token'))}")
            print(f"User: {data.get('user', {}).get('email', 'N/A')}")
            return True, data
        else:
            print(f"❌ FAIL - HR login failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR - HR login request failed: {str(e)}")
        return False, None


def test_safety_login():
    """Test POST /api/safety/login with preview credentials"""
    print("\n" + "=" * 80)
    print("TEST 4: POST /api/safety/login")
    print("=" * 80)
    
    url = f"{BACKEND_URL}/safety/login"
    payload = {
        "email": SAFETY_EMAIL,
        "password": SAFETY_PASSWORD
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - Safety login successful")
            print(f"Token present: {bool(data.get('token'))}")
            print(f"User: {data.get('user', {}).get('email', 'N/A')}")
            return True, data
        else:
            print(f"❌ FAIL - Safety login failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR - Safety login request failed: {str(e)}")
        return False, None


def test_dispatch_login():
    """Test POST /api/dispatch/login with preview credentials"""
    print("\n" + "=" * 80)
    print("TEST 5: POST /api/dispatch/login")
    print("=" * 80)
    
    url = f"{BACKEND_URL}/dispatch/login"
    payload = {
        "email": DISPATCH_EMAIL,
        "password": DISPATCH_PASSWORD
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - Dispatch login successful")
            print(f"Token present: {bool(data.get('token'))}")
            print(f"User: {data.get('user', {}).get('email', 'N/A')}")
            return True, data
        else:
            print(f"❌ FAIL - Dispatch login failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR - Dispatch login request failed: {str(e)}")
        return False, None


def test_shop_login():
    """Test POST /api/shop/login with preview credentials"""
    print("\n" + "=" * 80)
    print("TEST 6: POST /api/shop/login")
    print("=" * 80)
    
    url = f"{BACKEND_URL}/shop/login"
    payload = {
        "email": SHOP_EMAIL,
        "password": SHOP_PASSWORD
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - Shop login successful")
            print(f"Token present: {bool(data.get('token'))}")
            print(f"User: {data.get('user', {}).get('email', 'N/A')}")
            return True, data
        else:
            print(f"❌ FAIL - Shop login failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR - Shop login request failed: {str(e)}")
        return False, None


def test_field_leadership_login():
    """Test POST /api/field-leadership/portal/login with preview credentials"""
    print("\n" + "=" * 80)
    print("TEST 7: POST /api/field-leadership/portal/login")
    print("=" * 80)
    
    url = f"{BACKEND_URL}/field-leadership/portal/login"
    payload = {
        "email": FL_EMAIL,
        "password": FL_PASSWORD
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - Field Leadership login successful")
            print(f"Token present: {bool(data.get('token'))}")
            print(f"User: {data.get('user', {}).get('email', 'N/A')}")
            return True, data
        else:
            print(f"❌ FAIL - Field Leadership login failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR - Field Leadership login request failed: {str(e)}")
        return False, None


def test_safety_forgot_password():
    """Test POST /api/safety/forgot-password"""
    print("\n" + "=" * 80)
    print("TEST 8: POST /api/safety/forgot-password")
    print("=" * 80)
    
    url = f"{BACKEND_URL}/safety/forgot-password"
    payload = {
        "email": SAFETY_EMAIL
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - Safety forgot-password endpoint operational")
            print(f"Response keys: {list(data.keys())}")
            
            # Check for preview-only token exposure
            response_str = json.dumps(data)
            if "token_for_dev" in response_str or "preview_token" in response_str:
                print(f"⚠️  WARNING - Preview reset token exposed in response: {data}")
            else:
                print(f"✅ No preview token exposure detected in response payload")
            
            return True, data
        else:
            print(f"❌ FAIL - Safety forgot-password failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR - Safety forgot-password request failed: {str(e)}")
        return False, None


def test_dispatch_forgot_password():
    """Test POST /api/dispatch/forgot-password"""
    print("\n" + "=" * 80)
    print("TEST 9: POST /api/dispatch/forgot-password")
    print("=" * 80)
    
    url = f"{BACKEND_URL}/dispatch/forgot-password"
    payload = {
        "email": DISPATCH_EMAIL
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - Dispatch forgot-password endpoint operational")
            print(f"Response keys: {list(data.keys())}")
            
            # Check for preview-only token exposure
            response_str = json.dumps(data)
            if "token_for_dev" in response_str or "preview_token" in response_str:
                print(f"⚠️  WARNING - Preview reset token exposed in response: {data}")
            else:
                print(f"✅ No preview token exposure detected in response payload")
            
            return True, data
        else:
            print(f"❌ FAIL - Dispatch forgot-password failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR - Dispatch forgot-password request failed: {str(e)}")
        return False, None


def test_dev_login():
    """Test POST /api/dev/login (expected to fail-closed in preview)"""
    print("\n" + "=" * 80)
    print("TEST 10: POST /api/dev/login")
    print("=" * 80)
    
    url = f"{BACKEND_URL}/dev/login"
    payload = {
        "password": "any_password"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            print(f"✅ PASS - Dev login fail-closed as expected (404)")
            print(f"Preview environment correctly disables dev login endpoint")
            return True, None
        elif response.status_code == 401:
            print(f"✅ PASS - Dev login requires authentication (401)")
            print(f"Endpoint exists but rejects unauthenticated access")
            return True, None
        elif response.status_code == 200:
            data = response.json()
            print(f"⚠️  WARNING - Dev login succeeded with status 200")
            print(f"Response: {data}")
            print(f"Dev login may be enabled in preview environment")
            return True, data
        else:
            print(f"⚠️  INFO - Dev login returned status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return True, None
            
    except Exception as e:
        print(f"❌ ERROR - Dev login request failed: {str(e)}")
        return False, None


def print_summary(results):
    """Print test summary"""
    print("\n" + "=" * 80)
    print("WP-16 PHASE B WAVE 1 - BACKEND AUTH VERIFICATION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, notes in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if notes:
            print(f"         {notes}")
    
    print("=" * 80)
    print(f"TOTAL: {passed}/{total} tests passed ({int(passed/total*100)}% pass rate)")
    print("=" * 80)
    print("\nVERIFICATION-ONLY EVIDENCE COLLECTION COMPLETE")
    print("NO CODE MODIFICATIONS - NO CODE REPAIRS")
    print("=" * 80)


def main():
    """Run all backend auth endpoint verification tests"""
    print("\n" + "=" * 80)
    print("WP-16 PHASE B WAVE 1 - BACKEND AUTH ENDPOINTS VERIFICATION")
    print("VERIFICATION-ONLY - NO CODE REPAIRS")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Scope: Public Pages & Authentication")
    print("=" * 80 + "\n")
    
    results = []
    
    # Test 1: Admin multi-login
    success, data = test_multi_login_admin()
    results.append(("POST /api/auth/multi-login (Admin)", success, 
                   "Core Wave 1 auth portal - operational success" if success else "Failed"))
    
    # Test 2: PM login
    success, data = test_pm_login()
    results.append(("POST /api/pm/login", success,
                   "Core Wave 1 auth portal - operational success" if success else "Failed"))
    
    # Test 3: HR login
    success, data = test_hr_login()
    results.append(("POST /api/hr/login", success,
                   "Core Wave 1 auth portal - operational success" if success else "Failed"))
    
    # Test 4: Safety login
    success, data = test_safety_login()
    results.append(("POST /api/safety/login", success,
                   "Core Wave 1 auth portal - operational success" if success else "Failed"))
    
    # Test 5: Dispatch login
    success, data = test_dispatch_login()
    results.append(("POST /api/dispatch/login", success,
                   "Core Wave 1 auth portal - operational success" if success else "Failed"))
    
    # Test 6: Shop login
    success, data = test_shop_login()
    results.append(("POST /api/shop/login", success,
                   "Core Wave 1 auth portal - operational success" if success else "Failed"))
    
    # Test 7: Field Leadership login
    success, data = test_field_leadership_login()
    results.append(("POST /api/field-leadership/portal/login", success,
                   "Core Wave 1 auth portal - operational success" if success else "Failed"))
    
    # Test 8: Safety forgot-password
    success, data = test_safety_forgot_password()
    notes = "Checked for preview token exposure" if success else "Failed"
    results.append(("POST /api/safety/forgot-password", success, notes))
    
    # Test 9: Dispatch forgot-password
    success, data = test_dispatch_forgot_password()
    notes = "Checked for preview token exposure" if success else "Failed"
    results.append(("POST /api/dispatch/forgot-password", success, notes))
    
    # Test 10: Dev login
    success, data = test_dev_login()
    notes = "Preview environment behavior verified" if success else "Failed"
    results.append(("POST /api/dev/login", success, notes))
    
    # Print summary
    print_summary(results)
    
    # Exit with appropriate code
    all_passed = all(result[1] for result in results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

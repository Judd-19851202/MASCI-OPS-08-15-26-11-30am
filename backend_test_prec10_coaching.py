"""
Backend API Testing for PRE-C10 Progressive Disclosure/Coaching Closure Batch
Tests the exact API behaviors specified in the review request.

Focus:
1. Multi-login/auth contracts for Super Admin and HR preview users
2. HR route access for /hr/employees after login
3. Guidance tips API for specific form keys: employee-lifecycle, corrective, time-verification, dispatch.handoff
4. No auth/session regression from frontend-only coaching refactor
5. Report any 4xx/5xx or contract drift
"""
import requests
import json
import sys
from typing import Dict, Any, Optional

# Backend URL from frontend/.env
BACKEND_URL = "https://masci-audit-hub.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"

HR_EMAIL = "cert.hr@example.com"
HR_PASSWORD = "CertProof2026!"

DISPATCH_EMAIL = "cert.dispatch@example.com"
DISPATCH_PASSWORD = "CertProof2026!"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test_header(test_name: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}TEST: {test_name}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*80}{Colors.END}")

def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, test_name: str, details: str = ""):
        self.passed.append((test_name, details))
        print_success(f"{test_name}: PASS {details}")
    
    def add_fail(self, test_name: str, details: str):
        self.failed.append((test_name, details))
        print_error(f"{test_name}: FAIL - {details}")
    
    def add_warning(self, test_name: str, details: str):
        self.warnings.append((test_name, details))
        print_warning(f"{test_name}: WARNING - {details}")
    
    def print_summary(self):
        print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.GREEN}Passed: {len(self.passed)}{Colors.END}")
        print(f"{Colors.RED}Failed: {len(self.failed)}{Colors.END}")
        print(f"{Colors.YELLOW}Warnings: {len(self.warnings)}{Colors.END}")
        
        if self.failed:
            print(f"\n{Colors.RED}{Colors.BOLD}FAILED TESTS:{Colors.END}")
            for test_name, details in self.failed:
                print(f"  {Colors.RED}✗ {test_name}: {details}{Colors.END}")
        
        if self.warnings:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}WARNINGS:{Colors.END}")
            for test_name, details in self.warnings:
                print(f"  {Colors.YELLOW}⚠ {test_name}: {details}{Colors.END}")
        
        return len(self.failed) == 0

results = TestResults()

def test_super_admin_multi_login() -> Optional[Dict[str, Any]]:
    """
    Test 1: POST /api/auth/multi-login - Super Admin
    Expected: Returns portal_tokens.admin, portal_tokens.hr, and session_token
    """
    print_test_header("1. POST /api/auth/multi-login - Super Admin Login")
    
    try:
        url = f"{BACKEND_URL}/auth/multi-login"
        payload = {
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }
        
        print_info(f"POST {url}")
        print_info(f"Email: {SUPER_ADMIN_EMAIL}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("super-admin-login", f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return None
        
        data = response.json()
        
        # Check for session_token
        if "session_token" not in data:
            results.add_fail("super-admin-login", "Missing session_token in response")
            return None
        
        session_token = data.get("session_token")
        print_success(f"session_token present: {session_token[:20]}...")
        
        # Check for portal_tokens
        if "portal_tokens" not in data:
            results.add_fail("super-admin-login", "Missing portal_tokens in response")
            return None
        
        portal_tokens = data.get("portal_tokens", {})
        
        # Check for admin token
        if "admin" not in portal_tokens or not portal_tokens["admin"]:
            results.add_fail("super-admin-login", "Missing portal_tokens.admin")
            return None
        
        admin_token = portal_tokens["admin"]
        print_success(f"portal_tokens.admin present: {admin_token[:20]}...")
        
        results.add_pass("super-admin-login", "Super Admin login successful with required tokens")
        
        return {
            "session_token": session_token,
            "admin_token": admin_token,
            "portal_tokens": portal_tokens
        }
        
    except Exception as e:
        results.add_fail("super-admin-login", f"Exception: {str(e)}")
        return None

def test_hr_multi_login() -> Optional[Dict[str, Any]]:
    """
    Test 2: POST /api/auth/multi-login - HR User
    Expected: Returns portal_tokens.hr and session_token
    """
    print_test_header("2. POST /api/auth/multi-login - HR User Login")
    
    try:
        url = f"{BACKEND_URL}/auth/multi-login"
        payload = {
            "email": HR_EMAIL,
            "password": HR_PASSWORD
        }
        
        print_info(f"POST {url}")
        print_info(f"Email: {HR_EMAIL}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("hr-login", f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return None
        
        data = response.json()
        
        # Check for session_token
        if "session_token" not in data:
            results.add_fail("hr-login", "Missing session_token in response")
            return None
        
        session_token = data.get("session_token")
        print_success(f"session_token present: {session_token[:20]}...")
        
        # Check for portal_tokens
        if "portal_tokens" not in data:
            results.add_fail("hr-login", "Missing portal_tokens in response")
            return None
        
        portal_tokens = data.get("portal_tokens", {})
        
        # Check for hr token
        if "hr" not in portal_tokens or not portal_tokens["hr"]:
            results.add_fail("hr-login", "Missing portal_tokens.hr")
            return None
        
        hr_token = portal_tokens["hr"]
        print_success(f"portal_tokens.hr present: {hr_token[:20]}...")
        
        results.add_pass("hr-login", "HR user login successful with required tokens")
        
        return {
            "session_token": session_token,
            "hr_token": hr_token,
            "portal_tokens": portal_tokens
        }
        
    except Exception as e:
        results.add_fail("hr-login", f"Exception: {str(e)}")
        return None

def test_dispatch_multi_login() -> Optional[Dict[str, Any]]:
    """
    Test 3: POST /api/auth/multi-login - Dispatch User
    Expected: Returns portal_tokens.dispatch and session_token
    """
    print_test_header("3. POST /api/auth/multi-login - Dispatch User Login")
    
    try:
        url = f"{BACKEND_URL}/auth/multi-login"
        payload = {
            "email": DISPATCH_EMAIL,
            "password": DISPATCH_PASSWORD
        }
        
        print_info(f"POST {url}")
        print_info(f"Email: {DISPATCH_EMAIL}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("dispatch-login", f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return None
        
        data = response.json()
        
        # Check for session_token
        if "session_token" not in data:
            results.add_fail("dispatch-login", "Missing session_token in response")
            return None
        
        session_token = data.get("session_token")
        print_success(f"session_token present: {session_token[:20]}...")
        
        # Check for portal_tokens
        if "portal_tokens" not in data:
            results.add_fail("dispatch-login", "Missing portal_tokens in response")
            return None
        
        portal_tokens = data.get("portal_tokens", {})
        
        # Check for dispatch token
        if "dispatch" not in portal_tokens or not portal_tokens["dispatch"]:
            results.add_fail("dispatch-login", "Missing portal_tokens.dispatch")
            return None
        
        dispatch_token = portal_tokens["dispatch"]
        print_success(f"portal_tokens.dispatch present: {dispatch_token[:20]}...")
        
        results.add_pass("dispatch-login", "Dispatch user login successful with required tokens")
        
        return {
            "session_token": session_token,
            "dispatch_token": dispatch_token,
            "portal_tokens": portal_tokens
        }
        
    except Exception as e:
        results.add_fail("dispatch-login", f"Exception: {str(e)}")
        return None

def test_hr_employees_access(hr_token: str, session_token: str):
    """
    Test 4: GET /api/hr/employees - HR Route Access
    Expected: Returns 200 with items list after HR login
    """
    print_test_header("4. GET /api/hr/employees - HR Route Access After Login")
    
    try:
        url = f"{BACKEND_URL}/hr/employees"
        headers = {
            "X-HR-Token": hr_token,
            "X-Directory-Token": session_token
        }
        
        print_info(f"GET {url}")
        print_info(f"Headers: X-HR-Token, X-Directory-Token")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("hr-employees-access", f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return
        
        data = response.json()
        
        # Check for items key
        if "items" not in data:
            results.add_fail("hr-employees-access", "Missing 'items' key in response")
            return
        
        items = data["items"]
        if not isinstance(items, list):
            results.add_fail("hr-employees-access", "'items' is not an array")
            return
        
        print_success(f"items array present with {len(items)} employees")
        
        # Check for count key
        if "count" in data:
            print_success(f"count: {data['count']}")
        
        results.add_pass("hr-employees-access", f"HR route access working correctly ({len(items)} employees)")
        
    except Exception as e:
        results.add_fail("hr-employees-access", f"Exception: {str(e)}")

def test_guidance_tips_api(form_keys: list):
    """
    Test 5: GET /api/guidance/tips - Guidance Tips API for specific form keys
    Expected: Returns 200 with tips array for each form_key
    Form keys to test: employee-lifecycle, corrective, time-verification, dispatch.handoff
    """
    print_test_header("5. GET /api/guidance/tips - Guidance Tips API for Form Keys")
    
    all_passed = True
    
    for form_key in form_keys:
        try:
            url = f"{BACKEND_URL}/guidance/tips?form_key={form_key}"
            
            print_info(f"\nTesting form_key: {form_key}")
            print_info(f"GET {url}")
            
            response = requests.get(url, timeout=30)
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code != 200:
                results.add_fail(f"guidance-tips-{form_key}", f"Expected 200, got {response.status_code}")
                print_error(f"Response: {response.text[:500]}")
                all_passed = False
                continue
            
            data = response.json()
            
            # Check for required keys
            if "form_key" not in data:
                results.add_fail(f"guidance-tips-{form_key}", "Missing 'form_key' in response")
                all_passed = False
                continue
            
            if "tips" not in data:
                results.add_fail(f"guidance-tips-{form_key}", "Missing 'tips' array in response")
                all_passed = False
                continue
            
            tips = data["tips"]
            if not isinstance(tips, list):
                results.add_fail(f"guidance-tips-{form_key}", "'tips' is not an array")
                all_passed = False
                continue
            
            print_success(f"form_key '{form_key}': {len(tips)} tips returned")
            
            # Check tip structure if tips exist
            if len(tips) > 0:
                first_tip = tips[0]
                if "id" in first_tip and "content" in first_tip:
                    print_success(f"  Tip structure valid (has 'id' and 'content')")
                else:
                    results.add_warning(f"guidance-tips-{form_key}", "Tip structure missing 'id' or 'content'")
            
        except Exception as e:
            results.add_fail(f"guidance-tips-{form_key}", f"Exception: {str(e)}")
            all_passed = False
    
    if all_passed:
        results.add_pass("guidance-tips-api", f"All {len(form_keys)} form keys returned valid responses")
    else:
        results.add_fail("guidance-tips-api", "One or more form keys failed")

def test_auth_session_regression(admin_token: str, hr_token: str, dispatch_token: str, 
                                  admin_session: str, hr_session: str, dispatch_session: str):
    """
    Test 6: Auth/Session Regression Check
    Verify no auth/session regression was introduced by frontend-only coaching refactor
    Re-test key endpoints to ensure no 401/403 errors
    """
    print_test_header("6. Auth/Session Regression Check - Verify No 401/403 Errors")
    
    endpoints = [
        ("hr-employees-admin", f"{BACKEND_URL}/hr/employees", 
         {"X-Admin-Token": admin_token, "X-Directory-Token": admin_session}),
        ("hr-employees-hr", f"{BACKEND_URL}/hr/employees", 
         {"X-HR-Token": hr_token, "X-Directory-Token": hr_session}),
        ("guidance-tips-public", f"{BACKEND_URL}/guidance/tips?form_key=employee-lifecycle", {}),
    ]
    
    all_passed = True
    for name, url, headers in endpoints:
        try:
            print_info(f"\nTesting: {name}")
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code in [401, 403]:
                results.add_fail(f"auth-regression-{name}", f"Got {response.status_code} (auth/session regression)")
                print_error(f"{name}: {response.status_code} - Auth/Session Regression Detected")
                all_passed = False
            elif response.status_code >= 400:
                results.add_warning(f"auth-regression-{name}", f"Got {response.status_code} (not auth-related)")
                print_warning(f"{name}: {response.status_code} (not auth-related)")
            else:
                print_success(f"{name}: No auth regression (status={response.status_code})")
        except Exception as e:
            results.add_fail(f"auth-regression-{name}", f"Exception: {str(e)}")
            all_passed = False
    
    if all_passed:
        results.add_pass("auth-session-regression", "No auth/session regression detected")
    else:
        results.add_fail("auth-session-regression", "Auth/session regression detected on one or more endpoints")

def test_4xx_5xx_contract_drift():
    """
    Test 7: 4xx/5xx and Contract Drift Check
    Test various endpoints to ensure no unexpected 4xx/5xx errors or contract drift
    """
    print_test_header("7. 4xx/5xx and Contract Drift Check")
    
    # Test public endpoints that should always work
    public_endpoints = [
        ("guidance-sections", f"{BACKEND_URL}/guidance/sections"),
        ("guidance-articles", f"{BACKEND_URL}/guidance/articles"),
        ("guidance-tips-empty", f"{BACKEND_URL}/guidance/tips?form_key="),
    ]
    
    all_passed = True
    for name, url in public_endpoints:
        try:
            print_info(f"\nTesting: {name}")
            response = requests.get(url, timeout=30)
            
            if response.status_code >= 500:
                results.add_fail(f"contract-drift-{name}", f"Got 5xx error: {response.status_code}")
                print_error(f"{name}: {response.status_code} - Server Error")
                all_passed = False
            elif response.status_code >= 400:
                results.add_warning(f"contract-drift-{name}", f"Got 4xx error: {response.status_code}")
                print_warning(f"{name}: {response.status_code} - Client Error")
            else:
                print_success(f"{name}: {response.status_code} - OK")
                
                # Check basic contract structure
                try:
                    data = response.json()
                    print_success(f"  Response is valid JSON")
                except:
                    results.add_warning(f"contract-drift-{name}", "Response is not valid JSON")
        except Exception as e:
            results.add_fail(f"contract-drift-{name}", f"Exception: {str(e)}")
            all_passed = False
    
    if all_passed:
        results.add_pass("4xx-5xx-contract-drift", "No unexpected 4xx/5xx errors or contract drift detected")

def main():
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}PRE-C10 PROGRESSIVE DISCLOSURE/COACHING CLOSURE BATCH{Colors.END}")
    print(f"{Colors.BOLD}Backend-Only Regression Smoke Test{Colors.END}")
    print(f"{Colors.BOLD}Preview URL: https://masci-audit-hub.preview.emergentagent.com{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")
    
    # Test 1: Super Admin Multi-Login
    admin_tokens = test_super_admin_multi_login()
    if not admin_tokens:
        print_error("\nSuper Admin login failed - cannot proceed with admin tests")
    
    # Test 2: HR Multi-Login
    hr_tokens = test_hr_multi_login()
    if not hr_tokens:
        print_error("\nHR login failed - cannot proceed with HR tests")
    
    # Test 3: Dispatch Multi-Login
    dispatch_tokens = test_dispatch_multi_login()
    if not dispatch_tokens:
        print_error("\nDispatch login failed - cannot proceed with dispatch tests")
    
    # Test 4: HR Employees Access (if HR login succeeded)
    if hr_tokens:
        test_hr_employees_access(hr_tokens["hr_token"], hr_tokens["session_token"])
    
    # Test 5: Guidance Tips API for specific form keys
    form_keys = ["employee-lifecycle", "corrective", "time-verification", "dispatch.handoff"]
    test_guidance_tips_api(form_keys)
    
    # Test 6: Auth/Session Regression Check (if all logins succeeded)
    if admin_tokens and hr_tokens and dispatch_tokens:
        test_auth_session_regression(
            admin_tokens.get("admin_token", ""),
            hr_tokens.get("hr_token", ""),
            dispatch_tokens.get("dispatch_token", ""),
            admin_tokens.get("session_token", ""),
            hr_tokens.get("session_token", ""),
            dispatch_tokens.get("session_token", "")
        )
    
    # Test 7: 4xx/5xx and Contract Drift Check
    test_4xx_5xx_contract_drift()
    
    # Print summary
    success = results.print_summary()
    
    if success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED{Colors.END}\n")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.END}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()

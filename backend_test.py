"""
Backend API Testing for PRE-C10 Remediation Batch
Tests the exact API behaviors specified in the review request.
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

def test_multi_login() -> Optional[Dict[str, Any]]:
    """
    Test 1: POST /api/auth/multi-login
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
        print_info(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("multi-login", f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return None
        
        data = response.json()
        
        # Check for session_token
        if "session_token" not in data:
            results.add_fail("multi-login", "Missing session_token in response")
            return None
        
        session_token = data.get("session_token")
        print_success(f"session_token present: {session_token[:20]}...")
        
        # Check for portal_tokens
        if "portal_tokens" not in data:
            results.add_fail("multi-login", "Missing portal_tokens in response")
            return None
        
        portal_tokens = data.get("portal_tokens", {})
        
        # Check for admin token
        if "admin" not in portal_tokens or not portal_tokens["admin"]:
            results.add_fail("multi-login", "Missing portal_tokens.admin")
            return None
        
        admin_token = portal_tokens["admin"]
        print_success(f"portal_tokens.admin present: {admin_token[:20]}...")
        
        # Check for hr token
        if "hr" not in portal_tokens or not portal_tokens["hr"]:
            results.add_fail("multi-login", "Missing portal_tokens.hr")
            return None
        
        hr_token = portal_tokens["hr"]
        print_success(f"portal_tokens.hr present: {hr_token[:20]}...")
        
        results.add_pass("multi-login", "All required tokens present")
        
        return {
            "session_token": session_token,
            "admin_token": admin_token,
            "hr_token": hr_token,
            "portal_tokens": portal_tokens
        }
        
    except Exception as e:
        results.add_fail("multi-login", f"Exception: {str(e)}")
        return None

def test_deploy_recovery(admin_token: str, session_token: str):
    """
    Test 2: GET /api/admin/deploy-recovery
    Expected: Returns 200 with current, r2, and recent_backups keys
    """
    print_test_header("2. GET /api/admin/deploy-recovery - Deployment Recovery Info")
    
    try:
        url = f"{BACKEND_URL}/admin/deploy-recovery"
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        print_info(f"GET {url}")
        print_info(f"Headers: X-Admin-Token, X-Directory-Token")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("deploy-recovery", f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return
        
        data = response.json()
        
        # Check for required keys
        required_keys = ["current", "r2", "recent_backups"]
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            results.add_fail("deploy-recovery", f"Missing keys: {', '.join(missing_keys)}")
            print_error(f"Response keys: {list(data.keys())}")
            return
        
        print_success(f"'current' key present: {type(data['current'])}")
        print_success(f"'r2' key present: {type(data['r2'])}")
        print_success(f"'recent_backups' key present: {type(data['recent_backups'])}")
        
        results.add_pass("deploy-recovery", "All required keys present")
        
    except Exception as e:
        results.add_fail("deploy-recovery", f"Exception: {str(e)}")

def test_trust_spine(admin_token: str, session_token: str):
    """
    Test 3: GET /api/admin/trust-spine
    Expected: Returns 200 with platform_band, canonical_status, and workflows array
    """
    print_test_header("3. GET /api/admin/trust-spine - Trust Spine Status")
    
    try:
        url = f"{BACKEND_URL}/admin/trust-spine"
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        print_info(f"GET {url}")
        print_info(f"Headers: X-Admin-Token, X-Directory-Token")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("trust-spine", f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return
        
        data = response.json()
        
        # Check for required keys
        if "platform_band" not in data:
            results.add_fail("trust-spine", "Missing 'platform_band' key")
            return
        
        if "canonical_status" not in data:
            results.add_fail("trust-spine", "Missing 'canonical_status' key")
            return
        
        if "workflows" not in data:
            results.add_fail("trust-spine", "Missing 'workflows' key")
            return
        
        if not isinstance(data["workflows"], list):
            results.add_fail("trust-spine", "'workflows' is not an array")
            return
        
        print_success(f"platform_band: {data['platform_band']}")
        print_success(f"canonical_status: {data['canonical_status']}")
        print_success(f"workflows array length: {len(data['workflows'])}")
        
        results.add_pass("trust-spine", "All required keys present with correct structure")
        
    except Exception as e:
        results.add_fail("trust-spine", f"Exception: {str(e)}")

def test_deployment_readiness(admin_token: str, session_token: str):
    """
    Test 4: GET /api/admin/deployment-readiness
    Expected: Returns 200 with structured decision payload
    """
    print_test_header("4. GET /api/admin/deployment-readiness - Deployment Readiness Decision")
    
    try:
        url = f"{BACKEND_URL}/admin/deployment-readiness"
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        print_info(f"GET {url}")
        print_info(f"Headers: X-Admin-Token, X-Directory-Token")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("deployment-readiness", f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return
        
        data = response.json()
        
        # Check for decision key
        if "decision" not in data:
            results.add_fail("deployment-readiness", "Missing 'decision' key")
            return
        
        decision = data["decision"]
        print_success(f"decision: {decision}")
        
        # Check for other expected keys
        expected_keys = ["blocking_gates", "advisory_findings", "summary"]
        for key in expected_keys:
            if key in data:
                print_success(f"'{key}' key present")
            else:
                results.add_warning("deployment-readiness", f"Missing '{key}' key")
        
        results.add_pass("deployment-readiness", f"Structured decision payload present (decision={decision})")
        
    except Exception as e:
        results.add_fail("deployment-readiness", f"Exception: {str(e)}")

def test_hr_employees(admin_token: str, hr_token: str, session_token: str):
    """
    Test 5: GET /api/hr/employees
    Expected: Returns 200 with items list (admin+HR session context)
    """
    print_test_header("5. GET /api/hr/employees - HR Employee List")
    
    try:
        url = f"{BACKEND_URL}/hr/employees"
        headers = {
            "X-Admin-Token": admin_token,
            "X-HR-Token": hr_token,
            "X-Directory-Token": session_token
        }
        
        print_info(f"GET {url}")
        print_info(f"Headers: X-Admin-Token, X-HR-Token, X-Directory-Token")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("hr-employees", f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return
        
        data = response.json()
        
        # Check for items key
        if "items" not in data:
            results.add_fail("hr-employees", "Missing 'items' key")
            return
        
        items = data["items"]
        if not isinstance(items, list):
            results.add_fail("hr-employees", "'items' is not an array")
            return
        
        print_success(f"items array present with {len(items)} employees")
        
        if len(items) == 0:
            results.add_warning("hr-employees", "items list is empty")
        else:
            results.add_pass("hr-employees", f"Non-empty items list ({len(items)} employees)")
        
    except Exception as e:
        results.add_fail("hr-employees", f"Exception: {str(e)}")

def test_project_staffing_summary(admin_token: str, session_token: str):
    """
    Test 6: GET /api/project-staffing/summary?limit=10
    Expected: Returns 200 with items and totals payload
    """
    print_test_header("6. GET /api/project-staffing/summary - Project Staffing Summary")
    
    try:
        url = f"{BACKEND_URL}/project-staffing/summary?limit=10"
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        print_info(f"GET {url}")
        print_info(f"Headers: X-Admin-Token, X-Directory-Token")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("project-staffing", f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return
        
        data = response.json()
        
        # Check for items and totals keys
        if "items" not in data:
            results.add_fail("project-staffing", "Missing 'items' key")
            return
        
        if "totals" not in data:
            results.add_fail("project-staffing", "Missing 'totals' key")
            return
        
        items = data["items"]
        totals = data["totals"]
        
        if not isinstance(items, list):
            results.add_fail("project-staffing", "'items' is not an array")
            return
        
        print_success(f"items array present with {len(items)} projects")
        print_success(f"totals object present: {type(totals)}")
        
        results.add_pass("project-staffing", f"Structured items/totals payload present")
        
    except Exception as e:
        results.add_fail("project-staffing", f"Exception: {str(e)}")

def test_auth_header_regressions(admin_token: str, hr_token: str, session_token: str):
    """
    Test 7: Verify no auth-header regressions (401s)
    Re-test all endpoints to ensure no 401 errors
    """
    print_test_header("7. Auth Header Regression Check - Verify No 401s")
    
    endpoints = [
        ("deploy-recovery", f"{BACKEND_URL}/admin/deploy-recovery", {"X-Admin-Token": admin_token, "X-Directory-Token": session_token}),
        ("trust-spine", f"{BACKEND_URL}/admin/trust-spine", {"X-Admin-Token": admin_token, "X-Directory-Token": session_token}),
        ("deployment-readiness", f"{BACKEND_URL}/admin/deployment-readiness", {"X-Admin-Token": admin_token, "X-Directory-Token": session_token}),
        ("hr-employees", f"{BACKEND_URL}/hr/employees", {"X-Admin-Token": admin_token, "X-HR-Token": hr_token, "X-Directory-Token": session_token}),
        ("project-staffing", f"{BACKEND_URL}/project-staffing/summary?limit=10", {"X-Admin-Token": admin_token, "X-Directory-Token": session_token}),
    ]
    
    all_passed = True
    for name, url, headers in endpoints:
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 401:
                results.add_fail(f"auth-regression-{name}", f"Got 401 Unauthorized")
                all_passed = False
                print_error(f"{name}: 401 Unauthorized")
            else:
                print_success(f"{name}: No 401 (status={response.status_code})")
        except Exception as e:
            results.add_fail(f"auth-regression-{name}", f"Exception: {str(e)}")
            all_passed = False
    
    if all_passed:
        results.add_pass("auth-header-regressions", "No 401 errors detected across all endpoints")
    else:
        results.add_fail("auth-header-regressions", "One or more endpoints returned 401")

def main():
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}PRE-C10 REMEDIATION BATCH - BACKEND API VALIDATION{Colors.END}")
    print(f"{Colors.BOLD}Preview URL: https://masci-audit-hub.preview.emergentagent.com{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")
    
    # Test 1: Multi-login
    tokens = test_multi_login()
    if not tokens:
        print_error("\nCannot proceed without valid authentication tokens")
        results.print_summary()
        sys.exit(1)
    
    admin_token = tokens["admin_token"]
    hr_token = tokens["hr_token"]
    session_token = tokens["session_token"]
    
    # Test 2: Deploy Recovery
    test_deploy_recovery(admin_token, session_token)
    
    # Test 3: Trust Spine
    test_trust_spine(admin_token, session_token)
    
    # Test 4: Deployment Readiness
    test_deployment_readiness(admin_token, session_token)
    
    # Test 5: HR Employees
    test_hr_employees(admin_token, hr_token, session_token)
    
    # Test 6: Project Staffing Summary
    test_project_staffing_summary(admin_token, session_token)
    
    # Test 7: Auth Header Regressions
    test_auth_header_regressions(admin_token, hr_token, session_token)
    
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

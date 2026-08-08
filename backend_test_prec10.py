"""
Backend API Testing for PRE-C10 Contamination-Governance Remediation
Tests the exact API behaviors specified in the review request.
"""
import requests
import json
import sys
import re
from typing import Dict, Any, Optional, List

# Backend URL from frontend/.env
BACKEND_URL = "https://masci-audit-hub.preview.emergentagent.com/api"

# Test credentials from review request
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Synthetic prefixes to check for leaks
SYNTHETIC_PREFIXES = [
    "TEST_", "TEST-", "SMOKE_", "SYNTHETIC_", "CERT_TEST", "PARITY_",
]

# Regex pattern for ITER[0-9] prefix
ITER_PATTERN = re.compile(r"^ITER\d", re.IGNORECASE)

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

def is_synthetic_name(name: str) -> bool:
    """Check if a name starts with synthetic/test prefixes."""
    if not name:
        return False
    name_upper = name.upper()
    for prefix in SYNTHETIC_PREFIXES:
        if name_upper.startswith(prefix.upper()):
            return True
    if ITER_PATTERN.match(name):
        return True
    return False

def test_multi_login() -> Optional[Dict[str, Any]]:
    """
    Test 1: POST /api/auth/multi-login
    Expected: Returns portal_tokens.admin and session_token
    """
    print_test_header("1. POST /api/auth/multi-login - Admin Login")
    
    try:
        url = f"{BACKEND_URL}/auth/multi-login"
        payload = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        print_info(f"POST {url}")
        print_info(f"Email: {ADMIN_EMAIL}")
        
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
        
        results.add_pass("multi-login", "Authentication successful with required tokens")
        
        return {
            "session_token": session_token,
            "admin_token": admin_token,
            "portal_tokens": portal_tokens
        }
        
    except Exception as e:
        results.add_fail("multi-login", f"Exception: {str(e)}")
        return None

def test_contamination_endpoint(admin_token: str, session_token: str):
    """
    Test 2: GET /api/admin/platform-truth-integrity/contamination
    Expected: Returns 200 with overall_status=green, release_gate_blocked=false, 
              blocking_findings=[], and all families showing green status with heuristic_only_count=0
    """
    print_test_header("2. GET /api/admin/platform-truth-integrity/contamination")
    
    try:
        url = f"{BACKEND_URL}/admin/platform-truth-integrity/contamination"
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        print_info(f"GET {url}")
        
        response = requests.get(url, headers=headers, timeout=180)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("contamination-endpoint", f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return
        
        data = response.json()
        
        # Check overall_status
        overall_status = data.get("overall_status")
        if overall_status != "green":
            results.add_fail("contamination-overall-status", f"Expected 'green', got '{overall_status}'")
        else:
            print_success(f"overall_status = green")
        
        # Check release_gate_blocked
        release_gate_blocked = data.get("release_gate_blocked")
        if release_gate_blocked is not False:
            results.add_fail("contamination-release-gate", f"Expected false, got {release_gate_blocked}")
        else:
            print_success(f"release_gate_blocked = false")
        
        # Check blocking_findings
        blocking_findings = data.get("blocking_findings", [])
        if len(blocking_findings) > 0:
            results.add_fail("contamination-blocking-findings", f"Expected empty array, got {len(blocking_findings)} findings")
            print_error(f"Blocking findings: {json.dumps(blocking_findings, indent=2)}")
        else:
            print_success(f"blocking_findings is empty")
        
        # Check families
        families = data.get("families", [])
        print_info(f"Found {len(families)} families")
        
        required_families = [
            "employees", "daily_reports", "field_leadership_records", 
            "incidents", "meetings", "jhas", "inspections", 
            "training_records", "safety_issuances", "dispatch_assignments", 
            "equipment_inspections"
        ]
        
        family_map = {f.get("family_id"): f for f in families if f.get("present")}
        
        all_families_green = True
        for family_id in required_families:
            if family_id not in family_map:
                print_warning(f"Family '{family_id}' not found in response")
                continue
            
            family = family_map[family_id]
            status = family.get("status")
            heuristic_only_count = family.get("heuristic_only_count", 0)
            
            if status != "green":
                results.add_fail(f"contamination-family-{family_id}", f"Expected status='green', got '{status}'")
                all_families_green = False
            elif heuristic_only_count != 0:
                results.add_fail(f"contamination-family-{family_id}", f"Expected heuristic_only_count=0, got {heuristic_only_count}")
                all_families_green = False
            else:
                print_success(f"Family '{family_id}': status=green, heuristic_only_count=0")
        
        if all_families_green and overall_status == "green" and not release_gate_blocked and len(blocking_findings) == 0:
            results.add_pass("contamination-endpoint", "All contamination checks passed")
        
    except Exception as e:
        results.add_fail("contamination-endpoint", f"Exception: {str(e)}")

def test_platform_truth_integrity(admin_token: str, session_token: str):
    """
    Test 3: GET /api/admin/platform-truth-integrity
    Expected: Returns 200 with overall_status=green, release_gate_blocked=false,
              contamination.overall_status=green, stale_derived_state.overall_status=green
    """
    print_test_header("3. GET /api/admin/platform-truth-integrity")
    
    try:
        url = f"{BACKEND_URL}/admin/platform-truth-integrity"
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        print_info(f"GET {url}")
        
        response = requests.get(url, headers=headers, timeout=180)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("platform-truth-integrity", f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return
        
        data = response.json()
        
        # Check overall_status
        overall_status = data.get("overall_status")
        if overall_status != "green":
            results.add_fail("truth-integrity-overall-status", f"Expected 'green', got '{overall_status}'")
        else:
            print_success(f"overall_status = green")
        
        # Check release_gate_blocked
        release_gate_blocked = data.get("release_gate_blocked")
        if release_gate_blocked is not False:
            results.add_fail("truth-integrity-release-gate", f"Expected false, got {release_gate_blocked}")
        else:
            print_success(f"release_gate_blocked = false")
        
        # Check contamination.overall_status
        contamination = data.get("contamination", {})
        contamination_status = contamination.get("overall_status")
        if contamination_status != "green":
            results.add_fail("truth-integrity-contamination", f"Expected contamination.overall_status='green', got '{contamination_status}'")
        else:
            print_success(f"contamination.overall_status = green")
        
        # Check stale_derived_state.overall_status
        stale_derived_state = data.get("stale_derived_state", {})
        stale_status = stale_derived_state.get("overall_status")
        if stale_status != "green":
            results.add_fail("truth-integrity-stale-state", f"Expected stale_derived_state.overall_status='green', got '{stale_status}'")
        else:
            print_success(f"stale_derived_state.overall_status = green")
        
        if overall_status == "green" and not release_gate_blocked and contamination_status == "green" and stale_status == "green":
            results.add_pass("platform-truth-integrity", "All platform truth integrity checks passed")
        
    except Exception as e:
        results.add_fail("platform-truth-integrity", f"Exception: {str(e)}")

def test_employees_leak_check(admin_token: str, session_token: str):
    """
    Test 4: GET /api/employees?limit=200
    Expected: Should not return operator-visible names starting with synthetic prefixes
    """
    print_test_header("4. GET /api/employees?limit=200 - Business Consumer Leak Check")
    
    try:
        url = f"{BACKEND_URL}/hr/employees?limit=200"
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        print_info(f"GET {url}")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("employees-leak-check", f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return
        
        data = response.json()
        items = data.get("items", [])
        
        print_info(f"Found {len(items)} employees")
        
        leaked_employees = []
        for emp in items:
            name = emp.get("name", "")
            preferred_name = emp.get("preferred_name", "")
            
            if is_synthetic_name(name):
                leaked_employees.append({"name": name, "field": "name", "id": emp.get("id")})
            elif is_synthetic_name(preferred_name):
                leaked_employees.append({"name": preferred_name, "field": "preferred_name", "id": emp.get("id")})
        
        if leaked_employees:
            results.add_fail("employees-leak-check", f"Found {len(leaked_employees)} synthetic/test employees in operator-visible results")
            print_error(f"Leaked employees:")
            for leak in leaked_employees[:10]:  # Show first 10
                print_error(f"  - {leak['field']}: {leak['name']} (id: {leak['id']})")
        else:
            print_success(f"No synthetic/test employee names found in {len(items)} results")
            results.add_pass("employees-leak-check", f"No leaks detected in {len(items)} employees")
        
    except Exception as e:
        results.add_fail("employees-leak-check", f"Exception: {str(e)}")

def test_daily_reports_leak_check(admin_token: str, session_token: str):
    """
    Test 5: GET /api/daily-reports?limit=200
    Expected: Should not return operator-visible project_name values starting with synthetic prefixes
    """
    print_test_header("5. GET /api/daily-reports - Business Consumer Leak Check")
    
    try:
        url = f"{BACKEND_URL}/daily-reports"
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        print_info(f"GET {url}")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("daily-reports-leak-check", f"Expected 200, got {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return
        
        # Response is a list, not a dict with items
        if isinstance(response.json(), list):
            items = response.json()
        else:
            items = response.json().get("items", [])
        
        print_info(f"Found {len(items)} daily reports")
        
        leaked_reports = []
        for report in items:
            project_name = report.get("project_name", "")
            project_number = report.get("project_number", "")
            
            if is_synthetic_name(project_name):
                leaked_reports.append({
                    "project_name": project_name, 
                    "project_number": project_number,
                    "id": report.get("id")
                })
            elif is_synthetic_name(project_number):
                leaked_reports.append({
                    "project_name": project_name, 
                    "project_number": project_number,
                    "id": report.get("id")
                })
        
        if leaked_reports:
            results.add_fail("daily-reports-leak-check", f"Found {len(leaked_reports)} synthetic/test daily reports in operator-visible results")
            print_error(f"Leaked daily reports:")
            for leak in leaked_reports[:10]:  # Show first 10
                print_error(f"  - project_name: {leak['project_name']}, project_number: {leak['project_number']} (id: {leak['id']})")
        else:
            print_success(f"No synthetic/test project names found in {len(items)} results")
            results.add_pass("daily-reports-leak-check", f"No leaks detected in {len(items)} daily reports")
        
    except Exception as e:
        results.add_fail("daily-reports-leak-check", f"Exception: {str(e)}")

def test_auth_regression(admin_token: str, session_token: str):
    """
    Test 6: Verify multi-login and protected admin route access works
    """
    print_test_header("6. Auth Regression - Protected Admin Route Access")
    
    try:
        # Test that we can access a protected admin route
        url = f"{BACKEND_URL}/admin/platform-truth-integrity/contamination"
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        print_info(f"Testing protected route access: {url}")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 401:
            results.add_fail("auth-regression", "Got 401 Unauthorized on protected admin route")
        elif response.status_code == 403:
            results.add_fail("auth-regression", "Got 403 Forbidden on protected admin route")
        elif response.status_code == 200:
            print_success(f"Protected admin route accessible with token pair")
            results.add_pass("auth-regression", "Multi-login and protected route access working correctly")
        else:
            results.add_warning("auth-regression", f"Unexpected status code: {response.status_code}")
        
    except Exception as e:
        results.add_fail("auth-regression", f"Exception: {str(e)}")

def main():
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}PRE-C10 CONTAMINATION-GOVERNANCE REMEDIATION - BACKEND VERIFICATION{Colors.END}")
    print(f"{Colors.BOLD}Preview URL: https://masci-audit-hub.preview.emergentagent.com{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")
    
    # Test 1: Multi-login
    tokens = test_multi_login()
    if not tokens:
        print_error("\nCannot proceed without valid authentication tokens")
        results.print_summary()
        sys.exit(1)
    
    admin_token = tokens["admin_token"]
    session_token = tokens["session_token"]
    
    # Test 2: Contamination endpoint
    test_contamination_endpoint(admin_token, session_token)
    
    # Test 3: Platform truth integrity
    test_platform_truth_integrity(admin_token, session_token)
    
    # Test 4: Employees leak check
    test_employees_leak_check(admin_token, session_token)
    
    # Test 5: Daily reports leak check
    test_daily_reports_leak_check(admin_token, session_token)
    
    # Test 6: Auth regression
    test_auth_regression(admin_token, session_token)
    
    # Print summary
    success = results.print_summary()
    
    if success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL PRE-C10 TESTS PASSED{Colors.END}\n")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ SOME PRE-C10 TESTS FAILED{Colors.END}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()

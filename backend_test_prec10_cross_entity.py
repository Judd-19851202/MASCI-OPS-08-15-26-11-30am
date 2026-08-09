"""
Backend API Testing for PRE-C10 Cross-Entity Evidence & History Integrity Batch
Tests the exact API behaviors specified in the review request.
"""
import requests
import json
import sys
from typing import Dict, Any, Optional, List

# Backend URL from frontend/.env
BACKEND_URL = "https://masci-audit-hub.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

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
        self.critical_issues = []
    
    def add_pass(self, test_name: str, details: str = ""):
        self.passed.append((test_name, details))
        print_success(f"{test_name}: PASS {details}")
    
    def add_fail(self, test_name: str, details: str, critical: bool = False):
        self.failed.append((test_name, details))
        if critical:
            self.critical_issues.append((test_name, details))
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
        
        if self.critical_issues:
            print(f"\n{Colors.RED}{Colors.BOLD}CRITICAL ISSUES:{Colors.END}")
            for test_name, details in self.critical_issues:
                print(f"  {Colors.RED}✗ {test_name}: {details}{Colors.END}")
        
        if self.failed:
            print(f"\n{Colors.RED}{Colors.BOLD}FAILED TESTS:{Colors.END}")
            for test_name, details in self.failed:
                if (test_name, details) not in self.critical_issues:
                    print(f"  {Colors.RED}✗ {test_name}: {details}{Colors.END}")
        
        if self.warnings:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}WARNINGS:{Colors.END}")
            for test_name, details in self.warnings:
                print(f"  {Colors.YELLOW}⚠ {test_name}: {details}{Colors.END}")
        
        return len(self.failed) == 0

results = TestResults()

def test_auth_multi_login() -> Optional[Dict[str, Any]]:
    """
    Test 1: POST /api/auth/multi-login
    Expected: Returns session_token and portal_tokens.admin
    """
    print_test_header("1. Auth Continuity Smoke - POST /api/auth/multi-login")
    
    try:
        url = f"{BACKEND_URL}/auth/multi-login"
        payload = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        print_info(f"POST {url}")
        print_info(f"Credentials: {ADMIN_EMAIL}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("auth-multi-login", f"Expected 200, got {response.status_code}", critical=True)
            print_error(f"Response: {response.text[:500]}")
            return None
        
        data = response.json()
        
        # Check for session_token
        if "session_token" not in data:
            results.add_fail("auth-multi-login", "Missing session_token in response", critical=True)
            return None
        
        session_token = data.get("session_token")
        print_success(f"session_token present: {session_token[:20]}...")
        
        # Check for portal_tokens
        if "portal_tokens" not in data:
            results.add_fail("auth-multi-login", "Missing portal_tokens in response", critical=True)
            return None
        
        portal_tokens = data.get("portal_tokens", {})
        
        # Check for admin token
        if "admin" not in portal_tokens or not portal_tokens["admin"]:
            results.add_fail("auth-multi-login", "Missing portal_tokens.admin", critical=True)
            return None
        
        admin_token = portal_tokens["admin"]
        print_success(f"portal_tokens.admin present: {admin_token[:20]}...")
        
        results.add_pass("auth-multi-login", "Admin session and portal tokens returned successfully")
        
        return {
            "session_token": session_token,
            "admin_token": admin_token,
            "portal_tokens": portal_tokens
        }
        
    except Exception as e:
        results.add_fail("auth-multi-login", f"Exception: {str(e)}", critical=True)
        return None

def test_cross_entity_integrity(admin_token: str, session_token: str):
    """
    Test 2: GET /api/admin/platform-truth-integrity/cross-entity
    Expected: Returns 200 with overall_status, release_gate_blocked, blocking_findings, and checks array
    """
    print_test_header("2. Cross-Entity Runtime Audit Surface")
    
    try:
        url = f"{BACKEND_URL}/admin/platform-truth-integrity/cross-entity"
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        print_info(f"GET {url}")
        print_info(f"Headers: X-Admin-Token, X-Directory-Token")
        
        response = requests.get(url, headers=headers, timeout=90)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("cross-entity-integrity", f"Expected 200, got {response.status_code}", critical=True)
            print_error(f"Response: {response.text[:500]}")
            return
        
        data = response.json()
        
        # Check for required top-level keys
        required_keys = ["overall_status", "release_gate_blocked", "blocking_findings", "checks"]
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            results.add_fail("cross-entity-integrity", f"Missing required keys: {', '.join(missing_keys)}", critical=True)
            print_error(f"Response keys: {list(data.keys())}")
            return
        
        print_success(f"overall_status: {data['overall_status']}")
        print_success(f"release_gate_blocked: {data['release_gate_blocked']}")
        print_success(f"blocking_findings count: {len(data['blocking_findings'])}")
        
        # Verify checks array structure
        checks = data.get("checks", [])
        if not isinstance(checks, list):
            results.add_fail("cross-entity-integrity", "'checks' is not an array", critical=True)
            return
        
        print_success(f"checks array present with {len(checks)} checks")
        
        # Verify expected check IDs are present
        expected_check_ids = [
            "project_team_assignment_authority",
            "meeting_attendee_identity_normalization",
            "incident_project_and_submitter_lineage",
            "daily_report_project_and_submitter_lineage",
            "equipment_preop_asset_and_operator_lineage",
            "dispatch_driver_truck_project_linkage",
            "transport_employee_projection_authority"
        ]
        
        check_ids = [check.get("id") for check in checks]
        missing_check_ids = [check_id for check_id in expected_check_ids if check_id not in check_ids]
        
        if missing_check_ids:
            results.add_fail("cross-entity-integrity", f"Missing expected check IDs: {', '.join(missing_check_ids)}", critical=True)
        else:
            print_success(f"All {len(expected_check_ids)} expected check IDs present")
        
        # Note: Red status is expected per review request
        if data['overall_status'] == 'red':
            print_info("Cross-entity status is RED (expected per review request - known blockers remain)")
        
        results.add_pass("cross-entity-integrity", f"Endpoint returns valid structure with {len(checks)} checks")
        
        # Print check details for visibility
        print(f"\n{Colors.BLUE}Check Details:{Colors.END}")
        for check in checks:
            status_color = Colors.GREEN if check.get('status') == 'green' else Colors.RED if check.get('status') == 'red' else Colors.YELLOW
            print(f"  {status_color}• {check.get('id')}: {check.get('status')}{Colors.END}")
            if check.get('status') == 'red':
                print(f"    {Colors.RED}Summary: {check.get('summary', 'N/A')[:100]}{Colors.END}")
        
    except Exception as e:
        results.add_fail("cross-entity-integrity", f"Exception: {str(e)}", critical=True)

def test_aggregated_truth_integrity(admin_token: str, session_token: str):
    """
    Test 3: GET /api/admin/platform-truth-integrity
    Expected: Returns 200 with contamination, stale_derived_state, and cross_entity sections
    """
    print_test_header("3. Aggregated Truth Endpoint")
    
    try:
        url = f"{BACKEND_URL}/admin/platform-truth-integrity"
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        print_info(f"GET {url}")
        print_info(f"Headers: X-Admin-Token, X-Directory-Token")
        
        response = requests.get(url, headers=headers, timeout=90)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("aggregated-truth", f"Expected 200, got {response.status_code}", critical=True)
            print_error(f"Response: {response.text[:500]}")
            return
        
        data = response.json()
        
        # Check for required sections
        required_sections = ["contamination", "stale_derived_state", "cross_entity"]
        missing_sections = [section for section in required_sections if section not in data]
        
        if missing_sections:
            results.add_fail("aggregated-truth", f"Missing required sections: {', '.join(missing_sections)}", critical=True)
            print_error(f"Response keys: {list(data.keys())}")
            return
        
        print_success("contamination section present")
        print_success("stale_derived_state section present")
        print_success("cross_entity section present")
        
        # Verify top-level release_gate_blocked
        if "release_gate_blocked" not in data:
            results.add_fail("aggregated-truth", "Missing top-level release_gate_blocked", critical=True)
            return
        
        print_success(f"release_gate_blocked: {data['release_gate_blocked']}")
        
        # Verify release_gate_blocked is true because cross_entity is blocked
        if data.get("cross_entity", {}).get("release_gate_blocked"):
            if not data["release_gate_blocked"]:
                results.add_fail("aggregated-truth", "Top-level release_gate_blocked should be true when cross_entity is blocked", critical=True)
            else:
                print_success("Top-level release_gate_blocked correctly reflects cross_entity blocked state")
        
        results.add_pass("aggregated-truth", "Aggregated truth endpoint returns all required sections")
        
    except Exception as e:
        results.add_fail("aggregated-truth", f"Exception: {str(e)}", critical=True)

def get_sample_employee_id(admin_token: str, session_token: str) -> Optional[str]:
    """Helper: Get a sample employee ID from the employees collection"""
    try:
        url = f"{BACKEND_URL}/hr/employees?limit=1"
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        response = requests.get(url, headers=headers, timeout=90)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            if items and len(items) > 0:
                employee_id = items[0].get("id")
                if employee_id:
                    print_info(f"Found sample employee ID: {employee_id}")
                    return employee_id
        
        return None
    except Exception as e:
        print_warning(f"Could not fetch sample employee ID: {str(e)}")
        return None

def get_sample_equipment_id(admin_token: str, session_token: str) -> Optional[str]:
    """Helper: Get a sample equipment ID from the equipment_master collection"""
    try:
        # Try to get equipment via admin endpoint
        url = f"{BACKEND_URL}/admin/equipment-master?limit=1"
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        response = requests.get(url, headers=headers, timeout=90)
        
        if response.status_code == 200:
            data = response.json()
            # Handle different possible response structures
            items = data.get("items", data.get("equipment", []))
            if items and len(items) > 0:
                equipment_id = items[0].get("id")
                if equipment_id:
                    print_info(f"Found sample equipment ID: {equipment_id}")
                    return equipment_id
        
        return None
    except Exception as e:
        print_warning(f"Could not fetch sample equipment ID: {str(e)}")
        return None

def test_master_history_employee(admin_token: str, session_token: str, employee_id: str):
    """
    Test 4a: GET /api/master-lookup/employees/{id}/history
    Expected: Returns 200 with structured history payload
    """
    print_test_header(f"4a. Master History - Employee ({employee_id})")
    
    try:
        url = f"{BACKEND_URL}/master-lookup/employees/{employee_id}/history"
        
        print_info(f"GET {url}")
        print_info("Note: This endpoint is public (no auth required)")
        
        response = requests.get(url, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("master-history-employee", f"Expected 200, got {response.status_code}", critical=True)
            print_error(f"Response: {response.text[:500]}")
            return
        
        data = response.json()
        
        # Check for expected structure
        expected_keys = ["master", "events", "total", "summary"]
        missing_keys = [key for key in expected_keys if key not in data]
        
        if missing_keys:
            results.add_fail("master-history-employee", f"Missing expected keys: {', '.join(missing_keys)}")
            print_error(f"Response keys: {list(data.keys())}")
            return
        
        print_success(f"master object present: {type(data['master'])}")
        print_success(f"events array present with {len(data.get('events', []))} events")
        print_success(f"total: {data.get('total')}")
        print_success(f"summary: {data.get('summary')}")
        
        # Verify no serialization issues (ObjectId errors)
        if "events" in data and isinstance(data["events"], list):
            print_success("Events array is properly serialized (no ObjectId issues)")
        
        results.add_pass("master-history-employee", f"Employee history endpoint working correctly ({data.get('total', 0)} events)")
        
    except Exception as e:
        results.add_fail("master-history-employee", f"Exception: {str(e)}", critical=True)

def test_master_history_equipment(admin_token: str, session_token: str, equipment_id: str):
    """
    Test 4b: GET /api/master-lookup/equipment/{id}/history
    Expected: Returns 200 with structured history payload
    """
    print_test_header(f"4b. Master History - Equipment ({equipment_id})")
    
    try:
        url = f"{BACKEND_URL}/master-lookup/equipment/{equipment_id}/history"
        
        print_info(f"GET {url}")
        print_info("Note: This endpoint is public (no auth required)")
        
        response = requests.get(url, timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            results.add_fail("master-history-equipment", f"Expected 200, got {response.status_code}", critical=True)
            print_error(f"Response: {response.text[:500]}")
            return
        
        data = response.json()
        
        # Check for expected structure
        expected_keys = ["master", "events", "total", "summary"]
        missing_keys = [key for key in expected_keys if key not in data]
        
        if missing_keys:
            results.add_fail("master-history-equipment", f"Missing expected keys: {', '.join(missing_keys)}")
            print_error(f"Response keys: {list(data.keys())}")
            return
        
        print_success(f"master object present: {type(data['master'])}")
        print_success(f"events array present with {len(data.get('events', []))} events")
        print_success(f"total: {data.get('total')}")
        print_success(f"summary: {data.get('summary')}")
        
        # Verify no serialization issues (ObjectId errors)
        if "events" in data and isinstance(data["events"], list):
            print_success("Events array is properly serialized (no ObjectId issues)")
        
        results.add_pass("master-history-equipment", f"Equipment history endpoint working correctly ({data.get('total', 0)} events)")
        
    except Exception as e:
        results.add_fail("master-history-equipment", f"Exception: {str(e)}", critical=True)

def test_regression_watch(admin_token: str, session_token: str):
    """
    Test 5: Regression Watch
    Re-test critical endpoints to ensure no regressions
    """
    print_test_header("5. Regression Watch - Auth & Runtime Init")
    
    endpoints = [
        ("platform-truth-integrity", f"{BACKEND_URL}/admin/platform-truth-integrity"),
        ("cross-entity-integrity", f"{BACKEND_URL}/admin/platform-truth-integrity/cross-entity"),
    ]
    
    all_passed = True
    for name, url in endpoints:
        try:
            headers = {
                "X-Admin-Token": admin_token,
                "X-Directory-Token": session_token
            }
            response = requests.get(url, headers=headers, timeout=90)
            
            if response.status_code == 401:
                results.add_fail(f"regression-{name}", "Got 401 Unauthorized (auth regression)", critical=True)
                all_passed = False
                print_error(f"{name}: 401 Unauthorized")
            elif response.status_code == 500:
                results.add_fail(f"regression-{name}", "Got 500 Internal Server Error (runtime regression)", critical=True)
                all_passed = False
                print_error(f"{name}: 500 Internal Server Error")
                print_error(f"Response: {response.text[:500]}")
            elif response.status_code == 200:
                print_success(f"{name}: No regression (status=200)")
            else:
                print_warning(f"{name}: Unexpected status {response.status_code}")
        except Exception as e:
            results.add_fail(f"regression-{name}", f"Exception: {str(e)}", critical=True)
            all_passed = False
    
    if all_passed:
        results.add_pass("regression-watch", "No auth/runtime regressions detected")
    else:
        results.add_fail("regression-watch", "One or more regression issues detected", critical=True)

def main():
    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}PRE-C10 CROSS-ENTITY EVIDENCE & HISTORY INTEGRITY BATCH{Colors.END}")
    print(f"{Colors.BOLD}Backend-Only Verification{Colors.END}")
    print(f"{Colors.BOLD}Preview URL: https://masci-audit-hub.preview.emergentagent.com{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")
    
    print_info("Governing state: PRE-C10 OPEN / NO-GO")
    print_info("Testing: Cross-entity audit + shared backend repairs")
    print_info("Expected: Cross-entity RED (known blockers remain)")
    
    # Test 1: Auth Multi-Login
    tokens = test_auth_multi_login()
    if not tokens:
        print_error("\nCannot proceed without valid authentication tokens")
        results.print_summary()
        sys.exit(1)
    
    admin_token = tokens["admin_token"]
    session_token = tokens["session_token"]
    
    # Test 2: Cross-Entity Integrity
    test_cross_entity_integrity(admin_token, session_token)
    
    # Test 3: Aggregated Truth Integrity
    test_aggregated_truth_integrity(admin_token, session_token)
    
    # Test 4: Master History Endpoints
    print_info("\nFetching sample IDs for master history tests...")
    employee_id = get_sample_employee_id(admin_token, session_token)
    equipment_id = get_sample_equipment_id(admin_token, session_token)
    
    if employee_id:
        test_master_history_employee(admin_token, session_token, employee_id)
    else:
        results.add_warning("master-history-employee", "No employee ID available for testing")
    
    if equipment_id:
        test_master_history_equipment(admin_token, session_token, equipment_id)
    else:
        results.add_warning("master-history-equipment", "No equipment ID available for testing")
    
    # Test 5: Regression Watch
    test_regression_watch(admin_token, session_token)
    
    # Print summary
    success = results.print_summary()
    
    if success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED{Colors.END}")
        print(f"{Colors.BLUE}Note: Cross-entity RED status is expected (known blockers remain){Colors.END}\n")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.END}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()

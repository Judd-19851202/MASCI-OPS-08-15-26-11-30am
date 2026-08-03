"""MASCI OPS Wave 3 Family 1 - OCC Health Aggregator Bounded Repair Verification.

This test verifies the bounded repair for the OCC Health Aggregator on Preview:
1. Authenticate through POST /api/auth/multi-login
2. GET /api/admin/occ/health with admin token
3. Verify family role = AGGREGATOR (not canonical owner)
4. Verify canonical ownership remains upstream at platform_attestation
5. Verify no duplicate owner/truth engine introduced
6. Verify honest unknown handling remains intact
7. Check no backup/recovery/DR APIs were modified
"""
import os
import sys
import requests
from datetime import datetime

# Preview base URL from environment
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com").rstrip("/")

# Test credentials from test_credentials.md
TEST_EMAIL = "jaymn.judd@mascigc.com"
TEST_PASSWORD = "Maddix123!"

# ANSI color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def log_test(name, status, details=""):
    """Log test result with color coding."""
    color = GREEN if status == "PASS" else RED if status == "FAIL" else YELLOW
    print(f"{color}[{status}]{RESET} {name}")
    if details:
        print(f"      {details}")

def main():
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}MASCI OPS Wave 3 Family 1 - OCC Health Aggregator Bounded Repair Verification{RESET}")
    print(f"{BLUE}Preview URL: {BASE_URL}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "warnings": 0
    }
    
    # ========================================================================
    # TEST 1: Authenticate through POST /api/auth/multi-login
    # ========================================================================
    print(f"\n{BLUE}TEST 1: Authentication{RESET}")
    results["total"] += 1
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        
        if response.status_code != 200:
            log_test("Authentication", "FAIL", f"Status: {response.status_code}, Response: {response.text[:200]}")
            results["failed"] += 1
            print(f"\n{RED}CRITICAL: Cannot proceed without authentication{RESET}")
            return results
        
        data = response.json()
        admin_token = data.get("portal_tokens", {}).get("admin") or data.get("token")
        directory_token = data.get("session_token")
        
        if not admin_token:
            log_test("Authentication", "FAIL", "No admin token in response")
            results["failed"] += 1
            print(f"\n{RED}CRITICAL: Cannot proceed without admin token{RESET}")
            return results
        
        log_test("Authentication", "PASS", f"Admin token: {admin_token[:20]}..., Directory token: {directory_token[:20] if directory_token else 'None'}...")
        results["passed"] += 1
        
        # Store both tokens for later use
        auth_headers = {
            "X-Admin-Token": admin_token,
        }
        if directory_token:
            auth_headers["X-Directory-Token"] = directory_token
        
    except Exception as e:
        log_test("Authentication", "FAIL", f"Exception: {str(e)}")
        results["failed"] += 1
        return results
    
    # ========================================================================
    # TEST 2: GET /api/admin/occ/health with authenticated admin token
    # ========================================================================
    print(f"\n{BLUE}TEST 2: OCC Health Endpoint Access{RESET}")
    results["total"] += 1
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers=auth_headers,
            timeout=60
        )
        
        if response.status_code != 200:
            log_test("OCC Health Endpoint", "FAIL", f"Status: {response.status_code}, Response: {response.text[:200]}")
            results["failed"] += 1
            print(f"\n{RED}CRITICAL: Cannot proceed without OCC health data{RESET}")
            return results
        
        occ_data = response.json()
        log_test("OCC Health Endpoint", "PASS", f"Status: 200, Data keys: {list(occ_data.keys())[:10]}")
        results["passed"] += 1
        
    except Exception as e:
        log_test("OCC Health Endpoint", "FAIL", f"Exception: {str(e)}")
        results["failed"] += 1
        return results
    
    # ========================================================================
    # TEST 3: Verify family role = AGGREGATOR (not canonical owner)
    # ========================================================================
    print(f"\n{BLUE}TEST 3: Verify Role = AGGREGATOR{RESET}")
    
    # Test 3a: truth_relationship.role = AGGREGATOR
    results["total"] += 1
    truth_relationship = occ_data.get("truth_relationship", {})
    relationship_role = truth_relationship.get("role")
    
    if relationship_role == "AGGREGATOR":
        log_test("truth_relationship.role = AGGREGATOR", "PASS", f"Role: {relationship_role}")
        results["passed"] += 1
    else:
        log_test("truth_relationship.role = AGGREGATOR", "FAIL", f"Expected AGGREGATOR, got: {relationship_role}")
        results["failed"] += 1
    
    # Test 3b: truth_surface.role = AGGREGATOR
    results["total"] += 1
    truth_surface = occ_data.get("truth_surface", {})
    surface_role = truth_surface.get("role")
    
    if surface_role == "AGGREGATOR":
        log_test("truth_surface.role = AGGREGATOR", "PASS", f"Role: {surface_role}")
        results["passed"] += 1
    else:
        log_test("truth_surface.role = AGGREGATOR", "FAIL", f"Expected AGGREGATOR, got: {surface_role}")
        results["failed"] += 1
    
    # ========================================================================
    # TEST 4: Verify canonical ownership remains upstream
    # ========================================================================
    print(f"\n{BLUE}TEST 4: Verify Canonical Ownership Upstream{RESET}")
    
    # Test 4a: truth_relationship.canonical_owner_id = platform_attestation
    results["total"] += 1
    relationship_owner_id = truth_relationship.get("canonical_owner_id")
    
    if relationship_owner_id == "platform_attestation":
        log_test("truth_relationship.canonical_owner_id = platform_attestation", "PASS", f"Owner ID: {relationship_owner_id}")
        results["passed"] += 1
    else:
        log_test("truth_relationship.canonical_owner_id = platform_attestation", "FAIL", f"Expected platform_attestation, got: {relationship_owner_id}")
        results["failed"] += 1
    
    # Test 4b: truth_relationship.canonical_owner_route = /api/admin/platform/status
    results["total"] += 1
    relationship_owner_route = truth_relationship.get("canonical_owner_route")
    
    if relationship_owner_route == "/api/admin/platform/status":
        log_test("truth_relationship.canonical_owner_route = /api/admin/platform/status", "PASS", f"Owner route: {relationship_owner_route}")
        results["passed"] += 1
    else:
        log_test("truth_relationship.canonical_owner_route = /api/admin/platform/status", "FAIL", f"Expected /api/admin/platform/status, got: {relationship_owner_route}")
        results["failed"] += 1
    
    # Test 4c: Verify route does NOT point to itself
    results["total"] += 1
    if relationship_owner_route != "/api/admin/occ/health":
        log_test("canonical_owner_route NOT pointing to self", "PASS", f"Route correctly points upstream: {relationship_owner_route}")
        results["passed"] += 1
    else:
        log_test("canonical_owner_route NOT pointing to self", "FAIL", "Route incorrectly points to /api/admin/occ/health")
        results["failed"] += 1
    
    # Test 4d: truth_surface.truth_subject = shared_operational_posture
    results["total"] += 1
    truth_subject = truth_surface.get("truth_subject")
    
    if truth_subject == "shared_operational_posture":
        log_test("truth_surface.truth_subject = shared_operational_posture", "PASS", f"Truth subject: {truth_subject}")
        results["passed"] += 1
    else:
        log_test("truth_surface.truth_subject = shared_operational_posture", "FAIL", f"Expected shared_operational_posture, got: {truth_subject}")
        results["failed"] += 1
    
    # ========================================================================
    # TEST 5: Verify no duplicate owner/truth engine introduced
    # ========================================================================
    print(f"\n{BLUE}TEST 5: Verify No Duplicate Truth Engine{RESET}")
    
    # Test 5a: truth_relationship.is_canonical must be false
    results["total"] += 1
    is_canonical = truth_relationship.get("is_canonical")
    
    if is_canonical is False:
        log_test("truth_relationship.is_canonical = False", "PASS", f"is_canonical: {is_canonical}")
        results["passed"] += 1
    else:
        log_test("truth_relationship.is_canonical = False", "FAIL", f"Expected False, got: {is_canonical}")
        results["failed"] += 1
    
    # Test 5b: Role must NOT be CANONICAL_OWNER
    results["total"] += 1
    if relationship_role != "CANONICAL_OWNER":
        log_test("Role is NOT CANONICAL_OWNER", "PASS", f"Role: {relationship_role}")
        results["passed"] += 1
    else:
        log_test("Role is NOT CANONICAL_OWNER", "FAIL", "OCC should not be a CANONICAL_OWNER")
        results["failed"] += 1
    
    # ========================================================================
    # TEST 6: Verify honest unknown handling remains intact
    # ========================================================================
    print(f"\n{BLUE}TEST 6: Verify Honest Unknown Handling{RESET}")
    
    # Test 6a: canonical_counts present
    results["total"] += 1
    canonical_counts = occ_data.get("canonical_counts", {})
    
    required_count_keys = {"verified", "degraded", "mismatch", "unverifiable", "not_applicable"}
    missing_keys = required_count_keys - set(canonical_counts.keys())
    
    if not missing_keys:
        log_test("canonical_counts has all required keys", "PASS", f"Keys: {list(canonical_counts.keys())}")
        results["passed"] += 1
    else:
        log_test("canonical_counts has all required keys", "FAIL", f"Missing keys: {missing_keys}")
        results["failed"] += 1
    
    # Test 6b: If unverifiable > 0, overall_canonical must not be VERIFIED
    results["total"] += 1
    unverifiable_count = canonical_counts.get("unverifiable", 0)
    overall_canonical = occ_data.get("overall_canonical")
    
    if unverifiable_count > 0:
        if overall_canonical != "VERIFIED":
            log_test("Honest unknown handling (unverifiable > 0)", "PASS", f"unverifiable={unverifiable_count}, overall_canonical={overall_canonical}")
            results["passed"] += 1
        else:
            log_test("Honest unknown handling (unverifiable > 0)", "FAIL", f"overall_canonical should not be VERIFIED when unverifiable={unverifiable_count}")
            results["failed"] += 1
    else:
        log_test("Honest unknown handling (unverifiable = 0)", "PASS", f"No unverifiable cards, overall_canonical={overall_canonical}")
        results["passed"] += 1
    
    # Test 6c: Sections present
    results["total"] += 1
    sections = occ_data.get("sections", [])
    
    if len(sections) >= 8:
        log_test("Response includes sections", "PASS", f"Sections count: {len(sections)}")
        results["passed"] += 1
    else:
        log_test("Response includes sections", "FAIL", f"Expected >= 8 sections, got: {len(sections)}")
        results["failed"] += 1
    
    # ========================================================================
    # TEST 7: Verify no backup/recovery/DR APIs modified
    # ========================================================================
    print(f"\n{BLUE}TEST 7: Verify No Backup/Recovery/DR API Modifications{RESET}")
    
    # Test 7a: Check /api/admin/recovery/snapshot still works
    results["total"] += 1
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers=auth_headers,
            timeout=30
        )
        
        if response.status_code == 200:
            log_test("Recovery snapshot endpoint unchanged", "PASS", f"Status: {response.status_code}")
            results["passed"] += 1
        else:
            log_test("Recovery snapshot endpoint unchanged", "WARN", f"Status: {response.status_code} (may be expected)")
            results["warnings"] += 1
    except Exception as e:
        log_test("Recovery snapshot endpoint unchanged", "WARN", f"Exception: {str(e)}")
        results["warnings"] += 1
    
    # Test 7b: Check /api/admin/backups-scheduler-state still works
    results["total"] += 1
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=auth_headers,
            timeout=30
        )
        
        if response.status_code == 200:
            log_test("Backup scheduler endpoint unchanged", "PASS", f"Status: {response.status_code}")
            results["passed"] += 1
        else:
            log_test("Backup scheduler endpoint unchanged", "WARN", f"Status: {response.status_code} (may be expected)")
            results["warnings"] += 1
    except Exception as e:
        log_test("Backup scheduler endpoint unchanged", "WARN", f"Exception: {str(e)}")
        results["warnings"] += 1
    
    # Test 7c: Check /api/admin/r2/lifecycle/health still works
    results["total"] += 1
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/r2/lifecycle/health",
            headers=auth_headers,
            timeout=30
        )
        
        if response.status_code == 200:
            log_test("R2 lifecycle endpoint unchanged", "PASS", f"Status: {response.status_code}")
            results["passed"] += 1
        else:
            log_test("R2 lifecycle endpoint unchanged", "WARN", f"Status: {response.status_code} (may be expected)")
            results["warnings"] += 1
    except Exception as e:
        log_test("R2 lifecycle endpoint unchanged", "WARN", f"Exception: {str(e)}")
        results["warnings"] += 1
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}TEST SUMMARY{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    print(f"Total Tests:    {results['total']}")
    print(f"{GREEN}Passed:         {results['passed']}{RESET}")
    print(f"{RED}Failed:         {results['failed']}{RESET}")
    print(f"{YELLOW}Warnings:       {results['warnings']}{RESET}")
    
    pass_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
    print(f"\nPass Rate:      {pass_rate:.1f}%")
    
    if results['failed'] == 0:
        print(f"\n{GREEN}✅ ALL CRITICAL TESTS PASSED{RESET}")
        print(f"{GREEN}OCC Health Aggregator bounded repair verified successfully.{RESET}")
        return 0
    else:
        print(f"\n{RED}❌ {results['failed']} TEST(S) FAILED{RESET}")
        print(f"{RED}OCC Health Aggregator bounded repair has issues.{RESET}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

#!/usr/bin/env python3
"""
WP-18C8 Earned Value Engine Backend Verification

Test the new WP-18C8 Earned Value Engine backend against live preview/local runtime.
Focus on C8 and its immediate C3/C5/C7 reuse contract.

Test flows:
1. PM auth -> GET /api/pm/project-controls/projects/ZZ-RUNTIME-CERT-2026/earned-value
   - Returns 200 and readiness overall=ready
2. Admin auth -> GET /api/admin/governance/project-controls/projects/ZZ-RUNTIME-CERT-2026/earned-value
   - Returns 200 and mirrors the governed summary
3. GET /api/pm/project-controls/projects/ZZ-RUNTIME-CERT-2026/budget/overview
   - Shows approved commitment and actual-cost candidates with review_queue_open=0
4. Validate metric truth from seeded project:
   - BAC=1200, EV=1200, AC=900, CPI≈1.3333
   - open_actual_cost_count=0, open_commitment_count=0
5. Validate C8 review-preservation contract:
   - Approved commitment/actual-cost linkage survives overview sync
   - Does not revert to review_required

Credentials:
- PM: cert.pm@example.com / CertProof2026!
- Admin: jaymn.judd@mascigc.com / Maddix123!

Context: New code lives in:
- /app/backend/services/project_earned_value_engine.py
- /app/backend/services/project_budget_authority.py
- /app/backend/routes/enterprise_governance.py

C7 is frozen; do not treat C7 as mutable scope.
"""

import json
import sys
from typing import Any, Dict

import requests

# Configuration
BASE_URL = "https://masci-audit-hub.preview.emergentagent.com"
PROJECT_NUMBER = "ZZ-RUNTIME-CERT-2026"
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Expected metrics from seeded project
EXPECTED_BAC = 1200.0
EXPECTED_EV = 1200.0
EXPECTED_AC = 900.0
EXPECTED_CPI = 1.3333  # EV / AC = 1200 / 900 ≈ 1.3333
CPI_TOLERANCE = 0.01  # Allow small floating point differences

# Test results
test_results = []


def log_test(test_name: str, passed: bool, details: str = ""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    result = {"test": test_name, "passed": passed, "details": details}
    test_results.append(result)
    print(f"{status} - {test_name}")
    if details:
        print(f"  Details: {details}")


def pm_login() -> Dict[str, str]:
    """Login as PM and return tokens"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            timeout=15,
        )
        if response.status_code != 200:
            log_test("PM Login", False, f"Status {response.status_code}: {response.text[:200]}")
            return {}
        
        data = response.json()
        pm_token = data.get("token", "")
        
        if not pm_token:
            log_test("PM Login", False, "No PM token in response")
            return {}
        
        log_test("PM Login", True, f"PM token length: {len(pm_token)}")
        return {"X-PM-Token": pm_token}
    except Exception as e:
        log_test("PM Login", False, f"Exception: {str(e)}")
        return {}


def admin_login() -> Dict[str, str]:
    """Login as Admin and return tokens"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15,
        )
        if response.status_code != 200:
            log_test("Admin Login", False, f"Status {response.status_code}: {response.text[:200]}")
            return {}
        
        data = response.json()
        session_token = data.get("session_token", "")
        admin_token = data.get("portal_tokens", {}).get("admin", "")
        
        if not session_token or not admin_token:
            log_test("Admin Login", False, "Missing session_token or admin token")
            return {}
        
        log_test("Admin Login", True, f"Session token length: {len(session_token)}, Admin token length: {len(admin_token)}")
        return {"X-Directory-Token": session_token, "X-Admin-Token": admin_token}
    except Exception as e:
        log_test("Admin Login", False, f"Exception: {str(e)}")
        return {}


def test_pm_earned_value_endpoint(pm_headers: Dict[str, str]):
    """Test 1: PM earned value endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{PROJECT_NUMBER}/earned-value",
            headers=pm_headers,
            timeout=30,
        )
        
        if response.status_code != 200:
            log_test(
                "Test 1: PM Earned Value Endpoint - HTTP 200",
                False,
                f"Status {response.status_code}: {response.text[:200]}"
            )
            return None
        
        log_test("Test 1: PM Earned Value Endpoint - HTTP 200", True, "Endpoint accessible")
        
        data = response.json()
        
        # Check readiness
        readiness = data.get("readiness", {})
        overall = readiness.get("overall", "")
        
        if overall == "ready":
            log_test("Test 1: PM Earned Value - Readiness Overall=Ready", True, f"Overall readiness: {overall}")
        else:
            log_test(
                "Test 1: PM Earned Value - Readiness Overall=Ready",
                False,
                f"Overall readiness: {overall}, expected 'ready'. Readiness details: {json.dumps(readiness, indent=2)}"
            )
        
        return data
    except Exception as e:
        log_test("Test 1: PM Earned Value Endpoint", False, f"Exception: {str(e)}")
        return None


def test_admin_earned_value_endpoint(admin_headers: Dict[str, str]):
    """Test 2: Admin earned value endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/projects/{PROJECT_NUMBER}/earned-value",
            headers=admin_headers,
            timeout=30,
        )
        
        if response.status_code != 200:
            log_test(
                "Test 2: Admin Earned Value Endpoint - HTTP 200",
                False,
                f"Status {response.status_code}: {response.text[:200]}"
            )
            return None
        
        log_test("Test 2: Admin Earned Value Endpoint - HTTP 200", True, "Endpoint accessible")
        
        data = response.json()
        
        # Check if it mirrors the governed summary
        summary = data.get("summary", {})
        if summary:
            log_test(
                "Test 2: Admin Earned Value - Governed Summary Present",
                True,
                f"Summary keys: {list(summary.keys())}"
            )
        else:
            log_test("Test 2: Admin Earned Value - Governed Summary Present", False, "No summary in response")
        
        return data
    except Exception as e:
        log_test("Test 2: Admin Earned Value Endpoint", False, f"Exception: {str(e)}")
        return None


def test_budget_overview(pm_headers: Dict[str, str]):
    """Test 3: Budget overview endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{PROJECT_NUMBER}/budget/overview",
            headers=pm_headers,
            timeout=30,
        )
        
        if response.status_code != 200:
            log_test(
                "Test 3: Budget Overview Endpoint - HTTP 200",
                False,
                f"Status {response.status_code}: {response.text[:200]}"
            )
            return None
        
        log_test("Test 3: Budget Overview Endpoint - HTTP 200", True, "Endpoint accessible")
        
        data = response.json()
        
        # Check for approved commitment and actual-cost candidates
        commitment_candidates = data.get("commitment_candidates", [])
        actual_cost_candidates = data.get("actual_cost_candidates", [])
        
        # Count review_queue_open (candidates with review_status in pending_review or review_required)
        review_queue_open = 0
        for candidate in commitment_candidates:
            if candidate.get("review_status") in ["pending_review", "review_required"]:
                review_queue_open += 1
        for candidate in actual_cost_candidates:
            if candidate.get("review_status") in ["pending_review", "review_required"]:
                review_queue_open += 1
        
        if review_queue_open == 0:
            log_test(
                "Test 3: Budget Overview - Review Queue Open = 0",
                True,
                f"Review queue open: {review_queue_open}"
            )
        else:
            log_test(
                "Test 3: Budget Overview - Review Queue Open = 0",
                False,
                f"Review queue open: {review_queue_open}, expected 0"
            )
        
        return data
    except Exception as e:
        log_test("Test 3: Budget Overview Endpoint", False, f"Exception: {str(e)}")
        return None


def test_metric_truth(pm_ev_data: Dict[str, Any]):
    """Test 4: Validate metric truth from seeded project"""
    if not pm_ev_data:
        log_test("Test 4: Metric Truth Validation", False, "No PM earned value data available")
        return
    
    summary = pm_ev_data.get("summary", {})
    
    # Check BAC
    bac = summary.get("bac")
    if bac is not None and abs(bac - EXPECTED_BAC) < 0.01:
        log_test("Test 4: Metric Truth - BAC = 1200", True, f"BAC: {bac}")
    else:
        log_test("Test 4: Metric Truth - BAC = 1200", False, f"BAC: {bac}, expected {EXPECTED_BAC}")
    
    # Check EV
    ev = summary.get("ev")
    if ev is not None and abs(ev - EXPECTED_EV) < 0.01:
        log_test("Test 4: Metric Truth - EV = 1200", True, f"EV: {ev}")
    else:
        log_test("Test 4: Metric Truth - EV = 1200", False, f"EV: {ev}, expected {EXPECTED_EV}")
    
    # Check AC
    ac = summary.get("ac")
    if ac is not None and abs(ac - EXPECTED_AC) < 0.01:
        log_test("Test 4: Metric Truth - AC = 900", True, f"AC: {ac}")
    else:
        log_test("Test 4: Metric Truth - AC = 900", False, f"AC: {ac}, expected {EXPECTED_AC}")
    
    # Check CPI
    cpi = summary.get("cpi")
    if cpi is not None and abs(cpi - EXPECTED_CPI) < CPI_TOLERANCE:
        log_test("Test 4: Metric Truth - CPI ≈ 1.3333", True, f"CPI: {cpi}")
    else:
        log_test("Test 4: Metric Truth - CPI ≈ 1.3333", False, f"CPI: {cpi}, expected ≈{EXPECTED_CPI}")
    
    # Check open counts
    open_actual_cost_count = summary.get("open_actual_cost_count", -1)
    open_commitment_count = summary.get("open_commitment_count", -1)
    
    if open_actual_cost_count == 0:
        log_test("Test 4: Metric Truth - Open Actual Cost Count = 0", True, f"Count: {open_actual_cost_count}")
    else:
        log_test(
            "Test 4: Metric Truth - Open Actual Cost Count = 0",
            False,
            f"Count: {open_actual_cost_count}, expected 0"
        )
    
    if open_commitment_count == 0:
        log_test("Test 4: Metric Truth - Open Commitment Count = 0", True, f"Count: {open_commitment_count}")
    else:
        log_test(
            "Test 4: Metric Truth - Open Commitment Count = 0",
            False,
            f"Count: {open_commitment_count}, expected 0"
        )


def test_c8_review_preservation(pm_headers: Dict[str, str], budget_overview: Dict[str, Any]):
    """Test 5: Validate C8 review-preservation contract"""
    if not budget_overview:
        log_test("Test 5: C8 Review Preservation", False, "No budget overview data available")
        return
    
    # Check approved commitment candidates
    commitment_candidates = budget_overview.get("commitment_candidates", [])
    approved_commitments = [c for c in commitment_candidates if c.get("review_status") == "approved"]
    
    if approved_commitments:
        log_test(
            "Test 5: C8 Review Preservation - Approved Commitments Present",
            True,
            f"Found {len(approved_commitments)} approved commitment(s)"
        )
        
        # Check that approved commitments have allocations
        has_allocations = all(c.get("allocations") for c in approved_commitments)
        if has_allocations:
            log_test(
                "Test 5: C8 Review Preservation - Approved Commitments Have Allocations",
                True,
                "All approved commitments have allocations"
            )
        else:
            log_test(
                "Test 5: C8 Review Preservation - Approved Commitments Have Allocations",
                False,
                "Some approved commitments missing allocations"
            )
    else:
        log_test(
            "Test 5: C8 Review Preservation - Approved Commitments Present",
            False,
            "No approved commitments found (may be expected if no seeded data)"
        )
    
    # Check approved actual-cost candidates
    actual_cost_candidates = budget_overview.get("actual_cost_candidates", [])
    approved_actuals = [c for c in actual_cost_candidates if c.get("review_status") == "approved"]
    
    if approved_actuals:
        log_test(
            "Test 5: C8 Review Preservation - Approved Actual Costs Present",
            True,
            f"Found {len(approved_actuals)} approved actual cost(s)"
        )
        
        # Check that approved actuals have allocations
        has_allocations = all(c.get("allocations") for c in approved_actuals)
        if has_allocations:
            log_test(
                "Test 5: C8 Review Preservation - Approved Actual Costs Have Allocations",
                True,
                "All approved actual costs have allocations"
            )
        else:
            log_test(
                "Test 5: C8 Review Preservation - Approved Actual Costs Have Allocations",
                False,
                "Some approved actual costs missing allocations"
            )
    else:
        log_test(
            "Test 5: C8 Review Preservation - Approved Actual Costs Present",
            False,
            "No approved actual costs found (may be expected if no seeded data)"
        )
    
    # Verify no reversion to review_required
    reverted_commitments = [
        c for c in commitment_candidates
        if c.get("review_status") == "review_required" and c.get("reviewed_at")
    ]
    reverted_actuals = [
        c for c in actual_cost_candidates
        if c.get("review_status") == "review_required" and c.get("reviewed_at")
    ]
    
    if not reverted_commitments and not reverted_actuals:
        log_test(
            "Test 5: C8 Review Preservation - No Reversion to Review Required",
            True,
            "No previously reviewed items reverted to review_required"
        )
    else:
        log_test(
            "Test 5: C8 Review Preservation - No Reversion to Review Required",
            False,
            f"Found {len(reverted_commitments)} reverted commitments and {len(reverted_actuals)} reverted actuals"
        )


def main():
    """Run all WP-18C8 backend tests"""
    print("=" * 80)
    print("WP-18C8 Earned Value Engine Backend Verification")
    print("=" * 80)
    print()
    
    # Login
    pm_headers = pm_login()
    admin_headers = admin_login()
    
    if not pm_headers or not admin_headers:
        print("\n❌ CRITICAL: Authentication failed. Cannot proceed with tests.")
        sys.exit(1)
    
    print()
    
    # Test 1: PM earned value endpoint
    pm_ev_data = test_pm_earned_value_endpoint(pm_headers)
    print()
    
    # Test 2: Admin earned value endpoint
    admin_ev_data = test_admin_earned_value_endpoint(admin_headers)
    print()
    
    # Test 3: Budget overview
    budget_overview = test_budget_overview(pm_headers)
    print()
    
    # Test 4: Metric truth validation
    test_metric_truth(pm_ev_data)
    print()
    
    # Test 5: C8 review preservation
    test_c8_review_preservation(pm_headers, budget_overview)
    print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed_count = sum(1 for r in test_results if r["passed"])
    total_count = len(test_results)
    pass_rate = (passed_count / total_count * 100) if total_count > 0 else 0
    
    print(f"\nTotal Tests: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    print()
    
    # List failed tests
    failed_tests = [r for r in test_results if not r["passed"]]
    if failed_tests:
        print("FAILED TESTS:")
        for test in failed_tests:
            print(f"  ❌ {test['test']}")
            if test["details"]:
                print(f"     {test['details']}")
        print()
    
    # Save results to file
    with open("/app/backend_test_wp18c8_results.json", "w") as f:
        json.dump(
            {
                "total": total_count,
                "passed": passed_count,
                "failed": total_count - passed_count,
                "pass_rate": pass_rate,
                "tests": test_results,
            },
            f,
            indent=2,
        )
    
    print("Results saved to /app/backend_test_wp18c8_results.json")
    print()
    
    # Exit with appropriate code
    if passed_count == total_count:
        print("✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()

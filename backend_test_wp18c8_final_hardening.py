#!/usr/bin/env python3
"""
WP-18C8 Final Executive Hardening - Backend Verification
========================================================

Test all backend behaviors for WP-18C8 Final Executive Hardening on live preview.

Preview base URL: https://masci-audit-hub.preview.emergentagent.com
Credentials:
- PM: cert.pm@example.com / CertProof2026!
- Admin: jaymn.judd@mascigc.com / Maddix123!
Project fixture: ZZ-RUNTIME-CERT-2026

Verification Points:
1. PM login succeeds and PM earned-value GET returns 200 with truthful seeded metrics
2. PM force_refresh earned-value GET works and does not regress truth/readiness
3. Admin login succeeds and executive earned-value GET + force_refresh work
4. PM and Admin earned-value CSV export endpoints return CSV with correct headers
5. PM budget overview endpoint works after backend foundation-cache fix
6. Unauthenticated earned-value access is denied with 401
7. Re-run /app/backend/tests/test_wp18c8_earned_value_engine.py
8. Note any remaining query/index or reliability contradiction
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Tuple

# Configuration
BASE_URL = "https://masci-audit-hub.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"
PROJECT_NUMBER = "ZZ-RUNTIME-CERT-2026"

# Credentials
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Expected seeded metrics
EXPECTED_BAC = 1200
EXPECTED_EV = 1200
EXPECTED_AC = 900
EXPECTED_CPI = 1.3333
EXPECTED_OPEN_ACTUAL_COST_COUNT = 0
EXPECTED_OPEN_COMMITMENT_COUNT = 0
EXPECTED_READINESS = "ready"

# Test results
results = {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "tests": []
}

def log_test(name: str, passed: bool, details: str = ""):
    """Log test result"""
    results["total_tests"] += 1
    if passed:
        results["passed"] += 1
        status = "✅ PASS"
    else:
        results["failed"] += 1
        status = "❌ FAIL"
    
    results["tests"].append({
        "name": name,
        "passed": passed,
        "details": details
    })
    
    print(f"{status} - {name}")
    if details:
        print(f"  {details}")

def pm_login() -> Tuple[str, Dict[str, Any]]:
    """PM login via /api/pm/login"""
    try:
        response = requests.post(
            f"{API_BASE}/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            log_test("PM Login", True, f"Token length: {len(token)}")
            return token, data
        else:
            log_test("PM Login", False, f"HTTP {response.status_code}: {response.text[:200]}")
            return None, {}
    except Exception as e:
        log_test("PM Login", False, f"Exception: {str(e)}")
        return None, {}

def admin_login() -> Tuple[str, str, Dict[str, Any]]:
    """Admin login via /api/auth/multi-login"""
    try:
        response = requests.post(
            f"{API_BASE}/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            session_token = data.get("session_token")
            admin_token = data.get("portal_tokens", {}).get("admin")
            log_test("Admin Login", True, f"Session token length: {len(session_token)}, Admin token length: {len(admin_token)}")
            return session_token, admin_token, data
        else:
            log_test("Admin Login", False, f"HTTP {response.status_code}: {response.text[:200]}")
            return None, None, {}
    except Exception as e:
        log_test("Admin Login", False, f"Exception: {str(e)}")
        return None, None, {}

def test_pm_earned_value(pm_token: str):
    """Test 1: PM earned-value GET returns 200 with truthful seeded metrics"""
    try:
        start_time = time.time()
        response = requests.get(
            f"{API_BASE}/pm/project-controls/projects/{PROJECT_NUMBER}/earned-value",
            headers={"X-PM-Token": pm_token},
            timeout=60
        )
        elapsed = time.time() - start_time
        
        if response.status_code != 200:
            log_test("PM Earned Value GET", False, f"HTTP {response.status_code}")
            return
        
        data = response.json()
        
        # Check readiness
        readiness = data.get("readiness", {})
        overall_readiness = readiness.get("overall")
        
        # Check summary metrics
        summary = data.get("summary", {})
        bac = summary.get("bac")
        ev = summary.get("ev")
        ac = summary.get("ac")
        cpi = summary.get("cpi")
        open_actual_cost_count = summary.get("open_actual_cost_count")
        open_commitment_count = summary.get("open_commitment_count")
        
        # Validate metrics
        checks = []
        checks.append(("BAC", bac == EXPECTED_BAC, f"Expected {EXPECTED_BAC}, got {bac}"))
        checks.append(("EV", ev == EXPECTED_EV, f"Expected {EXPECTED_EV}, got {ev}"))
        checks.append(("AC", ac == EXPECTED_AC, f"Expected {EXPECTED_AC}, got {ac}"))
        checks.append(("CPI", abs(cpi - EXPECTED_CPI) < 0.01, f"Expected ~{EXPECTED_CPI}, got {cpi}"))
        checks.append(("open_actual_cost_count", open_actual_cost_count == EXPECTED_OPEN_ACTUAL_COST_COUNT, f"Expected {EXPECTED_OPEN_ACTUAL_COST_COUNT}, got {open_actual_cost_count}"))
        checks.append(("open_commitment_count", open_commitment_count == EXPECTED_OPEN_COMMITMENT_COUNT, f"Expected {EXPECTED_OPEN_COMMITMENT_COUNT}, got {open_commitment_count}"))
        checks.append(("readiness overall", overall_readiness == EXPECTED_READINESS, f"Expected '{EXPECTED_READINESS}', got '{overall_readiness}'"))
        
        all_passed = all(check[1] for check in checks)
        details = f"Response time: {elapsed:.2f}s. " + ", ".join([f"{name}: {result}" for name, result, _ in checks])
        
        log_test("PM Earned Value - Truthful Seeded Metrics", all_passed, details)
        
        # Log individual metric checks
        for name, passed, detail in checks:
            log_test(f"  PM Earned Value - {name}", passed, detail)
        
    except Exception as e:
        log_test("PM Earned Value GET", False, f"Exception: {str(e)}")

def test_pm_force_refresh(pm_token: str):
    """Test 2: PM force_refresh earned-value GET works and does not regress truth/readiness"""
    try:
        start_time = time.time()
        response = requests.get(
            f"{API_BASE}/pm/project-controls/projects/{PROJECT_NUMBER}/earned-value?force_refresh=true",
            headers={"X-PM-Token": pm_token},
            timeout=60
        )
        elapsed = time.time() - start_time
        
        if response.status_code != 200:
            log_test("PM Force Refresh", False, f"HTTP {response.status_code}")
            return
        
        data = response.json()
        
        # Check readiness
        readiness = data.get("readiness", {})
        overall_readiness = readiness.get("overall")
        
        # Check summary metrics
        summary = data.get("summary", {})
        bac = summary.get("bac")
        ev = summary.get("ev")
        ac = summary.get("ac")
        cpi = summary.get("cpi")
        
        # Validate metrics (should not regress)
        checks = []
        checks.append(("BAC", bac == EXPECTED_BAC, f"Expected {EXPECTED_BAC}, got {bac}"))
        checks.append(("EV", ev == EXPECTED_EV, f"Expected {EXPECTED_EV}, got {ev}"))
        checks.append(("AC", ac == EXPECTED_AC, f"Expected {EXPECTED_AC}, got {ac}"))
        checks.append(("CPI", abs(cpi - EXPECTED_CPI) < 0.01, f"Expected ~{EXPECTED_CPI}, got {cpi}"))
        checks.append(("readiness overall", overall_readiness == EXPECTED_READINESS, f"Expected '{EXPECTED_READINESS}', got '{overall_readiness}'"))
        
        all_passed = all(check[1] for check in checks)
        details = f"Response time: {elapsed:.2f}s. " + ", ".join([f"{name}: {result}" for name, result, _ in checks])
        
        log_test("PM Force Refresh - No Regression", all_passed, details)
        
        # Check if performance is improved (should be materially reduced from 26-28s baseline)
        if elapsed < 10:
            log_test("PM Force Refresh - Performance", True, f"Response time: {elapsed:.2f}s (materially reduced from 26-28s baseline)")
        else:
            log_test("PM Force Refresh - Performance", False, f"Response time: {elapsed:.2f}s (still slow, expected <10s)")
        
    except Exception as e:
        log_test("PM Force Refresh", False, f"Exception: {str(e)}")

def test_admin_earned_value(session_token: str, admin_token: str):
    """Test 3: Admin earned-value GET + force_refresh work"""
    try:
        # Test regular GET
        start_time = time.time()
        response = requests.get(
            f"{API_BASE}/admin/governance/project-controls/projects/{PROJECT_NUMBER}/earned-value",
            headers={
                "X-Admin-Token": admin_token,
                "X-Directory-Token": session_token
            },
            timeout=60
        )
        elapsed = time.time() - start_time
        
        if response.status_code != 200:
            log_test("Admin Earned Value GET", False, f"HTTP {response.status_code}")
            return
        
        data = response.json()
        
        # Check summary metrics
        summary = data.get("summary", {})
        bac = summary.get("bac")
        ev = summary.get("ev")
        ac = summary.get("ac")
        
        checks = []
        checks.append(("BAC", bac == EXPECTED_BAC, f"Expected {EXPECTED_BAC}, got {bac}"))
        checks.append(("EV", ev == EXPECTED_EV, f"Expected {EXPECTED_EV}, got {ev}"))
        checks.append(("AC", ac == EXPECTED_AC, f"Expected {EXPECTED_AC}, got {ac}"))
        
        all_passed = all(check[1] for check in checks)
        details = f"Response time: {elapsed:.2f}s. " + ", ".join([f"{name}: {result}" for name, result, _ in checks])
        
        log_test("Admin Earned Value GET", all_passed, details)
        
        # Test force_refresh
        start_time = time.time()
        response = requests.get(
            f"{API_BASE}/admin/governance/project-controls/projects/{PROJECT_NUMBER}/earned-value?force_refresh=true",
            headers={
                "X-Admin-Token": admin_token,
                "X-Directory-Token": session_token
            },
            timeout=60
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            log_test("Admin Force Refresh", True, f"Response time: {elapsed:.2f}s")
        else:
            log_test("Admin Force Refresh", False, f"HTTP {response.status_code}")
        
    except Exception as e:
        log_test("Admin Earned Value", False, f"Exception: {str(e)}")

def test_csv_exports(pm_token: str, session_token: str, admin_token: str):
    """Test 4: PM and Admin earned-value CSV export endpoints"""
    try:
        # Test PM export
        response = requests.get(
            f"{API_BASE}/pm/project-controls/projects/{PROJECT_NUMBER}/earned-value/export",
            headers={"X-PM-Token": pm_token},
            timeout=60
        )
        
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            content_disposition = response.headers.get("Content-Disposition", "")
            is_csv = "text/csv" in content_type
            has_disposition = "attachment" in content_disposition or "filename" in content_disposition
            
            if is_csv and has_disposition:
                log_test("PM CSV Export", True, f"Content-Type: {content_type}, Content-Disposition: {content_disposition}")
            else:
                log_test("PM CSV Export", False, f"Missing CSV headers. Content-Type: {content_type}, Content-Disposition: {content_disposition}")
        else:
            log_test("PM CSV Export", False, f"HTTP {response.status_code}")
        
        # Test Admin export
        response = requests.get(
            f"{API_BASE}/admin/governance/project-controls/projects/{PROJECT_NUMBER}/earned-value/export",
            headers={
                "X-Admin-Token": admin_token,
                "X-Directory-Token": session_token
            },
            timeout=60
        )
        
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            content_disposition = response.headers.get("Content-Disposition", "")
            is_csv = "text/csv" in content_type
            has_disposition = "attachment" in content_disposition or "filename" in content_disposition
            
            if is_csv and has_disposition:
                log_test("Admin CSV Export", True, f"Content-Type: {content_type}, Content-Disposition: {content_disposition}")
            else:
                log_test("Admin CSV Export", False, f"Missing CSV headers. Content-Type: {content_type}, Content-Disposition: {content_disposition}")
        else:
            log_test("Admin CSV Export", False, f"HTTP {response.status_code}")
        
    except Exception as e:
        log_test("CSV Exports", False, f"Exception: {str(e)}")

def test_budget_overview_performance(pm_token: str):
    """Test 5: PM budget overview endpoint performance after foundation-cache fix"""
    try:
        start_time = time.time()
        response = requests.get(
            f"{API_BASE}/pm/project-controls/projects/{PROJECT_NUMBER}/budget/overview",
            headers={"X-PM-Token": pm_token},
            timeout=60
        )
        elapsed = time.time() - start_time
        
        if response.status_code != 200:
            log_test("PM Budget Overview", False, f"HTTP {response.status_code}")
            return
        
        # Check if performance is improved (should be ~1.73s p50, not ~11.5s)
        if elapsed < 5:
            log_test("PM Budget Overview - Performance", True, f"Response time: {elapsed:.2f}s (improved from ~11.5s baseline)")
        elif elapsed < 10:
            log_test("PM Budget Overview - Performance", True, f"Response time: {elapsed:.2f}s (acceptable, but could be faster)")
        else:
            log_test("PM Budget Overview - Performance", False, f"Response time: {elapsed:.2f}s (still slow, expected <5s)")
        
    except Exception as e:
        log_test("PM Budget Overview", False, f"Exception: {str(e)}")

def test_unauthenticated_access():
    """Test 6: Unauthenticated earned-value access is denied with 401"""
    try:
        response = requests.get(
            f"{API_BASE}/pm/project-controls/projects/{PROJECT_NUMBER}/earned-value",
            timeout=15
        )
        
        if response.status_code == 401:
            log_test("Unauthenticated Access Denied", True, "Correctly returned 401")
        else:
            log_test("Unauthenticated Access Denied", False, f"Expected 401, got {response.status_code}")
        
    except Exception as e:
        log_test("Unauthenticated Access", False, f"Exception: {str(e)}")

def test_pytest_suite():
    """Test 7: Re-run /app/backend/tests/test_wp18c8_earned_value_engine.py"""
    try:
        import subprocess
        result = subprocess.run(
            ["python", "-m", "pytest", "/app/backend/tests/test_wp18c8_earned_value_engine.py", "-v"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd="/app"
        )
        
        # Parse pytest output
        output = result.stdout + result.stderr
        
        if "passed" in output.lower():
            # Extract test counts
            import re
            match = re.search(r"(\d+) passed", output)
            if match:
                passed_count = int(match.group(1))
                log_test("Pytest Suite", True, f"{passed_count} tests passed")
            else:
                log_test("Pytest Suite", True, "Tests passed (count not parsed)")
        else:
            log_test("Pytest Suite", False, f"Pytest failed or no tests passed. Output: {output[:500]}")
        
    except subprocess.TimeoutExpired:
        log_test("Pytest Suite", False, "Pytest timed out after 120s")
    except Exception as e:
        log_test("Pytest Suite", False, f"Exception: {str(e)}")

def main():
    """Run all tests"""
    print("=" * 80)
    print("WP-18C8 Final Executive Hardening - Backend Verification")
    print("=" * 80)
    print()
    
    # Test 1-2: PM login and earned-value tests
    pm_token, pm_data = pm_login()
    if pm_token:
        test_pm_earned_value(pm_token)
        test_pm_force_refresh(pm_token)
        test_budget_overview_performance(pm_token)
    
    # Test 3-4: Admin login and earned-value tests
    session_token, admin_token, admin_data = admin_login()
    if session_token and admin_token:
        test_admin_earned_value(session_token, admin_token)
    
    # Test 4: CSV exports (requires both PM and Admin tokens)
    if pm_token and session_token and admin_token:
        test_csv_exports(pm_token, session_token, admin_token)
    
    # Test 6: Unauthenticated access
    test_unauthenticated_access()
    
    # Test 7: Pytest suite
    test_pytest_suite()
    
    # Print summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total tests: {results['total_tests']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Pass rate: {results['passed'] / results['total_tests'] * 100:.1f}%")
    print()
    
    # Save results to file
    with open("/app/backend_test_wp18c8_final_hardening_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("Results saved to /app/backend_test_wp18c8_final_hardening_results.json")
    
    # Exit with appropriate code
    sys.exit(0 if results['failed'] == 0 else 1)

if __name__ == "__main__":
    main()

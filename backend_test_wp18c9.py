"""
WP-18C9 Portfolio Intelligence Backend/Runtime Readiness Verification

Scope:
1. Admin endpoint family:
   - GET /api/admin/governance/project-controls/portfolio-intelligence
   - POST /api/admin/governance/project-controls/portfolio-intelligence/refresh
   - GET /api/admin/governance/project-controls/portfolio-intelligence/export
2. PM endpoint family:
   - GET /api/pm/project-controls/portfolio-intelligence
   - POST /api/pm/project-controls/portfolio-intelligence/refresh
   - GET /api/pm/project-controls/portfolio-intelligence/export
3. Inherited regression sanity:
   - Existing C7/C8 drill-back endpoints must still respond for at least one project.
4. Permission/privacy:
   - PM scope must stay restricted to forensic PM projects only.
   - Unauthenticated access should fail safely.
5. Truth checks:
   - schema_version should be WP18C9/v1
   - blocked_dependencies.open_blocked_by_c9_count should be 0
   - admin project count should be full scope; PM should only see ZZ-FOR-ASSIGN-01 and ZZ-FOR-ASSIGN-02
   - export endpoints should return CSV attachments

Credentials:
- Admin: jaymn.judd@mascigc.com / Maddix123!
- PM: pm.scope.forensic@example.com / ForensicPm2026!
"""

import json
import os
import sys
import time

import requests
from dotenv import dotenv_values


def _base_url():
    env_value = (os.environ.get("REACT_APP_BACKEND_URL") or "").rstrip("/")
    if env_value and ".preview.emergentagent.com" not in env_value:
        return env_value
    file_value = str((dotenv_values("/app/frontend/.env").get("REACT_APP_BACKEND_URL") or "")).rstrip("/")
    if file_value:
        return file_value
    return "http://127.0.0.1:8001"


BASE_URL = _base_url()
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
PM_EMAIL = "pm.scope.forensic@example.com"
PM_PASSWORD = "ForensicPm2026!"
PM_EXPECTED_PROJECTS = {"ZZ-FOR-ASSIGN-01", "ZZ-FOR-ASSIGN-02"}

results = {
    "test_suite": "WP-18C9 Portfolio Intelligence Backend Verification",
    "base_url": BASE_URL,
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    "tests": [],
    "summary": {"total": 0, "passed": 0, "failed": 0},
}


def log_test(name, status, details=None):
    """Log test result"""
    test_result = {
        "name": name,
        "status": status,
        "details": details or {},
    }
    results["tests"].append(test_result)
    results["summary"]["total"] += 1
    if status == "PASS":
        results["summary"]["passed"] += 1
        print(f"✅ PASS ({results['summary']['total']}) - {name}")
    else:
        results["summary"]["failed"] += 1
        print(f"❌ FAIL ({results['summary']['total']}) - {name}")
    if details:
        for key, value in details.items():
            print(f"   {key}: {value}")
    return status == "PASS"


def wait_for_backend(timeout_seconds=120):
    """Wait for backend to be ready"""
    print(f"Waiting for backend at {BASE_URL}...")
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend is ready")
                return True
        except Exception:
            pass
        time.sleep(2)
    print("❌ Backend health check timeout")
    return False


def test_admin_login():
    """Test 1: Admin Multi-Login"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "portal": "admin"},
            headers={"X-Device-Id": "wp18c9-test-admin", "X-Test-Rate-Limit-Bypass": "1"},
            timeout=120,
        )
        if response.status_code != 200:
            return log_test(
                "Admin Multi-Login",
                "FAIL",
                {"status_code": response.status_code, "error": response.text[:200]},
            )
        
        data = response.json()
        portal_tokens = data.get("portal_tokens") or {}
        admin_token = portal_tokens.get("admin") or data.get("admin_token") or data.get("token")
        directory_token = data.get("session_token") or data.get("directory_token")
        
        if not admin_token or not directory_token:
            return log_test(
                "Admin Multi-Login",
                "FAIL",
                {"error": "Missing admin_token or directory_token"},
            )
        
        return log_test(
            "Admin Multi-Login",
            "PASS",
            {
                "admin_token_length": len(admin_token),
                "directory_token_length": len(directory_token),
            },
        ), {"admin_token": admin_token, "directory_token": directory_token}
    except Exception as e:
        log_test("Admin Multi-Login", "FAIL", {"exception": str(e)})
        return False, None


def test_pm_login():
    """Test 2: PM Login"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            headers={"X-Device-Id": "wp18c9-test-pm", "X-Test-Rate-Limit-Bypass": "1"},
            timeout=120,
        )
        if response.status_code != 200:
            return log_test(
                "PM Login",
                "FAIL",
                {"status_code": response.status_code, "error": response.text[:200]},
            )
        
        data = response.json()
        pm_token = data.get("token") or data.get("access_token")
        
        if not pm_token:
            return log_test("PM Login", "FAIL", {"error": "Missing PM token"})
        
        return log_test(
            "PM Login",
            "PASS",
            {"pm_token_length": len(pm_token)},
        ), {"pm_token": pm_token}
    except Exception as e:
        log_test("PM Login", "FAIL", {"exception": str(e)})
        return False, None


def test_admin_portfolio_snapshot(admin_tokens):
    """Test 3: Admin Portfolio Intelligence Snapshot GET"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/portfolio-intelligence",
            headers={
                "X-Admin-Token": admin_tokens["admin_token"],
                "X-Directory-Token": admin_tokens["directory_token"],
            },
            timeout=180,
        )
        
        if response.status_code != 200:
            return log_test(
                "Admin Portfolio Snapshot GET",
                "FAIL",
                {"status_code": response.status_code, "error": response.text[:200]},
            )
        
        data = response.json()
        
        # Truth checks
        checks = {
            "schema_version": data.get("schema_version") == "WP18C9/v1",
            "audience": data.get("audience") == "executive",
            "has_projects": len(data.get("projects", [])) > 0,
            "blocked_dependencies_zero": data.get("blocked_dependencies", {}).get("open_blocked_by_c9_count") == 0,
            "has_portfolio_summary": "portfolio_summary" in data,
            "has_authority_contract": "authority_contract" in data,
        }
        
        project_count = data.get("scope", {}).get("project_count", 0)
        
        if not all(checks.values()):
            return log_test(
                "Admin Portfolio Snapshot GET",
                "FAIL",
                {
                    "checks": checks,
                    "schema_version": data.get("schema_version"),
                    "audience": data.get("audience"),
                    "project_count": project_count,
                    "blocked_count": data.get("blocked_dependencies", {}).get("open_blocked_by_c9_count"),
                },
            )
        
        return log_test(
            "Admin Portfolio Snapshot GET",
            "PASS",
            {
                "schema_version": data.get("schema_version"),
                "audience": data.get("audience"),
                "project_count": project_count,
                "blocked_dependencies_count": data.get("blocked_dependencies", {}).get("open_blocked_by_c9_count"),
                "priority_counts": data.get("portfolio_summary", {}).get("counts", {}),
            },
        )
    except Exception as e:
        return log_test(
            "Admin Portfolio Snapshot GET",
            "FAIL",
            {"exception": str(e)},
        )


def test_admin_portfolio_refresh(admin_tokens):
    """Test 4: Admin Portfolio Intelligence Refresh POST"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/governance/project-controls/portfolio-intelligence/refresh",
            headers={
                "X-Admin-Token": admin_tokens["admin_token"],
                "X-Directory-Token": admin_tokens["directory_token"],
            },
            timeout=300,
        )
        
        if response.status_code != 200:
            return log_test(
                "Admin Portfolio Refresh POST",
                "FAIL",
                {"status_code": response.status_code, "error": response.text[:200]},
            )
        
        data = response.json()
        
        # Verify refresh returns valid snapshot
        checks = {
            "schema_version": data.get("schema_version") == "WP18C9/v1",
            "blocked_dependencies_zero": data.get("blocked_dependencies", {}).get("open_blocked_by_c9_count") == 0,
            "has_projects": len(data.get("projects", [])) > 0,
        }
        
        if not all(checks.values()):
            return log_test(
                "Admin Portfolio Refresh POST",
                "FAIL",
                {"checks": checks},
            )
        
        return log_test(
            "Admin Portfolio Refresh POST",
            "PASS",
            {
                "schema_version": data.get("schema_version"),
                "project_count": data.get("scope", {}).get("project_count", 0),
                "cache_status": data.get("cache_status"),
            },
        )
    except Exception as e:
        return log_test(
            "Admin Portfolio Refresh POST",
            "FAIL",
            {"exception": str(e)},
        )


def test_admin_portfolio_export(admin_tokens):
    """Test 5: Admin Portfolio Intelligence Export GET"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/portfolio-intelligence/export",
            headers={
                "X-Admin-Token": admin_tokens["admin_token"],
                "X-Directory-Token": admin_tokens["directory_token"],
            },
            timeout=180,
        )
        
        if response.status_code != 200:
            return log_test(
                "Admin Portfolio Export GET",
                "FAIL",
                {"status_code": response.status_code, "error": response.text[:200]},
            )
        
        # Verify CSV response
        content_type = response.headers.get("content-type", "")
        content_disposition = response.headers.get("content-disposition", "")
        
        checks = {
            "is_csv": "text/csv" in content_type,
            "is_attachment": "attachment" in content_disposition,
            "has_content": len(response.text) > 0,
            "has_header": "project_number" in response.text.splitlines()[0] if response.text else False,
        }
        
        if not all(checks.values()):
            return log_test(
                "Admin Portfolio Export GET",
                "FAIL",
                {
                    "checks": checks,
                    "content_type": content_type,
                    "content_disposition": content_disposition,
                },
            )
        
        return log_test(
            "Admin Portfolio Export GET",
            "PASS",
            {
                "content_type": content_type,
                "content_length": len(response.text),
                "row_count": len(response.text.splitlines()) - 1,  # Exclude header
            },
        )
    except Exception as e:
        return log_test(
            "Admin Portfolio Export GET",
            "FAIL",
            {"exception": str(e)},
        )


def test_pm_portfolio_snapshot(pm_tokens):
    """Test 6: PM Portfolio Intelligence Snapshot GET (Scoped)"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/portfolio-intelligence",
            headers={"X-PM-Token": pm_tokens["pm_token"]},
            timeout=180,
        )
        
        if response.status_code != 200:
            return log_test(
                "PM Portfolio Snapshot GET (Scoped)",
                "FAIL",
                {"status_code": response.status_code, "error": response.text[:200]},
            )
        
        data = response.json()
        
        # PM scope checks
        project_numbers = {row.get("project_number") for row in data.get("projects", [])}
        
        checks = {
            "schema_version": data.get("schema_version") == "WP18C9/v1",
            "audience": data.get("audience") == "pm",
            "scope_mode": data.get("scope", {}).get("mode") == "scoped",
            "correct_projects": project_numbers == PM_EXPECTED_PROJECTS,
            "blocked_dependencies_zero": data.get("blocked_dependencies", {}).get("open_blocked_by_c9_count") == 0,
        }
        
        # Verify PM drilldowns start with /pm/
        drilldown_checks = []
        for row in data.get("projects", []):
            drilldowns = row.get("drilldowns", {})
            forecasting = str(drilldowns.get("forecasting", ""))
            earned_value = str(drilldowns.get("earned_value", ""))
            drilldown_checks.append(forecasting.startswith("/pm/") and earned_value.startswith("/pm/"))
        
        checks["pm_drilldowns"] = all(drilldown_checks) if drilldown_checks else False
        
        if not all(checks.values()):
            return log_test(
                "PM Portfolio Snapshot GET (Scoped)",
                "FAIL",
                {
                    "checks": checks,
                    "expected_projects": list(PM_EXPECTED_PROJECTS),
                    "actual_projects": list(project_numbers),
                    "audience": data.get("audience"),
                    "scope_mode": data.get("scope", {}).get("mode"),
                },
            )
        
        return log_test(
            "PM Portfolio Snapshot GET (Scoped)",
            "PASS",
            {
                "schema_version": data.get("schema_version"),
                "audience": data.get("audience"),
                "scope_mode": data.get("scope", {}).get("mode"),
                "project_count": len(project_numbers),
                "projects": list(project_numbers),
            },
        )
    except Exception as e:
        return log_test(
            "PM Portfolio Snapshot GET (Scoped)",
            "FAIL",
            {"exception": str(e)},
        )


def test_pm_portfolio_refresh(pm_tokens):
    """Test 7: PM Portfolio Intelligence Refresh POST"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/pm/project-controls/portfolio-intelligence/refresh",
            headers={"X-PM-Token": pm_tokens["pm_token"]},
            timeout=300,
        )
        
        if response.status_code != 200:
            return log_test(
                "PM Portfolio Refresh POST",
                "FAIL",
                {"status_code": response.status_code, "error": response.text[:200]},
            )
        
        data = response.json()
        project_numbers = {row.get("project_number") for row in data.get("projects", [])}
        
        checks = {
            "schema_version": data.get("schema_version") == "WP18C9/v1",
            "audience": data.get("audience") == "pm",
            "correct_projects": project_numbers == PM_EXPECTED_PROJECTS,
        }
        
        if not all(checks.values()):
            return log_test(
                "PM Portfolio Refresh POST",
                "FAIL",
                {"checks": checks},
            )
        
        return log_test(
            "PM Portfolio Refresh POST",
            "PASS",
            {
                "schema_version": data.get("schema_version"),
                "project_count": len(project_numbers),
                "cache_status": data.get("cache_status"),
            },
        )
    except Exception as e:
        return log_test(
            "PM Portfolio Refresh POST",
            "FAIL",
            {"exception": str(e)},
        )


def test_pm_portfolio_export(pm_tokens):
    """Test 8: PM Portfolio Intelligence Export GET"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/portfolio-intelligence/export",
            headers={"X-PM-Token": pm_tokens["pm_token"]},
            timeout=180,
        )
        
        if response.status_code != 200:
            return log_test(
                "PM Portfolio Export GET",
                "FAIL",
                {"status_code": response.status_code, "error": response.text[:200]},
            )
        
        content_type = response.headers.get("content-type", "")
        
        checks = {
            "is_csv": "text/csv" in content_type,
            "has_content": len(response.text) > 0,
        }
        
        if not all(checks.values()):
            return log_test(
                "PM Portfolio Export GET",
                "FAIL",
                {"checks": checks, "content_type": content_type},
            )
        
        return log_test(
            "PM Portfolio Export GET",
            "PASS",
            {
                "content_type": content_type,
                "content_length": len(response.text),
                "row_count": len(response.text.splitlines()) - 1,
            },
        )
    except Exception as e:
        return log_test(
            "PM Portfolio Export GET",
            "FAIL",
            {"exception": str(e)},
        )


def test_unauthenticated_access():
    """Test 9: Unauthenticated Access Should Fail"""
    endpoints = [
        "/api/admin/governance/project-controls/portfolio-intelligence",
        "/api/pm/project-controls/portfolio-intelligence",
    ]
    
    all_passed = True
    details = {}
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=30)
            if response.status_code in [401, 403]:
                details[endpoint] = f"Correctly rejected with {response.status_code}"
            else:
                details[endpoint] = f"FAIL: Expected 401/403, got {response.status_code}"
                all_passed = False
        except Exception as e:
            details[endpoint] = f"Exception: {str(e)}"
            all_passed = False
    
    return log_test(
        "Unauthenticated Access Should Fail",
        "PASS" if all_passed else "FAIL",
        details,
    )


def test_c7_c8_drillback_regression(admin_tokens):
    """Test 10: C7/C8 Drill-back Regression Sanity"""
    try:
        # First get portfolio snapshot to find a project
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/portfolio-intelligence",
            headers={
                "X-Admin-Token": admin_tokens["admin_token"],
                "X-Directory-Token": admin_tokens["directory_token"],
            },
            timeout=180,
        )
        
        if response.status_code != 200 or not response.json().get("projects"):
            return log_test(
                "C7/C8 Drill-back Regression Sanity",
                "FAIL",
                {"error": "No projects available for regression test"},
            )
        
        # Get first project
        project = response.json()["projects"][0]
        project_number = project.get("project_number")
        
        # Test C7 (Forecasting) endpoint
        c7_response = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/projects/{project_number}/forecasting/workspace",
            headers={
                "X-Admin-Token": admin_tokens["admin_token"],
                "X-Directory-Token": admin_tokens["directory_token"],
            },
            timeout=180,
        )
        
        # Test C8 (Earned Value) endpoint
        c8_response = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/projects/{project_number}/earned-value",
            headers={
                "X-Admin-Token": admin_tokens["admin_token"],
                "X-Directory-Token": admin_tokens["directory_token"],
            },
            timeout=180,
        )
        
        checks = {
            "c7_accessible": c7_response.status_code == 200,
            "c8_accessible": c8_response.status_code == 200,
        }
        
        if not all(checks.values()):
            return log_test(
                "C7/C8 Drill-back Regression Sanity",
                "FAIL",
                {
                    "project_number": project_number,
                    "c7_status": c7_response.status_code,
                    "c8_status": c8_response.status_code,
                },
            )
        
        return log_test(
            "C7/C8 Drill-back Regression Sanity",
            "PASS",
            {
                "project_number": project_number,
                "c7_status": c7_response.status_code,
                "c8_status": c8_response.status_code,
            },
        )
    except Exception as e:
        return log_test(
            "C7/C8 Drill-back Regression Sanity",
            "FAIL",
            {"exception": str(e)},
        )


def main():
    """Main test execution"""
    print("=" * 80)
    print("WP-18C9 Portfolio Intelligence Backend/Runtime Readiness Verification")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {results['timestamp']}")
    print("=" * 80)
    
    # Wait for backend
    if not wait_for_backend():
        print("\n❌ Backend not ready. Exiting.")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("AUTHENTICATION TESTS")
    print("=" * 80)
    
    # Test 1: Admin Login
    admin_success, admin_tokens = test_admin_login()
    if not admin_success:
        print("\n❌ Admin login failed. Cannot continue with admin tests.")
        admin_tokens = None
    
    # Test 2: PM Login
    pm_success, pm_tokens = test_pm_login()
    if not pm_success:
        print("\n❌ PM login failed. Cannot continue with PM tests.")
        pm_tokens = None
    
    print("\n" + "=" * 80)
    print("ADMIN ENDPOINT TESTS")
    print("=" * 80)
    
    if admin_tokens:
        # Test 3: Admin Portfolio Snapshot GET
        test_admin_portfolio_snapshot(admin_tokens)
        
        # Test 4: Admin Portfolio Refresh POST
        test_admin_portfolio_refresh(admin_tokens)
        
        # Test 5: Admin Portfolio Export GET
        test_admin_portfolio_export(admin_tokens)
    else:
        log_test("Admin Portfolio Snapshot GET", "SKIP", {"reason": "Admin login failed"})
        log_test("Admin Portfolio Refresh POST", "SKIP", {"reason": "Admin login failed"})
        log_test("Admin Portfolio Export GET", "SKIP", {"reason": "Admin login failed"})
    
    print("\n" + "=" * 80)
    print("PM ENDPOINT TESTS")
    print("=" * 80)
    
    if pm_tokens:
        # Test 6: PM Portfolio Snapshot GET (Scoped)
        test_pm_portfolio_snapshot(pm_tokens)
        
        # Test 7: PM Portfolio Refresh POST
        test_pm_portfolio_refresh(pm_tokens)
        
        # Test 8: PM Portfolio Export GET
        test_pm_portfolio_export(pm_tokens)
    else:
        log_test("PM Portfolio Snapshot GET (Scoped)", "SKIP", {"reason": "PM login failed"})
        log_test("PM Portfolio Refresh POST", "SKIP", {"reason": "PM login failed"})
        log_test("PM Portfolio Export GET", "SKIP", {"reason": "PM login failed"})
    
    print("\n" + "=" * 80)
    print("SECURITY & REGRESSION TESTS")
    print("=" * 80)
    
    # Test 9: Unauthenticated Access
    test_unauthenticated_access()
    
    # Test 10: C7/C8 Drill-back Regression
    if admin_tokens:
        test_c7_c8_drillback_regression(admin_tokens)
    else:
        log_test("C7/C8 Drill-back Regression Sanity", "SKIP", {"reason": "Admin login failed"})
    
    # Save results
    with open("/app/backend_test_wp18c9_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {results['summary']['total']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Pass Rate: {results['summary']['passed'] / results['summary']['total'] * 100:.1f}%")
    print("=" * 80)
    
    if results['summary']['failed'] > 0:
        print("\n❌ VERIFICATION FAILED - Some tests did not pass")
        sys.exit(1)
    else:
        print("\n✅ VERIFICATION COMPLETE - All tests passed")
        sys.exit(0)


if __name__ == "__main__":
    main()

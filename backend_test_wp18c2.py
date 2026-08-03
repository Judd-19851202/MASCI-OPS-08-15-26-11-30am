#!/usr/bin/env python3
"""
WP-18C2 Project Controls Backend Verification
Focused backend verification for WP-18C2 project-controls foundation.

Test Scope:
1. Admin endpoints for project-controls
2. PM endpoints for assigned project ZZ-RUNTIME-CERT-2026
3. Daily Report compatibility evidence (work_blocks/work_block_summary)
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "https://masci-audit-hub.preview.emergentagent.com/api"

# Credentials from test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"

# Test project
ASSIGNED_PROJECT = "ZZ-RUNTIME-CERT-2026"
UNASSIGNED_PROJECT = "ZZ-UNASSIGNED-TEST-PROJECT"

results = {
    "test_run_timestamp": datetime.utcnow().isoformat() + "Z",
    "base_url": BASE_URL,
    "tests": []
}

def log_test(test_name, passed, details):
    """Log test result"""
    result = {
        "test": test_name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    results["tests"].append(result)
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if not passed:
        print(f"  Details: {details}")
    return passed

def admin_login():
    """Test 1: Admin Multi-Login"""
    print("\n=== TEST 1: Admin Multi-Login ===")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            session_token = data.get("session_token")
            portal_tokens = data.get("portal_tokens", {})
            admin_token = portal_tokens.get("admin")
            
            if session_token and admin_token:
                log_test(
                    "Admin Multi-Login",
                    True,
                    f"Login successful. Session token length: {len(session_token)}, Admin token length: {len(admin_token)}"
                )
                return session_token, admin_token
            else:
                log_test(
                    "Admin Multi-Login",
                    False,
                    f"Missing tokens in response. session_token: {bool(session_token)}, admin_token: {bool(admin_token)}"
                )
                return None, None
        else:
            log_test(
                "Admin Multi-Login",
                False,
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
            return None, None
    except Exception as e:
        log_test("Admin Multi-Login", False, f"Exception: {str(e)}")
        return None, None

def pm_login():
    """Test 2: PM Multi-Login"""
    print("\n=== TEST 2: PM Multi-Login ===")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/multi-login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            session_token = data.get("session_token")
            portal_tokens = data.get("portal_tokens", {})
            pm_token = portal_tokens.get("pm")
            
            if session_token and pm_token:
                log_test(
                    "PM Multi-Login",
                    True,
                    f"Login successful. Session token length: {len(session_token)}, PM token length: {len(pm_token)}"
                )
                return session_token, pm_token
            else:
                log_test(
                    "PM Multi-Login",
                    False,
                    f"Missing tokens in response. session_token: {bool(session_token)}, pm_token: {bool(pm_token)}"
                )
                return None, None
        else:
            log_test(
                "PM Multi-Login",
                False,
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
            return None, None
    except Exception as e:
        log_test("PM Multi-Login", False, f"Exception: {str(e)}")
        return None, None

def test_admin_work_types(session_token, admin_token):
    """Test 3: Admin Work Types Endpoint"""
    print("\n=== TEST 3: Admin Work Types Endpoint ===")
    try:
        headers = {
            "X-Directory-Token": session_token,
            "X-Admin-Token": admin_token
        }
        response = requests.get(
            f"{BASE_URL}/admin/governance/project-controls/work-types",
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            work_types_count = len(data) if isinstance(data, list) else data.get("count", 0)
            log_test(
                "Admin Work Types Endpoint",
                True,
                f"HTTP 200. Work types count: {work_types_count}"
            )
            return True
        else:
            log_test(
                "Admin Work Types Endpoint",
                False,
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
            return False
    except Exception as e:
        log_test("Admin Work Types Endpoint", False, f"Exception: {str(e)}")
        return False

def test_admin_overview(session_token, admin_token):
    """Test 4: Admin Overview Endpoint"""
    print("\n=== TEST 4: Admin Overview Endpoint ===")
    try:
        headers = {
            "X-Directory-Token": session_token,
            "X-Admin-Token": admin_token
        }
        response = requests.get(
            f"{BASE_URL}/admin/governance/project-controls/overview",
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            log_test(
                "Admin Overview Endpoint",
                True,
                f"HTTP 200. Response keys: {list(data.keys()) if isinstance(data, dict) else 'list response'}"
            )
            return True
        else:
            log_test(
                "Admin Overview Endpoint",
                False,
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
            return False
    except Exception as e:
        log_test("Admin Overview Endpoint", False, f"Exception: {str(e)}")
        return False

def test_admin_review_queue(session_token, admin_token):
    """Test 5: Admin Review Queue Endpoint"""
    print("\n=== TEST 5: Admin Review Queue Endpoint ===")
    try:
        headers = {
            "X-Directory-Token": session_token,
            "X-Admin-Token": admin_token
        }
        response = requests.get(
            f"{BASE_URL}/admin/governance/project-controls/review-queue",
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            queue_count = len(data) if isinstance(data, list) else data.get("count", 0)
            log_test(
                "Admin Review Queue Endpoint",
                True,
                f"HTTP 200. Review queue count: {queue_count}"
            )
            return True
        else:
            log_test(
                "Admin Review Queue Endpoint",
                False,
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
            return False
    except Exception as e:
        log_test("Admin Review Queue Endpoint", False, f"Exception: {str(e)}")
        return False

def test_pm_overview(session_token, pm_token, project=None):
    """Test 6: PM Overview Endpoint"""
    print(f"\n=== TEST 6: PM Overview Endpoint{' (Project: ' + project + ')' if project else ''} ===")
    try:
        headers = {
            "X-Directory-Token": session_token,
            "X-PM-Token": pm_token
        }
        url = f"{BASE_URL}/pm/project-controls/overview"
        if project:
            url += f"?project_number={project}"
        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            test_name = f"PM Overview Endpoint{' (' + project + ')' if project else ''}"
            log_test(
                test_name,
                True,
                f"HTTP 200. Response keys: {list(data.keys()) if isinstance(data, dict) else 'list response'}"
            )
            return True
        else:
            test_name = f"PM Overview Endpoint{' (' + project + ')' if project else ''}"
            log_test(
                test_name,
                False,
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
            return False
    except Exception as e:
        test_name = f"PM Overview Endpoint{' (' + project + ')' if project else ''}"
        log_test(test_name, False, f"Exception: {str(e)}")
        return False

def test_pm_pay_items(session_token, pm_token, project):
    """Test 7: PM Pay Items Endpoint"""
    print(f"\n=== TEST 7: PM Pay Items Endpoint (Project: {project}) ===")
    try:
        headers = {
            "X-Directory-Token": session_token,
            "X-PM-Token": pm_token
        }
        response = requests.get(
            f"{BASE_URL}/pm/project-controls/projects/{project}/pay-items",
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            items_count = len(data) if isinstance(data, list) else data.get("count", 0)
            log_test(
                f"PM Pay Items Endpoint ({project})",
                True,
                f"HTTP 200. Pay items count: {items_count}"
            )
            return True
        else:
            log_test(
                f"PM Pay Items Endpoint ({project})",
                False,
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
            return False
    except Exception as e:
        log_test(f"PM Pay Items Endpoint ({project})", False, f"Exception: {str(e)}")
        return False

def test_pm_mappings(session_token, pm_token, project):
    """Test 8: PM Mappings Endpoint"""
    print(f"\n=== TEST 8: PM Mappings Endpoint (Project: {project}) ===")
    try:
        headers = {
            "X-Directory-Token": session_token,
            "X-PM-Token": pm_token
        }
        response = requests.get(
            f"{BASE_URL}/pm/project-controls/projects/{project}/mappings",
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            mappings_count = len(data) if isinstance(data, list) else data.get("count", 0)
            log_test(
                f"PM Mappings Endpoint ({project})",
                True,
                f"HTTP 200. Mappings count: {mappings_count}"
            )
            return True
        else:
            log_test(
                f"PM Mappings Endpoint ({project})",
                False,
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
            return False
    except Exception as e:
        log_test(f"PM Mappings Endpoint ({project})", False, f"Exception: {str(e)}")
        return False

def test_pm_lookahead(session_token, pm_token, project):
    """Test 9: PM Lookahead Endpoint"""
    print(f"\n=== TEST 9: PM Lookahead Endpoint (Project: {project}) ===")
    try:
        headers = {
            "X-Directory-Token": session_token,
            "X-PM-Token": pm_token
        }
        response = requests.get(
            f"{BASE_URL}/pm/project-controls/projects/{project}/lookahead",
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            log_test(
                f"PM Lookahead Endpoint ({project})",
                True,
                f"HTTP 200. Response keys: {list(data.keys()) if isinstance(data, dict) else 'list response'}"
            )
            return True
        else:
            log_test(
                f"PM Lookahead Endpoint ({project})",
                False,
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
            return False
    except Exception as e:
        log_test(f"PM Lookahead Endpoint ({project})", False, f"Exception: {str(e)}")
        return False

def test_pm_lifecycle(session_token, pm_token, project):
    """Test 10: PM Lifecycle Endpoint"""
    print(f"\n=== TEST 10: PM Lifecycle Endpoint (Project: {project}) ===")
    try:
        headers = {
            "X-Directory-Token": session_token,
            "X-PM-Token": pm_token
        }
        response = requests.get(
            f"{BASE_URL}/pm/project-controls/projects/{project}/lifecycle",
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            log_test(
                f"PM Lifecycle Endpoint ({project})",
                True,
                f"HTTP 200. Response keys: {list(data.keys()) if isinstance(data, dict) else 'list response'}"
            )
            return True
        else:
            log_test(
                f"PM Lifecycle Endpoint ({project})",
                False,
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
            return False
    except Exception as e:
        log_test(f"PM Lifecycle Endpoint ({project})", False, f"Exception: {str(e)}")
        return False

def test_pm_crew_intelligence(session_token, pm_token, project):
    """Test 11: PM Crew Intelligence Endpoint"""
    print(f"\n=== TEST 11: PM Crew Intelligence Endpoint (Project: {project}) ===")
    try:
        headers = {
            "X-Directory-Token": session_token,
            "X-PM-Token": pm_token
        }
        response = requests.get(
            f"{BASE_URL}/pm/project-controls/projects/{project}/crew-intelligence",
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            log_test(
                f"PM Crew Intelligence Endpoint ({project})",
                True,
                f"HTTP 200. Response keys: {list(data.keys()) if isinstance(data, dict) else 'list response'}"
            )
            return True
        else:
            log_test(
                f"PM Crew Intelligence Endpoint ({project})",
                False,
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
            return False
    except Exception as e:
        log_test(f"PM Crew Intelligence Endpoint ({project})", False, f"Exception: {str(e)}")
        return False

def test_pm_work_ledger(session_token, pm_token, project):
    """Test 12: PM Work Ledger Endpoint"""
    print(f"\n=== TEST 12: PM Work Ledger Endpoint (Project: {project}) ===")
    try:
        headers = {
            "X-Directory-Token": session_token,
            "X-PM-Token": pm_token
        }
        response = requests.get(
            f"{BASE_URL}/pm/project-controls/projects/{project}/work-ledger",
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            log_test(
                f"PM Work Ledger Endpoint ({project})",
                True,
                f"HTTP 200. Response keys: {list(data.keys()) if isinstance(data, dict) else 'list response'}"
            )
            return True
        else:
            log_test(
                f"PM Work Ledger Endpoint ({project})",
                False,
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
            return False
    except Exception as e:
        log_test(f"PM Work Ledger Endpoint ({project})", False, f"Exception: {str(e)}")
        return False

def test_pm_scope_denial(session_token, pm_token, unassigned_project):
    """Test 13: PM Scope Denial on Unassigned Project"""
    print(f"\n=== TEST 13: PM Scope Denial (Unassigned Project: {unassigned_project}) ===")
    try:
        headers = {
            "X-Directory-Token": session_token,
            "X-PM-Token": pm_token
        }
        response = requests.get(
            f"{BASE_URL}/pm/project-controls/projects/{unassigned_project}/pay-items",
            headers=headers,
            timeout=15
        )
        
        # Expecting 403 or 404 for unassigned project
        if response.status_code in [403, 404]:
            log_test(
                f"PM Scope Denial ({unassigned_project})",
                True,
                f"HTTP {response.status_code}. Correctly denied access to unassigned project."
            )
            return True
        elif response.status_code == 200:
            log_test(
                f"PM Scope Denial ({unassigned_project})",
                False,
                f"HTTP 200. SECURITY ISSUE: PM should not have access to unassigned project."
            )
            return False
        else:
            log_test(
                f"PM Scope Denial ({unassigned_project})",
                False,
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
            return False
    except Exception as e:
        log_test(f"PM Scope Denial ({unassigned_project})", False, f"Exception: {str(e)}")
        return False

def test_daily_report_work_blocks(session_token, admin_token):
    """Test 14: Daily Report Work Blocks Compatibility"""
    print("\n=== TEST 14: Daily Report Work Blocks Compatibility ===")
    try:
        headers = {
            "X-Directory-Token": session_token,
            "X-Admin-Token": admin_token
        }
        
        # First, get a list of daily reports
        response = requests.get(
            f"{BASE_URL}/daily-reports?limit=10",
            headers=headers,
            timeout=15
        )
        
        if response.status_code != 200:
            log_test(
                "Daily Report Work Blocks Compatibility",
                False,
                f"Failed to fetch daily reports list. HTTP {response.status_code}"
            )
            return False
        
        reports = response.json()
        if not reports or len(reports) == 0:
            log_test(
                "Daily Report Work Blocks Compatibility",
                False,
                "No daily reports found to test work_blocks compatibility"
            )
            return False
        
        # Get the first report detail
        report_id = reports[0].get("id") if isinstance(reports, list) else reports.get("items", [{}])[0].get("id")
        
        if not report_id:
            log_test(
                "Daily Report Work Blocks Compatibility",
                False,
                "Could not extract report ID from response"
            )
            return False
        
        response = requests.get(
            f"{BASE_URL}/daily-reports/{report_id}",
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for work_blocks or work_block_summary fields
            has_work_blocks = "work_blocks" in data
            has_work_block_summary = "work_block_summary" in data
            has_compatibility_version = "compatibility_version" in data or "version" in data
            
            if has_work_blocks or has_work_block_summary:
                log_test(
                    "Daily Report Work Blocks Compatibility",
                    True,
                    f"HTTP 200. work_blocks: {has_work_blocks}, work_block_summary: {has_work_block_summary}, compatibility_version: {has_compatibility_version}"
                )
                return True
            else:
                log_test(
                    "Daily Report Work Blocks Compatibility",
                    False,
                    f"HTTP 200 but work_blocks/work_block_summary fields not found in response. Available keys: {list(data.keys())}"
                )
                return False
        else:
            log_test(
                "Daily Report Work Blocks Compatibility",
                False,
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
            return False
    except Exception as e:
        log_test("Daily Report Work Blocks Compatibility", False, f"Exception: {str(e)}")
        return False

def main():
    """Main test execution"""
    print("=" * 80)
    print("WP-18C2 PROJECT CONTROLS BACKEND VERIFICATION")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Test Run: {results['test_run_timestamp']}")
    print("=" * 80)
    
    # Test 1 & 2: Authentication
    admin_session, admin_token = admin_login()
    pm_session, pm_token = pm_login()
    
    if not admin_session or not admin_token:
        print("\n❌ CRITICAL: Admin authentication failed. Cannot proceed with admin tests.")
        results["summary"] = "FAILED - Admin authentication failed"
        with open("/app/backend_test_wp18c2_results.json", "w") as f:
            json.dump(results, f, indent=2)
        return 1
    
    if not pm_session or not pm_token:
        print("\n❌ CRITICAL: PM authentication failed. Cannot proceed with PM tests.")
        results["summary"] = "FAILED - PM authentication failed"
        with open("/app/backend_test_wp18c2_results.json", "w") as f:
            json.dump(results, f, indent=2)
        return 1
    
    # Test 3-5: Admin Endpoints
    admin_tests = [
        test_admin_work_types(admin_session, admin_token),
        test_admin_overview(admin_session, admin_token),
        test_admin_review_queue(admin_session, admin_token)
    ]
    
    # Test 6-12: PM Endpoints for Assigned Project
    pm_tests = [
        test_pm_overview(pm_session, pm_token, ASSIGNED_PROJECT),
        test_pm_pay_items(pm_session, pm_token, ASSIGNED_PROJECT),
        test_pm_mappings(pm_session, pm_token, ASSIGNED_PROJECT),
        test_pm_lookahead(pm_session, pm_token, ASSIGNED_PROJECT),
        test_pm_lifecycle(pm_session, pm_token, ASSIGNED_PROJECT),
        test_pm_crew_intelligence(pm_session, pm_token, ASSIGNED_PROJECT),
        test_pm_work_ledger(pm_session, pm_token, ASSIGNED_PROJECT)
    ]
    
    # Test 13: PM Scope Denial
    scope_test = test_pm_scope_denial(pm_session, pm_token, UNASSIGNED_PROJECT)
    
    # Test 14: Daily Report Work Blocks Compatibility
    dr_test = test_daily_report_work_blocks(admin_session, admin_token)
    
    # Calculate results
    total_tests = len(results["tests"])
    passed_tests = sum(1 for t in results["tests"] if t["passed"])
    failed_tests = total_tests - passed_tests
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    print("=" * 80)
    
    # Detailed summary
    if failed_tests == 0:
        results["summary"] = f"✅ ALL TESTS PASSED ({passed_tests}/{total_tests}, 100%)"
        print(f"\n✅ SUCCESS: All {passed_tests} tests passed!")
    else:
        results["summary"] = f"❌ SOME TESTS FAILED ({passed_tests}/{total_tests}, {pass_rate:.1f}%)"
        print(f"\n⚠️ WARNING: {failed_tests} test(s) failed")
        print("\nFailed Tests:")
        for test in results["tests"]:
            if not test["passed"]:
                print(f"  - {test['test']}: {test['details']}")
    
    # Save results
    with open("/app/backend_test_wp18c2_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: /app/backend_test_wp18c2_results.json")
    
    return 0 if failed_tests == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

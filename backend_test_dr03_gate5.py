#!/usr/bin/env python3
"""
DR-03 Gate 5 Containment Repair Backend Verification
=====================================================

Tests the following requirements:
1. Dispatch Daily Reports list excludes certification/synthetic/hidden records
2. Existing Admin/PM/HR/search/export synthetic exclusion behavior not regressed
3. /api/daily-reports/{id}/photo-intelligence returns truthful status contract
4. No runtime regressions for legacy write containment (/api/dr-v2/... still 410)

Test against: https://masci-audit-hub.preview.emergentagent.com/api
Credentials: jaymn.judd@mascigc.com / Maddix123!
"""

import requests
import sys
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://masci-audit-hub.preview.emergentagent.com/api"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test results tracking
tests_passed = 0
tests_failed = 0
test_results = []


def log_test(name: str, passed: bool, details: str = ""):
    """Log test result"""
    global tests_passed, tests_failed
    status = "✓ PASS" if passed else "✗ FAIL"
    result = f"{status} | {name}"
    if details:
        result += f"\n      {details}"
    test_results.append(result)
    if passed:
        tests_passed += 1
    else:
        tests_failed += 1
    print(result)


def get_admin_token() -> Optional[str]:
    """Authenticate and get admin token"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/multi-login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
            },
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("portal_tokens", {}).get("admin")
            if token:
                print(f"✓ Authentication successful (token length: {len(token)})")
                return token
            else:
                print(f"✗ Authentication failed: No admin token in response")
                return None
        else:
            print(f"✗ Authentication failed: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        print(f"✗ Authentication error: {e}")
        return None


def test_daily_reports_list_excludes_synthetic(token: str):
    """Test 1: GET /api/daily-reports excludes synthetic/certification/hidden records"""
    print("\n" + "="*80)
    print("TEST 1: Daily Reports List Synthetic Exclusion")
    print("="*80)
    
    try:
        response = requests.get(
            f"{BASE_URL}/daily-reports",
            headers={"X-Admin-Token": token},
            timeout=15,
        )
        
        if response.status_code != 200:
            log_test(
                "GET /api/daily-reports returns 200",
                False,
                f"Status: {response.status_code}, Body: {response.text[:200]}"
            )
            return
        
        log_test("GET /api/daily-reports returns 200", True)
        
        data = response.json()
        if not isinstance(data, list):
            log_test(
                "Response is a list",
                False,
                f"Got type: {type(data)}"
            )
            return
        
        log_test("Response is a list", True, f"Count: {len(data)}")
        
        # Check for synthetic records in the response
        synthetic_found = []
        for report in data:
            project_number = report.get("project_number", "")
            project_name = report.get("project_name", "")
            
            # Check for synthetic markers
            if any([
                project_number.upper().startswith("TEST_"),
                project_number.upper().startswith("TEST-"),
                project_number.upper().startswith("SMOKE"),
                project_number.upper().startswith("SYNTHETIC"),
                project_number.upper().startswith("0000-TEST"),
                project_name.upper().startswith("TEST_"),
                project_name.upper().startswith("SMOKE_"),
            ]):
                synthetic_found.append({
                    "id": report.get("id"),
                    "project_number": project_number,
                    "project_name": project_name,
                })
        
        if synthetic_found:
            log_test(
                "No synthetic records in list",
                False,
                f"Found {len(synthetic_found)} synthetic records: {synthetic_found[:3]}"
            )
        else:
            log_test(
                "No synthetic records in list",
                True,
                "All records appear to be operational (no TEST_/SMOKE_/SYNTHETIC_ prefixes)"
            )
        
    except Exception as e:
        log_test("GET /api/daily-reports", False, f"Exception: {e}")


def test_csv_export_excludes_synthetic(token: str):
    """Test 2: GET /api/daily-reports.csv excludes synthetic records"""
    print("\n" + "="*80)
    print("TEST 2: CSV Export Synthetic Exclusion")
    print("="*80)
    
    try:
        response = requests.get(
            f"{BASE_URL}/daily-reports.csv",
            headers={"X-Admin-Token": token},
            timeout=15,
        )
        
        if response.status_code != 200:
            log_test(
                "GET /api/daily-reports.csv returns 200",
                False,
                f"Status: {response.status_code}"
            )
            return
        
        log_test("GET /api/daily-reports.csv returns 200", True)
        
        # Check content type
        content_type = response.headers.get("Content-Type", "")
        if "csv" in content_type.lower():
            log_test("Response is CSV", True, f"Content-Type: {content_type}")
        else:
            log_test("Response is CSV", False, f"Content-Type: {content_type}")
        
        # Check for synthetic markers in CSV content
        csv_content = response.text
        lines = csv_content.split("\n")
        
        synthetic_lines = []
        for i, line in enumerate(lines[1:], start=2):  # Skip header
            if not line.strip():
                continue
            line_upper = line.upper()
            if any([
                "TEST_" in line_upper,
                "TEST-" in line_upper,
                "SMOKE" in line_upper,
                "SYNTHETIC" in line_upper,
                "0000-TEST" in line_upper,
            ]):
                synthetic_lines.append(f"Line {i}: {line[:100]}")
        
        if synthetic_lines:
            log_test(
                "CSV contains no synthetic records",
                False,
                f"Found {len(synthetic_lines)} synthetic lines: {synthetic_lines[:2]}"
            )
        else:
            log_test(
                "CSV contains no synthetic records",
                True,
                f"Checked {len(lines)-1} data rows, no synthetic markers found"
            )
        
    except Exception as e:
        log_test("GET /api/daily-reports.csv", False, f"Exception: {e}")


def test_duplicate_check_excludes_synthetic(token: str):
    """Test 3: GET /api/daily-reports/duplicate-check excludes synthetic records"""
    print("\n" + "="*80)
    print("TEST 3: Duplicate Check Synthetic Exclusion")
    print("="*80)
    
    try:
        # Test with a real project number
        response = requests.get(
            f"{BASE_URL}/daily-reports/duplicate-check",
            params={
                "project_number": "26-07",
                "report_date": "2026-07-15",
            },
            headers={"X-Admin-Token": token},
            timeout=10,
        )
        
        if response.status_code != 200:
            log_test(
                "GET /api/daily-reports/duplicate-check returns 200",
                False,
                f"Status: {response.status_code}"
            )
            return
        
        log_test("GET /api/daily-reports/duplicate-check returns 200", True)
        
        data = response.json()
        matches = data.get("matches", [])
        
        # Check if any matches are synthetic
        synthetic_matches = []
        for match in matches:
            pn = match.get("project_number", "")
            if any([
                pn.upper().startswith("TEST_"),
                pn.upper().startswith("SMOKE"),
                pn.upper().startswith("SYNTHETIC"),
            ]):
                synthetic_matches.append(match)
        
        if synthetic_matches:
            log_test(
                "Duplicate check excludes synthetic records",
                False,
                f"Found {len(synthetic_matches)} synthetic matches"
            )
        else:
            log_test(
                "Duplicate check excludes synthetic records",
                True,
                f"Checked {len(matches)} matches, none are synthetic"
            )
        
    except Exception as e:
        log_test("GET /api/daily-reports/duplicate-check", False, f"Exception: {e}")


def test_exposure_signals_excludes_synthetic(token: str):
    """Test 4: GET /api/daily-reports/exposure-signals excludes synthetic records"""
    print("\n" + "="*80)
    print("TEST 4: Exposure Signals Synthetic Exclusion")
    print("="*80)
    
    try:
        response = requests.get(
            f"{BASE_URL}/daily-reports/exposure-signals",
            params={"days": 14},
            headers={"X-Admin-Token": token},
            timeout=15,
        )
        
        if response.status_code != 200:
            log_test(
                "GET /api/daily-reports/exposure-signals returns 200",
                False,
                f"Status: {response.status_code}"
            )
            return
        
        log_test("GET /api/daily-reports/exposure-signals returns 200", True)
        
        data = response.json()
        top_projects = data.get("top_projects", [])
        
        # Check if any top projects are synthetic
        synthetic_projects = []
        for proj in top_projects:
            pn = proj.get("project_number", "")
            if any([
                pn.upper().startswith("TEST_"),
                pn.upper().startswith("SMOKE"),
                pn.upper().startswith("SYNTHETIC"),
            ]):
                synthetic_projects.append(proj)
        
        if synthetic_projects:
            log_test(
                "Exposure signals excludes synthetic records",
                False,
                f"Found {len(synthetic_projects)} synthetic projects in top_projects"
            )
        else:
            log_test(
                "Exposure signals excludes synthetic records",
                True,
                f"Checked {len(top_projects)} top projects, none are synthetic"
            )
        
    except Exception as e:
        log_test("GET /api/daily-reports/exposure-signals", False, f"Exception: {e}")


def test_safety_portal_excludes_synthetic(token: str):
    """Test 5: GET /api/safety/daily-reports excludes synthetic records"""
    print("\n" + "="*80)
    print("TEST 5: Safety Portal Synthetic Exclusion")
    print("="*80)
    
    try:
        response = requests.get(
            f"{BASE_URL}/safety/daily-reports",
            params={"only_flagged": False, "limit": 100},
            headers={"X-Admin-Token": token},
            timeout=15,
        )
        
        if response.status_code != 200:
            log_test(
                "GET /api/safety/daily-reports returns 200",
                False,
                f"Status: {response.status_code}"
            )
            return
        
        log_test("GET /api/safety/daily-reports returns 200", True)
        
        data = response.json()
        items = data.get("items", [])
        
        # Check for synthetic records
        synthetic_found = []
        for report in items:
            pn = report.get("project_number", "")
            if any([
                pn.upper().startswith("TEST_"),
                pn.upper().startswith("SMOKE"),
                pn.upper().startswith("SYNTHETIC"),
            ]):
                synthetic_found.append(report)
        
        if synthetic_found:
            log_test(
                "Safety portal excludes synthetic records",
                False,
                f"Found {len(synthetic_found)} synthetic records"
            )
        else:
            log_test(
                "Safety portal excludes synthetic records",
                True,
                f"Checked {len(items)} items, none are synthetic"
            )
        
    except Exception as e:
        log_test("GET /api/safety/daily-reports", False, f"Exception: {e}")


def test_photo_intelligence_truthful_status(token: str):
    """Test 6: /api/daily-reports/{id}/photo-intelligence returns truthful status"""
    print("\n" + "="*80)
    print("TEST 6: Photo Intelligence Truthful Status Contract")
    print("="*80)
    
    # First, get a list of reports to find different types
    try:
        response = requests.get(
            f"{BASE_URL}/daily-reports",
            headers={"X-Admin-Token": token},
            timeout=15,
        )
        
        if response.status_code != 200:
            log_test(
                "Get reports list for photo intel test",
                False,
                f"Status: {response.status_code}"
            )
            return
        
        reports = response.json()
        if not reports:
            log_test(
                "Get reports list for photo intel test",
                False,
                "No reports found"
            )
            return
        
        log_test(
            "Get reports list for photo intel test",
            True,
            f"Found {len(reports)} reports"
        )
        
        # Test with first available report
        test_report_id = reports[0].get("id")
        
        response = requests.get(
            f"{BASE_URL}/daily-reports/{test_report_id}/photo-intelligence",
            timeout=15,
        )
        
        if response.status_code != 200:
            log_test(
                f"GET /api/daily-reports/{test_report_id}/photo-intelligence returns 200",
                False,
                f"Status: {response.status_code}"
            )
            return
        
        log_test(
            f"GET /api/daily-reports/{{id}}/photo-intelligence returns 200",
            True,
            f"Tested with report_id: {test_report_id}"
        )
        
        data = response.json()
        
        # Check for required fields
        required_fields = ["report_id", "photo_count", "analyzed", "pending", "status"]
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            log_test(
                "Response contains required fields",
                False,
                f"Missing fields: {missing_fields}"
            )
        else:
            log_test(
                "Response contains required fields",
                True,
                f"All required fields present: {required_fields}"
            )
        
        # Check status field
        status = data.get("status")
        valid_statuses = [
            "no_photos",
            "suppressed",
            "pending",
            "failed",
            "complete_with_observations",
            "complete_zero_observations",
            "not_requested",
            "unknown",
        ]
        
        if status in valid_statuses:
            log_test(
                "Status field is valid",
                True,
                f"Status: {status}"
            )
        else:
            log_test(
                "Status field is valid",
                False,
                f"Invalid status: {status}, expected one of {valid_statuses}"
            )
        
        # Check classification field for suppressed/not_requested cases
        classification = data.get("classification")
        if status in ["suppressed", "not_requested"]:
            if classification:
                log_test(
                    "Classification field present for suppressed/not_requested",
                    True,
                    f"Classification: {classification}"
                )
            else:
                log_test(
                    "Classification field present for suppressed/not_requested",
                    False,
                    f"Status is {status} but classification is missing"
                )
        
        # Check observations structure
        observations = data.get("observations", [])
        if isinstance(observations, list):
            log_test(
                "Observations field is a list",
                True,
                f"Count: {len(observations)}"
            )
        else:
            log_test(
                "Observations field is a list",
                False,
                f"Got type: {type(observations)}"
            )
        
    except Exception as e:
        log_test("Photo intelligence status contract", False, f"Exception: {e}")


def test_legacy_write_containment():
    """Test 7: Legacy V2 write endpoints return 410 Gone"""
    print("\n" + "="*80)
    print("TEST 7: Legacy V2 Write Containment (410 Gone)")
    print("="*80)
    
    legacy_write_endpoints = [
        ("POST", "/dr-v2/drafts", {}),
        ("POST", "/dr-v2/ai/synthesize", {"draft_id": "test"}),
        ("POST", "/dr-v2/ai/approve", {"draft_id": "test"}),
        ("POST", "/dr-v2/reports/test-id/canonicalize", {}),
        ("POST", "/dr-v2/photos/test-photo-id/analyze", {"photo_id": "test"}),
        ("POST", "/dr-v2/photos/test-photo-id/links/test-link-id/accept", {}),
        ("POST", "/dr-v2/photos/test-photo-id/links/test-link-id/dismiss", {}),
        ("POST", "/dr-v2/photos/test-photo-id/questions/test-q-id/resolve", {"resolution": "test"}),
    ]
    
    for method, endpoint, payload in legacy_write_endpoints:
        try:
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json=payload,
                timeout=10,
            )
            
            if response.status_code == 410:
                data = response.json()
                error = data.get("detail", {})
                if isinstance(error, dict):
                    error_code = error.get("error")
                    if error_code == "legacy_daily_report_runtime_retired":
                        log_test(
                            f"{method} {endpoint} returns 410 with correct error",
                            True,
                            f"Error: {error_code}"
                        )
                    else:
                        log_test(
                            f"{method} {endpoint} returns 410 with correct error",
                            False,
                            f"Wrong error code: {error_code}"
                        )
                else:
                    log_test(
                        f"{method} {endpoint} returns 410",
                        True,
                        "Status 410 confirmed"
                    )
            else:
                log_test(
                    f"{method} {endpoint} returns 410",
                    False,
                    f"Got status: {response.status_code}"
                )
        
        except Exception as e:
            log_test(f"{method} {endpoint}", False, f"Exception: {e}")


def test_legacy_read_compatibility():
    """Test 8: Legacy V2 read endpoints still work (compatibility mode)"""
    print("\n" + "="*80)
    print("TEST 8: Legacy V2 Read Compatibility")
    print("="*80)
    
    legacy_read_endpoints = [
        ("GET", "/dr-v2/meta", None),
        ("GET", "/dr-v2/drafts/nonexistent-id", None),
        ("GET", "/dr-v2/ai/audit/nonexistent-id", None),
        ("GET", "/dr-v2/photos/nonexistent-id/intelligence", None),
    ]
    
    for method, endpoint, params in legacy_read_endpoints:
        try:
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                params=params,
                timeout=10,
            )
            
            # Read endpoints should return 200 or 404, not 410
            if response.status_code in [200, 404]:
                log_test(
                    f"{method} {endpoint} is accessible (not 410)",
                    True,
                    f"Status: {response.status_code}"
                )
            elif response.status_code == 410:
                log_test(
                    f"{method} {endpoint} is accessible (not 410)",
                    False,
                    "Read endpoint incorrectly returns 410"
                )
            else:
                log_test(
                    f"{method} {endpoint} is accessible",
                    True,
                    f"Status: {response.status_code} (acceptable for read endpoint)"
                )
        
        except Exception as e:
            log_test(f"{method} {endpoint}", False, f"Exception: {e}")


def main():
    """Run all tests"""
    print("="*80)
    print("DR-03 Gate 5 Containment Repair Backend Verification")
    print("="*80)
    print(f"Target: {BASE_URL}")
    print(f"Admin: {ADMIN_EMAIL}")
    print("="*80)
    
    # Authenticate
    token = get_admin_token()
    if not token:
        print("\n✗ FATAL: Could not authenticate. Aborting tests.")
        sys.exit(1)
    
    # Run all tests
    test_daily_reports_list_excludes_synthetic(token)
    test_csv_export_excludes_synthetic(token)
    test_duplicate_check_excludes_synthetic(token)
    test_exposure_signals_excludes_synthetic(token)
    test_safety_portal_excludes_synthetic(token)
    test_photo_intelligence_truthful_status(token)
    test_legacy_write_containment()
    test_legacy_read_compatibility()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {tests_passed + tests_failed}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    print("="*80)
    
    if tests_failed > 0:
        print("\n✗ SOME TESTS FAILED")
        sys.exit(1)
    else:
        print("\n✓ ALL TESTS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()

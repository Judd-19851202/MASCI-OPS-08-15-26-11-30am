#!/usr/bin/env python3
"""
PRE-C10 Cross-Entity Green-State Milestone Backend Verification
Backend-only verification via curl/API checks
"""

import json
import sys
import requests
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://masci-audit-hub.preview.emergentagent.com"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test results tracking
test_results = []


def log_test(name: str, passed: bool, details: str = "", data: Any = None):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{status}: {name}")
    if details:
        print(f"  Details: {details}")
    if data and not passed:
        print(f"  Data: {json.dumps(data, indent=2)[:500]}")
    test_results.append({
        "name": name,
        "passed": passed,
        "details": details,
        "data": data
    })


def test_auth_continuity() -> Optional[Dict[str, str]]:
    """Test 1: Auth continuity smoke - POST /api/auth/multi-login"""
    print("\n" + "="*80)
    print("TEST 1: Auth Continuity Smoke")
    print("="*80)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            },
            timeout=30
        )
        
        if response.status_code != 200:
            log_test(
                "POST /api/auth/multi-login",
                False,
                f"Expected 200, got {response.status_code}",
                response.text[:500]
            )
            return None
        
        data = response.json()
        
        # Verify session_token exists
        if "session_token" not in data:
            log_test(
                "POST /api/auth/multi-login - session_token",
                False,
                "session_token not found in response",
                data
            )
            return None
        
        # Verify portal_tokens.admin exists
        if "portal_tokens" not in data or "admin" not in data.get("portal_tokens", {}):
            log_test(
                "POST /api/auth/multi-login - portal_tokens.admin",
                False,
                "portal_tokens.admin not found in response",
                data
            )
            return None
        
        log_test(
            "POST /api/auth/multi-login",
            True,
            "Admin authentication successful, tokens returned"
        )
        
        # Return headers for subsequent requests
        return {
            "X-Admin-Token": data["portal_tokens"]["admin"]
        }
        
    except Exception as e:
        log_test(
            "POST /api/auth/multi-login",
            False,
            f"Exception: {str(e)}"
        )
        return None


def test_cross_entity_gate(headers: Dict[str, str]):
    """Test 2: Cross-entity gate is now green"""
    print("\n" + "="*80)
    print("TEST 2: Cross-Entity Gate Status")
    print("="*80)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/platform-truth-integrity/cross-entity",
            headers=headers,
            timeout=60
        )
        
        if response.status_code != 200:
            log_test(
                "GET /api/admin/platform-truth-integrity/cross-entity - Status Code",
                False,
                f"Expected 200, got {response.status_code}",
                response.text[:500]
            )
            return
        
        log_test(
            "GET /api/admin/platform-truth-integrity/cross-entity - Status Code",
            True,
            "200 OK"
        )
        
        data = response.json()
        
        # Verify overall_status = green
        overall_status = data.get("overall_status")
        log_test(
            "Cross-entity overall_status = green",
            overall_status == "green",
            f"overall_status = {overall_status}"
        )
        
        # Verify release_gate_blocked = false
        release_gate_blocked = data.get("release_gate_blocked")
        log_test(
            "Cross-entity release_gate_blocked = false",
            release_gate_blocked == False,
            f"release_gate_blocked = {release_gate_blocked}"
        )
        
        # Verify blocking_findings is empty
        blocking_findings = data.get("blocking_findings", [])
        log_test(
            "Cross-entity blocking_findings is empty",
            len(blocking_findings) == 0,
            f"blocking_findings count = {len(blocking_findings)}",
            blocking_findings if len(blocking_findings) > 0 else None
        )
        
        # Verify all required checks are green
        checks = data.get("checks", [])
        required_checks = [
            "project_team_assignment_authority",
            "meeting_attendee_identity_normalization",
            "incident_project_and_submitter_lineage",
            "daily_report_project_and_submitter_lineage",
            "equipment_preop_asset_and_operator_lineage",
            "dispatch_driver_truck_project_linkage",
            "transport_employee_projection_authority"
        ]
        
        checks_by_id = {check.get("id"): check for check in checks}
        
        for check_id in required_checks:
            check = checks_by_id.get(check_id)
            if not check:
                log_test(
                    f"Cross-entity check: {check_id}",
                    False,
                    f"Check not found in response"
                )
                continue
            
            status = check.get("status")
            log_test(
                f"Cross-entity check: {check_id}",
                status == "green",
                f"status = {status}, summary = {check.get('summary', '')[:100]}"
            )
        
    except Exception as e:
        log_test(
            "GET /api/admin/platform-truth-integrity/cross-entity",
            False,
            f"Exception: {str(e)}"
        )


def test_exception_state_surfaces(headers: Dict[str, str]):
    """Test 3: Exception state surfaces"""
    print("\n" + "="*80)
    print("TEST 3: Exception State Surfaces")
    print("="*80)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/platform-truth-integrity/cross-entity/exceptions",
            headers=headers,
            timeout=60
        )
        
        if response.status_code != 200:
            log_test(
                "GET /api/admin/platform-truth-integrity/cross-entity/exceptions - Status Code",
                False,
                f"Expected 200, got {response.status_code}",
                response.text[:500]
            )
            return
        
        log_test(
            "GET /api/admin/platform-truth-integrity/cross-entity/exceptions - Status Code",
            True,
            "200 OK"
        )
        
        data = response.json()
        
        # Verify count > 0
        count = data.get("count", 0)
        log_test(
            "Exception count > 0",
            count > 0,
            f"count = {count}"
        )
        
        # Verify rows include non-blocking statuses
        rows = data.get("rows", [])
        if len(rows) > 0:
            non_blocking_statuses = ["accepted_historical_gap", "excluded_non_operational"]
            has_non_blocking = any(
                row.get("status") in non_blocking_statuses or not row.get("blocks_gate")
                for row in rows
            )
            
            # Sample some exception statuses
            sample_statuses = list(set(row.get("status") for row in rows[:20]))
            sample_blocks_gate = [row.get("blocks_gate") for row in rows[:5]]
            
            log_test(
                "Exception rows include non-blocking statuses",
                has_non_blocking,
                f"Sample statuses: {sample_statuses}, Sample blocks_gate: {sample_blocks_gate}"
            )
        else:
            log_test(
                "Exception rows include non-blocking statuses",
                False,
                "No rows returned"
            )
        
    except Exception as e:
        log_test(
            "GET /api/admin/platform-truth-integrity/cross-entity/exceptions",
            False,
            f"Exception: {str(e)}"
        )


def test_exception_csv_export(headers: Dict[str, str]):
    """Test 4: Exception CSV export"""
    print("\n" + "="*80)
    print("TEST 4: Exception CSV Export")
    print("="*80)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/platform-truth-integrity/cross-entity/exceptions/export.csv",
            headers=headers,
            timeout=60
        )
        
        if response.status_code != 200:
            log_test(
                "GET /api/admin/platform-truth-integrity/cross-entity/exceptions/export.csv - Status Code",
                False,
                f"Expected 200, got {response.status_code}",
                response.text[:500]
            )
            return
        
        log_test(
            "GET /api/admin/platform-truth-integrity/cross-entity/exceptions/export.csv - Status Code",
            True,
            "200 OK"
        )
        
        # Verify content type
        content_type = response.headers.get("Content-Type", "")
        log_test(
            "CSV export Content-Type",
            "text/csv" in content_type,
            f"Content-Type = {content_type}"
        )
        
        # Verify CSV content has header
        csv_content = response.text
        lines = csv_content.split("\n")
        
        if len(lines) > 0:
            header = lines[0]
            expected_columns = ["family", "source_collection", "source_record_id", "status", "blocks_gate"]
            has_expected_columns = all(col in header for col in expected_columns)
            
            log_test(
                "CSV export has expected header columns",
                has_expected_columns,
                f"Header: {header[:200]}"
            )
            
            log_test(
                "CSV export has data rows",
                len(lines) > 1,
                f"Total lines: {len(lines)}"
            )
        else:
            log_test(
                "CSV export has content",
                False,
                "Empty CSV response"
            )
        
    except Exception as e:
        log_test(
            "GET /api/admin/platform-truth-integrity/cross-entity/exceptions/export.csv",
            False,
            f"Exception: {str(e)}"
        )


def test_aggregate_truth_endpoint(headers: Dict[str, str]):
    """Test 5: Aggregate truth endpoint"""
    print("\n" + "="*80)
    print("TEST 5: Aggregate Truth Endpoint")
    print("="*80)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/platform-truth-integrity",
            headers=headers,
            timeout=120
        )
        
        if response.status_code != 200:
            log_test(
                "GET /api/admin/platform-truth-integrity - Status Code",
                False,
                f"Expected 200, got {response.status_code}",
                response.text[:500]
            )
            return
        
        log_test(
            "GET /api/admin/platform-truth-integrity - Status Code",
            True,
            "200 OK"
        )
        
        data = response.json()
        
        # Verify cross_entity.overall_status = green
        cross_entity_status = data.get("cross_entity", {}).get("overall_status")
        log_test(
            "Aggregate: cross_entity.overall_status = green",
            cross_entity_status == "green",
            f"cross_entity.overall_status = {cross_entity_status}"
        )
        
        # Verify top-level release_gate_blocked = false
        release_gate_blocked = data.get("release_gate_blocked")
        log_test(
            "Aggregate: release_gate_blocked = false",
            release_gate_blocked == False,
            f"release_gate_blocked = {release_gate_blocked}"
        )
        
        # Verify contamination and stale_derived_state are present
        has_contamination = "contamination" in data
        has_stale_derived_state = "stale_derived_state" in data
        
        log_test(
            "Aggregate: contamination section present",
            has_contamination,
            f"contamination present = {has_contamination}"
        )
        
        log_test(
            "Aggregate: stale_derived_state section present",
            has_stale_derived_state,
            f"stale_derived_state present = {has_stale_derived_state}"
        )
        
    except Exception as e:
        log_test(
            "GET /api/admin/platform-truth-integrity",
            False,
            f"Exception: {str(e)}"
        )


def test_history_regression_smoke(headers: Dict[str, str]):
    """Test 6: History regression smoke"""
    print("\n" + "="*80)
    print("TEST 6: History Regression Smoke")
    print("="*80)
    
    # First, get sample employee and equipment IDs from canonical collections
    try:
        # Get a sample employee ID - try /api/employees endpoint
        employee_response = requests.get(
            f"{BASE_URL}/api/employees",
            headers=headers,
            timeout=30
        )
        
        employee_id = None
        if employee_response.status_code == 200:
            employees = employee_response.json()
            if isinstance(employees, list) and len(employees) > 0:
                employee_id = employees[0].get("id")
            elif isinstance(employees, dict):
                if "employees" in employees:
                    emp_list = employees.get("employees", [])
                    if len(emp_list) > 0:
                        employee_id = emp_list[0].get("id")
                elif "rows" in employees:
                    emp_list = employees.get("rows", [])
                    if len(emp_list) > 0:
                        employee_id = emp_list[0].get("id")
                # Try direct list access
                elif len(employees) > 0 and isinstance(list(employees.values())[0], list):
                    first_list = list(employees.values())[0]
                    if len(first_list) > 0:
                        employee_id = first_list[0].get("id")
        
        if not employee_id:
            log_test(
                "Get sample employee ID",
                False,
                "Could not retrieve sample employee ID"
            )
        else:
            log_test(
                "Get sample employee ID",
                True,
                f"employee_id = {employee_id}"
            )
            
            # Test employee history endpoint
            emp_history_response = requests.get(
                f"{BASE_URL}/api/master-lookup/employees/{employee_id}/history",
                headers=headers,
                timeout=30
            )
            
            log_test(
                f"GET /api/master-lookup/employees/{employee_id}/history",
                emp_history_response.status_code == 200,
                f"Status: {emp_history_response.status_code}"
            )
            
            if emp_history_response.status_code == 200:
                emp_data = emp_history_response.json()
                # Verify no serialization issues
                has_master = "master" in emp_data
                has_events = "events" in emp_data
                log_test(
                    "Employee history response structure",
                    has_master and has_events,
                    f"Has master: {has_master}, Has events: {has_events}"
                )
        
    except Exception as e:
        log_test(
            "Employee history regression smoke",
            False,
            f"Exception: {str(e)}"
        )
    
    # Get a sample equipment ID
    try:
        # Try to get equipment from equipment_master - use /api/equipment-master endpoint
        equipment_response = requests.get(
            f"{BASE_URL}/api/equipment-master",
            headers=headers,
            timeout=30
        )
        
        equipment_id = None
        if equipment_response.status_code == 200:
            try:
                equipment_data = equipment_response.json()
                if isinstance(equipment_data, list) and len(equipment_data) > 0:
                    equipment_id = equipment_data[0].get("id")
                elif isinstance(equipment_data, dict):
                    if "equipment" in equipment_data:
                        eq_list = equipment_data.get("equipment", [])
                        if len(eq_list) > 0 and isinstance(eq_list[0], dict):
                            equipment_id = eq_list[0].get("id")
                    elif "rows" in equipment_data:
                        eq_list = equipment_data.get("rows", [])
                        if len(eq_list) > 0 and isinstance(eq_list[0], dict):
                            equipment_id = eq_list[0].get("id")
                    # Try direct list access
                    else:
                        for key, value in equipment_data.items():
                            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                                equipment_id = value[0].get("id")
                                break
            except (json.JSONDecodeError, AttributeError, TypeError) as parse_error:
                log_test(
                    "Parse equipment response",
                    False,
                    f"Failed to parse equipment response: {str(parse_error)}"
                )
        
        if not equipment_id:
            log_test(
                "Get sample equipment ID",
                False,
                "Could not retrieve sample equipment ID - may not be critical if no equipment exists"
            )
        else:
            log_test(
                "Get sample equipment ID",
                True,
                f"equipment_id = {equipment_id}"
            )
            
            # Test equipment history endpoint
            eq_history_response = requests.get(
                f"{BASE_URL}/api/master-lookup/equipment/{equipment_id}/history",
                headers=headers,
                timeout=30
            )
            
            log_test(
                f"GET /api/master-lookup/equipment/{equipment_id}/history",
                eq_history_response.status_code == 200,
                f"Status: {eq_history_response.status_code}"
            )
            
            if eq_history_response.status_code == 200:
                eq_data = eq_history_response.json()
                # Verify no serialization issues
                has_master = "master" in eq_data
                has_events = "events" in eq_data
                log_test(
                    "Equipment history response structure",
                    has_master and has_events,
                    f"Has master: {has_master}, Has events: {has_events}"
                )
        
    except Exception as e:
        log_test(
            "Equipment history regression smoke",
            False,
            f"Exception: {str(e)}"
        )


def print_summary():
    """Print test summary"""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total = len(test_results)
    passed = sum(1 for r in test_results if r["passed"])
    failed = total - passed
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed} ({100*passed//total if total > 0 else 0}%)")
    print(f"Failed: {failed} ({100*failed//total if total > 0 else 0}%)")
    
    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for result in test_results:
            if not result["passed"]:
                print(f"  - {result['name']}")
                if result["details"]:
                    print(f"    {result['details']}")
    
    return failed == 0


def main():
    """Main test execution"""
    print("="*80)
    print("PRE-C10 Cross-Entity Green-State Milestone Backend Verification")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Admin Email: {ADMIN_EMAIL}")
    
    # Test 1: Auth
    headers = test_auth_continuity()
    if not headers:
        print("\n❌ CRITICAL: Authentication failed. Cannot proceed with remaining tests.")
        print_summary()
        sys.exit(1)
    
    # Test 2: Cross-entity gate
    test_cross_entity_gate(headers)
    
    # Test 3: Exception state surfaces
    test_exception_state_surfaces(headers)
    
    # Test 4: Exception CSV export
    test_exception_csv_export(headers)
    
    # Test 5: Aggregate truth endpoint
    test_aggregate_truth_endpoint(headers)
    
    # Test 6: History regression smoke
    test_history_regression_smoke(headers)
    
    # Print summary
    all_passed = print_summary()
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()

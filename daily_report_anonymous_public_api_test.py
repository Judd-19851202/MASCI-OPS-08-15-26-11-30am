#!/usr/bin/env python3
"""
Daily Report Anonymous Public API Contract Test

Tests the backend/public API contract supporting the public anonymous Daily Report workflow.
Base URL: https://masci-audit-hub.preview.emergentagent.com/api

Test Coverage:
1. GET /hr/employee-roster/public - Returns active employee items for public dropdown use
2. GET /suppliers - Returns supplier/vendor items for public dropdown use
3. GET /equipment-master - Returns equipment items/categories for public dropdown use
4. POST /daily-reports/photo-intelligence/draft - Accepts anonymous draft payload
5. POST /daily-reports/summary/draft - Accepts anonymous draft payload and returns job
6. GET /jobs/{job_id}/status - Works for anonymous summary job id

IMPORTANT: Daily Report is a 100% public field workflow. NO auth headers or credentials used.
"""

import requests
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List

BASE_URL = "https://masci-audit-hub.preview.emergentagent.com/api"

# Test results storage
test_results = {
    "test_run_timestamp": datetime.now(timezone.utc).isoformat(),
    "base_url": BASE_URL,
    "tests": []
}


def log_test(test_name: str, passed: bool, details: Dict[str, Any]):
    """Log test result"""
    result = {
        "test_name": test_name,
        "passed": passed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details
    }
    test_results["tests"].append(result)
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{status}: {test_name}")
    if not passed:
        print(f"  Details: {json.dumps(details, indent=2)}")
    return passed


def test_employee_roster_public():
    """Test 1: GET /hr/employee-roster/public returns active employee items"""
    test_name = "GET /hr/employee-roster/public - Public Employee Roster"
    
    try:
        # NO auth headers - this is a public endpoint
        response = requests.get(f"{BASE_URL}/hr/employee-roster/public", timeout=10)
        
        details = {
            "status_code": response.status_code,
            "response_size": len(response.text)
        }
        
        if response.status_code != 200:
            details["error"] = f"Expected 200, got {response.status_code}"
            details["response_text"] = response.text[:500]
            return log_test(test_name, False, details)
        
        data = response.json()
        details["has_items"] = "items" in data
        details["has_count"] = "count" in data
        details["has_public_flag"] = "public" in data
        
        if "items" not in data:
            details["error"] = "Response missing 'items' key"
            details["response_keys"] = list(data.keys())
            return log_test(test_name, False, details)
        
        items = data.get("items", [])
        details["item_count"] = len(items)
        
        if len(items) > 0:
            details["sample_item"] = {
                "has_name": "name" in items[0] if items else False,
                "has_role": "role" in items[0] if items else False,
                "keys": list(items[0].keys()) if items else []
            }
        
        # Success criteria: 200 status, has items array
        passed = response.status_code == 200 and "items" in data
        return log_test(test_name, passed, details)
        
    except Exception as e:
        details = {"error": str(e), "error_type": type(e).__name__}
        return log_test(test_name, False, details)


def test_suppliers_public():
    """Test 2: GET /suppliers returns supplier/vendor items"""
    test_name = "GET /suppliers - Public Supplier/Vendor List"
    
    try:
        # NO auth headers - this is a public endpoint
        response = requests.get(f"{BASE_URL}/suppliers", timeout=10)
        
        details = {
            "status_code": response.status_code,
            "response_size": len(response.text)
        }
        
        if response.status_code != 200:
            details["error"] = f"Expected 200, got {response.status_code}"
            details["response_text"] = response.text[:500]
            return log_test(test_name, False, details)
        
        data = response.json()
        details["has_items"] = "items" in data
        
        if "items" not in data:
            details["error"] = "Response missing 'items' key"
            details["response_keys"] = list(data.keys())
            return log_test(test_name, False, details)
        
        items = data.get("items", [])
        details["item_count"] = len(items)
        
        if len(items) > 0:
            details["sample_item"] = {
                "has_name": "name" in items[0] if items else False,
                "keys": list(items[0].keys()) if items else []
            }
        
        # Success criteria: 200 status, has items array
        passed = response.status_code == 200 and "items" in data
        return log_test(test_name, passed, details)
        
    except Exception as e:
        details = {"error": str(e), "error_type": type(e).__name__}
        return log_test(test_name, False, details)


def test_equipment_master_public():
    """Test 3: GET /equipment-master returns equipment items/categories"""
    test_name = "GET /equipment-master - Public Equipment Master"
    
    try:
        # NO auth headers - this is a public endpoint
        response = requests.get(f"{BASE_URL}/equipment-master", timeout=10)
        
        details = {
            "status_code": response.status_code,
            "response_size": len(response.text)
        }
        
        if response.status_code != 200:
            details["error"] = f"Expected 200, got {response.status_code}"
            details["response_text"] = response.text[:500]
            return log_test(test_name, False, details)
        
        data = response.json()
        details["has_items"] = "items" in data
        details["has_categories"] = "categories" in data
        details["has_grouped"] = "grouped" in data
        
        if "items" not in data:
            details["error"] = "Response missing 'items' key"
            details["response_keys"] = list(data.keys())
            return log_test(test_name, False, details)
        
        items = data.get("items", [])
        details["item_count"] = len(items)
        
        if len(items) > 0:
            details["sample_item"] = {
                "keys": list(items[0].keys()) if items else []
            }
        
        # Success criteria: 200 status, has items array
        passed = response.status_code == 200 and "items" in data
        return log_test(test_name, passed, details)
        
    except Exception as e:
        details = {"error": str(e), "error_type": type(e).__name__}
        return log_test(test_name, False, details)


def test_photo_intelligence_draft():
    """Test 4: POST /daily-reports/photo-intelligence/draft accepts anonymous draft"""
    test_name = "POST /daily-reports/photo-intelligence/draft - Anonymous Photo Intelligence Draft"
    
    try:
        # Create realistic minimal draft payload
        draft_payload = {
            "form_key": f"anon-test-{int(time.time())}",
            "payload": {
                "project_number": "TEST-2026-001",
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "location": "Highway 101 North, Station 125+50",
                "prepared_by": "Michael Rodriguez - Field Supervisor",
                "crew": [
                    {
                        "name": "James Wilson",
                        "role": "Equipment Operator",
                        "hours": 8.0
                    }
                ],
                "photos": [
                    "photo://test-photo-1.jpg",
                    "photo://test-photo-2.jpg"
                ]
            }
        }
        
        # NO auth headers - this is a public endpoint
        response = requests.post(
            f"{BASE_URL}/daily-reports/photo-intelligence/draft",
            json=draft_payload,
            timeout=15
        )
        
        details = {
            "status_code": response.status_code,
            "response_size": len(response.text)
        }
        
        # Accept 200, 201, or 202 as success
        if response.status_code not in [200, 201, 202]:
            details["error"] = f"Expected 200/201/202, got {response.status_code}"
            details["response_text"] = response.text[:500]
            return log_test(test_name, False, details)
        
        data = response.json()
        details["response_keys"] = list(data.keys())
        
        # Check for non-crashing, truthful status
        # The endpoint should return some kind of status/result
        details["has_ok_field"] = "ok" in data
        details["has_status_field"] = "status" in data
        details["has_photos_field"] = "photos" in data
        
        # Success criteria: Non-500 status, returns JSON response
        passed = response.status_code in [200, 201, 202] and isinstance(data, dict)
        return log_test(test_name, passed, details)
        
    except Exception as e:
        details = {"error": str(e), "error_type": type(e).__name__}
        return log_test(test_name, False, details)


def test_summary_draft_and_job_status():
    """Test 5 & 6: POST /daily-reports/summary/draft and GET /jobs/{job_id}/status"""
    test_name = "POST /daily-reports/summary/draft + GET /jobs/{job_id}/status - Anonymous Summary Draft"
    
    try:
        # Create realistic minimal draft payload
        draft_payload = {
            "form_key": f"anon-test-{int(time.time())}",
            "language": "en",
            "payload": {
                "project_number": "TEST-2026-001",
                "project_name": "Highway 101 Widening Project",
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "location": "Highway 101 North, Station 125+50",
                "prepared_by": "Michael Rodriguez - Field Supervisor",
                "crew": [
                    {
                        "name": "James Wilson",
                        "role": "Equipment Operator",
                        "hours": 8.0
                    },
                    {
                        "name": "Sarah Chen",
                        "role": "General Laborer",
                        "hours": 8.0
                    }
                ],
                "activities": [
                    {
                        "description": "Excavation and grading work",
                        "quantity": 150,
                        "unit": "cubic yards"
                    }
                ],
                "work_performed": "Completed excavation and grading operations for roadway widening. Crew worked efficiently throughout the day with no delays."
            }
        }
        
        # NO auth headers - this is a public endpoint
        response = requests.post(
            f"{BASE_URL}/daily-reports/summary/draft",
            json=draft_payload,
            timeout=15
        )
        
        details = {
            "summary_draft_status_code": response.status_code,
            "summary_draft_response_size": len(response.text)
        }
        
        # Expect 202 (async job) or 200 (immediate response)
        if response.status_code not in [200, 202]:
            details["error"] = f"Expected 200/202, got {response.status_code}"
            details["response_text"] = response.text[:500]
            return log_test(test_name, False, details)
        
        data = response.json()
        details["summary_draft_response_keys"] = list(data.keys())
        
        # Check if it returns a job_id (async) or completed summary (sync)
        has_job_id = "job_id" in data
        has_summary_text = "summary_text" in data
        
        details["has_job_id"] = has_job_id
        details["has_summary_text"] = has_summary_text
        
        if not has_job_id and not has_summary_text:
            details["error"] = "Response has neither job_id nor summary_text"
            return log_test(test_name, False, details)
        
        # If we got a job_id, test the job status endpoint
        if has_job_id:
            job_id = data["job_id"]
            details["job_id"] = job_id
            
            # Test GET /jobs/{job_id}/status
            # Poll up to 5 times with 3 second intervals (max 15 seconds)
            max_polls = 5
            poll_interval = 3
            
            for poll_attempt in range(max_polls):
                time.sleep(poll_interval)
                
                # NO auth headers - this is a public endpoint
                job_response = requests.get(
                    f"{BASE_URL}/jobs/{job_id}/status",
                    timeout=10
                )
                
                details[f"job_status_poll_{poll_attempt + 1}_status_code"] = job_response.status_code
                
                if job_response.status_code != 200:
                    details[f"job_status_poll_{poll_attempt + 1}_error"] = f"Expected 200, got {job_response.status_code}"
                    continue
                
                job_data = job_response.json()
                details[f"job_status_poll_{poll_attempt + 1}_status"] = job_data.get("status")
                details[f"job_status_poll_{poll_attempt + 1}_keys"] = list(job_data.keys())
                
                # Check if job reached terminal state
                job_status = job_data.get("status")
                if job_status in ["completed", "failed", "error"]:
                    details["job_final_status"] = job_status
                    details["job_polls_needed"] = poll_attempt + 1
                    
                    if job_status == "completed":
                        details["job_has_result"] = "result" in job_data
                        if "result" in job_data:
                            result = job_data["result"]
                            if isinstance(result, dict):
                                details["job_result_has_summary_text"] = "summary_text" in result
                                if "summary_text" in result:
                                    details["summary_text_length"] = len(result["summary_text"])
                    break
            else:
                # Didn't reach terminal state
                details["warning"] = f"Job did not reach terminal state after {max_polls} polls"
        
        # Success criteria: 
        # - Returns 200/202 status
        # - Either has job_id or summary_text
        # - If job_id, the job status endpoint returns 200
        passed = (
            response.status_code in [200, 202] and
            (has_job_id or has_summary_text)
        )
        
        if has_job_id:
            # Also check that at least one job status poll succeeded
            job_status_worked = any(
                details.get(f"job_status_poll_{i}_status_code") == 200
                for i in range(1, max_polls + 1)
            )
            passed = passed and job_status_worked
            details["job_status_endpoint_working"] = job_status_worked
        
        return log_test(test_name, passed, details)
        
    except Exception as e:
        details = {"error": str(e), "error_type": type(e).__name__}
        return log_test(test_name, False, details)


def main():
    """Run all tests"""
    print("=" * 80)
    print("Daily Report Anonymous Public API Contract Test")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Test Run: {test_results['test_run_timestamp']}")
    print("=" * 80)
    
    # Run all tests
    results = []
    
    print("\n" + "=" * 80)
    print("TEST 1: Employee Roster Public Endpoint")
    print("=" * 80)
    results.append(test_employee_roster_public())
    
    print("\n" + "=" * 80)
    print("TEST 2: Suppliers Public Endpoint")
    print("=" * 80)
    results.append(test_suppliers_public())
    
    print("\n" + "=" * 80)
    print("TEST 3: Equipment Master Public Endpoint")
    print("=" * 80)
    results.append(test_equipment_master_public())
    
    print("\n" + "=" * 80)
    print("TEST 4: Photo Intelligence Draft Endpoint")
    print("=" * 80)
    results.append(test_photo_intelligence_draft())
    
    print("\n" + "=" * 80)
    print("TEST 5 & 6: Summary Draft + Job Status Endpoints")
    print("=" * 80)
    results.append(test_summary_draft_and_job_status())
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Pass Rate: {(passed_tests / total_tests * 100):.1f}%")
    
    test_results["summary"] = {
        "total_tests": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "pass_rate": f"{(passed_tests / total_tests * 100):.1f}%"
    }
    
    # Save results to file
    output_file = "/app/daily_report_anonymous_public_api_test_results.json"
    with open(output_file, "w") as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    
    if failed_tests > 0:
        print("\n❌ SOME TESTS FAILED - See details above")
        return 1
    else:
        print("\n✅ ALL TESTS PASSED")
        return 0


if __name__ == "__main__":
    exit(main())

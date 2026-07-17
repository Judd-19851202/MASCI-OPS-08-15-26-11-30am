#!/usr/bin/env python3
"""
REL-01 Runtime Reliability Backend Verification
Tests health/readiness endpoints, runtime headers, background tasks, incident forensics
"""

import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple

# Base URL from frontend/.env
BASE_URL = "https://backup-forensics.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Super-admin credentials
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test results tracking
test_results = []
admin_token = None


def log_test(test_name: str, passed: bool, details: str = ""):
    """Log test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    result = {
        "test": test_name,
        "passed": passed,
        "details": details,
        "status": status
    }
    test_results.append(result)
    print(f"{status}: {test_name}")
    if details:
        print(f"  Details: {details}")
    return passed


def test_1_health_endpoint_with_headers():
    """Test 1: GET /api/health returns 200 with runtime headers"""
    print("\n=== Test 1: Health Endpoint with Runtime Headers ===")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        
        # Check status code
        if response.status_code != 200:
            return log_test(
                "GET /api/health status code",
                False,
                f"Expected 200, got {response.status_code}"
            )
        
        log_test("GET /api/health status code", True, "Returns 200")
        
        # Check required headers
        headers = response.headers
        required_headers = [
            "X-MASCI-Liveness",
            "X-MASCI-Readiness",
            "X-MASCI-Full-Health",
            "X-MASCI-Instance"
        ]
        
        missing_headers = []
        present_headers = []
        
        for header in required_headers:
            if header in headers:
                present_headers.append(f"{header}={headers[header]}")
            else:
                missing_headers.append(header)
        
        if missing_headers:
            return log_test(
                "GET /api/health runtime headers",
                False,
                f"Missing headers: {', '.join(missing_headers)}"
            )
        
        return log_test(
            "GET /api/health runtime headers",
            True,
            f"All headers present: {', '.join(present_headers)}"
        )
        
    except Exception as e:
        return log_test("GET /api/health", False, f"Exception: {str(e)}")


def test_2_ready_endpoint():
    """Test 2: GET /api/ready returns 200 with readiness contract"""
    print("\n=== Test 2: Ready Endpoint ===")
    try:
        response = requests.get(f"{API_BASE}/ready", timeout=10)
        
        if response.status_code != 200:
            return log_test(
                "GET /api/ready status code",
                False,
                f"Expected 200, got {response.status_code}"
            )
        
        log_test("GET /api/ready status code", True, "Returns 200")
        
        # Check response body
        data = response.json()
        required_fields = [
            "ok",
            "state",
            "reason",
            "event_loop_ok",
            "mongo_ok",
            "startup_complete"
        ]
        
        missing_fields = []
        present_fields = []
        
        for field in required_fields:
            if field in data:
                present_fields.append(f"{field}={data[field]}")
            else:
                missing_fields.append(field)
        
        if missing_fields:
            return log_test(
                "GET /api/ready response fields",
                False,
                f"Missing fields: {', '.join(missing_fields)}"
            )
        
        return log_test(
            "GET /api/ready response fields",
            True,
            f"All fields present: {', '.join(present_fields)}"
        )
        
    except Exception as e:
        return log_test("GET /api/ready", False, f"Exception: {str(e)}")


def test_3_health_full_endpoint():
    """Test 3: GET /api/health/full returns 200 with legacy boolean contract"""
    print("\n=== Test 3: Health Full Endpoint ===")
    try:
        response = requests.get(f"{API_BASE}/health/full", timeout=10)
        
        if response.status_code != 200:
            return log_test(
                "GET /api/health/full status code",
                False,
                f"Expected 200, got {response.status_code}"
            )
        
        log_test("GET /api/health/full status code", True, "Returns 200")
        
        # Check legacy boolean contract
        data = response.json()
        required_fields = ["ok", "mongo", "scheduler", "backup_recent"]
        
        missing_fields = []
        present_fields = []
        
        for field in required_fields:
            if field in data:
                present_fields.append(f"{field}={data[field]}")
            else:
                missing_fields.append(field)
        
        if missing_fields:
            return log_test(
                "GET /api/health/full legacy contract",
                False,
                f"Missing fields: {', '.join(missing_fields)}"
            )
        
        return log_test(
            "GET /api/health/full legacy contract",
            True,
            f"All fields present: {', '.join(present_fields)}"
        )
        
    except Exception as e:
        return log_test("GET /api/health/full", False, f"Exception: {str(e)}")


def test_4_multi_login():
    """Test 4: POST /api/auth/multi-login returns portal_tokens"""
    print("\n=== Test 4: Multi-Login Authentication ===")
    global admin_token
    
    try:
        payload = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        response = requests.post(
            f"{API_BASE}/auth/multi-login",
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            return log_test(
                "POST /api/auth/multi-login",
                False,
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        data = response.json()
        
        if "portal_tokens" not in data:
            return log_test(
                "POST /api/auth/multi-login",
                False,
                "Response missing portal_tokens field"
            )
        
        portal_tokens = data["portal_tokens"]
        
        if "admin" not in portal_tokens:
            return log_test(
                "POST /api/auth/multi-login",
                False,
                "portal_tokens missing admin token"
            )
        
        admin_token = portal_tokens["admin"]
        
        return log_test(
            "POST /api/auth/multi-login",
            True,
            f"Admin token obtained (length: {len(admin_token)})"
        )
        
    except Exception as e:
        return log_test("POST /api/auth/multi-login", False, f"Exception: {str(e)}")


def test_5_runtime_health_diag():
    """Test 5: GET /api/admin-strict/diag/runtime-health returns layered runtime info"""
    print("\n=== Test 5: Runtime Health Diagnostics ===")
    
    if not admin_token:
        return log_test(
            "GET /api/admin-strict/diag/runtime-health",
            False,
            "No admin token available (auth failed)"
        )
    
    try:
        headers = {"X-Admin-Token": admin_token}
        response = requests.get(
            f"{API_BASE}/admin-strict/diag/runtime-health",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            return log_test(
                "GET /api/admin-strict/diag/runtime-health",
                False,
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        data = response.json()
        
        # Check for layered runtime info and background tasks
        has_runtime_info = any(key in data for key in [
            "liveness", "readiness", "full_health", "event_loop_lag_ms", 
            "mongo_latency_ms", "resources"
        ])
        
        has_background_tasks = "background_tasks" in data
        
        if not has_runtime_info:
            return log_test(
                "GET /api/admin-strict/diag/runtime-health",
                False,
                "Response missing runtime info fields"
            )
        
        # Extract key metrics
        metrics = []
        if "event_loop_lag_ms" in data:
            metrics.append(f"event_loop_lag={data['event_loop_lag_ms']}ms")
        if "mongo_latency_ms" in data:
            metrics.append(f"mongo_latency={data['mongo_latency_ms']}ms")
        if "background_tasks" in data:
            task_count = len(data["background_tasks"]) if isinstance(data["background_tasks"], list) else data["background_tasks"].get("count", 0)
            metrics.append(f"background_tasks={task_count}")
        
        details = f"Runtime info present. {', '.join(metrics)}"
        
        return log_test(
            "GET /api/admin-strict/diag/runtime-health",
            True,
            details
        )
        
    except Exception as e:
        return log_test(
            "GET /api/admin-strict/diag/runtime-health",
            False,
            f"Exception: {str(e)}"
        )


def test_6_incident_forensics():
    """Test 6: GET /api/admin-strict/diag/incident-forensics returns bounded list"""
    print("\n=== Test 6: Incident Forensics ===")
    
    if not admin_token:
        return log_test(
            "GET /api/admin-strict/diag/incident-forensics",
            False,
            "No admin token available (auth failed)"
        )
    
    try:
        headers = {"X-Admin-Token": admin_token}
        response = requests.get(
            f"{API_BASE}/admin-strict/diag/incident-forensics",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            return log_test(
                "GET /api/admin-strict/diag/incident-forensics",
                False,
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        data = response.json()
        
        # Check it's a bounded list (array or dict with incidents/rows)
        is_list = isinstance(data, list)
        is_dict_with_incidents = isinstance(data, dict) and (
            "incidents" in data or "events" in data or "forensics" in data or "rows" in data
        )
        
        if not (is_list or is_dict_with_incidents):
            return log_test(
                "GET /api/admin-strict/diag/incident-forensics",
                False,
                f"Unexpected response structure: {type(data)}"
            )
        
        # Check for secrets leakage (should not contain password, secret, key fields)
        response_text = json.dumps(data).lower()
        has_secrets = any(word in response_text for word in [
            '"password":', '"secret":', '"api_key":', '"private_key":'
        ])
        
        if has_secrets:
            return log_test(
                "GET /api/admin-strict/diag/incident-forensics",
                False,
                "Response may contain secrets (password/secret/key fields found)"
            )
        
        # Get count
        if is_list:
            count = len(data)
        elif "count" in data:
            count = data["count"]
        else:
            count = len(data.get("incidents", data.get("events", data.get("rows", []))))
        
        return log_test(
            "GET /api/admin-strict/diag/incident-forensics",
            True,
            f"Bounded list returned ({count} items), no secrets detected"
        )
        
    except Exception as e:
        return log_test(
            "GET /api/admin-strict/diag/incident-forensics",
            False,
            f"Exception: {str(e)}"
        )


def test_7_persistence_health():
    """Test 7: GET /api/admin-strict/diag/persistence-health returns 200"""
    print("\n=== Test 7: Persistence Health ===")
    
    if not admin_token:
        return log_test(
            "GET /api/admin-strict/diag/persistence-health",
            False,
            "No admin token available (auth failed)"
        )
    
    try:
        headers = {"X-Admin-Token": admin_token}
        response = requests.get(
            f"{API_BASE}/admin-strict/diag/persistence-health",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            return log_test(
                "GET /api/admin-strict/diag/persistence-health",
                False,
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        return log_test(
            "GET /api/admin-strict/diag/persistence-health",
            True,
            "Returns 200"
        )
        
    except Exception as e:
        return log_test(
            "GET /api/admin-strict/diag/persistence-health",
            False,
            f"Exception: {str(e)}"
        )


def test_8_daily_reports_approved():
    """Test 8: GET /api/daily-reports/approved?limit=1 returns 200"""
    print("\n=== Test 8: Daily Reports Approved ===")
    
    if not admin_token:
        return log_test(
            "GET /api/daily-reports/approved",
            False,
            "No admin token available (auth failed)"
        )
    
    try:
        headers = {"X-Admin-Token": admin_token}
        response = requests.get(
            f"{API_BASE}/daily-reports/approved?limit=1",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            return log_test(
                "GET /api/daily-reports/approved",
                False,
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        data = response.json()
        count = len(data) if isinstance(data, list) else data.get("count", 0)
        
        return log_test(
            "GET /api/daily-reports/approved",
            True,
            f"Returns 200 with {count} reports"
        )
        
    except Exception as e:
        return log_test(
            "GET /api/daily-reports/approved",
            False,
            f"Exception: {str(e)}"
        )


def test_9_search_endpoint():
    """Test 9: GET /api/search?q=report&limit=3 returns 200"""
    print("\n=== Test 9: Search Endpoint ===")
    
    if not admin_token:
        return log_test(
            "GET /api/search",
            False,
            "No admin token available (auth failed)"
        )
    
    try:
        headers = {"X-Admin-Token": admin_token}
        response = requests.get(
            f"{API_BASE}/search?q=report&limit=3",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            return log_test(
                "GET /api/search",
                False,
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        data = response.json()
        result_count = len(data) if isinstance(data, list) else len(data.get("results", []))
        
        return log_test(
            "GET /api/search",
            True,
            f"Returns 200 with {result_count} results"
        )
        
    except Exception as e:
        return log_test(
            "GET /api/search",
            False,
            f"Exception: {str(e)}"
        )


def test_10_dispatch_motive_posture():
    """Test 10: GET /api/dispatch/motive-posture returns 200"""
    print("\n=== Test 10: Dispatch Motive Posture ===")
    
    if not admin_token:
        return log_test(
            "GET /api/dispatch/motive-posture",
            False,
            "No admin token available (auth failed)"
        )
    
    try:
        headers = {"X-Admin-Token": admin_token}
        response = requests.get(
            f"{API_BASE}/dispatch/motive-posture",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            return log_test(
                "GET /api/dispatch/motive-posture",
                False,
                f"Expected 200, got {response.status_code}: {response.text[:200]}"
            )
        
        return log_test(
            "GET /api/dispatch/motive-posture",
            True,
            "Returns 200"
        )
        
    except Exception as e:
        return log_test(
            "GET /api/dispatch/motive-posture",
            False,
            f"Exception: {str(e)}"
        )


def test_11_concurrent_burst():
    """Test 11: Concurrent burst across multiple endpoints with no 5xx/timeouts"""
    print("\n=== Test 11: Concurrent Burst Test ===")
    
    if not admin_token:
        return log_test(
            "Concurrent burst test",
            False,
            "No admin token available (auth failed)"
        )
    
    # Endpoints to test concurrently
    endpoints = [
        ("/health", None),
        ("/ready", None),
        ("/daily-reports/approved?limit=1", admin_token),
        ("/search?q=report&limit=3", admin_token),
    ]
    
    # Repeat each endpoint 3 times for burst
    burst_requests = endpoints * 3
    
    results = []
    errors = []
    timeouts = []
    server_errors = []
    
    def make_request(endpoint_tuple):
        endpoint, token = endpoint_tuple
        try:
            headers = {"X-Admin-Token": token} if token else {}
            start = time.time()
            response = requests.get(
                f"{API_BASE}{endpoint}",
                headers=headers,
                timeout=10
            )
            elapsed = time.time() - start
            
            return {
                "endpoint": endpoint,
                "status": response.status_code,
                "elapsed": elapsed,
                "success": 200 <= response.status_code < 300
            }
        except requests.Timeout:
            return {
                "endpoint": endpoint,
                "status": "TIMEOUT",
                "elapsed": 10.0,
                "success": False
            }
        except Exception as e:
            return {
                "endpoint": endpoint,
                "status": "ERROR",
                "error": str(e),
                "success": False
            }
    
    print(f"  Running {len(burst_requests)} concurrent requests...")
    
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(make_request, req) for req in burst_requests]
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            
            if not result["success"]:
                if result["status"] == "TIMEOUT":
                    timeouts.append(result["endpoint"])
                elif result["status"] == "ERROR":
                    errors.append(f"{result['endpoint']}: {result.get('error', 'Unknown')}")
                elif result["status"] >= 500:
                    server_errors.append(f"{result['endpoint']}: {result['status']}")
    
    # Analyze results
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    avg_time = sum(r["elapsed"] for r in results) / total if total > 0 else 0
    
    print(f"  Total requests: {total}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {total - successful}")
    print(f"  Average response time: {avg_time:.2f}s")
    
    if timeouts:
        log_test(
            "Concurrent burst - no timeouts",
            False,
            f"{len(timeouts)} timeouts: {', '.join(set(timeouts))}"
        )
        return False
    
    if server_errors:
        log_test(
            "Concurrent burst - no 5xx errors",
            False,
            f"{len(server_errors)} server errors: {', '.join(set(server_errors))}"
        )
        return False
    
    if errors:
        log_test(
            "Concurrent burst - no errors",
            False,
            f"{len(errors)} errors: {', '.join(errors[:3])}"
        )
        return False
    
    return log_test(
        "Concurrent burst test",
        True,
        f"{total} requests, {successful} successful, avg {avg_time:.2f}s, no 5xx/timeouts"
    )


def main():
    """Run all REL-01 runtime reliability tests"""
    print("=" * 80)
    print("REL-01 RUNTIME RELIABILITY BACKEND VERIFICATION")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Admin: {ADMIN_EMAIL}")
    print("=" * 80)
    
    start_time = time.time()
    
    # Run tests in sequence
    test_1_health_endpoint_with_headers()
    test_2_ready_endpoint()
    test_3_health_full_endpoint()
    test_4_multi_login()
    test_5_runtime_health_diag()
    test_6_incident_forensics()
    test_7_persistence_health()
    test_8_daily_reports_approved()
    test_9_search_endpoint()
    test_10_dispatch_motive_posture()
    test_11_concurrent_burst()
    
    elapsed = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in test_results if r["passed"])
    failed = sum(1 for r in test_results if not r["passed"])
    total = len(test_results)
    
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(passed/total*100):.1f}%")
    print(f"Elapsed time: {elapsed:.2f}s")
    
    if failed > 0:
        print("\nFailed tests:")
        for result in test_results:
            if not result["passed"]:
                print(f"  ✗ {result['test']}")
                if result["details"]:
                    print(f"    {result['details']}")
    
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

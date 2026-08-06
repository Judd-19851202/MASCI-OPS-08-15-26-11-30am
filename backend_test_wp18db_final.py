#!/usr/bin/env python3
"""
WP-18DB Final Confirmation Run - Backend Verification
Verify the 6 specific admin endpoints for WP-18DB preview backend readiness.
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "https://masci-audit-hub.preview.emergentagent.com/api"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
TIMEOUT = 30

# Test results
results = {
    "test_run_timestamp": datetime.utcnow().isoformat() + "Z",
    "tests": [],
    "summary": {
        "total": 6,
        "passed": 0,
        "failed": 0,
        "transport_errors": 0
    }
}

def log_test(name, status, details):
    """Log test result"""
    test_result = {
        "name": name,
        "status": status,
        "details": details,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    results["tests"].append(test_result)
    
    if status == "PASS":
        results["summary"]["passed"] += 1
        print(f"✅ PASS: {name}")
    elif status == "FAIL":
        results["summary"]["failed"] += 1
        print(f"❌ FAIL: {name}")
    elif status == "TRANSPORT_ERROR":
        results["summary"]["transport_errors"] += 1
        print(f"⚠️ TRANSPORT ERROR: {name}")
    
    print(f"   Details: {details}")
    print()

def check_transport_error(response):
    """Check if error is transport-related (502, 503, 504)"""
    if response.status_code in [502, 503, 504]:
        return True, f"Transport error: HTTP {response.status_code}"
    return False, None

# Test 1: Admin Authentication
print("=" * 80)
print("TEST 1: Admin Authentication")
print("=" * 80)
try:
    response = requests.post(
        f"{BASE_URL}/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=TIMEOUT
    )
    
    if response.status_code == 200:
        data = response.json()
        session_token = data.get("session_token")
        admin_token = data["portal_tokens"].get("admin")
        
        if session_token and admin_token:
            log_test(
                "Admin Authentication",
                "PASS",
                f"Successfully authenticated. Session token length: {len(session_token)}, Admin token length: {len(admin_token)}"
            )
            
            # Store tokens for subsequent tests
            auth_headers = {
                "X-Admin-Token": admin_token,
                "X-Directory-Token": session_token
            }
        else:
            log_test(
                "Admin Authentication",
                "FAIL",
                "Missing session_token or admin token in response"
            )
            exit(1)
    else:
        is_transport, msg = check_transport_error(response)
        if is_transport:
            log_test("Admin Authentication", "TRANSPORT_ERROR", msg)
        else:
            log_test(
                "Admin Authentication",
                "FAIL",
                f"HTTP {response.status_code}: {response.text[:200]}"
            )
        exit(1)
except Exception as e:
    log_test("Admin Authentication", "FAIL", f"Exception: {str(e)}")
    exit(1)

# Test 2: /api/admin/recovery/snapshot - should be GREEN
print("=" * 80)
print("TEST 2: Recovery Snapshot - Should be GREEN")
print("=" * 80)
try:
    response = requests.get(
        f"{BASE_URL}/admin/recovery/snapshot",
        headers=auth_headers,
        timeout=TIMEOUT
    )
    
    is_transport, msg = check_transport_error(response)
    if is_transport:
        log_test("Recovery Snapshot", "TRANSPORT_ERROR", msg)
    elif response.status_code == 200:
        data = response.json()
        
        # Check for fresh backup evidence
        last_backup = data.get("last_backup", {})
        backup_age_minutes = data.get("backup_age_minutes", 999999)
        
        # Check backup status
        backup_ok = last_backup.get("ok", False)
        integrity_status = last_backup.get("integrity_status", "UNKNOWN")
        completeness_status = last_backup.get("completeness_status", "UNKNOWN")
        availability_status = last_backup.get("availability_status", "UNKNOWN")
        
        is_green = (
            backup_ok and
            integrity_status == "PASS" and
            completeness_status == "COMPLETE" and
            availability_status == "AVAILABLE" and
            backup_age_minutes < 1440  # Less than 24 hours
        )
        
        if is_green:
            log_test(
                "Recovery Snapshot",
                "PASS",
                f"GREEN - Fresh backup found. Age: {backup_age_minutes:.2f} minutes, "
                f"Integrity: {integrity_status}, Completeness: {completeness_status}, "
                f"Availability: {availability_status}"
            )
        else:
            log_test(
                "Recovery Snapshot",
                "FAIL",
                f"NOT GREEN - Backup age: {backup_age_minutes:.2f} minutes, "
                f"OK: {backup_ok}, Integrity: {integrity_status}, "
                f"Completeness: {completeness_status}, Availability: {availability_status}"
            )
    else:
        log_test(
            "Recovery Snapshot",
            "FAIL",
            f"HTTP {response.status_code}: {response.text[:200]}"
        )
except Exception as e:
    log_test("Recovery Snapshot", "FAIL", f"Exception: {str(e)}")

# Test 3: /api/admin/backup-trust-score - should be green/trusted
print("=" * 80)
print("TEST 3: Backup Trust Score - Should be Green/Trusted")
print("=" * 80)
try:
    response = requests.get(
        f"{BASE_URL}/admin/backup-trust-score",
        headers=auth_headers,
        timeout=TIMEOUT
    )
    
    is_transport, msg = check_transport_error(response)
    if is_transport:
        log_test("Backup Trust Score", "TRANSPORT_ERROR", msg)
    elif response.status_code == 200:
        data = response.json()
        
        trust_score = data.get("trust_score", 0)
        trust_band = data.get("trust_band", "unknown")
        
        # Green threshold is typically >= 80
        is_green = trust_score >= 80
        
        if is_green:
            log_test(
                "Backup Trust Score",
                "PASS",
                f"GREEN - Trust score: {trust_score}, Band: {trust_band}"
            )
        else:
            log_test(
                "Backup Trust Score",
                "FAIL",
                f"NOT GREEN - Trust score: {trust_score}, Band: {trust_band}"
            )
    else:
        log_test(
            "Backup Trust Score",
            "FAIL",
            f"HTTP {response.status_code}: {response.text[:200]}"
        )
except Exception as e:
    log_test("Backup Trust Score", "FAIL", f"Exception: {str(e)}")

# Test 4: /api/admin/deployment-readiness - should return pass
print("=" * 80)
print("TEST 4: Deployment Readiness - Should Return Pass")
print("=" * 80)
try:
    response = requests.get(
        f"{BASE_URL}/admin/deployment-readiness",
        headers=auth_headers,
        timeout=TIMEOUT
    )
    
    is_transport, msg = check_transport_error(response)
    if is_transport:
        log_test("Deployment Readiness", "TRANSPORT_ERROR", msg)
    elif response.status_code == 200:
        data = response.json()
        
        decision = data.get("decision", "").lower()
        blocking_gates = data.get("blocking_gates", [])
        
        is_pass = decision == "pass" and len(blocking_gates) == 0
        
        if is_pass:
            log_test(
                "Deployment Readiness",
                "PASS",
                f"PASS - Decision: {decision}, Blocking gates: {len(blocking_gates)}"
            )
        else:
            log_test(
                "Deployment Readiness",
                "FAIL",
                f"NOT PASS - Decision: {decision}, Blocking gates: {len(blocking_gates)}, Gates: {blocking_gates}"
            )
    else:
        log_test(
            "Deployment Readiness",
            "FAIL",
            f"HTTP {response.status_code}: {response.text[:200]}"
        )
except Exception as e:
    log_test("Deployment Readiness", "FAIL", f"Exception: {str(e)}")

# Test 5: /api/admin/deployment-readiness/performance-budget-contract - should return pass
print("=" * 80)
print("TEST 5: Performance Budget Contract - Should Return Pass")
print("=" * 80)
try:
    response = requests.get(
        f"{BASE_URL}/admin/deployment-readiness/performance-budget-contract",
        headers=auth_headers,
        timeout=TIMEOUT
    )
    
    is_transport, msg = check_transport_error(response)
    if is_transport:
        log_test("Performance Budget Contract", "TRANSPORT_ERROR", msg)
    elif response.status_code == 200:
        data = response.json()
        
        # Check if contract passes
        ok = data.get("ok", False)
        exists = data.get("exists", False)
        failing_rows = data.get("failing_rows", [])
        
        is_pass = ok and exists and len(failing_rows) == 0
        
        if is_pass:
            log_test(
                "Performance Budget Contract",
                "PASS",
                f"PASS - OK: {ok}, Exists: {exists}, Failing rows: {len(failing_rows)}"
            )
        else:
            log_test(
                "Performance Budget Contract",
                "FAIL",
                f"NOT PASS - OK: {ok}, Exists: {exists}, Failing rows: {len(failing_rows)}"
            )
    else:
        log_test(
            "Performance Budget Contract",
            "FAIL",
            f"HTTP {response.status_code}: {response.text[:200]}"
        )
except Exception as e:
    log_test("Performance Budget Contract", "FAIL", f"Exception: {str(e)}")

# Test 6: Release Gate for Preview - Check overall readiness
print("=" * 80)
print("TEST 6: Release Gate for Preview - Overall Readiness")
print("=" * 80)
try:
    # Check /api/ready endpoint for overall system readiness
    response = requests.get(
        f"{BASE_URL}/ready",
        timeout=TIMEOUT
    )
    
    is_transport, msg = check_transport_error(response)
    if is_transport:
        log_test("Release Gate", "TRANSPORT_ERROR", msg)
    elif response.status_code == 200:
        data = response.json()
        
        ok = data.get("ok", False)
        state = data.get("state", "")
        mongo_ok = data.get("mongo_ok", False)
        event_loop_ok = data.get("event_loop_ok", False)
        startup_complete = data.get("startup_complete", False)
        
        is_ready = ok and state == "ready" and mongo_ok and event_loop_ok and startup_complete
        
        if is_ready:
            log_test(
                "Release Gate",
                "PASS",
                f"PASSING - State: {state}, Mongo: {mongo_ok}, Event Loop: {event_loop_ok}, Startup: {startup_complete}"
            )
        else:
            log_test(
                "Release Gate",
                "FAIL",
                f"NOT PASSING - OK: {ok}, State: {state}, Mongo: {mongo_ok}, Event Loop: {event_loop_ok}, Startup: {startup_complete}"
            )
    else:
        log_test(
            "Release Gate",
            "FAIL",
            f"HTTP {response.status_code}: {response.text[:200]}"
        )
except Exception as e:
    log_test("Release Gate", "FAIL", f"Exception: {str(e)}")

# Print final summary
print("=" * 80)
print("FINAL SUMMARY")
print("=" * 80)
print(f"Total Tests: {results['summary']['total']}")
print(f"Passed: {results['summary']['passed']}")
print(f"Failed: {results['summary']['failed']}")
print(f"Transport Errors: {results['summary']['transport_errors']}")
print()

if results['summary']['failed'] == 0 and results['summary']['transport_errors'] == 0:
    print("✅ ALL TESTS PASSED - WP-18DB PREVIEW BACKEND IS READY")
    exit_code = 0
elif results['summary']['transport_errors'] > 0:
    print("⚠️ TRANSPORT ERRORS DETECTED - INGRESS ISSUES, NOT BACKEND FAILURE")
    exit_code = 2
else:
    print("❌ SOME TESTS FAILED - BLOCKING ISSUES FOUND")
    exit_code = 1

# Save results to file
with open("/app/backend_test_wp18db_final_results.json", "w") as f:
    json.dump(results, f, indent=2)

print()
print("Results saved to: /app/backend_test_wp18db_final_results.json")

exit(exit_code)

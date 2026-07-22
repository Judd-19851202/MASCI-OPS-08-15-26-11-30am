#!/usr/bin/env python3
"""
C2 Late Recovery/Identity/Recoverability Validation
Focused backend curl-level checks for candidate: 7141d5bcec2ac4a60f9ae91188b3bafea64814e2

Test exactly these behaviors:
1. GET /api/version returns 200 and shows commit 7141d5bcec2ac4a60f9ae91188b3bafea64814e2
2. GET /api/ready returns 200 with ok=true, state=ready, mongo_ok=true
3. GET /api/health/full returns 200 with ok=true, mongo=true, scheduler=true, backup_recent=true
4. POST /api/auth/multi-login with admin credentials succeeds and returns both session_token and portal_tokens.admin
5. Using both X-Admin-Token and X-Directory-Token, GET /api/admin/backups/integrity-check returns 200 and reflects fresh complete backup
6. If any request fails, capture exact response body and status
"""

import requests
import json
import sys
from datetime import datetime

# Backend base URL
BASE_URL = "http://localhost:8001"

# Admin credentials
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Expected commit
EXPECTED_COMMIT = "7141d5bcec2ac4a60f9ae91188b3bafea64814e2"

# Expected backup file pattern
EXPECTED_BACKUP_PATTERN = "MASCI_complete_backup_2026-07-22_155504Z.zip"

# Test results
results = {
    "test_timestamp": datetime.utcnow().isoformat() + "Z",
    "candidate_commit": EXPECTED_COMMIT,
    "tests": []
}

def log_test(test_name, passed, details):
    """Log test result"""
    result = {
        "test": test_name,
        "passed": passed,
        "details": details
    }
    results["tests"].append(result)
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{status}: {test_name}")
    print(f"Details: {json.dumps(details, indent=2)}")
    return passed

def test_1_version_endpoint():
    """Test 1: GET /api/version returns 200 and shows correct commit"""
    print("\n" + "="*80)
    print("TEST 1: Version Endpoint")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/api/version", timeout=10)
        
        details = {
            "status_code": response.status_code,
            "response_body": response.json() if response.status_code == 200 else response.text
        }
        
        if response.status_code != 200:
            return log_test("Version endpoint returns 200", False, details)
        
        data = response.json()
        commit = data.get("commit", "")
        frontend_commit = data.get("frontend_build_commit", "")
        release_match = data.get("frontend_backend_release_match", False)
        
        details["commit"] = commit
        details["frontend_build_commit"] = frontend_commit
        details["frontend_backend_release_match"] = release_match
        
        # Check commit matches expected
        commit_match = commit == EXPECTED_COMMIT
        frontend_match = frontend_commit == EXPECTED_COMMIT
        
        if not commit_match:
            details["error"] = f"Backend commit mismatch. Expected: {EXPECTED_COMMIT}, Got: {commit}"
            return log_test("Version endpoint commit verification", False, details)
        
        if not frontend_match:
            details["error"] = f"Frontend commit mismatch. Expected: {EXPECTED_COMMIT}, Got: {frontend_commit}"
            return log_test("Version endpoint frontend commit verification", False, details)
        
        if not release_match:
            details["error"] = "frontend_backend_release_match is not true"
            return log_test("Version endpoint release match verification", False, details)
        
        return log_test("Version endpoint verification", True, details)
        
    except Exception as e:
        details = {"error": str(e), "exception_type": type(e).__name__}
        return log_test("Version endpoint verification", False, details)

def test_2_ready_endpoint():
    """Test 2: GET /api/ready returns 200 with ok=true, state=ready, mongo_ok=true"""
    print("\n" + "="*80)
    print("TEST 2: Ready Endpoint")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/api/ready", timeout=10)
        
        details = {
            "status_code": response.status_code,
            "response_body": response.json() if response.status_code == 200 else response.text
        }
        
        if response.status_code != 200:
            return log_test("Ready endpoint returns 200", False, details)
        
        data = response.json()
        ok = data.get("ok", False)
        state = data.get("state", "")
        mongo_ok = data.get("mongo_ok", False)
        
        details["ok"] = ok
        details["state"] = state
        details["mongo_ok"] = mongo_ok
        
        if not ok:
            details["error"] = "ok is not true"
            return log_test("Ready endpoint ok verification", False, details)
        
        if state != "ready":
            details["error"] = f"state is not 'ready'. Got: {state}"
            return log_test("Ready endpoint state verification", False, details)
        
        if not mongo_ok:
            details["error"] = "mongo_ok is not true"
            return log_test("Ready endpoint mongo_ok verification", False, details)
        
        return log_test("Ready endpoint verification", True, details)
        
    except Exception as e:
        details = {"error": str(e), "exception_type": type(e).__name__}
        return log_test("Ready endpoint verification", False, details)

def test_3_health_full_endpoint():
    """Test 3: GET /api/health/full returns 200 with ok=true, mongo=true, scheduler=true, backup_recent=true"""
    print("\n" + "="*80)
    print("TEST 3: Health Full Endpoint")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/api/health/full", timeout=10)
        
        details = {
            "status_code": response.status_code,
            "response_body": response.json() if response.status_code == 200 else response.text
        }
        
        if response.status_code != 200:
            return log_test("Health full endpoint returns 200", False, details)
        
        data = response.json()
        ok = data.get("ok", False)
        mongo = data.get("mongo", False)
        scheduler = data.get("scheduler", False)
        backup_recent = data.get("backup_recent", False)
        
        details["ok"] = ok
        details["mongo"] = mongo
        details["scheduler"] = scheduler
        details["backup_recent"] = backup_recent
        
        if not ok:
            details["error"] = "ok is not true"
            return log_test("Health full endpoint ok verification", False, details)
        
        if not mongo:
            details["error"] = "mongo is not true"
            return log_test("Health full endpoint mongo verification", False, details)
        
        if not scheduler:
            details["error"] = "scheduler is not true"
            return log_test("Health full endpoint scheduler verification", False, details)
        
        if not backup_recent:
            details["error"] = "backup_recent is not true"
            return log_test("Health full endpoint backup_recent verification", False, details)
        
        return log_test("Health full endpoint verification", True, details)
        
    except Exception as e:
        details = {"error": str(e), "exception_type": type(e).__name__}
        return log_test("Health full endpoint verification", False, details)

def test_4_multi_login():
    """Test 4: POST /api/auth/multi-login succeeds and returns both session_token and portal_tokens.admin"""
    print("\n" + "="*80)
    print("TEST 4: Multi-Login Authentication")
    print("="*80)
    
    try:
        payload = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/multi-login", json=payload, timeout=10)
        
        details = {
            "status_code": response.status_code,
            "response_body": response.json() if response.status_code == 200 else response.text
        }
        
        if response.status_code != 200:
            return log_test("Multi-login authentication", False, details)
        
        data = response.json()
        session_token = data.get("session_token")
        portal_tokens = data.get("portal_tokens", {})
        admin_token = portal_tokens.get("admin")
        
        details["has_session_token"] = session_token is not None
        details["has_portal_tokens"] = portal_tokens is not None
        details["has_admin_token"] = admin_token is not None
        details["portal_list"] = list(portal_tokens.keys()) if portal_tokens else []
        
        if not session_token:
            details["error"] = "session_token not found in response"
            return log_test("Multi-login session_token verification", False, details)
        
        if not admin_token:
            details["error"] = "portal_tokens.admin not found in response"
            return log_test("Multi-login admin token verification", False, details)
        
        # Store tokens for next test
        results["session_token"] = session_token
        results["admin_token"] = admin_token
        
        return log_test("Multi-login authentication", True, details)
        
    except Exception as e:
        details = {"error": str(e), "exception_type": type(e).__name__}
        return log_test("Multi-login authentication", False, details)

def test_5_backup_integrity_check():
    """Test 5: GET /api/admin/backups/integrity-check with both headers returns 200 and reflects fresh complete backup"""
    print("\n" + "="*80)
    print("TEST 5: Backup Integrity Check")
    print("="*80)
    
    # Check if we have tokens from previous test
    if "session_token" not in results or "admin_token" not in results:
        details = {"error": "Cannot run test 5 without tokens from test 4"}
        return log_test("Backup integrity check", False, details)
    
    try:
        headers = {
            "X-Admin-Token": results["admin_token"],
            "X-Directory-Token": results["session_token"]
        }
        
        response = requests.get(f"{BASE_URL}/api/admin/backups/integrity-check", headers=headers, timeout=30)
        
        details = {
            "status_code": response.status_code,
            "response_body": response.json() if response.status_code == 200 else response.text
        }
        
        if response.status_code != 200:
            return log_test("Backup integrity check returns 200", False, details)
        
        data = response.json()
        
        # Check for expected backup file
        backup_file = data.get("backup_file", "")
        captured_collections = data.get("captured_collections", [])
        backup_incomplete = data.get("backup_incomplete", True)
        
        details["backup_file"] = backup_file
        details["captured_collections"] = captured_collections
        details["backup_incomplete"] = backup_incomplete
        details["notification_capture_v1_present"] = "notification_capture_v1" in captured_collections
        
        # Check if backup file matches expected pattern
        if EXPECTED_BACKUP_PATTERN not in backup_file:
            details["error"] = f"Expected backup file pattern '{EXPECTED_BACKUP_PATTERN}' not found. Got: {backup_file}"
            return log_test("Backup integrity check file verification", False, details)
        
        # Check if notification_capture_v1 is present
        if "notification_capture_v1" not in captured_collections:
            details["error"] = "notification_capture_v1 not found in captured_collections"
            return log_test("Backup integrity check notification_capture_v1 verification", False, details)
        
        # Check for BACKUP_INCOMPLETE false-positive
        if backup_incomplete:
            details["error"] = "BACKUP_INCOMPLETE false-positive detected (backup_incomplete=true)"
            return log_test("Backup integrity check BACKUP_INCOMPLETE verification", False, details)
        
        return log_test("Backup integrity check verification", True, details)
        
    except Exception as e:
        details = {"error": str(e), "exception_type": type(e).__name__}
        return log_test("Backup integrity check verification", False, details)

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("C2 LATE RECOVERY/IDENTITY/RECOVERABILITY VALIDATION")
    print(f"Candidate Commit: {EXPECTED_COMMIT}")
    print(f"Backend URL: {BASE_URL}")
    print(f"Test Timestamp: {results['test_timestamp']}")
    print("="*80)
    
    # Run tests in sequence
    test_results = []
    test_results.append(test_1_version_endpoint())
    test_results.append(test_2_ready_endpoint())
    test_results.append(test_3_health_full_endpoint())
    test_results.append(test_4_multi_login())
    test_results.append(test_5_backup_integrity_check())
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed_count = sum(1 for r in test_results if r)
    total_count = len(test_results)
    
    print(f"\nTotal Tests: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    print(f"Pass Rate: {(passed_count/total_count)*100:.1f}%")
    
    results["summary"] = {
        "total_tests": total_count,
        "passed": passed_count,
        "failed": total_count - passed_count,
        "pass_rate": f"{(passed_count/total_count)*100:.1f}%"
    }
    
    # Save results to file
    output_file = "/app/c2_recovery_identity_test_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    
    # Exit with appropriate code
    if passed_count == total_count:
        print("\n✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()

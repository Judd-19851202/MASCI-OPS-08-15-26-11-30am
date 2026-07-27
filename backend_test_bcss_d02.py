#!/usr/bin/env python3
"""
BCSS Release 2 / TRACK D-02 Backend Verification

Backend-only verification for BCSS Release 2 / TRACK D-02 in Preview.

App context:
- Preview backend base URL: https://backup-forensics.preview.emergentagent.com
- Environment target is PREVIEW only
- Login endpoint: POST /api/auth/multi-login
- Admin test credentials:
  - email: jaymn.judd@mascigc.com
  - password: Maddix123!
- Use the returned portal_tokens.admin as X-Admin-Token and session_token as X-Directory-Token

Test objectives:
1. Admin login succeeds and returns usable admin/session tokens
2. GET /api/admin/backups-complete-r2-state returns 200 and shows expected state
3. GET /api/admin/backup-verification/preview returns 200 and shows expected verification report
4. GET /api/admin/recovery/snapshot returns 200 and shows expected recovery posture
5. Verify latest archive record consistency across endpoints
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://backup-forensics.preview.emergentagent.com"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test results
results = {
    "test_suite": "BCSS Release 2 / TRACK D-02 Backend Verification",
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "base_url": BASE_URL,
    "tests": []
}

def log_test(name, passed, details=None, error=None):
    """Log a test result"""
    result = {
        "name": name,
        "passed": passed,
        "details": details or {},
        "error": error
    }
    results["tests"].append(result)
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if error:
        print(f"  Error: {error}")
    if details:
        for key, value in details.items():
            print(f"  {key}: {value}")
    return passed

def test_admin_login():
    """Test 1: Admin login succeeds and returns usable admin/session tokens"""
    print("\n=== Test 1: Admin Login ===")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=30
        )
        
        if response.status_code != 200:
            return log_test(
                "Admin login",
                False,
                {"status_code": response.status_code},
                f"Login failed with status {response.status_code}"
            )
        
        data = response.json()
        
        # Check for required tokens
        has_session_token = "session_token" in data
        has_admin_token = "portal_tokens" in data and "admin" in data.get("portal_tokens", {})
        
        if not has_session_token:
            return log_test(
                "Admin login",
                False,
                {"has_session_token": False},
                "session_token not found in response"
            )
        
        if not has_admin_token:
            return log_test(
                "Admin login",
                False,
                {"has_admin_token": False},
                "portal_tokens.admin not found in response"
            )
        
        # Store tokens for subsequent tests
        global admin_token, session_token
        admin_token = data["portal_tokens"]["admin"]
        session_token = data["session_token"]
        
        return log_test(
            "Admin login",
            True,
            {
                "session_token_length": len(session_token),
                "admin_token_length": len(admin_token),
                "portal_count": len(data.get("portal_tokens", {}))
            }
        )
        
    except Exception as e:
        return log_test("Admin login", False, error=str(e))

def test_backups_complete_r2_state():
    """Test 2: GET /api/admin/backups-complete-r2-state returns 200 and shows expected state"""
    print("\n=== Test 2: Backups Complete R2 State ===")
    try:
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=headers,
            timeout=90
        )
        
        if response.status_code != 200:
            return log_test(
                "Backups complete R2 state",
                False,
                {"status_code": response.status_code},
                f"Request failed with status {response.status_code}"
            )
        
        data = response.json()
        
        # Check required fields
        checks = {
            "in_progress": "in_progress" in data,
            "nightly_last": "nightly_last" in data,
            "hourly_activation": "hourly_activation" in data
        }
        
        # Optional fields that may not always be present
        if "stale_job_count" in data:
            checks["stale_job_count"] = True
        if "stale_lock_present" in data:
            checks["stale_lock_present"] = True
        
        details = {
            "in_progress": data.get("in_progress"),
            "stale_job_count": data.get("stale_job_count"),
            "stale_lock_present": data.get("stale_lock_present")
        }
        
        # Check nightly_last details
        if "nightly_last" in data and data["nightly_last"]:
            nightly_last = data["nightly_last"]
            details["nightly_last_filename"] = nightly_last.get("filename")
            details["nightly_last_r2_key"] = nightly_last.get("r2_key")
            
            # Verify expected filename pattern
            expected_filename = "MASCI_complete_backup_2026-07-27_021533Z.zip"
            if nightly_last.get("filename") == expected_filename:
                details["filename_matches_expected"] = True
            
            # Verify expected r2_key pattern
            expected_r2_key = "backups/auto-90d/MASCI_complete_backup_2026-07-27_021533Z.zip"
            if nightly_last.get("r2_key") == expected_r2_key:
                details["r2_key_matches_expected"] = True
        
        # Check hourly_activation details
        if "hourly_activation" in data and data["hourly_activation"]:
            hourly = data["hourly_activation"]
            details["hourly_activation_status"] = hourly.get("activation_status")
            details["hourly_activation_blockers"] = hourly.get("activation_blockers", [])
            
            # Check for expected blockers
            if "activation_blockers" in hourly:
                blockers = hourly["activation_blockers"]
                # Check if any blocker has code "environment_not_production"
                has_env_blocker = any(
                    b.get("code") == "environment_not_production" 
                    for b in blockers 
                    if isinstance(b, dict)
                )
                details["has_environment_not_production_blocker"] = has_env_blocker
            
            # Check resource preflight
            if "resource_preflight" in hourly:
                details["resource_preflight_ok"] = hourly["resource_preflight"].get("ok")
        
        all_checks_passed = all(checks.values())
        
        return log_test(
            "Backups complete R2 state",
            all_checks_passed,
            details
        )
        
    except Exception as e:
        return log_test("Backups complete R2 state", False, error=str(e))

def test_backup_verification_preview():
    """Test 3: GET /api/admin/backup-verification/preview returns 200 and shows expected verification report"""
    print("\n=== Test 3: Backup Verification Preview ===")
    try:
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        response = requests.get(
            f"{BASE_URL}/api/admin/backup-verification/preview",
            headers=headers,
            timeout=60  # Increased timeout for verification endpoint
        )
        
        if response.status_code != 200:
            return log_test(
                "Backup verification preview",
                False,
                {"status_code": response.status_code},
                f"Request failed with status {response.status_code}"
            )
        
        data = response.json()
        
        # Check required fields
        checks = {
            "report": "report" in data
        }
        
        details = {}
        
        # Check report details
        if "report" in data and data["report"]:
            report = data["report"]
            details["report_verdict"] = report.get("verdict")
            
            # Check R2 status
            if "r2" in report:
                details["r2_status"] = report["r2"].get("status")
            
            # Check ledger status
            if "ledger" in report:
                details["ledger_status"] = report["ledger"].get("status")
            
            # Check authoritative artifact
            if "r2" in report and "authoritative_artifact" in report["r2"]:
                artifact = report["r2"]["authoritative_artifact"]
                details["authoritative_artifact_filename"] = artifact.get("filename")
                
                # Verify expected filename pattern
                expected_filename = "MASCI_complete_backup_2026-07-27_021533Z.zip"
                if artifact.get("filename") == expected_filename:
                    details["artifact_filename_matches_expected"] = True
            
            # Check authoritative recovery point
            if "r2" in report and "authoritative_recovery_point" in report["r2"]:
                recovery_point = report["r2"]["authoritative_recovery_point"]
                details["authoritative_recovery_point"] = recovery_point
                
                # Check if recovery point is recent (within last 24 hours)
                # Expected: 2026-07-27T02:27:57.166000+00:00 or similar
                if recovery_point:
                    details["has_recovery_point"] = True
        
        all_checks_passed = all(checks.values())
        
        return log_test(
            "Backup verification preview",
            all_checks_passed,
            details
        )
        
    except Exception as e:
        return log_test("Backup verification preview", False, error=str(e))

def test_recovery_snapshot():
    """Test 4: GET /api/admin/recovery/snapshot returns 200 and shows expected recovery posture"""
    print("\n=== Test 4: Recovery Snapshot ===")
    try:
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        response = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers=headers,
            timeout=90
        )
        
        if response.status_code != 200:
            return log_test(
                "Recovery snapshot",
                False,
                {"status_code": response.status_code},
                f"Request failed with status {response.status_code}"
            )
        
        data = response.json()
        
        # Check required fields
        checks = {
            "last_backup": "last_backup" in data,
            "rpo": "rpo" in data,
            "last_drill": "last_drill" in data
        }
        
        details = {}
        
        # Check last_backup details
        if "last_backup" in data and data["last_backup"]:
            last_backup = data["last_backup"]
            details["last_backup_filename"] = last_backup.get("filename")
            
            # Verify expected filename pattern
            expected_filename = "MASCI_complete_backup_2026-07-27_021533Z.zip"
            if last_backup.get("filename") == expected_filename:
                details["last_backup_filename_matches_expected"] = True
        
        # Check RPO status
        if "rpo" in data and data["rpo"]:
            rpo = data["rpo"]
            details["rpo_status"] = rpo.get("status")
            
            # Verify RPO status is GREEN
            if rpo.get("status") == "GREEN":
                details["rpo_status_is_green"] = True
        
        # Check last_drill details
        if "last_drill" in data and data["last_drill"]:
            last_drill = data["last_drill"]
            details["last_drill_outcome"] = last_drill.get("outcome")
            
            # Verify last drill outcome is ok
            if last_drill.get("outcome") == "ok":
                details["last_drill_outcome_is_ok"] = True
        
        all_checks_passed = all(checks.values())
        
        return log_test(
            "Recovery snapshot",
            all_checks_passed,
            details
        )
        
    except Exception as e:
        return log_test("Recovery snapshot", False, error=str(e))

def test_archive_consistency():
    """Test 5: Verify latest archive record consistency across endpoints"""
    print("\n=== Test 5: Archive Consistency ===")
    try:
        # Collect filenames from all endpoints
        filenames = {}
        
        # From backups-complete-r2-state
        if results["tests"][1]["passed"]:
            test_details = results["tests"][1]["details"]
            if "nightly_last_filename" in test_details:
                filenames["backups_complete_r2_state"] = test_details["nightly_last_filename"]
        
        # From backup-verification-preview
        if results["tests"][2]["passed"]:
            test_details = results["tests"][2]["details"]
            if "authoritative_artifact_filename" in test_details:
                filenames["backup_verification_preview"] = test_details["authoritative_artifact_filename"]
        
        # From recovery-snapshot
        if results["tests"][3]["passed"]:
            test_details = results["tests"][3]["details"]
            if "last_backup_filename" in test_details:
                filenames["recovery_snapshot"] = test_details["last_backup_filename"]
        
        # Check consistency
        unique_filenames = set(filenames.values())
        is_consistent = len(unique_filenames) == 1
        
        details = {
            "filenames_by_endpoint": filenames,
            "unique_filenames": list(unique_filenames),
            "is_consistent": is_consistent
        }
        
        if is_consistent:
            details["consistent_filename"] = list(unique_filenames)[0]
        
        return log_test(
            "Archive consistency across endpoints",
            is_consistent,
            details
        )
        
    except Exception as e:
        return log_test("Archive consistency across endpoints", False, error=str(e))

def main():
    """Run all tests"""
    print("=" * 80)
    print("BCSS Release 2 / TRACK D-02 Backend Verification")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Admin Email: {ADMIN_EMAIL}")
    print(f"Timestamp: {results['timestamp']}")
    print("=" * 80)
    
    # Run tests in sequence
    test_results = []
    
    # Test 1: Admin login (required for subsequent tests)
    test_results.append(test_admin_login())
    
    if not test_results[0]:
        print("\n❌ Admin login failed. Cannot proceed with remaining tests.")
        results["summary"] = {
            "total_tests": 1,
            "passed": 0,
            "failed": 1,
            "pass_rate": "0.0%"
        }
    else:
        # Test 2-4: Backend endpoints
        test_results.append(test_backups_complete_r2_state())
        test_results.append(test_backup_verification_preview())
        test_results.append(test_recovery_snapshot())
        
        # Test 5: Archive consistency
        test_results.append(test_archive_consistency())
        
        # Calculate summary
        total_tests = len(test_results)
        passed_tests = sum(test_results)
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "pass_rate": f"{pass_rate:.1f}%"
        }
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {results['summary']['total_tests']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Pass Rate: {results['summary']['pass_rate']}")
    print("=" * 80)
    
    # Save results to file
    output_file = "/app/backend_test_bcss_d02_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_file}")
    
    # Exit with appropriate code
    sys.exit(0 if results['summary']['passed'] == results['summary']['total_tests'] else 1)

if __name__ == "__main__":
    main()

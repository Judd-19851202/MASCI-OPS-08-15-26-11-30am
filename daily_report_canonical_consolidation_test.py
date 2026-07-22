#!/usr/bin/env python3
"""
Daily Report Canonical Consolidation - Final Backend Verification
Focused backend certification check for Track 15.69 canonical consolidation.

Test Items:
1. GET /api/ready returns 200 ok=true
2. GET /api/health/full returns 200 ok=true
3. GET /api/version returns commit 8c4f2655ef2d29f5b58685e5770b766a213c9b2f and frontend_backend_release_match=true
4. POST /api/auth/multi-login with admin creds succeeds
5. GET /api/daily-reports/approved returns items with source=canonical only
6. GET /api/daily-reports/1/pdf returns queued PDF job payload
7. GET /api/dr-v2/meta is read-only compatibility (legacy_writes_blocked=true)
8. Admin backup integrity check passes
9. Rollback simulation artifact exists at /app/test_reports/track_15_69_rollback_simulation.json
"""

import requests
import json
import os
from pathlib import Path
from datetime import datetime

BASE_URL = "http://localhost:8001"
EXPECTED_COMMIT = "8c4f2655ef2d29f5b58685e5770b766a213c9b2f"

# Admin credentials from test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

results = {
    "test_suite": "Daily Report Canonical Consolidation - Final Backend Verification",
    "base_url": BASE_URL,
    "expected_commit": EXPECTED_COMMIT,
    "timestamp": datetime.utcnow().isoformat() + "Z",
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
    print(f"{status}: {test_name}")
    if not passed:
        print(f"  Details: {details}")
    return passed

def test_1_ready_endpoint():
    """Test 1: GET /api/ready returns 200 ok=true"""
    try:
        resp = requests.get(f"{BASE_URL}/api/ready", timeout=10)
        data = resp.json()
        
        passed = (
            resp.status_code == 200 and
            data.get("ok") is True
        )
        
        details = {
            "status_code": resp.status_code,
            "ok": data.get("ok"),
            "state": data.get("state"),
            "mongo_ok": data.get("mongo_ok"),
            "event_loop_ok": data.get("event_loop_ok"),
            "startup_complete": data.get("startup_complete")
        }
        
        return log_test("Test 1: /api/ready returns 200 ok=true", passed, details)
    except Exception as e:
        return log_test("Test 1: /api/ready returns 200 ok=true", False, {"error": str(e)})

def test_2_health_full_endpoint():
    """Test 2: GET /api/health/full returns 200 ok=true"""
    try:
        resp = requests.get(f"{BASE_URL}/api/health/full", timeout=10)
        data = resp.json()
        
        passed = (
            resp.status_code == 200 and
            data.get("ok") is True
        )
        
        details = {
            "status_code": resp.status_code,
            "ok": data.get("ok"),
            "mongo": data.get("mongo"),
            "scheduler": data.get("scheduler"),
            "backup_recent": data.get("backup_recent"),
            "runtime_identity_ok": data.get("runtime_identity_ok")
        }
        
        return log_test("Test 2: /api/health/full returns 200 ok=true", passed, details)
    except Exception as e:
        return log_test("Test 2: /api/health/full returns 200 ok=true", False, {"error": str(e)})

def test_3_version_endpoint():
    """Test 3: GET /api/version returns correct commit and frontend_backend_release_match=true"""
    try:
        resp = requests.get(f"{BASE_URL}/api/version", timeout=10)
        data = resp.json()
        
        passed = (
            resp.status_code == 200 and
            data.get("commit") == EXPECTED_COMMIT and
            data.get("frontend_backend_release_match") is True
        )
        
        details = {
            "status_code": resp.status_code,
            "commit": data.get("commit"),
            "expected_commit": EXPECTED_COMMIT,
            "commit_match": data.get("commit") == EXPECTED_COMMIT,
            "frontend_backend_release_match": data.get("frontend_backend_release_match"),
            "source_hash": data.get("source_hash"),
            "frontend_build_commit": data.get("frontend_build_commit")
        }
        
        return log_test("Test 3: /api/version returns correct commit and frontend_backend_release_match=true", passed, details)
    except Exception as e:
        return log_test("Test 3: /api/version returns correct commit and frontend_backend_release_match=true", False, {"error": str(e)})

def test_4_multi_login():
    """Test 4: POST /api/auth/multi-login with admin creds succeeds"""
    try:
        payload = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        resp = requests.post(f"{BASE_URL}/api/auth/multi-login", json=payload, timeout=10)
        data = resp.json()
        
        passed = (
            resp.status_code == 200 and
            "session_token" in data and
            "portal_tokens" in data and
            "admin" in data.get("portal_tokens", {})
        )
        
        details = {
            "status_code": resp.status_code,
            "has_session_token": "session_token" in data,
            "has_portal_tokens": "portal_tokens" in data,
            "portal_tokens_keys": list(data.get("portal_tokens", {}).keys()) if "portal_tokens" in data else []
        }
        
        # Store tokens for later tests
        if passed:
            global admin_token, directory_token
            admin_token = data["portal_tokens"]["admin"]
            directory_token = data["session_token"]
        
        return log_test("Test 4: POST /api/auth/multi-login succeeds", passed, details)
    except Exception as e:
        return log_test("Test 4: POST /api/auth/multi-login succeeds", False, {"error": str(e)})

def test_5_daily_reports_approved():
    """Test 5: GET /api/daily-reports/approved returns items with source=canonical only"""
    try:
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": directory_token
        }
        resp = requests.get(f"{BASE_URL}/api/daily-reports/approved", headers=headers, timeout=10)
        data = resp.json()
        
        items = data.get("items", [])
        
        # Check if all items have source=canonical
        non_canonical_sources = []
        for item in items:
            source = item.get("source")
            if source != "canonical":
                non_canonical_sources.append({
                    "id": item.get("id"),
                    "source": source
                })
        
        passed = (
            resp.status_code == 200 and
            len(non_canonical_sources) == 0
        )
        
        details = {
            "status_code": resp.status_code,
            "total_items": len(items),
            "all_canonical": len(non_canonical_sources) == 0,
            "non_canonical_count": len(non_canonical_sources),
            "non_canonical_samples": non_canonical_sources[:5] if non_canonical_sources else []
        }
        
        return log_test("Test 5: /api/daily-reports/approved returns items with source=canonical only", passed, details)
    except Exception as e:
        return log_test("Test 5: /api/daily-reports/approved returns items with source=canonical only", False, {"error": str(e)})

def test_6_daily_report_pdf():
    """Test 6: GET /api/daily-reports/1/pdf returns queued PDF job payload"""
    try:
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": directory_token
        }
        
        # First get a daily report ID
        resp_list = requests.get(f"{BASE_URL}/api/daily-reports/approved?limit=1", headers=headers, timeout=10)
        data_list = resp_list.json()
        items = data_list.get("items", [])
        
        if not items:
            return log_test("Test 6: /api/daily-reports/{id}/pdf returns queued PDF job payload", False, {
                "error": "No daily reports found to test PDF endpoint"
            })
        
        report_id = items[0].get("id")
        
        # Now test PDF endpoint
        resp = requests.get(f"{BASE_URL}/api/daily-reports/{report_id}/pdf", headers=headers, timeout=10)
        data = resp.json()
        
        # PDF endpoint should return 202 with job_id or similar queued response
        passed = (
            resp.status_code in [200, 202] and
            ("job_id" in data or "status" in data or "queued" in str(data).lower())
        )
        
        details = {
            "status_code": resp.status_code,
            "report_id": report_id,
            "response_keys": list(data.keys()) if isinstance(data, dict) else [],
            "has_job_id": "job_id" in data if isinstance(data, dict) else False,
            "response_sample": str(data)[:200]
        }
        
        return log_test("Test 6: /api/daily-reports/{id}/pdf returns queued PDF job payload", passed, details)
    except Exception as e:
        return log_test("Test 6: /api/daily-reports/{id}/pdf returns queued PDF job payload", False, {"error": str(e)})

def test_7_dr_v2_meta():
    """Test 7: GET /api/dr-v2/meta is read-only compatibility (legacy_writes_blocked=true)"""
    try:
        resp = requests.get(f"{BASE_URL}/api/dr-v2/meta", timeout=10)
        data = resp.json()
        
        passed = (
            resp.status_code == 200 and
            data.get("legacy_writes_blocked") is True and
            "canonical_route" in data and
            "canonical_api" in data
        )
        
        details = {
            "status_code": resp.status_code,
            "legacy_writes_blocked": data.get("legacy_writes_blocked"),
            "canonical_route": data.get("canonical_route"),
            "canonical_api": data.get("canonical_api"),
            "full_response": data
        }
        
        return log_test("Test 7: /api/dr-v2/meta is read-only compatibility (legacy_writes_blocked=true)", passed, details)
    except Exception as e:
        return log_test("Test 7: /api/dr-v2/meta is read-only compatibility (legacy_writes_blocked=true)", False, {"error": str(e)})

def test_8_backup_integrity():
    """Test 8: Admin backup integrity check passes"""
    try:
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": directory_token
        }
        resp = requests.get(f"{BASE_URL}/api/admin/backups/integrity-check", headers=headers, timeout=60)
        data = resp.json()
        
        passed = (
            resp.status_code == 200 and
            data.get("integrity_result") == "PASS"
        )
        
        details = {
            "status_code": resp.status_code,
            "integrity_result": data.get("integrity_result"),
            "last_backup_filename": data.get("last_backup_filename"),
            "collections_captured": data.get("collections_captured"),
            "documents_captured": data.get("documents_captured"),
            "missing_from_backup": data.get("missing_from_backup", [])
        }
        
        return log_test("Test 8: Admin backup integrity check passes", passed, details)
    except Exception as e:
        return log_test("Test 8: Admin backup integrity check passes", False, {"error": str(e)})

def test_9_rollback_simulation_artifact():
    """Test 9: Rollback simulation artifact exists"""
    try:
        artifact_path = Path("/app/test_reports/track_15_69_rollback_simulation.json")
        
        if not artifact_path.exists():
            return log_test("Test 9: Rollback simulation artifact exists", False, {
                "error": f"Artifact not found at {artifact_path}"
            })
        
        # Read and validate artifact
        with open(artifact_path, 'r') as f:
            artifact_data = json.load(f)
        
        # Check if artifact shows PASS (rollback_within_budget=true and drift_count=0)
        passed = (
            artifact_path.exists() and
            artifact_data.get("rollback_within_budget") is True and
            artifact_data.get("drift_count") == 0
        )
        
        details = {
            "artifact_path": str(artifact_path),
            "exists": True,
            "rollback_within_budget": artifact_data.get("rollback_within_budget"),
            "drift_count": artifact_data.get("drift_count"),
            "rollback_duration_s": artifact_data.get("rollback_duration_s"),
            "rollback_target_s": artifact_data.get("rollback_target_s")
        }
        
        return log_test("Test 9: Rollback simulation artifact exists and shows PASS", passed, details)
    except Exception as e:
        return log_test("Test 9: Rollback simulation artifact exists and shows PASS", False, {"error": str(e)})

def main():
    print("=" * 80)
    print("Daily Report Canonical Consolidation - Final Backend Verification")
    print(f"Base URL: {BASE_URL}")
    print(f"Expected Commit: {EXPECTED_COMMIT}")
    print("=" * 80)
    print()
    
    # Run tests in order
    test_results = []
    
    test_results.append(test_1_ready_endpoint())
    test_results.append(test_2_health_full_endpoint())
    test_results.append(test_3_version_endpoint())
    test_results.append(test_4_multi_login())
    
    # Tests 5-8 require authentication
    if test_results[3]:  # If multi-login succeeded
        test_results.append(test_5_daily_reports_approved())
        test_results.append(test_6_daily_report_pdf())
        test_results.append(test_7_dr_v2_meta())
        test_results.append(test_8_backup_integrity())
    else:
        print("\n⚠️  Skipping tests 5-8 due to authentication failure")
        test_results.extend([False, False, False, False])
    
    test_results.append(test_9_rollback_simulation_artifact())
    
    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    passed_count = sum(test_results)
    total_count = len(test_results)
    
    results["summary"] = {
        "total_tests": total_count,
        "passed": passed_count,
        "failed": total_count - passed_count,
        "pass_rate": f"{(passed_count/total_count)*100:.1f}%"
    }
    
    print(f"Total Tests: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    print(f"Pass Rate: {(passed_count/total_count)*100:.1f}%")
    print()
    
    if passed_count == total_count:
        print("✅ ALL TESTS PASSED - Daily Report canonical consolidation backend is VERIFIED")
        results["overall_status"] = "PASS"
    else:
        print("❌ SOME TESTS FAILED - Review details above")
        results["overall_status"] = "FAIL"
    
    # Save results
    output_path = Path("/app/daily_report_canonical_consolidation_results.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: {output_path}")
    
    return 0 if passed_count == total_count else 1

if __name__ == "__main__":
    exit(main())

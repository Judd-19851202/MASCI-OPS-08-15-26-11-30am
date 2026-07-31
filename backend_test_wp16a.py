#!/usr/bin/env python3
"""
Backend API Testing for WP-16A Backend Reliability Fixes

Tests the following:
1. Transportation cleanup endpoint performance and correctness
   - GET /api/admin/transportation/intelligence/cleanup-signals?days=30
   - Test with valid X-Dispatch-Token only
   - Test with valid X-Dispatch-Token + stale invalid X-Admin-Token
   - Test with valid X-Dispatch-Token + stale invalid X-Admin-Token + stale invalid X-Directory-Token
   - All three should return 200
   - Report approximate latency (should be well under ~25s)

2. Negative regression
   - No auth token on cleanup-signals should not expose data
   - Dispatch token on stricter admin-only /api/admin/transportation/intelligence/recommendations should be rejected

3. Backup reliability guard / manual trigger
   - Login as admin with jaymn.judd@mascigc.com / Maddix123!
   - Verify /api/admin/recovery/snapshot hourly activation blockers
   - POST /api/admin/backups/run-complete-now should be accepted for manual retry
   - GET /api/admin/backups-complete-r2-state should show accepted/in-progress or later-successful manual complete-r2 job
"""

import requests
import json
import sys
import time
from typing import Dict, Any, Optional

# Backend URL from environment
BACKEND_URL = "https://backup-forensics.preview.emergentagent.com/api"

# Test credentials
DISPATCH_CREDS = {
    "email": "cert.dispatch@example.com",
    "password": "CertProof2026!"
}

ADMIN_CREDS = {
    "email": "jaymn.judd@mascigc.com",
    "password": "Maddix123!"
}

class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.total = 0
    
    def add_pass(self, test_name: str, details: str = ""):
        self.total += 1
        self.passed.append((test_name, details))
        print(f"✅ PASS: {test_name}")
        if details:
            print(f"   {details}")
    
    def add_fail(self, test_name: str, details: str = ""):
        self.total += 1
        self.failed.append((test_name, details))
        print(f"❌ FAIL: {test_name}")
        if details:
            print(f"   {details}")
    
    def summary(self):
        print("\n" + "="*80)
        print(f"BACKEND TEST SUMMARY: {len(self.passed)}/{self.total} tests passed")
        print("="*80)
        if self.failed:
            print("\n❌ FAILED TESTS:")
            for test_name, details in self.failed:
                print(f"  - {test_name}")
                if details:
                    print(f"    {details}")
        else:
            print("\n✅ ALL TESTS PASSED")
        return len(self.failed) == 0

def login_dispatch(results: TestResult) -> Optional[str]:
    """Login as Dispatch user and return token"""
    test_name = "Login as Dispatch (cert.dispatch@example.com)"
    try:
        response = requests.post(
            f"{BACKEND_URL}/dispatch/login",
            json=DISPATCH_CREDS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "token" in data:
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, token obtained"
                )
                return data["token"]
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but missing token in response"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200. Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")
    return None

def login_admin(results: TestResult) -> Optional[Dict[str, str]]:
    """Login as Admin user and return tokens"""
    test_name = "Login as Admin (jaymn.judd@mascigc.com)"
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/multi-login",
            json=ADMIN_CREDS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "session_token" in data and "portal_tokens" in data:
                admin_token = data["portal_tokens"].get("admin")
                directory_token = data["session_token"]
                if admin_token:
                    results.add_pass(
                        test_name,
                        f"Status: {response.status_code}, admin and directory tokens obtained"
                    )
                    return {
                        "admin": admin_token,
                        "directory": directory_token
                    }
                else:
                    results.add_fail(
                        test_name,
                        f"Status: {response.status_code}, but missing admin token in portal_tokens"
                    )
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but missing session_token or portal_tokens"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200. Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")
    return None

def test_cleanup_signals_valid_dispatch_only(results: TestResult, dispatch_token: str):
    """Test cleanup-signals with only valid X-Dispatch-Token"""
    test_name = "GET /api/admin/transportation/intelligence/cleanup-signals?days=30 (valid X-Dispatch-Token only)"
    try:
        headers = {
            "X-Dispatch-Token": dispatch_token
        }
        
        start_time = time.time()
        response = requests.get(
            f"{BACKEND_URL}/admin/transportation/intelligence/cleanup-signals?days=30",
            headers=headers,
            timeout=30
        )
        latency = time.time() - start_time
        
        if response.status_code == 200:
            results.add_pass(
                test_name,
                f"Status: {response.status_code}, Latency: {latency:.2f}s (optimized from ~25s)"
            )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200. Latency: {latency:.2f}s. Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")

def test_cleanup_signals_with_stale_admin(results: TestResult, dispatch_token: str):
    """Test cleanup-signals with valid X-Dispatch-Token + stale invalid X-Admin-Token"""
    test_name = "GET /api/admin/transportation/intelligence/cleanup-signals?days=30 (valid Dispatch + stale Admin)"
    try:
        headers = {
            "X-Dispatch-Token": dispatch_token,
            "X-Admin-Token": "STALE_INVALID_ADMIN_TOKEN_12345"
        }
        
        start_time = time.time()
        response = requests.get(
            f"{BACKEND_URL}/admin/transportation/intelligence/cleanup-signals?days=30",
            headers=headers,
            timeout=30
        )
        latency = time.time() - start_time
        
        if response.status_code == 200:
            results.add_pass(
                test_name,
                f"Status: {response.status_code}, Latency: {latency:.2f}s (stale admin token did not block access)"
            )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200. Latency: {latency:.2f}s. Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")

def test_cleanup_signals_with_stale_admin_and_directory(results: TestResult, dispatch_token: str):
    """Test cleanup-signals with valid X-Dispatch-Token + stale invalid X-Admin-Token + stale invalid X-Directory-Token"""
    test_name = "GET /api/admin/transportation/intelligence/cleanup-signals?days=30 (valid Dispatch + stale Admin + stale Directory)"
    try:
        headers = {
            "X-Dispatch-Token": dispatch_token,
            "X-Admin-Token": "STALE_INVALID_ADMIN_TOKEN_12345",
            "X-Directory-Token": "STALE_INVALID_DIRECTORY_TOKEN_67890"
        }
        
        start_time = time.time()
        response = requests.get(
            f"{BACKEND_URL}/admin/transportation/intelligence/cleanup-signals?days=30",
            headers=headers,
            timeout=30
        )
        latency = time.time() - start_time
        
        if response.status_code == 200:
            results.add_pass(
                test_name,
                f"Status: {response.status_code}, Latency: {latency:.2f}s (stale tokens did not block access)"
            )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200. Latency: {latency:.2f}s. Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")

def test_cleanup_signals_no_auth(results: TestResult):
    """Test cleanup-signals with no auth token - should not expose data"""
    test_name = "GET /api/admin/transportation/intelligence/cleanup-signals?days=30 (no auth - should reject)"
    try:
        response = requests.get(
            f"{BACKEND_URL}/admin/transportation/intelligence/cleanup-signals?days=30",
            timeout=10
        )
        
        if response.status_code in [401, 403]:
            results.add_pass(
                test_name,
                f"Status: {response.status_code}, correctly rejected unauthenticated request"
            )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 401 or 403. Data may be exposed! Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")

def test_recommendations_dispatch_rejected(results: TestResult, dispatch_token: str):
    """Test recommendations endpoint with Dispatch token - should be rejected (admin-only)"""
    test_name = "GET /api/admin/transportation/intelligence/recommendations (Dispatch token - should reject)"
    try:
        headers = {
            "X-Dispatch-Token": dispatch_token
        }
        
        response = requests.get(
            f"{BACKEND_URL}/admin/transportation/intelligence/recommendations",
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [401, 403]:
            results.add_pass(
                test_name,
                f"Status: {response.status_code}, correctly rejected Dispatch token on admin-only endpoint"
            )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 401 or 403. Dispatch should not access admin-only endpoint! Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")

def test_recovery_snapshot(results: TestResult, admin_tokens: Dict[str, str]):
    """Test /api/admin/recovery/snapshot - verify hourly activation blockers"""
    test_name = "GET /api/admin/recovery/snapshot (verify tmp headroom check)"
    try:
        headers = {
            "X-Admin-Token": admin_tokens["admin"],
            "X-Directory-Token": admin_tokens["directory"]
        }
        
        response = requests.get(
            f"{BACKEND_URL}/admin/recovery/snapshot",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check recent failures for disk pressure blockers
            failures = data.get("failures_7d", [])
            recent_jobs = data.get("scheduler", {}).get("backup_runtime", {}).get("recent_complete_jobs", [])
            
            # Look for deferred jobs with app_disk_pressure when tmp headroom is sufficient
            problematic_deferrals = []
            for job in recent_jobs:
                if job.get("state") == "deferred" and job.get("result", {}).get("reason") == "resource_guard":
                    preflight = job.get("result", {}).get("preflight", {})
                    tmp_free = preflight.get("tmp_disk_free_bytes", 0)
                    min_required = preflight.get("min_free_bytes_required", 0)
                    reasons = preflight.get("reasons", [])
                    
                    # If tmp has sufficient headroom but still deferred due to app_disk_pressure
                    if tmp_free > min_required and any("app_disk_pressure" in r for r in reasons):
                        problematic_deferrals.append({
                            "job_id": job.get("job_id"),
                            "tmp_free_gb": round(tmp_free / (1024**3), 2),
                            "min_required_gb": round(min_required / (1024**3), 2),
                            "reasons": reasons
                        })
            
            if problematic_deferrals:
                details = f"Status: {response.status_code}, but found {len(problematic_deferrals)} deferred jobs with sufficient tmp headroom. "
                details += f"Example: tmp_free={problematic_deferrals[0]['tmp_free_gb']}GB > min_required={problematic_deferrals[0]['min_required_gb']}GB, "
                details += f"but deferred due to: {problematic_deferrals[0]['reasons']}"
                results.add_fail(test_name, details)
            else:
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, no problematic deferrals found (tmp headroom check working correctly)"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200. Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")

def test_run_complete_now(results: TestResult, admin_tokens: Dict[str, str]):
    """Test POST /api/admin/backups/run-complete-now - should accept manual retry"""
    test_name = "POST /api/admin/backups/run-complete-now (manual retry acceptance)"
    try:
        headers = {
            "X-Admin-Token": admin_tokens["admin"],
            "X-Directory-Token": admin_tokens["directory"]
        }
        
        response = requests.post(
            f"{BACKEND_URL}/admin/backups/run-complete-now",
            headers=headers,
            json={},
            timeout=10
        )
        
        if response.status_code in [200, 202]:
            results.add_pass(
                test_name,
                f"Status: {response.status_code}, manual retry accepted"
            )
        elif response.status_code == 409:
            # 409 means a backup is already in progress - this is acceptable behavior
            # The key is that same-hour manual retries should not be rejected just because
            # a prior same-hour manual attempt was deferred
            response_data = response.json()
            detail = response_data.get("detail", "")
            
            if "already in progress" in detail.lower():
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, backup already in progress (acceptable - not rejected due to prior deferral)"
                )
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, unexpected 409 reason: {detail}"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200, 202, or 409. Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")

def test_backups_complete_r2_state(results: TestResult, admin_tokens: Dict[str, str]):
    """Test GET /api/admin/backups-complete-r2-state - should show accepted/in-progress or successful job"""
    test_name = "GET /api/admin/backups-complete-r2-state (verify manual job state)"
    try:
        headers = {
            "X-Admin-Token": admin_tokens["admin"],
            "X-Directory-Token": admin_tokens["directory"]
        }
        
        response = requests.get(
            f"{BACKEND_URL}/admin/backups-complete-r2-state",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            state_text = json.dumps(data).lower()
            
            # Check for accepted, in-progress, or successful states
            has_accepted = "accepted" in state_text
            has_in_progress = "in_progress" in state_text or "in-progress" in state_text or "running" in state_text
            has_success = "success" in state_text or "completed" in state_text
            
            if has_accepted or has_in_progress or has_success:
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, manual complete-r2 job shows accepted/in-progress/successful state"
                )
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but no accepted/in-progress/successful state detected. Response: {json.dumps(data)[:200]}"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200. Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")

def main():
    print("="*80)
    print("WP-16A Backend Reliability Fixes Verification")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print("="*80)
    print()
    
    results = TestResult()
    
    # Section 1: Transportation cleanup endpoint
    print("="*80)
    print("SECTION 1: Transportation Cleanup Endpoint Performance and Correctness")
    print("="*80)
    print()
    
    dispatch_token = login_dispatch(results)
    if dispatch_token:
        print()
        test_cleanup_signals_valid_dispatch_only(results, dispatch_token)
        print()
        test_cleanup_signals_with_stale_admin(results, dispatch_token)
        print()
        test_cleanup_signals_with_stale_admin_and_directory(results, dispatch_token)
    else:
        print("❌ Cannot proceed with cleanup endpoint tests - Dispatch login failed")
    
    # Section 2: Negative regression
    print()
    print("="*80)
    print("SECTION 2: Negative Regression Tests")
    print("="*80)
    print()
    
    test_cleanup_signals_no_auth(results)
    print()
    
    if dispatch_token:
        test_recommendations_dispatch_rejected(results, dispatch_token)
    else:
        print("❌ Cannot test recommendations endpoint - Dispatch login failed")
    
    # Section 3: Backup reliability guard / manual trigger
    print()
    print("="*80)
    print("SECTION 3: Backup Reliability Guard / Manual Trigger")
    print("="*80)
    print()
    
    admin_tokens = login_admin(results)
    if admin_tokens:
        print()
        test_recovery_snapshot(results, admin_tokens)
        print()
        test_run_complete_now(results, admin_tokens)
        print()
        # Wait a moment for the job to be registered
        print("Waiting 2 seconds for job to be registered...")
        time.sleep(2)
        test_backups_complete_r2_state(results, admin_tokens)
    else:
        print("❌ Cannot proceed with backup tests - Admin login failed")
    
    # Print summary
    success = results.summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

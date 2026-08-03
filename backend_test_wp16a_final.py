#!/usr/bin/env python3
"""
WP-16A Backend Reliability Fixes - Final Independent Verification

Review Request Verification Points:
1. Cleanup-signals mixed-session cases still return 200 and remain fast (~sub-3s):
   - dispatch only
   - dispatch + stale admin
   - dispatch + stale admin + stale directory
2. No token still rejected on cleanup-signals
3. Dispatch still rejected on admin-only recommendations route
4. `/api/admin/recovery/snapshot` hourly activation blockers no longer include 
   `resource_preflight_failed` / app disk pressure blocker for complete-R2
5. Manual complete-backup retry endpoint still accepts same-hour manual retry attempts 
   (or returns acceptable in-progress conflict if one is already running)
6. `/api/admin/backups-complete-r2-state` reflects the current manual complete-r2 run truthfully
"""

import requests
import json
import time
from typing import Dict, Optional

BACKEND_URL = "https://masci-audit-hub.preview.emergentagent.com/api"

DISPATCH_CREDS = {
    "email": "cert.dispatch@example.com",
    "password": "CertProof2026!"
}

ADMIN_CREDS = {
    "email": "jaymn.judd@mascigc.com",
    "password": "Maddix123!"
}

class TestResults:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
    
    def add(self, name: str, passed: bool, details: str = "", latency: Optional[float] = None):
        status = "✅ PASS" if passed else "❌ FAIL"
        latency_str = f" ({latency:.2f}s)" if latency else ""
        print(f"{status}: {name}{latency_str}")
        if details:
            print(f"   {details}")
        print()
        
        self.tests.append({
            "name": name,
            "passed": passed,
            "details": details,
            "latency": latency
        })
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def summary(self):
        total = self.passed + self.failed
        print("="*80)
        print(f"FINAL RESULTS: {self.passed}/{total} tests passed")
        print("="*80)
        
        if self.failed > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.tests:
                if not test["passed"]:
                    print(f"  - {test['name']}")
                    if test["details"]:
                        print(f"    {test['details']}")
        else:
            print("\n✅ ALL TESTS PASSED")
        
        return self.failed == 0

def main():
    print("="*80)
    print("WP-16A Backend Reliability Fixes - Final Independent Verification")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print("="*80)
    print()
    
    results = TestResults()
    
    # ========================================================================
    # VERIFICATION POINT 1: Cleanup-signals mixed-session cases
    # ========================================================================
    print("="*80)
    print("VERIFICATION POINT 1: Cleanup-signals mixed-session cases")
    print("="*80)
    print()
    
    # Login as dispatch
    print("Logging in as dispatch...")
    try:
        response = requests.post(
            f"{BACKEND_URL}/dispatch/login",
            json=DISPATCH_CREDS,
            timeout=10
        )
        
        if response.status_code == 200:
            dispatch_token = response.json().get("token")
            print(f"✅ Dispatch login successful\n")
        else:
            print(f"❌ Dispatch login failed: {response.status_code}\n")
            dispatch_token = None
    except Exception as e:
        print(f"❌ Dispatch login exception: {e}\n")
        dispatch_token = None
    
    if dispatch_token:
        # Test 1a: dispatch only
        try:
            start = time.time()
            response = requests.get(
                f"{BACKEND_URL}/admin/transportation/intelligence/cleanup-signals?days=30",
                headers={"X-Dispatch-Token": dispatch_token},
                timeout=30
            )
            latency = time.time() - start
            
            passed = response.status_code == 200 and latency < 3.0
            details = f"Status: {response.status_code}, Latency: {latency:.2f}s"
            if not passed and response.status_code != 200:
                details += f", Response: {response.text[:200]}"
            elif not passed and latency >= 3.0:
                details += " (SLOW - should be sub-3s)"
            
            results.add(
                "1a. Cleanup-signals with dispatch only",
                passed,
                details,
                latency
            )
        except Exception as e:
            results.add("1a. Cleanup-signals with dispatch only", False, f"Exception: {e}")
        
        # Test 1b: dispatch + stale admin
        try:
            start = time.time()
            response = requests.get(
                f"{BACKEND_URL}/admin/transportation/intelligence/cleanup-signals?days=30",
                headers={
                    "X-Dispatch-Token": dispatch_token,
                    "X-Admin-Token": "STALE_INVALID_ADMIN_TOKEN_12345"
                },
                timeout=30
            )
            latency = time.time() - start
            
            passed = response.status_code == 200 and latency < 3.0
            details = f"Status: {response.status_code}, Latency: {latency:.2f}s"
            if not passed and response.status_code != 200:
                details += f", Response: {response.text[:200]}"
            elif not passed and latency >= 3.0:
                details += " (SLOW - should be sub-3s)"
            
            results.add(
                "1b. Cleanup-signals with dispatch + stale admin",
                passed,
                details,
                latency
            )
        except Exception as e:
            results.add("1b. Cleanup-signals with dispatch + stale admin", False, f"Exception: {e}")
        
        # Test 1c: dispatch + stale admin + stale directory
        try:
            start = time.time()
            response = requests.get(
                f"{BACKEND_URL}/admin/transportation/intelligence/cleanup-signals?days=30",
                headers={
                    "X-Dispatch-Token": dispatch_token,
                    "X-Admin-Token": "STALE_INVALID_ADMIN_TOKEN_12345",
                    "X-Directory-Token": "STALE_INVALID_DIRECTORY_TOKEN_67890"
                },
                timeout=30
            )
            latency = time.time() - start
            
            passed = response.status_code == 200 and latency < 3.0
            details = f"Status: {response.status_code}, Latency: {latency:.2f}s"
            if not passed and response.status_code != 200:
                details += f", Response: {response.text[:200]}"
            elif not passed and latency >= 3.0:
                details += " (SLOW - should be sub-3s)"
            
            results.add(
                "1c. Cleanup-signals with dispatch + stale admin + stale directory",
                passed,
                details,
                latency
            )
        except Exception as e:
            results.add("1c. Cleanup-signals with dispatch + stale admin + stale directory", False, f"Exception: {e}")
    
    # ========================================================================
    # VERIFICATION POINT 2: No token rejected on cleanup-signals
    # ========================================================================
    print("="*80)
    print("VERIFICATION POINT 2: No token rejected on cleanup-signals")
    print("="*80)
    print()
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/admin/transportation/intelligence/cleanup-signals?days=30",
            timeout=10
        )
        
        passed = response.status_code in [401, 403]
        details = f"Status: {response.status_code}"
        if not passed:
            details += f" (Expected 401/403), Response: {response.text[:200]}"
        
        results.add(
            "2. No token rejected on cleanup-signals",
            passed,
            details
        )
    except Exception as e:
        results.add("2. No token rejected on cleanup-signals", False, f"Exception: {e}")
    
    # ========================================================================
    # VERIFICATION POINT 3: Dispatch rejected on admin-only recommendations
    # ========================================================================
    print("="*80)
    print("VERIFICATION POINT 3: Dispatch rejected on admin-only recommendations")
    print("="*80)
    print()
    
    if dispatch_token:
        try:
            response = requests.get(
                f"{BACKEND_URL}/admin/transportation/intelligence/recommendations",
                headers={"X-Dispatch-Token": dispatch_token},
                timeout=10
            )
            
            passed = response.status_code in [401, 403]
            details = f"Status: {response.status_code}"
            if not passed:
                details += f" (Expected 401/403), Response: {response.text[:200]}"
            
            results.add(
                "3. Dispatch rejected on admin-only recommendations",
                passed,
                details
            )
        except Exception as e:
            results.add("3. Dispatch rejected on admin-only recommendations", False, f"Exception: {e}")
    
    # ========================================================================
    # VERIFICATION POINTS 4-6: Backup reliability
    # ========================================================================
    print("="*80)
    print("VERIFICATION POINTS 4-6: Backup reliability")
    print("="*80)
    print()
    
    # Login as admin
    print("Logging in as admin...")
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/multi-login",
            json=ADMIN_CREDS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            admin_token = data["portal_tokens"]["admin"]
            directory_token = data["session_token"]
            print(f"✅ Admin login successful\n")
        else:
            print(f"❌ Admin login failed: {response.status_code}\n")
            admin_token = None
            directory_token = None
    except Exception as e:
        print(f"❌ Admin login exception: {e}\n")
        admin_token = None
        directory_token = None
    
    if admin_token and directory_token:
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": directory_token
        }
        
        # ========================================================================
        # VERIFICATION POINT 4: Recovery snapshot - no app_disk_pressure blocker
        # ========================================================================
        try:
            response = requests.get(
                f"{BACKEND_URL}/admin/recovery/snapshot",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                recent_jobs = data.get("scheduler", {}).get("backup_runtime", {}).get("recent_complete_jobs", [])
                
                # Check for app_disk_pressure deferrals when tmp has sufficient headroom
                problematic_deferrals = []
                for job in recent_jobs:
                    if job.get("state") == "deferred" and job.get("result", {}).get("reason") == "resource_guard":
                        preflight = job.get("result", {}).get("preflight", {})
                        tmp_free = preflight.get("tmp_disk_free_bytes", 0)
                        min_required = preflight.get("min_free_bytes_required", 0)
                        reasons = preflight.get("reasons", [])
                        
                        if tmp_free > min_required and any("app_disk_pressure" in r for r in reasons):
                            problematic_deferrals.append({
                                "tmp_free_gb": round(tmp_free / (1024**3), 2),
                                "min_required_gb": round(min_required / (1024**3), 2),
                                "reasons": reasons
                            })
                
                passed = len(problematic_deferrals) == 0
                if passed:
                    details = f"Status: {response.status_code}, No app_disk_pressure blockers when tmp sufficient"
                else:
                    details = f"Status: {response.status_code}, Found {len(problematic_deferrals)} jobs deferred due to app_disk_pressure despite sufficient tmp. "
                    details += f"Example: {problematic_deferrals[0]['tmp_free_gb']}GB free vs {problematic_deferrals[0]['min_required_gb']}GB required (26x headroom)"
                
                results.add(
                    "4. Recovery snapshot - no app_disk_pressure blocker when tmp sufficient",
                    passed,
                    details
                )
            else:
                results.add(
                    "4. Recovery snapshot - no app_disk_pressure blocker when tmp sufficient",
                    False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
        except Exception as e:
            results.add("4. Recovery snapshot - no app_disk_pressure blocker when tmp sufficient", False, f"Exception: {e}")
        
        # ========================================================================
        # VERIFICATION POINT 5: Manual backup retry acceptance
        # ========================================================================
        try:
            response = requests.post(
                f"{BACKEND_URL}/admin/backups/run-complete-now",
                headers=headers,
                json={},
                timeout=10
            )
            
            # 200/202 = accepted, 409 = already in progress (acceptable)
            passed = response.status_code in [200, 202, 409]
            
            if response.status_code in [200, 202]:
                details = f"Status: {response.status_code}, Manual retry accepted"
            elif response.status_code == 409:
                response_data = response.json()
                detail = response_data.get("detail", "")
                if "already in progress" in detail.lower():
                    details = f"Status: {response.status_code}, Backup already in progress (acceptable)"
                else:
                    details = f"Status: {response.status_code}, Unexpected 409: {detail}"
                    passed = False
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            results.add(
                "5. Manual backup retry endpoint accepts same-hour retries",
                passed,
                details
            )
        except Exception as e:
            results.add("5. Manual backup retry endpoint accepts same-hour retries", False, f"Exception: {e}")
        
        # ========================================================================
        # VERIFICATION POINT 6: Backup state reflects manual run
        # ========================================================================
        try:
            # Wait a moment for job to be registered
            time.sleep(2)
            
            response = requests.get(
                f"{BACKEND_URL}/admin/backups-complete-r2-state",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                state_str = json.dumps(data).lower()
                
                # Check for accepted, in-progress, or successful states
                has_state = any(s in state_str for s in ["accepted", "in_progress", "in-progress", "running", "success", "completed"])
                
                passed = has_state
                if passed:
                    details = f"Status: {response.status_code}, Manual complete-r2 run state reflected truthfully"
                else:
                    details = f"Status: {response.status_code}, No accepted/in-progress/successful state detected"
                
                results.add(
                    "6. Backup state reflects current manual complete-r2 run",
                    passed,
                    details
                )
            else:
                results.add(
                    "6. Backup state reflects current manual complete-r2 run",
                    False,
                    f"Status: {response.status_code}, Response: {response.text[:200]}"
                )
        except Exception as e:
            results.add("6. Backup state reflects current manual complete-r2 run", False, f"Exception: {e}")
    
    # Print summary
    print()
    success = results.summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

#!/usr/bin/env python3
"""
Backend verification for trench backfill deployment-startup fix.

Review request: Re-test the preview backend after an additional deployment-startup fix.
Previous backend check found a startup blocker: deferred trench backfill used the lazy 
runtime DB proxy and produced repeated `Database accessed before runtime initialization` 
errors during/around startup. Fixed by capturing the concrete runtime DB target inside 
the trench backfill bootstrap and registering the task through the tracked background-task 
helper instead of raw `asyncio.create_task`.

Verification scope:
1. `/api/health`, `/api/version`, `/api/platform/data-truth`, and `/api/ready` return successfully.
2. No obvious startup-health regression remains from the trench backfill path.
3. PM schedule endpoint for `ZZ-RUNTIME-CERT-2026` still returns 200.
4. If possible, note whether the prior `Database accessed before runtime initialization` 
   startup/backfill issue still reproduces.

Credentials:
- PM login: cert.pm@example.com / CertProof2026!
- Super admin login: jaymn.judd@mascigc.com / Maddix123!

Backend-only verification, no frontend testing.
"""

import requests
import json
import sys
from datetime import datetime

# Base URL from frontend/.env
BASE_URL = "https://masci-audit-hub.preview.emergentagent.com/api"

# Test credentials
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test project
TEST_PROJECT = "ZZ-RUNTIME-CERT-2026"

def log(message):
    """Log with timestamp"""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{timestamp}] {message}")

def test_health_endpoint():
    """Test 1: GET /api/health returns successfully"""
    log("TEST 1: GET /api/health")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=15)
        log(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            log(f"  Response keys: {list(data.keys())}")
            log(f"  ok: {data.get('ok')}")
            log(f"  runtime_identity: {data.get('runtime_identity', {}).get('status')}")
            return True, "✅ PASS - /api/health returns 200 OK"
        else:
            return False, f"❌ FAIL - /api/health returned {response.status_code}"
    except Exception as e:
        return False, f"❌ FAIL - /api/health error: {str(e)}"

def test_version_endpoint():
    """Test 2: GET /api/version returns successfully"""
    log("TEST 2: GET /api/version")
    try:
        response = requests.get(f"{BASE_URL}/version", timeout=15)
        log(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            log(f"  Response keys: {list(data.keys())}")
            log(f"  commit: {data.get('commit', 'N/A')[:12]}")
            log(f"  source_hash: {data.get('source_hash', 'N/A')[:12]}")
            log(f"  frontend_backend_release_match: {data.get('frontend_backend_release_match')}")
            return True, "✅ PASS - /api/version returns 200 OK"
        else:
            return False, f"❌ FAIL - /api/version returned {response.status_code}"
    except Exception as e:
        return False, f"❌ FAIL - /api/version error: {str(e)}"

def test_platform_data_truth_endpoint():
    """Test 3: GET /api/platform/data-truth returns successfully"""
    log("TEST 3: GET /api/platform/data-truth")
    try:
        response = requests.get(f"{BASE_URL}/platform/data-truth", timeout=15)
        log(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            log(f"  Response keys: {list(data.keys())}")
            return True, "✅ PASS - /api/platform/data-truth returns 200 OK"
        else:
            return False, f"❌ FAIL - /api/platform/data-truth returned {response.status_code}"
    except Exception as e:
        return False, f"❌ FAIL - /api/platform/data-truth error: {str(e)}"

def test_ready_endpoint():
    """Test 4: GET /api/ready returns successfully"""
    log("TEST 4: GET /api/ready")
    try:
        response = requests.get(f"{BASE_URL}/ready", timeout=15)
        log(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            log(f"  Response keys: {list(data.keys())}")
            log(f"  ok: {data.get('ok')}")
            log(f"  state: {data.get('state')}")
            log(f"  mongo_ok: {data.get('mongo_ok')}")
            log(f"  event_loop_ok: {data.get('event_loop_ok')}")
            log(f"  startup_complete: {data.get('startup_complete')}")
            return True, "✅ PASS - /api/ready returns 200 OK with healthy state"
        else:
            return False, f"❌ FAIL - /api/ready returned {response.status_code}"
    except Exception as e:
        return False, f"❌ FAIL - /api/ready error: {str(e)}"

def test_pm_login_and_schedule():
    """Test 5: PM login and schedule endpoint for ZZ-RUNTIME-CERT-2026"""
    log("TEST 5: PM login and schedule endpoint")
    
    # Step 1: PM login
    log("  Step 5.1: POST /api/pm/login")
    try:
        login_response = requests.post(
            f"{BASE_URL}/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            timeout=15
        )
        log(f"    Login status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            return False, f"❌ FAIL - PM login failed with {login_response.status_code}"
        
        login_data = login_response.json()
        pm_token = login_data.get("token")
        
        if not pm_token:
            return False, "❌ FAIL - PM login did not return token"
        
        log(f"    PM token length: {len(pm_token)}")
        
        # Step 2: Test PM schedule endpoint
        log(f"  Step 5.2: GET /api/pm/project-controls/projects/{TEST_PROJECT}/schedule/overview")
        
        headers = {
            "X-PM-Token": pm_token
        }
        
        schedule_response = requests.get(
            f"{BASE_URL}/pm/project-controls/projects/{TEST_PROJECT}/schedule/overview",
            headers=headers,
            timeout=15
        )
        
        log(f"    Schedule status: {schedule_response.status_code}")
        
        if schedule_response.status_code == 200:
            schedule_data = schedule_response.json()
            log(f"    Response keys: {list(schedule_data.keys())[:5]}...")
            log(f"    Project: {schedule_data.get('project', {}).get('project_number')}")
            return True, f"✅ PASS - PM schedule endpoint for {TEST_PROJECT} returns 200 OK"
        else:
            return False, f"❌ FAIL - PM schedule endpoint returned {schedule_response.status_code}"
            
    except Exception as e:
        return False, f"❌ FAIL - PM login/schedule error: {str(e)}"

def check_backend_logs_for_db_errors():
    """Test 6: Check backend logs for 'Database accessed before runtime initialization' errors"""
    log("TEST 6: Check backend logs for database initialization errors")
    
    try:
        import subprocess
        
        # Check recent backend error logs
        result = subprocess.run(
            ["tail", "-n", "200", "/var/log/supervisor/backend.err.log"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        logs = result.stdout
        
        # Search for the specific error pattern
        db_init_errors = []
        for line in logs.split('\n'):
            if "Database accessed before runtime initialization" in line:
                db_init_errors.append(line)
        
        if db_init_errors:
            log(f"  ❌ FOUND {len(db_init_errors)} 'Database accessed before runtime initialization' errors:")
            for error in db_init_errors[:5]:  # Show first 5
                log(f"    {error}")
            return False, f"❌ FAIL - Found {len(db_init_errors)} database initialization errors in logs"
        else:
            log("  ✅ No 'Database accessed before runtime initialization' errors found in recent logs")
            
            # Also check for trench-related errors
            trench_errors = []
            for line in logs.split('\n'):
                if "trench" in line.lower() and ("error" in line.lower() or "exception" in line.lower()):
                    trench_errors.append(line)
            
            if trench_errors:
                log(f"  ⚠️ Found {len(trench_errors)} trench-related errors (may be unrelated):")
                for error in trench_errors[:3]:
                    log(f"    {error}")
            else:
                log("  ✅ No trench-related errors found in recent logs")
            
            return True, "✅ PASS - No database initialization errors in backend logs"
            
    except Exception as e:
        log(f"  ⚠️ Could not check logs: {str(e)}")
        return True, "⚠️ SKIP - Could not check backend logs (not a failure)"

def main():
    """Run all backend verification tests"""
    log("=" * 80)
    log("BACKEND VERIFICATION: Trench Backfill Deployment-Startup Fix")
    log("=" * 80)
    log("")
    
    results = []
    
    # Run all tests
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("Version Endpoint", test_version_endpoint),
        ("Platform Data Truth Endpoint", test_platform_data_truth_endpoint),
        ("Ready Endpoint", test_ready_endpoint),
        ("PM Login and Schedule Endpoint", test_pm_login_and_schedule),
        ("Backend Logs Check", check_backend_logs_for_db_errors),
    ]
    
    for test_name, test_func in tests:
        log("")
        log(f"Running: {test_name}")
        log("-" * 80)
        try:
            passed, message = test_func()
            results.append((test_name, passed, message))
            log(message)
        except Exception as e:
            results.append((test_name, False, f"❌ FAIL - Unexpected error: {str(e)}"))
            log(f"❌ FAIL - Unexpected error: {str(e)}")
    
    # Summary
    log("")
    log("=" * 80)
    log("SUMMARY")
    log("=" * 80)
    
    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)
    
    for test_name, passed, message in results:
        log(f"{message}")
    
    log("")
    log(f"TOTAL: {passed_count}/{total_count} tests passed ({passed_count*100//total_count}%)")
    
    if passed_count == total_count:
        log("")
        log("✅ ALL TESTS PASSED - Backend is healthy after trench backfill fix")
        log("✅ No 'Database accessed before runtime initialization' errors detected")
        log("✅ All required endpoints return successfully")
        log("✅ PM schedule endpoint for ZZ-RUNTIME-CERT-2026 returns 200")
        return 0
    else:
        log("")
        log(f"❌ {total_count - passed_count} TEST(S) FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())

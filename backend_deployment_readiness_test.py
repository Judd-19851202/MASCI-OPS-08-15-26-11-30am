#!/usr/bin/env python3
"""
Backend Deployment Readiness Test - Post Startup-Latency Fixes
Focus: Verify deployment readiness, not feature depth
Context: Production deploy logs showed nginx /health checks failing before uvicorn bound port 8001
Main agent changed backend startup orchestration for fast-startup
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://masci-audit-hub.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials from /app/memory/test_credentials.md
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test project
TEST_PROJECT = "ZZ-RUNTIME-CERT-2026"

def log_test(test_name, status, details=""):
    """Log test result"""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{symbol} [{timestamp}] {test_name}: {status}")
    if details:
        print(f"   {details}")
    return status == "PASS"

def test_health_endpoint():
    """Test 1: /api/health endpoint returns successfully"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                return log_test("Health Endpoint", "PASS", f"Status: {response.status_code}, ok={data.get('ok')}")
            else:
                return log_test("Health Endpoint", "FAIL", f"ok=False in response: {data}")
        else:
            return log_test("Health Endpoint", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        return log_test("Health Endpoint", "FAIL", f"Exception: {str(e)}")

def test_version_endpoint():
    """Test 2: /api/version endpoint returns successfully"""
    try:
        response = requests.get(f"{API_BASE}/version", timeout=15)
        if response.status_code == 200:
            data = response.json()
            commit = data.get("commit", "unknown")[:8]
            return log_test("Version Endpoint", "PASS", f"Status: {response.status_code}, commit={commit}")
        else:
            return log_test("Version Endpoint", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        return log_test("Version Endpoint", "FAIL", f"Exception: {str(e)}")

def test_platform_data_truth():
    """Test 3: /api/platform/data-truth endpoint returns successfully"""
    try:
        response = requests.get(f"{API_BASE}/platform/data-truth", timeout=15)
        if response.status_code == 200:
            data = response.json()
            return log_test("Platform Data-Truth Endpoint", "PASS", f"Status: {response.status_code}")
        else:
            return log_test("Platform Data-Truth Endpoint", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        return log_test("Platform Data-Truth Endpoint", "FAIL", f"Exception: {str(e)}")

def test_backend_startup_health():
    """Test 4: Backend import/startup remains healthy (check /api/ready)"""
    try:
        response = requests.get(f"{API_BASE}/ready", timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and data.get("state") == "ready":
                startup_complete = data.get("startup_complete", False)
                mongo_ok = data.get("mongo_ok", False)
                return log_test("Backend Startup Health", "PASS", 
                              f"State: {data.get('state')}, startup_complete={startup_complete}, mongo_ok={mongo_ok}")
            else:
                return log_test("Backend Startup Health", "FAIL", f"Not ready: {data}")
        else:
            return log_test("Backend Startup Health", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        return log_test("Backend Startup Health", "FAIL", f"Exception: {str(e)}")

def test_pm_schedule_endpoint():
    """Test 5: PM schedule endpoint for ZZ-RUNTIME-CERT-2026 returns 200"""
    try:
        # First login as PM
        login_response = requests.post(
            f"{API_BASE}/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            timeout=15
        )
        
        if login_response.status_code != 200:
            return log_test("PM Schedule Endpoint", "FAIL", f"PM login failed: {login_response.status_code}")
        
        pm_token = login_response.json().get("token")
        if not pm_token:
            return log_test("PM Schedule Endpoint", "FAIL", "No PM token in login response")
        
        # Test PM schedule overview endpoint
        headers = {"X-PM-Token": pm_token}
        schedule_response = requests.get(
            f"{API_BASE}/pm/project-controls/projects/{TEST_PROJECT}/schedule/overview",
            headers=headers,
            timeout=15
        )
        
        if schedule_response.status_code == 200:
            return log_test("PM Schedule Endpoint", "PASS", 
                          f"Status: {schedule_response.status_code} for project {TEST_PROJECT}")
        else:
            return log_test("PM Schedule Endpoint", "FAIL", 
                          f"Status: {schedule_response.status_code}")
    except Exception as e:
        return log_test("PM Schedule Endpoint", "FAIL", f"Exception: {str(e)}")

def test_pm_operational_intelligence():
    """Test 6: PM operational-intelligence endpoint for ZZ-RUNTIME-CERT-2026 returns 200"""
    try:
        # Login as PM
        login_response = requests.post(
            f"{API_BASE}/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            timeout=15
        )
        
        if login_response.status_code != 200:
            return log_test("PM Operational Intelligence", "FAIL", f"PM login failed: {login_response.status_code}")
        
        pm_token = login_response.json().get("token")
        if not pm_token:
            return log_test("PM Operational Intelligence", "FAIL", "No PM token in login response")
        
        # Test PM operational intelligence endpoint
        headers = {"X-PM-Token": pm_token}
        intel_response = requests.get(
            f"{API_BASE}/pm/project-controls/projects/{TEST_PROJECT}/operational-intelligence",
            headers=headers,
            timeout=15
        )
        
        if intel_response.status_code == 200:
            return log_test("PM Operational Intelligence", "PASS", 
                          f"Status: {intel_response.status_code} for project {TEST_PROJECT}")
        else:
            return log_test("PM Operational Intelligence", "FAIL", 
                          f"Status: {intel_response.status_code}")
    except Exception as e:
        return log_test("PM Operational Intelligence", "FAIL", f"Exception: {str(e)}")

def check_backend_logs():
    """Check backend logs for startup errors"""
    try:
        import subprocess
        result = subprocess.run(
            ["tail", "-n", "100", "/var/log/supervisor/backend.err.log"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        error_log = result.stdout
        
        # Check for critical errors
        critical_errors = []
        if "Connection refused" in error_log:
            critical_errors.append("Connection refused errors found")
        if "failed to bind" in error_log.lower():
            critical_errors.append("Port binding failures found")
        if "ImportError" in error_log:
            critical_errors.append("Import errors found")
        if "ModuleNotFoundError" in error_log:
            critical_errors.append("Module not found errors")
        
        if critical_errors:
            return log_test("Backend Error Logs", "FAIL", f"Critical errors: {', '.join(critical_errors)}")
        else:
            return log_test("Backend Error Logs", "PASS", "No critical startup errors in recent logs")
    except Exception as e:
        return log_test("Backend Error Logs", "WARN", f"Could not check logs: {str(e)}")

def main():
    """Run all deployment readiness tests"""
    print("=" * 80)
    print("BACKEND DEPLOYMENT READINESS TEST - POST STARTUP-LATENCY FIXES")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Project: {TEST_PROJECT}")
    print("=" * 80)
    print()
    
    results = []
    
    # Test 1: Health endpoint
    results.append(test_health_endpoint())
    
    # Test 2: Version endpoint
    results.append(test_version_endpoint())
    
    # Test 3: Platform data-truth endpoint
    results.append(test_platform_data_truth())
    
    # Test 4: Backend startup health
    results.append(test_backend_startup_health())
    
    # Test 5: PM schedule endpoint
    results.append(test_pm_schedule_endpoint())
    
    # Test 6: PM operational intelligence
    results.append(test_pm_operational_intelligence())
    
    # Test 7: Check backend logs
    results.append(check_backend_logs())
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("✅ ALL TESTS PASSED - Backend deployment readiness verified")
        return 0
    else:
        print(f"❌ {total - passed} TEST(S) FAILED - Backend has issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())

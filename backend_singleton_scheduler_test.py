#!/usr/bin/env python3
"""
Backend Singleton Scheduler Fix Verification
Re-test after second deployment-startup fix for lib/singleton_scheduler.run_with_singleton_lock()
"""

import requests
import json
from datetime import datetime

# Backend URL from frontend/.env
BASE_URL = "https://masci-audit-hub.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test project
PROJECT_NUMBER = "ZZ-RUNTIME-CERT-2026"

def test_health_endpoint():
    """Test 1: /api/health returns successfully"""
    print("\n" + "="*80)
    print("TEST 1: GET /api/health")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("✅ PASS - Health endpoint returns 200 OK")
            return True
        else:
            print(f"❌ FAIL - Health endpoint returned {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ FAIL - Health endpoint error: {e}")
        return False

def test_version_endpoint():
    """Test 2: /api/version returns successfully"""
    print("\n" + "="*80)
    print("TEST 2: GET /api/version")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/version", timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("✅ PASS - Version endpoint returns 200 OK")
            return True
        else:
            print(f"❌ FAIL - Version endpoint returned {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ FAIL - Version endpoint error: {e}")
        return False

def test_platform_data_truth_endpoint():
    """Test 3: /api/platform/data-truth returns successfully"""
    print("\n" + "="*80)
    print("TEST 3: GET /api/platform/data-truth")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/platform/data-truth", timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            print(f"Response length: {len(json.dumps(data))} chars")
            print("✅ PASS - Platform data-truth endpoint returns 200 OK")
            return True
        else:
            print(f"❌ FAIL - Platform data-truth endpoint returned {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"❌ FAIL - Platform data-truth endpoint error: {e}")
        return False

def test_ready_endpoint():
    """Test 4: /api/ready returns successfully"""
    print("\n" + "="*80)
    print("TEST 4: GET /api/ready")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/ready", timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("✅ PASS - Ready endpoint returns 200 OK")
            return True
        else:
            print(f"❌ FAIL - Ready endpoint returned {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ FAIL - Ready endpoint error: {e}")
        return False

def test_pm_schedule_endpoint():
    """Test 5: PM schedule endpoint for ZZ-RUNTIME-CERT-2026 returns 200"""
    print("\n" + "="*80)
    print(f"TEST 5: PM Schedule Endpoint for {PROJECT_NUMBER}")
    print("="*80)
    
    try:
        # First, login as PM
        print(f"Logging in as PM: {PM_EMAIL}")
        login_response = requests.post(
            f"{BASE_URL}/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            timeout=15
        )
        
        if login_response.status_code != 200:
            print(f"❌ FAIL - PM login failed with status {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
        
        login_data = login_response.json()
        pm_token = login_data.get("token")
        
        if not pm_token:
            print(f"❌ FAIL - No PM token in login response")
            return False
        
        print(f"✅ PM login successful, token length: {len(pm_token)}")
        
        # Now test the PM schedule endpoint
        schedule_url = f"{BASE_URL}/pm/project-controls/projects/{PROJECT_NUMBER}/schedule/overview"
        print(f"Testing: GET {schedule_url}")
        
        headers = {"X-PM-Token": pm_token}
        schedule_response = requests.get(schedule_url, headers=headers, timeout=15)
        
        print(f"Status Code: {schedule_response.status_code}")
        
        if schedule_response.status_code == 200:
            data = schedule_response.json()
            print(f"Response keys: {list(data.keys())}")
            print(f"Project: {data.get('project', {}).get('project_number', 'N/A')}")
            print("✅ PASS - PM schedule endpoint returns 200 OK")
            return True
        else:
            print(f"❌ FAIL - PM schedule endpoint returned {schedule_response.status_code}")
            print(f"Response: {schedule_response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - PM schedule endpoint error: {e}")
        return False

def main():
    """Run all backend verification tests"""
    print("\n" + "="*80)
    print("BACKEND SINGLETON SCHEDULER FIX VERIFICATION")
    print("Re-test after second deployment-startup fix")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print("="*80)
    
    results = []
    
    # Test 1: Health endpoint
    results.append(("Health endpoint", test_health_endpoint()))
    
    # Test 2: Version endpoint
    results.append(("Version endpoint", test_version_endpoint()))
    
    # Test 3: Platform data-truth endpoint
    results.append(("Platform data-truth endpoint", test_platform_data_truth_endpoint()))
    
    # Test 4: Ready endpoint
    results.append(("Ready endpoint", test_ready_endpoint()))
    
    # Test 5: PM schedule endpoint
    results.append(("PM schedule endpoint", test_pm_schedule_endpoint()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - Backend endpoints are healthy")
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED - Backend has issues")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

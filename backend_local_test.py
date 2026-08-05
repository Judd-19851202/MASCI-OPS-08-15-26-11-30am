#!/usr/bin/env python3
"""
Backend Singleton Scheduler Fix Verification - Local Testing
Re-test after second deployment-startup fix for lib/singleton_scheduler.run_with_singleton_lock()
"""

import requests
import json
from datetime import datetime

# Local backend URL
BASE_URL = "http://localhost:8001/api"

# Test credentials
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
PROJECT_NUMBER = "ZZ-RUNTIME-CERT-2026"

def test_endpoint(name, url, headers=None):
    """Generic endpoint test"""
    print(f"\n{'='*80}")
    print(f"TEST: GET {url}")
    print('='*80)
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'array'}")
                if isinstance(data, dict):
                    for key in ['ok', 'state', 'commit', 'service']:
                        if key in data:
                            print(f"  {key}: {data[key]}")
                print(f"✅ PASS - {name} returns 200 OK")
                return True, data
            except:
                print(f"Response (non-JSON): {response.text[:200]}")
                print(f"✅ PASS - {name} returns 200 OK")
                return True, response.text
        else:
            print(f"❌ FAIL - {name} returned {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False, None
    except Exception as e:
        print(f"❌ FAIL - {name} error: {e}")
        return False, None

def main():
    print("\n" + "="*80)
    print("BACKEND SINGLETON SCHEDULER FIX VERIFICATION - LOCAL")
    print("Re-test after second deployment-startup fix")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print("="*80)
    
    results = []
    
    # Test 1: Health
    success, _ = test_endpoint("Health", f"{BASE_URL}/health")
    results.append(("Health", success))
    
    # Test 2: Version
    success, _ = test_endpoint("Version", f"{BASE_URL}/version")
    results.append(("Version", success))
    
    # Test 3: Platform data-truth
    success, _ = test_endpoint("Platform data-truth", f"{BASE_URL}/platform/data-truth")
    results.append(("Platform data-truth", success))
    
    # Test 4: Ready
    success, _ = test_endpoint("Ready", f"{BASE_URL}/ready")
    results.append(("Ready", success))
    
    # Test 5: PM schedule endpoint
    print(f"\n{'='*80}")
    print(f"TEST: PM Schedule for {PROJECT_NUMBER}")
    print('='*80)
    
    try:
        # Login as PM
        print(f"Logging in as PM: {PM_EMAIL}")
        login_resp = requests.post(
            f"{BASE_URL}/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            timeout=10
        )
        
        if login_resp.status_code == 200:
            token = login_resp.json().get("token")
            print(f"✅ PM login successful, token length: {len(token)}")
            
            # Test schedule endpoint
            schedule_url = f"{BASE_URL}/pm/project-controls/projects/{PROJECT_NUMBER}/schedule/overview"
            headers = {"X-PM-Token": token}
            
            schedule_resp = requests.get(schedule_url, headers=headers, timeout=10)
            print(f"Status Code: {schedule_resp.status_code}")
            
            if schedule_resp.status_code == 200:
                data = schedule_resp.json()
                print(f"Response keys: {list(data.keys())}")
                print(f"Project: {data.get('project', {}).get('project_number', 'N/A')}")
                print(f"✅ PASS - PM schedule endpoint returns 200 OK")
                results.append(("PM schedule", True))
            else:
                print(f"❌ FAIL - PM schedule returned {schedule_resp.status_code}")
                results.append(("PM schedule", False))
        else:
            print(f"❌ FAIL - PM login failed: {login_resp.status_code}")
            results.append(("PM schedule", False))
    except Exception as e:
        print(f"❌ FAIL - PM schedule error: {e}")
        results.append(("PM schedule", False))
    
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
        print("\n✅ ALL TESTS PASSED")
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

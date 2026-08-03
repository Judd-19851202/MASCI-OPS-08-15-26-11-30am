#!/usr/bin/env python3
"""
Backend Documentation Regression Smoke Test
============================================

CONTEXT: Documentation-only changes were made (no backend code changes).
This is a lightweight smoke test to confirm the backend still responds
and no obvious regression is present before closeout.

SCOPE: Test safe, unauthenticated backend smoke endpoints:
1. GET /api/health - basic health check
2. GET /api/version - version info
3. GET /api/ready - readiness check

NO CREDENTIALS REQUIRED OR PROVIDED.
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://masci-audit-hub.preview.emergentagent.com"
TIMEOUT = 15

def test_health_endpoint():
    """Test GET /api/health - basic health check (unauthenticated)"""
    print("\n" + "="*80)
    print("TEST 1: GET /api/health - Basic Health Check")
    print("="*80)
    
    try:
        url = f"{BASE_URL}/api/health"
        print(f"Request: GET {url}")
        
        response = requests.get(url, timeout=TIMEOUT)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check for expected fields
            if data.get('ok') is True:
                print("✅ PASS: Health endpoint returns ok=true")
                return True
            else:
                print(f"❌ FAIL: Health endpoint returned ok={data.get('ok')}")
                return False
        else:
            print(f"❌ FAIL: Health endpoint returned {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False

def test_version_endpoint():
    """Test GET /api/version - version info (unauthenticated)"""
    print("\n" + "="*80)
    print("TEST 2: GET /api/version - Version Info")
    print("="*80)
    
    try:
        url = f"{BASE_URL}/api/version"
        print(f"Request: GET {url}")
        
        response = requests.get(url, timeout=TIMEOUT)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check for expected fields
            if 'commit' in data and 'service' in data:
                print(f"✅ PASS: Version endpoint returns commit={data.get('commit')}, service={data.get('service')}")
                return True
            else:
                print(f"❌ FAIL: Version endpoint missing expected fields")
                return False
        else:
            print(f"❌ FAIL: Version endpoint returned {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False

def test_ready_endpoint():
    """Test GET /api/ready - readiness check (unauthenticated)"""
    print("\n" + "="*80)
    print("TEST 3: GET /api/ready - Readiness Check")
    print("="*80)
    
    try:
        url = f"{BASE_URL}/api/ready"
        print(f"Request: GET {url}")
        
        response = requests.get(url, timeout=TIMEOUT)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check for expected fields
            if data.get('ok') is True and data.get('state') == 'ready':
                print("✅ PASS: Ready endpoint returns ok=true, state=ready")
                return True
            else:
                print(f"❌ FAIL: Ready endpoint returned ok={data.get('ok')}, state={data.get('state')}")
                return False
        else:
            print(f"❌ FAIL: Ready endpoint returned {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False

def main():
    """Run all backend documentation regression smoke tests"""
    print("="*80)
    print("BACKEND DOCUMENTATION REGRESSION SMOKE TEST")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print(f"Context: Documentation-only changes (no backend code changes)")
    print(f"Goal: Confirm backend still responds, no obvious regression")
    print("="*80)
    
    results = {
        'test_health': test_health_endpoint(),
        'test_version': test_version_endpoint(),
        'test_ready': test_ready_endpoint()
    }
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - Backend is responding correctly")
        print("No obvious regression detected after documentation changes")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED - Backend regression detected")
        return 1

if __name__ == "__main__":
    exit(main())

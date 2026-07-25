#!/usr/bin/env python3
"""
BCSS Checkpoint 3 - Light Backend No-Regression Validation
Documentation-only checkpoint - verify no backend runtime breakage
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://backup-forensics.preview.emergentagent.com"

def test_health_endpoint():
    """Test 1: GET /api/health returns 200 and ok=true"""
    print("\n=== TEST 1: GET /api/health ===")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if data.get("ok") is True:
                print("✅ PASS: /api/health returns 200 and ok=true")
                return True, "Health endpoint working correctly"
            else:
                print(f"❌ FAIL: ok={data.get('ok')}, expected True")
                return False, f"Health endpoint returned ok={data.get('ok')}"
        else:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            return False, f"Health endpoint returned {response.status_code}"
            
    except Exception as e:
        print(f"❌ FAIL: Exception - {str(e)}")
        return False, f"Health endpoint error: {str(e)}"

def test_version_endpoint():
    """Test 2 (Optional): GET /api/version for additional validation"""
    print("\n=== TEST 2: GET /api/version (Optional) ===")
    try:
        response = requests.get(f"{BASE_URL}/api/version", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("✅ PASS: /api/version accessible")
            return True, "Version endpoint working correctly"
        else:
            print(f"⚠️ WARNING: Expected 200, got {response.status_code}")
            return False, f"Version endpoint returned {response.status_code}"
            
    except Exception as e:
        print(f"⚠️ WARNING: Exception - {str(e)}")
        return False, f"Version endpoint error: {str(e)}"

def test_health_full_endpoint():
    """Test 3 (Optional): GET /api/health/full for comprehensive health check"""
    print("\n=== TEST 3: GET /api/health/full (Optional) ===")
    try:
        response = requests.get(f"{BASE_URL}/api/health/full", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if data.get("ok") is True:
                print("✅ PASS: /api/health/full returns 200 and ok=true")
                return True, "Full health endpoint working correctly"
            else:
                print(f"⚠️ WARNING: ok={data.get('ok')}, expected True")
                return False, f"Full health endpoint returned ok={data.get('ok')}"
        else:
            print(f"⚠️ WARNING: Expected 200, got {response.status_code}")
            return False, f"Full health endpoint returned {response.status_code}"
            
    except Exception as e:
        print(f"⚠️ WARNING: Exception - {str(e)}")
        return False, f"Full health endpoint error: {str(e)}"

def main():
    print("=" * 80)
    print("BCSS CHECKPOINT 3 - LIGHT BACKEND NO-REGRESSION VALIDATION")
    print("Documentation-only checkpoint - smoke test only")
    print(f"Target: {BASE_URL}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print("=" * 80)
    
    results = []
    
    # Test 1: Mandatory health check
    health_pass, health_msg = test_health_endpoint()
    results.append(("GET /api/health", health_pass, health_msg))
    
    # Test 2: Optional version check
    version_pass, version_msg = test_version_endpoint()
    results.append(("GET /api/version", version_pass, version_msg))
    
    # Test 3: Optional full health check
    health_full_pass, health_full_msg = test_health_full_endpoint()
    results.append(("GET /api/health/full", health_full_pass, health_full_msg))
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, p, _ in results if p)
    total = len(results)
    
    for test_name, passed_flag, message in results:
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    # Final verdict
    print("\n" + "=" * 80)
    print("FINAL VERDICT")
    print("=" * 80)
    
    # For documentation-only checkpoint, we only require /api/health to pass
    if results[0][1]:  # health endpoint passed
        print("✅ PASS - No backend regression detected")
        print("Documentation-only BCSS Checkpoint 3 validation complete")
        print("Backend health endpoint working correctly")
        return 0
    else:
        print("❌ FAIL - Backend regression detected")
        print("Health endpoint not working correctly")
        return 1

if __name__ == "__main__":
    exit(main())

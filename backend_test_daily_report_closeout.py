#!/usr/bin/env python3
"""
Backend-only verification for Daily Report release cleanup closeout.
Tests stability smoke checks and confirms backend remains responsive.
"""
import requests
import time
import sys

BASE_URL = "https://backup-forensics.preview.emergentagent.com"
API_URL = f"{BASE_URL}/api"

def test_stability_smoke():
    """Test basic stability: health, version, daily-reports endpoints."""
    print("\n=== STABILITY SMOKE TESTS ===")
    
    # Test 1: GET /health
    print("\n1. Testing GET /health...")
    try:
        start = time.time()
        resp = requests.get(f"{API_URL}/health", timeout=10)
        elapsed = time.time() - start
        print(f"   Status: {resp.status_code}, Time: {elapsed:.2f}s")
        if resp.status_code == 200:
            print(f"   Response: {resp.json()}")
            print("   ✓ PASS: /health responds immediately")
        else:
            print(f"   ✗ FAIL: Expected 200, got {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ FAIL: Exception - {e}")
        return False
    
    # Test 2: GET /api/version
    print("\n2. Testing GET /api/version...")
    try:
        start = time.time()
        resp = requests.get(f"{API_URL}/version", timeout=10)
        elapsed = time.time() - start
        print(f"   Status: {resp.status_code}, Time: {elapsed:.2f}s")
        if resp.status_code == 200:
            data = resp.json()
            print(f"   Commit: {data.get('commit', 'N/A')}")
            print(f"   Source hash: {data.get('source_hash', 'N/A')}")
            print("   ✓ PASS: /api/version responds immediately")
        else:
            print(f"   ✗ FAIL: Expected 200, got {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ FAIL: Exception - {e}")
        return False
    
    # Test 3: GET /api/daily-reports?limit=1 (401 acceptable without auth)
    print("\n3. Testing GET /api/daily-reports?limit=1 (without auth)...")
    try:
        start = time.time()
        resp = requests.get(f"{API_URL}/daily-reports?limit=1", timeout=10)
        elapsed = time.time() - start
        print(f"   Status: {resp.status_code}, Time: {elapsed:.2f}s")
        if resp.status_code in [200, 401]:
            print(f"   ✓ PASS: /api/daily-reports responds immediately (401 acceptable without auth)")
        else:
            print(f"   ✗ FAIL: Expected 200 or 401, got {resp.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ FAIL: Exception - {e}")
        return False
    
    return True

def test_repeated_polling():
    """Test backend remains responsive during repeated polling."""
    print("\n=== REPEATED POLLING TEST ===")
    print("Testing 10 rapid requests to /health to confirm no timeout/hang...")
    
    all_passed = True
    for i in range(10):
        try:
            start = time.time()
            resp = requests.get(f"{API_URL}/health", timeout=10)
            elapsed = time.time() - start
            if resp.status_code == 200 and elapsed < 5.0:
                print(f"   Request {i+1}/10: ✓ {resp.status_code} in {elapsed:.2f}s")
            else:
                print(f"   Request {i+1}/10: ✗ {resp.status_code} in {elapsed:.2f}s (slow or failed)")
                all_passed = False
        except Exception as e:
            print(f"   Request {i+1}/10: ✗ Exception - {e}")
            all_passed = False
        time.sleep(0.5)  # Small delay between requests
    
    if all_passed:
        print("\n✓ PASS: Backend remains responsive during repeated polling, no timeout/hang detected")
    else:
        print("\n✗ FAIL: Backend showed timeout/hang symptoms during repeated polling")
    
    return all_passed

def main():
    print("=" * 70)
    print("DAILY REPORT RELEASE CLEANUP CLOSEOUT - BACKEND VERIFICATION")
    print("=" * 70)
    
    # Run stability smoke tests
    smoke_passed = test_stability_smoke()
    
    # Run repeated polling test
    polling_passed = test_repeated_polling()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    if smoke_passed and polling_passed:
        print("✓ ALL STABILITY TESTS PASSED")
        print("  - /health, /api/version, /api/daily-reports respond immediately")
        print("  - Backend remains responsive during repeated polling")
        print("  - No timeout/hang symptoms detected")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        if not smoke_passed:
            print("  - Stability smoke tests failed")
        if not polling_passed:
            print("  - Repeated polling test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

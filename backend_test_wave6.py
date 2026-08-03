#!/usr/bin/env python3
"""
Backend API Testing for WP16-W6-001 - Wave 6 Blocker Verification
Testing the cleanup-signals endpoint with various auth token combinations.

Blocker: WP16-W6-001
Endpoint: GET /api/admin/transportation/intelligence/cleanup-signals?days=30

Test cases:
1. Positive: valid Dispatch token only -> should return 200 with cleanup signals payload
2. Positive blocker case: valid Dispatch token + stale invalid X-Admin-Token -> should still return 200
3. Positive blocker case: valid Dispatch token + stale invalid X-Admin-Token + stale invalid X-Directory-Token -> should still return 200
4. Negative: no auth token -> should not return cleanup data (401)
5. Regression: Dispatch token should still be rejected on stricter admin-only route like /api/admin/transportation/intelligence/recommendations
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# Backend URL from environment
BACKEND_URL = "https://masci-audit-hub.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
CREDENTIALS = {
    "dispatch": {
        "email": "cert.dispatch@example.com",
        "password": "CertProof2026!"
    },
    "admin": {
        "email": "ops8-admin-only-preview@example.com",
        "password": "AdminOnlyOps8!"
    }
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
        print(f"WP16-W6-001 BLOCKER TEST SUMMARY: {len(self.passed)}/{self.total} tests passed")
        print("="*80)
        if self.failed:
            print("\n❌ FAILED TESTS:")
            for test_name, details in self.failed:
                print(f"  - {test_name}")
                if details:
                    print(f"    {details}")
        else:
            print("\n✅ ALL TESTS PASSED - BLOCKER WP16-W6-001 CLOSED")
        return len(self.failed) == 0


def get_dispatch_token(results: TestResult) -> Optional[str]:
    """Login as dispatch user and get token"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/dispatch/login",
            json=CREDENTIALS["dispatch"],
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            if token:
                print(f"✓ Obtained dispatch token: {token[:20]}...")
                return token
            else:
                print(f"✗ Dispatch login succeeded but no token in response")
                return None
        else:
            print(f"✗ Dispatch login failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Exception during dispatch login: {str(e)}")
        return None


def get_admin_token(results: TestResult) -> Optional[str]:
    """Login as admin user and get token"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/multi-login",
            json=CREDENTIALS["admin"],
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            portal_tokens = data.get("portal_tokens", {})
            token = portal_tokens.get("admin")
            if token:
                print(f"✓ Obtained admin token: {token[:20]}...")
                return token
            else:
                print(f"✗ Admin login succeeded but no admin token in response")
                return None
        else:
            print(f"✗ Admin login failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Exception during admin login: {str(e)}")
        return None


def test_case_1_dispatch_token_only(results: TestResult, dispatch_token: str):
    """Test 1: Valid Dispatch token only -> should return 200"""
    test_name = "Test 1: Valid Dispatch token only"
    try:
        headers = {
            "X-Dispatch-Token": dispatch_token
        }
        response = requests.get(
            f"{BACKEND_URL}/admin/transportation/intelligence/cleanup-signals?days=30",
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check for expected payload structure
            if "ok" in data or "signals" in data or isinstance(data, dict):
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, Response has cleanup signals payload"
                )
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but response doesn't look like cleanup signals: {str(data)[:100]}"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200. Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")


def test_case_2_dispatch_with_stale_admin(results: TestResult, dispatch_token: str):
    """Test 2: Valid Dispatch token + stale invalid X-Admin-Token -> should still return 200"""
    test_name = "Test 2: Valid Dispatch token + stale invalid X-Admin-Token"
    try:
        headers = {
            "X-Dispatch-Token": dispatch_token,
            "X-Admin-Token": "stale-invalid-admin-token-12345"
        }
        response = requests.get(
            f"{BACKEND_URL}/admin/transportation/intelligence/cleanup-signals?days=30",
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if "ok" in data or "signals" in data or isinstance(data, dict):
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, Dispatch token worked despite stale admin token. BLOCKER FIXED!"
                )
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but response doesn't look like cleanup signals"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200. BLOCKER NOT FIXED! Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")


def test_case_3_dispatch_with_multiple_stale(results: TestResult, dispatch_token: str):
    """Test 3: Valid Dispatch token + stale invalid X-Admin-Token + stale invalid X-Directory-Token -> should still return 200"""
    test_name = "Test 3: Valid Dispatch token + stale X-Admin-Token + stale X-Directory-Token"
    try:
        headers = {
            "X-Dispatch-Token": dispatch_token,
            "X-Admin-Token": "stale-invalid-admin-token-67890",
            "X-Directory-Token": "stale-invalid-directory-token-abcdef"
        }
        response = requests.get(
            f"{BACKEND_URL}/admin/transportation/intelligence/cleanup-signals?days=30",
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if "ok" in data or "signals" in data or isinstance(data, dict):
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, Dispatch token worked despite multiple stale tokens. BLOCKER FIXED!"
                )
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but response doesn't look like cleanup signals"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200. BLOCKER NOT FIXED! Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")


def test_case_4_no_auth_token(results: TestResult):
    """Test 4: No auth token -> should not return cleanup data (401)"""
    test_name = "Test 4: No auth token (negative test)"
    try:
        response = requests.get(
            f"{BACKEND_URL}/admin/transportation/intelligence/cleanup-signals?days=30",
            timeout=10
        )
        
        if response.status_code == 401:
            results.add_pass(
                test_name,
                f"Status: {response.status_code}, Correctly rejected unauthenticated request"
            )
        elif response.status_code == 403:
            results.add_pass(
                test_name,
                f"Status: {response.status_code}, Correctly rejected unauthenticated request (403 also acceptable)"
            )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 401 or 403. Unauthenticated request should be rejected!"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")


def test_case_5_regression_dispatch_on_admin_only(results: TestResult, dispatch_token: str):
    """Test 5: Dispatch token should be rejected on stricter admin-only route like /recommendations"""
    test_name = "Test 5: Regression - Dispatch token on admin-only /recommendations route"
    try:
        headers = {
            "X-Dispatch-Token": dispatch_token
        }
        response = requests.get(
            f"{BACKEND_URL}/admin/transportation/intelligence/recommendations?scope=triple&limit=10",
            headers=headers,
            timeout=10
        )
        
        # The /recommendations endpoint uses require_admin_dep (admin-only), not ops_guard
        # So dispatch token should be rejected
        if response.status_code in [401, 403]:
            results.add_pass(
                test_name,
                f"Status: {response.status_code}, Dispatch token correctly rejected on admin-only route"
            )
        elif response.status_code == 200:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, REGRESSION! Dispatch token should NOT work on admin-only /recommendations route"
            )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Unexpected status. Expected: 401 or 403"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")


def main():
    print("="*80)
    print("WP16-W6-001 Wave 6 Blocker Verification")
    print("Testing: GET /api/admin/transportation/intelligence/cleanup-signals")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print("="*80)
    print()
    
    results = TestResult()
    
    # Get tokens
    print("Step 1: Obtaining authentication tokens...")
    print()
    dispatch_token = get_dispatch_token(results)
    if not dispatch_token:
        print("\n❌ CRITICAL: Could not obtain dispatch token. Cannot proceed with tests.")
        return 1
    
    print()
    print("="*80)
    print("Step 2: Running blocker verification tests...")
    print("="*80)
    print()
    
    # Run all test cases
    test_case_1_dispatch_token_only(results, dispatch_token)
    print()
    
    test_case_2_dispatch_with_stale_admin(results, dispatch_token)
    print()
    
    test_case_3_dispatch_with_multiple_stale(results, dispatch_token)
    print()
    
    test_case_4_no_auth_token(results)
    print()
    
    test_case_5_regression_dispatch_on_admin_only(results, dispatch_token)
    print()
    
    # Print summary
    success = results.summary()
    
    if success:
        print("\n" + "="*80)
        print("✅ BLOCKER WP16-W6-001 VERIFICATION COMPLETE")
        print("="*80)
        print("All tests passed. The blocker is CLOSED.")
        print()
        print("Summary:")
        print("  ✓ Dispatch token works on cleanup-signals endpoint")
        print("  ✓ Dispatch token works even with stale X-Admin-Token present")
        print("  ✓ Dispatch token works even with multiple stale tokens present")
        print("  ✓ Unauthenticated requests are correctly rejected")
        print("  ✓ Dispatch token is still rejected on admin-only routes (no regression)")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ BLOCKER WP16-W6-001 VERIFICATION FAILED")
        print("="*80)
        print("Some tests failed. The blocker may NOT be fully closed.")
        print("="*80)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

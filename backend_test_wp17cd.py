#!/usr/bin/env python3
"""
Backend Sanity Check for WP-17C/WP-17D Shared Table Batch

Focused backend verification for the completed WP-17C/WP-17D shared table batch.
Tests only the impacted backend paths after the LastActivityLine portal fix.

Base URL: https://masci-audit-hub.preview.emergentagent.com
Preview credential: ops8-admin-pm-preview@example.com / AdminPmOps8!
Login endpoint: POST /api/auth/multi-login

Verifies:
1. Auth/login works for the preview fixture
2. /api/admin/scheduler-runs?limit=100 returns successful authenticated response
3. /api/diag/last-activity?portal=admin returns successful authenticated response
4. No obvious regression from the table batch or LastActivityLine portal fix

Context:
- Frontend batch already passed visual and functional QA
- Low-priority console warning from /api/diag/last-activity?portal=undefined fixed
- Main agent updated caller to use portal=admin and added shared guard in LastActivityLine
- MaintainX remains MOCKED by design
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# Backend URL from environment
BACKEND_URL = "https://masci-audit-hub.preview.emergentagent.com/api"

# Test credentials from review request
CREDENTIALS = {
    "email": "ops8-admin-pm-preview@example.com",
    "password": "AdminPmOps8!"
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

def test_multi_login(results: TestResult) -> Optional[Dict[str, Any]]:
    """Test POST /api/auth/multi-login with ops8-admin-pm-preview credentials"""
    test_name = "POST /api/auth/multi-login (ops8-admin-pm-preview)"
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/multi-login",
            json=CREDENTIALS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"DEBUG: Multi-login response keys: {list(data.keys())}")
            print(f"DEBUG: Portal tokens: {list(data.get('portal_tokens', {}).keys())}")
            if "session_token" in data and "portal_tokens" in data:
                # Check if admin and pm tokens are present
                portal_tokens = data.get("portal_tokens", {})
                has_admin = "admin" in portal_tokens
                has_pm = "pm" in portal_tokens
                
                # Print first 50 chars of admin token for debugging
                if has_admin:
                    admin_token = portal_tokens["admin"]
                    print(f"DEBUG: Admin token (first 50 chars): {admin_token[:50]}...")
                
                if has_admin and has_pm:
                    results.add_pass(
                        test_name,
                        f"Status: {response.status_code}, session_token present, admin and pm portal tokens present"
                    )
                    return data
                else:
                    results.add_fail(
                        test_name,
                        f"Status: {response.status_code}, but missing expected portal tokens (admin: {has_admin}, pm: {has_pm})"
                    )
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but missing session_token or portal_tokens"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200, Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")
    return None

def test_scheduler_runs(results: TestResult, auth_data: Dict[str, Any]):
    """Test GET /api/admin/scheduler-runs?limit=100 with admin token"""
    test_name = "GET /api/admin/scheduler-runs?limit=100"
    try:
        # Extract admin token from auth_data
        admin_token = auth_data.get("portal_tokens", {}).get("admin")
        if not admin_token:
            results.add_fail(test_name, "No admin token available from login")
            return
        
        # Make authenticated request
        headers = {
            "X-Admin-Token": admin_token
        }
        response = requests.get(
            f"{BACKEND_URL}/admin/scheduler-runs?limit=100",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check if response has expected structure
            if isinstance(data, dict) and "runs" in data:
                runs = data.get("runs", [])
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, returned {len(runs)} scheduler runs"
                )
            elif isinstance(data, list):
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, returned {len(data)} scheduler runs"
                )
            else:
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, response structure: {type(data).__name__}"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200, Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")

def test_last_activity(results: TestResult, auth_data: Dict[str, Any]):
    """Test GET /api/diag/last-activity?portal=admin with admin token"""
    test_name = "GET /api/diag/last-activity?portal=admin"
    try:
        # Extract admin token and session token from auth_data
        portal_tokens = auth_data.get("portal_tokens", {})
        admin_token = portal_tokens.get("admin")
        session_token = auth_data.get("session_token")
        
        if not admin_token:
            results.add_fail(test_name, f"No admin token available from login. Available portals: {list(portal_tokens.keys())}")
            return
        
        # Make authenticated request with both admin token and directory session token
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        response = requests.get(
            f"{BACKEND_URL}/diag/last-activity?portal=admin",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check if response has expected structure
            if isinstance(data, dict):
                # Expected fields: timestamp, portal, etc.
                has_timestamp = "timestamp" in data or "ts" in data or "last_activity" in data
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, response keys: {list(data.keys())[:5]}"
                )
            else:
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, response type: {type(data).__name__}"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200, Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")

def test_last_activity_without_portal(results: TestResult, auth_data: Dict[str, Any]):
    """Test GET /api/diag/last-activity without portal parameter (should handle gracefully)"""
    test_name = "GET /api/diag/last-activity (no portal param - should handle gracefully)"
    try:
        # Extract admin token and session token from auth_data
        portal_tokens = auth_data.get("portal_tokens", {})
        admin_token = portal_tokens.get("admin")
        session_token = auth_data.get("session_token")
        
        if not admin_token:
            results.add_fail(test_name, f"No admin token available from login. Available portals: {list(portal_tokens.keys())}")
            return
        
        # Make authenticated request without portal parameter with both tokens
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        response = requests.get(
            f"{BACKEND_URL}/diag/last-activity",
            headers=headers,
            timeout=10
        )
        
        # This should either return 200 with a default or 400 with a clear error
        if response.status_code == 200:
            results.add_pass(
                test_name,
                f"Status: {response.status_code}, endpoint handles missing portal parameter gracefully"
            )
        elif response.status_code == 400:
            data = response.json()
            if "error" in data or "message" in data:
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, returns clear error for missing portal parameter"
                )
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but error message not clear"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200 or 400, Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")

def main():
    print("="*80)
    print("WP-17C/WP-17D Shared Table Batch - Backend Sanity Check")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Credential: {CREDENTIALS['email']}")
    print("="*80)
    print()
    
    results = TestResult()
    
    # Test 1: Authentication
    print("Testing authentication...")
    print()
    auth_data = test_multi_login(results)
    
    if not auth_data:
        print("\n❌ Authentication failed. Cannot proceed with endpoint tests.")
        results.summary()
        return 1
    
    print()
    print("Testing impacted backend endpoints...")
    print()
    
    # Small delay to ensure session is fully established
    import time
    time.sleep(2)
    
    # Test 2: Scheduler runs endpoint
    test_scheduler_runs(results, auth_data)
    
    # Test 3: Last activity endpoint with portal=admin
    test_last_activity(results, auth_data)
    
    # Test 4: Last activity endpoint without portal parameter (regression check)
    test_last_activity_without_portal(results, auth_data)
    
    # Print summary
    success = results.summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

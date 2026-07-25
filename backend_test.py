#!/usr/bin/env python3
"""
Checkpoint 5 OTS Adoption - Backend API Verification
Tests the 9 OTS contract endpoints + 3 health endpoints
SHA: dac8319ac0d9d4c37cb6adb3df656d59c2570803
"""

import requests
import json
import sys
from typing import Dict, Any, List, Tuple

# Configuration
BASE_URL = "https://backup-forensics.preview.emergentagent.com/api"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test endpoints
OTS_ENDPOINTS = [
    "/platform/data-truth",
    "/admin/recovery/snapshot",
    "/admin/backup-verification/state",
    "/admin/backup-verification/preview",
    "/admin/backup-trust-score",
    "/admin/deployment-readiness",
    "/admin/deployment-readiness/history?limit=1",
    "/admin/integrations/truth-status",
    "/admin/deploy-recovery",
]

HEALTH_ENDPOINTS = [
    "/health",
    "/version",
    "/health/full",
]

# OTS metadata fields to check
OTS_METADATA_FIELDS = ["ots_truth", "truth_relationship", "compatibility"]


class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
        
    def add_pass(self, endpoint: str, message: str):
        self.passed.append({"endpoint": endpoint, "message": message})
        
    def add_fail(self, endpoint: str, message: str, details: str = ""):
        self.failed.append({"endpoint": endpoint, "message": message, "details": details})
        
    def add_warning(self, endpoint: str, message: str):
        self.warnings.append({"endpoint": endpoint, "message": message})
        
    def print_summary(self):
        total = len(self.passed) + len(self.failed)
        print("\n" + "="*80)
        print("CHECKPOINT 5 OTS ADOPTION - BACKEND VERIFICATION SUMMARY")
        print("="*80)
        print(f"\nTotal Endpoints Tested: {total}")
        print(f"✅ Passed: {len(self.passed)}")
        print(f"❌ Failed: {len(self.failed)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"Pass Rate: {len(self.passed)/total*100:.1f}%")
        
        if self.failed:
            print("\n" + "-"*80)
            print("FAILED ENDPOINTS:")
            print("-"*80)
            for fail in self.failed:
                print(f"\n❌ {fail['endpoint']}")
                print(f"   {fail['message']}")
                if fail['details']:
                    print(f"   Details: {fail['details']}")
        
        if self.warnings:
            print("\n" + "-"*80)
            print("WARNINGS:")
            print("-"*80)
            for warn in self.warnings:
                print(f"\n⚠️  {warn['endpoint']}")
                print(f"   {warn['message']}")
        
        if self.passed:
            print("\n" + "-"*80)
            print("PASSED ENDPOINTS:")
            print("-"*80)
            for p in self.passed:
                print(f"✅ {p['endpoint']}: {p['message']}")
        
        print("\n" + "="*80)
        return len(self.failed) == 0


def login(session: requests.Session) -> bool:
    """Login and get session cookie"""
    try:
        print(f"Logging in as {ADMIN_EMAIL}...")
        response = session.post(
            f"{BASE_URL}/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login successful. User: {data.get('user', {}).get('email', 'unknown')}")
            print(f"   Cookies received: {list(session.cookies.keys())}")
            print(f"   Portal tokens: {list(data.get('portal_tokens', {}).keys())}")
            
            # Store portal tokens and directory session token for later use
            session.portal_tokens = data.get('portal_tokens', {})
            session.directory_token = data.get('session_token', '')
            
            # Debug: print token formats
            admin_token = session.portal_tokens.get('admin', '')
            if admin_token:
                print(f"   Admin token format: {admin_token[:20]}...{admin_token[-10:]} (length: {len(admin_token)})")
                print(f"   Has dot separator: {'.' in admin_token}")
            if session.directory_token:
                print(f"   Directory token: {session.directory_token[:20]}... (length: {len(session.directory_token)})")
            
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return False


def check_ots_metadata(data: Any, endpoint: str, result: TestResult) -> bool:
    """Check if OTS metadata fields are present in response"""
    if not isinstance(data, dict):
        return False
    
    found_fields = []
    for field in OTS_METADATA_FIELDS:
        if field in data:
            found_fields.append(field)
    
    if found_fields:
        result.add_warning(
            endpoint,
            f"OTS metadata present: {', '.join(found_fields)}"
        )
        return True
    
    # Check nested structures
    for key, value in data.items():
        if isinstance(value, dict):
            nested_found = []
            for field in OTS_METADATA_FIELDS:
                if field in value:
                    nested_found.append(f"{key}.{field}")
            if nested_found:
                result.add_warning(
                    endpoint,
                    f"OTS metadata present in nested structure: {', '.join(nested_found)}"
                )
                return True
    
    return False


def test_endpoint(session: requests.Session, endpoint: str, result: TestResult, 
                  requires_auth: bool = True, timeout: int = 30) -> bool:
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        print(f"\nTesting: {endpoint}")
        
        # Add portal token and directory token headers if available for admin endpoints
        headers = {}
        if requires_auth and hasattr(session, 'portal_tokens') and hasattr(session, 'directory_token'):
            admin_token = session.portal_tokens.get('admin')
            if admin_token and '/admin/' in endpoint:
                headers['X-Admin-Token'] = admin_token
                headers['X-Directory-Token'] = session.directory_token
                print(f"   Using X-Admin-Token and X-Directory-Token headers")
        
        response = session.get(url, headers=headers, timeout=timeout)
        
        # Check status code
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Check for OTS metadata
                has_ots = check_ots_metadata(data, endpoint, result)
                
                # Check response structure
                if isinstance(data, dict):
                    keys = list(data.keys())
                    result.add_pass(
                        endpoint,
                        f"200 OK, {len(keys)} top-level keys" + 
                        (f", OTS metadata present" if has_ots else "")
                    )
                elif isinstance(data, list):
                    result.add_pass(
                        endpoint,
                        f"200 OK, array with {len(data)} items"
                    )
                else:
                    result.add_pass(endpoint, f"200 OK, response type: {type(data).__name__}")
                
                return True
                
            except json.JSONDecodeError:
                result.add_pass(endpoint, f"200 OK, non-JSON response")
                return True
                
        elif response.status_code == 401:
            result.add_fail(
                endpoint,
                "401 Unauthorized - Authentication failed",
                "Session may have expired or endpoint requires different auth"
            )
            return False
            
        elif response.status_code == 403:
            result.add_fail(
                endpoint,
                "403 Forbidden - Access denied",
                "User may not have required permissions"
            )
            return False
            
        elif response.status_code == 404:
            result.add_fail(
                endpoint,
                "404 Not Found - Endpoint does not exist",
                "Route may not be implemented"
            )
            return False
            
        elif response.status_code == 500:
            result.add_fail(
                endpoint,
                "500 Internal Server Error",
                response.text[:200] if response.text else "No error details"
            )
            return False
            
        elif response.status_code == 504:
            result.add_fail(
                endpoint,
                "504 Gateway Timeout",
                "Request exceeded timeout limit"
            )
            return False
            
        else:
            result.add_fail(
                endpoint,
                f"{response.status_code} - Unexpected status code",
                response.text[:200] if response.text else ""
            )
            return False
            
    except requests.exceptions.Timeout:
        result.add_fail(
            endpoint,
            f"Request timeout (>{timeout}s)",
            "Endpoint may be slow or unresponsive"
        )
        return False
        
    except requests.exceptions.ConnectionError as e:
        result.add_fail(
            endpoint,
            "Connection error",
            str(e)[:200]
        )
        return False
        
    except Exception as e:
        result.add_fail(
            endpoint,
            f"Unexpected error: {type(e).__name__}",
            str(e)[:200]
        )
        return False


def main():
    print("="*80)
    print("CHECKPOINT 5 OTS ADOPTION - BACKEND API VERIFICATION")
    print("SHA: dac8319ac0d9d4c37cb6adb3df656d59c2570803")
    print("="*80)
    
    result = TestResult()
    session = requests.Session()
    
    # Login
    if not login(session):
        print("\n❌ CRITICAL: Login failed. Cannot proceed with testing.")
        sys.exit(1)
    
    # Test health endpoints (no auth required)
    print("\n" + "-"*80)
    print("TESTING HEALTH ENDPOINTS (3 endpoints)")
    print("-"*80)
    for endpoint in HEALTH_ENDPOINTS:
        test_endpoint(session, endpoint, result, requires_auth=False, timeout=10)
    
    # Test OTS endpoints (auth required)
    print("\n" + "-"*80)
    print("TESTING OTS CONTRACT ENDPOINTS (9 endpoints)")
    print("-"*80)
    for endpoint in OTS_ENDPOINTS:
        test_endpoint(session, endpoint, result, requires_auth=True, timeout=30)
    
    # Print summary
    success = result.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

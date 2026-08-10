#!/usr/bin/env python3
"""
Backend API Testing for Direct Portal Role Token Flows
=======================================================
Tests the remaining direct-role token flows for Dispatch, Shop, and Field Leadership
after the auth/session fix in /app/backend/user_directory.py.

Test Scope:
- Dispatch: cert.dispatch@example.com / CertProof2026!
- Shop: cert.shop@example.com / CertProof2026!
- Field Leadership: cert.foreman@example.com / CertProof2026!

Validates:
1. Login endpoints return 200 and usable tokens
2. Authenticated read endpoints accept the returned token
3. Logout endpoints (if exist) invalidate tokens
"""

import requests
import sys
import json
from typing import Dict, Optional, Tuple

# Backend URL from frontend/.env
BACKEND_URL = "https://masci-audit-hub.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
DISPATCH_EMAIL = "cert.dispatch@example.com"
DISPATCH_PASSWORD = "CertProof2026!"

SHOP_EMAIL = "cert.shop@example.com"
SHOP_PASSWORD = "CertProof2026!"

FIELD_LEADERSHIP_EMAIL = "cert.foreman@example.com"
FIELD_LEADERSHIP_PASSWORD = "CertProof2026!"


class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, test_name: str, details: str = ""):
        self.passed.append((test_name, details))
        print(f"✅ PASS: {test_name}")
        if details:
            print(f"   {details}")
    
    def add_fail(self, test_name: str, details: str):
        self.failed.append((test_name, details))
        print(f"❌ FAIL: {test_name}")
        print(f"   {details}")
    
    def add_warning(self, test_name: str, details: str):
        self.warnings.append((test_name, details))
        print(f"⚠️  WARNING: {test_name}")
        print(f"   {details}")
    
    def summary(self):
        total = len(self.passed) + len(self.failed)
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {total}")
        print(f"Passed: {len(self.passed)}")
        print(f"Failed: {len(self.failed)}")
        print(f"Warnings: {len(self.warnings)}")
        print("="*80)
        
        if self.failed:
            print("\n❌ FAILED TESTS:")
            for test_name, details in self.failed:
                print(f"  - {test_name}")
                print(f"    {details}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for test_name, details in self.warnings:
                print(f"  - {test_name}")
                print(f"    {details}")
        
        return len(self.failed) == 0


def test_dispatch_flow(result: TestResult):
    """Test Dispatch portal login, /me endpoint, and logout (if exists)."""
    print("\n" + "="*80)
    print("TESTING DISPATCH PORTAL")
    print("="*80)
    
    # Test 1: POST /api/dispatch/login
    print(f"\n1. Testing POST {BACKEND_URL}/dispatch/login")
    try:
        response = requests.post(
            f"{BACKEND_URL}/dispatch/login",
            json={"email": DISPATCH_EMAIL, "password": DISPATCH_PASSWORD},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            user = data.get("user")
            
            if token and user:
                result.add_pass(
                    "Dispatch Login (POST /api/dispatch/login)",
                    f"Status: 200, Token received: {token[:20]}..., User: {user.get('email')}"
                )
                
                # Test 2: GET /api/dispatch/me with X-Dispatch-Token
                print(f"\n2. Testing GET {BACKEND_URL}/dispatch/me with X-Dispatch-Token")
                try:
                    me_response = requests.get(
                        f"{BACKEND_URL}/dispatch/me",
                        headers={"X-Dispatch-Token": token},
                        timeout=30
                    )
                    
                    if me_response.status_code == 200:
                        me_data = me_response.json()
                        result.add_pass(
                            "Dispatch /me endpoint (GET /api/dispatch/me)",
                            f"Status: 200, User data: {json.dumps(me_data, indent=2)}"
                        )
                    else:
                        result.add_fail(
                            "Dispatch /me endpoint (GET /api/dispatch/me)",
                            f"Status: {me_response.status_code}, Body: {me_response.text[:200]}"
                        )
                except Exception as e:
                    result.add_fail(
                        "Dispatch /me endpoint (GET /api/dispatch/me)",
                        f"Exception: {str(e)}"
                    )
                
                # Test 3: Check for logout endpoint
                print(f"\n3. Checking for Dispatch logout endpoint")
                # Try common logout paths
                logout_paths = [
                    "/dispatch/logout",
                    "/dispatch/portal/logout",
                    "/auth/dispatch/logout"
                ]
                
                logout_found = False
                for path in logout_paths:
                    try:
                        logout_response = requests.post(
                            f"{BACKEND_URL}{path}",
                            headers={"X-Dispatch-Token": token},
                            timeout=10
                        )
                        if logout_response.status_code != 404:
                            logout_found = True
                            if logout_response.status_code in [200, 204]:
                                # Verify token is invalidated
                                verify_response = requests.get(
                                    f"{BACKEND_URL}/dispatch/me",
                                    headers={"X-Dispatch-Token": token},
                                    timeout=10
                                )
                                if verify_response.status_code == 401:
                                    result.add_pass(
                                        f"Dispatch Logout (POST {path})",
                                        f"Status: {logout_response.status_code}, Token invalidated successfully"
                                    )
                                else:
                                    result.add_fail(
                                        f"Dispatch Logout (POST {path})",
                                        f"Logout returned {logout_response.status_code} but token still valid (got {verify_response.status_code} on /me)"
                                    )
                            break
                    except Exception:
                        continue
                
                if not logout_found:
                    result.add_warning(
                        "Dispatch Logout endpoint",
                        "No dedicated logout endpoint found. This is acceptable if using shared-client-logout coverage."
                    )
            else:
                result.add_fail(
                    "Dispatch Login (POST /api/dispatch/login)",
                    f"Status: 200 but missing token or user in response. Data: {json.dumps(data, indent=2)}"
                )
        else:
            result.add_fail(
                "Dispatch Login (POST /api/dispatch/login)",
                f"Status: {response.status_code}, Body: {response.text[:500]}"
            )
    except Exception as e:
        result.add_fail(
            "Dispatch Login (POST /api/dispatch/login)",
            f"Exception: {str(e)}"
        )


def test_shop_flow(result: TestResult):
    """Test Shop portal login, /me endpoint, and logout (if exists)."""
    print("\n" + "="*80)
    print("TESTING SHOP PORTAL")
    print("="*80)
    
    # Test 1: POST /api/shop/login
    print(f"\n1. Testing POST {BACKEND_URL}/shop/login")
    try:
        response = requests.post(
            f"{BACKEND_URL}/shop/login",
            json={"email": SHOP_EMAIL, "password": SHOP_PASSWORD},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            user = data.get("user")
            
            if token and user:
                result.add_pass(
                    "Shop Login (POST /api/shop/login)",
                    f"Status: 200, Token received: {token[:20]}..., User: {user.get('email')}"
                )
                
                # Test 2: GET /api/shop/me with X-Shop-Token
                print(f"\n2. Testing GET {BACKEND_URL}/shop/me with X-Shop-Token")
                try:
                    me_response = requests.get(
                        f"{BACKEND_URL}/shop/me",
                        headers={"X-Shop-Token": token},
                        timeout=30
                    )
                    
                    if me_response.status_code == 200:
                        me_data = me_response.json()
                        result.add_pass(
                            "Shop /me endpoint (GET /api/shop/me)",
                            f"Status: 200, User data: {json.dumps(me_data, indent=2)}"
                        )
                    else:
                        result.add_fail(
                            "Shop /me endpoint (GET /api/shop/me)",
                            f"Status: {me_response.status_code}, Body: {me_response.text[:200]}"
                        )
                except Exception as e:
                    result.add_fail(
                        "Shop /me endpoint (GET /api/shop/me)",
                        f"Exception: {str(e)}"
                    )
                
                # Test 3: Check for logout endpoint
                print(f"\n3. Checking for Shop logout endpoint")
                logout_paths = [
                    "/shop/logout",
                    "/shop/portal/logout",
                    "/auth/shop/logout"
                ]
                
                logout_found = False
                for path in logout_paths:
                    try:
                        logout_response = requests.post(
                            f"{BACKEND_URL}{path}",
                            headers={"X-Shop-Token": token},
                            timeout=10
                        )
                        if logout_response.status_code != 404:
                            logout_found = True
                            if logout_response.status_code in [200, 204]:
                                # Verify token is invalidated
                                verify_response = requests.get(
                                    f"{BACKEND_URL}/shop/me",
                                    headers={"X-Shop-Token": token},
                                    timeout=10
                                )
                                if verify_response.status_code == 401:
                                    result.add_pass(
                                        f"Shop Logout (POST {path})",
                                        f"Status: {logout_response.status_code}, Token invalidated successfully"
                                    )
                                else:
                                    result.add_fail(
                                        f"Shop Logout (POST {path})",
                                        f"Logout returned {logout_response.status_code} but token still valid (got {verify_response.status_code} on /me)"
                                    )
                            break
                    except Exception:
                        continue
                
                if not logout_found:
                    result.add_warning(
                        "Shop Logout endpoint",
                        "No dedicated logout endpoint found. This is acceptable if using shared-client-logout coverage."
                    )
            else:
                result.add_fail(
                    "Shop Login (POST /api/shop/login)",
                    f"Status: 200 but missing token or user in response. Data: {json.dumps(data, indent=2)}"
                )
        else:
            result.add_fail(
                "Shop Login (POST /api/shop/login)",
                f"Status: {response.status_code}, Body: {response.text[:500]}"
            )
    except Exception as e:
        result.add_fail(
            "Shop Login (POST /api/shop/login)",
            f"Exception: {str(e)}"
        )


def test_field_leadership_flow(result: TestResult):
    """Test Field Leadership portal login, /me endpoint, and logout (if exists)."""
    print("\n" + "="*80)
    print("TESTING FIELD LEADERSHIP PORTAL")
    print("="*80)
    
    # Test 1: POST /api/field-leadership/portal/login
    print(f"\n1. Testing POST {BACKEND_URL}/field-leadership/portal/login")
    try:
        response = requests.post(
            f"{BACKEND_URL}/field-leadership/portal/login",
            json={"email": FIELD_LEADERSHIP_EMAIL, "password": FIELD_LEADERSHIP_PASSWORD},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            user = data.get("user")
            
            if token and user:
                result.add_pass(
                    "Field Leadership Login (POST /api/field-leadership/portal/login)",
                    f"Status: 200, Token received: {token[:20]}..., User: {user.get('email')}"
                )
                
                # Test 2: GET /api/field-leadership/portal/me with X-FL-Token
                print(f"\n2. Testing GET {BACKEND_URL}/field-leadership/portal/me with X-FL-Token")
                try:
                    me_response = requests.get(
                        f"{BACKEND_URL}/field-leadership/portal/me",
                        headers={"X-FL-Token": token},
                        timeout=30
                    )
                    
                    if me_response.status_code == 200:
                        me_data = me_response.json()
                        result.add_pass(
                            "Field Leadership /me endpoint (GET /api/field-leadership/portal/me)",
                            f"Status: 200, User data: {json.dumps(me_data, indent=2)}"
                        )
                    else:
                        result.add_fail(
                            "Field Leadership /me endpoint (GET /api/field-leadership/portal/me)",
                            f"Status: {me_response.status_code}, Body: {me_response.text[:200]}"
                        )
                except Exception as e:
                    result.add_fail(
                        "Field Leadership /me endpoint (GET /api/field-leadership/portal/me)",
                        f"Exception: {str(e)}"
                    )
                
                # Test 3: Check for logout endpoint
                print(f"\n3. Checking for Field Leadership logout endpoint")
                logout_paths = [
                    "/field-leadership/portal/logout",
                    "/field-leadership/logout",
                    "/auth/field-leadership/logout"
                ]
                
                logout_found = False
                for path in logout_paths:
                    try:
                        logout_response = requests.post(
                            f"{BACKEND_URL}{path}",
                            headers={"X-FL-Token": token},
                            timeout=10
                        )
                        if logout_response.status_code != 404:
                            logout_found = True
                            if logout_response.status_code in [200, 204]:
                                # Verify token is invalidated
                                verify_response = requests.get(
                                    f"{BACKEND_URL}/field-leadership/portal/me",
                                    headers={"X-FL-Token": token},
                                    timeout=10
                                )
                                if verify_response.status_code == 401:
                                    result.add_pass(
                                        f"Field Leadership Logout (POST {path})",
                                        f"Status: {logout_response.status_code}, Token invalidated successfully"
                                    )
                                else:
                                    result.add_fail(
                                        f"Field Leadership Logout (POST {path})",
                                        f"Logout returned {logout_response.status_code} but token still valid (got {verify_response.status_code} on /me)"
                                    )
                            break
                    except Exception:
                        continue
                
                if not logout_found:
                    result.add_warning(
                        "Field Leadership Logout endpoint",
                        "No dedicated logout endpoint found. This is acceptable if using shared-client-logout coverage."
                    )
            else:
                result.add_fail(
                    "Field Leadership Login (POST /api/field-leadership/portal/login)",
                    f"Status: 200 but missing token or user in response. Data: {json.dumps(data, indent=2)}"
                )
        else:
            result.add_fail(
                "Field Leadership Login (POST /api/field-leadership/portal/login)",
                f"Status: {response.status_code}, Body: {response.text[:500]}"
            )
    except Exception as e:
        result.add_fail(
            "Field Leadership Login (POST /api/field-leadership/portal/login)",
            f"Exception: {str(e)}"
        )


def main():
    print("="*80)
    print("BACKEND API TESTING: Direct Portal Role Token Flows")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Testing Dispatch, Shop, and Field Leadership portals")
    print("="*80)
    
    result = TestResult()
    
    # Run all tests
    test_dispatch_flow(result)
    test_shop_flow(result)
    test_field_leadership_flow(result)
    
    # Print summary
    success = result.summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Backend API Testing for WP-16 Wave 1 - Public Pages & Authentication
Final backend verification after targeted repairs.

Tests the following endpoints:
1. POST /api/auth/multi-login (admin preview credentials)
2. POST /api/pm/login (certification PM credentials)
3. POST /api/hr/login (certification HR credentials)
4. POST /api/safety/login (certification Safety credentials)
5. POST /api/dispatch/login (certification Dispatch credentials)
6. POST /api/shop/login (certification Shop credentials)
7. POST /api/field-leadership/portal/login (certification Foreman credentials)
8. POST /api/safety/forgot-password (known preview safety email)
9. POST /api/dispatch/forgot-password (known preview dispatch email)
10. POST /api/dev/login (should fail with 404 in preview environment)
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# Backend URL from environment
BACKEND_URL = "https://backup-forensics.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
CREDENTIALS = {
    "admin": {
        "email": "ops8-admin-only-preview@example.com",
        "password": "AdminOnlyOps8!"
    },
    "pm": {
        "email": "cert.pm@example.com",
        "password": "CertProof2026!"
    },
    "hr": {
        "email": "cert.hr@example.com",
        "password": "CertProof2026!"
    },
    "safety": {
        "email": "cert.safety@example.com",
        "password": "CertProof2026!"
    },
    "dispatch": {
        "email": "cert.dispatch@example.com",
        "password": "CertProof2026!"
    },
    "shop": {
        "email": "cert.shop@example.com",
        "password": "CertProof2026!"
    },
    "foreman": {
        "email": "cert.foreman@example.com",
        "password": "CertProof2026!"
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

def test_multi_login(results: TestResult):
    """Test POST /api/auth/multi-login with admin preview credentials"""
    test_name = "POST /api/auth/multi-login (admin preview)"
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/multi-login",
            json=CREDENTIALS["admin"],
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "session_token" in data and "portal_tokens" in data:
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, session_token present, portal_tokens present"
                )
                return data
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but missing session_token or portal_tokens"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")
    return None

def test_pm_login(results: TestResult):
    """Test POST /api/pm/login with certification PM credentials"""
    test_name = "POST /api/pm/login (certification PM)"
    try:
        response = requests.post(
            f"{BACKEND_URL}/pm/login",
            json=CREDENTIALS["pm"],
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "token" in data:
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, token present"
                )
                return data
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but missing token"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")
    return None

def test_hr_login(results: TestResult):
    """Test POST /api/hr/login with certification HR credentials"""
    test_name = "POST /api/hr/login (certification HR)"
    try:
        response = requests.post(
            f"{BACKEND_URL}/hr/login",
            json=CREDENTIALS["hr"],
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "token" in data:
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, token present"
                )
                return data
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but missing token"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")
    return None

def test_safety_login(results: TestResult):
    """Test POST /api/safety/login with certification Safety credentials"""
    test_name = "POST /api/safety/login (certification Safety)"
    try:
        response = requests.post(
            f"{BACKEND_URL}/safety/login",
            json=CREDENTIALS["safety"],
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "token" in data:
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, token present"
                )
                return data
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but missing token"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")
    return None

def test_dispatch_login(results: TestResult):
    """Test POST /api/dispatch/login with certification Dispatch credentials"""
    test_name = "POST /api/dispatch/login (certification Dispatch)"
    try:
        response = requests.post(
            f"{BACKEND_URL}/dispatch/login",
            json=CREDENTIALS["dispatch"],
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "token" in data:
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, token present"
                )
                return data
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but missing token"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")
    return None

def test_shop_login(results: TestResult):
    """Test POST /api/shop/login with certification Shop credentials"""
    test_name = "POST /api/shop/login (certification Shop)"
    try:
        response = requests.post(
            f"{BACKEND_URL}/shop/login",
            json=CREDENTIALS["shop"],
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "token" in data:
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, token present"
                )
                return data
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but missing token"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")
    return None

def test_field_leadership_login(results: TestResult):
    """Test POST /api/field-leadership/portal/login with certification Foreman credentials"""
    test_name = "POST /api/field-leadership/portal/login (certification Foreman)"
    try:
        response = requests.post(
            f"{BACKEND_URL}/field-leadership/portal/login",
            json=CREDENTIALS["foreman"],
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "token" in data:
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, token present"
                )
                return data
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but missing token"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")
    return None

def test_safety_forgot_password(results: TestResult):
    """Test POST /api/safety/forgot-password with known preview safety email"""
    test_name = "POST /api/safety/forgot-password (preview safety email)"
    try:
        response = requests.post(
            f"{BACKEND_URL}/safety/forgot-password",
            json={"email": CREDENTIALS["safety"]["email"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "ok" in data and data["ok"]:
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, success-shaped response received"
                )
                return data
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but response not success-shaped"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")
    return None

def test_dispatch_forgot_password(results: TestResult):
    """Test POST /api/dispatch/forgot-password with known preview dispatch email"""
    test_name = "POST /api/dispatch/forgot-password (preview dispatch email)"
    try:
        response = requests.post(
            f"{BACKEND_URL}/dispatch/forgot-password",
            json={"email": CREDENTIALS["dispatch"]["email"]},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "ok" in data and data["ok"]:
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, success-shaped response received"
                )
                return data
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but response not success-shaped"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")
    return None

def test_dev_login(results: TestResult):
    """Test POST /api/dev/login - should fail with 404 in preview environment"""
    test_name = "POST /api/dev/login (should fail with 404)"
    try:
        response = requests.post(
            f"{BACKEND_URL}/dev/login",
            json={"password": "any_password"},
            timeout=10
        )
        
        if response.status_code == 404:
            results.add_pass(
                test_name,
                f"Status: {response.status_code}, correctly returns 404 in preview environment"
            )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 404"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")
    return None

def main():
    print("="*80)
    print("WP-16 Wave 1 Backend Verification - Public Pages & Authentication")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print("="*80)
    print()
    
    results = TestResult()
    
    # Run all tests
    print("Testing authentication endpoints...")
    print()
    
    test_multi_login(results)
    test_pm_login(results)
    test_hr_login(results)
    test_safety_login(results)
    test_dispatch_login(results)
    test_shop_login(results)
    test_field_leadership_login(results)
    
    print()
    print("Testing forgot-password endpoints...")
    print()
    
    test_safety_forgot_password(results)
    test_dispatch_forgot_password(results)
    
    print()
    print("Testing dev login (should fail)...")
    print()
    
    test_dev_login(results)
    
    # Print summary
    success = results.summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

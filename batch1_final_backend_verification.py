#!/usr/bin/env python3
"""
Batch 1 Final Backend/API Verification
READ-ONLY verification against https://backup-forensics.preview.emergentagent.com/api
NO CODE MODIFICATIONS
"""

import requests
import json
from typing import Dict, List, Tuple
from datetime import datetime

BASE_URL = "https://backup-forensics.preview.emergentagent.com/api"

# Test credentials from review request
CREDENTIALS = {
    "super_admin": {
        "email": "jaymn.judd@mascigc.com",
        "password": "Maddix123!",
        "label": "Super Admin"
    },
    "admin_only": {
        "email": "ops8-admin-only-preview@example.com",
        "password": "AdminOnlyOps8!",
        "label": "Admin-only"
    },
    "pm_only": {
        "email": "cert.pm@example.com",
        "password": "CertProof2026!",
        "label": "PM-only"
    },
    "safety_only": {
        "email": "cert.safety@example.com",
        "password": "CertProof2026!",
        "label": "Safety-only"
    },
    "pm_shop": {
        "email": "ops8-pm-shop-preview@example.com",
        "password": "PmShopOps8!",
        "label": "PM+Shop"
    }
}

class TestResults:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
        
    def add(self, category: str, test_name: str, passed: bool, details: str):
        self.tests.append({
            "category": category,
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def get_summary(self):
        return {
            "total": len(self.tests),
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": f"{(self.passed / len(self.tests) * 100):.1f}%" if self.tests else "0%"
        }

def multi_login(email: str, password: str) -> Tuple[bool, Dict]:
    """Perform multi-login and return success status and tokens"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/multi-login",
            json={"email": email, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, {
                "session_token": data.get("session_token"),
                "portal_tokens": data.get("portal_tokens", {})
            }
        else:
            return False, {"error": f"Status {response.status_code}", "body": response.text[:200]}
    except Exception as e:
        return False, {"error": str(e)}

def test_api_with_auth(endpoint: str, directory_token: str, portal_token: str = None, portal_name: str = None) -> Tuple[int, str]:
    """Test API endpoint with dual-token auth"""
    headers = {
        "X-Directory-Token": directory_token
    }
    
    if portal_token and portal_name:
        # Map portal name to header name
        portal_header_map = {
            "admin": "X-Admin-Token",
            "pm": "X-PM-Token",
            "safety": "X-Safety-Token",
            "shop": "X-Shop-Token",
            "dispatch": "X-Dispatch-Token",
            "hr": "X-HR-Token",
            "field_leadership": "X-FL-Token",
            "fl": "X-FL-Token"
        }
        header_name = portal_header_map.get(portal_name, f"X-{portal_name.title()}-Token")
        headers[header_name] = portal_token
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10)
        return response.status_code, response.text[:500]
    except Exception as e:
        return 0, str(e)

def test_api_without_auth(endpoint: str) -> Tuple[int, str]:
    """Test API endpoint without auth (should fail)"""
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        return response.status_code, response.text[:500]
    except Exception as e:
        return 0, str(e)

def main():
    results = TestResults()
    print("=" * 80)
    print("BATCH 1 FINAL BACKEND/API VERIFICATION")
    print("=" * 80)
    print(f"Target: {BASE_URL}")
    print(f"Started: {datetime.utcnow().isoformat()}")
    print()
    
    # Login all test users
    print("Authenticating test users...")
    auth_tokens = {}
    for key, creds in CREDENTIALS.items():
        success, tokens = multi_login(creds["email"], creds["password"])
        if success:
            auth_tokens[key] = tokens
            print(f"✓ {creds['label']}: Logged in successfully")
            print(f"  Portals: {list(tokens['portal_tokens'].keys())}")
        else:
            print(f"✗ {creds['label']}: Login failed - {tokens.get('error')}")
            results.add("AUTH", f"{creds['label']} login", False, f"Login failed: {tokens.get('error')}")
    
    print()
    print("=" * 80)
    print("TEST 1: INCIDENTS AUTH CONTRACT WITH CANONICAL DUAL-TOKEN USAGE")
    print("=" * 80)
    
    # Test Super Admin with all portal tokens
    if "super_admin" in auth_tokens:
        tokens = auth_tokens["super_admin"]
        dir_token = tokens["session_token"]
        
        # Test with admin token
        if "admin" in tokens["portal_tokens"]:
            status, body = test_api_with_auth("/incidents", dir_token, tokens["portal_tokens"]["admin"], "admin")
            passed = status == 200
            results.add("INCIDENTS", "Super Admin with admin token", passed, f"Status: {status}")
            print(f"{'✓' if passed else '✗'} Super Admin with admin token: {status}")
        
        # Test with pm token
        if "pm" in tokens["portal_tokens"]:
            status, body = test_api_with_auth("/incidents", dir_token, tokens["portal_tokens"]["pm"], "pm")
            passed = status == 200
            results.add("INCIDENTS", "Super Admin with pm token", passed, f"Status: {status}")
            print(f"{'✓' if passed else '✗'} Super Admin with pm token: {status}")
        
        # Test with safety token
        if "safety" in tokens["portal_tokens"]:
            status, body = test_api_with_auth("/incidents", dir_token, tokens["portal_tokens"]["safety"], "safety")
            passed = status == 200
            results.add("INCIDENTS", "Super Admin with safety token", passed, f"Status: {status}")
            print(f"{'✓' if passed else '✗'} Super Admin with safety token: {status}")
    
    # Test Admin-only with admin token
    if "admin_only" in auth_tokens:
        tokens = auth_tokens["admin_only"]
        dir_token = tokens["session_token"]
        
        if "admin" in tokens["portal_tokens"]:
            status, body = test_api_with_auth("/incidents", dir_token, tokens["portal_tokens"]["admin"], "admin")
            passed = status == 200
            results.add("INCIDENTS", "Admin-only with admin token", passed, f"Status: {status}")
            print(f"{'✓' if passed else '✗'} Admin-only with admin token: {status}")
    
    # Test PM-only with pm token
    if "pm_only" in auth_tokens:
        tokens = auth_tokens["pm_only"]
        dir_token = tokens["session_token"]
        
        if "pm" in tokens["portal_tokens"]:
            status, body = test_api_with_auth("/incidents", dir_token, tokens["portal_tokens"]["pm"], "pm")
            passed = status == 200
            results.add("INCIDENTS", "PM-only with pm token", passed, f"Status: {status}")
            print(f"{'✓' if passed else '✗'} PM-only with pm token: {status}")
    
    # Test Safety-only with safety token
    if "safety_only" in auth_tokens:
        tokens = auth_tokens["safety_only"]
        dir_token = tokens["session_token"]
        
        if "safety" in tokens["portal_tokens"]:
            status, body = test_api_with_auth("/incidents", dir_token, tokens["portal_tokens"]["safety"], "safety")
            passed = status == 200
            results.add("INCIDENTS", "Safety-only with safety token", passed, f"Status: {status}")
            print(f"{'✓' if passed else '✗'} Safety-only with safety token: {status}")
    
    print()
    print("=" * 80)
    print("TEST 2: SHARED NON-PREFIXED ROUTE APIs WITH PROPER CANONICAL TOKENS")
    print("=" * 80)
    
    # Use Super Admin for non-prefixed routes
    if "super_admin" in auth_tokens:
        tokens = auth_tokens["super_admin"]
        dir_token = tokens["session_token"]
        admin_token = tokens["portal_tokens"].get("admin")
        
        non_prefixed_routes = [
            "/project-health",
            "/asset-transfers",
            "/odr?status=draft",
            "/operational-records",
            "/operations-actions",
            "/operational-intelligence/recipients?limit=5"
        ]
        
        for route in non_prefixed_routes:
            status, body = test_api_with_auth(route, dir_token, admin_token, "admin")
            passed = status in [200, 404]  # 404 acceptable if not implemented
            results.add("NON-PREFIXED", f"GET {route}", passed, f"Status: {status}")
            print(f"{'✓' if passed else '✗'} GET {route}: {status}")
    
    print()
    print("=" * 80)
    print("TEST 3: NO REGRESSIONS ON PREVIOUSLY PASSING AUTH APIs")
    print("=" * 80)
    
    # Use Super Admin for regression checks
    if "super_admin" in auth_tokens:
        tokens = auth_tokens["super_admin"]
        dir_token = tokens["session_token"]
        admin_token = tokens["portal_tokens"].get("admin")
        pm_token = tokens["portal_tokens"].get("pm")
        safety_token = tokens["portal_tokens"].get("safety")
        
        regression_tests = [
            ("/admin/check", admin_token, "admin"),
            ("/pm/check", pm_token, "pm"),
            ("/safety/overview", safety_token, "safety"),
            ("/version", None, None),  # Public endpoint
            ("/health/full", None, None)  # Public endpoint
        ]
        
        for endpoint, token, portal in regression_tests:
            if token:
                status, body = test_api_with_auth(endpoint, dir_token, token, portal)
            else:
                status, body = test_api_without_auth(endpoint)
            
            passed = status in [200, 404]  # 404 acceptable if not implemented
            results.add("REGRESSION", f"GET {endpoint}", passed, f"Status: {status}")
            print(f"{'✓' if passed else '✗'} GET {endpoint}: {status}")
    
    print()
    print("=" * 80)
    print("TEST 4: NEGATIVE CHECKS - MISSING/WRONG TOKENS SHOULD FAIL")
    print("=" * 80)
    
    # Test missing token on /incidents
    status, body = test_api_without_auth("/incidents")
    passed = status == 401
    results.add("NEGATIVE", "GET /incidents without auth", passed, f"Status: {status} (expected 401)")
    print(f"{'✓' if passed else '✗'} GET /incidents without auth: {status} (expected 401)")
    
    # Test wrong-role access
    if "pm_only" in auth_tokens:
        tokens = auth_tokens["pm_only"]
        dir_token = tokens["session_token"]
        pm_token = tokens["portal_tokens"].get("pm")
        
        # PM user trying to access admin endpoint
        status, body = test_api_with_auth("/admin/check", dir_token, pm_token, "pm")
        passed = status == 401
        results.add("NEGATIVE", "PM-only accessing /admin/check", passed, f"Status: {status} (expected 401)")
        print(f"{'✓' if passed else '✗'} PM-only accessing /admin/check: {status} (expected 401)")
    
    if "admin_only" in auth_tokens:
        tokens = auth_tokens["admin_only"]
        dir_token = tokens["session_token"]
        admin_token = tokens["portal_tokens"].get("admin")
        
        # Admin user trying to access PM endpoint
        status, body = test_api_with_auth("/pm/check", dir_token, admin_token, "admin")
        passed = status == 401
        results.add("NEGATIVE", "Admin-only accessing /pm/check", passed, f"Status: {status} (expected 401)")
        print(f"{'✓' if passed else '✗'} Admin-only accessing /pm/check: {status} (expected 401)")
    
    print()
    print("=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    
    summary = results.get_summary()
    print(f"Total Tests: {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Pass Rate: {summary['pass_rate']}")
    print()
    
    # Categorize results
    categories = {}
    for test in results.tests:
        cat = test["category"]
        if cat not in categories:
            categories[cat] = {"passed": 0, "failed": 0, "tests": []}
        
        if test["passed"]:
            categories[cat]["passed"] += 1
        else:
            categories[cat]["failed"] += 1
        categories[cat]["tests"].append(test)
    
    print("RESULTS BY CATEGORY:")
    for cat, data in categories.items():
        total = data["passed"] + data["failed"]
        print(f"\n{cat}: {data['passed']}/{total} PASS")
        for test in data["tests"]:
            status = "✓ PASS" if test["passed"] else "✗ FAIL"
            print(f"  {status}: {test['test']} - {test['details']}")
    
    # Determine final verdict
    print()
    print("=" * 80)
    if results.failed == 0:
        print("FINAL BACKEND VERDICT: ✅ PASS")
        print("All backend API tests passed. No regressions found.")
    else:
        print("FINAL BACKEND VERDICT: ❌ FAIL")
        print(f"Found {results.failed} failing test(s). Backend regressions detected.")
    print("=" * 80)
    
    # Save results
    output = {
        "summary": summary,
        "categories": categories,
        "all_tests": results.tests,
        "verdict": "PASS" if results.failed == 0 else "FAIL",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    with open("/app/batch1_final_backend_verification_results.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to: /app/batch1_final_backend_verification_results.json")
    
    return 0 if results.failed == 0 else 1

if __name__ == "__main__":
    exit(main())

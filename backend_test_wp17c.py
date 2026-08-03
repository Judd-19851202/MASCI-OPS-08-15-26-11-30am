#!/usr/bin/env python3
"""
Backend API Smoke Testing for WP-17C
Backend smoke verification for the completed WP-17C representative foundation.

Tests the following endpoints:
1. POST /api/auth/multi-login (Super Admin jaymn.judd@mascigc.com / Maddix123!)
2. GET /api/admin/operational-inventory (using X-Admin-Token + directory token/session)
3. GET /api/asset-spine/assets (using same auth, should return at least one asset item)
4. GET /api/asset-spine/assets/{asset_id} (using same auth, for one returned asset id)
5. No backend regression check (verify all endpoints work correctly)
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# Backend URL from environment
BACKEND_URL = "https://masci-audit-hub.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
SUPER_ADMIN_CREDENTIALS = {
    "email": "jaymn.judd@mascigc.com",
    "password": "Maddix123!"
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
    """
    Test 1: POST /api/auth/multi-login succeeds for Super Admin 
    and returns usable portal tokens
    """
    test_name = "1. POST /api/auth/multi-login (Super Admin)"
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/multi-login",
            json=SUPER_ADMIN_CREDENTIALS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check for required fields
            if "session_token" in data and "portal_tokens" in data:
                portal_tokens = data.get("portal_tokens", {})
                admin_token = portal_tokens.get("admin")
                directory_token = data.get("session_token")
                
                if admin_token and directory_token:
                    results.add_pass(
                        test_name,
                        f"Status: {response.status_code}, X-Admin-Token present, Directory token present"
                    )
                    return {
                        "admin_token": admin_token,
                        "directory_token": directory_token,
                        "portal_tokens": portal_tokens
                    }
                else:
                    results.add_fail(
                        test_name,
                        f"Status: {response.status_code}, but missing admin_token or directory_token"
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

def test_operational_inventory(results: TestResult, auth_tokens: Dict[str, Any]) -> bool:
    """
    Test 2: GET /api/admin/operational-inventory succeeds 
    using X-Admin-Token + directory token/session
    """
    test_name = "2. GET /api/admin/operational-inventory"
    try:
        headers = {
            "X-Admin-Token": auth_tokens["admin_token"],
            "X-Directory-Token": auth_tokens["directory_token"]
        }
        
        response = requests.get(
            f"{BACKEND_URL}/admin/operational-inventory",
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            results.add_pass(
                test_name,
                f"Status: {response.status_code}, Response data received (length: {len(str(data))} chars)"
            )
            return True
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200, Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")
    return False

def test_asset_spine_assets(results: TestResult, auth_tokens: Dict[str, Any]) -> Optional[str]:
    """
    Test 3: GET /api/asset-spine/assets succeeds and returns at least one asset item
    """
    test_name = "3. GET /api/asset-spine/assets (should return at least one asset)"
    try:
        headers = {
            "X-Admin-Token": auth_tokens["admin_token"],
            "X-Directory-Token": auth_tokens["directory_token"]
        }
        
        response = requests.get(
            f"{BACKEND_URL}/asset-spine/assets",
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if data is a list or dict with assets
            assets = []
            if isinstance(data, list):
                assets = data
            elif isinstance(data, dict):
                # Could be {"assets": [...]} or {"data": [...]} or similar
                assets = data.get("assets", data.get("data", data.get("items", [])))
            
            if len(assets) > 0:
                # Get first asset ID for next test
                first_asset = assets[0]
                asset_id = None
                
                # Try different possible ID field names
                for id_field in ["id", "asset_id", "_id", "assetId", "uuid"]:
                    if id_field in first_asset:
                        asset_id = first_asset[id_field]
                        break
                
                results.add_pass(
                    test_name,
                    f"Status: {response.status_code}, Found {len(assets)} assets, First asset ID: {asset_id}"
                )
                return asset_id
            else:
                results.add_fail(
                    test_name,
                    f"Status: {response.status_code}, but no assets returned. Response: {str(data)[:200]}"
                )
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200, Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")
    return None

def test_asset_spine_asset_detail(results: TestResult, auth_tokens: Dict[str, Any], asset_id: str) -> bool:
    """
    Test 4: GET /api/asset-spine/assets/{asset_id} succeeds for one returned asset id
    """
    test_name = f"4. GET /api/asset-spine/assets/{asset_id}"
    try:
        headers = {
            "X-Admin-Token": auth_tokens["admin_token"],
            "X-Directory-Token": auth_tokens["directory_token"]
        }
        
        response = requests.get(
            f"{BACKEND_URL}/asset-spine/assets/{asset_id}",
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            results.add_pass(
                test_name,
                f"Status: {response.status_code}, Asset detail retrieved (length: {len(str(data))} chars)"
            )
            return True
        else:
            results.add_fail(
                test_name,
                f"Status: {response.status_code}, Expected: 200, Response: {response.text[:200]}"
            )
    except Exception as e:
        results.add_fail(test_name, f"Exception: {str(e)}")
    return False

def main():
    print("="*80)
    print("WP-17C Backend Smoke Verification")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Testing with Super Admin: {SUPER_ADMIN_CREDENTIALS['email']}")
    print("="*80)
    print()
    
    results = TestResult()
    
    # Test 1: Multi-login
    print("Test 1: POST /api/auth/multi-login")
    print("-" * 80)
    auth_tokens = test_multi_login(results)
    print()
    
    if not auth_tokens:
        print("❌ CRITICAL: Cannot proceed without valid auth tokens")
        results.summary()
        return 1
    
    # Test 2: Operational inventory
    print("Test 2: GET /api/admin/operational-inventory")
    print("-" * 80)
    test_operational_inventory(results, auth_tokens)
    print()
    
    # Test 3: Asset spine assets list
    print("Test 3: GET /api/asset-spine/assets")
    print("-" * 80)
    asset_id = test_asset_spine_assets(results, auth_tokens)
    print()
    
    # Test 4: Asset spine asset detail (only if we got an asset_id)
    if asset_id:
        print("Test 4: GET /api/asset-spine/assets/{asset_id}")
        print("-" * 80)
        test_asset_spine_asset_detail(results, auth_tokens, asset_id)
        print()
    else:
        print("⚠️  SKIPPED Test 4: No asset_id available from Test 3")
        print()
    
    # Test 5: No backend regression (implicit - if all above pass, no regression)
    if results.total > 0 and len(results.failed) == 0:
        results.add_pass(
            "5. No backend regression",
            "All WP-17C backend endpoints working correctly"
        )
    elif results.total > 0:
        results.add_fail(
            "5. Backend regression detected",
            f"{len(results.failed)} endpoint(s) failed"
        )
    
    # Print summary
    success = results.summary()
    
    print("\n" + "="*80)
    print("WP-17C Backend Smoke Verification Complete")
    print("="*80)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

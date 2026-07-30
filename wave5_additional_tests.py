#!/usr/bin/env python3
"""
WP-16 Wave 5 Safety Certification - Additional Backend API Tests
Testing additional endpoints and correcting path issues from initial inspection.
"""

import requests
import json
import sys

BASE_URL = "https://backup-forensics.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Use Safety token from initial test
SAFETY_CREDS = {"email": "cert.safety@example.com", "password": "CertProof2026!"}
SHOP_CREDS = {"email": "cert.shop@example.com", "password": "CertProof2026!"}

def get_safety_token():
    """Get Safety token"""
    response = requests.post(f"{API_BASE}/safety/login", json=SAFETY_CREDS, timeout=10)
    if response.status_code == 200:
        return response.json().get("token")
    return None

def get_shop_token():
    """Get Shop token via multi-login"""
    response = requests.post(f"{API_BASE}/auth/multi-login", json=SHOP_CREDS, timeout=10)
    if response.status_code == 200:
        data = response.json()
        return data.get("portal_tokens", {}).get("shop")
    return None

def test_shop_repairs(shop_token):
    """Test /api/trench-safety/shop/repairs endpoint"""
    print("\n=== Testing Shop Repairs Endpoint ===")
    try:
        response = requests.get(
            f"{API_BASE}/trench-safety/shop/repairs",
            headers={"X-Shop-Token": shop_token},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS: Shop repairs endpoint returned data")
            print(f"   Keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
        else:
            print(f"❌ FAIL: Status {response.status_code}, Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ FAIL: Exception: {str(e)}")

def test_trench_safety_deployments(safety_token):
    """Test /api/trench-safety/deployments endpoint"""
    print("\n=== Testing Trench Safety Deployments ===")
    try:
        response = requests.get(
            f"{API_BASE}/trench-safety/deployments",
            headers={"X-Safety-Token": safety_token},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            print(f"✅ PASS: Deployments returned {count} items")
        else:
            print(f"❌ FAIL: Status {response.status_code}, Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ FAIL: Exception: {str(e)}")

def test_trench_safety_holds(safety_token):
    """Test /api/trench-safety/holds endpoint"""
    print("\n=== Testing Trench Safety Holds ===")
    try:
        response = requests.get(
            f"{API_BASE}/trench-safety/holds",
            headers={"X-Safety-Token": safety_token},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            print(f"✅ PASS: Holds returned {count} items")
        else:
            print(f"❌ FAIL: Status {response.status_code}, Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ FAIL: Exception: {str(e)}")

def test_trench_safety_certifications(safety_token):
    """Test /api/trench-safety/certifications endpoint"""
    print("\n=== Testing Trench Safety Certifications ===")
    try:
        response = requests.get(
            f"{API_BASE}/trench-safety/certifications",
            headers={"X-Safety-Token": safety_token},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            print(f"✅ PASS: Certifications returned {count} items")
        else:
            print(f"❌ FAIL: Status {response.status_code}, Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ FAIL: Exception: {str(e)}")

def test_trench_safety_pulse(safety_token):
    """Test /api/trench-safety/pulse endpoint"""
    print("\n=== Testing Trench Safety Pulse ===")
    try:
        response = requests.get(
            f"{API_BASE}/trench-safety/pulse",
            headers={"X-Safety-Token": safety_token},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS: Pulse returned data")
            print(f"   Keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
        else:
            print(f"❌ FAIL: Status {response.status_code}, Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ FAIL: Exception: {str(e)}")

def test_trench_safety_reports(safety_token):
    """Test /api/trench-safety/reports endpoints"""
    print("\n=== Testing Trench Safety Reports ===")
    
    # Test digest endpoint
    try:
        response = requests.get(
            f"{API_BASE}/trench-safety/reports/digest",
            headers={"X-Safety-Token": safety_token},
            timeout=10
        )
        print(f"Digest Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ PASS: Reports digest endpoint working")
        else:
            print(f"⚠️  WARN: Digest status {response.status_code}")
    except Exception as e:
        print(f"⚠️  WARN: Digest exception: {str(e)}")

def test_asset_specific_endpoints(safety_token):
    """Test asset-specific endpoints if we have assets"""
    print("\n=== Testing Asset-Specific Endpoints ===")
    
    # First get assets
    try:
        response = requests.get(
            f"{API_BASE}/trench-safety/assets",
            headers={"X-Safety-Token": safety_token},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", []) if isinstance(data, dict) else data
            
            if items and len(items) > 0:
                asset_id = items[0].get("asset_id") or items[0].get("id")
                print(f"Found asset: {asset_id}")
                
                # Test inspections for this asset
                insp_response = requests.get(
                    f"{API_BASE}/trench-safety/assets/{asset_id}/inspections",
                    headers={"X-Safety-Token": safety_token},
                    timeout=10
                )
                print(f"Inspections Status: {insp_response.status_code}")
                if insp_response.status_code == 200:
                    print(f"✅ PASS: Asset inspections endpoint working")
                else:
                    print(f"❌ FAIL: Inspections status {insp_response.status_code}")
                
                # Test repairs for this asset
                repair_response = requests.get(
                    f"{API_BASE}/trench-safety/assets/{asset_id}/repairs",
                    headers={"X-Safety-Token": safety_token},
                    timeout=10
                )
                print(f"Repairs Status: {repair_response.status_code}")
                if repair_response.status_code == 200:
                    print(f"✅ PASS: Asset repairs endpoint working")
                else:
                    print(f"❌ FAIL: Repairs status {repair_response.status_code}")
            else:
                print("⚠️  No assets found to test asset-specific endpoints")
    except Exception as e:
        print(f"❌ FAIL: Exception: {str(e)}")

def test_incident_intelligence(safety_token):
    """Test incident intelligence endpoints"""
    print("\n=== Testing Incident Intelligence ===")
    try:
        response = requests.get(
            f"{API_BASE}/incident-intelligence/corrective-actions",
            headers={"X-Safety-Token": safety_token},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS: Incident intelligence corrective actions returned data")
        else:
            print(f"❌ FAIL: Status {response.status_code}, Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ FAIL: Exception: {str(e)}")

def test_safety_equipment_issuances(safety_token):
    """Test safety forms equipment issuances with Safety token"""
    print("\n=== Testing Safety Forms Equipment Issuances (Safety Token) ===")
    try:
        response = requests.get(
            f"{API_BASE}/safety-forms/equipment-issuances",
            headers={"X-Safety-Token": safety_token},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            print(f"✅ PASS: Equipment issuances returned {count} items")
        else:
            print(f"⚠️  WARN: Status {response.status_code} (may require Safety Forms token)")
    except Exception as e:
        print(f"⚠️  WARN: Exception: {str(e)}")

def test_safety_equipment_trainings(safety_token):
    """Test safety forms equipment trainings with Safety token"""
    print("\n=== Testing Safety Forms Equipment Trainings (Safety Token) ===")
    try:
        response = requests.get(
            f"{API_BASE}/safety-forms/equipment-trainings",
            headers={"X-Safety-Token": safety_token},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else "unknown"
            print(f"✅ PASS: Equipment trainings returned {count} items")
        else:
            print(f"⚠️  WARN: Status {response.status_code} (may require Safety Forms token)")
    except Exception as e:
        print(f"⚠️  WARN: Exception: {str(e)}")

def main():
    print("WP-16 Wave 5 Safety Certification - Additional Backend API Tests")
    print("="*80)
    
    # Get tokens
    print("\nAuthenticating...")
    safety_token = get_safety_token()
    if not safety_token:
        print("❌ CRITICAL: Could not get Safety token")
        sys.exit(1)
    print("✅ Safety token obtained")
    
    shop_token = get_shop_token()
    if shop_token:
        print("✅ Shop token obtained")
    else:
        print("⚠️  Could not get Shop token (some tests will be skipped)")
    
    # Run additional tests
    if shop_token:
        test_shop_repairs(shop_token)
    
    test_trench_safety_deployments(safety_token)
    test_trench_safety_holds(safety_token)
    test_trench_safety_certifications(safety_token)
    test_trench_safety_pulse(safety_token)
    test_trench_safety_reports(safety_token)
    test_asset_specific_endpoints(safety_token)
    test_incident_intelligence(safety_token)
    test_safety_equipment_issuances(safety_token)
    test_safety_equipment_trainings(safety_token)
    
    print("\n" + "="*80)
    print("Additional tests complete")
    print("="*80)

if __name__ == "__main__":
    main()

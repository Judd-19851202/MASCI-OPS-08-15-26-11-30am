#!/usr/bin/env python3
"""
Deep dive into FL auth issue
"""

import requests
import json

BACKEND_URL = "https://backup-forensics.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

CREDENTIALS = {
    "fl": {"email": "cert.foreman@example.com", "password": "CertProof2026!"},
}

def multi_login(email: str, password: str):
    """Perform multi-login and return tokens"""
    response = requests.post(
        f"{API_BASE}/auth/multi-login",
        json={"email": email, "password": password},
        timeout=30
    )
    if response.status_code == 200:
        return response.json()
    print(f"Login failed: {response.status_code}")
    print(response.text)
    return None

print("=" * 80)
print("FL AUTH DEEP DIVE")
print("=" * 80)

fl_login = multi_login(CREDENTIALS["fl"]["email"], CREDENTIALS["fl"]["password"])
if fl_login:
    print("\n✅ FL Login Response:")
    print(json.dumps(fl_login, indent=2))
    
    session_token = fl_login.get("session_token")
    portal_tokens = fl_login.get("portal_tokens", {})
    
    print(f"\n📋 Available portal tokens: {list(portal_tokens.keys())}")
    
    # Try both field_leadership and fl keys
    fl_token_from_field_leadership = portal_tokens.get("field_leadership")
    fl_token_from_fl = portal_tokens.get("fl")
    
    print(f"\nfield_leadership token: {fl_token_from_field_leadership}")
    print(f"fl token: {fl_token_from_fl}")
    
    # Test with different header combinations
    test_cases = [
        {
            "name": "X-FL-Token + X-Directory-Token (field_leadership key)",
            "headers": {
                "X-FL-Token": fl_token_from_field_leadership,
                "X-Directory-Token": session_token
            }
        },
        {
            "name": "X-FL-Token + X-Directory-Token (fl key)",
            "headers": {
                "X-FL-Token": fl_token_from_fl,
                "X-Directory-Token": session_token
            }
        },
        {
            "name": "X-Field-Leadership-Token + X-Directory-Token",
            "headers": {
                "X-Field-Leadership-Token": fl_token_from_field_leadership,
                "X-Directory-Token": session_token
            }
        },
        {
            "name": "Only X-FL-Token (no directory)",
            "headers": {
                "X-FL-Token": fl_token_from_field_leadership
            }
        },
        {
            "name": "Only X-Directory-Token (no portal)",
            "headers": {
                "X-Directory-Token": session_token
            }
        }
    ]
    
    endpoint = "/field-leadership/portal"
    
    print(f"\n🧪 Testing endpoint: {endpoint}")
    print("=" * 80)
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        response = requests.get(
            f"{API_BASE}{endpoint}",
            headers=test_case['headers'],
            timeout=30
        )
        print(f"  Status: {response.status_code}")
        if response.status_code != 200:
            try:
                print(f"  Response: {response.json()}")
            except:
                print(f"  Response: {response.text[:200]}")
        else:
            print(f"  ✅ SUCCESS")
    
    # Also test the public FL roster endpoint to confirm it's different
    print(f"\n🧪 Testing public endpoint: /field-leadership-roster")
    print("=" * 80)
    response = requests.get(f"{API_BASE}/field-leadership-roster", timeout=30)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Public endpoint accessible without auth (as expected)")

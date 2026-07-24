#!/usr/bin/env python3
"""
Test FL portal endpoints with directory-based tokens
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
    return None

print("=" * 80)
print("FL PORTAL DIRECTORY-BASED AUTH TEST")
print("=" * 80)

fl_login = multi_login(CREDENTIALS["fl"]["email"], CREDENTIALS["fl"]["password"])
if fl_login:
    session_token = fl_login.get("session_token")
    fl_token = fl_login.get("portal_tokens", {}).get("field_leadership") or fl_login.get("portal_tokens", {}).get("fl")
    
    print(f"\n✅ FL multi-login successful")
    print(f"FL token: {fl_token[:30]}..." if fl_token else "No FL token")
    
    headers = {
        "X-FL-Token": fl_token,
        "X-Directory-Token": session_token
    }
    
    # Test FL portal endpoints (directory-based)
    fl_portal_endpoints = [
        "/field-leadership/portal/me",
        "/field-leadership/portal/dispatch-today",
        "/field-leadership/portal/driver-qualification"
    ]
    
    print("\n🧪 Testing FL PORTAL endpoints (directory-based auth):")
    print("=" * 80)
    for endpoint in fl_portal_endpoints:
        response = requests.get(f"{API_BASE}{endpoint}", headers=headers, timeout=30)
        status_icon = "✅" if response.status_code == 200 else "❌" if response.status_code == 401 else "⚠️"
        print(f"{status_icon} {endpoint}: {response.status_code}")
        if response.status_code == 401:
            try:
                print(f"    Error: {response.json()}")
            except:
                print(f"    Error: {response.text[:200]}")
        elif response.status_code == 200:
            try:
                data = response.json()
                print(f"    Success: {list(data.keys())[:5]}")
            except:
                pass
    
    # Also test the legacy FL endpoints (shared-password based) - should fail with directory token
    print("\n🧪 Testing LEGACY FL endpoints (shared-password auth - should fail with directory token):")
    print("=" * 80)
    legacy_endpoints = [
        "/field-leadership/records",
        "/field-leadership/login"
    ]
    for endpoint in legacy_endpoints:
        response = requests.get(f"{API_BASE}{endpoint}", headers=headers, timeout=30)
        status_icon = "✅" if response.status_code in [401, 404, 405] else "⚠️"
        print(f"{status_icon} {endpoint}: {response.status_code} (expected 401/404/405 for legacy endpoints)")

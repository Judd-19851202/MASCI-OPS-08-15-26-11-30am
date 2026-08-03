#!/usr/bin/env python3
"""
Test Safety endpoints to find one that exists
"""

import requests

BACKEND_URL = "https://masci-audit-hub.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

CREDENTIALS = {
    "safety": {"email": "cert.safety@example.com", "password": "CertProof2026!"},
}

def multi_login(email: str, password: str):
    response = requests.post(
        f"{API_BASE}/auth/multi-login",
        json={"email": email, "password": password},
        timeout=30
    )
    if response.status_code == 200:
        return response.json()
    return None

print("Testing Safety endpoints...")

safety_login = multi_login(CREDENTIALS["safety"]["email"], CREDENTIALS["safety"]["password"])
if safety_login:
    session_token = safety_login.get("session_token")
    safety_token = safety_login.get("portal_tokens", {}).get("safety")
    
    headers = {
        "X-Safety-Token": safety_token,
        "X-Directory-Token": session_token
    }
    
    # Test various safety endpoints
    endpoints = [
        "/inspections",
        "/meetings",
        "/jhas",
        "/incidents",
        "/safety/dashboard",
        "/safety/incidents"
    ]
    
    print("\nWith Safety auth:")
    for endpoint in endpoints:
        response = requests.get(f"{API_BASE}{endpoint}", headers=headers, timeout=30)
        print(f"  {endpoint}: {response.status_code}")
    
    print("\nWithout auth (should be 401):")
    for endpoint in endpoints:
        response = requests.get(f"{API_BASE}{endpoint}", timeout=30)
        print(f"  {endpoint}: {response.status_code}")

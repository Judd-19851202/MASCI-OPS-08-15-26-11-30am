#!/usr/bin/env python3
"""
Investigate specific auth issues found in initial test
"""

import requests
import json

BACKEND_URL = "https://backup-forensics.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

CREDENTIALS = {
    "super_admin": {"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
    "safety": {"email": "cert.safety@example.com", "password": "CertProof2026!"},
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
print("INVESTIGATING SAFETY ENDPOINT")
print("=" * 80)

# Test Safety with different endpoints
safety_login = multi_login(CREDENTIALS["safety"]["email"], CREDENTIALS["safety"]["password"])
if safety_login:
    session_token = safety_login.get("session_token")
    safety_token = safety_login.get("portal_tokens", {}).get("safety")
    
    print(f"Safety login successful")
    print(f"Session token: {session_token[:20]}..." if session_token else "No session token")
    print(f"Safety token: {safety_token[:20]}..." if safety_token else "No safety token")
    
    headers = {
        "X-Safety-Token": safety_token,
        "X-Directory-Token": session_token
    }
    
    # Try different safety endpoints
    safety_endpoints = [
        "/safety/incidents",
        "/safety/dashboard",
        "/safety/trench-permits",
        "/safety/inspections"
    ]
    
    print("\nTesting Safety endpoints with auth:")
    for endpoint in safety_endpoints:
        response = requests.get(f"{API_BASE}{endpoint}", headers=headers, timeout=30)
        print(f"  {endpoint}: {response.status_code}")
        if response.status_code == 401:
            print(f"    ERROR: {response.text[:200]}")
    
    print("\nTesting Safety endpoints without auth (should be 401):")
    for endpoint in safety_endpoints:
        response = requests.get(f"{API_BASE}{endpoint}", timeout=30)
        print(f"  {endpoint}: {response.status_code}")

print("\n" + "=" * 80)
print("INVESTIGATING FIELD LEADERSHIP ENDPOINT")
print("=" * 80)

# Test FL with different endpoints
fl_login = multi_login(CREDENTIALS["fl"]["email"], CREDENTIALS["fl"]["password"])
if fl_login:
    session_token = fl_login.get("session_token")
    print(f"\nFL login successful")
    print(f"Session token: {session_token[:20]}..." if session_token else "No session token")
    print(f"Portal tokens available: {list(fl_login.get('portal_tokens', {}).keys())}")
    
    # Check both field_leadership and fl keys
    fl_token = fl_login.get("portal_tokens", {}).get("field_leadership") or fl_login.get("portal_tokens", {}).get("fl")
    print(f"FL token: {fl_token[:20]}..." if fl_token else "No FL token")
    
    if fl_token:
        headers = {
            "X-FL-Token": fl_token,
            "X-Directory-Token": session_token
        }
        
        # Try different FL endpoints
        fl_endpoints = [
            "/field-leadership/portal",
            "/field-leadership/dashboard",
            "/field-leadership-roster"
        ]
        
        print("\nTesting FL endpoints with auth:")
        for endpoint in fl_endpoints:
            response = requests.get(f"{API_BASE}{endpoint}", headers=headers, timeout=30)
            print(f"  {endpoint}: {response.status_code}")
            if response.status_code == 401:
                print(f"    ERROR: {response.text[:200]}")
        
        print("\nTesting FL endpoints without auth (should be 401 or 200 for public):")
        for endpoint in fl_endpoints:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=30)
            print(f"  {endpoint}: {response.status_code}")

print("\n" + "=" * 80)
print("CHECKING ADMIN ACCESS TO VERIFY AUTH IS WORKING")
print("=" * 80)

admin_login = multi_login(CREDENTIALS["super_admin"]["email"], CREDENTIALS["super_admin"]["password"])
if admin_login:
    session_token = admin_login.get("session_token")
    admin_token = admin_login.get("portal_tokens", {}).get("admin")
    
    headers = {
        "X-Admin-Token": admin_token,
        "X-Directory-Token": session_token
    }
    
    # Test admin endpoints
    admin_endpoints = [
        "/admin/deployment-readiness",
        "/admin/users",
        "/admin/backups/integrity-check"
    ]
    
    print("\nTesting Admin endpoints with auth:")
    for endpoint in admin_endpoints:
        response = requests.get(f"{API_BASE}{endpoint}", headers=headers, timeout=30)
        print(f"  {endpoint}: {response.status_code}")

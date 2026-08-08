#!/usr/bin/env python3
"""
Production Authentication Diagnostic
Diagnose why portal tokens from multi-login aren't working
"""

import requests
import json
import time

BASE_URL = "https://mascidocs.com"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

print("="*80)
print("PRODUCTION AUTHENTICATION DIAGNOSTIC")
print("="*80 + "\n")

# Step 1: Multi-login
print("Step 1: Performing multi-login...")
login_response = requests.post(
    f"{BASE_URL}/api/auth/multi-login",
    json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    timeout=10
)

print(f"Status: {login_response.status_code}")
if login_response.status_code != 200:
    print(f"ERROR: Login failed")
    print(json.dumps(login_response.json(), indent=2))
    exit(1)

login_data = login_response.json()
print(f"✅ Login successful")
print(f"Portals returned: {list(login_data.get('portal_tokens', {}).keys())}")
print(f"Has session_token: {bool(login_data.get('session_token'))}")
print(f"Must change password: {login_data.get('must_change_password', False)}")
print()

# Extract tokens
admin_token = login_data.get("portal_tokens", {}).get("admin")
pm_token = login_data.get("portal_tokens", {}).get("pm")
session_token = login_data.get("session_token")

if not admin_token:
    print("ERROR: No admin token returned")
    exit(1)

print(f"Admin token (first 50 chars): {admin_token[:50]}...")
print()

# Step 2: Try admin/check immediately
print("Step 2: Testing /api/admin/check immediately after login...")
check_response = requests.get(
    f"{BASE_URL}/api/admin/check",
    headers={"X-Admin-Token": admin_token},
    timeout=10
)
print(f"Status: {check_response.status_code}")
print(f"Response: {json.dumps(check_response.json(), indent=2)}")
print()

# Step 3: Wait and try again
if check_response.status_code != 200:
    print("Step 3: Waiting 2 seconds and trying again...")
    time.sleep(2)
    check_response2 = requests.get(
        f"{BASE_URL}/api/admin/check",
        headers={"X-Admin-Token": admin_token},
        timeout=10
    )
    print(f"Status: {check_response2.status_code}")
    print(f"Response: {json.dumps(check_response2.json(), indent=2)}")
    print()

# Step 4: Try with session token
if session_token:
    print("Step 4: Testing with X-Directory-Token (session_token)...")
    check_response3 = requests.get(
        f"{BASE_URL}/api/admin/check",
        headers={"X-Directory-Token": session_token},
        timeout=10
    )
    print(f"Status: {check_response3.status_code}")
    print(f"Response: {json.dumps(check_response3.json(), indent=2)}")
    print()

# Step 5: Try PM endpoint with PM token
if pm_token:
    print("Step 5: Testing /api/pm/jobs with PM token...")
    pm_response = requests.get(
        f"{BASE_URL}/api/pm/jobs",
        headers={"X-PM-Token": pm_token},
        timeout=10
    )
    print(f"Status: {pm_response.status_code}")
    if pm_response.status_code == 200:
        data = pm_response.json()
        print(f"✅ PM endpoint works! Returned {len(data) if isinstance(data, list) else 'N/A'} jobs")
    else:
        print(f"Response: {json.dumps(pm_response.json(), indent=2)}")
    print()

# Step 6: Try a different admin endpoint
print("Step 6: Testing /api/admin/deployment-readiness...")
deploy_response = requests.get(
    f"{BASE_URL}/api/admin/deployment-readiness",
    headers={"X-Admin-Token": admin_token},
    timeout=10
)
print(f"Status: {deploy_response.status_code}")
if deploy_response.status_code == 200:
    print(f"✅ Deployment readiness endpoint works!")
else:
    print(f"Response: {json.dumps(deploy_response.json(), indent=2)}")
print()

# Summary
print("="*80)
print("DIAGNOSTIC SUMMARY")
print("="*80)
print(f"Login: {'✅ SUCCESS' if login_response.status_code == 200 else '❌ FAILED'}")
print(f"Admin token received: {'✅ YES' if admin_token else '❌ NO'}")
print(f"Admin check: {'✅ SUCCESS' if check_response.status_code == 200 else '❌ FAILED'}")
if pm_token:
    print(f"PM endpoint: {'✅ SUCCESS' if pm_response.status_code == 200 else '❌ FAILED'}")
print()

if check_response.status_code != 200:
    print("⚠️  ISSUE IDENTIFIED:")
    print("Portal tokens are being returned from multi-login but are not being")
    print("accepted by authenticated endpoints. This suggests:")
    print("1. Session activity records may not be created properly")
    print("2. Token validation logic may have changed")
    print("3. There may be a production-specific configuration issue")

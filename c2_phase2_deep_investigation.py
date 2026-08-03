#!/usr/bin/env python3
"""
Deep investigation of potential deployment blockers
"""

import requests
import json

PREVIEW_BASE_URL = "https://masci-audit-hub.preview.emergentagent.com"
API_BASE_URL = f"{PREVIEW_BASE_URL}/api"
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"

print("=" * 80)
print("DEEP INVESTIGATION OF POTENTIAL BLOCKERS")
print("=" * 80)

# Issue 1: Old token after relogin
print("\n[ISSUE 1] Old token after relogin")
print("-" * 80)

# First login
resp1 = requests.post(f"{API_BASE_URL}/auth/multi-login", 
                      json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD})
auth1 = resp1.json()
old_admin_token = auth1["portal_tokens"]["admin"]
old_directory_token = auth1["session_token"]

print(f"First login - Admin token: {old_admin_token[:20]}...")
print(f"First login - Directory token: {old_directory_token[:20]}...")

# Logout
requests.post(f"{API_BASE_URL}/auth/multi-logout", 
              headers={"X-Directory-Token": old_directory_token})
print("Logged out")

# Second login
resp2 = requests.post(f"{API_BASE_URL}/auth/multi-login",
                      json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD})
auth2 = resp2.json()
new_admin_token = auth2["portal_tokens"]["admin"]
new_directory_token = auth2["session_token"]

print(f"Second login - Admin token: {new_admin_token[:20]}...")
print(f"Second login - Directory token: {new_directory_token[:20]}...")

# Test 1: Old admin token + new directory token
headers1 = {
    "X-Admin-Token": old_admin_token,
    "X-Directory-Token": new_directory_token
}
resp_test1 = requests.get(f"{API_BASE_URL}/daily-reports?limit=1", headers=headers1)
print(f"\nTest 1 - Old admin + new directory: {resp_test1.status_code}")

# Test 2: Old admin token + old directory token
headers2 = {
    "X-Admin-Token": old_admin_token,
    "X-Directory-Token": old_directory_token
}
resp_test2 = requests.get(f"{API_BASE_URL}/daily-reports?limit=1", headers=headers2)
print(f"Test 2 - Old admin + old directory: {resp_test2.status_code}")

# Test 3: New admin token + old directory token
headers3 = {
    "X-Admin-Token": new_admin_token,
    "X-Directory-Token": old_directory_token
}
resp_test3 = requests.get(f"{API_BASE_URL}/daily-reports?limit=1", headers=headers3)
print(f"Test 3 - New admin + old directory: {resp_test3.status_code}")

# Test 4: New admin token + new directory token
headers4 = {
    "X-Admin-Token": new_admin_token,
    "X-Directory-Token": new_directory_token
}
resp_test4 = requests.get(f"{API_BASE_URL}/daily-reports?limit=1", headers=headers4)
print(f"Test 4 - New admin + new directory: {resp_test4.status_code}")

print("\nANALYSIS:")
if resp_test1.status_code == 200:
    print("⚠️  Old admin token works with new directory token")
    print("   This suggests portal tokens are NOT tied to directory sessions")
    print("   OR portal tokens have longer TTL than directory tokens")
else:
    print("✅ Old admin token correctly rejected with new directory token")

# Issue 2: Protected admin route
print("\n\n[ISSUE 2] Protected admin route /api/users")
print("-" * 80)

# Get fresh auth
resp = requests.post(f"{API_BASE_URL}/auth/multi-login",
                     json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD})
auth = resp.json()

headers = {
    "X-Admin-Token": auth["portal_tokens"]["admin"],
    "X-Directory-Token": auth["session_token"]
}

# Test /api/users
resp_users = requests.get(f"{API_BASE_URL}/users", headers=headers)
print(f"/api/users status: {resp_users.status_code}")
if resp_users.status_code != 200:
    print(f"Response: {resp_users.text[:200]}")

# Try alternative admin endpoints
admin_endpoints = [
    "/admin/users",
    "/directory/users",
    "/projects",
    "/admin/projects"
]

print("\nTrying alternative admin endpoints:")
for endpoint in admin_endpoints:
    resp = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers)
    print(f"  {endpoint}: {resp.status_code}")

print("\nANALYSIS:")
if resp_users.status_code == 401:
    print("⚠️  /api/users endpoint returns 401 with valid admin credentials")
    print("   This might be expected if the endpoint doesn't exist or requires different auth")
    print("   NOT a deployment blocker if other admin endpoints work")
elif resp_users.status_code == 404:
    print("✅ /api/users endpoint doesn't exist (404) - this is fine")
else:
    print(f"✅ /api/users endpoint accessible: {resp_users.status_code}")

# Issue 3: CORS behavior
print("\n\n[ISSUE 3] CORS configuration")
print("-" * 80)

# Test with malicious origin
headers_malicious = {
    "Origin": "https://malicious-site.com",
    "X-Admin-Token": auth["portal_tokens"]["admin"],
    "X-Directory-Token": auth["session_token"]
}
resp_cors1 = requests.get(f"{API_BASE_URL}/daily-reports?limit=1", headers=headers_malicious)
cors_header1 = resp_cors1.headers.get("Access-Control-Allow-Origin")
cors_creds1 = resp_cors1.headers.get("Access-Control-Allow-Credentials")

print(f"Request with Origin: https://malicious-site.com")
print(f"  Access-Control-Allow-Origin: {cors_header1}")
print(f"  Access-Control-Allow-Credentials: {cors_creds1}")

# Test with legitimate origin
headers_legit = {
    "Origin": PREVIEW_BASE_URL,
    "X-Admin-Token": auth["portal_tokens"]["admin"],
    "X-Directory-Token": auth["session_token"]
}
resp_cors2 = requests.get(f"{API_BASE_URL}/daily-reports?limit=1", headers=headers_legit)
cors_header2 = resp_cors2.headers.get("Access-Control-Allow-Origin")
cors_creds2 = resp_cors2.headers.get("Access-Control-Allow-Credentials")

print(f"\nRequest with Origin: {PREVIEW_BASE_URL}")
print(f"  Access-Control-Allow-Origin: {cors_header2}")
print(f"  Access-Control-Allow-Credentials: {cors_creds2}")

# Test without origin
resp_cors3 = requests.get(f"{API_BASE_URL}/daily-reports?limit=1", headers={
    "X-Admin-Token": auth["portal_tokens"]["admin"],
    "X-Directory-Token": auth["session_token"]
})
cors_header3 = resp_cors3.headers.get("Access-Control-Allow-Origin")
cors_creds3 = resp_cors3.headers.get("Access-Control-Allow-Credentials")

print(f"\nRequest without Origin header:")
print(f"  Access-Control-Allow-Origin: {cors_header3}")
print(f"  Access-Control-Allow-Credentials: {cors_creds3}")

print("\nANALYSIS:")
if cors_header1 == "*" and cors_creds1 == "true":
    print("🚨 DEPLOYMENT BLOCKER: CORS allows wildcard origin with credentials")
    print("   This is a security vulnerability")
elif cors_header1 == "https://malicious-site.com":
    print("🚨 DEPLOYMENT BLOCKER: CORS reflects arbitrary origins")
    print("   This allows credential theft from malicious sites")
elif cors_header1 is None or cors_header1 == PREVIEW_BASE_URL:
    print("✅ CORS properly configured - only allows legitimate origins")
else:
    print(f"⚠️  Unexpected CORS behavior: {cors_header1}")

print("\n" + "=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)

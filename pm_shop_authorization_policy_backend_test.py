#!/usr/bin/env python3
"""
PM/Shop Authorization Policy Repair - Final Backend Verification

Tests the bounded policy fix where ordinary Admin is NOT Super Admin and must
not access PM or Shop unless explicitly granted. Super Admin retains full access.

Preview backend: https://masci-audit-hub.preview.emergentagent.com/api
"""
import json
import os
import sys
from datetime import datetime, timezone
import requests

# Test credentials from /app/memory/test_credentials.md
BACKEND_URL = "https://masci-audit-hub.preview.emergentagent.com/api"

CREDENTIALS = {
    "super_admin": {
        "email": "jaymn.judd@mascigc.com",
        "password": "Maddix123!",
        "expected_portals": ["admin", "pm", "shop", "hr", "safety", "dispatch", "field_leadership", "fl"],
    },
    "admin_only": {
        "email": "ops8-admin-only-preview@example.com",
        "password": "AdminOnlyOps8!",
        "expected_portals": ["admin"],
    },
    "admin_pm": {
        "email": "ops8-admin-pm-preview@example.com",
        "password": "AdminPmOps8!",
        "expected_portals": ["admin", "pm"],
    },
    "admin_shop": {
        "email": "ops8-admin-shop-preview@example.com",
        "password": "AdminShopOps8!",
        "expected_portals": ["admin", "shop"],
    },
    "pm_shop": {
        "email": "ops8-pm-shop-preview@example.com",
        "password": "PmShopOps8!",
        "expected_portals": ["pm", "shop"],
    },
    "pm_only": {
        "email": "cert.pm@example.com",
        "password": "CertProof2026!",
        "expected_portals": ["pm"],
    },
    "shop_only": {
        "email": "cert.shop@example.com",
        "password": "CertProof2026!",
        "expected_portals": ["shop"],
    },
    "disabled": {
        "email": "ops8-disabled-hr-preview@example.com",
        "password": "DisabledHrOps8!",
        "expected_portals": [],
    },
}

results = {
    "test_start": datetime.now(timezone.utc).isoformat(),
    "backend_url": BACKEND_URL,
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
    },
}


def log_test(name, passed, details):
    """Log a test result."""
    results["tests"].append({
        "name": name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    results["summary"]["total"] += 1
    if passed:
        results["summary"]["passed"] += 1
        print(f"✅ {name}")
    else:
        results["summary"]["failed"] += 1
        print(f"❌ {name}")
        print(f"   Details: {details}")


def multi_login(email, password):
    """Perform multi-login and return session_token and portal_tokens."""
    try:
        resp = requests.post(
            f"{BACKEND_URL}/auth/multi-login",
            json={"email": email, "password": password},
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "success": True,
                "session_token": data.get("session_token"),
                "portal_tokens": data.get("portal_tokens", {}),
                "response": data,
            }
        else:
            return {
                "success": False,
                "status_code": resp.status_code,
                "response": resp.text[:500],
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_pm_api(admin_token, pm_token, directory_token):
    """Test PM API access with given tokens."""
    headers = {}
    if admin_token:
        headers["X-Admin-Token"] = admin_token
    if pm_token:
        headers["X-PM-Token"] = pm_token
    if directory_token:
        headers["X-Directory-Token"] = directory_token
    
    try:
        # Test /api/pm/check endpoint
        resp = requests.get(
            f"{BACKEND_URL}/pm/check",
            headers=headers,
            timeout=30,
        )
        return {
            "status_code": resp.status_code,
            "success": resp.status_code == 200,
            "response": resp.json() if resp.status_code == 200 else resp.text[:200],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_shop_api(admin_token, shop_token, directory_token):
    """Test Shop API access with given tokens."""
    headers = {}
    if admin_token:
        headers["X-Admin-Token"] = admin_token
    if shop_token:
        headers["X-Shop-Token"] = shop_token
    if directory_token:
        headers["X-Directory-Token"] = directory_token
    
    try:
        # Test /api/shop/check endpoint
        resp = requests.get(
            f"{BACKEND_URL}/shop/check",
            headers=headers,
            timeout=30,
        )
        return {
            "status_code": resp.status_code,
            "success": resp.status_code == 200,
            "response": resp.json() if resp.status_code == 200 else resp.text[:200],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_admin_api(admin_token, directory_token):
    """Test Admin API access with given tokens."""
    headers = {}
    if admin_token:
        headers["X-Admin-Token"] = admin_token
    if directory_token:
        headers["X-Directory-Token"] = directory_token
    
    try:
        # Test /api/admin/deployment-readiness endpoint
        resp = requests.get(
            f"{BACKEND_URL}/admin/deployment-readiness",
            headers=headers,
            timeout=30,
        )
        return {
            "status_code": resp.status_code,
            "success": resp.status_code == 200,
            "response": resp.json() if resp.status_code == 200 else resp.text[:200],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


print("=" * 80)
print("PM/Shop Authorization Policy Repair - Backend Verification")
print("=" * 80)
print()

# Test 1: Login response portal tokens match assigned portals
print("TEST 1: Login response portal tokens exactly match assigned portals")
print("-" * 80)
for key, creds in CREDENTIALS.items():
    if key == "disabled":
        continue  # Skip disabled user for this test
    
    result = multi_login(creds["email"], creds["password"])
    
    if result["success"]:
        actual_portals = sorted(result["portal_tokens"].keys())
        expected_portals = sorted(creds["expected_portals"])
        
        match = actual_portals == expected_portals
        log_test(
            f"1.{key}: Portal tokens match for {creds['email']}",
            match,
            {
                "expected": expected_portals,
                "actual": actual_portals,
                "match": match,
            },
        )
    else:
        log_test(
            f"1.{key}: Login failed for {creds['email']}",
            False,
            result,
        )

print()

# Test 2: Ordinary Admin token alone no longer unlocks PM or Shop direct APIs
print("TEST 2: Ordinary Admin token alone no longer unlocks PM or Shop APIs")
print("-" * 80)

admin_only_login = multi_login(
    CREDENTIALS["admin_only"]["email"],
    CREDENTIALS["admin_only"]["password"],
)

if admin_only_login["success"]:
    admin_token = admin_only_login["portal_tokens"].get("admin")
    directory_token = admin_only_login["session_token"]
    
    # Test PM API with admin token only (should fail)
    pm_result = test_pm_api(admin_token, None, directory_token)
    log_test(
        "2.1: Admin-only token correctly rejected by PM API",
        pm_result["status_code"] == 401,
        {
            "status_code": pm_result["status_code"],
            "expected": 401,
            "response": pm_result.get("response"),
        },
    )
    
    # Test Shop API with admin token only (should fail)
    shop_result = test_shop_api(admin_token, None, directory_token)
    log_test(
        "2.2: Admin-only token correctly rejected by Shop API",
        shop_result["status_code"] == 401,
        {
            "status_code": shop_result["status_code"],
            "expected": 401,
            "response": shop_result.get("response"),
        },
    )
    
    # Test Admin API with admin token (should succeed)
    admin_result = test_admin_api(admin_token, directory_token)
    log_test(
        "2.3: Admin-only token correctly accepted by Admin API",
        admin_result["status_code"] == 200,
        {
            "status_code": admin_result["status_code"],
            "expected": 200,
        },
    )
else:
    log_test("2: Admin-only login failed", False, admin_only_login)

print()

# Test 3: Admin+PM only unlocks Admin and PM (not Shop)
print("TEST 3: Admin+PM only unlocks Admin and PM (not Shop)")
print("-" * 80)

admin_pm_login = multi_login(
    CREDENTIALS["admin_pm"]["email"],
    CREDENTIALS["admin_pm"]["password"],
)

if admin_pm_login["success"]:
    admin_token = admin_pm_login["portal_tokens"].get("admin")
    pm_token = admin_pm_login["portal_tokens"].get("pm")
    directory_token = admin_pm_login["session_token"]
    
    # Test Admin API (should succeed)
    admin_result = test_admin_api(admin_token, directory_token)
    log_test(
        "3.1: Admin+PM can access Admin API",
        admin_result["status_code"] == 200,
        {"status_code": admin_result["status_code"]},
    )
    
    # Test PM API (should succeed)
    pm_result = test_pm_api(None, pm_token, directory_token)
    log_test(
        "3.2: Admin+PM can access PM API",
        pm_result["status_code"] == 200,
        {"status_code": pm_result["status_code"]},
    )
    
    # Test Shop API (should fail - no shop token)
    shop_result = test_shop_api(admin_token, None, directory_token)
    log_test(
        "3.3: Admin+PM correctly denied Shop API",
        shop_result["status_code"] == 401,
        {"status_code": shop_result["status_code"]},
    )
else:
    log_test("3: Admin+PM login failed", False, admin_pm_login)

print()

# Test 4: Admin+Shop only unlocks Admin and Shop (not PM)
print("TEST 4: Admin+Shop only unlocks Admin and Shop (not PM)")
print("-" * 80)

admin_shop_login = multi_login(
    CREDENTIALS["admin_shop"]["email"],
    CREDENTIALS["admin_shop"]["password"],
)

if admin_shop_login["success"]:
    admin_token = admin_shop_login["portal_tokens"].get("admin")
    shop_token = admin_shop_login["portal_tokens"].get("shop")
    directory_token = admin_shop_login["session_token"]
    
    # Test Admin API (should succeed)
    admin_result = test_admin_api(admin_token, directory_token)
    log_test(
        "4.1: Admin+Shop can access Admin API",
        admin_result["status_code"] == 200,
        {"status_code": admin_result["status_code"]},
    )
    
    # Test Shop API (should succeed)
    shop_result = test_shop_api(None, shop_token, directory_token)
    log_test(
        "4.2: Admin+Shop can access Shop API",
        shop_result["status_code"] == 200,
        {"status_code": shop_result["status_code"]},
    )
    
    # Test PM API (should fail - no pm token)
    pm_result = test_pm_api(admin_token, None, directory_token)
    log_test(
        "4.3: Admin+Shop correctly denied PM API",
        pm_result["status_code"] == 401,
        {"status_code": pm_result["status_code"]},
    )
else:
    log_test("4: Admin+Shop login failed", False, admin_shop_login)

print()

# Test 5: Super Admin still reaches PM and Shop
print("TEST 5: Super Admin still reaches PM and Shop plus all portals")
print("-" * 80)

super_admin_login = multi_login(
    CREDENTIALS["super_admin"]["email"],
    CREDENTIALS["super_admin"]["password"],
)

if super_admin_login["success"]:
    admin_token = super_admin_login["portal_tokens"].get("admin")
    pm_token = super_admin_login["portal_tokens"].get("pm")
    shop_token = super_admin_login["portal_tokens"].get("shop")
    directory_token = super_admin_login["session_token"]
    
    # Test Admin API
    admin_result = test_admin_api(admin_token, directory_token)
    log_test(
        "5.1: Super Admin can access Admin API",
        admin_result["status_code"] == 200,
        {"status_code": admin_result["status_code"]},
    )
    
    # Test PM API with admin token (Super Admin bypass)
    pm_result_admin = test_pm_api(admin_token, None, directory_token)
    log_test(
        "5.2: Super Admin can access PM API with admin token",
        pm_result_admin["status_code"] == 200,
        {"status_code": pm_result_admin["status_code"]},
    )
    
    # Test PM API with pm token
    pm_result_pm = test_pm_api(None, pm_token, directory_token)
    log_test(
        "5.3: Super Admin can access PM API with pm token",
        pm_result_pm["status_code"] == 200,
        {"status_code": pm_result_pm["status_code"]},
    )
    
    # Test Shop API with admin token (Super Admin bypass)
    shop_result_admin = test_shop_api(admin_token, None, directory_token)
    log_test(
        "5.4: Super Admin can access Shop API with admin token",
        shop_result_admin["status_code"] == 200,
        {"status_code": shop_result_admin["status_code"]},
    )
    
    # Test Shop API with shop token
    shop_result_shop = test_shop_api(None, shop_token, directory_token)
    log_test(
        "5.5: Super Admin can access Shop API with shop token",
        shop_result_shop["status_code"] == 200,
        {"status_code": shop_result_shop["status_code"]},
    )
else:
    log_test("5: Super Admin login failed", False, super_admin_login)

print()

# Test 6: PM-only and Shop-only remain properly scoped
print("TEST 6: PM-only and Shop-only remain properly scoped")
print("-" * 80)

pm_only_login = multi_login(
    CREDENTIALS["pm_only"]["email"],
    CREDENTIALS["pm_only"]["password"],
)

if pm_only_login["success"]:
    pm_token = pm_only_login["portal_tokens"].get("pm")
    directory_token = pm_only_login["session_token"]
    
    # Test PM API (should succeed)
    pm_result = test_pm_api(None, pm_token, directory_token)
    log_test(
        "6.1: PM-only can access PM API",
        pm_result["status_code"] == 200,
        {"status_code": pm_result["status_code"]},
    )
    
    # Test Shop API (should fail)
    shop_result = test_shop_api(None, None, directory_token)
    log_test(
        "6.2: PM-only correctly denied Shop API",
        shop_result["status_code"] == 401,
        {"status_code": shop_result["status_code"]},
    )
    
    # Test Admin API (should fail)
    admin_result = test_admin_api(None, directory_token)
    log_test(
        "6.3: PM-only correctly denied Admin API",
        admin_result["status_code"] == 401,
        {"status_code": admin_result["status_code"]},
    )
else:
    log_test("6: PM-only login failed", False, pm_only_login)

shop_only_login = multi_login(
    CREDENTIALS["shop_only"]["email"],
    CREDENTIALS["shop_only"]["password"],
)

if shop_only_login["success"]:
    shop_token = shop_only_login["portal_tokens"].get("shop")
    directory_token = shop_only_login["session_token"]
    
    # Test Shop API (should succeed)
    shop_result = test_shop_api(None, shop_token, directory_token)
    log_test(
        "6.4: Shop-only can access Shop API",
        shop_result["status_code"] == 200,
        {"status_code": shop_result["status_code"]},
    )
    
    # Test PM API (should fail)
    pm_result = test_pm_api(None, None, directory_token)
    log_test(
        "6.5: Shop-only correctly denied PM API",
        pm_result["status_code"] == 401,
        {"status_code": pm_result["status_code"]},
    )
    
    # Test Admin API (should fail)
    admin_result = test_admin_api(None, directory_token)
    log_test(
        "6.6: Shop-only correctly denied Admin API",
        admin_result["status_code"] == 401,
        {"status_code": admin_result["status_code"]},
    )
else:
    log_test("6: Shop-only login failed", False, shop_only_login)

print()

# Test 7: Disabled fixture cannot authenticate
print("TEST 7: Disabled fixture cannot authenticate")
print("-" * 80)

disabled_login = multi_login(
    CREDENTIALS["disabled"]["email"],
    CREDENTIALS["disabled"]["password"],
)

log_test(
    "7.1: Disabled user cannot authenticate",
    not disabled_login["success"],
    {
        "success": disabled_login["success"],
        "status_code": disabled_login.get("status_code"),
        "response": disabled_login.get("response", "")[:200],
    },
)

print()

# Test 8: Core regressions remain good
print("TEST 8: Core regressions remain good")
print("-" * 80)

# Test /api/version
try:
    resp = requests.get(f"{BACKEND_URL}/version", timeout=30)
    log_test(
        "8.1: /api/version returns 200",
        resp.status_code == 200,
        {"status_code": resp.status_code},
    )
except Exception as e:
    log_test("8.1: /api/version failed", False, {"error": str(e)})

# Test /api/health/full
try:
    resp = requests.get(f"{BACKEND_URL}/health/full", timeout=30)
    log_test(
        "8.2: /api/health/full returns 200",
        resp.status_code == 200,
        {"status_code": resp.status_code, "ok": resp.json().get("ok") if resp.status_code == 200 else None},
    )
except Exception as e:
    log_test("8.2: /api/health/full failed", False, {"error": str(e)})

# Test /api/admin/deployment-readiness with super admin
if super_admin_login["success"]:
    admin_token = super_admin_login["portal_tokens"].get("admin")
    directory_token = super_admin_login["session_token"]
    admin_result = test_admin_api(admin_token, directory_token)
    log_test(
        "8.3: /api/admin/deployment-readiness returns 200 with super admin",
        admin_result["status_code"] == 200,
        {"status_code": admin_result["status_code"]},
    )

# Test anonymous access to protected HR route stays blocked
try:
    resp = requests.get(f"{BACKEND_URL}/hr/daily-reports", timeout=30)
    log_test(
        "8.4: Anonymous access to /api/hr/daily-reports blocked",
        resp.status_code == 401,
        {"status_code": resp.status_code},
    )
except Exception as e:
    log_test("8.4: Anonymous HR access test failed", False, {"error": str(e)})

# Test public home stays public
try:
    resp = requests.get("https://masci-audit-hub.preview.emergentagent.com", timeout=30)
    log_test(
        "8.5: Public home stays public",
        resp.status_code == 200,
        {"status_code": resp.status_code},
    )
except Exception as e:
    log_test("8.5: Public home test failed", False, {"error": str(e)})

print()

# Test 9: Verify existing non-fixture identities unchanged
print("TEST 9: Verify existing non-fixture preview identities unchanged")
print("-" * 80)

try:
    with open("/app/test_reports/preview_identity_db_baseline_before.json", "r") as f:
        before = json.load(f)
    with open("/app/test_reports/preview_identity_db_baseline_after.json", "r") as f:
        after = json.load(f)
    
    # Filter out fixture accounts
    fixture_emails = [creds["email"].lower() for creds in CREDENTIALS.values()]
    
    before_users = {u["email"].lower(): u for u in before.get("users", []) if u["email"].lower() not in fixture_emails}
    after_users = {u["email"].lower(): u for u in after.get("users", []) if u["email"].lower() not in fixture_emails}
    
    # Check no deletions
    deleted = set(before_users.keys()) - set(after_users.keys())
    log_test(
        "9.1: No non-fixture users deleted",
        len(deleted) == 0,
        {"deleted_count": len(deleted), "deleted": list(deleted)[:5]},
    )
    
    # Check no portal changes
    portal_changes = []
    for email, before_user in before_users.items():
        if email in after_users:
            after_user = after_users[email]
            if sorted(before_user.get("portals", [])) != sorted(after_user.get("portals", [])):
                portal_changes.append({
                    "email": email,
                    "before": before_user.get("portals", []),
                    "after": after_user.get("portals", []),
                })
    
    log_test(
        "9.2: No portal changes for non-fixture users",
        len(portal_changes) == 0,
        {"changes_count": len(portal_changes), "changes": portal_changes[:3]},
    )
    
    # Check no disablement changes
    disablement_changes = []
    for email, before_user in before_users.items():
        if email in after_users:
            after_user = after_users[email]
            if before_user.get("disabled") != after_user.get("disabled"):
                disablement_changes.append({
                    "email": email,
                    "before": before_user.get("disabled"),
                    "after": after_user.get("disabled"),
                })
    
    log_test(
        "9.3: No disablement changes for non-fixture users",
        len(disablement_changes) == 0,
        {"changes_count": len(disablement_changes), "changes": disablement_changes[:3]},
    )
    
    # Check no password hash presence changes
    hash_changes = []
    for email, before_user in before_users.items():
        if email in after_users:
            after_user = after_users[email]
            if before_user.get("has_password_hash") != after_user.get("has_password_hash"):
                hash_changes.append({
                    "email": email,
                    "before": before_user.get("has_password_hash"),
                    "after": after_user.get("has_password_hash"),
                })
    
    log_test(
        "9.4: No password hash presence changes for non-fixture users",
        len(hash_changes) == 0,
        {"changes_count": len(hash_changes), "changes": hash_changes[:3]},
    )
    
except Exception as e:
    log_test("9: Identity preservation check failed", False, {"error": str(e)})

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total tests: {results['summary']['total']}")
print(f"Passed: {results['summary']['passed']}")
print(f"Failed: {results['summary']['failed']}")
print(f"Pass rate: {results['summary']['passed'] / results['summary']['total'] * 100:.1f}%")
print()

# Save results
results["test_end"] = datetime.now(timezone.utc).isoformat()
with open("/app/pm_shop_authorization_policy_backend_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"Results saved to /app/pm_shop_authorization_policy_backend_results.json")
print()

if results["summary"]["failed"] > 0:
    print("❌ VERIFICATION FAILED - Some tests did not pass")
    sys.exit(1)
else:
    print("✅ VERIFICATION PASSED - All tests passed")
    sys.exit(0)

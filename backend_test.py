#!/usr/bin/env python3
"""
MASCI Platform Backend Pre-Deployment Sweep
Deep backend validation against preview environment before production deployment.

Test Categories:
1. Authentication / session continuity
2. Deployment / operational gates
3. Role / permission continuity
4. Recovery / integrity regressions
5. Performance / readiness sanity
"""

import requests
import json
import sys
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Preview URL from frontend/.env
BASE_URL = "https://backup-forensics.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test credentials from /app/memory/test_credentials.md
SUPER_ADMIN = {
    "email": "jaymn.judd@mascigc.com",
    "password": "Maddix123!"
}

PORTAL_USERS = {
    "admin_only": {
        "email": "ops8-admin-only-preview@example.com",
        "password": "AdminOnlyOps8!"
    },
    "pm": {
        "email": "cert.pm@example.com",
        "password": "CertProof2026!"
    },
    "hr": {
        "email": "cert.hr@example.com",
        "password": "CertProof2026!"
    },
    "safety": {
        "email": "cert.safety@example.com",
        "password": "CertProof2026!"
    },
    "dispatch": {
        "email": "cert.dispatch@example.com",
        "password": "CertProof2026!"
    },
    "shop": {
        "email": "cert.shop@example.com",
        "password": "CertProof2026!"
    },
    "field_leadership": {
        "email": "cert.foreman@example.com",
        "password": "CertProof2026!"
    }
}

# Disabled account for negative testing
DISABLED_USER = {
    "email": "ops8-disabled-hr-preview@example.com",
    "password": "DisabledHrOps8!"
}

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
        self.critical = []
        
    def add_pass(self, test_name: str, details: str = ""):
        self.passed.append({"test": test_name, "details": details})
        print(f"✅ PASS: {test_name}")
        if details:
            print(f"   {details}")
    
    def add_fail(self, test_name: str, details: str, critical: bool = False):
        entry = {"test": test_name, "details": details}
        if critical:
            self.critical.append(entry)
            print(f"❌ CRITICAL FAIL: {test_name}")
        else:
            self.failed.append(entry)
            print(f"❌ FAIL: {test_name}")
        print(f"   {details}")
    
    def add_warning(self, test_name: str, details: str):
        self.warnings.append({"test": test_name, "details": details})
        print(f"⚠️  WARNING: {test_name}")
        print(f"   {details}")
    
    def summary(self) -> Dict[str, Any]:
        return {
            "total_tests": len(self.passed) + len(self.failed) + len(self.critical),
            "passed": len(self.passed),
            "failed": len(self.failed),
            "critical": len(self.critical),
            "warnings": len(self.warnings),
            "pass_rate": f"{(len(self.passed) / max(1, len(self.passed) + len(self.failed) + len(self.critical))) * 100:.1f}%"
        }

results = TestResults()

def login_multi_portal(email: str, password: str) -> Tuple[Optional[Dict], Optional[Dict]]:
    """Login via /api/auth/multi-login and return tokens dict + response"""
    try:
        resp = requests.post(
            f"{API_BASE}/auth/multi-login",
            json={"email": email, "password": password},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            # Return the full tokens structure
            tokens = {
                "session_token": data.get("session_token"),
                "portal_tokens": data.get("portal_tokens", {}),
                "user": data.get("user", {})
            }
            return tokens, data
        return None, resp.json() if resp.text else {"status_code": resp.status_code}
    except Exception as e:
        return None, {"error": str(e)}

def test_endpoint(
    endpoint: str,
    method: str = "GET",
    headers: Optional[Dict] = None,
    json_data: Optional[Dict] = None,
    expected_status: int = 200,
    timeout: int = 10
) -> Tuple[bool, Any]:
    """Test an endpoint and return (success, response_data)"""
    try:
        url = f"{API_BASE}{endpoint}"
        kwargs = {"timeout": timeout}
        if headers:
            kwargs["headers"] = headers
        if json_data:
            kwargs["json"] = json_data
        
        if method == "GET":
            resp = requests.get(url, **kwargs)
        elif method == "POST":
            resp = requests.post(url, **kwargs)
        else:
            return False, {"error": f"Unsupported method: {method}"}
        
        success = resp.status_code == expected_status
        try:
            data = resp.json()
        except:
            data = {"status_code": resp.status_code, "text": resp.text[:200]}
        
        return success, data
    except Exception as e:
        return False, {"error": str(e)}

# ============================================================================
# CATEGORY 1: AUTHENTICATION / SESSION CONTINUITY
# ============================================================================

def test_auth_session():
    print("\n" + "="*80)
    print("CATEGORY 1: AUTHENTICATION / SESSION CONTINUITY")
    print("="*80)
    
    # Test 1.1: Super admin login via multi-login
    print("\n[1.1] Super Admin Login via /api/auth/multi-login")
    tokens, resp = login_multi_portal(SUPER_ADMIN["email"], SUPER_ADMIN["password"])
    if tokens and tokens.get("portal_tokens", {}).get("admin"):
        results.add_pass(
            "Super Admin multi-login",
            f"Token received, portals: {list(tokens.get('portal_tokens', {}).keys())}"
        )
        super_admin_token = tokens["portal_tokens"]["admin"]
        super_admin_session = tokens["session_token"]
    else:
        results.add_fail(
            "Super Admin multi-login",
            f"Login failed: {resp}",
            critical=True
        )
        return None
    
    # Test 1.2: Portal users authentication
    print("\n[1.2] Portal Users Authentication")
    portal_tokens = {}
    portal_sessions = {}
    portal_token_map = {
        "admin_only": "admin",
        "pm": "pm",
        "hr": "hr",
        "safety": "safety",
        "dispatch": "dispatch",
        "shop": "shop",
        "field_leadership": "field_leadership"
    }
    
    for role, creds in PORTAL_USERS.items():
        tokens, resp = login_multi_portal(creds["email"], creds["password"])
        if tokens:
            portal_key = portal_token_map.get(role, role)
            token = tokens.get("portal_tokens", {}).get(portal_key)
            session = tokens.get("session_token")
            
            if token:
                results.add_pass(
                    f"{role} user login",
                    f"Email: {creds['email']}"
                )
                portal_tokens[role] = token
                portal_sessions[role] = session
            else:
                results.add_fail(
                    f"{role} user login",
                    f"No {portal_key} token for {creds['email']}: {list(tokens.get('portal_tokens', {}).keys())}",
                    critical=True
                )
        else:
            results.add_fail(
                f"{role} user login",
                f"Failed for {creds['email']}: {resp}",
                critical=True
            )
    
    # Test 1.3: Disabled account behavior
    print("\n[1.3] Disabled Account Behavior")
    tokens, resp = login_multi_portal(DISABLED_USER["email"], DISABLED_USER["password"])
    if not tokens:
        results.add_pass(
            "Disabled account rejection",
            f"Correctly rejected: {resp.get('detail', resp)}"
        )
    else:
        results.add_fail(
            "Disabled account rejection",
            "Disabled account was allowed to login",
            critical=True
        )
    
    # Test 1.4: /api/auth/me-directory for portal users
    print("\n[1.4] /api/auth/me-directory for Portal Users")
    # Test with super admin session token
    success, data = test_endpoint(
        "/auth/me-directory",
        headers={"X-Directory-Token": super_admin_session}
    )
    if success and data.get("user", {}).get("email"):
        results.add_pass(
            "/api/auth/me-directory for super admin",
            f"Email: {data.get('user', {}).get('email')}"
        )
    else:
        results.add_fail(
            "/api/auth/me-directory for super admin",
            f"Failed: {data}"
        )
    
    # Test with other portal users
    for role, session in portal_sessions.items():
        if session:
            success, data = test_endpoint(
                "/auth/me-directory",
                headers={"X-Directory-Token": session}
            )
            if success and data.get("user", {}).get("email"):
                results.add_pass(
                    f"/api/auth/me-directory for {role}",
                    f"Email: {data.get('user', {}).get('email')}"
                )
            else:
                results.add_fail(
                    f"/api/auth/me-directory for {role}",
                    f"Failed: {data}"
                )
    
    # Test 1.5: Admin-gated routes require valid token
    print("\n[1.5] Admin-Gated Routes Require Valid Token")
    # Test without token
    success, data = test_endpoint("/admin/deployment-readiness", expected_status=401)
    if not success and data.get("status_code") == 401:
        results.add_pass(
            "Admin route blocks unauthenticated",
            "/admin/deployment-readiness correctly returns 401"
        )
    else:
        results.add_fail(
            "Admin route blocks unauthenticated",
            f"Expected 401, got: {data}"
        )
    
    # Test with valid tokens (both admin token and directory session)
    success, data = test_endpoint(
        "/admin/deployment-readiness",
        headers={
            "X-Admin-Token": super_admin_token,
            "X-Directory-Token": super_admin_session
        }
    )
    if success:
        results.add_pass(
            "Admin route accepts valid token",
            "/admin/deployment-readiness accessible with admin token"
        )
    else:
        results.add_fail(
            "Admin route accepts valid token",
            f"Failed with valid token: {data}",
            critical=True
        )
    
    return (super_admin_token, super_admin_session)

# ============================================================================
# CATEGORY 2: DEPLOYMENT / OPERATIONAL GATES
# ============================================================================

def test_deployment_gates(admin_token: str, session_token: str):
    print("\n" + "="*80)
    print("CATEGORY 2: DEPLOYMENT / OPERATIONAL GATES")
    print("="*80)
    
    headers = {
        "X-Admin-Token": admin_token,
        "X-Directory-Token": session_token
    }
    
    # Test 2.1: /api/admin/deployment-readiness
    print("\n[2.1] /api/admin/deployment-readiness")
    success, data = test_endpoint("/admin/deployment-readiness", headers=headers, timeout=30)
    if success:
        decision = data.get("decision")
        # Check if unknown_audit_status_count exists in response
        if "unknown_audit_status_count" in data:
            unknown_audit_count = data.get("unknown_audit_status_count", -1)
        else:
            # Field not present - check if it's in a nested structure
            unknown_audit_count = None
            for key in ["trust_score", "notification_delivery", "bootstrap"]:
                if key in data and isinstance(data[key], dict):
                    if "unknown_audit_status_count" in data[key]:
                        unknown_audit_count = data[key]["unknown_audit_status_count"]
                        break
        
        regression_count = data.get("regression_gate_count", -1)
        
        if decision == "pass" or decision == "PASS":
            results.add_pass(
                "/admin/deployment-readiness decision",
                f"Decision: {decision}, regressions: {regression_count}"
            )
        else:
            results.add_fail(
                "/admin/deployment-readiness decision",
                f"Decision: {decision}, regressions: {regression_count}",
                critical=True
            )
        
        # Only check unknown_audit_count if it's present
        if unknown_audit_count is not None:
            if unknown_audit_count == 0:
                results.add_pass(
                    "/admin/deployment-readiness unknown audit status",
                    "No unknown audit statuses"
                )
            else:
                results.add_fail(
                    "/admin/deployment-readiness unknown audit status",
                    f"Unknown audit status count: {unknown_audit_count}",
                    critical=True
                )
        else:
            results.add_warning(
                "/admin/deployment-readiness unknown audit status",
                "unknown_audit_status_count field not found in response"
            )
        
        if regression_count >= 0:
            results.add_pass(
                "/admin/deployment-readiness regression count",
                f"Regression gate count: {regression_count}"
            )
        else:
            results.add_warning(
                "/admin/deployment-readiness regression count",
                f"Regression count not reported or negative: {regression_count}"
            )
    else:
        results.add_fail(
            "/admin/deployment-readiness",
            f"Endpoint failed: {data}",
            critical=True
        )
    
    # Test 2.2: /api/admin/deploy-readiness
    print("\n[2.2] /api/admin/deploy-readiness")
    success, data = test_endpoint("/admin/deploy-readiness", headers=headers)
    if success:
        results.add_pass(
            "/admin/deploy-readiness",
            f"Endpoint reachable, keys: {list(data.keys())[:5]}"
        )
    else:
        results.add_fail(
            "/admin/deploy-readiness",
            f"Endpoint failed: {data}",
            critical=True
        )
    
    # Test 2.3: /api/admin/platform-trust/validate
    print("\n[2.3] /api/admin/platform-trust/validate")
    success, data = test_endpoint("/admin/platform-trust/validate", headers=headers, timeout=60)
    if success:
        # Check if unknown_audit_status_count exists
        unknown_audit_count = data.get("unknown_audit_status_count")
        
        # Check for secrets in response
        response_str = json.dumps(data).lower()
        secret_keywords = ["password", "api_key", "secret_key", "credential"]
        found_secrets = [kw for kw in secret_keywords if kw in response_str]
        
        if not found_secrets:
            results.add_pass(
                "/admin/platform-trust/validate secret-free",
                "No secrets detected in response"
            )
        else:
            results.add_fail(
                "/admin/platform-trust/validate secret-free",
                f"Potential secrets found: {found_secrets}",
                critical=True
            )
        
        if unknown_audit_count is not None:
            if unknown_audit_count == 0:
                results.add_pass(
                    "/admin/platform-trust/validate unknown audit status",
                    "No unknown audit statuses"
                )
            else:
                results.add_fail(
                    "/admin/platform-trust/validate unknown audit status",
                    f"Unknown audit status count: {unknown_audit_count}",
                    critical=True
                )
        else:
            results.add_warning(
                "/admin/platform-trust/validate unknown audit status",
                "unknown_audit_status_count field not found in response"
            )
    else:
        results.add_fail(
            "/admin/platform-trust/validate",
            f"Endpoint failed: {data}",
            critical=True
        )
    
    # Test 2.4: /api/admin/operations-trust-center
    print("\n[2.4] /api/admin/operations-trust-center")
    success, data = test_endpoint("/admin/operations-trust-center", headers=headers)
    if success:
        results.add_pass(
            "/admin/operations-trust-center",
            f"Endpoint reachable, keys: {list(data.keys())[:5]}"
        )
    else:
        results.add_fail(
            "/admin/operations-trust-center",
            f"Endpoint failed: {data}",
            critical=True
        )
    
    # Test 2.5: Health endpoints
    print("\n[2.5] Health Endpoints")
    health_endpoints = [
        "/health",
        "/healthz",
        "/ready",
        "/health/full"
    ]
    
    for endpoint in health_endpoints:
        success, data = test_endpoint(endpoint)
        if success:
            results.add_pass(
                f"Health endpoint {endpoint}",
                f"Status: {data.get('status', 'ok')}"
            )
        else:
            results.add_fail(
                f"Health endpoint {endpoint}",
                f"Failed: {data}",
                critical=True
            )

# ============================================================================
# CATEGORY 3: ROLE / PERMISSION CONTINUITY
# ============================================================================

def test_role_permissions():
    print("\n" + "="*80)
    print("CATEGORY 3: ROLE / PERMISSION CONTINUITY")
    print("="*80)
    
    # Test 3.1: Admin-only user access
    print("\n[3.1] Admin-Only User Access")
    tokens, resp = login_multi_portal(
        PORTAL_USERS["admin_only"]["email"],
        PORTAL_USERS["admin_only"]["password"]
    )
    if tokens:
        admin_token = tokens.get("portal_tokens", {}).get("admin")
        session_token = tokens.get("session_token")
        if admin_token and session_token:
            # Should access admin routes
            success, data = test_endpoint(
                "/admin/deployment-readiness",
                headers={
                    "X-Admin-Token": admin_token,
                    "X-Directory-Token": session_token
                }
            )
            if success:
                results.add_pass(
                    "Admin-only user admin access",
                    "Can access /admin/deployment-readiness"
                )
            else:
                results.add_fail(
                    "Admin-only user admin access",
                    f"Cannot access admin route: {data}",
                    critical=True
                )
        else:
            results.add_fail(
                "Admin-only user admin access",
                "No admin token or session token in response",
                critical=True
            )
    
    # Test 3.2: PM user access
    print("\n[3.2] PM User Access")
    tokens, resp = login_multi_portal(
        PORTAL_USERS["pm"]["email"],
        PORTAL_USERS["pm"]["password"]
    )
    if tokens:
        pm_token = tokens.get("portal_tokens", {}).get("pm")
        if pm_token:
            # PM should NOT access admin namespace
            success, data = test_endpoint(
                "/admin/deployment-readiness",
                headers={"X-PM-Token": pm_token},
                expected_status=401
            )
            if not success and data.get("status_code") == 401:
                results.add_pass(
                    "PM user blocked from admin namespace",
                    "Correctly blocked from /admin/deployment-readiness"
                )
            else:
                results.add_fail(
                    "PM user blocked from admin namespace",
                    f"PM should be blocked but got: {data}",
                    critical=True
                )
    
    # Test 3.3: HR user access
    print("\n[3.3] HR User Access")
    tokens, resp = login_multi_portal(
        PORTAL_USERS["hr"]["email"],
        PORTAL_USERS["hr"]["password"]
    )
    if tokens:
        session = tokens.get("session_token")
        if session:
            success, data = test_endpoint(
                "/auth/me-directory",
                headers={"X-Directory-Token": session}
            )
            if success:
                results.add_pass(
                    "HR user session",
                    f"HR user authenticated: {data.get('user', {}).get('email')}"
                )
            else:
                results.add_fail(
                    "HR user session",
                    f"HR user session failed: {data}"
                )
    
    # Test 3.4: Safety user access
    print("\n[3.4] Safety User Access")
    tokens, resp = login_multi_portal(
        PORTAL_USERS["safety"]["email"],
        PORTAL_USERS["safety"]["password"]
    )
    if tokens:
        session = tokens.get("session_token")
        if session:
            success, data = test_endpoint(
                "/auth/me-directory",
                headers={"X-Directory-Token": session}
            )
            if success:
                results.add_pass(
                    "Safety user session",
                    f"Safety user authenticated: {data.get('user', {}).get('email')}"
                )
            else:
                results.add_fail(
                    "Safety user session",
                    f"Safety user session failed: {data}"
                )
    
    # Test 3.5: Dispatch user access
    print("\n[3.5] Dispatch User Access")
    tokens, resp = login_multi_portal(
        PORTAL_USERS["dispatch"]["email"],
        PORTAL_USERS["dispatch"]["password"]
    )
    if tokens:
        session = tokens.get("session_token")
        if session:
            success, data = test_endpoint(
                "/auth/me-directory",
                headers={"X-Directory-Token": session}
            )
            if success:
                results.add_pass(
                    "Dispatch user session",
                    f"Dispatch user authenticated: {data.get('user', {}).get('email')}"
                )
            else:
                results.add_fail(
                    "Dispatch user session",
                    f"Dispatch user session failed: {data}"
                )
    
    # Test 3.6: Shop user access
    print("\n[3.6] Shop User Access")
    tokens, resp = login_multi_portal(
        PORTAL_USERS["shop"]["email"],
        PORTAL_USERS["shop"]["password"]
    )
    if tokens:
        session = tokens.get("session_token")
        if session:
            success, data = test_endpoint(
                "/auth/me-directory",
                headers={"X-Directory-Token": session}
            )
            if success:
                results.add_pass(
                    "Shop user session",
                    f"Shop user authenticated: {data.get('user', {}).get('email')}"
                )
            else:
                results.add_fail(
                    "Shop user session",
                    f"Shop user session failed: {data}"
                )
    
    # Test 3.7: Field Leadership user access
    print("\n[3.7] Field Leadership User Access")
    tokens, resp = login_multi_portal(
        PORTAL_USERS["field_leadership"]["email"],
        PORTAL_USERS["field_leadership"]["password"]
    )
    if tokens:
        session = tokens.get("session_token")
        if session:
            success, data = test_endpoint(
                "/auth/me-directory",
                headers={"X-Directory-Token": session}
            )
            if success:
                results.add_pass(
                    "Field Leadership user session",
                    f"FL user authenticated: {data.get('user', {}).get('email')}"
                )
            else:
                results.add_fail(
                    "Field Leadership user session",
                    f"FL user session failed: {data}"
                )

# ============================================================================
# CATEGORY 4: RECOVERY / INTEGRITY REGRESSIONS
# ============================================================================

def test_recovery_integrity(admin_token: str, session_token: str):
    print("\n" + "="*80)
    print("CATEGORY 4: RECOVERY / INTEGRITY REGRESSIONS")
    print("="*80)
    
    headers = {
        "X-Admin-Token": admin_token,
        "X-Directory-Token": session_token
    }
    
    # Test 4.1: /api/admin/recovery/snapshot
    print("\n[4.1] /api/admin/recovery/snapshot")
    success, data = test_endpoint("/admin/recovery/snapshot", headers=headers, timeout=60)
    if success:
        results.add_pass(
            "/admin/recovery/snapshot",
            f"Endpoint reachable, keys: {list(data.keys())[:5]}"
        )
    else:
        results.add_fail(
            "/admin/recovery/snapshot",
            f"Endpoint failed: {data}",
            critical=True
        )
    
    # Test 4.2: /api/admin/trust-spine
    print("\n[4.2] /api/admin/trust-spine")
    success, data = test_endpoint("/admin/trust-spine", headers=headers)
    if success:
        results.add_pass(
            "/admin/trust-spine",
            f"Endpoint reachable, keys: {list(data.keys())[:5]}"
        )
    else:
        results.add_fail(
            "/admin/trust-spine",
            f"Endpoint failed: {data}",
            critical=True
        )
    
    # Test 4.3: /api/admin/integrations/truth-status
    print("\n[4.3] /api/admin/integrations/truth-status")
    success, data = test_endpoint("/admin/integrations/truth-status", headers=headers)
    if success:
        results.add_pass(
            "/admin/integrations/truth-status",
            f"Endpoint reachable, keys: {list(data.keys())[:5]}"
        )
    else:
        results.add_fail(
            "/admin/integrations/truth-status",
            f"Endpoint failed: {data}",
            critical=True
        )
    
    # Test 4.4: /api/admin/backup-verification/state
    print("\n[4.4] /api/admin/backup-verification/state")
    success, data = test_endpoint("/admin/backup-verification/state", headers=headers)
    if success:
        results.add_pass(
            "/admin/backup-verification/state",
            f"Endpoint reachable, keys: {list(data.keys())[:5]}"
        )
    else:
        results.add_fail(
            "/admin/backup-verification/state",
            f"Endpoint failed: {data}",
            critical=True
        )
    
    # Test 4.5: /api/admin/scheduler-runs
    print("\n[4.5] /api/admin/scheduler-runs")
    success, data = test_endpoint("/admin/scheduler-runs", headers=headers)
    if success:
        results.add_pass(
            "/admin/scheduler-runs",
            f"Endpoint reachable, runs count: {len(data) if isinstance(data, list) else 'N/A'}"
        )
    else:
        results.add_fail(
            "/admin/scheduler-runs",
            f"Endpoint failed: {data}",
            critical=True
        )
    
    # Test 4.6: Audit status contract (no unknown statuses)
    print("\n[4.6] Audit Status Contract Verification")
    # Check deployment-readiness for unknown audit statuses
    success, data = test_endpoint("/admin/deployment-readiness", headers=headers, timeout=30)
    if success:
        unknown_count = data.get("unknown_audit_status_count")
        if unknown_count is not None:
            if unknown_count == 0:
                results.add_pass(
                    "Audit status contract (deployment-readiness)",
                    "No unknown audit statuses in deployment-readiness"
                )
            else:
                results.add_fail(
                    "Audit status contract (deployment-readiness)",
                    f"Unknown audit status count: {unknown_count}",
                    critical=True
                )
        else:
            results.add_warning(
                "Audit status contract (deployment-readiness)",
                "unknown_audit_status_count field not in response - may be in nested structure"
            )
    
    # Check platform-trust/validate for unknown audit statuses
    success, data = test_endpoint("/admin/platform-trust/validate", headers=headers, timeout=60)
    if success:
        unknown_count = data.get("unknown_audit_status_count")
        if unknown_count is not None:
            if unknown_count == 0:
                results.add_pass(
                    "Audit status contract (platform-trust)",
                    "No unknown audit statuses in platform-trust/validate"
                )
            else:
                results.add_fail(
                    "Audit status contract (platform-trust)",
                    f"Unknown audit status count: {unknown_count}",
                    critical=True
                )
        else:
            results.add_warning(
                "Audit status contract (platform-trust)",
                "unknown_audit_status_count field not in response - may be in nested structure"
            )

# ============================================================================
# CATEGORY 5: PERFORMANCE / READINESS SANITY
# ============================================================================

def test_performance_readiness(admin_token: str, session_token: str):
    print("\n" + "="*80)
    print("CATEGORY 5: PERFORMANCE / READINESS SANITY")
    print("="*80)
    
    headers = {
        "X-Admin-Token": admin_token,
        "X-Directory-Token": session_token
    }
    
    # Test 5.1: Response time checks
    print("\n[5.1] Response Time Checks")
    import time
    
    endpoints_to_check = [
        ("/health", 10),
        ("/admin/deployment-readiness", 30),
        ("/admin/platform-trust/validate", 60)
    ]
    
    for endpoint, timeout_val in endpoints_to_check:
        start = time.time()
        success, data = test_endpoint(endpoint, headers=headers, timeout=timeout_val)
        elapsed = time.time() - start
        
        if success:
            if elapsed < 5.0:
                results.add_pass(
                    f"Response time {endpoint}",
                    f"Responded in {elapsed:.2f}s"
                )
            elif elapsed < 10.0:
                results.add_warning(
                    f"Response time {endpoint}",
                    f"Slow response: {elapsed:.2f}s"
                )
            else:
                results.add_fail(
                    f"Response time {endpoint}",
                    f"Very slow response: {elapsed:.2f}s"
                )
        else:
            results.add_fail(
                f"Response time {endpoint}",
                f"Endpoint failed: {data}"
            )
    
    # Test 5.2: Check for obvious failures
    print("\n[5.2] Obvious Failure Detection")
    critical_endpoints = [
        ("/admin/deployment-readiness", 30),
        ("/admin/deploy-readiness", 30),
        ("/admin/operations-trust-center", 30)
    ]
    
    failed_endpoints = []
    for endpoint, timeout_val in critical_endpoints:
        success, data = test_endpoint(endpoint, headers=headers, timeout=timeout_val)
        if not success:
            failed_endpoints.append(endpoint)
    
    if not failed_endpoints:
        results.add_pass(
            "Critical endpoints availability",
            "All critical endpoints responding"
        )
    else:
        results.add_fail(
            "Critical endpoints availability",
            f"Failed endpoints: {failed_endpoints}",
            critical=True
        )

# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

def main():
    print("\n" + "="*80)
    print("MASCI PLATFORM BACKEND PRE-DEPLOYMENT SWEEP")
    print("="*80)
    print(f"Preview URL: {BASE_URL}")
    print(f"Test Start: {datetime.now().isoformat()}")
    print("="*80)
    
    # Category 1: Authentication / Session Continuity
    auth_result = test_auth_session()
    if not auth_result:
        print("\n❌ CRITICAL: Super Admin authentication failed. Cannot continue.")
        sys.exit(1)
    
    admin_token, session_token = auth_result
    
    # Category 2: Deployment / Operational Gates
    test_deployment_gates(admin_token, session_token)
    
    # Category 3: Role / Permission Continuity
    test_role_permissions()
    
    # Category 4: Recovery / Integrity Regressions
    test_recovery_integrity(admin_token, session_token)
    
    # Category 5: Performance / Readiness Sanity
    test_performance_readiness(admin_token, session_token)
    
    # Print Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    summary = results.summary()
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']} ✅")
    print(f"Failed: {summary['failed']} ❌")
    print(f"Critical: {summary['critical']} 🔴")
    print(f"Warnings: {summary['warnings']} ⚠️")
    print(f"Pass Rate: {summary['pass_rate']}")
    
    if results.critical:
        print("\n🔴 CRITICAL FAILURES:")
        for item in results.critical:
            print(f"  - {item['test']}: {item['details']}")
    
    if results.failed:
        print("\n❌ FAILURES:")
        for item in results.failed:
            print(f"  - {item['test']}: {item['details']}")
    
    if results.warnings:
        print("\n⚠️  WARNINGS:")
        for item in results.warnings:
            print(f"  - {item['test']}: {item['details']}")
    
    print("\n" + "="*80)
    print(f"Test End: {datetime.now().isoformat()}")
    print("="*80)
    
    # Exit with appropriate code
    if results.critical:
        print("\n❌ DEPLOYMENT BLOCKED: Critical failures detected")
        sys.exit(1)
    elif results.failed:
        print("\n⚠️  DEPLOYMENT RISKY: Non-critical failures detected")
        sys.exit(1)
    else:
        print("\n✅ DEPLOYMENT READY: All tests passed")
        sys.exit(0)

if __name__ == "__main__":
    main()

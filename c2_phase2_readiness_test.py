#!/usr/bin/env python3
"""
C2 Phase 2 Pre-Deployment Readiness Review
READ-ONLY verification against preview environment
https://masci-audit-hub.preview.emergentagent.com
"""

import requests
import json
import time
from typing import Dict, List, Any, Tuple

# Preview environment configuration
PREVIEW_BASE_URL = "https://masci-audit-hub.preview.emergentagent.com"
API_BASE_URL = f"{PREVIEW_BASE_URL}/api"

# Test credentials from /app/memory/test_credentials.md
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"

# Invalid credentials for negative testing
INVALID_EMAIL = "invalid@example.com"
INVALID_PASSWORD = "WrongPassword123!"

# Test results storage
test_results = {
    "1_release_runtime_identity": {},
    "2_authentication_session_logout": {},
    "3_core_workflows": {},
    "4_daily_report_critical_path": {},
    "5_notifications_integrations": {},
    "6_security_deployment_blockers": {},
    "7_rollback_operational_safety": {},
    "deployment_blockers": []
}


def log_test(category: str, test_name: str, status: str, details: Any):
    """Log test result"""
    if category not in test_results:
        test_results[category] = {}
    test_results[category][test_name] = {
        "status": status,
        "details": details
    }
    print(f"[{status}] {category} - {test_name}")
    if status == "FAIL":
        print(f"  Details: {details}")


def add_deployment_blocker(blocker: str):
    """Add a deployment blocker"""
    test_results["deployment_blockers"].append(blocker)
    print(f"🚨 DEPLOYMENT BLOCKER: {blocker}")


# ============================================================================
# 1. RELEASE/RUNTIME IDENTITY
# ============================================================================

def test_version_endpoint():
    """Test GET /api/version for release identity"""
    try:
        # Make 3 repeated calls to verify consistency
        responses = []
        for i in range(3):
            resp = requests.get(f"{API_BASE_URL}/version", timeout=10)
            responses.append({
                "status_code": resp.status_code,
                "data": resp.json() if resp.status_code == 200 else None,
                "headers": dict(resp.headers)
            })
            time.sleep(0.5)
        
        # Check all responses are 200
        if all(r["status_code"] == 200 for r in responses):
            # Check consistency across calls
            first_data = responses[0]["data"]
            all_consistent = all(
                r["data"].get("commit") == first_data.get("commit") and
                r["data"].get("source_hash") == first_data.get("source_hash")
                for r in responses
            )
            
            if all_consistent:
                log_test("1_release_runtime_identity", "version_endpoint_consistency", "PASS", {
                    "commit": first_data.get("commit"),
                    "source_hash": first_data.get("source_hash"),
                    "frontend_backend_release_match": first_data.get("frontend_backend_release_match"),
                    "calls_made": 3,
                    "all_consistent": True
                })
            else:
                log_test("1_release_runtime_identity", "version_endpoint_consistency", "FAIL", 
                         "Version data inconsistent across repeated calls")
                add_deployment_blocker("Version endpoint returns inconsistent data across calls")
        else:
            log_test("1_release_runtime_identity", "version_endpoint_consistency", "FAIL",
                     f"Non-200 responses: {[r['status_code'] for r in responses]}")
            add_deployment_blocker(f"Version endpoint not returning 200: {responses[0]['status_code']}")
    except Exception as e:
        log_test("1_release_runtime_identity", "version_endpoint_consistency", "FAIL", str(e))
        add_deployment_blocker(f"Version endpoint error: {str(e)}")


def test_health_endpoints():
    """Test GET /api/health and /api/health/full"""
    try:
        # Test /api/health
        health_resp = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if health_resp.status_code == 200:
            health_data = health_resp.json()
            if health_data.get("ok") is True:
                log_test("1_release_runtime_identity", "health_endpoint", "PASS", {
                    "ok": True,
                    "runtime_identity_status": health_data.get("runtime_identity", {}).get("status")
                })
            else:
                log_test("1_release_runtime_identity", "health_endpoint", "FAIL", 
                         f"Health check returned ok=False: {health_data}")
                add_deployment_blocker("Health endpoint reports unhealthy state")
        else:
            log_test("1_release_runtime_identity", "health_endpoint", "FAIL",
                     f"Status code: {health_resp.status_code}")
            add_deployment_blocker(f"Health endpoint not returning 200: {health_resp.status_code}")
        
        # Test /api/health/full
        full_health_resp = requests.get(f"{API_BASE_URL}/health/full", timeout=10)
        if full_health_resp.status_code == 200:
            full_health_data = full_health_resp.json()
            if full_health_data.get("ok") is True:
                log_test("1_release_runtime_identity", "health_full_endpoint", "PASS", {
                    "ok": True,
                    "mongo": full_health_data.get("mongo"),
                    "scheduler": full_health_data.get("scheduler"),
                    "backup_recent": full_health_data.get("backup_recent"),
                    "runtime_identity_ok": full_health_data.get("runtime_identity_ok")
                })
            else:
                log_test("1_release_runtime_identity", "health_full_endpoint", "FAIL",
                         f"Full health check returned ok=False: {full_health_data}")
                add_deployment_blocker("Full health endpoint reports unhealthy subsystems")
        else:
            log_test("1_release_runtime_identity", "health_full_endpoint", "FAIL",
                     f"Status code: {full_health_resp.status_code}")
            add_deployment_blocker(f"Full health endpoint not returning 200: {full_health_resp.status_code}")
    except Exception as e:
        log_test("1_release_runtime_identity", "health_endpoints", "FAIL", str(e))
        add_deployment_blocker(f"Health endpoints error: {str(e)}")


# ============================================================================
# 2. AUTHENTICATION/SESSION/LOGOUT
# ============================================================================

def test_multi_login_valid():
    """Test POST /api/auth/multi-login with valid credentials"""
    try:
        payload = {
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }
        resp = requests.post(f"{API_BASE_URL}/auth/multi-login", json=payload, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("session_token") and data.get("portal_tokens"):
                portals = list(data["portal_tokens"].keys())
                log_test("2_authentication_session_logout", "multi_login_valid", "PASS", {
                    "has_session_token": True,
                    "portals": portals,
                    "portal_count": len(portals)
                })
                return data  # Return for use in other tests
            else:
                log_test("2_authentication_session_logout", "multi_login_valid", "FAIL",
                         "Missing session_token or portal_tokens in response")
                add_deployment_blocker("Multi-login not returning required tokens")
                return None
        else:
            log_test("2_authentication_session_logout", "multi_login_valid", "FAIL",
                     f"Status code: {resp.status_code}, Body: {resp.text}")
            add_deployment_blocker(f"Multi-login failing with valid credentials: {resp.status_code}")
            return None
    except Exception as e:
        log_test("2_authentication_session_logout", "multi_login_valid", "FAIL", str(e))
        add_deployment_blocker(f"Multi-login error: {str(e)}")
        return None


def test_multi_login_invalid():
    """Test POST /api/auth/multi-login with invalid credentials"""
    try:
        payload = {
            "email": INVALID_EMAIL,
            "password": INVALID_PASSWORD
        }
        resp = requests.post(f"{API_BASE_URL}/auth/multi-login", json=payload, timeout=10)
        
        if resp.status_code in [401, 403]:
            log_test("2_authentication_session_logout", "multi_login_invalid", "PASS",
                     f"Correctly rejected with status {resp.status_code}")
        else:
            log_test("2_authentication_session_logout", "multi_login_invalid", "FAIL",
                     f"Unexpected status code: {resp.status_code}")
            if resp.status_code == 200:
                add_deployment_blocker("Invalid credentials accepted - authentication bypass detected")
    except Exception as e:
        log_test("2_authentication_session_logout", "multi_login_invalid", "FAIL", str(e))


def test_canonical_multi_logout(auth_data: Dict):
    """Test POST /api/auth/multi-logout"""
    if not auth_data:
        log_test("2_authentication_session_logout", "canonical_multi_logout", "UNVERIFIED",
                 "Skipped - no valid auth data")
        return
    
    try:
        headers = {
            "X-Directory-Token": auth_data["session_token"]
        }
        resp = requests.post(f"{API_BASE_URL}/auth/multi-logout", headers=headers, timeout=10)
        
        if resp.status_code == 200:
            log_test("2_authentication_session_logout", "canonical_multi_logout", "PASS",
                     "Logout successful")
        else:
            log_test("2_authentication_session_logout", "canonical_multi_logout", "FAIL",
                     f"Status code: {resp.status_code}")
            add_deployment_blocker(f"Canonical logout endpoint failing: {resp.status_code}")
    except Exception as e:
        log_test("2_authentication_session_logout", "canonical_multi_logout", "FAIL", str(e))


def test_compatibility_logout_wrappers(auth_data: Dict):
    """Test /api/admin/logout and /api/pm/logout compatibility wrappers"""
    if not auth_data:
        log_test("2_authentication_session_logout", "compatibility_logout_wrappers", "UNVERIFIED",
                 "Skipped - no valid auth data")
        return
    
    # Get fresh auth for each wrapper test
    try:
        # Test /api/admin/logout
        admin_auth = test_multi_login_valid()
        if admin_auth and "admin" in admin_auth.get("portal_tokens", {}):
            headers = {
                "X-Admin-Token": admin_auth["portal_tokens"]["admin"],
                "X-Directory-Token": admin_auth["session_token"]
            }
            resp = requests.post(f"{API_BASE_URL}/admin/logout", headers=headers, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("canonical_logout") == "/api/auth/multi-logout":
                    log_test("2_authentication_session_logout", "admin_logout_wrapper", "PASS",
                             "Wrapper correctly references canonical endpoint")
                else:
                    log_test("2_authentication_session_logout", "admin_logout_wrapper", "FAIL",
                             "Wrapper does not reference canonical endpoint")
            else:
                log_test("2_authentication_session_logout", "admin_logout_wrapper", "FAIL",
                         f"Status code: {resp.status_code}")
        
        # Test /api/pm/logout
        pm_auth = test_multi_login_valid()
        if pm_auth and "pm" in pm_auth.get("portal_tokens", {}):
            headers = {
                "X-PM-Token": pm_auth["portal_tokens"]["pm"],
                "X-Directory-Token": pm_auth["session_token"]
            }
            resp = requests.post(f"{API_BASE_URL}/pm/logout", headers=headers, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("canonical_logout") == "/api/auth/multi-logout":
                    log_test("2_authentication_session_logout", "pm_logout_wrapper", "PASS",
                             "Wrapper correctly references canonical endpoint")
                else:
                    log_test("2_authentication_session_logout", "pm_logout_wrapper", "FAIL",
                             "Wrapper does not reference canonical endpoint")
            else:
                log_test("2_authentication_session_logout", "pm_logout_wrapper", "FAIL",
                         f"Status code: {resp.status_code}")
    except Exception as e:
        log_test("2_authentication_session_logout", "compatibility_logout_wrappers", "FAIL", str(e))


def test_old_token_after_relogin():
    """Test that old tokens are invalid after fresh re-login"""
    try:
        # First login
        first_auth = test_multi_login_valid()
        if not first_auth:
            log_test("2_authentication_session_logout", "old_token_after_relogin", "UNVERIFIED",
                     "Skipped - first login failed")
            return
        
        old_admin_token = first_auth["portal_tokens"].get("admin")
        old_directory_token = first_auth["session_token"]
        
        # Logout
        headers = {"X-Directory-Token": old_directory_token}
        requests.post(f"{API_BASE_URL}/auth/multi-logout", headers=headers, timeout=10)
        
        # Second login
        second_auth = test_multi_login_valid()
        if not second_auth:
            log_test("2_authentication_session_logout", "old_token_after_relogin", "UNVERIFIED",
                     "Skipped - second login failed")
            return
        
        new_directory_token = second_auth["session_token"]
        
        # Try to use old admin token with new directory token
        headers = {
            "X-Admin-Token": old_admin_token,
            "X-Directory-Token": new_directory_token
        }
        resp = requests.get(f"{API_BASE_URL}/daily-reports?limit=1", headers=headers, timeout=10)
        
        if resp.status_code == 401:
            log_test("2_authentication_session_logout", "old_token_after_relogin", "PASS",
                     "Old token correctly rejected after relogin")
        else:
            log_test("2_authentication_session_logout", "old_token_after_relogin", "FAIL",
                     f"Old token still accepted: {resp.status_code}")
            add_deployment_blocker("Session tokens not properly invalidated on logout/relogin")
    except Exception as e:
        log_test("2_authentication_session_logout", "old_token_after_relogin", "FAIL", str(e))


def test_api_replay_after_logout():
    """Test that API calls fail after logout"""
    try:
        # Login
        auth = test_multi_login_valid()
        if not auth:
            log_test("2_authentication_session_logout", "api_replay_after_logout", "UNVERIFIED",
                     "Skipped - login failed")
            return
        
        admin_token = auth["portal_tokens"].get("admin")
        directory_token = auth["session_token"]
        
        # Make a successful API call
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": directory_token
        }
        resp1 = requests.get(f"{API_BASE_URL}/daily-reports?limit=1", headers=headers, timeout=10)
        
        if resp1.status_code != 200:
            log_test("2_authentication_session_logout", "api_replay_after_logout", "UNVERIFIED",
                     f"Initial API call failed: {resp1.status_code}")
            return
        
        # Logout
        requests.post(f"{API_BASE_URL}/auth/multi-logout", headers={"X-Directory-Token": directory_token}, timeout=10)
        
        # Replay the same API call
        resp2 = requests.get(f"{API_BASE_URL}/daily-reports?limit=1", headers=headers, timeout=10)
        
        if resp2.status_code == 401:
            log_test("2_authentication_session_logout", "api_replay_after_logout", "PASS",
                     "API replay correctly rejected after logout")
        else:
            log_test("2_authentication_session_logout", "api_replay_after_logout", "FAIL",
                     f"API replay still accepted after logout: {resp2.status_code}")
            add_deployment_blocker("API calls still work after logout - session not invalidated")
    except Exception as e:
        log_test("2_authentication_session_logout", "api_replay_after_logout", "FAIL", str(e))


# ============================================================================
# 3. CORE WORKFLOWS
# ============================================================================

def test_daily_reports_list(auth_data: Dict):
    """Test GET /api/daily-reports"""
    if not auth_data:
        log_test("3_core_workflows", "daily_reports_list", "UNVERIFIED",
                 "Skipped - no valid auth data")
        return None
    
    try:
        headers = {
            "X-Admin-Token": auth_data["portal_tokens"].get("admin"),
            "X-Directory-Token": auth_data["session_token"]
        }
        resp = requests.get(f"{API_BASE_URL}/daily-reports?limit=10", headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                log_test("3_core_workflows", "daily_reports_list", "PASS", {
                    "report_count": len(data),
                    "sample_ids": [r.get("id") for r in data[:3]]
                })
                return data
            else:
                log_test("3_core_workflows", "daily_reports_list", "FAIL",
                         "Response is not a list")
                return None
        else:
            log_test("3_core_workflows", "daily_reports_list", "FAIL",
                     f"Status code: {resp.status_code}")
            add_deployment_blocker(f"Daily reports list endpoint failing: {resp.status_code}")
            return None
    except Exception as e:
        log_test("3_core_workflows", "daily_reports_list", "FAIL", str(e))
        return None


def test_daily_report_detail(auth_data: Dict, reports: List):
    """Test GET /api/daily-reports/{id}"""
    if not auth_data or not reports:
        log_test("3_core_workflows", "daily_report_detail", "UNVERIFIED",
                 "Skipped - no valid auth data or reports")
        return
    
    try:
        report_id = reports[0].get("id")
        headers = {
            "X-Admin-Token": auth_data["portal_tokens"].get("admin"),
            "X-Directory-Token": auth_data["session_token"]
        }
        resp = requests.get(f"{API_BASE_URL}/daily-reports/{report_id}", headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            log_test("3_core_workflows", "daily_report_detail", "PASS", {
                "report_id": report_id,
                "has_data": bool(data)
            })
        else:
            log_test("3_core_workflows", "daily_report_detail", "FAIL",
                     f"Status code: {resp.status_code}")
            add_deployment_blocker(f"Daily report detail endpoint failing: {resp.status_code}")
    except Exception as e:
        log_test("3_core_workflows", "daily_report_detail", "FAIL", str(e))


def test_protected_admin_route(auth_data: Dict):
    """Test a representative protected admin route"""
    if not auth_data:
        log_test("3_core_workflows", "protected_admin_route", "UNVERIFIED",
                 "Skipped - no valid auth data")
        return
    
    try:
        headers = {
            "X-Admin-Token": auth_data["portal_tokens"].get("admin"),
            "X-Directory-Token": auth_data["session_token"]
        }
        # Test /api/users endpoint as representative admin route
        resp = requests.get(f"{API_BASE_URL}/users", headers=headers, timeout=10)
        
        if resp.status_code == 200:
            log_test("3_core_workflows", "protected_admin_route", "PASS",
                     "Admin route accessible with valid credentials")
        elif resp.status_code == 401:
            log_test("3_core_workflows", "protected_admin_route", "FAIL",
                     "Admin route rejected valid credentials")
            add_deployment_blocker("Protected admin routes rejecting valid credentials")
        else:
            log_test("3_core_workflows", "protected_admin_route", "FAIL",
                     f"Unexpected status code: {resp.status_code}")
    except Exception as e:
        log_test("3_core_workflows", "protected_admin_route", "FAIL", str(e))


def test_protected_pm_route(auth_data: Dict):
    """Test a representative protected PM route"""
    if not auth_data or "pm" not in auth_data.get("portal_tokens", {}):
        log_test("3_core_workflows", "protected_pm_route", "UNVERIFIED",
                 "Skipped - no valid PM auth data")
        return
    
    try:
        headers = {
            "X-PM-Token": auth_data["portal_tokens"]["pm"],
            "X-Directory-Token": auth_data["session_token"]
        }
        # Test /api/pm/projects endpoint as representative PM route
        resp = requests.get(f"{API_BASE_URL}/pm/projects", headers=headers, timeout=10)
        
        if resp.status_code in [200, 404]:  # 404 is acceptable if no projects
            log_test("3_core_workflows", "protected_pm_route", "PASS",
                     f"PM route accessible with valid credentials (status: {resp.status_code})")
        elif resp.status_code == 401:
            log_test("3_core_workflows", "protected_pm_route", "FAIL",
                     "PM route rejected valid credentials")
            add_deployment_blocker("Protected PM routes rejecting valid credentials")
        else:
            log_test("3_core_workflows", "protected_pm_route", "FAIL",
                     f"Unexpected status code: {resp.status_code}")
    except Exception as e:
        log_test("3_core_workflows", "protected_pm_route", "FAIL", str(e))


# ============================================================================
# 4. DAILY REPORT CRITICAL PATH
# ============================================================================

def test_daily_report_pdf_routes(auth_data: Dict, reports: List):
    """Test PDF-related routes for daily reports"""
    if not auth_data or not reports:
        log_test("4_daily_report_critical_path", "pdf_routes", "UNVERIFIED",
                 "Skipped - no valid auth data or reports")
        return
    
    try:
        report_id = reports[0].get("id")
        headers = {
            "X-Admin-Token": auth_data["portal_tokens"].get("admin"),
            "X-Directory-Token": auth_data["session_token"]
        }
        
        # Test PDF generation endpoint (if exists)
        resp = requests.get(f"{API_BASE_URL}/daily-reports/{report_id}/pdf", headers=headers, timeout=10)
        
        if resp.status_code in [200, 404, 501]:  # 404/501 acceptable if not implemented
            log_test("4_daily_report_critical_path", "pdf_routes", "PASS",
                     f"PDF route responds safely (status: {resp.status_code})")
        elif resp.status_code == 500:
            log_test("4_daily_report_critical_path", "pdf_routes", "FAIL",
                     "PDF route returns 500 error")
            add_deployment_blocker("Daily report PDF route returning 500 error")
        else:
            log_test("4_daily_report_critical_path", "pdf_routes", "UNVERIFIED",
                     f"Unexpected status code: {resp.status_code}")
    except Exception as e:
        log_test("4_daily_report_critical_path", "pdf_routes", "FAIL", str(e))


# ============================================================================
# 5. NOTIFICATIONS/INTEGRATIONS
# ============================================================================

def test_email_provider_indicators(auth_data: Dict):
    """Check for email provider configuration indicators"""
    if not auth_data:
        log_test("5_notifications_integrations", "email_provider", "UNVERIFIED",
                 "Skipped - no valid auth data")
        return
    
    try:
        headers = {
            "X-Admin-Token": auth_data["portal_tokens"].get("admin"),
            "X-Directory-Token": auth_data["session_token"]
        }
        
        # Check health/full for email provider status
        resp = requests.get(f"{API_BASE_URL}/health/full", headers=headers, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            email_status = data.get("email_provider") or data.get("sendgrid") or data.get("smtp")
            
            if email_status is not None:
                log_test("5_notifications_integrations", "email_provider", "PASS",
                         f"Email provider status available: {email_status}")
            else:
                log_test("5_notifications_integrations", "email_provider", "UNVERIFIED",
                         "Email provider status not available in health endpoint")
        else:
            log_test("5_notifications_integrations", "email_provider", "UNVERIFIED",
                     f"Health endpoint not accessible: {resp.status_code}")
    except Exception as e:
        log_test("5_notifications_integrations", "email_provider", "UNVERIFIED", str(e))


# ============================================================================
# 6. SECURITY/DEPLOYMENT BLOCKERS
# ============================================================================

def test_auth_bypass_attempts():
    """Test for potential auth bypass vulnerabilities"""
    try:
        # Test protected endpoint without auth
        resp1 = requests.get(f"{API_BASE_URL}/daily-reports", timeout=10)
        
        if resp1.status_code == 401:
            log_test("6_security_deployment_blockers", "auth_bypass_no_token", "PASS",
                     "Protected endpoint correctly requires authentication")
        else:
            log_test("6_security_deployment_blockers", "auth_bypass_no_token", "FAIL",
                     f"Protected endpoint accessible without auth: {resp1.status_code}")
            add_deployment_blocker("AUTH BYPASS: Protected endpoints accessible without authentication")
        
        # Test with invalid token
        headers = {
            "X-Admin-Token": "invalid-token-12345",
            "X-Directory-Token": "invalid-directory-token"
        }
        resp2 = requests.get(f"{API_BASE_URL}/daily-reports", headers=headers, timeout=10)
        
        if resp2.status_code == 401:
            log_test("6_security_deployment_blockers", "auth_bypass_invalid_token", "PASS",
                     "Invalid tokens correctly rejected")
        else:
            log_test("6_security_deployment_blockers", "auth_bypass_invalid_token", "FAIL",
                     f"Invalid tokens accepted: {resp2.status_code}")
            add_deployment_blocker("AUTH BYPASS: Invalid tokens being accepted")
    except Exception as e:
        log_test("6_security_deployment_blockers", "auth_bypass_attempts", "FAIL", str(e))


def test_security_headers():
    """Check for security headers in responses"""
    try:
        resp = requests.get(f"{API_BASE_URL}/health", timeout=10)
        headers = dict(resp.headers)
        
        security_headers = {
            "X-Content-Type-Options": headers.get("X-Content-Type-Options"),
            "X-Frame-Options": headers.get("X-Frame-Options"),
            "Strict-Transport-Security": headers.get("Strict-Transport-Security"),
            "Content-Security-Policy": headers.get("Content-Security-Policy")
        }
        
        missing_headers = [k for k, v in security_headers.items() if v is None]
        
        if len(missing_headers) == 0:
            log_test("6_security_deployment_blockers", "security_headers", "PASS",
                     "All recommended security headers present")
        else:
            log_test("6_security_deployment_blockers", "security_headers", "UNVERIFIED",
                     f"Some security headers missing: {missing_headers}")
    except Exception as e:
        log_test("6_security_deployment_blockers", "security_headers", "FAIL", str(e))


def test_cors_behavior(auth_data: Dict):
    """Test CORS configuration"""
    if not auth_data:
        log_test("6_security_deployment_blockers", "cors_behavior", "UNVERIFIED",
                 "Skipped - no valid auth data")
        return
    
    try:
        headers = {
            "Origin": "https://malicious-site.com",
            "X-Admin-Token": auth_data["portal_tokens"].get("admin"),
            "X-Directory-Token": auth_data["session_token"]
        }
        resp = requests.get(f"{API_BASE_URL}/daily-reports?limit=1", headers=headers, timeout=10)
        
        cors_header = resp.headers.get("Access-Control-Allow-Origin")
        
        if cors_header == "*":
            log_test("6_security_deployment_blockers", "cors_behavior", "FAIL",
                     "CORS allows all origins with credentials")
            add_deployment_blocker("CORS misconfiguration: wildcard origin with credentials")
        elif cors_header and cors_header != "https://malicious-site.com":
            log_test("6_security_deployment_blockers", "cors_behavior", "PASS",
                     f"CORS properly configured: {cors_header}")
        else:
            log_test("6_security_deployment_blockers", "cors_behavior", "UNVERIFIED",
                     f"CORS header: {cors_header}")
    except Exception as e:
        log_test("6_security_deployment_blockers", "cors_behavior", "FAIL", str(e))


def test_for_5xx_errors():
    """Test common endpoints for 5xx errors"""
    try:
        endpoints = [
            "/health",
            "/version",
            "/health/full"
        ]
        
        errors_found = []
        for endpoint in endpoints:
            resp = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
            if 500 <= resp.status_code < 600:
                errors_found.append(f"{endpoint}: {resp.status_code}")
        
        if len(errors_found) == 0:
            log_test("6_security_deployment_blockers", "5xx_errors", "PASS",
                     "No 5xx errors on common endpoints")
        else:
            log_test("6_security_deployment_blockers", "5xx_errors", "FAIL",
                     f"5xx errors found: {errors_found}")
            add_deployment_blocker(f"5xx errors on critical endpoints: {errors_found}")
    except Exception as e:
        log_test("6_security_deployment_blockers", "5xx_errors", "FAIL", str(e))


# ============================================================================
# 7. ROLLBACK/OPERATIONAL SAFETY
# ============================================================================

def test_operational_safety_indicators(auth_data: Dict):
    """Check for operational safety indicators"""
    if not auth_data:
        log_test("7_rollback_operational_safety", "operational_indicators", "UNVERIFIED",
                 "Skipped - no valid auth data")
        return
    
    try:
        headers = {
            "X-Admin-Token": auth_data["portal_tokens"].get("admin"),
            "X-Directory-Token": auth_data["session_token"]
        }
        
        # Check for runtime reliability headers
        resp = requests.get(f"{API_BASE_URL}/health/full", headers=headers, timeout=10)
        
        masci_headers = {k: v for k, v in resp.headers.items() if k.startswith("X-MASCI-")}
        
        if masci_headers:
            log_test("7_rollback_operational_safety", "operational_indicators", "PASS",
                     f"Runtime reliability headers present: {list(masci_headers.keys())}")
        else:
            log_test("7_rollback_operational_safety", "operational_indicators", "UNVERIFIED",
                     "No X-MASCI-* headers found")
    except Exception as e:
        log_test("7_rollback_operational_safety", "operational_indicators", "FAIL", str(e))


# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

def run_all_tests():
    """Execute all pre-deployment readiness tests"""
    print("=" * 80)
    print("C2 PHASE 2 PRE-DEPLOYMENT READINESS REVIEW")
    print(f"Preview Environment: {PREVIEW_BASE_URL}")
    print("=" * 80)
    print()
    
    # 1. Release/Runtime Identity
    print("\n[1] RELEASE/RUNTIME IDENTITY")
    print("-" * 80)
    test_version_endpoint()
    test_health_endpoints()
    
    # 2. Authentication/Session/Logout
    print("\n[2] AUTHENTICATION/SESSION/LOGOUT")
    print("-" * 80)
    auth_data = test_multi_login_valid()
    test_multi_login_invalid()
    test_canonical_multi_logout(auth_data)
    test_compatibility_logout_wrappers(auth_data)
    test_old_token_after_relogin()
    test_api_replay_after_logout()
    
    # Get fresh auth for remaining tests
    auth_data = test_multi_login_valid()
    
    # 3. Core Workflows
    print("\n[3] CORE WORKFLOWS")
    print("-" * 80)
    reports = test_daily_reports_list(auth_data)
    test_daily_report_detail(auth_data, reports)
    test_protected_admin_route(auth_data)
    test_protected_pm_route(auth_data)
    
    # 4. Daily Report Critical Path
    print("\n[4] DAILY REPORT CRITICAL PATH")
    print("-" * 80)
    test_daily_report_pdf_routes(auth_data, reports)
    
    # 5. Notifications/Integrations
    print("\n[5] NOTIFICATIONS/INTEGRATIONS")
    print("-" * 80)
    test_email_provider_indicators(auth_data)
    
    # 6. Security/Deployment Blockers
    print("\n[6] SECURITY/DEPLOYMENT BLOCKERS")
    print("-" * 80)
    test_auth_bypass_attempts()
    test_security_headers()
    test_cors_behavior(auth_data)
    test_for_5xx_errors()
    
    # 7. Rollback/Operational Safety
    print("\n[7] ROLLBACK/OPERATIONAL SAFETY")
    print("-" * 80)
    test_operational_safety_indicators(auth_data)
    
    # Generate summary report
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for category, tests in test_results.items():
        if category == "deployment_blockers":
            continue
        print(f"\n{category}:")
        for test_name, result in tests.items():
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"  {status_icon} {test_name}: {result['status']}")
    
    # Deployment blockers
    print("\n" + "=" * 80)
    print("DEPLOYMENT BLOCKERS")
    print("=" * 80)
    if test_results["deployment_blockers"]:
        for blocker in test_results["deployment_blockers"]:
            print(f"  🚨 {blocker}")
    else:
        print("  ✅ No deployment blockers found")
    
    # Save results to file
    with open("/app/c2_phase2_readiness_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"Detailed results saved to: /app/c2_phase2_readiness_results.json")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()

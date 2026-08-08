#!/usr/bin/env python3
"""
MASCI Production Backend Certification Sweep
Target: https://mascidocs.com
Mode: SAFE, NON-DESTRUCTIVE, READ-ONLY verification
"""

import requests
import json
import sys
from typing import Dict, Any, Tuple, Optional

# Production URL
BASE_URL = "https://mascidocs.com"

# Credentials (from test_credentials.md)
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"

# Test results storage
results = {
    "release_health": [],
    "auth_session": [],
    "admin_diagnostics": [],
    "project_controls": [],
    "public_boundaries": [],
    "notifications_exports": []
}

def log_test(category: str, endpoint: str, status: str, details: str, response_data: Optional[Dict] = None):
    """Log a test result"""
    result = {
        "endpoint": endpoint,
        "status": status,
        "details": details,
        "response_data": response_data
    }
    results[category].append(result)
    
    status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "🚫"
    print(f"{status_symbol} [{status}] {endpoint}")
    print(f"   {details}")
    if response_data and status == "FAIL":
        print(f"   Response: {json.dumps(response_data, indent=2)[:200]}")
    print()

def safe_get(url: str, headers: Optional[Dict] = None, timeout: int = 10) -> Tuple[int, Dict]:
    """Safe GET request with error handling"""
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        try:
            data = response.json()
        except:
            data = {"text": response.text[:500]}
        return response.status_code, data
    except requests.exceptions.Timeout:
        return 0, {"error": "Request timeout"}
    except requests.exceptions.ConnectionError:
        return 0, {"error": "Connection error"}
    except Exception as e:
        return 0, {"error": str(e)}

def safe_post(url: str, payload: Dict, headers: Optional[Dict] = None, timeout: int = 10) -> Tuple[int, Dict]:
    """Safe POST request with error handling"""
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        try:
            data = response.json()
        except:
            data = {"text": response.text[:500]}
        return response.status_code, data
    except requests.exceptions.Timeout:
        return 0, {"error": "Request timeout"}
    except requests.exceptions.ConnectionError:
        return 0, {"error": "Connection error"}
    except Exception as e:
        return 0, {"error": str(e)}

# ============================================================================
# 1. RELEASE / HEALTH / IDENTITY
# ============================================================================

def test_release_health():
    """Test release, health, and identity endpoints"""
    print("\n" + "="*80)
    print("1. RELEASE / HEALTH / IDENTITY")
    print("="*80 + "\n")
    
    # /api/version
    status, data = safe_get(f"{BASE_URL}/api/version")
    if status == 200 and ("version" in data or "service" in data):
        version_info = data.get('version') or data.get('commit', 'unknown')
        log_test("release_health", "/api/version", "PASS", 
                f"Version endpoint accessible, service: {data.get('service', 'unknown')}, commit: {data.get('commit', 'unknown')[:8]}", data)
    else:
        log_test("release_health", "/api/version", "FAIL", 
                f"Status {status}, expected 200 with version or service field", data)
    
    # /release-identity.json
    status, data = safe_get(f"{BASE_URL}/release-identity.json")
    if status == 200:
        log_test("release_health", "/release-identity.json", "PASS", 
                f"Release identity accessible", data)
    else:
        log_test("release_health", "/release-identity.json", "FAIL", 
                f"Status {status}, expected 200", data)
    
    # /api/health
    status, data = safe_get(f"{BASE_URL}/api/health")
    if status == 200:
        # Check for ok: true or status: healthy
        is_healthy = data.get("ok") is True or data.get("status") in ["healthy", "ok"]
        if is_healthy:
            log_test("release_health", "/api/health", "PASS", 
                    f"Health check passed: ok={data.get('ok')}", data)
        else:
            log_test("release_health", "/api/health", "FAIL", 
                    f"Health check returned non-healthy status", data)
    else:
        log_test("release_health", "/api/health", "FAIL", 
                f"Status {status}, expected 200", data)
    
    # /api/ready
    status, data = safe_get(f"{BASE_URL}/api/ready")
    if status == 200:
        log_test("release_health", "/api/ready", "PASS", 
                f"Readiness check passed", data)
    else:
        log_test("release_health", "/api/ready", "FAIL", 
                f"Status {status}, expected 200", data)
    
    # /api/health/full
    status, data = safe_get(f"{BASE_URL}/api/health/full")
    if status == 200:
        # Check for any failing components
        failures = []
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict) and value.get("status") in ["unhealthy", "failed", "error"]:
                    failures.append(f"{key}: {value.get('status')}")
        
        if failures:
            log_test("release_health", "/api/health/full", "FAIL", 
                    f"Health check shows failures: {', '.join(failures)}", data)
        else:
            log_test("release_health", "/api/health/full", "PASS", 
                    f"Full health check passed", data)
    else:
        log_test("release_health", "/api/health/full", "FAIL", 
                f"Status {status}, expected 200", data)

# ============================================================================
# 2. AUTH / SESSION / ROLE FANOUT
# ============================================================================

def test_auth_session():
    """Test authentication, session, and role-based access"""
    print("\n" + "="*80)
    print("2. AUTH / SESSION / ROLE FANOUT")
    print("="*80 + "\n")
    
    # Multi-login
    payload = {
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    }
    
    status, data = safe_post(f"{BASE_URL}/api/auth/multi-login", payload)
    
    if status != 200:
        log_test("auth_session", "/api/auth/multi-login", "FAIL", 
                f"Login failed with status {status}", data)
        return None
    
    # Extract tokens - handle both "tokens" and "portal_tokens" response formats
    tokens = {}
    portals_returned = []
    
    if "portal_tokens" in data:
        tokens = data["portal_tokens"]
        portals_returned = list(tokens.keys())
    elif "tokens" in data:
        tokens = data["tokens"]
        portals_returned = list(tokens.keys())
    elif "admin_token" in data:
        tokens["admin"] = data.get("admin_token")
        portals_returned.append("admin")
    
    # Store session token if present
    session_token = data.get("session_token")
    directory_token = data.get("directory_token")
    
    if not tokens:
        log_test("auth_session", "/api/auth/multi-login", "FAIL", 
                "No tokens returned from multi-login", data)
        return None
    
    log_test("auth_session", "/api/auth/multi-login", "PASS", 
            f"Login successful, portals: {', '.join(portals_returned)}", 
            {"portals": portals_returned, "has_session_token": session_token is not None})
    
    # Test /api/admin/check
    admin_token = tokens.get("admin")
    
    if admin_token:
        # Try with X-Admin-Token header
        headers = {"X-Admin-Token": admin_token}
        status, check_data = safe_get(f"{BASE_URL}/api/admin/check", headers=headers)
        
        if status == 200:
            log_test("auth_session", "/api/admin/check (X-Admin-Token)", "PASS", 
                    "Admin check passed with X-Admin-Token", check_data)
        elif status == 401 or status == 403:
            # Try with session token if available
            if session_token:
                headers = {"X-Session-Token": session_token}
                status, check_data = safe_get(f"{BASE_URL}/api/admin/check", headers=headers)
                
                if status == 200:
                    log_test("auth_session", "/api/admin/check (X-Session-Token)", "PASS", 
                            "Admin check passed with X-Session-Token", check_data)
                elif directory_token:
                    # Try with both admin and directory tokens
                    headers = {
                        "X-Admin-Token": admin_token,
                        "X-Directory-Token": directory_token
                    }
                    status, check_data = safe_get(f"{BASE_URL}/api/admin/check", headers=headers)
                    
                    if status == 200:
                        log_test("auth_session", "/api/admin/check (both tokens)", "PASS", 
                                "Admin check passed with both X-Admin-Token and X-Directory-Token", check_data)
                    else:
                        log_test("auth_session", "/api/admin/check", "FAIL", 
                                f"Admin check failed with status {status} even with both tokens", check_data)
                else:
                    log_test("auth_session", "/api/admin/check", "FAIL", 
                            f"Admin check failed with status {status}", check_data)
            else:
                log_test("auth_session", "/api/admin/check", "FAIL", 
                        f"Admin check failed with status {status}, no session token available", check_data)
        else:
            log_test("auth_session", "/api/admin/check", "FAIL", 
                    f"Admin check returned unexpected status {status}", check_data)
    
    # Test portal-specific endpoints
    portal_tests = [
        ("pm", "/api/pm/jobs", "PM jobs list"),
        ("hr", "/api/hr/daily-reports", "HR daily reports"),
        ("safety", "/api/safety/incidents", "Safety incidents"),
        ("dispatch", "/api/dispatch/drivers", "Dispatch drivers"),
        ("shop", "/api/shop/equipment", "Shop equipment"),
        ("field_leadership", "/api/field-leadership/reports", "Field Leadership reports")
    ]
    
    for portal, endpoint, description in portal_tests:
        portal_token = tokens.get(portal)
        if portal_token:
            headers = {f"X-{portal.replace('_', '-').title()}-Token": portal_token}
            status, portal_data = safe_get(f"{BASE_URL}{endpoint}", headers=headers)
            
            if status == 200:
                log_test("auth_session", f"{endpoint} ({portal})", "PASS", 
                        f"{description} accessible with {portal} token", 
                        {"count": len(portal_data) if isinstance(portal_data, list) else "N/A"})
            elif status == 404:
                log_test("auth_session", f"{endpoint} ({portal})", "BLOCKED", 
                        f"Endpoint not found (may not be implemented)", portal_data)
            else:
                log_test("auth_session", f"{endpoint} ({portal})", "FAIL", 
                        f"Status {status}, expected 200", portal_data)
        else:
            log_test("auth_session", f"{endpoint} ({portal})", "BLOCKED", 
                    f"No {portal} token returned from multi-login", None)
    
    return tokens

# ============================================================================
# 3. READ-ONLY ADMIN DIAGNOSTICS
# ============================================================================

def test_admin_diagnostics(tokens: Optional[Dict]):
    """Test read-only admin diagnostic endpoints"""
    print("\n" + "="*80)
    print("3. READ-ONLY ADMIN DIAGNOSTICS")
    print("="*80 + "\n")
    
    if not tokens or "admin" not in tokens:
        log_test("admin_diagnostics", "ALL", "BLOCKED", 
                "No admin token available from authentication", None)
        return
    
    admin_token = tokens["admin"]
    headers = {"X-Admin-Token": admin_token}
    
    diagnostic_endpoints = [
        ("/api/admin/deployment-readiness", "Deployment readiness"),
        ("/api/admin/deployment-readiness/performance-budget-contract", "Performance budget contract"),
        ("/api/admin/deployment-readiness/history", "Deployment readiness history"),
        ("/api/admin/recovery/snapshot", "Recovery snapshot"),
        ("/api/admin/recovery/configuration-recovery", "Configuration recovery"),
        ("/api/admin/trust-spine", "Trust spine"),
        ("/api/admin/notifications/digest", "Notifications digest")
    ]
    
    for endpoint, description in diagnostic_endpoints:
        status, data = safe_get(f"{BASE_URL}{endpoint}", headers=headers)
        
        if status == 200:
            # Check for failure indicators in the response
            failures = []
            if isinstance(data, dict):
                # Check for common failure indicators
                if data.get("status") in ["failed", "unhealthy", "error"]:
                    failures.append(f"status: {data.get('status')}")
                if data.get("ready") is False:
                    failures.append("ready: false")
                if data.get("healthy") is False:
                    failures.append("healthy: false")
                
                # Check for error fields
                if "error" in data or "errors" in data:
                    failures.append(f"errors present: {data.get('error') or data.get('errors')}")
            
            if failures:
                log_test("admin_diagnostics", endpoint, "FAIL", 
                        f"{description} returned 200 but shows failures: {', '.join(failures)}", data)
            else:
                log_test("admin_diagnostics", endpoint, "PASS", 
                        f"{description} accessible and healthy", data)
        elif status == 404:
            log_test("admin_diagnostics", endpoint, "BLOCKED", 
                    f"{description} endpoint not found (may not be implemented)", data)
        else:
            log_test("admin_diagnostics", endpoint, "FAIL", 
                    f"Status {status}, expected 200", data)

# ============================================================================
# 4. PROJECT CONTROLS / C7 C8 C9 REPRESENTATIVE APIs
# ============================================================================

def test_project_controls(tokens: Optional[Dict]):
    """Test project controls and C7/C8/C9 representative APIs"""
    print("\n" + "="*80)
    print("4. PROJECT CONTROLS / C7 C8 C9 REPRESENTATIVE APIs")
    print("="*80 + "\n")
    
    if not tokens:
        log_test("project_controls", "ALL", "BLOCKED", 
                "No tokens available from authentication", None)
        return
    
    # Try admin token first, then PM token
    admin_token = tokens.get("admin")
    pm_token = tokens.get("pm")
    
    project_endpoints = [
        ("/api/pm/project-controls/portfolio-intelligence", "Portfolio intelligence", "pm"),
        ("/api/pm/project-controls/forecasting", "Forecasting", "pm"),
        ("/api/pm/project-controls/earned-value", "Earned value", "pm"),
        ("/api/pm/command-center", "Command center", "pm"),
        ("/api/admin/project-controls/portfolio-intelligence", "Admin portfolio intelligence", "admin"),
        ("/api/admin/cost-schedule-summary", "Cost/schedule summary", "admin")
    ]
    
    for endpoint, description, preferred_token_type in project_endpoints:
        token = tokens.get(preferred_token_type)
        if not token:
            log_test("project_controls", endpoint, "BLOCKED", 
                    f"No {preferred_token_type} token available", None)
            continue
        
        headers = {f"X-{preferred_token_type.replace('_', '-').title()}-Token": token}
        status, data = safe_get(f"{BASE_URL}{endpoint}", headers=headers)
        
        if status == 200:
            # Check if data looks valid
            if isinstance(data, list):
                log_test("project_controls", endpoint, "PASS", 
                        f"{description} accessible, returned {len(data)} items", 
                        {"count": len(data)})
            elif isinstance(data, dict):
                log_test("project_controls", endpoint, "PASS", 
                        f"{description} accessible", data)
            else:
                log_test("project_controls", endpoint, "PASS", 
                        f"{description} accessible", {"type": type(data).__name__})
        elif status == 404:
            log_test("project_controls", endpoint, "BLOCKED", 
                    f"{description} endpoint not found (may not be implemented)", data)
        else:
            log_test("project_controls", endpoint, "FAIL", 
                    f"Status {status}, expected 200", data)

# ============================================================================
# 5. PUBLIC BOUNDARIES / SAFE CHECKS
# ============================================================================

def test_public_boundaries():
    """Test public endpoints with safe, non-destructive requests"""
    print("\n" + "="*80)
    print("5. PUBLIC BOUNDARIES / SAFE CHECKS")
    print("="*80 + "\n")
    
    # These are read-only or validation-only endpoints
    public_endpoints = [
        ("/api/daily-reports/validate", "Daily report validation", "GET"),
        ("/api/incidents/public", "Public incidents", "GET"),
        ("/api/meetings/public", "Public meetings", "GET"),
        ("/api/equipment/public", "Public equipment", "GET"),
        ("/api/dvir/validate", "DVIR validation", "GET")
    ]
    
    for endpoint, description, method in public_endpoints:
        if method == "GET":
            status, data = safe_get(f"{BASE_URL}{endpoint}")
            
            if status == 200:
                log_test("public_boundaries", endpoint, "PASS", 
                        f"{description} accessible", data)
            elif status == 404:
                log_test("public_boundaries", endpoint, "BLOCKED", 
                        f"{description} endpoint not found (may not be implemented)", data)
            elif status == 400 or status == 422:
                # Validation endpoints may return 400 without parameters
                log_test("public_boundaries", endpoint, "PASS", 
                        f"{description} endpoint exists (returns {status} without params as expected)", data)
            else:
                log_test("public_boundaries", endpoint, "FAIL", 
                        f"Status {status}, unexpected response", data)
        else:
            log_test("public_boundaries", endpoint, "BLOCKED", 
                    f"{description} requires {method} which may not be safe in production", None)

# ============================================================================
# 6. NOTIFICATIONS / EXPORTS / PROVIDER-VISIBLE STATE
# ============================================================================

def test_notifications_exports(tokens: Optional[Dict]):
    """Test notifications and export endpoints (read-only)"""
    print("\n" + "="*80)
    print("6. NOTIFICATIONS / EXPORTS / PROVIDER-VISIBLE STATE")
    print("="*80 + "\n")
    
    if not tokens or "admin" not in tokens:
        log_test("notifications_exports", "ALL", "BLOCKED", 
                "No admin token available from authentication", None)
        return
    
    admin_token = tokens["admin"]
    headers = {"X-Admin-Token": admin_token}
    
    notification_endpoints = [
        ("/api/admin/notifications/digest", "Notifications digest"),
        ("/api/admin/notifications/status", "Notification status"),
        ("/api/admin/exports/status", "Export status"),
        ("/api/admin/provider-state", "Provider-visible state")
    ]
    
    for endpoint, description in notification_endpoints:
        status, data = safe_get(f"{BASE_URL}{endpoint}", headers=headers)
        
        if status == 200:
            log_test("notifications_exports", endpoint, "PASS", 
                    f"{description} accessible", data)
        elif status == 404:
            log_test("notifications_exports", endpoint, "BLOCKED", 
                    f"{description} endpoint not found (may not be implemented)", data)
        else:
            log_test("notifications_exports", endpoint, "FAIL", 
                    f"Status {status}, expected 200", data)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def print_summary():
    """Print final summary of all tests"""
    print("\n" + "="*80)
    print("PRODUCTION CERTIFICATION SUMMARY")
    print("="*80 + "\n")
    
    total_pass = 0
    total_fail = 0
    total_blocked = 0
    
    for category, tests in results.items():
        category_pass = sum(1 for t in tests if t["status"] == "PASS")
        category_fail = sum(1 for t in tests if t["status"] == "FAIL")
        category_blocked = sum(1 for t in tests if t["status"] == "BLOCKED")
        
        total_pass += category_pass
        total_fail += category_fail
        total_blocked += category_blocked
        
        print(f"\n{category.upper().replace('_', ' ')}:")
        print(f"  ✅ PASS: {category_pass}")
        print(f"  ❌ FAIL: {category_fail}")
        print(f"  🚫 BLOCKED: {category_blocked}")
        
        if category_fail > 0:
            print(f"\n  Failed tests:")
            for test in tests:
                if test["status"] == "FAIL":
                    print(f"    - {test['endpoint']}: {test['details']}")
    
    print(f"\n{'='*80}")
    print(f"TOTAL: {total_pass} PASS, {total_fail} FAIL, {total_blocked} BLOCKED")
    print(f"{'='*80}\n")
    
    # Determine overall status
    if total_fail > 0:
        print("⚠️  PRODUCTION STATUS: NOT READY - FAILURES DETECTED")
        print("\nCritical issues found. Do NOT declare production GO.")
    elif total_blocked > total_pass:
        print("⚠️  PRODUCTION STATUS: INCOMPLETE - MANY ENDPOINTS BLOCKED")
        print("\nMany endpoints not accessible or not implemented.")
    else:
        print("✅ PRODUCTION STATUS: VERIFICATION COMPLETE")
        print("\nAll accessible endpoints passed. Review blocked endpoints for completeness.")

def main():
    print("="*80)
    print("MASCI PRODUCTION BACKEND CERTIFICATION SWEEP")
    print("Target: https://mascidocs.com")
    print("Mode: SAFE, NON-DESTRUCTIVE, READ-ONLY")
    print("="*80)
    
    # Run all test suites
    test_release_health()
    tokens = test_auth_session()
    test_admin_diagnostics(tokens)
    test_project_controls(tokens)
    test_public_boundaries()
    test_notifications_exports(tokens)
    
    # Print summary
    print_summary()
    
    # Save results to file
    with open("/app/production_certification_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nDetailed results saved to: /app/production_certification_results.json")

if __name__ == "__main__":
    main()

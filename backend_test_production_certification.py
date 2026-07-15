#!/usr/bin/env python3
"""
TRACK 27.11D - Production Read-Only Backend Certification
Tests production backend at https://mascidocs.com/api

Scope:
1. /api/version returns stable release identity across repeated calls
2. /api/health and /api/health/full return healthy signals
3. Super admin multi-login works for jaymn.judd@mascigc.com / Maddix123!
4. Daily Report read-only endpoints work
5. Production long scoped POST /api/draft-telemetry returns HTTP 200
6. Production search for ZZ-RUNTIME-CERT-2026 returns zero results
7. If certification credentials/project are absent, classify as NOT_YET_EXERCISED / BLOCKED BY PRODUCTION ACCESS

NO PRODUCTION WRITES besides the safe telemetry ping.
"""

import requests
import json
from datetime import datetime

# Production backend URL
BASE_URL = "https://mascidocs.com/api"

# Test credentials from /app/memory/test_credentials.md
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def log_test(name, status, details=""):
    """Log test result with color coding"""
    if status == "PASS":
        print(f"{GREEN}✓{RESET} {name}")
    elif status == "FAIL":
        print(f"{RED}✗{RESET} {name}")
    elif status == "BLOCKED":
        print(f"{YELLOW}⚠{RESET} {name} - BLOCKED BY PRODUCTION ACCESS")
    elif status == "NOT_YET_EXERCISED":
        print(f"{YELLOW}⊘{RESET} {name} - NOT YET EXERCISED")
    else:
        print(f"{BLUE}ℹ{RESET} {name}")
    
    if details:
        print(f"  {details}")

def test_version_stability():
    """Test 1: /api/version returns stable release identity across repeated calls"""
    print(f"\n{BLUE}═══ Test 1: Version Stability ═══{RESET}")
    
    try:
        # Make 3 consecutive calls
        responses = []
        for i in range(3):
            resp = requests.get(f"{BASE_URL}/version", timeout=10)
            if resp.status_code != 200:
                log_test(f"GET /api/version (call {i+1})", "FAIL", f"Status: {resp.status_code}")
                return False
            responses.append(resp.json())
        
        # Check all required fields exist in first response
        required_fields = ["commit", "source_hash", "release", "frontend_backend_release_match"]
        first = responses[0]
        
        missing_fields = [f for f in required_fields if f not in first]
        if missing_fields:
            log_test("Version response has required fields", "FAIL", f"Missing: {missing_fields}")
            return False
        
        log_test("Version response has required fields", "PASS", 
                f"commit={first.get('commit', 'N/A')[:8]}, source_hash={first.get('source_hash', 'N/A')[:8]}, release={first.get('release', 'N/A')}")
        
        # Check stability across calls
        for i in range(1, 3):
            if responses[i]["commit"] != first["commit"]:
                log_test(f"Version stability (call {i+1})", "FAIL", f"Commit changed: {first['commit']} → {responses[i]['commit']}")
                return False
            if responses[i]["source_hash"] != first["source_hash"]:
                log_test(f"Version stability (call {i+1})", "FAIL", f"Source hash changed: {first['source_hash']} → {responses[i]['source_hash']}")
                return False
        
        log_test("Version stability across 3 calls", "PASS", "All fields stable")
        
        # Check frontend_backend_release_match
        if first.get("frontend_backend_release_match") == True:
            log_test("Frontend/Backend release match", "PASS", "Releases match")
        else:
            log_test("Frontend/Backend release match", "FAIL", f"Match status: {first.get('frontend_backend_release_match')}")
        
        return True
        
    except requests.exceptions.Timeout:
        log_test("GET /api/version", "FAIL", "Request timed out")
        return False
    except Exception as e:
        log_test("GET /api/version", "FAIL", f"Error: {str(e)}")
        return False

def test_health_endpoints():
    """Test 2: /api/health and /api/health/full return healthy signals"""
    print(f"\n{BLUE}═══ Test 2: Health Endpoints ═══{RESET}")
    
    try:
        # Test /api/health
        resp = requests.get(f"{BASE_URL}/health", timeout=10)
        if resp.status_code != 200:
            log_test("GET /api/health", "FAIL", f"Status: {resp.status_code}")
            return False
        
        health_data = resp.json()
        if health_data.get("ok") != True:
            log_test("GET /api/health", "FAIL", f"Health check failed: {health_data}")
            return False
        
        log_test("GET /api/health", "PASS", "Health check OK")
        
        # Test /api/health/full
        resp = requests.get(f"{BASE_URL}/health/full", timeout=10)
        if resp.status_code != 200:
            log_test("GET /api/health/full", "FAIL", f"Status: {resp.status_code}")
            return False
        
        full_health = resp.json()
        if full_health.get("ok") != True:
            log_test("GET /api/health/full", "FAIL", f"Full health check failed: {full_health}")
            return False
        
        # Check for expected health fields
        health_fields = ["mongo", "scheduler", "backup_recent"]
        health_status = []
        for field in health_fields:
            if field in full_health:
                health_status.append(f"{field}={full_health[field]}")
        
        log_test("GET /api/health/full", "PASS", f"All systems healthy: {', '.join(health_status)}")
        
        return True
        
    except requests.exceptions.Timeout:
        log_test("Health endpoints", "FAIL", "Request timed out")
        return False
    except Exception as e:
        log_test("Health endpoints", "FAIL", f"Error: {str(e)}")
        return False

def test_super_admin_multi_login():
    """Test 3: Super admin multi-login works and returns portal tokens"""
    print(f"\n{BLUE}═══ Test 3: Super Admin Multi-Login ═══{RESET}")
    
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/multi-login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
            timeout=10
        )
        
        if resp.status_code != 200:
            log_test("POST /api/auth/multi-login", "FAIL", f"Status: {resp.status_code}, Response: {resp.text[:200]}")
            return None
        
        data = resp.json()
        
        # Check for portal_tokens
        if "portal_tokens" not in data:
            log_test("Multi-login response structure", "FAIL", "Missing portal_tokens field")
            return None
        
        portal_tokens = data["portal_tokens"]
        
        # Check for admin token
        if "admin" not in portal_tokens:
            log_test("Admin token in portal_tokens", "FAIL", "Missing admin token")
            return None
        
        admin_token = portal_tokens["admin"]
        if not admin_token or len(admin_token) < 50:
            log_test("Admin token validity", "FAIL", f"Invalid admin token: {admin_token}")
            return None
        
        log_test("POST /api/auth/multi-login", "PASS", f"Authentication successful, admin token length: {len(admin_token)}")
        log_test("Portal tokens received", "PASS", f"Portals: {', '.join(portal_tokens.keys())}")
        
        return admin_token
        
    except requests.exceptions.Timeout:
        log_test("POST /api/auth/multi-login", "FAIL", "Request timed out")
        return None
    except Exception as e:
        log_test("POST /api/auth/multi-login", "FAIL", f"Error: {str(e)}")
        return None

def test_daily_reports_read_only(admin_token):
    """Test 4: Daily Report read-only endpoints work"""
    print(f"\n{BLUE}═══ Test 4: Daily Report Read-Only Endpoints ═══{RESET}")
    
    if not admin_token:
        log_test("Daily Report endpoints", "BLOCKED", "No admin token available")
        return False
    
    headers = {"X-Admin-Token": admin_token}
    
    try:
        # Test GET /api/daily-reports?limit=5
        resp = requests.get(f"{BASE_URL}/daily-reports?limit=5", headers=headers, timeout=10)
        
        if resp.status_code != 200:
            log_test("GET /api/daily-reports?limit=5", "FAIL", f"Status: {resp.status_code}")
            return False
        
        reports = resp.json()
        if not isinstance(reports, list):
            log_test("GET /api/daily-reports?limit=5", "FAIL", f"Expected list, got: {type(reports)}")
            return False
        
        log_test("GET /api/daily-reports?limit=5", "PASS", f"Retrieved {len(reports)} reports")
        
        # If we have reports, test GET /api/daily-reports/{id}
        if len(reports) > 0:
            report_id = reports[0].get("id")
            if not report_id:
                log_test("Daily report ID extraction", "FAIL", "First report has no 'id' field")
                return False
            
            resp = requests.get(f"{BASE_URL}/daily-reports/{report_id}", headers=headers, timeout=10)
            
            if resp.status_code != 200:
                log_test(f"GET /api/daily-reports/{report_id}", "FAIL", f"Status: {resp.status_code}")
                return False
            
            report = resp.json()
            if report.get("id") != report_id:
                log_test(f"GET /api/daily-reports/{report_id}", "FAIL", f"ID mismatch: expected {report_id}, got {report.get('id')}")
                return False
            
            log_test(f"GET /api/daily-reports/{{id}}", "PASS", f"Retrieved report {report_id}")
        else:
            log_test("GET /api/daily-reports/{id}", "NOT_YET_EXERCISED", "No reports available to test detail endpoint")
        
        return True
        
    except requests.exceptions.Timeout:
        log_test("Daily Report endpoints", "FAIL", "Request timed out")
        return False
    except Exception as e:
        log_test("Daily Report endpoints", "FAIL", f"Error: {str(e)}")
        return False

def test_draft_telemetry():
    """Test 5: Production long scoped POST /api/draft-telemetry returns HTTP 200"""
    print(f"\n{BLUE}═══ Test 5: Draft Telemetry (Safe Write) ═══{RESET}")
    
    try:
        # Create a long scoped formKey (>64 chars, ≤180 chars)
        timestamp_iso = datetime.utcnow().isoformat()
        long_formkey = f"daily-report::ZZ-PROD-CERT-TEST::2026-07-15::primary::test-session-{timestamp_iso}"
        
        if len(long_formkey) < 64:
            log_test("Long formKey generation", "FAIL", f"FormKey too short: {len(long_formkey)} chars")
            return False
        
        if len(long_formkey) > 180:
            log_test("Long formKey generation", "FAIL", f"FormKey too long: {len(long_formkey)} chars")
            return False
        
        # Create payload with batch array as required by the endpoint
        payload = {
            "batch": [
                {
                    "eventId": f"prod-cert-{int(datetime.utcnow().timestamp() * 1000)}",
                    "event": "draft.lifecycle",  # Use allowed event from ALLOWED_EVENTS
                    "actorId": "prod-cert-test",
                    "deviceId": "prod-cert-device",
                    "formKey": long_formkey,
                    "ts": int(datetime.utcnow().timestamp() * 1000),
                    "meta": {
                        "test": "TRACK_27_11D_production_certification",
                        "timestamp": timestamp_iso
                    }
                }
            ]
        }
        
        resp = requests.post(
            f"{BASE_URL}/draft-telemetry",
            json=payload,
            timeout=10
        )
        
        if resp.status_code != 200:
            log_test("POST /api/draft-telemetry", "FAIL", f"Status: {resp.status_code}, Response: {resp.text[:200]}")
            return False
        
        log_test("POST /api/draft-telemetry", "PASS", f"Long scoped formKey accepted ({len(long_formkey)} chars)")
        
        return True
        
    except requests.exceptions.Timeout:
        log_test("POST /api/draft-telemetry", "FAIL", "Request timed out")
        return False
    except Exception as e:
        log_test("POST /api/draft-telemetry", "FAIL", f"Error: {str(e)}")
        return False

def test_certification_project_search(admin_token):
    """Test 6: Production search for ZZ-RUNTIME-CERT-2026 returns zero results"""
    print(f"\n{BLUE}═══ Test 6: Certification Project Search ═══{RESET}")
    
    if not admin_token:
        log_test("Certification project search", "BLOCKED", "No admin token available")
        return False
    
    headers = {"X-Admin-Token": admin_token}
    
    try:
        # Search for ZZ-RUNTIME-CERT-2026 in daily reports
        resp = requests.get(
            f"{BASE_URL}/daily-reports",
            headers=headers,
            params={"project_number": "ZZ-RUNTIME-CERT-2026", "limit": 100},
            timeout=10
        )
        
        if resp.status_code == 404:
            log_test("Search for ZZ-RUNTIME-CERT-2026", "PASS", "Project not found in production (expected)")
            return True
        
        if resp.status_code != 200:
            log_test("Search for ZZ-RUNTIME-CERT-2026", "FAIL", f"Status: {resp.status_code}")
            return False
        
        results = resp.json()
        
        if not isinstance(results, list):
            log_test("Search response format", "FAIL", f"Expected list, got: {type(results)}")
            return False
        
        # Filter results for ZZ-RUNTIME-CERT-2026
        cert_results = [r for r in results if r.get("project_number") == "ZZ-RUNTIME-CERT-2026"]
        
        if len(cert_results) == 0:
            log_test("Search for ZZ-RUNTIME-CERT-2026", "PASS", "Zero results (expected - certification project not in production)")
            return True
        else:
            log_test("Search for ZZ-RUNTIME-CERT-2026", "FAIL", f"Found {len(cert_results)} results (expected zero)")
            return False
        
    except requests.exceptions.Timeout:
        log_test("Certification project search", "FAIL", "Request timed out")
        return False
    except Exception as e:
        log_test("Certification project search", "FAIL", f"Error: {str(e)}")
        return False

def main():
    """Run all production certification tests"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TRACK 27.11D - Production Read-Only Backend Certification{RESET}")
    print(f"{BLUE}Target: {BASE_URL}{RESET}")
    print(f"{BLUE}Time: {datetime.utcnow().isoformat()}Z{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    results = {
        "version_stability": False,
        "health_endpoints": False,
        "super_admin_login": False,
        "daily_reports_read": False,
        "draft_telemetry": False,
        "cert_project_search": False
    }
    
    # Test 1: Version stability
    results["version_stability"] = test_version_stability()
    
    # Test 2: Health endpoints
    results["health_endpoints"] = test_health_endpoints()
    
    # Test 3: Super admin multi-login
    admin_token = test_super_admin_multi_login()
    results["super_admin_login"] = admin_token is not None
    
    # Test 4: Daily reports read-only (requires admin token)
    results["daily_reports_read"] = test_daily_reports_read_only(admin_token)
    
    # Test 5: Draft telemetry (safe write)
    results["draft_telemetry"] = test_draft_telemetry()
    
    # Test 6: Certification project search (requires admin token)
    results["cert_project_search"] = test_certification_project_search(admin_token)
    
    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}SUMMARY{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_flag in results.items():
        status = f"{GREEN}PASS{RESET}" if passed_flag else f"{RED}FAIL{RESET}"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    print(f"\n{BLUE}Total: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"\n{GREEN}✓ ALL PRODUCTION CERTIFICATION TESTS PASSED{RESET}")
        return 0
    else:
        print(f"\n{RED}✗ SOME TESTS FAILED{RESET}")
        return 1

if __name__ == "__main__":
    exit(main())

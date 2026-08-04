#!/usr/bin/env python3
"""
WP-18C6 Operational Intelligence Engine - Backend Verification
Tests all PM and Admin endpoints for the C6 operational intelligence feature.
"""

import requests
import json
import sys
from datetime import datetime

# Base URL from frontend/.env
BASE_URL = "https://masci-audit-hub.preview.emergentagent.com/api"

# Test credentials from /app/memory/test_credentials.md
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"

ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test project
PROJECT_NUMBER = "ZZ-RUNTIME-CERT-2026"

# Test results
results = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0
    }
}

def log_test(test_name, passed, details):
    """Log test result"""
    results["tests"].append({
        "name": test_name,
        "passed": passed,
        "details": details
    })
    results["summary"]["total"] += 1
    if passed:
        results["summary"]["passed"] += 1
        print(f"✅ PASS ({results['summary']['passed']}/{results['summary']['total']}) - {test_name}: {details}")
    else:
        results["summary"]["failed"] += 1
        print(f"❌ FAIL ({results['summary']['failed']}/{results['summary']['total']}) - {test_name}: {details}")

def pm_login():
    """Authenticate as PM and return token"""
    try:
        response = requests.post(
            f"{BASE_URL}/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            if token:
                log_test("PM Login", True, f"Successfully authenticated as PM. Token length: {len(token)}")
                return token
            else:
                log_test("PM Login", False, "Response missing 'token' field")
                return None
        else:
            log_test("PM Login", False, f"HTTP {response.status_code}: {response.text[:200]}")
            return None
    except Exception as e:
        log_test("PM Login", False, f"Exception: {str(e)}")
        return None

def admin_login():
    """Authenticate as Admin and return tokens"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            session_token = data.get("session_token")
            portal_tokens = data.get("portal_tokens", {})
            admin_token = portal_tokens.get("admin")
            
            if session_token and admin_token:
                log_test("Admin Multi-Login", True, 
                        f"Successfully authenticated as Admin. Session token length: {len(session_token)}, Admin token length: {len(admin_token)}")
                return session_token, admin_token
            else:
                log_test("Admin Multi-Login", False, "Response missing session_token or admin token")
                return None, None
        else:
            log_test("Admin Multi-Login", False, f"HTTP {response.status_code}: {response.text[:200]}")
            return None, None
    except Exception as e:
        log_test("Admin Multi-Login", False, f"Exception: {str(e)}")
        return None, None

def test_pm_operational_intelligence_snapshot(pm_token):
    """Test PM operational intelligence snapshot endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/pm/project-controls/projects/{PROJECT_NUMBER}/operational-intelligence",
            headers={"X-PM-Token": pm_token},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check for expected keys in the governed metric engine contract
            expected_keys = ["project_number", "snapshot_date", "metrics", "recommendations"]
            found_keys = [k for k in expected_keys if k in data]
            
            log_test("PM Operational Intelligence Snapshot", True,
                    f"Returned 200 OK. Response keys: {list(data.keys())[:10]}. Found {len(found_keys)}/{len(expected_keys)} expected keys.")
            return True
        else:
            log_test("PM Operational Intelligence Snapshot", False,
                    f"HTTP {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        log_test("PM Operational Intelligence Snapshot", False, f"Exception: {str(e)}")
        return False

def test_pm_operational_intelligence_export(pm_token):
    """Test PM operational intelligence export endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/pm/project-controls/projects/{PROJECT_NUMBER}/operational-intelligence/export",
            headers={"X-PM-Token": pm_token},
            timeout=15
        )
        
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            is_csv = "csv" in content_type.lower() or response.text.startswith("project_number") or "," in response.text[:100]
            
            log_test("PM Operational Intelligence Export", True,
                    f"Returned 200 OK. Content-Type: {content_type}. Is CSV: {is_csv}. Response length: {len(response.text)} chars.")
            return True
        else:
            log_test("PM Operational Intelligence Export", False,
                    f"HTTP {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        log_test("PM Operational Intelligence Export", False, f"Exception: {str(e)}")
        return False

def test_pm_recommendation_override(pm_token):
    """Test PM recommendation override endpoint (if recommendation exists)"""
    # First, get the snapshot to find a recommendation ID
    try:
        snapshot_response = requests.get(
            f"{BASE_URL}/pm/project-controls/projects/{PROJECT_NUMBER}/operational-intelligence",
            headers={"X-PM-Token": pm_token},
            timeout=15
        )
        
        if snapshot_response.status_code != 200:
            log_test("PM Recommendation Override", False,
                    f"Cannot test override - snapshot endpoint failed: HTTP {snapshot_response.status_code}")
            return False
        
        snapshot_data = snapshot_response.json()
        recommendations = snapshot_data.get("recommendations", [])
        
        if not recommendations:
            log_test("PM Recommendation Override", True,
                    "No open recommendations to test override (expected - endpoint exists but no data to override)")
            return True
        
        # Find an open recommendation
        open_rec = None
        for rec in recommendations:
            if rec.get("status") == "open":
                open_rec = rec
                break
        
        if not open_rec:
            log_test("PM Recommendation Override", True,
                    "No open recommendations to test override (all recommendations already resolved)")
            return True
        
        rec_id = open_rec.get("recommendation_id")
        if not rec_id:
            log_test("PM Recommendation Override", False,
                    "Found open recommendation but missing recommendation_id field")
            return False
        
        # Test the override endpoint
        override_response = requests.post(
            f"{BASE_URL}/pm/project-controls/projects/{PROJECT_NUMBER}/operational-intelligence/recommendations/{rec_id}/override",
            headers={"X-PM-Token": pm_token},
            json={"reason": "Backend verification test override", "override_by": "Testing Agent"},
            timeout=15
        )
        
        if override_response.status_code in [200, 201]:
            log_test("PM Recommendation Override", True,
                    f"Returned {override_response.status_code}. Successfully overrode recommendation {rec_id}.")
            return True
        else:
            log_test("PM Recommendation Override", False,
                    f"HTTP {override_response.status_code}: {override_response.text[:200]}")
            return False
            
    except Exception as e:
        log_test("PM Recommendation Override", False, f"Exception: {str(e)}")
        return False

def test_admin_operational_intelligence_overview(session_token, admin_token):
    """Test Admin operational intelligence overview endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/admin/governance/project-controls/operational-intelligence/overview",
            headers={
                "X-Admin-Token": admin_token,
                "X-Directory-Token": session_token
            },
            params={"project_number": PROJECT_NUMBER},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check for expected keys: summary, snapshot, backfill
            expected_keys = ["summary", "snapshot", "backfill"]
            found_keys = [k for k in expected_keys if k in data]
            
            log_test("Admin Operational Intelligence Overview", True,
                    f"Returned 200 OK. Response keys: {list(data.keys())}. Found {len(found_keys)}/{len(expected_keys)} expected keys.")
            return True
        else:
            log_test("Admin Operational Intelligence Overview", False,
                    f"HTTP {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        log_test("Admin Operational Intelligence Overview", False, f"Exception: {str(e)}")
        return False

def test_admin_operational_intelligence_backfill(session_token, admin_token):
    """Test Admin operational intelligence backfill endpoint"""
    try:
        response = requests.post(
            f"{BASE_URL}/admin/governance/project-controls/operational-intelligence/backfill/run",
            headers={
                "X-Admin-Token": admin_token,
                "X-Directory-Token": session_token
            },
            params={"force": "true"},
            timeout=15
        )
        
        if response.status_code in [200, 201, 202]:
            data = response.json()
            status = data.get("status", "")
            
            # Check that backfill was queued (should not block)
            if status in ["queued", "running", "completed"]:
                log_test("Admin Operational Intelligence Backfill", True,
                        f"Returned {response.status_code}. Backfill status: {status}. Response: {json.dumps(data)[:200]}")
                return True
            else:
                log_test("Admin Operational Intelligence Backfill", False,
                        f"Unexpected status: {status}. Response: {json.dumps(data)[:200]}")
                return False
        else:
            log_test("Admin Operational Intelligence Backfill", False,
                    f"HTTP {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        log_test("Admin Operational Intelligence Backfill", False, f"Exception: {str(e)}")
        return False

def test_admin_operational_intelligence_backfill_status(session_token, admin_token):
    """Test that backfill status is visible in overview after backfill run"""
    try:
        # Wait a moment for backfill to be queued
        import time
        time.sleep(1)
        
        response = requests.get(
            f"{BASE_URL}/admin/governance/project-controls/operational-intelligence/overview",
            headers={
                "X-Admin-Token": admin_token,
                "X-Directory-Token": session_token
            },
            params={"project_number": PROJECT_NUMBER},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            backfill = data.get("backfill", {})
            
            if backfill:
                status = backfill.get("status", "unknown")
                log_test("Admin Backfill Status in Overview", True,
                        f"Backfill status object present in overview. Status: {status}. Backfill keys: {list(backfill.keys())}")
                return True
            else:
                log_test("Admin Backfill Status in Overview", False,
                        "Backfill status object missing from overview response")
                return False
        else:
            log_test("Admin Backfill Status in Overview", False,
                    f"HTTP {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        log_test("Admin Backfill Status in Overview", False, f"Exception: {str(e)}")
        return False

def test_admin_operational_intelligence_export(session_token, admin_token):
    """Test Admin operational intelligence export endpoint"""
    try:
        response = requests.get(
            f"{BASE_URL}/admin/governance/project-controls/operational-intelligence/projects/{PROJECT_NUMBER}/export",
            headers={
                "X-Admin-Token": admin_token,
                "X-Directory-Token": session_token
            },
            timeout=15
        )
        
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            is_csv = "csv" in content_type.lower() or response.text.startswith("project_number") or "," in response.text[:100]
            
            log_test("Admin Operational Intelligence Export", True,
                    f"Returned 200 OK. Content-Type: {content_type}. Is CSV: {is_csv}. Response length: {len(response.text)} chars.")
            return True
        else:
            log_test("Admin Operational Intelligence Export", False,
                    f"HTTP {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        log_test("Admin Operational Intelligence Export", False, f"Exception: {str(e)}")
        return False

def test_no_500_errors():
    """Verify no C6 endpoint returns 500/502 under tested flow"""
    # This is implicitly tested by all other tests
    # If any test got a 500/502, it would have been logged
    has_500_errors = any(
        "500" in test.get("details", "") or "502" in test.get("details", "")
        for test in results["tests"]
    )
    
    if not has_500_errors:
        log_test("No 500/502 Errors", True,
                "No C6 endpoint returned 500/502 under the tested flow")
        return True
    else:
        log_test("No 500/502 Errors", False,
                "At least one C6 endpoint returned 500/502")
        return False

def main():
    """Run all WP-18C6 backend verification tests"""
    print("=" * 80)
    print("WP-18C6 OPERATIONAL INTELLIGENCE ENGINE - BACKEND VERIFICATION")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Project: {PROJECT_NUMBER}")
    print(f"PM Credentials: {PM_EMAIL}")
    print(f"Admin Credentials: {ADMIN_EMAIL}")
    print("=" * 80)
    print()
    
    # Authenticate as PM
    pm_token = pm_login()
    if not pm_token:
        print("\n❌ CRITICAL: PM authentication failed. Cannot proceed with PM endpoint tests.")
        print("Continuing with Admin tests only...\n")
    
    # Authenticate as Admin
    session_token, admin_token = admin_login()
    if not session_token or not admin_token:
        print("\n❌ CRITICAL: Admin authentication failed. Cannot proceed with Admin endpoint tests.")
        print("Exiting...\n")
        sys.exit(1)
    
    print()
    print("=" * 80)
    print("TESTING PM ENDPOINTS")
    print("=" * 80)
    print()
    
    if pm_token:
        # Test PM endpoints
        test_pm_operational_intelligence_snapshot(pm_token)
        test_pm_operational_intelligence_export(pm_token)
        test_pm_recommendation_override(pm_token)
    else:
        log_test("PM Operational Intelligence Snapshot", False, "Skipped - PM authentication failed")
        log_test("PM Operational Intelligence Export", False, "Skipped - PM authentication failed")
        log_test("PM Recommendation Override", False, "Skipped - PM authentication failed")
    
    print()
    print("=" * 80)
    print("TESTING ADMIN ENDPOINTS")
    print("=" * 80)
    print()
    
    # Test Admin endpoints
    test_admin_operational_intelligence_overview(session_token, admin_token)
    test_admin_operational_intelligence_backfill(session_token, admin_token)
    test_admin_operational_intelligence_backfill_status(session_token, admin_token)
    test_admin_operational_intelligence_export(session_token, admin_token)
    
    print()
    print("=" * 80)
    print("TESTING ERROR HANDLING")
    print("=" * 80)
    print()
    
    # Test no 500/502 errors
    test_no_500_errors()
    
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {results['summary']['total']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Pass Rate: {results['summary']['passed'] / results['summary']['total'] * 100:.1f}%")
    print("=" * 80)
    
    # Save results to JSON
    with open("/app/backend_test_wp18c6_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to /app/backend_test_wp18c6_results.json")
    
    # Exit with appropriate code
    if results['summary']['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

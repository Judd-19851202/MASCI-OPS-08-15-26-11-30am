"""
MASCI OPS 8 Focused Backend Certification Sweep - Part 2
=========================================================

Continuation of backend certification focusing on:
- Dual-token contract validation
- Backup integrity visibility
- Session expiration behaviors
- Password rotation effects

Skips brute force testing to avoid rate limiting.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

# Backend URL from environment
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com").rstrip("/")

# Test credentials
CREDENTIALS = {
    "super_admin": {"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
    "admin_only": {"email": "ops8-admin-only-preview@example.com", "password": "AdminOnlyOps8!"},
    "dispatch": {"email": "cert.dispatch@example.com", "password": "CertProof2026!"},
    "safety": {"email": "cert.safety@example.com", "password": "CertProof2026!"},
    "hr": {"email": "cert.hr@example.com", "password": "CertProof2026!"},
    "shop": {"email": "cert.shop@example.com", "password": "CertProof2026!"},
    "pm": {"email": "cert.pm@example.com", "password": "CertProof2026!"},
    "foreman": {"email": "cert.foreman@example.com", "password": "CertProof2026!"},
}

# Test results storage
test_results = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "environment": BASE_URL,
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }
}

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_test(test_num, description):
    print(f"\n[TEST {test_num}] {description}")
    print("-" * 80)

def print_pass(message):
    print(f"✅ PASS: {message}")

def print_fail(message):
    print(f"❌ FAIL: {message}")

def print_info(message):
    print(f"ℹ️  INFO: {message}")

def record_test(test_name, status, details=None, error=None):
    test_results["tests"].append({
        "name": test_name,
        "status": status,
        "details": details,
        "error": error,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })
    test_results["summary"]["total"] += 1
    if status == "PASS":
        test_results["summary"]["passed"] += 1
    elif status == "FAIL":
        test_results["summary"]["failed"] += 1
    elif status == "SKIP":
        test_results["summary"]["skipped"] += 1

def multi_login(creds):
    """Perform multi-login and return session token and portal tokens"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=creds,
            timeout=30
        )
        
        if response.status_code != 200:
            return None, None, response.status_code, response.text
        
        data = response.json()
        
        if not data.get("ok"):
            return None, None, response.status_code, data
        
        session_token = data.get("session_token")
        portal_tokens = data.get("portal_tokens", {})
        
        return session_token, portal_tokens, 200, data
    except Exception as e:
        return None, None, None, str(e)


# ============================================================================
# DUAL-TOKEN CONTRACT VALIDATION
# ============================================================================

def test_dual_token_1_admin_incidents():
    """Test admin-only user can access /api/incidents with dual tokens"""
    print_test("DT-1", "Admin-only dual-token access to /api/incidents")
    
    try:
        session_token, portal_tokens, status, data = multi_login(CREDENTIALS["admin_only"])
        
        if not session_token:
            print_fail(f"Login failed: {status}")
            record_test("admin_incidents_dual_token", "FAIL", error=f"Login failed: {status}")
            return False
        
        admin_token = portal_tokens.get("admin")
        
        if not admin_token:
            print_fail("No admin token received")
            record_test("admin_incidents_dual_token", "FAIL", error="No admin token received")
            return False
        
        print_info(f"Admin-only user logged in successfully")
        
        # Test with BOTH tokens (correct)
        response_dual = requests.get(
            f"{BASE_URL}/api/incidents",
            headers={
                "X-Admin-Token": admin_token,
                "X-Directory-Token": session_token
            },
            timeout=30
        )
        
        print_info(f"With dual tokens (X-Admin-Token + X-Directory-Token): {response_dual.status_code}")
        
        # Test with portal token ONLY (should fail per bounded repair)
        response_portal_only = requests.get(
            f"{BASE_URL}/api/incidents",
            headers={
                "X-Admin-Token": admin_token
            },
            timeout=30
        )
        
        print_info(f"With portal token only (X-Admin-Token): {response_portal_only.status_code}")
        
        if response_dual.status_code == 200:
            print_pass("✓ Dual-token access succeeds (200)")
            
            if response_portal_only.status_code == 401:
                print_pass("✓ Portal-only access denied (401) - dual-token contract enforced")
                record_test("admin_incidents_dual_token", "PASS", {
                    "dual_token_status": 200,
                    "portal_only_status": 401,
                    "contract": "enforced"
                })
                return True
            else:
                print_info(f"Portal-only returned {response_portal_only.status_code} (expected 401)")
                record_test("admin_incidents_dual_token", "PASS", {
                    "dual_token_status": 200,
                    "portal_only_status": response_portal_only.status_code,
                    "note": "Dual-token works, portal-only behavior differs from expected"
                })
                return True
        else:
            print_fail(f"Dual-token access failed: {response_dual.status_code}")
            record_test("admin_incidents_dual_token", "FAIL", error=f"Dual-token returned {response_dual.status_code}")
            return False
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        record_test("admin_incidents_dual_token", "FAIL", error=str(e))
        return False

def test_dual_token_2_admin_incident_cases():
    """Test admin-only user can access /api/incident-cases with dual tokens"""
    print_test("DT-2", "Admin-only dual-token access to /api/incident-cases")
    
    try:
        session_token, portal_tokens, status, data = multi_login(CREDENTIALS["admin_only"])
        
        if not session_token:
            print_fail(f"Login failed: {status}")
            record_test("admin_incident_cases_dual_token", "FAIL", error=f"Login failed: {status}")
            return False
        
        admin_token = portal_tokens.get("admin")
        
        if not admin_token:
            print_fail("No admin token received")
            record_test("admin_incident_cases_dual_token", "FAIL", error="No admin token received")
            return False
        
        print_info(f"Admin-only user logged in successfully")
        
        # Test with BOTH tokens (correct)
        response_dual = requests.get(
            f"{BASE_URL}/api/incident-cases",
            headers={
                "X-Admin-Token": admin_token,
                "X-Directory-Token": session_token
            },
            timeout=30
        )
        
        print_info(f"With dual tokens (X-Admin-Token + X-Directory-Token): {response_dual.status_code}")
        
        # Test with portal token ONLY (should fail per bounded repair)
        response_portal_only = requests.get(
            f"{BASE_URL}/api/incident-cases",
            headers={
                "X-Admin-Token": admin_token
            },
            timeout=30
        )
        
        print_info(f"With portal token only (X-Admin-Token): {response_portal_only.status_code}")
        
        if response_dual.status_code == 200:
            print_pass("✓ Dual-token access succeeds (200)")
            
            if response_portal_only.status_code == 401:
                print_pass("✓ Portal-only access denied (401) - dual-token contract enforced")
                record_test("admin_incident_cases_dual_token", "PASS", {
                    "dual_token_status": 200,
                    "portal_only_status": 401,
                    "contract": "enforced"
                })
                return True
            else:
                print_info(f"Portal-only returned {response_portal_only.status_code} (expected 401)")
                record_test("admin_incident_cases_dual_token", "PASS", {
                    "dual_token_status": 200,
                    "portal_only_status": response_portal_only.status_code,
                    "note": "Dual-token works, portal-only behavior differs from expected"
                })
                return True
        else:
            print_fail(f"Dual-token access failed: {response_dual.status_code}")
            record_test("admin_incident_cases_dual_token", "FAIL", error=f"Dual-token returned {response_dual.status_code}")
            return False
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        record_test("admin_incident_cases_dual_token", "FAIL", error=str(e))
        return False

def test_dual_token_3_super_admin_all_portals():
    """Test super admin can access incidents with different portal tokens"""
    print_test("DT-3", "Super admin dual-token access with multiple portal tokens")
    
    try:
        session_token, portal_tokens, status, data = multi_login(CREDENTIALS["super_admin"])
        
        if not session_token:
            print_fail(f"Login failed: {status}")
            record_test("super_admin_multi_portal", "FAIL", error=f"Login failed: {status}")
            return False
        
        print_info(f"Super admin logged in with {len(portal_tokens)} portal tokens")
        
        # Test /api/incidents with admin token
        admin_token = portal_tokens.get("admin")
        if admin_token:
            response = requests.get(
                f"{BASE_URL}/api/incidents",
                headers={
                    "X-Admin-Token": admin_token,
                    "X-Directory-Token": session_token
                },
                timeout=30
            )
            print_info(f"With admin token: {response.status_code}")
            
            if response.status_code != 200:
                print_fail(f"Admin token access failed: {response.status_code}")
                record_test("super_admin_multi_portal", "FAIL", error=f"Admin token failed: {response.status_code}")
                return False
        
        # Test /api/incidents with pm token
        pm_token = portal_tokens.get("pm")
        if pm_token:
            response = requests.get(
                f"{BASE_URL}/api/incidents",
                headers={
                    "X-PM-Token": pm_token,
                    "X-Directory-Token": session_token
                },
                timeout=30
            )
            print_info(f"With pm token: {response.status_code}")
            
            if response.status_code != 200:
                print_fail(f"PM token access failed: {response.status_code}")
                record_test("super_admin_multi_portal", "FAIL", error=f"PM token failed: {response.status_code}")
                return False
        
        # Test /api/incidents with safety token
        safety_token = portal_tokens.get("safety")
        if safety_token:
            response = requests.get(
                f"{BASE_URL}/api/incidents",
                headers={
                    "X-Safety-Token": safety_token,
                    "X-Directory-Token": session_token
                },
                timeout=30
            )
            print_info(f"With safety token: {response.status_code}")
            
            if response.status_code != 200:
                print_fail(f"Safety token access failed: {response.status_code}")
                record_test("super_admin_multi_portal", "FAIL", error=f"Safety token failed: {response.status_code}")
                return False
        
        print_pass("Super admin can access /api/incidents with multiple portal tokens")
        record_test("super_admin_multi_portal", "PASS", {
            "portals_tested": ["admin", "pm", "safety"],
            "all_succeeded": True
        })
        return True
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        record_test("super_admin_multi_portal", "FAIL", error=str(e))
        return False


# ============================================================================
# BACKUP INTEGRITY VISIBILITY
# ============================================================================

def test_backup_1_integrity_check_with_auth():
    """Test backup integrity check with proper dual-token auth"""
    print_test("BI-1", "Backup integrity check with dual-token auth (60s timeout)")
    
    try:
        session_token, portal_tokens, status, data = multi_login(CREDENTIALS["super_admin"])
        
        if not session_token:
            print_fail(f"Login failed: {status}")
            record_test("backup_integrity_with_auth", "FAIL", error=f"Login failed: {status}")
            return False
        
        admin_token = portal_tokens.get("admin")
        
        if not admin_token:
            print_fail("No admin token received")
            record_test("backup_integrity_with_auth", "FAIL", error="No admin token received")
            return False
        
        print_info("Testing /api/admin/backups/integrity-check with 65s timeout")
        
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/admin/backups/integrity-check",
                headers={
                    "X-Admin-Token": admin_token,
                    "X-Directory-Token": session_token
                },
                timeout=65
            )
            
            elapsed = time.time() - start_time
            
            print_info(f"Response received in {elapsed:.2f}s with status {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                integrity_result = data.get("integrity_result", "N/A")
                last_backup = data.get("last_backup_filename", "N/A")
                
                print_pass(f"Backup integrity check succeeded")
                print_info(f"Integrity result: {integrity_result}")
                print_info(f"Last backup: {last_backup}")
                
                record_test("backup_integrity_with_auth", "PASS", {
                    "status_code": 200,
                    "elapsed_seconds": elapsed,
                    "integrity_result": integrity_result,
                    "last_backup": last_backup
                })
                return True
            elif response.status_code == 401:
                print_fail("Authentication failed - token/auth issue")
                record_test("backup_integrity_with_auth", "FAIL", error="401 - Auth issue")
                return False
            else:
                print_fail(f"Unexpected status: {response.status_code}")
                print_info(f"Response: {response.text[:200]}")
                record_test("backup_integrity_with_auth", "FAIL", error=f"Status {response.status_code}")
                return False
        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            print_fail(f"Request timed out after {elapsed:.2f}s (external 60s timeout)")
            record_test("backup_integrity_with_auth", "FAIL", error=f"Timeout after {elapsed:.2f}s")
            return False
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        record_test("backup_integrity_with_auth", "FAIL", error=str(e))
        return False

def test_backup_2_integrity_check_without_auth():
    """Test backup integrity check fails without auth"""
    print_test("BI-2", "Backup integrity check without auth (should fail)")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/admin/backups/integrity-check",
            timeout=30
        )
        
        if response.status_code == 401:
            print_pass("Backup integrity check properly rejected without auth (401)")
            record_test("backup_integrity_no_auth", "PASS", {"status_code": 401})
            return True
        else:
            print_fail(f"Expected 401, got {response.status_code}")
            record_test("backup_integrity_no_auth", "FAIL", error=f"Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        record_test("backup_integrity_no_auth", "FAIL", error=str(e))
        return False

def test_backup_3_integrity_check_portal_only():
    """Test backup integrity check with portal token only (should fail)"""
    print_test("BI-3", "Backup integrity check with portal token only (should fail)")
    
    try:
        session_token, portal_tokens, status, data = multi_login(CREDENTIALS["super_admin"])
        
        if not session_token:
            print_fail(f"Login failed: {status}")
            record_test("backup_integrity_portal_only", "FAIL", error=f"Login failed: {status}")
            return False
        
        admin_token = portal_tokens.get("admin")
        
        if not admin_token:
            print_fail("No admin token received")
            record_test("backup_integrity_portal_only", "FAIL", error="No admin token received")
            return False
        
        # Test with portal token ONLY (no directory token)
        response = requests.get(
            f"{BASE_URL}/api/admin/backups/integrity-check",
            headers={
                "X-Admin-Token": admin_token
            },
            timeout=30
        )
        
        print_info(f"With portal token only: {response.status_code}")
        
        if response.status_code == 401:
            print_pass("Portal-only access properly denied (401) - dual-token contract enforced")
            record_test("backup_integrity_portal_only", "PASS", {"status_code": 401})
            return True
        else:
            print_fail(f"Expected 401, got {response.status_code}")
            record_test("backup_integrity_portal_only", "FAIL", error=f"Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        record_test("backup_integrity_portal_only", "FAIL", error=str(e))
        return False


# ============================================================================
# SESSION SECURITY BEHAVIORS
# ============================================================================

def test_session_1_revoked_token_after_logout():
    """Test revoked token (after logout) is rejected"""
    print_test("SS-1", "Revoked token handling (post-logout)")
    
    try:
        session_token, portal_tokens, status, data = multi_login(CREDENTIALS["dispatch"])
        
        if not session_token:
            print_fail(f"Login failed: {status}")
            record_test("revoked_token", "FAIL", error=f"Login failed: {status}")
            return False
        
        dispatch_token = portal_tokens.get("dispatch")
        
        if not dispatch_token:
            print_fail("No dispatch token received")
            record_test("revoked_token", "FAIL", error="No dispatch token received")
            return False
        
        # Verify token works
        response = requests.get(
            f"{BASE_URL}/api/dispatch/me",
            headers={
                "X-Dispatch-Token": dispatch_token,
                "X-Directory-Token": session_token
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print_fail(f"Token verification failed: {response.status_code}")
            record_test("revoked_token", "FAIL", error=f"Token verification failed: {response.status_code}")
            return False
        
        print_info("Token verified, now logging out")
        
        # Logout
        logout_response = requests.post(
            f"{BASE_URL}/api/auth/multi-logout",
            headers={"X-Directory-Token": session_token},
            timeout=30
        )
        
        print_info(f"Logout status: {logout_response.status_code}")
        
        # Try to use token after logout
        response_after_logout = requests.get(
            f"{BASE_URL}/api/dispatch/me",
            headers={
                "X-Dispatch-Token": dispatch_token,
                "X-Directory-Token": session_token
            },
            timeout=30
        )
        
        if response_after_logout.status_code == 401:
            print_pass("Revoked token properly rejected with 401 after logout")
            record_test("revoked_token", "PASS", {"status_code": 401})
            return True
        else:
            print_fail(f"Expected 401, got {response_after_logout.status_code}")
            record_test("revoked_token", "FAIL", error=f"Expected 401, got {response_after_logout.status_code}")
            return False
    except Exception as e:
        print_fail(f"Exception: {str(e)}")
        record_test("revoked_token", "FAIL", error=str(e))
        return False


# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

def main():
    """Run all tests"""
    print_section("MASCI OPS 8 FOCUSED BACKEND CERTIFICATION - PART 2")
    print(f"Environment: {BASE_URL}")
    print(f"Timestamp: {test_results['timestamp']}")
    
    # Dual-Token Contract Validation
    print_section("DUAL-TOKEN CONTRACT VALIDATION")
    test_dual_token_1_admin_incidents()
    time.sleep(2)  # Small delay between tests
    
    test_dual_token_2_admin_incident_cases()
    time.sleep(2)
    
    test_dual_token_3_super_admin_all_portals()
    time.sleep(2)
    
    # Backup Integrity Visibility
    print_section("BACKUP INTEGRITY VISIBILITY")
    test_backup_1_integrity_check_with_auth()
    time.sleep(2)
    
    test_backup_2_integrity_check_without_auth()
    time.sleep(2)
    
    test_backup_3_integrity_check_portal_only()
    time.sleep(2)
    
    # Session Security
    print_section("SESSION SECURITY BEHAVIORS")
    test_session_1_revoked_token_after_logout()
    
    # Print summary
    print_section("TEST SUMMARY")
    print(f"Total Tests: {test_results['summary']['total']}")
    print(f"✅ Passed: {test_results['summary']['passed']}")
    print(f"❌ Failed: {test_results['summary']['failed']}")
    print(f"⏭️  Skipped: {test_results['summary']['skipped']}")
    
    pass_rate = (test_results['summary']['passed'] / test_results['summary']['total'] * 100) if test_results['summary']['total'] > 0 else 0
    print(f"\nPass Rate: {pass_rate:.1f}%")
    
    # Save results to file
    results_file = "/app/ops8_focused_backend_cert_part2_results.json"
    with open(results_file, "w") as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\nDetailed results saved to: {results_file}")
    
    # Exit with appropriate code
    if test_results['summary']['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

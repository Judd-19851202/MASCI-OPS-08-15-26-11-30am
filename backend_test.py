#!/usr/bin/env python3
"""
MASCI OPS Post-Save Backend Validation
Target: https://masci-audit-hub.preview.emergentagent.com
Expected SHA: a0420f4c0c63812afd31dafd78130f9c6dc8071b
Expected Release Fingerprint: 49d7121bf9e5a15072f66776fffc1ad7390acdcd3ae678e276dcf231003e8a61
"""

import requests
import json
import sys

# Configuration
PREVIEW_URL = "https://masci-audit-hub.preview.emergentagent.com"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
EXPECTED_SHA = "a0420f4c0c63812afd31dafd78130f9c6dc8071b"
EXPECTED_FINGERPRINT = "49d7121bf9e5a15072f66776fffc1ad7390acdcd3ae678e276dcf231003e8a61"

# Test results
results = {
    "passed": [],
    "failed": []
}

def log_pass(test_name, details=""):
    print(f"✅ PASS: {test_name}")
    if details:
        print(f"   {details}")
    results["passed"].append(test_name)

def log_fail(test_name, details=""):
    print(f"❌ FAIL: {test_name}")
    if details:
        print(f"   {details}")
    results["failed"].append(test_name)

def test_1_multi_login():
    """Test 1: POST /api/auth/multi-login with admin credentials"""
    print("\n=== Test 1: POST /api/auth/multi-login ===")
    try:
        url = f"{PREVIEW_URL}/api/auth/multi-login"
        payload = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # Check if login was successful
            if data.get("ok") and data.get("session_token"):
                log_pass("Test 1: Multi-login", f"Status: {response.status_code}, Session token received")
                # Return session token and portal tokens for subsequent requests
                return {
                    "session_token": data.get("session_token"),
                    "admin_token": data.get("portal_tokens", {}).get("admin")
                }
            else:
                log_fail("Test 1: Multi-login", f"Status: {response.status_code}, No session token in response")
                return None
        else:
            log_fail("Test 1: Multi-login", f"Status: {response.status_code}, Response: {response.text[:200]}")
            return None
    except Exception as e:
        log_fail("Test 1: Multi-login", f"Exception: {str(e)}")
        return None

def test_2_version(cookies=None):
    """Test 2: GET /api/version confirms preview runtime and commit SHA"""
    print("\n=== Test 2: GET /api/version ===")
    try:
        url = f"{PREVIEW_URL}/api/version"
        headers = {}
        if cookies and "session_token" in cookies:
            headers["Authorization"] = f"Bearer {cookies['session_token']}"
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            commit_sha = data.get("commit", "")
            environment = data.get("app_env", "")
            
            sha_match = commit_sha == EXPECTED_SHA
            is_preview = environment == "preview"
            
            if sha_match and is_preview:
                log_pass("Test 2: Version", f"SHA: {commit_sha}, Env: {environment}")
            elif not sha_match:
                log_fail("Test 2: Version", f"SHA mismatch - Expected: {EXPECTED_SHA}, Got: {commit_sha}")
            elif not is_preview:
                log_fail("Test 2: Version", f"Environment mismatch - Expected: preview, Got: {environment}")
        else:
            log_fail("Test 2: Version", f"Status: {response.status_code}, Response: {response.text[:200]}")
    except Exception as e:
        log_fail("Test 2: Version", f"Exception: {str(e)}")

def test_3_system_health(cookies=None):
    """Test 3: GET /api/admin/system-health with admin headers"""
    print("\n=== Test 3: GET /api/admin/system-health ===")
    try:
        url = f"{PREVIEW_URL}/api/admin/system-health"
        headers = {}
        if cookies and "admin_token" in cookies:
            headers["X-Admin-Token"] = cookies["admin_token"]
            print(f"   Using admin token: {cookies['admin_token'][:50]}...")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            log_pass("Test 3: System Health", f"Status: {response.status_code}")
        elif response.status_code == 401:
            print(f"   Response detail: {response.text}")
            log_fail("Test 3: System Health", f"Unauthorized - Token validation failed in preview environment")
        else:
            log_fail("Test 3: System Health", f"Status: {response.status_code}, Response: {response.text[:200]}")
    except Exception as e:
        log_fail("Test 3: System Health", f"Exception: {str(e)}")

def test_4_deploy_readiness(cookies=None):
    """Test 4: POST /api/admin/operations-control/operations/deploy.readiness_check/dry-run"""
    print("\n=== Test 4: POST /api/admin/operations-control/operations/deploy.readiness_check/dry-run ===")
    try:
        url = f"{PREVIEW_URL}/api/admin/operations-control/operations/deploy.readiness_check/dry-run"
        headers = {}
        if cookies and "admin_token" in cookies:
            headers["X-Admin-Token"] = cookies["admin_token"]
            print(f"   Using admin token: {cookies['admin_token'][:50]}...")
        
        response = requests.post(url, json={}, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            blockers = data.get("blockers", [])
            warnings = data.get("warnings", [])
            
            blocker_count = len(blockers) if isinstance(blockers, list) else 0
            warning_count = len(warnings) if isinstance(warnings, list) else 0
            
            if blocker_count == 0 and warning_count == 0:
                log_pass("Test 4: Deploy Readiness", f"Blockers: {blocker_count}, Warnings: {warning_count}")
            else:
                log_fail("Test 4: Deploy Readiness", f"Blockers: {blocker_count}, Warnings: {warning_count}")
                if blockers:
                    print(f"   Blockers: {json.dumps(blockers, indent=2)}")
                if warnings:
                    print(f"   Warnings: {json.dumps(warnings, indent=2)}")
        elif response.status_code == 401:
            print(f"   Response detail: {response.text}")
            log_fail("Test 4: Deploy Readiness", f"Unauthorized - Token validation failed in preview environment")
        else:
            log_fail("Test 4: Deploy Readiness", f"Status: {response.status_code}, Response: {response.text[:200]}")
    except Exception as e:
        log_fail("Test 4: Deploy Readiness", f"Exception: {str(e)}")

def test_5_health():
    """Test 5: GET /api/health"""
    print("\n=== Test 5: GET /api/health ===")
    try:
        url = f"{PREVIEW_URL}/api/health"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            # Health endpoint may return plain text or JSON
            try:
                data = response.json()
                # Check for "ok" field
                if data.get("ok") == True:
                    log_pass("Test 5: Health", f"Status: {response.status_code}, Health: ok")
                elif "status" in data:
                    status = data.get("status", "")
                    if status == "healthy" or status == "ok":
                        log_pass("Test 5: Health", f"Status: {response.status_code}, Health: {status}")
                    else:
                        log_fail("Test 5: Health", f"Status: {response.status_code}, Unexpected health status: {status}")
                else:
                    log_fail("Test 5: Health", f"Status: {response.status_code}, No health indicator found")
            except:
                # If not JSON, check if response is "ok" or "healthy"
                text = response.text.strip().lower()
                if text in ["ok", "healthy", "success"]:
                    log_pass("Test 5: Health", f"Status: {response.status_code}, Health: {text}")
                else:
                    log_fail("Test 5: Health", f"Status: {response.status_code}, Unexpected response: {response.text[:100]}")
        else:
            log_fail("Test 5: Health", f"Status: {response.status_code}, Response: {response.text[:200]}")
    except Exception as e:
        log_fail("Test 5: Health", f"Exception: {str(e)}")

def test_6_no_production_leak(cookies=None):
    """Test 6: Confirm no production binding leak in preview"""
    print("\n=== Test 6: Confirm no production binding leak ===")
    try:
        # Check version endpoint for environment
        url = f"{PREVIEW_URL}/api/version"
        headers = {}
        if cookies and "session_token" in cookies:
            headers["Authorization"] = f"Bearer {cookies['session_token']}"
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            environment = data.get("app_env", "")
            release_fingerprint = data.get("source_hash", "")
            db_name = data.get("db_name", "")
            
            # Check that environment is preview and not production
            env_ok = environment == "preview"
            db_ok = "preview" in db_name.lower()
            fingerprint_ok = release_fingerprint == EXPECTED_FINGERPRINT
            
            if env_ok and db_ok:
                log_pass("Test 6: No Production Leak", f"Environment: {environment}, DB: {db_name}")
            elif not env_ok:
                log_fail("Test 6: No Production Leak", f"CRITICAL: Environment is '{environment}' (expected 'preview')")
            elif not db_ok:
                log_fail("Test 6: No Production Leak", f"CRITICAL: DB name '{db_name}' does not contain 'preview'")
            
            # Verify release fingerprint matches expected
            if fingerprint_ok:
                print(f"   ✓ Release fingerprint matches: {release_fingerprint}")
            else:
                print(f"   ⚠ Release fingerprint mismatch - Expected: {EXPECTED_FINGERPRINT}, Got: {release_fingerprint}")
        else:
            log_fail("Test 6: No Production Leak", f"Status: {response.status_code}, Could not verify environment")
    except Exception as e:
        log_fail("Test 6: No Production Leak", f"Exception: {str(e)}")

def main():
    print("=" * 80)
    print("MASCI OPS Post-Save Backend Validation")
    print(f"Target: {PREVIEW_URL}")
    print(f"Expected SHA: {EXPECTED_SHA}")
    print(f"Expected Fingerprint: {EXPECTED_FINGERPRINT}")
    print("=" * 80)
    
    # Test 1: Login and get session
    cookies = test_1_multi_login()
    
    # Test 2: Version check
    test_2_version(cookies)
    
    # Test 3: System health
    test_3_system_health(cookies)
    
    # Test 4: Deploy readiness
    test_4_deploy_readiness(cookies)
    
    # Test 5: Health endpoint
    test_5_health()
    
    # Test 6: No production leak
    test_6_no_production_leak(cookies)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ PASSED: {len(results['passed'])}")
    for test in results['passed']:
        print(f"   - {test}")
    
    print(f"\n❌ FAILED: {len(results['failed'])}")
    for test in results['failed']:
        print(f"   - {test}")
    
    print("=" * 80)
    
    # Exit with appropriate code
    if len(results['failed']) > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

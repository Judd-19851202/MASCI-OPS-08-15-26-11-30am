#!/usr/bin/env python3
"""
WP-15 Final Backend/API Verification
=====================================
Verify final constitutional behaviors after governance scanner cleanup.

Expected state:
- legacy_but_migratable = 0
- manual_auth_header_construction = 0
- category_f = 0
- special_case_infrastructure = 52 (documented constitutional exemptions)
- Local certification bundle: 152 passed

Preview URL: https://backup-forensics.preview.emergentagent.com

Credentials:
- Super admin: jaymn.judd@mascigc.com / Maddix123!
- Admin only: ops8-admin-only-preview@example.com / AdminOnlyOps8!
- PM only: cert.pm@example.com / CertProof2026!
- Safety only: cert.safety@example.com / CertProof2026!
- Dispatch only: cert.dispatch@example.com / CertProof2026!
- HR only: cert.hr@example.com / CertProof2026!
- FL only: cert.foreman@example.com / CertProof2026!

Verification items:
1. Multi-login returns directory session + portal tokens
2. Governed admin API works with valid lifecycle headers and fails without/mismatched directory token
3. PM governed read works with valid lifecycle headers
4. Safety, Dispatch, and HR representative protected reads authenticate successfully
5. Asset-admin recovery / protected route behavior works for preview-safe paths
6. Emergency override API succeeds for valid admin governance session
7. No systemic 401 storm / regression across checks
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple

BASE_URL = "https://backup-forensics.preview.emergentagent.com"

# Test credentials
CREDENTIALS = {
    "super_admin": {"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
    "admin_only": {"email": "ops8-admin-only-preview@example.com", "password": "AdminOnlyOps8!"},
    "pm_only": {"email": "cert.pm@example.com", "password": "CertProof2026!"},
    "safety_only": {"email": "cert.safety@example.com", "password": "CertProof2026!"},
    "dispatch_only": {"email": "cert.dispatch@example.com", "password": "CertProof2026!"},
    "hr_only": {"email": "cert.hr@example.com", "password": "CertProof2026!"},
    "fl_only": {"email": "cert.foreman@example.com", "password": "CertProof2026!"},
}

results = {
    "test_run_timestamp": datetime.utcnow().isoformat() + "Z",
    "base_url": BASE_URL,
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
    }
}

def log_test(test_name: str, status: str, details: Dict[str, Any]):
    """Log test result"""
    results["tests"].append({
        "test": test_name,
        "status": status,
        "details": details,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })
    results["summary"]["total"] += 1
    if status == "PASS":
        results["summary"]["passed"] += 1
        print(f"✅ PASS: {test_name}")
    else:
        results["summary"]["failed"] += 1
        print(f"❌ FAIL: {test_name}")
    print(f"   Details: {json.dumps(details, indent=2)}")

def multi_login(email: str, password: str) -> Tuple[int, Dict[str, Any]]:
    """Perform multi-login and return status code and response"""
    url = f"{BASE_URL}/api/auth/multi-login"
    payload = {"email": email, "password": password}
    try:
        response = requests.post(url, json=payload, timeout=30)
        return response.status_code, response.json() if response.status_code == 200 else {"error": response.text}
    except Exception as e:
        return 0, {"error": str(e)}

def test_1_multi_login_directory_and_portal_tokens():
    """Test 1: Multi-login returns directory session + portal tokens"""
    print("\n" + "="*80)
    print("TEST 1: Multi-login returns directory session + portal tokens")
    print("="*80)
    
    # Test super admin
    status, response = multi_login(CREDENTIALS["super_admin"]["email"], CREDENTIALS["super_admin"]["password"])
    
    if status == 200:
        has_session_token = "session_token" in response
        has_portal_tokens = "portal_tokens" in response
        
        if has_session_token and has_portal_tokens:
            portal_count = len(response.get("portal_tokens", {}))
            log_test(
                "1. Multi-login directory session + portal tokens",
                "PASS",
                {
                    "status_code": status,
                    "has_session_token": has_session_token,
                    "session_token_length": len(response.get("session_token", "")),
                    "has_portal_tokens": has_portal_tokens,
                    "portal_count": portal_count,
                    "portals": list(response.get("portal_tokens", {}).keys()),
                    "message": f"Super admin received directory session token and {portal_count} portal tokens"
                }
            )
            return response  # Return for use in subsequent tests
        else:
            log_test(
                "1. Multi-login directory session + portal tokens",
                "FAIL",
                {
                    "status_code": status,
                    "has_session_token": has_session_token,
                    "has_portal_tokens": has_portal_tokens,
                    "message": "Missing session_token or portal_tokens in response"
                }
            )
    else:
        log_test(
            "1. Multi-login directory session + portal tokens",
            "FAIL",
            {
                "status_code": status,
                "error": response.get("error", "Unknown error"),
                "message": "Multi-login failed"
            }
        )
    return None

def test_2_governed_admin_api_with_lifecycle_headers(session_token: str, admin_token: str):
    """Test 2: Governed admin API works with valid lifecycle headers and fails without/mismatched directory token"""
    print("\n" + "="*80)
    print("TEST 2: Governed admin API with lifecycle headers")
    print("="*80)
    
    url = f"{BASE_URL}/api/admin/governance/overview"
    
    # Test 2a: Valid headers (both tokens)
    headers_valid = {
        "X-Directory-Token": session_token,
        "X-Admin-Token": admin_token
    }
    try:
        response_valid = requests.get(url, headers=headers_valid, timeout=30)
        status_valid = response_valid.status_code
    except Exception as e:
        status_valid = 0
    
    # Test 2b: Missing directory token
    headers_no_dir = {
        "X-Admin-Token": admin_token
    }
    try:
        response_no_dir = requests.get(url, headers=headers_no_dir, timeout=30)
        status_no_dir = response_no_dir.status_code
    except Exception as e:
        status_no_dir = 0
    
    # Test 2c: Mismatched directory token
    headers_mismatch = {
        "X-Directory-Token": "fake-mismatched-token-12345",
        "X-Admin-Token": admin_token
    }
    try:
        response_mismatch = requests.get(url, headers=headers_mismatch, timeout=30)
        status_mismatch = response_mismatch.status_code
    except Exception as e:
        status_mismatch = 0
    
    # Evaluate results
    valid_success = status_valid == 200
    no_dir_denied = status_no_dir in [401, 403]
    mismatch_denied = status_mismatch in [401, 403]
    
    if valid_success and no_dir_denied and mismatch_denied:
        log_test(
            "2. Governed admin API lifecycle headers",
            "PASS",
            {
                "valid_headers_status": status_valid,
                "missing_directory_token_status": status_no_dir,
                "mismatched_directory_token_status": status_mismatch,
                "message": "Governed admin API correctly requires both X-Admin-Token and X-Directory-Token. Missing or mismatched tokens denied."
            }
        )
    else:
        log_test(
            "2. Governed admin API lifecycle headers",
            "FAIL",
            {
                "valid_headers_status": status_valid,
                "valid_success": valid_success,
                "missing_directory_token_status": status_no_dir,
                "no_dir_denied": no_dir_denied,
                "mismatched_directory_token_status": status_mismatch,
                "mismatch_denied": mismatch_denied,
                "message": "Governed admin API lifecycle header enforcement failed"
            }
        )

def test_3_pm_governed_read_with_lifecycle_headers():
    """Test 3: PM governed read works with valid lifecycle headers"""
    print("\n" + "="*80)
    print("TEST 3: PM governed read with lifecycle headers")
    print("="*80)
    
    # Login as PM
    status, response = multi_login(CREDENTIALS["pm_only"]["email"], CREDENTIALS["pm_only"]["password"])
    
    if status != 200:
        log_test(
            "3. PM governed read with lifecycle headers",
            "FAIL",
            {
                "status_code": status,
                "message": "PM login failed"
            }
        )
        return
    
    session_token = response.get("session_token")
    pm_token = response.get("portal_tokens", {}).get("pm")
    
    if not session_token or not pm_token:
        log_test(
            "3. PM governed read with lifecycle headers",
            "FAIL",
            {
                "has_session_token": bool(session_token),
                "has_pm_token": bool(pm_token),
                "message": "PM login missing required tokens"
            }
        )
        return
    
    # Test PM governed endpoint
    url = f"{BASE_URL}/api/pm/command-center/overview"
    headers = {
        "X-Directory-Token": session_token,
        "X-PM-Token": pm_token
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        status_code = response.status_code
        
        if status_code == 200:
            log_test(
                "3. PM governed read with lifecycle headers",
                "PASS",
                {
                    "status_code": status_code,
                    "endpoint": url,
                    "message": "PM governed read with valid X-PM-Token + X-Directory-Token successful"
                }
            )
        else:
            log_test(
                "3. PM governed read with lifecycle headers",
                "FAIL",
                {
                    "status_code": status_code,
                    "endpoint": url,
                    "message": f"PM governed read failed with status {status_code}"
                }
            )
    except Exception as e:
        log_test(
            "3. PM governed read with lifecycle headers",
            "FAIL",
            {
                "error": str(e),
                "message": "PM governed read request failed"
            }
        )

def test_4_representative_protected_reads():
    """Test 4: Safety, Dispatch, and HR representative protected reads authenticate successfully"""
    print("\n" + "="*80)
    print("TEST 4: Representative protected reads (Safety, Dispatch, HR)")
    print("="*80)
    
    test_cases = [
        {
            "role": "Safety",
            "credentials": CREDENTIALS["safety_only"],
            "portal_key": "safety",
            "endpoint": "/api/safety/overview",
            "header_key": "X-Safety-Token"
        },
        {
            "role": "Dispatch",
            "credentials": CREDENTIALS["dispatch_only"],
            "portal_key": "dispatch",
            "endpoint": "/api/dispatch/command/summary",
            "header_key": "X-Dispatch-Token"
        },
        {
            "role": "HR",
            "credentials": CREDENTIALS["hr_only"],
            "portal_key": "hr",
            "endpoint": "/api/hr/employees",
            "header_key": "X-HR-Token"
        }
    ]
    
    all_passed = True
    details = []
    
    for test_case in test_cases:
        # Login
        status, response = multi_login(test_case["credentials"]["email"], test_case["credentials"]["password"])
        
        if status != 200:
            all_passed = False
            details.append({
                "role": test_case["role"],
                "login_status": status,
                "success": False,
                "message": f"{test_case['role']} login failed"
            })
            continue
        
        session_token = response.get("session_token")
        portal_token = response.get("portal_tokens", {}).get(test_case["portal_key"])
        
        if not session_token or not portal_token:
            all_passed = False
            details.append({
                "role": test_case["role"],
                "has_session_token": bool(session_token),
                "has_portal_token": bool(portal_token),
                "success": False,
                "message": f"{test_case['role']} login missing required tokens"
            })
            continue
        
        # Test protected endpoint
        url = f"{BASE_URL}{test_case['endpoint']}"
        headers = {
            "X-Directory-Token": session_token,
            test_case["header_key"]: portal_token
        }
        
        try:
            endpoint_response = requests.get(url, headers=headers, timeout=30)
            endpoint_status = endpoint_response.status_code
            
            if endpoint_status == 200:
                details.append({
                    "role": test_case["role"],
                    "endpoint": test_case["endpoint"],
                    "status_code": endpoint_status,
                    "success": True,
                    "message": f"{test_case['role']} protected read successful"
                })
            else:
                all_passed = False
                details.append({
                    "role": test_case["role"],
                    "endpoint": test_case["endpoint"],
                    "status_code": endpoint_status,
                    "success": False,
                    "message": f"{test_case['role']} protected read failed with status {endpoint_status}"
                })
        except Exception as e:
            all_passed = False
            details.append({
                "role": test_case["role"],
                "endpoint": test_case["endpoint"],
                "error": str(e),
                "success": False,
                "message": f"{test_case['role']} protected read request failed"
            })
    
    if all_passed:
        log_test(
            "4. Representative protected reads (Safety, Dispatch, HR)",
            "PASS",
            {
                "details": details,
                "message": "All representative protected reads (Safety, Dispatch, HR) authenticated successfully"
            }
        )
    else:
        log_test(
            "4. Representative protected reads (Safety, Dispatch, HR)",
            "FAIL",
            {
                "details": details,
                "message": "One or more representative protected reads failed"
            }
        )

def test_5_asset_admin_recovery_protected_routes(session_token: str, admin_token: str):
    """Test 5: Asset-admin recovery / protected route behavior for preview-safe paths"""
    print("\n" + "="*80)
    print("TEST 5: Asset-admin recovery / protected route behavior")
    print("="*80)
    
    # Test preview-safe asset/admin recovery endpoints
    test_endpoints = [
        "/api/admin/recovery/snapshot",
        "/api/admin/backup-verification/state",
        "/api/admin/deployment-readiness"
    ]
    
    all_passed = True
    details = []
    
    headers = {
        "X-Directory-Token": session_token,
        "X-Admin-Token": admin_token
    }
    
    for endpoint in test_endpoints:
        url = f"{BASE_URL}{endpoint}"
        try:
            response = requests.get(url, headers=headers, timeout=30)
            status_code = response.status_code
            
            if status_code == 200:
                details.append({
                    "endpoint": endpoint,
                    "status_code": status_code,
                    "success": True,
                    "message": f"Asset-admin recovery endpoint {endpoint} accessible"
                })
            else:
                all_passed = False
                details.append({
                    "endpoint": endpoint,
                    "status_code": status_code,
                    "success": False,
                    "message": f"Asset-admin recovery endpoint {endpoint} failed with status {status_code}"
                })
        except Exception as e:
            all_passed = False
            details.append({
                "endpoint": endpoint,
                "error": str(e),
                "success": False,
                "message": f"Asset-admin recovery endpoint {endpoint} request failed"
            })
    
    if all_passed:
        log_test(
            "5. Asset-admin recovery / protected route behavior",
            "PASS",
            {
                "details": details,
                "message": "All asset-admin recovery / protected routes accessible for preview-safe paths"
            }
        )
    else:
        log_test(
            "5. Asset-admin recovery / protected route behavior",
            "FAIL",
            {
                "details": details,
                "message": "One or more asset-admin recovery / protected routes failed"
            }
        )

def test_6_emergency_override_api(session_token: str, admin_token: str):
    """Test 6: Emergency override API succeeds for valid admin governance session"""
    print("\n" + "="*80)
    print("TEST 6: Emergency override API")
    print("="*80)
    
    url = f"{BASE_URL}/api/admin/governance/emergency-overrides"
    headers = {
        "X-Directory-Token": session_token,
        "X-Admin-Token": admin_token
    }
    
    # Create emergency override payload
    payload = {
        "action_key": "operational_case.close",
        "module_key": "operations_control",
        "record_type": "operational_case",
        "record_id": "test-wp15-final-verification",
        "company_id": "MASCI",
        "project_number": "TEST-001",
        "denied_policy_id": "operational_case_close_policy",
        "justification": "WP-15 final backend verification - emergency override API test",
        "operational_urgency": "high",
        "evidence": ["Testing emergency override API for WP-15 final verification"],
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        status_code = response.status_code
        
        if status_code == 200:
            response_data = response.json()
            override_id = response_data.get("override", {}).get("override_id")
            log_test(
                "6. Emergency override API",
                "PASS",
                {
                    "status_code": status_code,
                    "override_id": override_id,
                    "message": "Emergency override API succeeded for valid admin governance session"
                }
            )
        else:
            log_test(
                "6. Emergency override API",
                "FAIL",
                {
                    "status_code": status_code,
                    "response": response.text[:500],
                    "message": f"Emergency override API failed with status {status_code}"
                }
            )
    except Exception as e:
        log_test(
            "6. Emergency override API",
            "FAIL",
            {
                "error": str(e),
                "message": "Emergency override API request failed"
            }
        )

def test_7_no_systemic_401_storm(session_token: str, admin_token: str):
    """Test 7: No systemic 401 storm / regression across checks"""
    print("\n" + "="*80)
    print("TEST 7: No systemic 401 storm / regression")
    print("="*80)
    
    # Test multiple sequential requests to different governed endpoints
    test_endpoints = [
        "/api/admin/governance/overview",
        "/api/admin/operations-control/registry",
        "/api/admin/platform/status",
        "/api/admin/governance/decisions",
        "/api/admin/operations-control/cases"
    ]
    
    headers = {
        "X-Directory-Token": session_token,
        "X-Admin-Token": admin_token
    }
    
    results_list = []
    auth_errors = 0
    
    for endpoint in test_endpoints:
        url = f"{BASE_URL}{endpoint}"
        try:
            response = requests.get(url, headers=headers, timeout=30)
            status_code = response.status_code
            
            results_list.append({
                "endpoint": endpoint,
                "status_code": status_code
            })
            
            if status_code in [401, 403]:
                auth_errors += 1
        except Exception as e:
            results_list.append({
                "endpoint": endpoint,
                "error": str(e)
            })
            auth_errors += 1
    
    if auth_errors == 0:
        log_test(
            "7. No systemic 401 storm / regression",
            "PASS",
            {
                "total_requests": len(test_endpoints),
                "auth_errors": auth_errors,
                "results": results_list,
                "message": f"No 401/403 errors in {len(test_endpoints)} sequential requests. No auth storm detected."
            }
        )
    else:
        log_test(
            "7. No systemic 401 storm / regression",
            "FAIL",
            {
                "total_requests": len(test_endpoints),
                "auth_errors": auth_errors,
                "results": results_list,
                "message": f"Detected {auth_errors} auth errors in {len(test_endpoints)} requests. Possible auth storm."
            }
        )

def main():
    print("="*80)
    print("WP-15 FINAL BACKEND/API VERIFICATION")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Test run: {datetime.utcnow().isoformat()}Z")
    print("="*80)
    
    # Test 1: Multi-login
    login_response = test_1_multi_login_directory_and_portal_tokens()
    
    if not login_response:
        print("\n❌ CRITICAL: Multi-login failed. Cannot proceed with remaining tests.")
        return
    
    session_token = login_response.get("session_token")
    admin_token = login_response.get("portal_tokens", {}).get("admin")
    
    if not session_token or not admin_token:
        print("\n❌ CRITICAL: Missing session_token or admin_token. Cannot proceed with remaining tests.")
        return
    
    # Test 2: Governed admin API with lifecycle headers
    test_2_governed_admin_api_with_lifecycle_headers(session_token, admin_token)
    
    # Test 3: PM governed read
    test_3_pm_governed_read_with_lifecycle_headers()
    
    # Test 4: Representative protected reads
    test_4_representative_protected_reads()
    
    # Test 5: Asset-admin recovery / protected routes
    test_5_asset_admin_recovery_protected_routes(session_token, admin_token)
    
    # Test 6: Emergency override API
    test_6_emergency_override_api(session_token, admin_token)
    
    # Test 7: No systemic 401 storm
    test_7_no_systemic_401_storm(session_token, admin_token)
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total tests: {results['summary']['total']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Pass rate: {results['summary']['passed'] / results['summary']['total'] * 100:.1f}%")
    print("="*80)
    
    # Save results to file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = f"/app/wp15_final_backend_verification_results_{timestamp}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_file}")
    
    # Final verdict
    if results['summary']['failed'] == 0:
        print("\n✅ FINAL VERDICT: PASS - All WP-15 final backend verification tests passed.")
    else:
        print(f"\n❌ FINAL VERDICT: FAIL - {results['summary']['failed']} test(s) failed.")

if __name__ == "__main__":
    main()

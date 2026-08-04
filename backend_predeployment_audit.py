#!/usr/bin/env python3
"""
Pre-Deployment Backend Audit
Scope: READ-ONLY verification of:
1. Preview API / version / platform identity surfaces (internal consistency, release-attestation drift)
2. Production identity surfaces (commit bd9bdd2012c4f2e31b57d7390218b20c361c6dcc, source hash 665ea6071d75dd046905a35dfe8dcea4)
3. Production backup health and certification routes (reachable with dual admin tokens)
4. Backend deploy blockers or inconsistent auth/token requirements
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
PREVIEW_BASE_URL = "https://masci-audit-hub.preview.emergentagent.com/api"
PRODUCTION_BASE_URL = "https://mascidocs.com/api"

# Expected production identity
EXPECTED_PROD_COMMIT = "bd9bdd2012c4f2e31b57d7390218b20c361c6dcc"
EXPECTED_PROD_SOURCE_HASH = "665ea6071d75dd046905a35dfe8dcea4"

# Admin credentials from test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test results
results = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "warnings": 0
    }
}

def log_test(name, status, details, severity="info"):
    """Log a test result"""
    test_result = {
        "name": name,
        "status": status,
        "details": details,
        "severity": severity
    }
    results["tests"].append(test_result)
    results["summary"]["total"] += 1
    
    if status == "PASS":
        results["summary"]["passed"] += 1
        print(f"✅ PASS: {name}")
    elif status == "FAIL":
        results["summary"]["failed"] += 1
        print(f"❌ FAIL: {name}")
        print(f"   Details: {details}")
    elif status == "WARNING":
        results["summary"]["warnings"] += 1
        print(f"⚠️  WARNING: {name}")
        print(f"   Details: {details}")
    
    if severity == "critical":
        print(f"   🚨 CRITICAL: {details}")

def test_preview_version_identity():
    """Test 1: Preview API version and platform identity surfaces"""
    try:
        response = requests.get(f"{PREVIEW_BASE_URL}/version", timeout=15)
        
        if response.status_code != 200:
            log_test(
                "Preview /api/version endpoint",
                "FAIL",
                f"Expected 200, got {response.status_code}",
                "critical"
            )
            return None
        
        data = response.json()
        
        # Check internal consistency
        issues = []
        
        if not data.get("commit"):
            issues.append("Missing commit field")
        
        if not data.get("source_hash"):
            issues.append("Missing source_hash field")
        
        if not data.get("app_env"):
            issues.append("Missing app_env field")
        elif data.get("app_env") != "preview":
            issues.append(f"app_env is '{data.get('app_env')}', expected 'preview'")
        
        # Check frontend/backend release match
        if "frontend_backend_release_match" in data:
            if not data["frontend_backend_release_match"]:
                issues.append("frontend_backend_release_match is false - release attestation drift detected")
        
        # Check runtime identity
        if "runtime_identity" in data:
            runtime_id = data["runtime_identity"]
            if runtime_id.get("status") not in ["NOT_APPLICABLE", "MATCH"]:
                issues.append(f"runtime_identity status is '{runtime_id.get('status')}' - potential drift")
        
        if issues:
            log_test(
                "Preview API identity surfaces - internal consistency",
                "WARNING",
                f"Issues found: {', '.join(issues)}. Data: commit={data.get('commit')}, source_hash={data.get('source_hash')}, app_env={data.get('app_env')}",
                "medium"
            )
        else:
            log_test(
                "Preview API identity surfaces - internal consistency",
                "PASS",
                f"All identity surfaces consistent. commit={data.get('commit')}, source_hash={data.get('source_hash')}, app_env={data.get('app_env')}, frontend_backend_release_match={data.get('frontend_backend_release_match')}"
            )
        
        return data
        
    except Exception as e:
        log_test(
            "Preview /api/version endpoint",
            "FAIL",
            f"Exception: {str(e)}",
            "critical"
        )
        return None

def test_production_version_identity():
    """Test 2: Production API version and identity surfaces"""
    try:
        response = requests.get(f"{PRODUCTION_BASE_URL}/version", timeout=15)
        
        if response.status_code != 200:
            log_test(
                "Production /api/version endpoint",
                "FAIL",
                f"Expected 200, got {response.status_code}",
                "critical"
            )
            return None
        
        data = response.json()
        
        # Check expected commit
        actual_commit = data.get("commit", "")
        if actual_commit != EXPECTED_PROD_COMMIT:
            log_test(
                "Production commit verification",
                "FAIL",
                f"Expected commit {EXPECTED_PROD_COMMIT}, got {actual_commit}",
                "critical"
            )
        else:
            log_test(
                "Production commit verification",
                "PASS",
                f"Commit matches expected: {EXPECTED_PROD_COMMIT}"
            )
        
        # Check expected source hash
        actual_hash = data.get("source_hash", "")
        if actual_hash != EXPECTED_PROD_SOURCE_HASH:
            log_test(
                "Production source hash verification",
                "FAIL",
                f"Expected source_hash {EXPECTED_PROD_SOURCE_HASH}, got {actual_hash}",
                "critical"
            )
        else:
            log_test(
                "Production source hash verification",
                "PASS",
                f"Source hash matches expected: {EXPECTED_PROD_SOURCE_HASH}"
            )
        
        return data
        
    except Exception as e:
        log_test(
            "Production /api/version endpoint",
            "FAIL",
            f"Exception: {str(e)}",
            "critical"
        )
        return None

def test_production_backup_health():
    """Test 3: Production backup health and certification routes with dual admin tokens"""
    try:
        # First, authenticate to get tokens
        login_response = requests.post(
            f"{PRODUCTION_BASE_URL}/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15
        )
        
        if login_response.status_code != 200:
            log_test(
                "Production admin authentication",
                "FAIL",
                f"Login failed with status {login_response.status_code}",
                "critical"
            )
            return
        
        login_data = login_response.json()
        session_token = login_data.get("session_token")
        admin_token = login_data.get("portal_tokens", {}).get("admin")
        
        if not session_token or not admin_token:
            log_test(
                "Production admin authentication",
                "FAIL",
                "Missing session_token or admin token in login response",
                "critical"
            )
            return
        
        log_test(
            "Production admin authentication",
            "PASS",
            f"Successfully authenticated. Session token length: {len(session_token)}, Admin token length: {len(admin_token)}"
        )
        
        # Test backup integrity check with dual tokens
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        backup_response = requests.get(
            f"{PRODUCTION_BASE_URL}/admin/backups/integrity-check",
            headers=headers,
            timeout=60  # Longer timeout for backup check
        )
        
        if backup_response.status_code != 200:
            log_test(
                "Production backup integrity check",
                "FAIL",
                f"Expected 200, got {backup_response.status_code}. Response: {backup_response.text[:500]}",
                "critical"
            )
            return
        
        backup_data = backup_response.json()
        
        # Check backup health
        integrity_result = backup_data.get("integrity_result")
        if integrity_result != "PASS":
            log_test(
                "Production backup health",
                "FAIL",
                f"Backup integrity result is '{integrity_result}', expected 'PASS'. Missing: {backup_data.get('missing_from_backup', [])}",
                "critical"
            )
        else:
            log_test(
                "Production backup health",
                "PASS",
                f"Backup integrity PASS. Last backup: {backup_data.get('last_backup_filename')}, Collections: {backup_data.get('collections_captured', 'N/A')}, Documents: {backup_data.get('documents_captured', 'N/A')}"
            )
        
        # Test deployment readiness endpoint
        readiness_response = requests.get(
            f"{PRODUCTION_BASE_URL}/admin/deployment-readiness",
            headers=headers,
            timeout=15
        )
        
        if readiness_response.status_code != 200:
            log_test(
                "Production deployment readiness",
                "WARNING",
                f"Expected 200, got {readiness_response.status_code}",
                "medium"
            )
        else:
            readiness_data = readiness_response.json()
            decision = readiness_data.get("decision")
            blocking_gates = readiness_data.get("blocking_gates", [])
            
            if decision != "pass":
                log_test(
                    "Production deployment readiness",
                    "WARNING",
                    f"Decision is '{decision}', blocking gates: {blocking_gates}",
                    "medium"
                )
            else:
                log_test(
                    "Production deployment readiness",
                    "PASS",
                    f"Deployment readiness decision: {decision}"
                )
        
    except Exception as e:
        log_test(
            "Production backup health and certification routes",
            "FAIL",
            f"Exception: {str(e)}",
            "critical"
        )

def test_auth_token_consistency():
    """Test 4: Backend auth/token requirements consistency"""
    try:
        # Test preview auth flow
        login_response = requests.post(
            f"{PREVIEW_BASE_URL}/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15
        )
        
        if login_response.status_code != 200:
            log_test(
                "Preview auth flow consistency",
                "FAIL",
                f"Multi-login failed with status {login_response.status_code}",
                "critical"
            )
            return
        
        login_data = login_response.json()
        
        # Check token structure
        issues = []
        
        if "session_token" not in login_data:
            issues.append("Missing session_token in multi-login response")
        
        if "portal_tokens" not in login_data:
            issues.append("Missing portal_tokens in multi-login response")
        elif not isinstance(login_data["portal_tokens"], dict):
            issues.append("portal_tokens is not a dict")
        elif "admin" not in login_data["portal_tokens"]:
            issues.append("Missing admin token in portal_tokens")
        
        if "user" not in login_data:
            issues.append("Missing user object in multi-login response")
        
        if issues:
            log_test(
                "Preview auth token structure",
                "FAIL",
                f"Token structure issues: {', '.join(issues)}",
                "critical"
            )
            return
        
        log_test(
            "Preview auth token structure",
            "PASS",
            f"Auth token structure consistent. Portal tokens: {list(login_data['portal_tokens'].keys())}"
        )
        
        # Test dual-token requirement for protected endpoints
        session_token = login_data["session_token"]
        admin_token = login_data["portal_tokens"]["admin"]
        
        # Test with both tokens (should succeed)
        headers_dual = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        response_dual = requests.get(
            f"{PREVIEW_BASE_URL}/admin/deployment-readiness",
            headers=headers_dual,
            timeout=15
        )
        
        # Test with only admin token (should fail)
        headers_single = {
            "X-Admin-Token": admin_token
        }
        
        response_single = requests.get(
            f"{PREVIEW_BASE_URL}/admin/deployment-readiness",
            headers=headers_single,
            timeout=15
        )
        
        # Analyze results
        if response_dual.status_code == 200 and response_single.status_code == 401:
            log_test(
                "Dual-token auth requirement",
                "PASS",
                "Protected endpoints correctly require both X-Admin-Token and X-Directory-Token"
            )
        elif response_dual.status_code != 200:
            log_test(
                "Dual-token auth requirement",
                "FAIL",
                f"Dual-token request failed with status {response_dual.status_code}",
                "critical"
            )
        elif response_single.status_code == 200:
            log_test(
                "Dual-token auth requirement",
                "WARNING",
                "Single admin token was accepted (expected 401). Potential security issue.",
                "high"
            )
        else:
            log_test(
                "Dual-token auth requirement",
                "WARNING",
                f"Unexpected behavior: dual={response_dual.status_code}, single={response_single.status_code}",
                "medium"
            )
        
    except Exception as e:
        log_test(
            "Auth token consistency check",
            "FAIL",
            f"Exception: {str(e)}",
            "critical"
        )

def test_preview_health_endpoints():
    """Test 5: Preview health and readiness endpoints"""
    try:
        # Test /api/health
        health_response = requests.get(f"{PREVIEW_BASE_URL}/health", timeout=15)
        
        if health_response.status_code != 200:
            log_test(
                "Preview /api/health endpoint",
                "FAIL",
                f"Expected 200, got {health_response.status_code}",
                "critical"
            )
        else:
            health_data = health_response.json()
            if health_data.get("ok") != True:
                log_test(
                    "Preview health status",
                    "WARNING",
                    f"Health check returned ok={health_data.get('ok')}",
                    "medium"
                )
            else:
                log_test(
                    "Preview health status",
                    "PASS",
                    f"Health check OK. Runtime identity: {health_data.get('runtime_identity', {}).get('status')}"
                )
        
        # Test /api/ready
        ready_response = requests.get(f"{PREVIEW_BASE_URL}/ready", timeout=15)
        
        if ready_response.status_code != 200:
            log_test(
                "Preview /api/ready endpoint",
                "FAIL",
                f"Expected 200, got {ready_response.status_code}",
                "critical"
            )
        else:
            ready_data = ready_response.json()
            if ready_data.get("ok") != True or ready_data.get("state") != "ready":
                log_test(
                    "Preview readiness status",
                    "WARNING",
                    f"Readiness check: ok={ready_data.get('ok')}, state={ready_data.get('state')}",
                    "medium"
                )
            else:
                log_test(
                    "Preview readiness status",
                    "PASS",
                    f"System ready. mongo_ok={ready_data.get('mongo_ok')}, event_loop_ok={ready_data.get('event_loop_ok')}"
                )
        
    except Exception as e:
        log_test(
            "Preview health endpoints",
            "FAIL",
            f"Exception: {str(e)}",
            "critical"
        )

def main():
    print("=" * 80)
    print("PRE-DEPLOYMENT BACKEND AUDIT")
    print("=" * 80)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Preview Base URL: {PREVIEW_BASE_URL}")
    print(f"Production Base URL: {PRODUCTION_BASE_URL}")
    print("=" * 80)
    print()
    
    # Run all tests
    print("TEST 1: Preview API Identity Surfaces")
    print("-" * 80)
    test_preview_version_identity()
    print()
    
    print("TEST 2: Production API Identity Surfaces")
    print("-" * 80)
    test_production_version_identity()
    print()
    
    print("TEST 3: Production Backup Health and Certification Routes")
    print("-" * 80)
    test_production_backup_health()
    print()
    
    print("TEST 4: Auth Token Consistency")
    print("-" * 80)
    test_auth_token_consistency()
    print()
    
    print("TEST 5: Preview Health Endpoints")
    print("-" * 80)
    test_preview_health_endpoints()
    print()
    
    # Print summary
    print("=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {results['summary']['total']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Warnings: {results['summary']['warnings']}")
    print()
    
    # Determine overall status
    if results['summary']['failed'] > 0:
        print("❌ OVERALL STATUS: FAILED - Deploy blockers found")
        exit_code = 1
    elif results['summary']['warnings'] > 0:
        print("⚠️  OVERALL STATUS: WARNINGS - Review recommended before deployment")
        exit_code = 0
    else:
        print("✅ OVERALL STATUS: PASSED - No deploy blockers found")
        exit_code = 0
    
    # Save results to file
    output_file = "/app/backend_predeployment_audit_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    print("=" * 80)
    
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

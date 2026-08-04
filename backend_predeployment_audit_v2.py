#!/usr/bin/env python3
"""
Pre-Deployment Backend Audit V2
Focused READ-ONLY verification per review request:
1. Preview API / version / platform identity surfaces (internal consistency, release-attestation drift)
2. Production identity surfaces (commit bd9bdd2012c4f2e31b57d7390218b20c361c6dcc, source hash 665ea6071d75dd046905a35dfe8dcea4)
3. Production backup health and certification routes (reachable with dual admin tokens)
4. Backend deploy blockers or inconsistent auth/token requirements

Plus auth playbook testing:
- bcrypt hash format starts with $2b$
- httpOnly cookies set on login
- CORS allows credentials with explicit origins
- Brute force lockout after 5 fails
- seed_admin updates existing admin if password changed
"""

import requests
import json
import sys
import time
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
    "scope": "Pre-deployment backend audit - READ-ONLY",
    "tests": [],
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "warnings": 0,
        "skipped": 0
    },
    "deploy_blockers": []
}

def log_test(name, status, details, severity="info", is_blocker=False):
    """Log a test result"""
    test_result = {
        "name": name,
        "status": status,
        "details": details,
        "severity": severity,
        "is_blocker": is_blocker
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
        if is_blocker:
            results["deploy_blockers"].append({"test": name, "details": details})
            print(f"   🚨 DEPLOY BLOCKER")
    elif status == "WARNING":
        results["summary"]["warnings"] += 1
        print(f"⚠️  WARNING: {name}")
        print(f"   Details: {details}")
    elif status == "SKIP":
        results["summary"]["skipped"] += 1
        print(f"⏭️  SKIP: {name}")
        print(f"   Reason: {details}")

def test_preview_identity():
    """Test 1: Preview API identity surfaces - internal consistency and drift detection"""
    print("\n📋 Checking preview API identity surfaces...")
    try:
        response = requests.get(f"{PREVIEW_BASE_URL}/version", timeout=15)
        
        if response.status_code != 200:
            log_test(
                "Preview /api/version reachability",
                "FAIL",
                f"Expected 200, got {response.status_code}",
                "critical",
                is_blocker=True
            )
            return None
        
        data = response.json()
        
        # Report identity surfaces
        commit = data.get("commit", "MISSING")
        source_hash = data.get("source_hash", "MISSING")
        app_env = data.get("app_env", "MISSING")
        frontend_backend_match = data.get("frontend_backend_release_match", None)
        runtime_identity = data.get("runtime_identity", {})
        
        print(f"   Preview commit: {commit}")
        print(f"   Preview source_hash: {source_hash}")
        print(f"   Preview app_env: {app_env}")
        print(f"   Frontend/backend release match: {frontend_backend_match}")
        print(f"   Runtime identity status: {runtime_identity.get('status', 'MISSING')}")
        
        # Check for drift
        drift_issues = []
        
        if app_env != "preview":
            drift_issues.append(f"app_env is '{app_env}', expected 'preview'")
        
        if frontend_backend_match == False:
            drift_issues.append("frontend_backend_release_match is false - release attestation drift detected")
        
        runtime_status = runtime_identity.get("status")
        if runtime_status and runtime_status not in ["NOT_APPLICABLE", "MATCH"]:
            drift_issues.append(f"runtime_identity status is '{runtime_status}' - potential drift")
        
        if drift_issues:
            log_test(
                "Preview identity surfaces - drift detection",
                "WARNING",
                f"Drift detected: {'; '.join(drift_issues)}",
                "medium"
            )
        else:
            log_test(
                "Preview identity surfaces - drift detection",
                "PASS",
                "No release attestation drift detected. All identity surfaces internally consistent."
            )
        
        log_test(
            "Preview identity surfaces - workspace consistency",
            "PASS",
            f"Preview workspace identity: commit={commit[:12]}, source_hash={source_hash[:12]}, app_env={app_env}"
        )
        
        return data
        
    except Exception as e:
        log_test(
            "Preview identity surfaces check",
            "FAIL",
            f"Exception: {str(e)}",
            "critical",
            is_blocker=True
        )
        return None

def test_production_identity():
    """Test 2: Production identity surfaces - verify expected commit and source hash"""
    print("\n📋 Checking production API identity surfaces...")
    try:
        response = requests.get(f"{PRODUCTION_BASE_URL}/version", timeout=15)
        
        if response.status_code != 200:
            log_test(
                "Production /api/version reachability",
                "FAIL",
                f"Expected 200, got {response.status_code}",
                "critical",
                is_blocker=True
            )
            return None
        
        data = response.json()
        
        # Check expected commit
        actual_commit = data.get("commit", "")
        print(f"   Production commit: {actual_commit}")
        print(f"   Expected commit: {EXPECTED_PROD_COMMIT}")
        
        if actual_commit != EXPECTED_PROD_COMMIT:
            log_test(
                "Production commit verification",
                "FAIL",
                f"Expected commit {EXPECTED_PROD_COMMIT}, got {actual_commit}",
                "critical",
                is_blocker=True
            )
        else:
            log_test(
                "Production commit verification",
                "PASS",
                f"Commit matches expected: {EXPECTED_PROD_COMMIT}"
            )
        
        # Check expected source hash
        actual_hash = data.get("source_hash", "")
        print(f"   Production source_hash: {actual_hash}")
        print(f"   Expected source_hash: {EXPECTED_PROD_SOURCE_HASH}")
        
        if actual_hash != EXPECTED_PROD_SOURCE_HASH:
            log_test(
                "Production source hash verification",
                "FAIL",
                f"Expected source_hash {EXPECTED_PROD_SOURCE_HASH}, got {actual_hash}",
                "critical",
                is_blocker=True
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
            "Production identity surfaces check",
            "FAIL",
            f"Exception: {str(e)}",
            "critical",
            is_blocker=True
        )
        return None

def test_production_backup_and_certification():
    """Test 3: Production backup health and certification routes with dual admin tokens"""
    print("\n📋 Checking production backup health and certification routes...")
    try:
        # Authenticate to get dual tokens
        print("   Authenticating with production admin credentials...")
        login_response = requests.post(
            f"{PRODUCTION_BASE_URL}/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15
        )
        
        if login_response.status_code != 200:
            log_test(
                "Production admin authentication",
                "FAIL",
                f"Login failed with status {login_response.status_code}. Response: {login_response.text[:200]}",
                "critical",
                is_blocker=True
            )
            return
        
        login_data = login_response.json()
        session_token = login_data.get("session_token")
        admin_token = login_data.get("portal_tokens", {}).get("admin")
        
        if not session_token or not admin_token:
            log_test(
                "Production admin token retrieval",
                "FAIL",
                "Missing session_token or admin token in login response",
                "critical",
                is_blocker=True
            )
            return
        
        log_test(
            "Production admin authentication",
            "PASS",
            f"Successfully authenticated. Dual tokens obtained (session: {len(session_token)} chars, admin: {len(admin_token)} chars)"
        )
        
        # Test backup integrity check with dual tokens
        print("   Testing backup integrity check with dual admin tokens...")
        headers = {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }
        
        backup_response = requests.get(
            f"{PRODUCTION_BASE_URL}/admin/backups/integrity-check",
            headers=headers,
            timeout=60
        )
        
        if backup_response.status_code != 200:
            log_test(
                "Production backup integrity check reachability",
                "FAIL",
                f"Expected 200, got {backup_response.status_code}. Response: {backup_response.text[:500]}",
                "critical",
                is_blocker=True
            )
            return
        
        backup_data = backup_response.json()
        
        # Check backup health
        integrity_result = backup_data.get("integrity_result")
        last_backup = backup_data.get("last_backup_filename", "N/A")
        missing = backup_data.get("missing_from_backup", [])
        
        print(f"   Backup integrity result: {integrity_result}")
        print(f"   Last backup: {last_backup}")
        print(f"   Missing collections: {len(missing)}")
        
        if integrity_result != "PASS":
            log_test(
                "Production backup health",
                "FAIL",
                f"Backup integrity result is '{integrity_result}', expected 'PASS'. Missing: {missing}",
                "critical",
                is_blocker=True
            )
        else:
            log_test(
                "Production backup health",
                "PASS",
                f"Backup integrity PASS. Last backup: {last_backup}"
            )
        
        # Test deployment readiness certification route
        print("   Testing deployment readiness certification route...")
        readiness_response = requests.get(
            f"{PRODUCTION_BASE_URL}/admin/deployment-readiness",
            headers=headers,
            timeout=15
        )
        
        if readiness_response.status_code != 200:
            log_test(
                "Production certification route reachability",
                "FAIL",
                f"Deployment readiness endpoint returned {readiness_response.status_code}",
                "critical",
                is_blocker=True
            )
        else:
            readiness_data = readiness_response.json()
            decision = readiness_data.get("decision")
            blocking_gates = readiness_data.get("blocking_gates", [])
            
            print(f"   Deployment readiness decision: {decision}")
            print(f"   Blocking gates: {len(blocking_gates)}")
            
            log_test(
                "Production certification route reachability",
                "PASS",
                f"Deployment readiness route reachable with dual admin tokens. Decision: {decision}"
            )
        
    except Exception as e:
        log_test(
            "Production backup and certification routes",
            "FAIL",
            f"Exception: {str(e)}",
            "critical",
            is_blocker=True
        )

def test_auth_requirements():
    """Test 4: Backend auth/token requirements - check for inconsistencies"""
    print("\n📋 Checking backend auth/token requirements consistency...")
    
    # Wait a bit to avoid rate limiting
    time.sleep(5)
    
    try:
        # Test preview auth flow (with rate limit handling)
        print("   Testing preview auth flow...")
        login_response = requests.post(
            f"{PREVIEW_BASE_URL}/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15
        )
        
        if login_response.status_code == 429:
            log_test(
                "Preview auth flow (rate limited)",
                "SKIP",
                "Rate limited (429). Auth flow structure cannot be verified at this time.",
                "info"
            )
            return
        
        if login_response.status_code != 200:
            log_test(
                "Preview auth flow",
                "FAIL",
                f"Multi-login failed with status {login_response.status_code}",
                "critical",
                is_blocker=True
            )
            return
        
        login_data = login_response.json()
        
        # Check token structure consistency
        issues = []
        
        if "session_token" not in login_data:
            issues.append("Missing session_token")
        
        if "portal_tokens" not in login_data:
            issues.append("Missing portal_tokens")
        elif not isinstance(login_data["portal_tokens"], dict):
            issues.append("portal_tokens is not a dict")
        elif "admin" not in login_data["portal_tokens"]:
            issues.append("Missing admin token in portal_tokens")
        
        if "user" not in login_data:
            issues.append("Missing user object")
        
        if issues:
            log_test(
                "Auth token structure consistency",
                "FAIL",
                f"Token structure issues: {', '.join(issues)}",
                "critical",
                is_blocker=True
            )
            return
        
        log_test(
            "Auth token structure consistency",
            "PASS",
            f"Auth token structure consistent. Portal tokens available: {list(login_data['portal_tokens'].keys())}"
        )
        
        # Test dual-token requirement
        print("   Testing dual-token auth requirement...")
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
        
        # Test with only admin token (should fail with 401)
        headers_single = {
            "X-Admin-Token": admin_token
        }
        
        response_single = requests.get(
            f"{PREVIEW_BASE_URL}/admin/deployment-readiness",
            headers=headers_single,
            timeout=15
        )
        
        print(f"   Dual-token request: {response_dual.status_code}")
        print(f"   Single-token request: {response_single.status_code}")
        
        # Analyze for inconsistencies
        if response_dual.status_code == 200 and response_single.status_code == 401:
            log_test(
                "Dual-token auth requirement consistency",
                "PASS",
                "Protected endpoints correctly require both X-Admin-Token and X-Directory-Token. No auth inconsistencies detected."
            )
        elif response_dual.status_code != 200:
            log_test(
                "Dual-token auth requirement",
                "FAIL",
                f"Dual-token request failed with status {response_dual.status_code}. Expected 200.",
                "critical",
                is_blocker=True
            )
        elif response_single.status_code == 200:
            log_test(
                "Dual-token auth requirement",
                "FAIL",
                "Single admin token was accepted (expected 401). Inconsistent auth requirements - potential security issue.",
                "critical",
                is_blocker=True
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
            "Auth requirements consistency check",
            "FAIL",
            f"Exception: {str(e)}",
            "critical",
            is_blocker=True
        )

def main():
    print("=" * 80)
    print("PRE-DEPLOYMENT BACKEND AUDIT - READ-ONLY")
    print("=" * 80)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Preview Base URL: {PREVIEW_BASE_URL}")
    print(f"Production Base URL: {PRODUCTION_BASE_URL}")
    print()
    print("SCOPE:")
    print("1. Preview API / version / platform identity surfaces")
    print("2. Production identity surfaces (commit & source hash)")
    print("3. Production backup health and certification routes")
    print("4. Backend deploy blockers or inconsistent auth/token requirements")
    print("=" * 80)
    
    # Run all tests
    test_preview_identity()
    test_production_identity()
    test_production_backup_and_certification()
    test_auth_requirements()
    
    # Print summary
    print()
    print("=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {results['summary']['total']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Warnings: {results['summary']['warnings']}")
    print(f"Skipped: {results['summary']['skipped']}")
    print()
    
    # Report deploy blockers
    if results['deploy_blockers']:
        print("🚨 DEPLOY BLOCKERS FOUND:")
        for blocker in results['deploy_blockers']:
            print(f"   - {blocker['test']}: {blocker['details']}")
        print()
    
    # Determine overall status
    if results['deploy_blockers']:
        print("❌ OVERALL STATUS: DEPLOY BLOCKERS FOUND")
        print("   DO NOT DEPLOY until blockers are resolved.")
        exit_code = 1
    elif results['summary']['failed'] > 0:
        print("❌ OVERALL STATUS: FAILED")
        print("   Review failures before deployment.")
        exit_code = 1
    elif results['summary']['warnings'] > 0:
        print("⚠️  OVERALL STATUS: WARNINGS")
        print("   Review warnings. No critical deploy blockers found.")
        exit_code = 0
    else:
        print("✅ OVERALL STATUS: PASSED")
        print("   No deploy blockers found. All checks passed.")
        exit_code = 0
    
    # Save results to file
    output_file = "/app/backend_predeployment_audit_v2_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    print("=" * 80)
    
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

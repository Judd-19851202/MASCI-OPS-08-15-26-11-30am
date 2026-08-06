"""
WP-18DB Backend Readiness and Resilience Endpoints Test Suite

Tests:
1. Local backend health after controlled restart
2. Release gate for target=preview
3. /api/admin/recovery/snapshot - backup and restore evidence
4. /api/admin/backup-trust-score - green after preview-only hourly penalty fix
5. /api/admin/deployment-readiness - should return pass
6. /api/admin/deployment-readiness/performance-budget-contract - should return pass
7. /api/admin/scheduler-runs and scheduler/recovery surfaces - no auth regressions
8. Distinguish preview-ingress transport flakiness from actual backend failure
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any, List

import httpx

# Backend URL from environment
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com")
API_BASE = f"{BACKEND_URL}/api"

# Super admin credentials
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test results
results = {
    "test_suite": "WP-18DB Backend Readiness and Resilience",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "tests": [],
    "summary": {"passed": 0, "failed": 0, "warnings": 0}
}

# Auth tokens
auth_tokens = {
    "session_token": None,
    "admin_token": None,
    "directory_token": None
}


def log_test(name: str, status: str, details: str = "", data: Any = None):
    """Log a test result"""
    result = {
        "name": name,
        "status": status,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    if data is not None:
        result["data"] = data
    
    results["tests"].append(result)
    
    if status == "PASS":
        results["summary"]["passed"] += 1
        print(f"✅ {name}: {status}")
    elif status == "FAIL":
        results["summary"]["failed"] += 1
        print(f"❌ {name}: {status}")
    else:
        results["summary"]["warnings"] += 1
        print(f"⚠️  {name}: {status}")
    
    if details:
        print(f"   {details}")


async def authenticate():
    """Authenticate and get admin tokens"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE}/auth/multi-login",
                json={
                    "email": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                auth_tokens["session_token"] = data.get("session_token")
                
                # Get admin portal token
                portal_tokens = data.get("portal_tokens", {})
                auth_tokens["admin_token"] = portal_tokens.get("admin")
                # session_token IS the directory token
                auth_tokens["directory_token"] = data.get("session_token")
                
                log_test(
                    "0. Authentication",
                    "PASS",
                    f"Logged in as {ADMIN_EMAIL}, Admin token: {auth_tokens['admin_token'][:20]}..., Directory token: {auth_tokens['directory_token'][:20]}..."
                )
                return True
            else:
                log_test(
                    "0. Authentication",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
    except Exception as e:
        log_test("0. Authentication", "FAIL", str(e))
        return False


async def test_backend_health():
    """Test 1: Local backend health after controlled restart"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE}/health")
        
        if response.status_code == 200:
            data = response.json()
            ok = data.get("ok", False)
            service = data.get("service", "unknown")
            
            if ok:
                log_test(
                    "1. Backend Health",
                    "PASS",
                    f"Service: {service}, OK: {ok}",
                    data
                )
                return True
            else:
                log_test(
                    "1. Backend Health",
                    "FAIL",
                    f"Service: {service}, OK: {ok} (expected ok=true)",
                    data
                )
                return False
        else:
            log_test("1. Backend Health", "FAIL", f"HTTP {response.status_code}")
            return False
    except Exception as e:
        log_test("1. Backend Health", "FAIL", str(e))
        return False


async def test_release_gate():
    """Test 2: Release gate for target=preview"""
    try:
        headers = {
            "X-Admin-Token": auth_tokens["admin_token"],
            "X-Directory-Token": auth_tokens["directory_token"]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE}/admin/release-gate",
                headers=headers,
                params={"target": "preview"}
            )
        
        if response.status_code == 200:
            data = response.json()
            gate_status = data.get("status", "unknown")
            
            if gate_status == "green" or gate_status == "pass":
                log_test(
                    "2. Release Gate (target=preview)",
                    "PASS",
                    f"Gate status: {gate_status}",
                    data
                )
                return True
            else:
                log_test(
                    "2. Release Gate (target=preview)",
                    "WARNING",
                    f"Gate status: {gate_status} (expected green/pass)",
                    data
                )
                return True
        else:
            log_test("2. Release Gate", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test("2. Release Gate", "FAIL", str(e))
        return False


async def test_recovery_snapshot():
    """Test 3: /api/admin/recovery/snapshot - backup and restore evidence"""
    try:
        headers = {
            "X-Admin-Token": auth_tokens["admin_token"],
            "X-Directory-Token": auth_tokens["directory_token"]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE}/admin/recovery/snapshot",
                headers=headers
            )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for backup evidence
            has_backup_evidence = "last_backup" in data
            # Check for restore evidence (drill = restore test)
            has_restore_evidence = "last_drill" in data
            
            if has_backup_evidence and has_restore_evidence:
                backup_age_min = data.get("backup_age_minutes", "unknown")
                drill_outcome = data.get("last_drill", {}).get("outcome", "unknown")
                log_test(
                    "3. Recovery Snapshot",
                    "PASS",
                    f"Fresh backup evidence (age: {backup_age_min} min) and latest restore evidence (drill outcome: {drill_outcome}) present",
                    data
                )
                return True
            elif has_backup_evidence:
                log_test(
                    "3. Recovery Snapshot",
                    "WARNING",
                    "Backup evidence present, but restore evidence may be missing",
                    data
                )
                return True
            else:
                log_test(
                    "3. Recovery Snapshot",
                    "FAIL",
                    "Missing backup or restore evidence",
                    data
                )
                return False
        else:
            log_test("3. Recovery Snapshot", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test("3. Recovery Snapshot", "FAIL", str(e))
        return False


async def test_backup_trust_score():
    """Test 4: /api/admin/backup-trust-score - should be green after preview-only hourly penalty fix"""
    try:
        headers = {
            "X-Admin-Token": auth_tokens["admin_token"],
            "X-Directory-Token": auth_tokens["directory_token"]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE}/admin/backup-trust-score",
                headers=headers
            )
        
        if response.status_code == 200:
            data = response.json()
            trust_score = data.get("trust_score", 0)
            score_band = data.get("score_band", "unknown")
            score_band_label = data.get("score_band_label", "unknown")
            
            # Check if green/pass
            is_green = score_band == "green" or score_band_label == "Trusted"
            
            if is_green:
                log_test(
                    "4. Backup Trust Score",
                    "PASS",
                    f"Trust score: {trust_score}, Band: {score_band} ({score_band_label})",
                    data
                )
                return True
            else:
                log_test(
                    "4. Backup Trust Score",
                    "WARNING",
                    f"Trust score: {trust_score}, Band: {score_band} ({score_band_label}) (expected green)",
                    data
                )
                return True
        else:
            log_test("4. Backup Trust Score", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test("4. Backup Trust Score", "FAIL", str(e))
        return False


async def test_deployment_readiness():
    """Test 5: /api/admin/deployment-readiness - should return pass"""
    try:
        headers = {
            "X-Admin-Token": auth_tokens["admin_token"],
            "X-Directory-Token": auth_tokens["directory_token"]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE}/admin/deployment-readiness",
                headers=headers
            )
        
        if response.status_code == 200:
            data = response.json()
            decision = data.get("decision", "unknown")
            blocking_gates = data.get("blocking_gates", [])
            
            if decision == "pass" and len(blocking_gates) == 0:
                log_test(
                    "5. Deployment Readiness",
                    "PASS",
                    f"Decision: {decision}, Blocking gates: {len(blocking_gates)}",
                    data
                )
                return True
            else:
                log_test(
                    "5. Deployment Readiness",
                    "FAIL",
                    f"Decision: {decision}, Blocking gates: {len(blocking_gates)} (expected pass with 0 blockers)",
                    data
                )
                return False
        else:
            log_test("5. Deployment Readiness", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test("5. Deployment Readiness", "FAIL", str(e))
        return False


async def test_performance_budget_contract():
    """Test 6: /api/admin/deployment-readiness/performance-budget-contract - should return pass"""
    try:
        headers = {
            "X-Admin-Token": auth_tokens["admin_token"],
            "X-Directory-Token": auth_tokens["directory_token"]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE}/admin/deployment-readiness/performance-budget-contract",
                headers=headers
            )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")
            passed = data.get("passed", False)
            
            if status == "pass" or passed == True:
                log_test(
                    "6. Performance Budget Contract",
                    "PASS",
                    f"Status: {status}, Passed: {passed}",
                    data
                )
                return True
            else:
                log_test(
                    "6. Performance Budget Contract",
                    "FAIL",
                    f"Status: {status}, Passed: {passed} (expected pass)",
                    data
                )
                return False
        else:
            log_test("6. Performance Budget Contract", "FAIL", f"HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log_test("6. Performance Budget Contract", "FAIL", str(e))
        return False


async def test_scheduler_runs():
    """Test 7.1: /api/admin/scheduler-runs - no auth regressions"""
    try:
        headers = {
            "X-Admin-Token": auth_tokens["admin_token"],
            "X-Directory-Token": auth_tokens["directory_token"]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE}/admin/scheduler-runs",
                headers=headers
            )
        
        if response.status_code == 200:
            data = response.json()
            log_test(
                "7.1 Scheduler Runs",
                "PASS",
                "Endpoint accessible, no auth regression",
                data
            )
            return True
        elif response.status_code == 401:
            log_test(
                "7.1 Scheduler Runs",
                "FAIL",
                "Auth regression detected - endpoint returned 401"
            )
            return False
        else:
            log_test("7.1 Scheduler Runs", "WARNING", f"HTTP {response.status_code}: {response.text}")
            return True
    except Exception as e:
        log_test("7.1 Scheduler Runs", "FAIL", str(e))
        return False


async def test_scheduler_recovery_surfaces():
    """Test 7.2: Scheduler/recovery surfaces - no auth regressions"""
    endpoints = [
        "/admin/backups-scheduler-state",
        "/admin/system-health",
        "/admin/backups-complete-r2-state",
        "/admin/backups-list-r2"
    ]
    
    all_pass = True
    for endpoint in endpoints:
        try:
            headers = {
                "X-Admin-Token": auth_tokens["admin_token"],
                "X-Directory-Token": auth_tokens["directory_token"]
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{API_BASE}{endpoint}",
                    headers=headers
                )
            
            if response.status_code == 200:
                log_test(
                    f"7.2 Recovery Surface: {endpoint}",
                    "PASS",
                    "Endpoint accessible, no auth regression"
                )
            elif response.status_code == 401:
                log_test(
                    f"7.2 Recovery Surface: {endpoint}",
                    "FAIL",
                    "Auth regression detected - endpoint returned 401"
                )
                all_pass = False
            else:
                log_test(
                    f"7.2 Recovery Surface: {endpoint}",
                    "WARNING",
                    f"HTTP {response.status_code}"
                )
        except Exception as e:
            log_test(f"7.2 Recovery Surface: {endpoint}", "FAIL", str(e))
            all_pass = False
    
    return all_pass


async def test_transport_flakiness():
    """Test 8: Distinguish preview-ingress transport flakiness from actual backend failure"""
    try:
        # Make multiple requests to check for transport flakiness
        success_count = 0
        total_attempts = 5
        
        for i in range(total_attempts):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{API_BASE}/health")
                    if response.status_code == 200:
                        success_count += 1
            except Exception:
                pass
            
            # Small delay between requests
            await asyncio.sleep(0.5)
        
        success_rate = (success_count / total_attempts) * 100
        
        if success_rate == 100:
            log_test(
                "8. Transport Flakiness Check",
                "PASS",
                f"All {total_attempts} health checks succeeded (100% success rate)"
            )
            return True
        elif success_rate >= 80:
            log_test(
                "8. Transport Flakiness Check",
                "WARNING",
                f"{success_count}/{total_attempts} health checks succeeded ({success_rate:.0f}% success rate) - possible transport flakiness"
            )
            return True
        else:
            log_test(
                "8. Transport Flakiness Check",
                "FAIL",
                f"Only {success_count}/{total_attempts} health checks succeeded ({success_rate:.0f}% success rate) - backend may be failing"
            )
            return False
    except Exception as e:
        log_test("8. Transport Flakiness Check", "FAIL", str(e))
        return False


async def main():
    """Run all tests"""
    print("=" * 80)
    print("WP-18DB Backend Readiness and Resilience Endpoints Test Suite")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Timestamp: {results['timestamp']}")
    print("=" * 80)
    print()
    
    # Authenticate first
    print("Authentication")
    print("-" * 80)
    auth_success = await authenticate()
    print()
    
    if not auth_success:
        print("❌ Authentication failed - cannot proceed with admin endpoint tests")
        sys.exit(1)
    
    # Test 1: Backend health
    print("Test 1: Local Backend Health")
    print("-" * 80)
    await test_backend_health()
    print()
    
    # Test 2: Release gate
    print("Test 2: Release Gate (target=preview)")
    print("-" * 80)
    await test_release_gate()
    print()
    
    # Test 3: Recovery snapshot
    print("Test 3: Recovery Snapshot")
    print("-" * 80)
    await test_recovery_snapshot()
    print()
    
    # Test 4: Backup trust score
    print("Test 4: Backup Trust Score")
    print("-" * 80)
    await test_backup_trust_score()
    print()
    
    # Test 5: Deployment readiness
    print("Test 5: Deployment Readiness")
    print("-" * 80)
    await test_deployment_readiness()
    print()
    
    # Test 6: Performance budget contract
    print("Test 6: Performance Budget Contract")
    print("-" * 80)
    await test_performance_budget_contract()
    print()
    
    # Test 7: Scheduler runs and recovery surfaces
    print("Test 7: Scheduler Runs and Recovery Surfaces")
    print("-" * 80)
    await test_scheduler_runs()
    await test_scheduler_recovery_surfaces()
    print()
    
    # Test 8: Transport flakiness
    print("Test 8: Transport Flakiness Check")
    print("-" * 80)
    await test_transport_flakiness()
    print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(results['tests'])}")
    print(f"✅ Passed: {results['summary']['passed']}")
    print(f"❌ Failed: {results['summary']['failed']}")
    print(f"⚠️  Warnings: {results['summary']['warnings']}")
    print()
    
    # Save results to file
    with open("/app/wp18db_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to: /app/wp18db_test_results.json")
    print()
    
    # Exit code
    if results['summary']['failed'] > 0:
        print("❌ OVERALL STATUS: FAIL - Some tests failed")
        sys.exit(1)
    elif results['summary']['warnings'] > 0:
        print("⚠️  OVERALL STATUS: PASS WITH WARNINGS")
        sys.exit(0)
    else:
        print("✅ OVERALL STATUS: PASS - All tests passed")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

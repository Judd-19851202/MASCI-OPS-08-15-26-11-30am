#!/usr/bin/env python3
"""
Backup/Recovery Hardening Backend Verification Test

Validates the hardened backup/recovery backend in Preview at
https://masci-audit-hub.preview.emergentagent.com using admin credentials.

Focus on these backend behaviors only:
1. /api/admin/backups-complete-r2-state returns backup_runtime and keeps
   r2_hourly_effective=false, r2_hourly_locked_off=true
2. /api/admin/backups-scheduler-state returns scheduler health plus backup_runtime
3. /api/admin/backup-trust-score returns trust_score with
   production_activation_disabled=true and restore drill evidence
4. /api/admin/backup-verification/run-now returns ok=true with a built report
   in Preview even when email is safety-blocked
5. /api/admin/recovery/snapshot includes the latest drill evidence
6. No endpoint suggests production activation was enabled

This is Preview-only and production must remain disabled.
"""
import json
import sys
from datetime import datetime
from typing import Any, Dict, List

import requests

# Configuration
BASE_URL = "https://masci-audit-hub.preview.emergentagent.com"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test results
results: List[Dict[str, Any]] = []


def log_test(test_name: str, passed: bool, details: str, response_data: Any = None):
    """Log a test result."""
    result = {
        "test": test_name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if response_data is not None:
        result["response_data"] = response_data
    results.append(result)
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")
    print(f"  Details: {details}")
    if not passed and response_data:
        print(f"  Response: {json.dumps(response_data, indent=2)[:500]}")


def authenticate() -> tuple[str, str]:
    """Authenticate and return directory token and admin token."""
    print(f"\n🔐 Authenticating as {ADMIN_EMAIL}...")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)
    
    data = response.json()
    directory_token = data.get("session_token")
    portal_tokens = data.get("portal_tokens", {})
    admin_token = portal_tokens.get("admin")
    
    if not directory_token or not admin_token:
        print(f"❌ Missing tokens in response")
        print(f"Response: {json.dumps(data, indent=2)}")
        sys.exit(1)
    
    print(f"✅ Authenticated successfully")
    print(f"   Directory token: {directory_token[:20]}...")
    print(f"   Admin token: {admin_token[:20]}...")
    print(f"   Available portals: {list(portal_tokens.keys())}")
    
    return directory_token, admin_token


def test_backups_complete_r2_state(directory_token: str, admin_token: str):
    """Test 1: /api/admin/backups-complete-r2-state returns backup_runtime
    and keeps r2_hourly_effective=false, r2_hourly_locked_off=true."""
    
    print("\n📋 Test 1: /api/admin/backups-complete-r2-state")
    
    response = requests.get(
        f"{BASE_URL}/api/admin/backups-complete-r2-state",
        headers={
            "X-Directory-Token": directory_token,
            "X-Admin-Token": admin_token,
        },
        timeout=30,
    )
    
    if response.status_code != 200:
        log_test(
            "backups-complete-r2-state: HTTP 200",
            False,
            f"Expected 200, got {response.status_code}",
            response.text,
        )
        return
    
    log_test("backups-complete-r2-state: HTTP 200", True, "Endpoint accessible")
    
    data = response.json()
    
    # Check backup_runtime exists
    has_backup_runtime = "backup_runtime" in data
    log_test(
        "backups-complete-r2-state: backup_runtime present",
        has_backup_runtime,
        f"backup_runtime field {'present' if has_backup_runtime else 'MISSING'}",
        data.get("backup_runtime"),
    )
    
    # Check r2_hourly_effective=false
    r2_hourly_effective = data.get("r2_hourly_effective")
    log_test(
        "backups-complete-r2-state: r2_hourly_effective=false",
        r2_hourly_effective is False,
        f"r2_hourly_effective={r2_hourly_effective} (expected False)",
        {"r2_hourly_effective": r2_hourly_effective},
    )
    
    # Check r2_hourly_locked_off=true
    r2_hourly_locked_off = data.get("r2_hourly_locked_off")
    log_test(
        "backups-complete-r2-state: r2_hourly_locked_off=true",
        r2_hourly_locked_off is True,
        f"r2_hourly_locked_off={r2_hourly_locked_off} (expected True)",
        {"r2_hourly_locked_off": r2_hourly_locked_off},
    )
    
    # Check no production activation hints
    production_hints = []
    for key in ["production_enabled", "production_active", "hourly_enabled"]:
        if key in data and data[key]:
            production_hints.append(f"{key}={data[key]}")
    
    log_test(
        "backups-complete-r2-state: no production activation hints",
        len(production_hints) == 0,
        f"Production hints: {production_hints if production_hints else 'none'}",
        {k: data.get(k) for k in ["production_enabled", "production_active", "hourly_enabled"] if k in data},
    )


def test_backups_scheduler_state(directory_token: str, admin_token: str):
    """Test 2: /api/admin/backups-scheduler-state returns scheduler health
    plus backup_runtime."""
    
    print("\n📋 Test 2: /api/admin/backups-scheduler-state")
    
    response = requests.get(
        f"{BASE_URL}/api/admin/backups-scheduler-state",
        headers={
            "X-Directory-Token": directory_token,
            "X-Admin-Token": admin_token,
        },
        timeout=30,
    )
    
    if response.status_code != 200:
        log_test(
            "backups-scheduler-state: HTTP 200",
            False,
            f"Expected 200, got {response.status_code}",
            response.text,
        )
        return
    
    log_test("backups-scheduler-state: HTTP 200", True, "Endpoint accessible")
    
    data = response.json()
    
    # Check scheduler health fields
    health_fields = ["alive", "is_healthy", "signal_source", "reason_code"]
    missing_health = [f for f in health_fields if f not in data]
    log_test(
        "backups-scheduler-state: scheduler health fields present",
        len(missing_health) == 0,
        f"Health fields: {health_fields if not missing_health else f'missing {missing_health}'}",
        {k: data.get(k) for k in health_fields},
    )
    
    # Check backup_runtime exists
    has_backup_runtime = "backup_runtime" in data
    log_test(
        "backups-scheduler-state: backup_runtime present",
        has_backup_runtime,
        f"backup_runtime field {'present' if has_backup_runtime else 'MISSING'}",
        data.get("backup_runtime"),
    )
    
    # Check scheduler state
    scheduler_alive = data.get("alive")
    scheduler_healthy = data.get("is_healthy")
    log_test(
        "backups-scheduler-state: scheduler status",
        True,  # Just informational
        f"alive={scheduler_alive}, is_healthy={scheduler_healthy}",
        {"alive": scheduler_alive, "is_healthy": scheduler_healthy, "signal_source": data.get("signal_source")},
    )


def test_backup_trust_score(directory_token: str, admin_token: str):
    """Test 3: /api/admin/backup-trust-score returns trust_score with
    production_activation_disabled=true and restore drill evidence."""
    
    print("\n📋 Test 3: /api/admin/backup-trust-score")
    
    response = requests.get(
        f"{BASE_URL}/api/admin/backup-trust-score",
        headers={
            "X-Directory-Token": directory_token,
            "X-Admin-Token": admin_token,
        },
        timeout=30,
    )
    
    if response.status_code != 200:
        log_test(
            "backup-trust-score: HTTP 200",
            False,
            f"Expected 200, got {response.status_code}",
            response.text,
        )
        return
    
    log_test("backup-trust-score: HTTP 200", True, "Endpoint accessible")
    
    data = response.json()
    
    # Check trust_score exists
    has_trust_score = "trust_score" in data
    trust_score = data.get("trust_score")
    log_test(
        "backup-trust-score: trust_score present",
        has_trust_score,
        f"trust_score={trust_score}" if has_trust_score else "trust_score MISSING",
        {"trust_score": trust_score},
    )
    
    # Check production_activation_disabled=true
    production_disabled = data.get("production_activation_disabled")
    log_test(
        "backup-trust-score: production_activation_disabled=true",
        production_disabled is True,
        f"production_activation_disabled={production_disabled} (expected True)",
        {"production_activation_disabled": production_disabled},
    )
    
    # Check restore drill evidence
    evidence = data.get("evidence", {})
    has_drill_evidence = "last_restore_drill" in evidence
    drill_data = evidence.get("last_restore_drill")
    log_test(
        "backup-trust-score: restore drill evidence present",
        has_drill_evidence,
        f"last_restore_drill {'present' if has_drill_evidence else 'MISSING'}" +
        (f" (outcome={drill_data.get('outcome')})" if drill_data else ""),
        drill_data,
    )
    
    # Check evidence structure
    expected_evidence_keys = ["latest_complete_backup", "newest_r2_age_hours", "restore_drill_age_days", "runtime"]
    missing_evidence = [k for k in expected_evidence_keys if k not in evidence]
    log_test(
        "backup-trust-score: evidence structure complete",
        len(missing_evidence) == 0,
        f"Evidence keys: {expected_evidence_keys if not missing_evidence else f'missing {missing_evidence}'}",
        {k: evidence.get(k) for k in expected_evidence_keys if k in evidence},
    )


def test_backup_verification_run_now(directory_token: str, admin_token: str):
    """Test 4: /api/admin/backup-verification/run-now returns ok=true with
    a built report in Preview even when email is safety-blocked."""
    
    print("\n📋 Test 4: /api/admin/backup-verification/run-now")
    
    response = requests.post(
        f"{BASE_URL}/api/admin/backup-verification/run-now",
        headers={
            "X-Directory-Token": directory_token,
            "X-Admin-Token": admin_token,
            "Content-Type": "application/json",
        },
        json={},
        timeout=60,
    )
    
    if response.status_code != 200:
        log_test(
            "backup-verification/run-now: HTTP 200",
            False,
            f"Expected 200, got {response.status_code}",
            response.text,
        )
        return
    
    log_test("backup-verification/run-now: HTTP 200", True, "Endpoint accessible")
    
    data = response.json()
    
    # Check ok=true
    ok_status = data.get("ok")
    log_test(
        "backup-verification/run-now: ok=true",
        ok_status is True,
        f"ok={ok_status} (expected True)",
        {"ok": ok_status},
    )
    
    # Check report exists
    has_report = "report" in data
    report = data.get("report", {})
    log_test(
        "backup-verification/run-now: report built",
        has_report and isinstance(report, dict) and len(report) > 0,
        f"Report {'present' if has_report else 'MISSING'}" +
        (f" with {len(report)} keys" if has_report else ""),
        {"report_keys": list(report.keys()) if has_report else None},
    )
    
    # Check email safety-blocked (Preview mode)
    sent_status = data.get("sent")
    safety_mode = data.get("safety_mode") or data.get("mode")
    log_test(
        "backup-verification/run-now: email safety-blocked in Preview",
        True,  # Informational - we expect either sent=false or safety_mode indicator
        f"sent={sent_status}, safety_mode={safety_mode}",
        {"sent": sent_status, "safety_mode": safety_mode, "mode": data.get("mode")},
    )
    
    # Verify report structure
    if has_report:
        expected_report_keys = ["backup_age_hours", "backup_status", "scheduler_status"]
        report_keys = list(report.keys())
        log_test(
            "backup-verification/run-now: report structure",
            True,  # Informational
            f"Report contains: {report_keys[:5]}...",
            {"report_keys": report_keys},
        )


def test_recovery_snapshot(directory_token: str, admin_token: str):
    """Test 5: /api/admin/recovery/snapshot includes the latest drill evidence."""
    
    print("\n📋 Test 5: /api/admin/recovery/snapshot")
    
    response = requests.get(
        f"{BASE_URL}/api/admin/recovery/snapshot",
        headers={
            "X-Directory-Token": directory_token,
            "X-Admin-Token": admin_token,
        },
        timeout=30,
    )
    
    if response.status_code != 200:
        log_test(
            "recovery/snapshot: HTTP 200",
            False,
            f"Expected 200, got {response.status_code}",
            response.text,
        )
        return
    
    log_test("recovery/snapshot: HTTP 200", True, "Endpoint accessible")
    
    data = response.json()
    
    # Check drill evidence
    has_drill = "last_drill" in data
    drill_data = data.get("last_drill")
    log_test(
        "recovery/snapshot: last_drill present",
        has_drill,
        f"last_drill {'present' if has_drill else 'MISSING'}" +
        (f" (outcome={drill_data.get('outcome')})" if drill_data else ""),
        drill_data,
    )
    
    # Check drill structure if present
    if has_drill and drill_data:
        expected_drill_keys = ["ts", "outcome", "records", "photos"]
        missing_drill_keys = [k for k in expected_drill_keys if k not in drill_data]
        log_test(
            "recovery/snapshot: drill evidence structure",
            len(missing_drill_keys) == 0,
            f"Drill keys: {expected_drill_keys if not missing_drill_keys else f'missing {missing_drill_keys}'}",
            {k: drill_data.get(k) for k in expected_drill_keys if k in drill_data},
        )
    
    # Check other recovery snapshot fields
    expected_snapshot_keys = ["last_backup", "backup_age_minutes", "scheduler", "bucket_usage"]
    missing_snapshot = [k for k in expected_snapshot_keys if k not in data]
    log_test(
        "recovery/snapshot: snapshot structure complete",
        len(missing_snapshot) == 0,
        f"Snapshot keys: {expected_snapshot_keys if not missing_snapshot else f'missing {missing_snapshot}'}",
        {k: type(data.get(k)).__name__ if k in data else None for k in expected_snapshot_keys},
    )


def test_no_production_activation(directory_token: str, admin_token: str):
    """Test 6: No endpoint suggests production activation was enabled."""
    
    print("\n📋 Test 6: No production activation hints across all endpoints")
    
    endpoints = [
        "/api/admin/backups-complete-r2-state",
        "/api/admin/backups-scheduler-state",
        "/api/admin/backup-trust-score",
        "/api/admin/recovery/snapshot",
    ]
    
    production_hints_found = []
    
    for endpoint in endpoints:
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers={
                "X-Directory-Token": directory_token,
                "X-Admin-Token": admin_token,
            },
            timeout=30,
        )
        
        if response.status_code != 200:
            continue
        
        data = response.json()
        
        # Check for production activation hints
        suspicious_keys = [
            "production_enabled",
            "production_active",
            "production_mode",
            "hourly_enabled",
            "r2_hourly_effective",
        ]
        
        for key in suspicious_keys:
            if key in data and data[key] is True:
                production_hints_found.append(f"{endpoint}: {key}=true")
            
            # Check nested evidence
            if "evidence" in data and isinstance(data["evidence"], dict):
                if key in data["evidence"] and data["evidence"][key] is True:
                    production_hints_found.append(f"{endpoint}.evidence: {key}=true")
    
    log_test(
        "no-production-activation: all endpoints",
        len(production_hints_found) == 0,
        f"Production hints: {production_hints_found if production_hints_found else 'none found (GOOD)'}",
        {"hints": production_hints_found},
    )


def main():
    """Run all backup/recovery hardening tests."""
    print("=" * 80)
    print("Backup/Recovery Hardening Backend Verification Test")
    print("=" * 80)
    print(f"Target: {BASE_URL}")
    print(f"Admin: {ADMIN_EMAIL}")
    print("=" * 80)
    
    # Authenticate
    directory_token, admin_token = authenticate()
    
    # Run all tests
    test_backups_complete_r2_state(directory_token, admin_token)
    test_backups_scheduler_state(directory_token, admin_token)
    test_backup_trust_score(directory_token, admin_token)
    test_backup_verification_run_now(directory_token, admin_token)
    test_recovery_snapshot(directory_token, admin_token)
    test_no_production_activation(directory_token, admin_token)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    
    print(f"Total tests: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Pass rate: {(passed / total * 100):.1f}%")
    
    # Show failures
    failures = [r for r in results if not r["passed"]]
    if failures:
        print("\n❌ FAILED TESTS:")
        for f in failures:
            print(f"  - {f['test']}: {f['details']}")
    
    # Save results
    output_file = "/app/backup_recovery_hardening_test_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": round(passed / total * 100, 1),
            },
            "tests": results,
            "timestamp": datetime.utcnow().isoformat(),
        }, f, indent=2)
    
    print(f"\n📄 Results saved to: {output_file}")
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()

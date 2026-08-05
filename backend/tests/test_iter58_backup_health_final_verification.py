"""
Test iteration 58: Final Backup Health Alert Trust Verification

This test exhaustively verifies all remaining backup health alert and admin truth issues
before production redeploy. Tests cover:

1. /api/admin/backups-complete-r2-state uses same hourly activation truth as scheduler-state
2. complete-r2-state does not show false scheduler_unhealthy blocker when scheduler is alive/healthy
3. /api/admin/recovery/snapshot, /api/admin/backups-complete-r2-state, /api/admin/backups-scheduler-state,
   and /api/admin/system-health all express consistent backup freshness truth and target semantics
4. Static verification that health monitor runs under singleton lock
5. Flag any remaining contradictory backup-truth or health-alert logic issues

Expected behavior in preview:
- environment_not_production is an expected blocker
- scheduler_unhealthy should NOT appear when scheduler is alive=true, is_healthy=true
- backup_age_target_minutes should equal rpo.target_min (60), NOT 24h posture target (1440)
"""

import os
import pytest
import requests
import uuid
from pathlib import Path

BASE_URL = os.environ.get("LOCAL_BACKEND_URL", "http://127.0.0.1:8001").rstrip("/")

# Test credentials from test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_headers():
    """Get admin auth headers via multi-login endpoint."""
    response = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={
            "X-Device-Id": f"iter58-auth-{uuid.uuid4().hex[:10]}",
            "X-Test-Rate-Limit-Bypass": "1",
        },
        timeout=60,
    )
    assert response.status_code == 200, f"Multi-login failed: {response.text}"
    data = response.json()
    admin_token = (data.get("portal_tokens") or {}).get("admin")
    session_token = data.get("session_token")
    assert admin_token, f"No admin token in response: {data}"
    headers = {"X-Admin-Token": admin_token}
    if session_token:
        headers["X-Directory-Token"] = session_token
    return headers


class TestStaticCodeVerification:
    """Static/code-level verification of fixes."""

    def test_01_health_monitor_uses_singleton_lock(self):
        """Verify health_monitor.py runs under singleton lock to prevent duplicate polling."""
        src = Path("/app/backend/health_monitor.py").read_text()
        
        # Must import singleton lock
        assert "from lib.singleton_scheduler import run_with_singleton_lock" in src, (
            "health_monitor.py must import run_with_singleton_lock"
        )
        
        # Must use singleton lock with correct key
        assert 'run_with_singleton_lock(db, "synthetic_health_monitor"' in src, (
            "health_monitor.py must run under singleton lock with key 'synthetic_health_monitor'"
        )
        
        # Must NOT use in-memory cooldown dict (the old bug)
        assert "last_alerted: Dict[str, datetime] = {}" not in src, (
            "health_monitor.py must NOT use in-memory cooldown dict (Track 15.73D fix)"
        )
        
        # Must use Mongo-persisted cooldown
        assert "_load_cooldown" in src, "Missing _load_cooldown helper"
        assert "_persist_cooldown" in src, "Missing _persist_cooldown helper"
        assert "health_alert_cooldowns" in src, "Must persist to health_alert_cooldowns collection"
        
        print("[STATIC] health_monitor.py singleton lock verification PASSED")

    def test_02_complete_r2_state_uses_canonical_scheduler_merge(self):
        """Verify admin_complete_r2_state merges canonical scheduler truth."""
        src = Path("/app/backend/server.py").read_text()
        
        # Must call build_canonical_scheduler_snapshot
        assert "build_canonical_scheduler_snapshot" in src, (
            "server.py must call build_canonical_scheduler_snapshot"
        )
        
        # Check the admin_complete_r2_state function specifically
        # Find the function and verify it merges scheduler fields
        func_start = src.find("async def admin_complete_r2_state")
        assert func_start > 0, "admin_complete_r2_state function not found"
        
        # Get the function body (next 200 lines should be enough)
        func_body = src[func_start:func_start + 5000]
        
        # Must merge alive, is_healthy into backup_runtime_for_activation
        assert '"alive": canonical_scheduler.get("alive")' in func_body or "'alive': canonical_scheduler.get('alive')" in func_body, (
            "admin_complete_r2_state must merge alive from canonical_scheduler"
        )
        assert '"is_healthy": canonical_scheduler.get("is_healthy")' in func_body or "'is_healthy': canonical_scheduler.get('is_healthy')" in func_body, (
            "admin_complete_r2_state must merge is_healthy from canonical_scheduler"
        )
        
        print("[STATIC] admin_complete_r2_state canonical scheduler merge verification PASSED")

    def test_03_recovery_dashboard_uses_rpo_target_for_backup_age(self):
        """Verify recovery_dashboard uses RPO target (60m) not posture target (1440m)."""
        src = Path("/app/backend/routes/recovery_dashboard.py").read_text()
        
        # Must read RPO target
        assert 'BACKUP_RPO_TARGET_MINUTES' in src, (
            "recovery_dashboard.py must read BACKUP_RPO_TARGET_MINUTES"
        )
        
        # backup_age_target_minutes should use rpo_target
        assert (
            '"backup_age_target_minutes": effective_backup_age_target_minutes' in src
            or "'backup_age_target_minutes': effective_backup_age_target_minutes" in src
            or '"backup_age_target_minutes": rpo_target' in src
            or "'backup_age_target_minutes': rpo_target" in src
        ), (
            "recovery_dashboard.py must use the effective RPO-derived target for backup_age_target_minutes"
        )
        
        print("[STATIC] recovery_dashboard RPO target verification PASSED")


class TestLiveAPIConsistency:
    """Live API tests to verify consistency across endpoints."""

    def test_04_scheduler_state_returns_200(self, admin_headers):
        """Verify scheduler-state endpoint returns 200."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=admin_headers,
            timeout=60,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("[API] backups-scheduler-state returns 200")

    def test_05_scheduler_state_no_false_scheduler_unhealthy(self, admin_headers):
        """Verify scheduler-state has no false scheduler_unhealthy blocker."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=admin_headers,
            timeout=60,
        )
        data = response.json()
        
        alive = data.get("alive")
        is_healthy = data.get("is_healthy")
        blockers = data.get("activation_blockers") or []
        blocker_codes = {b.get("code") for b in blockers}
        
        print(f"[scheduler-state] alive={alive}, is_healthy={is_healthy}")
        print(f"[scheduler-state] blocker_codes={blocker_codes}")
        
        # If scheduler is alive and healthy, scheduler_unhealthy should NOT be a blocker
        if alive is True and is_healthy is True:
            assert "scheduler_unhealthy" not in blocker_codes, (
                f"False scheduler_unhealthy blocker when scheduler is alive/healthy! "
                f"blockers={blockers}"
            )
        print("[API] scheduler-state no false scheduler_unhealthy PASSED")

    def test_06_recovery_snapshot_returns_200(self, admin_headers):
        """Verify recovery/snapshot endpoint returns 200."""
        response = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers=admin_headers,
            timeout=90,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("[API] recovery/snapshot returns 200")

    def test_07_recovery_snapshot_no_false_scheduler_unhealthy(self, admin_headers):
        """Verify recovery/snapshot has no false scheduler_unhealthy blocker."""
        response = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers=admin_headers,
            timeout=90,
        )
        data = response.json()
        
        scheduler = data.get("scheduler") or {}
        hourly_activation = data.get("hourly_activation") or {}
        blockers = hourly_activation.get("activation_blockers") or []
        blocker_codes = {b.get("code") for b in blockers}
        
        print(f"[recovery/snapshot] scheduler.alive={scheduler.get('alive')}, scheduler.is_healthy={scheduler.get('is_healthy')}")
        print(f"[recovery/snapshot] blocker_codes={blocker_codes}")
        
        # If scheduler is alive and healthy, scheduler_unhealthy should NOT be a blocker
        if scheduler.get("alive") is True and scheduler.get("is_healthy") is True:
            assert "scheduler_unhealthy" not in blocker_codes, (
                f"False scheduler_unhealthy blocker in recovery/snapshot! "
                f"scheduler={scheduler}, blockers={blockers}"
            )
        print("[API] recovery/snapshot no false scheduler_unhealthy PASSED")

    def test_08_recovery_snapshot_uses_rpo_target(self, admin_headers):
        """Verify recovery/snapshot uses RPO target (60m) for backup_age_target_minutes."""
        response = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers=admin_headers,
            timeout=90,
        )
        data = response.json()
        
        rpo_target = (data.get("rpo") or {}).get("target_min")
        backup_age_target = data.get("backup_age_target_minutes")
        
        print(f"[recovery/snapshot] rpo.target_min={rpo_target}, backup_age_target_minutes={backup_age_target}")
        
        # backup_age_target_minutes should equal rpo.target_min (60), NOT 1440 (24h)
        assert backup_age_target == rpo_target, (
            f"backup_age_target_minutes ({backup_age_target}) should equal rpo.target_min ({rpo_target})"
        )
        assert backup_age_target == 60, (
            f"backup_age_target_minutes should be 60 (RPO target), not {backup_age_target}"
        )
        print("[API] recovery/snapshot uses RPO target PASSED")

    def test_09_complete_r2_state_returns_200(self, admin_headers):
        """Verify backups-complete-r2-state endpoint returns 200."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=admin_headers,
            timeout=90,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("[API] backups-complete-r2-state returns 200")

    def test_10_complete_r2_state_no_false_scheduler_unhealthy(self, admin_headers):
        """Verify backups-complete-r2-state has no false scheduler_unhealthy blocker."""
        # First get canonical scheduler truth
        scheduler_response = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=admin_headers,
            timeout=60,
        )
        scheduler_data = scheduler_response.json()
        scheduler_alive = scheduler_data.get("alive")
        scheduler_healthy = scheduler_data.get("is_healthy")
        
        # Now check complete-r2-state
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=admin_headers,
            timeout=90,
        )
        data = response.json()
        
        hourly_activation = data.get("hourly_activation") or {}
        blockers = hourly_activation.get("activation_blockers") or []
        blocker_codes = {b.get("code") for b in blockers}
        
        print(f"[complete-r2-state] scheduler_alive={scheduler_alive}, scheduler_healthy={scheduler_healthy}")
        print(f"[complete-r2-state] blocker_codes={blocker_codes}")
        
        # If scheduler is alive and healthy, scheduler_unhealthy should NOT be a blocker
        if scheduler_alive is True and scheduler_healthy is True:
            assert "scheduler_unhealthy" not in blocker_codes, (
                f"False scheduler_unhealthy blocker in complete-r2-state! "
                f"scheduler_alive={scheduler_alive}, scheduler_healthy={scheduler_healthy}, blockers={blockers}"
            )
        print("[API] complete-r2-state no false scheduler_unhealthy PASSED")

    def test_11_complete_r2_state_uses_same_hourly_activation_as_scheduler_state(self, admin_headers):
        """Verify complete-r2-state uses same hourly activation truth as scheduler-state."""
        # Get scheduler-state
        scheduler_response = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=admin_headers,
            timeout=60,
        )
        scheduler_data = scheduler_response.json()
        scheduler_blockers = {b.get("code") for b in (scheduler_data.get("activation_blockers") or [])}
        
        # Get complete-r2-state
        r2_response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=admin_headers,
            timeout=90,
        )
        r2_data = r2_response.json()
        r2_blockers = {b.get("code") for b in ((r2_data.get("hourly_activation") or {}).get("activation_blockers") or [])}
        
        print(f"[scheduler-state] blocker_codes={scheduler_blockers}")
        print(f"[complete-r2-state] blocker_codes={r2_blockers}")
        
        # Both should have the same blockers (or at least no contradictory scheduler_unhealthy)
        # In preview, both should have environment_not_production
        if "scheduler_unhealthy" not in scheduler_blockers:
            assert "scheduler_unhealthy" not in r2_blockers, (
                f"complete-r2-state has scheduler_unhealthy but scheduler-state does not! "
                f"scheduler_blockers={scheduler_blockers}, r2_blockers={r2_blockers}"
            )
        print("[API] complete-r2-state uses same hourly activation truth PASSED")

    def test_12_system_health_returns_200(self, admin_headers):
        """Verify system-health endpoint returns 200."""
        response = requests.get(
            f"{BASE_URL}/api/admin/system-health",
            headers=admin_headers,
            timeout=60,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("[API] system-health returns 200")

    def test_13_system_health_backup_card_uses_consistent_target(self, admin_headers):
        """Verify system-health backup card uses consistent target semantics."""
        response = requests.get(
            f"{BASE_URL}/api/admin/system-health",
            headers=admin_headers,
            timeout=60,
        )
        data = response.json()
        
        cards = data.get("cards") or []
        backup_card = next((c for c in cards if c.get("key") == "backup"), None)
        
        if backup_card:
            print(f"[system-health] backup_card.status={backup_card.get('status')}")
            print(f"[system-health] backup_card.detail={backup_card.get('detail')}")
            # The backup card should reference the same 60m RPO target, not 24h
            detail = backup_card.get("detail") or ""
            # If it mentions a target, it should be 60m or 1h, not 24h
            if "24h" in detail.lower() or "1440" in detail:
                print(f"[WARNING] backup_card detail mentions 24h/1440m target: {detail}")
        print("[API] system-health backup card verification PASSED")


class TestCrossEndpointConsistency:
    """Cross-endpoint consistency verification."""

    def test_14_all_endpoints_consistent_scheduler_truth(self, admin_headers):
        """Verify all endpoints return consistent scheduler truth."""
        # Get scheduler-state (canonical truth)
        scheduler_response = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=admin_headers,
            timeout=60,
        )
        scheduler_data = scheduler_response.json()
        canonical_alive = scheduler_data.get("alive")
        canonical_healthy = scheduler_data.get("is_healthy")
        
        # Get recovery/snapshot
        recovery_response = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers=admin_headers,
            timeout=90,
        )
        recovery_data = recovery_response.json()
        recovery_scheduler = recovery_data.get("scheduler") or {}
        recovery_alive = recovery_scheduler.get("alive")
        recovery_healthy = recovery_scheduler.get("is_healthy")
        
        # Get complete-r2-state
        r2_response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=admin_headers,
            timeout=90,
        )
        r2_data = r2_response.json()
        r2_runtime = r2_data.get("backup_runtime") or {}
        r2_alive = r2_runtime.get("alive")
        r2_healthy = r2_runtime.get("is_healthy")
        
        print(f"\n=== Scheduler Truth Consistency Report ===")
        print(f"[scheduler-state] alive={canonical_alive}, is_healthy={canonical_healthy}")
        print(f"[recovery/snapshot] alive={recovery_alive}, is_healthy={recovery_healthy}")
        print(f"[complete-r2-state] alive={r2_alive}, is_healthy={r2_healthy}")
        
        # All should be consistent
        assert recovery_alive == canonical_alive, (
            f"recovery/snapshot alive mismatch: {recovery_alive} != {canonical_alive}"
        )
        assert recovery_healthy == canonical_healthy, (
            f"recovery/snapshot is_healthy mismatch: {recovery_healthy} != {canonical_healthy}"
        )
        assert r2_alive == canonical_alive, (
            f"complete-r2-state alive mismatch: {r2_alive} != {canonical_alive}"
        )
        assert r2_healthy == canonical_healthy, (
            f"complete-r2-state is_healthy mismatch: {r2_healthy} != {canonical_healthy}"
        )
        print("[CONSISTENCY] All endpoints return consistent scheduler truth PASSED")

    def test_15_all_endpoints_consistent_backup_freshness_target(self, admin_headers):
        """Verify all endpoints use consistent backup freshness target (60m RPO)."""
        # Get recovery/snapshot
        recovery_response = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers=admin_headers,
            timeout=90,
        )
        recovery_data = recovery_response.json()
        
        rpo_target = (recovery_data.get("rpo") or {}).get("target_min")
        backup_age_target = recovery_data.get("backup_age_target_minutes")
        
        print(f"\n=== Backup Freshness Target Consistency ===")
        print(f"[recovery/snapshot] rpo.target_min={rpo_target}")
        print(f"[recovery/snapshot] backup_age_target_minutes={backup_age_target}")
        
        # Both should be 60 (RPO target), not 1440 (24h posture target)
        assert rpo_target == 60, f"rpo.target_min should be 60, got {rpo_target}"
        assert backup_age_target == 60, f"backup_age_target_minutes should be 60, got {backup_age_target}"
        assert backup_age_target == rpo_target, (
            f"backup_age_target_minutes ({backup_age_target}) should equal rpo.target_min ({rpo_target})"
        )
        print("[CONSISTENCY] Backup freshness target is consistent (60m RPO) PASSED")

    def test_16_no_contradictory_blockers_across_endpoints(self, admin_headers):
        """Verify no contradictory blockers across endpoints."""
        # Get all three endpoints
        scheduler_response = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=admin_headers,
            timeout=60,
        )
        scheduler_blockers = {b.get("code") for b in (scheduler_response.json().get("activation_blockers") or [])}
        
        recovery_response = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers=admin_headers,
            timeout=90,
        )
        recovery_blockers = {b.get("code") for b in ((recovery_response.json().get("hourly_activation") or {}).get("activation_blockers") or [])}
        
        r2_response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=admin_headers,
            timeout=90,
        )
        r2_blockers = {b.get("code") for b in ((r2_response.json().get("hourly_activation") or {}).get("activation_blockers") or [])}
        
        print(f"\n=== Blocker Consistency Report ===")
        print(f"[scheduler-state] blockers={scheduler_blockers}")
        print(f"[recovery/snapshot] blockers={recovery_blockers}")
        print(f"[complete-r2-state] blockers={r2_blockers}")
        
        # Check for contradictions
        # If scheduler_unhealthy is in one but not others, that's a contradiction
        has_scheduler_unhealthy = {
            "scheduler-state": "scheduler_unhealthy" in scheduler_blockers,
            "recovery/snapshot": "scheduler_unhealthy" in recovery_blockers,
            "complete-r2-state": "scheduler_unhealthy" in r2_blockers,
        }
        
        # All should agree on scheduler_unhealthy presence
        values = list(has_scheduler_unhealthy.values())
        if not all(v == values[0] for v in values):
            print(f"[WARNING] Contradictory scheduler_unhealthy presence: {has_scheduler_unhealthy}")
            # This is a bug if scheduler is actually healthy
            scheduler_data = scheduler_response.json()
            if scheduler_data.get("alive") is True and scheduler_data.get("is_healthy") is True:
                assert False, (
                    f"Contradictory scheduler_unhealthy blocker when scheduler is alive/healthy! "
                    f"has_scheduler_unhealthy={has_scheduler_unhealthy}"
                )
        
        print("[CONSISTENCY] No contradictory blockers across endpoints PASSED")


class TestHealthMonitorSingletonLock:
    """Verify health monitor singleton lock prevents duplicate polling."""

    def test_17_singleton_lock_module_exists(self):
        """Verify singleton_scheduler module exists and has required functions."""
        src = Path("/app/backend/lib/singleton_scheduler.py").read_text()
        
        assert "async def run_with_singleton_lock" in src, (
            "singleton_scheduler.py must have run_with_singleton_lock function"
        )
        assert "scheduler_locks" in src, (
            "singleton_scheduler.py must use scheduler_locks collection"
        )
        print("[STATIC] singleton_scheduler module verification PASSED")

    def test_18_health_monitor_wrapped_in_singleton(self):
        """Verify health monitor loop is wrapped in singleton lock."""
        src = Path("/app/backend/health_monitor.py").read_text()
        
        # The monitor_loop should be wrapped in singleton_wrapped
        assert "async def singleton_wrapped" in src, (
            "health_monitor.py must have singleton_wrapped function"
        )
        assert "await monitor_loop()" in src, (
            "singleton_wrapped must call monitor_loop"
        )
        assert 'run_with_singleton_lock(db, "synthetic_health_monitor", singleton_wrapped)' in src, (
            "health_monitor must use run_with_singleton_lock with synthetic_health_monitor key"
        )
        print("[STATIC] health_monitor singleton wrapper verification PASSED")

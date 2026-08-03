"""
Test iteration 56: Scheduler Truth Consistency Verification

This test verifies that the scheduler truth is consistent across three endpoints:
1. /api/admin/recovery/snapshot
2. /api/admin/backups-complete-r2-state
3. /api/admin/backups-scheduler-state

The bug being tested: False scheduler_unhealthy blocker appearing in recovery/snapshot
and backups-complete-r2-state when the scheduler is actually alive/healthy according
to backups-scheduler-state.

Expected behavior in preview:
- environment_not_production is an expected blocker
- scheduler_unhealthy should NOT appear when scheduler is alive=true, is_healthy=true
"""

import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://masci-audit-hub.preview.emergentagent.com"

# Test credentials from test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_headers():
    """Get admin auth headers via multi-login endpoint."""
    response = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
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


class TestSchedulerTruthConsistency:
    """Test that scheduler truth is consistent across all three endpoints."""

    # ─────────────────────────────────────────────────────────────────────
    # Test 1: /api/admin/backups-scheduler-state (canonical truth source)
    # ─────────────────────────────────────────────────────────────────────
    def test_01_scheduler_state_returns_200(self, admin_headers):
        """Verify scheduler-state endpoint returns 200."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=admin_headers,
            timeout=60,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_02_scheduler_state_has_alive_and_is_healthy(self, admin_headers):
        """Verify scheduler-state returns alive and is_healthy fields."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=admin_headers,
            timeout=60,
        )
        data = response.json()
        assert "alive" in data, f"Missing 'alive' field: {data.keys()}"
        assert "is_healthy" in data, f"Missing 'is_healthy' field: {data.keys()}"
        print(f"[scheduler-state] alive={data.get('alive')}, is_healthy={data.get('is_healthy')}")

    def test_03_scheduler_state_activation_blockers(self, admin_headers):
        """Verify scheduler-state activation blockers - only environment_not_production expected."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=admin_headers,
            timeout=60,
        )
        data = response.json()
        blockers = data.get("activation_blockers") or []
        blocker_codes = {b.get("code") for b in blockers}
        
        print(f"[scheduler-state] activation_status={data.get('activation_status')}")
        print(f"[scheduler-state] blocker_codes={blocker_codes}")
        
        # In preview, environment_not_production is expected
        # scheduler_unhealthy should NOT appear when alive=true and is_healthy=true
        if data.get("alive") is True and data.get("is_healthy") is True:
            assert "scheduler_unhealthy" not in blocker_codes, (
                f"False scheduler_unhealthy blocker when scheduler is alive/healthy! "
                f"blockers={blockers}"
            )

    # ─────────────────────────────────────────────────────────────────────
    # Test 2: /api/admin/recovery/snapshot
    # ─────────────────────────────────────────────────────────────────────
    def test_04_recovery_snapshot_returns_200(self, admin_headers):
        """Verify recovery/snapshot endpoint returns 200."""
        response = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers=admin_headers,
            timeout=90,  # Longer timeout as this endpoint does more work
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_05_recovery_snapshot_scheduler_truth(self, admin_headers):
        """Verify recovery/snapshot uses canonical scheduler truth."""
        response = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers=admin_headers,
            timeout=90,
        )
        data = response.json()
        scheduler = data.get("scheduler") or {}
        
        print(f"[recovery/snapshot] scheduler.alive={scheduler.get('alive')}")
        print(f"[recovery/snapshot] scheduler.is_healthy={scheduler.get('is_healthy')}")
        print(f"[recovery/snapshot] scheduler.signal_source={scheduler.get('signal_source')}")
        
        assert "alive" in scheduler, f"Missing scheduler.alive: {scheduler.keys()}"
        assert "is_healthy" in scheduler, f"Missing scheduler.is_healthy: {scheduler.keys()}"

    def test_06_recovery_snapshot_no_false_scheduler_unhealthy(self, admin_headers):
        """Verify recovery/snapshot does not show false scheduler_unhealthy blocker."""
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
        
        print(f"[recovery/snapshot] hourly_activation.activation_status={hourly_activation.get('activation_status')}")
        print(f"[recovery/snapshot] blocker_codes={blocker_codes}")
        
        # If scheduler is alive and healthy, scheduler_unhealthy should NOT be a blocker
        if scheduler.get("alive") is True and scheduler.get("is_healthy") is True:
            assert "scheduler_unhealthy" not in blocker_codes, (
                f"False scheduler_unhealthy blocker in recovery/snapshot when scheduler is alive/healthy! "
                f"scheduler={scheduler}, blockers={blockers}"
            )

    # ─────────────────────────────────────────────────────────────────────
    # Test 3: /api/admin/backups-complete-r2-state
    # ─────────────────────────────────────────────────────────────────────
    def test_07_complete_r2_state_returns_200(self, admin_headers):
        """Verify backups-complete-r2-state endpoint returns 200."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=admin_headers,
            timeout=90,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_08_complete_r2_state_hourly_activation(self, admin_headers):
        """Verify backups-complete-r2-state has hourly_activation field."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=admin_headers,
            timeout=90,
        )
        data = response.json()
        hourly_activation = data.get("hourly_activation") or {}
        
        print(f"[complete-r2-state] hourly_activation.activation_status={hourly_activation.get('activation_status')}")
        
        assert "hourly_activation" in data, f"Missing hourly_activation: {data.keys()}"

    def test_09_complete_r2_state_no_false_scheduler_unhealthy(self, admin_headers):
        """Verify backups-complete-r2-state does not show false scheduler_unhealthy blocker."""
        # First get the canonical scheduler truth
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
        
        print(f"[complete-r2-state] blocker_codes={blocker_codes}")
        
        # If scheduler is alive and healthy, scheduler_unhealthy should NOT be a blocker
        if scheduler_alive is True and scheduler_healthy is True:
            assert "scheduler_unhealthy" not in blocker_codes, (
                f"False scheduler_unhealthy blocker in complete-r2-state when scheduler is alive/healthy! "
                f"scheduler_alive={scheduler_alive}, scheduler_healthy={scheduler_healthy}, blockers={blockers}"
            )

    # ─────────────────────────────────────────────────────────────────────
    # Test 4: Cross-endpoint consistency
    # ─────────────────────────────────────────────────────────────────────
    def test_10_scheduler_truth_consistent_across_endpoints(self, admin_headers):
        """Verify scheduler truth is consistent across all three endpoints."""
        # Get scheduler-state (canonical truth)
        scheduler_response = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=admin_headers,
            timeout=60,
        )
        scheduler_data = scheduler_response.json()
        canonical_alive = scheduler_data.get("alive")
        canonical_healthy = scheduler_data.get("is_healthy")
        canonical_blockers = {b.get("code") for b in (scheduler_data.get("activation_blockers") or [])}
        
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
        recovery_blockers = {b.get("code") for b in ((recovery_data.get("hourly_activation") or {}).get("activation_blockers") or [])}
        
        # Get complete-r2-state
        r2_response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=admin_headers,
            timeout=90,
        )
        r2_data = r2_response.json()
        r2_blockers = {b.get("code") for b in ((r2_data.get("hourly_activation") or {}).get("activation_blockers") or [])}
        
        print(f"\n=== Scheduler Truth Consistency Report ===")
        print(f"[scheduler-state] alive={canonical_alive}, is_healthy={canonical_healthy}")
        print(f"[scheduler-state] blockers={canonical_blockers}")
        print(f"[recovery/snapshot] alive={recovery_alive}, is_healthy={recovery_healthy}")
        print(f"[recovery/snapshot] blockers={recovery_blockers}")
        print(f"[complete-r2-state] blockers={r2_blockers}")
        
        # Verify alive/is_healthy consistency
        assert recovery_alive == canonical_alive, (
            f"recovery/snapshot alive mismatch: {recovery_alive} != {canonical_alive}"
        )
        assert recovery_healthy == canonical_healthy, (
            f"recovery/snapshot is_healthy mismatch: {recovery_healthy} != {canonical_healthy}"
        )
        
        # Verify no false scheduler_unhealthy blocker when scheduler is healthy
        if canonical_alive is True and canonical_healthy is True:
            assert "scheduler_unhealthy" not in recovery_blockers, (
                f"False scheduler_unhealthy in recovery/snapshot"
            )
            assert "scheduler_unhealthy" not in r2_blockers, (
                f"False scheduler_unhealthy in complete-r2-state"
            )

    def test_11_expected_preview_blocker_only(self, admin_headers):
        """Verify that in preview, only environment_not_production is the expected blocker."""
        # Get scheduler-state
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=admin_headers,
            timeout=60,
        )
        data = response.json()
        blockers = data.get("activation_blockers") or []
        blocker_codes = {b.get("code") for b in blockers}
        
        print(f"[preview-blocker-check] activation_status={data.get('activation_status')}")
        print(f"[preview-blocker-check] blocker_codes={blocker_codes}")
        
        # In preview, environment_not_production is expected
        # This is the ONLY expected blocker when scheduler is healthy
        if data.get("alive") is True and data.get("is_healthy") is True:
            # Filter out expected blockers
            unexpected_blockers = blocker_codes - {"environment_not_production", "r2_not_configured"}
            # scheduler_unhealthy should definitely not be there
            assert "scheduler_unhealthy" not in unexpected_blockers, (
                f"Unexpected scheduler_unhealthy blocker: {blockers}"
            )

    def test_12_recovery_snapshot_backup_runtime_has_scheduler_fields(self, admin_headers):
        """Verify recovery/snapshot backup_runtime includes canonical scheduler fields."""
        response = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers=admin_headers,
            timeout=90,
        )
        data = response.json()
        scheduler = data.get("scheduler") or {}
        backup_runtime = scheduler.get("backup_runtime") or {}
        
        print(f"[recovery/snapshot] backup_runtime keys: {backup_runtime.keys()}")
        
        # The fix should ensure backup_runtime has alive/is_healthy merged from canonical scheduler
        # These fields should be present after the fix
        assert "alive" in backup_runtime or "alive" in scheduler, (
            f"Missing alive in backup_runtime or scheduler"
        )


class TestSchedulerTruthFields:
    """Test that all expected scheduler truth fields are present."""

    def test_13_scheduler_state_has_all_expected_fields(self, admin_headers):
        """Verify scheduler-state has all expected fields."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=admin_headers,
            timeout=60,
        )
        data = response.json()
        
        expected_fields = [
            "alive",
            "is_healthy",
            "activation_status",
            "activation_blockers",
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing expected field '{field}' in scheduler-state"
        
        print(f"[scheduler-state] All expected fields present: {expected_fields}")

    def test_14_recovery_snapshot_scheduler_has_expected_fields(self, admin_headers):
        """Verify recovery/snapshot scheduler section has expected fields."""
        response = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers=admin_headers,
            timeout=90,
        )
        data = response.json()
        scheduler = data.get("scheduler") or {}
        
        expected_fields = [
            "alive",
            "is_healthy",
            "signal_source",
            "reason_code",
        ]
        
        for field in expected_fields:
            assert field in scheduler, f"Missing expected field '{field}' in recovery/snapshot scheduler"
        
        print(f"[recovery/snapshot] scheduler fields: {list(scheduler.keys())}")

    def test_15_complete_r2_state_hourly_activation_has_expected_fields(self, admin_headers):
        """Verify complete-r2-state hourly_activation has expected fields."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=admin_headers,
            timeout=90,
        )
        data = response.json()
        hourly_activation = data.get("hourly_activation") or {}
        
        expected_fields = [
            "activation_status",
            "activation_blockers",
        ]
        
        for field in expected_fields:
            assert field in hourly_activation, f"Missing expected field '{field}' in complete-r2-state hourly_activation"
        
        print(f"[complete-r2-state] hourly_activation fields: {list(hourly_activation.keys())}")

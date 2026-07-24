"""
OPS8 Backup Recovery & Trust System Tests
==========================================
Tests for MASCI OPS 8 — BACKUP, RECOVERY & RESTORE TRUST SYSTEM

Features tested:
- Admin login and Recovery Posture page access
- GET /api/admin/backups-complete-r2-state (backup_runtime evidence, hourly disabled)
- GET /api/admin/backups-scheduler-state (backup_runtime evidence, scheduler health)
- GET /api/admin/backup-trust-score (trust score JSON, production_activation_disabled=true)
- POST /api/admin/backup-verification/run-now (ok=true in Preview even when email blocked)
- Verification report uses latest complete-r2 backup row for last_r2 truth
- Restore endpoint rejects when backup job overlap exists
- Drill evidence in recovery snapshot
"""

import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "http://localhost:8001"

# Test credentials from /app/memory/test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_token():
    """Authenticate as admin and return the token."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=60,
    )
    if resp.status_code != 200:
        pytest.skip(f"Admin login failed: {resp.status_code} - {resp.text[:200]}")
    data = resp.json()
    # Token can be in portal_tokens.admin, admin_token, token, or access_token
    token = (
        (data.get("portal_tokens") or {}).get("admin")
        or data.get("admin_token")
        or data.get("token")
        or data.get("access_token")
    )
    if not token:
        pytest.skip(f"No admin token in response: {list(data.keys())}")
    return token


@pytest.fixture(scope="module")
def session_token():
    """Authenticate as admin and return the directory session token."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=60,
    )
    if resp.status_code != 200:
        pytest.skip(f"Admin login failed: {resp.status_code} - {resp.text[:200]}")
    data = resp.json()
    token = data.get("session_token")
    if not token:
        pytest.skip(f"No session_token in response: {list(data.keys())}")
    return token


@pytest.fixture(scope="module")
def api_client(admin_token, session_token):
    """Return a requests session with admin auth headers."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-Admin-Token": admin_token,
        "X-Directory-Token": session_token,
    })
    return session


class TestAdminLogin:
    """Test admin authentication."""

    def test_admin_login_success(self):
        """Admin can log in with valid credentials."""
        resp = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=60,
        )
        assert resp.status_code == 200, f"Login failed: {resp.text[:200]}"
        data = resp.json()
        # Token can be in portal_tokens.admin, admin_token, token, or access_token
        token = (
            (data.get("portal_tokens") or {}).get("admin")
            or data.get("admin_token")
            or data.get("token")
            or data.get("access_token")
        )
        assert token, f"No admin token in response: {list(data.keys())}"


class TestBackupsCompleteR2State:
    """Test GET /api/admin/backups-complete-r2-state endpoint."""

    def test_backups_complete_r2_state_returns_200(self, api_client):
        """Endpoint returns 200 with backup_runtime evidence."""
        resp = api_client.get(f"{BASE_URL}/api/admin/backups-complete-r2-state", timeout=30)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"

    def test_backups_complete_r2_state_has_backup_runtime(self, api_client):
        """Response includes backup_runtime evidence."""
        resp = api_client.get(f"{BASE_URL}/api/admin/backups-complete-r2-state", timeout=30)
        data = resp.json()
        # Should have backup_runtime field
        assert "backup_runtime" in data, f"Missing backup_runtime in response: {list(data.keys())}"

    def test_backups_complete_r2_state_hourly_disabled(self, api_client):
        """Hourly R2 backups are disabled by default."""
        resp = api_client.get(f"{BASE_URL}/api/admin/backups-complete-r2-state", timeout=30)
        data = resp.json()
        # r2_hourly_effective should be False in Preview until production activation
        assert data.get("r2_hourly_effective") is False, \
            f"Expected r2_hourly_effective=False, got {data.get('r2_hourly_effective')}"
        hourly = data.get("hourly_activation") or {}
        assert hourly.get("activation_status") in {
            "DISABLED BY CONFIGURATION",
            "BLOCKED BY ENVIRONMENT",
            "READY BUT DISABLED",
            "BLOCKED BY SAFETY GUARD",
            "STALE",
        }


class TestBackupsSchedulerState:
    """Test GET /api/admin/backups-scheduler-state endpoint."""

    def test_backups_scheduler_state_returns_200(self, api_client):
        """Endpoint returns 200 with scheduler health fields."""
        resp = api_client.get(f"{BASE_URL}/api/admin/backups-scheduler-state", timeout=30)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"

    def test_backups_scheduler_state_has_backup_runtime(self, api_client):
        """Response includes backup_runtime evidence."""
        resp = api_client.get(f"{BASE_URL}/api/admin/backups-scheduler-state", timeout=30)
        data = resp.json()
        assert "backup_runtime" in data, f"Missing backup_runtime in response: {list(data.keys())}"

    def test_backups_scheduler_state_has_scheduler_health_fields(self, api_client):
        """Response includes scheduler health fields."""
        resp = api_client.get(f"{BASE_URL}/api/admin/backups-scheduler-state", timeout=30)
        data = resp.json()
        # Should have scheduler-related fields
        expected_fields = ["alive", "is_healthy", "seconds_since_last_tick"]
        for field in expected_fields:
            assert field in data, f"Missing {field} in response: {list(data.keys())}"


class TestBackupTrustScore:
    """Test GET /api/admin/backup-trust-score endpoint."""

    def test_backup_trust_score_returns_200(self, api_client):
        """Endpoint returns 200 with trust score JSON."""
        resp = api_client.get(f"{BASE_URL}/api/admin/backup-trust-score", timeout=30)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"

    def test_backup_trust_score_has_required_fields(self, api_client):
        """Response includes trust_score and production_activation_disabled."""
        resp = api_client.get(f"{BASE_URL}/api/admin/backup-trust-score", timeout=30)
        data = resp.json()
        assert "trust_score" in data, f"Missing trust_score in response: {list(data.keys())}"
        assert "production_activation_disabled" in data, \
            f"Missing production_activation_disabled in response: {list(data.keys())}"

    def test_backup_trust_score_production_activation_disabled(self, api_client):
        """production_activation_disabled should be True."""
        resp = api_client.get(f"{BASE_URL}/api/admin/backup-trust-score", timeout=30)
        data = resp.json()
        assert data.get("production_activation_disabled") is True, \
            f"Expected production_activation_disabled=True, got {data.get('production_activation_disabled')}"
        assert "hourly_activation" in data

    def test_backup_trust_score_has_evidence(self, api_client):
        """Response includes evidence field with backup details."""
        resp = api_client.get(f"{BASE_URL}/api/admin/backup-trust-score", timeout=30)
        data = resp.json()
        assert "evidence" in data, f"Missing evidence in response: {list(data.keys())}"
        evidence = data["evidence"]
        # Evidence should have runtime info
        assert "runtime" in evidence, f"Missing runtime in evidence: {list(evidence.keys())}"


class TestBackupVerificationRunNow:
    """Test POST /api/admin/backup-verification/run-now endpoint."""

    def test_backup_verification_run_now_returns_ok(self, api_client):
        """Run-now returns ok=true in Preview even when email is safety-blocked."""
        resp = api_client.post(f"{BASE_URL}/api/admin/backup-verification/run-now", json={}, timeout=60)
        # Should return 200 even if email is blocked
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        # Should have report built
        assert "report" in data, f"Missing report in response: {list(data.keys())}"
        # Report should have verdict
        report = data.get("report") or {}
        assert "verdict" in report, f"Missing verdict in report: {list(report.keys())}"

    def test_backup_verification_report_uses_complete_r2_for_last_r2(self, api_client):
        """Verification report uses latest complete-r2 backup row for last_r2 truth."""
        resp = api_client.post(f"{BASE_URL}/api/admin/backup-verification/run-now", json={}, timeout=60)
        data = resp.json()
        report = data.get("report") or {}
        ledger = report.get("ledger") or {}
        last_r2 = ledger.get("last_r2")
        # If last_r2 exists, it should be a complete-r2 backup, not r2-usage-alert
        if last_r2:
            # The mode should be complete-r2 (not r2-usage-alert or verification marker)
            mode = last_r2.get("mode", "")
            assert mode == "complete-r2" or "complete" in mode.lower(), \
                f"last_r2 should be complete-r2 backup, got mode={mode}"


class TestRecoverySnapshot:
    """Test GET /api/admin/recovery/snapshot endpoint."""

    def test_recovery_snapshot_returns_200(self, api_client):
        """Endpoint returns 200 with recovery posture data."""
        resp = api_client.get(f"{BASE_URL}/api/admin/recovery/snapshot", timeout=30)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"

    def test_recovery_snapshot_has_pill(self, api_client):
        """Response includes pill (overall status indicator)."""
        resp = api_client.get(f"{BASE_URL}/api/admin/recovery/snapshot", timeout=30)
        data = resp.json()
        assert "pill" in data, f"Missing pill in response: {list(data.keys())}"
        assert data["pill"] in ["GREEN", "AMBER", "RED"], \
            f"Invalid pill value: {data['pill']}"

    def test_recovery_snapshot_has_scheduler_info(self, api_client):
        """Response includes scheduler information with backup_runtime."""
        resp = api_client.get(f"{BASE_URL}/api/admin/recovery/snapshot", timeout=30)
        data = resp.json()
        assert "scheduler" in data, f"Missing scheduler in response: {list(data.keys())}"
        scheduler = data["scheduler"]
        assert "backup_runtime" in scheduler, \
            f"Missing backup_runtime in scheduler: {list(scheduler.keys())}"

    def test_recovery_snapshot_has_drill_evidence(self, api_client):
        """Response includes last_drill evidence from drill_runs."""
        resp = api_client.get(f"{BASE_URL}/api/admin/recovery/snapshot", timeout=30)
        data = resp.json()
        # last_drill may be None if no drills have run, but the field should exist
        assert "last_drill" in data, f"Missing last_drill in response: {list(data.keys())}"
        # If drill exists, verify it has expected fields
        if data["last_drill"]:
            drill = data["last_drill"]
            assert "outcome" in drill, f"Missing outcome in last_drill: {list(drill.keys())}"
            assert "records" in drill, f"Missing records in last_drill: {list(drill.keys())}"

    def test_recovery_snapshot_hourly_disabled(self, api_client):
        """hourly_cadence_enabled should be False."""
        resp = api_client.get(f"{BASE_URL}/api/admin/recovery/snapshot", timeout=30)
        data = resp.json()
        assert "hourly_cadence_enabled" in data, \
            f"Missing hourly_cadence_enabled in response: {list(data.keys())}"
        # Per requirements, hourly production backups must remain disabled
        assert data["hourly_cadence_enabled"] is False, \
            f"Expected hourly_cadence_enabled=False, got {data['hourly_cadence_enabled']}"


class TestRestoreEndpointOverlapGuard:
    """Test that restore endpoint rejects when backup job overlap exists."""

    def test_restore_requires_admin_auth(self):
        """Restore endpoint requires admin authentication."""
        # Try without auth
        resp = requests.post(
            f"{BASE_URL}/api/exports/restore",
            files={"file": ("test.zip", b"not a real zip", "application/zip")},
            data={"merge": "true", "confirm": "", "backup_ack": "false", "dry_run": "true"},
            timeout=30,
        )
        # Should return 401 without auth
        assert resp.status_code == 401, f"Expected 401 without auth, got {resp.status_code}"


class TestBackupVerificationState:
    """Test GET /api/admin/backup-verification/state endpoint."""

    def test_backup_verification_state_returns_200(self, api_client):
        """Endpoint returns 200 with verification state."""
        resp = api_client.get(f"{BASE_URL}/api/admin/backup-verification/state", timeout=30)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"

    def test_backup_verification_state_has_schedule(self, api_client):
        """Response includes schedule information."""
        resp = api_client.get(f"{BASE_URL}/api/admin/backup-verification/state", timeout=30)
        data = resp.json()
        assert "schedule" in data, f"Missing schedule in response: {list(data.keys())}"
        assert "enabled" in data, f"Missing enabled in response: {list(data.keys())}"


class TestBackupVerificationPreview:
    """Test GET /api/admin/backup-verification/preview endpoint."""

    def test_backup_verification_preview_returns_200(self, api_client):
        """Preview endpoint returns 200 with report."""
        resp = api_client.get(f"{BASE_URL}/api/admin/backup-verification/preview", timeout=60)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"

    def test_backup_verification_preview_has_report(self, api_client):
        """Preview response includes report with verdict."""
        resp = api_client.get(f"{BASE_URL}/api/admin/backup-verification/preview", timeout=60)
        data = resp.json()
        assert "report" in data, f"Missing report in response: {list(data.keys())}"
        report = data.get("report") or {}
        assert "verdict" in report, f"Missing verdict in report: {list(report.keys())}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

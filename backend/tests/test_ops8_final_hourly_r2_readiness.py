"""OPS8 Final Hourly R2 Activation Readiness Tests.

Tests the canonical hourly activation state, backup trust score, and
recovery dashboard endpoints for Preview environment compliance.

Key requirements:
- Preview environment never reports hourly effective=true
- activation_status should appear (not HARD-CODED DISABLED)
- hourly_activation fields present in API responses
- bucket usage evidence in backup-trust-score
"""

import os
import pytest
import requests
from pathlib import Path

# Load BASE_URL from frontend/.env if not in environment
def _load_base_url():
    url = os.environ.get("REACT_APP_BACKEND_URL", "").strip()
    if url:
        return url.rstrip("/")
    # Try to read from frontend/.env
    env_path = Path(__file__).parent.parent.parent / "frontend" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip().rstrip("/")
    return "http://localhost:8001"

# Use localhost for testing since external URL may be unavailable
BASE_URL = "http://localhost:8001"
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
def admin_session(admin_token, session_token):
    """Return a requests session with admin auth headers."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-Admin-Token": admin_token,
        "X-Directory-Token": session_token,
    })
    return session


class TestBackupsCompleteR2StateHourlyActivation:
    """Tests for /api/admin/backups-complete-r2-state hourly activation fields."""
    
    def test_returns_hourly_activation_object(self, admin_session):
        """Verify hourly_activation object is present in response."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/backups-complete-r2-state")
        assert resp.status_code == 200
        data = resp.json()
        
        assert "hourly_activation" in data, "Missing hourly_activation in response"
        hourly = data["hourly_activation"]
        assert isinstance(hourly, dict), "hourly_activation should be a dict"
    
    def test_hourly_activation_has_canonical_fields(self, admin_session):
        """Verify all canonical hourly activation fields are present."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/backups-complete-r2-state")
        assert resp.status_code == 200
        data = resp.json()
        hourly = data.get("hourly_activation", {})
        
        # Required canonical fields
        required_fields = [
            "r2_hourly_requested",
            "r2_hourly_effective",
            "r2_hourly_locked_off",
            "hourly_cadence_enabled",
            "activation_status",
            "environment",
        ]
        for field in required_fields:
            assert field in hourly, f"Missing required field: {field}"
    
    def test_preview_hourly_effective_is_false(self, admin_session):
        """Preview environment must never report hourly effective=true."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/backups-complete-r2-state")
        assert resp.status_code == 200
        data = resp.json()
        
        # Top-level fields
        assert data.get("r2_hourly_effective") is False, "r2_hourly_effective must be False in Preview"
        assert data.get("hourly_cadence_enabled") is False, "hourly_cadence_enabled must be False in Preview"
        
        # Nested hourly_activation fields
        hourly = data.get("hourly_activation", {})
        assert hourly.get("r2_hourly_effective") is False, "hourly_activation.r2_hourly_effective must be False"
        assert hourly.get("hourly_cadence_enabled") is False, "hourly_activation.hourly_cadence_enabled must be False"
    
    def test_activation_status_not_hardcoded_disabled(self, admin_session):
        """activation_status should be a meaningful status, not HARD-CODED DISABLED."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/backups-complete-r2-state")
        assert resp.status_code == 200
        data = resp.json()
        hourly = data.get("hourly_activation", {})
        
        status = hourly.get("activation_status", "")
        assert status, "activation_status should not be empty"
        # Should be one of the valid statuses from hourly_activation.py
        valid_statuses = [
            "ACTIVE",
            "STALE",
            "FAILED",
            "BLOCKED BY ENVIRONMENT",
            "BLOCKED BY SAFETY GUARD",
            "READY BUT DISABLED",
            "DISABLED BY CONFIGURATION",
        ]
        assert status in valid_statuses, f"Unexpected activation_status: {status}"
        # In Preview, it should be blocked by environment or disabled
        assert "HARD-CODED" not in status.upper(), "Status should not say HARD-CODED"
    
    def test_environment_is_preview(self, admin_session):
        """Verify environment field reflects Preview."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/backups-complete-r2-state")
        assert resp.status_code == 200
        data = resp.json()
        hourly = data.get("hourly_activation", {})
        
        env = hourly.get("environment", "")
        assert env == "preview", f"Expected environment=preview, got {env}"


class TestBackupTrustScoreHourlyActivation:
    """Tests for /api/admin/backup-trust-score hourly activation and bucket usage."""
    
    def test_returns_hourly_activation(self, admin_session):
        """Verify hourly_activation is present in backup-trust-score response."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/backup-trust-score")
        assert resp.status_code == 200
        data = resp.json()
        
        assert "hourly_activation" in data, "Missing hourly_activation in backup-trust-score"
        hourly = data["hourly_activation"]
        assert isinstance(hourly, dict), "hourly_activation should be a dict"
    
    def test_production_activation_disabled_in_preview(self, admin_session):
        """production_activation_disabled should be true in Preview."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/backup-trust-score")
        assert resp.status_code == 200
        data = resp.json()
        
        assert data.get("production_activation_disabled") is True, \
            "production_activation_disabled must be True in Preview"
    
    def test_has_bucket_usage_evidence(self, admin_session):
        """Verify bucket usage evidence is present."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/backup-trust-score")
        assert resp.status_code == 200
        data = resp.json()
        
        evidence = data.get("evidence", {})
        assert "bucket_usage" in evidence, "Missing bucket_usage in evidence"
        bucket = evidence["bucket_usage"]
        
        # Should have status and gb fields
        assert "status" in bucket, "bucket_usage missing status"
        assert "gb" in bucket or bucket.get("total_bytes") is not None, \
            "bucket_usage missing size information"
    
    def test_has_trust_score_fields(self, admin_session):
        """Verify trust score computation fields are present."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/backup-trust-score")
        assert resp.status_code == 200
        data = resp.json()
        
        # Core trust score fields
        assert "trust_score" in data, "Missing trust_score"
        assert "score_band" in data, "Missing score_band"
        assert "score_band_label" in data, "Missing score_band_label"
        assert "score_reason" in data, "Missing score_reason"
    
    def test_evidence_has_hourly_activation(self, admin_session):
        """Verify evidence includes hourly_activation."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/backup-trust-score")
        assert resp.status_code == 200
        data = resp.json()
        
        evidence = data.get("evidence", {})
        assert "hourly_activation" in evidence, "Missing hourly_activation in evidence"


class TestRecoverySnapshotHourlyActivation:
    """Tests for /api/admin/recovery/snapshot hourly activation fields."""
    
    def test_returns_hourly_activation(self, admin_session):
        """Verify hourly_activation is present in recovery snapshot."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/recovery/snapshot")
        assert resp.status_code == 200
        data = resp.json()
        
        assert "hourly_activation" in data, "Missing hourly_activation in recovery snapshot"
        hourly = data["hourly_activation"]
        assert isinstance(hourly, dict), "hourly_activation should be a dict"
    
    def test_hourly_cadence_enabled_is_false_in_preview(self, admin_session):
        """hourly_cadence_enabled must be False in Preview."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/recovery/snapshot")
        assert resp.status_code == 200
        data = resp.json()
        
        assert data.get("hourly_cadence_enabled") is False, \
            "hourly_cadence_enabled must be False in Preview"
    
    def test_has_full_restore_status(self, admin_session):
        """Verify full_restore_status is present."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/recovery/snapshot")
        assert resp.status_code == 200
        data = resp.json()
        
        assert "full_restore_status" in data, "Missing full_restore_status"
        frs = data["full_restore_status"]
        assert "status" in frs, "full_restore_status missing status"
        assert "message" in frs, "full_restore_status missing message"
    
    def test_has_production_only_evidence_status(self, admin_session):
        """Verify production_only_evidence_status is present."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/recovery/snapshot")
        assert resp.status_code == 200
        data = resp.json()
        
        assert "production_only_evidence_status" in data, "Missing production_only_evidence_status"
        poes = data["production_only_evidence_status"]
        assert "status" in poes, "production_only_evidence_status missing status"
        assert "message" in poes, "production_only_evidence_status missing message"
    
    def test_activation_status_in_hourly_activation(self, admin_session):
        """Verify activation_status is present and valid."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/recovery/snapshot")
        assert resp.status_code == 200
        data = resp.json()
        hourly = data.get("hourly_activation", {})
        
        status = hourly.get("activation_status", "")
        assert status, "activation_status should not be empty"
        assert "HARD-CODED" not in status.upper(), "Status should not say HARD-CODED"


class TestRetentionPolicyConstants:
    """Tests for approved retention policy constants."""
    
    def test_retention_constants_are_approved(self):
        """Verify retention constants match approved 72h/30d/90d/12m policy."""
        from lib.r2_retention import (
            HOURLY_RETENTION_HOURS,
            DAILY_RETENTION_DAYS,
            WEEKLY_RETENTION_DAYS,
            MONTHLY_RETENTION_MONTHS,
        )
        
        assert HOURLY_RETENTION_HOURS == 72, f"Expected 72h, got {HOURLY_RETENTION_HOURS}h"
        assert DAILY_RETENTION_DAYS == 30, f"Expected 30d, got {DAILY_RETENTION_DAYS}d"
        assert WEEKLY_RETENTION_DAYS == 90, f"Expected 90d, got {WEEKLY_RETENTION_DAYS}d"
        assert MONTHLY_RETENTION_MONTHS == 12, f"Expected 12m, got {MONTHLY_RETENTION_MONTHS}m"


class TestBackupRuntimeOverlapGuard:
    """Tests for backup/restore overlap prevention."""
    
    def test_overlap_classification_in_complete_r2_state(self, admin_session):
        """Verify overlap guard state is present in backups-complete-r2-state."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/backups-complete-r2-state")
        assert resp.status_code == 200
        data = resp.json()
        
        runtime = data.get("backup_runtime", {})
        assert "overlap" in runtime, "Missing overlap in backup_runtime"
        overlap = runtime["overlap"]
        
        # Should have backup_active and restore_active flags
        assert "backup_active" in overlap, "Missing backup_active in overlap"
        assert "restore_active" in overlap, "Missing restore_active in overlap"
        assert "overlap_blocked" in overlap, "Missing overlap_blocked in overlap"


class TestSchedulerHealthFields:
    """Tests for scheduler health fields in API responses."""
    
    def test_scheduler_state_has_health_fields(self, admin_session):
        """Verify scheduler state includes health fields."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/backups-scheduler-state")
        assert resp.status_code == 200
        data = resp.json()
        
        # Should have alive and is_healthy fields
        assert "alive" in data, "Missing alive field"
        assert "is_healthy" in data, "Missing is_healthy field"
        assert "seconds_since_last_tick" in data or "last_tick_ts" in data, \
            "Missing tick timing information"
    
    def test_recovery_snapshot_has_scheduler_info(self, admin_session):
        """Verify recovery snapshot includes scheduler info."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/recovery/snapshot")
        assert resp.status_code == 200
        data = resp.json()
        
        scheduler = data.get("scheduler", {})
        assert "alive" in scheduler, "Missing alive in scheduler"
        assert "is_healthy" in scheduler, "Missing is_healthy in scheduler"

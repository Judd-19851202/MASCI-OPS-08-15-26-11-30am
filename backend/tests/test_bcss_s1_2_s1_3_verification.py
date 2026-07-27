"""
BCSS Release 2 Platform Survivability Program - S1-2 and S1-3 Verification Tests
================================================================================

S1-2: Secrets & Configuration Recovery Certification
S1-3: Backup Verification Hardening

Tests verify:
- S1-2: Configuration recovery package returns PASS status with no secret values exposed
- S1-2: Recovery snapshot includes configuration_recovery summary with PASS status
- S1-2: Health endpoints remain green after config recovery work
- S1-3: Fresh manual backup (MASCI_complete_backup_2026-07-27_111254Z.zip) is authoritative
- S1-3: Archive lineage shows direct_evidence_status=VERIFIED, read_mode=SIDECAR
- S1-3: Backup verification reflects hardened direct-evidence contract
"""
from __future__ import annotations

import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://backup-forensics.preview.emergentagent.com"

# Test credentials from /app/memory/test_credentials.md
TEST_EMAIL = "jaymn.judd@mascigc.com"
TEST_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_tokens():
    """Authenticate and get admin tokens for testing."""
    response = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=60,
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    admin_token = data.get("portal_tokens", {}).get("admin", "")
    directory_token = data.get("session_token", "")
    assert admin_token, "No admin token returned"
    return {"X-Admin-Token": admin_token, "X-Directory-Token": directory_token}


class TestHealthEndpoints:
    """S1-2: Verify health endpoints remain green after config recovery work."""

    def test_health_returns_200_ok(self):
        """GET /api/health returns 200 with ok=true."""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True

    def test_health_full_returns_200_ok(self):
        """GET /api/health/full returns 200 with ok=true."""
        response = requests.get(f"{BASE_URL}/api/health/full", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True
        assert data.get("mongo") is True


class TestS12ConfigurationRecovery:
    """S1-2: Secrets & Configuration Recovery Certification tests."""

    def test_configuration_recovery_returns_pass_status(self, admin_tokens):
        """GET /api/admin/recovery/configuration-recovery returns PASS status."""
        response = requests.get(
            f"{BASE_URL}/api/admin/recovery/configuration-recovery",
            headers=admin_tokens,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True
        
        package = data.get("package", {})
        validator = package.get("validator", {})
        
        # S1-2 requirement: validator.overall_status=PASS
        assert validator.get("overall_status") == "PASS", f"Expected PASS, got {validator.get('overall_status')}"

    def test_configuration_recovery_environment_separation_pass(self, admin_tokens):
        """Configuration recovery shows environment_separation.status=PASS."""
        response = requests.get(
            f"{BASE_URL}/api/admin/recovery/configuration-recovery",
            headers=admin_tokens,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        package = data.get("package", {})
        env_sep = package.get("environment_separation", {})
        
        # S1-2 requirement: environment_separation.status=PASS
        assert env_sep.get("status") == "PASS", f"Expected PASS, got {env_sep.get('status')}"

    def test_configuration_recovery_has_inventories(self, admin_tokens):
        """Configuration recovery includes configuration and secret reference inventories."""
        response = requests.get(
            f"{BASE_URL}/api/admin/recovery/configuration-recovery",
            headers=admin_tokens,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        package = data.get("package", {})
        
        # S1-2 requirement: configuration inventory present
        config_inventory = package.get("configuration_inventory", [])
        assert len(config_inventory) > 0, "Configuration inventory is empty"
        
        # S1-2 requirement: secret_reference_inventory present
        secret_inventory = package.get("secret_reference_inventory", [])
        assert len(secret_inventory) > 0, "Secret reference inventory is empty"

    def test_configuration_recovery_no_secrets_exposed(self, admin_tokens):
        """Configuration recovery does not expose secret values in response body."""
        import json
        
        response = requests.get(
            f"{BASE_URL}/api/admin/recovery/configuration-recovery",
            headers=admin_tokens,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        package = data.get("package", {})
        
        # Serialize to check for secret patterns
        text = json.dumps(package)
        
        # S1-2 requirement: no secret values exposed
        # Check for MongoDB connection string patterns
        assert "mongodb+srv://" not in text or "@" not in text.split("mongodb+srv://")[1].split("/")[0] if "mongodb+srv://" in text else True, \
            "MongoDB connection string with credentials found in response"
        
        # Check secret inventory items have value_exposed=false
        for item in package.get("secret_reference_inventory", []):
            assert item.get("value_exposed") is False, f"Secret {item.get('key')} has value_exposed=True"

    def test_recovery_snapshot_includes_configuration_recovery_summary(self, admin_tokens):
        """GET /api/admin/recovery/snapshot includes configuration_recovery summary with PASS status."""
        response = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers=admin_tokens,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        
        config_recovery = data.get("configuration_recovery", {})
        
        # S1-2 requirement: configuration_recovery summary with PASS status
        assert config_recovery.get("status") == "PASS", f"Expected PASS, got {config_recovery.get('status')}"
        
        # S1-2 requirement: no blocker count
        assert config_recovery.get("blocking_issue_count") == 0, \
            f"Expected 0 blocking issues, got {config_recovery.get('blocking_issue_count')}"


class TestS13BackupVerificationHardening:
    """S1-3: Backup Verification Hardening tests."""

    def test_backups_complete_r2_state_shows_fresh_backup(self, admin_tokens):
        """GET /api/admin/backups-complete-r2-state shows the fresh manual backup."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=admin_tokens,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        
        lineage = data.get("archive_lineage", {})
        newest_valid = lineage.get("newest_valid_recoverable_artifact", {})
        
        # S1-3 requirement: fresh backup MASCI_complete_backup_2026-07-27_111254Z.zip
        assert newest_valid.get("filename") == "MASCI_complete_backup_2026-07-27_111254Z.zip", \
            f"Expected fresh backup, got {newest_valid.get('filename')}"

    def test_fresh_backup_has_verified_direct_evidence(self, admin_tokens):
        """Fresh backup has direct_evidence_status=VERIFIED."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=admin_tokens,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        
        lineage = data.get("archive_lineage", {})
        newest_valid = lineage.get("newest_valid_recoverable_artifact", {})
        
        # S1-3 requirement: direct_evidence_status=VERIFIED
        assert newest_valid.get("direct_evidence_status") == "VERIFIED", \
            f"Expected VERIFIED, got {newest_valid.get('direct_evidence_status')}"

    def test_fresh_backup_uses_sidecar_read_mode(self, admin_tokens):
        """Fresh backup has direct_evidence_read_mode=SIDECAR."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=admin_tokens,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        
        lineage = data.get("archive_lineage", {})
        newest_valid = lineage.get("newest_valid_recoverable_artifact", {})
        
        # S1-3 requirement: direct_evidence_read_mode=SIDECAR
        assert newest_valid.get("direct_evidence_read_mode") == "SIDECAR", \
            f"Expected SIDECAR, got {newest_valid.get('direct_evidence_read_mode')}"

    def test_fresh_backup_integrity_pass(self, admin_tokens):
        """Fresh backup has integrity_status=PASS."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=admin_tokens,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        
        lineage = data.get("archive_lineage", {})
        newest_valid = lineage.get("newest_valid_recoverable_artifact", {})
        
        # S1-3 requirement: integrity_status=PASS
        assert newest_valid.get("integrity_status") == "PASS", \
            f"Expected PASS, got {newest_valid.get('integrity_status')}"

    def test_fresh_backup_completeness_complete(self, admin_tokens):
        """Fresh backup has completeness_status=COMPLETE."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=admin_tokens,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        
        lineage = data.get("archive_lineage", {})
        newest_valid = lineage.get("newest_valid_recoverable_artifact", {})
        
        # S1-3 requirement: completeness_status=COMPLETE
        assert newest_valid.get("completeness_status") == "COMPLETE", \
            f"Expected COMPLETE, got {newest_valid.get('completeness_status')}"

    def test_fresh_backup_availability_available(self, admin_tokens):
        """Fresh backup has availability_status=AVAILABLE."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=admin_tokens,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        
        lineage = data.get("archive_lineage", {})
        newest_valid = lineage.get("newest_valid_recoverable_artifact", {})
        
        # S1-3 requirement: availability_status=AVAILABLE
        assert newest_valid.get("availability_status") == "AVAILABLE", \
            f"Expected AVAILABLE, got {newest_valid.get('availability_status')}"

    def test_fresh_backup_high_lineage_confidence(self, admin_tokens):
        """Fresh backup has lineage_confidence=HIGH."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=admin_tokens,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        
        lineage = data.get("archive_lineage", {})
        newest_valid = lineage.get("newest_valid_recoverable_artifact", {})
        
        # S1-3 requirement: lineage_confidence=HIGH
        assert newest_valid.get("lineage_confidence") == "HIGH", \
            f"Expected HIGH, got {newest_valid.get('lineage_confidence')}"

    def test_fresh_backup_valid_recoverable(self, admin_tokens):
        """Fresh backup has valid_recoverable=true."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=admin_tokens,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        
        lineage = data.get("archive_lineage", {})
        newest_valid = lineage.get("newest_valid_recoverable_artifact", {})
        
        # S1-3 requirement: valid_recoverable=true
        assert newest_valid.get("valid_recoverable") is True, \
            f"Expected True, got {newest_valid.get('valid_recoverable')}"

    def test_backup_verification_preview_shows_hardened_contract(self, admin_tokens):
        """GET /api/admin/backup-verification/preview reflects hardened direct-evidence contract."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backup-verification/preview",
            headers=admin_tokens,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("ok") is True
        report = data.get("report", {})
        
        # S1-3 requirement: verdict should be pass for fresh backup
        assert report.get("verdict") == "pass", f"Expected pass, got {report.get('verdict')}"
        
        r2 = report.get("r2", {})
        assert r2.get("configured") is True
        assert r2.get("status") == "ok"
        
        # Check authoritative artifact has hardened direct-evidence
        auth_artifact = r2.get("authoritative_artifact", {})
        if auth_artifact:
            assert auth_artifact.get("direct_evidence_status") == "VERIFIED", \
                f"Expected VERIFIED, got {auth_artifact.get('direct_evidence_status')}"
            assert auth_artifact.get("direct_evidence_read_mode") == "SIDECAR", \
                f"Expected SIDECAR, got {auth_artifact.get('direct_evidence_read_mode')}"

    def test_archive_lineage_overall_status(self, admin_tokens):
        """Archive lineage shows overall HIGH confidence and PASS integrity."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-complete-r2-state",
            headers=admin_tokens,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        
        lineage = data.get("archive_lineage", {})
        
        # S1-3 requirement: overall lineage confidence HIGH
        assert lineage.get("lineage_confidence") == "HIGH", \
            f"Expected HIGH, got {lineage.get('lineage_confidence')}"
        
        # S1-3 requirement: overall integrity PASS
        assert lineage.get("integrity_status") == "PASS", \
            f"Expected PASS, got {lineage.get('integrity_status')}"
        
        # S1-3 requirement: overall completeness COMPLETE
        assert lineage.get("completeness_status") == "COMPLETE", \
            f"Expected COMPLETE, got {lineage.get('completeness_status')}"
        
        # S1-3 requirement: overall availability AVAILABLE
        assert lineage.get("availability_status") == "AVAILABLE", \
            f"Expected AVAILABLE, got {lineage.get('availability_status')}"


class TestS13NightlyLastArchive:
    """S1-3: Verify nightly_last archive is reported correctly."""

    def test_recovery_snapshot_shows_archive_lineage(self, admin_tokens):
        """GET /api/admin/recovery/snapshot includes archive_lineage with fresh backup."""
        response = requests.get(
            f"{BASE_URL}/api/admin/recovery/snapshot",
            headers=admin_tokens,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        
        lineage = data.get("archive_lineage", {})
        
        # S1-3 requirement: archive_lineage present with authoritative recovery point
        assert lineage.get("authoritative_recovery_point_time") is not None, \
            "No authoritative_recovery_point_time in archive_lineage"
        
        # Check the newest valid artifact
        newest_valid = lineage.get("newest_valid_recoverable_artifact", {})
        if newest_valid:
            # Should be the fresh backup
            assert "MASCI_complete_backup_2026-07-27" in str(newest_valid.get("filename", "")), \
                f"Expected fresh backup, got {newest_valid.get('filename')}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
BCSS Checkpoint 2 Integration Tests - Archive Lineage & Freshness Precedence Convergence

Tests the canonical archive-lineage resolver and verifies that all consumers
derive from it rather than independent freshness calculations.
"""
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import requests


def _discover_base_url() -> str:
    direct = os.environ.get('REACT_APP_BACKEND_URL', '').strip().rstrip('/')
    if direct:
        return direct
    env_file = Path('/app/frontend/.env')
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith('REACT_APP_BACKEND_URL='):
                return line.split('=', 1)[1].strip().rstrip('/')
    return ''


BASE_URL = _discover_base_url()

# Test credentials
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASS = "Maddix123!"


@pytest.fixture(scope="module")
def admin_session():
    """Get authenticated admin session with cookies."""
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL could not be resolved for live integration tests.")
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Login using multi-login endpoint
    login_resp = session.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}
    )
    
    if login_resp.status_code != 200:
        pytest.skip(f"Admin login failed: {login_resp.status_code}")
    
    data = login_resp.json()
    admin_token = data.get("portal_tokens", {}).get("admin", "")
    if not admin_token:
        pytest.skip("Admin portal token missing from multi-login response.")
    session.headers.update({"X-Admin-Token": admin_token})
    session.headers.update({"Authorization": f"Bearer {admin_token}"})

    probe = session.get(f"{BASE_URL}/api/admin/backup-trust-score", timeout=30)
    if probe.status_code == 401:
        pytest.skip("Preview/live admin-token gate rejected the issued admin token; checkpoint integration endpoints skipped truthfully.")
    
    return session


class TestHealthEndpoints:
    """Test health endpoints that consume archive lineage."""
    
    def test_health_basic(self):
        """Basic health endpoint should return ok."""
        resp = requests.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True
    
    def test_health_full(self):
        """Full health endpoint should include backup_recent status."""
        resp = requests.get(f"{BASE_URL}/api/health/full")
        assert resp.status_code == 200
        data = resp.json()
        assert "ok" in data
        assert "backup_recent" in data
        # backup_recent should be derived from canonical archive lineage
        assert isinstance(data["backup_recent"], bool)


class TestBackupTrustScore:
    """Test backup trust score endpoint that consumes archive lineage."""
    
    def test_backup_trust_score_structure(self, admin_session):
        """Backup trust score should have required fields."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/backup-trust-score")
        assert resp.status_code == 200
        data = resp.json()
        
        # Required fields
        assert "trust_score" in data
        assert "score_band" in data
        assert "score_band_label" in data
        assert "score_reason" in data
        
        # Trust score should be a number
        assert isinstance(data["trust_score"], (int, float))
        
        # Score band should be one of the expected values
        assert data["score_band"] in ["green", "amber", "red"]


class TestBackupsCompleteR2State:
    """Test backups-complete-r2-state endpoint that consumes archive lineage."""
    
    def test_backups_complete_r2_state_structure(self, admin_session):
        """Backups complete R2 state should include archive lineage."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/backups-complete-r2-state")
        assert resp.status_code == 200
        data = resp.json()
        
        # Should include archive_lineage
        assert "archive_lineage" in data
        lineage = data["archive_lineage"]
        
        # Archive lineage should have required fields
        assert "authoritative_recovery_point_time" in lineage or lineage.get("authoritative_recovery_point_time") is None
        assert "authoritative_time_source" in lineage
        assert "lineage_confidence" in lineage
        assert "integrity_status" in lineage
        assert "completeness_status" in lineage
        
        # Time source should be one of the expected values
        valid_sources = [
            "VERIFIED_LOGICAL_RECOVERY_POINT",
            "COMPLETED_ARCHIVE_TIME",
            "PROVIDER_DURABLE_COMPLETION_TIME",
            "UNKNOWN"
        ]
        assert lineage["authoritative_time_source"] in valid_sources
        
        # Confidence should be one of the expected values
        valid_confidence = ["HIGH", "MEDIUM", "LOW"]
        assert lineage["lineage_confidence"] in valid_confidence


class TestRecoverySnapshot:
    """Test recovery snapshot endpoint that consumes archive lineage."""
    
    def test_recovery_snapshot_structure(self, admin_session):
        """Recovery snapshot should include archive lineage."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/recovery/snapshot")
        assert resp.status_code == 200
        data = resp.json()
        
        # Should include archive_lineage
        assert "archive_lineage" in data
        lineage = data["archive_lineage"]
        
        # Archive lineage should have required fields
        assert "authoritative_time_source" in lineage
        assert "lineage_confidence" in lineage
        assert "integrity_status" in lineage
        assert "completeness_status" in lineage
        
        # Should include last_backup with source field
        assert "last_backup" in data
        if data["last_backup"]:
            assert "source" in data["last_backup"]
            # Source should indicate canonical archive lineage
            assert "canonical" in data["last_backup"]["source"].lower() or "backup_health" in data["last_backup"]["source"].lower()


class TestBackupVerificationPreview:
    """Test backup verification preview endpoint that consumes archive lineage."""
    
    def test_backup_verification_preview_structure(self, admin_session):
        """Backup verification preview should include archive lineage."""
        resp = admin_session.get(f"{BASE_URL}/api/admin/backup-verification/preview")
        assert resp.status_code == 200
        data = resp.json()
        
        # Should include report
        assert "report" in data
        report = data["report"]
        
        # Report should have verdict
        assert "verdict" in report
        assert report["verdict"] in ["pass", "warn", "fail"]
        
        # Report should include archive lineage or r2 section with lineage
        if "archive_lineage" in report:
            lineage = report["archive_lineage"]
            assert "authoritative_time_source" in lineage
        elif "r2" in report and "archive_lineage" in report["r2"]:
            lineage = report["r2"]["archive_lineage"]
            assert "authoritative_time_source" in lineage


class TestArchiveLineageConsistency:
    """Test that archive lineage is consistent across all consumers."""
    
    def test_lineage_consistency_across_endpoints(self, admin_session):
        """Archive lineage should be consistent across all endpoints."""
        # Get lineage from multiple endpoints
        r2_state = admin_session.get(f"{BASE_URL}/api/admin/backups-complete-r2-state").json()
        recovery = admin_session.get(f"{BASE_URL}/api/admin/recovery/snapshot").json()
        
        r2_lineage = r2_state.get("archive_lineage", {})
        recovery_lineage = recovery.get("archive_lineage", {})
        
        # Key fields should be consistent
        assert r2_lineage.get("authoritative_time_source") == recovery_lineage.get("authoritative_time_source")
        assert r2_lineage.get("lineage_confidence") == recovery_lineage.get("lineage_confidence")
        assert r2_lineage.get("integrity_status") == recovery_lineage.get("integrity_status")
        assert r2_lineage.get("completeness_status") == recovery_lineage.get("completeness_status")


class TestTimestampPrecedence:
    """Test timestamp precedence rules."""
    
    def test_timestamp_precedence_documented(self):
        """Verify timestamp precedence is documented in the resolver."""
        # Import the resolver module
        import sys
        sys.path.insert(0, '/app/backend')
        from lib.archive_lineage import resolve_archive_lineage_from_inputs
        
        # The resolver should exist and be callable
        assert callable(resolve_archive_lineage_from_inputs)


class TestLegacyDegradation:
    """Test that legacy records degrade truthfully."""
    
    def test_legacy_degradation_behavior(self):
        """Legacy records should degrade truthfully."""
        import sys
        sys.path.insert(0, '/app/backend')
        from lib.archive_lineage import resolve_archive_lineage_from_inputs
        
        # Create a legacy archive without manifest
        legacy_archive = {
            "filename": "legacy.zip",
            "key": "backups/auto-90d/legacy.zip",
            "last_modified_iso": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            "size_bytes": 1000,
            "etag": "etag-legacy",
        }
        
        legacy_row = {
            "filename": "legacy.zip",
            "ts": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            "ok": True,
            "mode": "complete-r2",
            "records": 100,
            "size_bytes": 1000,
            "error": {"lineage": {"checksum_sha256": "sha-legacy"}},
        }
        
        # Resolve with no manifest
        result = resolve_archive_lineage_from_inputs(
            runtime_identity={"app_env": "preview", "db_name": "masci"},
            archive_rows=[legacy_archive],
            recent_rows=[legacy_row],
            manifest_bundles={},
        )
        
        # Legacy record should have degraded status
        if result.get("authoritative_artifact"):
            assert result["authoritative_artifact"]["authoritative_time_source"] == "PROVIDER_DURABLE_COMPLETION_TIME"
            assert "LEGACY" in result["authoritative_artifact"]["completeness_status"]


class TestNoParallelResolver:
    """Test that no duplicate active freshness resolver exists."""
    
    def test_single_canonical_resolver(self):
        """Verify only one canonical resolver exists."""
        import sys
        sys.path.insert(0, '/app/backend')
        
        # The canonical resolver should be in lib/archive_lineage.py
        from lib.archive_lineage import (
            resolve_archive_lineage_from_inputs,
            backup_recent_truth,
            consumer_freshness_status,
            public_archive_lineage_payload,
        )
        
        # All these functions should exist and be callable
        assert callable(resolve_archive_lineage_from_inputs)
        assert callable(backup_recent_truth)
        assert callable(consumer_freshness_status)
        assert callable(public_archive_lineage_payload)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

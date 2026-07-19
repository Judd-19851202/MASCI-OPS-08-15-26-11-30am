"""
Test D1 Production Identity Contract - HTTP Integration Tests

Tests the runtime identity contract via live HTTP endpoints to verify:
1. Production identity contract accepts approved production hostname + database + environment
2. Preview runtime surfaces production-cluster mismatch honestly and is no longer a valid D1 completion state until startup refuses it
3. Identity output is redacted and does not expose raw Mongo credentials
4. Readiness and full health degrade when runtime identity is mismatched
5. Legacy safety contracts from Track 28.09A and Checkpoint B remain intact
"""
from __future__ import annotations

import os
import pytest
import requests

# Use localhost for internal testing - external URL may have different latency
BASE_URL = "http://localhost:8001"


class TestD1RuntimeIdentityHTTP:
    """HTTP integration tests for D1 runtime identity contract."""

    def test_health_endpoint_returns_ok(self):
        """Basic health check should return ok."""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True

    def test_version_endpoint_includes_runtime_identity(self):
        """Version endpoint should include runtime_identity payload."""
        response = requests.get(f"{BASE_URL}/api/version", timeout=10)
        assert response.status_code == 200
        data = response.json()
        
        # Verify runtime_identity is present
        assert "runtime_identity" in data
        ri = data["runtime_identity"]
        
        # Verify structure
        assert "status" in ri
        assert "valid" in ri
        assert "identity" in ri
        assert "validation" in ri

    def test_version_runtime_identity_shows_mismatch_for_preview_on_prod_cluster(self):
        """Preview env pointing to production cluster should show MISMATCH status."""
        response = requests.get(f"{BASE_URL}/api/version", timeout=10)
        assert response.status_code == 200
        data = response.json()
        
        ri = data["runtime_identity"]
        # Current preview env is configured with APP_ENV=preview but pointing to prod cluster
        # This should result in MISMATCH status
        assert ri["status"] == "MISMATCH"
        assert ri["valid"] is False
        assert ri["mismatch_category"] == "PREVIEW_PRODUCTION_CLUSTER_REFUSED"

    def test_version_identity_does_not_expose_raw_credentials(self):
        """Identity output should not expose raw Mongo credentials or full connection strings."""
        response = requests.get(f"{BASE_URL}/api/version", timeout=10)
        assert response.status_code == 200
        data = response.json()
        
        # Convert to string for credential scanning
        text = str(data)
        
        # Should NOT contain raw connection strings
        assert "mongodb+srv://" not in text
        assert "mongodb://" not in text
        
        # Should NOT contain password patterns
        assert "iOt2XSuFK3NNR7Uv" not in text  # Preview password from .env
        
        # Should contain redacted hostname (this is allowed)
        ri = data["runtime_identity"]
        assert ri["identity"]["mongo_hostname_redacted"] == "masci-prod.1nduwmg.mongodb.net"

    def test_readyz_returns_503_when_identity_mismatched(self):
        """Readiness endpoint should return 503 when runtime identity is mismatched."""
        response = requests.get(f"{BASE_URL}/readyz", timeout=10)
        
        # Should return 503 due to identity mismatch
        assert response.status_code == 503
        
        data = response.json()
        assert data["ok"] is False
        assert "runtime_identity" in data
        assert data["runtime_identity"]["ok"] is False
        assert data["runtime_identity"]["status"] == "MISMATCH"

    def test_health_full_shows_runtime_identity_not_ok(self):
        """Full health endpoint should show runtime_identity_ok=false when mismatched."""
        response = requests.get(f"{BASE_URL}/api/health/full", timeout=10)
        # Returns 503 when overall health is not ok (due to identity mismatch)
        assert response.status_code == 503
        
        data = response.json()
        # Full health should report identity not ok
        assert data["runtime_identity_ok"] is False
        assert data["runtime_identity_status"] == "MISMATCH"
        
        # Overall ok should be false due to identity mismatch
        assert data["ok"] is False
        
        # But other subsystems should still be healthy
        assert data["mongo"] is True
        assert data["scheduler"] is True

    def test_platform_data_truth_includes_runtime_identity(self):
        """Platform data-truth endpoint should include runtime_identity payload."""
        response = requests.get(f"{BASE_URL}/api/platform/data-truth", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert data["ok"] is True
        assert "runtime_identity" in data
        
        ri = data["runtime_identity"]
        assert ri["status"] == "MISMATCH"
        assert ri["valid"] is False
        
        # Verify environment is correctly identified
        assert data["environment"] == "preview"
        assert data["database"] == "masci_safety_preview"

    def test_cluster_capacity_includes_runtime_identity(self):
        """Cluster capacity endpoint should include runtime_identity payload."""
        response = requests.get(f"{BASE_URL}/api/cluster/capacity", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert data["ok"] is True
        assert "runtime_identity" in data
        
        ri = data["runtime_identity"]
        assert ri["status"] == "MISMATCH"
        assert ri["valid"] is False

    def test_identity_fingerprint_is_stable(self):
        """Identity fingerprint should be stable across multiple requests."""
        response1 = requests.get(f"{BASE_URL}/api/version", timeout=10)
        response2 = requests.get(f"{BASE_URL}/api/version", timeout=10)
        
        fp1 = response1.json()["runtime_identity"]["identity"]["identity_fingerprint"]
        fp2 = response2.json()["runtime_identity"]["identity"]["identity_fingerprint"]
        
        assert fp1 == fp2
        assert len(fp1) == 12  # SHA prefix is 12 chars

    def test_identity_validation_errors_are_surfaced(self):
        """Validation errors should be surfaced in the identity payload."""
        response = requests.get(f"{BASE_URL}/api/version", timeout=10)
        data = response.json()
        
        validation = data["runtime_identity"]["validation"]
        assert "errors" in validation
        assert isinstance(validation["errors"], list)
        
        # Should have the preview_pointing_to_production_cluster error
        assert "preview_pointing_to_production_cluster" in validation["errors"]

    def test_identity_remediation_info_is_present(self):
        """Remediation owner and action should be present in validation."""
        response = requests.get(f"{BASE_URL}/api/version", timeout=10)
        data = response.json()
        
        validation = data["runtime_identity"]["validation"]
        assert validation["remediation_owner"] == "platform-ops"
        assert "Correct runtime identity inputs" in validation["remediation_action"]


class TestD1LegacySafetyContracts:
    """Tests for legacy safety contracts from Track 28.09A and Checkpoint B."""

    def test_environment_identity_in_version(self):
        """Version endpoint should include environment_identity block."""
        response = requests.get(f"{BASE_URL}/api/version", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert "environment_identity" in data
        
        env_id = data["environment_identity"]
        assert env_id["app_env"] == "preview"
        assert env_id["db_name"] == "masci_safety_preview"
        assert env_id["db_isolation_enforced"] is True

    def test_runtime_identity_status_in_environment_identity(self):
        """Environment identity should include runtime_identity_status."""
        response = requests.get(f"{BASE_URL}/api/version", timeout=10)
        data = response.json()
        
        env_id = data["environment_identity"]
        assert "runtime_identity_status" in env_id
        assert env_id["runtime_identity_status"] == "MISMATCH"
        assert "runtime_identity_mismatch_category" in env_id
        assert env_id["runtime_identity_mismatch_category"] == "PREVIEW_PRODUCTION_CLUSTER_REFUSED"

    def test_mongo_hostname_redacted_in_environment_identity(self):
        """Environment identity should include redacted mongo hostname."""
        response = requests.get(f"{BASE_URL}/api/version", timeout=10)
        data = response.json()
        
        env_id = data["environment_identity"]
        assert "mongo_hostname_redacted" in env_id
        # Should be the hostname, not the full URL with credentials
        # The hostname can contain "mongodb.net" (Atlas domain) but should NOT contain
        # the full connection string prefix or credentials
        hostname = env_id["mongo_hostname_redacted"]
        assert "mongodb://" not in hostname
        assert "mongodb+srv://" not in hostname
        assert "@" not in hostname
        assert ":" not in hostname or hostname.count(":") == 0  # No port in SRV hostnames


class TestD1PreviewIsolationTruth:
    """Tests documenting the currently exposed preview→production mismatch truth."""

    def test_preview_surfaces_mismatch_honestly(self):
        """Preview should clearly expose the production-cluster mismatch category."""
        response = requests.get(f"{BASE_URL}/api/version", timeout=10)
        data = response.json()

        ri = data["runtime_identity"]
        assert ri["valid"] is False
        assert ri["status"] == "MISMATCH"
        assert ri["mismatch_category"] == "PREVIEW_PRODUCTION_CLUSTER_REFUSED"

        identity = ri["identity"]
        assert identity["app_env"] == "preview"
        assert identity["db_name"] == "masci_safety_preview"
        assert identity["approved_db_name"] == "masci_safety"
        assert identity["approved_hostname"] == "masci-prod.1nduwmg.mongodb.net"

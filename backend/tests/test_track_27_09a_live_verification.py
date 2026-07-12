"""Track 27.09A · Live preview backend verification.

Tests the two repair truths against the running preview backend:
1. Inventory prefix normalization: backups/ normalizes to backups
2. Integrity-check MANIFEST metadata truthfulness
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token via multi-login."""
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not set")
    resp = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    data = resp.json()
    token = data.get("portal_tokens", {}).get("admin") or data.get("token")
    assert token, "No admin token in response"
    return token


class TestInventoryPrefixNormalization:
    """Bug fix: prefix=backups/ must return same population as prefix=backups."""

    def test_backups_and_backups_slash_return_same_count(self, admin_token):
        """Both prefix=backups and prefix=backups/ must return identical total_matching."""
        headers = {"X-Admin-Token": admin_token}
        
        resp_no_slash = requests.get(
            f"{BASE_URL}/api/admin/r2/lifecycle/inventory",
            params={"prefix": "backups", "limit": 1},
            headers=headers,
            timeout=30,
        )
        assert resp_no_slash.status_code == 200, f"backups failed: {resp_no_slash.text}"
        
        resp_with_slash = requests.get(
            f"{BASE_URL}/api/admin/r2/lifecycle/inventory",
            params={"prefix": "backups/", "limit": 1},
            headers=headers,
            timeout=30,
        )
        assert resp_with_slash.status_code == 200, f"backups/ failed: {resp_with_slash.text}"
        
        count_no_slash = resp_no_slash.json().get("total_matching", 0)
        count_with_slash = resp_with_slash.json().get("total_matching", 0)
        
        assert count_no_slash == count_with_slash, (
            f"Prefix normalization failed: backups={count_no_slash}, "
            f"backups/={count_with_slash}"
        )
        assert count_no_slash > 0, "Expected at least some backup archives"

    def test_nested_path_filter_returns_subset(self, admin_token):
        """Deeper prefixes like backups/auto-90d/ should return a scoped subset."""
        headers = {"X-Admin-Token": admin_token}
        
        resp_all = requests.get(
            f"{BASE_URL}/api/admin/r2/lifecycle/inventory",
            params={"prefix": "backups", "limit": 1},
            headers=headers,
            timeout=30,
        )
        assert resp_all.status_code == 200
        
        resp_nested = requests.get(
            f"{BASE_URL}/api/admin/r2/lifecycle/inventory",
            params={"prefix": "backups/auto-90d/", "limit": 1},
            headers=headers,
            timeout=30,
        )
        assert resp_nested.status_code == 200
        
        count_all = resp_all.json().get("total_matching", 0)
        count_nested = resp_nested.json().get("total_matching", 0)
        
        # Nested should be a subset (less than or equal to all)
        assert count_nested <= count_all, (
            f"Nested path should be subset: all={count_all}, nested={count_nested}"
        )


class TestIntegrityCheckManifestTruthfulness:
    """Bug fix: integrity-check must surface truthful R2 MANIFEST metadata."""

    def test_integrity_check_returns_r2_manifest_evidence(self, admin_token):
        """Integrity-check should prefer R2 MANIFEST and return truthful metadata."""
        headers = {"X-Admin-Token": admin_token}
        
        resp = requests.get(
            f"{BASE_URL}/api/admin/backups/integrity-check",
            headers=headers,
            timeout=60,
        )
        assert resp.status_code == 200, f"integrity-check failed: {resp.text}"
        
        data = resp.json()
        
        # Must have non-empty truthful metadata fields
        assert data.get("last_backup_filename"), "last_backup_filename should be non-empty"
        assert data.get("last_backup_object_key"), "last_backup_object_key should be non-empty"
        assert data.get("captured_collections"), "captured_collections should be non-empty"
        assert data.get("document_count") is not None, "document_count should be present"
        assert data.get("archive_size_bytes") is not None, "archive_size_bytes should be present"
        
        # Evidence source should indicate R2 MANIFEST
        evidence_source = data.get("evidence_source", "")
        assert evidence_source.startswith("r2:"), (
            f"Expected evidence_source to start with 'r2:', got: {evidence_source}"
        )
        assert "MANIFEST" in evidence_source or "manifest" in evidence_source, (
            f"Expected MANIFEST in evidence_source, got: {evidence_source}"
        )

    def test_integrity_check_has_collection_counts(self, admin_token):
        """Integrity-check should return per-collection counts from MANIFEST."""
        headers = {"X-Admin-Token": admin_token}
        
        resp = requests.get(
            f"{BASE_URL}/api/admin/backups/integrity-check",
            headers=headers,
            timeout=60,
        )
        assert resp.status_code == 200
        
        data = resp.json()
        collection_counts = data.get("collection_counts")
        
        assert collection_counts is not None, "collection_counts should be present"
        assert isinstance(collection_counts, dict), "collection_counts should be a dict"
        assert len(collection_counts) > 0, "collection_counts should have entries"

    def test_integrity_check_returns_integrity_result(self, admin_token):
        """Integrity-check should return a valid integrity_result."""
        headers = {"X-Admin-Token": admin_token}
        
        resp = requests.get(
            f"{BASE_URL}/api/admin/backups/integrity-check",
            headers=headers,
            timeout=60,
        )
        assert resp.status_code == 200
        
        data = resp.json()
        integrity_result = data.get("integrity_result")
        
        assert integrity_result in ("PASS", "FAIL", "UNKNOWN"), (
            f"integrity_result should be PASS/FAIL/UNKNOWN, got: {integrity_result}"
        )


class TestRegressionSafety:
    """Verify no destructive storage behavior in the tested flow."""

    def test_inventory_endpoint_is_read_only(self, admin_token):
        """Inventory endpoint should not modify any data."""
        headers = {"X-Admin-Token": admin_token}
        
        # Call inventory twice and verify counts are stable
        resp1 = requests.get(
            f"{BASE_URL}/api/admin/r2/lifecycle/inventory",
            params={"prefix": "backups", "limit": 1},
            headers=headers,
            timeout=30,
        )
        assert resp1.status_code == 200
        count1 = resp1.json().get("total_matching", 0)
        
        resp2 = requests.get(
            f"{BASE_URL}/api/admin/r2/lifecycle/inventory",
            params={"prefix": "backups", "limit": 1},
            headers=headers,
            timeout=30,
        )
        assert resp2.status_code == 200
        count2 = resp2.json().get("total_matching", 0)
        
        assert count1 == count2, "Inventory count should be stable (read-only)"

    def test_integrity_check_is_read_only(self, admin_token):
        """Integrity-check endpoint should not modify any data."""
        headers = {"X-Admin-Token": admin_token}
        
        # Call integrity-check twice and verify key fields are stable
        resp1 = requests.get(
            f"{BASE_URL}/api/admin/backups/integrity-check",
            headers=headers,
            timeout=60,
        )
        assert resp1.status_code == 200
        data1 = resp1.json()
        
        resp2 = requests.get(
            f"{BASE_URL}/api/admin/backups/integrity-check",
            headers=headers,
            timeout=60,
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        
        # Key fields should be identical
        assert data1.get("last_backup_filename") == data2.get("last_backup_filename")
        assert data1.get("last_backup_object_key") == data2.get("last_backup_object_key")
        assert data1.get("document_count") == data2.get("document_count")

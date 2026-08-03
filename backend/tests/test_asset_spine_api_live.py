"""
tests/test_asset_spine_api_live.py · Asset Spine API Live Verification

Tests the bounded Asset Spine contract for dot_expiration and calibration_expiration
fields via the live preview API with proper dual-token authentication.

Run with:
    cd /app/backend && python -m pytest tests/test_asset_spine_api_live.py -v --tb=short
"""
from __future__ import annotations

import os
import time
import uuid
import pytest
import requests

# Get base URL from environment
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback for local testing
    BASE_URL = "https://masci-audit-hub.preview.emergentagent.com"

# Test credentials from test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


def _retry_request(method, url, max_retries=3, **kwargs):
    """Retry request with exponential backoff for transient failures"""
    kwargs.setdefault("timeout", 60)
    for attempt in range(max_retries):
        try:
            response = method(url, **kwargs)
            if response.status_code != 502:  # Not a gateway error
                return response
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            if attempt == max_retries - 1:
                raise
        time.sleep(2 ** attempt)  # Exponential backoff
    return response


class TestAssetSpineAPILive:
    """Live API tests for Asset Spine dot_expiration and calibration_expiration fields"""

    @pytest.fixture(scope="class")
    def auth_tokens(self):
        """Get dual authentication tokens (X-Admin-Token and X-Directory-Token)"""
        # Multi-login to get both tokens with retry
        response = _retry_request(
            requests.post,
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Multi-login failed: {response.status_code} - {response.text}")
        
        data = response.json()
        
        # Extract tokens
        session_token = data.get("session_token")
        portal_tokens = data.get("portal_tokens", {})
        admin_token = portal_tokens.get("admin")
        
        if not session_token or not admin_token:
            pytest.skip(f"Missing tokens in response: session_token={bool(session_token)}, admin_token={bool(admin_token)}")
        
        return {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }

    @pytest.fixture(scope="class")
    def test_asset_number(self):
        """Generate unique asset number for test isolation"""
        return f"TEST-SPINE-{uuid.uuid4().hex[:8].upper()}"

    def test_01_auth_tokens_obtained(self, auth_tokens):
        """Verify dual-token authentication works"""
        assert "X-Admin-Token" in auth_tokens
        assert "X-Directory-Token" in auth_tokens
        assert auth_tokens["X-Admin-Token"] is not None
        assert auth_tokens["X-Directory-Token"] is not None
        print(f"Auth tokens obtained successfully")

    def test_02_create_asset_with_expiration_fields(self, auth_tokens, test_asset_number):
        """Create asset with dot_expiration and calibration_expiration, verify they persist"""
        create_payload = {
            "asset_number": test_asset_number,
            "asset_name": "Test Asset for Expiration Fields",
            "asset_type": "Truck",
            "asset_category": "Heavy",
            "dot_expiration": "2026-12-31",
            "calibration_expiration": "2027-01-15"
        }
        
        response = _retry_request(
            requests.post,
            f"{BASE_URL}/api/asset-spine/assets",
            json=create_payload,
            headers=auth_tokens
        )
        
        assert response.status_code == 200, f"Create failed: {response.status_code} - {response.text}"
        
        data = response.json()
        
        # Verify expiration fields in create response
        assert data.get("dot_expiration") == "2026-12-31", f"dot_expiration mismatch: {data.get('dot_expiration')}"
        assert data.get("calibration_expiration") == "2027-01-15", f"calibration_expiration mismatch: {data.get('calibration_expiration')}"
        assert data.get("asset_number") == test_asset_number
        assert data.get("asset_id") is not None
        
        # Store asset_id for subsequent tests
        self.__class__.created_asset_id = data.get("asset_id")
        print(f"Created asset {test_asset_number} with id={self.created_asset_id}")
        print(f"  dot_expiration: {data.get('dot_expiration')}")
        print(f"  calibration_expiration: {data.get('calibration_expiration')}")

    def test_03_read_asset_returns_expiration_fields(self, auth_tokens):
        """GET asset returns persisted dot_expiration and calibration_expiration unchanged"""
        asset_id = getattr(self.__class__, "created_asset_id", None)
        if not asset_id:
            pytest.skip("No asset created in previous test")
        
        response = _retry_request(
            requests.get,
            f"{BASE_URL}/api/asset-spine/assets/{asset_id}",
            headers=auth_tokens
        )
        
        assert response.status_code == 200, f"GET failed: {response.status_code} - {response.text}"
        
        data = response.json()
        
        # Verify expiration fields persisted correctly
        assert data.get("dot_expiration") == "2026-12-31", f"dot_expiration mismatch on read: {data.get('dot_expiration')}"
        assert data.get("calibration_expiration") == "2027-01-15", f"calibration_expiration mismatch on read: {data.get('calibration_expiration')}"
        print(f"Read asset {asset_id} - expiration fields verified")

    def test_04_update_asset_expiration_fields(self, auth_tokens):
        """PATCH asset with new expiration values, verify they persist"""
        asset_id = getattr(self.__class__, "created_asset_id", None)
        if not asset_id:
            pytest.skip("No asset created in previous test")
        
        update_payload = {
            "dot_expiration": "2027-12-31",
            "calibration_expiration": "2028-01-15"
        }
        
        response = _retry_request(
            requests.patch,
            f"{BASE_URL}/api/asset-spine/assets/{asset_id}",
            json=update_payload,
            headers=auth_tokens
        )
        
        assert response.status_code == 200, f"PATCH failed: {response.status_code} - {response.text}"
        
        data = response.json()
        
        # Verify updated expiration fields in response
        assert data.get("dot_expiration") == "2027-12-31", f"dot_expiration mismatch after update: {data.get('dot_expiration')}"
        assert data.get("calibration_expiration") == "2028-01-15", f"calibration_expiration mismatch after update: {data.get('calibration_expiration')}"
        print(f"Updated asset {asset_id} - new expiration fields verified")

    def test_05_read_after_update_returns_updated_fields(self, auth_tokens):
        """GET after update returns the updated expiration values"""
        asset_id = getattr(self.__class__, "created_asset_id", None)
        if not asset_id:
            pytest.skip("No asset created in previous test")
        
        response = _retry_request(
            requests.get,
            f"{BASE_URL}/api/asset-spine/assets/{asset_id}",
            headers=auth_tokens
        )
        
        assert response.status_code == 200, f"GET after update failed: {response.status_code} - {response.text}"
        
        data = response.json()
        
        # Verify updated expiration fields persisted
        assert data.get("dot_expiration") == "2027-12-31", f"dot_expiration mismatch on read after update: {data.get('dot_expiration')}"
        assert data.get("calibration_expiration") == "2028-01-15", f"calibration_expiration mismatch on read after update: {data.get('calibration_expiration')}"
        print(f"Read after update verified - expiration fields correctly persisted")

    def test_06_duplicate_asset_number_rejected(self, auth_tokens, test_asset_number):
        """Verify duplicate asset_number prevention still works"""
        create_payload = {
            "asset_number": test_asset_number,  # Same as created asset
            "asset_name": "Duplicate Test",
            "asset_type": "Truck"
        }
        
        response = _retry_request(
            requests.post,
            f"{BASE_URL}/api/asset-spine/assets",
            json=create_payload,
            headers=auth_tokens
        )
        
        # Should return 409 Conflict for duplicate
        assert response.status_code == 409, f"Expected 409 for duplicate, got: {response.status_code} - {response.text}"
        print(f"Duplicate asset_number correctly rejected with 409")

    def test_07_auth_enforced_on_create(self):
        """Verify auth is enforced on create endpoint (no tokens)"""
        create_payload = {
            "asset_number": f"TEST-NOAUTH-{uuid.uuid4().hex[:8]}",
            "asset_name": "No Auth Test",
            "asset_type": "Truck"
        }
        
        response = _retry_request(
            requests.post,
            f"{BASE_URL}/api/asset-spine/assets",
            json=create_payload
        )
        
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got: {response.status_code}"
        print(f"Auth enforced on create - returned {response.status_code}")

    def test_08_auth_enforced_on_update(self):
        """Verify auth is enforced on update endpoint (no tokens)"""
        asset_id = getattr(self.__class__, "created_asset_id", None)
        if not asset_id:
            pytest.skip("No asset created in previous test")
        
        update_payload = {"asset_name": "Unauthorized Update"}
        
        response = _retry_request(
            requests.patch,
            f"{BASE_URL}/api/asset-spine/assets/{asset_id}",
            json=update_payload
        )
        
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got: {response.status_code}"
        print(f"Auth enforced on update - returned {response.status_code}")

    def test_09_partial_auth_rejected_on_create(self, auth_tokens):
        """Verify partial auth (only admin token) is rejected on create"""
        create_payload = {
            "asset_number": f"TEST-PARTIAL-{uuid.uuid4().hex[:8]}",
            "asset_name": "Partial Auth Test",
            "asset_type": "Truck"
        }
        
        # Only send X-Admin-Token, not X-Directory-Token
        partial_headers = {"X-Admin-Token": auth_tokens["X-Admin-Token"]}
        
        response = _retry_request(
            requests.post,
            f"{BASE_URL}/api/asset-spine/assets",
            json=create_payload,
            headers=partial_headers
        )
        
        # Should return 401 or 403 with partial auth
        assert response.status_code in [401, 403], f"Expected 401/403 with partial auth, got: {response.status_code}"
        print(f"Partial auth rejected on create - returned {response.status_code}")

    def test_10_cleanup_test_asset(self, auth_tokens):
        """Cleanup: Delete the test asset from preview DB"""
        asset_id = getattr(self.__class__, "created_asset_id", None)
        if not asset_id:
            pytest.skip("No asset to cleanup")
        
        # Retire the asset (soft delete)
        response = _retry_request(
            requests.post,
            f"{BASE_URL}/api/asset-spine/assets/{asset_id}/retire",
            json={"reason": "Test cleanup"},
            headers=auth_tokens
        )
        
        if response.status_code == 200:
            print(f"Test asset {asset_id} retired for cleanup")
        else:
            print(f"Warning: Could not retire test asset: {response.status_code}")
        
        # Note: Full deletion would require direct DB access
        # For preview, retiring is sufficient cleanup


class TestAssetSpineReadEndpoints:
    """Test read endpoints work with any portal auth"""

    @pytest.fixture(scope="class")
    def auth_tokens(self):
        """Get dual authentication tokens"""
        response = _retry_request(
            requests.post,
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Multi-login failed: {response.status_code}")
        
        data = response.json()
        session_token = data.get("session_token")
        portal_tokens = data.get("portal_tokens", {})
        admin_token = portal_tokens.get("admin")
        
        return {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }

    def test_list_assets_works(self, auth_tokens):
        """GET /api/asset-spine/assets returns list"""
        response = _retry_request(
            requests.get,
            f"{BASE_URL}/api/asset-spine/assets",
            headers=auth_tokens,
            params={"limit": 5}
        )
        
        assert response.status_code == 200, f"List failed: {response.status_code}"
        data = response.json()
        assert "items" in data
        assert "count" in data
        print(f"List assets returned {data.get('count')} items")

    def test_health_endpoint_works(self, auth_tokens):
        """GET /api/asset-spine/health returns health data"""
        response = _retry_request(
            requests.get,
            f"{BASE_URL}/api/asset-spine/health",
            headers=auth_tokens
        )
        
        assert response.status_code == 200, f"Health failed: {response.status_code}"
        data = response.json()
        assert "total_assets" in data
        assert "active_assets" in data
        print(f"Health: total={data.get('total_assets')}, active={data.get('active_assets')}")

    def test_taxonomy_endpoint_works(self, auth_tokens):
        """GET /api/asset-spine/taxonomy returns taxonomy data"""
        response = _retry_request(
            requests.get,
            f"{BASE_URL}/api/asset-spine/taxonomy",
            headers=auth_tokens
        )
        
        assert response.status_code == 200, f"Taxonomy failed: {response.status_code}"
        data = response.json()
        assert "asset_classes" in data
        assert "asset_types_by_class" in data
        print(f"Taxonomy: {len(data.get('asset_classes', []))} classes")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

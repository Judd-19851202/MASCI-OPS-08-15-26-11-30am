"""
tests/test_asset_spine_inspection_expiration.py · BCSS R2/P2/W3/F3D-1 Slice 2

Bounded verification for the single-field repair: inspection_expiration
canonical field consistency in Asset Spine backend contract.

Tests:
1. Create asset with inspection_expiration → persists and returns unchanged
2. GET asset returns persisted inspection_expiration unchanged
3. PATCH asset with new inspection_expiration → persists and returns unchanged
4. GET after PATCH returns updated inspection_expiration unchanged
5. Duplicate asset_number prevention still works
6. Auth enforcement on create/update still works

Run with:
    cd /app/backend && python -m pytest tests/test_asset_spine_inspection_expiration.py -v --tb=short
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
    BASE_URL = "https://backup-forensics.preview.emergentagent.com"

# Test credentials from test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


def _retry_request(method, url, max_retries=3, **kwargs):
    """Retry request with exponential backoff for transient failures"""
    kwargs.setdefault("timeout", 60)
    for attempt in range(max_retries):
        try:
            response = method(url, **kwargs)
            if response.status_code != 502:
                return response
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            if attempt == max_retries - 1:
                raise
        time.sleep(2 ** attempt)
    return response


class TestInspectionExpirationContract:
    """
    Bounded verification for inspection_expiration field in Asset Spine.
    
    This test class verifies the single-field repair scope:
    - inspection_expiration accepted in create payload
    - inspection_expiration persisted to MongoDB equipment_master
    - inspection_expiration returned unchanged in create response
    - GET returns persisted inspection_expiration
    - PATCH accepts new inspection_expiration value
    - GET after PATCH returns updated inspection_expiration
    """

    @pytest.fixture(scope="class")
    def auth_tokens(self):
        """Get dual authentication tokens (X-Admin-Token and X-Directory-Token)"""
        response = _retry_request(
            requests.post,
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Multi-login failed: {response.status_code} - {response.text}")
        
        data = response.json()
        session_token = data.get("session_token")
        portal_tokens = data.get("portal_tokens", {})
        admin_token = portal_tokens.get("admin")
        
        if not session_token or not admin_token:
            pytest.skip(f"Missing tokens: session_token={bool(session_token)}, admin_token={bool(admin_token)}")
        
        return {
            "X-Admin-Token": admin_token,
            "X-Directory-Token": session_token
        }

    @pytest.fixture(scope="class")
    def test_asset_number(self):
        """Generate unique asset number for test isolation"""
        return f"TEST-3D1-INSP-{uuid.uuid4().hex[:8].upper()}"

    # -------------------------------------------------------------------------
    # Core inspection_expiration contract tests
    # -------------------------------------------------------------------------

    def test_01_create_asset_with_inspection_expiration(self, auth_tokens, test_asset_number):
        """
        Create asset with inspection_expiration → persists and returns unchanged.
        
        Verifies:
        - POST /api/asset-spine/assets accepts inspection_expiration in payload
        - Response includes inspection_expiration with exact value sent
        """
        create_payload = {
            "asset_number": test_asset_number,
            "asset_name": "Test Asset for inspection_expiration",
            "asset_type": "Truck",
            "asset_category": "Heavy",
            "inspection_expiration": "2026-11-30"
        }
        
        response = _retry_request(
            requests.post,
            f"{BASE_URL}/api/asset-spine/assets",
            json=create_payload,
            headers=auth_tokens
        )
        
        assert response.status_code == 200, f"Create failed: {response.status_code} - {response.text}"
        
        data = response.json()
        
        # Core assertion: inspection_expiration returned unchanged
        assert data.get("inspection_expiration") == "2026-11-30", \
            f"inspection_expiration mismatch in create response: expected '2026-11-30', got '{data.get('inspection_expiration')}'"
        
        assert data.get("asset_number") == test_asset_number
        assert data.get("asset_id") is not None
        
        # Store asset_id for subsequent tests
        self.__class__.created_asset_id = data.get("asset_id")
        print(f"PASS: Created asset {test_asset_number} with inspection_expiration='2026-11-30'")

    def test_02_read_asset_returns_inspection_expiration(self, auth_tokens):
        """
        GET asset returns persisted inspection_expiration unchanged.
        
        Verifies:
        - GET /api/asset-spine/assets/{id} returns inspection_expiration
        - Value matches what was sent in create
        """
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
        
        # Core assertion: inspection_expiration persisted correctly
        assert data.get("inspection_expiration") == "2026-11-30", \
            f"inspection_expiration mismatch on read: expected '2026-11-30', got '{data.get('inspection_expiration')}'"
        
        print(f"PASS: GET asset {asset_id} returned inspection_expiration='2026-11-30'")

    def test_03_update_asset_inspection_expiration(self, auth_tokens):
        """
        PATCH asset with new inspection_expiration → persists and returns unchanged.
        
        Verifies:
        - PATCH /api/asset-spine/assets/{id} accepts inspection_expiration
        - Response includes updated inspection_expiration with exact value sent
        """
        asset_id = getattr(self.__class__, "created_asset_id", None)
        if not asset_id:
            pytest.skip("No asset created in previous test")
        
        update_payload = {
            "inspection_expiration": "2027-11-30"
        }
        
        response = _retry_request(
            requests.patch,
            f"{BASE_URL}/api/asset-spine/assets/{asset_id}",
            json=update_payload,
            headers=auth_tokens
        )
        
        assert response.status_code == 200, f"PATCH failed: {response.status_code} - {response.text}"
        
        data = response.json()
        
        # Core assertion: inspection_expiration updated correctly
        assert data.get("inspection_expiration") == "2027-11-30", \
            f"inspection_expiration mismatch after update: expected '2027-11-30', got '{data.get('inspection_expiration')}'"
        
        print(f"PASS: PATCH asset {asset_id} updated inspection_expiration='2027-11-30'")

    def test_04_read_after_update_returns_updated_inspection_expiration(self, auth_tokens):
        """
        GET after PATCH returns updated inspection_expiration unchanged.
        
        Verifies:
        - Updated inspection_expiration persisted to database
        - GET returns the new value
        """
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
        
        # Core assertion: updated inspection_expiration persisted
        assert data.get("inspection_expiration") == "2027-11-30", \
            f"inspection_expiration mismatch on read after update: expected '2027-11-30', got '{data.get('inspection_expiration')}'"
        
        print(f"PASS: GET after update returned inspection_expiration='2027-11-30'")

    # -------------------------------------------------------------------------
    # Regression tests: existing behavior unchanged
    # -------------------------------------------------------------------------

    def test_05_duplicate_asset_number_rejected(self, auth_tokens, test_asset_number):
        """
        Verify duplicate asset_number prevention still works.
        
        Regression test: this repair should not break existing duplicate prevention.
        """
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
        
        assert response.status_code == 409, \
            f"Expected 409 for duplicate asset_number, got: {response.status_code} - {response.text}"
        
        print(f"PASS: Duplicate asset_number correctly rejected with 409")

    def test_06_auth_enforced_on_create(self):
        """
        Verify auth is enforced on create endpoint (no tokens).
        
        Regression test: this repair should not break auth enforcement.
        """
        create_payload = {
            "asset_number": f"TEST-NOAUTH-{uuid.uuid4().hex[:8]}",
            "asset_name": "No Auth Test",
            "asset_type": "Truck",
            "inspection_expiration": "2026-12-31"
        }
        
        response = _retry_request(
            requests.post,
            f"{BASE_URL}/api/asset-spine/assets",
            json=create_payload
        )
        
        assert response.status_code in [401, 403], \
            f"Expected 401/403 without auth, got: {response.status_code}"
        
        print(f"PASS: Auth enforced on create - returned {response.status_code}")

    def test_07_auth_enforced_on_update(self):
        """
        Verify auth is enforced on update endpoint (no tokens).
        
        Regression test: this repair should not break auth enforcement.
        """
        asset_id = getattr(self.__class__, "created_asset_id", None)
        if not asset_id:
            pytest.skip("No asset created in previous test")
        
        update_payload = {"inspection_expiration": "2028-01-01"}
        
        response = _retry_request(
            requests.patch,
            f"{BASE_URL}/api/asset-spine/assets/{asset_id}",
            json=update_payload
        )
        
        assert response.status_code in [401, 403], \
            f"Expected 401/403 without auth, got: {response.status_code}"
        
        print(f"PASS: Auth enforced on update - returned {response.status_code}")

    def test_08_partial_auth_rejected(self, auth_tokens):
        """
        Verify partial auth (only admin token) is rejected.
        
        Regression test: dual-token requirement still enforced.
        """
        create_payload = {
            "asset_number": f"TEST-PARTIAL-{uuid.uuid4().hex[:8]}",
            "asset_name": "Partial Auth Test",
            "asset_type": "Truck",
            "inspection_expiration": "2026-12-31"
        }
        
        # Only send X-Admin-Token, not X-Directory-Token
        partial_headers = {"X-Admin-Token": auth_tokens["X-Admin-Token"]}
        
        response = _retry_request(
            requests.post,
            f"{BASE_URL}/api/asset-spine/assets",
            json=create_payload,
            headers=partial_headers
        )
        
        assert response.status_code in [401, 403], \
            f"Expected 401/403 with partial auth, got: {response.status_code}"
        
        print(f"PASS: Partial auth rejected - returned {response.status_code}")

    def test_09_cleanup_test_asset(self, auth_tokens):
        """
        Cleanup: Retire the test asset from preview DB.
        """
        asset_id = getattr(self.__class__, "created_asset_id", None)
        if not asset_id:
            pytest.skip("No asset to cleanup")
        
        response = _retry_request(
            requests.post,
            f"{BASE_URL}/api/asset-spine/assets/{asset_id}/retire",
            json={"reason": "Test cleanup - inspection_expiration verification"},
            headers=auth_tokens
        )
        
        if response.status_code == 200:
            print(f"PASS: Test asset {asset_id} retired for cleanup")
        else:
            print(f"WARNING: Could not retire test asset: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

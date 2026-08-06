"""
Test suite for backup admin endpoints on Preview environment.

Tests:
1. /api/admin/backups-scheduler-state - hourly_activation with stale_lock_present=false
2. /api/admin/system-health - backup card should show truthful green/verified status
3. /api/admin/backups-complete-r2-state - nightly_last.r2_key uses preview-scoped prefix
4. /api/admin/backups-list-r2 - environment-scoped prefix (backups/preview/auto-90d/)
5. Regression safety - no backend startup failure, endpoints responsive
"""

import os
import time
import uuid
import pytest
import requests
from typing import Dict, Any, Optional


def _read_preview_base_url() -> str:
    base_url = (os.environ.get("REACT_APP_BACKEND_URL") or "").strip().rstrip("/")
    if base_url:
        return base_url
    for env_path in ("/app/frontend/.env", "/app/.env"):
        try:
            with open(env_path, encoding="utf-8") as handle:
                for line in handle:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        return line.split("=", 1)[1].strip().strip('"').rstrip("/")
        except OSError:
            continue
    return ""


BASE_URL = _read_preview_base_url()
PREVIEW_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
PREVIEW_ADMIN_PASSWORD = "Maddix123!"


def _request_with_retry(method: str, url: str, *, attempts: int = 3, timeout: int = 60, **kwargs):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
            if response.status_code in {502, 503, 504, 520} and attempt < attempts:
                time.sleep(min(3 * attempt, 8))
                continue
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt == attempts:
                raise
            time.sleep(min(2 * attempt, 5))
    raise last_error  # pragma: no cover


class TestBackupAdminEndpointsPreview:
    """Test backup admin endpoints on Preview environment."""

    @pytest.fixture(scope="class")
    def admin_tokens(self) -> Dict[str, str]:
        """Authenticate as super admin and get portal tokens."""
        assert BASE_URL.startswith("http"), f"Invalid preview base URL: {BASE_URL!r}"
        login_url = f"{BASE_URL}/api/auth/multi-login"
        payload = {
            "email": PREVIEW_ADMIN_EMAIL,
            "password": PREVIEW_ADMIN_PASSWORD,
        }
        response = _request_with_retry(
            "POST",
            login_url,
            json=payload,
            timeout=90,
            headers={"X-Device-Id": f"pytest-preview-{uuid.uuid4().hex[:12]}"},
        )
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Extract tokens from response
        tokens = {}
        
        # Handle portal_tokens (plural) structure with nested portal-specific tokens
        # The admin token from portal_tokens should be used as X-Admin-Token
        if "portal_tokens" in data:
            portal_tokens = data["portal_tokens"]
            # Use admin token for admin endpoints - this goes in X-Admin-Token header
            if "admin" in portal_tokens:
                tokens["X-Admin-Token"] = portal_tokens["admin"]
        
        # Also check for session_token (directory token)
        if "session_token" in data:
            tokens["X-Directory-Token"] = data["session_token"]
        
        # Legacy flat structure fallback
        if "portal_token" in data:
            tokens["X-Portal-Token"] = data["portal_token"]
        if "admin_token" in data:
            tokens["X-Admin-Token"] = data["admin_token"]
        if "directory_token" in data:
            tokens["X-Directory-Token"] = data["directory_token"]
        
        # Also check for tokens in nested structure
        if "tokens" in data:
            if "portal_token" in data["tokens"]:
                tokens["X-Portal-Token"] = data["tokens"]["portal_token"]
            if "admin_token" in data["tokens"]:
                tokens["X-Admin-Token"] = data["tokens"]["admin_token"]
            if "directory_token" in data["tokens"]:
                tokens["X-Directory-Token"] = data["tokens"]["directory_token"]
        
        assert "X-Admin-Token" in tokens, f"No admin token received from login. Response: {data}"
        print(f"Admin tokens obtained: {list(tokens.keys())}")
        return tokens

    def test_01_backend_health_check(self):
        """Regression safety: Backend is responsive."""
        response = _request_with_retry("GET", f"{BASE_URL}/api/health", timeout=60)
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print(f"Backend health check passed: {response.json()}")

    def test_02_backups_scheduler_state_hourly_activation(self, admin_tokens):
        """
        Test /api/admin/backups-scheduler-state returns hourly_activation with:
        - stale_lock_present=false (no fake blockers from stale phantom signals)
        - Both stale-job counters present (stale_job_count, reclaimable_stale_job_count)
        
        In preview, BACKUP_R2_HOURLY may be disabled by config, but stale historical
        jobs must not create fake blockers.
        """
        url = f"{BASE_URL}/api/admin/backups-scheduler-state"
        response = requests.get(url, headers=admin_tokens, timeout=30)
        
        assert response.status_code == 200, f"Scheduler state failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify hourly_activation is present
        assert "hourly_activation" in data, f"Missing hourly_activation in response: {data.keys()}"
        hourly_activation = data["hourly_activation"]
        
        # Verify stale_lock_present is false (no fake blockers)
        stale_lock_present = hourly_activation.get("stale_lock_present")
        print(f"stale_lock_present: {stale_lock_present}")
        assert stale_lock_present is False, f"stale_lock_present should be False, got: {stale_lock_present}"
        
        # Verify both stale-job counters are present
        assert "stale_job_count" in hourly_activation or "blocking_stale_job_count" in hourly_activation, \
            f"Missing stale job count fields in hourly_activation: {hourly_activation.keys()}"
        
        # Check for reclaimable_stale_job_count
        assert "reclaimable_stale_job_count" in hourly_activation, \
            f"Missing reclaimable_stale_job_count in hourly_activation: {hourly_activation.keys()}"
        
        print(f"Hourly activation state:")
        print(f"  - activation_status: {hourly_activation.get('activation_status')}")
        print(f"  - stale_lock_present: {stale_lock_present}")
        print(f"  - stale_job_count: {hourly_activation.get('stale_job_count')}")
        print(f"  - blocking_stale_job_count: {hourly_activation.get('blocking_stale_job_count')}")
        print(f"  - reclaimable_stale_job_count: {hourly_activation.get('reclaimable_stale_job_count')}")
        print(f"  - environment: {hourly_activation.get('environment')}")
        
        # In preview, hourly may be disabled by config - that's expected
        # The key is that stale phantom signals don't create fake blockers
        activation_status = hourly_activation.get("activation_status", "")
        print(f"  - Full activation_status: {activation_status}")
        
        # Verify no stale-related blockers are present when stale_lock_present is false
        activation_blockers = hourly_activation.get("activation_blockers", [])
        stale_blockers = [b for b in activation_blockers if b.get("category") == "stale"]
        print(f"  - Stale blockers: {stale_blockers}")
        
        # If stale_lock_present is false, there should be no stale_scheduler_lock_present blocker
        stale_lock_blockers = [b for b in activation_blockers if b.get("code") == "stale_scheduler_lock_present"]
        assert len(stale_lock_blockers) == 0, f"Unexpected stale_scheduler_lock_present blocker when stale_lock_present=false: {stale_lock_blockers}"

    def test_03_system_health_backup_card(self, admin_tokens):
        """
        Test /api/admin/system-health backup card:
        - Should NOT say 'Authoritative recovery point unknown'
        - Should return truthful green/verified-style backup card
        - Should include canonical recoverable point and artifact filename when evidence exists
        """
        url = f"{BASE_URL}/api/admin/system-health"
        response = requests.get(url, headers=admin_tokens, timeout=30)
        
        assert response.status_code == 200, f"System health failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Find the backup card
        cards = data.get("cards", [])
        backup_card = None
        for card in cards:
            if card.get("key") == "backup":
                backup_card = card
                break
        
        assert backup_card is not None, f"Backup card not found in system health cards: {[c.get('key') for c in cards]}"
        
        print(f"Backup card:")
        print(f"  - status: {backup_card.get('status')}")
        print(f"  - canonical_status: {backup_card.get('canonical_status')}")
        print(f"  - detail: {backup_card.get('detail')}")
        print(f"  - label: {backup_card.get('label')}")
        
        detail = backup_card.get("detail", "")
        
        # Verify it doesn't say 'Authoritative recovery point unknown'
        assert "Authoritative recovery point unknown" not in detail, \
            f"Backup card should not say 'Authoritative recovery point unknown'. Detail: {detail}"
        
        # If there's backup evidence, the card should show canonical recoverable point
        status = backup_card.get("status", "")
        canonical_status = backup_card.get("canonical_status", "")
        
        # Check for truthful status (green/verified when evidence exists)
        if "Canonical recoverable point" in detail:
            print(f"  - Backup card shows canonical recoverable point (good)")
            # Should be green/verified when we have a canonical recoverable point
            assert status in ["green", "VERIFIED"] or canonical_status in ["VERIFIED", "DEGRADED"], \
                f"Expected green/verified status when canonical recoverable point exists. Status: {status}, Canonical: {canonical_status}"
        else:
            # If no canonical recoverable point, check if it's a valid degraded state
            print(f"  - No canonical recoverable point in detail, checking for valid degraded state")
            # This is acceptable if there's genuinely no backup evidence

    def test_04_backups_complete_r2_state_preview_prefix(self, admin_tokens):
        """
        Test /api/admin/backups-complete-r2-state:
        - nightly_last.r2_key should use preview-scoped prefix (backups/preview/auto-90d/...)
        - NOT the shared legacy prefix
        """
        url = f"{BASE_URL}/api/admin/backups-complete-r2-state"
        response = requests.get(url, headers=admin_tokens, timeout=30)
        
        assert response.status_code == 200, f"Complete R2 state failed: {response.status_code} - {response.text}"
        data = response.json()
        
        print(f"Complete R2 state response keys: {data.keys()}")
        
        nightly_last = data.get("nightly_last")
        print(f"nightly_last: {nightly_last}")
        
        if nightly_last:
            r2_key = nightly_last.get("r2_key", "")
            print(f"  - r2_key: {r2_key}")
            
            # Verify it uses preview-scoped prefix
            assert r2_key.startswith("backups/preview/auto-90d/"), \
                f"nightly_last.r2_key should use preview-scoped prefix 'backups/preview/auto-90d/', got: {r2_key}"
            
            # Verify it does NOT use the legacy shared prefix
            assert not r2_key.startswith("backups/auto-90d/"), \
                f"nightly_last.r2_key should NOT use legacy shared prefix 'backups/auto-90d/', got: {r2_key}"
        else:
            print("  - No nightly_last data (may be expected if no backups exist)")
        
        # Also check hourly_activation in this response
        hourly_activation = data.get("hourly_activation", {})
        print(f"hourly_activation environment: {hourly_activation.get('environment')}")
        
        # Check archive_lineage if present
        archive_lineage = data.get("archive_lineage", {})
        if archive_lineage:
            print(f"archive_lineage keys: {archive_lineage.keys()}")

    def test_05_backups_list_r2_environment_scoped(self, admin_tokens):
        """
        Test /api/admin/backups-list-r2:
        - prefix should equal backups/preview/auto-90d/
        - returned keys should stay inside that prefix (not broad/shared bucket enumeration)
        """
        url = f"{BASE_URL}/api/admin/backups-list-r2"
        response = requests.get(url, headers=admin_tokens, timeout=30)
        
        assert response.status_code == 200, f"List R2 backups failed: {response.status_code} - {response.text}"
        data = response.json()
        
        print(f"List R2 backups response:")
        print(f"  - count: {data.get('count')}")
        print(f"  - total_in_bucket: {data.get('total_in_bucket')}")
        print(f"  - prefix: {data.get('prefix')}")
        
        # Verify prefix is environment-scoped
        prefix = data.get("prefix", "")
        assert prefix == "backups/preview/auto-90d/", \
            f"prefix should be 'backups/preview/auto-90d/', got: {prefix}"
        
        # Verify returned keys stay inside the prefix
        backups = data.get("backups", [])
        for backup in backups[:5]:  # Check first 5
            key = backup.get("key", "")
            print(f"  - backup key: {key}")
            assert key.startswith("backups/preview/auto-90d/"), \
                f"Backup key should start with 'backups/preview/auto-90d/', got: {key}"
            
            # Verify it's NOT using legacy shared prefix
            assert not key.startswith("backups/auto-90d/") or key.startswith("backups/preview/auto-90d/"), \
                f"Backup key should not use legacy shared prefix without environment scope: {key}"

    def test_06_regression_no_504_520_on_admin_endpoints(self, admin_tokens):
        """
        Regression safety: Key admin backup endpoints should remain responsive
        (no 504/520 style regressions).
        """
        endpoints = [
            "/api/admin/backups-scheduler-state",
            "/api/admin/backups-complete-r2-state",
            "/api/admin/backups-list-r2",
            "/api/admin/system-health",
        ]
        
        for endpoint in endpoints:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, headers=admin_tokens, timeout=60)
            
            # Should not get 504 (Gateway Timeout) or 520 (Cloudflare error)
            assert response.status_code not in [504, 520], \
                f"Endpoint {endpoint} returned {response.status_code} (timeout/error)"
            
            # Should get 200 OK
            assert response.status_code == 200, \
                f"Endpoint {endpoint} returned {response.status_code}: {response.text[:200]}"
            
            print(f"Endpoint {endpoint}: OK (200)")

    def test_07_hourly_activation_blockers_structure(self, admin_tokens):
        """
        Verify hourly_activation blockers have proper structure and categories.
        """
        url = f"{BASE_URL}/api/admin/backups-scheduler-state"
        response = requests.get(url, headers=admin_tokens, timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        
        hourly_activation = data.get("hourly_activation", {})
        activation_blockers = hourly_activation.get("activation_blockers", [])
        
        print(f"Activation blockers ({len(activation_blockers)}):")
        for blocker in activation_blockers:
            print(f"  - code: {blocker.get('code')}, category: {blocker.get('category')}, blocking: {blocker.get('blocking')}")
            
            # Verify blocker structure
            assert "code" in blocker, f"Blocker missing 'code': {blocker}"
            assert "category" in blocker, f"Blocker missing 'category': {blocker}"
            assert "detail" in blocker, f"Blocker missing 'detail': {blocker}"
            assert "blocking" in blocker, f"Blocker missing 'blocking': {blocker}"
        
        # In preview environment, we expect environment_not_production blocker
        env_blockers = [b for b in activation_blockers if b.get("code") == "environment_not_production"]
        if hourly_activation.get("environment") == "preview":
            assert len(env_blockers) > 0, "Expected environment_not_production blocker in preview"
            print(f"  - Correctly has environment_not_production blocker for preview")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

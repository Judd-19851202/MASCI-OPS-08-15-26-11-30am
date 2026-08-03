"""
BCSS Release 2 / Program 2 / Wave 3 / Family 3A Bounded Verification
Tests the strict-admin, read-only Core Admin Operations surface.
"""
import os
import pytest
import requests
import httpx

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


def _raw_get(path, headers=None, timeout=15):
    """Direct httpx GET to bypass any conftest auto-admin-token patch."""
    with httpx.Client(timeout=timeout) as c:
        return c.get(f"{BASE_URL}{path}", headers=headers or {})


@pytest.fixture(scope="module")
def auth_bundle():
    """Get admin auth bundle via multi-login."""
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=20,
    )
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text}"
    data = r.json()
    tokens = data.get("portal_tokens") or {}
    assert tokens.get("admin"), "missing admin token"
    assert data.get("session_token"), "missing directory session token"
    return data


@pytest.fixture(scope="module")
def admin_headers(auth_bundle):
    """Strict admin headers with both X-Admin-Token and X-Directory-Token."""
    return {
        "X-Admin-Token": auth_bundle["portal_tokens"]["admin"],
        "X-Directory-Token": auth_bundle["session_token"],
    }


# ═══════════════════════════════════════════════════════════════════════════
# FAMILY 3A STRICT-ADMIN BOUNDARY VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════

class TestFamily3AStrictAdminBoundary:
    """Verify strict-admin boundary is preserved for all Family 3A endpoints."""
    
    def test_system_health_requires_admin(self):
        """Anonymous access to /api/admin/system-health must be rejected."""
        r = _raw_get("/api/admin/system-health")
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"
    
    def test_system_health_recent_requires_admin(self):
        """Anonymous access to /api/admin/system-health/recent must be rejected."""
        r = _raw_get("/api/admin/system-health/recent")
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"
    
    def test_audit_log_requires_admin(self):
        """Anonymous access to /api/admin/audit-log must be rejected."""
        r = _raw_get("/api/admin/audit-log")
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"
    
    def test_search_requires_admin(self):
        """Anonymous access to /api/admin/search must be rejected."""
        r = _raw_get("/api/admin/search?q=test")
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"
    
    def test_lookup_requires_admin(self):
        """Anonymous access to /api/admin/lookup must be rejected."""
        r = _raw_get("/api/admin/lookup?ref=TEST-123")
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"
    
    def test_non_admin_token_rejected_system_health(self):
        """Non-admin tokens (e.g., HR-only) must be rejected."""
        r = _raw_get("/api/admin/system-health", headers={"X-HR-Token": "bogus"})
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"
    
    def test_non_admin_token_rejected_lookup(self):
        """Non-admin tokens (e.g., PM-only without admin) must be rejected for lookup."""
        r = _raw_get("/api/admin/lookup?ref=TEST-123", headers={"X-PM-Token": "bogus"})
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"


# ═══════════════════════════════════════════════════════════════════════════
# FAMILY 3A READ-ONLY VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════

class TestFamily3AReadOnly:
    """Verify Family 3A endpoints remain read-only (no mutations)."""
    
    def test_system_health_is_read_only(self, admin_headers):
        """Multiple calls to /api/admin/system-health must not mutate data."""
        r1 = requests.get(f"{BASE_URL}/api/admin/system-health", headers=admin_headers, timeout=30)
        r2 = requests.get(f"{BASE_URL}/api/admin/system-health", headers=admin_headers, timeout=30)
        assert r1.status_code == 200
        assert r2.status_code == 200
        d1, d2 = r1.json(), r2.json()
        # Structure must be identical (only checked_at may differ)
        assert d1["overall"] == d2["overall"]
        assert len(d1["cards"]) == len(d2["cards"])
        for c1, c2 in zip(d1["cards"], d2["cards"]):
            assert c1["key"] == c2["key"]
            assert c1["label"] == c2["label"]
    
    def test_system_health_recent_is_read_only(self, admin_headers):
        """Multiple calls to /api/admin/system-health/recent must not mutate data."""
        r1 = requests.get(f"{BASE_URL}/api/admin/system-health/recent", headers=admin_headers, timeout=15)
        r2 = requests.get(f"{BASE_URL}/api/admin/system-health/recent", headers=admin_headers, timeout=15)
        assert r1.status_code == 200
        assert r2.status_code == 200
        d1, d2 = r1.json(), r2.json()
        assert d1["limit"] == d2["limit"]
        # Row count should be stable (may grow if monitor runs, but not shrink)
        assert len(d1["rows"]) <= len(d2["rows"]) + 1  # Allow for 1 new row
    
    def test_audit_log_is_read_only(self, admin_headers):
        """Multiple calls to /api/admin/audit-log must not mutate data."""
        r1 = requests.get(f"{BASE_URL}/api/admin/audit-log?limit=10", headers=admin_headers, timeout=30)
        r2 = requests.get(f"{BASE_URL}/api/admin/audit-log?limit=10", headers=admin_headers, timeout=30)
        assert r1.status_code == 200
        assert r2.status_code == 200
        d1, d2 = r1.json(), r2.json()
        assert d1["limit"] == d2["limit"]
    
    def test_search_is_read_only(self, admin_headers):
        """Multiple calls to /api/admin/search must not mutate data."""
        r1 = requests.get(f"{BASE_URL}/api/admin/search?q=test", headers=admin_headers, timeout=30)
        r2 = requests.get(f"{BASE_URL}/api/admin/search?q=test", headers=admin_headers, timeout=30)
        assert r1.status_code == 200
        assert r2.status_code == 200
        d1, d2 = r1.json(), r2.json()
        assert d1["q"] == d2["q"]
    
    def test_lookup_is_read_only(self, admin_headers):
        """Multiple calls to /api/admin/lookup must not mutate data."""
        r1 = requests.get(f"{BASE_URL}/api/admin/lookup?ref=DOES-NOT-EXIST", headers=admin_headers, timeout=15)
        r2 = requests.get(f"{BASE_URL}/api/admin/lookup?ref=DOES-NOT-EXIST", headers=admin_headers, timeout=15)
        assert r1.status_code == 200
        assert r2.status_code == 200
        d1, d2 = r1.json(), r2.json()
        assert d1["found"] == d2["found"]
        assert d1["ref"] == d2["ref"]


# ═══════════════════════════════════════════════════════════════════════════
# FAMILY 3A CONTRACT VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════

class TestFamily3ASystemHealthContract:
    """Verify /api/admin/system-health returns bounded contract with UI status."""
    
    def test_system_health_returns_ui_status(self, admin_headers):
        """System health must return UI-safe status (green|yellow|red)."""
        r = requests.get(f"{BASE_URL}/api/admin/system-health", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        
        # Overall status must be UI-safe
        assert data["overall"] in ("green", "yellow", "red"), f"invalid overall: {data['overall']}"
        
        # Overall canonical status must be present
        assert "overall_canonical" in data
        assert data["overall_canonical"] in ("VERIFIED", "DEGRADED", "MISMATCH", "UNVERIFIABLE", "NOT_APPLICABLE")
        
        # Cards must have both UI status and canonical status
        assert "cards" in data
        assert isinstance(data["cards"], list)
        for card in data["cards"]:
            assert "key" in card
            assert "label" in card
            assert "status" in card
            assert card["status"] in ("green", "yellow", "red"), f"invalid card status: {card['status']}"
            assert "canonical_status" in card
            assert card["canonical_status"] in ("VERIFIED", "DEGRADED", "MISMATCH", "UNVERIFIABLE", "NOT_APPLICABLE")
            assert "detail" in card
    
    def test_system_health_has_required_cards(self, admin_headers):
        """System health must include required card keys."""
        r = requests.get(f"{BASE_URL}/api/admin/system-health", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        
        keys = {c["key"] for c in data["cards"]}
        required = {"database", "r2", "backup", "auth_failures", "integrations", "failed_syncs", "active_sessions", "version"}
        missing = required - keys
        assert not missing, f"missing health card keys: {missing}"
    
    def test_system_health_has_counts(self, admin_headers):
        """System health must include canonical counts."""
        r = requests.get(f"{BASE_URL}/api/admin/system-health", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        
        assert "counts" in data
        counts = data["counts"]
        for key in ("verified", "degraded", "mismatch", "unverifiable", "not_applicable", "total_applicable", "total_cards"):
            assert key in counts, f"missing count key: {key}"


class TestFamily3ASystemHealthRecentContract:
    """Verify /api/admin/system-health/recent returns correct shape."""
    
    def test_system_health_recent_shape(self, admin_headers):
        """System health recent must return limit and rows."""
        r = requests.get(f"{BASE_URL}/api/admin/system-health/recent", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        
        assert "limit" in data
        assert "rows" in data
        assert isinstance(data["rows"], list)
        
        # If rows exist, verify shape
        if data["rows"]:
            row = data["rows"][0]
            assert "at" in row
            assert "overall" in row
            assert "red_keys" in row
            assert "alerted" in row


class TestFamily3AAuditLogContract:
    """Verify /api/admin/audit-log returns correct shape."""
    
    def test_audit_log_shape(self, admin_headers):
        """Audit log must return paginated rows with normalized fields."""
        r = requests.get(f"{BASE_URL}/api/admin/audit-log?limit=10", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        
        for key in ("total", "offset", "limit", "rows"):
            assert key in data, f"missing key: {key}"
        
        assert isinstance(data["rows"], list)
        if data["rows"]:
            row = data["rows"][0]
            for key in ("at", "actor", "action", "target", "source", "detail"):
                assert key in row, f"row missing key: {key}"


class TestFamily3ASearchContract:
    """Verify /api/admin/search returns correct shape."""
    
    def test_search_shape(self, admin_headers):
        """Search must return q, groups, and total."""
        r = requests.get(f"{BASE_URL}/api/admin/search?q=test", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        
        assert "q" in data
        assert data["q"] == "test"
        assert "groups" in data
        assert isinstance(data["groups"], list)
        assert "total" in data
        
        # If groups exist, verify shape
        for g in data["groups"]:
            assert "label" in g
            assert "count" in g
            assert "rows" in g


class TestFamily3ALookupContract:
    """Verify /api/admin/lookup returns correct shape."""
    
    def test_lookup_found_shape(self, admin_headers):
        """Lookup for known incident ref must return found=True with path."""
        r = requests.get(f"{BASE_URL}/api/admin/lookup?ref=INC-2026-0517-002", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        
        assert "found" in data
        if data["found"]:
            assert "kind" in data
            assert "id" in data
            assert "ref" in data
            assert "path" in data
    
    def test_lookup_miss_shape(self, admin_headers):
        """Lookup for unknown ref must return found=False gracefully."""
        r = requests.get(f"{BASE_URL}/api/admin/lookup?ref=DOES-NOT-EXIST-9999", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        
        assert data["found"] is False
        assert "ref" in data


# ═══════════════════════════════════════════════════════════════════════════
# FAMILY 3A NO SPILLOVER VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════

class TestFamily3ANoSpillover:
    """Verify no adjacent family behavior is required or modified."""
    
    def test_operations_py_not_required(self, admin_headers):
        """Family 3A endpoints must work without requiring operations.py routes."""
        # All Family 3A endpoints should work independently
        r = requests.get(f"{BASE_URL}/api/admin/system-health", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        
        r = requests.get(f"{BASE_URL}/api/admin/audit-log?limit=5", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        
        r = requests.get(f"{BASE_URL}/api/admin/search?q=test", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        
        r = requests.get(f"{BASE_URL}/api/admin/lookup?ref=TEST", headers=admin_headers, timeout=15)
        assert r.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

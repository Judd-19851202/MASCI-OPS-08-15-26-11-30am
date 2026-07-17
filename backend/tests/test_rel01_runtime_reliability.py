"""
REL-01 Track Testing: Production 520 Root-Cause Forensics and Permanent Reliability Repair

Tests the new runtime reliability infrastructure:
- Layered health states (liveness, readiness, full health)
- Background task registry and monitoring
- Incident forensics capture
- Scheduler isolation
- X-MASCI-* runtime headers

Test credentials: jaymn.judd@mascigc.com / Maddix123!
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    pytest.skip("REACT_APP_BACKEND_URL not set", allow_module_level=True)

# Super-admin credentials for multi-login
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token via multi-login"""
    response = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
        timeout=15,
    )
    assert response.status_code == 200, f"Multi-login failed: {response.text}"
    data = response.json()
    assert data.get("ok") is True, f"Multi-login not ok: {data}"
    assert "portal_tokens" in data, "No portal_tokens in response"
    assert "admin" in data["portal_tokens"], "No admin token in portal_tokens"
    return data["portal_tokens"]["admin"]


class TestPublicHealthEndpoints:
    """Test public health endpoints (no auth required)"""

    def test_api_health_returns_200_with_headers(self):
        """GET /api/health returns 200 quickly with X-MASCI-* headers"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=15)
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        
        # Verify response body
        data = response.json()
        assert data.get("ok") is True
        assert data.get("service") == "masci-hub"
        assert "ts" in data
        
        # Verify X-MASCI-* headers
        headers = response.headers
        assert "X-MASCI-Liveness" in headers, "Missing X-MASCI-Liveness header"
        assert "X-MASCI-Readiness" in headers, "Missing X-MASCI-Readiness header"
        assert "X-MASCI-Full-Health" in headers, "Missing X-MASCI-Full-Health header"
        assert "X-MASCI-Instance" in headers, "Missing X-MASCI-Instance header"
        
        # Verify header values
        assert headers["X-MASCI-Liveness"] == "alive"
        assert headers["X-MASCI-Readiness"] == "ready"
        assert headers["X-MASCI-Full-Health"] in ["healthy", "degraded"]

    def test_api_ready_returns_readiness_payload(self):
        """GET /api/ready returns 200 with readiness summary"""
        response = requests.get(f"{BASE_URL}/api/ready", timeout=10)
        assert response.status_code == 200, f"Ready check failed: {response.status_code}"
        
        data = response.json()
        # Verify required fields
        assert "ok" in data, "Missing 'ok' field"
        assert "state" in data, "Missing 'state' field"
        assert "reason" in data, "Missing 'reason' field"
        assert "event_loop_ok" in data, "Missing 'event_loop_ok' field"
        assert "mongo_ok" in data, "Missing 'mongo_ok' field"
        assert "startup_complete" in data, "Missing 'startup_complete' field"
        
        # Verify values for healthy state
        assert data["ok"] is True, f"Readiness not ok: {data}"
        assert data["state"] == "ready"
        assert data["event_loop_ok"] is True
        assert data["mongo_ok"] is True
        assert data["startup_complete"] is True

    def test_api_health_full_returns_legacy_contract(self):
        """GET /api/health/full returns legacy boolean contract"""
        response = requests.get(f"{BASE_URL}/api/health/full", timeout=10)
        assert response.status_code == 200, f"Full health check failed: {response.status_code}"
        
        data = response.json()
        # Verify legacy contract fields
        assert "ok" in data, "Missing 'ok' field"
        assert "mongo" in data, "Missing 'mongo' field"
        assert "scheduler" in data, "Missing 'scheduler' field"
        assert "backup_recent" in data, "Missing 'backup_recent' field"
        
        # All should be boolean
        assert isinstance(data["ok"], bool)
        assert isinstance(data["mongo"], bool)
        assert isinstance(data["scheduler"], bool)
        assert isinstance(data["backup_recent"], bool)
        
        # In healthy preview environment, all should be True
        assert data["ok"] is True, f"Full health not ok: {data}"
        assert data["mongo"] is True, f"Mongo not healthy: {data}"
        assert data["scheduler"] is True, f"Scheduler not healthy: {data}"
        assert data["backup_recent"] is True, f"Backup not recent: {data}"

    def test_api_version_returns_release_info(self):
        """GET /api/version returns release information"""
        response = requests.get(f"{BASE_URL}/api/version", timeout=10)
        assert response.status_code == 200, f"Version check failed: {response.status_code}"
        
        data = response.json()
        assert "service" in data
        assert "commit" in data
        assert "source_hash" in data
        assert data["service"] == "masci-hub"


class TestAuthenticatedDiagnosticEndpoints:
    """Test admin-strict diagnostic endpoints (require admin token)"""

    def test_runtime_health_returns_layered_snapshot(self, admin_token):
        """GET /api/admin-strict/diag/runtime-health returns layered health snapshot"""
        response = requests.get(
            f"{BASE_URL}/api/admin-strict/diag/runtime-health",
            headers={"X-Admin-Token": admin_token},
            timeout=15,
        )
        assert response.status_code == 200, f"Runtime health failed: {response.status_code}"
        
        data = response.json()
        
        # Verify layered health structure
        assert "liveness" in data, "Missing 'liveness' layer"
        assert "readiness" in data, "Missing 'readiness' layer"
        assert "full_health" in data, "Missing 'full_health' layer"
        
        # Verify liveness layer
        assert data["liveness"]["ok"] is True
        assert data["liveness"]["state"] == "alive"
        
        # Verify readiness layer
        assert "ok" in data["readiness"]
        assert "state" in data["readiness"]
        assert "reason" in data["readiness"]
        
        # Verify full_health layer
        assert "ok" in data["full_health"]
        assert "state" in data["full_health"]
        assert "reason_codes" in data["full_health"]
        
        # Verify metrics
        assert "event_loop_lag_ms" in data
        assert "mongo_latency_ms" in data
        assert "mongo_ok" in data
        assert "resources" in data
        
        # Verify background tasks
        assert "background_tasks" in data
        assert isinstance(data["background_tasks"], list)
        
        # Verify at least some background tasks are running
        running_tasks = [t for t in data["background_tasks"] if t.get("status") == "running"]
        assert len(running_tasks) > 0, "No running background tasks found"
        
        # Verify task structure
        for task in data["background_tasks"]:
            assert "name" in task
            assert "category" in task
            assert "status" in task
            assert "critical" in task

    def test_incident_forensics_returns_bounded_list(self, admin_token):
        """GET /api/admin-strict/diag/incident-forensics returns bounded list without secrets"""
        response = requests.get(
            f"{BASE_URL}/api/admin-strict/diag/incident-forensics?limit=10",
            headers={"X-Admin-Token": admin_token},
            timeout=15,
        )
        assert response.status_code == 200, f"Incident forensics failed: {response.status_code}"
        
        data = response.json()
        
        # Verify response structure
        assert "count" in data, "Missing 'count' field"
        assert "rows" in data, "Missing 'rows' field"
        assert isinstance(data["rows"], list)
        
        # Verify count matches rows
        assert data["count"] == len(data["rows"])
        
        # Verify limit is respected
        assert data["count"] <= 10
        
        # If there are incidents, verify structure and no secrets
        for incident in data["rows"]:
            # Should have basic fields
            if "captured_at" in incident:
                assert "trigger" in incident
            
            # Should NOT contain secrets (check for redaction)
            incident_str = str(incident).lower()
            assert "password" not in incident_str or "***" in incident_str
            assert "api_key" not in incident_str or "***" in incident_str
            # MongoDB URIs should be redacted
            if "mongodb" in incident_str:
                assert "***" in incident_str

    def test_persistence_health_returns_status(self, admin_token):
        """GET /api/admin-strict/diag/persistence-health returns persistence status"""
        response = requests.get(
            f"{BASE_URL}/api/admin-strict/diag/persistence-health",
            headers={"X-Admin-Token": admin_token},
            timeout=15,
        )
        assert response.status_code == 200, f"Persistence health failed: {response.status_code}"
        
        data = response.json()
        
        # Verify key fields
        assert "captured_at" in data
        assert "atlas_connected" in data
        assert "db_name" in data
        assert "collections_detected" in data
        
        # Verify healthy state
        assert data["atlas_connected"] is True
        assert data["collections_detected"] > 0
        
        # Verify backup info
        assert "last_backup_time" in data or "r2_backup_success" in data


class TestOperationalEndpoints:
    """Test operational endpoints that should work with admin token"""

    def test_daily_reports_approved_works(self, admin_token):
        """GET /api/daily-reports/approved?limit=1 works"""
        response = requests.get(
            f"{BASE_URL}/api/daily-reports/approved?limit=1",
            headers={"X-Admin-Token": admin_token},
            timeout=15,
        )
        assert response.status_code == 200, f"Daily reports approved failed: {response.status_code}"
        
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_search_works(self, admin_token):
        """GET /api/search?q=report&limit=3 works"""
        response = requests.get(
            f"{BASE_URL}/api/search?q=report&limit=3",
            headers={"X-Admin-Token": admin_token},
            timeout=15,
        )
        assert response.status_code == 200, f"Search failed: {response.status_code}"
        
        data = response.json()
        assert "q" in data
        assert data["q"] == "report"

    def test_dispatch_motive_posture_works(self, admin_token):
        """GET /api/dispatch/motive-posture works"""
        response = requests.get(
            f"{BASE_URL}/api/dispatch/motive-posture",
            headers={"X-Admin-Token": admin_token},
            timeout=15,
        )
        assert response.status_code == 200, f"Motive posture failed: {response.status_code}"
        
        data = response.json()
        assert "id" in data
        assert data["id"] == "motive"
        assert "operational_status" in data
        assert "overall" in data


class TestMultiLogin:
    """Test multi-login authentication"""

    def test_multi_login_returns_portal_tokens(self):
        """POST /api/auth/multi-login returns portal_tokens"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
            timeout=15,
        )
        assert response.status_code == 200, f"Multi-login failed: {response.status_code}"
        
        data = response.json()
        assert data.get("ok") is True
        assert "portal_tokens" in data
        
        # Super admin should have all portal tokens
        tokens = data["portal_tokens"]
        assert "admin" in tokens
        assert "pm" in tokens
        assert "shop" in tokens
        assert "hr" in tokens
        assert "safety" in tokens
        assert "dispatch" in tokens
        
        # Verify user info
        assert "user" in data
        assert data["user"]["email"] == SUPER_ADMIN_EMAIL
        assert data["user"]["is_super_admin"] is True


class TestRegressionProbes:
    """Regression tests for probe artifacts"""

    def test_api_health_no_timeout(self):
        """Health endpoint should respond quickly (no timeout)"""
        import time
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/health", timeout=15)
        elapsed = time.time() - start
        
        assert response.status_code == 200
        # Allow up to 5s for network latency in test environment
        assert elapsed < 5.0, f"Health check took too long: {elapsed}s"

    def test_api_version_no_500(self):
        """Version endpoint should not return 500"""
        response = requests.get(f"{BASE_URL}/api/version", timeout=10)
        assert response.status_code != 500, f"Version returned 500: {response.text}"
        assert response.status_code == 200

    def test_api_ready_no_500(self):
        """Ready endpoint should not return 500"""
        response = requests.get(f"{BASE_URL}/api/ready", timeout=10)
        assert response.status_code != 500, f"Ready returned 500: {response.text}"
        # Can be 200 (ready) or 503 (not ready), but not 500
        assert response.status_code in [200, 503]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

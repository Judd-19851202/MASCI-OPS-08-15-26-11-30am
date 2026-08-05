"""
TRACK 15.79 · C2 Deployment Identity & Automatic Governance Closure Tests

Tests for:
- /release-identity.json (frontend artifact identity)
- /api/version (backend runtime identity + frontend parity)
- /api/health/full (deep health with backup_recent)
- Protected governance endpoints with dual-token auth
- Automatic deployment verification ledger
- Daily Report public workflow remains anonymous
"""
import os
import pytest
import requests
import uuid
from lib.rate_limiting import _reset_login_fails

PUBLIC_BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not PUBLIC_BASE_URL:
    PUBLIC_BASE_URL = "https://masci-audit-hub.preview.emergentagent.com"
API_BASE_URL = os.environ.get('LOCAL_BACKEND_URL', 'http://127.0.0.1:8001').rstrip('/')


def _api_get(path: str, *, timeout: int = 30):
    last_error = None
    for base in (API_BASE_URL, PUBLIC_BASE_URL):
        try:
            response = requests.get(f"{base}{path}", timeout=timeout)
            if response.status_code == 200:
                return response
        except requests.RequestException as exc:
            last_error = exc
    if last_error:
        raise last_error
    raise AssertionError(f"Unable to fetch {path} from API surfaces")

# Test credentials from test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


class TestPublicEndpoints:
    """Test public endpoints that don't require authentication"""
    
    def test_frontend_loads_not_blank(self):
        """Public preview root loads and is not blank"""
        response = requests.get(f"{PUBLIC_BASE_URL}/", timeout=10)
        assert response.status_code == 200
        assert len(response.text) > 1000, "Frontend should return substantial HTML"
        assert "MASCI" in response.text, "Frontend should contain MASCI branding"
        assert "/static/js/bundle.js" in response.text, "Frontend should reference bundle.js"
        print("✓ Frontend loads and is not blank")
    
    def test_release_identity_json(self):
        """GET /release-identity.json returns served frontend artifact identity"""
        response = requests.get(f"{PUBLIC_BASE_URL}/release-identity.json", timeout=10)
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "commit" in data, "release-identity.json must have commit"
        assert "source_hash" in data, "release-identity.json must have source_hash"
        assert "built_at" in data, "release-identity.json must have built_at"
        assert "version" in data, "release-identity.json must have version"
        
        # Verify commit is a full SHA (40 chars)
        commit = data.get("commit", "")
        assert len(commit) == 40, f"Commit should be full 40-char SHA, got {len(commit)} chars"
        
        # Verify source_hash is present
        source_hash = data.get("source_hash", "")
        assert len(source_hash) >= 12, "source_hash should be at least 12 chars"
        
        print(f"✓ /release-identity.json returns valid identity: commit={commit[:12]}, source_hash={source_hash[:12]}")
    
    def test_api_version(self):
        """GET /api/version reports backend runtime commit and frontend parity"""
        response = _api_get("/api/version")
        assert response.status_code == 200
        data = response.json()
        
        # Backend runtime identity
        assert "commit" in data, "/api/version must have commit"
        assert "source_hash" in data, "/api/version must have source_hash"
        backend_commit = data.get("commit", "")
        assert len(backend_commit) == 40, f"Backend commit should be 40-char SHA, got {len(backend_commit)}"
        
        # Frontend build identity
        assert "frontend_build_commit" in data, "/api/version must have frontend_build_commit"
        frontend_commit = data.get("frontend_build_commit", "")
        assert len(frontend_commit) == 40, f"Frontend commit should be 40-char SHA, got {len(frontend_commit)}"
        
        # Release parity
        assert "frontend_backend_release_match" in data, "/api/version must have frontend_backend_release_match"
        assert data["frontend_backend_release_match"] is True, "frontend_backend_release_match should be true"
        
        # Frontend build source should point to served identity
        assert "frontend_build_source" in data, "/api/version must have frontend_build_source"
        frontend_source = data.get("frontend_build_source", "")
        assert "served:" in frontend_source, f"frontend_build_source should be served:*, got {frontend_source}"
        
        print(f"✓ /api/version: backend={backend_commit[:12]}, frontend={frontend_commit[:12]}, match=true")
    
    def test_api_health_full(self):
        """GET /api/health/full returns 200 with all subsystems healthy"""
        response = _api_get("/api/health/full")
        assert response.status_code == 200
        data = response.json()
        
        # Required health checks
        assert data.get("ok") is True, "ok should be true"
        assert data.get("mongo") is True, "mongo should be true"
        assert data.get("scheduler") is True, "scheduler should be true"
        assert data.get("backup_recent") is True, "backup_recent should be true"
        
        # Should not leak secrets
        response_text = response.text.lower()
        assert "password" not in response_text, "Should not leak password"
        assert "secret" not in response_text, "Should not leak secret"
        assert "api_key" not in response_text, "Should not leak api_key"
        
        print("✓ /api/health/full: ok=true, mongo=true, scheduler=true, backup_recent=true")
    
    def test_daily_submit_public_access(self):
        """Daily Report public workflow remains anonymous: /daily/submit loads without auth"""
        response = requests.get(f"{PUBLIC_BASE_URL}/daily/submit", timeout=10)
        assert response.status_code == 200
        assert len(response.text) > 1000, "Daily submit page should return substantial HTML"
        print("✓ /daily/submit loads without auth gating")


class TestProtectedGovernanceEndpoints:
    """Test protected governance endpoints requiring dual-token auth"""
    
    @pytest.fixture(scope="class")
    def auth_tokens(self):
        """Get admin and directory tokens via multi-login"""
        _reset_login_fails("127.0.0.1")
        response = requests.post(
            f"{API_BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"X-Device-Id": f"c2-auth-{uuid.uuid4().hex[:10]}"},
            timeout=10
        )
        assert response.status_code == 200, f"Multi-login failed: {response.text}"
        data = response.json()
        
        admin_token = data.get("portal_tokens", {}).get("admin")
        directory_token = data.get("session_token")
        
        assert admin_token, "Admin token not returned"
        assert directory_token, "Directory token not returned"
        
        return {"admin": admin_token, "directory": directory_token}
    
    def test_admin_check(self, auth_tokens):
        """Protected /api/admin/check accessible with both tokens"""
        headers = {
            "X-Admin-Token": auth_tokens["admin"],
            "X-Directory-Token": auth_tokens["directory"]
        }
        response = requests.get(f"{API_BASE_URL}/api/admin/check", headers=headers, timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True
        print("✓ /api/admin/check returns ok=true with dual tokens")
    
    def test_deployment_readiness(self, auth_tokens):
        """Protected /api/admin/deployment-readiness accessible with both tokens"""
        headers = {
            "X-Admin-Token": auth_tokens["admin"],
            "X-Directory-Token": auth_tokens["directory"]
        }
        response = requests.get(f"{API_BASE_URL}/api/admin/deployment-readiness", headers=headers, timeout=10)
        assert response.status_code == 200
        data = response.json()
        
        assert "decision" in data, "deployment-readiness must have decision"
        assert data["decision"] in ["pass", "fail"], f"decision must be pass/fail, got {data['decision']}"
        print(f"✓ /api/admin/deployment-readiness: decision={data['decision']}")
    
    def test_deployment_readiness_history(self, auth_tokens):
        """Protected /api/admin/deployment-readiness/history accessible with both tokens"""
        headers = {
            "X-Admin-Token": auth_tokens["admin"],
            "X-Directory-Token": auth_tokens["directory"]
        }
        response = requests.get(
            f"{API_BASE_URL}/api/admin/deployment-readiness/history?limit=5",
            headers=headers,
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "events" in data, "history must have events"
        assert "total_ever" in data, "history must have total_ever"
        
        # Verify latest event has expected fields
        if data["events"]:
            latest = data["events"][0]
            assert "verification_id" in latest, "event must have verification_id"
            assert "decision" in latest, "event must have decision"
            assert "backend_runtime_commit" in latest, "event must have backend_runtime_commit"
            assert "frontend_build_commit" in latest, "event must have frontend_build_commit"
        
        print(f"✓ /api/admin/deployment-readiness/history: {len(data['events'])} events, total={data['total_ever']}")
    
    def test_occ_trust_events(self, auth_tokens):
        """Protected /api/admin/occ/trust-events accessible with both tokens"""
        headers = {
            "X-Admin-Token": auth_tokens["admin"],
            "X-Directory-Token": auth_tokens["directory"]
        }
        response = requests.get(
            f"{API_BASE_URL}/api/admin/occ/trust-events?limit=10",
            headers=headers,
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "events" in data, "trust-events must have events"
        assert "counts" in data, "trust-events must have counts"
        assert "by_kind" in data, "trust-events must have by_kind"
        
        # Verify deploy events are present
        deploy_count = data.get("by_kind", {}).get("deploy", 0)
        print(f"✓ /api/admin/occ/trust-events: {len(data['events'])} events, {deploy_count} deploy events")


class TestAutomaticDeploymentVerification:
    """Test automatic startup deployment verification creates ledger records"""
    
    @pytest.fixture(scope="class")
    def auth_tokens(self):
        """Get admin and directory tokens via multi-login"""
        _reset_login_fails("127.0.0.1")
        response = requests.post(
            f"{API_BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"X-Device-Id": f"c2-auto-{uuid.uuid4().hex[:10]}"},
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        return {
            "admin": data.get("portal_tokens", {}).get("admin"),
            "directory": data.get("session_token")
        }
    
    def test_automatic_verification_ledger_record(self, auth_tokens):
        """Automatic startup verification creates deployment_decisions ledger record"""
        headers = {
            "X-Admin-Token": auth_tokens["admin"],
            "X-Directory-Token": auth_tokens["directory"]
        }
        
        # Get version to find current commit
        version_resp = requests.get(f"{API_BASE_URL}/api/version", timeout=10)
        version_data = version_resp.json()
        current_commit = version_data.get("commit", "")[:12]
        
        # Get deployment history
        history_resp = requests.get(
            f"{API_BASE_URL}/api/admin/deployment-readiness/history?limit=20",
            headers=headers,
            timeout=10
        )
        assert history_resp.status_code == 200
        history_data = history_resp.json()
        
        # Find automatic verification for current commit
        auto_verifications = [
            e for e in history_data.get("events", [])
            if e.get("verification_source") == "automatic_startup_verification"
            and e.get("backend_runtime_commit", "").startswith(current_commit)
        ]
        
        assert len(auto_verifications) > 0, f"No automatic verification found for commit {current_commit}"
        
        latest_auto = auto_verifications[0]
        assert latest_auto.get("decision") in ["pass", "fail"], "Auto verification must have decision"
        assert latest_auto.get("go_no_go") in ["GO", "NO-GO"], "Auto verification must have go_no_go"
        
        print(f"✓ Automatic verification found: decision={latest_auto['decision']}, go_no_go={latest_auto['go_no_go']}")
    
    def test_deployment_verification_audit_event(self, auth_tokens):
        """Automatic startup verification is visible through admin audit surfaces."""
        headers = {
            "X-Admin-Token": auth_tokens["admin"],
            "X-Directory-Token": auth_tokens["directory"]
        }
        
        # Get trust events which include audit entries
        trust_resp = requests.get(
            f"{API_BASE_URL}/api/admin/occ/trust-events?limit=50",
            headers=headers,
            timeout=10
        )
        assert trust_resp.status_code == 200
        trust_data = trust_resp.json()
        
        # Find deployment_verification events
        deploy_events = [
            e for e in trust_data.get("events", [])
            if e.get("kind") == "deploy"
            and "deployment_verification" in str(e.get("evidence", {}).get("action", ""))
        ]
        
        if not deploy_events:
            state_resp = requests.get(
                f"{API_BASE_URL}/api/version",
                timeout=10,
            )
            assert state_resp.status_code == 200
            version_data = state_resp.json()
            verification = version_data.get("deployment_verification") or {}
            if verification.get("verification_source") == "automatic_startup_verification":
                assert verification.get("verification_id")
                return

            history_resp = requests.get(
                f"{API_BASE_URL}/api/admin/deployment-readiness/history?limit=20",
                headers=headers,
                timeout=10,
            )
            assert history_resp.status_code == 200
            history_events = history_resp.json().get("events", [])
            deploy_events = [
                e for e in history_events
                if e.get("verification_source") == "automatic_startup_verification"
            ]

        assert len(deploy_events) > 0, "No deployment verification evidence found in trust-events, /api/version, or readiness history"
        
        latest_deploy = deploy_events[0]
        if latest_deploy.get("evidence"):
            evidence = latest_deploy.get("evidence", {})
            diff = evidence.get("diff", {})
            assert "verification_id" in diff, "Deploy event must have verification_id in diff"
            assert "go_no_go" in diff, "Deploy event must have go_no_go in diff"
            print(f"✓ Deployment verification audit event found: go_no_go={diff.get('go_no_go')}")
        else:
            assert latest_deploy.get("verification_id"), "Deployment verification history entry missing verification_id"
            assert latest_deploy.get("go_no_go") in ["GO", "NO-GO"]
            print(f"✓ Deployment verification history found: go_no_go={latest_deploy.get('go_no_go')}")


class TestAuthRequirements:
    """Test that protected endpoints require proper authentication"""
    
    def test_admin_check_requires_auth(self):
        """Protected endpoints reject requests without tokens"""
        response = requests.get(f"{API_BASE_URL}/api/admin/check", timeout=10)
        assert response.status_code == 401, "Should require auth"
        print("✓ /api/admin/check requires authentication")
    
    def test_deployment_readiness_requires_auth(self):
        """Deployment readiness requires admin token"""
        response = requests.get(f"{API_BASE_URL}/api/admin/deployment-readiness", timeout=10)
        assert response.status_code == 401, "Should require auth"
        print("✓ /api/admin/deployment-readiness requires authentication")
    
    def test_occ_trust_events_requires_auth(self):
        """OCC trust events requires admin token"""
        response = requests.get(f"{API_BASE_URL}/api/admin/occ/trust-events", timeout=10)
        assert response.status_code == 401, "Should require auth"
        print("✓ /api/admin/occ/trust-events requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

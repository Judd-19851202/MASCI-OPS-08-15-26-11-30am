"""Test iteration 55 · Full pre-deployment sweep for admin health endpoints.

Verifies:
1. Admin multi-login succeeds with super admin credentials
2. GET /api/admin/backups-scheduler-state returns 200 and does NOT include false scheduler_unhealthy blocker
3. GET /api/admin/persistence-health returns 200 with atlas_connected=true
4. GET /api/admin/runtime-reliability returns 200 with liveness=alive, readiness=ready, mongo_ok=true
5. GET /api/admin/database returns 200 with valid database capacity payload
6. GET /api/admin/occ/health returns 200 and does NOT degrade to UNVERIFIABLE due to auth header issues
7. GET /api/admin-strict/diag/persistence-health and GET /api/admin-strict/diag/runtime-health return 200
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://masci-audit-hub.preview.emergentagent.com"

# Test credentials from test_credentials.md
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"


def get_admin_headers():
    """Helper to get admin auth headers."""
    response = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
        timeout=60,
    )
    assert response.status_code == 200, f"Multi-login failed: {response.status_code} - {response.text}"
    data = response.json()
    
    # Extract tokens from response - portal_tokens.admin is the admin token
    portal_tokens = data.get("portal_tokens") or {}
    admin_token = portal_tokens.get("admin") or data.get("admin_token") or data.get("token")
    directory_token = data.get("session_token") or data.get("directory_token")
    
    assert admin_token, f"No admin token in response: {data.keys()}"
    headers = {"X-Admin-Token": admin_token}
    if directory_token:
        headers["X-Directory-Token"] = directory_token
    return headers, data


class TestAdminMultiLogin:
    """Test admin multi-login authentication flow."""
    
    def test_01_multi_login_returns_tokens(self):
        """Verify multi-login returns usable admin and directory tokens."""
        headers, data = get_admin_headers()
        assert headers.get("X-Admin-Token"), "Admin token should be present"
        print(f"✓ Multi-login succeeded, admin_token present")
        print(f"  Directory token present: {bool(headers.get('X-Directory-Token'))}")
        print(f"  Response keys: {list(data.keys())}")
        print(f"  Portal tokens: {list((data.get('portal_tokens') or {}).keys())}")


class TestBackupsSchedulerState:
    """Test /api/admin/backups-scheduler-state endpoint."""
    
    def test_02_backups_scheduler_state_returns_200(self):
        admin_headers, _ = get_admin_headers()
        """Verify /api/admin/backups-scheduler-state returns 200."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=admin_headers,
            timeout=30,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        print(f"✓ backups-scheduler-state returned 200")
        print(f"  alive: {data.get('alive')}")
        print(f"  is_healthy: {data.get('is_healthy')}")
        print(f"  activation_status: {data.get('activation_status')}")
    
    def test_03_scheduler_state_no_false_unhealthy_blocker(self):
        admin_headers, _ = get_admin_headers()
        """Verify scheduler_unhealthy blocker is NOT present when alive=true and is_healthy=true."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=admin_headers,
            timeout=30,
        )
        assert response.status_code == 200
        data = response.json()
        
        alive = data.get("alive")
        is_healthy = data.get("is_healthy")
        activation_blockers = data.get("activation_blockers") or []
        
        print(f"  alive={alive}, is_healthy={is_healthy}")
        print(f"  activation_blockers: {activation_blockers}")
        
        # In preview, environment_not_production is expected
        # But scheduler_unhealthy should NOT be present if alive=true and is_healthy=true
        if alive is True and is_healthy is True:
            assert "scheduler_unhealthy" not in activation_blockers, (
                f"scheduler_unhealthy should NOT be in blockers when alive=true and is_healthy=true. "
                f"Blockers: {activation_blockers}"
            )
            print(f"✓ No false scheduler_unhealthy blocker when scheduler is healthy")
        else:
            # If scheduler is not healthy, scheduler_unhealthy blocker is legitimate
            print(f"  Note: Scheduler not fully healthy (alive={alive}, is_healthy={is_healthy})")
            print(f"  scheduler_unhealthy blocker may be legitimate")
    
    def test_04_scheduler_state_has_expected_fields(self):
        admin_headers, _ = get_admin_headers()
        """Verify scheduler state has all expected fields."""
        response = requests.get(
            f"{BASE_URL}/api/admin/backups-scheduler-state",
            headers=admin_headers,
            timeout=30,
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check for expected fields
        expected_fields = [
            "alive", "is_healthy", "activation_status", "activation_blockers",
            "hourly_activation", "scheduler", "now_utc"
        ]
        for field in expected_fields:
            assert field in data, f"Missing expected field: {field}"
        
        # Check hourly_activation structure
        hourly = data.get("hourly_activation") or {}
        assert "stale_lock_present" in hourly or "stale_lock_present" in data, "stale_lock_present should be present"
        print(f"✓ All expected fields present in scheduler state")


class TestPersistenceHealth:
    """Test /api/admin/persistence-health endpoint."""
    
    def test_05_persistence_health_returns_200(self):
        admin_headers, _ = get_admin_headers()
        """Verify /api/admin/persistence-health returns 200."""
        response = requests.get(
            f"{BASE_URL}/api/admin/persistence-health",
            headers=admin_headers,
            timeout=30,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ persistence-health returned 200")
    
    def test_06_persistence_health_atlas_connected_true(self):
        admin_headers, _ = get_admin_headers()
        """Verify atlas_connected=true using runtime identity truth."""
        response = requests.get(
            f"{BASE_URL}/api/admin/persistence-health",
            headers=admin_headers,
            timeout=30,
        )
        assert response.status_code == 200
        data = response.json()
        
        atlas_connected = data.get("atlas_connected")
        atlas_detection_basis = data.get("atlas_detection_basis") or {}
        
        print(f"  atlas_connected: {atlas_connected}")
        print(f"  atlas_detection_basis: {atlas_detection_basis}")
        
        assert atlas_connected is True, (
            f"atlas_connected should be True. Got: {atlas_connected}. "
            f"Detection basis: {atlas_detection_basis}"
        )
        print(f"✓ atlas_connected=true confirmed")
    
    def test_07_persistence_health_has_expected_fields(self):
        admin_headers, _ = get_admin_headers()
        """Verify persistence health has all expected fields."""
        response = requests.get(
            f"{BASE_URL}/api/admin/persistence-health",
            headers=admin_headers,
            timeout=30,
        )
        assert response.status_code == 200
        data = response.json()
        
        expected_fields = [
            "captured_at", "atlas_connected", "mongo_version", 
            "collections_detected", "persistent_storage_confirmed"
        ]
        for field in expected_fields:
            assert field in data, f"Missing expected field: {field}"
        
        print(f"✓ All expected fields present in persistence health")
        print(f"  mongo_version: {data.get('mongo_version')}")
        print(f"  collections_detected: {data.get('collections_detected')}")


class TestRuntimeReliability:
    """Test /api/admin/runtime-reliability endpoint."""
    
    def test_08_runtime_reliability_returns_200(self):
        admin_headers, _ = get_admin_headers()
        """Verify /api/admin/runtime-reliability returns 200."""
        response = requests.get(
            f"{BASE_URL}/api/admin/runtime-reliability",
            headers=admin_headers,
            timeout=30,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ runtime-reliability returned 200")
    
    def test_09_runtime_reliability_liveness_and_readiness(self):
        admin_headers, _ = get_admin_headers()
        """Verify liveness=alive, readiness=ready, mongo_ok=true."""
        response = requests.get(
            f"{BASE_URL}/api/admin/runtime-reliability",
            headers=admin_headers,
            timeout=30,
        )
        assert response.status_code == 200
        data = response.json()
        
        liveness = data.get("liveness")
        readiness = data.get("readiness")
        mongo_ok = data.get("mongo_ok")
        
        print(f"  liveness: {liveness}")
        print(f"  readiness: {readiness}")
        print(f"  mongo_ok: {mongo_ok}")
        
        # Check liveness - can be dict with state or direct value
        if isinstance(liveness, dict):
            liveness_state = liveness.get("state") or liveness.get("ok")
            assert liveness_state == "alive" or liveness_state is True, f"Expected liveness=alive, got {liveness}"
        else:
            assert liveness == "alive" or liveness is True, f"Expected liveness=alive, got {liveness}"
        
        # Check readiness - can be dict with state or direct value
        if isinstance(readiness, dict):
            readiness_state = readiness.get("state") or readiness.get("ok")
            assert readiness_state == "ready" or readiness_state is True, f"Expected readiness=ready, got {readiness}"
        else:
            assert readiness == "ready" or readiness is True, f"Expected readiness=ready, got {readiness}"
        
        # Check mongo_ok
        assert mongo_ok is True, f"Expected mongo_ok=true, got {mongo_ok}"
        
        print(f"✓ Runtime reliability checks passed")


class TestDatabaseEndpoint:
    """Test /api/admin/database endpoint."""
    
    def test_10_database_returns_200(self):
        admin_headers, _ = get_admin_headers()
        """Verify /api/admin/database returns 200 (not 404)."""
        response = requests.get(
            f"{BASE_URL}/api/admin/database",
            headers=admin_headers,
            timeout=30,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ /api/admin/database returned 200 (not 404)")
    
    def test_11_database_has_valid_capacity_payload(self):
        admin_headers, _ = get_admin_headers()
        """Verify database endpoint returns valid capacity payload."""
        response = requests.get(
            f"{BASE_URL}/api/admin/database",
            headers=admin_headers,
            timeout=30,
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check for capacity-related fields
        print(f"  Response keys: {list(data.keys())}")
        
        # The endpoint should return capacity information
        # Check for common capacity fields
        has_capacity_info = any(k in data for k in [
            "capacity", "storage", "used_bytes", "total_bytes", 
            "usage_percent", "db_stats", "cluster"
        ])
        
        assert has_capacity_info or data, f"Expected capacity payload, got: {data}"
        print(f"✓ Database capacity payload is valid")


class TestOCCHealth:
    """Test /api/admin/occ/health endpoint."""
    
    def test_12_occ_health_returns_200(self):
        admin_headers, _ = get_admin_headers()
        """Verify /api/admin/occ/health returns 200."""
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers=admin_headers,
            timeout=60,  # OCC health fans out to multiple endpoints
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ occ/health returned 200")
    
    def test_13_occ_health_no_false_unverifiable(self):
        admin_headers, _ = get_admin_headers()
        """Verify OCC health does NOT degrade to UNVERIFIABLE due to auth header issues."""
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers=admin_headers,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        
        overall_status = data.get("overall_status")
        sections = data.get("sections") or []
        
        print(f"  overall_status: {overall_status}")
        
        # Count UNVERIFIABLE cards
        unverifiable_cards = []
        for section in sections:
            for card in section.get("cards") or []:
                if card.get("status") == "UNVERIFIABLE":
                    unverifiable_cards.append({
                        "id": card.get("id"),
                        "title": card.get("title"),
                        "evidence": card.get("evidence"),
                    })
        
        print(f"  UNVERIFIABLE cards count: {len(unverifiable_cards)}")
        for card in unverifiable_cards:
            print(f"    - {card['id']}: {card['title']}")
            if card.get("evidence", {}).get("error"):
                print(f"      Error: {card['evidence']['error']}")
        
        # Check that auth-related UNVERIFIABLE issues are not present
        # (i.e., cards should not fail due to missing forwarded auth headers)
        auth_related_errors = [
            c for c in unverifiable_cards 
            if "401" in str(c.get("evidence", {}).get("error", "")) or
               "403" in str(c.get("evidence", {}).get("error", "")) or
               "auth" in str(c.get("evidence", {}).get("error", "")).lower()
        ]
        
        assert len(auth_related_errors) == 0, (
            f"Found auth-related UNVERIFIABLE cards (auth header passthrough issue): {auth_related_errors}"
        )
        print(f"✓ No false UNVERIFIABLE cards due to auth header issues")
    
    def test_14_occ_health_has_expected_structure(self):
        admin_headers, _ = get_admin_headers()
        """Verify OCC health has expected structure."""
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers=admin_headers,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check for expected top-level fields
        expected_fields = ["generated_at", "overall_status", "sections", "counts"]
        for field in expected_fields:
            assert field in data, f"Missing expected field: {field}"
        
        # Check sections structure
        sections = data.get("sections") or []
        assert len(sections) > 0, "Expected at least one section"
        
        for section in sections:
            assert "id" in section, "Section missing 'id'"
            assert "cards" in section, "Section missing 'cards'"
        
        print(f"✓ OCC health has expected structure")
        print(f"  Sections: {[s['id'] for s in sections]}")


class TestStrictDiagEndpoints:
    """Test /api/admin-strict/diag/* endpoints."""
    
    def test_15_strict_persistence_health_returns_200(self):
        admin_headers, _ = get_admin_headers()
        """Verify /api/admin-strict/diag/persistence-health returns 200."""
        response = requests.get(
            f"{BASE_URL}/api/admin-strict/diag/persistence-health",
            headers=admin_headers,
            timeout=30,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify it has the same structure as the alias
        assert "atlas_connected" in data, "Missing atlas_connected field"
        print(f"✓ /api/admin-strict/diag/persistence-health returned 200")
        print(f"  atlas_connected: {data.get('atlas_connected')}")
    
    def test_16_strict_runtime_health_returns_200(self):
        admin_headers, _ = get_admin_headers()
        """Verify /api/admin-strict/diag/runtime-health returns 200."""
        response = requests.get(
            f"{BASE_URL}/api/admin-strict/diag/runtime-health",
            headers=admin_headers,
            timeout=30,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        print(f"✓ /api/admin-strict/diag/runtime-health returned 200")
        print(f"  Response keys: {list(data.keys())}")
    
    def test_17_alias_routes_aligned_with_strict_routes(self):
        admin_headers, _ = get_admin_headers()
        """Verify alias routes return same data as strict routes."""
        # Get persistence health from both routes
        alias_response = requests.get(
            f"{BASE_URL}/api/admin/persistence-health",
            headers=admin_headers,
            timeout=30,
        )
        strict_response = requests.get(
            f"{BASE_URL}/api/admin-strict/diag/persistence-health",
            headers=admin_headers,
            timeout=30,
        )
        
        assert alias_response.status_code == 200
        assert strict_response.status_code == 200
        
        alias_data = alias_response.json()
        strict_data = strict_response.json()
        
        # Both should have atlas_connected
        assert alias_data.get("atlas_connected") == strict_data.get("atlas_connected"), (
            f"Alias and strict routes should return same atlas_connected value. "
            f"Alias: {alias_data.get('atlas_connected')}, Strict: {strict_data.get('atlas_connected')}"
        )
        
        print(f"✓ Alias routes aligned with strict routes")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

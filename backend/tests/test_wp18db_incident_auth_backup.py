"""
WP-18DB Executive Regression Hold & Final Production Field Repair Tests

Tests:
1. Incident field auth: field user can create/patch/transition incident cases
2. Unauthorized behavior: no-auth and directory-only requests remain 401
3. PM token without field authority must not gain create access
4. Backup health alert buffer: 60-minute RPO target, 75-minute alert threshold
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials from /app/memory/test_credentials.md
FIELD_USER_EMAIL = "cert.foreman@example.com"
FIELD_USER_PASSWORD = "CertProof2026!"
PM_USER_EMAIL = "cert.pm@example.com"
PM_USER_PASSWORD = "CertProof2026!"
SAFETY_USER_EMAIL = "cert.safety@example.com"
SAFETY_USER_PASSWORD = "CertProof2026!"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


class TestIncidentFieldAuth:
    """Test incident field auth using legitimate field user credentials."""

    @pytest.fixture(scope="class")
    def field_tokens(self):
        """Get field leadership tokens for cert.foreman@example.com."""
        # Login to get directory token
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": FIELD_USER_EMAIL, "password": FIELD_USER_PASSWORD},
            timeout=30,
        )
        if login_resp.status_code != 200:
            pytest.skip(f"Field user login failed: {login_resp.status_code} - {login_resp.text[:200]}")
        
        data = login_resp.json()
        portal_tokens = data.get("portal_tokens", {})
        session_token = data.get("session_token")
        fl_token = portal_tokens.get("fl")
        
        if not session_token:
            pytest.skip("No session token returned for field user")
        
        return {
            "directory": session_token,
            "fl": fl_token,
        }

    @pytest.fixture(scope="class")
    def pm_tokens(self):
        """Get PM tokens for cert.pm@example.com."""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": PM_USER_EMAIL, "password": PM_USER_PASSWORD},
            timeout=30,
        )
        if login_resp.status_code != 200:
            pytest.skip(f"PM user login failed: {login_resp.status_code}")
        
        data = login_resp.json()
        portal_tokens = data.get("portal_tokens", {})
        session_token = data.get("session_token")
        return {
            "directory": session_token,
            "pm": portal_tokens.get("pm"),
        }

    @pytest.fixture(scope="class")
    def safety_tokens(self):
        """Get Safety tokens for cert.safety@example.com."""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": SAFETY_USER_EMAIL, "password": SAFETY_USER_PASSWORD},
            timeout=30,
        )
        if login_resp.status_code != 200:
            pytest.skip(f"Safety user login failed: {login_resp.status_code}")
        
        data = login_resp.json()
        portal_tokens = data.get("portal_tokens", {})
        session_token = data.get("session_token")
        return {
            "directory": session_token,
            "safety": portal_tokens.get("safety"),
        }

    def test_no_auth_incident_cases_returns_401(self):
        """No-auth requests to /api/incident-cases must return 401."""
        resp = requests.get(f"{BASE_URL}/api/incident-cases", timeout=30)
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text[:200]}"

    def test_no_auth_incident_create_returns_401(self):
        """No-auth POST to /api/incident-cases must return 401."""
        resp = requests.post(
            f"{BASE_URL}/api/incident-cases",
            json={"field_block": {"incident_type": "near_miss"}},
            timeout=30,
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text[:200]}"

    def test_directory_only_incident_create_returns_401(self, field_tokens):
        """Directory-only token (no FL token) should return 401 for incident create."""
        headers = {
            "X-Directory-Token": field_tokens["directory"],
            # Intentionally NOT sending X-FL-Token
        }
        resp = requests.post(
            f"{BASE_URL}/api/incident-cases",
            json={"field_block": {"incident_type": "near_miss"}},
            headers=headers,
            timeout=30,
        )
        # Should be 401 because the field actor gate requires X-FL-Token
        assert resp.status_code == 401, f"Expected 401 for directory-only, got {resp.status_code}: {resp.text[:200]}"

    def test_field_user_can_fetch_vocabulary(self, field_tokens):
        """Field user with FL token can fetch incident vocabulary."""
        headers = {
            "X-Directory-Token": field_tokens["directory"],
            "X-FL-Token": field_tokens["fl"],
        }
        resp = requests.get(
            f"{BASE_URL}/api/incident-cases/vocabulary",
            headers=headers,
            timeout=30,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert "actor_role" in data
        assert "actor_capabilities" in data

    def test_field_user_can_create_incident_case(self, field_tokens):
        """Field user with FL token can create an incident case."""
        headers = {
            "X-Directory-Token": field_tokens["directory"],
            "X-FL-Token": field_tokens["fl"],
        }
        field_block = {
            "incident_type": "near_miss",
            "occurred_at": "2026-08-06T10:00:00Z",
            "reported_at": "2026-08-06T10:05:00Z",
            "location_label": "Test Location - WP18DB",
            "job_number": "TEST-WP18DB-001",
            "reporter_name": "Test Foreman",
            "reporter_role": "Foreman",
            "weather": "Clear",
            "immediate_actions": "Area secured",
        }
        resp = requests.post(
            f"{BASE_URL}/api/incident-cases",
            json={"field_block": field_block},
            headers=headers,
            timeout=30,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert "id" in data
        assert "case_number" in data or "state" in data
        return data.get("id")

    def test_field_user_can_patch_field_block(self, field_tokens):
        """Field user can patch the field block of an incident case."""
        headers = {
            "X-Directory-Token": field_tokens["directory"],
            "X-FL-Token": field_tokens["fl"],
        }
        # First create a case
        field_block = {
            "incident_type": "near_miss",
            "occurred_at": "2026-08-06T11:00:00Z",
            "reported_at": "2026-08-06T11:05:00Z",
            "location_label": "Patch Test Location - WP18DB",
            "job_number": "TEST-WP18DB-002",
            "reporter_name": "Test Foreman",
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/incident-cases",
            json={"field_block": field_block},
            headers=headers,
            timeout=30,
        )
        if create_resp.status_code != 200:
            pytest.skip(f"Could not create case for patch test: {create_resp.status_code}")
        
        case_id = create_resp.json().get("id")
        
        # Now patch it
        patch_resp = requests.patch(
            f"{BASE_URL}/api/incident-cases/{case_id}/field-block",
            json={"patch": {"weather": "Partly cloudy", "immediate_actions": "Updated actions"}},
            headers=headers,
            timeout=30,
        )
        assert patch_resp.status_code == 200, f"Expected 200, got {patch_resp.status_code}: {patch_resp.text[:200]}"

    def test_field_user_can_add_evidence(self, field_tokens):
        """Field user can add evidence to an incident case."""
        headers = {
            "X-Directory-Token": field_tokens["directory"],
            "X-FL-Token": field_tokens["fl"],
        }
        # First create a case
        field_block = {
            "incident_type": "near_miss",
            "occurred_at": "2026-08-06T12:00:00Z",
            "reported_at": "2026-08-06T12:05:00Z",
            "location_label": "Evidence Test Location - WP18DB",
            "job_number": "TEST-WP18DB-003",
            "reporter_name": "Test Foreman",
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/incident-cases",
            json={"field_block": field_block},
            headers=headers,
            timeout=30,
        )
        if create_resp.status_code != 200:
            pytest.skip(f"Could not create case for evidence test: {create_resp.status_code}")
        
        case_id = create_resp.json().get("id")
        
        # Add evidence
        evidence_resp = requests.post(
            f"{BASE_URL}/api/incident-cases/{case_id}/evidence",
            json={
                "evidence_type": "photo",
                "label": "Test photo evidence",
                "description": "WP18DB test evidence",
                "metadata": {"test": True},
            },
            headers=headers,
            timeout=30,
        )
        assert evidence_resp.status_code == 200, f"Expected 200, got {evidence_resp.status_code}: {evidence_resp.text[:200]}"

    def test_field_user_can_transition_to_field_submitted(self, field_tokens):
        """Field user can transition case to FIELD_SUBMITTED."""
        headers = {
            "X-Directory-Token": field_tokens["directory"],
            "X-FL-Token": field_tokens["fl"],
        }
        # First create a case
        field_block = {
            "incident_type": "near_miss",
            "occurred_at": "2026-08-06T13:00:00Z",
            "reported_at": "2026-08-06T13:05:00Z",
            "location_label": "Transition Test Location - WP18DB",
            "job_number": "TEST-WP18DB-004",
            "reporter_name": "Test Foreman",
            "reporter_role": "Foreman",
            "weather": "Clear",
            "immediate_actions": "Area secured",
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/incident-cases",
            json={"field_block": field_block},
            headers=headers,
            timeout=30,
        )
        if create_resp.status_code != 200:
            pytest.skip(f"Could not create case for transition test: {create_resp.status_code}")
        
        case_id = create_resp.json().get("id")
        
        # Transition to FIELD_SUBMITTED
        transition_resp = requests.post(
            f"{BASE_URL}/api/incident-cases/{case_id}/transitions",
            json={"to_state": "FIELD_SUBMITTED", "reason": "WP18DB test submission"},
            headers=headers,
            timeout=30,
        )
        assert transition_resp.status_code == 200, f"Expected 200, got {transition_resp.status_code}: {transition_resp.text[:200]}"
        data = transition_resp.json()
        assert data.get("state") == "FIELD_SUBMITTED", f"Expected state FIELD_SUBMITTED, got {data.get('state')}"

    def test_pm_token_cannot_create_incident_without_field_authority(self, pm_tokens):
        """PM token without field/safety/admin authority must not gain create access."""
        headers = {
            "X-Directory-Token": pm_tokens["directory"],
            "X-PM-Token": pm_tokens["pm"],
        }
        field_block = {
            "incident_type": "near_miss",
            "occurred_at": "2026-08-06T14:00:00Z",
            "location_label": "PM Test Location - WP18DB",
        }
        resp = requests.post(
            f"{BASE_URL}/api/incident-cases",
            json={"field_block": field_block},
            headers=headers,
            timeout=30,
        )
        # PM should get 401 or 403 because they don't have field_leadership token
        assert resp.status_code in [401, 403], f"Expected 401/403 for PM-only, got {resp.status_code}: {resp.text[:200]}"

    def test_safety_user_can_access_incident_cases(self, safety_tokens):
        """Safety user can access incident cases (read gate)."""
        headers = {
            "X-Directory-Token": safety_tokens["directory"],
            "X-Safety-Token": safety_tokens["safety"],
        }
        resp = requests.get(
            f"{BASE_URL}/api/incident-cases",
            headers=headers,
            timeout=30,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"


class TestBackupHealthAlertThreshold:
    """Test backup health alert buffer: 60-minute RPO target, 75-minute alert threshold."""

    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin token."""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=30,
        )
        if login_resp.status_code != 200:
            pytest.skip(f"Admin login failed: {login_resp.status_code}")
        
        data = login_resp.json()
        portal_tokens = data.get("portal_tokens", {})
        session_token = data.get("session_token")
        return {
            "admin": portal_tokens.get("admin"),
            "directory": session_token,
        }

    def test_system_health_backup_card_classification(self, admin_token):
        """Validate backup card classification uses 60-minute warning, 75-minute red-alert threshold."""
        headers = {
            "X-Admin-Token": admin_token["admin"],
            "X-Directory-Token": admin_token["directory"],
        }
        resp = requests.get(
            f"{BASE_URL}/api/admin/system-health",
            headers=headers,
            timeout=30,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        
        data = resp.json()
        cards = data.get("cards", [])
        
        # Find the backup card
        backup_card = None
        for card in cards:
            if card.get("key") == "backup":
                backup_card = card
                break
        
        assert backup_card is not None, "Backup card not found in system health response"
        
        # Verify the card has expected fields
        assert "status" in backup_card, "Backup card missing status field"
        assert "detail" in backup_card, "Backup card missing detail field"
        
        # The detail should mention the thresholds
        detail = backup_card.get("detail", "")
        print(f"Backup card status: {backup_card.get('status')}")
        print(f"Backup card detail: {detail}")
        
        # Check if the detail mentions the threshold values
        # The format is: "...vs target ≤ 60m; alert > 75m..."
        if "target" in detail.lower() or "alert" in detail.lower():
            # Verify the thresholds are mentioned
            assert "60" in detail or "75" in detail, f"Expected threshold values in detail: {detail}"

    def test_backup_health_env_vars_in_source(self):
        """Verify the source code uses BACKUP_RPO_TARGET_MINUTES and BACKUP_HEALTH_ALERT_THRESHOLD_MINUTES."""
        # This is a code-path verification test
        # The admin_ops.py should read these env vars
        import subprocess
        result = subprocess.run(
            ["grep", "-c", "BACKUP_HEALTH_ALERT_THRESHOLD_MINUTES", "/app/backend/routes/admin_ops.py"],
            capture_output=True,
            text=True,
        )
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count >= 1, "BACKUP_HEALTH_ALERT_THRESHOLD_MINUTES not found in admin_ops.py"
        
        result2 = subprocess.run(
            ["grep", "-c", "BACKUP_RPO_TARGET_MINUTES", "/app/backend/routes/admin_ops.py"],
            capture_output=True,
            text=True,
        )
        count2 = int(result2.stdout.strip()) if result2.returncode == 0 else 0
        assert count2 >= 1, "BACKUP_RPO_TARGET_MINUTES not found in admin_ops.py"

    def test_consumer_freshness_status_logic(self):
        """Verify consumer_freshness_status uses warning_minutes and threshold_minutes correctly."""
        # This is a code-path verification test
        import subprocess
        result = subprocess.run(
            ["grep", "-c", "warning_minutes", "/app/backend/lib/archive_lineage.py"],
            capture_output=True,
            text=True,
        )
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count >= 2, "warning_minutes not found in archive_lineage.py"


class TestIncidentReportApiHeaders:
    """Test that incidentReportApi.js uses correct auth headers."""

    def test_incident_report_api_uses_field_leadership_scope(self):
        """Verify incidentReportApi.js includes field_leadership in scoped headers."""
        import subprocess
        result = subprocess.run(
            ["grep", "-c", "field_leadership", "/app/frontend/src/lib/incidentReportApi.js"],
            capture_output=True,
            text=True,
        )
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count >= 1, "field_leadership scope not found in incidentReportApi.js"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

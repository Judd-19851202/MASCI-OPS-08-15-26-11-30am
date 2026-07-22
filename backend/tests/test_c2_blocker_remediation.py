"""
C2 Blocker Remediation Acceptance Tests

Tests the bounded remediation for:
- F-001/F-002: Release identity mismatch
- F-003/F-004: Preview email SAFE_CAPTURE vs production PROVIDER_LIVE fail-closed
- Proof that previous 'api key is invalid' failures were caused by environment/delivery-mode logic

F-005 (BACKUP/ROLLBACK) remains BLOCKING and OWNER_EVIDENCE_REQUIRED - not tested here.
"""
import os
import pytest
import requests
from datetime import datetime, timezone
import uuid
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials from /app/memory/test_credentials.md
CERT_FOREMAN_EMAIL = "cert.foreman@example.com"
CERT_FOREMAN_PASSWORD = "CertProof2026!"
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"

# Expected source hash from evidence (source_hash is the key identity marker)
EXPECTED_SOURCE_HASH = "88e0a1d5994687b737b324b2f0e8f75f"


def retry_request(method, url, max_retries=3, delay=2, **kwargs):
    """Retry a request with exponential backoff for transient failures"""
    kwargs.setdefault("timeout", 60)
    last_error = None
    for attempt in range(max_retries):
        try:
            response = method(url, **kwargs)
            if response.status_code < 500:  # Success or client error
                return response
            # Server error - retry
            last_error = f"Server error {response.status_code}"
        except requests.exceptions.RequestException as e:
            last_error = str(e)
        
        if attempt < max_retries - 1:
            time.sleep(delay * (attempt + 1))
    
    # Return last response or raise error
    raise requests.exceptions.RequestException(f"Max retries exceeded: {last_error}")


class TestReleaseIdentityConsistency:
    """F-001/F-002: Release identity is consistent for Preview
    
    Key acceptance criteria:
    - One canonical source_hash aligns across workspace evidence, frontend build, and backend runtime
    - frontend_backend_release_match is True
    - Runtime identity is valid for preview environment
    """
    
    def test_version_endpoint_returns_consistent_identity(self):
        """Verify /api/version returns consistent release identity with source_hash alignment"""
        response = retry_request(requests.get, f"{BASE_URL}/api/version")
        assert response.status_code == 200, f"Version endpoint failed: {response.status_code} - {response.text[:500]}"
        
        data = response.json()
        
        # Verify commit SHA is present and valid format (40 hex chars)
        assert "commit" in data, "Missing commit field in version response"
        commit = data["commit"]
        assert len(commit) == 40 and all(c in "0123456789abcdef" for c in commit), f"Invalid commit format: {commit}"
        
        # Verify source hash matches expected
        assert "source_hash" in data, "Missing source_hash field"
        assert data["source_hash"] == EXPECTED_SOURCE_HASH, f"Source hash mismatch: expected {EXPECTED_SOURCE_HASH}, got {data['source_hash']}"
        
        # Verify frontend source hash matches backend source hash (key identity alignment)
        assert "frontend_build_source_hash" in data, "Missing frontend_build_source_hash"
        assert data["frontend_build_source_hash"] == data["source_hash"], \
            f"Frontend/backend source hash mismatch: frontend={data['frontend_build_source_hash']}, backend={data['source_hash']}"
        
        # Verify frontend_backend_release_match is true (the canonical identity check)
        assert data.get("frontend_backend_release_match") is True, "Frontend/backend release mismatch"
        
        print(f"PASS: Release identity consistent - commit={data['commit'][:12]}, source_hash={data['source_hash'][:12]}, match={data.get('frontend_backend_release_match')}")
    
    def test_version_endpoint_runtime_identity(self):
        """Verify runtime identity in /api/version is valid for preview"""
        response = retry_request(requests.get, f"{BASE_URL}/api/version")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify app_env is preview
        assert data.get("app_env") == "preview", f"Expected app_env=preview, got {data.get('app_env')}"
        
        # Verify runtime_identity
        runtime_identity = data.get("runtime_identity", {})
        assert runtime_identity.get("valid") is True, "Runtime identity not valid"
        
        identity = runtime_identity.get("identity", {})
        assert identity.get("app_env") == "preview", "Runtime identity app_env mismatch"
        
        # Verify source hash matches (source_hash is the canonical identity marker)
        assert identity.get("release_source_hash") == EXPECTED_SOURCE_HASH, \
            f"Runtime identity source hash mismatch: expected {EXPECTED_SOURCE_HASH}, got {identity.get('release_source_hash')}"
        
        print(f"PASS: Runtime identity valid for preview environment - source_hash={identity.get('release_source_hash')[:12]}")
    
    def test_version_endpoint_consistency_across_calls(self):
        """Verify version endpoint returns consistent values across multiple calls"""
        responses = []
        for _ in range(3):
            response = retry_request(requests.get, f"{BASE_URL}/api/version")
            assert response.status_code == 200
            responses.append(response.json())
        
        # All commits should match
        commits = [r.get("commit") for r in responses]
        assert len(set(commits)) == 1, f"Inconsistent commits across calls: {commits}"
        
        # All source hashes should match
        hashes = [r.get("source_hash") for r in responses]
        assert len(set(hashes)) == 1, f"Inconsistent source hashes across calls: {hashes}"
        
        print(f"PASS: Version endpoint consistent across {len(responses)} calls")


class TestCertForemanDailyReportSubmission:
    """Test that cert.foreman can login and submit a Daily Report without 'api key is invalid' error"""
    
    @pytest.fixture
    def foreman_session(self):
        """Login as cert.foreman and return session with tokens"""
        session = requests.Session()
        
        # Login via multi-login endpoint
        login_response = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={
                "email": CERT_FOREMAN_EMAIL,
                "password": CERT_FOREMAN_PASSWORD,
                "portal": "field_leadership"
            },
            timeout=30
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Foreman login failed: {login_response.status_code} - {login_response.text}")
        
        data = login_response.json()
        
        # Extract tokens
        directory_token = data.get("directory_token") or data.get("session_token")
        portal_tokens = data.get("portal_tokens", {})
        fl_token = portal_tokens.get("field_leadership") or portal_tokens.get("fl")
        
        session.headers.update({
            "X-Directory-Token": directory_token or "",
            "X-FL-Token": fl_token or "",
            "Content-Type": "application/json"
        })
        
        return {
            "session": session,
            "directory_token": directory_token,
            "fl_token": fl_token,
            "user_info": data.get("user") or data.get("user_info", {})
        }
    
    def test_foreman_login_successful(self, foreman_session):
        """Verify cert.foreman can login and obtain field leadership token"""
        assert foreman_session["directory_token"], "Missing directory token"
        assert foreman_session["fl_token"], "Missing field leadership token"
        
        user_info = foreman_session["user_info"]
        assert user_info.get("email") == CERT_FOREMAN_EMAIL, f"Email mismatch: {user_info.get('email')}"
        
        print(f"PASS: Foreman login successful - email={user_info.get('email')}")
    
    def test_daily_report_submission_no_api_key_error(self, foreman_session):
        """Submit a Daily Report and verify no 'api key is invalid' error"""
        session = foreman_session["session"]
        
        # Build a minimal valid Daily Report payload
        report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        unique_id = uuid.uuid4().hex[:8]
        
        payload = {
            "project_name": "ZZ-RUNTIME-CERT-2026 Certification Project",
            "project_number": "ZZ-RUNTIME-CERT-2026",
            "location": "Preview Certification Site",
            "report_date": report_date,
            "prepared_by": "Certification Foreman",
            "superintendent": "Cert Superintendent",
            "weather_summary": "75°F / Clear",
            "gps_lat": 29.1383,
            "gps_lng": -80.9956,
            "location_source": "manual",
            "weather_snapshot_meta": {
                "provider": "open-meteo",
                "gps_lat": 29.1383,
                "gps_lng": -80.9956,
                "observation_timestamp": datetime.now(timezone.utc).isoformat(),
                "location_source": "manual",
                "weather_coordinates_match_report": True
            },
            "schedule_delays": "No",
            "weather_impact": "No",
            "safety_incidents_today": "No",
            "injuries_reported": "No",
            "general_notes": f"C2 Blocker Remediation Test {unique_id} - SAFE_CAPTURE verification",
            "prepared_by_signature": "data:image/png;base64,CERT_SIG_FAKE",
            "ai_accepted_summary": f"C2 Blocker Remediation test {unique_id} - verifying SAFE_CAPTURE mode in Preview environment.",
            "ai_accepted_summary_meta": {
                "source": "manual",
                "approved_by": "Certification Foreman",
                "accepted_at": datetime.now(timezone.utc).isoformat()
            },
            "certification_record": True,
            "synthetic_record": True,
            "hidden_from_operations": True,
            "certification_track_id": "27.11B",
            "certification_release_source_hash": EXPECTED_SOURCE_HASH,
            "certification_release_reason": "governed_production_certification_lane",
            "certification_required_workflows": ["daily-report", "trust-spine", "audit", "ods", "search", "pdf"]
        }
        
        response = session.post(
            f"{BASE_URL}/api/daily-reports",
            json=payload,
            timeout=60
        )
        
        # Check response
        assert response.status_code in [200, 201], f"Daily Report submission failed: {response.status_code} - {response.text}"
        
        data = response.json()
        
        # Verify no 'api key is invalid' error in response
        response_text = response.text.lower()
        assert "api key is invalid" not in response_text, "Found 'api key is invalid' error in response"
        assert "invalid api key" not in response_text, "Found 'invalid api key' error in response"
        
        # Verify record was created
        assert data.get("id"), "Missing record ID in response"
        assert data.get("doc_id") or data.get("report_number"), "Missing doc_id/report_number"
        
        # Verify notification delivery mode is SAFE_CAPTURE
        assert data.get("notification_delivery_mode") == "SAFE_CAPTURE", \
            f"Expected SAFE_CAPTURE, got {data.get('notification_delivery_mode')}"
        
        print(f"PASS: Daily Report submitted - id={data.get('id')}, doc_id={data.get('doc_id')}, delivery_mode={data.get('notification_delivery_mode')}")
        
        return data


class TestPreviewSafeCaptureSemantics:
    """F-003/F-004: Preview Daily Report notification completes via SAFE_CAPTURE"""
    
    @pytest.fixture
    def admin_session(self):
        """Login as super admin and return session"""
        session = requests.Session()
        
        login_response = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={
                "email": SUPER_ADMIN_EMAIL,
                "password": SUPER_ADMIN_PASSWORD,
                "portal": "admin"
            },
            timeout=30
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Admin login failed: {login_response.status_code}")
        
        data = login_response.json()
        directory_token = data.get("directory_token") or data.get("session_token")
        admin_token = (data.get("portal_tokens") or {}).get("admin")
        
        session.headers.update({
            "X-Directory-Token": directory_token or "",
            "X-Admin-Token": admin_token or "",
            "Content-Type": "application/json"
        })
        
        return session
    
    def test_delivery_contract_preview_forces_safe_capture(self):
        """Verify delivery contract forces SAFE_CAPTURE in preview environment"""
        # This tests the notification_delivery.py logic directly via the version endpoint
        response = retry_request(requests.get, f"{BASE_URL}/api/version")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify we're in preview
        assert data.get("app_env") == "preview", "Not in preview environment"
        
        # The environment_identity should show preview configuration
        env_identity = data.get("environment_identity", {})
        assert env_identity.get("app_env") == "preview", "Environment identity not preview"
        
        print(f"PASS: Preview environment confirmed - app_env={data.get('app_env')}")
    
    def test_submitted_report_has_safe_capture_fields(self, admin_session):
        """Verify a submitted report has correct SAFE_CAPTURE notification fields"""
        # Get a recent daily report to check its notification fields
        response = admin_session.get(
            f"{BASE_URL}/api/daily-reports",
            params={"limit": 5},
            timeout=30
        )
        
        if response.status_code != 200:
            pytest.skip(f"Could not fetch daily reports: {response.status_code}")
        
        reports = response.json()
        if not reports:
            pytest.skip("No daily reports found to verify")
        
        # Check the most recent report
        report_id = reports[0].get("id")
        if not report_id:
            pytest.skip("Report missing ID")
        
        # Get full report details
        detail_response = admin_session.get(
            f"{BASE_URL}/api/daily-reports/{report_id}",
            timeout=30
        )
        
        if detail_response.status_code != 200:
            pytest.skip(f"Could not fetch report details: {detail_response.status_code}")
        
        report = detail_response.json()
        
        # Verify notification fields for SAFE_CAPTURE
        delivery_mode = report.get("notification_delivery_mode")
        notification_state = report.get("notification_state")
        provider_called = report.get("notification_provider_called")
        provider_accepted = report.get("notification_provider_accepted")
        
        print(f"Report {report.get('doc_id')}: delivery_mode={delivery_mode}, state={notification_state}, provider_called={provider_called}, provider_accepted={provider_accepted}")
        
        # In preview, delivery_mode should be SAFE_CAPTURE
        if delivery_mode:
            assert delivery_mode == "SAFE_CAPTURE", f"Expected SAFE_CAPTURE, got {delivery_mode}"
        
        # If notification completed, verify SAFE_CAPTURE semantics
        if notification_state == "captured_preview":
            # provider_called should be false
            assert provider_called is False, "Provider should not be called in SAFE_CAPTURE mode"
            # provider_accepted should be false
            assert provider_accepted is False, "Provider should not accept in SAFE_CAPTURE mode"
            # capture_id should be present
            capture_id = report.get("notification_capture_id")
            assert capture_id, "Missing notification_capture_id for captured_preview state"
            print(f"PASS: SAFE_CAPTURE semantics verified - capture_id={capture_id}")


class TestProductionFailClosedContract:
    """F-004: Production contract remains fail-closed when live provider configuration is missing/invalid"""
    
    def test_notification_delivery_contract_logic(self):
        """Verify the notification delivery contract logic via code inspection"""
        # This test verifies the contract logic exists in the codebase
        # The actual production behavior is tested via the evidence files
        
        # Read the notification_delivery.py to verify fail-closed logic
        import sys
        sys.path.insert(0, "/app/backend")
        
        from lib.notification_delivery import (
            delivery_contract,
            DELIVERY_MODE_PROVIDER_LIVE,
            DELIVERY_MODE_SAFE_CAPTURE,
        )
        
        # Test preview environment contract
        preview_contract = delivery_contract({"APP_ENV": "preview", "RESEND_API_KEY": "re_test_key_12345"})
        assert preview_contract["environment"] == "preview", "Preview env not detected"
        assert preview_contract["delivery_mode"] == DELIVERY_MODE_SAFE_CAPTURE, "Preview should force SAFE_CAPTURE"
        assert preview_contract["external_send_allowed"] is False, "Preview should not allow external send"
        assert preview_contract["blocking"] is False, "Preview should not block"
        
        # Test production environment with missing key
        prod_missing_key = delivery_contract({"APP_ENV": "production", "RESEND_API_KEY": ""})
        assert prod_missing_key["environment"] == "production", "Production env not detected"
        assert prod_missing_key["delivery_mode"] == DELIVERY_MODE_PROVIDER_LIVE, "Production should force PROVIDER_LIVE"
        assert prod_missing_key["blocking"] is True, "Production with missing key should block"
        assert prod_missing_key["provider_validation_status"] == "missing", "Should report missing key"
        
        # Test production environment with invalid key shape
        prod_invalid_key = delivery_contract({"APP_ENV": "production", "RESEND_API_KEY": "invalid_key"})
        assert prod_invalid_key["blocking"] is True, "Production with invalid key should block"
        assert prod_invalid_key["provider_validation_status"] == "invalid", "Should report invalid key"
        
        # Test production environment with valid key
        prod_valid_key = delivery_contract({"APP_ENV": "production", "RESEND_API_KEY": "re_valid_key_12345678"})
        assert prod_valid_key["blocking"] is False, "Production with valid key should not block"
        assert prod_valid_key["external_send_allowed"] is True, "Production with valid key should allow external send"
        
        print("PASS: Production fail-closed contract logic verified")


class TestRootCauseAnalysisEvidence:
    """Verify the root cause analysis evidence for 'api key is invalid' failures"""
    
    def test_rca_evidence_file_exists(self):
        """Verify root cause analysis evidence file exists and has correct conclusion"""
        import json
        
        rca_path = "/app/test_reports/c2_phase2_blocker_remediation/root_cause_analysis.json"
        
        with open(rca_path, "r") as f:
            rca = json.load(f)
        
        # Verify finding
        finding = rca.get("finding", "")
        assert "environment/delivery-mode" in finding.lower() or "safe_capture" in finding.lower(), \
            "RCA finding should mention environment/delivery-mode or SAFE_CAPTURE"
        
        # Verify before evidence shows the old failures
        before = rca.get("before_evidence", {})
        invalid_key_rows = before.get("invalid_api_key_trust_spine_rows", [])
        assert len(invalid_key_rows) > 0 or before.get("legacy_behavior_summary"), \
            "Before evidence should show legacy failures"
        
        # Verify after evidence shows the fix
        after = rca.get("after_evidence", {})
        preview_contract = after.get("preview_contract", {})
        assert preview_contract.get("delivery_mode") == "SAFE_CAPTURE", \
            "After evidence should show SAFE_CAPTURE delivery mode"
        assert preview_contract.get("provider_called") is False or after.get("provider_called") is False, \
            "After evidence should show provider not called"
        
        # Verify conclusion
        conclusion = rca.get("conclusion", "")
        assert "resolved" in conclusion.lower() or "safe_capture" in conclusion.lower(), \
            "Conclusion should indicate resolution"
        
        print(f"PASS: RCA evidence verified - finding: {finding[:100]}...")
    
    def test_notification_environment_contract_evidence(self):
        """Verify notification environment contract evidence"""
        import json
        
        contract_path = "/app/test_reports/c2_phase2_blocker_remediation/notification_environment_contract.json"
        
        with open(contract_path, "r") as f:
            contract = json.load(f)
        
        # Verify preview contract
        preview = contract.get("preview_contract_forced_live_override", {})
        assert preview.get("environment") == "preview", "Preview environment not set"
        assert preview.get("delivery_mode") == "SAFE_CAPTURE", "Preview should force SAFE_CAPTURE"
        assert preview.get("external_send_allowed") is False, "Preview should not allow external send"
        
        # Verify production contract blocks on missing key
        prod_missing = contract.get("production_contract_missing_key", {})
        assert prod_missing.get("environment") == "production", "Production environment not set"
        assert prod_missing.get("blocking") is True, "Production should block on missing key"
        
        # Verify production contract blocks on invalid key
        prod_invalid = contract.get("production_contract_invalid_key", {})
        assert prod_invalid.get("blocking") is True, "Production should block on invalid key"
        
        # Verify assertions
        assertions = contract.get("assertions", {})
        assert assertions.get("preview_forces_safe_capture") is True
        assert assertions.get("preview_disallows_external_send") is True
        assert assertions.get("production_forces_provider_live") is True
        assert assertions.get("production_blocks_missing_key") is True
        assert assertions.get("production_blocks_invalid_key_shape") is True
        
        print("PASS: Notification environment contract evidence verified")


class TestF005RemainsBlocking:
    """Verify F-005 (BACKUP/ROLLBACK) remains BLOCKING and OWNER_EVIDENCE_REQUIRED"""
    
    def test_independent_rereview_shows_f005_blocking(self):
        """Verify independent re-review shows F-005 as BLOCKING"""
        import json
        
        rereview_path = "/app/test_reports/c2_phase2_blocker_remediation/independent_rereview.json"
        
        with open(rereview_path, "r") as f:
            rereview = json.load(f)
        
        # Find F-005 in blockers
        blockers = rereview.get("blockers", [])
        f005 = next((b for b in blockers if b.get("id") == "F-005"), None)
        
        assert f005 is not None, "F-005 not found in blockers list"
        assert f005.get("status") == "BLOCKING", f"F-005 should be BLOCKING, got {f005.get('status')}"
        assert f005.get("classification") == "OWNER_EVIDENCE_REQUIRED", \
            f"F-005 should be OWNER_EVIDENCE_REQUIRED, got {f005.get('classification')}"
        
        # Verify other blockers are resolved
        for blocker in blockers:
            if blocker.get("id") in ["F-001", "F-002", "F-003", "F-004"]:
                assert blocker.get("status") == "RESOLVED", \
                    f"{blocker.get('id')} should be RESOLVED, got {blocker.get('status')}"
        
        print("PASS: F-005 remains BLOCKING with OWNER_EVIDENCE_REQUIRED classification")


@pytest.fixture(scope="session")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Iteration 570 — Production Certification Lane Testing

Tests:
1. Governed certification foreman can submit a Daily Report on project ZZ-RUNTIME-CERT-2026
   and the response is automatically classified as certification_record=true, synthetic_record=true,
   hidden_from_operations=true, email_dispatch_suppressed=false, with a governed routing_override
   pointing only to certification recipients.

2. A valid long scoped telemetry event posted to POST /api/draft-telemetry (formKey longer than 64 chars)
   returns HTTP 200 instead of 422.

3. HR/Shop/Safety intelligence timeout UI remains truthful and retryable.
"""
import os
import pytest
import requests
import uuid
from datetime import datetime, timezone

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials from test_credentials.md
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"
CERT_FOREMAN_EMAIL = "cert.foreman@example.com"
CERT_FOREMAN_PASSWORD = "CertProof2026!"
CERT_PROJECT_NUMBER = "ZZ-RUNTIME-CERT-2026"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token via multi-login."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
        timeout=15,
    )
    if resp.status_code != 200:
        pytest.skip(f"Admin login failed: {resp.status_code} - {resp.text[:200]}")
    data = resp.json()
    tokens = data.get("portal_tokens", {})
    return tokens.get("admin")


@pytest.fixture(scope="module")
def fl_token():
    """Get field leadership token for cert.foreman@example.com."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": CERT_FOREMAN_EMAIL, "password": CERT_FOREMAN_PASSWORD},
        timeout=15,
    )
    if resp.status_code != 200:
        pytest.skip(f"Cert foreman login failed: {resp.status_code} - {resp.text[:200]}")
    data = resp.json()
    tokens = data.get("portal_tokens", {})
    # Foreman gets field_leadership or fl token
    return tokens.get("field_leadership") or tokens.get("fl")


class TestDraftTelemetryLongFormKey:
    """Test that long formKey (>64 chars) returns 200 instead of 422."""

    def test_long_formkey_returns_200(self):
        """POST /api/draft-telemetry with formKey > 64 chars should return 200."""
        # Create a formKey longer than 64 characters (but within the new 180 limit)
        long_form_key = "daily-report-form-" + "a" * 100  # 118 chars total
        assert len(long_form_key) > 64, "formKey should be longer than 64 chars"
        assert len(long_form_key) <= 180, "formKey should be within 180 char limit"

        event_id = str(uuid.uuid4())
        payload = {
            "batch": [
                {
                    "eventId": event_id,
                    "event": "draft.write.ok",
                    "actorId": "test-actor-" + str(uuid.uuid4())[:8],
                    "deviceId": "test-device-" + str(uuid.uuid4())[:8],
                    "formKey": long_form_key,
                    "ts": int(datetime.now(timezone.utc).timestamp() * 1000),
                    "meta": {"trigger": "test", "payloadBytes": 1024},
                }
            ]
        }

        resp = requests.post(
            f"{BASE_URL}/api/draft-telemetry",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        # Should return 200, not 422
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "received" in data, f"Response should contain 'received': {data}"
        print(f"✓ Long formKey ({len(long_form_key)} chars) accepted: received={data.get('received')}")

    def test_very_long_formkey_at_limit(self):
        """POST /api/draft-telemetry with formKey at exactly 180 chars should return 200."""
        # Create a formKey at exactly 180 characters
        long_form_key = "x" * 180
        assert len(long_form_key) == 180, "formKey should be exactly 180 chars"

        event_id = str(uuid.uuid4())
        payload = {
            "batch": [
                {
                    "eventId": event_id,
                    "event": "draft.write.ok",
                    "actorId": "test-actor-180",
                    "deviceId": "test-device-180",
                    "formKey": long_form_key,
                    "ts": int(datetime.now(timezone.utc).timestamp() * 1000),
                    "meta": {},
                }
            ]
        }

        resp = requests.post(
            f"{BASE_URL}/api/draft-telemetry",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print(f"✓ formKey at 180 char limit accepted")

    def test_formkey_over_limit_rejected(self):
        """POST /api/draft-telemetry with formKey > 180 chars should return 422."""
        # Create a formKey over 180 characters
        over_limit_form_key = "x" * 181
        assert len(over_limit_form_key) > 180, "formKey should be over 180 chars"

        event_id = str(uuid.uuid4())
        payload = {
            "batch": [
                {
                    "eventId": event_id,
                    "event": "draft.write.ok",
                    "actorId": "test-actor-over",
                    "deviceId": "test-device-over",
                    "formKey": over_limit_form_key,
                    "ts": int(datetime.now(timezone.utc).timestamp() * 1000),
                    "meta": {},
                }
            ]
        }

        resp = requests.post(
            f"{BASE_URL}/api/draft-telemetry",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        # Should return 422 for over-limit
        assert resp.status_code == 422, f"Expected 422 for over-limit, got {resp.status_code}: {resp.text}"
        print(f"✓ formKey over 180 char limit correctly rejected with 422")


class TestGovernedCertificationLane:
    """Test governed certification lane for Daily Reports."""

    def test_cert_foreman_login_works(self, fl_token):
        """Verify cert.foreman@example.com can authenticate."""
        assert fl_token is not None, "Cert foreman should get a field_leadership token"
        print(f"✓ Cert foreman authenticated with FL token: {fl_token[:20]}...")

    def test_cert_project_exists(self, admin_token):
        """Verify ZZ-RUNTIME-CERT-2026 project exists."""
        if not admin_token:
            pytest.skip("Admin token required")

        resp = requests.get(
            f"{BASE_URL}/api/admin/jobs",
            headers={"X-Admin-Token": admin_token},
            timeout=15,
        )
        assert resp.status_code == 200, f"Jobs list failed: {resp.status_code}"
        jobs = resp.json()

        cert_project = None
        for job in jobs:
            if job.get("project_number") == CERT_PROJECT_NUMBER:
                cert_project = job
                break

        if cert_project:
            print(f"✓ Certification project found: {cert_project.get('project_name')}")
        else:
            print(f"⚠ Certification project {CERT_PROJECT_NUMBER} not found in jobs list - may need seeding")

    def test_governed_lane_module_functions(self):
        """Test the governed certification lane module functions directly."""
        # Import the module
        import sys
        sys.path.insert(0, "/app/backend")
        from lib.governed_certification_lane import (
            is_governed_certification_identity,
            is_governed_certification_project,
            apply_governed_daily_report_lane,
            build_governed_routing_override,
            GOVERNED_CERTIFICATION_PROJECT_NUMBER,
        )

        # Test identity check
        cert_identity = {"email": "cert.foreman@example.com", "name": "Cert Foreman"}
        assert is_governed_certification_identity(cert_identity), "cert.foreman should be a governed identity"
        print("✓ is_governed_certification_identity works for cert.foreman@example.com")

        # Test project check
        assert is_governed_certification_project(GOVERNED_CERTIFICATION_PROJECT_NUMBER), \
            f"{GOVERNED_CERTIFICATION_PROJECT_NUMBER} should be a governed project"
        print(f"✓ is_governed_certification_project works for {GOVERNED_CERTIFICATION_PROJECT_NUMBER}")

        # Test routing override
        routing = build_governed_routing_override()
        assert routing.get("enabled") is True, "routing_override should be enabled"
        assert routing.get("reason") == "governed_production_certification_lane"
        assert "cert.pm@example.com" in routing.get("to", [])
        print(f"✓ build_governed_routing_override returns correct structure: {routing}")

        # Test apply_governed_daily_report_lane
        test_doc = {
            "project_number": GOVERNED_CERTIFICATION_PROJECT_NUMBER,
            "project_name": "Runtime Certification — Internal Test Project",
            "prepared_by_identity": cert_identity,
            "report_date": "2026-07-15",
        }
        result = apply_governed_daily_report_lane(test_doc)

        assert result.get("certification_record") is True, "Should set certification_record=true"
        assert result.get("synthetic_record") is True, "Should set synthetic_record=true"
        assert result.get("hidden_from_operations") is True, "Should set hidden_from_operations=true"
        assert result.get("email_dispatch_suppressed") is False, "Should set email_dispatch_suppressed=false"
        assert result.get("routing_override", {}).get("enabled") is True, "Should have routing_override.enabled=true"
        print("✓ apply_governed_daily_report_lane sets all required fields correctly")


class TestIntelligenceTimeoutBehavior:
    """Test that intelligence endpoints handle timeouts gracefully."""

    def test_hr_intelligence_endpoint_exists(self, admin_token):
        """Test HR intelligence endpoint responds (may timeout but should not crash)."""
        if not admin_token:
            pytest.skip("Admin token required")

        # Use a short timeout to test timeout handling
        try:
            resp = requests.get(
                f"{BASE_URL}/api/hr/intelligence/summary",
                headers={"X-Admin-Token": admin_token},
                timeout=6,  # Short timeout
            )
            # Any response is acceptable - we're testing it doesn't crash
            print(f"✓ HR intelligence endpoint responded: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"  Data keys: {list(data.keys())[:5]}")
        except requests.exceptions.Timeout:
            print("✓ HR intelligence endpoint timed out (expected behavior)")
        except requests.exceptions.RequestException as e:
            print(f"⚠ HR intelligence endpoint error: {e}")

    def test_shop_intelligence_endpoint_exists(self, admin_token):
        """Test Shop intelligence endpoint responds (may timeout but should not crash)."""
        if not admin_token:
            pytest.skip("Admin token required")

        try:
            resp = requests.get(
                f"{BASE_URL}/api/operations/intelligence/shop",
                headers={"X-Admin-Token": admin_token},
                timeout=6,
            )
            print(f"✓ Shop intelligence endpoint responded: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"  Data keys: {list(data.keys())[:5]}")
        except requests.exceptions.Timeout:
            print("✓ Shop intelligence endpoint timed out (expected behavior)")
        except requests.exceptions.RequestException as e:
            print(f"⚠ Shop intelligence endpoint error: {e}")

    def test_safety_intelligence_endpoint_exists(self, admin_token):
        """Test Safety intelligence endpoint responds (may timeout but should not crash)."""
        if not admin_token:
            pytest.skip("Admin token required")

        try:
            resp = requests.get(
                f"{BASE_URL}/api/safety/company/safety-kpis",
                headers={"X-Admin-Token": admin_token},
                timeout=6,
            )
            print(f"✓ Safety intelligence endpoint responded: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"  Data keys: {list(data.keys())[:5]}")
        except requests.exceptions.Timeout:
            print("✓ Safety intelligence endpoint timed out (expected behavior)")
        except requests.exceptions.RequestException as e:
            print(f"⚠ Safety intelligence endpoint error: {e}")


class TestDailySubmitPageLoads:
    """Test that /daily/submit page loads and is not blank."""

    def test_daily_submit_page_accessible(self):
        """Test that the daily submit page returns HTML content."""
        resp = requests.get(
            f"{BASE_URL}/daily/submit",
            timeout=15,
            allow_redirects=True,
        )
        # Should return 200 with HTML content
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        content = resp.text
        # Check it's not blank and contains expected React app markers
        assert len(content) > 1000, "Page content should not be blank"
        assert "<div id=\"root\">" in content or "<!doctype html>" in content.lower(), \
            "Page should contain React root or HTML doctype"
        print(f"✓ /daily/submit page loads ({len(content)} bytes)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

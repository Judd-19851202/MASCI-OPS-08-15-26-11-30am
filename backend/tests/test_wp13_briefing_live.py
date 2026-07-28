"""
WP-13 Monday Morning Briefing Live API Tests
Tests project + enterprise briefing lifecycle: generate, approve, freeze, PDF
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials from test_credentials.md
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


def _login_and_get_headers(email, password, portal):
    """Login and return headers with both portal token and directory token"""
    resp = requests.post(f"{BASE_URL}/api/auth/multi-login", json={
        "email": email,
        "password": password,
        "portal": portal
    })
    if resp.status_code != 200:
        return None, f"Login failed: {resp.status_code} - {resp.text[:200]}"
    data = resp.json()
    portal_token = data.get("portal_tokens", {}).get(portal, "")
    session_token = data.get("session_token", "")
    header_map = {
        "admin": "X-Admin-Token",
        "pm": "X-PM-Token",
        "hr": "X-HR-Token",
        "shop": "X-Shop-Token",
        "safety": "X-Safety-Token",
        "dispatch": "X-Dispatch-Token",
    }
    headers = {
        "Content-Type": "application/json",
        header_map.get(portal, f"X-{portal.title()}-Token"): portal_token,
        "X-Directory-Token": session_token,
    }
    return headers, None


@pytest.fixture(scope="module")
def pm_headers():
    """Get PM headers with portal and directory tokens"""
    headers, err = _login_and_get_headers(PM_EMAIL, PM_PASSWORD, "pm")
    if err:
        pytest.skip(err)
    return headers


@pytest.fixture(scope="module")
def admin_headers():
    """Get Admin headers with portal and directory tokens"""
    headers, err = _login_and_get_headers(ADMIN_EMAIL, ADMIN_PASSWORD, "admin")
    if err:
        pytest.skip(err)
    return headers


@pytest.fixture(scope="module")
def pm_project(admin_headers):
    """Get a project number from jobs_master (admin has access to all)"""
    resp = requests.get(f"{BASE_URL}/api/jobs-master", headers=admin_headers)
    if resp.status_code != 200:
        pytest.skip(f"Could not get jobs: {resp.status_code}")
    jobs = resp.json()
    if not jobs:
        pytest.skip("No jobs available")
    return jobs[0].get("project_number")


class TestProjectMondayBriefingLifecycle:
    """WP-13: Project Monday Morning Briefing lifecycle tests"""

    def test_get_project_monday_briefing(self, admin_headers, pm_project):
        """GET /oppc/projects/{project_number}/monday-briefing returns briefing doc"""
        resp = requests.get(f"{BASE_URL}/api/oppc/projects/{pm_project}/monday-briefing", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert "briefing" in data
        assert "scope" in data
        briefing = data["briefing"]
        # Verify canonical structure
        assert briefing.get("doc_type") == "oppc_monday_morning_briefing"
        assert briefing.get("scope_type") == "project"
        assert "explainability" in briefing
        assert briefing["explainability"].get("truth_basis") == "canonical_operational_data"
        print(f"PASS: Project briefing loaded for {pm_project}, status={briefing.get('status')}")

    def test_generate_project_monday_briefing(self, admin_headers, pm_project):
        """POST /oppc/projects/{project_number}/monday-briefing/generate creates briefing"""
        import datetime
        week_ending = (datetime.date.today() + datetime.timedelta(days=28)).isoformat()
        resp = requests.post(
            f"{BASE_URL}/api/oppc/projects/{pm_project}/monday-briefing/generate",
            json={"week_ending": week_ending},
            headers=admin_headers
        )
        # 409 is acceptable if briefing is already frozen for this week
        if resp.status_code == 409:
            print("PASS: Project briefing already frozen (governance working)")
            return
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert data.get("ok") is True
        briefing = data.get("briefing", {})
        assert briefing.get("status") == "draft"
        assert "content_hash" in briefing
        assert "sections" in briefing
        # Verify canonical sections
        sections = briefing.get("sections", {})
        assert "forecast" in sections
        assert "confidence" in sections
        assert "production" in sections
        assert "payroll" in sections
        assert "variances" in sections
        assert "monday_review" in sections
        print(f"PASS: Project briefing generated, hash={briefing.get('content_hash')[:16]}...")

    def test_approve_project_monday_briefing(self, admin_headers, pm_project):
        """POST /oppc/projects/{project_number}/monday-briefing/approve approves briefing"""
        import datetime
        week_ending = (datetime.date.today() + datetime.timedelta(days=35)).isoformat()
        # First generate to ensure we have a draft
        requests.post(
            f"{BASE_URL}/api/oppc/projects/{pm_project}/monday-briefing/generate",
            json={"week_ending": week_ending},
            headers=admin_headers
        )
        resp = requests.post(
            f"{BASE_URL}/api/oppc/projects/{pm_project}/monday-briefing/approve",
            json={"week_ending": week_ending, "note": "WP-13 test approval"},
            headers=admin_headers
        )
        # 409 is acceptable if briefing is already frozen
        if resp.status_code == 409:
            print("PASS: Project briefing already frozen (governance working)")
            return
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert data.get("ok") is True
        briefing = data.get("briefing", {})
        assert briefing.get("status") == "approved"
        assert "approved_at" in briefing
        assert "approval_history" in briefing
        print(f"PASS: Project briefing approved at {briefing.get('approved_at')}")

    def test_freeze_project_monday_briefing(self, admin_headers, pm_project):
        """POST /oppc/projects/{project_number}/monday-briefing/freeze freezes approved briefing"""
        import datetime
        import random
        # Use a random future week to avoid conflicts with previously frozen briefings
        week_ending = (datetime.date.today() + datetime.timedelta(days=200 + random.randint(1, 100))).isoformat()
        # Generate and approve first
        requests.post(
            f"{BASE_URL}/api/oppc/projects/{pm_project}/monday-briefing/generate",
            json={"week_ending": week_ending},
            headers=admin_headers
        )
        requests.post(
            f"{BASE_URL}/api/oppc/projects/{pm_project}/monday-briefing/approve",
            json={"week_ending": week_ending},
            headers=admin_headers
        )
        resp = requests.post(
            f"{BASE_URL}/api/oppc/projects/{pm_project}/monday-briefing/freeze",
            json={"week_ending": week_ending, "note": "WP-13 test freeze"},
            headers=admin_headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert data.get("ok") is True
        briefing = data.get("briefing", {})
        assert briefing.get("status") == "frozen"
        assert briefing.get("frozen") is True
        assert "frozen_at" in briefing
        print(f"PASS: Project briefing frozen at {briefing.get('frozen_at')}")

    def test_frozen_briefing_cannot_be_regenerated(self, admin_headers, pm_project):
        """Frozen briefings cannot be regenerated (governance discipline)"""
        import datetime
        week_ending = (datetime.date.today() + datetime.timedelta(days=49)).isoformat()
        # Ensure briefing is frozen
        requests.post(f"{BASE_URL}/api/oppc/projects/{pm_project}/monday-briefing/generate", json={"week_ending": week_ending}, headers=admin_headers)
        requests.post(f"{BASE_URL}/api/oppc/projects/{pm_project}/monday-briefing/approve", json={"week_ending": week_ending}, headers=admin_headers)
        requests.post(f"{BASE_URL}/api/oppc/projects/{pm_project}/monday-briefing/freeze", json={"week_ending": week_ending}, headers=admin_headers)
        
        # Try to regenerate - should fail with 409
        resp = requests.post(
            f"{BASE_URL}/api/oppc/projects/{pm_project}/monday-briefing/generate",
            json={"week_ending": week_ending},
            headers=admin_headers
        )
        assert resp.status_code == 409, f"Expected 409 Conflict, got {resp.status_code}"
        print("PASS: Frozen briefing correctly rejected regeneration attempt")

    def test_project_monday_briefing_pdf(self, admin_headers, pm_project):
        """GET /oppc/projects/{project_number}/monday-briefing/pdf returns PDF"""
        resp = requests.get(f"{BASE_URL}/api/oppc/projects/{pm_project}/monday-briefing/pdf", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert resp.headers.get("content-type") == "application/pdf"
        assert resp.content.startswith(b"%PDF")
        print(f"PASS: Project briefing PDF returned, size={len(resp.content)} bytes")


class TestEnterpriseMondayBriefingLifecycle:
    """WP-13: Enterprise Monday Morning Briefing lifecycle tests (admin only)"""

    def test_get_enterprise_monday_briefing(self, admin_headers):
        """GET /oppc/enterprise/monday-briefing returns enterprise briefing"""
        resp = requests.get(f"{BASE_URL}/api/oppc/enterprise/monday-briefing", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert "briefing" in data
        briefing = data["briefing"]
        assert briefing.get("scope_type") == "enterprise"
        assert briefing.get("scope_key") == "enterprise"
        assert "explainability" in briefing
        assert briefing["explainability"].get("truth_basis") == "canonical_operational_data"
        print(f"PASS: Enterprise briefing loaded, status={briefing.get('status')}")

    def test_generate_enterprise_monday_briefing(self, admin_headers):
        """POST /oppc/enterprise/monday-briefing/generate creates enterprise briefing"""
        # Use a unique week_ending to avoid frozen briefing conflicts
        import datetime
        week_ending = (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
        resp = requests.post(
            f"{BASE_URL}/api/oppc/enterprise/monday-briefing/generate",
            json={"week_ending": week_ending},
            headers=admin_headers
        )
        # 409 is acceptable if briefing is already frozen for this week
        if resp.status_code == 409:
            print("PASS: Enterprise briefing already frozen (governance working)")
            return
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert data.get("ok") is True
        briefing = data.get("briefing", {})
        assert briefing.get("status") == "draft"
        # Verify enterprise sections
        sections = briefing.get("sections", {})
        assert "portfolio_summary" in sections
        assert "confidence_summary" in sections
        assert "at_risk_projects" in sections
        print(f"PASS: Enterprise briefing generated, hash={briefing.get('content_hash', '')[:16]}...")

    def test_approve_enterprise_monday_briefing(self, admin_headers):
        """POST /oppc/enterprise/monday-briefing/approve approves enterprise briefing"""
        import datetime
        week_ending = (datetime.date.today() + datetime.timedelta(days=14)).isoformat()
        requests.post(f"{BASE_URL}/api/oppc/enterprise/monday-briefing/generate", json={"week_ending": week_ending}, headers=admin_headers)
        resp = requests.post(
            f"{BASE_URL}/api/oppc/enterprise/monday-briefing/approve",
            json={"week_ending": week_ending, "note": "WP-13 enterprise approval"},
            headers=admin_headers
        )
        # 409 is acceptable if briefing is already frozen
        if resp.status_code == 409:
            print("PASS: Enterprise briefing already frozen (governance working)")
            return
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert data.get("ok") is True
        briefing = data.get("briefing", {})
        assert briefing.get("status") == "approved"
        print(f"PASS: Enterprise briefing approved at {briefing.get('approved_at')}")

    def test_freeze_enterprise_monday_briefing(self, admin_headers):
        """POST /oppc/enterprise/monday-briefing/freeze freezes enterprise briefing"""
        import datetime
        import random
        # Use a random future week to avoid conflicts with previously frozen briefings
        week_ending = (datetime.date.today() + datetime.timedelta(days=100 + random.randint(1, 100))).isoformat()
        requests.post(f"{BASE_URL}/api/oppc/enterprise/monday-briefing/generate", json={"week_ending": week_ending}, headers=admin_headers)
        requests.post(f"{BASE_URL}/api/oppc/enterprise/monday-briefing/approve", json={"week_ending": week_ending}, headers=admin_headers)
        resp = requests.post(
            f"{BASE_URL}/api/oppc/enterprise/monday-briefing/freeze",
            json={"week_ending": week_ending, "note": "WP-13 enterprise freeze"},
            headers=admin_headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert data.get("ok") is True
        briefing = data.get("briefing", {})
        assert briefing.get("status") == "frozen"
        assert briefing.get("frozen") is True
        print(f"PASS: Enterprise briefing frozen at {briefing.get('frozen_at')}")

    def test_enterprise_monday_briefing_pdf(self, admin_headers):
        """GET /oppc/enterprise/monday-briefing/pdf returns PDF"""
        resp = requests.get(f"{BASE_URL}/api/oppc/enterprise/monday-briefing/pdf", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert resp.headers.get("content-type") == "application/pdf"
        assert resp.content.startswith(b"%PDF")
        print(f"PASS: Enterprise briefing PDF returned, size={len(resp.content)} bytes")

    def test_pm_cannot_access_enterprise_briefing(self, pm_headers):
        """PM users cannot access enterprise briefing (admin only)"""
        resp = requests.get(f"{BASE_URL}/api/oppc/enterprise/monday-briefing", headers=pm_headers)
        assert resp.status_code == 403, f"Expected 403 Forbidden, got {resp.status_code}"
        print("PASS: PM correctly denied access to enterprise briefing")


class TestBriefingGovernanceDiscipline:
    """WP-13: Governance discipline checks"""

    def test_briefing_truth_basis_is_canonical(self, admin_headers, pm_project):
        """Briefing truth_basis must be canonical_operational_data"""
        resp = requests.get(f"{BASE_URL}/api/oppc/projects/{pm_project}/monday-briefing", headers=admin_headers)
        assert resp.status_code == 200
        briefing = resp.json().get("briefing", {})
        explainability = briefing.get("explainability", {})
        assert explainability.get("truth_basis") == "canonical_operational_data"
        print("PASS: Briefing truth_basis is canonical_operational_data")

    def test_briefing_has_content_hash(self, admin_headers, pm_project):
        """Generated briefing must have content_hash for integrity"""
        resp = requests.post(
            f"{BASE_URL}/api/oppc/projects/{pm_project}/monday-briefing/generate",
            json={},
            headers=admin_headers
        )
        if resp.status_code == 409:  # Frozen
            pytest.skip("Briefing is frozen, cannot regenerate")
        assert resp.status_code == 200
        briefing = resp.json().get("briefing", {})
        assert "content_hash" in briefing
        assert len(briefing["content_hash"]) == 64  # SHA-256 hex
        print(f"PASS: Briefing has content_hash: {briefing['content_hash'][:16]}...")

    def test_briefing_has_warnings(self, admin_headers, pm_project):
        """Briefing must surface warnings from canonical data"""
        resp = requests.get(f"{BASE_URL}/api/oppc/projects/{pm_project}/monday-briefing", headers=admin_headers)
        assert resp.status_code == 200
        briefing = resp.json().get("briefing", {})
        assert "warnings" in briefing
        assert isinstance(briefing["warnings"], list)
        print(f"PASS: Briefing has warnings field with {len(briefing['warnings'])} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

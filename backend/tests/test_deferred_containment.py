"""
Test Deferred Containment Backend Endpoints
============================================
Verifies that all deferred surfaces return 404 with release_deferred_surface detail.

Deferred surfaces:
- PM Project Performance CSV export: GET /api/pm/project-controls/projects/{project}/operational-intelligence/export
- PM Schedule email-review: POST /api/pm/project-controls/projects/{project}/schedule/export/email
- Monday Briefing PDF (project): GET /api/oppc/projects/{project}/monday-briefing/pdf
- Monday Briefing PDF (enterprise): GET /api/oppc/enterprise/monday-briefing/pdf
- Internal certification preview: POST /api/admin/operations-control/certifications/preview-daily-report
- Internal certification run: POST /api/admin/operations-control/certifications/run
- Daily report AI summary draft: POST /api/daily-reports/summary/draft
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
PROJECT_NUMBER = "ZZ-RUNTIME-CERT-2026"

# Test credentials
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"


@pytest.fixture(scope="module")
def admin_session():
    """Get admin session with tokens."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Login as admin
    resp = session.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={"X-Test-Rate-Limit-Bypass": "1"}
    )
    if resp.status_code != 200:
        pytest.skip(f"Admin login failed: {resp.status_code}")
    
    data = resp.json()
    # Extract admin token from portal_tokens
    portal_tokens = data.get("portal_tokens", {})
    admin_token = portal_tokens.get("admin") or data.get("admin_token") or data.get("token")
    directory_token = data.get("session_token") or data.get("directory_token")
    
    if admin_token:
        session.headers.update({"X-Admin-Token": admin_token})
    if directory_token:
        session.headers.update({"X-Directory-Token": directory_token})
    
    return session


@pytest.fixture(scope="module")
def pm_session():
    """Get PM session with token."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Login as PM
    resp = session.post(
        f"{BASE_URL}/api/pm/login",
        json={"email": PM_EMAIL, "password": PM_PASSWORD},
        headers={"X-Test-Rate-Limit-Bypass": "1"}
    )
    if resp.status_code != 200:
        pytest.skip(f"PM login failed: {resp.status_code}")
    
    data = resp.json()
    pm_token = data.get("token")
    
    if pm_token:
        session.headers.update({"X-PM-Token": pm_token})
    
    return session


class TestReleaseDeferredContainment:
    """Test that deferred surfaces return 404 with release_deferred_surface detail."""
    
    def test_pm_operational_intelligence_export_deferred(self, pm_session):
        """PM Project Performance CSV export should return 404 with release_deferred_surface."""
        resp = pm_session.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{PROJECT_NUMBER}/operational-intelligence/export"
        )
        
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        detail = data.get("detail", {})
        
        # Verify the deferred surface detail
        assert detail.get("code") == "release_deferred_surface", f"Expected release_deferred_surface code, got: {detail}"
        assert detail.get("surface") == "pm_project_performance_csv_export", f"Expected pm_project_performance_csv_export surface, got: {detail}"
        print(f"PASS: PM operational intelligence export returns 404 with release_deferred_surface: {detail}")
    
    def test_pm_schedule_email_export_deferred(self, pm_session):
        """PM Schedule email-review action should return 404 with release_deferred_surface."""
        resp = pm_session.post(
            f"{BASE_URL}/api/pm/project-controls/projects/{PROJECT_NUMBER}/schedule/export/email",
            json={"export_kind": "master_schedule_csv", "recipients": ["test@example.com"]}
        )
        
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        detail = data.get("detail", {})
        
        assert detail.get("code") == "release_deferred_surface", f"Expected release_deferred_surface code, got: {detail}"
        assert detail.get("surface") == "pm_schedule_email_review", f"Expected pm_schedule_email_review surface, got: {detail}"
        print(f"PASS: PM schedule email export returns 404 with release_deferred_surface: {detail}")
    
    def test_project_monday_briefing_pdf_deferred(self, pm_session):
        """Project Monday Briefing PDF should return 404 with release_deferred_surface."""
        resp = pm_session.get(
            f"{BASE_URL}/api/oppc/projects/{PROJECT_NUMBER}/monday-briefing/pdf"
        )
        
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        detail = data.get("detail", {})
        
        assert detail.get("code") == "release_deferred_surface", f"Expected release_deferred_surface code, got: {detail}"
        assert detail.get("surface") == "executive_monday_briefing_pdf", f"Expected executive_monday_briefing_pdf surface, got: {detail}"
        print(f"PASS: Project Monday Briefing PDF returns 404 with release_deferred_surface: {detail}")
    
    def test_enterprise_monday_briefing_pdf_deferred(self, admin_session):
        """Enterprise Monday Briefing PDF should return 404 with release_deferred_surface."""
        resp = admin_session.get(
            f"{BASE_URL}/api/oppc/enterprise/monday-briefing/pdf"
        )
        
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        detail = data.get("detail", {})
        
        assert detail.get("code") == "release_deferred_surface", f"Expected release_deferred_surface code, got: {detail}"
        assert detail.get("surface") == "executive_monday_briefing_pdf", f"Expected executive_monday_briefing_pdf surface, got: {detail}"
        print(f"PASS: Enterprise Monday Briefing PDF returns 404 with release_deferred_surface: {detail}")
    
    def test_internal_certification_preview_deferred(self, admin_session):
        """Internal certification preview-daily-report should return 404 with release_deferred_surface."""
        resp = admin_session.post(
            f"{BASE_URL}/api/admin/operations-control/certifications/preview-daily-report"
        )
        
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        detail = data.get("detail", {})
        
        assert detail.get("code") == "release_deferred_surface", f"Expected release_deferred_surface code, got: {detail}"
        assert detail.get("surface") == "internal_certification_route", f"Expected internal_certification_route surface, got: {detail}"
        print(f"PASS: Internal certification preview returns 404 with release_deferred_surface: {detail}")
    
    def test_internal_certification_run_deferred(self, admin_session):
        """Internal certification run should return 404 with release_deferred_surface."""
        resp = admin_session.post(
            f"{BASE_URL}/api/admin/operations-control/certifications/run"
        )
        
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        detail = data.get("detail", {})
        
        assert detail.get("code") == "release_deferred_surface", f"Expected release_deferred_surface code, got: {detail}"
        assert detail.get("surface") == "internal_certification_route", f"Expected internal_certification_route surface, got: {detail}"
        print(f"PASS: Internal certification run returns 404 with release_deferred_surface: {detail}")
    
    def test_daily_report_summary_draft_deferred(self):
        """Daily report AI summary draft should return 404 with release_deferred_surface."""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        resp = session.post(
            f"{BASE_URL}/api/daily-reports/summary/draft",
            json={"payload": {"project_number": PROJECT_NUMBER}}
        )
        
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        detail = data.get("detail", {})
        
        assert detail.get("code") == "release_deferred_surface", f"Expected release_deferred_surface code, got: {detail}"
        assert detail.get("surface") == "daily_report_dedicated_ai_summary", f"Expected daily_report_dedicated_ai_summary surface, got: {detail}"
        print(f"PASS: Daily report summary draft returns 404 with release_deferred_surface: {detail}")


class TestReleaseIdentityDataTruth:
    """Test release identity and data truth endpoints."""
    
    def test_version_endpoint_release_match(self):
        """GET /api/version should report frontend_backend_release_match=true."""
        resp = requests.get(f"{BASE_URL}/api/version")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        
        # Verify frontend_backend_release_match is true
        assert data.get("frontend_backend_release_match") is True, \
            f"Expected frontend_backend_release_match=true, got: {data.get('frontend_backend_release_match')}"
        
        # Verify runtime identity is populated
        runtime_identity = data.get("runtime_identity", {})
        identity = runtime_identity.get("identity", {})
        
        assert identity.get("app_env") is not None, f"Expected app_env to be populated, got: {identity}"
        assert identity.get("db_name") is not None, f"Expected db_name to be populated, got: {identity}"
        
        print(f"PASS: /api/version reports frontend_backend_release_match=true")
        print(f"  - app_env: {identity.get('app_env')}")
        print(f"  - db_name: {identity.get('db_name')}")
        print(f"  - release_commit: {identity.get('release_commit', 'N/A')[:12]}...")
        print(f"  - release_source_hash: {identity.get('release_source_hash', 'N/A')}")
    
    def test_platform_data_truth_populated(self):
        """GET /api/platform/data-truth should return populated runtime identity fields."""
        resp = requests.get(f"{BASE_URL}/api/platform/data-truth")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        
        # Verify runtime_identity is populated (not null identity block)
        runtime_identity = data.get("runtime_identity", {})
        identity = runtime_identity.get("identity", {})
        
        assert runtime_identity is not None, "Expected runtime_identity to be present"
        assert identity is not None, "Expected identity block to be present"
        assert identity.get("app_env") is not None, f"Expected app_env to be populated, got: {identity}"
        assert identity.get("db_name") is not None, f"Expected db_name to be populated, got: {identity}"
        
        # Verify validation is valid
        validation = runtime_identity.get("validation", {})
        assert validation.get("valid") is True, f"Expected validation.valid=true, got: {validation}"
        
        # Verify environment and database fields
        assert data.get("environment") is not None, f"Expected environment to be populated"
        assert data.get("database") is not None, f"Expected database to be populated"
        
        print(f"PASS: /api/platform/data-truth returns populated runtime identity")
        print(f"  - status: {data.get('status')}")
        print(f"  - ok: {data.get('ok')}")
        print(f"  - environment: {data.get('environment')}")
        print(f"  - database: {data.get('database')}")
        print(f"  - identity.app_env: {identity.get('app_env')}")
        print(f"  - identity.db_name: {identity.get('db_name')}")
        print(f"  - validation.valid: {validation.get('valid')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

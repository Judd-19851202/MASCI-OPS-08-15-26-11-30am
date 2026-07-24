"""
PM Project-Scoping Repair Verification Tests

Tests the bounded repair for PM project-scoping:
1. Super Admin using Admin-token context - unrestricted access
2. Super Admin using PM-token context - unrestricted access (no empty-scope regression)
3. PM-only user - sees assigned, denied unassigned
4. Unauthorized/no-token access - denied
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import requests


BASE_URL = next(
    line.split("=", 1)[1]
    for line in Path("/app/frontend/.env").read_text().splitlines()
    if line.startswith("REACT_APP_BACKEND_URL=")
)
CREDS_TEXT = Path("/app/memory/test_credentials.md").read_text()


def _extract_password(email: str) -> str:
    pattern = re.compile(rf"Email:\s*`{re.escape(email)}`.*?Password:\s*`([^`]+)`", re.S)
    match = pattern.search(CREDS_TEXT)
    if not match:
        raise AssertionError(f"Password for {email} not found in test_credentials.md")
    return match.group(1)


def _login(email: str, password: str) -> dict:
    response = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": email, "password": password},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def _headers_admin(bundle: dict) -> dict:
    """Headers for admin-token context"""
    return {
        "X-Directory-Token": bundle["session_token"],
        "X-Admin-Token": bundle["portal_tokens"]["admin"],
    }


def _headers_pm(bundle: dict) -> dict:
    """Headers for PM-token context"""
    return {
        "X-Directory-Token": bundle["session_token"],
        "X-PM-Token": bundle["portal_tokens"]["pm"],
    }


class TestSuperAdminAdminTokenContext:
    """Super Admin using Admin-token context can load Daily Reports list, Job Photos list, 
    assigned and unassigned project records, and raw photo access works."""
    
    @pytest.fixture(scope="class")
    def admin_bundle(self):
        admin_email = "jaymn.judd@mascigc.com"
        return _login(admin_email, _extract_password(admin_email))
    
    def test_daily_reports_list_non_empty(self, admin_bundle):
        """Admin-token context: Daily Reports list should be non-empty"""
        headers = _headers_admin(admin_bundle)
        response = requests.get(f"{BASE_URL}/api/daily-reports", headers=headers, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Admin-token daily reports should be non-empty"
    
    def test_job_photos_list_non_empty(self, admin_bundle):
        """Admin-token context: Job Photos list should be non-empty"""
        headers = _headers_admin(admin_bundle)
        response = requests.get(f"{BASE_URL}/api/job-photos", headers=headers, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0, "Admin-token job photos should be non-empty"
    
    def test_assigned_project_daily_report_accessible(self, admin_bundle):
        """Admin-token context: Can access assigned project daily report"""
        headers = _headers_admin(admin_bundle)
        # Use known assigned daily report ID
        response = requests.get(
            f"{BASE_URL}/api/daily-reports/652b4e6f-bcb6-4065-8e89-4938c49d1f64",
            headers=headers,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("project_number") == "ZZ-RUNTIME-CERT-2026"
    
    def test_raw_photo_access_works(self, admin_bundle):
        """Admin-token context: Raw photo access should work"""
        headers = _headers_admin(admin_bundle)
        response = requests.get(
            f"{BASE_URL}/api/job-photos/daily_report:652b4e6f-bcb6-4065-8e89-4938c49d1f64:1/raw",
            headers=headers,
            timeout=60,
        )
        assert response.status_code == 200


class TestSuperAdminPMTokenContext:
    """Super Admin using PM-token context remains unrestricted on Daily Reports and Job Photos 
    and no empty-scope regression remains."""
    
    @pytest.fixture(scope="class")
    def admin_bundle(self):
        admin_email = "jaymn.judd@mascigc.com"
        return _login(admin_email, _extract_password(admin_email))
    
    def test_daily_reports_list_non_empty(self, admin_bundle):
        """PM-token context: Super Admin Daily Reports list should be non-empty (unrestricted)"""
        headers = _headers_pm(admin_bundle)
        response = requests.get(f"{BASE_URL}/api/daily-reports", headers=headers, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Super Admin PM-token daily reports should stay unrestricted"
    
    def test_job_photos_list_non_empty(self, admin_bundle):
        """PM-token context: Super Admin Job Photos list should be non-empty (unrestricted)"""
        headers = _headers_pm(admin_bundle)
        response = requests.get(f"{BASE_URL}/api/job-photos", headers=headers, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0, "Super Admin PM-token job photos should stay unrestricted"
    
    def test_no_empty_scope_regression(self, admin_bundle):
        """PM-token context: Verify no empty-scope regression - counts should match admin context"""
        admin_headers = _headers_admin(admin_bundle)
        pm_headers = _headers_pm(admin_bundle)
        
        # Get counts with admin token
        admin_daily = requests.get(f"{BASE_URL}/api/daily-reports", headers=admin_headers, timeout=60)
        admin_photos = requests.get(f"{BASE_URL}/api/job-photos", headers=admin_headers, timeout=60)
        
        # Get counts with PM token
        pm_daily = requests.get(f"{BASE_URL}/api/daily-reports", headers=pm_headers, timeout=60)
        pm_photos = requests.get(f"{BASE_URL}/api/job-photos", headers=pm_headers, timeout=60)
        
        admin_daily_count = len(admin_daily.json())
        pm_daily_count = len(pm_daily.json())
        admin_photo_count = len(admin_photos.json().get("items", []))
        pm_photo_count = len(pm_photos.json().get("items", []))
        
        # Super Admin PM-token context should have same unrestricted access
        assert pm_daily_count == admin_daily_count, f"PM-token daily count ({pm_daily_count}) should match admin-token ({admin_daily_count})"
        assert pm_photo_count == admin_photo_count, f"PM-token photo count ({pm_photo_count}) should match admin-token ({admin_photo_count})"


class TestPMOnlyUser:
    """PM-only user sees assigned Daily Reports, assigned Job Photos, assigned Daily Report detail, 
    assigned raw photos, while unassigned Daily Report detail is denied and unassigned raw photo access is denied."""
    
    @pytest.fixture(scope="class")
    def pm_bundle(self):
        pm_email = "cert.pm@example.com"
        return _login(pm_email, _extract_password(pm_email))
    
    def test_assigned_daily_reports_visible(self, pm_bundle):
        """PM-only: Assigned daily reports should be visible"""
        headers = _headers_pm(pm_bundle)
        response = requests.get(f"{BASE_URL}/api/daily-reports", headers=headers, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "PM assigned daily reports should be visible"
        # Verify project numbers are present
        project_numbers = {item.get("project_number") for item in data if item.get("project_number")}
        assert project_numbers, "PM daily reports should carry project numbers"
    
    def test_assigned_job_photos_visible(self, pm_bundle):
        """PM-only: Assigned job photos should be visible"""
        headers = _headers_pm(pm_bundle)
        response = requests.get(f"{BASE_URL}/api/job-photos", headers=headers, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0, "PM assigned job photos should be visible"
        # Verify assigned project is in results
        assert any(item.get("project_number") == "ZZ-RUNTIME-CERT-2026" for item in data["items"])
    
    def test_assigned_daily_report_detail_accessible(self, pm_bundle):
        """PM-only: Assigned daily report detail should be accessible"""
        headers = _headers_pm(pm_bundle)
        response = requests.get(
            f"{BASE_URL}/api/daily-reports/652b4e6f-bcb6-4065-8e89-4938c49d1f64",
            headers=headers,
            timeout=60,
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("project_number") == "ZZ-RUNTIME-CERT-2026"
    
    def test_assigned_raw_photo_accessible(self, pm_bundle):
        """PM-only: Assigned raw photo should be accessible"""
        headers = _headers_pm(pm_bundle)
        response = requests.get(
            f"{BASE_URL}/api/job-photos/daily_report:652b4e6f-bcb6-4065-8e89-4938c49d1f64:1/raw",
            headers=headers,
            timeout=60,
        )
        assert response.status_code == 200
    
    def test_unassigned_daily_report_detail_denied(self, pm_bundle):
        """PM-only: Unassigned daily report detail should be denied (404)"""
        headers = _headers_pm(pm_bundle)
        response = requests.get(
            f"{BASE_URL}/api/daily-reports/forensic-dr-zz-for-unassign-01",
            headers=headers,
            timeout=60,
        )
        assert response.status_code == 404, "Unassigned daily report should return 404"
    
    def test_unassigned_raw_photo_denied(self, pm_bundle):
        """PM-only: Unassigned raw photo should be denied (403)"""
        headers = _headers_pm(pm_bundle)
        response = requests.get(
            f"{BASE_URL}/api/job-photos/daily_report:85c5ed25-368e-46fe-8fa9-ae93993dd452:0/raw",
            headers=headers,
            timeout=60,
        )
        assert response.status_code == 403, "Unassigned raw photo should return 403"


class TestForensicPMFixture:
    """Test with the forensic PM fixture for isolated verification"""
    
    @pytest.fixture(scope="class")
    def forensic_pm_bundle(self):
        pm_email = "pm.scope.forensic@example.com"
        return _login(pm_email, _extract_password(pm_email))
    
    def test_assigned_daily_reports_visible(self, forensic_pm_bundle):
        """Forensic PM: Assigned daily reports should be visible"""
        headers = _headers_pm(forensic_pm_bundle)
        response = requests.get(f"{BASE_URL}/api/daily-reports", headers=headers, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Forensic fixture has 2 assigned projects
        assert len(data) >= 2, "Forensic PM should see at least 2 assigned daily reports"
    
    def test_assigned_job_photos_visible(self, forensic_pm_bundle):
        """Forensic PM: Assigned job photos should be visible"""
        headers = _headers_pm(forensic_pm_bundle)
        response = requests.get(f"{BASE_URL}/api/job-photos", headers=headers, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 2, "Forensic PM should see at least 2 assigned job photos"


class TestUnauthorizedAccess:
    """Unauthorized/no-token access to PM-protected endpoints is denied and not converted into empty success responses."""
    
    def test_daily_reports_no_token_denied(self):
        """No token: Daily reports should return 401"""
        response = requests.get(f"{BASE_URL}/api/daily-reports", timeout=60)
        assert response.status_code == 401, "No-token daily reports should return 401"
    
    def test_job_photos_no_token_denied(self):
        """No token: Job photos should return 401"""
        response = requests.get(f"{BASE_URL}/api/job-photos", timeout=60)
        assert response.status_code == 401, "No-token job photos should return 401"
    
    def test_daily_report_detail_no_token_denied(self):
        """No token: Daily report detail should return 401"""
        response = requests.get(
            f"{BASE_URL}/api/daily-reports/652b4e6f-bcb6-4065-8e89-4938c49d1f64",
            timeout=60,
        )
        assert response.status_code == 401, "No-token daily report detail should return 401"
    
    def test_raw_photo_no_token_denied(self):
        """No token: Raw photo should return 401"""
        response = requests.get(
            f"{BASE_URL}/api/job-photos/daily_report:652b4e6f-bcb6-4065-8e89-4938c49d1f64:1/raw",
            timeout=60,
        )
        assert response.status_code == 401, "No-token raw photo should return 401"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

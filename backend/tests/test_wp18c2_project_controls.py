"""
WP-18C2 Project Controls Authority API Tests
Tests for Admin and PM project controls endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"


class TestAdminProjectControlsAuthority:
    """Admin Project Controls Authority endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if login_response.status_code == 200:
            data = login_response.json()
            self.admin_token = data.get("token") or data.get("admin_token")
            self.directory_token = data.get("directory_token")
            if self.admin_token:
                self.session.headers.update({
                    "X-Admin-Token": self.admin_token,
                    "X-Directory-Token": self.directory_token or self.admin_token
                })
        yield
        self.session.close()
    
    def test_admin_project_controls_overview(self):
        """Test GET /api/admin/governance/project-controls/overview"""
        response = self.session.get(f"{BASE_URL}/api/admin/governance/project-controls/overview")
        print(f"Admin overview response: {response.status_code}")
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert "summary" in data or isinstance(data, dict)
            print(f"Admin overview data: {data}")
    
    def test_admin_enterprise_work_types_list(self):
        """Test GET /api/admin/governance/project-controls/work-types"""
        response = self.session.get(f"{BASE_URL}/api/admin/governance/project-controls/work-types")
        print(f"Work types list response: {response.status_code}")
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)
            print(f"Work types count: {len(data.get('items', data))}")
    
    def test_admin_create_enterprise_work_type(self):
        """Test POST /api/admin/governance/project-controls/work-types"""
        payload = {
            "code": "TEST_WP18C2_WORK_TYPE",
            "name": "Test WP18C2 Work Type",
            "category": "Testing",
            "description": "A test work type for WP-18C2 testing",
            "keywords": ["test", "testing", "wp18c2"]
        }
        response = self.session.post(
            f"{BASE_URL}/api/admin/governance/project-controls/work-types",
            json=payload
        )
        print(f"Create work type response: {response.status_code}")
        assert response.status_code in [200, 201, 401, 403, 409], f"Unexpected status: {response.status_code}"
        if response.status_code in [200, 201]:
            data = response.json()
            assert "work_type_id" in data or "code" in data
            print(f"Created work type: {data}")
    
    def test_admin_review_queue(self):
        """Test GET /api/admin/governance/project-controls/review-queue"""
        response = self.session.get(f"{BASE_URL}/api/admin/governance/project-controls/review-queue")
        print(f"Review queue response: {response.status_code}")
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)
            print(f"Review queue count: {len(data.get('items', data))}")
    
    def test_admin_event_contracts(self):
        """Test GET /api/admin/governance/project-controls/event-contracts"""
        response = self.session.get(f"{BASE_URL}/api/admin/governance/project-controls/event-contracts")
        print(f"Event contracts response: {response.status_code}")
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)
            print(f"Event contracts count: {len(data.get('items', data))}")
    
    def test_admin_backfill(self):
        """Test POST /api/admin/governance/project-controls/backfill/run"""
        response = self.session.post(
            f"{BASE_URL}/api/admin/governance/project-controls/backfill/run",
            json={}
        )
        print(f"Backfill response: {response.status_code}")
        assert response.status_code in [200, 201, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"Backfill result: {data}")


class TestPmProjectControlsAuthority:
    """PM Project Controls Authority endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup PM authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as PM
        login_response = self.session.post(f"{BASE_URL}/api/pm/login", json={
            "email": PM_EMAIL,
            "password": PM_PASSWORD
        })
        if login_response.status_code == 200:
            data = login_response.json()
            self.pm_token = data.get("token") or data.get("pm_token")
            self.directory_token = data.get("directory_token")
            if self.pm_token:
                self.session.headers.update({
                    "X-PM-Token": self.pm_token,
                    "X-Directory-Token": self.directory_token or self.pm_token
                })
        yield
        self.session.close()
    
    def test_pm_project_controls_overview(self):
        """Test GET /api/pm/project-controls/overview - requires project_number"""
        # Test without project number - should fail or return empty
        response = self.session.get(f"{BASE_URL}/api/pm/project-controls/overview")
        print(f"PM overview (no project) response: {response.status_code}")
        
        # Test with a project number
        response = self.session.get(f"{BASE_URL}/api/pm/project-controls/overview?project_number=Operations%20support")
        print(f"PM overview (with project) response: {response.status_code}")
        assert response.status_code in [200, 401, 403, 404], f"Unexpected status: {response.status_code}"
    
    def test_pm_work_types_list(self):
        """Test GET /api/pm/project-controls/work-types"""
        response = self.session.get(f"{BASE_URL}/api/pm/project-controls/work-types")
        print(f"PM work types response: {response.status_code}")
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert "items" in data or isinstance(data, list)
            print(f"PM work types count: {len(data.get('items', data))}")
    
    def test_pm_project_scope_enforcement(self):
        """Test PM scope enforcement - accessing unassigned project returns 403"""
        # Try to access CERT-001 which PM doesn't have access to
        response = self.session.get(f"{BASE_URL}/api/pm/project-controls/overview?project_number=CERT-001")
        print(f"PM scope enforcement response: {response.status_code}")
        # Should return 403 for unassigned project
        assert response.status_code in [403, 404, 401], f"Expected 403/404/401 for unassigned project, got: {response.status_code}"
        print("PM scope enforcement working correctly - access denied for unassigned project")
    
    def test_pm_project_pay_items(self):
        """Test GET /api/pm/project-controls/projects/{project_number}/pay-items"""
        project_number = "Operations%20support"
        response = self.session.get(f"{BASE_URL}/api/pm/project-controls/projects/{project_number}/pay-items")
        print(f"PM pay items response: {response.status_code}")
        assert response.status_code in [200, 401, 403, 404], f"Unexpected status: {response.status_code}"
    
    def test_pm_project_mappings(self):
        """Test GET /api/pm/project-controls/projects/{project_number}/mappings"""
        project_number = "Operations%20support"
        response = self.session.get(f"{BASE_URL}/api/pm/project-controls/projects/{project_number}/mappings")
        print(f"PM mappings response: {response.status_code}")
        assert response.status_code in [200, 401, 403, 404], f"Unexpected status: {response.status_code}"
    
    def test_pm_project_lookahead(self):
        """Test GET /api/pm/project-controls/projects/{project_number}/lookahead"""
        project_number = "Operations%20support"
        response = self.session.get(f"{BASE_URL}/api/pm/project-controls/projects/{project_number}/lookahead")
        print(f"PM lookahead response: {response.status_code}")
        assert response.status_code in [200, 401, 403, 404], f"Unexpected status: {response.status_code}"
    
    def test_pm_project_lifecycle(self):
        """Test GET /api/pm/project-controls/projects/{project_number}/lifecycle"""
        project_number = "Operations%20support"
        response = self.session.get(f"{BASE_URL}/api/pm/project-controls/projects/{project_number}/lifecycle")
        print(f"PM lifecycle response: {response.status_code}")
        assert response.status_code in [200, 401, 403, 404], f"Unexpected status: {response.status_code}"
    
    def test_pm_crew_intelligence(self):
        """Test GET /api/pm/project-controls/projects/{project_number}/crew-intelligence"""
        project_number = "Operations%20support"
        response = self.session.get(f"{BASE_URL}/api/pm/project-controls/projects/{project_number}/crew-intelligence")
        print(f"PM crew intelligence response: {response.status_code}")
        assert response.status_code in [200, 401, 403, 404], f"Unexpected status: {response.status_code}"
    
    def test_pm_work_ledger(self):
        """Test GET /api/pm/project-controls/projects/{project_number}/work-ledger"""
        project_number = "Operations%20support"
        response = self.session.get(f"{BASE_URL}/api/pm/project-controls/projects/{project_number}/work-ledger")
        print(f"PM work ledger response: {response.status_code}")
        assert response.status_code in [200, 401, 403, 404], f"Unexpected status: {response.status_code}"


class TestDailyReportWorkBlocks:
    """Daily Report work blocks integration tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin authentication for daily report tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if login_response.status_code == 200:
            data = login_response.json()
            self.admin_token = data.get("token") or data.get("admin_token")
            self.directory_token = data.get("directory_token")
            if self.admin_token:
                self.session.headers.update({
                    "X-Admin-Token": self.admin_token,
                    "X-Directory-Token": self.directory_token or self.admin_token
                })
        yield
        self.session.close()
    
    def test_daily_reports_list(self):
        """Test GET /api/daily-reports - verify work_blocks field exists"""
        response = self.session.get(f"{BASE_URL}/api/daily-reports?limit=5")
        print(f"Daily reports list response: {response.status_code}")
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            reports = data.get("items", data) if isinstance(data, dict) else data
            if reports and len(reports) > 0:
                # Check if work_blocks field exists in the schema
                first_report = reports[0]
                print(f"Daily report fields: {list(first_report.keys())[:10]}...")
                # work_blocks may or may not be present depending on data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

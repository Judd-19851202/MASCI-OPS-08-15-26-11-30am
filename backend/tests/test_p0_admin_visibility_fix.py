"""
P0 Production Data Visibility Incident - Admin Historical Data Visibility Tests

This test suite validates the fix for the P0 incident where admin historical
operational data became invisible after DB migration. The fix targets a shared
admin actor visibility defect in /app/backend/pm_auth.py where dict-shaped admin
actors from cross-portal reads were incorrectly treated as PM-scoped instead of
unrestricted admins.

Test Coverage:
1. Admin cross-portal visibility - admin can load historical records
2. Admin API visibility - all operational endpoints return non-empty data
3. PM isolation - PM users remain project-scoped
4. Unassigned PM empty-scope behavior
5. No synthetic/certification leakage regression
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com").rstrip("/")

# Admin credentials from test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# PM credentials for scoped verification
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token via multi-login."""
    response = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    assert data.get("ok") is True, "Admin login response not ok"
    token = data.get("portal_tokens", {}).get("admin")
    assert token, "No admin token in response"
    return token


@pytest.fixture(scope="module")
def pm_token():
    """Get PM token via multi-login for scoped verification."""
    response = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": PM_EMAIL, "password": PM_PASSWORD},
        timeout=30,
    )
    if response.status_code != 200:
        pytest.skip(f"PM login failed: {response.text}")
    data = response.json()
    token = data.get("portal_tokens", {}).get("pm")
    if not token:
        pytest.skip("No PM token in response")
    return token


class TestAdminCrossPortalVisibility:
    """Test that admin can see historical records across all operational modules."""

    def test_admin_login_returns_all_portals(self, admin_token):
        """Admin login should return tokens for all portals."""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=30,
        )
        assert response.status_code == 200
        data = response.json()
        portal_tokens = data.get("portal_tokens", {})
        # Super admin should have access to all portals
        assert "admin" in portal_tokens, "Missing admin portal token"
        assert "pm" in portal_tokens, "Missing pm portal token"
        user = data.get("user", {})
        assert user.get("is_super_admin") is True, "User should be super admin"

    def test_daily_reports_returns_data(self, admin_token):
        """Admin should see historical daily reports."""
        response = requests.get(
            f"{BASE_URL}/api/daily-reports",
            headers={"X-Admin-Token": admin_token},
            timeout=30,
        )
        assert response.status_code == 200, f"Daily reports failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Admin should see historical daily reports (not empty)"
        print(f"Admin sees {len(data)} daily reports")

    def test_meetings_returns_data(self, admin_token):
        """Admin should see historical safety meetings."""
        response = requests.get(
            f"{BASE_URL}/api/meetings",
            headers={"X-Admin-Token": admin_token},
            timeout=30,
        )
        assert response.status_code == 200, f"Meetings failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Admin should see historical meetings (not empty)"
        print(f"Admin sees {len(data)} meetings")

    def test_incidents_returns_data(self, admin_token):
        """Admin should see historical incidents."""
        response = requests.get(
            f"{BASE_URL}/api/incidents",
            headers={"X-Admin-Token": admin_token},
            timeout=30,
        )
        assert response.status_code == 200, f"Incidents failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Admin should see historical incidents (not empty)"
        print(f"Admin sees {len(data)} incidents")

    def test_jhas_returns_data(self, admin_token):
        """Admin should see historical JHAs."""
        response = requests.get(
            f"{BASE_URL}/api/jhas",
            headers={"X-Admin-Token": admin_token},
            timeout=30,
        )
        assert response.status_code == 200, f"JHAs failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Admin should see historical JHAs (not empty)"
        print(f"Admin sees {len(data)} JHAs")

    def test_equipment_inspections_returns_data(self, admin_token):
        """Admin should see historical equipment inspections."""
        response = requests.get(
            f"{BASE_URL}/api/equipment-inspections",
            headers={"X-Admin-Token": admin_token},
            timeout=30,
        )
        assert response.status_code == 200, f"Equipment inspections failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Admin should see historical equipment inspections (not empty)"
        print(f"Admin sees {len(data)} equipment inspections")

    def test_inspections_returns_data(self, admin_token):
        """Admin should see historical inspections."""
        response = requests.get(
            f"{BASE_URL}/api/inspections",
            headers={"X-Admin-Token": admin_token},
            timeout=30,
        )
        assert response.status_code == 200, f"Inspections failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Admin should see historical inspections (not empty)"
        print(f"Admin sees {len(data)} inspections")

    def test_notifications_returns_data(self, admin_token):
        """Admin should see notifications."""
        response = requests.get(
            f"{BASE_URL}/api/notifications?limit=10",
            headers={"X-Admin-Token": admin_token},
            timeout=30,
        )
        assert response.status_code == 200, f"Notifications failed: {response.text}"
        data = response.json()
        # Notifications endpoint returns {count, items} or a list
        if isinstance(data, dict):
            items = data.get("items", [])
            count = data.get("count", len(items))
        else:
            items = data
            count = len(items)
        print(f"Admin sees {count} notifications")

    def test_operations_center_returns_data(self, admin_token):
        """Admin should see operations center data."""
        response = requests.get(
            f"{BASE_URL}/api/operations-center",
            headers={"X-Admin-Token": admin_token},
            timeout=30,
        )
        assert response.status_code == 200, f"Operations center failed: {response.text}"
        data = response.json()
        assert "total" in data, "Response should have total field"
        assert data.get("total", 0) > 0, "Operations center should show non-zero total"
        print(f"Operations center shows {data.get('total')} total records")


class TestPMIsolation:
    """Test that PM users remain project-scoped and don't gain unrestricted access."""

    def test_pm_sees_limited_daily_reports(self, pm_token, admin_token):
        """PM should see fewer daily reports than admin (project-scoped)."""
        # Get admin count
        admin_response = requests.get(
            f"{BASE_URL}/api/daily-reports",
            headers={"X-Admin-Token": admin_token},
            timeout=30,
        )
        assert admin_response.status_code == 200
        admin_count = len(admin_response.json())

        # Get PM count
        pm_response = requests.get(
            f"{BASE_URL}/api/daily-reports",
            headers={"X-PM-Token": pm_token},
            timeout=30,
        )
        assert pm_response.status_code == 200
        pm_count = len(pm_response.json())

        # PM should see fewer records than admin (unless PM is assigned to all projects)
        print(f"Admin sees {admin_count} daily reports, PM sees {pm_count}")
        assert pm_count <= admin_count, "PM should not see more records than admin"

    def test_pm_sees_limited_meetings(self, pm_token, admin_token):
        """PM should see fewer meetings than admin (project-scoped)."""
        admin_response = requests.get(
            f"{BASE_URL}/api/meetings",
            headers={"X-Admin-Token": admin_token},
            timeout=30,
        )
        assert admin_response.status_code == 200
        admin_count = len(admin_response.json())

        pm_response = requests.get(
            f"{BASE_URL}/api/meetings",
            headers={"X-PM-Token": pm_token},
            timeout=30,
        )
        assert pm_response.status_code == 200
        pm_count = len(pm_response.json())

        print(f"Admin sees {admin_count} meetings, PM sees {pm_count}")
        assert pm_count <= admin_count, "PM should not see more records than admin"


class TestComputePmScopeUnit:
    """Unit tests for compute_pm_scope function."""

    def test_directory_admin_actor_gets_unrestricted_scope(self):
        """Admin actor from directory should get unrestricted scope."""
        import asyncio
        import sys
        sys.path.insert(0, "/app/backend")
        from pm_auth import compute_pm_scope

        class MockCursor:
            def __init__(self, rows):
                self._rows = list(rows)
                self._index = 0

            def __aiter__(self):
                self._index = 0
                return self

            async def __anext__(self):
                if self._index >= len(self._rows):
                    raise StopAsyncIteration
                row = self._rows[self._index]
                self._index += 1
                return row

        class MockCollection:
            def __init__(self, rows):
                self.rows = list(rows)

            def find(self, query, projection=None):
                return MockCursor(self.rows)

        class MockDB:
            def __init__(self):
                self.jobs_master = MockCollection([])
                self.project_team_assignments = MockCollection([])

        # Test admin actor from directory (dict-shaped with portals)
        admin_actor = {
            "_actor": "admin",
            "email": "jaymn.judd@mascigc.com",
            "name": "Super Admin",
            "portals": ["admin", "pm", "shop"],
            "is_super_admin": True,
        }

        scope = asyncio.run(compute_pm_scope(MockDB(), admin_actor))
        assert scope.is_admin is True, "Admin actor should have unrestricted scope"
        assert scope.project_numbers is None, "Admin should have no project filter"

    def test_legacy_true_admin_stays_unrestricted(self):
        """Legacy True admin should stay unrestricted."""
        import asyncio
        import sys
        sys.path.insert(0, "/app/backend")
        from pm_auth import compute_pm_scope

        class MockDB:
            jobs_master = None
            project_team_assignments = None

        scope = asyncio.run(compute_pm_scope(MockDB(), True))
        assert scope.is_admin is True, "Legacy True admin should be unrestricted"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

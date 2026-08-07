"""
WP-18C9 Portfolio Intelligence backend tests.
"""

import os

import pytest
import requests
from dotenv import dotenv_values

from services.portfolio_intelligence import _financial_rollup


def _base_url():
    env_value = (os.environ.get("REACT_APP_BACKEND_URL") or "").rstrip("/")
    if env_value and ".preview.emergentagent.com" not in env_value:
        return env_value
    file_value = str((dotenv_values("/app/frontend/.env").get("REACT_APP_BACKEND_URL") or "")).rstrip("/")
    if file_value:
        return file_value
    return "http://127.0.0.1:8001"


BASE_URL = _base_url()
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
PM_EMAIL = "pm.scope.forensic@example.com"
PM_PASSWORD = "ForensicPm2026!"
PM_SCOPE = {"ZZ-FOR-ASSIGN-01", "ZZ-FOR-ASSIGN-02"}


def wait_for_backend(timeout_seconds=120):
    deadline = __import__("time").time() + timeout_seconds
    while __import__("time").time() < deadline:
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=5)
            if response.status_code == 200:
                return
        except Exception:
            pass
        __import__("time").sleep(2)
    raise RuntimeError(f"Backend health did not become ready at {BASE_URL}")


class TestPortfolioIntelligenceMath:
    def test_financial_rollup_uses_aggregate_totals_not_average_ratios(self):
        rows = [
            {"financial": {"ev": 100.0, "ac": 50.0, "pv": 80.0, "bac": 120.0, "etc": 25.0, "eac": 75.0}},
            {"financial": {"ev": 10.0, "ac": 20.0, "pv": 40.0, "bac": 50.0, "etc": 30.0, "eac": 50.0}},
        ]
        rollup = _financial_rollup(rows)
        assert rollup["cpi"] == 1.5714
        assert rollup["spi"] == 0.9167
        assert rollup["cpi"] != 1.25
        assert rollup["coverage"]["comparable_projects"] == 2


class TestPortfolioIntelligenceApi:
    @pytest.fixture(scope="class")
    def admin_tokens(self):
        wait_for_backend()
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "portal": "admin"},
            headers={"X-Device-Id": "c9-pytest-admin", "X-Test-Rate-Limit-Bypass": "1"},
            timeout=120,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        portal_tokens = data.get("portal_tokens") or {}
        return {
            "admin_token": portal_tokens.get("admin") or data.get("admin_token") or data.get("token"),
            "directory_token": data.get("session_token") or data.get("directory_token"),
        }

    @pytest.fixture(scope="class")
    def pm_token(self):
        wait_for_backend()
        response = requests.post(
            f"{BASE_URL}/api/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            headers={"X-Device-Id": "c9-pytest-pm", "X-Test-Rate-Limit-Bypass": "1"},
            timeout=120,
        )
        assert response.status_code == 200, response.text
        return response.json().get("token") or response.json().get("access_token")

    def test_admin_portfolio_snapshot_get(self, admin_tokens):
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/portfolio-intelligence",
            headers={
                "X-Admin-Token": admin_tokens["admin_token"],
                "X-Directory-Token": admin_tokens["directory_token"],
            },
            timeout=180,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data.get("schema_version") == "WP18C9/v1"
        assert data.get("audience") == "executive"
        assert data.get("scope", {}).get("project_count", 0) > 0
        assert data.get("blocked_dependencies", {}).get("open_blocked_by_c9_count") == 0
        assert "portfolio_summary" in data
        assert "projects" in data
        assert data.get("projects"), "Expected non-empty project list"
        first = data["projects"][0]
        assert "source_lineage" in first
        assert "drilldowns" in first
        assert "priority_band" in first

    def test_admin_portfolio_refresh_and_export(self, admin_tokens):
        headers = {
            "X-Admin-Token": admin_tokens["admin_token"],
            "X-Directory-Token": admin_tokens["directory_token"],
        }
        refresh = requests.post(
            f"{BASE_URL}/api/admin/governance/project-controls/portfolio-intelligence/refresh",
            headers=headers,
            timeout=300,
        )
        assert refresh.status_code == 200, refresh.text
        refreshed = refresh.json()
        assert refreshed.get("blocked_dependencies", {}).get("open_blocked_by_c9_count") == 0
        export = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/portfolio-intelligence/export",
            headers=headers,
            timeout=180,
        )
        assert export.status_code == 200, export.text
        assert "text/csv" in export.headers.get("content-type", "")
        assert "attachment" in export.headers.get("content-disposition", "")
        assert "project_number,project_name,priority_band" in export.text.splitlines()[0]

    def test_pm_portfolio_scope_is_restricted(self, pm_token):
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/portfolio-intelligence",
            headers={"X-PM-Token": pm_token},
            timeout=180,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data.get("audience") == "pm"
        assert data.get("scope", {}).get("mode") == "scoped"
        project_numbers = {row.get("project_number") for row in (data.get("projects") or [])}
        assert project_numbers == PM_SCOPE
        for row in data.get("projects") or []:
            drilldowns = row.get("drilldowns") or {}
            assert str(drilldowns.get("forecasting") or "").startswith("/pm/")
            assert str(drilldowns.get("earned_value") or "").startswith("/pm/")

    def test_pm_portfolio_export(self, pm_token):
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/portfolio-intelligence/export",
            headers={"X-PM-Token": pm_token},
            timeout=180,
        )
        assert response.status_code == 200, response.text
        assert "text/csv" in response.headers.get("content-type", "")

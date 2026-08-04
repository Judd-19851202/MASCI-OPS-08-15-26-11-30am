import os
import time
from pathlib import Path

import pytest
import requests


def _load_base_url() -> str:
    env_value = (os.environ.get("REACT_APP_BACKEND_URL") or "").strip().rstrip("/")
    if env_value:
        return env_value
    env_file = Path("/app/frontend/.env")
    if not env_file.exists():
        return ""
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'").rstrip("/")
    return ""


BASE_URL = _load_base_url()
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
TEST_PROJECT = "ZZ-RUNTIME-CERT-2026"


class TestWP18C6OperationalIntelligenceAPI:
    @pytest.fixture(scope="class")
    def pm_headers(self):
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL is not configured for runtime API verification")
        response = requests.post(
            f"{BASE_URL}/api/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            timeout=30,
        )
        if response.status_code != 200:
            pytest.skip(f"PM login failed: {response.status_code}")
        token = response.json().get("token") or response.json().get("pm_token")
        return {"X-PM-Token": token}

    @pytest.fixture(scope="class")
    def admin_headers(self):
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL is not configured for runtime API verification")
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "portal": "admin"},
            timeout=30,
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code}")
        data = response.json()
        return {
            "X-Admin-Token": ((data.get("portal_tokens") or {}).get("admin") or data.get("admin_token") or data.get("token")),
            "X-Directory-Token": data.get("session_token") or data.get("directory_token") or "",
        }

    def test_wp18c6_pm_snapshot_is_governed(self, pm_headers):
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/operational-intelligence",
            headers=pm_headers,
            timeout=60,
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["metric_engine_authority"] == "Governed Metric Engine"
        assert payload["authority_contract"]["all_calculations_from"] == "Governed Metric Engine"
        assert payload["summary"]["manual_reporting_entries_added"] == 0
        metric = payload["metric_cards"][0]
        for field in (
            "definition",
            "formula",
            "owner",
            "source_records",
            "work_block_lineage",
            "confidence",
            "freshness",
            "version",
            "audit_trail",
            "calculation_timestamp",
            "supporting_evidence",
            "drilldown_path",
        ):
            assert field in metric

    def test_wp18c6_pm_export_is_centralized_csv(self, pm_headers):
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/operational-intelligence/export",
            headers=pm_headers,
            timeout=60,
        )
        assert response.status_code == 200, response.text
        assert "text/csv" in response.headers.get("content-type", "")
        assert response.text.splitlines()[0] == "section,metric_id,label,value,unit,confidence,notes"

    def test_wp18c6_admin_governance_and_backfill_queue(self, admin_headers):
        overview = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/operational-intelligence/overview?project_number={TEST_PROJECT}&force_refresh=true",
            headers=admin_headers,
            timeout=60,
        )
        assert overview.status_code == 200, overview.text
        payload = overview.json()
        assert payload["snapshot"]["metric_engine_authority"] == "Governed Metric Engine"

        queue = requests.post(
            f"{BASE_URL}/api/admin/governance/project-controls/operational-intelligence/backfill/run?force=true",
            headers=admin_headers,
            timeout=30,
        )
        assert queue.status_code == 200, queue.text
        assert queue.json()["status"] == "queued"

        time.sleep(5)
        after = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/operational-intelligence/overview?project_number={TEST_PROJECT}",
            headers=admin_headers,
            timeout=60,
        )
        assert after.status_code == 200, after.text
        assert after.json()["backfill"]["status"] in {"running", "completed"}
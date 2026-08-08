"""
WP-18C4 Schedule Authority API Tests
Verifies overview, CSV import governance, activation, and export lanes.
"""

import io
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
ADMIN_EMAIL = "ops8-admin-only-preview@example.com"
ADMIN_PASSWORD = "AdminOnlyOps8!"
TEST_PROJECT = "ZZ-RUNTIME-CERT-2026"


class TestWP18C4ScheduleAPIs:
    @pytest.fixture(scope="class")
    def admin_session(self):
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL is not configured for runtime API verification")
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code}")
        data = response.json()
        admin_token = (data.get("portal_tokens") or {}).get("admin")
        directory_token = data.get("session_token") or ""
        if not admin_token or not directory_token:
            pytest.skip("Admin fixture missing admin/session token")
        session.headers.update(
            {
                "X-Admin-Token": admin_token,
                "X-Directory-Token": directory_token,
            }
        )
        return session

    @pytest.fixture(scope="class")
    def pm_session(self):
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL is not configured for runtime API verification")
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
        )
        if response.status_code != 200:
            pytest.skip(f"PM login failed: {response.status_code}")
        data = response.json()
        session.headers.update({"X-PM-Token": data.get("token") or data.get("pm_token")})
        return session

    def test_admin_schedule_overview_returns_200(self, admin_session):
        response = admin_session.get(f"{BASE_URL}/api/admin/governance/project-controls/schedule/overview")
        assert response.status_code == 200, response.text
        data = response.json()
        assert "summary" in data
        assert "versions" in data
        assert "imports" in data
        assert "review_queue" in data

    def test_admin_schedule_backfill_queues_work(self, admin_session):
        response = admin_session.post(f"{BASE_URL}/api/admin/governance/project-controls/schedule/backfill/run")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data.get("ok") is True
        assert data.get("status") == "queued"

    def test_pm_schedule_overview_returns_200(self, pm_session):
        response = pm_session.get(f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/schedule/overview")
        assert response.status_code == 200, response.text
        data = response.json()
        assert "project" in data
        assert "authority_boundaries" in data
        assert data["authority_boundaries"]["budget_truth"] == "project_budget_lines"
        assert data["authority_boundaries"]["daily_field_actuals"] == "daily_reports"
        assert data["authority_boundaries"]["ai_role"] == "advisory_only"

    def test_pm_schedule_csv_import_review_activate_and_export(self, pm_session):
        budget_response = pm_session.get(f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/budget/overview")
        assert budget_response.status_code == 200, budget_response.text
        budget_data = budget_response.json()
        active_lines = budget_data.get("active_lines_preview") or []
        if not active_lines:
            pytest.skip("No active budget lines available for schedule certification flow")

        line = active_lines[0]
        activity_suffix = str(int(time.time()))[-6:]
        activity_id = f"ACT-{activity_suffix}"
        csv_content = (
            "Activity ID,Activity Name,Phase,Work Package,Project Cost Code,Customer Pay Item,Start Date,Finish Date,Duration,Owner,Priority\n"
            f"{activity_id},Certified Drainage Install,{line.get('phase_id') or 'PH-1'},{line.get('work_package_id') or 'WP-CERT'},{line.get('project_cost_code') or ''},{line.get('customer_pay_item_number') or ''},2026-08-10,2026-08-12,3,Certified PM,high\n"
        )

        import_response = pm_session.post(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/schedule/imports",
            data={
                "source_kind": "csv",
                "target_version_kind": "master_schedule",
                "version_name": f"Runtime Cert {activity_suffix}",
            },
            headers={key: value for key, value in pm_session.headers.items() if key.lower() != "content-type"},
            files={"file": (f"schedule-{activity_suffix}.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        )
        assert import_response.status_code == 200, import_response.text
        import_detail = import_response.json()
        session = import_detail.get("session") or {}
        rows = import_detail.get("rows") or []
        assert session.get("import_id")
        assert rows, import_detail

        row = rows[0]
        review_response = pm_session.post(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/schedule/imports/{session['import_id']}/rows/{row['row_id']}/review",
            json={
                "action": "approve",
                "activity_id": activity_id,
                "activity_name": "Certified Drainage Install",
                "phase_id": line.get("phase_id") or "PH-1",
                "work_package_id": line.get("work_package_id") or "WP-CERT",
                "budget_line_id": line.get("budget_line_id"),
                "customer_pay_item_number": line.get("customer_pay_item_number"),
                "enterprise_work_type_id": line.get("enterprise_work_type_id"),
                "project_cost_code": line.get("project_cost_code"),
                "planned_start_date": "2026-08-10",
                "planned_finish_date": "2026-08-12",
                "duration_days": 3,
                "calendar_name": "Default",
                "status": "not_started",
                "percent_complete": 0,
                "owner": "Certified PM",
                "priority": "high",
                "notes": "Runtime certification row",
                "planned_crew_ids": [{"crew_id": "crew-cert", "label": "Crew Cert"}],
                "planned_employee_ids": [{"employee_id": "emp-cert", "label": "Employee Cert"}],
                "planned_equipment_ids": [{"equipment_id": "eq-cert", "label": "Excavator Cert"}],
                "planned_materials": [{"material_id": "mat-cert", "description": "Drainage Pipe", "quantity": 25, "unit": "LF"}],
                "planned_vendor_refs": [{"vendor_id": "ven-cert", "vendor_name": "Supply Cert"}],
                "planned_subcontractor_refs": [{"vendor_id": "sub-cert", "subcontractor_name": "Civil Cert"}],
                "planned_production_quantity": 25,
                "planned_hours": 16,
                "planned_constraints": [{"constraint_id": "con-cert", "category": "weather", "title": "Weather watch", "status": "planned", "notes": "Monitor rain"}],
                "review_note": "Approved for runtime certification",
            },
        )
        assert review_response.status_code == 200, review_response.text
        reviewed_row = review_response.json()["row"]
        assert reviewed_row["review_status"] == "approved"

        activate_response = pm_session.post(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/schedule/imports/{session['import_id']}/activate",
            json={},
        )
        assert activate_response.status_code == 200, activate_response.text
        activate_data = activate_response.json()
        assert activate_data.get("ok") is True
        assert activate_data.get("activity_count", 0) >= 1
        version_id = activate_data["version"]["version_id"]

        export_response = pm_session.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/schedule/export",
            params={"version_id": version_id, "export_kind": "master_schedule_csv"},
        )
        assert export_response.status_code == 200, export_response.text
        assert "text/csv" in export_response.headers.get("content-type", "")
        assert activity_id in export_response.text

        crew_export_response = pm_session.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/schedule/export",
            params={"version_id": version_id, "export_kind": "crew_plan_csv"},
        )
        assert crew_export_response.status_code == 200, crew_export_response.text
        assert "Crew Cert" in crew_export_response.text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
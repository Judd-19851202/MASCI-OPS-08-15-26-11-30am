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


BASE_URL = os.environ.get("LOCAL_BACKEND_URL", "http://127.0.0.1:8001").rstrip("/")
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
TEST_PROJECT = "ZZ-RUNTIME-CERT-2026"


class TestWP18C5ScheduleActualsAPIs:
    @pytest.fixture(scope="class")
    def admin_session(self):
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL is not configured for runtime API verification")
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "portal": "admin"},
            headers={"X-Device-Id": "wp18c5-admin", "X-Test-Rate-Limit-Bypass": "1"},
            timeout=30,
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code}")
        data = response.json()
        session.headers.update(
            {
                "X-Admin-Token": ((data.get("portal_tokens") or {}).get("admin") or data.get("admin_token") or data.get("token")),
                "X-Directory-Token": data.get("session_token") or data.get("directory_token") or "",
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
            headers={"X-Device-Id": "wp18c5-pm", "X-Test-Rate-Limit-Bypass": "1"},
            timeout=30,
        )
        if response.status_code != 200:
            pytest.skip(f"PM login failed: {response.status_code}")
        data = response.json()
        session.headers.update({"X-PM-Token": data.get("token") or data.get("pm_token")})
        return session

    def test_wp18c5_runtime_actuals_chain(self, admin_session, pm_session):
        budget_response = pm_session.get(f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/budget/overview", timeout=45)
        assert budget_response.status_code == 200, budget_response.text
        active_lines = (budget_response.json() or {}).get("active_lines_preview") or []
        if not active_lines:
            pytest.skip("No active budget lines available for C5 runtime certification flow")
        line = active_lines[0]

        suffix = str(int(time.time()))[-6:]
        activity_id = f"ACT-C5-{suffix}"
        csv_content = (
            "Activity ID,Activity Name,Phase,Work Package,Project Cost Code,Customer Pay Item,Start Date,Finish Date,Duration,Owner,Priority\n"
            f"{activity_id},Certified C5 Install,{line.get('phase_id') or 'PH-1'},{line.get('work_package_id') or 'WP-C5'},{line.get('project_cost_code') or ''},{line.get('customer_pay_item_number') or ''},2026-08-20,2026-08-22,3,Certified PM,high\n"
        )

        import_response = pm_session.post(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/schedule/imports",
            data={
                "source_kind": "csv",
                "target_version_kind": "master_schedule",
                "version_name": f"C5 Runtime {suffix}",
            },
            headers={key: value for key, value in pm_session.headers.items() if key.lower() != "content-type"},
            files={"file": (f"schedule-c5-{suffix}.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
            timeout=60,
        )
        assert import_response.status_code == 200, import_response.text
        import_detail = import_response.json()
        session = import_detail.get("session") or {}
        rows = import_detail.get("rows") or []
        assert session.get("import_id")
        assert rows

        row = rows[0]
        review_response = pm_session.post(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/schedule/imports/{session['import_id']}/rows/{row['row_id']}/review",
            json={
                "action": "approve",
                "activity_id": activity_id,
                "activity_name": "Certified C5 Install",
                "phase_id": line.get("phase_id") or "PH-1",
                "work_package_id": line.get("work_package_id") or "WP-C5",
                "budget_line_id": line.get("budget_line_id"),
                "customer_pay_item_number": line.get("customer_pay_item_number"),
                "enterprise_work_type_id": line.get("enterprise_work_type_id"),
                "project_cost_code": line.get("project_cost_code"),
                "planned_start_date": "2026-08-20",
                "planned_finish_date": "2026-08-22",
                "duration_days": 3,
                "calendar_name": "Default",
                "status": "not_started",
                "percent_complete": 0,
                "owner": "Certified PM",
                "priority": "high",
                "notes": "C5 runtime certification row",
                "planned_crew_ids": [{"crew_id": "crew-c5", "label": "Crew C5"}],
                "planned_equipment_ids": [{"equipment_id": "eq-c5", "label": "Excavator C5"}],
                "planned_materials": [{"material_id": "mat-c5", "description": "Pipe", "quantity": 10, "unit": "LF"}],
                "planned_vendor_refs": [{"vendor_id": "ven-c5", "vendor_name": "Vendor C5"}],
                "planned_subcontractor_refs": [{"vendor_id": "sub-c5", "subcontractor_name": "Sub C5"}],
                "planned_production_quantity": 10,
                "planned_hours": 12,
                "review_note": "Approved for C5 runtime certification",
            },
            timeout=60,
        )
        assert review_response.status_code == 200, review_response.text

        activate_response = pm_session.post(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/schedule/imports/{session['import_id']}/activate",
            json={},
            timeout=60,
        )
        assert activate_response.status_code == 200, activate_response.text
        version_id = activate_response.json()["version"]["version_id"]

        equipment_master = admin_session.get(f"{BASE_URL}/api/equipment-master", timeout=45).json()
        suppliers = admin_session.get(f"{BASE_URL}/api/suppliers", timeout=45).json()
        equipment_item = (equipment_master.get("items") or [{}])[0]
        supplier_item = (suppliers.get("items") or [{}])[0]

        report_date = f"2026-08-{int(suffix[-2:]) % 20 + 10:02d}"
        daily_payload = {
            "project_name": "C5 Runtime Project",
            "project_number": TEST_PROJECT,
            "location": "Certified Area",
            "report_date": report_date,
            "prepared_by": "Certified Superintendent",
            "weather_summary": "Clear",
            "general_notes": f"C5 runtime certification {suffix}",
            "ai_accepted_summary": "Approved summary: C5 runtime certification placed the governed work block and preserved the PM review actuals gate.",
            "ai_accepted_summary_meta": {"accepted": True, "accepted_at": f"{report_date}T18:30:00Z", "source": "manual", "edited_by_supervisor": True},
            "materials": [
                {
                    "description": "Pipe",
                    "quantity": 10,
                    "unit": "LF",
                    "supplier": supplier_item.get("name") or "Vendor C5",
                    "cost_code": line.get("project_cost_code") or "",
                }
            ],
            "equipment": [
                {
                    "equipment_id": equipment_item.get("id") or "",
                    "description": equipment_item.get("unit_number") or equipment_item.get("display_label") or "Excavator C5",
                    "hours_used": 4,
                    "cost_code": line.get("project_cost_code") or "",
                }
            ],
            "subcontractors": [
                {
                    "company": supplier_item.get("name") or "Vendor C5",
                    "trade": "Utility",
                    "hours": 4,
                    "count": 1,
                    "work_performed": "Support install",
                    "cost_code": line.get("project_cost_code") or "",
                }
            ],
            "cost_code_quantities": [
                {
                    "cost_code": line.get("project_cost_code") or "",
                    "item_name": "Certified C5 Install",
                    "installed_quantity": 10,
                    "unit_of_measure": "LF",
                    "cpm_activity_id": activity_id,
                    "cpm_activity_name": "Certified C5 Install",
                }
            ],
            "work_blocks": [
                {
                    "title": "Certified install",
                    "work_package_id": line.get("work_package_id") or "WP-C5",
                    "customer_pay_item_number": line.get("customer_pay_item_number") or "",
                    "cost_code": line.get("project_cost_code") or "",
                    "schedule_activity_id": activity_id,
                    "schedule_activity_name": "Certified C5 Install",
                    "installed_quantity": 10,
                    "unit": "LF",
                    "location": "Certified Area",
                    "labor_entries": [{"name": "Crew Lead", "hours": 8}],
                    "equipment_entries": [{"equipment_id": equipment_item.get("id") or "", "description": equipment_item.get("unit_number") or "Excavator C5", "hours_used": 4}],
                    "material_entries": [{"description": "Pipe", "quantity": 10, "unit": "LF", "supplier": supplier_item.get("name") or "Vendor C5"}],
                    "subcontractor_entries": [{"company": supplier_item.get("name") or "Vendor C5", "hours": 4}],
                }
            ],
        }
        daily_response = admin_session.post(f"{BASE_URL}/api/daily-reports", json=daily_payload, timeout=90)
        assert daily_response.status_code in (200, 201), daily_response.text
        daily_data = daily_response.json()
        report_id = daily_data.get("id")
        assert report_id

        actuals_response = pm_session.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/schedule/actuals/overview",
            params={"work_date": report_date},
            timeout=60,
        )
        assert actuals_response.status_code == 200, actuals_response.text
        actuals_data = actuals_response.json()
        candidate = next((row for row in (actuals_data.get("candidates") or []) if row.get("source_report_id") == report_id), None)
        assert candidate, actuals_data
        assert candidate.get("activity_resolution", {}).get("resolved_activity_id") == activity_id

        approve_response = admin_session.post(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/schedule/actuals/candidates/{candidate['candidate_id']}/review",
            json={
                "action": "approve",
                "activity_id": activity_id,
                "activity_name": "Certified C5 Install",
                "actual_start_date": report_date,
                "actual_finish_date": report_date,
                "approved_percent_complete": 100,
                "approved_installed_quantity": 10,
                "schedule_progress_status": "completed",
                "review_note": "Approved in runtime certification",
            },
            timeout=60,
        )
        assert approve_response.status_code == 200, approve_response.text
        approved_candidate = approve_response.json()["candidate"]
        assert approved_candidate["review_status"] == "approved"
        assert approved_candidate["approved_actual"]["activity_id"] == activity_id

        daily_plan_response = pm_session.put(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/schedule/daily-work-plan",
            json={
                "work_date": report_date,
                "status": "published",
                "notes": "Runtime certified C5 daily plan",
                "items": [
                    {
                        "plan_item_id": f"plan-item:{activity_id}",
                        "activity_id": activity_id,
                        "activity_name": "Certified C5 Install",
                        "work_package_id": line.get("work_package_id") or "WP-C5",
                        "budget_line_id": line.get("budget_line_id") or "",
                        "customer_pay_item_number": line.get("customer_pay_item_number") or "",
                        "project_cost_code": line.get("project_cost_code") or "",
                        "planned_quantity": 10,
                        "planned_hours": 12,
                        "actual_status": "completed",
                        "approved_percent_complete": 100,
                        "daily_goal_note": "Finish and verify the certified scope.",
                    }
                ],
            },
            timeout=60,
        )
        assert daily_plan_response.status_code == 200, daily_plan_response.text
        assert daily_plan_response.json()["daily_work_plan"]["status"] == "published"

        read_report = pm_session.get(f"{BASE_URL}/api/daily-reports/{report_id}", timeout=60)
        assert read_report.status_code == 200, read_report.text
        report_data = read_report.json()
        assert report_data.get("schedule_actual_candidate_summary", {}).get("count", 0) >= 1
        assert any(row.get("candidate_id") == candidate["candidate_id"] for row in (report_data.get("schedule_actual_candidates") or []))

        forecast_export = pm_session.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/schedule/export",
            params={"version_id": version_id, "export_kind": "forecast_schedule_csv"},
            timeout=60,
        )
        assert forecast_export.status_code == 200, forecast_export.text
        assert activity_id in forecast_export.text

        actuals_export = pm_session.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/schedule/export",
            params={"version_id": version_id, "export_kind": "schedule_actuals_csv"},
            timeout=60,
        )
        assert actuals_export.status_code == 200, actuals_export.text
        assert candidate["candidate_id"] in actuals_export.text
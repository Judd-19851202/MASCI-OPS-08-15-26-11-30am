from __future__ import annotations

from pathlib import Path

import requests
from pymongo import MongoClient
from requests import exceptions as req_exc


def _read_env(path: str, key: str) -> str:
    for line in Path(path).read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


BASE_URL = _read_env("/app/frontend/.env", "REACT_APP_BACKEND_URL").rstrip("/")
INTERNAL_BASE_URL = "http://127.0.0.1:8001"
MONGO_URL = _read_env("/app/backend/.env", "MONGO_URL")
DB_NAME = _read_env("/app/backend/.env", "DB_NAME")
PROJECT = "ZZ-RUNTIME-CERT-2026"
WORK_DATE = "2026-08-29"


def _db():
    return MongoClient(MONGO_URL)[DB_NAME]


def _pm_headers() -> dict[str, str]:
    resp = _request(
        "POST",
        "/api/pm/login",
        json={"email": "cert.pm@example.com", "password": "CertProof2026!"},
        timeout=30,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    return {"X-PM-Token": body.get("token") or body.get("pm_token")}


def _request(method: str, path: str, **kwargs):
    try:
        return requests.request(method, f"{BASE_URL}{path}", **kwargs)
    except (req_exc.ReadTimeout, req_exc.ConnectionError):
        return requests.request(method, f"{INTERNAL_BASE_URL}{path}", **kwargs)


def _latest_work_ledger_window(db) -> list[dict]:
    return list(
        db.project_controls_work_ledger
        .find({"project_number": PROJECT}, {"_id": 0})
        .sort([("report_date", -1)])
        .limit(50)
    )


def test_schedule_lookahead_and_actual_chain_match_source_authority():
    db = _db()
    headers = _pm_headers()

    schedule = _request("GET", f"/api/pm/project-controls/projects/{PROJECT}/schedule/overview", headers=headers, timeout=60)
    lookahead = _request("GET", f"/api/pm/project-controls/projects/{PROJECT}/schedule/lookahead", headers=headers, timeout=60)
    daily_plan = _request("GET", f"/api/pm/project-controls/projects/{PROJECT}/schedule/daily-work-plan?work_date={WORK_DATE}", headers=headers, timeout=60)

    assert schedule.status_code == 200, schedule.text
    assert lookahead.status_code == 200, lookahead.text
    assert daily_plan.status_code == 200, daily_plan.text

    schedule_body = schedule.json()
    lookahead_body = lookahead.json()
    daily_plan_body = daily_plan.json()

    job = db.jobs_master.find_one({"project_number": PROJECT}, {"_id": 0})
    active_version = db.project_schedule_versions.find_one({"project_number": PROJECT, "status": "active"}, {"_id": 0})
    active_activity = db.project_schedule_activities.find_one(
        {"project_number": PROJECT, "version_id": active_version["version_id"]},
        {"_id": 0},
    )
    lookahead_doc = db.project_controls_lookaheads.find_one({"project_number": PROJECT, "lookahead_id": f"lookahead:{PROJECT}:current"}, {"_id": 0})
    daily_plan_doc = db.project_daily_work_plans.find_one({"project_number": PROJECT, "work_date": WORK_DATE}, {"_id": 0})
    approved_candidates = list(
        db.project_schedule_actual_candidates.find(
            {"project_number": PROJECT, "review_status": "approved"},
            {"_id": 0, "approved_actual.approved_installed_quantity": 1},
        )
    )
    work_ledger_rows = _latest_work_ledger_window(db)

    assigned_code = (job.get("assigned_cost_codes") or [None])[0]
    schedule_activity = (schedule_body.get("activities") or [None])[0]
    lookahead_task = (lookahead_body.get("tasks") or [None])[0]
    daily_plan_item = (daily_plan_body.get("items") or [None])[0]

    assert schedule_body["project"]["project_number"] == job["project_number"] == PROJECT
    assert schedule_body["project"]["project_name"] == job["project_name"]

    assert schedule_body["active_version"]["version_id"] == active_version["version_id"]
    assert schedule_body["active_version"]["baseline_version_id"] == active_version["baseline_version_id"]
    assert schedule_activity["activity_id"] == active_activity["activity_id"]
    assert schedule_activity["planned_start_date"] == active_activity["planned_start_date"] == assigned_code["schedule_start_date"]
    assert schedule_activity["planned_finish_date"] == active_activity["planned_finish_date"]
    assert schedule_activity["budget_line_id"] == active_activity["budget_line_id"] == assigned_code["budget_line_id"]
    assert schedule_activity["customer_pay_item_number"] == active_activity["customer_pay_item_number"] == assigned_code["customer_pay_item_number"]
    assert schedule_activity["project_cost_code"] == active_activity["project_cost_code"] == assigned_code["project_cost_code"]
    assert (schedule_activity.get("planned_assignments") or {}).get("planned_production_quantity") == assigned_code["planned_production_quantity"]
    assert (schedule_activity.get("planned_assignments") or {}).get("planned_hours") == assigned_code["planned_hours"]

    assert lookahead_body["lookahead_id"] == lookahead_doc["lookahead_id"]
    assert lookahead_task["activity_id"] == active_activity["activity_id"]
    assert lookahead_task["budget_line_id"] == active_activity["budget_line_id"]
    assert lookahead_task["customer_pay_item_number"] == active_activity["customer_pay_item_number"]
    assert lookahead_task["planned_start"] == active_activity["planned_start_date"]
    assert lookahead_task["planned_finish"] == active_activity["planned_finish_date"]
    assert lookahead_body["constraints"] == lookahead_doc["constraints"] == lookahead_task["planned_constraints"]

    assert daily_plan_body["version_id"] == daily_plan_doc["version_id"]
    assert daily_plan_body["baseline_version_id"] == daily_plan_doc["baseline_version_id"] == active_version["baseline_version_id"]
    assert daily_plan_body["lookahead_id"] == daily_plan_doc["lookahead_id"] == lookahead_body["lookahead_id"]
    assert daily_plan_item["budget_line_id"] == active_activity["budget_line_id"]
    assert daily_plan_item["customer_pay_item_number"] == active_activity["customer_pay_item_number"]
    assert daily_plan_item["project_cost_code"] == active_activity["project_cost_code"]

    expected_work_block_links = sum(1 for row in work_ledger_rows if row.get("schedule_activity_id"))
    expected_daily_reports = len({row.get("source_report_id") for row in work_ledger_rows if row.get("source_report_id")})
    expected_production_rows = sum(1 for row in work_ledger_rows if float(row.get("installed_quantity") or 0) > 0)
    expected_approved_actuals = len(approved_candidates)

    assert schedule_body["actual_chain"]["work_block_links"] == expected_work_block_links
    assert schedule_body["actual_chain"]["daily_report_rows"] == expected_daily_reports
    assert schedule_body["actual_chain"]["production_rows"] == expected_production_rows
    assert schedule_body["actual_chain"]["approved_actuals"] == expected_approved_actuals


def test_source_to_c7_c8_c9_values_reconcile_for_certification_project():
    db = _db()
    headers = _pm_headers()

    c7 = _request("GET", f"/api/pm/project-controls/projects/{PROJECT}/forecasting/workspace", headers=headers, timeout=90)
    c8 = _request("GET", f"/api/pm/project-controls/projects/{PROJECT}/earned-value", headers=headers, timeout=90)
    c9 = _request("GET", "/api/pm/project-controls/portfolio-intelligence", headers=headers, timeout=90)

    assert c7.status_code == 200, c7.text
    assert c8.status_code == 200, c8.text
    assert c9.status_code == 200, c9.text

    c7_body = c7.json()
    c8_body = c8.json()
    c9_body = c9.json()

    job = db.jobs_master.find_one({"project_number": PROJECT}, {"_id": 0})
    active_version = db.project_schedule_versions.find_one({"project_number": PROJECT, "status": "active"}, {"_id": 0})
    active_activity = db.project_schedule_activities.find_one(
        {"project_number": PROJECT, "version_id": active_version["version_id"]},
        {"_id": 0},
    )
    assigned_code = (job.get("assigned_cost_codes") or [None])[0]
    progress_code = ((job.get("cost_code_progress") or {}).get("codes") or [None])[0]
    po_request = db.po_requests.find_one({"project_number": PROJECT}, {"_id": 0})
    approved_candidates = list(
        db.project_schedule_actual_candidates.find(
            {"project_number": PROJECT, "review_status": "approved"},
            {"_id": 0, "approved_actual.approved_installed_quantity": 1},
        )
    )
    approved_quantity = sum(float((row.get("approved_actual") or {}).get("approved_installed_quantity") or 0) for row in approved_candidates)

    c7_task = ((((c7_body.get("schedule") or {}).get("scenario_comparison") or {}).get("baseline") or {}).get("schedule", {}).get("tasks") or [None])[0]
    c8_line = (c8_body.get("lines") or [None])[0]
    c9_project = next((row for row in (c9_body.get("projects") or []) if row.get("project_number") == PROJECT), None)

    assert c7_task["cpm_activity_id"] == assigned_code["cpm_activity_id"]
    assert c7_task["baseline_start_date"] == assigned_code["schedule_start_date"]
    assert c7_task["baseline_finish_date"] == active_activity["planned_finish_date"]
    assert c7_task["authorized_quantity"] == assigned_code["authorized_quantity"]
    assert c7_task["forecast_quantity"] == assigned_code["forecast_quantity"]
    assert c7_task["installed_quantity"] == progress_code["installed_quantity"]
    assert c7_task["progress_percent"] == progress_code["progress_percent"]
    if progress_code.get("actual_finish_date"):
        assert c7_task["forecast_finish_date"] == progress_code["actual_finish_date"]

    assert c8_line["approved_quantity"] == approved_quantity
    assert c8_line["commitment_amount"] == po_request["approved_amount"] == po_request["receipt_amount"] == 900.0
    assert c8_body["summary"]["bac"] == c9_project["financial"]["bac"] == c8_line["bac"]
    assert c8_body["summary"]["ev"] == c9_project["financial"]["ev"] == c8_line["ev"]
    assert c8_body["summary"]["ac"] == c9_project["financial"]["ac"] == c8_line["ac"]
    assert c8_body["summary"]["eac"] == c9_project["financial"]["eac"] == c8_line["eac"]
    assert c7_task["forecast_finish_date"] == c9_project["schedule"]["likely_finish_date"]
    assert c7_task["committed_finish_date"] == c9_project["schedule"]["committed_finish_date"]
    assert c8_line["commitment_amount"] == c9_project["cost_forecast"]["commitment_exposure"] == c9_project["cost_forecast"]["projected_final_cost_floor"]
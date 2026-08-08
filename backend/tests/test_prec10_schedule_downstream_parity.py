from __future__ import annotations

from pathlib import Path

import requests


def _read_env(path: str, key: str) -> str:
    for line in Path(path).read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


BASE_URL = _read_env("/app/frontend/.env", "REACT_APP_BACKEND_URL").rstrip("/")
PROJECT = "ZZ-RUNTIME-CERT-2026"


def _request_with_retry(method: str, path: str, *, headers: dict | None = None, json_body: dict | None = None, attempts: int = 3):
    last_error = None
    for _ in range(attempts):
        try:
            return requests.request(method, f"{BASE_URL}{path}", headers=headers, json=json_body, timeout=60)
        except requests.RequestException as exc:
            last_error = exc
    if last_error:
        raise last_error
    raise RuntimeError(f"failed request {method} {path}")


def _pm_headers() -> dict:
    r = _request_with_retry("POST", "/api/pm/login", json_body={"email": "cert.pm@example.com", "password": "CertProof2026!"})
    assert r.status_code == 200, r.text
    return {"X-PM-Token": r.json().get("token") or r.json().get("pm_token")}


def _admin_headers() -> dict:
    r = _request_with_retry("POST", "/api/auth/multi-login", json_body={"email": "ops8-admin-only-preview@example.com", "password": "AdminOnlyOps8!", "portal": "admin"})
    assert r.status_code == 200, r.text
    body = r.json()
    return {
        "X-Admin-Token": (body.get("portal_tokens") or {}).get("admin"),
        "X-Directory-Token": body.get("session_token"),
    }


def _load_parity_payloads() -> tuple[dict, dict, dict, dict]:
    pm_headers = _pm_headers()
    admin_headers = _admin_headers()
    schedule = _request_with_retry("GET", f"/api/pm/project-controls/projects/{PROJECT}/schedule/overview", headers=pm_headers)
    c7 = _request_with_retry("GET", f"/api/pm/project-controls/projects/{PROJECT}/forecasting/workspace", headers=pm_headers)
    c8 = _request_with_retry("GET", f"/api/admin/governance/project-controls/projects/{PROJECT}/earned-value", headers=admin_headers)
    c9 = _request_with_retry("GET", "/api/admin/governance/project-controls/portfolio-intelligence", headers=admin_headers)
    for resp in (schedule, c7, c8, c9):
        assert resp.status_code == 200, resp.text
    return schedule.json(), c7.json(), c8.json(), c9.json()


def test_schedule_c7_c8_c9_parity_for_certification_project():
    schedule, c7, c8, c9 = _load_parity_payloads()

    schedule_activity = (schedule.get("activities") or [{}])[0]
    c7_task = (((c7.get("schedule") or {}).get("scenario_comparison") or {}).get("baseline") or {}).get("schedule", {}).get("tasks", [{}])[0]
    c8_line = next((row for row in (c8.get("lines") or []) if row.get("budget_line_id")), {})
    c9_project = next((row for row in (c9.get("projects") or []) if row.get("project_number") == PROJECT), {})

    assert schedule_activity.get("planned_start_date") == c7_task.get("baseline_start_date")
    assert schedule_activity.get("planned_finish_date") == c7_task.get("baseline_finish_date")
    assert (schedule_activity.get("planned_assignments") or {}).get("planned_production_quantity") == c7_task.get("forecast_quantity")

    assert c7_task.get("committed_finish_date") == (c9_project.get("schedule") or {}).get("committed_finish_date")
    assert c7_task.get("forecast_finish_date") == (c9_project.get("schedule") or {}).get("likely_finish_date")

    assert c8.get("summary", {}).get("bac") == (c9_project.get("financial") or {}).get("bac")
    assert c8.get("summary", {}).get("ev") == (c9_project.get("financial") or {}).get("ev")
    assert c8.get("summary", {}).get("ac") == (c9_project.get("financial") or {}).get("ac")
    assert c8.get("summary", {}).get("cpi") == (c9_project.get("financial") or {}).get("cpi")

    evidence = c8_line.get("evidence") or {}
    assert evidence.get("active_activity_count") == schedule.get("counts", {}).get("activities")
    assert evidence.get("baseline_activity_count") == schedule.get("counts", {}).get("activities")


def test_schedule_version_history_preserves_prior_versions():
    schedule, _, _, _ = _load_parity_payloads()
    active_version = schedule.get("active_version") or {}
    versions = schedule.get("versions") or []
    version_ids = {row.get("version_id") for row in versions}

    assert active_version.get("version_id") in version_ids
    assert active_version.get("parent_version_id")
    assert active_version.get("baseline_version_id")
    assert active_version.get("parent_version_id") in version_ids
    assert active_version.get("baseline_preserved") is True
    assert active_version.get("created_by")
    assert active_version.get("approved_by")
    assert active_version.get("activated_by")
    assert active_version.get("created_at")
    assert active_version.get("approved_at")
    assert active_version.get("activated_at")


def test_rolling_two_week_lookahead_stays_a_governed_overlay():
    pm_headers = _pm_headers()
    schedule = _request_with_retry("GET", f"/api/pm/project-controls/projects/{PROJECT}/schedule/overview", headers=pm_headers)
    lookahead = _request_with_retry("GET", f"/api/pm/project-controls/projects/{PROJECT}/schedule/lookahead", headers=pm_headers)
    daily_plan = _request_with_retry("GET", f"/api/pm/project-controls/projects/{PROJECT}/schedule/daily-work-plan?work_date=2026-08-08", headers=pm_headers)
    for resp in (schedule, lookahead, daily_plan):
        assert resp.status_code == 200, resp.text

    schedule_body = schedule.json()
    lookahead_body = lookahead.json()
    daily_plan_body = daily_plan.json()

    schedule_activity = (schedule_body.get("activities") or [{}])[0]
    lookahead_task = (lookahead_body.get("tasks") or [{}])[0]

    assert schedule_body.get("actual_chain", {}).get("work_block_links", 0) > 0
    assert schedule_body.get("actual_chain", {}).get("daily_report_rows", 0) > 0
    assert schedule_body.get("actual_chain", {}).get("production_rows", 0) > 0

    assert lookahead_task.get("budget_line_id") == schedule_activity.get("budget_line_id")
    assert lookahead_task.get("customer_pay_item_number") == schedule_activity.get("customer_pay_item_number")
    assert lookahead_task.get("planned_constraints") == (schedule_activity.get("planned_assignments") or {}).get("planned_constraints")
    assert lookahead_body.get("constraints") == lookahead_task.get("planned_constraints")

    assert daily_plan_body.get("lookahead_id") == lookahead_body.get("lookahead_id")
    assert daily_plan_body.get("baseline_version_id") == (schedule_body.get("active_version") or {}).get("baseline_version_id")
    assert daily_plan_body.get("version_id") != daily_plan_body.get("baseline_version_id")
    assert "never overwrite baseline history" in (daily_plan_body.get("notes") or "")
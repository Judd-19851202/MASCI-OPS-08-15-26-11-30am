from __future__ import annotations

import os
from pathlib import Path
from time import sleep

import requests
from pymongo import MongoClient

from lib.corrective_action_truth import open_corrective_action_query, overdue_corrective_action_query
from lib.synthetic_corrective_action_filter import apply_synthetic_corrective_action_exclusion


def _kv(path: str, key: str) -> str:
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        return ""
    return ""


BASE_URL = (_kv("/app/frontend/.env", "REACT_APP_BACKEND_URL") or os.environ.get("REACT_APP_BACKEND_URL", "")).rstrip("/")
MONGO_URL = _kv("/app/backend/.env", "MONGO_URL")
DB_NAME = _kv("/app/backend/.env", "DB_NAME")

SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"

_CLOSED_CA = ["Completed", "Closed", "Cancelled"]


def _admin_headers() -> dict[str, str]:
    last_exc = None
    for attempt in range(6):
        try:
            resp = requests.post(
                f"{BASE_URL}/api/auth/multi-login",
                json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "X-Admin-Token": data["portal_tokens"]["admin"],
                "X-Directory-Token": data["session_token"],
            }
        except requests.RequestException as exc:  # pragma: no cover - transient preview ingress
            last_exc = exc
            sleep(min(2 + attempt, 6))
    raise AssertionError(f"admin login failed after retries: {last_exc}")


def _db():
    return MongoClient(MONGO_URL)[DB_NAME]


def test_executive_overview_reconciles_canonical_safety_counts():
    headers = _admin_headers()
    data = requests.get(f"{BASE_URL}/api/admin/executive/overview", headers=headers, timeout=30).json()
    db = _db()

    assert "kpi_metadata" in data
    assert "verdict" in data["kpi_metadata"]

    api_incidents = data["tiles"]["safety"]["unresolved_incidents"]
    db_incidents = db.incidents.count_documents({"resolution_status": {"$ne": "Closed"}})
    assert api_incidents == db_incidents

    api_open_ca = data["tiles"]["safety"]["unresolved_corrective_actions"]
    db_open_ca = db.corrective_actions.count_documents(
        apply_synthetic_corrective_action_exclusion(open_corrective_action_query())
    )
    assert api_open_ca == db_open_ca

    generated_at = data["generated_at"]
    api_overdue_ca = data["tiles"]["overdue"]["overdue_corrective_actions"]
    db_overdue_ca = db.corrective_actions.count_documents(
        apply_synthetic_corrective_action_exclusion(
            overdue_corrective_action_query(today_iso=generated_at[:10])
        )
    )
    assert api_overdue_ca == db_overdue_ca


def test_project_health_reconciles_row_counts_and_contract_metadata():
    headers = _admin_headers()
    data = requests.get(f"{BASE_URL}/api/project-health", headers=headers, timeout=30).json()
    db = _db()

    assert "kpi_metadata" in data
    assert "indicators" in data["kpi_metadata"]
    assert data["summary"]["total"] == len(data["rows"])
    assert data["summary"]["red"] + data["summary"]["amber"] + data["summary"]["green"] == data["summary"]["total"]

    if not data["rows"]:
        return

    row = data["rows"][0]
    pn = row["project_number"]
    generated_at = data["generated_at"]

    db_incidents = db.incidents.count_documents({
        "project_number": pn,
        "resolution_status": {"$ne": "Closed"},
    })
    assert row["indicators"]["incidents_open"] == db_incidents

    db_ca_overdue = db.corrective_actions.count_documents({
        "project_number": pn,
        **apply_synthetic_corrective_action_exclusion(
            overdue_corrective_action_query(today_iso=generated_at[:10])
        ),
    })
    assert row["indicators"]["ca_overdue"] == db_ca_overdue


def test_hr_request_queue_and_timeoff_metadata_present():
    headers = _admin_headers()
    req_data = requests.get(f"{BASE_URL}/api/hr/employee-requests?status=pending", headers=headers, timeout=30).json()
    time_off = requests.get(f"{BASE_URL}/api/field-leadership/time-off/stats", headers=headers, timeout=30).json()
    roster = requests.get(f"{BASE_URL}/api/hr/employee-roster?limit=5000", headers=headers, timeout=30).json()
    exp = requests.get(f"{BASE_URL}/api/operations/expirations/summary", headers=headers, timeout=30).json()
    db = _db()

    assert req_data["pending_count"] == db.employee_requests.count_documents({"status": "pending"})
    assert req_data.get("kpi_metadata", {}).get("api_endpoint") == "/api/hr/employee-requests"
    assert time_off.get("kpi_metadata", {}).get("api_endpoint") == "/api/field-leadership/time-off/stats"
    assert roster.get("kpi_metadata", {}).get("api_endpoint") == "/api/hr/employee-roster"
    assert exp.get("kpi_metadata", {}).get("api_endpoint") == "/api/operations/expirations/summary"
    assert roster["count"] == len(roster["items"])


def test_safety_company_metadata_and_band_logic():
    headers = _admin_headers()
    data = requests.get(f"{BASE_URL}/api/safety/company/safety-kpis?window=30d", headers=headers, timeout=30).json()

    assert data.get("kpi_metadata", {}).get("page", {}).get("api_endpoint") == "/api/safety/company/safety-kpis"
    assert "cards" in data["kpi_metadata"]

    totals = data["totals"]
    if totals["escalation_gap_count"] > 0 or totals["injuries_reported"] > 0:
        expected = "red"
    elif totals["incident_count"] > 0 or totals["near_miss_count"] > 0:
        expected = "amber"
    else:
        expected = "green"
    assert data["status_band"] == expected
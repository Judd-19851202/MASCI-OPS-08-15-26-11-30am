from __future__ import annotations

import os
from pathlib import Path
from time import sleep

import requests
from pymongo import MongoClient


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
_ALL_CLOSED_CA = {
    "Completed", "Closed", "Cancelled", "Canceled",
    "completed", "closed", "cancelled", "canceled",
}
_HIDDEN_CLASSIFICATIONS = {
    "preview_certification",
    "synthetic_test",
    "legacy_hidden_backfill",
}


def _is_operator_visible_corrective_action(row: dict) -> bool:
    cls = str(row.get("technical_record_classification") or "").strip().lower()
    if cls in _HIDDEN_CLASSIFICATIONS:
        return False
    if row.get("truth_visibility_scope") == "technical_audit_only":
        return False
    if row.get("synthetic_record") is True:
        return False
    if row.get("hidden_from_operations") is True:
        return False
    if row.get("certification_record") is True:
        return False
    return True


def _is_open_corrective_action(row: dict) -> bool:
    return _is_operator_visible_corrective_action(row) and str(row.get("status") or "") not in _ALL_CLOSED_CA


def _is_overdue_corrective_action(row: dict, *, today_iso: str) -> bool:
    if not _is_open_corrective_action(row):
        return False
    due = (row.get("due_date") or "").strip()
    return bool(due) and due[:10] < today_iso


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
    rows = list(db.corrective_actions.find({}, {"_id": 0}))
    db_open_ca = sum(1 for row in rows if _is_open_corrective_action(row))
    assert api_open_ca == db_open_ca

    generated_at = data["generated_at"]
    api_overdue_ca = data["tiles"]["overdue"]["overdue_corrective_actions"]
    db_overdue_ca = sum(1 for row in rows if _is_overdue_corrective_action(row, today_iso=generated_at[:10]))
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

    db_ca_overdue = sum(
        1
        for row in db.corrective_actions.find({"project_number": pn}, {"_id": 0})
        if _is_overdue_corrective_action(row, today_iso=generated_at[:10])
    )
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


def test_safety_overview_and_dispatch_summary_publish_governed_metadata():
    headers = _admin_headers()
    safety = requests.get(f"{BASE_URL}/api/admin/safety/overview", headers=headers, timeout=30).json()
    dispatch = requests.get(f"{BASE_URL}/api/dispatch/command/summary", headers=headers, timeout=30).json()

    assert safety.get("kpi_metadata", {}).get("page", {}).get("api_endpoint") == "/api/safety/overview"
    assert "corrective_actions" in safety.get("kpi_metadata", {}).get("sections", {})
    assert "compliance" in safety.get("kpi_metadata", {}).get("sections", {})
    assert "incidents" in safety.get("kpi_metadata", {}).get("sections", {})

    assert dispatch.get("kpi_metadata", {}).get("page", {}).get("api_endpoint") == "/api/dispatch/command/summary"
    assert "drivers_haul" in dispatch.get("kpi_metadata", {}).get("sections", {})
    assert "fleet_shop" in dispatch.get("kpi_metadata", {}).get("sections", {})
    assert "safety_watch" in dispatch.get("kpi_metadata", {}).get("sections", {})
    assert "command_strip" in dispatch.get("kpi_metadata", {}).get("sections", {})
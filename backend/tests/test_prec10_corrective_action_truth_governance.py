from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
from pymongo import MongoClient


def _read_env(path: str, key: str) -> str:
    for line in Path(path).read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


BASE_URL = _read_env("/app/frontend/.env", "REACT_APP_BACKEND_URL").rstrip("/")
MONGO_URL = _read_env("/app/backend/.env", "MONGO_URL")
DB_NAME = _read_env("/app/backend/.env", "DB_NAME")

_CLOSED = {
    "Completed", "Closed", "Cancelled", "Canceled",
    "completed", "closed", "cancelled", "canceled",
}
_HIDDEN_CLASSIFICATIONS = {
    "preview_certification",
    "synthetic_test",
    "legacy_hidden_backfill",
}


def _db():
    return MongoClient(MONGO_URL)[DB_NAME]


def _admin_headers() -> dict[str, str]:
    resp = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=30,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    return {
        "X-Admin-Token": body["portal_tokens"]["admin"],
        "X-Directory-Token": body["session_token"],
    }


def _safety_headers() -> dict[str, str]:
    resp = requests.post(
        f"{BASE_URL}/api/safety/login",
        json={"email": "cert.safety@example.com", "password": "CertProof2026!"},
        timeout=30,
    )
    assert resp.status_code == 200, resp.text
    return {"X-Safety-Token": resp.json()["token"]}


def _is_visible_operator_ca(row: dict) -> bool:
    classification = str(row.get("technical_record_classification") or "").strip().lower()
    if classification in _HIDDEN_CLASSIFICATIONS:
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


def _is_open_ca(row: dict) -> bool:
    return _is_visible_operator_ca(row) and str(row.get("status") or "") not in _CLOSED


def _is_overdue_ca(row: dict, *, today_iso: str) -> bool:
    if not _is_open_ca(row):
        return False
    due = (row.get("due_date") or "").strip()
    return bool(due) and due[:10] < today_iso


def _expected_counts(db, *, today_iso: str) -> tuple[int, int]:
    rows = list(db.corrective_actions.find({}, {"_id": 0}))
    open_count = sum(1 for row in rows if _is_open_ca(row))
    overdue_count = sum(1 for row in rows if _is_overdue_ca(row, today_iso=today_iso))
    return open_count, overdue_count


def _project_overdue_count(db, project_number: str, *, today_iso: str) -> int:
    rows = db.corrective_actions.find({"project_number": project_number}, {"_id": 0})
    return sum(1 for row in rows if _is_overdue_ca(row, today_iso=today_iso))


def _csv_rows(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def _executive_export_counts(headers: dict[str, str]) -> dict[str, int]:
    resp = requests.get(f"{BASE_URL}/api/safety/exports/executive?format=csv", headers=headers, timeout=30)
    assert resp.status_code == 200, resp.text
    rows = _csv_rows(resp.text)
    return {row["Indicator"]: int(row["Value"]) for row in rows}


def _corrective_action_export_count(headers: dict[str, str]) -> int:
    resp = requests.get(f"{BASE_URL}/api/safety/exports/corrective-actions?format=csv", headers=headers, timeout=30)
    assert resp.status_code == 200, resp.text
    rows = _csv_rows(resp.text)
    return len(rows)


def test_independent_corrective_action_oracle_matches_runtime_consumers():
    admin_headers = _admin_headers()
    safety_headers = _safety_headers()
    db = _db()

    safety_overview = requests.get(f"{BASE_URL}/api/safety/overview", headers=safety_headers, timeout=30)
    executive_overview = requests.get(f"{BASE_URL}/api/admin/executive/overview", headers=admin_headers, timeout=30)
    project_health = requests.get(f"{BASE_URL}/api/project-health", headers=admin_headers, timeout=30)
    ca_list = requests.get(f"{BASE_URL}/api/safety/corrective-actions", headers=safety_headers, timeout=30)

    assert safety_overview.status_code == 200, safety_overview.text
    assert executive_overview.status_code == 200, executive_overview.text
    assert project_health.status_code == 200, project_health.text
    assert ca_list.status_code == 200, ca_list.text

    safety_body = safety_overview.json()
    executive_body = executive_overview.json()
    project_health_body = project_health.json()
    today_iso = safety_body["generated_at"][:10]

    expected_open, expected_overdue = _expected_counts(db, today_iso=today_iso)
    export_counts = _executive_export_counts(safety_headers)

    assert expected_open == safety_body["corrective_actions_open"] == executive_body["tiles"]["safety"]["unresolved_corrective_actions"]
    assert expected_overdue == safety_body["corrective_actions_overdue"] == executive_body["tiles"]["overdue"]["overdue_corrective_actions"]
    visible_rows = ca_list.json()
    assert export_counts["Open Corrective Actions"] == expected_open
    assert export_counts["Overdue Corrective Actions"] == expected_overdue
    assert sum(1 for row in visible_rows if _is_open_ca(row)) == expected_open
    assert all(_is_visible_operator_ca(row) for row in visible_rows)
    assert _corrective_action_export_count(safety_headers) == expected_open

    row_2412 = next((row for row in (project_health_body.get("rows") or []) if row.get("project_number") == "24-12"), None)
    assert row_2412 is not None
    assert row_2412["indicators"]["ca_overdue"] == _project_overdue_count(db, "24-12", today_iso=today_iso)


def test_explicit_hidden_marker_excludes_row_without_name_heuristics_and_keeps_auditability():
    admin_headers = _admin_headers()
    safety_headers = _safety_headers()
    db = _db()
    marker = f"hostile-explicit-hidden-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": marker,
        "title": "Operator follow-up required",
        "description": "Neutral title: should only be hidden because governed markers say so.",
        "source_kind": "manual",
        "source_id": "",
        "project_number": "24-12",
        "assigned_to_name": "Neutral Owner",
        "assigned_to_email": "neutral.owner@example.com",
        "priority": "Medium",
        "due_date": "2026-06-15",
        "status": "Open",
        "created_by_name": "Technical Auditor",
        "created_by_email": "auditor@example.com",
        "created_at": now,
        "updated_at": now,
        "technical_record_classification": "synthetic_test",
        "truth_visibility_scope": "technical_audit_only",
        "governed_classification_reason": "hostile_explicit_marker_test",
        "governed_classification_source": "pytest:test_prec10_corrective_action_truth_governance.py",
        "synthetic_record": True,
        "hidden_from_operations": True,
        "certification_record": False,
    }
    before_safety = requests.get(f"{BASE_URL}/api/safety/overview", headers=safety_headers, timeout=30).json()
    before_exec = requests.get(f"{BASE_URL}/api/admin/executive/overview", headers=admin_headers, timeout=30).json()
    before_export = _executive_export_counts(safety_headers)
    before_project = requests.get(f"{BASE_URL}/api/project-health", headers=admin_headers, timeout=30).json()
    before_list_ids = {row["id"] for row in requests.get(f"{BASE_URL}/api/safety/corrective-actions", headers=safety_headers, timeout=30).json()}

    try:
        db.corrective_actions.insert_one(doc)

        after_safety = requests.get(f"{BASE_URL}/api/safety/overview", headers=safety_headers, timeout=30).json()
        after_exec = requests.get(f"{BASE_URL}/api/admin/executive/overview", headers=admin_headers, timeout=30).json()
        after_export = _executive_export_counts(safety_headers)
        after_project = requests.get(f"{BASE_URL}/api/project-health", headers=admin_headers, timeout=30).json()
        after_list = requests.get(f"{BASE_URL}/api/safety/corrective-actions", headers=safety_headers, timeout=30).json()
        technical = requests.get(
            f"{BASE_URL}/api/admin/safety/corrective-actions/technical?q={marker}",
            headers=admin_headers,
            timeout=30,
        ).json()

        assert after_safety["corrective_actions_open"] == before_safety["corrective_actions_open"]
        assert after_safety["corrective_actions_overdue"] == before_safety["corrective_actions_overdue"]
        assert after_exec["tiles"]["safety"]["unresolved_corrective_actions"] == before_exec["tiles"]["safety"]["unresolved_corrective_actions"]
        assert after_exec["tiles"]["overdue"]["overdue_corrective_actions"] == before_exec["tiles"]["overdue"]["overdue_corrective_actions"]
        assert after_export == before_export
        assert {row["id"] for row in after_list} == before_list_ids

        before_2412 = next(row for row in before_project["rows"] if row["project_number"] == "24-12")
        after_2412 = next(row for row in after_project["rows"] if row["project_number"] == "24-12")
        assert after_2412["indicators"]["ca_overdue"] == before_2412["indicators"]["ca_overdue"]
        assert technical["count"] >= 1
        assert any(row["id"] == marker for row in technical["items"])
    finally:
        db.corrective_actions.delete_one({"id": marker})


def test_live_record_with_test_like_name_is_not_hidden_by_heuristic_matching():
    admin_headers = _admin_headers()
    safety_headers = _safety_headers()
    db = _db()
    marker = f"hostile-visible-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": marker,
        "title": "iter356-lifecycle-test-looking but operator-visible",
        "description": "Looks like a test by name only. Governed markers say this is live.",
        "source_kind": "manual",
        "source_id": "",
        "project_number": "24-12",
        "assigned_to_name": "Real Owner",
        "assigned_to_email": "real.owner@example.com",
        "priority": "Medium",
        "due_date": "2026-06-15",
        "status": "Open",
        "created_by_name": "Field Operator",
        "created_by_email": "field.operator@example.com",
        "created_at": now,
        "updated_at": now,
        "technical_record_classification": "live_operational",
        "truth_visibility_scope": "live_operations",
        "governed_classification_reason": "hostile_visible_control",
        "governed_classification_source": "pytest:test_prec10_corrective_action_truth_governance.py",
        "synthetic_record": False,
        "hidden_from_operations": False,
        "certification_record": False,
    }
    before_safety = requests.get(f"{BASE_URL}/api/safety/overview", headers=safety_headers, timeout=30).json()
    before_exec = requests.get(f"{BASE_URL}/api/admin/executive/overview", headers=admin_headers, timeout=30).json()
    before_export = _executive_export_counts(safety_headers)
    before_project = requests.get(f"{BASE_URL}/api/project-health", headers=admin_headers, timeout=30).json()

    try:
        db.corrective_actions.insert_one(doc)

        after_safety = requests.get(f"{BASE_URL}/api/safety/overview", headers=safety_headers, timeout=30).json()
        after_exec = requests.get(f"{BASE_URL}/api/admin/executive/overview", headers=admin_headers, timeout=30).json()
        after_export = _executive_export_counts(safety_headers)
        after_project = requests.get(f"{BASE_URL}/api/project-health", headers=admin_headers, timeout=30).json()
        after_list = requests.get(f"{BASE_URL}/api/safety/corrective-actions", headers=safety_headers, timeout=30).json()
        technical = requests.get(
            f"{BASE_URL}/api/admin/safety/corrective-actions/technical?q={marker}",
            headers=admin_headers,
            timeout=30,
        ).json()

        assert after_safety["corrective_actions_open"] == before_safety["corrective_actions_open"] + 1
        assert after_safety["corrective_actions_overdue"] == before_safety["corrective_actions_overdue"] + 1
        assert after_exec["tiles"]["safety"]["unresolved_corrective_actions"] == before_exec["tiles"]["safety"]["unresolved_corrective_actions"] + 1
        assert after_exec["tiles"]["overdue"]["overdue_corrective_actions"] == before_exec["tiles"]["overdue"]["overdue_corrective_actions"] + 1
        assert after_export["Open Corrective Actions"] == before_export["Open Corrective Actions"] + 1
        assert after_export["Overdue Corrective Actions"] == before_export["Overdue Corrective Actions"] + 1

        before_2412 = next(row for row in before_project["rows"] if row["project_number"] == "24-12")
        after_2412 = next(row for row in after_project["rows"] if row["project_number"] == "24-12")
        assert after_2412["indicators"]["ca_overdue"] == before_2412["indicators"]["ca_overdue"] + 1
        assert any(row["id"] == marker for row in after_list)
        assert technical["count"] == 0
    finally:
        db.corrective_actions.delete_one({"id": marker})
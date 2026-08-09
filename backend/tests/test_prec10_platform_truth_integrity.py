from __future__ import annotations

import asyncio
from pathlib import Path

import requests
from motor.motor_asyncio import AsyncIOMotorClient

from lib.platform_truth_integrity import scan_platform_contamination_integrity, scan_platform_stale_derived_state, scan_platform_truth_integrity


def _read_env(path: str, key: str) -> str:
    for line in Path(path).read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


BASE_URL = "http://127.0.0.1:8001"
MONGO_URL = _read_env("/app/backend/.env", "MONGO_URL")
DB_NAME = _read_env("/app/backend/.env", "DB_NAME")


def _db():
    return AsyncIOMotorClient(MONGO_URL)[DB_NAME]


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


def test_platform_truth_integrity_route_and_scans_reflect_current_state():
    async def _run():
        db = _db()
        contamination = await scan_platform_contamination_integrity(db)
        stale = await scan_platform_stale_derived_state(db)
        truth = await scan_platform_truth_integrity(db)
        return contamination, stale, truth

    contamination, stale, truth = asyncio.run(_run())

    assert contamination["overall_status"] == "green"
    by_family = {row["family_id"]: row for row in contamination["families"] if row.get("present")}
    assert by_family["corrective_actions"]["status"] == "green"
    assert by_family["employees"]["status"] == "green"
    assert by_family["employees"]["heuristic_only_count"] == 0
    assert by_family["daily_reports"]["status"] == "green"
    assert by_family["daily_reports"]["heuristic_only_count"] == 0
    assert by_family["field_leadership_records"]["status"] == "green"
    assert by_family["project_forecasting_snapshots"]["status"] in {"green", "yellow"}

    by_check = {row["id"]: row for row in stale["checks"]}
    assert by_check["schedule_lookahead_active_signature"]["status"] == "green"
    assert by_check["lookahead_daily_plan_current_signature"]["status"] == "green"
    assert by_check["c7_to_c8_snapshot_dependency"]["status"] == "green"
    assert by_check["c7_c8_to_c9_snapshot_dependency"]["status"] == "green"
    assert by_check["safety_source_to_aggregate"]["status"] == "green"

    cross = truth["cross_entity"]
    assert cross["overall_status"] == "green"
    cross_by_id = {row["id"]: row for row in cross["checks"]}
    assert cross_by_id["project_team_assignment_authority"]["status"] == "green"
    assert cross_by_id["transport_employee_projection_authority"]["status"] == "green"
    assert cross_by_id["meeting_attendee_identity_normalization"]["status"] == "green"
    assert cross_by_id["incident_project_and_submitter_lineage"]["status"] == "green"
    assert cross_by_id["daily_report_project_and_submitter_lineage"]["status"] == "green"
    assert cross_by_id["equipment_preop_asset_and_operator_lineage"]["status"] == "green"
    assert cross_by_id["dispatch_driver_truck_project_linkage"]["status"] == "green"
    assert cross_by_id["daily_report_project_and_submitter_lineage"]["counts"]["documented_exceptions"] > 0

    headers = _admin_headers()
    resp = requests.get(f"{BASE_URL}/api/admin/platform-truth-integrity", headers=headers, timeout=180)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["contamination"]["overall_status"] == contamination["overall_status"]
    assert body["stale_derived_state"]["overall_status"] == stale["overall_status"]
    assert body["cross_entity"]["overall_status"] == cross["overall_status"]
    assert body["release_gate_blocked"] is False

    cross_resp = requests.get(
        f"{BASE_URL}/api/admin/platform-truth-integrity/cross-entity",
        headers=headers,
        timeout=180,
    )
    assert cross_resp.status_code == 200, cross_resp.text
    assert cross_resp.json()["overall_status"] == cross["overall_status"]

    exc_resp = requests.get(
        f"{BASE_URL}/api/admin/platform-truth-integrity/cross-entity/exceptions",
        headers=headers,
        timeout=180,
    )
    assert exc_resp.status_code == 200, exc_resp.text
    exc_body = exc_resp.json()
    assert exc_body["count"] > 0
    assert any(row["status"] in {"accepted_historical_gap", "excluded_non_operational"} for row in exc_body["rows"])

    csv_resp = requests.get(
        f"{BASE_URL}/api/admin/platform-truth-integrity/cross-entity/exceptions/export.csv",
        headers=headers,
        timeout=180,
    )
    assert csv_resp.status_code == 200, csv_resp.text
    assert "family,source_collection,source_record_id" in csv_resp.text

    reconcile_resp = requests.post(
        f"{BASE_URL}/api/admin/platform-truth-integrity/cross-entity/exceptions/reconcile",
        headers=headers,
        timeout=180,
    )
    assert reconcile_resp.status_code == 200, reconcile_resp.text
    reconcile_body = reconcile_resp.json()
    assert reconcile_body["reconciliation"]["total_exceptions"] > 0
    assert reconcile_body["reconciliation"]["classification_integrity"]["materially_misclassified_exceptions"] == 0

    reconciliation_resp = requests.get(
        f"{BASE_URL}/api/admin/platform-truth-integrity/cross-entity/exceptions/reconciliation",
        headers=headers,
        timeout=180,
    )
    assert reconciliation_resp.status_code == 200, reconciliation_resp.text
    reconciliation_body = reconciliation_resp.json()
    assert reconciliation_body["classification_integrity"]["materially_misclassified_exceptions"] == 0
    assert reconciliation_body["record_temporality"]["current_live_operational_records"] >= 0

    reconciliation_csv_resp = requests.get(
        f"{BASE_URL}/api/admin/platform-truth-integrity/cross-entity/exceptions/reconciliation.csv",
        headers=headers,
        timeout=180,
    )
    assert reconciliation_csv_resp.status_code == 200, reconciliation_csv_resp.text
    assert "section,metric,count" in reconciliation_csv_resp.text
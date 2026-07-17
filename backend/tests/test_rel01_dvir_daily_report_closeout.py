from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict, Iterable, List, Optional

import checklists_fleet as _ck
import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv(dotenv_path="/app/backend/.env")
load_dotenv(dotenv_path="/app/frontend/.env")

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or "").rstrip("/")
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"
CERT_FOREMAN_EMAIL = "cert.foreman@example.com"
CERT_FOREMAN_PASSWORD = "CertProof2026!"
CERT_PROJECT_NUMBER = "ZZ-RUNTIME-CERT-2026"
ONE_PX = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkAAIA"
    "AAoAAv/lxKUAAAAASUVORK5CYII="
)


def _db():
    cli = MongoClient(os.environ["MONGO_URL"])
    return cli, cli[os.environ["DB_NAME"]]


def _login(email: str, password: str) -> Dict[str, Any]:
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not configured")
    resp = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": email, "password": password},
        timeout=30,
    )
    if resp.status_code != 200:
        pytest.skip(f"multi-login failed for {email}: {resp.status_code} {resp.text[:200]}")
    return resp.json()


@pytest.fixture(scope="module")
def admin_token() -> str:
    portal_tokens = (_login(SUPER_ADMIN_EMAIL, SUPER_ADMIN_PASSWORD).get("portal_tokens") or {})
    token = portal_tokens.get("admin")
    if not token:
        pytest.skip("multi-login did not mint admin token")
    return token


@pytest.fixture(scope="module")
def field_token() -> str:
    portal_tokens = (_login(CERT_FOREMAN_EMAIL, CERT_FOREMAN_PASSWORD).get("portal_tokens") or {})
    token = portal_tokens.get("field_leadership") or portal_tokens.get("fl")
    if not token:
        pytest.skip("cert.foreman multi-login did not mint field leadership token")
    return token


def _poll_json(url: str, headers: Dict[str, str], timeout_s: float = 20.0) -> Dict[str, Any]:
    deadline = time.time() + timeout_s
    last: Optional[requests.Response] = None
    while time.time() < deadline:
        resp = requests.get(url, headers=headers, timeout=15)
        last = resp
        assert resp.status_code == 200, f"poll failed {resp.status_code}: {resp.text[:200]}"
        body = resp.json()
        if body.get("status") == "completed":
            return body
        if body.get("status") == "failed":
            pytest.fail(f"async job failed: {body}")
        time.sleep(max(float(body.get("poll_after_ms") or 1200) / 1000.0, 0.35))
    detail = last.text[:200] if last is not None else "no response"
    pytest.fail(f"async job did not complete in time: {detail}")


def _wait_for_trust_spine(
    db,
    *,
    workflow: str,
    record_ids: Iterable[str],
    stage: str,
    timeout_s: float = 12.0,
) -> Dict[str, Any]:
    ids = [str(x) for x in record_ids if x]
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        row = db.trust_spine_events.find_one(
            {"workflow": workflow, "stage": stage, "record_id": {"$in": ids}},
            {"_id": 0},
            sort=[("ts", -1)],
        )
        if row:
            return row
        time.sleep(0.4)
    pytest.fail(f"trust_spine stage {stage} missing for workflow={workflow} ids={ids}")


def _remove_dvir_artifacts(truck: str, inspection_id: Optional[str], defect_ids: List[str]) -> None:
    cli, db = _db()
    try:
        db.equipment_inspections.delete_many({"truck_unit_number": truck})
        db.fleet_defects.delete_many({"truck_unit_number": truck})
        db.fleet_status.delete_one({"unit_number": truck})
        db.fleet_audit.delete_many({"$or": [
            {"target_id": truck},
            {"target_id": inspection_id or "__none__"},
            {"target_id": {"$in": defect_ids or ["__none__"]}},
        ]})
        db.notifications.delete_many({
            "$or": [
                {"linked_source_record_id": inspection_id or "__none__"},
                {"linked_source_module": "fleet.dvir", "message": {"$regex": truck}},
            ]
        })
        db.tasks.delete_many({"source_module": "fleet.dvir", "source_record_id": inspection_id or "__none__"})
        db.trust_spine_events.delete_many({
            "workflow": "dvir",
            "record_id": {"$in": [x for x in [inspection_id, truck] if x]},
        })
    finally:
        cli.close()


def _remove_daily_report_artifacts(report_ids: List[str], doc_ids: List[str]) -> None:
    cli, db = _db()
    try:
        ids = [x for x in report_ids if x]
        docs = [x for x in doc_ids if x]
        db.daily_reports.delete_many({"id": {"$in": ids}})
        db.notifications.delete_many({"linked_source_record_id": {"$in": ids}})
        db.workflow_state_events.delete_many({"workflow": "daily_report", "record_id": {"$in": ids}})
        db.trust_spine_events.delete_many({
            "workflow": "daily-report",
            "record_id": {"$in": list(dict.fromkeys(ids + docs))},
        })
    finally:
        cli.close()


def test_rel01_dvir_delivery_and_bell_parity_preview_truth() -> None:
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not configured")
    truck = f"REL01-DVIR-{uuid.uuid4().hex[:8].upper()}"
    key = f"rel01-dvir-{uuid.uuid4().hex[:12]}"
    oos_item = "Brake lights — both sides functional"
    checklist = {item: "pass" for item in _ck.dvir_truck_items()}
    checklist[oos_item] = "fail"
    payload = {
        "kind": "dvir",
        "driver_name": "REL01 Delivery Driver",
        "inspection_date": "2026-07-17",
        "inspection_time": "07:05",
        "truck_unit_number": truck,
        "truck_checklist": checklist,
        "defect_details": {oos_item: {"note": "REL-01 proof defect", "photos": []}},
        "driver_signature": ONE_PX,
        "submitted_via": "public_tile",
    }

    inspection_id: Optional[str] = None
    defect_ids: List[str] = []
    try:
        headers = {"Content-Type": "application/json", "Idempotency-Key": key}
        first = requests.post(f"{BASE_URL}/api/fleet/inspections", json=payload, headers=headers, timeout=30)
        second = requests.post(f"{BASE_URL}/api/fleet/inspections", json=payload, headers=headers, timeout=30)
        assert first.status_code == 200, first.text[:400]
        assert second.status_code == 200, second.text[:400]

        a = first.json()
        b = second.json()
        inspection_id = a.get("inspection_id")
        assert inspection_id, a
        assert a.get("inspection_id") == b.get("inspection_id")
        assert a.get("out_of_service") is True
        assert a.get("truck_status_after") == "oos"

        cli, db = _db()
        try:
            inspection = db.equipment_inspections.find_one({"id": inspection_id}, {"_id": 0})
            defects = list(db.fleet_defects.find({"truck_unit_number": truck}, {"_id": 0}))
            notifications = list(
                db.notifications.find(
                    {"linked_source_record_id": inspection_id},
                    {"_id": 0, "type": 1, "recipient_role": 1, "severity": 1},
                )
            )
            tasks = list(
                db.tasks.find(
                    {"source_module": "fleet.dvir", "source_record_id": inspection_id},
                    {"_id": 0, "priority": 1, "assignee_role": 1},
                )
            )
            audits = list(
                db.fleet_audit.find(
                    {"action": "fleet_inspection_submitted", "target_id": inspection_id},
                    {"_id": 0, "payload": 1},
                )
            )
            defect_ids = [d.get("id") for d in defects if d.get("id")]
            assert inspection and inspection.get("out_of_service") == "Yes"
            assert len(defects) == 1
            assert any(n.get("type") == "dvir.defect.oos" and n.get("recipient_role") == "shop" for n in notifications)
            assert any(n.get("type") == "dvir.defect.oos" and n.get("recipient_role") == "dispatch" for n in notifications)
            assert len(tasks) == 1
            assert tasks[0].get("assignee_role") == "shop"
            assert tasks[0].get("priority") == "Critical"
            assert len(audits) == 1
            assert audits[0].get("payload", {}).get("out_of_service") == "Yes"

            record_created = _wait_for_trust_spine(
                db,
                workflow="dvir",
                record_ids=[inspection_id],
                stage="record_created",
            )
            queued = _wait_for_trust_spine(
                db,
                workflow="dvir",
                record_ids=[inspection_id],
                stage="notification_queued",
            )
            assert record_created.get("status") == "ok"
            assert queued.get("status") == "skipped"
            assert queued.get("failure_reason") == "email_safety_mode:strict"
        finally:
            cli.close()
    finally:
        _remove_dvir_artifacts(truck, inspection_id, defect_ids)


def test_rel01_daily_report_governed_delivery_proof(admin_token: str, field_token: str) -> None:
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not configured")
    run_id = uuid.uuid4().hex[:8]
    project_name = f"Runtime Certification — REL01 {run_id}"
    payload = {
        "project_name": project_name,
        "project_number": CERT_PROJECT_NUMBER,
        "location": "REL-01 governed lane",
        "report_date": "2026-07-17",
        "prepared_by": "Certification Foreman",
        "weather_summary": "Clear, 78°F",
        "gps_lat": 29.4241,
        "gps_lng": -98.4936,
        "gps_accuracy": 5,
        "location_source": "device_gps",
        "location_captured_at": "2026-07-17T13:45:00Z",
        "weather_snapshot_meta": {
            "provider": "open-meteo",
            "source": "open-meteo",
            "gps_lat": 29.4241,
            "gps_lng": -98.4936,
            "observation_timestamp": "2026-07-17T08:00:00-05:00",
            "timezone": "America/Chicago",
        },
        "photos": [ONE_PX] * 6,
        "prepared_by_signature": ONE_PX,
        "ai_accepted_summary": (
            "Approved summary: governed REL-01 proof passed the summary gate, "
            "captured field evidence, and queued delivery safely in preview."
        ),
        "ai_accepted_summary_meta": {
            "source": "manual",
            "approved_by": "Certification Foreman",
            "accepted_at": "2026-07-17T14:00:00Z",
        },
        "production": [{
            "description": "Curb prep",
            "quantity": 120,
            "unit": "LF",
            "unit_snapshot": "Linear Feet",
        }],
        "materials": [{
            "description": "Base rock",
            "quantity": 8,
            "unit": "TON",
            "unit_snapshot": "Tons",
        }],
        "equipment": [{
            "description": "Skid Steer",
            "run_time": 3.5,
            "idle_time": 0.5,
        }],
    }

    report_id: Optional[str] = None
    doc_id: Optional[str] = None
    try:
        submit_headers = {
            "Content-Type": "application/json",
            "X-FL-Token": field_token,
            "X-Test-Rate-Limit-Bypass": "1",
        }
        resp = requests.post(f"{BASE_URL}/api/daily-reports", json=payload, headers=submit_headers, timeout=45)
        assert resp.status_code in (200, 201), resp.text[:500]
        body = resp.json()
        report_id = body.get("id")
        doc_id = body.get("doc_id") or body.get("report_number")
        assert report_id, body
        assert body.get("certification_record") is True
        assert body.get("synthetic_record") is True
        assert body.get("hidden_from_operations") is True
        assert body.get("email_dispatch_suppressed") is False
        routing_override = body.get("routing_override") or {}
        assert routing_override.get("enabled") is True
        assert routing_override.get("to") == ["cert.pm@example.com"]
        assert routing_override.get("cc") == ["cert.copm@example.com"]

        # Fresh governed proof must also transition into PENDING_REVIEW to
        # exercise the existing bell parity path.
        transition = requests.post(
            f"{BASE_URL}/api/daily-reports/{report_id}/transition",
            json={
                "to_state": "PENDING_REVIEW",
                "reason": "REL-01 governed proof",
                "evidence": {
                    "office_review_complete": True,
                    "payroll_inputs_verified": True,
                },
            },
            headers={"Content-Type": "application/json", "X-Admin-Token": admin_token},
            timeout=30,
        )
        assert transition.status_code == 200, transition.text[:300]
        assert transition.json().get("to_state") == "PENDING_REVIEW"

        # PDF proof (focused, real endpoint).
        pdf_job = requests.get(
            f"{BASE_URL}/api/daily-reports/{report_id}/pdf",
            headers={"X-Admin-Token": admin_token},
            timeout=30,
        )
        assert pdf_job.status_code == 202, pdf_job.text[:200]
        pdf_job_body = pdf_job.json()
        status_url = pdf_job_body.get("status_url")
        assert status_url, pdf_job_body
        job_status = _poll_json(f"{BASE_URL}{status_url}", {"X-Admin-Token": admin_token})
        download_url = ((job_status.get("result") or {}).get("download_url") or "")
        assert download_url, job_status
        pdf_resp = requests.get(f"{BASE_URL}{download_url}", headers={"X-Admin-Token": admin_token}, timeout=30)
        assert pdf_resp.status_code == 200, pdf_resp.text[:200]
        assert pdf_resp.content[:4] == b"%PDF"
        assert "pdf" in (pdf_resp.headers.get("Content-Type") or "").lower()

        # Audit footer truth.
        footer = requests.get(
            f"{BASE_URL}/api/daily-reports/{report_id}/audit-footer",
            headers={"X-Admin-Token": admin_token},
            timeout=30,
        )
        assert footer.status_code == 200, footer.text[:200]
        footer_body = footer.json()
        assert footer_body.get("sha256")
        assert footer_body.get("footer_text")

        # Preview suppression + routing truth come from the existing forensic endpoint.
        forensic = requests.get(
            f"{BASE_URL}/api/admin/daily-report-delivery/forensics",
            params={"project_number": CERT_PROJECT_NUMBER, "since_hours": 48, "limit": 50},
            headers={"X-Admin-Token": admin_token},
            timeout=45,
        )
        assert forensic.status_code == 200, forensic.text[:300]
        rows = (forensic.json().get("reports") or [])
        row = next((r for r in rows if r.get("report_id") == report_id), None)
        assert row, rows[:3]
        assert row.get("resolver_result", {}).get("to") == ["cert.pm@example.com"]
        assert row.get("resolver_result", {}).get("cc") == ["cert.copm@example.com"]
        assert row.get("root_cause_code") == "delivery_suppressed_by_environment"
        stages = row.get("trust_spine_stages") or []
        queued = next((s for s in reversed(stages) if s.get("stage") == "notification_queued"), None)
        assert queued and queued.get("status") == "skipped"
        assert queued.get("failure_reason") == "email_safety_mode:strict"

        # Bell parity and audit trail.
        cli, db = _db()
        try:
            notifications = list(
                db.notifications.find(
                    {"linked_source_record_id": report_id, "type": "daily_report.pending_review"},
                    {"_id": 0, "recipient_role": 1, "type": 1},
                )
            )
            events = list(
                db.workflow_state_events.find(
                    {"workflow": "daily_report", "record_id": report_id},
                    {"_id": 0, "to_state": 1, "actor_role": 1, "reason": 1},
                )
            )
            assert {n.get("recipient_role") for n in notifications} >= {"admin", "pm", "safety"}
            assert any(ev.get("to_state") == "PENDING_REVIEW" for ev in events)
            assert any(ev.get("reason") == "REL-01 governed proof" for ev in events)
        finally:
            cli.close()
    finally:
        _remove_daily_report_artifacts([report_id] if report_id else [], [doc_id] if doc_id else [])
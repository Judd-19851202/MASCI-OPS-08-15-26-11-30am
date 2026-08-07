"""
WP-18DB reopened regression suite.

Focus:
1. Public Incident Report submit path (no login required from field/safety tiles)
2. Protected incident workspace path still denies unauthenticated writes
3. Backup alert buffer (warn at 60m, red-alert after 75m)
4. Daily Report midnight continuity contract (active draft session anchor)
"""

from __future__ import annotations

import os
import re
import time
import uuid
from pathlib import Path

import pytest
import requests

import checklists_fleet as _ck
from lib.archive_lineage import consumer_freshness_status


TEST_CREDENTIALS_PATH = Path("/app/memory/test_credentials.md")
FRONTEND_ENV_PATH = Path("/app/frontend/.env")
LOCAL_API_ROOT = "http://127.0.0.1:8001"


def _base_url() -> str:
    env_url = (os.environ.get("REACT_APP_BACKEND_URL") or "").rstrip("/")
    if env_url:
        return env_url
    if FRONTEND_ENV_PATH.exists():
        for line in FRONTEND_ENV_PATH.read_text(encoding="utf-8").splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL is not configured for WP18DB tests")


BASE_URL = _base_url()


def _request(method: str, path: str, **kwargs):
    timeout = kwargs.pop("timeout", 30)
    try:
        primary = requests.request(method, f"{BASE_URL}{path}", timeout=timeout, **kwargs)
        if primary.status_code not in {502, 503, 504}:
            return primary
    except requests.RequestException:
        pass
    return requests.request(method, f"{LOCAL_API_ROOT}{path}", timeout=timeout, **kwargs)


def _password_for(email: str) -> str:
    text = TEST_CREDENTIALS_PATH.read_text(encoding="utf-8")
    inline = re.search(rf"`{re.escape(email)}\s*/\s*([^`]+)`", text)
    if inline:
        return inline.group(1)
    block = re.search(rf"Email:\s*`{re.escape(email)}`\s*\n\s*-\s*Password:\s*`([^`]+)`", text)
    if block:
        return block.group(1)
    raise RuntimeError(f"Password not found in {TEST_CREDENTIALS_PATH} for {email}")


ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = _password_for(ADMIN_EMAIL)


def _public_incident_body(idempotency_key: str) -> dict:
    return {
        "field_block": {
            "incident_type": "near_miss",
            "occurred_at": "2026-08-06T12:00:00Z",
            "reported_at": "2026-08-06T12:05:00Z",
            "location_label": "Public Incident Proof",
            "job_number": "PUBLIC-WP18DB-001",
            "reporter_name": "Preview Public User",
            "reporter_role": "Foreman",
            "weather": "Clear",
            "immediate_actions": "Area secured",
            "observed_conditions": "Anonymous public proof",
            "witnesses": [
                {
                    "name": "Witness One",
                    "statement": "Saw the event",
                    "contact": "555-0100",
                }
            ],
            "submitter_language": "en",
        },
        "evidence_items": [
            {
                "evidence_type": "photo",
                "label": "proof photo",
                "data_url": "data:image/png;base64,ZmFrZQ==",
                "metadata": {"mime": "image/png", "captured_at": "2026-08-06T12:05:00Z"},
            },
            {
                "evidence_type": "witness_statement",
                "label": "Witness One",
                "description": "Saw the event",
                "metadata": {"contact": "555-0100"},
            },
        ],
        "idempotency_key": idempotency_key,
    }


def _daily_report_body() -> dict:
    unique = uuid.uuid4().hex[:8]
    return {
        "project_name": f"WP18DB Public Daily {unique}",
        "project_number": f"WP18DB-DR-{unique}",
        "location": "Public runtime certification",
        "report_date": "2026-08-07",
        "prepared_by": "WP18DB Runtime Cert",
        "weather_summary": "Clear",
        "general_notes": "Public no-login daily runtime certification",
        "ai_accepted_summary": "Manual approved summary for public runtime certification.",
        "ai_accepted_summary_meta": {
            "source": "manual",
            "approved_by": "WP18DB Runtime Cert",
            "accepted_at": "2026-08-07T07:00:00Z",
        },
        "photos": [],
        "prepared_by_signature": "",
        "certification_record": True,
        "synthetic_record": True,
        "hidden_from_operations": True,
        "email_dispatch_suppressed": True,
        "certification_track_id": "WP18DB_PUBLIC_RUNTIME",
        "certification_run_id": f"wp18db-dr-{unique}",
    }


def _meeting_body() -> dict:
    unique = uuid.uuid4().hex[:8]
    return {
        "project_name": f"WP18DB Public Meeting {unique}",
        "project_number": f"WP18DB-MTG-{unique}",
        "location": "Public runtime certification",
        "meeting_date": "2026-08-07",
        "meeting_time": "07:00",
        "conducted_by": "WP18DB Runtime Cert",
        "topic": "Public no-login safety meeting runtime certification",
        "discussion_notes": "WP18DB public meeting submit proof.",
        "attendees": [
            {
                "name": "Runtime Cert Foreman",
                "employee_id": "",
                "non_masci": False,
                "company": "MASCI",
                "trade": "Foreman",
                "signature": "data:image/png;base64,iVBORw0KGgo=",
                "acknowledged": True,
                "acknowledged_at": "2026-08-07T07:05:00Z",
            }
        ],
        "photos": [],
        "conductor_signature": "data:image/png;base64,iVBORw0KGgo=",
    }


def _equipment_body() -> dict:
    unique = uuid.uuid4().hex[:6]
    return {
        "project_name": "WP18DB Public Equipment Pre-Op",
        "project_number": "WP18DB-EQ-001",
        "location": "Public runtime certification",
        "inspection_date": "2026-08-07",
        "inspection_time": "06:45",
        "operator_name": "Runtime Cert Operator",
        "equipment_type": "Excavator",
        "equipment_unit": f"WP18DB-EQ-{unique}",
        "equipment_make": "CAT",
        "equipment_model": "320",
        "equipment_serial": "WP18DB-SN",
        "hour_meter": "1234.5",
        "odometer": "",
        "checklist": {"Fluids & Leaks": {"Engine oil level": {"status": "pass", "note": ""}}},
        "fail_count": 0,
        "pass_count": 1,
        "na_count": 0,
        "deficiency_notes": "",
        "corrective_actions": "",
        "out_of_service": "No",
        "photos": [],
        "operator_signature": "",
    }


def _dvir_body() -> dict:
    unique = uuid.uuid4().hex[:6]
    return {
        "kind": "dvir",
        "driver_name": "Runtime Cert Driver",
        "inspection_date": "2026-08-07",
        "inspection_time": "06:30",
        "truck_unit_number": f"WP18DB-TRUCK-{unique}",
        "odometer_miles": "234567",
        "truck_checklist": {item: "pass" for item in _ck.dvir_truck_items()},
        "trailers": [],
        "defect_details": {},
        "driver_signature": "data:image/png;base64,iVBORw0KGgo=",
        "submitted_via": "public_tile",
    }


class TestPublicIncidentContract:
    def test_public_incident_submit_requires_no_login(self):
        unique_key = f"wp18db-public-proof-{int(time.time())}"
        resp = _request("POST", "/api/public/incident-cases", json=_public_incident_body(unique_key))
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:300]}"
        body = resp.json()
        assert body.get("case_id"), body
        assert body.get("case_number"), body
        assert body.get("duplicate") is False, body
        assert body.get("case", {}).get("state") == "FIELD_SUBMITTED", body

    def test_public_incident_submit_is_idempotent(self):
        key = "wp18db-public-proof-202"
        first = _request("POST", "/api/public/incident-cases", json=_public_incident_body(key))
        second = _request("POST", "/api/public/incident-cases", json=_public_incident_body(key))
        assert first.status_code == 200, first.text[:300]
        assert second.status_code == 200, second.text[:300]
        first_body = first.json()
        second_body = second.json()
        assert second_body.get("duplicate") is True, second_body
        assert second_body.get("case_id") == first_body.get("case_id"), (first_body, second_body)
        assert second_body.get("case_number") == first_body.get("case_number"), (first_body, second_body)

    def test_internal_incident_workspace_write_stays_protected(self):
        resp = _request("POST", "/api/incident-cases", json={"field_block": {"incident_type": "near_miss"}})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text[:200]}"

    def test_public_weather_helper_is_not_auth_gated(self):
        resp = _request("GET", "/api/incident-intelligence/weather?lat=36.1&lng=-115.1")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:240]}"
        body = resp.json()
        assert body.get("summary") or body.get("description"), body

    def test_public_project_context_helper_is_not_auth_gated(self):
        resp = _request("GET", "/api/incident-intelligence/project-context/2742")
        assert resp.status_code not in {401, 403}, f"Expected non-auth response, got {resp.status_code}: {resp.text[:240]}"


class TestOtherPublicFieldForms:
    def test_public_daily_report_submit_requires_no_login(self):
        resp = _request("POST", "/api/daily-reports", json=_daily_report_body())
        assert resp.status_code in {200, 201}, f"Expected 200/201, got {resp.status_code}: {resp.text[:300]}"
        body = resp.json()
        assert body.get("id"), body
        assert str(body.get("doc_id") or "").startswith("DR-"), body

    def test_public_safety_meeting_submit_requires_no_login(self):
        resp = _request("POST", "/api/meetings", json=_meeting_body())
        assert resp.status_code in {200, 201}, f"Expected 200/201, got {resp.status_code}: {resp.text[:300]}"
        body = resp.json()
        assert body.get("id"), body
        assert str(body.get("doc_id") or "").startswith("MTG-"), body

    def test_public_equipment_preop_submit_requires_no_login(self):
        resp = _request("POST", "/api/equipment-inspections", json=_equipment_body())
        assert resp.status_code in {200, 201}, f"Expected 200/201, got {resp.status_code}: {resp.text[:300]}"
        body = resp.json()
        assert body.get("id"), body
        assert str(body.get("doc_id") or "").startswith("PRE-"), body

    def test_public_dvir_submit_requires_no_login(self):
        resp = _request("POST", "/api/fleet/inspections", json=_dvir_body())
        assert resp.status_code in {200, 201}, f"Expected 200/201, got {resp.status_code}: {resp.text[:300]}"
        body = resp.json()
        assert body.get("ok") is True, body
        assert body.get("kind") == "dvir", body
        assert body.get("inspection_id"), body


class TestBackupHealthAlertThreshold:
    @pytest.fixture(scope="class")
    def admin_headers(self):
        login_resp = _request(
            "POST",
            "/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        if login_resp.status_code != 200:
            pytest.skip(f"Admin login failed: {login_resp.status_code}")
        data = login_resp.json()
        return {
            "X-Admin-Token": data.get("portal_tokens", {}).get("admin"),
            "X-Directory-Token": data.get("session_token"),
        }

    def test_system_health_backup_card_mentions_60_and_75_thresholds(self, admin_headers):
        resp = _request("GET", "/api/admin/system-health", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        cards = resp.json().get("cards", [])
        backup_card = next((card for card in cards if card.get("key") == "backup"), None)
        assert backup_card is not None, "Backup card not found"
        detail = str(backup_card.get("detail") or "")
        assert "60" in detail and "75" in detail, detail

    def test_backup_threshold_source_contract(self):
        admin_ops = Path("/app/backend/routes/admin_ops.py").read_text(encoding="utf-8")
        assert "BACKUP_RPO_TARGET_MINUTES" in admin_ops
        assert "BACKUP_HEALTH_ALERT_THRESHOLD_MINUTES" in admin_ops

    def test_backup_threshold_behavior_current_to_75_to_red_after(self):
        assert consumer_freshness_status({"freshness_age_minutes": 60}, threshold_minutes=75, warning_minutes=60)["status"] == "CURRENT"
        assert consumer_freshness_status({"freshness_age_minutes": 61}, threshold_minutes=75, warning_minutes=60)["status"] == "AGING"
        assert consumer_freshness_status({"freshness_age_minutes": 75}, threshold_minutes=75, warning_minutes=60)["status"] == "AGING"
        assert consumer_freshness_status({"freshness_age_minutes": 76}, threshold_minutes=75, warning_minutes=60)["status"] == "STALE"

    def test_health_monitor_only_alerts_red_cards_source_contract(self):
        monitor_src = Path("/app/backend/health_monitor.py").read_text(encoding="utf-8")
        assert 'red_cards = [c for c in cards if c.get("status") == "red"]' in monitor_src


class TestDailyMidnightContinuityContract:
    def test_daily_report_session_anchor_source_present(self):
        source = Path("/app/frontend/src/lib/resiliency/dailyReportScope.js").read_text(encoding="utf-8")
        assert "masci.daily-report.active-session.v1" in source
        assert "buildDailyReportSessionScope" in source
        assert "draft_session_id" in source

    def test_daily_report_page_auto_restores_same_session(self):
        source = Path("/app/frontend/src/pages/NewDailyReportV3.jsx").read_text(encoding="utf-8")
        assert "activeSession !== pendingSession" in source
        assert "restoreDraft()" in source
        assert "clearActiveDailyReportDraftSession" in source

    def test_site_audit_route_remains_authenticated_by_design_source(self):
        app_routes = Path("/app/frontend/src/app/routing/AppRoutes.jsx").read_text(encoding="utf-8")
        assert 'path="/safety/inspections/new" element={SF(<NewInspection />)}' in app_routes
        assert 'to="/safety-portal/login?returnTo=/safety/inspections/new"' in app_routes


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
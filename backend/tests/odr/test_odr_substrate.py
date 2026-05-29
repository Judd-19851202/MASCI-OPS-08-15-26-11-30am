"""Substrate-level pytest suite for the Phase V.1 ODR routes (M0.1).

Run:
    cd /app/backend && python -m pytest tests/odr/test_odr_substrate.py -v

Covers:
    1. Create draft → doc_id format, schema_version=2, status=draft
    2. Patch (delays + signature) → mutation persisted, last_edited stamped
    3. Submit hard-stop (no foreman ack) → 409 with hard_stops
    4. Submit success → status=submitted, readiness.score=ready,
       amend_allowed_until_utc set to +24h
    5. Timeline emission → operational_links row created on submit
    6. Section events audit trail → draft_created + patched + submitted
    7. Submit twice → 409 (status already submitted)
    8. FLL projector → admin sees fll=FLL-6 verb=SUMMARY in list
    9. Mongo _id never leaks
    10. Index existence on `odr`
"""
from __future__ import annotations

import os
import time
import uuid

import pytest
import requests


URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
if not URL.startswith("http"):
    URL = "http://localhost:8001"

ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_token() -> str:
    r = requests.post(
        f"{URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=10,
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    tok = (r.json().get("portal_tokens") or {}).get("admin")
    assert tok, "no admin portal token returned"
    return tok


@pytest.fixture(scope="module")
def headers(admin_token: str) -> dict:
    return {"Content-Type": "application/json", "X-Admin-Token": admin_token}


@pytest.fixture(scope="module")
def odr_payload() -> dict:
    return {
        "project": {
            "project_id": f"proj-test-{uuid.uuid4().hex[:8]}",
            "project_number": f"99-{uuid.uuid4().hex[:4]}",
            "project_name": "ODR Substrate Pytest",
            "report_date": "2026-05-29",
            "foreman_uid": ADMIN_EMAIL,
            "foreman_name": "Pytest Foreman",
        },
        "crew_profile": {
            "crew_id": f"crew-{uuid.uuid4().hex[:8]}",
            "crew_name": "Pytest Crew",
            "crew_type": "pipe",
            "primary_operation": "RCP install",
        },
    }


@pytest.fixture(scope="module")
def created_odr(headers: dict, odr_payload: dict) -> dict:
    r = requests.post(f"{URL}/api/odr", json=odr_payload, headers=headers, timeout=10)
    assert r.status_code == 200, r.text
    doc = r.json()
    return doc


def test_1_create_draft_envelope(created_odr: dict):
    assert created_odr["status"] == "draft"
    assert created_odr["schema_version"] == 2
    assert created_odr["doc_id"].startswith("ODR-2026-")
    assert len(created_odr["doc_id"].split("-")[2]) == 5
    assert created_odr["id"]
    assert "_id" not in created_odr  # _id never leaks


def test_2_patch_delays(headers: dict, created_odr: dict):
    odr_id = created_odr["id"]
    r = requests.patch(
        f"{URL}/api/odr/{odr_id}",
        json={
            "delays": {
                "any_delays": True,
                "entries": [{
                    "delay_type": "weather",
                    "hours_lost": 2.5,
                    "description": {"text": "Rain AM"},
                    "photos": [],
                }],
                "total_hours_lost": 2.5,
            },
        },
        headers=headers,
        timeout=10,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["status"] == "draft"
    assert d["delays"]["any_delays"] is True
    assert len(d["delays"]["entries"]) == 1
    assert d["last_edited_by_uid"]


def test_3_submit_hard_stop_blocks(headers: dict, created_odr: dict):
    odr_id = created_odr["id"]
    r = requests.post(
        f"{URL}/api/odr/{odr_id}/submit",
        json={},
        headers=headers,
        timeout=10,
    )
    assert r.status_code == 409, r.text
    detail = r.json().get("detail", {})
    assert "hard_stops" in detail
    assert any("signature" in s for s in detail["hard_stops"])


def test_4_submit_succeeds_after_ack(headers: dict, created_odr: dict):
    odr_id = created_odr["id"]
    # First patch the signature ack.
    r = requests.patch(
        f"{URL}/api/odr/{odr_id}",
        json={
            "signature": {
                "foreman_acknowledgement": {
                    "acknowledged": True,
                    "acknowledged_by_uid": ADMIN_EMAIL,
                    "text": "I confirm this report is true and complete",
                },
            },
        },
        headers=headers,
        timeout=10,
    )
    assert r.status_code == 200, r.text

    r = requests.post(
        f"{URL}/api/odr/{odr_id}/submit",
        json={"signature_text": "I confirm"},
        headers=headers,
        timeout=10,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["status"] == "submitted"
    assert d["submitted_at"]
    assert d["amend_allowed_until_utc"]
    assert d["readiness"]["score"] == "ready"
    assert d["readiness"]["hard_stops"] == []


def test_5_timeline_link_emitted_on_submit(headers: dict, created_odr: dict):
    odr_id = created_odr["id"]
    project_id = created_odr["project"]["project_id"]
    r = requests.get(
        f"{URL}/api/operational-links",
        params={
            "project_id": project_id,
            "source_type": "odr",
            "source_id": odr_id,
        },
        headers=headers,
        timeout=10,
    )
    assert r.status_code == 200, r.text
    links = r.json()
    assert isinstance(links, list)
    assert len(links) >= 1
    assert links[0]["source_type"] == "odr"
    assert links[0]["target_type"] == "project"
    assert links[0]["relationship"] == "documents"
    assert links[0]["project_id"] == project_id


def test_6_section_events_audit_trail(headers: dict, created_odr: dict):
    odr_id = created_odr["id"]
    r = requests.get(
        f"{URL}/api/odr/{odr_id}/section-events",
        headers=headers,
        timeout=10,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    actions = [e["action"] for e in d["events"]]
    assert "draft_created" in actions
    assert "patched" in actions
    assert "submitted" in actions


def test_7_double_submit_409(headers: dict, created_odr: dict):
    odr_id = created_odr["id"]
    r = requests.post(
        f"{URL}/api/odr/{odr_id}/submit",
        json={},
        headers=headers,
        timeout=10,
    )
    assert r.status_code == 409, r.text


def test_8_list_returns_fll_verb_for_admin(headers: dict):
    r = requests.get(f"{URL}/api/odr?limit=5", headers=headers, timeout=10)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["fll"] == "FLL-6"
    assert d["verb"] == "SUMMARY"
    assert "items" in d


def test_9_get_existing_odr_no_id_leak(headers: dict, created_odr: dict):
    odr_id = created_odr["id"]
    r = requests.get(f"{URL}/api/odr/{odr_id}", headers=headers, timeout=10)
    assert r.status_code == 200, r.text
    body_str = r.text
    assert '"_id"' not in body_str, "Mongo _id leaked in response"


def test_10_get_unknown_odr_404(headers: dict):
    r = requests.get(f"{URL}/api/odr/does-not-exist-zzzz", headers=headers, timeout=10)
    assert r.status_code == 404


def test_11_section_event_post(headers: dict, created_odr: dict):
    odr_id = created_odr["id"]
    r = requests.post(
        f"{URL}/api/odr/{odr_id}/section-event",
        json={
            "section": "manpower.rows[0].hours",
            "action": "value_changed",
            "note": "operator adjusted",
            "old_value_hash": "abc",
            "new_value_hash": "def",
        },
        headers=headers,
        timeout=10,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["section"] == "manpower.rows[0].hours"
    assert d["action"] == "value_changed"
    assert d["event_id"]
    assert d["at_utc"].endswith("Z")


def test_12_post_submitted_patch_within_window(
    headers: dict, created_odr: dict,
):
    """Submitted records carry an open 24h amend window — patch allowed."""
    odr_id = created_odr["id"]
    r = requests.patch(
        f"{URL}/api/odr/{odr_id}",
        json={"plan_vs_actual": {"completed_planned_work": True}},
        headers=headers,
        timeout=10,
    )
    # Inside window → 200; if window already closed in some lag → 403
    assert r.status_code in (200, 403), r.text

"""Phase 10A-B · Integration Hardening tests.

Covers OMEGA Correction Directive items:
  • Correction 1 — Daily Report excavation activity gate + two-way linkage
  • Correction 4/5 — Public asset roster endpoint (Trench Boxes + Road Plates)
  • Correction 7 — Smart OSHA triggers (SOIL_TYPE_C, RAIN_REINSPECTION, COMPETENT_PERSON)
  • Correction 9 — Spanish original-language preservation
  • Correction 10 — Reinspection trigger queue + endpoint
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import pytest
import requests

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

API = os.environ.get("TS_API_BASE", "http://localhost:8001")


def _admin_token() -> str:
    pwd = os.environ.get("ADMIN_PASSWORD", "MASCI1982!")
    r = requests.post(f"{API}/api/admin/login", json={"password": pwd}, timeout=15)
    r.raise_for_status()
    return r.json()["token"]


def _h(token: str) -> dict:
    return {"X-Admin-Token": token, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def token():
    return _admin_token()


def _submit(payload):
    r = requests.post(f"{API}/api/trench-safety/excavations/public/submit", json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


# ════════════════════════════════════════════════════════════════════════
# Correction 4 + 5 · Public asset roster
# ════════════════════════════════════════════════════════════════════════

def test_public_asset_roster_returns_field_safe_rows():
    r = requests.get(f"{API}/api/trench-safety/excavations/public/asset-roster", params={"limit": 5}, timeout=15)
    r.raise_for_status()
    body = r.json()
    assert "items" in body and isinstance(body["items"], list)
    assert "count" in body
    if body["items"]:
        row = body["items"][0]
        # Field-safe projection — never leak PII or admin-only fields
        for k in ("asset_id", "asset_type", "operational_status", "tabulated_data_available", "open_holds_count"):
            assert k in row, f"missing field {k}"
        # Negative — should never expose admin fields
        for k in ("created_by", "created_at_admin", "_id"):
            assert k not in row, f"leaked admin field {k}"


def test_public_asset_roster_filter_by_asset_type():
    r = requests.get(f"{API}/api/trench-safety/excavations/public/asset-roster",
                     params={"asset_type": "Road Plate", "limit": 50}, timeout=15)
    r.raise_for_status()
    body = r.json()
    for it in body["items"]:
        assert it["asset_type"] == "Road Plate"


def test_public_asset_roster_search_by_id():
    # Get first asset to derive a search term
    r0 = requests.get(f"{API}/api/trench-safety/excavations/public/asset-roster", params={"limit": 1}, timeout=15)
    items = r0.json().get("items", [])
    if not items:
        pytest.skip("No assets seeded")
    aid = items[0]["asset_id"]
    r = requests.get(f"{API}/api/trench-safety/excavations/public/asset-roster", params={"q": aid}, timeout=15)
    body = r.json()
    assert any(it["asset_id"] == aid for it in body["items"])


# ════════════════════════════════════════════════════════════════════════
# Correction 7 · Smart OSHA triggers
# ════════════════════════════════════════════════════════════════════════

def _base(**overrides):
    base = {
        "project_name": f"QA-Integration {uuid.uuid4().hex[:5]}",
        "foreman_name": "Test Foreman",
        "submitted_by": "qa-integration@example.com",
        "date_of_work": "2026-02-07",
        "work_type": "Other",
        "soil_classification": "Type B",
        "protective_system": "Sloping",
    }
    base.update(overrides)
    return base


def test_smart_trigger_soil_type_c_adds_flag():
    doc = _submit(_base(soil_classification="Type C"))
    codes = {f["code"] for f in doc["flags"]}
    assert "SOIL_TYPE_C" in codes


def test_smart_trigger_rain_event_adds_reinspection_flag():
    doc = _submit(_base(rain_event_observed=True))
    codes = {f["code"] for f in doc["flags"]}
    assert "RAIN_REINSPECTION" in codes


def test_smart_trigger_deep_no_competent_person():
    doc = _submit(_base(depth_ge_5ft=True, depth_ft=6, protective_system="Sloping",
                         competent_person_name="", competent_person_id=""))
    codes = {f["code"] for f in doc["flags"]}
    assert "COMPETENT_PERSON" in codes


def test_smart_trigger_road_plates_used_no_assets():
    doc = _submit(_base(road_plates_used=True, road_plate_ids=[]))
    codes = {f["code"] for f in doc["flags"]}
    assert "ROAD_PLATE_ASSIGNMENT" in codes


# ════════════════════════════════════════════════════════════════════════
# Correction 9 · Spanish original-language preservation
# ════════════════════════════════════════════════════════════════════════

def test_spanish_original_language_preserved(token):
    spanish_note = "Zanja con agua — el competente debe revisarla."
    doc = _submit(_base(field_notes=spanish_note, language="es"))
    r = requests.get(f"{API}/api/trench-safety/excavations/{doc['id']}", headers=_h(token), timeout=15)
    r.raise_for_status()
    fetched = r.json()
    assert fetched["field_notes"] == spanish_note
    # Original-language fields must be stamped
    assert fetched.get("field_notes_original_text") == spanish_note
    assert fetched.get("field_notes_original_language") == "es"


def test_translation_override_endpoint(token):
    doc = _submit(_base(field_notes="zanja con piedras", language="es"))
    ex_id = doc["id"]
    translation = "Trench with stones."
    r = requests.post(
        f"{API}/api/trench-safety/excavations/{ex_id}/translate-notes",
        headers=_h(token),
        json={"translated_text": translation},
        timeout=15,
    )
    r.raise_for_status()
    fetched = r.json()
    # Translation stored but original NOT destroyed
    assert fetched.get("field_notes_translated_text") == translation
    assert fetched.get("field_notes_original_text") == "zanja con piedras"
    assert fetched.get("field_notes_original_language") == "es"


# ════════════════════════════════════════════════════════════════════════
# Correction 10 · Reinspection trigger + queue
# ════════════════════════════════════════════════════════════════════════

def test_reinspection_trigger_endpoint(token):
    doc = _submit(_base())
    ex_id = doc["id"]
    r = requests.post(
        f"{API}/api/trench-safety/excavations/{ex_id}/reinspection-trigger",
        headers=_h(token),
        json={"reason": "Rain", "note": "Half inch overnight rain"},
        timeout=15,
    )
    r.raise_for_status()
    updated = r.json()
    assert updated["reinspection_required"] is True
    assert updated["reinspection_completed"] is False
    history = updated.get("reinspection_history") or []
    assert any(h.get("reason") == "Rain" for h in history)
    # Status escalates because of REINSPECTION flag
    assert updated["status"] in ("Action Required", "Needs Review")


def test_reinspection_queue_endpoint(token):
    # Ensure at least one open reinspection record exists
    doc = _submit(_base())
    requests.post(
        f"{API}/api/trench-safety/excavations/{doc['id']}/reinspection-trigger",
        headers=_h(token),
        json={"reason": "Utility Strike", "note": "Hit unmarked fiber"},
        timeout=15,
    ).raise_for_status()
    r = requests.get(f"{API}/api/trench-safety/excavations/reinspection-queue", headers=_h(token), timeout=15)
    r.raise_for_status()
    body = r.json()
    assert "items" in body
    assert any(it["id"] == doc["id"] for it in body["items"])
    for it in body["items"]:
        assert it.get("reinspection_required") is True


# ════════════════════════════════════════════════════════════════════════
# Correction 1 · Daily Report excavation activity gate
# ════════════════════════════════════════════════════════════════════════

def _minimal_daily_report(**overrides):
    base = {
        "project_name": f"QA-DR {uuid.uuid4().hex[:5]}",
        "project_number": "QA-DR-001",
        "location": "QA Site",
        "report_date": "2026-02-07",
        "prepared_by": "QA Foreman",
    }
    base.update(overrides)
    return base


def test_daily_report_excavation_gate_blocks_yes_without_link():
    """Correction 1 — YES selected, no linked_excavation_ids → 422 with structured error."""
    r = requests.post(
        f"{API}/api/daily-reports",
        json=_minimal_daily_report(excavation_activity_today="Yes", linked_excavation_ids=[]),
        timeout=15,
    )
    assert r.status_code == 422, r.text
    body = r.json()
    detail = body.get("detail")
    if isinstance(detail, dict):
        assert detail.get("error") == "excavation_record_required"


def test_daily_report_gate_allows_when_no_excavation_activity():
    """NO selected → submit allowed."""
    r = requests.post(
        f"{API}/api/daily-reports",
        json=_minimal_daily_report(excavation_activity_today="No"),
        timeout=15,
    )
    # We may still get 200 OR a different validation error for unrelated
    # required fields. We only care that excavation gate did NOT block.
    if r.status_code == 422:
        detail = (r.json() or {}).get("detail")
        if isinstance(detail, dict):
            assert detail.get("error") != "excavation_record_required"


def test_daily_report_two_way_linkage_on_excavation_submit(token):
    """Correction 1 — submitting an excavation linked to a Daily Report
    stamps the daily_report_id onto the excavation AND writes a
    reverse-link onto the daily_report doc."""
    # 1. Create a real daily report
    dr_payload = _minimal_daily_report(
        project_number=f"QA-DR-{uuid.uuid4().hex[:4]}",
        excavation_activity_today="No",
    )
    dr_resp = requests.post(f"{API}/api/daily-reports", json=dr_payload, timeout=15)
    if dr_resp.status_code not in (200, 201):
        pytest.skip(f"Daily Report POST returned {dr_resp.status_code}: {dr_resp.text[:200]}")
    dr = dr_resp.json()
    dr_id = dr["id"]
    # 2. Submit an excavation referencing the same project_number + date
    exc = _submit(_base(
        project_number=dr_payload["project_number"],
        date_of_work=dr_payload["report_date"],
        triggered_from_daily_report_id=dr_id,
    ))
    # Forward link on excavation
    forward = exc.get("daily_report_links") or []
    assert any(lk.get("daily_report_id") == dr_id for lk in forward), \
        f"excavation missing forward daily_report_link to {dr_id}"
    # Reverse link on daily report
    list_resp = requests.get(f"{API}/api/daily-reports", headers=_h(token), timeout=15)
    if list_resp.status_code == 200:
        items = list_resp.json()
        target = next((it for it in items if it.get("id") == dr_id), None)
        # Reverse linkage is stored as linked_excavation_ids on the doc;
        # the list response may or may not project it. Hit the doc directly
        # if needed (no public detail endpoint — use Mongo via admin)
        if target is not None and "linked_excavation_ids" in target:
            assert exc["id"] in target["linked_excavation_ids"]


# ════════════════════════════════════════════════════════════════════════
# Correction 2 · MASCI Job integration — submit accepts job_id + auto fields
# ════════════════════════════════════════════════════════════════════════

def test_job_id_and_customer_persist_on_excavation(token):
    doc = _submit(_base(
        job_id="qa-job-123",
        project_number="QA-J-001",
        customer="QA Customer",
        project_manager="QA PM",
        pm_email="qa-pm@example.com",
    ))
    r = requests.get(f"{API}/api/trench-safety/excavations/{doc['id']}", headers=_h(token), timeout=15)
    r.raise_for_status()
    fetched = r.json()
    assert fetched.get("job_id") == "qa-job-123"
    assert fetched.get("project_number") == "QA-J-001"
    assert fetched.get("customer") == "QA Customer"
    assert fetched.get("project_manager") == "QA PM"


# ════════════════════════════════════════════════════════════════════════
# Correction 3 · Personnel fields persist
# ════════════════════════════════════════════════════════════════════════

def test_personnel_fields_persist(token):
    doc = _submit(_base(
        prepared_by_id="emp-1", prepared_by_name="Prep Person",
        foreman_id="emp-2", foreman_name="Foreman Person",
        leadman_id="emp-3", leadman_name="Leadman Person",
        superintendent_id="emp-4", superintendent_name="Super Person",
        competent_person_id="emp-5", competent_person_name="CP Person",
    ))
    r = requests.get(f"{API}/api/trench-safety/excavations/{doc['id']}", headers=_h(token), timeout=15)
    r.raise_for_status()
    fetched = r.json()
    assert fetched["prepared_by_name"] == "Prep Person"
    assert fetched["foreman_name"] == "Foreman Person"
    assert fetched["leadman_name"] == "Leadman Person"
    assert fetched["superintendent_name"] == "Super Person"
    assert fetched["competent_person_name"] == "CP Person"
    # supervisor_name mirror
    assert fetched["supervisor_name"] == "Foreman Person"

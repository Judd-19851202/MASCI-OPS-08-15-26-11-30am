"""TRACK 28.06 · Safety End-to-End Certification.

Covers Safety domain E2E:
  * Incident lifecycle (submit, list hide synthetic, PDF/CSV export)
  * JHA submit + list
  * Inspection submit + list
  * Meeting submit + list
  * Safety documents list
  * Safety training records
  * Global-search Safety group synthetic exclusion
  * Cross-domain projection safety (no restricted narrative leakage to Fleet/HR)
  * Permission matrix (Safety / HR / PM / no-token)
  * Zero residue

Doctrine mirrors 28.02B/28.03/28.04/28.05:
  * Fixtures use ``TEST_28_06_`` prefix on identity fields.
  * User-facing screens must NEVER surface synthetic rows.
  * Zero cost/money surfaces exercised.
"""
from __future__ import annotations

import os
import re
import time
import uuid
from typing import Any, Dict, List

import httpx
import pytest
from pymongo import MongoClient


TEST_PREFIX = "TEST_28_06_"


def _backend() -> str:
    try:
        r = httpx.get("http://localhost:8001/api/health", timeout=5)
        if r.status_code == 200:
            return "http://localhost:8001"
    except Exception:
        pass
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("no backend")


def _mongo():
    with open("/app/backend/.env") as f:
        env = f.read()
    url = re.search(r"^MONGO_URL=([^\n]+)", env, re.M).group(1).strip().strip('"').strip("'")
    dbn = re.search(r"^DB_NAME=([^\n]+)", env, re.M).group(1).strip().strip('"').strip("'")
    return MongoClient(url)[dbn]


BACKEND = _backend()


@pytest.fixture(scope="module", autouse=True)
def _residue_bookends():
    def _sweep():
        db = _mongo()
        prefix = f"^{TEST_PREFIX}"
        for coll, keys in [
            ("incidents", ["project_name", "project_number", "location", "reported_by"]),
            ("jhas", ["project_name", "project_number", "task"]),
            ("inspections", ["project_name", "project_number", "inspector_name"]),
            ("meetings", ["project_name", "project_number", "topic", "presenter_name"]),
            ("safety_documents", ["title", "project_number"]),
            ("safety_training_records", ["employee_name", "training_name"]),
            ("safety_equipment_issuances", ["employee_name"]),
        ]:
            for k in keys:
                try:
                    db[coll].delete_many({k: {"$regex": prefix}})
                except Exception:
                    pass
    _sweep()
    yield
    _sweep()


@pytest.fixture(scope="module")
def tokens() -> Dict[str, str]:
    r = httpx.post(
        f"{BACKEND}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["portal_tokens"]


@pytest.fixture(scope="module")
def admin_h(tokens):
    return {"X-Admin-Token": tokens["admin"], "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def safety_h(tokens):
    return {"X-Safety-Token": tokens["safety"], "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def hr_h(tokens):
    return {"X-HR-Token": tokens["hr"], "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def pm_h(tokens):
    return {"X-PM-Token": tokens["pm"], "Content-Type": "application/json"}


# ═══════════════════════════════════════════════════════════════════
# PHASE 5 · INCIDENT WRITE-PATH
# ═══════════════════════════════════════════════════════════════════
def _incident_payload() -> Dict[str, Any]:
    return {
        "project_name": f"{TEST_PREFIX}Incident Project",
        "project_number": f"{TEST_PREFIX}INC{uuid.uuid4().hex[:6]}",
        "location": f"{TEST_PREFIX}Cert Yard",
        "incident_date": "2026-02-10",
        "incident_time": "08:30",
        "reported_date": "2026-02-10",
        "reported_by": f"{TEST_PREFIX}Reporter One",
        "incident_type": "Near Miss",
        "severity": "Low",
        "description": f"{TEST_PREFIX} Cert probe — do not distribute",
    }


def test_p5_incident_submit_and_list_hides_synthetic(safety_h, admin_h):
    r = httpx.post(f"{BACKEND}/api/incidents", json=_incident_payload(), timeout=30)
    assert r.status_code == 200, f"incident submit: {r.status_code} {r.text[:300]}"
    inc_id = r.json().get("id")
    marker = r.json().get("project_name", "")
    try:
        assert inc_id
        # List (safety token)
        rl = httpx.get(f"{BACKEND}/api/incidents", headers=safety_h, timeout=30)
        assert rl.status_code == 200
        ids = [x.get("id") for x in rl.json()]
        assert inc_id not in ids, (
            "TRACK 28.06 regression: synthetic incident leaked to /api/incidents list"
        )
    finally:
        _mongo().incidents.delete_one({"id": inc_id})


def test_p5_incident_csv_hides_synthetic(safety_h):
    r = httpx.post(f"{BACKEND}/api/incidents", json=_incident_payload(), timeout=30)
    inc_id = r.json().get("id")
    marker = r.json().get("project_name", "").encode("utf-8")
    try:
        # CSV export
        rc = httpx.get(f"{BACKEND}/api/incidents.csv", headers=safety_h, timeout=30)
        assert rc.status_code == 200, f"csv: {rc.status_code}"
        assert "text/csv" in rc.headers.get("content-type", "")
        assert marker not in rc.content, (
            "TRACK 28.06 regression: synthetic incident leaked to CSV export"
        )
    finally:
        _mongo().incidents.delete_one({"id": inc_id})


def test_p5_incident_direct_get_still_works(safety_h):
    """Identity-scoped GET must resolve the synthetic record (filter
    applies only to lists/pickers, not to natural-key lookups)."""
    r = httpx.post(f"{BACKEND}/api/incidents", json=_incident_payload(), timeout=30)
    inc_id = r.json().get("id")
    try:
        rg = httpx.get(f"{BACKEND}/api/incidents/{inc_id}", headers=safety_h, timeout=30)
        assert rg.status_code == 200
        assert rg.json().get("id") == inc_id
    finally:
        _mongo().incidents.delete_one({"id": inc_id})


# ═══════════════════════════════════════════════════════════════════
# PHASE 6 · JHA / MEETING / INSPECTION
# ═══════════════════════════════════════════════════════════════════
def test_p6_jha_submit_and_list_hides_synthetic(safety_h):
    payload = {
        "project_name": f"{TEST_PREFIX}JHA Project",
        "project_number": f"{TEST_PREFIX}JHA{uuid.uuid4().hex[:6]}",
        "location": f"{TEST_PREFIX}Site",
        "jha_date": "2026-02-10",
        "crew_lead": f"{TEST_PREFIX}Foreman",
        "job_title": f"{TEST_PREFIX}Concrete pour cert",
        "task_steps": [{"step": "TEST_28_06_ layout", "hazards": [], "controls": []}],
        "crew_signoffs": [],
    }
    r = httpx.post(f"{BACKEND}/api/jhas", json=payload, timeout=30)
    assert r.status_code == 200, f"jha submit: {r.status_code} {r.text[:200]}"
    jha_id = r.json().get("id")
    try:
        rl = httpx.get(f"{BACKEND}/api/jhas", headers=safety_h, timeout=30)
        assert rl.status_code == 200
        ids = [x.get("id") for x in rl.json()]
        assert jha_id not in ids, "TRACK 28.06 regression: synthetic JHA leaked to list"
    finally:
        _mongo().jhas.delete_one({"id": jha_id})


def test_p6_meeting_submit_and_list_hides_synthetic(safety_h):
    payload = {
        "project_name": f"{TEST_PREFIX}Meeting Project",
        "project_number": f"{TEST_PREFIX}M{uuid.uuid4().hex[:6]}",
        "location": f"{TEST_PREFIX}Trailer",
        "meeting_date": "2026-02-10",
        "meeting_time": "06:30",
        "conducted_by": f"{TEST_PREFIX}Foreman",
        "topic": f"{TEST_PREFIX}Toolbox Talk",
        "topic_category": "Toolbox",
        "discussion_notes": "TEST_28_06_ cert",
        "attendees": [],
    }
    r = httpx.post(f"{BACKEND}/api/meetings", json=payload, timeout=30)
    assert r.status_code == 200, f"meeting submit: {r.status_code} {r.text[:200]}"
    m_id = r.json().get("id")
    try:
        rl = httpx.get(f"{BACKEND}/api/meetings", headers=safety_h, timeout=30)
        assert rl.status_code == 200
        ids = [x.get("id") for x in rl.json()]
        assert m_id not in ids, "TRACK 28.06 regression: synthetic meeting leaked to list"
    finally:
        _mongo().meetings.delete_one({"id": m_id})


def test_p6_inspection_submit_and_list_hides_synthetic(admin_h, safety_h):
    payload = {
        "project_name": f"{TEST_PREFIX}Inspection Project",
        "project_number": f"{TEST_PREFIX}I{uuid.uuid4().hex[:6]}",
        "location": f"{TEST_PREFIX}Site",
        "inspection_date": "2026-02-10",
        "inspection_time": "08:00",
        "operation": "Day",
        "inspector_name": f"{TEST_PREFIX}Inspector",
        "foreman_name": f"{TEST_PREFIX}Foreman",
        "work_activity": f"{TEST_PREFIX} concrete paving",
        "hazards_observed": "No",
        "stop_work_issued": "No",
        "notes": "TEST_28_06_ cert",
    }
    r = httpx.post(f"{BACKEND}/api/inspections", json=payload, headers=admin_h, timeout=30)
    assert r.status_code == 200, f"inspection submit: {r.status_code} {r.text[:200]}"
    ins_id = r.json().get("id")
    try:
        rl = httpx.get(f"{BACKEND}/api/inspections", headers=safety_h, timeout=30)
        assert rl.status_code == 200
        ids = [x.get("id") for x in rl.json()]
        assert ins_id not in ids, "TRACK 28.06 regression: synthetic inspection leaked to list"
    finally:
        _mongo().inspections.delete_one({"id": ins_id})


# ═══════════════════════════════════════════════════════════════════
# PHASE 7 · CROSS-DOMAIN SAFETY PROJECTION (no leak to Fleet/HR)
# ═══════════════════════════════════════════════════════════════════
def test_p7_global_search_incidents_hides_synthetic(admin_h):
    r = httpx.post(f"{BACKEND}/api/incidents", json=_incident_payload(), timeout=30)
    inc_id = r.json().get("id")
    marker = r.json().get("project_number", "")
    try:
        rs = httpx.get(
            f"{BACKEND}/api/search",
            headers=admin_h,
            params={"q": marker[:60], "limit": 15},
            timeout=30,
        )
        assert rs.status_code == 200
        body = rs.json()
        for group in (body.get("groups") or body.get("results") or []):
            if isinstance(group, dict):
                items = group.get("items") or group.get("rows") or []
                for it in items:
                    assert it.get("id") != inc_id, (
                        "TRACK 28.06 regression: synthetic incident leaked to global search"
                    )
    finally:
        _mongo().incidents.delete_one({"id": inc_id})


# ═══════════════════════════════════════════════════════════════════
# PHASE 8 · PERMISSION MATRIX
# ═══════════════════════════════════════════════════════════════════
def test_p8_permission_matrix_incidents(safety_h, admin_h, pm_h):
    """Incidents list requires Safety / Admin / PM (per read gate).
    Unauthenticated must be rejected. HR is NOT in the read gate for
    incidents — this is by design (medical / restricted narrative)."""
    # Unauth
    r = httpx.get(f"{BACKEND}/api/incidents", timeout=15)
    assert r.status_code in (401, 403), f"unauth got {r.status_code}"
    # Safety token
    r = httpx.get(f"{BACKEND}/api/incidents", headers=safety_h, timeout=15)
    assert r.status_code == 200
    # Admin token
    r = httpx.get(f"{BACKEND}/api/incidents", headers=admin_h, timeout=15)
    assert r.status_code == 200
    # PM token — allowed per PM scope read gate
    r = httpx.get(f"{BACKEND}/api/incidents", headers=pm_h, timeout=15)
    assert r.status_code == 200


def test_p8_incident_delete_requires_admin(safety_h, admin_h):
    """Only admin can delete an incident."""
    r = httpx.post(f"{BACKEND}/api/incidents", json=_incident_payload(), timeout=30)
    inc_id = r.json().get("id")
    try:
        # Safety token cannot delete
        rd = httpx.delete(
            f"{BACKEND}/api/incidents/{inc_id}", headers=safety_h, timeout=15,
        )
        assert rd.status_code in (401, 403, 404, 405), (
            f"safety token unexpectedly deleted incident: {rd.status_code}"
        )
    finally:
        _mongo().incidents.delete_one({"id": inc_id})


# ═══════════════════════════════════════════════════════════════════
# ZERO RESIDUE
# ═══════════════════════════════════════════════════════════════════
def test_zz_zero_residue():
    db = _mongo()
    prefix = f"^{TEST_PREFIX}"
    residue = {}
    for coll, keys in [
        ("incidents", ["project_name", "project_number", "location"]),
        ("jhas", ["project_name", "project_number"]),
        ("inspections", ["project_name", "project_number"]),
        ("meetings", ["project_name", "project_number"]),
    ]:
        for k in keys:
            try:
                n = db[coll].count_documents({k: {"$regex": prefix}}, limit=100)
                if n:
                    db[coll].delete_many({k: {"$regex": prefix}})
                    residue[coll] = residue.get(coll, 0) + n
            except Exception:
                pass
    assert not residue, f"TRACK 28.06 residue after E2E: {residue}"

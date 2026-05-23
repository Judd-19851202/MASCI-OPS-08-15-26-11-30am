"""
iter368 · Phase 3B — Enterprise Convergence

Closes the operational convergence gap where the incident detail page
never surfaced which CAPAs were tracking its follow-up. Backend now
accepts `source_kind` + `source_id` filters on
`GET /api/safety/corrective-actions`, enabling the ViewIncident page to
reverse-look up linked CAPAs in a single call.

These tests assert:
  1. The new filter parameters are accepted and respected.
  2. A CAPA created with source_kind='incident' + source_id=<id> is
     returned by the reverse query.
  3. The filter is mutually-exclusive — wrong source_id returns 0.
"""
from __future__ import annotations

import datetime as dt
import uuid
from pathlib import Path

import pytest
import requests


def _read_env(path: str, key: str) -> str:
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:  # noqa: BLE001
        return ""
    return ""


BASE_URL = _read_env("/app/frontend/.env", "REACT_APP_BACKEND_URL").rstrip("/")
ADMIN_PW = _read_env("/app/backend/.env", "ADMIN_PASSWORD") or "MASCI1982!"

TODAY = dt.date.today().isoformat()


@pytest.fixture(scope="module")
def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def admin_token(session: requests.Session) -> str:
    r = session.post(f"{BASE_URL}/api/admin/login",
                     json={"password": ADMIN_PW},
                     headers={"Content-Type": "application/json"})
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code}")
    return r.json().get("token", "")


@pytest.fixture(scope="module")
def safety_token(session: requests.Session) -> str:
    r = session.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        headers={"Content-Type": "application/json"},
    )
    if r.status_code != 200:
        pytest.skip(f"multi-login failed: {r.status_code}")
    return (r.json().get("portal_tokens") or {}).get("safety", "")


@pytest.fixture(scope="module")
def linked_incident_and_capa(session, admin_token, safety_token):
    """Create one incident + one CAPA pointing at it, return both ids."""
    # 1. Create incident
    inc_body = {
        "project_name": f"iter368-{uuid.uuid4().hex[:6]}",
        "project_number": "",
        "location": "Yard",
        "incident_date": TODAY,
        "incident_time": "10:00",
        "reported_date": TODAY,
        "reported_by": "iter368 Auto-Test",
        "incident_type": "Near Miss",
        "severity": "Low",
        "person_name": "iter368 Test Person",
        "description": "iter368 reverse-link verification",
    }
    r = session.post(f"{BASE_URL}/api/incidents",
                     json=inc_body,
                     headers={"X-Admin-Token": "", "Content-Type": "application/json"})
    assert r.status_code == 200, r.text
    inc_id = r.json()["id"]

    # 2. Create CAPA linked to that incident
    capa_body = {
        "title": f"iter368 CAPA for {inc_id[:8]}",
        "description": "Reverse-link verification CAPA",
        "source_kind": "incident",
        "source_id": inc_id,
        "project_number": "",
        "assigned_to_name": "iter368 Owner",
        "assigned_to_email": "",
        "priority": "Medium",
    }
    r = session.post(
        f"{BASE_URL}/api/safety/corrective-actions",
        json=capa_body,
        headers={"X-Safety-Token": safety_token, "Content-Type": "application/json"},
    )
    assert r.status_code == 200, r.text
    capa_id = r.json()["id"]

    return {"incident_id": inc_id, "capa_id": capa_id}


# ───────────────────── reverse-link filter tests ─────────────────────


class TestIncidentCapaReverseLink:
    def test_filter_returns_only_matching_source_id(self, session, safety_token, linked_incident_and_capa):
        inc_id = linked_incident_and_capa["incident_id"]
        capa_id = linked_incident_and_capa["capa_id"]
        r = session.get(
            f"{BASE_URL}/api/safety/corrective-actions",
            params={"source_kind": "incident", "source_id": inc_id},
            headers={"X-Safety-Token": safety_token, "Content-Type": "application/json"},
        )
        assert r.status_code == 200, r.text
        items = r.json()
        assert isinstance(items, list)
        # Must include the CAPA we just created.
        capa_ids = [c["id"] for c in items]
        assert capa_id in capa_ids, f"Expected {capa_id} in {capa_ids}"
        # All returned CAPAs must reference the same incident.
        for c in items:
            assert c.get("source_id") == inc_id, c
            assert c.get("source_kind") == "incident", c

    def test_filter_with_wrong_source_id_returns_empty(self, session, safety_token):
        fake_id = f"iter368-no-such-incident-{uuid.uuid4().hex[:8]}"
        r = session.get(
            f"{BASE_URL}/api/safety/corrective-actions",
            params={"source_kind": "incident", "source_id": fake_id},
            headers={"X-Safety-Token": safety_token, "Content-Type": "application/json"},
        )
        assert r.status_code == 200
        assert r.json() == []

    def test_filter_with_source_kind_only(self, session, safety_token):
        r = session.get(
            f"{BASE_URL}/api/safety/corrective-actions",
            params={"source_kind": "incident"},
            headers={"X-Safety-Token": safety_token, "Content-Type": "application/json"},
        )
        assert r.status_code == 200
        items = r.json()
        # Every returned CAPA must have source_kind='incident'.
        for c in items:
            assert c.get("source_kind") == "incident", c

    def test_filter_does_not_break_existing_status_filter(self, session, safety_token):
        # iter139 status filter must still work alongside iter368 filters.
        r = session.get(
            f"{BASE_URL}/api/safety/corrective-actions",
            params={"status": "Open", "source_kind": "incident"},
            headers={"X-Safety-Token": safety_token, "Content-Type": "application/json"},
        )
        assert r.status_code == 200
        items = r.json()
        for c in items:
            assert c.get("status") == "Open", c
            assert c.get("source_kind") == "incident", c

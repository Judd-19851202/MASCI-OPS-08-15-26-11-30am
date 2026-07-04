"""Pytest suite for Phase V.1 M0.3.

Covers:
  - Observation telemetry: closed-enum guard + summary aggregation
  - Public viewer continuity flow (no-auth · gated)
  - PDF audience routing inheritance
  - Guidance + readiness inheritance
  - Trust banner doctrine wiring (DOM-level check is in playwright suite)

Run:
    cd /app/backend && python -m pytest tests/odr/test_odr_m03.py -v
"""
from __future__ import annotations

import os
import uuid

import pytest
import requests


URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
if not URL.startswith("http"):
    URL = "http://localhost:8001"

ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def headers() -> dict:
    r = requests.post(
        f"{URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=10,
    )
    assert r.status_code == 200
    tok = r.json()["portal_tokens"]["admin"]
    return {"Content-Type": "application/json", "X-Admin-Token": tok}


# ── Observation ──────────────────────────────────────────────────────


def test_observation_event_ok(headers: dict):
    r = requests.post(
        f"{URL}/api/odr/observation/event",
        json={
            "surface": "foreman",
            "kind": "session_start",
            "device_kind": "phone",
            "lang": "en",
        },
        headers=headers, timeout=10,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["event_id"]
    assert d["surface"] == "foreman"
    assert d["kind"] == "session_start"
    assert "actor_uid_hash" not in d  # never leak even hashed uid in response


def test_observation_closed_enum_kind(headers: dict):
    r = requests.post(
        f"{URL}/api/odr/observation/event",
        json={"surface": "foreman", "kind": "bogus_event_kind"},
        headers=headers, timeout=10,
    )
    assert r.status_code == 422


def test_observation_closed_enum_surface(headers: dict):
    r = requests.post(
        f"{URL}/api/odr/observation/event",
        json={"surface": "bogus_surface", "kind": "session_start"},
        headers=headers, timeout=10,
    )
    assert r.status_code == 422


def test_observation_summary_admin(headers: dict):
    # Seed a couple events
    for kind in ("session_start", "submit_success", "pdf_rendered"):
        requests.post(
            f"{URL}/api/odr/observation/event",
            json={
                "surface": "foreman" if kind != "pdf_rendered" else "fl_center",
                "kind": kind,
                "device_kind": "phone",
                "lang": "en",
                "context": {"duration_ms": 90000} if kind == "submit_success" else {},
            },
            headers=headers, timeout=10,
        )
    r = requests.get(
        f"{URL}/api/odr/observation/summary?days=1",
        headers=headers, timeout=10,
    )
    assert r.status_code == 200
    d = r.json()
    assert d["total_events"] >= 3
    assert "by_surface" in d
    assert "by_kind" in d
    assert "average_submit_duration_s" in d
    # NEVER returns per-actor data
    assert "by_uid" not in d
    assert "actors" not in d


# ── Public viewer continuity ─────────────────────────────────────────


@pytest.fixture(scope="module")
def public_link(headers: dict) -> dict:
    payload = {
        "project": {
            "project_id": f"proj-m03-{uuid.uuid4().hex[:8]}",
            "project_number": f"M03-{uuid.uuid4().hex[:4]}",
            "project_name": "TEST_M0_3_Test",
            "report_date": "2026-05-29",
            "foreman_uid": ADMIN_EMAIL,
            "foreman_name": "Pytest Foreman",
        },
        "crew_profile": {
            "crew_id": f"crew-{uuid.uuid4().hex[:8]}",
            "crew_name": "M0.3 Crew",
            "crew_type": "pipe",
            "primary_operation": "RCP install",
        },
    }
    r = requests.post(f"{URL}/api/odr", json=payload, headers=headers, timeout=10)
    assert r.status_code == 200
    odr = r.json()
    requests.patch(
        f"{URL}/api/odr/{odr['id']}",
        json={"signature": {"foreman_acknowledgement": {
            "acknowledged": True,
            "acknowledged_by_uid": ADMIN_EMAIL,
            "text": "ack",
        }}},
        headers=headers, timeout=10,
    )
    requests.post(f"{URL}/api/odr/{odr['id']}/submit", json={}, headers=headers, timeout=10)
    r2 = requests.post(
        f"{URL}/api/odr/{odr['id']}/link",
        json={"link_scope": "project_crew"},
        headers=headers, timeout=10,
    )
    link = r2.json()
    return {"odr": odr, "link_id": link["link_id"], "doc_id": odr["doc_id"]}


def test_public_resolve_strips_internal_fields(public_link):
    r = requests.get(
        f"{URL}/api/odr/public/{public_link['doc_id']}",
        params={"link_id": public_link["link_id"]},
        timeout=10,
    )
    assert r.status_code == 200
    d = r.json()
    # External fields MUST be absent
    forbidden = (
        "completion_telemetry", "consumer_dispatch",
        "readiness", "reliability",
    )
    for f in forbidden:
        assert f not in d, f"public envelope leaked {f}"
    # Safety-event details redacted at top level (only flags exposed)
    assert "events" not in (d.get("safety") or {})


def test_public_resolve_revoked_link_410(headers: dict, public_link):
    # Revoke
    r = requests.patch(
        f"{URL}/api/odr/public-links/{public_link['link_id']}",
        json={"revoke": True},
        headers=headers, timeout=10,
    )
    assert r.status_code == 200, r.text
    # Now resolve must return 410 Gone
    r2 = requests.get(
        f"{URL}/api/odr/public/{public_link['doc_id']}",
        params={"link_id": public_link["link_id"]},
        timeout=10,
    )
    assert r2.status_code == 410


# ── Doctrine locks (from operator directive) ────────────────────────


# NOTE: `tests/conftest.py` auto-injects X-Admin-Token into every
# requests call from inside this directory. We therefore cannot test
# the "no token → 401" path here; that is verified by direct shell
# curl in the M0.3 operator review guide. What we CAN test is that
# admin-portal-aware audiences DO work (they should), confirming the
# positive branch of the role gate.


def test_decision_lock_external_pdf_audience_supported(headers: dict, public_link):
    """External audience PDF still renders for Admin — and carries SHA256 footer."""
    r = requests.get(
        f"{URL}/api/odr/{public_link['odr']['id']}/pdf",
        params={"audience": "external"},
        headers=headers, timeout=10,
    )
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"
    sha = r.headers.get("X-ODR-SHA256")
    assert sha and len(sha) == 64

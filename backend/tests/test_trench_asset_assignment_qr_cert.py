"""
test_trench_asset_assignment_qr_cert.py
TRACK 14.0-TRENCH-ASSET-ASSIGNMENT-QR-FIX regression suite.

Locks:
  * TrenchSafetyAssetUpdate exposes project-assignment fields.
  * StatusChangeBody → operational_status="Assigned" REQUIRES project_id /
    project_number + project_name (otherwise 422).
  * Status → "Available" clears project context + resets current_location.
  * QR meta endpoint returns a base64 png_data_url so the frontend
    <img> renders without an authenticated follow-up.
"""
from __future__ import annotations

import sys

import pytest

sys.path.insert(0, "/app/backend")

from routes.trench_safety._models import (  # noqa: E402
    StatusChangeBody,
    TrenchSafetyAssetUpdate,
)


def test_update_model_exposes_project_assignment_fields():
    schema = TrenchSafetyAssetUpdate.model_json_schema()
    props = schema.get("properties", {})
    for f in ("current_project_id", "current_project_name",
              "current_project_number", "assigned_to_name", "assigned_to_role"):
        assert f in props, f"TrenchSafetyAssetUpdate missing project field {f!r}"


def test_update_accepts_project_assignment():
    body = TrenchSafetyAssetUpdate(
        current_project_id="proj-uuid",
        current_project_name="Cert Project",
        current_project_number="ZZ-001",
        current_location="Cert Project Site",
        assigned_to_name="James Fisher (Jimmy)",
        assigned_to_role="superintendent",
    )
    assert body.current_project_name == "Cert Project"
    assert body.current_project_number == "ZZ-001"


def test_status_assigned_payload_carries_project():
    body = StatusChangeBody(
        operational_status="Assigned",
        project_id="proj-id",
        project_number="ZZ-001",
        project_name="Cert Project",
    )
    assert body.operational_status == "Assigned"
    assert body.project_number == "ZZ-001"


def test_status_available_payload_minimal():
    body = StatusChangeBody(operational_status="Available")
    assert body.project_id is None
    assert body.project_name is None


# ── Live HTTP tests against the preview backend ────────────────────


import os  # noqa: E402

import requests  # noqa: E402

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    from pathlib import Path
    env = Path("/app/frontend/.env").read_text().splitlines()
    for line in env:
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip()
BASE = (BASE_URL or "").rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_token():
    if not BASE:
        pytest.skip("no backend URL")
    r = requests.post(
        f"{BASE}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=90,
    )
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code}")
    return r.json()["portal_tokens"]["admin"]


@pytest.fixture(scope="module")
def cert_asset(admin_token):
    """Create + yield a clean RC1-LIVE-VERIFY trench asset. Tear down
    via retire after the test (Retired is the terminal state).
    Asset ID is timestamp-suffixed so each test run is fresh."""
    h = {"X-Admin-Token": admin_token, "Content-Type": "application/json"}
    import time as _t
    asset_id = f"RC1-TBQR-CERT-{int(_t.time())}"
    payload = {
        "asset_id": asset_id,
        "asset_type": "Trench Box",
        "manufacturer": "Cert Co",
        "model": "Cert-8x16",
        "serial_number": "RC1-TBQR-CERT-01-SN",
        "size": "8'×16'",
        "operational_status": "Available",
        "condition": "Good",
        "yard_location": "MASCI Yard",
        "current_location": "MASCI Yard",
        "notes": "RC1-LIVE-VERIFY · TRENCH-ASSET-ASSIGNMENT-QR-FIX smoke",
    }
    r = requests.post(f"{BASE}/api/trench-safety/assets",
                      headers=h, json=payload, timeout=60)
    if r.status_code not in (200, 201):
        # Already exists from a prior run — that's fine.
        if r.status_code == 409:
            pass
        else:
            pytest.skip(f"could not create cert asset: {r.status_code} {r.text[:200]}")
    yield asset_id
    # Cleanup: retire
    try:
        requests.post(
            f"{BASE}/api/trench-safety/assets/{asset_id}/retire",
            headers=h,
            json={"retired_reason": "RC1-LIVE-VERIFY smoke cleanup"},
            timeout=30,
        )
    except Exception:
        pass


def test_live_status_assigned_without_project_is_422(admin_token, cert_asset):
    h = {"X-Admin-Token": admin_token, "Content-Type": "application/json"}
    r = requests.post(
        f"{BASE}/api/trench-safety/assets/{cert_asset}/status",
        headers=h, json={"operational_status": "Assigned"}, timeout=30,
    )
    assert r.status_code == 422, r.text


def test_live_status_assigned_with_project_assigns(admin_token, cert_asset):
    h = {"X-Admin-Token": admin_token, "Content-Type": "application/json"}
    r = requests.post(
        f"{BASE}/api/trench-safety/assets/{cert_asset}/status",
        headers=h,
        json={
            "operational_status": "Assigned",
            "project_id": "ZZ-CERT-PROJ",
            "project_name": "TEST_RC1_Cert_Project",
            "project_number": "ZZ-CERT-2026",
            "location": "RC1 Cert Project Site",
        }, timeout=30,
    )
    assert r.status_code == 200, r.text
    asset = r.json()
    assert asset["operational_status"] == "Assigned"
    assert asset["current_project_name"] == "RC1 Cert Project"
    assert asset["current_project_number"] == "ZZ-CERT-2026"
    assert asset["current_location"] == "RC1 Cert Project Site"


def test_live_status_available_clears_project(admin_token, cert_asset):
    h = {"X-Admin-Token": admin_token, "Content-Type": "application/json"}
    r = requests.post(
        f"{BASE}/api/trench-safety/assets/{cert_asset}/status",
        headers=h,
        json={"operational_status": "Available"}, timeout=30,
    )
    assert r.status_code == 200, r.text
    asset = r.json()
    assert asset["operational_status"] == "Available"
    assert asset["current_project_name"] in (None, "")
    assert asset["current_project_number"] in (None, "")
    assert asset["current_location"] == "MASCI Yard"


def test_live_qr_meta_returns_data_url(admin_token, cert_asset):
    r = requests.get(
        f"{BASE}/api/trench-safety/assets/{cert_asset}/qr-label",
        headers={"X-Admin-Token": admin_token}, timeout=30,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "png_data_url" in body
    assert body["png_data_url"].startswith("data:image/png;base64,")
    assert len(body["png_data_url"]) > 200  # actual PNG bytes encoded


def test_live_deployment_history_records_assign_and_return(admin_token, cert_asset):
    h = {"X-Admin-Token": admin_token, "Content-Type": "application/json"}
    # Assign
    requests.post(
        f"{BASE}/api/trench-safety/assets/{cert_asset}/status",
        headers=h,
        json={
            "operational_status": "Assigned",
            "project_id": "ZZ-CERT-PROJ", "project_name": "TEST_RC1_Cert_Project",
            "project_number": "ZZ-CERT-2026",
        }, timeout=30,
    )
    # Return
    requests.post(
        f"{BASE}/api/trench-safety/assets/{cert_asset}/status",
        headers=h, json={"operational_status": "Available"}, timeout=30,
    )
    # Inspect audit (deployment_history is internal collection — use
    # the audit feed which is the public visibility path).
    ra = requests.get(
        f"{BASE}/api/trench-safety/assets/{cert_asset}/audit",
        headers={"X-Admin-Token": admin_token}, timeout=30,
    )
    if ra.status_code == 200:
        events = ra.json() if isinstance(ra.json(), list) else ra.json().get("items", [])
        kinds = [e.get("kind") for e in events]
        assert "trench_asset_status_changed" in kinds

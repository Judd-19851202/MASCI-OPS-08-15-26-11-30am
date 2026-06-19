"""Phase 8B — Operational Polish backend tests.

Validates the operational adoption layer:
  • Dashboard endpoint exposes the new Phase 8B alert counters
    (on_hold, no_project_assignment, missing_photos,
    road_plate_missing_capacity) AND recent_activity_7d.
  • Asset search `$or` accepts QR code value + markings.
  • CSV import preview validates rows without writing.
  • CSV import commit writes new assets through the same path the
    single-asset create endpoint uses (audit + mirror).
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
    pwd = os.environ.get("ADMIN_PASSWORD", "Maddix123!")
    r = requests.post(f"{API}/api/admin/login", json={"password": pwd}, timeout=15)
    r.raise_for_status()
    return r.json()["token"]


def _h(token: str) -> dict:
    return {"X-Admin-Token": token, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def token():
    return _admin_token()


# ─────────────────────────────────────────────────────────────────────
# 1 · Dashboard exposes Phase 8B fields
# ─────────────────────────────────────────────────────────────────────
def test_dashboard_phase8b_fields(token):
    r = requests.get(f"{API}/api/trench-safety/dashboard", headers=_h(token), timeout=15)
    r.raise_for_status()
    data = r.json()
    al = data.get("alerts", {})
    for k in ["on_hold", "no_project_assignment", "missing_photos", "road_plate_missing_capacity"]:
        assert k in al, f"alerts.{k} missing"
        assert isinstance(al[k], int)
    assert "recent_activity_7d" in data


# ─────────────────────────────────────────────────────────────────────
# 2 · Search extension — qr_code_value + markings
# ─────────────────────────────────────────────────────────────────────
def test_search_supports_qr_value(token):
    # Pick a known seed asset — TB-01 has qr_code_value="TB-01"
    r = requests.get(
        f"{API}/api/trench-safety/assets",
        headers=_h(token), params={"q": "TB-01"}, timeout=15,
    )
    r.raise_for_status()
    ids = [a["asset_id"] for a in r.json().get("items", [])]
    assert "TB-01" in ids


def test_search_supports_markings(token):
    # Create a Road Plate with a distinctive marking string, then
    # search by a substring of the markings.
    aid = f"RP-MK{uuid.uuid4().hex[:4].upper()}"
    marker = f"MARK-{uuid.uuid4().hex[:6].upper()}"
    requests.post(
        f"{API}/api/trench-safety/assets",
        headers=_h(token),
        json={
            "asset_id": aid, "asset_type": "Road Plate",
            "condition": "Good", "markings": marker,
        }, timeout=15,
    ).raise_for_status()
    try:
        r = requests.get(
            f"{API}/api/trench-safety/assets",
            headers=_h(token), params={"q": marker[:8]}, timeout=15,
        )
        r.raise_for_status()
        ids = [a["asset_id"] for a in r.json().get("items", [])]
        assert aid in ids
    finally:
        requests.post(
            f"{API}/api/trench-safety/assets/{aid}/retire",
            headers=_h(token), json={"retired_reason": "test"}, timeout=15,
        )


# ─────────────────────────────────────────────────────────────────────
# 3 · CSV import preview — validation only, no writes
# ─────────────────────────────────────────────────────────────────────
def _count_assets(token) -> int:
    r = requests.get(f"{API}/api/trench-safety/assets", headers=_h(token), timeout=15)
    r.raise_for_status()
    return len(r.json().get("items", []))


def test_csv_import_preview_does_not_write(token):
    rp_id = f"RP-CS{uuid.uuid4().hex[:4].upper()}"
    csv_text = f"""asset_id,asset_type,manufacturer,size,condition
{rp_id},Road Plate,Acme Steel,96x48,Good
TB-01,Trench Box,Already Exists,,Good
,End Panel,Missing ID,7x8,Good
"""
    before = _count_assets(token)
    r = requests.post(
        f"{API}/api/trench-safety/assets/import/preview",
        headers=_h(token), json={"csv_text": csv_text}, timeout=15,
    )
    r.raise_for_status()
    body = r.json()
    assert body["total_rows"] == 3
    statuses = {d["asset_id"]: d["status"] for d in body["diagnoses"]}
    assert statuses[rp_id] == "will_insert"
    assert statuses["TB-01"] == "duplicate"
    # Error row may have empty asset_id but status="error"
    error_diag = [d for d in body["diagnoses"] if d["status"] == "error"]
    assert len(error_diag) >= 1
    # Counts add up
    assert body["counts"]["will_insert"] >= 1
    assert body["counts"]["duplicate"] >= 1
    assert body["counts"]["error"] >= 1
    # No new rows were written
    after = _count_assets(token)
    assert after == before


# ─────────────────────────────────────────────────────────────────────
# 4 · CSV import commit — writes via the same certified path
# ─────────────────────────────────────────────────────────────────────
def test_csv_import_commit_writes_valid_rows(token):
    rp1 = f"RP-CI{uuid.uuid4().hex[:3].upper()}A"
    rp2 = f"RP-CI{uuid.uuid4().hex[:3].upper()}B"
    csv_text = f"""asset_id,asset_type,manufacturer,size,condition,length_in,width_in,thickness_in,rated_capacity_lb,material
{rp1},Road Plate,Acme,96x48,Good,96,48,1.0,80000,A36 Steel
{rp2},Road Plate,Acme,72x48,Good,72,48,0.75,60000,A36 Steel
TB-01,Trench Box,Dup,,Good,,,,,
"""
    try:
        r = requests.post(
            f"{API}/api/trench-safety/assets/import",
            headers=_h(token), json={"csv_text": csv_text}, timeout=20,
        )
        r.raise_for_status()
        body = r.json()
        assert body["inserted_count"] == 2
        assert rp1 in body["inserted"]
        assert rp2 in body["inserted"]
        assert body["skipped_count"] >= 1
        # Verify they actually landed in the registry with their physical specs
        r2 = requests.get(f"{API}/api/trench-safety/assets/{rp1}", headers=_h(token), timeout=15)
        r2.raise_for_status()
        doc = r2.json()
        assert doc["asset_type"] == "Road Plate"
        assert doc["length_in"] == 96
        assert doc["rated_capacity_lb"] == 80000
        # Audit row exists
        r3 = requests.get(
            f"{API}/api/trench-safety/assets/{rp1}/audit",
            headers=_h(token), timeout=15,
        )
        r3.raise_for_status()
        kinds = [ev["kind"] for ev in r3.json().get("items", [])]
        assert "trench_asset_created" in kinds
    finally:
        for aid in (rp1, rp2):
            requests.post(
                f"{API}/api/trench-safety/assets/{aid}/retire",
                headers=_h(token), json={"retired_reason": "test"}, timeout=15,
            )


def test_csv_import_rejects_oversize_payload(token):
    # Build 501 valid-ish rows; backend must 413
    rows = ["asset_id,asset_type,condition"]
    for i in range(501):
        rows.append(f"RP-Z{i:04d},Road Plate,Good")
    r = requests.post(
        f"{API}/api/trench-safety/assets/import/preview",
        headers=_h(token), json={"csv_text": "\n".join(rows)}, timeout=20,
    )
    assert r.status_code == 413

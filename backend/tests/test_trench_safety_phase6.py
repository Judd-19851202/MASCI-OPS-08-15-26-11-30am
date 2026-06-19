"""Trench Safety · Phase 6 — Shop Repair Workflow test suite.

OMEGA Phase 6 — Shop-facing trench safety repair queue, status workflow,
completion, and Safety verification (which is the ONLY path that releases
an Inspection Hold tied to a reinspection-required repair).

Hold preservation is the non-negotiable invariant:
  - Repair Complete does NOT equal Safe To Use.
  - Higher-priority holds (Safety / Certification) survive every action.
"""
from __future__ import annotations

import os
import uuid
from typing import Dict

import httpx
import pytest

API_BASE = (os.environ.get("TRENCH_SAFETY_API_BASE") or "http://localhost:8001").rstrip("/")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Maddix123!")


@pytest.fixture(scope="module")
def admin_headers() -> Dict[str, str]:
    r = httpx.post(f"{API_BASE}/api/admin/login", json={"password": ADMIN_PASSWORD}, timeout=15.0)
    assert r.status_code == 200
    return {"X-Admin-Token": r.json()["token"]}


@pytest.fixture
def client() -> httpx.Client:
    return httpx.Client(base_url=API_BASE, timeout=20.0)


def _reset_asset(client, headers, tag):
    # Close ALL open / in-progress / waiting / vendor repairs for the asset
    # (left behind by prior Phase 4B / 5 test runs). Phase 6 needs a clean
    # repair slate to assert hold transitions deterministically.
    for st in ("Open", "In Progress", "Waiting on Parts", "Vendor Repair", "Completed"):
        existing = client.get(f"/api/trench-safety/assets/{tag}/repairs",
                              params={"status": st, "limit": 500},
                              headers=headers).json().get("items", [])
        for rep in existing:
            try:
                client.post(f"/api/trench-safety/repairs/{rep['id']}/complete", headers=headers)
                client.post(f"/api/trench-safety/repairs/{rep['id']}/verify",
                            json={"verification_notes": "phase6 reset", "reinspection_passed": True},
                            headers=headers)
            except Exception:
                pass
    r = client.get(f"/api/trench-safety/assets/{tag}/holds", params={"active_only": "true"}, headers=headers)
    if r.status_code == 200:
        for h in r.json().get("items", []):
            client.post(f"/api/trench-safety/holds/{h['id']}/clear",
                        json={"clear_reason": "phase6 reset", "clear_source": "manual"}, headers=headers)
    client.put(f"/api/trench-safety/assets/{tag}", json={"requires_certification": False}, headers=headers)
    client.post(f"/api/trench-safety/assets/{tag}/return", json={"returned_by": "phase6-reset"}, headers=headers)


@pytest.fixture(scope="module", autouse=True)
def _phase6_setup(admin_headers):
    with httpx.Client(base_url=API_BASE, timeout=15.0) as c:
        for tag in ("TB-01", "TB-02", "TB-03", "TB-04", "TB-05", "TB-06", "TB-07"):
            _reset_asset(c, admin_headers, tag)
    yield
    with httpx.Client(base_url=API_BASE, timeout=15.0) as c:
        for tag in ("TB-01", "TB-02", "TB-03", "TB-04", "TB-05", "TB-06", "TB-07"):
            _reset_asset(c, admin_headers, tag)


def _fail_inspection(client, headers, tag, severity):
    return client.post(
        f"/api/trench-safety/assets/{tag}/inspections",
        json={
            "inspection_type": "Daily Visual", "inspector_name": "phase6",
            "result": "Fail", "severity": severity, "findings": f"phase6 {severity}",
            "checklist": [],
        }, headers=headers,
    )


# ──────────────────────────────────────────────────────────────────────
# § Shop queue
# ──────────────────────────────────────────────────────────────────────

def test_shop_queue_lists_repairs_with_asset_metadata(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-01")
    r = _fail_inspection(client, admin_headers, "TB-01", "Major")
    assert r.json()["repair_stub_id"]
    q = client.get("/api/trench-safety/shop/repairs", headers=admin_headers).json()
    rows = [x for x in q["items"] if x["asset_id"] == "TB-01" and x["status"] != "Closed After Verification"]
    assert rows, "TB-01 repair stub should appear in the queue"
    row = rows[0]
    assert row["asset_type"] is not None
    assert row["size"] is not None
    assert row["operational_status"] in ("Maintenance Hold", "Safety Hold", "Inspection Hold")


def test_queue_filter_by_status_and_severity(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-02")
    _fail_inspection(client, admin_headers, "TB-02", "Critical")
    q = client.get("/api/trench-safety/shop/repairs",
                   params={"severity": "Critical"}, headers=admin_headers).json()
    assert q["count"] >= 1
    assert all(x["severity_at_creation"] == "Critical" for x in q["items"])


def test_critical_inspection_creates_safety_hold(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-03")
    r = _fail_inspection(client, admin_headers, "TB-03", "Critical")
    assert r.json()["asset"]["operational_status"] == "Safety Hold"


# ──────────────────────────────────────────────────────────────────────
# § Status workflow
# ──────────────────────────────────────────────────────────────────────

def _get_repair(client, headers, tag):
    return client.get(f"/api/trench-safety/assets/{tag}/repairs",
                      params={"status": "Open"}, headers=headers).json()["items"][0]


def test_shop_can_start_and_progress_repair(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-04")
    _fail_inspection(client, admin_headers, "TB-04", "Major")
    rep = _get_repair(client, admin_headers, "TB-04")
    rid = rep["id"]
    # Start → In Progress
    r = client.patch(f"/api/trench-safety/repairs/{rid}",
                     json={"status": "In Progress"}, headers=admin_headers)
    assert r.status_code == 200 and r.json()["status"] == "In Progress"
    # Waiting on Parts
    r = client.patch(f"/api/trench-safety/repairs/{rid}",
                     json={"status": "Waiting on Parts"}, headers=admin_headers)
    assert r.json()["status"] == "Waiting on Parts"
    # Vendor Repair
    r = client.patch(f"/api/trench-safety/repairs/{rid}",
                     json={"status": "Vendor Repair", "repair_vendor": "Test Vendor",
                           "repair_cost": 1234.56}, headers=admin_headers)
    assert r.json()["status"] == "Vendor Repair"
    assert r.json()["repair_vendor"] == "Test Vendor"
    assert r.json()["repair_cost"] == 1234.56


def test_shop_can_append_repair_notes(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-05")
    _fail_inspection(client, admin_headers, "TB-05", "Major")
    rep = _get_repair(client, admin_headers, "TB-05")
    rid = rep["id"]
    client.patch(f"/api/trench-safety/repairs/{rid}",
                 json={"note": "ordered welding kit"}, headers=admin_headers)
    client.patch(f"/api/trench-safety/repairs/{rid}",
                 json={"note": "kit arrived"}, headers=admin_headers)
    fresh = client.get(f"/api/trench-safety/assets/TB-05/repairs",
                       params={"status": "Open"}, headers=admin_headers).json()["items"][0]
    history = fresh.get("notes_history", [])
    assert len(history) == 2
    assert history[0]["text"] == "ordered welding kit"
    assert history[1]["text"] == "kit arrived"


def test_shop_complete_does_not_clear_inspection_hold_when_reinspection_required(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-06")
    _fail_inspection(client, admin_headers, "TB-06", "Major")
    rep = _get_repair(client, admin_headers, "TB-06")
    r = client.post(f"/api/trench-safety/repairs/{rep['id']}/complete", headers=admin_headers)
    assert r.status_code == 200
    # Repair Completed but Inspection Hold remains because requires_reinspection=true
    asset = r.json()["asset"]
    assert asset["operational_status"] == "Inspection Hold", \
        f"expected Inspection Hold after Major repair completes (reinspection required), got {asset['operational_status']}"


def test_higher_priority_safety_hold_survives_repair_completion(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-07")
    _fail_inspection(client, admin_headers, "TB-07", "Critical")
    rep = _get_repair(client, admin_headers, "TB-07")
    r = client.post(f"/api/trench-safety/repairs/{rep['id']}/complete", headers=admin_headers)
    assert r.status_code == 200
    # Safety Hold remains (higher priority than Maintenance/Inspection)
    assert r.json()["asset"]["operational_status"] == "Safety Hold"


# ──────────────────────────────────────────────────────────────────────
# § Safety verification
# ──────────────────────────────────────────────────────────────────────

def test_safety_verification_closes_repair_and_releases_inspection_hold(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-01")
    _fail_inspection(client, admin_headers, "TB-01", "Major")
    rep = _get_repair(client, admin_headers, "TB-01")
    # Complete the repair (Shop side)
    client.post(f"/api/trench-safety/repairs/{rep['id']}/complete", headers=admin_headers)
    # Safety verifies — pass
    r = client.post(
        f"/api/trench-safety/repairs/{rep['id']}/verify",
        json={"verification_notes": "Visual + dim check OK", "reinspection_passed": True},
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json()["repair"]["status"] == "Closed After Verification"
    # Inspection Hold cleared → Asset back to Available
    assert r.json()["asset"]["operational_status"] == "Available"


def test_safety_verification_with_failed_reinspection_keeps_hold(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-02")
    _fail_inspection(client, admin_headers, "TB-02", "Major")
    rep = _get_repair(client, admin_headers, "TB-02")
    client.post(f"/api/trench-safety/repairs/{rep['id']}/complete", headers=admin_headers)
    r = client.post(
        f"/api/trench-safety/repairs/{rep['id']}/verify",
        json={"verification_notes": "Still bent — not acceptable", "reinspection_passed": False},
        headers=admin_headers,
    )
    assert r.status_code == 200
    assert r.json()["repair"]["status"] == "Closed After Verification"
    # Inspection Hold remains because reinspection_passed=False
    assert r.json()["asset"]["operational_status"] == "Inspection Hold"


def test_verify_rejects_uncompleted_repair(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-03")
    _fail_inspection(client, admin_headers, "TB-03", "Major")
    rep = _get_repair(client, admin_headers, "TB-03")
    r = client.post(
        f"/api/trench-safety/repairs/{rep['id']}/verify",
        json={"verification_notes": "premature", "reinspection_passed": True},
        headers=admin_headers,
    )
    assert r.status_code == 409


# ──────────────────────────────────────────────────────────────────────
# § Visibility — equipment_master / by-project / public QR
# ──────────────────────────────────────────────────────────────────────

def test_equipment_master_reflects_maintenance_hold_during_repair(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-04")
    _fail_inspection(client, admin_headers, "TB-04", "Major")
    em = next((i for i in client.get("/api/equipment-master", params={"category": "Trench Safety"}).json()["items"]
               if i["asset_id"] == "TB-04"), None)
    assert em is not None
    assert em["operational_status"] in ("Maintenance Hold", "Safety Hold", "Inspection Hold")
    holds = [h["kind"] for h in em.get("active_holds", [])]
    assert "Maintenance Hold" in holds


def test_public_qr_view_shows_do_not_use_during_repair(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-05")
    _fail_inspection(client, admin_headers, "TB-05", "Major")
    pub = client.get("/api/trench-safety/public/assets/TB-05").json()
    assert pub["operational_status"] in ("Maintenance Hold", "Safety Hold", "Inspection Hold")
    # No admin/PII leakage
    for forbidden in ("repair_vendor", "repair_cost", "updated_by", "notes_history"):
        assert forbidden not in pub, f"public field view must NOT expose {forbidden}"


# ──────────────────────────────────────────────────────────────────────
# § Audit trail
# ──────────────────────────────────────────────────────────────────────

def test_audit_chain_for_full_repair_lifecycle(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-06")
    _fail_inspection(client, admin_headers, "TB-06", "Major")
    rep = _get_repair(client, admin_headers, "TB-06")
    client.patch(f"/api/trench-safety/repairs/{rep['id']}",
                 json={"status": "In Progress", "note": "starting"}, headers=admin_headers)
    client.post(f"/api/trench-safety/repairs/{rep['id']}/complete", headers=admin_headers)
    client.post(f"/api/trench-safety/repairs/{rep['id']}/verify",
                json={"verification_notes": "OK", "reinspection_passed": True}, headers=admin_headers)
    audit = client.get("/api/trench-safety/assets/TB-06/audit",
                       params={"limit": 200}, headers=admin_headers).json()["items"]
    kinds = {e["kind"] for e in audit}
    assert "trench_asset_repair_updated" in kinds
    assert "trench_asset_repair_completed" in kinds
    assert "trench_asset_repair_verified" in kinds

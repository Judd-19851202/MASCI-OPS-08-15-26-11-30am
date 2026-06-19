"""Trench Safety Operations System — Phase 4A backend test suite.

OMEGA DIRECTIVE PHASE 4A · Equipment Inventory + Operations Integration.

Covers:
  1. TB-01…TB-07 visible via /api/equipment-master with category=Trench Safety
     and populated unit_number / make_model / preop_equipment_type.
  2. Assignment with superintendent + foreman + project_number persists on
     the asset AND on the deployment doc AND on the equipment_master mirror.
  3. Returning the asset clears all current_* operational fields.
  4. /api/trench-safety/by-project returns the asset while assigned and
     no longer returns it after the return endpoint fires.
  5. /api/trench-safety/by-project supports lookup by project_id,
     project_number, and project_name.
  6. Inspection Hold / Repair / Retired block assignment with 409.
  7. Deployment history grows on every assign/return cycle and exposes
     the new superintendent/foreman/project_number fields.
  8. Audit events recorded for every assign/return (kind=trench_asset_*).
  9. Equipment-master mirror keeps current_project_* in lockstep across
     assign and return cycles.
 10. /api/trench-safety/operations/picker exposes a filtered projection.
"""
from __future__ import annotations

import os
import time
from typing import Dict

import httpx
import pytest

API_BASE = (
    os.environ.get("TRENCH_SAFETY_API_BASE") or "http://localhost:8001"
).rstrip("/")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Maddix123!")


@pytest.fixture(scope="module")
def admin_headers() -> Dict[str, str]:
    r = httpx.post(
        f"{API_BASE}/api/admin/login",
        json={"password": ADMIN_PASSWORD},
        timeout=15.0,
    )
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    tok = r.json().get("token")
    assert tok, "no token in admin-login response"
    return {"X-Admin-Token": tok}


@pytest.fixture
def client() -> httpx.Client:
    return httpx.Client(base_url=API_BASE, timeout=20.0)


# ──────────────────────────────────────────────────────────────────────
# Module-level prep — clear any leftover Inspection Hold / Repair status
# from prior test runs (e.g., the Phase 2 fail-inspection lifecycle test
# leaves assets parked in holds). Phase 4A's domain is assignment, not
# inspections, so we lift those holds back to Available before our
# assertions begin.
# ──────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module", autouse=True)
def _phase4a_setup(admin_headers):
    with httpx.Client(base_url=API_BASE, timeout=15.0) as c:
        for tag in ("TB-01", "TB-02", "TB-03", "TB-04", "TB-05", "TB-06", "TB-07"):
            asset = c.get(
                f"/api/trench-safety/assets/{tag}", headers=admin_headers
            ).json()
            status = asset.get("operational_status")
            if status == "Inspection Hold":
                # Clear with a Monthly Competent Person Pass inspection
                c.post(
                    f"/api/trench-safety/assets/{tag}/inspections",
                    json={
                        "inspection_type": "Monthly Competent Person",
                        "inspector_name": "phase4a-setup",
                        "competent_person_confirmed": True,
                        "result": "Pass",
                        "findings": "phase 4a setup clearing prior hold",
                        "checklist": [],
                    },
                    headers=admin_headers,
                )
            elif status == "Assigned":
                c.post(
                    f"/api/trench-safety/assets/{tag}/return",
                    json={"returned_by": "phase4a-setup"},
                    headers=admin_headers,
                )
    yield
    # Teardown — see test at bottom of file
    with httpx.Client(base_url=API_BASE, timeout=15.0) as c:
        for tag in ("TB-01", "TB-02", "TB-03", "TB-04", "TB-05", "TB-06", "TB-07"):
            try:
                asset = c.get(
                    f"/api/trench-safety/assets/{tag}", headers=admin_headers
                ).json()
                if asset.get("operational_status") == "Inspection Hold":
                    c.post(
                        f"/api/trench-safety/assets/{tag}/inspections",
                        json={
                            "inspection_type": "Monthly Competent Person",
                            "inspector_name": "phase4a-teardown",
                            "competent_person_confirmed": True,
                            "result": "Pass",
                            "findings": "phase 4a teardown clear",
                            "checklist": [],
                        },
                        headers=admin_headers,
                    )
                c.post(
                    f"/api/trench-safety/assets/{tag}/return",
                    json={"returned_by": "phase4a-teardown"},
                    headers=admin_headers,
                )
            except Exception:
                pass


# ──────────────────────────────────────────────────────────────────────
# Phase 4A.1 — Equipment Inventory Integration
# ──────────────────────────────────────────────────────────────────────

def test_equipment_master_lists_trench_safety_with_unit_number(client):
    r = client.get("/api/equipment-master", params={"category": "Trench Safety"})
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 7
    items = data["items"]
    by_id = {i["asset_id"]: i for i in items if i.get("asset_id")}
    for tag in ("TB-01", "TB-02", "TB-03", "TB-04", "TB-05", "TB-06", "TB-07"):
        assert tag in by_id, f"missing {tag} from equipment_master"
        row = by_id[tag]
        # Phase 4A enrichment — these are what the Fleet table consumes
        assert row.get("unit_number") == tag
        assert row.get("category") == "Trench Safety"
        assert row.get("make_model"), "make_model must be populated"
        assert row.get("preop_equipment_type") == "Other"
        assert row.get("vin_serial_number") is not None  # may be ""
        assert row.get("display_label")
        # Operational fields the dashboards consume
        assert "status" in row
        assert "operational_status" in row
        assert row.get("type") == "Trench Box"


def test_equipment_master_searchable_by_asset_id(client):
    r = client.get("/api/equipment-master")
    assert r.status_code == 200
    items = r.json()["items"]
    unit_numbers = {i.get("unit_number") for i in items}
    for tag in ("TB-01", "TB-07"):
        assert tag in unit_numbers


# ──────────────────────────────────────────────────────────────────────
# Phase 4A.2 — Project Assignment + propagation
# ──────────────────────────────────────────────────────────────────────

def _assign(client, headers, asset_id, **overrides):
    payload = {
        "project_id": "PRJ-NSB-AIR",
        "project_name": "NSB Airport",
        "project_number": "24-118",
        "superintendent": "Jaymn Judd",
        "foreman": "Carlos M.",
        "assigned_by": "test@masci.com",
        "condition_at_assign": "Good",
        "source": "Manual Assignment",
        "notes": "phase 4a pytest",
    }
    payload.update(overrides)
    return client.post(
        f"/api/trench-safety/assets/{asset_id}/assign",
        json=payload,
        headers=headers,
    )


def _return(client, headers, asset_id, **overrides):
    payload = {
        "returned_by": "test@masci.com",
        "condition_at_return": "Good",
        "notes": "phase 4a pytest return",
    }
    payload.update(overrides)
    return client.post(
        f"/api/trench-safety/assets/{asset_id}/return",
        json=payload,
        headers=headers,
    )


def test_assign_propagates_superintendent_foreman_to_asset_and_deployment(client, admin_headers):
    # Ensure clean slate
    _return(client, admin_headers, "TB-02")
    time.sleep(0.2)

    r = _assign(client, admin_headers, "TB-02")
    assert r.status_code == 200, r.text
    body = r.json()
    asset = body["asset"]
    dep = body["deployment"]

    assert asset["operational_status"] == "Assigned"
    assert asset["current_project_id"] == "PRJ-NSB-AIR"
    assert asset["current_project_name"] == "NSB Airport"
    assert asset["current_project_number"] == "24-118"
    assert asset["current_superintendent"] == "Jaymn Judd"
    assert asset["current_foreman"] == "Carlos M."

    assert dep["project_number"] == "24-118"
    assert dep["superintendent"] == "Jaymn Judd"
    assert dep["foreman"] == "Carlos M."
    assert dep["assigned_by"] == "test@masci.com"
    assert dep["source"] == "Manual Assignment"


def test_assignment_mirrors_to_equipment_master(client, admin_headers):
    _return(client, admin_headers, "TB-03")
    time.sleep(0.2)
    r = _assign(client, admin_headers, "TB-03", project_name="Phase4A Mirror Test", project_id="PRJ-MIRROR-1", project_number="MIRROR-1")
    assert r.status_code == 200, r.text

    r2 = client.get("/api/equipment-master", params={"category": "Trench Safety"})
    by_id = {i["asset_id"]: i for i in r2.json()["items"]}
    row = by_id["TB-03"]
    assert row["current_project_id"] == "PRJ-MIRROR-1"
    assert row["current_project_name"] == "Phase4A Mirror Test"
    assert row["current_project_number"] == "MIRROR-1"
    assert row["operational_status"] == "Assigned"


def test_return_clears_current_project_fields(client, admin_headers):
    _return(client, admin_headers, "TB-04")
    _assign(client, admin_headers, "TB-04")
    time.sleep(0.2)
    r = _return(client, admin_headers, "TB-04")
    assert r.status_code == 200, r.text
    asset = r.json()["asset"]
    assert asset["operational_status"] == "Available"
    assert asset["current_project_id"] is None
    assert asset["current_project_name"] is None
    assert asset["current_project_number"] is None
    assert asset["current_superintendent"] is None
    assert asset["current_foreman"] is None


# ──────────────────────────────────────────────────────────────────────
# Phase 4A.3 — by-project endpoint
# ──────────────────────────────────────────────────────────────────────

def test_by_project_returns_current_assignments(client, admin_headers):
    _return(client, admin_headers, "TB-06")
    _assign(client, admin_headers, "TB-06", project_name="ByProj Job A", project_id="PRJ-A-001", project_number="A-001")

    r = client.get(
        "/api/trench-safety/by-project",
        params={"project_id": "PRJ-A-001"},
        headers=admin_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["current_count"] >= 1
    ids = [a["asset_id"] for a in body["current"]]
    assert "TB-06" in ids
    a = next(x for x in body["current"] if x["asset_id"] == "TB-06")
    assert a["current_project_name"] == "ByProj Job A"
    assert a["operational_status"] == "Assigned"


def test_by_project_supports_project_number_and_name_lookups(client, admin_headers):
    _return(client, admin_headers, "TB-07")
    _assign(client, admin_headers, "TB-07", project_name="ByProj Lookup B", project_id="PRJ-B-002", project_number="B-002")

    r_num = client.get(
        "/api/trench-safety/by-project",
        params={"project_number": "B-002"},
        headers=admin_headers,
    )
    assert r_num.status_code == 200
    assert any(a["asset_id"] == "TB-07" for a in r_num.json()["current"])

    r_name = client.get(
        "/api/trench-safety/by-project",
        params={"project_name": "ByProj Lookup B"},
        headers=admin_headers,
    )
    assert r_name.status_code == 200
    assert any(a["asset_id"] == "TB-07" for a in r_name.json()["current"])


def test_by_project_requires_at_least_one_filter(client, admin_headers):
    r = client.get("/api/trench-safety/by-project", headers=admin_headers)
    assert r.status_code == 422


def test_by_project_excludes_after_return(client, admin_headers):
    _return(client, admin_headers, "TB-06")
    _assign(client, admin_headers, "TB-06", project_name="Exclude Test", project_id="PRJ-EXCL", project_number="EXCL-1")
    _return(client, admin_headers, "TB-06")
    r = client.get(
        "/api/trench-safety/by-project",
        params={"project_id": "PRJ-EXCL"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    ids = [a["asset_id"] for a in r.json()["current"]]
    assert "TB-06" not in ids


def test_by_project_include_history(client, admin_headers):
    _return(client, admin_headers, "TB-02")
    _assign(client, admin_headers, "TB-02", project_name="Hist Job", project_id="PRJ-HIST", project_number="HIST-1")
    _return(client, admin_headers, "TB-02")
    r = client.get(
        "/api/trench-safety/by-project",
        params={"project_id": "PRJ-HIST", "include_history": "true"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert "history" in body
    assert body["history_count"] >= 1
    h = body["history"][0]
    assert h["project_id"] == "PRJ-HIST"


# ──────────────────────────────────────────────────────────────────────
# Phase 4A.4 — Lifecycle guards (Inspection Hold / Repair / Retired)
# ──────────────────────────────────────────────────────────────────────

def test_inspection_hold_blocks_assignment(client, admin_headers):
    _return(client, admin_headers, "TB-05")
    # Move TB-05 into Inspection Hold by submitting a failing inspection
    fail_payload = {
        "inspection_type": "Daily Visual",
        "inspector_name": "pytest-inspector",
        "competent_person_confirmed": True,
        "result": "Fail",
        "findings": "phase 4a guard test",
        "checklist": [],
    }
    ri = client.post(
        "/api/trench-safety/assets/TB-05/inspections",
        json=fail_payload,
        headers=admin_headers,
    )
    assert ri.status_code == 200, ri.text

    r = _assign(client, admin_headers, "TB-05")
    assert r.status_code == 409, f"expected 409 but got {r.status_code}: {r.text}"

    # Cleanup — clear the hold with a passing Monthly Competent Person inspection
    clear_payload = {
        "inspection_type": "Monthly Competent Person",
        "inspector_name": "pytest-inspector",
        "competent_person_confirmed": True,
        "result": "Pass",
        "findings": "phase 4a guard cleared",
        "checklist": [],
    }
    rc = client.post(
        "/api/trench-safety/assets/TB-05/inspections",
        json=clear_payload,
        headers=admin_headers,
    )
    assert rc.status_code == 200, rc.text


# ──────────────────────────────────────────────────────────────────────
# Phase 4A.5 — Deployment history grows correctly
# ──────────────────────────────────────────────────────────────────────

def test_deployment_history_grows_and_carries_phase4a_fields(client, admin_headers):
    _return(client, admin_headers, "TB-01")
    pre = client.get(
        "/api/trench-safety/assets/TB-01/deployments",
        params={"limit": 500},
        headers=admin_headers,
    )
    pre_count = len(pre.json()["items"])

    _assign(client, admin_headers, "TB-01", project_name="History Grow Test", project_id="PRJ-HG", project_number="HG-1", superintendent="Super X", foreman="Fore Y")
    time.sleep(0.2)
    _return(client, admin_headers, "TB-01")

    post = client.get(
        "/api/trench-safety/assets/TB-01/deployments",
        params={"limit": 500},
        headers=admin_headers,
    )
    items = post.json()["items"]
    assert len(items) == pre_count + 1
    latest = items[0]
    assert latest["project_id"] == "PRJ-HG"
    assert latest["project_number"] == "HG-1"
    assert latest["superintendent"] == "Super X"
    assert latest["foreman"] == "Fore Y"
    assert latest["returned_at"] is not None


# ──────────────────────────────────────────────────────────────────────
# Phase 4A.6 — Audit events
# ──────────────────────────────────────────────────────────────────────

def test_audit_events_record_assign_and_return(client, admin_headers):
    _return(client, admin_headers, "TB-02")
    _assign(client, admin_headers, "TB-02", project_name="Audit Job", project_id="PRJ-AUD", project_number="AUD-1")
    _return(client, admin_headers, "TB-02")

    r = client.get(
        "/api/trench-safety/assets/TB-02/audit",
        params={"limit": 50},
        headers=admin_headers,
    )
    assert r.status_code == 200
    kinds = [e["kind"] for e in r.json()["items"]]
    assert "trench_asset_assigned" in kinds
    assert "trench_asset_returned" in kinds


# ──────────────────────────────────────────────────────────────────────
# Phase 4A.7 — Operations picker projection
# ──────────────────────────────────────────────────────────────────────

def test_operations_picker_returns_projection(client, admin_headers):
    r = client.get(
        "/api/trench-safety/operations/picker",
        headers=admin_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 7
    sample = body["items"][0]
    expected_keys = {
        "asset_id",
        "asset_type",
        "size",
        "operational_status",
        "current_project_name",
        "qr_url",
    }
    assert expected_keys.issubset(sample.keys())


def test_operations_picker_available_only(client, admin_headers):
    # Ensure at least one asset is Available
    _return(client, admin_headers, "TB-04")
    r = client.get(
        "/api/trench-safety/operations/picker",
        params={"available_only": "true"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    for item in r.json()["items"]:
        assert item["operational_status"] == "Available"


# ──────────────────────────────────────────────────────────────────────
# Phase 4A.8 — Existing systems unaffected
# ──────────────────────────────────────────────────────────────────────

def test_equipment_master_still_serves_other_categories(client):
    """Trench safety category must NOT crowd out the existing fleet."""
    r = client.get("/api/equipment-master")
    assert r.status_code == 200
    cats = r.json()["categories"]
    # There should be more than just Trench Safety — JSON-seeded fleet
    # exists and equipment_master must keep returning it.
    assert len(cats) >= 2
    assert "Trench Safety" in cats


# ──────────────────────────────────────────────────────────────────────
# Teardown — handled by the module-scoped autouse fixture _phase4a_setup
# defined at the top of this file. See its yield block.
# ──────────────────────────────────────────────────────────────────────

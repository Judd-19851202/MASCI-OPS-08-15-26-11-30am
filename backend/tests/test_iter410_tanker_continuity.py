"""
test_iter410_tanker_continuity.py · Phase 15.1 · Tanker / Liquid Asphalt.

Verifies the 5th haul type (Tanker / Liquid Asphalt) flows through the
SAME DLS as material / equipment-move hauls. No new collection, no new
write endpoint — same `POST /api/dispatch/assignments` (extended
additively with `liquid_product`), same lookups endpoint (extended with
`tanker_sources`, `tanker_destinations`, `liquid_products`).
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
import requests


def _read_kv(path: Path, key: str) -> str:
    try:
        for line in path.read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        return ""
    return ""


URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
API = f"{URL}/api"


def _admin_hdrs():
    r = requests.post(
        f"{API}/admin/login",
        json={"password": "Maddix123!"},
        timeout=15,
    )
    if r.status_code == 200:
        token = r.json().get("token")
        if token:
            return {"X-Admin-Token": token}
    pytest.skip("No admin token in this env.")


# ════════════════════════════════════════════════════════════════════
# 1. HAUL_TYPES now includes Tanker
# ════════════════════════════════════════════════════════════════════
def test_tanker_in_haul_types():
    hdrs = _admin_hdrs()
    r = requests.get(f"{API}/dispatch/driver/assignment-lookups", headers=hdrs, timeout=15)
    j = r.json()
    assert "Tanker / Liquid Asphalt" in j["haul_types"]
    # Order: Material, Equipment Move, Tanker, Spoils, Support
    assert j["haul_types"] == [
        "Material", "Equipment Move", "Tanker / Liquid Asphalt",
        "Spoils / Dump", "Support / Misc",
    ]


# ════════════════════════════════════════════════════════════════════
# 2. Seeded tanker sources / destinations / liquid products
# ════════════════════════════════════════════════════════════════════
def test_seeded_tanker_sources():
    hdrs = _admin_hdrs()
    hdrs["X-Tenant-Id"] = f"iter410-tsrc-{uuid.uuid4().hex[:6]}"
    r = requests.get(f"{API}/dispatch/driver/assignment-lookups", headers=hdrs, timeout=15)
    j = r.json()
    labels = {s["label"] for s in j.get("tanker_sources", [])}
    expected = {
        "MASCI Hot Plant 1", "Terminal", "Asphalt Terminal", "Port",
        "Storage Yard", "Vendor Plant", "Fuel Depot", "Job Site", "Shop",
    }
    assert expected.issubset(labels)
    for s in j["tanker_sources"]:
        if s["label"] in expected:
            assert s["source"] == "seed"


def test_seeded_tanker_destinations():
    hdrs = _admin_hdrs()
    hdrs["X-Tenant-Id"] = f"iter410-tdst-{uuid.uuid4().hex[:6]}"
    r = requests.get(f"{API}/dispatch/driver/assignment-lookups", headers=hdrs, timeout=15)
    j = r.json()
    labels = {d["label"] for d in j.get("tanker_destinations", [])}
    expected = {
        "MASCI Hot Plant 1", "Asphalt Plant", "Other Plant",
        "Storage Tank", "Fuel Tank", "Job Site", "Yard", "Shop", "Terminal",
    }
    assert expected.issubset(labels)


def test_liquid_products_seeded_with_categories():
    hdrs = _admin_hdrs()
    r = requests.get(f"{API}/dispatch/driver/assignment-lookups", headers=hdrs, timeout=15)
    j = r.json()
    products = j.get("liquid_products", [])
    labels = {p["label"] for p in products}
    # Spot-check across categories
    assert "PG 64-22" in labels
    assert "AC-20" in labels
    assert "Polymer Modified Binder" in labels
    assert "CRS-1" in labels
    assert "Tack Oil" in labels
    assert "Diesel" in labels
    assert "DEF" in labels
    categories = {p["category"] for p in products if p.get("source") == "seed"}
    assert {"Asphalt Binders", "Emulsions / Tack", "Fuel / Support"}.issubset(categories)


# ════════════════════════════════════════════════════════════════════
# 3. POST creates a tanker assignment with liquid_product persisted
# ════════════════════════════════════════════════════════════════════
def test_post_tanker_assignment_persists_liquid_product():
    hdrs = _admin_hdrs()
    tenant = f"iter410-tank-post-{uuid.uuid4().hex[:6]}"
    hdrs["X-Tenant-Id"] = tenant
    payload = {
        "truck_id": "T-TANK-1",
        "haul_type": "Tanker / Liquid Asphalt",
        "trailer_id": "tr-tank-1",
        "trailer_label": "TK-09",
        "carrier": "MASCI",
        "source_location": "Asphalt Terminal",
        "destination": "MASCI Hot Plant 1",
        "liquid_product": "PG 64-22",
        "project_number": "PRJ-T-1",
    }
    rc = requests.post(
        f"{API}/dispatch/assignments",
        headers=hdrs, json=payload, timeout=15,
    )
    assert rc.status_code == 200, rc.text
    a = rc.json()["assignment"]
    assert a["haul_type"] == "Tanker / Liquid Asphalt"
    assert a["liquid_product"] == "PG 64-22"
    assert a["source_location"] == "Asphalt Terminal"
    assert a["destination"] == "MASCI Hot Plant 1"
    assert a["trailer_label"] == "TK-09"


# ════════════════════════════════════════════════════════════════════
# 4. Historical merge tags for tanker fields
# ════════════════════════════════════════════════════════════════════
def test_historical_tanker_values_merge_with_history_flag():
    hdrs = _admin_hdrs()
    tenant = f"iter410-tank-hist-{uuid.uuid4().hex[:6]}"
    hdrs["X-Tenant-Id"] = tenant
    rc = requests.post(
        f"{API}/dispatch/assignments",
        headers=hdrs,
        json={
            "truck_id": "T-TANK-H",
            "haul_type": "Tanker / Liquid Asphalt",
            "source_location": "Refinery North",
            "destination": "Plant Delta",
            "liquid_product": "Custom Binder Blend X",
        },
        timeout=15,
    )
    assert rc.status_code == 200

    r = requests.get(
        f"{API}/dispatch/driver/assignment-lookups",
        headers=hdrs, timeout=15,
    )
    j = r.json()
    tanker_sources = {(s["label"], s["source"]) for s in j["tanker_sources"]}
    tanker_dests = {(d["label"], d["source"]) for d in j["tanker_destinations"]}
    liquid_products = {(p["label"], p.get("source")) for p in j["liquid_products"]}
    assert ("Refinery North", "history") in tanker_sources
    assert ("Plant Delta", "history") in tanker_dests
    assert ("Custom Binder Blend X", "history") in liquid_products


# ════════════════════════════════════════════════════════════════════
# 5. Tanker assignment flows through full DLS lifecycle → cycle doc
# ════════════════════════════════════════════════════════════════════
def test_tanker_cycle_carries_liquid_product():
    hdrs = _admin_hdrs()
    tenant = f"iter410-tank-cyc-{uuid.uuid4().hex[:6]}"
    hdrs["X-Tenant-Id"] = tenant

    rc = requests.post(
        f"{API}/dispatch/assignments",
        headers=hdrs,
        json={
            "truck_id": "T-TANK-CYC",
            "haul_type": "Tanker / Liquid Asphalt",
            "source_location": "Asphalt Terminal",
            "destination": "MASCI Hot Plant 1",
            "liquid_product": "PG 76-22",
            "project_number": "PRJ-T-CYC",
        },
        timeout=15,
    )
    assert rc.status_code == 200
    aid = rc.json()["assignment"]["id"]

    for st in ["ENROUTE_TO_LOAD", "AT_LOAD", "LOADING", "ENROUTE_TO_JOB",
               "ARRIVED_JOB", "DUMPING", "COMPLETE"]:
        rt = requests.post(
            f"{API}/dispatch/assignments/{aid}/transition",
            headers=hdrs, json={"to_state": st}, timeout=15,
        )
        assert rt.status_code == 200, rt.text

    rc2 = requests.get(
        f"{API}/dispatch/haul-cycles?project_number=PRJ-T-CYC",
        headers=hdrs, timeout=15,
    )
    cycles = rc2.json().get("cycles") or []
    assert len(cycles) == 1
    cycle = cycles[0]
    assert cycle["haul_type"] == "Tanker / Liquid Asphalt"
    assert cycle["liquid_product"] == "PG 76-22"
    assert cycle["source_location"] == "Asphalt Terminal"
    assert cycle["destination"] == "MASCI Hot Plant 1"


# ════════════════════════════════════════════════════════════════════
# 6. Backward compat — Material POST without liquid_product still works
# ════════════════════════════════════════════════════════════════════
def test_material_post_still_works_without_liquid_product():
    hdrs = _admin_hdrs()
    tenant = f"iter410-mat-{uuid.uuid4().hex[:6]}"
    hdrs["X-Tenant-Id"] = tenant
    rc = requests.post(
        f"{API}/dispatch/assignments",
        headers=hdrs,
        json={
            "truck_id": "T-BCK",
            "material": "Hot Mix Asphalt",
            "source_location": "MASCI Hot Plant 1",
            "destination": "Job Site",
        },
        timeout=15,
    )
    assert rc.status_code == 200
    a = rc.json()["assignment"]
    assert a["haul_type"] == "Material"
    assert a["liquid_product"] == ""


# ════════════════════════════════════════════════════════════════════
# 7. Restraint · no internal field leakage in new arrays
# ════════════════════════════════════════════════════════════════════
def test_no_internal_field_leakage_in_tanker_arrays():
    hdrs = _admin_hdrs()
    r = requests.get(f"{API}/dispatch/driver/assignment-lookups", headers=hdrs, timeout=15)
    j = r.json()
    for cat in ("tanker_sources", "tanker_destinations", "liquid_products"):
        for row in j.get(cat, []):
            assert "_id" not in row
            for k in row.keys():
                assert not k.startswith("_"), f"Internal leakage in {cat}: {k}"

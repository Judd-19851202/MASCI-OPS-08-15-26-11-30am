"""
test_iter408_assignment_lookups_expanded.py · Phase 14.1 + 14.2.

Covers the expanded assignment-lookups contract plus the new
haul_type / equipment / pickup / dropoff fields on the
POST /api/dispatch/assignments endpoint.

Phase 14.1 contract:
  • Endpoint returns seeded sources/destinations/pickup/dropoff
    and material catalog even on a brand-new tenant.
  • Drivers list returns CDL-qualified employees from the master
    (no q≥2 privacy gate — dispatch is authenticated).
  • Master lists (trucks, trailers, equipment, carriers) populated
    from equipment_master.
  • Historical recents merge in with `source: "history"` flag.

Phase 14.2 contract:
  • haul_types ∈ {Material, Equipment Move, Spoils / Dump, Support / Misc}.
  • equipment list (non-truck/non-trailer categories) returned.
  • POST /api/dispatch/assignments accepts haul_type + equipment_id +
    equipment_label + pickup_location + dropoff_location and persists
    them on the created assignment doc (additive, backward compatible).
"""
from __future__ import annotations

import os
import urllib.error
import urllib.request
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


def _anon_status(path: str) -> int:
    req = urllib.request.Request(
        f"{API}{path}", method="GET",
        headers={"User-Agent": "Mozilla/5.0 (iter408 anon test)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


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
    pytest.skip("No admin token available in this env.")


# ════════════════════════════════════════════════════════════════════
# Auth
# ════════════════════════════════════════════════════════════════════
def test_lookups_still_require_auth():
    assert _anon_status("/dispatch/driver/assignment-lookups") == 401


# ════════════════════════════════════════════════════════════════════
# Phase 14.1 · Seeded operational vocabulary always present
# ════════════════════════════════════════════════════════════════════
def test_seeded_sources_present_on_empty_tenant():
    hdrs = _admin_hdrs()
    hdrs["X-Tenant-Id"] = f"iter408-empty-{uuid.uuid4().hex[:6]}"
    r = requests.get(f"{API}/dispatch/driver/assignment-lookups", headers=hdrs, timeout=15)
    j = r.json()
    src_labels = {s["label"] for s in j.get("sources", [])}
    assert {"MASCI Hot Plant 1", "415 Yard", "Port", "Job Site", "Shop"}.issubset(src_labels)
    for s in j["sources"]:
        if s["label"] in {"MASCI Hot Plant 1", "415 Yard", "Port", "Job Site", "Shop"}:
            assert s["source"] == "seed"


def test_seeded_destinations_include_dump():
    hdrs = _admin_hdrs()
    hdrs["X-Tenant-Id"] = f"iter408-dest-{uuid.uuid4().hex[:6]}"
    r = requests.get(f"{API}/dispatch/driver/assignment-lookups", headers=hdrs, timeout=15)
    j = r.json()
    dest_labels = {d["label"] for d in j.get("destinations", [])}
    assert "Dump" in dest_labels
    assert {"MASCI Hot Plant 1", "415 Yard", "Job Site", "Shop"}.issubset(dest_labels)


def test_seeded_pickup_and_dropoff_locations():
    hdrs = _admin_hdrs()
    r = requests.get(f"{API}/dispatch/driver/assignment-lookups", headers=hdrs, timeout=15)
    j = r.json()
    pu = {p["label"] for p in j.get("pickup_locations", [])}
    do = {d["label"] for d in j.get("dropoff_locations", [])}
    assert {"MASCI Hot Plant 1", "415 Yard", "Shop", "Other Yard", "Vendor", "Rental Yard"}.issubset(pu)
    assert "Dump" in do
    assert {"Shop", "Vendor", "Rental Yard"}.issubset(do)


def test_material_catalog_seeded_with_categories():
    hdrs = _admin_hdrs()
    r = requests.get(f"{API}/dispatch/driver/assignment-lookups", headers=hdrs, timeout=15)
    j = r.json()
    mats = j.get("materials", [])
    labels = {m["label"] for m in mats}
    # Spot-check across categories
    assert "Hot Mix Asphalt" in labels
    assert "SP-9.5" in labels
    assert "Limerock" in labels
    assert "Common Fill" in labels
    assert "Broken Concrete" in labels
    assert "RCP Pipe" in labels
    categories = {m["category"] for m in mats if m.get("source") == "seed"}
    assert {"Asphalt / Plant", "Aggregate / Base", "Earthwork / Soils"}.issubset(categories)


def test_haul_types_returned():
    hdrs = _admin_hdrs()
    r = requests.get(f"{API}/dispatch/driver/assignment-lookups", headers=hdrs, timeout=15)
    j = r.json()
    # iter410 · Tanker added as 3rd entry between Equipment Move and Spoils.
    assert j.get("haul_types") == [
        "Material",
        "Equipment Move",
        "Tanker / Liquid Asphalt",
        "Spoils / Dump",
        "Support / Misc",
    ]


# ════════════════════════════════════════════════════════════════════
# Phase 14.1 · Drivers list (CDL-qualified, no q gate)
# ════════════════════════════════════════════════════════════════════
def test_drivers_returned_without_q_for_dispatch():
    """No more privacy gate — dispatch is authenticated; CDL-qualified
    employees show up immediately."""
    hdrs = _admin_hdrs()
    r = requests.get(f"{API}/dispatch/driver/assignment-lookups", headers=hdrs, timeout=15)
    j = r.json()
    drivers = j.get("drivers", [])
    # Driver list is allowed to be empty in a brand-new DB; verify
    # SHAPE when populated.
    for d in drivers:
        assert set(d.keys()) >= {"name", "employee_id"}
        # iter408 enriched fields
        assert "cdl" in d
        assert "approved" in d


# ════════════════════════════════════════════════════════════════════
# Phase 14.1 · Equipment master surfaces equipment + carriers
# ════════════════════════════════════════════════════════════════════
def test_equipment_list_separate_from_trucks_and_trailers():
    hdrs = _admin_hdrs()
    r = requests.get(f"{API}/dispatch/driver/assignment-lookups", headers=hdrs, timeout=15)
    j = r.json()
    truck_pks = {t["unit_pk"] for t in j["trucks"] if t.get("unit_pk")}
    trailer_pks = {t["unit_pk"] for t in j["trailers"] if t.get("unit_pk")}
    equipment_pks = {e["unit_pk"] for e in j.get("equipment", []) if e.get("unit_pk")}
    assert truck_pks.isdisjoint(equipment_pks)
    assert trailer_pks.isdisjoint(equipment_pks)


def test_equipment_examples_for_temporary_add():
    hdrs = _admin_hdrs()
    r = requests.get(f"{API}/dispatch/driver/assignment-lookups", headers=hdrs, timeout=15)
    j = r.json()
    examples = j.get("equipment_examples", [])
    assert "Excavator" in examples
    assert "Dozer" in examples
    assert "Paver" in examples


def test_carriers_masci_first():
    hdrs = _admin_hdrs()
    r = requests.get(f"{API}/dispatch/driver/assignment-lookups", headers=hdrs, timeout=15)
    j = r.json()
    carriers = [c["name"] for c in j.get("carriers", [])]
    assert "MASCI" in carriers
    assert carriers[0] == "MASCI"


# ════════════════════════════════════════════════════════════════════
# Phase 14.1 · Historical merge flag
# ════════════════════════════════════════════════════════════════════
def test_history_label_after_post():
    hdrs = _admin_hdrs()
    tenant = f"iter408-hist-{uuid.uuid4().hex[:6]}"
    hdrs["X-Tenant-Id"] = tenant
    # Post an assignment with a NEW source / destination / material that
    # is not in the seed list — confirm they come back tagged history.
    rc = requests.post(
        f"{API}/dispatch/assignments",
        headers=hdrs,
        json={
            "truck_id": "T-IT408-H",
            "source_location": "Pit 27",
            "destination": "Lot 99",
            "material": "RX-Mix 408",
        },
        timeout=15,
    )
    assert rc.status_code == 200

    r = requests.get(f"{API}/dispatch/driver/assignment-lookups", headers=hdrs, timeout=15)
    j = r.json()
    sources = {(s["label"], s["source"]) for s in j["sources"]}
    destinations = {(d["label"], d["source"]) for d in j["destinations"]}
    materials = {(m["label"], m.get("source")) for m in j["materials"]}
    assert ("Pit 27", "history") in sources
    assert ("Lot 99", "history") in destinations
    assert ("RX-Mix 408", "history") in materials


# ════════════════════════════════════════════════════════════════════
# Phase 14.2 · Haul Type continuity persisted on assignment doc
# ════════════════════════════════════════════════════════════════════
def test_equipment_move_persists_new_fields():
    hdrs = _admin_hdrs()
    tenant = f"iter408-em-{uuid.uuid4().hex[:6]}"
    hdrs["X-Tenant-Id"] = tenant
    rc = requests.post(
        f"{API}/dispatch/assignments",
        headers=hdrs,
        json={
            "truck_id": "T-EM-1",
            "haul_type": "Equipment Move",
            "equipment_id": "eq-unit-pk-7",
            "equipment_label": "EX-12",
            "pickup_location": "415 Yard",
            "dropoff_location": "Job Site",
            "carrier": "MASCI",
            "trailer_id": "tr-unit-pk-3",
            "trailer_label": "LB-04",
        },
        timeout=15,
    )
    assert rc.status_code == 200, rc.text
    a = rc.json()["assignment"]
    assert a["haul_type"] == "Equipment Move"
    assert a["equipment_id"] == "eq-unit-pk-7"
    assert a["equipment_label"] == "EX-12"
    assert a["pickup_location"] == "415 Yard"
    assert a["dropoff_location"] == "Job Site"
    assert a["carrier"] == "MASCI"
    assert a["trailer_id"] == "tr-unit-pk-3"
    assert a["trailer_label"] == "LB-04"


def test_material_assignment_defaults_haul_type():
    hdrs = _admin_hdrs()
    tenant = f"iter408-mat-{uuid.uuid4().hex[:6]}"
    hdrs["X-Tenant-Id"] = tenant
    # Legacy-shaped POST (no haul_type field) — must default to Material.
    rc = requests.post(
        f"{API}/dispatch/assignments",
        headers=hdrs,
        json={
            "truck_id": "T-LEG-1",
            "material": "Hot Mix Asphalt",
            "source_location": "MASCI Hot Plant 1",
            "destination": "Job Site",
        },
        timeout=15,
    )
    assert rc.status_code == 200
    a = rc.json()["assignment"]
    assert a["haul_type"] == "Material"
    assert a["material"] == "Hot Mix Asphalt"


def test_pickup_dropoff_history_for_equipment_moves():
    hdrs = _admin_hdrs()
    tenant = f"iter408-em-hist-{uuid.uuid4().hex[:6]}"
    hdrs["X-Tenant-Id"] = tenant
    # Post a custom pickup/dropoff — confirm it surfaces in pickup_locations history.
    rc = requests.post(
        f"{API}/dispatch/assignments",
        headers=hdrs,
        json={
            "truck_id": "T-EM-2",
            "haul_type": "Equipment Move",
            "pickup_location": "South Storage Lot",
            "dropoff_location": "North Project Site",
        },
        timeout=15,
    )
    assert rc.status_code == 200

    r = requests.get(f"{API}/dispatch/driver/assignment-lookups", headers=hdrs, timeout=15)
    j = r.json()
    pu = {(p["label"], p["source"]) for p in j["pickup_locations"]}
    do = {(d["label"], d["source"]) for d in j["dropoff_locations"]}
    assert ("South Storage Lot", "history") in pu
    assert ("North Project Site", "history") in do


# ════════════════════════════════════════════════════════════════════
# Restraint · No internal field leakage
# ════════════════════════════════════════════════════════════════════
def test_no_internal_fields_leaked():
    hdrs = _admin_hdrs()
    r = requests.get(f"{API}/dispatch/driver/assignment-lookups", headers=hdrs, timeout=15)
    j = r.json()
    for cat in ("drivers", "trucks", "trailers", "equipment", "carriers",
                "projects", "sources", "destinations", "pickup_locations",
                "dropoff_locations", "materials"):
        for row in j.get(cat, []):
            assert "_id" not in row
            for k in row.keys():
                assert not k.startswith("_"), f"Internal field leaked in {cat}: {k}"

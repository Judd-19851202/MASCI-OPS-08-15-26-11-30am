"""Track 13.31B-D5.2 · Canonical Pre-Op + DVIR inspection template expansion tests.

Validates:
  • Registry covers every directive-required canonical asset type with
    operator-grade sections.
  • Pre-Op surface (Excavator/Dozer/Roller/Paver/etc.) stamps
    template_status="available" + template_key + template_source.
  • DVIR surface (Dump/Service/Fuel/Water/Pickup/Trailer etc.) does same.
  • Service Truck stays Service Truck — does NOT resolve to Haul Truck.
  • Unknown asset_type → honest missing_template.
  • `/api/asset-spine/inspection-templates*` endpoints serve the registry.
  • Missing-template backlog is ordered by active-fleet impact.
  • Legacy equipment_type preserved.
"""
import os
import uuid as _uuid

import httpx
import pytest

REACT_APP_BACKEND_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=", 1)[-1].splitlines()[0].strip()
)
API = REACT_APP_BACKEND_URL.rstrip("/") + "/api"


def _admin():
    r = httpx.post(f"{API}/admin/login", json={"password": "MASCI1982!"}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code}")
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_tok():
    return _admin()


def _seed_verified(admin_tok, asset_class: str, asset_type: str, prefix: str = "D52"):
    h = {"X-Admin-Token": admin_tok, "Content-Type": "application/json"}
    suffix = _uuid.uuid4().hex[:8]
    body = {
        "asset_number": f"{prefix}-{asset_type.replace(' ', '')[:8].upper()}-{suffix}",
        "asset_name": f"D5.2 test {asset_type}",
        "asset_class": asset_class,
        "asset_type": asset_type,
        "taxonomy_verified": True,
        "taxonomy_source": "manual",
    }
    r = httpx.post(f"{API}/asset-spine/assets", json=body, headers=h, timeout=30)
    assert r.status_code in (200, 201), r.text
    return body["asset_number"]


def _submit_preop(unit_number: str, legacy_type: str = "Other") -> str:
    body = {
        "project_name": "D5.2", "project_number": "20-07", "location": "Field",
        "inspection_date": "2026-06-13", "inspection_time": "08:00",
        "operator_name": "D5.2 Tester",
        "equipment_type": legacy_type, "equipment_unit": unit_number,
        "checklist": {}, "pass_count": 1, "fail_count": 0,
    }
    r = httpx.post(f"{API}/equipment-inspections", json=body, timeout=30)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _submit_dvir(truck_unit: str) -> str:
    body = {
        "kind": "dvir", "driver_name": "D5.2 Driver",
        "inspection_date": "2026-06-13", "inspection_time": "08:00",
        "truck_unit_number": truck_unit,
        "truck_checklist": {}, "trailers": [],
    }
    r = httpx.post(f"{API}/fleet/inspections", json=body, timeout=30)
    assert r.status_code in (200, 201), r.text
    j = r.json()
    return j.get("inspection_id") or j.get("id")


def _read(insp_id: str, tok: str):
    r = httpx.get(f"{API}/equipment-inspections/{insp_id}", headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 200
    return r.json()


# ── 1 · Pre-Op templates exist for every directive-named asset type ──


@pytest.mark.parametrize("asset_class, asset_type", [
    ("Heavy Equipment", "Paver"),
    ("Heavy Equipment", "Roller"),
    ("Heavy Equipment", "Dozer"),
    ("Heavy Equipment", "Motor Grader"),
    ("Heavy Equipment", "Backhoe"),
    ("Heavy Equipment", "Compactor"),
    ("Heavy Equipment", "Skid Steer"),
    ("Heavy Equipment", "Loader"),
    ("Heavy Equipment", "Excavator"),
    ("Support Equipment", "Pump"),
    ("Support Equipment", "Generator"),
    ("Support Equipment", "Light Tower"),
    ("Support Equipment", "Air Compressor"),
    ("Support Equipment", "Welder"),
])
def test_preop_template_available_for_required_types(admin_tok, asset_class, asset_type):
    unit = _seed_verified(admin_tok, asset_class, asset_type)
    insp = _submit_preop(unit)
    row = _read(insp, admin_tok)
    assert row["asset_type"] == asset_type
    assert row["template_status"] == "available", row
    assert row["template_key"], row
    assert row["template_source"] == "canonical_asset_type"


# ── 2 · DVIR templates exist for every directive-named truck type ────


@pytest.mark.parametrize("asset_type", [
    "Dump Truck", "Service Truck", "Fuel Truck", "Lube Truck",
    "Water Truck", "Pickup Truck", "Flatbed Truck", "Semi Tractor",
])
def test_dvir_template_available_for_required_truck_types(admin_tok, asset_type):
    unit = _seed_verified(admin_tok, "Truck", asset_type)
    insp = _submit_dvir(unit)
    row = _read(insp, admin_tok)
    assert row["asset_type"] == asset_type
    assert row["template_status"] == "available", row
    assert row["template_key"], row


# ── 3 · Service Truck does NOT silently become Haul Truck ────────────


def test_service_truck_stays_service_truck_in_dvir(admin_tok):
    unit = _seed_verified(admin_tok, "Truck", "Service Truck")
    insp = _submit_dvir(unit)
    row = _read(insp, admin_tok)
    assert row["asset_type"] == "Service Truck"
    assert row["asset_type"] != "Haul Truck"
    assert row["template_key"] == "service_truck"


# ── 4 · Trailer DVIR carries per-trailer canonical template too ──────


def test_trailer_dvir_carries_canonical(admin_tok):
    truck = _seed_verified(admin_tok, "Truck", "Dump Truck")
    trailer = _seed_verified(admin_tok, "Trailer", "Lowboy Trailer", prefix="D52T")
    body = {
        "kind": "dvir", "driver_name": "D5.2 Driver",
        "inspection_date": "2026-06-13", "inspection_time": "08:00",
        "truck_unit_number": truck, "truck_checklist": {},
        "trailers": [{"trailer_unit_number": trailer, "trailer_type": "", "checklist": {}}],
    }
    r = httpx.post(f"{API}/fleet/inspections", json=body, timeout=30)
    assert r.status_code in (200, 201)
    insp = r.json().get("inspection_id") or r.json().get("id")
    row = _read(insp, admin_tok)
    tc = row.get("trailer_classifications") or []
    assert len(tc) == 1
    assert tc[0]["asset_type"] == "Lowboy Trailer"
    assert tc[0]["template_status"] == "available"


# ── 5 · Unknown asset_type → honest missing_template ─────────────────


def test_unknown_asset_type_stamps_missing_template(admin_tok):
    # Use a unit that isn't in equipment_master
    insp = _submit_preop(f"UNKNOWN-{_uuid.uuid4().hex[:6]}")
    row = _read(insp, admin_tok)
    assert row["classification_status"] == "unmatched"
    assert row["template_status"] == "missing_template"
    assert row["template_key"] in (None, "")
    assert row["template_source"] in (None, "")


# ── 6 · Registry endpoints serve the templates ──────────────────────


def test_registry_list_endpoint(admin_tok):
    h = {"X-Admin-Token": admin_tok}
    r = httpx.get(f"{API}/asset-spine/inspection-templates", headers=h, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["count"] >= 40
    types = {t["asset_type"] for t in d["items"]}
    for required in ("Paver", "Roller", "Dozer", "Motor Grader", "Backhoe",
                     "Dump Truck", "Service Truck", "Fuel Truck", "Lube Truck",
                     "Water Truck", "Pump", "Generator", "Light Tower",
                     "Lowboy Trailer", "Equipment Trailer"):
        assert required in types, f"registry missing {required!r}"


def test_registry_filter_by_surface(admin_tok):
    h = {"X-Admin-Token": admin_tok}
    r_preop = httpx.get(f"{API}/asset-spine/inspection-templates?applies_to=pre_op", headers=h, timeout=30)
    r_dvir = httpx.get(f"{API}/asset-spine/inspection-templates?applies_to=dvir", headers=h, timeout=30)
    assert r_preop.status_code == 200 and r_dvir.status_code == 200
    p_types = {t["asset_type"] for t in r_preop.json()["items"]}
    d_types = {t["asset_type"] for t in r_dvir.json()["items"]}
    assert "Excavator" in p_types and "Excavator" not in d_types
    assert "Dump Truck" in d_types and "Dump Truck" not in p_types


def test_registry_by_asset_type_returns_sections(admin_tok):
    h = {"X-Admin-Token": admin_tok}
    r = httpx.get(f"{API}/asset-spine/inspection-templates/by-asset-type/Paver", headers=h, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["template_status"] == "available"
    assert d["template_key"] == "paver"
    labels = [s["label"] for s in d["sections"]]
    # Operator-grade section labels from the registry
    assert any("Hopper" in l for l in labels)
    assert any("Screed" in l for l in labels)
    assert any("Conveyor" in l for l in labels)


def test_registry_by_asset_type_missing_is_honest(admin_tok):
    h = {"X-Admin-Token": admin_tok}
    r = httpx.get(f"{API}/asset-spine/inspection-templates/by-asset-type/NopeNotARealType", headers=h, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["template_status"] == "missing_template"
    assert d["sections"] == []


# ── 7 · Missing-template backlog endpoint ────────────────────────────


def test_missing_backlog_endpoint_requires_admin():
    r = httpx.get(f"{API}/asset-spine/inspection-templates/missing-backlog", timeout=30)
    assert r.status_code in (401, 403)


def test_missing_backlog_shape(admin_tok):
    h = {"X-Admin-Token": admin_tok}
    r = httpx.get(f"{API}/asset-spine/inspection-templates/missing-backlog", headers=h, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "scanned" in d
    assert "missing_template_types" in d
    assert "items" in d
    if d["items"]:
        # Items ordered desc by count
        counts = [it["count"] for it in d["items"]]
        assert counts == sorted(counts, reverse=True)


# ── 8 · Legacy equipment_type preserved across all writes ────────────


def test_legacy_equipment_type_preserved_with_new_templates(admin_tok):
    unit = _seed_verified(admin_tok, "Heavy Equipment", "Paver")
    insp = _submit_preop(unit, legacy_type="Other")
    row = _read(insp, admin_tok)
    assert row["asset_type"] == "Paver"
    assert row["template_status"] == "available"
    assert row["legacy_equipment_type"] == "Other"
    assert row["equipment_type"] == "Other"


# ── 9 · "Other" not used for known asset types ───────────────────────


def test_known_asset_not_resolved_as_other(admin_tok):
    for at in ("Paver", "Roller", "Dozer", "Motor Grader", "Backhoe"):
        unit = _seed_verified(admin_tok, "Heavy Equipment", at)
        insp = _submit_preop(unit, legacy_type="Other")
        row = _read(insp, admin_tok)
        assert row["asset_type"] == at
        assert row["asset_type"] != "Other"
        assert row["template_status"] == "available"


# ── 10 · Pure-python registry · no new collection ──────────────────


def test_no_new_collection_in_registry():
    src = open("/app/backend/services/inspection_templates.py").read()
    assert "create_collection" not in src
    assert "db." not in src
    assert "insert_one" not in src
    assert "update_one" not in src

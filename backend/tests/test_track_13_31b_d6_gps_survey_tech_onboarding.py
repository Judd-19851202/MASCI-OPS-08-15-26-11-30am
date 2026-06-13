"""Track 13.31B-D6 · Asset Spine finalization · GPS/Survey/Tech onboarding tests.

Verifies:
  * The canonical asset taxonomy now contains GPS / Survey / Technology /
    Communication / Drone / Utility-Locating asset types previously absent.
  * The required-documents resolver returns calibration certificates for
    GPS/Survey/Locating tools and warranty/purchase/photo for Technology.
  * Asset Admin can create new GPS / Tech assets through the existing
    asset endpoint — no new collection, no new route.
  * Upload + render still works for the new types.
  * Smart Pre-Op / DVIR / Document / PM regression remains green
    (covered by the cross-file regression tests already on disk).
"""
import io
import os
import uuid

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


def _seed(tok: str, asset_class: str, asset_type: str) -> str:
    h = {"X-Admin-Token": tok, "Content-Type": "application/json"}
    body = {
        "asset_number": f"D6-{uuid.uuid4().hex[:8]}",
        "asset_name": f"D6 {asset_type}",
        "asset_class": asset_class,
        "asset_type": asset_type,
        "taxonomy_verified": True,
        "taxonomy_source": "manual",
    }
    r = httpx.post(f"{API}/asset-spine/assets", json=body, headers=h, timeout=30)
    assert r.status_code in (200, 201), r.text
    j = r.json()
    return j.get("id") or j.get("asset_id")


# ── 1 · Taxonomy now contains GPS / Survey / Tech amendment items ──────


@pytest.mark.parametrize(
    "asset_class,asset_type",
    [
        # GPS / Machine Control
        ("GPS / Machine Control", "GPS Rover"),
        ("GPS / Machine Control", "GPS Base"),
        ("GPS / Machine Control", "GNSS Receiver"),
        ("GPS / Machine Control", "Topcon Hiper XR"),
        ("GPS / Machine Control", "Topcon Hiper VR"),
        ("GPS / Machine Control", "Machine Control Receiver"),
        ("GPS / Machine Control", "Base Radio"),
        ("GPS / Machine Control", "Rover Radio"),
        # Survey · instruments + lasers
        ("Survey Equipment", "Total Station"),
        ("Survey Equipment", "Robotic Total Station"),
        ("Survey Equipment", "Data Collector"),
        ("Survey Equipment", "Laser Level"),
        ("Survey Equipment", "Rotating Laser"),
        ("Survey Equipment", "Pipe Laser"),
        ("Survey Equipment", "Theodolite"),
        # Survey · utility locating
        ("Survey Equipment", "Utility Locator"),
        ("Survey Equipment", "Ground Penetrating Radar"),
        ("Survey Equipment", "Pipe Locator"),
        ("Survey Equipment", "Cable Locator"),
        # Technology · devices
        ("Technology Equipment", "iPad"),
        ("Technology Equipment", "Tablet"),
        ("Technology Equipment", "Laptop"),
        ("Technology Equipment", "Phone"),
        ("Technology Equipment", "Printer"),
        # Technology · drones
        ("Technology Equipment", "Drone"),
        ("Technology Equipment", "Drone Controller"),
        # Communication
        ("Technology Equipment", "Handheld Radio"),
        ("Technology Equipment", "Satellite Phone"),
        ("Technology Equipment", "Mobile Radio"),
    ],
)
def test_canonical_asset_type_creatable(admin_tok, asset_class, asset_type):
    asset_id = _seed(admin_tok, asset_class, asset_type)
    g = httpx.get(f"{API}/asset-spine/assets/{asset_id}",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert g.status_code == 200
    body = g.json()
    assert body.get("asset_class") == asset_class
    assert body.get("asset_type") == asset_type
    assert body.get("taxonomy_verified") is True


# ── 2 · Required-docs resolver: GPS / Survey / Locating → calibration ──


def test_required_docs_gps_rover_has_calibration(admin_tok):
    asset_id = _seed(admin_tok, "GPS / Machine Control", "GPS Rover")
    r = httpx.get(f"{API}/asset-spine/assets/{asset_id}/required-documents",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert r.status_code == 200
    types = {d["document_type"] for d in r.json()["required_documents"]}
    assert "calibration_certificate" in types
    assert "operator_manual" in types
    assert "asset_photo" in types


def test_required_docs_utility_locator_has_calibration(admin_tok):
    asset_id = _seed(admin_tok, "Survey Equipment", "Utility Locator")
    r = httpx.get(f"{API}/asset-spine/assets/{asset_id}/required-documents",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    types = {d["document_type"] for d in r.json()["required_documents"]}
    assert "calibration_certificate" in types


def test_required_docs_total_station_has_calibration(admin_tok):
    asset_id = _seed(admin_tok, "Survey Equipment", "Robotic Total Station")
    r = httpx.get(f"{API}/asset-spine/assets/{asset_id}/required-documents",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    types = {d["document_type"] for d in r.json()["required_documents"]}
    assert "calibration_certificate" in types


# ── 3 · Required-docs resolver: Technology → warranty + purchase + photo ──


def test_required_docs_ipad(admin_tok):
    asset_id = _seed(admin_tok, "Technology Equipment", "iPad")
    r = httpx.get(f"{API}/asset-spine/assets/{asset_id}/required-documents",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    types = {d["document_type"] for d in r.json()["required_documents"]}
    assert "warranty" in types
    assert "purchase_document" in types
    assert "asset_photo" in types


def test_required_docs_drone(admin_tok):
    asset_id = _seed(admin_tok, "Technology Equipment", "Drone")
    r = httpx.get(f"{API}/asset-spine/assets/{asset_id}/required-documents",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    types = {d["document_type"] for d in r.json()["required_documents"]}
    assert "warranty" in types
    assert "asset_photo" in types


def test_required_docs_handheld_radio(admin_tok):
    asset_id = _seed(admin_tok, "Technology Equipment", "Handheld Radio")
    r = httpx.get(f"{API}/asset-spine/assets/{asset_id}/required-documents",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    types = {d["document_type"] for d in r.json()["required_documents"]}
    assert "warranty" in types


# ── 4 · Calibration upload + mirror onto equipment_master.calibration_expiration ──


def test_calibration_upload_mirrors_expiration(admin_tok):
    asset_id = _seed(admin_tok, "Survey Equipment", "Robotic Total Station")
    files = {"file": ("cal.pdf", io.BytesIO(b"%PDF-1.4\ntest\n%%EOF"), "application/pdf")}
    data = {"document_type": "calibration_certificate",
            "expiration_date": "2027-03-15"}
    r = httpx.post(
        f"{API}/asset-spine/assets/{asset_id}/documents/upload",
        files=files, data=data, headers={"X-Admin-Token": admin_tok}, timeout=30,
    )
    assert r.status_code in (200, 201), r.text
    g = httpx.get(f"{API}/asset-spine/assets/{asset_id}",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert g.json().get("calibration_expiration") == "2027-03-15"


# ── 5 · Behavior matrix surfaces calibration_required for GPS/Survey ──


def test_behavior_matrix_calibration_flags(admin_tok):
    r = httpx.get(f"{API}/asset-spine/taxonomy",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    behaviors = r.json()["behaviors"]
    for t in ("GPS Rover", "Topcon Hiper XR", "Robotic Total Station",
              "Pipe Laser", "Utility Locator", "Ground Penetrating Radar"):
        assert behaviors.get(t, {}).get("calibration_required") is True, (
            f"calibration_required absent for {t}: {behaviors.get(t)}"
        )


# ── 6 · Behavior matrix surfaces employee_lifecycle_managed for Tech/Comm ──


def test_behavior_matrix_lifecycle_flags(admin_tok):
    r = httpx.get(f"{API}/asset-spine/taxonomy",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    behaviors = r.json()["behaviors"]
    for t in ("iPad", "Laptop", "Handheld Radio", "Drone"):
        assert behaviors.get(t, {}).get("employee_lifecycle_managed") is True


# ── 7 · CSV inventory export includes a GPS/Survey/Tech row ──────────


def test_csv_inventory_includes_new_types(admin_tok):
    _seed(admin_tok, "GPS / Machine Control", "Topcon Hiper XR")
    _seed(admin_tok, "Technology Equipment", "iPad")
    r = httpx.get(f"{API}/asset-spine/exports/assets.csv",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert r.status_code == 200
    text = r.text
    assert "Topcon Hiper XR" in text
    assert "iPad" in text


# ── 8 · No new collection / no new spine introduced ──────────────────


def test_no_new_collection_introduced():
    src = open("/app/backend/services/asset_taxonomy.py").read()
    req_src = open("/app/backend/services/required_documents.py").read()
    for name in ("technology_assets", "survey_assets", "gps_assets",
                 "asset_documents_collection", "new_asset_spine",
                 "create_collection"):
        assert name not in src, f"banned token in taxonomy: {name}"
        assert name not in req_src, f"banned token in required_documents: {name}"


# ── 9 · D5.4 + D3D4 regression integrity — taxonomy still self-consistent ──


def test_taxonomy_self_consistency(admin_tok):
    r = httpx.get(f"{API}/asset-spine/taxonomy",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    body = r.json()
    classes = body["asset_classes"]
    types_by_class = body["asset_types_by_class"]
    behaviors = body["behaviors"]
    # Every class has at least one type
    for cls in classes:
        assert types_by_class.get(cls), f"empty class {cls}"
    # Every behavior entry corresponds to a real type
    flat_types = {t for ts in types_by_class.values() for t in ts}
    for t in behaviors:
        assert t in flat_types, f"orphan behavior key {t}"

"""Track 13.31B-D0D1 · Taxonomy + Asset Admin Spine Foundation tests."""
import os
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


# ── 1 · Canonical taxonomy enums exposed ──────────────────────────────


def test_taxonomy_enums_endpoint(admin_tok):
    r = httpx.get(f"{API}/asset-spine/taxonomy", headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["version"] == "1.0.0"
    assert "Heavy Equipment" in d["asset_classes"]
    assert "Truck" in d["asset_classes"]
    assert "Trailer" in d["asset_classes"]
    assert "Technology Equipment" in d["asset_classes"]
    assert "Excavator" in d["asset_types_by_class"]["Heavy Equipment"]
    assert "Motor Grader" in d["asset_types_by_class"]["Heavy Equipment"]
    assert "iPad" in d["asset_types_by_class"]["Technology Equipment"]
    # Behaviors are derived per asset_type
    assert d["behaviors"]["Excavator"]["requires_pm"] is True
    assert d["behaviors"]["Excavator"]["requires_preop"] is True
    assert d["behaviors"]["iPad"]["requires_pm"] is False
    assert d["behaviors"]["iPad"]["employee_lifecycle_managed"] is True
    assert d["behaviors"]["Dump Truck"]["dot_required"] is True
    assert d["behaviors"]["Pickup Truck"]["dot_required"] is False


# ── 2 · classify-legacy verified path ─────────────────────────────────


def test_classify_legacy_verified_single_source(admin_tok):
    h = {"X-Admin-Token": admin_tok}
    r = httpx.get(f"{API}/asset-spine/taxonomy/classify-legacy",
                  params={"category": "Excavators"}, headers=h, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["asset_class"] == "Heavy Equipment"
    assert d["asset_type"] == "Excavator"
    assert d["taxonomy_verified"] is True
    assert d["taxonomy_source"] == "legacy_mapped"


def test_classify_legacy_road_plate_type_override(admin_tok):
    """legacy `type` field is the most specific source"""
    r = httpx.get(f"{API}/asset-spine/taxonomy/classify-legacy",
                  params={"type": "Road Plate"},
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    d = r.json()
    assert d["asset_class"] == "Trench Safety"
    assert d["asset_type"] == "Road Plate"
    assert d["taxonomy_verified"] is True


# ── 3 · Unknown taxonomy → needs_review (not fabricated) ─────────────


def test_classify_legacy_unknown_returns_needs_review(admin_tok):
    r = httpx.get(f"{API}/asset-spine/taxonomy/classify-legacy",
                  params={"category": "TotallyMadeUpThingX"},
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    d = r.json()
    assert d["asset_class"] is None
    assert d["asset_type"] is None
    assert d["taxonomy_verified"] is False
    assert d["taxonomy_source"] == "needs_review"


# ── 4 · Conflict detection ────────────────────────────────────────────


def test_classify_legacy_conflict_detected(admin_tok):
    r = httpx.get(f"{API}/asset-spine/taxonomy/classify-legacy",
                  params={"category": "Excavators",
                          "preop_equipment_type": "Motor Grader"},
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    d = r.json()
    assert d["taxonomy_verified"] is False
    assert d["taxonomy_source"] == "needs_review"
    assert "legacy_field_conflict" in (d.get("taxonomy_review_reason") or "")


# ── 5 · review-needed queue auth + shape ──────────────────────────────


def test_review_needed_queue_admin_only():
    # No token → 401
    r = httpx.get(f"{API}/asset-spine/taxonomy/review-needed", timeout=30)
    assert r.status_code in (401, 403)


def test_review_needed_queue_returns_real_legacy_rows(admin_tok):
    r = httpx.get(f"{API}/asset-spine/taxonomy/review-needed?limit=10",
                  headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert "count" in d and "items" in d
    if d["count"] > 0:
        row = d["items"][0]
        for key in ("id", "unit_number", "display_label",
                    "legacy_category", "current_taxonomy_verified", "suggested"):
            assert key in row, f"missing key: {key}"
        # Suggested taxonomy never fabricates
        sug = row["suggested"]
        assert sug["taxonomy_source"] in {"legacy_mapped", "needs_review", "manual"}


# ── 6 · Dry-run crosswalk is read-only ────────────────────────────────


def test_apply_legacy_crosswalk_dry_run_does_not_persist(admin_tok):
    # Snapshot before
    h = {"X-Admin-Token": admin_tok}
    before = httpx.get(f"{API}/asset-spine/taxonomy/review-needed?limit=1",
                       headers=h, timeout=30).json()["count"]
    r = httpx.post(f"{API}/asset-spine/taxonomy/apply-legacy-crosswalk",
                   params={"dry_run": "true", "limit": 50}, headers=h, timeout=60)
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True
    assert d["dry_run"] is True
    assert d["scanned"] > 0
    # Snapshot after — review-needed count must be unchanged (dry run)
    after = httpx.get(f"{API}/asset-spine/taxonomy/review-needed?limit=1",
                      headers=h, timeout=30).json()["count"]
    assert before == after, "dry_run unexpectedly persisted"


# ── 7 · AssetCreate accepts new admin fields ──────────────────────────


def test_asset_create_accepts_admin_fields(admin_tok):
    import uuid as _uuid
    h = {"X-Admin-Token": admin_tok, "Content-Type": "application/json"}
    suffix = _uuid.uuid4().hex[:8]
    body = {
        "asset_number": f"PMTEST-AA-{suffix}",
        "asset_name": "Track 13.31B test asset",
        "asset_class": "Heavy Equipment",
        "asset_type": "Excavator",
        "lifecycle_status": "pending_delivery",
        "registration_number": "ABC-123",
        "registration_state": "NJ",
        "registration_expiration": "2027-01-01",
        "insurance_carrier": "Test Insurance Co",
        "insurance_policy_number": "POL-XYZ",
        "insurance_expiration": "2027-01-01",
        "title_status": "owned",
        "warranty_expiration": "2028-01-01",
        "division": "MASCI_GC_NJ",
        "region": "north",
        "supervisor_id": "EMP-001",
        "gps_device_id": "MOT-DEVICE-X",
        "normalized_company": "MASCI_GC",
        "motive_vehicle_id": "motive-test-X",
        "taxonomy_verified": True,
        "taxonomy_source": "manual",
    }
    r = httpx.post(f"{API}/asset-spine/assets", json=body, headers=h, timeout=30)
    assert r.status_code in (200, 201), r.text
    asset = r.json()
    # Reading back the asset must reflect the new admin fields
    aid = asset.get("id") or asset.get("asset_id") or asset.get("asset_number")
    if aid:
        r2 = httpx.get(f"{API}/asset-spine/assets/{aid}", headers=h, timeout=30)
        if r2.status_code == 200:
            body2 = r2.json()
            # Pick the canonical asset payload regardless of envelope shape
            payload = body2.get("asset") or body2.get("data") or body2
            for k in ("asset_class", "lifecycle_status", "registration_number",
                      "insurance_carrier", "motive_vehicle_id"):
                assert k in str(payload), f"new field {k!r} missing in read-back"


# ── 8 · equipment_master remains the canonical collection ─────────────


def test_equipment_master_remains_canonical():
    # services/asset_spine.py line 9 is the contract: equipment_master IS the spine.
    src = open("/app/backend/services/asset_spine.py").read()
    assert "equipment_master" in src
    assert "Single source-of-truth collection: `equipment_master`" in src


# ── 9 · No new collection · no duplicate spine ────────────────────────


def test_no_new_collections_introduced():
    """13.31B-D0D1 must not add new collections. All work is additive on
    equipment_master + new service module."""
    import os
    for path in (
        "/app/backend/services/asset_taxonomy.py",
        "/app/backend/routes/asset_spine.py",
        "/app/backend/services/asset_spine.py",
    ):
        assert os.path.exists(path)
    # Forbidden patterns — anything that would create a new asset collection
    src = open("/app/backend/services/asset_taxonomy.py").read()
    assert "insert_one" not in src
    assert "create_collection" not in src
    assert "db." not in src  # taxonomy module is pure-python; never touches DB


# ── 10 · No accounting / cost / PO leakage ────────────────────────────


def test_no_cost_or_accounting_fields_exposed(admin_tok):
    h = {"X-Admin-Token": admin_tok}
    blob = repr(httpx.get(f"{API}/asset-spine/taxonomy", headers=h, timeout=30).json()).lower()
    for forbidden in ("cost", "price", "tax", "invoice", "margin",
                      "pay_app", "accounting", "erp", "po_number"):
        assert forbidden not in blob, f"forbidden field surfaced: {forbidden}"


# ── 11 · Behavior matrix matches operator expectations ───────────────


def test_behavior_matrix_truck_vs_ipad():
    from services.asset_taxonomy import behavior_for
    truck = behavior_for("Dump Truck")
    ipad = behavior_for("iPad")
    assert truck["requires_registration"] is True
    assert truck["requires_insurance"] is True
    assert truck["dot_required"] is True
    assert truck["appears_on_map"] is True
    assert ipad["requires_registration"] is False
    assert ipad["requires_pm"] is False
    assert ipad["employee_lifecycle_managed"] is True
    assert ipad["document_vault_required"] is True


# ── 12 · Company normalization ────────────────────────────────────────


def test_company_normalization():
    from services.asset_taxonomy import normalize_company
    assert normalize_company("MGC") == ("MASCI_GC", False)
    assert normalize_company("Masci") == ("MASCI_GC", False)
    assert normalize_company("masci corp") == ("MASCI_GC", False)
    assert normalize_company("FERIA") == ("FERIA", False)
    # "?" routes to default but flags review-needed
    assert normalize_company("?") == ("MASCI_GC", True)
    # Unknown returns None + review-needed
    assert normalize_company("SomeOtherCo") == (None, True)
    assert normalize_company("") == (None, True)
    assert normalize_company(None) == (None, True)

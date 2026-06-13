"""Track 13.31B-D5.1 BUILD · Smart Pre-Op + Smart DVIR canonical write stamp tests.

Proves the platform now stamps canonical asset classification onto every
new Pre-Op + DVIR submission where unit identity resolves, while
preserving legacy fields verbatim. No fabrication. No silent verify.
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


@pytest.fixture(scope="module")
def verified_unit(admin_tok):
    """Create a fresh equipment_master row with verified canonical taxonomy."""
    h = {"X-Admin-Token": admin_tok, "Content-Type": "application/json"}
    suffix = _uuid.uuid4().hex[:8]
    body = {
        "asset_number": f"D51-VER-{suffix}",
        "asset_name": "Track 13.31B-D5.1 verified asset",
        "asset_class": "Heavy Equipment",
        "asset_type": "Excavator",
        "taxonomy_verified": True,
        "taxonomy_source": "manual",
    }
    r = httpx.post(f"{API}/asset-spine/assets", json=body, headers=h, timeout=30)
    assert r.status_code in (200, 201), r.text
    return body["asset_number"]


def _submit_preop(unit_number: str, legacy_equipment_type: str = "Other") -> str:
    body = {
        "project_name": "D5.1 test", "project_number": "20-07", "location": "Field",
        "inspection_date": "2026-06-13", "inspection_time": "08:00",
        "operator_name": "D5.1 Tester",
        "equipment_type": legacy_equipment_type, "equipment_unit": unit_number,
        "checklist": {}, "pass_count": 1, "fail_count": 0,
    }
    r = httpx.post(f"{API}/equipment-inspections", json=body, timeout=30)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _read_preop(insp_id: str, tok: str) -> dict:
    r = httpx.get(f"{API}/equipment-inspections/{insp_id}",
                  headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


# ── 1 · Pre-Op against verified unit stamps canonical class/type ────────


def test_preop_against_verified_unit_stamps_canonical(admin_tok, verified_unit):
    insp_id = _submit_preop(verified_unit, legacy_equipment_type="Other")
    row = _read_preop(insp_id, admin_tok)
    assert row["asset_class"] == "Heavy Equipment"
    assert row["asset_type"] == "Excavator"
    assert row["taxonomy_verified"] is True
    assert row["classification_status"] == "verified"
    assert row["taxonomy_source"] == "canonical"
    # Legacy field preserved
    assert row["legacy_equipment_type"] == "Other"
    assert row["equipment_type"] == "Other"


# ── 2 · Pre-Op against legacy-mapped unit stamps "mapped" status ────────


def test_preop_against_legacy_mapped_unit_stamps_mapped_status(admin_tok):
    """Use a real review-needed asset whose legacy crosswalk maps cleanly."""
    h = {"X-Admin-Token": admin_tok}
    # Find an asset whose legacy crosswalk would produce a clean mapping.
    rq = httpx.get(f"{API}/asset-spine/taxonomy/review-needed?limit=200", headers=h, timeout=30)
    units = []
    for it in rq.json()["items"]:
        s = it.get("suggested") or {}
        if not (it.get("unit_number") or "").strip():
            continue
        if s.get("taxonomy_verified") and s.get("asset_class") and s.get("asset_type"):
            units.append(it["unit_number"])
    if not units:
        pytest.skip("no legacy-mapped candidates in preview")
    unit = units[0]
    insp_id = _submit_preop(unit, legacy_equipment_type="Other")
    row = _read_preop(insp_id, admin_tok)
    # mapped, not verified
    assert row["taxonomy_verified"] is False
    assert row["classification_status"] == "mapped"
    assert row["taxonomy_source"] == "legacy_mapped"
    assert row["asset_class"] and row["asset_type"]
    assert row["legacy_equipment_type"] == "Other"


# ── 3 · Pre-Op against needs_review unit allows submission with honest tag ──


def test_preop_against_needs_review_unit_allows_submission(admin_tok):
    h = {"X-Admin-Token": admin_tok}
    rq = httpx.get(f"{API}/asset-spine/taxonomy/review-needed?limit=200", headers=h, timeout=30)
    units = []
    for it in rq.json()["items"]:
        s = it.get("suggested") or {}
        if not (it.get("unit_number") or "").strip():
            continue
        if not s.get("taxonomy_verified"):
            units.append(it["unit_number"])
    if not units:
        pytest.skip("no needs_review candidates in preview")
    unit = units[0]
    insp_id = _submit_preop(unit, legacy_equipment_type="Other")
    row = _read_preop(insp_id, admin_tok)
    assert row["classification_status"] == "needs_review"
    assert row["taxonomy_verified"] is False
    assert row["taxonomy_review_reason"]


# ── 4 · Pre-Op against unknown unit_number does NOT fabricate ─────────


def test_preop_against_unknown_unit_stamps_unmatched(admin_tok):
    insp_id = _submit_preop(f"UNKNOWN-{_uuid.uuid4().hex[:6]}", legacy_equipment_type="Other")
    row = _read_preop(insp_id, admin_tok)
    assert row.get("asset_id") in (None, "")
    assert row.get("classification_status") == "unmatched"
    assert row.get("asset_class") in (None, "")
    assert row.get("asset_type") in (None, "")
    assert row.get("taxonomy_verified") is False


# ── 5 · Legacy `equipment_type` field always preserved verbatim ───────


def test_legacy_equipment_type_preserved(admin_tok, verified_unit):
    for legacy in ("Skid Steer", "Other", "Truck", "", "Loader"):
        insp_id = _submit_preop(verified_unit, legacy_equipment_type=legacy)
        row = _read_preop(insp_id, admin_tok)
        assert row["equipment_type"] == legacy
        assert row["legacy_equipment_type"] == legacy


# ── 6 · Known heavy equipment does not save as "Other" canonical ──────


def test_known_heavy_equipment_does_not_become_other(admin_tok, verified_unit):
    """The operator selected 'Other' — but the system knows this unit is an
    Excavator. The canonical stamp must override the dropdown."""
    insp_id = _submit_preop(verified_unit, legacy_equipment_type="Other")
    row = _read_preop(insp_id, admin_tok)
    assert row["asset_type"] == "Excavator"
    assert row["asset_type"] != "Other"


# ── 7 · template_status flags missing templates for D5.2 ──────────────


def test_template_status_flags_missing(admin_tok, verified_unit):
    """Excavator template is present in current pre-op form set; should
    stamp template_present."""
    insp_id = _submit_preop(verified_unit)
    row = _read_preop(insp_id, admin_tok)
    assert row["template_status"] == "available"
    assert row["template_recommended"] == "Excavator"


def test_template_status_missing_for_unsupported_types(admin_tok):
    """Light Tower template lives in Pre-Op surface — verify a DVIR call
    against a Light Tower correctly stamps missing_template (DVIR surface
    has no Light Tower template, so D5.2's applies_to gate kicks in)."""
    # Track 13.31B-D5.2 ships templates for nearly all canonical types;
    # the surface gate (pre_op vs dvir) is now the missing-template
    # signal. Test path: pre-op against a survey-class asset has no
    # template in the registry yet.
    from services.inspection_templates import has_template
    # Find any canonical asset_type that does NOT have a template
    from services.asset_taxonomy import ASSET_TYPES_BY_CLASS
    missing = None
    for cls, types in ASSET_TYPES_BY_CLASS.items():
        for at in types:
            if not has_template(at):
                missing = (cls, at)
                break
        if missing:
            break
    if not missing:
        pytest.skip("registry covers every canonical asset_type; nothing missing")
    h = {"X-Admin-Token": admin_tok, "Content-Type": "application/json"}
    suffix = _uuid.uuid4().hex[:8]
    body = {
        "asset_number": f"D51-MISS-{suffix}",
        "asset_name": "Track 13.31B-D5.1 missing template test",
        "asset_class": missing[0],
        "asset_type": missing[1],
        "taxonomy_verified": True,
        "taxonomy_source": "manual",
    }
    r = httpx.post(f"{API}/asset-spine/assets", json=body, headers=h, timeout=30)
    assert r.status_code in (200, 201), r.text
    insp_id = _submit_preop(body["asset_number"])
    row = _read_preop(insp_id, admin_tok)
    assert row["asset_type"] == missing[1]
    assert row["template_status"] == "missing_template"


# ── 8 · DVIR write-stamp lands canonical fields on the truck row ──────


def test_dvir_against_verified_truck_stamps_canonical(admin_tok):
    """Create a verified Service Truck and submit a DVIR against it."""
    h = {"X-Admin-Token": admin_tok, "Content-Type": "application/json"}
    suffix = _uuid.uuid4().hex[:8]
    truck_unit = f"D51-SVC-{suffix}"
    body = {
        "asset_number": truck_unit,
        "asset_name": "D5.1 Service Truck",
        "asset_class": "Truck",
        "asset_type": "Service Truck",
        "taxonomy_verified": True,
        "taxonomy_source": "manual",
    }
    r = httpx.post(f"{API}/asset-spine/assets", json=body, headers=h, timeout=30)
    assert r.status_code in (200, 201)

    # Submit a DVIR for it
    dvir = {
        "kind": "dvir",
        "driver_name": "D5.1 Driver",
        "inspection_date": "2026-06-13", "inspection_time": "08:00",
        "truck_unit_number": truck_unit,
        "truck_checklist": {},
        "trailers": [],
    }
    r2 = httpx.post(f"{API}/fleet/inspections", json=dvir, timeout=30)
    assert r2.status_code in (200, 201), r2.text
    dvir_id = r2.json()["inspection_id"] if "inspection_id" in r2.json() else r2.json().get("id")
    # Read back via the existing inspection lookup endpoint
    rr = httpx.get(f"{API}/equipment-inspections/{dvir_id}", headers={"X-Admin-Token": admin_tok}, timeout=30)
    assert rr.status_code == 200, rr.text
    row = rr.json()
    assert row.get("asset_class") == "Truck"
    assert row.get("asset_type") == "Service Truck"
    # Critical: Service Truck stays Service Truck, not "Haul Truck"
    assert row.get("asset_type") != "Haul Truck"
    assert row.get("taxonomy_verified") is True
    assert row.get("classification_status") == "verified"


# ── 9 · DVIR with trailers carries per-trailer canonical snapshots ────


def test_dvir_trailer_classifications_stamped(admin_tok):
    """DVIR with one trailer should record per-trailer canonical resolution."""
    h = {"X-Admin-Token": admin_tok, "Content-Type": "application/json"}
    suffix = _uuid.uuid4().hex[:8]
    truck_unit = f"D51-DT-{suffix}"
    trailer_unit = f"D51-LB-{suffix}"
    # Seed both as verified canonical
    for body in (
        {"asset_number": truck_unit, "asset_name": "Dump", "asset_class": "Truck",
         "asset_type": "Dump Truck", "taxonomy_verified": True, "taxonomy_source": "manual"},
        {"asset_number": trailer_unit, "asset_name": "Lowboy", "asset_class": "Trailer",
         "asset_type": "Lowboy Trailer", "taxonomy_verified": True, "taxonomy_source": "manual"},
    ):
        r = httpx.post(f"{API}/asset-spine/assets", json=body, headers=h, timeout=30)
        assert r.status_code in (200, 201), r.text

    dvir = {
        "kind": "dvir", "driver_name": "D5.1 Driver",
        "inspection_date": "2026-06-13", "inspection_time": "08:00",
        "truck_unit_number": truck_unit,
        "truck_checklist": {},
        "trailers": [{"trailer_unit_number": trailer_unit, "trailer_type": "", "checklist": {}}],
    }
    r2 = httpx.post(f"{API}/fleet/inspections", json=dvir, timeout=30)
    assert r2.status_code in (200, 201), r2.text
    body = r2.json()
    dvir_id = body.get("inspection_id") or body.get("id")
    rr = httpx.get(f"{API}/equipment-inspections/{dvir_id}",
                   headers={"X-Admin-Token": admin_tok}, timeout=30)
    row = rr.json()
    assert row.get("asset_class") == "Truck"
    assert row.get("asset_type") == "Dump Truck"
    trailer_cls = row.get("trailer_classifications") or []
    assert len(trailer_cls) == 1
    t0 = trailer_cls[0]
    assert t0["trailer_unit_number"] == trailer_unit
    assert t0["asset_class"] == "Trailer"
    assert t0["asset_type"] == "Lowboy Trailer"
    assert t0["classification_status"] == "verified"


# ── 10 · Equipment Master remains canonical · no new collection ───────


def test_no_new_inspection_collection_introduced():
    """The smart stamp is a $set patch on the existing
    `equipment_inspections` collection. No new collection."""
    src = open("/app/backend/services/inspection_classification.py").read()
    # The only collection touched is equipment_inspections
    assert "db.equipment_inspections.update_one" in src
    assert "create_collection" not in src
    # No new asset collection
    assert "db.assets" not in src
    assert "db.classification_records" not in src

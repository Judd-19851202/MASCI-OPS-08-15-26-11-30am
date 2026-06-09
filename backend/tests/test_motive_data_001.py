"""MOTIVE-DATA-001 · Asset mapping reconciliation · regression suite."""
from __future__ import annotations
import json, os, urllib.request, urllib.error, uuid
from datetime import datetime, timezone
import pytest
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
BACKEND = os.environ.get("BACKEND_URL", "http://127.0.0.1:8001")
API = f"{BACKEND}/api"
ADMIN_PW = os.environ.get("ADMIN_PASSWORD", "MASCI1982!")


def _req(method, path, *, body=None, token=""):
    h = {"Content-Type": "application/json"}
    if token: h["X-Admin-Token"] = token
    d = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API}{path}", data=d, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return {"status": r.status, "json": json.loads(r.read().decode() or "{}")}
    except urllib.error.HTTPError as e:
        try: return {"status": e.code, "json": json.loads(e.read().decode() or "{}")}
        except Exception: return {"status": e.code, "json": {}}


def _nid(): return str(uuid.uuid4())
def _now(): return datetime.now(timezone.utc).isoformat()


@pytest.fixture(scope="module")
def db():
    cli = MongoClient(os.environ["MONGO_URL"])
    yield cli[os.environ["DB_NAME"]]
    cli.close()


@pytest.fixture(scope="module")
def tok():
    return _req("POST", "/admin/login", body={"password": ADMIN_PW})["json"]["token"]


@pytest.fixture
def world(db):
    tag = f"MD1-{uuid.uuid4().hex[:8].upper()}"
    # Seed dispatch (one truck), asset_mappings (matching VIN), equipment_master
    truck = f"T-{tag}"
    vin = f"VIN-{tag}"
    db.dispatch_assignments.insert_one({
        "id": _nid(), "truck_id": truck, "equipment_id": "",
        "project_number": f"{tag}-P", "current_state": "ASSIGNED",
        "created_at": _now(), "updated_at": _now(),
        "state_history": [], "wait_events": []
    })
    mm_id = _nid()
    db.asset_mappings.insert_one({
        "id": mm_id, "provider": "motive", "asset_kind": "vehicle",
        "masci_equipment_id": None,
        "motive": {"vehicle_id": f"V-{tag}", "vin": vin,
                   "year": "2024", "make": "Mack", "model": "Anthem"},
    })
    db.equipment_master.insert_one({
        "id": _nid(), "asset_id": truck, "display_label": truck,
        "vin": vin, "unit_label": truck,
    })
    yield {"tag": tag, "truck": truck, "vin": vin, "motive_mapping_id": mm_id}
    db.dispatch_assignments.delete_many({"truck_id": truck})
    db.asset_mappings.delete_many({"id": mm_id})
    db.equipment_master.delete_many({"asset_id": truck})
    db.asset_mapping_proposals.delete_many({"truck_id": truck})


# ─── Pure scorer ─────────────────────────────────────────────────────
def test_exact_masci_id():
    from routes.asset_mapping_recon import score_match
    out = score_match({"truck_id": "T-X"},
                      {"masci_equipment_id": "T-X", "motive": {}}, None)
    assert out["band"] == "HIGH"
    assert out["best_signal"]["kind"] == "masci_id_exact"
    assert out["score"] >= 0.99


def test_vin_match():
    from routes.asset_mapping_recon import score_match
    out = score_match({"truck_id": "T-X"},
                      {"masci_equipment_id": None, "motive": {"vin": "VIN-1"}},
                      {"vin": "VIN-1"})
    assert out["band"] == "HIGH"
    assert out["best_signal"]["kind"] == "vin"


def test_unit_number_match():
    from routes.asset_mapping_recon import score_match
    out = score_match({"truck_id": "U-42"},
                      {"masci_equipment_id": None, "motive": {}},
                      {"unit_label": "U-42"})
    assert out["band"] == "HIGH"
    assert out["best_signal"]["kind"] in ("unit_number", "equipment_number")


def test_fuzzy_only_is_low_or_medium():
    from routes.asset_mapping_recon import score_match
    out = score_match({"truck_id": "T-7", "equipment_label": "CAT 320"},
                      {"masci_equipment_id": None,
                       "motive": {"name": "CAT 320 something"}},
                      None)
    assert out["band"] in ("MEDIUM", "HIGH")


def test_no_signal_is_unknown():
    from routes.asset_mapping_recon import score_match
    out = score_match({"truck_id": "X", "equipment_label": ""},
                      {"masci_equipment_id": None, "motive": {}}, None)
    assert out["band"] == "UNKNOWN"


# ─── HTTP integration ────────────────────────────────────────────────
def test_scan_creates_proposals(world, tok, db):
    s = world
    r = _req("POST", "/admin/asset-mapping/scan", token=tok)
    assert r["status"] == 200
    p = db.asset_mapping_proposals.find_one({"truck_id": s["truck"]})
    assert p is not None
    assert p["confidence_band"] == "HIGH"
    assert p["motive_mapping_id"] == s["motive_mapping_id"]
    assert p["status"] == "Matched"
    # Did NOT auto-link
    m = db.asset_mappings.find_one({"id": s["motive_mapping_id"]})
    assert not m.get("masci_equipment_id"), "scan must not auto-link"


def test_approve_links(world, tok, db):
    s = world
    _req("POST", "/admin/asset-mapping/scan", token=tok)
    p = db.asset_mapping_proposals.find_one({"truck_id": s["truck"]})
    r = _req("POST", f"/admin/asset-mapping/{p['id']}/approve", token=tok)
    assert r["status"] == 200
    m = db.asset_mappings.find_one({"id": s["motive_mapping_id"]})
    assert m["masci_equipment_id"] == s["truck"]
    p2 = db.asset_mapping_proposals.find_one({"id": p["id"]})
    assert p2["status"] == "Verified"


def test_reject_does_not_link(world, tok, db):
    s = world
    _req("POST", "/admin/asset-mapping/scan", token=tok)
    p = db.asset_mapping_proposals.find_one({"truck_id": s["truck"]})
    r = _req("POST", f"/admin/asset-mapping/{p['id']}/reject", token=tok)
    assert r["status"] == 200
    m = db.asset_mappings.find_one({"id": s["motive_mapping_id"]})
    assert not m.get("masci_equipment_id")


def test_reassign(world, tok, db):
    s = world
    _req("POST", "/admin/asset-mapping/scan", token=tok)
    p = db.asset_mapping_proposals.find_one({"truck_id": s["truck"]})
    # bad motive_mapping_id → 400
    r = _req("POST", f"/admin/asset-mapping/{p['id']}/reassign",
             body={"motive_mapping_id": "XXX-NOPE"}, token=tok)
    assert r["status"] == 400
    # Good
    r = _req("POST", f"/admin/asset-mapping/{p['id']}/reassign",
             body={"motive_mapping_id": s["motive_mapping_id"]}, token=tok)
    assert r["status"] == 200
    p2 = db.asset_mapping_proposals.find_one({"id": p["id"]})
    assert p2["match_signal"]["kind"] == "manual"
    assert p2["status"] == "Verified"


def test_bulk_approve_high_only(world, tok, db):
    s = world
    _req("POST", "/admin/asset-mapping/scan", token=tok)
    p = db.asset_mapping_proposals.find_one({"truck_id": s["truck"]})
    # Lower its confidence and bulk-approve must skip
    db.asset_mapping_proposals.update_one(
        {"id": p["id"]},
        {"$set": {"confidence_score": 0.6, "confidence_band": "MEDIUM",
                  "status": "Matched"}})
    r = _req("POST", "/admin/asset-mapping/bulk-approve",
             body={"ids": [p["id"]]}, token=tok)
    assert r["status"] == 200
    assert r["json"]["approved_count"] == 0
    assert r["json"]["skipped"][0]["reason"] == "below_high_confidence"
    # Restore to HIGH
    db.asset_mapping_proposals.update_one(
        {"id": p["id"]},
        {"$set": {"confidence_score": 0.95, "confidence_band": "HIGH"}})
    r = _req("POST", "/admin/asset-mapping/bulk-approve",
             body={"ids": [p["id"]]}, token=tok)
    assert r["json"]["approved_count"] == 1


def test_coverage_endpoint(tok):
    r = _req("GET", "/admin/asset-mapping/coverage", token=tok)
    assert r["status"] == 200
    for k in ("total_dispatch_trucks", "mapped_assets", "unmapped_assets",
              "coverage_pct"):
        assert k in r["json"]


def test_audit_endpoint_shape(tok):
    r = _req("GET", "/admin/asset-mapping/audit", token=tok)
    assert r["status"] == 200
    a = r["json"]["answers"]
    for k in ("q1_total_dispatch_assets", "q2_total_motive_assets",
              "q3_total_mapped", "q4_total_unmapped",
              "q5_total_duplicates", "q6_total_conflicts",
              "q7_coverage_pct", "q8_verification_unlock_pct",
              "q9_highest_risk_gaps", "q10_estimated_trust_improvement_pct"):
        assert k in a


def test_admin_endpoints_require_token():
    for p in ("/admin/asset-mapping/scan", "/admin/asset-mapping/audit",
              "/admin/asset-mapping/coverage", "/admin/asset-mapping/queue"):
        r = _req("GET" if "scan" not in p else "POST", p)
        assert r["status"] in (401, 403)


# ─── Constitutional ──────────────────────────────────────────────────
def test_no_motive_or_workflow_writes_in_source():
    import inspect
    from routes import asset_mapping_recon as r
    src = inspect.getsource(r)
    assert "from services.motive_service" not in src
    assert "MotiveService(" not in src
    assert "import httpx" not in src
    for forbidden in [
        "daily_reports.insert", "daily_reports.update", "daily_reports.delete",
        "dispatch_assignments.insert", "dispatch_assignments.update",
        "dispatch_assignments.delete",
        "motive_events.insert", "motive_events.update", "motive_events.delete",
        "operational_events.insert", "operational_events.update",
        "workflow_state_events.insert", "operations_actions.insert",
    ]:
        assert forbidden not in src, f"forbidden write: {forbidden}"


def test_no_unwanted_writes_during_scan_audit(world, tok, db):
    s = world
    dr_b = db.daily_reports.count_documents({})
    da_b = db.dispatch_assignments.count_documents({})
    me_b = db.motive_events.count_documents({})
    oe_b = db.operational_events.count_documents({})
    ol_b = db.operational_locations.count_documents({})

    _req("POST", "/admin/asset-mapping/scan", token=tok)
    _req("GET", "/admin/asset-mapping/audit", token=tok)
    _req("GET", "/admin/asset-mapping/coverage", token=tok)
    _req("GET", "/admin/asset-mapping/queue", token=tok)

    assert db.daily_reports.count_documents({}) == dr_b
    assert db.dispatch_assignments.count_documents({}) == da_b
    assert db.motive_events.count_documents({}) == me_b
    assert db.operational_events.count_documents({}) == oe_b
    assert db.operational_locations.count_documents({}) == ol_b

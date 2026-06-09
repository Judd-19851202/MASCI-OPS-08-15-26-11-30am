"""
VER-1 · Operational Verification Layer · regression suite.
"""
from __future__ import annotations
import json
import os
import urllib.request
import urllib.error
import uuid
from datetime import datetime, timezone

import pytest
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

BACKEND = os.environ.get("BACKEND_URL", "http://127.0.0.1:8001")
API = f"{BACKEND}/api"
ADMIN_PW = os.environ.get("ADMIN_PASSWORD", "MASCI1982!")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]


def _req(method, path, *, body=None, token=""):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Admin-Token"] = token
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return {"status": r.status, "json": json.loads(r.read().decode() or "{}")}
    except urllib.error.HTTPError as e:
        try:
            return {"status": e.code, "json": json.loads(e.read().decode() or "{}")}
        except Exception:
            return {"status": e.code, "json": {}}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _nid() -> str:
    return str(uuid.uuid4())


@pytest.fixture(scope="module")
def db():
    cli = MongoClient(MONGO_URL)
    yield cli[DB_NAME]
    cli.close()


@pytest.fixture(scope="module")
def admin_token():
    r = _req("POST", "/admin/login", body={"password": ADMIN_PW})
    assert r["status"] == 200, r
    return r["json"]["token"]


# ─── Pure-function tests ─────────────────────────────────────────────
def test_compute_trust_state_confirmed():
    from routes.verification import compute_trust_state
    s, r = compute_trust_state(True, True, False)
    assert s == "CONFIRMED"


def test_compute_trust_state_pending():
    from routes.verification import compute_trust_state
    s, r = compute_trust_state(True, False, False)
    assert s == "PENDING_CONFIRMATION"


def test_compute_trust_state_mismatch():
    from routes.verification import compute_trust_state
    s, r = compute_trust_state(True, False, True)
    assert s == "MISMATCH"


def test_compute_trust_state_quiet():
    from routes.verification import compute_trust_state
    s, r = compute_trust_state(False, False, False)
    assert s == "QUIET"


def test_compute_trust_state_observed_no_expectation_is_quiet():
    """No expectation but evidence present should stay QUIET (don't
    promote 'stuff happening' into Confirmed-against-nothing)."""
    from routes.verification import compute_trust_state
    s, r = compute_trust_state(False, True, False)
    assert s == "QUIET"


def test_trust_states_canonical():
    from routes.verification import TRUST_STATES
    assert TRUST_STATES == {"CONFIRMED", "PENDING_CONFIRMATION",
                             "MISMATCH", "QUIET"}


# ─── HTTP-level integration ──────────────────────────────────────────
@pytest.fixture
def ver_world(db):
    """Seed: a Verified JOB op_location for project VER1-PRJ. An asset
    mapping for truck T-VER1 (vehicle 9001). 3 dispatch_assignments:
    one CONFIRMED scenario, one PENDING, one MISMATCH. And one
    operational_event row per CONFIRMED + MISMATCH actor."""
    tag = f"VER1-{uuid.uuid4().hex[:8].upper()}"
    proj = f"{tag}-P"
    other = f"{tag}-OTHER"
    gid = f"VER1-GF-{tag}"
    other_gid = f"VER1-GF-OTHER-{tag}"

    db.operational_locations.insert_many([
        {"id": _nid(), "location_type": "JOB", "name": f"{tag} Site",
         "geocode_status": "Verified", "motive_geofence_id": gid,
         "project_number": proj, "active": True,
         "latitude": 29.0, "longitude": -81.0, "geofence_radius": 300,
         "created_at": _now(), "updated_at": _now()},
        {"id": _nid(), "location_type": "JOB", "name": f"{tag} Other Site",
         "geocode_status": "Verified", "motive_geofence_id": other_gid,
         "project_number": other, "active": True,
         "latitude": 29.5, "longitude": -81.5, "geofence_radius": 300,
         "created_at": _now(), "updated_at": _now()},
    ])

    confirmed_truck = f"T-{tag}-CONF"
    mismatch_truck  = f"T-{tag}-MIS"
    pending_truck   = f"T-{tag}-PEND"
    conf_vid = f"VID-{tag}-1"
    mis_vid  = f"VID-{tag}-2"
    db.asset_mappings.insert_many([
        {"id": _nid(), "provider": "motive", "asset_kind": "vehicle",
         "masci_equipment_id": confirmed_truck,
         "motive": {"vehicle_id": conf_vid, "year": "2024",
                    "make": "Mack", "model": "Anthem"}},
        {"id": _nid(), "provider": "motive", "asset_kind": "vehicle",
         "masci_equipment_id": mismatch_truck,
         "motive": {"vehicle_id": mis_vid, "year": "2020",
                    "make": "Peterbilt", "model": "567"}},
        # No mapping for pending_truck on purpose
    ])

    # Dispatch assignments
    dispatches = []
    for truck, label in [(confirmed_truck, "CONF"),
                          (mismatch_truck, "MIS"),
                          (pending_truck, "PEND")]:
        did = _nid()
        db.dispatch_assignments.insert_one({
            "id": did, "project_number": proj,
            "project_name": f"{tag} project",
            "truck_id": truck, "equipment_id": "",
            "current_state": "ASSIGNED",
            "destination": "Test", "carrier": "",
            "created_at": _now(), "updated_at": _now(),
            "state_history": [], "wait_events": [],
        })
        dispatches.append((label, did))

    # operational_events: confirmed actor at project, mismatch actor at OTHER
    day = datetime.now(timezone.utc)
    day_s = day.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    db.operational_events.insert_many([
        {"id": f"VE-{tag}-1", "asset_key": f"vehicle:{conf_vid}",
         "asset_kind": "vehicle", "asset_label": "Conf Truck",
         "occurred_at": day_s, "location_type": "JOB",
         "location_id": gid, "location_name": "Site",
         "project_number": proj, "event_type": "PROJECT_ARRIVAL",
         "confidence": "HIGH", "source_event_ids": ["x"],
         "created_at": _now(), "updated_at": _now()},
        {"id": f"VE-{tag}-2", "asset_key": f"vehicle:{mis_vid}",
         "asset_kind": "vehicle", "asset_label": "Mis Truck",
         "occurred_at": day_s, "location_type": "JOB",
         "location_id": other_gid, "location_name": "Other",
         "project_number": other, "event_type": "PROJECT_ARRIVAL",
         "confidence": "HIGH", "source_event_ids": ["y"],
         "created_at": _now(), "updated_at": _now()},
    ])

    yield {"tag": tag, "proj": proj, "other": other, "gid": gid,
           "dispatches": dispatches}

    db.operational_locations.delete_many({"name": {"$regex": tag}})
    db.asset_mappings.delete_many({"masci_equipment_id": {"$regex": tag}})
    db.dispatch_assignments.delete_many({"id": {"$in": [d for _, d in dispatches]}})
    db.operational_events.delete_many({"id": {"$regex": f"^VE-{tag}"}})


def test_dispatch_confirmed(ver_world):
    s = ver_world
    label_id = {l: d for l, d in s["dispatches"]}
    r = _req("GET", f"/verification/dispatch/{label_id['CONF']}")
    assert r["status"] == 200
    assert r["json"]["trust_state"] == "CONFIRMED"


def test_dispatch_mismatch(ver_world):
    s = ver_world
    label_id = {l: d for l, d in s["dispatches"]}
    r = _req("GET", f"/verification/dispatch/{label_id['MIS']}")
    assert r["status"] == 200
    assert r["json"]["trust_state"] == "MISMATCH"
    assert s["other"] in r["json"].get("observed_other_projects", [])


def test_dispatch_pending_no_mapping(ver_world):
    s = ver_world
    label_id = {l: d for l, d in s["dispatches"]}
    r = _req("GET", f"/verification/dispatch/{label_id['PEND']}")
    assert r["status"] == 200
    assert r["json"]["trust_state"] == "PENDING_CONFIRMATION"


def test_project_presence_confirmed(ver_world, admin_token):
    s = ver_world
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    r = _req("GET", f"/verification/project-presence/{s['proj']}/{today}",
             token=admin_token)
    assert r["status"] == 200
    assert r["json"]["trust_state"] in ("CONFIRMED", "MISMATCH")


def test_dashboard_counts(ver_world, admin_token):
    r = _req("GET", "/admin/verification/dashboard", token=admin_token)
    assert r["status"] == 200
    counts = r["json"]["dispatch_counts_by_trust"]
    # Must contain all 4 canonical keys
    for k in ("CONFIRMED", "PENDING_CONFIRMATION", "MISMATCH", "QUIET"):
        assert k in counts


def test_audit_endpoint_shape(admin_token):
    r = _req("GET", "/admin/verification/audit", token=admin_token)
    assert r["status"] == 200
    a = r["json"]["answers"]
    for k in [
        "q1_total_verified_assignments", "q2_total_pending_assignments",
        "q3_total_mismatches", "q4_total_quiet_assets",
        "q5_top_mismatch_causes", "q6_most_common_missing_evidence",
        "q7_verification_accuracy_pct", "q8_false_positive_rate",
        "q9_false_negative_rate", "q10_operator_trust_score",
    ]:
        assert k in a


def test_admin_endpoints_require_token():
    r = _req("GET", "/admin/verification/dashboard")
    assert r["status"] in (401, 403)
    r = _req("GET", "/admin/verification/audit")
    assert r["status"] in (401, 403)


# ─── Constitutional guards ───────────────────────────────────────────
def test_no_writes_anywhere(ver_world, admin_token, db):
    s = ver_world
    dr_b = db.daily_reports.count_documents({})
    da_b = db.dispatch_assignments.count_documents({})
    me_b = db.motive_events.count_documents({})
    am_b = db.asset_mappings.count_documents({})
    ol_b = db.operational_locations.count_documents({})
    oe_b = db.operational_events.count_documents({})

    # Call every public + admin endpoint
    label_id = {l: d for l, d in s["dispatches"]}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    _req("GET", f"/verification/dispatch/{label_id['CONF']}")
    _req("GET", f"/verification/dispatch/{label_id['MIS']}")
    _req("GET", f"/verification/dispatch/{label_id['PEND']}")
    _req("GET", f"/verification/project-presence/{s['proj']}/{today}", token=admin_token)
    _req("GET", "/admin/verification/dashboard", token=admin_token)
    _req("GET", "/admin/verification/audit", token=admin_token)

    assert db.daily_reports.count_documents({}) == dr_b
    assert db.dispatch_assignments.count_documents({}) == da_b
    assert db.motive_events.count_documents({}) == me_b
    assert db.asset_mappings.count_documents({}) == am_b
    assert db.operational_locations.count_documents({}) == ol_b
    assert db.operational_events.count_documents({}) == oe_b


def test_no_motive_service_or_httpx_coupling():
    import inspect
    from routes import verification as v
    src = inspect.getsource(v)
    assert "from services.motive_service" not in src
    assert "MotiveService(" not in src
    assert "import httpx" not in src
    assert "httpx.AsyncClient" not in src


def test_no_workflow_or_oa_or_dr_writes():
    import inspect
    from routes import verification as v
    src = inspect.getsource(v)
    for forbidden in [
        "daily_reports.insert", "daily_reports.update", "daily_reports.delete",
        "dispatch_assignments.insert", "dispatch_assignments.update", "dispatch_assignments.delete",
        "motive_events.insert", "motive_events.update", "motive_events.delete",
        "operational_events.insert", "operational_events.update", "operational_events.delete",
        "operational_locations.insert", "operational_locations.update", "operational_locations.delete",
        "asset_mappings.insert", "asset_mappings.update", "asset_mappings.delete",
        "workflow_state_events.insert", "operations_actions.insert",
    ]:
        assert forbidden not in src, f"VER-1 must not perform '{forbidden}'"

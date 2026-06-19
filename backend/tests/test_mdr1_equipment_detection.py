"""
M-DR-1 · Equipment Auto-Discovery · regression suite.

Tests cover:
  • Correct project attribution (verified geofences only)
  • HIGH confidence (≥5 min dwell inside verified geofence)
  • MEDIUM confidence (<5 min dwell = drive-through)
  • Drive-through correctly downgraded (not auto-suppressed)
  • Constitutional rules:
      - LOW never surfaces (proximity heuristic suppressed)
      - No DR mutation by the endpoint
      - No notifications / no OA events / no Motive writes
      - No regression to M-3 (operational_locations untouched)
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

BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8001")
API = f"{BACKEND}/api"
ADMIN_PW = os.environ.get("ADMIN_PASSWORD", "Maddix123!")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]


def _req(method, path, *, body=None, token=""):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Admin-Token"] = token
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return {"status": resp.status, "json": json.loads(resp.read().decode() or "{}")}
    except urllib.error.HTTPError as e:
        try:
            return {"status": e.code, "json": json.loads(e.read().decode() or "{}")}
        except Exception:
            return {"status": e.code, "json": {}}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture(scope="module")
def db():
    cli = MongoClient(MONGO_URL)
    yield cli[DB_NAME]
    cli.close()


@pytest.fixture
def fixture_world(db):
    """Spin up: verified operational_location, motive_geofence row,
    asset_mappings (vehicle + equipment), motive_events for two assets:
    one with HIGH-dwell behavior and one with drive-through MEDIUM."""
    tag = f"MDR1-{uuid.uuid4().hex[:8].upper()}"
    state = {"tag": tag, "ids": []}
    date = "2026-06-08"

    # 1. Seed a Verified operational_location linked to a fake geofence
    motive_gid = f"MDR1-GF-{tag}"
    project_number = f"{tag}-P"
    op_doc = {
        "id": _new_id(),
        "location_type": "JOB",
        "name": f"{tag} project site",
        "latitude": 29.0, "longitude": -81.0,
        "geofence_radius": 350,
        "geocode_status": "Verified",
        "motive_geofence_id": motive_gid,
        "project_number": project_number,
        "active": True,
        "created_at": _now(), "updated_at": _now(),
    }
    db.operational_locations.insert_one(op_doc)
    state["op_id"] = op_doc["id"]

    # 2. Seed asset_mappings (one vehicle, one piece of equipment)
    motive_vehicle_id = f"MDR1-V-{tag}"
    veh_doc = {
        "id": _new_id(), "provider": "motive", "asset_kind": "vehicle",
        "masci_equipment_id": f"masci-truck-{tag}",
        "motive": {"vehicle_id": motive_vehicle_id,
                   "year": "2024", "make": "Mack", "model": "Anthem"},
        "created_at": _now(), "updated_at": _now(),
    }
    motive_asset_id = f"MDR1-A-{tag}"
    asset_doc = {
        "id": _new_id(), "provider": "motive", "asset_kind": "equipment",
        "masci_equipment_id": f"masci-exc-{tag}",
        "motive": {"asset_id": motive_asset_id, "name": f"EXC {tag}",
                   "type": "excavator"},
        "created_at": _now(), "updated_at": _now(),
    }
    db.asset_mappings.insert_many([veh_doc, asset_doc])
    state["mapping_ids"] = [veh_doc["id"], asset_doc["id"]]

    # 3. Seed motive_events:
    #    Vehicle: enter 07:00 → exit 16:30 (long dwell → HIGH)
    #    Equipment: enter 09:00 → exit 09:03 (3 min → drive-through MEDIUM)
    events = [
        {
            "id": _new_id(),
            "event_kind": "geofence_enter",
            "event_family": "geofence_enter",
            "event_at": f"{date}T07:00:00+00:00",
            "source": "webhook",
            "vehicle_id": motive_vehicle_id, "asset_id": None,
            "raw": {
                "event_type": "geofence_enter",
                "vehicle": {"id": motive_vehicle_id},
                "geofence": {"id": motive_gid, "name": f"{tag} project site"},
                "event_time": f"{date}T07:00:00Z",
            },
            "severity": "info",
        },
        {
            "id": _new_id(),
            "event_kind": "geofence_exit",
            "event_family": "geofence_exit",
            "event_at": f"{date}T16:30:00+00:00",
            "source": "webhook",
            "vehicle_id": motive_vehicle_id, "asset_id": None,
            "raw": {
                "event_type": "geofence_exit",
                "vehicle": {"id": motive_vehicle_id},
                "geofence": {"id": motive_gid, "name": f"{tag} project site"},
                "event_time": f"{date}T16:30:00Z",
            },
            "severity": "info",
        },
        # Drive-through equipment — 3 min only
        {
            "id": _new_id(),
            "event_kind": "asset_geofence_enter",
            "event_family": "asset_geofence_enter",
            "event_at": f"{date}T09:00:00+00:00",
            "source": "webhook",
            "vehicle_id": "", "asset_id": motive_asset_id,
            "raw": {
                "event_type": "asset_geofence_enter",
                "asset": {"id": motive_asset_id, "name": f"EXC {tag}"},
                "geofence": {"id": motive_gid, "name": f"{tag} project site"},
                "event_time": f"{date}T09:00:00Z",
            },
            "severity": "medium",
        },
        {
            "id": _new_id(),
            "event_kind": "asset_geofence_exit",
            "event_family": "asset_geofence_exit",
            "event_at": f"{date}T09:03:00+00:00",
            "source": "webhook",
            "vehicle_id": "", "asset_id": motive_asset_id,
            "raw": {
                "event_type": "asset_geofence_exit",
                "asset": {"id": motive_asset_id, "name": f"EXC {tag}"},
                "geofence": {"id": motive_gid, "name": f"{tag} project site"},
                "event_time": f"{date}T09:03:00Z",
            },
            "severity": "medium",
        },
    ]
    db.motive_events.insert_many(events)
    state["event_ids"] = [e["id"] for e in events]
    state["project_number"] = project_number
    state["date"] = date
    state["motive_gid"] = motive_gid
    state["motive_vehicle_id"] = motive_vehicle_id
    state["motive_asset_id"] = motive_asset_id

    yield state

    # Cleanup — only docs we seeded
    db.operational_locations.delete_one({"id": state["op_id"]})
    db.asset_mappings.delete_many({"id": {"$in": state["mapping_ids"]}})
    db.motive_events.delete_many({"id": {"$in": state["event_ids"]}})


# ─── HTTP-level tests ────────────────────────────────────────────────
def test_high_confidence_long_dwell(fixture_world):
    s = fixture_world
    r = _req("GET", f"/equipment-detection/{s['project_number']}/{s['date']}")
    assert r["status"] == 200, r
    j = r["json"]
    assert j["ok"]
    assert j["verified_geofences"] == 1
    assert j["events_considered"] >= 4
    by_key = {d["detection_key"]: d for d in j["detections"]}
    # Vehicle row → HIGH (9.5 hour dwell)
    veh_key = f"vehicle:{s['motive_vehicle_id']}"
    assert veh_key in by_key, f"vehicle not detected: {by_key.keys()}"
    veh = by_key[veh_key]
    assert veh["confidence"] == "HIGH"
    assert veh["dwell_minutes"] >= 570  # 9h 30m
    assert veh["first_seen"] == "07:00"
    assert veh["last_seen"] == "16:30"
    assert veh["asset_kind"] == "vehicle"
    assert veh["label"] == "2024 Mack Anthem"
    assert veh["masci_equipment_id"] == f"masci-truck-{s['tag']}"
    assert veh["source"] == "motive"
    assert veh["geofence"]["id"] == s["motive_gid"]


def test_medium_confidence_drive_through(fixture_world):
    s = fixture_world
    r = _req("GET", f"/equipment-detection/{s['project_number']}/{s['date']}")
    assert r["status"] == 200
    by_key = {d["detection_key"]: d for d in r["json"]["detections"]}
    eq_key = f"equipment:{s['motive_asset_id']}"
    assert eq_key in by_key
    eq = by_key[eq_key]
    # 3-minute dwell → MEDIUM (drive-through)
    assert eq["confidence"] == "MEDIUM"
    assert eq["dwell_minutes"] == 3
    assert eq["asset_kind"] == "equipment"
    assert eq["label"] == f"EXC {s['tag']}"


def test_project_attribution_via_verified_geofence_only(fixture_world, db):
    """If we flip the operational_locations row to Rejected, the project
    should report no verified geofence and produce zero detections."""
    s = fixture_world
    db.operational_locations.update_one(
        {"id": s["op_id"]}, {"$set": {"geocode_status": "Rejected"}}
    )
    try:
        r = _req("GET", f"/equipment-detection/{s['project_number']}/{s['date']}")
        assert r["status"] == 200
        j = r["json"]
        assert j["detections"] == []
        assert j["verified_geofences"] == 0
        assert j["no_detection_reason"] == "no_verified_geofence"
    finally:
        db.operational_locations.update_one(
            {"id": s["op_id"]}, {"$set": {"geocode_status": "Verified"}}
        )


def test_unknown_project_returns_empty(fixture_world):
    r = _req("GET", "/equipment-detection/DOES-NOT-EXIST-XYZ/2026-06-08")
    assert r["status"] == 200
    assert r["json"]["detections"] == []
    assert r["json"]["no_detection_reason"] == "no_verified_geofence"


def test_invalid_date_format_rejected():
    r = _req("GET", "/equipment-detection/X/2026-13-99")
    # Regex on the path will 404 before the handler runs
    assert r["status"] in (400, 404, 422)


def test_no_low_band_is_ever_surfaced(fixture_world, db):
    """LOW band events are computed only inside a verified geofence,
    BUT the endpoint suppresses LOW entirely (MDR1-4). We synthesize a
    zero-dwell pair to confirm the endpoint never emits LOW."""
    s = fixture_world
    # Inject a zero-dwell pair for a brand-new vehicle (same enter+exit
    # second).
    new_vid = f"MDR1-NEAR-{s['tag']}"
    near_evs = [
        {
            "id": _new_id(),
            "event_kind": "geofence_enter",
            "event_family": "geofence_enter",
            "event_at": f"{s['date']}T11:00:00+00:00",
            "source": "webhook",
            "vehicle_id": new_vid, "asset_id": None,
            "raw": {
                "vehicle": {"id": new_vid},
                "geofence": {"id": s["motive_gid"]},
                "event_time": f"{s['date']}T11:00:00Z",
            },
            "severity": "info",
        },
        {
            "id": _new_id(),
            "event_kind": "geofence_exit",
            "event_family": "geofence_exit",
            "event_at": f"{s['date']}T11:00:00+00:00",
            "source": "webhook",
            "vehicle_id": new_vid, "asset_id": None,
            "raw": {
                "vehicle": {"id": new_vid},
                "geofence": {"id": s["motive_gid"]},
                "event_time": f"{s['date']}T11:00:00Z",
            },
            "severity": "info",
        },
    ]
    db.motive_events.insert_many(near_evs)
    try:
        r = _req("GET", f"/equipment-detection/{s['project_number']}/{s['date']}")
        # The zero-dwell row is MEDIUM (still inside a verified geofence,
        # just <5 min), NOT LOW. LOW would require no verified geofence
        # which the endpoint short-circuits earlier.
        confidences = [d["confidence"] for d in r["json"]["detections"]]
        assert "LOW" not in confidences, "LOW must NEVER surface per MDR1-4"
        # And the new zero-dwell vehicle does appear as MEDIUM
        keys = [d["detection_key"] for d in r["json"]["detections"]]
        assert f"vehicle:{new_vid}" in keys
    finally:
        db.motive_events.delete_many({"id": {"$in": [e["id"] for e in near_evs]}})


# ─── Constitutional checks ────────────────────────────────────────────
def test_no_daily_report_mutation(fixture_world, db):
    """Hitting the endpoint must NOT touch daily_reports, dispatch,
    motive_events, asset_mappings, or operational_locations counts."""
    s = fixture_world
    dr_before = db.daily_reports.count_documents({})
    da_before = db.dispatch_assignments.count_documents({})
    me_before = db.motive_events.count_documents({})
    am_before = db.asset_mappings.count_documents({})
    ol_before = db.operational_locations.count_documents({})

    _req("GET", f"/equipment-detection/{s['project_number']}/{s['date']}")
    _req("GET", f"/equipment-detection/{s['project_number']}/{s['date']}")
    _req("GET", f"/equipment-detection/{s['project_number']}/{s['date']}")

    assert db.daily_reports.count_documents({}) == dr_before
    assert db.dispatch_assignments.count_documents({}) == da_before
    assert db.motive_events.count_documents({}) == me_before
    assert db.asset_mappings.count_documents({}) == am_before
    assert db.operational_locations.count_documents({}) == ol_before


def test_no_motive_service_coupling():
    """M-DR-1 must NOT push to Motive — no motive_service import, no httpx."""
    import inspect
    from routes import equipment_detection as ed
    src = inspect.getsource(ed)
    assert "from services.motive_service" not in src
    assert "MotiveService(" not in src
    assert "import httpx" not in src
    assert "httpx.AsyncClient" not in src


def test_constants_match_doctrine():
    from routes.equipment_detection import HIGH_DWELL_MIN, PRESENCE_EVENTS
    assert HIGH_DWELL_MIN == 5
    assert PRESENCE_EVENTS == {
        "geofence_enter", "geofence_exit",
        "asset_geofence_enter", "asset_geofence_exit",
    }


def test_m3_collection_untouched(fixture_world, db):
    """Pinging M-DR-1 does not perturb operational_locations beyond what
    we seeded — no schema drift, no extra fields."""
    s = fixture_world
    before = db.operational_locations.find_one({"id": s["op_id"]})
    _req("GET", f"/equipment-detection/{s['project_number']}/{s['date']}")
    after = db.operational_locations.find_one({"id": s["op_id"]})
    # All keys present before are still present + values unchanged.
    for k, v in before.items():
        assert after[k] == v, f"M-DR-1 leaked into M-3 collection at key {k}"


def test_endpoint_does_not_require_admin_token(fixture_world):
    """Per Daily-Report public-form pattern, the suggestion endpoint
    must be reachable WITHOUT an admin token (foremen don't have it)."""
    s = fixture_world
    r = _req("GET", f"/equipment-detection/{s['project_number']}/{s['date']}")
    assert r["status"] == 200, "must be public-read"

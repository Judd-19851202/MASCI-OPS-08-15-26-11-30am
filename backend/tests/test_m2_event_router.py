"""
M-2 · Event Router · regression suite.

Tests cover:
  • Pure-function router: dedupe, arrival/departure pairing, UNKNOWN handling,
    drive-through MEDIUM, idempotent stable ids.
  • Materialize endpoint, audit endpoint, dashboard, project-day, timeline,
    dispatch-status.
  • Constitutional: M-2-8 forbidden fields, no daily_report / dispatch /
    motive_events / asset_mappings writes, no motive_service coupling,
    no driver-surveillance fields.
  • M-3 + M-DR-1 regression: tests still pass after M-2 ships.
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
        with urllib.request.urlopen(req, timeout=20) as resp:
            return {"status": resp.status, "json": json.loads(resp.read().decode() or "{}")}
    except urllib.error.HTTPError as e:
        try:
            return {"status": e.code, "json": json.loads(e.read().decode() or "{}")}
        except Exception:  # noqa: BLE001
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


@pytest.fixture
def world(db):
    """Seed: 2 Verified op_locations (1 JOB, 1 SHOP) + 1 UNKNOWN fence
    used only in events. 1 vehicle + 1 equipment in asset_mappings.
    A timeline of events covering arrival/departure for both."""
    tag = f"M2T-{uuid.uuid4().hex[:8].upper()}"
    date = "2026-06-08"

    job_gid = f"M2GF-JOB-{tag}"
    shop_gid = f"M2GF-SHOP-{tag}"
    unknown_gid = f"M2GF-UNK-{tag}"  # No op_location for this one
    proj_num = f"{tag}-P"

    db.operational_locations.insert_many([
        {"id": _nid(), "location_type": "JOB", "name": f"{tag} Project",
         "geocode_status": "Verified", "motive_geofence_id": job_gid,
         "project_number": proj_num, "active": True,
         "latitude": 29.0, "longitude": -81.0, "geofence_radius": 400,
         "created_at": _now(), "updated_at": _now()},
        {"id": _nid(), "location_type": "SHOP", "name": f"{tag} Shop",
         "geocode_status": "Verified", "motive_geofence_id": shop_gid,
         "project_number": None, "active": True,
         "latitude": 29.1, "longitude": -81.1, "geofence_radius": 200,
         "created_at": _now(), "updated_at": _now()},
    ])
    veh = f"M2V-{tag}"
    ast = f"M2A-{tag}"
    db.asset_mappings.insert_many([
        {"id": _nid(), "provider": "motive", "asset_kind": "vehicle",
         "masci_equipment_id": f"TRUCK-{tag}",
         "motive": {"vehicle_id": veh, "year": "2024", "make": "Mack",
                    "model": "Anthem"}},
        {"id": _nid(), "provider": "motive", "asset_kind": "equipment",
         "masci_equipment_id": f"EX-{tag}",
         "motive": {"asset_id": ast, "name": f"CAT 320 {tag}",
                    "type": "excavator"}},
    ])

    # Timeline (for the vehicle):
    #   06:47 enter JOB → 12:04 exit JOB → 12:38 enter SHOP → 13:12 exit SHOP → 13:46 enter JOB → 17:00 exit JOB
    # Excavator: enter JOB 07:30 → drive-through SHOP 09:00-09:03 → back JOB 09:30 → exit 16:55
    # Vehicle re-enter JOB twice on purpose (dedupe test)
    base = f"{date}T"
    ev = lambda fam, t, gid, kind, aid, eid: {
        "id": eid, "event_kind": fam, "event_family": fam,
        "event_at": f"{base}{t}:00+00:00", "source": "webhook",
        "vehicle_id": aid if kind == "vehicle" else "",
        "asset_id": None,
        "raw": {"event_type": fam,
                ("vehicle" if kind == "vehicle" else "asset"): {"id": aid, "name": f"Demo {aid}"},
                "geofence": {"id": gid, "name": "demo"},
                "event_time": f"{base}{t}:00Z"},
        "severity": "info",
        "created_at": _now(),
    }
    seeded = [
        ev("geofence_enter", "06:47", job_gid,     "vehicle",   veh, f"{tag}-ve1"),
        ev("geofence_enter", "06:50", job_gid,     "vehicle",   veh, f"{tag}-ve1b"),  # DEDUPE
        ev("geofence_exit",  "12:04", job_gid,     "vehicle",   veh, f"{tag}-ve2"),
        ev("geofence_enter", "12:38", shop_gid,    "vehicle",   veh, f"{tag}-ve3"),
        ev("geofence_exit",  "13:12", shop_gid,    "vehicle",   veh, f"{tag}-ve4"),
        ev("geofence_enter", "13:46", job_gid,     "vehicle",   veh, f"{tag}-ve5"),
        ev("geofence_exit",  "17:00", job_gid,     "vehicle",   veh, f"{tag}-ve6"),
        # Excavator
        ev("asset_geofence_enter", "07:30", job_gid,     "asset", ast, f"{tag}-ae1"),
        ev("asset_geofence_exit",  "16:55", job_gid,     "asset", ast, f"{tag}-ae2"),
        # UNKNOWN fence in events (no op_location) — must yield UNKNOWN_*
        ev("geofence_enter", "18:00", unknown_gid, "vehicle", veh, f"{tag}-uu1"),
        ev("geofence_exit",  "18:30", unknown_gid, "vehicle", veh, f"{tag}-uu2"),
    ]
    db.motive_events.insert_many(seeded)

    yield {"tag": tag, "date": date, "job_gid": job_gid, "shop_gid": shop_gid,
           "unknown_gid": unknown_gid, "proj_num": proj_num,
           "veh": veh, "ast": ast, "event_ids": [e["id"] for e in seeded]}

    # Cleanup
    db.operational_locations.delete_many({"name": {"$regex": tag}})
    db.asset_mappings.delete_many({"masci_equipment_id": {"$regex": tag}})
    db.motive_events.delete_many({"id": {"$in": [e["id"] for e in seeded]}})
    db.operational_events.delete_many({"asset_key": {"$in":
        [f"vehicle:{veh}", f"equipment:{ast}"]}})


# ─── Pure-function unit tests ─────────────────────────────────────────
def test_router_basic_arrival_and_dedupe():
    from routes.operational_events import route_motive_events
    op_by_gid = {
        "GF1": {"id": "L1", "location_type": "JOB", "name": "Site A",
                "project_number": "JOB-A"}
    }
    resolver = lambda k: ("Test Truck", "MASCI-1", "vehicle")
    evs = [
        {"id": "e1", "event_family": "geofence_enter", "event_at": "2026-06-08T07:00:00Z",
         "raw": {"vehicle": {"id": "V"}, "geofence": {"id": "GF1"}}},
        {"id": "e2", "event_family": "geofence_enter", "event_at": "2026-06-08T07:01:00Z",
         "raw": {"vehicle": {"id": "V"}, "geofence": {"id": "GF1"}}},  # dedupe
        {"id": "e3", "event_family": "geofence_exit",  "event_at": "2026-06-08T16:00:00Z",
         "raw": {"vehicle": {"id": "V"}, "geofence": {"id": "GF1"}}},
    ]
    out = route_motive_events(evs, op_by_gid, resolver)
    types = [e["event_type"] for e in out]
    assert types == ["PROJECT_ARRIVAL", "PROJECT_DEPARTURE"]
    assert out[0]["confidence"] == "HIGH"
    assert out[1]["dwell_minutes_so_far"] == 540  # 9h


def test_router_unknown_geofence_stays_unknown():
    from routes.operational_events import route_motive_events
    op_by_gid = {}  # nothing verified
    resolver = lambda k: ("X", None, "vehicle")
    evs = [
        {"id": "e1", "event_family": "geofence_enter", "event_at": "2026-06-08T10:00:00Z",
         "raw": {"vehicle": {"id": "V"}, "geofence": {"id": "GF-Z"}}},
        {"id": "e2", "event_family": "geofence_exit",  "event_at": "2026-06-08T10:08:00Z",
         "raw": {"vehicle": {"id": "V"}, "geofence": {"id": "GF-Z"}}},
    ]
    out = route_motive_events(evs, op_by_gid, resolver)
    assert all(e["location_type"] == "UNKNOWN" for e in out)
    assert [e["event_type"] for e in out] == ["UNKNOWN_ARRIVAL", "UNKNOWN_DEPARTURE"]


def test_router_idempotent_stable_id():
    from routes.operational_events import route_motive_events
    op = {"GF1": {"id": "L1", "location_type": "JOB", "name": "S",
                  "project_number": "P"}}
    resolver = lambda k: ("X", None, "vehicle")
    evs = [
        {"id": "e1", "event_family": "geofence_enter", "event_at": "2026-06-08T07:00:00Z",
         "raw": {"vehicle": {"id": "V"}, "geofence": {"id": "GF1"}}},
        {"id": "e2", "event_family": "geofence_exit",  "event_at": "2026-06-08T16:00:00Z",
         "raw": {"vehicle": {"id": "V"}, "geofence": {"id": "GF1"}}},
    ]
    a = route_motive_events(evs, op, resolver)
    b = route_motive_events(evs, op, resolver)
    assert [d["id"] for d in a] == [d["id"] for d in b]


def test_router_drive_through_is_medium():
    from routes.operational_events import route_motive_events
    op = {"GF1": {"id": "L1", "location_type": "JOB", "name": "S",
                  "project_number": "P"}}
    resolver = lambda k: ("X", None, "vehicle")
    evs = [
        {"id": "e1", "event_family": "geofence_enter", "event_at": "2026-06-08T07:00:00Z",
         "raw": {"vehicle": {"id": "V"}, "geofence": {"id": "GF1"}}},
        {"id": "e2", "event_family": "geofence_exit",  "event_at": "2026-06-08T07:02:00Z",
         "raw": {"vehicle": {"id": "V"}, "geofence": {"id": "GF1"}}},
    ]
    out = route_motive_events(evs, op, resolver)
    types_conf = [(e["event_type"], e["confidence"]) for e in out]
    assert ("PROJECT_DEPARTURE", "MEDIUM") in types_conf


def test_storage_gate_rejects_forbidden_field():
    from routes.operational_events import _validate_doc
    with pytest.raises(ValueError):
        _validate_doc({"id": "x", "asset_key": "v:1",
                       "driver_score": 99,  # forbidden keyword
                       "occurred_at": "x", "location_type": "JOB",
                       "event_type": "PROJECT_ARRIVAL", "confidence": "HIGH"})
    with pytest.raises(ValueError):
        _validate_doc({"id": "x", "asset_key": "v:1",
                       "occurred_at": "x", "location_type": "JOB",
                       "event_type": "PROJECT_ARRIVAL", "confidence": "HIGH",
                       "behavior_metric": 0.1})


def test_constants_correct():
    from routes.operational_events import (
        HIGH_DWELL_MIN, PRESENCE_EVENTS, LOCATION_TYPE_TO_ARRIVAL,
        FORBIDDEN_KEYWORDS, ALLOWED_EVENT_FIELDS,
    )
    assert HIGH_DWELL_MIN == 5
    assert PRESENCE_EVENTS == {"geofence_enter", "geofence_exit",
                                "asset_geofence_enter", "asset_geofence_exit"}
    # All 8 location types + UNKNOWN
    for k in ["JOB", "ASPHALT_PLANT", "CONCRETE_PLANT", "PIT", "YARD", "SHOP",
              "DISPOSAL_SITE", "VENDOR", "UNKNOWN"]:
        assert k in LOCATION_TYPE_TO_ARRIVAL
    assert "behavior" in FORBIDDEN_KEYWORDS
    assert "asset_key" in ALLOWED_EVENT_FIELDS
    # No driver behavior / surveillance allowed
    assert not any("driver_score" in f for f in ALLOWED_EVENT_FIELDS)


# ─── HTTP-level integration tests ────────────────────────────────────
def test_materialize_and_project_day(world, admin_token, db):
    s = world
    r = _req("POST", "/admin/operational-events/materialize",
             token=admin_token)
    assert r["status"] == 200, r
    assert r["json"]["routed"] > 0
    upserted = r["json"]["upserted"]

    # Idempotency: re-run produces same upserts (same ids)
    r2 = _req("POST", "/admin/operational-events/materialize",
              token=admin_token)
    assert r2["json"]["upserted"] == upserted

    # Project-day endpoint — vehicle should show first 06:47 arrival and
    # last 17:00 departure (after merge).
    r = _req("GET", f"/operational-events/project-day/{s['proj_num']}/{s['date']}")
    assert r["status"] == 200
    assets = r["json"]["assets"]
    assert len(assets) >= 1
    vehicle = next(a for a in assets if a["asset_key"] == f"vehicle:{s['veh']}")
    assert vehicle["first_seen"] == "06:47"
    assert vehicle["last_seen"] == "17:00"
    assert vehicle["still_on_site"] is False


def test_timeline_endpoint(world, admin_token):
    s = world
    _req("POST", "/admin/operational-events/materialize", token=admin_token)
    r = _req("GET", f"/operational-events/timeline/vehicle:{s['veh']}/{s['date']}")
    assert r["status"] == 200
    types = [e["event_type"] for e in r["json"]["events"]]
    # Expected sequence (UNKNOWN at 18:00/18:30 is also included):
    #   PROJECT_ARRIVAL → PROJECT_DEPARTURE → SHOP_ARRIVAL → SHOP_DEPARTURE
    #   → PROJECT_ARRIVAL → PROJECT_DEPARTURE → UNKNOWN_ARRIVAL → UNKNOWN_DEPARTURE
    assert types == [
        "PROJECT_ARRIVAL", "PROJECT_DEPARTURE",
        "SHOP_ARRIVAL",    "SHOP_DEPARTURE",
        "PROJECT_ARRIVAL", "PROJECT_DEPARTURE",
        "UNKNOWN_ARRIVAL", "UNKNOWN_DEPARTURE",
    ]


def test_dispatch_status_endpoint(world, admin_token):
    s = world
    _req("POST", "/admin/operational-events/materialize", token=admin_token)
    r = _req("GET", f"/operational-events/dispatch-status/vehicle:{s['veh']}")
    assert r["status"] == 200
    # After all the events, vehicle's last event is UNKNOWN_DEPARTURE
    assert r["json"]["state"] == "DEPARTED"


def test_dashboard_buckets(admin_token, world):
    s = world
    _req("POST", "/admin/operational-events/materialize", token=admin_token)
    r = _req("GET", "/admin/operational-events/dashboard", token=admin_token)
    assert r["status"] == 200
    buckets = r["json"]["buckets"]
    # Buckets keyed by the brief's labels (M-2-7).
    for label in ["Equipment On Projects", "Equipment At Plants",
                  "Equipment At Yard", "Equipment At Shop",
                  "Equipment At Disposal Sites", "Equipment At Pits",
                  "Unknown Location"]:
        assert label in buckets


def test_audit_endpoint_shape(admin_token):
    _req("POST", "/admin/operational-events/materialize", token=admin_token)
    r = _req("GET", "/admin/operational-events/audit", token=admin_token)
    assert r["status"] == 200
    ans = r["json"]["answers"]
    for k in ["q1_assets_generating_events", "q2_presence_events_total",
              "q3_distinct_geofences_in_events", "q3_unmatched_geofences",
              "q5_duplicates_collapsed", "q6_asset_mappings_total",
              "q6_asset_mappings_masci_mapped", "q6_asset_mappings_unmapped",
              "q8_top_geofences", "q9_event_distribution_by_category",
              "q10_accuracy_pct_estimate"]:
        assert k in ans


def test_admin_endpoints_require_token():
    """All /admin/operational-events/* require X-Admin-Token."""
    for path in [
        "/admin/operational-events/materialize",
        "/admin/operational-events/audit",
        "/admin/operational-events/dashboard",
    ]:
        r = _req("POST" if "materialize" in path else "GET", path)
        assert r["status"] in (401, 403), f"{path} returned {r['status']}"


def test_unknown_geofence_does_not_create_op_location(world, admin_token, db):
    """Materializing a window with an UNKNOWN geofence must NOT create
    an op_location row for it."""
    s = world
    before = db.operational_locations.count_documents(
        {"motive_geofence_id": s["unknown_gid"]}
    )
    assert before == 0
    _req("POST", "/admin/operational-events/materialize", token=admin_token)
    after = db.operational_locations.count_documents(
        {"motive_geofence_id": s["unknown_gid"]}
    )
    assert after == 0


# ─── Constitutional guards ────────────────────────────────────────────
def test_no_daily_report_or_dispatch_or_motive_writes(admin_token, db, world):
    dr_b = db.daily_reports.count_documents({})
    da_b = db.dispatch_assignments.count_documents({})
    me_b = db.motive_events.count_documents({})
    am_b = db.asset_mappings.count_documents({})

    _req("POST", "/admin/operational-events/materialize", token=admin_token)
    _req("GET", "/admin/operational-events/audit", token=admin_token)
    _req("GET", "/admin/operational-events/dashboard", token=admin_token)
    _req("GET", f"/operational-events/project-day/{world['proj_num']}/{world['date']}")
    _req("GET", f"/operational-events/timeline/vehicle:{world['veh']}/{world['date']}")
    _req("GET", f"/operational-events/dispatch-status/vehicle:{world['veh']}")

    assert db.daily_reports.count_documents({}) == dr_b
    assert db.dispatch_assignments.count_documents({}) == da_b
    assert db.motive_events.count_documents({}) == me_b
    assert db.asset_mappings.count_documents({}) == am_b


def test_no_motive_service_or_httpx_coupling():
    import inspect
    from routes import operational_events as oe
    src = inspect.getsource(oe)
    assert "from services.motive_service" not in src
    assert "MotiveService(" not in src
    assert "import httpx" not in src
    assert "httpx.AsyncClient" not in src


def test_no_workflow_state_or_oa_writes():
    """Source must NOT write to workflow_state_events or
    operations_actions collections."""
    import inspect
    from routes import operational_events as oe
    src = inspect.getsource(oe)
    # Allow reads if any; ensure no insert/update operations
    for forbidden in [
        "workflow_state_events.insert",
        "workflow_state_events.update",
        "operations_actions.insert",
        "operations_actions.update",
        "daily_reports.insert", "daily_reports.update",
        "dispatch_assignments.insert", "dispatch_assignments.update",
        "motive_events.insert", "motive_events.update",
        "motive_events.delete",
        "asset_mappings.insert", "asset_mappings.update",
    ]:
        assert forbidden not in src, f"M-2 must not perform '{forbidden}'"


# ─── M-3 + M-DR-1 regression sanity ───────────────────────────────────
def test_m3_collection_untouched_by_m2(admin_token, db, world):
    """Materializing M-2 must not touch operational_locations rows
    beyond what we seeded."""
    s = world
    before = list(db.operational_locations.find({"name": {"$regex": s["tag"]}}))
    _req("POST", "/admin/operational-events/materialize", token=admin_token)
    after = list(db.operational_locations.find({"name": {"$regex": s["tag"]}}))
    assert len(before) == len(after)
    for b, a in zip(before, after):
        for k in b:
            if k == "_id":
                continue
            assert b[k] == a[k], f"M-2 leaked into M-3: key {k}"

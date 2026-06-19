"""
M-3 · Geocode Foundation · regression suite.

Tests cover:
  • Scorer pure-function bands (HIGH / MEDIUM / LOW)
  • Polygon centroid + max-radius math
  • Geofence import (idempotent, polygon → centroid + radius)
  • Reconciliation engine
  • Approval / Reject / Reassign / Bulk-approve (HIGH-only restriction)
  • By-project visibility (M3-5)
  • Constitutional rules: no Motive writes, no Daily Report side effects,
    no automatic project assignment.

Uses sync pytest pattern (urllib.request) to match the rest of the suite.
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
        except Exception:  # noqa: BLE001
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


@pytest.fixture(scope="module")
def admin_token():
    r = _req("POST", "/admin/login", body={"password": ADMIN_PW})
    assert r["status"] == 200, f"login failed: {r}"
    return r["json"]["token"]


@pytest.fixture
def isolated_tag(db):
    """A unique tag for test docs. Cleanup after each test."""
    tag = f"M3T-{uuid.uuid4().hex[:8].upper()}"
    yield tag
    db.operational_locations.delete_many({"name": {"$regex": tag}})
    db.motive_geofences.delete_many({"name": {"$regex": tag}})
    db.jobs_master.delete_many({"project_number": {"$regex": tag}})


# ─── Pure-function tests on the scorer (no DB / no HTTP) ──────────────
def test_score_matches_project_number():
    from routes.operational_locations import _score_match
    job = {"project_number": "24-06", "project_name": "T5824 - SR 46 (W 1ST ST.)",
           "location": "SR 46 W 1st St"}
    fence = {"name": "24-06 SR 46 W 1st St", "address": ""}
    out = _score_match(job, fence)
    assert out["band"] == "high"
    assert out["score"] >= 0.85
    assert out["best_signal"]["kind"] == "project_number"


def test_score_matches_t_number():
    from routes.operational_locations import _score_match
    job = {"project_number": "24-06", "project_name": "T5824 - SR 46 (W 1ST ST.)",
           "location": "SR 46 W 1st St"}
    fence = {"name": "T5824 jobsite", "address": ""}
    out = _score_match(job, fence)
    assert out["band"] == "high"
    assert out["best_signal"]["kind"] in ("t_number", "project_number")


def test_score_low_unrelated():
    from routes.operational_locations import _score_match
    job = {"project_number": "26-05", "project_name": "Fillmore Ave Reconstruction",
           "location": "Fillmore Ave"}
    fence = {"name": "Random Plant Daytona", "address": ""}
    out = _score_match(job, fence)
    assert out["band"] == "low"
    assert out["score"] < 0.55


def test_polygon_centroid_and_radius():
    from routes.operational_locations import _polygon_centroid, _polygon_radius_ft
    pts = [
        {"lat": 28.9995, "lon": -81.0005},
        {"lat": 29.0005, "lon": -81.0005},
        {"lat": 29.0005, "lon": -80.9995},
        {"lat": 28.9995, "lon": -80.9995},
    ]
    c = _polygon_centroid(pts)
    assert c is not None
    assert abs(c["lat"] - 29.0) < 1e-4
    assert abs(c["lon"] - (-81.0)) < 1e-4
    r = _polygon_radius_ft(pts, c)
    # ~100 m square → centroid-to-corner ~70 m → ~230 ft
    assert 100 < r < 800


def test_polygon_radius_defaults_when_empty():
    from routes.operational_locations import _polygon_radius_ft
    assert _polygon_radius_ft([], {}) == 250


# ─── HTTP-level integration tests ─────────────────────────────────────
def test_import_reconcile_approve_full_flow(db, admin_token, isolated_tag):
    tag = isolated_tag
    gid = f"GF-{tag}"
    proj_num = f"{tag}-A"

    # Seed a job with a strong, distinctive project number that will match exactly
    db.jobs_master.insert_one({
        "id": _new_id(),
        "project_number": proj_num,
        "project_name": f"T9999 {tag} Test Project",
        "location": "Test Loc",
        "client": "TEST", "project_manager": "", "pm_email": "",
        "co_pm_emails": [], "active": True,
        "created_at": _now(), "updated_at": _now(),
    })
    # Seed a Motive geofence (read-source for import) named with that project_number
    db.motive_geofences.insert_one({
        "id": _new_id(),
        "motive_geofence_id": gid,
        "name": f"{proj_num} T9999 {tag} Jobsite",
        "address": "",
        "category": "Job Site",
        "status": "active",
        "location_points": [
            {"lat": 28.9995, "lon": -81.0005},
            {"lat": 29.0005, "lon": -81.0005},
            {"lat": 29.0005, "lon": -80.9995},
            {"lat": 28.9995, "lon": -80.9995},
        ],
        "created_at": _now(), "updated_at": _now(),
    })

    # 1. Import — non-destructive
    r = _req("POST", "/admin/locations/import-geofences", token=admin_token)
    assert r["status"] == 200
    assert r["json"]["ok"]

    loc = db.operational_locations.find_one({"motive_geofence_id": gid})
    assert loc, "import did not create operational_locations row"
    assert loc["geocode_status"] == "Imported"
    assert loc.get("latitude") and loc.get("longitude")
    assert loc.get("geofence_radius") and loc["geofence_radius"] > 0
    # CONSTITUTIONAL: project_number must NOT be set on import.
    assert not loc.get("project_number"), "import must not auto-assign project_number"
    loc_id = loc["id"]

    # 1b. Idempotency
    _req("POST", "/admin/locations/import-geofences", token=admin_token)
    assert db.operational_locations.count_documents({"motive_geofence_id": gid}) == 1

    # 2. Reconcile
    r = _req("POST", "/admin/locations/reconcile", token=admin_token)
    assert r["status"] == 200
    reconciled = db.operational_locations.find_one({"id": loc_id})
    assert reconciled["proposed_project_number"] == proj_num
    assert reconciled["confidence_band"] == "high"
    assert reconciled["geocode_status"] == "Matched"
    # CONSTITUTIONAL: project_number is STILL not set after reconcile.
    assert not reconciled.get("project_number"), "reconcile must not auto-set project_number"

    # 3. Reconciliation queue
    r = _req("GET", "/admin/locations/reconciliation-queue?band=high", token=admin_token)
    assert r["status"] == 200
    assert any(row["id"] == loc_id for row in r["json"]["rows"])
    assert "counts" in r["json"]

    # 4. Bulk-approve restriction: below-HIGH gets skipped
    db.operational_locations.update_one(
        {"id": loc_id},
        {"$set": {"confidence_score": 0.70, "confidence_band": "medium"}},
    )
    r = _req("POST", "/admin/locations/bulk-approve",
             body={"ids": [loc_id]}, token=admin_token)
    assert r["status"] == 200
    p = r["json"]
    assert p["approved_count"] == 0
    assert p["skipped_count"] == 1
    assert p["skipped"][0]["reason"] == "below_high_confidence"

    # 5. Bulk-approve HIGH succeeds
    db.operational_locations.update_one(
        {"id": loc_id},
        {"$set": {"confidence_score": 0.95, "confidence_band": "high"}},
    )
    r = _req("POST", "/admin/locations/bulk-approve",
             body={"ids": [loc_id]}, token=admin_token)
    assert r["status"] == 200
    assert r["json"]["approved_count"] == 1
    verified = db.operational_locations.find_one({"id": loc_id})
    assert verified["geocode_status"] == "Verified"
    assert verified["project_number"] == proj_num

    # 6. by-project visibility (M3-5)
    r = _req("GET", "/admin/locations/by-project", token=admin_token)
    assert r["status"] == 200
    assert proj_num in r["json"]["verified"]
    assert r["json"]["verified"][proj_num]["motive_geofence_id"] == gid


def test_reject_and_reassign(db, admin_token, isolated_tag):
    tag = isolated_tag
    gid = f"GF2-{tag}"
    proj_num = f"{tag}-B"

    db.jobs_master.insert_one({
        "id": _new_id(),
        "project_number": proj_num,
        "project_name": f"{tag} second", "location": "x",
        "client": "TEST", "project_manager": "", "pm_email": "",
        "co_pm_emails": [], "active": True,
        "created_at": _now(), "updated_at": _now(),
    })
    db.motive_geofences.insert_one({
        "id": _new_id(),
        "motive_geofence_id": gid,
        "name": f"Unrelated {tag}",
        "address": "",
        "category": "Terminal / Yard",
        "status": "active",
        "location_points": [{"lat": 28.9, "lon": -81.5}, {"lat": 28.91, "lon": -81.5}],
        "created_at": _now(), "updated_at": _now(),
    })

    _req("POST", "/admin/locations/import-geofences", token=admin_token)
    loc = db.operational_locations.find_one({"motive_geofence_id": gid})
    # Category routing: "Terminal / Yard" → YARD
    assert loc["location_type"] == "YARD"

    # Reject
    r = _req("POST", f"/admin/locations/{loc['id']}/reject", token=admin_token)
    assert r["status"] == 200
    assert db.operational_locations.find_one({"id": loc["id"]})["geocode_status"] == "Rejected"

    # Reassign rejects unknown project_number
    r = _req("POST", f"/admin/locations/{loc['id']}/reassign",
             body={"project_number": "DOES-NOT-EXIST-XYZ"}, token=admin_token)
    assert r["status"] == 400

    # Reassign to real project_number → Verified
    r = _req("POST", f"/admin/locations/{loc['id']}/reassign",
             body={"project_number": proj_num}, token=admin_token)
    assert r["status"] == 200
    out = db.operational_locations.find_one({"id": loc["id"]})
    assert out["project_number"] == proj_num
    assert out["geocode_status"] == "Verified"
    assert out["match_signal"]["kind"] == "manual"


def test_admin_gate_required():
    """No admin token → 403/401."""
    r = _req("GET", "/admin/locations/reconciliation-queue")
    assert r["status"] in (401, 403)
    r = _req("POST", "/admin/locations/reconcile")
    assert r["status"] in (401, 403)
    r = _req("POST", "/admin/locations/import-geofences")
    assert r["status"] in (401, 403)


# ─── Constitutional / Doctrinal checks ────────────────────────────────
def test_no_motive_service_coupling():
    """M-3 router MUST NOT import motive_service.
    This guards against a future accidental coupling that would let
    M-3 push back to Motive."""
    import inspect
    from routes import operational_locations as opl
    src = inspect.getsource(opl)
    assert "from services.motive_service" not in src
    assert "MotiveService(" not in src
    # And no httpx (no outbound HTTP calls to Motive's API)
    assert "import httpx" not in src
    assert "httpx.AsyncClient" not in src


def test_no_daily_report_or_dispatch_writes(db, admin_token):
    dr_before = db.daily_reports.count_documents({})
    da_before = db.dispatch_assignments.count_documents({})
    me_before = db.motive_events.count_documents({})

    _req("POST", "/admin/locations/import-geofences", token=admin_token)
    _req("POST", "/admin/locations/reconcile", token=admin_token)

    assert db.daily_reports.count_documents({}) == dr_before
    assert db.dispatch_assignments.count_documents({}) == da_before
    assert db.motive_events.count_documents({}) == me_before


def test_location_types_enum_complete():
    """The 8 canonical location_type values are intact."""
    from routes.operational_locations import LOCATION_TYPES
    assert LOCATION_TYPES == {
        "JOB", "ASPHALT_PLANT", "CONCRETE_PLANT", "PIT",
        "YARD", "SHOP", "DISPOSAL_SITE", "VENDOR",
    }


def test_geocode_statuses_enum_complete():
    from routes.operational_locations import GEOCODE_STATUSES
    assert GEOCODE_STATUSES == {
        "Not Geocoded", "Imported", "Matched", "Verified", "Rejected",
    }

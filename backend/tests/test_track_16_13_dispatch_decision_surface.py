"""TRACK 16.13 · Dispatch Decision Surface regression."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path("/app")
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

ROUTE = BACKEND / "routes" / "dispatch_decision_surface.py"
SERVER = BACKEND / "server.py"
FE_CHIP = ROOT / "frontend" / "src" / "components" / "dispatch" / "DispatchDecisionChip.jsx"
FE_DRAWER = ROOT / "frontend" / "src" / "components" / "dispatch" / "AssignmentDrawer.jsx"
GATE = ROOT / "scripts" / "deployment_gate.py"


# ---- minimal fake DB (reused pattern) ------------------------------------
def _matches(row: Dict[str, Any], q: Dict[str, Any]) -> bool:
    for k, v in (q or {}).items():
        if k == "$or":
            if not any(_matches(row, sub) for sub in v):
                return False
            continue
        if isinstance(v, dict) and "$in" in v:
            if row.get(k) not in v["$in"]:
                return False
            continue
        if row.get(k) != v:
            return False
    return True


class _Cur:
    def __init__(self, items): self._items = list(items)
    def sort(self, *_, **__): return self
    def limit(self, _): return self
    async def to_list(self, _=None): return list(self._items)


class _Coll:
    def __init__(self): self.rows: List[Dict[str, Any]] = []
    def find(self, q=None, *_, **__):
        return _Cur([r for r in self.rows if _matches(r, q or {})])
    async def find_one(self, q=None, *_, **kwargs):
        rows = [r for r in self.rows if _matches(r, q or {})]
        return rows[0] if rows else None
    async def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = f"_id_{len(self.rows)}"
        self.rows.append(doc)
        return type("R", (), {"inserted_id": doc["_id"]})()
    async def update_one(self, q, update, upsert=False):
        for r in self.rows:
            if _matches(r, q or {}):
                if "$set" in update:
                    r.update(update["$set"])
                return type("R", (), {"matched_count": 1})()
        if upsert:
            doc = dict((update or {}).get("$set", {}))
            doc.update((update or {}).get("$setOnInsert", {}))
            doc.update(q or {})
            await self.insert_one(doc)
        return type("R", (), {"matched_count": 0})()


class _DB:
    def __init__(self): self._c: Dict[str, _Coll] = {}
    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._c:
            self._c[name] = _Coll()
        return self._c[name]
    def __getitem__(self, k): return getattr(self, k)


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _seed_driver(db, *, did="tp-1", elig="eligible", carrier_id=None):
    from datetime import datetime, timezone, timedelta
    db.transport_persons.rows.append({
        "_id": f"_id_{did}", "id": did, "tenant": "masci",
        "kind": "masci_employee", "employee_id": "E1",
        "carrier_id": carrier_id,
        "first_name": "Jane", "last_name": "Driver", "status": "active",
    })
    db.transport_eligibility_state.rows.append({
        "tenant": "masci", "target_type": "person",
        "target_id": did, "state": elig, "reasons": [],
        "computed_at": "2026-02-09T12:00:00+00:00",
    })
    if elig == "eligible":
        future = (datetime.now(timezone.utc) + timedelta(days=120)).isoformat()
        db.transport_certificates.rows.append({
            "id": f"cert-{did}", "tenant": "masci",
            "transport_person_id": did,
            "issued_at": "2026-01-01T00:00:00+00:00",
            "expires_at": future,
        })


def _seed_carrier(db, *, cid="c-1"):
    db.carriers.rows.append({
        "_id": f"_id_{cid}", "id": cid, "tenant": "masci",
        "legal_name": "Coastal Hauling", "carrier_type": "leased_hauler",
        "status": "active", "safety_hold": False,
        "created_at": "2024-01-01T00:00:00+00:00",
    })
    db.transport_carrier_packets.rows.append({
        "tenant": "masci", "carrier_id": cid, "status": "approved",
        "rate_acknowledged": True,
    })


def _seed_truck(db, *, tid="t-1", elig="eligible", carrier_id="c-1"):
    db.transport_trucks.rows.append({
        "_id": f"_id_{tid}", "id": tid, "tenant": "masci",
        "truck_number": "T-100", "truck_type": "dump_truck",
        "ownership": "leased_carrier", "carrier_id": carrier_id,
        "status": "active", "safety_hold": False,
    })
    db.transport_eligibility_state.rows.append({
        "tenant": "masci", "target_type": "truck",
        "target_id": tid, "state": elig, "reasons": [],
        "computed_at": "2026-02-09T12:00:00+00:00",
    })
    db.transport_truck_inspections.rows.append({
        "id": f"insp-{tid}", "tenant": "masci",
        "transport_truck_id": tid, "result": "ready" if elig == "eligible" else "not_ready",
        "inspected_at": "2026-02-01T00:00:00+00:00",
    })


def _build_app():
    """Build a tiny FastAPI app + register Track 16.13 routes with a
    stub dispatch_or_admin dependency that captures the actor."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from routes.dispatch_decision_surface import register_track_16_13_routes
    app = FastAPI()
    db = _DB()

    async def fake_auth():
        return {"role": "dispatch", "email": "dispatcher@masci",
                "id": "user-1"}

    register_track_16_13_routes(app, db,
                                 require_dispatch_or_admin_dep=fake_auth)
    client = TestClient(app)
    return app, db, client


# ===========================================================================
# 1 — Endpoint exists
# ===========================================================================
def test_01_endpoint_exists():
    src = ROUTE.read_text()
    assert "/recommendation" in src
    assert "/recommendation/audit" in src


# ===========================================================================
# 2 — Endpoint is read-only GET (only audit is POST)
# ===========================================================================
def test_02_endpoint_read_only_get():
    src = ROUTE.read_text()
    assert '@router.get("/recommendation")' in src
    # Only POST should be on /recommendation/audit
    assert '@router.post("/recommendation/audit")' in src
    # No PATCH/DELETE/PUT.
    for verb in ("@router.patch", "@router.delete", "@router.put"):
        assert verb not in src


# ===========================================================================
# 3 + 4 — Admin and dispatch tokens both pass via shared dependency
# ===========================================================================
def test_03_admin_and_dispatch_accept_via_shared_dep():
    src = ROUTE.read_text()
    assert "require_dispatch_or_admin_dep" in src
    # Both GET and POST handlers depend on the shared gate.
    assert src.count("Depends(require_dispatch_or_admin_dep)") >= 2


def test_04_anonymous_blocked_when_dependency_raises():
    """Verify that when the dependency raises, the route returns 401."""
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
    from routes.dispatch_decision_surface import register_track_16_13_routes
    app = FastAPI()
    db = _DB()

    async def boom():
        raise HTTPException(401, "Login required")

    register_track_16_13_routes(app, db,
                                 require_dispatch_or_admin_dep=boom)
    client = TestClient(app)
    r = client.get("/api/dispatch/transportation/recommendation")
    assert r.status_code == 401


# ===========================================================================
# 5 — Uses the existing recommendation engine
# ===========================================================================
def test_05_uses_recommendation_engine():
    src = ROUTE.read_text()
    assert "from lib.transport_recommendation_engine import" in src
    assert "recommend_dispatch_triple" in src


# ===========================================================================
# 6 — No duplicated scoring logic introduced in the route file
# ===========================================================================
def test_06_no_duplicated_scoring_logic():
    src = ROUTE.read_text()
    forbidden = ("def compute_driver_intelligence",
                  "def compute_carrier_intelligence",
                  "def compute_truck_intelligence",
                  "def composite(", "def grade(")
    for f in forbidden:
        assert f not in src, f"Route file must not redefine: {f}"


# ===========================================================================
# 7 — Excludes non-dispatchable options from the ranked alternatives
# ===========================================================================
def test_07_excludes_non_dispatchable():
    _, db, client = _build_app()
    _seed_driver(db, did="tp-eligible", elig="eligible")
    _seed_driver(db, did="tp-blocked", elig="not_dispatchable")
    _seed_carrier(db)
    _seed_truck(db)
    r = client.get("/api/dispatch/transportation/recommendation?limit=5")
    body = r.json()
    assert body["ok"] is True
    alt_driver_ids = {d["driver_id"] for d in body["alternatives"]["drivers"]}
    assert "tp-eligible" in alt_driver_ids
    assert "tp-blocked" not in alt_driver_ids


# ===========================================================================
# 8 — Excluded options include reason labels
# ===========================================================================
def test_08_excluded_carries_reason_labels():
    _, db, client = _build_app()
    _seed_driver(db, did="tp-blocked", elig="not_dispatchable")
    db.transport_eligibility_state.rows[0]["reasons"] = [
        {"code": "hr_status_terminated", "label": "Employee is terminated in HR"},
    ]
    r = client.get("/api/dispatch/transportation/recommendation")
    body = r.json()
    excluded_drivers = body["excluded"]["drivers"]
    assert excluded_drivers
    assert excluded_drivers[0]["reasons"][0]["label"]


# ===========================================================================
# 9 — Returns recommended triple
# ===========================================================================
def test_09_returns_recommended_triple():
    _, db, client = _build_app()
    _seed_driver(db)
    _seed_carrier(db)
    _seed_truck(db)
    body = client.get(
        "/api/dispatch/transportation/recommendation").json()
    assert body["recommended"]["driver"]
    assert body["recommended"]["carrier"]
    assert body["recommended"]["truck"]


# ===========================================================================
# 10 — Returns alternatives list
# ===========================================================================
def test_10_returns_alternatives():
    _, db, client = _build_app()
    _seed_driver(db)
    _seed_carrier(db)
    _seed_truck(db)
    body = client.get(
        "/api/dispatch/transportation/recommendation").json()
    for k in ("drivers", "carriers", "trucks"):
        assert k in body["alternatives"]


# ===========================================================================
# 11 — Returns why[] and watch[]
# ===========================================================================
def test_11_returns_why_and_watch():
    _, db, client = _build_app()
    _seed_driver(db)
    _seed_carrier(db)
    _seed_truck(db)
    body = client.get(
        "/api/dispatch/transportation/recommendation").json()
    rec = body["recommended"]
    assert "why" in rec and isinstance(rec["why"], list)
    assert "watch" in rec and isinstance(rec["watch"], list)


# ===========================================================================
# 12 — Schema version is 16.13.0
# ===========================================================================
def test_12_schema_version():
    _, db, client = _build_app()
    body = client.get(
        "/api/dispatch/transportation/recommendation").json()
    assert body["schema_version"] == "16.13.0"


# ===========================================================================
# 13 — Audit row written when recommendation generated
# ===========================================================================
def test_13_audit_recommendation_generated():
    _, db, client = _build_app()
    _seed_driver(db)
    _seed_carrier(db)
    _seed_truck(db)
    client.get("/api/dispatch/transportation/recommendation")
    kinds = [r.get("kind") for r in
              db.transport_dispatch_recommendation_audit.rows]
    assert "transport_dispatch_recommendation_generated" in kinds


# ===========================================================================
# 14 — Viewed audit event
# ===========================================================================
def test_14_audit_viewed():
    _, db, client = _build_app()
    r = client.post(
        "/api/dispatch/transportation/recommendation/audit",
        json={"event": "viewed", "recommendation_id": "rid-1"})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    kinds = [r.get("kind") for r in
              db.transport_dispatch_recommendation_audit.rows]
    assert "transport_dispatch_recommendation_viewed" in kinds


# ===========================================================================
# 15 — Selected audit event
# ===========================================================================
def test_15_audit_selected():
    _, db, client = _build_app()
    client.post("/api/dispatch/transportation/recommendation/audit",
                 json={"event": "selected", "driver_id": "tp-1"})
    kinds = [r.get("kind") for r in
              db.transport_dispatch_recommendation_audit.rows]
    assert "transport_dispatch_recommendation_selected" in kinds


# ===========================================================================
# 16 — Non-recommended eligible selection audit event
# ===========================================================================
def test_16_audit_non_recommended_selected():
    _, db, client = _build_app()
    client.post("/api/dispatch/transportation/recommendation/audit",
                 json={"event": "non_recommended_selected",
                        "selected_driver_id": "tp-other",
                        "note": "operator preference"})
    kinds = [r.get("kind") for r in
              db.transport_dispatch_recommendation_audit.rows]
    assert "transport_dispatch_non_recommended_selected" in kinds


# ===========================================================================
# 17 — Ignored audit event
# ===========================================================================
def test_17_audit_ignored():
    _, db, client = _build_app()
    client.post("/api/dispatch/transportation/recommendation/audit",
                 json={"event": "ignored"})
    kinds = [r.get("kind") for r in
              db.transport_dispatch_recommendation_audit.rows]
    assert "transport_dispatch_recommendation_ignored" in kinds


# ===========================================================================
# 18 — Invalid audit event rejected
# ===========================================================================
def test_18_audit_invalid_event_rejected():
    _, _, client = _build_app()
    r = client.post("/api/dispatch/transportation/recommendation/audit",
                     json={"event": "deleted"})
    assert r.status_code in (400, 422)


# ===========================================================================
# 19 — Note length capped at 500 chars
# ===========================================================================
def test_19_note_length_capped():
    _, _, client = _build_app()
    r = client.post("/api/dispatch/transportation/recommendation/audit",
                     json={"event": "ignored", "note": "x" * 501})
    assert r.status_code in (400, 422)


# ===========================================================================
# 20 — Engine unavailable: still returns ok=false + fallback message
# ===========================================================================
def test_20_engine_unavailable_does_not_block():
    """Simulate engine failure by passing a DB that raises on the
    recommendation engine's collection access. Endpoint must return a
    graceful payload."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from routes.dispatch_decision_surface import register_track_16_13_routes

    class _BoomDB:
        def __getattr__(self, _name):
            raise RuntimeError("boom")
        def __getitem__(self, _k):
            raise RuntimeError("boom")

    app = FastAPI()

    async def auth():
        return {"role": "dispatch"}

    register_track_16_13_routes(app, _BoomDB(),
                                 require_dispatch_or_admin_dep=auth)
    r = TestClient(app).get(
        "/api/dispatch/transportation/recommendation")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert "standard eligibility gate" in body["message"]


# ===========================================================================
# 21 — Frontend chip component exists
# ===========================================================================
def test_21_frontend_chip_exists():
    assert FE_CHIP.exists()
    src = FE_CHIP.read_text()
    assert "DispatchDecisionChip" in src
    assert "dispatch-decision-chip" in src


# ===========================================================================
# 22 — Frontend Why drawer exists
# ===========================================================================
def test_22_frontend_why_drawer_exists():
    src = FE_CHIP.read_text()
    assert "dispatch-decision-why-drawer" in src
    assert "Why this recommendation" in src


# ===========================================================================
# 23 — Frontend alternatives list rendered
# ===========================================================================
def test_23_frontend_alternatives_rendered():
    src = FE_CHIP.read_text()
    assert "dispatch-decision-alt-drivers" in src
    assert "dispatch-decision-alt-trucks" in src
    assert "dispatch-decision-alt-carriers" in src


# ===========================================================================
# 24 — Frontend excluded section rendered
# ===========================================================================
def test_24_frontend_excluded_section():
    src = FE_CHIP.read_text()
    assert "dispatch-decision-excluded" in src


# ===========================================================================
# 25 — Selecting alternative populates assignment fields via callback
# ===========================================================================
def test_25_alternative_selection_populates_fields():
    drawer_src = FE_DRAWER.read_text()
    # Drawer wires the chip with an onSelectRecommendation callback that
    # writes into setNewDriverId / setNewTruckId.
    assert "DispatchDecisionChip" in drawer_src
    assert "setNewDriverId(triple.driver.driver_id)" in drawer_src
    assert "setNewTruckId(triple.truck.truck_id)" in drawer_src


# ===========================================================================
# 26 — Final assignment still respects Track 16.09 gate (no bypass)
# ===========================================================================
def test_26_no_dispatch_gate_bypass():
    """The chip/drawer file MUST NOT introduce any direct write to
    dispatch eligibility or bypass the existing assignment POST."""
    src = FE_CHIP.read_text()
    for forbidden in ("/api/dispatch/assignments",
                       "PATCH",
                       "method: \"DELETE\"",
                       "eligibility_state",
                       "transport_eligibility_state"):
        assert forbidden not in src, \
            f"Decision surface must not write dispatch: {forbidden}"


# ===========================================================================
# 27 — No new blocking logic introduced in the route file
# ===========================================================================
def test_27_no_new_blocking_logic():
    src = ROUTE.read_text()
    # No HARD HTTP 403 / "blocked" payloads — recommendations never block.
    for forbidden in ("HTTPException(403", "block_reasons",
                       "block_envelope"):
        assert forbidden not in src


# ===========================================================================
# 28 — No SMS / Twilio / push references
# ===========================================================================
def test_28_no_sms_or_push():
    for p in (ROUTE, FE_CHIP):
        src = p.read_text()
        for forbidden in ("twilio", "TWILIO", "sendSms",
                           "push_notification", "fcm.googleapis"):
            assert forbidden not in src, f"{p.name}: {forbidden}"


# ===========================================================================
# 29 — No punitive vocabulary in user-facing strings
# ===========================================================================
def test_29_no_punitive_language():
    for p in (ROUTE, FE_CHIP):
        src = p.read_text()
        for forbidden in ("Rejected", "Denied", "Failed —",
                           "rejected!", "denied!"):
            assert forbidden not in src, f"{p.name}: {forbidden}"


# ===========================================================================
# 30 — Router wired into server.py
# ===========================================================================
def test_30_router_registered_in_server():
    src = SERVER.read_text()
    assert "register_track_16_13_routes" in src
    assert "dispatch_decision_surface" in src


# ===========================================================================
# 31 — Deployment gate includes Track 16.13 tests
# ===========================================================================
def test_31_deployment_gate_includes_track_16_13():
    src = GATE.read_text()
    assert "test_track_16_13_dispatch_decision_surface" in src


# ===========================================================================
# 32 — Prior transport tracks preserved in deployment gate
# ===========================================================================
def test_32_prior_tracks_preserved_in_gate():
    src = GATE.read_text()
    for f in (
        "test_track_16_12_transport_operations_intelligence",
        "test_track_16_11A_transport_sync_monitor",
        "test_track_16_11_transport_hr_lifecycle_integration",
        "test_track_16_10a_transport_command_digest",
        "test_track_16_10_transportation_automation_engine",
        "test_track_16_09_transportation_dispatch_gate_email_pilot",
    ):
        assert f in src

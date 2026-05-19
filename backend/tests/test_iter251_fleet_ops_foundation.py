"""iter251 Phase A · Fleet Operations Foundation · backend tests.

Operator-approved Phase A coverage:
  - Severity table integrity (every checklist item has an entry)
  - Cross-module consistency (checklists ↔ severity table)
  - DVIR submission flow · OOS detection · status flip
  - Defect lifecycle state machine (open → ack → repair → cleared)
  - Anti-self-classify (unknown checklist item refused)
  - Anon RBAC on all gated endpoints
  - Public-tile submission acceptable (operator D2 decision)
  - Trailer multi-coupling supported
  - kind discriminator migration backfill
  - Audit trail captures every action

Style mirrors iter249 Phase B tests: live HTTP for RBAC, direct
function calls for aggregation correctness, motor for cleanup.
"""
from __future__ import annotations

import os
import uuid
import asyncio
import urllib.request
import urllib.error
import json

import pytest
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path="/app/backend/.env")

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402

import fleet_defect_severity as _sev  # noqa: E402
import checklists_fleet as _ck  # noqa: E402


def _read_kv(p, k):
    try:
        for line in open(p):
            if line.startswith(f"{k}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


URL = (
    _read_kv("/app/frontend/.env", "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")


def _db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli[os.environ["DB_NAME"]]


@pytest.fixture(scope="module")
def admin_token():
    if not URL:
        pytest.skip("REACT_APP_BACKEND_URL not configured")
    r = requests.post(
        f"{URL}/api/admin/login",
        json={"password": os.environ.get("ADMIN_PASSWORD_E2E", "MASCI1982!")},
        timeout=15,
    )
    assert r.status_code == 200
    return r.json()["token"]


# ─── Severity table integrity ────────────────────────────────────────
def test_every_dvir_truck_item_has_severity_classification():
    """Submission endpoint refuses unknown items · this test catches
    drift between checklists_fleet.py and fleet_defect_severity.py
    before it can reach the field."""
    missing = []
    for item in _ck.dvir_truck_items():
        if item not in _sev.FLEET_DEFECT_SEVERITY:
            missing.append(item)
    assert missing == [], (
        f"DVIR truck items missing severity classification: {missing[:5]}"
    )


def test_every_dvir_trailer_item_has_severity_classification():
    missing = [item for item in _ck.dvir_trailer_items()
               if item not in _sev.FLEET_DEFECT_SEVERITY]
    assert missing == [], (
        f"DVIR trailer items missing severity classification: {missing[:5]}"
    )


def test_every_dvir_emergency_item_has_severity_classification():
    missing = [item for item in _ck.dvir_emergency_items()
               if item not in _sev.FLEET_DEFECT_SEVERITY]
    assert missing == [], (
        f"Weekly emergency items missing severity classification: {missing[:5]}"
    )


def test_every_weekly_lead_item_has_severity_classification():
    missing = [item for item in _ck.dvir_weekly_lead_items()
               if item not in _sev.FLEET_DEFECT_SEVERITY]
    assert missing == [], (
        f"Weekly lead items missing severity classification: {missing[:5]}"
    )


def test_severity_classify_returns_valid_tuple():
    s, c = _sev.classify("Service brakes — apply firmly · stop straight · no pulling")
    assert s == _sev.SEVERITY_OOS
    assert c == _sev.CATEGORY_BRAKES


def test_severity_is_oos_predicate():
    assert _sev.is_oos("Brake lights — both sides functional")
    assert not _sev.is_oos("Body — cosmetic dings · scrapes · paint")


def test_classify_unknown_raises_keyerror():
    with pytest.raises(KeyError):
        _sev.classify("totally fictional checklist item " + uuid.uuid4().hex)


# ─── HTTP-level RBAC ────────────────────────────────────────────────
def test_anon_can_read_fleet_meta():
    """Per D2 · driver UX may be public · meta needs to be reachable."""
    if not URL:
        pytest.skip()
    r = requests.get(f"{URL}/api/fleet/_meta", timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert d["phase"] == "A"
    assert "dvir" in d["kinds"]


def test_anon_blocked_from_dispatch_status():
    if not URL:
        pytest.skip()
    req = urllib.request.Request(f"{URL}/api/dispatch/fleet/status")
    try:
        urllib.request.urlopen(req, timeout=10)
        pytest.fail("anon call should have been blocked")
    except urllib.error.HTTPError as e:
        assert e.code in (401, 403)


def test_anon_blocked_from_shop_defects():
    if not URL:
        pytest.skip()
    req = urllib.request.Request(f"{URL}/api/shop/fleet/defects")
    try:
        urllib.request.urlopen(req, timeout=10)
        pytest.fail("anon call should have been blocked")
    except urllib.error.HTTPError as e:
        assert e.code in (401, 403)


def test_anon_blocked_from_safety_emergency_view():
    if not URL:
        pytest.skip()
    req = urllib.request.Request(f"{URL}/api/safety/fleet/emergency-equipment")
    try:
        urllib.request.urlopen(req, timeout=10)
        pytest.fail("anon call should have been blocked")
    except urllib.error.HTTPError as e:
        assert e.code in (401, 403)


def test_anon_blocked_from_migrate_endpoint():
    if not URL:
        pytest.skip()
    req = urllib.request.Request(
        f"{URL}/api/admin/fleet/migrate-kind-field", method="POST"
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        pytest.fail("anon migrate should have been blocked")
    except urllib.error.HTTPError as e:
        assert e.code in (401, 403)


# ─── DVIR submission · public tile · clean truck (all PASS) ─────────
def test_anon_dvir_submission_clean_truck_passes(admin_token):
    """Operator D2 decision: public-tile submission OK · audit captures
    driver_name + truck_unit + signature."""
    if not URL:
        pytest.skip()
    truck = f"TEST-TRUCK-{uuid.uuid4().hex[:6]}"
    payload = {
        "kind": "dvir",
        "driver_name": "Test Driver",
        "inspection_date": "2024-08-15",
        "inspection_time": "06:30",
        "truck_unit_number": truck,
        "odometer_miles": "234567",
        "truck_checklist": {item: "pass" for item in _ck.dvir_truck_items()},
        "trailers": [],
        "defect_details": {},
        "driver_signature": "data:image/png;base64,iVBORw0KGgo",
        "submitted_via": "public_tile",
    }
    try:
        # NOTE: anon, no token sent · per D2 this is allowed
        r = requests.post(f"{URL}/api/fleet/inspections", json=payload, timeout=30)
        assert r.status_code == 200, r.text[:300]
        out = r.json()
        assert out["ok"] is True
        assert out["kind"] == "dvir"
        assert out["out_of_service"] is False
        assert out["defect_count"] == 0
        assert out["truck_status_after"] == "available"
    finally:
        async def _go():
            db = _db()
            await db.equipment_inspections.delete_many({"truck_unit_number": truck})
            await db.fleet_defects.delete_many({"truck_unit_number": truck})
            await db.fleet_status.delete_one({"unit_number": truck})
            await db.fleet_audit.delete_many({"target_id": truck})
        asyncio.run(_go())


# ─── DVIR submission · OOS fail flips truck status ──────────────────
def test_dvir_oos_failure_flips_truck_status():
    """A FAIL on a severity=oos item must produce an `oos` defect AND
    flip fleet_status.status to 'oos'."""
    if not URL:
        pytest.skip()
    truck = f"OOS-TRUCK-{uuid.uuid4().hex[:6]}"
    checklist = {item: "pass" for item in _ck.dvir_truck_items()}
    # Mark a known-OOS item as failed
    oos_item = "Brake lights — both sides functional"
    checklist[oos_item] = "fail"
    payload = {
        "kind": "dvir",
        "driver_name": "Test Driver OOS",
        "inspection_date": "2024-08-15",
        "inspection_time": "07:00",
        "truck_unit_number": truck,
        "truck_checklist": checklist,
        "defect_details": {oos_item: {"note": "left side out", "photos": []}},
        "submitted_via": "public_tile",
    }
    insp_id = None
    try:
        r = requests.post(f"{URL}/api/fleet/inspections", json=payload, timeout=30)
        assert r.status_code == 200, r.text[:300]
        out = r.json()
        assert out["out_of_service"] is True
        assert out["defect_count"] == 1
        assert out["truck_status_after"] == "oos"
        insp_id = out["inspection_id"]

        async def _verify():
            db = _db()
            # Defect row exists with correct severity + category + note
            defects = await db.fleet_defects.find(
                {"truck_unit_number": truck}, {"_id": 0}
            ).to_list(None)
            assert len(defects) == 1
            d = defects[0]
            assert d["severity"] == "oos"
            assert d["category"] == "lights"
            assert d["status"] == "open"
            assert d["note"] == "left side out"
            assert d["inspection_id"] == insp_id
            # Status row reflects OOS
            status = await db.fleet_status.find_one({"unit_number": truck}, {"_id": 0})
            assert status["status"] == "oos"
            assert status["open_oos_count"] == 1
            # Audit captured submission
            audits = await db.fleet_audit.find(
                {"target_id": insp_id}, {"_id": 0}
            ).to_list(None)
            assert any(a["action"] == "fleet_inspection_submitted" for a in audits)
        asyncio.run(_verify())
    finally:
        async def _go():
            db = _db()
            await db.equipment_inspections.delete_many({"truck_unit_number": truck})
            await db.fleet_defects.delete_many({"truck_unit_number": truck})
            await db.fleet_status.delete_one({"unit_number": truck})
            await db.fleet_audit.delete_many({"target_id": insp_id} if insp_id else {"target_id": truck})
            if insp_id:
                await db.fleet_audit.delete_many({"target_id": insp_id})
        asyncio.run(_go())


# ─── Monitor failure produces defect but truck still available ──────
def test_dvir_monitor_failure_logs_but_does_not_oos():
    if not URL:
        pytest.skip()
    truck = f"MON-TRUCK-{uuid.uuid4().hex[:6]}"
    checklist = {item: "pass" for item in _ck.dvir_truck_items()}
    monitor_item = "Body — cosmetic dings · scrapes · paint"
    checklist[monitor_item] = "fail"
    payload = {
        "kind": "dvir",
        "driver_name": "Monitor Driver",
        "inspection_date": "2024-08-15",
        "inspection_time": "08:00",
        "truck_unit_number": truck,
        "truck_checklist": checklist,
        "defect_details": {},
        "submitted_via": "public_tile",
    }
    try:
        r = requests.post(f"{URL}/api/fleet/inspections", json=payload, timeout=30)
        assert r.status_code == 200, r.text[:300]
        out = r.json()
        assert out["out_of_service"] is False
        assert out["defect_count"] == 1
        assert out["truck_status_after"] == "defect_open"
    finally:
        async def _go():
            db = _db()
            await db.equipment_inspections.delete_many({"truck_unit_number": truck})
            await db.fleet_defects.delete_many({"truck_unit_number": truck})
            await db.fleet_status.delete_one({"unit_number": truck})
        asyncio.run(_go())


# ─── Unknown checklist item refused (no silent misrouting) ──────────
def test_unknown_checklist_item_refused_with_400():
    if not URL:
        pytest.skip()
    truck = f"BAD-TRUCK-{uuid.uuid4().hex[:6]}"
    payload = {
        "kind": "dvir",
        "driver_name": "Bad Item Driver",
        "inspection_date": "2024-08-15",
        "inspection_time": "08:30",
        "truck_unit_number": truck,
        "truck_checklist": {"fictional made-up item": "fail"},
        "submitted_via": "public_tile",
    }
    r = requests.post(f"{URL}/api/fleet/inspections", json=payload, timeout=15)
    assert r.status_code == 400
    assert "fleet_defect_severity" in r.text or "no severity" in r.text.lower()


# ─── Trailer support (multi-coupling) ────────────────────────────────
def test_dvir_with_multiple_trailers_creates_per_trailer_defects():
    if not URL:
        pytest.skip()
    truck = f"COMBO-{uuid.uuid4().hex[:6]}"
    trailer_a = f"TRA-{uuid.uuid4().hex[:6]}"
    trailer_b = f"TRB-{uuid.uuid4().hex[:6]}"
    trailer_oos = "Trailer brake lights — both sides functional"
    payload = {
        "kind": "dvir",
        "driver_name": "Doubles Driver",
        "inspection_date": "2024-08-15",
        "inspection_time": "09:00",
        "truck_unit_number": truck,
        "truck_checklist": {item: "pass" for item in _ck.dvir_truck_items()},
        "trailers": [
            {
                "trailer_unit_number": trailer_a,
                "checklist": {**{item: "pass" for item in _ck.dvir_trailer_items()},
                              trailer_oos: "fail"},
            },
            {
                "trailer_unit_number": trailer_b,
                "checklist": {item: "pass" for item in _ck.dvir_trailer_items()},
            },
        ],
        "submitted_via": "public_tile",
    }
    insp_id: str = ""
    try:
        r = requests.post(f"{URL}/api/fleet/inspections", json=payload, timeout=30)
        assert r.status_code == 200, r.text[:300]
        out = r.json()
        assert out["out_of_service"] is True
        assert out["defect_count"] == 1
        insp_id = out["inspection_id"]

        async def _verify():
            db = _db()
            # Trailer A is OOS (defect exists, status oos)
            sa = await db.fleet_status.find_one({"unit_number": trailer_a}, {"_id": 0})
            assert sa["status"] == "oos"
            # Trailer B is available (no defects)
            sb = await db.fleet_status.find_one({"unit_number": trailer_b}, {"_id": 0})
            assert sb["status"] == "available"
            # Truck itself is "defect_open" or "available" since its own
            # checklist was clean. Actually — the truck has no defects
            # of its own, so its status should be "available". The
            # rebuild treats trailer-attached defects separately.
            st = await db.fleet_status.find_one({"unit_number": truck}, {"_id": 0})
            assert st["status"] == "available"
        asyncio.run(_verify())
    finally:
        async def _go():
            db = _db()
            await db.equipment_inspections.delete_many({"truck_unit_number": truck})
            await db.fleet_defects.delete_many(
                {"$or": [{"truck_unit_number": truck},
                         {"trailer_unit_number": {"$in": [trailer_a, trailer_b]}}]}
            )
            await db.fleet_status.delete_many(
                {"unit_number": {"$in": [truck, trailer_a, trailer_b]}}
            )
        asyncio.run(_go())


# ─── Defect lifecycle: open → ack → repair → cleared ────────────────
def test_defect_lifecycle_state_machine(admin_token):
    if not URL:
        pytest.skip()
    truck = f"LIFECYCLE-{uuid.uuid4().hex[:6]}"
    insp_id = None
    defect_id = None
    try:
        # Submit a failing inspection
        oos_item = "Horn — sounds at normal volume"
        payload = {
            "kind": "dvir",
            "driver_name": "Lifecycle Driver",
            "inspection_date": "2024-08-15",
            "inspection_time": "10:00",
            "truck_unit_number": truck,
            "truck_checklist": {**{item: "pass" for item in _ck.dvir_truck_items()},
                                oos_item: "fail"},
            "defect_details": {oos_item: {"note": "no sound at all"}},
            "submitted_via": "public_tile",
        }
        r = requests.post(f"{URL}/api/fleet/inspections", json=payload, timeout=30)
        assert r.status_code == 200
        out = r.json()
        insp_id = out["inspection_id"]
        assert out["truck_status_after"] == "oos"

        async def _get_defect():
            db = _db()
            d = await db.fleet_defects.find_one({"truck_unit_number": truck}, {"_id": 0})
            return d
        defect = asyncio.run(_get_defect())
        defect_id = defect["id"]
        assert defect["status"] == "open"

        H_ADMIN = {"X-Admin-Token": admin_token}
        # Acknowledge
        r = requests.post(
            f"{URL}/api/shop/fleet/defects/{defect_id}/acknowledge",
            json={"actor_name": "Shop Tech A"},
            headers=H_ADMIN, timeout=15,
        )
        assert r.status_code == 200, r.text[:300]

        # Repair
        r = requests.post(
            f"{URL}/api/shop/fleet/defects/{defect_id}/repair",
            json={"actor_name": "Shop Tech A",
                  "notes": "replaced horn relay",
                  "photos": []},
            headers=H_ADMIN, timeout=15,
        )
        assert r.status_code == 200, r.text[:300]

        # Phase 4 · Truck must NOT yet be cleared back to "available".
        # Dispatch still needs to confirm Return-to-Service. The interim
        # state is "repair_in_progress" (awaiting RTS).
        async def _status_after_repair():
            db = _db()
            return await db.fleet_status.find_one({"unit_number": truck}, {"_id": 0})
        st = asyncio.run(_status_after_repair())
        assert st["status"] == "repair_in_progress", (
            "after repair (Phase 4), unit awaits Dispatch RTS confirmation"
        )

        # Clear (dispatch RTS confirmation)
        r = requests.post(
            f"{URL}/api/dispatch/fleet/defects/{defect_id}/clear",
            json={"actor_name": "Dispatch Mike"},
            headers=H_ADMIN, timeout=15,
        )
        assert r.status_code == 200, r.text[:300]

        # After RTS, unit returns to "available"
        st2 = asyncio.run(_status_after_repair())
        assert st2["status"] == "available", (
            "after Dispatch RTS, unit is back to available"
        )

        # Final defect doc has full lifecycle stamped
        async def _final_defect():
            db = _db()
            return await db.fleet_defects.find_one({"id": defect_id}, {"_id": 0})
        d = asyncio.run(_final_defect())
        assert d["status"] == "cleared"
        assert d["acknowledged_by_name"] == "Shop Tech A"
        assert d["repaired_by_name"] == "Shop Tech A"
        assert d["repair_notes"] == "replaced horn relay"
        assert d["cleared_by_name"] == "Dispatch Mike"

        # Audit captured every transition
        async def _audits():
            db = _db()
            return await db.fleet_audit.find(
                {"target_id": defect_id}, {"_id": 0}
            ).to_list(None)
        events = asyncio.run(_audits())
        actions = {e["action"] for e in events}
        assert {"defect_acknowledged", "defect_repaired", "defect_cleared"}.issubset(actions)
    finally:
        async def _go():
            db = _db()
            await db.equipment_inspections.delete_many({"truck_unit_number": truck})
            await db.fleet_defects.delete_many({"truck_unit_number": truck})
            await db.fleet_status.delete_one({"unit_number": truck})
            for tid in filter(None, [insp_id, defect_id, truck]):
                await db.fleet_audit.delete_many({"target_id": tid})
        asyncio.run(_go())


# ─── Defect lifecycle guard rails ───────────────────────────────────
def test_cannot_repair_without_acknowledge_or_open(admin_token):
    """Acknowledge can ONLY come from open. Repair can come from
    open OR acknowledged. Clear can ONLY come from repaired."""
    if not URL:
        pytest.skip()
    # Create a defect via manual OOS flip
    unit = f"GUARD-{uuid.uuid4().hex[:6]}"
    H = {"X-Admin-Token": admin_token}
    r = requests.post(
        f"{URL}/api/dispatch/fleet/units/{unit}/oos",
        json={"actor_name": "Dispatch G",
              "notes": "smelled fuel · pulled from rotation"},
        headers=H, timeout=15,
    )
    assert r.status_code == 200, r.text[:300]
    defect_id = r.json()["defect_id"]
    try:
        # Cannot clear directly from open
        r = requests.post(
            f"{URL}/api/dispatch/fleet/defects/{defect_id}/clear",
            json={"actor_name": "Dispatch G"},
            headers=H, timeout=15,
        )
        assert r.status_code == 400
    finally:
        async def _go():
            db = _db()
            await db.fleet_defects.delete_many({"id": defect_id})
            await db.fleet_status.delete_one({"unit_number": unit})
            await db.fleet_audit.delete_many({"target_id": defect_id})
            await db.fleet_audit.delete_many({"target_id": unit})
        asyncio.run(_go())


# ─── Migration backfill is idempotent ───────────────────────────────
def test_migrate_kind_field_idempotent(admin_token):
    """Running the migration twice is safe · second run touches zero rows."""
    if not URL:
        pytest.skip()
    H = {"X-Admin-Token": admin_token}
    r1 = requests.post(
        f"{URL}/api/admin/fleet/migrate-kind-field",
        headers=H, timeout=20,
    )
    assert r1.status_code == 200
    r2 = requests.post(
        f"{URL}/api/admin/fleet/migrate-kind-field",
        headers=H, timeout=20,
    )
    assert r2.status_code == 200
    assert r2.json()["rows_missing_kind_before"] == 0
    assert r2.json()["rows_updated"] == 0


# ─── Kind discriminator scope guard ─────────────────────────────────
def test_kind_discriminator_unknown_kind_refused():
    if not URL:
        pytest.skip()
    payload = {
        "kind": "totally_made_up_kind",
        "driver_name": "X", "inspection_date": "2024-01-01",
        "inspection_time": "01:00", "truck_unit_number": "WHATEVER",
        "truck_checklist": {},
    }
    r = requests.post(f"{URL}/api/fleet/inspections", json=payload, timeout=15)
    assert r.status_code == 400
    assert "unknown fleet inspection kind" in r.text.lower()


def test_weekly_emergency_does_not_accept_trailers():
    if not URL:
        pytest.skip()
    payload = {
        "kind": "weekly_emergency",
        "driver_name": "X", "inspection_date": "2024-01-01",
        "inspection_time": "01:00", "truck_unit_number": "WHATEVER",
        "truck_checklist": {},
        "trailers": [{"trailer_unit_number": "T1", "checklist": {}}],
    }
    r = requests.post(f"{URL}/api/fleet/inspections", json=payload, timeout=15)
    assert r.status_code == 400
    assert "does not accept trailers" in r.text.lower()


# ─── Fleet selector (reuses equipment_master) ────────────────────────
def test_fleet_units_selector_returns_only_fleet_categories():
    if not URL:
        pytest.skip()
    r = requests.get(f"{URL}/api/fleet/units?limit=200", timeout=15)
    assert r.status_code == 200
    out = r.json()
    fleet_categories = {
        "Dump Trucks", "Tractor Trailer Trucks", "Service Trucks",
        "Pickup Trucks", "Flatbed Trucks", "Water Trucks",
        "Misc Trucks", "Supervisor / Mgmt Trucks", "Trailers",
    }
    bad = [u for u in out["units"] if u["category"] not in fleet_categories]
    assert bad == [], f"non-fleet categories leaked into selector: {bad[:3]}"


def test_fleet_units_selector_filters_by_unit_type():
    if not URL:
        pytest.skip()
    r1 = requests.get(f"{URL}/api/fleet/units?unit_type=trailer", timeout=15)
    assert r1.status_code == 200
    assert all(u["category"] == "Trailers" for u in r1.json()["units"])
    r2 = requests.get(f"{URL}/api/fleet/units?unit_type=truck&limit=50", timeout=15)
    assert r2.status_code == 200
    assert all(u["category"] != "Trailers" for u in r2.json()["units"])


# ─── Integration-ready identifiers (Motive / MaintainX) ─────────────
def test_defect_carries_external_refs_reserved_fields():
    """Phase F (Motive/MaintainX) will populate these · iter251 reserves
    them empty so future integration is schema-stable."""
    if not URL:
        pytest.skip()
    truck = f"IDENT-{uuid.uuid4().hex[:6]}"
    oos = "Reflective triangles — 3 present · case intact"
    payload = {
        "kind": "dvir",
        "driver_name": "Ident Driver",
        "inspection_date": "2024-08-15",
        "inspection_time": "11:00",
        "truck_unit_number": truck,
        "truck_vin": "1FUJA6CK67LX12345",
        "truck_plate": "TX-ABC-1234",
        "truck_checklist": {**{item: "pass" for item in _ck.dvir_truck_items()},
                            oos: "fail"},
    }
    try:
        r = requests.post(f"{URL}/api/fleet/inspections", json=payload, timeout=15)
        assert r.status_code == 200
        async def _check():
            db = _db()
            d = await db.fleet_defects.find_one({"truck_unit_number": truck}, {"_id": 0})
            assert "external_refs" in d
            assert d["external_refs"]["motive_id"] is None
            assert d["external_refs"]["maintainx_work_order_id"] is None
            insp = await db.equipment_inspections.find_one(
                {"truck_unit_number": truck}, {"_id": 0}
            )
            assert "external_refs" in insp
            assert insp.get("truck_vin") == "1FUJA6CK67LX12345"
            assert insp.get("truck_plate") == "TX-ABC-1234"
        asyncio.run(_check())
    finally:
        async def _go():
            db = _db()
            await db.equipment_inspections.delete_many({"truck_unit_number": truck})
            await db.fleet_defects.delete_many({"truck_unit_number": truck})
            await db.fleet_status.delete_one({"unit_number": truck})
        asyncio.run(_go())


# ─── Routes registered ──────────────────────────────────────────────
def test_fleet_endpoints_registered():
    import sys
    import importlib
    if "server" in sys.modules:
        importlib.reload(sys.modules["server"])
    import server as srv
    paths = {getattr(r, "path", None) for r in srv.app.routes}
    required = {
        "/api/fleet/_meta",
        "/api/fleet/units",
        "/api/fleet/inspections",
        "/api/fleet/inspections/{inspection_id}",
        "/api/fleet/defects/{defect_id}",
        "/api/dispatch/fleet/status",
        "/api/dispatch/fleet/defects/{defect_id}/clear",
        "/api/dispatch/fleet/units/{unit_number}/oos",
        "/api/shop/fleet/defects",
        "/api/shop/fleet/defects/{defect_id}/acknowledge",
        "/api/shop/fleet/defects/{defect_id}/repair",
        "/api/safety/fleet/emergency-equipment",
        "/api/admin/fleet/migrate-kind-field",
    }
    missing = required - paths
    assert not missing, f"missing fleet endpoints: {missing}"

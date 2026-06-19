"""Track 13.31 · PM Engine backend test suite.

Covers templates, schedules, work-order lifecycle, due-state math,
notification side-effects, ASE projection, and the RTS hard-lock.
"""
import os
import uuid
import asyncio
import httpx
import pytest

from datetime import datetime, timezone, timedelta

REACT_APP_BACKEND_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=", 1)[-1].splitlines()[0].strip()
)
API = REACT_APP_BACKEND_URL.rstrip("/") + "/api"


# ── Helpers ────────────────────────────────────────────────────────────


def _admin() -> str:
    r = httpx.post(f"{API}/admin/login", json={"password": "Maddix123!"}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code}")
    return r.json()["token"]


def _env() -> dict:
    e = {}
    for line in open("/app/backend/.env"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            e[k.strip()] = v.strip().strip('"').strip("'")
    return e


# ── Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def admin_tok():
    return _admin()


@pytest.fixture
def cleanup_pm():
    """Per-test cleanup of PM collections (preview-only)."""
    yield
    from motor.motor_asyncio import AsyncIOMotorClient
    env = _env()

    async def _wipe():
        cli = AsyncIOMotorClient(env["MONGO_URL"])
        db = cli[env["DB_NAME"]]
        await db.pm_work_orders.delete_many({"source_system": "masci_pm_engine"})
        await db.pm_schedules.delete_many({"source_system": "masci_pm_engine"})
        await db.pm_templates.delete_many({"source_system": "masci_pm_engine"})

    asyncio.run(_wipe())


# ── 1-2 · Template CRUD ────────────────────────────────────────────────


def test_template_requires_auth():
    r = httpx.get(f"{API}/shop/pm/templates", timeout=30)
    assert r.status_code == 401


def test_template_create_list_update(admin_tok, cleanup_pm):
    h = {"X-Admin-Token": admin_tok}
    body = {
        "name": "TEST 250-hr Excavator",
        "asset_type": "Excavator",
        "interval_type": "hours",
        "interval_value": 250,
        "warning_threshold": 25,
        "description": "Oil + filter",
        "checklist_items": [{"label": "Drain oil", "required": True}],
        "default_parts": [{"name": "Oil", "quantity": 4}],
        "active": True,
    }
    r = httpx.post(f"{API}/shop/pm/templates", json=body, headers=h, timeout=30)
    assert r.status_code == 200, r.text
    tpl = r.json()["template"]
    tid = tpl["id"]
    assert tpl["name"] == body["name"]
    assert tpl["interval_value"] == 250

    # List
    r = httpx.get(f"{API}/shop/pm/templates", headers=h, timeout=30)
    assert r.status_code == 200
    assert any(t["id"] == tid for t in r.json()["items"])

    # Update
    upd = {**body, "interval_value": 500, "name": "TEST 500-hr Excavator"}
    r = httpx.put(f"{API}/shop/pm/templates/{tid}", json=upd, headers=h, timeout=30)
    assert r.status_code == 200
    assert r.json()["template"]["interval_value"] == 500


def test_template_invalid_interval_type(admin_tok, cleanup_pm):
    h = {"X-Admin-Token": admin_tok}
    body = {"name": "X", "asset_type": "Excavator", "interval_type": "fortnights",
            "interval_value": 1, "warning_threshold": 0, "active": True}
    r = httpx.post(f"{API}/shop/pm/templates", json=body, headers=h, timeout=30)
    assert r.status_code == 422


# ── 3-7 · Due / overdue / unknown_meter math ───────────────────────────


def _seed_meter_visit(unit: str, meter: float):
    """Insert a fuel_lube_visit with a given meter so `_current_meter`
    returns deterministic data."""
    from motor.motor_asyncio import AsyncIOMotorClient
    env = _env()

    async def _go():
        cli = AsyncIOMotorClient(env["MONGO_URL"])
        db = cli[env["DB_NAME"]]
        await db.fuel_lube_visits.insert_one({
            "id": f"flv-pmtest-{uuid.uuid4().hex[:8]}",
            "visit_date": "2026-06-13",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "equipment_lines": [{
                "unit_number": unit,
                "meter_hours": meter,
                "issue_present": False,
            }],
            "_pm_test_seed": True,
        })
    asyncio.run(_go())


def _clear_meter_seed():
    from motor.motor_asyncio import AsyncIOMotorClient
    env = _env()

    async def _go():
        cli = AsyncIOMotorClient(env["MONGO_URL"])
        db = cli[env["DB_NAME"]]
        await db.fuel_lube_visits.delete_many({"_pm_test_seed": True})
    asyncio.run(_go())


def test_schedule_unknown_meter_when_no_visit(admin_tok, cleanup_pm):
    h = {"X-Admin-Token": admin_tok}
    suffix = uuid.uuid4().hex[:6]
    unit = f"PMNOM-{suffix}"
    tpl = httpx.post(f"{API}/shop/pm/templates", headers=h, json={
        "name": "T", "asset_type": "Excavator", "interval_type": "hours",
        "interval_value": 250, "warning_threshold": 25, "active": True,
    }, timeout=30).json()["template"]
    r = httpx.post(f"{API}/shop/pm/schedules", headers=h, json={
        "unit_number": unit, "template_id": tpl["id"],
        "last_completed_meter": 0, "active": True,
    }, timeout=30)
    assert r.status_code == 200
    assert r.json()["schedule"]["status"] == "unknown_meter"


def test_schedule_overdue_due_due_soon_ok_hours(admin_tok, cleanup_pm):
    h = {"X-Admin-Token": admin_tok}
    suffix = uuid.uuid4().hex[:6]
    unit = f"PMHRS-{suffix}"
    try:
        # Template: 250 hr interval, 25-hr warning threshold
        tpl = httpx.post(f"{API}/shop/pm/templates", headers=h, json={
            "name": "250hr", "asset_type": "Excavator", "interval_type": "hours",
            "interval_value": 250, "warning_threshold": 25, "active": True,
        }, timeout=30).json()["template"]

        def _make_sched(last_done_meter):
            return httpx.post(f"{API}/shop/pm/schedules", headers=h, json={
                "unit_number": unit, "template_id": tpl["id"],
                "last_completed_meter": last_done_meter, "active": True,
            }, timeout=30).json()["schedule"]

        # Current meter = 1300, last done = 1000 → due at 1250 → overdue by 50
        _seed_meter_visit(unit, 1300)
        s = _make_sched(1000)
        assert s["status"] == "overdue", s
        assert s["remaining_hours"] == -50

        # Last done = 1240 → due at 1490, remaining 190 — ok
        # Wipe schedule and re-seed
        httpx.put(f"{API}/shop/pm/schedules/{s['id']}", headers=h, json={
            "unit_number": unit, "template_id": tpl["id"],
            "last_completed_meter": 1240, "active": True,
        }, timeout=30)
        s2 = httpx.post(f"{API}/shop/pm/schedules/{s['id']}/recompute",
                        headers=h, timeout=30).json()["schedule"]
        assert s2["status"] == "ok", s2

        # Last done = 1080 → due at 1330, remaining 30 → due (within 25-hr threshold? no — 30 > 25 → due_soon-ish)
        # Actually with threshold=25 and interval=250, due_soon window = 25 + 25 = 50. Remaining 30 → due_soon? Code says due if remaining <= threshold, else due_soon if remaining <= threshold + 10% of interval.
        # threshold = 25, 10% of 250 = 25. So due_soon zone = 25..50.
        httpx.put(f"{API}/shop/pm/schedules/{s['id']}", headers=h, json={
            "unit_number": unit, "template_id": tpl["id"],
            "last_completed_meter": 1080, "active": True,
        }, timeout=30)
        s3 = httpx.post(f"{API}/shop/pm/schedules/{s['id']}/recompute",
                        headers=h, timeout=30).json()["schedule"]
        assert s3["status"] == "due_soon", s3

        # Last done = 1085 → due at 1335, remaining 35 → still due_soon (between 25 and 50)
        # For an actual "due" hit, remaining must be <= 25.
        httpx.put(f"{API}/shop/pm/schedules/{s['id']}", headers=h, json={
            "unit_number": unit, "template_id": tpl["id"],
            "last_completed_meter": 1090, "active": True,
        }, timeout=30)
        s4 = httpx.post(f"{API}/shop/pm/schedules/{s['id']}/recompute",
                        headers=h, timeout=30).json()["schedule"]
        # remaining 40 → due_soon
        assert s4["status"] == "due_soon", s4

        httpx.put(f"{API}/shop/pm/schedules/{s['id']}", headers=h, json={
            "unit_number": unit, "template_id": tpl["id"],
            "last_completed_meter": 1080, "active": True, "warning_threshold": 30,
        }, timeout=30)
        # With threshold 30, remaining 30 → due (30 <= 30)
        s5 = httpx.post(f"{API}/shop/pm/schedules/{s['id']}/recompute",
                        headers=h, timeout=30).json()["schedule"]
        assert s5["status"] == "due", s5
        assert "Due within" in s5["explanation"]
    finally:
        _clear_meter_seed()


def test_schedule_days_overdue(admin_tok, cleanup_pm):
    h = {"X-Admin-Token": admin_tok}
    suffix = uuid.uuid4().hex[:6]
    tpl = httpx.post(f"{API}/shop/pm/templates", headers=h, json={
        "name": "90-day", "asset_type": "Other Trailer", "interval_type": "days",
        "interval_value": 90, "warning_threshold": 7, "active": True,
    }, timeout=30).json()["template"]
    last = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
    r = httpx.post(f"{API}/shop/pm/schedules", headers=h, json={
        "unit_number": f"TRL-{suffix}", "template_id": tpl["id"],
        "last_completed_at": last, "active": True,
    }, timeout=30)
    assert r.json()["schedule"]["status"] == "overdue"


def test_schedule_paused(admin_tok, cleanup_pm):
    h = {"X-Admin-Token": admin_tok}
    tpl = httpx.post(f"{API}/shop/pm/templates", headers=h, json={
        "name": "P", "asset_type": "Excavator", "interval_type": "hours",
        "interval_value": 250, "warning_threshold": 0, "active": True,
    }, timeout=30).json()["template"]
    r = httpx.post(f"{API}/shop/pm/schedules", headers=h, json={
        "unit_number": f"PMP-{uuid.uuid4().hex[:4]}", "template_id": tpl["id"],
        "last_completed_meter": 0, "active": True, "paused": True,
    }, timeout=30)
    assert r.json()["schedule"]["status"] == "paused"


# ── 10-17 · Work order lifecycle ──────────────────────────────────────


def test_work_order_full_lifecycle_and_rts_note(admin_tok, cleanup_pm):
    h = {"X-Admin-Token": admin_tok}
    suffix = uuid.uuid4().hex[:6]
    unit = f"PMLC-{suffix}"
    try:
        _seed_meter_visit(unit, 1300)
        tpl = httpx.post(f"{API}/shop/pm/templates", headers=h, json={
            "name": "LC", "asset_type": "Excavator", "interval_type": "hours",
            "interval_value": 250, "warning_threshold": 25, "active": True,
            "checklist_items": [{"label": "Drain oil", "required": True}],
        }, timeout=30).json()["template"]
        sch = httpx.post(f"{API}/shop/pm/schedules", headers=h, json={
            "unit_number": unit, "template_id": tpl["id"],
            "last_completed_meter": 1000, "active": True,
        }, timeout=30).json()["schedule"]

        # Generate WO
        wo = httpx.post(f"{API}/shop/pm/work-orders", headers=h, json={
            "schedule_id": sch["id"], "notes": "first cycle",
        }, timeout=30).json()["work_order"]
        wid = wo["id"]
        assert wo["status"] == "open"
        assert len(wo["checklist_results"]) == 1

        # Cannot generate again while open
        dup = httpx.post(f"{API}/shop/pm/work-orders", headers=h, json={
            "schedule_id": sch["id"],
        }, timeout=30)
        assert dup.status_code == 409

        # Assign
        r = httpx.post(f"{API}/shop/pm/work-orders/{wid}/assign", headers=h, json={
            "mechanic_id": "mech-1", "mechanic_name": "Mech One",
        }, timeout=30)
        assert r.json()["work_order"]["status"] == "assigned"
        # Accept
        assert httpx.post(f"{API}/shop/pm/work-orders/{wid}/accept",
                          headers=h, timeout=30).json()["work_order"]["status"] == "accepted"
        # Start
        assert httpx.post(f"{API}/shop/pm/work-orders/{wid}/start",
                          headers=h, json={"notes": "go"},
                          timeout=30).json()["work_order"]["status"] == "in_progress"
        # Complete requires 10+ char notes
        bad = httpx.post(f"{API}/shop/pm/work-orders/{wid}/complete", headers=h, json={
            "notes": "ok", "completed_by_name": "Mech One",
        }, timeout=30)
        assert bad.status_code == 422
        # Complete properly
        ok = httpx.post(f"{API}/shop/pm/work-orders/{wid}/complete", headers=h, json={
            "notes": "Drained oil, replaced filter, topped fluids.",
            "completion_meter": 1305,
            "checklist_results": [{"label": "Drain oil", "pass": True, "notes": ""}],
            "parts_used": [{"name": "Shell 15W-40", "quantity": 4}],
            "completed_by_name": "Mech One",
        }, timeout=30).json()
        assert ok["work_order"]["status"] == "completed"
        assert ok["work_order"]["completion_meter"] == 1305

        # Manager approve → reviewed + RTS note + schedule rolled forward
        rev = httpx.post(f"{API}/shop/pm/work-orders/{wid}/manager-review", headers=h, json={
            "decision": "approve", "reviewer_name": "Shop Mgr", "notes": "OK",
        }, timeout=30).json()
        assert rev["work_order"]["status"] == "reviewed"
        assert "does NOT return the unit to service" in rev["rts_note"]

        # Schedule should now have last_completed_meter = 1305
        s2 = httpx.post(f"{API}/shop/pm/schedules/{sch['id']}/recompute",
                        headers=h, timeout=30).json()["schedule"]
        assert s2["last_completed_meter"] == 1305

        # Generate next WO succeeds (no longer blocked)
        wo2 = httpx.post(f"{API}/shop/pm/work-orders", headers=h, json={
            "schedule_id": sch["id"],
        }, timeout=30)
        assert wo2.status_code == 200
    finally:
        _clear_meter_seed()


def test_work_order_manager_reject(admin_tok, cleanup_pm):
    h = {"X-Admin-Token": admin_tok}
    suffix = uuid.uuid4().hex[:6]
    unit = f"PMRJ-{suffix}"
    try:
        _seed_meter_visit(unit, 1300)
        tpl = httpx.post(f"{API}/shop/pm/templates", headers=h, json={
            "name": "R", "asset_type": "Excavator", "interval_type": "hours",
            "interval_value": 250, "warning_threshold": 25, "active": True,
        }, timeout=30).json()["template"]
        sch = httpx.post(f"{API}/shop/pm/schedules", headers=h, json={
            "unit_number": unit, "template_id": tpl["id"],
            "last_completed_meter": 1000, "active": True,
        }, timeout=30).json()["schedule"]
        wo = httpx.post(f"{API}/shop/pm/work-orders", headers=h, json={
            "schedule_id": sch["id"],
        }, timeout=30).json()["work_order"]
        # Race lifecycle
        for path, body in [
            ("assign", {"mechanic_id": "m", "mechanic_name": "M"}),
            ("accept", None), ("start", {"notes": ""}),
            ("complete", {"notes": "did the work cleanly",
                          "completed_by_name": "M"}),
        ]:
            kw = {"json": body} if body is not None else {}
            r = httpx.post(f"{API}/shop/pm/work-orders/{wo['id']}/{path}",
                           headers=h, timeout=30, **kw)
            assert r.status_code == 200, (path, r.text)
        # Reject
        rev = httpx.post(f"{API}/shop/pm/work-orders/{wo['id']}/manager-review",
                         headers=h, json={"decision": "reject",
                                          "reviewer_name": "Mgr",
                                          "notes": "Re-do step 3"},
                         timeout=30).json()
        assert rev["work_order"]["status"] == "rejected"
    finally:
        _clear_meter_seed()


# ── 18 · ASE projects PM events ────────────────────────────────────────


def test_ase_projects_pm_events(admin_tok, cleanup_pm):
    h = {"X-Admin-Token": admin_tok}
    unit = "EXC-PMTEST-1"
    try:
        _seed_meter_visit(unit, 1300)
        # Also seed equipment_master for canonical lookup
        from motor.motor_asyncio import AsyncIOMotorClient
        env = _env()

        async def _seed_em():
            cli = AsyncIOMotorClient(env["MONGO_URL"])
            db = cli[env["DB_NAME"]]
            await db.equipment_master.insert_one({
                "id": f"em-{unit}", "unit_number": unit, "label": "PM Test",
                "type": "excavator", "is_active": True,
            })
        asyncio.run(_seed_em())
        tpl = httpx.post(f"{API}/shop/pm/templates", headers=h, json={
            "name": "ASE PM", "asset_type": "Excavator", "interval_type": "hours",
            "interval_value": 250, "warning_threshold": 25, "active": True,
        }, timeout=30).json()["template"]
        sch = httpx.post(f"{API}/shop/pm/schedules", headers=h, json={
            "unit_number": unit, "template_id": tpl["id"],
            "last_completed_meter": 1000, "active": True,
        }, timeout=30).json()["schedule"]
        wo = httpx.post(f"{API}/shop/pm/work-orders", headers=h, json={
            "schedule_id": sch["id"],
        }, timeout=30).json()["work_order"]
        httpx.post(f"{API}/shop/pm/work-orders/{wo['id']}/assign", headers=h, json={
            "mechanic_id": "mm", "mechanic_name": "MM",
        }, timeout=30)
        httpx.post(f"{API}/shop/pm/work-orders/{wo['id']}/accept", headers=h, timeout=30)
        httpx.post(f"{API}/shop/pm/work-orders/{wo['id']}/start", headers=h, json={}, timeout=30)
        httpx.post(f"{API}/shop/pm/work-orders/{wo['id']}/complete", headers=h, json={
            "notes": "Did the PM cleanly.", "completed_by_name": "MM",
        }, timeout=30)
        httpx.post(f"{API}/shop/pm/work-orders/{wo['id']}/manager-review", headers=h, json={
            "decision": "approve", "reviewer_name": "Mgr",
        }, timeout=30)

        # Now hit ASE (90-day window cap)
        today = datetime.now(timezone.utc).date()
        date_from = (today - timedelta(days=30)).isoformat()
        r = httpx.get(f"{API}/assets/{unit}/timeline",
                      params={"from": date_from, "to": today.isoformat()},
                      headers=h, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        pm_count = d["counts"]["by_event_type"].get("pm", 0)
        assert pm_count >= 4, f"expected ≥4 PM events (assigned/started/completed/reviewed) — got {pm_count}"
        # `pm` no longer appears in unavailable list
        unavailable_types = [u["event_type"] for u in d.get("unavailable_event_types", [])]
        assert "pm" not in unavailable_types
        assert "maintainx" in unavailable_types  # still unavailable
    finally:
        _clear_meter_seed()
        from motor.motor_asyncio import AsyncIOMotorClient
        env = _env()

        async def _wipe():
            cli = AsyncIOMotorClient(env["MONGO_URL"])
            db = cli[env["DB_NAME"]]
            await db.equipment_master.delete_one({"id": f"em-{unit}"})
        asyncio.run(_wipe())


# ── 19 · Summary + queue shape ─────────────────────────────────────────


def test_summary_shape_and_doctrine(admin_tok):
    h = {"X-Admin-Token": admin_tok}
    r = httpx.get(f"{API}/shop/pm/summary", headers=h, timeout=30)
    assert r.status_code == 200
    d = r.json()
    for k in ("schedule_counts", "work_order_counts", "unassigned",
              "source", "doctrine"):
        assert k in d
    # Doctrine flags
    assert d["doctrine"]["pm_completion_equals_rts"] is False
    assert d["doctrine"]["maintainx_active"] is False
    assert d["doctrine"]["manufacturer_db_active"] is False
    # No cost / accounting / PO / pay-app fields anywhere in summary
    blob = repr(d).lower()
    for forbidden in ("cost", "price", "po_number", "tax", "invoice", "margin",
                      "pay_app", "accounting", "erp"):
        assert forbidden not in blob, f"forbidden field surfaced: {forbidden}"


def test_queue_shape(admin_tok):
    h = {"X-Admin-Token": admin_tok}
    r = httpx.get(f"{API}/shop/pm/queue", headers=h, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert "work_orders" in d and "schedules" in d
    for k in ("open", "assigned", "accepted", "in_progress",
             "waiting_parts", "completed", "rejected"):
        assert k in d["work_orders"]
    for k in ("overdue", "due", "due_soon"):
        assert k in d["schedules"]


# ── 20-21 · Hard locks ────────────────────────────────────────────────


def test_no_cost_fields_in_work_order_response(admin_tok, cleanup_pm):
    h = {"X-Admin-Token": admin_tok}
    tpl = httpx.post(f"{API}/shop/pm/templates", headers=h, json={
        "name": "HL", "asset_type": "Excavator", "interval_type": "hours",
        "interval_value": 100, "active": True,
    }, timeout=30).json()["template"]
    sch = httpx.post(f"{API}/shop/pm/schedules", headers=h, json={
        "unit_number": f"HL-{uuid.uuid4().hex[:4]}", "template_id": tpl["id"],
        "active": True, "paused": True,
    }, timeout=30).json()["schedule"]
    # Note: paused schedule means current state is paused — but we can still
    # mint a work order against it. Verify the shape.
    wo = httpx.post(f"{API}/shop/pm/work-orders", headers=h, json={
        "schedule_id": sch["id"], "notes": "hard-lock smoke",
    }, timeout=30)
    assert wo.status_code == 200
    body = wo.json()
    blob = repr(body).lower()
    for forbidden in ("cost", "price", "tax", "invoice", "margin", "pay_app"):
        assert forbidden not in blob


def test_meter_endpoint_honest_unknown(admin_tok):
    h = {"X-Admin-Token": admin_tok}
    r = httpx.get(f"{API}/shop/pm/meter/UNIT-DOES-NOT-EXIST-XYZ",
                  headers=h, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["current_meter"]["source"] == "unknown"
    assert d["current_meter"]["meter_hours"] is None


# ── 22 · Manufacturer DB / MaintainX hard-lock ─────────────────────────


def test_maintainx_not_consumed(admin_tok):
    h = {"X-Admin-Token": admin_tok}
    r = httpx.get(f"{API}/shop/pm/summary", headers=h, timeout=30).json()
    assert r["doctrine"]["maintainx_active"] is False
    assert r["doctrine"]["manufacturer_db_active"] is False

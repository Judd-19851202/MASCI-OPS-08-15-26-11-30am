"""Track 13.30D · Parts-on-order + Mechanic workload backend tests."""
import os
import uuid
import asyncio
import httpx
import pytest


REACT_APP_BACKEND_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=", 1)[-1].splitlines()[0].strip()
)
API = REACT_APP_BACKEND_URL.rstrip("/") + "/api"


def _admin() -> str:
    r = httpx.post(f"{API}/admin/login", json={"password": "MASCI1982!"}, timeout=30)
    if r.status_code != 200:
        pytest.skip("admin login failed")
    return r.json()["token"]


def _forbidden_term_scan(blob: str):
    s = repr(blob).lower()
    for t in ("po_number", "cost", "price", "invoice", "tax", "margin",
              "payroll", "productivity", "discipline"):
        assert t not in s, f"forbidden term leaked: {t}"


def test_parts_on_order_auth_required():
    r = httpx.get(f"{API}/shop/parts/on-order/summary", timeout=30)
    assert r.status_code == 401


def test_parts_on_order_shape_and_no_cost_fields():
    tok = _admin()
    r = httpx.get(f"{API}/shop/parts/on-order/summary",
                  headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 200
    b = r.json()
    for k in ("generated_at", "total_parts_on_order", "units_waiting_parts",
              "defects_waiting_parts", "expected_today", "overdue_parts",
              "items", "source"):
        assert k in b
    assert b["source"] == "shop_command_center_intel"
    _forbidden_term_scan(b)


def test_parts_on_order_counts_seeded_row():
    tok = _admin()
    from motor.motor_asyncio import AsyncIOMotorClient
    e = {}
    for line in open("/app/backend/.env"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            e[k.strip()] = v.strip().strip('"').strip("'")
    unit = f"ITEST-PARTS-{uuid.uuid4().hex[:6]}"
    did = f"itestdef-{uuid.uuid4().hex[:8]}"

    async def seed_and_clean():
        cli = AsyncIOMotorClient(e["MONGO_URL"])
        db = cli[e["DB_NAME"]]
        try:
            await db.fleet_defects.insert_one({
                "id": did, "truck_unit_number": unit,
                "status": "in_progress", "severity": "critical",
                "item_text": "brake pad", "reported_at": "2026-06-12T00:00:00Z",
                "parts_on_order": [{"name": "Brake Pad Set",
                                     "part_number": "BP-12",
                                     "manufacturer": "ACME",
                                     "expected_date": "2026-06-13",
                                     "quantity": 4}],
                "assigned_to_mechanic_id": "ITEST-MECH",
                "assigned_to_mechanic_name": "ITest Mechanic",
            })
            r = httpx.get(f"{API}/shop/parts/on-order/summary",
                          headers={"X-Admin-Token": tok}, timeout=30)
            b = r.json()
            assert b["total_parts_on_order"] >= 1
            assert b["units_waiting_parts"] >= 1
            assert b["defects_waiting_parts"] >= 1
            rows = [it for it in b["items"] if it["unit_number"] == unit]
            assert rows and rows[0]["part_name"] == "Brake Pad Set"
            assert rows[0]["assigned_mechanic_name"] == "ITest Mechanic"
            assert rows[0]["links"]["unit_history"] == f"/shop/units/{unit}/history"

            # Workload sees the same mechanic
            r2 = httpx.get(f"{API}/shop/mechanics/workload",
                           headers={"X-Admin-Token": tok}, timeout=30)
            b2 = r2.json()
            mlist = [m for m in b2["mechanics"] if m["mechanic_id"] == "ITEST-MECH"]
            assert mlist
            m = mlist[0]
            assert m["in_progress"] >= 1
            assert m["waiting_parts"] >= 1
            assert m["load_status"] in {"clear", "normal", "busy", "heavy_load"}
            _forbidden_term_scan(b2)
        finally:
            await db.fleet_defects.delete_one({"id": did})

    asyncio.run(seed_and_clean())


def test_mechanics_workload_auth_required():
    r = httpx.get(f"{API}/shop/mechanics/workload", timeout=30)
    assert r.status_code == 401


def test_mechanics_workload_shape():
    tok = _admin()
    r = httpx.get(f"{API}/shop/mechanics/workload",
                  headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 200
    b = r.json()
    for k in ("generated_at", "mechanic_count", "total_assigned",
              "total_in_progress", "total_pending_review",
              "total_waiting_parts", "mechanics", "source"):
        assert k in b
    _forbidden_term_scan(b)

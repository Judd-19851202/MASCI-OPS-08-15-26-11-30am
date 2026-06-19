"""iter251 Phase 4 · Repair Lifecycle · backend integration tests.

Operator-approved Phase 4 scope:
  - Shop POST /api/shop/fleet/defects/{id}/repair  (mechanic + notes + photos)
  - Dispatch POST /api/dispatch/fleet/defects/{id}/clear  (RTS confirmation)
  - GET /api/fleet/defects/{id}/detail  (multi-portal · audit trail)
  - by-unit endpoint surfaces awaiting_rts_count + repaired defects
  - fleet_status transitions: open → ack → repaired → cleared
      maps to: oos|defect_open → repair_in_progress → available

These are end-to-end black-box tests against the live preview API.
"""
from __future__ import annotations

import os
import time
import uuid

import requests


BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://safety-audit-mobile-1.preview.emergentagent.com",
).rstrip("/")
ADMIN_PW = os.environ.get("ADMIN_PASSWORD", "Maddix123!")


def _admin_token() -> str:
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PW}, timeout=15)
    r.raise_for_status()
    return r.json()["token"]


def _admin_h() -> dict:
    return {"X-Admin-Token": _admin_token()}


# ─── Fixture-free helper · seeds an inspection that creates one OOS defect
def _seed_oos_defect(unit: str) -> str:
    """Submit a DVIR that fails one OOS-classified item · returns defect_id."""
    payload = {
        "kind": "dvir",
        "driver_name": f"Phase4 Driver {unit}",
        "driver_employee_id": "",
        "inspection_date": "2026-05-19",
        "inspection_time": "10:00",
        "truck_unit_number": unit,
        "truck_vin": "",
        "trailers": [],
        # The item below is OOS per the v1.3 severity table
        "truck_checklist": {"Service brakes — apply firmly · stop straight · no pulling": "fail"},
        "defect_details": {
            "Service brakes — apply firmly · stop straight · no pulling": {
                "note": "Phase4 seed · simulated OOS defect for lifecycle test",
                "photos": [],
            }
        },
        "driver_signature": "data:image/png;base64,iVBORw0KGgo=",
    }
    r = requests.post(
        f"{BASE_URL}/api/fleet/inspections",
        json=payload,
        headers={"X-Admin-Token": ""},  # public-tile is allowed
        timeout=20,
    )
    assert r.status_code == 200, f"seed failed {r.status_code}: {r.text[:200]}"
    j = r.json()
    assert j.get("defect_count", 0) >= 1, f"no defect created: {j}"
    # Look up the freshly inserted defect ID by inspection_id
    insp_id = j["inspection_id"]
    # poll briefly · find the defect tied to this inspection
    for _ in range(5):
        rd = requests.get(
            f"{BASE_URL}/api/shop/fleet/by-unit",
            headers={"X-Admin-Token": _admin_token()}, timeout=15,
        )
        rd.raise_for_status()
        for g in rd.json().get("groups", []):
            if g["unit_number"] == unit:
                for d in g["defects"]:
                    if d.get("inspection_id") == insp_id:
                        return d["defect_id"]
        time.sleep(0.3)
    raise AssertionError(f"could not locate freshly seeded defect for unit={unit}")


def _cleanup(unit: str, defect_id: str) -> None:
    """Best-effort scrub of seeded data so reruns are clean."""
    try:
        import asyncio
        from motor.motor_asyncio import AsyncIOMotorClient
        async def _go():
            c = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
            db = c[os.environ.get("DB_NAME", "test_database")]
            await db.fleet_defects.delete_many({"truck_unit_number": unit})
            await db.equipment_inspections.delete_many({"truck_unit_number": unit})
            await db.fleet_status.delete_one({"unit_number": unit})
            await db.fleet_audit.delete_many({"target_id": defect_id})
            await db.fleet_audit.delete_many({"target_id": unit})
        asyncio.run(_go())
    except Exception:
        pass


# ────────────────────────────────────────────────────────────────────


class TestRepairLifecycle:

    def test_full_lifecycle_open_to_returned_to_service(self):
        unit = f"P4UNIT-{uuid.uuid4().hex[:6].upper()}"
        defect_id = _seed_oos_defect(unit)
        try:
            H = _admin_h()

            # 1 · defect appears in by-unit with status=open, severity=oos
            r = requests.get(f"{BASE_URL}/api/shop/fleet/by-unit", headers=H, timeout=15)
            assert r.status_code == 200
            groups = {g["unit_number"]: g for g in r.json()["groups"]}
            assert unit in groups, f"seeded unit {unit} not in by-unit"
            grp = groups[unit]
            assert grp["open_oos_count"] == 1
            assert grp["awaiting_rts_count"] == 0
            assert grp["truck_status"] == "oos"
            d = next(x for x in grp["defects"] if x["defect_id"] == defect_id)
            assert d["status"] == "open"
            assert d["severity"] == "oos"
            # Phase 3 spec field names (operator-approved contract)
            assert "checklist_item" in d
            assert "driver_note" in d
            assert "reported_by_driver_name" in d
            assert "regulation_ref" in d

            # 2 · Shop marks repaired
            r = requests.post(
                f"{BASE_URL}/api/shop/fleet/defects/{defect_id}/repair",
                json={
                    "actor_name": "Phase4 Mechanic",
                    "notes": "Replaced front pads · road-tested · pulling resolved",
                    "photos": [],
                },
                headers=H, timeout=15,
            )
            assert r.status_code == 200, r.text[:300]

            # 3 · by-unit now shows repaired defect + awaiting_rts_count=1 + truck_status=repair_in_progress
            r = requests.get(f"{BASE_URL}/api/shop/fleet/by-unit", headers=H, timeout=15)
            assert r.status_code == 200
            groups = {g["unit_number"]: g for g in r.json()["groups"]}
            assert unit in groups
            grp = groups[unit]
            assert grp["open_oos_count"] == 0
            assert grp["awaiting_rts_count"] == 1
            assert grp["truck_status"] == "repair_in_progress", grp
            d = next(x for x in grp["defects"] if x["defect_id"] == defect_id)
            assert d["status"] == "repaired"
            assert d["repaired_by_name"] == "Phase4 Mechanic"
            assert "Replaced front pads" in (d.get("repair_notes") or "")

            # 4 · Dispatch confirms Return-to-Service
            r = requests.post(
                f"{BASE_URL}/api/dispatch/fleet/defects/{defect_id}/clear",
                json={
                    "actor_name": "Phase4 Dispatcher",
                    "notes": "Confirmed road test PASS",
                },
                headers=H, timeout=15,
            )
            assert r.status_code == 200, r.text[:300]

            # 5 · After RTS the defect is cleared and the unit drops from by-unit
            r = requests.get(f"{BASE_URL}/api/shop/fleet/by-unit", headers=H, timeout=15)
            groups = {g["unit_number"]: g for g in r.json()["groups"]}
            # Unit no longer in the active-defect feed
            assert unit not in groups, (
                f"unit {unit} should have dropped from by-unit after RTS"
            )

            # 6 · Detail endpoint surfaces full lifecycle + audit
            r = requests.get(
                f"{BASE_URL}/api/fleet/defects/{defect_id}/detail",
                headers=H, timeout=15,
            )
            assert r.status_code == 200, r.text[:300]
            j = r.json()
            assert j["defect"]["status"] == "cleared"
            assert j["defect"]["repaired_by_name"] == "Phase4 Mechanic"
            assert j["defect"]["cleared_by_name"] == "Phase4 Dispatcher"
            actions = [e["action"] for e in j["audit"]]
            assert "defect_repaired" in actions
            assert "defect_cleared" in actions
            # Every audit row carries status_before / status_after
            for e in j["audit"]:
                if e["action"] in ("defect_repaired", "defect_cleared"):
                    assert "status_before" in (e.get("payload") or {})
                    assert "status_after" in (e.get("payload") or {})
                    assert (e.get("payload") or {}).get("unit_number") == unit
        finally:
            _cleanup(unit, defect_id)

    def test_rts_blocked_when_defect_not_repaired(self):
        """Dispatch must not clear a defect that has NOT been repaired by Shop."""
        unit = f"P4UNIT-{uuid.uuid4().hex[:6].upper()}"
        defect_id = _seed_oos_defect(unit)
        try:
            r = requests.post(
                f"{BASE_URL}/api/dispatch/fleet/defects/{defect_id}/clear",
                json={"actor_name": "Phase4 Dispatcher"},
                headers=_admin_h(), timeout=15,
            )
            assert r.status_code == 400, (
                f"expected 400 trying to clear an open defect, got {r.status_code}"
            )
        finally:
            _cleanup(unit, defect_id)

    def test_detail_endpoint_multi_portal_read(self):
        """detail endpoint must accept any portal token (admin in this test)."""
        unit = f"P4UNIT-{uuid.uuid4().hex[:6].upper()}"
        defect_id = _seed_oos_defect(unit)
        try:
            r = requests.get(
                f"{BASE_URL}/api/fleet/defects/{defect_id}/detail",
                headers=_admin_h(), timeout=15,
            )
            assert r.status_code == 200
            j = r.json()
            assert j["defect"]["defect_id"] == defect_id
            # No transitions yet, only the bare defect with empty audit
            assert isinstance(j["audit"], list)
        finally:
            _cleanup(unit, defect_id)

    def test_detail_endpoint_anon_blocked(self):
        unit = f"P4UNIT-{uuid.uuid4().hex[:6].upper()}"
        defect_id = _seed_oos_defect(unit)
        try:
            r = requests.get(
                f"{BASE_URL}/api/fleet/defects/{defect_id}/detail",
                headers={"X-Admin-Token": ""},  # bypass conftest auto-injection
                timeout=15,
            )
            assert r.status_code in (401, 403), (
                f"detail endpoint must require a portal token; got {r.status_code}"
            )
        finally:
            _cleanup(unit, defect_id)

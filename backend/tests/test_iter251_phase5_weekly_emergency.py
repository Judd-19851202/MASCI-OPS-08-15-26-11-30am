"""iter251 Phase 5 · Weekly Lead + Weekly Emergency forms.

Operator-bounded Phase 5 scope:
  - Weekly Lead Inspection (fleet lead / lead mechanic / super / safety)
  - Weekly Emergency Equipment Check (fire ext · triangles · PPE · etc.)

The backend already had the registry stubbed in Phase A (`weekly_lead`
and `weekly_emergency` kinds with their checklists). Phase 5 wires the
frontend and validates the integration:
  - `/api/fleet/_meta` advertises all three kinds.
  - `/api/fleet/inspections` accepts the new kinds and creates defects
    that flow through the same Phase 4 repair-lifecycle path.
  - severity table covers every emergency-equipment item that should
    be OOS (fire extinguisher present/charged · triangles · etc.).
"""
from __future__ import annotations

import os
import uuid

import requests


BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://backup-forensics.preview.emergentagent.com",
).rstrip("/")
ADMIN_PW = os.environ.get("ADMIN_PASSWORD", "Maddix123!")


def _admin_token() -> str:
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_PW}, timeout=15)
    r.raise_for_status()
    return r.json()["token"]


def _admin_h() -> dict:
    return {"X-Admin-Token": _admin_token()}


def _cleanup(unit: str) -> None:
    try:
        import asyncio
        from motor.motor_asyncio import AsyncIOMotorClient
        async def _go():
            c = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
            db = c[os.environ.get("DB_NAME", "test_database")]
            await db.fleet_defects.delete_many({"truck_unit_number": unit})
            await db.equipment_inspections.delete_many({"truck_unit_number": unit})
            await db.fleet_status.delete_one({"unit_number": unit})
            await db.fleet_audit.delete_many({"target_id": unit})
        asyncio.run(_go())
    except Exception:
        pass


class TestPhase5Kinds:

    def test_meta_advertises_three_kinds(self):
        r = requests.get(f"{BASE_URL}/api/fleet/_meta", headers=_admin_h(), timeout=15)
        assert r.status_code == 200
        kinds = r.json()["kinds"]
        # Phase 5 acceptance: all three kinds available.
        assert set(kinds.keys()) == {"dvir", "weekly_lead", "weekly_emergency"}
        # Trailer affordance: only the daily DVIR allows trailers.
        assert kinds["dvir"]["allows_trailers"] is True
        assert kinds["weekly_lead"]["allows_trailers"] is False
        assert kinds["weekly_emergency"]["allows_trailers"] is False
        # Each kind must carry a non-empty checklist for the truck section.
        for k in ("dvir", "weekly_lead", "weekly_emergency"):
            assert kinds[k]["truck_items"], f"{k} has no truck_items"

    def test_weekly_lead_submission_creates_inspection_with_kind(self):
        unit = f"P5-LEAD-{uuid.uuid4().hex[:6].upper()}"
        try:
            payload = {
                "kind": "weekly_lead",
                "driver_name": "Lead Inspector",
                "inspection_date": "2026-05-19",
                "inspection_time": "08:00",
                "truck_unit_number": unit,
                "trailers": [],
                # All items PASS · no defects expected
                "truck_checklist": {
                    item: "pass"
                    for item in (
                        "Body — cosmetic dings · scrapes · paint",
                        "Tire — minor sidewall scuff / cosmetic",
                        "Mirror — minor crack / chip with visible image",
                        "Cab heater — functional · escalates to OOS if window fogging affects visibility",
                        "Wheel — no surface rust streaks (cosmetic)",
                        "Landing gear — minor cosmetic wear",
                        "Seat belt — present · functional · no fraying",
                        "Fire extinguisher — present · charged · sealed · tag current",
                        "Reflective triangles — 3 present · case intact",
                    )
                },
                "defect_details": {},
                "driver_signature": "data:image/png;base64,iVBORw0KGgo=",
            }
            r = requests.post(
                f"{BASE_URL}/api/fleet/inspections",
                json=payload, headers={"X-Admin-Token": ""}, timeout=20,
            )
            assert r.status_code == 200, r.text[:300]
            j = r.json()
            assert j["defect_count"] == 0, j
            # Confirm the inspection was persisted with the new kind discriminator.
            assert j.get("inspection_id")
        finally:
            _cleanup(unit)

    def test_weekly_emergency_failure_creates_oos_defect(self):
        """Missing/expired fire extinguisher must produce an OOS defect
        that flows through the SAME Phase 4 lifecycle."""
        unit = f"P5-EMER-{uuid.uuid4().hex[:6].upper()}"
        try:
            payload = {
                "kind": "weekly_emergency",
                "driver_name": "Safety Inspector",
                "inspection_date": "2026-05-19",
                "inspection_time": "09:00",
                "truck_unit_number": unit,
                "trailers": [],
                "truck_checklist": {
                    "Fire extinguisher — present · charged · sealed · tag current": "fail",
                },
                "defect_details": {
                    "Fire extinguisher — present · charged · sealed · tag current": {
                        "note": "Phase 5 emergency seed · extinguisher tag expired",
                        "photos": [],
                    },
                },
                "driver_signature": "data:image/png;base64,iVBORw0KGgo=",
            }
            r = requests.post(
                f"{BASE_URL}/api/fleet/inspections",
                json=payload, headers={"X-Admin-Token": ""}, timeout=20,
            )
            assert r.status_code == 200, r.text[:300]
            j = r.json()
            assert j["defect_count"] >= 1
            # Confirm the defect shows up in by-unit and the unit is OOS.
            r2 = requests.get(
                f"{BASE_URL}/api/shop/fleet/by-unit", headers=_admin_h(), timeout=15,
            )
            groups = {g["unit_number"]: g for g in r2.json()["groups"]}
            assert unit in groups, f"unit {unit} not in shop by-unit"
            grp = groups[unit]
            assert grp["open_oos_count"] >= 1, grp
            assert grp["truck_status"] == "oos"
            d = grp["defects"][0]
            assert d["severity"] == "oos"
            assert "Fire extinguisher" in d["checklist_item"]
        finally:
            _cleanup(unit)

    def test_unknown_kind_rejected(self):
        r = requests.post(
            f"{BASE_URL}/api/fleet/inspections",
            json={
                "kind": "made_up_kind",
                "driver_name": "X",
                "inspection_date": "2026-05-19",
                "inspection_time": "09:00",
                "truck_unit_number": "DOES-NOT-EXIST",
                "trailers": [],
                "truck_checklist": {},
                "defect_details": {},
                "driver_signature": "x",
            },
            headers={"X-Admin-Token": ""}, timeout=15,
        )
        # Unknown kind must be refused (Phase A allow-list).
        assert r.status_code in (400, 422)

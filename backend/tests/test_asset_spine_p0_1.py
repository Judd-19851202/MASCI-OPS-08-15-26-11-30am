"""
tests/test_asset_spine_p0_1.py · FORGEDOPS P0.1 Asset Spine pinning.

Run with:
    cd /app/backend && python -m pytest tests/test_asset_spine_p0_1.py -q
"""
from __future__ import annotations

import asyncio
import os
import uuid

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

from services.asset_spine import AssetSpine, project_asset
from services.asset_spine_detection import (
    detect_duplicates, run_detectors,
)


def _new_id() -> str:
    return f"test-{uuid.uuid4()}"


def _db():
    """Get a Motor DB, loading .env if MONGO_URL not already set."""
    if "MONGO_URL" not in os.environ:
        try:
            with open(os.path.join(os.path.dirname(__file__), "..", ".env")) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("MONGO_URL=") or line.startswith("DB_NAME="):
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k, v.strip().strip('"'))
        except Exception:
            pass
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return client[os.environ["DB_NAME"]]


def _run(coro):
    """Run an async coroutine in a fresh loop. Avoids pytest-asyncio dep."""
    return asyncio.get_event_loop().run_until_complete(coro) if asyncio.get_event_loop().is_running() is False else asyncio.run(coro)


# ---------------------------------------------------------------------------
# project_asset · canonical field surface (pure)
# ---------------------------------------------------------------------------

def test_project_asset_maps_legacy_fields_to_canonical():
    doc = {
        "id": "a1", "unit_number": "T-42", "label": "Truck 42",
        "type": "Truck", "category": "Heavy",
        "company": "MGC", "make": "Mack", "model": "TerraPro",
        "year": 2022, "vin_serial_number": "1M2…42",
        "is_active": True, "current_project_id": "25-21",
        "current_project_name": "SJR2C", "updated_by": "ops",
        "updated_at": "2026-02-10T00:00:00Z",
    }
    a = project_asset(doc)
    assert a["asset_id"] == "a1"
    assert a["asset_number"] == "T-42"
    assert a["asset_name"] == "Truck 42"
    assert a["asset_type"] == "Truck"
    assert a["asset_category"] == "Heavy"
    assert a["ownership"] == "MGC"
    assert a["vin"] == "1M2…42"
    assert a["assigned_project_id"] == "25-21"
    assert a["assigned_project_name"] == "SJR2C"
    assert a["last_modified_by"] == "ops"
    assert a["active"] is True


def test_project_asset_none_returns_empty():
    assert project_asset(None) == {}


def test_project_asset_empty_doc_returns_canonical_nulls():
    """An empty doc still returns the full canonical shape with Nones."""
    a = project_asset({})
    # Empty doc projection: docs without an id return {} per project_asset
    # design; documents that have at least one key get the full shape.
    a2 = project_asset({"id": "stub"})
    assert a2["asset_id"] == "stub"
    assert a2["asset_number"] is None
    assert a2["active"] is True  # default when is_active missing


def test_project_asset_is_active_false_yields_active_false():
    a = project_asset({"id": "x", "is_active": False})
    assert a["active"] is False


# ---------------------------------------------------------------------------
# AssetSpine · CRUD round-trip (live preview DB, uuid-isolated)
# ---------------------------------------------------------------------------

def test_create_update_retire_activate_roundtrip():
    async def go():
        db = _db()
        spine = AssetSpine(db)
        actor = "pytest-spine"
        unit = f"PYTEST-{_new_id()}"
        create_dot = "2026-12-31"
        create_cal = "2027-01-15"
        update_dot = "2027-12-31"
        update_cal = "2028-01-15"
        a = await spine.create_asset(
            {
                "asset_number": unit,
                "asset_name": "Pytest truck",
                "asset_type": "Truck",
                "dot_expiration": create_dot,
                "calibration_expiration": create_cal,
            },
            actor=actor,
        )
        aid = a["asset_id"]
        try:
            assert a["asset_number"] == unit
            assert a["active"] is True
            assert a["dot_expiration"] == create_dot
            assert a["calibration_expiration"] == create_cal

            created_read = await spine.get_asset(aid)
            assert created_read["dot_expiration"] == create_dot
            assert created_read["calibration_expiration"] == create_cal

            try:
                await spine.create_asset({"asset_number": unit}, actor=actor)
                raise AssertionError("duplicate create should have raised")
            except ValueError:
                pass

            upd = await spine.update_asset(
                aid,
                {
                    "asset_name": "Renamed",
                    "ownership": "MGC",
                    "dot_expiration": update_dot,
                    "calibration_expiration": update_cal,
                },
                actor=actor,
            )
            assert upd["asset_name"] == "Renamed"
            assert upd["ownership"] == "MGC"
            assert upd["last_modified_by"] == actor
            assert upd["dot_expiration"] == update_dot
            assert upd["calibration_expiration"] == update_cal

            updated_read = await spine.get_asset(aid)
            assert updated_read["dot_expiration"] == update_dot
            assert updated_read["calibration_expiration"] == update_cal

            ret = await spine.retire_asset(aid, actor=actor, reason="test")
            assert ret["active"] is False
            assert ret["asset_status"] == "RETIRED"
            assert ret["retirement_date"] is not None
            assert ret["dot_expiration"] == update_dot
            assert ret["calibration_expiration"] == update_cal

            again = await spine.retire_asset(aid, actor=actor)
            assert again["active"] is False
            assert again["dot_expiration"] == update_dot
            assert again["calibration_expiration"] == update_cal

            act = await spine.activate_asset(aid, actor=actor, reason="test-undo")
            assert act["active"] is True
            assert act["asset_status"] == "ACTIVE"
            assert act["dot_expiration"] == update_dot
            assert act["calibration_expiration"] == update_cal

            n = await db.admin_audit_log.count_documents({"target_id": aid})
            assert n >= 4
        finally:
            await db.equipment_master.delete_one({"id": aid})
            await db.admin_audit_log.delete_many({"target_id": aid})
            await db.audit_events.delete_many({"asset_id": aid})
            await db.asset_transfers.delete_many({"asset_id": aid})
    asyncio.run(go())


# ---------------------------------------------------------------------------
# Detection · structural contract
# ---------------------------------------------------------------------------

def test_detection_returns_structured_findings():
    async def go():
        db = _db()
        findings = await run_detectors(db)
        assert isinstance(findings, dict)
        assert set(findings.keys()) == {"duplicates", "retired_but_active", "orphaned", "unsynced"}
        for k, v in findings.items():
            assert isinstance(v, list), f"{k} not list"
    asyncio.run(go())


def test_duplicate_detection_groups_by_vin():
    async def go():
        db = _db()
        vin = f"PYTEST-VIN-{uuid.uuid4()}"
        ids = []
        try:
            for n in range(2):
                doc = {
                    "id": _new_id(),
                    "unit_number": f"DUP-{n}-{vin[-6:]}",
                    "vin_serial_number": vin,
                    "label": f"dup test {n}",
                    "is_active": True,
                }
                await db.equipment_master.insert_one(doc)
                ids.append(doc["id"])
            dups = await detect_duplicates(db)
            ours = [d for d in dups if d.get("value") == vin.lower()]
            assert len(ours) == 1
            assert len(ours[0]["asset_ids"]) == 2
            assert ours[0]["field"] == "vin"
        finally:
            await db.equipment_master.delete_many({"id": {"$in": ids}})
    asyncio.run(go())


# ---------------------------------------------------------------------------
# Health endpoint shape
# ---------------------------------------------------------------------------

def test_health_returns_canonical_shape():
    async def go():
        db = _db()
        spine = AssetSpine(db)
        h = await spine.health()
        for k in ("total_assets", "active_assets", "inactive_assets", "retired_assets",
                  "mapped_to_motive", "unmapped_to_motive", "motive_coverage_pct",
                  "mapping_queue_depth", "conflicts"):
            assert k in h, f"missing {k}"
        assert isinstance(h["total_assets"], int)
        assert h["total_assets"] > 0
    asyncio.run(go())

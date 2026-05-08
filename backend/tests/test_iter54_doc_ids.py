"""
iter54 — Human-readable doc IDs across every submission collection.

Tests the doc_ids module: minting, idempotence, year buckets, backfill,
admin lookup, and the field_leadership prefix resolver.

Doesn't require pytest-asyncio — uses plain asyncio.run() per test so
async code runs inside a regular sync pytest function.
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")
sys.path.insert(0, "/app/backend")

from doc_ids import (  # noqa: E402
    REGISTRY,
    _field_leadership_prefix,
    _year_for,
    backfill_collection,
    ensure_doc_id,
    find_record_by_doc_id,
    mint_doc_id,
)

TEST_DB_NAME = f"{os.environ['DB_NAME']}_iter54"


def _with_db(coro_factory):
    """Run an async coroutine that takes (db) inside a fresh asyncio loop.

    Each test gets its own client + a freshly-dropped DB so counters and
    backfill state don't leak across tests."""
    async def runner():
        client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = client[TEST_DB_NAME]
        await client.drop_database(TEST_DB_NAME)
        try:
            return await coro_factory(db)
        finally:
            await client.drop_database(TEST_DB_NAME)
            client.close()
    return asyncio.run(runner())


def test_mint_doc_id_atomic_per_year():
    async def go(db):
        one = await mint_doc_id(db, "PRE", when="2026-05-08T10:00:00Z")
        two = await mint_doc_id(db, "PRE", when="2026-08-01T10:00:00Z")
        three = await mint_doc_id(db, "PRE", when="2027-01-01T00:00:00Z")
        return one, two, three
    one, two, three = _with_db(go)
    assert one == "PRE-2026-00001"
    assert two == "PRE-2026-00002"
    assert three == "PRE-2027-00001"


def test_mint_doc_id_concurrent_safe():
    """Spawn 50 concurrent mints — every doc_id must be unique."""
    async def go(db):
        return await asyncio.gather(
            *[mint_doc_id(db, "DR", when="2026-05-08T10:00:00Z") for _ in range(50)]
        )
    results = _with_db(go)
    assert len(set(results)) == 50
    seqs = sorted(int(r.split("-")[-1]) for r in results)
    assert seqs == list(range(1, 51))


def test_ensure_doc_id_idempotent():
    async def go(db):
        doc = {"id": "abc", "kind": "equipment_checkout"}
        first = await ensure_doc_id(db, doc, "EQC")
        second = await ensure_doc_id(db, doc, "EQC")
        return first, second, doc["doc_id"]
    first, second, stored = _with_db(go)
    assert first == second == stored


def test_field_leadership_prefix_resolver():
    assert _field_leadership_prefix({"kind": "equipment_checkout"}) == "EQC"
    assert _field_leadership_prefix({"kind": "equipment_return"}) == "EQR"
    assert _field_leadership_prefix({"kind": "near_miss"}) == "FLM"
    assert _field_leadership_prefix({"kind": "anything_else"}) == "FL"
    assert _field_leadership_prefix({}) == "FL"


def test_year_for_resolver():
    assert _year_for("2026-05-08") == 2026
    assert _year_for("2026-12-31T23:00:00Z") == 2026
    # 11pm EST Dec 31 is 4am UTC Jan 1 → next year
    assert _year_for("2026-12-31T23:00:00-05:00") == 2027
    assert _year_for(datetime(2024, 6, 1, tzinfo=timezone.utc)) == 2024


def test_backfill_collection_walks_chronologically():
    async def go(db):
        await db.daily_reports.insert_many([
            {"id": "a", "report_date": "2026-05-03", "doc_id": ""},
            {"id": "b", "report_date": "2026-05-01", "doc_id": ""},
            {"id": "c", "report_date": "2026-05-02", "doc_id": ""},
        ])
        n = await backfill_collection(db, "daily_reports", "DR", sort_key="report_date")
        rows = await db.daily_reports.find(
            {}, {"_id": 0, "id": 1, "doc_id": 1}
        ).to_list(10)
        return n, sorted(rows, key=lambda r: r["doc_id"])
    n, rows = _with_db(go)
    assert n == 3
    assert rows[0]["id"] == "b" and rows[0]["doc_id"] == "DR-2026-00001"
    assert rows[1]["id"] == "c" and rows[1]["doc_id"] == "DR-2026-00002"
    assert rows[2]["id"] == "a" and rows[2]["doc_id"] == "DR-2026-00003"


def test_backfill_idempotent_on_second_run():
    async def go(db):
        await db.daily_reports.insert_one(
            {"id": "a", "report_date": "2026-05-01", "doc_id": ""}
        )
        n1 = await backfill_collection(db, "daily_reports", "DR", sort_key="report_date")
        n2 = await backfill_collection(db, "daily_reports", "DR", sort_key="report_date")
        return n1, n2
    n1, n2 = _with_db(go)
    assert n1 == 1
    assert n2 == 0


def test_find_by_doc_id_cross_collection():
    async def go(db):
        await db.daily_reports.insert_one(
            {"id": "dr1", "report_date": "2026-05-01", "doc_id": "DR-2026-00007"}
        )
        await db.equipment_inspections.insert_one(
            {"id": "ei1", "doc_id": "PRE-2026-00042"}
        )
        await db.field_leadership_records.insert_one(
            {"id": "fl1", "kind": "equipment_return", "doc_id": "EQR-2026-00012"}
        )
        return {
            "dr": await find_record_by_doc_id(db, "DR-2026-00007"),
            "lower_pre": await find_record_by_doc_id(db, "pre-2026-00042"),
            "eqr": await find_record_by_doc_id(db, "EQR-2026-00012"),
            "fake": await find_record_by_doc_id(db, "FAKE-9999-99999"),
        }
    out = _with_db(go)
    assert out["dr"] and out["dr"]["collection"] == "daily_reports"
    assert out["lower_pre"] and out["lower_pre"]["collection"] == "equipment_inspections"
    assert out["eqr"] and out["eqr"]["collection"] == "field_leadership_records"
    assert out["fake"] is None


def test_registry_includes_all_known_collections():
    """Guardrail: if someone adds a new submission collection, the
    REGISTRY must be updated. We pin the current list so an accidental
    delete shows up in CI."""
    expected = {
        "equipment_inspections", "daily_reports", "inspections", "meetings",
        "jhas", "incidents", "qaqc_inspections", "field_leadership_records",
        "safety_equipment_issuances", "safety_equipment_trainings",
    }
    actual = {entry[0] for entry in REGISTRY}
    assert actual == expected, (
        f"REGISTRY drift: missing={expected - actual}, extra={actual - expected}"
    )

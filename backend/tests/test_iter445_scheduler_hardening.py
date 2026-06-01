"""Tests for iter445 · Sprint · Scheduler Hardening.

Run directly: `python -m pytest tests/test_iter445_scheduler_hardening.py -v`

Uses plain asyncio.run() per test (no pytest-asyncio dependency).

Verifies:
  1. claim_slot dedup — concurrent claims for the same slot · first wins
  2. claim_slot — different slots / different schedulers don't false-dedup
  3. mark_completed sets duration + status
  4. mark_failed records error
  5. heartbeat_loop cancels scheduler_task on lock-loss
"""
import asyncio
import os
import sys
import time
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.scheduler_runs import (  # noqa: E402
    claim_slot,
    mark_completed,
    mark_failed,
    ensure_scheduler_runs_indexes,
    SCHEDULER_RUNS_COLLECTION,
)
from lib.singleton_scheduler import _heartbeat_loop  # noqa: E402


def _read_mongo_url():
    path = "/app/backend/.env"
    try:
        with open(path) as f:
            for line in f:
                if line.startswith("MONGO_URL="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return os.environ.get("MONGO_URL") or "mongodb://localhost:27017"


async def _setup_db():
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient(_read_mongo_url())
    db = client.get_database("scheduler_test_iter445")
    await ensure_scheduler_runs_indexes(db)
    await db[SCHEDULER_RUNS_COLLECTION].delete_many({})
    return client, db


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


def test_claim_slot_dedup_first_wins():
    async def go():
        client, db = await _setup_db()
        try:
            slot_key = "2026-06-01T14:00:00+00:00"
            a = await claim_slot(db, "po_digest", slot_key, owner_id="podA")
            assert a is not None
            assert a["scheduler"] == "po_digest"
            assert a["slot_key"] == slot_key
            assert a["owner_id"] == "podA"
            assert a["status"] == "in_progress"

            b = await claim_slot(db, "po_digest", slot_key, owner_id="podB")
            assert b is None, "second claim must lose"

            doc = await db[SCHEDULER_RUNS_COLLECTION].find_one(
                {"scheduler": "po_digest", "slot_key": slot_key},
                {"_id": 0},
            )
            assert doc is not None
            assert doc["owner_id"] == "podA"
            assert doc.get("dedup_attempts") == 1
            log = doc.get("dedup_attempt_log") or []
            assert len(log) == 1
            assert log[0]["owner_id"] == "podB"
        finally:
            await db[SCHEDULER_RUNS_COLLECTION].delete_many({})
            client.close()
    _run(go())


def test_claim_slot_different_slots_both_succeed():
    async def go():
        client, db = await _setup_db()
        try:
            a = await claim_slot(db, "po_digest", "2026-06-01T14:00:00+00:00", owner_id="podA")
            b = await claim_slot(db, "po_digest", "2026-06-08T14:00:00+00:00", owner_id="podA")
            assert a is not None and b is not None
        finally:
            await db[SCHEDULER_RUNS_COLLECTION].delete_many({})
            client.close()
    _run(go())


def test_claim_slot_different_schedulers_isolated():
    async def go():
        client, db = await _setup_db()
        try:
            slot_key = "2026-06-01T14:00:00+00:00"
            a = await claim_slot(db, "po_digest", slot_key, owner_id="podA")
            b = await claim_slot(db, "safety_digest", slot_key, owner_id="podA")
            assert a is not None and b is not None
        finally:
            await db[SCHEDULER_RUNS_COLLECTION].delete_many({})
            client.close()
    _run(go())


def test_mark_completed_sets_duration():
    async def go():
        client, db = await _setup_db()
        try:
            slot_key = "2026-06-01T14:00:00+00:00"
            await claim_slot(db, "po_digest", slot_key, owner_id="podA")
            await asyncio.sleep(0.05)
            await mark_completed(db, "po_digest", slot_key, recipients=11)
            doc = await db[SCHEDULER_RUNS_COLLECTION].find_one(
                {"scheduler": "po_digest", "slot_key": slot_key},
                {"_id": 0},
            )
            assert doc["status"] == "done"
            assert doc["recipients"] == 11
            assert doc.get("duration_s", 0) >= 0.04
            assert doc.get("finished_at") is not None
        finally:
            await db[SCHEDULER_RUNS_COLLECTION].delete_many({})
            client.close()
    _run(go())


def test_mark_failed_records_error():
    async def go():
        client, db = await _setup_db()
        try:
            slot_key = "2026-06-01T14:00:00+00:00"
            await claim_slot(db, "po_digest", slot_key, owner_id="podA")
            await mark_failed(db, "po_digest", slot_key, error="boom")
            doc = await db[SCHEDULER_RUNS_COLLECTION].find_one(
                {"scheduler": "po_digest", "slot_key": slot_key},
                {"_id": 0},
            )
            assert doc["status"] == "failed"
            assert doc["error"] == "boom"
            assert doc["recipients"] == 0
        finally:
            await db[SCHEDULER_RUNS_COLLECTION].delete_many({})
            client.close()
    _run(go())


def test_concurrent_claims_only_one_wins():
    async def go():
        client, db = await _setup_db()
        try:
            slot_key = "2026-06-01T14:00:00+00:00"
            results = await asyncio.gather(*[
                claim_slot(db, "po_digest", slot_key, owner_id=f"pod{i}")
                for i in range(20)
            ])
            winners = [r for r in results if r is not None]
            losers = [r for r in results if r is None]
            assert len(winners) == 1, f"expected 1 winner, got {len(winners)}"
            assert len(losers) == 19

            doc = await db[SCHEDULER_RUNS_COLLECTION].find_one(
                {"scheduler": "po_digest", "slot_key": slot_key},
                {"_id": 0},
            )
            assert doc["dedup_attempts"] == 19
            assert len(doc["dedup_attempt_log"]) == 19
        finally:
            await db[SCHEDULER_RUNS_COLLECTION].delete_many({})
            client.close()
    _run(go())


def test_heartbeat_cancels_scheduler_on_lock_loss():
    async def go():
        client, db = await _setup_db()
        try:
            cancelled = asyncio.Event()

            async def fake_scheduler():
                try:
                    await asyncio.sleep(60)
                except asyncio.CancelledError:
                    cancelled.set()
                    raise

            sched_task = asyncio.create_task(fake_scheduler())

            import lib.singleton_scheduler as ss
            original_refresh = ss._refresh_lock
            original_interval = ss.HEARTBEAT_INTERVAL_SECONDS
            ss.HEARTBEAT_INTERVAL_SECONDS = 0.05

            async def fake_refresh(*a, **k):
                return False  # simulate immediate lock loss
            ss._refresh_lock = fake_refresh

            try:
                hb_task = asyncio.create_task(
                    _heartbeat_loop(db, "po_digest", "podA", sched_task)
                )
                await asyncio.wait_for(hb_task, timeout=2.0)
                await asyncio.wait_for(cancelled.wait(), timeout=2.0)
                # Give the event loop a moment to mark sched_task as cancelled
                await asyncio.sleep(0)
                assert sched_task.cancelled() or sched_task.done()
            finally:
                ss._refresh_lock = original_refresh
                ss.HEARTBEAT_INTERVAL_SECONDS = original_interval
                if not sched_task.done():
                    sched_task.cancel()
                    try:
                        await sched_task
                    except Exception:
                        pass
        finally:
            client.close()
    _run(go())

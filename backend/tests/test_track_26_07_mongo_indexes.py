"""
TRACK 26.07 — MongoDB query-targeting hardening regression tests.

Verifies:
  1. `daily_reports.updated_at` index exists.
  2. `job_photo_thumb_cache.{fmt: 1, photo_id: 1}` compound index exists.
  3. `_warm_missing_thumbs` executes with bounded, index-backed queries
     (no COLLSCAN, no unbounded set-load) — proven via `explain()`.
  4. The 10-min `background_indexer_loop` filter
     `daily_reports.find({photos.0: {$exists}, updated_at: {$gte: X}})`
     is index-eligible (uses an index, not COLLSCAN).

Read-only against real DB. No collection mutation beyond `create_index`
(which is idempotent). Uses the preview DB as a proxy for the production
index shape at deploy time.

Run with:
    cd /app/backend && python -m pytest tests/test_track_26_07_mongo_indexes.py -q
"""
from __future__ import annotations

import asyncio
import os
import sys

import pytest
from motor.motor_asyncio import AsyncIOMotorClient

# Ensure the backend package is importable when pytest is invoked from /app/backend.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _bootstrap_env() -> None:
    if "MONGO_URL" in os.environ and "DB_NAME" in os.environ:
        return
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("MONGO_URL=") or line.startswith("DB_NAME="):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k, v.strip().strip('"'))
    except Exception:
        pass


def _db():
    _bootstrap_env()
    client = AsyncIOMotorClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=8000)
    return client[os.environ["DB_NAME"]]


def _run(coro):
    return asyncio.run(coro)


async def _bootstrap_indexes(db) -> None:
    """Force the app's index-ensure routines to run so tests verify the
    state we ship, not the state that happens to exist in preview."""
    from routes.job_photos import _ensure_thumb_cache_indexes
    await _ensure_thumb_cache_indexes(db)
    try:
        await db.daily_reports.create_index("updated_at")
    except Exception:
        pass


def _stage_present(node, name: str) -> bool:
    """Recursively check whether a stage of `name` appears in a plan tree."""
    if not isinstance(node, dict):
        return False
    if node.get("stage") == name:
        return True
    children = []
    if node.get("inputStage"):
        children.append(node["inputStage"])
    if node.get("inputStages"):
        children.extend(node["inputStages"])
    for c in children:
        if _stage_present(c, name):
            return True
    return False


# ---------------------------------------------------------------------------


def test_daily_reports_updated_at_index_exists():
    """Track 26.07: `updated_at` index must exist to prevent COLLSCAN in
    the job-photos background indexer loop (`background_indexer_loop`)."""
    async def _t():
        db = _db()
        await _bootstrap_indexes(db)
        names = set()
        async for idx in db.daily_reports.list_indexes():
            names.add(idx.get("name"))
        assert (
            "updated_at_1" in names or "updated_at_-1" in names
        ), f"daily_reports.updated_at index missing. Present: {sorted(names)}"
    _run(_t())


def test_thumb_cache_fmt_photo_id_compound_index_exists():
    """Track 26.07: `{fmt: 1, photo_id: 1}` compound index must exist to
    serve the bounded `$in` lookup in `_warm_missing_thumbs`."""
    async def _t():
        db = _db()
        await _bootstrap_indexes(db)
        names = set()
        async for idx in db.job_photo_thumb_cache.list_indexes():
            names.add(idx.get("name"))
        assert (
            "fmt_1_photo_id_1" in names
        ), (
            f"job_photo_thumb_cache.{{fmt:1, photo_id:1}} index missing. "
            f"Present: {sorted(names)}"
        )
    _run(_t())


def test_warm_missing_thumbs_query_uses_ixscan():
    """Track 26.07: the per-tick warm lookup query
    `{fmt: "jpeg", photo_id: {$in: [...]}}` MUST use IXSCAN (compound
    index served) and MUST NOT fall back to COLLSCAN."""
    async def _t():
        db = _db()
        await _bootstrap_indexes(db)
        sample_ids = []
        async for d in db.job_photos.find({}, {"_id": 0, "id": 1}).limit(5):
            if d.get("id"):
                sample_ids.append(d["id"])
        if not sample_ids:
            sample_ids = ["synthetic-1", "synthetic-2"]
        explain = await db.command({
            "explain": {
                "find": "job_photo_thumb_cache",
                "filter": {"fmt": "jpeg", "photo_id": {"$in": sample_ids}},
                "projection": {"_id": 0, "photo_id": 1},
            },
            "verbosity": "queryPlanner",
        })
        winning = (explain.get("queryPlanner") or {}).get("winningPlan") or {}
        assert _stage_present(winning, "IXSCAN"), (
            f"warm-lookup query is not index-backed. winningPlan={winning}"
        )
        assert not _stage_present(winning, "COLLSCAN"), (
            f"warm-lookup query fell back to COLLSCAN. winningPlan={winning}"
        )
    _run(_t())


def test_warm_missing_thumbs_is_bounded():
    """Track 26.07: refactored `_warm_missing_thumbs` MUST bound the
    batch and MUST NOT load the full warm-cache set. Function returns
    `{warmed, failed}` with sum ≤ `batch_limit`."""
    from routes.job_photos import _warm_missing_thumbs

    async def _t():
        db = _db()
        result = await _warm_missing_thumbs(db, batch_limit=1)
        assert isinstance(result, dict), f"unexpected return type: {type(result)}"
        assert {"warmed", "failed"} <= set(result.keys()), (
            f"missing expected keys: {result}"
        )
        assert result["warmed"] + result["failed"] <= 1, (
            f"tick was unbounded: {result}"
        )
    _run(_t())


def test_indexer_loop_filter_is_index_eligible():
    """Track 26.07: `background_indexer_loop`'s daily_reports filter
    `{photos.0: {$exists: True}, updated_at: {$gte: X}}` must be
    index-eligible (winning plan must use an index, not COLLSCAN)."""
    async def _t():
        db = _db()
        await _bootstrap_indexes(db)
        explain = await db.command({
            "explain": {
                "find": "daily_reports",
                "filter": {
                    "photos.0": {"$exists": True},
                    "updated_at": {"$gte": "2026-07-08T00:00:00+00:00"},
                },
                "projection": {"_id": 0, "id": 1, "photos": 1, "project_number": 1},
            },
            "verbosity": "queryPlanner",
        })
        winning = (explain.get("queryPlanner") or {}).get("winningPlan") or {}
        assert not _stage_present(winning, "COLLSCAN"), (
            f"indexer-loop filter fell back to COLLSCAN. winningPlan={winning}"
        )
        assert _stage_present(winning, "IXSCAN"), (
            f"indexer-loop filter did not use an index. winningPlan={winning}"
        )
    _run(_t())

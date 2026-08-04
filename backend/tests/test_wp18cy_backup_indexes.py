from __future__ import annotations

import asyncio
import os
import sys

from motor.motor_asyncio import AsyncIOMotorClient


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _bootstrap_env() -> None:
    if "MONGO_URL" in os.environ and "DB_NAME" in os.environ:
        return
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("MONGO_URL=") or line.startswith("DB_NAME="):
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v.strip().strip('"'))


def _db():
    _bootstrap_env()
    client = AsyncIOMotorClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=8000)
    return client[os.environ["DB_NAME"]]


def _run(coro):
    return asyncio.run(coro)


def _stage_present(node, name: str) -> bool:
    if not isinstance(node, dict):
        return False
    if node.get("stage") == name:
        return True
    children = []
    if node.get("inputStage"):
        children.append(node["inputStage"])
    if node.get("inputStages"):
        children.extend(node["inputStages"])
    for child in children:
        if _stage_present(child, name):
            return True
    return False


async def _bootstrap_indexes(db) -> None:
    await db.backup_health.create_index(
        [("mode", 1), ("ts", -1)],
        name="backup_health_mode_ts_desc",
    )
    await db.backup_health.create_index(
        [("ok", 1), ("ts", -1)],
        name="backup_health_ok_ts_desc",
    )
    await db.drill_runs.create_index(
        [("state", 1), ("started_at", -1)],
        name="drill_runs_state_started_desc",
    )


def test_backup_health_indexes_exist():
    async def _t():
        db = _db()
        await _bootstrap_indexes(db)
        names = set()
        async for idx in db.backup_health.list_indexes():
            names.add(idx.get("name"))
        assert "backup_health_mode_ts_desc" in names
        assert "backup_health_ok_ts_desc" in names
    _run(_t())


def test_drill_runs_index_exists():
    async def _t():
        db = _db()
        await _bootstrap_indexes(db)
        names = set()
        async for idx in db.drill_runs.list_indexes():
            names.add(idx.get("name"))
        assert "drill_runs_state_started_desc" in names
    _run(_t())


def test_backup_health_latest_success_query_uses_ixscan():
    async def _t():
        db = _db()
        await _bootstrap_indexes(db)
        explain = await db.command({
            "explain": {
                "find": "backup_health",
                "filter": {"ok": True},
                "sort": {"ts": -1},
                "limit": 5,
                "projection": {"_id": 0, "ts": 1, "mode": 1, "filename": 1},
            },
            "verbosity": "queryPlanner",
        })
        winning = (explain.get("queryPlanner") or {}).get("winningPlan") or {}
        assert _stage_present(winning, "IXSCAN"), winning
        assert not _stage_present(winning, "COLLSCAN"), winning
    _run(_t())


def test_drill_runs_latest_done_query_uses_ixscan():
    async def _t():
        db = _db()
        await _bootstrap_indexes(db)
        explain = await db.command({
            "explain": {
                "find": "drill_runs",
                "filter": {"state": "done"},
                "sort": {"started_at": -1},
                "limit": 5,
                "projection": {"_id": 0, "started_at": 1, "finished_at": 1, "outcome": 1},
            },
            "verbosity": "queryPlanner",
        })
        winning = (explain.get("queryPlanner") or {}).get("winningPlan") or {}
        assert _stage_present(winning, "IXSCAN"), winning
        assert not _stage_present(winning, "COLLSCAN"), winning
    _run(_t())
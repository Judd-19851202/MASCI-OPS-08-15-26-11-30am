from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import sys

sys.path.insert(0, "/app/backend")

import server  # noqa: E402


class _LocksCollection:
    def __init__(self, row):
        self.row = row

    async def find_one(self, query, projection):
        threshold = query["expires_at"]["$lt"]
        expires_at = self.row.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at < threshold:
            return {"scheduler": self.row.get("scheduler")}
        return None


class _Db:
    def __init__(self, row):
        self.scheduler_locks = _LocksCollection(row)


def test_stale_scheduler_lock_truth_accepts_bson_datetime() -> None:
    db = _Db({
        "scheduler": "backup_scheduler",
        "expires_at": datetime.now(timezone.utc) - timedelta(minutes=5),
    })

    out = asyncio.run(server._stale_scheduler_lock_present(db))
    assert out is True
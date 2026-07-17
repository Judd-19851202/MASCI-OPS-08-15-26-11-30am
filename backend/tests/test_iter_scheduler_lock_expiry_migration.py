from datetime import datetime, timezone

import pytest

from lib.singleton_scheduler import _coerce_lock_expiry, migrate_string_lock_expiries


def test_coerce_lock_expiry_accepts_iso_z_string():
    parsed = _coerce_lock_expiry("2026-07-17T11:02:49.354000Z")
    assert isinstance(parsed, datetime)
    assert parsed.tzinfo is not None
    assert parsed == datetime(2026, 7, 17, 11, 2, 49, 354000, tzinfo=timezone.utc)


class _AsyncCursor:
    def __init__(self, rows):
        self._rows = list(rows)
        self._index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._index >= len(self._rows):
            raise StopAsyncIteration
        item = self._rows[self._index]
        self._index += 1
        return item


class _AsyncResult:
    def __init__(self, modified_count):
        self.modified_count = modified_count


class _AsyncCollection:
    def __init__(self, rows):
        self.rows = rows

    def find(self, query=None, *_args, **_kwargs):
        query = query or {}
        rows = self.rows
        expires_q = query.get("expires_at") or {}
        if expires_q.get("$type") == "string":
            rows = [row for row in rows if isinstance(row.get("expires_at"), str)]
        return _AsyncCursor(rows)

    async def update_one(self, query, update):
        for row in self.rows:
            if row["_id"] == query["_id"]:
                row["expires_at"] = update["$set"]["expires_at"]
                return _AsyncResult(1)
        return _AsyncResult(0)


class _AsyncDb:
    def __init__(self, rows):
        self._coll = _AsyncCollection(rows)

    def __getitem__(self, _name):
        return self._coll


@pytest.mark.asyncio
async def test_migrate_string_lock_expiries_updates_string_values():
    rows = [
        {"_id": "backup_scheduler", "expires_at": "2026-07-17T11:02:49.354000Z"},
        {"_id": "digest_scheduler", "expires_at": datetime(2026, 7, 17, 11, 3, 0, tzinfo=timezone.utc)},
    ]
    db = _AsyncDb(rows)
    migrated = await migrate_string_lock_expiries(db)
    assert migrated == 1
    assert isinstance(rows[0]["expires_at"], datetime)
    assert rows[0]["expires_at"].tzinfo is not None
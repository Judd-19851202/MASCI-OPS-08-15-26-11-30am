from __future__ import annotations

import asyncio
import sys
from types import SimpleNamespace

sys.path.insert(0, "/app/backend")

from routes.governance import _issue_missing_ppe_records  # noqa: E402


class _AsyncCursor:
    def __init__(self, rows):
        self.rows = list(rows)

    def limit(self, _n):
        return self

    async def __aiter__(self):
        for row in self.rows:
            yield row


class _Collection:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.upserts = []

    def find(self, *_args, **_kwargs):
        return _AsyncCursor(self.rows)

    async def update_one(self, flt, update, upsert=False):
        self.upserts.append({"filter": flt, "update": update, "upsert": upsert})


class _Db(SimpleNamespace):
    pass


def test_issue_missing_ppe_records_dry_run_lists_missing_employees() -> None:
    db = _Db(
        employees=_Collection([
            {"id": "EMP-1", "name": "Alice Crew", "is_active": True, "is_field": True},
            {"id": "EMP-2", "name": "Bob Field", "is_active": True, "is_field": True},
        ]),
        safety_equipment_issuances=_Collection([
            {"employee_name": "Alice Crew"},
        ]),
    )

    out = asyncio.run(_issue_missing_ppe_records(db, dry_run=True, issued_by="QA", default_items=["Hard Hat"]))
    assert out["missing_employee_count"] == 1
    assert out["created_count"] == 0
    assert out["preview"][0]["employee_name"] == "Bob Field"


def test_issue_missing_ppe_records_writes_upserts_when_not_dry_run() -> None:
    issuance_collection = _Collection([])
    db = _Db(
        employees=_Collection([
            {"id": "EMP-9", "name": "Charlie Crew", "is_active": True, "is_field": True},
        ]),
        safety_equipment_issuances=issuance_collection,
    )

    out = asyncio.run(_issue_missing_ppe_records(db, dry_run=False, issued_by="QA", default_items=["Vest"]))
    assert out["created_count"] == 1
    assert len(issuance_collection.upserts) == 1
    payload = issuance_collection.upserts[0]["update"]["$setOnInsert"]
    assert payload["employee_name"] == "Charlie Crew"
    assert payload["items"][0]["name"] == "Vest"
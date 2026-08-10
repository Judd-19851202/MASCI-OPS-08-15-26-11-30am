from __future__ import annotations

import asyncio
import sys
from types import SimpleNamespace

sys.path.insert(0, "/app/backend")

from routes.governance import _backfill_employee_links, _employee_ppe_applicability, _issue_missing_ppe_records  # noqa: E402


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
        if self.rows and "$set" in update and flt.get("id"):
            for row in self.rows:
                if row.get("id") == flt.get("id"):
                    row.update(update["$set"])


class _Db(SimpleNamespace):
    def __getitem__(self, key):
        return getattr(self, key)


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


def test_employee_ppe_applicability_requires_affirmative_field_signal() -> None:
    assert _employee_ppe_applicability({"name": "Unknown", "is_field": None}) == {
        "requires_ppe": False,
        "reason": "missing_field_applicability_evidence",
    }
    assert _employee_ppe_applicability({"name": "Crew", "trade": "General Laborer"}) == {
        "requires_ppe": True,
        "reason": "trade_signal",
    }
    assert _employee_ppe_applicability({"name": "Office", "trade": "Accounting Clerk", "crew": "Accounting"}) == {
        "requires_ppe": False,
        "reason": "office_or_admin_role",
    }


def test_issue_missing_ppe_records_skips_employees_without_field_applicability() -> None:
    db = _Db(
        employees=_Collection([
            {"id": "EMP-10", "name": "Sparse Person", "is_active": True},
            {"id": "EMP-11", "name": "Accounting Person", "is_active": True, "trade": "Accounting Clerk", "crew": "Accounting"},
            {"id": "EMP-12", "name": "Field Person", "is_active": True, "trade": "General Laborer"},
        ]),
        safety_equipment_issuances=_Collection([]),
    )

    out = asyncio.run(_issue_missing_ppe_records(db, dry_run=True, issued_by="QA", default_items=["Vest"]))
    assert out["missing_employee_count"] == 1
    assert out["preview"][0]["employee_name"] == "Field Person"


def test_backfill_employee_links_updates_daily_report_crew_employee_ids() -> None:
    daily_reports = _Collection([
        {
            "id": "DR-1",
            "masci_crews": [
                {"name": "Amado Delfin", "trade": "Earthwork"},
                {"name": "x", "trade": "Earthwork"},
            ],
        }
    ])
    db = _Db(
        employees=_Collection([
            {"id": "EMP-12", "name": "Amado Delfin", "is_active": True},
        ]),
        daily_reports=daily_reports,
        safety_training_records=_Collection([]),
        safety_equipment_issuances=_Collection([]),
        corrective_actions=_Collection([]),
        incidents=_Collection([]),
    )

    preview = asyncio.run(_backfill_employee_links(db, dry_run=True))
    assert preview["per_collection"]["daily_reports"]["backfilled"] == 1

    committed = asyncio.run(_backfill_employee_links(db, dry_run=False))
    assert committed["per_collection"]["daily_reports"]["backfilled"] == 1
    assert daily_reports.rows[0]["masci_crews"][0]["employee_id"] == "EMP-12"
    assert "employee_id" not in daily_reports.rows[0]["masci_crews"][1]

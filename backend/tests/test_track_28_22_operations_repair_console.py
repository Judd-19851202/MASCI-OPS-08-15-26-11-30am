from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.r2_retention_authority import build_retention_rows, retention_policy_payload  # noqa: E402
from services.operations_control import build_registry  # noqa: E402


class _AsyncCursor:
    def __init__(self, rows):
        self.rows = list(rows)

    def sort(self, *_args, **_kwargs):
        return self

    def limit(self, n):
        self.rows = self.rows[:n]
        return self

    async def __aiter__(self):
        for row in self.rows:
            yield row


class _Collection:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.updates = []

    def find(self, *_args, **_kwargs):
        return _AsyncCursor(self.rows)

    async def update_one(self, flt, update, upsert=False):
        self.updates.append({"filter": flt, "update": update, "upsert": upsert})


class _Db(SimpleNamespace):
    def __getitem__(self, name):
        return getattr(self, name)


def _run(coro):
    return asyncio.run(coro)


def test_registry_includes_governance_repairs():
    registry = build_registry(db=None)
    assert "governance.employee_link_backfill" in registry
    assert "governance.issue_missing_ppe" in registry
    assert registry["governance.employee_link_backfill"].requires_dry_run is True
    assert registry["governance.issue_missing_ppe"].requires_dry_run is True


def test_employee_link_repair_dry_run_reports_candidates():
    db = _Db(
        employees=_Collection([
            {"id": "EMP-1", "name": "Alice Crew", "is_active": True},
            {"id": "EMP-2", "name": "Bob Field", "is_active": True},
        ]),
        incidents=_Collection([{"id": "INC-1", "person_name": "Alice Crew", "employee_id": ""}]),
        corrective_actions=_Collection([]),
        safety_training_records=_Collection([]),
        safety_equipment_issuances=_Collection([]),
    )
    op = build_registry(db)["governance.employee_link_backfill"]
    result = _run(op.dry_run_fn({"_db": db}))
    assert result["status"] == "dry_run_ready"
    assert result["candidate_count"] >= 1


def test_ppe_repair_dry_run_reports_missing_people():
    db = _Db(
        employees=_Collection([
            {"id": "EMP-1", "name": "Alice Crew", "is_active": True, "is_field": True},
            {"id": "EMP-2", "name": "Bob Field", "is_active": True, "is_field": True},
        ]),
        safety_equipment_issuances=_Collection([
            {"employee_name": "Alice Crew"},
        ]),
    )
    op = build_registry(db)["governance.issue_missing_ppe"]
    result = _run(op.dry_run_fn({"_db": db, "actor_email": "qa@example.com"}))
    assert result["status"] == "dry_run_ready"
    assert result["candidate_count"] == 1
    assert result["preview"][0]["employee_name"] == "Bob Field"


def test_retention_authority_reports_truthful_policy_and_decisions():
    rows = [
        {"key": "backups/preview/auto-90d/MASCI_complete_backup_2026-07-28_120000Z.zip", "timestamp": "2026-07-28T12:00:00+00:00", "size_bytes": 500_000_000},
        {"key": "backups/preview/auto-90d/MASCI_complete_backup_2026-07-20_120000Z.zip", "timestamp": "2026-07-20T12:00:00+00:00", "size_bytes": 450_000_000},
        {"key": "backups/preview/auto-90d/MASCI_complete_backup_2025-01-01_120000Z.zip", "timestamp": "2025-01-01T12:00:00+00:00", "size_bytes": 400_000_000},
    ]
    result = build_retention_rows(rows)
    policy = retention_policy_payload()
    assert result["policy"]["architecture"] == policy["architecture"]
    assert result["archive_count"] == 3
    assert len(result["decisions"]) == 3
    assert "survivors_by_tier" in result
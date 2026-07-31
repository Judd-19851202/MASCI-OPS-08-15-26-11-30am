from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "/app/backend")

from routes.governance import _governance_freshness  # noqa: E402
from lib import production_certification as prod_cert  # noqa: E402
from services.r2_lifecycle import health as r2_health  # noqa: E402


def test_governance_freshness_current():
    now = datetime.now(timezone.utc)
    out = _governance_freshness({"finished_at": (now - timedelta(hours=2)).isoformat(), "detector_errors": []}, now=now)
    assert out["state"] == "CURRENT"
    assert out["confidence"] == "HIGH"


def test_governance_freshness_stale():
    now = datetime.now(timezone.utc)
    out = _governance_freshness({"finished_at": (now - timedelta(days=8)).isoformat(), "detector_errors": []}, now=now)
    assert out["state"] == "STALE"
    assert out["confidence"] == "STALE"


def test_governance_freshness_scan_failed():
    now = datetime.now(timezone.utc)
    out = _governance_freshness({
        "finished_at": (now - timedelta(hours=1)).isoformat(),
        "detector_errors": [{"rule": "x"}],
    }, now=now)
    assert out["state"] == "SCAN_FAILED"
    assert out["scan_execution_health"] == "FAILED"


class _FakeFindOneCollection:
    def __init__(self, rows):
        self.rows = rows

    async def find_one(self, *_args, **_kwargs):
        return self.rows.pop(0) if self.rows else None


class _FakeAggCursor:
    def __init__(self, rows):
        self.rows = rows

    async def to_list(self, _limit):
        return list(self.rows)


class _FakeInventoryCollection:
    def __init__(self, rows):
        self.rows = rows

    def aggregate(self, _pipeline):
        return _FakeAggCursor(self.rows)


class _FakeDB:
    def __init__(self, *, usage_row, cls_row, inv_row):
        self.backup_health = _FakeFindOneCollection([usage_row])
        self.r2_lifecycle_runs = _FakeFindOneCollection([cls_row, inv_row])
        self.r2_inventory = _FakeInventoryCollection([])


def test_compute_storage_health_exposes_freshness_and_ownership(monkeypatch):
    now = datetime.now(timezone.utc)
    db = _FakeDB(
        usage_row={"size_bytes": 10 * (1024 ** 3)},
        cls_row={
            "counts": {
                "VERIFIED_OWNER": 50,
                "VERIFIED_ORPHAN": 10,
                "AMBIGUOUS": 5,
                "PENDING": 5,
                "UNKNOWN": 10,
                "SYSTEM_RESERVED": 10,
                "RETENTION_PROTECTED": 0,
                "BACKUP_PROTECTED": 0,
                "LEGAL_HOLD": 0,
                "HISTORICAL": 0,
            },
            "verified_orphan_bytes": 1234,
        },
        inv_row={
            "completed_at": (now - timedelta(days=10)).isoformat(),
            "total_objects": 100,
        },
    )

    async def fake_lineage(_db):
        return {
            "freshness_age_minutes": 30,
            "authoritative_recovery_point_time": now.isoformat(),
            "authoritative_time_source": "test",
            "lineage_confidence": "HIGH",
        }

    monkeypatch.setattr(r2_health, "build_canonical_archive_lineage", fake_lineage)
    out = asyncio.run(r2_health.compute_storage_health(db, now=now))
    assert out["freshness"]["inventory_state"] == "STALE"
    assert out["ownership"]["ownership_unresolved_pct"] == 11.1
    assert out["ownership"]["ownership_unknown_pct"] == 11.1
    assert out["ownership"]["confirmed_orphan_pct"] == 11.11


def test_production_certification_freshness_helpers_expose_policy():
    ts = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    assert prod_cert._freshness_window_for_workflow("nonexistent").total_seconds() == 48 * 3600
    assert prod_cert._evidence_age_hours(ts) >= 3
    assert prod_cert._is_stale(ts, "nonexistent") is False
    daily = prod_cert._policy_payload("daily-report")
    weekly = prod_cert._policy_payload("oppc-weekly-rollover")
    assert daily["freshness_sla_hours"] == 36
    assert weekly["freshness_sla_hours"] == 192
    assert "terminal_success_criteria" in daily
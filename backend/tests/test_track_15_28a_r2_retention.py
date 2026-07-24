from __future__ import annotations

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.r2_retention import (  # noqa: E402
    ARCHITECTURE,
    DAILY_RETENTION_DAYS,
    HOURLY_RETENTION_HOURS,
    MONTHLY_RETENTION_MONTHS,
    WEEKLY_RETENTION_DAYS,
    _parse_filename_to_ts,
    enforce_r2_retention,
    plan_retention,
)

NOW = datetime(2026, 7, 24, 12, 0, 0, tzinfo=timezone.utc)


def _mk_key(ts: datetime) -> str:
    return f"backups/auto-90d/MASCI_complete_backup_{ts.strftime('%Y-%m-%d_%H%M%S')}Z.zip"


def _dataset() -> list[dict]:
    rows = []
    for hour in range(0, 72, 6):
        ts = NOW - timedelta(hours=hour)
        rows.append({"key": _mk_key(ts), "timestamp": ts, "size_bytes": 600_000_000})
    for day in range(4, 31):
        for hour in (2, 14, 22):
            ts = NOW - timedelta(days=day, hours=23 - hour)
            rows.append({"key": _mk_key(ts), "timestamp": ts, "size_bytes": 550_000_000})
    for day in range(35, 91, 7):
        for hour in (3, 18):
            ts = NOW - timedelta(days=day, hours=23 - hour)
            rows.append({"key": _mk_key(ts), "timestamp": ts, "size_bytes": 525_000_000})
    for month in range(4, 13):
        for day in (1, 12, 23):
            ts = NOW - timedelta(days=(month * 30) + day)
            rows.append({"key": _mk_key(ts), "timestamp": ts, "size_bytes": 500_000_000})
    rows.append({"key": _mk_key(NOW - timedelta(days=500)), "timestamp": NOW - timedelta(days=500), "size_bytes": 490_000_000})
    return rows


def test_policy_constants_are_approved_values():
    assert HOURLY_RETENTION_HOURS == 72
    assert DAILY_RETENTION_DAYS == 30
    assert WEEKLY_RETENTION_DAYS == 90
    assert MONTHLY_RETENTION_MONTHS == 12
    assert ARCHITECTURE == "selected_surviving_hourly_archives"


def test_hourly_daily_weekly_monthly_windows_produce_survivors():
    plan = plan_retention(_dataset(), now=NOW)
    assert plan.survivor_counts_by_tier["hourly"] > 0
    assert plan.survivor_counts_by_tier["daily"] > 0
    assert plan.survivor_counts_by_tier["weekly"] > 0
    assert plan.survivor_counts_by_tier["monthly"] > 0
    assert plan.deleted_by_tier["expired"] >= 1


def test_newest_healthy_archive_is_always_preserved():
    rows = _dataset()
    newest = max(rows, key=lambda row: row["timestamp"])
    plan = plan_retention(rows, now=NOW)
    assert newest["key"] in plan.keep
    assert newest["key"] not in plan.delete


def test_unhealthy_and_held_archives_are_not_canonical_deletes():
    rows = _dataset()
    rows.append({
        "key": _mk_key(NOW - timedelta(days=420)),
        "timestamp": NOW - timedelta(days=420),
        "size_bytes": 480_000_000,
        "healthy": False,
    })
    rows.append({
        "key": _mk_key(NOW - timedelta(days=430)),
        "timestamp": NOW - timedelta(days=430),
        "size_bytes": 470_000_000,
        "hold": True,
    })
    plan = plan_retention(rows, now=NOW)
    special_reasons = {decision.reason for decision in plan.decisions if decision.window == "special"}
    assert "not_healthy_preserved_fail_closed" in special_reasons
    assert "protected_or_hold" in special_reasons


def test_dry_run_counts_and_projected_size_are_returned():
    plan = plan_retention(_dataset(), now=NOW)
    assert plan.would_delete_count == len(plan.delete)
    assert plan.would_preserve_count == len(plan.keep)
    assert isinstance(plan.delete_sample_keys, list)
    assert isinstance(plan.preserve_sample_keys, list)
    assert plan.projected_post_retention_size_bytes is not None


def test_second_pass_is_idempotent():
    rows = _dataset()
    first = plan_retention(rows, now=NOW)
    survivors = [row for row in rows if row["key"] in first.keep]
    second = plan_retention(survivors, now=NOW)
    assert second.delete == []
    assert second.deleted_by_tier == {"daily": 0, "weekly": 0, "monthly": 0, "expired": 0}


class _FakeS3:
    def __init__(self, rows):
        self.objects = [{"Key": row["key"], "Size": row["size_bytes"], "LastModified": row["timestamp"]} for row in rows]
        self.deleted = []

    def get_paginator(self, _name):
        outer = self

        class _Paginator:
            def paginate(self_inner, **_kwargs):
                yield {"Contents": outer.objects}

        return _Paginator()

    def delete_objects(self, *, Bucket, Delete):
        for item in Delete["Objects"]:
            self.deleted.append(item["Key"])
            self.objects = [obj for obj in self.objects if obj["Key"] != item["Key"]]
        return {"Deleted": Delete["Objects"]}


def test_runner_dry_run_preserves_bucket_objects():
    fake = _FakeS3(_dataset())
    result = enforce_r2_retention(fake, "fake-bucket", dry_run=True, now=NOW)
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["would_delete_count"] >= 0
    assert fake.deleted == []


def test_runner_apply_then_stops_on_second_pass():
    fake = _FakeS3(_dataset())
    first = enforce_r2_retention(fake, "fake-bucket", dry_run=False, now=NOW)
    second = enforce_r2_retention(fake, "fake-bucket", dry_run=False, now=NOW)
    assert first["ok"] is True
    assert second["ok"] is True
    assert second["deleted"] == 0


def test_filename_parser_accepts_canonical_names_only():
    ts = _parse_filename_to_ts("backups/auto-90d/MASCI_complete_backup_2026-07-24_120000Z.zip")
    assert ts == datetime(2026, 7, 24, 12, 0, 0, tzinfo=timezone.utc)
    assert _parse_filename_to_ts("backups/legacy.zip") is None

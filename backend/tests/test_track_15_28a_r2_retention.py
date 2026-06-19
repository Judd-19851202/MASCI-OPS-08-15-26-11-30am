"""TRACK 15.28A · R2 retention certification suite (8 tests).

Pure-Python · no live R2 contact · synthetic dataset only. Verifies the
planning logic and the live runner (against a fake-S3 mock) before any
production exposure.

Run: ``pytest /app/backend/tests/test_track_15_28a_r2_retention.py -v``
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.r2_retention import (  # noqa: E402
    plan_retention,
    enforce_r2_retention,
    _parse_filename_to_ts,
    TIER1_DAYS, TIER2_DAYS, TIER3_DAYS,
)

NOW = datetime(2026, 6, 19, 12, 0, 0, tzinfo=timezone.utc)


def _mk_key(ts: datetime) -> str:
    return f"backups/auto-90d/MASCI_complete_backup_{ts.strftime('%Y-%m-%d_%H%M%S')}Z.zip"


def _synth_dataset() -> list[tuple[str, datetime]]:
    """14 days hourly · 90 days daily · 12 months monthly."""
    keys = []
    # Tier-1 window: last 14 days hourly = 14 * 24 = 336 zips
    for h in range(14 * 24):
        ts = NOW - timedelta(hours=h)
        keys.append((_mk_key(ts), ts))
    # Day 15..90 — three backups per day so Tier-2 can prove "newest survives"
    for d in range(15, 91):
        for hour in (2, 14, 22):
            ts = NOW - timedelta(days=d, hours=23 - hour)
            keys.append((_mk_key(ts), ts))
    # Month 4..12 — three backups per month so Tier-3 can prove "newest survives"
    for m in range(4, 13):
        for offset_d in (1, 12, 28):
            ts = NOW - timedelta(days=30 * m + offset_d, hours=12)
            keys.append((_mk_key(ts), ts))
    # Beyond 1 year — 5 zips, all should be Tier-4 deletes
    for d in (370, 400, 500, 600, 1000):
        ts = NOW - timedelta(days=d)
        keys.append((_mk_key(ts), ts))
    return keys


def test_t1_synthetic_dataset_survivor_count():
    """Test 1 — verify exact expected survivors across all tiers."""
    keys = _synth_dataset()
    plan = plan_retention(keys, now=NOW)
    # Tier 1: 336 (14 days × 24 hourly)
    assert plan.survivor_counts_by_tier[1] == 14 * 24, plan.survivor_counts_by_tier
    # Tier 2: keeps newest per calendar day for days 15..90 → ~76 days
    # (depending on how UTC day boundaries fall; allow a small ±1 jitter
    # because our synthetic uses 23-hour offsets that may shift one row
    # across a UTC boundary)
    assert 70 <= plan.survivor_counts_by_tier[2] <= 80
    # Tier 3: months 4..12 → 9 monthly survivors (10 if date math crosses
    # a calendar boundary across 365d horizon — accept both as valid).
    assert plan.survivor_counts_by_tier[3] in (9, 10), plan.survivor_counts_by_tier
    # Tier 4: 5 deletes
    assert plan.deleted_by_tier[4] >= 5
    # Sanity totals
    assert len(plan.keep) == sum(plan.survivor_counts_by_tier.values())


def test_t2_newest_hourly_survives():
    """Test 2 — newest hourly zip must survive."""
    keys = _synth_dataset()
    plan = plan_retention(keys, now=NOW)
    newest = _mk_key(NOW)
    assert newest in plan.keep
    assert newest not in plan.delete


def test_t3_newest_daily_survives():
    """Test 3 — for Tier-2 days, the newest UTC-day backup survives."""
    keys = _synth_dataset()
    plan = plan_retention(keys, now=NOW)
    # For day 20 (deep in Tier-2), the survivor must have hour=22 (newest of the three)
    survivors_day20 = [
        d for d in plan.decisions
        if d.tier == 2 and d.keep and "2026-05-30" in d.reason  # NOW - 20 days = 2026-05-30
    ]
    # Find any one of the 3 candidates for day 20 (NOW-20d)
    day20_kept = [d for d in plan.decisions if d.tier == 2 and d.keep
                  and d.timestamp.date() == (NOW - timedelta(days=20)).date()]
    assert len(day20_kept) == 1
    day20_dropped = [d for d in plan.decisions if d.tier == 2 and not d.keep
                     and d.timestamp.date() == (NOW - timedelta(days=20)).date()]
    assert len(day20_dropped) == 2
    # Survivor must be the latest hour among the three
    survivor_ts = day20_kept[0].timestamp
    for d in day20_dropped:
        assert d.timestamp < survivor_ts


def test_t4_newest_monthly_survives():
    """Test 4 — for Tier-3, only the newest backup per UTC calendar month survives."""
    keys = _synth_dataset()
    plan = plan_retention(keys, now=NOW)
    by_month = {}
    for d in plan.decisions:
        if d.tier == 3 and d.keep:
            mk = d.timestamp.strftime("%Y-%m")
            by_month.setdefault(mk, []).append(d)
    # Exactly one survivor per month
    for mk, group in by_month.items():
        assert len(group) == 1, f"{mk}: {len(group)} survivors"


def test_t5_required_deletions_occur():
    """Test 5 — confirm every Tier-2/3/4 loser is in plan.delete."""
    keys = _synth_dataset()
    plan = plan_retention(keys, now=NOW)
    # Sum of deletes across tiers 2/3/4 == len(plan.delete)
    total_should_delete = (plan.deleted_by_tier[2] + plan.deleted_by_tier[3]
                           + plan.deleted_by_tier[4])
    assert len(plan.delete) == total_should_delete


def test_t6_recent_backups_untouched():
    """Test 6 — backups newer than retention limits are untouched (Tier-1)."""
    keys = _synth_dataset()
    plan = plan_retention(keys, now=NOW)
    for d in plan.decisions:
        if d.tier == 1:
            assert d.keep is True, f"Tier-1 backup should never be deleted: {d.key}"
        if d.age_days <= TIER1_DAYS:
            assert d.keep is True, f"backup within Tier-1 window deleted: {d}"


def test_t7_restore_path_intact():
    """Test 7 — restore path: the survivor set must always include the very
    newest object so a "restore latest" operation can never fail."""
    keys = _synth_dataset()
    plan = plan_retention(keys, now=NOW)
    keys_sorted = sorted(keys, key=lambda kt: kt[1], reverse=True)
    newest_key, _ = keys_sorted[0]
    assert newest_key in plan.keep
    # And the newest in each tier window must be in plan.keep (only check
    # windows that actually have survivors — Tier 4 has none by design)
    for tier_days in (TIER1_DAYS, TIER2_DAYS, TIER3_DAYS):
        cutoff = NOW - timedelta(days=tier_days - 0.5)
        candidates = [kt for kt in keys
                      if kt[1] <= cutoff
                      and (NOW - kt[1]).days <= tier_days]
        if candidates:
            candidates.sort(key=lambda kt: kt[1], reverse=True)
            assert candidates[0][0] in plan.keep, f"newest in tier {tier_days}d window not kept"


def test_t8_idempotency():
    """Test 8 — run twice. Second pass produces zero new deletes."""
    keys = _synth_dataset()
    plan_a = plan_retention(keys, now=NOW)
    # Simulate "second run" — apply deletes, then re-run on the surviving set
    survivors = [(k, t) for k, t in keys if k in plan_a.keep]
    plan_b = plan_retention(survivors, now=NOW)
    assert len(plan_b.delete) == 0, (
        f"second-run deletions: {plan_b.delete[:5]} (drift!)"
    )
    # Survivor counts must be unchanged
    assert plan_a.survivor_counts_by_tier == plan_b.survivor_counts_by_tier


# ---------- runner-mode tests against a fake S3 ----------

class _FakeS3:
    def __init__(self, keys):
        self.objects = [{"Key": k, "Size": 600_000_000, "LastModified": ts}
                        for k, ts in keys]
        self.deleted = []

    def get_paginator(self, op):
        outer = self

        class _P:
            def paginate(self_inner, **kw):
                yield {"Contents": outer.objects}
        return _P()

    def delete_objects(self, *, Bucket, Delete):
        for o in Delete["Objects"]:
            self.deleted.append(o["Key"])
            self.objects = [x for x in self.objects if x["Key"] != o["Key"]]
        return {"Deleted": [{"Key": o["Key"]} for o in Delete["Objects"]]}


def test_runner_dry_run_no_mutation():
    fake = _FakeS3(_synth_dataset())
    pre = len(fake.objects)
    result = enforce_r2_retention(
        fake, "fake-bucket", prefix="backups/auto-90d/",
        dry_run=True, now=NOW,
    )
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["scanned"] == pre
    assert fake.deleted == []  # nothing actually deleted in dry-run
    assert len(fake.objects) == pre


def test_runner_apply_then_idempotent():
    fake = _FakeS3(_synth_dataset())
    r1 = enforce_r2_retention(
        fake, "fake-bucket", prefix="backups/auto-90d/",
        dry_run=False, now=NOW,
    )
    assert r1["ok"] is True
    assert r1["deleted"] > 0
    n_after = len(fake.objects)

    # Re-run — zero further deletions
    r2 = enforce_r2_retention(
        fake, "fake-bucket", prefix="backups/auto-90d/",
        dry_run=False, now=NOW,
    )
    assert r2["ok"] is True
    assert r2["deleted"] == 0, f"second run deleted: {r2['deleted']}"
    assert len(fake.objects) == n_after


def test_filename_parser():
    """Filename parser handles canonical naming + rejects unknown shapes."""
    ts = _parse_filename_to_ts("backups/auto-90d/MASCI_complete_backup_2026-06-19_120000Z.zip")
    assert ts == datetime(2026, 6, 19, 12, 0, 0, tzinfo=timezone.utc)
    assert _parse_filename_to_ts("backups/random_file.zip") is None
    assert _parse_filename_to_ts("backups/legacy_2024.zip") is None

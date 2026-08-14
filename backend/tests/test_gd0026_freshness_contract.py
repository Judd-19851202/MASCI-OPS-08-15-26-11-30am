"""GD-0026 — Canonical FRESHNESS/TIME state machine + failure injection (Wave 6).

Falsifiable: unknown/missing/malformed/future/failed timestamps must NEVER read as
CURRENT; threshold boundaries resolve deterministically; UTC vs naive handled.
"""
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.kpi_freshness import freshness_state, CURRENT, AGING, STALE, UNKNOWN, FUTURE, SCAN_FAILED

NOW = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
FRESH = 3600.0        # 1h
STALE_AFTER = 86400.0  # 24h


def _at(seconds_ago):
    return NOW - timedelta(seconds=seconds_ago)


def test_just_before_threshold_is_current():
    assert freshness_state(_at(FRESH - 1), fresh_within_s=FRESH, stale_after_s=STALE_AFTER, now=NOW) == CURRENT


def test_exact_fresh_threshold_is_current():
    assert freshness_state(_at(FRESH), fresh_within_s=FRESH, stale_after_s=STALE_AFTER, now=NOW) == CURRENT


def test_just_after_fresh_is_aging():
    assert freshness_state(_at(FRESH + 1), fresh_within_s=FRESH, stale_after_s=STALE_AFTER, now=NOW) == AGING


def test_after_stale_threshold_is_stale():
    assert freshness_state(_at(STALE_AFTER + 1), fresh_within_s=FRESH, stale_after_s=STALE_AFTER, now=NOW) == STALE


def test_missing_timestamp_is_unknown_never_current():
    for v in (None, ""):
        st = freshness_state(v, fresh_within_s=FRESH, stale_after_s=STALE_AFTER, now=NOW)
        assert st == UNKNOWN and st != CURRENT


def test_malformed_timestamp_is_unknown_never_current():
    st = freshness_state("not-a-date", fresh_within_s=FRESH, stale_after_s=STALE_AFTER, now=NOW)
    assert st == UNKNOWN and st != CURRENT


def test_future_timestamp_is_future_never_current():
    st = freshness_state(NOW + timedelta(hours=2), fresh_within_s=FRESH, stale_after_s=STALE_AFTER, now=NOW)
    assert st == FUTURE and st != CURRENT


def test_scan_failed_never_current_or_stale_only():
    st = freshness_state(_at(10), fresh_within_s=FRESH, stale_after_s=STALE_AFTER, now=NOW, scan_failed=True)
    assert st == SCAN_FAILED and st not in (CURRENT, STALE)


def test_naive_timestamp_treated_as_utc():
    naive = datetime(2026, 6, 15, 11, 30, 0)  # 30 min ago, no tz
    assert freshness_state(naive, fresh_within_s=FRESH, stale_after_s=STALE_AFTER, now=NOW) == CURRENT


def test_iso_z_string_parsed():
    assert freshness_state("2026-06-15T11:59:00Z", fresh_within_s=FRESH, stale_after_s=STALE_AFTER, now=NOW) == CURRENT


def test_small_clock_skew_tolerated_as_current():
    # 60s in the future is within tolerance -> not FUTURE, resolves CURRENT
    assert freshness_state(NOW + timedelta(seconds=60), fresh_within_s=FRESH, stale_after_s=STALE_AFTER, now=NOW) == CURRENT

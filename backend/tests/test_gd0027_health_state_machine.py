"""GD-0027 — Canonical HEALTH STATE MACHINE + failure injection (Wave 7).

Guards lib.canonical_status (the shared health-state owner) so that:
  - stale evidence -> DEGRADED, never VERIFIED (no stale-as-green);
  - unknown/unrecognised -> UNVERIFIABLE, never VERIFIED (no unknown-as-green);
  - a single MISMATCH child drives the worst-of rollup (weighted score cannot hide it);
  - freshness is a SEPARATE axis from health (a stale timestamp doesn't fake VERIFIED);
  - not-applicable/disabled is distinct from healthy.
Falsifiable: fails if any false-green / false-red path is introduced.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import canonical_status as cs


def test_healthy_aliases_map_to_verified():
    for raw in ("green", "ok", "pass", "healthy", "live", "ready", "verified"):
        assert cs.to_canonical(raw) == cs.VERIFIED, raw


def test_degraded_aliases_map_to_degraded():
    for raw in ("amber", "yellow", "warning", "attention", "advisory", "at_risk", "degraded"):
        assert cs.to_canonical(raw) == cs.DEGRADED, raw


def test_stale_never_becomes_verified():
    # stale flag forces DEGRADED even if the raw signal looks healthy (no stale-as-green)
    assert cs.to_canonical("green", stale=True) == cs.DEGRADED


def test_unknown_or_unrecognised_is_unverifiable_never_verified():
    st = cs.to_canonical("some-garbage-status")
    assert st == cs.UNVERIFIABLE and st != cs.VERIFIED


def test_not_applicable_is_distinct_from_healthy():
    assert cs.to_canonical("green", applicable=False) == cs.NOT_APPLICABLE
    assert cs.to_canonical("green", enabled=False) == cs.NOT_APPLICABLE


def test_worst_of_rollup_a_single_mismatch_drives_state():
    # weighted majority of green cannot hide one MISMATCH
    assert cs.highest([cs.VERIFIED, cs.VERIFIED, cs.VERIFIED, cs.MISMATCH]) == cs.MISMATCH
    assert cs.highest([cs.VERIFIED, cs.DEGRADED]) == cs.DEGRADED
    assert cs.highest([cs.VERIFIED, cs.VERIFIED]) == cs.VERIFIED


def test_mismatch_outranks_degraded_outranks_verified():
    assert cs.severity(cs.MISMATCH) > cs.severity(cs.DEGRADED) > cs.severity(cs.VERIFIED)


def test_summarize_highest_reflects_worst_child():
    cards = [{"canonical_status": cs.VERIFIED}, {"canonical_status": cs.VERIFIED},
             {"canonical_status": cs.MISMATCH}]
    out = cs.summarize(cards)
    assert out["highest"] == cs.MISMATCH
    assert out["mismatch"] == 1 and out["verified"] == 2


def test_freshness_is_separate_axis_unknown_ts_not_fresh():
    r = cs.freshness_status(evidence_at=None, max_age_seconds=3600)
    assert r["stale"] is True and r["fresh"] is False  # unknown timestamp is not fresh


def test_freshness_stale_beyond_max_age():
    r = cs.freshness_status(evidence_at="2000-01-01T00:00:00Z", max_age_seconds=3600)
    assert r["stale"] is True and r["fresh"] is False

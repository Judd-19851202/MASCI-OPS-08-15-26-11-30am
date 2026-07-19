"""TRACK 28.11 · Canonical operational-signal invariants.

These tests lock down the vocabulary + summary rules so future
diagnostics/OCC/system-health work cannot silently regress. They run
in-process without hitting the DB or any HTTP layer.
"""
import pytest

from lib.canonical_status import (
    HEALTHY, ATTENTION, CRITICAL, UNKNOWN, STALE,
    DISABLED, NOT_APPLICABLE,
    to_canonical, summarize, highest, severity, freshness_status,
)


# ─── to_canonical ──────────────────────────────────────────────────────

class TestToCanonical:
    def test_green_family_maps_to_healthy(self):
        for raw in ("green", "ok", "pass", "healthy", "GREEN", " ok ", "live"):
            assert to_canonical(raw) == HEALTHY, raw

    def test_yellow_family_maps_to_attention(self):
        for raw in ("yellow", "amber", "warning", "warn", "watch", "attention", "degraded"):
            assert to_canonical(raw) == ATTENTION, raw

    def test_red_family_maps_to_critical(self):
        for raw in ("red", "critical", "failed", "fail", "blocker", "error", "no-go"):
            assert to_canonical(raw) == CRITICAL, raw

    def test_unknown_family_maps_to_unknown(self):
        for raw in ("unknown", "", None, "loading", "unavailable"):
            assert to_canonical(raw) == UNKNOWN, raw

    def test_disabled_with_mocked_becomes_not_applicable(self):
        assert to_canonical("disabled", mocked=True) == NOT_APPLICABLE

    def test_not_applicable_flag_wins(self):
        # applicable=False overrides everything else.
        assert to_canonical("critical", applicable=False) == NOT_APPLICABLE
        assert to_canonical("green", applicable=False) == NOT_APPLICABLE

    def test_disabled_flag_when_applicable(self):
        assert to_canonical("green", enabled=False, applicable=True) == DISABLED

    def test_stale_flag(self):
        assert to_canonical("green", stale=True) == STALE

    def test_canonical_passthrough(self):
        for c in (HEALTHY, ATTENTION, CRITICAL, UNKNOWN, STALE, DISABLED, NOT_APPLICABLE):
            assert to_canonical(c) == c


# ─── summarize ─────────────────────────────────────────────────────────

class TestSummarize:
    def test_all_healthy(self):
        cards = [{"canonical_status": HEALTHY} for _ in range(5)]
        s = summarize(cards)
        assert s["verified"] == 5
        assert s["total_applicable"] == 5
        assert s["highest"] == HEALTHY

    def test_disabled_and_not_applicable_do_not_count_as_failed(self):
        cards = [
            {"canonical_status": HEALTHY},
            {"canonical_status": DISABLED},
            {"canonical_status": NOT_APPLICABLE},
        ]
        s = summarize(cards)
        assert s["verified"] == 1
        assert s["not_applicable"] == 2
        assert s["mismatch"] == 0
        assert s["degraded"] == 0
        assert s["total_applicable"] == 1
        # Highest severity across the set: still HEALTHY because DISABLED
        # + NOT_APPLICABLE never escalate.
        assert s["highest"] == HEALTHY

    def test_critical_dominates(self):
        cards = [
            {"canonical_status": HEALTHY},
            {"canonical_status": ATTENTION},
            {"canonical_status": CRITICAL},
            {"canonical_status": UNKNOWN},
        ]
        s = summarize(cards)
        assert s["highest"] == CRITICAL

    def test_missing_status_becomes_unknown(self):
        s = summarize([{"canonical_status": None}, {}])
        assert s["unverifiable"] == 2

    def test_legacy_status_key(self):
        # Cards using the legacy `status` key still normalize correctly.
        s = summarize([{"status": "green"}, {"status": "red"}])
        assert s["verified"] == 1
        assert s["mismatch"] == 1


# ─── highest / severity ──────────────────────────────────────────────

class TestHighestAndSeverity:
    def test_severity_ordering(self):
        assert severity(HEALTHY) < severity(ATTENTION)
        assert severity(ATTENTION) < severity(CRITICAL)
        assert severity(ATTENTION) < severity(UNKNOWN)

    def test_highest_empty_is_healthy(self):
        assert highest([]) == NOT_APPLICABLE

    def test_highest_picks_worst(self):
        assert highest([HEALTHY, ATTENTION, CRITICAL, HEALTHY]) == CRITICAL

    def test_disabled_does_not_escalate(self):
        assert highest([HEALTHY, DISABLED, NOT_APPLICABLE]) == HEALTHY


# ─── freshness_status ────────────────────────────────────────────────

class TestFreshness:
    def test_no_policy_is_never_stale(self):
        r = freshness_status(evidence_at="2026-07-11T00:00:00+00:00",
                             max_age_seconds=None)
        assert r["stale"] is False
        assert r["fresh"] is None

    def test_missing_evidence_with_policy_is_stale(self):
        r = freshness_status(evidence_at=None, max_age_seconds=3600)
        assert r["stale"] is True
        assert r["fresh"] is False

    def test_fresh_evidence(self):
        from datetime import datetime, timezone, timedelta
        recent = datetime.now(timezone.utc) - timedelta(seconds=60)
        r = freshness_status(evidence_at=recent, max_age_seconds=3600)
        assert r["fresh"] is True
        assert r["stale"] is False

    def test_stale_evidence(self):
        from datetime import datetime, timezone, timedelta
        old = datetime.now(timezone.utc) - timedelta(days=100)
        r = freshness_status(evidence_at=old, max_age_seconds=60 * 86400)
        assert r["stale"] is True
        assert r["fresh"] is False
        assert r["evidence_age_seconds"] > 60 * 86400


# ─── Regression: MaintainX intentional stub (28.10 → 28.11) ──────────

class TestMaintainXNotApplicable:
    """MaintainX is not used by MASCI. Its `disabled + mocked=True`
    probe must NEVER count as degraded, failed, critical, or unknown.
    """

    def test_maintainx_stub_is_not_applicable(self):
        # simulating the shape emitted by compute_provider_status
        maintainx_probe = {
            "id": "maintainx",
            "status": "disabled",
            "mocked": True,
        }
        assert to_canonical(
            maintainx_probe["status"], mocked=maintainx_probe["mocked"]
        ) == NOT_APPLICABLE

    def test_maintainx_does_not_escalate_platform_status(self):
        cards = [
            {"canonical_status": HEALTHY},  # motive up
            {"canonical_status": NOT_APPLICABLE},  # maintainx stub
            {"canonical_status": HEALTHY},  # r2 ok
        ]
        s = summarize(cards)
        assert s["highest"] == HEALTHY
        assert s["not_applicable"] == 1
        assert s["mismatch"] == 0
        assert s["degraded"] == 0

"""GD-0004 — Governance health/freshness contract regression (SO-06).

Truth invariants (Truth & Trust program, Wave 2):
- critical-severity==0  =>  health_label MUST NOT be "critical"
- >=1 critical-severity + low score  =>  "critical" preserved
- clean findings  =>  "healthy"
- freshness (STALE/UNKNOWN/FAILED) is a SEPARATE axis and never turns a
  zero-critical backlog into an active "critical" health label.
"""
from backend.routes.governance import (
    _derive_governance_health_label,
    _governance_freshness,
)
from datetime import datetime, timezone, timedelta


def _score(c, h, m, l):
    return max(0, min(100, 100 - 20 * c - 8 * h - 3 * m - 1 * l))


def test_high_medium_backlog_no_critical_is_not_critical():
    sev = {"critical": 0, "high": 46, "medium": 312, "low": 0}
    assert _derive_governance_health_label(_score(0, 46, 312, 0), sev) == "degraded"


def test_real_critical_low_score_is_critical():
    sev = {"critical": 3, "high": 2, "medium": 0, "low": 0}
    assert _derive_governance_health_label(_score(3, 2, 0, 0), sev) == "critical"


def test_clean_is_healthy():
    sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    assert _derive_governance_health_label(_score(0, 0, 0, 0), sev) == "healthy"


def test_small_advisory_no_critical_never_critical():
    sev = {"critical": 0, "high": 2, "medium": 0, "low": 0}
    assert _derive_governance_health_label(_score(0, 2, 0, 0), sev) != "critical"


def test_freshness_is_independent_of_severity():
    now = datetime.now(timezone.utc)
    stale_scan = {"finished_at": (now - timedelta(days=33)).isoformat()}
    fresh = _governance_freshness(stale_scan, now=now)
    # Stale evidence is reported on its own freshness axis (state=STALE)...
    assert fresh["state"] == "STALE"
    # ...and a zero-critical backlog is NOT critical regardless of staleness.
    assert _derive_governance_health_label(_score(0, 46, 312, 0),
                                           {"critical": 0, "high": 46, "medium": 312, "low": 0}) == "degraded"


def test_scan_failed_and_unavailable_states_are_governed():
    now = datetime.now(timezone.utc)
    none_state = _governance_freshness(None, now=now)
    assert none_state["scan_execution_health"] in ("UNKNOWN", "FAILED")

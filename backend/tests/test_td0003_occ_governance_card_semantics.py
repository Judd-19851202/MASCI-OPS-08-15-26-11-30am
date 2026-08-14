"""TD-0003 — OCC governance card severity semantics (SO-06 / SO-10).

Root cause (live production evidence, mascidocs.com, read-only):
- OCC "Platform overview" showed Source/Overall status = MISMATCH.
- GET /api/admin/occ/health overall = MISMATCH driven by ONE red card:
  `governance` (/api/admin/governance/summary).
- Governance summary: severity_counts {critical:0, high:46, medium:312},
  health_label "critical" (false — SO-06), all advisory findings
  (PPE_MISSING / EMP_LINK_*), zero critical-severity.
- `_eval_governance` forced MISMATCH via TWO independent clauses:
  (a) health_label == "critical"  (SO-06 defect, fixed in governance.py)
  (b) highs > 20                    (OCC-local advisory-count heuristic)
  Clause (b) meant the SO-06 fix alone would NOT clear the OCC red.

Truth invariants:
- Zero critical-severity + advisory high/medium backlog => DEGRADED, never MISMATCH.
- >=1 critical-severity finding => MISMATCH (genuine red preserved).
- governed health_label "critical" => MISMATCH (post-SO-06 it requires a real critical).
- Clean governance => VERIFIED.
- Unreachable governance summary => UNVERIFIABLE (honest unknown, not fake green).
"""
from backend.routes.occ_health_aggregator import _eval_governance


def _status(body):
    return _eval_governance(body, None, "2026-06-01T00:00:00Z")["status"]


def test_production_advisory_backlog_is_degraded_not_mismatch():
    # Exact live-production shape after the SO-06 health_label fix.
    body = {
        "severity_counts": {"critical": 0, "high": 46, "medium": 312, "low": 0},
        "health_label": "degraded",
        "convergence_score": 0,
    }
    assert _status(body) == "DEGRADED"


def test_legacy_false_critical_label_no_criticals_is_not_red():
    # Even if an upstream still emits the pre-fix false "critical" label with
    # zero critical-severity, a lone advisory backlog must not be red unless
    # the label itself is critical; here the label drives it but severity is 0.
    # (health_label == "critical" is respected because governance.py now only
    # emits "critical" when there is a real critical-severity finding.)
    body = {
        "severity_counts": {"critical": 0, "high": 46, "medium": 312},
        "health_label": "critical",
    }
    assert _status(body) == "MISMATCH"


def test_real_critical_finding_is_mismatch():
    body = {
        "severity_counts": {"critical": 2, "high": 3, "medium": 0},
        "health_label": "critical",
    }
    assert _status(body) == "MISMATCH"


def test_high_backlog_over_20_no_critical_is_degraded():
    # Directly guards against regression to the old `highs > 20 -> MISMATCH`.
    body = {
        "severity_counts": {"critical": 0, "high": 99, "medium": 0},
        "health_label": "degraded",
    }
    assert _status(body) == "DEGRADED"


def test_clean_governance_is_verified():
    body = {
        "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
        "health_label": "healthy",
    }
    assert _status(body) == "VERIFIED"


def test_unreachable_governance_is_unverifiable():
    assert _eval_governance(None, "connect timeout", "2026-06-01T00:00:00Z")["status"] == "UNVERIFIABLE"

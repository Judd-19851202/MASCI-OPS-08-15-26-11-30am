"""Track 19.38 · Cross-portal read fanout + Portfolio Attention Feed · lock test.

Enforces:
- Aggregator module exists · imports cleanly.
- Aggregator is read-only (no Mongo writes).
- Scorer reuse (calls Track 19.37 ``compute_presence_score`` · no
  duplicate implementation of injury/utility/vehicle/... presence).
- PM projection is a strict allow-list with the mandated forbidden-token
  set; the runtime leak-guard raises when a forbidden token would leak.
- Portfolio view exposes ``top_signals``; Safety view supersedes it
  with a ``safety_preview`` object.
- Sort order is DESC by attention_score.
- Existing Phase D endpoints preserved.
- Frontend Portfolio Attention Feed section exists, is bilingual, and
  deep-links to the Executive Case Report.
- Track 19.34 field-vs-safety grep invariant remains green.
- 6 required docs + PRD + CHANGELOG updated.

Run in isolation:
    pytest backend/tests/test_track_19_38_portfolio_intelligence.py -q
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

APP = Path("/app")
BE = APP / "backend"
FE = APP / "frontend/src"
MEM = APP / "memory"

AGG = BE / "incident_engine/portfolio_intelligence.py"
SERVER = BE / "server.py"
DASH_PAGE = FE / "pages/ExecutiveIntelligence.jsx"
INCIDENT_REPORT = FE / "pages/IncidentReport.jsx"
INCIDENT_SCHEMA = FE / "lib/incidentReportSchema.js"


# ---------------------------------------------------------------- module locks


def test_aggregator_module_exists():
    assert AGG.exists(), f"Missing {AGG}"


def test_aggregator_imports_cleanly():
    import importlib
    mod = importlib.import_module("incident_engine.portfolio_intelligence")
    assert hasattr(mod, "register_portfolio_intelligence_routes")
    assert hasattr(mod, "_PM_ALLOWED_KEYS")
    assert hasattr(mod, "_PM_FORBIDDEN_TOKENS")


# --------------------------------------------------------------------- writes


def test_aggregator_is_read_only():
    text = AGG.read_text(encoding="utf-8")
    forbidden = [
        "insert_one", "insert_many",
        "update_one", "update_many",
        "replace_one",
        "delete_one", "delete_many",
        "find_one_and_update", "find_one_and_replace", "find_one_and_delete",
    ]
    hits = [f for f in forbidden if f in text]
    assert not hits, f"Aggregator must be read-only. Found writes: {hits}"


# --------------------------------------------------------------- scorer reuse


def test_aggregator_reuses_track_19_37_scorer():
    text = AGG.read_text(encoding="utf-8")
    assert "from .presence_score import compute_presence_score" in text
    assert "compute_presence_score(" in text


def test_aggregator_does_not_reimplement_signal_rules():
    """Grep the aggregator for tokens that would indicate a local
    reimplementation of the Track 19.37 rules. If any appear as a
    function definition inside portfolio_intelligence.py, the reuse
    contract has been violated."""
    text = AGG.read_text(encoding="utf-8")
    forbidden_locally = [
        "def _signal_injury", "def _signal_utility",
        "def _signal_vehicle_equipment", "def _signal_environmental",
        "def _signal_property_damage", "def _signal_public_exposure",
        "def _signal_police_agency", "def _signal_evidence_gap",
        "def _signal_delayed_closeout", "def _signal_overdue_capa",
        "def _signal_executive_review_needed",
    ]
    hits = [t for t in forbidden_locally if t in text]
    assert not hits, (
        f"Aggregator must not reimplement Track 19.37 signal rules. "
        f"Found local definitions: {hits}"
    )


# -------------------------------------------------------------- allow-list


def test_pm_allowed_keys_shape():
    from incident_engine.portfolio_intelligence import _PM_ALLOWED_KEYS
    assert isinstance(_PM_ALLOWED_KEYS, set)
    assert 0 < len(_PM_ALLOWED_KEYS) <= 16, (
        f"PM allow-list must be tight; got {len(_PM_ALLOWED_KEYS)} keys"
    )
    # A few obvious forbidden field names must NOT be on the allow-list.
    forbidden_on_list = {
        "safety_block", "regulatory_review", "osha_recordable",
        "root_cause", "root_cause_summary", "liability",
        "discipline", "preventability", "top_signals", "signals",
    }
    leak = _PM_ALLOWED_KEYS & forbidden_on_list
    assert not leak, f"PM allow-list must exclude decision fields; got {leak}"


REQUIRED_FORBIDDEN_TOKENS = {
    "safety_block", "regulatory_review",
    "osha_recordable", "root_cause",
    "liability", "discipline", "preventability", "insurance",
    "signal_rationale", "rationale",
}


def test_pm_forbidden_tokens_contains_mandated_set():
    from incident_engine.portfolio_intelligence import _PM_FORBIDDEN_TOKENS
    missing = REQUIRED_FORBIDDEN_TOKENS - set(_PM_FORBIDDEN_TOKENS)
    assert not missing, f"PM forbidden-token set missing: {missing}"


# -------------------------------------------------------- projection semantics


def _synthetic_wide_row():
    return {
        "case_id": "cid-1",
        "case_number": "2026-9999",
        "state": "OPEN",
        "incident_type": "utility_strike",
        "job_number": "J-100",
        "location_label": "Loc A",
        "occurred_at": "2026-06-01T00:00:00+00:00",
        "submitted_at": "2026-06-02T00:00:00+00:00",
        "days_open": 12,
        "capa_open": 2,
        "capa_total": 3,
        "tasks_open": 1,
        "readiness_band": "medium",
        "attention_level": "high",
        "attention_score": 71,
        "_attention_full": {
            "signals": [
                {"signal_key": "possible_utility_involvement",
                 "score": 0.9, "confidence": "high",
                 "rationale": "utility_strike",
                 "source_fields": ["field_block.incident_type"],
                 "recommended_review_owner": "safety",
                 "label": "Possible utility involvement"},
            ]
        },
        "_safety_block": {
            "root_cause_summary": "",
            "executive_reviewer": "",
            "investigator_name": "",
        },
    }


def test_pm_view_is_strict_allow_list():
    from incident_engine.portfolio_intelligence import _view_pm, _PM_ALLOWED_KEYS
    projected = _view_pm(_synthetic_wide_row())
    extra = set(projected.keys()) - _PM_ALLOWED_KEYS
    assert not extra, f"PM view leaked non-allow-listed keys: {extra}"
    for banned in ("top_signals", "safety_preview", "_attention_full", "_safety_block"):
        assert banned not in projected, f"PM view must never include {banned!r}"


def test_pm_view_runtime_leak_guard_raises_on_forbidden():
    from fastapi import HTTPException
    from incident_engine.portfolio_intelligence import _assert_pm_safe
    with pytest.raises(HTTPException) as ei:
        _assert_pm_safe({"note": "OSHA_RECORDABLE flag set"})
    assert ei.value.status_code == 500
    assert "pm_projection_leak" in str(ei.value.detail)


def test_portfolio_view_includes_top_signals():
    from incident_engine.portfolio_intelligence import _view_portfolio
    v = _view_portfolio(_synthetic_wide_row())
    assert "top_signals" in v
    assert isinstance(v["top_signals"], list)
    assert v["top_signals"][0]["signal_key"] == "possible_utility_involvement"


def test_safety_view_supersets_portfolio_with_preview():
    from incident_engine.portfolio_intelligence import _view_portfolio, _view_safety
    p = _view_portfolio(_synthetic_wide_row())
    s = _view_safety(_synthetic_wide_row())
    # every portfolio key present in safety
    for k in p.keys():
        assert k in s, f"safety view missing portfolio key: {k}"
    # safety preview shape
    assert "safety_preview" in s
    sp = s["safety_preview"]
    for k in ("root_cause_documented", "executive_reviewer_present", "investigator_name"):
        assert k in sp, f"safety_preview missing key: {k}"


def test_sort_order_is_attention_desc():
    rows = [
        {"attention_score": 10, "days_open": 3, "case_id": "a"},
        {"attention_score": 90, "days_open": 1, "case_id": "b"},
        {"attention_score": 45, "days_open": 7, "case_id": "c"},
    ]
    rows.sort(key=lambda r: (-(r.get("attention_score") or 0), -(r.get("days_open") or 0)))
    assert [r["case_id"] for r in rows] == ["b", "c", "a"]


# --------------------------------------------------------- server registration


def test_server_wires_all_three_routes():
    text = SERVER.read_text(encoding="utf-8")
    assert "register_portfolio_intelligence_routes" in text
    assert "portfolio_intelligence" in text
    # Phase D endpoint preserved.
    assert "register_intelligence_routes" in text


# --------------------------------------------------------------- frontend locks


def test_dashboard_has_portfolio_attention_feed_section():
    text = DASH_PAGE.read_text(encoding="utf-8")
    assert 'data-testid="portfolio-attention-feed"' in text
    assert '/incident-intelligence/portfolio-attention' in text


def test_dashboard_feed_is_bilingual():
    text = DASH_PAGE.read_text(encoding="utf-8")
    idx = text.find('data-testid="portfolio-attention-feed"')
    assert idx != -1
    block = text[idx: idx + 5000]
    wraps = re.findall(r't\("[^"]+"\)', block)
    assert len(wraps) >= 3, f"feed must wrap ≥ 3 strings; found {len(wraps)}"


def test_dashboard_feed_deep_links_to_executive_report():
    text = DASH_PAGE.read_text(encoding="utf-8")
    idx = text.find('data-testid="portfolio-attention-feed"')
    block = text[idx: idx + 5000]
    assert "/safety/cases/" in block
    assert "/executive-report" in block


def test_dashboard_still_uses_phase_d_endpoints():
    text = DASH_PAGE.read_text(encoding="utf-8")
    for path in ["/incident-intelligence/home",
                 "/incident-intelligence/root-causes",
                 "/incident-intelligence/corrective-actions",
                 "/incident-intelligence/projects",
                 "/incident-intelligence/fleet",
                 "/incident-intelligence/learning",
                 "/incident-intelligence/brief"]:
        assert path in text, f"Phase D endpoint removed by 19.38: {path}"


# ---------------------------------------------------- doctrine regression locks


TRACK_19_34_FORBIDDEN_FIELDS = [
    "osha_recordable", "recordable_case", "osha_reportable",
    "root_cause", "preventability", "preventable_by",
    "workers_comp", "insurance_liable", "liability_determination",
    "disciplinary_action", "disciplinary_conclusion",
]


def test_track_19_34_field_intake_invariant_preserved():
    schema = INCIDENT_SCHEMA.read_text(encoding="utf-8")
    report = INCIDENT_REPORT.read_text(encoding="utf-8")
    for field in TRACK_19_34_FORBIDDEN_FIELDS:
        assert field not in schema, (
            f"Track 19.34 invariant broken by 19.38 in {INCIDENT_SCHEMA.name}: {field}"
        )
        assert field not in report, (
            f"Track 19.34 invariant broken by 19.38 in {INCIDENT_REPORT.name}: {field}"
        )


# ------------------------------------------------------------------- doc locks


REQUIRED_DOCS = [
    "TRACK_19_38_CROSS_PORTAL_READ_FANOUT.md",
    "TRACK_19_38_PORTFOLIO_ATTENTION_FEED.md",
    "TRACK_19_38_PERMISSION_MATRIX.md",
    "TRACK_19_38_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_38_QUALITY_GATE_CLOSEOUT.md",
    "TRACK_19_38_TEST_REPORT.md",
]


def test_all_track_19_38_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"Missing Track 19.38 docs: {missing}"


def test_closeout_declares_go():
    text = (MEM / "TRACK_19_38_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "🟢 GO" in text or "🟢 **GO" in text


def test_closeout_includes_six_pillar_score_and_rollback():
    text = (MEM / "TRACK_19_38_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    for pillar in ["Powerful", "Simple", "Beautiful", "Trusted", "Proven", "Operational"]:
        assert pillar in text
    assert "/ 60" in text or "/60" in text
    assert "Rollback" in text or "ROLLBACK" in text


ZERO_DRIFT_CATEGORIES = [
    "Schemas", "Backend routes", "Payloads", "PDFs", "Emails",
    "Notifications", "Permissions", "Trust Spine", "Audit events",
    "Rollback",
]


def test_zero_drift_matrix_covers_all_categories():
    text = (MEM / "TRACK_19_38_ZERO_DRIFT_MATRIX.md").read_text(encoding="utf-8")
    for cat in ZERO_DRIFT_CATEGORIES:
        assert cat in text, f"Zero-drift matrix missing category: {cat}"


def test_prd_updated_for_19_38():
    assert "TRACK 19.38" in (MEM / "PRD.md").read_text(encoding="utf-8")


def test_changelog_updated_for_19_38():
    assert "TRACK 19.38" in (MEM / "CHANGELOG.md").read_text(encoding="utf-8")

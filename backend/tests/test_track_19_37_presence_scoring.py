"""Track 19.37 · Passive Incident-Presence Scoring · lock test.

Enforces:
- Scorer + routes modules exist and import cleanly.
- Scorer is read-only (grep · no writes).
- Executive Intelligence model version bumped additively.
- Model exposes ``attention_signals`` with full shape.
- All 20 pre-19.37 Track 19.36 keys preserved.
- 11 signals with required per-signal shape.
- Deterministic (same inputs → same outputs).
- No-auto-decision notice present and correctly worded.
- Forbidden vocabulary absent from the signal payload (excluding the notice).
- Frontend panel present, uses neutral wording, bilingual.
- Track 19.34 field-vs-safety grep invariant preserved.
- 7 required docs + PRD + CHANGELOG updated.

Run in isolation:
    pytest backend/tests/test_track_19_37_presence_scoring.py -q
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any, Dict

import pytest

APP = Path("/app")
BE = APP / "backend"
FE = APP / "frontend/src"
MEM = APP / "memory"

SCORER = BE / "incident_engine/presence_score.py"
ROUTES = BE / "incident_engine/presence_score_routes.py"
ASSEMBLER = BE / "incident_engine/executive_intelligence.py"
SERVER = BE / "server.py"
REPORT_PAGE = FE / "pages/ExecutiveCaseReport.jsx"
INCIDENT_REPORT = FE / "pages/IncidentReport.jsx"
INCIDENT_SCHEMA = FE / "lib/incidentReportSchema.js"


REQUIRED_SIGNAL_KEYS = {
    "possible_injury_presence",
    "possible_utility_involvement",
    "possible_vehicle_equipment_involvement",
    "possible_environmental_involvement",
    "possible_property_damage",
    "possible_public_exposure",
    "possible_police_agency_involvement",
    "possible_open_evidence_gap",
    "possible_delayed_closeout",
    "possible_overdue_capa",
    "possible_executive_review_needed",
}

REQUIRED_TOP_KEYS_PRESENCE = {
    "case_id", "model_version", "generated_at",
    "overall_attention_score", "attention_level",
    "signals", "missing_inputs", "no_auto_decision_notice",
}

REQUIRED_SIGNAL_SHAPE = {
    "signal_key", "label", "score", "confidence", "rationale",
    "source_fields", "recommended_review_owner",
}

# Vocabulary the platform explicitly does NOT decide. These words must not
# appear anywhere in the signal payload EXCEPT inside the
# ``no_auto_decision_notice`` field, which is required to name them.
FORBIDDEN_DECISION_VOCAB = [
    "osha_recordable",
    "liability", "liable",
    "discipline", "disciplinary",
    "fault", "blame", "at_fault",
    "preventability",
    "root_cause_conclusion",
]

TRACK_19_36_TOP_KEYS = {
    "model_version", "generated_at",
    "case_ref", "executive_summary", "why_it_matters",
    "timeline", "evidence_chain",
    "people", "asset_buckets",
    "medical", "agency", "communications",
    "corrective_actions", "outstanding_tasks",
    "regulatory_review", "readiness", "decision_records",
    "operational_intelligence", "sources", "missing_fields",
}


# ------------------------------------------------------------------- fixtures


@pytest.fixture(scope="module")
def live_model() -> Dict[str, Any]:
    """Assemble Executive Intelligence Model against the live DB."""
    from motor.motor_asyncio import AsyncIOMotorClient
    from incident_engine.executive_intelligence import (
        assemble_executive_intelligence,
    )
    env = (BE / ".env").read_text(encoding="utf-8")
    mongo = ""
    dbname = ""
    for line in env.splitlines():
        if line.startswith("MONGO_URL="):
            mongo = line.split("=", 1)[1].strip().strip('"').strip("'")
        if line.startswith("DB_NAME="):
            dbname = line.split("=", 1)[1].strip().strip('"').strip("'")

    async def _load():
        client = AsyncIOMotorClient(mongo)
        db = client[dbname]
        c = await db.incident_cases.find_one({}, {"_id": 0, "id": 1})
        if not c:
            return None
        return await assemble_executive_intelligence(db, case_id=c["id"])

    return asyncio.run(_load())


# --------------------------------------------------------------- module locks


def test_scorer_module_exists():
    assert SCORER.exists(), f"Missing {SCORER}"


def test_routes_module_exists():
    assert ROUTES.exists(), f"Missing {ROUTES}"


def test_scorer_imports_cleanly():
    import importlib
    mod = importlib.import_module("incident_engine.presence_score")
    assert hasattr(mod, "compute_presence_score")
    assert hasattr(mod, "PRESENCE_SCORE_MODEL_VERSION")
    assert hasattr(mod, "NO_AUTO_DECISION_NOTICE")


def test_routes_imports_cleanly():
    import importlib
    mod = importlib.import_module("incident_engine.presence_score_routes")
    assert hasattr(mod, "register_presence_score_routes")


# ---------------------------------------------------------------- read-only


def test_scorer_is_read_only():
    text = SCORER.read_text(encoding="utf-8")
    forbidden = [
        "insert_one", "insert_many",
        "update_one", "update_many",
        "replace_one",
        "delete_one", "delete_many",
        "find_one_and_update", "find_one_and_replace", "find_one_and_delete",
    ]
    hits = [f for f in forbidden if f in text]
    assert not hits, f"Scorer must be read-only. Found writes: {hits}"


# ---------------------------------------------------------- route registration


def test_server_wires_presence_score_route():
    text = SERVER.read_text(encoding="utf-8")
    assert "register_presence_score_routes" in text
    assert "presence_score_routes" in text


# --------------------------------------------------------- model bump lock


def test_executive_model_bumped_to_at_least_1_1_0():
    from incident_engine.executive_intelligence import (
        EXECUTIVE_INTELLIGENCE_MODEL_VERSION,
    )
    parts = EXECUTIVE_INTELLIGENCE_MODEL_VERSION.split(".")
    assert len(parts) == 3
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    assert major == 1, "Breaking major bump not permitted"
    assert (major, minor, patch) >= (1, 1, 0), (
        f"Model must be ≥ 1.1.0 after Track 19.37; got "
        f"{EXECUTIVE_INTELLIGENCE_MODEL_VERSION}"
    )


def test_executive_model_all_pre_19_37_keys_preserved(live_model):
    if live_model is None:
        pytest.skip("No cases in live DB")
    missing = TRACK_19_36_TOP_KEYS - set(live_model.keys())
    assert not missing, f"Track 19.36 model keys removed by 19.37: {missing}"


def test_executive_model_contains_attention_signals(live_model):
    if live_model is None:
        pytest.skip("No cases in live DB")
    assert "attention_signals" in live_model


# ----------------------------------------------------- presence-score shape


def test_presence_score_top_shape(live_model):
    if live_model is None:
        pytest.skip("No cases in live DB")
    a = live_model["attention_signals"]
    missing = REQUIRED_TOP_KEYS_PRESENCE - set(a.keys())
    assert not missing, f"presence score missing top keys: {missing}"
    assert isinstance(a["signals"], list)
    assert isinstance(a["missing_inputs"], list)


def test_presence_score_attention_level_enum(live_model):
    if live_model is None:
        pytest.skip("No cases in live DB")
    a = live_model["attention_signals"]
    assert a["attention_level"] in ("low", "medium", "high")


def test_presence_score_overall_score_range(live_model):
    if live_model is None:
        pytest.skip("No cases in live DB")
    a = live_model["attention_signals"]
    v = a["overall_attention_score"]
    assert isinstance(v, int)
    assert 0 <= v <= 100


def test_presence_score_signal_set(live_model):
    if live_model is None:
        pytest.skip("No cases in live DB")
    a = live_model["attention_signals"]
    keys = {s["signal_key"] for s in a["signals"]}
    missing = REQUIRED_SIGNAL_KEYS - keys
    extra = keys - REQUIRED_SIGNAL_KEYS
    assert not missing, f"missing signal keys: {missing}"
    assert not extra, f"unexpected signal keys: {extra}"


def test_every_signal_has_full_shape(live_model):
    if live_model is None:
        pytest.skip("No cases in live DB")
    a = live_model["attention_signals"]
    for s in a["signals"]:
        gaps = REQUIRED_SIGNAL_SHAPE - set(s.keys())
        assert not gaps, f"signal {s.get('signal_key')} missing keys: {gaps}"
        assert isinstance(s["score"], (int, float))
        assert 0.0 <= float(s["score"]) <= 1.0
        assert s["confidence"] in ("low", "medium", "high")
        assert s["recommended_review_owner"] in ("safety", "executive", "pm")
        assert isinstance(s["source_fields"], list)
        assert isinstance(s["rationale"], str) and s["rationale"].strip()


def test_no_auto_decision_notice_wording(live_model):
    if live_model is None:
        pytest.skip("No cases in live DB")
    notice = (live_model["attention_signals"]["no_auto_decision_notice"] or "").lower()
    assert "attention signal only" in notice
    assert "safety owns investigation" in notice
    # Notice IS allowed to name what the platform does NOT decide.
    for tok in ["osha", "root cause", "liability", "fault", "discipline"]:
        assert tok in notice, f"notice must name '{tok}' as a domain the platform does NOT decide"


def test_signals_free_of_forbidden_decision_vocabulary(live_model):
    """Forbidden vocab must not appear in signal_key/label/rationale/
    source_fields/recommended_review_owner. The notice is exempt."""
    if live_model is None:
        pytest.skip("No cases in live DB")
    signals_dump = str(live_model["attention_signals"]["signals"]).lower()
    hits = [t for t in FORBIDDEN_DECISION_VOCAB if t in signals_dump]
    assert not hits, f"forbidden decision vocabulary leaked into signals: {hits}"


def test_scorer_is_deterministic():
    """Same inputs → same outputs (except generated_at, which is time-based)."""
    from incident_engine.presence_score import compute_presence_score
    case = {
        "id": "det-fixture-1",
        "state": "OPEN",
        "submitted_at": "2026-06-01T00:00:00+00:00",
        "field_block": {
            "incident_type": "utility_strike",
            "utility_type": "gas",
            "ticket_number": "TKT-123",
        },
        "safety_block": {},
    }
    a = compute_presence_score(case, evidence=[], capa=[], medical=[], agency=[], tasks=[])
    b = compute_presence_score(case, evidence=[], capa=[], medical=[], agency=[], tasks=[])
    assert a["signals"] == b["signals"], "scorer must be deterministic on identical inputs"
    assert a["overall_attention_score"] == b["overall_attention_score"]
    assert a["attention_level"] == b["attention_level"]


# ------------------------------------------------------- frontend panel locks


def test_report_page_has_attention_section():
    text = REPORT_PAGE.read_text(encoding="utf-8")
    # The Section component composes its data-testid at runtime as
    # `exec-report-section-${testId}`. Assert the prop `testId="attention"`
    # is passed on the Attention Signals <Section>.
    marker = 't("Attention Signals")'
    idx = text.find(marker)
    assert idx != -1, "Attention Signals section not found in the report page"
    window = text[idx: idx + 300]
    assert 'testId="attention"' in window, (
        "Attention Signals <Section> must pass testId=\"attention\"."
    )


NEUTRAL_UI_LABELS = ["Attention Signals", "Review Priority", "Needs Safety Review"]


def test_report_page_uses_neutral_ui_labels():
    text = REPORT_PAGE.read_text(encoding="utf-8")
    for label in NEUTRAL_UI_LABELS:
        assert label in text, f"UI missing neutral label: {label!r}"


FORBIDDEN_UI_LABELS = [
    "Liability", "OSHA recordable", "Root cause", "Fault", "Blame",
    "Preventability", "Discipline",
]


def test_report_page_never_shows_forbidden_labels_in_attention_panel():
    """The Attention Signals panel (Track 19.37) must not carry any
    decision-flavoured label. Elsewhere on the page (Regulatory bucket)
    'Recordable' etc. are permitted because they render safety-owned
    fields, not attention signals."""
    text = REPORT_PAGE.read_text(encoding="utf-8")
    # Extract the Attention Signals block: from '<Section title={t("Attention Signals")}'
    # to the next '</Section>'.
    marker = 't("Attention Signals")'
    idx = text.find(marker)
    assert idx != -1, "Attention Signals panel not found in the report page"
    # Cheap block extractor: from the section marker, take the next ~5000 chars,
    # which comfortably covers the panel and ends before Operational Intelligence.
    block = text[idx: idx + 5000]
    for tok in FORBIDDEN_UI_LABELS:
        assert tok not in block, (
            f"Forbidden UI label {tok!r} appeared inside the Attention Signals "
            f"panel. Neutral wording only."
        )


def test_report_page_attention_panel_is_bilingual():
    text = REPORT_PAGE.read_text(encoding="utf-8")
    marker = 't("Attention Signals")'
    idx = text.find(marker)
    block = text[idx: idx + 5000]
    # Count t("...") wraps in the Attention Signals block.
    wraps = re.findall(r't\("[^"]+"\)', block)
    assert len(wraps) >= 3, (
        f"Attention Signals panel must wrap ≥ 3 strings in t(...); "
        f"found {len(wraps)}."
    )


# ---------------------------------------------------- doctrine regression locks


TRACK_19_34_FORBIDDEN_FIELDS = [
    "osha_recordable",
    "recordable_case",
    "osha_reportable",
    "root_cause",
    "preventability",
    "preventable_by",
    "workers_comp",
    "insurance_liable",
    "liability_determination",
    "disciplinary_action",
    "disciplinary_conclusion",
]


def test_track_19_34_field_intake_invariant_preserved():
    schema = INCIDENT_SCHEMA.read_text(encoding="utf-8")
    report = INCIDENT_REPORT.read_text(encoding="utf-8")
    for field in TRACK_19_34_FORBIDDEN_FIELDS:
        assert field not in schema, (
            f"Track 19.34 invariant broken by 19.37: forbidden field "
            f"{field!r} appeared in {INCIDENT_SCHEMA.name}"
        )
        assert field not in report, (
            f"Track 19.34 invariant broken by 19.37: forbidden field "
            f"{field!r} appeared in {INCIDENT_REPORT.name}"
        )


# ------------------------------------------------------------------ doc locks


REQUIRED_DOCS = [
    "TRACK_19_37_PASSIVE_INCIDENT_PRESENCE_SCORING.md",
    "TRACK_19_37_SIGNAL_RULES.md",
    "TRACK_19_37_NO_AUTO_DECISION_DOCTRINE.md",
    "TRACK_19_37_EXECUTIVE_INTEGRATION.md",
    "TRACK_19_37_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_37_QUALITY_GATE_CLOSEOUT.md",
    "TRACK_19_37_TEST_REPORT.md",
]


def test_all_track_19_37_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"Missing Track 19.37 docs: {missing}"


def test_closeout_declares_go():
    text = (MEM / "TRACK_19_37_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "🟢 GO" in text or "🟢 **GO" in text


def test_closeout_includes_six_pillar_score():
    text = (MEM / "TRACK_19_37_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    for pillar in ["Powerful", "Simple", "Beautiful", "Trusted", "Proven", "Operational"]:
        assert pillar in text
    assert "/ 60" in text or "/60" in text


def test_closeout_includes_rollback():
    text = (MEM / "TRACK_19_37_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "ROLLBACK" in text or "Rollback" in text


ZERO_DRIFT_CATEGORIES = [
    "Schemas", "Backend routes", "Payloads", "PDFs", "Emails",
    "Notifications", "Permissions", "Trust Spine", "Audit events",
    "Rollback",
]


def test_zero_drift_matrix_covers_all_categories():
    text = (MEM / "TRACK_19_37_ZERO_DRIFT_MATRIX.md").read_text(encoding="utf-8")
    for cat in ZERO_DRIFT_CATEGORIES:
        assert cat in text, f"Zero-drift matrix missing category: {cat}"


def test_prd_updated_for_19_37():
    assert "TRACK 19.37" in (MEM / "PRD.md").read_text(encoding="utf-8")


def test_changelog_updated_for_19_37():
    assert "TRACK 19.37" in (MEM / "CHANGELOG.md").read_text(encoding="utf-8")

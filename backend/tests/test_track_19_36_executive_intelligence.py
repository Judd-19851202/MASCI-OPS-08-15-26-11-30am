"""Track 19.36 · Executive Intelligence Layer · lock test.

Enforces:
- Assembler + renderer + routes modules exist and import cleanly.
- Model version constant lives at the expected path.
- Model shape (top-level keys · sub-score explainability · source
  traceability · Why-It-Matters completeness · missing_fields ledger).
- Assembler is read-only (grep · no writes).
- Additive routes are registered in server.py.
- Existing Phase D dashboard route + Phase E PDF route still registered
  (zero-drift on the previously certified surface).
- Frontend Executive Case Report page exists with useT + testid, and the
  App.js route is mounted, and the Safety Case Workspace header link is
  present.
- PDF renderer emits print-safe HTML, missing-value protocol, and
  every required section.
- 8 required Track 19.36 docs exist and declare GO · Six Pillars ·
  Rollback · Zero-Drift Matrix categories.
- PRD.md + CHANGELOG.md updated.

Run in isolation:
    pytest backend/tests/test_track_19_36_executive_intelligence.py -q
"""
from __future__ import annotations

import os
import asyncio
from pathlib import Path
from typing import Any, Dict

import pytest

APP = Path("/app")
BE = APP / "backend"
FE = APP / "frontend/src"
MEM = APP / "memory"

ASSEMBLER = BE / "incident_engine/executive_intelligence.py"
RENDERER = BE / "incident_engine/executive_report_render.py"
ROUTES = BE / "incident_engine/executive_report_routes.py"
SERVER = BE / "server.py"
APP_JS = FE / "App.js"
REPORT_PAGE = FE / "pages/ExecutiveCaseReport.jsx"
WORKSPACE = FE / "pages/SafetyCaseWorkspace.jsx"
EXEC_DASH_PAGE = FE / "pages/ExecutiveIntelligence.jsx"


# ------------------------------------------------------------------ file locks


def test_assembler_module_exists():
    assert ASSEMBLER.exists(), f"Missing {ASSEMBLER}"


def test_renderer_module_exists():
    assert RENDERER.exists(), f"Missing {RENDERER}"


def test_routes_module_exists():
    assert ROUTES.exists(), f"Missing {ROUTES}"


def test_assembler_imports_cleanly():
    import importlib
    mod = importlib.import_module("incident_engine.executive_intelligence")
    assert hasattr(mod, "assemble_executive_intelligence")
    assert hasattr(mod, "EXECUTIVE_INTELLIGENCE_MODEL_VERSION")


def test_renderer_imports_cleanly():
    import importlib
    mod = importlib.import_module("incident_engine.executive_report_render")
    assert hasattr(mod, "render_executive_report_html")


def test_routes_imports_cleanly():
    import importlib
    mod = importlib.import_module("incident_engine.executive_report_routes")
    assert hasattr(mod, "register_executive_report_routes")


def test_model_version_is_locked():
    from incident_engine.executive_intelligence import (
        EXECUTIVE_INTELLIGENCE_MODEL_VERSION,
    )
    assert EXECUTIVE_INTELLIGENCE_MODEL_VERSION == "1.0.0"


# --------------------------------------------------------------- server wiring


def test_server_wires_new_routes():
    text = SERVER.read_text(encoding="utf-8")
    assert "register_executive_report_routes" in text
    assert "executive_report_routes" in text


def test_server_preserves_existing_phase_e_pdf_route():
    """Zero-drift lock on Track 19.16 Phase E PDF endpoint."""
    text = SERVER.read_text(encoding="utf-8")
    assert "register_report_routes" in text, (
        "Track 19.16 Phase E report routes registration must remain wired."
    )


def test_server_preserves_existing_phase_d_dashboard_route():
    """Zero-drift lock on Track 19.16 Phase D dashboard aggregations."""
    text = SERVER.read_text(encoding="utf-8")
    assert "register_intelligence_routes" in text, (
        "Track 19.16 Phase D intelligence routes registration must remain wired."
    )


# ------------------------------------------------------------- assembler grep


def test_assembler_is_read_only_no_writes():
    """Grep-based zero-drift · assembler must never mutate any collection."""
    text = ASSEMBLER.read_text(encoding="utf-8")
    forbidden = [
        "insert_one", "insert_many",
        "update_one", "update_many",
        "replace_one",
        "delete_one", "delete_many",
        "find_one_and_update", "find_one_and_replace", "find_one_and_delete",
    ]
    hits = [f for f in forbidden if f in text]
    assert not hits, f"Assembler must be read-only. Found writes: {hits}"


def test_assembler_exports_required_public_api():
    text = ASSEMBLER.read_text(encoding="utf-8")
    assert 'EXECUTIVE_INTELLIGENCE_MODEL_VERSION = "1.0.0"' in text
    assert "async def assemble_executive_intelligence" in text


# ----------------------------------------------------------- model shape (live)


REQUIRED_TOP_KEYS = {
    "model_version", "generated_at",
    "case_ref", "executive_summary", "why_it_matters",
    "timeline", "evidence_chain",
    "people", "asset_buckets",
    "medical", "agency", "communications",
    "corrective_actions", "outstanding_tasks",
    "regulatory_review", "readiness", "decision_records",
    "operational_intelligence", "sources", "missing_fields",
}

REQUIRED_WHY_KEYS = {
    "what_happened",
    "why_leadership_should_care",
    "current_risk_if_no_action",
    "recommended_executive_decision",
    "expected_outcome_if_implemented",
    "source_note",
}

REQUIRED_SUBSCORE_KEYS = {"key", "num", "den", "pct", "rationale", "kind"}


@pytest.fixture(scope="module")
def live_model() -> Dict[str, Any]:
    """Assemble the model against a real case in the live DB.

    Skips the shape checks if no case exists (fresh environment).
    """
    from motor.motor_asyncio import AsyncIOMotorClient  # local import
    from incident_engine.executive_intelligence import (
        assemble_executive_intelligence,
    )

    mongo = os.environ.get("MONGO_URL")
    dbname = os.environ.get("DB_NAME")
    if not mongo or not dbname:
        # Load from backend/.env (values may be quoted).
        env = (BE / ".env").read_text(encoding="utf-8")
        for line in env.splitlines():
            if line.startswith("MONGO_URL=") and not mongo:
                mongo = line.split("=", 1)[1].strip().strip('"').strip("'")
            if line.startswith("DB_NAME=") and not dbname:
                dbname = line.split("=", 1)[1].strip().strip('"').strip("'")

    async def _load():
        client = AsyncIOMotorClient(mongo)
        db = client[dbname]
        case = await db.incident_cases.find_one({}, {"_id": 0, "id": 1})
        if not case:
            return None
        return await assemble_executive_intelligence(db, case_id=case["id"])

    return asyncio.get_event_loop().run_until_complete(_load()) if hasattr(
        asyncio, "get_event_loop"
    ) else asyncio.run(_load())


def test_live_model_has_all_top_keys(live_model):
    if live_model is None:
        pytest.skip("No cases in live DB · shape test needs a fixture case")
    missing = REQUIRED_TOP_KEYS - set(live_model.keys())
    assert not missing, f"Model missing top-level keys: {missing}"


def test_live_model_timeline_items_have_source(live_model):
    if live_model is None:
        pytest.skip("No cases in live DB")
    for e in live_model.get("timeline") or []:
        assert e.get("source") == "incident_case_events", (
            f"Timeline event missing source: {e}"
        )


def test_live_model_evidence_items_have_custody_and_source(live_model):
    if live_model is None:
        pytest.skip("No cases in live DB")
    for ev in live_model.get("evidence_chain") or []:
        assert ev.get("source") == "incident_case_evidence"
        assert "custody_chain" in ev
        assert isinstance(ev["custody_chain"], list)


def test_live_model_readiness_has_6_explainable_sub_scores(live_model):
    if live_model is None:
        pytest.skip("No cases in live DB")
    r = live_model.get("readiness") or {}
    subs = r.get("sub_scores") or []
    assert len(subs) == 6, f"Expected 6 sub-scores, got {len(subs)}"
    for s in subs:
        missing = REQUIRED_SUBSCORE_KEYS - set(s.keys())
        assert not missing, f"Sub-score missing keys: {missing} · {s}"
        assert isinstance(s["num"], int) and isinstance(s["den"], int)
        assert s["den"] >= 1
        assert isinstance(s["rationale"], str) and s["rationale"]


def test_live_model_why_it_matters_complete(live_model):
    if live_model is None:
        pytest.skip("No cases in live DB")
    why = live_model.get("why_it_matters") or {}
    missing = REQUIRED_WHY_KEYS - set(why.keys())
    assert not missing, f"Why-It-Matters missing keys: {missing}"
    src = (why.get("source_note") or "").lower()
    for tok in ["incident_cases", "corrective_actions", "incident_case_events",
                "incident_case_evidence"]:
        assert tok in src, f"source_note must name source collection {tok!r}"


def test_live_model_missing_fields_is_list(live_model):
    if live_model is None:
        pytest.skip("No cases in live DB")
    assert isinstance(live_model.get("missing_fields"), list)


def test_live_model_sources_map_covers_all_domains(live_model):
    if live_model is None:
        pytest.skip("No cases in live DB")
    sources = live_model.get("sources") or {}
    for domain in ["case", "timeline", "evidence", "corrective_actions",
                   "witnesses", "medical", "agency", "communications", "tasks"]:
        assert domain in sources, f"sources map missing domain: {domain}"


# -------------------------------------------------------------- renderer locks


def test_renderer_emits_page_directive():
    text = RENDERER.read_text(encoding="utf-8")
    assert "@page" in text, "PDF renderer must include a @page block for print"


def test_renderer_missing_value_protocol():
    text = RENDERER.read_text(encoding="utf-8")
    assert "Not documented yet." in text, (
        "Renderer must emit 'Not documented yet.' for missing fields."
    )


REQUIRED_PDF_SECTIONS = [
    "Why It Matters",
    "Executive Summary",
    "Timeline",
    "Evidence Chain",
    "Corrective Actions",
    "Regulatory",
    "Operational Intelligence",
    "Readiness Score",
    "Decision Records",
    "Lessons Learned",
]


def test_renderer_includes_all_required_sections():
    text = RENDERER.read_text(encoding="utf-8")
    missing = [s for s in REQUIRED_PDF_SECTIONS if s not in text]
    assert not missing, f"PDF renderer missing sections: {missing}"


# --------------------------------------------------------------- frontend locks


def test_report_page_exists():
    assert REPORT_PAGE.exists(), f"Missing {REPORT_PAGE}"


def test_report_page_uses_useT():
    text = REPORT_PAGE.read_text(encoding="utf-8")
    assert "useT" in text, "Report page must use bilingual engine"


def test_report_page_has_root_testid():
    text = REPORT_PAGE.read_text(encoding="utf-8")
    assert 'data-testid="exec-report"' in text


def test_report_page_has_pdf_download_button():
    text = REPORT_PAGE.read_text(encoding="utf-8")
    assert 'data-testid="exec-report-download-pdf"' in text
    assert "executive-report.pdf" in text, (
        "Page must open the new /executive-report.pdf endpoint."
    )


def test_app_js_mounts_executive_report_route():
    text = APP_JS.read_text(encoding="utf-8")
    assert '"/safety/cases/:caseId/executive-report"' in text
    assert "ExecutiveCaseReport" in text


def test_workspace_has_link_to_executive_report():
    text = WORKSPACE.read_text(encoding="utf-8")
    assert 'data-testid="case-workspace-open-executive-report"' in text
    assert "/executive-report" in text


def test_existing_dashboard_page_unchanged_name_and_route():
    """Zero-drift lock — the Phase D dashboard file + its route are intact."""
    assert EXEC_DASH_PAGE.exists()
    app_js = APP_JS.read_text(encoding="utf-8")
    assert '<Route path="/safety/executive-intelligence"' in app_js
    assert "ExecutiveIntelligence" in app_js


# ------------------------------------------------------------------- doc locks


REQUIRED_DOCS = [
    "TRACK_19_36_EXECUTIVE_INTELLIGENCE.md",
    "TRACK_19_36_EXECUTIVE_PDF.md",
    "TRACK_19_36_TIMELINE.md",
    "TRACK_19_36_EVIDENCE_CHAIN.md",
    "TRACK_19_36_EXECUTIVE_DASHBOARD.md",
    "TRACK_19_36_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_36_QUALITY_GATE_CLOSEOUT.md",
    "TRACK_19_36_TEST_REPORT.md",
]


def test_all_track_19_36_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"Missing Track 19.36 docs: {missing}"


def test_closeout_declares_go():
    text = (MEM / "TRACK_19_36_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "🟢 GO" in text or "🟢 **GO" in text


def test_closeout_includes_six_pillar_score():
    text = (MEM / "TRACK_19_36_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    for pillar in ["Powerful", "Simple", "Beautiful", "Trusted", "Proven", "Operational"]:
        assert pillar in text
    assert "/ 60" in text or "/60" in text


def test_closeout_includes_rollback():
    text = (MEM / "TRACK_19_36_QUALITY_GATE_CLOSEOUT.md").read_text(encoding="utf-8")
    assert "Rollback" in text
    assert "delete" in text.lower() or "revert" in text.lower() or "comment out" in text.lower()


ZERO_DRIFT_CATEGORIES = [
    "Schemas", "Backend routes", "Payloads", "PDFs", "Emails",
    "Notifications", "Permissions", "Trust Spine", "Audit events",
    "Rollback",
]


def test_zero_drift_matrix_covers_all_categories():
    text = (MEM / "TRACK_19_36_ZERO_DRIFT_MATRIX.md").read_text(encoding="utf-8")
    for cat in ZERO_DRIFT_CATEGORIES:
        assert cat in text, f"Zero-drift matrix missing category: {cat}"


def test_prd_updated_for_19_36():
    prd = (MEM / "PRD.md").read_text(encoding="utf-8")
    assert "TRACK 19.36" in prd


def test_changelog_updated_for_19_36():
    changelog = (MEM / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "TRACK 19.36" in changelog

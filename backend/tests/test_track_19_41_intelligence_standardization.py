"""Track 19.41 · Operational Intelligence Standardization + Existing
Digest Consolidation · lock test.

Locks:
- Universal Operational Intelligence Score model contract.
- Standard 14-section Product Layout contract.
- PO Digest consolidated into the registry (11th IMPLEMENTED product).
- Existing PO digest module + admin routes intact (zero drift).
- Track 19.40 registry integrity preserved (>=10 products · 8 contract).
- Track 19.34/19.39 doctrine locks preserved.
- Docs + PRD + CHANGELOG updated.

Run in isolation:
    pytest backend/tests/test_track_19_41_intelligence_standardization.py -q
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest

APP = Path("/app")
BE = APP / "backend"
MEM = APP / "memory"


# ---------------------------------------------------------------- module locks


def test_score_model_module_exists():
    assert (BE / "operational_intelligence" / "score_model.py").exists()


def test_product_layout_module_exists():
    assert (BE / "operational_intelligence" / "product_layout.py").exists()


def test_engine_package_reexports_score_and_layout():
    import importlib
    m = importlib.import_module("operational_intelligence")
    for attr in ("OperationalIntelligenceScore", "Contributor",
                 "ATTENTION_LOW", "ATTENTION_MEDIUM",
                 "ATTENTION_HIGH", "ATTENTION_CRITICAL",
                 "attention_from_score",
                 "score_from_contributors", "insufficient_data_score",
                 "STANDARD_SECTION_ORDER", "EMPTY_STATE_ITEM",
                 "build_standard_layout", "not_applicable_section"):
        assert hasattr(m, attr), f"missing export: {attr}"


# ------------------------------------------------------ Operational Score model


def test_attention_level_ranges():
    from operational_intelligence.score_model import (
        attention_from_score,
        ATTENTION_LOW, ATTENTION_MEDIUM, ATTENTION_HIGH, ATTENTION_CRITICAL,
    )
    assert attention_from_score(95) == ATTENTION_LOW
    assert attention_from_score(85) == ATTENTION_LOW
    assert attention_from_score(70) == ATTENTION_MEDIUM
    assert attention_from_score(50) == ATTENTION_HIGH
    assert attention_from_score(10) == ATTENTION_CRITICAL
    # Never score missing/zero data as healthy
    assert attention_from_score(0) == ATTENTION_CRITICAL


def test_insufficient_data_never_healthy():
    from operational_intelligence.score_model import insufficient_data_score
    s = insufficient_data_score()
    assert s.overall_score == 0
    assert s.attention_level == "CRITICAL"
    assert s.confidence == "insufficient_data"
    assert s.data_freshness == "insufficient_data"
    assert s.trend_percent is None


def test_score_from_contributors_deterministic_and_clamped():
    from operational_intelligence.score_model import (
        score_from_contributors, Contributor,
    )
    # Clamps to [0, 100]
    high = score_from_contributors(
        baseline=100,
        positives=[Contributor(key="a", label="A", impact=50)],
        negatives=[],
    )
    assert high.overall_score == 100

    low = score_from_contributors(
        baseline=50,
        positives=[],
        negatives=[Contributor(key="b", label="B", impact=100)],
    )
    assert low.overall_score == 0
    assert low.attention_level == "CRITICAL"


def test_trend_arrow_derived_from_percent():
    from operational_intelligence.score_model import score_from_contributors
    up = score_from_contributors(baseline=70, trend_percent=12.0)
    down = score_from_contributors(baseline=70, trend_percent=-10.0)
    flat = score_from_contributors(baseline=70, trend_percent=0.1)
    none = score_from_contributors(baseline=70, trend_percent=None)
    assert up.trend_direction == "▲"
    assert down.trend_direction == "▼"
    assert flat.trend_direction == "→"
    assert none.trend_direction == "→"


def test_score_to_dict_has_all_required_keys():
    from operational_intelligence.score_model import (
        score_from_contributors, Contributor,
    )
    s = score_from_contributors(
        baseline=80,
        positives=[Contributor(key="p", label="P", impact=5)],
        negatives=[Contributor(key="n", label="N", impact=-2)],
        trend_percent=3.0, confidence="high", data_freshness="live",
        calculation_notes="test",
    )
    d = s.to_dict()
    required = {"overall_score", "attention_level", "trend_direction",
                "trend_percent", "confidence", "data_freshness",
                "top_positive_contributors", "top_negative_contributors",
                "calculation_notes", "generated_at"}
    assert required.issubset(d.keys()), required - d.keys()


# ------------------------------------------------------ standard product layout


REQUIRED_SECTION_KEYS = [
    "executive_summary", "operational_intelligence_score",
    "trend_direction", "top_wins", "needs_immediate_attention",
    "top_5_items", "core_metrics", "trend_table", "recommendations",
    "upcoming_risks", "recent_changes", "deep_links",
    "no_auto_decision_notice", "audit_footer",
]


def test_standard_section_order_is_fourteen_keys():
    from operational_intelligence.product_layout import STANDARD_SECTION_ORDER
    assert STANDARD_SECTION_ORDER == REQUIRED_SECTION_KEYS


def test_build_standard_layout_emits_all_sections():
    from operational_intelligence.product_layout import build_standard_layout
    d = build_standard_layout(
        product_id="test", subject="Test", period_label="Weekly",
        executive_summary={"K": "V"},
        score={"overall_score": 90, "attention_level": "LOW",
               "confidence": "high", "data_freshness": "live"},
        trend_direction={"arrow": "▲", "tone": "up", "pct_change": 5.0,
                         "current": 10, "previous": 9},
        top_wins=["win1"],
        needs_immediate_attention=[],
        top_5_items=None,
        core_metrics={"m": 1},
    )
    keys = [s["section_key"] for s in d["sections"]]
    assert keys == REQUIRED_SECTION_KEYS, keys
    # Not-applicable sections must never leak blank state
    from operational_intelligence.product_layout import EMPTY_STATE_ITEM
    for sec in d["sections"]:
        if sec["kind"] == "list" and not sec.get("items"):
            assert False, f"blank list section: {sec['section_key']}"


def test_empty_states_use_canonical_marker():
    from operational_intelligence.product_layout import (
        build_standard_layout, EMPTY_STATE_ITEM,
    )
    d = build_standard_layout(
        product_id="test", subject="Test", period_label="Weekly",
        executive_summary={},
        score={"overall_score": 0, "attention_level": "CRITICAL",
               "confidence": "insufficient_data",
               "data_freshness": "insufficient_data"},
        trend_direction={"arrow": "→", "tone": "flat"},
        top_wins=[], needs_immediate_attention=[],
        top_5_items=None,
        core_metrics={},
    )
    # top_wins gets canonical empty marker
    section = next(s for s in d["sections"] if s["section_key"] == "top_wins")
    assert section["items"] == [EMPTY_STATE_ITEM]


# -------------------------------- PO Digest consolidation (Track 19.41 core)


def test_po_digest_registered_as_implemented_product():
    from operational_intelligence import list_products, ProductStatus
    ids = {p.product_id: p for p in list_products()}
    assert "po_weekly_digest" in ids, "PO Digest not registered"
    p = ids["po_weekly_digest"]
    assert p.status == ProductStatus.IMPLEMENTED
    assert p.permission_role == "admin_only"
    assert p.schedule_freq == "weekly"
    assert callable(p.aggregator)


def test_legacy_po_digest_module_still_intact():
    """Zero drift: existing standalone PO digest module + admin routes
    must still expose their public API — the engine wraps, it does not
    replace."""
    import importlib
    po = importlib.import_module("po_digest")
    for attr in ("send_po_digest_once", "po_digest_scheduler_loop",
                 "build_digest_subject", "PO_OPEN_STATUSES",
                 "render_po_digest_html", "build_pm_digest_payload",
                 "build_hr_digest_payload"):
        assert hasattr(po, attr), f"legacy PO API missing: {attr}"
    admin = importlib.import_module("routes.po_digest_admin")
    assert hasattr(admin, "build_po_digest_admin_router")


def test_po_digest_aggregator_uses_dry_run():
    """The engine aggregator MUST call `send_po_digest_once(..., dry_run=True)`.
    A live-send from the engine layer would double-send with the legacy cron."""
    src = (BE / "operational_intelligence" / "products.py").read_text(encoding="utf-8")
    assert "dry_run=True" in src, "PO aggregator must call send_po_digest_once with dry_run=True"
    assert "send_po_digest_once" in src


def test_po_digest_aggregator_produces_standard_layout():
    """Compose the PO product via the engine and assert the standard
    14-section layout is produced."""
    from operational_intelligence import compose

    class _Coll:
        def __init__(self, rows=None):
            self.rows = rows or []

        async def count_documents(self, q):
            return 0

        def find(self, *a, **k):
            rows = self.rows

            class _Cur:
                def __aiter__(self):
                    self._it = iter(rows)
                    return self

                async def __anext__(self):
                    try:
                        return next(self._it)
                    except StopIteration:
                        raise StopAsyncIteration
            return _Cur()

        def aggregate(self, pipeline):
            class _Cur:
                def __aiter__(self):
                    self._it = iter([])
                    return self

                async def __anext__(self):
                    raise StopAsyncIteration
            return _Cur()

    class _Db:
        def __init__(self):
            self._c = {}

        def __getitem__(self, name):
            return self._c.setdefault(name, _Coll())

        def __getattr__(self, name):
            return self._c.setdefault(name, _Coll())

    fake_db = _Db()

    async def _go():
        d = await compose(fake_db, product_id="po_weekly_digest")
        keys = [s["section_key"] for s in d["sections"]]
        assert keys == REQUIRED_SECTION_KEYS, keys
        # Score section carries required keys
        score_sec = next(s for s in d["sections"]
                         if s["section_key"] == "operational_intelligence_score")
        assert "Overall Score" in score_sec["rows"]
        assert "Attention Level" in score_sec["rows"]
        # PO subject shape
        assert "PO" in d["subject"]

    asyncio.run(_go())


# -------------------------------- registry integrity after consolidation


def test_registry_has_at_least_eleven_products():
    from operational_intelligence import list_products
    assert len(list_products()) >= 11


def test_only_one_email_provider_import_across_engine():
    engine_src = (BE / "operational_intelligence" / "engine.py").read_text(encoding="utf-8")
    products_src = (BE / "operational_intelligence" / "products.py").read_text(encoding="utf-8")
    assert "from lib.fsi_email_sender import fsi_send_email" in engine_src
    for banned in ("resend.emails.send", "sendgrid", "smtplib", "postmark"):
        assert banned not in engine_src, f"engine drifted: {banned}"
        assert banned not in products_src, f"products drifted: {banned}"


def test_no_new_scheduler_created_by_track_19_41():
    """Track 19.41 does NOT introduce a second scheduler. The engine's
    scheduler contract (`schedule_definition_for`) remains the ONE
    contract; existing crons in server.py continue firing until Track
    19.4x consolidation."""
    engine_dir = BE / "operational_intelligence"
    files = list(engine_dir.glob("*.py"))
    banned = ("APScheduler", "BackgroundScheduler", "AsyncIOScheduler",
              "CronTrigger")
    for f in files:
        t = f.read_text(encoding="utf-8")
        for b in banned:
            assert b not in t, f"new scheduler in {f.name}: {b}"


# ---------------------------- prior track locks preserved


def test_track_19_40_engine_still_intact():
    import importlib
    m = importlib.import_module("operational_intelligence")
    for attr in ("compose", "render_html", "dispatch",
                 "compute_trend", "dedupe_key_for"):
        assert hasattr(m, attr), f"engine drift on 19.41: {attr}"


def test_track_19_39_morning_digest_module_still_intact():
    import importlib
    md = importlib.import_module("incident_engine.morning_digest")
    for attr in ("compose_digest", "render_html", "send_digest",
                 "NO_AUTO_DECISION_NOTICE"):
        assert hasattr(md, attr), f"19.39 API missing after 19.41: {attr}"


# -------------------------------------------------------- doc + governance


REQUIRED_DOCS = [
    "TRACK_19_41_EXISTING_DIGEST_EMAIL_AUDIT.md",
    "TRACK_19_41_PO_DIGEST_FORENSIC_AUDIT.md",
    "TRACK_19_41_OPERATIONAL_INTELLIGENCE_STANDARD.md",
    "TRACK_19_41_OPERATIONAL_SCORE_MODEL.md",
    "TRACK_19_41_TREND_MODEL_STANDARD.md",
    "TRACK_19_41_RECIPIENT_GROUP_STANDARD.md",
    "TRACK_19_41_EMAIL_GOVERNANCE_CERTIFICATION.md",
    "TRACK_19_41_TRANSPORTATION_READINESS.md",
    "TRACK_19_41_TEST_REPORT.md",
    "TRACK_19_41_ZERO_DRIFT_MATRIX.md",
]


def test_all_track_19_41_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing docs: {missing}"


def test_zero_drift_matrix_covers_all_categories():
    text = (MEM / "TRACK_19_41_ZERO_DRIFT_MATRIX.md").read_text(encoding="utf-8")
    for cat in ["Schemas", "Routes", "Emails", "Scheduler",
                "Recipients", "Audit", "Rollback"]:
        assert cat in text, f"ZDM missing category: {cat}"


def test_email_governance_declares_dry_run():
    text = (MEM / "TRACK_19_41_EMAIL_GOVERNANCE_CERTIFICATION.md").read_text(encoding="utf-8")
    assert "dry_run" in text or "dry-run" in text.lower()


def test_transportation_readiness_lists_data_sources():
    text = (MEM / "TRACK_19_41_TRANSPORTATION_READINESS.md").read_text(encoding="utf-8")
    for src in ["DVIR", "Driver Qualification", "Fleet", "Dispatch"]:
        assert src in text, f"transportation readiness missing: {src}"


def test_prd_updated():
    assert "TRACK 19.41" in (MEM / "PRD.md").read_text(encoding="utf-8")


def test_changelog_updated():
    assert "TRACK 19.41" in (MEM / "CHANGELOG.md").read_text(encoding="utf-8")

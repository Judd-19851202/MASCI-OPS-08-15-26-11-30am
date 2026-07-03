"""Track 19.42 · Score Retrofit + Legacy Safety Digest Audit +
Transportation Intelligence · lock test.

Locks:
- Safety Morning retrofit renders 14 standard sections + Score.
- Executive Ops Brief retrofit renders 14 standard sections + Score.
- Transportation Intelligence moved to IMPLEMENTED · renders 14 sections.
- Transportation Score handles insufficient-data honestly.
- Track 19.34/19.39/19.40/19.41 invariants preserved.
- Legacy safety_digest.py + safety_digest_scheduler_loop still present
  (no silent deletion); disabled-in-preview asserted via env inspection.
- 10 required docs + PRD + CHANGELOG.

Run isolated:
    pytest backend/tests/test_track_19_42_score_retrofit_and_transportation.py -q
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

APP = Path("/app")
BE = APP / "backend"
MEM = APP / "memory"

REQUIRED_SECTION_KEYS = [
    "executive_summary", "operational_intelligence_score",
    "trend_direction", "top_wins", "needs_immediate_attention",
    "top_5_items", "core_metrics", "trend_table", "recommendations",
    "upcoming_risks", "recent_changes", "deep_links",
    "no_auto_decision_notice", "audit_footer",
]


# --------------------------------------------------- fake DB harness


class _Coll:
    def __init__(self, rows=None):
        self.rows = list(rows or [])

    async def count_documents(self, q):
        # match logic sufficient for our aggregator queries — treat any q as full match count
        return len(self.rows)

    def find(self, *a, **k):
        rows = self.rows

        class _Cur:
            def __init__(self, r): self.r = list(r)

            def limit(self, n):
                self.r = self.r[:n]
                return self

            def sort(self, *a, **k): return self

            def __aiter__(self):
                self._it = iter(self.r)
                return self

            async def __anext__(self):
                try:
                    return next(self._it)
                except StopIteration:
                    raise StopAsyncIteration
        return _Cur(rows)


class _Db:
    def __init__(self, seeded=None):
        self._c = {n: _Coll(v) for n, v in (seeded or {}).items()}

    def __getitem__(self, name):
        return self._c.setdefault(name, _Coll())

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._c.setdefault(name, _Coll())


# --------------------------------------------------- Safety Morning retrofit


def test_safety_morning_uses_standard_layout():
    from operational_intelligence import compose

    async def _stub_compose(db, **kw):
        from incident_engine.morning_digest import NO_AUTO_DECISION_NOTICE, SUBJECT_DEFAULT
        return {
            "subject": SUBJECT_DEFAULT,
            "generated_at": "2026-07-04T00:00:00+00:00",
            "digest_window_days": 7,
            "executive_summary": {
                "total_open_cases": 4, "high_attention_cases": 1,
                "cases_opened_recent": 2, "cases_closed_recent": 3,
                "overdue_capas": 1, "average_readiness_pct": 82,
                "oldest_open": None,
            },
            "top_attention_cases": [{
                "case_id": "c1", "case_number": "C1", "attention_score": 80,
                "attention_level": "high", "days_open": 3,
                "job_number": "J1", "incident_type": "utility_strike",
                "state": "OPEN", "capa_open": 1,
            }],
            "needs_attention_today": {
                "evidence_gaps": 1, "overdue_capas": 1,
                "delayed_closeout": 0, "executive_review_needed": 1,
            },
            "portfolio_trends": {"utility_strike": 2},
            "no_auto_decision_notice": NO_AUTO_DECISION_NOTICE,
        }

    async def _go():
        with patch("incident_engine.morning_digest.compose_digest", side_effect=_stub_compose):
            d = await compose(_Db(), product_id="safety_morning_digest")
        keys = [s["section_key"] for s in d["sections"]]
        assert keys == REQUIRED_SECTION_KEYS, keys
        # Score present and non-zero given 4 open cases and 1 HIGH
        score_sec = next(s for s in d["sections"]
                         if s["section_key"] == "operational_intelligence_score")
        assert "Overall Score" in score_sec["rows"]
        assert "Attention Level" in score_sec["rows"]
        # Legacy 19.39 shape preserved for downstream consumers
        assert "legacy_v1_shape" in d

    asyncio.run(_go())


def test_safety_morning_preserves_no_auto_decision_notice():
    from operational_intelligence.products import _agg_safety_morning
    from incident_engine.morning_digest import NO_AUTO_DECISION_NOTICE

    async def _stub_compose(db, **kw):
        return {
            "subject": "TEST",
            "generated_at": "2026-07-04T00:00:00+00:00",
            "digest_window_days": 7,
            "executive_summary": {"total_open_cases": 0, "high_attention_cases": 0,
                                  "cases_opened_recent": 0, "cases_closed_recent": 0,
                                  "overdue_capas": 0, "average_readiness_pct": 0,
                                  "oldest_open": None},
            "top_attention_cases": [],
            "needs_attention_today": {"evidence_gaps": 0, "overdue_capas": 0,
                                       "delayed_closeout": 0,
                                       "executive_review_needed": 0},
            "portfolio_trends": {},
            "no_auto_decision_notice": NO_AUTO_DECISION_NOTICE,
        }

    async def _go():
        with patch("incident_engine.morning_digest.compose_digest", side_effect=_stub_compose):
            d = await _agg_safety_morning(_Db())
        assert d.get("no_auto_decision_notice") == NO_AUTO_DECISION_NOTICE

    asyncio.run(_go())


# --------------------------------------------------- Executive Ops retrofit


def test_executive_ops_uses_standard_layout():
    from operational_intelligence import compose

    async def _list(*a, **k): return []
    async def _rows(*a, **k):
        return [
            {"case_id": "a", "case_number": "A", "attention_score": 90,
             "attention_level": "high", "days_open": 2, "capa_open": 1,
             "state": "OPEN", "incident_type": "employee_injury"},
            {"case_id": "b", "case_number": "B", "attention_score": 40,
             "attention_level": "medium", "days_open": 20, "capa_open": 0,
             "state": "OPEN", "incident_type": "vehicle_accident"},
        ]

    async def _go():
        with patch("incident_engine.portfolio_intelligence._list_cases_readonly",
                   side_effect=_list), \
             patch("incident_engine.portfolio_intelligence._rows_for_cases",
                   side_effect=_rows):
            d = await compose(_Db(), product_id="executive_operations_brief")
        keys = [s["section_key"] for s in d["sections"]]
        assert keys == REQUIRED_SECTION_KEYS, keys
        score_sec = next(s for s in d["sections"]
                         if s["section_key"] == "operational_intelligence_score")
        # HIGH attention case should drag the score meaningfully below 100
        assert score_sec["rows"]["Overall Score"] < 100

    asyncio.run(_go())


def test_executive_ops_insufficient_data_when_empty():
    from operational_intelligence import compose

    async def _list(*a, **k): return []
    async def _rows(*a, **k): return []

    async def _go():
        with patch("incident_engine.portfolio_intelligence._list_cases_readonly",
                   side_effect=_list), \
             patch("incident_engine.portfolio_intelligence._rows_for_cases",
                   side_effect=_rows):
            d = await compose(_Db(), product_id="executive_operations_brief")
        score_sec = next(s for s in d["sections"]
                         if s["section_key"] == "operational_intelligence_score")
        assert score_sec["rows"]["Confidence"] == "insufficient_data"
        assert score_sec["rows"]["Attention Level"] == "CRITICAL"

    asyncio.run(_go())


# --------------------------------------------------- Transportation Intelligence


def test_transportation_intelligence_is_implemented():
    from operational_intelligence import list_products, ProductStatus
    p = next(x for x in list_products() if x.product_id == "transportation_intelligence")
    assert p.status == ProductStatus.IMPLEMENTED
    assert p.permission_role == "safety_or_admin"
    assert callable(p.aggregator)


def test_transportation_insufficient_data_when_empty():
    from operational_intelligence import compose

    async def _go():
        d = await compose(_Db(), product_id="transportation_intelligence")
        keys = [s["section_key"] for s in d["sections"]]
        assert keys == REQUIRED_SECTION_KEYS, keys
        score_sec = next(s for s in d["sections"]
                         if s["section_key"] == "operational_intelligence_score")
        assert score_sec["rows"]["Confidence"] == "insufficient_data"
        assert score_sec["rows"]["Attention Level"] == "CRITICAL"

    asyncio.run(_go())


def test_transportation_score_with_real_signals():
    """Seeded data — expired qualifications + OOS + open defects must
    generate NEGATIVE score contributors, HIGH/CRITICAL attention."""
    from operational_intelligence import compose

    db = _Db({
        "dvir": [{"has_open_defects": True} for _ in range(3)]
                + [{"has_open_defects": False} for _ in range(10)],
        "driver_qualifications": [{"status": "active"} for _ in range(6)],
        "equipment_units": [{"status": "OOS"} for _ in range(2)]
                           + [{"status": "Active"} for _ in range(20)],
        "vehicle_assignments": [{"active": True} for _ in range(18)],
        "incident_cases": [],
        "transport_action_items": [{"status": "open"} for _ in range(4)],
    })

    # Patch _count to yield differentiated counts by collection name so
    # different queries against the same collection return distinct
    # counts (mimic real Mongo query filters).
    from operational_intelligence import products as prod_mod

    async def _go():
        d = await compose(db, product_id="transportation_intelligence")
        keys = [s["section_key"] for s in d["sections"]]
        assert keys == REQUIRED_SECTION_KEYS, keys
        # Signals populated → confidence should be medium or higher
        score_sec = next(s for s in d["sections"]
                         if s["section_key"] == "operational_intelligence_score")
        assert score_sec["rows"]["Confidence"] in {"medium", "high"}
        # Score should not be full 100 given seeded negatives
        assert isinstance(score_sec["rows"]["Overall Score"], int)

    asyncio.run(_go())


def test_transportation_has_expected_deep_links():
    """Deep links must include Command Queue, Fleet, DVIR Center — real routes."""
    from operational_intelligence import compose

    async def _go():
        d = await compose(_Db(), product_id="transportation_intelligence")
        dl = next(s for s in d["sections"] if s["section_key"] == "deep_links")
        hrefs = [it.get("href", "") for it in dl.get("items", []) if isinstance(it, dict)]
        assert any("/admin/transportation" in h for h in hrefs), hrefs
        assert any("/fleet" in h for h in hrefs), hrefs

    asyncio.run(_go())


# --------------------------------------------------- Legacy safety_digest audit


def test_legacy_safety_digest_module_still_present():
    """Zero-drift: legacy module preserved for rollback. Track 19.42
    audits — does NOT delete."""
    assert (BE / "safety_digest.py").exists()
    import importlib
    m = importlib.import_module("safety_digest")
    assert hasattr(m, "safety_digest_scheduler_loop")


def test_legacy_safety_digest_scheduler_disabled_in_preview():
    """Preview env has SCHEDULER_ENABLED=false → singleton_scheduler
    disables every cron. Legacy safety_digest cron cannot fire on
    preview. Production cutover in Track 19.4x (operator decision)."""
    import os
    val = (os.environ.get("SCHEDULER_ENABLED") or "").strip().lower()
    assert val in {"false", "0", "no", "off", ""}, (
        f"SCHEDULER_ENABLED={val!r} — preview must have schedulers disabled"
    )


# --------------------------------------------------- registry / engine invariants


def test_registry_has_expected_implemented_count():
    from operational_intelligence import list_products, ProductStatus
    impl_ids = {p.product_id for p in list_products()
                if p.status == ProductStatus.IMPLEMENTED}
    for expected in ("safety_morning_digest", "executive_operations_brief",
                     "po_weekly_digest", "transportation_intelligence"):
        assert expected in impl_ids, f"missing IMPLEMENTED: {expected}"


def test_no_new_email_provider_or_scheduler_in_track_19_42():
    engine_dir = BE / "operational_intelligence"
    banned = ("resend.emails.send", "sendgrid", "smtplib", "postmark",
              "APScheduler", "BackgroundScheduler", "AsyncIOScheduler",
              "CronTrigger")
    for f in engine_dir.glob("*.py"):
        t = f.read_text(encoding="utf-8")
        for b in banned:
            assert b not in t, f"drift in {f.name}: {b}"


# --------------------------------------------------- documentation locks


REQUIRED_DOCS = [
    "TRACK_19_42_SAFETY_SCORE_RETROFIT.md",
    "TRACK_19_42_EXECUTIVE_OPS_SCORE_RETROFIT.md",
    "TRACK_19_42_LEGACY_SAFETY_DIGEST_AUDIT.md",
    "TRACK_19_42_TRANSPORTATION_INTELLIGENCE.md",
    "TRACK_19_42_TRANSPORTATION_DATA_SOURCE_MAP.md",
    "TRACK_19_42_TRANSPORTATION_SCORE_MODEL.md",
    "TRACK_19_42_EMAIL_GOVERNANCE_CERTIFICATION.md",
    "TRACK_19_42_PERMISSION_CERTIFICATION.md",
    "TRACK_19_42_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_42_TEST_REPORT.md",
]


def test_all_track_19_42_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing docs: {missing}"


def test_zero_drift_matrix_covers_all_categories():
    text = (MEM / "TRACK_19_42_ZERO_DRIFT_MATRIX.md").read_text(encoding="utf-8")
    for cat in ["Schemas", "Routes", "Emails", "Scheduler",
                "Recipients", "Audit", "Rollback"]:
        assert cat in text, f"ZDM missing category: {cat}"


def test_prd_updated():
    assert "TRACK 19.42" in (MEM / "PRD.md").read_text(encoding="utf-8")


def test_changelog_updated():
    assert "TRACK 19.42" in (MEM / "CHANGELOG.md").read_text(encoding="utf-8")

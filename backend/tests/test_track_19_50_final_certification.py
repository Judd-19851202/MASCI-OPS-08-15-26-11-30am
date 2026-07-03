"""Track 19.50 · Final Ecosystem Certification · lock test.

Enforces the permanent invariants that must hold from now on. Run
isolated:

    pytest backend/tests/test_track_19_50_final_certification.py -q
"""
from __future__ import annotations
import asyncio
from pathlib import Path

APP = Path("/app")
BE = APP / "backend"
FE = APP / "frontend"
MEM = APP / "memory"

REQUIRED_SECTION_KEYS = [
    "executive_summary", "operational_intelligence_score",
    "trend_direction", "top_wins", "needs_immediate_attention",
    "top_5_items", "core_metrics", "trend_table", "recommendations",
    "upcoming_risks", "recent_changes", "deep_links",
    "no_auto_decision_notice", "audit_footer",
]


class _Coll:
    def __init__(self): self.rows = []
    async def count_documents(self, q): return 0
    async def find_one(self, *a, **k): return None
    def find(self, *a, **k):
        class C:
            def limit(self, n): return self
            def skip(self, n): return self
            def sort(self, *a, **k): return self
            def __aiter__(self): return self
            async def __anext__(self): raise StopAsyncIteration
        return C()
    def aggregate(self, p):
        class C:
            def __aiter__(self): return self
            async def __anext__(self): raise StopAsyncIteration
        return C()


class _Db:
    def __getitem__(self, name): return _Coll()
    def __getattr__(self, name): return _Coll()


def test_registry_frozen_at_eleven_implemented_zero_contract():
    from operational_intelligence import list_products, ProductStatus
    impl = [p for p in list_products() if p.status == ProductStatus.IMPLEMENTED]
    contract = [p for p in list_products()
                if p.status == ProductStatus.CONTRACT_REGISTERED]
    assert len(impl) == 11, sorted(p.product_id for p in impl)
    assert len(contract) == 0, sorted(p.product_id for p in contract)


def test_all_products_declare_valid_schedule_metadata():
    from operational_intelligence import list_products, ProductStatus
    for p in list_products():
        if p.status != ProductStatus.IMPLEMENTED:
            continue
        assert p.schedule_freq in {"weekly", "monthly", "daily"}, (p.product_id, p.schedule_freq)
        assert isinstance(p.schedule_hour_utc, int), (p.product_id, p.schedule_hour_utc)
        assert isinstance(p.schedule_iso_day, int), (p.product_id, p.schedule_iso_day)


def test_every_implemented_product_compose_renders_14_sections_on_empty_db():
    from operational_intelligence import list_products, compose, ProductStatus

    async def _go():
        for p in list_products():
            if p.status != ProductStatus.IMPLEMENTED:
                continue
            d = await compose(_Db(), product_id=p.product_id)
            keys = [s["section_key"] for s in d["sections"]]
            assert keys == REQUIRED_SECTION_KEYS, (p.product_id, keys)

    asyncio.run(_go())


def test_no_todo_fixme_mock_fake_in_engine():
    engine_dir = BE / "operational_intelligence"
    banned = ("TODO", "FIXME", "fake_data", "fake data", "fake_score")
    for f in engine_dir.glob("*.py"):
        t = f.read_text(encoding="utf-8")
        for b in banned:
            assert b.lower() not in t.lower(), f"{b} found in {f.name}"


def test_no_generic_ai_filler_language_in_aggregators():
    src = (BE / "operational_intelligence" / "products.py").read_text(
        encoding="utf-8")
    for banned in ("keep an eye on", "continue watching",
                   "keep watching", "keep watch",
                   "let's monitor", "will monitor closely"):
        assert banned not in src.lower(), (
            f"generic AI filler found: {banned!r}")


def test_single_recipient_module_in_engine():
    engine_dir = BE / "operational_intelligence"
    files = list(engine_dir.glob("recipients*.py"))
    assert len(files) == 1, [f.name for f in files]


def test_single_history_and_audit_collections():
    src = (BE / "operational_intelligence" / "engine.py").read_text(
        encoding="utf-8")
    # Exactly one COLLECTION_HISTORY / COLLECTION_AUDIT constant.
    assert src.count('COLLECTION_HISTORY = "operational_intelligence_history"') == 1
    assert src.count('COLLECTION_AUDIT = "operational_intelligence_audit"') == 1


def test_no_hr_or_user_account_mutations_in_recipient_ui():
    p = FE / "src/pages/admin/AdminOperationalIntelligenceRecipients.jsx"
    t = p.read_text(encoding="utf-8")
    banned = [
        'api.post("/hr/', 'api.patch("/hr/', 'api.put("/hr/', 'api.delete("/hr/',
        'api.post("/admin/employees', 'api.patch("/admin/employees',
        'api.post("/admin/directory', 'api.patch("/admin/directory',
        'api.delete("/admin/directory',
        'api.post("/employees',
    ]
    for b in banned:
        assert b not in t, f"HR/user mutation leaked: {b}"


def test_no_live_send_button_in_any_admin_page():
    """Neither the Cockpit nor the Recipient page may expose a
    live-send code path. `dry_run: false` is grep-banned."""
    for p in (FE / "src/pages/admin/AdminOperationalIntelligence.jsx",
              FE / "src/pages/admin/AdminOperationalIntelligenceRecipients.jsx"):
        t = p.read_text(encoding="utf-8")
        assert "dry_run: false" not in t.lower(), f"live-send leaked in {p.name}"


REQUIRED_DOCS = [
    "TRACK_19_50_EXECUTIVE_CERTIFICATION_REPORT.md",
    "TRACK_19_50_INDUSTRY_COMPARISON.md",
    "TRACK_19_50_FINAL_DEPLOYMENT_CHECKLIST.md",
    "TRACK_19_50_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_50_FINAL_QUALITY_GATE_REPORT.md",
    "TRACK_19_50_TEST_REPORT.md",
]


def test_all_track_19_50_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, missing


def test_prd_updated():
    assert "TRACK 19.50" in (MEM / "PRD.md").read_text(encoding="utf-8")


def test_changelog_updated():
    assert "TRACK 19.50" in (MEM / "CHANGELOG.md").read_text(encoding="utf-8")

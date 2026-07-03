"""Track 19.45B · Shop Intelligence + Corporate Intelligence · lock test.

Run isolated:
    pytest backend/tests/test_track_19_45b_shop_corporate_intelligence.py -q
"""
from __future__ import annotations

import asyncio
from pathlib import Path

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


# ---------------------------------------------------- fake DB harness ------
class _Coll:
    def __init__(self, rows=None):
        self.rows = list(rows or [])

    async def count_documents(self, q):
        return len(self.rows)

    def find(self, *a, **k):
        rows = self.rows

        class _Cur:
            def __init__(self, r): self.r = list(r)
            def limit(self, n): self.r = self.r[:n]; return self
            def sort(self, *a, **k): return self
            def __aiter__(self): self._it = iter(self.r); return self
            async def __anext__(self):
                try: return next(self._it)
                except StopIteration: raise StopAsyncIteration
        return _Cur(rows)

    def aggregate(self, pipeline):
        rows = self.rows

        class _Cur:
            def __init__(self, r): self.r = list(r)
            def __aiter__(self): self._it = iter(self.r); return self
            async def __anext__(self):
                try: return next(self._it)
                except StopIteration: raise StopAsyncIteration
        counts = {}
        for d in rows:
            k = d.get("job_number", "?")
            counts[k] = counts.get(k, 0) + 1
        return _Cur([{"_id": k, "count": v}
                     for k, v in sorted(counts.items(), key=lambda x: -x[1])[:5]])


class _Db:
    def __init__(self, seeded=None):
        self._c = {n: _Coll(v) for n, v in (seeded or {}).items()}

    def __getitem__(self, name):
        return self._c.setdefault(name, _Coll())


# ---------------------------------------------------- Shop Intelligence ----
def test_shop_intelligence_is_implemented():
    from operational_intelligence import list_products, ProductStatus
    p = next(x for x in list_products() if x.product_id == "shop_intelligence")
    assert p.status == ProductStatus.IMPLEMENTED
    assert p.permission_role == "safety_or_admin"
    assert p.aggregator is not None


def test_shop_insufficient_data_when_empty():
    from operational_intelligence import compose

    async def _go():
        d = await compose(_Db(), product_id="shop_intelligence")
        keys = [s["section_key"] for s in d["sections"]]
        assert keys == REQUIRED_SECTION_KEYS, keys
        sc = next(s for s in d["sections"]
                  if s["section_key"] == "operational_intelligence_score")
        assert sc["rows"]["Confidence"] == "insufficient_data"
        assert sc["rows"]["Attention Level"] == "CRITICAL"

    asyncio.run(_go())


def test_shop_score_with_real_signals():
    from operational_intelligence import compose

    db = _Db({
        "equipment_master": [{} for _ in range(15)],
        "equipment_units": [
            {"status": "OOS", "unit_number": f"U{i}",
             "oos_since": "2026-06-01", "make": "Cat", "model": "D6"}
            for i in range(2)
        ],
        "asset_holds": [
            {"hold_type": "safety", "status": "active",
             "unit_number": "U-SAFE", "reason": "lockout tag missing",
             "opened_at": "2026-07-01", "opened_by": "safety_rep"},
        ],
        "fleet_defects": [
            {"severity": "critical", "status": "open",
             "created_at": "2020-01-01", "unit_number": "U-AGE",
             "defect_title": "brake air loss",
             "assigned_to": "shop_mgr"},
            {"severity": "high", "status": "open",
             "created_at": "2026-07-01", "unit_number": "U2"},
        ],
        "maintainx_work_orders": [{"status": "open"} for _ in range(3)],
        "equipment_inspections": [{"submitted_at": "2026-07-01"}
                                  for _ in range(4)],
        "dvir": [{"has_open_defects": True}],
        "incident_cases": [
            {"incident_type": "equipment_damage",
             "submitted_at": "2026-07-01"},
        ],
        "equipment_transfers": [{"created_at": "2026-07-01"}],
    })

    async def _go():
        d = await compose(db, product_id="shop_intelligence")
        keys = [s["section_key"] for s in d["sections"]]
        assert keys == REQUIRED_SECTION_KEYS, keys
        sc = next(s for s in d["sections"]
                  if s["section_key"] == "operational_intelligence_score")
        assert sc["rows"]["Confidence"] in {"medium", "high"}
        # Top-5 must be a table when we seeded holds/defects/OOS
        top5 = next(s for s in d["sections"] if s["section_key"] == "top_5_items")
        assert top5["kind"] == "table"
        assert len(top5["rows"]) >= 1
        # Score must be below 100 since we seeded a safety hold + aging critical
        assert int(sc["rows"]["Overall Score"]) < 100

    asyncio.run(_go())


def test_shop_top5_preference_order():
    """Safety holds preferred over aging critical defects preferred over OOS."""
    from operational_intelligence import compose

    db_safety = _Db({
        "asset_holds": [
            {"hold_type": "safety", "status": "active",
             "unit_number": "U1", "reason": "test",
             "opened_at": "2026-07-01"},
        ],
        "fleet_defects": [
            {"severity": "critical", "status": "open",
             "created_at": "2020-01-01"},
        ],
        "equipment_units": [{"status": "OOS", "unit_number": "U2"}],
    })

    async def _go():
        d = await compose(db_safety, product_id="shop_intelligence")
        top5 = next(s for s in d["sections"] if s["section_key"] == "top_5_items")
        # The safety-hold reason must appear in the first row when safety
        # holds are present.
        row = top5["rows"][0]
        assert any("Safety hold" in str(c) for c in row), row

    asyncio.run(_go())


def test_shop_has_expected_deep_links():
    from operational_intelligence import compose

    async def _go():
        d = await compose(_Db(), product_id="shop_intelligence")
        dl = next(s for s in d["sections"] if s["section_key"] == "deep_links")
        hrefs = [it.get("href", "") for it in dl.get("items", [])
                 if isinstance(it, dict)]
        # Required domain-owner links per spec
        assert "/shop" in hrefs, hrefs
        assert "/fleet" in hrefs, hrefs
        assert "/fleet/holds" in hrefs, hrefs
        assert "/fleet/defects" in hrefs, hrefs
        assert any(h.startswith("/safety/cases") for h in hrefs), hrefs

    asyncio.run(_go())


def test_shop_no_auto_decision_notice_present():
    from operational_intelligence import compose

    async def _go():
        d = await compose(_Db(), product_id="shop_intelligence")
        notice = d.get("no_auto_decision_notice") or ""
        # Must explicitly refuse to determine mechanic/operator fault etc.
        for kw in ("mechanic", "operator", "preventability", "liability"):
            assert kw in notice.lower(), f"missing {kw}: {notice}"

    asyncio.run(_go())


# ---------------------------------------------------- Corporate Intelligence
def test_corporate_intelligence_is_implemented():
    from operational_intelligence import list_products, ProductStatus
    p = next(x for x in list_products() if x.product_id == "corporate_intelligence")
    assert p.status == ProductStatus.IMPLEMENTED
    assert p.permission_role == "admin_only"
    assert p.aggregator is not None


def test_corporate_insufficient_data_when_all_domains_empty():
    from operational_intelligence import compose

    async def _go():
        d = await compose(_Db(), product_id="corporate_intelligence")
        keys = [s["section_key"] for s in d["sections"]]
        assert keys == REQUIRED_SECTION_KEYS, keys
        sc = next(s for s in d["sections"]
                  if s["section_key"] == "operational_intelligence_score")
        # All domain digests will hit their own insufficient_data path
        # (empty DB); corporate rollup therefore also insufficient_data.
        assert sc["rows"]["Confidence"] == "insufficient_data"

    asyncio.run(_go())


def test_corporate_weighted_rollup_with_populated_domains():
    """Populate enough shop + fleet + hr + training + project data so
    multiple domains produce real scores. Corporate must return a
    weighted rollup with medium-or-high confidence."""
    from operational_intelligence import compose

    db = _Db({
        # shop signals
        "equipment_master": [{} for _ in range(15)],
        "asset_holds": [
            {"hold_type": "safety", "status": "active",
             "unit_number": "U1", "reason": "x", "opened_at": "2026-07-01"},
        ],
        "fleet_defects": [
            {"severity": "critical", "status": "open",
             "created_at": "2020-01-01"},
        ],
        # hr / training signals
        "employees": [{"active": True} for _ in range(25)],
        "safety_training_records": [{"completed_at": "2026-07-01"}
                                    for _ in range(8)],
        "driver_qualifications": [
            {"expires_at": "2020-01-01", "employee_name": "T",
             "employee_id": "E1", "cert_type": "OSHA-30"},
        ],
        "safety_meetings": [{"held_at": "2026-07-01"} for _ in range(2)],
        # project signals
        "jobs_master": [{"status": "active"} for _ in range(6)],
        "daily_reports": [{"submitted_at": "2026-07-01"} for _ in range(18)],
        "job_photos": [{"uploaded_at": "2026-07-01"} for _ in range(30)],
        # transportation
        "dvir": [{"has_open_defects": False}],
        "equipment_units": [{"status": "active"} for _ in range(5)],
        # po
        "po_requests": [{"status": "Submitted"} for _ in range(4)],
        # incidents
        "incident_cases": [
            {"submitted_at": "2026-07-01", "job_number": "J1"},
        ],
    })

    async def _go():
        d = await compose(db, product_id="corporate_intelligence")
        keys = [s["section_key"] for s in d["sections"]]
        assert keys == REQUIRED_SECTION_KEYS, keys
        sc = next(s for s in d["sections"]
                  if s["section_key"] == "operational_intelligence_score")
        assert sc["rows"]["Confidence"] in {"medium", "high"}
        # Overall score must be 0..100
        s_val = int(sc["rows"]["Overall Score"])
        assert 0 <= s_val <= 100
        # Top 5 (domain scores) must be a table with domain rows
        top5 = next(s for s in d["sections"] if s["section_key"] == "top_5_items")
        assert top5["kind"] == "table"
        assert len(top5["rows"]) >= 3
        # Executive Summary must expose "Domains scored"
        es = next(s for s in d["sections"]
                  if s["section_key"] == "executive_summary")
        assert "Domains scored" in es["rows"]

    asyncio.run(_go())


def test_corporate_weight_model_covers_every_implemented_product():
    """The weight table must include every IMPLEMENTED domain product."""
    from operational_intelligence import list_products, ProductStatus
    from operational_intelligence.products import CORPORATE_WEIGHTS
    implemented = {p.product_id for p in list_products()
                   if p.status == ProductStatus.IMPLEMENTED
                   and p.product_id != "corporate_intelligence"}
    missing = implemented - set(CORPORATE_WEIGHTS.keys())
    assert not missing, f"weight table missing: {missing}"
    assert sum(CORPORATE_WEIGHTS.values()) == 100, sum(CORPORATE_WEIGHTS.values())


def test_corporate_has_expected_deep_links():
    from operational_intelligence import compose

    async def _go():
        d = await compose(_Db(), product_id="corporate_intelligence")
        dl = next(s for s in d["sections"] if s["section_key"] == "deep_links")
        hrefs = [it.get("href", "") for it in dl.get("items", [])
                 if isinstance(it, dict)]
        for expected in ("/safety/cases", "/pm/projects", "/fleet", "/shop",
                         "/hr/employees", "/hr/training-records"):
            assert expected in hrefs, f"missing {expected} in {hrefs}"

    asyncio.run(_go())


def test_corporate_no_auto_decision_notice_present():
    from operational_intelligence import compose

    async def _go():
        d = await compose(_Db(), product_id="corporate_intelligence")
        notice = (d.get("no_auto_decision_notice") or "").lower()
        for kw in ("compliant", "legal", "liability", "discipline"):
            assert kw in notice, f"missing {kw}: {notice}"

    asyncio.run(_go())


# ---------------------------------------------------- Registry integrity ---
def test_registry_implemented_count_now_ten():
    from operational_intelligence import list_products, ProductStatus
    impl = {p.product_id for p in list_products()
            if p.status == ProductStatus.IMPLEMENTED}
    for expected in ("safety_morning_digest", "executive_operations_brief",
                     "po_weekly_digest", "transportation_intelligence",
                     "fleet_intelligence", "hr_intelligence",
                     "training_intelligence", "project_intelligence",
                     "shop_intelligence", "corporate_intelligence"):
        assert expected in impl, f"missing IMPLEMENTED: {expected}"
    assert len(impl) == 10, sorted(impl)


def test_registry_contract_registered_only_weekly_operations():
    from operational_intelligence import list_products, ProductStatus
    contract = {p.product_id for p in list_products()
                if p.status == ProductStatus.CONTRACT_REGISTERED}
    assert contract == {"weekly_operations_digest"}, contract


def test_registry_total_product_count_is_eleven():
    from operational_intelligence import list_products
    assert len(list_products()) == 11, [p.product_id for p in list_products()]


# ---------------------------------------------------- Zero-drift proof -----
def test_no_new_email_provider_or_scheduler_in_track_19_45b():
    engine_dir = BE / "operational_intelligence"
    banned = ("resend.emails.send", "sendgrid", "smtplib", "postmark",
              "APScheduler", "BackgroundScheduler", "AsyncIOScheduler",
              "CronTrigger")
    for f in engine_dir.glob("*.py"):
        t = f.read_text(encoding="utf-8")
        for b in banned:
            assert b not in t, f"drift in {f.name}: {b}"


def test_one_engine_only():
    """Only one recipient engine, one score model, one layout, one engine."""
    engine_dir = BE / "operational_intelligence"
    for required in ("engine.py", "registry.py", "recipients.py",
                     "score_model.py", "product_layout.py", "routes.py",
                     "products.py"):
        assert (engine_dir / required).exists(), required


# ---------------------------------------------------- Documentation --------
REQUIRED_DOCS = [
    "TRACK_19_45B_SHOP_INTELLIGENCE.md",
    "TRACK_19_45B_SHOP_DATA_SOURCE_MAP.md",
    "TRACK_19_45B_SHOP_SCORE_MODEL.md",
    "TRACK_19_45B_CORPORATE_INTELLIGENCE.md",
    "TRACK_19_45B_CORPORATE_DATA_SOURCE_MAP.md",
    "TRACK_19_45B_CORPORATE_SCORE_MODEL.md",
    "TRACK_19_45B_RECIPIENT_GOVERNANCE_MAP.md",
    "TRACK_19_45B_EMAIL_GOVERNANCE_CERTIFICATION.md",
    "TRACK_19_45B_PERMISSION_CERTIFICATION.md",
    "TRACK_19_45B_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_45B_TEST_REPORT.md",
]


def test_all_track_19_45b_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing docs: {missing}"


def test_zero_drift_matrix_covers_all_categories():
    text = (MEM / "TRACK_19_45B_ZERO_DRIFT_MATRIX.md").read_text(encoding="utf-8")
    for cat in ["Schemas", "Routes", "Emails", "Scheduler",
                "Recipients", "Audit", "Rollback"]:
        assert cat in text, f"ZDM missing category: {cat}"


def test_prd_updated():
    assert "TRACK 19.45B" in (MEM / "PRD.md").read_text(encoding="utf-8")


def test_changelog_updated():
    assert "TRACK 19.45B" in (MEM / "CHANGELOG.md").read_text(encoding="utf-8")

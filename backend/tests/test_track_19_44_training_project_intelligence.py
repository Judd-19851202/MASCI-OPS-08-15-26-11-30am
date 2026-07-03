"""Track 19.44 · Training Intelligence + Project Intelligence +
PO Digest cutover gate · lock test.

Run isolated:
    pytest backend/tests/test_track_19_44_training_project_intelligence.py -q
"""
from __future__ import annotations

import asyncio
import os
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


# --------------------------------------------------- fake DB harness


class _Coll:
    def __init__(self, rows=None):
        self.rows = list(rows or [])

    async def count_documents(self, q):
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

    def aggregate(self, pipeline):
        rows = self.rows

        class _Cur:
            def __init__(self, r): self.r = list(r)

            def __aiter__(self):
                self._it = iter(self.r)
                return self

            async def __anext__(self):
                try:
                    return next(self._it)
                except StopIteration:
                    raise StopAsyncIteration
        # Simple simulated aggregation — returns grouped counts by job_number
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


# --------------------------------------------------- Training Intelligence


def test_training_intelligence_is_implemented():
    from operational_intelligence import list_products, ProductStatus
    p = next(x for x in list_products() if x.product_id == "training_intelligence")
    assert p.status == ProductStatus.IMPLEMENTED
    assert p.permission_role == "admin_only"


def test_training_insufficient_data_when_empty():
    from operational_intelligence import compose

    async def _go():
        d = await compose(_Db(), product_id="training_intelligence")
        keys = [s["section_key"] for s in d["sections"]]
        assert keys == REQUIRED_SECTION_KEYS, keys
        sc = next(s for s in d["sections"]
                  if s["section_key"] == "operational_intelligence_score")
        assert sc["rows"]["Confidence"] == "insufficient_data"

    asyncio.run(_go())


def test_training_score_with_real_signals():
    from operational_intelligence import compose

    db = _Db({
        "employees": [{"active": True} for _ in range(25)],
        "safety_training_records": [{"completed_at": "2026-07-01"} for _ in range(10)],
        "training_track_records": [{"status": "missing"} for _ in range(3)],
        "driver_qualifications": [
            {"expires_at": "2020-01-01", "employee_name": "T1",
             "employee_id": "E1", "cert_type": "OSHA-30"},
        ],
        "safety_meetings": [{"held_at": "2026-07-01"} for _ in range(2)],
    })

    async def _go():
        d = await compose(db, product_id="training_intelligence")
        keys = [s["section_key"] for s in d["sections"]]
        assert keys == REQUIRED_SECTION_KEYS, keys
        sc = next(s for s in d["sections"]
                  if s["section_key"] == "operational_intelligence_score")
        assert sc["rows"]["Confidence"] in {"medium", "high"}
        top5 = next(s for s in d["sections"] if s["section_key"] == "top_5_items")
        assert top5["kind"] == "table"

    asyncio.run(_go())


def test_training_has_expected_deep_links():
    from operational_intelligence import compose

    async def _go():
        d = await compose(_Db(), product_id="training_intelligence")
        dl = next(s for s in d["sections"] if s["section_key"] == "deep_links")
        hrefs = [it.get("href", "") for it in dl.get("items", [])
                 if isinstance(it, dict)]
        assert any(h.startswith("/hr/training") for h in hrefs), hrefs

    asyncio.run(_go())


# --------------------------------------------------- Project Intelligence


def test_project_intelligence_is_implemented():
    from operational_intelligence import list_products, ProductStatus
    p = next(x for x in list_products() if x.product_id == "project_intelligence")
    assert p.status == ProductStatus.IMPLEMENTED
    assert p.permission_role == "admin_only"


def test_project_insufficient_data_when_empty():
    from operational_intelligence import compose

    async def _go():
        d = await compose(_Db(), product_id="project_intelligence")
        keys = [s["section_key"] for s in d["sections"]]
        assert keys == REQUIRED_SECTION_KEYS, keys
        sc = next(s for s in d["sections"]
                  if s["section_key"] == "operational_intelligence_score")
        assert sc["rows"]["Confidence"] == "insufficient_data"

    asyncio.run(_go())


def test_project_score_with_real_signals():
    from operational_intelligence import compose
    db = _Db({
        "jobs_master": [{"status": "active"} for _ in range(6)],
        "daily_reports": [{"submitted_at": "2026-07-01"} for _ in range(18)],
        "job_photos": [{"uploaded_at": "2026-07-01"} for _ in range(30)],
        "operational_constraints": [{"status": "open",
                                     "opened_at": "2020-01-01"}
                                    for _ in range(3)],
        "incident_cases": [
            {"submitted_at": "2026-07-01", "job_number": "J1"},
            {"submitted_at": "2026-07-01", "job_number": "J1"},
            {"submitted_at": "2026-07-01", "job_number": "J2"},
        ],
        "po_requests": [{"status": "Submitted"} for _ in range(12)],
    })

    async def _go():
        d = await compose(db, product_id="project_intelligence")
        keys = [s["section_key"] for s in d["sections"]]
        assert keys == REQUIRED_SECTION_KEYS, keys
        sc = next(s for s in d["sections"]
                  if s["section_key"] == "operational_intelligence_score")
        assert sc["rows"]["Confidence"] in {"medium", "high"}

    asyncio.run(_go())


def test_project_has_expected_deep_links():
    from operational_intelligence import compose

    async def _go():
        d = await compose(_Db(), product_id="project_intelligence")
        dl = next(s for s in d["sections"] if s["section_key"] == "deep_links")
        hrefs = [it.get("href", "") for it in dl.get("items", [])
                 if isinstance(it, dict)]
        assert any(h.startswith("/pm") for h in hrefs), hrefs

    asyncio.run(_go())


# --------------------------------------------------- PO cutover gate


def test_po_cutover_gate_disables_legacy_when_flag_set():
    import po_digest as pd
    prev_live = os.environ.get("OI_ENGINE_PO_WEEKLY_LIVE")
    prev_enabled = os.environ.get("PO_DIGEST_ENABLED")
    try:
        os.environ["OI_ENGINE_PO_WEEKLY_LIVE"] = "true"
        os.environ["PO_DIGEST_ENABLED"] = "true"
        assert pd._enabled() is False, (
            "PO cutover gate did not disable legacy cron."
        )
        os.environ["OI_ENGINE_PO_WEEKLY_LIVE"] = "false"
        assert pd._enabled() is True
    finally:
        if prev_live is None:
            os.environ.pop("OI_ENGINE_PO_WEEKLY_LIVE", None)
        else:
            os.environ["OI_ENGINE_PO_WEEKLY_LIVE"] = prev_live
        if prev_enabled is None:
            os.environ.pop("PO_DIGEST_ENABLED", None)
        else:
            os.environ["PO_DIGEST_ENABLED"] = prev_enabled


def test_legacy_po_digest_module_still_present():
    import po_digest
    assert hasattr(po_digest, "po_digest_scheduler_loop")
    assert hasattr(po_digest, "_enabled")


# --------------------------------------------------- registry integrity


def test_registry_implemented_count_now_eight():
    from operational_intelligence import list_products, ProductStatus
    impl = {p.product_id for p in list_products()
            if p.status == ProductStatus.IMPLEMENTED}
    for expected in ("safety_morning_digest", "executive_operations_brief",
                     "po_weekly_digest", "transportation_intelligence",
                     "fleet_intelligence", "hr_intelligence",
                     "training_intelligence", "project_intelligence"):
        assert expected in impl, f"missing IMPLEMENTED: {expected}"


def test_registry_contract_registered_count_now_three():
    from operational_intelligence import list_products, ProductStatus
    contract = {p.product_id for p in list_products()
                if p.status == ProductStatus.CONTRACT_REGISTERED}
    assert contract == {
        "weekly_operations_digest", "shop_intelligence",
        "corporate_intelligence",
    }, contract


def test_no_new_email_provider_or_scheduler_in_track_19_44():
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
    "TRACK_19_44_TRAINING_INTELLIGENCE.md",
    "TRACK_19_44_TRAINING_DATA_SOURCE_MAP.md",
    "TRACK_19_44_TRAINING_SCORE_MODEL.md",
    "TRACK_19_44_PROJECT_INTELLIGENCE.md",
    "TRACK_19_44_PROJECT_DATA_SOURCE_MAP.md",
    "TRACK_19_44_PROJECT_SCORE_MODEL.md",
    "TRACK_19_44_PO_DIGEST_CUTOVER_GATE.md",
    "TRACK_19_44_SAFETY_DIGEST_CUTOVER_VERIFICATION.md",
    "TRACK_19_44_EMAIL_GOVERNANCE_CERTIFICATION.md",
    "TRACK_19_44_PERMISSION_CERTIFICATION.md",
    "TRACK_19_44_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_44_TEST_REPORT.md",
]


def test_all_track_19_44_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing docs: {missing}"


def test_zero_drift_matrix_covers_all_categories():
    text = (MEM / "TRACK_19_44_ZERO_DRIFT_MATRIX.md").read_text(encoding="utf-8")
    for cat in ["Schemas", "Routes", "Emails", "Scheduler",
                "Recipients", "Audit", "Rollback"]:
        assert cat in text, f"ZDM missing category: {cat}"


def test_prd_updated():
    assert "TRACK 19.44" in (MEM / "PRD.md").read_text(encoding="utf-8")


def test_changelog_updated():
    assert "TRACK 19.44" in (MEM / "CHANGELOG.md").read_text(encoding="utf-8")

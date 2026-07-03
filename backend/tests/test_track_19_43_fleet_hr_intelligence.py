"""Track 19.43 · Fleet Intelligence + HR Intelligence + Legacy Safety
Digest Cutover Gate · lock test.

Locks:
- Fleet Intelligence and HR Intelligence graduated to IMPLEMENTED.
- Both render the 14-section standard layout.
- Both compute a Score model (with insufficient-data guard).
- Deep links resolve to real routes.
- Track 19.40 registry: exactly 5 CONTRACT_REGISTERED remaining
  (weekly_operations · training · project · shop · corporate).
- Safety Digest cutover gate: `OI_ENGINE_SAFETY_MORNING_LIVE=true`
  forces the legacy cron `_enabled()` to return False even when
  `SAFETY_DIGEST_ENABLED=true`.
- Track 19.39/19.40/19.41/19.42 invariants preserved.
- 10 required docs + PRD + CHANGELOG.

Run isolated:
    pytest backend/tests/test_track_19_43_fleet_hr_intelligence.py -q
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


# ---------------------------------------------------- fake DB harness


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


class _Db:
    def __init__(self, seeded=None):
        self._c = {n: _Coll(v) for n, v in (seeded or {}).items()}

    def __getitem__(self, name):
        return self._c.setdefault(name, _Coll())


# --------------------------------------------------- Fleet Intelligence


def test_fleet_intelligence_is_implemented():
    from operational_intelligence import list_products, ProductStatus
    p = next(x for x in list_products() if x.product_id == "fleet_intelligence")
    assert p.status == ProductStatus.IMPLEMENTED
    assert p.permission_role == "safety_or_admin"
    assert callable(p.aggregator)


def test_fleet_insufficient_data_when_empty():
    from operational_intelligence import compose

    async def _go():
        d = await compose(_Db(), product_id="fleet_intelligence")
        keys = [s["section_key"] for s in d["sections"]]
        assert keys == REQUIRED_SECTION_KEYS, keys
        sc = next(s for s in d["sections"]
                  if s["section_key"] == "operational_intelligence_score")
        assert sc["rows"]["Confidence"] == "insufficient_data"
        assert sc["rows"]["Attention Level"] == "CRITICAL"

    asyncio.run(_go())


def test_fleet_score_with_real_signals():
    from operational_intelligence import compose

    db = _Db({
        "equipment_master": [{} for _ in range(25)],
        "equipment_units": [{"status": "OOS"} for _ in range(3)],
        "asset_holds": [{"hold_type": "safety", "status": "active",
                          "unit_number": f"U{i}", "reason": "Test",
                          "opened_at": "2026-07-01", "opened_by": "safety"}
                         for i in range(2)],
        "fleet_defects": [{"severity": "critical", "status": "open"}
                           for _ in range(1)],
        "equipment_inspections": [{} for _ in range(8)],
        "equipment_transfers": [{} for _ in range(2)],
        "incident_cases": [],
    })

    async def _go():
        d = await compose(db, product_id="fleet_intelligence")
        keys = [s["section_key"] for s in d["sections"]]
        assert keys == REQUIRED_SECTION_KEYS, keys
        sc = next(s for s in d["sections"]
                  if s["section_key"] == "operational_intelligence_score")
        assert sc["rows"]["Confidence"] in {"medium", "high"}
        assert isinstance(sc["rows"]["Overall Score"], int)
        # Top-5 items table should be populated from asset_holds
        top5 = next(s for s in d["sections"] if s["section_key"] == "top_5_items")
        assert top5["kind"] == "table"

    asyncio.run(_go())


def test_fleet_has_expected_deep_links():
    from operational_intelligence import compose

    async def _go():
        d = await compose(_Db(), product_id="fleet_intelligence")
        dl = next(s for s in d["sections"] if s["section_key"] == "deep_links")
        hrefs = [it.get("href", "") for it in dl.get("items", [])
                 if isinstance(it, dict)]
        assert any(h.startswith("/fleet") for h in hrefs), hrefs

    asyncio.run(_go())


# --------------------------------------------------- HR Intelligence


def test_hr_intelligence_is_implemented():
    from operational_intelligence import list_products, ProductStatus
    p = next(x for x in list_products() if x.product_id == "hr_intelligence")
    assert p.status == ProductStatus.IMPLEMENTED
    assert p.permission_role == "admin_only"
    assert callable(p.aggregator)


def test_hr_insufficient_data_when_empty():
    from operational_intelligence import compose

    async def _go():
        d = await compose(_Db(), product_id="hr_intelligence")
        keys = [s["section_key"] for s in d["sections"]]
        assert keys == REQUIRED_SECTION_KEYS, keys
        sc = next(s for s in d["sections"]
                  if s["section_key"] == "operational_intelligence_score")
        assert sc["rows"]["Confidence"] == "insufficient_data"

    asyncio.run(_go())


def test_hr_score_with_real_signals():
    from operational_intelligence import compose
    db = _Db({
        "employees": [{"active": True} for _ in range(30)],
        "employee_lifecycle_events": [{"event_type": "hired"} for _ in range(2)],
        "driver_qualifications": [
            {"expires_at": "2020-01-01", "employee_name": "Test One",
             "employee_id": "E1", "cert_type": "OSHA-30"},
            {"expires_at": "2020-01-01", "employee_name": "Test Two",
             "employee_id": "E2", "cert_type": "CDL-A"},
        ],
        "training_hits": [{} for _ in range(5)],
    })

    async def _go():
        d = await compose(db, product_id="hr_intelligence")
        keys = [s["section_key"] for s in d["sections"]]
        assert keys == REQUIRED_SECTION_KEYS, keys
        sc = next(s for s in d["sections"]
                  if s["section_key"] == "operational_intelligence_score")
        assert isinstance(sc["rows"]["Overall Score"], int)
        # Top-5 items table should be populated from expired qualifications
        top5 = next(s for s in d["sections"] if s["section_key"] == "top_5_items")
        assert top5["kind"] == "table"

    asyncio.run(_go())


def test_hr_has_expected_deep_links():
    from operational_intelligence import compose

    async def _go():
        d = await compose(_Db(), product_id="hr_intelligence")
        dl = next(s for s in d["sections"] if s["section_key"] == "deep_links")
        hrefs = [it.get("href", "") for it in dl.get("items", [])
                 if isinstance(it, dict)]
        assert any(h.startswith("/hr") for h in hrefs), hrefs

    asyncio.run(_go())


# --------------------------------------------------- Legacy safety_digest cutover


def test_cutover_gate_disables_legacy_safety_digest():
    """When `OI_ENGINE_SAFETY_MORNING_LIVE=true`, legacy `_enabled()`
    must return False even if `SAFETY_DIGEST_ENABLED=true`."""
    import safety_digest as sd
    prev_live = os.environ.get("OI_ENGINE_SAFETY_MORNING_LIVE")
    prev_enabled = os.environ.get("SAFETY_DIGEST_ENABLED")
    try:
        os.environ["OI_ENGINE_SAFETY_MORNING_LIVE"] = "true"
        os.environ["SAFETY_DIGEST_ENABLED"] = "true"
        assert sd._enabled() is False, (
            "Cutover gate did not disable legacy safety_digest cron."
        )
        # Disable the gate → legacy remains enabled per its own toggle.
        os.environ["OI_ENGINE_SAFETY_MORNING_LIVE"] = "false"
        assert sd._enabled() is True
    finally:
        # Restore env
        if prev_live is None:
            os.environ.pop("OI_ENGINE_SAFETY_MORNING_LIVE", None)
        else:
            os.environ["OI_ENGINE_SAFETY_MORNING_LIVE"] = prev_live
        if prev_enabled is None:
            os.environ.pop("SAFETY_DIGEST_ENABLED", None)
        else:
            os.environ["SAFETY_DIGEST_ENABLED"] = prev_enabled


def test_legacy_safety_digest_module_still_present():
    """Zero-drift: module preserved for rollback confidence."""
    import safety_digest
    assert hasattr(safety_digest, "safety_digest_scheduler_loop")
    assert hasattr(safety_digest, "_enabled")


# --------------------------------------------------- registry integrity


def test_registry_contract_registered_count_now_five():
    from operational_intelligence import list_products, ProductStatus
    contract = [p for p in list_products()
                if p.status == ProductStatus.CONTRACT_REGISTERED]
    ids = {p.product_id for p in contract}
    assert ids == {
        "weekly_operations_digest", "training_intelligence",
        "project_intelligence", "shop_intelligence",
        "corporate_intelligence",
    }, ids


def test_registry_implemented_count_now_six():
    from operational_intelligence import list_products, ProductStatus
    impl = {p.product_id for p in list_products()
            if p.status == ProductStatus.IMPLEMENTED}
    for expected in ("safety_morning_digest", "executive_operations_brief",
                     "po_weekly_digest", "transportation_intelligence",
                     "fleet_intelligence", "hr_intelligence"):
        assert expected in impl, f"missing IMPLEMENTED: {expected}"


def test_no_new_email_provider_or_scheduler_in_track_19_43():
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
    "TRACK_19_43_FLEET_INTELLIGENCE.md",
    "TRACK_19_43_FLEET_DATA_SOURCE_MAP.md",
    "TRACK_19_43_FLEET_SCORE_MODEL.md",
    "TRACK_19_43_HR_INTELLIGENCE.md",
    "TRACK_19_43_HR_DATA_SOURCE_MAP.md",
    "TRACK_19_43_HR_SCORE_MODEL.md",
    "TRACK_19_43_LEGACY_SAFETY_DIGEST_CUTOVER.md",
    "TRACK_19_43_PERMISSION_CERTIFICATION.md",
    "TRACK_19_43_ZERO_DRIFT_MATRIX.md",
    "TRACK_19_43_TEST_REPORT.md",
]


def test_all_track_19_43_docs_present():
    missing = [d for d in REQUIRED_DOCS if not (MEM / d).exists()]
    assert not missing, f"missing docs: {missing}"


def test_zero_drift_matrix_covers_all_categories():
    text = (MEM / "TRACK_19_43_ZERO_DRIFT_MATRIX.md").read_text(encoding="utf-8")
    for cat in ["Schemas", "Routes", "Emails", "Scheduler",
                "Recipients", "Audit", "Rollback"]:
        assert cat in text, f"ZDM missing category: {cat}"


def test_prd_updated():
    assert "TRACK 19.43" in (MEM / "PRD.md").read_text(encoding="utf-8")


def test_changelog_updated():
    assert "TRACK 19.43" in (MEM / "CHANGELOG.md").read_text(encoding="utf-8")

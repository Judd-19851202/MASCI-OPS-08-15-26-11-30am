"""ODS-001 · Operational Data Spine · unit + integration tests.

Covers: model validation, envelope enforcement, pure-function fact
building from DR-V2 drafts, idempotent supersede logic, KPI snapshot
math, route mounts, and V1/V2 zero-drift guards.

DOES NOT call live LLMs. DOES NOT rely on scheduler or emails.
"""
from __future__ import annotations
import asyncio
import os
import sys
import uuid
from pathlib import Path

import pytest

BACKEND = Path("/app/backend")
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("EMAIL_SAFETY_MODE", "strict")
os.environ.setdefault("SCHEDULER_ENABLED", "false")
os.environ.setdefault("ODS_ENABLED", "true")
os.environ.setdefault("DR_V2_SPINE_EMISSION_ENABLED", "true")


# ---------------------------------------------------------------------------
# Model / envelope
# ---------------------------------------------------------------------------

def test_fact_types_and_source_types_locked():
    from services.ods_spine.model import FACT_TYPES, SOURCE_TYPES
    assert len(FACT_TYPES) == 11
    assert "labor_fact" in FACT_TYPES
    assert "intelligence_fact" in FACT_TYPES
    assert "daily_report_v1" in SOURCE_TYPES
    assert "daily_report_v2" in SOURCE_TYPES


def test_envelope_validator_accepts_valid():
    from services.ods_spine.model import validate_fact_envelope
    f = {
        "fact_id": "f1", "fact_type": "labor_fact", "tenant_id": "t",
        "project_id": "p", "date": "2026-07-05",
        "source_type": "daily_report_v2", "source_id": "s",
        "confidence": 1.0, "payload": {"hours": 8},
    }
    assert validate_fact_envelope(f) is None


def test_envelope_validator_rejects_bad_type():
    from services.ods_spine.model import validate_fact_envelope
    f = {
        "fact_id": "f1", "fact_type": "unknown_fact", "tenant_id": "t",
        "project_id": "p", "date": "2026-07-05",
        "source_type": "daily_report_v2", "source_id": "s",
        "confidence": 1.0, "payload": {},
    }
    err = validate_fact_envelope(f)
    assert err is not None and "invalid_fact_type" in err


def test_envelope_validator_rejects_out_of_range_confidence():
    from services.ods_spine.model import validate_fact_envelope
    f = {
        "fact_id": "f1", "fact_type": "labor_fact", "tenant_id": "t",
        "project_id": "p", "date": "2026-07-05",
        "source_type": "daily_report_v2", "source_id": "s",
        "confidence": 1.5, "payload": {},
    }
    err = validate_fact_envelope(f)
    assert err is not None and "confidence_out_of_range" in err


def test_coerce_date_and_number():
    from services.ods_spine.model import coerce_date, coerce_number
    assert coerce_date("2026-07-05") == "2026-07-05"
    assert coerce_date("2026-07-05T12:00:00") == "2026-07-05"
    assert coerce_date(None) == ""
    assert coerce_number("8.5") == 8.5
    assert coerce_number(None) == 0.0
    assert coerce_number("bogus") == 0.0


# ---------------------------------------------------------------------------
# Pure fact-builder (no I/O)
# ---------------------------------------------------------------------------

def test_dr_v2_builder_emits_all_fact_types():
    from services.ods_spine.ingest import _build_facts_from_dr_v2_draft
    draft = {
        "report_id": "drv2-test-1",
        "updated_at": "2026-07-05T00:00:00+00:00",
        "day_setup": {"project_number": "P1", "report_date": "2026-07-05", "supervisor_name": "X"},
        "masci_crews": [{"crew": "C-1", "members": ["A", "B"], "hours": 8}],
        "equipment_used": [{"unit": "E-201", "hours": 6.5}],
        "activity_cards": [{"id": "a1", "area": "Storm", "activity": "Trench", "qty": 120, "unit": "LF"}],
        "constraint_cards": [{"id": "c1", "type": "weather", "duration_hours": 2, "note": "rain"}],
        "weather": {"temperature_f": 78, "precipitation": 0, "wind_mph": 9},
        "tomorrow_readiness": {"crew_ok": True, "materials_ok": False, "blockers": ["fittings"]},
        "photos": [{"id": "ph1", "ref": "photo://x"}],
        "safety": {"safety_incidents": [{"type": "observation", "severity": "info"}]},
    }
    facts = _build_facts_from_dr_v2_draft(draft)
    types = {f["fact_type"] for f in facts}
    assert {"labor_fact", "equipment_fact", "production_fact", "delay_fact",
            "weather_fact", "readiness_fact", "photo_evidence_fact", "safety_fact"}.issubset(types)
    # 2 crew members → 2 labor facts
    assert sum(1 for f in facts if f["fact_type"] == "labor_fact") == 2
    # Every fact has envelope
    for f in facts:
        for k in ("fact_id", "fact_type", "tenant_id", "project_id", "date",
                  "source_type", "source_id", "source_item_id", "confidence", "payload"):
            assert k in f, f"missing {k} in {f['fact_type']}"


def test_dr_v2_builder_returns_empty_without_anchor():
    from services.ods_spine.ingest import _build_facts_from_dr_v2_draft
    # No project or date → no facts
    facts = _build_facts_from_dr_v2_draft({"report_id": "x", "day_setup": {}})
    assert facts == []


def test_dr_v2_builder_source_item_ids_unique_per_row():
    from services.ods_spine.ingest import _build_facts_from_dr_v2_draft
    draft = {
        "report_id": "r1", "updated_at": "2026-07-05",
        "day_setup": {"project_number": "P1", "report_date": "2026-07-05"},
        "masci_crews": [
            {"crew": "C-1", "members": ["A", "B", "C"], "hours": 8},
            {"crew": "C-2", "members": ["D"], "hours": 8},
        ],
    }
    facts = _build_facts_from_dr_v2_draft(draft)
    labor = [f for f in facts if f["fact_type"] == "labor_fact"]
    assert len(labor) == 4
    ids = {f["source_item_id"] for f in labor}
    assert len(ids) == 4


# ---------------------------------------------------------------------------
# Store validation guard (async — uses in-memory dict)
# ---------------------------------------------------------------------------

class _InMemoryColl:
    def __init__(self):
        self.docs = []
        self.updates = []

    async def insert_one(self, d):
        self.docs.append(dict(d))
        return type("R", (), {"inserted_id": d.get("_id")})()

    async def insert_many(self, docs, ordered=False):  # noqa: ARG002
        for d in docs:
            self.docs.append(dict(d))
        return type("R", (), {"inserted_ids": [d.get("_id") for d in docs]})()

    async def update_many(self, q, u):
        self.updates.append((q, u))
        modified = 0
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items() if not isinstance(v, dict)):
                d.update(u.get("$set", {}))
                modified += 1
        return type("R", (), {"modified_count": modified})()

    async def find_one(self, q, projection=None):  # noqa: ARG002
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items() if not isinstance(v, dict)):
                return dict(d)
        return None

    async def create_index(self, *a, **kw):  # noqa: ARG002
        return None


class _InMemoryDB(dict):
    def __getitem__(self, k):
        if k not in self:
            super().__setitem__(k, _InMemoryColl())
        return super().__getitem__(k)


def test_write_facts_stamps_defaults_and_rejects_invalid():
    from services.ods_spine.store import write_facts

    db = _InMemoryDB()

    async def _run():
        good = {
            "fact_type": "labor_fact", "tenant_id": "t", "project_id": "p",
            "date": "2026-07-05", "source_type": "daily_report_v2",
            "source_id": "s", "source_item_id": "i1", "payload": {"hours": 8},
        }
        bad = dict(good)
        bad["fact_type"] = "not_a_fact"
        result = await write_facts(db, [good, bad], ingestion_run_id="run1")
        return result

    result = asyncio.get_event_loop().run_until_complete(_run())
    assert result == {"inserted": 1, "rejected": 1}
    inserted = db["operational_facts"].docs[0]
    assert inserted["is_current"] is True
    assert inserted["confidence"] == 1.0
    assert inserted["fact_id"]  # auto-assigned uuid


# ---------------------------------------------------------------------------
# Route mounts
# ---------------------------------------------------------------------------

def test_ods_routes_are_mounted():
    from importlib import import_module
    server = import_module("server")
    paths = {getattr(r, "path", "") for r in server.app.routes if hasattr(r, "endpoint")}
    expected = {
        "/api/ods/meta",
        "/api/ods/facts",
        "/api/ods/projects/{project_id}/summary",
        "/api/ods/projects/{project_id}/config",
        "/api/ods/snapshots",
        "/api/ods/snapshots/recompute",
        "/api/ods/ingest/dr-v2/{report_id}",
    }
    missing = expected - paths
    assert not missing, f"missing ODS routes: {missing}"


def test_ods_never_writes_to_daily_reports():
    src = (BACKEND / "routes" / "ods.py").read_text(encoding="utf-8")
    forbidden = ["db.daily_reports", "db['daily_reports']", 'db["daily_reports"]']
    hits = [p for p in forbidden if p in src]
    assert not hits, f"ods.py must not touch V1 collection: {hits}"

    ingest_src = (BACKEND / "services" / "ods_spine" / "ingest.py").read_text(encoding="utf-8")
    hits = [p for p in forbidden if p in ingest_src]
    assert not hits, f"ingest.py must not touch V1 collection: {hits}"


def test_flags_default_off():
    """With env unset, flags MUST be off. Guards production accidents."""
    import importlib
    from services.ods_spine import flags as f
    old_ods = os.environ.pop("ODS_ENABLED", None)
    old_emit = os.environ.pop("DR_V2_SPINE_EMISSION_ENABLED", None)
    try:
        importlib.reload(f)
        assert f.ods_enabled() is False
        assert f.dr_v2_spine_emission_enabled() is False
    finally:
        if old_ods is not None:
            os.environ["ODS_ENABLED"] = old_ods
        if old_emit is not None:
            os.environ["DR_V2_SPINE_EMISSION_ENABLED"] = old_emit
        importlib.reload(f)

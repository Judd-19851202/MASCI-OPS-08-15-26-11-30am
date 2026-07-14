"""
DR-CUTOVER-001 — V1 → ODS wiring lock envelope

Enforces that:
  1. `ingest_dr_v1_report` builds the expected fact shape from V1 daily_reports.
  2. Idempotency holds: re-running supersedes rather than duplicating.
  3. The V1 submit hook path exists (grep on daily_reports.py).
  4. Source type is `daily_report` (valid per model.SOURCE_TYPES).
  5. Backfill script exists and has --dry-run + --live modes.

All tests use in-memory fake collections. No live DB required.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

import pytest


# Force flags ON for the process so `ingest_dr_v1_report` doesn't early-return.
os.environ["ODS_ENABLED"] = "1"
os.environ["DR_V2_SPINE_EMISSION_ENABLED"] = "1"

from services.ods_spine.ingest import (
    _build_facts_from_dr_v1_report,
    _v1_yesno,
    ingest_dr_v1_report,
)


def _v1_doc(**overrides: Any) -> Dict[str, Any]:
    base = {
        "id": "dr-v1-lock-1",
        "project_number": "20-07",
        "project_name": "SR-826 Interchange",
        "location": "Bent 3 Cap",
        "report_date": "2026-04-25",
        "prepared_by": "Chris Wright",
        "created_at": "2026-04-25T18:00:00+00:00",
        "masci_crews": [
            {"trade": "Concrete", "foreman": "Foreman A", "count": 8, "hours": 9.0,
             "work_performed": "Bent 3 cap pour"}
        ],
        "equipment": [{"unit": "P-104", "hours": 6.0, "operator": "Op-1"}],
        "activities": [],
        "materials": [{"material": "Concrete", "quantity": 60, "unit": "cy", "supplier": "CEMEX"}],
        "photos": [{"key": "p1"}, {"key": "p2"}],
        "weather_snapshots": [{"time": "06:00", "condition": "Clear", "temp_f": 76, "wind_mph": 4}],
        "weather_summary": "Sunny",
        "weather_impact": "No",
        "schedule_delays": "Yes",
        "schedule_delays_notes": "Late crane 2h",
        "safety_incidents_today": "No",
        "injuries_reported": "No",
        "incident_notes": "",
        "subcontractors": [{"company": "SubX", "trade": "Rebar", "count": 4, "hours": 8.0}],
    }
    base.update(overrides)
    return base


# ─────────────────────────────── BUILDER ──────────────────────────────

def test_v1_builder_emits_labor_fact_with_labor_hours_multiplied_by_count():
    facts = _build_facts_from_dr_v1_report(_v1_doc())
    labor = [f for f in facts if f["fact_type"] == "labor_fact"]
    assert labor, "expected at least one labor_fact"
    # Crew of 8 × 9h = 72 labor_hours in payload.
    crew_row = next(f for f in labor if f["payload"].get("role") == "Concrete")
    assert crew_row["payload"]["labor_hours"] == 72.0
    assert crew_row["payload"]["crew_size"] == 8
    assert crew_row["payload"]["hours"] == 9.0


def test_v1_builder_emits_labor_fact_for_subcontractors():
    facts = _build_facts_from_dr_v1_report(_v1_doc())
    subs = [f for f in facts if f["fact_type"] == "labor_fact"
            and f["payload"].get("company") == "SubX"]
    assert len(subs) == 1
    assert subs[0]["payload"]["labor_hours"] == 32.0  # 4 × 8h


def test_v1_builder_emits_equipment_fact():
    facts = _build_facts_from_dr_v1_report(_v1_doc())
    eq = [f for f in facts if f["fact_type"] == "equipment_fact"]
    assert len(eq) == 1
    assert eq[0]["payload"]["equipment_label"] == "P-104"
    assert eq[0]["payload"]["hours_used"] == 6.0


def test_v1_builder_emits_weather_fact_from_snapshots():
    facts = _build_facts_from_dr_v1_report(_v1_doc())
    w = [f for f in facts if f["fact_type"] == "weather_fact"]
    assert len(w) == 1
    assert w[0]["payload"]["temperature_f"] == 76
    assert w[0]["payload"]["condition"] == "Clear"


def test_v1_builder_emits_delay_fact_for_schedule_delays():
    facts = _build_facts_from_dr_v1_report(_v1_doc())
    delays = [f for f in facts if f["fact_type"] == "delay_fact"]
    assert any(d["payload"]["delay_category"] == "schedule" for d in delays)


def test_v1_builder_emits_safety_fact_when_incident_reported():
    doc = _v1_doc(safety_incidents_today="Yes", injuries_reported="No",
                  incident_notes="Bee sting to laborer L2 — first aid")
    facts = _build_facts_from_dr_v1_report(doc)
    safety = [f for f in facts if f["fact_type"] == "safety_fact"]
    assert len(safety) == 1
    assert safety[0]["payload"]["safety_incident_reported"] is True
    assert "bee sting" in safety[0]["payload"]["narrative"].lower()


def test_v1_builder_emits_photo_evidence_facts():
    facts = _build_facts_from_dr_v1_report(_v1_doc())
    photos = [f for f in facts if f["fact_type"] == "photo_evidence_fact"]
    assert len(photos) == 2


def test_v1_builder_emits_material_facts():
    facts = _build_facts_from_dr_v1_report(_v1_doc())
    mats = [f for f in facts if f["fact_type"] == "material_fact"]
    assert len(mats) == 1
    assert mats[0]["payload"]["material"] == "Concrete"
    assert mats[0]["payload"]["quantity"] == 60


def test_v1_builder_uses_source_type_daily_report():
    facts = _build_facts_from_dr_v1_report(_v1_doc())
    assert all(f["source_type"] == "daily_report" for f in facts)


def test_v1_builder_returns_empty_when_missing_project_or_date():
    doc = _v1_doc(project_number="", project_name="", report_date="")
    facts = _build_facts_from_dr_v1_report(doc)
    assert facts == []


def test_v1_yesno_helper():
    assert _v1_yesno("Yes") is True
    assert _v1_yesno("YES") is True
    assert _v1_yesno("yes") is True
    assert _v1_yesno("No") is False
    assert _v1_yesno("") is False
    assert _v1_yesno(None) is False
    assert _v1_yesno(True) is True


# ───────────────────────────── IDEMPOTENCY ────────────────────────────

class _Coll:
    def __init__(self, name="?"):
        self.rows: List[Dict[str, Any]] = []
        self._name = name

    async def insert_many(self, docs, ordered=False):
        for d in docs:
            self.rows.append(dict(d))

    async def insert_one(self, doc):
        self.rows.append(dict(doc))

    async def update_many(self, q, update):
        matches = [r for r in self.rows if all(r.get(k) == v for k, v in q.items() if not isinstance(v, dict))]
        # handle {"is_current": True} etc.
        for r in matches:
            if "$set" in update:
                r.update(update["$set"])
        class _R:
            modified_count = len(matches)
        return _R()

    async def update_one(self, q, update, upsert=False):
        for r in self.rows:
            if all(r.get(k) == v for k, v in q.items()):
                if "$set" in update:
                    r.update(update["$set"])
                return
        if upsert and "$set" in update:
            self.rows.append({**q, **update["$set"]})

    async def find_one(self, q, projection=None):
        for r in self.rows:
            if all(r.get(k) == v for k, v in q.items()):
                return dict(r)
        return None

    def find(self, q=None, projection=None):
        q = q or {}
        matched = []
        for r in self.rows:
            ok = True
            for k, v in q.items():
                if isinstance(v, dict) and "$in" in v:
                    if r.get(k) not in v["$in"]:
                        ok = False; break
                elif r.get(k) != v:
                    ok = False; break
            if ok:
                matched.append(dict(r))
        class _C:
            def __init__(self, rows): self._rows = rows
            def sort(self, *_a, **_k): return self
            def limit(self, *_a, **_k): return self
            def __aiter__(self): self._i = iter(self._rows); return self
            async def __anext__(self):
                try: return next(self._i)
                except StopIteration: raise StopAsyncIteration
        return _C(matched)


class _DB:
    def __init__(self):
        self.operational_facts = _Coll("operational_facts")
        self.operational_ingestion_runs = _Coll("operational_ingestion_runs")

    def __getitem__(self, name):
        return getattr(self, name)


@pytest.mark.asyncio
async def test_ingest_v1_writes_facts():
    db = _DB()
    out = await ingest_dr_v1_report(db, _v1_doc(), actor="test")
    assert out["ok"] is True
    assert out["facts_inserted"] > 0
    assert out["facts_superseded"] == 0
    assert db.operational_facts.rows, "expected facts written"


@pytest.mark.asyncio
async def test_ingest_v1_is_idempotent_supersedes_on_rerun():
    db = _DB()
    first = await ingest_dr_v1_report(db, _v1_doc(), actor="t1")
    n1 = first["facts_inserted"]
    second = await ingest_dr_v1_report(db, _v1_doc(), actor="t2")
    # Same facts re-inserted; previous ones marked superseded.
    assert second["facts_inserted"] == n1
    assert second["facts_superseded"] == n1
    # Only the second-run facts should be is_current=True.
    current = [r for r in db.operational_facts.rows if r.get("is_current") is True]
    assert len(current) == n1


@pytest.mark.asyncio
async def test_ingest_v1_records_ingestion_run():
    db = _DB()
    await ingest_dr_v1_report(db, _v1_doc(), actor="test", trigger="event")
    runs = db.operational_ingestion_runs.rows
    assert runs, "expected at least one ingestion run"
    assert runs[0]["source_type"] == "daily_report"


# ────────────────────────────── HOOK PROBE ────────────────────────────

def test_v1_submit_hook_wired_into_daily_reports_route():
    from pathlib import Path
    src = Path("/app/backend/routes/daily_reports.py").read_text(encoding="utf-8")
    assert "ingest_dr_v1_report" in src, "V1 → ODS hook must be present in daily_reports.py"
    # Hook must sit AFTER `insert_one` so the doc is durable before ingestion.
    idx_insert = src.index("await db.daily_reports.insert_one(doc)")
    idx_ingest = src.index("ingest_dr_v1_report")
    assert idx_ingest > idx_insert, "hook must fire after insert_one"


def test_backfill_script_exists_with_dry_run_and_live_modes():
    from pathlib import Path
    src = Path("/app/backend/scripts/backfill_dr_v1_to_ods.py").read_text(encoding="utf-8")
    assert "--dry-run" in src
    assert "--live" in src
    assert "ingest_dr_v1_report" in src
    assert "operational_ingestion_runs" in src


def test_source_type_daily_report_is_valid_per_model():
    from services.ods_spine.model import SOURCE_TYPES
    assert "daily_report" in SOURCE_TYPES

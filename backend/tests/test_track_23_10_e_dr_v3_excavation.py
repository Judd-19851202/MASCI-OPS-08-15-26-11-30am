"""TRACK 23.10-E · Daily Report V3 Excavation service — lock envelope."""
from __future__ import annotations

import asyncio
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi import HTTPException

BACKEND = Path(__file__).resolve().parents[1]

from tests.test_track_23_10_c_project_linker_and_facts import _DB


def _r(p: Path) -> str:
    return p.read_text(encoding="utf-8")


@pytest.fixture
def db():
    return _DB()


NOW = datetime.now(timezone.utc)


def _seed_active_cp(db, qid="Q-CP-1", eid="E1"):
    db.employees.docs.append({"id": eid, "employee_id": eid,
                              "name": "Alice", "trade": "Foreman",
                              "crew": "Concrete", "is_active": True})
    db.safety_training_records.docs.append({
        "id": qid, "employee_id": eid, "employee_master_id": eid,
        "qualification_type": "COMPETENT_PERSON",
        "certification_type": "COMPETENT_PERSON",
        "verification_status": "active",
        "expiration_date": (NOW + timedelta(days=180)).date().isoformat(),
        "completed_date": (NOW - timedelta(days=30)).date().isoformat(),
        "issuing_organization": "MASCI",
        "certificate_number": "CP-001",
    })


def _seed_expired_cp(db, qid="Q-EXP", eid="E2"):
    db.employees.docs.append({"id": eid, "employee_id": eid,
                              "name": "Bob", "trade": "Foreman", "is_active": True})
    db.safety_training_records.docs.append({
        "id": qid, "employee_id": eid,
        "qualification_type": "COMPETENT_PERSON",
        "certification_type": "COMPETENT_PERSON",
        "verification_status": "expired",
        "expiration_date": (NOW - timedelta(days=10)).date().isoformat(),
    })


def _mk_dr(id_="DR-1", *, exc=None, project_number="P-1"):
    return {
        "id": id_,
        "project_number": project_number,
        "project_name": "Test Project",
        "report_date": NOW.date().isoformat(),
        "prepared_by": "Foreman",
        "excavation_activity_today": "Yes" if exc else "No",
        "excavation": exc or {},
    }


# ─── 1) Static lock tests ────────────────────────────────────────────

def test_files_exist():
    for p in (
        BACKEND / "services" / "daily_report_v3_excavation" / "__init__.py",
        BACKEND / "services" / "daily_report_v3_excavation" / "service.py",
        BACKEND.parent / "frontend" / "src" / "components" / "daily-report-v3" / "CompetentPersonCombo.jsx",
        BACKEND.parent / "frontend" / "src" / "components" / "daily-report-v3" / "DailyReportV3ExcavationSection.jsx",
    ):
        assert p.exists(), f"missing {p}"


def test_submit_route_calls_service():
    src = _r(BACKEND / "routes" / "daily_reports.py")
    assert "from services.daily_report_v3_excavation import" in src
    assert "process_excavation_on_submit(db, doc)" in src


def test_dr_v3_mounts_excavation_section():
    src = _r(BACKEND.parent / "frontend" / "src" / "pages" / "NewDailyReportV3.jsx")
    assert "DailyReportV3ExcavationSection" in src


def test_cp_combo_forbids_free_text():
    """CompetentPersonCombo must consume ONLY the registry — grep for
    any `<input type="text"` bound to a competent_person_name field."""
    src = _r(BACKEND.parent / "frontend" / "src" / "components" / "daily-report-v3" / "CompetentPersonCombo.jsx")
    banned = re.compile(r'competent_person_name.*<input type="text"|<input type="text"[^>]*competent_person_name')
    assert banned.search(src) is None, "free-text CP input found"
    # Registry endpoint used.
    assert "/api/employees/qualifications?type=COMPETENT_PERSON&active=true" in src


def test_excavation_section_gate_default_closed():
    src = _r(BACKEND.parent / "frontend" / "src" / "components" / "daily-report-v3" / "DailyReportV3ExcavationSection.jsx")
    assert "dr-v3-excavation-collapsed" in src
    assert "dr-v3-excavation-gate" in src


# ─── 2) CP registry enforcement ──────────────────────────────────────

def test_free_text_cp_rejected(db):
    from services.daily_report_v3_excavation import process_excavation_on_submit
    dr = _mk_dr(exc={"excavation_today": "yes",
                     "competent_person_name_freetext": "Random Person"})
    with pytest.raises(HTTPException) as e:
        asyncio.get_event_loop().run_until_complete(
            process_excavation_on_submit(db, dr))
    assert e.value.status_code == 400


def test_expired_cp_rejected(db):
    from services.daily_report_v3_excavation import process_excavation_on_submit
    _seed_expired_cp(db)
    dr = _mk_dr(exc={"excavation_today": "yes",
                     "competent_person_qualification_id": "Q-EXP"})
    with pytest.raises(HTTPException) as e:
        asyncio.get_event_loop().run_until_complete(
            process_excavation_on_submit(db, dr))
    assert e.value.status_code == 400


def test_missing_cp_qualification_rejected(db):
    from services.daily_report_v3_excavation import process_excavation_on_submit
    dr = _mk_dr(exc={"excavation_today": "yes",
                     "competent_person_qualification_id": "does-not-exist"})
    with pytest.raises(HTTPException):
        asyncio.get_event_loop().run_until_complete(
            process_excavation_on_submit(db, dr))


def test_active_cp_accepted_and_snapshot_frozen(db):
    from services.daily_report_v3_excavation import process_excavation_on_submit
    _seed_active_cp(db)
    dr = _mk_dr(exc={
        "excavation_today": "yes",
        "competent_person_qualification_id": "Q-CP-1",
        "length": 12, "width": 4, "depth": 6, "dimension_unit": "ft",
        "protective_systems": ["Trench Box"],
        "soil_type": "B",
        "inspection_completed": "yes",
        "inspection_required": "yes",
    })
    # Insert into db so update_one target exists.
    db.daily_reports.docs.append(dr)
    exc = asyncio.get_event_loop().run_until_complete(
        process_excavation_on_submit(db, dr))
    snap = exc["qualification_snapshot"]
    assert snap["qualification_type"] == "COMPETENT_PERSON"
    assert snap["is_active_at_selection"] is True
    assert snap["employee_id"] == "E1"


def test_non_excavation_report_passes_through(db):
    from services.daily_report_v3_excavation import process_excavation_on_submit
    dr = _mk_dr(exc=None)
    result = asyncio.get_event_loop().run_until_complete(
        process_excavation_on_submit(db, dr))
    assert result is None


# ─── 3) Readiness state ─────────────────────────────────────────────

def test_readiness_blocked_without_cp(db):
    from services.daily_report_v3_excavation.service import _compute_readiness
    r = _compute_readiness({"excavation_today": "yes"}, None)
    assert r["state"] == "BLOCKED"
    assert "no_active_competent_person" in r["blockers"]


def test_readiness_ready_when_clear(db):
    from services.daily_report_v3_excavation.service import _compute_readiness
    exc = {"excavation_today": "yes",
           "competent_person_qualification_id": "Q1",
           "inspection_required": "no",
           "protective_systems": ["Trench Box"],
           "access_egress_compliant": "yes",
           "atmospheric_testing_required": "no",
           "water_accumulation": "no"}
    snap = {"is_active_at_selection": True}
    r = _compute_readiness(exc, snap)
    assert r["state"] in ("READY", "READY_WITH_ADVISORIES")
    assert not r["blockers"]


def test_readiness_blocked_on_hold(db):
    from services.daily_report_v3_excavation.service import _compute_readiness
    exc = {"excavation_today": "yes",
           "competent_person_qualification_id": "Q1",
           "protective_systems": ["Trench Box"],
           "hold_issued": "yes"}
    r = _compute_readiness(exc, {"is_active_at_selection": True})
    assert r["state"] == "BLOCKED"
    assert "hold_issued" in r["blockers"]


def test_readiness_blocked_on_utility_strike(db):
    from services.daily_report_v3_excavation.service import _compute_readiness
    exc = {"excavation_today": "yes",
           "competent_person_qualification_id": "Q1",
           "protective_systems": ["Trench Box"],
           "utility_damage_or_strike": "yes"}
    r = _compute_readiness(exc, {"is_active_at_selection": True})
    assert r["state"] == "BLOCKED"
    assert "utility_damage_or_strike" in r["blockers"]


def test_readiness_blocked_when_inspection_required_but_missing(db):
    from services.daily_report_v3_excavation.service import _compute_readiness
    exc = {"excavation_today": "yes",
           "competent_person_qualification_id": "Q1",
           "protective_systems": ["Trench Box"],
           "inspection_required": "yes"}
    r = _compute_readiness(exc, {"is_active_at_selection": True})
    assert r["state"] == "BLOCKED"
    assert "inspection_required_but_not_completed" in r["blockers"]


def test_readiness_blocked_when_no_protective_system(db):
    from services.daily_report_v3_excavation.service import _compute_readiness
    exc = {"excavation_today": "yes",
           "competent_person_qualification_id": "Q1",
           "inspection_required": "no"}
    r = _compute_readiness(exc, {"is_active_at_selection": True})
    assert "no_protective_system_selected" in r["blockers"]


# ─── 4) AI / PDF / Email adapters ────────────────────────────────────

def test_ai_evidence_only_when_excavation():
    from services.daily_report_v3_excavation import excavation_evidence_for_ai
    assert excavation_evidence_for_ai(_mk_dr(exc=None)) is None
    dr = _mk_dr(exc={"excavation_today": "yes", "length": 5,
                     "protective_systems": ["Shield"]})
    e = excavation_evidence_for_ai(dr)
    assert e["excavation_gate"] == "yes"
    assert e["dimensions"]["length"] == 5
    assert e["ai_guidance"]["must_not_hallucinate"] is True


def test_pdf_section_only_when_excavation():
    from services.daily_report_v3_excavation import excavation_pdf_section
    assert excavation_pdf_section(_mk_dr(exc=None)) is None
    dr = _mk_dr(exc={"excavation_today": "yes", "length": 5,
                     "protective_systems": ["Shield"]})
    pdf = excavation_pdf_section(dr)
    assert pdf["title"] == "Excavation / Trench Operations"
    assert any(r["label"] == "Length" for r in pdf["rows"])


def test_email_summary_only_when_excavation():
    from services.daily_report_v3_excavation import excavation_email_summary
    assert excavation_email_summary(_mk_dr(exc=None)) == ""
    dr = _mk_dr(exc={"excavation_today": "yes", "length": 5,
                     "protective_systems": ["Shield"],
                     "readiness": {"state": "READY"}})
    s = excavation_email_summary(dr)
    assert "Excavation / trench operations were performed today" in s
    assert "READY" in s


def test_no_cost_keys_in_any_response():
    from services.daily_report_v3_excavation import (
        excavation_evidence_for_ai, excavation_pdf_section,
    )
    banned = {"cost", "rate", "budget", "payroll", "wage",
              "dollars", "amount", "price", "spend", "spent",
              "revenue", "invoice", "billing", "charge"}

    dr = _mk_dr(exc={"excavation_today": "yes", "length": 5,
                     "protective_systems": ["Shield"],
                     "cost": 9999, "budget": 5000})

    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                assert k not in banned, f"forbidden key {k}"
                walk(v)
        elif isinstance(obj, list):
            for x in obj:
                walk(x)

    walk(excavation_evidence_for_ai(dr))
    walk(excavation_pdf_section(dr))


# ─── 5) Regression ───────────────────────────────────────────────────

def test_regression_23_10_b_registry():
    from services.certifications.qualification_types import (
        QUALIFICATION_ENGINE_TYPES,
    )
    assert "COMPETENT_PERSON" in QUALIFICATION_ENGINE_TYPES


def test_regression_23_10_c_facts_reachable():
    from services.trench_safety.facts_emitter import (
        emit_competent_person_assignment_fact,
        emit_excavation_day_fact,
    )
    assert callable(emit_competent_person_assignment_fact)
    assert callable(emit_excavation_day_fact)


def test_regression_23_10_d_lift_reachable():
    from services.safety_portal_trench import company_trench_safety_kpis
    assert callable(company_trench_safety_kpis)

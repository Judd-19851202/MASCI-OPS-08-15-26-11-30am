"""Track 19.16 · Phase D · Executive Intelligence Center · LOCK TESTS."""
from __future__ import annotations
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from tests.test_track_19_16_incident_engine_phase_a import (  # noqa: E402
    _FakeDB, SAFETY, FIELD,
)
from incident_engine import case_service, intelligence
from incident_engine import corrective_actions as ca_engine
from incident_engine import workspace as ws


def _run(c): return asyncio.get_event_loop().run_until_complete(c)


@pytest.fixture
def db(): return _FakeDB()


def _mk(db, incident_type="near_miss", job_number="J-1"):
    return _run(case_service.create_case(
        db, actor=SAFETY,
        field_block={
            "incident_type": incident_type,
            "location_label": "Zone", "job_number": job_number,
            "reporter_name": "Foreman",
        },
    ))


def test_company_health_shape_and_zero_state(db):
    h = _run(intelligence.compute_company_health(db))
    for k in ("open_cases", "total_cases", "critical_cases", "avg_readiness_pct",
              "corrective_actions_open", "corrective_actions_total",
              "sla", "trend_30d", "trend_counts"):
        assert k in h, k
    assert h["open_cases"] == 0
    for k in ("on_pace", "watch", "behind", "missed", "unset"):
        assert k in h["sla"]


def test_company_health_counts_open_and_critical(db):
    _mk(db, incident_type="employee_injury")
    _mk(db, incident_type="utility_strike")
    _mk(db, incident_type="near_miss")
    h = _run(intelligence.compute_company_health(db))
    assert h["open_cases"] == 3
    assert h["critical_cases"] == 2


def test_action_queue_prioritises_critical_recordable_and_sla(db):
    # Critical incident type — should be flagged.
    c1 = _mk(db, incident_type="employee_injury")
    _run(case_service.transition_case(
        db, case_id=c1["id"], to_state="FIELD_SUBMITTED", actor=SAFETY))
    _run(case_service.update_safety_block(
        db, case_id=c1["id"], actor=SAFETY,
        patch={"osha_recordable": True},
    ))
    # Non-critical near miss should NOT be flagged (no recordability, no SLA set).
    _mk(db, incident_type="near_miss")

    q = _run(intelligence.compute_action_queue(db))
    ids = [r["case_id"] for r in q]
    assert c1["id"] in ids
    # Reasons include critical + osha
    for r in q:
        if r["case_id"] == c1["id"]:
            assert "critical_incident_type" in r["reasons"]
            assert "osha_recordable" in r["reasons"]
            assert r["urgency"] >= 30
            assert r["recommended_action"]


def test_sla_status_transitions(db):
    # Case with target_ready_at in past → MISSED
    c = _mk(db)
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    _run(case_service.update_safety_block(
        db, case_id=c["id"], actor=SAFETY,
        patch={"target_ready_at": past},
    ))
    updated = _run(case_service.get_case(db, c["id"]))
    assert intelligence._sla_status(updated) == "MISSED"

    # Case ~ 1 day out → BEHIND
    future = (datetime.now(timezone.utc) + timedelta(hours=18)).isoformat()
    _run(case_service.update_safety_block(
        db, case_id=c["id"], actor=SAFETY,
        patch={"target_ready_at": future},
    ))
    assert intelligence._sla_status(_run(case_service.get_case(db, c["id"]))) == "BEHIND"

    # ~3 days out → WATCH
    ok = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    _run(case_service.update_safety_block(
        db, case_id=c["id"], actor=SAFETY,
        patch={"target_ready_at": ok},
    ))
    assert intelligence._sla_status(_run(case_service.get_case(db, c["id"]))) == "WATCH"

    # >5 days out → ON_PACE
    on_pace = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    _run(case_service.update_safety_block(
        db, case_id=c["id"], actor=SAFETY,
        patch={"target_ready_at": on_pace},
    ))
    assert intelligence._sla_status(_run(case_service.get_case(db, c["id"]))) == "ON_PACE"


def test_root_cause_intelligence_aggregates(db):
    c1 = _mk(db)
    c2 = _mk(db)
    _run(case_service.update_safety_block(
        db, case_id=c1["id"], actor=SAFETY,
        patch={"root_cause_categories": ["training", "communication"],
               "contributing_factors": ["insufficient_walk_around", "time_pressure"]},
    ))
    _run(case_service.update_safety_block(
        db, case_id=c2["id"], actor=SAFETY,
        patch={"root_cause_categories": ["training"],
               "contributing_factors": ["time_pressure"]},
    ))
    rc = _run(intelligence.compute_root_cause_intelligence(db))
    cats = {c["code"]: c["count"] for c in rc["categories"]}
    assert cats["training"] == 2
    assert cats["communication"] == 1
    recurring = {r["code"]: r["occurrences"] for r in rc["recurring_factors"]}
    assert recurring.get("time_pressure") == 2
    # Non-recurring factors are NOT in the list.
    assert "insufficient_walk_around" not in recurring


def test_capa_intelligence_counts(db):
    c = _mk(db)
    a1 = _run(ca_engine.create_action(
        db, consumer_kind="incident_case", consumer_id=c["id"],
        action_class="training", title="a1", actor=SAFETY,
    ))
    _run(ca_engine.create_action(
        db, consumer_kind="incident_case", consumer_id=c["id"],
        action_class="ppe", title="a2", actor=SAFETY,
    ))
    _run(ca_engine.verify_action(db, action_id=a1["id"], actor=SAFETY))
    ci = _run(intelligence.compute_capa_intelligence(db))
    assert ci["total"] == 2
    assert ci["verified"] == 1
    assert ci["open"] == 1
    assert ci["overdue"] == 0


def test_project_intelligence_ranks_by_criticality(db):
    _mk(db, incident_type="employee_injury", job_number="J-100")
    _mk(db, incident_type="near_miss", job_number="J-100")
    _mk(db, incident_type="near_miss", job_number="J-200")
    projects = _run(intelligence.compute_project_intelligence(db))
    # J-100 has the critical case → should rank first.
    assert projects[0]["job_number"] == "J-100"
    assert projects[0]["critical"] == 1
    assert projects[0]["cases"] == 2


def test_fleet_intelligence_identifies_repeat_assets(db):
    c1 = _mk(db, incident_type="vehicle_accident")
    c2 = _mk(db, incident_type="vehicle_accident")
    _run(case_service.update_field_block(
        db, case_id=c1["id"], actor=SAFETY, patch={"vehicle_ids": "TRK-42"},
    ))
    _run(case_service.update_field_block(
        db, case_id=c2["id"], actor=SAFETY, patch={"vehicle_ids": "TRK-42"},
    ))
    fi = _run(intelligence.compute_fleet_intelligence(db))
    assert fi["vehicle_incidents_total"] == 2
    assert any(r["id"] == "TRK-42" and r["count"] == 2 for r in fi["repeat_vehicles"])


def test_learning_intelligence_counts_near_miss_and_peaks(db):
    _mk(db, incident_type="near_miss")
    _mk(db, incident_type="near_miss")
    _mk(db, incident_type="employee_injury")
    li = _run(intelligence.compute_learning_intelligence(db))
    assert li["near_miss_count"] == 2
    # Peaks exist (may be same hour for test cases but shape is what matters).
    assert isinstance(li["peak_hours"], list)


def test_risk_heatmap_shape(db):
    _mk(db, incident_type="vehicle_accident", job_number="J-1")
    _mk(db, incident_type="near_miss", job_number="J-1")
    _mk(db, incident_type="vehicle_accident", job_number="J-2")
    hm = _run(intelligence.compute_risk_heatmap(db))
    assert "incident_types" in hm and "jobs" in hm and "cells" in hm
    assert set(hm["incident_types"]) >= {"vehicle_accident", "near_miss"}
    assert set(hm["jobs"]) >= {"J-1", "J-2"}
    # Cells with count > 0 only.
    assert all(c["count"] > 0 for c in hm["cells"])


def test_executive_brief_has_all_sections(db):
    _mk(db, incident_type="employee_injury")
    brief = _run(intelligence.compute_executive_brief(db))
    for k in ("organization_health", "highest_risks", "positive_trends",
              "negative_trends", "top_projects_by_risk", "fleet", "learning"):
        assert k in brief, k


# ── Zero-Drift ──────────────────────────────────────────────────────
REPO_ROOT = Path("/app")


def test_intelligence_reads_only_never_writes():
    for f in ("intelligence.py", "intelligence_routes.py"):
        src = (REPO_ROOT / f"backend/incident_engine/{f}").read_text(encoding="utf-8")
        # No insert / update / delete on the incident engine collections.
        for forbidden in (".insert_one(", ".insert_many(", ".update_one(",
                          ".update_many(", ".delete_one(", ".delete_many(",
                          ".replace_one("):
            assert forbidden not in src, f"{f} :: {forbidden}"


def test_legacy_incident_lifecycle_still_untouched():
    txt = (REPO_ROOT / "backend/routes/incident_lifecycle.py").read_text(encoding="utf-8")
    assert "register_incident_lifecycle_routes" in txt


def test_server_registers_intelligence():
    src = (REPO_ROOT / "backend/server.py").read_text(encoding="utf-8")
    assert "_register_ie_intel_routes" in src


# ── Frontend surface ────────────────────────────────────────────────
FE_ROOT = REPO_ROOT / "frontend/src"


def test_intelligence_page_exists():
    p = FE_ROOT / "pages/ExecutiveIntelligence.jsx"
    assert p.is_file()
    src = p.read_text(encoding="utf-8")
    assert 'data-testid="executive-intelligence"' in src


def test_app_js_mounts_intelligence_route():
    txt = (FE_ROOT / "App.js").read_text(encoding="utf-8")
    assert "ExecutiveIntelligence" in txt
    assert '/safety/executive-intelligence' in txt

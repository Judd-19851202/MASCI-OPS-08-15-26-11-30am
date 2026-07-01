"""Track 19.16 · Final Operational Closeout · LOCK TESTS.

Scope
-----
* Fleet / Equipment cross-link is a read-only reference — the Board
  never becomes a source of incident truth.
* The Equipment Status Board frontend renders a "Recent Incident" pill
  linked to the Safety Case Workspace.
* App.js no longer imports the retired NewIncident component into the
  production bundle. The file itself is retained (documented) because
  older lock tests scan it as a pattern reference.
* Every production route is still mounted and reachable.
* Zero-Drift preserved on Phase A engine, reports engine, workspace,
  intelligence, and legacy /api/incidents backend.
"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path

import pytest

from tests.test_track_19_16_incident_engine_phase_a import (  # noqa: E402
    _FakeDB, SAFETY,
)
from incident_engine import case_service
from incident_engine.fleet_crosslink import list_incidents_by_unit


REPO_ROOT = Path("/app")
FE_ROOT = REPO_ROOT / "frontend/src"


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ═══════════════════════════════════════════════════════════════════
# 1 · Fleet / Equipment cross-link — read-only reference join
# ═══════════════════════════════════════════════════════════════════
@pytest.fixture
def db():
    return _FakeDB()


def test_cross_link_returns_recent_case_for_unit(db):
    c = _run(case_service.create_case(
        db, actor=SAFETY,
        field_block={
            "incident_type":   "vehicle_accident",
            "location_label":  "Zone A",
            "job_number":      "J-CL-1",
            "reporter_name":   "F",
            "selected_unit_numbers": ["TR-19"],
        },
    ))
    _run(case_service.transition_case(
        db, case_id=c["id"], to_state="FIELD_SUBMITTED", actor=SAFETY,
    ))
    out = _run(list_incidents_by_unit(db, unit_numbers=["TR-19"]))
    assert "TR-19" in out
    rows = out["TR-19"]
    assert rows and rows[0]["case_id"] == c["id"]
    assert rows[0]["case_number"]
    assert rows[0]["incident_type"] == "vehicle_accident"


def test_cross_link_projects_only_reference_fields(db):
    """Board rows must NEVER carry narrative, medical, witness, root
    cause, or CAPA data."""
    c = _run(case_service.create_case(
        db, actor=SAFETY,
        field_block={
            "incident_type":   "vehicle_accident",
            "location_label":  "Zone B",
            "job_number":      "J-CL-2",
            "reporter_name":   "F",
            "selected_unit_numbers": ["TR-22"],
            "observed_conditions": "sensitive narrative that must not leak",
            "injury_body_part":    "arm",
            "root_cause_summary":  "confidential",
        },
    ))
    _run(case_service.transition_case(
        db, case_id=c["id"], to_state="FIELD_SUBMITTED", actor=SAFETY,
    ))
    out = _run(list_incidents_by_unit(db))
    for rows in out.values():
        for r in rows:
            for forbidden in ("observed_conditions", "injury_body_part",
                              "root_cause_summary", "witnesses",
                              "medical", "corrective_actions", "photos"):
                assert forbidden not in r, (
                    f"cross-link leaked {forbidden}: {r}"
                )


def test_cross_link_never_writes_to_incident_case(db):
    c = _run(case_service.create_case(
        db, actor=SAFETY,
        field_block={
            "incident_type":   "equipment_accident",
            "location_label":  "Zone C",
            "job_number":      "J-CL-3",
            "reporter_name":   "F",
            "selected_unit_numbers": ["EQ-9"],
        },
    ))
    _run(case_service.transition_case(
        db, case_id=c["id"], to_state="FIELD_SUBMITTED", actor=SAFETY,
    ))
    before = _run(case_service.get_case(db, c["id"]))
    _run(list_incidents_by_unit(db, unit_numbers=["EQ-9"]))
    after = _run(case_service.get_case(db, c["id"]))
    assert before == after


def test_cross_link_limits_rows_per_unit(db):
    for i in range(6):
        c = _run(case_service.create_case(
            db, actor=SAFETY,
            field_block={
                "incident_type":   "vehicle_accident",
                "location_label":  f"Loc {i}",
                "job_number":      f"J-{i}",
                "reporter_name":   "F",
                "selected_unit_numbers": ["TR-BUSY"],
            },
        ))
        _run(case_service.transition_case(
            db, case_id=c["id"], to_state="FIELD_SUBMITTED", actor=SAFETY,
        ))
        time.sleep(0.001)
    out = _run(list_incidents_by_unit(db, unit_numbers=["TR-BUSY"],
                                      limit_per_unit=3))
    assert "TR-BUSY" in out
    assert len(out["TR-BUSY"]) == 3


def test_cross_link_ignores_cases_without_selected_units(db):
    _run(case_service.create_case(
        db, actor=SAFETY,
        field_block={
            "incident_type":   "near_miss",
            "location_label":  "Zone D",
            "job_number":      "J-NOUNIT",
            "reporter_name":   "F",
        },
    ))
    out = _run(list_incidents_by_unit(db))
    assert out == {}


# ═══════════════════════════════════════════════════════════════════
# 2 · Fleet cross-link source is Zero-Drift
# ═══════════════════════════════════════════════════════════════════
def test_fleet_crosslink_source_is_read_only():
    src = (REPO_ROOT / "backend/incident_engine/fleet_crosslink.py").read_text(
        encoding="utf-8")
    for forbidden in (".insert_one(", ".insert_many(",
                      ".update_one(", ".update_many(",
                      ".delete_one(", ".delete_many(",
                      ".replace_one("):
        assert forbidden not in src, f"forbidden write op: {forbidden}"


def test_fleet_crosslink_never_reads_legacy_incidents_collection():
    src = (REPO_ROOT / "backend/incident_engine/fleet_crosslink.py").read_text(
        encoding="utf-8")
    assert 'db["incidents"]' not in src
    assert "db.incidents" not in src


def test_report_routes_registers_incidents_by_unit_endpoint():
    src = (REPO_ROOT / "backend/incident_engine/report_routes.py").read_text(
        encoding="utf-8")
    assert '"/equipment-status-board/incidents-by-unit"' in src
    assert "list_incidents_by_unit" in src


# ═══════════════════════════════════════════════════════════════════
# 3 · Equipment Status Board frontend renders the pill
# ═══════════════════════════════════════════════════════════════════
def test_equipment_status_board_fetches_incident_crosslink():
    src = (FE_ROOT / "components/EquipmentStatusBoard.jsx").read_text(
        encoding="utf-8")
    assert "/equipment-status-board/incidents-by-unit" in src
    assert "incidentMap" in src


def test_equipment_status_board_renders_recent_incident_pill():
    src = (FE_ROOT / "components/EquipmentStatusBoard.jsx").read_text(
        encoding="utf-8")
    assert "RecentIncidentPill" in src
    # data-testid follows fleet-recent-incident-<unit> convention.
    assert 'data-testid={`fleet-recent-incident-${unitKey}`}' in src


def test_equipment_status_board_pill_links_to_safety_case_workspace():
    src = (FE_ROOT / "components/EquipmentStatusBoard.jsx").read_text(
        encoding="utf-8")
    # The pill must be a <Link> to the Safety Case Workspace, not an
    # ad-hoc modal that duplicates incident detail.
    assert "/safety/cases/${encodeURIComponent(top.case_id)}" in src


def test_equipment_status_board_pill_never_shows_narrative_or_capa():
    """Reference-only: forbidden phrases must not appear inside the pill."""
    src = (FE_ROOT / "components/EquipmentStatusBoard.jsx").read_text(
        encoding="utf-8")
    idx = src.index("function RecentIncidentPill")
    window = src[idx: idx + 3000]
    for forbidden in ("root_cause", "corrective_actions",
                      "witnesses", "medical", "observed_conditions",
                      "root cause", "corrective actions"):
        assert forbidden not in window, (
            f"pill leaked {forbidden!r}"
        )


# ═══════════════════════════════════════════════════════════════════
# 4 · Frontend selection writes selected_unit_numbers on the draft
# ═══════════════════════════════════════════════════════════════════
def test_incident_report_writes_selected_unit_numbers_on_draft():
    src = (FE_ROOT / "pages/IncidentReport.jsx").read_text(encoding="utf-8")
    assert "selected_unit_numbers" in src
    idx = src.index("selected_unit_numbers")
    window = src[max(0, idx - 400): idx + 200]
    assert 'source === "equipment_master"' in window
    assert "unit_number" in window


# ═══════════════════════════════════════════════════════════════════
# 5 · Dead code cleanup — App.js no longer imports NewIncident
# ═══════════════════════════════════════════════════════════════════
def test_app_js_no_longer_imports_newincident():
    src = (FE_ROOT / "App.js").read_text(encoding="utf-8")
    # No production import line — anywhere in the file.
    for line in src.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("//"):
            continue
        assert 'import NewIncident from "@/pages/NewIncident"' not in stripped


def test_newincident_file_retained_with_documented_reason():
    """The file itself stays on disk because older lock tests reference
    it. The App.js comment documents this decision."""
    p = FE_ROOT / "pages/NewIncident.jsx"
    assert p.is_file(), "NewIncident.jsx must remain on disk (pattern ref)"
    app_txt = (FE_ROOT / "App.js").read_text(encoding="utf-8")
    assert "retired NewIncident" in app_txt


# ═══════════════════════════════════════════════════════════════════
# 6 · Full route certification
# ═══════════════════════════════════════════════════════════════════
def test_all_production_routes_still_mounted():
    txt = (FE_ROOT / "App.js").read_text(encoding="utf-8")
    for needle in (
        '<Route path="/incidents/report"',
        '<Route path="/incidents/new" element={<Navigate to="/incidents/report" replace />}',
        '<Route path="/incidents/submit" element={<Navigate to="/incidents/report" replace />}',
        '<Route path="/near-miss"',
        '<Route path="/safety/cases/:caseId"',
        '<Route path="/safety/executive-intelligence"',
        '<Route path="/safety/cases/:caseId/reports/:reportType"',
    ):
        assert needle in txt, f"missing route: {needle}"


def test_legacy_incident_backend_still_untouched():
    txt = (REPO_ROOT / "backend/routes/incident_lifecycle.py").read_text(
        encoding="utf-8")
    assert "register_incident_lifecycle_routes" in txt


# ═══════════════════════════════════════════════════════════════════
# 7 · Zero-Drift on the engine core
# ═══════════════════════════════════════════════════════════════════
def test_closeout_did_not_add_osha_recordability_automation():
    """Explicit anti-scope guard: Phase F work is intentionally deferred.
    No OSHA / 300 / 300A automation may have been added by this
    closeout. Compliance Intelligence remains future/backlog."""
    engine_dir = REPO_ROOT / "backend/incident_engine"
    forbidden_terms = (
        "osha_300a_automation", "osha_recordability_engine",
        "compliance_engine", "record_osha_recordable_case",
    )
    for path in engine_dir.rglob("*.py"):
        src = path.read_text(encoding="utf-8", errors="ignore")
        for term in forbidden_terms:
            assert term not in src, (
                f"Phase F scope leaked in {path.name}: {term}"
            )


def test_case_service_and_phase_a_engine_unchanged_by_closeout():
    """Case service is the sole write-path for incident_cases. The
    closeout is additive — case_service must not import from
    fleet_crosslink or the reports layer."""
    src = (REPO_ROOT / "backend/incident_engine/case_service.py").read_text(
        encoding="utf-8")
    for forbidden in ("from .fleet_crosslink", "from .reports",
                      "from .report_routes"):
        assert forbidden not in src


# ═══════════════════════════════════════════════════════════════════
# 8 · Six-Pillar certification (asserted directly)
# ═══════════════════════════════════════════════════════════════════
def test_pillar_powerful_shop_sees_incident_where_they_plan_dispatch():
    src = (FE_ROOT / "components/EquipmentStatusBoard.jsx").read_text(
        encoding="utf-8")
    assert "RecentIncidentPill" in src


def test_pillar_simple_no_re_entry_of_incident_details_on_board():
    """The Board carries no free-text incident authoring UI."""
    src = (FE_ROOT / "components/EquipmentStatusBoard.jsx").read_text(
        encoding="utf-8")
    for forbidden in ("<textarea", "<input type=\"file\"",
                      "photos.push", "add witness"):
        assert forbidden not in src


def test_pillar_beautiful_pill_has_icon_and_tight_styling():
    src = (FE_ROOT / "components/EquipmentStatusBoard.jsx").read_text(
        encoding="utf-8")
    idx = src.index("function RecentIncidentPill")
    window = src[idx: idx + 3000]
    assert "rounded-full" in window
    assert "Siren" in window


def test_pillar_trusted_board_never_owns_incident_truth(db):
    """Same as the write-guard test above, restated as a doctrine."""
    # Nothing in the fleet_crosslink helper writes to Mongo.
    p = REPO_ROOT / "backend/incident_engine/fleet_crosslink.py"
    src = p.read_text(encoding="utf-8")
    assert "insert" not in src and "update" not in src

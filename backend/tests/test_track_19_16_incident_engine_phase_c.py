"""Track 19.16 · Phase C · Safety Case Workspace · LOCK TESTS."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from tests.test_track_19_16_incident_engine_phase_a import (  # noqa: E402
    _FakeDB, SAFETY, FIELD, PM, ADMIN, EXEC,
)
from incident_engine import case_service
from incident_engine import workspace as ws
from incident_engine import corrective_actions as ca_engine
from incident_engine import evidence as ev_engine


def _run(c):
    return asyncio.get_event_loop().run_until_complete(c)


@pytest.fixture
def db():
    return _FakeDB()


def _mk_case(db, incident_type="employee_injury"):
    c = _run(case_service.create_case(
        db, actor=SAFETY,
        field_block={
            "incident_type": incident_type,
            "location_label": "Zone A",
            "reporter_name": "Foreman",
            "job_number": "J-1",
        },
    ))
    return c


# ── Communications ──────────────────────────────────────────────────
def test_communication_add_and_list(db):
    c = _mk_case(db)
    comm = _run(ws.add_communication(
        db, case_id=c["id"], actor=SAFETY, kind="call",
        subject="Called injured worker", body="Doing OK",
        contact_name="Jose", contact_role="employee",
    ))
    assert comm["kind"] == "call"
    lst = _run(ws.list_communications(db, case_id=c["id"]))
    assert len(lst) == 1


def test_communication_kind_validation(db):
    c = _mk_case(db)
    with pytest.raises(ValueError):
        _run(ws.add_communication(db, case_id=c["id"], actor=SAFETY, kind="bogus"))


def test_communication_denied_for_field(db):
    c = _mk_case(db)
    with pytest.raises(PermissionError):
        _run(ws.add_communication(db, case_id=c["id"], actor=FIELD, kind="call"))


# ── Witnesses ───────────────────────────────────────────────────────
def test_witness_lifecycle(db):
    c = _mk_case(db)
    w = _run(ws.add_witness(
        db, case_id=c["id"], actor=SAFETY,
        kind="internal_employee", name="Jane",
    ))
    assert w["status"] == "pending"
    upd = _run(ws.update_witness(
        db, witness_id=w["id"], actor=SAFETY,
        patch={"status": "interviewed", "statement": "saw everything"},
    ))
    assert upd["status"] == "interviewed"
    assert upd["statement"] == "saw everything"


def test_witness_status_validation(db):
    c = _mk_case(db)
    with pytest.raises(ValueError):
        _run(ws.add_witness(
            db, case_id=c["id"], actor=SAFETY,
            kind="internal_employee", name="X", status="INVALID_STATUS",
        ))


def test_witness_credibility_field_exists(db):
    """Credibility notes exist on the model (safety-only field)."""
    c = _mk_case(db)
    w = _run(ws.add_witness(
        db, case_id=c["id"], actor=SAFETY,
        kind="public", name="Observer",
        credibility_notes="verify — third-party bystander",
    ))
    assert w["credibility_notes"].startswith("verify")


def test_witness_denied_for_field(db):
    c = _mk_case(db)
    with pytest.raises(PermissionError):
        _run(ws.add_witness(
            db, case_id=c["id"], actor=FIELD,
            kind="internal_employee", name="X",
        ))


# ── Medical ─────────────────────────────────────────────────────────
def test_medical_add_and_list(db):
    c = _mk_case(db)
    m = _run(ws.add_medical_entry(
        db, case_id=c["id"], actor=SAFETY, kind="first_aid",
        subject_name="Jose", provider="Site medic",
        notes="Ice pack", lost_days=0,
    ))
    assert m["kind"] == "first_aid"
    entries = _run(ws.list_medical(db, case_id=c["id"]))
    assert len(entries) == 1


def test_medical_kind_validation(db):
    c = _mk_case(db)
    with pytest.raises(ValueError):
        _run(ws.add_medical_entry(db, case_id=c["id"], actor=SAFETY, kind="bogus"))


# ── Agency ──────────────────────────────────────────────────────────
def test_agency_add_and_list(db):
    c = _mk_case(db)
    a = _run(ws.add_agency_contact(
        db, case_id=c["id"], actor=SAFETY,
        agency_name="City PD", officer_name="Officer M",
        report_number="R-1234",
    ))
    assert a["agency_name"] == "City PD"
    lst = _run(ws.list_agency(db, case_id=c["id"]))
    assert len(lst) == 1


# ── Tasks ───────────────────────────────────────────────────────────
def test_task_lifecycle(db):
    c = _mk_case(db)
    t = _run(ws.add_task(
        db, case_id=c["id"], actor=SAFETY,
        title="Interview operator", assigned_to_name="Sam",
    ))
    assert t["status"] == "open"
    upd = _run(ws.update_task(
        db, task_id=t["id"], actor=SAFETY,
        patch={"status": "completed"},
    ))
    assert upd["status"] == "completed"
    assert upd["completed_at"]
    assert upd["completed_by"]


def test_task_status_validation(db):
    c = _mk_case(db)
    t = _run(ws.add_task(db, case_id=c["id"], actor=SAFETY, title="test task"))
    with pytest.raises(ValueError):
        _run(ws.update_task(db, task_id=t["id"], actor=SAFETY,
                            patch={"status": "BOGUS_STATUS"}))


def test_task_denied_for_field(db):
    c = _mk_case(db)
    with pytest.raises(PermissionError):
        _run(ws.add_task(db, case_id=c["id"], actor=FIELD, title="x"))


# ── Case Health ─────────────────────────────────────────────────────
def test_case_health_flags_blockers(db):
    c = _mk_case(db, incident_type="employee_injury")
    # Fresh case — root cause missing, medical missing, recordability unset.
    h = _run(ws.compute_case_health(db, case_id=c["id"], case_doc=c))
    assert "root_cause_missing" in h["blockers"]
    assert "recordability_unset" in h["blockers"]
    assert "medical_entry_missing" in h["blockers"]
    assert h["completeness_pct"] < 100


def test_case_health_clears_when_satisfied(db):
    c = _mk_case(db, incident_type="near_miss")
    # Set root cause; near_miss has no medical requirement, no recordability requirement
    updated = _run(case_service.update_safety_block(
        db, case_id=c["id"], actor=SAFETY,
        patch={"root_cause_summary": "training gap in flagger placement"},
    ))
    h = _run(ws.compute_case_health(db, case_id=c["id"], case_doc=updated))
    assert "root_cause_missing" not in h["blockers"]


def test_case_health_counts_evidence_witnesses_communications(db):
    c = _mk_case(db)
    _run(ev_engine.add_evidence(db, case_id=c["id"], evidence_type="photo", actor=SAFETY))
    _run(ws.add_witness(db, case_id=c["id"], actor=SAFETY, kind="public", name="X"))
    _run(ws.add_communication(db, case_id=c["id"], actor=SAFETY, kind="call"))
    _run(ws.add_task(db, case_id=c["id"], actor=SAFETY, title="task 1"))
    _run(ca_engine.create_action(
        db, consumer_kind="incident_case", consumer_id=c["id"],
        action_class="training", title="CA", actor=SAFETY,
    ))
    fresh = _run(case_service.get_case(db, c["id"]))
    h = _run(ws.compute_case_health(db, case_id=c["id"], case_doc=fresh))
    counts = h["counts"]
    assert counts["evidence"] == 1
    assert counts["witnesses"] == 1
    assert counts["communications"] == 1
    assert counts["tasks_total"] == 1
    assert counts["tasks_open"] == 1
    assert counts["corrective_actions_total"] == 1
    assert counts["corrective_actions_open"] == 1
    assert "open_corrective_actions" in h["blockers"]
    assert "open_tasks" in h["blockers"]


# ── Executive Snapshot ──────────────────────────────────────────────
def test_executive_snapshot_shape(db):
    c = _mk_case(db)
    snap = _run(ws.compute_executive_snapshot(db, case_id=c["id"], case_doc=c))
    for key in ("case_id", "case_number", "state", "incident_type",
                "location_label", "job_number", "readiness"):
        assert key in snap, key
    assert "completeness_pct" in snap["readiness"]


# ── Timeline authoritativeness (event emission) ─────────────────────
def test_workspace_operations_emit_timeline_events(db):
    from incident_engine.events import list_events
    c = _mk_case(db)
    _run(ws.add_witness(db, case_id=c["id"], actor=SAFETY, kind="public", name="X"))
    _run(ws.add_communication(db, case_id=c["id"], actor=SAFETY, kind="call"))
    _run(ws.add_medical_entry(db, case_id=c["id"], actor=SAFETY, kind="first_aid"))
    _run(ws.add_task(db, case_id=c["id"], actor=SAFETY, title="t1"))
    events = _run(list_events(db, case_id=c["id"]))
    types = [e["event_type"] for e in events]
    # Every mutation contributed at least one event.
    assert "witness.added" in types
    assert types.count("safety_block.updated") >= 3


# ── Zero-Drift ──────────────────────────────────────────────────────
REPO_ROOT = Path("/app")


def test_workspace_never_writes_to_legacy_incidents():
    for f in ("workspace.py", "workspace_routes.py"):
        src = (REPO_ROOT / f"backend/incident_engine/{f}").read_text(encoding="utf-8")
        for forbidden in ("db.incidents.insert", 'db["incidents"].insert',
                          "db.incidents.update", "db.incidents.delete"):
            assert forbidden not in src, f"{f} :: {forbidden}"


def test_legacy_incident_lifecycle_still_untouched():
    txt = (REPO_ROOT / "backend/routes/incident_lifecycle.py").read_text(encoding="utf-8")
    assert "register_incident_lifecycle_routes" in txt


def test_server_registers_all_incident_engine_layers():
    src = (REPO_ROOT / "backend/server.py").read_text(encoding="utf-8")
    assert "register_incident_engine_routes" in src
    assert "_register_ie_public_routes" in src
    assert "_register_ie_workspace_routes" in src


def test_new_collections_are_isolated():
    from incident_engine.workspace import (
        COLLECTION_COMMUNICATIONS, COLLECTION_WITNESSES,
        COLLECTION_MEDICAL, COLLECTION_AGENCY, COLLECTION_TASKS,
    )
    from incident_engine.constants import COLLECTION_LEGACY_INCIDENTS
    for c in (COLLECTION_COMMUNICATIONS, COLLECTION_WITNESSES,
              COLLECTION_MEDICAL, COLLECTION_AGENCY, COLLECTION_TASKS):
        assert c != COLLECTION_LEGACY_INCIDENTS
        assert c.startswith("incident_case_")


# ── Frontend surface contracts ──────────────────────────────────────
FE_ROOT = REPO_ROOT / "frontend/src"


def test_workspace_page_exists():
    p = FE_ROOT / "pages/SafetyCaseWorkspace.jsx"
    assert p.is_file()
    src = p.read_text(encoding="utf-8")
    assert 'data-testid="safety-case-workspace"' in src
    assert "case-timeline" in src
    assert "case-health" in src


def test_workspace_api_client_exists():
    p = FE_ROOT / "lib/caseWorkspaceApi.js"
    assert p.is_file()
    src = p.read_text(encoding="utf-8")
    # Client must consume ALL satellite endpoints.
    for needle in (
        "/communications", "/witnesses", "/medical",
        "/agency-contacts", "/tasks", "/health", "/executive-snapshot",
        "/timeline", "/evidence",
    ):
        assert needle in src, needle


def test_app_js_mounts_workspace_route():
    txt = (FE_ROOT / "App.js").read_text(encoding="utf-8")
    assert 'path="/safety/cases/:caseId"' in txt or 'path="/safety/cases/:id"' in txt
    assert "SafetyCaseWorkspace" in txt
